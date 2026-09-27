import copy
import json
import math
from pathlib import Path
from statistics import mean
import unittest

from delta_t1.clustering.base import build_snapshot
from delta_t1.evaluation.cluster_metrics import squared_distance
from delta_t1.experiments.runner import (
    m2_clustering_config,
    prepare_m2_market_only_snapshots,
    prepare_snapshot_rows,
)


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/experiments/m2_market_only_v1.json"
C8 = ROOT / "artifacts/cafef_primary/cafef-c8-complete-only-v1"
FEATURES = (
    "mom_21", "mom_63", "mom_126", "mom_252",
    "vol_63", "mdd_126", "beta_126", "liquidity_21",
)


class M2MarketOnlyRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.source, prepared = prepare_m2_market_only_snapshots(
            C8, cls.config, snapshot_dates=("2023-11-30",),
        )
        cls.november = prepared[0]

    def test_1_filters_142_eligible_securities_for_sample_snapshot(self):
        self.assertEqual("ready", self.november["status"])
        self.assertEqual(142, self.november["eligible_count"])
        self.assertEqual(142, len(self.november["rows"]))
        self.assertTrue(all(row["market_feature_ready_v2"] for row in self.november["rows"]))
        self.assertTrue(all(row["eligibility"] is False for row in self.november["rows"]))

    def test_2_terminal_universe_is_not_applied_retrospectively(self):
        config = copy.deepcopy(self.config)
        config["min_eligible_count"] = 1
        early = self._row("EARLY_ONLY", "2023-11-30", ready=True)
        terminal = self._row("TERMINAL_ONLY", "2026-08-28", ready=True)
        historical = prepare_snapshot_rows([early], config, "2023-11-30")
        latest = prepare_snapshot_rows([terminal], config, "2026-08-28")
        self.assertEqual(["EARLY_ONLY"], [row["security_id"] for row in historical["rows"]])
        self.assertEqual(["TERMINAL_ONLY"], [row["security_id"] for row in latest["rows"]])
        self.assertEqual(142, self.november["eligible_count"])
        with self.assertRaisesRegex(ValueError, "only frozen development snapshots"):
            prepare_m2_market_only_snapshots(
                C8, self.config, snapshot_dates=("2026-08-28",),
            )

    def test_3_all_eight_features_are_present_numeric_and_finite(self):
        self.assertEqual(FEATURES, tuple(self.config["clustering"]["features"]))
        for row in self.november["rows"]:
            for feature in FEATURES:
                value = row[feature]
                self.assertIsNot(type(value), bool)
                self.assertIsInstance(value, (int, float))
                self.assertTrue(math.isfinite(value))
        broken = copy.deepcopy(self.november["rows"])
        broken[0]["mom_21"] = float("inf")
        with self.assertRaisesRegex(ValueError, "nonfinite M2 feature"):
            prepare_snapshot_rows(broken, self.config, "2023-11-30")

    def test_4_snapshot_below_minimum_is_skipped(self):
        rows = [self._row(f"SID-{index:03d}", "2024-01-31", ready=True)
                for index in range(119)]
        result = prepare_snapshot_rows(rows, self.config, "2024-01-31")
        self.assertEqual("skipped", result["status"])
        self.assertEqual(119, result["eligible_count"])
        self.assertEqual([], result["rows"])
        self.assertEqual("eligible_count_below_minimum: 119 < 120", result["reason"])

    def test_5_runner_output_is_accepted_by_common_snapshot_interface(self):
        cluster = m2_clustering_config(
            self.config,
            k=2,
            k_range=[2],
            momentum_feature="mom_63",
            risk_feature="vol_63",
        )

        def deterministic_test_fit(vectors, k, _config):
            order = sorted(range(len(vectors)), key=lambda index: (vectors[index][0], index))
            labels = [0] * len(vectors)
            for index in order[len(order) // 2:]:
                labels[index] = 1
            centers = [[mean(vectors[index][column] for index in range(len(vectors))
                             if labels[index] == label)
                        for column in range(len(vectors[0]))]
                       for label in range(k)]
            inertia = sum(squared_distance(row, centers[label])
                          for row, label in zip(vectors, labels))
            return dict(labels=labels, centroids=centers, inertia=inertia,
                        iterations=1, converged=True)

        snapshot = build_snapshot(self.november["rows"], cluster, deterministic_test_fit)
        self.assertEqual("2023-11-30", snapshot["snapshot_date"])
        self.assertEqual(142, len(snapshot["rows"]))
        self.assertEqual(142, len(snapshot["labels"]))
        self.assertEqual("robust_per_snapshot", snapshot["model"]["scaler"]["mom_21"]["method"])

    @staticmethod
    def _row(security_id, snapshot_date, ready):
        row = {
            "security_id": security_id,
            "as_of_date": snapshot_date,
            "available_at": snapshot_date + "T17:00:00+07:00",
            "adjustment_basis": "vendor_adjusted",
            "market_feature_ready_v2": ready,
            "eligibility": False,
        }
        row.update({feature: float(index + 1) for index, feature in enumerate(FEATURES)})
        return row


if __name__ == "__main__":
    unittest.main()
