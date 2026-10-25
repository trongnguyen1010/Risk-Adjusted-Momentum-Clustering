"""Snapshot-local transforms that stop a few extreme rows from defining clusters.

All parameters are fitted on one snapshot cohort only (no pooling across dates).
"""
import numpy as np
from scipy.stats import norm, rankdata

LOG_FEATURES = ('liquidity_21',)


def zscore(values):
    sd = values.std(axis=0)
    sd[sd == 0] = 1.0
    return (values - values.mean(axis=0)) / sd


def robust(values):
    q1, med, q3 = np.percentile(values, [25, 50, 75], axis=0)
    iqr = q3 - q1
    iqr[iqr == 0] = 1.0
    return (values - med) / iqr


def winsorize(values, lower=1.0, upper=99.0):
    lo, hi = np.percentile(values, [lower, upper], axis=0)
    return np.clip(values, lo, hi)


def log_columns(values, features):
    out = values.astype(float).copy()
    for j, name in enumerate(features):
        if name in LOG_FEATURES:
            if (out[:, j] < 0).any():
                raise ValueError(f'{name} must be non-negative before log1p')
            out[:, j] = np.log1p(out[:, j])
    return out


def rank_normal(values):
    """Rankit scores: (rank - 0.5) / n -> standard normal quantile, per column."""
    n = len(values)
    ranks = np.column_stack([rankdata(col, method='average') for col in values.T])
    return norm.ppf((ranks - 0.5) / n)


def transform(raw, features, recipe, baseline='zscore'):
    """T0 baseline, T1 log + winsorize + z-score, T2 rank -> normal scores."""
    raw = np.asarray(raw, dtype=float)
    if raw.ndim != 2 or not len(raw) or not np.isfinite(raw).all():
        raise ValueError('Missing/nonfinite input; no imputation.')
    if recipe == 'T0':
        return robust(raw) if baseline == 'robust' else zscore(raw)
    if recipe == 'T1':
        return zscore(winsorize(log_columns(raw, features)))
    if recipe == 'T2':
        return rank_normal(raw)
    raise ValueError('Unknown recipe ' + recipe)


def fit_t1(raw, features, lower=1.0, upper=99.0):
    """T1 parameters learned on one cohort (e.g. liquid stocks), reusable via apply_t1."""
    logged = log_columns(np.asarray(raw, dtype=float), features)
    lo, hi = np.percentile(logged, [lower, upper], axis=0)
    clipped = np.clip(logged, lo, hi)
    sd = clipped.std(axis=0)
    sd[sd == 0] = 1.0
    return dict(features=tuple(features), lo=lo, hi=hi, mean=clipped.mean(axis=0), sd=sd)


def apply_t1(raw, params):
    """Same log + clip + z-score as the fitted cohort; NaN cells stay NaN."""
    raw = np.asarray(raw, dtype=float)
    logged = raw.copy()
    for j, name in enumerate(params['features']):
        if name in LOG_FEATURES:
            logged[:, j] = np.log1p(np.where(raw[:, j] < 0, np.nan, raw[:, j]))
    return (np.clip(logged, params['lo'], params['hi']) - params['mean']) / params['sd']


def nearest_centroid(x, centroids):
    """Nearest centroid on the dimensions each row actually has (NaN dimensions skipped)."""
    x = np.asarray(x, dtype=float)
    out = np.empty(len(x), dtype=int)
    for i, row in enumerate(x):
        ok = np.isfinite(row)
        if not ok.any():
            raise ValueError('row without any finite feature')
        out[i] = int(np.argmin(((centroids[:, ok] - row[ok]) ** 2).sum(axis=1)))
    return out


def block_weights(values, widths, total=0.5):
    """Scale each feature block to equal total variance (C = market block + financial block)."""
    out = values.copy()
    start = 0
    for width in widths:
        block = out[:, start:start + width]
        variance = float(block.var(axis=0).sum())
        if variance <= 0:
            raise ValueError('Zero block variance')
        out[:, start:start + width] = block * np.sqrt(total / variance)
        start += width
    return out
