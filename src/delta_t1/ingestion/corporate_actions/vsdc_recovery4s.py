"""Recovery V4: import20reviewed queries, min4s, immutable verified user-pause segments."""
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import re
import shutil
import time

from . import vsdc_headless_chain as old
from . import vsdc_five_query4s_pilot as pilot

base, mbs, prior = old.base, old.mbs, old.prior
read, write, sha, hashes = old.read, old.write, old.sha, old.hashes
Pause, pause_signals, execution_lock = old.Pause, old.pause_signals, old.execution_lock
flatten, query_definition, query_folder = old.flatten, old.query_definition, old.query_folder
initial_totals, check_totals, ledger_cost = old.initial_totals, old.check_totals, old.ledger_cost
verify_zip, validate_progress = old.verify_zip, old.validate_progress
Progress, ProgressDriver = old.Progress, old.ProgressDriver
Guard, HeadlessDriver = pilot.Guard, pilot.Driver
source_contract, list_page, search_url = old.source_contract, old.list_page, old.search_url
ids_hash, deduplicate = old.ids_hash, old.deduplicate
CONFIG = 'configs/data/corporate_actions/vsdc_recovery4s_v4.json'
OUTPUT = 'data/corporate_actions/work/vsdc_recovery4s_v4'
PREP = 'data/corporate_actions/work/vsdc_recovery4s_preparation_20261103_v4'
TYPE = 'vsdc-reviewed-prefix20-recovery4s-pause-segment-v4'
PREP_TYPE = 'vsdc-reviewed-prefix20-recovery4s-preparation-v4'
PAUSED, STOPPED = old.PAUSED, old.STOPPED
COMPLETE = 'PASS_RECOVERY_QUERY_CHECKPOINTS_REVIEW_REQUIRED'
PILOT_RUN = pilot.OUTPUT + '/run-20261103T111211552864Z'
PILOT_REVIEW = 'data/corporate_actions/work/vsdc_five_query4s_live_review_20261103_v1'
PARENTS = {
    pilot.PREP: ('a9f521d6e8df174e512470595fcddaf83a9ede9e94b774528882d9c319800ca8', pilot.PREP_TYPE),
    PILOT_RUN + '/state': ('cc55fb879ac78365ff635072d09d5458bdb1c593aa010f8717fe701cd40658c4', pilot.TYPE),
    PILOT_REVIEW: ('f2beadcaeac9e407376b169407d25f0dc09d414402969f620b6127e868af4ee8',
                   'vsdc-five-full-query-four-second-offline-live-review-v1'),
    'data/corporate_actions/work/vsdc_five_query4s_validation_20261103_v1':
        ('27fad2306728636e698f5acbe02bc72ba97f989e22c7ccea25902e2451956273',
         'vsdc-five-query-four-second-preparation-validation-v1'),
}


def caps():
    return {**old.caps(), 'stage': 'VSDC_RECOVERY4S_QUERY_V4', 'output_base': OUTPUT,
        'preparation': PREP, 'business_interval_seconds': 4}


def contract():
    return {**old.contract(), 'stage': 'VSDC_RECOVERY4S_REVIEWED20_PREPARATION_V4',
        'output_base': OUTPUT, 'preparation': PREP, 'scope_and_source_caps': caps(),
        'reviewed_import_count': 20, 'remaining_queries_before_first_run': 1053,
        'remaining_batches_before_first_run': 53, 'recovery_import': 'ONLY_PINNED_REVIEWED15V3_PLUS5PILOT',
        'inherited_prefix_cadence': 'ORIGINAL15_AT2S_PLUS5_AT4S_NEVER_RELABEL',
        'prior_costs': 'INCLUDE_V3_FAILED_APP_AND_APP_DIAGNOSTIC_AND4S_PILOT',
        'ETA_initial_samples': 'NONE_WARMUP5_NEW_RECOVERY_QUERIES'}


def runtime(project):
    names = [CONFIG, 'src/delta_t1/ingestion/corporate_actions/vsdc_recovery4s.py',
        'scripts/corporate_actions/prepare_vsdc_recovery4s_v4.py',
        'scripts/corporate_actions/collect_vsdc_recovery4s_v4.py']
    return {**pilot.runtime(project), **{n: sha((project / n).read_bytes()) for n in names}}


def parents(project):
    _, prepared = pilot.load_preparation(project)
    if (project / pilot.OUTPUT / 'active.lock').exists(): raise ValueError('RECOVERY_PILOT_ACTIVE_LOCK')
    if sorted(p.name for p in (project / pilot.OUTPUT).glob('run-*')) != [Path(PILOT_RUN).name]:
        raise ValueError('RECOVERY_EXACT_REVIEWED_PILOT_REQUIRED')
    for name, (digest, kind) in PARENTS.items():
        folder = project / name
        if sha((folder / 'manifest.json').read_bytes()) != digest: raise ValueError('RECOVERY_PARENT_CHANGED')
        base.verify_artifact(folder, {kind})
    verify_zip(project / PILOT_RUN / 'state', project / PILOT_RUN / 'delta-vsdc-five-query4s.zip', pilot.TYPE)
    review = read(project / PILOT_REVIEW / 'review.json')
    if (review['status'] != 'PASS_BOUNDED_FIVE_QUERY4S_FULL_LISTS_PACING_AND_SAFE_DIAGNOSTICS'
            or review['remaining_original_selected_queries'] != 1053):
        raise ValueError('RECOVERY_REVIEWED4S_PASS_REQUIRED')
    return prepared


def import_spec(project):
    original = project / old.PREP
    selected = read(original / 'selected_batches.json'); order = flatten(selected)
    v3 = project / pilot.diagnostic.RUN / 'state'; p4 = project / PILOT_RUN / 'state'
    if read(v3 / 'completed_queries.json') != order[:15] or [r['ticker'] for r in order[15:20]] != list(pilot.TICKERS):
        raise ValueError('RECOVERY_IMPORT_PREFIX_SCOPE_CHANGED')
    if read(v3 / 'result.json')['status'] != old.STOPPED or read(p4 / 'result.json')['status'] != pilot.PASS:
        raise ValueError('RECOVERY_IMPORT_SOURCE_STATUS_CHANGED')
    known = set(read(original / 'known_discovery_provider_ids.json'))
    reusable = set(read(original / 'reusable_detail_provider_ids.json')); sources = []
    for i, row in enumerate(order[:20]):
        folder = query_folder(v3, i) if i < 15 else query_folder(p4, i-15)
        if i < 15:
            articles = old.validate_query(folder, row, known, reusable, project)
        else:
            context = read(folder / 'context.json')
            if context['runtime'] != pilot.runtime(project) or context['definition']['tickers'] != [row['ticker']]:
                raise ValueError('RECOVERY_PILOT_QUERY_SCOPE_RUNTIME_CHANGED')
            checked = pilot.validate_query(folder, context['definition'], reusable, known, context['previous_start'])
            if checked != read(folder / 'validation.json'): raise ValueError('RECOVERY_PILOT_VALIDATION_CHANGED')
            articles = read(folder / 'state/deduplicated_query_articles.json')
        known.update(a['provider_article_id'] for a in articles)
        sources.append({'scope': row, 'path': folder.relative_to(project).as_posix(),
            'original_interval_seconds': 2 if i < 15 else 4, 'files': hashes(folder)})
    if len(known) != 28501 or len(reusable) != 27731: raise ValueError('RECOVERY_IMPORTED_CACHE_MISMATCH')
    costs = []
    for name, state in [('V3_INCLUDING_FAILED_APP', v3),
            ('APP_DIAGNOSTIC', project / pilot.DIAG_RUN / 'state'), ('PILOT4S', p4)]:
        result = read(state / 'result.json')
        costs.append({'source': name, 'manifest_sha256': sha((state / 'manifest.json').read_bytes()),
            'business': result.get('source_requests_this_segment', result.get('business_requests')),
            'context': result.get('context_attempts', result.get('totals', {}).get('context')),
            'active_seconds': result.get('active_seconds', result.get('totals', {}).get('active_seconds'))})
    totals = initial_totals(selected)
    totals.update(business=sum(c['business'] for c in costs), context=sum(c['context'] for c in costs),
        active_seconds=sum(c['active_seconds'] for c in costs))
    if totals['business'] != 45 or totals['context'] != 1155 or abs(totals['active_seconds']-159.719) > 1e-6:
        raise ValueError('RECOVERY_REVIEWED_COSTS_CHANGED')
    # All reviewed requests belong to the original first batch. Charge ALL active
    # overhead/diagnostic time conservatively to this completed batch as well.
    totals['batches'][selected[0]['batch_id']] = {k: totals[k] for k in ('business', 'context', 'active_seconds')}
    check_totals(totals)
    return {'completed': order[:20], 'sources': sources, 'totals': totals, 'cost_provenance': costs,
        'known': sorted(known), 'durations': []}


def load_preparation(project):
    config = read(project / CONFIG)
    if config != contract(): raise ValueError('EXACT_RECOVERY4S_V4_CONTRACT_REQUIRED')
    parents(project); prep = project / PREP; base.verify_artifact(prep, {PREP_TYPE})
    if read(prep / 'runtime.json') != runtime(project) or read(prep / 'plan.json')['config'] != config:
        raise ValueError('RECOVERY_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project, read(prep / 'protected_old_files.json'))
    spec = import_spec(project)
    if read(prep / 'seed.json') != spec: raise ValueError('RECOVERY_SEED_CHANGED')
    if read(prep / 'known_discovery_provider_ids.json') != spec['known']: raise ValueError('RECOVERY_SEED_KNOWN_CHANGED')
    for i, source in enumerate(spec['sources']):
        if hashes(query_folder(prep, i)) != source['files']: raise ValueError('RECOVERY_IMPORTED_COPY_CHANGED')
    if read(prep / 'selected_batches.json') != read(project / old.PREP / 'selected_batches.json'):
        raise ValueError('RECOVERY_ORIGINAL_SELECTION_CHANGED')
    return config, prep


def prepare(project):
    project = Path(project).resolve()
    if read(project / CONFIG) != contract(): raise ValueError('EXACT_RECOVERY4S_V4_CONTRACT_REQUIRED')
    previous = parents(project); output = project / PREP
    if output.exists(): raise FileExistsError('REFUSE_OVERWRITE')
    spec = import_spec(project); protected = read(previous / 'protected_old_files.json')
    for name in PARENTS:
        folder = project / name
        for path in (folder / 'manifest.json', *[folder / n for n in read(folder / 'manifest.json')['files']]):
            protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    archive = project / PILOT_RUN / 'delta-vsdc-five-query4s.zip'
    protected[archive.relative_to(project).as_posix()] = sha(archive.read_bytes())
    protected.update(runtime(project)); output.mkdir(parents=True)
    for name in ('selected_batches.json', 'reusable_detail_provider_ids.json', 'cache_policy.json', 'query_inventory_before_chain.json'):
        (output / name).write_bytes((project / old.PREP / name).read_bytes())
    for i, source in enumerate(spec['sources']):
        shutil.copytree(project / source['path'], query_folder(output, i))
        if hashes(query_folder(output, i)) != source['files']: raise ValueError('RECOVERY_IMPORT_COPY_FAILED')
    write(output / 'seed.json', spec); write(output / 'known_discovery_provider_ids.json', spec['known'])
    write(output / 'runtime.json', runtime(project)); write(output / 'protected_old_files.json', protected)
    write(output / 'plan.json', {'status': 'PREPARED_NOT_EXECUTED', 'config': contract(), 'imported_queries': 20,
        'remaining_queries': 1053, 'remaining_batches': 53, 'source_requests': 0, 'browser_launches': 0,
        'readiness': mbs.old.readiness(caps()), 'costs_carried_forward': spec['totals'],
        'prefix': 'Exact immutable15queries_at2s_plus5queries_at4s;never relabel or auto-retry the old STOP.',
        'continuation': 'New V4 segments only after verified user pause;partial restarts page1;source/crash errors STOP.',
        'progress': '20/1073 initially,Batch2/54 original numbering;53pendingbatches;ETA after5newV4queries.',
        'next_step': 'User local one command;return OUTPUT_ZIP for offline review;no agent acquisition.'})
    write(output / 'manifest.json', {'artifact_type': PREP_TYPE, 'files': hashes(output)})
    load_preparation(project)
    return {'status': 'PREPARED_NOT_EXECUTED', 'imported_queries': 20, 'remaining_queries': 1053,
        'remaining_batches': 53, 'interval_seconds': 4, 'protected_files': len(protected),
        'source_requests': 0, 'output': str(output)}


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


def seal_run(state):
    archive = state.parent / 'delta-vsdc-recovery4s.zip'
    base.seal(state, archive, artifact_type=TYPE); verify_zip(state, archive, TYPE)
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


def history(project,config,prep):
    """Only the complete sealed PAUSED prefix is eligible, never a source-error or crash run."""
    root=project/config['output_base'];runs=sorted(root.glob('run-*')) if root.exists() else []
    if len(runs)>=config['max_segments']:raise ValueError('SEGMENT_COUNT_CAP_REVIEW_REQUIRED')
    selected=read(prep/'selected_batches.json');order=flatten(selected)
    known=set(read(prep/'known_discovery_provider_ids.json'));reusable=set(read(prep/'reusable_detail_provider_ids.json'))
    seed=read(prep/'seed.json');totals=json.loads(json.dumps(seed['totals']));count=len(seed['completed']);previous=None;durations=list(seed['durations'])
    prefix_hashes={i:hashes(query_folder(prep,i)) for i in range(count)}
    for run in runs:
        if not run.is_dir() or run.is_symlink():raise ValueError('UNEXPECTED_RUN_PATH')
        state=run/'state';verify_zip(state,run/'delta-vsdc-recovery4s.zip',TYPE)
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
        'selected_batches':len(selected),'remaining_batches':sum(not all(r in prior['completed'] for r in flatten([b])) for b in selected),'headless':True,'interval_seconds':4,'readiness':ready}
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
    if prior['completed']:
        old=prior['runs'][-1]/'state' if prior['runs'] else prep
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
        reporter.finish(result['status'])
        totals['active_seconds']=old_active+clock()-started
        write(output/'result.json',result);checkpoint('FINAL_SEGMENT')
    return result

