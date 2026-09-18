import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
TMP_ROOT = ROOT / "tmp"
TMP_ROOT.mkdir(exist_ok=True)

from delta_t1.ingestion.m1_scale import (
    M1_SCALE_SHARD, _compatible_text_hashes, _load_scale_security_master,
    _require_portable_hash, _unique_rows,
    build_scale_job_plan, dry_run_shard, load_scale_readiness,
    evaluate_m1_readiness_checks, evaluate_scale_shard_checks,
    load_assignment_index, validate_assignment,
    validate_pilot_gate,
)
from delta_t1.io import atomic_write, digest, read_json, write_json


def universe_rows(count=500):
    exchanges = ("HOSE", "HNX", "UPCOM")
    return [{
        "security_id": f"TEST:{index:04d}", "ticker": f"T{index:04d}",
        "exchange": exchanges[index % 3], "sector": f"Sector {index % 10}",
        "sector_status": "VERIFIED", "listing_date": "2010-01-01",
        "history_eligibility": "USABLE_3Y", "selection_reason": "reviewed fixture",
        "reference_only": False,
    } for index in range(count)]


def invalid_policy():
    return {
        "provider": "cafef", "symbol": "VNM", "trade_date": "2021-09-09",
        "classification": "PROVIDER_CORRUPT_ROW",
        "row_status": "INVALID_REQUIRED_MARKET_ROW", "policy": "EXCLUDE_ROW",
        "expected_raw_fields": {
            "BasicPrice": 85.4, "Ceiling": 223.6, "Floor": 194.4,
            "ClosePrice": 85.2, "AdjustPrice": 64.634, "Volume": 2452400,
            "TotalValue": 209239000000, "AgreedVolume": 0, "AgreedValue": 0,
        },
    }


def config(universe_file):
    return {
        "template_type": "M1_SCALE", "synthetic": False, "research_demo": True,
        "rights_status": "RIGHTS_NOT_VERIFIED",
        "risk_acceptance": "ACCEPTED_RESEARCH_RISK", "raw_redistribution": False,
        "start": "2020-01-01", "end": "2026-09-15",
        "universe_file": universe_file, "expected_total_symbols": 500,
        "expected_shards": 5, "symbols_per_shard": 100,
        "sector_coverage_limitation": None,
        "market_sources": {
            "ohlcv": "kbs_delta_public_http", "benchmark": "kbs_delta_public_http",
            "reference_limits_value": "cafef_direct",
        },
        "financial": {"mode": "RAW_ONLY_PIT_UNRESOLVED",
                      "enabled_for_market_gate": False,
                      "collect_raw_side_track": False},
        "http": {"timeout": 20, "attempts": 2, "min_interval": 2.0,
                 "max_bytes": 5000000, "concurrency": 1},
        "cafef": {"page_size": 30, "max_pages": 100,
                  "source_exhaustion_policy": "CHECKPOINT_PARTIAL_FAIL_GATE"},
        "coverage_thresholds": {"minimum_usable_three_year_ratio": 1.0,
                                "maximum_failed_symbols": 0},
        "invalid_market_row_policy": invalid_policy(),
    }


def pilot_gate():
    return {
        "gate": "REPRESENTATIVE_PILOT", "status": "PASS", "unlocks": ["M1_SCALE"],
        "checks": {"real_data": True},
        "input_evidence_hashes": {"pilot": "a" * 64},
    }


def assignment(ids, *, benchmark=True):
    return {
        "scale_id": "m1-scale-test-v1", "assignment_id": "m1-scale-test-v1-worker-01",
        "collector": "collector-01", "shard_index": 1, "security_ids": ids,
        "start": "2020-01-01", "end": "2026-09-15",
        "include_benchmark": benchmark,
    }


class M1ScaleTests(unittest.TestCase):
    def test_handoff_text_hash_accepts_lf_or_crlf_but_not_changed_content(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            path = Path(temp) / "frozen.json"
            lf = b'{\n  "value": 1\n}\n'
            crlf = lf.replace(b"\n", b"\r\n")
            atomic_write(path, lf)
            hashes = _compatible_text_hashes(path)
            self.assertIn(digest(lf), hashes)
            self.assertIn(digest(crlf), hashes)
            _require_portable_hash(path, digest(crlf), "fixture")
            with self.assertRaisesRegex(ValueError, "fixture hash mismatch"):
                _require_portable_hash(path, digest(b'{"value":2}'), "fixture")

    def files(self, directory, *, benchmark=True):
        rows = universe_rows()
        atomic_write(directory / ".gitignore", b"/data/\n")
        write_json(directory / "universe.json", rows)
        write_json(directory / "config.json", config("universe.json"))
        write_json(directory / "gate.json", pilot_gate())
        write_json(directory / "assignment.json", assignment(
            [row["security_id"] for row in rows[:100]], benchmark=benchmark))
        return (directory / "config.json", directory / "gate.json",
                directory / "assignment.json")

    def test_gate_must_be_real_pilot_pass_unlocking_scale(self):
        for changed in (
            {"status": "FAIL"}, {"gate": "SOURCE_SMOKE"}, {"unlocks": []},
            {"checks": {"real_data": False}},
        ):
            gate = pilot_gate() | changed
            with self.assertRaisesRegex(ValueError, "REPRESENTATIVE_PILOT"):
                validate_pilot_gate(gate)

    def test_scale_gate_accepts_three_to_five_year_symbols(self):
        manifest = {
            "aggregate": {
                "selected_symbols": 100,
                "usable_3y_clustering_symbols": 100,
                "usable_5y_symbols": 20,
                "failed_symbols": [],
                "reference_source_exhausted_symbols": [],
            },
            "benchmark": {"valid": True},
            "jobs": {"job": {"status": "COMPLETE"}},
            "financial": {"features_allowed": False},
        }
        checks = evaluate_scale_shard_checks(
            manifest, config("unused.json"), include_benchmark=True)
        self.assertTrue(all(checks.values()))
        self.assertNotIn("five_year_ratio_passed", checks)

    def test_m1_readiness_checks_are_independent_and_fail_closed(self):
        checks = evaluate_m1_readiness_checks(
            selected=500, observed_span_3y=500, observed_span_5y=484,
            historical_identity_ready=0,
            market_feature_artifact_generated=True,
        )
        self.assertTrue(checks["collection_coverage_at_least_300"])
        self.assertTrue(checks["market_feature_artifact_generated"])
        self.assertFalse(checks["historical_identity_ready_for_research"])
        self.assertFalse(checks["financial_pit_ready_for_research"])
        self.assertFalse(checks["research_sample_size_policy_resolved"])
        self.assertNotIn("at_least_300_latest_features_eligible", checks)

    def test_assignment_requires_exact_unique_known_security_ids(self):
        rows = universe_rows()
        by_id = {row["security_id"]: row for row in rows}
        base = assignment([row["security_id"] for row in rows[:100]])
        validate_assignment(base, config("unused.json"), by_id)
        duplicate = dict(base, security_ids=base["security_ids"][:-1] + [base["security_ids"][0]])
        with self.assertRaisesRegex(ValueError, "100 unique"):
            validate_assignment(duplicate, config("unused.json"), by_id)
        unknown = dict(base, security_ids=base["security_ids"][:-1] + ["UNKNOWN:1"])
        with self.assertRaisesRegex(ValueError, "unknown"):
            validate_assignment(unknown, config("unused.json"), by_id)

    def test_dry_run_is_zero_network_and_writes_scale_identity(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            directory = Path(temp)
            config_path, gate_path, assignment_path = self.files(directory)
            output, manifest = dry_run_shard(
                config_path, gate_path, assignment_path, root=directory,
                run_id="m1-shard-dry-run-test")
            self.assertEqual(("PASS", 0), (manifest["readiness"], manifest["network_requests"]))
            self.assertFalse(manifest["execution_started"])
            header = read_json(output / "run.json")
            self.assertEqual(M1_SCALE_SHARD, header["template_type"])
            self.assertEqual("DRY_RUN", header["mode"])
            self.assertEqual("m1-scale-test-v1", header["scale_id"])
            self.assertEqual(64, len(header["assignment_hash"]))
            plan = read_json(output / "job_plan.json")
            self.assertTrue(plan["include_benchmark"])
            self.assertTrue(any(job["kind"] == "index" for job in plan["jobs"]))

    def test_non_coordinator_shard_omits_benchmark(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            directory = Path(temp)
            config_path, gate_path, assignment_path = self.files(directory, benchmark=False)
            prepared = load_scale_readiness(
                config_path, gate_path, assignment_path, root=directory)
            plan = build_scale_job_plan(prepared)
            self.assertFalse(plan["include_benchmark"])
            self.assertFalse(any(job["kind"] == "index" for job in plan["jobs"]))
            self.assertEqual(100, sum(job["kind"] == "reference_limits_value"
                                      for job in plan["jobs"]))

    def test_master_universe_count_is_exact(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            directory = Path(temp)
            config_path, gate_path, assignment_path = self.files(directory)
            write_json(directory / "universe.json", universe_rows(499))
            with self.assertRaisesRegex(ValueError, "exactly 500"):
                load_scale_readiness(config_path, gate_path, assignment_path, root=directory)

    def assignment_index(self, directory, *, overlap=False):
        config_path, gate_path, _ = self.files(directory)
        rows = universe_rows()
        entries = []
        assignment_dir = directory / "assignments"
        for index in range(5):
            ids = [row["security_id"] for row in rows[index * 100:(index + 1) * 100]]
            if overlap and index == 1:
                ids[-1] = rows[0]["security_id"]
            item = assignment(ids, benchmark=index == 0)
            item.update(assignment_id=f"m1-scale-test-v1-worker-{index + 1:02d}",
                        collector=f"collector-{index + 1:02d}", shard_index=index + 1)
            path = assignment_dir / f"worker-{index + 1:02d}.json"
            write_json(path, item)
            entries.append({"assignment_id": item["assignment_id"],
                            "path": path.name, "sha256": digest(path.read_bytes())})
        index_path = assignment_dir / "index.json"
        write_json(index_path, {
            "scale_id": "m1-scale-test-v1", "status": "FROZEN",
            "config_sha256": digest(config_path.read_bytes()),
            "universe_sha256": digest((directory / "universe.json").read_bytes()),
            "pilot_gate_sha256": digest(gate_path.read_bytes()),
            "expected_total_symbols": 500, "expected_shards": 5,
            "symbols_per_shard": 100, "assignments": entries,
        })
        return config_path, gate_path, index_path

    def test_assignment_index_requires_exact_disjoint_union_and_one_benchmark(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            directory = Path(temp)
            config_path, gate_path, index_path = self.assignment_index(directory)
            index, prepared = load_assignment_index(
                config_path, gate_path, index_path, root=directory)
            self.assertEqual(5, len(prepared))
            self.assertEqual(500, len({security_id for shard in prepared
                                      for security_id in shard["assignment"]["security_ids"]}))
            self.assertEqual("FROZEN", index["status"])

    def test_assignment_index_rejects_overlap_even_when_file_hashes_match(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            directory = Path(temp)
            config_path, gate_path, index_path = self.assignment_index(directory, overlap=True)
            with self.assertRaisesRegex(ValueError, "overlap"):
                load_assignment_index(config_path, gate_path, index_path, root=directory)

    def test_canonical_merge_rejects_duplicate_semantic_key(self):
        rows = [{"security_id": "TEST:1", "trade_date": "2020-01-02", "value": 1},
                {"security_id": "TEST:1", "trade_date": "2020-01-02", "value": 2}]
        with self.assertRaisesRegex(ValueError, "duplicate prices_daily key"):
            _unique_rows(rows, lambda row: (row["security_id"], row["trade_date"]),
                         "prices_daily")

    def test_scale_security_master_requires_exact_ticker_set(self):
        rows = universe_rows()
        document = {
            "schema_version": "1.0.0", "purpose": "M1_SCALE_SECURITY_MASTER",
            "identity_scope": "M1_OBSERVED_INTERVAL_ONLY", "identity_status": "provisional",
            "source_evidence": {"selected_row_count": 500, "response_sha256": "a" * 64,
                                "fetched_at": "2026-09-17T00:00:00+07:00"},
            "securities": [{"ticker": row["ticker"], "company_name": row["ticker"] + " Co",
                            "exchange": row["exchange"], "instrument_type": "stock"}
                           for row in rows],
        }
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            path = Path(temp) / "securities.json"
            write_json(path, document)
            _, _, by_ticker = _load_scale_security_master(path, rows)
            self.assertEqual(500, len(by_ticker))
            document["securities"].pop()
            write_json(path, document)
            with self.assertRaisesRegex(ValueError, "exact M1 universe"):
                _load_scale_security_master(path, rows)


if __name__ == "__main__":
    unittest.main()
