"""Cluster-quality metrics, independent from model and portfolio evaluation."""
from collections import Counter
import math
from statistics import mean


def squared_distance(a: list[float], b: list[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(a, b))


def cluster_metrics(vectors: list[list[float]], fit: dict) -> dict:
    labels, centers = fit["labels"], fit["centroids"]
    k, n = len(centers), len(vectors)
    if len(labels) != n or k < 2 or n <= k:
        raise ValueError("cluster metrics require aligned labels and 2 <= k < n")
    groups = [[index for index, label in enumerate(labels) if label == cluster] for cluster in range(k)]
    if any(not group for group in groups):
        raise ValueError("cluster metrics require nonempty clusters")
    silhouettes = []
    for index, row in enumerate(vectors):
        own = groups[labels[index]]
        if len(own) == 1:
            silhouettes.append(0.0)
            continue
        within = mean(math.sqrt(squared_distance(row, vectors[other])) for other in own if index != other)
        nearest = min(mean(math.sqrt(squared_distance(row, vectors[other])) for other in group)
                      for cluster, group in enumerate(groups) if cluster != labels[index])
        silhouettes.append((nearest - within) / max(within, nearest) if max(within, nearest) else 0.0)
    grand = [mean(row[column] for row in vectors) for column in range(len(vectors[0]))]
    between = sum(len(group) * squared_distance(centers[cluster], grand)
                  for cluster, group in enumerate(groups))
    scatter = [mean(math.sqrt(squared_distance(vectors[index], centers[cluster])) for index in group)
               for cluster, group in enumerate(groups)]
    davies_bouldin = []
    for left in range(k):
        ratios = []
        for right in range(k):
            if left == right:
                continue
            separation = math.sqrt(squared_distance(centers[left], centers[right]))
            if separation <= 1e-16:
                raise ValueError("Davies-Bouldin is undefined for coincident centroids")
            ratios.append((scatter[left] + scatter[right]) / separation)
        davies_bouldin.append(max(ratios))
    sizes = dict(Counter(labels))
    return dict(
        k=k,
        silhouette=mean(silhouettes),
        calinski_harabasz=((between / (k - 1)) / (fit["inertia"] / (n - k))
                           if fit["inertia"] > 1e-16 else None),
        davies_bouldin=mean(davies_bouldin),
        inertia=fit["inertia"],
        cluster_sizes=sizes,
        cluster_balance=min(sizes.values()) / max(sizes.values()),
        converged=fit["converged"],
    )
