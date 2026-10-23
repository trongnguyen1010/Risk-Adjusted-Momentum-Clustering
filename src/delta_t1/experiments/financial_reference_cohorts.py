"""Recompute explicit reviewed report vintages without choosing a latest vintage."""
from collections import Counter,defaultdict
from decimal import Decimal,localcontext,InvalidOperation
from datetime import date
from hashlib import sha256
import json,csv,io

from ..features.financial_vas_reference import calculate_disclosed_basic_eps,REGISTRY
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put
from .financial_reviewed_batch import validate_fact,task_result,legacy_rows
from .financial_history_qa import csv_body

FAMILIES=['EPS','PE','PB','F_SCORE','M_SCORE','Z_SCORE']
EPS_BASES={'RESERVE_DEDUCTED_REPORTED_NOTE':'eps_adjusted_earnings_numerator',
           'REPORTED_UNESTIMATED_RESERVE_NOT_NORMALIZED':'reported_eps_numerator',
           'REPORTED_NOTE_NO_RESERVE_NORMALIZATION_CLAIM':'reported_eps_numerator'}


def snapshot_ratio(family,price,eps=None,equity=None,shares=None):
    if family not in ['PE','PB']:raise ValueError('unknown reported valuation family')
    REGISTRY.get('reported_basis_pe_reference' if family=='PE' else 'reported_basis_pb_reference')
    values=[price,eps] if family=='PE' else [price,equity,shares]
    try:
        if any(type(v) is bool for v in values):raise ValueError('boolean')
        nums=[Decimal(str(v)) for v in values]
        if any(not n.is_finite() or n<=0 for n in nums):raise ValueError('nonpositive or nonfinite valuation input')
        with localcontext() as ctx:
            ctx.prec=36
            value=nums[0]/nums[1] if family=='PE' else nums[0]*nums[2]/nums[1]
        return dict(value=str(value),status='REPORTED_BASIS_REFERENCE_CALCULATED')
    except (ValueError,InvalidOperation,ArithmeticError,TypeError):return dict(value=None,status='INVALID_VALUATION_INPUT')


def price_after_publication(price,publication):
    return bool(price and publication and date.fromisoformat(price['trade_date'])>date.fromisoformat(publication))


def dependency_dates(row,facts_by_id,publications):
    hashes=sorted({facts_by_id[fid]['provenance']['pdf_sha256'] for fid in row['dependency_ids']})
    unknown=[h for h in hashes if not publications.get(h)]
    complete=row['value'] is not None and bool(hashes) and not unknown
    return dict(all_financial_dependency_publication_dates_referenced=complete,
        unknown_dependency_publication_pdf_hashes=unknown,
        latest_financial_dependency_publication_date_reference=max(publications[h] for h in hashes) if complete else None)


def select_values(facts,cohort):
    primary=cohort['primary_pdf_sha256'];aux={(a['pdf_sha256'],a['field'],a['year']) for a in cohort.get('auxiliary_fields',[])}
    groups=defaultdict(list)
    for f in facts:
        if f['symbol']!=cohort['symbol'] or f.get('interval'):continue
        p=f['provenance']['pdf_sha256']
        if p==primary or (p,f['field'],f['year']) in aux:groups[f['field'],f['year']].append(f)
    values={};ids={};conflicts=[]
    for key,rs in groups.items():
        if len({(Decimal(r['value']),r['unit']) for r in rs})!=1:
            conflicts.append(dict(field=key[0],year=key[1],observations=rs));continue
        values[key]=rs[0]['value'];ids[key]=[r['id'] for r in rs]
    derivations=[]
    for year in [cohort['year'],cohort['year']-1]:
        keys=[('noncurrent_loans_and_finance_leases',year),('current_portion_original_long_term_debt',year)]
        if all(k in values for k in keys):
            key=('long_term_debt_including_current_portion',year);value=str(sum(Decimal(values[k]) for k in keys));sources=sum((ids[k] for k in keys),[])
            if key in values and Decimal(values[key])!=Decimal(value):
                conflicts.append(dict(field=key[0],year=year,status='EXPLICIT_TOTAL_DIFFERS_FROM_CLOSING_PARTS'));values.pop(key);ids.pop(key,None);continue
            values[key]=value;ids[key]=sorted(set(ids.get(key,[])+sources))
            derivations.append(dict(field=key[0],year=year,operation='SUM_EXPLICIT_CLOSING_CURRENT_AND_NONCURRENT_STOCKS',value=value,dependency_ids=ids[key]))
    return values,ids,conflicts,derivations


def compute_cohort(facts,cohort,price=None):
    if cohort.get('input_scope')!='CONSOLIDATED' or cohort.get('variant_clearance')!='EXISTING_NONFINANCIAL_REFERENCE_VARIANTS':
        raise ValueError('explicit existing consolidated reference variant clearance required')
    if cohort['eps_basis'] not in EPS_BASES or cohort['eps_numerator_field']!=EPS_BASES[cohort['eps_basis']]:
        raise ValueError('EPS basis/field not declared; no numerator aliasing')
    if cohort.get('period_months')!=12:raise ValueError('reviewed exact annual period required; no annualization')
    date.fromisoformat(cohort['fiscal_period_end'])
    values,ids,conflicts,derivations=select_values(facts,cohort);year=cohort['year'];symbol=cohort['symbol'];rows=[];checks=[]
    for y in sorted({k[1] for k in values}):
        for name,lhs,rhs in [('BALANCE','total_assets',['total_liabilities','total_equity']),('GROSS_PROFIT','net_revenue',['cost_of_goods_sold','gross_profit'])]:
            keys=[(f,y) for f in [lhs]+rhs]
            if all(k in values for k in keys):
                delta=Decimal(values[lhs,y])-sum(Decimal(values[f,y]) for f in rhs)
                if delta:raise ValueError('reviewed source accounting mismatch: '+name)
                checks.append(dict(year=y,check=name,difference=str(delta),passed=True))
    numerator=cohort['eps_numerator_field'];eps_keys=[(numerator,year),('weighted_average_basic_shares',year)]
    missing_eps=[dict(field=f,year=y) for f,y in eps_keys if (f,y) not in values]
    eps=calculate_disclosed_basic_eps(values.get((numerator,year)),values.get(('weighted_average_basic_shares',year)),12)
    if not missing_eps and ('vendor_basic_eps',year) in values:
        passed=Decimal(eps['rounded'])==Decimal(values['vendor_basic_eps',year]) if eps.get('rounded') is not None else False
        if not passed:raise ValueError('basic EPS rounding differs from disclosed note')
        checks.append(dict(year=year,check='ROUNDED_BASIC_EPS_MATCHES_DISCLOSED_NOTE',passed=True))
    eps_ids=sum((ids.get(k,[]) for k in eps_keys),[])
    for family in FAMILIES:
        if family=='EPS':
            row=dict(symbol=symbol,year=year,family=family,value=eps['value'],status=eps['status'],result=eps,missing_inputs=missing_eps,
                dependency_ids=eps_ids,eps_basis=cohort['eps_basis'],eps_numerator_field=numerator)
        elif family in ['PE','PB']:
            required=eps_keys if family=='PE' else [('total_equity',year),('noncontrolling_equity',year),('common_shares',year)]
            missing=[dict(field=f,year=y) for f,y in required if (f,y) not in values]
            if price is None:missing.append(dict(field='REVIEWED_RAW_PRICE_AND_SNAPSHOT_BASIS',year=year))
            if missing:
                row=dict(symbol=symbol,year=year,family=family,value=None,status='MISSING_REVIEWED_VALUATION_INPUTS',missing_inputs=missing,dependency_ids=sum((ids.get(k,[]) for k in required),[]))
            else:
                equity=str(Decimal(values['total_equity',year])-Decimal(values['noncontrolling_equity',year])) if family=='PB' else None
                valuation=snapshot_ratio(family,price['raw_close'],eps['value'],equity,values.get(('common_shares',year)))
                row=dict(symbol=symbol,year=year,family=family,value=valuation['value'],status=valuation['status'],result=valuation,
                    dependency_ids=sorted(set(sum((ids.get(k,[]) for k in required),[]))),
                    missing_inputs=[],snapshot_date=price['trade_date'],book_date=cohort['fiscal_period_end'],price_basis='RAW_CLOSE',annual_pe_not_ttm=True,current_event_adjustment_verified=False,
                    strict_current_pe=None,strict_current_pb=None)
        else:row=task_result(symbol,year,family,values,ids,'CONSOLIDATED')
        rows.append(dict(row,cohort_id=cohort['id'],primary_pdf_sha256=cohort['primary_pdf_sha256'],source_report_year=cohort['source_report_year'],
            temporal_status='EXACT_REPORT_VINTAGE_REFERENCE_NEVER_BACKFILL',strict_pit_ready=False,financial_features_allowed=False))
    return dict(metrics=rows,checks=checks,conflicts=conflicts,derivations=derivations)


def verify_price(root,item,pins):
    raw=inside(root,item['path']).read_bytes()
    if digest(raw)!=item['sha256']:raise ValueError('price reference evidence changed')
    pins[item['path']]=item['sha256'];e=json.loads(raw);p=inside(root,e['source_path']);hasher=sha256();selected=None
    with p.open('rb') as f:
        for line_number,line in enumerate(f,1):
            hasher.update(line)
            if line_number==e['selected']['line_number']:
                if digest(line)!=e['selected']['line_sha256']:raise ValueError('price source row changed')
                selected=json.loads(line)
    if hasher.hexdigest()!=e['source_sha256'] or selected!=e['selected']['row']:raise ValueError('sealed canonical price source differs')
    pins[e['source_path']]=e['source_sha256']
    if (selected['ticker']!=item['symbol'] or selected['exchange']!=item['exchange'] or selected['trade_date']!=item['snapshot_date']
        or Decimal(str(selected['raw_close']))<=0):raise ValueError('price snapshot identity differs')
    return selected


def run(root,config_path,action):
    c=read(inside(root,config_path));pins={};facts=[];publications={};documents={};source_anomalies=[]
    if c.get('version')!='financial-reference-cohorts-v1' or c.get('financial_features_allowed') is not False or len(c['cohorts'])>80:
        raise ValueError('bounded reviewed reference cohort contract required')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('review cohort evidence changed: '+path)
        pins[path]=sha;return raw
    for path in [config_path,'src/delta_t1/experiments/financial_reference_cohorts.py','scripts/financial_reference_cohorts.py',
        'scripts/financial_reference_cohorts.ps1','src/delta_t1/experiments/financial_reviewed_batch.py',
        'src/delta_t1/features/financial_reference.py','src/delta_t1/features/financial_vas_reference.py',
        'src/delta_t1/experiments/financial_cafef_pilot.py','src/delta_t1/ingestion/financial_pilot_readiness.py']:pin(path)
    registry=c['registry'];registry_rows=list(csv.DictReader(io.StringIO(pin(registry['path'],registry['sha256']).decode('utf-8-sig'))))
    for cohort in c['cohorts']:
        matches=[r for r in registry_rows if (r['registry_id'],r['ticker'],r['exchange'])==(cohort['registry_id'],cohort['symbol'],cohort['exchange'])]
        if len(matches)!=1:raise ValueError('reference cohort does not join exact registry partition')
    base=c['baseline_result'];bm=json.loads(pin(base['path']+'/manifest.json',base['manifest_sha256']))
    baseline=legacy_rows(pin(base['path']+'/metrics.csv',bm['metrics.csv']))
    pin(base['path']+'/reviewed-inputs.json',bm['reviewed-inputs.json'])
    if len(baseline)!=30 or sum(bool(r['value']) for r in baseline)!=29 or any(r['value'] for r in baseline if r['symbol']=='VNM' and r['family']=='F_SCORE'):
        raise ValueError('legacy29/30 or VNM F gap changed')
    for item in c['reviews']:
        review=json.loads(pin(item['path'],item['sha256']))
        if review['review_method']!='AGENT_VISUAL_REVIEW_OF_PINNED_PDF_PAGES' or review['pit_ready'] is not False:raise ValueError('exact visual reference review required')
        source_anomalies += [dict(x,review_path=item['path']) for x in review.get('source_anomalies',[])]
        for evidence in review['semantic_evidence']:
            for name in ['pdf','image']:pin(evidence[name+'_path'],evidence[name+'_sha256'])
        semantics={e['id']:e for e in review['semantic_evidence']}
        for doc in review['documents']:
            pub=doc.get('publication_date_reference')
            if pub:
                if doc.get('publication_evidence_status')!='EXPLICIT_ISSUER_DATE_ONLY_STATEMENT_VISUALLY_REVIEWED':raise ValueError('publication reference unsupported')
                date.fromisoformat(pub)
                proof=semantics.get(doc.get('publication_evidence_id'),{})
                if (proof.get('kind'),proof.get('value'),proof.get('pdf_sha256'))!=('PUBLICATION_DATE_REFERENCE',pub,doc['pdf_sha256']):
                    raise ValueError('publication reference does not identify exact reviewed document evidence')
            key=doc['pdf_sha256']
            if key in publications and publications[key]!=pub:raise ValueError('conflicting publication reference')
            if key in documents and any(doc[k]!=documents[key][k] for k in ['report_year','eps_basis']):raise ValueError('conflicting document vintage or EPS semantics')
            publications[key]=pub
            documents[key]=doc
        for fact in review['facts']:
            validate_fact(fact,'CONSOLIDATED');p=fact['provenance']
            doc=documents.get(p['pdf_sha256'])
            if not doc or p['source_report_year']!=doc['report_year']:raise ValueError('fact report vintage differs from document')
            for name in ['pdf','image']:pin(p[name+'_path'],p[name+'_sha256'])
            facts.append(fact)
    if len(facts)>3000 or len({f['id'] for f in facts})!=len(facts):raise ValueError('duplicate fact IDs or excessive reference batch')
    if len({x['id'] for x in c['cohorts']})!=len(c['cohorts']):raise ValueError('duplicate vintage cohort ID')
    prices={name:verify_price(root,item,pins) for name,item in c.get('valuation_snapshots',{}).items()}
    metrics=[];checks=[];conflicts=[];derivations=[];facts_by_id={f['id']:f for f in facts}
    for cohort in c['cohorts']:
        doc=documents.get(cohort['primary_pdf_sha256'])
        if not doc or doc['report_year']!=cohort['source_report_year'] or doc['eps_basis']!=cohort['eps_basis']:
            raise ValueError('cohort report vintage/EPS basis differs from reviewed document')
        price=prices.get(cohort.get('valuation_snapshot'));configured_price=price
        if price is not None and price['ticker']!=cohort['symbol']:raise ValueError('cross-issuer valuation reference')
        pub=publications.get(cohort['primary_pdf_sha256'])
        if price and not price_after_publication(price,pub):price=None
        result=compute_cohort(facts,cohort,price)
        for row in result['metrics']:
            row.update(dependency_dates(row,facts_by_id,publications))
            row['primary_publication_date_reference']=pub
            row['valuation_date_reference_eligible']=bool(price) if row['family'] in ['PE','PB'] else None
            if row['family'] in ['PE','PB']:
                row['raw_price_reference_present']=configured_price is not None
                row['valuation_snapshot_id']=cohort.get('valuation_snapshot')
                row['raw_price_reference_value']=str(configured_price['raw_close']) if configured_price else None
                if configured_price and price is None:
                    row['valuation_temporal_blocker']='PUBLICATION_REFERENCE_UNKNOWN_OR_SNAPSHOT_NOT_AFTER_PUBLICATION_DATE'
        metrics+=result['metrics'];checks += [dict(x,cohort_id=cohort['id']) for x in result['checks']]
        conflicts += [dict(x,cohort_id=cohort['id']) for x in result['conflicts']]
        derivations += [dict(x,cohort_id=cohort['id']) for x in result['derivations']]
    by_key=defaultdict(list)
    for row in metrics:
        if row['value'] is not None:by_key[row['symbol'],row['year'],row['family']].append(row)
    differences=[dict(key=list(k),cohort_values=[dict(cohort_id=r['cohort_id'],value=r['value']) for r in rs],action='KEEP_BOTH_VINTAGES_NO_LATEST_SELECTION')
        for k,rs in by_key.items() if len({Decimal(str(r['value'])) for r in rs})>1]
    summary=dict(status='PARTIAL_REFERENCE_COHORTS',reviewed_facts=len(facts),cohorts=len(c['cohorts']),metric_rows=len(metrics),
        metric_rows_with_values=sum(r['value'] is not None for r in metrics),distinct_symbol_year_family_keys_with_values=len(by_key),
        cross_vintage_value_difference_keys=len(differences),ambiguous_within_cohort_fields=len(conflicts),accounting_checks=len(checks),
        preserved_source_anomalies=len(source_anomalies),
        complete_strict_pit_metrics=0,financial_features_allowed=False,research_ready=False,baseline_unchanged=True)
    products={'summary.json':encoded(summary),'facts.json':encoded(facts),'metrics.json':encoded(metrics),'metrics.csv':csv_body(metrics),
        'checks.json':encoded(checks),'conflicts.json':encoded(conflicts),'derivations.json':encoded(derivations),'source-anomalies.json':encoded(source_anomalies),
        'cross-vintage-differences.json':encoded(differences),'input-pins.json':encoded(pins)}
    m={name:digest(raw) for name,raw in products.items()};out=inside(root,c['output_root'])/digest(encoded(m))[:20]
    if not out.is_relative_to(root/'data'/'financial') or out.is_relative_to(inside(root,base['path'])):
        raise ValueError('reference output must be separate from baseline')
    if action=='verify':
        if read(out/'manifest.json')!=m:raise ValueError('reference cohort manifest differs')
        for name,sha in m.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('reference cohort output changed')
    else:
        for name,raw in products.items():put(out/name,raw)
        put(out/'manifest.json',m)
    return dict(summary,output=out.relative_to(root).as_posix())
