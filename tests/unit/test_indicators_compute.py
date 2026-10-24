import math
import unittest

from delta_t1.indicators import compute as c


def regular(scale=1.0, **override):
    row = dict(common_share_capital_amount=1_000_000_000 * 10_000, paid_in_capital_amount=1_000_000_000 * 10_000,
               parent_net_profit=2_000e9 * scale, net_profit=2_200e9 * scale, noncontrolling_profit=200e9 * scale,
               total_equity=12_000e9 * scale, noncontrolling_interests=2_000e9, total_assets=30_000e9 * scale,
               total_liabilities=18_000e9 * scale, net_revenue=20_000e9 * scale, gross_profit=6_000e9 * scale,
               current_assets=15_000e9 * scale, current_liabilities=10_000e9, operating_cash_flow=2_500e9 * scale,
               noncurrent_loans_and_finance_leases=3_000e9, receivables=4_000e9 * scale,
               net_tangible_ppe=8_000e9 * scale, aggregate_fixed_property_depreciation_amortization=800e9 * scale,
               selling_expense=1_000e9 * scale, administrative_expense=1_000e9 * scale,
               retained_earnings=5_000e9 * scale, profit_before_tax=2_700e9 * scale, interest_expense=300e9 * scale)
    row.update(override)
    return row


ROWS = {2023: regular(0.8), 2024: regular(0.9), 2025: regular(1.0)}
PRICES = {2024: 25_000.0, 2025: 30_000.0}


class ComputeTest(unittest.TestCase):
    def setUp(self):
        self.y = c.compute_year(ROWS, PRICES, 2025, 'NON_FINANCIAL')

    def test_valuation_uses_par_value_shares_and_year_end_price(self):
        self.assertEqual(self.y['shares']['value'], 1e9)
        self.assertAlmostEqual(self.y['eps']['value'], 2_000.0)
        self.assertAlmostEqual(self.y['bvps']['value'], 10_000.0)  # (12000 - 2000) bn / 1bn shares
        self.assertAlmostEqual(self.y['pe']['value'], 15.0)
        self.assertAlmostEqual(self.y['pb']['value'], 3.0)
        self.assertAlmostEqual(self.y['market_cap']['value'], 30_000e9)
        self.assertEqual(self.y['eps']['inputs']['parent_net_profit@t'], 2_000e9)

    def test_profitability_uses_average_balances(self):
        eq_p = 12_000e9 * 0.9 - 2_000e9
        self.assertAlmostEqual(self.y['roe']['value'], 2_000e9 / ((10_000e9 + eq_p) / 2))
        self.assertAlmostEqual(self.y['roa']['value'], 2_200e9 / ((30_000e9 + 27_000e9) / 2))
        self.assertAlmostEqual(self.y['gross_margin']['value'], 0.3)
        self.assertAlmostEqual(self.y['revenue_growth']['value'], 1 / 0.9 - 1)
        self.assertAlmostEqual(self.y['profit_growth']['value'], 1 / 0.9 - 1)
        self.assertAlmostEqual(self.y['debt_to_equity']['value'], 1.5)
        self.assertAlmostEqual(self.y['current_ratio']['value'], 1.5)

    def test_f_score_full_signals(self):
        f = self.y['f_score']
        self.assertEqual(f['status'], c.OK)
        self.assertEqual(f['inputs']['known_signals'], 9)
        signals = f['inputs']['signals']
        self.assertTrue(signals['roa_positive'] and signals['cfo_positive'] and signals['accruals'])
        self.assertTrue(signals['liquidity_improving'] and signals['no_dilution'])
        self.assertFalse(signals['gross_margin_improving'])  # margin unchanged across years
        self.assertEqual(f['value'], float(sum(bool(v) for v in signals.values())))

    def test_f_score_missing_signal_keeps_partial_signals(self):
        rows = {2024: regular(0.9), 2025: regular(1.0)}  # no 2023: prior ROA unknown
        f = c.compute_year(rows, PRICES, 2025, 'NON_FINANCIAL')['f_score']
        self.assertIsNone(f['value'])
        self.assertEqual(f['status'], c.MISSING_INPUT)
        self.assertEqual(f['inputs']['known_signals'], 8)
        self.assertIn('roa_improving', f['inputs']['missing'])

    def test_m_and_z_scores(self):
        m = self.y['m_score']
        v = m['inputs']['variables']
        self.assertAlmostEqual(v['SGI'], 1 / 0.9)
        self.assertAlmostEqual(v['DSRI'], 1.0)
        self.assertAlmostEqual(v['TATA'], (2_200e9 - 2_500e9) / 30_000e9)
        expected = c.M_COEFFICIENTS['intercept'] + sum(c.M_COEFFICIENTS[k] * x for k, x in v.items())
        self.assertAlmostEqual(m['value'], expected)
        z = self.y['z_score']
        x = z['inputs']['variables']
        self.assertAlmostEqual(x['X3'], 3_000e9 / 30_000e9)  # EBIT = PBT + interest
        self.assertAlmostEqual(x['X4'], 30_000e9 / 18_000e9)
        self.assertAlmostEqual(z['value'], sum(c.Z_COEFFICIENTS[k] * x[k] for k in c.Z_COEFFICIENTS))
        self.assertEqual(self.y['z_score_dp']['inputs']['variant'], 'Z_DOUBLE_PRIME')

    def test_m_score_depreciation_falls_back_to_accumulated_change(self):
        dep = 'aggregate_fixed_property_depreciation_amortization'
        acc = c.ACCUMULATED_DEPRECIATION
        rows = {y: {k: val for k, val in regular(s, **{acc: -a}).items() if k != dep}
                for y, s, a in ((2023, 0.8, 4_000e9), (2024, 0.9, 4_720e9), (2025, 1.0, 5_520e9))}
        m = c.compute_year(rows, PRICES, 2025, 'NON_FINANCIAL')['m_score']
        self.assertEqual(m['status'], c.OK)
        self.assertIn('DEP_FROM_ACCUMULATED_DEPRECIATION:t', m['inputs']['flags'])
        self.assertIn('DEP_FROM_ACCUMULATED_DEPRECIATION:p', m['inputs']['flags'])
        ppe_t, ppe_p = 8_000e9, 7_200e9
        expected = (720e9 / (720e9 + ppe_p)) / (800e9 / (800e9 + ppe_t))
        self.assertAlmostEqual(m['inputs']['variables']['DEPI'], expected)
        rows[2023].pop(acc)  # no prior accumulated depreciation -> no fallback for p
        self.assertEqual(c.compute_year(rows, PRICES, 2025, 'NON_FINANCIAL')['m_score']['status'], c.MISSING_INPUT)

    def test_missing_price_and_negative_earnings(self):
        rows = {**ROWS, 2025: regular(1.0, parent_net_profit=-500e9)}
        y = c.compute_year(rows, {}, 2025, 'NON_FINANCIAL')
        self.assertEqual(y['pe']['status'], c.NEGATIVE_EARNINGS)
        self.assertEqual(y['pb']['status'], c.NO_PRICE)
        self.assertEqual(y['market_cap']['status'], c.NO_PRICE)
        self.assertEqual(y['z_score']['status'], c.NO_PRICE)
        self.assertEqual(y['z_score_dp']['status'], c.OK)  # book-value variant needs no price
        self.assertAlmostEqual(y['eps']['value'], -500.0)

    def test_nulls_propagate_and_zero_denominators(self):
        row = regular(1.0, net_revenue=0.0, interest_expense=None)
        row.pop('common_share_capital_amount')
        row.pop('paid_in_capital_amount')
        y = c.compute_year({2025: row}, PRICES, 2025, 'NON_FINANCIAL')
        for metric in ('eps', 'bvps', 'pe', 'pb', 'market_cap', 'gross_margin', 'revenue_growth', 'z_score'):
            self.assertEqual(y[metric]['status'], c.MISSING_INPUT, metric)
            self.assertIsNone(y[metric]['value'])
        self.assertIn('ZERO_DENOMINATOR', y['gross_margin']['inputs']['missing'])
        self.assertIn('AVG_CURRENT_ONLY:total_assets', y['roa']['inputs']['flags'])  # no 2024 row: no forward fill
        self.assertEqual(y['profit_growth']['status'], c.MISSING_INPUT)

    def test_parent_fallbacks_are_flagged(self):
        row = regular(1.0)
        row.pop('parent_net_profit')
        row.pop('noncontrolling_interests')
        y = c.compute_year({2025: row}, PRICES, 2025, 'NON_FINANCIAL')
        self.assertAlmostEqual(y['eps']['value'], 2_000.0)
        self.assertIn('PARENT_NI_FROM_NET_MINUS_NCI', y['eps']['inputs']['flags'])
        self.assertIn('NCI_ASSUMED_ZERO', y['bvps']['inputs']['flags'])

    def test_bank_gets_valuation_but_scores_not_applicable(self):
        y = c.compute_year(ROWS, PRICES, 2025, 'BANK')
        self.assertEqual(y['pe']['status'], c.OK)
        self.assertEqual(y['roa']['status'], c.OK)
        for metric in ('f_score', 'm_score', 'z_score', 'z_score_dp', 'gross_margin', 'current_ratio'):
            self.assertEqual(y[metric]['status'], c.NOT_APPLICABLE, metric)
        empty = c.compute_year({}, {}, 2025, 'BANK')
        self.assertEqual(empty['f_score']['status'], c.NOT_APPLICABLE)
        self.assertEqual(empty['eps']['status'], c.MISSING_INPUT)
        self.assertEqual(empty['eps']['inputs']['missing'], ['NO_ANNUAL_REPORT'])

    def test_every_metric_has_a_cell(self):
        cells = c.compute_ticker({}, {}, 'NON_FINANCIAL')
        self.assertEqual(sorted(cells), list(range(2016, 2026)))
        self.assertTrue(all(set(m) == set(c.METRICS) for m in cells.values()))
        self.assertTrue(all(not math.isnan(v['value']) for m in [self.y] for v in m.values() if v['value'] is not None))

    def test_ratings(self):
        self.assertEqual(c.f_rating(7), 'STRONG')
        self.assertEqual(c.f_rating(4), 'AVERAGE')
        self.assertEqual(c.f_rating(3), 'WEAK')
        self.assertEqual(c.z_zone(1.5), 'DISTRESS')
        self.assertEqual(c.z_zone(2.5), 'GREY')
        self.assertEqual(c.z_zone(3.5), 'SAFE')
        self.assertEqual(c.m_flag(-1.0), 'LIKELY_MANIPULATOR')
        self.assertEqual(c.m_flag(-2.5), 'NORMAL')


if __name__ == '__main__':
    unittest.main()
