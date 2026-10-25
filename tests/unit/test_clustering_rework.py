import unittest

import numpy as np

from delta_t1.clustering import robust_transforms as rt
from delta_t1.experiments import clustering_rework as cr

CFG = dict(algorithms=['kmeans', 'gmm'], k=[3], seed=42, stability_seeds=[1, 2], kmeans_n_init=5,
           gmm=dict(covariance_type='full', n_init=1, reg_covar=1e-4, max_iter=200),
           admissible=dict(min_cluster_share=0.05, share_of_snapshots=0.8, median_seed_ari=0.8))


def blobs(seed=0, n=60):
    rng = np.random.default_rng(seed)
    centers = np.array([[0, 0], [8, 0], [0, 8]])
    x = np.vstack([c + rng.normal(size=(n, 2)) for c in centers])
    return np.column_stack([x, rng.lognormal(10, 2, size=len(x))])  # third column: liquidity-like tail


class TransformTests(unittest.TestCase):
    def test_log_and_winsorize_bound_extremes(self):
        raw = np.column_stack([np.r_[np.zeros(98), 5, 1e6], np.r_[np.arange(99.0), 1e12]])
        out = rt.transform(raw, ('x', 'liquidity_21'), 'T1')
        self.assertLess(np.abs(out).max(), 10)  # a single 1e12 row can no longer dominate
        self.assertTrue(np.allclose(out.mean(axis=0), 0))

    def test_rank_normal_is_order_preserving_and_symmetric(self):
        raw = np.array([[1.0], [100.0], [1e9], [-5.0]])
        out = rt.transform(raw, ('x',), 'T2').ravel()
        self.assertEqual(list(np.argsort(out)), [3, 0, 1, 2])
        self.assertAlmostEqual(out.sum(), 0.0)

    def test_missing_values_are_rejected(self):
        with self.assertRaises(ValueError):
            rt.transform(np.array([[1.0, np.nan]]), ('a', 'b'), 'T1')
        with self.assertRaises(ValueError):
            rt.log_columns(np.array([[-1.0]]), ('liquidity_21',))

    def test_block_weights_equalize_variance(self):
        x = np.column_stack([np.arange(10.0), np.arange(10.0) * 5, np.arange(10.0) * 100])
        out = rt.block_weights(x, (2, 1))
        self.assertAlmostEqual(out[:, :2].var(axis=0).sum(), 0.5)
        self.assertAlmostEqual(out[:, 2:].var(axis=0).sum(), 0.5)


class SweepTests(unittest.TestCase):
    def test_sweep_selects_balanced_stable_config(self):
        snaps = [cr.Snapshot('A', f'2025-0{i}', [f'T{j}' for j in range(180)], blobs(i), ('a', 'b', 'liquidity_21'))
                 for i in (1, 2)]
        rows = cr.sweep(snaps, CFG, recipes=('T1', 'T2'))
        self.assertEqual(len(rows), 2 * 2 * 2)
        summary = cr.summarize(rows, CFG)
        choice = cr.select(summary, 'A')
        self.assertIsNotNone(choice)
        self.assertEqual(choice['k'], 3)
        self.assertGreaterEqual(choice['median_min_share'], 0.05)
        series = cr.full_series(snaps, choice, CFG)
        self.assertGreater(series[1]['temporal_ari'], 0.5)

    def test_tiny_cluster_configs_are_not_admissible(self):
        rows = [dict(family='A', recipe='T0', algo='kmeans', k=3, min_share=0.001, k_used=3, max_share=0.99,
                     balance=0.1, silhouette=0.95, davies_bouldin=0.3, seed_ari=1.0)] * 5
        summary = cr.summarize(rows, CFG)
        self.assertFalse(summary[0]['admissible'])
        self.assertIsNone(cr.select(summary, 'A'))  # high silhouette alone does not win


if __name__ == '__main__':
    unittest.main()
