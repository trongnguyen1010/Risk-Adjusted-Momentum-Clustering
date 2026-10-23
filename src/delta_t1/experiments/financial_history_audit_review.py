"""Exact field audit of seeded cohorts; never promotes provider candidates."""
from decimal import Decimal
import json

from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read, put
from .financial_history_audit_plan import FIELDS


def compare(sample, candidates, review):
    if review['sample_id'] != sample['id'] or review['symbol'] != sample['symbol']:
        raise ValueError('review does not belong to seeded sample')
    if (review['year'],review['quarter'],review['mode']) != (sample['year'],sample['quarter'],sample['mode']):
        raise ValueError('review period differs')
    if review['currency'] != 'VND' or review['scope'] not in ['CONSOLIDATED','COMPANY_REPORTED','ISSUER_NO_SUBSIDIARIES']:
        raise ValueError('explicit document unit/scope required')
    if not review.get('scope_evidence') or review['source_report_year'] != sample['year']:
        raise ValueError('original report-year/scope proof required for this audit')
    facts=review['fields']
    if len(facts)!=len(FIELDS) or {r['field'] for r in facts}!=FIELDS:
        raise ValueError('all nine distinct audit fields required')
    rows=[]
    for fact in facts:
        if type(fact['pdf_page']) is not int or fact['pdf_page']<1 or not fact.get('row_label'):
            raise ValueError('physical page and label required')
        expected_kind='INSTANT' if fact['field'] in {'current_assets','total_assets','current_liabilities','total_liabilities','total_equity'} else ('ANNUAL' if sample['mode']=='NAM' else 'QUARTER_STANDALONE')
        # Quarterly cash flow may be YTD; this must be explicit, never silently annualized.
        if fact['period_kind'] != expected_kind and not (sample['mode']=='QUY' and fact['field']=='operating_cash_flow' and fact['period_kind']=='YTD'):
            raise ValueError('explicit compatible period kind required')
        source=[r for r in candidates if (r['symbol'],r['year'],r['quarter'],r['mode'],r['provider_type'],r['field']) == (sample['symbol'],sample['year'],sample['quarter'],sample['mode'],sample['provider_type'],fact['field'])]
        if len(source)!=1:raise ValueError('ambiguous/missing provider field')
        if (source[0].get('provider_raw_unit')!='VND' or source[0].get('unit_multiplier')!='1'
                or source[0].get('unit_status')!='RAW_VND_PROVIDER_DISPLAY_CONTRACT_REFERENCE'
                or source[0].get('unit_value')!=source[0]['value']):
            raise ValueError('pinned provider VND-unit evidence required')
        left=Decimal(source[0]['value']);right=Decimal(fact['value'])
        if not left.is_finite() or not right.is_finite():raise ValueError('finite values required')
        rows.append(dict(field=fact['field'],api_value=str(left),pdf_value=str(right),difference=str(left-right),
                         pdf_page=fact['pdf_page'],period_kind=fact['period_kind'],status='MATCH' if left==right else 'CONFLICT'))
    return dict(sample_id=sample['id'],symbol=sample['symbol'],year=sample['year'],quarter=sample['quarter'],mode=sample['mode'],
                status='DOCUMENT_FIELD_AUDIT_MATCH_REFERENCE_ONLY' if all(r['status']=='MATCH' for r in rows) else 'DOCUMENT_FIELD_AUDIT_CONFLICT',
                fields=rows,scope=review['scope'],provider_type=sample['provider_type'],
                pdf_path=review.get('pdf_path'),pdf_sha256=review.get('pdf_sha256'),
                source_anomalies=review.get('source_anomalies',[]),
                provider_scope_accepted=False,accepted_facts=0,pit_eligible=False)


def quarantine_rows(results):
    rows=[]
    for result in results:
        for field in result['fields']:
            if field['status']!='CONFLICT':continue
            rows.append(dict(symbol=result['symbol'],year=result['year'],quarter=result['quarter'],
                             mode=result['mode'],provider_type=result['provider_type'],field=field['field'],
                             api_value=field['api_value'],pdf_value=field['pdf_value'],difference=field['difference'],
                             pdf_page=field['pdf_page'],pdf_sha256=result['pdf_sha256'],sample_id=result['sample_id'],
                             reason='EXACT_SOURCE_DIFFERENCE_REVIEW_REQUIRED',accepted=False,automatic_override=False))
    return sorted(rows,key=lambda r:(r['symbol'],r['year'],r['quarter'],r['mode'],r['provider_type'],r['field']))


def run(root, config_path, action):
    config=read(inside(root,config_path));pins={}
    if config.get('version')!='financial-history-audit-review-v1':raise ValueError('audit review version required')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('changed audit input: '+path)
        pins[path]=sha;return raw
    pin(config_path)
    for path in ['src/delta_t1/experiments/financial_history_audit_review.py','src/delta_t1/experiments/financial_history_audit_plan.py','scripts/financial_history_audit_review.py']:pin(path)
    plan=config['audit_plan'];pm=json.loads(pin(plan+'/manifest.json',config['audit_plan_manifest_sha256']))
    samples=json.loads(pin(plan+'/audit-tasks.json',pm['audit-tasks.json']))
    qa=config['qa_result'];qm=json.loads(pin(qa+'/manifest.json',config['qa_manifest_sha256']))
    pin(qa+'/mapped_candidates.jsonl',qm['mapped_candidates.jsonl'])
    units=config['unit_overlay'];um=json.loads(pin(units+'/manifest.json',config['unit_overlay_manifest_sha256']))
    candidates=[json.loads(r) for r in pin(units+'/unit-candidates.jsonl',um['unit-candidates.jsonl']).splitlines()]
    results=[];seen=set()
    for item in config['reviews']:
        review=json.loads(pin(item['path'],item['sha256']));sample=next(r for r in samples if r.get('id')==review['sample_id'])
        if review['sample_id'] in seen:raise ValueError('duplicate sample review')
        seen.add(review['sample_id']);pin(review['pdf_path'],review['pdf_sha256'])
        for evidence in review['render_pins']:pin(evidence['path'],evidence['sha256'])
        results.append(compare(sample,candidates,review))
    pending=[r for r in samples if r.get('id') not in seen]
    quarantined=quarantine_rows(results)
    summary=dict(status='PARTIAL' if pending else 'AUDITED_WITH_CONFLICTS' if quarantined else 'AUDITED_REFERENCE_ONLY',completed_document_field_audits=len(results),
                 matching_document_field_audits=sum(r['status']=='DOCUMENT_FIELD_AUDIT_MATCH_REFERENCE_ONLY' for r in results),
                 required_document_reviews=len(samples),pending_document_reviews=len(pending),
                 compared_fields=sum(len(r['fields']) for r in results),conflicting_fields=len(quarantined),
                 maximum_absolute_difference=str(max((abs(Decimal(r['difference'])) for r in quarantined),default=Decimal(0))),
                 accepted_facts=0,batch20_allowed=False,financial_features_allowed=False,strict_pit_metrics=0)
    products={'summary.json':encoded(summary),'reviews.json':encoded(results),'pending.json':encoded(pending),
              'candidate-quarantine.json':encoded(quarantined),'input-pins.json':encoded(pins)}
    manifest={name:digest(raw) for name,raw in products.items()};out=inside(root,config['output_root'])/digest(encoded(manifest))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=manifest:raise ValueError('audit review manifest changed')
        for name,sha in manifest.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('audit result changed')
    else:
        for name,raw in products.items():put(out/name,raw)
        put(out/'manifest.json',manifest)
    return dict(summary,output=out.relative_to(root).as_posix())
