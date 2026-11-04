from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_browser_batch001 as p
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_browser_html as html
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old

ROOT=old.ROOT;CONFIG=p.read(ROOT/p.CONFIG)
TOTALS=dict(zip(p.TICKERS,[33,49,27,34,27,47,200,44,41,28,25,24,26,73,32,21,31,24,33,34]))


class Driver:
    def __init__(self,config,guard,clock,mode=None):
        self.config,self.guard,self.clock=config,guard,clock;self.mode=mode
        self.ticker=config['ticker'];self.total=TOTALS[self.ticker];self.closed=False;self.clicks=[]
        self.version='TEST_NOT_REAL_CHROME'
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def pace(self,seconds):self.clock.sleep(seconds)
    def capture(self,number):
        status=429 if self.mode=='ABT429' and self.ticker=='ABT' else 200
        self.guard.response(self.config['url'],'GET' if number==1 else 'POST',status,{'content-type':'text/html'})
        self.guard.check()
        total=401 if self.mode=='AAM401rows' and self.ticker=='AAM' else self.total
        if self.mode=='CHANGED' and self.ticker=='AAM' and number==2:total+=1
        first=(number-1)*20+1;last=min(number*20,total)
        offset=1000000+p.TICKERS.index(self.ticker)*1000
        ids=list(range(offset+first,offset+last+1))
        if number==1:ids[0]=999999
        fragment=html.second(first,last,total,ids).replace('MBS',self.ticker)
        if self.mode=='STALE' and self.ticker=='AAM' and number==2:
            fragment=html.second(1,20,total,range(1000001,1000021))
        return {**html.value(fragment,old.PAGE1.replace('MBS',self.ticker)),'url':self.config['url']}
    def first(self):
        assert self.guard.admit(self.config['url'],'GET','document')
        return self.capture(1)
    def next_page(self,number,previous):
        self.clicks.append(number)
        assert self.guard.admit(self.config['url'],'POST','xhr',json.dumps({'SearchKey':4,'CurrentPage':number}))
        return self.capture(number)


class BatchTests(unittest.TestCase):
    def run_fake(self,tmp,*,dry=False,ready=True,mode=None):
        prep=Path(tmp)/'prep';prep.mkdir()
        for name,val in [('manifest.json',{'files':{}}),('protected_old_files.json',{}),
                ('reusable_detail_provider_ids.json',['999999','1000002','187243']),
                ('known_discovery_provider_ids.json',['999999','1000002','1000003','187243']),
                ('batch_plan.json',{}),('cache_policy.json',{})]:p.write(prep/name,val)
        clock=old.Clock();drivers=[]
        def factory(config,guard):
            d=Driver(config,guard,clock,mode);drivers.append(d);return d
        with patch.object(p,'load_preparation',return_value=(deepcopy(CONFIG),prep)), \
                patch.object(p.mbs.old,'readiness',return_value={'ready':ready}):
            result=p.run(ROOT,Path(tmp)/'state',dry_run=dry,driver_factory=factory,clock=clock.now)
        return result,drivers

    def test_exact20_contract_no_other_batch_or_security_weakening(self):
        p.validate(CONFIG);self.assertEqual(20,len(p.TICKERS));self.assertEqual(54,sum((n+19)//20 for n in TOTALS.values()))
        for key,val in [('tickers',['A32']),('batch_id','proposed-002'),('max_business_requests',101),
                ('max_list_pages_per_query',21),('business_interval_seconds',2),('max_seconds',3600),
                ('details',True),('bulk_enabled',True),('retry',True),('resume',True),
                ('ignore_https_errors',True),('persistent_profile',True),('headless',True),('user_agent','spoof')]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate({**CONFIG,key:val})

    def test_all20_queries54_requests_four_seconds_and_cache_discovery_separation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.run_fake(tmp)
            self.assertEqual('PASS_BATCH001_LIST_DISCOVERY_REVIEW_REQUIRED',result['status'])
            self.assertEqual(list(p.TICKERS),result['completed_tickers']);self.assertEqual(20,result['browser_launches'])
            self.assertEqual(54,result['business_requests']);self.assertEqual(212,result['elapsed_seconds'])
            self.assertTrue(all(d.closed for d in drivers));self.assertEqual(list(range(2,11)),drivers[6].clicks)
            self.assertEqual(0,result['detail_requests']);self.assertFalse(result['resumable']);self.assertFalse(result['bulk_collection_ready'])
            self.assertEqual(0,result['canonical_fields_applied'])
            self.assertEqual(2,result['reusable_cached_detail_IDs']);self.assertEqual(1,result['previously_discovered_uncached_IDs'])
            self.assertEqual(result['new_candidate_IDs'],result['first_discovered_IDs']+result['previously_discovered_uncached_IDs'])
            state=Path(tmp)/'state';calls=[]
            for ticker in p.TICKERS:
                complete=p.read(state/ticker/'complete_query.json');self.assertEqual(TOTALS[ticker],complete['reported_total'])
                self.assertFalse(complete['historical_event_coverage_certified']);calls.extend(p.read(state/ticker/'business_requests.json'))
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic']==4 for a,b in zip(calls,calls[1:])))
            merged=p.read(state/'deduplicated_query_articles.json');common=next(r for r in merged if r['provider_article_id']=='999999')
            self.assertEqual(list(p.TICKERS),common['query_tickers'])
            self.assertTrue(all(not r['detail_fetch_authorized'] and not r['event_identity_verified'] for r in merged))
            checkpoints=sorted((state/'checkpoints').glob('*.json'));self.assertEqual(41,len(checkpoints))
            self.assertEqual('FINAL_REVIEW_REQUIRED',p.read(checkpoints[-1])['event'])
            archive=Path(tmp)/'batch.zip';p.seal(state,archive,artifact_type=p.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                for name,digest in json.loads(z.read('manifest.json'))['files'].items():self.assertEqual(digest,p.sha(z.read(name)))

    def test_error_stops_whole_batch_preserving_completed_queries(self):
        for mode,expected in [('ABT429',list(p.TICKERS[:5])),('CHANGED',[]),('STALE',[]),('AAM401rows',[])]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.run_fake(tmp,mode=mode)
                self.assertTrue(result['source_stopped']);self.assertEqual(expected,result['completed_tickers'])
                self.assertEqual(len(expected)+1,len(drivers));self.assertTrue(all(d.closed for d in drivers))
                self.assertFalse(result['resumable']);self.assertFalse(result['bulk_collection_ready'])
                p.seal(Path(tmp)/'state',Path(tmp)/'partial.zip',artifact_type=p.TYPE)

    def test_dryrun_and_missing_setup_do_not_start_browser(self):
        for dry,ready in [(True,True),(False,False)]:
            with self.subTest(dry=dry),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.run_fake(tmp,dry=dry,ready=ready);self.assertEqual([],drivers)
                if dry:self.assertFalse((Path(tmp)/'state').exists())
                else:self.assertEqual(0,result['browser_launches'])

    def test_twentieth_page_range_and_overlap_duplicate_or_total_change_gates(self):
        fragment=html.second(381,400,400,range(1381,1401))
        parsed=p.list_page(fragment,20,'ACB',400,set(range(1001,1381)))
        self.assertEqual(20,len(parsed['article_ids']))
        for number,total,seen in [(21,400,()),(20,399,()),(20,400,['1381'])]:
            with self.subTest(number=number,total=total),self.assertRaises(ValueError):p.list_page(fragment,number,'ACB',total,seen)

    def test_CLI_fixed_batch_rejects_other_batch_resume_force_or_rate_override(self):
        spec=importlib.util.spec_from_file_location('batch001_cli',ROOT/'scripts/corporate_actions/collect_vsdc_browser_batch001_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,CONFIG)
            (root/CONFIG['output_base']/'run-existing').mkdir(parents=True)
            for args in [['batch'],['batch','--batch','2'],['batch','--resume'],['batch','--force'],['batch','--interval','2']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(cli,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',old.io.StringIO()),self.assertRaises(SystemExit):cli.main()
                run.assert_not_called()


class GuardTests(unittest.TestCase):
    def make(self,tmp):
        c=old.Clock();shared=p.SharedBudget(CONFIG,c.now)
        local={**CONFIG,'ticker':'ACB','url':p.search_url('ACB'),'max_seconds':180,
               'max_context_request_attempts':98,'max_asset_attempts':78}
        return p.Guard(local,Path(tmp),lambda:None,c.now,shared),shared,c

    def test_pages1_through20_allow_then21_and_skips_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            g,s,c=self.make(tmp);self.assertTrue(g.admit(p.search_url('ACB'),'GET','document'))
            for number in range(2,21):
                c.sleep(4);self.assertTrue(g.admit(p.search_url('ACB'),'POST','xhr',json.dumps({'SearchKey':4,'CurrentPage':number})))
            c.sleep(4);self.assertFalse(g.admit(p.search_url('ACB'),'POST','xhr','{"SearchKey":4,"CurrentPage":21}'))
        with tempfile.TemporaryDirectory() as tmp:
            g,s,c=self.make(tmp);g.admit(p.search_url('ACB'),'GET','document');c.sleep(4)
            self.assertFalse(g.admit(p.search_url('ACB'),'POST','xhr','{"SearchKey":4,"CurrentPage":3}'))

    def test_batch_and_query_context_asset_time_caps_and_interval(self):
        for mode in ['business','global_context','query_context','assets','global_time','query_time','interval','oldfile']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp)
                if mode=='business':s.business=100
                if mode=='global_context':s.attempts=1660
                if mode=='query_context':g.attempts=98
                if mode=='assets':g.assets=78
                if mode=='global_time':c.sleep(1200)
                if mode=='query_time':c.sleep(180)
                if mode=='interval':s.last=c.now()-3.999
                if mode=='oldfile':g.check_old=lambda:(_ for _ in ()).throw(ValueError('OLD_CHANGED'))
                url='https://vsdc.vn/assets/x.css' if mode=='assets' else p.search_url('ACB')
                self.assertFalse(g.admit(url,'GET','stylesheet' if mode=='assets' else 'document'))
                self.assertIsNotNone(g.stop_reason)

    def test_no_other_queries_details_redirects_or_cookie_exports(self):
        for args in [(p.search_url('MBS'),'GET','document',None,False),
                     (p.mbs.DETAIL_URL,'GET','document',None,False),
                     (p.search_url('ACB'),'GET','document',None,True)]:
            with self.subTest(args=args[:2]),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);self.assertFalse(g.admit(*args));self.assertIsNotNone(g.stop_reason)
        for status,headers in [(400,{}),(403,{}),(429,{}),(200,{'Retry-After':'8'})]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);g.response(p.search_url('ACB'),'GET',status,{**headers,'Set-Cookie':'SECRET'})
                with self.assertRaises(ValueError):g.check()
                self.assertNotIn('SECRET',(Path(tmp)/'network_ledger.jsonl').read_text(encoding='utf8'))


class AdapterTests(html.PlaywrightAdapterTests):
    def test_archived_ACB10page_button_fixture_has_observed_next_action(self):
        folder=ROOT/'tests/fixtures/corporate_actions/vsdc_batch001_v1'
        raw=(folder/'acb_page1_paging.html').read_bytes();provenance=p.read(folder/'provenance.json')
        self.assertEqual(provenance['fixture_sha256'],p.sha(raw))
        buttons=p.mbs.Document(raw.decode()).root.find('button')
        self.assertIn(('>','changePageArticles(2)'),[(n.text(),n.attrs['onclick']) for n in buttons])
        self.assertIn(('>>','changePageArticles(10)'),[(n.text(),n.attrs['onclick']) for n in buttons])

    def test_numeric_then_observed_next_arrow_and_missing_or_ambiguous_stop(self):
        for numeric,arrow,clicks,label in [(1,1,1,'6'),(0,1,1,'>'),(0,0,0,None),(2,1,0,None),(0,2,0,None)]:
            with self.subTest(numeric=numeric,arrow=arrow),tempfile.TemporaryDirectory() as tmp:
                starter,manager,browser,context,page,response=self.mocks()
                numeric_node=MagicMock();numeric_node.count.return_value=numeric
                arrow_node=MagicMock();arrow_node.count.return_value=arrow
                page.locator.return_value.filter.side_effect=[numeric_node,arrow_node]
                page.url=p.search_url('ACB')
                with self.playwright_module(starter):
                    g,s,c=GuardTests().make(tmp)
                    with p.Driver({**CONFIG,'url':p.search_url('ACB')},g) as driver:
                        if clicks:driver.next_page(6,html.FIRST)
                        else:
                            with self.assertRaises(ValueError):driver.next_page(6,html.FIRST)
                target=numeric_node if numeric==1 else arrow_node
                self.assertEqual(clicks,target.click.call_count)
                if not clicks:page.expect_response.assert_not_called()
                else:
                    ledger=p.speed.base.rows(Path(tmp)/'network_ledger.jsonl')
                    self.assertEqual(label,ledger[0]['visible_label']);self.assertEqual(6,ledger[0]['target_page'])


if __name__=='__main__':unittest.main()
