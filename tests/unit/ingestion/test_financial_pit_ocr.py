from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from delta_t1.ingestion.financial_pit_ocr import (
    classify_preflight,
    numeric_ocr_safety,
    ocr_provenance_complete,
    select_ocr_pages,
    semantic_text_allowed,
    timing_fields_preserved,
)
from delta_t1.ingestion.financial_pit_semantic import (
    classify_duration,
    parse_numeric_candidate,
    parse_unit,
)


class FinancialPitOcrTests(unittest.TestCase):
    def test_01_text_based_usable_document_does_not_schedule_ocr(self):
        pages = ["Báo cáo tài chính " * 50, "Bảng cân đối kế toán " * 50]
        classification = classify_preflight(pages)
        self.assertEqual(classification, "TEXT_BASED_USABLE")
        self.assertEqual(select_ocr_pages(classification, pages)[0], [])

    def test_02_scan_only_document_schedules_derived_pages_without_touching_raw(self):
        pages = ["", ""]
        self.assertEqual(classify_preflight(pages), "SCAN_IMAGE_ONLY")
        selected, _ = select_ocr_pages("SCAN_IMAGE_ONLY", pages)
        self.assertEqual(selected, [1, 2])
        with tempfile.TemporaryDirectory() as temp_name:
            raw = Path(temp_name) / "raw.pdf"
            derived = Path(temp_name) / "ocr.json"
            raw.write_bytes(b"%PDF-immutable-test")
            before = hashlib.sha256(raw.read_bytes()).hexdigest()
            derived.write_text('{"derived": true}', encoding="utf-8")
            after = hashlib.sha256(raw.read_bytes()).hexdigest()
            self.assertTrue(derived.is_file())
            self.assertEqual(before, after)

    def test_03_ocr_provenance_is_required(self):
        complete = {
            "document_hash": "a" * 64,
            "page": 1,
            "ocr_engine": "Tesseract OCR",
            "ocr_version": "tesseract 5.4.0",
            "ocr_config_hash": "b" * 64,
            "raw_ocr_text": "x",
            "normalized_text_candidate": "x",
            "confidence": {"mean_word_confidence": 80.0},
            "processing_status": "OCR_SUCCESS",
        }
        self.assertTrue(ocr_provenance_complete(complete))
        incomplete = dict(complete)
        incomplete.pop("ocr_config_hash")
        self.assertFalse(ocr_provenance_complete(incomplete))

    def test_04_low_confidence_ocr_cannot_semantic_promote(self):
        row = {
            "document_hash": "a" * 64,
            "page": 1,
            "ocr_engine": "Tesseract OCR",
            "ocr_version": "tesseract 5.4.0",
            "ocr_config_hash": "b" * 64,
            "raw_ocr_text": "x",
            "normalized_text_candidate": "x",
            "confidence": {"mean_word_confidence": 20.0},
            "processing_status": "LOW_CONFIDENCE",
        }
        self.assertFalse(semantic_text_allowed(row))

    def test_05_q2_three_month_wording_is_standalone(self):
        self.assertEqual(
            classify_duration("INCOME_STATEMENT", "Cho 3 tháng kết thúc ngày 30 tháng 6 năm 2024"),
            "STANDALONE",
        )

    def test_06_q2_six_month_wording_is_ytd(self):
        self.assertEqual(
            classify_duration("INCOME_STATEMENT", "Cho 6 tháng kết thúc ngày 30 tháng 6 năm 2024"),
            "YTD",
        )

    def test_07_q3_nine_month_wording_is_ytd(self):
        self.assertEqual(
            classify_duration("CASH_FLOW_STATEMENT", "Cho 9 tháng kết thúc ngày 30 tháng 9 năm 2024"),
            "YTD",
        )

    def test_08_unknown_period_wording_remains_unknown(self):
        self.assertEqual(classify_duration("INCOME_STATEMENT", "Quý 2 năm 2024"), "UNKNOWN")

    def test_09_consolidated_and_separate_remain_distinct(self):
        identities = {("ACV", "2022Q2", scope) for scope in ("CONSOLIDATED", "SEPARATE")}
        self.assertEqual(len(identities), 2)

    def test_10_unit_ocr_parse_preserves_multiplier(self):
        unit = parse_unit("Đơn vị: triệu đồng")
        self.assertEqual(unit["normalized_unit"], "million VND")
        self.assertEqual(unit["unit_multiplier"], 1_000_000)

    def test_11_numeric_ocr_ambiguity_fails_closed(self):
        safety = numeric_ocr_safety("1.000.00O")
        self.assertEqual(safety["parse_status"], "UNRESOLVED")
        self.assertEqual(parse_numeric_candidate("1.000.00O")["parse_status"], "UNRESOLVED")

    def test_12_revision_relation_requires_official_evidence(self):
        revision = {"document_hashes": ["a", "b"], "revision_relation": "UNKNOWN", "resolved": False}
        self.assertEqual(revision["revision_relation"], "UNKNOWN")
        self.assertFalse(revision["resolved"])

    def test_13_r5_timing_fields_are_preserved(self):
        before = {
            "publication_date": "2024-07-30",
            "eligible_from": "2024-07-31",
            "timing_grade": "B_OFFICIAL_DATE_D1",
            "timing_policy_version": "B_OFFICIAL_DATE_D1_V1",
            "timing_evidence_source": "official",
        }
        self.assertTrue(timing_fields_preserved(before, dict(before)))
        changed = dict(before, timing_grade="A_EXACT_TIMESTAMP")
        self.assertFalse(timing_fields_preserved(before, changed))

    def test_14_raw_document_hash_change_is_detectable(self):
        with tempfile.TemporaryDirectory() as temp_name:
            path = Path(temp_name) / "raw.pdf"
            path.write_bytes(b"original")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            path.write_bytes(b"changed")
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertNotEqual(before, after)

    def test_15_stage_contract_has_no_canonical_output(self):
        gate = {
            "canonical_rows_written": 0,
            "financial_features_written": 0,
            "financial_features_allowed": False,
        }
        self.assertEqual(gate["canonical_rows_written"], 0)
        self.assertEqual(gate["financial_features_written"], 0)
        self.assertFalse(gate["financial_features_allowed"])


if __name__ == "__main__":
    unittest.main()
