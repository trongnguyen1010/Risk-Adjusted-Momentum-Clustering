"""Exact first list-discovery batch, reviewed4s pacing; no automatic batch chain."""
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import re
import time

from . import vsdc_speed4s_pilot as speed

mbs=speed.mbs
read,write,hashes,sha,seal=speed.read,speed.write,speed.hashes,speed.sha,speed.seal
verify_artifact,search_url=speed.verify_artifact,speed.search_url
source_contract=speed.source_contract
SharedBudget=speed.SharedBudget
INTERVAL=4
TICKERS=('AAM','ABB','ABC','ABI','ABR','ABT','ACB','ACC','ACE','ACL',
         'ACM','ACV','ADC','ADP','ADS','AFX','AGF','AGG','AGM','AGP')
CONFIG='configs/data/corporate_actions/vsdc_browser_batch001_v1.json'
PREP_TYPE='vsdc-browser-batch001-preparation-v1'
TYPE='vsdc-browser-batch001-list-discovery-v1'
PARENTS={
    'speed_preparation':('data/corporate_actions/work/vsdc_three_query_speed4s_preparation_20261103_v1',
        '1ac15e9f789a09b3ab6c3904b771b85d222b965ade8f8c481c71585e91d86a67',speed.PREP_TYPE),
    'speed_run':('data/corporate_actions/work/vsdc_three_query_speed4s_pilot_v1/run-20261103T063424932059Z/state',
        '689dca3b4c9b9c993606d1e72872eef0c29dae01b1a77a8d5fa9e1415e6dce57',speed.TYPE),
    'speed_review':('data/corporate_actions/work/vsdc_three_query_speed4s_live_review_20261103_v1',
        '06a1b18aa97e50d7306c9a4c9f0d9ea27b59d78c48f9d33e17c5e12a4e273534',
        'vsdc-three-query-speed4s-offline-live-review-v1'),
}


def contract():
    config={**speed.contract(),'stage':'VSDC_BROWSER_BATCH001_FIXED20_PREPARATION_V1',
        'batch_id':'proposed-001','tickers':list(TICKERS),
        'output_base':'data/corporate_actions/work/vsdc_browser_batch001_v1',
        'preparation':'data/corporate_actions/work/vsdc_browser_batch001_preparation_20261103_v1',
        'max_list_pages_per_query':20,'max_business_requests':100,'max_context_attempts':1660,
        'max_context_per_query':98,'max_seconds':1200,'max_query_seconds':180}
    del config['pilot_tickers']
    return config


def validate(config):
    if config!=contract():raise ValueError('EXACT_FIRST_BATCH20_LIST_ONLY_CONTRACT_REQUIRED')


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_browser_batch001.py',
        'scripts/corporate_actions/prepare_vsdc_browser_batch001_v1.py',
        'scripts/corporate_actions/collect_vsdc_browser_batch001_v1.py']
    return {**speed.runtime(project),**{n:sha((project/n).read_bytes()) for n in names}}


def parents(project):
    _,prep=speed.load_preparation(project)
    for name,(rel,digest,kind) in PARENTS.items():
        path=project/rel
        if sha((path/'manifest.json').read_bytes())!=digest:raise ValueError('BATCH_PARENT_CHANGED: '+name)
        verify_artifact(path,{kind})
    if read(project/PARENTS['speed_review'][0]/'review.json')['status']!='PASS_BOUNDED_4S_INTERVAL_WITH_SAME_QUERY_DATA':
        raise ValueError('REVIEWED_4S_PASS_REQUIRED')
    return prep


def load_preparation(project):
    config=read(project/CONFIG);validate(config);parents(project)
    prep=project/config['preparation'];verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('BATCH_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    plan=read(prep/'batch_plan.json')
    if plan['tickers']!=list(TICKERS) or plan['archived_estimated_list_requests']!=54:
        raise ValueError('FROZEN_BATCH_MEMBERSHIP_CHANGED')
    if len(read(prep/'reusable_detail_provider_ids.json'))!=27731:
        raise ValueError('CACHE_DETAIL_BASELINE_CHANGED')
    return config,prep


def prepare(project):
    project=Path(project).resolve();config=read(project/CONFIG);validate(config)
    old_prep=parents(project);out=project/config['preparation']
    if out.exists():raise FileExistsError('REFUSE_OVERWRITE')
    broad_prep=project/speed.base.contract()['preparation']
    original=read(broad_prep/'proposed_batches.json')[0]
    if original['tickers']!=list(TICKERS) or original['estimated_list_requests']!=54:
        raise ValueError('FIRST_PROPOSED_BATCH_CHANGED')
    inventory={r['ticker']:r for r in read(broad_prep/'query_inventory.json')}
    reviewed_overlay=read(project/speed.PARENTS['baseline_review'][0]/'query_inventory_reviewed_overlay.json')
    overlay={r['ticker']:r for r in reviewed_overlay}
    if any(overlay[t]['status']!='PLANNED_NOT_AUTHORIZED' for t in TICKERS):
        raise ValueError('BATCH_MEMBERS_ALREADY_COMPLETED_OR_HELD')
    protected=read(old_prep/'protected_old_files.json')
    for rel,_,_ in PARENTS.values():
        folder=project/rel
        for name in ['manifest.json',*read(folder/'manifest.json')['files']]:
            path=folder/name;protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    protected.update(speed.runtime(project))
    known=set(read(old_prep/'reusable_detail_provider_ids.json'))
    mbs_review=read(project/speed.base.SOURCES['mbs_review'][0]/'review.json')
    mbs_state=Path(mbs_review['inputs']['state']['path'])
    known.update(a['provider_article_id'] for a in read(mbs_state/'complete_query_articles.json')['articles'])
    for rel in [speed.PARENTS['baseline_run'][0],PARENTS['speed_run'][0]]:
        known.update(a['provider_article_id'] for a in read(project/rel/'deduplicated_query_articles.json'))
    out.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','cache_policy.json']:
        (out/name).write_bytes((old_prep/name).read_bytes())
    write(out/'known_discovery_provider_ids.json',sorted(known))
    write(out/'batch_plan.json',{'batch_id':'proposed-001','tickers':list(TICKERS),
        'archived_estimated_list_requests':54,'members':[inventory[t] for t in TICKERS],
        'status':'PREPARED_FOR_EXACT_LOCAL_USER_RUN_NOT_EXECUTED',
        'other_batches_executable':False,'details_enabled':False,
        'new_completion_credit_before_review':0,'pending_known_query_gaps_before_run':1100,
        'fresh_total_cap_per_query':400,'fresh_query_counts_may_change_within_caps':True,
        'same_session_full_lists_required':True,'no_stitching_archived_pages':True})
    write(out/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,
        'browser_launches':0,'readiness':mbs.old.readiness(config),'parents':PARENTS,
        'estimated_list_requests':54,'max_business_requests':100,'selected_queries':20,
        'reusable_detail_IDs':27731,'known_discovery_IDs':len(known),
        'phase':'LIST_DISCOVERY_ONLY_THEN_OFFLINE_REVIEW','canonical_or_owner_changes':False})
    write(out/'protected_old_files.json',protected);write(out/'runtime.json',runtime(project))
    write(out/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(out)})
    load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','source_requests':0,'selected_queries':20,
        'estimated_list_requests':54,'max_business_requests':100,'interval_seconds':4,
        'known_discovery_IDs':len(known),'protected_old_files':len(protected),'output':str(out)}


class Guard(speed.Guard):
    def admit(self,url,method,resource,body=None,redirected=False):
        self.shared.attempts+=1
        if self.shared.attempts>self.shared.config['max_context_attempts']:
            self.fail('BATCH_GLOBAL_CONTEXT_BUDGET')
        if url!=self.config['url']:
            return mbs.old.Guard.admit(self,url,method,resource,body,redirected)
        self.attempts+=1
        event={'event':'REQUEST_ATTEMPT','number':self.attempts,'url':url,'method':method,'resource_type':resource}
        try:
            self.check();self.check_old()
            if self.attempts>self.config['max_context_request_attempts']:
                raise ValueError('BROWSER_CONTEXT_REQUEST_BUDGET_EXHAUSTED')
            if redirected:raise ValueError('BROWSER_REDIRECT_NOT_FOLLOWED')
            if self.shared.business>=self.shared.config['max_business_requests']:
                raise ValueError('BATCH_GLOBAL_BUSINESS_BUDGET')
            if self.shared.last is not None and self.clock()-self.shared.last<INTERVAL:
                raise ValueError('BATCH_GLOBAL_FOUR_SECOND_INTERVAL_REQUIRED')
            index=len(self.business)
            if index>=self.config['max_list_pages_per_query']:raise ValueError('BATCH_QUERY_PAGE_BUDGET')
            if index==0:
                if method!='GET' or resource!='document' or body is not None:raise ValueError('FRESH_QUERY_GET_REQUIRED')
            elif (method!='POST' or resource not in {'xhr','fetch'}
                    or json.loads(body or 'null')!={'SearchKey':4,'CurrentPage':index+1}):
                raise ValueError('SEQUENTIAL_UI_QUERY_PAGE_REQUIRED')
            started=self.clock()
            if index==0:self.first_business_at=started
            self.business.append({'url':url,'method':method,'at_monotonic':started,'classification':'BUSINESS_LIST'})
            self.shared.business+=1;self.shared.last=started;self.allowed+=1
            event.update(allowed=True,classification='BUSINESS_LIST');self.log(event);return True
        except Exception as exc:
            self.fail(str(exc));event.update(allowed=False,stop_reason=self.stop_reason);self.log(event);return False


def list_page(fragment,number,ticker,total=None,seen=()):
    mbs.old.fragment_bytes(fragment,2000000)
    articles=speed.base.search_links(fragment.encode(),search_url(ticker));ids=[r['provider_article_id'] for r in articles]
    coverage=speed.base.snapshot_coverage(fragment.encode(),ids);count=coverage.get('reported_total')
    if (not isinstance(count,int) or not 1<=count<=400 or number not in range(1,21)
            or total is not None and count!=total or coverage.get('first')!=(number-1)*20+1
            or coverage.get('last')!=min(number*20,count) or len(ids)!=min(20,count-(number-1)*20)
            or len(set(ids))!=len(ids) or set(ids)&set(seen)):
        raise ValueError('BATCH_QUERY_RANGE_TOTAL_OR_ID_CONSISTENCY_REQUIRED')
    return {'ticker':ticker,'page':number,'coverage':coverage,'articles':articles,'article_ids':ids}


class Driver(mbs.Driver):
    def next_page(self,number,previous):
        selector=f'#divGlSearchArticles #d_number_of_page button[onclick="changePageArticles({number})"]'
        candidates=self.page.locator(selector)
        button=candidates.filter(has_text=re.compile(rf'^\s*{number}\s*$'))
        label=str(number)
        if button.count()==0:
            button=candidates.filter(has_text=re.compile(r'^\s*>\s*$'));label='>'
        if button.count()!=1:raise ValueError('UNIQUE_OBSERVED_SEQUENTIAL_PAGE_BUTTON_REQUIRED')
        self.guard.log({'event':'UI_PAGE_BUTTON','target_page':number,'visible_label':label,
                        'source_onclick':f'changePageArticles({number})'})
        with self.page.expect_response(lambda r:r.url==self.config['url'] and r.request.method=='POST',
                                       timeout=self.guard.timeout_ms()) as pending:
            button.click(timeout=self.guard.timeout_ms(),no_wait_after=True)
        response=pending.value;self.guard.check()
        if response.status!=200:raise ValueError('BATCH_NEXT_PAGE_HTTP200_REQUIRED')
        self.page.wait_for_function("old => {const el=document.querySelector('#divGlSearchArticles'); return el && el.outerHTML !== old;}",
                                    arg=previous,timeout=self.guard.timeout_ms())
        return self._snapshot(response,False)


def run(project,output,*,dry_run=False,driver_factory=Driver,clock=time.monotonic):
    project,output=Path(project).resolve(),Path(output).resolve()
    config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    ready=mbs.old.readiness(config)
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED',
        'source_requests':0,'browser_launched':False,'batch_tickers':list(TICKERS),'readiness':ready}
    output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','batch_plan.json','cache_policy.json','protected_old_files.json','known_discovery_provider_ids.json']:
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config);write(output/'runtime.json',runtime(project));write(output/'environment.json',ready)
    write(output/'input_provenance.json',{'preparation':str(prep),'manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'capture_kind':'PUBLIC_RENDERED_QUERY_FRAGMENTS_NOT_RAW_HTTP'})
    protected=read(prep/'protected_old_files.json');check=lambda:mbs.old.protected_check(project,protected)
    shared=SharedBudget(config,clock);guards=[];completed=[];all_articles=[];reusable=set(read(prep/'reusable_detail_provider_ids.json'))
    known=set(read(prep/'known_discovery_provider_ids.json'))
    checkpoint_seq=0
    def progress(event,ticker=None):
        nonlocal checkpoint_seq
        checkpoint_seq+=1
        folder=output/'checkpoints';folder.mkdir(exist_ok=True)
        write(folder/f'{checkpoint_seq:03d}.json',{'event':event,'ticker':ticker,'completed_tickers':list(completed),
            'business_requests':shared.business,'context_attempts':shared.attempts,'elapsed_seconds':clock()-shared.started,'resumable':False})
    result={'status':'STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED','resumable':False,'bulk_collection_ready':False,
        'browser_launches':0,'business_interval_seconds':4,'batch_id':'proposed-001','source_stopped':False,'detail_requests':0,'canonical_fields_applied':0,
        'normalized_observations':0,'pit_or_identity_promoted':False,'openai_api_calls':0}
    try:
        if not ready['ready']:raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
        for ticker in TICKERS:
            shared.check();check();progress('QUERY_START',ticker)
            folder=output/ticker;folder.mkdir();(folder/'network_ledger.jsonl').touch()
            local={**config,'ticker':ticker,'url':search_url(ticker),'max_seconds':config['max_query_seconds'],
                   'max_context_request_attempts':config['max_context_per_query'],'max_asset_attempts':config['max_assets_per_query']}
            guard=Guard(local,folder,check,clock,shared);guards.append((ticker,guard))
            try:
                with driver_factory(local,guard) as driver:
                    result['browser_launches']+=1
                    if shared.last is not None:driver.pace(max(0,INTERVAL-(clock()-shared.last)))
                    current=driver.first();guard.check()
                    write(folder/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,
                        'default_identity':True,'TLS_ignore_errors':False,'cookie_auth_exported':False})
                    write(folder/'fresh_source_contract.json',source_contract(current['scope_html'],ticker))
                    seen=[];query_articles=[];total=None;previous=''
                    for number in range(1,config['max_list_pages_per_query']+1):
                        if number>1:
                            check();driver.pace(max(0,INTERVAL-(clock()-shared.last)))
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
                    progress('QUERY_LIST_COMPLETE',ticker)
                    write(folder/'complete_query.json',{'ticker':ticker,'reported_total':total,'article_ids':seen,
                        'query_exhausted_in_session':True,'historical_event_coverage_certified':False})
                    guard.check()
                guard.check()
            finally:
                write(folder/'business_requests.json',guard.business);write(folder/'business_responses.json',guard.responses)
        if completed!=list(TICKERS):raise ValueError('ALL_TWENTY_QUERY_COMPLETIONS_REQUIRED')
        result['status']='PASS_BATCH001_LIST_DISCOVERY_REVIEW_REQUIRED'
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
                'query_tickers':[],'known_discovery_before_batch':aid in known,'detail_reusable_from_cache':aid in reusable,'detail_fetch_authorized':False,'event_identity_verified':False}
            row=dedup[aid]
            for field,value in [('titles',article['title']),('query_tickers',article['query_ticker'])]:
                if value not in row[field]:row[field].append(value)
        write(output/'deduplicated_query_articles.json',list(dedup.values()))
        result.update(completed_tickers=completed,context_request_attempts=shared.attempts,business_requests=shared.business,
            assets_attempts=sum(g.assets for _,g in guards),external_resources_blocked=sum(g.external_blocked for _,g in guards),
            unique_provider_IDs=len(dedup),reusable_cached_detail_IDs=sum(r['detail_reusable_from_cache'] for r in dedup.values()),
            new_candidate_IDs=sum(not r['detail_reusable_from_cache'] for r in dedup.values()),
            first_discovered_IDs=sum(not r['known_discovery_before_batch'] for r in dedup.values()),
            previously_discovered_uncached_IDs=sum(r['known_discovery_before_batch'] and not r['detail_reusable_from_cache'] for r in dedup.values()),
            elapsed_seconds=clock()-shared.started)
        progress('FINAL_REVIEW_REQUIRED')
        write(output/'checkpoint.json',{'status':result['status'],'resumable':False,'completed_tickers':completed,'old_runs_never_resumed':True})
        write(output/'result.json',result)
    return result
