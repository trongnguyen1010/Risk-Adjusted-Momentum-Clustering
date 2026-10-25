"""Bundle v4 = bundle v3 + presentation layer (owner request 25/10/2026). Clusters are NOT refitted.

Adds, per snapshot:
- a 2-D "model map": PCA of the same transformed space the model used (fitted on the
  rows that defined the clusters), stored as display features _map_x/_map_y;
- a plain-language name and one-sentence description per cluster (profiles.name,
  profiles.description), derived from which features differ most from the fitted cohort;
- boundary_share (rows whose second-nearest centroid is within 10%) and map_variance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402

from delta_t1.clustering.robust_transforms import apply_t1, fit_t1  # noqa: E402
from delta_t1.product.cluster_story import describe_clusters  # noqa: E402
from delta_t1.product.terminal_export import encoded  # noqa: E402

SOURCE = 'data/web/delta-intelligence-v3'
TARGET = 'data/web/delta-intelligence-v4'
SEED = 42
VI = 'web/frontend/lib/vi.json'
MARKET_WIDTH = 8  # combined = 8 market features + financial block (bundle v3)


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def model_space(raw, features, fit_mask, kind):
    """(space the model used, unweighted z-scores). Fitted on the rows that defined the clusters.

    Combined weights each block to equal variance, which shrinks per-feature z; names are
    read from the unweighted z-scores so a 0.5 SD difference means the same in A, B and C.
    """
    if kind != 'combined':
        z = apply_t1(raw, fit_t1(raw[fit_mask], features))
        return z, z
    blocks, plain = [], []
    for lo, hi in ((0, MARKET_WIDTH), (MARKET_WIDTH, len(features))):
        part = apply_t1(raw[:, lo:hi], fit_t1(raw[fit_mask, lo:hi], features[lo:hi]))
        plain.append(part)
        blocks.append(part * np.sqrt(0.5 / np.nanvar(part[fit_mask], axis=0).sum()))
    return np.hstack(blocks), np.hstack(plain)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    source, target = ROOT / SOURCE, ROOT / TARGET
    if target.exists():
        raise SystemExit(f'{TARGET} already exists; bundles are immutable.')
    v3 = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    if sha(source / 'terminal.sqlite') != v3['database_sha256']:
        raise SystemExit('v3 bundle checksum mismatch')
    t0 = time.time()
    target.mkdir(parents=True)
    building = target / 'terminal.building.sqlite'
    shutil.copyfile(source / 'terminal.sqlite', building)
    db = sqlite3.connect(building)
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('ALTER TABLE profiles ADD COLUMN name TEXT')
    db.execute('ALTER TABLE profiles ADD COLUMN description TEXT')
    meta = json.loads(db.execute("select value from metadata where key='overview'").fetchone()[0])
    definitions = meta['definitions']
    # Stored labels are English source labels (the UI translates them); stories are Vietnamese text.
    vi = json.loads((ROOT / VI).read_text(encoding='utf-8'))
    labels_vi = {f: dict(d, label=vi.get(d['label'], d['label'])) for f, d in definitions.items()}
    for kind in ('market', 'financial', 'combined'):
        features = tuple(meta['model_configs'][kind]['features'])
        for (date,) in db.execute('select date from snapshots where kind=? order by date', (kind,)).fetchall():
            rows = db.execute('select ticker, features, cluster, liquidity from observations where kind=? and date=? '
                              'order by ticker', (kind, date)).fetchall()
            values = [json.loads(r[1]) for r in rows]
            raw = np.array([[v.get(f) if v.get(f) is not None else np.nan for f in features] for v in values], dtype=float)
            labels = np.array([r[2] for r in rows])
            fit_mask = np.array([r[3] in (None, 'LIQUID') for r in rows]) & np.isfinite(raw).all(axis=1)
            z, z_plain = model_space(raw, features, fit_mask, kind)
            z_filled = np.where(np.isfinite(z), z, 0.0)  # display only: a missing feature sits at the cohort mean
            pca = PCA(n_components=2, random_state=SEED).fit(z_filled[fit_mask])
            coords = pca.transform(z_filled)
            if coords[fit_mask][labels[fit_mask] == labels[fit_mask].max(), 0].mean() < 0:
                coords[:, 0] = -coords[:, 0]  # stable orientation across dates
            updates = []
            for (ticker, _, cluster, _), v, (cx, cy) in zip(rows, values, coords):
                v['_map_x'], v['_map_y'] = round(float(cx), 4), round(float(cy), 4)
                updates.append((encoded(v), kind, date, ticker))
            db.executemany('update observations set features=? where kind=? and date=? and ticker=?', updates)
            ks = sorted(set(labels))
            centroids = np.array([z_filled[fit_mask & (labels == c)].mean(axis=0) for c in ks])
            d = np.sqrt(((z_filled[fit_mask][:, None, :] - centroids[None]) ** 2).sum(axis=2))
            d.sort(axis=1)
            boundary = float((d[:, 1] / np.maximum(d[:, 0], 1e-12) < 1.1).mean())
            stories = describe_clusters(raw[fit_mask], z_plain[fit_mask], labels[fit_mask], features, labels_vi)
            for c, story in stories.items():
                db.execute('update profiles set name=?, description=? where kind=? and date=? and cluster=?',
                           (story['name'], story['description'], kind, date, int(c)))
            snap = json.loads(db.execute('select metrics from snapshots where kind=? and date=?', (kind, date)).fetchone()[0])
            snap.update(boundary_share=boundary, map_variance=float(pca.explained_variance_ratio_.sum()),
                        fitted_n=int(fit_mask.sum()))
            db.execute('update snapshots set metrics=? where kind=? and date=?', (encoded(snap), kind, date))
            if date.endswith('12-31') or kind == 'financial' and date == '2025':
                print(f'{kind} {date}: boundary {boundary:.2f}, map {pca.explained_variance_ratio_.sum():.2f}, '
                      + ' | '.join(f'{c}: {s["name"]}' for c, s in stories.items()), flush=True)
    definitions['_map_x'] = dict(label='Trục chính 1', formula='PCA của không gian mô hình', unit='ratio', family='map')
    definitions['_map_y'] = dict(label='Trục chính 2', formula='PCA của không gian mô hình', unit='ratio', family='map')
    meta.update(generated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), bundle='delta-intelligence-v4',
                presentation=dict(map='PCA 2D of the model space, fitted on rows that defined the clusters',
                                  names='derived from feature medians vs the fitted cohort; clusters unchanged from v3'))
    db.execute("update metadata set value=? where key='overview'", (encoded(meta),))
    db.commit()
    db.execute('VACUUM')
    db.execute('ANALYZE')
    db.close()
    final = target / 'terminal.sqlite'
    building.rename(final)
    sources = dict(v3['sources'])
    for rel in (SOURCE + '/terminal.sqlite', 'scripts/build_delta_bundle_v4.py', 'src/delta_t1/product/cluster_story.py', VI):
        sources[rel] = dict(sha256=sha(ROOT / rel), size=(ROOT / rel).stat().st_size)
    manifest = dict(version='delta-intelligence-v1', bundle='delta-intelligence-v4', database='terminal.sqlite',
                    database_sha256=sha(final), sources=sources, metadata=meta)
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'bundle v4 built in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
