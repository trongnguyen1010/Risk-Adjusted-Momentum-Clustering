"""Deterministic cross-sectional KMeans and auditable preprocessing (stdlib)."""
from collections import Counter
from datetime import datetime
import math
import random
from statistics import mean, median, pstdev


def distance(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = int(pos)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (pos - lo)


def preprocess(rows: list[dict], config: dict) -> tuple[list[list[float]], dict]:
    """Fit only the supplied cross-section; serialize clipping and scaling values."""
    fields = config["features"]
    q = config["winsor_quantile"]
    method = config["scaling"]
    if not 0 <= q < .5 or method not in ("zscore", "robust", "rank", "none"):
        raise ValueError("invalid preprocessing")
    columns, bundle = [], {}
    for name in fields:
        values = [r[name] for r in rows]
        if any(v is None or not math.isfinite(v) for v in values):
            raise ValueError("nonfinite clustering feature: " + name)
        if name in config.get("log1p_features", []):
            if any(v < 0 for v in values):
                raise ValueError("log1p feature must be nonnegative")
            values = [math.log1p(v) for v in values]
        lower, upper = quantile(values, q), quantile(values, 1 - q)
        values = [max(lower, min(upper, v)) for v in values]
        center, scale = 0.0, 1.0
        if method == "zscore":
            center, scale = mean(values), pstdev(values) or 1.0
        elif method == "robust":
            center, scale = median(values), quantile(values, .75) - quantile(values, .25) or 1.0
        elif method == "rank":
            original = values[:]
            values = [(sum(x < v for x in original) + .5 * sum(x == v for x in original)) / len(values) for v in original]
        columns.append([(v - center) / scale for v in values])
        bundle[name] = dict(lower=lower, upper=upper, center=center, scale=scale, method=method,
                            rank_reference=sorted(original) if method == "rank" else None)
    return [list(row) for row in zip(*columns)], bundle


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
    labels, centers = fit["labels"], fit["centroids"]
    k, n = len(centers), len(x)
    groups = [[i for i, c in enumerate(labels) if c == j] for j in range(k)]
    silhouette = []
    for i, row in enumerate(x):
        own = groups[labels[i]]
        if len(own) == 1:
            silhouette.append(0.0)
            continue
        a = mean(math.sqrt(distance(row, x[j])) for j in own if i != j)
        b = min(mean(math.sqrt(distance(row, x[j])) for j in group) for c, group in enumerate(groups) if c != labels[i])
        silhouette.append((b - a) / max(a, b) if max(a, b) else 0.0)
    grand = [mean(row[j] for row in x) for j in range(len(x[0]))]
    between = sum(len(group) * distance(centers[c], grand) for c, group in enumerate(groups))
    scatter = [mean(math.sqrt(distance(x[i], centers[c])) for i in group) for c, group in enumerate(groups)]
    db = [max((scatter[i] + scatter[j]) / math.sqrt(distance(centers[i], centers[j])) for j in range(k) if i != j) for i in range(k)]
    return dict(k=k, silhouette=mean(silhouette), calinski_harabasz=(between / (k - 1)) / (fit["inertia"] / (n - k)) if fit["inertia"] > 1e-16 else None,
                davies_bouldin=mean(db), inertia=fit["inertia"], cluster_sizes=dict(Counter(labels)), converged=fit["converged"])


def fit_snapshot(rows: list[dict], config: dict) -> dict:
    """Fixed preregistered k; diagnostic alternatives never auto-select a winner."""
    rows = sorted((r for r in rows if r["eligibility"]), key=lambda r: r["security_id"])
    if len({r["as_of_date"] for r in rows}) != 1 or len({r["security_id"] for r in rows}) != len(rows):
        raise ValueError("one nonempty unique cross-section required")
    if len({r.get("adjustment_basis") for r in rows}) > 1:
        raise ValueError("mixed return conventions in cross-section")
    x, scaler = preprocess(rows, config)
    fits, metrics = {}, []
    for k in sorted(set(config["k_range"] + [config["k"]])):
        try:
            fits[k] = fit_kmeans(x, k, config["seed"], config["n_init"], config["max_iter"])
            metrics.append(diagnostics(x, fits[k]))
        except ValueError as exc:
            metrics.append(dict(k=k, status="unavailable", reason=str(exc)))
    if config["k"] not in fits:
        raise ValueError("selected k unavailable: insufficient sample/distinct points/convergence")
    fit = fits[config["k"]]
    mom, risk = config["momentum_feature"], config["risk_feature"]
    profiles = []
    for c in range(config["k"]):
        members = [r for r, label in zip(rows, fit["labels"]) if label == c]
        centroid = {name: mean(r[name] for r in members) for name in set(config["features"] + [mom, risk])}
        semantic = ("High" if centroid[mom] >= median(r[mom] for r in rows) else "Low") + " Momentum / " + ("High" if centroid[risk] >= median(r[risk] for r in rows) else "Low") + " Risk"
        profiles.append(dict(raw_cluster_id=c, semantic_label=semantic, size=len(members), centroid=centroid))
    ranking = sorted(profiles, key=lambda p: (-p["centroid"][mom], p["centroid"][risk], p["raw_cluster_id"]))
    for rank, p in enumerate(ranking):
        p["economic_rank"] = rank
    return dict(snapshot_date=rows[0]["as_of_date"], rows=rows, labels=fit["labels"], profiles=profiles,
                model=dict(scaler=scaler, centroids=fit["centroids"], config=config, fit_as_of=max((r["available_at"] for r in rows), key=datetime.fromisoformat)), diagnostics=metrics)
