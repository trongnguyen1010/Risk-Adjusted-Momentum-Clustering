import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.reconciliation.candidates import (
    KEY_FIELDS, candidate_from_row, financial_report_comparison_key,
)
from delta_t1.ingestion.reconciliation.rules import (
    SourcePriorityPolicy, reconcile_candidates,
)
from delta_t1.ingestion.sources.cafef import CafeFSource
from delta_t1.ingestion.sources.vietfin import VietFinSource


class SourceBoundaryTests(unittest.TestCase):
    def test_unverified_sources_fail_closed(self):
        for source in (CafeFSource(), VietFinSource()):
            with self.assertRaisesRegex(ValueError, "not verified"):
                source.acquire({"symbol": "FPT"})

    def market_candidate(self, source, close=100000, volume=5000000,
                         basis="unadjusted", fetched="2025-01-03T00:00:00+00:00",
                         field_semantics=None):
        row = {
            "security_id": "SEC-FPT", "ticker": "FPT", "exchange": "HOSE",
            "trade_date": "2025-01-02", "raw_open": 99000, "raw_high": 101000,
            "raw_low": 98000, "raw_close": close, "adj_close": None,
            "reference_price": 99000, "ceiling_price": 105000, "floor_price": 93000,
            "adjustment_basis": basis, "volume": volume, "traded_value": 500000000000,
            "trading_status": "normal", "available_at": "2025-01-02T17:00:00+07:00",
            "source": source, "fetched_at": fetched, "data_version": "v1",
        }
        return candidate_from_row(
            "prices_daily", row, raw_hash="hash-" + source,
            field_semantics=field_semantics,
        )

    def test_field_match_ignores_fetch_metadata(self):
        rows, decisions, conflicts = reconcile_candidates([
            self.market_candidate("cafef", fetched="2025-01-03T00:00:00+00:00"),
            self.market_candidate("vietfin", fetched="2025-01-04T00:00:00+00:00"),
        ])
        self.assertEqual(1, len(rows["prices_daily"]))
        self.assertFalse(conflicts)
        close = next(item for item in decisions if item["field"] == "raw_close")
        self.assertEqual("MATCH", close["status"])
        self.assertEqual(["cafef", "vietfin"], close["candidate_sources"])
        self.assertEqual(["hash-cafef", "hash-vietfin"], close["raw_hashes"])

    def test_value_conflict_is_not_averaged(self):
        rows, decisions, conflicts = reconcile_candidates([
            self.market_candidate("cafef", volume=5000000),
            self.market_candidate("vietfin", volume=5000),
        ])
        self.assertFalse(rows)
        volume = next(item for item in decisions if item["field"] == "volume")
        self.assertEqual("VALUE_CONFLICT", volume["status"])
        self.assertEqual("UNRESOLVED", volume["resolution_status"])
        self.assertEqual("VALUE_CONFLICT", conflicts[0]["status"])

    def test_missing_timing_and_identity_statuses_are_distinct(self):
        missing = self.market_candidate("vietfin")
        missing.row["traded_value"] = None
        rows, decisions, conflicts = reconcile_candidates([
            self.market_candidate("cafef"), missing,
        ])
        self.assertFalse(conflicts)
        self.assertEqual("MISSING_ON_SOURCE",
                         next(item for item in decisions if item["field"] == "traded_value")["status"])
        self.assertTrue(rows)
        late = self.market_candidate("vietfin")
        late.row["available_at"] = "2025-01-03T17:00:00+07:00"
        _, _, timing = reconcile_candidates([self.market_candidate("cafef"), late])
        self.assertIn("TIMING_CONFLICT", {item["status"] for item in timing})
        wrong_ticker = self.market_candidate("vietfin")
        wrong_ticker.row["ticker"] = "FPT-OLD"
        _, _, identity = reconcile_candidates([self.market_candidate("cafef"), wrong_ticker])
        self.assertIn("IDENTITY_CONFLICT", {item["status"] for item in identity})

    def test_declared_unit_and_price_basis_conflicts_are_distinct(self):
        _, _, unit_conflicts = reconcile_candidates([
            self.market_candidate("cafef", field_semantics={"volume": {"unit": "shares"}}),
            self.market_candidate("vietfin", volume=5000,
                                  field_semantics={"volume": {"unit": "lots_1000"}}),
        ])
        self.assertIn("UNIT_CONFLICT", {item["status"] for item in unit_conflicts})
        _, _, basis_conflicts = reconcile_candidates([
            self.market_candidate("cafef", basis="unadjusted"),
            self.market_candidate("vietfin", basis="vendor_adjusted"),
        ])
        self.assertIn("PRICE_BASIS_CONFLICT", {item["status"] for item in basis_conflicts})

    def test_approved_priority_records_resolution(self):
        policy = SourcePriorityPolicy.from_dict({
            "approved": True, "sources": ["cafef", "vietfin"],
            "rule_id": "SRC-01", "version": "1.0", "reason": "Reviewed field policy",
        })
        rows, decisions, conflicts = reconcile_candidates([
            self.market_candidate("cafef", volume=5000000),
            self.market_candidate("vietfin", volume=4999999),
        ], policy)
        self.assertFalse(conflicts)
        self.assertEqual(5000000, rows["prices_daily"][0]["volume"])
        decision = next(item for item in decisions if item["field"] == "volume")
        self.assertEqual(("SRC-01", "1.0", "cafef"),
                         (decision["rule_id"], decision["rule_version"], decision["chosen_source"]))

    def test_financial_keys_keep_statement_type_and_compare_semantically(self):
        self.assertEqual(("report_id", "statement_type", "item_code"),
                         KEY_FIELDS["financial_facts"])
        base = {
            "security_id": "SEC-FPT", "fiscal_year": 2025, "fiscal_quarter": 2,
            "period_end": "2025-06-30", "statement_scope": "consolidated", "revision": 1,
        }
        self.assertEqual(financial_report_comparison_key(dict(base, report_id="CAFEF-1")),
                         financial_report_comparison_key(dict(base, report_id="VIETFIN-9")))
        fact_a = {"report_id": "CAFEF-1", "security_id": "SEC-FPT",
                  "statement_type": "income_statement", "item_code": "REVENUE",
                  "value": 100, "currency": "VND", "unit_scale": 1000000,
                  "source": "cafef", "fetched_at": "2025-08-01T00:00:00+00:00"}
        fact_b = dict(fact_a, report_id="VIETFIN-9", source="vietfin",
                      fetched_at="2025-08-02T00:00:00+00:00")
        report_key = financial_report_comparison_key(base)
        left = candidate_from_row("financial_facts", fact_a, report_comparison_key=report_key)
        right = candidate_from_row("financial_facts", fact_b, report_comparison_key=report_key)
        self.assertEqual(left.comparison_key, right.comparison_key)


if __name__ == "__main__":
    unittest.main()
