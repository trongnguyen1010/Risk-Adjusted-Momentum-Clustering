from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "m1_market_foundation_report",
    ROOT / "scripts/build_m1_market_foundation_report.py",
)
REPORT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REPORT)


class M1MarketFoundationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = REPORT.build_data(ROOT)

    def test_verified_headline_and_gate_counts(self) -> None:
        self.assertEqual(
            self.data["headline"],
            {
                "candidate_count": 952,
                "baseline_count": 500,
                "complete_expansion_count": 452,
                "deferred_expansion_count": 148,
                "feature_complete": 922,
                "market_feature_ready_v2": 905,
                "market_readiness_failures": 47,
                "latest253_complete": 922,
                "latest253_incomplete": 30,
                "historical_identity_ready": 0,
                "research_ready": 0,
            },
        )
        by_source = {
            row["candidate_source"]: row for row in self.data["source_stats"]
        }
        self.assertEqual(by_source["C5_BASELINE_500"]["market_ready"], 490)
        self.assertEqual(by_source["C7_COMPLETE_EXPANSION"]["market_ready"], 415)
        self.assertEqual(
            self.data["tradability"],
            {"ACTIVE": 675, "OBSERVED_ZERO_VOLUME": 276, "UNKNOWN": 1},
        )

    def test_required_feature_coverage_uses_actual_snapshot_rows(self) -> None:
        coverage = {
            row["feature"]: row for row in self.data["feature_coverage"]
        }
        self.assertEqual(set(coverage), set(REPORT.REQUIRED_FEATURES))
        self.assertEqual(coverage["mom_21"]["available"], 949)
        self.assertEqual(coverage["mom_252"]["available"], 922)
        self.assertEqual(coverage["beta_126"]["available"], 938)
        self.assertTrue(all(row["denominator"] == 952 for row in coverage.values()))
        self.assertTrue(
            all(row["snapshot_date"] == "2026-08-28" for row in coverage.values())
        )

    def test_monthly_readiness_is_ordered_unique_and_pit_scoped(self) -> None:
        rows = self.data["monthly_rows"]
        dates = [row["snapshot_date"] for row in rows]
        self.assertEqual(dates, sorted(set(dates)))
        self.assertEqual(dates[0], "2020-01-31")
        self.assertEqual(dates[-1], "2026-08-28")
        self.assertEqual(len(dates), 80)
        self.assertEqual(rows[-1]["candidate_rows"], 951)
        self.assertEqual(rows[-1]["feature_complete"], 922)
        self.assertEqual(rows[-1]["market_feature_ready_v2"], 905)

    def test_blockers_and_explicit_exception_sets(self) -> None:
        self.assertEqual(
            self.data["primary_blockers"],
            {
                "INSUFFICIENT_LATEST253_REAL_OBSERVATIONS": 29,
                "INSUFFICIENT_THREE_YEAR_HISTORY": 17,
                "NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE": 1,
            },
        )
        self.assertEqual(self.data["latest_blockers"], REPORT.EXPECTED_LATEST_BLOCKERS)
        self.assertEqual(
            tuple(self.data["complete_not_ready"]),
            REPORT.EXPECTED_COMPLETE_NOT_READY,
        )
        self.assertEqual(len(self.data["latest253_incomplete_tickers"]), 30)

    def test_artifact_hashes_and_notebook_are_offline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            output = temp_path / REPORT.ARTIFACT_ID
            notebook = temp_path / "inspection.ipynb"
            REPORT.generate(ROOT, output, notebook)
            REPORT.verify_existing(ROOT, output, notebook)

            manifest = json.loads(
                (output / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(manifest["outputs"]), 16)
            self.assertEqual(manifest["network_requests"], 0)
            self.assertEqual(
                set(manifest["outputs"]),
                {
                    *REPORT.REPORT_FILES,
                    *(f"plots/{name}" for name in REPORT.PLOT_FILES),
                },
            )
            document = json.loads(notebook.read_text(encoding="utf-8"))
            self.assertEqual(document["nbformat"], 4)
            text = json.dumps(document).lower()
            for token in ("urlopen(", "requests.get(", "http://", "https://"):
                self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
