"""Build presentation bundle v3 (owner request 25/10/2026): fit on liquid stocks, assign the rest.

A = 9 market features (adds downside_vol_63), light liquidity filter, K-Means k=3 fitted on
    liquid stocks only; illiquid stocks are assigned to the nearest centroid and flagged
    liquidity='ILLIQUID' ("Kém thanh khoản"). Every ticker keeps a cluster.
C = December A (8 base features) + same-FY B features, per-block T1 + equal block variance,
    PCA(80%) + K-Means k=4 on liquid stocks; illiquid stocks assigned to the nearest centroid.
B = unchanged from bundle v2, flagged as exploratory (subsample stability 0.50).

Bundle v2 is copied and left untouched. Labels are renumbered by liquid cluster size.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score  # noqa: E402

from delta_t1.clustering.robust_transforms import apply_t1, fit_t1, nearest_centroid  # noqa: E402
from delta_t1.experiments import clustering_rework as cr  # noqa: E402
from delta_t1.experiments import clustering_rework_v2 as cr2  # noqa: E402
from delta_t1.product.terminal_export import encoded, quantiles  # noqa: E402

SOURCE = 'data/web/delta-intelligence-v2'
TARGET = 'data/web/delta-intelligence-v3'
INDICATORS = 'configs/product/indicators_v1.json'
CONFIG = 'configs/experiments/clustering_rework_v2.json'
SEED, N_INIT = 42, 10
K_MARKET, K_COMBINED = 3, 4
FINANCIAL = ('roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio', 'asset_turnover',
             'revenue_growth', 'cfo_to_ni')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def renumber(labels, k):
    order = np.argsort(-np.bincount(labels, minlength=k), kind='stable')
    remap = np.empty(k, dtype=int)
    remap[order] = np.arange(k)
    return remap[labels]


def summary_stats(member_rows, features):
    cols = {f: [r[j] for r in member_rows if r[j] is not None and np.isfinite(r[j])] for j, f in enumerate(features)}
    return ({f: float(np.mean(v)) if v else None for f, v in cols.items()},
            {f: statistics.median(v) if v else None for f, v in cols.items()},
            {f: quantiles(v) for f, v in cols.items()})


def fit_and_assign(x_liquid, x_illiquid, k, pca=False):
    """Fit on liquid rows; centroids are member means in the same space; assign illiquid rows."""
    z = PCA(n_components=0.8, svd_solver='full', random_state=SEED).fit_transform(x_liquid) if pca else x_liquid
    lab = renumber(KMeans(n_clusters=k, n_init=N_INIT, random_state=SEED).fit_predict(z), k)
    centroids = np.array([x_liquid[lab == c].mean(axis=0) for c in range(k)])
    assigned = nearest_centroid(x_illiquid, centroids) if len(x_illiquid) else np.array([], dtype=int)
    return lab, assigned


def quality(x, lab):
    return dict(silhouette=float(silhouette_score(x, lab)), davies_bouldin=float(davies_bouldin_score(x, lab)),
                calinski_harabasz=float(calinski_harabasz_score(x, lab)))


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    source, target = ROOT / SOURCE, ROOT / TARGET
    if target.exists():
        raise SystemExit(f'{TARGET} already exists; bundles are immutable.')
    v2 = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    if sha(source / 'terminal.sqlite') != v2['database_sha256']:
        raise SystemExit('v2 bundle checksum mismatch')
    pointer = json.loads((ROOT / INDICATORS).read_text(encoding='utf-8'))
    cfg = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    level = cfg['liquidity_filter']['levels']['light']
    a_features = tuple(cfg['feature_sets']['A_dvol'])
    c_market = tuple(cfg['feature_sets']['A_base'])

    t0 = time.time()
    market = cr.load_terminal(source / 'terminal.sqlite', 'A')
    activity = cr2.price_activity(source / 'terminal.sqlite', [s.date for s in market])
    financial = {s.date: s for s in cr.load_indicators(ROOT / pointer['file'], FINANCIAL)}
    print(f'inputs loaded in {time.time() - t0:.0f}s', flush=True)

    target.mkdir(parents=True)
    building = target / 'terminal.building.sqlite'
    shutil.copyfile(source / 'terminal.sqlite', building)
    db = sqlite3.connect(building)
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('ALTER TABLE observations ADD COLUMN liquidity TEXT')
    ids = {(d, t): s for d, t, s in db.execute("select date, ticker, security_id from observations where kind='market'")}
    financial_labels = {}
    for d, t, c in db.execute("select date, ticker, cluster from observations where kind='financial'"):
        financial_labels.setdefault(d, {})[t] = c
    meta = json.loads(db.execute("select value from metadata where key='overview'").fetchone()[0])
    db.execute("delete from observations where kind in ('market', 'combined')")
    db.execute("delete from snapshots where kind in ('market', 'combined')")
    db.execute("delete from profiles where kind in ('market', 'combined')")
    db.execute('delete from relations')

    def write(kind, date, tickers, raw, features, liquid_mask, lab_all, x_liquid, lab_liquid, scope, k):
        rows = []
        for t, r, c, liquid in zip(tickers, raw, lab_all, liquid_mask):
            values = {f: (float(v) if np.isfinite(v) else None) for f, v in zip(features, r)}
            rows.append((kind, date, t, ids.get((date[:10], t)) or t, int(c), encoded(values), scope,
                         'LIQUID' if liquid else 'ILLIQUID'))
        db.executemany('insert into observations values (?,?,?,?,?,?,?,?)', rows)
        sizes = {str(c): int((lab_all == c).sum()) for c in range(k)}
        illiquid = {str(c): int(((lab_all == c) & ~liquid_mask).sum()) for c in range(k)}
        metrics = dict(**quality(x_liquid, lab_liquid), inertia=None,
                       cluster_balance=float(min(np.bincount(lab_liquid, minlength=k)) / len(lab_liquid)),
                       min_cluster_size=min(sizes.values()), liquid_n=int(liquid_mask.sum()),
                       illiquid_n=int((~liquid_mask).sum()), illiquid_by_cluster=illiquid,
                       fitted_on='LIQUID_ONLY', quality_status='OWNER_APPROVED_REWORK_V2_LIGHT')
        db.execute('insert into snapshots values (?,?,?,?,?,?,?)',
                   (kind, date, len(tickers), k, encoded(sizes), encoded(metrics), scope))
        liquid_raw = raw[liquid_mask]
        for c in range(k):
            # Size counts every member (liquid + assigned) like snapshot sizes; the
            # medians/quartiles describe the liquid members that define the cluster.
            members = [list(r) for r in liquid_raw[lab_liquid == c]]
            means, medians, boxes = summary_stats(members, features)
            db.execute('insert into profiles values (?,?,?,?,?,?,?)',
                       (kind, date, c, int((lab_all == c).sum()), encoded(means), encoded(medians), encoded(boxes)))
        return dict(zip(tickers, map(int, lab_all))), metrics

    a_labels = {}
    for snap in market:
        act = activity[snap.date]
        obs = {t: dict(zip(snap.features, r)) for t, r in zip(snap.tickers, snap.raw)}
        raw = np.array([[obs[t][f] if f in obs[t] else (act.get(t, (None, np.nan))[1]) for f in a_features]
                        for t in snap.tickers], dtype=float)
        liquid = np.array([not cr2.illiquid(obs[t], act.get(t), level) for t in snap.tickers])
        liquid &= np.isfinite(raw).all(axis=1)
        params = fit_t1(raw[liquid], a_features)
        x_liquid = apply_t1(raw[liquid], params)
        lab_liquid, assigned = fit_and_assign(x_liquid, apply_t1(raw[~liquid], params), K_MARKET)
        lab_all = np.empty(len(snap.tickers), dtype=int)
        lab_all[liquid], lab_all[~liquid] = lab_liquid, assigned
        a_labels[snap.date], m = write('market', snap.date, snap.tickers, raw, a_features, liquid, lab_all, x_liquid,
                                       lab_liquid, 'MARKET_ONLY_PROVISIONAL_IDENTITY_FIT_LIQUID_V3', K_MARKET)
        a_liquid = dict(zip(snap.tickers, liquid))
        if snap.date[5:7] == '12':
            print(f'market {snap.date}: liquid {m["liquid_n"]} illiquid {m["illiquid_n"]} sizes '
                  f'{[int((lab_all == c).sum()) for c in range(K_MARKET)]} sil={m["silhouette"]:.3f}', flush=True)
        fy = snap.date[:4]
        if snap.date[5:7] != '12' or fy not in financial:
            continue
        b = financial[fy]
        rows_b = dict(zip(b.tickers, b.raw))
        tickers = [t for t in snap.tickers if t in rows_b]
        raw_c = np.array([[obs[t][f] for f in c_market] + list(rows_b[t]) for t in tickers], dtype=float)
        liq_c = np.array([a_liquid[t] for t in tickers])
        width = len(c_market)
        pa, pb = fit_t1(raw_c[liq_c, :width], c_market), fit_t1(raw_c[liq_c, width:], FINANCIAL)
        blocks = [apply_t1(raw_c[:, :width], pa), apply_t1(raw_c[:, width:], pb)]
        weights = [np.sqrt(0.5 / np.nanvar(blk[liq_c], axis=0).sum()) for blk in blocks]
        x_c = np.hstack([blk * w for blk, w in zip(blocks, weights)])
        lab_liquid, assigned = fit_and_assign(x_c[liq_c], x_c[~liq_c], K_COMBINED, pca=True)
        lab_c = np.empty(len(tickers), dtype=int)
        lab_c[liq_c], lab_c[~liq_c] = lab_liquid, assigned
        c_labels, mc = write('combined', snap.date, tickers, raw_c, c_market + FINANCIAL, liq_c, lab_c, x_c[liq_c],
                             lab_liquid, 'EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT_FIT_LIQUID_V3', K_COMBINED)
        print(f'combined {snap.date}: liquid {mc["liquid_n"]} illiquid {mc["illiquid_n"]} sizes '
              f'{[int((lab_c == c).sum()) for c in range(K_COMBINED)]} sil={mc["silhouette"]:.3f}', flush=True)
        f_lab = financial_labels.get(fy, {})
        rel = []
        for t in sorted(set(a_labels[snap.date]) | set(f_lab)):
            a, f = a_labels[snap.date].get(t), f_lab.get(t)
            coverage = 'BOTH' if a is not None and f is not None else 'MARKET_ONLY' if a is not None else 'FINANCIAL_ONLY'
            rel.append((snap.date, t, a, f, c_labels.get(t), coverage))
        db.executemany('insert into relations values (?,?,?,?,?,?)', rel)

    meta['definitions']['downside_vol_63'] = dict(label='Biến động giảm · 63 phiên',
                                                  formula='sqrt(mean(min(r,0)^2)) × sqrt(252), lợi suất ngày giá điều chỉnh',
                                                  unit='ratio', family='market')
    filter_text = (f'Kém thanh khoản: >{level["zero_volume_share_gt"]:.0%} phiên không khớp trong 63 phiên hoặc '
                   f'giá trị giao dịch < {level["liquidity_21_lt"] / 1e6:.0f} triệu đ/ngày; được gán vào cụm gần nhất')
    configs = meta['model_configs']
    configs['market'].update(k=K_MARKET, features=list(a_features), version='rework-v2 A light k3',
                             scaling='log(thanh khoản) + cắt đuôi 1–99% + z-score, học trên mã có giao dịch',
                             liquidity_filter=filter_text)
    configs['combined'].update(k=K_COMBINED, features=list(c_market) + list(FINANCIAL), version='rework-v2 C light pca k4',
                               scaling='Mỗi khối cắt đuôi + z-score, cân 50/50, PCA 80% + K-Means; học trên mã có giao dịch',
                               liquidity_filter=filter_text)
    configs['financial']['stability_note'] = ('Chưa ổn định: khi bỏ ngẫu nhiên 10% số mã, nhóm chỉ giữ được '
                                              'khoảng 50% (ARI 0,50). Chỉ dùng để tham khảo.')
    meta.update(generated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), bundle='delta-intelligence-v3',
                clustering=dict(meta.get('clustering', {}), v3=dict(source=CONFIG, decision='Owner approval in chat 25/10/2026',
                                fit='liquid stocks only', assignment='nearest centroid for illiquid stocks')))
    db.execute("delete from metadata where key='overview'")
    db.execute('insert into metadata values (?,?)', ('overview', encoded(meta)))
    db.commit()
    db.execute('VACUUM')
    db.execute('ANALYZE')
    db.close()
    final = target / 'terminal.sqlite'
    building.rename(final)
    sources = dict(v2['sources'])
    for rel in (SOURCE + '/terminal.sqlite', pointer['file'], CONFIG, 'scripts/build_delta_bundle_v3.py',
                'src/delta_t1/clustering/robust_transforms.py', 'src/delta_t1/experiments/clustering_rework_v2.py'):
        sources[rel] = dict(sha256=sha(ROOT / rel), size=(ROOT / rel).stat().st_size)
    manifest = dict(version='delta-intelligence-v1', bundle='delta-intelligence-v3', database='terminal.sqlite',
                    database_sha256=sha(final), sources=sources, metadata=meta)
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'bundle v3 built in {time.time() - t0:.0f}s: {final.relative_to(ROOT).as_posix()}')


if __name__ == '__main__':
    main()
