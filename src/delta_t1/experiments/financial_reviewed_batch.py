"""Versioned reviewed-fact bundle and complete annual task grid; no API promotion."""
from collections import Counter, defaultdict
from decimal import Decimal
import json

from ..features.financial_reference import calculate
from ..features.financial_vas_reference import (
    calculate_disclosed_basic_eps, calculate_vas_f_score, calculate_vas_m_score)
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_cafef_pilot import required_keys, FAMILIES
from .financial_history_documents import put, read
from .financial_history_qa import csv_body
from .financial_history_review import check_quarter
from .financial_quarterly_review import check_quarter_v2, period_eps, publication_status
from .financial_period_date_view import build_date_view, monthly_decisions


def unit_for(field):
    if field in ['weighted_average_basic_shares','weighted_average_diluted_shares','common_shares']:
        return 'SHARES'
    if field=='parent_common_equity_issuance_verified':return 'INDICATOR'
    if field=='vendor_basic_eps':return 'VND/share'
    return 'VND'


def validate_fact(fact, allowed_scope='CONSOLIDATED'):
    if allowed_scope not in ['CONSOLIDATED','ISSUER_NO_SUBSIDIARIES','COMPANY_REPORTED']:
        raise ValueError('unreviewed input scope policy')
    if (fact.get('review_status')!='REVIEWED_REFERENCE_ONLY'
            or fact.get('scope')!=allowed_scope or fact.get('framework')!='VAS'
            # Older quarterly reviews omit eligibility, which grants no PIT rights.
            or fact.get('pit_ready', False) is not False or fact.get('available_at') is not None):
        raise ValueError('unreviewed, incompatible or unaccepted PIT fact')
    if (fact['unit']!=unit_for(fact['field']) or isinstance(fact['value'],bool)
            or not Decimal(fact['value']).is_finite()):
        raise ValueError('unit or numeric mismatch')


def legacy_rows(raw):
    import csv,io
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    keys=[(x['symbol'],int(x['year']),x['family']) for x in rows]
    if len(set(keys))!=len(keys):raise ValueError('duplicate baseline metric key')
    return rows


def annual_values(facts, symbol, allowed_pdf_hashes, allowed_scope='CONSOLIDATED'):
    groups=defaultdict(list)
    for f in facts:
        if (f['symbol']==symbol and f.get('scope')==allowed_scope and not f.get('interval')
                and f['provenance']['pdf_sha256'] in allowed_pdf_hashes):
            groups[f['field'],f['year']].append(f)
    values,ids,conflicts={}, {}, []
    for key,rows in groups.items():
        if len({(Decimal(x['value']),x['unit']) for x in rows})!=1:
            conflicts.append(dict(symbol=symbol,field=key[0],year=key[1],observations=rows,status='AMBIGUOUS_NO_SELECTION'))
            continue
        values[key]=rows[0]['value'];ids[key]=[x['id'] for x in rows]
    return values,ids,conflicts


def task_result(symbol, year, family, values, ids, input_scope='CONSOLIDATED'):
    if input_scope=='COMPANY_REPORTED' and family!='EPS':
        raise ValueError('company-only report is cleared for disclosed basic EPS arithmetic only')
    v={(field,y-year):value for (field,y),value in values.items()}
    dependencies=[]
    for key in required_keys(family):dependencies+=ids.get((key[0],year+key[1]),[])
    current={field:value for (field,offset),value in v.items() if offset==0}
    derived=None
    if family=='Z_SCORE' and 'profit_before_tax' in current and 'interest_expense' in current:
        current['document_reconciled_ebit']=str(Decimal(current['profit_before_tax'])+Decimal(current['interest_expense']))
        v['document_reconciled_ebit',0]=current['document_reconciled_ebit']
        dependencies+=ids.get(('profit_before_tax',year),[])+ids.get(('interest_expense',year),[])
        derived=dict(field='document_reconciled_ebit',operation='profit_before_tax + interest_expense',value=current['document_reconciled_ebit'])
    missing=[dict(field=f,year=year+o) for f,o in sorted(required_keys(family)-v.keys())]
    if family in ['PE','PB']:
        result=dict(value=None,status='MISSING_REVIEWED_VALUATION_PRICE_SHARE_EVENT_BASIS')
    elif missing:result=dict(value=None,status='MISSING_OR_AMBIGUOUS_REVIEWED_INPUTS')
    elif family=='EPS':result=calculate_disclosed_basic_eps(current['eps_adjusted_earnings_numerator'],current['weighted_average_basic_shares'],12)
    elif family=='F_SCORE':result=calculate_vas_f_score(v)
    elif family=='M_SCORE':result=calculate_vas_m_score(v,'GROSS_SHORT_TERM_TRADE')
    else:
        result=calculate('Z_SCORE',current)
        result=dict(result,value=result['value']['em_z_double_prime_reference'] if result['value'] else None)
    return dict(symbol=symbol,year=year,family=family,input_scope=input_scope,value=result['value'],status=result['status'],
        dependency_ids=sorted(set(dependencies)),missing_inputs=missing,derivation=derived,result=result,
        computation='RECOMPUTED_FROM_REVIEWED_EXACT_INPUTS',temporal_status='SOURCE_VINTAGE_REFERENCE_ONLY',
        strict_pit_ready=False,financial_features_allowed=False)


def run(root, config_path, action):
    config=read(inside(root,config_path))
    if config.get('version')!='financial-reviewed-batch-v1' or config.get('financial_features_allowed') is not False:
        raise ValueError('reviewed reference bundle required')
    if len(config['symbols'])>20 or config['years']!=list(range(2013,2026)):
        raise ValueError('bounded annual history grid required')
    for cohort in config['cohorts'].values():
        if (cohort.get('input_scope')=='COMPANY_REPORTED'
                and set(cohort.get('applicable_families',[]))-{'EPS'}):
            raise ValueError('company scope cannot open consolidated reference families')
    pins={};facts=[];quarter_checks=[];quarter_eps=[];publication_checks=[];date_slices=[];raw_cache={}
    def pin(relative,expected=None):
        if relative not in raw_cache:
            raw_cache[relative]=inside(root,relative).read_bytes()
        raw=raw_cache[relative];h=pins.get(relative) or digest(raw)
        if expected is not None and h!=expected:raise ValueError('bundle input hash mismatch: '+relative)
        pins[relative]=h;return raw
    pin(config_path)
    for path in ['src/delta_t1/experiments/financial_reviewed_batch.py', 'scripts/financial_reviewed_batch.py',
                 'src/delta_t1/experiments/financial_history_review.py','src/delta_t1/experiments/financial_quarterly_review.py',
                 'src/delta_t1/experiments/financial_period_date_view.py','src/delta_t1/ingestion/financial_date_pit.py',
                 'src/delta_t1/experiments/financial_cafef_pilot.py',
                 'src/delta_t1/features/financial_reference.py','src/delta_t1/features/financial_vas_reference.py']:
        pin(path)
    for item in config['reviews']:
        review=json.loads(pin(item['path'],item['sha256']))
        if item['kind']=='QUARTER_V2':
            quarter_checks += [dict(x,review_path=item['path']) for x in check_quarter_v2(review)]
            quarter_eps += [dict(x,review_path=item['path']) for x in period_eps(review)]
            publication_checks.append(dict(review_path=item['path'],candidate=review.get('publication_candidate',{}),
                                           status=publication_status(review.get('publication_candidate',{})),pit_ready=False))
            if config.get('monthly_date_view') and review.get('publication_link'):
                link=review['publication_link']
                approved=json.loads(pin(link['review_path'],link['review_sha256']))
                pub=approved['publication'];evidence=pub['evidence']
                pin(evidence['image_path'],evidence['image_sha256'])
                policy=json.loads(pin(approved['date_policy']))
                calendar_raw=pin(approved['calendar_path'],approved['calendar_sha256'])
                if policy['calendar_path']!=approved['calendar_path'] or policy['calendar_sha256']!=approved['calendar_sha256']:
                    raise ValueError('approved calendar identity changed')
                if link.get('exchange') not in ['HOSE','HNX','UPCOM']:raise ValueError('explicit reviewed publication exchange required')
                date_slices.append(dict(review=review,publication=pub,exchange=link['exchange'],policy=policy,
                                        calendar=[json.loads(line) for line in calendar_raw.splitlines()]))
        if item['kind']=='QUARTER':
            identity={(f['symbol'],f['year'],f['quarter'],f['provenance']['pdf_sha256']) for f in review['facts']}
            if len(identity)!=1:raise ValueError('quarter review mixes report identities')
            symbol,year,quarter,pdf_hash=next(iter(identity))
            quarter_checks += [dict(x,symbol=symbol,year=year,quarter=quarter,pdf_sha256=pdf_hash,
                                    review_path=item['path']) for x in check_quarter(review)]
        for fact in review['facts']:
            validate_fact(fact,item.get('fact_scope','CONSOLIDATED'))
            p=fact['provenance']
            for name in ['pdf','image']:
                pin(p[name+'_path'],p[name+'_sha256'])
            facts.append(fact)
    if len(facts)>3000 or len({f['id'] for f in facts})!=len(facts):
        raise ValueError('fact budget/identity mismatch')
    # Baseline remains the already verified FY2025 reference, never silently rebuilt.
    base=config['baseline_result'];manifest=json.loads(pin(base+'/manifest.json',config['baseline_manifest_sha256']))
    legacy=legacy_rows(pin(base+'/metrics.csv',manifest['metrics.csv']))
    known={(x['symbol'],int(x['year']),x['family']):x for x in legacy}
    if len(known)!=len(legacy):raise ValueError('duplicate baseline metric key')
    rows=[];conflicts=[]
    for symbol in config['symbols']:
        for year in config['years']:
            cohort=config['cohorts'].get(symbol+':'+str(year),{})
            scope=cohort.get('input_scope','CONSOLIDATED')
            values,ids,ambiguous=annual_values(facts,symbol,cohort.get('allowed_pdf_hashes',[]),scope)
            for x in ambiguous:
                if x not in conflicts:conflicts.append(x)
            for family in FAMILIES:
                old=known.get((symbol,year,family))
                if old:
                    rows.append(dict(symbol=symbol,year=year,family=family,value=old['value'] or None,
                        status=old['status'],computation='UNCHANGED_LEGACY_FY2025_REFERENCE',
                        temporal_status=old['temporal_status'],legacy_row=old,strict_pit_ready=False,financial_features_allowed=False))
                elif family not in cohort.get('applicable_families',[]):
                    rows.append(dict(symbol=symbol,year=year,family=family,input_scope=scope,value=None,
                        status=cohort.get('blocked_family_reason','REVIEWED_INPUT_COHORT_NOT_YET_AVAILABLE'),
                        computation='NOT_COMPUTED',missing_inputs=[dict(field=f,year=year+o) for f,o in sorted(required_keys(family))],
                        strict_pit_ready=False,financial_features_allowed=False))
                else:rows.append(task_result(symbol,year,family,values,ids,scope))
    date_rows=[]
    if config.get('monthly_date_view'):
        years=config['monthly_date_view']['years']
        if years!=list(range(2016,2026)):raise ValueError('market-aligned monthly date view required')
        if date_slices:
            if any(s['policy']!=date_slices[0]['policy'] or s['calendar']!=date_slices[0]['calendar'] for s in date_slices):
                raise ValueError('date slices use incompatible calendar/policy')
            date_rows=build_date_view(date_slices,date_slices[0]['calendar'],date_slices[0]['policy'],monthly_decisions(years))
    summary=dict(status='PARTIAL',annual_task_rows=len(rows),reviewed_facts=len(facts),
        reviewed_fact_scopes=dict(Counter(f['scope'] for f in facts)),
        annual_facts=sum(not bool(f.get('interval')) for f in facts),quarter_instant_ytd_facts=sum(bool(f.get('interval')) for f in facts),
        metric_rows_with_values=sum(x['value'] is not None for x in rows),
        legacy_reference_values=sum(x['value'] is not None and x['computation']=='UNCHANGED_LEGACY_FY2025_REFERENCE' for x in rows),
        newly_computed_reference_values=sum(x['value'] is not None and x['computation']=='RECOMPUTED_FROM_REVIEWED_EXACT_INPUTS' for x in rows),
        newly_computed_value_scopes=dict(Counter(r['input_scope'] for r in rows
            if r['value'] is not None and r['computation']=='RECOMPUTED_FROM_REVIEWED_EXACT_INPUTS')),
        quarterly_period_eps_values=sum(x['value'] is not None for x in quarter_eps),
        monthly_period_date_reference_rows=len(date_rows),monthly_date_eligible_period_eps_rows=sum(r['date_eligible_reference'] for r in date_rows),
        statuses=dict(Counter(x['status'] for x in rows)),ambiguous_fact_keys=len(conflicts),
        applicable_model_variants='Existing pilot reference variants only; no bank/insurance applicability inferred',
        quarterly_ttm_metrics='NOT_COMPLETE; exact-period notes and compatible share history required',
        complete_pit_metrics=0,financial_features_allowed=False,batch20_allowed=False)
    products={'summary.json':encoded(summary),'facts.json':encoded(facts),'annual-metrics.json':encoded(rows),
        'annual-metrics.csv':csv_body(rows),'fact-conflicts.json':encoded(conflicts),
        'quarter-period-eps.json':encoded(quarter_eps),'quarter-publication-checks.json':encoded(publication_checks),
        'monthly-period-date-reference.json':encoded(date_rows),
        'quarter-checks.json':encoded(quarter_checks),'input-pins.json':encoded(pins)}
    manifest={n:digest(b) for n,b in sorted(products.items())}
    out=inside(root,config['output_root'])/digest(encoded(manifest))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=manifest:raise ValueError('bundle manifest differs')
        for n,h in manifest.items():
            if digest((out/n).read_bytes())!=h:raise ValueError('bundle product changed: '+n)
    else:
        for n,b in products.items():put(out/n,b)
        put(out/'manifest.json',manifest)
    return dict(summary,status='VERIFIED' if action=='verify' else 'PARTIAL',output=out.relative_to(root).as_posix())
