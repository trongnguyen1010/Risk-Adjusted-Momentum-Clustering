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
