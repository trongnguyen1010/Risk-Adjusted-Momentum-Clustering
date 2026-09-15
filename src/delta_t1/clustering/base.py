"""Common snapshot-clustering interface and shared cross-section orchestration."""
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Callable

from ..evaluation.cluster_metrics import cluster_metrics
from ..features.preprocessing import preprocess
from ..features.registry import FEATURE_REGISTRY


@dataclass(frozen=True)
class ClusteringAlgorithm:
    name: str
    fit_snapshot: Callable[[list[dict], dict], dict]
    validate_config: Callable[[dict], None]


def validate_k_config(config: dict) -> None:
    if not 2 <= config["k"] <= 10 or not config["k_range"] or any(
            not 2 <= value <= 10 for value in config["k_range"]):
        raise ValueError("cluster range must be 2..10")


def build_snapshot(rows: list[dict], config: dict,
                   fit_vectors: Callable[[list[list[float]], int, dict], dict]) -> dict:
    """Apply shared validation, preprocessing, metrics and profile construction."""
    FEATURE_REGISTRY.require_cluster_eligible(config["features"])
    rows = sorted((row for row in rows if row["eligibility"]), key=lambda row: row["security_id"])
    if len({row["as_of_date"] for row in rows}) != 1 or len({row["security_id"] for row in rows}) != len(rows):
        raise ValueError("one nonempty unique cross-section required")
    if len({row.get("adjustment_basis") for row in rows}) > 1:
        raise ValueError("mixed return conventions in cross-section")
    vectors, scaler = preprocess(rows, config)
    fits, diagnostics = {}, []
    for k in sorted(set(config["k_range"] + [config["k"]])):
        try:
            fits[k] = fit_vectors(vectors, k, config)
            diagnostics.append(cluster_metrics(vectors, fits[k]))
        except ValueError as exc:
            diagnostics.append(dict(k=k, status="unavailable", reason=str(exc)))
    if config["k"] not in fits:
        raise ValueError("selected k unavailable: insufficient sample/distinct points/convergence")
    fit = fits[config["k"]]
    momentum_name, risk_name = config["momentum_feature"], config["risk_feature"]
    profiles = []
    for cluster in range(config["k"]):
        members = [row for row, label in zip(rows, fit["labels"]) if label == cluster]
        centroid = {name: mean(row[name] for row in members)
                    for name in set(config["features"] + [momentum_name, risk_name])}
        semantic = (
            ("High" if centroid[momentum_name] >= median(row[momentum_name] for row in rows) else "Low")
            + " Momentum / "
            + ("High" if centroid[risk_name] >= median(row[risk_name] for row in rows) else "Low")
            + " Risk"
        )
        profiles.append(dict(raw_cluster_id=cluster, semantic_label=semantic,
                             size=len(members), centroid=centroid))
    ranking = sorted(profiles, key=lambda profile: (-profile["centroid"][momentum_name],
                                                    profile["centroid"][risk_name],
                                                    profile["raw_cluster_id"]))
    for rank, profile in enumerate(ranking):
        profile["economic_rank"] = rank
    return dict(
        snapshot_date=rows[0]["as_of_date"],
        rows=rows,
        labels=fit["labels"],
        profiles=profiles,
        model=dict(scaler=scaler, centroids=fit["centroids"], config=config,
                   fit_as_of=max((row["available_at"] for row in rows), key=datetime.fromisoformat)),
        diagnostics=diagnostics,
    )
