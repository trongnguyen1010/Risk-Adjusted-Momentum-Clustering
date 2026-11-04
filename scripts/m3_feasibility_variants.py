"""Candidate Universe size per month for the Q5/Q6 options in docs/M3_PLAN.md (counts only, no returns).

Variants combine the market rule (best cluster by median mom_126, or best two) with the financial rule (best cluster
by median ROE, or every cluster except the weakest). Output: data/experiments/m3/feasibility-variants/<run>/.

With B-PIT pinned in the M3 config (financial_pit.artifact) the financial labels and the cluster order frozen at the
B-PIT cutoff are used; otherwise B v4 is used and the run is marked B_V4_REFERENCE_NOT_PIT. The official config
(Va + N_min) is also counted through Strategies.combined, i.e. after FINANCIAL_CRITERIA_MISSING is dropped — the same
N that the backtest uses for N_min and top-30 % (plan §3.5.3, §3.7).

Usage: python scripts/m3_feasibility_variants.py [--b-v4]
"""
import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.m3 import inputs  # noqa: E402
from delta_t1.m3.ranking import n_select  # noqa: E402
from delta_t1.m3.strategies import Strategies  # noqa: E402
from delta_t1.m3.universe import allowed_clusters, candidate_universe, cluster_order  # noqa: E402

CONFIG = ROOT / 'configs/experiments/m3_strategy_v1.json'

DEV_END = '2023-12-29'
VARIANTS = {
    'V0 · cụm mạnh nhất ∩ cụm mạnh nhất (đề xuất gốc)': ('leading', 'leading'),
    'Va · cụm mạnh nhất ∩ tài chính không thuộc cụm yếu nhất': ('leading', 'not_weakest'),
    'Vb · 2 cụm mạnh nhất ∩ cụm mạnh nhất': ('top2', 'leading'),
    'Vab · 2 cụm mạnh nhất ∩ tài chính không thuộc cụm yếu nhất': ('top2', 'not_weakest'),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--b-v4', action='store_true', help='force the B v4 reference even if B-PIT is pinned')
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    stale = cfg.get('stale_months', 18)
    market = inputs.market_snapshots()
    sector = inputs.sectors()
    pin = (cfg.get('financial_pit') or {}).get('artifact')
    if pin and not args.b_v4:
        fin, fin_order, _, fin_cutoffs = inputs.bpit(pin, include_cutoffs=True)
        source = 'B_PIT:' + pin
    else:
        fin = inputs.financial_labels()
        fin_order = {y: cluster_order(list(v.values()), 'roe', 'debt_to_equity', higher_tiebreak=False)
                     for y, v in fin.items()}
        source = 'B_V4_REFERENCE_NOT_PIT'
        fin_cutoffs = None
    avail = inputs.availability(historical_reference=source == 'B_V4_REFERENCE_NOT_PIT')
    print('financial source:', source)
    out = {}
    for name, (market_rule, fin_rule) in VARIANTS.items():
        allowed_fin = {y: allowed_clusters(o, fin_rule) for y, o in fin_order.items()}
        rows = []
        for date in sorted(market):
            cands, audit, _ = candidate_universe(market[date], date, fin, avail, sector, allowed_fin,
                                                 market_rule=market_rule, stale_months=stale,
                                                 financial_cutoffs=fin_cutoffs)
            rows.append(dict(date=date, segment='development' if date <= DEV_END else 'holdout',
                             market_pool=sum(a['market_eligible'] for a in audit), candidates=len(cands)))
        summary = {}
        for seg in ('development', 'holdout'):
            part = [r for r in rows if r['segment'] == seg]
            c = [r['candidates'] for r in part]
            summary[seg] = dict(months=len(part), min=min(c), median=statistics.median(c), max=max(c),
                                below_10=sum(x < 10 for x in c), below_5=sum(x < 5 for x in c),
                                selected_median=statistics.median(n_select(x) for x in c),
                                market_pool_median=statistics.median(r['market_pool'] for r in part))
        out[name] = dict(market_rule=market_rule, financial_rule=fin_rule, summary=summary, monthly=rows)
        print(name, json.dumps(summary, ensure_ascii=False))
    strategies = Strategies(cfg, market, fin, avail, sector, inputs.indicators(), fin_order=fin_order,
                            financial_cutoffs=fin_cutoffs)
    official = []
    for date in sorted(market):
        res = strategies.combined(date)
        official.append(dict(date=date, segment='development' if date <= DEV_END else 'holdout',
                             candidates=res['candidates'], status=res['status']))
    official_summary = {}
    for seg in ('development', 'holdout'):
        part = [r for r in official if r['segment'] == seg]
        c = [r['candidates'] for r in part]
        official_summary[seg] = dict(months=len(part), min=min(c), median=statistics.median(c), max=max(c),
                                     universe_too_small=sum(r['status'] == 'UNIVERSE_TOO_SMALL' for r in part),
                                     selected_median=statistics.median(n_select(x) for x in c))
    print('official config (after FINANCIAL_CRITERIA_MISSING):', json.dumps(official_summary, ensure_ascii=False))
    run = OUT = ROOT / 'data/experiments/m3/feasibility-variants' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run.mkdir(parents=True)
    (OUT / 'variants.json').write_text(json.dumps(dict(financial_source=source,
                                                       financial_order={y: o for y, o in fin_order.items()},
                                                       official_config=dict(summary=official_summary,
                                                                            monthly=official),
                                                       variants=out), ensure_ascii=False, indent=1), encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    main()
