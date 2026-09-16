import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.planning import (
    M1_SCALE, REPRESENTATIVE_PILOT, SOURCE_SMOKE, plan_extended_scale,
    plan_m1_scale, representative_pilot_report, source_smoke_report,
)
from delta_t1.io import read_json
from delta_t1.pipeline import load_config


def source_evidence(synthetic=False):
    return {
        "synthetic": synthetic,
        "symbol_count": 4,
        "representative_exchange_evidence": "HOSE/HNX/UPCOM + edge case",
        "requested_history_years": 5,
        "verified_market_fields": [
            "open", "high", "low", "close", "reference_price", "ceiling_price",
            "floor_price", "volume", "traded_value",
        ],
        "required_symbol_market_checks_passed": True,
        "benchmark_passed": True,
        "history_depth_passed": True,
        "safe_anomaly_policy_applied": True,
        "volume_semantics_safe": True,
        "provenance_valid": True,
        "cafef_window_evidence_hashed": True,
        "corporate_actions_inspected": 2,
        "shares_capital_structure_documented": True,
        "quarterly_reports_inspected": 3,
        "collection_semantics_verified": True,
        "rights_reviewed": True,
        "evidence_hashes": {"source-review.json": "a" * 64},
    }


def pilot_evidence(synthetic=False):
    return {
        "synthetic": synthetic, "symbol_count": 55, "history_years": 5.2,
        "representative_exchanges": True, "representative_sectors": True,
        "historical_identity_verified": True,
        "price_and_corporate_action_semantics_verified": True,
        "multi_source_reconciliation_reviewed": True,
        "pit_financial_support_verified": True, "qc_and_coverage_passed": True,
        "evidence_hashes": {"pilot-manifest.json": "b" * 64},
    }


class PlanningGateTests(unittest.TestCase):
    def test_synthetic_cannot_pass_real_gates(self):
        smoke = source_smoke_report(source_evidence(synthetic=True))
        self.assertEqual((SOURCE_SMOKE, "FAIL"), (smoke["gate"], smoke["status"]))
        real_smoke = source_smoke_report(source_evidence())
        pilot = representative_pilot_report(pilot_evidence(synthetic=True), real_smoke)
        self.assertEqual("BLOCKED", pilot["status"])
        self.assertIn("real_data", pilot["blocking_reasons"])

    def test_only_representative_pilot_unlocks_m1_scale(self):
        smoke = source_smoke_report(source_evidence())
        self.assertEqual("PASS", smoke["status"])
        self.assertEqual([REPRESENTATIVE_PILOT], smoke["unlocks"])
        self.assertTrue(smoke["checks"]["real_data"])
        self.assertTrue(smoke["input_evidence_hashes"])
        config = {"start": "2020-01-01", "end": "2025-12-31",
                  "symbols": [f"S{i:03d}" for i in range(300)],
                  "universe_evidence": "reviewed", "evidence_hashes": {}}
        self.assertEqual("BLOCKED", plan_m1_scale(config, smoke)["status"])
        pilot = representative_pilot_report(pilot_evidence(), smoke)
        plan = plan_m1_scale(config, pilot)
        self.assertEqual((M1_SCALE, "PLANNED"), (plan["gate"], plan["status"]))

    def test_extended_scale_has_no_350_symbol_cap(self):
        pilot = representative_pilot_report(pilot_evidence(), source_smoke_report(source_evidence()))
        config = {"start": "2011-01-01", "end": "2025-12-31",
                  "symbols": [f"S{i:04d}" for i in range(1201)],
                  "universe_evidence": "reviewed historical universe"}
        self.assertEqual("PLANNED", plan_extended_scale(config, pilot)["status"])

    def test_source_smoke_required_failure_has_no_unlocks(self):
        evidence = source_evidence()
        evidence["required_symbol_market_checks_passed"] = False
        smoke = source_smoke_report(evidence)
        self.assertEqual("FAIL", smoke["status"])
        self.assertEqual([], smoke["unlocks"])
        self.assertIn("required_symbol_market_checks_passed", smoke["blocking_reasons"])

    def test_smoke_configs_are_unambiguous_and_source_template_fails_closed(self):
        self.assertFalse((ROOT / "configs/data/smoke.example.json").exists())
        self.assertTrue(read_json(ROOT / "configs/data/synthetic_smoke.example.json")["synthetic"])
        source = read_json(ROOT / "configs/data/source_smoke.example.json")
        self.assertFalse(source["synthetic"])
        self.assertEqual(4, len(source["symbols"]))
        self.assertNotIn("example.invalid", str(source).lower())
        self.assertNotIn("jobs", source)
        with self.assertRaisesRegex(ValueError, "fail-closed"):
            load_config(ROOT / "configs/data/source_smoke.example.json")


if __name__ == "__main__":
    unittest.main()
