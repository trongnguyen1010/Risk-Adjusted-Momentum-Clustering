"""CafeF C3-R1 canonical market contract and immutable 27-security pilot.

The builder is offline except for one explicitly requested bounded VNINDEX extension.
It never mutates the prior CafeF staging artifact or any project baseline artifact.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from delta_t1.contracts import validate_rows
from delta_t1.features.market import build_features, latest_completed_snapshot_rows
from delta_t1.io import atomic_write, digest, encoded, now, read_json, read_rows, write_json
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.vnstock import KBSPublicHttpSource, map_kbs_wire_ohlcv_row


PRICE_CONTRACT = "CAFEF_CANONICAL_MARKET_V1_0"
TOTAL_ACTIVITY_CONTRACT = "CAFEF_TOTAL_MARKET_ACTIVITY_V1"
MARKET_AVAILABILITY_POLICY = "CAFEF_EOD_AVAILABILITY_ASSUMPTION_V1"
IDENTITY_AVAILABILITY_POLICY = "PILOT_IDENTITY_EFFECTIVE_FROM_ASSUMPTION_V1"
CALENDAR_POLICY = "BENCHMARK_DERIVED_RESEARCH_CALENDAR_V1"
QUARANTINE_FLAGS = {"INVALID_OHLC", "NONPOSITIVE_PRICE", "NEGATIVE_MARKET_VALUE"}
EXCHANGES = ("HOSE", "HNX", "UPCOM")
FEATURE_COLUMNS = (
    "security_id", "ticker", "as_of_date", "mom_21", "mom_63", "mom_126",
    "mom_252", "vol_63", "mdd_126", "beta_126", "liquidity_21",
    "feature_complete", "market_feature_ready", "historical_identity_ready",
    "research_ready", "universe_segment", "lookback_observations", "missing_count",
)
QUARANTINE_COLUMNS = (
    "candidate_id", "security_id", "ticker", "exchange", "trade_date",
    "quality_flags", "source_run_id", "request_key", "raw_relative_path", "raw_sha256",
)
COVERAGE_COLUMNS = (
    "security_id", "ticker", "exchange", "interval_start", "interval_end",
    "classification", "research_effect",
)
DOMAIN_COLUMNS = ("table", "disposition", "reason", "evidence")


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or _sha256_file(path) != expected:
        raise ValueError(f"{label} checksum mismatch: {path}")


def _csv_bytes(rows: list[dict], columns: tuple[str, ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows([{column: row.get(column, "") for column in columns} for row in rows])
    return stream.getvalue().encode("utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_jsonl(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def _max_timestamp(values) -> str:
    populated = [value for value in values if value]
    if not populated:
        raise ValueError("no timestamp evidence")
    return max(populated, key=lambda value: datetime.fromisoformat(value))


def _finite_positive(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _null_safe_total(first, second):
    for value in (first, second):
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("market activity components must be finite, non-negative, or null")
    return first + second


def _intervals(plan_row: dict[str, str]) -> list[dict]:
    rows = json.loads(plan_row["identity_intervals"])
    if not rows:
        raise ValueError(f"missing identity intervals for {plan_row['ticker']}")
    return rows


def _interval_for_day(plan_row: dict[str, str], day: str) -> dict | None:
    for interval in _intervals(plan_row):
        if interval["effective_from"] <= day <= (interval.get("effective_to") or "9999-12-31"):
            return interval
    return None


def acquire_benchmark_extension(root: Path, config: dict) -> dict:
    """Acquire exactly one public VNINDEX response and preserve immutable raw bytes."""
    target = _resolve(root, config["inputs"]["benchmark_extension_dir"])
    manifest_path = target / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        raw_path = target / manifest["raw_path"]
        _require_hash(raw_path, manifest["raw_sha256"], "benchmark extension raw")
        return manifest
    if target.exists():
        raise FileExistsError(f"refusing partial benchmark evidence directory: {target}")
    request = config["benchmark_extension"]
    if request.get("network_request_limit") != 1:
        raise ValueError("benchmark extension must be exactly one bounded request")
    client = PublicJsonClient(timeout=30, attempts=1, min_interval=0.0, max_bytes=2_000_000)
    response = KBSPublicHttpSource(client=client).acquire_ohlcv(
        request["symbol"], request["start"], request["end"], is_index=True,
    )
    mapped = [
        map_kbs_wire_ohlcv_row(row, request["symbol"], request["exchange"], is_index=True)
        for row in response["payload"]["data_day"]
    ]
    if not mapped or any(not request["start"] <= row["trade_date"] <= request["end"] for row in mapped):
        raise ValueError("VNINDEX extension returned an empty or out-of-range payload")
    target.mkdir(parents=True)
    raw_relative = "raw/vnindex_2026-09-16_2026-09-23.json"
    atomic_write(target / raw_relative, response["body"])
    manifest = {
        "run_id": target.name,
        "status": "COMPLETE",
        "provider": request["provider"],
        "symbol": request["symbol"],
        "exchange": request["exchange"],
        "requested_start": request["start"],
        "requested_end": request["end"],
        "url": response["url"],
        "http_status": response["status"],
        "fetched_at": now(),
        "network_requests": 1,
        "raw_path": raw_relative,
        "raw_sha256": digest(response["body"]),
        "row_count": len(mapped),
        "first_trade_date": min(row["trade_date"] for row in mapped),
        "last_trade_date": max(row["trade_date"] for row in mapped),
        "rights_status": "RIGHTS_NOT_VERIFIED",
        "execution_policy": "ACCEPTED_RESEARCH_RISK",
    }
    write_json(manifest_path, manifest)
    return manifest


def _load_inputs(root: Path, config: dict):
    inputs, expected = config["inputs"], config["expected_sha256"]
    c2_dir = _resolve(root, inputs["c2_c3_dir"])
    parent = _resolve(root, inputs["reviewed_canonical_dir"])
    master_path = _resolve(root, inputs["reviewed_security_master"])
    paths = {
        "c2_manifest": c2_dir / "manifest.json",
        "candidates": c2_dir / "normalized_market_candidates.jsonl",
        "master": master_path,
        "parent_manifest": parent / "manifest.json",
        "parent_securities": parent / "clean/securities.jsonl",
        "scale_securities": _resolve(root, inputs["reviewed_scale_securities"]),
        "parent_calendar": parent / "clean/trading_calendar.jsonl",
        "parent_benchmark": parent / "clean/benchmark_daily.jsonl",
    }
    for key, expected_key in (
        ("c2_manifest", "c2_c3_manifest"), ("candidates", "normalized_candidates"),
        ("master", "reviewed_security_master"), ("parent_manifest", "reviewed_canonical_manifest"),
        ("parent_securities", "reviewed_securities"), ("parent_calendar", "reviewed_calendar"),
        ("parent_benchmark", "reviewed_benchmark"),
        ("scale_securities", "reviewed_scale_securities"),
    ):
        _require_hash(paths[key], expected[expected_key], key)
    c2_manifest = read_json(paths["c2_manifest"])
    if c2_manifest.get("summary", {}).get("raw_audit_pass_count") != 27:
        raise ValueError("C3-R1 requires the audited 27-security C2/C3 parent")
    parent_manifest = read_json(paths["parent_manifest"])
    if parent_manifest.get("canonical_promotion_status") != "PASS_PROVISIONAL_PILOT":
        raise ValueError("reviewed parent canonical artifact is not approved for pilot reuse")
    extension_dir = _resolve(root, inputs["benchmark_extension_dir"])
    extension_manifest = read_json(extension_dir / "manifest.json")
    if extension_manifest.get("status") != "COMPLETE" or extension_manifest.get("network_requests") != 1:
        raise ValueError("bounded benchmark extension evidence is missing or invalid")
    _require_hash(
        extension_dir / extension_manifest["raw_path"],
        extension_manifest["raw_sha256"],
        "benchmark extension raw",
    )
    paths["extension_dir"] = extension_dir
    return paths, c2_manifest, parent_manifest, extension_manifest


def _build_securities(plan_rows, master_document, parent_rows, scale_rows, data_version):
    master = {row["ticker"]: row for row in master_document["securities"]}
    parent = {row["ticker"]: row for row in parent_rows}
    scale = {row["ticker"]: row for row in scale_rows}
    if master_document.get("identity_status") != "provisional_verified_for_pilot":
        raise ValueError("reviewed security master scope is incompatible")
    required_tickers = {row["ticker"] for row in plan_rows}
    if not required_tickers <= (set(master) | set(scale)) or not required_tickers <= (set(parent) | set(scale)):
        raise ValueError("reviewed security metadata does not cover the CafeF pilot")
    output = []
    for plan in plan_rows:
        ticker = plan["ticker"]
        name_evidence = master.get(ticker) or scale[ticker]
        detail_evidence = parent.get(ticker) or scale[ticker]
        current_exchange = _intervals(plan)[-1]["exchange"]
        if name_evidence["exchange"] != current_exchange:
            raise ValueError(f"current reviewed exchange differs from frozen identity for {ticker}")
        fetched_at = (
            master_document["source_evidence"]["fetched_at"]
            if ticker in master else name_evidence["fetched_at"]
        )
        for interval in _intervals(plan):
            effective_to = interval.get("effective_to")
            valid_to = (
                (date.fromisoformat(effective_to) + timedelta(days=1)).isoformat()
                if effective_to else None
            )
            output.append({
                "security_id": plan["security_id"],
                "ticker": ticker,
                "company_name": name_evidence["company_name"],
                "exchange": interval["exchange"],
                "listing_date": detail_evidence.get("listing_date"),
                "delisting_date": None,
                "valid_from": interval["effective_from"],
                "valid_to": valid_to,
                "available_at": f"{interval['effective_from']}T00:00:00+07:00",
                "sector": detail_evidence.get("sector"),
                "industry": detail_evidence.get("industry"),
                "currency": "VND",
                "price_unit": "VND",
                "identity_status": "provisional_verified_for_pilot",
                "source": (
                    "frozen_cafef_v3_identity+reviewed_pilot_security_master"
                    if ticker in master
                    else "frozen_cafef_v3_identity+reviewed_m1_scale_security_master"
                ),
                "fetched_at": fetched_at,
                "data_version": data_version,
            })
    output.sort(key=lambda row: (row["security_id"], row["valid_from"]))
    return output


def map_candidate(candidate: dict, plan_row: dict[str, str], data_version: str) -> dict | None:
    """Map one non-quarantined candidate under the frozen CafeF market contract."""
    if set(candidate.get("quality_flags", [])) & QUARANTINE_FLAGS:
        return None
    adjusted = candidate.get("provider_adjusted_vnd")
    if not _finite_positive(adjusted):
        return None
    interval = _interval_for_day(plan_row, candidate["trade_date"])
    if interval is None:
        raise ValueError(f"price outside frozen identity interval: {candidate['ticker']} {candidate['trade_date']}")
    if candidate["exchange"] != interval["exchange"]:
        raise ValueError(f"identity-routed exchange mismatch: {candidate['ticker']} {candidate['trade_date']}")
    matched_volume = candidate.get("matched_volume_shares")
    status = (
        "normal"
        if isinstance(matched_volume, (int, float)) and not isinstance(matched_volume, bool)
        and math.isfinite(matched_volume) and matched_volume > 0
        else "unknown"
    )
    return {
        "security_id": candidate["security_id"],
        "ticker": candidate["ticker"],
        "exchange": interval["exchange"],
        "trade_date": candidate["trade_date"],
        "raw_open": None,
        "raw_high": None,
        "raw_low": None,
        "raw_close": None,
        "reference_price": None,
        "ceiling_price": None,
        "floor_price": None,
        "adj_close": adjusted,
        "adjustment_basis": "vendor_adjusted",
        "volume": _null_safe_total(
            candidate.get("matched_volume_shares"), candidate.get("negotiated_volume_shares")
        ),
        "traded_value": _null_safe_total(
            candidate.get("matched_value_vnd"), candidate.get("negotiated_value_vnd")
        ),
        "trading_status": status,
        "available_at": f"{candidate['trade_date']}T17:00:00+07:00",
        "source": "cafef",
        "fetched_at": candidate["fetched_at"],
        "data_version": data_version,
    }


def _quarantine_row(candidate: dict) -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "security_id": candidate["security_id"],
        "ticker": candidate["ticker"],
        "exchange": candidate["exchange"],
        "trade_date": candidate["trade_date"],
        "quality_flags": candidate.get("quality_flags", []),
        "source_run_id": candidate["source_run_id"],
        "request_key": candidate["request_key"],
        "raw_relative_path": candidate["raw_relative_path"],
        "raw_sha256": candidate["raw_sha256"],
    }


def _load_extension_rows(extension_dir: Path, manifest: dict) -> list[dict]:
    payload = json.loads((extension_dir / manifest["raw_path"]).read_text(encoding="utf-8"))
    rows = [
        map_kbs_wire_ohlcv_row(raw, "VNINDEX", "HOSE", is_index=True)
        for raw in payload["data_day"]
    ]
    if len(rows) != manifest["row_count"]:
        raise ValueError("benchmark extension row count changed")
    return rows


def _build_benchmark(parent_rows, extension_rows, start, end, extension_manifest, data_version):
    by_date = {}
    for row in parent_rows:
        if start <= row["trade_date"] <= end:
            by_date[row["trade_date"]] = dict(row, data_version=data_version)
    for row in extension_rows:
        if not start <= row["trade_date"] <= end:
            continue
        mapped = {
            "index_id": "VNINDEX",
            "trade_date": row["trade_date"],
            "close": row["close"],
            "total_return_level": None,
            "available_at": f"{row['trade_date']}T17:00:00+07:00",
            "source": "kbs_delta_public_http",
            "fetched_at": extension_manifest["fetched_at"],
            "data_version": data_version,
            "exchange": "HOSE",
            "index_basis": "price",
        }
        existing = by_date.get(row["trade_date"])
        if existing and existing["close"] != mapped["close"]:
            raise ValueError(f"conflicting VNINDEX close on {row['trade_date']}")
        by_date[row["trade_date"]] = mapped
    output = [by_date[day] for day in sorted(by_date)]
    if not output or output[0]["trade_date"] > start or output[-1]["trade_date"] != end:
        raise ValueError("VNINDEX benchmark does not cover the bounded pilot window")
    return output


def _reviewed_calendar_sets(rows, start, cutoff):
    sets = {exchange: set() for exchange in EXCHANGES}
    for row in rows:
        if row["is_open"] and start <= row["trade_date"] <= cutoff and row["exchange"] in sets:
            sets[row["exchange"]].add(row["trade_date"])
    if not sets["HOSE"] or any(sets[exchange] != sets["HOSE"] for exchange in EXCHANGES[1:]):
        raise ValueError("reviewed calendar does not support the shared three-exchange pilot assumption")
    return sets


def _build_calendar(parent_rows, benchmark, prices, start, end, extension_start, fetched_at, data_version):
    cutoff = (date.fromisoformat(extension_start) - timedelta(days=1)).isoformat()
    sets = _reviewed_calendar_sets(parent_rows, start, cutoff)
    extension_days = {row["trade_date"] for row in benchmark if row["trade_date"] >= extension_start}
    for exchange in EXCHANGES:
        sets[exchange].update(extension_days)
    price_keys = {(row["exchange"], row["trade_date"]) for row in prices}
    missing = sorted(key for key in price_keys if key[1] not in sets[key[0]])
    if missing:
        raise ValueError(f"CafeF canonical price lacks reviewed/benchmark calendar evidence: {missing[:5]}")
    output = []
    for exchange in EXCHANGES:
        days = sorted(day for day in sets[exchange] if start <= day <= end)
        month_ends = {day[:7]: day for day in days}
        for day in days:
            output.append({
                "exchange": exchange,
                "trade_date": day,
                "is_open": True,
                "is_month_end": month_ends[day[:7]] == day,
                "close_at": f"{day}T15:00:00+07:00",
                "decision_at": f"{day}T17:00:00+07:00",
                "source": "reviewed_calendar+benchmark_extension_shared_session_assumption",
                "fetched_at": fetched_at,
                "data_version": data_version,
                "open_at": None,
                "available_at": f"{day}T17:00:00+07:00",
            })
    output.sort(key=lambda row: (row["exchange"], row["trade_date"]))
    return output


def _coverage_exceptions(plan_rows, candidates, start, end):
    observed = defaultdict(set)
    for row in candidates:
        observed[(row["security_id"], row["exchange"])].add(row["trade_date"])
    exceptions = []
    for plan in plan_rows:
        for interval in _intervals(plan):
            interval_start = max(start, interval["effective_from"])
            interval_end = min(end, interval.get("effective_to") or end)
            if interval_start > interval_end:
                continue
            dates = observed[(plan["security_id"], interval["exchange"])]
            if not any(interval_start <= day <= interval_end for day in dates):
                exceptions.append({
                    "security_id": plan["security_id"],
                    "ticker": plan["ticker"],
                    "exchange": interval["exchange"],
                    "interval_start": interval_start,
                    "interval_end": interval_end,
                    "classification": "UNRESOLVED_IDENTITY_INTERVAL_NO_OBSERVATIONS",
                    "research_effect": "retain security; later complete windows remain independently evaluated",
                })
    return exceptions


def _dependency_report(feature_config: dict) -> dict:
    required = feature_config["required_features"]
    dependencies = {
        "mom_21": ["prices_daily.adj_close", "trading_calendar.open_sessions"],
        "mom_63": ["prices_daily.adj_close", "trading_calendar.open_sessions"],
        "mom_126": ["prices_daily.adj_close", "trading_calendar.open_sessions"],
        "mom_252": ["prices_daily.adj_close", "trading_calendar.open_sessions"],
        "vol_63": ["prices_daily.adj_close", "trading_calendar.open_sessions"],
        "mdd_126": ["prices_daily.adj_close", "trading_calendar.open_sessions"],
        "beta_126": [
            "prices_daily.adj_close", "benchmark_daily.close", "trading_calendar.open_sessions"
        ],
        "liquidity_21": ["prices_daily.traded_value", "trading_calendar.open_sessions"],
    }
    if any(name not in dependencies for name in required):
        raise ValueError("required feature dependency is not documented")
    return {
        "report_version": "CAFEF_MARKET_FEATURE_DEPENDENCY_REPORT_V1_0",
        "feature_set": feature_config["feature_set"],
        "required_features": required,
        "dependencies": {name: dependencies[name] for name in required},
        "price_selection_rule": "vendor_adjusted selects prices_daily.adj_close",
        "missing_session_policy": "None; no fill, interpolation, zero return, or timeline compression",
        "implementation_reference": "src/delta_t1/features/market.py:build_features",
    }


def _domain_disposition() -> list[dict]:
    ready = "READY_FOR_CURRENT_MARKET_PIPELINE"
    deferred = "DEFERRED_NOT_REQUIRED_FOR_CURRENT_MARKET_PIPELINE"
    return [
        {"table": "prices_daily", "disposition": ready,
         "reason": "CafeF GiaDieuChinh approved as vendor_adjusted; null-safe total activity policy frozen",
         "evidence": PRICE_CONTRACT},
        {"table": "securities", "disposition": ready,
         "reason": "reviewed company labels plus frozen V3 identity intervals; pilot-scoped identity only",
         "evidence": IDENTITY_AVAILABILITY_POLICY},
        {"table": "trading_calendar", "disposition": ready,
         "reason": "reviewed shared session history extended by bounded VNINDEX sessions; not official calendar",
         "evidence": CALENDAR_POLICY},
        {"table": "benchmark_daily", "disposition": ready,
         "reason": "reviewed immutable VNINDEX price index plus one bounded extension",
         "evidence": "VNINDEX_PRICE_INDEX_REUSE_AND_EXTENSION_V1"},
        {"table": "shares_history", "disposition": deferred,
         "reason": "no approved historical share-count source; no active required market feature depends on it",
         "evidence": "NO_FABRICATION"},
        {"table": "corporate_actions", "disposition": deferred,
         "reason": "vendor_adjusted proxy does not require independent DELTA adjustment reconstruction",
         "evidence": "OWNER_C3_R1_DECISION"},
        {"table": "financial_reports", "disposition": deferred,
         "reason": "financial PIT remains unresolved and is outside current market-only feature config",
         "evidence": "PIT_UNRESOLVED"},
        {"table": "financial_facts", "disposition": deferred,
         "reason": "financial PIT remains unresolved and is outside current market-only feature config",
         "evidence": "PIT_UNRESOLVED"},
    ]


def _feature_readiness(features, collection_end, required):
    snapshot_date, latest = latest_completed_snapshot_rows(features, collection_end)
    rows = []
    for row in sorted(latest.values(), key=lambda item: item["ticker"]):
        rows.append({column: row.get(column) for column in FEATURE_COLUMNS})
    coverage = {
        name: {
            "available": sum(row.get(name) is not None for row in latest.values()),
            "total": len(latest),
        }
        for name in required
    }
    summary = {
        "snapshot_date": snapshot_date,
        "total": len(latest),
        "feature_complete": sum(row["feature_complete"] for row in latest.values()),
        "market_feature_ready": sum(row["market_feature_ready"] for row in latest.values()),
        "historical_identity_ready": sum(row["historical_identity_ready"] for row in latest.values()),
        "research_ready": sum(row["research_ready"] for row in latest.values()),
        "reference_only": sum(row["universe_segment"] == "REFERENCE_ONLY" for row in latest.values()),
        "per_feature_non_null": coverage,
    }
    return rows, summary


def _stage_status(checks: dict, feature_summary: dict) -> str:
    """Require all 27 pilot securities to satisfy the frozen market feature gate."""
    return (
        "PASS"
        if all(checks.values()) and feature_summary["market_feature_ready"] == 27
        else "PARTIAL_MANUAL_REVIEW_REQUIRED"
    )


def _latest_window_missing_sessions(calendar, prices, securities, snapshot_date: str) -> list[dict]:
    """Group missing observations in the 253-session momentum window without filling them."""
    sessions = defaultdict(list)
    for row in calendar:
        if row["is_open"] and row["trade_date"] <= snapshot_date:
            sessions[row["exchange"]].append(row["trade_date"])
    observed = defaultdict(set)
    for row in prices:
        if row["trade_date"] <= snapshot_date:
            observed[row["security_id"]].add(row["trade_date"])
    current = {}
    for row in securities:
        if row["valid_from"] <= snapshot_date < (row["valid_to"] or "9999-12-31"):
            current[row["security_id"]] = row
    grouped = defaultdict(list)
    for security_id, row in current.items():
        window = sorted(set(sessions[row["exchange"]]))[-253:]
        missing = tuple(day for day in window if day not in observed[security_id])
        if missing:
            grouped[missing].append(row["ticker"])
    return [
        {"tickers": sorted(tickers), "missing_sessions": list(missing)}
        for missing, tickers in sorted(grouped.items(), key=lambda item: (len(item[0]), item[0]))
    ]


def build_canonical_pilot(root: Path, config: dict, output_dir: Path) -> dict:
    """Build and validate a new immutable CafeF canonical pilot artifact."""
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite immutable output: {output_dir}")
    paths, c2_manifest, parent_manifest, extension_manifest = _load_inputs(root, config)
    start, end = config["base_window"]["start"], config["base_window"]["end"]
    plan_rows = _read_csv(_resolve(root, config["inputs"]["active_plan_csv"]))
    if len(plan_rows) != 27:
        raise ValueError("C3-R1 pilot plan must contain exactly 27 securities")
    plan_by_ticker = {row["ticker"]: row for row in plan_rows}
    feature_config = read_json(_resolve(root, config["inputs"]["feature_config"]))
    run_id = output_dir.name
    data_version = PRICE_CONTRACT

    all_candidates, canonical_prices, quarantined = [], [], []
    for candidate in _read_jsonl(paths["candidates"]):
        if not start <= candidate["trade_date"] <= end:
            continue
        all_candidates.append(candidate)
        if set(candidate.get("quality_flags", [])) & QUARANTINE_FLAGS or not _finite_positive(
            candidate.get("provider_adjusted_vnd")
        ):
            quarantined.append(_quarantine_row(candidate))
            continue
        mapped = map_candidate(candidate, plan_by_ticker[candidate["ticker"]], data_version)
        if mapped is not None:
            canonical_prices.append(mapped)
    canonical_prices.sort(key=lambda row: (row["security_id"], row["trade_date"]))
    quarantined.sort(key=lambda row: (row["security_id"], row["trade_date"]))

    master_document = read_json(paths["master"])
    parent_securities = list(_read_jsonl(paths["parent_securities"]))
    scale_securities = list(_read_jsonl(paths["scale_securities"]))
    securities = _build_securities(
        plan_rows, master_document, parent_securities, scale_securities, data_version,
    )
    parent_benchmark = list(_read_jsonl(paths["parent_benchmark"]))
    extension_rows = _load_extension_rows(paths["extension_dir"], extension_manifest)
    benchmark = _build_benchmark(
        parent_benchmark, extension_rows, start, end, extension_manifest, data_version,
    )
    parent_calendar = list(_read_jsonl(paths["parent_calendar"]))
    calendar_fetched_at = _max_timestamp(
        [row["fetched_at"] for row in parent_calendar] + [extension_manifest["fetched_at"]]
    )
    calendar = _build_calendar(
        parent_calendar, benchmark, canonical_prices, start, end,
        config["benchmark_extension"]["start"], calendar_fetched_at, data_version,
    )

    for table, rows in (
        ("prices_daily", canonical_prices), ("securities", securities),
        ("trading_calendar", calendar), ("benchmark_daily", benchmark),
    ):
        validate_rows(table, rows)
    price_keys = {(row["security_id"], row["trade_date"]) for row in canonical_prices}
    quarantine_keys = {(row["security_id"], row["trade_date"]) for row in quarantined}
    if price_keys & quarantine_keys:
        raise ValueError("quarantine/canonical price intersection is non-empty")
    if len(price_keys) != len(canonical_prices):
        raise ValueError("duplicate canonical price key")
    security_intervals = defaultdict(list)
    for row in securities:
        security_intervals[row["security_id"]].append(row)
    for row in canonical_prices:
        matches = [
            item for item in security_intervals[row["security_id"]]
            if item["valid_from"] <= row["trade_date"] < (item["valid_to"] or "9999-12-31")
        ]
        if len(matches) != 1 or matches[0]["exchange"] != row["exchange"]:
            raise ValueError(f"canonical price identity relation failed: {row['security_id']} {row['trade_date']}")
    open_days = {(row["exchange"], row["trade_date"]) for row in calendar if row["is_open"]}
    if any((row["exchange"], row["trade_date"]) not in open_days for row in canonical_prices):
        raise ValueError("canonical price calendar relation failed")
    if any(any(row[field] is not None for field in ("raw_open", "raw_high", "raw_low", "raw_close"))
           for row in canonical_prices):
        raise ValueError("provider OHLC leaked into canonical raw fields")

    dependency_report = _dependency_report(feature_config)
    feature_config = dict(feature_config)
    feature_config.update({
        "data_mode": "real",
        "vendor_run_id": c2_manifest["run_id"],
        "canonical_run_id": run_id,
    })
    features = build_features({
        "securities": securities,
        "prices_daily": canonical_prices,
        "trading_calendar": calendar,
        "benchmark_daily": benchmark,
    }, feature_config, run_id)
    validate_rows("feature_snapshots", features)
    feature_rows, feature_summary = _feature_readiness(
        features, end, feature_config["required_features"],
    )
    if feature_summary["total"] != 27:
        raise ValueError("feature dry run did not produce the exact pilot snapshot")

    coverage_exceptions = _coverage_exceptions(plan_rows, all_candidates, start, end)
    domain_rows = _domain_disposition()
    benchmark_dates = {row["trade_date"] for row in benchmark}
    hose_sessions = {row["trade_date"] for row in calendar if row["exchange"] == "HOSE"}
    checks = {
        "prices_daily_schema": True,
        "securities_schema": True,
        "trading_calendar_schema": True,
        "benchmark_daily_schema": True,
        "feature_snapshots_schema": True,
        "unique_price_keys": len(price_keys) == len(canonical_prices),
        "identity_relation": True,
        "calendar_relation": True,
        "quarantine_excluded": not bool(price_keys & quarantine_keys),
        "quarantine_count_is_11": len(quarantined) == 11,
        "raw_ohlc_null": all(row["raw_close"] is None for row in canonical_prices),
        "vendor_adjusted_only": all(row["adjustment_basis"] == "vendor_adjusted" for row in canonical_prices),
        "positive_adjusted_close": all(_finite_positive(row["adj_close"]) for row in canonical_prices),
        "no_imputation": True,
        "benchmark_reaches_window_end": max(benchmark_dates) == end,
        "calendar_reaches_window_end": max(hose_sessions) == end,
        "required_features_unchanged": feature_config["required_features"] == [
            "mom_21", "mom_63", "mom_126", "mom_252",
            "vol_63", "mdd_126", "beta_126", "liquidity_21",
        ],
        "feature_dry_run": True,
        "market_feature_ready_all_27": feature_summary["market_feature_ready"] == 27,
        "canonical_baseline_preserved": True,
        "no_scale_crawl": True,
    }
    status = _stage_status(checks, feature_summary)
    missing_feature_sessions = _latest_window_missing_sessions(
        calendar, canonical_prices, securities, feature_summary["snapshot_date"],
    )
    quality = {
        "stage": "C3-R1",
        "status": status,
        "checks": checks,
        "policies": {
            "price_basis": "GiaDieuChinh*1000 -> adj_close; vendor_adjusted research proxy",
            "raw_ohlc": "staging-only; canonical null",
            "volume": "matched_volume_shares + negotiated_volume_shares; null if either component null",
            "traded_value": "matched_value_vnd + negotiated_value_vnd; null if either component null",
            "availability": MARKET_AVAILABILITY_POLICY,
            "identity_availability": IDENTITY_AVAILABILITY_POLICY,
            "calendar": CALENDAR_POLICY,
        },
        "benchmark_coverage": {
            "calendar_open_sessions": len(hose_sessions),
            "benchmark_sessions": len(benchmark_dates),
            "calendar_sessions_without_benchmark": len(hose_sessions - benchmark_dates),
            "benchmark_first_date": min(benchmark_dates),
            "benchmark_last_date": max(benchmark_dates),
        },
        "counts": {
            "parent_candidates": len(all_candidates),
            "prices_daily": len(canonical_prices),
            "quarantined": len(quarantined),
            "securities": len(securities),
            "trading_calendar": len(calendar),
            "benchmark_daily": len(benchmark),
            "coverage_exceptions": len(coverage_exceptions),
        },
        "feature_readiness": feature_summary,
        "market_feature_blockers": {
            "missing_session_policy": "None; no fill or timeline compression",
            "latest_253_session_window_missing_observations": missing_feature_sessions,
        },
    }

    output_dir.mkdir(parents=True)
    outputs = {
        "prices_daily.jsonl": b"".join(encoded(row) + b"\n" for row in canonical_prices),
        "securities.jsonl": b"".join(encoded(row) + b"\n" for row in securities),
        "trading_calendar.jsonl": b"".join(encoded(row) + b"\n" for row in calendar),
        "benchmark_daily.jsonl": b"".join(encoded(row) + b"\n" for row in benchmark),
        "quarantined_market_rows.jsonl": b"".join(encoded(row) + b"\n" for row in quarantined),
        "coverage_exceptions.csv": _csv_bytes(coverage_exceptions, COVERAGE_COLUMNS),
        "domain_disposition.csv": _csv_bytes(domain_rows, DOMAIN_COLUMNS),
        "market_feature_dependency_report.json": encoded(dependency_report) + b"\n",
        "quality_report.json": encoded(quality) + b"\n",
        "feature_readiness_report.csv": _csv_bytes(feature_rows, FEATURE_COLUMNS),
        "feature_snapshots_pilot.jsonl": b"".join(encoded(row) + b"\n" for row in features),
    }
    for name, content in outputs.items():
        atomic_write(output_dir / name, content)
    manifest = {
        "run_id": run_id,
        "stage": "C3-R1 CAFEF CANONICAL MARKET CONTRACT",
        "status": status,
        "price_contract": PRICE_CONTRACT,
        "total_activity_contract": TOTAL_ACTIVITY_CONTRACT,
        "market_availability_policy": MARKET_AVAILABILITY_POLICY,
        "identity_availability_policy": IDENTITY_AVAILABILITY_POLICY,
        "calendar_policy": CALENDAR_POLICY,
        "network_requests": extension_manifest["network_requests"],
        "canonical_baseline_overwritten": False,
        "scale_crawl": False,
        "counts": quality["counts"],
        "feature_readiness": feature_summary,
        "checks": checks,
        "coverage_exceptions": [row["ticker"] for row in coverage_exceptions],
        "deferred_domains": [
            row["table"] for row in domain_rows
            if row["disposition"] == "DEFERRED_NOT_REQUIRED_FOR_CURRENT_MARKET_PIPELINE"
        ],
        "parents": {
            "cafef_c2_c3": c2_manifest["run_id"],
            "reviewed_canonical": parent_manifest["run_id"],
            "benchmark_extension": extension_manifest["run_id"],
        },
        "input_hashes": config["expected_sha256"],
        "config_sha256": digest(encoded(config)),
        "builder_sha256": _sha256_file(Path(__file__)),
        "output_hashes": {name: digest(content) for name, content in outputs.items()},
        "limitations": [
            "GiaDieuChinh is a provider-published vendor-adjusted research proxy, not reconstructed total return",
            "provider OHLC remains staging-only",
            "calendar is a bounded research calendar, not an official exchange calendar",
            "identity remains provisional_verified_for_pilot",
            "historical provider publication timestamps are unavailable; EOD availability is an assumption",
        ],
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest
