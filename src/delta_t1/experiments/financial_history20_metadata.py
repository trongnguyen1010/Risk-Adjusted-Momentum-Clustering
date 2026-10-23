"""Bounded current-profile acquisition for choosing the next history stage."""
from collections import Counter
import copy,csv,json,re
from urllib.parse import urlsplit

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_history_documents import DocumentTransport,read,put
from .financial_history_pit import audit_boundaries,PILOT
from .financial_history_stage_gate import run as gate_run
from .financial_user_workflow import exclusive

CODE=['src/delta_t1/experiments/financial_history20_metadata.py','scripts/financial_history20_metadata.py',
      'src/delta_t1/experiments/financial_history_documents.py','src/delta_t1/experiments/financial_history_stage_gate.py',
      'scripts/financial_history_stage_gate.py','src/delta_t1/ingestion/financial_compact_trial.py',
      'src/delta_t1/ingestion/financial_trial_transport.py','src/delta_t1/ingestion/financial_batch_evidence.py',
      'src/delta_t1/experiments/financial_user_workflow.py']


def select_members(rows,legacy,quotas,existing):
    if len(existing)!=5 or len(set(existing))!=5:raise ValueError('five fixed controls required')
    existing_rows=[r for r in rows if r['ticker'] in existing]
    if len(existing_rows)!=5 or any(r['exchange']!='HOSE' for r in existing_rows):raise ValueError('ambiguous pilot registry identity')
    pool=[]
    for member in legacy:
        if member['ticker'] in existing:continue
        # The provisional legacy identity, exchange and ticker must all join.
        found=[r for r in rows if (r['ticker'],r['exchange'],r['legacy_security_id'])==(member['ticker'],member['exchange'],member['security_id'])]
        if len(found)==1:pool.append((found[0],member))
    selected=[];seen=set()
    for quota in quotas:
        choices=sorted([(r,m) for r,m in pool if r['registry_id'] not in seen and r['exchange']==quota['exchange'] and m['proposed_company_type']==quota['proposed_company_type']],key=lambda item:item[0]['registry_id'])
        if type(quota['count']) is not int or quota['count']<1 or len(choices)<quota['count']:raise ValueError('insufficient evidenced selection stratum')
        for row,member in choices[:quota['count']]:
            seen.add(row['registry_id']);symbol=row['ticker']
            if not re.fullmatch('[A-Z0-9]{2,8}',symbol):raise ValueError('invalid provider symbol')
            selected.append(dict(registry_id=row['registry_id'],symbol=symbol,exchange=row['exchange'],company_name=row['company_name'],
                legacy_security_id=row['legacy_security_id'],provider_partition_id='PROVISIONAL:CAFEF:'+row['registry_id'],
                issuer_id=row['issuer_id'],security_id=row['security_id'],identity_status=row['identity_status'],
                proposed_company_type=member['proposed_company_type'],classification_status='LEGACY_PROPOSAL_PROFILE_AND_API_CHECK_REQUIRED',
                market_universe_role='CURRENT_ENGINEERING_SAMPLE_NOT_HISTORICAL_MEMBERSHIP',
                target_start='2013-01-01',target_end='2025-12-31',auxiliary_balance_year=2012,
                profile_url='https://web.stockbiz.vn/Stocks/'+symbol+'/Overview.aspx'))
    if len(selected)!=15 or len(seen)!=15 or len({r['symbol'] for r in selected})!=15:raise ValueError('exactly fifteen distinct additional securities required')
    return sorted(selected,key=lambda r:r['registry_id'])


def prepare(root,config_path):
    c=read(inside(root,config_path))
    if c.get('version')!='financial-history20-metadata-v1' or c['approved_hosts']!=['web.stockbiz.vn']:
        raise ValueError('bounded current-profile source contract required')
    if c.get('existing_symbols')!=PILOT or c.get('network_concurrency')!=1 or c.get('max_campaign_days')!=90:
        raise ValueError('fixed controls, one worker and original campaign policy required')
    for key in ['financial_features_allowed','research_ready','numeric_acceptance_allowed']:
        if c.get(key) is not False:raise ValueError('metadata cannot open numerical/research gates')
    pins={p:digest(inside(root,p).read_bytes()) for p in CODE+[config_path]}
    def pinned(item):
        raw=inside(root,item['path']).read_bytes()
        if digest(raw)!=item['sha256']:raise ValueError('metadata selection input changed')
        pins[item['path']]=item['sha256'];return raw
    rows=list(csv.DictReader(pinned(c['registry']).decode('utf-8-sig').splitlines()))
    legacy=json.loads(pinned(c['legacy_plan']))['members']
    members=select_members(rows,legacy,c['quotas'],c['existing_symbols'])
    gate_config=pinned(c['gate_config'])
    gate=gate_run(root,c['gate_config']['path'],'verify')
    if gate['output']!=c['gate_result'] or not gate['pilot_history_engineering_pass']:raise ValueError('pilot gate not passed')
    parent=inside(root,c['parent_network'])
    if digest((parent/'transport.jsonl').read_bytes())!=c['parent_journal_sha256']:raise ValueError('parent counter journal changed')
    seed=read_compact(parent)
    if seed['torn_tail_bytes'] or seed['state']['boundary'] or seed['state']['budget_stop']:raise ValueError('unsafe metadata counter parent')
    b=c['budgets'];s=seed['state']
    caps=dict(max_logical_requests=s['logical_requests']+15,max_transport_attempts=s['transport_attempts']+30,
              max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5_000_000,
              max_total_downloaded_bytes=s['downloaded_bytes']+75_000_000,max_wall_seconds=259200,
              max_attempts_per_request=2,timeout_seconds=20)
    if any(type(b.get(k)) is not int or b[k]<1 or b[k]>cap for k,cap in caps.items()) or b['min_seconds_between_transport_attempts']<2:
        raise ValueError('invalid bounded profile budgets')
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True)
    if (out/'contract.json').exists():
        contract=read(out/'contract.json')
        if contract['pins']!=pins or contract['members']!=members:raise ValueError('frozen metadata inputs/code changed')
        for record in contract['boundaries']['records']:
            if digest(inside(root,record['path']).read_bytes())!=record['sha256']:raise ValueError('imported source boundary changed')
    else:
        boundaries=audit_boundaries(root,dict(boundary_roots=c['boundary_roots']),out)
        if boundaries['errors']:raise ValueError('metadata boundary inventory errors')
        contract=dict(version=c['version'],pins=pins,members=members,boundaries=boundaries,seed=copy.deepcopy(s),
                      gate_result=c['gate_result'],existing_symbols=c['existing_symbols'])
        put(out/'contract.json',contract)
        put(out/'assignment.json',dict(domain='FINANCIAL_CURRENT_PROFILE_AND_SOURCE_PROBES',owner=c['owner'],batch_id='financial-history-total20-metadata-v1',
            registry=c['registry'],new_members=members,existing_symbols=c['existing_symbols'],financial_years=list(range(2013,2026)),
            auxiliary_balance_year=2012,identity_scope='PROVISIONAL_PROVIDER_PARTITIONS',historical_identity_ready=False,numeric_acceptance_allowed=False))
    return c,out,contract,gate


def execute(root,config_path,action,network=False,max_new_requests=15):
    if action not in ['plan','run','verify']:raise ValueError('unknown metadata action')
    if type(max_new_requests) is not int or not 0<=max_new_requests<=15:raise ValueError('metadata wave must be0..15')
    c,out,contract,gate=prepare(root,config_path)
    if network and (action!='run' or not gate['bounded_candidate_extension_eligible']):raise ValueError('live candidate extension gate closed')
    if network:
        with exclusive(inside(root,c['campaign_worker_root'])):
            with exclusive(out):
                transport=None;used=0
                for member in contract['members']:
                    url=member['profile_url'];rid=digest(url.encode());rp=out/'receipts'/(rid+'.json')
                    if rp.exists():continue
                    if urlsplit(url).hostname in contract['boundaries']['blocked_hosts']:
                        put(rp,dict(member=member,status='IMPORTED_SOURCE_BOUNDARY'));continue
                    if used>=max_new_requests:break
                    if transport is None:transport=DocumentTransport(root,out/'network',c,contract['seed'])
                    if any(r['url']==url for r in transport.state['requests'].values()):raise ValueError('interrupted profile request without receipt; explicit review required')
                    transport.context=dict(kind='structured',symbol=member['symbol'],report='CURRENT_COMPANY_PROFILE')
                    try:
                        body,status=transport.get(url);raw=out/'raw'/(digest(body)+'.html');put(raw,body)
                        put(rp,dict(member=member,status='ACQUIRED',path=raw.relative_to(root).as_posix(),sha256=digest(body),bytes=len(body),http_status=status))
                    except Exception as error:
                        put(rp,dict(member=member,status='FAILED_OR_STOPPED',reason=str(error)))
                        if transport.state['boundary'] or transport.state['budget_stop']:break
                    used+=1
    receipts=[]
    for member in contract['members']:
        p=out/'receipts'/(digest(member['profile_url'].encode())+'.json')
        receipt=read(p) if p.exists() else dict(member=member,status='PENDING')
        if receipt.get('path') and digest(inside(root,receipt['path']).read_bytes())!=receipt['sha256']:raise ValueError('raw profile changed')
        receipts.append(receipt)
    statuses=dict(Counter(r['status'] for r in receipts));network_path=out/'network/transport.jsonl'
    state=read_compact(network_path.parent)['state'] if network_path.exists() else contract['seed']
    counters={k:v for k,v in state.items() if k not in ['requests','cache']}
    summary=dict(status='ACQUIRED_CURRENT_PROFILES_ONLY' if statuses.get('ACQUIRED')==15 else 'PARTIAL',
                 new_profile_tasks=15,total_next_stage_issuers=20,task_statuses=statuses,counters=counters,
                 profile_semantics_status='OFFLINE_PROFILE_PARSE_REQUIRED',historical_identity_ready=False,
                 numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False)
    products={'summary.json':encoded(summary),'receipts.json':encoded(receipts),'contract-pin.json':encoded(dict(sha256=digest((out/'contract.json').read_bytes())))}
    manifest={name:digest(raw) for name,raw in products.items()};result=out/'results'/digest(encoded(manifest))[:20]
    if action=='verify':
        if read(result/'manifest.json')!=manifest:raise ValueError('metadata snapshot differs')
        for name,sha in manifest.items():
            if digest((result/name).read_bytes())!=sha:raise ValueError('metadata artifact changed')
    else:
        for name,raw in products.items():put(result/name,raw)
        put(result/'manifest.json',manifest)
    return dict(summary,output=result.relative_to(root).as_posix())
