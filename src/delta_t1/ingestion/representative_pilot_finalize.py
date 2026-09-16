"""Offline, immutable QC replay for a completed real representative pilot."""
from datetime import date
import json
from pathlib import Path

from ..artifact_ids import new_artifact_id
from ..io import digest, encoded, read_json, write_json
from .planning import representative_pilot_report
from .representative_pilot import (
    FINANCIAL_PIT_UNRESOLVED, OFFICIAL_MARKET_SOURCES, REQUIRED_EXCHANGES,
    _valid_kbs, load_readiness, utc_now,
)
from .sources.cafef import (
    classify_cafef_page_row, map_trade_history_row, price_band_row_status,
)
from .sources.vnstock import classify_volume_semantics, map_kbs_wire_ohlcv_row


def load_qc_policy(path, source_run_id):
    policy_path = Path(path).resolve()
    policy = read_json(policy_path)
    if (policy.get("policy_id") != "REPRESENTATIVE_PILOT_QC_V1"
            or policy.get("source_run_id") != source_run_id
            or policy.get("action") != "EXCLUDE_EXACT_RAW_HASH_ONLY"):
        raise ValueError("QC policy identity/action does not match the source run")
    coverage = policy.get("coverage_policy", {})
    if coverage != {
        "primary_ohlcv": {"provider": "kbs", "minimum_years": 5, "required": True},
        "reference_limits_value": {
            "provider": "cafef", "partial_source_qualified_allowed": True,
            "required_nonempty": True,
        },
    }:
        raise ValueError("QC coverage policy must keep KBS primary and CafeF source-qualified")
    rules = {}
    for item in policy.get("rules", []):
        if (not isinstance(item, list) or len(item) != 5
                or item[0] not in ("kbs", "cafef")
                or len(item[3]) != 64
                or any(char not in "0123456789abcdef" for char in item[3])):
            raise ValueError("QC policy contains an invalid exact-hash rule")
        expected_classification = (
            "PROVIDER_OHLC_INVARIANT_VIOLATION" if item[0] == "kbs"
            else "PROVIDER_PRICE_BAND_INVARIANT_VIOLATION")
        if item[4] != expected_classification:
            raise ValueError("QC policy classification does not match provider invariant")
        key = tuple(item[:4])
        if key in rules:
            raise ValueError("QC policy contains a duplicate exact-hash rule")
        rules[key] = item[4]
    if not rules:
        raise ValueError("QC policy must contain reviewed exact-hash rules")
    return policy_path, policy, rules


def _source_run(root, run_id, prepared):
    directory = root / "data" / "raw" / "representative_pilot" / run_id
    header = read_json(directory / "run.json")
    manifest = read_json(directory / "manifest.json")
    plan = read_json(directory / "job_plan.json")
    if (header.get("run_id") != run_id or manifest.get("run_id") != run_id
            or header.get("mode") != "REAL_EXECUTION"
            or manifest.get("mode") != "REAL_EXECUTION"):
        raise ValueError("offline QC requires one immutable REAL_EXECUTION run")
    if manifest.get("status") not in ("COMPLETE", "FAILED_GATE"):
        raise ValueError("source run acquisition is not complete")
    if digest(encoded(plan)) != header.get("job_plan_hash"):
        raise ValueError("source job_plan.json integrity mismatch")
    expected = {job["id"]: job for job in plan.get("jobs", [])}
    stored = manifest.get("jobs", {})
    if set(stored) != set(expected):
        raise ValueError("source manifest job set mismatch")
    if any(state.get("job") != expected[job_id] or state.get("status") != "COMPLETE"
           for job_id, state in stored.items()):
        raise ValueError("source manifest job definition/status mismatch")
    for field, expected_hash in (
        ("config_hash", prepared["config_hash"]),
        ("universe_hash", prepared["universe_hash"]),
        ("source_gate_hash", prepared["source_gate_hash"]),
    ):
        if header.get(field) != expected_hash:
            raise ValueError(f"source run {field} mismatch")
    return directory, header, manifest, plan


def _raw_payload(root, run_id, artifact):
    raw_path = artifact.get("raw_path")
    provider = artifact.get("provider")
    expected_prefix = f"data/raw/{provider}/{run_id}/"
    if not isinstance(raw_path, str) or not raw_path.startswith(expected_prefix):
        raise ValueError("provider artifact path escapes its immutable run")
    path = (root / raw_path).resolve()
    expected_directory = (root / expected_prefix).resolve()
    if not path.is_relative_to(expected_directory):
        raise ValueError("provider artifact path escapes its immutable run")
    if not path.is_file() or digest(path.read_bytes()) != artifact.get("sha256"):
        raise ValueError(f"provider artifact checksum mismatch: {raw_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _rule(rules, used, provider, symbol, trade_date, raw_row):
    key = (provider, symbol, trade_date, digest(encoded(raw_row)))
    classification = rules.get(key)
    if classification:
        used.add(key)
    return classification


def _years(rows):
    dates = {row["trade_date"] for row in rows}
    if not dates:
        return 0.0
    return (date.fromisoformat(max(dates)) - date.fromisoformat(min(dates))).days / 365.2425


def finalize_real_run(config_path, gate_report_path, policy_path, run_id, *, root):
    """Re-evaluate checksummed raw artifacts without network or raw mutation."""
    root = Path(root).resolve()
    prepared = load_readiness(config_path, gate_report_path, root=root)
    source_dir, header, source, plan = _source_run(root, run_id, prepared)
    policy_path, policy, rules = load_qc_policy(policy_path, run_id)
    universe = {row["ticker"]: row for row in prepared["universe"]}
    kbs_rows, cafef_rows, coverage = {}, {}, {}
    hashes, used, findings = {}, set(), []

    for state in source["jobs"].values():
        job = state["job"]
        for artifact in state["artifacts"]:
            payload = _raw_payload(root, run_id, artifact)
            hashes[artifact["raw_path"]] = artifact["sha256"]
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
                        findings.append({"provider": "kbs", "symbol": job["symbol"],
                                         "trade_date": mapped["trade_date"],
                                         "classification": classification,
                                         "action": "EXCLUDE_ROW"})
                        continue
                    kbs_rows.setdefault(job["symbol"], []).append(mapped)
            elif job["kind"] == "reference_limits_value":
                if artifact.get("coverage"):
                    coverage[job["symbol"]] = artifact["coverage"]
                page = artifact.get("request", {}).get("page_index")
                if not isinstance(page, int) or page < 1:
                    raise ValueError("CafeF replay artifact lacks page_index")
                for row_index, raw in enumerate(payload["Data"]):
                    if classify_cafef_page_row(
                            raw.get("TradeDate"), page=page,
                            row_index=row_index) == "CURRENT_SNAPSHOT":
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
                        findings.append({"provider": "cafef", "symbol": job["symbol"],
                                         "trade_date": mapped["trade_date"],
                                         "classification": classification,
                                         "action": "EXCLUDE_ROW"})
                        continue
                    cafef_rows.setdefault(job["symbol"], []).append(mapped)

    if used != set(rules):
        missing = sorted(set(rules) - used)
        raise ValueError(f"QC policy rules do not exactly match source evidence: {missing[:3]}")

    symbols, failed, conflicts = {}, [], 0
    for symbol, meta in universe.items():
        krows = sorted(kbs_rows.get(symbol, []), key=lambda row: row["trade_date"])
        crows = sorted(cafef_rows.get(symbol, []), key=lambda row: row["trade_date"])
        kdates = {row["trade_date"] for row in krows}
        cdates = {row["trade_date"] for row in crows}
        duplicates = len(krows) - len(kdates) + len(crows) - len(cdates)
        years = _years(krows)
        volume = classify_volume_semantics(krows, crows)
        conflicts += int(volume["classification"] == "UNRESOLVED")
        qc = (_valid_kbs(krows) and bool(crows) and duplicates == 0
              and years >= policy["coverage_policy"]["primary_ohlcv"]["minimum_years"]
              and volume["market_collection_safe"])
        if not qc:
            failed.append(symbol)
        symbols[symbol] = {
            "symbol": symbol, "exchange": meta["exchange"], "sector": meta["sector"],
            "observed_min_date": min(kdates) if kdates else None,
            "observed_max_date": max(kdates) if kdates else None,
            "kbs_row_count": len(krows), "cafef_row_count": len(crows),
            "usable_5y": years >= 5, "usable_3y_for_clustering": years >= 3,
            "reference_only": meta["reference_only"] or years < 3,
            "invalid_rows_excluded": sum(
                item["symbol"] == symbol for item in findings),
            "reference_source_coverage": coverage.get(symbol, {"status": "UNKNOWN"}),
            "volume_semantic": volume["classification"],
            "qc_status": "PASS" if qc else "FAIL",
        }

    benchmark = sorted(kbs_rows.get("VNINDEX", []), key=lambda row: row["trade_date"])
    aggregate = {
        "selected_symbols": len(symbols),
        "usable_5y_symbols": sum(item["usable_5y"] for item in symbols.values()),
        "usable_3y_clustering_symbols": sum(
            item["usable_3y_for_clustering"] and not item["reference_only"]
            for item in symbols.values()),
        "reference_only_symbols": sorted(
            symbol for symbol, item in symbols.items() if item["reference_only"]),
        "failed_symbols": failed,
        "quarantined_rows": len(findings),
        "provider_conflicts": conflicts,
        "reference_source_partial_symbols": sorted(
            symbol for symbol, item in symbols.items()
            if item["reference_source_coverage"].get("status") == "PARTIAL_SOURCE_EXHAUSTED"),
        "exchange_coverage": sorted({item["exchange"] for item in symbols.values()}),
        "sector_coverage": sorted({item["sector"] for item in symbols.values()}),
    }
    threshold = prepared["config"]["coverage_thresholds"]
    market_qc = (
        len(failed) <= threshold["maximum_failed_symbols"]
        and aggregate["usable_5y_symbols"] / len(symbols)
        >= threshold["minimum_usable_five_year_ratio"]
        and _valid_kbs(benchmark, index=True)
    )
    policy_hash = digest(policy_path.read_bytes())
    evidence = {
        "synthetic": False, "run_mode": "REAL_EXECUTION",
        "qc_evaluation_mode": "OFFLINE_IMMUTABLE_REPLAY",
        "source_run_id": run_id, "source_run_status": source["status"],
        "qc_policy_hash": policy_hash,
        "symbol_count": len(symbols), "history_years": plan["history_years"],
        "representative_exchanges": set(aggregate["exchange_coverage"]) == REQUIRED_EXCHANGES,
        "representative_sectors_or_documented_limit": prepared["universe_summary"][
            "representative_sectors_or_documented_limit"],
        "source_routing_matches_smoke": plan["source_routing"] == OFFICIAL_MARKET_SOURCES,
        "market_qc_passed": market_qc,
        "price_basis_safe": True, "reconciliation_policy_safe": True,
        "provenance_complete": all(
            artifact.get("provider") and artifact.get("acquisition_client")
            for state in source["jobs"].values() for artifact in state["artifacts"]),
        "invalid_rows_fail_closed": used == set(rules),
        "source_qualified_conflicts": True,
        "missing_values_preserved": True, "no_price_forward_fill": True,
        "no_current_shares_backfill": True,
        "financial_pit_status": FINANCIAL_PIT_UNRESOLVED,
        "financial_features_allowed": False,
        "provider_artifact_hashes": hashes,
        "evidence_hashes": {
            "pilot-config": prepared["config_hash"],
            "pilot-universe": prepared["universe_hash"],
            "source-gate": prepared["source_gate_hash"],
            "source-manifest": digest((source_dir / "manifest.json").read_bytes()),
            "qc-policy": policy_hash,
        } | hashes,
    }
    gate = representative_pilot_report(evidence, prepared["source_gate"])
    assessment_id = new_artifact_id("representative-pilot-qc")
    output = root / "data" / "derived" / "representative_pilot_qc" / assessment_id
    assessment = {
        "assessment_id": assessment_id, "created_at": utc_now(),
        "mode": "OFFLINE_IMMUTABLE_REPLAY", "network_requests": 0,
        "source_run_id": run_id, "source_run_status": source["status"],
        "policy_id": policy["policy_id"], "policy_hash": policy_hash,
        "source_manifest_hash": evidence["evidence_hashes"]["source-manifest"],
        "config_hash": prepared["config_hash"], "universe_hash": prepared["universe_hash"],
        "source_gate_hash": prepared["source_gate_hash"],
        "coverage_policy": policy["coverage_policy"],
        "aggregate": aggregate,
        "benchmark": {"symbol": "VNINDEX", "rows": len(benchmark),
                      "valid": _valid_kbs(benchmark, index=True)},
        "financial": {"pit_status": FINANCIAL_PIT_UNRESOLVED,
                      "features_allowed": False},
        "quarantine_findings": findings, "symbols": symbols,
        "gate_status": gate["status"],
    }
    write_json(output / "assessment.json", assessment)
    write_json(output / "gate.json", gate)
    return output, assessment, gate
