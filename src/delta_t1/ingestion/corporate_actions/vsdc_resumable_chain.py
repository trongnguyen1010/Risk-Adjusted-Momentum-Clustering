"""Fixed54 local discovery, immutable segments, continuation only after a verified user pause."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import signal
import threading
import time
import zipfile

from . import vsdc_remaining_chain as base

read,write,sha,hashes=base.read,base.write,base.sha,base.hashes
CONFIG='configs/data/corporate_actions/vsdc_remaining54_resumable_v2.json'
TYPE='vsdc-remaining54-user-pause-segment-v2'
PREP_TYPE='vsdc-remaining54-user-pause-preparation-v2'
PAUSED='PAUSED_BY_USER_VERIFIED_CHECKPOINT'
COMPLETE='PASS_ALL54_QUERY_CHECKPOINTS_REVIEW_REQUIRED'
STOPPED='STOPPED_SOURCE_OR_INTEGRITY_REVIEW_REQUIRED'
OLD_PREP_DIGEST='320566da3757d52634ef0548010c34a4c3c133229083c6796318caae87d41245'
OLD_VALIDATION='data/corporate_actions/work/vsdc_remaining54_chain_validation_20261103_v1'
OLD_VALIDATION_DIGEST='72cd150a791d7c917e76ea133e81087cb02700800e030e176b365af26284c162'


def contract():
    return {'stage':'VSDC_FIXED54_USER_PAUSE_CONTINUATION_PREPARATION_V2',
        'output_base':'data/corporate_actions/work/vsdc_remaining54_resumable_v2',
        'preparation':'data/corporate_actions/work/vsdc_remaining54_resumable_preparation_20261103_v2',
        'scope_and_source_caps':base.contract(),'max_segments':100,
        'continuation':'ONLY_VERIFIED_USER_PAUSE','query_checkpoint':'FULL_QUERY_REPARSE_AND_ZIP',
        'partial_query':'RESTART_FROM_PAGE1_FRESH_CONTEXT','source_error_resume':False,
        'automatic_retry':False,'import_v1_run':False,'agent_acquisition':False}


def runtime(project):
    names=[CONFIG,'src/delta_t1/ingestion/corporate_actions/vsdc_resumable_chain.py',
        'scripts/corporate_actions/collect_vsdc_remaining54_resumable_v2.py',
        'scripts/corporate_actions/prepare_vsdc_remaining54_resumable_v2.py']
    return {**base.runtime(project),**{n:sha((project/n).read_bytes()) for n in names}}


def prepare(project):
    project=Path(project).resolve();old_config,old=base.load_preparation(project)
    config=read(project/CONFIG)
    if config!=contract():raise ValueError('EXACT_V2_CONTRACT_REQUIRED')
    if sha((old/'manifest.json').read_bytes())!=OLD_PREP_DIGEST:raise ValueError('V1_PREPARATION_CHANGED')
    validation=project/OLD_VALIDATION
    if sha((validation/'manifest.json').read_bytes())!=OLD_VALIDATION_DIGEST:raise ValueError('V1_VALIDATION_CHANGED')
    base.verify_artifact(validation,{'vsdc-remaining54-chain-preparation-validation-v1'})
    if (project/old_config['output_base']).exists():raise ValueError('EXISTING_V1_RUN_REQUIRES_OFFLINE_REVIEW_NOT_AUTO_IMPORT')
    out=project/config['preparation']
    if out.exists():raise FileExistsError('REFUSE_OVERWRITE')
    protected=read(old/'protected_old_files.json')
    for folder in (old,validation):
        for name in ['manifest.json',*read(folder/'manifest.json')['files']]:
            path=folder/name;protected[path.relative_to(project).as_posix()]=sha(path.read_bytes())
    protected.update(base.runtime(project))
    out.mkdir(parents=True)
    for name in ('selected_batches.json','reusable_detail_provider_ids.json','known_discovery_provider_ids.json',
                 'cache_policy.json','query_inventory_before_chain.json'):
        (out/name).write_bytes((old/name).read_bytes())
    write(out/'protected_old_files.json',protected);write(out/'runtime.json',runtime(project))
    write(out/'plan.json',{'config':config,'status':'PREPARED_NOT_EXECUTED','source_requests':0,'browser_launches':0,
        'scope':{'batches':54,'queries':1073,'estimated_list_requests':2839,'large_HOLD_excluded':7,
                 'archived_exhausted_outside':414,'unverified_outside':4},
        'pause':'Ctrl+C requests cooperative pause; --pause writes external control file',
        'continuation':'Same CLI, new immutable segment; verify all predecessors and copied complete query evidence',
        'caps':'Cumulative source counts and active time across all pauses, including discarded partial queries',
        'crash':'Unsealed output or stale active lock requires offline review; never automatic recovery',
        'new_completion_credit':0,'canonical_or_owner_changes':False,
        'readiness':base.mbs.old.readiness(base.contract())})
    write(out/'manifest.json',{'artifact_type':PREP_TYPE,'files':hashes(out)})
    load_preparation(project)
    return {'status':'PREPARED_NOT_EXECUTED','batches':54,'queries':1073,'source_requests':0,
        'protected_old_files':len(protected),'output':str(out)}


def load_preparation(project):
    base.load_preparation(project)
    config=read(project/CONFIG)
    if config!=contract():raise ValueError('EXACT_V2_CONTRACT_REQUIRED')
    prep=project/config['preparation'];base.verify_artifact(prep,{PREP_TYPE})
    if read(prep/'plan.json')['config']!=config or read(prep/'runtime.json')!=runtime(project):
        raise ValueError('V2_PREPARED_RUNTIME_CHANGED')
    base.mbs.old.protected_check(project,read(prep/'protected_old_files.json'))
    base.validate_selection(read(prep/'selected_batches.json'),read(prep/'query_inventory_before_chain.json'))
    if (project/base.contract()['output_base']).exists():raise ValueError('V1_RUN_PRESENT_REVIEW_REQUIRED')
    return config,prep


class Pause:
    def __init__(self,control):self.control=Path(control);self.event=threading.Event()
    def request(self,*args):self.event.set()
    def requested(self):return self.event.is_set() or self.control.exists()
    def check(self):
        if self.requested():raise KeyboardInterrupt('USER_PAUSE')


@contextmanager
def pause_signals(pause):
    previous=signal.getsignal(signal.SIGINT);signal.signal(signal.SIGINT,pause.request)
    try:yield
    finally:signal.signal(signal.SIGINT,previous)


class PauseDriver:
    """Pause between bounded browser operations; do not interrupt evidence sealing or writes."""
    def __init__(self,driver,pause):self.driver,self.pause=driver,pause
    def __enter__(self):self.driver.__enter__();return self
    def __exit__(self,*args):return self.driver.__exit__(*args)
    @property
    def version(self):return self.driver.version
    def first(self):self.pause.check();return self.driver.first()
    def next_page(self,*args):self.pause.check();return self.driver.next_page(*args)
    def pace(self,seconds):self.pause.check();return self.driver.pace(seconds)


def verify_zip(state,archive,kind):
    base.verify_artifact(state,{kind});expected=set(read(state/'manifest.json')['files'])|{'manifest.json'}
    if {p.relative_to(state).as_posix() for p in state.rglob('*') if p.is_file()}!=expected:
        raise ValueError('SEGMENT_MANIFEST_FILE_SET_MISMATCH')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist())!=len(expected) or set(z.namelist())!=expected:
            raise ValueError('SEGMENT_ZIP_CRC_OR_MEMBER_MISMATCH')
        for name in expected:
            if z.read(name)!=(state/name).read_bytes():raise ValueError('SEGMENT_ZIP_STATE_MISMATCH')


def seal_run(state):
    archive=state.parent/'delta-vsdc-resumable54.zip'
    base.seal(state,archive,artifact_type=TYPE)
    verify_zip(state,archive,TYPE)
    return archive


def flatten(selected):
    return [{'batch_id':b['batch_id'],'ticker':ticker} for b in selected for ticker in b['tickers']]


def query_definition(row):return {'batch_id':row['batch_id'],'tickers':[row['ticker']], 'estimated_list_requests':1}


def query_folder(state,index):return state/'queries'/f'{index+1:04d}'


def validate_query(folder,row,known,reusable):
    context=read(folder/'context.json')
    if context['scope']!=row:raise ValueError('QUERY_CHECKPOINT_SCOPE_MISMATCH')
    checked=base.validate_batch(folder/'state',folder/'query.zip',query_definition(row),base.contract(),
        reusable,known,context['previous_start'])
    if read(folder/'state/runtime.json')!=context['v1_runtime']:raise ValueError('QUERY_FROZEN_RUNTIME_MISMATCH')
    saved=read(folder/'validation.json')
    if {k:v for k,v in checked.items() if k!='state'}!={k:v for k,v in saved.items() if k!='state'}:
        raise ValueError('QUERY_CHECKPOINT_VALIDATION_MISMATCH')
    return read(folder/'state/deduplicated_query_articles.json')


def ledger_cost(folder):
    rows=[r for path in (folder/'state').glob('*/network_ledger.jsonl') for r in base.mbs.old.rows(path)]
    attempts=[r for r in rows if r['event']=='REQUEST_ATTEMPT']
    return {'business':sum(r.get('allowed') and r.get('classification')=='BUSINESS_LIST' for r in attempts),
        'context':len(attempts),'boundary':any('stop_reason' in r for r in rows)}


def initial_totals(selected):
    return {'business':0,'context':0,'active_seconds':0,
        'batches':{b['batch_id']:{'business':0,'context':0,'active_seconds':0} for b in selected}}


def check_totals(totals):
    c=base.contract()
    if (totals['business']>=c['max_business_requests'] or totals['context']>=c['max_context_attempts']
            or not math.isfinite(totals['active_seconds']) or not 0<=totals['active_seconds']<c['max_seconds']):
        raise ValueError('CUMULATIVE_CHAIN_BUDGET_EXHAUSTED')
    if any(b['business']>100 or b['context']>1660 or not math.isfinite(b['active_seconds'])
           or not 0<=b['active_seconds']<1200 for b in totals['batches'].values()):
        raise ValueError('CUMULATIVE_BATCH_BUDGET_EXHAUSTED')


def history(project,config,prep):
    """Only the complete sealed PAUSED prefix is eligible, never a source-error or crash run."""
    root=project/config['output_base'];runs=sorted(root.glob('run-*')) if root.exists() else []
    if len(runs)>=config['max_segments']:raise ValueError('SEGMENT_COUNT_CAP_REVIEW_REQUIRED')
    selected=read(prep/'selected_batches.json');order=flatten(selected)
    known=set(read(prep/'known_discovery_provider_ids.json'));reusable=set(read(prep/'reusable_detail_provider_ids.json'))
    totals=initial_totals(selected);count=0;previous=None;prefix_hashes={}
    for run in runs:
        if not run.is_dir() or run.is_symlink():raise ValueError('UNEXPECTED_RUN_PATH')
        state=run/'state';verify_zip(state,run/'delta-vsdc-resumable54.zip',TYPE)
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
            if attempt['complete']:expected_index+=1
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
            if context['v1_runtime']!=base.runtime(project):raise ValueError('QUERY_RUNTIME_CHANGED')
            articles=validate_query(folder,order[i],known,reusable)
            known.update(r['provider_article_id'] for r in articles)
        if (read(state/'known_discovery_after_validated_queries.json')!=sorted(known)
                or result['completed_query_count']!=len(completed)
                or result['remaining_query_count']!=len(order)-len(completed)
                or result['known_list_IDs']!=len(known) or result['reusable_detail_IDs_unchanged']!=len(reusable)
                or result['detail_requests'] or result['canonical_fields_applied'] or result['owner_choices_changed']
                or result['pit_or_identity_promoted'] or result['full_history_certified']):
            raise ValueError('SEGMENT_PROGRESS_OR_CACHE_CLASSIFICATION_MISMATCH')
        totals=result['totals'];check_totals(totals)
        count=len(completed);prefix_hashes={i:hashes(query_folder(state,i)) for i in range(count)}
        previous={'run':run.name,'manifest_sha256':sha((state/'manifest.json').read_bytes())}
    return {'runs':runs,'completed':order[:count],'known':known,'reusable':reusable,'totals':totals,
        'predecessor':previous,'prefix_hashes':prefix_hashes}


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


@contextmanager
def execution_lock(root,run_name):
    root.mkdir(parents=True,exist_ok=True);lock=root/'active.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    with os.fdopen(fd,'w',encoding='utf8') as f:json.dump({'run':run_name,'pid':os.getpid()},f)
    try:yield
    except BaseException:
        # An unhandled interruption leaves a deliberate review lock; do not auto-recover it.
        raise
    else:lock.unlink()


def run(project,output,*,pause=None,driver_factory=base.Driver,clock=time.monotonic,emit=print,dry_run=False):
    project,output=Path(project).resolve(),Path(output).resolve();config,prep=load_preparation(project)
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    prior=history(project,config,prep);selected=read(prep/'selected_batches.json');order=flatten(selected)
    ready=base.mbs.old.readiness(base.contract())
    if dry_run:return {'status':'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED','source_requests':0,
        'browser_launched':False,'completed_queries':len(prior['completed']),'remaining_queries':len(order)-len(prior['completed']),
        'selected_batches':len(selected),'readiness':ready}
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
    result={'status':STOPPED,'resumable':False,'source_requests_this_segment':0,'browser_launches_this_segment':0,
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
            emit(json.dumps({'event':'QUERY_START','batch_id':bid,'ticker':active['ticker'],
                'completed_queries':len(completed),'total_queries':len(order)}),flush=True)
            checkpoint('QUERY_START');folder=query_folder(output,i);folder.mkdir(parents=True)
            shared_config={**base.contract(),'max_batch_business_requests':100-b['business'],
                'max_batch_context_attempts':1660-b['context']}
            shared=base.Budget(shared_config,clock);shared.started=started-old_active
            shared.business=totals['business'];shared.attempts=totals['context'];shared.last=last;shared.begin(bid)
            shared.batch_started=attempt_started-b['active_seconds']
            write(folder/'context.json',{'scope':active,'previous_start':shared.previous_start,'v1_runtime':base.runtime(project)})
            before_business=shared.business;before_context=shared.attempts
            passed=False
            try:
                acquired=base.acquire_batch(project,folder/'state',query_definition(active),base.contract(),prep,shared,
                    prior['reusable'],known,check,lambda cfg,g:PauseDriver(driver_factory(cfg,g),pause),clock)
                result['browser_launches_this_segment']+=acquired['browser_launches']
                check();base.seal(folder/'state',folder/'query.zip',artifact_type=base.BATCH_TYPE)
                if acquired['status']=='PASS_SOURCE_BATCH_REQUIRES_AUTOMATED_VALIDATION':
                    checked=base.validate_batch(folder/'state',folder/'query.zip',query_definition(active),base.contract(),
                        prior['reusable'],known,shared.previous_start)
                    if read(folder/'state/runtime.json')!=base.runtime(project):raise ValueError('QUERY_RUNTIME_CHANGED')
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
                checkpoint('QUERY_VALIDATED')
                if i+1==len(order) or order[i+1]['batch_id']!=bid:
                    emit(json.dumps({'event':'BATCH_VALIDATED','batch_id':bid,'completed_queries':len(completed)}),flush=True)
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
        write(output/'result.json',result);checkpoint('FINAL_SEGMENT')
    return result
