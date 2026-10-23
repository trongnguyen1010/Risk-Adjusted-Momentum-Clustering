"""Counterfactual presentation audit only. Never imports or accepts candidates."""
import argparse
import csv
import io
import json
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path
from .financial_history_documents import put,read
from .financial_pdf_pipeline import file_hash
from .financial_precision_review import evaluate
from .financial_api_input_review import csv_bytes
from ..features.financial_exploratory import calculate_core
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside

EXPENSES={'revenue_deductions','cost_of_goods_sold','finance_expense','interest_expense',
          'selling_expense','administrative_expense','other_expense','current_tax_expense'}

def hypothesis(values):
    """PDF-inspired hypothesis, NOT a provider-wide normalization contract."""
    if 'cost_of_goods_sold' not in values or Decimal(values['cost_of_goods_sold'])>=0:
        return dict(values),[]
    proposed=dict(values);changes=[]
    for field in sorted(EXPENSES|{'deferred_tax_expense'}):
        if field not in values:continue
        original=Decimal(values[field])
        value=-original if field=='deferred_tax_expense' else abs(original)
        if value!=original:
            proposed[field]=str(value);changes.append(dict(field=field,before=str(original),after=str(value)))
    return proposed,changes

def run(root,config_path):
    c=read(inside(root,config_path));pins={}
    if c['version']!='financial-presentation-sign-audit-v1' or c['acceptance_allowed'] is not False:
        raise ValueError('counterfactual-only audit required')
    def pin(path,sha=None):
        p=inside(root,path);actual=file_hash(p)
        if sha is not None and actual!=sha:raise ValueError('source changed: '+path)
        pins[path]=actual;return p.read_bytes()
    def js(path,sha=None):return json.loads(pin(path,sha))
    for path in [config_path,'src/delta_t1/experiments/financial_presentation_sign_audit.py',
        'scripts/financial_presentation_sign_audit.py','src/delta_t1/experiments/financial_precision_review.py',
        'src/delta_t1/experiments/financial_template_contract.py','src/delta_t1/features/financial_exploratory.py']:
        pin(path)
    roots={};manifests={}
    for domain,spec in c['sources'].items():
        roots[domain]=spec['path'];manifests[domain]=js(spec['path']+'/manifest.json',spec['manifest_sha256'])
    def table(domain,name):
        return list(csv.DictReader(io.StringIO(pin(roots[domain]+'/'+name,manifests[domain][name]).decode('utf-8-sig'))))
    coverage=table('baseline','coverage-by-symbol.csv');gaps=table('baseline','remaining-document-review-candidates.csv')
    one={r['registry_id'] for r in coverage if int(r['after_periods'])==9}
    targets=[r for r in gaps if r['registry_id'] in one]
    indexes={d:js(roots[d]+'/symbol-manifests.json',manifests[d]['symbol-manifests.json']) for d in ['api','template']}
    audit=[]
    for gap in targets:
        rid=gap['registry_id'];year=int(gap['year']);base=dict(symbol=gap['symbol'],registry_id=rid,year=year,
          original_reasons=json.loads(gap['reasons']),accepted=False,manual_review_required=True,
          strict_pit_ready=False,research_ready=False)
        record=dict(**base,status='NOT_A_PRESENTATION_SIGN_CANDIDATE',counterfactual_gate_pass=False)
        # No attempt to choose between provider partitions or invent absent years.
        if any(r in gap['reasons'] for r in ['NO_ANNUAL_PARTITION','MULTIPLE_PROVIDER']):
            audit.append(record);continue
        parts={};values=defaultdict(dict);overlay=defaultdict(set);displacements=[]
        for domain in ['api','template']:
            spec=indexes[domain][rid];manifest=js(spec['path'],spec['sha256']);folder=Path(spec['path']).parent
            if domain=='api':
                path=(folder/'field-inputs.json').as_posix();fields=js(path,manifest['field-inputs.json'])
                for row in fields:
                    if row['year']==year and row['value'] is not None:values[row['provider_type']][row['field']]=row['value']
                record['api_evidence']=path
            else:
                parts=js((folder/'candidate-z-and-bridges.json').as_posix(),manifest['candidate-z-and-bridges.json'])
                changes=js((folder/'proposed-finance-fields.json').as_posix(),manifest['proposed-finance-fields.json'])
                for r in changes:
                    if r['year']==year:overlay[r['provider_type'],r['proposed_field']].add(Decimal(r['value']))
                local=js((folder/'input-pins.json').as_posix(),manifest['input-pins.json'])
                for path,sha in local.items():
                    if path.endswith('/displacements.json'):displacements.extend(js(path,sha))
        selected=[r for r in parts if r['year']==year]
        if len(selected)!=1:
            audit.append(record);continue
        provider=selected[0]['provider_type'];v=values[provider]
        for (pt,field),numbers in overlay.items():
            if pt==provider and len(numbers)==1:v[field]=str(next(iter(numbers)))
        proposed,changes=hypothesis(v)
        displaced=any(r['year']==year and r['annual_provider_type']==provider for r in displacements)
        before=evaluate(v,displaced);after=evaluate(proposed,displaced);features=calculate_core(proposed)
        record.update(provider_type=provider,changes=changes,displaced=displaced,before_checks=before['checks'],after_checks=after['checks'],
          counterfactual_gate_pass=bool(changes) and after['quality_gate'] and features['values'] is not None,
          counterfactual_ratios=features['values'] if changes else None,
          transformed_field_observations=[r for r in fields if r['year']==year and r['provider_type']==provider and r['field'] in {x['field'] for x in changes}])
        if changes:record['status']='COUNTERFACTUAL_PASS_REQUIRES_METHOD_REVIEW' if record['counterfactual_gate_pass'] else 'HELD_AFTER_COUNTERFACTUAL'
        audit.append(record)
    summary=dict(status='DIAGNOSTIC_ONLY_NO_ACCEPTANCE',targets=len(audit),
        status_counts=dict(Counter(r['status'] for r in audit)),hypothetical_new_full10=sum(r['counterfactual_gate_pass'] for r in audit),
        actual_new_full10=0,actual_new_rows=0,network_requests=0,pdf_downloads=0,ocr_pages=0,
        acceptance_allowed=False,manual_review_required=True,research_ready=False,strict_pit_ready=False)
    products={'summary.json':encoded(summary),'audit.json':encoded(audit),'audit.csv':csv_bytes(audit),'input-pins.json':encoded(pins)}
    manifest={name:digest(raw) for name,raw in products.items()};out=inside(root,c['output_root'])/'results'/digest(encoded(manifest))[:20]
    for name,raw in products.items():put(out/name,raw)
    put(out/'manifest.json',manifest)
    result=dict(path=out.relative_to(root).as_posix(),manifest_sha256=file_hash(out/'manifest.json'))
    put(inside(root,c['report_root'])/'presentation-audit-ref.json',result)
    print(json.dumps(dict(result=result,summary=summary)));return result

def cli(root):
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);args=p.parse_args();run(root,args.config)
