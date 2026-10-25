"""Clustering rework v1: transform x algorithm x k sweep with a minimum cluster size.

Descriptive and ex post only. Selection uses geometry, balance and stability,
never returns. Nothing here changes the served model.
"""
from collections import defaultdict
import json
import sqlite3

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture

from ..clustering.robust_transforms import block_weights, transform

MARKET = ('mom_21', 'mom_63', 'mom_126', 'mom_252', 'vol_63', 'mdd_126', 'beta_126', 'liquidity_21')
FINANCIAL = ('gross_margin', 'net_margin', 'liabilities_to_assets', 'current_ratio',
             'operating_cashflow_to_assets', 'asset_turnover_ending_assets')


class Snapshot:
    def __init__(self, family, date, tickers, raw, features, widths=None):
        self.family, self.date, self.tickers = family, date, list(tickers)
        self.raw, self.features, self.widths = np.asarray(raw, dtype=float), tuple(features), widths

    def space(self, recipe):
        baseline = 'robust' if self.family == 'A' else 'zscore'
        if self.widths:  # C: transform each block on its own, then equal block variance.
            m = self.widths[0]
            parts = [transform(self.raw[:, :m], self.features[:m], recipe, 'robust' if recipe == 'T0' else 'zscore'),
                     transform(self.raw[:, m:], self.features[m:], recipe)]
            return block_weights(np.hstack(parts), self.widths)
        return transform(self.raw, self.features, recipe, baseline)


def _observations(db, kind):
    out = defaultdict(dict)
    for date, ticker, features in db.execute('select date, ticker, features from observations where kind = ? '
                                             'order by date, ticker', (kind,)):
        out[date][ticker] = json.loads(features)
    return out


def _matrix(rows, features):
    tickers, values = [], []
    for t, f in sorted(rows.items()):
        v = [f.get(k) for k in features]
        if all(x is not None and np.isfinite(x) for x in v):
            tickers.append(t)
            values.append(v)
    return tickers, np.array(values, dtype=float)


def load_terminal(path, family, months=None):
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as db:
        if family == 'A':
            obs = _observations(db, 'market')
            dates = [d for d in obs if months is None or d[5:7] in months]
            return [Snapshot('A', d, *_matrix(obs[d], MARKET), MARKET) for d in dates]
        if family == 'B':
            obs = _observations(db, 'financial')
            return [Snapshot('B', d, *_matrix(obs[d], FINANCIAL), FINANCIAL) for d in sorted(obs)]
        if family == 'C':
            market, financial = _observations(db, 'market'), _observations(db, 'financial')
            snaps = []
            for d in sorted(market):
                fy = d[:4]
                if d[5:7] != '12' or fy not in financial:
                    continue
                joined = {t: {**market[d][t], **financial[fy][t]} for t in market[d] if t in financial[fy]}
                tickers, raw = _matrix(joined, MARKET + FINANCIAL)
                snaps.append(Snapshot('C', d, tickers, raw, MARKET + FINANCIAL, (len(MARKET), len(FINANCIAL))))
            return snaps
    raise ValueError(family)


def load_indicators(path, features, sector='NON_FINANCIAL', years=range(2016, 2026)):
    """B2: new D-IND-01 indicators, complete cases only (no imputation)."""
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as db:
        allowed = {t for (t,) in db.execute('select ticker from company where sector_group = ?', (sector,))}
        marks = ','.join('?' * len(features))
        rows = db.execute(f"select ticker, fiscal_year, metric, value from indicator_values where status = 'OK' "
                          f"and metric in ({marks})", tuple(features)).fetchall()
    data = defaultdict(lambda: defaultdict(dict))
    for t, y, m, v in rows:
        if t in allowed:
            data[y][t][m] = v
    return [Snapshot('B2', str(y), *_matrix(data[y], features), features) for y in years if y in data]


def fit(algo, x, k, seed, cfg):
    if algo == 'kmeans':
        return KMeans(n_clusters=k, n_init=cfg['kmeans_n_init'], random_state=seed).fit_predict(x), None
    g = cfg['gmm']
    model = GaussianMixture(n_components=k, covariance_type=g['covariance_type'], n_init=g['n_init'],
                            reg_covar=g['reg_covar'], max_iter=g['max_iter'], random_state=seed).fit(x)
    return model.predict(x), float(model.bic(x))


def evaluate(reference, labels, k):
    counts = np.bincount(labels, minlength=k)
    used = counts[counts > 0]
    shares = used / len(labels)
    out = dict(n=len(labels), k_used=int(len(used)), min_share=float(shares.min()), max_share=float(shares.max()),
               balance=float(-(shares * np.log(shares)).sum() / np.log(k)) if k > 1 else 0.0,
               sizes=sorted(map(int, used), reverse=True))
    if len(used) > 1:
        out.update(silhouette=float(silhouette_score(reference, labels)),
                   davies_bouldin=float(davies_bouldin_score(reference, labels)),
                   calinski_harabasz=float(calinski_harabasz_score(reference, labels)))
    else:
        out.update(silhouette=None, davies_bouldin=None, calinski_harabasz=None)
    return out


def sweep(snapshots, cfg, recipes=('T0', 'T1', 'T2'), algos=None, ks=None, progress=None):
    algos, ks = algos or cfg['algorithms'], ks or cfg['k']
    rows = []
    for snap in snapshots:
        reference = snap.space('T1')
        for recipe in recipes:
            x = snap.space(recipe)
            for algo in algos:
                for k in ks:
                    labels, bic = fit(algo, x, k, cfg['seed'], cfg)
                    seeds = [adjusted_rand_score(labels, fit(algo, x, k, s, cfg)[0]) for s in cfg['stability_seeds']]
                    rows.append(dict(family=snap.family, date=snap.date, recipe=recipe, algo=algo, k=k, bic=bic,
                                     seed_ari=float(np.median(seeds)), own_silhouette=float(silhouette_score(x, labels))
                                     if len(set(labels)) > 1 else None, **evaluate(reference, labels, k)))
        if progress:
            progress(snap)
    return rows


def summarize(rows, cfg):
    """One line per (family, recipe, algo, k) with admissibility per the preregistered rule."""
    rule = cfg['admissible']
    groups = defaultdict(list)
    for r in rows:
        groups[r['family'], r['recipe'], r['algo'], r['k']].append(r)
    out = []
    for (family, recipe, algo, k), rs in groups.items():
        med = lambda key: float(np.median([r[key] for r in rs if r[key] is not None])) if any(r[key] is not None for r in rs) else None  # noqa: E731
        balanced = np.mean([r['min_share'] >= rule['min_cluster_share'] and r['k_used'] == k for r in rs])
        out.append(dict(family=family, recipe=recipe, algo=algo, k=k, snapshots=len(rs),
                        balanced_fraction=float(balanced), median_min_share=med('min_share'),
                        median_max_share=med('max_share'), median_balance=med('balance'),
                        median_silhouette=med('silhouette'), median_davies_bouldin=med('davies_bouldin'),
                        median_seed_ari=med('seed_ari'),
                        admissible=bool(balanced >= rule['share_of_snapshots'] and (med('seed_ari') or 0) >= rule['median_seed_ari'])))
    return out


def select(summary, family):
    rank_recipe = {'T1': 0, 'T2': 1, 'T0': 2}
    rank_algo = {'kmeans': 0, 'gmm': 1}
    ok = [s for s in summary if s['family'] == family and s['admissible'] and s['median_silhouette'] is not None]
    if not ok:
        return None
    best = max(s['median_silhouette'] for s in ok)
    near = [s for s in ok if s['median_silhouette'] >= best - 0.01]
    return min(near, key=lambda s: (s['k'], rank_recipe[s['recipe']], rank_algo[s['algo']]))


def full_series(snapshots, choice, cfg):
    """Fit the chosen config on every snapshot; temporal ARI on consecutive common tickers."""
    out, previous = [], None
    for snap in snapshots:
        labels, _ = fit(choice['algo'], snap.space(choice['recipe']), choice['k'], cfg['seed'], cfg)
        ev = evaluate(snap.space('T1'), labels, choice['k'])
        temporal = None
        if previous is not None:
            common = sorted(set(previous[0]) & set(snap.tickers))
            a = dict(zip(*previous))
            b = dict(zip(snap.tickers, labels))
            temporal = float(adjusted_rand_score([a[t] for t in common], [b[t] for t in common])) if common else None
        out.append(dict(date=snap.date, labels=dict(zip(snap.tickers, map(int, labels))), temporal_ari=temporal, **ev))
        previous = (snap.tickers, labels)
    return out


def profile(snap, labels):
    """Median raw feature per cluster: what each group means in original units."""
    lab = np.array([labels[t] for t in snap.tickers])
    rows = []
    for c in sorted(set(lab)):
        member = snap.raw[lab == c]
        rows.append(dict(cluster=int(c), size=int(len(member)),
                         **{f: float(np.median(member[:, j])) for j, f in enumerate(snap.features)}))
    return rows
