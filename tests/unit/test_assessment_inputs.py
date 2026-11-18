import unittest
import sqlite3
import tempfile
import csv
from pathlib import Path

from delta_t1.experiments.assessment.inputs import (
    AssessmentInputResolver,
    AssessmentInputRecord,
    FINANCIAL_FEATURES,
    MARKET_FEATURES,
)

class TestAssessmentInputs(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # 1. Tạo SQLite mẫu
        self.db_path = self.dir_path / "test_indicators.sqlite"
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE company(ticker text primary key, sector_group text)")
        cur.execute("""
            CREATE TABLE indicator_values(
                ticker text,
                fiscal_year integer,
                metric text,
                value real,
                status text,
                primary key(ticker, fiscal_year, metric)
            )
        """)
        cur.execute("INSERT INTO company VALUES ('FPT', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('VCB', 'BANK')")

        for m in FINANCIAL_FEATURES:
            cur.execute("INSERT INTO indicator_values VALUES ('FPT', 2024, ?, 0.25, 'OK')", (m,))

        conn.commit()
        conn.close()

        # 2. Tạo availability.csv
        self.avail_path = self.dir_path / "test_avail.csv"
        with open(self.avail_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "usable_from_date", "date_source"])
            writer.writeheader()
            writer.writerow({"ticker": "FPT", "fiscal_year": "2024", "usable_from_date": "2025-04-15", "date_source": "CAFEF_DISCLOSURE"})
            writer.writerow({"ticker": "VCB", "fiscal_year": "2024", "usable_from_date": "2025-04-10", "date_source": "CAFEF_DISCLOSURE"})

        # 3. Tạo labels.csv
        self.bpit_path = self.dir_path / "labels.csv"
        with open(self.bpit_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "cluster", "role", "usable_from_date"])
            writer.writeheader()
            writer.writerow({"ticker": "FPT", "fiscal_year": "2024", "cluster": "1", "role": "FIT", "usable_from_date": "2025-04-15"})

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resolve_eligible_ticker(self):
        resolver = AssessmentInputResolver(
            indicators_db_path=self.db_path,
            availability_csv_path=self.avail_path,
            bpit_labels_path=self.bpit_path,
        )
        rec = resolver.resolve_ticker("FPT", as_of="2026-01-02")
        self.assertTrue(rec.is_eligible)
        self.assertEqual(rec.ticker, "FPT")
        self.assertEqual(rec.latest_fy, 2024)
        self.assertEqual(rec.cluster_b, 1)
        self.assertEqual(len(rec.financial_features), 9)
        self.assertEqual(rec.financial_features["roe"], 0.25)

    def test_resolve_sector_excluded_ticker(self):
        resolver = AssessmentInputResolver(
            indicators_db_path=self.db_path,
            availability_csv_path=self.avail_path,
            bpit_labels_path=self.bpit_path,
        )
        rec = resolver.resolve_ticker("VCB", as_of="2026-01-02")
        self.assertFalse(rec.is_eligible)
        self.assertEqual(rec.eligibility_reason, "SECTOR_EXCLUDED")
        self.assertEqual(rec.sector_group, "BANK")

    def test_resolve_unknown_ticker(self):
        resolver = AssessmentInputResolver(
            indicators_db_path=self.db_path,
            availability_csv_path=self.avail_path,
            bpit_labels_path=self.bpit_path,
        )
        rec = resolver.resolve_ticker("UNKNOWN_TICKER", as_of="2026-01-02")
        self.assertFalse(rec.is_eligible)
        self.assertEqual(rec.eligibility_reason, "SECTOR_EXCLUDED")

if __name__ == "__main__":
    unittest.main()
