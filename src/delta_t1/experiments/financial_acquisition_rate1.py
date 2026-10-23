"""Single-worker 1s successor, migrating only a proved unattempted reservation."""
from collections import defaultdict
import copy,json,shutil,time
from urllib.parse import urlsplit
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_history_documents import DocumentTransport,read,put
from .financial_history_pit import audit_boundaries,page_state
from .financial_history_batch import parse_receipt,EvidenceIntegrityError
from .financial_acquisition_batches import snapshot
from .financial_user_workflow import exclusive
CODE=['src/delta_t1/experiments/financial_acquisition_rate1.py','scripts/financial_acquisition_rate1.py',
      'scripts/financial_acquisition_rate1.ps1','src/delta_t1/experiments/financial_history_batch.py',
      'src/delta_t1/experiments/financial_acquisition_batches.py','src/delta_t1/experiments/financial_history_documents.py',
      'src/delta_t1/experiments/financial_template_candidates.py','src/delta_t1/experiments/financial_history_pit.py',
      'src/delta_t1/ingestion/financial_compact_trial.py','src/delta_t1/ingestion/financial_trial_transport.py',
      'src/delta_t1/experiments/financial_user_workflow.py']


def validate_policy(c,old):
    if c['budgets']['min_seconds_between_transport_attempts']!=1 or c['network_concurrency']!=1:
        raise ValueError('only single worker 1second policy approved')
    for key,value in old['budgets'].items():
        if key!='min_seconds_between_transport_attempts' and c['budgets'].get(key)!=value:raise ValueError('budget/deadline reset forbidden')
    for key in ['years','auxiliary_balance_year','approved_hosts','max_campaign_days','cache_epoch','numeric_acceptance_allowed','financial_features_allowed','research_ready']:
        if c.get(key)!=old.get(key):raise ValueError('checkpoint source/scope/policy changed: '+key)


def prior_request_allowed(c,task,prior):
    if not prior:return True
    return len(prior)==1 and task['url']==c['authorized_unattempted_url'] and prior[0]['attempts']==0 and prior[0]['kind']=='structured'


def verify_inheritance(state,seed,key):
    if state['created_at']!=seed['created_at']:raise ValueError('original anchor changed')
    for k,v in seed['requests'].items():
        current=state['requests'].get(k)
        if k==key:
            if not current or v['attempts']!=0 or not 0<=current['attempts']<=2 or dict(current,attempts=0)!=v:
                raise ValueError('reserved request identity/attempts changed')
        elif current!=v:raise ValueError('inherited completed request changed')


def prepare(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-acquisition-rate1-v1':raise ValueError('unknown rate successor')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('source pin changed: '+path)
        pins[path]=sha;return raw
    for path in CODE+[config_path]:pin(path)
    old=json.loads(pin(c['checkpoint_config']['path'],c['checkpoint_config']['sha256']));validate_policy(c,old)
    handoff=json.loads(pin(c['handoff']['path'],c['handoff']['sha256']))
    if handoff['status']!='STOPPED_AT_UNATTEMPTED_RESERVATION':raise ValueError('unsafe handoff')
    contract_path=old['output_root']+'/contract.json';source=json.loads(pin(contract_path,handoff['source_contract_sha256']))
    for path,sha in source['pins'].items():pin(path,sha)
    parent=old['output_root']+'/network';pin(parent+'/transport.jsonl',handoff['journal_sha256'])
    ledger=read_compact(inside(root,parent));seed=ledger['state'];key=handoff['reserved_request_key']
    if ledger['torn_tail_bytes'] or seed['boundary'] or seed['budget_stop'] or seed['reserved_bytes']:
        raise ValueError('unsafe source journal')
    reserved=seed['requests'].get(key)
    if not reserved or reserved['attempts']!=0 or reserved['kind']!='structured' or reserved['url']!=c['authorized_unattempted_url']:
        raise ValueError('only explicit unattempted reservation may migrate')
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True);jobs=source['tasks'];expected={t['id']:t for t in jobs};receipts={}
    for rp in sorted((inside(root,old['output_root'])/'receipts').glob('*.json')):
        relative=rp.relative_to(root).as_posix();raw=pin(relative);record=json.loads(raw);task=record['task']
        if expected.get(task['id'])!=task or rp.name!=task['id']+'.json':raise ValueError('source receipt differs')
        if record.get('record'):pin(record['record']['path'],record['record']['sha256'])
        receipts[task['url']]=raw
    job_urls={t['url'] for t in jobs}
    unfinished=[v for v in seed['requests'].values() if v['url'] in job_urls and v['url'] not in receipts]
    if unfinished!=[reserved]:raise ValueError('unexpected other unreceipted request; review required')
    cp=out/'contract.json'
    if cp.exists():
        contract=read(cp)
        if contract['pins']!=pins or contract['tasks']!=jobs:raise ValueError('frozen rate successor changed')
        for item in contract['boundaries']['records']:pin(item['path'],item['sha256'])
    else:
        boundaries=audit_boundaries(root,c,out)
        if boundaries['errors']:raise ValueError('boundary inventory failed')
        contract=dict(version=c['version'],pins=dict(pins),tasks=jobs,cache={},boundaries=boundaries,seed=copy.deepcopy(seed),
            gate=dict(status='RATE_ONLY_HANDOFF_NOT_NUMERIC_ACCEPTANCE',source_contract=contract_path,reserved_request_key=key))
        put(cp,contract);put(out/'task-plan.json',jobs);put(out/'assignment.json',read(inside(root,old['output_root']+'/assignment.json')))
        for task in jobs:
            if task['url'] in receipts:put(out/'receipts'/(task['id']+'.json'),receipts[task['url']])
    return c,out,contract

def collect(root,c,out,contract,network,max_new_requests,transport_factory=DocumentTransport):
    """Reconstruct pagination on resume; never retry an unreceipted request."""
    histories=defaultdict(list);stopped=set();transport=None;used=0
    for task in contract['tasks']:
        rp=out/'receipts'/(task['id']+'.json');r=read(rp) if rp.exists() else None
        if r is None:
            if task['series'] in stopped:r=dict(task=task,status='NOT_REQUIRED_AFTER_SERIES_STOP')
            elif task['page']>1 and len(histories[task['series']])!=task['page']-1:continue
            elif task['url'] in contract['cache']:r=dict(task=task,status='CACHED_PROBE',record=contract['cache'][task['url']])
            elif urlsplit(task['url']).hostname in contract['boundaries']['blocked_hosts']:r=dict(task=task,status='IMPORTED_SOURCE_BOUNDARY')
            elif not network or used>=max_new_requests:continue
            elif task['kind']!='REPORT':raise ValueError('catalogue network is outside F3 API-only scope')
            else:
                if transport is None:
                    if shutil.disk_usage(root).free<30_000_000_000:raise ValueError('DISK_FLOOR')
                    transport=transport_factory(root,out/'network',c,contract['seed'])
                if not prior_request_allowed(c,task,[q for q in transport.state['requests'].values() if q['url']==task['url']]):
                    raise ValueError('interrupted history request without receipt; explicit review required')
                transport.context=dict(kind='structured',symbol=task['symbol'],report=task['statement'],page=task['page'])
                try:
                    raw,http_status=transport.get(task['url']);sha=digest(raw);path=out/'raw'/(sha+'.json');put(path,raw)
                    r=dict(task=task,status='ACQUIRED',record=dict(path=path.relative_to(root).as_posix(),sha256=sha,http_status=http_status))
                except Exception as error:
                    r=dict(task=task,status='FAILED_OR_STOPPED',reason=str(error))
                used+=1
                if used%50==0:print(json.dumps(dict(event='F3_NETWORK_CHECKPOINT',new_requests=used,last_symbol=task['symbol'],page=task['page'])),flush=True)
            put(rp,r)
        if r['task']!=task:raise ValueError('history receipt task changed')
        if r.get('record'):
            try:
                rows=parse_receipt(root,r);state=page_state(task,rows,histories[task['series']]);histories[task['series']].append(state)
                if state['stop']:stopped.add(task['series'])
            except (ValueError,KeyError,TypeError):stopped.add(task['series'])
        elif r['status']!='NOT_REQUIRED_AFTER_SERIES_STOP':stopped.add(task['series'])
        if transport and (transport.state['boundary'] or transport.state['budget_stop']):break
    return used



def execute(root,config_path,action,network=False,max_new_requests=14000):
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=14000:raise ValueError('invalid action/wave')
    c,out,contract=prepare(root,config_path)
    if network and (action!='run' or time.time()>=contract['seed']['created_at']+259200):raise ValueError('original deadline closed')
    journal=out/'network/transport.jsonl'
    if journal.exists():
        ledger=read_compact(journal.parent)
        if ledger['torn_tail_bytes']:raise EvidenceIntegrityError('torn journal')
        verify_inheritance(ledger['state'],contract['seed'],contract['gate']['reserved_request_key'])
        if network and (ledger['state']['boundary'] or ledger['state']['budget_stop']):raise ValueError('source/budget latch remains closed')
    if action=='run':
        worker=inside(root,c['campaign_worker_root']);worker.mkdir(parents=True,exist_ok=True)
        with exclusive(worker):
            with exclusive(out):collect(root,c,out,contract,network,max_new_requests)
    return snapshot(root,c,out,contract,action)
