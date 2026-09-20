import copy
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
TMP_ROOT = ROOT / "tmp"
TMP_ROOT.mkdir(exist_ok=True)

from delta_t1.ingestion.session_audit import build_a1_audit, write_a1_parquet


def _security(**changes):
    row = {"security_id": "SEC:AAA", "ticker": "AAA", "exchange": "HOSE",
           "valid_from": "2024-01-02", "valid_to": None, "listing_date": "2024-01-03",
           "delisting_date": "2024-01-05", "identity_status": "verified"}
    return row | changes


def _calendar(source="official_fixture"):
    return [{"exchange": "HOSE", "trade_date": day, "is_open": True, "source": source}
            for day in ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05")]


def _features(**changes):
    row = {"security_id": "SEC:AAA", "as_of_date": "2024-01-05", "mom_21": 1,
           "mom_63": 1, "mom_126": 1, "mom_252": 1, "market_feature_ready": True}
    return [row | changes]


class SessionAuditTests(unittest.TestCase):
    def test_expected_sessions_respect_effective_listing_and_delisting_evidence(self):
        detail, symbols, _, _ = build_a1_audit(
            [_security()], [{"security_id": "SEC:AAA", "trade_date": "2024-01-03", "source": "local"}],
            _calendar(), _features(), collection_end="2024-02-01")
        self.assertEqual(2, symbols[0]["expected_sessions_total"])
        self.assertEqual(["2024-01-04"], [row["trading_date"] for row in detail])

    def test_missing_is_not_zero_or_filled_and_provisional_is_not_provider_gap(self):
        prices = [{"security_id": "SEC:AAA", "trade_date": "2024-01-03", "raw_close": 12.5, "source": "local"}]
        original = copy.deepcopy(prices)
        detail, _, recovery, _ = build_a1_audit(
            [_security(identity_status="provisional")], prices, _calendar("kbs_observed_session_union"),
            _features(market_feature_ready=False, mom_252=None), collection_end="2024-02-01")
        self.assertEqual(prices, original)
        self.assertEqual("CALENDAR_UNCERTAIN", detail[0]["missing_classification"])
        self.assertEqual("P4", recovery[0]["recovery_priority"])
        self.assertNotEqual(0, prices[0]["raw_close"])

    def test_momentum_252_uses_baseline_complete_observation_semantics(self):
        _, symbols, _, _ = build_a1_audit(
            [_security()], [{"security_id": "SEC:AAA", "trade_date": "2024-01-03", "source": "local"}],
            _calendar(), _features(mom_252=None, market_feature_ready=False), collection_end="2024-02-01")
        self.assertFalse(symbols[0]["mom252_complete"])
        self.assertFalse(symbols[0]["market_feature_ready"])

    def test_audit_is_deterministic_and_parquet_has_valid_magic(self):
        args = ([_security()], [{"security_id": "SEC:AAA", "trade_date": "2024-01-03", "source": "local"}],
                _calendar(), _features())
        one = build_a1_audit(*args, collection_end="2024-02-01")
        two = build_a1_audit(*args, collection_end="2024-02-01")
        self.assertEqual(one, two)
        path = TMP_ROOT / "session-audit-test.parquet"
        try:
            write_a1_parquet(path, one[0])
            payload = path.read_bytes()
        finally:
            path.unlink(missing_ok=True)
        self.assertTrue(payload.startswith(b"PAR1") and payload.endswith(b"PAR1"))


if __name__ == "__main__":
    unittest.main()
