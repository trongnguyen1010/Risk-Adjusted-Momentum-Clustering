import json
import tempfile
import unittest
from pathlib import Path

from delta_t1.product.assessment_repository import resolve_assessment_release


class TestAssessmentReleaseConfig(unittest.TestCase):
    def write_config(self, root: Path, **overrides) -> Path:
        config_path = root / "configs" / "product" / "assessment_release_v1.json"
        config_path.parent.mkdir(parents=True)
        config = {
            "schema_version": "assessment-release-pointer-v1",
            "release_status": "RELEASED",
            "release_id": "assessment_v1_run01",
            "release_revision": "assessment-v1-run01-r1",
            "artifact_dir": "data/experiments/assessment/assessment_v1_run01",
            "assessment_context": "SIMULATED_AS_OF",
            "as_of": "2026-01-02",
            "required_price_session": "2025-12-31",
            "evidence_cutoff_at": None,
            "verification_status": "PASS",
        }
        config.update(overrides)
        config_path.write_text(json.dumps(config), encoding="utf-8")
        return config_path

    def test_explicit_config_resolves_the_pinned_artifact(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "data" / "experiments" / "assessment" / "assessment_v1_run01"
            artifact.mkdir(parents=True)
            config_path = self.write_config(root)

            result = resolve_assessment_release(config_path, repository_root=root)

            self.assertTrue(result.ready)
            self.assertEqual(result.release.artifact_dir, artifact.resolve())
            self.assertEqual(result.release.assessment_context, "SIMULATED_AS_OF")
            self.assertEqual(result.release.release_revision, "assessment-v1-run01-r1")

    def test_missing_pointer_is_not_ready_without_fallback(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "data" / "experiments" / "assessment" / "newer_run").mkdir(parents=True)
            config_path = self.write_config(root, artifact_dir="")

            result = resolve_assessment_release(config_path, repository_root=root)

            self.assertFalse(result.ready)
            self.assertEqual(result.status, "NOT_READY")
            self.assertEqual(result.reason, "RELEASE_POINTER_INVALID")

    def test_missing_artifact_is_not_ready(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            config_path = self.write_config(root)

            result = resolve_assessment_release(config_path, repository_root=root)

            self.assertFalse(result.ready)
            self.assertEqual(result.reason, "ARTIFACT_NOT_FOUND")

    def test_no_config_is_not_ready(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            result = resolve_assessment_release("configs/product/assessment_release_v1.json", repository_root=root)

            self.assertFalse(result.ready)
            self.assertEqual(result.reason, "CONFIG_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
