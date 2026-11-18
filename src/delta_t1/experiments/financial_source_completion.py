"""Bounded reference execution from reviewed original vintages and raw candidates."""
import json
from decimal import Decimal
from pathlib import Path
from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.financial_date_pit import next_session, iso_date
from ..ingestion.financial_pilot_readiness import SIGNALS, eligible_fact
from ..ingestion.financial_provider_normalize import normalize_kbs, compare_cell
from ..ingestion.financial_review_corrections import apply_review_corrections, verify_correction_evidence
from ..features.financial_reference import calculate_f_score, calculate
from ..features.financial_vas_reference import calculate_vas_f_score, calculate_vas_m_score, calculate_reported_valuation, M_FIELDS, F_VARIANT, M_VARIANT


def select_original(facts, publications, calendar, year, field, decision_date):
    iso_date(decision_date)
    docs=[p for p in publications if p['symbol']=='FPT' and p['year']==year]
    if len(docs)!=1:raise ValueError('ambiguous original annual publication')
    pub=docs[0]
    if pub.get('validation_status')!='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED' or pub.get('precision')!='DATE_ONLY':
        raise ValueError('unreviewed publication')
    usable,status=next_session(pub['publication_date'],pub['exchange'],calendar)
    if usable is None or usable>decision_date:return None
    choices=[f for f in facts if f['symbol']=='FPT' and f['year']==year and f['item']==field
        and f['pdf_sha256']==pub['pdf_sha256'] and f.get('validation_status')=='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED'
        and f.get('statement_scope')=='CONSOLIDATED' and f.get('accounting_framework')=='VAS'
        and eligible_fact(f)]
    if not choices:return None
    if len({(f['value'],f['unit'],f.get('period_start')) for f in choices})!=1:
        raise ValueError(f'conflicting reviewed original values: {year}/{field}')
    return dict(fact=choices[0],publication=pub,usable_from_date=usable,date_pit_status=status)


def export(root, config_path, output):
    root=Path(root);config=json.loads((root/config_path).read_bytes());out=root/output
    if config.get('financial_features_allowed') is not False or config.get('full_universe_allowed') is not False:
        raise ValueError('reference only')
    if config.get('f_variant')!=F_VARIANT or config.get('m_variant')!=M_VARIANT:
        raise ValueError('undeclared variant policy')
    if config['symbol']!='FPT' or not 1<=len(config['f_years'])<=5 or len(config['m_years'])>2:
        raise ValueError('reviewed pilot budget exceeded')
    sources=[config['readiness_run'],config['extended_review_run'],config['publication_run'],config['previous_flow_run'],
             config['revision_review_run'],config['interim_review_run'],config['correction_run']]+config['provider_runs']
    for run in sources:verify_inventory(root/run)
    readiness=json.loads((root/config['readiness_run']/'readiness.json').read_bytes())
    facts=[f for row in readiness['rows'] for f in row['document_evidence']]
    extra=json.loads((root/config['extended_review_run']/'facts.json').read_bytes())
    if not all(c['passed'] for c in extra['checks']):raise ValueError('mapping check failed')
    revision=json.loads((root/config['revision_review_run']/'facts.json').read_bytes())
    facts+=extra['facts']+revision['facts']
    corrections=json.loads((root/config['correction_run']/'corrections.json').read_bytes())
    verify_correction_evidence(corrections)
    facts,excluded_transcriptions=apply_review_corrections(facts,corrections)
    checked=set()
    for fact in facts:
        if fact['symbol']!='FPT':continue
        for key in ['pdf','image']:
            p=Path(fact[f'{key}_path']);identity=(str(p),fact[f'{key}_sha256'])
            if identity not in checked:
                if digest(p.read_bytes())!=identity[1]:raise ValueError('review evidence modified')
                checked.add(identity)
    publications=json.loads((root/config['publication_run']/'publications.json').read_bytes())['documents']
    for pub in publications:
        e=pub['evidence']
        if digest(Path(e['image_path']).read_bytes())!=e['image_sha256']:
            raise ValueError('publication evidence changed')
    policy=json.loads((root/config['date_policy']).read_bytes());calendar_path=root/policy['calendar_path']
    if digest(calendar_path.read_bytes())!=policy['calendar_sha256']:raise ValueError('calendar changed')
    calendar=[json.loads(l) for l in calendar_path.read_text(encoding='utf8').splitlines()]
    def pick(year,field,decision):return select_original(facts,publications,calendar,year,field,decision)
    f_results=[]
    required=set(k for keys in SIGNALS.values() for k in keys if k[0]!='income_before_extraordinary_items')|{('net_profit',0),('net_profit',-1)}
    for year in config['f_years']:
        current_pub=next(p for p in publications if p['symbol']=='FPT' and p['year']==year)
        first,_=next_session(current_pub['publication_date'],'HOSE',calendar)
        for decision in [current_pub['publication_date'],first]:
            values={};inputs=[]
            for field,offset in sorted(required):
                r=pick(year+offset,field,decision)
                if r:values[field,offset]=r['fact']['value'];inputs.append(r)
            f_results.append(dict(year=year,decision_date=decision,inputs=inputs,
                strict=calculate_f_score(values),vas_reference=calculate_vas_f_score(values)))
    m_results=[]
    aliases={'receivables':'gross_short_term_trade_receivables','owned_tangible_ppe_depreciation':'tangible_owned_ppe_depreciation_in_year'}
    for year in config['m_years']:
        values={};inputs=[];allowances={};decision=config['annual_decision_date']
        for field,offset in sorted({(f,o) for f in M_FIELDS for o in [0,-1]}|{('net_profit',0),('operating_cash_flow',0)}):
            r=pick(year+offset,aliases.get(field,field),decision)
            if r:values[field,offset]=r['fact']['value'];inputs.append(r)
        for offset in [0,-1]:
            r=pick(year+offset,'all_short_term_receivables_allowance',decision)
            if r:allowances[offset]=r['fact']['value'];inputs.append(r)
        scenarios=[]
        if len(allowances)==2 and all(('receivables',o) in values for o in [0,-1]):
            for current in [0,1]:
                for prior in [0,1]:
                    v=dict(values)
                    for o,allocated in [(0,current),(-1,prior)]:v['receivables',o]-=allowances[o]*allocated
                    scenarios.append(dict(current_allowance_allocated=current,prior_allowance_allocated=prior,
                        result=calculate_vas_m_score(v,'ALLOCATION_BOUND_SCENARIO')))
        gross=calculate_vas_m_score(values,'GROSS_SHORT_TERM_TRADE')
        computed=[Decimal(s['result']['value']) for s in scenarios if s['result']['value'] is not None]
        m_results.append(dict(year=year,decision_date=decision,inputs=inputs,strict_value=None,
            strict_missing=['net trade allowance allocation','income before extraordinary items','full tangible including leases depreciation bridge'],
            gross_trade_reference=gross,conditional_scenarios=scenarios,
            conditional_range=[str(min(computed)),str(max(computed))] if len(computed)==4 else None,
            range_meaning='Conditional only on allowance allocation; not bounds on the strict original model'))
    candidates=[];comparisons=[];provider_inventory=[]
    for run in config['provider_runs']:
        inventory=json.loads((root/run/'inventory.json').read_bytes())['requests'];provider_inventory+=inventory
        for request in inventory:
            if request['status']!='RAW_JSON_CAPTURED' or request['provider']!='KBS':continue
            raw=Path(request['path']).read_bytes()
            if digest(raw)!=request['sha256']:raise ValueError('raw provider modified')
            cells=normalize_kbs(json.loads(raw),request);candidates+=cells
            if request['symbol']!='FPT' or request['period']!='year':continue
            for cell in cells:
                if not cell['field']:continue
                year=cell['header']['YearPeriod'];field=cell['field']
                # EPS must compare both original and later reviewed revisions, never inherit provider dates.
                alias='basic_eps' if field=='basic_eps' else field
                r=pick(year,alias,config['annual_decision_date']) if year in range(2019,2026) else None
                if r is None:continue
                comparison=compare_cell(cell,r['fact']['value'])
                if field=='basic_eps':
                    comparison=dict(status='PER_SHARE_UNIT_AND_REVISION_REVIEW_REQUIRED',original_value=r['fact']['value'],
                        provider_raw_value=cell['raw_value'],financial_features_allowed=False)
                    if year==2024:
                        revised=next(f for f in revision['facts'] if f['year']==year and f['item']=='basic_eps')
                        pub=next(p for p in publications if p['symbol']==revised['symbol'] and p['pdf_sha256']==revised['pdf_sha256'])
                        usable,_=next_session(pub['publication_date'],pub['exchange'],calendar)
                        if usable and usable<=config['annual_decision_date']:
                            comparison.update(latest_reviewed_value=revised['value'],revision_conflict=cell['raw_value']!=revised['value'],
                                revision_reference=dict(fact=revised,publication=pub,usable_from_date=usable))
                comparisons.append(dict(cell=cell,reviewed=r,comparison=comparison))
    # An end-of-day raw price and FY2025 exact 12-month EPS. No adjusted-price mixing.
    prices=root/config['price_path'];price=None
    for line in prices.open(encoding='utf8'):
        row=json.loads(line)
        if row['ticker']=='FPT' and row['exchange']=='HOSE' and row['trade_date']==config['valuation_date']:
            if price is not None:raise ValueError('duplicate price')
            price=row
    if price is None or price['available_at']>config['valuation_decision_at']:raise ValueError('price not available')
    valuation_inputs={f:pick(2025,f,config['valuation_date']) for f in [
        'eps_adjusted_earnings_numerator','weighted_average_basic_shares','weighted_average_diluted_shares',
        'parent_common_equity','outstanding_common_shares']}
    if not all(valuation_inputs.values()):raise ValueError('valuation evidence incomplete')
    eps=calculate('EPS_RECOMPUTE',{f:r['fact']['value'] for f,r in valuation_inputs.items() if f.startswith('eps_') or f.startswith('weighted_')})
    valuation=calculate_reported_valuation(price['raw_close'],eps['value']['annual_basic_eps_reference'],
        valuation_inputs['parent_common_equity']['fact']['value'],valuation_inputs['outstanding_common_shares']['fact']['value'])
    valuation.update(decision_at=config['valuation_decision_at'],price=price,eps=eps,inputs=valuation_inputs,
        price_sha256=digest(prices.read_bytes()),price_basis='RAW_CLOSE_VND_PER_SHARE',
        annual_window=['2025-01-01','2025-12-31'],exact_12_month_annual_eps=True,
        pb_basis='Reported 2025-12-31 common equity and outstanding shares',
        live_pe_pb_ready=False,intervening_share_event_coverage='PENDING',historical_identity='PROVISIONAL',
        interpretation='Reported-basis reference only; event-complete PIT valuation remains pending')
    previous=json.loads((root/config['previous_flow_run']/'flow.json').read_bytes())
    unchanged=[r for r in previous['results'] if r['decision_date']=='2026-08-28' and r['task'] in ['EPS_RECOMPUTE','Z_SCORE']]
    result=dict(stage='FIN_D4_SOURCE_RESEARCH_AND_VAS_REFERENCES',status='PARTIAL',f_score=f_results,m_score=m_results,
        reported_valuation=valuation,existing_eps_z=unchanged,provider_requests=provider_inventory,
        interim_review=json.loads((root/config['interim_review_run']/'review.json').read_bytes()),
        review_corrections=corrections,excluded_transcriptions=excluded_transcriptions,
        provider_cells=len(candidates),provider_comparisons=comparisons,
        financial_features_allowed=False,research_ready=False,full_universe_allowed=False,
        production_review_status='MANUAL_REVIEW_REQUIRED',input_manifest_sha256={run:digest((root/run/'manifest.json').read_bytes()) for run in sources})
    out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'result.json',encoded(result));immutable_write(out/'provider_candidates.json',encoded(candidates))
    immutable_write(out/'config.json',(root/config_path).read_bytes())
    for name,path in [('runner.py',Path(__file__)),('features.py',root/'src/delta_t1/features/financial_vas_reference.py'),
                      ('provider_normalizer.py',root/'src/delta_t1/ingestion/financial_provider_normalize.py'),
                      ('corrections.py',root/'src/delta_t1/ingestion/financial_review_corrections.py')]:
        immutable_write(out/name,path.read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return result
