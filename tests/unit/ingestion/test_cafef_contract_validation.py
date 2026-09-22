import json
import unittest

from delta_t1.ingestion.cafef_contract_validation import (
    CONTRACT_VERSION, field_contract, parse_price_history_date, validation_plan,
)
from delta_t1.ingestion.sources.cafef import CafeFSource, PRICE_HISTORY_ENDPOINT


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_json(self, endpoint, params=None):
        self.calls.append((endpoint, params))
        body = json.dumps(self.payload).encode()
        return {"url": endpoint, "status": 200, "headers": {}, "body": body, "payload": self.payload}


class CafeFContractValidationTests(unittest.TestCase):
    def test_plan_is_bounded_and_representative(self):
        plan = validation_plan()
        self.assertEqual(11, len(plan))
        self.assertEqual({"HOSE", "HNX", "UPCOM"}, {row["exchange"] for row in plan})
        self.assertTrue(any("CA" in row["id"] for row in plan))
        self.assertTrue(any("ZERO" in row["id"] for row in plan))
        self.assertTrue(any("NO-ROW" in row["id"] for row in plan))
        self.assertTrue(any(row.get("page_index") == 2 for row in plan))

    def test_contract_keeps_price_basis_and_promotion_closed(self):
        contract = field_contract()
        self.assertEqual(CONTRACT_VERSION, contract["contract_version"])
        adjusted = next(row for row in contract["fields"] if row["concept"] == "adjusted_price")
        self.assertEqual("DIAGNOSTIC_ONLY", adjusted["status"])
        self.assertEqual("LOW", adjusted["confidence"])
        self.assertIn("same provider row/session date", adjusted["time_date_semantics"])
        self.assertTrue(contract["acceptance_contract"]["promotable"].startswith("NO."))
        self.assertIn("20 valid observations before + 20 after", contract["acceptance_contract"]["overlap_policy"])

    def test_price_history_date_and_envelope(self):
        self.assertEqual("2026-09-15", parse_price_history_date("15/09/2026"))
        payload = {"Success": True, "Data": {"TotalCount": 0, "Data": []}}
        client = FakeClient(payload)
        response = CafeFSource(client).acquire_price_history_page({
            "symbol": "FPT", "exchange": "HOSE", "start_date": "09/14/2026",
            "end_date": "09/15/2026", "page_index": 1, "page_size": 20,
        })
        self.assertEqual(payload, response["payload"])
        self.assertEqual(PRICE_HISTORY_ENDPOINT, client.calls[0][0])
        self.assertEqual("HOSE", client.calls[0][1]["ExchangeType"])


if __name__ == "__main__":
    unittest.main()
