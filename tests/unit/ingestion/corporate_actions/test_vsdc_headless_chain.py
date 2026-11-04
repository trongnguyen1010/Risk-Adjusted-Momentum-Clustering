from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions import vsdc_headless_chain as p
from tests.unit.ingestion.corporate_actions import test_vsdc_remaining_chain as old
from tests.unit.ingestion.corporate_actions import test_vsdc_shared_browser_pilot as lifecycle

ROOT=old.ROOT
SELECTED=[{'batch_id':'proposed-002','tickers':['A32','AAA'],'estimated_list_requests':5},
          {'batch_id':'proposed-003','tickers':['IDJ'],'estimated_list_requests':2}]


class ResumeTests(unittest.TestCase):
    def setup(self,tmp,selected=SELECTED):
        project=Path(tmp);prep=project/'prep';prep.mkdir()
        for name,value in [('manifest.json',{'files':{}}),('protected_old_files.json',{}),
                ('reusable_detail_provider_ids.json',['100002']),('known_discovery_provider_ids.json',['100002']),
                ('cache_policy.json',{}),('query_inventory_before_chain.json',[]),('selected_batches.json',selected)]:
            p.write(prep/name,value)
        return project,prep

    def invoke(self,project,prep,number,*,trigger=None,mode=None,start=1000,dry=False,seed=None):
        output=project/p.contract()['output_base']/f'run-{number:03}'/'state'
        pause=p.Pause(output.parent/'PAUSE_REQUEST');clock=old.old.Clock();clock.sleep(start-clock.now());drivers=[]
        def factory(config,guard):
            driver=old.Driver(config,guard,clock,mode);drivers.append(driver)
            original=driver.snapshot
            def snapshot(n):
                try:data=original(n)
                except ValueError:
                    if trigger==(config['ticker'],n):pause.request()
                    raise
                if trigger==(config['ticker'],n):pause.request()
                return data
            driver.snapshot=snapshot
            return driver
        with ExitStack() as stack:
            stack.enter_context(patch.object(p,'load_preparation',return_value=(p.contract(),prep)))
            stack.enter_context(patch.object(p,'runtime',return_value={'outer':'frozen'}))
            stack.enter_context(patch.object(p.base,'runtime',return_value={'inner':'frozen'}))
            stack.enter_context(patch.object(p.base.mbs.old,'readiness',return_value={'ready':True}))
            if seed is not None:stack.enter_context(patch.object(p,'history',return_value=seed))
            if mode=='VALIDATION_FAIL':
                original_validate=p.base.validate_batch
                def validate(*args):
                    if args[0].parent.name=='0002':raise ValueError('TEST_VALIDATION_FAILURE')
                    return original_validate(*args)
                stack.enter_context(patch.object(p.base,'validate_batch',side_effect=validate))
            result=p.run(project,output,pause=pause,driver_factory=factory,clock=clock.now,emit=lambda *a,**k:None,dry_run=dry)
            if not dry:p.seal_run(output)
        return result,drivers,output

    def test_pause_mid_query_then_restart_page1_without_stitching_and_keep_cumulative_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp)
            first,drivers,state=self.invoke(root,prep,1,trigger=('A32',1))
            self.assertEqual(p.PAUSED,first['status'],first);self.assertTrue(first['resumable'])
            self.assertEqual(0,first['completed_query_count']);self.assertEqual(1,first['totals']['business'])
            digest=p.sha((state/'manifest.json').read_bytes())
            second,drivers2,state2=self.invoke(root,prep,2,start=100000)
            self.assertEqual(p.COMPLETE,second['status'],second)
            self.assertEqual(['A32','AAA','IDJ'],[d.ticker for d in drivers2])
            self.assertEqual(8,second['totals']['business']);self.assertEqual(7,second['source_requests_this_segment'])
            self.assertLess(second['totals']['active_seconds'],100)
            self.assertEqual(digest,p.sha((state/'manifest.json').read_bytes()))
            calls=p.read(state2/'queries/0001/state/A32/business_requests.json')
            self.assertEqual(['GET','POST'],[r['method'] for r in calls])
            self.assertEqual(2,p.read(state2/'queries/0001/state/result.json')['business_requests'])
            self.assertTrue(all(d.closed for d in drivers+drivers2))

    def test_complete_query_in_partial_batch_is_reused_and_batch_completes_after_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp)
            first,_,state=self.invoke(root,prep,1,trigger=('AAA',1))
            self.assertEqual(p.PAUSED,first['status']);self.assertEqual(1,first['completed_query_count'])
            self.assertEqual([],first['validated_batch_ids'])
            original=p.hashes(state/'queries/0001')
            second,drivers,state2=self.invoke(root,prep,2)
            self.assertEqual(p.COMPLETE,second['status'],second)
            self.assertEqual(['AAA','IDJ'],[d.ticker for d in drivers])
            self.assertEqual(original,p.hashes(state2/'queries/0001'))
            self.assertEqual(['proposed-002','proposed-003'],second['validated_batch_ids'])
            self.assertEqual(8,second['totals']['business'])
            merged=p.read(state2/'known_discovery_after_validated_queries.json')
            self.assertEqual(108,len(merged));self.assertEqual(1,second['reusable_detail_IDs_unchanged'])

    def test_multiple_pauses_preserve_order_skip_completed_and_keep_all_original_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp)
            a,_,s1=self.invoke(root,prep,1,trigger=('AAA',1))
            b,ds,s2=self.invoke(root,prep,2,trigger=('IDJ',1))
            self.assertEqual(p.PAUSED,b['status'],b);self.assertEqual(2,b['completed_query_count'])
            self.assertEqual(['AAA','IDJ'],[d.ticker for d in ds])
            c,ds,s3=self.invoke(root,prep,3)
            self.assertEqual(p.COMPLETE,c['status'],c);self.assertEqual(['IDJ'],[d.ticker for d in ds])
            self.assertEqual(9,c['totals']['business'])
            self.assertEqual(p.hashes(s1/'queries/0001'),p.hashes(s3/'queries/0001'))
            self.assertEqual(p.hashes(s2/'queries/0002'),p.hashes(s3/'queries/0002'))

    def test_source_error_is_not_resumable_and_same_command_cannot_retry_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp)
            result,drivers,state=self.invoke(root,prep,1,mode='AAA_HTTP400')
            self.assertEqual(p.STOPPED,result['status']);self.assertFalse(result['resumable'])
            self.assertEqual(1,result['completed_query_count']);self.assertEqual(2,len(drivers))
            with self.assertRaisesRegex(ValueError,'ONLY_USER_PAUSED_RUN'):self.invoke(root,prep,2)

    def test_pause_coincident_with_source_error_does_not_unlock_continuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp)
            result,_,state=self.invoke(root,prep,1,trigger=('AAA',1),mode='AAA_HTTP400')
            self.assertEqual(p.STOPPED,result['status']);self.assertFalse(result['resumable'])
            with self.assertRaisesRegex(ValueError,'ONLY_USER_PAUSED_RUN'):self.invoke(root,prep,2)

    def test_validation_failure_still_accounts_all_requests_before_stopping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp)
            result,drivers,state=self.invoke(root,prep,1,mode='VALIDATION_FAIL')
            self.assertEqual(p.STOPPED,result['status']);self.assertEqual(1,result['completed_query_count'])
            self.assertEqual(5,result['totals']['business']);self.assertEqual(5,result['source_requests_this_segment'])
            self.assertEqual(2,len(drivers));self.assertFalse(result['resumable'])

    def test_semantic_tampering_resealed_query_and_segment_cannot_be_continued(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp)
            result,_,state=self.invoke(root,prep,1,trigger=('AAA',1))
            folder=state/'queries/0001';obj=p.read(folder/'state/A32/page1.json');obj['page']=9
            (folder/'state/A32/page1.json').write_text(json.dumps(obj),encoding='utf8')
            (folder/'state/manifest.json').unlink();(folder/'query.zip').unlink()
            p.base.seal(folder/'state',folder/'query.zip',artifact_type=p.base.BATCH_TYPE)
            (state/'manifest.json').unlink();(state.parent/'delta-vsdc-headless54.zip').unlink();p.seal_run(state)
            with self.assertRaisesRegex(ValueError,'REPARSE'):self.invoke(root,prep,2)

    def test_unsealed_crash_and_changed_zip_are_blocked_before_browser(self):
        for mode in ['unsealed','zip']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,prep=self.setup(tmp);_,_,state=self.invoke(root,prep,1,trigger=('A32',1))
                if mode=='unsealed':(state/'manifest.json').unlink()
                else:(state.parent/'delta-vsdc-headless54.zip').write_bytes(b'broken')
                with self.assertRaises(Exception):self.invoke(root,prep,2)

    def test_cumulative_global_and_batch_request_budgets_are_not_reset(self):
        for mode in ['global','batch']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,prep=self.setup(tmp);totals=p.initial_totals(SELECTED)
                totals['business']=5399 if mode=='global' else 99
                totals['batches']['proposed-002']['business']=99
                seed={'runs':[],'completed':[],'known':{'100002'},'reusable':{'100002'},'totals':totals,'predecessor':None}
                result,drivers,state=self.invoke(root,prep,1,seed=seed)
                self.assertEqual(p.STOPPED,result['status']);self.assertFalse(result['resumable'])
                self.assertEqual(1,len(drivers));self.assertEqual(1,result['source_requests_this_segment'])
                self.assertEqual(100,result['totals']['batches']['proposed-002']['business'])

    def test_cumulative_active_time_budget_is_not_reset(self):
        for mode in ['global','batch']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,prep=self.setup(tmp);totals=p.initial_totals(SELECTED)
                if mode=='global':totals['active_seconds']=28799
                else:totals['batches']['proposed-002']['active_seconds']=1199
                seed={'runs':[],'completed':[],'known':{'100002'},'reusable':{'100002'},'totals':totals,'predecessor':None}
                result,drivers,state=self.invoke(root,prep,1,seed=seed)
                self.assertEqual(p.STOPPED,result['status']);self.assertFalse(result['resumable'])
                self.assertEqual(0,result['source_requests_this_segment'])

    def test_54_batches_still_complete_in_one_uninterrupted_invocation(self):
        selected=[{'batch_id':bid,'tickers':['A32'],'estimated_list_requests':2} for bid in p.base.BATCH_IDS]
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp,selected)
            result,drivers,state=self.invoke(root,prep,1)
            self.assertEqual(p.COMPLETE,result['status'],result);self.assertEqual(54,len(drivers))
            self.assertEqual(list(p.base.BATCH_IDS),result['validated_batch_ids'])
            self.assertEqual(108,result['totals']['business'])
            with self.assertRaisesRegex(ValueError,'ONLY_USER_PAUSED_RUN'):self.invoke(root,prep,2)

    def test_offline_check_creates_no_output_or_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp);result,drivers,state=self.invoke(root,prep,1,dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS',result['status']);self.assertFalse(state.exists());self.assertEqual([],drivers)

    def test_headless_config_and_progress_prefix_persist_through_pause_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp);first,_,state=self.invoke(root,prep,1,trigger=('AAA',1))
            rows=p.mbs.old.rows(state/'progress.jsonl')
            self.assertTrue(first['headless']);self.assertEqual(p.PAUSED,rows[-1]['status'])
            self.assertEqual(1,rows[-1]['completed_queries']);self.assertEqual(3,rows[-1]['total_queries'])
            self.assertEqual(2,rows[-1]['remaining_queries']);self.assertIsNone(rows[-1]['ETA_seconds'])
            self.assertEqual(['A32'],[r['ticker'] for r in rows if r['event']=='QUERY_VALIDATED'])
            second,drivers,state2=self.invoke(root,prep,2,start=100000)
            self.assertEqual(p.COMPLETE,second['status'],second);self.assertEqual(['AAA','IDJ'],[d.ticker for d in drivers])
            rows2=p.mbs.old.rows(state2/'progress.jsonl');self.assertEqual(1,rows2[0]['completed_queries'])
            self.assertLess(rows2[0]['active_elapsed_seconds'],100)
            self.assertEqual(3,rows2[-1]['completed_queries']);self.assertEqual(100,rows2[-1]['percent'])
            for i in range(3):
                ticker=['A32','AAA','IDJ'][i]
                self.assertTrue(p.read(state2/f'queries/{i+1:04d}/state'/ticker/'browser.json')['headless'])
                self.assertEqual(p.caps(),p.read(state2/f'queries/{i+1:04d}/state/chain_config.json'))

    def test_resealed_progress_counter_or_ETA_or_human_text_tamper_blocks_resume(self):
        for mode in ('counter','eta','human'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,prep=self.setup(tmp);_,_,state=self.invoke(root,prep,1,trigger=('AAA',1))
                if mode=='human':
                    path=state/'progress.log';path.write_text(path.read_text(encoding='utf8').replace('ETA tạm tính','ETA giả'),encoding='utf8')
                else:
                    path=state/'progress.jsonl';rows=p.mbs.old.rows(path)
                    if mode=='counter':rows[0]['completed_queries']=999
                    else:rows[0]['ETA_seconds']=0
                    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
                (state/'manifest.json').unlink();(state.parent/'delta-vsdc-headless54.zip').unlink();p.seal_run(state)
                with self.assertRaisesRegex(ValueError,'PROGRESS'):self.invoke(root,prep,2)

    def test_resealed_visible_browser_metadata_cannot_resume_under_headless_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,prep=self.setup(tmp);_,_,state=self.invoke(root,prep,1,trigger=('AAA',1))
            folder=state/'queries/0001';path=folder/'state/A32/browser.json';obj=p.read(path);obj['headless']=False
            path.write_text(json.dumps(obj),encoding='utf8')
            (folder/'state/manifest.json').unlink();(folder/'query.zip').unlink()
            p.base.seal(folder/'state',folder/'query.zip',artifact_type=p.base.BATCH_TYPE)
            (state/'manifest.json').unlink();(state.parent/'delta-vsdc-headless54.zip').unlink();p.seal_run(state)
            with self.assertRaisesRegex(ValueError,'HEADLESS_BROWSER_RECEIPT'):self.invoke(root,prep,2)

    def test_external_pause_control_and_exclusive_lock_and_crash_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/p.contract()['output_base'];run=base/'run-test';(run/'state').mkdir(parents=True)
            with p.execution_lock(base,'run-test'):
                with self.assertRaises(FileExistsError):
                    with p.execution_lock(base,'run-other'):pass
                self.assertEqual('PAUSE_REQUESTED',p.request_pause(root)['status'])
                self.assertTrue(p.Pause(run/'PAUSE_REQUEST').requested())
            self.assertFalse((base/'active.lock').exists())
            with self.assertRaises(ValueError):
                with p.execution_lock(base,'run-test'):raise ValueError('CRASH')
            self.assertTrue((base/'active.lock').exists())

    def test_CtrlC_handler_only_sets_flag_and_restores_previous_handler(self):
        with tempfile.TemporaryDirectory() as tmp:
            pause=p.Pause(Path(tmp)/'marker')
            with patch.object(p.prior.signal,'getsignal',return_value='previous'),patch.object(p.prior.signal,'signal') as change:
                with p.pause_signals(pause):
                    handler=change.call_args.args[1];handler(None,None)
                    self.assertTrue(pause.requested())
                self.assertEqual('previous',change.call_args.args[1])

    def test_CLI_has_no_force_subset_interval_or_error_resume_flags(self):
        spec=importlib.util.spec_from_file_location('resume_cli',ROOT/'scripts/corporate_actions/collect_vsdc_remaining54_headless_v3.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        for args in [['c','--force'],['c','--interval','1'],['c','--batch','11'],['c','--resume-errors'],['c','--check','--pause'],
                ['c','--headed'],['c','--workers','2'],['c','--hash-mode','mtime']]:
            with self.subTest(args=args),patch('sys.argv',args),patch('sys.stderr',old.old.io.StringIO()),self.assertRaises(SystemExit):cli.main()


class ProgressAndHeadlessTests(unittest.TestCase):
    def test_ETA_starts_after_five_completed_queries_and_decreases_while_current_query_runs(self):
        selected=[{'batch_id':'proposed-002','tickers':[f'T{i}' for i in range(8)]}]
        with tempfile.TemporaryDirectory() as tmp:
            c=old.old.Clock();report=p.Progress(tmp,selected,[],[],c.now(),0,c.now,lambda *a,**k:None)
            report.record('START')
            for i in range(5):
                report.begin(i,c.now());c.sleep(10);report.done(10)
                row=p.mbs.old.rows(Path(tmp)/'progress.jsonl')[-1]
                if i<4:self.assertIsNone(row['ETA_seconds'])
            self.assertEqual(30,row['ETA_seconds']);self.assertEqual(5,row['ETA_sample_count'])
            report.begin(5,c.now());c.sleep(3);report.page_start(1)
            a=p.mbs.old.rows(Path(tmp)/'progress.jsonl')[-1];self.assertEqual(27,a['ETA_seconds'])
            c.sleep(2);report.page_complete(1,1)
            b=p.mbs.old.rows(Path(tmp)/'progress.jsonl')[-1];self.assertEqual(25,b['ETA_seconds'])
            self.assertLess(b['ETA_seconds'],a['ETA_seconds'])
            report.done(5);d=p.mbs.old.rows(Path(tmp)/'progress.jsonl')[-1]
            self.assertAlmostEqual(55/6*2,d['ETA_seconds']);self.assertEqual(0,d['current_query_elapsed_seconds'])

    def test_resumed_ETA_uses_last_twenty_validated_durations_and_excludes_user_off_time(self):
        selected=[{'batch_id':'proposed-002','tickers':[f'T{i}' for i in range(30)]}]
        order=p.flatten(selected)
        with tempfile.TemporaryDirectory() as tmp:
            c=old.old.Clock();c.sleep(99000)
            report=p.Progress(tmp,selected,order[:25],list(range(1,26)),c.now(),100,c.now,lambda *a,**k:None)
            report.record('START');row=p.mbs.old.rows(Path(tmp)/'progress.jsonl')[-1]
            self.assertEqual(25,row['completed_queries']);self.assertEqual(20,row['ETA_sample_count'])
            self.assertEqual(15.5,row['ETA_mean_completed_query_seconds']);self.assertEqual(77.5,row['ETA_seconds'])
            self.assertEqual(100,row['active_elapsed_seconds'])

    def test_actual_driver_opens_only_headless_strict_fresh_context_and_closes_every_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,module,manager,browser,guards=lifecycle.LifecycleTests().harness(tmp)
            with patch.dict('sys.modules',{'playwright.sync_api':module}):
                with p.HeadlessDriver({**guards[0].config,'headless':True},guards[0]) as driver:
                    self.assertIs(driver.browser,browser)
            manager.chromium.launch.assert_called_once()
            self.assertEqual({'channel','headless','timeout'},set(manager.chromium.launch.call_args.kwargs))
            self.assertTrue(manager.chromium.launch.call_args.kwargs['headless'])
            self.assertEqual('chrome',manager.chromium.launch.call_args.kwargs['channel'])
            self.assertEqual({'ignore_https_errors':False,'accept_downloads':False,'service_workers':'block'},browser.new_context.call_args.kwargs)
            browser.new_context.return_value.close.assert_called_once();browser.close.assert_called_once();manager.stop.assert_called_once()

    def test_headless_launch_or_cleanup_failure_has_no_headed_fallback(self):
        for mode in ('launch','cleanup'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                _,module,manager,browser,guards=lifecycle.LifecycleTests().harness(tmp)
                if mode=='launch':manager.chromium.launch.side_effect=ValueError('LAUNCH_FAILED')
                else:browser.new_context.return_value.close.side_effect=ValueError('CLOSE_FAILED')
                with patch.dict('sys.modules',{'playwright.sync_api':module}),self.assertRaises(ValueError):
                    with p.HeadlessDriver(guards[0].config,guards[0]):pass
                manager.chromium.launch.assert_called_once();self.assertTrue(manager.chromium.launch.call_args.kwargs['headless'])
                manager.stop.assert_called_once()
                if mode=='cleanup':browser.close.assert_called_once();self.assertIsNotNone(guards[0].stop_reason)

    def test_caps_only_change_headless_and_stage_metadata_and_legacy_V2_output_is_not_auto_imported(self):
        self.assertEqual({'stage','output_base','preparation','headless'},
            {k for k in p.caps() if p.caps()[k]!=p.base.contract()[k]})
        self.assertTrue(p.caps()['headless']);self.assertEqual(2,p.caps()['business_interval_seconds'])
        self.assertEqual(100,p.contract()['max_segments']);self.assertFalse(p.contract()['source_error_resume'])
        self.assertEqual(5,p.contract()['ETA_warmup_queries']);self.assertEqual(20,p.contract()['ETA_window_queries'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p.legacy_output_gate(root)
            path=root/p.prior.contract()['output_base'];path.mkdir(parents=True)
            p.legacy_output_gate(root);(path/'run-old').mkdir()
            with self.assertRaisesRegex(ValueError,'NO_AUTO_IMPORT'):p.legacy_output_gate(root)


if __name__=='__main__':unittest.main()
