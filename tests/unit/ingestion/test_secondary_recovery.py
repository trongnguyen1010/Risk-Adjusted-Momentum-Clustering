"""Offline tests for Stage A4 secondary recovery."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from delta_t1.ingestion.secondary_recovery import (
    build_request_plan,
    execute_request_plan,
    validate_a3_scope,
    validate_price_basis,
)
from delta_t1.io import encoded


def _raw(symbol, day, *, adjusted=10.0, volume=100):
    row = {
        "Symbol": symbol, "TradeDate": f"{day}T17:00:00+07:00",
        "BasicPrice": 10.0, "ClosePrice": 10.0, "Volume": volume,
        "AdjustPrice": adjusted, "Ceiling": 11.0, "Floor": 9.0,
        "TotalValue": 1_000_000, "AgreedVolume": 0, "AgreedValue": 0,
    }
    return row


class FakeCafeF:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def acquire_trade_history_page(self, request):
        self.calls.append(dict(request))
        payload = {"Success": True, "Data": self.rows if request["page_index"] == 1 else []}
        return {"url": "https://example.invalid/cafef", "status": 200,
                "payload": payload, "body": encoded(payload)}


class SecondaryRecoveryTests(unittest.TestCase):
    def test_price_basis_accepts_stable_near_one_ratio(self):
        before = [(10_000, 10_000), (10_100, 10_100)]
        after = [(10_200, 10_200), (10_300, 10_300)]
        result = validate_price_basis(before, after, min_each_side=2)
        self.assertEqual("MATCH", result["status"])
        self.assertTrue(result["compatible"])

    def test_price_basis_rejects_structural_shift_without_averaging(self):
        before = [(10_000, 10_000), (10_100, 10_100)]
        after = [(10_000, 5_000), (10_200, 5_100)]
        result = validate_price_basis(before, after, min_each_side=2)
        self.assertEqual("PRICE_BASIS_CONFLICT", result["status"])
        self.assertFalse(result["compatible"])

    def test_request_plan_is_a3_subset_and_has_two_sided_context(self):
        securities = [{"security_id": "KBS:HOSE:AAA", "ticker": "AAA", "exchange": "HOSE"}]
        prices = [{"security_id": "KBS:HOSE:AAA", "trade_date": day, "adj_close": 10_000}
                  for day in ("2025-01-01", "2025-01-02", "2025-01-04", "2025-01-05")]
        a3 = [{"security_id": "KBS:HOSE:AAA", "ticker": "AAA", "exchange": "HOSE",
               "trade_date": "2025-01-03", "status": "UNRESOLVED"}]
        requests, _ = build_request_plan(a3, securities, prices, overlap_sessions=2, max_pages=3)
        self.assertEqual(["2025-01-01", "2025-01-02"],
                         requests[0]["overlap_context"]["2025-01-03"]["before"])
        self.assertEqual(["2025-01-04", "2025-01-05"],
                         requests[0]["overlap_context"]["2025-01-03"]["after"])
        with self.assertRaisesRegex(ValueError, "subset"):
            build_request_plan(a3, securities, prices, symbols=["ZZZ"])

    def test_a3_result_ticker_must_be_in_frozen_selection(self):
        rows = [{"ticker": "AAA"}, {"ticker": "ZZZ"}]
        with self.assertRaisesRegex(ValueError, "outside selected_symbols"):
            validate_a3_scope(rows, ["AAA"])

    def _execute(self, target, overlap_rows, *, target_row=None):
        request = {
            "request_id": "cafef-AAA", "security_id": "KBS:HOSE:AAA",
            "ticker": "AAA", "exchange": "HOSE", "targeted_dates": [target],
            "overlap_context": {target: {
                "before": ["2025-01-01", "2025-01-02"],
                "after": ["2025-01-04", "2025-01-05"]}},
            "earliest_needed": "2025-01-01", "latest_needed": "2025-01-05",
            "max_pages": 2,
        }
        rows = [target_row or _raw("AAA", target)] + overlap_rows
        primary = {"KBS:HOSE:AAA": {day: 10_000.0 for day in
                   ("2025-01-01", "2025-01-02", "2025-01-04", "2025-01-05")}}
        temporary = tempfile.TemporaryDirectory()
        output = Path(temporary.name)
        result = execute_request_plan(
            [request], provider=FakeCafeF(rows), output=output,
            primary_by_security=primary, min_overlap_each_side=2)
        return temporary, result

    def test_compatible_diagnostic_does_not_bypass_unapproved_contract(self):
        overlap = [_raw("AAA", day) for day in
                   ("2025-01-01", "2025-01-02", "2025-01-04", "2025-01-05")]
        temporary, (candidates, evidence, statuses, calls) = self._execute(
            "2025-01-03", overlap)
        try:
            self.assertEqual("UNRESOLVED_MISSING", evidence[0]["reconciliation_status"])
            self.assertEqual("SECONDARY_ACCEPTANCE_BLOCKED", candidates[0]["reason"])
            diagnostic = evidence[0]["price_basis_validation"]
            self.assertEqual("MATCH", diagnostic["diagnostic_status"])
            self.assertTrue(diagnostic["diagnostic_compatible"])
            self.assertIn("PRICE_BASIS_ACCEPTANCE_POLICY_UNAPPROVED", diagnostic["validation_blockers"])
            self.assertIn("CAFEF_OHLC_CONTRACT_UNSUPPORTED", diagnostic["validation_blockers"])
            self.assertEqual(1, calls)
            self.assertEqual("EARLIEST_CONTEXT_REACHED", statuses[0]["stop_reason"])
            self.assertTrue((Path(temporary.name) / candidates[0]["raw_path"]).is_file())
        finally:
            temporary.cleanup()

    def test_provider_published_zero_volume_is_preserved_but_not_synthesized(self):
        overlap = [_raw("AAA", day) for day in
                   ("2025-01-01", "2025-01-02", "2025-01-04", "2025-01-05")]
        target = _raw("AAA", "2025-01-03", volume=0)
        temporary, (candidates, evidence, _, _) = self._execute(
            "2025-01-03", overlap, target_row=target)
        try:
            self.assertEqual(0, candidates[0]["volume"])
            self.assertIn('"Volume": 0', candidates[0]["raw_row_json"])
            self.assertEqual("UNRESOLVED_MISSING", evidence[0]["reconciliation_status"])
            self.assertEqual("MATCH", evidence[0]["price_basis_validation"]["diagnostic_status"])
        finally:
            temporary.cleanup()

    def test_a5_remediation_gate_keeps_b0_blocked(self):
        root = Path(__file__).resolve().parents[3]
        plan = (root / "docs" / "crawl" /
                "M1_DATA_ENRICHMENT_AND_UNIVERSE_EXPANSION_MASTER_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("A5-R1 — CafeF Contract & Endpoint Validation", plan)
        self.assertIn("B0 may begin only when multi-source recovery semantics are frozen", plan)
        self.assertLess(plan.index("# A5 Remediation Track"), plan.index("# Stage B0"))

    def test_no_target_row_is_missing_not_zero_filled(self):
        request = {
            "request_id": "cafef-AAA", "security_id": "KBS:HOSE:AAA",
            "ticker": "AAA", "exchange": "HOSE", "targeted_dates": ["2025-01-03"],
            "overlap_context": {"2025-01-03": {"before": [], "after": []}},
            "earliest_needed": "2025-01-03", "latest_needed": "2025-01-03", "max_pages": 1,
        }
        with tempfile.TemporaryDirectory() as tmp:
            _, evidence, _, _ = execute_request_plan(
                [request], provider=FakeCafeF([]), output=Path(tmp),
                primary_by_security={"KBS:HOSE:AAA": {}})
        self.assertEqual("MISSING_ON_SOURCE", evidence[0]["reconciliation_status"])
        self.assertNotIn("0", evidence[0].values())

    def test_target_row_with_wrong_symbol_is_identity_conflict(self):
        request = {
            "request_id": "cafef-AAA", "security_id": "KBS:HOSE:AAA",
            "ticker": "AAA", "exchange": "HOSE", "targeted_dates": ["2025-01-03"],
            "overlap_context": {"2025-01-03": {"before": [], "after": []}},
            "earliest_needed": "2025-01-03", "latest_needed": "2025-01-03", "max_pages": 1,
        }
        with tempfile.TemporaryDirectory() as tmp:
            candidates, evidence, _, _ = execute_request_plan(
                [request], provider=FakeCafeF([_raw("BBB", "2025-01-03")]),
                output=Path(tmp), primary_by_security={"KBS:HOSE:AAA": {}})
        self.assertEqual("IDENTITY_CONFLICT", evidence[0]["reconciliation_status"])
        self.assertEqual("IDENTITY_CONFLICT", candidates[0]["reconciliation_status"])

    def test_target_row_with_naive_iso_date_is_timing_conflict(self):
        request = {
            "request_id": "cafef-AAA", "security_id": "KBS:HOSE:AAA",
            "ticker": "AAA", "exchange": "HOSE", "targeted_dates": ["2025-01-03"],
            "overlap_context": {"2025-01-03": {"before": [], "after": []}},
            "earliest_needed": "2025-01-03", "latest_needed": "2025-01-03", "max_pages": 1,
        }
        invalid = _raw("AAA", "2025-01-03")
        invalid["TradeDate"] = "2025-01-03T17:00:00"
        with tempfile.TemporaryDirectory() as tmp:
            candidates, evidence, _, _ = execute_request_plan(
                [request], provider=FakeCafeF([invalid]), output=Path(tmp),
                primary_by_security={"KBS:HOSE:AAA": {}})
        self.assertEqual("TIMING_CONFLICT", evidence[0]["reconciliation_status"])
        self.assertEqual("TIMING_CONFLICT", candidates[0]["reconciliation_status"])


if __name__ == "__main__":
    unittest.main()
