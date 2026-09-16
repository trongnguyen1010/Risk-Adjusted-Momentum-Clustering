import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
TMP_ROOT = ROOT / "tmp"
TMP_ROOT.mkdir(exist_ok=True)

from delta_t1.ingestion.representative_pilot import (
    CAFE_VERSION, KBS_VERSION, OFFICIAL_MARKET_SOURCES, _write_run_headers,
    build_job_plan, build_run_identity, dry_run, load_readiness,
    run_real, validate_resume_identity, validate_source_gate, validate_universe,
)
from delta_t1.ingestion.sources.vnstock import KBSPublicHttpSource, collect
from delta_t1.io import digest, encoded, read_json, write_json

PILOT_CLI_SPEC = importlib.util.spec_from_file_location(
    "representative_pilot_cli", ROOT / "scripts" / "run_representative_pilot.py")
pilot_cli = importlib.util.module_from_spec(PILOT_CLI_SPEC)
PILOT_CLI_SPEC.loader.exec_module(pilot_cli)


def universe(size=50):
    exchanges = ("HOSE", "HNX", "UPCOM")
    sectors = ("FINANCIALS", "INDUSTRIALS", "CONSUMER")
    return [{
        "security_id": f"SEC-{index:03d}", "ticker": f"S{index:03d}",
        "exchange": exchanges[index % len(exchanges)],
        "sector": sectors[index % len(sectors)], "sector_status": "VERIFIED",
        "listing_date": "2010-01-01", "history_eligibility": "TARGET_5Y",
        "selection_reason": "deterministic zero-network readiness fixture",
        "reference_only": False,
    } for index in range(size)]


def config(universe_path):
    return {
        "template_type": "REPRESENTATIVE_PILOT", "synthetic": False,
        "research_demo": True, "rights_status": "RIGHTS_NOT_VERIFIED",
        "risk_acceptance": "ACCEPTED_RESEARCH_RISK", "raw_redistribution": False,
        "start": "2020-01-01", "end": "2025-12-31",
        "universe_file": str(universe_path), "sector_coverage_limitation": None,
        "market_sources": dict(OFFICIAL_MARKET_SOURCES),
        "financial": {"mode": "RAW_ONLY_PIT_UNRESOLVED",
                      "enabled_for_market_gate": False, "collect_raw_side_track": False},
        "http": {"timeout": 20, "attempts": 2, "min_interval": 2.0,
                 "max_bytes": 5000000, "concurrency": 1},
        "cafef": {"page_size": 30, "max_pages": 100},
        "coverage_thresholds": {"minimum_usable_five_year_ratio": 0.9,
                                "maximum_failed_symbols": 0},
        "invalid_market_row_policy": {
            "provider": "cafef", "symbol": "VNM", "trade_date": "2021-09-09",
            "classification": "PROVIDER_CORRUPT_ROW",
            "row_status": "INVALID_REQUIRED_MARKET_ROW", "policy": "EXCLUDE_ROW",
            "expected_raw_fields": {"BasicPrice": 85.4, "Ceiling": 223.6,
                "Floor": 194.4, "ClosePrice": 85.2, "AdjustPrice": 64.634,
                "Volume": 2452400, "TotalValue": 209239000000,
                "AgreedVolume": 0, "AgreedValue": 0},
        },
    }


def gate():
    return {"gate": "SOURCE_SMOKE", "status": "PASS",
            "unlocks": ["REPRESENTATIVE_PILOT"],
            "checks": {"real_data": True},
            "input_evidence_hashes": {"smoke.json": "a" * 64}}


class RepresentativePilotTests(unittest.TestCase):
    def setup_files(self, directory, rows=None):
        root = Path(directory)
        (root / ".gitignore").write_text("/data/\n", encoding="utf-8")
        universe_path, config_path, gate_path = root / "universe.json", root / "pilot.json", root / "gate.json"
        write_json(universe_path, universe() if rows is None else rows)
        write_json(config_path, config(universe_path))
        write_json(gate_path, gate())
        return root, config_path, gate_path

    def build_identity_fixture(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path = self.setup_files(temp)
            prepared = load_readiness(config_path, gate_path, root=root)
            plan = build_job_plan(prepared)
            with patch("delta_t1.ingestion.representative_pilot.code_hash",
                       return_value="c" * 64):
                identity = build_run_identity(prepared, plan)
            return identity

    def build_real_run_header(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path = self.setup_files(temp)
            prepared = load_readiness(config_path, gate_path, root=root)
            plan = build_job_plan(prepared)
            with patch("delta_t1.ingestion.representative_pilot.code_hash",
                       return_value="c" * 64):
                directory = _write_run_headers(
                    prepared, plan, "representative-pilot-20260916T000000Z-1234abcd",
                    dry_run=False)
            return read_json(directory / "run.json"), plan

    def assert_cli_refused(self, arguments):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                pilot_cli.main(arguments)
        self.assertEqual(2, raised.exception.code)

    def test_cli_refuses_missing_mode(self):
        self.assert_cli_refused(["--config", "pilot.json", "--gate-report", "gate.json"])

    def test_cli_refuses_dry_run_and_execute_together(self):
        self.assert_cli_refused([
            "--config", "pilot.json", "--gate-report", "gate.json",
            "--dry-run", "--execute",
        ])

    def test_cli_refuses_resume_without_execute(self):
        self.assert_cli_refused([
            "--config", "pilot.json", "--gate-report", "gate.json",
            "--dry-run", "--resume", "representative-pilot-existing",
        ])

    def test_cli_execute_calls_real_path(self):
        gate_report = {"gate": "REPRESENTATIVE_PILOT", "status": "PASS", "unlocks": []}
        with patch.object(pilot_cli, "run_real",
                          return_value=(Path("run"), {}, gate_report)) as runner:
            result = pilot_cli.main([
                "--config", "pilot.json", "--gate-report", "gate.json", "--execute",
            ])
        self.assertEqual(0, result)
        runner.assert_called_once_with(
            "pilot.json", "gate.json", root=ROOT, resume=None)

    def test_dry_run_performs_zero_network_and_cannot_unlock_scale(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path = self.setup_files(temp)
            with patch("delta_t1.ingestion.representative_pilot.PublicJsonClient",
                       side_effect=AssertionError("network client constructed")) as client:
                directory, manifest = dry_run(config_path, gate_path, root=root,
                                              run_id="representative-pilot-20260916T000000Z-1234abcd")
            client.assert_not_called()
            self.assertEqual(0, manifest["network_requests"])
            self.assertEqual([], manifest["unlocks"])
            self.assertFalse(manifest["gate_emitted"])
            self.assertFalse((directory / "gate.json").exists())

    def test_new_real_run_stores_code_hash(self):
        header, _ = self.build_real_run_header()
        self.assertEqual("c" * 64, header["code_hash"])

    def test_new_real_run_stores_job_plan_hash(self):
        header, plan = self.build_real_run_header()
        self.assertEqual(digest(encoded(plan)), header["job_plan_hash"])

    def test_new_real_run_stores_kbs_adapter_version(self):
        header, _ = self.build_real_run_header()
        self.assertEqual(KBS_VERSION, header["kbs_adapter_version"])

    def test_new_real_run_stores_cafef_adapter_version(self):
        header, _ = self.build_real_run_header()
        self.assertEqual(CAFE_VERSION, header["cafef_adapter_version"])

    def test_resume_refuses_changed_code_hash(self):
        identity = self.build_identity_fixture()
        stored = dict(identity, code_hash="changed")
        with self.assertRaisesRegex(ValueError, "code_hash mismatch"):
            validate_resume_identity(stored, identity)

    def test_resume_refuses_changed_job_plan_hash(self):
        identity = self.build_identity_fixture()
        stored = dict(identity, job_plan_hash="changed")
        with self.assertRaisesRegex(ValueError, "job_plan_hash mismatch"):
            validate_resume_identity(stored, identity)

    def test_resume_refuses_changed_kbs_adapter_version(self):
        identity = self.build_identity_fixture()
        stored = dict(identity, kbs_adapter_version="changed")
        with self.assertRaisesRegex(ValueError, "kbs_adapter_version mismatch"):
            validate_resume_identity(stored, identity)

    def test_resume_refuses_changed_cafef_adapter_version(self):
        identity = self.build_identity_fixture()
        stored = dict(identity, cafef_adapter_version="changed")
        with self.assertRaisesRegex(ValueError, "cafef_adapter_version mismatch"):
            validate_resume_identity(stored, identity)

    def test_unchanged_identity_permits_resume_path(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path = self.setup_files(temp)
            prepared = load_readiness(config_path, gate_path, root=root)
            plan = build_job_plan(prepared)
            run_id = "representative-pilot-20260916T000000Z-1234abcd"
            with patch("delta_t1.ingestion.representative_pilot.code_hash",
                       return_value="c" * 64):
                directory = _write_run_headers(
                    prepared, plan, run_id, dry_run=False)
                write_json(directory / "manifest.json", {
                    "run_id": run_id, "mode": "REAL_EXECUTION", "status": "RUNNING",
                    "jobs": {job["id"]: {
                        "status": "COMPLETE", "job": job, "artifacts": [],
                    } for job in plan["jobs"]},
                })
                with patch("delta_t1.ingestion.representative_pilot._execute_job",
                           side_effect=AssertionError("completed resume job re-executed")) as execute:
                    resumed, _, _ = run_real(
                        config_path, gate_path, root=root, resume=run_id)
            execute.assert_not_called()
            self.assertEqual(directory, resumed)

    def test_universe_count_duplicate_history_and_exchange_rules_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "50-60"):
            validate_universe(universe(49))
        duplicate = universe(50); duplicate[-1]["ticker"] = duplicate[0]["ticker"]
        with self.assertRaises(ValueError):
            validate_universe(duplicate)
        short = universe(50); short[0]["history_eligibility"] = "SHORT_HISTORY"
        with self.assertRaisesRegex(ValueError, "REFERENCE_ONLY"):
            validate_universe(short)
        hose_only = universe(50)
        for row in hose_only:
            row["exchange"] = "HOSE"
        with self.assertRaisesRegex(ValueError, "HOSE, HNX and UPCOM"):
            validate_universe(hose_only)

    def test_source_gate_and_official_routing_are_required(self):
        bad = gate(); bad["status"] = "FAIL"; bad["unlocks"] = []
        with self.assertRaisesRegex(ValueError, "SOURCE_SMOKE"):
            validate_source_gate(bad)
        self.assertEqual("delta_public_http", KBSPublicHttpSource.acquisition_client)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path = self.setup_files(temp)
            prepared = load_readiness(config_path, gate_path, root=root)
            plan = build_job_plan(prepared)
            self.assertEqual(OFFICIAL_MARKET_SOURCES, plan["source_routing"])
            self.assertFalse(any(job["kind"] == "financial_raw_only" for job in plan["jobs"]))
            self.assertFalse(plan["financial_features_allowed"])

    def test_legacy_sdk_cannot_consume_official_gate(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            gate_path = Path(temp) / "gate.json"; write_json(gate_path, gate())
            with self.assertRaisesRegex(ValueError, "legacy Vnstock SDK path"):
                collect(temp, "2020-01-01", "2025-12-31",
                        [f"S{index:03d}" for index in range(50)], gate_report_path=gate_path)

    def test_less_than_five_years_and_wrong_routing_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path = self.setup_files(temp)
            value = read_json(config_path); value["start"] = "2022-01-01"
            write_json(config_path, value)
            with self.assertRaisesRegex(ValueError, "five years"):
                load_readiness(config_path, gate_path, root=root)
            value["start"] = "2020-01-01"; value["market_sources"]["ohlcv"] = "vnstock_sdk"
            write_json(config_path, value)
            with self.assertRaisesRegex(ValueError, "routing"):
                load_readiness(config_path, gate_path, root=root)


if __name__ == "__main__":
    unittest.main()
