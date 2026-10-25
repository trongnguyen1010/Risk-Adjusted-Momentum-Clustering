import unittest

import numpy as np

from delta_t1.experiments import clustering_rework_v2 as cr2
from delta_t1.experiments.clustering_rework import Snapshot

CFG = dict(k=[3], seed=42,
           algorithms=dict(kmeans=dict(n_init=5), pca_kmeans=dict(variance=0.8, n_init=5), ward=dict(linkage='ward'),
                           gmm=dict(covariance_type='full', n_init=1, reg_covar=1e-4, max_iter=200)),
           stability=dict(subsample=0.9, seeds=[1, 2]),
           admissible=dict(min_cluster_share=0.05, share_of_snapshots=0.8, median_stability=0.8))
LEVEL = dict(zero_volume_share_gt=0.3, liquidity_21_lt=1e8)


def blobs(seed, n=50):
    rng = np.random.default_rng(seed)
    centers = np.array([[0, 0], [8, 0], [0, 8]])  # every dimension carries cluster signal
    return np.vstack([c + rng.normal(size=(n, 2)) for c in centers])


class LiquidityTests(unittest.TestCase):
    def test_filter_flags_idle_or_thin_trading(self):
        self.assertTrue(cr2.illiquid({'liquidity_21': 5e9}, (0.6, 0.3), LEVEL))   # idle most sessions
        self.assertTrue(cr2.illiquid({'liquidity_21': 5e7}, (0.0, 0.3), LEVEL))   # trades daily but tiny value
        self.assertTrue(cr2.illiquid({'liquidity_21': 5e9}, None, LEVEL))         # < 63 sessions observed
        self.assertTrue(cr2.illiquid({'liquidity_21': 5e9}, (float('nan'), 0.3), LEVEL))
        self.assertFalse(cr2.illiquid({'liquidity_21': 5e9}, (0.1, 0.3), LEVEL))


class SweepTests(unittest.TestCase):
    def setUp(self):
        self.snaps = [Snapshot('B', str(y), [f'T{i}' for i in range(150)], blobs(y), ('a', 'b')) for y in (2024, 2025)]

    def test_all_four_algorithms_recover_clear_clusters(self):
        rows, labels = cr2.sweep(self.snaps, CFG, 'B_test')
        self.assertEqual({r['algo'] for r in rows}, set(cr2.ALGO_ORDER))
        for r in rows:
            self.assertGreater(r['silhouette'], 0.5, r['algo'])
            self.assertGreater(r['stability'], 0.9, r['algo'])
        second = [r for r in rows if r['date'] == '2025']
        self.assertTrue(all(r['temporal_ari'] > 0.9 for r in second))
        self.assertIsNone([r for r in rows if r['date'] == '2024'][0]['temporal_ari'])

    def test_multi_metric_rank_and_selection(self):
        rows, _ = cr2.sweep(self.snaps, CFG, 'B_test')
        summary = cr2.summarize(rows, CFG)
        scored = [s for s in summary if s['score'] is not None]
        self.assertEqual(len(scored), 4)
        self.assertTrue(all(1 <= s['score'] <= 4 for s in scored))
        choice = cr2.select(summary, 'B_test')
        self.assertEqual(choice['score'], min(s['score'] for s in scored))

    def test_unbalanced_configs_are_never_ranked(self):
        rows = [dict(group='A', date=d, algo='kmeans', k=3, n=100, k_used=3, min_share=0.01, max_share=0.97,
                     sizes=[97, 2, 1], silhouette=0.9, davies_bouldin=0.2, calinski_harabasz=900.0, stability=1.0,
                     temporal_ari=1.0) for d in ('1', '2')]
        summary = cr2.summarize(rows, CFG)
        self.assertFalse(summary[0]['admissible'])
        self.assertIsNone(cr2.select(summary, 'A'))


if __name__ == '__main__':
    unittest.main()
