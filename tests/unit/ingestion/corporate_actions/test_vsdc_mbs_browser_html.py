from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch, MagicMock
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_mbs_browser_html as p
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old

ROOT = old.ROOT
CONFIG = p.read(ROOT / p.CONFIG)
FIRST = re.search(r'<div id="divGlSearchArticles">[\s\S]*?\n {16}</div>', old.PAGE1).group()


def second(first=21, last=40, total=63, ids=None):
    return '<div id="divGlSearchArticles">' + old.fragment(first, last, total, ids) + '</div>'


def value(fragment, scope=None, status=200):
    return {"url": CONFIG["url"], "fragment": fragment, "scope_html": scope,
            "http_body_sha256": p.sha(fragment.encode()), "http_body_bytes": len(fragment.encode()),
            "http_status": status}


class Driver:
    def __init__(self, config, guard, clock, first=FIRST, next_page=None, status=200, transport_error=False):
        self.config, self.guard, self.clock = config, guard, clock
        self.first_html, self.next_html, self.status = first, next_page or second(), status
        self.transport_error = transport_error
        self.version = "TEST_DRIVER_NOT_A_BROWSER"
        self.closed = False; self.clicks = 0

    def __enter__(self): return self
    def __exit__(self, *args): self.closed = True

    def first(self):
        assert self.guard.admit(CONFIG["url"], "GET", "document")
        self.guard.response(CONFIG["url"], "GET", 200, {"content-type": "text/html"})
        return value(self.first_html, old.PAGE1)

    def pace(self, seconds): self.clock.sleep(seconds)

    def second(self, previous):
        self.clicks += 1
        assert self.guard.admit(CONFIG["url"], "POST", "xhr", '{"SearchKey":4,"CurrentPage":2}')
        if self.transport_error:
            self.guard.fail("BROWSER_REQUEST_FAILED_TLS_OR_TRANSPORT"); self.guard.check()
        self.guard.response(CONFIG["url"], "POST", self.status, {"content-type": "text/html"})
        self.guard.check()
        return value(self.next_html, status=self.status)


class BrowserHTMLTests(unittest.TestCase):
    def fake_run(self, tmp, *, dry=False, ready=True, **options):
        prep = Path(tmp) / "prep"; prep.mkdir()
        p.write(prep / "protected_old_files.json", {})
        p.write(prep / "cached_article_ids.json", ["100001"])
        p.write(prep / "manifest.json", {"files": {}})
        clock = old.Clock(); created = []
        def factory(config, guard):
            driver = Driver(config, guard, clock, **options); created.append(driver); return driver
        with patch.object(p, "load_preparation", return_value=(deepcopy(CONFIG), prep)), \
                patch.object(p, "readiness", return_value={"ready": ready}), \
                patch.object(p, "PlaywrightDriver", side_effect=AssertionError("NO REAL BROWSER")):
            result = p.run(ROOT, Path(tmp) / "state", dry_run=dry, driver_factory=factory, clock=clock.now)
        return result, created

    def test_exact_browser_contract_cannot_expand_or_weaken(self):
        p.validate(CONFIG)
        for key, val in [("ticker", "SSI"), ("max_business_requests", 3), ("max_context_request_attempts", 100),
                ("max_asset_attempts", 90), ("max_seconds", 180), ("headless", True),
                ("ignore_https_errors", True), ("persistent_profile", True), ("retry", True),
                ("resume", True), ("details", True), ("export_cookies_or_auth", True),
                ("playwright_version", "other"), ("user_agent", "spoof"), ("channel", "msedge")]:
            with self.subTest(key=key), self.assertRaises(ValueError): p.validate({**CONFIG, key: val})

    def test_archived_public_container_and_observed_button_contract(self):
        data = p.fragment_bytes(FIRST, 2000000)
        self.assertEqual(FIRST.encode(), data)
        parsed = p.prior.page(FIRST, 1)
        self.assertEqual((20, 63), (len(parsed["article_ids"]), parsed["coverage"]["reported_total"]))
        buttons = p.Document(FIRST).root.find("button")
        observed = [b for b in buttons if b.attrs.get("onclick") == "changePageArticles(2)" and b.text() == "2"]
        self.assertEqual(1, len(observed))

    def test_dry_check_creates_no_output_or_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, created = self.fake_run(tmp, dry=True)
            self.assertEqual("OFFLINE_CHECK_PASS", result["status"])
            self.assertEqual([], created); self.assertFalse((Path(tmp) / "state").exists())

    def test_missing_setup_stops_before_browser_and_can_seal_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, created = self.fake_run(tmp, ready=False)
            self.assertFalse(result["page2_verified"]); self.assertFalse(result["browser_launched"])
            self.assertEqual([], created); self.assertEqual(0, result["business_requests"])
            p.seal(Path(tmp) / "state", Path(tmp) / "partial.zip", artifact_type=p.TYPE)

    def test_two_rendered_HTML_pages_and_ZIP_hashes_without_full_DOM_or_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, created = self.fake_run(tmp)
            self.assertEqual("PASS_BROWSER_HTML_PAGE2_REVIEW_REQUIRED", result["status"])
            self.assertEqual([200, 200], result["http_business_statuses"])
            self.assertEqual(2, result["business_requests"])
            self.assertEqual(2, result["context_request_attempts"])
            self.assertEqual(1, created[0].clicks); self.assertTrue(created[0].closed)
            self.assertEqual(1, result["cached_page2_provider_ids"])
            self.assertEqual(23, result["remaining_query_rows"])
            self.assertFalse(result["resumable"]); self.assertFalse(result["bulk_collection_ready"])
            self.assertEqual(0, result["detail_requests"]); self.assertEqual(0, result["canonical_fields_applied"])
            out = Path(tmp) / "state"
            requests = p.read(out / "business_requests.json")
            self.assertGreaterEqual(requests[1]["at_monotonic"] - requests[0]["at_monotonic"], 8)
            self.assertEqual(FIRST.encode(), (out / "rendered_html/page1.html").read_bytes())
            self.assertFalse(p.read(out / "page1_receipt.json")["raw_http_body_archived"])
            archive = Path(tmp) / "pilot.zip"; p.seal(out, archive, artifact_type=p.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                manifest = json.loads(z.read("manifest.json"))
                self.assertEqual(p.TYPE, manifest["artifact_type"])
                for name, digest in manifest["files"].items(): self.assertEqual(digest, p.sha(z.read(name)))
                self.assertFalse(any("storage_state" in n or "har" in n or "cookies" in n for n in z.namelist()))

    def test_page2_source_failures_stop_after_single_click_and_seal(self):
        for options in [{"status": s} for s in [302, 400, 401, 403, 429, 500]] + [{"transport_error": True}]:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as tmp:
                result, created = self.fake_run(tmp, **options)
                self.assertEqual(1, created[0].clicks); self.assertTrue(created[0].closed)
                self.assertFalse(result["page2_verified"]); self.assertFalse(result["resumable"])
                self.assertTrue(result["source_stopped"])
                p.seal(Path(tmp) / "state", Path(tmp) / "partial.zip", artifact_type=p.TYPE)

    def test_repeated_overlap_duplicate_total_range_and_sensitive_DOM_never_pass(self):
        ids = [p.prior.page(FIRST, 1)["article_ids"][0], *range(100002,100021)]
        for fragment in [FIRST, second(total=64), second(first=41,last=60), second(ids=ids),
                second(ids=[100001]*20), second().replace('</div>','<input value="SECRET"></div>'),
                second().replace('</div>','<script>SECRET</script></div>'),
                second().replace('id="divGlSearchArticles"','id="divGlSearchArticles" data-token="SECRET"'),
                second().replace('</div>','verify you are human</div>')]:
            with self.subTest(fragment=fragment[:40]), tempfile.TemporaryDirectory() as tmp:
                result, created = self.fake_run(tmp, next_page=fragment)
                self.assertFalse(result["page2_verified"]); self.assertTrue(created[0].closed)
                files=list((Path(tmp)/'state').rglob('*.html'))
                self.assertFalse(any(b'SECRET' in f.read_bytes() for f in files))

    def test_html_size_limit_and_wrong_container(self):
        for fragment, limit in [(FIRST, 10), ('<div id="wrong"></div>', 2000000)]:
            with self.subTest(), self.assertRaises(ValueError): p.fragment_bytes(fragment, limit)

    def test_cli_blocks_rerun_and_has_no_resume_or_force(self):
        spec = importlib.util.spec_from_file_location("html_cli", ROOT/'scripts/corporate_actions/collect_vsdc_mbs_browser_html_pilot_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,CONFIG)
            (root/CONFIG['output_base']/'run-existing').mkdir(parents=True)
            for args in [['pilot'],['pilot','--resume'],['pilot','--force']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(cli,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',old.io.StringIO()),self.assertRaises(SystemExit):
                    cli.main()
                run.assert_not_called()


class PlaywrightAdapterTests(unittest.TestCase):
    def playwright_module(self, starter):
        package=ModuleType('playwright');api=ModuleType('playwright.sync_api')
        api.sync_playwright=lambda:starter;package.sync_api=api
        return patch.dict(sys.modules,{'playwright':package,'playwright.sync_api':api})

    def mocks(self):
        manager=MagicMock(); browser=manager.chromium.launch.return_value
        browser.version='TEST_BROWSER_NOT_LAUNCHED'
        context=browser.new_context.return_value; page=context.new_page.return_value
        page.url=CONFIG['url']
        response=MagicMock();response.status=200;response.body.return_value=old.PAGE1.encode()
        page.goto.return_value=response;page.content.return_value=old.PAGE1
        page.locator.return_value.evaluate.side_effect=[FIRST,second()]
        page.locator.return_value.filter.return_value.count.return_value=1
        pending=page.expect_response.return_value.__enter__.return_value
        pending.value=response
        starter=MagicMock();starter.start.return_value=manager
        return starter,manager,browser,context,page,response

    def test_normal_fresh_Chrome_options_DOM_reads_and_single_observed_button_click(self):
        starter,manager,browser,context,page,response=self.mocks()
        with tempfile.TemporaryDirectory() as tmp,self.playwright_module(starter):
            clock=old.Clock();g=p.Guard(CONFIG,Path(tmp),clock=clock.now)
            with p.PlaywrightDriver(CONFIG,g) as driver:
                request=MagicMock();request.url=CONFIG['url'];request.method='GET'
                request.resource_type='document';request.post_data=None;request.redirected_from=None
                request.headers={'cookie':'SECRET','accept':'text/html'}
                request.header_value.side_effect=lambda name:None
                route=MagicMock();route.request=request
                driver._route(route);route.continue_.assert_called_once()
                self.assertNotIn('SECRET',json.dumps(g.business))
                self.assertIn('cookie',g.business[0]['request_header_names'])
                self.assertEqual(FIRST,driver.first()['fragment'])
                driver.pace(8)
                driver.second(FIRST)
            manager.chromium.launch.assert_called_once_with(channel='chrome',headless=False,timeout=15000)
            browser.new_context.assert_called_once_with(ignore_https_errors=False,accept_downloads=False,service_workers='block')
            context.route.assert_called_once();context.route_web_socket.assert_called_once()
            page.locator.return_value.filter.return_value.click.assert_called_once()
            self.assertEqual(p.BUTTON,page.locator.call_args_list[1].args[0])
            self.assertTrue(all(c.args==('(el) => el.outerHTML',) for c in page.locator.return_value.evaluate.call_args_list))
            context.close.assert_called_once();browser.close.assert_called_once();manager.stop.assert_called_once()
            self.assertIsNone(g.stop_reason)

    def test_missing_page2_button_never_clicks_or_falls_back(self):
        starter,manager,browser,context,page,response=self.mocks()
        page.locator.return_value.filter.return_value.count.return_value=0
        with tempfile.TemporaryDirectory() as tmp,self.playwright_module(starter):
            g=p.Guard(CONFIG,Path(tmp),clock=old.Clock().now)
            with p.PlaywrightDriver(CONFIG,g) as driver,self.assertRaises(ValueError):driver.second(FIRST)
            page.locator.return_value.filter.return_value.click.assert_not_called()
            page.expect_response.assert_not_called()

    def test_browser_setup_failure_closes_and_TLSError_has_no_fallback(self):
        starter,manager,browser,context,page,response=self.mocks()
        manager.chromium.launch.side_effect=RuntimeError('TLS or browser launch failure')
        with tempfile.TemporaryDirectory() as tmp,self.playwright_module(starter):
            g=p.Guard(CONFIG,Path(tmp),clock=old.Clock().now)
            with self.assertRaises(RuntimeError):
                with p.PlaywrightDriver(CONFIG,g):pass
            self.assertEqual(1,manager.chromium.launch.call_count);manager.stop.assert_called_once()


class NetworkGuardTests(unittest.TestCase):
    def guard(self, tmp, check=lambda:None):
        clock=old.Clock();return p.Guard(deepcopy(CONFIG),Path(tmp),check,clock.now),clock

    def test_assets_scoped_external_blocked_and_no_header_values_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            g,c=self.guard(tmp)
            self.assertTrue(g.admit(CONFIG['url'],'GET','document'))
            self.assertTrue(g.admit('https://vsdc.vn/assets/libs/js/jquery.min.js?v=SECRET','GET','script'))
            self.assertFalse(g.admit('https://external.example/tracker?token=SECRET','GET','script'))
            self.assertIsNone(g.stop_reason);self.assertEqual(1,g.external_blocked)
            c.sleep(8);self.assertTrue(g.admit(CONFIG['url'],'POST','xhr','{ "SearchKey":4, "CurrentPage":2 }'))
            g.response(CONFIG['url'],'POST',200,{'Content-Type':'text/html','Set-Cookie':'SECRET','Authorization':'SECRET'})
            text=(Path(tmp)/'network_ledger.jsonl').read_text(encoding='utf-8')
            self.assertNotIn('SECRET',text);self.assertNotIn('Set-Cookie',text)

    def test_other_queries_details_credentials_redirects_bad_POST_and_early_click_block(self):
        cases=[('https://vsdc.vn/vi/ad/123','GET','document',None,False),
               (CONFIG['url'].replace('MBS','SSI'),'GET','document',None,False),
               ('https://person:SECRET@vsdc.vn/assets/x.js','GET','script',None,False),
               (CONFIG['url'],'GET','document',None,True),
               (CONFIG['url'],'POST','xhr','{"SearchKey":4,"CurrentPage":2}',False)]
        for args in cases:
            with self.subTest(args=args[:3]),tempfile.TemporaryDirectory() as tmp:
                g,c=self.guard(tmp);self.assertFalse(g.admit(*args));self.assertIsNotNone(g.stop_reason)
        for body, delay in [('{"SearchKey":4,"CurrentPage":3}',8),('{"SearchKey":4,"CurrentPage":2}',0)]:
            with tempfile.TemporaryDirectory() as tmp:
                g,c=self.guard(tmp);g.admit(CONFIG['url'],'GET','document');c.sleep(delay)
                self.assertFalse(g.admit(CONFIG['url'],'POST','xhr',body))

    def test_business_asset_context_time_and_old_state_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            g,c=self.guard(tmp);g.admit(CONFIG['url'],'GET','document');c.sleep(8)
            self.assertTrue(g.admit(CONFIG['url'],'POST','xhr','{"SearchKey":4,"CurrentPage":2}'))
            self.assertFalse(g.admit(CONFIG['url'],'POST','xhr','{"SearchKey":4,"CurrentPage":2}'))
        for kind in ['assets','context','time','old']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                def changed():raise ValueError('PROTECTED_OLD_FILE_CHANGED')
                g,c=self.guard(tmp,changed if kind=='old' else lambda:None)
                if kind=='assets':g.assets=78
                if kind=='context':g.attempts=80
                if kind=='time':c.sleep(90)
                args=(CONFIG['url'],'GET','document') if kind in {'time','old'} else ('https://vsdc.vn/assets/x.css','GET','stylesheet')
                self.assertFalse(g.admit(*args));self.assertIsNotNone(g.stop_reason)

    def test_all_HTTP_errors_retry_after_and_declared_oversize_stop(self):
        for status,headers in [(s,{}) for s in [301,400,401,403,429,500]]+[(200,{'Retry-After':'60'}),(200,{'Content-Length':'2000001'})]:
            with self.subTest(status=status,headers=headers),tempfile.TemporaryDirectory() as tmp:
                g,c=self.guard(tmp);g.response(CONFIG['url'],'GET',status,headers)
                with self.assertRaises(ValueError):g.check()


if __name__=='__main__':unittest.main()
