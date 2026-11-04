"""Separately frozen four-second experiment, never modifies the reviewed8s run."""
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import time

from . import vsdc_supplement_plan as base

mbs=base.mbs
read,write,hashes,sha,seal=base.read,base.write,base.hashes,base.sha,base.seal
verify_artifact,search_url=base.verify_artifact,base.search_url
source_contract,list_page=base.source_contract,base.list_page
PILOT=base.PILOT
SharedBudget=base.SharedBudget
CONFIG="configs/data/corporate_actions/vsdc_three_query_speed4s_pilot_v1.json"
PREP_TYPE="vsdc-three-query-speed4s-preparation-v1"
TYPE="vsdc-three-query-speed4s-browser-list-pilot-v1"
INTERVAL=4
PARENTS={
    'baseline_preparation':('data/corporate_actions/work/vsdc_supplement_plan_preparation_20261103_v1',
        'f4c2dab982359dccc8e8a86234cb944460307488443e9638c3e3fbe490efc412',base.PREP_TYPE),
    'baseline_run':('data/corporate_actions/work/vsdc_three_query_browser_pilot_v1/run-20261103T061831245900Z/state',
        'b3f8e74296e3e3cbe8f087e1b9aa2962cf7e82da769e9895d679daa55c0aeb4e',base.TYPE),
    'baseline_review':('data/corporate_actions/work/vsdc_three_query_browser_live_review_20261103_v1',
        '5fab1a45d191a263a6d5d15afd8c5e8896bf9723d38996a89d42ec03f20b4e01',
        'vsdc-three-query-browser-offline-live-review-v1'),
}


def contract():
    return {**base.contract(),'stage':'VSDC_THREE_QUERY_SPEED4S_PREPARATION_V1',
        'business_interval_seconds':4,
        'output_base':'data/corporate_actions/work/vsdc_three_query_speed4s_pilot_v1',
        'preparation':'data/corporate_actions/work/vsdc_three_query_speed4s_preparation_20261103_v1'}


def validate(config):
    if config!=contract():raise ValueError('EXACT_FIXED_FOUR_SECOND_EXPERIMENT_REQUIRED')


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_speed4s_pilot.py',
        'scripts/corporate_actions/prepare_vsdc_three_query_speed4s_pilot_v1.py',
        'scripts/corporate_actions/collect_vsdc_three_query_speed4s_pilot_v1.py']
    return {**base.runtime(project),**{name:sha((project/name).read_bytes()) for name in names}}


def parents(project):
    _,prep=base.load_preparation(project)
    for name,(rel,digest,kind) in PARENTS.items():
        path=project/rel
        if sha((path/'manifest.json').read_bytes())!=digest:raise ValueError('SPEED_BASELINE_CHANGED: '+name)
        verify_artifact(path,{kind})
    baseline=read(project/PARENTS['baseline_review'][0]/'review.json')
    if baseline['status']!='PASS_THREE_EXCHANGES_LIST_AND_CACHE_DEDUP_VALIDATION':
        raise ValueError('REVIEWED_8S_BASELINE_PASS_REQUIRED')
    return prep,baseline


def load_preparation(project):
    config=read(project/CONFIG);validate(config);parents(project)
    prep=project/config['preparation'];verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('SPEED_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    return config,prep


def prepare(project):
    project=Path(project).resolve();config=read(project/CONFIG);validate(config)
    old_prep,baseline=parents(project);out=project/config['preparation']
    if out.exists():raise FileExistsError('REFUSE_OVERWRITE')
    protected=read(old_prep/'protected_old_files.json')
    for rel,_,_ in PARENTS.values():
        folder=project/rel
        for name in ['manifest.json',*read(folder/'manifest.json')['files']]:
            path=folder/name;protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    protected.update(base.runtime(project))
    out.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','pilot_plan.json','cache_policy.json']:
        (out/name).write_bytes((old_prep/name).read_bytes())
    write(out/'experiment.json',{'kind':'REPEAT_SAME_THREE_QUERY_LIST_PILOT_AT_FOUR_SECONDS',
        'baseline_interval_seconds':8,'experimental_interval_seconds':4,
        'baseline_review':{'path':PARENTS['baseline_review'][0],'manifest_sha256':PARENTS['baseline_review'][1]},
        'baseline_query_rows':{r['ticker']:r['query_rows'] for r in baseline['query_summaries']},
        'baseline_business_requests':7,'baseline_elapsed_seconds':baseline['observations']['elapsed_seconds'],
        'expected_new_query_completion_credit':0,
        'acceptance':'All three fresh query lists complete, consistent ranges/totals/IDs, all business200, no boundary errors; review timings offline.',
        'limits':'A single small success is not proof of long-run safe rate or guaranteed2x speed; changed rows/assets/timings affect comparability.',
        'on_error':'STOP entire run; no retries, interval escalation, fallback to8s or alternate profile in this run.',
        'global_pending_queries_still':1100,'detail_downloads':False,'bulk_authorized':False})
    write(out/'protected_old_files.json',protected);write(out/'runtime.json',runtime(project))
    write(out/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,
        'browser_launches':0,'readiness':mbs.old.readiness(config),
        'only_acquisition_policy_change':'Minimum interval between admitted business request starts8s->4s, including ticker transitions',
        'all_other_caps_and_source_access_privacy_gates_unchanged':True,
        'same_query_reread_for_speed_experiment_not_new_missing_query_work':True})
    write(out/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(out)})
    load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','source_requests':0,'interval_seconds':4,
        'pilot_tickers':list(PILOT),'protected_old_files':len(protected),'output':str(out)}


class Guard(base.Guard):
    def admit(self,url,method,resource,body=None,redirected=False):
        self.shared.attempts+=1
        if self.shared.attempts>self.shared.config['max_context_attempts']:
            self.fail('PILOT_GLOBAL_CONTEXT_BUDGET')
        if url!=self.config['url']:
            # Reuse the unchanged static-resource/redirect/access gates directly.
            # The business branch below is independent of frozen8s business guards.
            return mbs.old.Guard.admit(self,url,method,resource,body,redirected)
        self.attempts+=1
        event={'event':'REQUEST_ATTEMPT','number':self.attempts,'url':url,
               'method':method,'resource_type':resource}
        try:
            self.check();self.check_old()
            if self.attempts>self.config['max_context_request_attempts']:
                raise ValueError('BROWSER_CONTEXT_REQUEST_BUDGET_EXHAUSTED')
            if redirected:raise ValueError('BROWSER_REDIRECT_NOT_FOLLOWED')
            if self.shared.business>=self.shared.config['max_business_requests']:
                raise ValueError('PILOT_GLOBAL_BUSINESS_BUDGET')
            if self.shared.last is not None and self.clock()-self.shared.last<INTERVAL:
                raise ValueError('PILOT_GLOBAL_FOUR_SECOND_INTERVAL_REQUIRED')
            index=len(self.business)
            if index>=4:raise ValueError('MAX_FOUR_LIST_PAGES_REQUIRED')
            if index==0:
                if method!='GET' or resource!='document' or body is not None:
                    raise ValueError('FRESH_QUERY_GET_REQUIRED')
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


def run(project,output,*,dry_run=False,driver_factory=mbs.Driver,clock=time.monotonic):
    project,output=Path(project).resolve(),Path(output).resolve()
    config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    ready=mbs.old.readiness(config)
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED',
        'source_requests':0,'browser_launched':False,'pilot_tickers':list(PILOT),'readiness':ready}
    output.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','pilot_plan.json','cache_policy.json','protected_old_files.json','experiment.json']:
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config);write(output/'runtime.json',runtime(project));write(output/'environment.json',ready)
    write(output/'input_provenance.json',{'preparation':str(prep),'manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'capture_kind':'PUBLIC_RENDERED_QUERY_FRAGMENTS_NOT_RAW_HTTP'})
    protected=read(prep/'protected_old_files.json');check=lambda:mbs.old.protected_check(project,protected)
    shared=SharedBudget(config,clock);guards=[];completed=[];all_articles=[];reusable=set(read(prep/'reusable_detail_provider_ids.json'))
    result={'status':'STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED','resumable':False,'bulk_collection_ready':False,
        'browser_launches':0,'business_interval_seconds':4,'source_stopped':False,'detail_requests':0,'canonical_fields_applied':0,
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
                    if shared.last is not None:driver.pace(max(0,INTERVAL-(clock()-shared.last)))
                    current=driver.first();guard.check()
                    write(folder/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,
                        'default_identity':True,'TLS_ignore_errors':False,'cookie_auth_exported':False})
                    write(folder/'fresh_source_contract.json',source_contract(current['scope_html'],ticker))
                    seen=[];query_articles=[];total=None;previous=''
                    for number in range(1,5):
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
                    write(folder/'complete_query.json',{'ticker':ticker,'reported_total':total,'article_ids':seen,
                        'query_exhausted_in_session':True,'historical_event_coverage_certified':False})
                    guard.check()
                guard.check()
            finally:
                write(folder/'business_requests.json',guard.business);write(folder/'business_responses.json',guard.responses)
        if completed!=list(PILOT):raise ValueError('ALL_THREE_QUERY_COMPLETIONS_REQUIRED')
        result['status']='PASS_FOUR_SECOND_PILOT_REVIEW_REQUIRED'
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
