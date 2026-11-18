import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify_investment_assessment_v1 import (
    FEATURES,
    FINANCIAL_FEATURES,
    MARKET_FEATURES,
    sha256_file,
    verify_assessment_artifacts,
    write_verification_report,
)


class TestAssessmentReleaseVerifier(unittest.TestCase):
    def build_artifact(self, root: Path) -> Path:
        artifact = root / "assessment-release"
        artifact.mkdir()
        assessment = {
            "ticker": "AAA", "as_of": "2026-01-02", "verdict": "MONITOR", "usable_from_date": "2025-12-31",
            "financial_features": {feature: 1.0 for feature in FINANCIAL_FEATURES},
            "market_features": {feature: 1.0 for feature in MARKET_FEATURES},
            "peer_comparisons": {feature: {"peer_basis": "SAME_A_AND_B", "peer_count": 3, "peer_median": 1.0, "p25": 0.5, "p75": 1.5} for feature in FEATURES},
        }
        (artifact / "assessments.jsonl").write_text(json.dumps(assessment) + "\n", encoding="utf-8")
        peer_rows = ["ticker,metric,peer_basis,peer_count,peer_median,p25,p75"]
        peer_rows.extend(f"AAA,{feature},SAME_A_AND_B,3,1.0,0.5,1.5" for feature in sorted(FEATURES))
        (artifact / "peer_benchmarks.csv").write_text("\n".join(peer_rows) + "\n", encoding="utf-8")
        coverage_rows = ["feature,category,total_tickers,valid_count,coverage_pct"]
        coverage_rows.extend(f"{feature},{'FINANCIAL' if feature in FINANCIAL_FEATURES else 'MARKET'},1,1,100.0" for feature in sorted(FEATURES))
        (artifact / "coverage.csv").write_text("\n".join(coverage_rows) + "\n", encoding="utf-8")
        history_rows = [json.dumps({"ticker": "AAA", "fiscal_year": 2025, "metric": feature, "value": 1.0, "status": "OK", "usable_from_date": "2025-12-31", "source": "TEST"}) for feature in sorted(FEATURES)]
        (artifact / "feature_history.jsonl").write_text("\n".join(history_rows) + "\n", encoding="utf-8")
        self.write_manifest(artifact)
        return artifact

    def write_manifest(self, artifact: Path) -> None:
        output_files = {filename: sha256_file(artifact / filename) for filename in ("assessments.jsonl", "peer_benchmarks.csv", "coverage.csv", "feature_history.jsonl")}
        manifest = {
            "version": "investment_assessment_v1", "as_of": "2026-01-02", "total_tickers": 1,
            "verdict_summary": {"WORTH_CONSIDERING": 0, "MONITOR": 1, "LOW_PRIORITY": 0, "INSUFFICIENT_EVIDENCE": 0},
            "deterministic_content_sha256": "a" * 64,
            "input_hashes": {"indicators_sqlite_sha256": "b" * 64, "availability_csv_sha256": "c" * 64, "bpit_labels_csv_sha256": "d" * 64},
            "output_files": output_files,
        }
        (artifact / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_valid_artifact_passes_and_can_write_external_sidecar(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = self.build_artifact(root)
            report = verify_assessment_artifacts(artifact)
            self.assertTrue(report["passed"], report["errors"])
            self.assertEqual(report["total_assessments"], 1)
            sidecar = root / "verification.json"
            write_verification_report(sidecar, report, artifact)
            self.assertEqual(json.loads(sidecar.read_text(encoding="utf-8"))["verification_status"], "PASS")

    def test_tampered_file_fails_checksum(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = self.build_artifact(Path(temporary_directory))
            with (artifact / "assessments.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(" ")
            report = verify_assessment_artifacts(artifact)
            self.assertFalse(report["passed"])
            self.assertIn("Checksum không khớp: assessments.jsonl", report["errors"])

    def test_future_usable_date_fails_even_when_manifest_is_rehashed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = self.build_artifact(Path(temporary_directory))
            record = json.loads((artifact / "assessments.jsonl").read_text(encoding="utf-8"))
            record["usable_from_date"] = "2026-01-03"
            (artifact / "assessments.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            self.write_manifest(artifact)
            report = verify_assessment_artifacts(artifact)
            self.assertFalse(report["passed"])
            self.assertTrue(any("future leakage" in error for error in report["errors"]))

    def test_outside_whitelist_fails_even_when_manifest_is_rehashed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = self.build_artifact(Path(temporary_directory))
            record = json.loads((artifact / "assessments.jsonl").read_text(encoding="utf-8"))
            record["market_features"]["unexpected_feature"] = 1.0
            (artifact / "assessments.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            self.write_manifest(artifact)
            report = verify_assessment_artifacts(artifact)
            self.assertFalse(report["passed"])
            self.assertTrue(any("market_features không đúng whitelist" in error for error in report["errors"]))

    def test_refuses_to_write_into_immutable_artifact_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = self.build_artifact(Path(temporary_directory))
            report = verify_assessment_artifacts(artifact)
            with self.assertRaises(ValueError):
                write_verification_report(artifact / "verification.json", report, artifact)

    def test_insufficient_evidence_can_keep_peer_and_history_availability_gaps(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = self.build_artifact(Path(temporary_directory))
            record = json.loads((artifact / "assessments.jsonl").read_text(encoding="utf-8"))
            record["verdict"] = "INSUFFICIENT_EVIDENCE"
            record["peer_comparisons"] = {}
            (artifact / "assessments.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            history = [json.loads(line) for line in (artifact / "feature_history.jsonl").read_text(encoding="utf-8").splitlines()]
            history[0]["usable_from_date"] = ""
            (artifact / "feature_history.jsonl").write_text("\n".join(json.dumps(row) for row in history) + "\n", encoding="utf-8")
            self.write_manifest(artifact)
            manifest_path = artifact / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["verdict_summary"] = {"WORTH_CONSIDERING": 0, "MONITOR": 0, "LOW_PRIORITY": 0, "INSUFFICIENT_EVIDENCE": 1}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = verify_assessment_artifacts(artifact)
            self.assertTrue(report["passed"], report["errors"])


if __name__ == "__main__":
    unittest.main()
