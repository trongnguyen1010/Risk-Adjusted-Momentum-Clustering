"""Clustering rework v2: liquidity eligibility, Ward / PCA+K-Means comparators, multi-metric selection.

Descriptive and ex post only. Illiquid tickers get their own label (-1) and are
left out of fitting and of every metric. Nothing here changes the served model.
"""
from collections import defaultdict
import json
import math
import sqlite3

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture

from .clustering_rework import Snapshot, _matrix, _observations

ALGO_ORDER = ('kmeans', 'pca_kmeans', 'ward', 'gmm')
ILLIQUID = -1


# ---------- inputs -----------------------------------------------------------

def price_activity(db_path, dates, window=63):
    """zero_volume_share_63 and downside_vol_63 per (ticker, snapshot date), from served prices."""
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as db:
        prices = pd.read_sql('select ticker, date, volume, adj_close from prices order by ticker, date', db)
    prices['idle'] = (prices['volume'].fillna(0) <= 0).astype(float)
    g = prices.groupby('ticker', sort=False)
    prices['ret'] = g['adj_close'].pct_change(fill_method=None)
    prices['down2'] = np.minimum(prices['ret'], 0) ** 2
    g = prices.groupby('ticker', sort=False)
    prices['zero_volume_share_63'] = g['idle'].transform(lambda s: s.rolling(window, min_periods=window).mean())
    prices['downside_vol_63'] = np.sqrt(g['down2'].transform(lambda s: s.rolling(window, min_periods=window).mean())) * math.sqrt(252)
    out = {}
    for date in dates:
        last = prices[prices['date'] <= date].groupby('ticker').tail(1)
        out[date] = {t: (z, d) for t, z, d in last[['ticker', 'zero_volume_share_63', 'downside_vol_63']].itertuples(index=False)}
    return out


def illiquid(features, activity, level):
    zero = activity[0] if activity else None
    if zero is None or not np.isfinite(zero):
        return True  # Fewer than 63 sessions observed: not eligible.
    return zero > level['zero_volume_share_gt'] or features['liquidity_21'] < level['liquidity_21_lt']


def market_snapshots(db_path, features, level, months=None, activity=None):
    """Liquid tickers as a Snapshot plus the list of illiquid tickers per date."""
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as db:
        obs = _observations(db, 'market')
    dates = [d for d in sorted(obs) if months is None or d[5:7] in months]
    activity = activity or price_activity(db_path, dates)
    snaps, excluded = [], {}
    for d in dates:
        liquid, out = {}, []
        for t, f in obs[d].items():
            act = activity[d].get(t)
            if illiquid(f, act, level):
                out.append(t)
            else:
                liquid[t] = {**f, 'downside_vol_63': act[1]}
        tickers, raw = _matrix(liquid, features)
        snaps.append(Snapshot('A', d, tickers, raw, features))
        excluded[d] = sorted(out)
    return snaps, excluded


def financial_snapshots(indicators_path, features, years=range(2017, 2026)):
    derived = {'earnings_yield', 'book_to_price', 'log_market_cap'}
    base = [f for f in features if f not in derived]
    need = sorted(set(base) | ({'eps', 'bvps', 'price', 'market_cap'} if derived & set(features) else set()))
    with sqlite3.connect(f'file:{indicators_path}?mode=ro', uri=True) as db:
        allowed = {t for (t,) in db.execute("select ticker from company where sector_group = 'NON_FINANCIAL'")}
        marks = ','.join('?' * len(need))
        rows = db.execute(f"select ticker, fiscal_year, metric, value from indicator_values where status = 'OK' "
                          f"and metric in ({marks})", tuple(need)).fetchall()
    data = defaultdict(lambda: defaultdict(dict))
    for t, y, m, v in rows:
        if t in allowed:
            data[y][t][m] = v
    snaps = []
    for y in years:
        cells = {}
        for t, f in data.get(y, {}).items():
            f = dict(f)
            if derived & set(features):
                price = f.get('price')
                f['earnings_yield'] = f['eps'] / price if price and 'eps' in f else None
                f['book_to_price'] = f['bvps'] / price if price and 'bvps' in f else None
                f['log_market_cap'] = math.log(f['market_cap']) if f.get('market_cap') else None
            cells[t] = f
        tickers, raw = _matrix(cells, features)
        snaps.append(Snapshot('B', str(y), tickers, raw, features))
    return snaps


def combined_snapshots(market, financial):
    by_fy = {s.date: s for s in financial}
    out = []
    for m in market:
        fy = m.date[:4]
        if m.date[5:7] != '12' or fy not in by_fy:
            continue
        b = by_fy[fy]
        rows_b = dict(zip(b.tickers, b.raw))
        keep = [i for i, t in enumerate(m.tickers) if t in rows_b]
        tickers = [m.tickers[i] for i in keep]
        raw = np.hstack([m.raw[keep], np.array([rows_b[t] for t in tickers])]) if keep else np.empty((0, len(m.features) + len(b.features)))
        out.append(Snapshot('C', m.date, tickers, raw, tuple(m.features) + tuple(b.features), (len(m.features), len(b.features))))
    return out


# ---------- fitting and metrics ---------------------------------------------

def fit(algo, x, k, seed, cfg):
    a = cfg['algorithms']
    if algo == 'kmeans':
        return KMeans(n_clusters=k, n_init=a['kmeans']['n_init'], random_state=seed).fit_predict(x)
    if algo == 'pca_kmeans':
        z = PCA(n_components=a['pca_kmeans']['variance'], svd_solver='full', random_state=seed).fit_transform(x)
        return KMeans(n_clusters=k, n_init=a['pca_kmeans']['n_init'], random_state=seed).fit_predict(z)
    if algo == 'ward':
        return AgglomerativeClustering(n_clusters=k, linkage='ward').fit_predict(x)
    g = a['gmm']
    return GaussianMixture(n_components=k, covariance_type=g['covariance_type'], n_init=g['n_init'],
                           reg_covar=g['reg_covar'], max_iter=g['max_iter'], random_state=seed).fit(x).predict(x)


def stability(algo, x, k, labels, cfg):
    s = cfg['stability']
    scores = []
    for seed in s['seeds']:
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(len(x), size=int(len(x) * s['subsample']), replace=False))
        scores.append(adjusted_rand_score(labels[idx], fit(algo, x[idx], k, seed, cfg)))
    return float(np.median(scores))


def metrics(x, labels, k):
    counts = np.bincount(labels, minlength=k)
    used = counts[counts > 0]
    shares = used / len(labels)
    out = dict(n=int(len(labels)), k_used=int(len(used)), min_share=float(shares.min()), max_share=float(shares.max()),
               sizes=sorted(map(int, used), reverse=True))
    if len(used) > 1:
        out.update(silhouette=float(silhouette_score(x, labels)), davies_bouldin=float(davies_bouldin_score(x, labels)),
                   calinski_harabasz=float(calinski_harabasz_score(x, labels)))
    else:
        out.update(silhouette=None, davies_bouldin=None, calinski_harabasz=None)
    return out


def sweep(snapshots, cfg, group, progress=None):
    """One row per (snapshot, algo, k); temporal ARI filled per config afterwards."""
    rows, labels = [], {}
    for snap in snapshots:
        x = snap.space('T1')
        for algo in ALGO_ORDER:
            for k in cfg['k']:
                if len(x) < 10 * k:
                    continue
                lab = fit(algo, x, k, cfg['seed'], cfg)
                labels[algo, k, snap.date] = dict(zip(snap.tickers, lab))
                rows.append(dict(group=group, date=snap.date, algo=algo, k=k,
                                 stability=stability(algo, x, k, lab, cfg), **metrics(x, lab, k)))
        if progress:
            progress(snap)
    dates = [s.date for s in snapshots]
    for r in rows:
        i = dates.index(r['date'])
        prev = labels.get((r['algo'], r['k'], dates[i - 1])) if i else None
        cur = labels[r['algo'], r['k'], r['date']]
        common = sorted(set(prev) & set(cur)) if prev else []
        r['temporal_ari'] = float(adjusted_rand_score([prev[t] for t in common], [cur[t] for t in common])) if len(common) > 1 else None
    return rows, labels


def summarize(rows, cfg):
    rule = cfg['admissible']
    groups = defaultdict(list)
    for r in rows:
        groups[r['group'], r['algo'], r['k']].append(r)

    def med(rs, key):
        vals = [r[key] for r in rs if r[key] is not None]
        return float(np.median(vals)) if vals else None

    out = []
    for (group, algo, k), rs in groups.items():
        balanced = float(np.mean([r['min_share'] >= rule['min_cluster_share'] and r['k_used'] == k for r in rs]))
        s = dict(group=group, algo=algo, k=k, snapshots=len(rs), balanced_fraction=balanced,
                 median_n=med(rs, 'n'), median_min_share=med(rs, 'min_share'), median_max_share=med(rs, 'max_share'),
                 silhouette=med(rs, 'silhouette'), davies_bouldin=med(rs, 'davies_bouldin'),
                 calinski_harabasz=med(rs, 'calinski_harabasz'), stability=med(rs, 'stability'),
                 temporal_ari=med(rs, 'temporal_ari'))
        s['admissible'] = bool(balanced >= rule['share_of_snapshots'] and (s['stability'] or 0) >= rule['median_stability'])
        out.append(s)
    return rank(out)


RANKED = (('silhouette', True), ('davies_bouldin', False), ('calinski_harabasz', True), ('stability', True),
          ('temporal_ari', True))


def rank(summary):
    """Mean rank over five metrics among admissible configs of the same group (1 = best)."""
    by_group = defaultdict(list)
    for s in summary:
        s['score'] = None
        if s['admissible']:
            by_group[s['group']].append(s)
    for items in by_group.values():
        for metric, higher in RANKED:
            values = pd.Series([s[metric] if s[metric] is not None else (-np.inf if higher else np.inf) for s in items])
            ranks = values.rank(ascending=not higher, method='average')
            for s, r in zip(items, ranks):
                s.setdefault('ranks', {})[metric] = float(r)
        for s in items:
            s['score'] = float(np.mean(list(s['ranks'].values())))
    return summary


def select(summary, group):
    ok = [s for s in summary if s['group'] == group and s['score'] is not None]
    if not ok:
        return None
    return min(ok, key=lambda s: (s['score'], s['k'], ALGO_ORDER.index(s['algo'])))


def profile(snap, labels):
    lab = np.array([labels[t] for t in snap.tickers])
    return [dict(cluster=int(c), size=int((lab == c).sum()),
                 **{f: float(np.median(snap.raw[lab == c, j])) for j, f in enumerate(snap.features)})
            for c in sorted(set(lab))]


def json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    raise TypeError(type(value))


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=json_default), encoding='utf-8')
