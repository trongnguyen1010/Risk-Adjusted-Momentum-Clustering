"""R2-10: export sealed baseline/enriched M3 comparisons, separately for each segment.

Reads artifacts only; never fits a model, reruns backtests or combines segment NAVs.
Usage: python scripts/export_backtest_comparison_metrics.py [--output NEW_DIRECTORY]
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.m3 import inputs  # noqa: E402
from scripts import build_m3_presentation as presentation  # noqa: E402
from scripts import verify_m3_enriched_run as verifier  # noqa: E402
from scripts.run_m3 import write_csv  # noqa: E402

STRATEGIES = presentation.STRATEGIES
SEGMENTS = presentation.SEGMENTS
CONTROLS = verifier.CONTROLS
MARKET_PINS = ('terminal_sha256', 'c8_benchmark_sha256', 'c8_calendar_sha256', 'c8_prices_sha256')
PRICE_BASIS = 'vendor-adjusted adj_close; includes cash dividends; costs=0, slippage=0'
BENCHMARK_BASIS = 'VNINDEX price index; excludes dividends'
DEFAULTS = dict(
    baseline_development='M3/outputs/development/20261104T121107Z-5557288c',
    baseline_holdout='M3/outputs/holdout/20261104T133507Z-5557288c',
    enriched_development='data/experiments/m3/development/20261118T165114Z-46fc18c0',
    enriched_holdout='data/experiments/m3/holdout/20261118T170517Z-46fc18c0')


def relative(path):
    path = Path(path).resolve()
    try:
        return path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def numeric(value, where):
    try:
        result = float(value)
    except (ValueError, TypeError) as error:
        raise verifier.VerificationError(f'{where}: invalid number') from error
    verifier.require(math.isfinite(result), f'{where}: non-finite number')
    return result


def stats(values, prefix):
    return {prefix + '_min': min(values) if values else None,
            prefix + '_median': statistics.median(values) if values else None,
            prefix + '_max': max(values) if values else None}


def load_run(path, segment, role, *, expected_seal_sha=None):
    path = Path(path).resolve()
    seal_path = path / 'seal.json'
    seal_hash = inputs.sha256(seal_path)
    if expected_seal_sha is not None:
        verifier.equal(seal_hash, expected_seal_sha, f'{role}/{segment}: published seal hash')
    seal = verifier.read_json(seal_path)
    verifier.require(seal.get('status') == 'PASS', f'{role}/{segment}: seal must be PASS')
    if role == 'enriched':
        verifier.require(seal.get('version') == verifier.VERSION and seal.get('segment') == segment,
                         f'{role}/{segment}: unsupported seal')
        verifier.equal(seal.get('checks'), verifier.CHECKS, f'{role}/{segment}: seal checks')
        pins = seal.get('run_files_sha256', {})
    else:
        verifier.require(seal.get('schema_version') == 1, f'{role}/{segment}: unsupported legacy seal')
        pins = seal.get('artifacts_sha256', {})
    expected_files = {'manifest.json', 'metrics.json', 'benchmark_vnindex.csv'} | {
        f'{prefix}_{strategy}.csv' for strategy in STRATEGIES
        for prefix in ('targets', 'universe_audit', 'nav', 'trade_ledger', 'holdings', 'turnover')}
    verifier.require(expected_files <= pins.keys(), f'{role}/{segment}: incomplete sealed file inventory')
    for filename, digest in pins.items():
        file = (path / filename).resolve()
        verifier.require(file.is_relative_to(path) and re.fullmatch(r'[0-9a-f]{64}', digest) is not None,
                         f'{role}/{segment}: invalid artifact pin')
        verifier.equal(inputs.sha256(file), digest, f'{role}/{segment}: {filename} checksum')
    manifest = verifier.read_json(path / 'manifest.json')
    verifier.require(manifest.get('targets_only') is False and manifest.get('status') == 'LOCKED'
                     and manifest.get('git_dirty') is False and manifest.get('segment') == segment,
                     f'{role}/{segment}: not a sealed full clean LOCKED run')
    verifier.require(manifest.get('financial_source') == 'B_PIT', f'{role}/{segment}: B-PIT required')
    if role == 'enriched':
        verifier.equal(verifier.receipt(manifest), seal['execution'], f'{role}/{segment}: execution pins')
        verifier.equal(inputs.sha256(path / 'manifest.json'), seal['manifest_sha256'], f'{role}/{segment}: manifest pin')
        verifier.require(seal['run_id'] == manifest['run_id'], f'{role}/{segment}: run ID mismatch')
    else:
        verifier.equal(verifier.receipt(manifest), {k: seal[k] for k in verifier.receipt(manifest)},
                       f'{role}/{segment}: execution pins')
    for digest in manifest['inputs_sha256'].values():
        verifier.require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest) is not None,
                         f'{role}/{segment}: missing full-run input hash')
    metrics = verifier.read_json(path / 'metrics.json')
    verifier.require(all('sharpe' not in k.lower() for name in ('vnindex', *STRATEGIES) for k in metrics[name]),
                     f'{role}/{segment}: unexpected Sharpe')
    return dict(path=path, manifest=manifest, seal=seal, metrics=metrics,
                snapshot=verifier.snapshot(path), seal_sha256=seal_hash)


def run_tables(run, segment, role):
    path, manifest, metrics = run['path'], run['manifest'], run['metrics']
    source_id = f'{segment}:{role}'
    start, end = manifest['segment_start'], manifest['end_date']
    verifier.require(end <= manifest['segment_end_date'], f'{source_id}: invalid end date')
    summary, periods, series = [], [], []
    for strategy in (*STRATEGIES, 'vnindex'):
        file = path / ('benchmark_vnindex.csv' if strategy == 'vnindex' else f'nav_{strategy}.csv')
        dates, nav = presentation.series(file, 'nav')
        verifier.require(bool(nav) and dates == sorted(dates) and all(start <= d <= end for d in dates)
                         and dates[-1] == end and all(math.isfinite(v) and v > 0 for v in nav),
                         f'{source_id}/{strategy}: NAV date/value bounds')
        verifier.equal(nav[0], 1, f'{source_id}/{strategy}: independent initial NAV')
        dd = presentation.drawdown(nav)
        metric = metrics[strategy]
        verifier.equal(metric['total_return'], nav[-1] / nav[0] - 1, f'{source_id}/{strategy}: return series')
        verifier.equal(metric['max_drawdown'], min(dd), f'{source_id}/{strategy}: drawdown series')
        basis = BENCHMARK_BASIS if strategy == 'vnindex' else PRICE_BASIS
        series.extend(dict(source_id=source_id, segment=segment, source=role, strategy=strategy,
                           row_index=i, date=date, nav=value, drawdown=drawdown, price_basis=basis)
                      for i, (date, value, drawdown) in enumerate(zip(dates, nav, dd)))
        row = dict(source_id=source_id, segment=segment, source=role, strategy=strategy, run_id=manifest['run_id'],
                   start=start, end=end, nav_start=nav[0], nav_end=nav[-1], total_return=metric['total_return'],
                   cagr=metric['cagr'], max_drawdown=metric['max_drawdown'],
                   volatility_annual=metric['volatility_annual'], avg_cash_after_trading=metric['avg_cash_after_trading'],
                   avg_turnover=metric['avg_turnover'], failed_buys=metric['failed_buys'], failed_sells=metric['failed_sells'],
                   scaled_buys=metric['scaled_buys'], price_stale=metric.get('price_stale'),
                   limit_data_missing=metric.get('limit_data_missing'), price_basis=basis)
        if strategy == 'vnindex':
            row.update(dict.fromkeys(['decisions', 'executed', 'not_executed_segment_end', 'n_below_10',
                                      'selected_median', 'held_median', 'candidates_min', 'candidates_median', 'candidates_max']))
            summary.append(row)
            continue
        grouped, holdings, ledger = defaultdict(list), defaultdict(list), defaultdict(list)
        audits = defaultdict(list)
        for record in presentation.rows(path / f'targets_{strategy}.csv'):
            grouped[record['decision_date']].append(record)
        for record in presentation.rows(path / f'universe_audit_{strategy}.csv'):
            audits[record['decision_date']].append(record)
        for record in presentation.rows(path / f'holdings_{strategy}.csv'):
            holdings[record['date']].append(record)
        for record in presentation.rows(path / f'trade_ledger_{strategy}.csv'):
            ledger[record['date']].append(record)
        count = manifest['counts'][strategy]
        verifier.require(len(grouped) == count['decisions'], f'{source_id}/{strategy}: decision count')
        candidate_counts, selected_counts, held_counts, cash_weights = [], [], [], []
        executed_count, final_count, too_small_count = 0, 0, 0
        for date, targets in sorted(grouped.items()):
            first = targets[0]
            verifier.require(start <= date <= end, f'{source_id}/{strategy}: decision outside segment')
            verifier.require(all((r['execution_date'], r['status'], r['candidates']) ==
                                 (first['execution_date'], first['status'], first['candidates']) for r in targets),
                             f'{source_id}/{strategy}: inconsistent target period')
            n = int(first['candidates'])
            verifier.require(n >= 0 and sum(a['in_candidate_universe'] == 'True' for a in audits[date]) == n,
                             f'{source_id}/{strategy}: candidate audit mismatch')
            selected = [r for r in targets if r['ticker']]
            verifier.require(len({r['ticker'] for r in selected}) == len(selected), f'{source_id}: duplicate picks')
            if selected:
                verifier.equal(sum(numeric(r['target_weight'], 'target weight') for r in selected), 1,
                               f'{source_id}/{strategy}: target weights')
            executed = first['status'] != 'NOT_EXECUTED_SEGMENT_END'
            execution_date = first['execution_date']
            held, cash = None, None
            failed_buys = failed_sells = scaled_buys = None
            if executed:
                verifier.require(date < execution_date <= end and execution_date in holdings,
                                 f'{source_id}/{strategy}: missing/invalid execution holdings')
                weights = holdings[execution_date]
                verifier.require(len({r['ticker'] for r in weights}) == len(weights), f'{source_id}: duplicate holdings')
                verifier.require(all(numeric(r['weight'], 'holding') >= -1e-10 for r in weights), f'{source_id}: negative weight')
                verifier.equal(sum(numeric(r['weight'], 'holding') for r in weights), 1, f'{source_id}: holdings sum')
                cash_rows = [r for r in weights if r['ticker'] == 'CASH']
                verifier.require(len(cash_rows) == 1, f'{source_id}: missing CASH')
                cash = numeric(cash_rows[0]['weight'], 'cash')
                held = sum(r['ticker'] != 'CASH' and numeric(r['weight'], 'holding') > 1e-12 for r in weights)
                held_counts.append(held); cash_weights.append(cash)
                trades = ledger[execution_date]
                failed_buys = sum(r['status'] == 'BUY_FAILED' for r in trades)
                failed_sells = sum(r['status'] == 'SELL_FAILED' for r in trades)
                scaled_buys = sum(r['status'] == 'SCALED' for r in trades)
                executed_count += 1
            else:
                verifier.require(not execution_date or execution_date > end, f'{source_id}: invalid final decision')
                final_count += 1
            too_small_count += first['status'] == 'UNIVERSE_TOO_SMALL'
            candidate_counts.append(n); selected_counts.append(len(selected))
            periods.append(dict(source_id=source_id, segment=segment, source=role, strategy=strategy,
                                decision_date=date, execution_date=execution_date, status=first['status'],
                                executed=executed, candidates=n, selected_count=len(selected), held_count=held,
                                cash_after_trading=cash, failed_buys=failed_buys, failed_sells=failed_sells,
                                scaled_buys=scaled_buys))
        verifier.equal(count, dict(decisions=len(grouped), executed=executed_count, too_small=too_small_count,
                                   not_executed_segment_end=final_count), f'{source_id}/{strategy}: manifest counts')
        verifier.equal(metric['failed_buys'], sum(r['status'] == 'BUY_FAILED' for v in ledger.values() for r in v),
                       f'{source_id}/{strategy}: failed buys')
        verifier.equal(metric['failed_sells'], sum(r['status'] == 'SELL_FAILED' for v in ledger.values() for r in v),
                       f'{source_id}/{strategy}: failed sells')
        verifier.equal(metric['avg_cash_after_trading'], statistics.mean(cash_weights), f'{source_id}: cash series')
        row.update(decisions=count['decisions'], executed=count['executed'],
                   not_executed_segment_end=count['not_executed_segment_end'], n_below_10=sum(n < 10 for n in candidate_counts),
                   selected_median=statistics.median(selected_counts), held_median=statistics.median(held_counts),
                   **stats(candidate_counts, 'candidates'))
        summary.append(row)
    return summary, periods, series


def build_comparison(paths, *, baseline_seal_pins):
    runs = {}
    for segment in SEGMENTS:
        for role in ('baseline', 'enriched'):
            runs[segment, role] = load_run(paths[segment, role], segment, role,
                                           expected_seal_sha=baseline_seal_pins[segment] if role == 'baseline' else None)
    for role in ('baseline', 'enriched'):
        dev, hold = (runs[s, role] for s in SEGMENTS)
        verifier.equal(verifier.receipt(dev['manifest']), verifier.receipt(hold['manifest']), f'{role}: segment execution pins')
        verifier.require(dev['manifest']['end_date'] < hold['manifest']['segment_start'], f'{role}: overlapping segments')
    verifier.equal(runs['holdout', 'enriched']['seal']['development_seal_sha256'],
                   runs['development', 'enriched']['seal_sha256'], 'Holdout Dev seal dependency')
    for segment in SEGMENTS:
        base, enriched = (runs[segment, role] for role in ('baseline', 'enriched'))
        for key in ('segment_start', 'segment_end_date', 'end_date'):
            verifier.equal(base['manifest'][key], enriched['manifest'][key], f'{segment}: {key}')
        for key in MARKET_PINS:
            verifier.equal(base['manifest']['inputs_sha256'][key], enriched['manifest']['inputs_sha256'][key],
                           f'{segment}: market input pin {key}')
        verifier.compare_control_csv(enriched['path'] / 'benchmark_vnindex.csv', base['path'] / 'benchmark_vnindex.csv')
        verifier.equal(enriched['metrics']['vnindex'], base['metrics']['vnindex'], f'{segment}: VNINDEX metrics')
        for strategy in CONTROLS:
            for prefix in ('targets', 'universe_audit', 'nav', 'trade_ledger', 'holdings', 'turnover'):
                verifier.compare_control_csv(enriched['path'] / f'{prefix}_{strategy}.csv',
                                             base['path'] / f'{prefix}_{strategy}.csv')
            verifier.equal(enriched['metrics'][strategy], base['metrics'][strategy], f'{segment}/{strategy}: control metrics')
    summary, periods, series, sources = [], [], [], {}
    for (segment, role), run in runs.items():
        part = run_tables(run, segment, role)
        summary.extend(part[0]); periods.extend(part[1]); series.extend(part[2])
        manifest = run['manifest']
        sources[f'{segment}:{role}'] = dict(path=relative(run['path']), run_id=manifest['run_id'],
            seal_sha256=run['seal_sha256'], manifest_sha256=inputs.sha256(run['path'] / 'manifest.json'),
            execution=verifier.receipt(manifest), files_sha256=run['snapshot'])
    indexed = {(r['segment'], r['source'], r['strategy']): r for r in summary}
    differences = []
    fields = dict(total_return='total_return_pp', max_drawdown='max_drawdown_pp', avg_cash_after_trading='avg_cash_pp',
                  nav_end='nav_end', candidates_median='candidates_median', n_below_10='n_below_10',
                  failed_buys='failed_buys', failed_sells='failed_sells', selected_median='selected_median', held_median='held_median')
    for segment in SEGMENTS:
        for strategy in (*STRATEGIES, 'vnindex'):
            before, after = (indexed[segment, role, strategy] for role in ('baseline', 'enriched'))
            row = dict(segment=segment, strategy=strategy, baseline_source_id=f'{segment}:baseline',
                       enriched_source_id=f'{segment}:enriched', price_basis=after['price_basis'])
            for key, label in fields.items():
                value = None if before[key] is None or after[key] is None else after[key] - before[key]
                row['delta_' + label] = value * 100 if value is not None and label.endswith('_pp') else value
            differences.append(row)
    for run in runs.values():
        verifier.equal(verifier.snapshot(run['path']), run['snapshot'], 'Source artifacts changed during export')
        verifier.equal(inputs.sha256(run['path'] / 'seal.json'), run['seal_sha256'], 'Source seal changed during export')
    return dict(summary=summary, periods=periods, nav_series=series, comparison=differences, sources=sources)


def export_comparison(paths, *, baseline_seal_pins, output):
    output = Path(output).resolve()
    verifier.require(not output.exists(), 'Output already exists; choose a new immutable export directory')
    verifier.require(all(not output.is_relative_to(Path(p).resolve()) for p in paths.values()), 'Output must be outside source runs')
    result = build_comparison(paths, baseline_seal_pins=baseline_seal_pins)
    output.mkdir(parents=True)
    files = {}
    for name in ('summary', 'periods', 'nav_series', 'comparison'):
        file = output / (name + '.csv')
        write_csv(file, result[name])
        files[file.name] = inputs.sha256(file)
    payload = dict(version='m3-baseline-enriched-comparison-v1', status='PASS',
                   created_utc=datetime.now(timezone.utc).isoformat(),
                   source_runs=result['sources'], outputs_sha256=files,
                   content_sha256=hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest(),
                   notes=['Segments have independent initial NAV=1; never concatenate or compound segments.',
                          'NAV/return/drawdown are reporting outputs, never model selection inputs.',
                          'N and selected include all decisions; held/cash cover executed dates only.',
                          'Final unexecuted decisions have no held/cash/trade outcome.',
                          'All differences, including adverse values, are retained.', PRICE_BASIS, BENCHMARK_BASIS])
    (output / 'manifest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in DEFAULTS.items():
        parser.add_argument('--' + name.replace('_', '-'), type=Path, default=Path(default))
    parser.add_argument('--baseline-manifest', type=Path, default=Path('M3/outputs/manifest.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    anchor = verifier.read_json(ROOT / args.baseline_manifest)
    pins = {s: anchor['source_seals'][s]['seal_sha256'] for s in SEGMENTS}
    paths = {(s, role): ROOT / getattr(args, f'{role}_{s}') for s in SEGMENTS for role in ('baseline', 'enriched')}
    output = ROOT / args.output if args.output else ROOT / 'data/experiments/m3/comparison' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    result = export_comparison(paths, baseline_seal_pins=pins, output=output)
    print(output)
    print(json.dumps(dict(status=result['status'], source_runs=len(result['source_runs']), files=len(result['outputs_sha256']) + 1)))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(json.dumps(dict(status='FAIL', error=str(error)), ensure_ascii=False))
        sys.exit(1)
