import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_headless_progress_pilot as p
from tests.unit.ingestion.corporate_actions import test_vsdc_shared_browser_pilot as previous

ROOT=previous.ROOT


class PilotTests(unittest.TestCase):
    def fake_run(self,tmp,mode=None,dry=False,ready=True):
        prep=Path(tmp)/'prep';prep.mkdir()
        for name,value in [('manifest.json',{'files':{}}),('protected_old_files.json',{}),
                ('reusable_detail_provider_ids.json',['999999','100002']),('known_discovery_provider_ids.json',['999999','100002']),
                ('cache_policy.json',{}),('pilot_plan.json',{}),('experiment.json',{'test_only':True})]:p.write(prep/name,value)
        clock=previous.old.Clock();owners=[];lines=[]
        def factory(timings,config):
            owner=previous.FakeOwner(timings,config,clock,mode);owners.append(owner);create=owner.driver
            def driver(local,guard):
                value=create(local,guard);snapshot=value.snapshot
                def wrapped(number):
                    if mode=='HTTP429':
                        guard.response(local['url'],'GET',429,{'retry-after':'10'});guard.check()
                    if mode=='CANCEL':raise KeyboardInterrupt()
                    data=snapshot(number)
                    if mode=='CHALLENGE':data['fragment']='<div id="divGlSearchArticles">verify you are human</div>'
                    return data
                value.snapshot=wrapped;return value
            owner.driver=driver;return owner
        with patch.object(p,'load_preparation',return_value=(p.contract(),prep)), \
                patch.object(p,'runtime',return_value={'fixture':'runtime'}), \
                patch.object(p.mbs.old,'readiness',return_value={'ready':ready}), \
                patch.object(p.mbs.old,'protected_check',side_effect=lambda *a:clock.sleep(.01)):
            result=p.run(ROOT,Path(tmp)/'state',owner_factory=factory,clock=clock.now,dry_run=dry,emit=lambda line,**k:lines.append(line))
        return result,owners,lines

    def test_fixed_headless_progress_contract_keeps_original_hash_and2s_source_caps(self):
        config=p.contract();p.validate(config)
        self.assertEqual({'stage','preparation','output_base','headless','progress','hash_checker'},
            {k for k in config if config.get(k)!=p.previous.contract().get(k)})
        self.assertEqual('ORIGINAL_FULL_SHA256_EVERY_CHECK',config['hash_checker'])
        self.assertIs(p.baseline.Guard,p.previous.baseline.Guard)
        for key,value in [('headless',False),('business_interval_seconds',1),('retry',True),('resume',True),
                ('details',True),('max_business_requests',100),('max_context_attempts',10000),
                ('ignore_https_errors',True),('persistent_profile',True),('hash_checker','MTIME_CACHE'),('user_agent','spoof')]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate({**config,key:value})

    def test_readable_progress_increments_only_on_validated_query_with_ETA_and_sealed_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,lines=self.fake_run(tmp);state=Path(tmp)/'state'
            self.assertEqual(p.PASS,result['status'],result);self.assertTrue(result['headless'])
            self.assertEqual(3,result['progress_completed_queries']);self.assertEqual(3,result['progress_total_queries'])
            self.assertEqual(7,result['business_requests']);self.assertEqual(1,result['browser_launches'])
            self.assertEqual(3,result['fresh_contexts']);self.assertEqual(3,result['closed_contexts']);self.assertTrue(owners[0].closed)
            rows=p.mbs.old.rows(state/'progress.jsonl');self.assertEqual(22,len(rows));self.assertEqual(22,len(lines))
            self.assertEqual(lines,(state/'progress.log').read_text(encoding='utf8').splitlines())
            self.assertEqual('START',rows[0]['event']);self.assertEqual('FINAL',rows[-1]['event']);self.assertEqual(p.PASS,rows[-1]['status'])
            done=[r for r in rows if r['event']=='QUERY_VALIDATED']
            self.assertEqual(['A32','AAA','IDJ'],[r['ticker'] for r in done]);self.assertEqual([1,2,3],[r['completed_queries'] for r in done])
            completed=0
            for row in rows:
                if row['event']=='QUERY_VALIDATED':completed+=1
                self.assertEqual(completed,row['completed_queries']);self.assertEqual(3,row['total_queries'])
                self.assertEqual(3-completed,row['remaining_queries']);self.assertAlmostEqual(100*completed/3,row['percent'])
                self.assertEqual(1,row['batch_index']);self.assertEqual(1,row['total_batches'])
                if completed==0:self.assertIsNone(row['ETA_seconds'])
                else:self.assertGreaterEqual(row['ETA_seconds'],0)
            self.assertEqual(100,rows[-1]['percent']);self.assertEqual(0,rows[-1]['ETA_seconds'])
            pages=[r for r in rows if r['event']=='PAGE_COMPLETE'];self.assertEqual(7,len(pages))
            self.assertTrue(any('1/3 mã' in line and 'ETA tạm tính' in line for line in lines))
            self.assertTrue(any('Trang 3/3' in line for line in lines))
            calls=[]
            for ticker in p.baseline.PILOT:
                calls+=p.read(state/ticker/'business_requests.json');self.assertTrue(p.read(state/ticker/'browser.json')['headless'])
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic']>=2 for a,b in zip(calls,calls[1:])))
            times=p.read(state/'timings.json');self.assertEqual(22,times['categories']['progress_ui']['count'])
            self.assertEqual(15,times['categories']['protected_hash']['count'])
            self.assertAlmostEqual(times['elapsed_seconds'],times['measured_exclusive_seconds']+times['other_seconds'])
            archive=Path(tmp)/'pilot.zip';receipt=p.package(state,archive)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip());self.assertIn('progress.log',z.namelist());self.assertIn('progress.jsonl',z.namelist())
                manifest=p.read(state/'manifest.json');self.assertEqual(p.TYPE,manifest['artifact_type'])
                for name,digest in manifest['files'].items():self.assertEqual(digest,p.sha(z.read(name)))
            self.assertEqual(p.sha(archive.read_bytes()),p.read(receipt)['ZIP_sha256'])

    def test_same_parsed_data_JS_cache_and_complete_lists_as_headed_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            one=Path(tmp)/'one';two=Path(tmp)/'two';one.mkdir();two.mkdir()
            self.fake_run(one);previous.PilotTests().fake_run(two)
            for ticker,pages in [('A32',2),('AAA',3),('IDJ',2)]:
                for name in ['complete_query.json','fresh_source_contract.json',*[f'page{i}.json' for i in range(1,pages+1)]]:
                    self.assertEqual(p.read(one/'state'/ticker/name),p.read(two/'state'/ticker/name))
            self.assertEqual(p.read(one/'state/deduplicated_query_articles.json'),p.read(two/'state/deduplicated_query_articles.json'))

    def test_HTTP429_400_layout_challenge_failure_does_not_increment_failed_query_or_continue(self):
        for mode,completed,drivers in [('HTTP429',0,1),('AAA_HTTP400',1,2),('STALE',0,1),('CHALLENGE',0,1),('CLOSE_FAIL',1,2)]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,owners,lines=self.fake_run(tmp,mode);state=Path(tmp)/'state'
                self.assertNotEqual(p.PASS,result['status']);self.assertTrue(result['source_stopped'])
                self.assertEqual(completed,result['progress_completed_queries']);self.assertEqual(drivers,len(owners[0].drivers))
                self.assertTrue(owners[0].closed);self.assertFalse(result['resumable'])
                rows=p.mbs.old.rows(state/'progress.jsonl')
                self.assertEqual(completed,rows[-1]['completed_queries']);self.assertEqual(result['status'],rows[-1]['status'])
                self.assertEqual(completed,len([r for r in rows if r['event']=='QUERY_VALIDATED']))
                self.assertTrue(all(p.PASS not in line for line in lines))
                p.package(state,Path(tmp)/'partial.zip')

    def test_final_browser_cleanup_failure_is_STOP_even_if_three_queries_reached100percent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,_,lines=self.fake_run(tmp,'BROWSER_CLOSE_FAIL')
            self.assertNotEqual(p.PASS,result['status']);self.assertTrue(result['source_stopped'])
            final=p.mbs.old.rows(Path(tmp)/'state/progress.jsonl')[-1]
            self.assertEqual(3,final['completed_queries']);self.assertEqual(100,final['percent'])
            self.assertEqual(result['status'],final['status']);self.assertNotEqual(p.PASS,final['status'])
            self.assertIn('STOPPED',lines[-1])

    def test_interrupt_preserves_partial_progress_without_resume_or_false_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,_=self.fake_run(tmp,'CANCEL')
            self.assertEqual('CANCELLED_REVIEW_REQUIRED',result['status']);self.assertFalse(result['resumable'])
            self.assertEqual(0,result['progress_completed_queries']);self.assertTrue(owners[0].closed)
            self.assertEqual('CANCELLED_REVIEW_REQUIRED',p.mbs.old.rows(Path(tmp)/'state/progress.jsonl')[-1]['status'])

    def test_offline_check_creates_no_browser_owner_or_progress_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,lines=self.fake_run(tmp,dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS',result['status']);self.assertTrue(result['headless'])
            self.assertFalse((Path(tmp)/'state').exists());self.assertEqual([],owners);self.assertEqual([],lines)

    def test_CLI_rejects_rerun_headed_fallback_rate_identity_force_or_resume_flags(self):
        spec=importlib.util.spec_from_file_location('headless_cli',ROOT/'scripts/corporate_actions/collect_vsdc_headless_progress2s_pilot_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,p.contract())
            (root/p.contract()['output_base']/'run-existing').mkdir(parents=True)
            for args in [['p'],['p','--headed'],['p','--fallback'],['p','--interval','1'],['p','--user-agent','spoof'],['p','--force'],['p','--resume']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(p,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',previous.old.io.StringIO()),self.assertRaises(SystemExit):cli.main()
                run.assert_not_called()


class HeadlessLifecycleTests(unittest.TestCase):
    def test_real_owner_launches_only_headless_chrome_and_reuses_three_clean_contexts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,module,manager,browser,guards=previous.LifecycleTests().harness(tmp)
            owner=p.HeadlessOwner(p.Timings(previous.old.Clock().now),p.contract())
            with patch.dict('sys.modules',{'playwright.sync_api':module}):
                for guard in guards:
                    with owner.driver({**guard.config,'headless':True},guard):pass
                owner.close()
            manager.chromium.launch.assert_called_once()
            self.assertEqual({'channel','headless','timeout'},set(manager.chromium.launch.call_args.kwargs))
            self.assertEqual('chrome',manager.chromium.launch.call_args.kwargs['channel']);self.assertTrue(manager.chromium.launch.call_args.kwargs['headless'])
            self.assertEqual(3,browser.new_context.call_count)
            for call in browser.new_context.call_args_list:
                self.assertEqual({'ignore_https_errors':False,'accept_downloads':False,'service_workers':'block'},call.kwargs)
            self.assertEqual(1,owner.launches);self.assertEqual(3,owner.closed_contexts)

    def test_headless_launch_failure_never_falls_back_to_visible_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,module,manager,browser,guards=previous.LifecycleTests().harness(tmp)
            owner=p.HeadlessOwner(p.Timings(previous.old.Clock().now),p.contract())
            manager.chromium.launch.side_effect=ValueError('HEADLESS_FAILED')
            with patch.dict('sys.modules',{'playwright.sync_api':module}):
                for guard in guards[:2]:
                    with self.assertRaises(ValueError):
                        with owner.driver(guard.config,guard):pass
                owner.close()
            manager.chromium.launch.assert_called_once();self.assertTrue(manager.chromium.launch.call_args.kwargs['headless'])
            browser.new_context.assert_not_called();manager.stop.assert_called_once()


class ProgressTests(unittest.TestCase):
    def test_progress_query_order_ETA_and_duration_formatting_without_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock=previous.old.Clock();lines=[];timer=p.Timings(clock.now)
            progress=p.Progress(tmp,['A32','AAA','IDJ'],timer,clock.now,emit=lambda line,**k:lines.append(line))
            progress.record('START');clock.sleep(10);progress.begin('A32');progress.page('A32',1,2)
            self.assertEqual(0,progress.completed);progress.done('A32')
            last=p.mbs.old.rows(Path(tmp)/'progress.jsonl')[-1]
            self.assertEqual(1,last['completed_queries']);self.assertEqual(20,last['ETA_seconds'])
            with self.assertRaises(ValueError):progress.begin('IDJ')
            with self.assertRaises(ValueError):progress.finish(p.PASS)
            self.assertEqual('01:01:01',p.duration(3661));self.assertEqual('00:00:00',p.duration(-1))

    def test_empty_duplicate_scope_or_wrong_completion_cannot_fake_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            timer=p.Timings()
            for tickers in ([],['A32','A32']):
                with self.assertRaises(ValueError):p.Progress(tmp,tickers,timer)
            progress=p.Progress(tmp,['A32'],timer,emit=lambda *a,**k:None)
            with self.assertRaises(ValueError):progress.done('A32')
            progress.begin('A32')
            with self.assertRaises(ValueError):progress.page('AAA',1)
            with self.assertRaises(ValueError):progress.done('AAA')
            self.assertEqual(0,progress.completed)


if __name__=='__main__':unittest.main()
