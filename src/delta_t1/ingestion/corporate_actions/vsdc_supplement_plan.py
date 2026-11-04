"""Cache-first VSDC batching plan and exact three-query browser validation pilot."""
from datetime import datetime, timezone
import math
from pathlib import Path
import re
import time

from ..corporate_action_sources import Document, sha, search_url
from ..corporate_action_cache_audit import search_links
from ..hnx_announcement_batch import verify_artifact
from .hnx_local_supplement import read, rows, write, hashes
from .hnx_local_pvs import seal
from .vsdc_pagination_audit import snapshot_coverage
from . import vsdc_mbs_browser_supplement as mbs

CONFIG = "configs/data/corporate_actions/vsdc_supplement_plan_pilot_v1.json"
PREP_TYPE = "vsdc-supplement-batch-plan-and-three-query-preparation-v1"
TYPE = "vsdc-three-query-browser-list-validation-v1"
PILOT = ("A32", "AAA", "IDJ")
SOURCES = {
    "audit": ("data/corporate_actions/work/vsdc_pagination_scope_audit_20261103_v2",
        "a3e0c726d86027a5e65c442c857d86d452b4aa04a20c92f24c4a0643e453e864", None),
    "mbs_preparation": ("data/corporate_actions/work/vsdc_mbs_browser_supplement_preparation_20261103_v1",
        "99a56cb5f7631f2602287177f1741495c675ee9b6014ff1d4c358de3703494e1", mbs.PREP_TYPE),
    "mbs_review": ("data/corporate_actions/work/vsdc_mbs_browser_supplement_live_review_20261103_v1",
        "1fd85f086b2efe616b68f867525cf82280d27f288289009d82f9c485061b129f", "vsdc-mbs-browser-supplement-offline-live-review-v1"),
}


def contract():
    return {"stage":"VSDC_BATCH_PLAN_AND_THREE_QUERY_PILOT_PREPARATION_V1", "pilot_tickers":list(PILOT),
        "output_base":"data/corporate_actions/work/vsdc_three_query_browser_pilot_v1",
        "preparation":"data/corporate_actions/work/vsdc_supplement_plan_preparation_20261103_v1",
        "max_list_pages_per_query":4,"max_business_requests":12,"max_context_attempts":246,
        "max_context_per_query":82,"max_assets_per_query":78,"max_seconds":240,"max_query_seconds":90,
        "operation_timeout_seconds":15,"business_interval_seconds":8,"max_html_bytes":2000000,
        "workers":1,"channel":"chrome","headless":False,"playwright_version":"1.57.0",
        "retry":False,"resume":False,"details":False,"bulk_enabled":False,
        "persistent_profile":False,"ignore_https_errors":False,"export_cookies_or_auth":False,
        "batch_max_tickers":20,"batch_max_estimated_list_requests":100,"planned_query_page_cap":20}


def validate(config):
    if config != contract(): raise ValueError("EXACT_THREE_QUERY_LIST_ONLY_CONTRACT_REQUIRED")


def runtime(project):
    names=[CONFIG,"src/delta_t1/ingestion/corporate_actions/vsdc_supplement_plan.py",
        "scripts/corporate_actions/prepare_vsdc_supplement_plan_v1.py",
        "scripts/corporate_actions/collect_vsdc_three_query_browser_pilot_v1.py"]
    return {**mbs.runtime(project),**{n:sha((project/n).read_bytes()) for n in names}}


def verify_sources(project):
    _,prep=mbs.load_preparation(project)
    for name,(rel,digest,kind) in SOURCES.items():
        path=project/rel
        if sha((path/'manifest.json').read_bytes())!=digest:raise ValueError('PLAN_PARENT_CHANGED: '+name)
        verify_artifact(path,{kind} if kind else None)
    review=read(project/SOURCES['mbs_review'][0]/'review.json')
    if review['technical_status']!='PASS_FULL_QUERY_AND_EXACT_DETAIL':raise ValueError('MBS_REVIEW_PASS_REQUIRED')
    state=Path(review['inputs']['state']['path']).resolve()
    if not state.is_relative_to(project):raise ValueError('PARENT_STATE_OUTSIDE_WORKSPACE')
    reference=verify_artifact(state,{mbs.TYPE})
    if reference['manifest_sha256']!=review['inputs']['state']['manifest_sha256']:
        raise ValueError('REVIEWED_MBS_STATE_CHANGED')
    return prep,state


def build_plan(candidates, completed, config):
    """Partition every original query once; estimates never authorize acquisition."""
    if len({r['ticker'] for r in candidates})!=len(candidates):raise ValueError('DUPLICATE_QUERY_TICKERS')
    inventory=[]
    for r in sorted(candidates,key=lambda r:r['ticker']):
        total=r['reported_total']
        if not isinstance(total,int) or total<=20 or r['query_status']!='QUERY_LIST_INCOMPLETE':
            raise ValueError('ARCHIVED_INCOMPLETE_QUERY_REQUIRED')
        pages=math.ceil(total/20)
        status=('COMPLETED_REVIEWED_QUERY_SNAPSHOT' if r['ticker'] in completed else
                'HOLD_LARGE_QUERY_SCOPE_REVIEW' if pages>config['planned_query_page_cap'] else
                'PILOT_PREPARED_NOT_EXECUTED' if r['ticker'] in config['pilot_tickers'] else
                'PLANNED_NOT_AUTHORIZED')
        inventory.append({'ticker':r['ticker'],'exchange':r['exchange'],'url':r['url'],
            'archived_total_rows':total,'archived_known_rows':r['known_list_ids'],
            'archived_unseen_row_slots':r['unseen_query_row_slots'],
            'estimated_fresh_list_requests':pages,'status':status,'bulk_authorized':False,
            'new_detail_requests_estimate':None,'historical_event_coverage_certified':False})
    if not completed.issubset({r['ticker'] for r in inventory}):raise ValueError('UNKNOWN_COMPLETED_QUERY')
    normal=[r for r in inventory if r['status']=='PLANNED_NOT_AUTHORIZED']
    batches=[];current=[];requests=0
    for r in normal:
        if current and (len(current)>=config['batch_max_tickers']
                or requests+r['estimated_fresh_list_requests']>config['batch_max_estimated_list_requests']):
            batches.append(current);current=[];requests=0
        current.append(r);requests+=r['estimated_fresh_list_requests']
    if current:batches.append(current)
    batches=[{'batch_id':f'proposed-{i:03d}','tickers':[r['ticker'] for r in batch],
        'estimated_list_requests':sum(r['estimated_fresh_list_requests'] for r in batch),
        'status':'PROPOSED_NOT_EXECUTABLE','acquisition_authorized':False}
        for i,batch in enumerate(batches,1)]
    return inventory,batches


def prepare(project):
    project=Path(project).resolve();config=read(project/CONFIG);validate(config)
    old_prep,state=verify_sources(project);out=project/config['preparation']
    if out.exists():raise FileExistsError('REFUSE_OVERWRITE')
    audit=project/SOURCES['audit'][0];candidates=rows(audit/'supplement_candidates.jsonl')
    if len(candidates)!=1104:raise ValueError('EXPECTED_1104_BASELINE_QUERIES')
    inventory,batches=build_plan(candidates,{'MBS'},config)
    indexed={r['ticker']:r for r in inventory}
    if [indexed[t]['exchange'] for t in PILOT]!=['UPCOM','HOSE','HNX']:
        raise ValueError('PILOT_EXCHANGE_REPRESENTATION_CHANGED')
    if any(indexed[t]['estimated_fresh_list_requests']>4 for t in PILOT):raise ValueError('PILOT_PAGE_BUDGET')
    cache_ids=set(read(old_prep/'cached_article_ids.json'))
    if len(cache_ids)!=27730:raise ValueError('CACHE_BASELINE_ID_COUNT_CHANGED')
    cache_path=project/'tmp/ca_cache_inventory_20261102_v4'
    cache_manifest=cache_path/'manifest.json';index=cache_path/'raw_document_index.jsonl'
    if (sha(cache_manifest.read_bytes())!='4ace8b76f77bffd7fd224a55da5b290916275df3ca114e5a65b7553bd413f378'
            or sha(index.read_bytes())!=read(cache_manifest)['files'][index.name]):
        raise ValueError('BASELINE_RAW_DOCUMENT_INDEX_CHANGED')
    # Only187243 gained a detail: 43 new list IDs must not all become reusable-detail IDs.
    detail=state/'rendered_html/detail187243.html'
    receipt=read(state/'detail187243_receipt.json')
    if sha(detail.read_bytes())!=receipt['fragment_sha256']:raise ValueError('NEW_RENDERED_DETAIL_CHANGED')
    cache_ids.add('187243')
    protected=read(old_prep/'protected_old_files.json')
    for path in [cache_manifest,index]:protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    for rel,_,_ in SOURCES.values():
        path=project/rel
        for name in ['manifest.json',*read(path/'manifest.json')['files']]:
            target=path/name;protected[target.relative_to(project).as_posix()]=sha(target.read_bytes())
    for name in ['manifest.json',*read(state/'manifest.json')['files']]:
        target=state/name;protected[target.relative_to(project).as_posix()]=sha(target.read_bytes())
    protected.update(mbs.runtime(project))
    out.mkdir(parents=True)
    for name,value in [('query_inventory.json',inventory),('proposed_batches.json',batches),
        ('reusable_detail_provider_ids.json',sorted(cache_ids)),('protected_old_files.json',protected),
        ('runtime.json',runtime(project))]:write(out/name,value)
    write(out/'pilot_plan.json',{'tickers':[indexed[t] for t in PILOT],
        'business_request_cap':12,'archived_estimated_list_requests':sum(indexed[t]['estimated_fresh_list_requests'] for t in PILOT),
        'details_enabled':False,'query_reread':'Fresh same-session complete lists, not stitched archived pages',
        'stop_on_any_error':True,'no_automatic_bulk_after_pass':True})
    write(out/'cache_policy.json',{'baseline_cache_provider_ids':27730,'new_rendered_detail_provider_ids':['187243'],
        'reusable_detail_provider_id_count':len(cache_ids),'rendered_detail_overlay':{
            'provider_article_id':'187243','path':str(detail),'sha256':receipt['fragment_sha256'],
            'basis':'RENDERED_PUBLIC_DETAIL_NOT_RAW_HTTP'},
        'baseline_raw_index':'tmp/ca_cache_inventory_20261102_v4/raw_document_index.jsonl',
        'detail_fetch_rule':'Discover/deduplicate/provider-scope-review first; no new detail fetch in this pilot'})
    summary={'baseline_incomplete_queries':1104,'reviewed_query_completed':['MBS'],'pending_queries':1103,
        'pilot_tickers':list(PILOT),'pilot_exchanges':['UPCOM','HOSE','HNX'],
        'large_query_hold':[r['ticker'] for r in inventory if r['status']=='HOLD_LARGE_QUERY_SCOPE_REVIEW'],
        'normal_pending_including_pilot':sum(r['status'] in {'PLANNED_NOT_AUTHORIZED','PILOT_PREPARED_NOT_EXECUTED'} for r in inventory),
        'proposed_batch_count_excluding_pilot':len(batches),'archived_unseen_slots_baseline':52819,
        'archived_unseen_slots_after_MBS_query_completion':sum(r['archived_unseen_row_slots'] for r in inventory if r['ticker']!='MBS'),
        'reusable_detail_provider_id_count':len(cache_ids),'unverified_queries_outside1104':['DTR','KAI','LPS','PCB'],
        'exhausted_archived_queries_outside1104':414,'bulk_collection_ready':False,'detail_requests':0,
        'rows_are_not_distinct_events_or_new_requests':True}
    write(out/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,
        'browser_launches':0,'readiness':mbs.old.readiness(config),'summary':summary,
        'phases':['VALIDATE_THREE_QUERY_LIST_PILOT','REVIEW_ZIP','VERSIONED_BATCH_LIST_ACQUISITION',
                  'DEDUP_PROVIDER_IDS_AND_REUSE_CACHE','REVIEW_SCOPE_BEFORE_NEW_DETAILS'],
        'parents':{k:{'path':v[0],'manifest_sha256':v[1]} for k,v in SOURCES.items()}})
    write(out/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(out)})
    load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','source_requests':0,'summary':summary,
        'protected_old_files':len(protected),'output':str(out)}


def load_preparation(project):
    config=read(project/CONFIG);validate(config);verify_sources(project)
    prep=project/config['preparation'];verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('PLAN_PILOT_RUNTIME_CHANGED')
    mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    ids=read(prep/'reusable_detail_provider_ids.json')
    if len(ids)!=27731 or len(set(ids))!=27731 or '187243' not in ids:
        raise ValueError('CACHE_DETAIL_OVERLAY_CHANGED')
    return config,prep


class SharedBudget:
    def __init__(self,config,clock):
        self.config,self.clock=config,clock;self.started=clock();self.attempts=self.business=0;self.last=None
    def check(self):
        if self.clock()-self.started>=self.config['max_seconds']:raise ValueError('PILOT_GLOBAL_TIME_BUDGET')


class Guard(mbs.Guard):
    def __init__(self,config,output,check_old,clock,shared):
        super().__init__(config,output,check_old,clock);self.shared=shared
    def check(self):
        try:self.shared.check()
        except ValueError as exc:self.fail(str(exc))
        super().check()
    def timeout_ms(self):
        return min(super().timeout_ms(),max(1,int((self.shared.config['max_seconds']-(self.clock()-self.shared.started))*1000)))
    def admit(self,url,method,resource,body=None,redirected=False):
        self.shared.attempts+=1
        if self.shared.attempts>self.shared.config['max_context_attempts']:
            self.fail('PILOT_GLOBAL_CONTEXT_BUDGET')
        if url==mbs.DETAIL_URL:self.fail('LIST_ONLY_PILOT_NO_DETAIL_REQUESTS')
        if url==self.config['url']:
            if self.shared.business>=self.shared.config['max_business_requests']:self.fail('PILOT_GLOBAL_BUSINESS_BUDGET')
            if self.shared.last is not None and self.clock()-self.shared.last<8:self.fail('PILOT_GLOBAL_SHARED_INTERVAL')
        allowed=super().admit(url,method,resource,body,redirected)
        if allowed and url==self.config['url']:
            self.shared.business+=1;self.shared.last=self.clock()
        return allowed


def source_contract(html,ticker):
    root=Document(html).root;echo='Kết quả tìm kiếm với từ: '+ticker
    if [n.text() for n in root.find('p')].count(echo)!=1 or len(root.find(id='divGlSearchArticles'))!=1:
        raise ValueError('FRESH_EXACT_TICKER_QUERY_ECHO_REQUIRED')
    start=html.find('function searchGlSearch(type)');end=html.find('</script>',start)
    if start<0 or end<start:raise ValueError('FRESH_PUBLIC_PAGINATION_SCRIPT_REQUIRED')
    # Reuse frozen JS-shape validation; the actual ticker echo was validated above.
    checked=mbs.old.prior.source_contract('<p>Kết quả tìm kiếm với từ: MBS</p><div id="divGlSearchArticles"></div><script>'+html[start:end]+'</script>')
    return {**checked,'query_echo':echo,'ticker':ticker}


def list_page(fragment,number,ticker,total=None,seen=()):
    mbs.old.fragment_bytes(fragment,2000000)
    articles=search_links(fragment.encode(),search_url(ticker));ids=[r['provider_article_id'] for r in articles]
    coverage=snapshot_coverage(fragment.encode(),ids);count=coverage.get('reported_total')
    if (not isinstance(count,int) or not 1<=count<=80 or number not in range(1,5)
            or total is not None and count!=total or coverage.get('first')!=(number-1)*20+1
            or coverage.get('last')!=min(number*20,count) or len(ids)!=min(20,count-(number-1)*20)
            or len(set(ids))!=len(ids) or set(ids)&set(seen)):
        raise ValueError('QUERY_RANGE_TOTAL_OR_ID_CONSISTENCY_REQUIRED')
    return {'ticker':ticker,'page':number,'coverage':coverage,'articles':articles,'article_ids':ids}


def run(project,output,*,dry_run=False,driver_factory=mbs.Driver,clock=time.monotonic):
    project,output=Path(project).resolve(),Path(output).resolve()
    config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    ready=mbs.old.readiness(config)
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED',
        'source_requests':0,'browser_launched':False,'pilot_tickers':list(PILOT),'readiness':ready}
    output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','pilot_plan.json','cache_policy.json','protected_old_files.json']:
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config);write(output/'runtime.json',runtime(project));write(output/'environment.json',ready)
    write(output/'input_provenance.json',{'preparation':str(prep),'manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'capture_kind':'PUBLIC_RENDERED_QUERY_FRAGMENTS_NOT_RAW_HTTP'})
    protected=read(prep/'protected_old_files.json');check=lambda:mbs.old.protected_check(project,protected)
    shared=SharedBudget(config,clock);guards=[];completed=[];all_articles=[];reusable=set(read(prep/'reusable_detail_provider_ids.json'))
    result={'status':'STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED','resumable':False,'bulk_collection_ready':False,
        'browser_launches':0,'source_stopped':False,'detail_requests':0,'canonical_fields_applied':0,
        'normalized_observations':0,'pit_or_identity_promoted':False,'openai_api_calls':0}
    try:
        if not ready['ready']:raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
        for ticker in PILOT:
            shared.check();check()
            folder=output/ticker;folder.mkdir();(folder/'network_ledger.jsonl').touch()
            local={**config,'ticker':ticker,'url':search_url(ticker),'max_seconds':config['max_query_seconds'],
                   'max_context_request_attempts':config['max_context_per_query'],'max_asset_attempts':config['max_assets_per_query']}
            guard=Guard(local,folder,check,clock,shared);guards.append((ticker,guard))
            try:
                with driver_factory(local,guard) as driver:
                    result['browser_launches']+=1
                    if shared.last is not None:driver.pace(max(0,8-(clock()-shared.last)))
                    current=driver.first();guard.check()
                    write(folder/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,
                        'default_identity':True,'TLS_ignore_errors':False,'cookie_auth_exported':False})
                    write(folder/'fresh_source_contract.json',source_contract(current['scope_html'],ticker))
                    seen=[];query_articles=[];total=None;previous=''
                    for number in range(1,5):
                        if number>1:
                            check();driver.pace(max(0,8-(clock()-shared.last)))
                            current=driver.next_page(number,previous);guard.check()
                        if current['url']!=local['url'] or current['http_status']!=200:raise ValueError('EXACT_QUERY_HTTP200_REQUIRED')
                        data=mbs.old.fragment_bytes(current['fragment'],2000000)
                        fragments=folder/'rendered_html';fragments.mkdir(exist_ok=True)
                        with (fragments/f'page{number}.html').open('xb') as f:f.write(data)
                        write(folder/f'page{number}_receipt.json',{'url':current['url'],'page':number,
                            'captured_at':datetime.now(timezone.utc).isoformat(),'fragment_sha256':sha(data),'http_status':200,
                            'http_body_hash_not_archived':current['http_body_sha256'],'http_body_bytes':current['http_body_bytes'],
                            'raw_http_body_archived':False})
                        parsed=list_page(current['fragment'],number,ticker,total,seen)
                        write(folder/f'page{number}.json',parsed)
                        total=parsed['coverage']['reported_total'];seen.extend(parsed['article_ids']);query_articles.extend(parsed['articles'])
                        previous=current['fragment']
                        if len(seen)==total:break
                    if len(seen)!=total or len(guard.business)!=math.ceil(total/20) or [r['status'] for r in guard.responses]!=[200]*number:
                        raise ValueError('COMPLETE_QUERY_AND_BUSINESS_RECEIPTS_REQUIRED')
                    completed.append(ticker);all_articles.extend({**a,'query_ticker':ticker} for a in query_articles)
                    write(folder/'complete_query.json',{'ticker':ticker,'reported_total':total,'article_ids':seen,
                        'query_exhausted_in_session':True,'historical_event_coverage_certified':False})
                    guard.check()
                guard.check()
            finally:
                write(folder/'business_requests.json',guard.business);write(folder/'business_responses.json',guard.responses)
        if completed!=list(PILOT):raise ValueError('ALL_THREE_QUERY_COMPLETIONS_REQUIRED')
        result['status']='PASS_THREE_QUERY_LIST_VALIDATION_REVIEW_REQUIRED'
    except KeyboardInterrupt:result.update(status='CANCELLED_REVIEW_REQUIRED',stop_reason='USER_INTERRUPT_NO_REPLAY')
    except Exception as exc:
        result.update(status='STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED',source_stopped=True,
            error_type=type(exc).__name__,stop_reason=next((g.stop_reason for _,g in guards if g.stop_reason),None) or str(exc))
    finally:
        try:check()
        except Exception as exc:result.update(status='PROTECTED_OLD_FILE_CHANGED_REVIEW_REQUIRED',source_stopped=True,stop_reason=str(exc))
        dedup={}
        for article in all_articles:
            aid=article['provider_article_id']
            if aid not in dedup:dedup[aid]={'provider_article_id':aid,'url':article['url'],'titles':[],
                'query_tickers':[],'detail_reusable_from_cache':aid in reusable,'detail_fetch_authorized':False,'event_identity_verified':False}
            row=dedup[aid]
            for field,value in [('titles',article['title']),('query_tickers',article['query_ticker'])]:
                if value not in row[field]:row[field].append(value)
        write(output/'deduplicated_query_articles.json',list(dedup.values()))
        result.update(completed_tickers=completed,context_request_attempts=shared.attempts,business_requests=shared.business,
            assets_attempts=sum(g.assets for _,g in guards),external_resources_blocked=sum(g.external_blocked for _,g in guards),
            unique_provider_IDs=len(dedup),reusable_cached_detail_IDs=sum(r['detail_reusable_from_cache'] for r in dedup.values()),
            new_candidate_IDs=sum(not r['detail_reusable_from_cache'] for r in dedup.values()),elapsed_seconds=clock()-shared.started)
        write(output/'checkpoint.json',{'status':result['status'],'resumable':False,'completed_tickers':completed,'old_runs_never_resumed':True})
        write(output/'result.json',result)
    return result
