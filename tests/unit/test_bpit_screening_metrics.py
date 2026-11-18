import unittest
import numpy as np

from delta_t1.clustering.bpit_adapters import BpitKMeansAdapter
from delta_t1.evaluation.bpit_screening import (
    compute_cluster_quality_metrics,
    compute_subsample_stability,
    compute_temporal_ari,
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

class TestBpitScreeningMetrics(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        # Tạo 3 cụm tách biệt rõ ràng để test
        c1 = np.random.normal(loc=-3.0, scale=0.5, size=(40, len(FEATURES)))
        c2 = np.random.normal(loc=0.0, scale=0.5, size=(40, len(FEATURES)))
        c3 = np.random.normal(loc=3.0, scale=0.5, size=(40, len(FEATURES)))
        self.x_t1 = np.vstack([c1, c2, c3])
        self.raw = np.abs(self.x_t1) + 0.1
        self.labels = np.array([0] * 40 + [1] * 40 + [2] * 40)

    def test_cluster_quality_metrics(self):
        res = compute_cluster_quality_metrics(self.x_t1, self.labels, k=3)
        self.assertTrue(res["valid"])
        self.assertIsNotNone(res["silhouette"])
        self.assertIsNotNone(res["davies_bouldin"])
        self.assertIsNotNone(res["calinski_harabasz"])
        # Silhouette cho các cụm tách biệt rõ thường > 0.4
        self.assertGreater(res["silhouette"], 0.4)
        # Min share cho 3 cụm đều nhau xấp xỉ 1/3 (0.33)
        self.assertAlmostEqual(res["min_cluster_share"], 1/3, places=2)

    def test_degenerate_metrics(self):
        # Trường hợp tất cả chung 1 nhãn
        single_labels = np.zeros(len(self.x_t1), dtype=int)
        res = compute_cluster_quality_metrics(self.x_t1, single_labels, k=3)
        self.assertFalse(res["valid"])
        self.assertIsNone(res["silhouette"])

    def test_subsample_stability(self):
        med_ari, aris = compute_subsample_stability(
            adapter_cls=BpitKMeansAdapter,
            adapter_kwargs={"k": 3, "n_init": 5},
            x_fit=self.x_t1,
            raw_fit=self.raw,
            features=FEATURES,
            full_labels=self.labels,
            subsample_ratio=0.9,
            seeds=(1, 2, 3),
        )
        self.assertEqual(len(aris), 3)
        # Với cụm tách biệt rõ, độ ổn định ARI phải rất cao (> 0.8)
        self.assertGreaterEqual(med_ari, 0.8)

    def test_temporal_ari(self):
        tickers_prev = ["A", "B", "C", "D"]
        labels_prev = np.array([0, 0, 1, 1])

        tickers_curr = ["B", "C", "D", "E"]
        # Cho mã B cụm 1, C và D cụm 0 (đảo tên nhãn) -> ARI trên {B, C, D} phải = 1.0 vì phân hoạch giống nhau
        labels_curr = np.array([1, 0, 0, 2])

        ari = compute_temporal_ari(tickers_prev, labels_prev, tickers_curr, labels_curr)
        self.assertIsNotNone(ari)
        self.assertAlmostEqual(ari, 1.0, places=4)

if __name__ == "__main__":
    unittest.main()
