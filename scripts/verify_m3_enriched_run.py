"""R2-06: verify a full enriched M3 run, then optionally write an exclusive seal.json.

Usage: python scripts/verify_m3_enriched_run.py --run RUN --targets-run TARGETS
       --baseline-run BASELINE [--development-seal DEV/seal.json] [--seal]
No source/run artifact is rewritten. Full-run replay uses pinned sources, not cached price limits.
"""
import argparse
from bisect import bisect_right
import csv
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.m3 import inputs  # noqa: E402
from delta_t1.m3.benchmark import benchmark_nav  # noqa: E402
from delta_t1.m3.engine import run as replay  # noqa: E402
from delta_t1.m3.prices import PriceBook, load_limits  # noqa: E402
from delta_t1.m3.strategies import AUDIT_KEYS, Strategies  # noqa: E402
from scripts import run_m3 as runner  # noqa: E402

VERSION = 'm3-enriched-verifier-v1'
CONTROLS = ('market_only', 'equal_weight', 'momentum_only')
STRATEGIES = ('combined', 'market_only', 'financial_only', 'equal_weight', 'momentum_only')
CHECKS = ['pins', 'execution_head', 'segment_bounds', 'targets_and_audit', 'cash_conservation',
          'source_replay', 'ledger', 'holdings', 'nav', 'metrics', 'controls', 'immutable_bytes']
LEDGER_KEYS = ('date', 'ticker', 'side', 'pre_weight', 'target_weight', 'intended', 'executed', 'scale', 'status', 'flag')


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def read_json(path):
    def reject(value):
        raise VerificationError(f'Non-finite JSON number: {value}')
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject)


def equal(actual, expected, where):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), f'{where}: keys differ')
        for key in expected:
            equal(actual[key], expected[key], f'{where}.{key}')
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f'{where}: row count differs')
        for i, (left, right) in enumerate(zip(actual, expected)):
            equal(left, right, f'{where}[{i}]')
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        require(isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and math.isfinite(actual) and math.isfinite(expected)
                and math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-10), f'{where}: numeric mismatch')
    else:
        require(actual == expected and type(actual) is type(expected), f'{where}: value differs')


def read_csv(path):
    with Path(path).open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(set(reader.fieldnames)),
                f'{path}: missing or duplicate headers')
        require(all(None not in row and None not in row.values() for row in rows), f'{path}: malformed CSV')
        return reader.fieldnames, rows


def check_csv(path, expected, keys):
    fields, rows = read_csv(path)
    require(fields == list(keys) and len(rows) == len(expected), f'{path}: schema/row count mismatch')
    for index, (row, wanted) in enumerate(zip(rows, expected)):
        for key in keys:
            value = wanted.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                try:
                    number = float(row[key])
                except (ValueError, TypeError) as error:
                    raise VerificationError(f'{path}:{index}:{key}: invalid numeric value') from error
                equal(number, value, f'{path}:{index}:{key}')
            else:
                require(row[key] == ('' if value is None else str(value)), f'{path}:{index}:{key}: mismatch')
    return rows


def snapshot(directory):
    directory = Path(directory).resolve()
    out = {}
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), f'Symlink in immutable run: {path}')
        if path.is_file() and path != directory / 'seal.json':
            out[path.relative_to(directory).as_posix()] = inputs.sha256(path)
    require('manifest.json' in out, f'Missing manifest: {directory}')
    return out


def receipt(manifest):
    return {key: manifest[key] for key in ('git_commit', 'config_sha256', 'inputs_sha256')}


def check_development_seal(path, holdout_manifest):
    path = Path(path).resolve()
    seal = read_json(path)
    require(seal.get('version') == VERSION and seal.get('status') == 'PASS'
            and seal.get('segment') == 'development', 'Holdout requires a PASS Development seal')
    run_dir = Path(seal['run_dir']).resolve()
    require(run_dir != Path(holdout_manifest.get('_run_dir', '')).resolve(), 'Segments must use separate run directories')
    equal(snapshot(run_dir), seal['run_files_sha256'], 'Development sealed bytes')
    manifest = read_json(run_dir / 'manifest.json')
    equal(seal.get('checks'), CHECKS, 'Development completed checks')
    require(seal.get('run_id') == manifest.get('run_id'), 'Development run ID differs')
    require(manifest['segment'] == 'development' and manifest['targets_only'] is False
            and manifest['git_dirty'] is False and manifest['status'] == 'LOCKED', 'Invalid sealed Development manifest')
    equal(receipt(manifest), seal['execution'], 'Development execution receipt')
    equal(receipt(manifest), receipt(holdout_manifest), 'Dev/Holdout code/config/inputs')
    require(seal['manifest_sha256'] == inputs.sha256(run_dir / 'manifest.json'), 'Development manifest hash differs')
    for name, expected in seal['references'].items():
        equal(snapshot(expected['path']), expected['files_sha256'], f'Development {name} reference bytes')
    return inputs.sha256(path)


def check_cash(run_dir, name, executions):
    _, ledger = read_csv(run_dir / f'trade_ledger_{name}.csv')
    _, holdings = read_csv(run_dir / f'holdings_{name}.csv')
    _, nav = read_csv(run_dir / f'nav_{name}.csv')
    cash = 1.0
    require(len(nav) == len(executions) + 1, f'{name}: NAV bounds/count mismatch')
    for index, date in enumerate(executions):
        nav_before = float(nav[index]['nav'])
        rows = [r for r in ledger if r['date'] == date]
        for row in rows:
            executed, intended, scale = (float(row[k]) for k in ('executed', 'intended', 'scale'))
            require(all(math.isfinite(x) for x in (executed, intended, scale))
                    and 0 <= executed <= intended + 1e-9 and 0 <= scale <= 1 + 1e-9,
                    f'{name}: invalid cash/trade amount')
            if row['side'] == 'SELL':
                cash += executed
            elif row['side'] == 'BUY':
                cash -= executed
            else:
                require(row['side'] == 'HOLD' and executed == intended == 0, f'{name}: invalid HOLD cash')
            if row['status'] in ('BUY_FAILED', 'SELL_FAILED'):
                require(executed == 0, f'{name}: failed trade moved cash')
        require(cash >= -1e-9, f'{name}: negative cash')
        weights = [r for r in holdings if r['date'] == date]
        require(len({r['ticker'] for r in weights}) == len(weights), f'{name}: duplicate holdings')
        require(all(math.isfinite(float(r['weight'])) and float(r['weight']) >= -1e-10 for r in weights),
                f'{name}: invalid holdings weights')
        equal(sum(float(r['weight']) for r in weights), 1.0, f'{name}: holdings sum')
        cash_rows = [r for r in weights if r['ticker'] == 'CASH']
        require(len(cash_rows) == 1, f'{name}: missing/duplicate CASH')
        equal(float(cash_rows[0]['weight']) * nav_before, cash, f'{name}: cash conservation')


def compare_control_csv(left, right):
    fields, rows = read_csv(right)
    numeric = {'nav', 'pre_weight', 'target_weight', 'intended', 'executed', 'scale', 'weight', 'turnover',
               'target_weight', 'rank', 'candidates'}
    expected = [{key: float(value) if key in numeric and value != '' else value for key, value in row.items()}
                for row in rows]
    check_csv(left, expected, fields)


def verify_run(run_dir, *, targets_run, baseline_run, development_seal=None):
    run_dir, targets_run, baseline_run = (Path(p).resolve() for p in (run_dir, targets_run, baseline_run))
    require(len({run_dir, targets_run, baseline_run}) == 3, 'Full, targets-only and baseline runs must be distinct')
    original = snapshot(run_dir)
    targets_snapshot, baseline_snapshot = snapshot(targets_run), snapshot(baseline_run)
    manifest = read_json(run_dir / 'manifest.json')
    require(manifest.get('targets_only') is False and manifest.get('status') == 'LOCKED'
            and manifest.get('git_dirty') is False and manifest.get('financial_source') == 'B_PIT',
            'Requires a full LOCKED clean B-PIT run')
    require(run_dir.name == manifest.get('run_id'), 'Run directory does not match run_id')
    segment = manifest['segment']
    require(segment in ('development', 'holdout'), 'Only separate Development/Holdout runs are supported')
    require(re.fullmatch(r'[0-9a-f]{40}', manifest.get('git_commit', '')) is not None, 'Missing execution SHA')
    commit, dirty = runner.git_state()
    require(not dirty and commit == manifest['git_commit'], 'Verifier code/config must match clean execution HEAD')
    config_path = ROOT / manifest['config']
    cfg = read_json(config_path)
    require(cfg.get('status') == 'LOCKED' and 'financial_data' in cfg, 'Config must be LOCKED and enriched')
    require(set(cfg['strategies']) == set(STRATEGIES) and len(cfg['strategies']) == len(STRATEGIES),
            'Missing/duplicate official strategies or controls')
    require(inputs.sha256(config_path) == manifest['config_sha256'], 'Config hash mismatch')
    start, end = cfg['segments'][segment][0], cfg['segment_end_dates'][segment]
    require(manifest['segment_start'] == start and manifest['segment_end_date'] == end, 'Manifest date bounds mismatch')
    sources = inputs.financial_sources(cfg, root=ROOT)
    load_cfg = dict(cfg, financial_pit=dict(cfg['financial_pit'], artifact=str(ROOT / cfg['financial_pit']['artifact'])))
    fin, order, _, artifact, cutoffs = runner.load_financial(load_cfg, targets_only=False)
    actual_hashes = runner.input_hashes(artifact, False, **sources)
    require(all(isinstance(v, str) and re.fullmatch(r'[0-9a-f]{64}', v) for v in actual_hashes.values()),
            'Full-run input hashes must be complete; skipped C8 hash is not sealable')
    equal(manifest['inputs_sha256'], actual_hashes, 'Input pins')
    dev_hash = None
    if segment == 'holdout':
        require(development_seal is not None, 'Holdout requires a PASS Development seal')
        dev_hash = check_development_seal(development_seal, dict(manifest, _run_dir=str(run_dir)))
    require(not (targets_run / 'metrics.json').exists() and not list(targets_run.glob('nav_*.csv')),
            'Targets-only reference must not contain returns/NAV')
    targets_manifest = read_json(targets_run / 'manifest.json')
    require(targets_manifest.get('targets_only') is True and targets_manifest.get('git_dirty') is False
            and targets_manifest.get('financial_source') == 'B_PIT', 'Invalid targets-only reference')
    for key in ('segment', 'segment_start', 'segment_end_date', 'end_date', 'git_commit', 'config_sha256', 'counts'):
        equal(targets_manifest[key], manifest[key], f'Targets-only {key}')
    expected_targets_hashes = dict(actual_hashes, c8_prices_sha256=None)
    equal(targets_manifest['inputs_sha256'], expected_targets_hashes, 'Targets-only input pins')
    baseline_manifest = read_json(baseline_run / 'manifest.json')
    require(baseline_manifest.get('targets_only') is False and baseline_manifest.get('git_dirty') is False
            and baseline_manifest.get('status') == 'LOCKED', 'Invalid baseline reference')
    for key in ('segment', 'segment_start', 'segment_end_date', 'end_date'):
        equal(baseline_manifest[key], manifest[key], f'Baseline {key}')
    for key in ('terminal_sha256', 'c8_prices_sha256', 'c8_benchmark_sha256', 'c8_calendar_sha256'):
        equal(baseline_manifest['inputs_sha256'][key], actual_hashes[key], f'Baseline market source {key}')
    market = inputs.market_snapshots(bundle=inputs.BUNDLE)
    calendar = inputs.calendar(path=inputs.CALENDAR)
    bounded = [d for d in calendar if start <= d <= end]
    require(bool(bounded) and manifest['end_date'] == bounded[-1], 'NAV end_date/calendar bounds mismatch')
    end_date = bounded[-1]
    decisions = sorted(d for d in market if start <= d <= end)
    require(bool(decisions), 'No decisions in segment')
    strategies = Strategies(cfg, market, fin, inputs.availability(sources['availability_path']),
                            inputs.sectors(sources['indicators_path']), inputs.indicators(sources['indicators_path']),
                            fin_order=order, financial_cutoffs=cutoffs)
    schedules, counts = {}, {}
    for name in cfg['strategies']:
        targets, audits, schedule, statuses = [], [], [], []
        for date in decisions:
            result = strategies.target_for(name, date)
            index = bisect_right(calendar, date)
            execution = calendar[index] if index < len(calendar) else None
            status = result.get('status', 'OK')
            if execution is None or execution > end:
                status = 'NOT_EXECUTED_SEGMENT_END'
            else:
                schedule.append((date, execution, result['engine_target']))
            statuses.append(status)
            target = result.get('target') or {}
            targets.extend([dict(decision_date=date, execution_date=execution or '', ticker=ticker, rank=i + 1,
                                 target_weight=target[ticker], candidates=result['candidates'], status=status)
                            for i, ticker in enumerate(result['picks'])] or [dict(
                decision_date=date, execution_date=execution or '', ticker='', rank='', target_weight='',
                candidates=result['candidates'], status=status)])
            audits.extend(result['audit'])
        require(bool(schedule), f'{name}: no executable decisions')
        counts[name] = dict(decisions=len(decisions), executed=len(schedule),
                            too_small=statuses.count('UNIVERSE_TOO_SMALL'),
                            not_executed_segment_end=statuses.count('NOT_EXECUTED_SEGMENT_END'))
        for reference in (run_dir, targets_run):
            check_csv(reference / f'targets_{name}.csv', targets, runner.TARGET_KEYS)
            check_csv(reference / f'universe_audit_{name}.csv', audits, AUDIT_KEYS)
        schedules[name] = schedule
    equal(manifest['counts'], counts, 'Manifest counts')
    dates = sorted({date for schedule in schedules.values() for _, date, _ in schedule} | {end_date})
    limits = load_limits(dates, path=inputs.PRICES_C8, cache=None)
    book = PriceBook(dates, calendar, bundle=inputs.BUNDLE, limits=limits, segment_start=start, segment_end=end)
    closes = inputs.benchmark(path=inputs.BENCHMARK)
    require(all(date in closes for date in dates), 'Missing benchmark valuation date')
    bench = benchmark_nav(closes, dates)
    check_csv(run_dir / 'benchmark_vnindex.csv', [dict(date=d, nav=v) for d, v in bench], ('date', 'nav'))
    expected_metrics = dict(vnindex=runner.metrics(bench, [], [], [], False), adj_glitches_repaired=len(book.flags))
    for name, schedule in schedules.items():
        book.limit_missing = set()
        result = replay(schedule, book.price, book.tradable, end_date=end_date)
        equal(result['nav'][0][1], 1.0, f'{name}: segment must start at NAV 1')
        for row in result['ledger']:
            row['flag'] = 'LIMIT_DATA_MISSING' if row['status'] in ('BUY_FAILED', 'SELL_FAILED') \
                and (row['ticker'], row['date']) in book.limit_missing else ''
        check_csv(run_dir / f'nav_{name}.csv', [dict(date=d, nav=v) for d, v in result['nav']], ('date', 'nav'))
        check_csv(run_dir / f'trade_ledger_{name}.csv', result['ledger'], LEDGER_KEYS)
        check_csv(run_dir / f'holdings_{name}.csv', result['holdings'], ('date', 'ticker', 'weight'))
        check_csv(run_dir / f'turnover_{name}.csv', [dict(date=d, turnover=v) for d, v in result['turnover']],
                  ('date', 'turnover'))
        check_cash(run_dir, name, [d for _, d, _ in schedule])
        expected_metrics[name] = dict(runner.metrics(result['nav'], result['turnover'], result['ledger'],
                                                     result['holdings'], False),
                                      price_stale=len(result['stale']), limit_data_missing=len(book.limit_missing))
    actual_metrics = read_json(run_dir / 'metrics.json')
    equal(actual_metrics, expected_metrics, 'Metrics (no Sharpe in Development/Holdout)')
    baseline_metrics = read_json(baseline_run / 'metrics.json')
    compare_control_csv(run_dir / 'benchmark_vnindex.csv', baseline_run / 'benchmark_vnindex.csv')
    equal(actual_metrics['vnindex'], baseline_metrics['vnindex'], 'VNINDEX control metrics')
    for name in CONTROLS:
        for prefix in ('targets', 'universe_audit', 'nav', 'trade_ledger', 'holdings', 'turnover'):
            compare_control_csv(run_dir / f'{prefix}_{name}.csv', baseline_run / f'{prefix}_{name}.csv')
        equal(actual_metrics[name], baseline_metrics[name], f'{name} control metrics')
    equal(runner.input_hashes(artifact, False, **sources), actual_hashes, 'Inputs changed during verification')
    require(inputs.sha256(config_path) == manifest['config_sha256'], 'Config changed during verification')
    require(runner.git_state() == (manifest['git_commit'], False), 'Code/config changed during verification')
    equal(snapshot(run_dir), original, 'Run bytes changed during verification')
    equal(snapshot(targets_run), targets_snapshot, 'Targets-only bytes changed during verification')
    equal(snapshot(baseline_run), baseline_snapshot, 'Baseline bytes changed during verification')
    return dict(version=VERSION, status='PASS', segment=segment, run_id=manifest['run_id'], run_dir=str(run_dir),
                manifest_sha256=inputs.sha256(run_dir / 'manifest.json'), execution=receipt(manifest),
                run_files_sha256=original, development_seal_sha256=dev_hash,
                references=dict(targets=dict(path=str(targets_run), files_sha256=targets_snapshot),
                                baseline=dict(path=str(baseline_run), files_sha256=baseline_snapshot)),
                checks=CHECKS)


def verify_and_seal(run_dir, *, seal=False, **kwargs):
    result = verify_run(run_dir, **kwargs)
    if seal:
        # Exclusive creation: never overwrite a previous receipt or modify any run artifact.
        with (Path(run_dir) / 'seal.json').open('x', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--targets-run', required=True, type=Path)
    parser.add_argument('--baseline-run', required=True, type=Path)
    parser.add_argument('--development-seal', type=Path)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    try:
        result = verify_and_seal(args.run, targets_run=args.targets_run, baseline_run=args.baseline_run,
                                 development_seal=args.development_seal, seal=args.seal)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps(dict(status='FAIL', error=str(error)), ensure_ascii=False))
        return 1
    print(json.dumps(dict(status=result['status'], segment=result['segment'], run_id=result['run_id'],
                         sealed=args.seal), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
