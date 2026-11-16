import unittest
import tempfile
import csv
from pathlib import Path

from delta_t1.features.financial_enrichment.eligibility import EligibleCell
from delta_t1.features.financial_enrichment.imputation import (
    impute_cells,
    export_imputed_cells_csv,
    ImputedCellRecord,
)

class FinancialEnrichmentImputationTests(unittest.TestCase):
    def test_impute_cells_mapping_and_provenance(self):
        cells = [
            EligibleCell(
                ticker="AAA",
                fiscal_year=2020,
                metric="roe",
                original_status="MISSING_INPUT",
                usable_from_date="2021-04-30",
                cutoff="2021-07-01",
                reason="MISSING_INPUT",
            ),
            EligibleCell(
                ticker="BBB",
                fiscal_year=2020,
                metric="cfo_to_ni",
                original_status="MISSING_INPUT",
                usable_from_date="2021-04-30",
                cutoff="2021-07-01",
                reason="CFO_MISSING_POSITIVE_NI",
            ),
        ]
        medians_map = {
            (2020, "roe"): 0.0951,
            (2020, "cfo_to_ni"): 1.2653,
        }
        donor_counts = {
            (2020, "roe"): 977,
            (2020, "cfo_to_ni"): 977,
        }

        records = impute_cells(cells, medians_map, donor_counts)
        self.assertEqual(len(records), 2)

        r0 = records[0]
        self.assertEqual(r0.ticker, "AAA")
        self.assertEqual(r0.metric, "roe")
        self.assertEqual(r0.new_status, "IMPUTED_MEDIAN")
        self.assertAlmostEqual(r0.imputed_value, 0.0951)
        self.assertEqual(r0.n_donor_observations, 977)
        self.assertEqual(r0.method, "MEDIAN_SAME_FY_FIT")

        # Test CSV export
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "imputed_cells.csv"
            export_imputed_cells_csv(records, out_csv)
            self.assertTrue(out_csv.exists())
            with open(out_csv, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0]["new_status"], "IMPUTED_MEDIAN")

if __name__ == "__main__":
    unittest.main()

