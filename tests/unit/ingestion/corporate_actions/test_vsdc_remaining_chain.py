from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_remaining_chain as p
from tests.unit.ingestion.corporate_actions import test_vsdc_supplement_plan as prior
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_pilot as old

ROOT=old.ROOT
CONFIG=p.contract()
SELECTED=[{'batch_id':'proposed-002','tickers':['A32'],'estimated_list_requests':2},
          {'batch_id':'proposed-003','tickers':['AAA'],'estimated_list_requests':3},
          {'batch_id':'proposed-004','tickers':['IDJ'],'estimated_list_requests':2}]


class Driver(prior.Driver):
    def metadata(self):
        self.guard.business[-1].update(request_header_names=['content-type','cookie','x-requested-with'],
            request_content_type=None if len(self.guard.business)==1 else 'application/json;charset=UTF-8',
            x_requested_with=None if len(self.guard.business)==1 else 'XMLHttpRequest')
    def snapshot(self,number):
        value=super().snapshot(number)
        if self.mode=='SECRET' and self.ticker=='AAA':value['fragment']+='<input value="SECRET">'
        return value
    def first(self):
        assert self.guard.admit(self.config['url'],'GET','document');self.metadata()
        return self.snapshot(1)
    def next_page(self,number,previous):
        self.guard.log({'event':'UI_PAGE_BUTTON','target_page':number,
            'visible_label':str(number),'source_onclick':f'changePageArticles({number})'})
        assert self.guard.admit(self.config['url'],'POST','xhr',json.dumps({'SearchKey':4,'CurrentPage':number}))
        self.metadata();return self.snapshot(number)
    def __enter__(self):
        # Match the real driver's safe response metadata: keys present even when absent on wire.
        original=self.guard.response
        self.guard.response=lambda url,method,status,headers:original(url,method,status,
            {'content-type':headers.get('content-type'),'content-length':None,'retry-after':None})
        return self


class ChainTests(unittest.TestCase):
    def run_fake(self,tmp,mode=None,gate=None,selected=SELECTED,dry=False,ready=True):
        prep=Path(tmp)/'prep';prep.mkdir()
        for name,value in [('protected_old_files.json',{}),('reusable_detail_provider_ids.json',['100002']),
                ('known_discovery_provider_ids.json',['100002']),('selected_batches.json',selected),
                ('cache_policy.json',{}),('query_inventory_before_chain.json',[]),('manifest.json',{'files':{}})]:
            p.write(prep/name,value)
        clock=old.Clock();drivers=[]
        def factory(config,guard):
            driver=Driver(config,guard,clock,mode);drivers.append(driver);return driver
        real=p.validate_batch
        def validate(*args):
            if gate:return gate(real,*args)
            return real(*args)
        with patch.object(p,'load_preparation',return_value=(deepcopy(CONFIG),prep)), \
                patch.object(p.mbs.old,'readiness',return_value={'ready':ready}), \
                patch.object(p,'validate_batch',side_effect=validate):
            result=p.run(ROOT,Path(tmp)/'state',dry_run=dry,driver_factory=factory,clock=clock.now,emit=lambda *a,**k:None)
        return result,drivers

    def test_three_real_acquire_seal_validate_transitions_share_pacing_and_known_IDs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.run_fake(tmp)
            self.assertEqual('PASS_ALL_SELECTED_BATCHES_AUTOMATED_VALIDATION_REVIEW_REQUIRED',result['status'],result)
            self.assertEqual(3,result['validated_batch_count']);self.assertEqual(3,result['validated_query_count'])
            self.assertEqual(7,result['business_requests']);self.assertEqual(12,result['elapsed_seconds'])
            self.assertEqual(1,result['reusable_detail_IDs_unchanged']);self.assertEqual(108,result['unique_provider_IDs_in_validated_batches'])
            self.assertEqual(107,result['first_discovered_IDs']);self.assertEqual(108,result['known_discovery_IDs_after_validated_batches'])
            self.assertEqual(0,result['detail_requests']);self.assertFalse(result['resumable'])
            self.assertFalse(result['pit_or_identity_promoted']);self.assertTrue(all(d.closed for d in drivers))
            state=Path(tmp)/'state';calls=[]
            for b in SELECTED:
                folder=state/'batches'/b['batch_id']/'state'
                self.assertEqual('PASS_AUTOMATED_BATCH_VALIDATION',p.read(folder.parent/'validation.json')['status'])
                calls+=p.read(folder/b['tickers'][0]/'business_requests.json')
            self.assertEqual([2]*6,[b['at_monotonic']-a['at_monotonic'] for a,b in zip(calls,calls[1:])])
            first=p.read(state/'batches/proposed-002/state/deduplicated_query_articles.json')
            second=p.read(state/'batches/proposed-003/state/deduplicated_query_articles.json')
            self.assertFalse(next(r for r in first if r['provider_article_id']=='999999')['known_discovery_before_batch'])
            common=next(r for r in second if r['provider_article_id']=='999999')
            self.assertTrue(common['known_discovery_before_batch']);self.assertFalse(common['detail_reusable_from_cache'])
            merged=p.read(state/'deduplicated_validated_query_articles.json')
            common=next(r for r in merged if r['provider_article_id']=='999999')
            self.assertEqual(['A32','AAA','IDJ'],common['query_tickers']);self.assertEqual(3,len(common['batch_ids']))
            archive=Path(tmp)/'all.zip';p.seal(state,archive,artifact_type=p.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip());self.assertIn('batches/proposed-004/state/manifest.json',z.namelist())
                self.assertNotIn('batch_zips/proposed-002.zip',z.namelist())
                for name,digest in json.loads(z.read('manifest.json'))['files'].items():self.assertEqual(digest,p.sha(z.read(name)))

    def test_source_layout_and_privacy_failure_stop_whole_chain_preserve_passed_batch(self):
        for mode,passed,browsers in [('STALE',0,1),('AAA_HTTP400',1,2),('SECRET',1,2)]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.run_fake(tmp,mode)
                self.assertEqual('STOPPED_CHAIN_SOURCE_OR_INTEGRITY',result['status'])
                self.assertEqual(passed,result['validated_batch_count']);self.assertEqual(browsers,len(drivers))
                self.assertFalse(result['resumable']);self.assertTrue(all(d.closed for d in drivers))
                self.assertFalse((Path(tmp)/'state/batches/proposed-004').exists())
                p.seal(Path(tmp)/'state',Path(tmp)/'partial.zip',artifact_type=p.TYPE)
                if mode=='SECRET':
                    self.assertTrue(all(b'SECRET' not in f.read_bytes() for f in (Path(tmp)/'state').rglob('*') if f.is_file()))

    def test_corrupt_zip_gate_prevents_next_browser_and_keeps_first_batch(self):
        def gate(real,folder,archive,*args):
            if folder.parent.name=='proposed-003':
                with zipfile.ZipFile(archive,'a') as z:z.writestr('UNDECLARED.txt','bad')
            return real(folder,archive,*args)
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.run_fake(tmp,gate=gate)
            self.assertEqual(1,result['validated_batch_count']);self.assertEqual(2,len(drivers))
            self.assertIn('ZIP_CRC_OR_MEMBER',result['stop_reason'])

    def test_semantic_reparse_detects_mutation_even_when_attacker_reseals_manifest_and_zip(self):
        for mode in ['parsed','checkpoint','pacing','dedup','ledger','receipt']:
            def gate(real,folder,archive,*args):
                if folder.parent.name=='proposed-003':
                    paths={'parsed':('AAA/page1.json','page',2),
                        'checkpoint':('checkpoints/002.json','completed_tickers',[]),
                        'pacing':('input_provenance.json','previous_business_start',None),
                        'receipt':('AAA/page1_receipt.json','http_body_hash_not_archived','SECRET')}
                    if mode in paths:
                        name,key,value=paths[mode];obj=p.read(folder/name);obj[key]=value;p.write(folder/name,obj)
                    elif mode=='dedup':p.write(folder/'deduplicated_query_articles.json',[])
                    else:
                        path=folder/'AAA/network_ledger.jsonl'
                        path.write_text(path.read_text(encoding='utf8').replace('changePageArticles(2)','changePageArticles(3)'),encoding='utf8')
                    (folder/'manifest.json').unlink();archive.unlink();p.seal(folder,archive,artifact_type=p.BATCH_TYPE)
                return real(folder,archive,*args)
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.run_fake(tmp,gate=gate)
                self.assertEqual(1,result['validated_batch_count']);self.assertEqual(2,len(drivers))
                self.assertEqual('proposed-003',result['failed_batch'])

    def test_offline_check_and_setup_failure_do_not_launch_browser(self):
        for dry,ready in [(True,True),(False,False)]:
            with self.subTest(dry=dry),tempfile.TemporaryDirectory() as tmp:
                result,drivers=self.run_fake(tmp,dry=dry,ready=ready)
                self.assertEqual([],drivers)
                if dry:self.assertFalse((Path(tmp)/'state').exists())
                else:self.assertEqual(0,result['validated_batch_count'])

    def test_orchestrator_reaches_batch055_without_an_eleven_batch_limit(self):
        # Synthetic repeated fixture isolates chain length; production uniqueness is tested separately.
        selected=[{'batch_id':bid,'tickers':['A32'],'estimated_list_requests':2} for bid in p.BATCH_IDS]
        with tempfile.TemporaryDirectory() as tmp:
            result,drivers=self.run_fake(tmp,selected=selected)
            self.assertEqual(list(p.BATCH_IDS),result['validated_batch_ids'],result)
            self.assertEqual(54,len(drivers));self.assertEqual(108,result['business_requests'])
            self.assertEqual('PASS_ALL_SELECTED_BATCHES_AUTOMATED_VALIDATION_REVIEW_REQUIRED',result['status'])

    def test_exact_selection_54_batches1073_queries_and2839_estimate(self):
        selected=[];overlay=[];offset=0
        for i,bid in enumerate(p.BATCH_IDS):
            tickers=[f'T{n:04d}' for n in range(offset,offset+(13 if i==53 else 20))];offset+=len(tickers)
            selected.append({'batch_id':bid,'tickers':tickers,'estimated_list_requests':83 if i==0 else 52})
            overlay.extend({'ticker':t,'status':'PLANNED_NOT_AUTHORIZED'} for t in tickers)
        self.assertEqual(1073,len(p.validate_selection(selected,overlay)))
        for mode in ['order','missing','duplicate','estimate','completed','held']:
            a,b=deepcopy(selected),deepcopy(overlay)
            if mode=='order':a.reverse()
            elif mode=='missing':a[-1]['tickers'].pop()
            elif mode=='duplicate':a[-1]['tickers'][-1]=a[0]['tickers'][0]
            elif mode=='estimate':a[0]['estimated_list_requests']+=1
            elif mode=='completed':b[0]['status']='COMPLETED_REVIEWED_QUERY_SNAPSHOT'
            else:b[0]['status']='HOLD_LARGE_QUERY_SCOPE_REVIEW'
            with self.subTest(mode=mode),self.assertRaises(ValueError):p.validate_selection(a,b)

    def test_exact_contract_no_scope_rate_privacy_or_retry_override(self):
        p.validate(CONFIG)
        for key,value in [('batch_ids',list(p.BATCH_IDS)[:11]),('business_interval_seconds',1),('details',True),
                ('resume',True),('retry',True),('ignore_https_errors',True),('headless',True),('max_seconds',999999)]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate({**CONFIG,key:value})

    def test_CLI_rerun_guard_and_no_batch_resume_force_or_interval_override(self):
        spec=importlib.util.spec_from_file_location('chain_cli',ROOT/'scripts/corporate_actions/collect_vsdc_remaining54_chain_v1.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/p.CONFIG;path.parent.mkdir(parents=True);p.write(path,CONFIG)
            (root/CONFIG['output_base']/'run-existing').mkdir(parents=True)
            for args in [['chain'],['chain','--interval','1'],['chain','--resume'],['chain','--force'],['chain','--batch','11'],['chain','--start-at','4']]:
                with self.subTest(args=args),patch.object(cli,'ROOT',root),patch.object(cli,'run') as run, \
                        patch('sys.argv',args),patch('sys.stderr',old.io.StringIO()),self.assertRaises(SystemExit):cli.main()
                run.assert_not_called()


class GuardTests(unittest.TestCase):
    def make(self,tmp,ticker='A32',clock=None,shared=None):
        clock=clock or old.Clock();shared=shared or p.Budget(CONFIG,clock.now)
        if not shared.active:shared.begin('proposed-002')
        config={**CONFIG,'ticker':ticker,'url':p.search_url(ticker),'max_seconds':180,
            'max_context_request_attempts':98,'max_asset_attempts':78}
        return p.Guard(config,Path(tmp),lambda:None,clock.now,shared),shared,clock

    def test_two_seconds_shared_between_batches_not_reset(self):
        for delay,allowed in [(1.999,False),(2,True)]:
            with self.subTest(delay=delay),tempfile.TemporaryDirectory() as tmp:
                a=Path(tmp)/'a';b=Path(tmp)/'b';a.mkdir();b.mkdir()
                g,s,c=self.make(a);self.assertTrue(g.admit(p.search_url('A32'),'GET','document'))
                s.end();s.begin('proposed-003');c.sleep(delay);h,_,_=self.make(b,'AAA',c,s)
                self.assertEqual(g.business[0]['at_monotonic'],s.previous_start)
                self.assertEqual(allowed,h.admit(p.search_url('AAA'),'GET','document'))

    def test_global_batch_query_business_context_asset_and_time_caps(self):
        for mode in ['global_context','batch_context','query_context','asset','global_business','batch_business','query_time','batch_time','global_time']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp)
                if mode=='global_context':s.attempts=CONFIG['max_context_attempts']
                if mode=='batch_context':s.attempts=CONFIG['max_batch_context_attempts']
                if mode=='query_context':g.attempts=98
                if mode=='asset':g.assets=78
                if mode=='global_business':s.business=5400
                if mode=='batch_business':s.business=100
                if mode=='query_time':c.sleep(180)
                if mode=='batch_time':s.batch_started=-1200
                if mode=='global_time':s.started=-28800
                self.assertFalse(g.admit('https://vsdc.vn/assets/a.css' if mode=='asset' else p.search_url('A32'),
                    'GET','stylesheet' if mode=='asset' else 'document'))

    def test_twenty_sequential_pages_allowed_twenty_first_and_details_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            g,s,c=self.make(tmp);self.assertTrue(g.admit(p.search_url('A32'),'GET','document'))
            for n in range(2,21):
                c.sleep(2);self.assertTrue(g.admit(p.search_url('A32'),'POST','xhr',json.dumps({'SearchKey':4,'CurrentPage':n})))
            c.sleep(2);self.assertFalse(g.admit(p.search_url('A32'),'POST','xhr','{"SearchKey":4,"CurrentPage":21}'))
        with tempfile.TemporaryDirectory() as tmp:
            g,s,c=self.make(tmp);self.assertFalse(g.admit(p.mbs.DETAIL_URL,'GET','document'))

    def test_unchanged_inputs_redirect_and_source_boundary_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            g,s,c=self.make(tmp)
            def changed():raise ValueError('OLD_STATE_CHANGED')
            g.check_old=changed;self.assertFalse(g.admit(p.search_url('A32'),'GET','document'))
        for status,headers in [(429,{}),(403,{}),(301,{}),(200,{'retry-after':'10'})]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                g,s,c=self.make(tmp);g.response(p.search_url('A32'),'GET',status,headers)
                self.assertFalse(g.admit(p.search_url('A32'),'GET','document'))


if __name__=='__main__':unittest.main()
