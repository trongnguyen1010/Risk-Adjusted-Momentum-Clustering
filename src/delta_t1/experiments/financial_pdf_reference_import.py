"""Import explicitly reviewed single-PDF vectors; never repair an API partition."""
import csv
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from .financial_api_input_review import accounting, FORMULAS, csv_bytes
from .financial_template_contract import finance_bridge
from .financial_precision_review import residual_decision, BRIDGE_FIELDS
from .financial_near_full_review import document_vectors, choose_document
from .financial_direct_cashflow_review import longest_run
from .financial_history_documents import put
from ..features.financial_exploratory import REQUIRED
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside


def validate_review(root, r, pin):
    if r['review_status'] != 'REVIEWED_REFERENCE_ONLY' or r['review_method'] != 'AGENT_VISUAL_REVIEW_WITH_PINNED_OCR':
        raise ValueError('explicit visual review receipt required')
    if r['interval'] != 'ANNUAL' or r['report_year'] != r['year'] or r['unit'] != 'VND' or r['scope'] not in ['CONSOLIDATED', 'ISSUER_NO_SUBSIDIARIES']:
        raise ValueError('year/interval/unit/scope review mismatch')
    pin(r['pdf_path'],r['pdf_sha256'])
    values = {}; facts = []
    for f in r['fields']:
        field = f['field']
        if field in values or type(f['value']) is bool or not Decimal(str(f['value'])).is_finite():
            raise ValueError('duplicate/invalid reviewed field')
        if f['column_year'] != r['year'] or not f['visual_locator'] or not f['column_label']:
            raise ValueError('current-year column review required')
        job = json.loads(pin(f['ocr_receipt'],f['ocr_receipt_sha256']))
        if job['job']['pdf_sha256'] != r['pdf_sha256'] or job['job']['pdf_page'] != f['pdf_page'] or job['status'] != 'OCR_CANDIDATE_ONLY':
            raise ValueError('OCR source/year/page chain mismatch')
        pin(job['job']['image_path'],job['job']['image_sha256'])
        if job['job']['pdf_path'] != r['pdf_path']:
            raise ValueError('review mixes document sources')
        values[field] = str(f['value'])
        facts.append(dict(symbol=r['symbol'],year=r['year'],field=field,reviewed_value=str(f['value']),reviewed_scope=r['scope'],reviewed_unit=r['unit'],pdf_sha256=r['pdf_sha256'],evidence=f))
    if not REQUIRED <= values.keys():
        raise ValueError('all8 reviewed core inputs required')
    if r.get('cfo_signed_components') and sum(Decimal(str(n)) for n in r['cfo_signed_components']) != Decimal(values['operating_cash_flow']):
        raise ValueError('reviewed CFO component reconciliation differs')
    qa = []
    for check, (_, lhs, rhs) in zip(accounting(values), FORMULAS):
        terms = [values[k] for k in [lhs,*rhs] if k in values]
        qa.append(dict(check,precision_status=residual_decision(check['difference'],terms)))
    bridge = finance_bridge(values)
    qa.append(dict(check='FINANCE_BRIDGE',difference=bridge['difference'],precision_status=residual_decision(bridge['difference'],[values[k] for k in BRIDGE_FIELDS if k in values])))
    if any(x['difference'] is not None and x['precision_status'].startswith('HELD') for x in qa):
        raise ValueError('observed material PDF accounting mismatch')
    vector, status = choose_document(document_vectors(facts))
    if vector is None:
        raise ValueError(status)
    return vector, qa


def run(root, config_path):
    c=json.loads(inside(root,config_path).read_bytes());pins={}
    if c['version'] != 'financial-pdf-reference-import-v1' or c['network_allowed'] is not False or c['research_promotion_allowed'] is not False:
        raise ValueError('offline reference-only import required')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and expected!=sha:raise ValueError('source changed: '+path)
        pins[path]=sha;return body
    for path in [config_path,'src/delta_t1/experiments/financial_pdf_reference_import.py','scripts/financial_pdf_reference_import.py',
                 'src/delta_t1/experiments/financial_near_full_review.py','src/delta_t1/features/financial_exploratory.py',
                 'src/delta_t1/experiments/financial_api_input_review.py','src/delta_t1/experiments/financial_precision_review.py',
                 'src/delta_t1/experiments/financial_template_contract.py','src/delta_t1/experiments/financial_direct_cashflow_review.py']:
        pin(path)
    b=c['baseline'];m=json.loads(pin(b['path']+'/manifest.json',b['manifest_sha256']))
    def table(name):return list(csv.DictReader(io.StringIO(pin(b['path']+'/'+name,m[name]).decode('utf-8-sig'))))
    features=table('features.csv');coverage=table('coverage-by-symbol.csv');gaps=table('remaining-document-review-candidates.csv')
    reviews=json.loads(pin(c['reviews']))['reviews'];keys={(r['registry_id'],int(r['year'])) for r in features}
    gapkeys={(r['registry_id'],int(r['year'])) for r in gaps}
    coverage_by_id={r['registry_id']:r for r in coverage};new=[];qa_rows=[]
    for review in reviews:
        key=review['registry_id'],review['year']
        if key in keys or key not in gapkeys or coverage_by_id[key[0]]['symbol']!=review['symbol']:
            raise ValueError('review target is not a unique unresolved baseline period')
        vector,qa=validate_review(root,review,pin)
        qa_rows.extend(dict(symbol=review['symbol'],year=review['year'],**r) for r in qa)
        new.append(dict(symbol=review['symbol'],registry_id=review['registry_id'],year=review['year'],provider_type='REVIEWED_PDF_REFERENCE_NOT_API_PARTITION',
            **vector['values'],source_evidence=c['reviews'],source_kind='SINGLE_DOCUMENT_REVIEWED_CORE_VECTOR',pdf_path=review['pdf_path'],pdf_sha256=review['pdf_sha256'],
            scope=review['scope'],unit='VND',qa_policy='financial-near-full-review-v1:document_vectors',recovery_policy=c['version'],published_at=None,
            strict_pit_ready=False,research_ready=False,financial_features_allowed=False))
        keys.add(key)
    dataset=sorted(features+new,key=lambda r:(r['registry_id'],int(r['year'])))
    if len({(r['registry_id'],int(r['year'])) for r in dataset})!=len(dataset):raise ValueError('duplicate dataset key')
    years=defaultdict(set)
    for r in dataset:years[r['registry_id']].add(int(r['year']))
    nextcov=[]
    for row in coverage:
        yy=years[row['registry_id']]
        nextcov.append(dict(symbol=row['symbol'],registry_id=row['registry_id'],before_periods=int(row['after_periods']),after_periods=len(yy),valid_years=sorted(yy),missing_years=sorted(set(range(2016,2026))-yy),longest_consecutive_annual_periods=longest_run(yy),full10=len(yy)==10,coverage_only_not_model_or_pit_acceptance=True))
    remaining=[r for r in gaps if (r['registry_id'],int(r['year'])) not in keys]
    summary=dict(status='COMPLETE_REVIEWED_REFERENCE_IMPORT_GOAL_PARTIAL',rows_before=len(features),rows_after=len(dataset),new_rows=len(new),full10_before=sum(int(r['after_periods'])==10 for r in coverage),full10_after=sum(r['full10'] for r in nextcov),distinct_candidates=sum(bool(v) for v in years.values()),remaining_one_year_gap_candidates=sum(r['after_periods']==9 for r in nextcov),remaining_regular_annual_gap_cases=len(remaining),consecutive_history_counts={str(n):sum(longest_run(v)>=n for v in years.values()) for n in [3,5,8,10]},min_period_counts={str(n):sum(len(v)>=n for v in years.values()) for n in [3,5,8,10]},rows_by_year=dict(sorted(Counter(int(r['year']) for r in dataset).items())),local_replay_network_requests=0,pdf_downloads_in_import=0,strict_pit_ready=False,research_ready=False)
    products={'summary.json':encoded(summary),'features.csv':csv_bytes(dataset),'recovered-rows.csv':csv_bytes(new),'coverage-by-symbol.csv':csv_bytes(nextcov),'remaining-document-review-candidates.csv':csv_bytes(remaining),'review-qa.json':encoded(qa_rows),'input-pins.json':encoded(pins),'config.json':encoded(c)}
    manifest={n:digest(v) for n,v in products.items()};out=inside(root,c['output_root'])/'results'/digest(encoded(manifest))[:20]
    for n,v in products.items():put(out/n,v)
    put(out/'manifest.json',encoded(manifest))
    result=dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest(encoded(manifest)))
    put(inside(root,c['report_root'])/'dataset-result-ref.json',encoded(result))
    print(json.dumps(dict(result=result,summary=summary)));return result
