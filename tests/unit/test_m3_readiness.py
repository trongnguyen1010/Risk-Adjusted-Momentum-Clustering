"""M3 readiness changes (ADR D-M3-01): config-driven staleness, N_min after FINANCIAL_CRITERIA_MISSING, audit rows,
B-PIT cutoff/fit rules."""
import importlib.util
import unittest

import numpy as np

from delta_t1.m3 import bpit
from delta_t1.m3.strategies import AUDIT_KEYS, Strategies
from delta_t1.m3.universe import financial_state, stale_after

SKLEARN = importlib.util.find_spec('sklearn') is not None


def config(**kw):
    cfg = dict(financial_rule='not_weakest', market_rule='leading', n_min=3, top_share=0.3, stale_months=18,
               combined_weight_market=0.5, market_criteria={'mom_126': True}, financial_criteria={'roe': True})
    cfg.update(kw)
    return cfg


def market_row(ticker, cluster, mom, liquidity='LIQUID'):
    return dict(ticker=ticker, cluster=cluster, liquidity=liquidity,
                features=dict(mom_126=mom, mdd_126=-0.1, liquidity_21=1.0))


class StalenessFromConfigTests(unittest.TestCase):
    def test_stale_months_parameter(self):
        self.assertEqual(stale_after(2022, 12), '2023-12-30')
        av = {('AAA', 2022): dict(usable_from_date='2023-03-13')}
        self.assertEqual(financial_state('AAA', '2024-01-31', av, [2022], stale_months=12)[1], 'FINANCIAL_STALE')
        self.assertEqual(financial_state('AAA', '2024-01-31', av, [2022], stale_months=18), (2022, None))


class StrategyReadinessTests(unittest.TestCase):
    def setUp(self):
        tickers = ['A', 'B', 'C', 'D', 'E']
        self.market = {'2024-04-26': [market_row(t, 0, 0.5 + i / 10) for i, t in enumerate(tickers)]
                       + [market_row('Z', 1, -0.5), market_row('ILL', 0, 0.9, 'ILLIQUID')]}
        self.fin = {2023: {t: (0, {}) for t in tickers + ['Z', 'ILL']}}
        self.avail = {(t, 2023): dict(usable_from_date='2024-03-11') for t in tickers + ['Z', 'ILL']}
        self.order = {2023: [0, 1]}  # frozen B-PIT order: cluster 0 best, 1 weakest

    def strategies(self, ind, **kw):
        return Strategies(config(**kw), self.market, self.fin, self.avail, {}, ind, fin_order=self.order)

    def test_n_min_counts_after_financial_criteria_missing(self):
        ind = {('A', 2023): dict(roe=0.1), ('B', 2023): dict(roe=0.2), ('C', 2023): dict(roe=None),
               ('D', 2023): {}, ('E', 2023): dict(roe=0.3)}
        res = self.strategies(ind, n_min=4).combined('2024-04-26')
        self.assertEqual(res['status'], 'UNIVERSE_TOO_SMALL')  # 5 eligible, 2 missing every FC → N = 3 < 4
        self.assertEqual(res['candidates'], 3)
        reasons = {a['ticker']: a['reason'] for a in res['audit']}
        self.assertEqual(reasons['C'], 'FINANCIAL_CRITERIA_MISSING')
        self.assertEqual(reasons['ILL'], 'MARKET_ILLIQUID')
        self.assertTrue(all(set(a) == set(AUDIT_KEYS) for a in res['audit']))

    def test_ok_universe_and_frozen_order_used(self):
        ind = {(t, 2023): dict(roe=r) for t, r in zip('ABCDE', (0.1, 0.2, 0.3, 0.4, 0.5))}
        s = self.strategies(ind)
        self.assertEqual(s.allowed_fin, {2023: {0}})
        res = s.combined('2024-04-26')
        self.assertEqual(res['status'], 'OK')
        self.assertEqual(res['candidates'], 5)
        self.assertEqual(len(res['picks']), 2)  # ceil(0.3 × 5)

    def test_one_sided_and_partial_missing_flags(self):
        ind = {(t, 2023): dict(roe=0.1) for t in 'ABCDE'}
        res = self.strategies(ind, financial_criteria={'roe': True, 'f_score': True}).financial_only('2024-04-26')
        flags = {a['ticker']: a['flags'] for a in res['audit']}
        self.assertEqual(flags['A'], 'FC_MISSING:f_score')

    def test_empty_universe_no_division_by_zero(self):
        s = Strategies(config(), {'d': [market_row('X', 0, None, 'ILLIQUID')]}, {}, {}, {}, {}, fin_order={})
        self.assertEqual(s.equal_weight('d')['status'], 'NO_CANDIDATES')
        self.assertEqual(s.momentum_only('d')['target'], {})


class BPitTests(unittest.TestCase):
    def test_cutoff_rule(self):
        self.assertEqual(bpit.cutoff_for(2023, ['2024-03-11', '2024-05-20', '']), '2024-04-30')
        self.assertEqual(bpit.cutoff_for(2020, ['2021-07-01', '2021-07-01']), '2021-07-01')  # LAG_RULE year
        self.assertEqual(bpit.cutoff_for(2020, []), '2021-04-30')

    def test_fit_leak_audit(self):
        self.assertEqual(bpit.fit_leaks(['2024-03-01', '2024-06-01', ''], [True, True, True], '2024-04-30'), [1, 2])

    @unittest.skipUnless(SKLEARN, 'scikit-learn not installed')
    def test_build_year_fits_only_reports_usable_at_cutoff(self):
        rng = np.random.default_rng(0)
        centers = np.array([[0.25, 0.1, 0.3, 0.2, 0.3, 2.0, 1.0, 0.2, 1.2],
                            [0.05, 0.02, 0.2, 0.05, 1.5, 1.2, 0.8, 0.05, 0.8],
                            [-0.1, -0.05, 0.1, -0.1, 3.0, 0.8, 0.5, -0.2, 0.2]])
        raw = np.vstack([c + rng.normal(0, 0.02, (20, 9)) for c in centers])
        tickers = [f'T{i:02d}' for i in range(len(raw))]
        usable = ['2024-03-15'] * len(raw)
        late = [5, 25, 45]
        for i in late:
            usable[i] = '2024-07-15'
        res = bpit.build_year(2023, tickers, raw, usable)
        self.assertEqual(res['cutoff'], '2024-04-30')
        self.assertEqual(res['n_fit'], 57)
        self.assertFalse(res['fitted'][late].any())
        self.assertEqual(bpit.fit_leaks(usable, res['fitted'], res['cutoff']), [])
        # late reports land in the cluster of their true group; order = high ROE first, weakest last
        groups = [res['labels'][0], res['labels'][20], res['labels'][40]]
        self.assertEqual([res['labels'][i] for i in late], groups)
        self.assertEqual(res['cluster_order'], [int(g) for g in groups])

    @unittest.skipUnless(SKLEARN, 'scikit-learn not installed')
    def test_lag_rule_year_fits_everything(self):
        rng = np.random.default_rng(1)
        raw = rng.normal(0, 1, (30, 9))
        res = bpit.build_year(2020, [str(i) for i in range(30)], raw, ['2021-07-01'] * 30)
        self.assertEqual((res['cutoff'], res['n_fit'], res['n_assigned']), ('2021-07-01', 30, 0))


if __name__ == '__main__':
    unittest.main()
