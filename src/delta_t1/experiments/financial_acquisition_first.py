"""Acquisition-first successor. Review backlog never accepts candidate values."""
from collections import Counter,defaultdict
import copy,csv,io,json,re,time
from urllib.parse import urlsplit
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_history_documents import read,put
from .financial_history_pit import audit_boundaries,csv_bytes,GROUPS
from .financial_history_batch import tasks as old_tasks,collect,parse_receipt,EvidenceIntegrityError
from .financial_user_workflow import exclusive

CODE=['src/delta_t1/experiments/financial_acquisition_first.py','scripts/financial_acquisition_first.py',
      'scripts/financial_acquisition_first.ps1','src/delta_t1/experiments/financial_history_batch.py',
      'src/delta_t1/experiments/financial_template_candidates.py','src/delta_t1/experiments/financial_history_documents.py',
      'src/delta_t1/experiments/financial_history_pit.py','src/delta_t1/ingestion/financial_compact_trial.py',
      'src/delta_t1/ingestion/financial_trial_transport.py','src/delta_t1/experiments/financial_user_workflow.py',
      'src/delta_t1/ingestion/cafef_financial_deep.py','src/delta_t1/ingestion/financial_batch_evidence.py']


def select_members(rows,legacy,existing):
    pool=[]
    for m in legacy:
        if m['ticker'] in existing:continue
        found=[r for r in rows if (r['ticker'],r['exchange'],r['legacy_security_id']) ==
               (m['ticker'],m['exchange'],m['security_id'])]
        if len(found)!=1:raise ValueError('ambiguous provisional registry join: '+m['ticker'])
        row=found[0]
        if not re.fullmatch('[A-Z0-9]{2,8}',row['ticker']):raise ValueError('invalid ticker')
        pool.append(dict(registry_id=row['registry_id'],symbol=row['ticker'],exchange=row['exchange'],
            company_name=row['company_name'],provider_partition_id='PROVISIONAL:CAFEF:'+row['registry_id'],
            historical_identity_ready=False,classification_status='UNVERIFIED_NOT_USED_FOR_SCORE_MAPPING'))
    pool.sort(key=lambda r:r['registry_id'])
    if len(pool)<30:raise ValueError('insufficient additional registry partitions')
    selected=pool[:30]
    if len({r['registry_id'] for r in selected})!=30 or len({r['symbol'] for r in selected})!=30:
        raise ValueError('duplicate assignment')
    return selected,pool[30:]


def validate_budget(c,s):
    if c.get('approved_hosts')!=['apiweb.cafef.vn'] or c.get('network_concurrency')!=1 or c.get('max_campaign_days')!=90:
        raise ValueError('source/concurrency/campaign policy changed')
    if c.get('years')!=list(range(2013,2026)) or c.get('auxiliary_balance_year')!=2012:
        raise ValueError('history range changed')
    if any(c.get(k) is not False for k in ['numeric_acceptance_allowed','financial_features_allowed','research_ready','next50_allowed']):
        raise ValueError('candidate-only policy required')
    caps=dict(max_logical_requests=s['logical_requests']+4200,max_transport_attempts=s['transport_attempts']+8400,
        max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5000000,
        max_total_downloaded_bytes=s['downloaded_bytes']+2000000000,max_wall_seconds=259200,
        max_attempts_per_request=2,timeout_seconds=20)
    if any(type(c['budgets'].get(k)) is not int or not 1<=c['budgets'][k]<=v for k,v in caps.items()):
        raise ValueError('acquisition budget cannot reset/increase original policy')
    if c['budgets']['min_seconds_between_transport_attempts']<2:raise ValueError('spacing below policy')


def prepare(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-acquisition-first-v1':raise ValueError('unknown version')
    def pin(path,sha=None):
        raw=inside(root,path).read_bytes();actual=digest(raw)
        if sha is not None and actual!=sha:raise ValueError('source pin changed: '+path)
        pins[path]=actual;return raw
    for p in CODE+[config_path]:pin(p)
    rows=list(csv.DictReader(io.StringIO(pin(c['registry']['path'],c['registry']['sha256']).decode('utf-8-sig'))))
    legacy=json.loads(pin(c['legacy_plan']['path'],c['legacy_plan']['sha256']))['members']
    profiles=json.loads(pin(c['previous_profiles']['path'],c['previous_profiles']['sha256']))
    existing={'BRC','FPT','MWG','GMD','VNM'}|{r['symbol'] for r in profiles}
    if len(existing)!=20:raise ValueError('previous20 mismatch')
    members,deferred=select_members(rows,legacy,existing)
    gate=json.loads(pin(c['engineering_gate']['path'],c['engineering_gate']['sha256']))
    previous=json.loads(pin(c['previous_summary']['path'],c['previous_summary']['sha256']))
    qa=json.loads(pin(c['previous_qa']['path'],c['previous_qa']['sha256']))
    if not gate['pilot_history_engineering_pass'] or previous['task_statuses'].get('PENDING',0) or previous['parser_errors'] or qa['acquisition_parser_errors']:
        raise ValueError('engineering source gate closed')
    pin(c['review_backlog']['path'],c['review_backlog']['sha256'])
    pin(c['parent_network']+'/transport.jsonl',c['parent_journal_sha256'])
    ledger=read_compact(inside(root,c['parent_network']));s=ledger['state']
    if ledger['torn_tail_bytes'] or s['boundary'] or s['budget_stop']:raise ValueError('unsafe counter parent')
    validate_budget(c,s)
    jobs=old_tasks(members[:15])+old_tasks(members[15:])
    jobs.sort(key=lambda t:(t['page'],t['kind'],t['symbol'],t['mode'],t['statement'],t['group']))
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True)
    cp=out/'contract.json'
    if cp.exists():
        contract=read(cp)
        if contract['pins']!=pins or contract['tasks']!=jobs:raise ValueError('frozen acquisition successor changed')
        for item in contract['boundaries']['records']:pin(item['path'],item['sha256'])
        for path,sha in contract['cache_pins'].items():pin(path,sha)
    else:
        boundaries=audit_boundaries(root,c,out)
        if boundaries['errors']:raise ValueError('boundary inventory errors')
        urls={t['url'] for t in jobs};variants=defaultdict(list);base_pins=dict(pins)
        # Inventory exact URL receipts before any request; conflicting vintages are retained separately.
        for rp in sorted(inside(root,'data/financial').rglob('*.json')):
            if rp.is_relative_to(out) or not (rp.name.endswith('.receipt.json') or rp.parent.name=='receipts'):continue
            receipt=read(rp);task=receipt.get('task',{});record=receipt.get('record',receipt)
            url=task.get('url',receipt.get('url'))
            if url not in urls or receipt.get('status') not in [None,'ACQUIRED','CACHED_PROBE']:continue
            path=record.get('path');sha=record.get('sha256')
            if not path and receipt.get('name'):path=(rp.parent/receipt['name']).relative_to(root).as_posix()
            if not path or not sha:continue
            pin(path,sha);pin(rp.relative_to(root).as_posix())
            variants[url].append(dict(path=path,sha256=sha,receipt=rp.relative_to(root).as_posix(),provenance='EXACT_URL_CACHE_UNVERIFIED_VINTAGE'))
        cache={url:items[0] for url,items in sorted(variants.items())}
        contract=dict(version=c['version'],pins=base_pins,cache_pins={k:v for k,v in pins.items() if k not in base_pins},tasks=jobs,cache=cache,cache_variants=dict(variants),
            boundaries=boundaries,seed=copy.deepcopy(s),gate=dict(status='PASS_ACQUISITION_ONLY_OWNER_RESEQUENCING',
            previous_full_F3_delivery='PARTIAL',review_backlog=c['review_backlog'],numeric_acceptance_allowed=False,research_ready=False))
        put(cp,contract);put(out/'task-plan.json',jobs)
        put(out/'assignment.json',dict(domain='FINANCIAL_API_CANDIDATES_ONLY',batch_id=c['batch_id'],owner=c['owner'],
            members=members,deferred=deferred,previous_symbols=sorted(existing),registry=c['registry'],years=c['years'],
            auxiliary_balance_year=2012,identity_scope='PROVISIONAL_PROVIDER_PARTITIONS_NOT_HISTORICAL_MEMBERSHIP',
            numeric_acceptance_allowed=False,pit_ready=False))
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
    summary=dict(stage='ACQUISITION_FIRST_ADDITIONAL30',status='COMPLETE_CANDIDATE_TASK_ACCOUNTING' if not statuses['PENDING'] else 'PARTIAL_CANDIDATE_ACQUISITION',
        tasks=len(contract['tasks']),task_statuses=dict(statuses),candidate_cells=cells,mapping_statuses=dict(mappings),parser_errors=len(errors),
        candidate_coverage_slots=len(coverage),coverage_statuses=dict(Counter(r['status'] for r in coverage)),
        counters={k:v for k,v in state.items() if k not in ['requests','cache']},
        accepted_new_facts=0,numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False,next50_allowed=False,
        acquisition_scope='Additional30 provisional provider partitions only; previous20 immutable; no numeric/PIT promotion',
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
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=4200:
        raise ValueError('invalid acquisition action/wave')
    c,out,contract=prepare(root,config_path)
    if network and (action!='run' or time.time()>=contract['seed']['created_at']+259200):raise ValueError('original F3 deadline closed')
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
