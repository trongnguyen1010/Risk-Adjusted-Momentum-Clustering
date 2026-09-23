#!/usr/bin/env python3
"""Sequential, resumable raw-only runner for the frozen CafeF C1-SOLO v2 plan.

This file is prepared in C1-PREP-SOLO but must not be executed against CafeF until the
user has manually reviewed the plan and explicitly approved C1-SOLO.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "docs/crawl/plans/cafef_c1_solo_v2"
ARTIFACT_ROOT = ROOT / "artifacts/cafef_primary"
PLAN_FILES = (
    "cafef_c1_solo_selected_pilot.csv",
    "cafef_c1_solo_execution_order.csv",
    "cafef_c1_solo_request_estimates.csv",
    "cafef_c1_solo_contract.json",
    "cafef_c1_solo_failure_policy.json",
    "cafef_c1_solo_resume_contract.json",
)


class RunnerError(RuntimeError):
    pass


class AccessControlStop(RunnerError):
    pass


class TransientRequestError(RunnerError):
    pass


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str


class UrlLibClient:
    def get(self, url: str, params: dict[str, str], timeout: float, max_bytes: int) -> HttpResponse:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            full_url,
            headers={"User-Agent": "DELTA-CafeF-C1-Solo/2.0 raw-evidence research pilot"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise RunnerError("response exceeds frozen maximum_response_bytes")
                return HttpResponse(
                    status=int(response.status),
                    headers={key: value for key, value in response.headers.items()},
                    body=body,
                    url=full_url,
                )
        except urllib.error.HTTPError as exc:
            body = exc.read(max_bytes + 1)
            return HttpResponse(int(exc.code), dict(exc.headers.items()), body, full_url)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TransientRequestError(str(exc)) from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
        for attempt in range(5):
            try:
                os.replace(name, path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.05 * (attempt + 1))
    finally:
        if os.path.exists(name):
            os.unlink(name)


def append_jsonl(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _code_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return f"script-sha256:{sha256_file(Path(__file__))}"


def load_frozen_plan(plan_dir: Path = PLAN_DIR) -> tuple[list[dict[str, str]], dict, dict, dict, dict]:
    manifest = _read_json(plan_dir / "manifest.json")
    contract = _read_json(plan_dir / "cafef_c1_solo_contract.json")
    failure = _read_json(plan_dir / "cafef_c1_solo_failure_policy.json")
    resume = _read_json(plan_dir / "cafef_c1_solo_resume_contract.json")
    with (plan_dir / "cafef_c1_solo_execution_order.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    orders = [int(row["execution_order"]) for row in rows]
    if orders != list(range(1, len(rows) + 1)):
        raise RunnerError("frozen execution_order is not contiguous and deterministic")
    if any(row["target_end"] != contract["collection_end_date"] for row in rows):
        raise RunnerError("plan target_end differs from frozen collection_end_date")
    expected_hashes = manifest["output_hashes"]
    for name in PLAN_FILES:
        actual = sha256_file(plan_dir / name)
        if expected_hashes.get(name) != actual:
            raise RunnerError(f"frozen plan checksum mismatch: {name}")
    plan_hash = sha256_bytes(b"".join((plan_dir / name).read_bytes() for name in sorted(PLAN_FILES)))
    if plan_hash != manifest["plan_hash"]:
        raise RunnerError("frozen plan hash mismatch")
    return rows, manifest, contract, failure, resume


def iter_calendar_year_ranges(start: date, end: date) -> Iterable[tuple[date, date]]:
    cursor = start
    while cursor <= end:
        range_end = min(end, date(cursor.year, 12, 31))
        yield cursor, range_end
        cursor = date(cursor.year + 1, 1, 1)


def raw_output_path(run_dir: Path, ticker: str, start: date, end: date, page: int) -> Path:
    return run_dir / "raw" / ticker / f"{start.isoformat()}_{end.isoformat()}" / f"page_{page:04d}.json"


def metadata_output_path(raw_path: Path) -> Path:
    return raw_path.with_suffix(".meta.json")


def request_key(row: dict[str, str], start: date, end: date, page: int) -> str:
    return f"{row['security_id']}|{start.isoformat()}|{end.isoformat()}|{page:04d}"


def _exchange_type(exchange: str) -> str:
    mapping = {"HOSE": "1", "HNX": "2", "UPCOM": "3"}
    try:
        return mapping[exchange]
    except KeyError as exc:
        raise RunnerError(f"unsupported frozen exchange: {exchange}") from exc


def _parse_envelope(body: bytes) -> tuple[list[dict], int]:
    try:
        payload = json.loads(body.decode("utf-8-sig"))
        data = payload["Data"]
        rows = data["Data"]
        total = int(data["TotalCount"])
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RunnerError("CafeF response does not match frozen PriceHistory envelope") from exc
    if not isinstance(rows, list) or total < 0:
        raise RunnerError("invalid PriceHistory rows or TotalCount")
    return rows, total


def _row_diagnostics(rows: list[dict], start: date, end: date, seen_dates: set[str]) -> dict:
    parsed: list[date] = []
    duplicate_count = 0
    out_of_window_count = 0
    row_dates: list[str] = []
    for row in rows:
        raw_date = row.get("Ngay")
        if not isinstance(raw_date, str):
            raise RunnerError("PriceHistory row missing Ngay")
        try:
            parsed_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
        except ValueError as exc:
            raise RunnerError(f"invalid PriceHistory Ngay: {raw_date}") from exc
        iso_date = parsed_date.isoformat()
        if iso_date in seen_dates:
            duplicate_count += 1
        seen_dates.add(iso_date)
        row_dates.append(iso_date)
        parsed.append(parsed_date)
        if parsed_date < start or parsed_date > end:
            out_of_window_count += 1
    return {
        "row_dates": row_dates,
        "earliest_date": min(parsed).isoformat() if parsed else None,
        "latest_date": max(parsed).isoformat() if parsed else None,
        "duplicate_date_count": duplicate_count,
        "out_of_window_row_count": out_of_window_count,
    }


def _access_control_reason(response: HttpResponse, contract: dict) -> str | None:
    policy = contract["request_policy"]
    if response.status in policy["stop_http_status"]:
        return f"HTTP_{response.status}"
    sample = response.body[:200_000].decode("utf-8", errors="ignore").lower()
    for marker in policy["stop_body_markers"]:
        if marker.lower() in sample:
            return f"BODY_MARKER_{marker.upper().replace(' ', '_')}"
    return None


def _validated_resume_skip(run_dir: Path, entry: dict) -> bool:
    path = run_dir / entry["raw_path"]
    return path.is_file() and sha256_file(path) == entry["sha256"]


def _request_with_retry(
    client: object,
    url: str,
    params: dict[str, str],
    contract: dict,
    sleep: Callable[[float], None],
) -> tuple[HttpResponse, int]:
    policy = contract["request_policy"]
    attempts = int(policy["maximum_attempts"])
    retryable_status = set(policy["retryable_http_status"])
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = client.get(url, params, float(policy["timeout_seconds"]), int(policy["maximum_response_bytes"]))
            access_reason = _access_control_reason(response, contract)
            if access_reason:
                raise AccessControlStop(access_reason)
            if response.status in retryable_status:
                raise TransientRequestError(f"HTTP_{response.status}")
            if response.status != 200:
                raise RunnerError(f"non-success HTTP status {response.status}")
            return response, attempt
        except AccessControlStop:
            raise
        except TransientRequestError as exc:
            last_error = exc
            if attempt >= attempts:
                break
            backoffs = policy["transient_backoff_seconds"]
            sleep(float(backoffs[min(attempt - 1, len(backoffs) - 1)]))
    raise TransientRequestError(f"bounded retry exhausted after {attempts} attempts: {last_error}")


def _new_run_id(plan_hash: str, now: datetime) -> str:
    return f"cafef-c1-solo-{now.strftime('%Y%m%dT%H%M%SZ')}-{plan_hash[:10]}"


def _initialize_run(run_dir: Path, plan_dir: Path, manifest: dict, contract: dict, now: datetime) -> tuple[dict, dict]:
    if run_dir.exists():
        raise RunnerError(f"run directory already exists: {run_dir}")
    snapshot = run_dir / "plan_snapshot"
    snapshot.mkdir(parents=True)
    for name in (*PLAN_FILES, "manifest.json"):
        shutil.copy2(plan_dir / name, snapshot / name)
    identity = {
        "run_id": run_dir.name,
        "stage": "C1-SOLO",
        "status": "RUNNING",
        "plan_id": manifest["plan_id"],
        "plan_hash": manifest["plan_hash"],
        "contract_version": contract["contract_version"],
        "code_version": _code_version(),
        "collection_end_date": contract["collection_end_date"],
        "hard_lower_date_boundary": contract["hard_lower_date_boundary"],
        "created_at": now.isoformat(),
        "raw_only": True,
        "canonical_mutations": 0,
        "feature_rebuild": False,
    }
    progress = {"identity": identity, "completed": {}, "status": "RUNNING", "request_count": 0}
    atomic_write(run_dir / "manifest.json", stable_json_bytes(identity))
    atomic_write(run_dir / "progress.json", stable_json_bytes(progress))
    return identity, progress


def _load_resume(run_dir: Path, manifest: dict, contract: dict) -> tuple[dict, dict]:
    identity = _read_json(run_dir / "manifest.json")
    progress = _read_json(run_dir / "progress.json")
    expected = {
        "plan_id": manifest["plan_id"],
        "plan_hash": manifest["plan_hash"],
        "contract_version": contract["contract_version"],
        "code_version": _code_version(),
        "collection_end_date": contract["collection_end_date"],
        "hard_lower_date_boundary": contract["hard_lower_date_boundary"],
    }
    mismatches = {key: (identity.get(key), value) for key, value in expected.items() if identity.get(key) != value}
    if mismatches:
        raise RunnerError(f"resume identity mismatch: {mismatches}")
    for key, entry in progress.get("completed", {}).items():
        if not _validated_resume_skip(run_dir, entry):
            raise RunnerError(f"resume checksum mismatch: {key}")
    progress["status"] = "RUNNING"
    return identity, progress


def run_solo(
    *,
    plan_dir: Path = PLAN_DIR,
    artifact_root: Path = ARTIFACT_ROOT,
    execute: bool,
    resume: bool = False,
    run_id: str | None = None,
    max_requests: int | None = None,
    only_ticker: str | None = None,
    client: object | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> Path:
    if not execute:
        raise RunnerError("refusing to run without explicit --execute")
    rows, plan_manifest, contract, _failure, _resume_contract = load_frozen_plan(plan_dir)
    if only_ticker:
        only_ticker = only_ticker.upper()
        rows = [row for row in rows if row["ticker"] == only_ticker]
        if len(rows) != 1:
            raise RunnerError("--only-ticker must name exactly one ticker in the frozen plan")
    if any(row["crawl_allowed"] != "YES" for row in rows):
        raise RunnerError("frozen plan contains a selected row that is not crawl_allowed")

    current_time = now()
    if resume:
        if not run_id:
            raise RunnerError("--resume requires --run-id")
        run_dir = artifact_root / run_id
        identity, progress = _load_resume(run_dir, plan_manifest, contract)
    else:
        run_id = run_id or _new_run_id(plan_manifest["plan_hash"], current_time)
        run_dir = artifact_root / run_id
        identity, progress = _initialize_run(run_dir, plan_dir, plan_manifest, contract, current_time)

    http = client or UrlLibClient()
    requests_this_invocation = 0
    interval = float(contract["request_policy"]["minimum_request_interval_seconds"])
    last_request_at: float | None = None
    try:
        for row in rows:
            start = date.fromisoformat(row["target_start"])
            end = date.fromisoformat(row["target_end"])
            for range_start, range_end in iter_calendar_year_ranges(start, end):
                page = 1
                expected_pages: int | None = None
                seen_dates: set[str] = set()
                while expected_pages is None or page <= expected_pages:
                    if max_requests is not None and requests_this_invocation >= max_requests:
                        progress["status"] = "PAUSED_MAX_REQUESTS"
                        atomic_write(run_dir / "progress.json", stable_json_bytes(progress))
                        return run_dir
                    key = request_key(row, range_start, range_end, page)
                    prior = progress["completed"].get(key)
                    if prior:
                        if not _validated_resume_skip(run_dir, prior):
                            raise RunnerError(f"completed raw checksum invalid: {key}")
                        seen_dates.update(prior.get("row_dates", []))
                        expected_pages = int(prior["expected_pages"])
                        page += 1
                        continue
                    raw_path = raw_output_path(run_dir, row["ticker"], range_start, range_end, page)
                    if raw_path.exists():
                        sidecar_path = metadata_output_path(raw_path)
                        if not sidecar_path.is_file():
                            raise RunnerError(f"refusing to overwrite untracked raw response: {raw_path}")
                        recovered = _read_json(sidecar_path)
                        if recovered.get("request_key") != key or recovered.get("sha256") != sha256_file(raw_path):
                            raise RunnerError(f"untracked raw sidecar mismatch: {raw_path}")
                        recovered["recovered_from_sidecar"] = True
                        append_jsonl(run_dir / "request_log.jsonl", recovered)
                        progress["completed"][key] = recovered
                        progress["request_count"] = len(progress["completed"])
                        atomic_write(run_dir / "progress.json", stable_json_bytes(progress))
                        seen_dates.update(recovered.get("row_dates", []))
                        expected_pages = int(recovered["expected_pages"])
                        page += 1
                        continue
                    if last_request_at is not None:
                        sleep(max(0.0, interval - (time.monotonic() - last_request_at)))
                    params = {
                        "ExchangeType": _exchange_type(row["exchange"]),
                        "Symbol": row["ticker"],
                        "StartDate": range_start.strftime("%m/%d/%Y"),
                        "EndDate": range_end.strftime("%m/%d/%Y"),
                        "PageIndex": str(page),
                        "PageSize": str(contract["request_surface"]["page_size"]),
                    }
                    response, attempts = _request_with_retry(http, contract["request_surface"]["base_url"], params, contract, sleep)
                    last_request_at = time.monotonic()
                    requests_this_invocation += 1
                    rows_data, total_count = _parse_envelope(response.body)
                    if len(rows_data) > int(contract["request_surface"]["page_size"]):
                        raise RunnerError("PriceHistory response exceeds frozen page_size")
                    diagnostics = _row_diagnostics(rows_data, range_start, range_end, seen_dates)
                    expected_pages = max(1, (total_count + int(contract["request_surface"]["page_size"]) - 1) // int(contract["request_surface"]["page_size"]))
                    if expected_pages > int(contract["request_surface"]["max_pages_per_range"]):
                        raise RunnerError("validated TotalCount exceeds frozen max_pages_per_range")
                    atomic_write(raw_path, response.body)
                    digest = sha256_bytes(response.body)
                    relative = raw_path.relative_to(run_dir).as_posix()
                    fetched_at = now().isoformat()
                    log_entry = {
                        "request_key": key,
                        "ticker": row["ticker"],
                        "security_id": row["security_id"],
                        "exchange": row["exchange"],
                        "identity_intervals": json.loads(row["identity_intervals"]),
                        "requested_start": range_start.isoformat(),
                        "requested_end": range_end.isoformat(),
                        "page": page,
                        "page_size": contract["request_surface"]["page_size"],
                        "request_url": response.url,
                        "request_params": params,
                        "http_status": response.status,
                        "fetched_at": fetched_at,
                        "byte_size": len(response.body),
                        "sha256": digest,
                        "raw_path": relative,
                        "row_count": len(rows_data),
                        "total_count": total_count,
                        "expected_pages": expected_pages,
                        "attempts": attempts,
                        "contract_version": contract["contract_version"],
                        "empty_classification": "PROVIDER_EMPTY_RESPONSE_UNRESOLVED" if total_count == 0 else "NONEMPTY",
                        **diagnostics,
                    }
                    atomic_write(metadata_output_path(raw_path), stable_json_bytes(log_entry))
                    append_jsonl(run_dir / "request_log.jsonl", log_entry)
                    progress["completed"][key] = log_entry
                    progress["request_count"] = len(progress["completed"])
                    atomic_write(run_dir / "progress.json", stable_json_bytes(progress))
                    page += 1
        progress["status"] = "COMPLETED"
        identity["status"] = "COMPLETED"
        identity["completed_at"] = now().isoformat()
        atomic_write(run_dir / "progress.json", stable_json_bytes(progress))
        atomic_write(run_dir / "manifest.json", stable_json_bytes(identity))
        return run_dir
    except Exception as exc:
        failure = {
            "failed_at": now().isoformat(),
            "error_type": type(exc).__name__,
            "message": str(exc),
            "access_control_stop": isinstance(exc, AccessControlStop),
        }
        append_jsonl(run_dir / "failures.jsonl", failure)
        progress["status"] = "STOPPED_ACCESS_CONTROL" if isinstance(exc, AccessControlStop) else "FAILED"
        atomic_write(run_dir / "progress.json", stable_json_bytes(progress))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen sequential CafeF C1-SOLO raw acquisition")
    parser.add_argument("--execute", action="store_true", help="required explicit execution gate")
    parser.add_argument("--resume", action="store_true", help="resume an existing checksum-valid run")
    parser.add_argument("--run-id", help="new explicit run id, or existing run id with --resume")
    parser.add_argument("--max-requests", type=int, help="pause after this many HTTP requests in this invocation")
    parser.add_argument("--only-ticker", help="debug one ticker while preserving its frozen contract and boundaries")
    args = parser.parse_args()
    if args.max_requests is not None and args.max_requests < 1:
        parser.error("--max-requests must be positive")
    try:
        run_dir = run_solo(
            execute=args.execute,
            resume=args.resume,
            run_id=args.run_id,
            max_requests=args.max_requests,
            only_ticker=args.only_ticker,
        )
    except RunnerError as exc:
        parser.error(str(exc))
    print(json.dumps({"run_directory": str(run_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
