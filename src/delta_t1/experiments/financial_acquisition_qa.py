"""Offline acquisition QA; unknown institution templates stay unmapped."""
from collections import Counter,defaultdict
import csv,io,json
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put
from .financial_history_batch import parse_receipt
from .financial_history_batch_qa import diagnose
CODE=['src/delta_t1/experiments/financial_acquisition_qa.py','scripts/financial_acquisition_qa.py',
      'src/delta_t1/experiments/financial_history_batch_qa.py','src/delta_t1/experiments/financial_history_qa.py',
      'src/delta_t1/experiments/financial_history_batch.py','src/delta_t1/experiments/financial_template_candidates.py']


def classify_templates(rows,reference,templates):
    reference_types={r['symbol']:r['proposed_company_type'] for r in reference}
    known=defaultdict(set)
    for item in templates:
        if item['task']['statement']!='KQKD':continue
        for fingerprint in item['template_sha256']:known[fingerprint].add(reference_types[item['task']['symbol']])
    observed=defaultdict(set);symbols={row['symbol'] for row in rows}
    for row in rows:
        if row['statement']=='KQKD':observed[row['symbol']].add(row['template_sha256'])
    profiles=[];proof=[]
    for symbol in sorted(symbols):
        signatures=observed[symbol];families={next(iter(known[h])) for h in signatures if len(known[h])==1}
        resolved=bool(signatures) and all(len(known[h])==1 for h in signatures) and len(families)==1
        kind=next(iter(families)) if resolved else 'UNKNOWN'
        profiles.append(dict(symbol=symbol,proposed_company_type=kind))
        proof.append(dict(symbol=symbol,diagnostic_template_family=kind,template_hashes=sorted(signatures),
            source='PINNED_CURRENT_PROFILE_AND_EXACT_KQKD_TEMPLATE_REFERENCE',industry_accepted=False,
            regular_semantic_diagnostics_allowed=kind=='Regular',accepted=False,pit_ready=False))
    return profiles,proof

def run(root,config_path,action):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-acquisition-qa-v1':raise ValueError('F3 QA contract required')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('QA input changed: '+path)
        pins[path]=sha;return body
    for path in [config_path]+CODE:pin(path)
    mode=c.get('input_mode','SEALED_BATCH_RESULT');rows=[];payloads={};source_receipts=[];parser_errors=[]
    contract_path=c['batch_root']+'/contract.json'
    if mode=='SEALED_BATCH_RESULT':
        report=c['input_result'];manifest=json.loads(pin(report+'/manifest.json',c['input_manifest_sha256']))
        for name,sha in manifest.items():pin(report+'/'+name,sha)
        shards=read(inside(root,report+'/candidate-shards.json'))
        for shard in shards:
            body=pin(shard['path'],shard['sha256']);part=[json.loads(line) for line in body.splitlines()]
            if len(part)!=shard['cells']:raise ValueError('candidate shard row count differs')
            rows.extend(part)
        cp=read(inside(root,report+'/contract-pin.json'));contract=json.loads(pin(contract_path,cp['sha256']))
        receipts=read(inside(root,report+'/receipt-pins.json'))
        coverage=list(csv.DictReader(io.StringIO(pin(report+'/financial_coverage.csv').decode('utf-8'))))
        parser_errors=read(inside(root,report+'/parser-errors.json'))
    elif mode=='FROZEN_RECEIPT_PREVIEW':
        contract=json.loads(pin(contract_path,c['batch_contract_sha256']))
        inventory=json.loads(pin(c['receipt_inventory']['path'],c['receipt_inventory']['sha256']))
        receipts=inventory['receipts'];coverage=[]
        if not receipts:raise ValueError('empty preview is not a data QA run')
    else:raise ValueError('unknown QA input mode')
    expected={t['id']:t for t in contract['tasks']};seen=set()
    for path,sha in receipts.items():
        relative=path if mode=='FROZEN_RECEIPT_PREVIEW' else c['batch_root']+'/'+path
        target=inside(root,relative)
        if not target.is_relative_to(inside(root,c['batch_root'])/'receipts'):raise ValueError('QA receipt outside batch')
        receipt=json.loads(pin(relative,sha));task=receipt['task'];tid=task['id']
        if tid in seen or expected.get(tid)!=task or target.name!=tid+'.json':raise ValueError('QA receipt assignment differs')
        seen.add(tid);source_receipts.append(receipt)
        if receipt.get('record'):
            record=receipt['record'];body=pin(record['path'],record['sha256'])
            try:payloads[record['path']]=json.loads(body)
            except ValueError:pass  # Producer parser_errors retain this response; no facts accepted.
            if mode=='FROZEN_RECEIPT_PREVIEW':
                try:rows.extend(parse_receipt(root,receipt))
                except (ValueError,KeyError,TypeError) as error:parser_errors.append(dict(task=task,reason=str(error)))
    for row in rows:
        path=row['source_path']
        if pins.get(path)!=row['source_sha256']:raise ValueError('QA candidate raw hash differs from receipt')
    for path,sha in contract['pins'].items():pin(path,sha)
    reference=json.loads(pin(c['reference_profiles']['path'],c['reference_profiles']['sha256']))
    templates=json.loads(pin(c['reference_templates']['path'],c['reference_templates']['sha256']))
    profiles,classification=classify_templates(rows,reference,templates)
    findings=diagnose(rows,profiles,payloads,coverage)
    findings['summary'].update(input_mode=mode,acquisition_parser_errors=len(parser_errors),receipt_count=len(receipts),
        receipt_statuses=dict(Counter(r['status'] for r in source_receipts)),
        coverage_assessment='NOT_PERFORMED_PREVIEW' if mode=='FROZEN_RECEIPT_PREVIEW' else 'SEALED_ACQUISITION_SNAPSHOT')
    findings['summary']['classification_policy']='EXACT_OBSERVED_TEMPLATE_FAMILY_DIAGNOSTICS_ONLY_UNKNOWN_HELD'
    products={'template-classification.json':encoded(classification),'summary.json':encoded(findings['summary']),'input-pins.json':encoded(pins),'acquisition-parser-errors.json':encoded(parser_errors)}
    products['mapped_candidates.jsonl']=b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for r in findings['mapped'])
    for key in ['structural','unresolved','orphans','invalid','conflicts','arithmetic','annual_q4','displacements','missing','schema_changes','document_queue']:
        products[key+'.json']=encoded(findings[key])
    m={name:digest(body) for name,body in products.items()};out=inside(root,c['output_root'])/digest(encoded(m))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=m:raise ValueError('QA output manifest differs')
        for name,sha in m.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('QA output changed')
    else:
        for name,body in products.items():put(out/name,body)
        put(out/'manifest.json',m)
    return dict(findings['summary'],output=out.relative_to(root).as_posix())
