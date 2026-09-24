#!/usr/bin/env python3
"""Audit stopped CafeF V2.3 evidence and build the frozen C1 history V3 plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
V2_PLAN_DIR = ROOT / "docs/crawl/plans/cafef_c1_solo_v2"
DEFAULT_OUTPUT_DIR = ROOT / "docs/crawl/plans/cafef_c1_history_v3"
DEFAULT_SOURCE_RUN = ROOT / "artifacts/cafef_primary/cafef-c1-solo-main-v2"
DEFAULT_REGISTRY_DIR = ROOT / "artifacts/cafef_primary/history_registry_v1"

PLAN_ID = "cafef-c1-history-v3"
PLAN_VERSION = "3.0.0"
HISTORY_POLICY = "HISTORY_POLICY_V3"
RAW_CONTRACT_VERSION = "CAFEF_C1_SOLO_RAW_CONTRACT_V3_0"
RESUME_CONTRACT_VERSION = "CAFEF_C1_SOLO_RESUME_V3_0"
SOURCE_CONTRACT_VERSION = "CAFEF_C1_SOLO_RAW_CONTRACT_V2_3"
COLLECTION_END = date(2026, 9, 23)
BASE_LOWER_BOUND = date(2021, 9, 23)
DEEP_LOWER_BOUND = date(2016, 9, 23)
PAGE_SIZE = 20
DEEP_SELECTOR_SEED = "CAFEF_HISTORY_POLICY_V3_DEEP_10Y_SEED_20260923"

PLAN_COLUMNS = [
    "execution_order", "security_id", "ticker", "exchange", "pilot_role", "priority_tier",
    "methodology_edge_case", "known_evidence_tags", "history_tier",
    "base_5y_target_start", "base_5y_target_end", "base_5y_status", "target_start", "target_end",
    "identity_intervals", "existing_history_status", "existing_history_source_run",
    "existing_history_contract", "history_registry_reference", "acquisition_action",
    "crawl_required", "crawl_allowed", "estimated_quarter_ranges", "estimated_pages",
    "estimated_requests", "blocking_reason",
]

REGISTRY_COLUMNS = [
    "security_id", "ticker", "audit_status", "source_run_id", "source_contract_version",
    "history_start", "history_end", "identity_intervals", "quarter_range_count",
    "completed_request_count", "raw_checksum_validation_status", "history_tier", "reuse_status",
]


def stable_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".tmp.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def csv_bytes(rows: list[dict], columns: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows([{column: row.get(column, "") for column in columns} for row in rows])
    return stream.getvalue().encode("utf-8")


def quarter_intersections(start: date, end: date) -> Iterable[tuple[date, date]]:
    cursor = start
    while cursor <= end:
        quarter_start_month = ((cursor.month - 1) // 3) * 3 + 1
        next_month = quarter_start_month + 3
        next_start = date(cursor.year + 1, 1, 1) if next_month == 13 else date(cursor.year, next_month, 1)
        range_end = min(end, next_start - timedelta(days=1))
        yield cursor, range_end
        cursor = range_end + timedelta(days=1)


def identity_ranges(row: dict[str, str], start: date, end: date) -> list[tuple[dict, date, date]]:
    intervals = json.loads(row["identity_intervals"])
    result: list[tuple[dict, date, date]] = []
    for interval in intervals:
        interval_start = max(start, date.fromisoformat(interval["effective_from"]))
        interval_end = min(end, date.fromisoformat(interval["effective_to"]) if interval.get("effective_to") else end)
        if interval_start > interval_end:
            continue
        for range_start, range_end in quarter_intersections(interval_start, interval_end):
            result.append((interval, range_start, range_end))
    return result


def base_target_start(row: dict[str, str]) -> date:
    intervals = json.loads(row["identity_intervals"])
    legitimate_start = min(date.fromisoformat(interval["effective_from"]) for interval in intervals)
    return max(BASE_LOWER_BOUND, legitimate_start)


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _failure_tickers(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    tickers: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if value.get("ticker"):
            tickers.add(str(value["ticker"]).upper())
    return tickers


def audit_v23_run(run_dir: Path) -> tuple[list[dict], dict]:
    run_dir = run_dir.resolve()
    snapshot = run_dir / "plan_snapshot"
    manifest_path = run_dir / "manifest.json"
    progress_path = run_dir / "progress.json"
    execution_path = snapshot / "cafef_c1_solo_execution_order.csv"
    contract_path = snapshot / "cafef_c1_solo_contract.json"
    if not all(path.is_file() for path in (manifest_path, progress_path, execution_path, contract_path)):
        raise ValueError(f"stopped V2.3 run is missing required audit files: {run_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if manifest.get("contract_version") != SOURCE_CONTRACT_VERSION:
        raise ValueError("source run is not CafeF raw contract V2.3")
    if contract.get("request_surface", {}).get("range_iteration") != "NON_OVERLAPPING_CALENDAR_QUARTER_INTERSECTIONS_OLDEST_TO_NEWEST":
        raise ValueError("source run is not quarter bounded")
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    completed = progress.get("completed", {})
    failures = _failure_tickers(run_dir / "failures.jsonl")
    rows = _load_csv(execution_path)
    entries_by_ticker: dict[str, list[tuple[str, dict]]] = {}
    for key, entry in completed.items():
        entries_by_ticker.setdefault(str(entry.get("ticker", "")).upper(), []).append((key, entry))

    records: list[dict] = []
    for row in rows:
        ticker = row["ticker"].upper()
        expected_ranges = identity_ranges(
            row, date.fromisoformat(row["target_start"]), date.fromisoformat(row["target_end"])
        )
        ticker_entries = entries_by_ticker.get(ticker, [])
        raw_folder = run_dir / "raw" / ticker
        has_raw = raw_folder.is_dir() and any(raw_folder.rglob("page_*.json"))
        checksum_ok = True
        all_ranges_complete = True
        matched_keys: set[str] = set()
        for interval, range_start, range_end in expected_ranges:
            matching = [
                (key, entry) for key, entry in ticker_entries
                if entry.get("exchange") == interval["exchange"]
                and entry.get("identity_interval_effective_from") == interval["effective_from"]
                and entry.get("identity_interval_effective_to") == interval.get("effective_to")
                and entry.get("requested_start") == range_start.isoformat()
                and entry.get("requested_end") == range_end.isoformat()
            ]
            if not matching:
                all_ranges_complete = False
                continue
            matched_keys.update(key for key, _entry in matching)
            expected_page_values = {int(entry.get("expected_pages", -1)) for _key, entry in matching}
            if len(expected_page_values) != 1:
                all_ranges_complete = False
                continue
            expected_pages = next(iter(expected_page_values))
            required_pages = max(1, expected_pages)
            if {int(entry.get("page", -1)) for _key, entry in matching} != set(range(1, required_pages + 1)):
                all_ranges_complete = False
            for key, entry in matching:
                if entry.get("request_key") != key:
                    checksum_ok = False
                raw_path = run_dir / entry.get("raw_path", "")
                meta_path = raw_path.with_suffix(".meta.json")
                if not raw_path.is_file() or sha256_file(raw_path) != entry.get("sha256"):
                    checksum_ok = False
                    continue
                if not meta_path.is_file():
                    checksum_ok = False
                    continue
                sidecar = json.loads(meta_path.read_text(encoding="utf-8"))
                if sidecar.get("request_key") != key or sidecar.get("sha256") != entry.get("sha256"):
                    checksum_ok = False
        if len(matched_keys) != len(ticker_entries):
            all_ranges_complete = False
        if not ticker_entries and not has_raw:
            audit_status = "NOT_STARTED"
            checksum_status = "NOT_APPLICABLE"
        elif all_ranges_complete and checksum_ok and ticker not in failures:
            audit_status = "LONG_HISTORY_COMPLETE"
            checksum_status = "PASS"
        else:
            audit_status = "PARTIAL"
            checksum_status = "PASS" if checksum_ok else "FAIL"
        records.append({
            "security_id": row["security_id"],
            "ticker": ticker,
            "audit_status": audit_status,
            "source_run_id": run_dir.name,
            "source_contract_version": manifest["contract_version"],
            "history_start": row["target_start"],
            "history_end": row["target_end"],
            "identity_intervals": row["identity_intervals"],
            "quarter_range_count": len(expected_ranges),
            "completed_request_count": len(ticker_entries),
            "raw_checksum_validation_status": checksum_status,
            "history_tier": "LONG_15Y_VALIDATION" if audit_status == "LONG_HISTORY_COMPLETE" else "BASE_5Y",
            "reuse_status": "ELIGIBLE_FOR_BASE5Y_REUSE" if audit_status == "LONG_HISTORY_COMPLETE" else "NOT_REUSED",
        })
    summary = {
        "source_run_id": run_dir.name,
        "source_contract_version": manifest["contract_version"],
        "source_run_created_at": manifest.get("created_at"),
        "classification_counts": {
            status: sum(record["audit_status"] == status for record in records)
            for status in ("LONG_HISTORY_COMPLETE", "PARTIAL", "NOT_STARTED")
        },
        "audit_method": "EXPECTED_IDENTITY_QUARTERS_AND_PAGES_PLUS_RAW_AND_SIDECAR_SHA256",
    }
    return records, summary


def write_registry(registry_dir: Path, records: list[dict], summary: dict, now: datetime) -> dict:
    complete = [record for record in records if record["audit_status"] == "LONG_HISTORY_COMPLETE"]
    excluded = [record for record in records if record["audit_status"] != "LONG_HISTORY_COMPLETE"]
    atomic_write(registry_dir / "long_history_complete.csv", csv_bytes(complete, REGISTRY_COLUMNS))
    atomic_write(registry_dir / "partial_not_reused.csv", csv_bytes(excluded, REGISTRY_COLUMNS))
    manifest = {
        **summary,
        "registry_version": "CAFEF_HISTORY_REGISTRY_V1",
        "created_at": summary.get("source_run_created_at") or now.isoformat(),
        "history_set_label": "OPERATIONAL_LONG_HISTORY_VALIDATION_SET",
        "statistical_representativeness": "NOT_CLAIMED",
        "long_history_complete_count": len(complete),
        "partial_or_not_started_count": len(excluded),
        "files": {
            "long_history_complete.csv": sha256_file(registry_dir / "long_history_complete.csv"),
            "partial_not_reused.csv": sha256_file(registry_dir / "partial_not_reused.csv"),
        },
    }
    atomic_write(registry_dir / "manifest.json", stable_json_bytes(manifest))
    return manifest


def select_deep_10y(rows: list[dict], seed: str = DEEP_SELECTOR_SEED, fraction: float = 0.10) -> list[str]:
    eligible = [
        row for row in rows
        if date.fromisoformat(row["legitimate_history_start"]) <= DEEP_LOWER_BOUND
    ]
    if not eligible:
        return []
    target = max(1, round(len(rows) * fraction))
    target = min(target, len(eligible))
    rank = lambda row: (sha256_bytes(f"{seed}|{row['security_id']}".encode()), row["security_id"])

    def strata(row: dict) -> tuple[str, str, str, str]:
        history_start = date.fromisoformat(row["legitimate_history_start"])
        if history_start <= date(2011, 9, 23):
            age_band = "15Y_PLUS"
        elif history_start <= date(2014, 9, 23):
            age_band = "12Y_TO_15Y"
        else:
            age_band = "10Y_TO_12Y"
        role = str(row.get("pilot_role", "UNSPECIFIED")).split(";", 1)[0]
        edge = "EDGE_CASE" if str(row.get("methodology_edge_case", "NO")).upper() == "YES" else "STANDARD"
        return row["exchange"], age_band, role, edge

    selected: list[dict] = []
    covered = [set(), set(), set(), set()]

    def add(row: dict) -> None:
        selected.append(row)
        for index, value in enumerate(strata(row)):
            covered[index].add(value)

    def diversity_rank(row: dict) -> tuple:
        values = strata(row)
        novelty = sum(value not in covered[index] for index, value in enumerate(values))
        balance = sum(sum(strata(chosen)[index] == value for chosen in selected) for index, value in enumerate(values))
        return -novelty, balance, *rank(row)

    exchanges = sorted({row["exchange"] for row in eligible})
    if target >= len(exchanges):
        for exchange in exchanges:
            add(min((row for row in eligible if row["exchange"] == exchange), key=diversity_rank))
    selected_ids = {row["security_id"] for row in selected}
    while len(selected) < target:
        row = min((item for item in eligible if item["security_id"] not in selected_ids), key=diversity_rank)
        add(row)
        selected_ids.add(row["security_id"])
    return sorted(row["security_id"] for row in selected)


def _estimate_ranges(row: dict[str, str], start: date, end: date) -> tuple[int, int]:
    ranges = identity_ranges(row, start, end)
    pages = 0
    for _interval, range_start, range_end in ranges:
        days = (range_end - range_start).days + 1
        estimated_rows = min(days, math.ceil(days * 252 / 365.2425))
        pages += math.ceil(estimated_rows / PAGE_SIZE)
    return len(ranges), pages


def build_plan(v2_plan_dir: Path, output_dir: Path, registry_records: list[dict], registry_manifest: dict | None) -> dict:
    old_rows = _load_csv(v2_plan_dir / "cafef_c1_solo_execution_order.csv")
    registry_by_ticker = {record["ticker"]: record for record in registry_records}
    plan_rows: list[dict] = []
    deep_candidates: list[dict] = []
    for old in old_rows:
        intervals = json.loads(old["identity_intervals"])
        legitimate_start = min(date.fromisoformat(interval["effective_from"]) for interval in intervals)
        base_start = base_target_start(old)
        audit = registry_by_ticker.get(old["ticker"])
        reusable = bool(
            audit and audit["audit_status"] == "LONG_HISTORY_COMPLETE"
            and date.fromisoformat(audit["history_start"]) <= base_start
            and date.fromisoformat(audit["history_end"]) >= COLLECTION_END
            and audit["raw_checksum_validation_status"] == "PASS"
        )
        ranges, requests = _estimate_ranges(old, base_start, COLLECTION_END)
        plan_rows.append({
            "execution_order": old["execution_order"],
            "security_id": old["security_id"],
            "ticker": old["ticker"],
            "exchange": old["exchange"],
            "pilot_role": old["pilot_role"],
            "priority_tier": old["priority_tier"],
            "methodology_edge_case": old["methodology_edge_case"],
            "known_evidence_tags": old["known_evidence_tags"],
            "history_tier": "LONG_15Y_VALIDATION" if reusable else "BASE_5Y",
            "base_5y_target_start": base_start.isoformat(),
            "base_5y_target_end": COLLECTION_END.isoformat(),
            "base_5y_status": "SATISFIED_BY_EXISTING_LONG_HISTORY" if reusable else "ACQUISITION_REQUIRED",
            "target_start": base_start.isoformat(),
            "target_end": COLLECTION_END.isoformat(),
            "identity_intervals": old["identity_intervals"],
            "existing_history_status": audit["audit_status"] if audit else "LOCAL_LONG_HISTORY_RUN_NOT_AVAILABLE",
            "existing_history_source_run": audit["source_run_id"] if reusable else "",
            "existing_history_contract": audit["source_contract_version"] if reusable else "",
            "history_registry_reference": "artifacts/cafef_primary/history_registry_v1/manifest.json" if reusable else "",
            "acquisition_action": "REUSE_EXISTING_VALID_RAW" if reusable else "CRAWL_BASE_5Y",
            "crawl_required": "NO" if reusable else "YES",
            "crawl_allowed": "YES",
            "estimated_quarter_ranges": 0 if reusable else ranges,
            "estimated_pages": 0 if reusable else requests,
            "estimated_requests": 0 if reusable else requests,
            "blocking_reason": "",
        })
        deep_candidates.append({
            "security_id": old["security_id"], "exchange": old["exchange"],
            "pilot_role": old["pilot_role"], "legitimate_history_start": legitimate_start.isoformat(),
            "methodology_edge_case": old["methodology_edge_case"],
        })

    deep_selection = select_deep_10y(deep_candidates)
    contract = {
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "contract_version": RAW_CONTRACT_VERSION,
        "history_policy": HISTORY_POLICY,
        "priority_policy": "CAFEF_C1_SOLO_PRIORITY_V2",
        "default_history_tier": "BASE_5Y",
        "base_history_lower_bound": BASE_LOWER_BOUND.isoformat(),
        "hard_lower_date_boundary": BASE_LOWER_BOUND.isoformat(),
        "collection_end_date": COLLECTION_END.isoformat(),
        "minimum_research_history_years": 3,
        "acquisition_history_depth_is_research_eligibility": False,
        "request_surface": {
            "base_url": "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx",
            "parameters": ["ExchangeType", "Symbol", "StartDate", "EndDate", "PageIndex", "PageSize"],
            "page_size": PAGE_SIZE,
            "page_index_origin": 1,
            "ordering": "NEWEST_FIRST",
            "range_iteration": "NON_OVERLAPPING_CALENDAR_QUARTER_INTERSECTIONS_OLDEST_TO_NEWEST",
            "range_hard_guard": "START_AND_END_MUST_SHARE_ONE_CALENDAR_QUARTER",
            "max_pages_per_range": 20,
        },
        "request_policy": {
            "concurrency": 1, "minimum_request_interval_seconds": 5.0, "timeout_seconds": 20,
            "maximum_response_bytes": 5_000_000, "maximum_attempts": 2,
            "transient_backoff_seconds": [10.0], "retryable_http_status": [500, 502, 503, 504],
            "stop_http_status": [401, 403, 429],
            "stop_body_markers": ["captcha", "cloudflare", "access denied", "cf-chl"],
            "bypass_controls": False,
        },
        "reuse_policy": {
            "complete_v23_long_history": "REUSE_EXISTING_VALID_RAW",
            "partial_v23_history": "NOT_AUTOMATICALLY_REUSED",
            "raw_duplication": "FORBIDDEN",
        },
        "raw_only": {"canonical_write": False, "research_price_build": False, "feature_build": False},
    }
    failure_policy = json.loads((v2_plan_dir / "cafef_c1_solo_failure_policy.json").read_text(encoding="utf-8"))
    failure_policy["plan_id"] = PLAN_ID
    resume_contract = {
        "plan_id": PLAN_ID,
        "contract_version": RESUME_CONTRACT_VERSION,
        "resume_requires_exact_match": [
            "plan_hash", "contract_version", "resume_contract_version", "code_version",
            "collection_end_date", "history_policy", "raw_file_checksum_state",
        ],
        "v2_3_resume_into_v3": "FORBIDDEN",
        "completed_valid_request": "VERIFY_SHA256_AND_SKIP",
        "rejected_response_completed": "FORBIDDEN",
        "raw_overwrite": "FORBIDDEN",
    }
    deep_policy = {
        "history_tier": "DEEP_10Y",
        "execution_status": "PREPARED_NOT_EXECUTED",
        "lower_bound": DEEP_LOWER_BOUND.isoformat(),
        "fraction": 0.10,
        "fixed_seed": DEEP_SELECTOR_SEED,
        "selector": "DETERMINISTIC_HASH_RANK_WITH_EXCHANGE_REPRESENTATION_WHERE_FEASIBLE",
        "selected_security_ids_for_current_pilot_preview": deep_selection,
        "representativeness": "NOT_POPULARITY_OR_MARKET_CAP_CLAIM",
    }
    outputs = {
        "cafef_c1_history_v3_plan.csv": csv_bytes(plan_rows, PLAN_COLUMNS),
        "cafef_c1_history_v3_contract.json": stable_json_bytes(contract),
        "cafef_c1_history_v3_failure_policy.json": stable_json_bytes(failure_policy),
        "cafef_c1_history_v3_resume_contract.json": stable_json_bytes(resume_contract),
        "cafef_c1_history_v3_deep_10y_policy.json": stable_json_bytes(deep_policy),
    }
    for name, data in outputs.items():
        atomic_write(output_dir / name, data)
    plan_hash = sha256_bytes(b"".join(outputs[name] for name in sorted(outputs)))
    reused = [row for row in plan_rows if row["crawl_required"] == "NO"]
    crawl = [row for row in plan_rows if row["crawl_required"] == "YES"]
    manifest = {
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "stage": "C1-HISTORY-POLICY-V3",
        "status": "COMPLETED_USER_MANUAL_REVIEW_REQUIRED",
        "history_policy": HISTORY_POLICY,
        "priority_policy": "CAFEF_C1_SOLO_PRIORITY_V2",
        "collection_end_date": COLLECTION_END.isoformat(),
        "base_history_lower_bound": BASE_LOWER_BOUND.isoformat(),
        "pilot_security_count": len(plan_rows),
        "existing_long_history_complete_count": len(reused),
        "existing_long_history_complete_tickers": [row["ticker"] for row in reused],
        "base5y_reused_count": len(reused),
        "base5y_reused_tickers": [row["ticker"] for row in reused],
        "base5y_crawl_required_count": len(crawl),
        "base5y_crawl_required_tickers": [row["ticker"] for row in crawl],
        "base5y_quarter_range_count": sum(int(row["estimated_quarter_ranges"]) for row in crawl),
        "base5y_estimated_requests": sum(int(row["estimated_requests"]) for row in crawl),
        "estimate_label": "ESTIMATE_NOT_ACTUAL",
        "execution_plan_file": "cafef_c1_history_v3_plan.csv",
        "contract_file": "cafef_c1_history_v3_contract.json",
        "failure_policy_file": "cafef_c1_history_v3_failure_policy.json",
        "resume_contract_file": "cafef_c1_history_v3_resume_contract.json",
        "plan_files": sorted(outputs),
        "plan_hash": plan_hash,
        "output_hashes": {name: sha256_bytes(data) for name, data in outputs.items()},
        "history_registry_reference": "artifacts/cafef_primary/history_registry_v1/manifest.json" if registry_manifest else None,
        "history_registry_manifest_sha256": sha256_bytes(stable_json_bytes(registry_manifest)) if registry_manifest else None,
        "deep_10y_execution": "NOT_EXECUTED",
        "deep_10y_selector_seed": DEEP_SELECTOR_SEED,
        "long_15y_set_label": "OPERATIONAL_LONG_HISTORY_VALIDATION_SET",
        "actual_market_data_requests": 0,
        "actual_crawl_executed": False,
        "canonical_mutations": 0,
        "feature_rebuild": False,
        "next_allowed_action": "USER MANUAL REVIEW OF V3 PLAN",
    }
    atomic_write(output_dir / "manifest.json", stable_json_bytes(manifest))
    return {"rows": plan_rows, "manifest": manifest, "contract": contract, "resume": resume_contract}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CafeF C1 HISTORY_POLICY_V3 plan offline")
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE_RUN)
    parser.add_argument("--registry-dir", type=Path, default=DEFAULT_REGISTRY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    if args.source_run.is_dir():
        records, summary = audit_v23_run(args.source_run)
        registry = write_registry(args.registry_dir, records, summary, datetime.now(timezone.utc))
    else:
        records, registry = [], None
    result = build_plan(V2_PLAN_DIR, args.output_dir, records, registry)
    print(json.dumps({
        "plan_id": result["manifest"]["plan_id"],
        "pilot_security_count": result["manifest"]["pilot_security_count"],
        "base5y_reused_count": result["manifest"]["base5y_reused_count"],
        "base5y_crawl_required_count": result["manifest"]["base5y_crawl_required_count"],
        "base5y_estimated_requests": result["manifest"]["base5y_estimated_requests"],
        "actual_market_data_requests": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
