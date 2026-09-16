import json
import importlib.util
import sys
import unittest
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.sources.base import AccessControlError, PublicJsonClient
from delta_t1.ingestion.sources.cafef import (apply_invalid_row_policy,
                                               map_trade_history_row,
                                               price_band_row_status)
from delta_t1.ingestion.sources.vnstock import (classify_volume_semantics,
                                                 financial_raw_only_metadata,
                                                 map_kbs_wire_ohlcv_row,
                                                 map_vnstock_ohlcv_row)

SPEC = importlib.util.spec_from_file_location("source_smoke_runner", ROOT / "scripts/run_source_smoke.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


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

    def test_kbs_direct_http_provenance_is_truthful(self):
        row = map_kbs_wire_ohlcv_row({"t": "2026-09-15 07:00", "o": 72700,
            "h": 73400, "l": 72500, "c": 72700, "v": 3977500}, "FPT", "HOSE")
        self.assertEqual(row["provider"], "kbs")
        self.assertEqual(row["acquisition_client"], "delta_public_http")
        self.assertEqual(row["endpoint_discovered_via"], "vnstock")

    def test_vnm_corrupt_price_band_is_excluded_only_by_pinned_policy(self):
        row = map_trade_history_row(self.cafef_row(Symbol="VNM", TradeDate="/Date(1631120400000)/",
            BasicPrice=85.4, Ceiling=223.6, Floor=194.4, ClosePrice=85.2,
            AdjustPrice=64.634, Volume=2452400, TotalValue=209239000000,
            AgreedVolume=0, AgreedValue=0), "VNM", "HOSE")
        policy = {"provider": "cafef", "symbol": "VNM", "trade_date": "2021-09-09",
                  "classification": "PROVIDER_CORRUPT_ROW",
                  "row_status": "INVALID_REQUIRED_MARKET_ROW", "policy": "EXCLUDE_ROW",
                  "expected_raw_fields": {"BasicPrice": 85.4, "Ceiling": 223.6,
                      "Floor": 194.4, "ClosePrice": 85.2, "AdjustPrice": 64.634,
                      "Volume": 2452400, "TotalValue": 209239000000,
                      "AgreedVolume": 0, "AgreedValue": 0}}
        self.assertEqual(price_band_row_status(row), "INVALID_REQUIRED_MARKET_ROW")
        eligible, findings = apply_invalid_row_policy([row], policy)
        self.assertEqual([], eligible)
        self.assertEqual("PROVIDER_CORRUPT_ROW", findings[0]["classification"])
        self.assertEqual("EXCLUDE_ROW", findings[0]["policy"])
        self.assertTrue(findings[0]["safe"])
        bad_policy = dict(policy, expected_raw_fields={"BasicPrice": 1})
        _, findings = apply_invalid_row_policy([row], bad_policy)
        self.assertEqual("FAIL_SYMBOL_WINDOW", findings[0]["policy"])
        self.assertFalse(findings[0]["safe"])
        wrong_provider = dict(policy, provider="kbs")
        _, findings = apply_invalid_row_policy([row], wrong_provider)
        self.assertEqual("FAIL_SYMBOL_WINDOW", findings[0]["policy"])
        self.assertFalse(findings[0]["safe"])

    def test_acv_volume_remains_unresolved_and_source_qualified(self):
        kbs = [{"trade_date": f"2026-09-{day:02d}", "volume": value}
               for day, value in ((15, 231600), (14, 413700), (11, 462000), (10, 193500), (9, 713500))]
        cafef = [{"trade_date": f"2026-09-{day:02d}", "matched_volume": matched,
                  "put_through_volume": put_through}
                 for day, matched, put_through in ((15, 229900, 0), (14, 413400, 110000),
                     (11, 460800, 0), (10, 193300, 46300), (9, 705700, 0))]
        finding = classify_volume_semantics(kbs, cafef)
        self.assertEqual("UNRESOLVED", finding["classification"])
        self.assertEqual(5, finding["dates_checked"])
        self.assertEqual("KEEP_SOURCE_QUALIFIED", finding["storage_policy"])
        self.assertFalse(finding["equality_assumption"])
        self.assertFalse(finding["canonical_merge_allowed"])
        self.assertTrue(finding["market_collection_safe"])

    def test_volume_semantics_require_exact_or_documented_evidence(self):
        kbs = [{"trade_date": "2026-09-15", "volume": 100}]
        matched = [{"trade_date": "2026-09-15", "matched_volume": 100,
                    "put_through_volume": 25}]
        total = [{"trade_date": "2026-09-15", "matched_volume": 75,
                  "put_through_volume": 25}]
        approximate = [{"trade_date": "2026-09-15", "matched_volume": 99,
                        "put_through_volume": 0}]
        self.assertEqual("MATCHED_VOLUME", classify_volume_semantics(kbs, matched)["classification"])
        self.assertEqual("TOTAL_VOLUME", classify_volume_semantics(kbs, total)["classification"])
        self.assertEqual("UNRESOLVED", classify_volume_semantics(kbs, approximate)["classification"])
        self.assertEqual("OTHER_DOCUMENTED_SEMANTIC",
                         classify_volume_semantics(kbs, approximate,
                             documented_mapping="provider-documented auction inclusion")["classification"])

    def test_cafef_window_records_actual_contributing_page_hash(self):
        class Source:
            def acquire_trade_history_page(self, _request):
                payload = {"Success": True, "Data": [self_row]}
                return {"payload": payload, "body": json.dumps(payload).encode(),
                        "url": "https://example.test", "status": 200}
        class Store:
            def save(self, *_args, **_kwargs):
                return {"raw_path": "data/raw/cafef/run/FPT-page-001.json", "sha256": "a" * 64}
        self_row = self.cafef_row()
        evidence = RUNNER.locate_cafef_window(Source(), Store(), "FPT", "HOSE",
            {"start": "2021-09-01", "end": "2021-09-20"}, "WINDOW_OLD", 1, {})
        self.assertEqual([1], [item["page"] for item in evidence["contributing_pages"]])
        self.assertEqual("a" * 64, evidence["contributing_pages"][0]["sha256"])

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
