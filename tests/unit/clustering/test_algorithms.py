import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.clustering.hierarchical import fit_ward
from delta_t1.clustering.kmeans import fit_snapshot as fit_kmeans_snapshot
from delta_t1.clustering.registry import algorithms
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score


class AlgorithmTests(unittest.TestCase):
    def test_registry_has_static_baseline_and_comparator(self):
        self.assertTrue({"kmeans", "hierarchical"} <= set(algorithms()))

    def test_ward_is_deterministic(self):
        vectors = [[0, 0], [0, 1], [10, 10], [10, 11]]
        self.assertEqual(fit_ward(vectors, 2), fit_ward(vectors, 2))

    def test_explicit_sklearn_kmeans_matches_library(self):
        features = ["mom_21", "mom_63", "mom_126", "mom_252", "vol_63",
                    "mdd_126", "beta_126", "liquidity_21"]
        rows = []
        for index, liquidity in enumerate([1, 2, 3, 100, 110, 120]):
            row = dict(security_id=f"TEST:{index}", ticker=f"T{index}",
                       as_of_date="2023-01-31", available_at="2023-01-31T00:00:00+00:00",
                       adjustment_basis="vendor_adjusted", market_feature_ready_v2=True)
            row.update({name: float(index + 1) for name in features})
            row["liquidity_21"] = float(liquidity)
            rows.append(row)
        config = dict(features=features, winsor_quantile=0, scaling="robust_per_snapshot",
                      eligibility_field="market_feature_ready_v2", momentum_feature="mom_21",
                      risk_feature="vol_63", k=2, k_range=[2], seed=42, n_init=10,
                      max_iter=300, implementation="sklearn")
        from delta_t1.features.preprocessing import preprocess
        vectors, _ = preprocess(rows, config)
        expected = KMeans(n_clusters=2, random_state=42, n_init=10, max_iter=300).fit(vectors)
        actual = fit_kmeans_snapshot(rows, config)
        self.assertEqual(adjusted_rand_score(expected.labels_, actual["labels"]), 1.0)
        self.assertAlmostEqual(expected.inertia_, actual["diagnostics"][0]["inertia"])


if __name__ == "__main__":
    unittest.main()
