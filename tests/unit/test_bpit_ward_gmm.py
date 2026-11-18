import unittest
import numpy as np

from delta_t1.clustering.bpit_adapters import (
    BpitWardAdapter,
    BpitGmmAdapter,
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

class TestBpitWardGmm(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        self.n_samples = 120
        self.raw_fit = np.random.uniform(0.01, 1.0, size=(self.n_samples, len(FEATURES)))
        self.raw_fit[:, 0] = np.random.uniform(-0.1, 0.4, size=self.n_samples)
        self.raw_fit[:, 4] = np.random.uniform(0.1, 3.0, size=self.n_samples)

        self.x_fit = (self.raw_fit - self.raw_fit.mean(axis=0)) / self.raw_fit.std(axis=0)
        self.x_late = np.random.normal(size=(20, len(FEATURES)))

    def test_ward_adapter(self):
        for k in [3, 4, 5]:
            adapter = BpitWardAdapter(k=k)
            labels = adapter.fit(self.x_fit, self.raw_fit, FEATURES)

            # 1. Đủ k cụm và đánh số 0..k-1
            self.assertEqual(len(set(labels)), k)
            self.assertEqual(set(labels), set(range(k)))

            # 2. Cụm 0 là cụm đông nhất
            counts = np.bincount(labels, minlength=k)
            self.assertEqual(np.argmax(counts), 0)

            # 3. Thứ tự cụm
            self.assertEqual(len(adapter.cluster_order), k)
            self.assertEqual(set(adapter.cluster_order), set(range(k)))

            # 4. Gán late dùng centroid
            late_labels = adapter.assign_late(self.x_late)
            self.assertEqual(len(late_labels), len(self.x_late))
            self.assertTrue(all(0 <= lab < k for lab in late_labels))

    def test_gmm_adapter(self):
        for k in [3, 4]:
            adapter = BpitGmmAdapter(k=k, seed=42, n_init=2)
            labels = adapter.fit(self.x_fit, self.raw_fit, FEATURES)

            # 1. Đủ k cụm và đánh số 0..k-1
            self.assertEqual(len(set(labels)), k)
            self.assertEqual(set(labels), set(range(k)))

            # 2. GMM đã hội tụ
            self.assertTrue(adapter.model.converged_)

            # 3. Gán late dùng posterior model
            late_labels = adapter.assign_late(self.x_late)
            self.assertEqual(len(late_labels), len(self.x_late))
            self.assertTrue(all(0 <= lab < k for lab in late_labels))

if __name__ == "__main__":
    unittest.main()
