"""Seeded independent document-audit targets; never select by PDF availability."""
from collections import defaultdict
from hashlib import sha256
from math import ceil
import json

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put
from .financial_history_qa import csv_body

FIELDS={'current_assets','total_assets','current_liabilities','total_liabilities','total_equity',
        'net_revenue','cost_of_goods_sold','gross_profit','operating_cash_flow'}
CHECKS={'ASSETS_EQUALS_CAPITAL','ASSETS_EQUALS_LIABILITIES_EQUITY','ASSET_PARTS','LIABILITY_PARTS','GROSS_PROFIT'}
ERAS=[(2013,2015),(2016,2019),(2020,2025)]


def choose_samples(candidates, checks, shifts, symbols, seed):
    groups=defaultdict(list);quality=defaultdict(dict)
    for row in candidates:
        key=(row['symbol'],row['year'],row['quarter'],row['mode'],row['provider_type'])
        if row['symbol'] in symbols and 2013<=row['year']<=2025 and row['mode'] in ['NAM','QUY']:
            groups[key].append(row)
    for check in checks:quality[tuple(check['period'])][check['check']]=check['status']
    bad_annual={(r['symbol'],r['year']) for r in shifts}
    clean=[]
    for key,rows in groups.items():
        if key[3]=='NAM' and key[:2] in bad_annual:continue
        if not FIELDS<={r['field'] for r in rows}:continue
        if not {'CDKT','KQKD','LCTT'}<={r['statement'] for r in rows}:continue
        if any(quality[key].get(name)!='RAW_EQUALITY' for name in CHECKS):continue
        clean.append((key,rows))
    rank=lambda value:sha256((seed+'|'+str(value)).encode()).hexdigest()
    selected=sorted(symbols,key=lambda s:rank(('issuer',s)))[:min(len(symbols),max(3,ceil(.05*len(symbols))))]
    samples=[]
    for issuer_index,symbol in enumerate(selected):
        for mode_index,mode in enumerate(['NAM','QUY']):
            preferred=ERAS[(issuer_index+mode_index)%len(ERAS)]
            available=[item for item in clean if item[0][0]==symbol and item[0][3]==mode]
            preferred_rows=[item for item in available if preferred[0]<=item[0][1]<=preferred[1]]
            choices=preferred_rows or available
            if not choices:
                samples.append(dict(symbol=symbol,mode=mode,status='NO_ARITHMETIC_CLEAN_COHORT',preferred_era=list(preferred)))
                continue
            key,rows=min(choices,key=lambda item:rank(('period',item[0])))
            sample_id=digest(encoded(dict(seed=seed,key=key)))[:20]
            samples.append(dict(id=sample_id,symbol=symbol,year=key[1],quarter=key[2],mode=mode,
                                provider_type=key[4],preferred_era=list(preferred),
                                preferred_era_present=bool(preferred_rows),status='INDEPENDENT_DOCUMENT_REVIEW_PENDING',
                                source_pins={r['source_path']:r['source_sha256'] for r in rows},
                                template_sha256=sorted({r['template_sha256'] for r in rows}),
                                mapped_fields=sorted({r['field'] for r in rows}),
                                cashflow_duration='REQUIRES_PDF_PERIOD_REVIEW; not assumed standalone quarter',
                                unit_scope_vintage_status='CANDIDATES_ONLY; arithmetic pass is not semantic acceptance'))
    return samples,len(clean)


def run(root,config_path,action):
    config=read(inside(root,config_path));pins={}
    if config.get('version')!='financial-history-audit-plan-v1' or len(config['symbols'])>20:
        raise ValueError('bounded audit-plan contract required')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('audit input changed: '+path)
        pins[path]=sha;return raw
    pin(config_path)
    for p in ['src/delta_t1/experiments/financial_history_audit_plan.py','scripts/financial_history_audit_plan.py']:
        pin(p)
    qa=config['qa_result'];manifest=json.loads(pin(qa+'/manifest.json',config['qa_manifest_sha256']))
    def qa_product(name):return pin(qa+'/'+name,manifest[name])
    candidates=[json.loads(line) for line in qa_product('mapped_candidates.jsonl').splitlines()]
    checks=json.loads(qa_product('accounting_checks.json'));shifts=json.loads(qa_product('possible_row_displacements.json'))
    samples,qualified=choose_samples(candidates,checks,shifts,config['symbols'],config['seed'])
    bundle=config['reviewed_bundle'];bm=json.loads(pin(bundle+'/manifest.json',config['reviewed_bundle_manifest_sha256']))
    facts=json.loads(pin(bundle+'/facts.json',bm['facts.json']))
    baseline=config['baseline_result'];baseline_manifest=json.loads(pin(baseline+'/manifest.json',config['baseline_manifest_sha256']))
    facts+=json.loads(pin(baseline+'/reviewed-inputs.json',baseline_manifest['reviewed-inputs.json']))
    for sample in samples:
        possible=defaultdict(list)
        for fact in facts:
            if (fact['symbol']!=sample['symbol'] or fact['year']!=sample.get('year')):continue
            if sample['mode']=='NAM' and fact.get('interval'):continue
            if sample['mode']=='QUY' and fact.get('quarter')!=sample.get('quarter'):continue
            possible[fact['provenance']['pdf_sha256']].append(fact)
        sample['comparison_document_candidates']=[dict(pdf_sha256=sha,pdf_path=rows[0]['provenance']['pdf_path'],
            reviewed_fields=sorted({r['field'] for r in rows}),scopes=sorted({r['scope'] for r in rows}),
            source_report_years=sorted({str(r.get('source_report_year','UNKNOWN')) for r in rows}),
            role='CACHE_COMPARISON_LEAD_NOT_AUDIT_PASS_OR_ORIGINAL_VINTAGE_PROOF') for sha,rows in sorted(possible.items())]
    summary=dict(status='AUDIT_PENDING',qualified_raw_arithmetic_cohorts=qualified,selected_issuers=sorted({r['symbol'] for r in samples}),
                 required_document_reviews=len(samples),completed_independent_audits=0,batch20_allowed=False,
                 financial_features_allowed=False,seed=config['seed'],
                 reason='Independent seeded annual/quarter audit must be completed; earlier targeted gap reviews do not replace these samples')
    products={'summary.json':encoded(summary),'audit-tasks.json':encoded(samples),'audit-tasks.csv':csv_body(samples),'input-pins.json':encoded(pins)}
    hashes={n:digest(raw) for n,raw in products.items()};out=inside(root,config['output_root'])/digest(encoded(hashes))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=hashes:raise ValueError('audit plan manifest differs')
        for name,sha in hashes.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('audit plan changed')
    else:
        for name,raw in products.items():put(out/name,raw)
        put(out/'manifest.json',hashes)
    return dict(summary,status='VERIFIED_PLAN_ONLY' if action=='verify' else summary['status'],output=out.relative_to(root).as_posix())
