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

    centers = {index: vectors[index] for index in range(len(vectors))}
    sizes = {index: 1 for index in range(len(vectors))}
    
    distances = {i: {} for i in range(len(vectors))}
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            distances[i][j] = 0.5 * squared_distance(centers[i], centers[j])

    while len(clusters) > k:
        candidates = []
        for i in distances:
            for j, dist in distances[i].items():
                candidates.append((dist, clusters[i], clusters[j], i, j))
        _, _, _, left, right = min(candidates)
        
        clusters[next_id] = tuple(sorted(clusters.pop(left) + clusters.pop(right)))
        new_size = sizes[left] + sizes[right]
        sizes[next_id] = new_size
        
        new_center = []
        for c in range(len(vectors[0])):
            new_center.append((centers[left][c] * sizes[left] + centers[right][c] * sizes[right]) / new_size)
        centers[next_id] = new_center
        
        del centers[left]
        del centers[right]
        del sizes[left]
        del sizes[right]
        del distances[left]
        del distances[right]
        
        for i in distances:
            if left in distances[i]: del distances[i][left]
            if right in distances[i]: del distances[i][right]
            
        distances[next_id] = {}
        for i in centers:
            if i != next_id:
                inc = (sizes[i] * new_size) / (sizes[i] + new_size) * squared_distance(centers[i], new_center)
                if i < next_id:
                    distances[i][next_id] = inc
                else:
                    distances[next_id][i] = inc
                    
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
