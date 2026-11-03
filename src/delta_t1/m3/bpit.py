"""B-PIT: point-in-time Financial clustering for M3 (KE_HOACH_M3_SCHEMA_GITHUB §3.1.5, §5.2.A; ADR D-M3-01).

Same recipe as Financial model B v4 (bundle v2/v3/v4): nine D-IND-01 indicators, non-financial companies, complete
cases only, T1 = winsorize 1–99 % + z-score fitted on one fiscal-year cohort, K-Means k=3 (n_init=10, seed 42),
labels renumbered by fitted-cluster size. The only change is WHICH reports are fitted on:

  cutoff(t) = max(30/04/(t+1), earliest usable_from_date among FY t reports)

- FY >= 2022: usable dates come from CafeF disclosure, the earliest is before 30/04, so cutoff = 30/04/(t+1). Reports
  usable after the cutoff are transformed with the frozen T1 parameters and assigned to the nearest frozen centroid.
- FY < 2022: every report is usable from the same LAG_RULE session (first session after 30/06/(t+1)), so the cutoff is
  that session and all reports are fitted — no decision can use FY t before then, so this is not leakage.

The Financial cluster order (median ROE desc, ties median D/E asc) is computed on the fitted reports only and frozen
with the centroids; M3 reads it instead of recomputing it on the whole fiscal year at decision time.
"""
import numpy as np

from delta_t1.clustering.robust_transforms import apply_t1, fit_t1, nearest_centroid

from .universe import cluster_order

FEATURES = ('roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio', 'asset_turnover',
            'revenue_growth', 'cfo_to_ni')
K, SEED, N_INIT = 3, 42, 10
EARLY_CUTOFF = '04-30'


def cutoff_for(fiscal_year, usable_dates):
    """max(30/04/(t+1), earliest non-empty usable_from_date of FY t)."""
    early = f'{fiscal_year + 1}-{EARLY_CUTOFF}'
    dates = [d for d in usable_dates if d]
    return max(early, min(dates)) if dates else early


def _renumber(labels, k):
    order = np.argsort(-np.bincount(labels, minlength=k), kind='stable')
    remap = np.empty(k, dtype=int)
    remap[order] = np.arange(k)
    return remap[labels]


def build_year(fiscal_year, tickers, raw, usable_dates, features=FEATURES, k=K, seed=SEED, n_init=N_INIT):
    """Fit one fiscal year. raw: complete-case matrix (len(tickers) × len(features)); usable_dates aligned with
    tickers ('' when unknown — such reports are never fitted, only assigned).

    Returns dict(cutoff, labels, fitted (bool array), params, centroids, cluster_order, profile, n_fit, n_assigned).
    """
    from sklearn.cluster import KMeans

    raw = np.asarray(raw, dtype=float)
    usable = np.array([d or '' for d in usable_dates], dtype=object)
    cutoff = cutoff_for(fiscal_year, list(usable))
    fitted = np.array([bool(d) and d <= cutoff for d in usable])
    if fitted.sum() < 2 * k:
        raise ValueError(f'FY{fiscal_year}: only {int(fitted.sum())} reports usable at cutoff {cutoff}')
    params = fit_t1(raw[fitted], features)
    x = apply_t1(raw, params)
    lab_fit = _renumber(KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit_predict(x[fitted]), k)
    centroids = np.array([x[fitted][lab_fit == c].mean(axis=0) for c in range(k)])
    labels = np.empty(len(tickers), dtype=int)
    labels[fitted] = lab_fit
    if (~fitted).any():
        labels[~fitted] = nearest_centroid(x[~fitted], centroids)
    roe, dte = features.index('roe'), features.index('debt_to_equity')
    members = [(int(c), dict(roe=float(r[roe]), debt_to_equity=float(r[dte])))
               for c, r in zip(lab_fit, raw[fitted])]
    order = cluster_order(members, 'roe', 'debt_to_equity', higher_tiebreak=False)
    if not order:
        raise ValueError(f'FY{fiscal_year}: cluster order ambiguous at cutoff (CLUSTER_PROFILE_AMBIGUOUS)')
    profile = {}
    for c in range(k):
        rows = raw[fitted][lab_fit == c]
        profile[c] = dict(n_fit=int(len(rows)), median_roe=float(np.median(rows[:, roe])),
                          median_debt_to_equity=float(np.median(rows[:, dte])))
    return dict(cutoff=cutoff, labels=labels, fitted=fitted, params=params, centroids=centroids,
                cluster_order=[int(c) for c in order], profile=profile, n_fit=int(fitted.sum()),
                n_assigned=int((~fitted).sum()))


def fit_leaks(usable_dates, fitted, cutoff):
    """Audit: tickers fitted although usable after the cutoff (must be empty)."""
    return [i for i, (d, f) in enumerate(zip(usable_dates, fitted)) if f and (not d or d > cutoff)]
