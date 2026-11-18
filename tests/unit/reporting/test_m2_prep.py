import json
from pathlib import Path
import unittest

from delta_t1.clustering.registry import get_algorithm
from delta_t1.clustering.dynamic.base import DynamicClusteringMethod
from delta_t1.experiments.m2_prep import (
    DEFAULT_OUTPUT,
    REQUIRED_FEATURES,
    build_data,
    sha256_input,
    verify_existing,
)
from delta_t1.experiments.protocol import validate_protocol


ROOT = Path(__file__).resolve().parents[3]


class M2PrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_data(ROOT)

    def test_latest_market_only_eligibility_is_905_of_952_and_separate(self):
        latest = [
            row for row in self.data["eligibility"]
            if row["snapshot_date"] == "2026-08-28"
        ]
        self.assertEqual(len(latest), 952)
        self.assertEqual(sum(row["market_experiment_eligible"] for row in latest), 905)
        source_rows = self.data["latest_universe"]
        self.assertEqual(len(source_rows), 905)
        self.assertEqual(self.data["latest_legacy_eligibility"], 0)

    def test_historical_membership_is_per_snapshot_not_terminal_905(self):
        totals = {
            row["snapshot_date"]: row["market_experiment_eligible"]
            for row in self.data["monthly"]
        }
        self.assertEqual(totals["2023-05-31"], 0)
        self.assertEqual(totals["2024-11-29"], 780)
        self.assertEqual(totals["2026-08-28"], 905)
        self.assertGreater(len(set(totals.values())), 10)

    def test_identity_research_and_portfolio_boundaries_remain_closed(self):
        summary = json.loads(
            (ROOT / DEFAULT_OUTPUT / "protocol_summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(summary["historical_identity_ready"], 0)
        self.assertEqual(summary["research_ready"], 0)
        self.assertFalse(summary["portfolio_evaluation"]["enabled"])
        forbidden = {
            row["metric"] for row in self.data["metrics"]
            if row["layer"] == "model_selection_firewall"
        }
        self.assertTrue({"future_return", "Sharpe", "ROI", "turnover"} <= forbidden)

    def test_monthly_diagnostics_reproduce_m1_and_explain_systemic_gaps(self):
        by_date = {row["snapshot_date"]: row for row in self.data["diagnostics"]}
        self.assertEqual(by_date["2023-05-31"]["benchmark_beta_dependency_fail"], 918)
        self.assertEqual(
            by_date["2023-05-31"]["classification"],
            "C_BENCHMARK_CALENDAR_PROPAGATION",
        )
        self.assertEqual(by_date["2025-02-28"]["insufficient_252_session_window"], 932)
        self.assertEqual(
            by_date["2025-02-28"]["classification"],
            "B_SPARSE_INCOMPLETE_MARKET_EVIDENCE",
        )

    def test_input_hashes_and_feature_contract(self):
        for relative, expected in self.data["input_hashes"].items():
            self.assertEqual(sha256_input(ROOT / relative), expected)
        self.assertEqual(tuple(row["name"] for row in self.data["feature_contract"]), REQUIRED_FEATURES)
        self.assertTrue(all(row["formula_code_status"] == "MATCH" for row in self.data["feature_contract"]))
        self.assertTrue(all(row["version_status"] == "MISMATCH_MANUAL_REVIEW_REQUIRED" for row in self.data["feature_contract"]))

    def test_dbscan_dynamic_and_strict_legacy_guards(self):
        with self.assertRaisesRegex(ValueError, "DBSCAN is not enabled"):
            get_algorithm("dbscan").validate_config({})
        self.assertEqual(DynamicClusteringMethod.__subclasses__(), [])
        legacy = json.loads(
            (ROOT / "configs/experiments/kmeans.example.json").read_text(encoding="utf-8")
        )
        validate_protocol(legacy)
        gaps = {row["area"]: row["status"] for row in self.data["implementation_gaps"]}
        self.assertEqual(gaps["experiment_runner"], "FIX_REQUIRED_BEFORE_M2_EXEC")
        self.assertEqual(gaps["input_loader"], "FIX_REQUIRED_BEFORE_M2_EXEC")

    def test_artifact_is_immutable_and_verifiable(self):
        verify_existing(ROOT)


if __name__ == "__main__":
    unittest.main()
