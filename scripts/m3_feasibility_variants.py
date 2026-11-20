"""Count M3 feasibility (no returns) using the same financial sources and cutoff gates as run_m3.

Usage: python scripts/m3_feasibility_variants.py [--config PATH] [--b-v4]
The four variants count the raw candidate universe; official_config counts after scoring drops
FINANCIAL_CRITERIA_MISSING. --b-v4 is a legacy baseline reference only, forbidden with enriched inputs.
"""
import argparse
from collections import Counter
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.m3 import inputs  # noqa: E402
from delta_t1.m3.ranking import n_select  # noqa: E402
from delta_t1.m3.strategies import Strategies, financial_order_from_labels  # noqa: E402
from delta_t1.m3.universe import allowed_clusters, candidate_universe  # noqa: E402
from scripts import run_m3 as m3_runner  # noqa: E402

CONFIG = ROOT / 'configs/experiments/m3_strategy_v1.json'
VARIANTS = {
    'V0 · cụm mạnh nhất ∩ cụm mạnh nhất (đề xuất gốc)': ('leading', 'leading'),
    'Va · cụm mạnh nhất ∩ tài chính không thuộc cụm yếu nhất': ('leading', 'not_weakest'),
    'Vb · 2 cụm mạnh nhất ∩ cụm mạnh nhất': ('top2', 'leading'),
    'Vab · 2 cụm mạnh nhất ∩ tài chính không thuộc cụm yếu nhất': ('top2', 'not_weakest'),
}


def decision_segments(cfg, market):
    """Use the runner's inclusive start/segment_end_dates; skip dates outside every configured segment."""
    bounds = {}
    for segment, dates in cfg['segments'].items():
        if segment not in cfg.get('segment_end_dates', {}):
            raise ValueError(f'Segment {segment!r} has no segment_end_date')
        start, end = dates[0], cfg['segment_end_dates'][segment]
        if start > end:
            raise ValueError(f'Invalid segment bounds: {segment}')
        bounds[segment] = start, end
    out = []
    for date in sorted(market):
        matches = [s for s, (start, end) in bounds.items() if start <= date <= end]
        if len(matches) > 1:
            raise ValueError(f'Overlapping segments for decision {date}')
        if matches:
            out.append((date, matches[0]))
    return out


def summary(rows, segments, *, official=False, share=0.3):
    out = {}
    for segment in segments:
        part = [r for r in rows if r['segment'] == segment]
        counts = [r['candidates'] for r in part]
        selected = [r['selected'] if official else n_select(r['candidates'], share) for r in part]
        item = dict(months=len(part), min=min(counts) if counts else None,
                    median=statistics.median(counts) if counts else None,
                    max=max(counts) if counts else None,
                    below_10=sum(n < 10 for n in counts), below_5=sum(n < 5 for n in counts),
                    selected_median=statistics.median(selected) if selected else None)
        if official:
            reasons = Counter()
            for row in part:
                reasons.update(row['reason_counts'])
            considered = sum(r['considered'] for r in part)
            item.update(universe_too_small=sum(r['status'] == 'UNIVERSE_TOO_SMALL' for r in part),
                        considered=considered, reason_counts=dict(sorted(reasons.items())),
                        reason_rates={k: v / considered for k, v in sorted(reasons.items())} if considered else {})
        else:
            item['market_pool_median'] = statistics.median(r['market_pool'] for r in part) if part else None
        out[segment] = item
    return out


def financial_input_hashes(sources, artifact):
    out = {name + '_sha256': inputs.sha256(sources[name + '_path'])
           for name in ('indicators', 'availability')}
    for filename, key in (('labels.csv', 'b_pit_labels_sha256'), ('models.json', 'b_pit_models_sha256')):
        out[key] = inputs.sha256(artifact / filename) if artifact else None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default=CONFIG, type=Path)
    ap.add_argument('--b-v4', action='store_true', help='force the legacy B v4 reference for baseline config only')
    args = ap.parse_args()
    config_path = ROOT / args.config
    cfg = json.loads(config_path.read_text(encoding='utf-8'))
    if args.b_v4 and ('financial_data' in cfg or cfg.get('version') == 'm3-strategy-enriched-v1'):
        ap.error('--b-v4 cannot be combined with enriched financial sources')
    sources = inputs.financial_sources(cfg, root=ROOT)
    load_cfg = dict(cfg)
    if args.b_v4:
        load_cfg.pop('financial_pit', None)
    elif cfg.get('financial_pit', {}).get('artifact'):
        load_cfg['financial_pit'] = dict(cfg['financial_pit'], artifact=str(ROOT / cfg['financial_pit']['artifact']))
    fin, fin_order, source_type, artifact, fin_cutoffs = m3_runner.load_financial(load_cfg, targets_only=True)
    if fin_order is None:
        fin_order = financial_order_from_labels(fin)
    source = 'B_PIT:' + str(cfg['financial_pit']['artifact']) if source_type == 'B_PIT' else source_type
    hashes = financial_input_hashes(sources, artifact)
    market = inputs.market_snapshots()
    sector = inputs.sectors(sources['indicators_path'])
    indicators = inputs.indicators(sources['indicators_path'])
    avail = inputs.availability(sources['availability_path'], historical_reference=source_type == 'B_V4_REFERENCE_NOT_PIT')
    decisions = decision_segments(cfg, market)
    print('financial source:', source)
    variants = {}
    for name, (market_rule, fin_rule) in VARIANTS.items():
        allowed_fin = {y: allowed_clusters(o, fin_rule) for y, o in fin_order.items()}
        rows = []
        for date, segment in decisions:
            cands, audit, _ = candidate_universe(market[date], date, fin, avail, sector, allowed_fin,
                                                market_rule=market_rule, stale_months=cfg.get('stale_months', 18),
                                                financial_cutoffs=fin_cutoffs)
            rows.append(dict(date=date, segment=segment, market_pool=sum(a['market_eligible'] for a in audit),
                             candidates=len(cands)))
        stats = summary(rows, cfg['segments'], share=cfg['top_share'])
        variants[name] = dict(market_rule=market_rule, financial_rule=fin_rule, summary=stats, monthly=rows)
        print(name, json.dumps(stats, ensure_ascii=False))
    strategies = Strategies(cfg, market, fin, avail, sector, indicators, fin_order=fin_order,
                            financial_cutoffs=fin_cutoffs)
    official = []
    for date, segment in decisions:
        result = strategies.target_for('combined', date)
        reasons = Counter(a['reason'] for a in result['audit'] if a['reason'])
        official.append(dict(date=date, segment=segment, candidates=result['candidates'], status=result['status'],
                             selected=len(result['picks']), considered=len(result['audit']),
                             reason_counts=dict(sorted(reasons.items())), audit=result['audit']))
    official_summary = summary(official, cfg['segments'], official=True)
    print('official config (after FINANCIAL_CRITERIA_MISSING):', json.dumps(official_summary, ensure_ascii=False))
    run = ROOT / 'data/experiments/m3/feasibility-variants' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True)
    commit, dirty = m3_runner.git_state()
    payload = dict(config=str(args.config), config_sha256=inputs.sha256(config_path),
                   git_commit=commit, git_dirty=dirty, inputs_sha256=hashes, financial_source=source,
                   financial_order=fin_order, reason_rate_denominator='all audited ticker-decision rows per segment',
                   official_config=dict(summary=official_summary, monthly=official), variants=variants)
    (run / 'variants.json').write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')
    print(run)


if __name__ == '__main__':
    main()
