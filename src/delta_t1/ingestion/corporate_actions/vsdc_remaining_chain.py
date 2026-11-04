"""One fixed user-run chain: proposed002..055, list discovery only, automatic batch validation."""
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import re
import time
import zipfile
from urllib.parse import urlsplit

from . import vsdc_speed2s_pilot as speed

batch=speed.batch001
mbs=speed.mbs
read,write,hashes,sha,seal=speed.read,speed.write,speed.hashes,speed.sha,speed.seal
verify_artifact,search_url=speed.verify_artifact,speed.search_url
source_contract,list_page,Driver=batch.source_contract,batch.list_page,batch.Driver
CONFIG='configs/data/corporate_actions/vsdc_remaining54_chain_v1.json'
PREP_TYPE='vsdc-remaining54-chain-preparation-v1'
TYPE='vsdc-remaining54-browser-list-chain-v1'
BATCH_TYPE='vsdc-chain-member-list-batch-v1'
BATCH_IDS=tuple(f'proposed-{i:03d}' for i in range(2,56))
PARENTS={
    'speed2_preparation':('data/corporate_actions/work/vsdc_three_query_speed2s_preparation_20261103_v1',
        '9e13437b8469e9754c9a0e272c676a8b18ca1d2bf5fe6a3b1fb22124b494b0a2',speed.PREP_TYPE),
    'speed2_run':('data/corporate_actions/work/vsdc_three_query_speed2s_pilot_v1/run-20261103T072216826201Z/state',
        '4d719a22c8e90bf3f2436d749e50dc868a98c48a14b2bec929c34b647e9efddf',speed.TYPE),
    'speed2_review':('data/corporate_actions/work/vsdc_three_query_speed2s_live_review_20261103_v1',
        'ea08122009b5890f6558295249a32d241de516d973246b921026ec0f1f9ca7e9',
        'vsdc-three-query-speed2s-offline-live-review-v1'),
}


def contract():
    return {'stage':'VSDC_REMAINING54_FIXED_CHAIN_PREPARATION_V1','batch_ids':list(BATCH_IDS),
        'output_base':'data/corporate_actions/work/vsdc_remaining54_chain_v1',
        'preparation':'data/corporate_actions/work/vsdc_remaining54_chain_preparation_20261103_v1',
        'selected_query_count':1073,'estimated_list_requests':2839,'business_interval_seconds':2,
        'max_list_pages_per_query':20,'max_business_requests':5400,'max_context_attempts':89094,
        'max_batch_business_requests':100,'max_batch_context_attempts':1660,
        'max_context_per_query':98,'max_assets_per_query':78,
        'max_seconds':28800,'max_batch_seconds':1200,'max_query_seconds':180,
        'operation_timeout_seconds':15,'max_html_bytes':2000000,'workers':1,
        'channel':'chrome','headless':False,'playwright_version':'1.57.0',
        'retry':False,'resume':False,'details':False,'persistent_profile':False,
        'ignore_https_errors':False,'export_cookies_or_auth':False,
        'canonical_build':False,'automatic_approval':False}


def validate(config):
    if config!=contract():raise ValueError('EXACT_REMAINING54_LIST_ONLY_CHAIN_REQUIRED')


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_remaining_chain.py',
        'scripts/corporate_actions/prepare_vsdc_remaining54_chain_v1.py',
        'scripts/corporate_actions/collect_vsdc_remaining54_chain_v1.py']
    return {**speed.runtime(project),**{name:sha((project/name).read_bytes()) for name in names}}


def parents(project):
    _,prep=speed.load_preparation(project)
    for name,(rel,digest,kind) in PARENTS.items():
        folder=project/rel
        if sha((folder/'manifest.json').read_bytes())!=digest:raise ValueError('CHAIN_PARENT_CHANGED: '+name)
        verify_artifact(folder,{kind})
    if read(project/PARENTS['speed2_review'][0]/'review.json')['status']!='PASS_BOUNDED_2S_INTERVAL_WITH_SAME_QUERY_DATA':
        raise ValueError('REVIEWED_2S_PILOT_PASS_REQUIRED')
    return prep


def validate_selection(selected,overlay):
    if [b['batch_id'] for b in selected]!=list(BATCH_IDS):raise ValueError('EXACT_BATCH002_TO055_ORDER_REQUIRED')
    tickers=[t for b in selected for t in b['tickers']]
    if len(tickers)!=1073 or len(set(tickers))!=1073:raise ValueError('EXACT_1073_UNIQUE_QUERIES_REQUIRED')
    if sum(b['estimated_list_requests'] for b in selected)!=2839:raise ValueError('ARCHIVED_REQUEST_ESTIMATE_CHANGED')
    indexed={r['ticker']:r for r in overlay}
    for b in selected:
        if not 1<=len(b['tickers'])<=20 or not 1<=b['estimated_list_requests']<=100:
            raise ValueError('PROPOSED_BATCH_CAP_CHANGED')
        if any(indexed.get(t,{}).get('status')!='PLANNED_NOT_AUTHORIZED' for t in b['tickers']):
            raise ValueError('COMPLETED_HELD_OR_UNKNOWN_QUERY_IN_CHAIN')
    return tickers


def load_preparation(project):
    config=read(project/CONFIG);validate(config);parents(project)
    prep=project/config['preparation'];verify_artifact(prep,{PREP_TYPE})
    if read(prep/'runtime.json')!=runtime(project) or read(prep/'plan.json')['config']!=config:
        raise ValueError('CHAIN_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    validate_selection(read(prep/'selected_batches.json'),read(prep/'query_inventory_before_chain.json'))
    if len(read(prep/'reusable_detail_provider_ids.json'))!=27731 or len(read(prep/'known_discovery_provider_ids.json'))!=28276:
        raise ValueError('CHAIN_CACHE_OR_DISCOVERY_OVERLAY_CHANGED')
    return config,prep


def prepare(project):
    project=Path(project).resolve();config=read(project/CONFIG);validate(config)
    old_prep=parents(project);out=project/config['preparation']
    if out.exists():raise FileExistsError('REFUSE_OVERWRITE')
    old_plan=project/speed.previous.base.contract()['preparation']
    selected=read(old_plan/'proposed_batches.json')[1:]
    reviewed=project/speed.PARENTS['batch001_review'][0]
    overlay=read(reviewed/'query_inventory_reviewed_overlay.json')
    validate_selection(selected,overlay)
    protected=read(old_prep/'protected_old_files.json')
    for rel,_,_ in PARENTS.values():
        folder=project/rel
        for name in ['manifest.json',*read(folder/'manifest.json')['files']]:
            path=folder/name;protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    protected.update(speed.runtime(project))
    out.mkdir(parents=True)
    for name in ['reusable_detail_provider_ids.json','known_discovery_provider_ids.json','cache_policy.json']:
        (out/name).write_bytes((old_prep/name).read_bytes())
    write(out/'selected_batches.json',selected);write(out/'query_inventory_before_chain.json',overlay)
    write(out/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,'browser_launches':0,
        'readiness':mbs.old.readiness(config),'execution_scope':'ALL54_REMAINING_PROPOSED_LIST_BATCHES_IN_ONE_USER_RUN',
        'parents':PARENTS,'batch_transition':'Seal ZIP, verify all hashes/CRC, reparse all pages and ledgers before next batch',
        'known_pending_before_run':1080,'normal_selected':1073,'large_HOLD_excluded':7,
        'archived_exhausted_outside_chain':414,'unverified_outside_chain':['DTR','KAI','LPS','PCB'],
        'detail_cache_IDs':27731,'known_discovery_IDs':28276,
        'new_details_or_canonical_or_owner_changes':False,'no_retry_resume_or_rate_fallback':True})
    write(out/'protected_old_files.json',protected);write(out/'runtime.json',runtime(project))
    write(out/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(out)})
    load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','batch_count':54,'selected_queries':1073,'estimated_list_requests':2839,
        'interval_seconds':2,'source_requests':0,'protected_old_files':len(protected),'output':str(out)}


def ids_hash(ids):
    return sha(json.dumps(sorted(ids),separators=(',',':')).encode())


class Budget:
    def __init__(self,config,clock):
        self.config,self.clock=config,clock;self.started=clock();self.attempts=self.business=0;self.last=None
        self.active=None;self.batch_started=None;self.batch_attempt_start=self.batch_business_start=0
        self.previous_start=None
    def check(self):
        if self.clock()-self.started>=self.config['max_seconds']:raise ValueError('CHAIN_GLOBAL_TIME_BUDGET')
        if self.active and self.clock()-self.batch_started>=self.config['max_batch_seconds']:
            raise ValueError('CHAIN_BATCH_TIME_BUDGET')
    def begin(self,batch_id):
        self.check()
        if self.active:raise ValueError('CHAIN_BATCH_ALREADY_ACTIVE')
        self.active=batch_id;self.batch_started=self.clock();self.previous_start=self.last
        self.batch_attempt_start=self.attempts;self.batch_business_start=self.business
    def end(self):
        self.check();self.active=None


class Guard(batch.Guard):
    def timeout_ms(self):
        remaining=self.shared.config['max_batch_seconds']-(self.clock()-self.shared.batch_started)
        return min(super().timeout_ms(),max(1,int(remaining*1000)))
    def admit(self,url,method,resource,body=None,redirected=False):
        self.shared.attempts+=1
        if not self.shared.active:self.fail('NO_ACTIVE_CHAIN_BATCH')
        if self.shared.attempts>self.shared.config['max_context_attempts']:self.fail('CHAIN_GLOBAL_CONTEXT_BUDGET')
        if self.shared.attempts-self.shared.batch_attempt_start>self.shared.config['max_batch_context_attempts']:
            self.fail('CHAIN_BATCH_CONTEXT_BUDGET')
        if url!=self.config['url']:return mbs.old.Guard.admit(self,url,method,resource,body,redirected)
        self.attempts+=1
        event={'event':'REQUEST_ATTEMPT','number':self.attempts,'url':url,'method':method,'resource_type':resource}
        try:
            self.check();self.check_old()
            if self.attempts>self.config['max_context_request_attempts']:raise ValueError('QUERY_CONTEXT_BUDGET')
            if redirected:raise ValueError('BROWSER_REDIRECT_NOT_FOLLOWED')
            if self.shared.business>=self.shared.config['max_business_requests']:raise ValueError('CHAIN_GLOBAL_BUSINESS_BUDGET')
            if self.shared.business-self.shared.batch_business_start>=self.shared.config['max_batch_business_requests']:
                raise ValueError('CHAIN_BATCH_BUSINESS_BUDGET')
            if self.shared.last is not None and self.clock()-self.shared.last<2:raise ValueError('CHAIN_SHARED_TWO_SECOND_INTERVAL')
            index=len(self.business)
            if index>=20:raise ValueError('QUERY_TWENTY_PAGE_CAP')
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


def deduplicate(articles,reusable,known):
    merged={}
    for a in articles:
        aid=a['provider_article_id']
        if aid not in merged:merged[aid]={'provider_article_id':aid,'url':a['url'],'titles':[],'query_tickers':[],
            'known_discovery_before_batch':aid in known,'detail_reusable_from_cache':aid in reusable,
            'detail_fetch_authorized':False,'event_identity_verified':False}
        row=merged[aid]
        for field,val in [('titles',a['title']),('query_tickers',a['query_ticker'])]:
            if val not in row[field]:row[field].append(val)
    return list(merged.values())


def acquire_batch(project,folder,definition,config,prep,shared,reusable,known,check_old,driver_factory,clock):
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
        'detail_requests':0,'canonical_fields_applied':0,'browser_launches':0,'business_interval_seconds':2}
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
                        'default_identity':True,'TLS_ignore_errors':False,'cookie_auth_exported':False})
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


def verify_sealed_zip(folder,archive):
    reference=verify_artifact(folder,{BATCH_TYPE});manifest=read(folder/'manifest.json')
    expected=set(manifest['files'])|{'manifest.json'}
    if {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}!=expected:
        raise ValueError('BATCH_MANIFEST_FILE_SET_MISMATCH')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())) or set(z.namelist())!=expected:
            raise ValueError('BATCH_ZIP_CRC_OR_MEMBER_MISMATCH')
        for name in expected:
            if z.read(name)!=(folder/name).read_bytes():raise ValueError('BATCH_ZIP_STATE_MISMATCH: '+name)
    return reference


def validate_batch(folder,archive,definition,config,reusable,known,previous_start):
    """Offline transition gate: complete source lists plus exact sealed evidence, no network."""
    reference=verify_sealed_zip(folder,archive)
    result=read(folder/'result.json')
    if (result['status']!='PASS_SOURCE_BATCH_REQUIRES_AUTOMATED_VALIDATION' or result['source_stopped']
            or result['completed_tickers']!=definition['tickers'] or result['detail_requests']
            or result['canonical_fields_applied'] or result['resumable']):
        raise ValueError('BATCH_SOURCE_NOT_COMPLETE_OR_STOPPED')
    if read(folder/'batch_plan.json')!=definition or read(folder/'chain_config.json')!=config:
        raise ValueError('BATCH_CONFIG_SCOPE_MISMATCH')
    provenance=read(folder/'input_provenance.json')
    if (provenance['known_before_batch_sha256']!=ids_hash(known)
            or provenance['reusable_detail_IDs_sha256']!=ids_hash(reusable)
            or provenance['previous_business_start']!=previous_start
            or provenance['capture_kind']!='PUBLIC_RENDERED_FRAGMENTS_NOT_RAW_HTTP'):
        raise ValueError('BATCH_CACHE_OR_PACING_PROVENANCE_MISMATCH')
    checkpoints=sorted((folder/'checkpoints').glob('*.json'))
    expected_events=[(event,t) for t in definition['tickers'] for event in ('QUERY_START','QUERY_LIST_COMPLETE')]
    expected_events.append(('FINAL_BATCH_REVIEW_REQUIRED',None))
    if [p.name for p in checkpoints]!=[f'{i:03}.json' for i in range(1,len(expected_events)+1)]:
        raise ValueError('BATCH_CHECKPOINT_SEQUENCE_MISMATCH')
    completed=[];previous_counts=(0,0)
    for path,(event,ticker) in zip(checkpoints,expected_events):
        row=read(path)
        if event=='QUERY_LIST_COMPLETE':completed.append(ticker)
        counts=(row['batch_business_requests'],row['batch_context_attempts'])
        if (row['event']!=event or row['ticker']!=ticker or row['completed_tickers']!=completed
                or row['resumable'] or any(a<b for a,b in zip(counts,previous_counts))):
            raise ValueError('BATCH_CHECKPOINT_CONTENT_MISMATCH')
        previous_counts=counts
    if (previous_counts!=(result['business_requests'],result['context_attempts'])
            or result['browser_launches']!=len(definition['tickers'])
            or result['business_interval_seconds']!=2
            or not 0<=result['elapsed_seconds']<config['max_batch_seconds']):
        raise ValueError('BATCH_FINAL_CHECKPOINT_OR_TIMING_MISMATCH')
    articles=[];calls=[];attempt_total=allowed_total=assets_total=blocked_total=0;query_rows={}
    for ticker in definition['tickers']:
        query=folder/ticker;complete=read(query/'complete_query.json');seen=[];query_articles=[]
        total=complete['reported_total'];pages=math.ceil(total/20)
        if complete['ticker']!=ticker or not complete['query_exhausted_in_session'] or complete['historical_event_coverage_certified']:
            raise ValueError('QUERY_COMPLETION_CLASSIFICATION_MISMATCH')
        for number in range(1,pages+1):
            data=(query/f'rendered_html/page{number}.html').read_bytes();text=data.decode('utf8')
            mbs.old.fragment_bytes(text,config['max_html_bytes'])
            parsed=list_page(text,number,ticker,total if number>1 else None,seen)
            if parsed!=read(query/f'page{number}.json'):raise ValueError('QUERY_REPARSE_MISMATCH')
            receipt=read(query/f'page{number}_receipt.json')
            if (receipt['fragment_sha256']!=sha(data) or receipt['url']!=search_url(ticker)
                    or receipt['http_status']!=200 or receipt['page']!=number or receipt['raw_http_body_archived']
                    or not re.fullmatch('[0-9a-f]{64}',receipt['http_body_hash_not_archived'])
                    or not 0<receipt['http_body_bytes']<=config['max_html_bytes']):raise ValueError('QUERY_RECEIPT_MISMATCH')
            seen.extend(parsed['article_ids']);query_articles.extend(parsed['articles'])
        if (seen!=complete['article_ids'] or len(seen)!=total
                or len(list((query/'rendered_html').glob('*.html')))!=pages):raise ValueError('QUERY_LIST_FILE_OR_COUNT_MISMATCH')
        contract=read(query/'fresh_source_contract.json')
        wrapper='<p>Kết quả tìm kiếm với từ: '+ticker+'</p><div id="divGlSearchArticles"></div><script>'+contract['script']+'</script>'
        if source_contract(wrapper,ticker)!=contract:raise ValueError('QUERY_SCOPE_JS_CONTRACT_MISMATCH')
        browser=read(query/'browser.json')
        if (browser['channel']!='chrome' or not browser['default_identity'] or browser['persistent']
                or browser['TLS_ignore_errors'] or browser['cookie_auth_exported']):raise ValueError('BROWSER_POLICY_MISMATCH')
        requests=read(query/'business_requests.json');responses=read(query/'business_responses.json')
        if (len(requests)!=pages or len(responses)!=pages or [r['method'] for r in requests]!=['GET']+['POST']*(pages-1)
                or [r['status'] for r in responses]!=[200]*pages):raise ValueError('QUERY_BUSINESS_SEQUENCE_OR_RESPONSE_MISMATCH')
        for i,r in enumerate(requests):
            if (r['url']!=search_url(ticker) or r['classification']!='BUSINESS_LIST'
                    or set(r)!={'url','method','at_monotonic','classification','request_header_names','request_content_type','x_requested_with'}):
                raise ValueError('QUERY_SAFE_REQUEST_METADATA_MISMATCH')
            if i and (r['request_content_type'] not in {'application/json;charset=UTF-8','application/json;charset=utf-8'}
                      or r['x_requested_with']!='XMLHttpRequest'):raise ValueError('OBSERVED_AJAX_HEADERS_MISMATCH')
        for i,r in enumerate(responses):
            if (r['url']!=search_url(ticker) or r['method']!=requests[i]['method']
                    or set(r['headers'])!={'content-type','content-length','retry-after'} or r['headers']['retry-after']):
                raise ValueError('QUERY_SAFE_RESPONSE_METADATA_MISMATCH')
        ledger=mbs.old.rows(query/'network_ledger.jsonl');attempts=[r for r in ledger if r['event']=='REQUEST_ATTEMPT']
        if (len(attempts)>config['max_context_per_query'] or [r['number'] for r in attempts]!=list(range(1,len(attempts)+1))
                or any('stop_reason' in r for r in ledger)):raise ValueError('QUERY_NETWORK_BOUNDARY_OR_CAP_FAILURE')
        business=[r for r in attempts if r['classification']=='BUSINESS_LIST']
        assets=[r for r in attempts if r['classification'] in {'FIRST_PARTY_ASSET','EXTERNAL_RESOURCE_BLOCKED'}]
        if len(business)!=pages or len(assets)>config['max_assets_per_query'] or len(business)+len(assets)!=len(attempts):
            raise ValueError('QUERY_NETWORK_CLASSIFICATION_MISMATCH')
        if ([(r['url'],r['method'],r['allowed']) for r in business]
                !=[(r['url'],r['method'],True) for r in requests]):
            raise ValueError('QUERY_REQUEST_LEDGER_MISMATCH')
        if [r for r in ledger if r['event']=='BUSINESS_RESPONSE']!=[{'event':'BUSINESS_RESPONSE',**r} for r in responses]:
            raise ValueError('QUERY_RESPONSE_LEDGER_MISMATCH')
        for r in attempts:
            u=urlsplit(r['url'])
            if r['allowed']:
                if u.scheme!='https' or u.hostname!='vsdc.vn':raise ValueError('NETWORK_HOST_OUTSIDE_SCOPE')
                if r['classification']=='FIRST_PARTY_ASSET':
                    if r['method']!='GET' or not(u.path.startswith(mbs.old.STATIC_PREFIXES) or u.path=='/favicon.ico'):
                        raise ValueError('NETWORK_ASSET_OUTSIDE_SCOPE')
                elif r['url']!=search_url(ticker):raise ValueError('NETWORK_QUERY_OUTSIDE_SCOPE')
            elif r['classification']!='EXTERNAL_RESOURCE_BLOCKED':raise ValueError('NETWORK_UNEXPECTED_BLOCKED_REQUEST')
        if len(requests)>1:
            ui=[r for r in ledger if r['event']=='UI_PAGE_BUTTON']
            if ([r['target_page'] for r in ui]!=list(range(2,pages+1))
                    or any(r['source_onclick']!=f"changePageArticles({r['target_page']})"
                           or r['visible_label'] not in {str(r['target_page']), '>'} for r in ui)):
                raise ValueError('OBSERVED_UI_PAGINATION_SEQUENCE_MISMATCH')
        calls.extend(requests);articles.extend({**a,'query_ticker':ticker} for a in query_articles);query_rows[ticker]=total
        attempt_total+=len(attempts);allowed_total+=sum(r['allowed'] for r in attempts)
        assets_total+=len(assets);blocked_total+=sum(not r['allowed'] for r in attempts)
    starts=([previous_start] if previous_start is not None else [])+[r['at_monotonic'] for r in calls]
    if any(not math.isfinite(s) for s in starts) or any(b-a<2 for a,b in zip(starts,starts[1:])):
        raise ValueError('CHAIN_PACING_BELOW_TWO_SECONDS')
    if len(calls)>config['max_batch_business_requests'] or attempt_total>config['max_batch_context_attempts']:
        raise ValueError('BATCH_REQUEST_CAP_EXCEEDED')
    merged=deduplicate(articles,reusable,known)
    if merged!=read(folder/'deduplicated_query_articles.json'):raise ValueError('BATCH_CACHE_DEDUP_PROVENANCE_MISMATCH')
    expected={'business_requests':len(calls),'context_attempts':attempt_total,'asset_attempts':assets_total,
        'external_blocks':blocked_total,'unique_provider_IDs':len(merged),
        'cached_detail_IDs':sum(r['detail_reusable_from_cache'] for r in merged),
        'uncached_candidate_IDs':sum(not r['detail_reusable_from_cache'] for r in merged),
        'first_discovered_IDs':sum(not r['known_discovery_before_batch'] for r in merged)}
    if any(result[k]!=v for k,v in expected.items()):raise ValueError('BATCH_RESULT_COUNTER_MISMATCH')
    return {'status':'PASS_AUTOMATED_BATCH_VALIDATION','batch_id':definition['batch_id'],'state':reference,
        'zip_sha256':sha(archive.read_bytes()),'query_rows':query_rows,'context_admissions':allowed_total,**expected}


def run(project,output,*,dry_run=False,driver_factory=Driver,clock=time.monotonic,emit=print):
    project,output=Path(project).resolve(),Path(output).resolve();config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    selected=read(prep/'selected_batches.json');ready=mbs.old.readiness(config)
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED','source_requests':0,
        'browser_launched':False,'selected_batches':len(selected),'selected_queries':sum(len(b['tickers']) for b in selected),'readiness':ready}
    output.mkdir(parents=True);zip_folder=output.parent/'batch_zips';zip_folder.mkdir()
    for name in ['selected_batches.json','reusable_detail_provider_ids.json','known_discovery_provider_ids.json',
                 'cache_policy.json','protected_old_files.json','query_inventory_before_chain.json']:
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config);write(output/'runtime.json',runtime(project));write(output/'environment.json',ready)
    write(output/'input_provenance.json',{'preparation':str(prep),'manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'capture_kind':'PUBLIC_RENDERED_LIST_FRAGMENTS_NOT_RAW_HTTP','separate_batch_zips':str(zip_folder)})
    protected=read(prep/'protected_old_files.json');check=lambda:mbs.old.protected_check(project,protected)
    reusable=set(read(prep/'reusable_detail_provider_ids.json'));known=set(read(prep/'known_discovery_provider_ids.json'))
    initial_known=set(known);shared=Budget(config,clock);passed=[];records=[];global_rows={};active=None;seq=0
    result={'status':'STOPPED_CHAIN_SOURCE_OR_INTEGRITY','resumable':False,'detail_requests':0,'canonical_fields_applied':0,
        'normalized_observations':0,'pit_or_identity_promoted':False,'owner_choices_changed':False,'openai_api_calls':0,
        'failed_batch':None,'browser_launches':0}
    def progress(event):
        nonlocal seq
        seq+=1;folder=output/'checkpoints';folder.mkdir(exist_ok=True)
        write(folder/f'{seq:03}.json',{'event':event,'active_batch':active,'validated_batches':list(passed),
            'business_requests':shared.business,'context_attempts':shared.attempts,'resumable':False,
            'elapsed_seconds':clock()-shared.started})
    try:
        if not ready['ready']:raise ValueError('LOCAL_PLAYWRIGHT_CHROME_SETUP_REQUIRED')
        for definition in selected:
            active=definition['batch_id'];check();shared.begin(active);progress('BATCH_START')
            emit(json.dumps({'event':'BATCH_START','batch_id':active,'tickers':len(definition['tickers'])}),flush=True)
            folder=output/'batches'/active/'state'
            acquired=acquire_batch(project,folder,definition,config,prep,shared,reusable,known,check,driver_factory,clock)
            result['browser_launches']+=acquired['browser_launches']
            check();archive=zip_folder/(active+'.zip');seal(folder,archive,artifact_type=BATCH_TYPE)
            try:
                checked=validate_batch(folder,archive,definition,config,reusable,known,shared.previous_start)
                if read(folder/'runtime.json')!=runtime(project):raise ValueError('BATCH_RUNTIME_CHANGED')
                check();shared.check()
            except Exception as exc:
                checked={'status':'FAIL_AUTOMATED_BATCH_VALIDATION','batch_id':active,'reason':str(exc)}
                write(folder.parent/'validation.json',checked);records.append(checked);progress('BATCH_STOPPED')
                raise ValueError('BATCH_NOT_PASSED: '+active+'; '+str(exc)) from exc
            write(folder.parent/'validation.json',checked);records.append(checked);passed.append(active)
            for row in read(folder/'deduplicated_query_articles.json'):
                aid=row['provider_article_id']
                if aid not in global_rows:global_rows[aid]={'provider_article_id':aid,'url':row['url'],'titles':[],
                    'query_tickers':[],'batch_ids':[],'known_discovery_before_chain':aid in initial_known,
                    'detail_reusable_from_cache':aid in reusable,'detail_fetch_authorized':False,'event_identity_verified':False}
                target=global_rows[aid]
                for field,values in [('titles',row['titles']),('query_tickers',row['query_tickers']),('batch_ids',[active])]:
                    for value in values:
                        if value not in target[field]:target[field].append(value)
                known.add(aid)
            shared.end();progress('BATCH_VALIDATED')
            emit(json.dumps({'event':'BATCH_VALIDATED','batch_id':active,'validated_batches':len(passed),
                'query_count':len(definition['tickers']),'business_requests':checked['business_requests']}),flush=True)
            active=None
        if passed!=[b['batch_id'] for b in selected]:raise ValueError('ALL_SELECTED_BATCHES_NOT_VALIDATED')
        result['status']='PASS_ALL_SELECTED_BATCHES_AUTOMATED_VALIDATION_REVIEW_REQUIRED'
    except KeyboardInterrupt:result.update(status='CANCELLED_CHAIN_NO_REPLAY',failed_batch=active,stop_reason='USER_INTERRUPT')
    except Exception as exc:result.update(status='STOPPED_CHAIN_SOURCE_OR_INTEGRITY',failed_batch=active,stop_reason=str(exc))
    finally:
        try:check()
        except Exception as exc:result.update(status='STOPPED_CHAIN_PROTECTED_INPUT_CHANGED',failed_batch=active,stop_reason=str(exc))
        result.update(validated_batch_ids=passed,validated_batch_count=len(passed),
            validated_query_count=sum(len(b['tickers']) for b in selected if b['batch_id'] in passed),
            business_requests=shared.business,context_attempts=shared.attempts,elapsed_seconds=clock()-shared.started,
            unique_provider_IDs_in_validated_batches=len(global_rows),
            cached_detail_IDs=sum(r['detail_reusable_from_cache'] for r in global_rows.values()),
            uncached_candidate_IDs=sum(not r['detail_reusable_from_cache'] for r in global_rows.values()),
            first_discovered_IDs=sum(not r['known_discovery_before_chain'] for r in global_rows.values()),
            known_discovery_IDs_after_validated_batches=len(known),reusable_detail_IDs_unchanged=len(reusable),
            manual_offline_review_pending=True)
        write(output/'batch_validation_index.json',records)
        write(output/'deduplicated_validated_query_articles.json',list(global_rows.values()))
        write(output/'known_discovery_provider_ids_after_validated_batches.json',sorted(known))
        progress('FINAL_CHAIN_REVIEW_REQUIRED');write(output/'result.json',result)
        write(output/'checkpoint.json',{'status':result['status'],'validated_batch_ids':passed,'failed_batch':result['failed_batch'],
            'resumable':False,'old_runs_never_resumed':True})
    return result
