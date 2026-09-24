import unittest

from delta_t1.features.market import momentum
from delta_t1.ingestion.cafef_canonical_market import (
    _coverage_exceptions,
    _dependency_report,
    _interval_for_day,
    _null_safe_total,
    _stage_status,
    map_candidate,
)


class CafeFCanonicalMarketTests(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "security_id": "SEC-ABC",
            "ticker": "ABC",
            "identity_intervals": (
                '[{"effective_from":"2020-01-01","effective_to":null,'
                '"exchange":"HOSE","ticker":"ABC","evidence_id":"TEST"}]'
            ),
        }
        self.candidate = {
            "candidate_id": "candidate-1",
            "security_id": "SEC-ABC",
            "ticker": "ABC",
            "exchange": "HOSE",
            "trade_date": "2025-07-18",
            "provider_adjusted_vnd": 72700.0,
            "provider_open_vnd": 74000.0,
            "provider_high_vnd": 75000.0,
            "provider_low_vnd": 72000.0,
            "provider_close_vnd": 73000.0,
            "matched_volume_shares": 1000,
            "negotiated_volume_shares": 200,
            "matched_value_vnd": 10_000_000.0,
            "negotiated_value_vnd": 2_000_000.0,
            "quality_flags": [],
            "fetched_at": "2026-09-24T00:00:00+00:00",
        }

    def test_price_mapping_uses_adjusted_only_and_eod_availability(self):
        row = map_candidate(self.candidate, self.plan, "canonical-test")
        self.assertEqual(72700.0, row["adj_close"])
        self.assertEqual("vendor_adjusted", row["adjustment_basis"])
        self.assertEqual("canonical-test", row["data_version"])
        self.assertEqual([None, None, None, None], [
            row["raw_open"], row["raw_high"], row["raw_low"], row["raw_close"],
        ])
        self.assertEqual("2025-07-18T17:00:00+07:00", row["available_at"])
        self.assertEqual("normal", row["trading_status"])

    def test_total_activity_is_exact_and_null_safe(self):
        row = map_candidate(self.candidate, self.plan, "canonical-test")
        self.assertEqual(1200, row["volume"])
        self.assertEqual(12_000_000.0, row["traded_value"])
        zero = map_candidate(dict(self.candidate, negotiated_volume_shares=0), self.plan, "canonical-test")
        self.assertEqual(1000, zero["volume"])
        missing = map_candidate(dict(self.candidate, negotiated_volume_shares=None), self.plan, "canonical-test")
        self.assertIsNone(missing["volume"])
        self.assertIsNone(_null_safe_total(1000, None))

    def test_quarantine_and_invalid_adjusted_close_are_not_promoted(self):
        quarantined = dict(self.candidate, quality_flags=["INVALID_OHLC"])
        self.assertIsNone(map_candidate(quarantined, self.plan, "canonical-test"))
        self.assertIsNone(map_candidate(dict(self.candidate, provider_adjusted_vnd=0), self.plan, "canonical-test"))

    def test_zero_matched_volume_is_unknown_not_suspended(self):
        row = map_candidate(dict(self.candidate, matched_volume_shares=0), self.plan, "canonical-test")
        self.assertEqual("unknown", row["trading_status"])
        self.assertEqual(200, row["volume"])

    def test_identity_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "exchange mismatch"):
            map_candidate(dict(self.candidate, exchange="HNX"), self.plan, "canonical-test")

    def test_bcm_ctr_shb_route_historical_intervals(self):
        cases = {
            "BCM": ('[{"effective_from":"2018-07-10","effective_to":"2020-08-30","exchange":"UPCOM"},'
                    '{"effective_from":"2020-08-31","effective_to":null,"exchange":"HOSE"}]',
                    [("2020-08-28", "UPCOM"), ("2020-08-31", "HOSE")]),
            "CTR": ('[{"effective_from":"2018-12-06","effective_to":"2022-02-22","exchange":"UPCOM"},'
                    '{"effective_from":"2022-02-23","effective_to":null,"exchange":"HOSE"}]',
                    [("2022-02-22", "UPCOM"), ("2022-02-23", "HOSE")]),
            "SHB": ('[{"effective_from":"2009-04-20","effective_to":"2021-10-10","exchange":"HNX"},'
                    '{"effective_from":"2021-10-11","effective_to":null,"exchange":"HOSE"}]',
                    [("2021-10-08", "HNX"), ("2021-10-11", "HOSE")]),
        }
        for ticker, (intervals, observations) in cases.items():
            plan = {"ticker": ticker, "identity_intervals": intervals}
            for day, exchange in observations:
                self.assertEqual(exchange, _interval_for_day(plan, day)["exchange"])

    def test_feature_dependencies_and_missing_session_policy_match_builder(self):
        config = {
            "feature_set": "delta_market_1.5.0",
            "required_features": [
                "mom_21", "mom_63", "mom_126", "mom_252",
                "vol_63", "mdd_126", "beta_126", "liquidity_21",
            ],
        }
        report = _dependency_report(config)
        self.assertIn("benchmark_daily.close", report["dependencies"]["beta_126"])
        self.assertIn("prices_daily.traded_value", report["dependencies"]["liquidity_21"])
        self.assertEqual("None; no fill, interpolation, zero return, or timeline compression",
                         report["missing_session_policy"])
        self.assertIsNone(momentum([100.0] * 21 + [None], 21))

    def test_coverage_exceptions_ignore_intervals_outside_window(self):
        plan = [{
            "security_id": "SEC-BCM",
            "ticker": "BCM",
            "identity_intervals": (
                '[{"effective_from":"2018-07-10","effective_to":"2020-08-30","exchange":"UPCOM"},'
                '{"effective_from":"2020-08-31","effective_to":null,"exchange":"HOSE"}]'
            ),
        }]
        candidates = [{
            "security_id": "SEC-BCM", "exchange": "HOSE", "trade_date": "2021-09-23",
        }]
        self.assertEqual([], _coverage_exceptions(plan, candidates, "2021-09-23", "2026-09-23"))

    def test_stage_status_does_not_lower_market_feature_gate(self):
        self.assertEqual(
            "PARTIAL_MANUAL_REVIEW_REQUIRED",
            _stage_status({"schemas": True}, {"market_feature_ready": 26}),
        )
        self.assertEqual("PASS", _stage_status({"schemas": True}, {"market_feature_ready": 27}))


if __name__ == "__main__":
    unittest.main()
