"""Export reviewable K=2 membership, profiles and fitted parameters for M2 Task 3.

Run from repo root. Reads only frozen development snapshots and verifies every
recomputed K=2 diagnostic against the completed Global K selection run.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.clustering.kmeans import fit_kmeans
from delta_t1.evaluation.cluster_metrics import cluster_metrics
from delta_t1.experiments.protocol import validate_protocol
from delta_t1.experiments.runner import prepare_m2_market_only_snapshots
from delta_t1.features.preprocessing import preprocess


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiments/m2_market_only_v1.json")
    parser.add_argument("--data-run", type=Path, default=ROOT / "artifacts/cafef_primary/cafef-c8-complete-only-v1")
    parser.add_argument("--selection-run", type=Path, default=ROOT / "artifacts/experiments/m2-task3-development-v1")
    parser.add_argument("--output", type=Path, required=True, help="New, nonexisting directory")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; select a new directory")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_protocol(config)
    decision = json.loads((args.selection_run / "global_k_decision.json").read_text(encoding="utf-8"))
    params = decision["parameters"]
    if (decision["status"] != "PROPOSED_MANUAL_REVIEW" or decision["proposed_global_k"] != 2
            or decision["count_rows"] != 105 or decision["count_ok"] != 105
            or decision["development_snapshots"] != config["development_snapshots"]
            or decision["k_range"] != config["clustering"]["k_range"]):
        raise ValueError("Selection decision is not the expected complete development K=2 proposal")
    if (sha256(args.config) != decision["config_sha256"]
            or sha256(args.data_run / "manifest.json") != decision["source_manifest_sha256"]
            or sha256(args.selection_run / "per_snapshot_k_metrics.csv") != decision["per_snapshot_sha256"]
            or sha256(args.selection_run / "aggregate_by_k.csv") != decision["aggregate_sha256"]):
        raise ValueError("Selection run or input checksums changed")
    with (args.selection_run / "per_snapshot_k_metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
        expected = {r["snapshot"]: r for r in csv.DictReader(stream) if r["k"] == "2"}
    days = config["development_snapshots"]
    if len(expected) != len(days) or set(expected) != set(days):
        raise ValueError("K=2 diagnostic rows incomplete")
    source, prepared = prepare_m2_market_only_snapshots(args.data_run, config, days)
    if source["outputs"]["canonical/feature_snapshots.jsonl"] != decision["feature_snapshot_sha256"]:
        raise ValueError("Feature snapshot checksum changed")
    features = config["clustering"]["features"]
    assignments, profiles, checks = [], [], []
    models = {}
    for snapshot in prepared:
        day, rows = snapshot["snapshot_date"], snapshot["rows"]
        if snapshot["status"] != "ready" or len(rows) != int(expected[day]["eligible_count"]):
            raise ValueError("Snapshot not ready or eligible count changed: " + day)
        vectors, scaler = preprocess(rows, dict(features=features,
            winsor_quantile=config["clustering"]["winsor_quantile"],
            scaling=config["clustering"]["scaling"], reduction={"method": "none"}))
        fit = fit_kmeans(vectors, 2, params["seed"], params["n_init"], params["max_iter"])
        metric = cluster_metrics(vectors, fit)
        prior = expected[day]
        if prior["status"] != "ok":
            raise ValueError("Prior K=2 row not valid: " + day)
        for name in ("silhouette", "davies_bouldin", "calinski_harabasz", "inertia", "cluster_balance"):
            if abs(metric[name] - float(prior[name])) > 1e-10:
                raise ValueError(f"Recomputed {name} differs at {day}")
        if (metric["cluster_sizes"] != {int(k): v for k, v in json.loads(prior["cluster_sizes"]).items()}
                or str(metric["converged"]) != prior["converged"]):
            raise ValueError("Recomputed sizes or convergence differs: " + day)
        sizes = Counter(fit["labels"])
        ordered = sorted(sizes, key=lambda label: (sizes[label], label))
        class_of = {ordered[0]: "small", ordered[1]: "large"}
        for row, label in zip(rows, fit["labels"]):
            assignments.append(dict(snapshot=day, security_id=row["security_id"],
                                    raw_cluster_id=label, size_class=class_of[label]))
        for label in sorted(sizes):
            members = [row for row, membership in zip(rows, fit["labels"]) if membership == label]
            profile = dict(snapshot=day, raw_cluster_id=label,
                           size_class=class_of[label], count=len(members))
            for feature in features:
                profile[feature + "_median"] = median(row[feature] for row in members)
            profiles.append(profile)
        models[day] = dict(snapshot=day, k=2, parameters=params,
                           feature_order=features, scaler=scaler,
                           centroids_scaled=fit["centroids"], iterations=fit["iterations"],
                           inertia=fit["inertia"], cluster_sizes=dict(sizes))
        checks.append(dict(snapshot=day, eligible_count=len(rows),
                           small_count=sizes[ordered[0]], large_count=sizes[ordered[1]],
                           metrics_match=True))
        print(f"{day}: verified K=2, {sizes[ordered[0]]}/{sizes[ordered[1]]}", flush=True)
    args.output.mkdir(parents=True)
    (args.output / "models").mkdir()
    write_csv(args.output / "assignments.csv",
              ["snapshot", "security_id", "raw_cluster_id", "size_class"], assignments)
    write_csv(args.output / "small_cluster_members.csv",
              ["snapshot", "security_id", "raw_cluster_id", "size_class"],
              [r for r in assignments if r["size_class"] == "small"])
    write_csv(args.output / "cluster_profiles.csv",
              ["snapshot", "raw_cluster_id", "size_class", "count"] + [f + "_median" for f in features], profiles)
    write_csv(args.output / "validation.csv",
              ["snapshot", "eligible_count", "small_count", "large_count", "metrics_match"], checks)
    for day, model in models.items():
        (args.output / "models" / (day + ".json")).write_text(
            json.dumps(model, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    files = sorted(p for p in args.output.rglob("*") if p.is_file())
    manifest = dict(stage="M2_TASK_3_K2_EVIDENCE_DEVELOPMENT", status="REVIEW_EVIDENCE_ONLY",
                    selected_k_candidate=2, review_status=decision["status"],
                    development_snapshots=days, total_assignments=len(assignments),
                    parameters=params, config_sha256=decision["config_sha256"],
                    selection_decision_sha256=sha256(args.selection_run / "global_k_decision.json"),
                    source_manifest_sha256=decision["source_manifest_sha256"],
                    script_sha256=sha256(__file__),
                    output_sha256={str(p.relative_to(args.output)): sha256(p) for p in files})
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(args.output), snapshots=len(days),
                          assignments=len(assignments), status=manifest["status"])), flush=True)


if __name__ == "__main__":
    main()
