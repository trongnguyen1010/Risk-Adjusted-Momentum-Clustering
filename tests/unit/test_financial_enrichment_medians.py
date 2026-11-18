import unittest
import sqlite3
import csv
import tempfile
from pathlib import Path

from delta_t1.features.financial_enrichment.medians import (
    compute_medians_from_fit,
    load_baseline_fit_tickers,
)

class FinancialEnrichmentMediansTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # 1. Tạo SQLite mẫu
        self.db_path = self.dir_path / "test_indicators.sqlite"
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE company(ticker text primary key, sector_group text)")
        cur.execute("CREATE TABLE indicator_values(ticker text, fiscal_year integer, metric text, value real, status text, inputs_json text, primary key(ticker, fiscal_year, metric))")

        # 3 tickers FIT: T1 (0.10), T2 (0.20), T3 (0.30) -> median = 0.20
        # 1 ticker non-FIT: T4 (100.0) -> không được tính vào median!
        cur.execute("INSERT INTO company VALUES ('T1', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('T2', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('T3', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('T4', 'NON_FINANCIAL')")

        for t, v in [('T1', 0.10), ('T2', 0.20), ('T3', 0.30), ('T4', 100.0)]:
            cur.execute("INSERT INTO indicator_values VALUES (?, 2020, 'roe', ?, 'OK', '{}')", (t, v))
            cur.execute("INSERT INTO indicator_values VALUES (?, 2020, 'roa', ?, 'OK', '{}')", (t, v * 0.5))

        conn.commit()
        conn.close()

        # 2. Tạo labels.csv giả lập B-PIT gốc
        self.labels_path = self.dir_path / "test_labels.csv"
        with open(self.labels_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "cluster", "role", "usable_from_date"])
            writer.writeheader()
            writer.writerow({"ticker": "T1", "fiscal_year": "2020", "cluster": "0", "role": "FIT", "usable_from_date": "2021-04-30"})
            writer.writerow({"ticker": "T2", "fiscal_year": "2020", "cluster": "1", "role": "FIT", "usable_from_date": "2021-04-30"})
            writer.writerow({"ticker": "T3", "fiscal_year": "2020", "cluster": "2", "role": "FIT", "usable_from_date": "2021-04-30"})
            writer.writerow({"ticker": "T4", "fiscal_year": "2020", "cluster": "0", "role": "ASSIGNED_AFTER_CUTOFF", "usable_from_date": "2021-08-30"})

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_medians_computed_strictly_from_fit_cohort(self):
        fit_map = load_baseline_fit_tickers(self.labels_path)
        self.assertEqual(len(fit_map[2020]), 3)
        self.assertNotIn("T4", fit_map[2020])

        med_map, records = compute_medians_from_fit(
            indicators_db_path=self.db_path,
            labels_csv_path=self.labels_path,
            features=("roe", "roa"),
            years=range(2020, 2021),
        )

        # Median ROE của [0.10, 0.20, 0.30] là 0.20 (không bị ảnh hưởng bởi 100.0 của T4)
        self.assertAlmostEqual(med_map[(2020, "roe")], 0.20, places=4)
        self.assertAlmostEqual(med_map[(2020, "roa")], 0.10, places=4)

        # Kiểm tra record metadata
        rec_roe = next(r for r in records if r["metric"] == "roe")
        self.assertEqual(rec_roe["n_observations"], 3)
        self.assertEqual(rec_roe["n_fit_cohort"], 3)

if __name__ == "__main__":
    unittest.main()

