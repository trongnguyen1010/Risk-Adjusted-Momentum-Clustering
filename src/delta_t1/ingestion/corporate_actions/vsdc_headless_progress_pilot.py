"""Headless2s three-query access pilot with readable event-driven progress;frozen54V2 unchanged."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

from . import vsdc_shared_browser_pilot as previous
from . import vsdc_fasthash_pilot as latest

baseline,mbs=previous.baseline,previous.mbs
read,write,sha,hashes,seal=previous.read,previous.write,previous.sha,previous.hashes,previous.seal
verify_artifact,Timings=previous.verify_artifact,previous.Timings
CONFIG='configs/data/corporate_actions/vsdc_headless_progress2s_pilot_v1.json'
TYPE='vsdc-headless-progress2s-three-query-pilot-v1'
PREP_TYPE='vsdc-headless-progress2s-preparation-v1'
PASS='PASS_HEADLESS_PROGRESS2S_PILOT_REVIEW_REQUIRED'
PARENTS={
    'fasthash_preparation':('data/corporate_actions/work/vsdc_fasthash2s_preparation_20261103_v1',
        '190e6ae059d3eb27bbdbe11d49e5e1b5e95aee84086a5814b4c70aa9256e285f',latest.PREP_TYPE),
    'fasthash_run':('data/corporate_actions/work/vsdc_fasthash2s_pilot_v1/run-20261103T091151545258Z/state',
        '5c7e3cec6bbf12602b61fb033d1166fd8cfd3723558adba99f1072f1b72dfee2',latest.TYPE),
    'fasthash_review':('data/corporate_actions/work/vsdc_fasthash2s_live_review_20261103_v1',
        '85a6d89dcf3423b7d20bcc86968ad4f48f3fc654773248a57adfad942d6adfb4','vsdc-fasthash2s-source-pilot-offline-live-review-v1'),
    'fasthash_validation':('data/corporate_actions/work/vsdc_fasthash2s_live_review_validation_20261103_v1',
        'ef33ae6e918a03d7f0f94fb821fd2ac403e4f4092249d9af158791d7a458f633','vsdc-fasthash2s-source-pilot-offline-live-review-validation-v1')}


def contract():
    return {**previous.contract(),'stage':'VSDC_HEADLESS_PROGRESS2S_PILOT_PREPARATION_V1',
        'output_base':'data/corporate_actions/work/vsdc_headless_progress2s_pilot_v1',
        'preparation':'data/corporate_actions/work/vsdc_headless_progress2s_preparation_20261103_v1',
        'headless':True,'progress':'READABLE_EVENTS_AND_JSONL_PER_PAGE_AND_VALIDATED_QUERY',
        'hash_checker':'ORIGINAL_FULL_SHA256_EVERY_CHECK'}


def validate(config):
    if config!=contract():raise ValueError('EXACT_HEADLESS2S_PROGRESS_THREE_QUERY_CONTRACT_REQUIRED')


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_headless_progress_pilot.py',
        'scripts/corporate_actions/prepare_vsdc_headless_progress2s_pilot_v1.py',
        'scripts/corporate_actions/collect_vsdc_headless_progress2s_pilot_v1.py']
    return {**latest.runtime(project),**{n:sha((project/n).read_bytes()) for n in names}}


def parents(project):
    _,prep=latest.load_preparation(project)
    for name,(rel,digest,kind) in PARENTS.items():
        folder=project/rel
        if sha((folder/'manifest.json').read_bytes())!=digest:raise ValueError('HEADLESS_PARENT_CHANGED: '+name)
        verify_artifact(folder,{kind})
    if read(project/PARENTS['fasthash_review'][0]/'review.json')['status']!='PASS_FASTHASH_DATA_SOURCE_AND_INTEGRITY_SMALL_END_TO_END_GAIN':
        raise ValueError('LATEST_OFFLINE_REVIEW_REQUIRED')
    return prep


def load_preparation(project):
    config=read(project/CONFIG);validate(config);parents(project)
    prep=project/config['preparation'];verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('HEADLESS_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    if (len(read(prep/'reusable_detail_provider_ids.json'))!=27731
            or len(read(prep/'known_discovery_provider_ids.json'))!=28276):raise ValueError('CACHE_BASELINE_CHANGED')
    return config,prep


def prepare(project):
    project=Path(project).resolve();config=read(project/CONFIG);validate(config);old=parents(project)
    output=project/config['preparation']
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    protected=read(old/'protected_old_files.json')
    for rel,_,_ in PARENTS.values():
        folder=project/rel
        for name in ['manifest.json',*read(folder/'manifest.json')['files']]:
            path=folder/name;protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    protected.update(latest.runtime(project));output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','known_discovery_provider_ids.json','cache_policy.json','pilot_plan.json']:
        (output/name).write_bytes((old/name).read_bytes())
    write(output/'experiment.json',{'kind':'HEADLESS2S_READABLE_PROGRESS_ACCESS_PILOT',
        'scope':['A32','AAA','IDJ'],'expected_business_requests':7,'expected_query_rows':{'A32':35,'AAA':51,'IDJ':24},
        'baseline_headed_shared_review':{'path':latest.PARENTS['shared_review'][0],
            'manifest_sha256':latest.PARENTS['shared_review'][1]},
        'hash_checker':'Original full-hash callback,no candidate optimization/calibration in this pilot',
        'browser_launch':{'channel':'chrome','headless':True,'custom_UA_or_headers_or_profile':False},
        'browser_lifecycle':'Oneprocess,three sequential fresh closed nonpersistent contexts',
        'progress':{'events':['START','QUERY_START','PAGE_START','PAGE_COMPLETE','QUERY_VALIDATED','FINAL'],
            'logs':['progress.log','progress.jsonl'],'total_queries':3,'batch_index':1,'total_batches':1,
            'commit':'Increment only after full query validated,persisted and context closed',
            'ETA':'Approximate average elapsed per completed query;none before first completion,not a bulk forecast'},
        'acceptance':'Headless launch metadata,three full consistent lists/data/JS/cache,allbusiness200,min2s,no source/access boundaries;progress must match validated completion order and final status.',
        'on_error':'STOP,no retries/headed fallback/custom identity or challenge handling',
        'expected_new_query_completion_credit':0,'bulk_runner_changed':False,'details':False,
        'limits':'New source access mode requires live user pilot;no claim headless access or54batch support before review. Timing differences are not causal speed evidence.'})
    write(output/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,'browser_launches':0,
        'readiness':mbs.old.readiness(config),'purpose':'Terminal observability without opening visible Chrome windows',
        'short_pilot_resumable':False,'existing54_V2_pause_continuation_unchanged':True,
        'next_step':'User-run once,offline review headless access/data/progress before preparing54batch headless version with pause/continuation'})
    write(output/'protected_old_files.json',protected);write(output/'runtime.json',runtime(project))
    write(output/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(output)});load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','source_requests':0,'headless':True,'tickers':list(baseline.PILOT),
        'protected_old_files':len(protected),'output':str(output)}


class HeadlessOwner(previous.BrowserOwner):
    def ensure(self,guard):
        if self.active is not None:raise ValueError('SEQUENTIAL_FRESH_CONTEXTS_REQUIRED')
        self.guard=guard;self.check()
        if self.browser is not None:
            if not self.browser.is_connected():raise ValueError('SHARED_BROWSER_CLOSED_NO_RELAUNCH')
            return
        if self.launch_attempts:raise ValueError('NO_BROWSER_RELAUNCH_OR_RETRY')
        from playwright.sync_api import sync_playwright
        with self.timings.span('playwright_start'):self.manager=sync_playwright().start()
        self.launch_attempts+=1
        with self.timings.span('browser_launch'):
            self.browser=self.manager.chromium.launch(channel='chrome',headless=True,timeout=guard.timeout_ms())
        self.launches+=1;self.browser.on('disconnected',self.disconnected);self.check()


def duration(seconds):
    seconds=max(0,int(seconds));return f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}'


class Progress:
    """Event-only progress:no polling;no increment for an in-flight or failed query."""
    def __init__(self,output,tickers,timings,clock=time.monotonic,emit=print):
        self.output,self.tickers,self.timings,self.clock,self.emit=Path(output),tuple(tickers),timings,clock,emit
        if not self.tickers or len(set(self.tickers))!=len(self.tickers):raise ValueError('PROGRESS_UNIQUE_NONEMPTY_SCOPE_REQUIRED')
        self.started=clock();self.completed=0;self.active=None
    def record(self,event,*,page=None,total_pages=None,status=None):
        with self.timings.span('progress_ui',self.active):
            elapsed=max(0,self.clock()-self.started);total=len(self.tickers)
            remaining=total-self.completed
            eta=(elapsed/self.completed*remaining if self.completed else None)
            row={'event':event,'completed_queries':self.completed,'total_queries':total,'remaining_queries':remaining,
                'percent':100*self.completed/total,'ticker':self.active,'page':page,'total_pages':total_pages,
                'batch_index':1,'total_batches':1,'elapsed_seconds':elapsed,'ETA_seconds':eta,'status':status}
            label={'START':'Bắt đầu pilot chạy ẩn','QUERY_START':'Đang thu','PAGE_START':'Đang tải trang',
                'PAGE_COMPLETE':'Đã kiểm tra trang','QUERY_VALIDATED':'Đã kiểm tra mã','FINAL':'Kết thúc'}[event]
            line=f'[{self.completed}/{total} mã | {row["percent"]:.1f}% | Còn {remaining}] {label}'
            if self.active:line+=f' {self.active}'
            if page is not None:line+=f' | Trang {page}/'+(str(total_pages) if total_pages is not None else '?')
            line+=f' | Batch 1/1 | Đã chạy {duration(elapsed)} | ETA tạm tính '+(duration(eta) if eta is not None else 'đang tính')
            if status:line+=' | '+status
            with (self.output/'progress.jsonl').open('a',encoding='utf8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
            with (self.output/'progress.log').open('a',encoding='utf8') as stream:stream.write(line+'\n')
            self.emit(line,flush=True)
    def begin(self,ticker):
        if self.active is not None or self.completed>=len(self.tickers) or ticker!=self.tickers[self.completed]:
            raise ValueError('PROGRESS_QUERY_ORDER_MISMATCH')
        self.active=ticker;self.record('QUERY_START')
    def page(self,ticker,number,total_pages=None,*,complete=False):
        if ticker!=self.active or number<1:raise ValueError('PROGRESS_ACTIVE_QUERY_MISMATCH')
        self.record('PAGE_COMPLETE' if complete else 'PAGE_START',page=number,total_pages=total_pages)
    def done(self,ticker):
        if ticker!=self.active:raise ValueError('PROGRESS_COMPLETION_MISMATCH')
        self.completed+=1;self.record('QUERY_VALIDATED');self.active=None
    def finish(self,status):
        if status==PASS and (self.completed!=len(self.tickers) or self.active is not None):raise ValueError('PROGRESS_PASS_WITH_INCOMPLETE_QUERIES')
        self.record('FINAL',status=status)


def run(project,output,*,dry_run=False,owner_factory=HeadlessOwner,clock=time.monotonic,emit=print):
    project,output=Path(project).resolve(),Path(output).resolve();timings=Timings(clock)
    with timings.span('preflight'):config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    ready=mbs.old.readiness(config)
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED','source_requests':0,
        'browser_launched':False,'pilot_tickers':list(baseline.PILOT),'planned_browser_launches':1,'planned_fresh_contexts':3,'headless':True,'readiness':ready}
    output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','known_discovery_provider_ids.json','cache_policy.json',
                 'pilot_plan.json','experiment.json','protected_old_files.json']:
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config)
    with timings.span('runtime_hash'):write(output/'runtime.json',runtime(project))
    write(output/'environment.json',ready)
    write(output/'input_provenance.json',{'preparation':str(prep),'manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'capture_kind':'PUBLIC_RENDERED_QUERY_FRAGMENTS_NOT_RAW_HTTP'})
    protected=read(prep/'protected_old_files.json')
    def check():
        with timings.span('protected_hash'):mbs.old.protected_check(project,protected)
    owner=owner_factory(timings,config);shared=baseline.SharedBudget(config,clock);guards=[];completed=[];articles=[]
    reporter=Progress(output,baseline.PILOT,timings,clock,emit);reporter.record('START')
    reusable=set(read(prep/'reusable_detail_provider_ids.json'));result={'status':'STOPPED_SHARED_BROWSER_OR_SOURCE_REVIEW_REQUIRED',
        'resumable':False,'bulk_collection_ready':False,'business_interval_seconds':2,'source_stopped':False,'detail_requests':0,
        'canonical_fields_applied':0,'normalized_observations':0,'pit_or_identity_promoted':False,'openai_api_calls':0}
    try:
        if not ready['ready']:raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
        for ticker in baseline.PILOT:
            shared.check();check();reporter.begin(ticker);folder=output/ticker;folder.mkdir();(folder/'network_ledger.jsonl').touch()
            local={**config,'ticker':ticker,'url':baseline.search_url(ticker),'max_seconds':config['max_query_seconds'],
                'max_context_request_attempts':config['max_context_per_query'],'max_asset_attempts':config['max_assets_per_query']}
            guard=baseline.Guard(local,folder,check,clock,shared);guards.append(guard)
            try:
                with owner.driver(local,guard) as driver:
                    if shared.last is not None:
                        with timings.span('pacing',ticker):driver.pace(max(0,2-(clock()-shared.last)))
                    reporter.page(ticker,1)
                    with timings.span('browser_first',ticker):current=driver.first();guard.check()
                    write(folder/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,'default_identity':True,
                        'TLS_ignore_errors':False,'cookie_auth_exported':False,'headless':True,'shared_process':True,'fresh_context_ordinal':driver.ordinal})
                    with timings.span('archive_parse',ticker):write(folder/'fresh_source_contract.json',baseline.source_contract(current['scope_html'],ticker))
                    seen=[];query_articles=[];total=None;previous=''
                    for number in range(1,5):
                        if number>1:
                            reporter.page(ticker,number,math.ceil(total/20));check()
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
                        reporter.page(ticker,number,math.ceil(total/20),complete=True)
                        if len(seen)==total:break
                    if (len(seen)!=total or len(guard.business)!=math.ceil(total/20)
                            or [r['status'] for r in guard.responses]!=[200]*number):raise ValueError('COMPLETE_QUERY_AND_RECEIPTS_REQUIRED')
                    guard.check()
                guard.check();owner.check()
                # Commit only after clean context shutdown, never before it.
                write(folder/'complete_query.json',{'ticker':ticker,'reported_total':total,'article_ids':seen,
                    'query_exhausted_in_session':True,'historical_event_coverage_certified':False})
                completed.append(ticker);articles.extend({**a,'query_ticker':ticker} for a in query_articles);reporter.done(ticker)
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
            result.update(headless=True,progress_completed_queries=reporter.completed,progress_total_queries=len(baseline.PILOT),
                browser_launch_attempts=owner.launch_attempts,browser_launches=owner.launches,fresh_contexts=owner.contexts,
                closed_contexts=owner.closed_contexts,completed_tickers=completed,business_requests=shared.business,
                context_request_attempts=shared.attempts,assets_attempts=sum(g.assets for g in guards),
                external_resources_blocked=sum(g.external_blocked for g in guards),unique_provider_IDs=len(merged),
                reusable_cached_detail_IDs=sum(r['detail_reusable_from_cache'] for r in merged.values()),
                new_candidate_IDs=sum(not r['detail_reusable_from_cache'] for r in merged.values()),elapsed_seconds=clock()-shared.started)
            write(output/'result.json',result)
            write(output/'checkpoint.json',{'status':result['status'],'resumable':False,'completed_tickers':completed,'old_runs_never_resumed':True})
        reporter.finish(result['status'])
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
