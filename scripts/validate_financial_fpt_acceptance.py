"""Check real FPT replay, exact evidence, temporal boundaries and accounting QA."""
import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.experiments.financial_ttm_valuation import verify_review


def validate(first, replay):
    a, b = ROOT / first, ROOT / replay
    for run in [a, b]:
        verify_inventory(run)
    if (a / 'results.json').read_bytes() != (b / 'results.json').read_bytes():
        raise ValueError('non-deterministic replay')
    r = json.loads((a / 'results.json').read_bytes())
    verify_review(r['equity_review'], ROOT)
    rows = r['results']
    latest = {x['task']: x for x in rows[-1]['metrics']}
    bridge = rows[-1]['equity_bridge']
    event = r['equity_review']['event']
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed:
            raise ValueError(name)
    check('DETERMINISTIC_REPLAY', True)
    check('SIX_DISTINCT_FAMILIES', set(latest) == {'F_SCORE', 'M_SCORE', 'Z_SCORE', 'EPS_RECOMPUTE', 'PE', 'PB'})
    check('LATEST_REFERENCE_COUNTS', [x['reference_metric_families_available'] for x in rows] == [3, 6, 6])
    check('PUBLICATION_DAY_LATEST_TTM_AND_PB_BLOCKED', all(x['value'] is None for x in rows[0]['metrics'] if x['task'] in {'EPS_RECOMPUTE', 'PE', 'PB'}))
    check('ALL_NINE_F_SIGNALS', latest['F_SCORE']['value'] == 3 and latest['F_SCORE']['source_result']['vas_reference']['known_signals'] == 9)
    check('EIGHT_M_RATIOS_NO_THRESHOLD', len(latest['M_SCORE']['source_result']['gross_trade_reference']['ratios']) == 8
          and latest['M_SCORE']['source_result']['gross_trade_reference']['classification_threshold'] is None)
    check('REGISTERED_CAPITAL_AND_BANK_TOTAL', event['registered_capital_increase'] == event['gross_bank_proceeds'] == 108193010000)
    check('GROSS_EQUITY_BRIDGE', Decimal(bridge['gross_bridge_parent_equity']) == Decimal(39851463524930) + Decimal(108193010000))
    check('INDEPENDENT_PB_ARITHMETIC', Decimal(bridge['value']).quantize(Decimal('.000000001')) ==
          (Decimal(73200) * Decimal(1714326422) / Decimal(39959656534930)).quantize(Decimal('.000000001')))
    check('UNKNOWN_CLASSIFICATION_NOT_INFERRED', bridge['gross_assets_change'] is None and bridge['gross_liabilities_change'] is None)
    check('UNKNOWN_FEE_NOT_ZERO_STRICT_PB_NULL', event['actual_issuance_fee'] is None and bridge['strict_event_adjusted_pb'] is None)
    check('REGISTRATION_DATE_TYPES_RETAINED', event['registration_effective_date'] == '2026-07-16'
          and event['registration_publication_date'] == '2026-07-17'
          and event['historical_common_share_effective_basis'].startswith('UNRESOLVED'))
    check('SEPARATE_EQUITY_NOT_SUBSTITUTED', event['accounting_discovery']['consolidated_parent_equity_from_separate_statement_allowed'] is False)
    check('STRICT_F_AND_M_NULL', latest['F_SCORE']['source_result']['strict']['value'] is None
          and latest['M_SCORE']['source_result']['strict_value'] is None)
    check('STRICT_TTM_NULL', latest['EPS_RECOMPUTE']['source_result']['strict_normalized_ttm_eps'] is None)
    check('ALL_PRODUCTION_GATES_CLOSED', all(r[k] is False for k in ['financial_features_allowed', 'research_ready', 'full_universe_allowed'])
          and all(not m['production_accepted'] for x in rows for m in x['metrics'])
          and all(not d['cluster_eligible'] for d in r['feature_registry']))
    return dict(checks=checks, passed=len(checks), accounting_checks=r['equity_review']['checks'], replay_identical=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True)
    p.add_argument('--replay', required=True)
    a = p.parse_args()
    print(json.dumps(validate(a.run, a.replay)))
