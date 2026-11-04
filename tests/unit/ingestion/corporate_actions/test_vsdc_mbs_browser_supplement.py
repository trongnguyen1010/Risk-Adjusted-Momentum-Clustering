from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_mbs_browser_supplement as p
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_browser_html as html
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old

ROOT=old.ROOT
CONFIG=p.read(ROOT/p.CONFIG)
TITLE='MBS : Nhận cổ phiếu phát hành do thực hiện tăng vốn cổ phần từ nguồn vốn chủ sở hữu; Thực hiện quyền mua cổ phiếu'
DETAIL='<h3 class="title-category">'+TITLE+'</h3><div class="content-category"><p>Mã chứng khoán: MBS</p><p>Đây là fixture tổng hợp, không phải evidence giá.</p></div>'


def fragment(number,total=63,has_candidate=True):
    first=(number-1)*20+1;last=min(number*20,total)
    result=html.second(first,last,total,range(100000+first,100000+last+1))
    if number==2 and has_candidate:
        result=result.replace('/vi/ad/100021','/vi/ad/187243').replace('MBS : Thông báo cổ đông 100021',TITLE)
    return result


class FakeDriver:
    def __init__(self,config,guard,clock,*,pages=None,detail=DETAIL,status=200):
        self.config,self.guard,self.clock=config,guard,clock
        self.pages=pages or [fragment(n) for n in range(1,5)]
        self.detail_html,self.status=detail,status
        self.closed=False;self.clicks=[];self.detail_calls=0;self.version='TEST_NOT_REAL_CHROME'
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def pace(self,seconds):self.clock.sleep(seconds)
    def response(self,number):
        status=self.status if number==3 else 200
        self.guard.response(CONFIG['url'],'GET' if number==1 else 'POST',status,{'content-type':'text/html'})
        self.guard.check()
        return html.value(self.pages[number-1],old.PAGE1)
    def first(self):
        assert self.guard.admit(CONFIG['url'],'GET','document')
        return self.response(1)
    def next_page(self,number,previous):
        self.clicks.append(number)
        assert self.guard.admit(CONFIG['url'],'POST','xhr',json.dumps({'SearchKey':4,'CurrentPage':number}))
        return self.response(number)
    def detail(self):
        self.detail_calls+=1
        assert self.guard.admit(p.DETAIL_URL,'GET','document')
        self.guard.response(p.DETAIL_URL,'GET',200,{'content-type':'text/html'})
        self.guard.check()
        return {**html.value(self.detail_html),'url':p.DETAIL_URL}


class SupplementTests(unittest.TestCase):
    def fake_run(self,tmp,*,dry=False,cached=None,ready=True,**options):
        prep=Path(tmp)/'prep';prep.mkdir()
        for name,value in [('protected_old_files.json',{}),('cached_article_ids.json',cached or ['100001']),
                           ('candidate_187243.json',{}),('parent_manifests.json',{}),('manifest.json',{'files':{}})]:
            p.write(prep/name,value)
        clock=old.Clock();drivers=[]
        def factory(config,guard):
            d=FakeDriver(config,guard,clock,**options);drivers.append(d);return d
        with patch.object(p,'load_preparation',return_value=(deepcopy(CONFIG),prep)), \
                patch.object(p.old,'readiness',return_value={'ready':ready}):
            result=p.run(ROOT,Path(tmp)/'state',dry_run=dry,driver_factory=factory,clock=clock.now)
        return result,drivers

    def test_exact_contract_cannot_expand_or_bypass(self):
        p.validate(CONFIG)
        for key,value in [('max_list_pages',5),('detail_url','https://vsdc.vn/vi/ad/1'),
                ('max_business_requests',6),('max_context_request_attempts',200),('max_seconds',999),
                ('retry',True),('resume',True),('ignore_https_errors',True),('headless',True),
                ('persistent_profile',True),('export_cookies_or_auth',True),('canonical_build',True),
                ('automatic_approval',True),('user_agent','spoof')]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate({**CONFIG,key:value})

    def test_full_four_pages_then_exact_detail_and_immutable_ZIP(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.fake_run(tmp)
            self.assertEqual('PASS_FRESH_MBS_QUERY_AND_EXACT_DETAIL_REVIEW_REQUIRED',result['status'])
            self.assertTrue(result['fresh_query_complete']);self.assertTrue(result['detail_captured'])
            self.assertEqual(63,result['query_article_ids']);self.assertEqual(4,result['list_pages'])
            self.assertEqual([2,3,4],drivers[0].clicks);self.assertEqual(1,drivers[0].detail_calls)
            self.assertTrue(drivers[0].closed);self.assertEqual([200]*5,result['http_business_statuses'])
            self.assertEqual(5,result['business_requests']);self.assertEqual(1,result['detail_requests'])
            self.assertFalse(result['bulk_collection_ready']);self.assertFalse(result['resumable'])
            self.assertEqual(0,result['canonical_fields_applied'])
            state=Path(tmp)/'state';query=p.read(state/'complete_query_articles.json')
            self.assertEqual(63,len(query['articles']));self.assertFalse(query['historical_event_coverage_certified'])
            self.assertFalse(p.read(state/'detail187243_public_text.json')['price_verified'])
            calls=p.read(state/'business_requests.json')
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic']>=8 for a,b in zip(calls,calls[1:])))
            archive=Path(tmp)/'output.zip';p.seal(state,archive,artifact_type=p.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                for name,digest in json.loads(z.read('manifest.json'))['files'].items():
                    self.assertEqual(digest,p.sha(z.read(name)))
            self.assertEqual(5,len(list((state/'rendered_html').glob('*.html'))))

    def test_dryrun_does_not_create_output_or_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.fake_run(tmp,dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS',result['status']);self.assertFalse(result['browser_launched'])
            self.assertEqual([],drivers);self.assertFalse((Path(tmp)/'state').exists())

    def test_setup_missing_seals_partial_without_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.fake_run(tmp,ready=False)
            self.assertEqual([],drivers);self.assertFalse(result['detail_captured'])
            p.seal(Path(tmp)/'state',Path(tmp)/'partial.zip',artifact_type=p.TYPE)

    def test_total_change_stale_overlap_duplicate_or_more_than_four_pages_stop_before_detail(self):
        cases=[]
        for bad in [fragment(3,total=64),fragment(2),fragment(3).replace('100042','100041'),
                    fragment(3).replace('100041','100022')]:
            pages=[fragment(n) for n in range(1,5)];pages[2]=bad;cases.append(pages)
        cases.append([fragment(n,total=81) for n in range(1,5)])
        for pages in cases:
            with self.subTest(pages=pages[2][:60]),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.fake_run(tmp,pages=pages)
                self.assertFalse(result['detail_captured']);self.assertEqual(0,drivers[0].detail_calls)
                self.assertTrue(result['source_stopped']);self.assertFalse(result['fresh_query_complete'])

    def test_candidate_missing_or_cached_never_opens_detail(self):
        for options in [{'pages':[fragment(n,has_candidate=False) for n in range(1,5)]},{'cached':['187243']}]:
            with self.subTest(options=list(options)),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.fake_run(tmp,**options)
                self.assertTrue(result['fresh_query_complete']);self.assertFalse(result['detail_captured'])
                self.assertEqual(0,drivers[0].detail_calls);self.assertTrue(result['source_stopped'])

    def test_HTTP_errors_stop_after_page3_no_retry_or_detail(self):
        for status in [301,400,401,403,429,500]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.fake_run(tmp,status=status)
                self.assertEqual([2,3],drivers[0].clicks);self.assertEqual(0,drivers[0].detail_calls)
                self.assertTrue(drivers[0].closed);self.assertTrue(result['source_stopped'])
                p.seal(Path(tmp)/'state',Path(tmp)/'partial.zip',artifact_type=p.TYPE)

    def test_private_challenge_or_wrong_detail_title_not_archived(self):
        for detail in [DETAIL.replace('MBS :','SSI :'),DETAIL.replace('</div>','<input value="SECRET"></div>'),
                DETAIL.replace('</div>','<script>SECRET</script></div>'),
                DETAIL.replace('content-category','content-category" data-token="SECRET'),
                DETAIL.replace('</div>','verify you are human</div>')]:
            with self.subTest(detail=detail[:30]),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.fake_run(tmp,detail=detail)
                self.assertFalse(result['detail_captured'])
                self.assertFalse((Path(tmp)/'state/rendered_html/detail187243.html').exists())

    def test_title_only_colon_spacing_normalization_no_terms_approval(self):
        data,preview=p.public_detail(DETAIL.replace('MBS :','MBS:'),TITLE)
        self.assertIn(b'title-category',data);self.assertFalse(preview['revision_coverage_verified'])
        self.assertFalse(preview['record_date_verified']);self.assertFalse(preview['terms_verified'])
        _,timed=p.public_detail(DETAIL+'<div class="time-newstcph">Cập nhật ngày 17/09/2025</div>',TITLE)
        self.assertEqual(['Cập nhật ngày 17/09/2025'],timed['source_time_texts'])
        self.assertIn('NOT_HISTORICAL_AVAILABLE_AT',timed['time_semantics'])

    def test_CLI_blocks_rerun_force_and_resume(self):
        spec=importlib.util.spec_from_file_location('mbs_supp_cli',ROOT/'scripts/corporate_actions/collect_vsdc_mbs_browser_supplement_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,CONFIG)
            (root/CONFIG['output_base']/'run-existing').mkdir(parents=True)
            for args in [['pilot'],['pilot','--resume'],['pilot','--force']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(cli,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',old.io.StringIO()),self.assertRaises(SystemExit):
                    cli.main()
                run.assert_not_called()


class GuardTests(unittest.TestCase):
    def make(self,tmp):
        clock=old.Clock();return p.Guard(deepcopy(CONFIG),Path(tmp),clock=clock.now),clock

    def fill(self,g,c):
        self.assertTrue(g.admit(CONFIG['url'],'GET','document'))
        for number in [2,3,4]:
            c.sleep(8);self.assertTrue(g.admit(CONFIG['url'],'POST','xhr',json.dumps({'SearchKey':4,'CurrentPage':number})))

    def test_detail_cannot_open_before_armed_or_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            g,c=self.make(tmp);self.assertFalse(g.admit(p.DETAIL_URL,'GET','document'))
        with tempfile.TemporaryDirectory() as tmp:
            g,c=self.make(tmp);self.fill(g,c);g.list_complete=True;g.expected_detail_title=TITLE
            c.sleep(8);self.assertTrue(g.admit(p.DETAIL_URL,'GET','document'))
            c.sleep(8);self.assertFalse(g.admit(p.DETAIL_URL,'GET','document'))

    def test_skipped_page_other_detail_extra_query_redirect_or_early_click_stop(self):
        cases=[(CONFIG['url'],'POST','xhr','{"SearchKey":4,"CurrentPage":3}',False,8),
               (CONFIG['url'],'POST','xhr','{"SearchKey":4,"CurrentPage":2}',False,0),
               (CONFIG['url'],'POST','xhr','{"SearchKey":4,"CurrentPage":2}',True,8),
               ('https://vsdc.vn/vi/ad/187244','GET','document',None,False,8)]
        for url,method,resource,body,redirect,delay in cases:
            with self.subTest(url=url,delay=delay),tempfile.TemporaryDirectory() as tmp:
                g,c=self.make(tmp);g.admit(CONFIG['url'],'GET','document');c.sleep(delay)
                self.assertFalse(g.admit(url,method,resource,body,redirect));self.assertIsNotNone(g.stop_reason)

    def test_shared_asset_context_time_access_and_old_state_gates(self):
        for kind in ['asset','context','time','old','challenge','TLS']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                g,c=self.make(tmp)
                if kind=='asset':g.assets=155
                if kind=='context':g.attempts=160
                if kind=='time':c.sleep(150)
                if kind=='old':g.check_old=lambda:(_ for _ in ()).throw(ValueError('OLD_CHANGED'))
                if kind=='TLS':g.fail('BROWSER_REQUEST_FAILED_TLS_OR_TRANSPORT')
                url='https://vsdc.vn/assets/x.css' if kind=='asset' else CONFIG['url']
                if kind=='challenge':url='https://vsdc.vn/login'
                self.assertFalse(g.admit(url,'GET','stylesheet' if kind=='asset' else 'document'))
                self.assertIsNotNone(g.stop_reason)

    def test_detail_response_error_retry_after_size_and_no_secrets(self):
        for status,headers in [(400,{}),(403,{}),(429,{}),(200,{'Retry-After':'8'}),
                (200,{'Content-Length':'2000001'})]:
            with self.subTest(status=status,headers=headers),tempfile.TemporaryDirectory() as tmp:
                g,c=self.make(tmp);g.response(p.DETAIL_URL,'GET',status,{**headers,'Set-Cookie':'SECRET'})
                self.assertEqual(1,len(g.responses));self.assertIsNotNone(g.stop_reason)
                self.assertNotIn('SECRET',(Path(tmp)/'network_ledger.jsonl').read_text(encoding='utf-8'))


class AdapterTests(html.PlaywrightAdapterTests):
    # Preserve all inherited fresh-browser/TLS/locator checks; these three tests exercise the new adapter paths.
    def test_next_page_uses_only_exact_UI_button_and_readonly_DOM(self):
        starter,manager,browser,context,page,response=self.mocks()
        with tempfile.TemporaryDirectory() as tmp,self.playwright_module(starter):
            g,c=GuardTests().make(tmp)
            with p.Driver(CONFIG,g) as d:d.next_page(3,html.FIRST)
            self.assertEqual('#divGlSearchArticles #d_number_of_page button[onclick="changePageArticles(3)"]',page.locator.call_args_list[0].args[0])
            page.locator.return_value.filter.return_value.click.assert_called_once()

    def test_detail_navigation_exact_url_and_two_public_selectors(self):
        starter,manager,browser,context,page,response=self.mocks();page.url=p.DETAIL_URL
        page.locator.return_value.count.return_value=1
        page.locator.return_value.evaluate.side_effect=['<h3 class="title-category">'+TITLE+'</h3>',
            '<div class="content-category">PUBLIC</div>','<div class="time-newstcph">UPDATE</div>']
        with tempfile.TemporaryDirectory() as tmp,self.playwright_module(starter):
            g,c=GuardTests().make(tmp)
            with p.Driver(CONFIG,g) as d:result=d.detail()
            page.goto.assert_called_once_with(p.DETAIL_URL,wait_until='domcontentloaded',timeout=15000)
            self.assertEqual(['.title-category','.content-category','.time-newstcph'],[x.args[0] for x in page.locator.call_args_list])
            self.assertEqual(p.DETAIL_URL,result['url'])


if __name__=='__main__':unittest.main()
