import json
import tempfile
import unittest
from pathlib import Path

from delta_t1.ingestion.cafef_financial_detail import (
    PublicEvidenceClient, collect, number_candidate, parse_detail, validate_config, verify,
)
from delta_t1.ingestion.sources.base import AccessControlError, RateLimitError, SemanticValidationError
from urllib.error import HTTPError
from email.message import Message


def html(quarter=0, symbol="FPT", last_year=2025, value="1.234"):
    labels = [str(y) for y in range(last_year - 3, last_year + 1)] if not quarter else [f"Quý {q}- {last_year}" for q in range(1, 5)]
    headers = "".join(f'<td class="h_t">{label}</td>' for label in labels)
    return (f'<input id="ContentPlaceHolder1_txtKeyword" value="{symbol}">'
            '<div class="dltlonote">Đơn vị: tỷ đồng</div>'
            f'<table id="tblGridData"><tr>{headers}</tr></table>'
            '<table id="tableContent"><tr id="20" class="r_item">'
            '<td>Lưu chuyển tiền thuần từ hoạt động kinh doanh</td>'
            f'<td>{value}</td><td>0</td><td></td><td>{value}</td>'
            '<td><table><tr><td>999</td></tr></table></td></tr></table>').encode()


def config():
    return {"contract_version": "cafef-financial-detail-v1", "symbols": ["FPT"],
            "statement_types": ["cashflow"], "start_year": 2025, "end_year": 2025,
            "max_requests": 5, "min_interval_seconds": 2, "financial_features_allowed": False,
            "pit_status": "PIT_UNRESOLVED"}


class Client:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = 0

    def get(self, url):
        self.calls += 1
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return value, 200


class DetailTests(unittest.TestCase):
    def test_explicit_supplement_host_and_response_cap(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, n): return b"%PDF-valid"[:n]
        class Opener:
            def open(self, request, timeout): return Response()
        client = PublicEvidenceClient(opener=Opener(), sleep=lambda _: None, approved_hosts={"www.ptsc.com.vn"}, max_bytes=5)
        with self.assertRaises(SemanticValidationError):
            client.get("https://www.ptsc.com.vn/document.pdf")
        client.max_bytes = 20
        self.assertEqual(client.get("https://www.ptsc.com.vn/document.pdf"), (b"%PDF-valid", 200))
        with self.assertRaises(ValueError):
            client.get("https://cafef.vn/document.pdf")
        with self.assertRaises(ValueError):
            PublicEvidenceClient(max_bytes=50_000_001)

    def test_transport_access_rate_redirect_stop_without_retry(self):
        class Opener:
            calls = 0
            def open(self, request, timeout):
                self.calls += 1
                raise HTTPError(request.full_url, code, "boundary", Message(), None)
        for code, error in ((401, AccessControlError), (403, AccessControlError),
                            (429, RateLimitError), (301, ValueError)):
            opener = Opener()
            client = PublicEvidenceClient(opener=opener, sleep=lambda _: None)
            with self.assertRaises(error):
                client.get("https://cafef.vn/du-lieu/test")
            self.assertEqual(opener.calls, 1)

    def test_transport_rejects_unobserved_hosts_and_credentials(self):
        client = PublicEvidenceClient(sleep=lambda _: None)
        for url in ("https://example.test/data", "http://cafef.vn/data", "https://user:password@cafef.vn/data"):
            with self.assertRaises(ValueError):
                client.get(url)

    def test_nested_chart_excluded_and_raw_unit_not_assumed(self):
        p = parse_detail(html(), "FPT", "cashflow", 2025, 0)
        self.assertEqual(len(p["facts"]), 4)
        self.assertEqual(p["facts"][0]["display_number_candidate"], 1234)
        self.assertEqual(p["facts"][1]["display_number_candidate"], 0)
        self.assertIsNone(p["facts"][2]["display_number_candidate"])
        self.assertIsNone(p["facts"][0]["unit_scale"])
        self.assertEqual(p["facts"][0]["period_semantics"], "DURATION_UNVERIFIED")

    def test_symbol_and_anchor_must_match(self):
        for body, year in ((html(symbol="VNM"), 2025), (html(last_year=2024), 2025)):
            with self.assertRaises(SemanticValidationError):
                parse_detail(body, "FPT", "cashflow", year, 0)

    def test_malformed_header_and_row_width_rejected(self):
        for body in (html().replace(b'2022', b'Q2 2022'), html().replace(b'<td>0</td>', b'')):
            with self.assertRaises(SemanticValidationError):
                parse_detail(body, "FPT", "cashflow", 2025, 0)

    def test_numbers_do_not_use_magnitude_or_fill(self):
        self.assertEqual(number_candidate("-1.234,56"), "-1234.56")
        self.assertIsNone(number_candidate("--"))
        for v in ("1,234.56", "NaN", "abc", "1.23"):
            with self.assertRaises(SemanticValidationError):
                number_candidate(v)

    def test_config_cannot_promote_or_scale(self):
        for key, value in (("financial_features_allowed", True), ("max_requests", 1000), ("min_interval_seconds", 0)):
            c = config(); c[key] = value
            with self.assertRaises(ValueError):
                validate_config(c)

    def test_live_shape_collection_replay_and_tamper(self):
        client = Client([html(), html(quarter=4), b'[]'])
        with tempfile.TemporaryDirectory() as root:
            run, result = collect(config(), root, client)
            self.assertEqual(client.calls, 3)
            self.assertEqual(result["execution_status"], "COMPLETE")
            self.assertEqual(result["coverage_status"], "PARTIAL")  # Q3 blank is not an observation.
            self.assertEqual(verify(run), result)
            next((run / "raw").rglob("*.html")).write_bytes(b"modified")
            with self.assertRaises(ValueError):
                verify(run)

    def test_access_boundary_stops_documents_and_next_job(self):
        client = Client([AccessControlError("403")])
        with tempfile.TemporaryDirectory() as root:
            run, result = collect(config(), root, client)
            self.assertEqual(client.calls, 1)
            self.assertEqual(result["execution_status"], "HARD_STOP")
            verify(run)

    def test_invalid_parse_is_preserved_and_not_accepted(self):
        client = Client([html(symbol="VNM"), html(quarter=4), b'[]'])
        with tempfile.TemporaryDirectory() as root:
            run, result = collect(config(), root, client)
            self.assertEqual(result["execution_status"], "PARTIAL")
            self.assertEqual(len(list((run / "raw").rglob("*.html"))), 2)
            verify(run)


if __name__ == "__main__":
    unittest.main()
