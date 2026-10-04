"""Fail-closed FIN-PIT-1A continuation for an exact approved proposal."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


CYCLE = "fin-pit-restart-20261003T083918Z-87c88ae1"


class BoundaryError(RuntimeError):
    """A frozen network boundary was reached."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def immutable_write(path: Path, value: bytes) -> None:
    if path.exists():
        raise FileExistsError(f"immutable path exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _same_issuer_redirect(source: str, target: str, allowed_hosts: set[str]) -> bool:
    source_host = (urlsplit(source).hostname or "").removeprefix("www.")
    target_host = (urlsplit(target).hostname or "").removeprefix("www.")
    return urlsplit(target).scheme == "https" and target_host == source_host and (urlsplit(target).hostname or "") in allowed_hosts


def _is_pdf_response(body: bytes, content_type: str) -> bool:
    normalized = content_type.casefold().split(";", 1)[0].strip()
    allowed_types = {"application/pdf", "application/octet-stream"}
    return (
        normalized in allowed_types
        and body.startswith(b"%PDF-")
        and b"%%EOF" in body[-2048:]
    )


def _persist_response_before_validation(output: Path, request_id: str, result: dict, observed_at: str) -> dict:
    """Persist bounded response bytes and provenance before semantic/content validation."""
    body = result["body"]
    raw_rel = Path("raw") / f"{request_id}.response.bin"
    metadata_rel = Path("raw") / f"{request_id}.metadata.json"
    evidence = {
        "raw_path": raw_rel.as_posix(),
        "metadata_path": metadata_rel.as_posix(),
        "bytes": len(body),
        "sha256": sha256_bytes(body),
        "final_url": result["url"],
        "http_status": result["status"],
        "content_type": result["content_type"],
        "fetched_at": observed_at,
    }
    immutable_write(output / raw_rel, body)
    immutable_write(output / metadata_rel, canonical_bytes(evidence))
    return evidence


def _validate_persisted_response(result: dict, *, acquisition: bool) -> str:
    if result["status"] != 200:
        raise BoundaryError(f"UNEXPECTED_HTTP_STATUS_{result['status']}")
    body = result["body"]
    marker = body[:65536].lower()
    if any(item in marker for item in (b"captcha", b"managed challenge", b"access denied", b"login required", b"cloudflare")):
        raise BoundaryError("ACCESS_CONTROL_MARKER")
    content_type = result["content_type"]
    if acquisition:
        if not _is_pdf_response(body, content_type):
            raise BoundaryError("NON_PDF_OR_INVALID_PDF")
        return "pdf"
    normalized = content_type.casefold()
    if body.startswith(b"%PDF-") or not (
        "html" in normalized
        or "xml" in normalized
        or body.lstrip().lower().startswith((b"<!doctype", b"<html", b"<?xml"))
    ):
        raise BoundaryError("DOCUMENT_OR_UNEXPECTED_CONTENT")
    return "xml" if "xml" in normalized else "html"


class Collector:
    def __init__(self, policy: dict, *, opener=None, sleeper=time.sleep, monotonic=time.monotonic) -> None:
        self.policy = policy
        self.opener = opener or build_opener(_NoRedirect())
        self.sleeper = sleeper
        self.monotonic = monotonic
        self.requests = 0
        self.bytes = 0
        self.last_request_at: float | None = None

    def get(self, url: str) -> dict:
        if self.requests >= self.policy["maximum_requests"]:
            raise BoundaryError("REQUEST_BOUND")
        if self.last_request_at is not None:
            delay = self.policy["minimum_interval_seconds"] - (self.monotonic() - self.last_request_at)
            if delay > 0:
                self.sleeper(delay)
        self.last_request_at = self.monotonic()
        self.requests += 1
        request = Request(url, headers={"User-Agent": self.policy["user_agent"], "Accept": self.policy["accept"]}, method="GET")
        try:
            with self.opener.open(request, timeout=self.policy["timeout_seconds"]) as response:
                body = response.read(self.policy["maximum_response_bytes"] + 1)
                if len(body) > self.policy["maximum_response_bytes"]:
                    raise BoundaryError("RESPONSE_BYTE_BOUND")
                if self.bytes + len(body) > self.policy["maximum_total_bytes"]:
                    raise BoundaryError("TOTAL_BYTE_BOUND")
                self.bytes += len(body)
                return {"kind": "response", "status": getattr(response, "status", 200), "url": response.geturl(),
                        "content_type": response.headers.get("Content-Type", ""), "body": body}
        except HTTPError as exc:
            if 300 <= exc.code < 400:
                return {"kind": "redirect", "status": exc.code, "location": exc.headers.get("Location"), "body": b""}
            if exc.code in {401, 403, 429}:
                raise BoundaryError(f"HTTP_{exc.code}") from None
            raise RuntimeError(f"HTTP_{exc.code}") from None
        except (URLError, TimeoutError, ConnectionError) as exc:
            raise RuntimeError(f"NETWORK_ERROR:{type(exc).__name__}") from None


def validate_config(config: dict, root: Path) -> dict:
    if config["restart_cycle_id"] != CYCLE or config["stage"] != "FIN-PIT-1A":
        raise ValueError("cycle/stage mismatch")
    proposal_path = root / config["proposal_path"]
    proposal_sha256 = sha256_file(proposal_path)
    if config["proposal_sha256"] != proposal_sha256:
        raise ValueError("proposal hash mismatch")
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    branch = next(item for item in proposal["branches"] if item["branch_id"] == config["branch_id"])
    frozen_bounds = branch.get("bounds", branch)
    approval = config["approval_record"]
    if approval["decision"] != "APPROVED" or approval["proposal_sha256"] != proposal_sha256:
        raise ValueError("approval mismatch")
    policy = config["network_policy"]
    resume_parent = config.get("redirect_resume_parent")
    if resume_parent:
        parent = root / resume_parent["path"]
        if sha256_file(parent / "manifest.json") != resume_parent["manifest_sha256"]:
            raise ValueError("redirect parent manifest mismatch")
        parent_coverage = json.loads((parent / "coverage.json").read_text(encoding="utf-8"))
        attempts = [json.loads(line) for line in (parent / "request_attempts.jsonl").read_text(encoding="utf-8").splitlines()]
        expected = [item["redirect_target"] for item in attempts if item.get("status") == "REDIRECT_NOT_FOLLOWED" and item.get("redirect_allowed")]
        expected_bounds = dict(frozen_bounds)
        expected_bounds["maximum_requests"] = frozen_bounds["maximum_requests"] - parent_coverage["network_requests"]
        expected_bounds["maximum_total_bytes"] = frozen_bounds["maximum_total_bytes"] - parent_coverage["network_bytes"]
    else:
        expected = branch.get("exact_urls") or branch.get("exact_seeds")
        if expected is None:
            expected = branch["exact_get_seeds"] + branch.get("proposed_unverified_acv_seeds", [])
        expected_bounds = frozen_bounds
    for key in ("maximum_requests", "maximum_documents", "maximum_response_bytes", "maximum_total_bytes", "timeout_seconds", "minimum_interval_seconds", "single_threaded", "retry_count"):
        if policy[key] != expected_bounds[key]:
            raise ValueError(f"bound mismatch: {key}")
    if config["urls"] != expected:
        raise ValueError("exact URL list mismatch")
    if config["branch_id"] == "ROUTE_DISCOVERY_CONTINUATION" and config.get("post_jobs"):
        raise ValueError("HNX POST not approved")
    for parent in config["parent_packages"]:
        if sha256_file(root / parent["path"] / "manifest.json") != parent["manifest_sha256"]:
            raise ValueError("parent manifest mismatch")
    return branch


def load_config(path: Path, root: Path) -> tuple[dict, dict]:
    config = json.loads(path.read_text(encoding="utf-8"))
    return config, validate_config(config, root)


def validate_proposal(path: Path) -> dict:
    proposal = json.loads(path.read_text(encoding="utf-8"))
    if proposal["restart_cycle_id"] != CYCLE or proposal["stage"] != "FIN-PIT-1A":
        raise ValueError("proposal cycle/stage mismatch")
    if proposal["approval_status"] != "PENDING":
        raise ValueError("preflight proposal must remain PENDING")
    seen: set[str] = set()
    totals = {"requests": 0, "documents": 0, "bytes": 0}
    for branch in proposal["branches"]:
        branch_id = branch["branch_id"]
        if branch_id in seen:
            raise ValueError(f"duplicate branch: {branch_id}")
        seen.add(branch_id)
        bounds = branch["bounds"]
        if not bounds["single_threaded"] or bounds["retry_count"] != 0:
            raise ValueError(f"unsafe concurrency/retry policy: {branch_id}")
        if min(bounds["maximum_requests"], bounds["maximum_response_bytes"], bounds["maximum_total_bytes"], bounds["timeout_seconds"]) <= 0:
            raise ValueError(f"non-positive bound: {branch_id}")
        urls = branch.get("exact_urls") or branch.get("exact_seeds") or []
        hosts = set(branch["allowlist"]["hosts"])
        prefixes = branch["allowlist"]["path_prefixes"]
        for url in urls:
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname not in hosts or not any(parsed.path.startswith(prefix) for prefix in prefixes):
                raise ValueError(f"URL outside allowlist: {branch_id}:{url}")
        if branch["operation"] == "document_acquisition" and bounds["maximum_documents"] > len(urls):
            raise ValueError(f"document cap exceeds exact URL count: {branch_id}")
        if branch["operation"] == "html_discovery" and bounds["maximum_documents"] != 0:
            raise ValueError(f"discovery permits documents: {branch_id}")
        totals["requests"] += bounds["maximum_requests"]
        totals["documents"] += bounds["maximum_documents"]
        totals["bytes"] += bounds["maximum_total_bytes"]
    aggregate = proposal["aggregate_maximums"]
    if any(aggregate[key] != value for key, value in totals.items()):
        raise ValueError("aggregate bounds mismatch")
    return {"proposal_sha256": sha256_file(path), "branches": len(seen), **totals, "network_requests": 0, "status": "PENDING_APPROVAL"}


def execute(config_path: Path, root: Path, *, collector: Collector | None = None) -> dict:
    config, branch = load_config(config_path, root)
    output = root / config["output_directory"]
    if output.exists():
        raise FileExistsError(f"immutable output exists: {output}")
    output.mkdir(parents=True)
    policy = config["network_policy"]
    collector = collector or Collector(policy)
    allowlist = branch.get("allowlist", {})
    allowed_hosts = set(branch.get("allowed_hosts", allowlist.get("hosts", [])))
    allowed_prefixes = branch.get("allowed_path_prefixes", allowlist.get("path_prefixes"))
    acquisition = branch.get("operation") == "document_acquisition" or config["branch_id"] == "FPT_EXACT_CANDIDATE_ACQUISITION"
    attempts: list[dict] = []
    documents = 0
    hard_stop = False
    for index, original_url in enumerate(config["urls"], start=1):
        if hard_stop or collector.requests >= policy["maximum_requests"]:
            break
        current_url = original_url
        parsed = urlsplit(current_url)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            raise ValueError("URL host outside frozen allowlist")
        if allowed_prefixes and not any(parsed.path.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError("URL path outside frozen allowlist")
        request_id = f"request-{index:02d}"
        observed = datetime.now(timezone.utc).isoformat()
        persisted: dict | None = None
        try:
            result = collector.get(current_url)
            if result["kind"] == "redirect":
                target = urljoin(current_url, result.get("location") or "")
                allowed = bool(result.get("location")) and _same_issuer_redirect(current_url, target, allowed_hosts)
                attempts.append({"request_id": request_id, "requested_url": current_url, "status": "REDIRECT_NOT_FOLLOWED",
                                 "http_status": result["status"], "redirect_target": target, "redirect_allowed": allowed,
                                 "fetched_at": observed, "bytes": 0, "document_downloaded": False})
                if not allowed:
                    hard_stop = True
                continue
            persisted = _persist_response_before_validation(output, request_id, result, observed)
            response_kind = _validate_persisted_response(result, acquisition=acquisition)
            if acquisition:
                documents += 1
            attempts.append({"request_id": request_id, "requested_url": current_url, "final_url": result["url"], "status": "SUCCESS",
                             "response_kind": response_kind, **persisted, "document_downloaded": acquisition})
        except BoundaryError as exc:
            attempt = {"request_id": request_id, "requested_url": current_url, "status": "HARD_STOP", "error": str(exc),
                       "fetched_at": observed, "bytes": 0, "document_downloaded": False}
            if persisted is not None:
                attempt.update(persisted)
                attempt["document_downloaded"] = False
                attempt["raw_evidence_preserved"] = True
            attempts.append(attempt)
            hard_stop = True
        except Exception as exc:
            attempts.append({"request_id": request_id, "requested_url": current_url, "status": "ERROR", "error": f"{type(exc).__name__}:{exc}",
                             "fetched_at": observed, "bytes": 0, "document_downloaded": False})
    immutable_write(output / "approval_record.json", canonical_bytes(config["approval_record"]))
    immutable_write(output / "request_attempts.jsonl", b"".join(canonical_bytes(item) for item in attempts))
    coverage = {"restart_cycle_id": CYCLE, "run_id": config["run_id"], "branch_id": config["branch_id"],
                "network_requests": collector.requests, "network_bytes": collector.bytes, "documents_downloaded": documents,
                "planned_urls": len(config["urls"]), "successful_responses": sum(item["status"] == "SUCCESS" for item in attempts),
                "hard_stop": hard_stop, "post_requests": 0, "canonical_rows_written": 0, "financial_features_written": 0}
    immutable_write(output / "coverage.json", canonical_bytes(coverage))
    immutable_write(output / "gate.json", canonical_bytes({"restart_cycle_id": CYCLE, "run_id": config["run_id"], "stage": "FIN-PIT-1A",
        "branch_id": config["branch_id"], "status": "MANUAL_REVIEW_REQUIRED", "execution_bounds_pass": collector.requests <= policy["maximum_requests"],
        "content_review_pending": True, "timing_usable": False, "next_stage_allowed": False, "stop_condition_confirmed": True}))
    immutable_write(output / "stage_handoff.md", (f"# FIN-PIT-1A {config['branch_id']} execution\n\nNETWORK_REQUESTS: {collector.requests}\nNETWORK_BYTES: {collector.bytes}\nDOCUMENTS_DOWNLOADED: {documents}\nSTATUS: MANUAL_REVIEW_REQUIRED\nCANONICAL_ROWS_WRITTEN: 0\nFINANCIAL_FEATURES_WRITTEN: 0\nSTOP CONDITION CONFIRMED: YES\n").encode("utf-8"))
    payloads = sorted(path for path in output.rglob("*") if path.is_file() and path.name not in {"manifest.json", "checksums.json"})
    checks = [{"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in payloads]
    immutable_write(output / "checksums.json", canonical_bytes({"algorithm": "sha256", "files": checks}))
    immutable_write(output / "manifest.json", canonical_bytes({"restart_cycle_id": CYCLE, "run_id": config["run_id"], "stage": "FIN-PIT-1A",
        "branch_id": config["branch_id"], "status": "MANUAL_REVIEW_REQUIRED", "execution_mode": "AI_EXECUTES",
        "proposal_sha256": config["proposal_sha256"], "config_sha256": sha256_file(config_path), "parent_runs": config["parent_packages"],
        **coverage, "output_artifacts": checks + [{"path": "checksums.json", "sha256": sha256_file(output / "checksums.json")},
        {"path": "manifest.json", "sha256": None, "reason": "self hash excluded"}]}))
    return coverage


def verify_existing(config_path: Path, root: Path) -> dict:
    config, _ = load_config(config_path, root)
    output = root / config["output_directory"]
    checks = json.loads((output / "checksums.json").read_text(encoding="utf-8"))
    for entry in checks["files"]:
        path = output / entry["path"]
        if not path.is_file() or path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            raise ValueError(f"checksum mismatch: {entry['path']}")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if manifest["config_sha256"] != sha256_file(config_path):
        raise ValueError("config hash mismatch")
    return {"run_id": manifest["run_id"], "branch_id": manifest["branch_id"], "network_requests": manifest["network_requests"],
            "network_bytes": manifest["network_bytes"], "documents_downloaded": manifest["documents_downloaded"],
            "verified_payload_count": len(checks["files"])}
