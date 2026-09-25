"""Build the deterministic M1 CafeF market-foundation report and inspection notebook."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ARTIFACT_ID = "m1-market-foundation-v1"
STAGE = "M1-REPORT"
SNAPSHOT_DATE = "2026-08-28"
SOURCE_COMMIT = "ca071cb207dc914cd1e83a9edf04ed533a28838e"
DEFAULT_OUTPUT = Path("artifacts/reports") / ARTIFACT_ID
DEFAULT_NOTEBOOK = Path("notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb")
C8_DIR = Path("artifacts/cafef_primary/cafef-c8-complete-only-v1")
VERIFY_DIR = Path("artifacts/cafef_primary/cafef-c8-verify-v1")
R1_DIR = Path("artifacts/repository/r1-consolidation-v1")
EXPECTED_PARENT_HASHES = {
    "parent_c8_manifest_sha256": "01ed9e890103c894239ac30accc781260de547b73193ec5b54dbb0d678a8702e",
    "parent_c8_verify_manifest_sha256": "0ff737d204a04919a79b606351e4dbf69a3e7145c2eade4e7654a90bcf689f10",
    "r1_manifest_sha256": "b8875c0686dc48b0581a9f64f445948b831d4f3c4732b4b786d74559df99cb55",
}
REQUIRED_FEATURES = (
    "mom_21",
    "mom_63",
    "mom_126",
    "mom_252",
    "vol_63",
    "mdd_126",
    "beta_126",
    "liquidity_21",
)
EXPECTED_HEADLINE = {
    "candidate_count": 952,
    "baseline_count": 500,
    "complete_expansion_count": 452,
    "deferred_expansion_count": 148,
    "feature_complete": 922,
    "market_feature_ready_v2": 905,
    "market_readiness_failures": 47,
    "latest253_complete": 922,
    "latest253_incomplete": 30,
    "historical_identity_ready": 0,
    "research_ready": 0,
}
EXPECTED_TRADABILITY = {
    "ACTIVE": 675,
    "OBSERVED_ZERO_VOLUME": 276,
    "UNKNOWN": 1,
}
EXPECTED_PRIMARY_BLOCKERS = {
    "INSUFFICIENT_LATEST253_REAL_OBSERVATIONS": 29,
    "INSUFFICIENT_THREE_YEAR_HISTORY": 17,
    "NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE": 1,
}
EXPECTED_LATEST_BLOCKERS = {
    "CALENDAR_UNCERTAIN": {"security_count": 14, "session_count": 227},
    "IDENTITY_OR_PROVIDER_BOUNDARY": {"security_count": 16, "session_count": 2266},
}
EXPECTED_COMPLETE_NOT_READY = (
    "AAH", "AIG", "AVG", "BGE", "BHH", "BMK", "DKG", "DSE", "F88",
    "GDA", "HNA", "QNP", "RYG", "SBG", "TAL", "TD6", "VPL",
)
REPORT_FILES = (
    "report.json",
    "per_security.csv",
    "feature_coverage.csv",
    "readiness_funnel.csv",
    "composition_by_source.csv",
    "composition_by_exchange.csv",
    "monthly_market_readiness.csv",
    "blocker_summary.csv",
)
PLOT_FILES = (
    "universe_composition.png",
    "readiness_funnel.png",
    "required_feature_coverage.png",
    "latest253_status.png",
    "market_readiness_blockers.png",
    "monthly_market_readiness.png",
    "tradability_distribution.png",
    "baseline_vs_expansion.png",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def as_bool(value: object) -> bool:
    return value is True or str(value).lower() == "true"


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


def verify_manifest(directory: Path) -> int:
    manifest = read_json(directory / "manifest.json")
    outputs = manifest.get("outputs", {})
    failures = [
        relative
        for relative, expected in outputs.items()
        if not (directory / relative).is_file()
        or sha256_file(directory / relative) != expected
    ]
    if failures:
        raise ValueError(f"parent artifact hash mismatch in {directory}: {failures}")
    return len(outputs)


def verify_inputs(root: Path) -> dict:
    paths = {
        "parent_c8_manifest_sha256": root / C8_DIR / "manifest.json",
        "parent_c8_verify_manifest_sha256": root / VERIFY_DIR / "manifest.json",
        "r1_manifest_sha256": root / R1_DIR / "manifest.json",
    }
    actual = {key: sha256_file(path) for key, path in paths.items()}
    if actual != EXPECTED_PARENT_HASHES:
        raise ValueError(
            "MANUAL_REVIEW_REQUIRED: parent manifest hash mismatch; STOP. "
            f"expected={EXPECTED_PARENT_HASHES}, actual={actual}"
        )
    counts = {
        "c8_outputs_verified": verify_manifest(root / C8_DIR),
        "c8_verify_outputs_verified": verify_manifest(root / VERIFY_DIR),
        "r1_outputs_verified": verify_manifest(root / R1_DIR),
    }
    return {**actual, **counts}


def indexed(rows: list[dict], label: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        key = row["security_id"]
        if key in result:
            raise ValueError(f"duplicate security_id in {label}: {key}")
        result[key] = row
    return result


def build_data(root: Path) -> dict:
    integrity = verify_inputs(root)
    candidate_rows = read_csv(root / C8_DIR / "candidate_universe.csv")
    deferred_rows = read_csv(root / C8_DIR / "deferred_expansion.csv")
    readiness_rows = read_csv(root / C8_DIR / "feature_readiness.csv")
    latest_audit_rows = read_csv(root / C8_DIR / "latest253_session_audit.csv")
    failure_rows = read_csv(root / VERIFY_DIR / "market_readiness_failures.csv")
    incomplete_rows = read_csv(root / VERIFY_DIR / "latest253_incomplete.csv")
    verify_summary = read_json(root / VERIFY_DIR / "verification_summary.json")

    candidates = indexed(candidate_rows, "candidate universe")
    readiness = indexed(readiness_rows, "feature readiness")
    latest_audit = indexed(latest_audit_rows, "latest253 audit")
    failures = indexed(failure_rows, "market readiness failures")
    if set(candidates) != set(readiness) or set(candidates) != set(latest_audit):
        raise ValueError("candidate/readiness/latest253 security sets differ")

    latest_snapshots: dict[str, dict] = {}
    monthly: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in iter_jsonl(root / C8_DIR / "canonical/feature_snapshots.jsonl"):
        snapshot = row["as_of_date"]
        security_id = row["security_id"]
        if security_id not in candidates:
            raise ValueError(f"feature snapshot outside candidate universe: {security_id}")
        if security_id in monthly[snapshot]:
            raise ValueError(f"duplicate monthly feature snapshot: {snapshot}/{security_id}")
        monthly[snapshot][security_id] = row
        if snapshot == SNAPSHOT_DATE:
            latest_snapshots[security_id] = row

    headline = {
        "candidate_count": len(candidates),
        "baseline_count": sum(
            row["candidate_source"] == "C5_BASELINE_500" for row in candidate_rows
        ),
        "complete_expansion_count": sum(
            row["candidate_source"] == "C7_COMPLETE_EXPANSION" for row in candidate_rows
        ),
        "deferred_expansion_count": len(deferred_rows),
        "feature_complete": sum(as_bool(row["feature_complete"]) for row in readiness_rows),
        "market_feature_ready_v2": sum(
            as_bool(row["market_feature_ready_v2"]) for row in readiness_rows
        ),
        "market_readiness_failures": sum(
            not as_bool(row["market_feature_ready_v2"]) for row in readiness_rows
        ),
        "latest253_complete": sum(
            as_bool(row["latest253_complete"]) for row in readiness_rows
        ),
        "latest253_incomplete": sum(
            not as_bool(row["latest253_complete"]) for row in readiness_rows
        ),
        "historical_identity_ready": sum(
            as_bool(row["historical_identity_ready"]) for row in readiness_rows
        ),
        "research_ready": sum(as_bool(row["research_ready"]) for row in readiness_rows),
    }
    if headline != EXPECTED_HEADLINE:
        raise ValueError(
            f"MANUAL_REVIEW_REQUIRED: scientific headline mismatch; STOP. {headline}"
        )
    verify_headline = verify_summary["headline"]
    headline_mapping = {
        "candidate_count": "candidate_count",
        "baseline_count": "baseline_candidate_count",
        "complete_expansion_count": "expansion_complete_count",
        "deferred_expansion_count": "deferred_expansion_count",
        "feature_complete": "feature_complete",
        "market_feature_ready_v2": "market_feature_ready_v2",
        "latest253_complete": "latest253_complete",
        "latest253_incomplete": "latest253_incomplete",
        "historical_identity_ready": "historical_identity_ready",
        "research_ready": "research_ready",
    }
    if any(headline[key] != verify_headline[remote] for key, remote in headline_mapping.items()):
        raise ValueError("MANUAL_REVIEW_REQUIRED: C8-VERIFY headline mismatch; STOP.")

    tradability = dict(
        sorted(Counter(row["trading_activity_status"] for row in readiness_rows).items())
    )
    if tradability != EXPECTED_TRADABILITY:
        raise ValueError(f"MANUAL_REVIEW_REQUIRED: tradability mismatch; STOP. {tradability}")

    source_stats = []
    for source in ("C5_BASELINE_500", "C7_COMPLETE_EXPANSION"):
        ids = [sid for sid, row in candidates.items() if row["candidate_source"] == source]
        source_stats.append({
            "candidate_source": source,
            "candidate_count": len(ids),
            "feature_complete": sum(as_bool(readiness[sid]["feature_complete"]) for sid in ids),
            "market_ready": sum(
                as_bool(readiness[sid]["market_feature_ready_v2"]) for sid in ids
            ),
            "latest253_complete": sum(
                as_bool(readiness[sid]["latest253_complete"]) for sid in ids
            ),
            "latest253_incomplete": sum(
                not as_bool(readiness[sid]["latest253_complete"]) for sid in ids
            ),
            "ACTIVE": sum(
                readiness[sid]["trading_activity_status"] == "ACTIVE" for sid in ids
            ),
            "OBSERVED_ZERO_VOLUME": sum(
                readiness[sid]["trading_activity_status"] == "OBSERVED_ZERO_VOLUME"
                for sid in ids
            ),
            "UNKNOWN": sum(
                readiness[sid]["trading_activity_status"] == "UNKNOWN" for sid in ids
            ),
            "market_readiness_rate": round(
                100
                * sum(as_bool(readiness[sid]["market_feature_ready_v2"]) for sid in ids)
                / len(ids),
                6,
            ),
        })
    source_by_name = {row["candidate_source"]: row for row in source_stats}
    if (
        source_by_name["C5_BASELINE_500"]["market_ready"] != 490
        or source_by_name["C7_COMPLETE_EXPANSION"]["market_ready"] != 415
    ):
        raise ValueError("MANUAL_REVIEW_REQUIRED: baseline/expansion readiness mismatch; STOP.")

    exchange_stats = []
    for exchange in sorted({row["exchange"] for row in candidate_rows}):
        ids = [sid for sid, row in candidates.items() if row["exchange"] == exchange]
        ready = sum(as_bool(readiness[sid]["market_feature_ready_v2"]) for sid in ids)
        exchange_stats.append({
            "exchange": exchange,
            "candidate_count": len(ids),
            "feature_complete": sum(as_bool(readiness[sid]["feature_complete"]) for sid in ids),
            "market_ready": ready,
            "market_not_ready": len(ids) - ready,
            "market_readiness_rate": round(100 * ready / len(ids), 6),
        })

    feature_coverage = []
    for feature in REQUIRED_FEATURES:
        available = sum(
            sid in latest_snapshots and latest_snapshots[sid].get(feature) is not None
            for sid in candidates
        )
        feature_coverage.append({
            "feature": feature,
            "available": available,
            "missing": len(candidates) - available,
            "available_percentage": round(100 * available / len(candidates), 6),
            "denominator": len(candidates),
            "snapshot_date": SNAPSHOT_DATE,
        })

    primary_blockers = Counter(row["primary_market_blocker"] for row in failure_rows)
    if dict(primary_blockers) != EXPECTED_PRIMARY_BLOCKERS:
        raise ValueError(
            f"MANUAL_REVIEW_REQUIRED: market blocker mismatch; STOP. {primary_blockers}"
        )
    if [row["ticker"] for row in failure_rows if row["primary_market_blocker"]
            == "NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE"] != ["GTX"]:
        raise ValueError("MANUAL_REVIEW_REQUIRED: GTX no-snapshot assertion failed; STOP.")

    complete_not_ready = tuple(sorted(
        row["ticker"] for row in failure_rows
        if as_bool(row["feature_complete"])
        and not as_bool(row["market_feature_ready_v2"])
    ))
    if complete_not_ready != EXPECTED_COMPLETE_NOT_READY:
        raise ValueError("MANUAL_REVIEW_REQUIRED: complete-not-ready set mismatch; STOP.")

    latest_blockers: dict[str, dict[str, int]] = {}
    for blocker in EXPECTED_LATEST_BLOCKERS:
        rows = [row for row in incomplete_rows if blocker in row["blocker_codes"].split("|")]
        session_field = (
            "calendar_uncertain_253"
            if blocker == "CALENDAR_UNCERTAIN"
            else "boundary_sessions_253"
        )
        latest_blockers[blocker] = {
            "security_count": len(rows),
            "session_count": sum(int(row[session_field]) for row in rows),
        }
    if latest_blockers != EXPECTED_LATEST_BLOCKERS:
        raise ValueError(
            f"MANUAL_REVIEW_REQUIRED: latest253 blockers mismatch; STOP. {latest_blockers}"
        )

    monthly_rows = []
    for snapshot in sorted(monthly):
        rows = monthly[snapshot]
        ids = sorted(rows)
        baseline_ids = [
            sid for sid in ids if candidates[sid]["candidate_source"] == "C5_BASELINE_500"
        ]
        expansion_ids = [
            sid for sid in ids
            if candidates[sid]["candidate_source"] == "C7_COMPLETE_EXPANSION"
        ]
        monthly_rows.append({
            "snapshot_date": snapshot,
            "candidate_rows": len(ids),
            "feature_complete": sum(as_bool(rows[sid]["feature_complete"]) for sid in ids),
            "market_feature_ready_v2": sum(
                as_bool(rows[sid]["market_feature_ready"]) for sid in ids
            ),
            "baseline_rows": len(baseline_ids),
            "baseline_ready": sum(
                as_bool(rows[sid]["market_feature_ready"]) for sid in baseline_ids
            ),
            "expansion_rows": len(expansion_ids),
            "expansion_ready": sum(
                as_bool(rows[sid]["market_feature_ready"]) for sid in expansion_ids
            ),
        })
    dates = [row["snapshot_date"] for row in monthly_rows]
    if dates != sorted(set(dates)) or dates[-1] != SNAPSHOT_DATE:
        raise ValueError("monthly readiness dates are not ordered/unique or latest is wrong")
    if (
        monthly_rows[-1]["feature_complete"] != 922
        or monthly_rows[-1]["market_feature_ready_v2"] != 905
    ):
        raise ValueError("latest monthly readiness does not reproduce verified headline")

    per_security = []
    for sid in sorted(candidates):
        candidate = candidates[sid]
        ready = readiness[sid]
        audit = latest_audit[sid]
        failure = failures.get(sid, {})
        snapshot = latest_snapshots.get(sid)
        row = {
            "security_id": sid,
            "ticker": candidate["ticker"],
            "exchange": candidate["exchange"],
            "candidate_source": candidate["candidate_source"],
            "snapshot_date": SNAPSHOT_DATE,
            "feature_snapshot_present": snapshot is not None,
            "feature_complete": as_bool(ready["feature_complete"]),
            "market_feature_ready_v2": as_bool(ready["market_feature_ready_v2"]),
            "latest253_complete": as_bool(ready["latest253_complete"]),
            "trading_activity_status": ready["trading_activity_status"],
            "historical_identity_ready": as_bool(ready["historical_identity_ready"]),
            "research_ready": as_bool(ready["research_ready"]),
            "primary_market_blocker": failure.get("primary_market_blocker", ""),
            "all_market_blockers": failure.get("all_market_blockers", ""),
            "missing_required_features": ready["missing_required_features"],
            "observed_valid_253": int(audit["observed_valid_253"]),
            "observed_zero_volume_253": int(audit["observed_zero_volume_253"]),
            "calendar_uncertain_253": int(audit["calendar_uncertain_253"]),
            "boundary_sessions_253": int(audit["boundary_sessions_253"]),
        }
        for feature in REQUIRED_FEATURES:
            row[f"{feature}_available"] = bool(
                snapshot is not None and snapshot.get(feature) is not None
            )
        per_security.append(row)

    funnel = [
        {"funnel": "market_foundation", "stage": "candidate", "count": 952, "denominator": 952},
        {"funnel": "market_foundation", "stage": "feature_complete", "count": 922, "denominator": 952},
        {"funnel": "market_foundation", "stage": "market_ready", "count": 905, "denominator": 952},
        {"funnel": "expansion_acquisition", "stage": "selected", "count": 600, "denominator": 600},
        {"funnel": "expansion_acquisition", "stage": "complete", "count": 452, "denominator": 600},
        {"funnel": "expansion_acquisition", "stage": "deferred", "count": 148, "denominator": 600},
    ]
    blocker_summary = [
        {
            "section": "market_readiness_primary",
            "blocker": blocker,
            "security_count": count,
            "session_count": "",
            "semantics": "primary mutually exclusive cause",
        }
        for blocker, count in sorted(primary_blockers.items())
    ] + [
        {
            "section": "latest253_incomplete",
            "blocker": blocker,
            "security_count": values["security_count"],
            "session_count": values["session_count"],
            "semantics": (
                "calendar evidence is not official-authoritative"
                if blocker == "CALENDAR_UNCERTAIN"
                else "identity or provider observation boundary; not listing proof"
            ),
        }
        for blocker, values in sorted(latest_blockers.items())
    ]

    input_paths = (
        C8_DIR / "manifest.json",
        C8_DIR / "candidate_universe.csv",
        C8_DIR / "deferred_expansion.csv",
        C8_DIR / "feature_readiness.csv",
        C8_DIR / "latest253_session_audit.csv",
        C8_DIR / "canonical/feature_snapshots.jsonl",
        VERIFY_DIR / "manifest.json",
        VERIFY_DIR / "verification_summary.json",
        VERIFY_DIR / "market_readiness_failures.csv",
        VERIFY_DIR / "latest253_incomplete.csv",
        R1_DIR / "manifest.json",
        Path("configs/data/cafef_c8_complete_only_v1.json"),
        Path("configs/data/identity_review_v1.json"),
    )
    input_hashes = {
        relative.as_posix(): sha256_file(root / relative) for relative in input_paths
    }
    return {
        "integrity": integrity,
        "headline": headline,
        "tradability": tradability,
        "feature_coverage": feature_coverage,
        "source_stats": source_stats,
        "exchange_stats": exchange_stats,
        "monthly_rows": monthly_rows,
        "per_security": per_security,
        "funnel": funnel,
        "blocker_summary": blocker_summary,
        "primary_blockers": dict(sorted(primary_blockers.items())),
        "latest_blockers": latest_blockers,
        "complete_not_ready": list(complete_not_ready),
        "latest253_incomplete_tickers": sorted(row["ticker"] for row in incomplete_rows),
        "input_hashes": input_hashes,
    }


def configure_plotting() -> None:
    plt.rcParams.update({
        "figure.dpi": 100,
        "savefig.dpi": 120,
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def save_plot(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", metadata={"Software": "DELTA M1-REPORT"})
    plt.close(fig)


def bar_labels(axis, bars) -> None:
    axis.bar_label(bars, padding=3, fontsize=8)


def create_plots(output: Path, data: dict) -> None:
    configure_plotting()
    plots = output / "plots"
    plots.mkdir()

    fig, ax = plt.subplots(figsize=(7, 4))
    labels = ["C5 baseline\n(candidate)", "C7 complete\n(candidate)", "C7 deferred\n(not candidate)"]
    values = [500, 452, 148]
    bars = ax.bar(labels, values, color=["#3465a4", "#4e9a06", "#888a85"])
    bar_labels(ax, bars)
    ax.set_title("Universe composition — C8 verified state")
    ax.set_ylabel("Securities")
    ax.set_ylim(0, 650)
    ax.text(2, 35, "Separate 600-selection denominator", ha="center", fontsize=8)
    save_plot(fig, plots / "universe_composition.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    rows = [row for row in data["funnel"] if row["funnel"] == "market_foundation"]
    bars = ax.bar([row["stage"] for row in rows], [row["count"] for row in rows],
                  color=["#3465a4", "#75507b", "#4e9a06"])
    bar_labels(ax, bars)
    ax.set_title(f"Market-foundation readiness — denominator 952 ({SNAPSHOT_DATE})")
    ax.set_ylabel("Securities")
    ax.set_ylim(0, 1020)
    save_plot(fig, plots / "readiness_funnel.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    rows = data["feature_coverage"]
    available = [row["available"] for row in rows]
    missing = [row["missing"] for row in rows]
    bars = ax.barh([row["feature"] for row in rows], available, color="#4e9a06", label="Available")
    ax.barh([row["feature"] for row in rows], missing, left=available,
            color="#cc0000", label="Missing")
    ax.set_title(f"Required feature coverage — 952 candidates ({SNAPSHOT_DATE})")
    ax.set_xlabel("Securities")
    ax.set_xlim(0, 1000)
    ax.legend(loc="lower right")
    for bar, value in zip(bars, available):
        ax.text(value - 8, bar.get_y() + bar.get_height() / 2, str(value),
                va="center", ha="right", color="white", fontsize=8)
    save_plot(fig, plots / "required_feature_coverage.png")

    fig, ax = plt.subplots(figsize=(6.5, 4))
    bars = ax.bar(["Complete", "Incomplete"], [922, 30], color=["#4e9a06", "#cc0000"])
    bar_labels(ax, bars)
    ax.set_title(f"Latest-253 status — 952 candidates ({SNAPSHOT_DATE})")
    ax.set_ylabel("Securities")
    ax.text(
        0.5, 0.89,
        "Calendar evidence is not official-authoritative",
        transform=ax.transAxes, ha="center", fontsize=8,
    )
    save_plot(fig, plots / "latest253_status.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    blockers = data["primary_blockers"]
    labels = [
        "Insufficient latest-253\nreal observations",
        "Insufficient three-year\nhistory",
        "No feature snapshot",
    ]
    values = [
        blockers["INSUFFICIENT_LATEST253_REAL_OBSERVATIONS"],
        blockers["INSUFFICIENT_THREE_YEAR_HISTORY"],
        blockers["NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE"],
    ]
    bars = ax.bar(labels, values, color=["#cc0000", "#f57900", "#888a85"])
    bar_labels(ax, bars)
    ax.set_title(f"Primary market-readiness blockers — 47 exclusions ({SNAPSHOT_DATE})")
    ax.set_ylabel("Securities")
    save_plot(fig, plots / "market_readiness_blockers.png")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    rows = data["monthly_rows"]
    dates = [row["snapshot_date"] for row in rows]
    x = list(range(len(rows)))
    ax.plot(x, [row["candidate_rows"] for row in rows], label="Candidate rows", linewidth=1.8)
    ax.plot(x, [row["feature_complete"] for row in rows], label="Feature complete", linewidth=1.8)
    ax.plot(x, [row["market_feature_ready_v2"] for row in rows], label="Market ready", linewidth=2.2)
    ticks = list(range(0, len(x), 12))
    if x[-1] not in ticks:
        ticks.append(x[-1])
    ax.set_xticks(ticks, [dates[i][:7] for i in ticks], rotation=35, ha="right")
    ax.set_title("Point-in-time monthly market readiness — existing C8 snapshots only")
    ax.set_xlabel("Snapshot month")
    ax.set_ylabel("Securities with a snapshot row")
    ax.legend()
    ax.text(
        0.01, 0.02,
        "No terminal-905 membership filter; descriptive, not a clustering result.",
        transform=ax.transAxes, fontsize=8,
    )
    save_plot(fig, plots / "monthly_market_readiness.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    labels = ["ACTIVE", "OBSERVED_ZERO_VOLUME", "UNKNOWN"]
    values = [data["tradability"][label] for label in labels]
    bars = ax.bar(labels, values, color=["#4e9a06", "#f57900", "#888a85"])
    bar_labels(ax, bars)
    ax.set_title(f"Tradability distribution — separate from market readiness ({SNAPSHOT_DATE})")
    ax.set_ylabel("Securities")
    save_plot(fig, plots / "tradability_distribution.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    metrics = ("candidate_count", "feature_complete", "market_ready",
               "latest253_complete", "latest253_incomplete")
    labels = ("Candidate", "Feature complete", "Market ready",
              "Latest-253 complete", "Latest-253 incomplete")
    baseline = next(row for row in data["source_stats"]
                    if row["candidate_source"] == "C5_BASELINE_500")
    expansion = next(row for row in data["source_stats"]
                     if row["candidate_source"] == "C7_COMPLETE_EXPANSION")
    x = list(range(len(metrics)))
    width = 0.36
    left = ax.bar([i - width / 2 for i in x], [baseline[key] for key in metrics],
                  width, label="C5 baseline", color="#3465a4")
    right = ax.bar([i + width / 2 for i in x], [expansion[key] for key in metrics],
                   width, label="C7 complete expansion", color="#4e9a06")
    bar_labels(ax, left)
    bar_labels(ax, right)
    ax.set_xticks(x, labels, rotation=20, ha="right")
    ax.set_ylabel("Securities")
    ax.set_title(f"Baseline vs complete expansion — descriptive only ({SNAPSHOT_DATE})")
    ax.legend()
    save_plot(fig, plots / "baseline_vs_expansion.png")


def notebook_cell(cell_type: str, source: str) -> dict:
    cell = {"cell_type": cell_type, "metadata": {}, "source": source.splitlines(keepends=True)}
    if cell_type == "code":
        cell.update({"execution_count": None, "outputs": []})
    return cell


def notebook_document() -> dict:
    cells = [
        notebook_cell("markdown", """# M1 CafeF Market Foundation — Inspection Notebook

**Purpose:** inspect the immutable `m1-market-foundation-v1` report artifact.

**Source of truth:** report artifact files, not this notebook.

> M1 MARKET DATA FOUNDATION: **COMPLETE FOR MARKET-ONLY EXPERIMENT PREPARATION**
> Strict research gate: **NOT READY**. Market feature readiness, tradability,
> historical identity readiness and research readiness are distinct gates.
"""),
        notebook_cell("code", """from pathlib import Path
import json
import pandas as pd
from IPython.display import Image, display

REPORT_DIR = Path("artifacts/reports/m1-market-foundation-v1")
if not REPORT_DIR.is_dir():
    for parent in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
        candidate = parent / "artifacts/reports/m1-market-foundation-v1"
        if candidate.is_dir():
            REPORT_DIR = candidate
            break
if not REPORT_DIR.is_dir():
    raise FileNotFoundError(f"Explicit report artifact is missing: {REPORT_DIR.resolve()}")
print(f"Report directory: {REPORT_DIR.resolve()}")
"""),
        notebook_cell("code", """report = json.loads((REPORT_DIR / "report.json").read_text(encoding="utf-8"))
print("Artifact:", report["artifact_id"])
print("Stage:", report["stage"])
print("Snapshot:", report["snapshot_date"])
print("Integrity:", report["integrity"]["status"])
print("Network requests:", report["network_requests"])
"""),
        notebook_cell("markdown", """## Integrity and provenance

The generator verifies the parent C8, C8-VERIFY and R1 manifests before writing
this report. C8 is not rerun.
"""),
        notebook_cell("code", """pd.Series(report["parent_manifests"], name="sha256").to_frame()
"""),
        notebook_cell("markdown", """## M1 readiness summary

Market-only experiment preparation may proceed under an explicit protocol.
This does not authorize research-ready promotion, a backtest, investment claims,
or a final research-universe claim.
"""),
        notebook_cell("code", """headline = pd.Series(report["headline"], name="count").to_frame()
display(headline)
print("\nMarket ready != tradability != historical identity ready != research ready")
"""),
        notebook_cell("markdown", "## Required feature coverage"),
        notebook_cell("code", """feature_coverage = pd.read_csv(REPORT_DIR / "feature_coverage.csv")
display(feature_coverage)
"""),
        notebook_cell("markdown", "## Source and exchange composition"),
        notebook_cell("code", """by_source = pd.read_csv(REPORT_DIR / "composition_by_source.csv")
by_exchange = pd.read_csv(REPORT_DIR / "composition_by_exchange.csv")
display(by_source)
display(by_exchange)
print("Descriptive composition only; neither cohort is claimed statistically representative.")
"""),
        notebook_cell("markdown", "## Pre-generated deterministic charts"),
        notebook_cell("code", """plot_names = [
    "universe_composition.png", "readiness_funnel.png",
    "required_feature_coverage.png", "latest253_status.png",
    "market_readiness_blockers.png", "monthly_market_readiness.png",
    "tradability_distribution.png", "baseline_vs_expansion.png",
]
for name in plot_names:
    print(name)
    display(Image(filename=str(REPORT_DIR / "plots" / name)))
"""),
        notebook_cell("markdown", "## Per-security inspection"),
        notebook_cell("code", """per_security = pd.read_csv(REPORT_DIR / "per_security.csv")
print("Rows:", len(per_security))
display(per_security.head())
"""),
        notebook_cell("markdown", """## Latest-253 incomplete securities

`CALENDAR_UNCERTAIN` is not a provider gap, suspension, delisting or
not-listed claim. Calendar evidence is not official-authoritative.
"""),
        notebook_cell("code", """incomplete = per_security.loc[~per_security["latest253_complete"]]
display(incomplete[[
    "ticker", "exchange", "candidate_source", "calendar_uncertain_253",
    "boundary_sessions_253", "primary_market_blocker",
]].sort_values("ticker"))
print("Incomplete count:", len(incomplete))
"""),
        notebook_cell("markdown", "## Market-ready securities"),
        notebook_cell("code", """market_ready = per_security.loc[per_security["market_feature_ready_v2"]]
print(f"Market ready: {len(market_ready)} / {len(per_security)}")
display(market_ready[[
    "ticker", "exchange", "candidate_source", "trading_activity_status"
]].head(30))
"""),
        notebook_cell("markdown", "## Market-readiness failures"),
        notebook_cell("code", """failures = per_security.loc[~per_security["market_feature_ready_v2"]]
display(failures[[
    "ticker", "exchange", "candidate_source", "feature_complete",
    "latest253_complete", "primary_market_blocker", "all_market_blockers",
]].sort_values(["primary_market_blocker", "ticker"]))
"""),
        notebook_cell("markdown", "## Feature-complete but not market-ready"),
        notebook_cell("code", """complete_not_ready = per_security.loc[
    per_security["feature_complete"] & ~per_security["market_feature_ready_v2"]
]
display(complete_not_ready[[
    "ticker", "exchange", "candidate_source", "primary_market_blocker"
]].sort_values("ticker"))
"""),
        notebook_cell("markdown", """## Monthly readiness trajectory

Rows are derived from each existing C8 monthly feature snapshot. Earlier months
are **not** filtered by terminal 2026-08-28 membership in the 905-security set.
This is descriptive evidence for PIT-safe M2-PREP window design.
"""),
        notebook_cell("code", """monthly = pd.read_csv(REPORT_DIR / "monthly_market_readiness.csv")
display(monthly)
print("Range:", monthly["snapshot_date"].iloc[0], "→", monthly["snapshot_date"].iloc[-1])
"""),
        notebook_cell("markdown", "## Blocker summary"),
        notebook_cell("code", """blockers = pd.read_csv(REPORT_DIR / "blocker_summary.csv")
display(blockers)
"""),
        notebook_cell("markdown", """## Historical pipeline continuity

**HISTORICAL PIPELINE REFERENCE ONLY:** the former KBS notebook described
500 selected securities, 614,430 daily rows and 169 latest market-feature-ready
securities. Do not interpret 169 → 905 as a direct improvement percentage:
provider, canonicalization, readiness semantics and universe changed materially.
"""),
        notebook_cell("markdown", """## Final M1 status

- **M1 MARKET DATA FOUNDATION:** COMPLETE FOR MARKET-ONLY EXPERIMENT PREPARATION
- **Strict research gate:** NOT READY
- **Current proposed latest-snapshot market-only universe:** 905 securities
- **historical_identity_ready:** 0
- **research_ready:** 0
- **Next stage:** M2-PREP — MARKET-ONLY EXPERIMENT PROTOCOL

This notebook authorizes neither backtest nor investment/final-universe claims.
"""),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def generate(root: Path, output: Path, notebook: Path) -> None:
    data = build_data(root)
    output_abs = root / output
    notebook_abs = root / notebook
    temp_parent = output_abs.parent
    temp_parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{ARTIFACT_ID}-", dir=temp_parent))
    try:
        create_plots(temp_dir, data)
        per_columns = (
            "security_id", "ticker", "exchange", "candidate_source", "snapshot_date",
            "feature_snapshot_present", "feature_complete", "market_feature_ready_v2",
            "latest253_complete", "trading_activity_status",
            "historical_identity_ready", "research_ready", "primary_market_blocker",
            "all_market_blockers", "missing_required_features",
            "observed_valid_253", "observed_zero_volume_253",
            "calendar_uncertain_253", "boundary_sessions_253",
            *(f"{feature}_available" for feature in REQUIRED_FEATURES),
        )
        write_csv(temp_dir / "per_security.csv", data["per_security"], per_columns)
        write_csv(
            temp_dir / "feature_coverage.csv",
            data["feature_coverage"],
            ("feature", "available", "missing", "available_percentage",
             "denominator", "snapshot_date"),
        )
        write_csv(
            temp_dir / "readiness_funnel.csv",
            data["funnel"],
            ("funnel", "stage", "count", "denominator"),
        )
        write_csv(
            temp_dir / "composition_by_source.csv",
            data["source_stats"],
            ("candidate_source", "candidate_count", "feature_complete", "market_ready",
             "latest253_complete", "latest253_incomplete", "ACTIVE",
             "OBSERVED_ZERO_VOLUME", "UNKNOWN", "market_readiness_rate"),
        )
        write_csv(
            temp_dir / "composition_by_exchange.csv",
            data["exchange_stats"],
            ("exchange", "candidate_count", "feature_complete", "market_ready",
             "market_not_ready", "market_readiness_rate"),
        )
        write_csv(
            temp_dir / "monthly_market_readiness.csv",
            data["monthly_rows"],
            ("snapshot_date", "candidate_rows", "feature_complete",
             "market_feature_ready_v2", "baseline_rows", "baseline_ready",
             "expansion_rows", "expansion_ready"),
        )
        write_csv(
            temp_dir / "blocker_summary.csv",
            data["blocker_summary"],
            ("section", "blocker", "security_count", "session_count", "semantics"),
        )
        report = {
            "artifact_id": ARTIFACT_ID,
            "stage": STAGE,
            "git_commit": SOURCE_COMMIT,
            "git_commit_semantics": "verified source parent commit before M1-REPORT",
            "snapshot_date": SNAPSHOT_DATE,
            "status": "PASS",
            "integrity": {"status": "PASS", **data["integrity"]},
            "parent_manifests": EXPECTED_PARENT_HASHES,
            "input_hashes": data["input_hashes"],
            "headline": data["headline"],
            "tradability": data["tradability"],
            "required_feature_coverage": data["feature_coverage"],
            "baseline_vs_expansion": data["source_stats"],
            "market_readiness_primary_blockers": data["primary_blockers"],
            "latest253_blockers": data["latest_blockers"],
            "latest253_incomplete_tickers": data["latest253_incomplete_tickers"],
            "feature_complete_not_market_ready_tickers": data["complete_not_ready"],
            "monthly_readiness": {
                "first_snapshot": data["monthly_rows"][0]["snapshot_date"],
                "last_snapshot": data["monthly_rows"][-1]["snapshot_date"],
                "snapshot_count": len(data["monthly_rows"]),
                "pit_semantics": (
                    "Each month uses rows present at that snapshot; no terminal-905 filter."
                ),
            },
            "gate_distinctions": (
                "MARKET_FEATURE_READY_V2 != TRADABILITY != "
                "HISTORICAL_IDENTITY_READY != RESEARCH_READY"
            ),
            "final_status": (
                "M1 MARKET DATA FOUNDATION: COMPLETE FOR MARKET-ONLY "
                "EXPERIMENT PREPARATION"
            ),
            "strict_research_gate": "NOT READY",
            "next_stage": "M2-PREP — MARKET-ONLY EXPERIMENT PROTOCOL",
            "network_requests": 0,
            "scope_confirmations": {
                "c8_rerun": False,
                "network_access": False,
                "supplemental_crawl": False,
                "clustering": False,
                "backtest": False,
                "identity_promoted": False,
                "research_ready_promoted": False,
            },
        }
        write_json(temp_dir / "report.json", report)
        outputs = {}
        for name in REPORT_FILES:
            outputs[name] = sha256_file(temp_dir / name)
        for name in PLOT_FILES:
            outputs[f"plots/{name}"] = sha256_file(temp_dir / "plots" / name)
        manifest = {
            "artifact_id": ARTIFACT_ID,
            "stage": STAGE,
            "git_commit": SOURCE_COMMIT,
            "git_commit_semantics": "verified source parent commit before M1-REPORT",
            "snapshot_date": SNAPSHOT_DATE,
            **EXPECTED_PARENT_HASHES,
            "input_hashes": data["input_hashes"],
            "outputs": dict(sorted(outputs.items())),
            "network_requests": 0,
        }
        write_json(temp_dir / "manifest.json", manifest)
        if output_abs.exists():
            shutil.rmtree(output_abs)
        temp_dir.replace(output_abs)
        notebook_abs.parent.mkdir(parents=True, exist_ok=True)
        write_json(notebook_abs, notebook_document())
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def verify_existing(root: Path, output: Path, notebook: Path) -> None:
    verify_inputs(root)
    directory = root / output
    manifest = read_json(directory / "manifest.json")
    if manifest.get("artifact_id") != ARTIFACT_ID or manifest.get("network_requests") != 0:
        raise ValueError("invalid M1 report manifest")
    for relative, expected in manifest["outputs"].items():
        if sha256_file(directory / relative) != expected:
            raise ValueError(f"M1 report output hash mismatch: {relative}")
    report = read_json(directory / "report.json")
    if report["headline"] != EXPECTED_HEADLINE or report["tradability"] != EXPECTED_TRADABILITY:
        raise ValueError("M1 report scientific counts changed")
    document = read_json(root / notebook)
    if document.get("nbformat") != 4:
        raise ValueError("inspection notebook is not valid nbformat 4 JSON")
    notebook_text = json.dumps(document).lower()
    forbidden = ("urlopen(", "requests.get(", "http://", "https://")
    if any(token in notebook_text for token in forbidden):
        raise ValueError("inspection notebook contains a network request or URL")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != root:
        raise SystemExit(f"run from repository root: {root}")
    if args.verify_existing:
        verify_existing(root, args.output_dir, args.notebook)
        print("M1 market-foundation report verification: PASS")
    else:
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", SOURCE_COMMIT, "HEAD"],
            check=False,
        )
        if ancestry.returncode != 0:
            raise SystemExit(
                "MANUAL_REVIEW_REQUIRED: verified source commit is not an ancestor "
                "of current HEAD"
            )
        generate(root, args.output_dir, args.notebook)
        print(f"Report artifact written: {args.output_dir}")
        print(f"Inspection notebook written: {args.notebook}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
