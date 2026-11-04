from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("gsp_kpf_followup", ROOT / "scripts/collect_gsp_kpf_followup_v1.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
config = json.loads((ROOT / "configs/data/corporate_action_gsp_kpf_followup_v1.json").read_text(encoding="utf-8"))


class Reply(io.BytesIO):
    def __init__(self, body=b"%PDF-1.4\npublic", code=200):
        super().__init__(body)
        self.code = code
        self.headers = {"Content-Type": "application/pdf"}


class Opener:
    def __init__(self, body=b"%PDF-1.4\npublic", code=200):
        self.body, self.code, self.calls = body, code, 0

    def open(self, *args, **kwargs):
        self.calls += 1
        return Reply(self.body, self.code)


class GspKpfFollowupTests(unittest.TestCase):
    def test_only_exact_pdf_get_allowed_before_network(self):
        opener = Opener()
        transport = runner.KpfNoticeTransport(Path("unused"), config, opener=opener, sleep=lambda _: None)
        for url in [config["kpf_pdf"] + "?token=x", config["kpf_pdf"] + "#x", "https://hnx.vn/file.pdf", "http://static2.vietstock.vn/file.pdf"]:
            with self.assertRaises(runner.SourceLimitation):
                transport.fetch(url, binary=True)
        with self.assertRaises(runner.SourceLimitation):
            transport.fetch(config["kpf_pdf"], binary=False)
        with self.assertRaises(runner.SourceLimitation):
            transport.fetch(config["kpf_pdf"], payload=b"x", binary=True)
        self.assertEqual(0, opener.calls)

    def test_no_ssl_redirect_hnx_or_approval_relaxation(self):
        for key, value in [("tls_verification", False), ("follow_redirects", True), ("hnx_requests_allowed", True),
            ("canonical_build", True), ("automatic_field_approval", True), ("max_requests", 2), ("interval_seconds", .25)]:
            bad = deepcopy(config)
            bad[key] = value
            with self.assertRaises(ValueError):
                runner.KpfNoticeTransport(Path("unused"), bad)

    def test_access_denial_stops_host_without_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            opener = Opener(code=403)
            transport = runner.KpfNoticeTransport(Path(folder), config, opener=opener, sleep=lambda _: None)
            for _ in range(2):
                with self.assertRaises(runner.SourceLimitation):
                    transport.fetch(config["kpf_pdf"], binary=True)
            self.assertEqual(1, opener.calls)
            self.assertIn("static2.vietstock.vn", transport.stopped_hosts)

    def test_pdf_signature_required_and_single_request_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            opener = Opener()
            transport = runner.KpfNoticeTransport(Path(folder), config, opener=opener, sleep=lambda _: None)
            body, receipt = transport.fetch(config["kpf_pdf"], binary=True)
            self.assertTrue(body.startswith(b"%PDF-"))
            self.assertTrue((Path(folder) / receipt["path"]).is_file())
            with self.assertRaises(runner.SourceLimitation):
                transport.fetch(config["kpf_pdf"], binary=True)
            self.assertEqual(1, opener.calls)


if __name__ == "__main__":
    unittest.main()
