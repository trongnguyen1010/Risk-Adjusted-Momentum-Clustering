"""Build presentation bundle v2 with the owner-approved clustering (25/10/2026).

A = market features, log + winsorize + z-score, k-means k=4 (all 84 months)
B = new D-IND-01 indicators, non-financial companies, same transform, k-means k=3
C = December A + same fiscal-year B features, per-block transform + equal block
    variance, k-means k=3

Prices and securities are copied from the v1 bundle; v1 is left untouched.
Labels are renumbered by cluster size (0 = largest) within each snapshot.
"""
import argparse
from collections import defaultdict
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

from delta_t1.experiments import clustering_rework as cr  # noqa: E402
from delta_t1.product.terminal_export import encoded, quantiles  # noqa: E402

SOURCE = 'data/web/delta-intelligence-v1'
TARGET = 'data/web/delta-intelligence-v2'
INDICATORS = 'configs/product/indicators_v1.json'
REWORK = 'configs/experiments/clustering_rework_v1.json'
FINANCIAL = ('roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio', 'asset_turnover',
             'revenue_growth', 'cfo_to_ni')
K = {'market': 4, 'financial': 3, 'combined': 3}
SEED, N_INIT = 42, 10
NEW_DEFINITIONS = {
    'roe': ('ROE', 'LNST công ty mẹ / VCSH bình quân', 'percent'),
    'roa': ('ROA', 'LNST / tổng tài sản bình quân', 'percent'),
    'gross_margin': ('Biên lãi gộp', 'LN gộp / doanh thu thuần', 'percent'),
    'net_margin': ('Biên lãi ròng', 'LNST / doanh thu thuần', 'percent'),
    'debt_to_equity': ('Nợ / VCSH', 'Nợ phải trả / VCSH', 'ratio'),
    'current_ratio': ('Thanh toán hiện hành', 'TS ngắn hạn / nợ ngắn hạn', 'ratio'),
    'asset_turnover': ('Vòng quay tài sản', 'Doanh thu / tổng tài sản bình quân', 'ratio'),
    'revenue_growth': ('Tăng trưởng doanh thu', 'Doanh thu năm nay / năm trước − 1', 'percent'),
    'cfo_to_ni': ('Dòng tiền / lợi nhuận', 'CFO / LNST', 'ratio'),
}


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def cluster(x, k):
    """k-means, then renumber labels by size (0 = largest) so colors are comparable across dates."""
    labels = KMeans(n_clusters=k, n_init=N_INIT, random_state=SEED).fit_predict(x)
    order = np.argsort(-np.bincount(labels, minlength=k), kind='stable')
    remap = np.empty(k, dtype=int)
    remap[order] = np.arange(k)
    return remap[labels]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    source, target = ROOT / SOURCE, ROOT / TARGET
    if target.exists():
        raise SystemExit(f'{TARGET} already exists; bundles are immutable. Remove it explicitly to rebuild.')
    v1_manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    if sha(source / 'terminal.sqlite') != v1_manifest['database_sha256']:
        raise SystemExit('v1 bundle checksum mismatch')
    pointer = json.loads((ROOT / INDICATORS).read_text(encoding='utf-8'))
    if sha(ROOT / pointer['file']) != pointer['file_sha256']:
        raise SystemExit('indicators.sqlite checksum mismatch')
    cfg = json.loads((ROOT / REWORK).read_text(encoding='utf-8'))
    target.mkdir(parents=True)
    building = target / 'terminal.building.sqlite'
    shutil.copyfile(source / 'terminal.sqlite', building)
    db = sqlite3.connect(building)
    db.execute('PRAGMA journal_mode=OFF')
    security_id = dict(db.execute('select ticker, security_id from securities'))
    market_ids = {(d, t): s for d, t, s in db.execute("select date, ticker, security_id from observations where kind='market'")}
    old_meta = json.loads(db.execute("select value from metadata where key='overview'").fetchone()[0])
    for table in ('observations', 'snapshots', 'profiles', 'relations'):
        db.execute(f'delete from {table}')

    market = cr.load_terminal(source / 'terminal.sqlite', 'A')
    financial = cr.load_indicators(ROOT / pointer['file'], FINANCIAL)
    by_fy = {s.date: s for s in financial}
    labels = {}  # (kind, date) -> {ticker: label}
    snaps = {}

    def store(kind, snap, x, scope):
        lab = cluster(x, K[kind])
        labels[kind, snap.date] = dict(zip(snap.tickers, map(int, lab)))
        snaps[kind, snap.date] = snap
        ev = cr.evaluate(snap.space('T1'), lab, K[kind])
        sizes = {str(c): int((lab == c).sum()) for c in range(K[kind])}
        metrics = dict(silhouette=ev['silhouette'], davies_bouldin=ev['davies_bouldin'],
                       calinski_harabasz=ev['calinski_harabasz'], inertia=None, cluster_balance=ev['balance'],
                       min_cluster_size=min(sizes.values()), quality_status='OWNER_APPROVED_REWORK_V1')
        db.execute('insert into snapshots values (?,?,?,?,?,?,?)',
                   (kind, snap.date, len(lab), K[kind], encoded(sizes), encoded(metrics), scope))
        for c in range(K[kind]):
            member = snap.raw[lab == c]
            cols = {f: member[:, j].tolist() for j, f in enumerate(snap.features)}
            db.execute('insert into profiles values (?,?,?,?,?,?,?)',
                       (kind, snap.date, c, len(member), encoded({f: float(np.mean(v)) for f, v in cols.items()}),
                        encoded({f: statistics.median(v) for f, v in cols.items()}),
                        encoded({f: quantiles(v) for f, v in cols.items()})))
        rows = []
        for t, row, c in zip(snap.tickers, snap.raw, lab):
            sid = market_ids.get((snap.date, t)) if kind != 'financial' else security_id.get(t, t)
            rows.append((kind, snap.date, t, sid or security_id.get(t, t), int(c),
                         encoded(dict(zip(snap.features, map(float, row)))), scope))
        db.executemany('insert into observations values (?,?,?,?,?,?,?)', rows)
        print(f'{kind} {snap.date}: n={len(lab)} sizes={sorted(sizes.values(), reverse=True)} '
              f'sil={ev["silhouette"]:.3f}', flush=True)

    t0 = time.time()
    for snap in market:
        store('market', snap, snap.space('T1'), 'MARKET_ONLY_PROVISIONAL_IDENTITY_REWORK_V1')
    for snap in financial:
        store('financial', snap, snap.space('T1'), 'EX_POST_FISCAL_YEAR_REFERENCE_NOT_PIT')
    combined_dates = []
    for snap in market:
        fy = snap.date[:4]
        if snap.date[5:7] != '12' or fy not in by_fy:
            continue
        b = by_fy[fy]
        rows_b = dict(zip(b.tickers, b.raw))
        keep = [i for i, t in enumerate(snap.tickers) if t in rows_b]
        tickers = [snap.tickers[i] for i in keep]
        raw = np.hstack([snap.raw[keep], np.array([rows_b[t] for t in tickers])])
        joined = cr.Snapshot('C', snap.date, tickers, raw, cr.MARKET + FINANCIAL, (len(cr.MARKET), len(FINANCIAL)))
        store('combined', joined, joined.space('T1'), 'EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT')
        combined_dates.append(snap.date)
        # Year-end relations: every ticker seen in A (that date) or B (that FY).
        a, f, c = labels['market', snap.date], labels['financial', fy], labels['combined', snap.date]
        rel = []
        for t in sorted(set(a) | set(f)):
            coverage = 'BOTH' if t in a and t in f else 'MARKET_ONLY' if t in a else 'FINANCIAL_ONLY'
            rel.append((snap.date, t, a.get(t), f.get(t), c.get(t), coverage))
        db.executemany('insert into relations values (?,?,?,?,?,?)', rel)

    definitions = dict(old_meta['definitions'])
    for name, (label, formula, unit) in NEW_DEFINITIONS.items():
        definitions[name] = dict(label=label, formula=formula, unit=unit, family='financial')
    configs = old_meta['model_configs']
    configs['market'].update(k=K['market'], scaling='log(thanh khoản) + cắt đuôi 1–99% + z-score mỗi kỳ',
                             version='rework-v1 A k4')
    configs['financial'] = dict(k=K['financial'], scaling='cắt đuôi 1–99% + z-score mỗi năm', frequency='Annual FY',
                                features=list(FINANCIAL), version='rework-v1 B2 k3')
    configs['combined'] = dict(k=K['combined'], scaling='Mỗi khối cắt đuôi + z-score, cân phương sai 50/50',
                               frequency='Annual December reference', features=list(cr.MARKET) + list(FINANCIAL),
                               version='rework-v1 C k3')
    meta = dict(old_meta, generated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), bundle='delta-intelligence-v2',
                financial_periods=len(financial), combined_snapshots=len(combined_dates),
                financial_rows=sum(len(s.tickers) for s in financial), definitions=definitions, model_configs=configs,
                clustering=dict(source=REWORK, decision='Owner approval in chat 25/10/2026', seed=SEED, n_init=N_INIT,
                                labels='renumbered by size within each snapshot (0 = largest)'),
                limitations=['Financial FY / December joins are ex-post, not verified PIT.',
                             'Financial clusters cover non-financial companies with all nine indicators that year.',
                             'Cluster labels are descriptive, not investment recommendations.',
                             'Labels from independent fits at different dates do not share meaning.'])
    db.execute("delete from metadata where key='overview'")
    db.execute('insert into metadata values (?,?)', ('overview', encoded(meta)))
    db.commit()
    db.execute('VACUUM')
    db.execute('ANALYZE')
    db.close()
    final = target / 'terminal.sqlite'
    building.rename(final)
    sources = dict(v1_manifest['sources'])
    for rel in (SOURCE + '/terminal.sqlite', pointer['file'], REWORK, 'scripts/build_delta_bundle_v2.py',
                'src/delta_t1/experiments/clustering_rework.py', 'src/delta_t1/clustering/robust_transforms.py'):
        sources[rel] = dict(sha256=sha(ROOT / rel), size=(ROOT / rel).stat().st_size)
    manifest = dict(version='delta-intelligence-v1', bundle='delta-intelligence-v2', database='terminal.sqlite',
                    database_sha256=sha(final), sources=sources, metadata=meta)
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'bundle v2 built in {time.time() - t0:.0f}s: {final.relative_to(ROOT).as_posix()}')


if __name__ == '__main__':
    main()
