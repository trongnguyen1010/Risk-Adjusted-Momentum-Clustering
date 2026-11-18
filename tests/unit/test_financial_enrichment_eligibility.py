import unittest
import sqlite3
import csv
import json
import tempfile
from pathlib import Path

from delta_t1.features.financial_enrichment.eligibility import (
    FinancialEnrichmentEligibility,
    EligibleCell,
    FEATURES,
)

class FinancialEnrichmentEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # 1. Tạo SQLite mẫu
        self.db_path = self.dir_path / "test_indicators.sqlite"
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE company(ticker text primary key, sector_group text)")
        cur.execute("CREATE TABLE indicator_values(ticker text, fiscal_year integer, metric text, value real, status text, inputs_json text, primary key(ticker, fiscal_year, metric))")

        # Cty phi tài chính
        cur.execute("INSERT INTO company VALUES ('AAA', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('BBB', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('CCC', 'BANK')") # Ngân hàng (loại)

        # AAA: 8 OK, 1 MISSING_INPUT (cfo_to_ni có net_profit@t > 0) -> Đủ điều kiện làm giàu
        for m in FEATURES:
            if m == "cfo_to_ni":
                cur.execute("INSERT INTO indicator_values VALUES ('AAA', 2020, ?, NULL, 'MISSING_INPUT', ?)", (m, json.dumps({'net_profit@t': 1000000})))
            else:
                cur.execute("INSERT INTO indicator_values VALUES ('AAA', 2020, ?, 0.15, 'OK', '{}')", (m,))

        # BBB: 8 OK, 1 NEGATIVE_EARNINGS trên cfo_to_ni -> Khoảng trống công thức -> Không điền
        for m in FEATURES:
            if m == "cfo_to_ni":
                cur.execute("INSERT INTO indicator_values VALUES ('BBB', 2020, ?, NULL, 'NEGATIVE_EARNINGS', ?)", (m, json.dumps({'ni': -50000})))
            else:
                cur.execute("INSERT INTO indicator_values VALUES ('BBB', 2020, ?, 0.15, 'OK', '{}')", (m,))

        conn.commit()
        conn.close()

        # 2. Tạo availability.csv
        self.avail_path = self.dir_path / "test_availability.csv"
        with open(self.avail_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "usable_from_date", "date_source"])
            writer.writeheader()
            writer.writerow({"ticker": "AAA", "fiscal_year": "2020", "usable_from_date": "2021-06-30", "date_source": "LAG_RULE"})
            writer.writerow({"ticker": "BBB", "fiscal_year": "2020", "usable_from_date": "2021-06-30", "date_source": "LAG_RULE"})

        self.cutoffs = {2020: "2021-07-01"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_eligible_single_missing_cell_recognized(self):
        analyzer = FinancialEnrichmentEligibility(
            indicators_path=self.db_path,
            availability_path=self.avail_path,
            cutoffs=self.cutoffs,
        )
        res = analyzer.analyze(start_year=2020, end_year=2020)
        self.assertEqual(res["eligible_rows_count"], 1)
        self.assertEqual(res["eligible_cells_count"], 1)
        cell = res["eligible_cells"][0]
        self.assertEqual(cell.ticker, "AAA")
        self.assertEqual(cell.metric, "cfo_to_ni")
        self.assertEqual(cell.reason, "CFO_MISSING_POSITIVE_NI")

    def test_formula_gap_rejected_from_imputation(self):
        analyzer = FinancialEnrichmentEligibility(
            indicators_path=self.db_path,
            availability_path=self.avail_path,
            cutoffs=self.cutoffs,
        )
        res = analyzer.analyze(start_year=2020, end_year=2020)
        # BBB có negative earnings nên không lọt vào danh sách eligible
        tickers = [r["ticker"] for r in res["eligible_rows"]]
        self.assertNotIn("BBB", tickers)

if __name__ == "__main__":
    unittest.main()

