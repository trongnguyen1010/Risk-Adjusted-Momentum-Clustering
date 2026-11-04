import json
import io
from pathlib import Path
import ssl
import tempfile
import unittest
import zipfile
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions import kbs_raw_probe as k

ROOT = Path(__file__).resolve().parents[4]
CONFIG = json.loads((ROOT / "configs/data/corporate_actions/kbs_raw_dxg_probe_v1.json").read_text(encoding="utf-8"))


def quiet(*args, **kwargs): pass


def response(body=b"[]", status=200, truncated=False):
    return {"body": body, "http_status": status, "truncated": truncated, "headers": {"content-type": "application/json"}}


class KbsRawProbeTests(unittest.TestCase):
    def run_probe(self, folder, fetch, sleep=quiet):
        return k.probe(folder, CONFIG, {"baseline_sdk_rows": 0}, fetch=fetch, sleep=sleep, emit=quiet)

    def test_exact_scope_and_safety_limits(self):
        k.validate_config(CONFIG)
        for key, value in [("ticker", "FPT"), ("endpoint", "https://example.com"), ("max_pages", 3),
            ("max_requests", 100), ("page_size", 100), ("interval_seconds", .1), ("timeout_seconds", 60),
            ("max_response_bytes", 100000000), ("event_type_filter", 3), ("tls_verification", False),
            ("retries", True), ("follow_redirects", True), ("provider_fallback", True), ("canonical_build", True)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                k.validate_config(dict(CONFIG, **{key: value}))

    def test_empty_first_page_stops_and_never_means_no_history(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            calls = []
            def fetch(url, cfg): calls.append(url); return response()
            result = self.run_probe(Path(tmp), fetch)
            self.assertEqual(1, len(calls))
            self.assertEqual([0], result["raw_rows_by_page"])
            self.assertFalse(result["empty_response_proves_no_historical_events"])
            self.assertEqual("UNVERIFIED", result["installed_native_sdk_endpoint_equivalence"])

    def test_two_pages_use_documented_params_no_type_filter_and_eight_second_gap(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            calls, waits = [], []
            def fetch(url, cfg):
                calls.append(parse_qs(urlsplit(url).query))
                return response(json.dumps([{"ID": str(i)} for i in range(10)] if len(calls) == 1 else [{"ID": "next"}]).encode())
            result = self.run_probe(Path(tmp), fetch, sleep=waits.append)
            self.assertEqual([{"l": ["1"], "p": ["1"], "s": ["10"]}, {"l": ["1"], "p": ["2"], "s": ["10"]}], calls)
            self.assertEqual([8], waits)
            self.assertEqual([10, 1], result["raw_rows_by_page"])
            self.assertFalse(result["rows_are_deduplicated_events"])

    def test_access_redirect_rate_limit_and_errors_preserve_body_and_never_retry(self):
        for status in (301, 302, 401, 403, 406, 407, 429, 500):
            with self.subTest(status=status), tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
                calls = []
                def fetch(url, cfg): calls.append(url); return response(b'denied bytes', status)
                result = self.run_probe(Path(tmp), fetch)
                self.assertEqual(1, len(calls))
                self.assertTrue(result["status"].startswith("STOPPED_"))
                self.assertEqual(b'denied bytes', (Path(tmp) / "raw/page-1.bin").read_bytes())

    def test_challenge_non_json_and_error_envelopes_stop(self):
        for body in (b'<html>captcha</html>', b'<html>login</html>', b'{"error":"no access"}', b'null', b'[1]', b'{broken'):
            with self.subTest(body=body):
                self.assertTrue(k.inspect_response(response(body))["status"].startswith("STOPPED_"))

    def test_limit_marks_truncation_without_parsing_or_next_page(self):
        assessment = k.inspect_response(response(b'[]', truncated=True))
        self.assertEqual("STOPPED_RESPONSE_LIMIT", assessment["status"])

    def test_transport_ssl_and_timeout_stop_without_another_call(self):
        for error in (URLError(ssl.SSLError('verify failed')), TimeoutError('timeout')):
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
                calls = []
                def fetch(url, cfg): calls.append(url); raise error
                result = self.run_probe(Path(tmp), fetch)
                self.assertEqual("STOPPED_TLS_OR_TRANSPORT", result["status"])
                self.assertEqual(1, len(calls))
                self.assertFalse(result["receipts"][0]["response_received"])

    def test_raw_bytes_and_hash_keep_number_literals_and_nulls_unchanged(self):
        body = b'[{"ratio":0.333333333333333333,"id":"0001","date":null}]'
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            result = self.run_probe(Path(tmp), lambda url, cfg: response(body))
            self.assertEqual(body, (Path(tmp) / "raw/page-1.bin").read_bytes())
            self.assertEqual(k.digest(body), result["receipts"][0]["raw_sha256"])
            self.assertFalse(result["canonical_build"])
            self.assertFalse(result["field_approval"])

    def test_repeated_second_page_is_review_not_unique_coverage(self):
        body = json.dumps([{"ID": i} for i in range(10)]).encode()
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            result = self.run_probe(Path(tmp), lambda url, cfg: response(body))
            self.assertEqual(2, result["requests_attempted"])
            self.assertEqual("PAGINATION_REPEATED_BODY_REVIEW_REQUIRED", result["status"])

    def test_input_baseline_and_public_endpoint_evidence_are_hash_verified(self):
        result = k.verify_inputs(ROOT, CONFIG)
        self.assertEqual(0, result["baseline_sdk_rows"])
        self.assertEqual(16, result["baseline_manifest_files_verified"])
        with self.assertRaisesRegex(ValueError, "BASELINE_ZIP_HASH_MISMATCH"):
            k.verify_inputs(ROOT, dict(CONFIG, baseline_zip_sha256="0" * 64))

    def test_transport_does_not_install_redirect_cookie_or_auth_handlers(self):
        from email.message import Message
        class Reply:
            code = 403
            headers = Message()
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'denied'
        with patch.object(k, 'build_opener') as build:
            build.return_value.open.return_value = Reply()
            received = k.get_public(k.ENDPOINT + '?l=1&p=1&s=10', CONFIG)
            self.assertEqual(403, received['http_status'])
            request = build.return_value.open.call_args.args[0]
            self.assertNotIn('Authorization', request.headers)
            self.assertNotIn('Cookie', request.headers)
            self.assertEqual(2, len(build.call_args.args))
            self.assertIsInstance(build.call_args.args[0], k.NoRedirect)

    def test_real_http_error_branch_retains_denied_body_without_retry(self):
        from email.message import Message
        error = HTTPError(k.ENDPOINT, 403, 'Forbidden', Message(), io.BytesIO(b'public denial'))
        with patch.object(k, 'build_opener') as build:
            build.return_value.open.side_effect = error
            received = k.get_public(k.ENDPOINT, CONFIG)
            self.assertEqual(1, build.return_value.open.call_count)
            self.assertEqual(403, received['http_status'])
            self.assertEqual(b'public denial', received['body'])
            self.assertEqual('STOPPED_ACCESS_OR_RATE_LIMIT', k.inspect_response(received)['status'])

    def test_transport_records_partial_capture_when_limit_exceeded(self):
        from email.message import Message
        class Reply:
            code = 200
            headers = Message()
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'x' * limit
        with patch.object(k, 'build_opener') as build:
            build.return_value.open.return_value = Reply()
            received = k.get_public(k.ENDPOINT, CONFIG)
            self.assertTrue(received['truncated'])
            self.assertEqual(CONFIG['max_response_bytes'], len(received['body']))
            self.assertEqual('STOPPED_RESPONSE_LIMIT', k.inspect_response(received)['status'])

    def test_raw_zip_is_classified_as_public_http_not_sdk_export_and_hashes_match(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as tmp:
            base = Path(tmp); output = base / 'state'; output.mkdir()
            self.run_probe(output, lambda url, cfg: response())
            k.seal_raw(output, base / 'raw.zip', {'status': 'RAW_DIAGNOSTIC_READY_FOR_REVIEW'})
            with zipfile.ZipFile(base / 'raw.zip') as z:
                manifest = json.loads(z.read('manifest.json'))
                self.assertEqual('kbs-public-raw-diagnostic-v1', manifest['artifact_type'])
                self.assertEqual('PUBLIC_HTTP_BYTES_NOT_CANONICAL_EVENTS', manifest['classification'])
                for name, expected in manifest['files'].items(): self.assertEqual(expected, k.digest(z.read(name)))
                self.assertEqual(b'[]', z.read('raw/page-1.bin'))


if __name__ == "__main__": unittest.main()
