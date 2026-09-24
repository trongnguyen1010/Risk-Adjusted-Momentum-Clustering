import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location("local_reuse", ROOT / "scripts/audit_cafef_tradehistory_local_reuse.py")
REUSE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REUSE)


class CafeFTradeHistoryLocalReuseTests(unittest.TestCase):
    def test_tradehistory_endpoint_and_checksum_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); raw = root / "cafef-ACB-page-001.json"; raw.write_text('{"Data": []}', encoding="utf-8")
            meta = raw.with_name("cafef-ACB-page-001.metadata.json")
            meta.write_text(json.dumps({"sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "url": "https://cafef.vn/TradeHistoryNew.ashx", "request": {"symbol": "ACB", "page_index": 1, "page_size": 30}}), encoding="utf-8")
            result, _ = REUSE.validate_page(raw, meta, {"ACB"})
            self.assertEqual("VALID_RAW_PAGE", result["classification"])
            self.assertTrue(REUSE.endpoint_is_tradehistory(json.loads(meta.read_text())))

    def test_duplicate_signature_and_conflicting_signature(self):
        first = {"ClosePrice": 10, "AdjustPrice": 9, "Volume": 1, "TotalValue": 2, "AgreedVolume": 0, "AgreedValue": 0, "BasicPrice": 9, "Ceiling": 11, "Floor": 8}
        second = dict(first)
        self.assertEqual(REUSE.signature(first), REUSE.signature(second))
        second["ClosePrice"] = 11
        self.assertNotEqual(REUSE.signature(first), REUSE.signature(second))

    def test_snapshot_date_and_endpoint_date_classification(self):
        from delta_t1.ingestion.sources.cafef import cafef_trade_date, classify_cafef_page_row
        self.assertEqual("2026-01-29", cafef_trade_date("/Date(1769626800000)/"))
        self.assertEqual("CURRENT_SNAPSHOT", classify_cafef_page_row("1/1/0001 12:00:00 AM", 1, 0))
        self.assertEqual("HISTORICAL", classify_cafef_page_row("1/1/0001 12:00:00 AM", 2, 0))
        self.assertEqual("TRADEHISTORY_ONLY", REUSE.endpoint_date_classification(False, True))
        self.assertEqual("PRICEHISTORY_ONLY", REUSE.endpoint_date_classification(True, False))

    def test_historical_exchange_routing_for_transfers(self):
        plans = {
            "BCM": {"intervals": [{"effective_from":"2018-07-10","effective_to":"2020-08-30","exchange":"UPCOM"},{"effective_from":"2020-08-31","effective_to":None,"exchange":"HOSE"}]},
            "CTR": {"intervals": [{"effective_from":"2018-12-06","effective_to":"2022-02-22","exchange":"UPCOM"},{"effective_from":"2022-02-23","effective_to":None,"exchange":"HOSE"}]},
            "SHB": {"intervals": [{"effective_from":"2009-04-20","effective_to":"2021-10-10","exchange":"HNX"},{"effective_from":"2021-10-11","effective_to":None,"exchange":"HOSE"}]},
        }
        self.assertEqual("HOSE", REUSE.route(plans, "BCM", "2026-01-29"))
        self.assertEqual("HOSE", REUSE.route(plans, "CTR", "2026-01-29"))
        self.assertEqual("HOSE", REUSE.route(plans, "SHB", "2026-01-29"))


if __name__ == "__main__":
    unittest.main()
