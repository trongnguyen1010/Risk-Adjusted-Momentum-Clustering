"""Offline, immutable missing-session audit for the M1 canonical market run.

This module intentionally does not acquire, recover, modify, or impute market
data.  Its exchange sessions are only as authoritative as the supplied
canonical calendar.  The current M1 calendar is an observed-session union,
therefore its missing rows remain ``CALENDAR_UNCERTAIN``.
"""
from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from ..artifact_ids import new_artifact_id
from ..features.market import latest_completed_snapshot_rows
from ..io import atomic_write, digest, now, read_json, read_rows, write_json


CALENDAR_PROVISIONAL_OBSERVED = "PROVISIONAL_OBSERVED"
IDENTITY_PROVISIONAL_OBSERVED = "PROVISIONAL_OBSERVED_INTERVAL_ONLY"
_WINDOWS = (21, 63, 126, 252, 300)
_MOM_WINDOWS = (21, 63, 126, 252)


def _inside(path, parent, label):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    if not path.is_relative_to(parent):
        raise ValueError(f"{label} escapes {parent}")
    return path


def _verify_artifacts(directory, manifest):
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("canonical manifest has no artifact checksums")
    for relative, expected in artifacts.items():
        path = directory / relative
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError(f"canonical artifact checksum mismatch: {relative}")


def _calendar_status(calendar_rows):
    sources = {row.get("source") for row in calendar_rows if row.get("is_open")}
    # Local evidence has no approved official-exchange-calendar provenance.  Do
    # not upgrade a source label to an official calendar merely by its name.
    if sources == {"kbs_observed_session_union"}:
        return CALENDAR_PROVISIONAL_OBSERVED
    return "CALENDAR_UNCERTAIN"


def _identity_status(security):
    if security.get("identity_status") == "verified":
        return "VERIFIED"
    if security.get("identity_status") == "provisional":
        return IDENTITY_PROVISIONAL_OBSERVED
    return "UNRESOLVED"


def _expected_dates(security, exchange_sessions):
    """Use only supplied effective/listing/delisting evidence.

    ``valid_from`` and ``valid_to`` are retained as an effective identity
    interval, not reinterpreted as proof of listing dates.  In particular, a
    null listing date never becomes the first observed price date.
    """
    start = max(filter(None, (security.get("valid_from"), security.get("listing_date"))))
    end_candidates = [value for value in (security.get("valid_to"), security.get("delisting_date")) if value]
    end = min(end_candidates) if end_candidates else None
    return [day for day in exchange_sessions if day >= start and (end is None or day < end)]


def _missing_classification(calendar_status, identity_status):
    if calendar_status == CALENDAR_PROVISIONAL_OBSERVED:
        return "CALENDAR_UNCERTAIN"
    if identity_status != "VERIFIED":
        return "IDENTITY_GAP_CANDIDATE"
    return "UNRESOLVED_MISSING"


def _gap_metrics(missing_dates):
    if not missing_dates:
        return {"max_consecutive_missing": 0, "first_missing_date": None,
                "last_missing_date": None, "missing_range_count": 0}
    ranges, longest, current = 1, 1, 1
    previous = missing_dates[0]
    for value in missing_dates[1:]:
        # The caller supplies dates in expected-session order and marks only
        # missing dates, so a calendar-day difference cannot identify a gap.
        # Consecutive runs are calculated before this helper, from flags.
        previous = value
    return {"max_consecutive_missing": longest, "first_missing_date": missing_dates[0],
            "last_missing_date": missing_dates[-1], "missing_range_count": ranges}


def _missing_runs(expected_dates, observed_dates):
    missing, ranges, current, longest = [], 0, 0, 0
    for day in expected_dates:
        if day not in observed_dates:
            missing.append(day)
            if current == 0:
                ranges += 1
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return missing, {"max_consecutive_missing": longest,
                     "first_missing_date": missing[0] if missing else None,
                     "last_missing_date": missing[-1] if missing else None,
                     "missing_range_count": ranges}


def _priority(snapshot, missing_last_252, calendar_status, identity_status):
    if not snapshot.get("market_feature_ready"):
        if (calendar_status != "OFFICIAL_EXCHANGE" or identity_status != "VERIFIED"):
            return "P4", "structural_identity_or_calendar_uncertainty"
        if 1 <= missing_last_252 <= 5:
            return "P0", "one_to_five_missing_in_latest_252"
        if 6 <= missing_last_252 <= 20:
            return "P1", "six_to_twenty_missing_in_latest_252"
        if 21 <= missing_last_252 <= 63:
            return "P2", "twenty_one_to_sixty_three_missing_in_latest_252"
        if missing_last_252 > 63:
            return "P3", "more_than_sixty_three_missing_in_latest_252"
        return "P4", "non_ready_without_a_confirmed_missing_session_cause"
    return None, None


def build_a1_audit(securities, prices, calendar, features, *, collection_end):
    """Return deterministic A1 rows/metrics without changing any input object."""
    calendar_status = _calendar_status(calendar)
    sessions = defaultdict(list)
    for row in calendar:
        if row.get("is_open"):
            sessions[row["exchange"]].append(row["trade_date"])
    for values in sessions.values():
        values.sort()
    observed = defaultdict(set)
    price_sources = defaultdict(set)
    for row in prices:
        key = (row["security_id"], row["trade_date"])
        if row["trade_date"] > collection_end:
            raise ValueError("price is later than canonical collection end")
        if row["trade_date"] in observed[row["security_id"]]:
            raise ValueError(f"duplicate canonical price key: {key}")
        observed[row["security_id"]].add(row["trade_date"])
        if row.get("source"):
            price_sources[row["security_id"]].add(row["source"])
    latest_date, latest = latest_completed_snapshot_rows(features, collection_end)
    by_security = {row["security_id"]: row for row in securities}
    if set(by_security) != set(latest):
        raise ValueError("latest feature snapshot does not cover the exact canonical universe")

    detail, per_symbol, recovery = [], [], []
    for security_id, security in sorted(by_security.items(), key=lambda item: (item[1]["ticker"], item[0])):
        expected = _expected_dates(security, sessions[security["exchange"]])
        if not expected:
            raise ValueError(f"no expected session evidence: {security_id}")
        unexpected = observed[security_id] - set(expected)
        if unexpected:
            raise ValueError(f"canonical observation outside effective identity interval: {security_id}")
        identity_status = _identity_status(security)
        snapshot = latest[security_id]
        missing, gap = _missing_runs(expected, observed[security_id])
        relevant = {window: set([day for day in expected if day <= latest_date][-window:]) for window in _WINDOWS}
        latest_missing = {window: sum(day in relevant[window] for day in missing) for window in _WINDOWS}
        classification = _missing_classification(calendar_status, identity_status)
        source = ";".join(sorted(price_sources[security_id])) or "UNKNOWN_CANONICAL_SOURCE"
        for day in missing:
            detail.append({
                "security_id": security_id, "ticker": security["ticker"], "exchange": security["exchange"],
                "trading_date": day, "expected_session": True, "observed_session": False,
                "missing_flag": True, "missing_classification": classification,
                **{f"latest_{window}_relevant": day in relevant[window] for window in _WINDOWS},
                "canonical_source": source, "identity_status": identity_status,
                "calendar_status": calendar_status,
            })
        priority, priority_reason = _priority(snapshot, latest_missing[252], calendar_status, identity_status)
        item = {
            "security_id": security_id, "ticker": security["ticker"], "exchange": security["exchange"],
            "listing_date": security.get("listing_date"), "delisting_date": security.get("delisting_date"),
            "identity_effective_from": security.get("valid_from"), "identity_effective_to": security.get("valid_to"),
            "identity_status": identity_status, "calendar_status": calendar_status,
            "canonical_source": source, "expected_sessions_total": len(expected),
            "observed_sessions_total": len(observed[security_id]), "missing_sessions_total": len(missing),
            "coverage_ratio": len(observed[security_id]) / len(expected),
            **{f"missing_last_{window}": latest_missing[window] for window in _WINDOWS}, **gap,
            **{f"mom{window}_complete": snapshot.get(f"mom_{window}") is not None for window in _MOM_WINDOWS},
            "market_feature_ready": bool(snapshot.get("market_feature_ready")),
            "latest_completed_snapshot": latest_date,
        }
        per_symbol.append(item)
        if priority:
            recovery.append({**item, "recovery_priority": priority, "priority_reason": priority_reason,
                             "missing_classification": classification})
    return detail, per_symbol, recovery, latest_date


def _csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


# Minimal Parquet 1.x writer for A1's non-null scalar audit rows.  The project
# environment deliberately has no pyarrow/fastparquet dependency; using this
# small writer avoids a network install while still producing a real PAR1 file.
_T_STOP, _T_TRUE, _T_FALSE, _T_I32, _T_I64, _T_BINARY, _T_LIST, _T_STRUCT = range(8)
_T_I32, _T_I64, _T_BINARY, _T_LIST, _T_STRUCT = 5, 6, 8, 9, 12


def _varint(value):
    value = int(value)
    output = bytearray()
    while value > 127:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)


def _zigzag(value):
    return _varint((int(value) << 1) ^ (int(value) >> 63))


def _struct(fields):
    output, previous = bytearray(), 0
    for field_id, field_type, payload in fields:
        delta = field_id - previous
        output.append((delta << 4 | field_type) if 0 < delta <= 15 else field_type)
        if not 0 < delta <= 15:
            output.extend(_varint(field_id))
        output.extend(payload)
        previous = field_id
    output.append(_T_STOP)
    return bytes(output)


def _i32(value):
    return _zigzag(value)


def _i64(value):
    return _zigzag(value)


def _binary(value):
    data = str(value).encode("utf-8")
    return _varint(len(data)) + data


def _list(element_type, values):
    values = list(values)
    header = bytes([(len(values) << 4) | element_type]) if len(values) <= 14 else bytes([0xF0 | element_type]) + _varint(len(values))
    return header + b"".join(values)


def _schema_element(name, *, type_id=None, utf8=False, children=None):
    fields = []
    if type_id is not None:
        fields.append((1, _T_I32, _i32(type_id)))
        fields.append((3, _T_I32, _i32(0)))  # REQUIRED
    fields.append((4, _T_BINARY, _binary(name)))
    if children is not None:
        fields.append((5, _T_I32, _i32(children)))
    if utf8:
        fields.append((6, _T_I32, _i32(0)))  # ConvertedType.UTF8
    return _struct(fields)


def _plain_boolean(values):
    output = bytearray((len(values) + 7) // 8)
    for index, value in enumerate(values):
        if value:
            output[index // 8] |= 1 << (index % 8)
    return bytes(output)


def _plain_binary(values):
    return b"".join(len(value.encode("utf-8")).to_bytes(4, "little", signed=True) + value.encode("utf-8") for value in values)


def write_a1_parquet(path, rows):
    """Write a valid uncompressed Parquet 1.x file without third-party code."""
    columns = [
        ("security_id", "text"), ("ticker", "text"), ("exchange", "text"), ("trading_date", "text"),
        ("expected_session", "bool"), ("observed_session", "bool"), ("missing_flag", "bool"),
        ("missing_classification", "text"), *( (f"latest_{window}_relevant", "bool") for window in _WINDOWS ),
        ("canonical_source", "text"), ("identity_status", "text"), ("calendar_status", "text"),
    ]
    chunks, metadata = [], []
    offset = 4
    for name, kind in columns:
        values = [row[name] for row in rows]
        raw = _plain_boolean(values) if kind == "bool" else _plain_binary(values)
        data_header = _struct([(1, _T_I32, _i32(len(values))), (2, _T_I32, _i32(0)),
                               (3, _T_I32, _i32(3)), (4, _T_I32, _i32(3))])
        page = _struct([(1, _T_I32, _i32(0)), (2, _T_I32, _i32(len(raw))),
                        (3, _T_I32, _i32(len(raw))), (5, _T_STRUCT, data_header)]) + raw
        chunks.append(page)
        type_id = 0 if kind == "bool" else 6  # BOOLEAN / BYTE_ARRAY
        column_meta = _struct([
            (1, _T_I32, _i32(type_id)), (2, _T_LIST, _list(_T_I32, [_i32(0)])),
            (3, _T_LIST, _list(_T_BINARY, [_binary(name)])), (4, _T_I32, _i32(0)),
            (5, _T_I64, _i64(len(values))), (6, _T_I64, _i64(len(page))),
            (7, _T_I64, _i64(len(page))), (9, _T_I64, _i64(offset)),
        ])
        metadata.append(_struct([(2, _T_I64, _i64(offset)), (3, _T_STRUCT, column_meta)]))
        offset += len(page)
    row_group = _struct([(1, _T_LIST, _list(_T_STRUCT, metadata)),
                         (2, _T_I64, _i64(sum(map(len, chunks)))), (3, _T_I64, _i64(len(rows)))])
    schema = [_schema_element("schema", children=len(columns))]
    schema.extend(_schema_element(name, type_id=0 if kind == "bool" else 6, utf8=kind == "text") for name, kind in columns)
    footer = _struct([(1, _T_I32, _i32(1)), (2, _T_LIST, _list(_T_STRUCT, schema)),
                      (3, _T_I64, _i64(len(rows))), (4, _T_LIST, _list(_T_STRUCT, [row_group])),
                      (6, _T_BINARY, _binary("delta-t1-a1-stdlib-parquet"))])
    atomic_write(path, b"PAR1" + b"".join(chunks) + footer + len(footer).to_bytes(4, "little") + b"PAR1")


def _report_markdown(report, recovery):
    summary, priority = report["summary"], report["priority_counts"]
    lines = [
        "# A1 — Missing Session Audit", "",
        f"Run: `{report['run_id']}`  ", f"Generated: `{report['generated_at']}`  ",
        f"Canonical baseline: `{report['canonical_run_id']}`  ",
        f"Feature readiness baseline: `{report['quality_report_id']}`", "",
        "## Kết luận", "",
        "A1 là audit offline/read-only. Không crawl, recovery, backfill, canonical mutation, "
        "forward-fill, backward-fill, interpolation hoặc zero-fill đã được thực hiện.", "",
        "## Câu trả lời bắt buộc", "",
        f"1. P0: {priority.get('P0', 0)}", f"2. P1: {priority.get('P1', 0)}",
        f"3. P2: {priority.get('P2', 0)}", f"4. P3: {priority.get('P3', 0)}",
        f"5. P4: {priority.get('P4', 0)}",
        f"6. Missing đúng 1 session: {summary['exactly_1_missing']}",
        f"7. Missing <=5 sessions: {summary['missing_le_5']}",
        f"8. Missing <=20 sessions: {summary['missing_le_20']}", "",
        "9. Phân bố exchange của missing observations/securities:", "",
        "| Exchange | Missing observations | Securities with missing |", "|---|---:|---:|",
    ]
    for exchange, values in report["exchange_distribution"].items():
        lines.append(f"| {exchange} | {values['missing_observations']} | {values['securities']} |")
    lines.extend(["", "10. Concentration theo tháng (top 12):", "",
                  "| Month | Missing observations |", "|---|---:|"])
    for month, count in list(report["month_concentration"].items())[:12]:
        lines.append(f"| {month} | {count} |")
    lines.extend([
        "", "11. Provider pattern: **NOT DETERMINABLE IN A1**. Local canonical rows chỉ có "
        "provenance của baseline, không có source query/reconciliation mới để xác nhận provider gap.",
        "", "12. Top 50 easy recovery/investigation candidates:", "",
        "| Priority | Ticker | Exchange | Missing latest 252 | Reason |", "|---|---|---|---:|---|",
    ])
    for row in recovery[:50]:
        lines.append(f"| {row['recovery_priority']} | {row['ticker']} | {row['exchange']} | "
                     f"{row['missing_last_252']} | {row['priority_reason']} |")
    lines.extend([
        "", "Các row trên là thứ tự điều tra, không phải xác nhận khả năng recovery. Với current "
        "evidence, tất cả identity/calendar unresolved phải ở P4 và không được blind recovery.",
        "", "13. Market-important non-ready securities: **NOT DETERMINABLE IN A1**. Không có "
        "deterministic, frozen market-priority/acquisition score trong baseline evidence.",
        "", "14. Structural hơn simple recovery: toàn bộ P4 (identity interval provisional và/hoặc "
        "calendar observed-union) — xem `recovery_priority.csv`.",
        "", f"15. Theoretical maximum readiness: {summary['theoretical_max_readiness']}/"
        f"{summary['securities']}, dưới giả định bảo thủ rằng A1 chỉ dùng real rows hiện hữu và "
        "không có evidence mới để promote/recover. Đây không phải forecast cho A2+.",
        "", "16. Not worth blind recovery: mọi P4; lý do là identity/calendar uncertainty nên missing "
        "canonical row không đủ để kết luận provider gap.",
        "", "## Reconciliation với baseline feature readiness", "",
        f"Latest completed snapshot là `{summary['latest_completed_snapshot']}`. Baseline quality "
        f"report ghi market-feature-ready = {summary['baseline_market_feature_ready']}; A1 đọc cùng "
        f"feature snapshot và cũng đếm {summary['a1_market_feature_ready']}. {'Khớp.' if summary['baseline_market_feature_ready'] == summary['a1_market_feature_ready'] else 'KHÔNG KHỚP — preserved for investigation.'}",
        "Momentum 252 giữ nguyên semantics của feature engine: cần đủ real observation structure; "
        "A1 không nén timeline hay biến missing thành observation.",
        "", "## Evidence / commands", "",
        "- Inputs và SHA-256: `manifest.json`.",
    ])
    lines.extend(f"- `{result}`" for result in report.get("test_results", []))
    return "\n".join(lines).encode("utf-8")


def build_stage_a1(canonical_path, quality_report_path, *, root, test_results=(), stage_status="PASS"):
    """Generate an immutable A1 artifact directory from approved local evidence."""
    root = Path(root).resolve()
    canonical_path = _inside(canonical_path, root / "data" / "canonical", "canonical path")
    manifest_path = canonical_path / "manifest.json"
    manifest = read_json(manifest_path)
    if (manifest.get("run_id") != canonical_path.name or manifest.get("canonical_promotion_status") != "PASS"
            or manifest.get("network_requests") != 0 or manifest.get("schema_version") != "1.5.0"):
        raise ValueError("A1 requires a completed offline canonical M1 promotion v1.5")
    _verify_artifacts(canonical_path, manifest)
    quality_report_path = _inside(quality_report_path, root / "data" / "derived" / "m1_scale_quality", "quality report path")
    quality = read_json(quality_report_path)
    if quality.get("canonical_run_id") != manifest["run_id"]:
        raise ValueError("quality report canonical run does not match A1 baseline")
    securities = read_rows(canonical_path / "clean" / "securities.jsonl")
    prices = read_rows(canonical_path / "clean" / "prices_daily.jsonl")
    calendar = read_rows(canonical_path / "clean" / "trading_calendar.jsonl")
    features = read_rows(canonical_path / "features" / "monthly.jsonl")
    detail, per_symbol, recovery, latest_date = build_a1_audit(
        securities, prices, calendar, features, collection_end=manifest["collection_end"])
    baseline_ready = quality["summary"]["market_feature_ready"]
    a1_ready = sum(row["market_feature_ready"] for row in per_symbol)
    priority_counts = Counter(row["recovery_priority"] for row in recovery)
    exchange = {name: {"missing_observations": sum(item["exchange"] == name for item in detail),
                        "securities": len({item["security_id"] for item in detail if item["exchange"] == name})}
                for name in sorted({row["exchange"] for row in per_symbol})}
    month = Counter(row["trading_date"][:7] for row in detail)
    run_id = new_artifact_id("m1-a1-missing-session-audit")
    output = root / "artifacts" / "data_enrichment" / run_id
    output.mkdir(parents=True, exist_ok=False)
    summary = {
        "securities": len(per_symbol), "missing_observations": len(detail),
        "exactly_1_missing": sum(row["missing_sessions_total"] == 1 for row in per_symbol),
        "missing_le_5": sum(0 < row["missing_sessions_total"] <= 5 for row in per_symbol),
        "missing_le_20": sum(0 < row["missing_sessions_total"] <= 20 for row in per_symbol),
        "latest_completed_snapshot": latest_date, "baseline_market_feature_ready": baseline_ready,
        "a1_market_feature_ready": a1_ready, "theoretical_max_readiness": a1_ready,
    }
    if stage_status not in {"PASS", "PARTIAL", "FAIL", "BLOCKED"}:
        raise ValueError("invalid A1 stage status")
    report = {"run_id": run_id, "generated_at": now(), "stage": "A1 — Missing Session Audit",
              "status": stage_status, "canonical_run_id": manifest["run_id"],
              "quality_report_id": quality["report_id"], "calendar_status": _calendar_status(calendar),
              "network_requests": 0, "summary": summary,
              "priority_counts": {key: priority_counts.get(key, 0) for key in ("P0", "P1", "P2", "P3", "P4")},
              "exchange_distribution": exchange,
              "month_concentration": dict(sorted(month.items(), key=lambda item: (-item[1], item[0]))),
              "input_hashes": {"canonical_manifest": digest(manifest_path.read_bytes()),
                               "quality_report": digest(quality_report_path.read_bytes())},
              "test_results": list(test_results),
              "limitations": ["calendar is PROVISIONAL_OBSERVED, not an official exchange calendar",
                              "historical identity intervals are provisional observed intervals",
                              "no provider-gap confirmation is possible without later source evidence"],}
    symbol_fields = list(per_symbol[0])
    recovery_fields = ["recovery_priority", "priority_reason", "missing_classification"] + symbol_fields
    detail_fields = list(detail[0]) if detail else ["security_id", "ticker", "exchange", "trading_date"]
    date_rows = [{"trading_date": day, "missing_observations": count,
                  "missing_securities": len({row["security_id"] for row in detail if row["trading_date"] == day})}
                 for day, count in sorted(Counter(row["trading_date"] for row in detail).items())]
    write_a1_parquet(output / "missing_session_audit.parquet", detail)
    atomic_write(output / "missing_session_by_symbol.csv", _csv_bytes(per_symbol, symbol_fields))
    atomic_write(output / "missing_session_by_date.csv", _csv_bytes(date_rows, list(date_rows[0]) if date_rows else ["trading_date", "missing_observations", "missing_securities"]))
    recovery.sort(key=lambda row: ({"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}[row["recovery_priority"]], row["missing_last_252"], row["ticker"]))
    atomic_write(output / "recovery_priority.csv", _csv_bytes(recovery, recovery_fields))
    write_json(output / "missing_classification_summary.json", report)
    atomic_write(output / "stage_a1_report.md", _report_markdown(report, recovery))
    report["artifacts"] = {path.relative_to(output).as_posix(): digest(path.read_bytes())
                           for path in sorted(output.iterdir()) if path.is_file()}
    write_json(output / "manifest.json", report)
    return output, report
