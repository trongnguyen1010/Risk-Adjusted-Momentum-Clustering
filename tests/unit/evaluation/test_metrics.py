import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.evaluation.cluster_metrics import cluster_metrics
from delta_t1.evaluation.portfolio_metrics import metrics


class MetricBoundaryTests(unittest.TestCase):
    def test_cluster_and_portfolio_metrics_are_separate(self):
        quality = cluster_metrics([[0], [1], [10], [11]],
                                  {"labels": [0, 0, 1, 1], "centroids": [[.5], [10.5]],
                                   "inertia": 1.0, "converged": True})
        performance = metrics([.01, -.01], [.005, -.005], 0, [0, 0])
        self.assertNotIn("sharpe", quality)
        self.assertIn("sharpe", performance)


if __name__ == "__main__":
    unittest.main()
