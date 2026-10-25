"""Fair comparison: M2 handoff (K-Means K=2, RobustScaler, 8 features) vs market model A of bundle v4
(K-Means k=3 on liquid stocks, T1 = log liquidity + winsorize + z-score, 9 features).

Both are scored on the SAME tickers (in the M2 universe and LIQUID in v4) and in the SAME feature spaces
(8 shared features): S1 = M2's robust scaling, S2 = T1. Development (≤ 2023-12-29) and holdout are reported
apart. Cluster metrics only — no returns. Output: data/experiments/m2_vs_rework/<run_id>/.

Usage: python scripts/compare_m2_vs_rework.py
"""
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.clustering.robust_transforms import apply_t1, fit_t1, robust  # noqa: E402
from delta_t1.m3 import inputs  # noqa: E402

BASE = ['mom_21', 'mom_63', 'mom_126', 'mom_252', 'vol_63', 'mdd_126', 'beta_126', 'liquidity_21']
NEW = BASE[:5] + ['downside_vol_63'] + BASE[5:]
DEV_END = '2023-12-29'
SEED, N_INIT, SUBSAMPLE, SEEDS = 42, 10, 0.9, (1, 2, 3)
OUT = ROOT / 'data/experiments/m2_vs_rework'


def kmeans(x, k, seed=SEED):
    return KMeans(n_clusters=k, n_init=N_INIT, random_state=seed).fit_predict(x)


def m2_space(raw):
    return robust(raw)


def t1_space(raw, features):
    return apply_t1(raw, fit_t1(raw, features))


def between_share(x, labels, features):
    """Share of between-cluster variance carried by each feature (sums to 1)."""
    mu = x.mean(axis=0)
    b = np.zeros(x.shape[1])
    for c in np.unique(labels):
        part = x[labels == c]
        b += len(part) * (part.mean(axis=0) - mu) ** 2
    return dict(zip(features, (b / b.sum()).tolist()))


def scores(x, labels):
    if len(np.unique(labels)) < 2:
        return dict(silhouette=None, davies_bouldin=None)
    return dict(silhouette=float(silhouette_score(x, labels, sample_size=min(2000, len(x)), random_state=SEED)),
                davies_bouldin=float(davies_bouldin_score(x, labels)))


def stability(x, k):
    """Median ARI between the full fit and a refit on a 90% subsample (rework v2 definition)."""
    full = kmeans(x, k)
    out = []
    for s in SEEDS:
        idx = np.random.default_rng(s).choice(len(x), int(SUBSAMPLE * len(x)), replace=False)
        out.append(adjusted_rand_score(full[idx], kmeans(x[idx], k, seed=s)))
    return float(np.median(out))


def main():
    market = inputs.market_snapshots()
    text = subprocess.run(['git', 'show', inputs.M2_LABELS_REF], cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8').stdout
    m2 = inputs.m2_labels(text)
    rows, previous = [], {}
    for date in sorted(set(market) & set(m2)):
        snap = {r['ticker']: r for r in market[date]}
        m2_t = [t for t in sorted(m2[date]) if t in snap and all(snap[t]['features'].get(f) is not None for f in BASE)]
        liquid = [t for t, r in sorted(snap.items()) if r['liquidity'] != 'ILLIQUID'
                  and all(r['features'].get(f) is not None for f in NEW)]
        common = sorted(set(m2_t) & set(liquid))
        raw_m2 = np.array([[snap[t]['features'][f] for f in BASE] for t in m2_t])
        raw_new = np.array([[snap[t]['features'][f] for f in NEW] for t in liquid])
        raw_common = np.array([[snap[t]['features'][f] for f in BASE] for t in common])
        lab_m2 = {t: m2[date][t] for t in m2_t}
        lab_new = {t: snap[t]['cluster'] for t in liquid}
        # Replication check: our refit of each pipeline vs the served labels.
        x_m2 = m2_space(raw_m2)
        x_new = t1_space(raw_new, NEW)
        rep_m2 = adjusted_rand_score([lab_m2[t] for t in m2_t], kmeans(x_m2, 2))
        rep_new = adjusted_rand_score([lab_new[t] for t in liquid], kmeans(x_new, 3))
        row = dict(date=date, segment='development' if date <= DEV_END else 'holdout', n_m2=len(m2_t),
                   n_liquid=len(liquid), n_common=len(common), replication_m2=rep_m2, replication_new=rep_new,
                   stability_m2=stability(x_m2, 2), stability_new=stability(x_new, 3))
        for space, x in (('S1_robust', m2_space(raw_common)), ('S2_t1', t1_space(raw_common, BASE))):
            for name, lab in (('m2', lab_m2), ('new', lab_new)):
                labels = np.array([lab[t] for t in common])
                sc = scores(x, labels)
                share = between_share(x, labels, BASE)
                sizes = np.bincount(labels) / len(labels)
                row.update({f'{name}_{space}_silhouette': sc['silhouette'], f'{name}_{space}_db': sc['davies_bouldin'],
                            f'{name}_{space}_liquidity_share': share['liquidity_21'],
                            f'{name}_{space}_momentum_share': sum(share[f] for f in BASE[:4]),
                            f'{name}_{space}_risk_share': sum(share[f] for f in ('vol_63', 'mdd_126', 'beta_126')),
                            f'{name}_min_share': float(sizes[sizes > 0].min())})
        for name, lab in (('m2', lab_m2), ('new', lab_new)):
            prev = previous.get(name)
            if prev:
                both = sorted(set(prev) & set(lab) & set(common))
                row[f'{name}_temporal_ari'] = adjusted_rand_score([prev[t] for t in both], [lab[t] for t in both])
            previous[name] = lab
        rows.append(row)
        print(date, f"n={len(common)} rep={rep_m2:.2f}/{rep_new:.2f} "
                    f"sil S2 m2={row['m2_S2_t1_silhouette']:.3f} new={row['new_S2_t1_silhouette']:.3f} "
                    f"liq m2={row['m2_S2_t1_liquidity_share']:.2f} new={row['new_S2_t1_liquidity_share']:.2f}",
              flush=True)
    keys = [k for k in rows[-1] if k not in ('date', 'segment')]
    summary = {}
    for seg in ('development', 'holdout'):
        part = [r for r in rows if r['segment'] == seg]
        summary[seg] = {k: float(np.median([r[k] for r in part if r.get(k) is not None])) for k in keys}
        summary[seg]['months'] = len(part)
        summary[seg]['m2_min_share_below_5pct'] = sum(r['m2_min_share'] < 0.05 for r in part)
        summary[seg]['new_min_share_below_5pct'] = sum(r['new_min_share'] < 0.05 for r in part)
    body = json.dumps(rows, sort_keys=True).encode()
    out = OUT / ('cmp-' + hashlib.sha256(body).hexdigest()[:16])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'monthly.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    (out / 'summary.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    print(out)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
