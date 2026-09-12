import copy
from datetime import datetime
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from test_foundation import generator
from delta_t1.ingestion.synthetic import build_vendor
from delta_t1.backtest.portfolio import weights
from delta_t1.backtest.returns_engine import rebalance, simulate
from delta_t1.clustering.kmeans import fit_snapshot, preprocess, fit_kmeans
from delta_t1.evaluation.stability import membership_metrics, compare, alignment
from delta_t1.evaluation.performance import metrics, bootstrap
from delta_t1.ingestion.promotion import promote, verify_vendor, map_record, trade_date, resolve_security
from delta_t1.ingestion.quality import clean_tables
from delta_t1.features.compute import build_features, returns, momentum
from delta_t1.io import read_json, read_rows, write_json, digest
from delta_t1.pipeline import run, run_canonical
from delta_t1.research import experiment, validate_protocol
from delta_t1.ingestion.planning import plan_large_crawl
from delta_t1.ingestion.recovery import recover_vendor


class ResearchUnitTests(unittest.TestCase):
    def test_fixture_dates_identity_and_gaps(self):
        fixture = read_json(ROOT / "tests/fixtures/vendor/edge_cases.json")
        for row in fixture["timestamps"]:
            self.assertEqual(trade_date(row["input"], row["offset"]), row["expected"])
        self.assertEqual(resolve_security(fixture["identity"], "NEW", "2025-01-01")["exchange"], "UPCOM")
        with self.assertRaises(ValueError):
            resolve_security(fixture["identity"], "OLD", "2025-01-01")
        self.assertEqual(returns(fixture["missing_day"]["prices"]), fixture["missing_day"]["expected"])
        self.assertIsNone(momentum([100] * 252, 252))

    def test_weighting_and_self_financing_costs(self):
        rows = [dict(security_id="a", vol=.1), dict(security_id="b", vol=.2)]
        self.assertAlmostEqual(weights(rows, "inverse_volatility", "vol")["a"], 2/3)
        self.assertEqual(weights(rows, "equal", "vol"), dict(a=.5, b=.5))
        values, cash, cost, turnover = rebalance({}, 1, {"a": 1}, .01)
        self.assertAlmostEqual(values["a"], 1/1.01)
        self.assertAlmostEqual(sum(values.values()) + cash + cost, 1)
        _, cash2, cost2, _ = rebalance(values, cash, {}, .01)
        self.assertAlmostEqual(cash2, .99/1.01)
        self.assertGreater(turnover, 0)

    def test_permutation_alignment_and_metrics(self):
        self.assertEqual(membership_metrics([0,0,1,1], [1,1,0,0]), (1,1))
        self.assertEqual(alignment([[5,0],[0,5]]), {1:0, 0:1})
        snapshot = dict(rows=[dict(security_id=str(i)) for i in range(4)], labels=[0,0,1,1], profiles=[dict(centroid={"x":0},size=2),dict(centroid={"x":1},size=2)])
        swapped = copy.deepcopy(snapshot)
        swapped["labels"] = [1,1,0,0]
        swapped["profiles"].reverse()
        result = compare(snapshot, swapped)
        self.assertEqual(result["membership_turnover"], 0)
        self.assertEqual(result["centroid_drift"], {0:{"x":0},1:{"x":0}})
        self.assertAlmostEqual(sum(r["rate"] for r in result["transitions"] if r["from_cluster"] == 0), 1)

    def test_metrics_hand_calculation_and_bootstrap(self):
        r = [.1, -.1]
        result = metrics(r, r, 0, [1,0])
        self.assertAlmostEqual(result["cumulative_return"], -.01)
        self.assertAlmostEqual(result["maximum_drawdown"], -.1)
        self.assertAlmostEqual(result["beta"], 1)
        self.assertAlmostEqual(result["alpha_annual"], 0)
        self.assertIsNone(result["information_ratio"])
        self.assertEqual(result["hit_rate"], .5)
        ci = bootstrap(r * 20, r * 20, 42, 30, 5)
        self.assertEqual((ci["lower_95"],ci["upper_95"]), (0,0))

    def test_clustering_deterministic_and_degenerate(self):
        x = [[0,0],[0,1],[10,10],[10,11]]
        a = fit_kmeans(x, 2, 42, 5, 100)
        self.assertEqual(a, fit_kmeans(x, 2, 42, 5, 100))
        self.assertEqual(a["labels"][0], a["labels"][1])
        self.assertNotEqual(a["labels"][0], a["labels"][2])
        with self.assertRaises(ValueError):
            fit_kmeans([[1],[1],[1]], 2, 42, 5, 100)

    def test_rank_ties_and_robust_scale(self):
        config = dict(features=["x"], winsor_quantile=0, scaling="rank")
        x, _ = preprocess([dict(x=v) for v in [1,1,3]], config)
        self.assertEqual(x[0], x[1])
        self.assertLess(x[0][0], x[2][0])

    def test_protocol_does_not_leak_holdout(self):
        config = read_json(ROOT / "configs/research.demo.json")
        config["development_end"] = "2025-01-01"
        with self.assertRaisesRegex(ValueError, "development"):
            validate_protocol(config)

    def test_scale_requires_real_pilot(self):
        with self.assertRaisesRegex(ValueError, "pilot"):
            plan_large_crawl(read_json(ROOT / "configs/crawl.scale.template.json"), {"status":"BLOCKED"})

    def test_corporate_action_adjustment_not_copied_from_raw(self):
        event = read_json(ROOT / "tests/fixtures/vendor/edge_cases.json")["corporate_action"]
        self.assertEqual(returns([event["before_price"], event["after_price"]]), [-.5])
        # Known synthetic split example: an adjusted path is economically distinct.
        self.assertEqual(returns([event["before_price"] / event["ratio"], event["after_price"]]), [0])


class ResearchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.config_path = generator.generate(cls.root)
        cls.directory, cls.manifest = run(cls.config_path, cls.root)
        cls.tables = {p.stem: read_rows(p) for p in (cls.directory / "clean").glob("*.jsonl")}
        cls.vendor, cls.policy_path = build_vendor(cls.root, cls.tables)
        cls.policy = read_json(cls.policy_path)
        cls.research_config = read_json(ROOT / "configs/research.demo.json")
        cls.research_config["plots"] = False
        cls.research_config["bootstrap"]["samples"] = 30
        cls.experiment_config = cls.root / "experiment.json"
        write_json(cls.experiment_config, cls.research_config)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_vendor_promote_canonical_features_cluster_backtest(self):
        before = {p.name:digest(p.read_bytes()) for p in (self.vendor / "raw").glob("*.json")}
        canonical, result = promote(self.vendor, self.policy_path, self.root)
        self.assertEqual(result["status"], "complete", result)
        directory, manifest = run_canonical(canonical, self.config_path, self.root)
        self.assertEqual(manifest["status"], "complete")
        features = read_rows(directory / "features/monthly.jsonl")
        self.assertEqual(len(features), 108)
        self.assertTrue(any(r["mom_252"] is not None for r in features))
        artifact, research = experiment(directory, self.experiment_config, self.root)
        self.assertEqual(research["status"], "complete", research.get("error"))
        self.assertGreater(research["n_assignments"], 0)
        self.assertFalse(research["real_pilot_accepted"])
        self.assertEqual(before, {p.name:digest(p.read_bytes()) for p in (self.vendor / "raw").glob("*.json")})
        execution = read_json(artifact / "backtests/cluster_execution.json")
        self.assertTrue(all(datetime.fromisoformat(r["execution_time"]) > datetime.fromisoformat(r["signal_time"]) for r in execution["executions"]))

    def test_unresolved_semantics_and_unknown_adjustment(self):
        policy = copy.deepcopy(self.policy)
        policy["price_multiplier"]["status"] = "unresolved"
        path = self.root / "unresolved.json"
        write_json(path, policy)
        target, result = promote(self.vendor, path, self.root)
        self.assertEqual(result["status"], "blocked")
        self.assertGreater(result["quarantined"], 0)
        self.assertTrue(read_rows(target / "quarantine/records.jsonl")[0]["vendor_run_id"])
        _, docs = verify_vendor(self.vendor, self.policy)
        doc = next(d for d in docs if d["job"]["kind"] == "equity")
        p = copy.deepcopy(self.policy)
        p["availability_policy"]["value"] = "fetched_at"
        p["adjustment_basis"]["value"] = "unadjusted"
        _, row = map_record(doc["records"][0], doc, p, self.tables["securities"], {})
        self.assertIsNone(row["adj_close"])
        self.assertIsNotNone(row["raw_close"])
        self.assertEqual(row["available_at"], doc["fetched_at"])

    def test_checksum_code_and_reference_tampering(self):
        policy = copy.deepcopy(self.policy)
        policy["approved_crawler_hashes"] = []
        with self.assertRaisesRegex(ValueError, "code hash"):
            verify_vendor(self.vendor, policy)
        p = self.vendor / "raw/listing.json"
        original = p.read_bytes()
        try:
            p.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "checksum"):
                verify_vendor(self.vendor, self.policy)
        finally:
            p.write_bytes(original)
        policy = copy.deepcopy(self.policy)
        policy["references"]["securities"]["sha256"] = "bad"
        path = self.root / "bad_reference.json"
        write_json(path, policy)
        _, result = promote(self.vendor, path, self.root)
        self.assertEqual(result["status"], "blocked")

    def test_recovery_keeps_old_snapshot_and_requires_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vendor, policy = build_vendor(root, self.tables)
            raw = vendor / "raw/listing.json"
            original = raw.read_bytes()
            cached = vendor / "work/listing-result.json"
            cached.parent.mkdir()
            cached.write_bytes(original)
            reformatted = json.dumps(json.loads(original), indent=2).encode()
            raw.write_bytes(reformatted)
            target, manifest = recover_vendor(vendor, policy, root)
            self.assertEqual(raw.read_bytes(), reformatted)
            self.assertEqual((target / "raw/listing.json").read_bytes(), original)
            self.assertEqual(manifest["recovery"]["original_run_id"], vendor.name)
            cached.write_bytes(b"unverified")
            with self.assertRaisesRegex(ValueError, "exact"):
                recover_vendor(vendor, policy, root)

    def test_qc_benchmark_and_action_edges(self):
        tables = copy.deepcopy(self.tables)
        tables["benchmark_daily"][0]["available_at"] = "2024-01-01T00:00:00+07:00"
        tables["prices_daily"][0].update(read_json(ROOT / "tests/fixtures/vendor/edge_cases.json")["invalid_ohlc"])
        tables["prices_daily"].append(copy.deepcopy(tables["prices_daily"][1]))
        tables["corporate_actions"] = [dict(event_id="split",security_id=tables["securities"][0]["security_id"],event_type="reverse_split",announcement_date="2024-01-01",ex_date="2024-01-02",effective_date="2024-01-02",available_at="2024-01-01T12:00:00+07:00")]
        raw = {name:[(r,dict(source="synthetic_fixture"),"2026-09-11T00:00:00+00:00") for r in rows] for name, rows in tables.items()}
        _, issues, rejected = clean_tables(raw, "test")
        self.assertTrue({"AVAILABILITY", "OHLC", "DUPLICATE_KEY", "ACTION_FIELDS"} <= {r["rule_id"] for r in issues})
        self.assertTrue(all("detected_at" in r for r in rejected))

    def test_calendar_unavailable_and_mixed_basis_reset(self):
        config = read_json(self.config_path)["features"]
        tables = copy.deepcopy(self.tables)
        for r in tables["trading_calendar"]:
            r["available_at"] = "2027-01-01T00:00:00+00:00"
        features = build_features(tables, config, "test")
        self.assertFalse(any(r["eligibility"] for r in features))
        tables = copy.deepcopy(self.tables)
        for r in tables["prices_daily"]:
            if r["trade_date"] >= "2025-06-01":
                r["adjustment_basis"] = "total_return"
        config["accepted_adjustments"].append("total_return")
        features = build_features(tables, config, "test")
        self.assertIsNone(features[-1]["mom_63"])

    def test_signal_lag_no_early_profit_gap_blocks_and_future_invariance(self):
        sid = self.tables["securities"][0]["security_id"]
        target = dict(snapshot_date="2025-05-30", decision_time="2025-05-30T18:00:00+07:00", weights={sid:1})
        config = self.research_config["backtest"]
        result = simulate([target], self.tables, config)
        self.assertEqual(result["nav"][0]["date"], "2025-06-02")
        self.assertAlmostEqual(result["nav"][0]["gross_return"], 0)
        self.assertLess(result["nav"][0]["net_return"], 0)
        tables = copy.deepcopy(self.tables)
        tables["prices_daily"] = [r for r in tables["prices_daily"] if not (r["security_id"] == sid and r["trade_date"] == "2025-06-03")]
        with self.assertRaisesRegex(ValueError, "missing"):
            simulate([target], tables, config)
        tables = copy.deepcopy(self.tables)
        for name in ("prices_daily", "benchmark_daily", "trading_calendar"):
            tables[name] = [r for r in tables[name] if r["trade_date"] <= "2025-06-10"]
        short = simulate([target], tables, config)
        self.assertEqual(short["nav"], [r for r in result["nav"] if r["date"] <= "2025-06-10"])

    def test_research_reproducible_outputs(self):
        first, a = experiment(self.directory, self.experiment_config, self.root)
        second, b = experiment(self.directory, self.experiment_config, self.root)
        self.assertEqual(a["status"], "complete", a.get("error"))
        self.assertEqual(b["status"], "complete", b.get("error"))
        self.assertNotEqual(a["run_id"], b["run_id"])
        for relative in ("performance.json", "profiles.jsonl", "diagnostics.jsonl", "backtests/cluster.jsonl"):
            self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
