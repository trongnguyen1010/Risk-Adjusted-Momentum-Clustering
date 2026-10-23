"""Fresh disjoint API waves: owner-approved 300 partitions, 0.4s, one worker."""
import copy,csv,io,re,time
from .financial_acquisition_bulk import CODE as BULK_CODE,boundaries,indexed_cache,collect,snapshot
from .financial_acquisition_batches import tasks
from .financial_history_documents import read,put
from .financial_history_batch import EvidenceIntegrityError
from .financial_user_workflow import exclusive
from ..ingestion.cafef_financial import digest
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_journal_stream import read_stream

CODE=BULK_CODE+['src/delta_t1/experiments/financial_acquisition_waves.py','scripts/financial_acquisition_waves.py']

def report_tasks(members):
    # Catalogue host remains latched; do not manufacture80 skipped receipts/member.
    return [t for t in tasks(members) if t['kind']=='REPORT']

def validate_assignment(rows,a):
    members=a['members'];previous=a['previous_members']
    if not 1<=len(members)<=300:raise ValueError('bounded wave1..300 required')
    all_members=members+previous
    if len({m['registry_id'] for m in all_members})!=len(all_members) or len({m['symbol'] for m in all_members})!=len(all_members):raise ValueError('duplicate or previously assigned partition')
    index={r['registry_id']:r for r in rows}
    if len(index)!=len(rows):raise ValueError('ambiguous registry')
    for m in all_members:
        r=index.get(m['registry_id'])
        if not r or (r['ticker'],r['exchange'],r['legacy_security_id'])!=(m['symbol'],m['exchange'],m['legacy_security_id']):raise ValueError('registry identity changed')
        if not re.fullmatch('[A-Z0-9]{3}',m['symbol']) or m['exchange'] not in ['HOSE','HNX','UPCOM']:raise ValueError('unsupported provider partition')
        if m['provider_partition_id']!='PROVISIONAL:CAFEF:'+m['registry_id'] or m['historical_identity_ready'] is not False:raise ValueError('identity promotion forbidden')
    return members

def validate_budget(c,s,n):
    if c['approved_hosts']!=['apiweb.cafef.vn'] or c['network_concurrency']!=1 or c['max_campaign_days']!=90:raise ValueError('source/concurrency changed')
    if c['years']!=list(range(2013,2026)) or c['auxiliary_balance_year']!=2012:raise ValueError('scope changed')
    if any(c.get(k) is not False for k in ['numeric_acceptance_allowed','financial_features_allowed','research_ready']):raise ValueError('candidate-only policy required')
    expected=dict(max_logical_requests=s['logical_requests']+140*n,max_transport_attempts=s['transport_attempts']+280*n,max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5000000,max_total_downloaded_bytes=s['downloaded_bytes']+2000000000,max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=.4)
    if c['budgets']!=expected:raise ValueError('unexpected inherited budget/rate')

def prepare(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c['version']!='financial-acquisition-waves-v1':raise ValueError('unknown wave version')
    def pin(p,sha=None):
        raw=inside(root,p).read_bytes();actual=digest(raw)
        if sha is not None and sha!=actual:raise ValueError('source changed: '+p)
        pins[p]=actual;return raw
    import json
    for p in CODE+[config_path]:pin(p)
    rows=list(csv.DictReader(io.StringIO(pin(c['registry']['path'],c['registry']['sha256']).decode('utf-8-sig'))))
    a=json.loads(pin(c['assignment']['path'],c['assignment']['sha256']))
    for item in a['evidence']:pin(item['path'],item['sha256'])
    members=validate_assignment(rows,a);jobs=report_tasks(members)
    gate=json.loads(pin(c['engineering_gate']['path'],c['engineering_gate']['sha256']))
    if gate.get('candidate_acquisition_allowed') is not True or not gate['checks'] or not all(gate['checks'].values()) or gate['approved_additional_partitions']!=len(members):raise ValueError('engineering gate held')
    for p,sha in gate['input_pins'].items():pin(p,sha)
    pin(c['parent_network']+'/transport.jsonl',c['parent_journal_sha256']);ledger=read_stream(inside(root,c['parent_network']));s=ledger['state']
    if ledger['torn_tail_bytes'] or s['boundary'] or s['budget_stop'] or s['reserved_bytes']:raise ValueError('unsafe parent counters')
    if {k:v for k,v in s.items() if k not in ['requests','cache']}!=gate['parent_counters']:raise ValueError('parent counters changed')
    validate_budget(c,s,len(members))
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True);cp=out/'contract.json'
    if cp.exists():
        contract=read(cp)
        if contract['pins']!=pins or contract['tasks']!=jobs:raise ValueError('frozen wave changed')
        for p,sha in contract['cache_pins'].items():pin(p,sha)
        for row in contract['boundaries']['records']:pin(row['path'],row['sha256'])
    else:
        imported=boundaries(root,c,out)
        if imported['errors']:raise ValueError('source boundary audit failed')
        base=dict(pins);cache,variants,stats=indexed_cache(root,out,{t['url'] for t in jobs if t['kind']=='REPORT'},pins)
        contract=dict(version=c['version'],pins=base,cache_pins={p:sha for p,sha in pins.items() if p not in base},tasks=jobs,cache=cache,cache_variants=variants,cache_inventory=stats,boundaries=imported,seed=copy.deepcopy(s),gate=gate)
        put(cp,contract);put(out/'assignment.json',a);put(out/'task-plan.json',jobs)
    return c,out,contract

def execute(root,config_path,action,network=False,max_new_requests=42000):
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=42000:raise ValueError('invalid wave action')
    c,out,contract=prepare(root,config_path)
    if network and (action!='run' or time.time()>=contract['seed']['created_at']+259200):raise ValueError('original deadline closed')
    journal=out/'network/transport.jsonl'
    if journal.exists():
        ledger=read_stream(journal.parent);s=ledger['state']
        if ledger['torn_tail_bytes'] or s['created_at']!=contract['seed']['created_at']:raise EvidenceIntegrityError('torn journal/anchor changed')
        if any(s['requests'].get(k)!=v for k,v in contract['seed']['requests'].items()):raise EvidenceIntegrityError('inherited request changed')
        if network and (s['boundary'] or s['budget_stop']):raise ValueError('source/budget latch remains closed')
    if action=='run':
        worker=inside(root,c['campaign_worker_root']);worker.mkdir(parents=True,exist_ok=True)
        with exclusive(worker):
            with exclusive(out):collect(root,c,out,contract,network,max_new_requests)
    return snapshot(root,c,out,contract,action)
