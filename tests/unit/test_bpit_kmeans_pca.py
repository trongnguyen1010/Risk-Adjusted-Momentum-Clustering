import unittest
import numpy as np

from delta_t1.clustering.bpit_adapters import (
    BpitKMeansAdapter,
    BpitPcaKMeansAdapter,
    renumber_by_size,
    compute_cluster_order,
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

class TestBpitKMeansPca(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        # Tạo 100 mẫu giả lập 9 chiều trong không gian T1 và raw
        self.n_samples = 120
        self.raw_fit = np.random.uniform(0.01, 1.0, size=(self.n_samples, len(FEATURES)))
        # raw ROE (cột 0) và D/E (cột 4)
        self.raw_fit[:, 0] = np.random.uniform(-0.1, 0.4, size=self.n_samples)
        self.raw_fit[:, 4] = np.random.uniform(0.1, 3.0, size=self.n_samples)

        self.x_fit = (self.raw_fit - self.raw_fit.mean(axis=0)) / self.raw_fit.std(axis=0)

        # Mẫu late để test assign_late
        self.x_late = np.random.normal(size=(20, len(FEATURES)))

    def test_kmeans_adapter(self):
        for k in [3, 4, 5]:
            adapter = BpitKMeansAdapter(k=k, seed=42, n_init=5)
            labels = adapter.fit(self.x_fit, self.raw_fit, FEATURES)

            # 1. Đủ k cụm và đánh số 0..k-1
            self.assertEqual(len(set(labels)), k)
            self.assertEqual(set(labels), set(range(k)))

            # 2. Cụm 0 là cụm đông nhất (renumber by size)
            counts = np.bincount(labels, minlength=k)
            self.assertEqual(np.argmax(counts), 0)

            # 3. Thứ tự cụm (cluster_order) đủ k cụm
            self.assertEqual(len(adapter.cluster_order), k)
            self.assertEqual(set(adapter.cluster_order), set(range(k)))

            # 4. Gán late không đổi và đúng k cụm
            late_labels = adapter.assign_late(self.x_late)
            self.assertEqual(len(late_labels), len(self.x_late))
            self.assertTrue(all(0 <= lab < k for lab in late_labels))

    def test_pca_kmeans_adapter(self):
        adapter = BpitPcaKMeansAdapter(k=3, variance=0.8, seed=42, n_init=5)
        labels = adapter.fit(self.x_fit, self.raw_fit, FEATURES)

        # 1. PCA giảm số chiều và giải thích ít nhất 80% phương sai
        n_comps = adapter.pca.n_components_
        self.assertLess(n_comps, len(FEATURES))
        self.assertGreaterEqual(float(np.sum(adapter.pca.explained_variance_ratio_)), 0.8)

        # 2. Đủ k cụm
        self.assertEqual(len(set(labels)), 3)
        self.assertEqual(set(labels), {0, 1, 2})

        # 3. Late assignment dùng frozen PCA
        late_labels = adapter.assign_late(self.x_late)
        self.assertEqual(len(late_labels), len(self.x_late))
        self.assertTrue(all(0 <= lab < 3 for lab in late_labels))

if __name__ == "__main__":
    unittest.main()
