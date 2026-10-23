"""Evidence gate for the next bounded candidate stage; no numeric/PIT promotion."""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import json
import shutil

from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_history_documents import read, put
from .financial_history_pit import parse_task
from .financial_history_audit_review import quarantine_rows

TERMINAL={'ACQUIRED','CACHED','NOT_REQUIRED_AFTER_SERIES_STOP','ACCESS_BLOCKED_IMPORTED','REQUEST_FAILED'}


def decide(e):
    """Only engineering readiness; gaps and quarantined candidates remain visible."""
    counters=['planned_tasks','terminal_tasks','transport_attempts','failed_requests','unfinished_requests',
              'successful_network_responses','network_parse_errors','cached_parse_errors','conflicting_raw_keys',
              'unexplained_orphans','required_audits','completed_audits','accepted_api_candidates','source_boundary_errors',
              'baseline_references','baseline_target','pdf_attempts','pdf_downloads','ocr_pages','max_pdf_ocr_pages',
              'artifact_bytes','free_disk_bytes']
    if any(type(e[k]) is not int or e[k]<0 for k in counters):raise ValueError('nonnegative integer gate counters required')
    attempt_rate=None if not e['transport_attempts'] else Decimal(e['failed_requests'])/e['transport_attempts']
    parser_rate=None if not e['successful_network_responses'] else Decimal(e['network_parse_errors'])/e['successful_network_responses']
    checks={
        'all_tasks_accounted':e['planned_tasks']>0 and e['planned_tasks']==e['terminal_tasks'],
        'no_interrupted_requests':e['unfinished_requests']==0,
        'failed_after_retry_rate':attempt_rate is not None and attempt_rate<=Decimal('.02'),
        'schema_parser_rate':parser_rate is not None and parser_rate<=Decimal('.01'),
        'cached_parser_replay':e['cached_parse_errors']==0,
        'raw_observation_keys':e['conflicting_raw_keys']==0 and e['unexplained_orphans']==0,
        'independent_document_audits':e['required_audits']>=6 and e['completed_audits']==e['required_audits'] and e['audit_issuer_modes_complete'],
        'all_audit_conflicts_quarantined':e['quarantine_complete'],
        'mapping_displacements_quarantined':e['row_shift_cohorts_held'],
        'no_candidate_auto_acceptance':e['accepted_api_candidates']==0,
        'source_boundaries':e['source_boundary_errors']==0 and not e['active_api_blocked'],
        'baseline_replay':e['baseline_references']==29 and e['baseline_target']==30,
        'resume_and_targeted_validation':e['resume_verified'] and e['targeted_validation_verified'],
        'budget':not e['budget_stop'] and e['pdf_attempts']<=100 and e['pdf_downloads']<=50 and e['ocr_pages']<=1000 and e['max_pdf_ocr_pages']<=40 and e['artifact_bytes']<=50_000_000_000,
        'disk_floor_at_decision':e['free_disk_bytes']>=30_000_000_000,
        'deadline_at_decision':e['campaign_anchor']<=e['decision_at']<e['campaign_anchor']+259200,
    }
    passed=all(checks.values())
    return dict(status='PASS_CANDIDATE_STAGE_ENGINEERING' if passed else 'PARTIAL',checks=checks,
                failed_after_retry_rate=None if attempt_rate is None else str(attempt_rate),
                schema_parser_failure_rate=None if parser_rate is None else str(parser_rate),
                rate_denominator_status='N_A' if attempt_rate is None or parser_rate is None else 'OBSERVED',
                pilot_history_engineering_pass=passed,max_total_issuers_next_stage=20,
                selection_metadata_required=True,batch20_started=False,financial_features_allowed=False,
                numeric_acceptance_allowed=False,research_ready=False,m3_ready=False)


def run(root,config_path,action):
    config=read(inside(root,config_path));pins={};cache={}
    if config.get('version')!='financial-history-stage-gate-v1':raise ValueError('gate version required')
    def pin(path,expected=None):
        if path not in cache:cache[path]=inside(root,path).read_bytes()
        raw=cache[path];sha=pins.get(path) or digest(raw)
        if expected is not None and sha!=expected:raise ValueError('gate input changed: '+path)
        pins[path]=sha;return raw
    pin(config_path)
    for p in ['src/delta_t1/experiments/financial_history_stage_gate.py','scripts/financial_history_stage_gate.py',
              'src/delta_t1/experiments/financial_history_pit.py','src/delta_t1/experiments/financial_history_audit_review.py']:pin(p)
    def product(source,name):
        folder=source['path'];manifest=json.loads(pin(folder+'/manifest.json',source['manifest_sha256']))
        return pin(folder+'/'+name,manifest[name])
    validation=json.loads(pin(config['validation']['path'],config['validation']['sha256']))
    for path,sha in validation['logs'].items():pin(path,sha)
    for record in validation['frozen_contracts']:
        contract=json.loads(pin(record['path'],record['sha256']))
        for path,sha in contract.get('code_pins',contract.get('pins',{})).items():pin(path,sha)
    pin(config['registry']['path'],config['registry']['sha256'])
    h=config['history_root'];plan=json.loads(pin(h+'/task-plan.json'));statuses=Counter();network_errors=cached_errors=0
    seen=set();parsed_network=0
    for task in plan:
        if task['id'] in seen:raise ValueError('duplicate planned task')
        seen.add(task['id']);p=h+'/receipts/'+task['id']+'.json'
        if not inside(root,p).exists():statuses['PENDING']+=1;continue
        receipt=json.loads(pin(p))
        if receipt['task']!=task:raise ValueError('receipt does not match task')
        statuses[receipt['status']]+=1
        if receipt.get('record'):
            record=receipt['record'];pin(record['path'],record['sha256'])
            try:parse_task(root,task,record)
            except (ValueError,KeyError,TypeError):
                if receipt['status']=='ACQUIRED':network_errors+=1
                else:cached_errors+=1
            if receipt['status']=='ACQUIRED':parsed_network+=1
    latest=None;starts=set();completed=set();failed=set();successful=0;pdf_downloads=0
    for item in config['network_journals']:
        raw=pin(item['path'],item['sha256']);ledger=read_compact(inside(root,item['path']).parent)
        if ledger['torn_tail_bytes']:raise ValueError('torn network journal')
        for line in raw.splitlines():
            event=json.loads(line);detail=event.get('detail',{});key=detail.get('request_key')
            if event['action']=='ATTEMPT_START':starts.add(key)
            elif event['action']=='ATTEMPT_COMPLETE':
                completed.add(key);successful+=1
                if detail.get('request_snapshot',{}).get('kind')=='pdf':pdf_downloads+=1
            elif event['action'] in ['HTTP_ERROR','TRANSPORT_ERROR']:failed.add(key)
        latest=ledger['state']
    if not latest or len(starts)!=latest['logical_requests']:raise ValueError('journal census does not match inherited logical counters')
    qa=json.loads(product(config['qa_result'],'summary.json'))
    shifts=json.loads(product(config['qa_result'],'possible_row_displacements.json'))
    reviews=json.loads(product(config['audit_result'],'reviews.json'));quarantine=json.loads(product(config['audit_result'],'candidate-quarantine.json'))
    tasks=json.loads(product(config['audit_plan'],'audit-tasks.json'))
    expected_ids={r['id'] for r in tasks};review_ids={r['sample_id'] for r in reviews}
    if len(review_ids)!=len(reviews) or review_ids!=expected_ids:raise ValueError('audit samples are not the frozen seeded targets')
    modes={s:{r['mode'] for r in reviews if r['symbol']==s} for s in {r['symbol'] for r in reviews}}
    held=json.loads(pin(config['disposition']['path'],config['disposition']['sha256']))
    if held['audit_result']!=config['audit_result']['path']:raise ValueError('disposition uses another audit vintage')
    boundaries=json.loads(pin(config['boundaries']['path'],config['boundaries']['sha256']))
    for record in boundaries['records']:pin(record['path'],record['sha256'])
    ocr=json.loads(product(config['ocr_result'],'summary.json'))
    reservations=json.loads(product(config['ocr_result'],'reservations.json'))
    if len(reservations)!=ocr['charged_pages']:raise ValueError('OCR reservation count differs')
    for item in reservations:
        p=item['output_root']+'/reservations/'+item['id']+'.json'
        if json.loads(pin(p))!=item['reservation']:raise ValueError('OCR reservation changed')
    baseline=json.loads(product(config['baseline_result'],'summary.json'))
    summary_keys=list(baseline)
    # Legacy completion summary has explicit completed/target, not provider ratios.
    refs=baseline.get('completed',baseline.get('verified_metrics'))
    target=baseline.get('target',baseline.get('target_metrics'))
    if refs is None or target is None:raise ValueError('unknown baseline completion schema: '+str(summary_keys))
    evidence=dict(planned_tasks=len(plan),terminal_tasks=sum(n for s,n in statuses.items() if s in TERMINAL),
        task_statuses=dict(statuses),transport_attempts=latest['transport_attempts'],failed_requests=len(failed-completed),
        unfinished_requests=len(starts-completed-failed),successful_network_responses=parsed_network,
        network_parse_errors=network_errors,cached_parse_errors=cached_errors,
        conflicting_raw_keys=qa['conflicting_observation_keys'],unexplained_orphans=qa['unexplained_orphans'],
        required_audits=len(tasks),completed_audits=len(reviews),audit_issuer_modes_complete=len(modes)>=3 and all(v=={'NAM','QUY'} for v in modes.values()),
        quarantine_complete=quarantine==quarantine_rows(reviews) and held['audit_conflicts_action']=='QUARANTINE_NO_NUMERIC_PROMOTION',
        row_shift_cohorts_held=held['row_shift_cohorts']==[dict(symbol=r['symbol'],year=r['year'],mode='NAM') for r in shifts] and held['row_shift_action']=='HOLD_MAPPING_PROMOTION',
        accepted_api_candidates=qa['accepted_new_facts'],source_boundary_errors=len(boundaries['errors']),
        active_api_blocked='apiweb.cafef.vn' in boundaries['blocked_hosts'],baseline_references=refs,baseline_target=target,
        resume_verified=validation['resume']['status']=='PASS' and validation['resume']['new_requests']==0 and validation['resume']['new_ocr_pages']==0,
        targeted_validation_verified=validation['targeted_tests']>=73 and validation['compile']=='PASS' and validation['active_process_verify']=='PASS',
        budget_stop=latest['budget_stop'] or latest['boundary'],pdf_attempts=latest['pdf_download_attempts'],pdf_downloads=pdf_downloads,
        ocr_pages=ocr['charged_pages'],max_pdf_ocr_pages=max(ocr['per_pdf_pages'].values(),default=0),
        campaign_anchor=latest['created_at'],decision_at=config['decision_at'],free_disk_bytes=config['free_disk_bytes_at_decision'],
        artifact_bytes=config['artifact_bytes_at_decision'],known_missing_coverage_slots=qa['missing_coverage_slots'])
    result=decide(evidence)
    result['scope']='Next bounded candidate acquisition only; category/identity partitions and template probes remain prerequisites. Not numeric/PIT acceptance.'
    products={'summary.json':encoded(result),'evidence.json':encoded(evidence),'input-pins.json':encoded(pins)}
    manifest={name:digest(raw) for name,raw in products.items()};out=inside(root,config['output_root'])/digest(encoded(manifest))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=manifest:raise ValueError('stage gate manifest changed')
        for name,sha in manifest.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('stage gate artifact changed')
    else:
        for name,raw in products.items():put(out/name,raw)
        put(out/'manifest.json',manifest)
    live_now=datetime.now(timezone.utc).timestamp()
    runtime_open=live_now<evidence['campaign_anchor']+259200 and shutil.disk_usage(root).free>=30_000_000_000
    return dict(result,runtime_extension_window_open=runtime_open,
                bounded_candidate_extension_eligible=result['pilot_history_engineering_pass'] and runtime_open,
                output=out.relative_to(root).as_posix())
