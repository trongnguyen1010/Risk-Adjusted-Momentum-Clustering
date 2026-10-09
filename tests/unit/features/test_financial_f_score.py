import unittest
from delta_t1.features.financial_reference import calculate_f_score
from delta_t1.ingestion.financial_pilot_readiness import eligible_fact


class FScoreTests(unittest.TestCase):
    def values(self):
        return {('total_assets',0):200,('total_assets',-1):100,('total_assets',-2):100,
            ('income_before_extraordinary_items',0):20,('income_before_extraordinary_items',-1):10,
            ('operating_cash_flow',0):30,('long_term_debt_including_current_portion',0):30,
            ('long_term_debt_including_current_portion',-1):30,('current_assets',0):80,
            ('current_assets',-1):50,('current_liabilities',0):20,('current_liabilities',-1):20,
            ('parent_common_equity_issuance_verified',0):0,('gross_profit',0):120,
            ('gross_profit',-1):40,('net_revenue',0):300,('net_revenue',-1):100}

    def test_full_score_uses_average_assets_and_strict_comparisons(self):
        result=calculate_f_score(self.values())
        self.assertEqual(result['value'],8)  # gross margins equal, strict > is false
        self.assertEqual(result['signals']['reduced_leverage']['value'],1)
        self.assertFalse(result['research_ready'])

    def test_missing_income_keeps_six_signals_without_total_or_proxy(self):
        values={k:v for k,v in self.values().items() if k[0]!='income_before_extraordinary_items'}
        values['net_profit',0]=20
        values['parent_common_equity_issuance_verified',0]=1
        result=calculate_f_score(values)
        self.assertIsNone(result['value'])
        self.assertEqual(result['known_signals'],6)
        self.assertEqual(result['signals']['no_parent_issuance']['value'],0)

    def test_invalid_denominator_and_unknown_issuance_remain_null(self):
        for value in [0,-1,float('nan'),True]:
            values=self.values();values['total_assets',-1]=value
            self.assertIsNone(calculate_f_score(values)['value'])
        values=self.values();values['parent_common_equity_issuance_verified',0]=2
        self.assertIsNone(calculate_f_score(values)['signals']['no_parent_issuance']['value'])

    def test_indicator_requires_explicit_binary_semantics(self):
        fact=dict(year=2024,statement_scope='CONSOLIDATED',validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',
            accounting_framework='VAS',item='parent_common_equity_issuance_verified',value=1,unit='INDICATOR',
            period_start='2024-01-01',period_end='2024-12-31',
            derivation=dict(rule='PARENT_COMMON_ISSUANCE_OCCURRED_VERIFIED'))
        self.assertTrue(eligible_fact(fact))
        for value in [None,True,2,1.0]:
            self.assertFalse(eligible_fact(dict(fact,value=value)))
        self.assertFalse(eligible_fact(dict(fact,derivation={})))
