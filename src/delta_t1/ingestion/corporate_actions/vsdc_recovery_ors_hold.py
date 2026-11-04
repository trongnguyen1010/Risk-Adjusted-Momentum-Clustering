"""V5: keep575 complete queries, retain ORS80/85 HOLD, acquire497others at4s."""
from pathlib import Path
from bisect import bisect_right
from collections import deque
from datetime import datetime, timezone
import copy
import json
import math
import re
import shutil
import time

from . import vsdc_recovery4s as old

base, mbs, pilot, prior = old.base, old.mbs, old.pilot, old.prior
read, write, sha, hashes = old.read, old.write, old.sha, old.hashes
Pause, pause_signals, execution_lock = old.Pause, old.pause_signals, old.execution_lock
flatten, query_definition, query_folder = old.flatten, old.query_definition, old.query_folder
initial_totals, check_totals, ledger_cost = old.initial_totals, old.check_totals, old.ledger_cost
verify_zip, ProgressDriver = old.verify_zip, old.ProgressDriver
Guard, HeadlessDriver = old.Guard, old.HeadlessDriver
source_contract, list_page, search_url = old.source_contract, old.list_page, old.search_url
ids_hash, deduplicate = old.ids_hash, old.deduplicate
CONFIG = 'configs/data/corporate_actions/vsdc_recovery_ors_hold_v5.json'
OUTPUT = 'data/corporate_actions/work/vsdc_recovery_ors_hold_v5'
PREP = 'data/corporate_actions/work/vsdc_recovery_ors_hold_preparation_20261103_v5'
TYPE = 'vsdc-reviewed575-recovery497-with-ORS-HOLD-segment-v5'
PREP_TYPE = 'vsdc-reviewed575-recovery497-with-ORS-HOLD-preparation-v5'
PAUSED, STOPPED = old.PAUSED, old.STOPPED
COMPLETE = 'PASS_SCOPED_QUERIES_WITH_ORS_HOLD_REVIEW_REQUIRED'
RUN = old.OUTPUT + '/run-20261103T112801286796Z'
REVIEW = 'data/corporate_actions/work/vsdc_recovery4s_stop_review_20261103_v4'
RUN_DIGEST = '86227097657f9f1e4e73b232c62a07f60e59e2c52a6c46cbd6ff7995e7a86cb5'
ZIP_DIGEST = 'fb5d4e6926d5feab59f81d29394fca870ad7d1a26c6e631d2293894fa0b792a4'
PARENTS = {
    old.PREP: ('b31dfcd0cd14898cdb43972b90491c281ff1e40f8e3b65ba5656b67fd1e0f2cc', old.PREP_TYPE),
    'data/corporate_actions/work/vsdc_recovery4s_validation_20261103_v4':
        ('496e093f04ab75d813898dac55f8251d0921a25197c9b1cc9943410ef00df36c',
         'vsdc-reviewed20-recovery4s-preparation-validation-v4'),
    REVIEW: ('52b96ff791e67eb949ff0540860b733fb899a88b3cf84a66c708d76d85a5bb95',
             'vsdc-recovery4s-ORS-empty-last-page-offline-stop-review-v4'),
}


def caps():
    return {**old.caps(), 'stage': 'VSDC_RECOVERY497_WITH_ORS_HOLD_QUERY_V5',
        'output_base': OUTPUT, 'preparation': PREP, 'selected_query_count': 1072,
        'estimated_list_requests': 2834}


def contract():
    return {**old.contract(), 'stage': 'VSDC_REVIEWED575_RECOVERY497_ORS_HOLD_V5',
        'output_base': OUTPUT, 'preparation': PREP, 'scope_and_source_caps': caps(),
        'reviewed_import_count': 575, 'remaining_queries_before_first_run': 497,
        'remaining_batches_before_first_run': 26, 'original_query_count': 1073,
        'scoped_query_count': 1072, 'held_tickers': ['ORS'],
        'recovery_import': 'ONLY_PINNED_V4_575_COMPLETE_WITH_IMMUTABLE_ORS_PARTIAL_HOLD',
        'prior_costs': 'CARRY_V4_TOTALS_INCLUDING_ALL_EARLIER_RUNS_AND_FAILED_ORS',
        'inherited_prefix_cadence': 'ORIGINAL15_AT2S_PLUS560_AT4S_NEVER_RELABEL',
        'evidence_checks': 'FULL_FILES_AT_PREFLIGHT_AND_COPY;FULL_SEALED_ZIP_SHA256_EVERY_SOURCE_CHECK',
        'completion': COMPLETE, 'full_query_acceptance_relaxed': False}


def runtime(project):
    names = [CONFIG, 'src/delta_t1/ingestion/corporate_actions/vsdc_recovery_ors_hold.py',
        'scripts/corporate_actions/prepare_vsdc_recovery_ors_hold_v5.py',
        'scripts/corporate_actions/collect_vsdc_recovery_ors_hold_v5.py']
    return {**old.runtime(project), **{n: sha((project / n).read_bytes()) for n in names}}


def parents(project):
    if (project / old.OUTPUT / 'active.lock').exists(): raise ValueError('RECOVERY_V4_ACTIVE_OR_UNCLEAN_LOCK')
    if sorted(p.name for p in (project / old.OUTPUT).glob('run-*')) != [Path(RUN).name]:
        raise ValueError('RECOVERY_EXACT_REVIEWED_V4_RUN_REQUIRED')
    for name, (digest, kind) in PARENTS.items():
        folder = project / name
        if sha((folder / 'manifest.json').read_bytes()) != digest: raise ValueError('RECOVERY_PARENT_CHANGED')
        base.verify_artifact(folder, {kind})
    if read(project / old.PREP / 'runtime.json') != old.runtime(project): raise ValueError('RECOVERY_OLD_RUNTIME_CHANGED')
    mbs.old.protected_check(project, read(project / old.PREP / 'protected_old_files.json'))
    state = project / RUN / 'state'
    if sha((state / 'manifest.json').read_bytes()) != RUN_DIGEST: raise ValueError('RECOVERY_V4_MANIFEST_CHANGED')
    if sha((project / RUN / 'delta-vsdc-recovery4s.zip').read_bytes()) != ZIP_DIGEST:
        raise ValueError('RECOVERY_V4_SEALED_ZIP_CHANGED')
    # Prior review binds this exact ZIP to the exact manifest/full raw state.
    # Preflight still rehashes every current raw file; per-operation checks below
    # use the full sealed ZIP digest instead of repeating24000file reads.
    base.verify_artifact(state, {old.TYPE})
    review = read(project / REVIEW / 'review.json')
    if (review['status'] != 'PASS_OFFLINE_REVIEW_OF_PARTIAL_V4_STOP_ORS_SOURCE_COUNT_GAP'
            or review['manifest_sha256'] != RUN_DIGEST or review['ZIP_sha256'] != ZIP_DIGEST
            or review['completed_original_selected_queries'] != 575):
        raise ValueError('RECOVERY_REVIEWED_575_AND_ORS_GAP_REQUIRED')
    return project / old.PREP


def subtree_files(manifest, prefix):
    return {name[len(prefix):]: digest for name, digest in manifest['files'].items() if name.startswith(prefix)}


def import_spec(project):
    state = project / RUN / 'state'; manifest = read(state / 'manifest.json')
    original = read(project / old.PREP / 'selected_batches.json'); order = flatten(original)
    completed = read(state / 'completed_queries.json'); result = read(state / 'result.json')
    if completed != order[:575] or result['status'] != STOPPED or result['active_query'] != order[575] or order[575]['ticker'] != 'ORS':
        raise ValueError('RECOVERY_575_PREFIX_AND_ORS_SCOPE_REQUIRED')
    scoped = copy.deepcopy(original)
    for batch in scoped:
        if 'ORS' in batch['tickers']:
            batch['tickers'].remove('ORS'); batch['estimated_list_requests'] -= 5
    active_order = flatten(scoped)
    if len(active_order) != 1072 or active_order[:575] != completed or len(active_order[575:]) != 497:
        raise ValueError('RECOVERY_EXACT_SCOPED_PARTITION_REQUIRED')
    sources = []
    for i, row in enumerate(completed):
        prefix = f'queries/{i+1:04d}/'; files = subtree_files(manifest, prefix)
        if not files: raise ValueError('RECOVERY_IMPORTED_EVIDENCE_MISSING')
        sources.append({'scope': row, 'path': (Path(RUN) / 'state' / prefix).as_posix(),
            'original_interval_seconds': 2 if i < 15 else 4, 'files': files})
    held_path = 'queries/0576/'; held_files = subtree_files(manifest, held_path)
    partial = state / held_path / 'state/ORS'; seen = []
    for number in range(1, 5):
        raw = (partial / f'rendered_html/page{number}.html').read_text(encoding='utf8')
        parsed = list_page(raw, number, 'ORS', 85 if number > 1 else None, seen)
        if parsed != read(partial / f'page{number}.json'): raise ValueError('RECOVERY_ORS_PARTIAL_REPARSE_CHANGED')
        seen.extend(parsed['article_ids'])
    try: list_page((partial / 'rendered_html/page5.html').read_text(encoding='utf8'), 5, 'ORS', 85, seen)
    except ValueError: pass
    else: raise ValueError('RECOVERY_ORS_GAP_NO_LONGER_MATCHES_REVIEW')
    if len(set(seen)) != 80 or (partial / 'complete_query.json').exists(): raise ValueError('RECOVERY_ORS_MUST_STAY_PARTIAL')
    held = {'ticker': 'ORS', 'original_scope': order[575], 'status': 'HOLD_SOURCE_COUNT_GAP',
        'reported_total': 85, 'observed_distinct_rows': 80, 'unresolved_reported_row_slots': 5,
        'query_complete': False, 'NO_EVENT': False, 'source_path': (Path(RUN) / 'state' / held_path).as_posix(),
        'source_manifest_sha256': RUN_DIGEST, 'evidence_files': held_files,
        'full_history_certified': False, 'costs_already_in_seed': True}
    totals = copy.deepcopy(result['totals'])
    if totals['business'] != 1514 or totals['context'] != 32092 or abs(totals['active_seconds']-7148.281) > 1e-6:
        raise ValueError('RECOVERY_V4_AUDITED_COSTS_CHANGED')
    check_totals(totals)
    known = read(state / 'known_discovery_after_validated_queries.json')
    if len(known) != 39567 or len(read(project / old.PREP / 'reusable_detail_provider_ids.json')) != 27731:
        raise ValueError('RECOVERY_KNOWN_OR_DETAIL_CACHE_CHANGED')
    return {'completed': completed, 'sources': sources, 'totals': totals, 'known': known,
        'durations': [], 'held': held, 'original_selected': original, 'scoped_selected': scoped,
        'cost_provenance': {'cumulative_V4_including_earlier_costs': totals,
            'V4_manifest_sha256': RUN_DIGEST, 'failed_ORS_included_not_charged_twice': True}}


def load_preparation(project):
    config = read(project / CONFIG)
    if config != contract(): raise ValueError('EXACT_RECOVERY497_ORS_HOLD_V5_CONTRACT_REQUIRED')
    parents(project); prep = project / PREP; base.verify_artifact(prep, {PREP_TYPE})
    if read(prep / 'runtime.json') != runtime(project) or read(prep / 'plan.json')['config'] != config:
        raise ValueError('RECOVERY_PREPARED_RUNTIME_CHANGED')
    mbs.old.protected_check(project, read(prep / 'protected_old_files.json'))
    spec = import_spec(project)
    if read(prep / 'seed.json') != spec: raise ValueError('RECOVERY_HOLD_SEED_CHANGED')
    if (read(prep / 'selected_batches.json') != spec['scoped_selected']
            or read(prep / 'original_selected_batches.json') != spec['original_selected']
            or read(prep / 'held_query.json') != spec['held']
            or read(prep / 'known_discovery_provider_ids.json') != spec['known']):
        raise ValueError('RECOVERY_SCOPED_PARTITION_OR_HOLD_CHANGED')
    for i, source in enumerate(spec['sources']):
        if hashes(query_folder(prep, i)) != source['files']: raise ValueError('RECOVERY_IMPORTED_COPY_CHANGED')
    if hashes(prep / 'holds/ORS') != spec['held']['evidence_files']: raise ValueError('RECOVERY_ORS_HOLD_COPY_CHANGED')
    return config, prep


def prepare(project):
    project = Path(project).resolve()
    if read(project / CONFIG) != contract(): raise ValueError('EXACT_RECOVERY497_ORS_HOLD_V5_CONTRACT_REQUIRED')
    previous = parents(project); output = project / PREP
    if output.exists(): raise FileExistsError('REFUSE_OVERWRITE')
    spec = import_spec(project); protected = read(previous / 'protected_old_files.json')
    for name in PARENTS:
        folder = project / name
        for path in (folder / 'manifest.json', *[folder / n for n in read(folder / 'manifest.json')['files']]):
            protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    # Preserve full SHA256 checks/cadence. Seal+manifest protect the reviewed V4
    # evidence used for the575copies; no mtime/digest cache or gate weakening.
    for path in (project / RUN / 'state/manifest.json', project / RUN / 'delta-vsdc-recovery4s.zip'):
        protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    protected.update(runtime(project)); output.mkdir(parents=True)
    for name in ('reusable_detail_provider_ids.json', 'cache_policy.json', 'query_inventory_before_chain.json'):
        (output / name).write_bytes((previous / name).read_bytes())
    for i, source in enumerate(spec['sources']):
        shutil.copytree(project / source['path'], query_folder(output, i))
        if hashes(query_folder(output, i)) != source['files']: raise ValueError('RECOVERY_IMPORT_COPY_FAILED')
    shutil.copytree(project / spec['held']['source_path'], output / 'holds/ORS')
    write(output / 'held_query.json', spec['held']); write(output / 'original_selected_batches.json', spec['original_selected'])
    write(output / 'selected_batches.json', spec['scoped_selected']); write(output / 'seed.json', spec)
    write(output / 'known_discovery_provider_ids.json', spec['known'])
    write(output / 'protected_old_files.json', protected); write(output / 'runtime.json', runtime(project))
    write(output / 'plan.json', {'status': 'PREPARED_NOT_EXECUTED', 'config': contract(),
        'imported_queries': 575, 'remaining_active_queries': 497, 'held_queries': 1,
        'original_total': 1073, 'scoped_total': 1072, 'remaining_batches': 26,
        'source_requests': 0, 'browser_launches': 0, 'readiness': mbs.old.readiness(caps()),
        'costs_carried': spec['totals'], 'prefix': 'Exact immutable575queryfolders;ORS80/85 preserved asHOLD,never complete.',
        'progress': '575/1072 scoped target,original1073/HOLD1 clearly shown;final status retains HOLD.',
        'integrity': 'Full source/preparation files checked at preflight;old protected checks retained;V4sealedZIP+manifest fullySHA256 every check;exact imported copies before source.',
        'next_step': 'User local sameCLI run/pause/continue,return ZIP;no agent acquisition.'})
    write(output / 'manifest.json', {'artifact_type': PREP_TYPE, 'files': hashes(output)})
    # Copies just verified while written; read-only CLI preflight revalidates the
    # sealed preparation before any source request,without repeating that here.
    base.verify_artifact(output, {PREP_TYPE})
    return {'status': 'PREPARED_NOT_EXECUTED', 'imported_queries': 575, 'remaining_queries': 497,
        'held_queries': 1, 'remaining_batches': 26, 'protected_files': len(protected), 'source_requests': 0,
        'output': str(output)}


def scope_summary(prep, completed):
    original = read(prep / 'original_selected_batches.json'); held = read(prep / 'held_query.json')
    done = {tuple(sorted(r.items())) for r in completed}
    fully_done = [b['batch_id'] for b in original if all(tuple(sorted({'batch_id': b['batch_id'], 'ticker': t}.items())) in done for t in b['tickers'])]
    return {'held_query_count': 1, 'held_tickers': [held['ticker']], 'original_total_queries': len(flatten(original)),
        'scoped_total_queries': len(flatten(original))-1, 'original_unresolved_query_count': len(flatten(original))-len(completed),
        'original_fully_completed_batch_ids': fully_done, 'original_full_scope_complete': False}


def validate_hold_copies(state, prep):
    if (read(state / 'held_query.json') != read(prep / 'held_query.json')
            or read(state / 'original_selected_batches.json') != read(prep / 'original_selected_batches.json')
            or hashes(state / 'holds/ORS') != read(prep / 'held_query.json')['evidence_files']):
        raise ValueError('RECOVERY_HOLD_EVIDENCE_OR_SCOPE_CHANGED')


def progress_line(row):
    return old.old.progress_line(row) + ' | Phạm vi gốc 1073 | ORS HOLD 1 (80/85)'


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


def seal_run(state):
    archive = state.parent / 'delta-vsdc-recovery-ORS-HOLD.zip'
    base.seal(state, archive, artifact_type=TYPE); verify_zip(state, archive, TYPE)
    return archive


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
        state=run/'state';verify_zip(state,run/'delta-vsdc-recovery-ORS-HOLD.zip',TYPE)
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
    prior=history(project,config,prep);selected=read(prep/'selected_batches.json');order=flatten(selected)
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
        result.update(scope_summary(prep,completed))
        try:validate_hold_copies(output,prep)
        except Exception as exc:result.update(status=STOPPED,resumable=False,stop_reason=pilot.safe_reason(exc))
        reporter.finish(result['status'])
        totals['active_seconds']=old_active+clock()-started
        write(output/'result.json',result);checkpoint('FINAL_SEGMENT')
    return result

