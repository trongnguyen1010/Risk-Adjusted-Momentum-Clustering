"""Leakage-safe transforms fitted only on the supplied cross-section."""
import math
from statistics import mean, median, pstdev


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = int(pos)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (pos - lo)


def preprocess(rows: list[dict], config: dict) -> tuple[list[list[float]], dict]:
    """Fit only supplied rows and serialize clipping/scaling parameters."""
    fields = config["features"]
    q = config["winsor_quantile"]
    method = config["scaling"]
    if not fields or not 0 <= q < .5 or method not in ("zscore", "robust", "rank", "none"):
        raise ValueError("invalid preprocessing")
    columns, bundle = [], {}
    for name in fields:
        values = [row[name] for row in rows]
        if any(value is None or not math.isfinite(value) for value in values):
            raise ValueError("nonfinite clustering feature: " + name)
        if name in config.get("log1p_features", []):
            if any(value < 0 for value in values):
                raise ValueError("log1p feature must be nonnegative")
            values = [math.log1p(value) for value in values]
        lower, upper = quantile(values, q), quantile(values, 1 - q)
        values = [max(lower, min(upper, value)) for value in values]
        center, scale = 0.0, 1.0
        if method == "zscore":
            center, scale = mean(values), pstdev(values) or 1.0
        elif method == "robust":
            center, scale = median(values), quantile(values, .75) - quantile(values, .25) or 1.0
        elif method == "rank":
            original = values[:]
            values = [(sum(item < value for item in original) + .5 * sum(item == value for item in original)) / len(values)
                      for value in original]
        columns.append([(value - center) / scale for value in values])
        bundle[name] = dict(lower=lower, upper=upper, center=center, scale=scale, method=method,
                            rank_reference=sorted(original) if method == "rank" else None)
    vectors = [list(row) for row in zip(*columns)]
    reduction = config.get("reduction", {"method": "none"})
    method_name = reduction.get("method", "none")
    if method_name == "none":
        return vectors, bundle
    if method_name != "pca":
        raise ValueError("unsupported dimensionality reduction")
    vectors, pca_bundle = fit_pca(vectors, reduction["n_components"])
    bundle["_reduction"] = pca_bundle
    return vectors, bundle


def _jacobi_eigen(matrix: list[list[float]], tolerance: float = 1e-12,
                  max_iterations: int = 10_000) -> tuple[list[float], list[list[float]]]:
    """Deterministic eigendecomposition for a small real symmetric matrix."""
    size = len(matrix)
    values = [row[:] for row in matrix]
    vectors = [[1.0 if row == column else 0.0 for column in range(size)] for row in range(size)]
    for _ in range(max_iterations):
        pairs = [(abs(values[left][right]), left, right)
                 for left in range(size) for right in range(left + 1, size)]
        if not pairs:
            break
        magnitude, left, right = max(pairs, key=lambda item: (item[0], -item[1], -item[2]))
        if magnitude <= tolerance:
            break
        angle = .5 * math.atan2(2 * values[left][right], values[right][right] - values[left][left])
        cosine, sine = math.cos(angle), math.sin(angle)
        for index in range(size):
            if index not in (left, right):
                a, b = values[index][left], values[index][right]
                values[index][left] = values[left][index] = cosine * a - sine * b
                values[index][right] = values[right][index] = sine * a + cosine * b
        a, b, cross = values[left][left], values[right][right], values[left][right]
        values[left][left] = cosine * cosine * a - 2 * sine * cosine * cross + sine * sine * b
        values[right][right] = sine * sine * a + 2 * sine * cosine * cross + cosine * cosine * b
        values[left][right] = values[right][left] = 0.0
        for index in range(size):
            a, b = vectors[index][left], vectors[index][right]
            vectors[index][left] = cosine * a - sine * b
            vectors[index][right] = sine * a + cosine * b
    else:
        raise ValueError("PCA eigendecomposition did not converge")
    return [values[index][index] for index in range(size)], vectors


def fit_pca(vectors: list[list[float]], n_components: int) -> tuple[list[list[float]], dict]:
    """Fit PCA only on supplied vectors and return loadings/explained variance."""
    if not vectors or len(vectors) < 2 or not vectors[0]:
        raise ValueError("PCA requires at least two nonempty observations")
    dimensions = len(vectors[0])
    if (isinstance(n_components, bool) or not isinstance(n_components, int)
            or not 1 <= n_components <= dimensions or any(len(row) != dimensions for row in vectors)):
        raise ValueError("invalid PCA component count or matrix shape")
    centers = [mean(row[column] for row in vectors) for column in range(dimensions)]
    centered = [[value - centers[column] for column, value in enumerate(row)] for row in vectors]
    covariance = [[sum(row[left] * row[right] for row in centered) / (len(centered) - 1)
                   for right in range(dimensions)] for left in range(dimensions)]
    eigenvalues, eigenvectors = _jacobi_eigen(covariance)
    ordered = sorted(range(dimensions), key=lambda index: (-eigenvalues[index], index))[:n_components]
    components = []
    for index in ordered:
        component = [eigenvectors[row][index] for row in range(dimensions)]
        pivot = max(range(dimensions), key=lambda column: (abs(component[column]), -column))
        if component[pivot] < 0:
            component = [-value for value in component]
        components.append(component)
    transformed = [[sum(row[column] * component[column] for column in range(dimensions))
                    for component in components] for row in centered]
    total = sum(max(value, 0.0) for value in eigenvalues)
    explained = [max(eigenvalues[index], 0.0) / total if total > 1e-16 else 0.0 for index in ordered]
    return transformed, dict(method="pca", n_components=n_components, input_center=centers,
                             components=components, explained_variance_ratio=explained,
                             fit_scope="supplied_snapshot_only")
