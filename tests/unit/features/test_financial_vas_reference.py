import unittest
from decimal import Decimal
from delta_t1.features.financial_vas_reference import calculate_vas_f_score, calculate_vas_m_score, calculate_reported_valuation, calculate_period_eps, calculate_disclosed_basic_eps, REGISTRY
from delta_t1.features.financial_reference import calculate_f_score


class VasReferenceTests(unittest.TestCase):
    def f_values(self):
        return {('total_assets',0):200,('total_assets',-1):100,('total_assets',-2):100,
            ('net_profit',0):20,('net_profit',-1):10,('operating_cash_flow',0):30,
            ('long_term_debt_including_current_portion',0):30,('long_term_debt_including_current_portion',-1):30,
            ('current_assets',0):80,('current_assets',-1):50,('current_liabilities',0):20,
            ('current_liabilities',-1):20,('parent_common_equity_issuance_verified',0):0,
            ('gross_profit',0):120,('gross_profit',-1):40,('net_revenue',0):300,('net_revenue',-1):100}

    def m_values(self):
        return {(f,o):v for o in [0,-1] for f,v in dict(receivables=20,net_revenue=100,gross_profit=40,
            current_assets=60,net_tangible_ppe=20,total_assets=100,owned_tangible_ppe_depreciation=5,
            selling_expense=5,administrative_expense=5,current_liabilities=30,
            noncurrent_loans_and_finance_leases=10,net_profit=10,operating_cash_flow=10).items()}

    def test_explicit_adaptation_does_not_mutate_or_fill_strict(self):
        values=self.f_values();original=dict(values)
        adapted=calculate_vas_f_score(values)
        self.assertEqual(adapted['value'],8)
        self.assertEqual(calculate_f_score(values)['known_signals'],6)
        self.assertEqual(values,original)
        self.assertFalse(adapted['strict_original_score'])
        self.assertFalse(adapted['research_ready'])

    def test_missing_profit_stays_missing(self):
        v=self.f_values();del v['net_profit',0]
        self.assertIsNone(calculate_vas_f_score(v)['value'])

    def test_equal_years_hand_calculated_m(self):
        r=calculate_vas_m_score(self.m_values(),'GROSS_SHORT_TERM_TRADE')
        # All seven indices=1; accruals=0. Sum coefficients and intercept by hand.
        self.assertEqual(Decimal(r['value']),Decimal('-2.48'))
        self.assertEqual(Decimal(r['ratios']['ACCRUALS']),0)
        self.assertIsNone(r['classification_threshold'])

    def test_receivables_changes_only_dsr(self):
        v=self.m_values();v['receivables',0]=40
        r=calculate_vas_m_score(v,'ALLOCATION_BOUND_SCENARIO')
        self.assertEqual(Decimal(r['value']),Decimal('-1.56'))

    def test_missing_zero_nonfinite_and_undeclared_basis_fail_closed(self):
        v=self.m_values();del v['net_revenue',0]
        self.assertIsNone(calculate_vas_m_score(v,'GROSS_SHORT_TERM_TRADE')['value'])
        for invalid in [0,-1,True,'NaN']:
            v=self.m_values();v['total_assets',0]=invalid
            self.assertIsNone(calculate_vas_m_score(v,'GROSS_SHORT_TERM_TRADE')['value'])
        self.assertIsNone(calculate_vas_m_score(self.m_values(),'NET_TRADE_ASSUMED')['value'])

    def test_valuation_raw_arithmetic_and_invalid_inputs(self):
        self.assertEqual(calculate_reported_valuation(100,10,1000,20)['pb'],'2')
        for invalid in [0,-1,True,'NaN',None]:
            self.assertIsNone(calculate_reported_valuation(100,invalid,1000,20)['pe'])

    def test_variants_cannot_enter_clustering(self):
        with self.assertRaises(ValueError):REGISTRY.require_cluster_eligible(REGISTRY.names())

    def test_interim_eps_not_annualized_and_unestimated_reserve_not_filled(self):
        r=calculate_period_eps(5054958601533,1703507121,1703507121,6)
        self.assertEqual(r['rounded']['basic'],'2967')
        self.assertFalse(r['annualized'])
        self.assertIsNone(calculate_period_eps(None,10,10,6)['value'])
        self.assertIsNone(calculate_period_eps(100,10,10,True)['value'])

    def test_basic_only_preserves_unknown_dilution_and_normalization(self):
        r = calculate_disclosed_basic_eps(10814923270844, 3582480552, 12)
        self.assertEqual(r['rounded'], '3019')
        self.assertIsNone(r['diluted_eps'])
        self.assertIsNone(r['strict_normalized_eps'])
        self.assertFalse(r['annualized'])
        for bad in [None, True, 0, -1, 'NaN']:
            self.assertIsNone(calculate_disclosed_basic_eps(100, bad, 6)['value'])
