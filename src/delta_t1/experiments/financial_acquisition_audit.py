"""Streaming acquisition replay/audit; semantic PDF/ratio validation remains deferred."""
from collections import Counter
import csv,io,json
from pathlib import Path
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put
from .financial_template_candidates import parse_candidates
from .financial_history_qa import structural_header
CODE=['src/delta_t1/experiments/financial_acquisition_audit.py','scripts/financial_acquisition_audit.py',
      'src/delta_t1/experiments/financial_template_candidates.py','src/delta_t1/experiments/financial_history_qa.py']


def classify(row,payload):
    if row.get('accepted') or row.get('pit_ready'):raise ValueError('candidate promotion forbidden')
    if row['value_status'] in ['INVALID_NUMERIC_QUARANTINED','BOOLEAN_QUARANTINED']:return 'INVALID_NUMERIC'
    if structural_header(row,payload):return 'PROVEN_STRUCTURAL_HEADER_ZERO'
    if row['mapping_status']!='UNIQUE_CODE_LABEL_CANDIDATE':return 'UNRESOLVED_MAPPING'
    return 'UNIQUE_CODE_LABEL_CANDIDATE'


def replay(body,task,record,shard):
    if digest(body)!=record['sha256']:raise ValueError('raw hash mismatch')
    rows=parse_candidates(body,task,record['path'],record['sha256'])
    expected=b''.join((json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode() for row in rows)
    if expected!=shard:raise ValueError('candidate shard differs from raw replay')
    return rows


def run(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c['version']!='financial-acquisition-stream-audit-v1':raise ValueError('unknown audit version')
    def pin(path,sha=None):
        body=inside(root,path).read_bytes();actual=digest(body)
        if sha is not None and actual!=sha:raise ValueError('audit source changed: '+path)
        pins[path]=actual;return body
    for p in CODE+[config_path]:pin(p)
    result=c['input_result'];manifest=json.loads(pin(result+'/manifest.json',c['input_manifest_sha256']))
    for name,sha in manifest.items():pin(result+'/'+name,sha)
    summary=read(inside(root,result+'/summary.json'))
    if summary['parser_errors'] or summary['task_statuses'].get('PENDING',0):raise ValueError('producer incomplete or parser errors')
    cp=read(inside(root,result+'/contract-pin.json'));contract=json.loads(pin(c['batch_root']+'/contract.json',cp['sha256']))
    tasks={t['id']:t for t in contract['tasks']};receipts={};statuses=Counter()
    for rel,sha in read(inside(root,result+'/receipt-pins.json')).items():
        rp=c['batch_root']+'/'+rel;r=json.loads(pin(rp,sha));task=r['task'];tid=task['id']
        if tasks.get(tid)!=task or Path(rel).name!=tid+'.json' or tid in receipts:raise ValueError('receipt assignment differs')
        receipts[tid]=r;statuses[r['status']]+=1
    if len(receipts)!=len(tasks) or dict(statuses)!=summary['task_statuses']:raise ValueError('task accounting mismatch')
    shards=read(inside(root,result+'/candidate-shards.json'));seen=set();counts=Counter();symbols=Counter();issues=[];cells=0;extra=0
    for shard in shards:
        tid=shard['task_id']
        if tid in seen or tid not in receipts or not receipts[tid].get('record'):raise ValueError('invalid shard assignment')
        seen.add(tid);record=receipts[tid]['record'];body=pin(record['path'],record['sha256']);raw_shard=pin(shard['path'],shard['sha256'])
        rows=replay(body,tasks[tid],record,raw_shard)
        if len(rows)!=shard['cells']:raise ValueError('shard cell count differs')
        payload=json.loads(body)
        for row in rows:
            cells+=1;symbols[row['symbol']]+=1
            if not 2012<=row['year']<=2025:extra+=1;continue
            kind=classify(row,payload);counts[kind]+=1
            if kind in ['UNRESOLVED_MAPPING','INVALID_NUMERIC']:
                issues.append(dict(kind=kind,symbol=row['symbol'],year=row['year'],quarter=row['quarter'],field=row['raw_code'],
                    status='DEFERRED_REVIEW_NOT_ACCEPTED',evidence=row))
    if seen!={tid for tid,r in receipts.items() if r.get('record')}:raise ValueError('acquired receipt lacks shard')
    if cells!=summary['candidate_cells']:raise ValueError('total cells differ')
    coverage=list(csv.DictReader(io.StringIO(pin(result+'/financial_coverage.csv').decode('utf-8'))))
    missing=[row for row in coverage if row['status'] in ['NO_CANDIDATE_IN_ACQUIRED_PAGES','PARTIAL_CANDIDATE_GROUPS','AUXILIARY_NOT_ACQUIRED']]
    for row in missing:issues.append(dict(kind='MISSING_COVERAGE',symbol=row['symbol'],year=int(row['year']),quarter=int(row['quarter']),field=row['statement'],status='DEFERRED_REVIEW_NOT_PROOF_OF_NONPUBLICATION',evidence=row))
    products={'summary.json':encoded(dict(status='PASS_ACQUISITION_INTEGRITY_ONLY' if not counts['INVALID_NUMERIC'] else 'HOLD_INVALID_NUMERIC',
        tasks=len(tasks),receipt_statuses=dict(statuses),raw_responses_replayed=len(shards),candidate_cells=cells,
        diagnostic_cells_by_symbol=dict(symbols),observed_cells_outside_diagnostic_range=extra,
        field_statuses=dict(counts),missing_coverage_slots=len(missing),review_items=len(issues),
        semantic_checks='DEFERRED_ACCOUNTING_ANNUAL_Q4_TEMPLATE_FAMILY_AND_PDF_REVIEW',
        numeric_acceptance_allowed=False,pit_ready=False,research_ready=False)),
        'input-pins.json':encoded(pins),'missing.json':encoded(missing)}
    products['review-items.jsonl']=b''.join((json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for row in issues)
    m={name:digest(body) for name,body in products.items()};out=inside(root,c['output_root'])/digest(encoded(m))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',m)
    return dict(json.loads(products['summary.json']),output=out.relative_to(root).as_posix())
