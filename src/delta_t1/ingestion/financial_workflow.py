"""Offline, deduplicated field work queue; extraction hints never grant acceptance."""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from .cafef_financial import digest, encoded, immutable_write
from .financial_documents import verify_inventory
from .financial_document_review import rejected_hashes

VERIFIED = 'DOCUMENT_VALUE_VERIFIED_PIT_PENDING'

def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.lower().replace('đ','d'))
                   if not unicodedata.combining(c))

def build(readiness, tasks, documents, pages, policy):
    if any(x.get('financial_features_allowed') is not False for x in [readiness,tasks,policy]):
        raise ValueError('workflow cannot grant financial features')
    symbols = policy['symbols']
    if not symbols or len(symbols)>policy['max_symbols'] or len(set(symbols))!=len(symbols):
        raise ValueError('invalid bounded symbol scope')
    rows={(r['symbol'],r['year'],r['field']):r for r in readiness['rows'] if r['symbol'] in symbols}
    consumers={}
    external={}
    for task in tasks['rows']:
        if task['symbol'] not in symbols: continue
        for blocker in task.get('semantic_blockers',[]):
            external.setdefault((task['symbol'],task['year'],blocker),set()).add(task['task'])
        for item in task['inputs']:
            key=(task['symbol'],item['year'],item['field'])
            consumers.setdefault(key,set()).add(f"{task['task']}:{task['year']}")
    queue=[]
    for key in sorted(set(rows)|set(consumers)):
        symbol,year,field=key
        row=rows.get(key,{})
        status=row.get('evidence_status','MISSING_SEMANTIC_MAPPING')
        docs=[d for d in documents if (d['symbol'],d['year'])==(symbol,year)]
        recipe=policy.get('field_recipes',{}).get(field,{})
        refs=row.get('document_evidence',[])
        if status==VERIFIED: action='REVIEW_VINTAGE_AND_PUBLICATION'
        elif status=='DOCUMENT_VALUE_CONFLICT': action='RESOLVE_SAME_VINTAGE_CONFLICT'
        elif not docs: action='ACQUIRE_SCOPE_FRAMEWORK_DOCUMENT'
        elif any(g['symbol']==symbol and year in g['years'] for g in policy.get('document_gaps',[])):
            action='ACQUIRE_REQUIRED_FRAMEWORK_DOCUMENT'
        elif recipe.get('requires_mapping'): action='REVIEW_SEMANTIC_MAPPING'
        else: action='EXTRACT_AND_VISUALLY_VERIFY'
        terms=[normalized(x) for x in recipe.get('search_terms',[])]
        matches=[{k:p[k] for k in ['pdf_sha256','pdf_page','ocr_path','image_path']}
                 for p in pages if (p['symbol'],p['year'])==(symbol,year)
                 and any(term in normalized(p['text']) for term in terms)]
        queue.append(dict(symbol=symbol,year=year,field=field,evidence_status=status,
            action=action,consumers=sorted(consumers.get(key,[])),
            documents=docs,search_page_hints=matches[:policy['max_hints_per_field']],
            hint_matches_total=len(matches),document_evidence=refs,
            required_qa=recipe.get('qa',['VALUE_UNIT_PERIOD_SCOPE_FRAMEWORK','SOURCE_COLUMN_AND_VINTAGE']),
            acceptance='NO_AUTOMATIC_ACCEPTANCE',financial_features_allowed=False))
    if len(queue)>policy['max_queue_cells']: raise ValueError('queue budget exceeded')
    external_rows=[dict(symbol=symbol,year=year,requirement=blocker,consumers=sorted(names),
                       action='ACQUIRE_QUARTER_YTD_AND_RECONCILE_TTM' if blocker=='COMPATIBLE_EPS_TTM_NOT_ANNUAL_EPS'
                       else 'VERIFY_EXTERNAL_TEMPORAL_DEPENDENCY',financial_features_allowed=False)
                   for (symbol,year,blocker),names in sorted(external.items())]
    return dict(rows=queue,external_requirements=external_rows,counts=dict(Counter(x['action'] for x in queue)),
        unique_field_year_cells=len(queue),task_input_references=sum(len(x['consumers']) for x in queue),
        ocr_hint_only=True,financial_features_allowed=False,financial_pit_gate='NOT_READY',
        full_universe_allowed=False)

def export(readiness_run,task_run,index_runs,policy_path,output,document_review_run=None):
    paths=[Path(readiness_run).resolve(),Path(task_run).resolve()]
    paths.extend(Path(x).resolve() for x in index_runs)
    for path in paths: verify_inventory(path)
    policy=json.loads(Path(policy_path).read_bytes())
    if not 1<=len(index_runs)<=policy['max_index_runs']: raise ValueError('index run budget exceeded')
    documents={};pages={}
    rejected = rejected_hashes(document_review_run)
    quarantined = set()
    for run in paths[2:]:
        index=json.loads((run/'index.json').read_bytes())
        if index.get('financial_features_allowed') is not False: raise ValueError('unapproved OCR input')
        for d in index['documents']:
            if d.get('quarter')!=0: continue
            pdf=Path(d.get('path',d.get('pdf_path')))
            pdf_hash=d.get('sha256',d.get('pdf_sha256'))
            if digest(pdf.read_bytes())!=pdf_hash:raise ValueError('source PDF hash mismatch')
            if pdf_hash in rejected:
                quarantined.add(pdf_hash)
                continue
            documents[(d['symbol'],d['year'],pdf_hash)]=dict(symbol=d['symbol'],year=d['year'],
                pdf_path=str(pdf),pdf_sha256=pdf_hash,scope_status='REQUIRES_DOCUMENT_VERIFICATION',
                accounting_framework_status='NOT_INFERRED_FROM_INDEX_OR_AUDIT_EXTRACT')
            if len(documents)>policy['max_unique_documents']:raise ValueError('document budget exceeded')
            for file in sorted((run/pdf.stem).glob('*.ocr.json')):
                record=json.loads(file.read_bytes())
                image=file.with_name(file.name.replace('.ocr.json','.png'))
                if digest(image.read_bytes())!=record['image_sha256']: raise ValueError('OCR image mismatch')
                page=int(re.search(r'page-(\d+)\.ocr\.json$',file.name)[1])
                pages[(pdf_hash,page)]=dict(symbol=d['symbol'],year=d['year'],pdf_sha256=pdf_hash,
                    pdf_page=page,text=record['text'],ocr_path=str(file),image_path=str(image))
                if len(pages)>policy['max_reused_ocr_pages']:raise ValueError('OCR reuse budget exceeded')
    result=build(json.loads((paths[0]/'readiness.json').read_bytes()),
                 json.loads((paths[1]/'task_readiness.json').read_bytes()),
                 list(documents.values()),list(pages.values()),policy)
    result.update(indexed_unique_documents=len(documents),reused_ocr_pages=len(pages),
        quarantined_pdf_hashes=sorted(quarantined),
        input_manifest_sha256={str(p):digest((p/'manifest.json').read_bytes()) for p in paths},
        policy_sha256=digest(Path(policy_path).read_bytes()))
    if document_review_run is not None:
        review = Path(document_review_run).resolve()
        result['input_manifest_sha256'][str(review)] = digest((review/'manifest.json').read_bytes())
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'workflow.json',encoded(result))
    immutable_write(out/'planner.py',Path(__file__).read_bytes())
    immutable_write(out/'policy.json',Path(policy_path).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return result
