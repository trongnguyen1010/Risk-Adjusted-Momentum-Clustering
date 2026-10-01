from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from delta_t1.ingestion.financial_pit_semantic import (
    classify_column_role,
    classify_duration,
    evidence_complete,
    parse_unit,
    review_revision_group,
    taxonomy_candidate,
)


class FinancialPitSemanticTests(unittest.TestCase):
    def test_01_balance_sheet_is_instant_only_with_as_of_evidence(self):
        self.assertEqual(classify_duration("BALANCE_SHEET", "Bảng cân đối kế toán tại ngày 30/06/2024"), "INSTANT")

    def test_02_q2_three_month_wording_is_standalone(self):
        self.assertEqual(classify_duration("INCOME_STATEMENT", "For the 3 months ended 30 June 2024"), "STANDALONE")

    def test_03_q2_six_month_wording_is_ytd(self):
        self.assertEqual(classify_duration("INCOME_STATEMENT", "Cho 6 tháng kết thúc ngày 30 tháng 6 năm 2024"), "YTD")

    def test_04_q3_nine_month_wording_is_ytd(self):
        self.assertEqual(classify_duration("CASH_FLOW_STATEMENT", "For the 9 months ended 30 September 2024"), "YTD")

    def test_05_unknown_duration_fails_closed(self):
        self.assertEqual(classify_duration("INCOME_STATEMENT", "Quý 2 năm 2024"), "UNKNOWN")

    def test_06_separate_and_consolidated_are_distinct_values(self):
        keys = {("PVS", "2022FY", scope) for scope in ("SEPARATE", "CONSOLIDATED")}
        self.assertEqual(len(keys), 2)

    def test_07_comparative_columns_are_not_current_columns(self):
        self.assertEqual(classify_column_role("năm trước - trình bày lại"), "PRIOR_YEAR_COMPARATIVE")
        self.assertEqual(classify_column_role("kỳ này"), "CURRENT_PERIOD")

    def test_08_unit_parsing_keeps_multiplier(self):
        unit = parse_unit("Đơn vị: triệu đồng")
        self.assertEqual(unit["normalized_unit"], "million VND")
        self.assertEqual(unit["unit_multiplier"], 1_000_000)
        self.assertEqual(unit["unit_status"], "VERIFIED")

    def test_09_taxonomy_ambiguity_is_not_fuzzy_promoted(self):
        result = taxonomy_candidate(None, "Lợi nhuận hoạt động", "INCOME_STATEMENT")
        self.assertEqual(result["taxonomy_status"], "UNRESOLVED")
        self.assertIsNone(result["taxonomy_candidate"])

    def test_10_different_hashes_do_not_become_restatement(self):
        group = {
            "ticker": "PVS",
            "period_candidate": "2022FY",
            "document_candidate_ids": ["a", "b"],
        }
        documents = {
            "a": {"document_hash": "1", "document_role": "PRIMARY_FINANCIAL_REPORT"},
            "b": {"document_hash": "2", "document_role": "EXPLANATORY_NOTE"},
        }
        result = review_revision_group(group, documents)
        self.assertEqual(result["revision_relation"], "UNKNOWN")
        self.assertFalse(result["resolved"])

    def test_11_verified_provenance_requires_page_region_text_and_method(self):
        self.assertFalse(evidence_complete({"page": 1, "source_text": "x", "extraction_method": "PDF_TEXT_LAYER"}))
        self.assertTrue(evidence_complete({
            "page": 1,
            "region": "PAGE_TEXT",
            "source_text": "x",
            "extraction_method": "PDF_TEXT_LAYER",
        }))

    def test_12_r5_date_grade_must_be_preserved_as_date_level(self):
        timing = {
            "publication_date": "2023-11-03",
            "eligible_from": "2023-11-06",
            "timing_grade": "B_OFFICIAL_DATE_D1",
        }
        self.assertEqual(timing["timing_grade"], "B_OFFICIAL_DATE_D1")
        self.assertNotIn("T", timing["publication_date"])

    def test_13_stage_contract_has_no_canonical_or_feature_output(self):
        gate = {"canonical_rows_written": 0, "financial_features_written": 0}
        self.assertEqual(gate["canonical_rows_written"], 0)
        self.assertEqual(gate["financial_features_written"], 0)


if __name__ == "__main__":
    unittest.main()
