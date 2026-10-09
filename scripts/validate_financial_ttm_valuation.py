"""Verify sealed reference artifacts and temporal/event regressions with actual review."""
import argparse,json,sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.ingestion.financial_share_events import select_common_shares


def validate(first,replay):
    a,b=ROOT/first,ROOT/replay
    for run in [a,b]:verify_inventory(run)
    if (a/'results.json').read_bytes()!=(b/'results.json').read_bytes():raise ValueError('non-deterministic replay')
    r=json.loads((a/'results.json').read_bytes());review=r['review'];rows=r['results']
    policy=json.loads((ROOT/'configs/data/financial_date_pit_v1.json').read_bytes())
    calendar=[json.loads(l) for l in (ROOT/policy['calendar_path']).read_text(encoding='utf8').splitlines()]
    checks=[]
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise ValueError(name)
    check('DETERMINISTIC_REPLAY',True)
    check('REPORTED_TTM_NUMERATOR',rows[-1]['ttm']['reported_numerator']=='9489154548717')
    check('PARENT_PROFIT_BRIDGE',rows[-1]['ttm']['parent_profit']=='9999322256386')
    check('SAME_PUBLICATION_DAY_BLOCKED',rows[0]['ttm']['value'] is None and rows[0]['valuation']['pe'] is None)
    check('FIRST_NEXT_SESSION_AND_LAST_SNAPSHOT',all(x['ttm']['status']=='REPORTED_TTM_REFERENCE_CALCULATED' for x in rows[1:]))
    check('CURRENT_COMMON_COUNT',all(x['shares']['value']==1714326422 for x in rows[1:]))
    check('PLAN_NOT_APPLIED',all(any(e['event_id']=='BONUS_2026_PLAN' and e['reason']=='PLAN_OR_CASH_EVENT_NOT_SHARE_ISSUANCE'
         for e in x['shares']['excluded']) for x in rows[1:]))
    check('UNESTIMATED_DEDUCTION_NOT_ZERO',review['periods']['current_ytd']['reported_deduction'] is None
        and all(x['ttm']['strict_normalized_ttm_eps'] is None for x in rows))
    check('STRICT_EVENT_ADJUSTED_PB_NULL',all(x['valuation']['strict_event_adjusted_pb'] is None for x in rows))
    check('CAPITAL_RECLASSIFICATION_NOT_ESOP_CASH',review['latest_balance']['reclassification_is_esop_cash_proceeds'] is False
        and review['latest_balance']['capital_reclassification_effect_on_total_parent_equity']==0)
    check('HISTORICAL_ISSUANCE_REVIEW_BLOCK',select_common_shares(review['initial_share_snapshot'],review['share_events'],
        '2026-06-29',calendar)['status']=='KNOWN_ISSUANCE_EFFECTIVE_BASIS_REVIEW_PENDING')
    check('GATES_CLOSED',all(r[k] is False for k in ['financial_features_allowed','research_ready','full_universe_allowed'])
        and all(d['cluster_eligible'] is False for d in r['feature_registry']))
    check('TTM_EPS_ROUND',Decimal(rows[-1]['ttm']['value']).quantize(Decimal(1),rounding=ROUND_HALF_UP)==5570)
    return dict(checks=checks,passed=len(checks),review_checks=review['checks'],replay_identical=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--replay',required=True)
    a=p.parse_args();print(json.dumps(validate(a.run,a.replay)))
