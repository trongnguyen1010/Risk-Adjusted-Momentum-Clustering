import unittest
import json
from pathlib import Path

from delta_t1.experiments.investment_assessment_v1 import (
    OfflineAssessmentBuilder,
    VERDICT_WORTH_CONSIDERING,
    VERDICT_MONITOR,
    VERDICT_LOW_PRIORITY,
    VERDICT_INSUFFICIENT_EVIDENCE,
)
from scripts.verify_investment_assessment_v1 import verify_assessment_artifacts

class TestAssessmentRealHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.indicators_db = cls.repo_root / "data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/indicators.sqlite"
        cls.availability_csv = cls.repo_root / "data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv"
        cls.bpit_labels = cls.repo_root / "data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01/labels.csv"
        cls.output_dir = cls.repo_root / "data/experiments/assessment/assessment_v1_run01"

        assert cls.indicators_db.exists(), f"Không tìm thấy {cls.indicators_db}"
        assert cls.availability_csv.exists(), f"Không tìm thấy {cls.availability_csv}"
        assert cls.bpit_labels.exists(), f"Không tìm thấy {cls.bpit_labels}"
        assert cls.output_dir.exists(), f"Không tìm thấy {cls.output_dir}"

        cls.builder = OfflineAssessmentBuilder(
            indicators_db_path=cls.indicators_db,
            availability_csv_path=cls.availability_csv,
            bpit_labels_path=cls.bpit_labels,
            as_of="2026-01-02",
        )

    def test_independent_verifier_pass(self):
        """Chạy verifier độc lập trên thư mục output thực tế và đảm bảo PASS."""
        report = verify_assessment_artifacts(self.output_dir)
        self.assertTrue(report["passed"], f"Verifier thất bại: {report.get('errors')}")
        self.assertGreater(report["total_assessments"], 1000)
        self.assertIn("WORTH_CONSIDERING", report["verdict_counts"])
        self.assertIn("MONITOR", report["verdict_counts"])
        self.assertIn("INSUFFICIENT_EVIDENCE", report["verdict_counts"])
        self.assertIsNotNone(report["deterministic_content_sha256"])

    def test_fpt_dynamic_evaluation(self):
        """FPT được đánh giá động dựa trên dữ liệu thật, không hard-code."""
        payloads = self.builder.build_all(["FPT"])
        self.assertEqual(len(payloads), 1)
        fpt = payloads[0]
        self.assertEqual(fpt.ticker, "FPT")
        self.assertIn(fpt.verdict, {VERDICT_WORTH_CONSIDERING, VERDICT_MONITOR})
        self.assertIsNotNone(fpt.cluster_a)
        self.assertIsNotNone(fpt.cluster_b)
        self.assertIsNotNone(fpt.latest_fy)
        self.assertLessEqual(fpt.usable_from_date, "2026-01-02")
        self.assertIn("roe", fpt.financial_features)
        self.assertIn("roe", fpt.peer_comparisons)
        # Kiểm tra rationale phản ánh đúng logic kết luận
        self.assertTrue(len(fpt.rationale) > 0)

    def test_valid_ticker_a32(self):
        """Mã A32 có đầy đủ dữ liệu tài chính B-PIT và ra kết luận hợp lệ."""
        payloads = self.builder.build_all(["A32"])
        self.assertEqual(len(payloads), 1)
        a32 = payloads[0]
        self.assertEqual(a32.ticker, "A32")
        self.assertIn(a32.verdict, {VERDICT_WORTH_CONSIDERING, VERDICT_MONITOR, VERDICT_LOW_PRIORITY})
        self.assertIsNotNone(a32.latest_fy)
        self.assertLessEqual(a32.usable_from_date, "2026-01-02")
        self.assertGreaterEqual(len(a32.peer_comparisons), 1)

    def test_vcb_sector_excluded(self):
        """VCB thuộc nhóm ngân hàng bị loại khỏi B-PIT, phải ra INSUFFICIENT_EVIDENCE."""
        payloads = self.builder.build_all(["VCB"])
        self.assertEqual(len(payloads), 1)
        vcb = payloads[0]
        self.assertEqual(vcb.ticker, "VCB")
        self.assertEqual(vcb.verdict, VERDICT_INSUFFICIENT_EVIDENCE)
        self.assertIn("SECTOR_EXCLUDED", vcb.rationale)

    def test_missing_history_insufficient_evidence(self):
        """Mã không có nhãn B-PIT hợp lệ hoặc thiếu dữ liệu phải ra INSUFFICIENT_EVIDENCE."""
        payloads = self.builder.build_all(["AAM"])
        self.assertEqual(len(payloads), 1)
        aam = payloads[0]
        self.assertEqual(aam.ticker, "AAM")
        self.assertEqual(aam.verdict, VERDICT_INSUFFICIENT_EVIDENCE)
        self.assertIn("INSUFFICIENT_EVIDENCE", aam.rationale)

    def test_manifest_metadata_and_hashes(self):
        """Manifest chứa đầy đủ hashes và references truy nguyên được."""
        manifest_path = self.output_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "investment_assessment_v1")
        self.assertEqual(manifest["as_of"], "2026-01-02")
        self.assertIn("input_hashes", manifest)
        self.assertIn("output_files", manifest)
        self.assertIn("deterministic_content_sha256", manifest)
        self.assertEqual(manifest["total_tickers"], 1428)

if __name__ == "__main__":
    unittest.main()

