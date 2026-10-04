"""Regression checks for aligned PCA notebook exports, using saved evidence."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "M2/artifacts/m2-task6-pca-kmeans-v1"
EVAL = ROOT / "M2/artifacts/m2-evaluation-pca-kmeans"


def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class PCANotebookArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((TASK / "manifest.json").read_text(encoding="utf-8"))
        cls.dates = cls.manifest["config"]["development_snapshots"]
        cls.features = cls.manifest["config"]["clustering"]["features"]
        cls.assignments = rows(TASK / "assignments.csv")
        cls.profiles = rows(TASK / "cluster_profiles.csv")

    def test_export_checksums_and_frozen_development_scope(self):
        self.assertEqual("complete", self.manifest["status"])
        self.assertEqual("m2-task6-pca-kmeans-v1", self.manifest["artifact_id"])
        self.assertTrue(self.manifest["storage_migration"]["requested_by_owner"])
        self.assertFalse(self.manifest["storage_migration"]["numeric_results_changed"])
        self.assertEqual(self.manifest["config"], json.loads(
            (ROOT / "configs/experiments/m2_task6_pca.json").read_text(encoding="utf-8")))
        self.assertFalse(self.manifest["holdout_accessed"])
        self.assertFalse(self.manifest["portfolio_evaluation_enabled"])
        for relative, expected in self.manifest["artifacts"].items():
            with self.subTest(path=relative):
                self.assertEqual(expected, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())

    def test_transitions_use_persistent_ids_and_match_member_counts(self):
        by_date = {day: {r["security_id"]: int(r["aligned_cluster_id"])
                         for r in self.assignments if r["snapshot_date"] == day} for day in self.dates}
        transitions = rows(EVAL / "transition_matrices.csv")
        temporal = rows(EVAL / "temporal_stability.csv")
        self.assertEqual(list(zip(self.dates[:-1], self.dates[1:])),
                         [(r["from_date"], r["to_date"]) for r in temporal])
        for pair in temporal:
            before, after = by_date[pair["from_date"]], by_date[pair["to_date"]]
            shared = before.keys() & after.keys()
            expected = Counter((before[sid], after[sid]) for sid in shared)
            saved = [r for r in transitions if (r["from_date"], r["to_date"])
                     == (pair["from_date"], pair["to_date"])]
            self.assertEqual(4, len(saved))
            for row in saved:
                source, target = int(row["from_cluster"]), int(row["to_cluster"])
                self.assertEqual(expected[source, target], int(row["count"]))
                denominator = sum(count for (label, _), count in expected.items() if label == source)
                if denominator:
                    self.assertAlmostEqual(expected[source, target] / denominator, float(row["rate"]))
            self.assertEqual(len(shared), int(pair["n_common"]))
            self.assertEqual(len(after.keys() - before.keys()), int(pair["entered_count"]))
            self.assertEqual(len(before.keys() - after.keys()), int(pair["exited_count"]))
            self.assertAlmostEqual(sum(count for (a, b), count in expected.items() if a != b)
                                   / len(shared), float(pair["migration_rate"]))

    def test_drift_has_real_endpoints_from_the_same_aligned_profile(self):
        profiles = {(r["snapshot_date"], int(r["aligned_cluster_id"])): r for r in self.profiles}
        drift = rows(EVAL / "centroid_drift.csv")
        self.assertEqual(224, len(drift))
        for row in drift:
            label, feature = int(row["aligned_cluster_id"]), row["feature"]
            before = float(profiles[row["from_date"], label][feature])
            after = float(profiles[row["to_date"], label][feature])
            self.assertAlmostEqual(before, float(row["value_from"]))
            self.assertAlmostEqual(after, float(row["value_to"]))
            self.assertAlmostEqual(after - before, float(row["delta"]), delta=max(1e-10, abs(after-before)*1e-12))

    def test_pca_scores_reproduce_saved_centroids_and_assignments(self):
        scores = rows(TASK / "pca_scores.csv")
        assignments = {(r["snapshot_date"], r["security_id"]): r for r in self.assignments}
        self.assertEqual(5615, len(scores))
        for day in self.dates:
            model = json.loads((TASK / f"models/{day}.json").read_text(encoding="utf-8"))
            for row in (r for r in scores if r["snapshot_date"] == day):
                vector = [float(row[f"PC{i}"]) for i in range(1, 5)]
                distances = [sum((a-b)**2 for a,b in zip(vector, center)) for center in model["centroids"]]
                assignment = assignments[day, row["security_id"]]
                self.assertEqual(distances.index(min(distances)), int(assignment["raw_cluster_id"]))
                self.assertAlmostEqual(vector[0], float(assignment["pca_x"]))
                self.assertAlmostEqual(vector[1], float(assignment["pca_y"]))
        summary = rows(TASK / "pca_diagnostics.csv")
        self.assertEqual(4, max(int(r["minimum_components_90"]) for r in summary))
        self.assertTrue(all(float(r["cumulative_explained_variance"]) >= .9 for r in summary))

    def test_quality_and_profile_schemas_follow_the_plan(self):
        quality = rows(EVAL / "quality_summary.csv")
        self.assertEqual(5, len(quality))
        self.assertEqual(["metric", "n_total", "n_available", "mean", "median", "minimum", "maximum"],
                         list(quality[0]))
        self.assertTrue(all(int(r["n_total"]) == int(r["n_available"]) == 15 for r in quality))
        self.assertEqual(["snapshot_date", "raw_cluster_id", "aligned_cluster_id", "size", "size_ratio", *self.features],
                         list(self.profiles[0]))


if __name__ == "__main__":
    unittest.main()
