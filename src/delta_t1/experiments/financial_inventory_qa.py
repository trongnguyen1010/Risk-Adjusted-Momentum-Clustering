"""Offline, per-security coverage inventory and existing diagnostic QA; no acceptance."""
import csv,io,json,os
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .financial_history_documents import read,put
from .financial_history_batch_qa import diagnose
from .financial_acquisition_qa import classify_templates
from .financial_template_candidates import parse_candidates
from .financial_acquisition_overnight import state_file
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside

CODE=['src/delta_t1/experiments/financial_inventory_qa.py','scripts/financial_inventory_qa.py',
      'src/delta_t1/experiments/financial_history_batch_qa.py','src/delta_t1/experiments/financial_history_qa.py',
      'src/delta_t1/experiments/financial_acquisition_qa.py','src/delta_t1/experiments/financial_template_candidates.py',
      'src/delta_t1/experiments/financial_acquisition_overnight.py','src/delta_t1/experiments/financial_history_documents.py',
      'src/delta_t1/ingestion/cafef_financial.py','src/delta_t1/ingestion/financial_batch_evidence.py']
DETAILS=['unresolved','orphans','invalid','conflicts','displacements','schema_changes','document_queue']
SYMBOL_COLUMNS=['registry_id','symbol','exchange','company_name','source_result','receipt_count','acquired_responses','failed_requests','candidate_cells','diagnostic_template_family','main_present_slots','main_missing_slots','auxiliary_present','earliest_candidate_period','latest_candidate_period','observed_years','mapped_diagnostic_cells','unresolved_nonstructural_codes','provider_value_conflicts','possible_row_displacements','document_queue_periods','historical_identity_ready','numeric_acceptance_allowed','pit_ready','next_action','evidence_ref']
FIELD_COLUMNS=['symbol','year','quarter','mode','provider_type','field','observation_count','distinct_value_count','candidate_values','evidence','status','accepted','pit_ready']

def csv_body(rows,columns):
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows);return f.getvalue().encode('utf-8')

def validate_ownership(registry,cohorts):
    by_symbol={r['ticker']:r for r in registry}
    if len(by_symbol)!=len(registry) or len({r['registry_id'] for r in registry})!=len(registry):raise ValueError('ambiguous current registry')
    owned={}
    for cohort in cohorts:
        for symbol in cohort:
            if symbol not in by_symbol or symbol in owned:raise ValueError('duplicate/outside source cohort')
            owned[symbol]=by_symbol[symbol]
    if set(owned)!=set(by_symbol):raise ValueError('source cohorts do not cover registry exactly')
    return owned

def coverage_grid(rows,symbol):
    keys={(int(r['year']),int(r['quarter']),r['mode'],r['statement']) for r in rows}
    expected={(y,q,m,s) for y in range(2013,2026) for m,qs in [('NAM',[0]),('QUY',[1,2,3,4])] for q in qs for s in ['CDKT','KQKD','LCTT']}|{(2012,0,'NAM','CDKT')}
    if len(keys)!=len(rows) or keys!=expected or any(r['symbol']!=symbol for r in rows):raise ValueError('coverage grid missing/duplicate/outside scope')
    return rows

def field_presence(mapped):
    groups=defaultdict(list)
    for row in mapped:groups[(row['symbol'],row['year'],row['quarter'],row['mode'],row['provider_type'],row['field'])].append(row)
    result=[]
    for key,rows in sorted(groups.items(),key=str):
        values=sorted({r['value'] for r in rows if r['value'] is not None})
        result.append(dict(zip(FIELD_COLUMNS[:6],key),observation_count=len(rows),distinct_value_count=len(values),candidate_values=json.dumps(values,ensure_ascii=False),evidence=json.dumps([{k:r.get(k) for k in ['source_path','source_sha256','raw_code','label']} for r in rows[:3]],ensure_ascii=False),status='DIAGNOSTIC_ALIAS_ONLY_NOT_METRIC_INPUT_ACCEPTANCE',accepted=False,pit_ready=False))
    return result

def load_receipt(root,item):
    path,sha,expected,shard=item;raw=inside(root,path).read_bytes()
    if digest(raw)!=sha:raise ValueError('receipt changed: '+path)
    r=json.loads(raw);task=r['task']
    if task['id']!=Path(path).stem or any(task.get(k)!=expected.get(k) for k in ['id','symbol','kind','statement','mode','group','page','url']):raise ValueError('receipt task differs')
    pins={path:sha};rows=[];payload=None
    if r.get('record'):
        if task['kind']!='REPORT':raise ValueError('unexpected catalogue payload in candidate inventory')
        rec=r['record'];body=inside(root,rec['path']).read_bytes()
        if digest(body)!=rec['sha256']:raise ValueError('raw hash changed')
        pins[rec['path']]=rec['sha256'];rows=parse_candidates(body,task,rec['path'],rec['sha256'])
        if shard:
            canonical=b''.join((json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode() for row in rows)
            if digest(canonical)!=shard['sha256'] or len(rows)!=shard['cells']:raise ValueError('raw replay differs from sealed modern candidate shard')
        raw_payload=json.loads(body);payload={'value':{'templace':raw_payload['value'].get('templace',[])}}
    return r,rows,payload,pins

def verify_checkpoint(root,out,expected_job):
    if not (out/'manifest.json').exists():raise ValueError('unsealed symbol checkpoint; inspect before resume')
    manifest=read(out/'manifest.json')
    for name,sha in manifest.items():
        if digest((out/name).read_bytes())!=sha:raise ValueError('symbol checkpoint output changed')
    pins=read(out/'input-pins.json')
    if pins['job_sha256']!=expected_job:raise ValueError('symbol checkpoint job changed')
    for path,sha in pins['sources'].items():
        if digest(inside(root,path).read_bytes())!=sha:raise ValueError('symbol checkpoint raw/receipt changed')
    return read(out/'inventory.json')

def process_symbol(root,out,member,items,coverage,reference,templates,job_sha,source_result,pool):
    if out.exists():return verify_checkpoint(root,out,job_sha)
    rows=[];payloads={};pins={};statuses=Counter();failed=[]
    for receipt,part,payload,used in pool.map(lambda item:load_receipt(root,item),items):
        pins.update(used);statuses[receipt['status']]+=1;rows.extend(part)
        if payload is not None:payloads[receipt['record']['path']]=payload
        if receipt['status']=='FAILED_OR_STOPPED':failed.append(receipt)
    if statuses['PENDING']:raise ValueError('pending source receipt')
    if any(row['symbol']!=member['ticker'] or row['accepted'] or row['pit_ready'] for row in rows):raise ValueError('candidate scope/acceptance changed')
    # A fully accounted legacy snapshot predates the explicit coverage flag.
    for c in coverage:
        c.setdefault('task_accounting_complete','True');c.setdefault('unique_code_label_cells','UNKNOWN_LEGACY_COVERAGE_SCHEMA')
    profiles,classification=classify_templates(rows,reference,templates)
    if not rows:profiles=[dict(symbol=member['ticker'],proposed_company_type='UNKNOWN')];classification=[dict(symbol=member['ticker'],diagnostic_template_family='UNKNOWN',accepted=False,pit_ready=False)]
    findings=diagnose(rows,profiles,payloads,coverage);s=findings['summary'];family=profiles[0]['proposed_company_type']
    present=[r for r in coverage if r['status']=='CANDIDATE_GROUPS_PRESENT'];main_missing=[r for r in coverage if int(r['year'])>=2013 and r['status']!='CANDIDATE_GROUPS_PRESENT']
    observed=sorted({f"{r['year']}-Q{r['quarter']}" for r in present})
    inventory=dict(registry_id=member['registry_id'],symbol=member['ticker'],exchange=member['exchange'],company_name=member['company_name'],source_result=source_result,receipt_count=sum(statuses.values()),acquired_responses=sum(statuses[k] for k in statuses if k in ['ACQUIRED','CACHED_PROBE','CACHE_HIT']),failed_requests=len(failed),candidate_cells=len(rows),diagnostic_template_family=family,main_present_slots=len(present),main_missing_slots=len(main_missing),auxiliary_present=any(r['status']=='AUXILIARY_CANDIDATES_PRESENT' for r in coverage),earliest_candidate_period=observed[0] if observed else '',latest_candidate_period=observed[-1] if observed else '',observed_years=';'.join(map(str,sorted({int(r['year']) for r in present}))),mapped_diagnostic_cells=s['mapped_diagnostic_cells'],unresolved_nonstructural_codes=s['unresolved_nonstructural_codes'],provider_value_conflicts=s['provider_value_conflicts'],possible_row_displacements=s['possible_row_displacements'],document_queue_periods=s['selective_document_queue_periods'],historical_identity_ready=False,numeric_acceptance_allowed=False,pit_ready=False,next_action='REVIEW_FAILURES_GAPS_AND_DIAGNOSTICS;UNITS_SCOPE_VINTAGES_PUBLICATION_SHARES_PRICE_REQUIRED',evidence_ref=out.relative_to(root).as_posix())
    products={'inventory.json':encoded(inventory),'summary.json':encoded(dict(s,receipt_statuses=dict(statuses),observed_candidate_years=sorted({r['year'] for r in rows}),cells_outside_diagnostic_range=sum(not 2012<=r['year']<=2025 for r in rows))),
        'input-pins.json':encoded(dict(job_sha256=job_sha,sources=pins)),'template-classification.json':encoded(classification),'failed-requests.json':encoded(failed),
        'coverage.csv':csv_body(coverage,sorted({k for r in coverage for k in r})),
        'field-presence.csv':csv_body(field_presence(findings['mapped']),FIELD_COLUMNS),
        'arithmetic-findings.json':encoded([x for x in findings['arithmetic'] if x['status']!='RAW_EQUALITY']),
        'annual-q4-findings.json':encoded([x for x in findings['annual_q4'] if x['status']!='RAW_EQUALITY'])}
    for name in DETAILS:products[name+'.json']=encoded(findings[name])
    manifest={name:digest(raw) for name,raw in products.items()}
    for name,raw in products.items():put(out/name,raw)
    put(out/'manifest.json',manifest)
    return inventory

def run(root,config_path):
    root=Path(root);c=read(inside(root,config_path));base=inside(root,c['output_root']);status=base/'pipeline-status.json';pins={}
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('inventory source changed: '+path)
        pins[path]=sha;return raw
    try:
        if c['version']!='financial-inventory-qa-v1':raise ValueError('unknown inventory version')
        for p in CODE+[config_path]:pin(p)
        registry=list(csv.DictReader(io.StringIO(pin(c['registry']['path'],c['registry']['sha256']).decode('utf-8-sig'))))
        reference=json.loads(pin(c['reference_profiles']['path'],c['reference_profiles']['sha256']));templates=json.loads(pin(c['reference_templates']['path'],c['reference_templates']['sha256']))
        cohorts=[];loaded=[]
        for source in c['sources']:
            result=source['result'];manifest=json.loads(pin(result+'/manifest.json',source['manifest_sha256']))
            summary=json.loads(pin(result+'/summary.json',manifest['summary.json']))
            if summary.get('parser_errors',0) or summary.get('task_statuses',{}).get('PENDING',0):raise ValueError('source incomplete/parser errors')
            coverage=list(csv.DictReader(io.StringIO(pin(result+'/financial_coverage.csv',manifest['financial_coverage.csv']).decode('utf-8-sig'))));symbols=sorted({r['symbol'] for r in coverage});cohorts.append(symbols)
            contract=json.loads(pin(source['batch_root']+'/contract.json',source['contract_sha256']))
            if 'contract-pin.json' in manifest:
                cp=json.loads(pin(result+'/contract-pin.json',manifest['contract-pin.json']))
                if cp['sha256']!=source['contract_sha256']:raise ValueError('source contract pin differs')
            if 'tasks' in contract:tasks=contract['tasks']
            else:tasks=list(csv.DictReader(io.StringIO(pin(result+'/tasks.csv',manifest['tasks.csv']).decode('utf-8-sig'))));tasks=[dict(t,page=int(t['page']),kind='REPORT' if t['statement']!='DISCLOSURE' else 'DISCLOSURE') for t in tasks]
            receipts=json.loads(pin(result+'/receipt-pins.json',manifest['receipt-pins.json']));shards={}
            if 'candidate-shards.json' in manifest:shards={s['task_id']:s for s in json.loads(pin(result+'/candidate-shards.json',manifest['candidate-shards.json']))}
            expected={t['id']:t for t in tasks}
            if len(expected)!=len(tasks) or len(receipts)!=len(tasks):raise ValueError('source task/receipt accounting differs')
            grouped=defaultdict(list);grid=defaultdict(list)
            for rel,sha in sorted(receipts.items()):
                tid=Path(rel).stem;t=expected[tid]
                if rel!='receipts/'+tid+'.json' or t['symbol'] not in symbols:raise ValueError('source task outside cohort')
                grouped[t['symbol']].append((source['batch_root']+'/'+rel,sha,t,shards.get(tid)))
            for row in coverage:grid[row['symbol']].append(row)
            for symbol in symbols:coverage_grid(grid[symbol],symbol)
            loaded.append((source,summary,grouped,grid))
        members=validate_ownership(registry,cohorts)
        if len(members)!=c['expected_symbols']:raise ValueError('unexpected registry count')
        job_sha=digest(encoded(pins));job=base/'jobs'/job_sha[:20];put(job/'input-pins.json',pins);put(job/'config.json',c)
        processed=[];cell_counts=Counter();state_file(status,'RUNNING_SYMBOL_QA',completed=0,total=len(members),job=job.relative_to(root).as_posix())
        with ThreadPoolExecutor(max_workers=8) as pool:
            for source,summary,grouped,grid in loaded:
                cohort_cells=0
                for symbol in sorted(grouped):
                    member=members[symbol];out=job/'symbols'/member['registry_id']
                    inv=process_symbol(root,out,member,grouped[symbol],grid[symbol],reference,templates,job_sha,source['result'],pool)
                    processed.append(inv);cohort_cells+=inv['candidate_cells']
                    if len(processed)%10==0:
                        state_file(status,'RUNNING_SYMBOL_QA',completed=len(processed),total=len(members),last_symbol=symbol,job=job.relative_to(root).as_posix());print(json.dumps(dict(event='INVENTORY_QA_CHECKPOINT',completed=len(processed),total=len(members),last_symbol=symbol)),flush=True)
                if cohort_cells!=summary['candidate_cells']:raise ValueError('cohort replay cell accounting differs')
                cell_counts[source['result']]=cohort_cells
        return consolidate(root,c,job,pins,processed,cell_counts,status)
    except Exception as error:
        state_file(status,'HELD_REVIEW_REQUIRED',reason=str(error));raise

def consolidate(root,c,job,pins,inventory,cell_counts,status):
    state_file(status,'CONSOLIDATING_OUTPUTS',completed=len(inventory),total=len(inventory))
    totals=Counter();classes=Counter();coverage_counts=Counter();checks=defaultdict(Counter);symbol_pins={}
    columns=['symbol','year','quarter','mode','statement','status','observed_groups','numeric_cells','task_accounting_complete','accepted','pit_ready','missing_interpretation','evidence_ref']
    streams={name:io.StringIO(newline='') for name in ['coverage.csv','missing-periods.csv','document-priority-queue.csv']}
    writers={name:csv.DictWriter(stream,fieldnames=columns if name!='document-priority-queue.csv' else ['symbol','year','quarter','mode','priority','reasons','action','evidence_ref']) for name,stream in streams.items()}
    for w in writers.values():w.writeheader()
    for item in sorted(inventory,key=lambda r:r['symbol']):
        out=inside(root,item['evidence_ref']);s=read(out/'summary.json');symbol_pins[item['registry_id']]=dict(path=item['evidence_ref']+'/manifest.json',sha256=digest((out/'manifest.json').read_bytes()))
        for key in ['candidate_cells','acquired_responses','failed_requests','mapped_diagnostic_cells','unresolved_nonstructural_codes','provider_value_conflicts','possible_row_displacements','document_queue_periods']:totals[key]+=item[key]
        classes[item['diagnostic_template_family']]+=1
        for name in ['raw_accounting_checks','annual_q4_checks']:checks[name].update(s[name])
        for row in csv.DictReader((out/'coverage.csv').open(encoding='utf-8-sig',newline='')):
            coverage_counts[row['status']]+=1;gap=row['status'] not in ['CANDIDATE_GROUPS_PRESENT','AUXILIARY_CANDIDATES_PRESENT'];r={k:row.get(k,'') for k in columns};r.update(missing_interpretation='ABSENT_FROM_ACQUIRED_PAGES_NOT_PROOF_OF_NONPUBLICATION' if gap else '',evidence_ref=item['evidence_ref']+'/coverage.csv')
            writers['coverage.csv'].writerow(r)
            if gap:writers['missing-periods.csv'].writerow(r)
        for entry in read(out/'document_queue.json'):
            writers['document-priority-queue.csv'].writerow(dict(symbol=entry['symbol'],year=entry['year'],quarter=entry['quarter'],mode=entry['mode'],priority=entry['priority'],reasons=';'.join(entry['reasons']),action=entry['action'],evidence_ref=item['evidence_ref']+'/document_queue.json'))
    summary=dict(status='PASS_OFFLINE_INVENTORY_QA_DIAGNOSTICS',symbols=len(inventory),source_cohorts=len(cell_counts),totals=dict(totals),diagnostic_template_families=dict(classes),coverage_statuses=dict(coverage_counts),checks={k:dict(v) for k,v in checks.items()},numeric_acceptance_allowed=False,pit_ready=False,research_ready=False,financial_delivery='PARTIAL_UNITS_SCOPE_VINTAGES_SHARES_PRICES_PUBLICATION_AND_METRIC_INPUT_REVIEW_REQUIRED',baseline_fy2025_verified=29,baseline_fy2025_target=30,diagnostic_alias_scope='EXISTING_REGULAR_COMPANY_ALIASES_ONLY_NOT_COMPLETE_METRIC_INPUT_CATALOGUE',unknown_templates='NO_REGULAR_SEMANTIC_FORMULA_OR_SCORE_MAPPING',current_registry_is_historical_universe=False)
    products={'summary.json':encoded(summary),'symbols.csv':csv_body(sorted(inventory,key=lambda r:r['symbol']),SYMBOL_COLUMNS),'symbol-manifests.json':encoded(symbol_pins),'source-cell-accounting.json':encoded(cell_counts),'input-pins.json':encoded(pins)}
    for name,stream in streams.items():products[name]=stream.getvalue().encode('utf-8')
    manifest={name:digest(body) for name,body in products.items()};out=job/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    report=inside(root,c['report_root']);rel=os.path.relpath(out,report).replace('\\','/')
    text=f'''# Inventory và QA tài chính 1.522 mã\n\nĐã inventory {len(inventory)} current provider candidates, {len(cell_counts)} cohort disjoint, {totals['candidate_cells']:,} candidate cells. Đây là chẩn đoán offline; không phải dữ liệu đã xác minh hoặc PIT.\n\n- [Danh sách mã và next action]({rel}/symbols.csv).\n- [Coverage theo mã/năm/quý/statement]({rel}/coverage.csv).\n- [Kỳ hoặc group thiếu]({rel}/missing-periods.csv).\n- [Hàng đợi PDF chọn lọc theo mức ưu tiên]({rel}/document-priority-queue.csv).\n- [Summary và counters]({rel}/summary.json).\n\nCó {totals['failed_requests']} failed requests; {totals['provider_value_conflicts']} key có nhiều giá trị provider; {totals['possible_row_displacements']} dấu hiệu displacement; {totals['unresolved_nonstructural_codes']} cells chưa map được. Đây là nghi vấn, không sửa số liệu hoặc coi raw equality là validation. Template families (diagnostic): {dict(classes)}. Unknown/institution templates không dùng aliases/công thức doanh nghiệp thường.\n\nMỗi mã có checkpoint và source hashes riêng, field-presence.csv, unresolved/orphans/conflicts/arithmetic-findings/annual-q4-findings/displacements/schema_changes/document_queue. Field presence chỉ phủ aliases QA hiện có; không tìm thấy alias không chứng minh raw/PDF thiếu field. Không cộng EPS quý, đổi lũy kế thành quý, suy units, trộn scope/provider types/vintages hoặc dùng báo cáo restated ngược lịch sử. Publication, weighted shares, snapshot price/market cap và identity chưa được acceptance trong stage này.\n\nCoverage groups present không chứng minh đủ field hoặc đủ mười năm liên tục; thiếu trong API không chứng minh không công bố. Auxiliary2012 giữ riêng; 2013–2025 annual/quarterly là cửa sổ chính financial. Reference metrics FY2025 vẫn29/30, VNM F chưa đủ input; không có numeric/PIT acceptance mới.\n\nBước sau: review các kỳ priority1 (displacement/conflict/invalid/nonzero orphan), xác định units/scope/vintage và input cho từng family; tra cache trước, chỉ bổ sung PDF/text/OCR trang cần thiết. Không tải PDF hàng loạt.\n'''
    put(report/'report.md',text.encode('utf-8'));put(report/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    state_file(status,'COMPLETE_OFFLINE_INVENTORY_QA_DIAGNOSTICS',completed=len(inventory),total=len(inventory),output=out.relative_to(root).as_posix(),report=(report/'report.md').relative_to(root).as_posix(),financial_delivery=summary['financial_delivery'])
    return dict(summary,output=out.relative_to(root).as_posix(),report=(report/'report.md').relative_to(root).as_posix())
