import importlib.util,json,sys,tempfile,unittest
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('corporate_action_resume',ROOT/'scripts/resume_corporate_actions_v1.py')
resume=importlib.util.module_from_spec(spec);spec.loader.exec_module(resume)


class ResumeTests(unittest.TestCase):
    def checkpoint(self,root,processed=None):
        root.mkdir()
        rows=[dict(ticker=f'T{i:04}',exchange=('HOSE','HNX','UPCOM')[i%3],security_id=f'SYNTHETIC-{i}') for i in range(1522)]
        resume.base.write_new(root/'scope.csv',resume.base.csv_text(tuple(rows[0]),rows))
        processed=processed or ['T0000']
        state=dict(start='2019-01-31',end='2025-12-31',scope_sha256=resume.base.digest(root/'scope.csv'),
                   processed_securities=processed,pending_securities=[r['ticker'] for r in rows if r['ticker'] not in processed])
        resume.base.write_new(root/'resume_state.json',resume.base.json_text(state))
        resume.base.write_new(root/'manifest.json',resume.base.json_text(dict(artifact_type='corporate-action-c8-v2-checkpoint',
            files={p.name:resume.base.digest(p) for p in root.iterdir() if p.is_file()})))
        return rows

    def test_dry_run_skips_processed_and_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'checkpoint';rows=self.checkpoint(root);out=Path(temp)/'out'
            with patch.object(resume,'canonical_keys',return_value=resume.scope_keys(rows)):
                result=resume.resume(root,out,max_securities=2,dry_run=True)
            self.assertEqual(['T0001','T0002'],result['next_securities'])
            self.assertEqual(0,result['network_requests']);self.assertFalse(out.exists())

    def test_scope_mismatch_fails_before_any_collection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'checkpoint';self.checkpoint(root)
            with patch.object(resume,'canonical_keys',return_value=set()),patch.object(resume.multi,'collect') as collect:
                with self.assertRaisesRegex(ValueError,'SCOPE_MISMATCH'):resume.resume(root,Path(temp)/'out',dry_run=True)
                collect.assert_not_called()

    def test_cached_receipt_preserves_time_and_uses_no_network(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=root/'archived.bin';raw.write_bytes(b'<html>synthetic</html>')
            url='https://vsdc.vn/vi/ad/1'
            entry=dict(url=url,status=200,archive_path=str(raw),source_hash=resume.base.digest(raw),fetched_at='2024-01-01T01:02:03+07:00')
            budget=dict(stopped_hosts=set(),max_requests=0,physical_requests=0,cache_hits=0,last=0.)
            factory=resume.cached_transport_factory({(url,None):entry},{},budget)
            with patch.object(resume.PublicTransport,'fetch') as physical:
                body,ev=factory(root/'new').fetch(url)
                physical.assert_not_called()
            self.assertEqual(entry['fetched_at'],ev['fetched_at']);self.assertEqual(0,budget['physical_requests'])
            self.assertEqual(raw.read_bytes(),(root/'new'/ev['path']).read_bytes())

    def test_corrupt_cache_and_disallowed_host_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            raw=Path(temp)/'raw';raw.write_bytes(b'changed')
            url='https://vsdc.vn/vi/ad/1';entry=dict(status=200,archive_path=str(raw),source_hash='0'*64)
            budget=dict(stopped_hosts=set(),max_requests=10,physical_requests=0,cache_hits=0,last=0.)
            factory=resume.cached_transport_factory({(url,None):entry},{},budget)
            with patch.object(resume.PublicTransport,'fetch') as physical:
                with self.assertRaisesRegex(ValueError,'RAW_CACHE_CHECKSUM'):factory(Path(temp)/'out').fetch(url)
                with self.assertRaises(resume.SourceLimitation):factory(Path(temp)/'out2').fetch('https://unapproved.example/')
                physical.assert_not_called()

    def test_saved_host_stop_blocks_cached_and_physical_requests(self):
        budget=dict(stopped_hosts={'vsdc.vn'},max_requests=10,physical_requests=0,cache_hits=0,last=0.)
        factory=resume.cached_transport_factory({}, {},budget)
        with patch.object(resume.PublicTransport,'fetch') as physical:
            with self.assertRaises(resume.SourceLimitation):factory(Path('unused')).fetch('https://vsdc.vn/vi/ad/1')
            physical.assert_not_called()

    def test_exchange_assignments_are_disjoint_and_preserve_full_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'checkpoint';rows=self.checkpoint(root);sets=[]
            with patch.object(resume,'canonical_keys',return_value=resume.scope_keys(rows)):
                for exchange in ['HOSE','HNX','UPCOM']:
                    result=resume.resume(root,Path(temp)/exchange,max_securities=1522,workers=3,exchanges=[exchange],dry_run=True)
                    self.assertEqual(1522,result['scope_count']);sets.append(set(result['next_securities']))
            self.assertEqual(1521,len(set.union(*sets)))
            self.assertFalse(sets[0]&sets[1] or sets[1]&sets[2] or sets[0]&sets[2])

    def test_shared_host_clock_applies_across_transport_instances(self):
        budget=dict(stopped_hosts=set(),max_requests=10,physical_requests=0,cache_hits=0,last=0.)
        factory=resume.cached_transport_factory({}, {},budget)
        def fake(client,url,*args):client.requests.append({'url':url});return 'ok',{}
        with patch.object(resume.PublicTransport,'fetch',fake),patch.object(resume.time,'monotonic',return_value=100),patch.object(resume.time,'sleep') as sleep:
            factory(Path('unused1')).fetch('https://vsdc.vn/vi/ad/1')
            factory(Path('unused2')).fetch('https://vsdc.vn/vi/ad/2')
            factory(Path('unused3')).fetch('https://www.hnx.vn/')
        self.assertEqual([0,2,0],[c.args[0] for c in sleep.call_args_list])

    def test_concurrent_host_stop_and_global_budget_are_shared(self):
        budget=dict(stopped_hosts=set(),max_requests=10,physical_requests=0,cache_hits=0,last=0.)
        factory=resume.cached_transport_factory({}, {},budget);entered=threading.Event();release=threading.Event();calls=[]
        def denied(client,url,*args):
            calls.append(url);client.requests.append({'status':403});entered.set();release.wait(2)
            client.stopped_hosts.add('vsdc.vn');raise resume.SourceLimitation('HTTP 403')
        def attempt(client,url):
            try:client.fetch(url)
            except resume.SourceLimitation:return 'BLOCKED'
        with patch.object(resume.PublicTransport,'fetch',denied),patch.object(resume.time,'sleep'):
            with ThreadPoolExecutor(max_workers=2) as pool:
                a=pool.submit(attempt,factory(Path('unused1')),'https://vsdc.vn/vi/ad/1')
                self.assertTrue(entered.wait(2))
                b=pool.submit(attempt,factory(Path('unused2')),'https://vsdc.vn/vi/ad/2')
                release.set();self.assertEqual('BLOCKED',a.result());self.assertEqual('BLOCKED',b.result())
        self.assertEqual(1,len(calls));self.assertEqual(1,budget['physical_requests'])
        budget=dict(stopped_hosts=set(),max_requests=1,physical_requests=0,cache_hits=0,last=0.)
        factory=resume.cached_transport_factory({}, {},budget);calls=[]
        def ok(client,url,*args):calls.append(url);client.requests.append({'status':200});return 'ok',{}
        with patch.object(resume.PublicTransport,'fetch',ok),patch.object(resume.time,'sleep'):
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures=[pool.submit(attempt,factory(Path('unused'+str(i))),url) for i,url in enumerate(['https://vsdc.vn/','https://www.hnx.vn/','https://api.hsx.vn/'])]
                for f in futures:f.result()
        self.assertEqual(1,len(calls));self.assertEqual(1,budget['physical_requests'])

    def test_parallel_batch_records_each_finished_security_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'checkpoint';rows=self.checkpoint(root);out=Path(temp)/'out'
            def fake_collect(scope,child,start,end,**kwargs):
                child.mkdir(parents=True);own=resume.legacy.load_scope(scope)
                resume.shutil.copyfile(scope,child/'scope.csv')
                plan=dict(created_at=resume.now(),start=start,end=end)
                receipt=dict(url='https://vsdc.vn/synthetic-offline-test',status=200,cache_reused=True)
                for name,value in [('plan.json',plan),('requests.json',[receipt]),('source_checks.json',dict(checks=[],limitations=[]))]:
                    resume.base.write_new(child/name,resume.base.json_text(value))
                resume.multi.finalize(child,[],own,plan)
                return resume.multi.manifest(child,dict(status='PARTIAL',network_requests=0,observation_count=0))
            with patch.object(resume,'canonical_keys',return_value=resume.scope_keys(rows)),patch.object(resume.multi,'collect',side_effect=fake_collect):
                result=resume.resume(root,out,max_securities=3,workers=3)
            state=json.loads((out/'resume_state.json').read_text())
            self.assertEqual(4,result['processed']);self.assertEqual(4,state['completed_count'])
            self.assertEqual(4,len(set(state['processed_securities'])))
            self.assertEqual(3,len(list((out/'checkpoints').glob('*.json'))))

    def test_portable_reference_and_time_budget_fail_closed(self):
        path=ROOT/'tmp/portable_reference_test'
        self.assertEqual(path.resolve(),resume.resolve_reference(resume.as_reference(path)))
        with self.assertRaises(ValueError):resume.resolve_reference('@repo/../../outside')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'checkpoint';rows=self.checkpoint(root);out=Path(temp)/'out'
            with patch.object(resume,'canonical_keys',return_value=resume.scope_keys(rows)),patch.object(resume.time,'monotonic',side_effect=[0,10,10]),patch.object(resume.multi,'collect') as collect:
                result=resume.resume(root,out,max_seconds=1,workers=3)
                collect.assert_not_called()
            self.assertEqual(1,result['processed'])
            self.assertEqual('TIME_BUDGET_REACHED',json.loads((out/'batch_results.json').read_text())['stop_reason'])

    def test_shard_ownership_is_stable_when_pending_list_shrinks(self):
        with tempfile.TemporaryDirectory() as temp:
            before=Path(temp)/'before';after=Path(temp)/'after';rows=self.checkpoint(before)
            processed=['T0000','T0001','T0011'];self.checkpoint(after,processed)
            partitions=[]
            with patch.object(resume,'canonical_keys',return_value=resume.scope_keys(rows)):
                for i in range(3):
                    a=resume.resume(before,Path(temp)/'unused',max_securities=1522,dry_run=True,shard_count=3,shard_index=i)
                    b=resume.resume(after,Path(temp)/'unused2',max_securities=1522,dry_run=True,shard_count=3,shard_index=i)
                    self.assertEqual(set(a['next_securities'])-set(processed),set(b['next_securities']))
                    partitions.append(set(a['next_securities']))
            self.assertEqual(1521,len(set.union(*partitions)))
            self.assertFalse(partitions[0]&partitions[1] or partitions[1]&partitions[2] or partitions[0]&partitions[2])

    def test_zero_successful_responses_keep_security_pending(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'checkpoint';rows=self.checkpoint(root);out=Path(temp)/'out'
            def no_source(scope,child,*args,**kwargs):
                child.mkdir(parents=True)
                resume.base.write_new(child/'requests.json','[{"status":403}]')
                return dict(observation_count=0,network_requests=1)
            with patch.object(resume,'canonical_keys',return_value=resume.scope_keys(rows)),patch.object(resume.multi,'collect',side_effect=no_source):
                result=resume.resume(root,out,max_securities=1)
            state=json.loads((out/'resume_state.json').read_text())
            self.assertEqual(1,result['processed']);self.assertEqual('T0001',state['next_security'])
            self.assertEqual(1,state['failed_deferred_count'])
