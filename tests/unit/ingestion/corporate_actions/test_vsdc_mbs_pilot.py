from copy import deepcopy
import io
import json
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_mbs_pilot as p
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import read, write
from delta_t1.ingestion.corporate_action_sources import PublicTransport, sha

ROOT = Path(__file__).resolve().parents[4]
CONFIG = read(ROOT / p.CONFIG)
PAGE1_BYTES = (ROOT / "tests/fixtures/corporate_actions/vsdc_mbs_pagination_v1/archived_page1.html").read_bytes()
PAGE1 = PAGE1_BYTES.decode("utf-8-sig")


def fragment(first=21, last=40, total=63, ids=None):
    ids = ids or list(range(100001, 100001 + last - first + 1))
    return ''.join(f'<h3><a href="/vi/ad/{aid}">MBS : Thông báo cổ đông {aid}</a></h3>' for aid in ids) + f'Hiển thị: {first} - {last} / {total} bản ghi'


class Clock:
    def __init__(self): self.value = 1000.
    def now(self): return self.value
    def sleep(self, value): self.value += value


class Response(io.BytesIO):
    def __init__(self, html, status=200, extra=None):
        super().__init__(html.encode())
        self.code = status
        self.headers = {"Content-Type": "text/html; charset=utf-8", **(extra or {})}


class Source:
    def __init__(self, clock, replies=None):
        self.clock, self.calls, self.factory_options = clock, [], []
        self.replies = list(replies or [PAGE1, fragment()])
    def factory(self, root, **options):
        self.factory_options.append(options)
        return PublicTransport(root, **{**options, "opener": self, "sleep": self.clock.sleep})
    def open(self, request, timeout=None):
        self.calls.append({"url": request.full_url, "payload": request.data,
            "content_type": request.get_header("Content-type"), "timeout": timeout, "start": self.clock.now(),
            "headers": {k.casefold(): v for k,v in request.header_items()}})
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException): raise reply
        return reply if isinstance(reply, Response) else Response(reply)


def quiet(*args, **kwargs): pass


class MbsPilotTests(unittest.TestCase):
    def fixture(self, tmp):
        prep = Path(tmp) / "prep";prep.mkdir()
        write(prep / "source_contract.json", p.source_contract(PAGE1))
        write(prep / "protected_old_files.json", {})
        write(prep / "cached_article_ids.json", ["100001"])
        write(prep / "manifest.json", {"files": {}})
        return prep

    def run_fake(self, tmp, source, clock, *, dry_run=False):
        prep = self.fixture(tmp)
        with patch.object(p, "load_preparation", return_value=(deepcopy(CONFIG), prep)), patch("time.monotonic", clock.now):
            return p.run(ROOT, Path(tmp) / "state", transport_factory=source.factory, clock=clock.now, emit=quiet, dry_run=dry_run)

    def test_scope_request_budget_and_no_resume_cannot_expand(self):
        p.validate(CONFIG)
        for key, value in [("ticker", "SSI"), ("max_requests", 3), ("max_seconds", 3600),
                ("workers", 2), ("retry", True), ("resume", True), ("interval_seconds", 2),
                ("detail_requests", 1), ("canonical_build", True), ("post_content_type", "application/json")]:
            with self.subTest(key=key), self.assertRaises(ValueError): p.validate(dict(CONFIG, **{key: value}))

    def test_archived_source_contract_and_page1_are_reproducible(self):
        self.assertEqual(CONFIG["archived_page1_sha256"], sha(PAGE1_BYTES))
        self.assertTrue(p.source_contract(PAGE1)["script_sha256"])
        first = p.page(PAGE1, 1)
        self.assertEqual((1, 20, 63), tuple(first["coverage"][k] for k in ("first", "last", "reported_total")))

    def test_dry_run_creates_no_output_and_makes_no_source_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = Clock();source = Source(clock)
            result = self.run_fake(tmp, source, clock, dry_run=True)
            self.assertEqual("OFFLINE_CHECK_PASS", result["status"])
            self.assertEqual([], source.calls);self.assertFalse((Path(tmp) / "state").exists())

    def test_exact_two_requests_shared_delay_layout_and_sealed_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = Clock();source = Source(clock)
            result = self.run_fake(tmp, source, clock)
            self.assertEqual("PASS_PAGE2_ACCESS_AND_LAYOUT_REVIEW_REQUIRED", result["status"])
            self.assertEqual(2, result["network_requests"])
            self.assertEqual(40, result["pair_distinct_article_ids"])
            self.assertEqual(23, result["remaining_query_rows_after_pair"])
            self.assertEqual(1, result["cached_page2_provider_ids"])
            self.assertTrue(all(r["url"] == CONFIG["url"] for r in source.calls))
            self.assertIsNone(source.calls[0]["payload"])
            self.assertEqual(b'{"SearchKey":4,"CurrentPage":2}', source.calls[1]["payload"])
            self.assertEqual("application/json;charset=utf-8", source.calls[1]["content_type"])
            self.assertGreaterEqual(source.calls[1]["start"] - source.calls[0]["start"], 8)
            self.assertTrue(any(isinstance(h,p.NoRedirect) for h in source.factory_options[0]['opener'].handlers))
            for call in source.calls:
                self.assertNotIn('cookie',call['headers']);self.assertNotIn('authorization',call['headers'])
                self.assertEqual('DeltaT1Research/0.2 (bounded corporate-action research)',call['headers']['user-agent'])
            self.assertFalse(result["resumable"]);self.assertFalse(result["bulk_collection_ready"])
            self.assertEqual(0, result["detail_requests"]);self.assertEqual(0, result["normalized_observations"])
            out = Path(tmp) / "state"
            self.assertEqual(2, len(p.rows(out / "request_log.jsonl")))
            archive = Path(tmp) / "pilot.zip";p.seal(out, archive, artifact_type=p.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                for name,digest in json.loads(z.read("manifest.json"))["files"].items():
                    self.assertEqual(digest, sha(z.read(name)))

    def test_http400_page2_stops_preserves_empty_raw_and_nonresumable_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock=Clock();source=Source(clock,[PAGE1,Response('',400)])
            result=self.run_fake(tmp,source,clock)
            self.assertEqual("STOPPED_SOURCE_OR_LAYOUT_REVIEW_REQUIRED",result["status"])
            self.assertEqual([200,400],result["http_statuses"])
            self.assertEqual(2,len(source.calls));self.assertFalse(result["resumable"])
            self.assertEqual(b'',(Path(tmp)/'state/raw/response-0002.bin').read_bytes())
            p.seal(Path(tmp)/'state',Path(tmp)/'partial.zip',artifact_type=p.TYPE)

    def test_access_tls_timeout_challenge_and_retry_after_stop_before_post(self):
        for reply in [Response('denied',401),Response('denied',403),Response('slow',429),
                Response('verify you are human'),Response('ok',extra={'Retry-After':'60'}),
                URLError(ssl.SSLCertVerificationError('certificate failed')),TimeoutError('timeout')]:
            with self.subTest(reply=repr(reply)),tempfile.TemporaryDirectory() as tmp:
                clock=Clock();source=Source(clock,[reply])
                result=self.run_fake(tmp,source,clock)
                self.assertEqual(1,result['network_requests']);self.assertEqual(1,len(source.calls))
                self.assertFalse(result['page2_verified']);self.assertFalse(result['resumable'])

    def test_wrong_echo_or_changed_first_party_contract_never_posts(self):
        for html in [PAGE1.replace('MBS</p>','SSI</p>',1), PAGE1.replace('SearchKey: type','SearchKey: changed')]:
            with self.subTest(),tempfile.TemporaryDirectory() as tmp:
                clock=Clock();source=Source(clock,[html])
                result=self.run_fake(tmp,source,clock)
                self.assertEqual(1,len(source.calls));self.assertFalse(result['page2_verified'])

    def test_repeated_page_changed_total_and_wrong_range_never_pass(self):
        for html in [PAGE1,fragment(total=64),fragment(first=41,last=60)]:
            with self.subTest(),tempfile.TemporaryDirectory() as tmp:
                clock=Clock();source=Source(clock,[PAGE1,html]);result=self.run_fake(tmp,source,clock)
                self.assertEqual(2,len(source.calls));self.assertFalse(result['page2_verified'])

    def test_overlap_and_duplicate_ids_fail_page_validation(self):
        first=p.page(PAGE1,1)
        for ids in [[first['article_ids'][0],*range(100002,100021)], [100001]*20]:
            with self.subTest(ids=ids),self.assertRaises(ValueError):
                p.page(fragment(ids=ids),2,63,first['article_ids'])

    def test_no_second_page_returns_partial_without_expansion(self):
        script=p.source_contract(PAGE1)['script']
        html='<p>Kết quả tìm kiếm với từ: MBS</p><div id="divGlSearchArticles">'+fragment(first=1,last=3,total=3)+'</div><script>'+script+'</script>'
        with tempfile.TemporaryDirectory() as tmp:
            clock=Clock();source=Source(clock,[html]);result=self.run_fake(tmp,source,clock)
            self.assertEqual('PARTIAL_FRESH_QUERY_HAS_NO_SECOND_PAGE',result['status'])
            self.assertEqual(1,len(source.calls));self.assertFalse(result['page2_verified'])

    def test_elapsed_run_budget_prevents_second_network_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock=Clock();source=Source(clock);original=source.open
            def delayed(request,timeout=None):
                response=original(request,timeout);clock.value+=90;return response
            source.open=delayed
            result=self.run_fake(tmp,source,clock)
            self.assertEqual(1,len(source.calls));self.assertIn('RUN_TIME_BUDGET',result['stop_reason'])

    def test_tls_verification_cannot_be_disabled(self):
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);context.check_hostname=False;context.verify_mode=ssl.CERT_NONE
        with tempfile.TemporaryDirectory() as tmp,patch.object(p.ssl,'create_default_context',return_value=context):
            clock=Clock();source=Source(clock);result=self.run_fake(tmp,source,clock)
            self.assertEqual(0,len(source.calls));self.assertIn('STRICT_TLS_REQUIRED',result['stop_reason'])


if __name__=='__main__':unittest.main()
