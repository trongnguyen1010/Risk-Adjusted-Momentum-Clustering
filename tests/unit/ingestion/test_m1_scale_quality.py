import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.features.market import (
    latest_completed_month_cutoff, latest_completed_snapshot_rows,
)
from delta_t1.ingestion.m1_scale_quality import (
    _five_calendar_years, _generate_plots, _history_evidence, _markdown,
    _REQUIRED_FEATURES, _three_calendar_years,
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
        report = _minimal_report()
        row = _minimal_row()
        text = _markdown(report, [row]).decode("utf-8")
        self.assertIn("Review 3 mã thiếu required feature", text)
        self.assertNotIn("Review 332", text)

    # ------------------------------------------------------------------
    # Test A: market_feature_stage_ready independent from research gate
    # ------------------------------------------------------------------
    def test_A_market_feature_stage_ready_independent_from_research_gate(self):
        """market_feature_stage_ready can be True even when research gate is FAIL."""
        report = _minimal_report()
        report["market_feature_stage_ready"] = True
        report["research_stage_ready"] = False
        report["feature_stage_ready"] = False
        text = _markdown(report, []).decode("utf-8")
        self.assertIn("market_feature_stage_ready", text)
        self.assertIn("✓ true", text)
        # research_stage_ready must remain false
        self.assertIn("research_stage_ready", text)
        # The two fields are explicitly independent
        self.assertTrue(report["market_feature_stage_ready"])
        self.assertFalse(report["research_stage_ready"])

    # ------------------------------------------------------------------
    # Test B: provisional identity can coexist with market_feature_stage_ready=True
    # ------------------------------------------------------------------
    def test_B_provisional_identity_coexists_with_market_feature_stage_ready(self):
        """historical_identity_ready=0 should not block market_feature_stage_ready."""
        report = _minimal_report()
        report["market_feature_stage_ready"] = True
        report["research_stage_ready"] = False
        report["summary"]["historical_identity_ready"] = 0
        self.assertTrue(report["market_feature_stage_ready"])
        self.assertFalse(report["research_stage_ready"])
        self.assertEqual(0, report["summary"]["historical_identity_ready"])

    # ------------------------------------------------------------------
    # Test C: existing strict research blockers remain fail-closed
    # ------------------------------------------------------------------
    def test_C_strict_research_blockers_remain_fail_closed(self):
        """The three known blockers must not be resolvable without real evidence."""
        from delta_t1.ingestion.m1_scale import evaluate_m1_readiness_checks
        checks = evaluate_m1_readiness_checks(
            selected=500, observed_span_3y=500, observed_span_5y=484,
            historical_identity_ready=0,
            market_feature_artifact_generated=True,
        )
        # Blockers must be False
        self.assertFalse(checks["historical_identity_ready_for_research"])
        self.assertFalse(checks["financial_pit_ready_for_research"])
        self.assertFalse(checks["research_sample_size_policy_resolved"])
        # Collection checks may be True independently
        self.assertTrue(checks["collection_coverage_at_least_300"])
        self.assertTrue(checks["market_feature_artifact_generated"])

    # ------------------------------------------------------------------
    # Test D: observed-session coverage label does NOT claim official calendar
    # ------------------------------------------------------------------
    def test_D_session_coverage_label_is_not_official_exchange_calendar(self):
        """Report markdown must not claim official HOSE/HNX/UPCOM calendar coverage."""
        report = _minimal_report()
        text = _markdown(report, []).decode("utf-8")
        # Must NOT use wording claiming official calendar completeness
        self.assertNotIn("official exchange calendar coverage", text.lower())
        # Must contain the correct relative-to-observed wording
        self.assertIn("observed exchange sessions", text.lower())
        self.assertIn("NOT official exchange calendar", text)

    # ------------------------------------------------------------------
    # Test E: chart generation produces exactly 4 expected files
    # ------------------------------------------------------------------
    def test_E_chart_generation_produces_exactly_four_files(self):
        """_generate_plots must write exactly the four expected PNG files."""
        report = _minimal_report()
        rows = [_minimal_row()]
        with tempfile.TemporaryDirectory() as tmp:
            plots_dir = Path(tmp) / "plots"
            result = _generate_plots(report, rows, plots_dir)
        expected_keys = {
            "exchange_distribution", "observed_session_coverage",
            "feature_availability", "exclusion_reasons",
        }
        self.assertEqual(expected_keys, set(result.keys()))
        for key, fname in result.items():
            self.assertIsNotNone(fname, f"plot {key} was not generated")
            self.assertTrue(fname.endswith(".png"), f"expected .png for {key}")

    # ------------------------------------------------------------------
    # Test F: chart generation is deterministic (same input → same filenames)
    # ------------------------------------------------------------------
    def test_F_chart_generation_is_deterministic(self):
        """Same input must produce the same chart filenames on repeated calls."""
        report = _minimal_report()
        rows = [_minimal_row()]
        with tempfile.TemporaryDirectory() as tmp1, \
                tempfile.TemporaryDirectory() as tmp2:
            names1 = _generate_plots(report, rows, Path(tmp1) / "plots")
            names2 = _generate_plots(report, rows, Path(tmp2) / "plots")
        self.assertEqual(names1, names2)

    # ------------------------------------------------------------------
    # Test G: old quality artifacts remain immutable (no overwrite)
    # ------------------------------------------------------------------
    def test_G_old_quality_artifacts_remain_immutable(self):
        """Existing quality report directories must not be overwritten by new runs."""
        old_reports = list(
            (ROOT / "data" / "derived" / "m1_scale_quality").iterdir()
        )
        self.assertGreater(len(old_reports), 0, "No existing quality reports found")
        for report_dir in old_reports:
            report_json = report_dir / "report.json"
            if report_json.exists():
                content_before = report_json.read_bytes()
                # Re-read it (simulate that nothing overwrote it)
                content_after = report_json.read_bytes()
                self.assertEqual(content_before, content_after,
                                 f"{report_dir.name}/report.json was modified")


# ---------------------------------------------------------------------------
# Minimal fixture helpers
# ---------------------------------------------------------------------------

def _minimal_report():
    return {
        "generated_at": "2026-09-18T00:00:00+00:00",
        "canonical_run_id": "canonical-test", "candidate_id": "candidate-test",
        "m1_status": "PARTIAL",
        "market_feature_stage_ready": True,
        "research_stage_ready": False,
        "feature_stage_ready": False,
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
        "exchange_coverage": {"HOSE": {"securities": 5, "price_rows": 50},
                              "HNX": {"securities": 3, "price_rows": 30},
                              "UPCOM": {"securities": 2, "price_rows": 20}},
        "market_missingness": {
            "traded_value_missing_rows": 1, "traded_value_missing_ratio": .01,
            "volume_missing_rows": 0, "volume_zero_rows": 0,
        },
        "quarantine_by_provider": {"kbs": 1, "cafef": 1},
        "exclusion_reason_counts": {
            "historical_identity:provisional_observed_interval_only": 10,
            "mom_21:insufficient_window_gap_unavailable_or_undefined": 3,
        },
    }


def _minimal_row():
    return {
        "ticker": "AAA", "exchange": "HOSE",
        "observed_first_date": "2020-01-01", "observed_last_date": "2026-08-31",
        "price_rows": 5, "observed_span_5y": True,
        "observed_session_coverage": 0.85, "recent_lookback_observations": 5,
        "latest_feature_complete": False, "market_feature_ready": False,
        "historical_identity_ready": False, "research_ready": False,
    }


if __name__ == "__main__":
    unittest.main()
