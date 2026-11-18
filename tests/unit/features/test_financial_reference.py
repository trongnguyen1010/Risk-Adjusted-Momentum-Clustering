import unittest
from delta_t1.features.financial_reference import calculate, REGISTRY


class FinancialCalculatorTests(unittest.TestCase):
    def test_missing_or_invalid_input_never_produces_partial_score(self):
        self.assertIsNone(calculate('Z_SCORE',dict(total_assets=100))['value'])
        invalid=dict(eps_adjusted_earnings_numerator=None,weighted_average_basic_shares=3,weighted_average_diluted_shares=3)
        self.assertIsNone(calculate('EPS_RECOMPUTE',invalid)['value'])

    def test_eps_rounding_and_invalid_denominators(self):
        values=dict(eps_adjusted_earnings_numerator=14831,weighted_average_basic_shares=3,weighted_average_diluted_shares=4)
        result=calculate('EPS_RECOMPUTE',values)
        self.assertEqual(result['rounded']['annual_basic_eps_reference'],'4944')
        self.assertEqual(result['rounded']['annual_diluted_eps_reference'],'3708')
        self.assertFalse(result['financial_features_allowed'])
        for denominator in [0,-1]:
            self.assertIsNone(calculate('EPS_RECOMPUTE',dict(values,weighted_average_basic_shares=denominator))['value'])

    def test_z_variant_constant_and_balance_denominators(self):
        values=dict(current_assets=50,current_liabilities=20,total_assets=100,retained_earnings=10,
                    document_reconciled_ebit=10,total_equity=50,total_liabilities=50)
        self.assertEqual(calculate('Z_SCORE',values)['value']['em_z_double_prime_reference'],'7.266')
        self.assertIsNone(calculate('Z_SCORE',dict(values,total_liabilities=0))['value'])
        with self.assertRaises(ValueError):
            REGISTRY.require_cluster_eligible(['em_z_double_prime_reference'])
