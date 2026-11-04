"""Isolated2s three-query source pilot for full-SHA256 fast path;old collectors stay frozen."""
from datetime import datetime, timezone
import math
from pathlib import Path
import time

from . import vsdc_shared_browser_pilot as previous
from .vsdc_hash_fastpath import FullHashPlan

baseline,mbs=previous.baseline,previous.mbs
read,write,sha,hashes,seal=previous.read,previous.write,previous.sha,previous.hashes,previous.seal
verify_artifact=previous.verify_artifact
BrowserOwner,Timings=previous.BrowserOwner,previous.Timings
CONFIG='configs/data/corporate_actions/vsdc_fasthash2s_pilot_v1.json'
TYPE='vsdc-fasthash2s-three-query-source-pilot-v1'
PREP_TYPE='vsdc-fasthash2s-source-pilot-preparation-v1'
PASS='PASS_FAST_FULL_HASH2S_SOURCE_PILOT_REVIEW_REQUIRED'
PARENTS={
    'shared_preparation':('data/corporate_actions/work/vsdc_shared_browser2s_preparation_20261103_v1',
        '759263c4c487c2dcb36ee3198b074885c6ad23920e25b68eb753317288b30b39',previous.PREP_TYPE),
    'shared_run':('data/corporate_actions/work/vsdc_shared_browser2s_pilot_v1/run-20261103T084428264720Z/state',
        '65864496db596545eafeafa22fca858b4465573d2bca58ea6a724819a9cb2de9',previous.TYPE),
    'shared_review':('data/corporate_actions/work/vsdc_shared_browser2s_live_review_20261103_v1',
        '9d21aaea9fcedfa36662e34b77dcf887ef29646ebcd1e2142b62ca62fdce9f5c','vsdc-shared-browser2s-offline-live-review-v1'),
    'shared_validation':('data/corporate_actions/work/vsdc_shared_browser2s_live_review_validation_20261103_v1',
        '9f33d0651614ffece3e0bb16fa2bc72a35fb7ea6467b08a37081462e6f2cdf50','vsdc-shared-browser2s-offline-live-review-validation-v1'),
    'offline_benchmark':('data/corporate_actions/work/vsdc_hash_fastpath_offline_benchmark_20261103_v1',
        '95286447a08471290821b3a20370c96d1db420609c900c5cb9e232fe086c94b8','vsdc-full-hash-fastpath-offline-benchmark-v1'),
    'offline_validation':('data/corporate_actions/work/vsdc_hash_fastpath_offline_validation_20261103_v1',
        'f286fa2007075f8699809654ed0ae7f1b628488a3b27b7b58cff5fa3a8720293','vsdc-full-hash-fastpath-offline-validation-v1')}


def contract():
    return {**previous.contract(),'stage':'VSDC_FAST_FULL_HASH2S_SOURCE_PILOT_PREPARATION_V1',
        'output_base':'data/corporate_actions/work/vsdc_fasthash2s_pilot_v1',
        'preparation':'data/corporate_actions/work/vsdc_fasthash2s_preparation_20261103_v1',
        'hash_checker':'COMPILED_PATH_FULL_SHA256_EVERY_CALL','hash_calibration_pairs':2}


def validate(config):
    if config!=contract():raise ValueError('EXACT_FAST_FULL_HASH2S_THREE_QUERY_CONTRACT_REQUIRED')


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_fasthash_pilot.py',
        'src/delta_t1/ingestion/corporate_actions/vsdc_hash_fastpath.py',
        'scripts/corporate_actions/prepare_vsdc_fasthash2s_pilot_v1.py',
        'scripts/corporate_actions/collect_vsdc_fasthash2s_pilot_v1.py']
    return {**previous.runtime(project),**{n:sha((project/n).read_bytes()) for n in names}}


def parents(project):
    _,prep=previous.load_preparation(project)
    for name,(rel,digest,kind) in PARENTS.items():
        folder=project/rel
        if sha((folder/'manifest.json').read_bytes())!=digest:raise ValueError('FASTHASH_PARENT_CHANGED: '+name)
        verify_artifact(folder,{kind})
    review=read(project/PARENTS['shared_review'][0]/'review.json')
    if review['status']!='PASS_SHARED_BROWSER_CONTEXT_ISOLATION_AND_DATA_NO_OBSERVED_SPEEDUP':raise ValueError('REVIEWED_SHARED_PROCESS_REQUIRED')
    if read(project/PARENTS['offline_benchmark'][0]/'result.json')['status']!='PASS_OFFLINE_EQUIVALENCE_AND_LOCAL_SPEEDUP':
        raise ValueError('OFFLINE_EQUIVALENCE_AND_BENCHMARK_PASS_REQUIRED')
    for name,digest in read(project/PARENTS['offline_validation'][0]/'self_review.json')['new_runtime_and_tests_sha256'].items():
        if sha((project/name).read_bytes())!=digest:raise ValueError('OFFLINE_CANDIDATE_CHANGED: '+name)
    receipt=Path(review['inputs']['packaging_receipt'])
    if sha(receipt.read_bytes())!=review['inputs']['packaging_receipt_sha256']:raise ValueError('SHARED_PACKAGING_RECEIPT_CHANGED')
    return prep,review,receipt


def load_preparation(project):
    config=read(project/CONFIG);validate(config);parents(project)
    prep=project/config['preparation'];verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('FASTHASH_PREPARED_RUNTIME_CHANGED')
    # Preflight still validates all approved evidence with the original implementation.
    mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    if (len(read(prep/'reusable_detail_provider_ids.json'))!=27731
            or len(read(prep/'known_discovery_provider_ids.json'))!=28276):raise ValueError('CACHE_BASELINE_CHANGED')
    return config,prep


def prepare(project):
    project=Path(project).resolve();config=read(project/CONFIG);validate(config);old,review,receipt=parents(project)
    output=project/config['preparation']
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    protected=read(old/'protected_old_files.json')
    for rel,_,_ in PARENTS.values():
        folder=project/rel
        for name in ['manifest.json',*read(folder/'manifest.json')['files']]:
            path=folder/name;protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    protected[receipt.relative_to(project).as_posix()]=sha(receipt.read_bytes())
    protected.update(previous.runtime(project))
    for name in ['src/delta_t1/ingestion/corporate_actions/vsdc_hash_fastpath.py',
                 'configs/data/corporate_actions/vsdc_hash_fastpath_offline_v1.json',
                 'scripts/corporate_actions/benchmark_vsdc_hash_fastpath_v1.py']:
        protected[name]=sha((project/name).read_bytes())
    output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','known_discovery_provider_ids.json','cache_policy.json','pilot_plan.json']:
        (output/name).write_bytes((old/name).read_bytes())
    write(output/'experiment.json',{'kind':'FAST_FULL_HASH_CHECKER_WITH_SAME_SHARED_BROWSER_AND2S',
        'primary_baseline':{'path':PARENTS['shared_review'][0],'manifest_sha256':PARENTS['shared_review'][1],
            'acquisition_seconds':review['comparison']['experimental_elapsed_seconds'],
            'protected_hash_seconds':review['timing_breakdown']['exclusive_seconds']['protected_hash'],
            'protected_hash_calls':15,'protected_file_count':864,'query_rows':{'A32':35,'AAA':51,'IDJ':24},'business_requests':7},
        'candidate_protected_file_count':len(protected),'same_set_offline_calibration_pairs':2,'calibration_order':['BASELINE_CANDIDATE','CANDIDATE_BASELINE'],
        'source_hash_callback_frequency_unchanged':True,'every_entry_open_fullread_SHA256_every_call':True,
        'content_stat_digest_cache':False,'expected_hash_deduplication':False,'browser_lifecycle_unchanged':True,
        'ZIP_policy_changed':False,'minimum_interval_seconds':2,'expected_new_query_completion_credit':0,
        'bulk_runner_changed':False,'detail_downloads':False,
        'acceptance':'Same complete query pages/IDs/titles/JS/cache,allbusiness200,min2s,onebrowser/threefreshclosedcontexts,no boundaries,timing sums and full-hash call counts reconcile.',
        'limits':'Primary source baseline historical/unpaired and protected set grew;calibrate both hash implementations on exact new set but do not claim paired source speedup. No39percent total collection claim.'})
    write(output/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,'browser_launches':0,
        'readiness':mbs.old.readiness(config),'runtime_change':'Only source protected-check callback now uses compiled full-hash plan;no checks removed',
        'calibration':'Offline2pairs before acquisition;preflight/calibration/compiler outside result acquisition elapsed',
        'on_error':'STOP no retry/relaunch/resume/rate fallback','next_step':'User-run once then offline ZIP/data/timing review before any54batch version change'})
    write(output/'protected_old_files.json',protected);write(output/'runtime.json',runtime(project))
    write(output/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(output)});load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','source_requests':0,'interval_seconds':2,'tickers':list(baseline.PILOT),
        'planned_browser_launches':1,'planned_fresh_contexts':3,'protected_old_files':len(protected),'output':str(output)}


def calibrate(project,protected,plan,timings,clock,records):
    """Same-set offline reference/candidate checks;no source/network and no digest caching."""
    with timings.span('hash_calibration'):
        for pair,order in enumerate((('baseline','candidate'),('candidate','baseline')),1):
            row={'pair':pair,'order':list(order),'seconds':{}}
            records.append(row)
            for name in order:
                started=clock()
                if name=='baseline':mbs.old.protected_check(project,protected)
                else:plan.check()
                row['seconds'][name]=clock()-started


def run(project,output,*,dry_run=False,owner_factory=BrowserOwner,clock=time.monotonic):
    project,output=Path(project).resolve(),Path(output).resolve();timings=Timings(clock)
    with timings.span('preflight'):config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    ready=mbs.old.readiness(config)
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED','source_requests':0,
        'browser_launched':False,'pilot_tickers':list(baseline.PILOT),'planned_browser_launches':1,'planned_fresh_contexts':3,'readiness':ready}
    output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','known_discovery_provider_ids.json','cache_policy.json',
                 'pilot_plan.json','experiment.json','protected_old_files.json']:
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config)
    with timings.span('runtime_hash'):write(output/'runtime.json',runtime(project))
    write(output/'environment.json',ready)
    write(output/'input_provenance.json',{'preparation':str(prep),'manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'capture_kind':'PUBLIC_RENDERED_QUERY_FRAGMENTS_NOT_RAW_HTTP'})
    protected=read(prep/'protected_old_files.json');plan=None;calibration=[];checks={'attempted':0,'completed':0}
    def check():
        checks['attempted']+=1
        with timings.span('protected_hash'):
            if plan is None:raise ValueError('FULL_HASH_PLAN_NOT_COMPILED')
            plan.check()
        checks['completed']+=1
    owner=owner_factory(timings,config);shared=baseline.SharedBudget(config,clock);guards=[];completed=[];articles=[]
    reusable=set(read(prep/'reusable_detail_provider_ids.json'));result={'status':'STOPPED_SHARED_BROWSER_OR_SOURCE_REVIEW_REQUIRED',
        'resumable':False,'bulk_collection_ready':False,'business_interval_seconds':2,'source_stopped':False,'detail_requests':0,
        'canonical_fields_applied':0,'normalized_observations':0,'pit_or_identity_promoted':False,'openai_api_calls':0}
    try:
        if not ready['ready']:raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
        with timings.span('hash_plan_compile'):plan=FullHashPlan(project,protected)
        calibrate(project,protected,plan,timings,clock,calibration)
        shared.started=clock()  # Preserve historical acquisition window;offline setup is measured separately.
        for ticker in baseline.PILOT:
            shared.check();check();folder=output/ticker;folder.mkdir();(folder/'network_ledger.jsonl').touch()
            local={**config,'ticker':ticker,'url':baseline.search_url(ticker),'max_seconds':config['max_query_seconds'],
                'max_context_request_attempts':config['max_context_per_query'],'max_asset_attempts':config['max_assets_per_query']}
            guard=baseline.Guard(local,folder,check,clock,shared);guards.append(guard)
            try:
                with owner.driver(local,guard) as driver:
                    if shared.last is not None:
                        with timings.span('pacing',ticker):driver.pace(max(0,2-(clock()-shared.last)))
                    with timings.span('browser_first',ticker):current=driver.first();guard.check()
                    write(folder/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,'default_identity':True,
                        'TLS_ignore_errors':False,'cookie_auth_exported':False,'shared_process':True,'fresh_context_ordinal':driver.ordinal})
                    with timings.span('archive_parse',ticker):write(folder/'fresh_source_contract.json',baseline.source_contract(current['scope_html'],ticker))
                    seen=[];query_articles=[];total=None;previous=''
                    for number in range(1,5):
                        if number>1:
                            check()
                            with timings.span('pacing',ticker):driver.pace(max(0,2-(clock()-shared.last)))
                            with timings.span('browser_next',ticker):current=driver.next_page(number,previous);guard.check()
                        with timings.span('archive_parse',ticker):
                            if current['url']!=local['url'] or current['http_status']!=200:raise ValueError('EXACT_QUERY_HTTP200_REQUIRED')
                            data=mbs.old.fragment_bytes(current['fragment'],config['max_html_bytes'])
                            fragments=folder/'rendered_html';fragments.mkdir(exist_ok=True)
                            with (fragments/f'page{number}.html').open('xb') as f:f.write(data)
                            write(folder/f'page{number}_receipt.json',{'url':current['url'],'page':number,
                                'captured_at':datetime.now(timezone.utc).isoformat(),'fragment_sha256':sha(data),'http_status':200,
                                'http_body_hash_not_archived':current['http_body_sha256'],'http_body_bytes':current['http_body_bytes'],
                                'raw_http_body_archived':False})
                            parsed=baseline.list_page(current['fragment'],number,ticker,total,seen);write(folder/f'page{number}.json',parsed)
                            total=parsed['coverage']['reported_total'];seen.extend(parsed['article_ids']);query_articles.extend(parsed['articles'])
                            previous=current['fragment']
                        if len(seen)==total:break
                    if (len(seen)!=total or len(guard.business)!=math.ceil(total/20)
                            or [r['status'] for r in guard.responses]!=[200]*number):raise ValueError('COMPLETE_QUERY_AND_RECEIPTS_REQUIRED')
                    guard.check()
                guard.check();owner.check()
                # Commit only after clean context shutdown, never before it.
                completed.append(ticker);articles.extend({**a,'query_ticker':ticker} for a in query_articles)
                write(folder/'complete_query.json',{'ticker':ticker,'reported_total':total,'article_ids':seen,
                    'query_exhausted_in_session':True,'historical_event_coverage_certified':False})
            finally:
                write(folder/'business_requests.json',guard.business);write(folder/'business_responses.json',guard.responses)
        if completed!=list(baseline.PILOT) or owner.launches!=1 or owner.contexts!=3 or owner.closed_contexts!=3:
            raise ValueError('ONE_BROWSER_THREE_COMPLETED_CLOSED_CONTEXTS_REQUIRED')
        result['status']=PASS
    except KeyboardInterrupt:result.update(status='CANCELLED_REVIEW_REQUIRED',stop_reason='USER_INTERRUPT_NO_REPLAY')
    except Exception as exc:
        result.update(source_stopped=True,stop_reason=next((g.stop_reason for g in guards if g.stop_reason),None) or str(exc),error_type=type(exc).__name__)
    finally:
        try:owner.close()
        except Exception as exc:result.update(status='STOPPED_SHARED_BROWSER_CLEANUP_REVIEW_REQUIRED',source_stopped=True,stop_reason=str(exc))
        try:check();shared.check()
        except Exception as exc:result.update(status='STOPPED_INPUT_OR_BUDGET_REVIEW_REQUIRED',source_stopped=True,stop_reason=str(exc))
        with timings.span('final_artifacts'):
            merged={}
            for a in articles:
                aid=a['provider_article_id']
                row=merged.setdefault(aid,{'provider_article_id':aid,'url':a['url'],'titles':[],'query_tickers':[],
                    'detail_reusable_from_cache':aid in reusable,'detail_fetch_authorized':False,'event_identity_verified':False})
                for field,value in [('titles',a['title']),('query_tickers',a['query_ticker'])]:
                    if value not in row[field]:row[field].append(value)
            write(output/'deduplicated_query_articles.json',list(merged.values()))
            result.update(browser_launch_attempts=owner.launch_attempts,browser_launches=owner.launches,fresh_contexts=owner.contexts,
                closed_contexts=owner.closed_contexts,completed_tickers=completed,business_requests=shared.business,
                context_request_attempts=shared.attempts,assets_attempts=sum(g.assets for g in guards),
                external_resources_blocked=sum(g.external_blocked for g in guards),unique_provider_IDs=len(merged),
                reusable_cached_detail_IDs=sum(r['detail_reusable_from_cache'] for r in merged.values()),
                new_candidate_IDs=sum(not r['detail_reusable_from_cache'] for r in merged.values()),elapsed_seconds=clock()-shared.started)
            result.update(protected_hash_checker='COMPILED_PATH_FULL_SHA256_EVERY_CALL',
                protected_hash_checks_attempted=checks['attempted'],protected_hash_checks_completed=checks['completed'],
                protected_files_per_check=len(protected),hash_plan_compilations=int(plan is not None),
                hash_calibration_completed_pairs=sum(len(r['seconds'])==2 for r in calibration))
            write(output/'hash_calibration.json',calibration)
            write(output/'result.json',result)
            write(output/'checkpoint.json',{'status':result['status'],'resumable':False,'completed_tickers':completed,'old_runs_never_resumed':True})
        write(output/'timings.json',timings.snapshot())
    return result


def package(output,archive,*,clock=time.monotonic):
    """Measure actual seal/hash/ZIP operation;sidecar deliberately outside immutable state."""
    output,archive=Path(output),Path(archive);started=clock();seal(output,archive,artifact_type=TYPE);elapsed=clock()-started
    receipt=archive.with_suffix('.packaging.json')
    write(receipt,{'state_manifest_sha256':sha((output/'manifest.json').read_bytes()),'ZIP_sha256':sha(archive.read_bytes()),
        'seal_hash_and_ZIP_seconds':elapsed,'ZIP_bytes':archive.stat().st_size,'source_requests':0,
        'semantics':'Separate finalization measurement;duration excludes its own receipt/ZIP hash reading and cannot be embedded in the archive being timed.'})
    return receipt
