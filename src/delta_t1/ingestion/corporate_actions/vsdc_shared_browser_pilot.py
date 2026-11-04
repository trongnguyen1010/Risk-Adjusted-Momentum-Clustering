"""One local Chrome process, three isolated contexts, unchanged2s source gates and explicit timings."""
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import math
from pathlib import Path
import time

from . import vsdc_speed1s_pilot as prior

baseline=prior.previous
mbs=baseline.mbs
read,write,sha,hashes,seal=baseline.read,baseline.write,baseline.sha,baseline.hashes,baseline.seal
verify_artifact=baseline.verify_artifact
CONFIG='configs/data/corporate_actions/vsdc_shared_browser2s_pilot_v1.json'
TYPE='vsdc-shared-browser2s-three-query-pilot-v1'
PREP_TYPE='vsdc-shared-browser2s-preparation-v1'
PASS='PASS_SHARED_BROWSER2S_PILOT_REVIEW_REQUIRED'
PARENTS={
    'speed1_preparation':('data/corporate_actions/work/vsdc_three_query_speed1s_preparation_20261103_v1',
        '886805c1b0c7759534e2754931a9008bc1ba47a1c152f5c9ccfe41fb3762e41e',prior.PREP_TYPE),
    'speed1_run':('data/corporate_actions/work/vsdc_three_query_speed1s_pilot_v1/run-20261103T082730656572Z/state',
        '27994315f12a190fef370fc3658f7bff3133f8de13409a8593d3e3a23dc6712d',prior.TYPE),
    'speed1_review':('data/corporate_actions/work/vsdc_three_query_speed1s_live_review_20261103_v1',
        '26a310a7f6f1f51dd9af38a60cdac9aaeab2f93616f942021cc914f79ba65fea','vsdc-three-query-speed1s-offline-live-review-v1'),
    'speed1_validation':('data/corporate_actions/work/vsdc_three_query_speed1s_live_review_validation_20261103_v1',
        '3d4c31a9badc7efa48192e0cfc146d321e2def7378cb4a1606358f3d8b3323b2','vsdc-three-query-speed1s-offline-live-review-validation-v1')}


def contract():
    return {**baseline.contract(),'stage':'VSDC_SHARED_BROWSER2S_TIMING_PILOT_PREPARATION_V1',
        'output_base':'data/corporate_actions/work/vsdc_shared_browser2s_pilot_v1',
        'preparation':'data/corporate_actions/work/vsdc_shared_browser2s_preparation_20261103_v1',
        'browser_lifecycle':'ONE_PROCESS_THREE_FRESH_NONPERSISTENT_CONTEXTS','timing_profile':True}


def validate(config):
    if config!=contract():raise ValueError('EXACT_SHARED_BROWSER2S_THREE_QUERY_CONTRACT_REQUIRED')


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_shared_browser_pilot.py',
        'scripts/corporate_actions/prepare_vsdc_shared_browser2s_pilot_v1.py',
        'scripts/corporate_actions/collect_vsdc_shared_browser2s_pilot_v1.py']
    return {**prior.runtime(project),**{n:sha((project/n).read_bytes()) for n in names}}


def parents(project):
    _,prep=prior.load_preparation(project)
    for name,(rel,digest,kind) in PARENTS.items():
        folder=project/rel
        if sha((folder/'manifest.json').read_bytes())!=digest:raise ValueError('SHARED_BROWSER_PARENT_CHANGED: '+name)
        verify_artifact(folder,{kind})
    if read(project/PARENTS['speed1_review'][0]/'review.json')['status']!='PASS_BOUNDED_1S_INTERVAL_WITH_SAME_QUERY_DATA_SMALL_TIME_GAIN':
        raise ValueError('REVIEWED_SPEED1_PILOT_REQUIRED')
    return prep


def load_preparation(project):
    config=read(project/CONFIG);validate(config);parents(project)
    prep=project/config['preparation'];verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('SHARED_BROWSER_PREPARED_RUNTIME_CHANGED')
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
    protected.update(prior.runtime(project));output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','known_discovery_provider_ids.json','cache_policy.json','pilot_plan.json']:
        (output/name).write_bytes((old/name).read_bytes())
    write(output/'experiment.json',{'kind':'ONE_CHROME_THREE_FRESH_CONTEXTS_AT_REVIEWED2S_WITH_TIMING',
        'baseline2s':{'path':prior.PARENTS['speed2_review'][0],'manifest_sha256':prior.PARENTS['speed2_review'][1],
            'seconds':15.234999999999673,'query_rows':{'A32':35,'AAA':51,'IDJ':24},'business_requests':7,'browser_launches':3},
        'secondary1s':{'path':PARENTS['speed1_review'][0],'seconds':14.71900000000096},
        'planned_browser_launches':1,'planned_fresh_contexts':3,'context_reuse':False,'hash_checks_removed':0,
        'ZIP_policy_change':False,'timing_inclusive_and_exclusive':True,
        'timing_categories':['protected_hash','runtime_hash','playwright_start','browser_launch','context_open','context_close',
            'browser_close','playwright_stop','browser_first','browser_next','pacing','archive_parse','final_artifacts'],
        'packaging_timing':'Separate sidecar outside sealed state, references ZIP/state hashes; cannot include its own duration in immutable ZIP.',
        'expected_new_query_completion_credit':0,'bulk_runner_changed':False,'detail_downloads':False,
        'acceptance':'Same three full lists/data/cache,7expectedbusiness200,no boundaries,min2s,one launch/three isolated contexts,exclusive timing sums reconcile.',
        'limits':'Historical baseline unpaired;different protected set/system/network load can affect elapsed. No sustained-rate or speed guarantee.'})
    write(output/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,'browser_launches':0,
        'readiness':mbs.old.readiness(config),'hash_and_ZIP_gates':'Unchanged;instrumentation only',
        'source_caps':'Same frozen2s three-query pilot','on_error':'STOP no retry/resume/relaunch/fallback',
        'next_step':'User runs once locally;offline review data,context isolation,elapsed andtimings before any54-chain optimization.'})
    write(output/'protected_old_files.json',protected);write(output/'runtime.json',runtime(project))
    write(output/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(output)});load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','source_requests':0,'interval_seconds':2,'tickers':list(baseline.PILOT),
        'planned_browser_launches':1,'planned_fresh_contexts':3,'protected_old_files':len(protected),'output':str(output)}


class Timings:
    """Monotonic inclusive/exclusive spans;nested hash work never double-counted in totals."""
    def __init__(self,clock=time.monotonic):self.clock=clock;self.started=clock();self.stack=[];self.events=[]
    @contextmanager
    def span(self,category,ticker=None):
        frame={'start':self.clock(),'children':0};self.stack.append(frame)
        try:yield
        finally:
            elapsed=self.clock()-frame['start'];exclusive=max(0,elapsed-frame['children']);self.stack.pop()
            if not math.isfinite(elapsed) or elapsed<0:raise ValueError('INVALID_MONOTONIC_TIMING')
            if self.stack:self.stack[-1]['children']+=elapsed
            self.events.append({'category':category,'ticker':ticker,'seconds_inclusive':elapsed,'seconds_exclusive':exclusive})
    def snapshot(self):
        if self.stack:raise ValueError('TIMING_SPAN_STILL_ACTIVE')
        elapsed=self.clock()-self.started;group=defaultdict(lambda:{'count':0,'seconds_inclusive':0,'seconds_exclusive':0})
        for row in self.events:
            item=group[row['category']];item['count']+=1
            for key in ('seconds_inclusive','seconds_exclusive'):item[key]+=row[key]
        measured=sum(row['seconds_exclusive'] for row in self.events)
        if measured>elapsed+1e-6:raise ValueError('TIMINGS_DOUBLE_COUNT_OR_CLOCK_ERROR')
        return {'elapsed_seconds':elapsed,'measured_exclusive_seconds':measured,'other_seconds':max(0,elapsed-measured),
            'categories':dict(group),'events':self.events,
            'semantics':'Inclusive spans can overlap;exclusive sums plus other_seconds equal elapsed. Browser calls combine source/network/render work;no causal attribution.',
            'packaging_included':False}


class BrowserOwner:
    def __init__(self,timings,config):
        self.timings,self.config=timings,config;self.manager=self.browser=None;self.guard=None
        self.launch_attempts=self.launches=self.contexts=self.closed_contexts=0;self.active=None
        self.fatal=None;self.closing=False
    def disconnected(self,*args):
        if not self.closing:
            self.fatal='UNEXPECTED_SHARED_BROWSER_DISCONNECTED'
            if self.guard:self.guard.fail(self.fatal)
    def check(self):
        if self.fatal:raise ValueError(self.fatal)
        if self.guard:self.guard.check()
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
            self.browser=self.manager.chromium.launch(channel='chrome',headless=False,timeout=guard.timeout_ms())
        self.launches+=1;self.browser.on('disconnected',self.disconnected);self.check()
    def driver(self,config,guard):return ContextDriver(config,guard,self)
    def close(self):
        self.closing=True;error=None
        if self.active is not None:
            try:self.active.__exit__(None,None,None)
            except Exception as exc:error=exc
        if self.browser is not None:
            try:
                with self.timings.span('browser_close'):self.browser.close()
            except Exception as exc:error=error or exc
        if self.manager is not None:
            try:
                with self.timings.span('playwright_stop'):self.manager.stop()
            except Exception as exc:error=error or exc
        if error:raise ValueError('BROWSER_CLEANUP_FAILED') from error


class ContextDriver(mbs.Driver):
    def __init__(self,config,guard,owner):
        super().__init__(config,guard);self.owner=owner;self.ordinal=None
    def __enter__(self):
        try:
            self.owner.ensure(self.guard);self.browser=self.owner.browser
            if self.owner.contexts>=3:raise ValueError('EXACT_MAX_THREE_FRESH_CONTEXTS')
            with self.owner.timings.span('context_open',self.config['ticker']):
                self.context=self.browser.new_context(ignore_https_errors=False,accept_downloads=False,service_workers='block')
                self.owner.active=self;self.owner.contexts+=1;self.ordinal=self.owner.contexts
                self.context.route('**/*',self._route)
                self.context.on('response',self._response);self.context.on('requestfailed',self._failed)
                self.context.route_web_socket('**/*',self._websocket)
                self.page=self.context.new_page();self.context.on('page',self._popup);self.page.on('dialog',self._dialog)
                self.version=self.browser.version
            self.owner.check();return self
        except BaseException:
            self.__exit__(None,None,None);raise
    def __exit__(self,*args):
        self.closing=True
        try:
            if self.context is not None:
                with self.owner.timings.span('context_close',self.config['ticker']):self.context.close()
                self.owner.closed_contexts+=1
        except Exception as exc:
            self.owner.fatal='FRESH_CONTEXT_CLOSE_FAILED';self.guard.fail(self.owner.fatal)
            raise ValueError(self.owner.fatal) from exc
        finally:
            self.context=None
            if self.owner.active is self:self.owner.active=None


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
    protected=read(prep/'protected_old_files.json')
    def check():
        with timings.span('protected_hash'):mbs.old.protected_check(project,protected)
    owner=owner_factory(timings,config);shared=baseline.SharedBudget(config,clock);guards=[];completed=[];articles=[]
    reusable=set(read(prep/'reusable_detail_provider_ids.json'));result={'status':'STOPPED_SHARED_BROWSER_OR_SOURCE_REVIEW_REQUIRED',
        'resumable':False,'bulk_collection_ready':False,'business_interval_seconds':2,'source_stopped':False,'detail_requests':0,
        'canonical_fields_applied':0,'normalized_observations':0,'pit_or_identity_promoted':False,'openai_api_calls':0}
    try:
        if not ready['ready']:raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
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
