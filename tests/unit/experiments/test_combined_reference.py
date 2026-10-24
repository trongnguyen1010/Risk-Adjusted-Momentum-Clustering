import copy
import json
from pathlib import Path
from statistics import mean
import unittest

from delta_t1.experiments.combined_reference import validate, transform, fit_one_year

ROOT = Path(__file__).resolve().parents[3]


class CombinedReferenceTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/'configs/experiments/combined_reference_v1.json').read_bytes())

    def fixture(self):
        fields = self.config['market_features'] + self.config['financial_features']
        return [dict(snapshot_date='2025-12-31', symbol=f'S{i:03}',
                     **{f: (i//34)*20 + (i%34)*.001 + j for j, f in enumerate(fields)})
                for i in range(102)]

    def test_pending_protocol_cannot_execute(self):
        c = copy.deepcopy(self.config)
        c['owner_approval']['status'] = 'MANUAL_REVIEW_REQUIRED'
        validate(c)
        with self.assertRaisesRegex(ValueError, 'MANUAL_REVIEW_REQUIRED'):
            validate(c, execute=True)

    def test_prohibited_promotions_and_preprocessing_fail_closed(self):
        for key in ['strict_pit_ready', 'research_ready', 'backtest_allowed', 'holdout_claim', 'clipping', 'pca', 'imputation']:
            c = copy.deepcopy(self.config)
            c[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(c)

    def test_equal_blocks_instead_of_more_features_or_currency_dominating(self):
        data = self.fixture()
        matrix, scalers = transform(data, self.config)
        split = len(self.config['market_features'])
        self.assertAlmostEqual(.5, mean(sum(v*v for v in x[:split]) for x in matrix))
        self.assertAlmostEqual(.5, mean(sum(v*v for v in x[split:]) for x in matrix))
        for r in data:
            r['liquidity_21'] *= 1_000_000_000
        again, _ = transform(data, self.config)
        for x, y in zip(matrix, again):
            for a, b in zip(x, y):
                self.assertAlmostEqual(a, b)

    def test_bounded_synthetic_determinism_and_three_clusters(self):
        a = fit_one_year(self.fixture(), self.config)
        b = fit_one_year(self.fixture(), self.config)
        self.assertEqual([34, 34, 34], sorted(p['size'] for p in a['profiles']))
        self.assertEqual([r['combined_cluster_id'] for r in a['assignments']],
                         [r['combined_cluster_id'] for r in b['assignments']])

    def test_missing_duplicate_and_mixed_years_are_rejected(self):
        bad = self.fixture()
        bad[0]['net_margin'] = float('nan')
        with self.assertRaises(ValueError):
            fit_one_year(bad, self.config)
        bad = self.fixture()
        bad[0]['snapshot_date'] = '2024-12-31'
        with self.assertRaises(ValueError):
            fit_one_year(bad, self.config)
        bad = self.fixture()
        bad[0]['symbol'] = bad[1]['symbol']
        with self.assertRaises(ValueError):
            fit_one_year(bad, self.config)
