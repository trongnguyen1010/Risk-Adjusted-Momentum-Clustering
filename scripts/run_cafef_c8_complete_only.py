"""Validate or execute the heavy complete-only C8 CafeF market audit."""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from delta_t1.features.market import build_features, latest_completed_snapshot_rows
from delta_t1.ingestion.cafef_c8 import *
from delta_t1.ingestion.cafef_expansion import (
    page_rows, read_json as read_expansion_json, sha256_bytes as expansion_sha256_bytes,
    validate_git_state, validate_handoff_commits, validate_handoff_set,
)
from delta_t1.ingestion.sources.cafef import classify_cafef_page_row
from verify_cafef_expansion_handoffs import verify_archive

C5 = ROOT / "artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2"
C4 = ROOT / "artifacts/cafef_primary/cafef-tradehistory-500-evaluation-v1"
C7 = ROOT / "artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1"
INCOMING = ROOT / "data/handoffs/cafef_expansion_v1/incoming"
EXPANSION_CONFIG = ROOT / "configs/data/cafef_expansion_v1"
OUT = ROOT / f"artifacts/cafef_primary/{C8_ARTIFACT_ID}"
_META = re.compile(r"^raw/([^/]+)/page-(\d+)\.metadata\.json$")


def validate_contract() -> dict:
    contract = read_json(ROOT / "configs/data/cafef_c8_complete_only_v1.json")
    expected = {
        "artifact_id": C8_ARTIFACT_ID, "execution_version": C8_EXECUTION_VERSION,
        "baseline_candidate_count": 500, "complete_expansion_count": 452,
        "deferred_expansion_count": 148, "combined_candidate_count": 952,
        "deferred_decision": DEFERRED_DECISION, "comparison_snapshot": SNAPSHOT_DATE,
        "adjustment_basis": "vendor_adjusted", "minimum_history_years": 3,
        "supplemental_acquisition_allowed": False, "clustering_or_backtest_allowed": False,
    }
    mismatches = [key for key, value in expected.items() if contract.get(key) != value]
    if mismatches or tuple(contract.get("required_features", [])) != REQUIRED_FEATURES:
        raise ValueError("C8 contract mismatch: " + ",".join(mismatches or ["required_features"]))
    identity_path = ROOT / contract.get("identity_review", "")
    if not identity_path.is_file():
        raise ValueError("active identity review file missing")
    aliases = load_identity_review(identity_path)
    if sha256_bytes(canonical_bytes(sorted(aliases))) != contract.get("identity_review_aliases_sha256"):
        raise ValueError("active identity review semantic hash mismatch")
    return contract


def verify_five_handoffs(scope: dict) -> list[Path]:
    paths = sorted(INCOMING.glob("*.zip"))
    if len(paths) != 5:
        raise ValueError(f"expected five immutable handoff ZIPs, found {len(paths)}")
    index = read_expansion_json(EXPANSION_CONFIG / "index.json")
    universe = read_expansion_json(EXPANSION_CONFIG / "universe.json")
    contract = read_expansion_json(EXPANSION_CONFIG / "crawl_contract.json")
    verified = [verify_archive(path, index, universe, contract) for path in paths]
    c7_report = read_json(C7 / "verification_report.json")
    validate_handoff_commits([item[1] for item in verified], c7_report["expected_commit"])
    reserve = {row["ticker"] for row in read_csv(EXPANSION_CONFIG / "reserve.csv")}
    validate_handoff_set([item[0] for item in verified], index, universe, reserve)
    expected_hashes = {row["source_zip"]: row["source_zip_sha256"] for row in scope["inventory"]}
    for path in paths:
        if sha256_file(path) != expected_hashes[path.name]:
            raise ValueError(f"C7 provenance hash mismatch: {path.name}")
    return paths


def validate_only(expected_commit: str) -> dict:
    validate_git_state(ROOT, expected_commit)
    validate_contract()
    verify_manifest_outputs(C5)
    c5_manifest = read_json(C5 / "manifest.json")
    if c5_manifest["parent_c4_manifest_hash"] != sha256_file(C4 / "manifest.json"):
        raise ValueError("C5 parent C4 manifest hash mismatch")
    scope = build_scope(ROOT)
    verify_five_handoffs(scope)
    result = {
        "readiness": "PASS", "network_requests": 0,
        "baseline_candidates": len(scope["baseline"]),
        "complete_expansion": len(scope["expansion"]),
        "combined_candidates": len(scope["candidates"]),
        "deferred_expansion": len(scope["deferred"]),
        "deferred_breakdown": dict(Counter(row["c7_acquisition_status"] for row in scope["deferred"])),
        "heavy_run_executed": False,
    }
    return result


def expansion_observations(paths: list[Path], scope: dict) -> tuple[list[dict], list[dict], list[dict]]:
    complete = {row["ticker"]: row for row in scope["expansion"]}
    observations, normalized, quarantine = [], [], []
    for path in paths:
        zip_sha256 = sha256_file(path)
        with zipfile.ZipFile(path) as archive:
            assignment = json.loads(archive.read("assignment.json"))
            manifest = json.loads(archive.read("handoff_manifest.json"))
            for name in sorted(archive.namelist()):
                match = _META.match(name)
                if not match or match.group(1) not in complete:
                    continue
                ticker, page_text = match.groups()
                page = int(page_text)
                raw_name = name.replace(".metadata.json", ".json")
                metadata = json.loads(archive.read(name))
                body = archive.read(raw_name)
                if expansion_sha256_bytes(body) != metadata.get("sha256"):
                    raise ValueError(f"raw checksum mismatch in {path.name}: {raw_name}")
                security = complete[ticker]
                for position, raw in enumerate(page_rows(body)):
                    if classify_cafef_page_row(raw.get("TradeDate"), page, position) == "CURRENT_SNAPSHOT":
                        continue
                    provenance = {
                        "worker_id": assignment["worker_id"], "assignment_id": assignment["assignment_id"],
                        "handoff_run_id": manifest["run_id"], "source_zip": path.name,
                        "source_zip_sha256": zip_sha256, "raw_path": raw_name,
                        "raw_sha256": metadata["sha256"], "fetched_at": metadata.get("fetched_at"),
                    }
                    try:
                        mapped = map_trade_history_row(raw, ticker, security["exchange"])
                        mapped.update(security_id=security["security_id"], ticker=ticker,
                                      exchange=security["exchange"])
                        quality = row_quality(mapped)
                        normalized.append({
                            "security_id": security["security_id"], "ticker": ticker,
                            "trade_date": mapped["trade_date"], "classification": quality,
                            "post_snapshot": mapped["trade_date"] > SNAPSHOT_DATE, **provenance,
                        })
                        if quality != "OBSERVED_VALID":
                            quarantine.append({
                                "security_id": security["security_id"], "ticker": ticker,
                                "trade_date": mapped["trade_date"], "classification": quality,
                                "raw_path": raw_name, "source_zip": path.name,
                            })
                            continue
                        observations.append(canonical_market_row(mapped, provenance))
                    except Exception as exc:
                        quarantine.append({
                            "security_id": security["security_id"], "ticker": ticker,
                            "trade_date": "", "classification": "INVALID_PROVIDER_ROW",
                            "error_type": type(exc).__name__, "raw_path": raw_name,
                            "source_zip": path.name,
                        })
    return observations, normalized, quarantine


def expansion_security_rows(scope: dict) -> list[dict]:
    rows = []
    for item in scope["expansion"]:
        rows.append({
            "security_id": item["security_id"], "ticker": item["ticker"],
            "exchange": item["exchange"], "company_name": item["company_name"],
            "currency": "VND", "price_unit": "VND", "industry": None, "sector": None,
            "listing_date": None, "delisting_date": None, "valid_from": item["audit_start"],
            "valid_to": None, "identity_status": "provisional",
            "source": "C7_COMPLETE_CURRENT_LISTING_PLUS_PROVIDER_BOUNDARY",
            "available_at": "2026-09-25T00:00:00+07:00",
            "fetched_at": None, "data_version": C8_DATA_VERSION,
            "boundary_basis": item["boundary_basis"],
        })
    return rows


def execute(expected_commit: str) -> dict:
    validate_git_state(ROOT, expected_commit)
    validate_contract()
    if OUT.exists():
        raise ValueError(f"immutable C8 output already exists: {OUT}")
    scope = build_scope(ROOT)
    paths = verify_five_handoffs(scope)
    verify_manifest_outputs(C5)
    c4_manifest = read_json(C4 / "manifest.json")
    c5_manifest = read_json(C5 / "manifest.json")
    if c5_manifest["parent_c4_manifest_hash"] != sha256_file(C4 / "manifest.json"):
        raise ValueError("C5 parent C4 manifest hash mismatch")
    for name in ("quarantine.jsonl", "conflicting_observations.csv"):
        if sha256_file(C4 / name) != c4_manifest["outputs"][name]:
            raise ValueError(f"C4 detailed evidence hash mismatch: {name}")
    OUT.mkdir(parents=True)
    (OUT / "canonical").mkdir()

    write_csv(OUT / "candidate_universe.csv", scope["candidates"])
    write_csv(OUT / "deferred_expansion.csv", scope["deferred"])
    write_csv(OUT / "expansion_attrition.csv", attrition_rows(scope))

    observations, normalized, quarantine = expansion_observations(paths, scope)
    expansion_clean, conflicts = resolve_observations(observations)
    baseline_invalid = []
    for row in iter_jsonl(C4 / "quarantine.jsonl"):
        if row.get("security_id") and row.get("trade_date"):
            baseline_invalid.append(row)
    baseline_conflicts = read_csv(C5 / "conflict_review.csv")
    invalid_keys = {(row["security_id"], row["trade_date"])
                    for row in quarantine + baseline_invalid
                    if row.get("trade_date") and row["trade_date"] <= SNAPSHOT_DATE}
    conflict_keys = {(row["security_id"], row["trade_date"])
                     for row in conflicts + baseline_conflicts if row.get("trade_date") <= SNAPSHOT_DATE}
    post_snapshot = [row for row in expansion_clean if row["trade_date"] > SNAPSHOT_DATE]
    expansion_snapshot = apply_snapshot_cutoff(expansion_clean)

    baseline_ids = {row["security_id"] for row in scope["baseline"]}
    baseline_prices = []
    for row in iter_jsonl(C5 / "clean/prices_daily.jsonl"):
        if row["security_id"] in baseline_ids and row["trade_date"] <= SNAPSHOT_DATE:
            item = dict(row)
            item["c8_source_stage"] = "C5_BASELINE_RETAINED"
            baseline_prices.append(item)
    prices = sorted(baseline_prices + expansion_snapshot,
                    key=lambda row: (row["security_id"], row["trade_date"]))
    calendar = [row for row in iter_jsonl(C5 / "clean/trading_calendar.jsonl")
                if row["trade_date"] <= SNAPSHOT_DATE]
    benchmark = [row for row in iter_jsonl(C5 / "clean/benchmark_daily.jsonl")
                 if row["trade_date"] <= SNAPSHOT_DATE]
    securities = scope["baseline_intervals"] + expansion_security_rows(scope)
    write_jsonl(OUT / "canonical/prices_daily.jsonl", prices)
    write_jsonl(OUT / "canonical/securities.jsonl", securities)
    write_jsonl(OUT / "canonical/trading_calendar.jsonl", calendar)
    write_jsonl(OUT / "canonical/benchmark_daily.jsonl", benchmark)
    write_jsonl(OUT / "canonical/normalized_expansion.jsonl", normalized)
    write_jsonl(OUT / "canonical/post_snapshot_provider_observations.jsonl", post_snapshot)

    valid_keys = {(row["security_id"], row["trade_date"]) for row in prices}
    zero_keys = {(row["security_id"], row["trade_date"]) for row in prices
                 if row.get("trading_activity_status") == "OBSERVED_ZERO_VOLUME"}
    full_audit, latest_audit = build_session_audits(
        scope["candidates"], calendar, valid_keys, conflict_keys, invalid_keys, zero_keys,
    )
    write_csv(OUT / "full_history_session_audit.csv", full_audit)
    write_csv(OUT / "latest253_session_audit.csv", latest_audit)

    config = read_json(ROOT / "configs/features/market.example.json")
    config.update(feature_set="delta_market_1.6.0", readiness_policy="MARKET_FEATURE_READINESS_V2",
                  accepted_adjustments=["vendor_adjusted"], minimum_history_years=3)
    features = build_features({
        "securities": securities, "prices_daily": prices,
        "trading_calendar": calendar, "benchmark_daily": benchmark,
    }, config, C8_DATA_VERSION)
    write_jsonl(OUT / "canonical/feature_snapshots.jsonl", features)
    actual_snapshot, latest = latest_completed_snapshot_rows(features, "2026-09-15")
    if actual_snapshot != SNAPSHOT_DATE:
        raise ValueError(f"feature snapshot mismatch: {actual_snapshot}")
    snapshot_rows = {row["security_id"]: row for row in prices if row["trade_date"] == SNAPSHOT_DATE}
    readiness = readiness_rows(scope["candidates"], latest, full_audit, latest_audit, snapshot_rows)
    write_csv(OUT / "feature_readiness.csv", readiness)

    activity = Counter(row["trading_activity_status"] if row["trading_activity_status"] in
                       {"ACTIVE", "OBSERVED_ZERO_VOLUME"} else "UNKNOWN" for row in readiness)
    tradability = [{"status": status, "security_count": activity[status]}
                   for status in ("ACTIVE", "OBSERVED_ZERO_VOLUME", "UNKNOWN")]
    write_csv(OUT / "tradability_summary.csv", tradability)
    all_conflicts = conflicts + [{
        "security_id": row["security_id"], "ticker": row["ticker"],
        "trade_date": row["trade_date"], "classification": row["classification"],
        "observation_count": 2,
    } for row in baseline_conflicts]
    write_csv(OUT / "conflict_summary.csv", all_conflicts,
              ["security_id", "ticker", "trade_date", "classification", "observation_count"])
    quarantine_counts = Counter(row.get("classification", row.get("reason", "OTHER"))
                                for row in quarantine + baseline_invalid)
    quarantine_summary = [{"classification": key, "row_count": value}
                          for key, value in sorted(quarantine_counts.items())]
    write_csv(OUT / "quarantine_summary.csv", quarantine_summary,
              ["classification", "row_count"])

    normalization = {
        "expansion_complete_input": 452, "normalized_provider_rows": len(normalized),
        "valid_expansion_observations_through_snapshot": len(expansion_snapshot),
        "post_snapshot_observations_preserved_not_used": len(post_snapshot),
        "conflicting_observation_keys": len(all_conflicts),
        "quarantined_rows": len(quarantine) + len(baseline_invalid),
        "price_mapping": "AdjustPrice*1000 -> adj_close",
        "adjustment_basis": "vendor_adjusted", "imputation": "NONE",
        "calendar_audit_policy": calendar_audit_policy(calendar),
    }
    write_json(OUT / "normalization_summary.json", normalization)
    full_status = Counter(row["full_history_status"] for row in full_audit)
    gate = data_quality_gate(readiness, latest_audit, full_audit)
    quality = {
        "stage": "C8", "execution_integrity": "PASS",
        "data_quality_gate": gate,
        "comparison_snapshot": SNAPSHOT_DATE, "baseline_candidate_count": 500,
        "expansion_complete_count": 452, "combined_candidate_count": 952,
        "deferred_expansion_count": 148,
        "full_history_status": {status: full_status[status] for status in
                                ("COMPLETE", "COMPLETE_WITHIN_OBSERVED_BOUNDARY",
                                 "UNCERTAIN_BOUNDARY", "INCOMPLETE")},
        "observed_window_complete": sum(row["observed_window_complete"] for row in full_audit),
        "full_history_complete": full_status["COMPLETE"],
        "full_history_not_complete": len(full_audit) - full_status["COMPLETE"],
        "latest253_complete": sum(row["latest253_complete"] for row in latest_audit),
        "latest253_incomplete": sum(not row["latest253_complete"] for row in latest_audit),
        "feature_complete": sum(row["feature_complete"] for row in readiness),
        "market_feature_ready_v2": sum(row["market_feature_ready_v2"] for row in readiness),
        "tradability": {status: activity[status]
                        for status in ("ACTIVE", "OBSERVED_ZERO_VOLUME", "UNKNOWN")},
        "historical_identity_ready": sum(row["historical_identity_ready"] for row in readiness),
        "research_ready": sum(row["research_ready"] for row in readiness),
        "network_requests": 0, "supplemental_acquisition_executed": False,
    }
    write_json(OUT / "quality_summary.json", quality)
    methodology = """# C8 complete-only methodology summary

C8 giữ 500 baseline C5 và chỉ thêm 452 expansion có acquisition `COMPLETE`. Toàn bộ 148 mã chưa complete được ghi `DEFERRED_EXPANSION_ACQUISITION`, không được diễn giải thành provider gap hay missing session.

Snapshot feature là 2026-08-28. Row provider muộn hơn được giữ làm evidence nhưng bị loại khỏi audit/readiness. `AdjustPrice × 1000` là `adj_close` với `vendor_adjusted`; null activity không đổi thành zero, zero provider là observation thật, và không có fill/interpolation/timeline compression. Calendar hiện là `kbs_observed_session_union`, không phải official authoritative calendar; vì vậy absence fail-closed thành `CALENDAR_UNCERTAIN`, không phải confirmed provider missing. Full-history báo riêng observed-window completeness và target-period status; provider boundary không chứng minh listing date. Full-history và latest-253 là hai audit độc lập. Market readiness, tradability, historical identity và research readiness được báo riêng.
"""
    (OUT / "methodology_summary.md").write_text(methodology, encoding="utf-8", newline="\n")
    outputs = [path for path in OUT.rglob("*") if path.is_file() and path.name != "manifest.json"]
    manifest = {
        "artifact_id": C8_ARTIFACT_ID, "execution_version": C8_EXECUTION_VERSION,
        "git_commit": expected_commit, "comparison_snapshot": SNAPSHOT_DATE,
        "c5_manifest_sha256": sha256_file(C5 / "manifest.json"),
        "c7_manifest_sha256": sha256_file(C7 / "manifest.json"),
        "identity_review_sha256": sha256_file(ROOT / "configs/data/identity_review_v1.json"),
        "source_zip_sha256": {path.name: sha256_file(path) for path in paths},
        "outputs": {str(path.relative_to(OUT)).replace("\\", "/"): sha256_file(path)
                    for path in sorted(outputs)},
    }
    write_json(OUT / "manifest.json", manifest)
    return quality


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-commit", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    result = validate_only(args.expected_commit) if args.validate_only else execute(args.expected_commit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
