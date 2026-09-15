import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.clustering.dynamic.base import DynamicClusteringMethod
from delta_t1.features.registry import FEATURE_REGISTRY


class InvariantTests(unittest.TestCase):
    def test_dynamic_method_has_no_concrete_implementation(self):
        self.assertTrue(inspect.isabstract(DynamicClusteringMethod))

    def test_roi_is_not_cluster_eligible(self):
        self.assertFalse(FEATURE_REGISTRY.get("roi").cluster_eligible)


if __name__ == "__main__":
    unittest.main()
