import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.io import write_json, write_rows
from delta_t1.product import ProductRepository, export_product_bundle


class ProductBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.canonical = root / "canonical-test"
        self.features = root / "run-test"
        self.experiment = root / "experiment-test"
        security = {
            "security_id": "SEC-FPT",
            "ticker": "FPT",
            "company_name": "FPT Test",
            "exchange": "HOSE",
            "sector": "Technology",
            "industry": "Software",
            "currency": "VND",
            "price_unit": "VND",
            "identity_status": "verified",
        }
        peer = dict(security, security_id="SEC-CMG", ticker="CMG", company_name="CMG Test")
        write_rows(self.canonical / "clean/securities.jsonl", [security, peer])
        write_rows(self.canonical / "clean/prices_daily.jsonl", [
            {"security_id":"SEC-FPT","ticker":"FPT","trade_date":"2026-01-02","raw_close":100.0,"adj_close":None,"raw_open":98.0,"raw_high":102.0,"raw_low":97.0,"volume":10.0,"adjustment_basis":"unadjusted","source":"fixture","data_version":"canonical-test"},
            {"security_id":"SEC-FPT","ticker":"FPT","trade_date":"2026-01-05","raw_close":105.0,"adj_close":None,"raw_open":100.0,"raw_high":106.0,"raw_low":99.0,"volume":20.0,"adjustment_basis":"unadjusted","source":"fixture","data_version":"canonical-test"},
        ])
        write_rows(self.features / "features/monthly.jsonl", [{
            "security_id":"SEC-FPT","ticker":"FPT","as_of_date":"2026-01-31","data_version":"run-test","canonical_run_id":"canonical-test",
            "mom_21":.05,"mom_63":.12,"mom_126":.2,"mom_252":.3,"vol_63":.15,"vol_126":.18,"downside_vol_63":.1,"beta_126":1.1,"mdd_126":-.08,"sharpe_63":9.9,
        }])
        assignments = [
            {"security_id":"SEC-FPT","snapshot_date":"2026-01-31","aligned_cluster_id":1,"run_id":"experiment-test"},
            {"security_id":"SEC-CMG","snapshot_date":"2026-01-31","aligned_cluster_id":1,"run_id":"experiment-test"},
        ]
        write_rows(self.experiment / "assignments.jsonl", assignments)
        write_rows(self.experiment / "profiles.jsonl", [{"snapshot_date":"2026-01-31","aligned_cluster_id":1,"semantic_label":"Growth peer","centroid":{"mom_63":.1},"size":2}])
        write_json(self.experiment / "manifest.json", {"status":"complete","run_id":"experiment-test"})

    def tearDown(self):
        self.temp.cleanup()

    def test_export_is_product_ready_and_does_not_fabricate_domains(self):
        output = Path(self.temp.name) / "bundle"
        manifest = export_product_bundle(self.canonical, self.features, self.experiment, output, generated_at="2026-01-01T00:00:00+00:00")
        self.assertEqual(2, manifest["company_count"])
        detail = ProductRepository(output).get_company("fpt")
        self.assertEqual(105.0, detail["quote"]["price"])
        self.assertAlmostEqual(.05, detail["quote"]["change_pct"])
        self.assertEqual("partial", detail["quote_state"]["status"])
        self.assertIn("ceiling", detail["quote_state"]["missing_fields"])
        self.assertEqual(["CMG"], detail["cluster"]["peers"])
        self.assertEqual("unavailable", detail["fundamentals"]["state"]["status"])
        self.assertNotIn("sharpe_63", detail["analytics"]["values"])

    def test_repository_rejects_path_traversal_and_unknown_ticker(self):
        output = Path(self.temp.name) / "bundle"
        export_product_bundle(self.canonical, self.features, self.experiment, output)
        repository = ProductRepository(output)
        with self.assertRaises(ValueError):
            repository.get_company("../manifest")
        with self.assertRaises(KeyError):
            repository.get_company("UNKNOWN")

    def test_export_refuses_incomplete_experiment(self):
        write_json(self.experiment / "manifest.json", {"status":"running"})
        with self.assertRaisesRegex(ValueError, "complete immutable experiment"):
            export_product_bundle(self.canonical, self.features, self.experiment, Path(self.temp.name) / "bundle")


if __name__ == "__main__":
    unittest.main()
