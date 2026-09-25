import csv
import importlib.util
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from delta_t1.ingestion.cafef_c8 import (
    DEFERRED_DECISION,
    SNAPSHOT_DATE,
    apply_snapshot_cutoff,
    build_scope,
    build_session_audits,
    calendar_audit_policy,
    canonical_market_row,
    current_security_rows,
    data_quality_gate,
    expansion_security_rows,
    load_identity_review,
    readiness_rows,
    resolve_observations,
    sha256_file,
    verify_manifest_outputs,
)
from delta_t1.features.market import market_metadata_available
from delta_t1.ingestion.cafef_market_semantics import classify_activity

ROOT = Path(__file__).resolve().parents[3]


def candidate(sid="SID", ticker="AAA", start="2020-01-01"):
    return {
        "security_id": sid, "ticker": ticker, "exchange": "HOSE",
        "candidate_source": "C7_COMPLETE_EXPANSION", "audit_start": start,
        "boundary_basis": "TARGET_START",
    }


class CafeFC8ScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = build_scope(ROOT)

    def test_exact_complete_deferred_and_combined_scope(self):
        self.assertEqual(452, len(self.scope["expansion"]))
        self.assertEqual(148, len(self.scope["deferred"]))
        self.assertEqual(952, len(self.scope["candidates"]))
        self.assertEqual(
            {"DEFERRED_EXPANSION_ACQUISITION"},
            {row["current_c8_decision"] for row in self.scope["deferred"]},
        )

    def test_expansion_metadata_timestamp_is_truthful_and_not_backdated(self):
        metadata = expansion_security_rows(self.scope)
        self.assertEqual(452, len(metadata))
        self.assertEqual({"2026-09-25T00:00:00+07:00"},
                         {row["available_at"] for row in metadata})
        self.assertEqual({"OBSERVED_PROVIDER_INTERVAL"},
                         {row["market_observation_routing"] for row in metadata})
        self.assertEqual({"provisional"}, {row["identity_status"] for row in metadata})
        self.assertEqual({None}, {row["listing_date"] for row in metadata})

    def test_bounded_real_feature_engine_probe_accepts_market_but_not_identity(self):
        spec = importlib.util.spec_from_file_location(
            "c8_runner_semantic_probe", ROOT / "scripts/run_cafef_c8_complete_only.py"
        )
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        runner.validate_expansion_feature_semantics(self.scope)

    def test_baseline_expansion_identity_is_disjoint(self):
        baseline = self.scope["baseline"]
        expansion = self.scope["expansion"]
        self.assertTrue({row["ticker"] for row in baseline}.isdisjoint(
            {row["ticker"] for row in expansion}
        ))
        self.assertTrue({row["security_id"] for row in baseline}.isdisjoint(
            {row["security_id"] for row in expansion}
        ))

    def test_active_identity_review_reproduces_legacy_alias_set(self):
        active = load_identity_review(ROOT / "configs/data/identity_review_v1.json")
        legacy_path = ROOT / "docs/crawl/plans/cafef_c1_prep_v1/cafef_c1_candidate_universe.csv"
        with legacy_path.open(encoding="utf-8", newline="") as handle:
            legacy_rows = list(csv.DictReader(handle))
        legacy = {row["current_ticker"].upper() for row in legacy_rows if row["current_ticker"]}
        for row in legacy_rows:
            legacy.update(str(interval.get("ticker", "")).upper()
                          for interval in json.loads(row["historical_identity_intervals"] or "[]")
                          if interval.get("ticker"))
        self.assertEqual(legacy, active)
        self.assertTrue(active.isdisjoint({row["ticker"] for row in self.scope["expansion"]}))

    def test_deferred_acquisition_is_not_provider_gap(self):
        forbidden = {"MISSING_ON_TRADEHISTORYNEW", "PROVIDER_GAP_CONFIRMED",
                     "SUSPENDED_OR_HALTED", "NOT_LISTED"}
        self.assertTrue(all(row["current_c8_decision"] == DEFERRED_DECISION
                            for row in self.scope["deferred"]))
        self.assertTrue(forbidden.isdisjoint(
            {row["current_c8_decision"] for row in self.scope["deferred"]}
        ))


class CafeFC8SemanticsTests(unittest.TestCase):
    def test_observed_interval_routing_is_scoped_and_baseline_remains_strict(self):
        cutoff = datetime.fromisoformat("2026-08-28T17:00:00+07:00")
        expansion = {
            "available_at": "2026-09-25T00:00:00+07:00",
            "identity_status": "provisional",
            "market_observation_routing": "OBSERVED_PROVIDER_INTERVAL",
        }
        config = {"market_observation_routing": "OBSERVED_PROVIDER_INTERVAL"}
        self.assertTrue(market_metadata_available(expansion, cutoff, config, True))
        self.assertFalse(market_metadata_available(expansion, cutoff, {}, True))
        self.assertFalse(market_metadata_available(expansion, cutoff, config, False))
        baseline = {"available_at": "2026-09-25T00:00:00+07:00",
                    "identity_status": "provisional"}
        self.assertFalse(market_metadata_available(baseline, cutoff, config, True))

    def test_snapshot_cutoff_excludes_post_snapshot_rows(self):
        rows = [{"trade_date": SNAPSHOT_DATE}, {"trade_date": "2026-09-01"}]
        self.assertEqual([{"trade_date": SNAPSHOT_DATE}], apply_snapshot_cutoff(rows))

    def test_zero_and_null_activity_semantics_are_preserved(self):
        self.assertEqual("OBSERVED_ZERO_VOLUME", classify_activity(0, 0)["trading_activity_status"])
        self.assertEqual(0, classify_activity(0, 0)["volume"])
        self.assertEqual("UNKNOWN_ACTIVITY_COMPONENTS", classify_activity(0, None)["trading_activity_status"])
        self.assertIsNone(classify_activity(0, None)["volume"])

    def test_normalization_does_not_impute_and_adjusts_price(self):
        mapped = {
            "security_id": "SID", "ticker": "AAA", "exchange": "HOSE",
            "trade_date": "2026-08-28", "cafef_close_price": 12000,
            "cafef_adjust_price": 11000, "reference_price": 11900,
            "ceiling_price": 12800, "floor_price": 11000,
            "matched_volume": 0, "put_through_volume": None,
            "matched_value": 0, "put_through_value": None,
        }
        row = canonical_market_row(mapped, {
            "handoff_run_id": "r", "raw_path": "raw/AAA/page-001.json",
            "raw_sha256": "a" * 64, "fetched_at": "2026-09-23T00:00:00Z",
        })
        self.assertEqual(11000, row["adj_close"])
        self.assertEqual("vendor_adjusted", row["adjustment_basis"])
        self.assertIsNone(row["volume"])
        self.assertIsNone(row["traded_value"])
        self.assertIsNone(row["raw_open"])

    def test_conflicts_are_not_averaged_or_filled(self):
        common = {
            "security_id": "SID", "ticker": "AAA", "trade_date": "2026-08-28",
            "raw_close": 10, "reference_price": 10, "ceiling_price": 11,
            "floor_price": 9, "matched_volume_shares": 1,
            "negotiated_volume_shares": 0, "matched_value_vnd": 10,
            "negotiated_value_vnd": 0,
        }
        clean, conflicts = resolve_observations([
            {**common, "adj_close": 10}, {**common, "adj_close": 11},
        ])
        self.assertEqual([], clean)
        self.assertEqual("CONFLICTING_PROVIDER_OBSERVATION", conflicts[0]["classification"])

    def test_full_history_and_latest253_are_independent(self):
        start = date(2025, 1, 1)
        days = [(start + timedelta(days=index)).isoformat() for index in range(300)]
        calendar = [{"exchange": "HOSE", "trade_date": day, "is_open": True} for day in days]
        valid = {("SID", day) for day in days[-253:]}
        full, latest = build_session_audits(
            [candidate(start=days[0])], calendar, valid, set(), set(), snapshot=days[-1]
        )
        self.assertFalse(full[0]["full_history_complete"])
        self.assertTrue(latest[0]["latest253_complete"])

    def test_uncertain_calendar_absence_is_not_confirmed_provider_missing(self):
        calendar = [{"exchange": "HOSE", "trade_date": "2020-01-02", "is_open": True,
                     "source": "kbs_observed_session_union"}]
        policy = calendar_audit_policy(calendar)
        self.assertEqual("CALENDAR_UNCERTAIN", policy["absence_classification"])
        full, latest = build_session_audits(
            [candidate(start="2020-01-01")], calendar, set(), set(), set(),
            snapshot="2020-01-02",
        )
        self.assertEqual(1, full[0]["calendar_uncertain"])
        self.assertEqual(0, full[0]["missing_on_tradehistorynew"])
        self.assertEqual(1, latest[0]["calendar_uncertain_253"])
        self.assertEqual(0, latest[0]["missing_sessions_253"])

    def test_latest253_requires_calendar_aligned_real_observations(self):
        start = date(2025, 1, 1)
        days = [(start + timedelta(days=index)).isoformat() for index in range(253)]
        calendar = [{"exchange": "HOSE", "trade_date": day, "is_open": True} for day in days]
        valid = {("SID", day) for day in days[:-1]}
        valid.add(("SID", "2024-12-31"))
        _, latest = build_session_audits(
            [candidate(start=days[0])], calendar, valid, set(), set(), snapshot=days[-1]
        )
        self.assertEqual(252, latest[0]["observed_valid_253"])
        self.assertFalse(latest[0]["latest253_complete"])

    def test_provider_boundary_is_deferred_review_not_listing_claim(self):
        days = ["2020-01-02", "2020-01-03", "2020-01-06"]
        calendar = [{"exchange": "HOSE", "trade_date": day, "is_open": True} for day in days]
        full, _ = build_session_audits(
            [candidate(start="2020-01-06")], calendar, {("SID", "2020-01-06")},
            set(), set(), snapshot="2020-01-06",
        )
        self.assertEqual(0, full[0]["identity_or_listing_boundary"])
        self.assertEqual(2, full[0]["deferred_review"])
        self.assertTrue(full[0]["observed_window_complete"])
        self.assertEqual("UNCERTAIN_BOUNDARY", full[0]["full_history_status"])
        self.assertFalse(full[0]["full_history_complete"])

    def test_valid_to_is_exclusive(self):
        rows = [
            {"security_id": "SID", "ticker": "OLD", "valid_from": "2020-01-01",
             "valid_to": "2026-08-28"},
            {"security_id": "SID", "ticker": "NEW", "valid_from": "2026-08-28",
             "valid_to": None},
        ]
        current = current_security_rows(rows, "2026-08-28")
        self.assertEqual("NEW", current[0]["ticker"])

    def test_market_readiness_is_independent_from_tradability(self):
        c = candidate()
        full = [{"security_id": "SID", "full_history_complete": True}]
        latest = [{"security_id": "SID", "latest253_complete": True}]
        feature = {name: 1.0 for name in (
            "mom_21", "mom_63", "mom_126", "mom_252", "vol_63", "mdd_126",
            "beta_126", "liquidity_21",
        )}
        feature.update(feature_complete=True, market_feature_ready=True,
                       historical_identity_ready=False, research_ready=False)
        output = readiness_rows(
            [c], {"SID": feature}, full, latest,
            {"SID": {"trading_activity_status": "OBSERVED_ZERO_VOLUME",
                     "tradability_eligible": False}},
        )[0]
        self.assertTrue(output["market_feature_ready_v2"])
        self.assertFalse(output["tradability_eligible"])

    def test_execution_integrity_is_separate_from_data_quality(self):
        readiness = [{"market_feature_ready_v2": False}]
        latest = [{"latest253_complete": False}]
        self.assertEqual("PARTIAL", data_quality_gate(readiness, latest))
        self.assertEqual("FAIL", data_quality_gate([], []))
        ready = [{"market_feature_ready_v2": True}]
        complete_latest = [{"latest253_complete": True}]
        incomplete_full = [{"full_history_status": "INCOMPLETE"}]
        uncertain_boundary = [{"full_history_status": "UNCERTAIN_BOUNDARY"}]
        self.assertEqual("PARTIAL", data_quality_gate(ready, complete_latest, incomplete_full))
        self.assertEqual("PASS", data_quality_gate(ready, complete_latest, uncertain_boundary))

    def test_manifest_hash_integrity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "output.txt").write_text("evidence", encoding="utf-8")
            (root / "manifest.json").write_text(json.dumps({
                "outputs": {"output.txt": sha256_file(root / "output.txt")}
            }), encoding="utf-8")
            verify_manifest_outputs(root)
            (root / "output.txt").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify_manifest_outputs(root)


if __name__ == "__main__":
    unittest.main()
