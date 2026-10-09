import json
import tempfile
import unittest

from delta_t1.ingestion.cafef_financial import (
    collect, coverage, parse_page, validate_config, verify,
)
from delta_t1.ingestion.sources.base import AccessControlError, SemanticValidationError


def config():
    return {"contract_version": "cafef-financial-raw-pilot-v1", "symbols": ["FPT"],
            "report_types": ["KQKD"], "time_modes": ["NAM"], "start_year": 2024,
            "end_year": 2025, "page_size": 4, "max_pages_per_stream": 2,
            "max_logical_requests": 4, "pit_status": "PIT_UNRESOLVED",
            "financial_features_allowed": False}


def row(year=2025, quarter=0):
    return {"symbol": "FPT", "year": year, "quater": quarter, "type": "HK",
            "content": "provider label", "time": str(year),
            "data": [{"code": "KQKD_15", "value": 0}, {"code": "KQKD_2", "value": None}]}


def payload(rows):
    return {"isSuccess": True, "errors": [], "value": {
        "templace": [], "count": 99, "data": [{"code": "KQKD", "data": rows}]}}


class Client:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.calls = 0

    def get_json(self, endpoint, params):
        self.calls += 1
        item = next(self.outcomes)
        if isinstance(item, Exception):
            raise item
        return {"body": json.dumps(item).encode(), "payload": item,
                "url": endpoint, "status": 200}


class FinancialPilotTests(unittest.TestCase):
    def test_annual_quarter_zero_and_null_zero_preserved(self):
        rows, status = parse_page(payload([row()]), "FPT", "KQKD", "NAM")
        self.assertEqual(status, "ROWS")
        self.assertEqual(rows[0]["data"][0]["value"], 0)
        self.assertIsNone(rows[0]["data"][1]["value"])
        with self.assertRaises(SemanticValidationError):
            parse_page(payload([row()]), "FPT", "KQKD", "QUY")

    def test_missing_group_is_not_empty_boundary(self):
        rows, status = parse_page(payload([row()]), "FPT", "LCTT", "NAM")
        self.assertEqual((rows, status), ([], "REPORT_TYPE_NOT_RETURNED"))
        self.assertEqual(parse_page(payload([]), "FPT", "KQKD", "NAM")[1], "EMPTY_PROVIDER_PAGE")

    def test_identity_order_duplicate_and_nonfinite_fail_closed(self):
        bad_symbol = row(); bad_symbol["symbol"] = "VNM"
        bad_number = row(); bad_number["data"][0]["value"] = float("nan")
        for rows in ([bad_symbol], [bad_number], [row(), row()], [row(2024), row(2025)]):
            with self.subTest(rows=rows), self.assertRaises(SemanticValidationError):
                parse_page(payload(rows), "FPT", "KQKD", "NAM")

    def test_config_prohibits_pit_promotion_and_oversized_pilot(self):
        for field, value in (("financial_features_allowed", True), ("page_size", 100),
                             ("max_pages_per_stream", 1000), ("symbols", ["../FPT"])):
            c = config(); c[field] = value
            with self.assertRaises(ValueError):
                validate_config(c)

    def test_coverage_reports_missing_period_and_keeps_timing_null(self):
        result = coverage(config(), "FPT", "KQKD", "NAM", [row()], "EMPTY_PROVIDER_PAGE")
        self.assertEqual(result["missing_periods"], ["2024"])
        self.assertEqual(result["null_fact_count"], 1)
        self.assertFalse(result["coverage_complete"])
        self.assertIsNone(result["available_at"])

    def test_collection_and_offline_replay_detect_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            run, result = collect(config(), directory, Client([payload([row(), row(2024)])]))
            self.assertEqual(result["coverage_status"], "PASS")
            self.assertEqual(verify(run), result)
            raw = next((run / "raw").rglob("page-001.json"))
            raw.write_bytes(b"{}")
            with self.assertRaises(ValueError):
                verify(run)

    def test_pagination_overlap_preserves_raw_and_marks_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            run, result = collect(config(), directory, Client([payload([row()]), payload([row()])]))
            self.assertEqual(result["execution_status"], "PARTIAL")
            self.assertEqual(result["streams"][0]["observed_periods"], 1)
            verify(run)
            self.assertEqual(len(list((run / "raw").rglob("*.metadata.json"))), 2)

    def test_access_boundary_stops_all_streams(self):
        c = config(); c["symbols"] = ["FPT", "VNM"]
        client = Client([AccessControlError("HTTP 403")])
        with tempfile.TemporaryDirectory() as directory:
            run, result = collect(c, directory, client)
            self.assertEqual(client.calls, 1)
            self.assertEqual(result["execution_status"], "HARD_STOP")
            self.assertEqual(result["streams"][1]["stop_reason"], "NOT_REQUESTED_HARD_STOP")
            verify(run)

    def test_caps_do_not_claim_complete_and_missing_group_is_reported(self):
        for c, outcomes, reason in (
            ({**config(), "max_pages_per_stream": 1}, [payload([row()])], "PAGE_CAP_REACHED"),
            ({**config(), "max_logical_requests": 1}, [payload([row()])], "REQUEST_CAP_REACHED"),
            (config(), [{"isSuccess": True, "errors": [], "value": {"data": [], "templace": []}}], "REPORT_TYPE_NOT_RETURNED"),
        ):
            with tempfile.TemporaryDirectory() as directory:
                run, result = collect(c, directory, Client(outcomes))
                self.assertEqual(result["streams"][0]["stop_reason"], reason)
                self.assertEqual(result["coverage_status"], "PARTIAL")
                verify(run)


if __name__ == "__main__":
    unittest.main()
