from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_speed4s_pilot as p
from tests.unit.ingestion.corporate_actions import test_vsdc_supplement_plan as prior
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old

ROOT=old.ROOT;CONFIG=p.read(ROOT/p.CONFIG)


class SpeedPilotTests(unittest.TestCase):
    def fake_run(self,tmp,*,dry=False,ready=True,mode=None):
        prep=Path(tmp)/'prep';prep.mkdir()
        for name,value in [('protected_old_files.json',{}),('reusable_detail_provider_ids.json',['999999','100002','187243']),
                ('pilot_plan.json',{}),('cache_policy.json',{}),('experiment.json',{'test_only':True}),('manifest.json',{'files':{}})]:
            p.write(prep/name,value)
        clock=old.Clock();drivers=[]
        def factory(config,guard):
            driver=prior.Driver(config,guard,clock,mode);drivers.append(driver);return driver
        with patch.object(p,'load_preparation',return_value=(deepcopy(CONFIG),prep)), \
                patch.object(p.mbs.old,'readiness',return_value={'ready':ready}):
            result=p.run(ROOT,Path(tmp)/'state',dry_run=dry,driver_factory=factory,clock=clock.now)
        return result,drivers

    def test_contract_only_changes_four_preparation_fields_and_interval(self):
        p.validate(CONFIG)
        difference={k for k in CONFIG if CONFIG[k]!=p.base.contract()[k]}
        self.assertEqual({'stage','output_base','preparation','business_interval_seconds'},difference)
        for key,value in [('business_interval_seconds',2),('business_interval_seconds',8),
                ('pilot_tickers',['MBS']),('max_business_requests',100),('details',True),('bulk_enabled',True),
                ('retry',True),('resume',True),('ignore_https_errors',True),('headless',True),
                ('persistent_profile',True),('user_agent','spoof')]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):p.validate({**CONFIG,key:value})

    def test_same_three_queries_at_exact_four_seconds_across_ticker_transitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.fake_run(tmp)
            self.assertEqual('PASS_FOUR_SECOND_PILOT_REVIEW_REQUIRED',result['status'])
            self.assertEqual(4,result['business_interval_seconds']);self.assertEqual(list(p.PILOT),result['completed_tickers'])
            self.assertEqual(7,result['business_requests']);self.assertEqual(3,result['browser_launches'])
            self.assertEqual(0,result['detail_requests']);self.assertFalse(result['resumable']);self.assertFalse(result['bulk_collection_ready'])
            self.assertTrue(all(d.closed for d in drivers))
            calls=[]
            for ticker in p.PILOT:calls.extend(p.read(Path(tmp)/'state'/ticker/'business_requests.json'))
            intervals=[b['at_monotonic']-a['at_monotonic'] for a,b in zip(calls,calls[1:])]
            self.assertEqual([4]*6,intervals);self.assertEqual(24,result['elapsed_seconds'])
            self.assertEqual(108,result['unique_provider_IDs']);self.assertEqual(2,result['reusable_cached_detail_IDs'])
            merged=p.read(Path(tmp)/'state/deduplicated_query_articles.json')
            common=next(r for r in merged if r['provider_article_id']=='999999')
            self.assertEqual(list(p.PILOT),common['query_tickers'])
            self.assertTrue(all(not r['detail_fetch_authorized'] and not r['event_identity_verified'] for r in merged))
            archive=Path(tmp)/'speed.zip';p.seal(Path(tmp)/'state',archive,artifact_type=p.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip());self.assertIn('experiment.json',z.namelist())
                manifest=json.loads(z.read('manifest.json'));self.assertEqual(p.TYPE,manifest['artifact_type'])
                for name,digest in manifest['files'].items():self.assertEqual(digest,p.sha(z.read(name)))

    def test_HTTP_and_stale_layout_errors_stop_no_auto_fallback_or_retry(self):
        for mode,browsers,completed in [('STALE',1,[]),('AAA_HTTP400',2,['A32'])]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.fake_run(tmp,mode=mode)
                self.assertTrue(result['source_stopped']);self.assertEqual(browsers,len(drivers))
                self.assertEqual(completed,result['completed_tickers']);self.assertTrue(all(d.closed for d in drivers))
                self.assertFalse(result['resumable']);self.assertEqual(0,result['detail_requests'])
                p.seal(Path(tmp)/'state',Path(tmp)/'partial.zip',artifact_type=p.TYPE)

    def test_offline_check_and_missing_setup_do_not_open_browser(self):
        for dry,ready in [(True,True),(False,False)]:
            with self.subTest(dry=dry),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.fake_run(tmp,dry=dry,ready=ready)
                self.assertEqual([],drivers)
                if dry:self.assertFalse((Path(tmp)/'state').exists())
                else:self.assertEqual(0,result['browser_launches'])

    def test_CLI_has_new_rerun_guard_and_no_rate_override_or_fallback_flags(self):
        spec=importlib.util.spec_from_file_location('speed_cli',ROOT/'scripts/corporate_actions/collect_vsdc_three_query_speed4s_pilot_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,CONFIG)
            (root/CONFIG['output_base']/'run-existing').mkdir(parents=True)
            for args in [['pilot'],['pilot','--interval','2'],['pilot','--resume'],['pilot','--force'],['pilot','--fallback','8']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(cli,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',old.io.StringIO()),self.assertRaises(SystemExit):cli.main()
                run.assert_not_called()


class SpeedGuardTests(unittest.TestCase):
    def make(self,tmp,ticker='A32',clock=None,shared=None):
        clock=clock or old.Clock();shared=shared or p.SharedBudget(CONFIG,clock.now)
        config={**CONFIG,'ticker':ticker,'url':p.search_url(ticker),'max_seconds':90,
                'max_context_request_attempts':82,'max_asset_attempts':78}
        return p.Guard(config,Path(tmp),lambda:None,clock.now,shared),shared,clock

    def test_four_seconds_allowed_but_earlier_rejected_with_no_hidden_eight_second_gate(self):
        for delay,allowed in [(0,False),(3,False),(3.999,False),(4,True),(5,True),(8,True)]:
            with self.subTest(delay=delay),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);self.assertTrue(g.admit(p.search_url('A32'),'GET','document'));c.sleep(delay)
                self.assertEqual(allowed,g.admit(p.search_url('A32'),'POST','xhr','{"SearchKey":4,"CurrentPage":2}'))
                if not allowed:self.assertEqual(1,s.business)

    def test_interval_is_shared_across_fresh_browsers(self):
        for delay,allowed in [(3.999,False),(4,True)]:
            with self.subTest(delay=delay),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp);(folder/'A').mkdir();(folder/'B').mkdir()
                first,shared,c=self.make(folder/'A');self.assertTrue(first.admit(p.search_url('A32'),'GET','document'))
                c.sleep(delay);second,_,_=self.make(folder/'B','AAA',c,shared)
                self.assertEqual(allowed,second.admit(p.search_url('AAA'),'GET','document'))

    def test_scope_page_sequence_detail_redirect_and_old_file_gates_unchanged(self):
        cases=[(p.mbs.DETAIL_URL,'GET','document',None,False),
               (p.search_url('AAA'),'GET','document',None,False),
               (p.search_url('A32'),'GET','document',None,True),
               (p.search_url('A32'),'POST','xhr','{"SearchKey":4,"CurrentPage":3}',False)]
        for args in cases:
            with self.subTest(args=args[:2]),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);self.assertFalse(g.admit(*args));self.assertIsNotNone(g.stop_reason)
        with tempfile.TemporaryDirectory() as tmp:
            g,s,c=self.make(tmp)
            def changed():raise ValueError('OLD_STATE_CHANGED')
            g.check_old=changed
            self.assertFalse(g.admit(p.search_url('A32'),'GET','document'))

    def test_all_global_and_local_request_asset_time_budgets_unchanged(self):
        for mode in ['global_context','global_business','local_context','local_asset','global_time','local_time']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp)
                if mode=='global_context':s.attempts=246
                if mode=='global_business':s.business=12
                if mode=='local_context':g.attempts=82
                if mode=='local_asset':g.assets=78
                if mode=='global_time':c.sleep(240)
                if mode=='local_time':c.sleep(90)
                url='https://vsdc.vn/assets/x.css' if mode=='local_asset' else p.search_url('A32')
                self.assertFalse(g.admit(url,'GET','stylesheet' if mode=='local_asset' else 'document'))
                self.assertIsNotNone(g.stop_reason)

    def test_source_errors_access_challenge_retry_after_TLS_privacy_stop(self):
        for status,headers in [(s,{}) for s in [301,400,401,403,429,500]]+[(200,{'Retry-After':'8'})]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);g.response(p.search_url('A32'),'GET',status,{**headers,'Set-Cookie':'SECRET'})
                with self.assertRaises(ValueError):g.check()
                self.assertNotIn('SECRET',(Path(tmp)/'network_ledger.jsonl').read_text(encoding='utf8'))
        for failure in ['BROWSER_REQUEST_FAILED_TLS_OR_TRANSPORT','BROWSER_CHALLENGE_STOP']:
            with tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);g.fail(failure)
                self.assertFalse(g.admit(p.search_url('A32'),'GET','document'))


if __name__=='__main__':unittest.main()
