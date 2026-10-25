"""M3 stage 0 (docs/M3_PLAN.md §7): input manifest, Candidate Universe counts, return-basis evidence.

No portfolio return is computed: the feasibility counts read only data available at each decision date, and the
return-basis check only compares adj_close with raw_close of the same day.

Usage: python scripts/m3_stage0.py [--skip-c8-hash]
"""
import argparse
import json
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.m3 import inputs  # noqa: E402
from delta_t1.m3.ranking import n_select  # noqa: E402
from delta_t1.m3.universe import candidate_universe, leading_cluster  # noqa: E402

OUT = ROOT / 'data/experiments/m3'
DEV_END = '2023-12-29'
N_MIN = 10


def manifest(skip_c8):
    files = dict(bundle_v4=inputs.BUNDLE, indicators_v1=inputs.INDICATORS, availability=inputs.AVAILABILITY,
                 vnindex=inputs.BENCHMARK, trading_calendar=inputs.CALENDAR, prices_c8=inputs.PRICES_C8)
    out = {}
    for name, path in files.items():
        entry = dict(path=str(path.relative_to(ROOT)).replace('\\', '/'), bytes=path.stat().st_size)
        if not (skip_c8 and name == 'prices_c8'):
            entry['sha256'] = inputs.sha256(path)
        out[name] = entry
    blob = subprocess.run(['git', 'rev-parse', inputs.M2_LABELS_REF], cwd=ROOT, capture_output=True, text=True)
    out['m2_k2_labels'] = dict(git_ref=inputs.M2_LABELS_REF, git_blob=blob.stdout.strip() or None)
    return out


def feasibility():
    market = inputs.market_snapshots()
    fin = inputs.financial_labels()
    avail = inputs.availability()
    sector = inputs.sectors()
    leading_fin, fin_stats = {}, {}
    for year, labels in fin.items():
        leading_fin[year], fin_stats[year] = leading_cluster(list(labels.values()), 'roe', 'debt_to_equity',
                                                             higher_tiebreak=False)
    m2_text = subprocess.run(['git', 'show', inputs.M2_LABELS_REF], cwd=ROOT, capture_output=True,
                             text=True, encoding='utf-8').stdout
    m2 = inputs.m2_labels(m2_text) if m2_text else {}
    rows, reasons = [], Counter()
    for date in sorted(market):
        snap = market[date]
        record = dict(decision_date=date, segment='development' if date <= DEV_END else 'holdout')
        cands, audit, lead = candidate_universe(snap, date, fin, avail, sector, leading_fin)
        reasons.update(a['reason'] for a in audit)
        pool = [a for a in audit if a['market_eligible']]
        record.update(liquid=sum(r['liquidity'] != 'ILLIQUID' for r in snap), leading_market=lead,
                      market_pool=len(pool), fin_eligible_all=sum(a['financial_eligible'] for a in audit),
                      financial_sector_in_pool=sum(a['reason'] == 'FINANCIAL_SECTOR_NO_B' for a in pool),
                      candidates=len(cands), selected=n_select(len(cands)))
        c2, _, _ = candidate_universe(snap, date, fin, avail, sector, leading_fin, include_illiquid=True)
        record.update(candidates_incl_illiquid=len(c2))
        if date in m2:
            by_ticker = {r['ticker']: r for r in snap}
            members = [(c, by_ticker[t]['features']) for t, c in m2[date].items() if t in by_ticker]
            lead2, _ = leading_cluster(members, 'mom_126', 'mdd_126')
            m2_rows = [dict(by_ticker[t], cluster=c, liquidity='LIQUID') for t, c in m2[date].items() if t in by_ticker]
            c3, a3, _ = candidate_universe(m2_rows, date, fin, avail, sector, leading_fin, leading_market=lead2)
            record.update(m2_market_pool=sum(a['market_eligible'] for a in a3), m2_candidates=len(c3))
        rows.append(record)
    return rows, reasons, leading_fin, fin_stats


def return_basis():
    """Steps in adj_close/raw_close per ticker: small positive steps ≈ cash dividends, large ≈ stock events."""
    db = inputs._ro(inputs.BUNDLE)
    last, small, large, glitches, tickers_small = {}, defaultdict(float), 0, [], set()
    previous_step = {}
    for ticker, date, adj, raw in db.execute(
            'select ticker, date, adj_close, raw_close from prices where adj_close > 0 and raw_close > 0 '
            "and date >= '2019-01-01' order by ticker, date"):
        ratio = adj / raw
        if ticker in last:
            step = ratio / last[ticker][1] - 1
            if abs(step) > 0.003:
                prev = previous_step.get(ticker)
                if prev and prev[0] == last[ticker][0] and prev[1] * step < 0 and abs(prev[1]) > 0.03:
                    glitches.append((ticker, prev[0], round(prev[1], 4), date, round(step, 4)))
                if 0.003 < step <= 0.06:
                    small[(ticker, date[:4])] += step
                    tickers_small.add(ticker)
                elif step > 0.06:
                    large += 1
            previous_step[ticker] = (date, step)
        last[ticker] = (date, ratio)
    yearly = sorted(small.values())
    return dict(tickers=len(last), tickers_with_small_steps=len(tickers_small), large_steps=large,
                small_step_ticker_years=len(yearly),
                implied_cash_dividend_yield_median=round(statistics.median(yearly), 4) if yearly else None,
                implied_cash_dividend_yield_p90=round(yearly[int(0.9 * len(yearly))], 4) if yearly else None,
                reversal_glitches=len(glitches), glitch_examples=glitches[:15])


def summarize(rows):
    out = {}
    for segment in ('development', 'holdout'):
        seg = [r for r in rows if r['segment'] == segment]
        def stat(key):
            vals = [r[key] for r in seg if key in r]
            return dict(min=min(vals), median=statistics.median(vals), max=max(vals)) if vals else None
        out[segment] = dict(months=len(seg), market_pool=stat('market_pool'), candidates=stat('candidates'),
                            selected=stat('selected'), months_below_n_min=sum(r['candidates'] < N_MIN for r in seg),
                            financial_sector_in_pool=stat('financial_sector_in_pool'),
                            candidates_incl_illiquid=stat('candidates_incl_illiquid'),
                            m2_market_pool=stat('m2_market_pool'), m2_candidates=stat('m2_candidates'),
                            m2_months_below_n_min=sum(r.get('m2_candidates', N_MIN) < N_MIN for r in seg))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--skip-c8-hash', action='store_true', help='Skip hashing the 4 GB C8 price file.')
    args = parser.parse_args()
    run_dir = OUT / f"stage0-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir.mkdir(parents=True)
    (OUT / 'inputs').mkdir(exist_ok=True)
    pins = manifest(args.skip_c8_hash)
    (OUT / 'inputs/manifest.json').write_text(json.dumps(pins, indent=1), encoding='utf-8')
    rows, reasons, leading_fin, fin_stats = feasibility()
    keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[-1]).index(k) if k in rows[-1] else 99)
    with (run_dir / 'feasibility.csv').open('w', encoding='utf-8', newline='') as f:
        f.write(','.join(keys) + '\n')
        for r in rows:
            f.write(','.join('' if r.get(k) is None else str(r.get(k)) for k in keys) + '\n')
    summary = dict(summary=summarize(rows), exclusion_reasons=dict(reasons.most_common()),
                   leading_financial_cluster={y: dict(cluster=c, median_roe_de={k: [round(x, 4) if x is not None else None
                                                                                     for x in v]
                                                                                 for k, v in fin_stats[y].items()})
                                              for y, c in sorted(leading_fin.items())},
                   return_basis=return_basis(), inputs=pins)
    (run_dir / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str),
                                          encoding='utf-8')
    print(run_dir)
    print(json.dumps({k: summary[k] for k in ('summary', 'exclusion_reasons', 'leading_financial_cluster',
                                              'return_basis')}, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
