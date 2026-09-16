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
    OFFICIAL_MARKET_SOURCES, build_job_plan, dry_run, load_readiness,
    validate_source_gate, validate_universe,
)
from delta_t1.ingestion.sources.vnstock import KBSPublicHttpSource, collect
from delta_t1.io import read_json, write_json


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
