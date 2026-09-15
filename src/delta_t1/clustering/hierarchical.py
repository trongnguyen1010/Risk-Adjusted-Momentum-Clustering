"""Deterministic Ward agglomerative comparator for bounded research snapshots."""
from statistics import mean

from .base import build_snapshot, validate_k_config
from ..evaluation.cluster_metrics import squared_distance


def fit_ward(vectors: list[list[float]], k: int) -> dict:
    if not 2 <= k < len(vectors) or len({tuple(row) for row in vectors}) < k:
        raise ValueError("insufficient distinct observations or invalid Ward parameters")
    clusters = {index: (index,) for index in range(len(vectors))}
    next_id = len(vectors)

    def centroid(members: tuple[int, ...]) -> list[float]:
        return [mean(vectors[index][column] for index in members) for column in range(len(vectors[0]))]

    while len(clusters) > k:
        ids = sorted(clusters)
        candidates = []
        for position, left in enumerate(ids):
            left_members = clusters[left]
            left_center = centroid(left_members)
            for right in ids[position + 1:]:
                right_members = clusters[right]
                increase = (len(left_members) * len(right_members)
                            / (len(left_members) + len(right_members))
                            * squared_distance(left_center, centroid(right_members)))
                candidates.append((increase, left_members, right_members, left, right))
        _, _, _, left, right = min(candidates)
        clusters[next_id] = tuple(sorted(clusters.pop(left) + clusters.pop(right)))
        next_id += 1
    ordered = sorted(clusters.values(), key=lambda members: (members[0], members))
    labels = [-1] * len(vectors)
    centers = []
    for label, members in enumerate(ordered):
        centers.append(centroid(members))
        for index in members:
            labels[index] = label
    inertia = sum(squared_distance(row, centers[label]) for row, label in zip(vectors, labels))
    return dict(labels=labels, centroids=centers, inertia=inertia,
                iterations=len(vectors) - k, converged=True)


def validate_config(config: dict) -> None:
    validate_k_config(config)
    if config.get("linkage", "ward") != "ward":
        raise ValueError("hierarchical comparator currently supports Ward linkage only")


def fit_snapshot(rows: list[dict], config: dict) -> dict:
    validate_config(config)
    return build_snapshot(rows, config, lambda vectors, k, _: fit_ward(vectors, k))
