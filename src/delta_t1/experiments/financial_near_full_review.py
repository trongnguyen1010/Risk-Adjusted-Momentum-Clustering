"""Audit one-year gaps; add complete, single-document reviewed reference vectors."""
import csv
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from .financial_api_input_review import csv_bytes
from .financial_history_documents import put
from ..features.financial_exploratory import REQUIRED, calculate_core
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside

VERSION = 'financial-near-full-review-v1'


def document_vectors(facts):
    groups = defaultdict(list); result = []
    for f in facts:
        if f['field'] in REQUIRED:
            groups[f['symbol'], f['year'], f['reviewed_scope'], f['pdf_sha256']].append(f)
    for (symbol, year, scope, sha), rows in sorted(groups.items()):
        fields = defaultdict(list)
        for r in rows: fields[r['field']].append(r)
        missing = sorted(REQUIRED-fields.keys()); status = 'COMPLETE_REVIEWED_DOCUMENT_VECTOR'
        if missing: status = 'HELD_MISSING_REVIEWED_FIELDS'
        elif scope not in ['CONSOLIDATED','ISSUER_NO_SUBSIDIARIES']: status = 'HELD_DOCUMENT_SCOPE'
        elif any(r['reviewed_unit']!='VND' for r in rows): status = 'HELD_DOCUMENT_UNITS'
        elif any(len({Decimal(r['reviewed_value']) for r in fields[f]}) != 1 for f in REQUIRED): status = 'HELD_REVIEWED_FIELD_CONFLICT'
        values = {f:rows[0]['reviewed_value'] for f,rows in fields.items()}
        calc = calculate_core(values) if status=='COMPLETE_REVIEWED_DOCUMENT_VECTOR' else {'values':None}
        if status=='COMPLETE_REVIEWED_DOCUMENT_VECTOR' and calc['values'] is None: status='HELD_DOCUMENT_FEATURE_VALIDITY'
        result.append(dict(symbol=symbol, year=year, scope=scope, pdf_sha256=sha, status=status,
            missing=missing, values=calc['values'] if status=='COMPLETE_REVIEWED_DOCUMENT_VECTOR' else None,
            input_values=values, evidence=rows))
    return result


def choose_document(vectors):
    """Do not pick a document/vintage priority even if multiple vectors agree."""
    eligible=[r for r in vectors if r['values'] is not None]
    if len(eligible)!=1: return None, 'NO_COMPLETE_DOCUMENT' if not eligible else 'MULTIPLE_DOCUMENT_VINTAGES_NO_SELECTION'
    return eligible[0], 'SINGLE_REVIEWED_DOCUMENT_REFERENCE'


def run(root, config_path):
    root=Path(root);c=json.loads(inside(root,config_path).read_bytes());pins={}
    if c.get('version')!=VERSION or c.get('scope')!='EXPLORATORY_REFERENCE_ONLY' or any(c.get(k) is not False for k in ['network_allowed','pdf_download_allowed','ocr_allowed','research_promotion_allowed']):
        raise ValueError('offline reference-only contract required')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('input hash changed: '+path)
        pins[path]=sha;return body
    def read(path,expected=None):return json.loads(pin(path,expected))
    def csvread(path,expected=None):return list(csv.DictReader(io.StringIO(pin(path,expected).decode('utf-8-sig'))))
    for path in [config_path,'scripts/financial_near_full_review.py','src/delta_t1/experiments/financial_near_full_review.py','src/delta_t1/features/financial_exploratory.py']:
        pin(path)
    sources={}
    for name in ['baseline','precision','verification']:
        s=c[name+'_result'];sources[name]=read(s['path']+'/manifest.json',s['manifest_sha256'])
    b=c['baseline_result']['path'];p=c['precision_result']['path'];v=c['verification_result']['path']
    features=csvread(b+'/features.csv',sources['baseline']['features.csv'])
    coverage=csvread(b+'/coverage-by-symbol.csv',sources['baseline']['coverage-by-symbol.csv'])
    remaining=csvread(b+'/remaining-document-review-candidates.csv',sources['baseline']['remaining-document-review-candidates.csv'])
    qas=csvread(p+'/qa-checks.csv',sources['precision']['qa-checks.csv'])
    facts=read(v+'/comparisons.json',sources['verification']['comparisons.json'])
    vpins=read(v+'/input-pins.json',sources['verification']['input-pins.json'])
    targets={(r['symbol'],json.loads(r['missing_years'])[0]):r for r in coverage if int(r['after_periods'])==9}
    if len(targets)!=412:raise ValueError('expected frozen 412 one-year gaps')
    # Revalidate only reviewed source documents for exact target symbols/years.
    facts=[f for f in facts if (f['symbol'],f['year']) in targets]
    for f in facts:
        pin(f['pdf_path'],f['pdf_sha256'])
        for path in [f.get('image_path'),f.get('source_package')]:
            if path:
                if path not in vpins:raise ValueError('reviewed source outside verification pin chain')
                pin(path,vpins[path])
    supplement=read(c['reviewed_supplement'])
    if supplement['review_method']!='AGENT_VISUAL_REVIEW_OF_CACHED_IMAGE' or supplement['new_ocr_pages']!=0:
        raise ValueError('cached visual supplement contract differs')
    for f in supplement['facts']:
        if (f['symbol'],f['year']) not in targets or f['field']!='operating_cash_flow' or f['review_status']!='REVIEWED_REFERENCE_ONLY' or f['interval']!='ANNUAL' or f['report_year']!=f['year'] or f['framework']!='VAS':
            raise ValueError('unexpected supplement fact')
        pin(f['pdf_path'],f['pdf_sha256']);pin(f['image_path'],f['image_sha256'])
        if sum(Decimal(n) for n in f['signed_components'])!=Decimal(f['reviewed_value']):
            raise ValueError('reviewed CFO component reconciliation differs')
        facts.append(f)
    vectors=document_vectors(facts);bykey=defaultdict(list)
    for r in vectors:bykey[r['symbol'],r['year']].append(r)
    existing={(r['registry_id'],int(r['year'])) for r in features};new=[];audit=[]
    qaby=defaultdict(list)
    for r in qas:qaby[r['symbol'],int(r['year'])].append(r)
    gaps={(r['symbol'],int(r['year'])):r for r in remaining}
    for key,owner in sorted(targets.items()):
        symbol,year=key;rid=owner['registry_id'];gap=gaps[key]
        selected,status=choose_document(bykey[key])
        held=[r for r in qaby[key] if r['status'].startswith('HELD') and r['difference']!='']
        row=dict(symbol=symbol,registry_id=rid,year=year,original_reasons=json.loads(gap['reasons']),
            failed_numeric_checks=held,reviewed_document_status=status,
            document_variants=[dict(scope=r['scope'],pdf_sha256=r['pdf_sha256'],status=r['status'],missing=r['missing']) for r in bykey[key]],
            cached_pdf_filename_hints=json.loads(gap['cached_same_year_filename_candidates']),
            restored=False,pdf_download_required_confirmed=False)
        if selected:
            if (rid,year) in existing:raise ValueError('reviewed vector would overwrite baseline')
            added=dict(symbol=symbol,registry_id=rid,year=year,provider_type='DOCUMENT_REFERENCE_NOT_API_PARTITION',
                **selected['values'],source_kind='SINGLE_DOCUMENT_REVIEWED_CORE_VECTOR',
                source_evidence=sorted({r['source_package'] for r in selected['evidence']}),
                pdf_sha256=selected['pdf_sha256'],document_scope=selected['scope'],
                evidence_field_ids=sorted({r.get('verification_id') or r['fact_id'] for r in selected['evidence']}),
                scope='DOCUMENT_REFERENCE_ONLY_NO_API_REPAIR_NO_PIT_PROMOTION',
                strict_pit_ready=False,research_ready=False,financial_features_allowed=False,published_at=None)
            new.append(added);row['restored']=True
        audit.append(row)
    dataset=sorted(features+new,key=lambda r:(r['registry_id'],int(r['year'])))
    keys={(r['registry_id'],int(r['year'])) for r in dataset}
    if len(keys)!=len(dataset):raise ValueError('duplicate observation key')
    updated=[]
    for r in coverage:
        years=sorted(y for rid,y in keys if rid==r['registry_id'])
        updated.append(dict(symbol=r['symbol'],registry_id=r['registry_id'],before_periods=int(r['after_periods']),
            after_periods=len(years),valid_years=years,missing_years=sorted(set(range(2016,2026))-set(years)),
            full10=len(years)==10,coverage_only_not_model_or_pit_acceptance=True))
    still=[r for r in remaining if (r['registry_id'],int(r['year'])) not in keys]
    summary=dict(status='COMPLETE_NEAR_FULL10_CACHED_REVIEW',targets_reviewed=len(audit),
        before_rows=len(features),after_rows=len(dataset),restored_rows=len(new),
        restored_symbols=[r['symbol'] for r in new],full10_before=459,
        full10_after=sum(r['after_periods']==10 for r in updated),
        remaining_one_year_gap_candidates=sum(r['after_periods']==9 for r in updated),
        remaining_regular_annual_gap_cases=len(still),
        target_reason_counts=dict(Counter(reason for r in audit for reason in r['original_reasons'])),
        target_document_status_counts=dict(Counter(r['reviewed_document_status'] for r in audit)),
        rows_by_year=dict(sorted(Counter(int(r['year']) for r in dataset).items())),
        reviewed_pdf_facts_added=len(supplement['facts']),new_pdf_downloads=0,new_ocr_pages=0,network_requests=0,
        confirmed_new_pdf_downloads_required=None,strict_pit_ready=False,research_ready=False,
        original_six_metric_goal='PARTIAL_UNCHANGED',model_recomputed=False)
    products={'summary.json':encoded(summary),'features.csv':csv_bytes(dataset),'coverage-by-symbol.csv':csv_bytes(updated),
        'near-full10-audit.json':encoded(audit),'near-full10-audit.csv':csv_bytes(audit),
        'document-vectors.json':encoded(vectors),'recovered-rows.csv':csv_bytes(new),
        'remaining-document-review-candidates.csv':csv_bytes(still),'input-pins.json':encoded(pins),'config.json':encoded(c)}
    manifest={n:digest(b) for n,b in products.items()};out=inside(root,c['output_root'])/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    put(inside(root,c['report_root'])/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    return dict(summary,output=out.relative_to(root).as_posix())
