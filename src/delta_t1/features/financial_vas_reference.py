"""Explicit VAS adaptations and sensitivity calculations, separate from strict scores."""
from decimal import Decimal, localcontext, InvalidOperation, ROUND_HALF_UP
from .financial_reference import calculate_f_score
from .registry import FeatureDefinition, FeatureRegistry

F_VARIANT='PIOTROSKI_VAS_REPORTED_NET_PROFIT_REFERENCE'
M_VARIANT='BENEISH_2013_VAS_REPORTED_PROFIT_OWNED_PPE_SENSITIVITY'
REGISTRY=FeatureRegistry([FeatureDefinition(name=name,family='financial_reference',version='1.0.0',formula=formula,
    required_source=('reviewed_consolidated_vas_facts','exact_pdf_publication') +
        (('raw_price','share_event_coverage') if name.startswith('reported_basis') else ()),
    lookback=('three annual years' if name.startswith('f_score') else 'two annual years' if name.startswith('m_score') else 'reported balance snapshot and exact 12-month EPS'),
    point_in_time_rule='all inputs available by decision date; reviewed PDF per year',
    missing_policy='NULL_WITH_REASON',transform='none',cluster_eligible=False,
    reference='docs/research/FINANCIAL_FEATURE_CONTRACT.md') for name,formula in [
    ('f_score_vas_reported_profit_reference','nine signals with explicit VAS reported net-profit adaptation'),
    ('m_score_vas_sensitivity_reference','eight-variable 2013 model; declared receivables/PPE/earnings assumptions'),
    ('reported_basis_pe_reference','raw price / latest eligible exact 12-month annual EPS'),
    ('reported_basis_pb_reference','raw price * reported common shares / same-date parent common equity')]])
REGISTRY.register(FeatureDefinition(name='period_eps_reference',family='financial_reference',version='1.0.0',
    formula='explicit reported EPS numerator / disclosed weighted shares for exact statement period',
    required_source=('reviewed_exact_period_eps_note','exact_pdf_publication'),lookback='explicit 3/6/9/12 month statement period',
    point_in_time_rule='source note released by decision date; no annualization or sum of quarterly EPS',
    missing_policy='NULL_WITH_REASON',transform='none',cluster_eligible=False,
    reference='docs/research/FINANCIAL_FEATURE_CONTRACT.md'))
REGISTRY.register(FeatureDefinition(name='disclosed_basic_eps_reference',family='financial_reference',version='1.0.0',
    formula='disclosed reported EPS numerator / disclosed weighted basic common shares',
    required_source=('reviewed_exact_period_eps_note','exact_pdf_publication'),lookback='explicit 3/6/9/12 month statement period',
    point_in_time_rule='source note released by decision date; comparative revision retained at current vintage',
    missing_policy='NULL_WITH_REASON; unknown dilution or reserve never becomes zero',transform='none',cluster_eligible=False,
    reference='docs/research/FINANCIAL_FEATURE_CONTRACT.md'))


def calculate_disclosed_basic_eps(numerator, basic_shares, months):
    """Reported arithmetic only; no claim about normalized reserve or dilution."""
    REGISTRY.get('disclosed_basic_eps_reference')
    base = dict(financial_features_allowed=False, research_ready=False, months=months,
                diluted_eps=None, strict_normalized_eps=None, annualized=False)
    if type(months) is not int or months not in [3, 6, 9, 12]:
        return dict(base, status='INVALID_PERIOD', value=None)
    try:
        if any(x is None or type(x) is bool for x in [numerator, basic_shares]):
            raise ValueError('missing or boolean')
        n, b = map(lambda x: Decimal(str(x)), [numerator, basic_shares])
        if not n.is_finite() or not b.is_finite() or b <= 0:
            raise ValueError('invalid')
        with localcontext() as c:
            c.prec = 36
            value = n / b
            return dict(base, status='DISCLOSED_BASIC_EPS_REFERENCE_CALCULATED', value=str(value),
                        rounded=str(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)))
    except (ValueError, InvalidOperation, ArithmeticError, TypeError):
        return dict(base, status='INVALID_EPS_INPUT', value=None)


def calculate_period_eps(numerator,basic_shares,diluted_shares,months):
    REGISTRY.get('period_eps_reference')
    base=dict(financial_features_allowed=False,research_ready=False,months=months)
    if type(months) is not int or months not in [3,6,9,12]:return dict(base,status='INVALID_PERIOD',value=None)
    try:
        if any(type(x) is bool for x in [numerator,basic_shares,diluted_shares]):raise ValueError('boolean')
        n,b,d=[Decimal(str(x)) for x in [numerator,basic_shares,diluted_shares]]
        if any(not x.is_finite() for x in [n,b,d]) or b<=0 or d<=0:raise ValueError('invalid')
        with localcontext() as c:
            c.prec=36;values=dict(basic=n/b,diluted=n/d)
            return dict(base,status='PERIOD_EPS_REFERENCE_CALCULATED',value={k:str(v) for k,v in values.items()},
                rounded={k:str(v.quantize(Decimal('1'),rounding=ROUND_HALF_UP)) for k,v in values.items()},annualized=False)
    except (ValueError,InvalidOperation,ArithmeticError,TypeError):return dict(base,status='INVALID_EPS_INPUT',value=None)


def calculate_vas_f_score(values):
    REGISTRY.get('f_score_vas_reported_profit_reference')
    adapted=dict(values)
    for offset in [0,-1]:
        adapted.pop(('income_before_extraordinary_items',offset),None)
        if ('net_profit',offset) in values:
            adapted['income_before_extraordinary_items',offset]=values['net_profit',offset]
    result=calculate_f_score(adapted)
    return dict(result,variant=F_VARIANT,earnings_basis='VAS_CONSOLIDATED_REPORTED_NET_PROFIT',
                strict_original_score=False,production_review_status='MANUAL_REVIEW_REQUIRED')


M_FIELDS=['receivables','net_revenue','gross_profit','current_assets','net_tangible_ppe',
          'total_assets','owned_tangible_ppe_depreciation','selling_expense','administrative_expense',
          'current_liabilities','noncurrent_loans_and_finance_leases']


def calculate_vas_m_score(values,receivables_basis):
    REGISTRY.get('m_score_vas_sensitivity_reference')
    required={(f,o) for f in M_FIELDS for o in [0,-1]}|{('net_profit',0),('operating_cash_flow',0)}
    base=dict(value=None,variant=M_VARIANT,receivables_basis=receivables_basis,strict_original_score=False,
              financial_features_allowed=False,research_ready=False,production_review_status='MANUAL_REVIEW_REQUIRED')
    if receivables_basis not in ['GROSS_SHORT_TERM_TRADE','ALLOCATION_BOUND_SCENARIO']:
        return dict(base,status='UNDECLARED_RECEIVABLES_BASIS')
    missing=sorted(required-values.keys())
    if missing:return dict(base,status='MISSING_REQUIRED_INPUTS',missing=[list(k) for k in missing])
    with localcontext() as context:
        context.prec=36
        try:
            if any(type(values[k]) is bool for k in required):raise ValueError('boolean')
            v={k:Decimal(str(values[k])) for k in required}
            if any(not x.is_finite() for x in v.values()):raise ValueError('nonfinite')
            def g(f,o=0):return v[f,o]
            def ratio(a,b):
                if b<=0:raise ValueError('nonpositive denominator')
                return a/b
            for o in [0,-1]:
                if any(g(f,o)<0 for f in ['receivables','net_tangible_ppe','owned_tangible_ppe_depreciation','noncurrent_loans_and_finance_leases']):
                    raise ValueError('negative component')
            ratios=dict(DSR=ratio(ratio(g('receivables'),g('net_revenue')),ratio(g('receivables',-1),g('net_revenue',-1))),
                GMI=ratio(ratio(g('gross_profit',-1),g('net_revenue',-1)),ratio(g('gross_profit'),g('net_revenue'))),
                AQI=ratio(1-ratio(g('current_assets')+g('net_tangible_ppe'),g('total_assets')),
                          1-ratio(g('current_assets',-1)+g('net_tangible_ppe',-1),g('total_assets',-1))),
                SGI=ratio(g('net_revenue'),g('net_revenue',-1)),
                DEPI=ratio(ratio(g('owned_tangible_ppe_depreciation',-1),g('owned_tangible_ppe_depreciation',-1)+g('net_tangible_ppe',-1)),
                           ratio(g('owned_tangible_ppe_depreciation'),g('owned_tangible_ppe_depreciation')+g('net_tangible_ppe'))),
                SGAI=ratio(ratio(g('selling_expense')+g('administrative_expense'),g('net_revenue')),
                           ratio(g('selling_expense',-1)+g('administrative_expense',-1),g('net_revenue',-1))),
                ACCRUALS=ratio(g('net_profit')-g('operating_cash_flow'),g('total_assets')),
                LEVI=ratio(ratio(g('current_liabilities')+g('noncurrent_loans_and_finance_leases'),g('total_assets')),
                           ratio(g('current_liabilities',-1)+g('noncurrent_loans_and_finance_leases',-1),g('total_assets',-1))))
            if 1-ratio(g('current_assets')+g('net_tangible_ppe'),g('total_assets'))<0:raise ValueError('negative asset quality')
            coefficients=dict(DSR='.92',GMI='.528',AQI='.404',SGI='.892',DEPI='.115',SGAI='-.172',ACCRUALS='4.679',LEVI='-.327')
            value=Decimal('-4.84')+sum(Decimal(coefficients[k])*x for k,x in ratios.items())
            return dict(base,status='REFERENCE_SENSITIVITY_CALCULATED',value=str(value),ratios={k:str(x) for k,x in ratios.items()},classification_threshold=None)
        except (ValueError,InvalidOperation,ArithmeticError,TypeError):
            return dict(base,status='INVALID_INPUT_OR_DENOMINATOR')


def calculate_reported_valuation(price,eps,parent_equity,shares):
    """Arithmetic for declared reported basis; orchestration must enforce temporal/event gates."""
    base=dict(financial_features_allowed=False,research_ready=False,production_review_status='MANUAL_REVIEW_REQUIRED')
    try:
        if any(type(x) is bool for x in [price,eps,parent_equity,shares]):raise ValueError('boolean')
        p,e,b,s=map(lambda x:Decimal(str(x)),[price,eps,parent_equity,shares])
        if any(not x.is_finite() or x<=0 for x in [p,e,b,s]):raise ValueError('invalid')
        with localcontext() as c:
            c.prec=36
            for name in ['reported_basis_pe_reference','reported_basis_pb_reference']:REGISTRY.get(name)
            return dict(base,status='REPORTED_BASIS_REFERENCE_CALCULATED',pe=str(p/e),pb=str(p*s/b),bvps=str(b/s))
    except (ValueError,InvalidOperation,ArithmeticError,TypeError):
        return dict(base,status='INVALID_VALUATION_INPUT',pe=None,pb=None,bvps=None)
