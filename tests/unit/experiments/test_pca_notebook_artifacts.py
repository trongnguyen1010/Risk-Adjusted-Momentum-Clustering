"""Regression checks for active PCA V2 notebook exports, using saved evidence."""
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "M2/artifacts/m2-task6-pca-kmeans"
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

    def assert_checksums(self, base, mapping):
        self.assertTrue(mapping)
        for relative, expected in mapping.items():
            with self.subTest(path=relative):
                path = (base / relative).resolve()
                self.assertTrue(path.is_relative_to(base.resolve()))
                self.assertEqual(expected, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_export_checksums_and_frozen_development_scope(self):
        self.assertEqual("complete", self.manifest["status"])
        self.assertEqual("m2-task6-pca-kmeans", self.manifest["artifact_id"])
        self.assertEqual(self.manifest["config"], json.loads(
            (ROOT / "configs/experiments/m2_pca_market_only.json").read_text(encoding="utf-8")))
        self.assertTrue(self.manifest["task6_exports_complete"])
        self.assertFalse(self.manifest["portfolio_evaluation_enabled"])
        self.assertFalse(self.manifest["config"]["portfolio_evaluation"]["enabled"])
        self.assertEqual("CAFEF_C8_COMPLETE_ONLY_V2", self.manifest["data_version"])
        self.assertEqual((60, 45646), (self.manifest["n_snapshots"], self.manifest["n_assignments"]))
        self.assertEqual(60, len(set(self.dates)))
        self.assertEqual(("2019-01-31", "2023-12-29"), (self.dates[0], self.dates[-1]))
        holdout = self.manifest["config"]["holdout_snapshots"]
        self.assertEqual(24, len(holdout))
        self.assertFalse(set(self.dates) & set(holdout))
        self.assertLess(max(self.dates), min(holdout))
        self.assertEqual(set(self.dates), {r["snapshot_date"] for r in self.assignments})
        self.assertEqual([day + ".json" for day in self.dates],
                         sorted(p.name for p in (TASK / "models").glob("*.json")))
        self.assertEqual(60, len(self.manifest["model_exports"]))
        self.assert_checksums(TASK, self.manifest["artifacts"])
        self.assert_checksums(ROOT, self.manifest["model_exports"])
        self.assert_checksums(ROOT, self.manifest["report_export"])
        freeze_path = ROOT / self.manifest["config"]["clustering"]["pca"]["freeze_evidence"]
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        self.assertEqual(self.manifest["lineage"]["pca_freeze_sha256"],
                         hashlib.sha256(freeze_path.read_bytes()).hexdigest())
        self.assertEqual(self.dates, freeze["development_snapshots"])
        self.assertEqual((2, 2, "development_only"),
                         (freeze["n_components"], freeze["global_k"], freeze["scope"]))
        self.assertLessEqual(datetime.fromisoformat(freeze["created_at"]),
                             datetime.fromisoformat(self.manifest["timestamp"]))
        self.assert_checksums(freeze_path.parent, freeze["evidence_hashes"])

    def test_task7_to_task9_exports_preserve_source_and_checksums(self):
        source_hash = hashlib.sha256((TASK / "manifest.json").read_bytes()).hexdigest()
        for filename, artifact_id in (
                ("manifest.json", "m2-task7-pca-kmeans-quality"),
                ("task8_manifest.json", "m2-task8-pca-kmeans-profiling"),
                ("task9_manifest.json", "m2-task9-pca-kmeans-temporal")):
            with self.subTest(manifest=filename):
                manifest = json.loads((EVAL / filename).read_text(encoding="utf-8"))
                self.assertEqual(artifact_id, manifest["artifact_id"])
                self.assertEqual("complete", manifest["status"])
                self.assertEqual(self.manifest["artifact_id"], manifest["source_artifact_id"])
                self.assertEqual(source_hash, manifest["source_manifest_sha256"])
                self.assertEqual(60, manifest["n_snapshots"])
                self.assertEqual(2, manifest["k"])
                self.assertTrue(manifest["no_refit"])
                self.assertFalse(manifest["holdout_accessed"])
                self.assert_checksums(EVAL, manifest.get("outputs", manifest.get("artifacts", {})))
                self.assert_checksums(ROOT, manifest["report"])
                if "source_artifacts_sha256" in manifest:
                    self.assert_checksums(TASK, manifest["source_artifacts_sha256"])
                if "source_models_sha256" in manifest:
                    self.assert_checksums(TASK, manifest["source_models_sha256"])

    def test_transitions_use_persistent_ids_and_match_member_counts(self):
        by_date = {day: {r["security_id"]: int(r["aligned_cluster_id"])
                         for r in self.assignments if r["snapshot_date"] == day} for day in self.dates}
        transitions = rows(EVAL / "transition_matrices.csv")
        temporal = rows(EVAL / "temporal_stability.csv")
        self.assertEqual(59, len(temporal))
        self.assertEqual(59 * 4, len(transitions))
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
        self.assertEqual(59 * 2 * 8, len(drift))
        self.assertEqual({(a, b, label, feature)
                          for a, b in zip(self.dates[:-1], self.dates[1:])
                          for label in range(2) for feature in self.features},
                         {(r["from_date"], r["to_date"], int(r["aligned_cluster_id"]), r["feature"])
                          for r in drift})
        for row in drift:
            label, feature = int(row["aligned_cluster_id"]), row["feature"]
            before = float(profiles[row["from_date"], label][feature])
            after = float(profiles[row["to_date"], label][feature])
            self.assertAlmostEqual(before, float(row["value_from"]), delta=max(1e-10, abs(before) * 1e-12))
            self.assertAlmostEqual(after, float(row["value_to"]), delta=max(1e-10, abs(after) * 1e-12))
            self.assertAlmostEqual(after - before, float(row["delta"]), delta=max(1e-10, abs(after-before)*1e-12))

    def test_pca_scores_reproduce_saved_centroids_and_assignments(self):
        scores = rows(TASK / "pca_scores.csv")
        assignments = {(r["snapshot_date"], r["security_id"]): r for r in self.assignments}
        inputs = {(r["snapshot_date"], r["security_id"]): r for r in rows(TASK / "input_features.csv")}
        json_scores = [json.loads(line) for line in (TASK / "pca_scores.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(45646, len(scores))
        self.assertEqual(45646, len(self.assignments))
        score_keys = {(r["snapshot_date"], r["security_id"]) for r in scores}
        self.assertEqual(45646, len(score_keys))
        self.assertEqual(set(assignments), score_keys)
        self.assertEqual(set(inputs), score_keys)
        self.assertEqual(len(scores), len(json_scores))
        self.assertEqual(["snapshot_date", "security_id", "PC1", "PC2"], list(scores[0]))
        for csv_row, json_row in zip(scores, json_scores):
            self.assertEqual((csv_row["snapshot_date"], csv_row["security_id"]),
                             (json_row["snapshot_date"], json_row["security_id"]))
            for component in ("PC1", "PC2"):
                self.assertEqual(float(csv_row[component]), json_row[component])
        for day in self.dates:
            model = json.loads((TASK / f"models/{day}.json").read_text(encoding="utf-8"))
            reduction = model["scaler"]["_reduction"]
            self.assertEqual(2, reduction["n_components"])
            self.assertEqual("supplied_snapshot_only", reduction["fit_scope"])
            self.assertEqual(2, len(model["centroids"]))
            self.assertTrue(all(len(center) == 2 for center in model["centroids"]))
            for row in (r for r in scores if r["snapshot_date"] == day):
                vector = [float(row[f"PC{i}"]) for i in range(1, 3)]
                source = inputs[day, row["security_id"]]
                scaled = []
                for feature in self.features:
                    scaler = model["scaler"][feature]
                    value = max(scaler["lower"], min(scaler["upper"], float(source[feature])))
                    scaled.append((value - scaler["center"]) / scaler["scale"])
                centered = [value - center for value, center in zip(scaled, reduction["input_center"])]
                projected = [sum(value * loading for value, loading in zip(centered, component))
                             for component in reduction["components"]]
                for actual, expected in zip(vector, projected):
                    self.assertAlmostEqual(actual, expected, delta=max(1e-9, abs(expected) * 1e-12))
                distances = [sum((a-b)**2 for a,b in zip(vector, center)) for center in model["centroids"]]
                assignment = assignments[day, row["security_id"]]
                self.assertEqual(distances.index(min(distances)), int(assignment["raw_cluster_id"]))
        summary = rows(TASK / "pca_diagnostics.csv")
        self.assertEqual(self.dates, [r["snapshot_date"] for r in summary])
        self.assertTrue(all(int(r["n_components"]) == 2 for r in summary))
        self.assertEqual(2, max(int(r["minimum_components_90"]) for r in summary))
        self.assertTrue(all(float(r["cumulative_explained_variance"]) >= .9 for r in summary))

    def test_quality_and_profile_schemas_follow_the_plan(self):
        quality = rows(EVAL / "quality_summary.csv")
        self.assertEqual(5, len(quality))
        self.assertEqual(["metric", "n_total", "n_available", "mean", "median", "minimum", "maximum"],
                         list(quality[0]))
        self.assertTrue(all(int(r["n_total"]) == int(r["n_available"]) == 60 for r in quality))
        self.assertEqual(120, len(self.profiles))
        self.assertEqual(["snapshot_date", "raw_cluster_id", "aligned_cluster_id", "size", "size_ratio", *self.features],
                         list(self.profiles[0]))


if __name__ == "__main__":
    unittest.main()
