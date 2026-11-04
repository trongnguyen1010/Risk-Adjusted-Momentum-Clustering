import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_fasthash_pilot as p
from delta_t1.ingestion.corporate_actions.vsdc_hash_fastpath import FullHashPlan as RealPlan
from tests.unit.ingestion.corporate_actions import test_vsdc_shared_browser_pilot as previous

ROOT=previous.ROOT


class FastHashPilotTests(unittest.TestCase):
    def fake_run(self,tmp,mode=None,dry=False,ready=True):
        root=Path(tmp);prep=root/'prep';prep.mkdir();evidence=root/'evidence.bin';evidence.write_bytes(b'original')
        protected={'evidence.bin':p.sha(evidence.read_bytes())}
        for name,value in [('manifest.json',{'files':{}}),('protected_old_files.json',protected),
                ('reusable_detail_provider_ids.json',['999999','100002']),('known_discovery_provider_ids.json',['999999','100002']),
                ('cache_policy.json',{}),('pilot_plan.json',{}),('experiment.json',{'test_only':True})]:p.write(prep/name,value)
        clock=previous.old.Clock();owners=[];plans=[]
        class CountingPlan:
            def __init__(self,project,approved):
                self.real=RealPlan(project,approved);self.calls=0;plans.append(self)
            def check(self):
                self.calls+=1
                if mode=='CALIBRATION_FAIL':raise ValueError('FULL_HASH_FAILURE_NO_FALLBACK')
                self.real.check();clock.sleep(.01)
        original=p.mbs.old.protected_check
        def reference(project,approved):original(project,approved);clock.sleep(.02)
        def factory(timings,config):
            owner=previous.FakeOwner(timings,config,clock,mode);owners.append(owner);create=owner.driver
            def driver(local,guard):
                value=create(local,guard);snapshot=value.snapshot
                def changed(number):
                    data=snapshot(number)
                    if mode=='MUTATE_SAME_METADATA' and local['ticker']=='A32' and number==1:
                        before=evidence.stat();evidence.write_bytes(b'changed!')
                        os.utime(evidence,ns=(before.st_atime_ns,before.st_mtime_ns))
                    return data
                value.snapshot=changed;return value
            owner.driver=driver;return owner
        with patch.object(p,'load_preparation',return_value=(p.contract(),prep)), \
                patch.object(p,'runtime',return_value={'fixture':'runtime'}), \
                patch.object(p.mbs.old,'readiness',return_value={'ready':ready}), \
                patch.object(p.mbs.old,'protected_check',side_effect=reference), \
                patch.object(p,'FullHashPlan',CountingPlan):
            result=p.run(root,root/'state',owner_factory=factory,clock=clock.now,dry_run=dry)
        return result,owners,plans

    def test_exact_same2s_source_browser_caps_with_only_hash_policy_and_metadata_changes(self):
        config=p.contract();p.validate(config)
        self.assertEqual({'stage','preparation','output_base','hash_checker','hash_calibration_pairs'},
            {k for k in config if config.get(k)!=p.previous.contract().get(k)})
        self.assertIs(p.BrowserOwner,p.previous.BrowserOwner);self.assertIs(p.baseline.Guard,p.previous.baseline.Guard)
        for key,value in [('business_interval_seconds',1),('hash_checker','MTIME_CACHE'),('hash_calibration_pairs',0),
                ('retry',True),('resume',True),('details',True),('max_business_requests',100),('max_context_attempts',10000),
                ('headless',True),('ignore_https_errors',True),('browser_lifecycle','SAME_CONTEXT')]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate({**config,key:value})

    def test_compile_once_calibrate_same_map_and_fifteen_full_hash_checks_all_source_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,plans=self.fake_run(tmp);state=Path(tmp)/'state'
            self.assertEqual(p.PASS,result['status'],result);self.assertEqual(1,len(plans))
            self.assertEqual(1,result['hash_plan_compilations']);self.assertEqual(2,result['hash_calibration_completed_pairs'])
            self.assertEqual(15,result['protected_hash_checks_attempted']);self.assertEqual(15,result['protected_hash_checks_completed'])
            self.assertEqual(17,plans[0].calls)  # Two offline comparisons plus all15 original guard/boundary checks.
            self.assertEqual(1,result['protected_files_per_check']);self.assertEqual(7,result['business_requests'])
            self.assertEqual(1,result['browser_launches']);self.assertEqual(3,result['fresh_contexts'])
            self.assertEqual(3,result['closed_contexts']);self.assertTrue(owners[0].closed)
            self.assertEqual(108,result['unique_provider_IDs']);self.assertEqual(2,result['reusable_cached_detail_IDs'])
            calibration=p.read(state/'hash_calibration.json')
            self.assertEqual([['baseline','candidate'],['candidate','baseline']],[r['order'] for r in calibration])
            self.assertTrue(all(set(r['seconds'])=={'baseline','candidate'} for r in calibration))
            calls=[]
            for ticker in p.baseline.PILOT:calls+=p.read(state/ticker/'business_requests.json')
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic']>=2 for a,b in zip(calls,calls[1:])))
            timing=p.read(state/'timings.json');self.assertEqual(1,timing['categories']['hash_plan_compile']['count'])
            self.assertEqual(1,timing['categories']['hash_calibration']['count'])
            self.assertEqual(15,timing['categories']['protected_hash']['count'])
            self.assertAlmostEqual(timing['elapsed_seconds'],timing['measured_exclusive_seconds']+timing['other_seconds'])
            self.assertGreater(timing['elapsed_seconds'],result['elapsed_seconds'])
            archive=Path(tmp)/'pilot.zip';receipt=p.package(state,archive)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip());self.assertIn('hash_calibration.json',z.namelist())
                manifest=p.read(state/'manifest.json');self.assertEqual(p.TYPE,manifest['artifact_type'])
                for name,digest in manifest['files'].items():self.assertEqual(digest,p.sha(z.read(name)))
            self.assertEqual(p.sha(archive.read_bytes()),p.read(receipt)['ZIP_sha256'])

    def test_same_parsed_pages_JS_complete_queries_and_cache_as_shared2s_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            one=Path(tmp)/'one';two=Path(tmp)/'two';one.mkdir();two.mkdir()
            result,_,_=self.fake_run(one);old,_,_=previous.PilotTests().fake_run(two)
            self.assertEqual(result['completed_tickers'],old['completed_tickers'])
            for ticker,pages in [('A32',2),('AAA',3),('IDJ',2)]:
                for name in ['complete_query.json','fresh_source_contract.json',*[f'page{i}.json' for i in range(1,pages+1)]]:
                    self.assertEqual(p.read(one/'state'/ticker/name),p.read(two/'state'/ticker/name))
            self.assertEqual(p.read(one/'state/deduplicated_query_articles.json'),p.read(two/'state/deduplicated_query_articles.json'))

    def test_same_size_and_mtime_mutation_during_first_query_stops_before_next_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,_=self.fake_run(tmp,'MUTATE_SAME_METADATA')
            self.assertNotEqual(p.PASS,result['status']);self.assertTrue(result['source_stopped'])
            self.assertEqual(1,result['business_requests']);self.assertEqual(1,len(owners[0].drivers))
            self.assertEqual([],result['completed_tickers']);self.assertIn('evidence.bin',result['stop_reason'])
            self.assertTrue(owners[0].closed);self.assertFalse(result['resumable'])
            p.package(Path(tmp)/'state',Path(tmp)/'partial.zip')

    def test_calibration_candidate_failure_has_no_reference_fallback_and_zero_source_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,_=self.fake_run(tmp,'CALIBRATION_FAIL')
            self.assertNotEqual(p.PASS,result['status']);self.assertEqual(0,result['business_requests'])
            self.assertEqual(0,result['browser_launches']);self.assertEqual([],owners[0].drivers)
            self.assertFalse(result['resumable']);self.assertEqual(0,result['hash_calibration_completed_pairs'])
            self.assertIn('FULL_HASH_FAILURE_NO_FALLBACK',result['stop_reason'])

    def test_HTTP_layout_and_context_cleanup_failures_still_stop_all_later_queries(self):
        for mode,browsers,completed in [('STALE',1,[]),('AAA_HTTP400',2,['A32']),('CLOSE_FAIL',2,['A32'])]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,owners,_=self.fake_run(tmp,mode)
                self.assertNotEqual(p.PASS,result['status']);self.assertTrue(result['source_stopped'])
                self.assertEqual(browsers,len(owners[0].drivers));self.assertEqual(completed,result['completed_tickers'])
                self.assertTrue(owners[0].closed);self.assertFalse(result['resumable'])

    def test_offline_check_does_not_compile_plan_create_owner_or_launch_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,owners,plans=self.fake_run(tmp,dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS',result['status']);self.assertEqual([],owners);self.assertEqual([],plans)
            self.assertFalse((Path(tmp)/'state').exists())

    def test_CLI_rejects_existing_run_and_rate_cache_force_resume_override_flags(self):
        spec=importlib.util.spec_from_file_location('fasthash_cli',ROOT/'scripts/corporate_actions/collect_vsdc_fasthash2s_pilot_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,p.contract())
            (root/p.contract()['output_base']/'run-existing').mkdir(parents=True)
            for args in [['p'],['p','--interval','1'],['p','--cache'],['p','--force'],['p','--resume']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(p,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',previous.old.io.StringIO()),self.assertRaises(SystemExit):cli.main()
                run.assert_not_called()


if __name__=='__main__':unittest.main()
