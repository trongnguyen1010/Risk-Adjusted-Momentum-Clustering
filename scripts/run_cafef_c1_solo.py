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
from datetime import date, datetime, timedelta, timezone
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


class ReceivedResponseError(RunnerError):
    def __init__(self, message: str, *, response: HttpResponse | None = None, attempts: int | None = None):
        super().__init__(message)
        self.response = response
        self.attempts = attempts


class AccessControlStop(ReceivedResponseError):
    pass


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str


class TransientRequestError(ReceivedResponseError):
    pass


class HttpResponseRejected(ReceivedResponseError):
    pass


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
            if len(body) > max_bytes:
                raise RunnerError("response exceeds frozen maximum_response_bytes")
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
    fd, name = tempfile.mkstemp(prefix=".tmp.", dir=path.parent)
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


def calendar_quarter(value: date) -> tuple[int, int]:
    return value.year, ((value.month - 1) // 3) + 1


def validate_calendar_quarter_range(start: date, end: date) -> None:
    if start > end:
        raise RunnerError("request range start must not be after end")
    if calendar_quarter(start) != calendar_quarter(end):
        raise RunnerError("request range must remain within one calendar quarter")


def iter_calendar_quarter_intersections(start: date, end: date) -> Iterable[tuple[date, date]]:
    if start > end:
        raise RunnerError("range start must not be after end")
    cursor = start
    while cursor <= end:
        quarter_start_month = ((cursor.month - 1) // 3) * 3 + 1
        next_quarter_month = quarter_start_month + 3
        if next_quarter_month == 13:
            next_quarter_start = date(cursor.year + 1, 1, 1)
        else:
            next_quarter_start = date(cursor.year, next_quarter_month, 1)
        range_end = min(end, next_quarter_start - timedelta(days=1))
        yield cursor, range_end
        cursor = range_end + timedelta(days=1)


def identity_request_segments(row: dict[str, str]) -> list[dict]:
    try:
        intervals = json.loads(row["identity_intervals"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RunnerError(f"invalid frozen identity_intervals for {row.get('ticker', '<unknown>')}") from exc
    if not isinstance(intervals, list) or not intervals:
        raise RunnerError(f"crawlable row has no identity intervals: {row.get('ticker', '<unknown>')}")
    target_start = date.fromisoformat(row["target_start"])
    target_end = date.fromisoformat(row["target_end"])
    segments: list[dict] = []
    for interval in intervals:
        if not isinstance(interval, dict):
            raise RunnerError("identity interval must be an object")
        try:
            interval_start = date.fromisoformat(interval["effective_from"])
            interval_end = date.fromisoformat(interval["effective_to"]) if interval.get("effective_to") else target_end
            exchange = interval["exchange"].upper()
            ticker = interval["ticker"].upper()
        except (KeyError, AttributeError, TypeError, ValueError) as exc:
            raise RunnerError(f"invalid identity interval for {row['ticker']}") from exc
        if exchange not in {"HOSE", "HNX", "UPCOM"}:
            raise RunnerError(f"unsupported frozen interval exchange: {exchange}")
        request_start = max(target_start, interval_start)
        request_end = min(target_end, interval_end)
        if request_start > request_end:
            continue
        segments.append({
            "ticker": ticker,
            "exchange": exchange,
            "interval_effective_from": interval_start,
            "interval_effective_to": date.fromisoformat(interval["effective_to"]) if interval.get("effective_to") else None,
            "request_start": request_start,
            "request_end": request_end,
        })
    segments.sort(key=lambda item: (item["request_start"], item["exchange"], item["ticker"]))
    if not segments:
        raise RunnerError(f"no identity interval intersects target window: {row['ticker']}")
    for previous, current in zip(segments, segments[1:]):
        if current["request_start"] <= previous["request_end"]:
            raise RunnerError(f"overlapping identity intervals for {row['ticker']}")
    return segments


def iter_identity_calendar_quarter_ranges(row: dict[str, str]) -> Iterable[tuple[dict, date, date]]:
    for segment in identity_request_segments(row):
        for range_start, range_end in iter_calendar_quarter_intersections(
            segment["request_start"], segment["request_end"]
        ):
            yield segment, range_start, range_end


def raw_output_path(
    run_dir: Path,
    ticker: str,
    exchange: str,
    interval_effective_from: date,
    interval_effective_to: date | None,
    start: date,
    end: date,
    page: int,
) -> Path:
    interval_label = f"identity_{interval_effective_from.isoformat()}_{interval_effective_to.isoformat() if interval_effective_to else 'OPEN'}"
    return (
        run_dir / "raw" / ticker / exchange / interval_label
        / f"{start.isoformat()}_{end.isoformat()}" / f"page_{page:04d}.json"
    )


def metadata_output_path(raw_path: Path) -> Path:
    return raw_path.with_suffix(".meta.json")


def failure_raw_output_path(
    run_dir: Path,
    ticker: str,
    exchange: str,
    interval_effective_from: date,
    interval_effective_to: date | None,
    start: date,
    end: date,
    page: int,
    digest: str,
) -> Path:
    interval_label = f"identity_{interval_effective_from.isoformat()}_{interval_effective_to.isoformat() if interval_effective_to else 'OPEN'}"
    return (
        run_dir / "failure_raw" / ticker / exchange / interval_label
        / f"{start.isoformat()}_{end.isoformat()}" / f"page_{page:04d}_{digest[:16]}.json"
    )


def _response_content_type(response: HttpResponse) -> str | None:
    return next((value for key, value in response.headers.items() if key.lower() == "content-type"), None)


def _preserve_failed_response(
    *,
    run_dir: Path,
    row: dict[str, str],
    segment: dict,
    start: date,
    end: date,
    page: int,
    page_size: int,
    key: str,
    params: dict[str, str],
    response: HttpResponse,
    attempts: int | None,
    contract_version: str,
    error: Exception,
    fetched_at: str,
) -> dict:
    digest = sha256_bytes(response.body)
    evidence_path = failure_raw_output_path(
        run_dir, segment["ticker"], segment["exchange"],
        segment["interval_effective_from"], segment["interval_effective_to"],
        start, end, page, digest,
    )
    if evidence_path.exists():
        if sha256_file(evidence_path) != digest:
            raise RunnerError(f"refusing to overwrite different failure evidence: {evidence_path}")
    else:
        atomic_write(evidence_path, response.body)
    entry = {
        "request_key": key,
        "security_id": row["security_id"],
        "ticker": segment["ticker"],
        "exchange": segment["exchange"],
        "identity_interval_effective_from": segment["interval_effective_from"].isoformat(),
        "identity_interval_effective_to": segment["interval_effective_to"].isoformat() if segment["interval_effective_to"] else None,
        "requested_start": start.isoformat(),
        "requested_end": end.isoformat(),
        "page": page,
        "page_size": page_size,
        "request_url": response.url,
        "request_params": params,
        "http_status": response.status,
        "response_content_type": _response_content_type(response),
        "fetched_at": fetched_at,
        "byte_size": len(response.body),
        "sha256": digest,
        "failure_raw_path": evidence_path.relative_to(run_dir).as_posix(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "contract_version": contract_version,
        "semantic_status": "REJECTED",
        "attempts": attempts,
        "access_control_stop": isinstance(error, AccessControlStop),
    }
    sidecar_path = metadata_output_path(evidence_path)
    if not sidecar_path.exists():
        atomic_write(sidecar_path, stable_json_bytes(entry))
    append_jsonl(run_dir / "failures.jsonl", entry)
    return entry


def request_key(row: dict[str, str], segment: dict, start: date, end: date, page: int) -> str:
    interval_end = segment["interval_effective_to"].isoformat() if segment["interval_effective_to"] else "OPEN"
    return "|".join([
        row["security_id"], segment["ticker"], segment["exchange"],
        segment["interval_effective_from"].isoformat(), interval_end,
        start.isoformat(), end.isoformat(), f"{page:04d}",
    ])


def build_request_params(segment: dict, start: date, end: date, page: int, page_size: int) -> dict[str, str]:
    validate_calendar_quarter_range(start, end)
    exchange = segment["exchange"]
    if exchange not in {"HOSE", "HNX", "UPCOM"}:
        raise RunnerError(f"unsupported frozen interval exchange: {exchange}")
    return {
        "ExchangeType": exchange,
        "Symbol": segment["ticker"],
        "StartDate": start.strftime("%m/%d/%Y"),
        "EndDate": end.strftime("%m/%d/%Y"),
        "PageIndex": str(page),
        "PageSize": str(page_size),
    }


def _parse_envelope(body: bytes) -> tuple[list[dict], int]:
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RunnerError("CafeF response does not match frozen PriceHistory envelope") from exc
    if not isinstance(payload, dict) or payload.get("Success") is not True:
        raise RunnerError("CafeF PriceHistory envelope requires Success=true")
    data = payload.get("Data")
    if not isinstance(data, dict):
        raise RunnerError("CafeF PriceHistory Data must be an object")
    rows = data.get("Data")
    total = data.get("TotalCount")
    if not isinstance(rows, list) or type(total) is not int or total < 0:
        raise RunnerError("invalid PriceHistory rows or TotalCount")
    if total == 0 and rows:
        raise RunnerError("PriceHistory TotalCount=0 is inconsistent with non-empty rows")
    if total < len(rows):
        raise RunnerError("PriceHistory TotalCount is smaller than returned row count")
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
                raise AccessControlStop(access_reason, response=response, attempts=attempt)
            if response.status in retryable_status:
                raise TransientRequestError(f"HTTP_{response.status}", response=response, attempts=attempt)
            if response.status != 200:
                raise HttpResponseRejected(
                    f"non-success HTTP status {response.status}", response=response, attempts=attempt
                )
            return response, attempt
        except AccessControlStop:
            raise
        except TransientRequestError as exc:
            last_error = exc
            if attempt >= attempts:
                break
            backoffs = policy["transient_backoff_seconds"]
            sleep(float(backoffs[min(attempt - 1, len(backoffs) - 1)]))
    final_response = last_error.response if isinstance(last_error, ReceivedResponseError) else None
    raise TransientRequestError(
        f"bounded retry exhausted after {attempts} attempts: {last_error}",
        response=final_response,
        attempts=attempts,
    )


def _new_run_id(plan_hash: str, now: datetime) -> str:
    return f"cafef-c1-solo-{now.strftime('%Y%m%dT%H%M%SZ')}-{plan_hash[:10]}"


def _initialize_run(
    run_dir: Path, plan_dir: Path, manifest: dict, contract: dict, resume_contract: dict, now: datetime
) -> tuple[dict, dict]:
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
        "resume_contract_version": resume_contract["contract_version"],
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


def _load_resume(run_dir: Path, manifest: dict, contract: dict, resume_contract: dict) -> tuple[dict, dict]:
    identity = _read_json(run_dir / "manifest.json")
    progress = _read_json(run_dir / "progress.json")
    expected = {
        "plan_id": manifest["plan_id"],
        "plan_hash": manifest["plan_hash"],
        "contract_version": contract["contract_version"],
        "resume_contract_version": resume_contract["contract_version"],
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
    rows, plan_manifest, contract, _failure, resume_contract = load_frozen_plan(plan_dir)
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
        identity, progress = _load_resume(run_dir, plan_manifest, contract, resume_contract)
    else:
        run_id = run_id or _new_run_id(plan_manifest["plan_hash"], current_time)
        run_dir = artifact_root / run_id
        identity, progress = _initialize_run(run_dir, plan_dir, plan_manifest, contract, resume_contract, current_time)

    http = client or UrlLibClient()
    requests_this_invocation = 0
    interval = float(contract["request_policy"]["minimum_request_interval_seconds"])
    last_request_at: float | None = None
    failure_evidence: dict | None = None
    try:
        for row in rows:
            for segment, range_start, range_end in iter_identity_calendar_quarter_ranges(row):
                page = 1
                expected_pages: int | None = None
                expected_total_count: int | None = None
                seen_dates: set[str] = set()
                while expected_pages is None or page <= expected_pages:
                    if max_requests is not None and requests_this_invocation >= max_requests:
                        progress["status"] = "PAUSED_MAX_REQUESTS"
                        atomic_write(run_dir / "progress.json", stable_json_bytes(progress))
                        return run_dir
                    key = request_key(row, segment, range_start, range_end, page)
                    prior = progress["completed"].get(key)
                    if prior:
                        if not _validated_resume_skip(run_dir, prior):
                            raise RunnerError(f"completed raw checksum invalid: {key}")
                        seen_dates.update(prior.get("row_dates", []))
                        expected_pages = int(prior["expected_pages"])
                        expected_total_count = int(prior["total_count"])
                        page += 1
                        continue
                    raw_path = raw_output_path(
                        run_dir, segment["ticker"], segment["exchange"],
                        segment["interval_effective_from"], segment["interval_effective_to"],
                        range_start, range_end, page,
                    )
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
                        expected_total_count = int(recovered["total_count"])
                        page += 1
                        continue
                    if last_request_at is not None:
                        sleep(max(0.0, interval - (time.monotonic() - last_request_at)))
                    params = build_request_params(
                        segment, range_start, range_end, page,
                        int(contract["request_surface"]["page_size"]),
                    )
                    response: HttpResponse | None = None
                    attempts: int | None = None
                    failure_evidence = None
                    try:
                        response, attempts = _request_with_retry(
                            http, contract["request_surface"]["base_url"], params, contract, sleep
                        )
                        last_request_at = time.monotonic()
                        requests_this_invocation += 1
                        rows_data, total_count = _parse_envelope(response.body)
                        if len(rows_data) > int(contract["request_surface"]["page_size"]):
                            raise RunnerError("PriceHistory response exceeds frozen page_size")
                        if expected_total_count is not None and total_count != expected_total_count:
                            raise RunnerError("PriceHistory TotalCount changed within a paginated range")
                        diagnostics = _row_diagnostics(rows_data, range_start, range_end, seen_dates)
                        expected_pages = (total_count + int(contract["request_surface"]["page_size"]) - 1) // int(contract["request_surface"]["page_size"])
                        expected_total_count = total_count
                        if total_count > 0 and not rows_data and page <= expected_pages:
                            raise RunnerError("PriceHistory returned an empty page inside the validated page range")
                        if expected_pages > int(contract["request_surface"]["max_pages_per_range"]):
                            raise RunnerError("validated TotalCount exceeds frozen max_pages_per_range")
                    except Exception as request_error:
                        rejected_response = response
                        rejected_attempts = attempts
                        if isinstance(request_error, ReceivedResponseError):
                            rejected_response = rejected_response or request_error.response
                            rejected_attempts = rejected_attempts or request_error.attempts
                        if rejected_response is not None:
                            failure_evidence = _preserve_failed_response(
                                run_dir=run_dir, row=row, segment=segment,
                                start=range_start, end=range_end, page=page,
                                page_size=int(contract["request_surface"]["page_size"]),
                                key=key, params=params, response=rejected_response,
                                attempts=rejected_attempts,
                                contract_version=contract["contract_version"],
                                error=request_error, fetched_at=now().isoformat(),
                            )
                        raise
                    atomic_write(raw_path, response.body)
                    digest = sha256_bytes(response.body)
                    relative = raw_path.relative_to(run_dir).as_posix()
                    fetched_at = now().isoformat()
                    log_entry = {
                        "request_key": key,
                        "ticker": segment["ticker"],
                        "security_id": row["security_id"],
                        "exchange": segment["exchange"],
                        "identity_interval_effective_from": segment["interval_effective_from"].isoformat(),
                        "identity_interval_effective_to": segment["interval_effective_to"].isoformat() if segment["interval_effective_to"] else None,
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
        if failure_evidence is None:
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
