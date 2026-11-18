from __future__ import annotations

import json
import unittest
from email.message import Message
from urllib.error import HTTPError

from delta_t1.ingestion.sources.base import AccessControlError, PublicJsonClient
from delta_t1.ingestion.sources.cafef import (
    apply_invalid_row_policy,
    map_trade_history_row,
    price_band_row_status,
)


class _Response:
    def __init__(self, payload: object, status: int = 200) -> None:
        self._payload = json.dumps(payload).encode("utf-8")
        self.status = status
        self.headers = Message()

        self.headers["Content-Type"] = "application/json"

    def read(self, _max_bytes: int = -1) -> bytes:
        return self._payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class _SequenceOpener:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0

    def open(self, _request: object, timeout: float) -> _Response:
        del timeout
        outcome = self.outcomes.pop(0)
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, _Response)
        return outcome


class CafeFSourceTests(unittest.TestCase):
    @staticmethod
    def cafef_row(**overrides: object) -> dict[str, object]:
        row: dict[str, object] = {
            "Symbol": "FPT",
            "TradeDate": "/Date(1631577600000)/",
            "BasicPrice": 72.4,
            "ClosePrice": 72.7,
            "Volume": 3_977_500,
            "AdjustPrice": 72.7,
            "Ceiling": 77.4,
            "Floor": 67.4,
            "TotalValue": 289_875_000_000,
            "AgreedVolume": 942_900,
            "AgreedValue": 68_159_160_000,
        }
        row.update(overrides)
        return row

    def test_trade_history_mapping_vnd_and_total(self) -> None:
        mapped = map_trade_history_row(self.cafef_row(), "FPT", "HOSE")
        self.assertEqual(mapped["trade_date"], "2021-09-14")
        self.assertEqual(mapped["reference_price"], 72_400)
        self.assertEqual(mapped["traded_value"], 358_034_160_000)
        self.assertEqual(mapped["rights_status"], "RIGHTS_NOT_VERIFIED")

    def test_missing_component_is_not_zero_filled(self) -> None:
        mapped = map_trade_history_row(
            self.cafef_row(AgreedVolume=None, AgreedValue=None), "FPT", "HOSE"
        )
        self.assertIsNone(mapped["put_through_volume"])
        self.assertIsNone(mapped["put_through_value"])
        self.assertIsNone(mapped["traded_value"])

    def test_corrupt_price_band_is_excluded_only_by_pinned_policy(self) -> None:
        raw = self.cafef_row(
            Symbol="VNM", TradeDate="/Date(1631120400000)/",
            BasicPrice=85.4, Ceiling=223.6, Floor=194.4, ClosePrice=85.2,
            AdjustPrice=64.634, Volume=2_452_400, TotalValue=209_239_000_000,
            AgreedVolume=0, AgreedValue=0,
        )
        mapped = map_trade_history_row(raw, "VNM", "HOSE")
        policy = {
            "provider": "cafef", "symbol": "VNM", "trade_date": "2021-09-09",
            "classification": "PROVIDER_CORRUPT_ROW",
            "row_status": "INVALID_REQUIRED_MARKET_ROW", "policy": "EXCLUDE_ROW",
            "expected_raw_fields": {
                "BasicPrice": 85.4, "Ceiling": 223.6, "Floor": 194.4,
                "ClosePrice": 85.2, "AdjustPrice": 64.634, "Volume": 2_452_400,
                "TotalValue": 209_239_000_000, "AgreedVolume": 0, "AgreedValue": 0,
            },
        }
        self.assertEqual(price_band_row_status(mapped), "INVALID_REQUIRED_MARKET_ROW")
        eligible, findings = apply_invalid_row_policy([mapped], policy)
        self.assertEqual(eligible, [])
        self.assertTrue(findings[0]["safe"])

    def test_401_and_403_fail_closed_without_retry(self) -> None:
        for status in (401, 403):
            with self.subTest(status=status):
                error = HTTPError("https://example.test", status, "blocked", Message(), None)
                opener = _SequenceOpener([error, _Response({"unexpected": True})])
                client = PublicJsonClient(
                    opener=opener, attempts=3, sleep=lambda _delay: None, min_interval=0
                )
                with self.assertRaises(AccessControlError):
                    client.get_json("https://example.test")
                self.assertEqual(opener.calls, 1)

    def test_429_honors_retry_after_then_retries_once(self) -> None:
        headers = Message()
        headers["Retry-After"] = "0"
        error = HTTPError("https://example.test", 429, "limited", headers, None)
        opener = _SequenceOpener([error, _Response({"ok": True})])
        client = PublicJsonClient(
            opener=opener, attempts=2, sleep=lambda _delay: None,
            monotonic=lambda: 100.0, min_interval=0,
        )
        self.assertEqual(client.get_json("https://example.test")["payload"], {"ok": True})
        self.assertEqual(opener.calls, 2)


if __name__ == "__main__":
    unittest.main()
