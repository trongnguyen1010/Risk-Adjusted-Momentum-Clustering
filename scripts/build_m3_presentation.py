"""Build the M3-B presentation bundle (m3-backtest-v1) from the sealed M3-A outputs in M3/outputs/.

Read-only on the research side: every CSV/JSON is checked against the seal of its run, and every seal against
M3/outputs/manifest.json, before anything is copied. No metric is recomputed; values come from metrics.json and the
CSVs as-is. The only derived series is drawdown = nav / running max(nav) - 1 (period basis, as in metrics.json).

Writes M3/presentation/m3-backtest-v1/backtest.json and configs/product/m3_backtest_v1.json (hash pointer).

Usage: python scripts/build_m3_presentation.py [--check]
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / 'M3/outputs'
VERSION = 'm3-backtest-v1'
BUNDLE = ROOT / 'M3/presentation' / VERSION / 'backtest.json'
POINTER = ROOT / 'configs/product/m3_backtest_v1.json'
SEGMENTS = ('development', 'holdout')
STRATEGIES = ('combined', 'market_only', 'financial_only', 'equal_weight', 'momentum_only')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def series(path, field):
    data = rows(path)
    return [r['date'] for r in data], [float(r[field]) for r in data]


def drawdown(values):
    peak, out = values[0], []
    for v in values:
        peak = max(peak, v)
        out.append(v / peak - 1)
    return out


def segment(name, seal_sha):
    runs = sorted((OUTPUTS / name).iterdir())
    if len(runs) != 1:
        raise SystemExit(f'expected one sealed run in {OUTPUTS / name}, found {len(runs)}')
    run = runs[0]
    if sha256(run / 'seal.json') != seal_sha:
        raise SystemExit(f'seal checksum mismatch: {run / "seal.json"}')
    seal = json.loads((run / 'seal.json').read_text(encoding='utf-8'))
    if seal['status'] != 'PASS':
        raise SystemExit(f'seal not PASS: {run}')
    for file, digest in seal['artifacts_sha256'].items():
        if (run / file).is_file() and sha256(run / file) != digest:
            raise SystemExit(f'artifact checksum mismatch: {run / file}')
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    metrics = json.loads((run / 'metrics.json').read_text(encoding='utf-8'))
    dates, bench = series(run / 'benchmark_vnindex.csv', 'nav')
    nav, turnover = {'vnindex': bench}, {}
    for s in STRATEGIES:
        d, nav[s] = series(run / f'nav_{s}.csv', 'nav')
        if d != dates:
            raise SystemExit(f'nav dates differ from benchmark: {s} in {run}')
        t_dates, turnover[s] = series(run / f'turnover_{s}.csv', 'turnover')
    holdings, cash = {}, {}
    for r in rows(run / 'holdings_combined.csv'):
        if r['ticker'] == 'CASH':  # Post-trade cash row, not a security.
            cash[r['date']] = float(r['weight'])
        else:
            holdings.setdefault(r['date'], []).append([r['ticker'], float(r['weight'])])
    # One period per decision; UNIVERSE_TOO_SMALL / NOT_EXECUTED_SEGMENT_END rows carry no ticker.
    targets = {}
    for r in rows(run / 'targets_combined.csv'):
        target = targets.setdefault(r['decision_date'], dict(date=r['execution_date'], candidates=int(r['candidates']),
                                                             status=r['status'], ranks={}))
        if r['ticker']:
            target['ranks'][r['ticker']] = int(r['rank'])
    periods = []
    for decision, target in sorted(targets.items()):
        items = sorted(holdings.get(target['date'], []), key=lambda x: (-x[1], x[0]))
        periods.append(dict(date=target['date'], decision_date=decision, candidates=target['candidates'],
                            status=target['status'], executed=target['date'] in t_dates, cash=cash.get(target['date']),
                            items=[dict(ticker=t, weight=w, rank=target['ranks'].get(t)) for t, w in items]))
    return dict(
        segment=name, run_id=manifest['run_id'], start=manifest['segment_start'], end=manifest['segment_end_date'],
        status=manifest['status'], financial_source=manifest['financial_source'], git_commit=manifest['git_commit'],
        config=manifest['config'], config_sha256=manifest['config_sha256'], counts=manifest['counts'],
        seal=dict(path=(run / 'seal.json').relative_to(ROOT).as_posix(), sha256=seal_sha, sealed_at=seal['sealed_at'],
                  status=seal['status']),
        inputs_sha256=manifest['inputs_sha256'],
        metrics={k: metrics[k] for k in ('vnindex', *STRATEGIES)},
        adj_glitches_repaired=metrics.get('adj_glitches_repaired'),
        nav=dict(dates=dates, series=nav),
        drawdown=dict(dates=dates, series={k: drawdown(v) for k, v in nav.items()}),
        turnover=dict(dates=t_dates, series=turnover),
        holdings=dict(strategy='combined', periods=periods),
        sources=[dict(path=(run / f).relative_to(ROOT).as_posix(), sha256=d) for f, d in sorted(seal['artifacts_sha256'].items())
                 if (run / f).is_file()],
    )


def build():
    manifest_path = OUTPUTS / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    segments = {name: segment(name, manifest['source_seals'][name]['seal_sha256']) for name in SEGMENTS}
    return dict(
        schema_version=1, version=VERSION, strategies=list(STRATEGIES), benchmark='vnindex',
        final_status=manifest['final_status'], source_commit=manifest['source_commit'],
        config_sha256=manifest['config_sha256'],
        outputs_manifest=dict(path=manifest_path.relative_to(ROOT).as_posix(), sha256=sha256(manifest_path)),
        segments=segments,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='rebuild in memory and fail if the committed bundle differs')
    args = ap.parse_args()
    text = json.dumps(build(), ensure_ascii=False, separators=(',', ':')) + '\n'
    if args.check:
        same = BUNDLE.is_file() and BUNDLE.read_text(encoding='utf-8') == text
        print('OK' if same else 'DIFFERS')
        sys.exit(0 if same else 1)
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    BUNDLE.write_bytes(text.encode('utf-8'))
    pointer = dict(version=VERSION, file=BUNDLE.relative_to(ROOT).as_posix(), file_sha256=sha256(BUNDLE),
                   source='M3/outputs (sealed M3-A runs); scripts/build_m3_presentation.py')
    POINTER.write_text(json.dumps(pointer, indent=2) + '\n', encoding='utf-8')
    print(f'{BUNDLE.relative_to(ROOT)}: {BUNDLE.stat().st_size} B, sha256 {pointer["file_sha256"]}')


if __name__ == '__main__':
    main()
