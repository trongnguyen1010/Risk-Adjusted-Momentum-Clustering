from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import Request

from delta_t1.ingestion.corporate_actions import vsdc_mbs_pilot_v2 as p
from delta_t1.ingestion.corporate_action_sources import PublicTransport
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old

ROOT = old.ROOT
CONFIG = p.read(ROOT / p.CONFIG)


class MbsPilotV2Tests(old.MbsPilotTests):
    """Keep V1 stop/layout/budget assertions; run them through the V2 transport."""
    def run_fake(self, tmp, source, clock, *, dry_run=False):
        prep = self.fixture(tmp)
        p.write(prep / "browser_request_headers.json", {"evidence_type": "TEST_ONLY"})

        def factory(root, **options):
            source.factory_options.append({**options, "opener": options["opener"].inner})
            # Keep the production header gate; replace only its network endpoint.
            options["opener"].inner = source
            return PublicTransport(root, **options, sleep=clock.sleep)

        source.factory = factory
        with patch.object(p, "load_preparation", return_value=(deepcopy(CONFIG), prep)), \
                patch("time.monotonic", clock.now):
            return p.run(ROOT, Path(tmp) / "state", transport_factory=factory,
                         clock=clock.now, emit=old.quiet, dry_run=dry_run)

    def test_scope_request_budget_and_no_resume_cannot_expand(self):
        p.validate(CONFIG)
        for key, value in [("ticker", "SSI"), ("max_requests", 3), ("max_seconds", 3600),
                ("workers", 2), ("retry", True), ("resume", True), ("interval_seconds", 2),
                ("detail_requests", 1), ("canonical_build", True), ("post_content_type", "application/json"),
                ("post_headers", {}), ("post_headers", {"Cookie": "test"}),
                ("post_headers", {"X-Requested-With": "wrong"}),
                ("post_headers", {**p.AJAX_HEADER, "Origin": "https://vsdc.vn"}),
                ("output_base", "somewhere"), ("v1_run_manifest_sha256", "0" * 64)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                p.validate(dict(CONFIG, **{key: value}))

    def test_only_post_receives_observed_header_and_construction_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = old.Clock(); source = old.Source(clock)
            result = self.run_fake(tmp, source, clock)
            self.assertTrue(result["page2_verified"])
            self.assertFalse(result["causal_fix_proven"])
            self.assertNotIn("x-requested-with", source.calls[0]["headers"])
            self.assertEqual("XMLHttpRequest", source.calls[1]["headers"]["x-requested-with"])
            self.assertEqual({**source.calls[0]["headers"],
                "content-type": "application/json;charset=utf-8",
                "x-requested-with": "XMLHttpRequest"}, source.calls[1]["headers"])
            construction = p.rows(Path(tmp) / "state/request_construction.jsonl")
            self.assertEqual(2, len(construction))
            for row, actual in zip(construction, source.calls):
                self.assertEqual(actual["headers"], {k.casefold(): v for k, v in row["headers"].items()})
                self.assertEqual(actual["url"], row["url"])
                self.assertIn("NOT_FULL_WIRE_CAPTURE", row["capture_stage"])
            archive = Path(tmp) / "v2.zip"
            p.seal(Path(tmp) / "state", archive, artifact_type=p.TYPE)
            with old.zipfile.ZipFile(archive) as z:
                self.assertEqual(p.TYPE, json.loads(z.read("manifest.json"))["artifact_type"])
                self.assertIn("request_construction.jsonl", z.namelist())
                self.assertIn("browser_request_headers.json", z.namelist())

    def test_page2_errors_keep_header_and_stop_without_retry(self):
        for reply in [old.Response("", 400), old.Response("denied", 401), old.Response("denied", 403),
                old.Response("slow", 429), old.Response("verify you are human"),
                old.Response("wait", extra={"Retry-After": "60"}),
                URLError(old.ssl.SSLCertVerificationError("TLS failed")), TimeoutError("timeout")]:
            with self.subTest(reply=repr(reply)), tempfile.TemporaryDirectory() as tmp:
                clock = old.Clock(); source = old.Source(clock, [old.PAGE1, reply])
                result = self.run_fake(tmp, source, clock)
                self.assertEqual(2, len(source.calls))
                self.assertEqual("XMLHttpRequest", source.calls[1]["headers"]["x-requested-with"])
                self.assertFalse(result["page2_verified"])
                self.assertFalse(result["resumable"])
                self.assertTrue(result["source_stopped"])


class FixedOpenerTests(unittest.TestCase):
    def test_invalid_headers_scope_sequence_or_payload_never_reach_network(self):
        class NoNetwork:
            def open(self, *args, **kwargs):
                raise AssertionError("invalid request reached network")

        cases = [
            (0, "https://example.com/", "GET", None, {}, 15),
            (0, p.search_url("MBS"), "POST", b"{}", {}, 15),
            (0, p.search_url("MBS"), "GET", None, {"Cookie": "test"}, 15),
            (0, p.search_url("MBS"), "GET", None, {"Authorization": "test"}, 15),
            (0, p.search_url("MBS"), "GET", None, {"User-Agent": "browser"}, 15),
            (0, p.search_url("MBS"), "GET", None, {}, 30),
            (1, p.search_url("MBS"), "POST", b'{"SearchKey":4,"CurrentPage":3}', {}, 15),
            (1, p.search_url("MBS"), "POST", b'{"SearchKey":4,"CurrentPage":2}',
                {"Content-Type": "text/html"}, 15),
            (1, p.search_url("MBS"), "POST", b'{"SearchKey":4,"CurrentPage":2}',
                {"X-Requested-With": "XMLHttpRequest"}, 15),
            (2, p.search_url("MBS"), "POST", b'{"SearchKey":4,"CurrentPage":2}', {}, 15),
        ]
        for count, url, method, body, extras, timeout in cases:
            with self.subTest(count=count, extras=extras), tempfile.TemporaryDirectory() as tmp:
                opener = p.AjaxPostOpener(NoNetwork(), Path(tmp)); opener.count = count
                headers = {"User-Agent": p.USER_AGENT, "Accept": "text/html",
                    "Content-Type": "text/html" if method == "GET" else "application/json;charset=utf-8",
                    **extras}
                request = Request(url, data=body, headers=headers, method=method)
                with self.assertRaises(ValueError):
                    opener.open(request, timeout=timeout)
                self.assertFalse((Path(tmp) / "request_construction.jsonl").exists())

    def test_cli_has_no_resume_and_blocks_second_real_run(self):
        spec = importlib.util.spec_from_file_location("v2_cli", ROOT / "scripts/corporate_actions/probe_vsdc_mbs_pagination_v2.py")
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            config_path = project / p.CONFIG; config_path.parent.mkdir(parents=True)
            p.write(config_path, CONFIG)
            (project / CONFIG["output_base"] / "run-existing").mkdir(parents=True)
            for args in [["pilot"], ["pilot", "--resume"], ["pilot", "--force"]]:
                with self.subTest(args=args), patch.object(cli, "ROOT", project), \
                        patch.object(cli, "run") as run, patch("sys.argv", args), \
                        patch("sys.stderr", old.io.StringIO()), self.assertRaises(SystemExit):
                    cli.main()
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
