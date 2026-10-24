"""Lossless diagnostic adapter: ambiguous codes never acquire positional labels."""
from collections import Counter,defaultdict
from decimal import Decimal,InvalidOperation
import json

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put


def parse_candidates(body,task,source_path,source_sha):
    if digest(body)!=source_sha:raise ValueError('candidate source hash differs')
    p=json.loads(body,parse_float=Decimal)
    if p.get('isSuccess') is not True:raise ValueError('unsuccessful provider response')
    v=p['value'];template=v.get('templace',[]);groups=v.get('data',[])
    fingerprint=digest(json.dumps(template,ensure_ascii=False,sort_keys=True,default=str).encode())
    if task['statement']=='KQKD':template=[dict(code='KQKD',data=template)];groups=[dict(code='KQKD',data=groups)]
    definitions=defaultdict(list)
    for group in template:
        for index,row in enumerate(group.get('data',[])):
            definitions[(group['code'],row['code'])].append(dict(template_row_index=index,name=row['name'],number=row.get('number'),static=row.get('static')))
    if len({g['code'] for g in groups})!=len(groups):raise ValueError('ambiguous repeated data group')
    rows=[]
    for group in groups:
        if group['code']!=task['group']:continue
        for period_index,period in enumerate(group.get('data',[])):
            if period['symbol'].upper()!=task['symbol'].upper():raise ValueError('candidate issuer differs')
            year,quarter=period['year'],period['quater']
            if type(year) is not int or type(quarter) is not int or not 1900<=year<=2200 or not 0<=quarter<=4:
                raise ValueError('invalid fiscal header')
            codes=Counter(c['code'] for c in period.get('data',[]))
            for ordinal,cell in enumerate(period.get('data',[])):
                code=cell['code'];labels=definitions[(group['code'],code)];label=None
                if not str(code).strip():status='BLANK_CODE_QUARANTINED'
                elif len(labels)>1:status='DUPLICATE_TEMPLATE_CODE_QUARANTINED'
                elif codes[code]>1:status='DUPLICATE_OBSERVATION_CODE_QUARANTINED'
                elif not labels:status='UNMAPPED_CODE_QUARANTINED'
                else:status='UNIQUE_CODE_LABEL_CANDIDATE';label=labels[0]['name']
                raw=cell.get('value');number=None;value_status='MISSING'
                if raw is not None and not isinstance(raw,bool) and str(raw).strip() not in ['', '-', '—']:
                    try:
                        number=Decimal(str(raw))
                        if not number.is_finite():raise InvalidOperation
                        number=str(number);value_status='NUMERIC_CANDIDATE'
                    except InvalidOperation:number=None;value_status='INVALID_NUMERIC_QUARANTINED'
                elif isinstance(raw,bool):value_status='BOOLEAN_QUARANTINED'
                rows.append(dict(symbol=task['symbol'],statement=task['statement'],mode=task['mode'],group=group['code'],
                    year=year,quarter=quarter,provider_type=period.get('type'),provider_header=period.get('time'),
                    period_occurrence=period_index,raw_cell_ordinal=ordinal,raw_code=code,
                    label=label,label_candidates=labels,mapping_status=status,raw_value=raw,value=number,value_status=value_status,
                    provider_unit=v.get('unit'),template_sha256=fingerprint,source_path=source_path,source_sha256=source_sha,
                    interval='ANNUAL' if task['mode']=='NAM' else 'INTERVAL_UNRESOLVED' if task['statement']=='LCTT' else 'QUARTER_UNVERIFIED',
                    ordinal_role='RAW_PROVENANCE_ONLY_NEVER_FIELD_ALIGNMENT',unit_status='UNVERIFIED',scope_status='UNRESOLVED',
                    accepted=False,pit_ready=False))
    # Decimal raw tokens are strings, with original exact JSON bytes retained by hash.
    return json.loads(json.dumps(rows,default=str,ensure_ascii=False))


def run(root,config_path,action):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-template-candidates-v1':raise ValueError('candidate adapter contract required')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('adapter evidence changed: '+path)
        pins[path]=sha;return raw
    for path in [config_path,'src/delta_t1/experiments/financial_template_candidates.py','scripts/financial_template_candidates.py']:pin(path)
    result=c['probe_result'];manifest=json.loads(pin(result+'/manifest.json',c['probe_manifest_sha256']))
    receipts=json.loads(pin(result+'/receipts.json',manifest['receipts.json']));rows=[];errors=[];catalogue=[]
    if len(receipts)!=180 or len({r['task']['id'] for r in receipts})!=180:raise ValueError('exact completed probe inventory required')
    for r in receipts:
        if r['status']!='ACQUIRED':errors.append(dict(task=r['task'],reason=r['status']));continue
        raw=pin(r['path'],r['sha256'])
        try:
            parsed=parse_candidates(raw,r['task'],r['path'],r['sha256']);rows.extend(parsed)
            catalogue.append(dict(task=r['task'],template_sha256=sorted({p['template_sha256'] for p in parsed}),
                cells=len(parsed),mapping_statuses=dict(Counter(p['mapping_status'] for p in parsed)),
                strict_probe_inspection=r['inspection']['status']))
        except (ValueError,KeyError,TypeError) as error:errors.append(dict(task=r['task'],reason=str(error)))
    statuses=dict(Counter(r['mapping_status'] for r in rows));quarantined=[r for r in rows if r['mapping_status']!='UNIQUE_CODE_LABEL_CANDIDATE' or r['value_status'] in ['INVALID_NUMERIC_QUARANTINED','BOOLEAN_QUARANTINED']]
    summary=dict(status='CANDIDATE_ADAPTER_REPLAYED_WITH_QUARANTINE' if not errors else 'PARTIAL_ADAPTER_REPLAY',
        tasks=len(receipts),parsed_tasks=len(catalogue),parser_errors=len(errors),candidate_cells=len(rows),mapping_statuses=statuses,
        quarantined_cells=len(quarantined),original_strict_parser_review_tasks=sum(r['inspection']['status']=='PARSE_REVIEW_REQUIRED' for r in receipts),
        numeric_acceptance_allowed=False,full_history_acquisition_allowed=False,financial_features_allowed=False,research_ready=False)
    products={'summary.json':encoded(summary),'template-catalogue.json':encoded(catalogue),'parser-errors.json':encoded(errors),
        'quarantine.json':encoded(quarantined),'input-pins.json':encoded(pins)}
    # JSONL records must each remain a single physical line.
    products['candidates.jsonl']=b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode() for r in rows)
    m={name:digest(raw) for name,raw in products.items()};out=inside(root,c['output_root'])/digest(encoded(m))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=m:raise ValueError('candidate adapter manifest differs')
        for name,sha in m.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('candidate adapter result changed')
    else:
        for name,raw in products.items():put(out/name,raw)
        put(out/'manifest.json',m)
    return dict(summary,output=out.relative_to(root).as_posix())
