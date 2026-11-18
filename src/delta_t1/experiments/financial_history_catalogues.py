"""Bounded public HTML catalogues; no PDF download or publication acceptance."""
from collections import Counter
import copy,json,re,time,shutil

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_history_documents import DocumentTransport,read,put
from .financial_history_pit import audit_boundaries
from .financial_user_workflow import exclusive

CODE=['src/delta_t1/experiments/financial_history_catalogues.py','scripts/financial_history_catalogues.py',
      'scripts/financial_history_catalogues.ps1','src/delta_t1/experiments/financial_history_documents.py',
      'src/delta_t1/experiments/financial_history_pit.py','src/delta_t1/ingestion/financial_compact_trial.py',
      'src/delta_t1/ingestion/financial_trial_transport.py','src/delta_t1/ingestion/financial_batch_evidence.py',
      'src/delta_t1/experiments/financial_user_workflow.py']


def jobs(assignment):
    members=assignment['members']
    if len(members)!=15 or len({m['registry_id'] for m in members})!=15 or len({m['symbol'] for m in members})!=15:
        raise ValueError('exact additional15 financial assignment required')
    result=[]
    for member in members:
        if not re.fullmatch('[A-Z0-9]{2,8}',member['symbol']):raise ValueError('invalid catalogue provider symbol')
        url='https://web.stockbiz.vn/Stocks/'+member['symbol']+'/Downloads.aspx'
        result.append(dict(member=member,url=url,id=digest(url.encode()),route_status='KNOWN_PUBLIC_HTML_ROUTE_PATTERN_NOT_GUESSED_PDF_FILENAME'))
    return sorted(result,key=lambda x:x['member']['registry_id'])


def prepare(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-history-catalogues-v1' or c.get('approved_hosts')!=['web.stockbiz.vn']:
        raise ValueError('bounded public HTML catalogue contract required')
    if c.get('network_concurrency')!=1 or c.get('max_campaign_days')!=90:raise ValueError('single worker/original deadline policy required')
    if any(c.get(k) is not False for k in ['numeric_acceptance_allowed','publication_acceptance_allowed','research_ready']):
        raise ValueError('catalogue collection cannot accept numbers/publication/PIT')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and expected!=sha:raise ValueError('catalogue prerequisite changed: '+path)
        pins[path]=sha;return body
    for p in CODE+[config_path]:pin(p)
    a=c['assignment'];assignment=json.loads(pin(a['path'],a['sha256']));tasks=jobs(assignment)
    evidence=json.loads(pin(c['route_evidence']['path'],c['route_evidence']['sha256']))
    if evidence['source']!='https://web.stockbiz.vn/Stocks/FPT/Downloads.aspx':raise ValueError('observed public route evidence differs')
    result=c['acquisition_result'];manifest=json.loads(pin(result['path']+'/manifest.json',result['manifest_sha256']))
    summary=json.loads(pin(result['path']+'/summary.json',manifest['summary.json']))
    if summary['tasks']!=3300 or summary['task_statuses'].get('PENDING',0) or summary['parser_errors']:
        raise ValueError('history acquisition must be terminal with accounted tasks')
    parent=inside(root,c['parent_network']);pin(c['parent_network']+'/transport.jsonl',c['parent_journal_sha256']);old=read_compact(parent);s=old['state']
    if old['torn_tail_bytes'] or s['boundary'] or s['budget_stop']:raise ValueError('unsafe catalogue counter parent')
    caps=dict(max_logical_requests=s['logical_requests']+15,max_transport_attempts=s['transport_attempts']+30,
        max_pdf_download_attempts=s['pdf_download_attempts'],max_response_bytes=5_000_000,max_total_downloaded_bytes=s['downloaded_bytes']+75_000_000,
        max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20)
    if any(type(c['budgets'].get(k)) is not int or not 1<=c['budgets'][k]<=cap for k,cap in caps.items()) or c['budgets']['min_seconds_between_transport_attempts']<2:
        raise ValueError('invalid finite catalogue budgets')
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True)
    if (out/'contract.json').exists():
        contract=read(out/'contract.json')
        if contract['pins']!=pins or contract['jobs']!=tasks:raise ValueError('frozen catalogue contract changed')
        for r in contract['boundaries']['records']:pin(r['path'],r['sha256'])
    else:
        boundaries=audit_boundaries(root,dict(boundary_roots=c['boundary_roots']),out)
        if boundaries['errors']:raise ValueError('catalogue boundary inventory failed')
        contract=dict(version=c['version'],pins=pins,jobs=tasks,boundaries=boundaries,seed=copy.deepcopy(s));put(out/'contract.json',contract)
    return c,out,contract


def execute(root,config_path,action,network=False,max_new_requests=15):
    if action not in ['plan','run','verify'] or type(max_new_requests) is not int or not 0<=max_new_requests<=15:
        raise ValueError('invalid catalogue action/wave')
    c,out,contract=prepare(root,config_path);journal=out/'network/transport.jsonl'
    state=read_compact(journal.parent)['state'] if journal.exists() else contract['seed']
    if state['created_at']!=contract['seed']['created_at'] or any(state['requests'].get(k)!=v for k,v in contract['seed']['requests'].items()):
        raise ValueError('catalogue inherited anchor/requests changed')
    if network:
        if action!='run' or state['boundary'] or state['budget_stop'] or time.time()>=state['created_at']+259200:
            raise ValueError('catalogue source/budget/deadline remains closed')
        if shutil.disk_usage(root).free<30_000_000_000:raise ValueError('DISK_FLOOR')
        worker=inside(root,c['campaign_worker_root']);worker.mkdir(parents=True,exist_ok=True)
        with exclusive(worker):
            with exclusive(out):
                transport=None;used=0
                for job in contract['jobs']:
                    rp=out/'receipts'/(job['id']+'.json')
                    if rp.exists():continue
                    if 'web.stockbiz.vn' in contract['boundaries']['blocked_hosts']:
                        put(rp,dict(job=job,status='IMPORTED_SOURCE_BOUNDARY'));continue
                    if used>=max_new_requests:break
                    if transport is None:transport=DocumentTransport(root,out/'network',c,contract['seed'])
                    if any(r['url']==job['url'] for r in transport.state['requests'].values()):raise ValueError('interrupted catalogue request without receipt requires review')
                    transport.context=dict(kind='structured',symbol=job['member']['symbol'],report='PUBLIC_FINANCIAL_DOCUMENT_CATALOGUE')
                    try:
                        body,http=transport.get(job['url']);sha=digest(body);p=out/'raw'/(sha+'.html');put(p,body)
                        put(rp,dict(job=job,status='ACQUIRED',path=p.relative_to(root).as_posix(),sha256=sha,bytes=len(body),http_status=http))
                    except Exception as error:
                        put(rp,dict(job=job,status='FAILED_OR_STOPPED',reason=str(error)))
                        if transport.state['boundary'] or transport.state['budget_stop']:break
                    used+=1
    receipts=[]
    for job in contract['jobs']:
        rp=out/'receipts'/(job['id']+'.json');r=read(rp) if rp.exists() else dict(job=job,status='PENDING')
        if r['job']!=job:raise ValueError('catalogue assignment changed')
        if r.get('path') and digest(inside(root,r['path']).read_bytes())!=r['sha256']:raise ValueError('catalogue raw changed')
        receipts.append(r)
    ledger=read_compact(journal.parent) if journal.exists() else None
    if ledger and ledger['torn_tail_bytes']:raise ValueError('torn catalogue journal requires review')
    state=ledger['state'] if ledger else contract['seed'];statuses=dict(Counter(r['status'] for r in receipts))
    summary=dict(status='HTML_CATALOGUES_ACQUIRED_SEMANTICS_PENDING' if statuses.get('ACQUIRED')==15 else 'PARTIAL_CATALOGUES',jobs=15,task_statuses=statuses,
        counters={k:v for k,v in state.items() if k not in ['requests','cache']},new_pdf_downloads=0,new_ocr_pages=0,
        numeric_acceptance_allowed=False,publication_acceptance_allowed=False,research_ready=False)
    products={'summary.json':encoded(summary),'receipts.json':encoded(receipts),'contract-pin.json':encoded(dict(sha256=digest((out/'contract.json').read_bytes())))}
    m={name:digest(body) for name,body in products.items()};result=out/'results'/digest(encoded(m))[:20]
    if action=='verify':
        if read(result/'manifest.json')!=m:raise ValueError('catalogue snapshot differs')
        for name,sha in m.items():
            if digest((result/name).read_bytes())!=sha:raise ValueError('catalogue output changed')
    else:
        for name,body in products.items():put(result/name,body)
        put(result/'manifest.json',m)
    return dict(summary,output=result.relative_to(root).as_posix())
