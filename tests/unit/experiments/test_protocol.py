import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.experiments.protocol import validate_protocol

CONFIG = ROOT / "configs/experiments/m2_market_only_v1.json"


class M2MarketOnlyProtocolTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_frozen_m2_market_only_config_is_valid(self):
        validate_protocol(self.config)
        self.assertEqual(len(self.config["development_snapshots"]), 15)
        self.assertEqual(len(self.config["holdout_snapshots"]), 7)
        self.assertFalse(self.config["portfolio_evaluation"]["enabled"])

    def test_pca_execution_requires_frozen_valid_component_count(self):
        config = copy.deepcopy(self.config)
        config["clustering"]["algorithm"] = "pca_kmeans"
        with self.assertRaisesRegex(ValueError, "component_rule_status"):
            validate_protocol(config)
        config["clustering"]["pca"]["component_rule_status"] = "frozen_on_development"
        for invalid in (None, True, 0, 9, 2.5):
            with self.subTest(count=invalid):
                config["clustering"]["pca"]["n_components"] = invalid
                with self.assertRaisesRegex(ValueError, "n_components"):
                    validate_protocol(config)
        config["clustering"]["pca"]["n_components"] = 2
        validate_protocol(config)
        config["clustering"]["reduction"] = {"method": "pca", "n_components": 4}
        with self.assertRaisesRegex(ValueError, "conflicts"):
            validate_protocol(config)

    def test_missing_required_feature_fails_closed(self):
        broken = copy.deepcopy(self.config)
        broken["clustering"]["features"].pop()
        with self.assertRaisesRegex(ValueError, "clustering.features"):
            validate_protocol(broken)

    def test_enabling_portfolio_evaluation_fails_closed(self):
        broken = copy.deepcopy(self.config)
        broken["portfolio_evaluation"]["enabled"] = True
        with self.assertRaisesRegex(ValueError, "portfolio_evaluation.enabled=false"):
            validate_protocol(broken)

    def test_changed_development_or_holdout_boundary_fails_closed(self):
        for field, value in (("start", "2023-12-29"), ("holdout_start", "2026-03-31")):
            with self.subTest(field=field):
                broken = copy.deepcopy(self.config)
                broken[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_protocol(broken)

    def test_preprocessing_and_minimum_count_are_frozen(self):
        mutations = (
            ("min_eligible_count", 119),
            ("scaling", "zscore"),
            ("winsor_quantile", 0.01),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                broken = copy.deepcopy(self.config)
                if field == "min_eligible_count":
                    broken[field] = value
                else:
                    broken["clustering"][field] = value
                with self.assertRaises(ValueError):
                    validate_protocol(broken)


if __name__ == "__main__":
    unittest.main()
