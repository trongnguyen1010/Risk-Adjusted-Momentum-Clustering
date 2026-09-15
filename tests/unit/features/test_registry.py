import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.features.preprocessing import fit_pca
from delta_t1.contracts import schema
from delta_t1.features.registry import FEATURE_REGISTRY


class FeatureRegistryTests(unittest.TestCase):
    def test_portfolio_metric_cannot_enter_cluster_space(self):
        with self.assertRaisesRegex(ValueError, "portfolio-only"):
            FEATURE_REGISTRY.require_cluster_eligible(["sharpe_63"])

    def test_sharpe_is_not_in_active_snapshot_or_registry(self):
        self.assertNotIn("sharpe_63", FEATURE_REGISTRY.names())
        self.assertNotIn("sharpe_126", schema("feature_snapshots")["fields"])
        self.assertIn("sharpe_63", schema("feature_snapshots_legacy_1_3_0")["fields"])

    def test_pca_records_snapshot_scope(self):
        _, bundle = fit_pca([[-1.0, -1.0], [0.0, 0.0], [1.0, 1.0]], 1)
        self.assertEqual(bundle["fit_scope"], "supplied_snapshot_only")


if __name__ == "__main__":
    unittest.main()
