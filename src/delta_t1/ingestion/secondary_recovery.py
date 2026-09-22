"""Stage A4 secondary-source recovery pilot.

The planner and reconciler are deterministic. Network activity is possible only
through the explicitly supplied CafeF provider. This module writes evidence
artifacts and never mutates the canonical input.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
from statistics import median

from ..artifact_ids import new_artifact_id
from ..io import atomic_write, digest, encoded, now, read_json, read_rows, write_json, write_rows
from .local_salvage import write_text_parquet
from .primary_recovery import _git_commit, _inside, _verify_artifacts
from .sources.base import AccessControlError, RateLimitError, SemanticValidationError
from .sources.cafef import (
    ADAPTER_VERSION as CAFE_ADAPTER_VERSION,
    PRICE_UNIT,
    cafef_trade_date,
    classify_cafef_page_row,
    map_trade_history_row,
)


STAGE = "A4 — Secondary Source Recovery Pilot"
ALLOWED_STATUSES = {
    "MATCH", "RECOVERED_PRIMARY", "RECOVERED_SECONDARY_CONFIRMED",
    "MISSING_ON_SOURCE", "VALUE_CONFLICT", "UNIT_CONFLICT",
    "PRICE_BASIS_CONFLICT", "TIMING_CONFLICT", "IDENTITY_CONFLICT",
    "UNRESOLVED_MISSING",
}
UNKNOWN_CAFEF_BASIS = "CAFEF_ADJUSTMENT_METHOD_UNKNOWN"
_CANDIDATE_COLUMNS = (
    "candidate_id", "request_id", "security_id", "ticker", "exchange",
    "trade_date", "provider", "provider_timestamp", "raw_path", "raw_sha256",
    "raw_row_sha256", "fetched_at", "price_unit", "volume_unit", "price_basis",
    "open", "high", "low", "close", "adjusted_close", "volume",
    "reconciliation_status", "reason", "overlap_before", "overlap_after",
    "median_ratio_before", "median_ratio_after", "max_ratio_deviation",
    "normalized_row_json", "raw_row_json",
)


def _finite_positive(value, *, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if value != value or value in (float("inf"), float("-inf")):
        return False
    return value >= 0 if allow_zero else value > 0


def validate_price_basis(before_pairs, after_pairs, *, min_each_side=5,
                         max_level_deviation=0.02,
                         max_ratio_deviation=0.02,
                         max_regime_shift=0.02):
    """Diagnose the primary canonical close / CafeF verified ClosePrice relation.

    A ratio must be close to one and stable on both sides. A stable non-one
    multiplier is not silently applied because multiplier inference is forbidden.
    """
    if min_each_side < 1:
        raise ValueError("min_each_side must be positive")
    for value in (max_level_deviation, max_ratio_deviation, max_regime_shift):
        if not 0 <= value <= 0.25:
            raise ValueError("price-basis tolerances must be between 0 and 0.25")

    def ratios(pairs):
        values = []
        for primary, secondary in pairs:
            if _finite_positive(primary) and _finite_positive(secondary):
                values.append(float(primary) / float(secondary))
        return values

    before, after = ratios(before_pairs), ratios(after_pairs)
    result = {
        "overlap_before": len(before), "overlap_after": len(after),
        "median_ratio_before": None, "median_ratio_after": None,
        "max_ratio_deviation": None, "regime_shift": None,
        "compatible": False,
    }
    if len(before) < min_each_side or len(after) < min_each_side:
        result.update(status="UNRESOLVED_MISSING", reason="INSUFFICIENT_TWO_SIDED_OVERLAP")
        return result
    before_median, after_median = median(before), median(after)
    combined_median = median(before + after)
    deviation = max(abs(value / combined_median - 1.0) for value in before + after)
    shift = abs(after_median / before_median - 1.0)
    level = abs(combined_median - 1.0)
    result.update(
        median_ratio_before=before_median,
        median_ratio_after=after_median,
        max_ratio_deviation=deviation,
        regime_shift=shift,
        median_ratio_combined=combined_median,
        level_deviation=level,
    )
    if level > max_level_deviation:
        result.update(status="PRICE_BASIS_CONFLICT", reason="RATIO_LEVEL_DIFFERS_FROM_ONE")
    elif deviation > max_ratio_deviation:
        result.update(status="PRICE_BASIS_CONFLICT", reason="RATIO_NOT_STABLE")
    elif shift > max_regime_shift:
        result.update(status="PRICE_BASIS_CONFLICT", reason="RATIO_REGIME_SHIFT")
    else:
        result.update(status="MATCH", reason="PRICE_BASIS_OVERLAP_COMPATIBLE", compatible=True)
    return result


def _load_a3_results(path):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return [row for row in rows if row.get("status") != "RECOVERED"]


def validate_a3_scope(rows, selected_symbols):
    selected = {value.upper() for value in selected_symbols
                if isinstance(value, str) and value}
    result_symbols = {row.get("ticker", "").upper() for row in rows}
    if not selected or "" in result_symbols or not result_symbols <= selected:
        raise ValueError("A3 results contain ticker outside selected_symbols")
    return selected


def build_request_plan(a3_rows, securities, prices, *, symbols=(), overlap_sessions=20,
                       max_pages=100):
    if not 1 <= overlap_sessions <= 40:
        raise ValueError("overlap_sessions must be between 1 and 40")
    if not 1 <= max_pages <= 100:
        raise ValueError("max_pages must be between 1 and 100")
    selected = tuple(dict.fromkeys(value.upper() for value in symbols))
    allowed = {row["ticker"].upper() for row in a3_rows}
    if selected and not set(selected) <= allowed:
        raise ValueError("A4 symbols must be an unresolved A3 subset")
    use = set(selected) if selected else allowed
    security_by_ticker = {row["ticker"].upper(): row for row in securities}
    primary = defaultdict(dict)
    for row in prices:
        value = row.get("adj_close")
        if _finite_positive(value):
            primary[row["security_id"]][row["trade_date"]] = float(value)
    targets = defaultdict(set)
    for row in a3_rows:
        ticker = row["ticker"].upper()
        if ticker in use:
            targets[ticker].add(row["trade_date"])
    requests = []
    for ticker in sorted(targets):
        security = security_by_ticker.get(ticker)
        if security is None:
            raise ValueError(f"A3 ticker missing from canonical security master: {ticker}")
        observed = sorted(primary[security["security_id"]])
        contexts = {}
        needed = set(targets[ticker])
        for target in sorted(targets[ticker]):
            before = [value for value in observed if value < target][-overlap_sessions:]
            after = [value for value in observed if value > target][:overlap_sessions]
            contexts[target] = {"before": before, "after": after}
            needed.update(before)
            needed.update(after)
        requests.append({
            "request_id": f"cafef-{ticker}", "provider": "cafef",
            "acquisition_path": "cafef_direct_trade_history",
            "security_id": security["security_id"], "ticker": ticker,
            "exchange": security["exchange"], "targeted_dates": sorted(targets[ticker]),
            "overlap_context": contexts, "earliest_needed": min(needed),
            "latest_needed": max(needed), "overlap_sessions": overlap_sessions,
            "page_size": 30, "max_pages": max_pages,
            "strategy": "SECONDARY_BOUNDED_PAGINATION_TO_EARLIEST_CONTEXT",
        })
    if not requests:
        raise ValueError("A4 request plan is empty")
    return requests, primary


def _preserve_page(output, request, page, response, validation_status, validation_error=""):
    raw_dir = output / "secondary_recovery_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{request['request_id']}-page-{page:03d}"
    raw_path = raw_dir / f"{stem}.json"
    body = response.get("body")
    if not isinstance(body, bytes):
        body = encoded(response.get("payload"))
    atomic_write(raw_path, body)
    metadata = {
        "request_id": request["request_id"], "page_index": page,
        "url": response.get("url"), "http_status": response.get("status"),
        "fetched_at": now(), "adapter_version": CAFE_ADAPTER_VERSION,
        "raw_path": raw_path.relative_to(output).as_posix(),
        "raw_sha256": digest(body), "validation_status": validation_status,
        "validation_error": validation_error,
    }
    write_json(raw_dir / f"{stem}.metadata.json", metadata)
    return metadata


def _candidate_from_raw(request, raw, mapped, raw_meta, basis, status, reason):
    normalized = {
        "open": None, "high": None, "low": None,
        "close": mapped.get("cafef_close_price"),
        "adjusted_close": mapped.get("cafef_adjust_price"),
        "volume": mapped.get("matched_volume"), "price_unit": mapped.get("price_unit"),
        "volume_unit": "SHARES", "price_basis": UNKNOWN_CAFEF_BASIS,
    }
    candidate_id = "cafef:" + digest(encoded({
        "security_id": request["security_id"], "trade_date": mapped["trade_date"],
        "raw": raw,
    }))[:24]
    return {
        "candidate_id": candidate_id, "request_id": request["request_id"],
        "security_id": request["security_id"], "ticker": request["ticker"],
        "exchange": request["exchange"], "trade_date": mapped["trade_date"],
        "provider": "cafef", "provider_timestamp": raw.get("TradeDate"),
        "raw_path": raw_meta["raw_path"], "raw_sha256": raw_meta["raw_sha256"],
        "raw_row_sha256": digest(encoded(raw)), "fetched_at": raw_meta["fetched_at"],
        "price_unit": PRICE_UNIT, "volume_unit": "SHARES",
        "price_basis": UNKNOWN_CAFEF_BASIS, **normalized,
        "reconciliation_status": status, "reason": reason,
        "overlap_before": basis.get("overlap_before"),
        "overlap_after": basis.get("overlap_after"),
        "median_ratio_before": basis.get("median_ratio_before"),
        "median_ratio_after": basis.get("median_ratio_after"),
        "max_ratio_deviation": basis.get("max_ratio_deviation"),
        "normalized_row_json": json.dumps(normalized, ensure_ascii=False, sort_keys=True),
        "raw_row_json": json.dumps(raw, ensure_ascii=False, sort_keys=True),
    }


def _rejected_candidate(request, raw, raw_meta, trade_date, status, reason):
    normalized = {"open": None, "high": None, "low": None, "close": None,
                  "adjusted_close": None, "volume": None,
                  "price_unit": None, "volume_unit": None, "price_basis": None}
    return {
        "candidate_id": "cafef:" + digest(encoded({"request_id": request["request_id"],
                                                      "trade_date": trade_date, "raw": raw}))[:24],
        "request_id": request["request_id"], "security_id": request["security_id"],
        "ticker": request["ticker"], "exchange": request["exchange"],
        "trade_date": trade_date, "provider": "cafef",
        "provider_timestamp": raw.get("TradeDate") if isinstance(raw, dict) else None,
        "raw_path": raw_meta["raw_path"], "raw_sha256": raw_meta["raw_sha256"],
        "raw_row_sha256": digest(encoded(raw)), "fetched_at": raw_meta["fetched_at"],
        **normalized, "reconciliation_status": status, "reason": reason,
        "overlap_before": 0, "overlap_after": 0, "median_ratio_before": None,
        "median_ratio_after": None, "max_ratio_deviation": None,
        "normalized_row_json": json.dumps(normalized, ensure_ascii=False, sort_keys=True),
        "raw_row_json": json.dumps(raw, ensure_ascii=False, sort_keys=True),
    }


def _invalid_row_target(raw, targeted_dates):
    """Link an invalid row only when its calendar date is explicit evidence."""
    value = raw.get("TradeDate") if isinstance(raw, dict) else None
    try:
        parsed = cafef_trade_date(value)
    except (TypeError, ValueError, SemanticValidationError):
        parsed = None
        if isinstance(value, str) and len(value) >= 10:
            prefix = value[:10]
            try:
                date.fromisoformat(prefix)
                parsed = prefix
            except ValueError:
                pass
    return parsed if parsed in targeted_dates else None


def _validate_target(request, raw, mapped, cafef_by_date, primary, *, min_overlap_each_side,
                     max_level_deviation, max_ratio_deviation, max_regime_shift):
    if mapped["symbol"] != request["ticker"] or mapped["exchange"] != request["exchange"]:
        return {"status": "IDENTITY_CONFLICT", "reason": "SECURITY_IDENTITY_MISMATCH"}
    if mapped["price_unit"] != PRICE_UNIT:
        return {"status": "UNIT_CONFLICT", "reason": "PRICE_UNIT_NOT_VND_PER_SHARE"}
    context = request["overlap_context"][mapped["trade_date"]]

    def samples(dates):
        return [{"trade_date": day, "primary_close": primary.get(day),
                 "secondary_close": cafef_by_date.get(day, {}).get("mapped", {}).get("cafef_close_price")}
                for day in dates]

    before, after = samples(context["before"]), samples(context["after"])
    result = validate_price_basis(
        [(row["primary_close"], row["secondary_close"]) for row in before],
        [(row["primary_close"], row["secondary_close"]) for row in after],
        min_each_side=min_overlap_each_side,
        max_level_deviation=max_level_deviation,
        max_ratio_deviation=max_ratio_deviation,
        max_regime_shift=max_regime_shift,
    )
    for row in before + after:
        if _finite_positive(row["primary_close"]) and _finite_positive(row["secondary_close"]):
            row["primary_secondary_ratio"] = row["primary_close"] / row["secondary_close"]
        else:
            row["primary_secondary_ratio"] = None
    result["overlap_samples_before"] = before
    result["overlap_samples_after"] = after
    result["diagnostic_status"] = result.pop("status")
    result["diagnostic_reason"] = result.pop("reason")
    result["diagnostic_compatible"] = result.get("compatible", False)
    blockers = ["PRICE_BASIS_ACCEPTANCE_POLICY_UNAPPROVED",
                "CAFEF_OHLC_CONTRACT_UNSUPPORTED"]
    if not _finite_positive(mapped.get("matched_volume"), allow_zero=True):
        blockers.append("INVALID_VOLUME")
    if not _finite_positive(mapped.get("cafef_close_price")):
        blockers.append("INVALID_CLOSE")
    if not _finite_positive(mapped.get("cafef_adjust_price")):
        blockers.append("ADJUST_PRICE_UNAVAILABLE")
    result["validation_blockers"] = blockers
    if result["diagnostic_status"] == "PRICE_BASIS_CONFLICT":
        result.update(status="PRICE_BASIS_CONFLICT",
                      reason=result["diagnostic_reason"], compatible=False)
    else:
        result.update(status="UNRESOLVED_MISSING",
                      reason="PRICE_BASIS_ACCEPTANCE_POLICY_UNAPPROVED",
                      compatible=False)
    return result


def execute_request_plan(requests, *, provider, output, primary_by_security,
                         min_overlap_each_side=5, max_level_deviation=0.02,
                         max_ratio_deviation=0.02, max_regime_shift=0.02,
                         progress=None):
    candidates, evidence, request_status = [], [], []
    page_calls = 0
    for number, request in enumerate(requests, 1):
        if progress:
            progress(f"[{number}/{len(requests)}] CafeF {request['ticker']} targets={len(request['targeted_dates'])}")
        cafef_by_date, rejected_by_target = {}, {}
        page_errors, last_oldest, stopped = [], None, "MAX_PAGES"
        pages_requested = 0
        for page in range(1, request["max_pages"] + 1):
            pages_requested = page
            page_calls += 1
            response = None
            try:
                response = provider.acquire_trade_history_page({
                    "symbol": request["ticker"], "page_index": page, "page_size": 30})
                payload = response.get("payload")
                if not isinstance(payload, dict) or payload.get("Success") is not True or not isinstance(payload.get("Data"), list):
                    raise SemanticValidationError("CafeF envelope is invalid")
                raw_rows = payload["Data"]
                meta = _preserve_page(output, request, page, response, "ACCEPTED_ENVELOPE")
                if not raw_rows:
                    stopped = "EMPTY_PAGE"
                    break
                page_dates = []
                for index, raw in enumerate(raw_rows):
                    if classify_cafef_page_row(raw.get("TradeDate"), page, index) == "CURRENT_SNAPSHOT":
                        continue
                    try:
                        mapped = map_trade_history_row(raw, request["ticker"], request["exchange"])
                    except (KeyError, TypeError, ValueError, SemanticValidationError) as exc:
                        page_errors.append(f"page={page} row={index}: {type(exc).__name__}: {exc}")
                        target = _invalid_row_target(raw, set(request["targeted_dates"]))
                        if target:
                            raw_symbol = raw.get("Symbol") if isinstance(raw, dict) else None
                            if isinstance(raw_symbol, str) and raw_symbol.upper() != request["ticker"]:
                                conflict = ("IDENTITY_CONFLICT", "SECONDARY_SYMBOL_IDENTITY_MISMATCH")
                            else:
                                try:
                                    cafef_trade_date(raw.get("TradeDate"))
                                    conflict = ("UNRESOLVED_MISSING", "SECONDARY_ROW_SCHEMA_INVALID")
                                except (TypeError, ValueError, SemanticValidationError):
                                    conflict = ("TIMING_CONFLICT", "PROVIDER_TIMESTAMP_INVALID")
                            rejected_by_target[target] = {
                                "raw": raw, "meta": meta, "status": conflict[0],
                                "reason": conflict[1],
                            }
                        continue
                    day = mapped["trade_date"]
                    page_dates.append(day)
                    previous = cafef_by_date.get(day)
                    if previous and previous["raw"] != raw:
                        previous["duplicate_conflict"] = True
                    else:
                        cafef_by_date[day] = {"raw": raw, "mapped": mapped, "meta": meta}
                if page_dates:
                    last_oldest = min(page_dates)
                    if last_oldest <= request["earliest_needed"]:
                        stopped = "EARLIEST_CONTEXT_REACHED"
                        break
                if len(raw_rows) < 30:
                    stopped = "SHORT_PAGE"
                    break
            except (AccessControlError, RateLimitError, SemanticValidationError,
                    KeyError, TypeError, ValueError, OSError) as exc:
                if response is not None:
                    _preserve_page(output, request, page, response, "REJECTED_ENVELOPE", str(exc))
                page_errors.append(f"page={page}: {type(exc).__name__}: {exc}")
                stopped = "REQUEST_FAILED"
                break

        primary = primary_by_security[request["security_id"]]
        for target in request["targeted_dates"]:
            found = cafef_by_date.get(target)
            base = {
                "request_id": request["request_id"], "security_id": request["security_id"],
                "ticker": request["ticker"], "exchange": request["exchange"],
                "trade_date": target, "provider": "cafef",
            }
            if found is None:
                rejected = rejected_by_target.get(target)
                if rejected:
                    candidate = _rejected_candidate(
                        request, rejected["raw"], rejected["meta"], target,
                        rejected["status"], rejected["reason"])
                    candidates.append(candidate)
                    item = {**base, "reconciliation_status": rejected["status"],
                            "reason": rejected["reason"], "overlap_before": 0,
                            "overlap_after": 0, "raw_path": candidate["raw_path"],
                            "candidate_id": candidate["candidate_id"]}
                else:
                    item = {**base, "reconciliation_status": "MISSING_ON_SOURCE",
                            "reason": "SECONDARY_PROVIDER_RETURNED_NO_TARGET_ROW",
                            "overlap_before": 0, "overlap_after": 0,
                            "raw_path": "", "candidate_id": ""}
            elif found.get("duplicate_conflict"):
                duplicate_basis = {"overlap_before": 0, "overlap_after": 0}
                candidate = _candidate_from_raw(
                    request, found["raw"], found["mapped"], found["meta"],
                    duplicate_basis, "VALUE_CONFLICT", "CONFLICTING_DUPLICATE_SECONDARY_ROWS")
                candidates.append(candidate)
                item = {**base, "reconciliation_status": "VALUE_CONFLICT",
                        "reason": "CONFLICTING_DUPLICATE_SECONDARY_ROWS",
                        "overlap_before": 0, "overlap_after": 0,
                        "raw_path": found["meta"]["raw_path"],
                        "candidate_id": candidate["candidate_id"]}
            else:
                basis = _validate_target(
                    request, found["raw"], found["mapped"], cafef_by_date, primary,
                    min_overlap_each_side=min_overlap_each_side,
                    max_level_deviation=max_level_deviation,
                    max_ratio_deviation=max_ratio_deviation,
                    max_regime_shift=max_regime_shift)
                status = basis["status"]
                if status not in ALLOWED_STATUSES:
                    raise AssertionError(f"invalid A4 reconciliation status: {status}")
                candidate = _candidate_from_raw(
                    request, found["raw"], found["mapped"], found["meta"],
                    basis, status, basis["reason"])
                candidates.append(candidate)
                item = {**base, "reconciliation_status": status,
                        "reason": basis["reason"], "raw_path": candidate["raw_path"],
                        "candidate_id": candidate["candidate_id"],
                        "overlap_before": basis.get("overlap_before", 0),
                        "overlap_after": basis.get("overlap_after", 0),
                        "price_basis_validation": basis}
            evidence.append(item)
        request_status.append({
            "request_id": request["request_id"], "ticker": request["ticker"],
            "status": "FAILED" if stopped == "REQUEST_FAILED" else "COMPLETE",
            "stop_reason": stopped, "pages_requested": pages_requested,
            "oldest_observed": last_oldest, "mapping_errors": page_errors,
        })
    return candidates, evidence, request_status, page_calls


def _report(manifest):
    metrics = manifest["metrics"]
    breakdown = manifest["reconciliation_status_breakdown"]
    lines = [
        "# Stage A4 — Secondary Source Recovery Pilot", "",
        f"- Run ID: `{manifest['run_id']}`", f"- Stage result: `{manifest['status']}`",
        f"- Logical requests: `{metrics['requests']}`", f"- Network page requests: `{metrics['network_page_requests']}`",
        f"- Rows requested: `{metrics['rows_requested']}`", f"- Recovered: `{metrics['rows_recovered']}`",
        f"- Canonical mutations: `{manifest['canonical_mutations']}`", "",
        "## Reconciliation status", "", "| Status | Rows |", "|---|---:|",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in sorted(breakdown.items()))
    lines.extend([
        "", "## Price-basis policy", "",
        "Đối chiếu diagnostic `canonical adj_close / CafeF ClosePrice` trên 20 phiên trước và 20 phiên sau mỗi gap. "
        "Ngưỡng tolerance không có quyền acceptance. Adapter CafeF hiện tại chưa xác minh OHLC và adjustment basis, "
        "nên mọi candidate fail-closed; không suy multiplier, không average, không nội suy.",
        "", "## Artifacts", "", "- `secondary_recovery_requests.jsonl`",
        "- `secondary_recovery_evidence.jsonl`", "- `secondary_recovery_raw/`",
        "- `secondary_recovery_candidates.parquet`", "- `reconciliation_report.json`",
        "- `manifest.json`", "", "## STOP", "", "Chờ review kết quả chạy thực tế; không tự động chuyển Stage A5.",
    ])
    return "\n".join(lines).encode("utf-8")


def build_stage_a4(canonical_path, a1_path, a2_path, a3_path, *, root, provider,
                   symbols=(), overlap_sessions=20, max_pages=100,
                   min_overlap_each_side=20, max_level_deviation=0.02,
                   max_ratio_deviation=0.02, max_regime_shift=0.02,
                   progress=None):
    if provider is None:
        raise ValueError("A4 execution requires an explicit CafeF provider")
    if overlap_sessions != 20 or min_overlap_each_side != 20:
        raise ValueError("A4 evidence contract requires 20 overlap sessions on each side")
    root = Path(root).resolve()
    canonical_path = _inside(canonical_path, root / "data" / "canonical", "canonical path")
    base = root / "artifacts" / "data_enrichment"
    a1_path, a2_path, a3_path = (_inside(value, base, label) for value, label in (
        (a1_path, "A1 path"), (a2_path, "A2 path"), (a3_path, "A3 path")))
    cm, m1, m2, m3 = (read_json(path / "manifest.json") for path in
                      (canonical_path, a1_path, a2_path, a3_path))
    if cm.get("canonical_promotion_status") != "PASS" or cm.get("synthetic") is not False:
        raise ValueError("A4 requires a real approved canonical baseline")
    if m1.get("status") != "PASS" or m1.get("canonical_run_id") != cm.get("run_id"):
        raise ValueError("A4 requires matching A1 PASS evidence")
    if (m2.get("status") != "PASS" or m2.get("canonical_run_id") != cm.get("run_id")
            or m2.get("a1_run_id") != m1.get("run_id")):
        raise ValueError("A4 requires matching A2 PASS evidence")
    if (m3.get("stage") != "A3 — Primary Provider Recovery Pilot"
            or m3.get("status") not in ("PASS", "PARTIAL")
            or m3.get("canonical_run_id") != cm.get("run_id") or m3.get("a1_run_id") != m1.get("run_id")
            or m3.get("a2_run_id") != m2.get("run_id")):
        raise ValueError("A4 requires a matching A3 evidence chain")
    if m3.get("metrics", {}).get("rows_recovered") != 0:
        raise ValueError("A4 pilot contract expects the supplied A3 run to recover zero rows")
    for path, manifest, label in ((canonical_path, cm, "canonical"), (a1_path, m1, "A1"),
                                  (a2_path, m2, "A2"), (a3_path, m3, "A3")):
        _verify_artifacts(path, manifest, label)
    unresolved = _load_a3_results(a3_path / "primary_recovery_results.csv")
    validate_a3_scope(unresolved, m3.get("selected_symbols", []))
    securities = read_rows(canonical_path / "clean" / "securities.jsonl")
    prices = read_rows(canonical_path / "clean" / "prices_daily.jsonl")
    requested_symbols = tuple(value.upper() for value in symbols)
    if requested_symbols and not set(requested_symbols) <= set(m3.get("selected_symbols", [])):
        raise ValueError("explicit A4 symbols must be an A3 pilot subset")
    requests, primary = build_request_plan(
        unresolved, securities, prices, symbols=requested_symbols,
        overlap_sessions=overlap_sessions, max_pages=max_pages)

    run_id = new_artifact_id("m1-a4-secondary-recovery")
    output = base / run_id
    output.mkdir(parents=True, exist_ok=False)
    write_rows(output / "secondary_recovery_requests.jsonl", requests)
    candidates, evidence, request_status, page_calls = execute_request_plan(
        requests, provider=provider, output=output, primary_by_security=primary,
        min_overlap_each_side=min_overlap_each_side,
        max_level_deviation=max_level_deviation,
        max_ratio_deviation=max_ratio_deviation,
        max_regime_shift=max_regime_shift, progress=progress)
    candidates.sort(key=lambda row: (row["ticker"], row["trade_date"]))
    evidence.sort(key=lambda row: (row["ticker"], row["trade_date"]))
    write_rows(output / "secondary_recovery_evidence.jsonl", evidence)
    write_text_parquet(output / "secondary_recovery_candidates.parquet", candidates,
                       _CANDIDATE_COLUMNS, creator="delta-t1-a4-stdlib-parquet")
    breakdown = Counter(row["reconciliation_status"] for row in evidence)
    reconciliation = {
        "allowed_statuses": sorted(ALLOWED_STATUSES),
        "status_breakdown": dict(sorted(breakdown.items())),
        "rows_requested": len(evidence),
        "rows_recovered": breakdown["RECOVERED_SECONDARY_CONFIRMED"],
        "average_sources": False, "canonical_mutations": 0,
        "request_status": request_status,
    }
    write_json(output / "reconciliation_report.json", reconciliation)
    config = {
        "symbols": list(requested_symbols), "overlap_sessions": overlap_sessions,
        "max_pages": max_pages, "min_overlap_each_side": min_overlap_each_side,
        "max_level_deviation": max_level_deviation,
        "max_ratio_deviation": max_ratio_deviation,
        "max_regime_shift": max_regime_shift,
    }
    failed = any(row["status"] == "FAILED" for row in request_status)
    recovered_count = breakdown["RECOVERED_SECONDARY_CONFIRMED"]
    status = "PASS" if not failed and recovered_count == len(evidence) else "PARTIAL"
    manifest = {
        "run_id": run_id, "stage": STAGE, "status": status, "created_at": now(),
        "git_commit": _git_commit(root), "config_hash": digest(encoded(config)),
        "canonical_run_id": cm["run_id"], "a1_run_id": m1["run_id"],
        "a2_run_id": m2["run_id"], "a3_run_id": m3["run_id"],
        "input_artifact_ids": [cm["run_id"], m1["run_id"], m2["run_id"], m3["run_id"]],
        "input_hashes": {label: digest((path / "manifest.json").read_bytes()) for label, path in
                         (("canonical_manifest", canonical_path), ("a1_manifest", a1_path),
                          ("a2_manifest", a2_path), ("a3_manifest", a3_path))},
        "provider": "cafef", "provider_versions": {"cafef": CAFE_ADAPTER_VERSION},
        "adapter_versions": {"cafef": CAFE_ADAPTER_VERSION},
        "selected_symbols": [row["ticker"] for row in requests],
        "network_requests": page_calls, "canonical_mutations": 0,
        "synthetic_rows": 0, "imputed_rows": 0,
        "reconciliation_status_breakdown": dict(sorted(breakdown.items())),
        "metrics": {
            "requests": len(requests), "network_page_requests": page_calls,
            "rows_requested": len(evidence),
            "rows_recovered": breakdown["RECOVERED_SECONDARY_CONFIRMED"],
            "rows_unresolved": len(evidence) - breakdown["RECOVERED_SECONDARY_CONFIRMED"],
        },
        "limitations": [
            "CafeF adapter v3 does not verify OHLC semantics; no candidate can be promoted",
            "CafeF AdjustPrice basis remains CAFEF_ADJUSTMENT_METHOD_UNKNOWN",
            "2% ratio tolerances are diagnostics only; acceptance policy is unapproved",
            "A4 writes evidence only and does not promote or rebuild canonical/features",
        ],
    }
    atomic_write(output / "stage_a4_report.md", _report(manifest))
    manifest["artifacts"] = {path.relative_to(output).as_posix(): digest(path.read_bytes())
                             for path in sorted(output.rglob("*")) if path.is_file()}
    write_json(output / "manifest.json", manifest)
    return output, manifest
