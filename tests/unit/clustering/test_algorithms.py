import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.clustering.hierarchical import fit_ward
from delta_t1.clustering.registry import algorithms


class AlgorithmTests(unittest.TestCase):
    def test_registry_has_static_baseline_and_comparator(self):
        self.assertTrue({"kmeans", "hierarchical"} <= set(algorithms()))

    def test_ward_is_deterministic(self):
        vectors = [[0, 0], [0, 1], [10, 10], [10, 11]]
        self.assertEqual(fit_ward(vectors, 2), fit_ward(vectors, 2))


if __name__ == "__main__":
    unittest.main()
