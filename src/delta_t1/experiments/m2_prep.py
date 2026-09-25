"""Build the offline M2-PREP audit without fitting a clustering model."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import statistics
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from ..features.registry import FEATURE_REGISTRY


ARTIFACT_ID = "m2-prep-v1"
STAGE = "M2-PREP"
FINAL_STATUS = "MANUAL_REVIEW_REQUIRED"
SNAPSHOT_DATE = "2026-08-28"
REQUIRED_FEATURES = (
    "mom_21", "mom_63", "mom_126", "mom_252",
    "vol_63", "mdd_126", "beta_126", "liquidity_21",
)
C8 = Path("artifacts/cafef_primary/cafef-c8-complete-only-v1")
C8_VERIFY = Path("artifacts/cafef_primary/cafef-c8-verify-v1")
M1_REPORT = Path("artifacts/reports/m1-market-foundation-v1")
DEFAULT_OUTPUT = Path("artifacts/experiments") / ARTIFACT_ID


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_input(path: Path) -> str:
    """Hash source text canonically so Git LF/CRLF checkout policy is irrelevant."""
    if path.suffix.lower() in {".md", ".py", ".json", ".csv"}:
        data = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
    return sha256_file(path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, rows: list[dict], columns: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: object) -> bool:
    return value is True or str(value).lower() == "true"


def market_experiment_eligible(row: dict | None) -> bool:
    """M2 market-only eligibility is per-snapshot V2 readiness, never legacy eligibility."""
    return bool(row and row.get("market_feature_ready") is True)


def _reason(row: dict | None, candidate: dict, snapshot: str) -> str:
    if row is None:
        return (
            "CANDIDATE_ENTRY_BOUNDARY"
            if candidate.get("audit_start") and candidate["audit_start"] > snapshot
            else "NO_FEATURE_SNAPSHOT_AT_DATE"
        )
    reasons = []
    if "history" in row.get("na_reason", {}):
        reasons.append("MINIMUM_THREE_CALENDAR_YEAR_HISTORY")
    if "metadata" in row.get("na_reason", {}):
        reasons.append("METADATA_PIT_UNAVAILABLE")
    if row.get("mom_21") is None:
        reasons.append("INSUFFICIENT_21_SESSION_WINDOW")
    if row.get("mom_63") is None or row.get("vol_63") is None:
        reasons.append("INSUFFICIENT_63_SESSION_WINDOW")
    if row.get("mom_126") is None or row.get("mdd_126") is None:
        reasons.append("INSUFFICIENT_126_SESSION_WINDOW")
    if row.get("mom_252") is None:
        reasons.append("INSUFFICIENT_252_SESSION_WINDOW")
    if row.get("beta_126") is None:
        reasons.append("BENCHMARK_OR_126_SESSION_DEPENDENCY")
    if row.get("liquidity_21") is None:
        reasons.append("LIQUIDITY_ACTIVITY_UNAVAILABLE")
    if not reasons and not row.get("market_feature_ready"):
        reasons.append("OTHER_MARKET_READINESS_BLOCKER")
    return "|".join(dict.fromkeys(reasons))


def _feature_rows(root: Path, candidates: dict[str, dict]):
    grouped: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in iter_jsonl(root / C8 / "canonical/feature_snapshots.jsonl"):
        if row["security_id"] not in candidates:
            raise ValueError("feature snapshot outside candidate universe")
        date_rows = grouped[row["as_of_date"]]
        if row["security_id"] in date_rows:
            raise ValueError("duplicate security/date feature snapshot")
        date_rows[row["security_id"]] = row
    return grouped


def _verify_parent_manifests(root: Path) -> dict[str, str]:
    m1_manifest = read_json(root / M1_REPORT / "manifest.json")
    expected = {
        (C8 / "manifest.json").as_posix(): m1_manifest["parent_c8_manifest_sha256"],
        (C8_VERIFY / "manifest.json").as_posix(): m1_manifest["parent_c8_verify_manifest_sha256"],
        (M1_REPORT / "manifest.json").as_posix(): sha256_file(root / M1_REPORT / "manifest.json"),
    }
    for relative, digest in expected.items():
        if sha256_file(root / relative) != digest:
            raise ValueError("immutable parent manifest mismatch: " + relative)
    for relative, digest in m1_manifest["outputs"].items():
        if sha256_file(root / M1_REPORT / relative) != digest:
            raise ValueError("M1 report output mismatch: " + relative)
    return expected


def _benchmark_gap_evidence(root: Path) -> dict:
    calendar = defaultdict(set)
    for row in iter_jsonl(root / C8 / "canonical/trading_calendar.jsonl"):
        if row["is_open"]:
            calendar[row["exchange"]].add(row["trade_date"])
    benchmark = {
        row["trade_date"] for row in iter_jsonl(root / C8 / "canonical/benchmark_daily.jsonl")
        if row["index_id"] == "VNINDEX"
    }
    date = "2023-05-15"
    return {
        "date": date,
        "open_exchanges": sorted(exchange for exchange, dates in calendar.items() if date in dates),
        "vnindex_row_present": date in benchmark,
    }


def _count_price_date(root: Path, date: str) -> int:
    needle = f'"trade_date": "{date}"'.encode()
    count = 0
    overlap = b""
    with (root / C8 / "canonical/prices_daily.jsonl").open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            data = overlap + chunk
            count += data.count(needle)
            overlap = data[-(len(needle) - 1):]
    return count


def _window_stats(name: str, rows: list[dict], note: str) -> dict:
    eligible = [row["market_feature_ready_v2"] for row in rows]
    baseline = sum(row["baseline_ready"] for row in rows)
    expansion = sum(row["expansion_ready"] for row in rows)
    total = baseline + expansion
    deltas = [right - left for left, right in zip(eligible, eligible[1:])]
    return {
        "option": name,
        "start_date": rows[0]["snapshot_date"],
        "end_date": rows[-1]["snapshot_date"],
        "snapshot_count": len(rows),
        "eligible_min": min(eligible),
        "eligible_median": statistics.median(eligible),
        "eligible_mean": round(statistics.mean(eligible), 6),
        "eligible_max": max(eligible),
        "zero_eligible_snapshots": sum(value == 0 for value in eligible),
        "low_coverage_snapshots": "",
        "low_coverage_threshold": "UNRESOLVED_MANUAL_REVIEW_REQUIRED",
        "largest_month_to_month_drop": min(deltas, default=0),
        "largest_month_to_month_gain": max(deltas, default=0),
        "baseline_share": round(baseline / total, 6) if total else "",
        "expansion_share": round(expansion / total, 6) if total else "",
        "continuity_notes": note,
    }


def _candidate_windows(monthly: list[dict]) -> list[dict]:
    def between(start: str, end: str) -> list[dict]:
        return [row for row in monthly if start <= row["snapshot_date"] <= end]

    return [
        _window_stats(
            "FULL_POST_HISTORY_GATE_WITH_SKIPS",
            between("2023-01-31", "2026-08-28"),
            "Contains 18 zero-readiness snapshots; requires an explicit skipped-month policy.",
        ),
        _window_stats(
            "PRE_BENCHMARK_GAP_SHORT",
            between("2023-01-31", "2023-04-28"),
            "Four nonzero snapshots only; ends before the VNINDEX 2023-05-15 gap propagates.",
        ),
        _window_stats(
            "CONTIGUOUS_MAIN",
            between("2023-11-30", "2025-01-24"),
            "Fifteen consecutive nonzero snapshots; ends before the 2025-02-03 all-equity gap enters mom_252.",
        ),
        _window_stats(
            "LATEST_RECOVERY",
            between("2026-02-27", "2026-08-28"),
            "Seven consecutive nonzero snapshots; short and closest to the latest universe.",
        ),
    ]


def _feature_contract() -> list[dict]:
    interpretations = {
        "mom_21": "1-month price momentum proxy",
        "mom_63": "3-month price momentum proxy",
        "mom_126": "6-month price momentum proxy",
        "mom_252": "12-month price momentum proxy",
        "vol_63": "annualized 63-session return volatility",
        "mdd_126": "126-session peak-to-trough drawdown",
        "beta_126": "126-return market sensitivity to VNINDEX",
        "liquidity_21": "21-session mean traded value activity",
    }
    rows = []
    for name in REQUIRED_FEATURES:
        item = FEATURE_REGISTRY.get(name)
        rows.append({
            "name": name,
            "registry_version": item.version,
            "c8_snapshot_version": "1.6.0",
            "version_status": "MISMATCH_MANUAL_REVIEW_REQUIRED",
            "formula": item.formula,
            "formula_code_status": "MATCH",
            "source": "|".join(item.required_source),
            "lookback": item.lookback,
            "missing_policy": item.missing_policy,
            "pit_rule": item.point_in_time_rule,
            "transform_metadata": item.transform,
            "transform_status": "UNFROZEN_AT_EXPERIMENT_LEVEL",
            "cluster_eligible": item.cluster_eligible,
            "economic_interpretation": interpretations[name],
        })
    return rows


def _preprocessing_matrix() -> list[dict]:
    return [
        {"transform": "missing_value_handling", "implemented": True, "status": "APPROVED_DEFAULT", "decision": "Reject nonfinite/missing eligible features; no imputation."},
        {"transform": "winsorization_clipping", "implemented": True, "status": "MANUAL_REVIEW_REQUIRED", "decision": "Quantile clipping is supported but q is not approved."},
        {"transform": "log1p", "implemented": True, "status": "NOT_APPROVED", "decision": "Negative market features make blanket log1p invalid; no M2 feature list approved."},
        {"transform": "zscore", "implemented": True, "status": "MANUAL_REVIEW_REQUIRED", "decision": "Snapshot-fit support exists; default not frozen."},
        {"transform": "robust_scaling", "implemented": True, "status": "MANUAL_REVIEW_REQUIRED", "decision": "Median/IQR support exists; comparator/default role not frozen."},
        {"transform": "rank_scaling", "implemented": True, "status": "NOT_APPROVED", "decision": "Support exists, but no M2 methodology approval."},
        {"transform": "no_scaling", "implemented": True, "status": "MANUAL_REVIEW_REQUIRED", "decision": "Supported candidate; scale-sensitive algorithms require owner decision."},
        {"transform": "pca", "implemented": True, "status": "APPROVED_COMPARATOR", "decision": "Distinct comparator branch only; component count remains unresolved."},
    ]


def _algorithm_matrix() -> list[dict]:
    return [
        {"algorithm": "K-Means", "implemented": True, "tested": True, "fixed_or_variable_k": "fixed", "noise_support": False, "literature_support": "MacQueen (1967)", "methodology_status": "PRIMARY_BASELINE", "parameter_audit": "K-Means++; seed+n_init+max_iter explicit; exact-label convergence; configurable tolerance absent", "role_in_M2": "Static monthly baseline after unresolved protocol choices are approved."},
        {"algorithm": "PCA + K-Means", "implemented": True, "tested": True, "fixed_or_variable_k": "fixed", "noise_support": False, "literature_support": "Pearson (1901) + MacQueen (1967)", "methodology_status": "APPROVED_COMPARATOR", "parameter_audit": "Snapshot-fit scaler/components/explained variance stored; fixed n_components only and unresolved", "role_in_M2": "Comparator only; n_components unresolved."},
        {"algorithm": "Ward/Agglomerative", "implemented": True, "tested": True, "fixed_or_variable_k": "fixed", "noise_support": False, "literature_support": "Ward (1963)", "methodology_status": "APPROVED_COMPARATOR", "parameter_audit": "Deterministic minimum Ward SSE increase on shared preprocessed Euclidean vectors; scale-sensitive", "role_in_M2": "Deterministic comparator using shared frozen preprocessing/k."},
        {"algorithm": "GMM", "implemented": False, "tested": False, "fixed_or_variable_k": "fixed_candidate", "noise_support": False, "literature_support": "Supporting literature only", "methodology_status": "FUTURE_COMPARATOR", "parameter_audit": "Stub: covariance type, initialization, seed, regularization and singularity handling unresolved", "role_in_M2": "Fail-closed stub; no explicit parameter protocol."},
        {"algorithm": "DBSCAN", "implemented": False, "tested": False, "fixed_or_variable_k": "variable", "noise_support": False, "literature_support": "Ester et al. (1996)", "methodology_status": "NOT_COMPATIBLE_WITH_CURRENT_PROTOCOL", "parameter_audit": "Stub: eps/min_samples/noise/all-noise/one-cluster/birth-death behavior unsupported", "role_in_M2": "NOT_APPROVED_FOR_CURRENT_M2; fixed-k interface lacks noise/birth/death handling."},
        {"algorithm": "Dynamic Clustering", "implemented": False, "tested": True, "fixed_or_variable_k": "sequence_method", "noise_support": False, "literature_support": "Chakrabarti (2006); João et al. (2023, 2024)", "methodology_status": "NOT_APPROVED", "parameter_audit": "Abstract interface only; no objective/state update/regularization implementation", "role_in_M2": "F3 is closest future candidate but needs separate review."},
    ]


def _metric_matrix() -> list[dict]:
    rows = []
    for name in ("silhouette", "davies_bouldin", "calinski_harabasz", "inertia", "cluster_balance"):
        rows.append({"layer": "cluster_quality", "metric": name, "implemented": True, "classification": "SECONDARY_DIAGNOSTIC", "behavior": "Supported; no single metric is frozen as selection objective."})
    for name in ("ARI", "NMI", "persistence_probability", "migration_rate", "transition_matrix", "centroid_drift", "entry_exit"):
        rows.append({"layer": "temporal_stability", "metric": name, "implemented": True, "classification": "SECONDARY_DIAGNOSTIC", "behavior": "Shared-security comparison; alignment is separate from ARI/NMI."})
    for name in ("future_return", "Sharpe", "ROI", "CAGR", "Sortino", "Calmar", "portfolio_alpha", "information_ratio", "turnover", "transaction_cost_adjusted_return"):
        rows.append({"layer": "model_selection_firewall", "metric": name, "implemented": False, "classification": "UNSUPPORTED", "behavior": "Forbidden for M2 algorithm/k/preprocessing selection."})
    return rows


def _implementation_gaps() -> list[dict]:
    return [
        {"area": "experiment_runner", "finding": "runner.py counts row['eligibility']", "status": "FIX_REQUIRED_BEFORE_M2_EXEC", "required_change": "Add explicit market-only mode and per-snapshot adapter; preserve legacy mode."},
        {"area": "clustering_base", "finding": "base.py filters row['eligibility']", "status": "FIX_REQUIRED_BEFORE_M2_EXEC", "required_change": "Use an explicitly configured eligibility field with no silent fallback in market-only mode."},
        {"area": "input_loader", "finding": "real loader requires verified identity and standard data-run layout", "status": "FIX_REQUIRED_BEFORE_M2_EXEC", "required_change": "Add narrow checksummed C8 market-only input adapter without weakening strict research path."},
        {"area": "protocol", "finding": "protocol 1.0 has no market-only eligibility/scope fields", "status": "FIX_REQUIRED_BEFORE_M2_EXEC", "required_change": "Version and validate explicit market-only scope after owner decisions."},
        {"area": "K-Means tolerance", "finding": "seed, n_init and max_iter are explicit but convergence uses exact unchanged labels; no tolerance parameter", "status": "MANUAL_REVIEW_REQUIRED", "required_change": "Approve exact-label convergence or add/freeze an explicit tolerance contract."},
        {"area": "feature_metadata", "finding": "registry metadata is 1.5.0 while C8 rows are 1.6.0", "status": "MANUAL_REVIEW_REQUIRED", "required_change": "Resolve version/documentation contract without mutating C8."},
        {"area": "feature_transform_metadata", "finding": "registry says winsorize_then_snapshot_scale but q/scaler are unfrozen", "status": "MANUAL_REVIEW_REQUIRED", "required_change": "Approve outlier/scaling policy before config creation."},
        {"area": "holdout", "finding": "runner enforces development_end but has no sealed final-holdout workflow", "status": "MANUAL_REVIEW_REQUIRED", "required_change": "Approve boundary and implement one-use holdout guard before final evaluation."},
        {"area": "GMM", "finding": "fail-closed stub only", "status": "EXPECTED_GUARD", "required_change": "No current M2 approval."},
        {"area": "DBSCAN", "finding": "fail-closed stub; fixed-k/noise contract incompatible", "status": "EXPECTED_GUARD", "required_change": "Separate variable-cluster design before future approval."},
        {"area": "Dynamic", "finding": "abstract interface only", "status": "EXPECTED_GUARD", "required_change": "Separate explicit methodology/mentor approval required."},
    ]


def _methodology_decisions() -> list[dict]:
    return [
        {"decision": "eligibility", "status": "FROZEN", "value": "market_experiment_eligible(t)=market_feature_ready_v2(t) per snapshot"},
        {"decision": "feature_set", "status": "FROZEN", "value": "|".join(REQUIRED_FEATURES)},
        {"decision": "missing_values", "status": "FROZEN", "value": "No imputation, fill, zero conversion, or timeline compression"},
        {"decision": "portfolio_boundary", "status": "FROZEN", "value": "portfolio_evaluation.enabled=false; no M2 backtest/performance"},
        {"decision": "model_selection_firewall", "status": "FROZEN", "value": "No return/portfolio metric may choose feature, preprocessing, algorithm, PCA, or k"},
        {"decision": "dynamic_clustering", "status": "FROZEN", "value": "NOT APPROVED"},
        {"decision": "latest_snapshot", "status": "REPRODUCED", "value": "905/952 at 2026-08-28; not retrospective"},
    ]


def _unresolved_decisions() -> list[dict]:
    return [
        {"decision": "development_window", "owner_action": "Choose among candidate windows and define minimum cross-section/consecutive-month/skipped-month thresholds.", "options": "2023-01..2023-04; 2023-11..2025-01; 2026-02..2026-08; full range with explicit skips"},
        {"decision": "final_holdout", "owner_action": "Approve a time boundary and one-use access rule.", "options": "Seal 2026-02..2026-08; reserve a tail of 2023-11..2025-01; acquire/correct evidence before defining holdout"},
        {"decision": "k_policy", "owner_action": "Choose fixed preregistered k or development-only selection rule and temporal comparability policy.", "options": "fixed k; one development-selected k; per-snapshot k is incompatible with current temporal alignment"},
        {"decision": "outlier_policy", "owner_action": "Approve no clipping, fixed preregistered quantile, or robust transform before results.", "options": "none; fixed winsor q; robust scaling"},
        {"decision": "scaling", "owner_action": "Approve default and comparator scaling.", "options": "zscore; robust; none; rank not currently approved"},
        {"decision": "PCA_components", "owner_action": "Approve fixed component count or development-only variance threshold.", "options": "fixed n; variance threshold; disable PCA comparator"},
        {"decision": "feature_version", "owner_action": "Resolve registry 1.5.0 versus C8 snapshot 1.6.0 metadata.", "options": "version registry metadata; document scoped compatibility"},
    ]


def _holdout_candidates() -> list[dict]:
    return [
        {"option": "SEAL_LATEST_RECOVERY", "development": "2023-11-30..2025-01-24", "final_holdout": "2026-02-27..2026-08-28", "status": "MANUAL_REVIEW_REQUIRED", "tradeoff": "Keeps seven latest snapshots unseen, but a 12-month zero-readiness block separates development and holdout."},
        {"option": "TAIL_OF_MAIN_WINDOW", "development": "2023-11-30..2024-08-30", "final_holdout": "2024-09-30..2025-01-24", "status": "MANUAL_REVIEW_REQUIRED", "tradeoff": "Continuous chronology, but only ten development and five holdout snapshots with changing coverage."},
        {"option": "DEFER_BOUNDARY", "development": "UNRESOLVED", "final_holdout": "UNRESOLVED", "status": "MANUAL_REVIEW_REQUIRED", "tradeoff": "Wait for owner decision or corrective source evidence; delays M2 but avoids a weak arbitrary split."},
    ]


def build_data(root: Path, *, scan_heavy_price_evidence: bool = False) -> dict:
    root = root.resolve()
    parent_hashes = _verify_parent_manifests(root)
    candidate_rows = read_csv(root / C8 / "candidate_universe.csv")
    candidates = {row["security_id"]: row for row in candidate_rows}
    if len(candidates) != 952:
        raise ValueError("candidate universe no longer has 952 unique securities")
    grouped = _feature_rows(root, candidates)
    report_monthly = read_csv(root / M1_REPORT / "monthly_market_readiness.csv")
    monthly = []
    eligibility = []
    diagnostics = []
    previous_ready = None
    for report_row in report_monthly:
        snapshot = report_row["snapshot_date"]
        rows = grouped.get(snapshot, {})
        summary = {
            key: int(report_row[key]) if key != "snapshot_date" else snapshot
            for key in report_row
        }
        actual_complete = sum(as_bool(row["feature_complete"]) for row in rows.values())
        actual_ready = sum(market_experiment_eligible(row) for row in rows.values())
        if (len(rows), actual_complete, actual_ready) != (
            summary["candidate_rows"], summary["feature_complete"], summary["market_feature_ready_v2"]
        ):
            raise ValueError("monthly M1 report mismatch at " + snapshot)
        summary["candidate_universe"] = len(candidates)
        summary["feature_snapshot_present"] = len(rows)
        summary["candidate_without_snapshot"] = len(candidates) - len(rows)
        summary["market_experiment_eligible"] = actual_ready
        summary["eligibility_rate_of_952"] = round(actual_ready / len(candidates), 9)
        monthly.append(summary)

        for security_id, candidate in sorted(candidates.items()):
            row = rows.get(security_id)
            feature_complete = bool(row and row.get("feature_complete"))
            ready = market_experiment_eligible(row)
            eligibility.append({
                "snapshot_date": snapshot,
                "security_id": security_id,
                "candidate_source": candidate["candidate_source"],
                "feature_snapshot_present": row is not None,
                "market_feature_ready_v2": ready,
                "market_experiment_eligible": ready,
                "feature_complete": feature_complete,
                "history_requirement_pass": bool(row and "history" not in row.get("na_reason", {})),
                "latest_window_requirement_pass": bool(row and row.get("mom_252") is not None),
                "reason_if_ineligible": "" if ready else _reason(row, candidate, snapshot),
            })

        def null_count(*names: str) -> int:
            return sum(any(row.get(name) is None for name in names) for row in rows.values())

        history_fail = sum("history" in row.get("na_reason", {}) for row in rows.values())
        metadata_fail = sum("metadata" in row.get("na_reason", {}) for row in rows.values())
        provider_boundary = sum(
            "PROVIDER_OBSERVED_HISTORY_BOUNDARY" in candidates[sid].get("boundary_basis", "")
            and "history" in row.get("na_reason", {})
            for sid, row in rows.items()
        )
        if snapshot < "2023-01-01":
            classification = "A_EXPECTED_METHODOLOGY_SEMANTICS"
            evidence = "Three-calendar-year history gate dominates before 2023."
        elif "2023-05-01" <= snapshot <= "2023-10-31":
            classification = "C_BENCHMARK_CALENDAR_PROPAGATION"
            evidence = "VNINDEX missing 2023-05-15 propagates through strict beta_126 window."
        elif "2025-02-01" <= snapshot <= "2026-01-31":
            classification = "B_SPARSE_INCOMPLETE_MARKET_EVIDENCE"
            evidence = "No equity price rows on open session 2025-02-03; strict mom_252 requires 253 prices."
        else:
            classification = "A_EXPECTED_PLUS_B_SECURITY_LEVEL_EVIDENCE"
            evidence = "Nonzero readiness; remaining losses follow strict windows/history/boundaries."
        diagnostics.append({
            "snapshot_date": snapshot,
            "candidate_universe": len(candidates),
            "candidate_rows_available": len(rows),
            "feature_snapshot_present": len(rows),
            "feature_complete": actual_complete,
            "market_feature_ready_v2": actual_ready,
            "insufficient_21_session_window": null_count("mom_21"),
            "insufficient_63_session_window": null_count("mom_63", "vol_63"),
            "insufficient_126_session_window": null_count("mom_126", "mdd_126"),
            "insufficient_252_session_window": null_count("mom_252"),
            "minimum_three_calendar_year_history_fail": history_fail,
            "benchmark_beta_dependency_fail": null_count("beta_126"),
            "liquidity_activity_fail": null_count("liquidity_21"),
            "calendar_uncertainty": "NOT_DERIVABLE_PER_MONTH_FROM_FEATURE_ROWS",
            "provider_boundary_history_fail": provider_boundary,
            "metadata_pit_fail": metadata_fail,
            "candidate_entry_or_no_snapshot": len(candidates) - len(rows),
            "month_to_month_ready_change": "" if previous_ready is None else actual_ready - previous_ready,
            "classification": classification,
            "evidence": evidence,
        })
        previous_ready = actual_ready

    latest = [row for row in eligibility if row["snapshot_date"] == SNAPSHOT_DATE]
    latest_universe = [row for row in latest if row["market_experiment_eligible"]]
    latest_legacy_eligibility = sum(
        as_bool(row.get("eligibility")) for row in grouped[SNAPSHOT_DATE].values()
    )
    if len(latest) != 952 or len(latest_universe) != 905:
        raise ValueError("latest market-only universe does not reproduce 905/952")
    if latest_legacy_eligibility == len(latest_universe):
        raise ValueError("legacy eligibility was incorrectly treated as market-only eligibility")
    all_feature_rows = (row for rows in grouped.values() for row in rows.values())
    if any(row.get("historical_identity_ready") for row in all_feature_rows):
        raise ValueError("historical identity was unexpectedly promoted")
    all_feature_rows = (row for rows in grouped.values() for row in rows.values())
    if any(row.get("research_ready") for row in all_feature_rows):
        raise ValueError("research readiness was unexpectedly promoted")

    benchmark_gap = _benchmark_gap_evidence(root)
    if benchmark_gap != {"date": "2023-05-15", "open_exchanges": ["HNX", "HOSE", "UPCOM"], "vnindex_row_present": False}:
        raise ValueError("benchmark-gap evidence changed")
    equity_gap_count = _count_price_date(root, "2025-02-03") if scan_heavy_price_evidence else 0
    if scan_heavy_price_evidence and equity_gap_count != 0:
        raise ValueError("expected zero canonical equity rows on 2025-02-03")

    input_paths = [
        C8 / "manifest.json", C8_VERIFY / "manifest.json", M1_REPORT / "manifest.json",
        Path("configs/data/cafef_c8_complete_only_v1.json"),
        Path("src/delta_t1/features/market.py"), Path("src/delta_t1/features/preprocessing.py"),
        Path("src/delta_t1/features/registry.py"),
        Path("src/delta_t1/clustering/base.py"), Path("src/delta_t1/clustering/kmeans.py"),
        Path("src/delta_t1/clustering/hierarchical.py"), Path("src/delta_t1/clustering/gmm.py"),
        Path("src/delta_t1/clustering/dbscan.py"), Path("src/delta_t1/clustering/dynamic/base.py"),
        Path("src/delta_t1/evaluation/cluster_metrics.py"),
        Path("src/delta_t1/evaluation/temporal_metrics.py"),
        Path("src/delta_t1/experiments/protocol.py"), Path("src/delta_t1/experiments/runner.py"),
        Path("src/delta_t1/experiments/artifacts.py"),
        Path("docs/METHODOLOGY.md"), Path("docs/DECISIONS.md"),
        Path("docs/research/EXPERIMENT_PROTOCOL.md"), Path("docs/research/LITERATURE_MATRIX.md"),
        Path("docs/research/DYNAMIC_CLUSTERING_REVIEW.md"),
    ]
    complete_literature = Path("docs/research/LITERATURE_MATRIX_COMPLETE.md")
    if (root / complete_literature).is_file():
        input_paths.append(complete_literature)
    input_hashes = {path.as_posix(): sha256_input(root / path) for path in input_paths}

    temporal_protocol = {
        "method": "STATIC_SNAPSHOT_CLUSTERING_PLUS_TEMPORAL_EVALUATION",
        "dynamic_clustering": "NOT_APPROVED",
        "shared_security_rule": "ARI/NMI/transitions use intersection; entry/exit reported separately.",
        "label_alignment": "Exact fixed-k assignment is separate from permutation-invariant ARI/NMI.",
        "skipped_snapshot": "Current runner resets comparison across nonconsecutive months.",
        "different_k": "Unsupported; compare() raises and requires a separate stability experiment.",
        "cluster_disappears": "Fixed-k fit requires nonempty clusters; variable-k birth/death unsupported.",
        "literature_future_candidate": "João et al. (2024) is closest architecturally; separate full methodology approval required.",
    }
    return {
        "parent_hashes": parent_hashes,
        "input_hashes": input_hashes,
        "monthly": monthly,
        "diagnostics": diagnostics,
        "eligibility": eligibility,
        "latest_universe": latest_universe,
        "candidate_windows": _candidate_windows(monthly),
        "feature_contract": _feature_contract(),
        "preprocessing": _preprocessing_matrix(),
        "algorithms": _algorithm_matrix(),
        "metrics": _metric_matrix(),
        "temporal_protocol": temporal_protocol,
        "implementation_gaps": _implementation_gaps(),
        "methodology_decisions": _methodology_decisions(),
        "unresolved_decisions": _unresolved_decisions(),
        "holdout_candidates": _holdout_candidates(),
        "benchmark_gap": benchmark_gap,
        "equity_gap": {"date": "2025-02-03", "canonical_price_rows": equity_gap_count, "calendar_status": "OPEN_ALL_THREE_EXCHANGES"},
        "literature_complete_present": (root / complete_literature).is_file(),
        "latest_legacy_eligibility": latest_legacy_eligibility,
    }


def generate(root: Path, output: Path = DEFAULT_OUTPUT, *, parent_head: str | None = None) -> None:
    root = root.resolve()
    output = (root / output).resolve()
    if output.exists():
        raise ValueError("immutable M2-PREP output already exists: " + str(output))
    data = build_data(root, scan_heavy_price_evidence=True)
    parent_head = parent_head or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix="m2-prep-", dir=output.parent))
    try:
        write_csv(temp / "snapshot_coverage.csv", data["monthly"], tuple(data["monthly"][0]))
        write_csv(temp / "snapshot_diagnostics.csv", data["diagnostics"], tuple(data["diagnostics"][0]))
        write_csv(temp / "snapshot_eligibility.csv", data["eligibility"], tuple(data["eligibility"][0]))
        latest_columns = (
            "snapshot_date", "security_id", "candidate_source", "market_experiment_eligible"
        )
        write_csv(
            temp / "latest_snapshot_universe.csv",
            [{key: row[key] for key in latest_columns} for row in data["latest_universe"]],
            latest_columns,
        )
        write_csv(temp / "candidate_windows.csv", data["candidate_windows"], tuple(data["candidate_windows"][0]))
        write_csv(temp / "feature_contract.csv", data["feature_contract"], tuple(data["feature_contract"][0]))
        write_csv(temp / "preprocessing_matrix.csv", data["preprocessing"], tuple(data["preprocessing"][0]))
        write_csv(temp / "algorithm_matrix.csv", data["algorithms"], tuple(data["algorithms"][0]))
        write_csv(temp / "metric_matrix.csv", data["metrics"], tuple(data["metrics"][0]))
        write_csv(temp / "implementation_gap_audit.csv", data["implementation_gaps"], tuple(data["implementation_gaps"][0]))
        write_csv(temp / "methodology_decisions.csv", data["methodology_decisions"], tuple(data["methodology_decisions"][0]))
        write_csv(temp / "unresolved_decisions.csv", data["unresolved_decisions"], tuple(data["unresolved_decisions"][0]))
        write_csv(temp / "holdout_candidates.csv", data["holdout_candidates"], tuple(data["holdout_candidates"][0]))
        write_json(temp / "temporal_protocol.json", data["temporal_protocol"])
        protocol = {
            "artifact_id": ARTIFACT_ID,
            "stage": STAGE,
            "parent_head": parent_head,
            "parent_worktree_clean_at_start": False,
            "parent_worktree_exception_at_start": "untracked docs/research/LITERATURE_MATRIX_COMPLETE.md",
            "status": FINAL_STATUS,
            "eligibility_semantics": "market_experiment_eligible(t) = market_feature_ready_v2(t) at the same snapshot",
            "latest_snapshot": SNAPSHOT_DATE,
            "latest_market_experiment_eligible": 905,
            "latest_legacy_eligibility": data["latest_legacy_eligibility"],
            "candidate_universe": 952,
            "historical_identity_ready": 0,
            "research_ready": 0,
            "required_features": list(REQUIRED_FEATURES),
            "portfolio_evaluation": {"enabled": False},
            "benchmark_gap_evidence": data["benchmark_gap"],
            "equity_gap_evidence": data["equity_gap"],
            "literature_matrix_complete_present": data["literature_complete_present"],
            "config_created": False,
            "config_reason": "Critical methodology and runner/input-adapter decisions remain unresolved.",
            "scope_confirmations": {
                "c8_rerun": False,
                "network_access": False,
                "supplemental_acquisition": False,
                "real_clustering": False,
                "backtest": False,
                "historical_identity_promoted": False,
                "research_ready_promoted": False,
                "terminal_905_retrospective_filter": False,
            },
        }
        write_json(temp / "protocol_summary.json", protocol)
        outputs = {
            path.relative_to(temp).as_posix(): sha256_file(path)
            for path in sorted(temp.iterdir()) if path.is_file()
        }
        manifest = {
            "artifact_id": ARTIFACT_ID,
            "stage": STAGE,
            "parent_head": parent_head,
            "status": FINAL_STATUS,
            "input_hashes": data["input_hashes"],
            "input_hash_method": "sha256 of canonical-LF UTF-8 text; raw bytes for non-text",
            "outputs": outputs,
            "network_requests": 0,
        }
        write_json(temp / "manifest.json", manifest)
        temp.replace(output)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def verify_existing(root: Path, output: Path = DEFAULT_OUTPUT) -> None:
    root = root.resolve()
    directory = (root / output).resolve()
    manifest = read_json(directory / "manifest.json")
    if manifest.get("status") != FINAL_STATUS or manifest.get("network_requests") != 0:
        raise ValueError("invalid M2-PREP manifest")
    for relative, expected in manifest["input_hashes"].items():
        if sha256_input(root / relative) != expected:
            raise ValueError("M2-PREP input hash mismatch: " + relative)
    for relative, expected in manifest["outputs"].items():
        if sha256_file(directory / relative) != expected:
            raise ValueError("M2-PREP output hash mismatch: " + relative)
    summary = read_json(directory / "protocol_summary.json")
    if summary["latest_market_experiment_eligible"] != 905 or summary["candidate_universe"] != 952:
        raise ValueError("M2-PREP latest eligibility changed")
    if summary["portfolio_evaluation"]["enabled"]:
        raise ValueError("M2-PREP portfolio evaluation must remain disabled")
