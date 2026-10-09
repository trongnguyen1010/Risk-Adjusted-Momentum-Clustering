import unittest
from delta_t1.experiments.financial_ttm_valuation import select_price


class PriceGateTests(unittest.TestCase):
    def row(self):
        return dict(ticker='FPT',trade_date='2026-08-28',security_id='ID',exchange='HOSE',
            market_observation_status='OBSERVED_VALID',available_at='2026-08-28T17:00:00+07:00',
            raw_close=73200,adj_close=999)
    def test_close_available_at_not_before_and_raw_basis(self):
        r=self.row()
        self.assertIsNone(select_price([r],'2026-08-28T16:59:00+07:00','FPT','ID')['value'])
        self.assertEqual(select_price([r],'2026-08-28T17:00:00+07:00','FPT','ID')['value'],73200)
        self.assertIsNone(select_price([r],'2026-08-27T17:00:00+07:00','FPT','ID')['value'])
    def test_duplicate_identity_and_naive_decision_fail(self):
        r=self.row()
        self.assertIsNone(select_price([r,r],'2026-08-28T17:00:00+07:00','FPT','ID')['value'])
        self.assertIsNone(select_price([r],'2026-08-28T17:00:00+07:00','FPT','OTHER')['value'])
        with self.assertRaises(ValueError):select_price([r],'2026-08-28T17:00:00','FPT','ID')
