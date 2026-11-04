from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions import vsdc_resumable_chain as p
from tests.unit.ingestion.corporate_actions import test_vsdc_remaining_chain as old

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
            (state/'manifest.json').unlink();(state.parent/'delta-vsdc-resumable54.zip').unlink();p.seal_run(state)
            with self.assertRaisesRegex(ValueError,'REPARSE'):self.invoke(root,prep,2)

    def test_unsealed_crash_and_changed_zip_are_blocked_before_browser(self):
        for mode in ['unsealed','zip']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,prep=self.setup(tmp);_,_,state=self.invoke(root,prep,1,trigger=('A32',1))
                if mode=='unsealed':(state/'manifest.json').unlink()
                else:(state.parent/'delta-vsdc-resumable54.zip').write_bytes(b'broken')
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
            with patch.object(p.signal,'getsignal',return_value='previous'),patch.object(p.signal,'signal') as change:
                with p.pause_signals(pause):
                    handler=change.call_args.args[1];handler(None,None)
                    self.assertTrue(pause.requested())
                self.assertEqual('previous',change.call_args.args[1])

    def test_CLI_has_no_force_subset_interval_or_error_resume_flags(self):
        spec=importlib.util.spec_from_file_location('resume_cli',ROOT/'scripts/corporate_actions/collect_vsdc_remaining54_resumable_v2.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        for args in [['c','--force'],['c','--interval','1'],['c','--batch','11'],['c','--resume-errors'],['c','--check','--pause']]:
            with self.subTest(args=args),patch('sys.argv',args),patch('sys.stderr',old.old.io.StringIO()),self.assertRaises(SystemExit):cli.main()


if __name__=='__main__':unittest.main()
