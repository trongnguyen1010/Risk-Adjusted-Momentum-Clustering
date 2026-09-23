"""DEPRECATED_FOR_C1 / FUTURE_C4_SCALE_REFERENCE_ONLY.

This historical planner produced the superseded C1-PREP v1 evidence. It reads
repository metadata only and deliberately contains no HTTP client, crawler, provider
call, or market-data acquisition path. Do not use it for active C1-SOLO execution.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path


PLAN_ID = "cafef-c1-prep-v1"
PLAN_VERSION = "1.0.0"
PRIORITY_POLICY = "CAFEF_ACQUISITION_PRIORITY_V1"
COLLECTION_END = date(2026, 9, 23)
MAX_HISTORY_START = date(2011, 9, 23)
PLANNING_BASE_COMMIT = "8a7ebd9217ddc7de363d28906d7d2966c25e1213"
WORKERS = tuple(f"worker_{number:02d}" for number in range(1, 6))

REPRESENTATIVE_PILOT_SOURCE = "configs/data/representative_pilot.universe.v1.json"
CURRENT_UNIVERSE_SOURCE = "configs/data/m1_scale.universe.v1.json"
TRANSITION_SOURCE = "evidence/a6/transitions.json"

# These tickers are already named in immutable repository documents.  They are
# not assertions about current popularity and do not change research eligibility.
A5_CAFEF_EVIDENCE = {"FPT", "VNM", "VCB", "PVS", "ACV", "HND", "KHP"}
MISSING_SESSION_EDGE = {
    "DDH", "HLS", "HND", "IDV", "KHP", "NO1", "POM", "SGB", "STK",
    "TVB", "UDC", "VNZ",
}
PRICE_BASIS_EDGE = {"IDV", "KHP", "UDC"}
CORPORATE_ACTION_EDGE = {"FPT", "IDV", "KHP", "UDC"}
UNRESOLVED_BOUNDARY_EDGE = {"DDH", "HLS", "HND", "IDV", "NO1", "POM", "SGB", "TVB", "VNZ"}

ORIGINAL_WEIGHTS = {
    "liquidity_traded_value_persistence": 30,
    "active_trading_frequency": 20,
    "index_market_importance": 15,
    "size_market_cap_proxy": 10,
    "exchange_acquisition_preference": 10,
    "identity_source_confidence": 10,
    "strategic_relevance_coverage_problem": 5,
}
AVAILABLE_WEIGHT = 40  # 15 + 10 + 10 + 5; the other inputs are unavailable offline.
EXCHANGE_SCORE = {"HOSE": 100, "HNX": 60, "UPCOM": 20}

CSV_COLUMNS = {
    "cafef_c1_priority_ranking.csv": [
        "priority_rank", "security_id", "current_ticker", "current_exchange",
        "candidate_sources", "liquidity_signal", "active_frequency_signal",
        "index_market_importance_signal", "index_market_importance_value",
        "size_market_cap_signal", "exchange_preference_value",
        "identity_confidence_signal", "identity_confidence_value",
        "strategic_relevance_signal", "strategic_relevance_value",
        "available_weight", "priority_score", "priority_tier",
        "popularity_signal", "research_eligibility_effect",
    ],
    "cafef_c1_candidate_universe.csv": [
        "security_id", "current_ticker", "current_exchange", "company_name",
        "sector", "listing_date", "identity_status", "historical_identity_intervals",
        "candidate_sources", "known_evidence_tags", "required_edge_case",
        "plan_input_status", "priority_rank", "priority_score", "priority_tier",
    ],
    "cafef_c1_selected_pilot.csv": [
        "selection_order", "priority_rank", "security_id", "current_ticker",
        "current_exchange", "priority_score", "priority_tier", "wave",
        "listing_date", "identity_status", "historical_identity_intervals",
        "target_start", "target_end", "history_target_reason",
        "required_edge_case", "known_evidence_tags", "selection_reason",
        "research_eligibility_effect",
    ],
    "cafef_c1_request_estimates.csv": [
        "security_id", "current_ticker", "current_exchange", "wave",
        "target_start", "target_end", "estimated_calendar_days",
        "estimated_history_years", "estimated_history_days", "range_chunk_count",
        "page_size", "estimated_pages", "estimated_requests", "estimate_label",
        "complexity_weight", "estimated_work_units", "identity_interval_count",
        "required_edge_case",
    ],
}

ASSIGNMENT_COLUMNS = [
    "local_execution_order", "plan_id", "worker_id", "wave", "priority_rank",
    "priority_score", "priority_tier", "security_id", "current_ticker",
    "current_exchange", "identity_status", "historical_identity_intervals",
    "listing_date", "target_start", "target_end", "history_target_reason",
    "estimated_history_days", "estimated_history_years", "range_chunk_count",
    "estimated_pages", "estimated_requests", "complexity_weight",
    "estimated_work_units", "required_edge_case", "known_evidence_tags",
]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_json(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_hash(path: Path) -> str:
    return _sha256(path.read_bytes())


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".tmp-cafef-c1-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _csv_bytes(rows: list[dict], columns: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _intervals_for_transition(transition: dict) -> list[dict]:
    effective = date.fromisoformat(transition["effective_date"])
    return [
        {
            "ticker": transition["from_ticker"],
            "exchange": transition["from_exchange"],
            "effective_from": transition["from_effective_from"],
            "effective_to": (effective - timedelta(days=1)).isoformat(),
            "evidence_id": transition["evidence_id"],
        },
        {
            "ticker": transition["to_ticker"],
            "exchange": transition["to_exchange"],
            "effective_from": transition["effective_date"],
            "effective_to": None,
            "evidence_id": transition["evidence_id"],
        },
    ]


def _candidate_universe(root: Path) -> list[dict]:
    current = _read_json(root / CURRENT_UNIVERSE_SOURCE)
    representative = _read_json(root / REPRESENTATIVE_PILOT_SOURCE)
    transitions = _read_json(root / TRANSITION_SOURCE)
    security_catalog = _read_json(root / "configs/data/m1_scale.securities.v1.json")
    company_names = {row["ticker"]: row.get("company_name", "") for row in security_catalog["securities"]}

    candidates: dict[str, dict] = {}
    for row in current:
        ticker = row["ticker"].upper()
        candidates[ticker] = {
            "security_id": row["security_id"],
            "current_ticker": ticker,
            "current_exchange": row["exchange"].upper(),
            "company_name": company_names.get(ticker, ""),
            "sector": row.get("sector") or "SIGNAL_UNAVAILABLE",
            "listing_date": row.get("listing_date") or "",
            "identity_status": "PROVISIONAL_CURRENT_UNIVERSE",
            "historical_identity_intervals": [],
            "candidate_sources": {"CURRENT_500"},
            "known_evidence_tags": set(),
            "representative_pilot": False,
        }

    for row in representative:
        ticker = row["ticker"].upper()
        candidate = candidates.setdefault(ticker, {
            "security_id": row["security_id"],
            "current_ticker": ticker,
            "current_exchange": row["exchange"].upper(),
            "company_name": "",
            "sector": row.get("sector") or "SIGNAL_UNAVAILABLE",
            "listing_date": row.get("listing_date") or "",
            "identity_status": "VERIFIED_LISTING_SNAPSHOT",
            "historical_identity_intervals": [],
            "candidate_sources": set(),
            "known_evidence_tags": set(),
            "representative_pilot": True,
        })
        if candidate["current_exchange"] != row["exchange"].upper():
            raise ValueError(f"exchange conflict for {ticker}")
        candidate["candidate_sources"].add("REPRESENTATIVE_PILOT_55")
        candidate["representative_pilot"] = True
        candidate["sector"] = row.get("sector") or candidate["sector"]
        candidate["listing_date"] = row.get("listing_date") or candidate["listing_date"]
        candidate["identity_status"] = "VERIFIED_LISTING_SNAPSHOT"
        candidate["known_evidence_tags"].add("REPRESENTATIVE_PILOT_EVIDENCE")

    # VCB is named in A5-R1.1 evidence but is absent from both local universe snapshots.
    candidates.setdefault("VCB", {
        "security_id": "PLAN_INPUT_UNRESOLVED:VCB",
        "current_ticker": "VCB",
        "current_exchange": "HOSE",
        "company_name": "",
        "sector": "SIGNAL_UNAVAILABLE",
        "listing_date": "",
        "identity_status": "PLAN_INPUT_UNRESOLVED",
        "historical_identity_intervals": [],
        "candidate_sources": {"A5_R1_1_CAFEF_EVIDENCE"},
        "known_evidence_tags": {"IDENTITY_INPUT_UNRESOLVED"},
        "representative_pilot": False,
    })

    for ticker in A5_CAFEF_EVIDENCE:
        candidate = candidates[ticker]
        candidate["candidate_sources"].add("A5_R1_1_CAFEF_EVIDENCE")
        candidate["known_evidence_tags"].add("CAFEF_EXISTING_EVIDENCE")
    for ticker in MISSING_SESSION_EDGE:
        candidates[ticker]["known_evidence_tags"].add("KNOWN_KBS_MISSING_SESSION")
    for ticker in PRICE_BASIS_EDGE:
        candidates[ticker]["known_evidence_tags"].add("KNOWN_PRICE_BASIS_DIFFERENCE")
    for ticker in CORPORATE_ACTION_EDGE:
        candidates[ticker]["known_evidence_tags"].add("CORPORATE_ACTION_WINDOW")
    for ticker in UNRESOLVED_BOUNDARY_EDGE:
        candidates[ticker]["known_evidence_tags"].add("PROVIDER_HISTORY_BOUNDARY_CASE")

    for transition in transitions:
        ticker = transition["to_ticker"].upper()
        candidate = candidates[ticker]
        candidate["candidate_sources"].add("A6_VERIFIED_TRANSFER")
        candidate["known_evidence_tags"].add("EXCHANGE_TRANSFER_IDENTITY")
        candidate["identity_status"] = "VERIFIED_TRANSFER"
        candidate["historical_identity_intervals"] = _intervals_for_transition(transition)

    result = []
    for ticker in sorted(candidates):
        candidate = candidates[ticker]
        if not candidate["historical_identity_intervals"] and candidate["listing_date"]:
            candidate["historical_identity_intervals"] = [{
                "ticker": ticker,
                "exchange": candidate["current_exchange"],
                "effective_from": candidate["listing_date"],
                "effective_to": None,
                "evidence_id": "REPRESENTATIVE_PILOT_LISTING_DATE",
            }]
        candidate["required_edge_case"] = "YES" if candidate["known_evidence_tags"] - {"REPRESENTATIVE_PILOT_EVIDENCE"} else "NO"
        candidate["plan_input_status"] = (
            "PLAN_INPUT_UNRESOLVED" if candidate["identity_status"] == "PLAN_INPUT_UNRESOLVED"
            else "PARTIAL_IDENTITY_UNRESOLVED" if not candidate["listing_date"] and not candidate["historical_identity_intervals"]
            else "OFFLINE_EVIDENCE_AVAILABLE"
        )
        candidate["candidate_sources"] = ";".join(sorted(candidate["candidate_sources"]))
        candidate["known_evidence_tags"] = ";".join(sorted(candidate["known_evidence_tags"]))
        candidate["historical_identity_intervals"] = json.dumps(
            candidate["historical_identity_intervals"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        result.append(candidate)
    return result


def _score_candidates(candidates: list[dict]) -> list[dict]:
    ranked = []
    for candidate in candidates:
        ticker = candidate["current_ticker"]
        representative = candidate["representative_pilot"]
        importance = 100 if representative else 80 if ticker in A5_CAFEF_EVIDENCE else None
        identity = (
            100 if candidate["identity_status"] in {"VERIFIED_LISTING_SNAPSHOT", "VERIFIED_TRANSFER"}
            else 60 if candidate["identity_status"] == "PROVISIONAL_CURRENT_UNIVERSE"
            else 0
        )
        has_edge = candidate["required_edge_case"] == "YES"
        strategic = 100 if ticker in A5_CAFEF_EVIDENCE or has_edge else 60 if representative else None
        points = (
            (0 if importance is None else importance * 15 / 100)
            + EXCHANGE_SCORE[candidate["current_exchange"]] * 10 / 100
            + identity * 10 / 100
            + (0 if strategic is None else strategic * 5 / 100)
        )
        score = round(points / AVAILABLE_WEIGHT * 100, 4)
        tier = "HIGH" if score >= 75 else "MEDIUM" if score >= 60 else "NORMAL"
        row = dict(candidate)
        row.update({
            "liquidity_signal": "SIGNAL_UNAVAILABLE",
            "active_frequency_signal": "SIGNAL_UNAVAILABLE",
            "index_market_importance_signal": "OFFLINE_PROJECT_IMPORTANCE_PROXY" if importance is not None else "SIGNAL_UNAVAILABLE",
            "index_market_importance_value": "" if importance is None else importance,
            "size_market_cap_signal": "SIGNAL_UNAVAILABLE",
            "exchange_preference_value": EXCHANGE_SCORE[candidate["current_exchange"]],
            "identity_confidence_signal": candidate["identity_status"],
            "identity_confidence_value": identity,
            "strategic_relevance_signal": "OFFLINE_PROJECT_OR_EDGE_EVIDENCE" if strategic is not None else "SIGNAL_UNAVAILABLE",
            "strategic_relevance_value": "" if strategic is None else strategic,
            "available_weight": AVAILABLE_WEIGHT,
            "priority_score": score,
            "priority_tier": tier,
            "popularity_signal": "POPULARITY_SIGNAL_NOT_AVAILABLE",
            "research_eligibility_effect": "NONE_ACQUISITION_ORDER_ONLY",
        })
        ranked.append(row)
    ranked.sort(key=lambda row: (-row["priority_score"], row["security_id"], row["current_ticker"]))
    for rank, row in enumerate(ranked, 1):
        row["priority_rank"] = rank
    return ranked


def _target_window(candidate: dict) -> tuple[date, str]:
    verified_starts = []
    if candidate["listing_date"]:
        verified_starts.append(date.fromisoformat(candidate["listing_date"]))
    intervals = json.loads(candidate["historical_identity_intervals"])
    verified_starts.extend(date.fromisoformat(item["effective_from"]) for item in intervals if item.get("effective_from"))
    if verified_starts:
        earliest = min(verified_starts)
        target = max(earliest, MAX_HISTORY_START)
        if target == MAX_HISTORY_START:
            return target, "MAX_15Y_BOUNDARY"
        if len(intervals) > 1 or candidate["identity_status"] == "VERIFIED_TRANSFER":
            return target, "IDENTITY_BOUNDARY"
        return target, "LISTING_BOUNDARY"
    return MAX_HISTORY_START, "PARTIAL_IDENTITY_UNRESOLVED"


def _range_chunks(start: date, end: date) -> list[tuple[date, date]]:
    chunks = []
    cursor = start
    while cursor <= end:
        chunk_end = min(end, date(cursor.year, 12, 31))
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def _estimate(candidate: dict) -> dict:
    start, reason = _target_window(candidate)
    chunks = _range_chunks(start, COLLECTION_END)
    calendar_days = (COLLECTION_END - start).days + 1
    estimated_days = 0
    estimated_pages = 0
    for chunk_start, chunk_end in chunks:
        days = (chunk_end - chunk_start).days + 1
        trading_days = max(1, round(days * 252 / 365.2425))
        estimated_days += trading_days
        estimated_pages += math.ceil(trading_days / 20)
    intervals = json.loads(candidate["historical_identity_intervals"])
    complexity = max(0, len(intervals) - 1) * 4
    if candidate["required_edge_case"] == "YES":
        complexity += 8
    if reason == "PARTIAL_IDENTITY_UNRESOLVED":
        complexity += 6
    return {
        "security_id": candidate["security_id"],
        "current_ticker": candidate["current_ticker"],
        "current_exchange": candidate["current_exchange"],
        "wave": {"HIGH": 1, "MEDIUM": 2, "NORMAL": 3}[candidate["priority_tier"]],
        "target_start": start.isoformat(),
        "target_end": COLLECTION_END.isoformat(),
        "history_target_reason": reason,
        "estimated_calendar_days": calendar_days,
        "estimated_history_years": round(calendar_days / 365.2425, 3),
        "estimated_history_days": estimated_days,
        "range_chunk_count": len(chunks),
        "page_size": 20,
        "estimated_pages": estimated_pages,
        "estimated_requests": estimated_pages,
        "estimate_label": "REQUEST_ESTIMATE",
        "complexity_weight": complexity,
        "estimated_work_units": estimated_pages + complexity,
        "identity_interval_count": len(intervals),
        "required_edge_case": candidate["required_edge_case"],
    }


def _selected_pilot(ranked: list[dict]) -> tuple[list[dict], list[dict]]:
    selected = [
        row for row in ranked
        if row["representative_pilot"] or row["required_edge_case"] == "YES" or row["current_ticker"] in A5_CAFEF_EVIDENCE
    ]
    estimates = {row["security_id"]: _estimate(row) for row in selected}
    selected.sort(key=lambda row: (
        {"HIGH": 1, "MEDIUM": 2, "NORMAL": 3}[row["priority_tier"]],
        -row["priority_score"], row["security_id"], row["current_ticker"],
    ))
    output = []
    for order, row in enumerate(selected, 1):
        estimate = estimates[row["security_id"]]
        reasons = []
        if row["representative_pilot"]:
            reasons.append("PRIOR_REPRESENTATIVE_PILOT")
        if row["current_ticker"] in A5_CAFEF_EVIDENCE:
            reasons.append("EXISTING_CAFEF_EVIDENCE")
        if row["required_edge_case"] == "YES":
            reasons.append("REQUIRED_EDGE_CASE")
        output.append({
            **row,
            **estimate,
            "selection_order": order,
            "wave": estimate["wave"],
            "selection_reason": ";".join(reasons),
        })
    request_rows = [dict(estimates[row["security_id"]]) for row in output]
    return output, request_rows


def _partition(selected: list[dict]) -> dict[str, list[dict]]:
    workers = {worker: [] for worker in WORKERS}
    loads = {worker: 0 for worker in WORKERS}
    for wave in (1, 2, 3):
        pending = [row for row in selected if row["wave"] == wave]
        pending.sort(key=lambda row: (-row["estimated_work_units"], row["security_id"], row["current_ticker"]))
        for row in pending:
            worker = min(WORKERS, key=lambda name: (loads[name], name))
            workers[worker].append(dict(row, worker_id=worker))
            loads[worker] += row["estimated_work_units"]
    for worker, rows in workers.items():
        rows.sort(key=lambda row: (
            row["wave"], -row["priority_score"], row["security_id"], row["current_ticker"]
        ))
        for order, row in enumerate(rows, 1):
            row["local_execution_order"] = order
            row["plan_id"] = PLAN_ID
    return workers


def _partition_summary(selected: list[dict], workers: dict[str, list[dict]]) -> dict:
    selected_ids = [row["security_id"] for row in selected]
    assigned_ids = [row["security_id"] for rows in workers.values() for row in rows]
    worker_summary = {}
    for worker, rows in workers.items():
        tiers = Counter(row["priority_tier"] for row in rows)
        exchanges = Counter(row["current_exchange"] for row in rows)
        high_tickers = [row["current_ticker"] for row in rows if row["priority_tier"] == "HIGH"][:5]
        worker_summary[worker] = {
            "ticker_count": len(rows),
            "high_count": tiers["HIGH"],
            "medium_count": tiers["MEDIUM"],
            "normal_count": tiers["NORMAL"],
            "hose_count": exchanges["HOSE"],
            "hnx_count": exchanges["HNX"],
            "upcom_count": exchanges["UPCOM"],
            "estimated_requests": sum(row["estimated_requests"] for row in rows),
            "estimated_pages": sum(row["estimated_pages"] for row in rows),
            "estimated_history_days": sum(row["estimated_history_days"] for row in rows),
            "estimated_history_years": round(sum(row["estimated_history_years"] for row in rows), 3),
            "estimated_work_units": sum(row["estimated_work_units"] for row in rows),
            "edge_case_count": sum(row["required_edge_case"] == "YES" for row in rows),
            "first_high_priority_tickers": high_tickers,
        }
    loads = [item["estimated_work_units"] for item in worker_summary.values()]
    checks = {
        "exactly_five_workers": len(workers) == 5,
        "selected_assigned_exactly_once": sorted(selected_ids) == sorted(assigned_ids) and len(assigned_ids) == len(set(assigned_ids)),
        "no_unintended_overlap": len(assigned_ids) == len(set(assigned_ids)),
        "no_omitted_selected_security": set(selected_ids) == set(assigned_ids),
        "wave_order_within_worker": all([row["wave"] for row in rows] == sorted(row["wave"] for row in rows) for rows in workers.values()),
        "history_target_at_most_15_years": all(date.fromisoformat(row["target_start"]) >= MAX_HISTORY_START for row in selected),
        "shared_collection_end_date": all(row["target_end"] == COLLECTION_END.isoformat() for row in selected),
        "all_three_exchanges_represented": {row["current_exchange"] for row in selected} == {"HOSE", "HNX", "UPCOM"},
        "important_upcom_not_excluded": all(ticker in {row["current_ticker"] for row in selected} for ticker in ("ACV", "OIL", "QNS", "VEA", "VGI")),
        "edge_case_coverage_present": any(row["required_edge_case"] == "YES" for row in selected),
        "priority_not_research_eligibility": all(row["research_eligibility_effect"] == "NONE_ACQUISITION_ORDER_ONLY" for row in selected),
    }
    return {
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "priority_policy": PRIORITY_POLICY,
        "collection_end_date": COLLECTION_END.isoformat(),
        "history_policy": "FULL_AVAILABLE_UP_TO_MAX_15Y",
        "worker_count": len(workers),
        "selected_security_count": len(selected),
        "worker_summary": worker_summary,
        "estimated_total_requests": sum(row["estimated_requests"] for row in selected),
        "estimated_total_pages": sum(row["estimated_pages"] for row in selected),
        "estimated_total_history_days": sum(row["estimated_history_days"] for row in selected),
        "estimated_work_unit_min": min(loads),
        "estimated_work_unit_max": max(loads),
        "estimated_work_unit_spread": max(loads) - min(loads),
        "estimated_work_unit_max_to_min_ratio": round(max(loads) / min(loads), 6),
        "checks": checks,
    }


def _crawl_contract(assignment_hashes: dict[str, str]) -> dict:
    return {
        "plan_id": PLAN_ID,
        "contract_version": "CAFEF_C1_RAW_CRAWL_CONTRACT_V1",
        "status": "PLANNING_ONLY_USER_MANUAL_REVIEW_REQUIRED",
        "branch": "m1-cafef-primary-experiment",
        "planning_base_commit": PLANNING_BASE_COMMIT,
        "approved_execution_commit": "PLAN_INPUT_UNRESOLVED",
        "adapter_version": "cafef-research-demo-4",
        "field_contract_version": "CAFEF_C1_PRICE_HISTORY_RAW_CANDIDATE_V1",
        "priority_policy": PRIORITY_POLICY,
        "collection_end_date": COLLECTION_END.isoformat(),
        "maximum_history_years": 15,
        "hard_lower_date_boundary": MAX_HISTORY_START.isoformat(),
        "history_policy": "FULL_AVAILABLE_UP_TO_MAX_15Y",
        "universe_snapshot": "cafef_c1_selected_pilot.csv",
        "worker_assignment_hashes": assignment_hashes,
        "request_surface": {
            "required_endpoint": "DataHistory/PriceHistory.ashx",
            "role": "RAW_OHLC_CANDIDATE_AND_MATCHED_NEGOTIATED_COMPONENT_EVIDENCE",
            "parameters": ["ExchangeType", "Symbol", "StartDate", "EndDate", "PageIndex", "PageSize"],
            "date_format": "MM/DD/YYYY",
            "page_index_origin": 1,
            "page_size": 20,
            "observed_ordering": "NEWEST_FIRST",
            "total_count_field": "Data.TotalCount",
            "range_iteration": "NON_OVERLAPPING_CALENDAR_YEAR_CHUNKS_OLDEST_TO_NEWEST",
            "page_iteration": "PAGE_1_THROUGH_CEIL_TOTALCOUNT_DIV_20",
            "stop_condition": "EXACT_EXPECTED_PAGE_COUNT_FROM_VALIDATED_TOTALCOUNT",
            "duplicate_date_policy": "RETAIN_RAW_AND_FLAG_DUPLICATE_DATE",
            "out_of_window_policy": "RETAIN_RAW_EVIDENCE_EXCLUDE_FROM_NORMALIZED_CANDIDATES",
            "early_empty_policy": "PROVIDER_EMPTY_RESPONSE_UNRESOLVED",
            "no_silent_page_skipping": True,
            "no_endless_empty_page_iteration": True,
        },
        "excluded_surface": {
            "endpoint": "TradeHistoryNew.ashx",
            "c1_status": "PLAN_INPUT_UNRESOLVED_NOT_IN_REQUIRED_C1_PLAN",
            "reason": "existing bounded adapter has no date-range parameter and a 100-page ceiling; full 15-year coverage cannot be frozen offline",
        },
        "field_semantics": {
            "GiaMoCua": "RAW_CANDIDATE_OPEN_VND_PER_SHARE_X1000_PENDING_C1_GATE",
            "GiaCaoNhat": "RAW_CANDIDATE_HIGH_VND_PER_SHARE_X1000_PENDING_C1_GATE",
            "GiaThapNhat": "RAW_CANDIDATE_LOW_VND_PER_SHARE_X1000_PENDING_C1_GATE",
            "GiaDongCua": "RAW_CANDIDATE_CLOSE_VND_PER_SHARE_X1000_PENDING_C1_GATE",
            "GiaDieuChinh": "PROVIDER_ADJUSTED_VALIDATION_ONLY_NEVER_DELTA_RESEARCH_PRICE",
            "KhoiLuongKhopLenh": "MATCHED_VOLUME_SHARES",
            "GiaTriKhopLenh": "MATCHED_VALUE_BILLION_VND_X1E9",
            "KLThoaThuan": "NEGOTIATED_VOLUME_SHARES",
            "GtThoaThuan": "NEGOTIATED_VALUE_BILLION_VND_X1E9",
        },
        "request_policy": {
            "per_worker_concurrency": 1,
            "min_interval_seconds": 5.0,
            "timeout_seconds": 20,
            "maximum_attempts": 2,
            "transient_retry_backoff_seconds": [10],
            "retryable": ["NETWORK_TIMEOUT", "HTTP_500", "HTTP_502", "HTTP_503", "HTTP_504"],
            "stop_without_evasion": ["HTTP_401", "HTTP_403", "HTTP_429", "CAPTCHA", "CLOUDFLARE_CHALLENGE", "AUTH_REQUIRED"],
            "anti_bot_bypass": False,
            "captcha_bypass": False,
            "cloudflare_bypass": False,
            "auth_bypass": False,
        },
        "raw_only": {
            "canonical_write": False,
            "research_price_build": False,
            "adjustment_factor_build": False,
            "feature_build": False,
            "adjust_price_role": "VALIDATION_ONLY",
        },
        "artifact_layout": "artifacts/cafef_primary/<c1_run_id>/{plan,worker_01,worker_02,worker_03,worker_04,worker_05,merge}",
        "worker_files": ["raw/", "request_log.jsonl", "failures.jsonl", "resume_state.json", "manifest.json"],
        "resume_requires_exact_match": [
            "plan_id", "worker_assignment_hash", "config_hash", "source_contract_version",
            "code_commit", "history_boundary", "collection_end_date", "raw_file_checksum_state",
        ],
        "resume_behavior": {
            "completed_request": "VERIFY_CHECKSUM_AND_SKIP",
            "failed_transient_request": "RETRY_WITHIN_REMAINING_BUDGET",
            "methodology_or_access_failure": "NO_AUTOMATIC_RETRY",
            "single_ticker_failure": "RECORD_AND_CONTINUE_OTHER_APPROVED_TICKERS",
        },
        "identity_rule": "USE_SECURITY_ID_AND_EVIDENCE_BACKED_INTERVALS; NEVER_CONCATENATE_WITHOUT_EVIDENCE",
        "research_eligibility_effect": "NONE",
        "plan_input_unresolved": [
            "LIQUIDITY_AND_TRADED_VALUE_PERSISTENCE_ARTIFACT",
            "ACTIVE_TRADING_FREQUENCY_ARTIFACT",
            "VERIFIED_INDEX_MEMBERSHIP_ARTIFACT",
            "VERIFIED_MARKET_CAP_OR_SIZE_ARTIFACT",
            "POPULARITY_SIGNAL",
            "LIQUIDITY_BAND_REPRESENTATION_PROOF",
            "VCB_CANONICAL_SECURITY_ID_AND_LISTING_BOUNDARY",
            "THIRTEEN_PARTIAL_IDENTITY_START_BOUNDARIES",
            "TRADEHISTORY_FULL_15Y_PAGINATION_CONTRACT",
            "APPROVED_EXECUTION_COMMIT",
        ],
        "manual_gates": [
            "USER_APPROVES_COMPLETE_C1_PLAN",
            "RIGHTS_EXECUTION_RISK_EXPLICITLY_ACCEPTED",
            "PLAN_INPUT_UNRESOLVED_IDENTITY_ITEMS_RESOLVED_OR_EXCLUDED_BY_APPROVED_REVISION",
            "EXECUTION_COMMIT_FROZEN",
        ],
    }


def _failure_policy() -> dict:
    return {
        "plan_id": PLAN_ID,
        "policy_version": "CAFEF_C1_FAILURE_POLICY_V1",
        "history_boundary_taxonomy": [
            "VERIFIED_LISTING_BOUNDARY", "VERIFIED_IDENTITY_BOUNDARY", "MAX_15Y_BOUNDARY",
            "PROVIDER_HISTORY_BOUNDARY_CONFIRMED", "PROVIDER_EMPTY_RESPONSE_UNRESOLVED",
            "ACCESS_ERROR", "SCHEMA_ERROR", "PAGINATION_ERROR", "UNRESOLVED_EARLY_HISTORY",
        ],
        "rules": {
            "empty_response": "NEVER_INFER_LISTING_OR_PROVIDER_BOUNDARY_WITHOUT_CONTRACT_EVIDENCE",
            "access_error": "STOP_AFFECTED_WORKER_PATH_RECORD_EVIDENCE_DO_NOT_EVADE",
            "schema_error": "STOP_AFFECTED_SECURITY_RANGE_RECORD_RAW_AND_SCHEMA_EVIDENCE",
            "pagination_error": "STOP_AFFECTED_SECURITY_RANGE_NO_SILENT_SKIP",
            "duplicate_date": "RETAIN_ALL_RAW_RESPONSES_FLAG_FOR_MERGE_REVIEW",
            "out_of_window_row": "RETAIN_RAW_EXCLUDE_FROM_REQUESTED_WINDOW_CANDIDATE",
            "unresolved_identity": "STOP_AFFECTED_SECURITY_BEFORE_REQUEST_UNLESS_APPROVED_PLAN_REVISION_RESOLVES_OR_EXCLUDES",
        },
        "worker_terminal_states": ["COMPLETED", "COMPLETED_WITH_RECORDED_FAILURES"],
        "automatic_retry_for_methodology_failure": False,
        "automatic_retry_for_access_control": False,
    }


def _merge_plan() -> bytes:
    text = """# CafeF C1 Raw Merge Plan

## Phạm vi

Đây chỉ là merge plan. C1-PREP không chạy worker và không merge dữ liệu. Merge C1 sau này chỉ tạo unified RAW acquisition artifact; không ghi canonical, research price, adjustment factor hoặc feature.

## Điều kiện bắt đầu

Chỉ bắt đầu khi cả năm worker ở trạng thái `COMPLETED` hoặc `COMPLETED_WITH_RECORDED_FAILURES`, đồng thời plan ID, assignment hash, contract version, code commit và `collection_end_date` khớp tuyệt đối.

## Trình tự deterministic

1. Verify đủ năm worker manifest và terminal state.
2. Verify assignment completeness, raw file checksums và request-log checksums.
3. Đối chiếu request thực tế với security/range/page đã giao; request ngoài plan bị quarantine.
4. Phát hiện duplicate request và duplicate security/date observation. Không average hoặc silently select.
5. Kiểm tra date-window coverage, maximum 15 years, identity interval và một cutoff chung.
6. Aggregate failure taxonomy mà không đổi classification của worker.
7. Ghi unified raw index theo `worker_id`, `security_id`, range start, range end, page index và raw hash.
8. Xuất merge manifest mới tham chiếu immutable worker manifests.

## Cấm tại merge C1

- Không promote canonical.
- Không xây DELTA research price hoặc adjustment factor.
- Không dùng `GiaDieuChinh` làm research price.
- Không suy listing/provider boundary từ empty response.
- Không loại raw conflict chỉ để tạo một row duy nhất.

## C1 success metrics sẽ đo sau execution

Planned-request completion, valid raw response rate, schema consistency, identity consistency, exchange coverage, observed earliest/latest date, observed history depth, duplicate-date rate, invalid-OHLC rate, request/access-control failure rate, pagination completeness, provenance completeness và confidence về raw semantics. C1-PREP không đánh giá các metric này.
"""
    return text.encode("utf-8")


def build_plan(root: Path, output_dir: Path) -> dict:
    root = root.resolve()
    output_dir = output_dir.resolve()
    ranked = _score_candidates(_candidate_universe(root))
    selected, request_rows = _selected_pilot(ranked)
    workers = _partition(selected)
    summary = _partition_summary(selected, workers)

    if len(selected) < 50 or len(selected) > 75:
        raise ValueError(f"pilot size outside planning envelope: {len(selected)}")
    failed_checks = [name for name, passed in summary["checks"].items() if not passed]
    if failed_checks:
        raise ValueError(f"partition checks failed: {failed_checks}")

    ranking_rows = [{**row} for row in ranked]
    candidate_rows = [{**row} for row in ranked]
    selected_rows = [{**row} for row in selected]
    request_rows.sort(key=lambda row: row["security_id"])

    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(output_dir / "cafef_c1_priority_ranking.csv", _csv_bytes(ranking_rows, CSV_COLUMNS["cafef_c1_priority_ranking.csv"]))
    _atomic_write(output_dir / "cafef_c1_candidate_universe.csv", _csv_bytes(candidate_rows, CSV_COLUMNS["cafef_c1_candidate_universe.csv"]))
    _atomic_write(output_dir / "cafef_c1_selected_pilot.csv", _csv_bytes(selected_rows, CSV_COLUMNS["cafef_c1_selected_pilot.csv"]))
    _atomic_write(output_dir / "cafef_c1_request_estimates.csv", _csv_bytes(request_rows, CSV_COLUMNS["cafef_c1_request_estimates.csv"]))

    assignment_hashes = {}
    for worker, rows in workers.items():
        filename = f"cafef_c1_{worker}_assignment.csv"
        data = _csv_bytes(rows, ASSIGNMENT_COLUMNS)
        _atomic_write(output_dir / filename, data)
        assignment_hashes[worker] = _sha256(data)

    summary["worker_assignment_hashes"] = assignment_hashes
    _atomic_write(output_dir / "cafef_c1_partition_summary.json", _stable_json(summary))
    _atomic_write(output_dir / "cafef_c1_crawl_contract.json", _stable_json(_crawl_contract(assignment_hashes)))
    _atomic_write(output_dir / "cafef_c1_failure_policy.json", _stable_json(_failure_policy()))
    _atomic_write(output_dir / "cafef_c1_merge_plan.md", _merge_plan())

    input_paths = [
        root / CURRENT_UNIVERSE_SOURCE,
        root / REPRESENTATIVE_PILOT_SOURCE,
        root / "configs/data/m1_scale.securities.v1.json",
        root / TRANSITION_SOURCE,
        root / "docs/crawl/M1_RECOVERY_PILOT_REPORT_A1_A6.md",
        root / "docs/crawl/M1_DATA_ENRICHMENT_AND_UNIVERSE_EXPANSION_MASTER_PLAN.md",
        root / "docs/crawl/sources/CAFEF.md",
        root / "scripts/plan_cafef_c1_workers.py",
    ]
    output_hashes = {
        path.name: _file_hash(path)
        for path in sorted(output_dir.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "stage": "C1-PREP",
        "status": "COMPLETED / USER_MANUAL_REVIEW_REQUIRED",
        "planning_as_of_date": COLLECTION_END.isoformat(),
        "planning_base_commit": PLANNING_BASE_COMMIT,
        "priority_policy": PRIORITY_POLICY,
        "history_policy": "FULL_AVAILABLE_UP_TO_MAX_15Y",
        "collection_end_date": COLLECTION_END.isoformat(),
        "pilot_security_count": len(selected),
        "worker_count": len(workers),
        "input_hashes": {path.relative_to(root).as_posix(): _file_hash(path) for path in input_paths},
        "output_hashes": output_hashes,
        "validation_checks": summary["checks"],
        "plan_input_unresolved": [
            "LIQUIDITY_INDEX_SIZE_POPULARITY_SIGNALS",
            "LIQUIDITY_BAND_REPRESENTATION_PROOF",
            "VCB_CANONICAL_SECURITY_ID_AND_LISTING_BOUNDARY",
            "THIRTEEN_PARTIAL_IDENTITY_START_BOUNDARIES",
            "TRADEHISTORY_FULL_15Y_PAGINATION_CONTRACT",
            "APPROVED_EXECUTION_COMMIT",
        ],
        "actual_market_data_requests": 0,
        "actual_crawl_executed": False,
        "canonical_mutations": 0,
        "feature_rebuild": False,
        "next_allowed_action": "USER MANUAL REVIEW OF C1 CRAWL PLAN",
    }
    _atomic_write(output_dir / "manifest.json", _stable_json(manifest))
    return {"manifest": manifest, "summary": summary}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic offline CafeF C1 planning artifacts")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/crawl/plans/cafef_c1_prep_v1"),
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else args.root / args.output
    result = build_plan(args.root, output)
    print(json.dumps({
        "plan_id": PLAN_ID,
        "pilot_security_count": result["manifest"]["pilot_security_count"],
        "estimated_total_requests": result["summary"]["estimated_total_requests"],
        "actual_market_data_requests": 0,
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
