import unittest

from delta_t1.m3.engine import Portfolio, rebalance, run
from delta_t1.m3.ranking import combined_scores, n_select, percentiles, select_top
from delta_t1.m3.prices import PriceBook, repair_ratio_glitches
from delta_t1.m3.universe import (allowed_clusters, candidate_universe, cluster_order, financial_state,
                                  leading_cluster, stale_after)


def prices(table):
    return lambda t, d: table.get(d, {}).get(t)


ALWAYS = lambda t, d, side: True  # noqa: E731


class SelectionTests(unittest.TestCase):
    def test_ceil_30_percent(self):
        self.assertEqual([n_select(n) for n in (8, 10, 11, 15, 20, 0, 1)], [3, 3, 4, 5, 6, 0, 1])

    def test_percentiles_ties_and_missing(self):
        p = percentiles({'a': 1, 'b': 2, 'c': 2, 'd': None, 'e': 3})
        self.assertEqual((p['a'], p['b'], p['c'], p['d'], p['e']), (0.0, 0.5, 0.5, None, 1.0))

    def test_combined_score_and_tie_rule_stable(self):
        rows = {'A': dict(m=3, risk=1, roe=0.2), 'B': dict(m=2, risk=2, roe=0.3), 'C': dict(m=1, risk=3, roe=None),
                'D': dict(m=1, risk=3, roe=None)}
        s = combined_scores(rows, {'m': True, 'risk': False}, {'roe': True})
        self.assertNotIn('C', s)  # every financial criterion missing → excluded
        self.assertEqual(s['A']['s_market'], 1.0)
        picks = select_top({'X': 0.5, 'Y': 0.5, 'Z': 0.1}, tiebreak={'X': 1.0, 'Y': 2.0})
        self.assertEqual(picks, [('Y', 1, 1.0)])
        shuffled = select_top({'Z': 0.1, 'Y': 0.5, 'X': 0.5}, tiebreak={'Y': 2.0, 'X': 1.0})
        self.assertEqual(picks, shuffled)

    def test_leading_cluster_by_profile_not_label(self):
        members = [(0, dict(mom_126=0.5, mdd_126=-0.1)), (0, dict(mom_126=0.4, mdd_126=-0.2)),
                   (1, dict(mom_126=0.1, mdd_126=-0.05)), (2, dict(mom_126=-0.2, mdd_126=-0.3))]
        self.assertEqual(leading_cluster(members, 'mom_126', 'mdd_126')[0], 0)
        tie = [(0, dict(k=1.0, d=2.0)), (1, dict(k=1.0, d=1.0))]
        self.assertEqual(leading_cluster(tie, 'k', 'd', higher_tiebreak=False)[0], 1)
        self.assertIsNone(leading_cluster([(0, dict(k=1, d=1)), (1, dict(k=1, d=1))], 'k', 'd')[0])


class PitTests(unittest.TestCase):
    AV = {('AAA', 2022): dict(usable_from_date='2023-03-13'), ('AAA', 2023): dict(usable_from_date='2024-03-11')}

    def test_future_report_never_used(self):
        self.assertEqual(financial_state('AAA', '2024-03-08', self.AV, [2022, 2023]), (2022, None))
        self.assertEqual(financial_state('AAA', '2024-03-11', self.AV, [2022, 2023]), (2023, None))
        self.assertEqual(financial_state('AAA', '2023-03-10', self.AV, [2022, 2023])[1], 'FINANCIAL_NOT_AVAILABLE')

    def test_staleness(self):
        self.assertEqual(stale_after(2022), '2024-06-30')
        self.assertEqual(financial_state('AAA', '2024-07-31', {('AAA', 2022): self.AV[('AAA', 2022)]}, [2022])[1],
                         'FINANCIAL_STALE')

    def test_candidate_universe_is_intersection_with_reasons(self):
        market = [dict(ticker=t, cluster=c, liquidity=l, features=dict(mom_126=m, mdd_126=-0.1))
                  for t, c, l, m in [('AAA', 0, 'LIQUID', 0.5), ('BBB', 0, 'LIQUID', 0.6), ('CCC', 1, 'LIQUID', 0.0),
                                     ('DDD', 0, 'ILLIQUID', 0.9), ('VCB', 0, 'LIQUID', 0.5)]]
        av = {(t, 2023): dict(usable_from_date='2024-03-11') for t in ('AAA', 'BBB', 'CCC', 'DDD')}
        fin = {2023: {'AAA': (1, {}), 'BBB': (2, {}), 'CCC': (1, {}), 'DDD': (1, {})}}
        cands, audit, lead = candidate_universe(market, '2024-04-26', fin, av, {'VCB': 'BANK'}, {2023: 1})
        self.assertEqual(lead, {0})
        self.assertEqual([c['ticker'] for c in cands], ['AAA'])
        reasons = {a['ticker']: a['reason'] for a in audit}
        self.assertEqual(reasons, dict(AAA='', BBB='FINANCIAL_NOT_IN_LEADING_CLUSTER', CCC='MARKET_NOT_IN_LEADING_CLUSTER',
                                       DDD='MARKET_ILLIQUID', VCB='FINANCIAL_SECTOR_NO_B'))
        self.assertTrue(all(a['combined'] == (a['market_eligible'] and a['financial_eligible']) for a in audit))


class EngineTests(unittest.TestCase):
    def test_first_period_buys_from_cash_and_nav_moves_with_prices(self):
        px = prices({'d1': dict(A=10, B=20), 'd2': dict(A=11, B=18)})
        out = run([('d0', 'd1', dict(A=0.5, B=0.5))], px, ALWAYS, end_date='d2')
        self.assertAlmostEqual(out['nav'][-1][1], 0.5 * 1.1 + 0.5 * 0.9)
        self.assertEqual({r['side'] for r in out['ledger']}, {'BUY'})

    def test_drifted_weights_not_reset_and_diff_on_union(self):
        px = prices({'d1': dict(A=10, B=10, C=10), 'd2': dict(A=12, B=8, C=10)})
        out = run([('d0', 'd1', dict(A=0.5, B=0.5)), ('d1x', 'd2', dict(A=0.5, C=0.5))], px, ALWAYS)
        second = {r['ticker']: r for r in out['ledger'] if r['date'] == 'd2'}
        self.assertAlmostEqual(second['A']['pre_weight'], 0.6)  # 6 / 10 after drift, not 0.5
        self.assertEqual((second['A']['side'], second['B']['side'], second['C']['side']), ('SELL', 'SELL', 'BUY'))
        self.assertAlmostEqual(second['B']['target_weight'], 0.0)  # left the target → sold entirely

    def test_hold_only_when_equal(self):
        pf = Portfolio(cash=0.5, values=dict(A=0.5), marks=dict(A=1.0))
        ledger, turnover = rebalance(pf, dict(A=0.5), 'd', lambda t, d: 1.0, ALWAYS)
        self.assertEqual([r['side'] for r in ledger], ['HOLD'])
        self.assertEqual(turnover, 0.0)

    def test_buy_failed_keeps_cash_and_is_not_redistributed(self):
        pf = Portfolio()
        ledger, _ = rebalance(pf, dict(A=0.5, B=0.5), 'd', lambda t, d: 1.0, lambda t, d, s: t != 'B')
        self.assertAlmostEqual(pf.values['A'], 0.5)
        self.assertAlmostEqual(pf.cash, 0.5)
        self.assertEqual({r['ticker']: r['status'] for r in ledger}, dict(A='EXECUTED', B='BUY_FAILED'))

    def test_sell_failed_triggers_proportional_scaling(self):
        pf = Portfolio(cash=0.0, values=dict(A=0.5, B=0.5), marks=dict(A=1.0, B=1.0))
        target = dict(C=0.5, D=0.25, B=0.25)  # sell A (fails) and part of B (ok) → 0.25 cash for 0.75 of buys
        ledger, turnover = rebalance(pf, target, 'd', lambda t, d: 1.0, lambda t, d, s: not (t == 'A' and s == 'SELL'))
        rows = {r['ticker']: r for r in ledger}
        self.assertEqual(rows['A']['status'], 'SELL_FAILED')
        self.assertAlmostEqual(rows['C']['scale'], 0.25 / 0.75)
        self.assertAlmostEqual(pf.values['C'], 0.5 / 3)
        self.assertAlmostEqual(pf.values['D'], 0.25 / 3)
        self.assertAlmostEqual(pf.values['A'], 0.5)
        self.assertAlmostEqual(pf.cash, 0.0)
        self.assertAlmostEqual(turnover, (0.25 + 0.25) / 2)

    def test_weights_sum_to_one_and_no_negative(self):
        px = prices({d: dict(A=10 + i, B=10 - i, C=10) for i, d in enumerate(['d1', 'd2', 'd3'])})
        sched = [('d0', 'd1', dict(A=1 / 3, B=1 / 3, C=1 / 3)), ('d1x', 'd2', dict(A=0.5, B=0.5)),
                 ('d2x', 'd3', dict(C=1.0))]
        out = run(sched, px, ALWAYS)
        for date in ('d1', 'd2', 'd3'):
            ws = [h['weight'] for h in out['holdings'] if h['date'] == date]
            self.assertAlmostEqual(sum(ws), 1.0)
            self.assertTrue(all(w >= -1e-12 for w in ws))

    def test_missing_price_is_stale_not_forward_filled_into_returns(self):
        px = prices({'d1': dict(A=10), 'd2': dict(), 'd3': dict(A=12)})
        out = run([('d0', 'd1', dict(A=1.0)), ('d1x', 'd2', dict(A=1.0))], px, ALWAYS, end_date='d3')
        self.assertIn(('d2', 'A'), out['stale'])
        self.assertAlmostEqual(out['nav'][-1][1], 1.2)

    def test_callable_target_keeps_book_when_universe_too_small(self):
        px = prices({'d1': dict(A=10, B=10), 'd2': dict(A=20, B=10)})
        keep = lambda pre: {t: w for t, w in pre.items() if t != 'CASH'}  # noqa: E731
        out = run([('d0', 'd1', dict(A=0.5, B=0.5)), ('d1x', 'd2', keep)], px, ALWAYS)
        self.assertEqual(out['turnover'][-1][1], 0.0)

    def test_execution_must_follow_decision(self):
        with self.assertRaises(AssertionError):
            run([('d1', 'd1', dict(A=1.0))], prices({'d1': dict(A=1)}), ALWAYS)


class RuleVariantTests(unittest.TestCase):
    def test_cluster_order_and_allowed_sets(self):
        members = [(0, dict(k=0.1, d=1)), (1, dict(k=0.5, d=1)), (2, dict(k=0.3, d=1))]
        order = cluster_order(members, 'k', 'd')
        self.assertEqual(order, [1, 2, 0])
        self.assertEqual(allowed_clusters(order, 'leading'), {1})
        self.assertEqual(allowed_clusters(order, 'top2'), {1, 2})
        self.assertEqual(allowed_clusters(order, 'not_weakest'), {1, 2})
        self.assertIsNone(allowed_clusters([], 'leading'))

    def test_one_sided_scores(self):
        rows = {'A': dict(m=1, roe=None), 'B': dict(m=2, roe=None)}
        s = combined_scores(rows, {'m': True}, {})
        self.assertEqual((s['A']['score'], s['B']['score']), (0.0, 1.0))
        f = combined_scores({'A': dict(roe=0.1), 'B': dict(roe=0.2)}, {}, {'roe': True})
        self.assertEqual(f['B']['score'], 1.0)


class PriceTests(unittest.TestCase):
    def test_one_session_adj_glitch_is_repaired(self):
        rows = [('d1', 123.0, 146.0), ('d2', 111.3, 145.5), ('d3', 123.1, 146.2)]  # FPT 03/02/2025 pattern
        fixed = repair_ratio_glitches(rows)
        self.assertEqual(fixed['d2'][1], 'ADJ_GLITCH_REPAIRED')
        self.assertAlmostEqual(fixed['d2'][0], 145.5 * 123.1 / 146.2)
        self.assertIsNone(fixed['d1'][1])

    def test_real_corporate_action_is_not_touched(self):
        rows = [('d1', 100.0, 100.0), ('d2', 100.0, 85.0), ('d3', 100.0, 85.0)]  # ratio steps and stays
        self.assertTrue(all(flag is None for _, flag in repair_ratio_glitches(rows).values()))

    def test_limit_close_blocks_the_matching_side(self):
        book = PriceBook.__new__(PriceBook)
        book.adj = {('A', 'd'): 10.0, ('B', 'd'): 10.0, ('C', 'd'): 10.0}
        book.volume = {('A', 'd'): 100, ('B', 'd'): 100, ('C', 'd'): 0}
        book.limits = {('A', 'd'): (10.7, 10.7, 9.3), ('B', 'd'): (9.3, 10.7, 9.3)}
        self.assertFalse(book.tradable('A', 'd', 'BUY'))
        self.assertTrue(book.tradable('A', 'd', 'SELL'))
        self.assertFalse(book.tradable('B', 'd', 'SELL'))
        self.assertFalse(book.tradable('C', 'd', 'BUY'))  # zero volume


class PlanV51ExampleTests(unittest.TestCase):
    """The three-period worked example of the team's M3 plan V5.1 (§16.1), reproduced number by number."""

    PRICES = {
        '2024-02-01': dict(FPT=100, HPG=50, VCB=80),
        '2024-03-01': dict(FPT=108, HPG=48, VCB=84.8, MWG=42, VNM=70, SSI=30),
        '2024-04-01': dict(FPT=112.32, HPG=50, VCB=76.32, MWG=47.04, VNM=71.4, SSI=28.2),
        '2024-05-02': dict(FPT=112.32 * 1.03, VCB=76.32 * 1.05, MWG=47.04 * 0.92),
    }
    BLOCKED = {('MWG', '2024-02-01', 'BUY'), ('VCB', '2024-03-01', 'SELL'), ('HPG', '2024-04-01', 'BUY')}

    def setUp(self):
        q = 0.25
        schedule = [('2024-01-31', '2024-02-01', dict(FPT=q, HPG=q, MWG=q, VCB=q)),
                    ('2024-02-29', '2024-03-01', dict(FPT=q, MWG=q, VNM=q, SSI=q)),
                    ('2024-03-29', '2024-04-01', dict(FPT=q, VCB=q, MWG=q, HPG=q))]
        self.out = run(schedule, prices(self.PRICES), lambda t, d, s: (t, d, s) not in self.BLOCKED, end_date='2024-05-02')

    def test_nav_path(self):
        navs = [round(v * 100, 6) for _, v in self.out['nav']]
        self.assertEqual(navs, [100.0, 102.5, 102.218333, 102.218333])

    def test_turnover_is_half_of_v51_gross_turnover(self):
        # V5.1 reports gross executed value / NAV (0.75, 0.739024, 0.415381); M3_PLAN Q13 uses one-way (÷ 2).
        got = [round(t * 2, 6) for _, t in self.out['turnover']]
        self.assertEqual(got, [0.75, 0.739024, 0.415381])

    def test_period_two_scaling_and_forced_hold(self):
        rows = {r['ticker']: r for r in self.out['ledger'] if r['date'] == '2024-03-01'}
        self.assertEqual(rows['VCB']['status'], 'SELL_FAILED')
        self.assertAlmostEqual(rows['MWG']['scale'], 50.375 / 76.875, places=6)
        self.assertAlmostEqual(rows['MWG']['executed'] * 100, 16.791667, places=5)

    def test_period_three_weights(self):
        w = {h['ticker']: h['weight'] for h in self.out['holdings'] if h['date'] == '2024-04-01'}
        for t in ('FPT', 'VCB', 'MWG', 'CASH'):
            self.assertAlmostEqual(w[t], 0.25, places=6)
        self.assertNotIn('HPG', w)


if __name__ == '__main__':
    unittest.main()
