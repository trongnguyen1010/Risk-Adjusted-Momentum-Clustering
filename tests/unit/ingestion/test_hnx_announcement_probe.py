import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_probe import probe, HnxAnnouncementTransport

URL = "https://hnx.vn/vi-vn/m-niem-yet/tin-tuc/synthetic-1-0.html"


class Response(io.BytesIO):
    def __init__(self, body, status=200, headers=None):
        super().__init__(body)
        self.code = status
        self.headers = headers or {"Content-Type": "text/html"}


class Opener:
    def __init__(self, body, status=200, error=None):
        self.body, self.status, self.error, self.calls = body, status, error, 0
    def open(self, request, timeout):
        self.calls += 1
        if self.error:
            raise self.error
        return Response(self.body, self.status)


class HnxAnnouncementProbeTests(unittest.TestCase):
    def run_probe(self, output, body=b"<html><h1>SYNTHETIC</h1><p>Notice</p></html>", status=200, error=None):
        opener = Opener(body, status, error)
        def factory(root, **kwargs):
            return HnxAnnouncementTransport(root, opener=opener, sleep=lambda _: None, **kwargs)
        return probe(URL, output, transport_factory=factory), opener

    def test_one_response_archived_without_claiming_field_or_pit_verification(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "run"
            result, opener = self.run_probe(out)
            self.assertEqual(1, opener.calls)
            self.assertEqual("PARTIAL", result["status"])
            self.assertTrue(result["public_response_received"])
            self.assertEqual("NOT_RUN_BY_ACCESS_PROBE", result["article_parser_status"])
            self.assertEqual("NOT_EVALUATED", result["pit_status"])
            self.assertFalse(result["canonical_build"])
            m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            for name, expected in m["files"].items():
                self.assertEqual(expected, hashlib.sha256((out / name).read_bytes()).hexdigest())

    def test_untrusted_urls_rejected_before_acquisition(self):
        for url in ["http://hnx.vn/vi-vn/x/tin-tuc/a.html", "https://other.example/vi-vn/x/tin-tuc/a.html",
                    "https://user:password@hnx.vn/vi-vn/x/tin-tuc/a.html", "https://hnx.vn/login",
                    URL + "?token=secret", "https://hnx.vn:444/vi-vn/x/tin-tuc/a.html"]:
            with self.subTest(url=url), tempfile.TemporaryDirectory() as t:
                with self.assertRaisesRegex(ValueError, "URL_NOT_PUBLIC"):
                    probe(url, Path(t) / "run")

    def test_dry_run_has_no_output_and_no_network(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "run"
            result = probe(URL, out, dry_run=True, transport_factory=lambda *a, **k: self.fail("network"))
            self.assertEqual("DRY_RUN", result["status"])
            self.assertFalse(out.exists())

    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileExistsError):
                probe(URL, Path(t))

    def test_ssl_error_sealed_as_limitation_without_retry(self):
        with tempfile.TemporaryDirectory() as t:
            result, opener = self.run_probe(Path(t) / "run", error=URLError("CERTIFICATE_VERIFY_FAILED"))
            self.assertFalse(result["public_response_received"])
            self.assertIn("CERTIFICATE_VERIFY_FAILED", result["limitation"])
            self.assertEqual(1, opener.calls)

    def test_access_challenge_or_redirect_is_not_success_or_retried(self):
        for body, status in [(b"captcha", 200), (b"forbidden", 403), (b"limited", 429), (b"redirect", 302)]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as t:
                result, opener = self.run_probe(Path(t) / "run", body=body, status=status)
                self.assertFalse(result["public_response_received"])
                self.assertEqual(1, opener.calls)
                self.assertEqual("FAILED_OR_DEFERRED", result["status"])


if __name__ == "__main__":
    unittest.main()
