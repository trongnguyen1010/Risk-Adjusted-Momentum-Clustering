import unittest
from unittest.mock import patch
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.contracts import validate_rows
from delta_t1.ingestion.representative_pilot_canonical import (
    _build_securities, _calendar, _latest_stamp, load_security_master,
)


class RepresentativePilotCanonicalTests(unittest.TestCase):
    def test_observed_calendar_marks_last_session_of_month(self):
        rows = [
            {"exchange": "HOSE", "trade_date": "2026-08-28"},
            {"exchange": "HOSE", "trade_date": "2026-08-31"},
            {"exchange": "HOSE", "trade_date": "2026-09-01"},
            {"exchange": "HNX", "trade_date": "2026-08-28"},
        ]
        calendar = _calendar(rows, "canonical-test", "2026-09-17T00:00:00+00:00")
        validate_rows("trading_calendar", calendar)
        month_ends = {(row["exchange"], row["trade_date"])
                      for row in calendar if row["is_month_end"]}
        self.assertEqual({("HOSE", "2026-08-31"), ("HOSE", "2026-09-01"),
                          ("HNX", "2026-08-28")}, month_ends)

    def test_latest_fetch_compares_timezone_aware_instants(self):
        self.assertEqual(
            "2026-09-17T01:00:00+07:00",
            _latest_stamp("2026-09-16T17:00:00+00:00", "2026-09-17T01:00:00+07:00"),
        )

    def _master(self, rows):
        return {
            "schema_version": "1.0.0",
            "purpose": "REPRESENTATIVE_PILOT_SECURITY_MASTER",
            "identity_scope": "PILOT_OBSERVED_INTERVAL_ONLY",
            "identity_status": "provisional_verified_for_pilot",
            "source_evidence": {
                "source": "kbs_delta_public_http", "http_status": 200,
                "selected_row_count": len(rows), "response_sha256": "a" * 64,
                "fetched_at": "2026-09-17T13:20:14+07:00",
            },
            "securities": rows,
        }

    def test_security_master_requires_exact_universe_and_exchange(self):
        universe = [{"security_id": "VCI:1", "ticker": "AAA", "exchange": "HOSE",
                     "sector": "Chemicals", "listing_date": "2016-11-25"}]
        row = {"ticker": "AAA", "company_name": "AAA Company", "exchange": "HOSE",
               "instrument_type": "stock"}
        path = ROOT / "not-read-securities.json"
        with patch("delta_t1.ingestion.representative_pilot_canonical.read_json",
                   return_value=self._master([row])):
            _, _, by_ticker = load_security_master(path, universe)
            self.assertEqual({"AAA"}, set(by_ticker))
        changed = self._master([dict(row, exchange="HNX")])
        with patch("delta_t1.ingestion.representative_pilot_canonical.read_json",
                   return_value=changed):
            with self.assertRaisesRegex(ValueError, "exchange mismatch"):
                load_security_master(path, universe)

    def test_security_master_rejects_missing_extra_and_non_stock(self):
        universe = [{"security_id": "VCI:1", "ticker": "AAA", "exchange": "HOSE"}]
        base = {"ticker": "AAA", "company_name": "AAA Company", "exchange": "HOSE",
                "instrument_type": "stock"}
        cases = [[], [base, dict(base, ticker="BBB")], [dict(base, instrument_type="fund")]]
        path = ROOT / "not-read-securities.json"
        for rows in cases:
            document = self._master(rows)
            document["source_evidence"]["selected_row_count"] = len(universe)
            with patch("delta_t1.ingestion.representative_pilot_canonical.read_json",
                       return_value=document):
                with self.assertRaises(ValueError):
                    load_security_master(path, universe)

    def test_build_securities_uses_first_observed_price_not_listing_date(self):
        universe = [{"security_id": "VCI:1", "ticker": "AAA", "exchange": "HOSE",
                     "sector": "Chemicals", "listing_date": "2016-11-25"}]
        master = self._master([{
            "ticker": "AAA", "company_name": "AAA Company", "exchange": "HOSE",
            "instrument_type": "stock",
        }])
        prices = [
            {"security_id": "VCI:1", "ticker": "AAA", "exchange": "HOSE",
             "trade_date": "2020-01-03"},
            {"security_id": "VCI:1", "ticker": "AAA", "exchange": "HOSE",
             "trade_date": "2020-01-02"},
        ]
        rows = _build_securities(universe, master, prices, "canonical-test")
        validate_rows("securities", rows)
        self.assertEqual("2020-01-02", rows[0]["valid_from"])
        self.assertEqual("2020-01-02T17:00:00+07:00", rows[0]["available_at"])
        self.assertEqual("provisional_verified_for_pilot", rows[0]["identity_status"])


if __name__ == "__main__":
    unittest.main()
