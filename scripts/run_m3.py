"""Run M3 (docs/KE_HOACH_M3_SCHEMA_GITHUB.md, ADR D-M3-01): targets per decision date and, once LOCKED, the backtest.

  python scripts/run_m3.py --segment development --targets-only
  python scripts/run_m3.py --segment development          # refused unless status == LOCKED and B-PIT is pinned

Each decision date trades at the next session; positions are held until the next decision's execution date.
Strict segment isolation (plan §3.9): a decision whose execution session falls after segment_end_date is saved with
status NOT_EXECUTED_SEGMENT_END and never traded; the segment is valued on its last session <= segment_end_date and no
price after segment_end_date is read. Output: data/experiments/m3/<segment>/<run_id>/.
"""
import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.m3 import inputs  # noqa: E402
from delta_t1.m3.benchmark import benchmark_nav, period_returns  # noqa: E402
from delta_t1.m3.engine import run  # noqa: E402
from delta_t1.m3.prices import PriceBook, load_limits  # noqa: E402
from delta_t1.m3.strategies import AUDIT_KEYS, Strategies  # noqa: E402

CONFIG = 'configs/experiments/m3_strategy_v1.json'
TARGET_KEYS = ('decision_date', 'execution_date', 'ticker', 'rank', 'target_weight', 'candidates', 'status')


def write_csv(path, rows, keys=None):
    keys = list(keys or dict.fromkeys(k for r in rows for k in r))
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def metrics(nav, turnover, ledger, holdings, allow_sharpe):
    """Segment metrics; Sharpe only where the config allows it (Final Evaluation)."""
    rets = [r for _, r in period_returns(nav)]
    years = len(rets) / 12
    total = nav[-1][1] / nav[0][1] - 1
    peak, mdd = nav[0][1], 0.0
    for _, v in nav:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    mean = sum(rets) / len(rets) if rets else 0.0
    vol = (sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)) ** 0.5 * math.sqrt(12) if len(rets) > 1 else None
    cash = [h['weight'] for h in holdings if h['ticker'] == 'CASH']
    out = dict(periods=len(rets), total_return=total, cagr=(1 + total) ** (1 / years) - 1 if years else None,
               volatility_annual=vol, max_drawdown=mdd,
               avg_turnover=sum(t for _, t in turnover) / len(turnover) if turnover else None,
               avg_cash_after_trading=sum(cash) / len(cash) if cash else None,
               failed_buys=sum(r['status'] == 'BUY_FAILED' for r in ledger),
               failed_sells=sum(r['status'] == 'SELL_FAILED' for r in ledger),
               scaled_buys=sum(r['status'] == 'SCALED' for r in ledger))
    if allow_sharpe and vol:
        out['sharpe_rf0'] = mean * 12 / vol
    return out


def git_state():
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'src', 'scripts', 'configs'], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    return head or None, bool(dirty)


def input_hashes(bpit_dir, skip_c8_prices):
    files = dict(terminal_sha256=inputs.BUNDLE, indicators_sha256=inputs.INDICATORS,
                 availability_sha256=inputs.AVAILABILITY, c8_benchmark_sha256=inputs.BENCHMARK,
                 c8_calendar_sha256=inputs.CALENDAR)
    out = {k: inputs.sha256(p) for k, p in files.items()}
    out['c8_prices_sha256'] = None if skip_c8_prices else inputs.sha256(inputs.PRICES_C8)
    out['b_pit_labels_sha256'] = inputs.sha256(bpit_dir / 'labels.csv') if bpit_dir else None
    return out


def load_financial(cfg, targets_only):
    """B-PIT when the config pins it; B v4 reference only for targets-only readiness runs."""
    pin = cfg.get('financial_pit') or {}
    if pin.get('artifact'):
        bpit_dir = ROOT / pin['artifact']
        actual = inputs.sha256(bpit_dir / 'labels.csv')
        if pin.get('labels_sha256') and actual != pin['labels_sha256']:
            sys.exit(f'B-PIT labels.csv sha256 {actual} does not match the pinned {pin["labels_sha256"]}')
        labels, order, _ = inputs.bpit(bpit_dir)
        return labels, order, 'B_PIT', bpit_dir
    if not targets_only:
        sys.exit('Config does not pin a B-PIT artifact (financial_pit.artifact). Build it with '
                 'scripts/build_financial_pit_clusters.py; official runs never use B v4.')
    return inputs.financial_labels(), None, 'B_V4_REFERENCE_NOT_PIT', None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default=CONFIG)
    ap.add_argument('--segment', choices=['development', 'holdout', 'final'], required=True)
    ap.add_argument('--targets-only', action='store_true')
    ap.add_argument('--skip-c8-prices-hash', action='store_true', help='skip hashing the 4 GB C8 price file')
    args = ap.parse_args()
    cfg = json.loads((ROOT / args.config).read_text(encoding='utf-8'))
    if not args.targets_only and cfg.get('status') != 'LOCKED':
        sys.exit(f"Config status is {cfg.get('status')!r}: only --targets-only is allowed until the strategy is LOCKED "
                 '(docs/M3_READINESS.md). No return was computed.')
    if args.segment not in cfg['segments'] or args.segment not in cfg.get('segment_end_dates', {}):
        sys.exit(f'Segment {args.segment!r} has no start/end in the config (final is locked after readiness, Q16).')
    start, _ = cfg['segments'][args.segment]
    segment_end = cfg['segment_end_dates'][args.segment]
    fin_labels, fin_order, fin_source, bpit_dir = load_financial(cfg, args.targets_only)
    market = inputs.market_snapshots()
    strategies = Strategies(cfg, market, fin_labels, inputs.availability(), inputs.sectors(), inputs.indicators(),
                            fin_order=fin_order)
    calendar = inputs.calendar()
    nxt_session = lambda d: calendar[i] if (i := bisect_right(calendar, d)) < len(calendar) else None  # noqa: E731
    decisions = [d for d in sorted(market) if start <= d <= segment_end]
    in_segment = [d for d in calendar if start <= d <= segment_end]
    end_date = in_segment[-1] if in_segment else None
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + hashlib.sha256(
        json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8]
    out = ROOT / 'data/experiments/m3' / args.segment / run_id
    out.mkdir(parents=True)
    schedules, counts = {}, {}
    for name in cfg['strategies']:
        rows, sched, audit = [], [], []
        for d in decisions:
            res = strategies.target_for(name, d)
            execution = nxt_session(d)
            status = res.get('status', 'OK')
            if execution is None or execution > segment_end:
                status = 'NOT_EXECUTED_SEGMENT_END'
            else:
                sched.append((d, execution, res['engine_target']))
            target = res.get('target') or {}
            rows += [dict(decision_date=d, execution_date=execution or '', ticker=t, rank=i + 1,
                          target_weight=target[t], candidates=res['candidates'], status=status)
                     for i, t in enumerate(res['picks'])] \
                or [dict(decision_date=d, execution_date=execution or '', ticker='', rank='', target_weight='',
                         candidates=res['candidates'], status=status)]
            audit += res.get('audit', [])
        schedules[name] = sched
        statuses = {}
        for r in rows:
            statuses.setdefault(r['decision_date'], r['status'])
        counts[name] = dict(decisions=len(decisions), executed=len(sched),
                            too_small=sum(s == 'UNIVERSE_TOO_SMALL' for s in statuses.values()),
                            not_executed_segment_end=sum(s == 'NOT_EXECUTED_SEGMENT_END' for s in statuses.values()))
        write_csv(out / f'targets_{name}.csv', rows, TARGET_KEYS)
        write_csv(out / f'universe_audit_{name}.csv', audit, AUDIT_KEYS)
    commit, dirty = git_state()
    manifest = dict(config=args.config, config_sha256=hashlib.sha256((ROOT / args.config).read_bytes()).hexdigest(),
                    status=cfg.get('status'), segment=args.segment, segment_start=start, segment_end_date=segment_end,
                    end_date=end_date, run_id=run_id, targets_only=args.targets_only, financial_source=fin_source,
                    git_commit=commit, git_dirty=dirty,
                    inputs_sha256=input_hashes(bpit_dir, args.skip_c8_prices_hash or args.targets_only),
                    counts=counts)
    if not args.targets_only:
        exec_dates = sorted({e for s in schedules.values() for _, e, _ in s} | {end_date})
        assert exec_dates[-1] <= segment_end, 'a valuation date fell after segment_end_date'
        book = PriceBook(exec_dates, calendar, limits=load_limits(exec_dates, cache=ROOT / 'data/experiments/m3/inputs/limits.json'))
        allow = args.segment in cfg['sharpe_allowed_segments']
        bench = benchmark_nav(inputs.benchmark(), exec_dates)
        summary = dict(vnindex=metrics(bench, [], [], [], allow), adj_glitches_repaired=len(book.flags))
        write_csv(out / 'benchmark_vnindex.csv', [dict(date=d, nav=v) for d, v in bench])
        for name, sched in schedules.items():
            book.limit_missing = set()
            res = run(sched, book.price, book.tradable, end_date=end_date)
            for row in res['ledger']:
                row['flag'] = ('LIMIT_DATA_MISSING' if row['status'] in ('BUY_FAILED', 'SELL_FAILED')
                               and (row['ticker'], row['date']) in book.limit_missing else '')
            write_csv(out / f'nav_{name}.csv', [dict(date=d, nav=v) for d, v in res['nav']])
            write_csv(out / f'trade_ledger_{name}.csv', res['ledger'],
                      ('date', 'ticker', 'side', 'pre_weight', 'target_weight', 'intended', 'executed', 'scale',
                       'status', 'flag'))
            write_csv(out / f'holdings_{name}.csv', res['holdings'], ('date', 'ticker', 'weight'))
            write_csv(out / f'turnover_{name}.csv', [dict(date=d, turnover=t) for d, t in res['turnover']])
            summary[name] = dict(metrics(res['nav'], res['turnover'], res['ledger'], res['holdings'], allow),
                                 price_stale=len(res['stale']), limit_data_missing=len(book.limit_missing))
        (out / 'metrics.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    print(out)
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
