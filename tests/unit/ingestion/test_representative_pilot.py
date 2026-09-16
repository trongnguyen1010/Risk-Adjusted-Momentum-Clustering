import contextlib
import importlib.util
import io
import json
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
    CAFE_VERSION, KBS_VERSION, OFFICIAL_MARKET_SOURCES, _build_real_manifest,
    _execute_job, _map_cafef_page_rows, _write_run_headers,
    build_job_plan, build_run_identity, dry_run, load_readiness,
    run_real, validate_resume_identity, validate_source_gate, validate_universe,
)
from delta_t1.ingestion.sources.base import SemanticValidationError
from delta_t1.ingestion.sources.cafef import (
    CAFEF_DATETIME_MIN_VALUE, CAFEF_DOTNET_DATETIME_MIN_VALUE,
    cafef_trade_date, classify_cafef_page_row, map_trade_history_row,
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

    def setup_real_resume_run(self, directory):
        root, config_path, gate_path = self.setup_files(directory)
        prepared = load_readiness(config_path, gate_path, root=root)
        plan = build_job_plan(prepared)
        run_id = "representative-pilot-20260916T000000Z-1234abcd"
        with patch("delta_t1.ingestion.representative_pilot.code_hash",
                   return_value="c" * 64):
            run_directory = _write_run_headers(
                prepared, plan, run_id, dry_run=False)
        write_json(run_directory / "manifest.json", {
            "run_id": run_id, "mode": "REAL_EXECUTION", "status": "RUNNING",
            "jobs": {job["id"]: {
                "status": "COMPLETE", "job": job, "artifacts": [],
            } for job in plan["jobs"]},
        })
        return root, config_path, gate_path, run_id, run_directory

    def assert_resume_refused_before_network(self, config_path, gate_path, root,
                                             run_id, message):
        with patch("delta_t1.ingestion.representative_pilot.code_hash",
                   return_value="c" * 64):
            with patch("delta_t1.ingestion.representative_pilot.PublicJsonClient",
                       side_effect=AssertionError("network client constructed")):
                with self.assertRaisesRegex(ValueError, message):
                    run_real(config_path, gate_path, root=root, resume=run_id)

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

    def test_dry_run_cannot_resume_as_real_execution(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path = self.setup_files(temp)
            run_id = "representative-pilot-20260916T000000Z-1234abcd"
            with patch("delta_t1.ingestion.representative_pilot.code_hash",
                       return_value="c" * 64):
                directory, _ = dry_run(
                    config_path, gate_path, root=root, run_id=run_id)
            before = read_json(directory / "manifest.json")
            self.assert_resume_refused_before_network(
                config_path, gate_path, root, run_id, "run header mode mismatch")
            self.assertEqual(before, read_json(directory / "manifest.json"))

    def test_resume_refuses_non_real_run_header_mode(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path, run_id, directory = self.setup_real_resume_run(temp)
            header = read_json(directory / "run.json")
            header["mode"] = "DRY_RUN"
            write_json(directory / "run.json", header)
            self.assert_resume_refused_before_network(
                config_path, gate_path, root, run_id, "run header mode mismatch")

    def test_resume_refuses_non_real_manifest_mode(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path, run_id, directory = self.setup_real_resume_run(temp)
            manifest = read_json(directory / "manifest.json")
            manifest["mode"] = "DRY_RUN"
            write_json(directory / "manifest.json", manifest)
            self.assert_resume_refused_before_network(
                config_path, gate_path, root, run_id, "manifest mode mismatch")

    def test_resume_refuses_run_id_mismatch(self):
        for filename, message in (("run.json", "run header run_id mismatch"),
                                  ("manifest.json", "manifest run_id mismatch")):
            with self.subTest(filename=filename):
                with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
                    root, config_path, gate_path, run_id, directory = (
                        self.setup_real_resume_run(temp))
                    document = read_json(directory / filename)
                    document["run_id"] = "representative-pilot-different"
                    write_json(directory / filename, document)
                    self.assert_resume_refused_before_network(
                        config_path, gate_path, root, run_id, message)

    def test_resume_refuses_tampered_stored_job_plan(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path, run_id, directory = self.setup_real_resume_run(temp)
            stored_plan = read_json(directory / "job_plan.json")
            stored_plan["benchmark"] = "TAMPERED"
            write_json(directory / "job_plan.json", stored_plan)
            self.assert_resume_refused_before_network(
                config_path, gate_path, root, run_id, "stored job_plan_hash mismatch")

    def test_resume_refuses_missing_manifest_job(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path, run_id, directory = self.setup_real_resume_run(temp)
            manifest = read_json(directory / "manifest.json")
            manifest["jobs"].pop(next(iter(manifest["jobs"])))
            write_json(directory / "manifest.json", manifest)
            self.assert_resume_refused_before_network(
                config_path, gate_path, root, run_id, "manifest job set mismatch")

    def test_resume_refuses_extra_manifest_job(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path, run_id, directory = self.setup_real_resume_run(temp)
            manifest = read_json(directory / "manifest.json")
            manifest["jobs"]["unexpected-job"] = {
                "status": "PENDING", "job": {"id": "unexpected-job"}, "artifacts": [],
            }
            write_json(directory / "manifest.json", manifest)
            self.assert_resume_refused_before_network(
                config_path, gate_path, root, run_id, "manifest job set mismatch")

    def test_resume_refuses_modified_manifest_job_definition(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path, run_id, directory = self.setup_real_resume_run(temp)
            manifest = read_json(directory / "manifest.json")
            job_id = next(iter(manifest["jobs"]))
            manifest["jobs"][job_id]["job"]["provider"] = "tampered"
            write_json(directory / "manifest.json", manifest)
            self.assert_resume_refused_before_network(
                config_path, gate_path, root, run_id, "manifest job definition mismatch")

    def test_unchanged_identity_permits_resume_path(self):
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            root, config_path, gate_path, run_id, directory = self.setup_real_resume_run(temp)
            with patch("delta_t1.ingestion.representative_pilot.code_hash",
                       return_value="c" * 64):
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



class CafeFSnapshotClassificationTests(unittest.TestCase):
    """Focused tests for CafeF TradeDate format support and snapshot classification.

    Addresses CafeF TradeHistoryNew semantics:
    - Legacy M/D/YYYY h:mm:ss AM/PM timestamps represent UTC-like semantics (17:00:00Z
      on the previous calendar day) and are parsed to local Asia/Ho_Chi_Minh calendar date.
    - Snapshot classification and exclusion is position-aware: only page == 1 and
      row_index == 0 is classified and excluded as a current/intraday snapshot.
    - Raw payloads are preserved unchanged.
    """

    # --- 1. Legacy AM/PM historical date is parsed correctly ------------------

    def test_legacy_ampm_historical_date_parsed(self):
        """Legacy AM/PM historical close timestamp (UTC 17:00) is parsed to local VN calendar date (D+1)."""
        # 9/14/2026 5:00:00 PM represents 2026-09-14 17:00:00 UTC -> 2026-09-15 local VN date
        self.assertEqual("2026-09-15", cafef_trade_date("9/14/2026 5:00:00 PM"))
        # 1/2/2021 5:00:00 PM -> 2021-01-03
        self.assertEqual("2021-01-03", cafef_trade_date("1/2/2021 5:00:00 PM"))
        # single-digit month/day: 8/3/2026 5:00:00 PM -> 2026-08-04
        self.assertEqual("2026-08-04", cafef_trade_date("8/3/2026 5:00:00 PM"))
        # Year boundary: 12/31/2025 5:00:00 PM -> 2026-01-01
        self.assertEqual("2026-01-01", cafef_trade_date("12/31/2025 5:00:00 PM"))

    def test_legacy_ampm_and_iso_semantics_consistency(self):
        """Legacy 5:00:00 PM matches documented ISO UTC 17:00:00Z semantics for the same trade date."""
        self.assertEqual(
            cafef_trade_date("2026-09-14T17:00:00Z"),
            cafef_trade_date("9/14/2026 5:00:00 PM"),
        )
        self.assertEqual("2026-09-15", cafef_trade_date("9/14/2026 5:00:00 PM"))

    def test_legacy_ampm_historical_date_is_classified_historical(self):
        """A historical close timestamp (17:00:00) is HISTORICAL, not a snapshot."""
        self.assertEqual("HISTORICAL", classify_cafef_page_row("9/14/2026 5:00:00 PM", page=1, row_index=0))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("8/3/2026 5:00:00 PM", page=1, row_index=0))

    # --- 2. Current snapshot with valid intraday timestamp --------------------

    def test_current_snapshot_with_intraday_timestamp_is_excluded(self):
        """An intraday AM/PM timestamp (e.g. 7:45:00 AM) at page 1 row 0 is classified as CURRENT_SNAPSHOT."""
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("9/16/2026 7:45:00 AM", page=1, row_index=0))
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("9/16/2026 7:59:56 AM", page=1, row_index=0))
        # A PM timestamp that is NOT 17:00:00 is also a snapshot at page 1 row 0
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("9/16/2026 3:30:00 PM", page=1, row_index=0))

    # --- 3. Current snapshot with DateTime.MinValue (AM/PM and .NET tick-epoch) ---

    def test_datetime_min_value_sentinel_is_classified_as_snapshot(self):
        """CafeF DateTime.MinValue sentinel (year 0001) is a CURRENT_SNAPSHOT at page 1 row 0."""
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("1/1/0001 12:00:00 AM", page=1, row_index=0))

    def test_dotnet_datetime_min_value_sentinel_is_classified_as_snapshot(self):
        """CafeF .NET DateTime.MinValue tick-epoch /Date(-62135596800000)/ is CURRENT_SNAPSHOT at page 1 row 0."""
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("/Date(-62135596800000)/", page=1, row_index=0))
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row(CAFEF_DOTNET_DATETIME_MIN_VALUE, page=1, row_index=0))
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row(r"\/Date(-62135596800000)\/", page=1, row_index=0))

    def test_datetime_min_value_constant_has_year_1(self):
        """CAFEF_DATETIME_MIN_VALUE sentinel value matches .NET DateTime.MinValue."""
        self.assertEqual(1, CAFEF_DATETIME_MIN_VALUE.year)

    def test_negative_dotnet_date_fails_closed_in_historical_parser(self):
        """Negative .NET timestamps are not valid historical trade dates and fail closed."""
        with self.assertRaises(SemanticValidationError):
            cafef_trade_date("/Date(-123456)/")
        with self.assertRaises(SemanticValidationError):
            cafef_trade_date("/Date(-62135596800000)/")

    # --- 4. Position awareness: no global snapshot classification -------------

    def test_snapshot_classification_is_position_aware(self):
        """Only page == 1 and row_index == 0 can be CURRENT_SNAPSHOT; other rows/pages are HISTORICAL."""
        # Page 1 row 0: intraday timestamp is CURRENT_SNAPSHOT
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("9/16/2026 7:45:00 AM", page=1, row_index=0))
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("1/1/0001 12:00:00 AM", page=1, row_index=0))
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("/Date(-62135596800000)/", page=1, row_index=0))
        # Page 1 row 1+ are NOT snapshot even if time != 17:00 or DateTime.MinValue
        self.assertEqual("HISTORICAL", classify_cafef_page_row("9/16/2026 7:45:00 AM", page=1, row_index=1))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("1/1/0001 12:00:00 AM", page=1, row_index=1))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("/Date(-62135596800000)/", page=1, row_index=1))
        # Page 2+ rows are NOT snapshot even if row_index == 0
        self.assertEqual("HISTORICAL", classify_cafef_page_row("9/16/2026 7:45:00 AM", page=2, row_index=0))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("1/1/0001 12:00:00 AM", page=2, row_index=0))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("/Date(-62135596800000)/", page=2, row_index=0))

    def test_dotnet_datetime_min_value_outside_page1_row0_is_historical_and_fails_closed(self):
        """At row_index > 0 or page > 1, /Date(-62135596800000)/ is HISTORICAL and fails closed on mapping."""
        self.assertEqual("HISTORICAL", classify_cafef_page_row("/Date(-62135596800000)/", page=1, row_index=1))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("/Date(-62135596800000)/", page=2, row_index=0))
        row = {
            "Symbol": "CMG", "TradeDate": "/Date(-62135596800000)/",
            "BasicPrice": 22.5, "ClosePrice": 22.8, "Volume": 124400,
            "AdjustPrice": 22.8, "Ceiling": 24.05, "Floor": 20.95,
            "TotalValue": 2857960000, "AgreedVolume": 0, "AgreedValue": 0,
        }
        with self.assertRaises(SemanticValidationError):
            map_trade_history_row(row, "CMG", "HOSE")

    # --- 5. Existing .NET Date(...) format is unchanged -----------------------

    def test_dotnet_date_format_still_works(self):
        """Existing .NET /Date(ms)/ format is unaffected by the patch."""
        # /Date(1631577600000)/ = 2021-09-14 in UTC -> 2021-09-14 VN (UTC+7)
        self.assertEqual("2021-09-14", cafef_trade_date("/Date(1631577600000)/"))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("/Date(1631577600000)/", page=1, row_index=0))

    # --- 6. Existing ISO date format is unchanged ----------------------------

    def test_iso_date_format_still_works(self):
        """Existing ISO-8601 format with tz is unaffected by the patch."""
        self.assertEqual("2026-09-14", cafef_trade_date("2026-09-14T17:00:00+07:00"))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("2026-09-14T17:00:00+07:00", page=1, row_index=0))

    # --- 7. Position-aware snapshot exclusion in _execute_job -----------------

    def test_execute_job_excludes_leading_datetime_min_value_snapshot(self):
        """_execute_job excludes DateTime.MinValue snapshot at page 1 row 0 and keeps raw payload."""
        import json as _json
        from delta_t1.ingestion.representative_pilot import _execute_job

        historical_row_1 = {
            "Symbol": "CMG", "TradeDate": "9/14/2026 5:00:00 PM",
            "BasicPrice": 22.5, "ClosePrice": 22.8, "Volume": 124400,
            "AdjustPrice": 22.8, "Ceiling": 24.05, "Floor": 20.95,
            "TotalValue": 2857960000, "AgreedVolume": 0, "AgreedValue": 0,
        }
        historical_row_0 = dict(historical_row_1, TradeDate="2019-12-31T17:00:00+07:00",
                                BasicPrice=10.0, Ceiling=11.0, Floor=9.0)
        payload = {
            "Success": True,
            "Data": [
                # Row 0: DateTime.MinValue sentinel (excluded from mapping)
                dict(historical_row_1, TradeDate="1/1/0001 12:00:00 AM"),
                # Row 1: real historical close (9/14/2026 5:00:00 PM -> 2026-09-15)
                historical_row_1,
                # Row 2: older than job start -> triggers reached_start
                historical_row_0,
            ],
        }
        body = _json.dumps(payload).encode()

        class SnapshotCafeFSource:
            def acquire_trade_history_page(self, _request):
                return {"payload": payload, "body": body,
                        "url": "https://example.test", "status": 200}

        class SnapshotStore:
            def __init__(self):
                self.saved = []
                self.saved_payloads = []
            def save(self, provider, artifact_id, response, metadata, **kwargs):
                self.saved.append(True)
                self.saved_payloads.append(response["payload"])
                return {"raw_path": "data/raw/cafef/run/CMG-page-001.json", "sha256": "a" * 64}

        job = {"id": "cafef-CMG", "provider": "cafef", "kind": "reference_limits_value",
               "symbol": "CMG", "exchange": "HOSE",
               "start": "2020-01-01", "end": "2026-09-14", "max_pages": 100}
        store = SnapshotStore()
        artifacts = _execute_job(job, {}, None, SnapshotCafeFSource(), store)
        self.assertEqual(1, len(artifacts))
        self.assertEqual(1, len(store.saved))
        # Verify raw payload is preserved unchanged with leading sentinel
        self.assertEqual("1/1/0001 12:00:00 AM", store.saved_payloads[0]["Data"][0]["TradeDate"])

    def test_execute_job_excludes_leading_dotnet_datetime_min_value_snapshot(self):
        """_execute_job excludes .NET DateTime.MinValue tick-epoch /Date(-62135596800000)/ at page 1 row 0 before mapping."""
        import json as _json
        from delta_t1.ingestion.representative_pilot import _execute_job

        historical_row_1 = {
            "Symbol": "CMG", "TradeDate": "9/14/2026 5:00:00 PM",
            "BasicPrice": 22.5, "ClosePrice": 22.8, "Volume": 124400,
            "AdjustPrice": 22.8, "Ceiling": 24.05, "Floor": 20.95,
            "TotalValue": 2857960000, "AgreedVolume": 0, "AgreedValue": 0,
        }
        historical_row_0 = dict(historical_row_1, TradeDate="2019-12-31T17:00:00+07:00",
                                BasicPrice=10.0, Ceiling=11.0, Floor=9.0)
        payload = {
            "Success": True,
            "Data": [
                # Row 0: .NET DateTime.MinValue sentinel (must be excluded before map_trade_history_row)
                dict(historical_row_1, TradeDate="/Date(-62135596800000)/"),
                # Row 1: real historical close
                historical_row_1,
                # Row 2: older than job start -> triggers reached_start
                historical_row_0,
            ],
        }
        body = _json.dumps(payload).encode()

        class SnapshotCafeFSource:
            def acquire_trade_history_page(self, _request):
                return {"payload": payload, "body": body,
                        "url": "https://example.test", "status": 200}

        class SnapshotStore:
            def __init__(self):
                self.saved = []
                self.saved_payloads = []
            def save(self, provider, artifact_id, response, metadata, **kwargs):
                self.saved.append(True)
                self.saved_payloads.append(response["payload"])
                return {"raw_path": "data/raw/cafef/run/CMG-page-001.json", "sha256": "a" * 64}

        job = {"id": "cafef-CMG", "provider": "cafef", "kind": "reference_limits_value",
               "symbol": "CMG", "exchange": "HOSE",
               "start": "2020-01-01", "end": "2026-09-14", "max_pages": 100}
        store = SnapshotStore()
        artifacts = _execute_job(job, {}, None, SnapshotCafeFSource(), store)
        self.assertEqual(1, len(artifacts))
        self.assertEqual(1, len(store.saved))
        # Raw payload preserved unchanged with /Date(-62135596800000)/
        self.assertEqual("/Date(-62135596800000)/", store.saved_payloads[0]["Data"][0]["TradeDate"])

    def test_execute_job_excludes_leading_intraday_snapshot(self):
        """_execute_job excludes normal intraday timestamp snapshot at page 1 row 0."""
        import json as _json
        from delta_t1.ingestion.representative_pilot import _execute_job

        historical_row_1 = {
            "Symbol": "CMG", "TradeDate": "9/14/2026 5:00:00 PM",
            "BasicPrice": 22.5, "ClosePrice": 22.8, "Volume": 124400,
            "AdjustPrice": 22.8, "Ceiling": 24.05, "Floor": 20.95,
            "TotalValue": 2857960000, "AgreedVolume": 0, "AgreedValue": 0,
        }
        historical_row_0 = dict(historical_row_1, TradeDate="2019-12-31T17:00:00+07:00",
                                BasicPrice=10.0, Ceiling=11.0, Floor=9.0)
        payload = {
            "Success": True,
            "Data": [
                # Row 0: intraday timestamp snapshot (excluded from mapping)
                dict(historical_row_1, TradeDate="9/16/2026 7:45:00 AM"),
                # Row 1: real historical close
                historical_row_1,
                # Row 2: older than job start
                historical_row_0,
            ],
        }
        body = _json.dumps(payload).encode()

        class SnapshotCafeFSource:
            def acquire_trade_history_page(self, _request):
                return {"payload": payload, "body": body,
                        "url": "https://example.test", "status": 200}

        class SnapshotStore:
            def __init__(self):
                self.saved = []
                self.saved_payloads = []
            def save(self, provider, artifact_id, response, metadata, **kwargs):
                self.saved.append(True)
                self.saved_payloads.append(response["payload"])
                return {"raw_path": "data/raw/cafef/run/CMG-page-001.json", "sha256": "a" * 64}

        job = {"id": "cafef-CMG", "provider": "cafef", "kind": "reference_limits_value",
               "symbol": "CMG", "exchange": "HOSE",
               "start": "2020-01-01", "end": "2026-09-14", "max_pages": 100}
        store = SnapshotStore()
        artifacts = _execute_job(job, {}, None, SnapshotCafeFSource(), store)
        self.assertEqual(1, len(artifacts))
        self.assertEqual(1, len(store.saved))
        # Raw payload preserved unchanged with intraday timestamp
        self.assertEqual("9/16/2026 7:45:00 AM", store.saved_payloads[0]["Data"][0]["TradeDate"])

    def test_execute_job_does_not_globally_exclude_non_leading_rows(self):
        """Rows at row_index > 0 or page > 1 with time != 17:00 are NOT excluded as snapshot."""
        import json as _json
        from delta_t1.ingestion.representative_pilot import _execute_job

        historical_row_1 = {
            "Symbol": "CMG", "TradeDate": "9/14/2026 5:00:00 PM",
            "BasicPrice": 22.5, "ClosePrice": 22.8, "Volume": 124400,
            "AdjustPrice": 22.8, "Ceiling": 24.05, "Floor": 20.95,
            "TotalValue": 2857960000, "AgreedVolume": 0, "AgreedValue": 0,
        }
        # A row with time != 17:00 at row_index 1
        non_standard_time_row = dict(historical_row_1, TradeDate="9/14/2026 9:30:00 AM")
        historical_row_0 = dict(historical_row_1, TradeDate="2019-12-31T17:00:00+07:00",
                                BasicPrice=10.0, Ceiling=11.0, Floor=9.0)

        # Page 1 has historical_row_1 at row 0 (not a snapshot), non_standard_time_row at row 1
        payload_p1 = {
            "Success": True,
            "Data": [
                historical_row_1,       # row 0 (17:00 -> not snapshot)
                non_standard_time_row,  # row 1 (time != 17:00, but NOT row 0 -> NOT excluded)
            ],
        }
        # Page 2 has another non-standard time row at row 0 (page != 1 -> NOT excluded)
        payload_p2 = {
            "Success": True,
            "Data": [
                dict(historical_row_1, TradeDate="9/13/2026 8:00:00 AM"),
                historical_row_0,       # older than job start -> triggers reached_start
            ],
        }

        class MultiPageCafeFSource:
            def acquire_trade_history_page(self, req):
                p = req["page_index"]
                payload = payload_p1 if p == 1 else payload_p2
                return {"payload": payload, "body": _json.dumps(payload).encode(),
                        "url": "https://example.test", "status": 200}

        class SnapshotStore:
            def __init__(self):
                self.saved = []
            def save(self, provider, artifact_id, response, metadata, **kwargs):
                self.saved.append(True)
                return {"raw_path": f"data/raw/cafef/run/CMG-page-{metadata['page_index']:03d}.json",
                        "sha256": "a" * 64}

        job = {"id": "cafef-CMG", "provider": "cafef", "kind": "reference_limits_value",
               "symbol": "CMG", "exchange": "HOSE",
               "start": "2020-01-01", "end": "2026-09-14", "max_pages": 100}
        store = SnapshotStore()
        artifacts = _execute_job(
            job, {"cafef": {"page_size": 2}}, None, MultiPageCafeFSource(), store)
        self.assertEqual(2, len(artifacts))


class CafeFPaginationHardeningTests(unittest.TestCase):
    def setUp(self):
        self.job = {
            "id": "cafef-ACB", "provider": "cafef", "kind": "reference_limits_value",
            "symbol": "ACB", "exchange": "HOSE", "start": "2020-01-01",
            "end": "2026-09-15", "max_pages": 2,
        }

    @staticmethod
    def row(day, trade_date=None):
        return {
            "Symbol": "ACB", "TradeDate": trade_date or f"2026-01-{day:02d}T17:00:00+07:00",
            "BasicPrice": 20.0, "ClosePrice": 20.5, "Volume": 1000,
            "AdjustPrice": 20.5, "Ceiling": 21.0, "Floor": 19.0,
            "TotalValue": 20500000, "AgreedVolume": 0, "AgreedValue": 0,
        }

    @staticmethod
    def source(pages):
        class Source:
            def acquire_trade_history_page(self, request):
                payload = {"Success": True, "Data": pages[request["page_index"] - 1]}
                return {"payload": payload, "body": json.dumps(payload).encode(),
                        "url": "https://example.test", "status": 200}
        return Source()

    @staticmethod
    def store():
        class Store:
            def __init__(self):
                self.pages = []
            def save(self, provider, name, response, request, **kwargs):
                self.pages.append(request["page_index"])
                return {"raw_path": f"data/raw/cafef/run/{name}.json",
                        "sha256": "a" * 64, "request": request}
        return Store()

    def test_acb_empty_page_is_source_exhausted_not_max_pages(self):
        page = [self.row(day) for day in range(30, 0, -1)]
        store = self.store()
        with self.assertRaisesRegex(
                ValueError,
                r"symbol=ACB.*oldest_date_observed=2026-01-01.*last_page=2.*SOURCE_EXHAUSTED_EMPTY_PAGE"):
            _execute_job(self.job, {"cafef": {"page_size": 30}}, None,
                         self.source([page, []]), store)
        self.assertEqual([1, 2], store.pages)

    def test_explicit_diagnostic_policy_checkpoints_source_exhaustion(self):
        page = [self.row(day) for day in range(30, 0, -1)]
        store = self.store()
        job = dict(self.job, source_exhaustion_policy="CHECKPOINT_PARTIAL_FAIL_GATE")
        artifacts = _execute_job(
            job, {"cafef": {"page_size": 30}}, None, self.source([page, []]), store)
        self.assertEqual([1, 2], store.pages)
        self.assertEqual("PARTIAL_SOURCE_EXHAUSTED", artifacts[-1]["coverage"]["status"])
        self.assertEqual("2026-01-01", artifacts[-1]["coverage"]["oldest_date_observed"])
        self.assertEqual("SOURCE_EXHAUSTED_EMPTY_PAGE",
                         artifacts[-1]["coverage"]["termination_reason"])

    def test_partial_final_page_is_source_exhausted(self):
        store = self.store()
        with self.assertRaisesRegex(ValueError, "SOURCE_EXHAUSTED_PARTIAL_PAGE"):
            _execute_job(self.job, {"cafef": {"page_size": 30}}, None,
                         self.source([[self.row(30), self.row(29)]]), store)
        self.assertEqual([1], store.pages)

    def test_actual_page_limit_reports_max_pages(self):
        page1 = [self.row(day) for day in range(30, 0, -1)]
        page2 = [self.row(1, f"2025-12-{day:02d}T17:00:00+07:00")
                 for day in range(31, 1, -1)]
        with self.assertRaisesRegex(ValueError, "termination_reason=MAX_PAGES_REACHED"):
            _execute_job(self.job, {"cafef": {"page_size": 30}}, None,
                         self.source([page1, page2]), self.store())

    def test_repeated_page_fails_before_more_requests(self):
        page = [self.row(day) for day in range(30, 0, -1)]
        store = self.store()
        with self.assertRaisesRegex(ValueError, "termination_reason=REPEATED_PAGE"):
            _execute_job(self.job, {"cafef": {"page_size": 30}}, None,
                         self.source([page, page]), store)
        self.assertEqual([1, 2], store.pages)

    def test_sentinel_outside_leading_position_fails_with_context(self):
        rows = [self.row(30), self.row(29, "/Date(-62135596800000)/")]
        with self.assertRaisesRegex(
                SemanticValidationError,
                r"provider=cafef symbol=ACB page=2 row_index=1 raw_trade_date='/Date"):
            _map_cafef_page_rows(rows, self.job, 2)

    def test_manifest_raw_replay_excludes_leading_snapshot_without_mutating_raw(self):
        snapshot = self.row(30, "/Date(-62135596800000)/")
        historical = self.row(29, "2026-01-29T17:00:00+07:00")
        payload = {"Success": True, "Data": [snapshot, historical]}
        before = json.loads(json.dumps(payload))
        artifact = {"raw_path": "data/raw/cafef/run/cafef-ACB-page-001.json",
                    "sha256": "a" * 64, "request": {"page_index": 1}}
        prepared = {
            "root": ROOT, "config": config("unused.json"),
            "universe": [universe(1)[0] | {
                "ticker": "ACB", "exchange": "HOSE", "sector": "Banks",
            }],
        }
        manifest = {"jobs": {"cafef-ACB": {"job": self.job, "artifacts": [artifact]}}}
        with patch("delta_t1.ingestion.representative_pilot._artifact_payload",
                   return_value=payload):
            result = _build_real_manifest(prepared, {}, manifest)
        self.assertEqual(1, result["symbols"]["ACB"]["cafef_row_count"])
        self.assertEqual(before, payload)


if __name__ == "__main__":
    unittest.main()
