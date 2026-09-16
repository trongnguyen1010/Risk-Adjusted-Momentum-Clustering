import json
import sys
import unittest
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.sources.base import AccessControlError, PublicJsonClient
from delta_t1.ingestion.sources.cafef import map_trade_history_row
from delta_t1.ingestion.sources.vnstock import (financial_raw_only_metadata,
                                                 map_vnstock_ohlcv_row)


class Response:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode()
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _):
        return self.body


class SequenceOpener:
    def __init__(self, *items):
        self.items = list(items)
        self.calls = 0

    def open(self, *_args, **_kwargs):
        self.calls += 1
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class ResearchDemoSourceTests(unittest.TestCase):
    def cafef_row(self, **changes):
        row = {"Symbol": "FPT", "TradeDate": "/Date(1631577600000)/", "BasicPrice": 72.4,
               "ClosePrice": 72.7, "Volume": 3977500, "AdjustPrice": 72.7,
               "Ceiling": 77.4, "Floor": 67.4, "TotalValue": 289875000000,
               "AgreedVolume": 942900, "AgreedValue": 68159160000}
        row.update(changes)
        return row

    def test_cafef_trade_history_mapping_vnd_and_total(self):
        row = map_trade_history_row(self.cafef_row(), "FPT", "HOSE")
        self.assertEqual(row["trade_date"], "2021-09-14")
        self.assertEqual(row["reference_price"], 72400)
        self.assertEqual(row["ceiling_price"], 77400)
        self.assertEqual(row["floor_price"], 67400)
        self.assertEqual(row["traded_value"], 358034160000)
        self.assertEqual(row["rights_status"], "RIGHTS_NOT_VERIFIED")
        self.assertEqual(row["execution_policy"], "ACCEPTED_RESEARCH_RISK")

    def test_cafef_missing_component_is_not_zero_filled(self):
        row = map_trade_history_row(self.cafef_row(AgreedValue=None, AgreedVolume=None), "FPT", "HOSE")
        self.assertIsNone(row["put_through_value"])
        self.assertIsNone(row["put_through_volume"])
        self.assertIsNone(row["traded_value"])

    def test_kbs_vnstock_price_transform_and_basis(self):
        row = map_vnstock_ohlcv_row({"time": "2026-09-15", "open": 72.7, "high": 73.4,
                                    "low": 72.5, "close": 72.7, "volume": 3977500},
                                   "FPT", "HOSE")
        self.assertEqual(row["open"], 72700)
        self.assertEqual(row["price_basis"], "VENDOR_ADJUSTED")
        self.assertEqual(row["provider"], "kbs")
        self.assertEqual(row["acquisition_client"], "vnstock")

    def test_financial_metadata_stays_raw_only_pit_unresolved(self):
        meta = financial_raw_only_metadata({"Head": [{"ReportDate": "2026-07-21T00:00:00",
            "DatePubDepartment": "2026-07-28T00:00:00", "CreatedDate": "2026-07-28T09:40:14",
            "LastUpdate": "2026-07-31T23:00:17", "PeriodBegin": 202604, "PeriodEnd": 202606,
            "YearPeriod": 2026, "TermCode": 2, "United": "HN", "AuditedStatus": "CKT"}]})[0]
        self.assertIsNone(meta["published_at"])
        self.assertIsNone(meta["available_at"])
        self.assertEqual(meta["pit_status"], "PIT_UNRESOLVED")

    def test_401_and_403_fail_closed_without_retry(self):
        for status in (401, 403):
            error = HTTPError("https://example.test", status, "stopped", Message(), None)
            opener = SequenceOpener(error)
            with self.assertRaises(AccessControlError):
                PublicJsonClient(opener=opener, sleep=lambda _: None, min_interval=0).get_json("https://example.test")
            self.assertEqual(opener.calls, 1)

    def test_429_honors_retry_after_then_retries_once(self):
        headers = Message(); headers["Retry-After"] = "3"
        waits = []
        opener = SequenceOpener(HTTPError("https://example.test", 429, "slow", headers, None),
                                Response({"items": []}))
        result = PublicJsonClient(opener=opener, sleep=waits.append, monotonic=lambda: 100,
                                  min_interval=0).get_json("https://example.test")
        self.assertEqual(result["payload"], {"items": []})
        self.assertIn(3.0, waits)
        self.assertEqual(opener.calls, 2)


if __name__ == "__main__":
    unittest.main()
