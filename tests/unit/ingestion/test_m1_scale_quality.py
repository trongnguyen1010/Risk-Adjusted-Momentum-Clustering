import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.features.market import (
    latest_completed_month_cutoff, latest_completed_snapshot_rows,
)
from delta_t1.ingestion.m1_scale_quality import (
    _five_calendar_years, _history_evidence, _markdown, _three_calendar_years,
)


class M1ScaleQualityTests(unittest.TestCase):
    def test_calendar_year_coverage_is_span_evidence_not_usable_label(self):
        self.assertTrue(_three_calendar_years("2021-09-15", "2024-09-15"))
        self.assertFalse(_three_calendar_years("2021-09-16", "2024-09-15"))
        self.assertTrue(_five_calendar_years("2020-02-29", "2025-02-28"))
        self.assertFalse(_five_calendar_years("2020-03-01", "2025-02-28"))

    def test_sparse_long_span_is_distinct_from_dense_history(self):
        sessions = ["2020-01-02", "2020-01-03", "2026-01-02"]
        sparse = _history_evidence([sessions[0], sessions[-1]], sessions)
        dense = _history_evidence(sessions, sessions)
        self.assertTrue(sparse["observed_span_5y"])
        self.assertEqual(2, sparse["price_rows"])
        self.assertEqual(1, sparse["missing_sessions_in_observed_range"])
        self.assertLess(sparse["observed_session_coverage"], dense["observed_session_coverage"])
        self.assertNotIn("usable_5y", sparse)

    def test_partial_current_month_selects_completed_prior_month(self):
        rows = [
            {"security_id": "A", "as_of_date": "2026-08-31"},
            {"security_id": "A", "as_of_date": "2026-09-15"},
        ]
        self.assertEqual("2026-08-31", latest_completed_month_cutoff("2026-09-15"))
        snapshot, selected = latest_completed_snapshot_rows(rows, "2026-09-15")
        self.assertEqual("2026-08-31", snapshot)
        self.assertEqual("2026-08-31", selected["A"]["as_of_date"])

    def test_completed_current_month_can_be_selected(self):
        rows = [
            {"security_id": "A", "as_of_date": "2026-08-31"},
            {"security_id": "A", "as_of_date": "2026-09-30"},
        ]
        snapshot, _ = latest_completed_snapshot_rows(rows, "2026-09-30")
        self.assertEqual("2026-09-30", snapshot)

    def test_markdown_review_count_is_dynamic(self):
        report = {
            "generated_at": "2026-09-18T00:00:00+00:00",
            "canonical_run_id": "canonical-test", "candidate_id": "candidate-test",
            "m1_status": "PARTIAL",
            "summary": {
                "selected_symbols": 10, "observed_span_3y": 10,
                "observed_span_5y": 9, "prices_daily": 100,
                "benchmark_daily": 10, "feature_snapshots": 20,
                "latest_completed_snapshot": "2026-08-31",
                "latest_feature_complete": 7, "market_feature_ready": 7,
                "historical_identity_ready": 0, "research_ready": 0,
                "legacy_scoped_eligible": 0, "quarantined_rows": 2,
            },
            "latest_feature_coverage": {"mom_21": {"available": 7, "missing": 3}},
            "price_rows_distribution": {
                "minimum": 1, "p25": 2, "median": 3, "p75": 4, "maximum": 5,
            },
            "session_coverage_distribution": {
                "minimum": .2, "p25": .4, "median": .6, "p75": .8, "maximum": 1,
            },
            "exchange_coverage": {"HOSE": {"securities": 10, "price_rows": 100}},
            "market_missingness": {
                "traded_value_missing_rows": 1, "traded_value_missing_ratio": .01,
                "volume_missing_rows": 0, "volume_zero_rows": 0,
            },
            "quarantine_by_provider": {"kbs": 1, "cafef": 1},
            "exclusion_reason_counts": {"feature:mom_21": 3},
        }
        row = {
            "ticker": "AAA", "exchange": "HOSE",
            "observed_first_date": "2020-01-01", "observed_last_date": "2026-08-31",
            "price_rows": 5, "observed_span_5y": True,
            "observed_session_coverage": 1, "recent_lookback_observations": 5,
            "latest_feature_complete": False, "market_feature_ready": False,
            "historical_identity_ready": False, "research_ready": False,
        }
        text = _markdown(report, [row]).decode("utf-8")
        self.assertIn("Review 3 mã thiếu required feature", text)
        self.assertNotIn("Review 332", text)


if __name__ == "__main__":
    unittest.main()
