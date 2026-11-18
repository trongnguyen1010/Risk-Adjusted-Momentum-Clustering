import unittest
import tempfile
import json
import csv
from pathlib import Path
import numpy as np

from delta_t1.experiments.bpit_enriched import EnrichedSnapshot, create_adapter
from delta_t1.clustering.robust_transforms import fit_t1, apply_t1

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

class TestBpitEnrichedArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "bpit_out"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        np.random.seed(42)
        c1 = np.random.normal(loc=-2.0, scale=0.5, size=(25, len(FEATURES)))
        c2 = np.random.normal(loc=2.0, scale=0.5, size=(25, len(FEATURES)))
        raw = np.abs(np.vstack([c1, c2])) + 0.1
        tickers = [f"T{i:02d}" for i in range(50)]
        usable = ["2023-03-31"] * 40 + ["2023-05-15"] * 10
        fit_mask = np.array([d <= "2023-04-30" for d in usable])

        self.snap = EnrichedSnapshot(
            fiscal_year=2022,
            tickers=tickers,
            raw=raw,
            usable_dates=usable,
            cutoff="2023-04-30",
            fit_mask=fit_mask,
            features=FEATURES,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_artifact_generation(self):
        # Giả lập pipeline xuất artifact cho 1 snapshot
        fit_idx = np.where(self.snap.fit_mask)[0]
        late_idx = np.where(~self.snap.fit_mask)[0]

        raw_fit = self.snap.raw[fit_idx]
        t1_params = fit_t1(raw_fit, self.snap.features)
        x_t1 = apply_t1(self.snap.raw, t1_params)

        adapter = create_adapter("kmeans", 3)
        labels_fit = adapter.fit(x_t1[fit_idx], raw_fit, self.snap.features)
        labels_late = adapter.assign_late(x_t1[late_idx])

        all_labels = np.empty(len(self.snap.tickers), dtype=int)
        all_labels[fit_idx] = labels_fit
        all_labels[late_idx] = labels_late

        # 1. Xuất labels.csv
        labels_path = self.output_dir / "labels.csv"
        with open(labels_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "cluster", "role", "usable_from_date"])
            writer.writeheader()
            for i, t in enumerate(self.snap.tickers):
                d = self.snap.usable_dates[i]
                role = "FIT" if self.snap.fit_mask[i] else "ASSIGNED_AFTER_CUTOFF"
                writer.writerow({
                    "ticker": t,
                    "fiscal_year": self.snap.fiscal_year,
                    "cluster": int(all_labels[i]),
                    "role": role,
                    "usable_from_date": d,
                })

        # 2. Xuất models.json
        models_path = self.output_dir / "models.json"
        models_data = {
            "2022": {
                "cutoff": self.snap.cutoff,
                "n_fit": len(fit_idx),
                "n_assigned": len(late_idx),
                "k": 3,
                "cluster_order": adapter.cluster_order,
            }
        }
        models_path.write_text(json.dumps(models_data), encoding="utf-8")

        # Kiểm tra file tồn tại và nội dung
        self.assertTrue(labels_path.exists())
        self.assertTrue(models_path.exists())

        with open(labels_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 50)
            # Kiểm tra fit_leaks
            for r in rows:
                if r["role"] == "FIT":
                    self.assertLessEqual(r["usable_from_date"], self.snap.cutoff)

        loaded_models = json.loads(models_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded_models["2022"]["n_fit"], 40)
        self.assertEqual(loaded_models["2022"]["n_assigned"], 10)
        self.assertEqual(len(loaded_models["2022"]["cluster_order"]), 3)

if __name__ == "__main__":
    unittest.main()
