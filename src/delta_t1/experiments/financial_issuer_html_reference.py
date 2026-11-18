"""Single issuer HTML reference; captured web text is not original HTTP bytes/PIT."""
import csv,io,json,re
from collections import Counter
from pathlib import Path
from .financial_api_input_review import csv_bytes
from .financial_precision_review import evaluate
from .financial_history_documents import put
from ..features.financial_exploratory import REQUIRED,calculate_core
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside


def captured_lines(texts):
    result={}
    for text in texts:
        for number,text in re.findall(r'^L(\d+):\s?(.*)$',text,re.M):
            number=int(number)
            if number in result and result[number]!=text:raise ValueError('web captures disagree at source line')
            result[number]=text
    return result


def validate_review(review,lines):
    if (review['symbol']!='PLX' or review['year']!=2023 or review['scope']!='CONSOLIDATED'
        or review['unit']!='VND' or review['interval']!='ANNUAL_12_MONTHS'
        or review['source_url']!='https://www.petrolimex.com.vn/bctn-2023-baocaotaichinh.html'
        or review['strict_pit_ready'] is not False):raise ValueError('unexpected reviewed source contract')
    values={}
    for f in review['fields']:
        block='\n'.join(lines.get(n,'') for n in range(f['line_start'],f['line_end']+1))
        if f['localized_value'] not in block or 'Mã số '+f['source_code'] not in block:
            raise ValueError('reviewed field not found at captured source rows: '+f['field'])
        if f['field'] in REQUIRED and ('2023' not in block or 'VND' not in block):
            raise ValueError('core field year/unit proof absent')
        number=f['localized_value'].replace('.','').replace('(','-').replace(')','')
        if number!=f['value'] or f['field'] in values:raise ValueError('numeric transcription or duplicate field')
        values[f['field']]=f['value']
    if not evaluate(values)['quality_gate']:raise ValueError('existing precision/accounting/finance checks held issuer HTML')
    calc=calculate_core(values)
    if calc['values'] is None:raise ValueError('invalid core input vector')
    return calc['values']


def run(root,config_path):
    root=Path(root);c=json.loads(inside(root,config_path).read_bytes());pins={}
    if c.get('version')!='financial-issuer-html-reference-v1' or any(c.get(k) is not False for k in ['network_allowed','pdf_download_allowed','ocr_allowed','research_promotion_allowed']):
        raise ValueError('offline reference replay required')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('input hash differs: '+path)
        pins[path]=sha;return body
    def read(path,expected=None):return json.loads(pin(path,expected))
    def csvread(path,expected=None):return list(csv.DictReader(io.StringIO(pin(path,expected).decode('utf-8-sig'))))
    for p in [config_path,'scripts/financial_issuer_html_reference.py','src/delta_t1/experiments/financial_issuer_html_reference.py','src/delta_t1/experiments/financial_precision_review.py','src/delta_t1/features/financial_exploratory.py']:
        pin(p)
    review=read(c['review'])
    first=pin(c['captures'][0]).decode('utf-8-sig').split('BÁO CÁO THƯỜNG NIÊN - COTECCONS')[0]
    second=pin(c['captures'][1]).decode('utf-8-sig')
    values=validate_review(review,captured_lines([first,second]))
    source=c['baseline_result'];base=source['path'];m=read(base+'/manifest.json',source['manifest_sha256'])
    features=csvread(base+'/features.csv',m['features.csv']);coverage=csvread(base+'/coverage-by-symbol.csv',m['coverage-by-symbol.csv'])
    gaps=csvread(base+'/remaining-document-review-candidates.csv',m['remaining-document-review-candidates.csv'])
    member=next(r for r in coverage if r['symbol']=='PLX');rid=member['registry_id']
    if int(member['after_periods'])!=9 or json.loads(member['missing_years'])!=[2023]:raise ValueError('not the expected single gap')
    if any(r['registry_id']==rid and int(r['year'])==2023 for r in features):raise ValueError('no overwrite allowed')
    new=dict(symbol='PLX',registry_id=rid,year=2023,provider_type='ISSUER_HTML_REFERENCE_NOT_API_PARTITION',
        **values,source_kind='SINGLE_ISSUER_HTML_REVIEWED_CORE_VECTOR',source_evidence=c['review'],source_url=review['source_url'],
        source_capture_kind='WEB_TOOL_EXTRACT_NOT_ORIGINAL_HTTP_RESPONSE',original_html_response_sha256=None,
        source_warnings=review['source_warnings'],scope='ISSUER_HTML_REFERENCE_ONLY_NOT_PIT',
        financial_features_allowed=False,strict_pit_ready=False,research_ready=False,published_at=None)
    features.append(new)
    updated=[]
    for row in coverage:
        if row['registry_id']==rid:row=dict(row,after_periods=10,valid_years=list(range(2016,2026)),missing_years=[],full10=True)
        updated.append(row)
    remaining=[r for r in gaps if not (r['registry_id']==rid and int(r['year'])==2023)]
    summary=dict(status='COMPLETE_ISSUER_HTML_REFERENCE_REPLAY',full10_before=462,full10_after=463,
        rows_before=len(features)-1,rows_after=len(features),new_rows=1,restored_symbols=['PLX'],
        remaining_regular_annual_gap_cases=len(remaining),remaining_one_year_gap_candidates=sum(int(r['after_periods'])==9 for r in updated),
        rows_by_year=dict(sorted(Counter(int(r['year']) for r in features).items())),
        local_replay_network_requests=0,pdf_downloads=0,ocr_pages=0,external_web_tool_calls_in_source_discovery=3,
        external_original_response_bytes_unavailable=True,strict_pit_ready=False,research_ready=False,final_goal='PARTIAL')
    products={'summary.json':encoded(summary),'features.csv':csv_bytes(features),'coverage-by-symbol.csv':csv_bytes(updated),
        'recovered-rows.csv':csv_bytes([new]),'remaining-document-review-candidates.csv':csv_bytes(remaining),
        'input-pins.json':encoded(pins),'config.json':encoded(c)}
    manifest={n:digest(b) for n,b in products.items()};out=inside(root,c['output_root'])/'html-reference'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    put(inside(root,c['report_root'])/'dataset-result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    return dict(summary,output=out.relative_to(root).as_posix())
