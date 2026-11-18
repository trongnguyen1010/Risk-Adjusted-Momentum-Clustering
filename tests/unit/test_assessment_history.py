import unittest
import sqlite3
import tempfile
import csv
import json
from pathlib import Path

from delta_t1.experiments.assessment.history import AssessmentHistoryBuilder
from delta_t1.experiments.assessment.inputs import FINANCIAL_FEATURES

class TestAssessmentHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # 1. SQLite mẫu
        self.db_path = self.dir_path / "test_ind.sqlite"
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE indicator_values(ticker text, fiscal_year integer, metric text, value real, status text)")
        # FPT 2022: 9 OK
        for m in FINANCIAL_FEATURES:
            cur.execute("INSERT INTO indicator_values VALUES ('FPT', 2022, ?, 0.2, 'OK')", (m,))
        # FPT 2023: 8 OK, 1 IMPUTED_MEDIAN
        for m in FINANCIAL_FEATURES:
            st = "IMPUTED_MEDIAN" if m == "cfo_to_ni" else "OK"
            cur.execute("INSERT INTO indicator_values VALUES ('FPT', 2023, ?, 0.22, ?)", (m, st))
        conn.commit()
        conn.close()

        # 2. Availability CSV
        self.avail_path = self.dir_path / "test_avail.csv"
        with open(self.avail_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "usable_from_date", "date_source"])
            writer.writeheader()
            writer.writerow({"ticker": "FPT", "fiscal_year": "2022", "usable_from_date": "2023-04-10", "date_source": "CAFEF_DISCLOSURE"})
            writer.writerow({"ticker": "FPT", "fiscal_year": "2023", "usable_from_date": "2024-04-12", "date_source": "CAFEF_DISCLOSURE"})

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_ticker_history(self):
        builder = AssessmentHistoryBuilder(self.db_path, self.avail_path)
        hist = builder.get_ticker_history("FPT", start_year=2022, end_year=2023)
        self.assertEqual(len(hist), 18)

        cov = builder.compute_coverage("FPT", start_year=2022, end_year=2023)
        self.assertEqual(cov["total_expected_cells"], 18)
        self.assertEqual(cov["observed_cells"], 18)
        self.assertEqual(cov["imputed_cells"], 1)
        self.assertEqual(cov["coverage_ratio"], 1.0)

    def test_export_history_jsonl(self):
        builder = AssessmentHistoryBuilder(self.db_path, self.avail_path)
        hist = builder.get_ticker_history("FPT", start_year=2022, end_year=2023)
        out_jsonl = self.dir_path / "feature_history.jsonl"
        builder.export_history_jsonl(hist, out_jsonl)

        self.assertTrue(out_jsonl.exists())
        lines = out_jsonl.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 18)
        first_row = json.loads(lines[0])
        self.assertEqual(first_row["ticker"], "FPT")
        self.assertEqual(first_row["fiscal_year"], 2022)

if __name__ == "__main__":
    unittest.main()
