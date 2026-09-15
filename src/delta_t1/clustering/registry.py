"""Clustering algorithm registry used by experiment protocols and runners."""
from .base import ClusteringAlgorithm


def algorithms() -> dict[str, ClusteringAlgorithm]:
    from . import dbscan, gmm, hierarchical, kmeans
    return {
        "kmeans": ClusteringAlgorithm("kmeans", kmeans.fit_snapshot, kmeans.validate_config),
        "hierarchical": ClusteringAlgorithm("hierarchical", hierarchical.fit_snapshot, hierarchical.validate_config),
        "ward": ClusteringAlgorithm("ward", hierarchical.fit_snapshot, hierarchical.validate_config),
        "dbscan": ClusteringAlgorithm("dbscan", dbscan.fit_snapshot, dbscan.validate_config),
        "gmm": ClusteringAlgorithm("gmm", gmm.fit_snapshot, gmm.validate_config),
    }


def get_algorithm(name: str) -> ClusteringAlgorithm:
    try:
        return algorithms()[name]
    except KeyError:
        raise ValueError("unsupported clustering algorithm: " + str(name)) from None
