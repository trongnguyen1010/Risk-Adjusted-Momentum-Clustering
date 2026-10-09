"""Offline reported-numerator TTM references; never sum rounded period EPS."""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from .registry import FeatureDefinition, FeatureRegistry

VARIANT = 'REPORTED_NUMERATOR_SHARE_DAYS_TTM_REFERENCE'
REGISTRY = FeatureRegistry([
    FeatureDefinition(name=name, family='financial_reference', version='1.0.0',
        formula=formula, required_source=('reviewed_eps_notes', 'exact_pdf_publications',
            'parent_earnings_scope_bridge', 'common_share_basis_evidence'),
        lookback='exact trailing calendar year from FY + current YTD - prior YTD',
        point_in_time_rule='every exact source usable by decision_date; no restatement backfill',
        missing_policy='NULL_WITH_REASON; unestimated deductions remain unknown',
        transform='none', cluster_eligible=False,
        reference='docs/research/FINANCIAL_FEATURE_CONTRACT.md')
    for name, formula in [
        ('reported_numerator_ttm_eps_reference',
         '(FY reported EPS numerator + current YTD numerator - prior YTD numerator) / combined share-days'),
        ('parent_profit_ttm_per_weighted_share_reference',
         '(FY parent profit + current YTD parent profit - prior YTD parent profit) / combined share-days'),
        ('reported_ttm_pe_reference', 'raw close / reported-numerator TTM EPS'),
        ('current_shares_reported_equity_pb_reference',
         'raw close * current common shares / last reported parent equity; disclose post-balance events')]])


def number(value, *, positive=False):
    if value is None or type(value) is bool:
        raise ValueError('missing or boolean number')
    result = Decimal(str(value))
    if not result.is_finite() or (positive and result <= 0):
        raise ValueError('invalid number')
    return result


def reported_ttm(periods, bridge, decision_date):
    """Periods are explicitly reviewed FY/current YTD/prior YTD, on one share basis.

    FY minus prior YTD isolates the previous year's remainder. Its share-days
    are then combined with current YTD using actual inclusive calendar days.
    This reports issuer EPS deduction practices, not an estimated normalized EPS.
    """
    REGISTRY.get('reported_numerator_ttm_eps_reference')
    base = dict(variant=VARIANT, value=None, financial_features_allowed=False,
        research_ready=False, strict_normalized_ttm_eps=None,
        production_review_status='MANUAL_REVIEW_REQUIRED')
    try:
        decision = date.fromisoformat(decision_date)
        if len(periods) != 3 or set(periods) != {'fy', 'current_ytd', 'prior_ytd'}:
            raise ValueError('exact three-period input required')
        f, c, p = [periods[k] for k in ['fy', 'current_ytd', 'prior_ytd']]
        starts = [date.fromisoformat(x['period_start']) for x in [f, c, p]]
        ends = [date.fromisoformat(x['period_end']) for x in [f, c, p]]
        fs, cs, ps = starts; fe, ce, pe = ends
        if (fs != date(fs.year, 1, 1) or fe != date(fs.year, 12, 31)
                or ps != fs or cs != date(fs.year + 1, 1, 1)
                or ce.year != cs.year or pe.year != fs.year
                or (pe.month, pe.day) != (ce.month, ce.day)
                or not (ps <= pe < fe and cs <= ce < date(cs.year, 12, 31))):
            return dict(base, status='INVALID_TTM_WINDOWS')
        if any(not x.get('usable_from_date') or date.fromisoformat(x['usable_from_date']) > decision
               for x in [f, c, p]) or not bridge.get('usable_from_date') or date.fromisoformat(bridge['usable_from_date']) > decision:
            return dict(base, status='INPUT_NOT_YET_AVAILABLE')
        if any(date.fromisoformat(x['usable_from_date']) <= end for x, end in zip([f,c,p],ends)):
            return dict(base, status='AVAILABILITY_PRECEDES_PERIOD_END')
        if any(not x.get('symbol') for x in [f,c,p]) or len({x['symbol'] for x in [f,c,p]}) != 1:
            return dict(base, status='INCOMPATIBLE_ENTITY')
        if any(x.get('validation_status') != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED'
               or x.get('numerator_unit') != 'VND' or x.get('share_unit') != 'SHARES'
               or x.get('statement_scope') != 'CONSOLIDATED' or x.get('accounting_framework') != 'VAS'
               for x in [f, c, p]):
            return dict(base, status='UNREVIEWED_OR_INCOMPATIBLE_SEMANTICS')
        if any(not x.get('share_basis_id') for x in [f, c, p]) or len({x['share_basis_id'] for x in [f, c, p]}) != 1:
            return dict(base, status='SHARE_BASIS_BRIDGE_REQUIRED')
        if bridge.get('parent_earnings_unchanged') is not True or bridge.get('h1_parent_profit_comparison_equal') is not True:
            return dict(base, status='PARENT_EARNINGS_SCOPE_BRIDGE_REQUIRED')
        policies = {x.get('deduction_policy') for x in [f, c, p]}
        if not policies <= {'ACTUAL_REPORTED_DEDUCTION', 'NOT_ESTIMATED_NOT_DEDUCTED'}:
            return dict(base, status='UNDECLARED_REPORTED_DEDUCTION_POLICY')
        with localcontext() as context:
            context.prec = 36
            ns = [number(x['reported_eps_numerator']) for x in [f, c, p]]
            profits = [number(x['parent_profit']) for x in [f, c, p]]
            for x, n, profit in zip([f, c, p], ns, profits):
                if x['deduction_policy'] == 'ACTUAL_REPORTED_DEDUCTION':
                    if n != profit - number(x['reported_deduction']) or number(x['reported_deduction']) < 0:
                        return dict(base, status='REPORTED_NUMERATOR_BRIDGE_FAILED')
                elif x.get('reported_deduction') is not None or n != profit:
                    return dict(base, status='UNESTIMATED_DEDUCTION_MUST_REMAIN_NULL')
            ds = [(e - s).days + 1 for s, e in zip(starts, ends)]
            fd, cd, pd = ds
            trailing_start = pe + timedelta(days=1)
            total_days = (ce - trailing_start).days + 1
            if total_days != fd - pd + cd:
                return dict(base, status='TTM_DAY_BRIDGE_FAILED')
            weighted = [number(x['weighted_basic_shares'], positive=True) for x in [f, c, p]]
            if any(v != v.to_integral_value() for v in weighted):
                return dict(base, status='WHOLE_SHARE_DISCLOSURE_REQUIRED')
            share_days = weighted[0]*fd + weighted[1]*cd - weighted[2]*pd
            if weighted[0]*fd - weighted[2]*pd <= 0:
                return dict(base, status='INVALID_PRIOR_REMAINDER_SHARE_DAYS')
            denominator = share_days / total_days
            if denominator <= 0:
                return dict(base, status='INVALID_TTM_DENOMINATOR')
            # Whole-share disclosures are rounded. This bound propagates ±0.5
            # share per source; it never snaps a denominator to current shares.
            error = Decimal('.5') * (fd + cd + pd) / total_days
            if denominator <= error:
                return dict(base, status='INVALID_TTM_DENOMINATOR')
            numerator = ns[0] + ns[1] - ns[2]
            parent_profit = profits[0] + profits[1] - profits[2]
            eps = numerator / denominator
            gross = parent_profit / denominator
            endpoints = sorted([numerator/(denominator-error), numerator/(denominator+error)])
            return dict(base, status='REPORTED_TTM_REFERENCE_CALCULATED', value=str(eps),
                parent_profit_per_weighted_share=str(gross), reported_numerator=str(numerator),
                parent_profit=str(parent_profit), weighted_basic_shares=str(denominator),
                weighted_share_rounding_error_bound=str(error), eps_rounding_interval=list(map(str, endpoints)),
                trailing_start=trailing_start.isoformat(), trailing_end=ce.isoformat(),
                calendar_days=dict(fy=fd, current_ytd=cd, prior_ytd=pd, ttm=total_days),
                reserve_status='UNESTIMATED_INTERIM_DEDUCTION_NOT_VERIFIED_ZERO'
                    if 'NOT_ESTIMATED_NOT_DEDUCTED' in policies else 'ALL_REPORTED_DEDUCTIONS',
                strict_reason='PERIOD_ALLOCATION_AND_CURRENT_UNESTIMATED_RESERVE_UNRESOLVED'
                    if 'NOT_ESTIMATED_NOT_DEDUCTED' in policies else 'PRODUCTION_ACCEPTANCE_PENDING',
                rounded_eps_not_summed=True)
    except (KeyError, ValueError, TypeError, InvalidOperation, ArithmeticError):
        return dict(base, status='INVALID_OR_MISSING_TTM_INPUT')


def reported_ttm_valuation(price, ttm, parent_equity, common_shares):
    """Declared current market-cap / latest reported book-equity reference.

    No cash proceeds, dividends or other post-balance changes are invented.
    It is not an event-adjusted or same-date book-equity claim.
    """
    base = dict(financial_features_allowed=False, research_ready=False,
        production_review_status='MANUAL_REVIEW_REQUIRED', pe=None, pb=None,
        strict_event_adjusted_pb=None, basis='CURRENT_COMMON_SHARES_LAST_REPORTED_PARENT_EQUITY')
    if ttm.get('status') != 'REPORTED_TTM_REFERENCE_CALCULATED':
        return dict(base, status='TTM_REFERENCE_UNAVAILABLE')
    try:
        with localcontext() as context:
            context.prec = 36
            p, e, b, s = [number(v, positive=True) for v in [price, ttm['value'], parent_equity, common_shares]]
            REGISTRY.get('reported_ttm_pe_reference')
            REGISTRY.get('current_shares_reported_equity_pb_reference')
            return dict(base, status='REPORTED_TTM_VALUATION_REFERENCE_CALCULATED',
                pe=str(p/e), pb=str(p*s/b), reported_equity_per_current_share=str(b/s))
    except (KeyError, ValueError, TypeError, InvalidOperation, ArithmeticError):
        return dict(base, status='NONPOSITIVE_OR_INVALID_VALUATION_INPUT')
