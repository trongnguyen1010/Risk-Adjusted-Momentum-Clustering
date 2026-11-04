"""Pilot 5 full queries ở 4 giây; giữ V3 STOP và diagnostic cũ bất biến."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

from . import vsdc_app_diagnostic as diagnostic

prior = diagnostic.prior
base, mbs = prior.base, prior.mbs
read, write, sha, hashes = prior.read, prior.write, prior.sha, prior.hashes
source_contract, list_page, search_url = prior.source_contract, prior.list_page, prior.search_url
ids_hash, deduplicate = prior.ids_hash, prior.deduplicate
body_evidence = diagnostic.body_evidence
CONFIG = 'configs/data/corporate_actions/vsdc_five_query4s_pilot_v1.json'
OUTPUT = 'data/corporate_actions/work/vsdc_five_query4s_pilot_v1'
PREP = 'data/corporate_actions/work/vsdc_five_query4s_preparation_20261103_v1'
TYPE = 'vsdc-five-full-query-four-second-pilot-v1'
QUERY_TYPE = 'vsdc-four-second-pilot-query-v1'
PREP_TYPE = 'vsdc-five-full-query-four-second-preparation-v1'
PASS = 'PASS_FIVE_QUERY4S_PILOT_REVIEW_REQUIRED'
STOP = 'STOPPED_FIVE_QUERY4S_PILOT_REVIEW_REQUIRED'
TICKERS = ('APP', 'APS', 'ARM', 'ART', 'ASG')
EXPECTED_ROWS = dict(zip(TICKERS, (43, 27, 37, 21, 22)))
DIAG_RUN = diagnostic.OUTPUT + '/run-20261103T104801448029Z'
DIAG_REVIEW = 'data/corporate_actions/work/vsdc_app_diagnostic_live_review_20261103_v1'
PARENTS = {
    diagnostic.PREP: ('ef91ab57e6bbf9830d789774516fcced22fc6f4516ef3a7e70e6ba01b7b531fd', diagnostic.PREP_TYPE),
    DIAG_RUN + '/state': ('5b5613428d677e85d0b6964f91958a6ae8af78acd47a04b95ff7ba2e4ecc93c2', diagnostic.TYPE),
    DIAG_REVIEW: ('046ff722c92afc293fd8e0d0cfab6c556d0ca2f749bd31152daac193e0596093',
                  'vsdc-app-single-get-diagnostic-offline-live-review-v1'),
    'data/corporate_actions/work/vsdc_app_diagnostic_validation_20261103_v1':
        ('fa627234d2afc4b3bbd8262fea963c92b6d488dac11f22b6bcbd41d283e8f361',
         'vsdc-app-single-get-diagnostic-preparation-validation-v1'),
}


def safe_reason(error):
    message = str(error)
    if len(message) <= 200 and re.fullmatch(r'(?:PILOT|EXACT_FIVE_QUERY4S)_[A-Z0-9_]+', message):
        return message
    return diagnostic.safe_reason(error)


def contract():
    return {**prior.caps(), 'stage': 'VSDC_FIVE_FULL_QUERY_FOUR_SECOND_PILOT_V1',
        'output_base': OUTPUT, 'preparation': PREP, 'batch_ids': ['PILOT4S'],
        'pilot_tickers': list(TICKERS), 'selected_query_count': 5, 'estimated_list_requests': 11,
        'business_interval_seconds': 4, 'max_business_requests': 30, 'max_context_attempts': 490,
        'max_batch_business_requests': 20, 'max_batch_context_attempts': 98,
        'max_seconds': 600, 'max_batch_seconds': 180, 'max_query_seconds': 180,
        'agent_acquisition': False, 'recovery_import': False, 'automatic_promotion': False,
        'comparison': 'BOUNDED_4S_OBSERVATION_NOT_CONTROLLED_CAUSAL_2S_VS_4S_TEST'}


def runtime(project):
    names = [CONFIG, 'src/delta_t1/ingestion/corporate_actions/vsdc_five_query4s_pilot.py',
        'scripts/corporate_actions/prepare_vsdc_five_query4s_pilot_v1.py',
        'scripts/corporate_actions/collect_vsdc_five_query4s_pilot_v1.py']
    return {**diagnostic.runtime(project), **{name: sha((project / name).read_bytes()) for name in names}}


def parents(project):
    _, old = diagnostic.load_preparation(project)
    if (project / diagnostic.OUTPUT / 'active.lock').exists():
        raise ValueError('PILOT_DIAGNOSTIC_ACTIVE_LOCK_REVIEW_REQUIRED')
    if sorted(p.name for p in (project / diagnostic.OUTPUT).glob('run-*')) != [Path(DIAG_RUN).name]:
        raise ValueError('PILOT_EXACT_DIAGNOSTIC_RUN_REQUIRED')
    for name, (digest, kind) in PARENTS.items():
        folder = project / name
        if sha((folder / 'manifest.json').read_bytes()) != digest:
            raise ValueError('PILOT_PARENT_CHANGED')
        base.verify_artifact(folder, {kind})
    prior.verify_zip(project / DIAG_RUN / 'state', project / DIAG_RUN / 'delta-vsdc-app-diagnostic.zip', diagnostic.TYPE)
    if read(project / DIAG_REVIEW / 'review.json')['status'] != 'PASS_APP_FIRST_PAGE_DIAGNOSTIC_OFFLINE_REVIEW_NO_OLD_FAILURE_REPRODUCTION':
        raise ValueError('PILOT_REVIEWED_APP_DIAGNOSTIC_REQUIRED')
    order = prior.flatten(read(project / prior.PREP / 'selected_batches.json'))
    if [r['ticker'] for r in order[15:20]] != list(TICKERS):
        raise ValueError('PILOT_NEXT_FIVE_PENDING_QUERIES_REQUIRED')
    return old


def load_preparation(project):
    config = read(project / CONFIG)
    if config != contract(): raise ValueError('EXACT_FIVE_QUERY4S_CONTRACT_REQUIRED')
    parents(project); prep = project / PREP
    base.verify_artifact(prep, {PREP_TYPE})
    if read(prep / 'runtime.json') != runtime(project) or read(prep / 'plan.json')['config'] != config:
        raise ValueError('PILOT_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project, read(prep / 'protected_old_files.json'))
    if len(read(prep / 'known_discovery_provider_ids.json')) != 28453 or len(read(prep / 'reusable_detail_provider_ids.json')) != 27731:
        raise ValueError('PILOT_VALIDATED_CACHE_BASELINE_CHANGED')
    return config, prep


def prepare(project):
    project = Path(project).resolve()
    if read(project / CONFIG) != contract(): raise ValueError('EXACT_FIVE_QUERY4S_CONTRACT_REQUIRED')
    old = parents(project); output = project / PREP
    if output.exists(): raise FileExistsError('REFUSE_OVERWRITE')
    protected = read(old / 'protected_old_files.json')
    for name in PARENTS:
        folder = project / name
        for path in (folder / 'manifest.json', *[folder / n for n in read(folder / 'manifest.json')['files']]):
            protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    archive = project / DIAG_RUN / 'delta-vsdc-app-diagnostic.zip'
    protected[archive.relative_to(project).as_posix()] = sha(archive.read_bytes())
    protected.update(runtime(project)); output.mkdir(parents=True)
    (output / 'known_discovery_provider_ids.json').write_bytes((project / diagnostic.RUN / 'state/known_discovery_after_validated_queries.json').read_bytes())
    for name in ('reusable_detail_provider_ids.json', 'cache_policy.json'):
        (output / name).write_bytes((project / prior.PREP / name).read_bytes())
    write(output / 'protected_old_files.json', protected); write(output / 'runtime.json', runtime(project))
    write(output / 'plan.json', {'config': contract(), 'status': 'PREPARED_NOT_EXECUTED',
        'source_requests': 0, 'browser_launches': 0, 'readiness': mbs.old.readiness(contract()),
        'expected_archived_rows': EXPECTED_ROWS, 'estimated_list_requests': 11,
        'scope': 'Five next pending FULL queries;fresh headless process/context each;single worker.',
        'diagnostics': 'Safe response evidence before selector/DOM-change wait on EVERY page;no raw body/DOM/private state.',
        'cadence': 'Min4s between business request STARTS across pages and tickers,not extra sleep after response.',
        'prior_source_costs_audit_only': {'V3': {'business': 33, 'context': 828, 'active_seconds': 104.61000000000058},
            'APP_diagnostic': {'business': 1, 'context': 51, 'active_seconds': 2.75}},
        'completion': 'Pilot query checkpoints only;no import into V3,owner/canonical/PIT/identity/history.',
        'limits': 'Five queries/estimated11requests cannot establish2s as old cause or certify remaining1058queries.',
        'next_step': 'User runs once locally,returns ZIP for offline pacing/source/coverage review before recovery preparation.'})
    write(output / 'manifest.json', {'artifact_type': PREP_TYPE, 'files': hashes(output)})
    load_preparation(project)
    return {'status': 'PREPARED_NOT_EXECUTED', 'tickers': list(TICKERS), 'estimated_list_requests': 11,
        'business_interval_seconds': 4, 'protected_files': len(protected), 'source_requests': 0, 'output': str(output)}


class Guard(prior.Guard):
    def admit(self, url, method, resource, body=None, redirected=False):
        if url == self.config['url'] and self.shared.last is not None and self.clock() - self.shared.last < 4:
            self.fail('PILOT_FOUR_SECOND_INTERVAL_REQUIRED')
        return super().admit(url, method, resource, body, redirected)


class Driver(diagnostic.DiagnosticDriver):
    def __init__(self, config, guard):
        super().__init__(config, guard); self.number = 1; self.previous = None

    def next_page(self, number, previous):
        self.number, self.previous = number, previous
        selector = f'#divGlSearchArticles #d_number_of_page button[onclick="changePageArticles({number})"]'
        candidates = self.page.locator(selector)
        button = candidates.filter(has_text=re.compile(rf'^\s*{number}\s*$')); label = str(number)
        if button.count() == 0:
            button = candidates.filter(has_text=re.compile(r'^\s*>\s*$')); label = '>'
        if button.count() != 1: raise ValueError('UNIQUE_OBSERVED_SEQUENTIAL_PAGE_BUTTON_REQUIRED')
        self.guard.log({'event': 'UI_PAGE_BUTTON', 'target_page': number, 'visible_label': label,
            'source_onclick': f'changePageArticles({number})'})
        with self.page.expect_response(lambda r: r.url == self.config['url'] and r.request.method == 'POST',
                timeout=self.guard.timeout_ms()) as pending:
            button.click(timeout=self.guard.timeout_ms(), no_wait_after=True)
        return self._snapshot(pending.value, False)

    def _snapshot(self, response, include_scope):
        if response.url != self.config['url'] or self.page.url != self.config['url']:
            raise ValueError('PILOT_QUERY_URL_CHANGED')
        output = self.guard.output / 'diagnostics' / f'page{self.number}'
        output.mkdir(parents=True)
        write(output / 'response_receipt.json', {'url': self.config['url'], 'status': response.status,
            'page': self.number, 'captured_at': datetime.now(timezone.utc).isoformat(),
            'capture_before_DOM_wait': True, 'raw_body_or_DOM_archived': False})
        try: data = response.body()
        except Exception as exc:
            write(output / 'body_read_failure.json', {'error_type': type(exc).__name__})
            raise ValueError('PILOT_BODY_READ_FAILED') from None
        evidence = body_evidence(data, self.config['max_html_bytes']); write(output / 'body_evidence.json', evidence)
        if evidence['size_limit_exceeded'] or evidence['marker_labels']:
            raise ValueError('PILOT_BODY_SIZE_OR_ACCESS_MARKERS_STOP')
        self.guard.check()
        if response.status != 200: raise ValueError('PILOT_PAGE_HTTP200_REQUIRED')
        if (not self.guard.responses or (self.guard.responses[-1]['headers'].get('content-type') or '').split(';')[0].strip().casefold() != 'text/html'):
            raise ValueError('PILOT_HTML_CONTENT_TYPE_REQUIRED')
        def dom(name):
            scope = self.page.content(); summary = body_evidence(scope.encode('utf8'), self.config['max_html_bytes'])
            write(output / name, summary)
            if summary['size_limit_exceeded'] or summary['marker_labels']:
                raise ValueError('PILOT_DOM_SIZE_OR_ACCESS_MARKERS_STOP')
            return scope
        dom('DOM_evidence_before_wait.json')
        try:
            if self.previous is not None:
                self.page.wait_for_function("old => {const el=document.querySelector('#divGlSearchArticles'); return el && el.outerHTML !== old;}",
                    arg=self.previous, timeout=self.guard.timeout_ms())
            fragment = self.page.locator(mbs.old.CONTAINER).evaluate('(el) => el.outerHTML', timeout=self.guard.timeout_ms())
        except Exception as exc:
            write(output / 'selector_check.json', {'outcome': 'LOOKUP_OR_CHANGE_WAIT_FAILED', 'error_type': type(exc).__name__})
            raise ValueError('PILOT_DOM_WAIT_FAILED') from None
        write(output / 'selector_check.json', {'outcome': 'FOUND_UPDATED' if self.previous is not None else 'FOUND'})
        scope = dom('DOM_evidence_after_wait.json'); self.guard.check()
        return {'url': self.page.url, 'fragment': fragment, 'scope_html': scope,
            'http_body_sha256': evidence['sha256'], 'http_body_bytes': evidence['bytes'], 'http_status': response.status}


def verify_sealed_zip(folder, archive):
    prior.verify_zip(folder, archive, QUERY_TYPE)
    return base.verify_artifact(folder, {QUERY_TYPE})


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
        'detail_requests':0,'canonical_fields_applied':0,'browser_launches':0,'business_interval_seconds':4,'headless':True}
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
                    if shared.last is not None:driver.pace(max(0,4-(clock()-shared.last)))
                    current=driver.first();guard.check()
                    write(query/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,
                        'default_identity':True,'TLS_ignore_errors':False,'cookie_auth_exported':False,'headless':True})
                    write(query/'fresh_source_contract.json',source_contract(current['scope_html'],ticker))
                    seen=[];query_articles=[];total=None;previous=''
                    for number in range(1,21):
                        if number>1:
                            check_old();driver.pace(max(0,4-(clock()-shared.last)))
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


def _validate_source_query(folder,archive,definition,config,reusable,known,previous_start):
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
            or result['business_interval_seconds']!=4
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
    if any(not math.isfinite(s) for s in starts) or any(b-a<4 for a,b in zip(starts,starts[1:])):
        raise ValueError('PILOT_PACING_BELOW_FOUR_SECONDS')
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



def validate_query(folder, definition, reusable, known, previous_start):
    checked = _validate_source_query(folder / 'state', folder / 'query.zip', definition, contract(), reusable, known, previous_start)
    state = folder / 'state'; ticker = definition['tickers'][0]
    if read(state / 'result.json').get('headless') is not True or read(state / ticker / 'browser.json').get('headless') is not True:
        raise ValueError('PILOT_HEADLESS_RECEIPTS_REQUIRED')
    calls = read(state / ticker / 'business_requests.json')
    for number in range(1, len(calls) + 1):
        page = state / ticker / 'diagnostics' / f'page{number}'
        if {f.name for f in page.iterdir()} != {'response_receipt.json', 'body_evidence.json',
                'DOM_evidence_before_wait.json', 'DOM_evidence_after_wait.json', 'selector_check.json'}:
            raise ValueError('PILOT_SAFE_DIAGNOSTIC_FILE_SET_REQUIRED')
        receipt = read(page / 'response_receipt.json')
        source_receipt = read(state / ticker / f'page{number}_receipt.json')
        if (receipt['url'] != search_url(ticker) or receipt['status'] != 200 or receipt['page'] != number
                or not receipt['capture_before_DOM_wait'] or receipt['raw_body_or_DOM_archived']):
            raise ValueError('PILOT_RESPONSE_DIAGNOSTIC_RECEIPT_MISMATCH')
        for name in ('body_evidence.json', 'DOM_evidence_before_wait.json', 'DOM_evidence_after_wait.json'):
            summary = read(page / name)
            if (set(summary) != {'bytes', 'sha256', 'size_limit_exceeded', 'structure', 'marker_labels', 'raw_archived'}
                    or summary['size_limit_exceeded'] is not False or summary['marker_labels'] != [] or summary['raw_archived'] is not False
                    or not 0 < summary['bytes'] <= 2000000 or not re.fullmatch('[0-9a-f]{64}', summary['sha256'])):
                raise ValueError('PILOT_SAFE_DIAGNOSTIC_FIELDS_REQUIRED')
            structure = summary['structure']
            if (set(structure) != {'article_containers', 'scripts', 'forms', 'password_inputs'}
                    or any(type(v) is not int or v < 0 for v in structure.values()) or structure['password_inputs']
                    or name != 'body_evidence.json' and structure['article_containers'] != 1):
                raise ValueError('PILOT_SAFE_DIAGNOSTIC_STRUCTURE_REQUIRED')
            if name == 'body_evidence.json' and (summary['sha256'] != source_receipt['http_body_hash_not_archived'] or summary['bytes'] != source_receipt['http_body_bytes']):
                raise ValueError('PILOT_BODY_RECEIPT_BINDING_MISMATCH')
        if read(page / 'selector_check.json') != {'outcome': 'FOUND' if number == 1 else 'FOUND_UPDATED'}:
            raise ValueError('PILOT_DOM_WAIT_CHECK_MISMATCH')
    return checked


def single_run_gate(project):
    root = Path(project) / OUTPUT
    if root.exists() and any(root.glob('run-*')): raise ValueError('PILOT_ALREADY_RUN_REVIEW_REQUIRED_NO_RETRY')


class Progress:
    def __init__(self, output, emit): self.output, self.emit, self.count = output, emit, 0
    def record(self, event, ticker=None, page=None, pages=None, status=None):
        row = {'event': event, 'completed_queries': self.count, 'total_queries': 5,
            'ticker': ticker, 'page': page, 'total_pages': pages, 'status': status}
        line = f'[{self.count}/5 mã] {event}' + (f' {ticker}' if ticker else '') + (f' | Trang {page}/{pages}' if page else '')
        if status: line += ' | ' + status
        with (self.output / 'progress.jsonl').open('a', encoding='utf8') as f: f.write(json.dumps(row, ensure_ascii=False) + '\n')
        with (self.output / 'progress.log').open('a', encoding='utf8') as f: f.write(line + '\n')
        self.emit(line, flush=True)
    def page_complete(self, number, pages): self.record('PAGE_COMPLETE', self.active, number, pages)


def run(project, output, *, dry_run=False, driver_factory=Driver, clock=time.monotonic, emit=print):
    project, output = Path(project).resolve(), Path(output).resolve(); config, prep = load_preparation(project)
    single_run_gate(project)
    if output.exists(): raise FileExistsError('REFUSE_OVERWRITE')
    ready = mbs.old.readiness(config)
    if dry_run: return {'status': 'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED',
        'tickers': list(TICKERS), 'business_interval_seconds': 4, 'estimated_list_requests': 11,
        'source_requests': 0, 'browser_launched': False, 'headless': True, 'readiness': ready}
    if not ready['ready']: raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
    output.mkdir(parents=True); write(output / 'plan.json', config); write(output / 'runtime.json', runtime(project))
    write(output / 'inputs.json', {'preparation_manifest_sha256': sha((prep / 'manifest.json').read_bytes())})
    known = set(read(prep / 'known_discovery_provider_ids.json')); initial = set(known)
    reusable = set(read(prep / 'reusable_detail_provider_ids.json'))
    protected = read(prep / 'protected_old_files.json'); check = lambda: mbs.old.protected_check(project, protected)
    shared = base.Budget(config, clock); completed = []; reporter = Progress(output, emit); reporter.record('START')
    result = {'status': STOP, 'resumable': False, 'business_interval_seconds': 4, 'headless': True,
        'detail_requests': 0, 'canonical_fields_applied': 0, 'owner_choices_changed': False,
        'pit_or_identity_promoted': False, 'full_history_certified': False, 'openai_api_calls': 0,
        'recovery_imported': False, 'browser_launches': 0, 'manual_offline_review_pending': True}
    try:
        check()
        for i, ticker in enumerate(TICKERS):
            shared.begin('PILOT4S'); reporter.active = ticker; reporter.record('QUERY_START', ticker)
            folder = output / 'queries' / f'{i+1:04d}'; folder.mkdir(parents=True)
            definition = {'batch_id': 'PILOT4S', 'tickers': [ticker], 'estimated_list_requests': math.ceil(EXPECTED_ROWS[ticker] / 20)}
            previous_start = shared.previous_start
            write(folder / 'context.json', {'definition': definition, 'previous_start': previous_start, 'runtime': runtime(project)})
            acquired = acquire_query(project, folder / 'state', definition, config, prep, shared,
                reusable, known, check, driver_factory, clock, progress=reporter)
            result['browser_launches'] += acquired['browser_launches']
            check(); base.seal(folder / 'state', folder / 'query.zip', artifact_type=QUERY_TYPE)
            if acquired['status'] != 'PASS_SOURCE_BATCH_REQUIRES_AUTOMATED_VALIDATION':
                raise ValueError('PILOT_QUERY_STOP_REVIEW_REQUIRED')
            validated = validate_query(folder, definition, reusable, known, previous_start)
            if read(folder / 'state/runtime.json') != runtime(project): raise ValueError('PILOT_QUERY_RUNTIME_CHANGED')
            write(folder / 'validation.json', validated); shared.end(); check()
            known.update(a['provider_article_id'] for a in read(folder / 'state/deduplicated_query_articles.json'))
            completed.append(ticker); reporter.count = len(completed); reporter.record('QUERY_VALIDATED', ticker)
        check(); shared.check(); result['status'] = PASS
    except KeyboardInterrupt: result.update(stop_reason='USER_INTERRUPT_NO_RESUME')
    except Exception as exc: result.update(stop_reason=safe_reason(exc), error_type=type(exc).__name__)
    finally:
        try: check(); shared.check()
        except Exception as exc: result.update(status=STOP, stop_reason=safe_reason(exc))
        result.update(completed_tickers=completed, completed_query_count=len(completed), remaining_pilot_queries=5-len(completed),
            business_requests=shared.business, context_attempts=shared.attempts, active_seconds=clock()-shared.started,
            known_list_IDs_before=len(initial), known_list_IDs_after=len(known), first_discovered_list_IDs=len(known-initial),
            reusable_detail_IDs_unchanged=len(reusable))
        write(output / 'known_discovery_after_validated_queries.json', sorted(known))
        reporter.record('FINAL', status=result['status']); write(output / 'result.json', result)
    return result


def package(state):
    archive = state.parent / 'delta-vsdc-five-query4s.zip'
    base.seal(state, archive, artifact_type=TYPE); prior.verify_zip(state, archive, TYPE)
    return archive
