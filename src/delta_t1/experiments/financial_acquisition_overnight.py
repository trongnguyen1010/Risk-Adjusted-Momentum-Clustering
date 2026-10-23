"""Sequential owner-authorized remaining registry waves, original deadline retained."""
import csv,io,json,os,shutil,time
from pathlib import Path
from .financial_acquisition_waves import execute,validate_assignment
from .financial_acquisition_audit import run as audit_run
from .financial_history_documents import read,put
from ..ingestion.cafef_financial import digest,encoded,now
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_journal_stream import read_stream

CODE=['src/delta_t1/experiments/financial_acquisition_overnight.py','scripts/financial_acquisition_overnight.py']

def state_file(path,stage,**detail):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=encoded(dict(stage=stage,at=now(),**detail));tmp=path.with_suffix('.pending')
    with tmp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def campaign_assignment(rows,previous,planned):
    if planned['previous_members']!=previous:raise ValueError('previous campaign membership changed')
    return validate_assignment(rows,planned)

def check_parent(summary,ledger):
    s=ledger['state']
    if summary['status']!='COMPLETE_CANDIDATE_TASK_ACCOUNTING' or summary['parser_errors'] or summary['task_statuses'].get('PENDING',0) or summary['task_statuses'].get('FAILED_OR_STOPPED',0):raise ValueError('parent acquisition requires review')
    if ledger['torn_tail_bytes'] or s['boundary'] or s['budget_stop'] or s['reserved_bytes'] or s['created_at']!=1792414507.836684:raise ValueError('parent source/budget/anchor held')
    if summary['counters']!={k:v for k,v in s.items() if k not in ['requests','cache']}:raise ValueError('parent summary counters differ')
    if time.time()>=s['created_at']+259200:raise ValueError('original deadline closed; no reset')
    return s

def artifact_bytes(path):
    total=0
    if not path.exists():return total
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_symlink():raise ValueError('artifact symlink needs review')
            if entry.is_dir(follow_symlinks=False):total+=artifact_bytes(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):total+=entry.stat(follow_symlinks=False).st_size
    return total

def run(root,config_path):
    root=Path(root);c=read(inside(root,config_path));output=inside(root,c['output_root']);status=output/'pipeline-status.json'
    def ref(path):return dict(path=path,sha256=digest(inside(root,path).read_bytes()))
    def checked(item):
        body=inside(root,item['path']).read_bytes()
        if digest(body)!=item['sha256']:raise ValueError('campaign pin changed: '+item['path'])
        return body
    def cancel():
        if (output/'pipeline.cancel').exists():raise ValueError('campaign cancelled before next action')
    try:
        if c['version']!='financial-acquisition-overnight-v1':raise ValueError('unknown overnight version')
        rows=list(csv.DictReader(io.StringIO(checked(c['registry']).decode('utf-8-sig'))))
        planned=[json.loads(checked(item)) for item in c['assignments']]
        seed_assignment=json.loads(checked(c['initial_assignment']));previous=seed_assignment['previous_members']+seed_assignment['members']
        for assignment in planned:campaign_assignment(rows,previous,assignment);previous+=assignment['members']
        if len(previous)!=c['target_partitions'] or len(previous)!=len(rows):raise ValueError('campaign does not cover exact current registry')
        first_status=read(inside(root,c['initial_batch_root'])/'pipeline-status.json')
        if first_status['stage']!='COMPLETE_CANDIDATE_TASK_ACCOUNTING':raise ValueError('initial batch requires review or is not terminal')
        parent_root=c['initial_batch_root'];parent_result=first_status['detail']
        for number,a in enumerate(planned,1):
            cancel();batch_root=c['batch_roots'][number-1];out=inside(root,batch_root);wave_status=out/'pipeline-status.json'
            if (out/'network/transport.jsonl').exists():raise ValueError('existing network wave requires explicit resume review')
            state_file(status,'AUDITING_PARENT',parent_root=parent_root,next_batch_root=batch_root,wave=number,target_partitions=c['target_partitions'])
            parent_summary=read(inside(root,parent_result)/'summary.json');ledger=read_stream(inside(root,parent_root)/'network');s=check_parent(parent_summary,ledger)
            parent_assignment=read(inside(root,parent_root)/'assignment.json')
            campaign_assignment(rows,parent_assignment['previous_members']+parent_assignment['members'],a)
            audit_config=dict(version='financial-acquisition-stream-audit-v1',input_result=parent_result,input_manifest_sha256=ref(parent_result+'/manifest.json')['sha256'],batch_root=parent_root,output_root=batch_root+'/parent-audit')
            ap=batch_root+'/preflight/parent-audit-config.json';put(inside(root,ap),audit_config)
            audit=audit_run(root,ap);put(out/'preflight/parent-audit-result.json',audit)
            if audit['status']!='PASS_ACQUISITION_INTEGRITY_ONLY' or audit['field_statuses'].get('INVALID_NUMERIC',0) or audit['numeric_acceptance_allowed'] or audit['pit_ready']:raise ValueError('parent audit held')
            audit_root=audit['output'];am=read(inside(root,audit_root)/'manifest.json')
            for name,sha in am.items():
                if ref(audit_root+'/'+name)['sha256']!=sha:raise ValueError('audit output changed')
            report='artifacts/reports/'+a['batch_id'];report_dir=inside(root,report)
            put(report_dir/'parent-review-items.jsonl',(inside(root,audit_root)/'review-items.jsonl').read_bytes())
            put(report_dir/'parent-audit-ref.json',ref(audit_root+'/manifest.json'))
            put(report_dir/'report.md',('# Acquisition audit và wave kế tiếp\n\nParent: '+parent_root+'; audit '+audit['status']+'. Missing slots='+str(audit['missing_coverage_slots'])+', review items='+str(audit['review_items'])+'. Semantic/PDF review deferred; numerical/PIT/M3 chưa đủ.\n').encode('utf-8'))
            cancel();state_file(status,'BUILDING_ENGINEERING_GATE',next_batch_root=batch_root,wave=number)
            n=len(a['members']);size=artifact_bytes(root/'data/financial')+sum(artifact_bytes(p) for p in (root/'artifacts/reports').glob('financial*') if p.is_dir())
            estimated=parent_summary['task_statuses'].get('ACQUIRED',0)/len(parent_assignment['members'])*n*.65
            checks=dict(raw_replay=audit['candidate_cells']==parent_summary['candidate_cells'],receipt_replay=audit['raw_responses_replayed']==sum(parent_summary['task_statuses'].get(k,0) for k in ['ACQUIRED','CACHED_PROBE']),no_invalid_tokens=not audit['field_statuses'].get('INVALID_NUMERIC',0),no_failed_parent=not parent_summary['task_statuses'].get('FAILED_OR_STOPPED',0),disk_floor=shutil.disk_usage(root).free>=30000000000,artifact_cap=size+6000000000<=50000000000,deadline_projection=time.time()+estimated<s['created_at']+259200)
            pins={p:ref(p)['sha256'] for p in CODE+[config_path,c['registry']['path'],c['assignments'][number-1]['path'],parent_result+'/manifest.json',parent_result+'/summary.json',audit_root+'/manifest.json',audit_root+'/summary.json',report+'/parent-review-items.jsonl']}
            gate=dict(status='PASS_NEXT_DISJOINT_WAVE' if all(checks.values()) else 'HOLD',checks=checks,input_pins=pins,approved_additional_partitions=n,candidate_acquisition_allowed=all(checks.values()),numeric_acceptance_allowed=False,pit_ready=False,research_ready=False,parent_counters={k:v for k,v in s.items() if k not in ['requests','cache']},cost_projection=dict(estimated_seconds=estimated,deadline_epoch=s['created_at']+259200,artifact_bytes_conservative=size))
            gp=batch_root+'/preflight/engineering-gate.json';put(inside(root,gp),gate)
            if not all(checks.values()):raise ValueError('next wave gate held: '+str(checks))
            conf=dict(version='financial-acquisition-waves-v1',batch_id=a['batch_id'],owner='financial-history-collector',output_root=batch_root,years=list(range(2013,2026)),auxiliary_balance_year=2012,registry=c['registry'],assignment=c['assignments'][number-1],engineering_gate=ref(gp),parent_network=parent_root+'/network',parent_journal_sha256=ref(parent_root+'/network/transport.jsonl')['sha256'],campaign_worker_root='data/financial/history_campaign_v1/network-worker',approved_hosts=['apiweb.cafef.vn'],boundary_roots=['data/financial','artifacts/reports/financial-cafef-rediscovery-v2/network'],cache_epoch=a['batch_id']+'-rate04',network_concurrency=1,max_campaign_days=90,numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False,budgets=dict(max_logical_requests=s['logical_requests']+140*n,max_transport_attempts=s['transport_attempts']+280*n,max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5000000,max_total_downloaded_bytes=s['downloaded_bytes']+2000000000,max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=.4))
            cp=batch_root+'/preflight/config.json';put(inside(root,cp),conf)
            cancel();state_file(status,'OFFLINE_PLAN_AND_VERIFY',next_batch_root=batch_root,wave=number)
            execute(root,cp,'plan',False,0);execute(root,cp,'verify',False,0)
            cancel();state_file(status,'RUNNING_CANDIDATE_ACQUISITION',batch_root=batch_root,wave=number,partitions=n,spacing_seconds=.4,network_concurrency=1)
            state_file(wave_status,'RUNNING_CANDIDATE_ACQUISITION',partitions=n,spacing_seconds=.4)
            result=execute(root,cp,'run',True,140*n);put(out/'terminal-summary.json',result)
            stage='COMPLETE_CANDIDATE_TASK_ACCOUNTING' if result['status']=='COMPLETE_CANDIDATE_TASK_ACCOUNTING' and not result['parser_errors'] and not result['task_statuses'].get('FAILED_OR_STOPPED',0) and not result['counters']['boundary'] and not result['counters']['budget_stop'] else 'PARTIAL_REVIEW_REQUIRED'
            state_file(wave_status,stage,detail=result['output'])
            if stage!='COMPLETE_CANDIDATE_TASK_ACCOUNTING':raise ValueError('wave held for review: '+result['output'])
            parent_root=batch_root;parent_result=result['output']
        state_file(status,'AUDITING_FINAL_WAVE',batch_root=parent_root)
        final_config=dict(version='financial-acquisition-stream-audit-v1',input_result=parent_result,input_manifest_sha256=ref(parent_result+'/manifest.json')['sha256'],batch_root=parent_root,output_root=parent_root+'/final-audit')
        fp=parent_root+'/preflight/final-audit-config.json';put(inside(root,fp),final_config)
        final_audit=audit_run(root,fp);put(inside(root,parent_root)/'preflight/final-audit-result.json',final_audit)
        if final_audit['status']!='PASS_ACQUISITION_INTEGRITY_ONLY':raise ValueError('final audit held')
        state_file(status,'COMPLETE_CURRENT_REGISTRY_TASK_ACCOUNTING',partitions=len(rows),last_result=parent_result,financial_delivery='PARTIAL_NOT_NUMERIC_OR_PIT_ACCEPTANCE',final_wave_audit=final_audit['output'])
        return read(status)
    except Exception as error:
        state_file(status,'HELD_OR_FAILED_NO_AUTOMATIC_RESTART',reason=str(error));raise
