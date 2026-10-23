"""Bounded financial template probes, preserving raw candidates and inherited budgets."""
from collections import Counter
import copy,json,time
from urllib.parse import urlsplit

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.cafef_financial_deep import parse_report,report_url
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_history_documents import DocumentTransport,read,put
from .financial_history_pit import audit_boundaries,GROUPS
from .financial_history20_profiles import run as profile_run
from .financial_user_workflow import exclusive

CODE=['src/delta_t1/experiments/financial_history20_probes.py','scripts/financial_history20_probes.py',
      'scripts/financial_history20_probes.ps1','src/delta_t1/experiments/financial_history20_profiles.py',
      'scripts/financial_history20_profiles.py','src/delta_t1/experiments/financial_history_documents.py',
      'src/delta_t1/experiments/financial_history_pit.py','src/delta_t1/ingestion/cafef_financial_deep.py',
      'src/delta_t1/ingestion/financial_compact_trial.py','src/delta_t1/ingestion/financial_trial_transport.py',
      'src/delta_t1/ingestion/financial_batch_evidence.py','src/delta_t1/experiments/financial_user_workflow.py']


def tasks(members):
    result=[]
    if len(members)!=15 or len({r['registry_id'] for r in members})!=15 or len({r['symbol'] for r in members})!=15:
        raise ValueError('fifteen distinct verified profile partitions required')
    for member in members:
        if member['status']!='CURRENT_PROFILE_OBSERVED':raise ValueError('unverified profile cannot be probed')
        for mode in ['NAM','QUY']:
            for statement,groups in GROUPS.items():
                for group in groups:
                    t=dict(registry_id=member['registry_id'],provider_partition_id=member['provider_partition_id'],
                           symbol=member['symbol'],statement=statement,mode=mode,group=group,page=1)
                    t['url']=report_url(t['symbol'],statement,mode,group,1);t['id']=digest(t['url'].encode());result.append(t)
    # First breadth across institutions and statements, annual before quarterly.
    return sorted(result,key=lambda t:(t['mode'],t['group'],t['symbol']))


def inspect(body,task,source):
    cells=parse_report(body,task['symbol'],task['statement'],task['mode'],source)
    expected=task['group']
    groups=sorted({r['group'] for r in cells})
    if groups and expected not in groups:raise ValueError('requested financial group absent in response')
    return dict(status='PARSED_CANDIDATES' if cells else 'EMPTY_PROVIDER_SERIES',cell_count=len(cells),
                template_sha256=sorted({r['template_sha256'] for r in cells}),observed_groups=groups,
                period_keys=[list(p) for p in sorted({(r['year'],r['quarter'],r['provider_type']) for r in cells},key=str)],
                unmapped_cells=sum(r['label'] is None for r in cells),
                accepted=False,pit_ready=False,scope_status='UNRESOLVED',unit_status='NOT_ACCEPTED')


def prepare(root,config_path):
    c=read(inside(root,config_path))
    if c.get('version')!='financial-history20-probes-v1' or c.get('approved_hosts')!=['apiweb.cafef.vn']:
        raise ValueError('dedicated API template probe contract required')
    if c.get('network_concurrency')!=1 or c.get('max_campaign_days')!=90:raise ValueError('single worker/original campaign required')
    if any(c.get(k) is not False for k in ['numeric_acceptance_allowed','full_history_acquisition_allowed','research_ready']):
        raise ValueError('template probe cannot open numeric/history/research gates')
    pins={p:digest(inside(root,p).read_bytes()) for p in CODE+[config_path]}
    pc=c['profiles_config'];raw=inside(root,pc['path']).read_bytes()
    if digest(raw)!=pc['sha256']:raise ValueError('profile configuration changed')
    pins[pc['path']]=pc['sha256'];profile=profile_run(root,pc['path'],'verify')
    if not profile['template_probe_eligible'] or profile['output']!=c['profiles_result']:raise ValueError('profile gate closed')
    source=c['profiles_result'];manifest=read(inside(root,source+'/manifest.json'))
    for name,sha in manifest.items():
        p=source+'/'+name
        if digest(inside(root,p).read_bytes())!=sha:raise ValueError('profile results changed')
        pins[p]=sha
    members=read(inside(root,source+'/profiles.json'));jobs=tasks(members)
    parent=inside(root,c['parent_network']);raw=(parent/'transport.jsonl').read_bytes()
    if digest(raw)!=c['parent_journal_sha256']:raise ValueError('probe counter parent changed')
    old=read_compact(parent);s=old['state']
    if old['torn_tail_bytes'] or s['boundary'] or s['budget_stop']:raise ValueError('unsafe probe counter parent')
    limits=dict(max_logical_requests=s['logical_requests']+180,max_transport_attempts=s['transport_attempts']+360,
                max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5_000_000,
                max_total_downloaded_bytes=s['downloaded_bytes']+900_000_000,max_wall_seconds=259200,
                max_attempts_per_request=2,timeout_seconds=20)
    b=c['budgets']
    if any(type(b.get(k)) is not int or not 1<=b[k]<=cap for k,cap in limits.items()):raise ValueError('invalid probe budget')
    if b['min_seconds_between_transport_attempts']<2:raise ValueError('financial spacing required')
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True)
    cp=out/'contract.json'
    if cp.exists():
        contract=read(cp)
        if contract['pins']!=pins or contract['tasks']!=jobs:raise ValueError('frozen probe contract changed')
        for item in contract['boundaries']['records']:
            if digest(inside(root,item['path']).read_bytes())!=item['sha256']:raise ValueError('imported boundary changed')
    else:
        boundaries=audit_boundaries(root,dict(boundary_roots=c['boundary_roots']),out)
        if boundaries['errors']:raise ValueError('probe source boundary inventory failed')
        contract=dict(pins=pins,tasks=jobs,boundaries=boundaries,seed=copy.deepcopy(s),version=c['version'])
        put(cp,contract)
    return c,out,contract


def execute(root,config_path,action,network=False,max_new_requests=180):
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=180:
        raise ValueError('invalid bounded probe action/wave')
    c,out,contract=prepare(root,config_path)
    if network:
        if action!='run' or time.time()>=contract['seed']['created_at']+c['budgets']['max_wall_seconds']:
            raise ValueError('original probe deadline closed')
        worker=inside(root,c['campaign_worker_root']);worker.mkdir(parents=True,exist_ok=True)
        with exclusive(worker):
            with exclusive(out):
                transport=None;used=0
                for task in contract['tasks']:
                    rp=out/'receipts'/(task['id']+'.json')
                    if rp.exists():continue
                    if urlsplit(task['url']).hostname in contract['boundaries']['blocked_hosts']:
                        put(rp,dict(task=task,status='IMPORTED_SOURCE_BOUNDARY'));continue
                    if used>=max_new_requests:break
                    if transport is None:transport=DocumentTransport(root,out/'network',c,contract['seed'])
                    if any(r['url']==task['url'] for r in transport.state['requests'].values()):
                        raise ValueError('interrupted probe without receipt requires explicit review')
                    transport.context=dict(kind='structured',symbol=task['symbol'],report='TEMPLATE_PROBE')
                    try:
                        body,status=transport.get(task['url']);sha=digest(body);raw=out/'raw'/(sha+'.json');put(raw,body)
                        receipt=dict(task=task,status='ACQUIRED',path=raw.relative_to(root).as_posix(),sha256=sha,bytes=len(body),http_status=status)
                        try:receipt['inspection']=inspect(body,task,sha)
                        except Exception as error:receipt['inspection']=dict(status='PARSE_REVIEW_REQUIRED',reason=str(error),accepted=False)
                        put(rp,receipt)
                    except Exception as error:
                        put(rp,dict(task=task,status='FAILED_OR_STOPPED',reason=str(error)))
                        if transport.state['boundary'] or transport.state['budget_stop']:break
                    used+=1
    receipts=[]
    for task in contract['tasks']:
        rp=out/'receipts'/(task['id']+'.json');r=read(rp) if rp.exists() else dict(task=task,status='PENDING')
        if r['task']!=task:raise ValueError('probe receipt assignment changed')
        if r.get('path'):
            raw=inside(root,r['path']).read_bytes()
            if digest(raw)!=r['sha256']:raise ValueError('probe raw changed')
            try:inspection=inspect(raw,task,r['sha256'])
            except Exception as error:inspection=dict(status='PARSE_REVIEW_REQUIRED',reason=str(error),accepted=False)
            if inspection!=r['inspection']:raise ValueError('probe parser replay differs')
        receipts.append(r)
    status=dict(Counter(r['status'] for r in receipts));parsed=dict(Counter(r.get('inspection',{}).get('status','NOT_PARSED') for r in receipts))
    journal=out/'network/transport.jsonl';state=read_compact(journal.parent)['state'] if journal.exists() else contract['seed']
    ready=status.get('ACQUIRED')==180 and not parsed.get('PARSE_REVIEW_REQUIRED') and not parsed.get('EMPTY_PROVIDER_SERIES')
    summary=dict(status='TEMPLATE_PROBES_ACQUIRED_REVIEW_REQUIRED' if ready else 'PARTIAL_TEMPLATE_PROBES',tasks=180,
        task_statuses=status,inspection_statuses=parsed,candidate_cells=sum(r.get('inspection',{}).get('cell_count',0) for r in receipts),
        counters={k:v for k,v in state.items() if k not in ['requests','cache']},
        full_history_acquisition_allowed=False,numeric_acceptance_allowed=False,research_ready=False,
        next_action='REVIEW_OBSERVED_TEMPLATE_FAMILIES_AND_SUCCESSOR_HISTORY_CONTRACT')
    products={'summary.json':encoded(summary),'receipts.json':encoded(receipts),'contract-pin.json':encoded(dict(sha256=digest((out/'contract.json').read_bytes())))}
    manifest={n:digest(raw) for n,raw in products.items()};result=out/'results'/digest(encoded(manifest))[:20]
    if action=='verify':
        if read(result/'manifest.json')!=manifest:raise ValueError('probe snapshot differs')
        for n,sha in manifest.items():
            if digest((result/n).read_bytes())!=sha:raise ValueError('probe result changed')
    else:
        for n,raw in products.items():put(result/n,raw)
        put(result/'manifest.json',manifest)
    return dict(summary,output=result.relative_to(root).as_posix())
