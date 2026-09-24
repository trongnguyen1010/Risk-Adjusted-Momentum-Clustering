"""Offline post-crawl audit and CafeF-primary field-readiness assessment.

This module never performs network I/O and never writes canonical tables. It converts
checksummed PriceHistory evidence into provider-qualified candidates, then reports what
the current evidence can and cannot populate under DELTA contracts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from delta_t1.contracts import schema
from delta_t1.io import atomic_write, encoded, write_json, write_rows


NORMALIZED_CONTRACT_VERSION = "CAFEF_PRIMARY_MARKET_CANDIDATE_V1_0"
AUDIT_CONTRACT_VERSION = "CAFEF_C2_C3_OFFLINE_AUDIT_V1_0"
PRICE_BASIS_STATUS = "UNRESOLVED_MANUAL_REVIEW_REQUIRED"
PROMOTION_STATUS = "CANDIDATE_ONLY_NOT_CANONICAL"
SOURCE_FIELDS = (
    "Symbol", "Ngay", "GiaDieuChinh", "GiaDongCua", "ThayDoi",
    "KhoiLuongKhopLenh", "GiaTriKhopLenh", "KLThoaThuan", "GtThoaThuan",
    "GiaMoCua", "GiaCaoNhat", "GiaThapNhat",
)

TICKER_QUALITY_COLUMNS = (
    "execution_order", "security_id", "ticker", "exchange", "source_run_id",
    "reuse_status", "raw_audit_status", "request_count", "raw_page_count",
    "normalized_row_count", "valid_candidate_row_count", "quarantined_row_count",
    "first_observed_date", "last_observed_date",
    "observed_span_years", "duplicate_date_count", "conflicting_duplicate_count",
    "invalid_source_row_count", "invalid_ohlc_count", "nonpositive_price_count",
    "null_ohlc_count", "zero_matched_volume_count", "exchange_union_missing_count",
    "exchange_union_coverage_rate", "minimum_3y_history_evidence",
    "identity_interval_without_rows_count", "canonical_price_ready", "quality_status",
    "blocking_reasons",
)

FIELD_COVERAGE_COLUMNS = (
    "table", "field", "nullable", "source_evidence", "coverage_state",
    "semantic_status", "candidate_source_field", "observed_row_count",
    "observed_non_null_count", "observed_non_null_rate", "canonical_fill_status",
    "blocking_reason",
)

TABLE_READINESS_COLUMNS = (
    "table", "total_field_count", "fields_with_source_evidence",
    "canonical_fillable_field_count", "unavailable_or_blocked_field_count",
    "required_field_count", "required_fields_available",
    "required_fields_blocked_or_missing", "nullable_fields_unavailable",
    "table_status", "primary_blockers",
)

DISCONTINUITY_COLUMNS = (
    "security_id", "ticker", "trade_date", "previous_trade_date",
    "provider_adjustment_ratio", "previous_adjustment_ratio",
    "ratio_change", "raw_close_return", "diagnostic_flags", "evidence_status",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _csv_bytes(rows: list[dict], columns: tuple[str, ...]) -> bytes:
    import io

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows([{column: row.get(column, "") for column in columns} for row in rows])
    return stream.getvalue().encode("utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _quarter_intersections(start: date, end: date):
    cursor = start
    while cursor <= end:
        quarter_month = ((cursor.month - 1) // 3) * 3 + 1
        next_month = quarter_month + 3
        next_quarter = date(cursor.year + 1, 1, 1) if next_month == 13 else date(cursor.year, next_month, 1)
        range_end = min(end, next_quarter - timedelta(days=1))
        yield cursor, range_end
        cursor = range_end + timedelta(days=1)


def _expected_ranges(plan_row: dict[str, str]) -> list[dict]:
    target_start = date.fromisoformat(plan_row["base_5y_target_start"])
    target_end = date.fromisoformat(plan_row["base_5y_target_end"])
    expected: list[dict] = []
    for interval in json.loads(plan_row["identity_intervals"]):
        interval_start = max(target_start, date.fromisoformat(interval["effective_from"]))
        interval_end = min(
            target_end,
            date.fromisoformat(interval["effective_to"]) if interval.get("effective_to") else target_end,
        )
        if interval_start > interval_end:
            continue
        for range_start, range_end in _quarter_intersections(interval_start, interval_end):
            expected.append({
                "exchange": interval["exchange"],
                "effective_from": interval["effective_from"],
                "effective_to": interval.get("effective_to"),
                "range_start": range_start,
                "range_end": range_end,
            })
    return expected


def _entry_covers(entry: dict, expected: dict) -> bool:
    return (
        entry.get("exchange") == expected["exchange"]
        and entry.get("identity_interval_effective_from") == expected["effective_from"]
        and entry.get("identity_interval_effective_to") == expected["effective_to"]
        and date.fromisoformat(entry["requested_start"]) <= expected["range_start"]
        and date.fromisoformat(entry["requested_end"]) >= expected["range_end"]
    )


def _validate_range(entries: list[tuple[str, dict]]) -> list[str]:
    issues: list[str] = []
    expected_pages = {int(entry.get("expected_pages", -1)) for _key, entry in entries}
    if len(expected_pages) != 1:
        return ["INCONSISTENT_EXPECTED_PAGE_COUNT"]
    page_count = max(1, next(iter(expected_pages)))
    pages = {int(entry.get("page", -1)) for _key, entry in entries}
    if pages != set(range(1, page_count + 1)):
        issues.append("MISSING_OR_EXTRA_PAGE")
    if len(entries) != len({key for key, _entry in entries}):
        issues.append("DUPLICATE_REQUEST_KEY")
    return issues


def _validate_raw_entry(run_dir: Path, key: str, entry: dict) -> list[str]:
    issues: list[str] = []
    if entry.get("request_key") != key:
        issues.append("PROGRESS_REQUEST_KEY_MISMATCH")
    raw_path = run_dir / str(entry.get("raw_path", ""))
    meta_path = raw_path.with_suffix(".meta.json")
    if not raw_path.is_file():
        return issues + ["RAW_FILE_MISSING"]
    if sha256_file(raw_path) != entry.get("sha256"):
        issues.append("RAW_SHA256_MISMATCH")
    if not meta_path.is_file():
        issues.append("SIDECAR_MISSING")
    else:
        sidecar = json.loads(meta_path.read_text(encoding="utf-8"))
        if sidecar.get("request_key") != key:
            issues.append("SIDECAR_REQUEST_KEY_MISMATCH")
        if sidecar.get("sha256") != entry.get("sha256"):
            issues.append("SIDECAR_SHA256_MISMATCH")
    return issues


def _parse_date(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Ngay must be DD/MM/YYYY text")
    return datetime.strptime(value, "%d/%m/%Y").date().isoformat()


def _number(value: object, field: str, *, multiplier: float = 1.0) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{field} must be finite numeric or null")
    result = float(value) * multiplier
    if field in {"KhoiLuongKhopLenh", "KLThoaThuan"}:
        if not result.is_integer():
            raise ValueError(f"{field} must be integer shares")
        return int(result)
    return result


def normalize_price_history_row(
    row: dict,
    *,
    plan_row: dict[str, str],
    source_run_id: str,
    source_contract_version: str,
    entry: dict,
    row_index: int,
) -> dict:
    missing = [field for field in SOURCE_FIELDS if field not in row]
    if missing:
        raise ValueError("missing source fields: " + ",".join(missing))
    ticker = plan_row["ticker"].upper()
    if str(row["Symbol"]).upper() != ticker:
        raise ValueError("source symbol does not match frozen plan")
    trade_date = _parse_date(row["Ngay"])
    raw_sha = entry["sha256"]
    candidate_id = hashlib.sha256(
        f"{plan_row['security_id']}|{trade_date}|{raw_sha}|{row_index}".encode("utf-8")
    ).hexdigest()
    result = {
        "candidate_id": candidate_id,
        "security_id": plan_row["security_id"],
        "ticker": ticker,
        "exchange": entry["exchange"],
        "trade_date": trade_date,
        "provider_open_vnd": _number(row["GiaMoCua"], "GiaMoCua", multiplier=1000),
        "provider_high_vnd": _number(row["GiaCaoNhat"], "GiaCaoNhat", multiplier=1000),
        "provider_low_vnd": _number(row["GiaThapNhat"], "GiaThapNhat", multiplier=1000),
        "provider_close_vnd": _number(row["GiaDongCua"], "GiaDongCua", multiplier=1000),
        "provider_adjusted_vnd": _number(row["GiaDieuChinh"], "GiaDieuChinh", multiplier=1000),
        "matched_volume_shares": _number(row["KhoiLuongKhopLenh"], "KhoiLuongKhopLenh"),
        "matched_value_vnd": _number(row["GiaTriKhopLenh"], "GiaTriKhopLenh", multiplier=1_000_000_000),
        "negotiated_volume_shares": _number(row["KLThoaThuan"], "KLThoaThuan"),
        "negotiated_value_vnd": _number(row["GtThoaThuan"], "GtThoaThuan", multiplier=1_000_000_000),
        "provider_change_text": row["ThayDoi"],
        "price_basis_status": PRICE_BASIS_STATUS,
        "canonical_promotion_status": PROMOTION_STATUS,
        "availability_status": "SOURCE_PUBLICATION_TIME_UNRESOLVED",
        "source": "cafef",
        "source_endpoint": "PriceHistory.ashx",
        "source_run_id": source_run_id,
        "source_contract_version": source_contract_version,
        "request_key": entry["request_key"],
        "raw_relative_path": entry["raw_path"],
        "raw_sha256": raw_sha,
        "fetched_at": entry["fetched_at"],
        "data_version": NORMALIZED_CONTRACT_VERSION,
    }
    close = result["provider_close_vnd"]
    adjusted = result["provider_adjusted_vnd"]
    result["provider_adjustment_ratio"] = (
        adjusted / close if close not in (None, 0) and adjusted is not None else None
    )
    return result


def _candidate_quality(candidate: dict) -> list[str]:
    issues: list[str] = []
    prices = [candidate[name] for name in (
        "provider_open_vnd", "provider_high_vnd", "provider_low_vnd", "provider_close_vnd"
    )]
    present = [value for value in prices if value is not None]
    if present and any(value <= 0 for value in present):
        issues.append("NONPOSITIVE_PRICE")
    if all(value is not None for value in prices):
        open_value, high, low, close = prices
        if high < max(open_value, low, close) or low > min(open_value, high, close):
            issues.append("INVALID_OHLC")
    if any(value is None for value in prices):
        issues.append("NULL_OHLC")
    for field in ("matched_volume_shares", "matched_value_vnd", "negotiated_volume_shares", "negotiated_value_vnd"):
        value = candidate[field]
        if value is not None and value < 0:
            issues.append("NEGATIVE_MARKET_VALUE")
    return issues


def _load_run(run_dir: Path) -> tuple[dict, dict[str, dict], set[str]]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    failures = {
        str(item.get("ticker", "")).upper()
        for item in _read_jsonl(run_dir / "failures.jsonl")
        if item.get("ticker")
    }
    return manifest, progress.get("completed", {}), failures


def audit_and_normalize(
    *,
    root: Path,
    plan_path: Path,
    new_run_dir: Path,
    reused_run_dir: Path,
    registry_path: Path,
) -> tuple[list[dict], list[dict], dict]:
    plan_rows = _read_csv(plan_path)
    new_manifest, new_completed, new_failures = _load_run(new_run_dir)
    reused_manifest, reused_completed, reused_failures = _load_run(reused_run_dir)
    registry = {row["ticker"]: row for row in _read_csv(registry_path)}
    run_data = {
        new_run_dir.name: (new_run_dir, new_manifest, new_completed, new_failures),
        reused_run_dir.name: (reused_run_dir, reused_manifest, reused_completed, reused_failures),
    }
    candidates: list[dict] = []
    raw_quality: dict[str, dict] = {}

    for plan_row in plan_rows:
        ticker = plan_row["ticker"].upper()
        reused = plan_row["crawl_required"] == "NO"
        source_run_id = plan_row["existing_history_source_run"] if reused else new_run_dir.name
        if source_run_id not in run_data:
            raise ValueError(f"unavailable source run for {ticker}: {source_run_id}")
        run_dir, manifest, completed, failures = run_data[source_run_id]
        ticker_entries = [(key, entry) for key, entry in completed.items() if entry.get("ticker") == ticker]
        issues: list[str] = []
        if ticker in failures:
            issues.append("BLOCKING_FAILURE_PRESENT")
        if reused:
            registry_row = registry.get(ticker)
            if not registry_row or registry_row.get("audit_status") != "LONG_HISTORY_COMPLETE":
                issues.append("REUSE_REGISTRY_NOT_COMPLETE")
            elif registry_row.get("raw_checksum_validation_status") != "PASS":
                issues.append("REUSE_REGISTRY_CHECKSUM_NOT_PASS")
        selected_entries: dict[str, dict] = {}
        for expected in _expected_ranges(plan_row):
            matches = [(key, entry) for key, entry in ticker_entries if _entry_covers(entry, expected)]
            if not matches:
                issues.append(
                    f"MISSING_RANGE:{expected['exchange']}:{expected['range_start']}:{expected['range_end']}"
                )
                continue
            issues.extend(_validate_range(matches))
            selected_entries.update(matches)
        for key, entry in selected_entries.items():
            issues.extend(_validate_raw_entry(run_dir, key, entry))

        invalid_rows = 0
        out_of_window = 0
        ticker_candidates: list[dict] = []
        target_start = date.fromisoformat(plan_row["base_5y_target_start"])
        target_end = date.fromisoformat(plan_row["base_5y_target_end"])
        for key, entry in sorted(selected_entries.items()):
            raw_path = run_dir / entry["raw_path"]
            if not raw_path.is_file() or sha256_file(raw_path) != entry.get("sha256"):
                continue
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
            rows = payload.get("Data", {}).get("Data", []) if isinstance(payload, dict) else []
            if not isinstance(rows, list):
                issues.append("INVALID_RAW_ENVELOPE")
                continue
            for row_index, row in enumerate(rows):
                try:
                    candidate = normalize_price_history_row(
                        row,
                        plan_row=plan_row,
                        source_run_id=source_run_id,
                        source_contract_version=manifest["contract_version"],
                        entry=entry,
                        row_index=row_index,
                    )
                except (ValueError, TypeError, KeyError):
                    invalid_rows += 1
                    continue
                trade_date = date.fromisoformat(candidate["trade_date"])
                if trade_date < target_start or trade_date > target_end:
                    out_of_window += 1
                    continue
                candidate["quality_flags"] = _candidate_quality(candidate)
                ticker_candidates.append(candidate)

        by_date: dict[str, list[dict]] = defaultdict(list)
        for candidate in ticker_candidates:
            by_date[candidate["trade_date"]].append(candidate)
        duplicate_dates = sum(len(rows) - 1 for rows in by_date.values() if len(rows) > 1)
        conflicting_duplicates = 0
        unique_candidates: list[dict] = []
        comparison_fields = (
            "provider_open_vnd", "provider_high_vnd", "provider_low_vnd", "provider_close_vnd",
            "provider_adjusted_vnd", "matched_volume_shares", "matched_value_vnd",
            "negotiated_volume_shares", "negotiated_value_vnd",
        )
        for trade_date, rows in sorted(by_date.items()):
            signatures = {tuple(row[field] for field in comparison_fields) for row in rows}
            if len(signatures) > 1:
                conflicting_duplicates += 1
                issues.append(f"CONFLICTING_DUPLICATE_DATE:{trade_date}")
            unique_candidates.append(rows[0])
        candidates.extend(unique_candidates)
        raw_quality[ticker] = {
            "plan_row": plan_row,
            "source_run_id": source_run_id,
            "reuse_status": "REUSED_LONG_HISTORY" if reused else "CRAWLED_BASE_5Y",
            "raw_audit_status": "PASS" if not issues else "FAIL",
            "issues": sorted(set(issues)),
            "request_count": len(selected_entries),
            "raw_page_count": len(selected_entries),
            "invalid_source_row_count": invalid_rows,
            "out_of_window_row_count": out_of_window,
            "duplicate_date_count": duplicate_dates,
            "conflicting_duplicate_count": conflicting_duplicates,
            "candidates": unique_candidates,
        }

    exchange_dates: dict[str, set[str]] = defaultdict(set)
    for candidate in candidates:
        exchange_dates[candidate["exchange"]].add(candidate["trade_date"])

    ticker_quality: list[dict] = []
    for ticker, quality in sorted(raw_quality.items(), key=lambda item: int(item[1]["plan_row"]["execution_order"])):
        plan_row = quality["plan_row"]
        rows = quality["candidates"]
        dates = sorted(row["trade_date"] for row in rows)
        row_dates = set(dates)
        target_start = date.fromisoformat(plan_row["base_5y_target_start"])
        target_end = date.fromisoformat(plan_row["base_5y_target_end"])
        expected_union: set[str] = set()
        empty_identity_intervals: list[str] = []
        for interval in json.loads(plan_row["identity_intervals"]):
            interval_start = max(target_start, date.fromisoformat(interval["effective_from"]))
            interval_end = min(
                target_end,
                date.fromisoformat(interval["effective_to"]) if interval.get("effective_to") else target_end,
            )
            if interval_start > interval_end:
                continue
            expected_union.update(
                value for value in exchange_dates[interval["exchange"]]
                if interval_start.isoformat() <= value <= interval_end.isoformat()
            )
            interval_rows = [
                row for row in rows
                if row["exchange"] == interval["exchange"]
                and interval_start.isoformat() <= row["trade_date"] <= interval_end.isoformat()
            ]
            if not interval_rows:
                empty_identity_intervals.append(
                    f"{interval['exchange']}:{interval_start.isoformat()}:{interval_end.isoformat()}"
                )
        missing_union = expected_union - row_dates
        invalid_ohlc = sum("INVALID_OHLC" in row["quality_flags"] for row in rows)
        nonpositive = sum("NONPOSITIVE_PRICE" in row["quality_flags"] for row in rows)
        null_ohlc = sum("NULL_OHLC" in row["quality_flags"] for row in rows)
        zero_volume = sum(row["matched_volume_shares"] == 0 for row in rows)
        quarantine_count = sum(bool(set(row["quality_flags"]) & {
            "INVALID_OHLC", "NONPOSITIVE_PRICE", "NEGATIVE_MARKET_VALUE"
        }) for row in rows)
        span_years = (
            (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days / 365.2425
            if len(dates) >= 2 else 0.0
        )
        integrity_blockers = list(quality["issues"])
        warnings: list[str] = []
        if invalid_ohlc:
            warnings.append("INVALID_OHLC_ROWS_QUARANTINE_REQUIRED")
        if nonpositive:
            warnings.append("NONPOSITIVE_PRICE_ROWS_QUARANTINE_REQUIRED")
        if empty_identity_intervals:
            warnings.extend(f"IDENTITY_INTERVAL_NO_OBSERVATIONS:{value}" for value in empty_identity_intervals)
        if integrity_blockers:
            quality_status = "FAIL_RAW_INTEGRITY"
        elif warnings:
            quality_status = "WARN_QUARANTINE_OR_COVERAGE_REVIEW_REQUIRED"
        else:
            quality_status = "PASS_RAW_CANDIDATE"
        ticker_quality.append({
            "execution_order": plan_row["execution_order"],
            "security_id": plan_row["security_id"],
            "ticker": ticker,
            "exchange": plan_row["exchange"],
            "source_run_id": quality["source_run_id"],
            "reuse_status": quality["reuse_status"],
            "raw_audit_status": quality["raw_audit_status"],
            "request_count": quality["request_count"],
            "raw_page_count": quality["raw_page_count"],
            "normalized_row_count": len(rows),
            "valid_candidate_row_count": len(rows) - quarantine_count,
            "quarantined_row_count": quarantine_count,
            "first_observed_date": dates[0] if dates else "",
            "last_observed_date": dates[-1] if dates else "",
            "observed_span_years": round(span_years, 4),
            "duplicate_date_count": quality["duplicate_date_count"],
            "conflicting_duplicate_count": quality["conflicting_duplicate_count"],
            "invalid_source_row_count": quality["invalid_source_row_count"],
            "invalid_ohlc_count": invalid_ohlc,
            "nonpositive_price_count": nonpositive,
            "null_ohlc_count": null_ohlc,
            "zero_matched_volume_count": zero_volume,
            "exchange_union_missing_count": len(missing_union),
            "exchange_union_coverage_rate": round(len(row_dates & expected_union) / len(expected_union), 6) if expected_union else 0.0,
            "minimum_3y_history_evidence": "PASS" if span_years >= 3 else "REFERENCE_ONLY_EVIDENCE",
            "identity_interval_without_rows_count": len(empty_identity_intervals),
            "canonical_price_ready": "NO_PRICE_BASIS_MANUAL_REVIEW_REQUIRED",
            "quality_status": quality_status,
            "blocking_reasons": ";".join(sorted(set(integrity_blockers + warnings))),
        })

    summary = {
        "pilot_security_count": len(plan_rows),
        "normalized_candidate_count": len(candidates),
        "raw_audit_pass_count": sum(row["raw_audit_status"] == "PASS" for row in ticker_quality),
        "raw_quality_pass_count": sum(row["quality_status"] == "PASS_RAW_CANDIDATE" for row in ticker_quality),
        "raw_quality_warning_count": sum(row["quality_status"].startswith("WARN_") for row in ticker_quality),
        "raw_quality_fail_count": sum(row["quality_status"] == "FAIL_RAW_INTEGRITY" for row in ticker_quality),
        "minimum_3y_evidence_count": sum(row["minimum_3y_history_evidence"] == "PASS" for row in ticker_quality),
        "invalid_ohlc_count": sum(int(row["invalid_ohlc_count"]) for row in ticker_quality),
        "nonpositive_price_count": sum(int(row["nonpositive_price_count"]) for row in ticker_quality),
        "conflicting_duplicate_count": sum(int(row["conflicting_duplicate_count"]) for row in ticker_quality),
        "quarantined_row_count": sum(int(row["quarantined_row_count"]) for row in ticker_quality),
        "identity_interval_without_rows_count": sum(int(row["identity_interval_without_rows_count"]) for row in ticker_quality),
        "new_run_status": new_manifest.get("status"),
        "new_run_request_count": len(new_completed),
        "reused_run_status": reused_manifest.get("status"),
    }
    return candidates, ticker_quality, summary


def build_discontinuity_candidates(candidates: list[dict]) -> list[dict]:
    by_security: dict[str, list[dict]] = defaultdict(list)
    for row in candidates:
        by_security[row["security_id"]].append(row)
    findings: list[dict] = []
    for rows in by_security.values():
        ordered = sorted(rows, key=lambda row: row["trade_date"])
        for previous, current in zip(ordered, ordered[1:]):
            previous_ratio = previous.get("provider_adjustment_ratio")
            ratio = current.get("provider_adjustment_ratio")
            ratio_change = (
                ratio / previous_ratio - 1
                if ratio not in (None, 0) and previous_ratio not in (None, 0) else None
            )
            previous_close = previous.get("provider_close_vnd")
            close = current.get("provider_close_vnd")
            raw_return = close / previous_close - 1 if close not in (None, 0) and previous_close not in (None, 0) else None
            flags: list[str] = []
            if ratio_change is not None and abs(ratio_change) >= 0.005:
                flags.append("PROVIDER_ADJUSTMENT_RATIO_CHANGE")
            if raw_return is not None and abs(raw_return) >= 0.20:
                flags.append("RAW_CLOSE_MOVE_GE_20_PERCENT")
            if flags:
                findings.append({
                    "security_id": current["security_id"],
                    "ticker": current["ticker"],
                    "trade_date": current["trade_date"],
                    "previous_trade_date": previous["trade_date"],
                    "provider_adjustment_ratio": ratio,
                    "previous_adjustment_ratio": previous_ratio,
                    "ratio_change": ratio_change,
                    "raw_close_return": raw_return,
                    "diagnostic_flags": ";".join(flags),
                    "evidence_status": "DIAGNOSTIC_ONLY_NOT_CORPORATE_ACTION_PROOF",
                })
    return findings


def build_field_coverage(candidates: list[dict] | None = None) -> tuple[list[dict], list[dict]]:
    candidates = candidates or []
    tables = (
        "securities", "shares_history", "prices_daily", "benchmark_daily",
        "trading_calendar", "corporate_actions", "financial_reports", "financial_facts",
    )
    evidence: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    candidate_field_map = {
        "security_id": "security_id", "ticker": "ticker", "exchange": "exchange",
        "trade_date": "trade_date", "raw_open": "provider_open_vnd",
        "raw_high": "provider_high_vnd", "raw_low": "provider_low_vnd",
        "raw_close": "provider_close_vnd", "adj_close": "provider_adjusted_vnd",
        "volume": "matched_volume_shares", "traded_value": "matched_value_vnd",
        "source": "source", "fetched_at": "fetched_at", "data_version": "data_version",
    }

    def set_fields(table: str, fields: tuple[str, ...], state: str, semantic: str, source: str, reason: str = ""):
        for field in fields:
            evidence[(table, field)] = (state, semantic, source, reason)

    set_fields("securities", ("security_id", "ticker", "exchange", "valid_from", "valid_to"),
               "AVAILABLE_FROM_FROZEN_PLAN", "APPROVED_FOR_PILOT_IDENTITY", "V3 plan identity intervals")
    set_fields("securities", ("currency", "price_unit", "source", "fetched_at", "data_version"),
               "AVAILABLE_BY_VERSIONED_POLICY", "POLICY_VALUE", "V3 plan/run metadata")
    set_fields("securities", ("listing_date", "identity_status"),
               "AVAILABLE_WITH_LIMITATION", "MANUAL_REVIEW_REQUIRED", "identity interval evidence",
               "identity interval start is not always authoritative listing proof")
    set_fields("securities", ("company_name", "available_at", "sector", "industry", "delisting_date"),
               "NOT_AVAILABLE", "MISSING_SOURCE_EVIDENCE", "PriceHistory does not provide this field")

    price_direct = ("security_id", "ticker", "exchange", "trade_date", "source", "fetched_at", "data_version")
    set_fields("prices_daily", price_direct, "AVAILABLE_FROM_CANDIDATE", "APPROVED_PROVENANCE", "normalized PriceHistory candidate")
    set_fields("prices_daily", ("raw_open", "raw_high", "raw_low", "raw_close"),
               "AVAILABLE_BUT_BLOCKED", "PRICE_BASIS_UNRESOLVED", "GiaMoCua/GiaCaoNhat/GiaThapNhat/GiaDongCua ×1000",
               "manual approval required before canonical raw OHLC mapping")
    set_fields("prices_daily", ("adj_close",), "AVAILABLE_BUT_BLOCKED", "ADJUSTMENT_METHOD_UNDOCUMENTED",
               "GiaDieuChinh ×1000", "provider-adjusted field is diagnostic only")
    set_fields("prices_daily", ("volume", "traded_value"), "AVAILABLE_BUT_BLOCKED", "COMPONENT_POLICY_UNRESOLVED",
               "matched and negotiated components are retained separately",
               "canonical aggregation policy is not approved")
    set_fields("prices_daily", ("reference_price", "ceiling_price", "floor_price"),
               "NOT_AVAILABLE", "NULLABLE_ON_CANONICAL", "PriceHistory omits historical limit fields")
    set_fields("prices_daily", ("adjustment_basis",), "AVAILABLE_BY_VERSIONED_POLICY", "UNKNOWN_ONLY",
               "canonical enum supports unknown", "does not resolve price semantics")
    set_fields("prices_daily", ("trading_status",), "AVAILABLE_BY_VERSIONED_POLICY", "UNKNOWN_ONLY",
               "canonical enum supports unknown", "PriceHistory has no historical status")
    set_fields("prices_daily", ("available_at",), "AVAILABLE_WITH_LIMITATION", "CONSERVATIVE_FETCH_TIME_ONLY",
               "fetched_at can be used as no-earlier-than availability",
               "historical source publication timestamp is unresolved")

    set_fields("trading_calendar", ("exchange", "trade_date", "is_open", "source", "fetched_at", "data_version"),
               "DERIVABLE_DIAGNOSTIC_ONLY", "OBSERVED_SESSION_ONLY", "union of CafeF observed rows",
               "row absence does not prove exchange closure")
    set_fields("trading_calendar", ("is_month_end", "close_at", "decision_at", "open_at", "available_at"),
               "NOT_AVAILABLE", "OFFICIAL_CALENDAR_REQUIRED", "PriceHistory has no calendar timestamps")

    set_fields("benchmark_daily", tuple(schema("benchmark_daily")["fields"]),
               "NOT_AVAILABLE", "HISTORICAL_BENCHMARK_NOT_ACQUIRED", "page-level current VNINDEX snapshot is not a daily history")
    set_fields("shares_history", tuple(schema("shares_history")["fields"]),
               "NOT_AVAILABLE", "PRICE_HISTORY_DOMAIN_MISMATCH", "PriceHistory has no share-count history")
    set_fields("corporate_actions", tuple(schema("corporate_actions")["fields"]),
               "NOT_AVAILABLE", "EVENT_DOCUMENTS_NOT_ACQUIRED", "price discontinuity is not event proof")
    set_fields("financial_reports", tuple(schema("financial_reports")["fields"]),
               "NOT_AVAILABLE", "FINANCIAL_DOCUMENTS_NOT_ACQUIRED", "PriceHistory has no PIT report metadata")
    set_fields("financial_facts", tuple(schema("financial_facts")["fields"]),
               "NOT_AVAILABLE", "FINANCIAL_DOCUMENTS_NOT_ACQUIRED", "PriceHistory has no financial facts")

    field_rows: list[dict] = []
    table_rows: list[dict] = []
    for table in tables:
        contract = schema(table)
        required = [name for name, field in contract["fields"].items() if not field.get("nullable", False)]
        available_required: list[str] = []
        blocked_required: list[str] = []
        unavailable_nullable: list[str] = []
        source_evidence_count = 0
        canonical_fillable_count = 0
        blockers: list[str] = []
        for field_name, field in contract["fields"].items():
            state, semantic, source, reason = evidence.get(
                (table, field_name),
                ("NOT_AVAILABLE", "NO_MAPPING_EVIDENCE", "No CafeF PriceHistory mapping", "field not observed"),
            )
            approved = state in {"AVAILABLE_FROM_FROZEN_PLAN", "AVAILABLE_FROM_CANDIDATE", "AVAILABLE_BY_VERSIONED_POLICY"}
            if state != "NOT_AVAILABLE":
                source_evidence_count += 1
            if approved:
                canonical_fillable_count += 1
            fill_status = "YES" if approved else "NO"
            candidate_source_field = candidate_field_map.get(field_name, "") if table == "prices_daily" else ""
            observed_count = len(candidates) if candidate_source_field else ""
            non_null_count = (
                sum(row.get(candidate_source_field) is not None for row in candidates)
                if candidate_source_field else ""
            )
            non_null_rate = (
                round(non_null_count / len(candidates), 6)
                if candidate_source_field and candidates else ""
            )
            if not field.get("nullable", False):
                if approved:
                    available_required.append(field_name)
                else:
                    blocked_required.append(field_name)
                    if reason:
                        blockers.append(f"{field_name}:{reason}")
            elif state == "NOT_AVAILABLE":
                unavailable_nullable.append(field_name)
            field_rows.append({
                "table": table,
                "field": field_name,
                "nullable": "YES" if field.get("nullable", False) else "NO",
                "source_evidence": source,
                "coverage_state": state,
                "semantic_status": semantic,
                "candidate_source_field": candidate_source_field,
                "observed_row_count": observed_count,
                "observed_non_null_count": non_null_count,
                "observed_non_null_rate": non_null_rate,
                "canonical_fill_status": fill_status,
                "blocking_reason": reason,
            })
        if table == "prices_daily":
            table_status = "CANDIDATE_ONLY_MANUAL_REVIEW_REQUIRED"
            blockers.extend([
                "OHLC price basis unresolved",
                "provider adjustment method undocumented",
                "volume/value component aggregation policy unresolved",
            ])
        elif blocked_required:
            table_status = "NOT_FILLABLE_FROM_CURRENT_PRICEHISTORY_RAW"
        else:
            table_status = "STRUCTURALLY_FILLABLE"
        table_rows.append({
            "table": table,
            "total_field_count": len(contract["fields"]),
            "fields_with_source_evidence": source_evidence_count,
            "canonical_fillable_field_count": canonical_fillable_count,
            "unavailable_or_blocked_field_count": len(contract["fields"]) - canonical_fillable_count,
            "required_field_count": len(required),
            "required_fields_available": ";".join(available_required),
            "required_fields_blocked_or_missing": ";".join(blocked_required),
            "nullable_fields_unavailable": ";".join(unavailable_nullable),
            "table_status": table_status,
            "primary_blockers": ";".join(dict.fromkeys(blockers)),
        })
    return field_rows, table_rows


def write_offline_artifact(
    *,
    output_dir: Path,
    candidates: list[dict],
    ticker_quality: list[dict],
    summary: dict,
    config: dict,
) -> dict:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite immutable output: {output_dir}")
    output_dir.mkdir(parents=True)
    discontinuities = build_discontinuity_candidates(candidates)
    field_coverage, table_readiness = build_field_coverage(candidates)
    outputs = {
        "normalized_market_candidates.jsonl": b"".join(encoded(row) + b"\n" for row in candidates),
        "ticker_quality.csv": _csv_bytes(ticker_quality, TICKER_QUALITY_COLUMNS),
        "adjustment_discontinuity_candidates.csv": _csv_bytes(discontinuities, DISCONTINUITY_COLUMNS),
        "field_coverage.csv": _csv_bytes(field_coverage, FIELD_COVERAGE_COLUMNS),
        "table_readiness.csv": _csv_bytes(table_readiness, TABLE_READINESS_COLUMNS),
    }
    for name, data in outputs.items():
        atomic_write(output_dir / name, data)
    manifest = {
        "run_id": output_dir.name,
        "audit_contract_version": AUDIT_CONTRACT_VERSION,
        "normalized_contract_version": NORMALIZED_CONTRACT_VERSION,
        "status": "PARTIAL_MANUAL_REVIEW_REQUIRED",
        "stages": {
            "C1_POSTCRAWL_RAW_AUDIT": "PASS" if summary["raw_audit_pass_count"] == summary["pilot_security_count"] else "FAIL",
            "C2_NORMALIZED_CANDIDATE_AND_EVENT_DIAGNOSTICS": "PARTIAL_EVENT_DOCUMENTS_NOT_ACQUIRED",
            "C3_CAFEF_PRIMARY_SELF_SUFFICIENCY": "COMPLETED_MANUAL_REVIEW_REQUIRED",
        },
        "kbs_comparison": "WAIVED_BY_USER_NOT_EXECUTED",
        "network_requests": 0,
        "canonical_mutations": 0,
        "feature_rebuild": False,
        "cafef_primary_market_candidate_viable": summary["raw_audit_pass_count"] == summary["pilot_security_count"],
        "cafef_canonical_ready": False,
        "full_m1_table_coverage": False,
        "manual_review_blockers": [
            "Approve or reject CafeF OHLC as unadjusted/raw price basis.",
            "Define canonical volume and traded-value component policy.",
            "Acquire authoritative corporate-action evidence before deriving research prices.",
            "Supply independent identity, calendar, benchmark, shares and financial domains.",
        ],
        "summary": summary,
        "discontinuity_candidate_count": len(discontinuities),
        "table_readiness": {row["table"]: row["table_status"] for row in table_readiness},
        "inputs": config["inputs"],
        "config_version": config["config_version"],
        "output_hashes": {name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()},
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def run_from_config(root: Path, config: dict, output_dir: Path) -> dict:
    inputs = config["inputs"]
    candidates, ticker_quality, summary = audit_and_normalize(
        root=root,
        plan_path=root / inputs["active_plan_csv"],
        new_run_dir=root / inputs["base5y_run_dir"],
        reused_run_dir=root / inputs["long_history_run_dir"],
        registry_path=root / inputs["long_history_registry_csv"],
    )
    return write_offline_artifact(
        output_dir=output_dir,
        candidates=candidates,
        ticker_quality=ticker_quality,
        summary=summary,
        config=config,
    )
