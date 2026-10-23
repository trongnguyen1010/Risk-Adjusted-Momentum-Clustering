"""Owner-approved0.4s/300-member checkpoint successor; no network parallelism."""
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
import copy,csv,io,json,os,shutil,time
from pathlib import Path
from urllib.parse import urlsplit
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_journal_stream import read_stream as read_compact,StreamingTransport
from .financial_history_documents import read,put
from .financial_history_pit import GROUPS,page_state,csv_bytes
from .financial_history_batch import parse_receipt,EvidenceIntegrityError
from .financial_acquisition_batches import tasks as make_tasks
from .financial_acquisition_rate1 import prior_request_allowed,verify_inheritance
from .financial_user_workflow import exclusive
CODE=['src/delta_t1/experiments/financial_acquisition_bulk.py','scripts/financial_acquisition_bulk.py','scripts/financial_acquisition_bulk.ps1',
      'src/delta_t1/ingestion/financial_journal_stream.py','src/delta_t1/ingestion/financial_compact_trial.py',
      'src/delta_t1/ingestion/financial_trial_transport.py','src/delta_t1/experiments/financial_acquisition_rate1.py',
      'src/delta_t1/experiments/financial_acquisition_batches.py','src/delta_t1/experiments/financial_history_batch.py',
      'src/delta_t1/experiments/financial_template_candidates.py','src/delta_t1/experiments/financial_history_pit.py',
      'src/delta_t1/experiments/financial_user_workflow.py']


def validate_policy(c,old,added):
    if c['budgets']['min_seconds_between_transport_attempts']!=0.4 or c['network_concurrency']!=1 or c.get('local_io_workers')!=8:
        raise ValueError('approved0.4second/one-network-worker policy required')
    if not 0<=added<=200:raise ValueError('at most200 additional partitions')
    expected=dict(old['budgets']);expected.update(min_seconds_between_transport_attempts=0.4,
        max_logical_requests=old['budgets']['max_logical_requests']+140*added,
        max_transport_attempts=old['budgets']['max_transport_attempts']+280*added,
        max_total_downloaded_bytes=old['budgets']['max_total_downloaded_bytes']+(2000000000 if added else 0))
    if c['budgets']!=expected:raise ValueError('unexpected budget/deadline change')
    for key in ['years','auxiliary_balance_year','approved_hosts','max_campaign_days','cache_epoch','boundary_roots','numeric_acceptance_allowed','financial_features_allowed','research_ready']:
        if c.get(key)!=old.get(key):raise ValueError('source/scope/acceptance changed: '+key)


def validate_members(registry,assignment,source_assignment):
    members=assignment['members'];prior=assignment['previous_members'];old=source_assignment['members']
    if not 1<=len(members)<=300 or len(members)>len(old)+200:raise ValueError('bounded300-member wave required')
    if prior!=source_assignment['previous_members']:raise ValueError('completed membership changed')
    ids={m['registry_id'] for m in members};previous_ids={m['registry_id'] for m in prior}
    if len(ids)!=len(members) or len({m['symbol'] for m in members})!=len(members) or ids&previous_ids:raise ValueError('duplicate/reassigned identity')
    if {m['symbol'] for m in members}&{m['symbol'] for m in prior}:raise ValueError('ambiguous provider ticker reuse')
    index={row['registry_id']:row for row in registry}
    if len(index)!=len(registry):raise ValueError('ambiguous registry')
    for m in members+prior:
        row=index.get(m['registry_id'])
        if not row or (row['ticker'],row['exchange'],row['legacy_security_id'])!=(m['symbol'],m['exchange'],m['legacy_security_id']):raise ValueError('registry join changed')
        if m['historical_identity_ready'] is not False or m['provider_partition_id']!='PROVISIONAL:CAFEF:'+m['registry_id']:raise ValueError('canonical identity promotion forbidden')
    by_id={m['registry_id']:m for m in members}
    if any(by_id.get(m['registry_id'])!=m for m in old):raise ValueError('checkpoint membership changed')
    return len(members)-len(old)


def boundaries(root,c,out):
    records=[];errors=[];journals=set()
    for relative in c['boundary_roots']:journals.update(inside(root,relative).rglob('transport.jsonl'))
    for path in sorted(journals):
        if path.is_relative_to(out):continue
        try:
            with path.open('rb') as f:first=json.loads(f.readline())
            if 'index' in first:
                ledger=read_compact(path.parent)
                if ledger['torn_tail_bytes']:raise ValueError('torn imported journal')
                state=ledger['state'];requests=list(state.get('requests',{}).values());sha=ledger['prefix_sha256']
            else:
                raw=path.read_bytes()
                if not raw.endswith(b'\n'):raise ValueError('torn imported journal')
                events=[json.loads(line) for line in raw.splitlines()];state=events[-1]['state'];requests=[e.get('data',{}).get('request',{}) for e in events];sha=digest(raw)
            if type(state.get('boundary')) is not bool:raise ValueError('unknown boundary schema')
            hosts=sorted({urlsplit(q['url']).hostname for q in requests[-1:] if q.get('url')})
            if state['boundary'] and not hosts:raise ValueError('unattributable source latch')
            records.append(dict(path=path.relative_to(root).as_posix(),sha256=sha,boundary=state['boundary'],hosts=hosts if state['boundary'] else [],reason=state.get('stop_reason'),counters={k:state.get(k) for k in ['created_at','logical_requests','transport_attempts','attempts','downloaded_bytes','bytes_read','budget_stop']}))
        except (ValueError,KeyError,TypeError) as error:errors.append(dict(path=path.relative_to(root).as_posix(),error=str(error)))
    return dict(records=records,errors=errors,blocked_hosts=sorted({h for row in records if row['boundary'] for h in row['hosts']}))


def load_receipt(root,path):
    raw=path.read_bytes();r=json.loads(raw);return path,raw,r


def indexed_cache(root,out,urls,pins):
    targets=[];indexed=set();contracts=0
    # Query immutable task plans first; do not open every unrelated historical receipt.
    for cp in sorted(inside(root,'data/financial').rglob('contract.json')):
        if cp.is_relative_to(out):continue
        raw=cp.read_bytes();contract=json.loads(raw);jobs=contract.get('tasks')
        if not isinstance(jobs,list) or not all(isinstance(t,dict) and 'url' in t and 'id' in t for t in jobs):continue
        indexed.add(cp.parent/'receipts');pins[cp.relative_to(root).as_posix()]=digest(raw);contracts+=1
        targets.extend(cp.parent/'receipts'/(t['id']+'.json') for t in jobs if t['url'] in urls and (cp.parent/'receipts'/(t['id']+'.json')).exists())
    for path in inside(root,'data/financial').rglob('*.json'):
        if path.is_relative_to(out):continue
        if path.name.endswith('.receipt.json') or (path.parent.name=='receipts' and path.parent not in indexed):targets.append(path)
    variants=defaultdict(list)
    with ThreadPoolExecutor(max_workers=8) as pool:
        for rp,raw,r in pool.map(lambda p:load_receipt(root,p),sorted(set(targets))):
            task=r.get('task',{});rec=r.get('record',r);url=task.get('url',r.get('url'))
            if url not in urls or r.get('status') not in [None,'ACQUIRED','CACHED_PROBE']:continue
            path=rec.get('path');sha=rec.get('sha256')
            if not path and r.get('name'):path=(rp.parent/r['name']).relative_to(root).as_posix()
            if not path or not sha:continue
            body=inside(root,path).read_bytes()
            if digest(body)!=sha:raise ValueError('cache raw hash differs')
            pins[path]=sha;pins[rp.relative_to(root).as_posix()]=digest(raw)
            variants[url].append(dict(path=path,sha256=sha,receipt=rp.relative_to(root).as_posix(),provenance='INDEXED_EXACT_URL_CACHE_UNVERIFIED_VINTAGE'))
    return {url:rows[0] for url,rows in sorted(variants.items())},dict(variants),dict(contracts_indexed=contracts,receipt_candidates_opened=len(set(targets)),matched_urls=len(variants))


def prepare(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-acquisition-bulk-v1':raise ValueError('unknown bulk version')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('source pin changed: '+path)
        pins[path]=sha;return raw
    for p in CODE+[config_path]:pin(p)
    old=json.loads(pin(c['checkpoint_config']['path'],c['checkpoint_config']['sha256']))
    h=json.loads(pin(c['handoff']['path'],c['handoff']['sha256']))
    if h['status']!='STOPPED_AT_UNATTEMPTED_RESERVATION':raise ValueError('unsafe handoff')
    source=json.loads(pin(old['output_root']+'/contract.json',h['source_contract_sha256']))
    for path,sha in source['pins'].items():pin(path,sha)
    source_assignment=json.loads(pin(old['output_root']+'/assignment.json'))
    assignment=json.loads(pin(c['assignment']['path'],c['assignment']['sha256']))
    registry=list(csv.DictReader(io.StringIO(pin(c['registry']['path'],c['registry']['sha256']).decode('utf-8-sig'))))
    added=validate_members(registry,assignment,source_assignment);validate_policy(c,old,added)
    parent=old['output_root']+'/network';pin(parent+'/transport.jsonl',h['journal_sha256']);ledger=read_compact(inside(root,parent));seed=ledger['state'];key=h['reserved_request_key']
    if ledger['torn_tail_bytes'] or seed['boundary'] or seed['budget_stop'] or seed['reserved_bytes']:raise ValueError('unsafe source journal')
    reserved=seed['requests'].get(key)
    if not reserved or reserved['attempts']!=0 or reserved['kind']!='structured' or reserved['url']!=c['authorized_unattempted_url']:raise ValueError('only proved unattempted reservation may migrate')
    jobs=make_tasks(assignment['members']);expected={t['id']:t for t in jobs}
    if any(expected.get(t['id'])!=t for t in source['tasks']):raise ValueError('checkpoint tasks altered')
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True);receipts={};source_paths={}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for rp,raw,r in pool.map(lambda p:load_receipt(root,p),sorted((inside(root,old['output_root'])/'receipts').glob('*.json'))):
            task=r['task'];tid=task['id']
            if expected.get(tid)!=task or rp.name!=tid+'.json':raise ValueError('source receipt differs')
            pins[rp.relative_to(root).as_posix()]=digest(raw);receipts[task['url']]=r;source_paths[tid]=rp
            if r.get('record'):pin(r['record']['path'],r['record']['sha256'])
    old_urls={t['url'] for t in source['tasks']};unfinished=[q for q in seed['requests'].values() if q['url'] in old_urls and q['url'] not in receipts]
    if unfinished!=[reserved]:raise ValueError('other unreceipted request requires review')
    cp=out/'contract.json'
    if cp.exists():
        contract=read(cp)
        if contract['pins']!=pins or contract['tasks']!=jobs:raise ValueError('frozen bulk successor changed')
        for path,sha in contract['cache_pins'].items():pin(path,sha)
        for row in contract['boundaries']['records']:pin(row['path'],row['sha256'])
    else:
        imported=boundaries(root,c,out)
        if imported['errors']:raise ValueError('source boundary audit failed')
        base=dict(pins);new_urls={t['url'] for t in jobs if t['kind']=='REPORT'}-old_urls
        cache,variants,stats=indexed_cache(root,out,new_urls,pins)
        contract=dict(version=c['version'],pins=base,cache_pins={p:sha for p,sha in pins.items() if p not in base},tasks=jobs,
            cache=cache,cache_variants=variants,cache_inventory=stats,boundaries=imported,seed=copy.deepcopy(seed),gate=dict(status='OWNER_APPROVED_RATE_AND_WAVE_EXPANSION',reserved_request_key=key,added_members=added,numeric_acceptance_allowed=False))
        put(cp,contract);put(out/'assignment.json',assignment);put(out/'task-plan.json',jobs)
        for tid,rp in source_paths.items():
            target=out/'receipts'/(tid+'.json');target.parent.mkdir(exist_ok=True)
            if target.exists():
                if target.read_bytes()!=rp.read_bytes():raise ValueError('imported receipt differs')
            else:
                try:os.link(rp,target)
                except OSError:put(target,rp.read_bytes())
    return c,out,contract


def collect(root,c,out,contract,network,max_new_requests,transport_factory=StreamingTransport):
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





def snapshot(root,c,out,contract,action):
    statuses=Counter();mappings=Counter();index=defaultdict(lambda:dict(numeric_cells=0,unique=0,groups=set()));shards=[];errors=[];receipt_pins={};pending_series=set();cells=0
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
            if row['value_status']=='NUMERIC_CANDIDATE':
                item=index[(row['symbol'],row['statement'],row['mode'],row['year'],row['quarter'])];item['numeric_cells']+=1;item['unique']+=row['mapping_status']=='UNIQUE_CODE_LABEL_CANDIDATE';item['groups'].add(row['group'])
    coverage=[]
    for symbol in sorted({t['symbol'] for t in contract['tasks']}):
        for year in c['years']:
            for mode,quarters in [('NAM',[0]),('QUY',[1,2,3,4])]:
                for quarter in quarters:
                    for statement,groups in GROUPS.items():
                        found=index.get((symbol,statement,mode,year,quarter),dict(numeric_cells=0,unique=0,groups=set()));observed=sorted(found['groups'])
                        complete=all(':'.join([symbol,statement,mode,g]) not in pending_series for g in groups)
                        status='CANDIDATE_GROUPS_PRESENT' if set(observed)>=set(groups) else 'PARTIAL_CANDIDATE_GROUPS' if found['numeric_cells'] else 'NO_CANDIDATE_IN_ACQUIRED_PAGES'
                        coverage.append(dict(symbol=symbol,year=year,quarter=quarter,mode=mode,statement=statement,status=status,
                            observed_groups=observed,numeric_cells=found['numeric_cells'],unique_code_label_cells=found['unique'],
                            task_accounting_complete=complete,accepted=False,pit_ready=False))
        found=index.get((symbol,'CDKT','NAM',2012,0),dict(numeric_cells=0,unique=0,groups=set()))
        coverage.append(dict(symbol=symbol,year=2012,quarter=0,mode='NAM',statement='CDKT',status='AUXILIARY_CANDIDATES_PRESENT' if found['numeric_cells'] else 'AUXILIARY_NOT_ACQUIRED',
            observed_groups=sorted(found['groups']),numeric_cells=found['numeric_cells'],unique_code_label_cells=found['unique'],
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






def execute(root,config_path,action,network=False,max_new_requests=42000):
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=42000:raise ValueError('invalid bulk action/wave')
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
