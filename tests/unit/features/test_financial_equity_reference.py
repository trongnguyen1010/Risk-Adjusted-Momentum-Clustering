import copy
import unittest
from decimal import Decimal
from delta_t1.features.financial_equity_reference import REGISTRY, gross_capital_bridge


class EquityBridgeTests(unittest.TestCase):
    def setUp(self):
        evidence = dict(usable_from_date='2026-08-24', validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED')
        self.snapshot = dict(symbol='FPT', balance_date='2026-06-30', parent_equity=100000,
                             reported_common_shares=100, evidence=evidence)
        self.event = dict(symbol='FPT', currency='VND', registration_effective_date='2026-07-16',
                          cash_treatment='BALANCE_CLASSIFICATION_NOT_SEPARATELY_DISCLOSED',
                          before_common_shares=100, after_common_shares=110, new_common_shares=10,
                          issue_price=1000, gross_bank_proceeds=10000, registered_capital_increase=10000,
                          actual_issuance_fee=None, evidence=[evidence])

    def calculate(self, day='2026-08-28', **event):
        return gross_capital_bridge(self.snapshot, dict(self.event, **event), 2000, 110, day)

    def test_unknown_cash_classification_and_fees_are_not_zero(self):
        result = self.calculate()
        self.assertEqual(Decimal(result['value']), Decimal(2))
        self.assertEqual(result['gross_bridge_parent_equity'], '110000')
        for key in ['gross_assets_change', 'gross_liabilities_change', 'actual_issuance_fee', 'strict_event_adjusted_pb']:
            self.assertIsNone(result[key])
        self.assertFalse(result['includes_subsequent_operating_results'])

    def test_verified_advance_converts_liability_without_double_cash(self):
        result = self.calculate(cash_treatment='VERIFIED_ADVANCE_LIABILITY_AT_BALANCE',
                                advance_balance_date='2026-06-30', verified_advance_liability=10000)
        self.assertEqual(result['gross_assets_change'], '0')
        self.assertEqual(result['gross_liabilities_change'], '-10000')
        self.assertEqual(result['gross_equity_change'], '10000')

    def test_late_publication_blocks_even_if_registration_occurred(self):
        self.assertIsNone(self.calculate(day='2026-08-21')['value'])
        self.assertEqual(self.calculate(day='2026-08-21')['status'], 'EVIDENCE_NOT_YET_USABLE')

    def test_share_price_cash_and_capital_must_reconcile(self):
        for change in [dict(gross_bank_proceeds=9999), dict(registered_capital_increase=9999),
                       dict(after_common_shares=109), dict(currency='USD'), dict(actual_issuance_fee=0)]:
            with self.subTest(change=change):
                self.assertIsNone(self.calculate(**change)['value'])

    def test_advance_requires_exact_balance_and_amount(self):
        self.assertIsNone(self.calculate(cash_treatment='VERIFIED_ADVANCE_LIABILITY_AT_BALANCE',
                                        advance_balance_date='2025-12-31', verified_advance_liability=10000)['value'])

    def test_no_future_effective_date_or_pre_balance_conversion(self):
        for effective in ['2026-08-29', '2026-06-29']:
            self.assertIsNone(self.calculate(registration_effective_date=effective)['value'])

    def test_fractional_outstanding_shares_not_accepted(self):
        self.assertIsNone(self.calculate(new_common_shares='10.5', gross_bank_proceeds=10500,
                                        registered_capital_increase=10500)['value'])

    def test_inputs_remain_unchanged_and_registry_closed(self):
        before = copy.deepcopy((self.snapshot, self.event))
        self.calculate()
        self.assertEqual(before, (self.snapshot, self.event))
        self.assertEqual(REGISTRY.names(cluster_eligible=True), ())
