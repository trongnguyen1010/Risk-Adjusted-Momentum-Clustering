"""Audit cached source evidence for annual holes; never converts quarters to years."""
import csv
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .financial_history_documents import put
from .financial_api_input_review import csv_bytes
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.cafef_financial_deep import report_url
from ..ingestion.financial_batch_evidence import inside
from ..features.financial_exploratory import REQUIRED

GROUPS={'CDKT':['TN','NV'],'KQKD':['KQKD'],'LCTT':['HDKD','HDDT','HDTC']}
VERSION='financial-annual-gap-audit-v1'


def year_position(year, observed):
    years=set(observed)
    if not years:return 'NO_ANNUAL_HEADERS_OBSERVED'
    if year in years:return 'YEAR_PRESENT_IN_RAW_REQUIRES_REVIEW'
    if year<min(years):return 'BEFORE_EARLIEST_OBSERVED_ANNUAL'
    if year>max(years):return 'AFTER_LATEST_OBSERVED_ANNUAL'
    return 'BETWEEN_OBSERVED_ANNUAL_YEARS'


def headers(body, statement, group, symbol):
    payload=json.loads(body)
    if payload.get('isSuccess') is not True:raise ValueError('unsuccessful cached report')
    value=payload.get('value') or {};data=value.get('data',[])
    if statement!='KQKD':
        selected=[g for g in data if g.get('code')==group]
        if len(selected)>1:raise ValueError('ambiguous raw data group')
        data=selected[0].get('data',[]) if selected else []
    out=[]
    for p in data:
        if p.get('symbol','').upper()!=symbol:raise ValueError('raw issuer differs')
        if type(p.get('year')) is not int or type(p.get('quater')) is not int or not 0<=p['quater']<=4:
            raise ValueError('invalid raw period header')
        numeric=0
        for cell in p.get('data',[]):
            x=cell.get('value')
            if x is None or type(x) is bool:continue
            try:n=Decimal(str(x))
            except InvalidOperation:continue
            numeric+=n.is_finite()
        out.append(dict(year=p['year'],quarter=p['quater'],provider_type=p.get('type'),
            provider_header=p.get('time'),provider_content=p.get('content'),numeric_cells=numeric))
    return out


def numeric_value(value):
    if value is None or type(value) is bool:return False
    try:return Decimal(str(value)).is_finite()
    except InvalidOperation:return False


def legacy_state(rows):
    if not rows:return 'NO_MATCHING_LEGACY_ROWS'
    present={r['field'] for r in rows if r.get('field') in REQUIRED and numeric_value(r.get('raw_value'))}
    if not present:return 'MATCHED_EMPTY_PLACEHOLDER_COLUMNS'
    return 'COMPLETE_FIELDS_REQUIRE_UNIT_INTERVAL_VINTAGE_REVIEW' if REQUIRED<=present else 'PARTIAL_NUMERIC_LEGACY_FIELDS'


def quarter_group_coverage(rows):
    byq=defaultdict(set)
    for r in rows:
        if r['status']=='CANDIDATE_GROUPS_PRESENT' and r['mode']=='QUY':byq[int(r['quarter'])].add(r['statement'])
    return dict(q4_three_groups=byq[4]==set(GROUPS),
                all_four_quarters_three_groups=all(byq[q]==set(GROUPS) for q in [1,2,3,4]))


def run(root, config_path):
    root=Path(root);c=json.loads(inside(root,config_path).read_bytes());pins={}
    if c.get('version')!=VERSION or any(c.get(k) is not False for k in ['network_allowed','pdf_download_allowed','ocr_allowed','research_promotion_allowed']):
        raise ValueError('explicit offline no-promotion contract required')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('source changed: '+path)
        pins[path]=sha;return body
    def read(path,expected=None):return json.loads(pin(path,expected))
    def csvread(path,expected=None):return list(csv.DictReader(io.StringIO(pin(path,expected).decode('utf-8-sig'))))
    for path in [config_path,'scripts/financial_annual_gap_audit.py','src/delta_t1/experiments/financial_annual_gap_audit.py','src/delta_t1/ingestion/cafef_financial_deep.py']:
        pin(path)
    sources={}
    for name in ['baseline','qa','catalogue','legacy']:
        s=c[name+'_result'];sources[name]=read(s['path']+'/manifest.json',s['manifest_sha256'])
    b=c['baseline_result']['path'];q=c['qa_result']['path'];cat=c['catalogue_result']['path'];legacy=c['legacy_result']['path']
    coverage=csvread(b+'/coverage-by-symbol.csv',sources['baseline']['coverage-by-symbol.csv'])
    gaps=csvread(b+'/remaining-document-review-candidates.csv',sources['baseline']['remaining-document-review-candidates.csv'])
    ids={r['registry_id'] for r in coverage if int(r['after_periods'])==9}
    targets=[r for r in gaps if r['registry_id'] in ids and 'NO_ANNUAL_PARTITION_IN_ACQUIRED_PAGES' in json.loads(r['reasons'])]
    if len(targets)!=125:raise ValueError('expected frozen125 annual input gaps')
    keys={(r['symbol'],int(r['year'])) for r in targets}
    sm=read(q+'/symbol-manifests.json',sources['qa']['symbol-manifests.json'])
    qcoverage=csvread(q+'/coverage.csv',sources['qa']['coverage.csv'])
    quarters=defaultdict(list)
    for row in qcoverage:
        key=(row['symbol'],int(row['year']))
        if key in keys:quarters[key].append(row)
    del qcoverage
    links=read(cat+'/document-links.json',sources['catalogue']['document-links.json'])
    legacyrows=defaultdict(list)
    pin(legacy+'/candidates.jsonl',sources['legacy']['files']['candidates.jsonl'])
    for line in inside(root,legacy+'/candidates.jsonl').open(encoding='utf-8'):
        r=json.loads(line);key=(r['symbol'],r['year'])
        if key in keys and r['quarter']==0:
            legacyrows[key].append(r)
            pin(r['source_path'],r['source_sha256'])
    audit=[];receipts=[];periods=[];leads=[]
    for index,target in enumerate(sorted(targets,key=lambda r:r['symbol']),1):
        symbol=target['symbol'];year=int(target['year']);rid=target['registry_id'];entry=sm[rid]
        m=read(entry['path'],entry['sha256']);folder=Path(entry['path']).parent
        sp=read((folder/'input-pins.json').as_posix(),m['input-pins.json'])['sources']
        receipt_index=defaultdict(list)
        for path,sha in sp.items():
            if '/receipts/' in path:receipt_index[Path(path).stem].append((path,sha))
        annual=[];cumulative=[];seen=set();counts=Counter();missing_receipt_slots=0
        for mode in ['NAM','LUYKE']:
            for statement,groups in GROUPS.items():
                if mode=='LUYKE' and statement=='CDKT':continue
                for group in groups:
                    for page in range(1,6):
                        url=report_url(symbol,statement,mode,group,page);taskid=digest(url.encode())
                        matches=receipt_index[taskid]
                        if not matches:missing_receipt_slots+=1
                        for path,sha in matches:
                            receipt=read(path,sha);task=receipt['task']
                            if (task['symbol'],task['mode'],task['statement'],task['group'],task['page'],task['url'])!=(symbol,mode,statement,group,page,url):
                                raise ValueError('receipt task/url identity mismatch')
                            counts[receipt['status']]+=1;rec=receipt.get('record')
                            receipts.append(dict(symbol=symbol,target_year=year,mode=mode,statement=statement,group=group,page=page,status=receipt['status'],receipt_path=path,record_path=rec['path'] if rec else None))
                            if not rec:continue
                            if sp.get(rec['path'])!=rec['sha256']:raise ValueError('raw missing from source pin chain')
                            key=(mode,statement,group,rec['path'])
                            if key in seen:continue
                            seen.add(key);raw=pin(rec['path'],rec['sha256'])
                            hs=headers(raw,statement,group,symbol)
                            for h in hs:
                                item=dict(symbol=symbol,target_year=year,mode=mode,statement=statement,group=group,
                                    source_path=rec['path'],source_sha256=rec['sha256'],**h)
                                periods.append(item)
                                (annual if mode=='NAM' else cumulative).append(item)
        years={r['year'] for r in annual if r['quarter']==0 and r['numeric_cells']>0}
        hit=[r for r in annual if r['year']==year and r['numeric_cells']>0]
        lk=[r for r in cumulative if r['year']==year and r['numeric_cells']>0]
        quarter=quarter_group_coverage(quarters[symbol,year])
        old=legacyrows[symbol,year]
        observed=[r for r in links if r['symbol']==symbol and r.get('provider_year')==year and r.get('provider_quarter')==0 and r['status']=='OBSERVED_FINANCIAL_PDF_LINK_CANDIDATE']
        leads.extend(dict(r,target_registry_id=rid,download_authorized=False) for r in observed)
        audit.append(dict(symbol=symbol,registry_id=rid,year=year,position=year_position(year,years),
            raw_annual_years=sorted(years),target_numeric_annual_header_groups=len(hit),
            target_annual_headers=hit,target_numeric_luyke_header_groups=len(lk),target_luyke_headers=lk,
            **quarter,legacy_state=legacy_state(old),legacy_matching_rows=len(old),
            legacy_numeric_core_rows=sum(r.get('field') in REQUIRED and numeric_value(r.get('raw_value')) for r in old),
            annual_observed_pdf_urls=sorted({r['resolved_url'] for r in observed}),
            receipt_status_counts=dict(counts),missing_cached_receipt_slots=missing_receipt_slots,
            annual_input_status='RAW_PERIOD_REVIEW_REQUIRED' if hit else 'NO_NUMERIC_TARGET_YEAR_IN_PINNED_ANNUAL_RESPONSES',
            recovered=False,confirmed_pdf_downloads_required=None,strict_pit_ready=False,research_ready=False,
            next_action='REVIEW_INTERVAL_SCOPE_VINTAGE_BEFORE_ANY_QUARTER_AGGREGATION' if quarter['q4_three_groups'] else 'IDENTITY_AND_ORIGINAL_ANNUAL_SOURCE_LOOKUP_REQUIRED'))
        if index%25==0:print(json.dumps(dict(completed=index,total=len(targets))),flush=True)
    summary=dict(status='COMPLETE_CACHED_ANNUAL_GAP_AUDIT_GOAL_PARTIAL',targets=len(targets),
        position_counts=dict(Counter(r['position'] for r in audit)),
        target_year_counts=dict(sorted(Counter(r['year'] for r in audit).items())),
        cases_with_numeric_annual_headers=sum(bool(r['target_numeric_annual_header_groups']) for r in audit),
        cases_with_numeric_luyke_headers=sum(bool(r['target_numeric_luyke_header_groups']) for r in audit),
        cases_with_q4_three_groups=sum(r['q4_three_groups'] for r in audit),
        cases_with_all_four_quarters_three_groups=sum(r['all_four_quarters_three_groups'] for r in audit),
        legacy_state_counts=dict(Counter(r['legacy_state'] for r in audit)),
        cases_with_exact_annual_catalogue_links=sum(bool(r['annual_observed_pdf_urls']) for r in audit),
        unique_observed_annual_pdf_urls=len({r['resolved_url'] for r in leads}),
        restored_rows=0,full10_before=462,full10_after=462,baseline_dataset_unchanged=True,
        confirmed_new_pdf_downloads_required=None,network_requests=0,pdf_downloads=0,ocr_pages=0,
        strict_pit_ready=False,research_ready=False)
    products={'summary.json':encoded(summary),'target-audit.csv':csv_bytes(audit),'target-audit.json':encoded(audit),
        'cached-receipts.csv':csv_bytes(receipts),'raw-period-headers.csv':csv_bytes(periods),
        'observed-annual-document-leads.csv':csv_bytes(leads),'input-pins.json':encoded(pins),'config.json':encoded(c)}
    manifest={n:digest(body) for n,body in products.items()};out=inside(root,c['output_root'])/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    put(inside(root,c['report_root'])/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    return dict(summary,output=out.relative_to(root).as_posix())
