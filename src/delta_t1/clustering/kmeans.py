"""Deterministic static K-Means baseline (stdlib)."""
import random
from statistics import mean

from .base import build_snapshot, validate_k_config
from ..evaluation.cluster_metrics import cluster_metrics, squared_distance
from ..features.preprocessing import preprocess, quantile


def distance(a: list[float], b: list[float]) -> float:
    return squared_distance(a, b)


def fit_kmeans(x: list[list[float]], k: int, seed: int, n_init: int, max_iter: int) -> dict:
    """KMeans++ initialization; deterministic tie breaks, lowest-inertia restart."""
    if not 2 <= k < len(x) or len({tuple(r) for r in x}) < k or n_init < 1 or max_iter < 1:
        raise ValueError("insufficient distinct observations or invalid KMeans parameters")
    best = None
    for restart in range(n_init):
        rng = random.Random(seed + restart)
        centers = [x[rng.randrange(len(x))][:]]
        while len(centers) < k:
            weights = [min(distance(row, c) for c in centers) for row in x]
            centers.append(x[rng.choices(range(len(x)), weights=weights)[0]][:])
        labels = [-1] * len(x)
        converged = False
        for iteration in range(max_iter):
            current = [min(range(k), key=lambda j: (distance(row, centers[j]), j)) for row in x]
            if len(set(current)) != k:
                break  # Degenerate restart is reported/ignored, never invent membership.
            if current == labels:
                converged = True
                break
            labels = current
            centers = [[mean(x[i][j] for i in range(len(x)) if labels[i] == c) for j in range(len(x[0]))] for c in range(k)]
        if not converged:
            continue
        inertia = sum(distance(row, centers[c]) for row, c in zip(x, labels))
        result = dict(labels=labels, centroids=centers, inertia=inertia, iterations=iteration + 1, converged=True)
        if best is None or inertia < best["inertia"]:
            best = result
    if best is None:
        raise ValueError("no converged nondegenerate KMeans restart")
    return best


def diagnostics(x: list[list[float]], fit: dict) -> dict:
    """Compatibility export; implementation belongs to evaluation."""
    return cluster_metrics(x, fit)


def fit_snapshot(rows: list[dict], config: dict) -> dict:
    """Fixed preregistered k; diagnostic alternatives never auto-select a winner."""
    validate_config(config)
    def fit_vectors(vectors, k, _):
        if config.get("implementation", "stdlib") == "sklearn":
            from sklearn.cluster import KMeans

            model = KMeans(
                n_clusters=k, random_state=config["seed"],
                n_init=config["n_init"], max_iter=config["max_iter"],
            ).fit(vectors)
            if model.n_iter_ >= config["max_iter"]:
                raise ValueError("scikit-learn K-Means reached max_iter without verified convergence")
            return dict(labels=model.labels_.tolist(), centroids=model.cluster_centers_.tolist(),
                        inertia=float(model.inertia_), iterations=int(model.n_iter_), converged=True)
        return fit_kmeans(vectors, k, config["seed"], config["n_init"], config["max_iter"])

    return build_snapshot(rows, config, fit_vectors)


def validate_config(config: dict) -> None:
    validate_k_config(config)
    if config.get("implementation", "stdlib") not in ("stdlib", "sklearn"):
        raise ValueError("unsupported K-Means implementation")
    if config["n_init"] < 1 or config["max_iter"] < 1:
        raise ValueError("invalid K-Means parameters")
