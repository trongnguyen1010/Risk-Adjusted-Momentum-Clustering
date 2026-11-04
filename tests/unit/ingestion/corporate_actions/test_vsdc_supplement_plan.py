from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_supplement_plan as p
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_browser_html as b
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old

ROOT=old.ROOT;CONFIG=p.read(ROOT/p.CONFIG)


def candidate(ticker,total,exchange='HNX'):
    return {'ticker':ticker,'exchange':exchange,'url':p.search_url(ticker),'reported_total':total,
        'known_list_ids':20,'unseen_query_row_slots':total-20,'query_status':'QUERY_LIST_INCOMPLETE'}


class PlanTests(unittest.TestCase):
    def test_contract_cannot_expand_pilot_to_bulk_or_fetch_details(self):
        p.validate(CONFIG)
        for key,val in [('pilot_tickers',['A32','AAA','MBS']),('details',True),('bulk_enabled',True),
                ('max_business_requests',100),('max_context_attempts',1000),('max_list_pages_per_query',20),
                ('max_seconds',3600),('ignore_https_errors',True),('retry',True),('resume',True),
                ('persistent_profile',True),('user_agent','spoof'),('headless',True)]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate({**CONFIG,key:val})

    def test_partition_closed_pilot_large_and_batches_once_with_budgets(self):
        source=[candidate('MBS',63),candidate('A32',35,'UPCOM'),candidate('AAA',51,'HOSE'),
                candidate('IDJ',24),candidate('HAN',15408,'UPCOM')]
        source.extend(candidate(f'T{i:03d}',399) for i in range(23))
        inv,batches=p.build_plan(source,{'MBS'},CONFIG)
        indexed={r['ticker']:r for r in inv}
        self.assertEqual('COMPLETED_REVIEWED_QUERY_SNAPSHOT',indexed['MBS']['status'])
        self.assertEqual('HOLD_LARGE_QUERY_SCOPE_REVIEW',indexed['HAN']['status'])
        self.assertEqual(771,indexed['HAN']['estimated_fresh_list_requests'])
        self.assertEqual('PILOT_PREPARED_NOT_EXECUTED',indexed['AAA']['status'])
        members=[t for batch in batches for t in batch['tickers']]
        self.assertEqual(23,len(members));self.assertEqual(23,len(set(members)))
        self.assertTrue(all(len(batch['tickers'])<=20 and batch['estimated_list_requests']<=100 for batch in batches))
        self.assertTrue(all(not batch['acquisition_authorized'] for batch in batches))
        self.assertTrue(all(r['new_detail_requests_estimate'] is None and not r['bulk_authorized'] for r in inv))
        self.assertNotIn('MBS',members);self.assertNotIn('HAN',members)

    def test_duplicate_invalid_and_unknown_completion_refused(self):
        for source,completed in [([candidate('A',25),candidate('A',30)],set()),
                ([candidate('A',20)],set()),([candidate('A',25)],{'MBS'})]:
            with self.subTest(),self.assertRaises(ValueError):p.build_plan(source,completed,CONFIG)


class Driver:
    def __init__(self,config,guard,clock,mode=None):
        self.config,self.guard,self.clock=config,guard,clock;self.mode=mode
        self.ticker=config['ticker'];self.version='MOCK_NOT_LIVE';self.closed=False;self.clicks=[]
        self.total={'A32':35,'AAA':51,'IDJ':24}[self.ticker]
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def pace(self,seconds):self.clock.sleep(seconds)
    def snapshot(self,number):
        status=400 if self.mode=='AAA_HTTP400' and self.ticker=='AAA' else 200
        self.guard.response(self.config['url'],'GET' if number==1 else 'POST',status,{'content-type':'text/html'})
        self.guard.check()
        first=(number-1)*20+1;last=min(number*20,self.total)
        # One provider ID appears across queries to exercise global deduplication.
        offset={'A32':100000,'AAA':200000,'IDJ':300000}[self.ticker]
        ids=list(range(offset+first,offset+last+1))
        if number==1:ids[0]=999999
        fragment=b.second(first,last,self.total,ids).replace('MBS',self.ticker)
        if self.mode=='STALE' and self.ticker=='A32' and number==2:
            fragment=b.second(1,20,self.total,list(range(100001,100021)))
        return {**b.value(fragment,old.PAGE1.replace('MBS',self.ticker)),'url':self.config['url']}
    def first(self):
        assert self.guard.admit(self.config['url'],'GET','document')
        return self.snapshot(1)
    def next_page(self,number,previous):
        self.clicks.append(number)
        assert self.guard.admit(self.config['url'],'POST','xhr',json.dumps({'SearchKey':4,'CurrentPage':number}))
        return self.snapshot(number)


class PilotTests(unittest.TestCase):
    def fake_run(self,tmp,*,dry=False,ready=True,mode=None):
        prep=Path(tmp)/'prep';prep.mkdir()
        for name,value in [('protected_old_files.json',{}),('reusable_detail_provider_ids.json',['999999','100002','187243']),
                           ('pilot_plan.json',{}),('cache_policy.json',{}),('manifest.json',{'files':{}})]:
            p.write(prep/name,value)
        clock=old.Clock();drivers=[]
        def factory(config,guard):
            driver=Driver(config,guard,clock,mode);drivers.append(driver);return driver
        with patch.object(p,'load_preparation',return_value=(deepcopy(CONFIG),prep)), \
                patch.object(p.mbs.old,'readiness',return_value={'ready':ready}):
            result=p.run(ROOT,Path(tmp)/'state',dry_run=dry,driver_factory=factory,clock=clock.now)
        return result,drivers

    def test_three_fresh_queries_shared_rate_cache_reuse_global_dedup_and_ZIP(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.fake_run(tmp)
            self.assertEqual('PASS_THREE_QUERY_LIST_VALIDATION_REVIEW_REQUIRED',result['status'])
            self.assertEqual(list(p.PILOT),result['completed_tickers']);self.assertEqual(3,result['browser_launches'])
            self.assertEqual(7,result['business_requests']);self.assertEqual(0,result['detail_requests'])
            self.assertTrue(all(d.closed for d in drivers));self.assertFalse(result['resumable'])
            self.assertFalse(result['bulk_collection_ready']);self.assertEqual(0,result['canonical_fields_applied'])
            # 35+51+24 rows minus two repeated instances of999999.
            self.assertEqual(108,result['unique_provider_IDs']);self.assertEqual(2,result['reusable_cached_detail_IDs'])
            self.assertEqual(106,result['new_candidate_IDs'])
            output=Path(tmp)/'state';all_calls=[]
            for ticker in p.PILOT:
                all_calls.extend(p.read(output/ticker/'business_requests.json'))
                self.assertTrue(p.read(output/ticker/'complete_query.json')['query_exhausted_in_session'])
                self.assertFalse(p.read(output/ticker/'complete_query.json')['historical_event_coverage_certified'])
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic']>=8 for a,b in zip(all_calls,all_calls[1:])))
            merged=p.read(output/'deduplicated_query_articles.json');common=next(r for r in merged if r['provider_article_id']=='999999')
            self.assertEqual(list(p.PILOT),common['query_tickers']);self.assertTrue(common['detail_reusable_from_cache'])
            self.assertTrue(all(not r['detail_fetch_authorized'] and not r['event_identity_verified'] for r in merged))
            archive=Path(tmp)/'pilot.zip';p.seal(output,archive,artifact_type=p.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                for name,digest in json.loads(z.read('manifest.json'))['files'].items():self.assertEqual(digest,p.sha(z.read(name)))

    def test_first_ticker_failure_stops_whole_run_without_second_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.fake_run(tmp,mode='STALE')
            self.assertEqual(1,len(drivers));self.assertTrue(drivers[0].closed)
            self.assertTrue(result['source_stopped']);self.assertEqual([],result['completed_tickers'])
            p.seal(Path(tmp)/'state',Path(tmp)/'partial.zip',artifact_type=p.TYPE)

    def test_later_HTTP_failure_preserves_completed_query_and_stops_before_IDJ(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.fake_run(tmp,mode='AAA_HTTP400')
            self.assertEqual(2,len(drivers));self.assertEqual(['A32'],result['completed_tickers'])
            self.assertTrue(all(d.closed for d in drivers));self.assertTrue(result['source_stopped'])
            self.assertTrue((Path(tmp)/'state/A32/complete_query.json').exists())
            self.assertFalse((Path(tmp)/'state/IDJ').exists())

    def test_dry_check_and_missing_setup_do_not_launch_browser(self):
        for dry,ready in [(True,True),(False,False)]:
            with self.subTest(dry=dry),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.fake_run(tmp,dry=dry,ready=ready)
                self.assertEqual([],drivers)
                if dry:self.assertFalse((Path(tmp)/'state').exists())
                else:self.assertEqual(0,result['browser_launches'])

    def test_source_echo_other_ticker_or_changed_JS_fails(self):
        for document in [old.PAGE1,old.PAGE1.replace('MBS','AAA').replace('SearchKey: type','SearchKey:wrong')]:
            with self.subTest(),self.assertRaises(ValueError):p.source_contract(document,'AAA')
        self.assertEqual('Kết quả tìm kiếm với từ: AAA',p.source_contract(old.PAGE1.replace('MBS','AAA'),'AAA')['query_echo'])

    def test_exact_CLI_does_not_accept_batch_force_resume_or_other_tickers(self):
        spec=importlib.util.spec_from_file_location('three_query_cli',ROOT/'scripts/corporate_actions/collect_vsdc_three_query_browser_pilot_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,CONFIG)
            (root/CONFIG['output_base']/'run-existing').mkdir(parents=True)
            for args in [['pilot'],['pilot','--resume'],['pilot','--force'],['pilot','--batch','1'],['pilot','--tickers','MBS']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(cli,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',old.io.StringIO()),self.assertRaises(SystemExit):cli.main()
                run.assert_not_called()


class GuardTests(unittest.TestCase):
    def make(self,tmp,ticker='A32',shared=None,clock=None):
        clock=clock or old.Clock();shared=shared or p.SharedBudget(CONFIG,clock.now)
        local={**CONFIG,'ticker':ticker,'url':p.search_url(ticker),'max_seconds':90,'max_context_request_attempts':82,'max_asset_attempts':78}
        return p.Guard(local,Path(tmp),lambda:None,clock.now,shared),shared,clock

    def test_query_scope_details_and_changed_or_skipped_page_denied(self):
        for url,method,resource,body in [(p.mbs.DETAIL_URL,'GET','document',None),
            ('https://vsdc.vn/vi/ad/1','GET','document',None),
            (p.search_url('AAA'),'GET','document',None),
            (p.search_url('A32'),'POST','xhr','{"SearchKey":4,"CurrentPage":3}')]:
            with self.subTest(url=url,method=method),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);self.assertFalse(g.admit(url,method,resource,body));self.assertIsNotNone(g.stop_reason)

    def test_global_time_context_business_and_cross_browser_interval_stop(self):
        for kind in ['time','context','business','interval']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp)
                if kind=='time':c.sleep(240)
                if kind=='context':s.attempts=246
                if kind=='business':s.business=12
                if kind=='interval':s.last=c.now()
                self.assertFalse(g.admit(p.search_url('A32'),'GET','document'));self.assertIsNotNone(g.stop_reason)

    def test_HTTP_retry_after_and_TLS_privacy_gates_still_apply(self):
        for status,headers in [(400,{}),(403,{}),(429,{}),(200,{'Retry-After':'8'})]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);g.response(p.search_url('A32'),'GET',status,{**headers,'Set-Cookie':'SECRET'})
                with self.assertRaises(ValueError):g.check()
                self.assertNotIn('SECRET',(Path(tmp)/'network_ledger.jsonl').read_text(encoding='utf8'))


if __name__=='__main__':unittest.main()
