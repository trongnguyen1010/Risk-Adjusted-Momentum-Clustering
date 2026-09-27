"""M2 Task 3: development-only K selection over verified C8 snapshots.

Run from the repository root with PYTHONPATH=src. This script produces a
reviewable candidate decision; it does not open holdout or run a backtest.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.clustering.kmeans import fit_kmeans
from delta_t1.evaluation.cluster_metrics import cluster_metrics
from delta_t1.experiments.protocol import validate_protocol
from delta_t1.experiments.runner import prepare_m2_market_only_snapshots
from delta_t1.features.preprocessing import preprocess


FIELDS = (
    "snapshot", "k", "eligible_count", "status", "reason", "silhouette",
    "davies_bouldin", "calinski_harabasz", "inertia", "cluster_balance",
    "cluster_sizes", "converged",
)
AGG_FIELDS = (
    "k", "completed_snapshots", "median_silhouette", "median_davies_bouldin",
    "median_calinski_harabasz", "median_inertia", "median_cluster_balance",
)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path,
                        default=ROOT / "configs/experiments/m2_market_only_v1.json")
    parser.add_argument("--data-run", type=Path,
                        default=ROOT / "artifacts/cafef_primary/cafef-c8-complete-only-v1")
    parser.add_argument("--output", type=Path, required=True,
                        help="New, nonexisting output directory")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--n-init", type=int, required=True)
    parser.add_argument("--max-iter", type=int, required=True)
    parser.add_argument("--smoke", action="store_true",
                        help="Test first development snapshot and K=2 only; no K decision")
    args = parser.parse_args()
    if args.n_init < 1 or args.max_iter < 1:
        parser.error("--n-init and --max-iter must be positive")
    if args.output.exists():
        parser.error("output already exists; use a new run directory")

    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_protocol(config)
    if config["portfolio_evaluation"]["enabled"] is not False:
        raise ValueError("portfolio evaluation must remain disabled")
    days = config["development_snapshots"][:1] if args.smoke else config["development_snapshots"]
    ks = [2] if args.smoke else config["clustering"]["k_range"]
    source, prepared = prepare_m2_market_only_snapshots(args.data_run, config, days)
    if len(prepared) != len(days):
        raise ValueError("development snapshot count mismatch")

    records = []
    for snapshot in prepared:
        day = snapshot["snapshot_date"]
        count = snapshot["eligible_count"]
        if snapshot["status"] == "ready":
            vectors, _scaler = preprocess(snapshot["rows"], dict(
                features=config["clustering"]["features"],
                winsor_quantile=config["clustering"]["winsor_quantile"],
                scaling=config["clustering"]["scaling"],
                reduction={"method": "none"},
            ))
        for k in ks:
            row = dict(snapshot=day, k=k, eligible_count=count,
                       status="skipped" if snapshot["status"] != "ready" else "ok",
                       reason=snapshot["reason"] or "")
            if row["status"] == "ok":
                try:
                    fit = fit_kmeans(vectors, k, args.seed, args.n_init, args.max_iter)
                    result = cluster_metrics(vectors, fit)
                    row.update({field: result[field] for field in (
                        "silhouette", "davies_bouldin", "calinski_harabasz",
                        "inertia", "cluster_balance", "converged",
                    )})
                    row["cluster_sizes"] = json.dumps(result["cluster_sizes"], sort_keys=True)
                except ValueError as exc:
                    row.update(status="unavailable", reason=str(exc))
            records.append(row)
            print(f"{day} K={k}: {row['status']}", flush=True)

    expected = len(days) * len(ks)
    if len(records) != expected:
        raise ValueError("missing snapshot x K diagnostics")
    aggregate = []
    for k in ks:
        available = [row for row in records if row["k"] == k and row["status"] == "ok"]
        summary = dict(k=k, completed_snapshots=len(available))
        for metric in ("silhouette", "davies_bouldin", "calinski_harabasz",
                       "inertia", "cluster_balance"):
            values = [row[metric] for row in available if row.get(metric) is not None]
            summary["median_" + metric] = median(values) if len(values) == len(available) and values else None
        aggregate.append(summary)

    complete = not args.smoke and all(row["status"] == "ok" for row in records)
    winner = None
    if complete:
        best_silhouette = max(row["median_silhouette"] for row in aggregate)
        tied = [row for row in aggregate if row["median_silhouette"] == best_silhouette]
        best_db = min(row["median_davies_bouldin"] for row in tied)
        tied = [row for row in tied if row["median_davies_bouldin"] == best_db]
        if len(tied) == 1:
            winner = tied[0]["k"]

    args.output.mkdir(parents=True)
    write_csv(args.output / "per_snapshot_k_metrics.csv", FIELDS, records)
    write_csv(args.output / "aggregate_by_k.csv", AGG_FIELDS, aggregate)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    decision = dict(
        stage="M2_TASK_3_GLOBAL_K_DEVELOPMENT",
        status=("SMOKE_ONLY" if args.smoke else
                "INCOMPLETE_MANUAL_REVIEW" if not complete or winner is None else
                "PROPOSED_MANUAL_REVIEW"),
        proposed_global_k=winner,
        review_note="Freeze only after reviewing parameters, complete diagnostics, and near-tie judgement.",
        rule=config["clustering"]["global_k_selection"],
        development_snapshots=days, k_range=ks,
        count_rows=len(records), count_ok=sum(row["status"] == "ok" for row in records),
        parameters=dict(seed=args.seed, n_init=args.n_init, max_iter=args.max_iter),
        git_commit=commit,
        config_sha256=sha256(args.config),
        source_manifest_sha256=sha256(args.data_run / "manifest.json"),
        feature_snapshot_sha256=source["outputs"]["canonical/feature_snapshots.jsonl"],
        script_sha256=sha256(__file__),
        per_snapshot_sha256=sha256(args.output / "per_snapshot_k_metrics.csv"),
        aggregate_sha256=sha256(args.output / "aggregate_by_k.csv"),
    )
    (args.output / "global_k_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(dict(status=decision["status"], proposed_global_k=winner,
                          output=str(args.output)), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
