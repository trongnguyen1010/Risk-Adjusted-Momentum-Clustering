"""Deterministic Ward agglomerative comparator for bounded research snapshots."""
from statistics import mean

from .base import build_snapshot, validate_k_config
from ..evaluation.cluster_metrics import squared_distance


def fit_ward(vectors: list[list[float]], k: int) -> dict:
    if not 2 <= k < len(vectors) or len({tuple(row) for row in vectors}) < k:
        raise ValueError("insufficient distinct observations or invalid Ward parameters")
    dim = len(vectors[0])
    clusters = {index: (index,) for index in range(len(vectors))}
    centroids = {index: list(vectors[index]) for index in range(len(vectors))}
    next_id = len(vectors)

    while len(clusters) > k:
        ids = sorted(clusters)
        candidates = []
        for position, left in enumerate(ids):
            left_members = clusters[left]
            left_center = centroids[left]
            len_l = len(left_members)
            for right in ids[position + 1:]:
                right_members = clusters[right]
                len_r = len(right_members)
                increase = (len_l * len_r / (len_l + len_r)
                            * squared_distance(left_center, centroids[right]))
                candidates.append((increase, left_members, right_members, left, right))
        _, _, _, left, right = min(candidates)
        l_m, r_m = clusters.pop(left), clusters.pop(right)
        l_c, r_c = centroids.pop(left), centroids.pop(right)
        len_l, len_r = len(l_m), len(r_m)
        len_new = len_l + len_r
        clusters[next_id] = tuple(sorted(l_m + r_m))
        centroids[next_id] = [(len_l * l_c[c] + len_r * r_c[c]) / len_new for c in range(dim)]
        next_id += 1
    ordered = sorted(clusters.values(), key=lambda members: (members[0], members))
    labels = [-1] * len(vectors)
    centers = []
    for label, members in enumerate(ordered):
        centers.append([mean(vectors[index][column] for index in members) for column in range(dim)])
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
