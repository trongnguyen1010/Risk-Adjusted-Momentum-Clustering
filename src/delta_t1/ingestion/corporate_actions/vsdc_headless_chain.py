"""Fixed54 headless collector with verified user pause,immutable query checkpoints and readable progress."""
from bisect import bisect_right
from collections import deque
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import time

from . import vsdc_resumable_chain as prior
from . import vsdc_headless_progress_pilot as pilot

base=prior.base
mbs=base.mbs
read,write,sha,hashes=prior.read,prior.write,prior.sha,prior.hashes
Pause,pause_signals,execution_lock=prior.Pause,prior.pause_signals,prior.execution_lock
flatten,query_definition,query_folder=prior.flatten,prior.query_definition,prior.query_folder
initial_totals,check_totals,ledger_cost=prior.initial_totals,prior.check_totals,prior.ledger_cost
verify_zip=prior.verify_zip
Guard,source_contract,list_page,search_url=base.Guard,base.source_contract,base.list_page,base.search_url
ids_hash=base.ids_hash
deduplicate=base.deduplicate
CONFIG='configs/data/corporate_actions/vsdc_remaining54_headless_v3.json'
OUTPUT='data/corporate_actions/work/vsdc_remaining54_headless_v3'
PREP='data/corporate_actions/work/vsdc_remaining54_headless_preparation_20261103_v3'
TYPE='vsdc-remaining54-headless-progress-pause-segment-v3'
PREP_TYPE='vsdc-remaining54-headless-progress-preparation-v3'
PAUSED,COMPLETE,STOPPED=prior.PAUSED,prior.COMPLETE,prior.STOPPED
PARENTS={
    'V2_preparation':('data/corporate_actions/work/vsdc_remaining54_resumable_preparation_20261103_v2',
        '4d51178c54ffa1fd1952e91479403cf80eb53180584870884e3b4f0512773648',prior.PREP_TYPE),
    'headless_preparation':('data/corporate_actions/work/vsdc_headless_progress2s_preparation_20261103_v1',
        '72a13e801f88a3c7fb4e9bb415b8f32c86bd832fbba5a07e821e2e49d3e5db90',pilot.PREP_TYPE),
    'headless_run':('data/corporate_actions/work/vsdc_headless_progress2s_pilot_v1/run-20261103T093821365887Z/state',
        'e218cf26d9da237c1708c57fee73b164335588e3e9dc6f742b33a2f84a487f4f',pilot.TYPE),
    'headless_review':('data/corporate_actions/work/vsdc_headless_progress2s_live_review_20261103_v1',
        '1c9bc2413cb2b162fb9da75b34a708a94a4cd8c637567648a85fc15067bd16fc','vsdc-headless-progress2s-offline-live-review-v1'),
    'headless_validation':('data/corporate_actions/work/vsdc_headless_progress2s_live_review_validation_20261103_v1',
        '28888e4c7a4d93f092fe9eb174f421271dc293f208f86fbd3d8b74a77e7fdec7','vsdc-headless-progress2s-offline-live-review-validation-v1')}


def caps():
    return {**base.contract(),'stage':'VSDC_REMAINING54_HEADLESS_QUERY_V3','output_base':OUTPUT,
        'preparation':PREP,'headless':True}


def contract():
    return {**prior.contract(),'stage':'VSDC_REMAINING54_HEADLESS_PROGRESS_PAUSE_PREPARATION_V3',
        'output_base':OUTPUT,'preparation':PREP,'scope_and_source_caps':caps(),
        'import_V2_run':False,'browser_lifecycle':'FRESH_HEADLESS_CHROME_PER_QUERY',
        'progress':'EVENT_LOGS_PER_PAGE_AND_VALIDATED_QUERY','ETA_warmup_queries':5,'ETA_window_queries':20,
        'hash_checker':'ORIGINAL_FULL_SHA256_EVERY_CHECK'}


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_headless_chain.py',
        'scripts/corporate_actions/prepare_vsdc_remaining54_headless_v3.py',
        'scripts/corporate_actions/collect_vsdc_remaining54_headless_v3.py']
    return {**pilot.runtime(project),**{name:sha((project/name).read_bytes()) for name in names}}


def legacy_output_gate(project):
    legacy=project/prior.contract()['output_base']
    if legacy.exists() and (any(legacy.glob('run-*')) or (legacy/'active.lock').exists()):
        raise ValueError('V2_OUTPUT_PRESENT_REVIEW_REQUIRED_NO_AUTO_IMPORT')


def parents(project):
    _,headless=pilot.load_preparation(project)
    for name,(rel,digest,kind) in PARENTS.items():
        folder=project/rel
        if sha((folder/'manifest.json').read_bytes())!=digest:raise ValueError('V3_PARENT_CHANGED: '+name)
        base.verify_artifact(folder,{kind})
    if read(project/PARENTS['headless_review'][0]/'review.json')['status']!='PASS_BOUNDED_HEADLESS_ACCESS_SAME_DATA_AND_READABLE_PROGRESS':
        raise ValueError('REVIEWED_HEADLESS_ACCESS_PASS_REQUIRED')
    legacy_output_gate(project)
    return headless


def load_preparation(project):
    config=read(project/CONFIG)
    if config!=contract():raise ValueError('EXACT_HEADLESS54_V3_CONTRACT_REQUIRED')
    parents(project);prep=project/config['preparation'];base.verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('V3_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    base.validate_selection(read(prep/'selected_batches.json'),read(prep/'query_inventory_before_chain.json'))
    if len(read(prep/'reusable_detail_provider_ids.json'))!=27731 or len(read(prep/'known_discovery_provider_ids.json'))!=28276:
        raise ValueError('V3_CACHE_BASELINE_CHANGED')
    return config,prep


def prepare(project):
    project=Path(project).resolve();config=read(project/CONFIG)
    if config!=contract():raise ValueError('EXACT_HEADLESS54_V3_CONTRACT_REQUIRED')
    headless=parents(project);old=project/PARENTS['V2_preparation'][0];output=project/PREP
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    protected=read(headless/'protected_old_files.json')
    for rel,_,_ in PARENTS.values():
        folder=project/rel
        for name in ['manifest.json',*read(folder/'manifest.json')['files']]:
            path=folder/name;protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    protected.update(runtime(project));output.mkdir(parents=True)
    for name in ('selected_batches.json','query_inventory_before_chain.json','reusable_detail_provider_ids.json',
                 'known_discovery_provider_ids.json','cache_policy.json'):
        (output/name).write_bytes((old/name).read_bytes())
    write(output/'protected_old_files.json',protected);write(output/'runtime.json',runtime(project))
    write(output/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,'browser_launches':0,
        'batches':54,'queries':1073,'estimated_list_requests':2839,'large_HOLD_outside':7,
        'archived_exhausted_outside':414,'unverified_outside':4,'new_completion_credit':0,
        'readiness':mbs.old.readiness(caps()),
        'browser':'Headless Chrome fresh process/context per query,preserving V2 isolation;no visible-window or headed fallback',
        'progress':'Readable log and JSONL,page events;global validated count only after sealed query passes offline reparse',
        'ETA':'None before5 validated durations;mean of last20,subtract current in-flight time,active time excludes user pauses',
        'continuation':'Only sealed verified user-pause lineage;new segment,no retries for source/error/crash states',
        'query_artifact':'Reuse generic immutable list-batch-v1 structure with exact V3 headless config/runtime plus headless validator',
        'budgets':'Same cumulative global/batch/query caps as V2,including discarded partial attempts',
        'next_step':'User runs once locally,may pause/continue via same CLI;offline ZIP review when complete or stopped'})
    write(output/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(output)});load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','batches':54,'queries':1073,'headless':True,'interval_seconds':2,
        'protected_old_files':len(protected),'source_requests':0,'output':str(output)}


class HeadlessDriver(base.Driver):
    """Same route/response/parse handlers as V2;launch mode hidden and cleanup fails closed."""
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        try:
            self.manager=sync_playwright().start()
            self.browser=self.manager.chromium.launch(channel='chrome',headless=True,timeout=self.guard.timeout_ms())
            self.browser.on('disconnected',self._disconnected)
            self.context=self.browser.new_context(ignore_https_errors=False,accept_downloads=False,service_workers='block')
            self.context.route('**/*',self._route);self.context.on('response',self._response)
            self.context.on('requestfailed',self._failed);self.context.route_web_socket('**/*',self._websocket)
            self.page=self.context.new_page();self.context.on('page',self._popup);self.page.on('dialog',self._dialog)
            self.version=self.browser.version;return self
        except BaseException:self.__exit__(None,None,None);raise
    def _disconnected(self,*args):
        if not self.closing:self.guard.fail('HEADLESS_BROWSER_DISCONNECTED')
    def __exit__(self,*args):
        self.closing=True;failed=False
        for item in (self.context,self.browser):
            if item is not None:
                try:item.close()
                except Exception:failed=True
        if self.manager is not None:
            try:self.manager.stop()
            except Exception:failed=True
        if failed:
            self.guard.fail('HEADLESS_QUERY_CLEANUP_FAILED');raise ValueError('HEADLESS_QUERY_CLEANUP_FAILED')


class Progress:
    def __init__(self,output,selected,completed,durations,started,old_active,clock,emit):
        self.output,self.order,self.clock,self.emit=Path(output),flatten(selected),clock,emit
        self.started,self.old_active=started,old_active;self.completed=len(completed);self.active=None;self.active_started=None
        self.samples=deque(durations[-20:],maxlen=20);self.batch_index={b['batch_id']:i+1 for i,b in enumerate(selected)}
        self.ends=[];end=0
        for batch in selected:end+=len(batch['tickers']);self.ends.append(end)
        self.page_total=None
    def record(self,event,*,scope=None,page=None,total_pages=None,status=None):
        current=scope or self.active or (self.order[min(self.completed,len(self.order)-1)] if self.order else None)
        now=self.clock();remaining=len(self.order)-self.completed
        current_seconds=max(0,now-self.active_started) if self.active_started is not None else 0
        mean=sum(self.samples)/len(self.samples) if self.samples else None
        eta=0 if remaining==0 else (max(1,mean*remaining-current_seconds) if len(self.samples)>=5 else None)
        row={'event':event,'completed_queries':self.completed,'total_queries':len(self.order),'remaining_queries':remaining,
            'percent':100*self.completed/len(self.order),'ticker':current['ticker'] if current else None,
            'batch_id':current['batch_id'] if current else None,'batch_index':self.batch_index[current['batch_id']] if current else 0,
            'total_batches':len(self.ends),'completed_batches':bisect_right(self.ends,self.completed),
            'page':page,'total_pages':total_pages,'active_elapsed_seconds':self.old_active+max(0,now-self.started),
            'current_query_elapsed_seconds':current_seconds,'ETA_seconds':eta,'ETA_sample_count':len(self.samples),
            'ETA_mean_completed_query_seconds':mean,'ETA_warmup_queries':5,'status':status}
        line=progress_line(row)
        with (self.output/'progress.jsonl').open('a',encoding='utf8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        with (self.output/'progress.log').open('a',encoding='utf8') as stream:stream.write(line+'\n')
        self.emit(line,flush=True)
    def begin(self,index,started):
        if self.active is not None or index!=self.completed:raise ValueError('PROGRESS_PREFIX_ORDER_CHANGED')
        self.active=self.order[index];self.active_started=started;self.page_total=None;self.record('QUERY_START')
    def page_start(self,number):self.record('PAGE_START',page=number,total_pages=self.page_total)
    def page_complete(self,number,pages):self.page_total=pages;self.record('PAGE_COMPLETE',page=number,total_pages=pages)
    def done(self,duration):
        self.completed+=1;self.samples.append(duration);self.active_started=None;self.record('QUERY_VALIDATED');self.active=None
    def batch_done(self,bid):self.record('BATCH_VALIDATED',scope={'batch_id':bid,'ticker':None})
    def finish(self,status):self.record('FINAL',status=status)


def progress_line(row):
    label={'START':'Bắt đầu/tiếp tục chạy ẩn','QUERY_START':'Đang thu','PAGE_START':'Đang tải trang',
        'PAGE_COMPLETE':'Đã kiểm tra trang','QUERY_VALIDATED':'Đã kiểm tra mã',
        'BATCH_VALIDATED':'Đã kiểm tra batch','FINAL':'Kết thúc lượt'}[row['event']]
    line=f'[{row["completed_queries"]}/{row["total_queries"]} mã | {row["percent"]:.1f}% | Còn {row["remaining_queries"]}] {label}'
    if row['ticker']:line+=' '+row['ticker']
    line+=f' | Batch {row["batch_index"]}/{row["total_batches"]}'
    if row['page'] is not None:line+=f' | Trang {row["page"]}/'+(str(row['total_pages']) if row['total_pages'] is not None else '?')
    line+=' | Đã chạy '+pilot.duration(row['active_elapsed_seconds'])+' | ETA tạm tính '+(pilot.duration(row['ETA_seconds']) if row['ETA_seconds'] is not None else 'đang lấy mẫu (5 mã)')
    if row['status']:line+=' | '+row['status']
    return line


class ProgressDriver(prior.PauseDriver):
    def __init__(self,driver,pause,progress):super().__init__(driver,pause);self.progress=progress
    def first(self):self.pause.check();self.progress.page_start(1);return self.driver.first()
    def next_page(self,number,previous):self.pause.check();self.progress.page_start(number);return self.driver.next_page(number,previous)


def validate_batch(folder,archive,definition,config,reusable,known,previous_start):
    if config!=caps():raise ValueError('EXACT_HEADLESS_SOURCE_CAPS_REQUIRED')
    checked=base.validate_batch(folder,archive,definition,config,reusable,known,previous_start)
    if read(folder/'result.json').get('headless') is not True:raise ValueError('HEADLESS_QUERY_RESULT_REQUIRED')
    for ticker in definition['tickers']:
        if read(folder/ticker/'browser.json').get('headless') is not True:raise ValueError('HEADLESS_BROWSER_RECEIPT_REQUIRED')
    return checked


def validate_query(folder,row,known,reusable,project):
    context=read(folder/'context.json')
    if context['scope']!=row or context['headless_query_runtime']!=runtime(project):
        raise ValueError('HEADLESS_QUERY_SCOPE_RUNTIME_CHANGED')
    checked=validate_batch(folder/'state',folder/'query.zip',query_definition(row),caps(),reusable,known,context['previous_start'])
    if read(folder/'state/runtime.json')!=context['headless_query_runtime']:raise ValueError('QUERY_FROZEN_RUNTIME_MISMATCH')
    saved=read(folder/'validation.json')
    if {k:v for k,v in checked.items() if k!='state'}!={k:v for k,v in saved.items() if k!='state'}:
        raise ValueError('QUERY_CHECKPOINT_VALIDATION_MISMATCH')
    return read(folder/'state/deduplicated_query_articles.json')


def validate_progress(state,order,selected,completed_before,durations_before,result,costs):
    rows=mbs.old.rows(state/'progress.jsonl');lines=(state/'progress.log').read_text(encoding='utf8').splitlines()
    if len(rows)!=len(lines) or not rows or rows[0]['event']!='START' or rows[-1]['event']!='FINAL':
        raise ValueError('PROGRESS_LOG_SEQUENCE_MISMATCH')
    count=completed_before;active=None;page_open=None;next_page=1;seen_batches=set();elapsed=-1
    samples=deque(durations_before[-20:],maxlen=20);cost_by_index={a['query_index']:a for a in costs}
    completed=read(state/'completed_queries.json');ends=[];end=0;batch_indices={b['batch_id']:i+1 for i,b in enumerate(selected)}
    for b in selected:end+=len(b['tickers']);ends.append(end)
    for position,(row,line) in enumerate(zip(rows,lines)):
        if set(row)!={'event','completed_queries','total_queries','remaining_queries','percent','ticker','batch_id','batch_index',
                'total_batches','completed_batches','page','total_pages','active_elapsed_seconds','current_query_elapsed_seconds',
                'ETA_seconds','ETA_sample_count','ETA_mean_completed_query_seconds','ETA_warmup_queries','status'}:
            raise ValueError('PROGRESS_SAFE_FIELDS_MISMATCH')
        event=row['event'];scope=active
        if event=='START':
            if position!=0:raise ValueError('DUPLICATE_PROGRESS_START')
        elif event=='QUERY_START':
            if active is not None or count>=len(order):raise ValueError('PROGRESS_QUERY_ORDER_MISMATCH')
            active=order[count];scope=active;page_open=None;next_page=1
        elif event in {'PAGE_START','PAGE_COMPLETE'}:
            if active is None:raise ValueError('PROGRESS_PAGE_WITHOUT_QUERY')
            if event=='PAGE_START':
                if page_open is not None or row['page']!=next_page:raise ValueError('PROGRESS_PAGE_ORDER_MISMATCH')
                page_open=row['page']
            else:
                if page_open!=row['page']:raise ValueError('PROGRESS_UNPAIRED_PAGE_COMPLETION')
                parsed=read(query_folder(state,count)/'state'/active['ticker']/f'page{row["page"]}.json')
                if row['total_pages']!=math.ceil(parsed['coverage']['reported_total']/20):raise ValueError('PROGRESS_PAGE_TOTAL_CHANGED')
                page_open=None;next_page+=1
        elif event=='QUERY_VALIDATED':
            if active is None or page_open is not None or count>=len(completed) or completed[count]!=active:
                raise ValueError('PROGRESS_FALSE_QUERY_COMPLETION')
            attempt=cost_by_index.get(count)
            if not attempt or not attempt['complete']:raise ValueError('PROGRESS_NO_VALIDATED_ATTEMPT')
            query=read(query_folder(state,count)/'state'/active['ticker']/'complete_query.json')
            if next_page-1!=math.ceil(query['reported_total']/20):raise ValueError('PROGRESS_QUERY_PAGE_COUNT_MISMATCH')
            samples.append(attempt['active_seconds']);count+=1
        elif event=='BATCH_VALIDATED':
            bid=row['batch_id'];scope={'batch_id':bid,'ticker':None}
            if active is not None or count not in ends or selected[ends.index(count)]['batch_id']!=bid or bid in seen_batches:
                raise ValueError('PROGRESS_FALSE_BATCH_COMPLETION')
            seen_batches.add(bid)
        elif event=='FINAL':
            if position!=len(rows)-1 or row['status']!=result['status']:raise ValueError('PROGRESS_FINAL_STATUS_MISMATCH')
        else:raise ValueError('UNKNOWN_PROGRESS_EVENT')
        expected_scope=scope or (order[min(count,len(order)-1)] if order else None)
        if row['completed_queries']!=count or row['total_queries']!=len(order) or row['remaining_queries']!=len(order)-count:
            raise ValueError('PROGRESS_PREFIX_COUNT_MISMATCH')
        if (not math.isfinite(row['percent']) or abs(row['percent']-100*count/len(order))>1e-8 or row['total_batches']!=len(selected)
                or row['completed_batches']!=bisect_right(ends,count) or row['batch_id']!=expected_scope['batch_id']
                or row['batch_index']!=batch_indices[expected_scope['batch_id']] or row['ticker']!=expected_scope['ticker']):
            raise ValueError('PROGRESS_SCOPE_PERCENT_OR_BATCH_MISMATCH')
        if not math.isfinite(row['active_elapsed_seconds']) or row['active_elapsed_seconds']<elapsed:
            raise ValueError('PROGRESS_ACTIVE_TIME_NOT_MONOTONIC')
        elapsed=row['active_elapsed_seconds']
        if not math.isfinite(row['current_query_elapsed_seconds']) or row['current_query_elapsed_seconds']<0:
            raise ValueError('PROGRESS_BAD_INFLIGHT_TIME')
        mean=sum(samples)/len(samples) if samples else None
        eta=0 if count==len(order) else (max(1,mean*(len(order)-count)-row['current_query_elapsed_seconds']) if len(samples)>=5 else None)
        if (row['ETA_sample_count']!=len(samples) or row['ETA_mean_completed_query_seconds']!=mean
                or row['ETA_warmup_queries']!=5 or row['ETA_seconds']!=eta):raise ValueError('PROGRESS_ETA_CHANGED')
        if event!='FINAL' and row['status'] is not None:raise ValueError('PROGRESS_PREMATURE_FINAL_STATUS')
        if line!=progress_line(row):raise ValueError('PROGRESS_HUMAN_TEXT_MISMATCH')
        if event=='QUERY_VALIDATED':active=None
    if count!=len(completed) or rows[-1]['completed_queries']!=result['completed_query_count']:
        raise ValueError('PROGRESS_FINAL_PREFIX_MISMATCH')


def seal_run(state):
    archive=state.parent/'delta-vsdc-headless54.zip'
    base.seal(state,archive,artifact_type=TYPE);verify_zip(state,archive,TYPE)
    return archive


def acquire_query(project,folder,definition,config,prep,shared,reusable,known,check_old,driver_factory,clock,progress=None):
    folder.mkdir(parents=True);guards=[];completed=[];articles=[];seq=0
    write(folder/'batch_plan.json',definition);write(folder/'chain_config.json',config)
    write(folder/'runtime.json',runtime(project))
    write(folder/'input_provenance.json',{'preparation_manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'known_before_batch_sha256':ids_hash(known),'reusable_detail_IDs_sha256':ids_hash(reusable),
        'previous_business_start':shared.previous_start,'capture_kind':'PUBLIC_RENDERED_FRAGMENTS_NOT_RAW_HTTP'})
    def checkpoint(event,ticker=None):
        nonlocal seq
        seq+=1;path=folder/'checkpoints';path.mkdir(exist_ok=True)
        write(path/f'{seq:03}.json',{'event':event,'ticker':ticker,'completed_tickers':list(completed),
            'batch_business_requests':shared.business-shared.batch_business_start,
            'batch_context_attempts':shared.attempts-shared.batch_attempt_start,'resumable':False})
    result={'status':'STOPPED_SOURCE_OR_LAYOUT','batch_id':definition['batch_id'],'resumable':False,'source_stopped':False,
        'detail_requests':0,'canonical_fields_applied':0,'browser_launches':0,'business_interval_seconds':2,'headless':True}
    try:
        for ticker in definition['tickers']:
            shared.check();check_old();checkpoint('QUERY_START',ticker)
            query=folder/ticker;query.mkdir();(query/'network_ledger.jsonl').touch()
            local={**config,'ticker':ticker,'url':search_url(ticker),'max_seconds':config['max_query_seconds'],
                'max_context_request_attempts':config['max_context_per_query'],'max_asset_attempts':config['max_assets_per_query']}
            guard=Guard(local,query,check_old,clock,shared);guards.append(guard)
            try:
                with driver_factory(local,guard) as driver:
                    result['browser_launches']+=1
                    if shared.last is not None:driver.pace(max(0,2-(clock()-shared.last)))
                    current=driver.first();guard.check()
                    write(query/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,
                        'default_identity':True,'TLS_ignore_errors':False,'cookie_auth_exported':False,'headless':True})
                    write(query/'fresh_source_contract.json',source_contract(current['scope_html'],ticker))
                    seen=[];query_articles=[];total=None;previous=''
                    for number in range(1,21):
                        if number>1:
                            check_old();driver.pace(max(0,2-(clock()-shared.last)))
                            current=driver.next_page(number,previous);guard.check()
                        if current['url']!=local['url'] or current['http_status']!=200:raise ValueError('EXACT_QUERY_HTTP200_REQUIRED')
                        data=mbs.old.fragment_bytes(current['fragment'],2000000)
                        raw=query/'rendered_html';raw.mkdir(exist_ok=True)
                        with (raw/f'page{number}.html').open('xb') as f:f.write(data)
                        write(query/f'page{number}_receipt.json',{'url':current['url'],'page':number,
                            'captured_at':datetime.now(timezone.utc).isoformat(),'fragment_sha256':sha(data),'http_status':200,
                            'http_body_hash_not_archived':current['http_body_sha256'],'http_body_bytes':current['http_body_bytes'],
                            'raw_http_body_archived':False})
                        parsed=list_page(current['fragment'],number,ticker,total,seen);write(query/f'page{number}.json',parsed)
                        total=parsed['coverage']['reported_total'];seen.extend(parsed['article_ids']);query_articles.extend(parsed['articles'])
                        previous=current['fragment']
                        if progress is not None:progress.page_complete(number,math.ceil(total/20))
                        if len(seen)==total:break
                    if len(seen)!=total or len(guard.business)!=math.ceil(total/20) or [r['status'] for r in guard.responses]!=[200]*number:
                        raise ValueError('FULL_QUERY_AND_BUSINESS_RECEIPTS_REQUIRED')
                    guard.check()
                guard.check()
                completed.append(ticker);articles.extend({**a,'query_ticker':ticker} for a in query_articles)
                write(query/'complete_query.json',{'ticker':ticker,'reported_total':total,'article_ids':seen,
                    'query_exhausted_in_session':True,'historical_event_coverage_certified':False})
                checkpoint('QUERY_LIST_COMPLETE',ticker)
            finally:
                write(query/'business_requests.json',guard.business);write(query/'business_responses.json',guard.responses)
        check_old();shared.check();result['status']='PASS_SOURCE_BATCH_REQUIRES_AUTOMATED_VALIDATION'
    except KeyboardInterrupt:result.update(status='CANCELLED_NO_REPLAY',stop_reason='USER_INTERRUPT')
    except Exception as exc:
        result.update(status='STOPPED_SOURCE_OR_LAYOUT',source_stopped=True,
            stop_reason=next((g.stop_reason for g in guards if g.stop_reason),None) or str(exc),error_type=type(exc).__name__)
    finally:
        merged=deduplicate(articles,reusable,known);write(folder/'deduplicated_query_articles.json',merged)
        result.update(completed_tickers=completed,business_requests=shared.business-shared.batch_business_start,
            context_attempts=shared.attempts-shared.batch_attempt_start,
            asset_attempts=sum(g.assets for g in guards),external_blocks=sum(g.external_blocked for g in guards),
            unique_provider_IDs=len(merged),cached_detail_IDs=sum(r['detail_reusable_from_cache'] for r in merged),
            uncached_candidate_IDs=sum(not r['detail_reusable_from_cache'] for r in merged),
            first_discovered_IDs=sum(not r['known_discovery_before_batch'] for r in merged),
            elapsed_seconds=clock()-shared.batch_started)
        checkpoint('FINAL_BATCH_REVIEW_REQUIRED');write(folder/'result.json',result)
    return result




def history(project,config,prep):
    """Only the complete sealed PAUSED prefix is eligible, never a source-error or crash run."""
    root=project/config['output_base'];runs=sorted(root.glob('run-*')) if root.exists() else []
    if len(runs)>=config['max_segments']:raise ValueError('SEGMENT_COUNT_CAP_REVIEW_REQUIRED')
    selected=read(prep/'selected_batches.json');order=flatten(selected)
    known=set(read(prep/'known_discovery_provider_ids.json'));reusable=set(read(prep/'reusable_detail_provider_ids.json'))
    totals=initial_totals(selected);count=0;previous=None;prefix_hashes={};durations=[]
    for run in runs:
        if not run.is_dir() or run.is_symlink():raise ValueError('UNEXPECTED_RUN_PATH')
        state=run/'state';verify_zip(state,run/'delta-vsdc-headless54.zip',TYPE)
        if read(state/'runtime.json')!=runtime(project) or read(state/'plan.json')!=config:
            raise ValueError('SEGMENT_RUNTIME_OR_CONFIG_CHANGED')
        inputs=read(state/'inputs.json')
        if inputs!={'preparation_manifest_sha256':sha((prep/'manifest.json').read_bytes()),'predecessor':previous,
                    'completed_before_segment':count}:
            raise ValueError('SEGMENT_LINEAGE_OR_PREFIX_CHANGED')
        result=read(state/'result.json')
        if result['status']!=PAUSED or not result['resumable']:raise ValueError('ONLY_USER_PAUSED_RUN_CAN_CONTINUE: '+result['status'])
        completed=read(state/'completed_queries.json')
        if completed!=order[:len(completed)] or not count<=len(completed)<=len(order):raise ValueError('QUERY_PREFIX_ORDER_CHANGED')
        for i in range(count):
            folder=query_folder(state,i)
            if hashes(folder)!=prefix_hashes[i]:raise ValueError('COPIED_QUERY_CHECKPOINT_CHANGED')
        durations_before=list(durations)
        costs=read(state/'new_attempts.json');expected_index=count
        computed=json.loads(json.dumps(totals))
        for attempt in costs:
            i=attempt['query_index']
            if i!=expected_index or i>=len(order):raise ValueError('ATTEMPT_ORDER_CHANGED')
            cost=ledger_cost(query_folder(state,i))
            if cost['boundary'] or cost['business']!=attempt['business'] or cost['context']!=attempt['context']:
                raise ValueError('PAUSED_RUN_HAS_BOUNDARY_OR_COST_MISMATCH')
            if not math.isfinite(attempt['active_seconds']) or attempt['active_seconds']<0:raise ValueError('INVALID_ATTEMPT_TIME')
            b=computed['batches'][order[i]['batch_id']]
            for key in ('business','context'):computed[key]+=cost[key];b[key]+=cost[key]
            b['active_seconds']+=attempt['active_seconds']
            if attempt['complete']:expected_index+=1;durations.append(attempt['active_seconds'])
            else:
                partial=read(query_folder(state,i)/'state/result.json')
                if (attempt is not costs[-1] or partial['status']!='CANCELLED_NO_REPLAY'
                        or partial['stop_reason']!='USER_INTERRUPT' or partial['source_stopped']):
                    raise ValueError('PARTIAL_ATTEMPT_NOT_A_USER_PAUSE')
        if expected_index!=len(completed):raise ValueError('COMPLETED_QUERY_ATTEMPTS_MISMATCH')
        if (result['totals']['business']!=computed['business'] or result['totals']['context']!=computed['context']
                or result['totals']['batches']!=computed['batches']
                or result['totals']['active_seconds']<totals['active_seconds']+sum(a['active_seconds'] for a in costs)):
            raise ValueError('CUMULATIVE_COST_CHECKPOINT_MISMATCH')
        for i in range(count,len(completed)):
            folder=query_folder(state,i);context=read(folder/'context.json')
            if context['headless_query_runtime']!=runtime(project):raise ValueError('QUERY_RUNTIME_CHANGED')
            articles=validate_query(folder,order[i],known,reusable,project)
            known.update(r['provider_article_id'] for r in articles)
        if (read(state/'known_discovery_after_validated_queries.json')!=sorted(known)
                or result['completed_query_count']!=len(completed)
                or result['remaining_query_count']!=len(order)-len(completed)
                or result['known_list_IDs']!=len(known) or result['reusable_detail_IDs_unchanged']!=len(reusable)
                or result['detail_requests'] or result['canonical_fields_applied'] or result['owner_choices_changed']
                or result['pit_or_identity_promoted'] or result['full_history_certified']):
            raise ValueError('SEGMENT_PROGRESS_OR_CACHE_CLASSIFICATION_MISMATCH')
        expected_batches=[b['batch_id'] for b in selected if all({'batch_id':b['batch_id'],'ticker':t} in completed for t in b['tickers'])]
        if (result['validated_batch_ids']!=expected_batches or result['source_requests_this_segment']!=sum(a['business'] for a in costs)
                or result['browser_launches_this_segment']!=sum(read(query_folder(state,a['query_index'])/'state/result.json')['browser_launches'] for a in costs)):
            raise ValueError('SEGMENT_BATCH_OR_SEGMENT_COST_MISMATCH')
        if result.get('headless') is not True:raise ValueError('HEADLESS_SEGMENT_REQUIRED')
        validate_progress(state,order,selected,count,durations_before,result,costs)
        totals=result['totals'];check_totals(totals)
        count=len(completed);prefix_hashes={i:hashes(query_folder(state,i)) for i in range(count)}
        previous={'run':run.name,'manifest_sha256':sha((state/'manifest.json').read_bytes())}
    return {'runs':runs,'completed':order[:count],'known':known,'reusable':reusable,'totals':totals,
        'predecessor':previous,'prefix_hashes':prefix_hashes,'durations':durations}




def request_pause(project):
    root=Path(project)/contract()['output_base'];lock=read(root/'active.lock')
    name=lock['run']
    if not isinstance(name,str) or not name.startswith('run-') or Path(name).name!=name:raise ValueError('INVALID_ACTIVE_RUN')
    run=root/name
    if not run.is_dir() or (run/'state/manifest.json').exists():raise ValueError('NO_ACTIVE_UNSEALED_RUN')
    marker=run/'PAUSE_REQUEST'
    try:
        with marker.open('x',encoding='utf8') as f:f.write('USER_REQUESTED_PAUSE\n')
    except FileExistsError:pass
    return {'status':'PAUSE_REQUESTED','run':name,'source_requests':0,'browser_launched':False}




def run(project,output,*,pause=None,driver_factory=HeadlessDriver,clock=time.monotonic,emit=print,dry_run=False):
    project,output=Path(project).resolve(),Path(output).resolve();config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    prior=history(project,config,prep);selected=read(prep/'selected_batches.json');order=flatten(selected)
    ready=base.mbs.old.readiness(caps())
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED','source_requests':0,
        'browser_launched':False,'completed_queries':len(prior['completed']),'remaining_queries':len(order)-len(prior['completed']),
        'selected_batches':len(selected),'headless':True,'readiness':ready}
    if not ready['ready']:raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
    if len(prior['completed'])==len(order):raise ValueError('ALL_SELECTED_QUERIES_ALREADY_COMPLETE')
    output.mkdir(parents=True);pause=pause or Pause(output.parent/'PAUSE_REQUEST')
    for name in ('selected_batches.json','reusable_detail_provider_ids.json','known_discovery_provider_ids.json',
                 'cache_policy.json','query_inventory_before_chain.json','protected_old_files.json'):
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config);write(output/'runtime.json',runtime(project));write(output/'environment.json',ready)
    write(output/'inputs.json',{'preparation_manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'predecessor':prior['predecessor'],'completed_before_segment':len(prior['completed'])})
    completed=list(prior['completed']);known=set(prior['known']);totals=prior['totals'];attempts=[]
    if prior['runs']:
        old=prior['runs'][-1]/'state'
        for i in range(len(completed)):
            shutil.copytree(query_folder(old,i),query_folder(output,i))
            if hashes(query_folder(output,i))!=prior['prefix_hashes'][i]:raise ValueError('COPIED_PREFIX_CHANGED_BEFORE_ACQUISITION')
    protected=read(prep/'protected_old_files.json');check=lambda:base.mbs.old.protected_check(project,protected)
    started=clock();old_active=totals['active_seconds'];last=clock();active=None
    reporter=Progress(output,selected,completed,prior.get('durations',[]),started,old_active,clock,emit);reporter.record('START')
    result={'status':STOPPED,'headless':True,'resumable':False,'source_requests_this_segment':0,'browser_launches_this_segment':0,
        'detail_requests':0,'canonical_fields_applied':0,'owner_choices_changed':False,'pit_or_identity_promoted':False,
        'full_history_certified':False,'openai_api_calls':0,'manual_offline_review_pending':True}
    def checkpoint(event):
        folder=output/'checkpoints';folder.mkdir(exist_ok=True)
        write(folder/f'{len(list(folder.glob("*.json")))+1:04}.json',{'event':event,'completed_queries':len(completed),
            'active_query':active,'business':totals['business'],'context':totals['context']})
    try:
        check();check_totals(totals)
        for i in range(len(completed),len(order)):
            if pause.requested():result.update(status=PAUSED,resumable=True);break
            active=order[i];bid=active['batch_id'];b=totals['batches'][bid];check();check_totals(totals)
            if b['business']>=100 or b['context']>=1660:raise ValueError('ACTIVE_BATCH_CUMULATIVE_BUDGET_EXHAUSTED')
            attempt_started=clock()
            reporter.begin(i,attempt_started)
            checkpoint('QUERY_START');folder=query_folder(output,i);folder.mkdir(parents=True)
            shared_config={**caps(),'max_batch_business_requests':100-b['business'],
                'max_batch_context_attempts':1660-b['context']}
            shared=base.Budget(shared_config,clock);shared.started=started-old_active
            shared.business=totals['business'];shared.attempts=totals['context'];shared.last=last;shared.begin(bid)
            shared.batch_started=attempt_started-b['active_seconds']
            write(folder/'context.json',{'scope':active,'previous_start':shared.previous_start,'headless_query_runtime':runtime(project)})
            before_business=shared.business;before_context=shared.attempts
            passed=False
            try:
                acquired=acquire_query(project,folder/'state',query_definition(active),caps(),prep,shared,
                    prior['reusable'],known,check,lambda cfg,g:ProgressDriver(driver_factory(cfg,g),pause,reporter),clock,progress=reporter)
                result['browser_launches_this_segment']+=acquired['browser_launches']
                check();base.seal(folder/'state',folder/'query.zip',artifact_type=base.BATCH_TYPE)
                if acquired['status']=='PASS_SOURCE_BATCH_REQUIRES_AUTOMATED_VALIDATION':
                    checked=validate_batch(folder/'state',folder/'query.zip',query_definition(active),caps(),
                        prior['reusable'],known,shared.previous_start)
                    if read(folder/'state/runtime.json')!=runtime(project):raise ValueError('QUERY_RUNTIME_CHANGED')
                    write(folder/'validation.json',checked);shared.check();check();passed=True
            finally:
                duration=clock()-attempt_started
                attempt={'query_index':i,'business':shared.business-before_business,'context':shared.attempts-before_context,
                    'active_seconds':duration,'complete':passed}
                attempts.append(attempt)
                for key in ('business','context'):totals[key]+=attempt[key];b[key]+=attempt[key]
                b['active_seconds']+=duration;totals['active_seconds']=old_active+clock()-started
                result['source_requests_this_segment']+=attempt['business'];last=shared.last
            if passed:
                completed.append(active);known.update(r['provider_article_id'] for r in read(folder/'state/deduplicated_query_articles.json'))
                checkpoint('QUERY_VALIDATED');reporter.done(duration)
                if i+1==len(order) or order[i+1]['batch_id']!=bid:
                    reporter.batch_done(bid)
                active=None
            else:
                cost=ledger_cost(folder);shared.check();check_totals(totals)
                if (acquired['status']=='CANCELLED_NO_REPLAY' and pause.requested() and not cost['boundary']
                        and cost['business']==attempt['business'] and cost['context']==attempt['context']):
                    result.update(status=PAUSED,resumable=True);break
                raise ValueError('QUERY_SOURCE_STOP: '+acquired.get('stop_reason',acquired['status']))
        else:result.update(status=COMPLETE,resumable=False)
    except KeyboardInterrupt:
        # Only the installed cooperative pause protocol can make a resumable result.
        result.update(status=STOPPED,resumable=False,stop_reason='UNHANDLED_INTERRUPT_REVIEW_REQUIRED')
    except Exception as exc:result.update(status=STOPPED,resumable=False,stop_reason=str(exc))
    finally:
        totals['active_seconds']=old_active+clock()-started
        try:
            check()
            if result['status']==PAUSED:check_totals(totals)
        except Exception as exc:result.update(status=STOPPED,resumable=False,stop_reason=str(exc))
        done={b['batch_id'] for b in selected if all({'batch_id':b['batch_id'],'ticker':t} in completed for t in b['tickers'])}
        result.update(completed_query_count=len(completed),remaining_query_count=len(order)-len(completed),
            validated_batch_ids=[b['batch_id'] for b in selected if b['batch_id'] in done],totals=totals,
            active_query=active,reusable_detail_IDs_unchanged=len(prior['reusable']),known_list_IDs=len(known))
        write(output/'completed_queries.json',completed);write(output/'new_attempts.json',attempts)
        write(output/'known_discovery_after_validated_queries.json',sorted(known))
        reporter.finish(result['status'])
        totals['active_seconds']=old_active+clock()-started
        write(output/'result.json',result);checkpoint('FINAL_SEGMENT')
    return result
