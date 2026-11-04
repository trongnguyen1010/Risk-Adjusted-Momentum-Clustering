from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import ModuleType
import unittest
from unittest.mock import MagicMock, patch
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_shared_browser_pilot as p
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old
from tests.unit.ingestion.corporate_actions import test_vsdc_supplement_plan as fixture

ROOT=old.ROOT


class FakeOwner:
    def __init__(self,timings,config,clock,mode=None):
        self.timings,self.config,self.clock,self.mode=timings,config,clock,mode
        self.launch_attempts=self.launches=self.contexts=self.closed_contexts=0;self.drivers=[];self.closed=False
    def driver(self,config,guard):
        owner=self
        class Driver(fixture.Driver):
            def __enter__(self):
                if not owner.launches:
                    with owner.timings.span('browser_launch'):owner.clock.sleep(.4)
                    owner.launch_attempts=owner.launches=1
                with owner.timings.span('context_open',config['ticker']):owner.clock.sleep(.05)
                owner.contexts+=1;self.ordinal=owner.contexts
                return super().__enter__()
            def __exit__(self,*args):
                super().__exit__(*args)
                with owner.timings.span('context_close',config['ticker']):owner.clock.sleep(.05)
                if owner.mode=='CLOSE_FAIL' and self.ticker=='AAA':raise ValueError('FRESH_CONTEXT_CLOSE_FAILED')
                owner.closed_contexts+=1
        driver=Driver(config,guard,self.clock,self.mode);self.drivers.append(driver);return driver
    def check(self):pass
    def close(self):
        with self.timings.span('browser_close'):self.clock.sleep(.1)
        self.closed=True
        if self.mode=='BROWSER_CLOSE_FAIL':raise ValueError('BROWSER_CLEANUP_FAILED')


class PilotTests(unittest.TestCase):
    def fake_run(self,tmp,mode=None,dry=False,ready=True):
        prep=Path(tmp)/'prep';prep.mkdir()
        for name,value in [('manifest.json',{'files':{}}),('protected_old_files.json',{}),
                ('reusable_detail_provider_ids.json',['999999','100002']),('known_discovery_provider_ids.json',['999999','100002']),
                ('cache_policy.json',{}),('pilot_plan.json',{}),('experiment.json',{'test_only':True})]:p.write(prep/name,value)
        clock=old.Clock();owners=[]
        def factory(timings,config):
            owner=FakeOwner(timings,config,clock,mode);owners.append(owner);return owner
        with patch.object(p,'load_preparation',return_value=(p.contract(),prep)), \
                patch.object(p,'runtime',return_value={'fixture':'runtime'}), \
                patch.object(p.mbs.old,'readiness',return_value={'ready':ready}), \
                patch.object(p.mbs.old,'protected_check',side_effect=lambda *a:clock.sleep(.01)):
            result=p.run(ROOT,Path(tmp)/'state',owner_factory=factory,clock=clock.now,dry_run=dry)
        return result,owners,clock

    def test_fixed_source_contract_and_guard_are_exact_reviewed2s(self):
        config=p.contract();p.validate(config)
        self.assertEqual({'stage','preparation','output_base','browser_lifecycle','timing_profile'},
            {k for k in config if config.get(k)!=p.baseline.contract().get(k)})
        for key,value in [('business_interval_seconds',1),('pilot_tickers',['MBS']),('max_business_requests',100),
                ('max_context_attempts',10000),('retry',True),('resume',True),('details',True),('ignore_https_errors',True),
                ('persistent_profile',True),('headless',True),('browser_lifecycle','REUSE_ONE_CONTEXT'),('timing_profile',False)]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate({**config,key:value})

    def test_one_browser_three_fresh_drivers_full_lists_and_shared2s_with_nonoverlapping_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,_=self.fake_run(tmp);owner=owners[0];state=Path(tmp)/'state'
            self.assertEqual(p.PASS,result['status'],result)
            self.assertEqual(1,result['browser_launches']);self.assertEqual(1,result['browser_launch_attempts'])
            self.assertEqual(3,result['fresh_contexts']);self.assertEqual(3,result['closed_contexts'])
            self.assertEqual(7,result['business_requests']);self.assertEqual(list(p.baseline.PILOT),result['completed_tickers'])
            self.assertEqual(108,result['unique_provider_IDs']);self.assertEqual(2,result['reusable_cached_detail_IDs'])
            self.assertTrue(owner.closed);self.assertTrue(all(d.closed for d in owner.drivers))
            self.assertEqual([1,2,3],[d.ordinal for d in owner.drivers]);calls=[]
            for ticker in p.baseline.PILOT:calls+=p.read(state/ticker/'business_requests.json')
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic']>=2 for a,b in zip(calls,calls[1:])))
            times=p.read(state/'timings.json');groups=times['categories']
            self.assertEqual(1,groups['browser_launch']['count']);self.assertEqual(3,groups['context_open']['count'])
            self.assertEqual(3,groups['context_close']['count']);self.assertGreater(groups['protected_hash']['count'],7)
            self.assertEqual(3,groups['browser_first']['count']);self.assertEqual(4,groups['browser_next']['count'])
            self.assertAlmostEqual(times['elapsed_seconds'],times['measured_exclusive_seconds']+times['other_seconds'])
            self.assertTrue(all(e['seconds_exclusive']<=e['seconds_inclusive'] for e in times['events']))
            archive=Path(tmp)/'pilot.zip';receipt=p.package(state,archive)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip());self.assertIn('timings.json',z.namelist());self.assertNotIn(receipt.name,z.namelist())
                for name,digest in json.loads(z.read('manifest.json'))['files'].items():self.assertEqual(digest,p.sha(z.read(name)))
            meta=p.read(receipt);self.assertEqual(p.sha(archive.read_bytes()),meta['ZIP_sha256'])
            self.assertEqual(p.sha((state/'manifest.json').read_bytes()),meta['state_manifest_sha256'])

    def test_same_parsed_query_IDs_titles_JS_cache_as_frozen2s_runner(self):
        from tests.unit.ingestion.corporate_actions.test_vsdc_speed2s_pilot import SpeedPilotTests as Baseline
        with tempfile.TemporaryDirectory() as tmp:
            shared=Path(tmp)/'shared';oldpath=Path(tmp)/'old';shared.mkdir();oldpath.mkdir()
            self.fake_run(shared);Baseline().fake_run(oldpath)
            for ticker,pages in [('A32',2),('AAA',3),('IDJ',2)]:
                for name in ['complete_query.json','fresh_source_contract.json',*[f'page{i}.json' for i in range(1,pages+1)]]:
                    self.assertEqual(p.read(shared/'state'/ticker/name),p.read(oldpath/'state'/ticker/name))
            # Fixtures deliberately have the same two cache hits, matching original pilot fixture cache membership.
            self.assertEqual(p.read(shared/'state/deduplicated_query_articles.json'),p.read(oldpath/'state/deduplicated_query_articles.json'))

    def test_HTTP_layout_and_context_cleanup_failure_stop_before_later_queries(self):
        for mode,drivers,completed in [('STALE',1,[]),('AAA_HTTP400',2,['A32']),('CLOSE_FAIL',2,['A32'])]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,owners,_=self.fake_run(tmp,mode)
                self.assertNotEqual(p.PASS,result['status']);self.assertTrue(result['source_stopped'])
                self.assertEqual(drivers,len(owners[0].drivers));self.assertEqual(completed,result['completed_tickers'])
                self.assertTrue(owners[0].closed);self.assertFalse(result['resumable'])
                p.package(Path(tmp)/'state',Path(tmp)/'partial.zip')

    def test_shared_browser_final_cleanup_failure_never_returns_PASS(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,_=self.fake_run(tmp,'BROWSER_CLOSE_FAIL')
            self.assertEqual('STOPPED_SHARED_BROWSER_CLEANUP_REVIEW_REQUIRED',result['status'])
            self.assertTrue(result['source_stopped']);self.assertFalse(result['resumable'])

    def test_offline_check_does_not_create_owner_or_output_and_missing_setup_has_zero_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,_=self.fake_run(tmp,dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS',result['status']);self.assertEqual([],owners)
            self.assertFalse((Path(tmp)/'state').exists())
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,_=self.fake_run(tmp,ready=False)
            self.assertEqual(0,result['browser_launches']);self.assertEqual([],owners[0].drivers)

    def test_CLI_rejects_rerun_rate_reuse_context_force_resume_flags(self):
        spec=importlib.util.spec_from_file_location('shared_cli',ROOT/'scripts/corporate_actions/collect_vsdc_shared_browser2s_pilot_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,p.contract())
            (root/p.contract()['output_base']/'run-existing').mkdir(parents=True)
            for args in [['p'],['p','--interval','1'],['p','--force'],['p','--resume'],['p','--reuse-context']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(p,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',old.io.StringIO()),self.assertRaises(SystemExit):cli.main()
                run.assert_not_called()


class LifecycleTests(unittest.TestCase):
    def harness(self,tmp):
        clock=old.Clock();timings=p.Timings(clock.now);owner=p.BrowserOwner(timings,p.contract())
        manager=MagicMock();browser=MagicMock();browser.version='MOCK_CHROME';browser.is_connected.return_value=True
        manager.chromium.launch.return_value=browser;module=ModuleType('playwright.sync_api')
        module.sync_playwright=MagicMock();module.sync_playwright.return_value.start.return_value=manager
        shared=p.baseline.SharedBudget(p.contract(),clock.now);guards=[]
        for ticker in p.baseline.PILOT:
            folder=Path(tmp)/ticker;folder.mkdir()
            config={**p.contract(),'ticker':ticker,'url':p.baseline.search_url(ticker),'max_seconds':90,
                'max_context_request_attempts':82,'max_asset_attempts':78}
            guards.append(p.baseline.Guard(config,folder,lambda:None,clock.now,shared))
        return owner,module,manager,browser,guards

    def test_real_owner_driver_launch_once_fresh_contexts_closed_between_tickers_no_state_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            owner,module,manager,browser,guards=self.harness(tmp);contexts=[MagicMock() for _ in range(3)]
            browser.new_context.side_effect=contexts
            with patch.dict('sys.modules',{'playwright.sync_api':module}):
                for i,guard in enumerate(guards):
                    with owner.driver(guard.config,guard) as driver:
                        self.assertEqual(i+1,driver.ordinal);self.assertIs(driver.context,contexts[i])
                        self.assertIsNone(driver.manager)
                    contexts[i].close.assert_called_once();browser.close.assert_not_called();manager.stop.assert_not_called()
                    contexts[i].route.assert_called_once();contexts[i].route_web_socket.assert_called_once()
                owner.close()
            module.sync_playwright.return_value.start.assert_called_once();manager.chromium.launch.assert_called_once()
            self.assertEqual({'channel','headless','timeout'},set(manager.chromium.launch.call_args.kwargs))
            self.assertEqual('chrome',manager.chromium.launch.call_args.kwargs['channel'])
            self.assertFalse(manager.chromium.launch.call_args.kwargs['headless'])
            self.assertEqual(3,browser.new_context.call_count)
            for call in browser.new_context.call_args_list:self.assertEqual({'ignore_https_errors':False,'accept_downloads':False,'service_workers':'block'},call.kwargs)
            browser.close.assert_called_once();manager.stop.assert_called_once()
            self.assertEqual(1,owner.launches);self.assertEqual(3,owner.contexts);self.assertEqual(3,owner.closed_contexts)

    def test_context_creation_failure_closes_browser_without_retry_or_extra_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            owner,module,manager,browser,guards=self.harness(tmp);browser.new_context.side_effect=ValueError('CONTEXT_FAILED')
            with patch.dict('sys.modules',{'playwright.sync_api':module}):
                with self.assertRaises(ValueError):
                    with owner.driver(guards[0].config,guards[0]):pass
                owner.close()
            manager.chromium.launch.assert_called_once();browser.new_context.assert_called_once();browser.close.assert_called_once();manager.stop.assert_called_once()

    def test_launch_failure_never_retries_and_stops_Playwright_manager(self):
        with tempfile.TemporaryDirectory() as tmp:
            owner,module,manager,browser,guards=self.harness(tmp)
            manager.chromium.launch.side_effect=ValueError('LAUNCH_FAILED')
            with patch.dict('sys.modules',{'playwright.sync_api':module}):
                with self.assertRaises(ValueError):
                    with owner.driver(guards[0].config,guards[0]):pass
                with self.assertRaisesRegex(ValueError,'NO_BROWSER_RELAUNCH'):
                    with owner.driver(guards[1].config,guards[1]):pass
                owner.close()
            manager.chromium.launch.assert_called_once();manager.stop.assert_called_once()
            browser.new_context.assert_not_called();self.assertEqual(0,owner.launches)

    def test_disconnection_and_context_close_failure_stop_reuse_without_relaunch(self):
        for mode in ['disconnect','close_fail']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                owner,module,manager,browser,guards=self.harness(tmp);context=browser.new_context.return_value
                if mode=='close_fail':context.close.side_effect=ValueError('CLOSE_FAILED')
                with patch.dict('sys.modules',{'playwright.sync_api':module}):
                    if mode=='close_fail':
                        with self.assertRaises(ValueError):
                            with owner.driver(guards[0].config,guards[0]):pass
                    else:
                        with owner.driver(guards[0].config,guards[0]):pass
                        owner.disconnected()
                    with self.assertRaises(ValueError):
                        with owner.driver(guards[1].config,guards[1]):pass
                    owner.close()
                manager.chromium.launch.assert_called_once();browser.new_context.assert_called_once()

    def test_new_context_has_same_network_access_and_response_failure_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            owner,module,manager,browser,guards=self.harness(tmp);guard=guards[0]
            with patch.dict('sys.modules',{'playwright.sync_api':module}):
                with owner.driver(guard.config,guard) as driver:
                    request=MagicMock();request.url=p.mbs.DETAIL_URL;request.method='GET';request.resource_type='document'
                    request.post_data=None;request.redirected_from=None;route=MagicMock();route.request=request
                    driver._route(route);route.abort.assert_called_once();route.continue_.assert_not_called()
                    self.assertIsNotNone(guard.stop_reason)
                owner.close()
        for status in [301,403,429,500]:
            with tempfile.TemporaryDirectory() as tmp:
                owner,module,manager,browser,guards=self.harness(tmp);guard=guards[0]
                guard.response(guard.config['url'],'GET',status,{})
                with self.assertRaises(ValueError):guard.check()


class TimingTests(unittest.TestCase):
    def test_nested_hash_work_subtracted_from_parent_and_failed_span_recorded(self):
        clock=old.Clock();timer=p.Timings(clock.now)
        with timer.span('browser_first','AAA'):
            clock.sleep(1)
            with timer.span('protected_hash'):clock.sleep(2)
            clock.sleep(3)
        with self.assertRaises(ValueError):
            with timer.span('archive_parse'):clock.sleep(.5);raise ValueError('FAIL')
        row=timer.snapshot();self.assertEqual(6.5,row['elapsed_seconds']);self.assertEqual(6.5,row['measured_exclusive_seconds'])
        self.assertEqual(6,row['categories']['browser_first']['seconds_inclusive'])
        self.assertEqual(4,row['categories']['browser_first']['seconds_exclusive'])
        self.assertEqual(.5,row['categories']['archive_parse']['seconds_exclusive'])
        self.assertFalse(row['packaging_included'])


if __name__=='__main__':unittest.main()
