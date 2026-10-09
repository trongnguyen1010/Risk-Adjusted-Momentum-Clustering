"""Offline reference calculators. No clustering/research eligibility promotion."""
from decimal import Decimal, localcontext, ROUND_HALF_UP, InvalidOperation
from .registry import FeatureDefinition, FeatureRegistry

REGISTRY = FeatureRegistry([
    FeatureDefinition(name=name, family='financial_reference', version='1.0.0', formula=formula,
        required_source=('reviewed_consolidated_vas_facts', 'exact_pdf_publication', 'observed_calendar'),
        lookback='three annual years' if name=='piotroski_f_score_reference' else 'same annual report vintage',
        point_in_time_rule='decision_date >= usable_from_date; reviewed annual PDF per year' if name=='piotroski_f_score_reference' else 'decision_date >= usable_from_date; same PDF',
        missing_policy='NULL_WITH_REASON; no partial total; positive denominator', transform='none',
        cluster_eligible=False, reference='docs/research/FINANCIAL_FEATURE_CONTRACT.md')
    for name, formula in [('annual_basic_eps_reference', 'adjusted_earnings / weighted_average_basic_shares'),
                          ('annual_diluted_eps_reference', 'adjusted_earnings / weighted_average_diluted_shares'),
                          ('em_z_double_prime_reference', '3.25+6.56*WC/TA+3.26*RE/TA+6.72*EBIT/TA+1.05*E/TL'),
                          ('piotroski_f_score_reference', 'sum of nine strict binary signals; NULL unless all nine known')]
])


def calculate_f_score(values):
    """Keys are (field, year offset); preserve missing/invalid signal reasons."""
    from ..ingestion.financial_pilot_readiness import SIGNALS
    REGISTRY.get('piotroski_f_score_reference')
    signals = {}
    with localcontext() as context:
        context.prec = 36
        for name, required in SIGNALS.items():
            missing = [dict(field=f, offset=o) for f, o in required if (f, o) not in values]
            if missing:
                signals[name] = dict(value=None, reason='MISSING_REQUIRED_INPUTS', missing=missing)
                continue
            try:
                if any(type(values[k]) is bool for k in required):
                    raise ValueError('boolean is not numeric evidence')
                v = {k: Decimal(str(values[k])) for k in required}
                if any(not x.is_finite() for x in v.values()):
                    raise ValueError('nonfinite')
                def get(field, offset=0):
                    return v[field, offset]
                def ratio(n, d):
                    if d <= 0:
                        raise ValueError('nonpositive denominator')
                    return n / d
                def average_assets(offset):
                    a, b = get('total_assets', offset), get('total_assets', offset-1)
                    if a <= 0 or b <= 0:
                        raise ValueError('nonpositive assets')
                    return (a+b)/2
                if name == 'positive_roa':
                    passed = ratio(get('income_before_extraordinary_items'), get('total_assets', -1)) > 0
                elif name == 'positive_cfo':
                    passed = ratio(get('operating_cash_flow'), get('total_assets', -1)) > 0
                elif name == 'improved_roa':
                    passed = ratio(get('income_before_extraordinary_items'), get('total_assets', -1)) > ratio(get('income_before_extraordinary_items', -1), get('total_assets', -2))
                elif name == 'cash_accrual_quality':
                    passed = ratio(get('operating_cash_flow'), get('total_assets', -1)) > ratio(get('income_before_extraordinary_items'), get('total_assets', -1))
                elif name == 'reduced_leverage':
                    if get('long_term_debt_including_current_portion') < 0 or get('long_term_debt_including_current_portion', -1) < 0:
                        raise ValueError('negative debt')
                    passed = ratio(get('long_term_debt_including_current_portion'), average_assets(0)) < ratio(get('long_term_debt_including_current_portion', -1), average_assets(-1))
                elif name == 'improved_liquidity':
                    passed = ratio(get('current_assets'), get('current_liabilities')) > ratio(get('current_assets', -1), get('current_liabilities', -1))
                elif name == 'no_parent_issuance':
                    issuance = get('parent_common_equity_issuance_verified')
                    if issuance not in (0, 1):
                        raise ValueError('invalid indicator')
                    passed = issuance == 0
                elif name == 'improved_gross_margin':
                    passed = ratio(get('gross_profit'), get('net_revenue')) > ratio(get('gross_profit', -1), get('net_revenue', -1))
                elif name == 'improved_turnover':
                    passed = ratio(get('net_revenue'), average_assets(0)) > ratio(get('net_revenue', -1), average_assets(-1))
                signals[name] = dict(value=int(passed), reason='REFERENCE_CALCULATED')
            except (InvalidOperation, ValueError, TypeError, ArithmeticError):
                signals[name] = dict(value=None, reason='INVALID_INPUT_OR_DENOMINATOR')
    known = [s['value'] for s in signals.values() if s['value'] is not None]
    return dict(status='REFERENCE_CALCULATED' if len(known)==9 else 'PARTIAL_REFERENCE_SIGNALS',
                value=sum(known) if len(known)==9 else None, signals=signals, known_signals=len(known),
                financial_features_allowed=False, research_ready=False)


def calculate(task, values):
    """Decimal arithmetic and explicit denominator checks; return JSON-safe strings."""
    required = {'EPS_RECOMPUTE': {'eps_adjusted_earnings_numerator','weighted_average_basic_shares','weighted_average_diluted_shares'},
                'Z_SCORE': {'current_assets','current_liabilities','total_assets','retained_earnings',
                            'document_reconciled_ebit','total_equity','total_liabilities'}}
    if task not in required:
        return dict(status='TASK_NOT_IMPLEMENTED_IN_REFERENCE_SLICE', value=None)
    missing = sorted(required[task]-values.keys())
    if missing:
        return dict(status='MISSING_REQUIRED_INPUTS',value=None,missing=missing)
    with localcontext() as context:
        context.prec = 36
        try:
            v = {k: Decimal(str(values[k])) for k in required[task]}
        except (InvalidOperation, ValueError, TypeError):
            return dict(status='INVALID_NUMERIC_INPUT',value=None)
        if any(not x.is_finite() for x in v.values()):
            return dict(status='INVALID_NONFINITE_INPUT', value=None)
        if task == 'EPS_RECOMPUTE':
            basic, diluted = v['weighted_average_basic_shares'], v['weighted_average_diluted_shares']
            if basic <= 0 or diluted <= 0:
                return dict(status='NONPOSITIVE_SHARE_DENOMINATOR', value=None)
            numerator = v['eps_adjusted_earnings_numerator']
            result = {'annual_basic_eps_reference': numerator/basic,
                      'annual_diluted_eps_reference': numerator/diluted}
        elif task == 'Z_SCORE':
            assets, liabilities = v['total_assets'], v['total_liabilities']
            if assets <= 0 or liabilities <= 0:
                return dict(status='NONPOSITIVE_BALANCE_DENOMINATOR', value=None)
            result = {'em_z_double_prime_reference': Decimal('3.25') + Decimal('6.56')*(v['current_assets']-v['current_liabilities'])/assets
                      + Decimal('3.26')*v['retained_earnings']/assets
                      + Decimal('6.72')*v['document_reconciled_ebit']/assets
                      + Decimal('1.05')*v['total_equity']/liabilities}
        else:
            return dict(status='TASK_NOT_IMPLEMENTED_IN_REFERENCE_SLICE', value=None)
        for name in result:
            REGISTRY.get(name)
        return dict(status='REFERENCE_CALCULATED', value={k:str(x) for k,x in result.items()},
                    rounded={k:str(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP)) for k,x in result.items()
                             if 'eps' in k},financial_features_allowed=False, research_ready=False)
