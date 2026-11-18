"""Offline verification and compact reporting for the immutable C8 artifact."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path


C8_ARTIFACT = "artifacts/cafef_primary/cafef-c8-complete-only-v1"
VERIFY_ARTIFACT = "artifacts/cafef_primary/cafef-c8-verify-v1"
EXPECTED_C8_COMMIT = "d60c8cba49c90b3b36c346dfea463a1e4f659ee1"
SNAPSHOT_DATE = "2026-08-28"
EXPECTED_HEADLINE = {
    "candidate_count": 952,
    "baseline_candidate_count": 500,
    "expansion_complete_count": 452,
    "deferred_expansion_count": 148,
    "feature_complete": 922,
    "market_feature_ready_v2": 905,
    "latest253_complete": 922,
    "latest253_incomplete": 30,
    "historical_identity_ready": 0,
    "research_ready": 0,
}
LATEST_BLOCKER_FIELDS = (
    ("CALENDAR_UNCERTAIN", "calendar_uncertain_253"),
    ("MISSING_ON_TRADEHISTORYNEW", "missing_sessions_253"),
    ("INVALID_PROVIDER_ROW", "invalid_sessions_253"),
    ("CONFLICTING_PROVIDER_OBSERVATION", "conflicting_sessions_253"),
    ("IDENTITY_OR_PROVIDER_BOUNDARY", "boundary_sessions_253"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def as_bool(value) -> bool:
    return value is True or str(value).lower() == "true"


def optional_bool(value):
    return "" if value in (None, "") else as_bool(value)


def as_int(value) -> int:
    return int(value or 0)


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_generated_manifest(output: Path) -> int:
    manifest = read_json(output / "manifest.json")
    expected_paths = set(manifest.get("outputs", {}))
    actual_paths = {path.name for path in output.iterdir()
                    if path.is_file() and path.name != "manifest.json"}
    if expected_paths != actual_paths:
        raise ValueError("verification artifact manifest file set mismatch")
    mismatches = [name for name, expected in manifest["outputs"].items()
                  if sha256_file(output / name) != expected]
    if mismatches:
        raise ValueError(f"verification artifact output hash mismatch: {mismatches}")
    return len(expected_paths)


def indexed(rows: list[dict], label: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        sid = row["security_id"]
        if sid in result:
            raise ValueError(f"duplicate security_id in {label}: {sid}")
        result[sid] = row
    return result


def verify_parent_integrity(root: Path) -> dict:
    c8 = root / C8_ARTIFACT
    manifest_path = c8 / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("C8 manifest.json missing")
    manifest = read_json(manifest_path)
    if manifest.get("git_commit") != EXPECTED_C8_COMMIT:
        raise ValueError("C8 manifest git_commit mismatch")

    output_checks = []
    for relative, expected in sorted(manifest.get("outputs", {}).items()):
        path = c8 / relative
        actual = sha256_file(path) if path.is_file() else None
        output_checks.append({
            "path": relative, "expected_sha256": expected,
            "actual_sha256": actual, "match": actual == expected,
        })
    if not output_checks or not all(row["match"] for row in output_checks):
        bad = [row["path"] for row in output_checks if not row["match"]]
        raise ValueError(f"C8 output hash mismatch: {bad}")

    references = (
        ("C5_MANIFEST", "c5_manifest_sha256",
         root / "artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2/manifest.json"),
        ("C7_MANIFEST", "c7_manifest_sha256",
         root / "artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1/manifest.json"),
        ("IDENTITY_REVIEW", "identity_review_sha256",
         root / "configs/data/identity_review_v1.json"),
    )
    reference_checks = []
    for label, key, path in references:
        actual = sha256_file(path) if path.is_file() else None
        expected = manifest.get(key)
        reference_checks.append({
            "reference": label, "path": str(path.relative_to(root)).replace("\\", "/"),
            "expected_sha256": expected, "actual_sha256": actual,
            "match": actual == expected,
        })
    if not all(row["match"] for row in reference_checks):
        raise ValueError("C8 parent reference hash mismatch")

    incoming = root / "data/handoffs/cafef_expansion_v1/incoming"
    expected_zips = manifest.get("source_zip_sha256", {})
    zip_checks = []
    for name, expected in sorted(expected_zips.items()):
        path = incoming / name
        actual = sha256_file(path) if path.is_file() else None
        zip_checks.append({
            "zip": name, "expected_sha256": expected,
            "actual_sha256": actual, "match": actual == expected,
        })
    if len(zip_checks) != 5 or not all(row["match"] for row in zip_checks):
        raise ValueError("five immutable source ZIP hashes do not match C8 manifest")

    quality = read_json(c8 / "quality_summary.json")
    if quality.get("network_requests") != 0:
        raise ValueError("C8 recorded non-zero network_requests")
    if quality.get("supplemental_acquisition_executed") is not False:
        raise ValueError("C8 recorded supplemental acquisition")
    return {
        "status": "PASS",
        "manifest_exists": True,
        "manifest_sha256": sha256_file(manifest_path),
        "git_commit": manifest["git_commit"],
        "output_hash_count": len(output_checks),
        "output_hash_mismatch_count": 0,
        "reference_checks": reference_checks,
        "source_zip_checks": zip_checks,
        "source_zips_unchanged": True,
        "network_requests": 0,
        "supplemental_acquisition_executed": False,
    }


def latest_blockers(row: dict) -> list[tuple[str, int]]:
    return [(label, as_int(row[field])) for label, field in LATEST_BLOCKER_FIELDS
            if as_int(row[field]) > 0]


def has_three_years(history_start: str | None) -> bool:
    if not history_start:
        return False
    start, end = date.fromisoformat(history_start), date.fromisoformat(SNAPSHOT_DATE)
    try:
        anniversary = start.replace(year=start.year + 3)
    except ValueError:
        anniversary = start.replace(year=start.year + 3, day=28)
    return anniversary <= end


def derive_market_blockers(readiness: dict, snapshot: dict | None,
                           latest: dict) -> tuple[str, list[str]]:
    blockers = []
    if snapshot is None:
        blockers.extend(("NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE", "METADATA_WINDOW_CONSTRAINT"))
    if readiness.get("missing_required_features"):
        blockers.append("MISSING_REQUIRED_FEATURES")
    if not as_bool(readiness["latest253_complete"]):
        blockers.append("INSUFFICIENT_LATEST253_REAL_OBSERVATIONS")
    if snapshot is not None:
        reasons = snapshot.get("na_reason", {})
        if "history" in reasons:
            blockers.append("INSUFFICIENT_THREE_YEAR_HISTORY")
        if "metadata" in reasons:
            blockers.append("METADATA_WINDOW_CONSTRAINT")
        if ("beta_126" in readiness.get("missing_required_features", "").split("|")
                and as_int(snapshot.get("lookback_observations")) >= 253):
            blockers.append("BETA_UNDEFINED_WITH_COMPLETE_STOCK_LOOKBACK")
        if ("liquidity_21" in readiness.get("missing_required_features", "").split("|")
                and as_int(snapshot.get("lookback_observations")) >= 21):
            blockers.append("LIQUIDITY_UNDEFINED_WITH_SUFFICIENT_PRICE_LOOKBACK")
    blockers.extend(label for label, _ in latest_blockers(latest))
    blockers = list(dict.fromkeys(blockers))

    if snapshot is None:
        primary = "NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE"
    elif as_bool(readiness["feature_complete"]):
        if "INSUFFICIENT_THREE_YEAR_HISTORY" in blockers:
            primary = "INSUFFICIENT_THREE_YEAR_HISTORY"
        elif "METADATA_WINDOW_CONSTRAINT" in blockers:
            primary = "METADATA_WINDOW_CONSTRAINT"
        else:
            raise ValueError(f"unexplained feature-complete readiness failure: {readiness['security_id']}")
    elif "INSUFFICIENT_LATEST253_REAL_OBSERVATIONS" in blockers:
        primary = "INSUFFICIENT_LATEST253_REAL_OBSERVATIONS"
    elif "MISSING_REQUIRED_FEATURES" in blockers:
        primary = "MISSING_REQUIRED_FEATURES"
    else:
        raise ValueError(f"unexplained market readiness failure: {readiness['security_id']}")
    return primary, blockers


def group_metrics(ids: list[str], readiness: dict[str, dict],
                  full: dict[str, dict]) -> dict:
    rows = [readiness[sid] for sid in ids]
    activity = Counter(row["trading_activity_status"] or "UNKNOWN" for row in rows)
    statuses = Counter(full[sid]["full_history_status"] for sid in ids)
    return {
        "candidate_count": len(rows),
        "feature_complete": sum(as_bool(row["feature_complete"]) for row in rows),
        "market_feature_ready_v2": sum(as_bool(row["market_feature_ready_v2"]) for row in rows),
        "latest253_complete": sum(as_bool(row["latest253_complete"]) for row in rows),
        "latest253_incomplete": sum(not as_bool(row["latest253_complete"]) for row in rows),
        "tradability": {key: activity[key] for key in ("ACTIVE", "OBSERVED_ZERO_VOLUME", "UNKNOWN")},
        "full_history_status": {key: statuses[key] for key in (
            "COMPLETE", "COMPLETE_WITHIN_OBSERVED_BOUNDARY", "UNCERTAIN_BOUNDARY", "INCOMPLETE")},
        "historical_identity_ready": sum(as_bool(row["historical_identity_ready"]) for row in rows),
        "research_ready": sum(as_bool(row["research_ready"]) for row in rows),
    }


def composition_rows(candidates: list[dict], readiness: dict[str, dict], field: str) -> list[dict]:
    groups = sorted({row[field] for row in candidates})
    output = []
    for group in groups:
        ids = [row["security_id"] for row in candidates if row[field] == group]
        ready = sum(as_bool(readiness[sid]["market_feature_ready_v2"]) for sid in ids)
        output.append({
            field: group, "candidate_count": len(ids),
            "market_ready_count": ready, "market_not_ready_count": len(ids) - ready,
        })
    return output


def generate(root: Path, output: Path | None = None) -> dict:
    root = root.resolve()
    c8 = root / C8_ARTIFACT
    output = (output or root / VERIFY_ARTIFACT).resolve()
    if output.exists():
        raise ValueError(f"immutable verification output already exists: {output}")
    integrity = verify_parent_integrity(root)

    candidates_list = read_csv(c8 / "candidate_universe.csv")
    candidates = indexed(candidates_list, "candidate_universe")
    readiness = indexed(read_csv(c8 / "feature_readiness.csv"), "feature_readiness")
    latest = indexed(read_csv(c8 / "latest253_session_audit.csv"), "latest253_session_audit")
    full = indexed(read_csv(c8 / "full_history_session_audit.csv"), "full_history_session_audit")
    ids = set(candidates)
    if ids != set(readiness) or ids != set(latest) or ids != set(full):
        raise ValueError("C8 security_id sets disagree")

    snapshots = {}
    for row in iter_jsonl(c8 / "canonical/feature_snapshots.jsonl"):
        if row.get("as_of_date") == SNAPSHOT_DATE:
            if row["security_id"] in snapshots:
                raise ValueError(f"duplicate comparison snapshot: {row['security_id']}")
            snapshots[row["security_id"]] = row
    identity = {}
    for row in iter_jsonl(c8 / "canonical/securities.jsonl"):
        identity[row["security_id"]] = row.get("identity_status")

    source_counts = Counter(row["candidate_source"] for row in candidates_list)
    headline = {
        "candidate_count": len(ids),
        "baseline_candidate_count": source_counts["C5_BASELINE_500"],
        "expansion_complete_count": source_counts["C7_COMPLETE_EXPANSION"],
        "deferred_expansion_count": len(read_csv(c8 / "deferred_expansion.csv")),
        "feature_complete": sum(as_bool(row["feature_complete"]) for row in readiness.values()),
        "market_feature_ready_v2": sum(as_bool(row["market_feature_ready_v2"]) for row in readiness.values()),
        "latest253_complete": sum(as_bool(row["latest253_complete"]) for row in latest.values()),
        "latest253_incomplete": sum(not as_bool(row["latest253_complete"]) for row in latest.values()),
        "historical_identity_ready": sum(as_bool(row["historical_identity_ready"]) for row in readiness.values()),
        "research_ready": sum(as_bool(row["research_ready"]) for row in readiness.values()),
    }
    disagreements = {key: {"expected": value, "actual": headline.get(key)}
                     for key, value in EXPECTED_HEADLINE.items() if headline.get(key) != value}
    if disagreements:
        raise ValueError(f"MANUAL_REVIEW_REQUIRED: headline disagreement: {disagreements}")

    latest_incomplete = []
    latest_summary = Counter()
    latest_security_count = Counter()
    for sid in sorted(ids, key=lambda value: (candidates[value]["ticker"], value)):
        audit = latest[sid]
        if as_bool(audit["latest253_complete"]):
            continue
        blockers = latest_blockers(audit)
        if not blockers:
            raise ValueError(f"latest253 failure without evidence blocker: {sid}")
        for label, count in blockers:
            latest_security_count[label] += 1
            latest_summary[label] += count
        latest_incomplete.append({
            "security_id": sid, "ticker": audit["ticker"],
            "candidate_source": candidates[sid]["candidate_source"],
            "exchange": audit["exchange"], "latest253_complete": False,
            "observed_valid_253": as_int(audit["observed_valid_253"]),
            "observed_zero_volume_253": as_int(audit["observed_zero_volume_253"]),
            "calendar_uncertain_253": as_int(audit["calendar_uncertain_253"]),
            "missing_sessions_253": as_int(audit["missing_sessions_253"]),
            "invalid_sessions_253": as_int(audit["invalid_sessions_253"]),
            "conflicting_sessions_253": as_int(audit["conflicting_sessions_253"]),
            "boundary_sessions_253": as_int(audit["boundary_sessions_253"]),
            "blocker_codes": "|".join(label for label, _ in blockers),
        })
    latest_blocker_summary = [{
        "blocker": label, "security_count": latest_security_count[label],
        "session_count": latest_summary[label],
    } for label, _ in LATEST_BLOCKER_FIELDS if latest_security_count[label]]

    failure_columns = [
        "security_id", "ticker", "candidate_source", "exchange", "feature_complete",
        "market_feature_ready_v2", "latest253_complete", "full_history_status",
        "missing_required_features", "history_start_date", "history_observations",
        "lookback_observations", "missing_count", "identity_status",
        "relevant_na_reason_entries", "primary_market_blocker", "all_market_blockers",
    ]
    failures = []
    blocker_security = Counter()
    primary_security = Counter()
    for sid in sorted(ids, key=lambda value: (candidates[value]["ticker"], value)):
        ready = readiness[sid]
        if as_bool(ready["market_feature_ready_v2"]):
            continue
        snapshot = snapshots.get(sid)
        primary, blockers = derive_market_blockers(ready, snapshot, latest[sid])
        primary_security[primary] += 1
        blocker_security.update(blockers)
        failures.append({
            "security_id": sid, "ticker": candidates[sid]["ticker"],
            "candidate_source": candidates[sid]["candidate_source"],
            "exchange": candidates[sid]["exchange"],
            "feature_complete": as_bool(ready["feature_complete"]),
            "market_feature_ready_v2": False,
            "latest253_complete": as_bool(ready["latest253_complete"]),
            "full_history_status": full[sid]["full_history_status"],
            "missing_required_features": ready["missing_required_features"],
            "history_start_date": snapshot.get("history_start_date") if snapshot else "",
            "history_observations": snapshot.get("history_observations") if snapshot else "",
            "lookback_observations": snapshot.get("lookback_observations") if snapshot else "",
            "missing_count": snapshot.get("missing_count") if snapshot else "",
            "identity_status": identity.get(sid, ""),
            "relevant_na_reason_entries": json_text(snapshot.get("na_reason", {}) if snapshot else {}),
            "primary_market_blocker": primary,
            "all_market_blockers": "|".join(blockers),
        })
    if len(failures) != 47:
        raise ValueError(f"expected 47 market readiness failures, found {len(failures)}")
    blocker_order = sorted(blocker_security, key=lambda key: (-blocker_security[key], key))
    market_blocker_summary = [{
        "blocker": key, "primary_security_count": primary_security[key],
        "security_count": blocker_security[key],
    } for key in blocker_order]
    feature_complete_not_ready = [row for row in failures if row["feature_complete"]]
    if len(feature_complete_not_ready) != 17:
        raise ValueError("922 vs 905 decomposition did not yield exactly 17 securities")

    gate_rows = []
    for latest_value in (True, False):
        for feature_value in (True, False):
            for market_value in (True, False):
                count = sum(
                    as_bool(row["latest253_complete"]) == latest_value
                    and as_bool(row["feature_complete"]) == feature_value
                    and as_bool(row["market_feature_ready_v2"]) == market_value
                    for row in readiness.values()
                )
                gate_rows.append({"view": "LATEST_X_FEATURE_X_MARKET",
                                  "latest253_complete": latest_value,
                                  "feature_complete": feature_value,
                                  "market_feature_ready_v2": market_value,
                                  "security_count": count})
    for view, first in (("LATEST_X_MARKET", "latest253_complete"),
                        ("FEATURE_X_MARKET", "feature_complete")):
        for first_value in (True, False):
            for market_value in (True, False):
                gate_rows.append({
                    "view": view,
                    "latest253_complete": first_value if first == "latest253_complete" else "",
                    "feature_complete": first_value if first == "feature_complete" else "",
                    "market_feature_ready_v2": market_value,
                    "security_count": sum(as_bool(row[first]) == first_value and
                                          as_bool(row["market_feature_ready_v2"]) == market_value
                                          for row in readiness.values()),
                })

    c5_rows = indexed(read_csv(root / "artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2/feature_readiness_500_v2.csv"), "C5 readiness")
    baseline_ids = sorted(sid for sid in ids if candidates[sid]["candidate_source"] == "C5_BASELINE_500")
    baseline_diff = []
    failure_by_sid = {row["security_id"]: row for row in failures}
    for sid in baseline_ids:
        old = as_bool(c5_rows[sid]["market_feature_ready_v2"])
        new = as_bool(readiness[sid]["market_feature_ready_v2"])
        if old != new:
            baseline_diff.append({
                "security_id": sid, "ticker": candidates[sid]["ticker"],
                "c5_market_feature_ready_v2": old,
                "c8_market_feature_ready_v2": new,
                "change_class": "C5_READY_C8_NOT_READY" if old else "C5_NOT_READY_C8_READY",
                "reason": failure_by_sid.get(sid, {}).get("all_market_blockers", "BECAME_READY"),
            })
    c5_ready = sum(as_bool(row["market_feature_ready_v2"]) for row in c5_rows.values())
    if c5_ready != 490 or baseline_diff:
        raise ValueError(f"MANUAL_REVIEW_REQUIRED: unexplained C5/C8 baseline difference: {baseline_diff}")

    full_rows = list(full.values())
    full_status_counts = Counter(row["full_history_status"] for row in full_rows)
    full_interpretation = {
        "calendar_source": "kbs_observed_session_union",
        "absence_classification": "CALENDAR_UNCERTAIN",
        "calendar_uncertain_security_count": sum(as_int(row["calendar_uncertain"]) > 0 for row in full_rows),
        "calendar_uncertain_session_count": sum(as_int(row["calendar_uncertain"]) for row in full_rows),
        "invalid_provider_row_security_count": sum(as_int(row["invalid_provider_row"]) > 0 for row in full_rows),
        "invalid_provider_row_session_count": sum(as_int(row["invalid_provider_row"]) for row in full_rows),
        "conflict_security_count": sum(as_int(row["conflicting_provider_observation"]) > 0 for row in full_rows),
        "conflict_session_count": sum(as_int(row["conflicting_provider_observation"]) for row in full_rows),
        "boundary_uncertainty_security_count": sum(row["full_history_status"] == "UNCERTAIN_BOUNDARY" for row in full_rows),
        "identity_boundary_security_count": sum(as_int(row["identity_or_listing_boundary"]) > 0 for row in full_rows),
        "provider_boundary_deferred_review_security_count": sum(as_int(row["deferred_review"]) > 0 for row in full_rows),
        "observed_window_incomplete_security_count": sum(not as_bool(row["observed_window_complete"]) for row in full_rows),
        "full_history_status": {key: full_status_counts[key] for key in (
            "COMPLETE", "COMPLETE_WITHIN_OBSERVED_BOUNDARY", "UNCERTAIN_BOUNDARY", "INCOMPLETE")},
        "primary_interpretation": "CALENDAR_EVIDENCE_LIMITATION_WITH_PROVIDER_INVALID_ROW_CONTRIBUTION",
        "interpretation": (
            "Full-history failure is primarily a conservative calendar-evidence limitation: "
            "provider absence remains CALENDAR_UNCERTAIN. Invalid provider rows also contribute; "
            "provider boundaries are not listing evidence and no uncertain absence is promoted to confirmed missing."
        ),
    }

    source_metrics = {
        source: group_metrics(sorted(sid for sid in ids if candidates[sid]["candidate_source"] == source), readiness, full)
        for source in ("C5_BASELINE_500", "C7_COMPLETE_EXPANSION")
    }
    proposed = []
    exclusions = []
    for sid in sorted(ids, key=lambda value: (candidates[value]["ticker"], value)):
        ready = readiness[sid]
        base = {
            "security_id": sid, "ticker": candidates[sid]["ticker"],
            "exchange": candidates[sid]["exchange"],
            "candidate_source": candidates[sid]["candidate_source"],
            "market_feature_ready_v2": as_bool(ready["market_feature_ready_v2"]),
            "latest253_complete": as_bool(ready["latest253_complete"]),
            "trading_activity_status": ready["trading_activity_status"],
            "tradability_eligible": optional_bool(ready["tradability_eligible"]),
            "historical_identity_ready": as_bool(ready["historical_identity_ready"]),
            "research_ready": as_bool(ready["research_ready"]),
            "full_history_status": full[sid]["full_history_status"],
        }
        if base["market_feature_ready_v2"]:
            proposed.append(base)
        else:
            reason = failure_by_sid[sid]
            exclusions.append({**base, "primary_market_blocker": reason["primary_market_blocker"],
                               "all_market_blockers": reason["all_market_blockers"]})
    if len(proposed) != 905 or len(exclusions) != 47:
        raise ValueError("proposed market-only universe count mismatch")

    selected_expansion_count = len(read_csv(
        root / "artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1/acquisition_inventory.csv"
    ))
    if selected_expansion_count != headline["expansion_complete_count"] + headline["deferred_expansion_count"]:
        raise ValueError("C7 selected expansion count does not reconcile to C8 complete plus deferred")
    summary = {
        "stage": "C8-VERIFY", "verification_status": "PASS",
        "manual_review_required": False, "comparison_snapshot": SNAPSHOT_DATE,
        "parent_c8_manifest_sha256": integrity["manifest_sha256"],
        "integrity": integrity, "headline": headline,
        "latest253_blocker_summary": latest_blocker_summary,
        "market_readiness_primary_blockers": dict(primary_security),
        "source_metrics": source_metrics,
        "baseline_c5_market_feature_ready_v2": c5_ready,
        "baseline_c8_market_feature_ready_v2": source_metrics["C5_BASELINE_500"]["market_feature_ready_v2"],
        "baseline_readiness_reproduced": not baseline_diff,
        "selected_expansion_count": selected_expansion_count,
        "complete_expansion_count": 452,
        "deferred_expansion_count": 148,
        "proposed_market_only_universe_count": len(proposed),
        "market_only_semantics": "PROPOSED_MARKET_ONLY_EXPERIMENTAL_UNIVERSE",
        "not_research_ready": True,
        "scope_confirmations": {
            "heavy_c8_rerun": False, "supplemental_crawl_run": False,
            "network_requests": 0, "clustering_run": False, "backtest_run": False,
            "historical_identity_promoted": False, "research_ready_promoted": False,
            "repository_mass_cleanup_executed": False,
        },
    }

    output.mkdir(parents=True)
    latest_columns = [
        "security_id", "ticker", "candidate_source", "exchange", "latest253_complete",
        "observed_valid_253", "observed_zero_volume_253", "calendar_uncertain_253",
        "missing_sessions_253", "invalid_sessions_253", "conflicting_sessions_253",
        "boundary_sessions_253", "blocker_codes",
    ]
    universe_columns = [
        "security_id", "ticker", "exchange", "candidate_source", "market_feature_ready_v2",
        "latest253_complete", "trading_activity_status", "tradability_eligible",
        "historical_identity_ready", "research_ready", "full_history_status",
    ]
    write_json(output / "verification_summary.json", summary)
    write_csv(output / "latest253_incomplete.csv", latest_incomplete, latest_columns)
    write_csv(output / "latest253_blocker_summary.csv", latest_blocker_summary,
              ["blocker", "security_count", "session_count"])
    write_csv(output / "market_readiness_failures.csv", failures, failure_columns)
    write_csv(output / "market_readiness_blocker_summary.csv", market_blocker_summary,
              ["blocker", "primary_security_count", "security_count"])
    write_csv(output / "feature_complete_not_ready.csv", feature_complete_not_ready, failure_columns)
    write_csv(output / "gate_crosstab.csv", gate_rows,
              ["view", "latest253_complete", "feature_complete", "market_feature_ready_v2", "security_count"])
    write_csv(output / "readiness_by_source.csv",
              composition_rows(candidates_list, readiness, "candidate_source"),
              ["candidate_source", "candidate_count", "market_ready_count", "market_not_ready_count"])
    write_csv(output / "readiness_by_exchange.csv",
              composition_rows(candidates_list, readiness, "exchange"),
              ["exchange", "candidate_count", "market_ready_count", "market_not_ready_count"])
    write_csv(output / "baseline_c5_vs_c8_readiness_diff.csv", baseline_diff,
              ["security_id", "ticker", "c5_market_feature_ready_v2", "c8_market_feature_ready_v2", "change_class", "reason"])
    write_json(output / "full_history_interpretation.json", full_interpretation)
    write_csv(output / "proposed_market_only_universe.csv", proposed, universe_columns)
    write_csv(output / "market_only_exclusions.csv", exclusions,
              universe_columns + ["primary_market_blocker", "all_market_blockers"])

    outputs = {path.name: sha256_file(path) for path in sorted(output.iterdir())
               if path.is_file() and path.name != "manifest.json"}
    write_json(output / "manifest.json", {
        "artifact_id": "cafef-c8-verify-v1", "stage": "C8-VERIFY",
        "parent_c8_artifact": C8_ARTIFACT,
        "parent_c8_manifest_sha256": integrity["manifest_sha256"],
        "outputs": outputs,
    })
    verify_generated_manifest(output)
    return summary
