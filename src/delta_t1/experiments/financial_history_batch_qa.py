"""Offline F3 diagnostics and selective document queue, without fact acceptance."""
from collections import Counter,defaultdict
import csv,io,json

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put
from .financial_history_batch import parse_receipt
from .financial_history_qa import semantic_field,structural_header,number,unique_value,displacement

FORMULAS=[('ASSETS_EQUALS_CAPITAL','total_assets',['total_capital']),
          ('ASSETS_EQUALS_LIABILITIES_EQUITY','total_assets',['total_liabilities','total_equity']),
          ('ASSET_PARTS','total_assets',['current_assets','noncurrent_assets']),
          ('LIABILITY_PARTS','total_liabilities',['current_liabilities','noncurrent_liabilities']),
          ('GROSS_PROFIT','net_revenue',['cost_of_goods_sold','gross_profit'])]


def observation(row):
    return {k:row.get(k) for k in ['source_path','source_sha256','template_sha256','raw_cell_ordinal',
        'period_occurrence','raw_code','label','value','provider_type','provider_header','provider_unit','interval']}


def diagnose(rows,profiles,payloads,coverage):
    if len({p['symbol'] for p in profiles})!=len(profiles):raise ValueError('ambiguous QA profile identity')
    profiles={r['symbol']:r for r in profiles};mapped=[];structural=[];orphans=[];unresolved=[];invalid=[]
    fields=defaultdict(list);raw=defaultdict(list);schema=defaultdict(set)
    for row in rows:
        if row['symbol'] not in profiles:raise ValueError('candidate outside frozen profile assignment')
        if not 2012<=row['year']<=2025:continue
        identity=(row['symbol'],row['year'],row['quarter'],row['mode'],row['provider_type'])
        base=dict(symbol=row['symbol'],year=row['year'],quarter=row['quarter'],mode=row['mode'],
            statement=row['statement'],group=row['group'],**observation(row),accepted=False,pit_ready=False)
        if row.get('value_status') in ['INVALID_NUMERIC_QUARANTINED','BOOLEAN_QUARANTINED']:
            invalid.append(dict(base,status=row['value_status']));continue
        # Exact raw group-number proof only. Blank bank template codes are not structural proof.
        if structural_header(row,payloads[row['source_path']]):
            structural.append(dict(base,status='PROVEN_RAW_GROUP_HEADER_ZERO'));continue
        if row['mapping_status']!='UNIQUE_CODE_LABEL_CANDIDATE':
            unresolved.append(dict(base,status=row['mapping_status']))
            if row['mapping_status']!='BLANK_CODE_QUARANTINED':orphans.append(dict(base,status='UNEXPLAINED_OR_AMBIGUOUS_CODE'))
            continue
        raw[identity+(row['statement'],row['group'],row['raw_code'])].append(row)
        schema[(row['symbol'],row['statement'],row['group'],row['mode'])].add(row['template_sha256'])
        # These frozen aliases describe regular-company templates only. No bank/securities reuse.
        if profiles[row['symbol']]['proposed_company_type']!='Regular':continue
        field=semantic_field(row)
        if field:
            mapped.append(dict(base,field=field,status='EXACT_CODE_LABEL_DIAGNOSTIC',
                temporal_status='ANNUAL_CANDIDATE' if row['mode']=='NAM' else 'DURATION_AND_STANDALONE_VS_YTD_REVIEW_REQUIRED'))
            fields[identity+(field,)].append(row)
    conflicts=[]
    for key,values in sorted(raw.items(),key=str):
        if len({number(r['value']) for r in values})>1:
            conflicts.append(dict(key=list(key),observations=[observation(r) for r in values],
                status='PROVIDER_VALUE_DIFFERENCE_NO_VINTAGE_SELECTION',accepted=False))
    arithmetic=[]
    for identity in sorted({k[:5] for k in fields},key=str):
        for name,lhs,rhs in FORMULAS:
            inputs={f:fields.get(identity+(f,),[]) for f in [lhs]+rhs}
            if not all(inputs.values()):continue
            values={f:unique_value(v) for f,v in inputs.items()}
            delta=None if None in values.values() else values[lhs]-sum(values[f] for f in rhs)
            arithmetic.append(dict(period=list(identity),check=name,status='AMBIGUOUS_OR_MISSING_VALUE' if delta is None else 'RAW_EQUALITY' if delta==0 else 'RAW_DIFFERENCE',
                difference=None if delta is None else str(delta),observations={f:[observation(r) for r in v] for f,v in inputs.items()},
                interpretation='RAW_PROVIDER_PARTITION_ONLY_UNIT_SCOPE_VINTAGE_UNVERIFIED',accepted=False))
    comparisons=[];shifts=[]
    balances=defaultdict(dict)
    for key,values in raw.items():
        symbol,year,quarter,mode,provider_type,statement,group,code=key
        if statement=='CDKT' and ((mode=='NAM' and quarter==0) or (mode=='QUY' and quarter==4)):
            balances[(symbol,year,mode,provider_type)][(group,code)]=values
    for (symbol,year,mode,atype),annual in sorted(balances.items(),key=str):
        if mode!='NAM' or profiles[symbol]['proposed_company_type']!='Regular':continue
        for (qs,qy,qm,qtype),quarter in sorted(balances.items(),key=str):
            if (qs,qy,qm)!=(symbol,year,'QUY'):continue
            for key in sorted(annual.keys()&quarter.keys()):
                a,q=annual[key],quarter[key];av,qv=unique_value(a),unique_value(q)
                comparisons.append(dict(symbol=symbol,year=year,annual_provider_type=atype,q4_provider_type=qtype,group=key[0],raw_code=key[1],
                    status='AMBIGUOUS_OR_MISSING_VALUE' if av is None or qv is None else 'RAW_EQUALITY' if av==qv else 'RAW_DIFFERENCE',
                    annual=[observation(r) for r in a],q4=[observation(r) for r in q],accepted=False,
                    interpretation='CLOSING_CANDIDATES_NOT_EQUIVALENT_REPORT_VINTAGES_OR_SCOPES'))
            def debt_codes(data):
                return {int(code):unique_value(values) for (group,code),values in data.items()
                    if group=='NV' and str(code).isdigit() and 311<=int(code)<=324}
            for match in displacement(debt_codes(annual),debt_codes(quarter)):
                shifts.append(dict(symbol=symbol,year=year,annual_provider_type=atype,q4_provider_type=qtype,
                    status='POSSIBLE_ROW_DISPLACEMENT_REVIEW_NO_REPAIR',accepted=False,**match))
    queue={}
    def enqueue(symbol,year,mode,quarter,priority,reason,evidence):
        key=(symbol,year,mode,quarter)
        item=queue.setdefault(key,dict(symbol=symbol,year=year,mode=mode,quarter=quarter,priority=priority,reasons=[],evidence=[],
            action='CACHE_LOOKUP_THEN_PRIMARY_PDF_TEXT_FIRST_OCR_SELECTED_PAGES_ONLY',accepted=False,pit_ready=False))
        item['priority']=min(item['priority'],priority)
        if reason not in item['reasons']:item['reasons'].append(reason)
        item['evidence'].append(evidence)
    for item in shifts:enqueue(item['symbol'],item['year'],'NAM',0,1,'POSSIBLE_ROW_DISPLACEMENT',item)
    for item in arithmetic:
        if item['status']=='RAW_DIFFERENCE':
            symbol,year,quarter,mode,ptype=item['period'];enqueue(symbol,year,mode,quarter,2,'RAW_ACCOUNTING_DIFFERENCE',dict(check=item['check'],provider_type=ptype,difference=item['difference']))
    missing=[]
    for row in coverage:
        if row['status'] not in ['NO_CANDIDATE_IN_ACQUIRED_PAGES','PARTIAL_CANDIDATE_GROUPS','AUXILIARY_NOT_ACQUIRED']:continue
        complete=str(row['task_accounting_complete']).lower()=='true'
        gap=dict(row,reason='ABSENT_FROM_ACQUIRED_PROVIDER_PAGES_NOT_PROOF_OF_NONPUBLICATION' if complete else 'ACQUISITION_PENDING_NOT_A_DATA_GAP')
        missing.append(gap)
        if complete:enqueue(row['symbol'],int(row['year']),row['mode'],int(row['quarter']),2,'MISSING_PROVIDER_PERIOD_OR_GROUP',dict(statement=row['statement'],status=row['status']))
    for item in conflicts:
        symbol,year,quarter,mode,ptype,*_=item['key'];enqueue(symbol,year,mode,quarter,1,'MULTIPLE_PROVIDER_VALUES_REVIEW_VINTAGE',dict(key=item['key']))
    for item in invalid:
        enqueue(item['symbol'],item['year'],item['mode'],item['quarter'],1,'INVALID_PROVIDER_NUMERIC_TOKEN',item)
    for item in orphans:
        if item['value'] is not None and number(item['value'])!=0:
            enqueue(item['symbol'],item['year'],item['mode'],item['quarter'],1,'NONZERO_UNMAPPED_PROVIDER_CODE',item)
    schema_changes=[dict(symbol=k[0],statement=k[1],group=k[2],mode=k[3],template_sha256=sorted(v),accepted=False) for k,v in sorted(schema.items()) if len(v)>1]
    summary=dict(status='PARTIAL_DIAGNOSTICS_ONLY',input_candidate_cells=len(rows),diagnostic_year_range=[2012,2025],
        structural_header_zeros=len(structural),unresolved_nonstructural_codes=len(unresolved),unexplained_or_ambiguous_codes=len(orphans),
        invalid_numeric_cells=len(invalid),
        mapped_diagnostic_cells=len(mapped),provider_value_conflicts=len(conflicts),template_variation_cohorts=len(schema_changes),
        raw_accounting_checks=dict(Counter(r['status'] for r in arithmetic)),annual_q4_checks=dict(Counter(r['status'] for r in comparisons)),
        possible_row_displacements=len(shifts),missing_coverage_slots=len(missing),selective_document_queue_periods=len(queue),
        current_profile_types=dict(Counter(r['proposed_company_type'] for r in profiles.values())),
        bank_securities_score_mapping='NOT_IMPLEMENTED_NOT_REPLACED_WITH_REGULAR_FORMULAS',
        accepted_new_facts=0,pit_eligible_new_facts=0,financial_features_allowed=False,research_ready=False,next50_allowed=False)
    return dict(summary=summary,mapped=mapped,structural=structural,unresolved=unresolved,orphans=orphans,invalid=invalid,conflicts=conflicts,
        arithmetic=arithmetic,annual_q4=comparisons,displacements=shifts,missing=missing,schema_changes=schema_changes,
        document_queue=sorted(queue.values(),key=lambda r:(r['priority'],r['symbol'],r['year'],r['mode'],r['quarter'])))


def run(root,config_path,action):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-history-batch-qa-v1':raise ValueError('F3 QA contract required')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('QA input changed: '+path)
        pins[path]=sha;return body
    for path in [config_path,'src/delta_t1/experiments/financial_history_batch_qa.py','scripts/financial_history_batch_qa.py',
                 'src/delta_t1/experiments/financial_history_qa.py']:pin(path)
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
    profiles_path=c['profiles_result'];pm=json.loads(pin(profiles_path+'/manifest.json',c['profiles_manifest_sha256']))
    if contract['pins'].get(profiles_path+'/profiles.json')!=pm['profiles.json']:raise ValueError('QA profiles differ from frozen acquisition selection')
    profiles=json.loads(pin(profiles_path+'/profiles.json',pm['profiles.json']))
    findings=diagnose(rows,profiles,payloads,coverage)
    findings['summary'].update(input_mode=mode,acquisition_parser_errors=len(parser_errors),receipt_count=len(receipts),
        receipt_statuses=dict(Counter(r['status'] for r in source_receipts)),
        coverage_assessment='NOT_PERFORMED_PREVIEW' if mode=='FROZEN_RECEIPT_PREVIEW' else 'SEALED_ACQUISITION_SNAPSHOT')
    products={'summary.json':encoded(findings['summary']),'input-pins.json':encoded(pins),'acquisition-parser-errors.json':encoded(parser_errors)}
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
