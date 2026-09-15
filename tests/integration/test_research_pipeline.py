import copy
from datetime import datetime
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
generator_spec = importlib.util.spec_from_file_location("generate_demo", ROOT / "scripts/generate_demo.py")
generator = importlib.util.module_from_spec(generator_spec)
generator_spec.loader.exec_module(generator)
from delta_t1.ingestion.synthetic import build_vendor
from delta_t1.backtest.portfolio import weights, select_backtest_universe
from delta_t1.backtest.returns_engine import rebalance, simulate
from delta_t1.clustering.kmeans import fit_snapshot, preprocess, fit_kmeans
from delta_t1.clustering.hierarchical import fit_ward
from delta_t1.clustering.registry import algorithms
from delta_t1.evaluation.cluster_metrics import cluster_metrics
from delta_t1.evaluation.temporal_metrics import membership_metrics, compare, alignment
from delta_t1.evaluation.portfolio_metrics import metrics, bootstrap
from delta_t1.ingestion.promotion import promote
from delta_t1.ingestion.normalization.identity import resolve_security
from delta_t1.ingestion.normalization.market import map_record, trade_date
from delta_t1.ingestion.sources.vnstock import verify_vendor
from delta_t1.ingestion.sources.cafef import CafeFSource
from delta_t1.ingestion.sources.vietfin import VietFinSource
from delta_t1.ingestion.reconciliation.candidates import candidate_from_row
from delta_t1.ingestion.reconciliation.rules import reconcile_candidates
from delta_t1.ingestion.quality import clean_tables
from delta_t1.features.market import build_features, returns, momentum
from delta_t1.features.point_in_time import latest_report_vintages
from delta_t1.features.registry import FEATURE_REGISTRY
from delta_t1.features.preprocessing import fit_pca
from delta_t1.io import read_json, read_rows, write_json, digest
from delta_t1.pipeline import run, run_canonical
from delta_t1.experiments.protocol import validate_protocol
from delta_t1.experiments.runner import experiment
from delta_t1.ingestion.recovery import recover_vendor
from delta_t1.ingestion.calendar import benchmark_calendar


class ResearchUnitTests(unittest.TestCase):
    def test_unverified_source_interfaces_fail_closed(self):
        for source in (CafeFSource(), VietFinSource()):
            with self.assertRaisesRegex(ValueError, "not verified"):
                source.acquire({"symbol": "FPT"})

    def test_reconciliation_preserves_basis_conflicts(self):
        common = dict(security_id="SEC-FPT", ticker="FPT", exchange="HOSE",
                      trade_date="2025-01-02", available_at="2025-01-02T17:00:00+07:00",
                      fetched_at="2025-01-03T00:00:00+00:00", raw_open=1, raw_high=1,
                      raw_low=1, raw_close=1, adj_close=None, volume=1, traded_value=1,
                      trading_status="normal")
        candidates = [
            candidate_from_row("prices_daily", dict(common, source="a", adjustment_basis="unadjusted")),
            candidate_from_row("prices_daily", dict(common, source="b", adjustment_basis="vendor_adjusted")),
        ]
        rows, decisions, conflicts = reconcile_candidates(candidates)
        self.assertFalse(rows)
        self.assertTrue(decisions)
        self.assertIn("PRICE_BASIS_CONFLICT", {item["status"] for item in conflicts})

    def test_feature_registry_controls_cluster_eligibility(self):
        self.assertTrue(FEATURE_REGISTRY.get("mom_63").cluster_eligible)
        self.assertNotIn("sharpe_63", FEATURE_REGISTRY.names())
        with self.assertRaisesRegex(ValueError, "portfolio-only"):
            FEATURE_REGISTRY.require_cluster_eligible(["sharpe_63"])

    def test_financial_vintage_is_point_in_time(self):
        base = dict(security_id="SEC-FPT", fiscal_year=2025, fiscal_quarter=2,
                    period_end="2025-06-30", statement_scope="consolidated",
                    published_at="2025-07-30T09:00:00+07:00")
        reports = [
            dict(base, report_id="R1", revision=1, available_at="2025-07-30T10:00:00+07:00"),
            dict(base, report_id="R2", revision=2, available_at="2025-08-15T10:00:00+07:00"),
        ]
        self.assertEqual(["R1"], [row["report_id"] for row in latest_report_vintages(
            reports, "SEC-FPT", "2025-08-01T17:00:00+07:00")])
        self.assertEqual(["R2"], [row["report_id"] for row in latest_report_vintages(
            reports, "SEC-FPT", "2025-08-31T17:00:00+07:00")])

    def test_benchmark_calendar_and_availability_assumption(self):
        rows = benchmark_calendar(["2025-01-30", "2025-01-31", "2025-02-03"], "2025-01-30", "2025-02-03", "2026-09-12T00:00:00+00:00")
        hose = {r["trade_date"]:r for r in rows if r["exchange"] == "HOSE"}
        self.assertTrue(hose["2025-01-31"]["is_month_end"])
        self.assertFalse(hose["2025-02-01"]["is_open"])
        self.assertEqual(hose["2025-01-31"]["decision_at"], "2025-01-31T17:00:00+07:00")
        with self.assertRaisesRegex(ValueError,"sessions"):
            benchmark_calendar(["2025-02-01"], "2025-02-01", "2025-02-01", "2026-09-12T00:00:00+00:00")

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

    def test_configurable_backtest_universe(self):
        rows=[dict(security_id=str(i),liquidity=i) for i in range(10)]
        percentage=select_backtest_universe(rows,{"mode":"percentage","value":.2,"rank_by":"liquidity","descending":True,"filters":{}})
        top_n=select_backtest_universe(rows,{"mode":"top_n","value":3,"rank_by":"liquidity","descending":True,"filters":{}})
        self.assertEqual([r['security_id'] for r in percentage],['9','8'])
        self.assertEqual([r['security_id'] for r in top_n],['9','8','7'])

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

    def test_ward_comparator_and_cluster_metrics_are_model_independent(self):
        vectors = [[0, 0], [0, 1], [10, 10], [10, 11]]
        fit = fit_ward(vectors, 2)
        self.assertEqual(fit, fit_ward(vectors, 2))
        self.assertEqual(fit["labels"][:2], [0, 0])
        self.assertEqual(fit["labels"][2:], [1, 1])
        quality = cluster_metrics(vectors, fit)
        self.assertEqual(quality["cluster_balance"], 1)
        self.assertIn("davies_bouldin", quality)

    def test_algorithm_registry_supports_comparator_and_fails_closed(self):
        self.assertIn("hierarchical", algorithms())
        config = read_json(ROOT / "configs/experiments/kmeans.example.json")
        config["clustering"]["algorithm"] = "hierarchical"
        validate_protocol(config)
        config["clustering"]["algorithm"] = "dbscan"
        with self.assertRaisesRegex(ValueError, "not enabled"):
            validate_protocol(config)

    def test_rank_ties_and_robust_scale(self):
        config = dict(features=["x"], winsor_quantile=0, scaling="rank")
        x, _ = preprocess([dict(x=v) for v in [1,1,3]], config)
        self.assertEqual(x[0], x[1])
        self.assertLess(x[0][0], x[2][0])

    def test_pca_is_deterministic_and_snapshot_scoped(self):
        vectors = [[-1.0, -1.0], [0.0, 0.0], [1.0, 1.0]]
        transformed, bundle = fit_pca(vectors, 1)
        self.assertEqual((transformed, bundle), fit_pca(vectors, 1))
        self.assertEqual(bundle["fit_scope"], "supplied_snapshot_only")
        self.assertAlmostEqual(bundle["explained_variance_ratio"][0], 1)

    def test_protocol_does_not_leak_holdout(self):
        config = read_json(ROOT / "configs/experiments/kmeans.example.json")
        config["development_end"] = "2025-01-01"
        with self.assertRaisesRegex(ValueError, "development"):
            validate_protocol(config)

    def test_protocol_rejects_sharpe_and_roi_clustering_inputs(self):
        for feature in ('sharpe_63','roi'):
            config=read_json(ROOT / 'configs/experiments/kmeans.example.json')
            config['clustering']['features'].append(feature)
            with self.assertRaisesRegex(ValueError,'Sharpe/ROI'):
                validate_protocol(config)

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
        cls.research_config = read_json(ROOT / "configs/experiments/kmeans.example.json")
        cls.research_config["portfolio_evaluation"]["enabled"] = True
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

    def test_kbs_price_conversion_optional_value_and_delayed_availability(self):
        # Artificial input is a unit fixture; it is never a real research run.
        _, docs = verify_vendor(self.vendor, self.policy)
        doc = next(d for d in docs if d["job"]["kind"] == "equity")
        record = dict(doc["records"][0], open=70, high=72, low=69, close=71.7, volume=123400)
        record.pop("va", None)
        policy = copy.deepcopy(self.policy)
        policy.update(price_multiplier=dict(status="verified",value=1000,evidence=["test fixture"]),
                      volume_multiplier=dict(status="verified",value=1,evidence=["test fixture"]),
                      traded_value_multiplier=dict(status="unresolved_optional",value=None,evidence=["optional"]),
                      availability_policy=dict(status="research_assumption",value="market_close_plus_delay",market_close_time="15:00:00+07:00",safety_delay_minutes=120,evidence=["explicit test assumption"]))
        policy["adjustment_basis"]["value"] = "unadjusted"
        policy["market_field_mappings"] = {
            "reference_price": {"status": "verified", "evidence": ["test fixture"],
                                "canonical_unit": "VND/share", "provider_field": "reference",
                                "multiplier": 1000},
            "ceiling_price": {"status": "verified", "evidence": ["test fixture"],
                              "canonical_unit": "VND/share", "provider_field": "ceiling",
                              "multiplier": 1000},
            "floor_price": {"status": "verified", "evidence": ["test fixture"],
                            "canonical_unit": "VND/share", "provider_field": "floor",
                            "multiplier": 1000},
        }
        record.update(reference=70, ceiling=75, floor=65)
        _, row = map_record(record, doc, policy, self.tables["securities"], {})
        self.assertAlmostEqual(row["raw_close"], 71700)
        self.assertEqual(row["raw_open"], 70000)
        self.assertEqual(row["volume"], 123400)
        self.assertIsNone(row["adj_close"])
        self.assertIsNone(row["traded_value"])
        self.assertEqual((70000, 75000, 65000),
                         (row["reference_price"], row["ceiling_price"], row["floor_price"]))
        self.assertTrue(row["available_at"].endswith("T17:00:00+07:00"))
        policy["adjustment_basis"]["value"] = "vendor_adjusted"
        policy.pop("market_field_mappings")
        _, row = map_record(record, doc, policy, self.tables["securities"], {})
        self.assertIsNone(row["raw_close"])
        self.assertAlmostEqual(row["adj_close"], 71700)
        with self.assertRaisesRegex(ValueError,"OHLC"):
            map_record(dict(record,low=100), doc, policy, self.tables["securities"], {})
        policy["availability_policy"]["safety_delay_minutes"]=-1
        with self.assertRaisesRegex(ValueError,"delay"):
            map_record(record,doc,policy,self.tables["securities"],{})

    def test_raw_features_do_not_require_adjusted_close(self):
        tables = copy.deepcopy(self.tables)
        fc = read_json(self.config_path)["features"]
        baseline = build_features(tables, fc, "unit-synthetic")
        for row in tables["prices_daily"]:
            row.update(raw_close=row["adj_close"],adj_close=None,adjustment_basis="unadjusted")
        fc["accepted_adjustments"]=["unadjusted"]
        actual = build_features(tables, fc, "unit-synthetic")
        self.assertEqual([r["mom_252"] for r in baseline],[r["mom_252"] for r in actual])
        self.assertEqual([r["vol_63"] for r in baseline],[r["vol_63"] for r in actual])

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

    def test_m2_experiment_disables_portfolio_evaluation(self):
        config = read_json(ROOT / "configs/experiments/kmeans.example.json")
        config["plots"] = False
        path = self.root / "m2-experiment.json"
        write_json(path, config)
        artifact, manifest = experiment(self.directory, path, self.root)
        self.assertEqual("complete", manifest["status"], manifest.get("error"))
        self.assertFalse(manifest["portfolio_evaluation_enabled"])
        self.assertFalse((artifact / "performance.json").exists())
        self.assertFalse((artifact / "backtests").exists())


if __name__ == "__main__":
    unittest.main()
