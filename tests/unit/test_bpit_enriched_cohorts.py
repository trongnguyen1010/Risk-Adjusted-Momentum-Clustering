import unittest
import sqlite3
import tempfile
import csv
from pathlib import Path
import numpy as np

from delta_t1.experiments.bpit_enriched import (
    load_enriched_indicators,
    load_availability_map,
    build_enriched_snapshots,
    EnrichedSnapshot,
)

FEATURES = (
    "roe",
    "roa",
    "gross_margin",
    "net_margin",
    "debt_to_equity",
    "current_ratio",
    "asset_turnover",
    "revenue_growth",
    "cfo_to_ni",
)

class TestBpitEnrichedCohorts(unittest.TestCase):
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
        cur.execute("INSERT INTO company VALUES ('AAA', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('BBB', 'NON_FINANCIAL')")
        cur.execute("INSERT INTO company VALUES ('CCC', 'BANK')") # Bank bị loại

        # AAA: 8 OK, 1 IMPUTED_MEDIAN
        for m in FEATURES:
            st = "IMPUTED_MEDIAN" if m == "cfo_to_ni" else "OK"
            cur.execute("INSERT INTO indicator_values VALUES ('AAA', 2022, ?, 0.2, ?)", (m, st))

        # BBB: 9 OK
        for m in FEATURES:
            cur.execute("INSERT INTO indicator_values VALUES ('BBB', 2022, ?, 0.15, 'OK')", (m,))

        # CCC: 9 OK nhưng là BANK
        for m in FEATURES:
            cur.execute("INSERT INTO indicator_values VALUES ('CCC', 2022, ?, 0.3, 'OK')", (m,))

        conn.commit()
        conn.close()

        # 2. Tạo availability.csv
        self.avail_path = self.dir_path / "test_availability.csv"
        with open(self.avail_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "usable_from_date", "date_source"])
            writer.writeheader()
            # AAA kịp cutoff 2023-04-30
            writer.writerow({"ticker": "AAA", "fiscal_year": "2022", "usable_from_date": "2023-03-31", "date_source": "CAFEF_DISCLOSURE"})
            # BBB muộn sau cutoff
            writer.writerow({"ticker": "BBB", "fiscal_year": "2022", "usable_from_date": "2023-05-15", "date_source": "CAFEF_DISCLOSURE"})

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_enriched_indicators_opt_in(self):
        # 1. Nạp với opt-in ('OK', 'IMPUTED_MEDIAN') -> Nạp cả AAA và BBB, loại CCC
        data_all = load_enriched_indicators(
            self.db_path,
            features=FEATURES,
            opt_in_statuses=("OK", "IMPUTED_MEDIAN"),
        )
        self.assertIn("AAA", data_all[2022])
        self.assertIn("BBB", data_all[2022])
        self.assertNotIn("CCC", data_all[2022])
        self.assertEqual(len(data_all[2022]["AAA"]), 9)

        # 2. Nạp với baseline ('OK',) -> AAA chỉ có 8 chỉ số (thiếu cfo_to_ni)
        data_ok_only = load_enriched_indicators(
            self.db_path,
            features=FEATURES,
            opt_in_statuses=("OK",),
        )
        self.assertEqual(len(data_ok_only[2022]["AAA"]), 8)
        self.assertEqual(len(data_ok_only[2022]["BBB"]), 9)

    def test_build_enriched_snapshots_and_fit_cohort(self):
        snapshots = build_enriched_snapshots(
            sqlite_path=self.db_path,
            availability_path=self.avail_path,
            features=FEATURES,
            years=range(2022, 2023),
            opt_in_statuses=("OK", "IMPUTED_MEDIAN"),
            pinned_cutoffs={2022: "2023-04-30"},
        )
        self.assertEqual(len(snapshots), 1)
        snap = snapshots[0]
        self.assertEqual(snap.fiscal_year, 2022)
        self.assertEqual(snap.tickers, ["AAA", "BBB"])
        self.assertEqual(snap.cutoff, "2023-04-30")

        # AAA (2023-03-31 <= 2023-04-30) -> FIT (True)
        # BBB (2023-05-15 > 2023-04-30) -> Late (False)
        self.assertTrue(snap.fit_mask[0])
        self.assertFalse(snap.fit_mask[1])

if __name__ == "__main__":
    unittest.main()
