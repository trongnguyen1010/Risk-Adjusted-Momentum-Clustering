"""Owner-authorized exploratory ratios, isolated from production feature registry."""
import math
from decimal import Decimal
from .registry import FeatureDefinition,FeatureRegistry

FORMULAS={
    'gross_margin':'gross_profit / net_revenue',
    'net_margin':'net_profit / net_revenue',
    'liabilities_to_assets':'total_liabilities / ending_total_assets',
    'current_ratio':'current_assets / current_liabilities',
    'operating_cashflow_to_assets':'operating_cash_flow / ending_total_assets',
    'asset_turnover_ending_assets':'net_revenue / ending_total_assets',
}
FEATURES=list(FORMULAS)
REQUIRED={'gross_profit','net_profit','net_revenue','total_liabilities','total_assets','current_assets','current_liabilities','operating_cash_flow'}
REGISTRY=FeatureRegistry([FeatureDefinition(name=name,family='financial_exploratory_reference',version='1.0.0',formula=formula,
    required_source=('sealed_api_candidates','reviewed_template_controls','accounting_qa'),lookback='single annual period',
    point_in_time_rule='NON_PIT_DESCRIPTIVE_REFERENCE_ONLY_NOT_AN_INVESTABLE_SNAPSHOT',missing_policy='COMPLETE_CASE_NO_FILL_POSITIVE_DENOMINATORS',
    transform='per-year descriptive cross-section zscore; no future-snapshot inputs',cluster_eligible=True,
    reference='configs/experiments/financial_exploratory_core_v1.json') for name,formula in FORMULAS.items()])


def calculate_core(values):
    missing=sorted(REQUIRED-values.keys())
    if missing:return dict(status='MISSING_INPUTS',values=None,missing=missing)
    if any(type(values[k]) is bool for k in REQUIRED):return dict(status='INVALID_BOOLEAN',values=None)
    try:v={k:Decimal(str(values[k])) for k in REQUIRED}
    except (ValueError,ArithmeticError):return dict(status='INVALID_NUMBER',values=None)
    if any(not x.is_finite() for x in v.values()):return dict(status='NONFINITE',values=None)
    if any(v[k]<=0 for k in ['net_revenue','total_assets','current_liabilities']):return dict(status='NONPOSITIVE_DENOMINATOR',values=None)
    if any(v[k]<0 for k in ['total_liabilities','current_assets']):return dict(status='NEGATIVE_BALANCE_COMPONENT',values=None)
    result=dict(gross_margin=v['gross_profit']/v['net_revenue'],net_margin=v['net_profit']/v['net_revenue'],
        liabilities_to_assets=v['total_liabilities']/v['total_assets'],current_ratio=v['current_assets']/v['current_liabilities'],
        operating_cashflow_to_assets=v['operating_cash_flow']/v['total_assets'],asset_turnover_ending_assets=v['net_revenue']/v['total_assets'])
    result={k:float(x) for k,x in result.items()}
    if any(not math.isfinite(x) for x in result.values()):return dict(status='NONFINITE_FLOAT',values=None)
    return dict(status='EXPLORATORY_RATIOS_CALCULATED',values=result,financial_features_allowed=False,strict_pit_ready=False)
