"""Bounded Task-11 tests; no real holdout fitting or mutable development outputs."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.experiments.final_holdout import freeze_gate, prepare_holdout, fit_holdout, run_final_holdout
from delta_t1.experiments.protocol import M2_HOLDOUT_SNAPSHOTS, M2_MARKET_FEATURES
from delta_t1.io import read_json, write_json


def row(day, index, shift=0):
    group = 0 if index < 60 else 1
    result = dict(security_id=f"FIXTURE-{index:03d}", as_of_date=day,
        available_at=day + "T17:00:00+07:00", feature_version="1.6.0",
        data_version="fixture", adjustment_basis="vendor_adjusted",
        market_feature_ready=True, eligibility=False)
    result.update({f: float(group * 10 + index % 7 + shift) for f in M2_MARKET_FEATURES})
    return result


class FinalHoldoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.production_gate = freeze_gate(ROOT)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in self.production_gate["input_sha256"]:
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, target)

    def test_freeze_status_is_checked_before_any_holdout_loader(self):
        path = self.root / "M2/artifacts/m2-evaluation/final_method_decision.json"
        decision = read_json(path)
        decision["status"] = "DRAFT"
        write_json(path, decision)
        with patch("delta_t1.experiments.final_holdout.load_verified_market_only_features") as loader:
            with self.assertRaisesRegex(ValueError, "FROZEN_FOR_HOLDOUT"):
                run_final_holdout(self.root)
            loader.assert_not_called()
        self.assertFalse((self.root / "M2/artifacts/m2-final-holdout-v1").exists())

    def test_model_tamper_is_rejected_before_holdout_access(self):
        path = self.root / "M2/models/final_selected_model/2023-11-30.json"
        path.write_bytes(path.read_bytes() + b" ")
        with patch("delta_t1.experiments.final_holdout.load_verified_market_only_features") as loader:
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                run_final_holdout(self.root)
            loader.assert_not_called()

    def test_future_decision_timestamp_and_k_scan_are_rejected(self):
        path = self.root / "M2/artifacts/m2-evaluation/final_method_decision.json"
        decision = read_json(path)
        decision["decision_timestamp"] = "2099-01-01T00:00:00+00:00"
        write_json(path, decision)
        with self.assertRaisesRegex(ValueError, "timestamp"):
            freeze_gate(self.root)
        config_path = self.root / "configs/experiments/m2_final_holdout_v1.json"
        config = read_json(config_path)
        config["k_scan_enabled"] = True
        write_json(config_path, config)
        with self.assertRaisesRegex(ValueError, "k_scan_enabled"):
            freeze_gate(self.root)

    def test_loader_receives_only_holdout_dates_and_uses_each_months_members(self):
        gate = freeze_gate(self.root)
        rows = [row(day, i) for day in M2_HOLDOUT_SNAPSHOTS for i in range(120)]
        rows[0]["security_id"] = "FIRST-MONTH-ONLY"
        with patch("delta_t1.experiments.final_holdout.load_verified_market_only_features",
                   return_value=({}, rows)) as loader:
            _, prepared = prepare_holdout(self.root, gate)
        self.assertEqual(M2_HOLDOUT_SNAPSHOTS, loader.call_args.args[1])
        self.assertIn("FIRST-MONTH-ONLY", {r["security_id"] for r in prepared[0]["rows"]})
        self.assertNotIn("FIRST-MONTH-ONLY", {r["security_id"] for r in prepared[-1]["rows"]})
        self.assertTrue(all(p["status"] == "ready" for p in prepared))

    def test_late_features_are_rejected(self):
        gate = freeze_gate(self.root)
        late = row(M2_HOLDOUT_SNAPSHOTS[0], 0)
        late["available_at"] = "2026-02-28T00:00:01+07:00"
        with patch("delta_t1.experiments.final_holdout.load_verified_market_only_features",
                   return_value=({}, [late])):
            with self.assertRaisesRegex(ValueError, "Future feature availability"):
                prepare_holdout(self.root, gate)

    def test_exactly_one_fit_at_k2_per_month_and_skip_resets_chain(self):
        gate = freeze_gate(self.root)
        prepared = [dict(snapshot_date=day, status="ready", rows=[dict(row(day, i, shift=m * 100), market_feature_ready_v2=True)
                    for i in range(120)]) for m, day in enumerate(M2_HOLDOUT_SNAPSHOTS)]
        from delta_t1.clustering.registry import get_algorithm
        real = get_algorithm(gate["algorithm"])
        with patch("delta_t1.experiments.final_holdout.get_algorithm", return_value=real) as lookup:
            snaps, temporal, transitions, _ = fit_holdout(prepared, gate["clustering"], gate["algorithm"])
        lookup.assert_called_once_with(gate["algorithm"])
        self.assertEqual(7, len(snaps))
        self.assertEqual(6, len(temporal))
        self.assertEqual(24, len(transitions))
        self.assertEqual(list(zip(M2_HOLDOUT_SNAPSHOTS[:-1], M2_HOLDOUT_SNAPSHOTS[1:])),
                         [(r["from_date"], r["to_date"]) for r in temporal])
        self.assertTrue(all(len(s["diagnostics"]) == 1 and s["diagnostics"][0]["k"] == 2 for s in snaps))
        centers = [s["model"]["scaler"]["mom_21"]["center"] for s in snaps]
        self.assertEqual(100, centers[1]-centers[0])
        skipped = copy.deepcopy(prepared)
        skipped[2].update(status="skipped", rows=[])
        _, temporal, _, _ = fit_holdout(skipped, gate["clustering"], gate["algorithm"])
        self.assertEqual(4, len(temporal))
        self.assertNotIn((M2_HOLDOUT_SNAPSHOTS[1], M2_HOLDOUT_SNAPSHOTS[3]),
                         [(r["from_date"], r["to_date"]) for r in temporal])

    def test_raw_label_permutation_does_not_create_false_migration(self):
        gate = freeze_gate(self.root)
        prepared = [dict(snapshot_date=day, status="ready", rows=[row(day, i) for i in range(4)])
                    for day in M2_HOLDOUT_SNAPSHOTS[:2]]
        class PermutedAlgorithm:
            def fit_snapshot(self, rows, config):
                flipped = rows[0]["as_of_date"] == M2_HOLDOUT_SNAPSHOTS[1]
                labels = [1, 1, 0, 0] if flipped else [0, 0, 1, 1]
                profiles = [dict(raw_cluster_id=raw, size=2, economic_rank=1-raw if flipped else raw,
                    centroid={f: float(1-raw if flipped else raw) for f in M2_MARKET_FEATURES}) for raw in range(2)]
                return dict(rows=rows, labels=labels, profiles=profiles,
                            snapshot_date=rows[0]["as_of_date"], diagnostics=[{"k":2}])
        with patch("delta_t1.experiments.final_holdout.get_algorithm", return_value=PermutedAlgorithm()):
            _, temporal, transitions, drift = fit_holdout(prepared, gate["clustering"], gate["algorithm"])
        self.assertEqual(0, temporal[0]["migration_rate"])
        self.assertEqual([2,0,0,2], [r["count"] for r in transitions])
        self.assertTrue(all(r["value_from"] == r["value_to"] and r["delta"] == 0 for r in drift))

    def test_119_eligible_rows_are_skipped_without_invention(self):
        gate = freeze_gate(self.root)
        rows = [row(day, i) for day in M2_HOLDOUT_SNAPSHOTS for i in range(119)]
        with patch("delta_t1.experiments.final_holdout.load_verified_market_only_features",
                   return_value=({}, rows)):
            _, prepared = prepare_holdout(self.root, gate)
        self.assertTrue(all(p["status"] == "skipped" and p["eligible_count"] == 119 and not p["rows"]
                            for p in prepared))


class SavedFinalHoldoutEvidenceTests(unittest.TestCase):
    """Independent saved-evidence checks; never retrain on real holdout."""
    @classmethod
    def setUpClass(cls):
        from delta_t1.experiments.final_holdout import _csv_rows
        cls.gate = freeze_gate(ROOT)
        cls.target = ROOT / "M2/artifacts/m2-final-holdout-v1"
        if not cls.target.exists():
            raise unittest.SkipTest("Task 11 has not been executed yet")
        cls.assignments = _csv_rows(cls.target / "assignments.csv")
        cls.profiles = _csv_rows(cls.target / "cluster_profiles.csv")
        cls.temporal = _csv_rows(cls.target / "temporal_stability.csv")
        cls.transitions = _csv_rows(cls.target / "transition_matrices.csv")
        cls.drift = _csv_rows(cls.target / "centroid_drift.csv")

    def test_repeat_execution_verifies_without_fit_or_artifact_mutation(self):
        from delta_t1.io import digest
        before = {p: digest(p.read_bytes()) for p in self.target.rglob("*") if p.is_file()}
        with patch("delta_t1.experiments.final_holdout.fit_holdout") as fit:
            _, manifest = run_final_holdout(ROOT)
            fit.assert_not_called()
        self.assertEqual(before, {p: digest(p.read_bytes()) for p in before})
        self.assertEqual(["kmeans"], manifest["methods_executed"])
        self.assertEqual([2], manifest["k_values_executed"])
        self.assertEqual((7,6,4624), (manifest["n_snapshots"], manifest["n_temporal_pairs"], manifest["n_assignments"]))

    def test_independent_cross_sections_reproduce_model_scalers_and_labels(self):
        import numpy as np
        _, prepared = prepare_holdout(ROOT, self.gate)
        saved = {(r["snapshot_date"],r["security_id"]):r for r in self.assignments}
        profiles = {(r["snapshot_date"],int(r["raw_cluster_id"])):r for r in self.profiles}
        for prep in prepared:
            day = prep["snapshot_date"]
            model = read_json(self.target / "models" / (day + ".json"))
            x = np.array([[r[f] for f in M2_MARKET_FEATURES] for r in prep["rows"]])
            center = np.array([model["scaler"][f]["center"] for f in M2_MARKET_FEATURES])
            scale = np.array([model["scaler"][f]["scale"] for f in M2_MARKET_FEATURES])
            iqr = np.quantile(x,.75,axis=0)-np.quantile(x,.25,axis=0)
            self.assertTrue(np.allclose(center,np.median(x,axis=0)))
            self.assertTrue(np.allclose(scale,np.where(iqr==0,1,iqr)))
            z=(x-center)/scale
            centers=np.array(model["centroids"])
            labels=((z[:,None,:]-centers[None,:,:])**2).sum(axis=2).argmin(axis=1)
            actual=[int(saved[day,r["security_id"]]["raw_cluster_id"]) for r in prep["rows"]]
            self.assertEqual(labels.tolist(),actual)
            for label in range(2):
                p=profiles[day,label]
                self.assertEqual(int(p["size"]), int((labels==label).sum()))
                self.assertTrue(np.allclose(x[labels==label].mean(axis=0),[float(p[f]) for f in M2_MARKET_FEATURES]))

    def test_temporal_counts_and_drift_match_persistent_labels(self):
        from collections import Counter
        dates=list(M2_HOLDOUT_SNAPSHOTS)
        members={day:{r["security_id"]:int(r["aligned_cluster_id"]) for r in self.assignments if r["snapshot_date"]==day}
                 for day in dates}
        self.assertEqual(list(zip(dates[:-1],dates[1:])),[(r["from_date"],r["to_date"]) for r in self.temporal])
        for pair in self.temporal:
            a,b=members[pair["from_date"]],members[pair["to_date"]]
            shared=a.keys() & b.keys()
            counts=Counter((a[s],b[s]) for s in shared)
            transitions=[r for r in self.transitions if r["from_date"]==pair["from_date"] and r["to_date"]==pair["to_date"]]
            for r in transitions:
                source,target=int(r["from_cluster"]),int(r["to_cluster"])
                self.assertEqual(counts[source,target],int(r["count"]))
            self.assertEqual(len(shared),int(pair["n_common"]))
            self.assertEqual(len(b.keys()-a.keys()),int(pair["entered_count"]))
            self.assertEqual(len(a.keys()-b.keys()),int(pair["exited_count"]))
            self.assertAlmostEqual(sum(c for (x,y),c in counts.items() if x!=y)/len(shared),float(pair["migration_rate"]))
        profiles={(r["snapshot_date"],int(r["aligned_cluster_id"])):r for r in self.profiles}
        self.assertEqual(96,len(self.drift))
        for r in self.drift:
            label,f=int(r["aligned_cluster_id"]),r["feature"]
            a=float(profiles[r["from_date"],label][f]); b=float(profiles[r["to_date"],label][f])
            self.assertAlmostEqual(a,float(r["value_from"]))
            self.assertAlmostEqual(b,float(r["value_to"]))
            self.assertAlmostEqual(b-a,float(r["delta"]),delta=max(1e-10,abs(b-a)*1e-12))


if __name__ == "__main__":
    unittest.main()
