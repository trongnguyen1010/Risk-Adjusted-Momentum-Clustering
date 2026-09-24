import unittest

from delta_t1.ingestion.cafef_primary_offline import (
    PRICE_BASIS_STATUS,
    build_discontinuity_candidates,
    build_field_coverage,
    normalize_price_history_row,
)


class CafeFPrimaryOfflineTests(unittest.TestCase):
    def setUp(self):
        self.plan_row = {
            "security_id": "SEC-ABC",
            "ticker": "ABC",
        }
        self.entry = {
            "exchange": "HOSE",
            "request_key": "request-1",
            "raw_path": "raw/ABC/page_0001.json",
            "sha256": "a" * 64,
            "fetched_at": "2026-09-24T00:00:00+00:00",
        }
        self.raw_row = {
            "Symbol": "ABC",
            "Ngay": "23/09/2021",
            "GiaDieuChinh": 9.5,
            "GiaDongCua": 10.0,
            "ThayDoi": "+0,10 (+1,01%)",
            "KhoiLuongKhopLenh": 1000,
            "GiaTriKhopLenh": 0.01,
            "KLThoaThuan": 200,
            "GtThoaThuan": 0.002,
            "GiaMoCua": 9.8,
            "GiaCaoNhat": 10.2,
            "GiaThapNhat": 9.7,
        }

    def _normalize(self, row=None):
        return normalize_price_history_row(
            row or self.raw_row,
            plan_row=self.plan_row,
            source_run_id="run-test",
            source_contract_version="CONTRACT-TEST",
            entry=self.entry,
            row_index=0,
        )

    def test_normalization_preserves_provider_components_and_provenance(self):
        result = self._normalize()
        self.assertEqual("2021-09-23", result["trade_date"])
        self.assertEqual(9800.0, result["provider_open_vnd"])
        self.assertEqual(10000.0, result["provider_close_vnd"])
        self.assertEqual(10_000_000.0, result["matched_value_vnd"])
        self.assertEqual(200, result["negotiated_volume_shares"])
        self.assertEqual(PRICE_BASIS_STATUS, result["price_basis_status"])
        self.assertEqual("CANDIDATE_ONLY_NOT_CANONICAL", result["canonical_promotion_status"])
        self.assertEqual(self.entry["sha256"], result["raw_sha256"])

    def test_normalization_rejects_symbol_mismatch_and_missing_field(self):
        mismatch = dict(self.raw_row, Symbol="XYZ")
        with self.assertRaisesRegex(ValueError, "symbol"):
            self._normalize(mismatch)
        missing = dict(self.raw_row)
        del missing["GiaDongCua"]
        with self.assertRaisesRegex(ValueError, "missing source fields"):
            self._normalize(missing)

    def test_field_coverage_does_not_claim_full_canonical_readiness(self):
        fields, tables = build_field_coverage([self._normalize()])
        by_table = {row["table"]: row for row in tables}
        self.assertEqual("CANDIDATE_ONLY_MANUAL_REVIEW_REQUIRED", by_table["prices_daily"]["table_status"])
        self.assertEqual(
            "NOT_FILLABLE_FROM_CURRENT_PRICEHISTORY_RAW",
            by_table["corporate_actions"]["table_status"],
        )
        self.assertEqual(
            "NOT_FILLABLE_FROM_CURRENT_PRICEHISTORY_RAW",
            by_table["financial_reports"]["table_status"],
        )
        raw_close = next(row for row in fields if row["table"] == "prices_daily" and row["field"] == "raw_close")
        self.assertEqual("AVAILABLE_BUT_BLOCKED", raw_close["coverage_state"])
        self.assertEqual("provider_close_vnd", raw_close["candidate_source_field"])
        self.assertEqual(1.0, raw_close["observed_non_null_rate"])
        self.assertEqual("NO", raw_close["canonical_fill_status"])

    def test_discontinuity_is_diagnostic_not_corporate_action_proof(self):
        first = self._normalize()
        second_raw = dict(self.raw_row, Ngay="24/09/2021", GiaDongCua=5.0, GiaDieuChinh=5.0)
        second = self._normalize(second_raw)
        findings = build_discontinuity_candidates([first, second])
        self.assertEqual(1, len(findings))
        self.assertIn("RAW_CLOSE_MOVE_GE_20_PERCENT", findings[0]["diagnostic_flags"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_CORPORATE_ACTION_PROOF", findings[0]["evidence_status"])


if __name__ == "__main__":
    unittest.main()
