import math
import unittest

import pandas as pd

from delta_t1.indicators import inputs as ind


def long(rows):
    return pd.DataFrame(rows, columns=['ticker', 'fiscal_year', 'field', 'value', 'provider_type'])


class IndicatorInputsTest(unittest.TestCase):
    def test_provider_priority_prefers_consolidated_audited(self):
        frame = long([('AAA', 2024, 'net_profit', 1.0, 'K'), ('AAA', 2024, 'net_profit', 2.0, 'HK'),
                      ('AAA', 2024, 'total_assets', 5.0, 'N')])
        picked = ind._pick_provider(frame).set_index('field')
        self.assertEqual(picked.loc['net_profit', 'value'], 2.0)
        self.assertEqual(picked.loc['total_assets', 'provider_type'], 'N')

    def test_finance_block_is_shifted_one_row(self):
        frame = long([('FPT', 2024, 'finance_income', 1811.0, 'HK'), ('FPT', 2024, 'finance_expense', 551.0, 'HK'),
                      ('FPT', 2024, 'interest_expense', 392.0, 'HK'), ('FPT', 2024, 'associate_profit', 0.0, 'HK'),
                      ('FPT', 2024, 'net_profit', 9.0, 'HK')])
        out = ind.realign_finance_block(frame).set_index('field')['value']
        self.assertEqual(out['finance_expense'], 1811.0)
        self.assertEqual(out['interest_expense'], 551.0)
        self.assertEqual(out['associate_profit'], 392.0)
        self.assertNotIn('finance_income', out.index)
        self.assertEqual(out['net_profit'], 9.0)

    def test_costs_become_positive_magnitudes(self):
        frame = pd.DataFrame([('A', 2024, 'cost_of_goods_sold', -5.0, 's'), ('A', 2024, 'net_profit', -3.0, 's')],
                             columns=['ticker', 'fiscal_year', 'field', 'value', 'source'])
        out = ind.normalize_signs(frame).set_index('field')['value']
        self.assertEqual(out['cost_of_goods_sold'], 5.0)
        self.assertEqual(out['net_profit'], -3.0)

    def test_financial_gate_drops_placeholders_and_broken_identities(self):
        frame = long([
            # Bank year with consistent balance sheet but zero placeholder revenue.
            ('VCB', 2024, 'total_assets', 100.0, 'HK'), ('VCB', 2024, 'total_liabilities', 90.0, 'HK'),
            ('VCB', 2024, '_equity_ex_nci', 9.0, 'HK'), ('VCB', 2024, 'noncontrolling_interests', 1.0, 'HK'),
            ('VCB', 2024, 'net_revenue', 0.0, 'HK'),
            ('VCB', 2024, 'net_profit', 1e9, 'HK'), ('VCB', 2024, 'parent_net_profit', 0.0, 'HK'),
            ('VCB', 2024, 'noncontrolling_profit', -2e7, 'HK'),
            # Year whose balance sheet does not add up.
            ('VCB', 2023, 'total_assets', 100.0, 'HK'), ('VCB', 2023, 'total_liabilities', 50.0, 'HK'),
            ('VCB', 2023, '_equity_ex_nci', 9.0, 'HK')])
        out, stats = ind.gate_financial(frame)
        got = {(r.fiscal_year, r.field): r.value for r in out.itertuples()}
        self.assertEqual(got[2024, 'total_assets'], 100.0)
        self.assertNotIn((2024, 'net_revenue'), got)
        self.assertNotIn((2024, 'parent_net_profit'), got)
        self.assertEqual(got[2024, 'noncontrolling_profit'], -2e7)  # Blank parent line: minority line kept.
        self.assertNotIn((2023, 'total_assets'), got)
        self.assertEqual(stats['balance_identity_dropped'], 1)
        self.assertEqual(stats['attribution_dropped'], 1)

    def test_checks_flag_without_correcting(self):
        wide = pd.DataFrame([
            dict(ticker='A', fiscal_year=2023, total_assets=100.0, total_liabilities=50.0, total_equity=50.0,
                 net_revenue=10.0, interest_expense=1.0, finance_expense=2.0, cashflow_interest_adjustment=1.0),
            dict(ticker='A', fiscal_year=2024, total_assets=20000.0, total_liabilities=50.0, total_equity=50.0,
                 net_revenue=-1.0, interest_expense=3e9, finance_expense=2e9, cashflow_interest_adjustment=float('nan'))])
        result = ind.run_checks(wide)
        self.assertFalse(result.ticker.isna().any())
        checks = set(result.check)
        self.assertNotIn('UNIT_JUMP_X100:total_equity', checks)
        self.assertIn('BALANCE_IDENTITY', checks)
        self.assertIn('NEGATIVE_NET_REVENUE', checks)
        self.assertIn('INTEREST_EXCEEDS_FINANCE_EXPENSE', checks)
        self.assertIn('UNIT_JUMP_X100:total_assets', checks)
        self.assertEqual(wide.loc[1, 'total_assets'], 20000.0)

    def test_dstock_rejected_when_core_field_fails(self):
        keys = [('A', y) for y in range(2016, 2026)] * 4
        cafef = pd.DataFrame([(t, y + 10 * i, f, 100.0, 'CAFEF:K') for i, (t, y) in enumerate(keys[:40])
                              for f in ind.DSTOCK_QA_FIELDS], columns=['ticker', 'fiscal_year', 'field', 'value', 'source'])
        dstock = cafef.assign(source='DSTOCK')
        dstock.loc[dstock.field == 'net_profit', 'value'] = 150.0
        report = ind.validate_dstock(cafef, dstock).set_index('field')
        self.assertFalse(report.accepted.any())
        self.assertEqual(report.loc['total_assets', 'pass_rate'], 1.0)

    def test_dstock_fills_only_years_cafef_lacks(self):
        cols = ['ticker', 'fiscal_year', 'field', 'value', 'source']
        cafef = pd.DataFrame([('A', 2024, 'total_assets', 100.0, 'CAFEF:HK')], columns=cols)
        dstock = pd.DataFrame([('A', 2024, 'net_profit', 5.0, 'DSTOCK'), ('A', 2023, 'total_assets', 90.0, 'DSTOCK'),
                               ('A', 2023, 'finance_income', 1.0, 'DSTOCK')], columns=cols)
        out = ind.combine([cafef], dstock, {'total_assets', 'net_profit'})
        got = {(r.fiscal_year, r.field): r.source for r in out.itertuples()}
        self.assertEqual(got, {(2024, 'total_assets'): 'CAFEF:HK', (2023, 'total_assets'): 'DSTOCK'})

    def test_labels_normalize_vietnamese(self):
        self.assertEqual(ind.nlabel('TỔNG CỘNG TÀI SẢN'), 'tongcongtaisan')
        self.assertEqual(ind.FINANCIAL_LABELS['KQKD', ind.nlabel('XV. Lợi nhuận sau thuế của cổ đông của Ngân hàng mẹ')],
                         'parent_net_profit')
        self.assertEqual(ind.sector_group('BVH', 'UNKNOWN'), 'INSURANCE')
        self.assertEqual(ind.sector_group('VCB', 'Bank'), 'BANK')
        self.assertTrue(math.isclose(ind.CAFEF_ABSENT, -1.0))


if __name__ == '__main__':
    unittest.main()
