"""Run M3 (docs/M3_PLAN.md): targets per decision date and, once the config is LOCKED, the backtest.

  python scripts/run_m3.py --segment development --targets-only
  python scripts/run_m3.py --segment development          # refused while status != LOCKED

Each decision date trades at the next session; positions are held until the next decision's execution date. The
last decision of a segment is valued at the following decision's execution date when the data has it. Output:
data/experiments/m3/<segment>/<run_id>/.
"""
import argparse
import csv
import hashlib
import json
import math
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
from delta_t1.m3.strategies import Strategies  # noqa: E402

CONFIG = 'configs/experiments/m3_strategy_v1.json'


def write_csv(path, rows):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default=CONFIG)
    ap.add_argument('--segment', choices=['development', 'holdout', 'final'], required=True)
    ap.add_argument('--targets-only', action='store_true')
    args = ap.parse_args()
    cfg = json.loads((ROOT / args.config).read_text(encoding='utf-8'))
    if not args.targets_only and cfg.get('status') != 'LOCKED':
        sys.exit(f"Config status is {cfg.get('status')!r}: only --targets-only is allowed until the strategy is LOCKED "
                 '(docs/M3_MENTOR_QUESTIONS.md). No return was computed.')
    start, end = cfg['segments'][args.segment]
    market = inputs.market_snapshots()
    strategies = Strategies(cfg, market, inputs.financial_labels(), inputs.availability(), inputs.sectors(),
                            inputs.indicators())
    calendar = inputs.calendar()
    nxt_session = lambda d: calendar[i] if (i := bisect_right(calendar, d)) < len(calendar) else None  # noqa: E731
    all_decisions = sorted(market)
    decisions = [d for d in all_decisions if start <= d <= end]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + hashlib.sha256(
        json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8]
    out = ROOT / 'data/experiments/m3' / args.segment / run_id
    out.mkdir(parents=True)
    schedules, counts = {}, {}
    for name in cfg['strategies']:
        rows, sched = [], []
        for d in decisions:
            res = strategies.target_for(name, d)
            status = res.get('status', 'OK')
            rows += [dict(decision_date=d, ticker=t, rank=i + 1, target_weight=res['target'][t],
                          candidates=res['candidates'], status=status) for i, t in enumerate(res['picks'])] \
                or [dict(decision_date=d, ticker='', rank='', target_weight='', candidates=res['candidates'], status=status)]
            if nxt_session(d):
                sched.append((d, nxt_session(d), res['engine_target']))
        schedules[name] = sched
        counts[name] = dict(decisions=len(decisions), too_small=sum(r['status'] == 'UNIVERSE_TOO_SMALL' for r in rows
                                                                    if r['ticker'] == ''))
        write_csv(out / f'targets_{name}.csv', rows)
    manifest = dict(config=args.config, config_sha256=hashlib.sha256((ROOT / args.config).read_bytes()).hexdigest(),
                    status=cfg.get('status'), segment=args.segment, run_id=run_id, targets_only=args.targets_only,
                    counts=counts)
    if not args.targets_only:
        following = next((d for d in all_decisions if d > decisions[-1]), None)
        end_date = nxt_session(following) if following else calendar[-1]
        exec_dates = sorted({e for s in schedules.values() for _, e, _ in s} | {end_date})
        book = PriceBook(exec_dates, calendar, limits=load_limits(exec_dates, cache=ROOT / 'data/experiments/m3/inputs/limits.json'))
        allow = args.segment in cfg['sharpe_allowed_segments']
        bench = benchmark_nav(inputs.benchmark(), exec_dates)
        summary = dict(vnindex=metrics(bench, [], [], [], allow), adj_glitches_repaired=len(book.flags))
        write_csv(out / 'benchmark_vnindex.csv', [dict(date=d, nav=v) for d, v in bench])
        for name, sched in schedules.items():
            res = run(sched, book.price, book.tradable, end_date=end_date)
            write_csv(out / f'nav_{name}.csv', [dict(date=d, nav=v) for d, v in res['nav']])
            write_csv(out / f'trade_ledger_{name}.csv', res['ledger'])
            write_csv(out / f'holdings_{name}.csv', res['holdings'])
            write_csv(out / f'turnover_{name}.csv', [dict(date=d, turnover=t) for d, t in res['turnover']])
            summary[name] = dict(metrics(res['nav'], res['turnover'], res['ledger'], res['holdings'], allow),
                                 price_stale=len(res['stale']))
        (out / 'metrics.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    print(out)
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
