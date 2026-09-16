"""Offline canonical-readiness mapping for one frozen representative pilot run."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ..artifact_ids import new_artifact_id
from ..contracts import validate_rows
from ..io import digest, encoded, now, read_json, write_json, write_rows
from .representative_pilot import _valid_kbs, load_readiness
from .representative_pilot_finalize import (
    _raw_payload, _rule, _source_run, load_qc_policy,
)
from .sources.cafef import (
    classify_cafef_page_row, map_trade_history_row, price_band_row_status,
)
from .sources.vnstock import map_kbs_wire_ohlcv_row


AVAILABILITY_TIME = "17:00:00+07:00"
CLOSE_TIME = "15:00:00+07:00"


def _fetched_at(artifact):
    value = artifact.get("fetched_at")
    if not isinstance(value, str):
        raise ValueError("provider artifact lacks fetched_at")
    return datetime.fromisoformat(value).isoformat()


def _latest_stamp(*values):
    values = [value for value in values if value]
    return max(values, key=datetime.fromisoformat)


def _validate_assessment(path, run_id, prepared, policy_hash):
    path = Path(path).resolve()
    assessment = read_json(path)
    gate = read_json(path.parent / "gate.json")
    required = (
        assessment.get("source_run_id") == run_id
        and assessment.get("mode") == "OFFLINE_IMMUTABLE_REPLAY"
        and assessment.get("network_requests") == 0
        and assessment.get("gate_status") == "PASS"
        and assessment.get("policy_hash") == policy_hash
        and assessment.get("config_hash") == prepared["config_hash"]
        and assessment.get("universe_hash") == prepared["universe_hash"]
        and assessment.get("source_gate_hash") == prepared["source_gate_hash"]
        and gate.get("gate") == "REPRESENTATIVE_PILOT"
        and gate.get("status") == "PASS"
    )
    if not required:
        raise ValueError("canonical mapping requires the matching PASS QC assessment")
    return path, assessment, gate


def _calendar(rows, data_version, fetched_at):
    dates = defaultdict(set)
    for row in rows:
        dates[row["exchange"]].add(row["trade_date"])
    output = []
    for exchange, days in sorted(dates.items()):
        month_end = {}
        for day in days:
            month_end[day[:7]] = max(day, month_end.get(day[:7], day))
        for day in sorted(days):
            output.append({
                "exchange": exchange, "trade_date": day, "is_open": True,
                "is_month_end": day == month_end[day[:7]],
                "open_at": None, "close_at": f"{day}T{CLOSE_TIME}",
                "decision_at": f"{day}T{AVAILABILITY_TIME}",
                "available_at": f"{day}T{AVAILABILITY_TIME}",
                "source": "kbs_observed_session_union",
                "fetched_at": fetched_at, "data_version": data_version,
            })
    return output


def map_canonical_candidates(config_path, gate_report_path, policy_path,
                             assessment_path, run_id, *, root):
    """Map accepted raw rows to standard market-table candidates without network."""
    root = Path(root).resolve()
    prepared = load_readiness(config_path, gate_report_path, root=root)
    source_dir, _, source, _ = _source_run(root, run_id, prepared)
    policy_path, _, rules = load_qc_policy(policy_path, run_id)
    policy_hash = digest(policy_path.read_bytes())
    assessment_path, assessment, pilot_gate = _validate_assessment(
        assessment_path, run_id, prepared, policy_hash)
    run_id_out = new_artifact_id("canonical-pilot-candidate")
    target = root / "data" / "canonical" / run_id_out
    if target.exists():
        raise ValueError("immutable canonical candidate already exists")

    universe = {row["ticker"]: row for row in prepared["universe"]}
    semantics_path = root / "docs" / "data" / "kbs_pilot_semantics.md"
    if not semantics_path.is_file():
        raise ValueError("required KBS mapping-semantics evidence is missing")
    kbs, cafef = defaultdict(list), defaultdict(list)
    raw_hashes, used, findings = {}, set(), []
    latest_fetch = None
    for state in source["jobs"].values():
        job = state["job"]
        for artifact in state["artifacts"]:
            payload = _raw_payload(root, run_id, artifact)
            raw_hashes[artifact["raw_path"]] = artifact["sha256"]
            stamp = _fetched_at(artifact)
            latest_fetch = _latest_stamp(latest_fetch, stamp)
            if job["kind"] in ("equity", "index"):
                for raw in payload["data_day"]:
                    mapped = map_kbs_wire_ohlcv_row(
                        raw, job["symbol"], job["exchange"],
                        is_index=job["kind"] == "index")
                    if not _valid_kbs([mapped], index=job["kind"] == "index"):
                        classification = _rule(
                            rules, used, "kbs", job["symbol"], mapped["trade_date"], raw)
                        if not classification:
                            raise ValueError(
                                f"unreviewed KBS invalid row: {job['symbol']} {mapped['trade_date']}")
                        findings.append(("kbs", job["symbol"], mapped["trade_date"]))
                        continue
                    kbs[job["symbol"]].append((mapped, artifact))
            elif job["kind"] == "reference_limits_value":
                page = artifact.get("request", {}).get("page_index")
                if not isinstance(page, int) or page < 1:
                    raise ValueError("CafeF replay artifact lacks page_index")
                for index, raw in enumerate(payload["Data"]):
                    if classify_cafef_page_row(
                            raw.get("TradeDate"), page=page,
                            row_index=index) == "CURRENT_SNAPSHOT":
                        continue
                    mapped = map_trade_history_row(raw, job["symbol"], job["exchange"])
                    if not job["start"] <= mapped["trade_date"] <= job["end"]:
                        continue
                    if price_band_row_status(mapped) != "VALID":
                        classification = _rule(
                            rules, used, "cafef", job["symbol"], mapped["trade_date"], raw)
                        if not classification:
                            raise ValueError(
                                f"unreviewed CafeF invalid row: {job['symbol']} {mapped['trade_date']}")
                        findings.append(("cafef", job["symbol"], mapped["trade_date"]))
                        continue
                    cafef[job["symbol"]].append((mapped, artifact))
    if used != set(rules):
        raise ValueError("QC rules do not exactly match replayed source evidence")

    prices, benchmark, lineage = [], [], []
    cafef_count = sum(len(rows) for rows in cafef.values())
    cafef_by_key = {
        (symbol, row["trade_date"]): (row, artifact)
        for symbol, rows in cafef.items() for row, artifact in rows
    }
    if len(cafef_by_key) != cafef_count:
        raise ValueError("duplicate CafeF symbol/date cannot be silently selected")
    for symbol, meta in universe.items():
        for row, artifact in kbs[symbol]:
            reference = cafef_by_key.get((symbol, row["trade_date"]))
            cafe_row, cafe_artifact = reference if reference else (None, None)
            source_name = "kbs_delta_public_http"
            fetched = _fetched_at(artifact)
            raw_inputs = [{"provider": "kbs", "raw_path": artifact["raw_path"],
                           "sha256": artifact["sha256"],
                           "fields": ["adj_close", "volume"]}]
            if cafe_row is not None:
                source_name += "+cafef_direct"
                fetched = _latest_stamp(fetched, _fetched_at(cafe_artifact))
                raw_inputs.append({"provider": "cafef", "raw_path": cafe_artifact["raw_path"],
                                   "sha256": cafe_artifact["sha256"],
                                   "fields": ["traded_value"]})
            prices.append({
                "security_id": meta["security_id"], "ticker": symbol,
                "exchange": meta["exchange"], "trade_date": row["trade_date"],
                "raw_open": None, "raw_high": None, "raw_low": None, "raw_close": None,
                "reference_price": None, "ceiling_price": None, "floor_price": None,
                "adj_close": row["close"], "adjustment_basis": "vendor_adjusted",
                "volume": row["volume"],
                "traded_value": cafe_row["traded_value"] if cafe_row else None,
                "trading_status": "normal" if row["volume"] is not None and row["volume"] > 0
                else "unknown",
                "available_at": f"{row['trade_date']}T{AVAILABILITY_TIME}",
                "source": source_name, "fetched_at": fetched, "data_version": run_id_out,
            })
            lineage.append({"table": "prices_daily",
                            "canonical_key": [meta["security_id"], row["trade_date"]],
                            "raw_inputs": raw_inputs})
    for row, artifact in kbs["VNINDEX"]:
        benchmark.append({
            "index_id": "VNINDEX", "trade_date": row["trade_date"],
            "close": row["close"], "total_return_level": None,
            "available_at": f"{row['trade_date']}T{AVAILABILITY_TIME}",
            "source": "kbs_delta_public_http", "fetched_at": _fetched_at(artifact),
            "data_version": run_id_out, "exchange": "HOSE", "index_basis": "price",
        })
        lineage.append({"table": "benchmark_daily",
                        "canonical_key": ["VNINDEX", row["trade_date"]],
                        "raw_inputs": [{"provider": "kbs", "raw_path": artifact["raw_path"],
                                        "sha256": artifact["sha256"], "fields": ["close"]}]})
    prices.sort(key=lambda row: (row["security_id"], row["trade_date"]))
    benchmark.sort(key=lambda row: row["trade_date"])
    calendar = _calendar(prices, run_id_out, latest_fetch)
    for name, rows in (("prices_daily", prices), ("benchmark_daily", benchmark),
                       ("trading_calendar", calendar)):
        validate_rows(name, rows)
    open_days = {(row["exchange"], row["trade_date"]) for row in calendar if row["is_open"]}
    if any((row["exchange"], row["trade_date"]) not in open_days for row in prices):
        raise ValueError("mapped price lacks observed-session calendar row")

    latest_21 = {}
    for symbol, meta in universe.items():
        rows = [row for row in prices if row["security_id"] == meta["security_id"]]
        tail = rows[-21:]
        latest_21[symbol] = sum(row["traded_value"] is not None for row in tail)
    identity_candidates = [{
        "security_id": row["security_id"], "ticker": row["ticker"],
        "exchange": row["exchange"], "sector": row["sector"],
        "listing_date": row["listing_date"], "company_name": None,
        "identity_status": "provisional_verified_for_pilot",
        "canonical_eligible": False,
        "blocking_fields": ["company_name", "historical_exchange_interval_evidence"],
    } for row in prepared["universe"]]
    blockers = [
        "securities.company_name is absent from the frozen reviewed universe; no placeholder was fabricated",
        "current ticker/exchange metadata does not prove complete historical identity intervals",
    ]
    manifest = {
        "run_id": run_id_out, "source_run_id": run_id,
        "status": "MAPPED_NOT_PROMOTED", "mapping_status": "PASS",
        "canonical_promotion_status": "BLOCKED", "feature_stage_ready": False,
        "network_requests": 0, "started_at": now(), "finished_at": now(),
        "schema_version": "1.4.0", "synthetic": False,
        "config_hash": prepared["config_hash"], "universe_hash": prepared["universe_hash"],
        "source_gate_hash": prepared["source_gate_hash"], "qc_policy_hash": policy_hash,
        "qc_assessment_hash": digest(assessment_path.read_bytes()),
        "source_manifest_hash": digest((source_dir / "manifest.json").read_bytes()),
        "pilot_gate_hash": digest((assessment_path.parent / "gate.json").read_bytes()),
        "mapping_semantics_hash": digest(semantics_path.read_bytes()),
        "availability_policy": "RESEARCH_ASSUMPTION_MARKET_CLOSE_PLUS_120_MINUTES",
        "mapping_policy": {
            "kbs_vendor_adjusted_close": "adj_close",
            "kbs_vendor_adjusted_ohl": "SOURCE_QUALIFIED_ONLY_NOT_CANONICAL_RAW_OHL",
            "kbs_volume": "volume",
            "kbs_va": "UNRESOLVED_NOT_PROMOTED",
            "cafef_traded_value": "traded_value_WHEN_EXACT_DATE_AVAILABLE",
            "cafef_price_bands": "NOT_MERGED_WITH_VENDOR_ADJUSTED_PRICE_BASIS",
            "missing": "PRESERVE_NULL_NO_FILL",
        },
        "counts": {"selected_symbols": len(universe), "prices_daily": len(prices),
                   "benchmark_daily": len(benchmark), "trading_calendar": len(calendar),
                   "identity_candidates": len(identity_candidates),
                   "qc_rows_excluded": len(findings),
                   "prices_with_traded_value": sum(row["traded_value"] is not None for row in prices)},
        "checks": {
            "qc_assessment_pass": pilot_gate["status"] == "PASS",
            "exact_hash_policy_replayed": used == set(rules),
            "standard_market_schemas_valid": True,
            "unique_price_keys": len(prices) == len({
                (row["security_id"], row["trade_date"]) for row in prices}),
            "calendar_relation_valid": True,
            "raw_ohl_not_fabricated": all(row["raw_close"] is None for row in prices),
            "vendor_adjusted_close_preserved": all(row["adj_close"] is not None for row in prices),
            "positive_volume_bars_marked_normal": all(
                row["trading_status"] == "normal" for row in prices),
            "missing_preserved": True, "network_zero": True,
            "all_symbols_have_latest_21_traded_value": all(value == 21 for value in latest_21.values()),
            "canonical_securities_valid": False,
        },
        "latest_21_traded_value_coverage": latest_21,
        "blocking_reasons": blockers,
        "financial": {"pit_status": "PIT_UNRESOLVED", "features_allowed": False},
        "raw_artifact_hashes": raw_hashes,
    }
    write_rows(target / "candidates" / "prices_daily.jsonl", prices)
    write_rows(target / "candidates" / "benchmark_daily.jsonl", benchmark)
    write_rows(target / "candidates" / "trading_calendar.jsonl", calendar)
    write_rows(target / "candidates" / "identity_candidates.jsonl", identity_candidates)
    write_rows(target / "lineage" / "market.jsonl", lineage)
    manifest["artifacts"] = {
        path.relative_to(target).as_posix(): digest(path.read_bytes())
        for path in sorted(target.rglob("*.jsonl"))
    }
    write_json(target / "manifest.json", manifest)
    return target, manifest
