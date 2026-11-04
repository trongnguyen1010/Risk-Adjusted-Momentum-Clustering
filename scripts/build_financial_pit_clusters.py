"""Build the B-PIT Financial clustering artifact for official M3 (ADR D-M3-01, plan §3.1.5 / §5.2.A).

Reads (read-only): Indicators v1 (configs/product/indicators_v1.json), the availability table (src/delta_t1/m3/inputs.py)
and, for the ARI audit only, B v4 labels from bundle v4. Never reads prices or returns.

Writes data/financial/b_pit_v1/bpit-<sha16>/:
  labels.csv     ticker, fiscal_year, cluster, role (FIT | ASSIGNED_AFTER_CUTOFF | ASSIGNED_NO_DATE), usable_from_date
  models.json    per fiscal year: cutoff, n_fit, n_assigned, T1 params, centroids, cluster_order, profile
  audit.json     fit-leak check (must be empty), ARI vs B v4, label agreement, sizes
  manifest.json  input hashes, code hashes, git commit, labels_sha256 (pin this value in the M3 config)

Usage: python scripts/build_financial_pit_clusters.py
Then copy the printed artifact path and labels_sha256 into configs/experiments/m3_strategy_v1.json → financial_pit.
"""
import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np  # noqa: E402
from sklearn.metrics import adjusted_rand_score  # noqa: E402

from delta_t1.experiments import clustering_rework as cr  # noqa: E402
from delta_t1.m3 import bpit, inputs  # noqa: E402

POINTER = ROOT / 'configs/product/indicators_v1.json'
CODE = ('scripts/build_financial_pit_clusters.py', 'src/delta_t1/m3/bpit.py',
        'src/delta_t1/m3/inputs.py',
        'src/delta_t1/clustering/robust_transforms.py', 'src/delta_t1/experiments/clustering_rework.py')


def rel(path):
    path = Path(path)
    return (str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)).replace('\\', '/')


def git_commit():
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', *CODE], cwd=ROOT, capture_output=True,
                           text=True).stdout.strip()
    return dict(commit=head or None, code_dirty=bool(dirty))


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    pointer = json.loads(POINTER.read_text(encoding='utf-8'))
    indicators_path = ROOT / pointer['file']
    if inputs.sha256(indicators_path) != pointer['file_sha256']:
        raise SystemExit('indicators.sqlite checksum does not match configs/product/indicators_v1.json')
    snapshots = cr.load_indicators(indicators_path, bpit.FEATURES)
    availability = inputs.availability()
    b_v4 = inputs.financial_labels()

    label_rows, models, audit = [], {}, dict(fit_leaks={}, years={})
    for snap in snapshots:
        fy = int(snap.date)
        usable = [availability.get((t, fy), {}).get('usable_from_date', '') for t in snap.tickers]
        cutoff = bpit.cutoff_for(fy, usable)
        n_ready = sum(bool(d) and d <= cutoff for d in usable)
        if n_ready < 2 * bpit.K:
            # e.g. the latest fiscal year whose reports are not yet inside the price calendar (CALENDAR_PENDING):
            # no decision can use it yet, so it gets no labels instead of a fit on too few reports.
            audit['years'][fy] = dict(status='NOT_READY_TOO_FEW_USABLE_REPORTS', cutoff=cutoff, n=len(snap.tickers),
                                      n_usable_at_cutoff=n_ready)
            print(f'FY{fy}: skipped, {n_ready} reports usable at cutoff {cutoff}', flush=True)
            continue
        res = bpit.build_year(fy, snap.tickers, snap.raw, usable)
        leaks = bpit.fit_leaks(usable, res['fitted'], res['cutoff'])
        if leaks:
            audit['fit_leaks'][fy] = [snap.tickers[i] for i in leaks]
        for t, c, f, d in zip(snap.tickers, res['labels'], res['fitted'], usable):
            role = 'FIT' if f else ('ASSIGNED_AFTER_CUTOFF' if d else 'ASSIGNED_NO_DATE')
            label_rows.append(dict(ticker=t, fiscal_year=fy, cluster=int(c), role=role, usable_from_date=d))
        ref = b_v4.get(fy, {})
        common = [i for i, t in enumerate(snap.tickers) if t in ref]
        ari = (float(adjusted_rand_score([ref[snap.tickers[i]][0] for i in common], res['labels'][common]))
               if len(common) > 1 else None)
        p = res['params']
        models[fy] = dict(cutoff=res['cutoff'], n_fit=res['n_fit'], n_assigned=res['n_assigned'],
                          features=list(bpit.FEATURES), k=bpit.K, seed=bpit.SEED, n_init=bpit.N_INIT,
                          t1=dict(lo=p['lo'].tolist(), hi=p['hi'].tolist(), mean=p['mean'].tolist(),
                                  sd=p['sd'].tolist()),
                          centroids=np.asarray(res['centroids']).tolist(), cluster_order=res['cluster_order'],
                          profile={str(c): v for c, v in res['profile'].items()})
        audit['years'][fy] = dict(status='OK', cutoff=res['cutoff'], n=len(snap.tickers), n_fit=res['n_fit'],
                                  n_assigned=res['n_assigned'],
                                  sizes={str(c): int((res['labels'] == c).sum()) for c in range(bpit.K)},
                                  ari_vs_b_v4=ari, n_common_with_b_v4=len(common),
                                  cluster_order=res['cluster_order'])
        print(f"FY{fy}: cutoff {res['cutoff']}, fit {res['n_fit']}, assigned {res['n_assigned']}, "
              f"order {res['cluster_order']}, ARI vs B v4 {ari}", flush=True)
    if audit['fit_leaks']:
        raise SystemExit(f"PIT audit FAILED: reports fitted after their cutoff: {audit['fit_leaks']}")

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=['ticker', 'fiscal_year', 'cluster', 'role', 'usable_from_date'],
                       lineterminator='\n')
    w.writeheader()
    w.writerows(sorted(label_rows, key=lambda r: (r['fiscal_year'], r['ticker'])))
    body = buf.getvalue()
    labels_sha = hashlib.sha256(body.encode()).hexdigest()
    out = inputs.BPIT_BASE / f'bpit-{labels_sha[:16]}'
    if out.exists():
        raise SystemExit(f'{out} already exists (same labels); artifacts are immutable.')
    out.mkdir(parents=True)
    (out / 'labels.csv').write_text(body, encoding='utf-8', newline='\n')
    (out / 'models.json').write_text(json.dumps(models, indent=1), encoding='utf-8')
    audit['status'] = 'PASS'
    (out / 'audit.json').write_text(json.dumps(audit, indent=1), encoding='utf-8')
    manifest = dict(
        artifact='b_pit_v1', created_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'),
        rule=bpit.__doc__.strip(), labels_sha256=labels_sha,
        inputs=dict(indicators=dict(path=pointer['file'], sha256=pointer['file_sha256']),
                    availability=dict(path=rel(inputs.AVAILABILITY),
                                      sha256=inputs.sha256(inputs.AVAILABILITY)),
                    bundle_v4_for_ari_only=dict(path=rel(inputs.BUNDLE),
                                                sha256=inputs.sha256(inputs.BUNDLE))),
        code={c: inputs.sha256(ROOT / c) for c in CODE}, git=git_commit(), rows=len(label_rows),
        audit_status='PASS')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    print(json.dumps(dict(artifact=rel(out), labels_sha256=labels_sha), indent=1))


if __name__ == '__main__':
    main()
