import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.contracts import validate_rows
from delta_t1.ingestion.representative_pilot_canonical import _calendar, _latest_stamp


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


if __name__ == "__main__":
    unittest.main()
