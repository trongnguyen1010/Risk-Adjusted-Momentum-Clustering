import unittest
import sqlite3
import tempfile
import json
import shutil
from pathlib import Path

from delta_t1.features.financial_enrichment.imputation import ImputedCellRecord
from delta_t1.features.financial_enrichment.export import export_enriched_dataset, sha256_file

class TestFinancialEnrichmentExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_orig.sqlite"
        self.output_dir = Path(self.temp_dir) / "output"

        # Khởi tạo db mẫu
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE indicator_values (
                ticker TEXT,
                fiscal_year INTEGER,
                metric TEXT,
                value REAL,
                status TEXT
            )
        """)
        cur.executemany("""
            INSERT INTO indicator_values VALUES (?, ?, ?, ?, ?)
        """, [
            ("AAA", 2023, "roe", None, "MISSING_RAW"),
            ("AAA", 2023, "cfo", 10.5, "OK"),
            ("BBB", 2023, "roe", 15.0, "OK"),
        ])
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_enriched_dataset(self):
        imputed_record = ImputedCellRecord(
            ticker="AAA",
            fiscal_year=2023,
            metric="roe",
            original_status="MISSING_RAW",
            new_status="IMPUTED_MEDIAN",
            imputed_value=12.5,
            usable_from_date="2024-03-31",
            cutoff="2024-04-30",
            method="cohort_median_fit_baseline",
            reason="missing_raw_in_financial_report",
            n_donor_observations=50,
        )
        medians_records = [{
            "fiscal_year": 2023,
            "metric": "roe",
            "median": 12.5,
            "n_observations": 50,
            "n_fit_cohort": 60,
        }]
        input_hashes = {"test_orig_sha256": "fakehash123"}

        manifest = export_enriched_dataset(
            original_db_path=self.db_path,
            output_dir=self.output_dir,
            imputed_records=[imputed_record],
            medians_records=medians_records,
            input_hashes=input_hashes,
            git_commit_sha="dummy_commit",
        )

        # 1. Kiểm tra manifest và các file sinh ra
        enriched_db = self.output_dir / "indicators.sqlite"
        imputed_csv = self.output_dir / "imputed_cells.csv"
        medians_csv = self.output_dir / "medians_by_year_metric.csv"
        summary_json = self.output_dir / "imputation_summary.json"
        manifest_json = self.output_dir / "manifest.json"

        self.assertTrue(enriched_db.exists())
        self.assertTrue(imputed_csv.exists())
        self.assertTrue(medians_csv.exists())
        self.assertTrue(summary_json.exists())
        self.assertTrue(manifest_json.exists())

        # 2. Kiểm tra dữ liệu trong db mới
        conn = sqlite3.connect(enriched_db)
        cur = conn.cursor()
        rows = cur.execute("SELECT ticker, fiscal_year, metric, value, status FROM indicator_values ORDER BY metric").fetchall()
        conn.close()

        # AAA cfo giữ nguyên
        self.assertEqual(rows[0], ("AAA", 2023, "cfo", 10.5, "OK"))
        # AAA roe được cập nhật
        self.assertEqual(rows[1], ("AAA", 2023, "roe", 12.5, "IMPUTED_MEDIAN"))
        # BBB roe giữ nguyên
        self.assertEqual(rows[2], ("BBB", 2023, "roe", 15.0, "OK"))

        # 3. Kiểm tra hash trong manifest
        self.assertEqual(manifest["outputs"]["indicators_sqlite_sha256"], sha256_file(enriched_db))
        self.assertEqual(manifest["stats"]["total_imputed_cells"], 1)

if __name__ == "__main__":
    unittest.main()
