"""Versioned bounded API batches. Registry assignment never grants PIT or fact acceptance."""
from collections import Counter,defaultdict
import copy,csv,io,json,re,shutil,time
from urllib.parse import urlsplit
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from ..ingestion.cafef_financial_deep import report_url
from .financial_history_documents import read,put
from .financial_history_pit import GROUPS,audit_boundaries,csv_bytes
from .financial_history_batch import collect,parse_receipt,EvidenceIntegrityError
from .financial_user_workflow import exclusive

CODE=['src/delta_t1/experiments/financial_acquisition_batches.py','scripts/financial_acquisition_batches.py',
      'scripts/financial_acquisition_batches.ps1','src/delta_t1/experiments/financial_history_batch.py',
      'src/delta_t1/experiments/financial_template_candidates.py','src/delta_t1/experiments/financial_history_documents.py',
      'src/delta_t1/experiments/financial_history_pit.py','src/delta_t1/ingestion/financial_compact_trial.py',
      'src/delta_t1/ingestion/financial_trial_transport.py','src/delta_t1/experiments/financial_user_workflow.py',
      'src/delta_t1/ingestion/cafef_financial_deep.py','src/delta_t1/ingestion/financial_batch_evidence.py']


def validate_assignment(rows,assignment):
    members=assignment['members'];previous=assignment['previous_members']
    if not 1<=len(members)<=100:raise ValueError('batch must contain1..100 provider partitions')
    if len({m['registry_id'] for m in members})!=len(members) or len({m['symbol'] for m in members})!=len(members):
        raise ValueError('duplicate new provider assignment')
    if {m['registry_id'] for m in members}&{m['registry_id'] for m in previous} or {m['symbol'] for m in members}&{m['symbol'] for m in previous}:
        raise ValueError('already assigned partition')
    for m in members+previous:
        found=[r for r in rows if r['registry_id']==m['registry_id']]
        if len(found)!=1 or any(found[0][k]!=m[k] for k in ['exchange','legacy_security_id']) or found[0]['ticker']!=m['symbol']:
            raise ValueError('registry identity ambiguous or changed')
        if not re.fullmatch('[A-Z0-9]{3}',m['symbol']) or m['exchange'] not in ['HOSE','HNX','UPCOM']:
            raise ValueError('unsupported discovery candidate')
        if m['provider_partition_id']!='PROVISIONAL:CAFEF:'+m['registry_id'] or m['historical_identity_ready'] is not False:
            raise ValueError('canonical identity promotion forbidden')
    return members


def tasks(members):
    jobs=[]
    for m in members:
        for mode,pages in [('NAM',5),('QUY',15),('LUYKE',5)]:
            for statement,groups in GROUPS.items():
                if mode=='LUYKE' and statement=='CDKT':continue
                for group in groups:
                    for page in range(1,pages+1):
                        t=dict(kind='REPORT',registry_id=m['registry_id'],provider_partition_id=m['provider_partition_id'],symbol=m['symbol'],
                            statement=statement,mode=mode,group=group,page=page,series=':'.join([m['symbol'],statement,mode,group]))
                        t['url']=report_url(m['symbol'],statement,mode,group,page);t['id']=digest(t['url'].encode());jobs.append(t)
        for page in range(1,81):
            t=dict(kind='DISCLOSURE',registry_id=m['registry_id'],provider_partition_id=m['provider_partition_id'],symbol=m['symbol'],
                statement='DISCLOSURE',mode='CATALOGUE',group='CATALOGUE',page=page,series=m['symbol']+':DISCLOSURE',
                url='https://cafef.vn/du-lieu/ajax/ajaxcongbothongtin.ashx?symbol='+m['symbol']+'&pagesize=20&pageindex='+str(page))
            t['id']=digest(t['url'].encode());jobs.append(t)
    return sorted(jobs,key=lambda t:(t['page'],t['kind'],t['symbol'],t['mode'],t['statement'],t['group']))


def validate_budget(c,s,count):
    if c.get('approved_hosts')!=['apiweb.cafef.vn'] or c.get('network_concurrency')!=1 or c.get('max_campaign_days')!=90:
        raise ValueError('source/concurrency/campaign policy changed')
    if c.get('years')!=list(range(2013,2026)) or c.get('auxiliary_balance_year')!=2012:raise ValueError('history range changed')
    if any(c.get(k) is not False for k in ['numeric_acceptance_allowed','financial_features_allowed','research_ready']):raise ValueError('candidate-only policy required')
    caps=dict(max_logical_requests=s['logical_requests']+140*count,max_transport_attempts=s['transport_attempts']+280*count,
        max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5000000,
        max_total_downloaded_bytes=s['downloaded_bytes']+2000000000,max_wall_seconds=259200,
        max_attempts_per_request=2,timeout_seconds=20)
    if any(type(c['budgets'].get(k)) is not int or not 1<=c['budgets'][k]<=v for k,v in caps.items()):raise ValueError('invalid inherited budget')
    if c['budgets']['min_seconds_between_transport_attempts']<2:raise ValueError('spacing below policy')


def prepare(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-acquisition-batches-v1':raise ValueError('unknown version')
    def pin(path,sha=None):
        raw=inside(root,path).read_bytes();actual=digest(raw)
        if sha is not None and actual!=sha:raise ValueError('source pin changed: '+path)
        pins[path]=actual;return raw
    for p in CODE+[config_path]:pin(p)
    rows=list(csv.DictReader(io.StringIO(pin(c['registry']['path'],c['registry']['sha256']).decode('utf-8-sig'))))
    assignment=json.loads(pin(c['assignment']['path'],c['assignment']['sha256']))
    for item in assignment['evidence']:pin(item['path'],item['sha256'])
    members=validate_assignment(rows,assignment);jobs=tasks(members)
    gate=json.loads(pin(c['engineering_gate']['path'],c['engineering_gate']['sha256']))
    if gate.get('candidate_acquisition_allowed') is not True or not all(gate['checks'].values()):raise ValueError('engineering gate held')
    for path,sha in gate['input_pins'].items():pin(path,sha)
    if len(members)!=gate['approved_additional_partitions']:raise ValueError('assignment exceeds gate scope')
    pin(c['parent_network']+'/transport.jsonl',c['parent_journal_sha256'])
    ledger=read_compact(inside(root,c['parent_network']));s=ledger['state']
    if ledger['torn_tail_bytes'] or s['boundary'] or s['budget_stop']:raise ValueError('unsafe counter parent')
    validate_budget(c,s,len(members))
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True);cp=out/'contract.json'
    if cp.exists():
        contract=read(cp)
        if contract['pins']!=pins or contract['tasks']!=jobs:raise ValueError('frozen batch changed')
        for item in contract['boundaries']['records']:pin(item['path'],item['sha256'])
        for path,sha in contract['cache_pins'].items():pin(path,sha)
    else:
        boundaries=audit_boundaries(root,c,out)
        if boundaries['errors']:raise ValueError('boundary inventory errors')
        urls={t['url'] for t in jobs};variants=defaultdict(list);base_pins=dict(pins)
        for rp in sorted(inside(root,'data/financial').rglob('*.json')):
            if rp.is_relative_to(out) or not (rp.name.endswith('.receipt.json') or rp.parent.name=='receipts'):continue
            receipt=read(rp);task=receipt.get('task',{});record=receipt.get('record',receipt);url=task.get('url',receipt.get('url'))
            if url not in urls or receipt.get('status') not in [None,'ACQUIRED','CACHED_PROBE']:continue
            path=record.get('path');sha=record.get('sha256')
            if not path and receipt.get('name'):path=(rp.parent/receipt['name']).relative_to(root).as_posix()
            if not path or not sha:continue
            pin(path,sha);pin(rp.relative_to(root).as_posix())
            variants[url].append(dict(path=path,sha256=sha,receipt=rp.relative_to(root).as_posix(),provenance='EXACT_URL_CACHE_UNVERIFIED_VINTAGE'))
        contract=dict(version=c['version'],pins=base_pins,cache_pins={k:v for k,v in pins.items() if k not in base_pins},tasks=jobs,
            cache={url:items[0] for url,items in sorted(variants.items())},cache_variants=dict(variants),boundaries=boundaries,
            seed=copy.deepcopy(s),gate=gate)
        put(cp,contract);put(out/'task-plan.json',jobs);put(out/'assignment.json',assignment)
    return c,out,contract

def snapshot(root,c,out,contract,action):
    statuses=Counter();mappings=Counter();index=defaultdict(list);shards=[];errors=[];receipt_pins={};pending_series=set();cells=0
    for task in contract['tasks']:
        rp=out/'receipts'/(task['id']+'.json');r=read(rp) if rp.exists() else dict(task=task,status='PENDING')
        if r['task']!=task:raise ValueError('snapshot receipt assignment differs')
        statuses[r['status']]+=1
        if rp.exists():receipt_pins[rp.relative_to(out).as_posix()]=digest(rp.read_bytes())
        if r['status']=='PENDING':pending_series.add(task['series'])
        if not r.get('record'):continue
        try:rows=parse_receipt(root,r)
        except (ValueError,KeyError,TypeError) as error:
            errors.append(dict(task=task,reason=str(error)));continue
        cells+=len(rows);mappings.update(row['mapping_status'] for row in rows)
        body=b''.join((json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode() for row in rows)
        path=out/'candidates'/(task['id']+'.jsonl')
        if action=='verify':
            if not path.exists() or path.read_bytes()!=body:raise ValueError('history candidate shard differs')
        else:put(path,body)
        shards.append(dict(path=path.relative_to(root).as_posix(),sha256=digest(body),cells=len(rows),task_id=task['id']))
        for row in rows:
            if row['value_status']=='NUMERIC_CANDIDATE':index[(row['symbol'],row['statement'],row['mode'],row['year'],row['quarter'])].append(row)
    coverage=[]
    for symbol in sorted({t['symbol'] for t in contract['tasks']}):
        for year in c['years']:
            for mode,quarters in [('NAM',[0]),('QUY',[1,2,3,4])]:
                for quarter in quarters:
                    for statement,groups in GROUPS.items():
                        found=index.get((symbol,statement,mode,year,quarter),[]);observed=sorted({r['group'] for r in found})
                        complete=all(':'.join([symbol,statement,mode,g]) not in pending_series for g in groups)
                        status='CANDIDATE_GROUPS_PRESENT' if set(observed)>=set(groups) else 'PARTIAL_CANDIDATE_GROUPS' if found else 'NO_CANDIDATE_IN_ACQUIRED_PAGES'
                        coverage.append(dict(symbol=symbol,year=year,quarter=quarter,mode=mode,statement=statement,status=status,
                            observed_groups=observed,numeric_cells=len(found),unique_code_label_cells=sum(r['mapping_status']=='UNIQUE_CODE_LABEL_CANDIDATE' for r in found),
                            task_accounting_complete=complete,accepted=False,pit_ready=False))
        found=index.get((symbol,'CDKT','NAM',2012,0),[])
        coverage.append(dict(symbol=symbol,year=2012,quarter=0,mode='NAM',statement='CDKT',status='AUXILIARY_CANDIDATES_PRESENT' if found else 'AUXILIARY_NOT_ACQUIRED',
            observed_groups=sorted({r['group'] for r in found}),numeric_cells=len(found),unique_code_label_cells=sum(r['mapping_status']=='UNIQUE_CODE_LABEL_CANDIDATE' for r in found),
            task_accounting_complete=all(':'.join([symbol,'CDKT','NAM',g]) not in pending_series for g in GROUPS['CDKT']),accepted=False,pit_ready=False))
    journal=out/'network/transport.jsonl';ledger=read_compact(journal.parent) if journal.exists() else None
    if ledger and ledger['torn_tail_bytes']:raise ValueError('torn F3 journal')
    state=ledger['state'] if ledger else contract['seed']
    summary=dict(stage=c['batch_id'],status='COMPLETE_CANDIDATE_TASK_ACCOUNTING' if not statuses['PENDING'] else 'PARTIAL_CANDIDATE_ACQUISITION',
        tasks=len(contract['tasks']),task_statuses=dict(statuses),candidate_cells=cells,mapping_statuses=dict(mappings),parser_errors=len(errors),
        candidate_coverage_slots=len(coverage),coverage_statuses=dict(Counter(r['status'] for r in coverage)),
        counters={k:v for k,v in state.items() if k not in ['requests','cache']},
        accepted_new_facts=0,numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False,next50_allowed=False,
        acquisition_scope='Bounded provider partitions; previous runs immutable; no numeric/PIT promotion',
        reference_delivery='PARTIAL_ACCEPTED_DEPENDENCIES_REQUIRED',pit_delivery='PARTIAL_PUBLICATION_SCOPE_IDENTITY_REQUIRED')
    products={'summary.json':encoded(summary),'candidate-shards.json':encoded(shards),'parser-errors.json':encoded(errors),
        'receipt-pins.json':encoded(receipt_pins),'gate.json':encoded(contract['gate']),
        'financial_coverage.csv':csv_bytes(coverage,list(coverage[0])),
        'contract-pin.json':encoded(dict(sha256=digest((out/'contract.json').read_bytes())))}
    m={name:digest(raw) for name,raw in products.items()};result=out/'results'/digest(encoded(m))[:20]
    if action=='verify':
        if read(result/'manifest.json')!=m:raise ValueError('F3 snapshot manifest differs')
        for name,sha in m.items():
            if digest((result/name).read_bytes())!=sha:raise ValueError('F3 snapshot changed')
    else:
        for name,raw in products.items():put(result/name,raw)
        put(result/'manifest.json',m)
    return dict(summary,output=result.relative_to(root).as_posix())




def execute(root,config_path,action,network=False,max_new_requests=200):
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=14000:
        raise ValueError('invalid acquisition action/wave')
    c,out,contract=prepare(root,config_path)
    if network and (action!='run' or time.time()>=contract['seed']['created_at']+259200):raise ValueError('original campaign/batch deadline closed')
    journal=out/'network/transport.jsonl'
    if journal.exists():
        ledger=read_compact(journal.parent);state=ledger['state']
        if ledger['torn_tail_bytes']:raise EvidenceIntegrityError('torn F3 journal requires explicit review')
        if state['created_at']!=contract['seed']['created_at']:raise EvidenceIntegrityError('F3 anchor changed')
        if any(state['requests'].get(k)!=v for k,v in contract['seed']['requests'].items()):
            raise EvidenceIntegrityError('F3 inherited requests changed')
        if network and (state['boundary'] or state['budget_stop']):raise ValueError('F3 source/budget latch remains closed')
    if action=='run':
        worker=inside(root,c['campaign_worker_root']);worker.mkdir(parents=True,exist_ok=True)
        with exclusive(worker):
            with exclusive(out):collect(root,c,out,contract,network,max_new_requests)
    return snapshot(root,c,out,contract,action)
