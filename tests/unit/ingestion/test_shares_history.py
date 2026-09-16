import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.contracts import validate_rows
from delta_t1.ingestion.quality import clean_tables
from delta_t1.ingestion.reconciliation.candidates import candidate_from_row


class SharesHistoryTests(unittest.TestCase):
    def shares_row(self, **overrides):
        row = {
            "security_id": "SEC-FPT",
            "effective_date": "2025-01-01",
            "available_at": "2025-01-02T09:00:00+07:00",
            "listed_shares": None,
            "outstanding_shares": 1_000_000,
            "issued_shares": None,
            "treasury_shares": None,
            "source": "test",
            "fetched_at": "2025-01-02T10:00:00+07:00",
            "data_version": "v1",
        }
        row.update(overrides)
        return row

    def security_row(self):
        return {
            "security_id": "SEC-FPT", "ticker": "FPT", "company_name": "FPT Corp",
            "exchange": "HOSE", "listing_date": "2006-12-13", "delisting_date": None,
            "valid_from": "2006-12-13", "valid_to": None,
            "available_at": "2025-01-01T00:00:00+07:00", "sector": None,
            "industry": None, "currency": "VND", "price_unit": "VND",
            "identity_status": "verified", "source": "test",
            "fetched_at": "2025-01-02T10:00:00+07:00", "data_version": "v1",
        }

    def clean(self, row):
        raw = {
            "securities": [(self.security_row(), {"source": "test"}, "2025-01-02T10:00:00+07:00")],
            "shares_history": [(row, {"source": "test"}, row["fetched_at"])],
        }
        return clean_tables(raw, "v1")

    def test_schema_accepts_only_outstanding_shares(self):
        validate_rows("shares_history", [self.shares_row()])

    def test_schema_accepts_all_share_counts(self):
        validate_rows("shares_history", [self.shares_row(
            listed_shares=1_200_000, issued_shares=1_100_000, treasury_shares=100_000
        )])

    def test_schema_rejects_negative_share_count(self):
        with self.assertRaisesRegex(ValueError, "below minimum"):
            validate_rows("shares_history", [self.shares_row(listed_shares=-1)])

    def test_qc_rejects_unknown_security(self):
        tables, issues, _ = self.clean(self.shares_row(security_id="SEC-UNKNOWN"))
        self.assertFalse(tables["shares_history"])
        self.assertIn("SHARES_FOREIGN_KEY", {issue["rule_id"] for issue in issues})

    def test_qc_rejects_all_counts_null(self):
        row = self.shares_row(outstanding_shares=None)
        tables, issues, _ = self.clean(row)
        self.assertFalse(tables["shares_history"])
        self.assertIn("SHARES_EMPTY", {issue["rule_id"] for issue in issues})

    def test_qc_rejects_fetch_before_availability(self):
        row = self.shares_row(fetched_at="2025-01-02T08:00:00+07:00")
        tables, issues, _ = self.clean(row)
        self.assertFalse(tables["shares_history"])
        self.assertIn("SHARES_AVAILABILITY", {issue["rule_id"] for issue in issues})

    def test_qc_accepts_availability_before_effective_date(self):
        row = self.shares_row(
            effective_date="2025-02-01",
            available_at="2025-01-15T09:00:00+07:00",
            fetched_at="2025-01-15T10:00:00+07:00",
        )
        tables, issues, _ = self.clean(row)
        self.assertEqual([row], tables["shares_history"])
        self.assertFalse(issues)

    def test_reconciliation_key_uses_security_and_effective_date(self):
        candidate = candidate_from_row("shares_history", self.shares_row())
        self.assertEqual(("SEC-FPT", "2025-01-01"), candidate.canonical_key)
        self.assertEqual(candidate.canonical_key, candidate.comparison_key)


if __name__ == "__main__":
    unittest.main()
