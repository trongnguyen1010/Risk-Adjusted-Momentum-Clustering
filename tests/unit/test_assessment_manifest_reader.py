import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from delta_t1.product.assessment_repository import open_assessment_release


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


class TestAssessmentManifestReader(unittest.TestCase):
    def build_release(self, root: Path) -> tuple[Path, Path]:
        artifact = root / "data" / "experiments" / "assessment" / "assessment_v1_run01"
        artifact.mkdir(parents=True)
        files = ("assessments.jsonl", "peer_benchmarks.csv", "coverage.csv", "feature_history.jsonl")
        for filename in files:
            (artifact / filename).write_text(filename + "\n", encoding="utf-8")
        input_hashes = {
            "indicators_sqlite_sha256": "1" * 64,
            "availability_csv_sha256": "2" * 64,
            "bpit_labels_csv_sha256": "3" * 64,
        }
        manifest = {
            "version": "investment_assessment_v1",
            "as_of": "2026-01-02",
            "deterministic_content_sha256": "d" * 64,
            "input_hashes": input_hashes,
            "output_files": {filename: sha256_file(artifact / filename) for filename in files},
        }
        manifest_path = artifact / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        config_path = root / "configs" / "product" / "assessment_release_v1.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps({
            "schema_version": "assessment-release-pointer-v1",
            "release_status": "RELEASED",
            "release_id": "assessment_v1_run01",
            "release_revision": "assessment-v1-run01-r1",
            "artifact_version": "investment_assessment_v1",
            "artifact_dir": "data/experiments/assessment/assessment_v1_run01",
            "assessment_context": "SIMULATED_AS_OF",
            "as_of": "2026-01-02",
            "required_price_session": "2025-12-31",
            "evidence_cutoff_at": None,
            "verification_status": "PASS",
            "policy_revision": "D-ASS-01",
            "manifest_sha256": sha256_file(manifest_path),
            "deterministic_content_sha256": "d" * 64,
            "input_hashes": input_hashes,
        }), encoding="utf-8")
        return artifact, config_path

    def test_open_accepts_manifest_and_serving_files_matching_pins(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, config_path = self.build_release(root)

            result = open_assessment_release(config_path, repository_root=root)

            self.assertTrue(result.ready)
            self.assertIsNotNone(result.release)

    def test_open_rejects_a_tampered_serving_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact, config_path = self.build_release(root)
            (artifact / "coverage.csv").write_text("tampered\n", encoding="utf-8")

            result = open_assessment_release(config_path, repository_root=root)

            self.assertFalse(result.ready)
            self.assertEqual(result.reason, "SERVING_FILE_HASH_MISMATCH")

    def test_open_rejects_manifest_with_changed_source_pin(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact, config_path = self.build_release(root)
            manifest_path = artifact / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["input_hashes"]["availability_csv_sha256"] = "c" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = open_assessment_release(config_path, repository_root=root)

            self.assertFalse(result.ready)
            self.assertEqual(result.reason, "MANIFEST_HASH_MISMATCH")

    def test_open_rejects_an_incompatible_artifact_revision(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, config_path = self.build_release(root)
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["artifact_version"] = "investment_assessment_v2"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            result = open_assessment_release(config_path, repository_root=root)

            self.assertFalse(result.ready)
            self.assertEqual(result.reason, "ARTIFACT_VERSION_MISMATCH")

    def test_open_rejects_manifest_missing_a_serving_output_pin(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact, config_path = self.build_release(root)
            manifest_path = artifact / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["output_files"]["coverage.csv"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = open_assessment_release(config_path, repository_root=root)
            self.assertFalse(result.ready)
            self.assertEqual(result.reason, "MANIFEST_HASH_MISMATCH")


if __name__ == "__main__":
    unittest.main()
