import unittest
import numpy as np

from delta_t1.experiments.bpit_enriched import (
    EnrichedSnapshot,
    create_adapter,
    evaluate_candidate,
    rank_and_select_candidates,
)

FEATURES = (
    "roe",
    "roa",
    "gross_margin",
    "net_margin",
    "debt_to_equity",
    "current_ratio",
    "asset_turnover",
    "revenue_growth",
    "cfo_to_ni",
)

class TestBpitScreeningSelection(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        # Tạo 2 snapshot năm 2017 và 2018 với 60 mã
        self.snapshots = []
        for y in [2017, 2018]:
            c1 = np.random.normal(loc=-2.0, scale=0.5, size=(30, len(FEATURES)))
            c2 = np.random.normal(loc=2.0, scale=0.5, size=(30, len(FEATURES)))
            raw = np.abs(np.vstack([c1, c2])) + 0.1
            tickers = [f"T{i:02d}" for i in range(60)]
            usable = ["2018-04-01"] * 60
            fit_mask = np.ones(60, dtype=bool)
            self.snapshots.append(
                EnrichedSnapshot(
                    fiscal_year=y,
                    tickers=tickers,
                    raw=raw,
                    usable_dates=usable,
                    cutoff="2018-04-30",
                    fit_mask=fit_mask,
                    features=FEATURES,
                )
            )

    def test_create_adapter(self):
        a1 = create_adapter("kmeans", 3)
        self.assertEqual(a1.k, 3)
        a2 = create_adapter("pca_kmeans", 4)
        self.assertEqual(a2.k, 4)
        a3 = create_adapter("ward", 5)
        self.assertEqual(a3.k, 5)
        a4 = create_adapter("gmm", 6)
        self.assertEqual(a4.k, 6)

    def test_evaluate_candidate(self):
        res = evaluate_candidate("kmeans", 3, self.snapshots)
        self.assertEqual(res["algo"], "kmeans")
        self.assertEqual(res["k"], 3)
        self.assertIsNotNone(res["median_silhouette"])
        self.assertIsNotNone(res["median_davies_bouldin"])
        self.assertIsNotNone(res["median_calinski_harabasz"])
        self.assertGreaterEqual(res["median_stability"], 0.0)

    def test_rank_and_select_candidates(self):
        eval_results = [
            {
                "algo": "kmeans",
                "k": 3,
                "median_silhouette": 0.5,
                "median_davies_bouldin": 0.8,
                "median_calinski_harabasz": 200.0,
                "median_stability": 0.85,
                "median_temporal_ari": 0.7,
                "is_admissible": True,
            },
            {
                "algo": "pca_kmeans",
                "k": 4,
                "median_silhouette": 0.4,
                "median_davies_bouldin": 1.0,
                "median_calinski_harabasz": 150.0,
                "median_stability": 0.82,
                "median_temporal_ari": 0.6,
                "is_admissible": True,
            },
            {
                "algo": "ward",
                "k": 5,
                "median_silhouette": 0.3,
                "median_davies_bouldin": 1.5,
                "median_calinski_harabasz": 100.0,
                "median_stability": 0.70, # không đạt ngưỡng 0.8
                "median_temporal_ari": 0.5,
                "is_admissible": False,
            },
        ]

        winner, ranked = rank_and_select_candidates(eval_results)
        self.assertIsNotNone(winner)
        # kmeans k=3 tốt hơn pca_kmeans k=4 ở cả 5 metrics -> mean_rank thấp hơn -> thắng
        self.assertEqual(winner["algo"], "kmeans")
        self.assertEqual(winner["k"], 3)
        self.assertEqual(len(ranked), 2) # Chỉ có 2 ứng viên đạt admissibility

if __name__ == "__main__":
    unittest.main()
