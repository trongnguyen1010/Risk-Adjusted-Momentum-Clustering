"""Offline gross capital bridge, separate from same-date net book equity."""
from datetime import date
from decimal import localcontext

from .financial_ttm_reference import number
from .registry import FeatureDefinition, FeatureRegistry

VARIANT = 'GROSS_ESOP_CAPITAL_BRIDGE_PB_REFERENCE'
REGISTRY = FeatureRegistry([
    FeatureDefinition(
        name='gross_esop_capital_bridge_pb_reference', family='financial_reference', version='1.0.0',
        formula='raw close * current common shares / (reported parent equity + verified gross ESOP capital conversion)',
        required_source=('reviewed_parent_equity', 'bank_proceeds_confirmations',
                         'registered_capital_notice', 'raw_close'),
        lookback='last reported balance plus explicitly reviewed ESOP event',
        point_in_time_rule='all evidence usable by decision_date; registration effective after balance date',
        missing_policy='NULL_WITH_REASON; unknown fees remain null; no implicit zero deduction',
        transform='none', cluster_eligible=False,
        reference='docs/research/FINANCIAL_FEATURE_CONTRACT.md')
])


def gross_capital_bridge(snapshot, event, raw_price, common_shares, decision_date):
    """Calculate a disclosed gross-event reference, without asserting current equity.

    Only the verified registered capital increase is added to gross equity.
    Cash receipt before the balance date does not establish its classification
    at that date. Asset/liability changes stay unknown unless separately reviewed.
    Fees and subsequent results are outside this bridge, not assumed zero.
    """
    base = dict(variant=VARIANT, value=None, strict_event_adjusted_pb=None,
                financial_features_allowed=False, research_ready=False,
                production_review_status='MANUAL_REVIEW_REQUIRED')
    try:
        day = date.fromisoformat(decision_date)
        balance = date.fromisoformat(snapshot['balance_date'])
        effective = date.fromisoformat(event['registration_effective_date'])
        if day < effective or balance >= effective:
            raise ValueError('registration outside post-balance decision window')
        evidence = [snapshot['evidence'], *event['evidence']]
        if not evidence or any(e['validation_status'] != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED'
                               for e in evidence):
            raise ValueError('unreviewed evidence')
        if any(date.fromisoformat(e['usable_from_date']) > day for e in evidence):
            return dict(base, status='EVIDENCE_NOT_YET_USABLE')
        if (event['symbol'] != snapshot['symbol'] or event['currency'] != 'VND'
                or event['cash_treatment'] not in {'VERIFIED_ADVANCE_LIABILITY_AT_BALANCE',
                                                  'BALANCE_CLASSIFICATION_NOT_SEPARATELY_DISCLOSED'}):
            raise ValueError('identity, units or advance treatment mismatch')
        equity = number(snapshot['parent_equity'], positive=True)
        cash = number(event['gross_bank_proceeds'], positive=True)
        new = number(event['new_common_shares'], positive=True)
        before = number(event['before_common_shares'], positive=True)
        after = number(common_shares, positive=True)
        if any(s != s.to_integral_value() for s in [before, new, after]):
            raise ValueError('fractional outstanding common shares')
        if (before != number(snapshot['reported_common_shares'], positive=True)
                or after != number(event['after_common_shares'], positive=True)
                or before + new != after
                or cash != new * number(event['issue_price'], positive=True)
                or cash != number(event['registered_capital_increase'], positive=True)):
            raise ValueError('cash, capital or share bridge mismatch')
        advance_verified = event['cash_treatment'] == 'VERIFIED_ADVANCE_LIABILITY_AT_BALANCE'
        if advance_verified and (event['advance_balance_date'] != snapshot['balance_date']
                                 or cash != number(event['verified_advance_liability'], positive=True)):
            raise ValueError('advance liability mismatch')
        # None is intentionally retained: a gross reference is not a zero-fee estimate.
        fee = event['actual_issuance_fee']
        if fee is not None:
            raise ValueError('net fee treatment needs a separate reviewed contract')
        with localcontext() as ctx:
            ctx.prec = 36
            gross_equity = equity + cash
            value = number(raw_price, positive=True) * after / gross_equity
        return dict(base, status='GROSS_CAPITAL_BRIDGE_REFERENCE_CALCULATED', value=str(value),
                    reported_parent_equity=str(equity), gross_capital_conversion=str(cash),
                    gross_bridge_parent_equity=str(gross_equity),
                    gross_assets_change='0' if advance_verified else None,
                    gross_liabilities_change=str(-cash) if advance_verified else None,
                    gross_equity_change=str(cash), actual_issuance_fee=None,
                    cash_treatment=event['cash_treatment'],
                    fee_status='NOT_SEPARATELY_VERIFIED',
                    book_equity_date=snapshot['balance_date'],
                    includes_subsequent_operating_results=False,
                    limitations=['Gross capital conversion excludes unknown fee treatment',
                                 'Subsequent earnings and other movements are not observed',
                                 'Event ledger is bounded; current net equity is not verified'])
    except (ValueError, KeyError, TypeError, ArithmeticError):
        return dict(base, status='INVALID_OR_INCOMPLETE_EQUITY_BRIDGE')
