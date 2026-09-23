#!/usr/bin/env python3
"""Build the frozen, offline CafeF C1-SOLO v2 plan.

This planner reads only repository evidence produced before C1-SOLO.  It performs no
HTTP requests and creates no worker partitions.  The explicit seed lists below are a
reviewable project-relevance proxy; they do not claim current popularity, liquidity,
market capitalization, or index membership.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from datetime import date
from pathlib import Path


PLAN_ID = "cafef-c1-solo-v2"
PLAN_VERSION = "2.1.0"
PRIORITY_POLICY = "CAFEF_C1_SOLO_PRIORITY_V2"
COLLECTION_END = date(2026, 9, 23)
HARD_LOWER_BOUND = date(2011, 9, 23)
PAGE_SIZE = 20
V1_SELECTED = Path("docs/crawl/plans/cafef_c1_prep_v1/cafef_c1_selected_pilot.csv")

# Manual seeds are explicitly grounded in the corrective-stage brief and in the
# repository's prior representative-pilot evidence.  Alphabetical order within a
# tier is the deterministic tie-break; security_id is the secondary tie-break.
TIER_A_CORE = {
    "ACB", "ACV", "BID", "CTG", "DGC", "FPT", "GAS", "GMD", "HCM",
    "HPG", "MBB", "MSN", "MWG", "PVD", "PVS", "QNS", "REE", "SSI",
    "VEA", "VGI", "VNM",
}
TIER_B_CORE = {"NTP", "PVI", "VCS"}
TIER_C_EDGE = {"BCM", "CTR", "SHB"}
EDGE_CASES = {"ACV", "BCM", "CTR", "FPT", "PVS", "SHB"}
SELECTED = TIER_A_CORE | TIER_B_CORE | TIER_C_EDGE
EXTRA_EVIDENCE_TAGS = {
    "FPT": ["KBS_MISSING_SESSION_CAFEF_EVIDENCE", "CORPORATE_ACTION_WINDOW"],
    "PVS": ["KBS_MISSING_SESSION_CAFEF_EVIDENCE"],
    "ACV": ["KBS_MISSING_SESSION_CAFEF_EVIDENCE", "PROVIDER_HISTORY_BOUNDARY_PROBE"],
    "QNS": ["PROVIDER_HISTORY_BOUNDARY_PROBE"],
    "VEA": ["PROVIDER_HISTORY_BOUNDARY_PROBE"],
    "VGI": ["PROVIDER_HISTORY_BOUNDARY_PROBE"],
}

PILOT_COLUMNS = [
    "execution_order", "security_id", "ticker", "exchange", "pilot_role",
    "priority_tier", "selection_reason", "known_evidence_tags", "identity_status",
    "identity_intervals", "listing_date", "target_start", "target_end",
    "history_target_reason", "estimated_pages", "estimated_requests",
    "methodology_edge_case", "crawl_allowed", "blocking_reason",
]

ESTIMATE_COLUMNS = [
    "execution_order", "security_id", "ticker", "exchange", "target_start",
    "target_end", "estimated_calendar_days", "estimated_history_years",
    "estimated_trading_days", "range_chunk_count", "page_size", "estimated_pages",
    "estimated_requests", "complexity", "estimate_label",
]


def _stable_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _csv_bytes(rows: list[dict], columns: list[str]) -> bytes:
    import io

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows([{column: row.get(column, "") for column in columns} for row in rows])
    return stream.getvalue().encode("utf-8")


def _load_v1_rows(root: Path) -> dict[str, dict[str, str]]:
    with (root / V1_SELECTED).open(encoding="utf-8", newline="") as stream:
        rows = {row["current_ticker"]: row for row in csv.DictReader(stream)}
    missing = sorted(SELECTED - rows.keys())
    if missing:
        raise ValueError(f"manual seed not supported by v1 evidence: {missing}")
    return rows


def _role(ticker: str) -> str:
    roles = []
    if ticker in TIER_A_CORE or ticker in TIER_B_CORE:
        roles.append("CORE_MARKET")
    if ticker in EDGE_CASES or ticker in TIER_C_EDGE:
        roles.append("METHODOLOGY_EDGE_CASE")
    return ";".join(roles)


def _tier(ticker: str) -> str:
    if ticker in TIER_A_CORE:
        return "TIER_A"
    if ticker in TIER_B_CORE:
        return "TIER_B"
    return "TIER_C"


def _selection_reason(ticker: str) -> str:
    reasons = []
    if ticker in TIER_A_CORE:
        reasons.extend(["CORE_MARKET", "HIGH_PROJECT_RELEVANCE", "MARKET_IMPORTANCE_PROXY"])
    elif ticker in TIER_B_CORE:
        reasons.extend(["CORE_MARKET", "REPRESENTATIVE_REMAINDER", "MARKET_IMPORTANCE_PROXY"])
    if ticker in EDGE_CASES or ticker in TIER_C_EDGE:
        reasons.append("METHODOLOGY_COVERAGE")
    return ";".join(reasons)


def _estimate(start: date, end: date) -> tuple[int, float, int, int, int]:
    calendar_days = (end - start).days + 1
    years = min(calendar_days / 365.2425, 15.0)
    # Planning estimate only: 252 exchange sessions per year, capped by calendar span.
    trading_days = min(calendar_days, math.ceil(years * 252))
    pages = math.ceil(trading_days / PAGE_SIZE)
    chunks = end.year - start.year + 1
    return calendar_days, round(years, 3), trading_days, chunks, pages


def _rows(root: Path) -> tuple[list[dict], list[dict]]:
    source = _load_v1_rows(root)
    ordered = sorted(SELECTED, key=lambda t: ({"TIER_A": 0, "TIER_B": 1, "TIER_C": 2}[_tier(t)], t, source[t]["security_id"]))
    pilot: list[dict] = []
    estimates: list[dict] = []
    for execution_order, ticker in enumerate(ordered, 1):
        row = source[ticker]
        identity = row["identity_status"]
        if identity not in {"VERIFIED_LISTING_SNAPSHOT", "VERIFIED_TRANSFER"}:
            raise ValueError(f"unresolved identity cannot enter solo plan: {ticker}={identity}")
        start = date.fromisoformat(row["target_start"])
        history_target_reason = row["history_target_reason"]
        if identity == "VERIFIED_TRANSFER":
            intervals = json.loads(row["historical_identity_intervals"])
            first_verified_identity = min(date.fromisoformat(item["effective_from"]) for item in intervals)
            start = max(HARD_LOWER_BOUND, first_verified_identity)
            history_target_reason = "VERIFIED_IDENTITY_BOUNDARY" if start > HARD_LOWER_BOUND else "MAX_15Y_BOUNDARY"
        end = COLLECTION_END
        if start < HARD_LOWER_BOUND:
            raise ValueError(f"history before hard lower bound: {ticker}")
        calendar_days, years, trading_days, chunks, pages = _estimate(start, end)
        tags = row["known_evidence_tags"]
        tags = ";".join(dict.fromkeys(filter(None, [*tags.split(";"), *EXTRA_EVIDENCE_TAGS.get(ticker, [])])))
        if ticker in TIER_A_CORE or ticker in TIER_B_CORE:
            tags = ";".join(filter(None, [tags, "MARKET_IMPORTANCE_PROXY"]))
        pilot_row = {
            "execution_order": execution_order,
            "security_id": row["security_id"],
            "ticker": ticker,
            "exchange": row["current_exchange"],
            "pilot_role": _role(ticker),
            "priority_tier": _tier(ticker),
            "selection_reason": _selection_reason(ticker),
            "known_evidence_tags": tags,
            "identity_status": identity,
            "identity_intervals": row["historical_identity_intervals"],
            "listing_date": row["listing_date"],
            "target_start": start.isoformat(),
            "target_end": end.isoformat(),
            "history_target_reason": history_target_reason,
            "estimated_pages": pages,
            "estimated_requests": pages,
            "methodology_edge_case": "YES" if "METHODOLOGY_EDGE_CASE" in _role(ticker) else "NO",
            "crawl_allowed": "YES",
            "blocking_reason": "",
        }
        pilot.append(pilot_row)
        estimates.append({
            "execution_order": execution_order,
            "security_id": row["security_id"],
            "ticker": ticker,
            "exchange": row["current_exchange"],
            "target_start": start.isoformat(),
            "target_end": end.isoformat(),
            "estimated_calendar_days": calendar_days,
            "estimated_history_years": years,
            "estimated_trading_days": trading_days,
            "range_chunk_count": chunks,
            "page_size": PAGE_SIZE,
            "estimated_pages": pages,
            "estimated_requests": pages,
            "complexity": "TRANSFER_IDENTITY" if identity == "VERIFIED_TRANSFER" else "STANDARD",
            "estimate_label": "ESTIMATE_NOT_ACTUAL",
        })
    return pilot, estimates


def _contract() -> dict:
    return {
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "contract_version": "CAFEF_C1_SOLO_RAW_CONTRACT_V2_1",
        "status": "PLANNING_ONLY_USER_MANUAL_REVIEW_REQUIRED",
        "priority_policy": PRIORITY_POLICY,
        "execution_model": "SINGLE_LOCAL_RUNNER",
        "operator_count": 1,
        "runner_count": 1,
        "parallel_requests": False,
        "worker_partitions": False,
        "collection_end_date": COLLECTION_END.isoformat(),
        "hard_lower_date_boundary": HARD_LOWER_BOUND.isoformat(),
        "maximum_history_years": 15,
        "history_policy": "FULL_AVAILABLE_UP_TO_MAX_15Y",
        "request_surface": {
            "base_url": "https://s.cafef.vn/Ajax/PageNew/DataHistory/PriceHistory.ashx",
            "endpoint": "DataHistory/PriceHistory.ashx",
            "parameters": ["ExchangeType", "Symbol", "StartDate", "EndDate", "PageIndex", "PageSize"],
            "date_format": "MM/DD/YYYY",
            "page_index_origin": 1,
            "page_size": PAGE_SIZE,
            "ordering": "NEWEST_FIRST",
            "total_count_field": "Data.TotalCount",
            "rows_field": "Data.Data",
            "success_field": "Success",
            "success_required": "EXACT_TRUE",
            "range_iteration": "NON_OVERLAPPING_CALENDAR_YEAR_CHUNKS_OLDEST_TO_NEWEST",
            "page_stop": "CEIL_VALIDATED_TOTALCOUNT_DIV_PAGE_SIZE",
            "total_count_consistency": "NON_NEGATIVE_INTEGER_ZERO_REQUIRES_EMPTY_ROWS",
            "max_pages_per_range": 20,
            "duplicate_date_policy": "RETAIN_RAW_AND_LOG_DUPLICATE_DATE",
            "out_of_window_policy": "RETAIN_RAW_AND_LOG_OUT_OF_WINDOW",
            "empty_response_policy": "PROVIDER_EMPTY_RESPONSE_UNRESOLVED_NOT_LISTING_INFERENCE",
        },
        "request_policy": {
            "concurrency": 1,
            "minimum_request_interval_seconds": 5.0,
            "timeout_seconds": 20,
            "maximum_response_bytes": 5_000_000,
            "maximum_attempts": 2,
            "transient_backoff_seconds": [10.0],
            "retryable_http_status": [500, 502, 503, 504],
            "stop_http_status": [401, 403, 429],
            "stop_body_markers": ["captcha", "cloudflare", "access denied", "cf-chl"],
            "bypass_controls": False,
        },
        "raw_only": {
            "canonical_write": False,
            "research_price_build": False,
            "adjustment_factor_build": False,
            "feature_build": False,
            "GiaDieuChinh_AdjustPrice": "PRESERVE_RAW_PROVIDER_BYTES_VALIDATION_ONLY",
        },
        "identity_policy": "EVIDENCE_BACKED_SECURITY_INTERVALS_ONLY",
        "identity_interval_routing": {
            "exchange_type": "LITERAL_INTERVAL_EXCHANGE_HOSE_HNX_UPCOM",
            "request_window": "INTERSECTION_TARGET_WINDOW_AND_IDENTITY_INTERVAL",
            "empty_intersection": "SKIP",
            "empty_identity_intervals": "FAIL_CLOSED",
            "raw_path_context": "TICKER_EXCHANGE_IDENTITY_INTERVAL_RANGE_PAGE",
            "request_key_context": "SECURITY_TICKER_EXCHANGE_IDENTITY_INTERVAL_RANGE_PAGE",
        },
        "excluded_unresolved": ["VCB_CANONICAL_SECURITY_ID_AND_LISTING_BOUNDARY"],
        "manual_gate": "USER_EXPLICIT_APPROVAL_REQUIRED_BEFORE_C1_SOLO",
    }


def _failure_policy() -> dict:
    return {
        "plan_id": PLAN_ID,
        "policy_version": "CAFEF_C1_SOLO_FAILURE_POLICY_V2",
        "empty_response": "PROVIDER_EMPTY_RESPONSE_UNRESOLVED_NOT_LISTING_INFERENCE",
        "access_control": "STOP_RUN_RECORD_EVIDENCE_DO_NOT_BYPASS",
        "schema_error": "STOP_SECURITY_RANGE_RECORD_RAW_AND_FAILURE",
        "pagination_error": "STOP_SECURITY_RANGE_NO_SILENT_SKIP",
        "duplicate_raw_path": "REFUSE_OVERWRITE_UNLESS_CHECKSUM_VALID_COMPLETION_IS_RESUMED",
        "out_of_window": "RETAIN_RAW_LOG_ONLY_NO_NORMALIZATION_IN_C1",
        "transient_failure": "BOUNDED_RETRY_THEN_RECORD_FAILURE",
        "methodology_failure": "STOP_NO_AUTOMATIC_RETRY",
        "no_imputation": True,
    }


def _resume_contract() -> dict:
    return {
        "plan_id": PLAN_ID,
        "contract_version": "CAFEF_C1_SOLO_RESUME_V2_1",
        "resume_requires_exact_match": [
            "plan_hash", "contract_version", "resume_contract_version", "code_version", "collection_end_date",
            "hard_lower_date_boundary", "raw_file_checksum_state",
        ],
        "completed_valid_request": "VERIFY_SHA256_AND_SKIP",
        "unfinished_request": "CONTINUE_IN_FROZEN_ORDER",
        "transient_failure": "RETRY_WITHIN_REMAINING_BUDGET",
        "access_or_methodology_failure": "REMAIN_STOPPED",
        "completed_ticker": "DO_NOT_RESTART",
        "raw_overwrite": "FORBIDDEN",
    }


def build_plan(root: Path, output_dir: Path) -> dict:
    root = root.resolve()
    output_dir = output_dir.resolve()
    pilot, estimates = _rows(root)
    if not 25 <= len(pilot) <= 30:
        raise ValueError(f"solo pilot outside requested range: {len(pilot)}")
    exchange_counts = {exchange: sum(row["exchange"] == exchange for row in pilot) for exchange in ("HOSE", "HNX", "UPCOM")}
    if exchange_counts != {"HOSE": 19, "HNX": 4, "UPCOM": 4}:
        raise ValueError(f"unexpected exchange shape: {exchange_counts}")

    outputs: dict[str, bytes] = {}
    outputs["cafef_c1_solo_selected_pilot.csv"] = _csv_bytes(pilot, PILOT_COLUMNS)
    outputs["cafef_c1_solo_execution_order.csv"] = _csv_bytes(pilot, PILOT_COLUMNS)
    outputs["cafef_c1_solo_request_estimates.csv"] = _csv_bytes(estimates, ESTIMATE_COLUMNS)
    outputs["cafef_c1_solo_contract.json"] = _stable_json(_contract())
    outputs["cafef_c1_solo_failure_policy.json"] = _stable_json(_failure_policy())
    outputs["cafef_c1_solo_resume_contract.json"] = _stable_json(_resume_contract())
    for name, data in outputs.items():
        _atomic_write(output_dir / name, data)

    plan_hash = _sha256(b"".join(outputs[name] for name in sorted(outputs)))
    core_count = sum("CORE_MARKET" in row["pilot_role"] for row in pilot)
    edge_count = sum("METHODOLOGY_EDGE_CASE" in row["pilot_role"] for row in pilot)
    manifest = {
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "stage": "C1-SOLO-RUNNER-FIX",
        "status": "COMPLETED_USER_MANUAL_REVIEW_REQUIRED",
        "execution_model": "SINGLE_LOCAL_RUNNER",
        "priority_policy": PRIORITY_POLICY,
        "selection_policy": "EXPLICIT_REVIEWABLE_MANUAL_SEEDS_FROM_CORRECTIVE_BRIEF_AND_EXISTING_PROJECT_EVIDENCE_STABLE_TICKER_TIEBREAK",
        "popularity_claim": "NOT_AVAILABLE_USE_MARKET_IMPORTANCE_PROXY",
        "collection_end_date": COLLECTION_END.isoformat(),
        "hard_lower_date_boundary": HARD_LOWER_BOUND.isoformat(),
        "history_policy": "FULL_AVAILABLE_UP_TO_MAX_15Y",
        "pilot_security_count": len(pilot),
        "core_market_count": core_count,
        "methodology_edge_case_count": edge_count,
        "role_counts_overlap": True,
        "exchange_counts": exchange_counts,
        "estimated_total_requests": sum(row["estimated_requests"] for row in estimates),
        "estimate_label": "ESTIMATE_NOT_ACTUAL",
        "plan_hash": plan_hash,
        "output_hashes": {name: _sha256(data) for name, data in outputs.items()},
        "actual_market_data_requests": 0,
        "actual_crawl_executed": False,
        "canonical_mutations": 0,
        "feature_rebuild": False,
        "five_worker_execution": "DEFERRED_TO_C4_PREP_SCALE",
        "runner_contract_corrected": True,
        "exchange_type_contract_aligned": True,
        "historical_identity_interval_routing": True,
        "envelope_success_validation": True,
        "next_allowed_action": "USER MANUAL REVIEW OF CORRECTED C1-SOLO RUNNER",
    }
    _atomic_write(output_dir / "manifest.json", _stable_json(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the deterministic offline CafeF C1-SOLO v2 plan")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("docs/crawl/plans/cafef_c1_solo_v2"))
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else args.root / args.output
    manifest = build_plan(args.root, output)
    print(json.dumps({
        "plan_id": PLAN_ID,
        "pilot_security_count": manifest["pilot_security_count"],
        "estimated_total_requests": manifest["estimated_total_requests"],
        "actual_market_data_requests": 0,
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
