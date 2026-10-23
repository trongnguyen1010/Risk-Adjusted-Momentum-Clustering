"""F3 history successor: cache-aware candidate acquisition, never numeric acceptance."""
from collections import Counter,defaultdict
import copy,json,shutil,time
from urllib.parse import urlsplit

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.cafef_financial_deep import report_url
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_history_documents import DocumentTransport,read,put
from .financial_history_pit import GROUPS,audit_boundaries,page_state,csv_bytes
from .financial_history20_profiles import run as profiles_run
from .financial_history_stage_gate import run as pilot_gate_run
from .financial_template_candidates import run as adapter_run,parse_candidates
from .financial_user_workflow import exclusive

CODE=['src/delta_t1/experiments/financial_history_batch.py','scripts/financial_history_batch.py',
      'scripts/financial_history_batch.ps1','src/delta_t1/experiments/financial_template_candidates.py',
      'scripts/financial_template_candidates.py','src/delta_t1/experiments/financial_history20_profiles.py',
      'scripts/financial_history20_profiles.py','src/delta_t1/experiments/financial_history_stage_gate.py',
      'scripts/financial_history_stage_gate.py','src/delta_t1/experiments/financial_history_documents.py',
      'src/delta_t1/experiments/financial_history_pit.py','src/delta_t1/ingestion/cafef_financial_deep.py',
      'src/delta_t1/ingestion/financial_compact_trial.py','src/delta_t1/ingestion/financial_trial_transport.py',
      'src/delta_t1/ingestion/financial_batch_evidence.py','src/delta_t1/experiments/financial_user_workflow.py']


class EvidenceIntegrityError(RuntimeError):
    pass


def tasks(members):
    if len(members)!=15 or len({m['registry_id'] for m in members})!=15 or len({m['symbol'] for m in members})!=15:
        raise ValueError('F3 requires exactly fifteen additional provider partitions')
    rows=[]
    for m in members:
        for mode,pages in [('NAM',5),('QUY',15),('LUYKE',5)]:
            for statement,groups in GROUPS.items():
                if mode=='LUYKE' and statement=='CDKT':continue
                for group in groups:
                    for page in range(1,pages+1):
                        t=dict(kind='REPORT',registry_id=m['registry_id'],provider_partition_id=m['provider_partition_id'],
                            symbol=m['symbol'],statement=statement,mode=mode,group=group,page=page,
                            series=':'.join([m['symbol'],statement,mode,group]))
                        t['url']=report_url(m['symbol'],statement,mode,group,page);t['id']=digest(t['url'].encode());rows.append(t)
        # The original catalogue host remains latched. Account its planned work explicitly.
        for page in range(1,81):
            t=dict(kind='DISCLOSURE',registry_id=m['registry_id'],provider_partition_id=m['provider_partition_id'],
                symbol=m['symbol'],statement='DISCLOSURE',mode='CATALOGUE',group='CATALOGUE',page=page,
                series=m['symbol']+':DISCLOSURE',url='https://cafef.vn/du-lieu/ajax/ajaxcongbothongtin.ashx?symbol='+m['symbol']+'&pagesize=20&pageindex='+str(page))
            t['id']=digest(t['url'].encode());rows.append(t)
    return sorted(rows,key=lambda t:(t['page'],t['kind'],t['symbol'],t['mode'],t['statement'],t['group']))


def decide_gate(pilot,profiles,adapter,catalogue,quarantine):
    """Current adapter gate is distinct from the frozen strict-parser result."""
    by_type=defaultdict(set);types={r['symbol']:r['proposed_company_type'] for r in profiles}
    for r in catalogue:
        if r['task']['statement']=='KQKD':by_type[types[r['task']['symbol']]].update(r['template_sha256'])
    disjoint=all(not by_type[a]&by_type[b] for a in by_type for b in by_type if a!=b)
    counts_ok=all(type(adapter.get(k)) is int and adapter[k]>=0 for k in
                  ['tasks','parsed_tasks','parser_errors','quarantined_cells','original_strict_parser_review_tasks'])
    checks=dict(nonnegative_counts=counts_ok,pilot_engineering=pilot['pilot_history_engineering_pass'],
        profile_identity=len(profiles)==15 and all(r['status']=='CURRENT_PROFILE_OBSERVED' for r in profiles),
        three_exchanges=len({r['exchange'] for r in profiles})==3,
        observed_institution_template_diversity=set(by_type)=={'Regular','Bank','Securities'} and disjoint and all(by_type.values()),
        all_probe_tasks_parsed=adapter['tasks']==180 and adapter['parsed_tasks']==180,
        current_parser_rate=counts_ok and adapter['parser_errors']/adapter['parsed_tasks']<=.01 if adapter['parsed_tasks'] else False,
        quarantine_complete=len(quarantine)==adapter['quarantined_cells'] and all(not r['accepted'] and not r['pit_ready'] for r in quarantine),
        no_numeric_promotion=not adapter['numeric_acceptance_allowed'] and not adapter['research_ready'])
    return dict(status='PASS_BOUNDED_HISTORY_CANDIDATES' if all(checks.values()) else 'HOLD_HISTORY_CANDIDATES',checks=checks,
        candidate_acquisition_allowed=all(checks.values()),original_strict_parser_review_tasks=adapter['original_strict_parser_review_tasks'],
        parser_version='financial-template-candidates-v1',numeric_acceptance_allowed=False,research_ready=False,
        scope='F3 additional15 history candidates only; no numeric/PIT/identity promotion')


def prepare(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-history-batch-f3-v1' or c.get('approved_hosts')!=['apiweb.cafef.vn']:
        raise ValueError('bounded F3 API-only successor required')
    if c.get('years')!=list(range(2013,2026)) or c.get('auxiliary_balance_year')!=2012:
        raise ValueError('exact financial history range required')
    if c.get('network_concurrency')!=1 or c.get('max_campaign_days')!=90:raise ValueError('single worker and original campaign policy required')
    if any(c.get(k) is not False for k in ['numeric_acceptance_allowed','financial_features_allowed','research_ready','next50_allowed']):
        raise ValueError('F3 acquisition cannot promote downstream gates')
    def pin(path,sha=None):
        raw=inside(root,path).read_bytes();actual=digest(raw)
        if sha is not None and actual!=sha:raise ValueError('F3 evidence changed: '+path)
        pins[path]=actual;return raw
    for path in CODE+[config_path]:pin(path)
    outputs={}
    for name,runner in [('pilot_gate',pilot_gate_run),('profiles',profiles_run),('adapter',adapter_run)]:
        item=c[name];pin(item['config'],item['config_sha256']);result=runner(root,item['config'],'verify')
        if result['output']!=item['result']:raise ValueError('F3 gate input result differs: '+name)
        outputs[name]=result
        manifest=json.loads(pin(item['result']+'/manifest.json',item['manifest_sha256']))
        for file,sha in manifest.items():pin(item['result']+'/'+file,sha)
    profiles=read(inside(root,c['profiles']['result']+'/profiles.json'))
    profile_config=read(inside(root,c['profiles']['config']))
    metadata_contract=read(inside(root,profile_config['metadata_root']+'/contract.json'))
    registry=c['registry'];pin(registry['path'],registry['sha256'])
    if metadata_contract['pins'].get(registry['path'])!=registry['sha256']:raise ValueError('F3 registry differs from profile selection')
    legacy=c['existing_pilot5_result'];lm=json.loads(pin(legacy['path']+'/manifest.json',legacy['manifest_sha256']))
    pin(legacy['path']+'/summary.json',lm['summary.json'])
    adapter_path=c['adapter']['result'];catalogue=read(inside(root,adapter_path+'/template-catalogue.json'))
    quarantine=read(inside(root,adapter_path+'/quarantine.json'))
    gate=decide_gate(outputs['pilot_gate'],profiles,outputs['adapter'],catalogue,quarantine)
    if not gate['candidate_acquisition_allowed']:raise ValueError('F3 adapter/template gate closed')
    source=c['probes'];m=json.loads(pin(source['result']+'/manifest.json',source['manifest_sha256']))
    receipts=json.loads(pin(source['result']+'/receipts.json',m['receipts.json']));cache={}
    if len(receipts)!=180 or any(r['status']!='ACQUIRED' for r in receipts):raise ValueError('complete page1 probe cache required')
    for r in receipts:
        if r['task']['url'] in cache:raise ValueError('duplicate probe URL')
        pin(r['path'],r['sha256']);cache[r['task']['url']]=dict(path=r['path'],sha256=r['sha256'],provenance='FROZEN_TEMPLATE_PROBE')
    parent=inside(root,c['parent_network']);pin(c['parent_network']+'/transport.jsonl',c['parent_journal_sha256'])
    old=read_compact(parent);s=old['state']
    if old['torn_tail_bytes'] or s['boundary'] or s['budget_stop']:raise ValueError('unsafe F3 counter parent')
    limits=dict(max_logical_requests=s['logical_requests']+2100,max_transport_attempts=s['transport_attempts']+4200,
                max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5_000_000,
                max_total_downloaded_bytes=s['downloaded_bytes']+2_000_000_000,max_wall_seconds=259200,
                max_attempts_per_request=2,timeout_seconds=20)
    b=c['budgets']
    if any(type(b.get(k)) is not int or not 1<=b[k]<=cap for k,cap in limits.items()) or b['min_seconds_between_transport_attempts']<2:
        raise ValueError('invalid F3 history budget')
    jobs=tasks(profiles);out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True);cp=out/'contract.json'
    if cp.exists():
        contract=read(cp)
        if contract['pins']!=pins or contract['tasks']!=jobs or contract['cache']!=cache:raise ValueError('frozen F3 successor changed')
        for item in contract['boundaries']['records']:pin(item['path'],item['sha256'])
    else:
        boundaries=audit_boundaries(root,dict(boundary_roots=c['boundary_roots']),out)
        if boundaries['errors']:raise ValueError('F3 source boundary inventory errors')
        contract=dict(version=c['version'],pins=dict(pins),tasks=jobs,cache=cache,boundaries=boundaries,gate=gate,seed=copy.deepcopy(s))
        put(cp,contract);put(out/'task-plan.json',jobs)
        put(out/'assignment.json',dict(domain='FINANCIAL_HISTORY_CANDIDATES',batch_id=c['batch_id'],owner=c['owner'],
            members=[dict(registry_id=r['registry_id'],symbol=r['symbol'],provider_partition_id=r['provider_partition_id']) for r in profiles],
            registry=c['registry'],years=c['years'],auxiliary_balance_year=2012,existing_pilot5_result=c['existing_pilot5_result'],
            historical_identity_ready=False,financial_features_allowed=False))
    return c,out,contract


def parse_receipt(root,r):
    record=r['record'];raw=inside(root,record['path']).read_bytes()
    if digest(raw)!=record['sha256']:raise EvidenceIntegrityError('history raw source changed')
    return parse_candidates(raw,r['task'],record['path'],record['sha256'])


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
                if any(q['url']==task['url'] for q in transport.state['requests'].values()):
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
    summary=dict(stage='F3_ADDITIONAL15_HISTORY_CANDIDATES',status='COMPLETE_CANDIDATE_TASK_ACCOUNTING' if not statuses['PENDING'] else 'PARTIAL_CANDIDATE_ACQUISITION',
        tasks=len(contract['tasks']),task_statuses=dict(statuses),candidate_cells=cells,mapping_statuses=dict(mappings),parser_errors=len(errors),
        candidate_coverage_slots=len(coverage),coverage_statuses=dict(Counter(r['status'] for r in coverage)),
        counters={k:v for k,v in state.items() if k not in ['requests','cache']},
        accepted_new_facts=0,numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False,next50_allowed=False,
        acquisition_scope='Additional15 only; existing pilot5 history remains separate immutable input',
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
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=2100:
        raise ValueError('invalid F3 action/wave')
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
