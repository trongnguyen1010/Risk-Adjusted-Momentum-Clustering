"""Deterministic Ward agglomerative comparator for bounded research snapshots."""
from statistics import mean

from .base import build_snapshot, validate_k_config
from ..evaluation.cluster_metrics import squared_distance


import numpy as np
import scipy.cluster.hierarchy as sch

def fit_ward(vectors: list[list[float]], k: int) -> dict:
    if not 2 <= k < len(vectors) or len({tuple(row) for row in vectors}) < k:
        raise ValueError("insufficient distinct observations or invalid Ward parameters")
    X = np.array(vectors, dtype=float)
    N = len(vectors)
    Z = sch.linkage(X, method="ward")

    linkage = []
    for i in range(N - k):
        left = int(Z[i, 0])
        right = int(Z[i, 1])
        dist = 0.5 * (float(Z[i, 2]) ** 2)
        sz = int(Z[i, 3])
        linkage.append({
            "left": left,
            "right": right,
            "distance": dist,
            "size": sz,
        })

    clusters = {i: (i,) for i in range(N)}
    next_id = N
    for i in range(N - k):
        l, r = linkage[i]["left"], linkage[i]["right"]
        clusters[next_id] = tuple(sorted(clusters.pop(l) + clusters.pop(r)))
        next_id += 1

    ordered = sorted(clusters.values(), key=lambda members: (members[0], members))
    labels = [-1] * N
    centers = []

    def centroid(members: tuple[int, ...]) -> list[float]:
        return [mean(vectors[index][column] for index in members) for column in range(len(vectors[0]))]

    for label, members in enumerate(ordered):
        centers.append(centroid(members))
        for index in members:
            labels[index] = label

    inertia = sum(squared_distance(row, centers[label]) for row, label in zip(vectors, labels))
    return dict(labels=labels, centroids=centers, inertia=inertia,
                iterations=N - k, converged=True, linkage=linkage)


def validate_config(config: dict) -> None:
    validate_k_config(config)
    if config.get("linkage", "ward") != "ward":
        raise ValueError("hierarchical comparator currently supports Ward linkage only")


def fit_snapshot(rows: list[dict], config: dict) -> dict:
    validate_config(config)
    selected_linkage = None

    def fit_vectors(vectors: list[list[float]], k: int, _: dict) -> dict:
        nonlocal selected_linkage
        fit = fit_ward(vectors, k)
        if k == config["k"]:
            selected_linkage = fit["linkage"]
        return fit

    snapshot = build_snapshot(rows, config, fit_vectors)
    snapshot["model"]["linkage"] = selected_linkage
    return snapshot
