"""V6 Windows isolated-worker pause;import616complete,PLC page1restart,ORS HOLD."""
from pathlib import Path
from bisect import bisect_right
from collections import deque
from datetime import datetime, timezone
import json
import math
import re
import shutil
import time

from . import vsdc_recovery_ors_hold as old
from . import vsdc_local_supervisor as supervisor

base, mbs, pilot, prior = old.base, old.mbs, old.pilot, old.prior
read, write, sha, hashes = old.read, old.write, old.sha, old.hashes
Pause, execution_lock = old.Pause, old.execution_lock
flatten, query_definition, query_folder = old.flatten, old.query_definition, old.query_folder
initial_totals, check_totals, ledger_cost = old.initial_totals, old.check_totals, old.ledger_cost
verify_zip, ProgressDriver, Progress = old.verify_zip, old.ProgressDriver, old.Progress
Guard = old.Guard
source_contract, list_page, search_url = old.source_contract, old.list_page, old.search_url
ids_hash, deduplicate = old.ids_hash, old.deduplicate
scope_summary, validate_hold_copies, progress_line = old.scope_summary, old.validate_hold_copies, old.progress_line
CONFIG = 'configs/data/corporate_actions/vsdc_recovery_pausefix_v6.json'
OUTPUT = 'data/corporate_actions/work/vsdc_recovery_pausefix_v6'
PREP = 'data/corporate_actions/work/vsdc_recovery_pausefix_preparation_20261103_v6'
TYPE = 'vsdc-reviewed616-Windows-isolated-pause-recovery-v6'
PREP_TYPE = 'vsdc-reviewed616-Windows-isolated-pause-preparation-v6'
PAUSED, STOPPED, COMPLETE = old.PAUSED, old.STOPPED, old.COMPLETE
SNAPSHOT = 'data/corporate_actions/work/vsdc_v5_closed_snapshot_20261103_v1'
SNAPSHOT_DIGEST = '872ed0a25ebbfe6062c6af959b73aad662b3e46c5f911931a3bcc834a6507770'
WORKER = 'scripts/corporate_actions/run_vsdc_recovery_pausefix_worker_v6.py'


def stage(label, done=None, total=None):
    suffix = f': {done}/{total}' if done is not None else ''
    print('[Chuẩn bị] '+label+suffix, flush=True)


def caps():
    return {**old.caps(), 'stage': 'VSDC_WINDOWS_PAUSEFIX_QUERY_V6', 'output_base': OUTPUT, 'preparation': PREP}


def contract():
    return {**old.contract(), 'stage': 'VSDC_REVIEWED616_WINDOWS_PAUSEFIX_V6',
        'output_base': OUTPUT, 'preparation': PREP, 'scope_and_source_caps': caps(),
        'reviewed_import_count': 616, 'remaining_queries_before_first_run': 456,
        'remaining_batches_before_first_run': 24, 'recovery_import': 'ONLY_REVIEWED_CLOSED_V5_616_PREFIX',
        'Windows_pause': 'SUPERVISOR_SIGINT_TO_MARKER;WORKER_NEW_PROCESS_GROUP_AND_NO_CONSOLE',
        'browser_handle_sigint': False, 'startup_progress': 'VISIBLE_PREFLIGHT_AND_COPY_COUNTS',
        'cost_accounting': 'CONSERVATIVE_INCLUDE_DRIVER_UNRESPONSIVE_TIME_UNTIL_PROCESS_CLOSED',
        'preparation_import_storage': 'PINNED_SOURCE_REFERENCES;EXACT_COPIES_AT_USER_RUN'}


def runtime(project):
    names = [CONFIG, 'src/delta_t1/ingestion/corporate_actions/vsdc_recovery_pausefix.py',
        'src/delta_t1/ingestion/corporate_actions/vsdc_local_supervisor.py',
        'scripts/corporate_actions/prepare_vsdc_recovery_pausefix_v6.py',
        'scripts/corporate_actions/collect_vsdc_recovery_pausefix_v6.py', WORKER]
    return {**old.runtime(project), **{n: sha((project / n).read_bytes()) for n in names}}


def verify_files(folder, kind, label):
    folder = Path(folder).resolve(); manifest = read(folder / 'manifest.json')
    if manifest.get('artifact_type') != kind: raise ValueError('UNSUPPORTED_BATCH_INPUT_ARTIFACT')
    total = len(manifest['files']); stage(label, 0, total)
    for i, (name, digest) in enumerate(manifest['files'].items()):
        target = (folder / name).resolve()
        if not target.is_relative_to(folder) or sha(target.read_bytes()) != digest:
            raise ValueError('BATCH_INPUT_CHECKSUM_MISMATCH')
        if (i+1) % 500 == 0 or i+1 == total: stage(label, i+1, total)
    return manifest


def parents(project):
    if (project / old.OUTPUT / 'active.lock').exists(): raise ValueError('RECOVERY_V5_SESSION_NOT_CLOSED')
    stage('Kiểm tra snapshot phiên V5 đã khép')
    snapshot = project / SNAPSHOT
    if sha((snapshot / 'manifest.json').read_bytes()) != SNAPSHOT_DIGEST: raise ValueError('RECOVERY_CLOSED_SNAPSHOT_CHANGED')
    base.verify_artifact(snapshot, {'vsdc-v5-externally-closed-crash-snapshot-v1'})
    closure = read(snapshot / 'closure.json')
    if closure['status'] != 'CRASH_CLOSED_REVIEWED_NOT_USER_PAUSED' or len(closure['completed']) != 616:
        raise ValueError('RECOVERY_REVIEWED616_CLOSED_REQUIRED')
    state = project / closure['source_state']; stage('Kiểm tra raw files đã freeze', 0, len(closure['source_files']))
    for i, (name, digest) in enumerate(closure['source_files'].items()):
        target = (state / name).resolve()
        if not target.is_relative_to(state.resolve()) or sha(target.read_bytes()) != digest:
            raise ValueError('RECOVERY_CLOSED_RAW_CHANGED')
        if (i+1) % 1000 == 0 or i+1 == len(closure['source_files']): stage('Kiểm tra raw files đã freeze', i+1, len(closure['source_files']))
    if read(state / 'runtime.json') != old.runtime(project): raise ValueError('RECOVERY_OLD_RUNTIME_CHANGED')
    mbs.old.protected_check(project, read(project / old.PREP / 'protected_old_files.json'))
    return closure


def spec_from_closure(project, closure):
    previous = project / old.PREP; selected = read(previous / 'selected_batches.json'); order = flatten(selected)
    if closure['completed'] != order[:616] or order[616]['ticker'] != 'PLC': raise ValueError('RECOVERY_PLC_PREFIX_SCOPE_CHANGED')
    sources = []
    for i, row in enumerate(order[:616]):
        prefix = f'queries/{i+1:04d}/'
        files = {n[len(prefix):]: d for n, d in closure['source_files'].items() if n.startswith(prefix)}
        if not files: raise ValueError('RECOVERY_IMPORTED_EVIDENCE_MISSING')
        sources.append({'scope': row, 'path': (Path(closure['source_state']) / prefix).as_posix(),
            'original_interval_seconds': 2 if i < 15 else 4, 'files': files})
    check_totals(closure['totals'])
    return {'completed': order[:616], 'sources': sources, 'totals': closure['totals'],
        'known': closure['known'], 'durations': [], 'held': closure['ORS_HOLD'],
        'original_selected': read(previous / 'original_selected_batches.json'), 'scoped_selected': selected,
        'cost_provenance': closure['time_accounting'], 'interrupted_PLC': closure['partial_attempt']}


def load_preparation(project):
    stage('Bắt đầu kiểm tra offline; chưa gọi VSDC')
    config = read(project / CONFIG)
    if config != contract(): raise ValueError('EXACT_RECOVERY_PAUSEFIX_V6_CONTRACT_REQUIRED')
    closure = parents(project); prep = project / PREP
    verify_files(prep, PREP_TYPE, 'Kiểm tra gói V6')
    if read(prep / 'runtime.json') != runtime(project) or read(prep / 'plan.json')['config'] != config:
        raise ValueError('RECOVERY_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project, read(prep / 'protected_old_files.json'))
    spec = spec_from_closure(project, closure)
    if read(prep / 'seed.json') != spec: raise ValueError('RECOVERY_SEED_CHANGED')
    for name, expected in [('selected_batches.json', spec['scoped_selected']),
            ('original_selected_batches.json', spec['original_selected']), ('held_query.json', spec['held']),
            ('known_discovery_provider_ids.json', spec['known'])]:
        if read(prep / name) != expected: raise ValueError('RECOVERY_SCOPE_CACHE_OR_HOLD_CHANGED')
    if hashes(prep / 'holds/ORS') != spec['held']['evidence_files']: raise ValueError('RECOVERY_HOLD_COPY_CHANGED')
    stage('Preflight đạt; đã giữ616 mã, PLC sẽ thu lại từ trang1')
    return config, prep


def prepare(project):
    project = Path(project).resolve()
    if read(project / CONFIG) != contract(): raise ValueError('EXACT_RECOVERY_PAUSEFIX_V6_CONTRACT_REQUIRED')
    closure = parents(project); output = project / PREP
    if output.exists(): raise FileExistsError('REFUSE_OVERWRITE')
    spec = spec_from_closure(project, closure); protected = read(project / old.PREP / 'protected_old_files.json')
    for name in ['manifest.json', *read(project / SNAPSHOT / 'manifest.json')['files']]:
        path = project / SNAPSHOT / name; protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    protected.update(runtime(project)); output.mkdir(parents=True)
    for name in ('reusable_detail_provider_ids.json', 'cache_policy.json', 'query_inventory_before_chain.json'):
        (output / name).write_bytes((project / old.PREP / name).read_bytes())
    write(output / 'seed.json', spec); write(output / 'selected_batches.json', spec['scoped_selected'])
    write(output / 'original_selected_batches.json', spec['original_selected']); write(output / 'held_query.json', spec['held'])
    write(output / 'known_discovery_provider_ids.json', spec['known'])
    shutil.copytree(project / closure['source_state'] / 'holds', output / 'holds')
    shutil.copytree(project / closure['source_state'] / 'queries/0617', output / 'interrupted/PLC-V5')
    write(output / 'runtime.json', runtime(project)); write(output / 'protected_old_files.json', protected)
    write(output / 'plan.json', {'status': 'PREPARED_NOT_EXECUTED', 'config': contract(), 'imported_queries': 616,
        'remaining_queries': 456, 'held_queries': 1, 'remaining_batches': 24, 'source_requests': 0,
        'readiness': mbs.old.readiness(caps()), 'costs_carried': spec['totals'],
        'progress': 'Visible raw/preparation/copy counters;616source refs copied once at user run.',
        'pause': 'Console supervisor handles Ctrl+C;worker hidden/newprocessgroup/no_console;marker only;browserhandle_sigintFalse.',
        'limits': 'No automatic kill/retry/crash resume;conservative old unresponsive time charged;perbatch caps unchanged.',
        'next_step': 'User local supervised V6 run then offline ZIPreview;ORS HOLD remains.'})
    write(output / 'manifest.json', {'artifact_type': PREP_TYPE, 'files': hashes(output)})
    base.verify_artifact(output, {PREP_TYPE})
    return {'status': 'PREPARED_NOT_EXECUTED', 'imported_queries': 616, 'remaining_queries': 456,
        'held_queries': 1, 'protected_files': len(protected), 'source_requests': 0}


def seed_query_source(project, prep, seed, index):
    return Path(project) / seed['sources'][index]['path']


class HeadlessDriver(old.HeadlessDriver):
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        try:
            self.manager=sync_playwright().start()
            self.browser=self.manager.chromium.launch(channel='chrome',headless=True,handle_sigint=False,timeout=self.guard.timeout_ms())
            self.browser.on('disconnected',self._disconnected)
            self.context=self.browser.new_context(ignore_https_errors=False,accept_downloads=False,service_workers='block')
            self.context.route('**/*',self._route);self.context.on('response',self._response)
            self.context.on('requestfailed',self._failed);self.context.route_web_socket('**/*',self._websocket)
            self.page=self.context.new_page();self.context.on('page',self._popup);self.page.on('dialog',self._dialog)
            self.version=self.browser.version;return self
        except BaseException:self.__exit__(None,None,None);raise


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


def _validate_four_second_query(folder, definition, reusable, known, previous_start):
    checked = pilot._validate_source_query(folder / 'state', folder / 'query.zip', definition, caps(), reusable, known, previous_start)
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


def validate_batch(folder, archive, definition, config, reusable, known, previous_start):
    if config != caps(): raise ValueError('EXACT_RECOVERY_QUERY_CAPS_REQUIRED')
    return _validate_four_second_query(folder.parent, definition, reusable, known, previous_start)


def validate_query(folder, row, known, reusable, project):
    context = read(folder / 'context.json')
    if context != {'scope': row, 'previous_start': context['previous_start'], 'headless_query_runtime': runtime(project)}:
        raise ValueError('RECOVERY_QUERY_SCOPE_RUNTIME_CHANGED')
    checked = validate_batch(folder / 'state', folder / 'query.zip', query_definition(row), caps(), reusable, known, context['previous_start'])
    if read(folder / 'state/runtime.json') != runtime(project): raise ValueError('RECOVERY_QUERY_RUNTIME_CHANGED')
    if checked != read(folder / 'validation.json'): raise ValueError('RECOVERY_QUERY_VALIDATION_CHANGED')
    return read(folder / 'state/deduplicated_query_articles.json')


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
    archive = state.parent / 'delta-vsdc-recovery-pausefix.zip'
    base.seal(state, archive, artifact_type=TYPE); verify_zip(state, archive, TYPE)
    return archive


def history(project,config,prep):
    """Only the complete sealed PAUSED prefix is eligible, never a source-error or crash run."""
    root=project/config['output_base'];runs=sorted(root.glob('run-*')) if root.exists() else []
    if len(runs)>=config['max_segments']:raise ValueError('SEGMENT_COUNT_CAP_REVIEW_REQUIRED')
    selected=read(prep/'selected_batches.json');order=flatten(selected)
    known=set(read(prep/'known_discovery_provider_ids.json'));reusable=set(read(prep/'reusable_detail_provider_ids.json'))
    seed=read(prep/'seed.json');totals=json.loads(json.dumps(seed['totals']));count=len(seed['completed']);previous=None;durations=list(seed['durations'])
    prefix_hashes={i:seed['sources'][i]['files'] for i in range(count)}
    for run in runs:
        if not run.is_dir() or run.is_symlink():raise ValueError('UNEXPECTED_RUN_PATH')
        state=run/'state';verify_zip(state,run/'delta-vsdc-recovery-pausefix.zip',TYPE)
        if read(state/'runtime.json')!=runtime(project) or read(state/'plan.json')!=config:
            raise ValueError('SEGMENT_RUNTIME_OR_CONFIG_CHANGED')
        inputs=read(state/'inputs.json')
        if inputs!={'preparation_manifest_sha256':sha((prep/'manifest.json').read_bytes()),'predecessor':previous,
                    'completed_before_segment':count}:
            raise ValueError('SEGMENT_LINEAGE_OR_PREFIX_CHANGED')
        result=read(state/'result.json');validate_hold_copies(state,prep)
        if result['status']!=PAUSED or not result['resumable']:raise ValueError('ONLY_USER_PAUSED_RUN_CAN_CONTINUE: '+result['status'])
        completed=read(state/'completed_queries.json')
        if any(result.get(k)!=v for k,v in scope_summary(prep,completed).items()):raise ValueError('RECOVERY_HOLD_COUNTS_OR_ORIGINAL_SCOPE_CHANGED')
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
    prior=history(project,config,prep);source_seed=read(prep/'seed.json');selected=read(prep/'selected_batches.json');order=flatten(selected)
    ready=base.mbs.old.readiness(caps())
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED','source_requests':0,
        'browser_launched':False,'completed_queries':len(prior['completed']),'remaining_queries':len(order)-len(prior['completed']),
        'selected_batches':len(selected),'remaining_batches':sum(not all(r in prior['completed'] for r in flatten([b])) for b in selected),'headless':True,'interval_seconds':4,'readiness':ready,**scope_summary(prep,prior['completed'])}
    if not ready['ready']:raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
    if len(prior['completed'])==len(order):raise ValueError('ALL_SELECTED_QUERIES_ALREADY_COMPLETE')
    output.mkdir(parents=True);pause=pause or Pause(output.parent/'PAUSE_REQUEST')
    for name in ('selected_batches.json','reusable_detail_provider_ids.json','known_discovery_provider_ids.json',
                 'cache_policy.json','query_inventory_before_chain.json','protected_old_files.json'):
        (output/name).write_bytes((prep/name).read_bytes())
    for name in ('held_query.json','original_selected_batches.json'):(output/name).write_bytes((prep/name).read_bytes())
    shutil.copytree(prep/'holds',output/'holds');validate_hold_copies(output,prep)
    if (prep/'interrupted').exists():shutil.copytree(prep/'interrupted',output/'interrupted')
    write(output/'plan.json',config);write(output/'runtime.json',runtime(project));write(output/'environment.json',ready)
    write(output/'inputs.json',{'preparation_manifest_sha256':sha((prep/'manifest.json').read_bytes()),
        'predecessor':prior['predecessor'],'completed_before_segment':len(prior['completed'])})
    completed=list(prior['completed']);known=set(prior['known']);totals=prior['totals'];attempts=[]
    if prior['completed']:
        old=prior['runs'][-1]/'state' if prior['runs'] else prep
        stage('Sao chép checkpoint',0,len(completed))
        for i in range(len(completed)):
            source=query_folder(old,i) if prior['runs'] else seed_query_source(project,prep,source_seed,i)
            shutil.copytree(source,query_folder(output,i))
            if hashes(query_folder(output,i))!=prior['prefix_hashes'][i]:raise ValueError('COPIED_PREFIX_CHANGED_BEFORE_ACQUISITION')
            if (i+1)%10==0 or i+1==len(completed):stage('Sao chép checkpoint',i+1,len(completed))
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
                check();base.seal(folder/'state',folder/'query.zip',artifact_type=pilot.QUERY_TYPE)
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
    except Exception as exc:result.update(status=STOPPED,resumable=False,stop_reason=pilot.safe_reason(exc))
    finally:
        totals['active_seconds']=old_active+clock()-started
        try:
            check()
            if result['status']==PAUSED:check_totals(totals)
        except Exception as exc:result.update(status=STOPPED,resumable=False,stop_reason=pilot.safe_reason(exc))
        done={b['batch_id'] for b in selected if all({'batch_id':b['batch_id'],'ticker':t} in completed for t in b['tickers'])}
        result.update(completed_query_count=len(completed),remaining_query_count=len(order)-len(completed),
            validated_batch_ids=[b['batch_id'] for b in selected if b['batch_id'] in done],totals=totals,
            active_query=active,reusable_detail_IDs_unchanged=len(prior['reusable']),known_list_IDs=len(known))
        write(output/'completed_queries.json',completed);write(output/'new_attempts.json',attempts)
        write(output/'known_discovery_after_validated_queries.json',sorted(known))
        result.update(scope_summary(prep,completed))
        try:validate_hold_copies(output,prep)
        except Exception as exc:result.update(status=STOPPED,resumable=False,stop_reason=pilot.safe_reason(exc))
        reporter.finish(result['status'])
        totals['active_seconds']=old_active+clock()-started
        write(output/'result.json',result);checkpoint('FINAL_SEGMENT')
    return result

