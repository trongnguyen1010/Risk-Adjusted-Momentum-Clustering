"""Replay a bounded PDF/OCR/reference/date-PIT/calculator vertical slice offline."""
import json
import re
from decimal import Decimal
from pathlib import Path
from collections import Counter
from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.financial_date_pit import overlay, select_as_of, next_session, iso_date
from ..ingestion.financial_table_parser import extract_cell, compare_candidate
from ..ingestion.financial_task_readiness import matrix
from ..ingestion.financial_pilot_readiness import eligible_fact
from ..features.financial_reference import calculate, calculate_f_score
from ..ingestion.financial_pilot_readiness import SIGNALS

DILUTION_RULE = 'BASIC_DENOMINATOR_EQUALS_DILUTED_WHEN_NOTE_EXPLICITLY_DISCLOSES_NO_DILUTIVE_POTENTIAL_COMMON_SHARES'


def eps_case_as_of(task, temporal_rows, cases, decision_date):
    row = next((r for r in temporal_rows if (r['symbol'],r['year'],r['field']) ==
                (task['symbol'],task['year'],'weighted_average_basic_shares')), {})
    selected = select_as_of(row.get('references', []), decision_date).get('selected')
    hashes = {r['fact']['pdf_sha256'] for r in selected or []}
    return next((c for c in cases if hashes == {c['pdf_sha256']}), cases[0])


def evaluate_f_score(symbol, year, temporal_rows, allowed_pdfs, decision_date):
    """Multi-year original references; arbitrary per-field vintage mixing is blocked."""
    inputs, values, blocked = [], {}, []
    required = sorted({k for fields in SIGNALS.values() for k in fields})
    for field, offset in required:
        row = next((r for r in temporal_rows if (r['symbol'],r['year'],r['field']) ==
                    (symbol,year+offset,field)), {})
        selection = select_as_of(row.get('references', []), decision_date)
        refs = selection.get('selected')
        reason = selection['status']
        if refs and (not all(eligible_fact(r['fact']) for r in refs) or
                     {r['fact']['pdf_sha256'] for r in refs} != {allowed_pdfs.get(str(year+offset))}):
            refs, reason = None, 'INCOMPATIBLE_OR_UNREVIEWED_YEAR_VINTAGE'
        if refs:
            values[field,offset] = refs[0]['fact']['value']
            inputs.append(dict(field=field,year=year+offset,references=refs))
        else:
            blocked.append(dict(field=field,year=year+offset,reason=reason))
    result = calculate_f_score(values)
    return dict(result, symbol=symbol,year=year,task='F_SCORE',decision_date=decision_date,
                inputs=inputs,missing_inputs=blocked,cluster_eligible=False,
                qa_scope='REVIEWED_FACTS_AND_DATE_PIT; NOT_FULL_OCR_AUTOMATION_OR_PRODUCTION_GATE')


def reviewed_values(readiness, symbol, year, field, pdf_hash):
    row = next((r for r in readiness['rows'] if (r['symbol'], r['year'], r['field']) == (symbol, year, field)), {})
    refs = [f for f in row.get('document_evidence', []) if f['pdf_sha256'] == pdf_hash and eligible_fact(f)]
    values = {(str(f['value']), f['unit']) for f in refs}
    return refs if len(values) == 1 else []


def evaluate(task, temporal_rows, case, parser_checks, decision_date):
    """A passed OCR cell cannot compensate for future, incompatible or missing inputs."""
    selected = []
    missing = []
    for item in task['inputs']:
        row = next((r for r in temporal_rows if (r['symbol'], r['year'], r['field']) ==
                    (task['symbol'], item['year'], item['field'])), {})
        try:
            selection = select_as_of(row.get('references', []), decision_date)
        except ValueError:
            selection = dict(selected=None, status='INCOMPATIBLE_REPORT_IDENTITY')
        if not selection.get('selected'):
            missing.append(dict(field=item['field'], year=item['year'], reason=selection['status']))
        else:
            selected.append(dict(field=item['field'], year=item['year'], references=selection['selected']))
    base = dict(symbol=task['symbol'], year=task['year'], task=task['task'], decision_date=decision_date,
                inputs=selected, missing_inputs=missing, value=None, financial_features_allowed=False,
                research_ready=False, cluster_eligible=False)
    if task['task'] not in ('EPS_RECOMPUTE', 'Z_SCORE'):
        return dict(base, status='BLOCKED_OUTSIDE_REFERENCE_CALCULATORS', blockers=task['semantic_blockers'])
    alerts = [a for a in case.get('revision_alerts',[]) if a['task']==task['task']
              and a.get('usable_from_date') and iso_date(a['usable_from_date']) <= iso_date(decision_date)]
    if alerts:
        return dict(base, status='BLOCKED_LATER_REVISION_NOT_MAPPED', revision_alerts=alerts)
    if missing:
        return dict(base, status='BLOCKED_MISSING_OR_UNAVAILABLE_INPUTS')
    hashes = {r['fact']['pdf_sha256'] for i in selected for r in i['references']}
    if hashes != {case['pdf_sha256']}:
        return dict(base, status='BLOCKED_JOINT_VINTAGE_OR_TEMPLATE')
    if any(not eligible_fact(r['fact']) for i in selected for r in i['references']):
        return dict(base, status='BLOCKED_FACT_SCOPE_UNIT_PERIOD')
    required_checks = ({'eps_adjusted_earnings_numerator','weighted_average_basic_shares','vendor_basic_eps'}
                       if task['task']=='EPS_RECOMPUTE' else
                       {'current_assets','total_assets','current_liabilities','total_liabilities','total_equity',
                        'retained_earnings','profit_before_tax','interest_expense','BALANCE_IDENTITY','EBIT_BRIDGE'})
    checks_by_field = {c['field']:c for c in parser_checks}
    failed = [f for f in sorted(required_checks) if not checks_by_field.get(f,{}).get('passed')]
    if failed:
        return dict(base, status='BLOCKED_OCR_REFERENCE_QA', blockers=failed)
    values = {i['field']: i['references'][0]['fact']['value'] for i in selected}
    if task['task'] == 'EPS_RECOMPUTE':
        diluted = next(i for i in selected if i['field'] == 'weighted_average_diluted_shares')
        if any(r['fact'].get('derivation', {}).get('rule') != DILUTION_RULE for r in diluted['references']):
            return dict(base, status='BLOCKED_DILUTION_SEMANTICS')
        for ref in diluted['references']:
            fact = ref['fact']
            derivation = fact.get('derivation', {})
            original = derivation.get('original_no_dilution_evidence')
            if original is not None:
                if (not eligible_fact(original) or original['year'] != task['year'] or
                    original.get('derivation',{}).get('rule') != DILUTION_RULE or
                    original['value'] + derivation.get('bonus_share_adjustment', 0) != fact['value']):
                    return dict(base,status='BLOCKED_RESTATED_DILUTION_BRIDGE')
                for path_key,hash_key in [('pdf_path','pdf_sha256'),('image_path','image_sha256')]:
                    if digest(Path(original[path_key]).read_bytes()) != original[hash_key]:
                        raise ValueError('original no-dilution evidence mismatch')
    else:
        ebit = next(i for i in selected if i['field'] == 'document_reconciled_ebit')
        if any(r['fact'].get('derivation', {}).get('rule') != 'EBT_PLUS_EXPENSED_INTEREST' for r in ebit['references']):
            return dict(base, status='BLOCKED_EBIT_RECONCILIATION')
    result = calculate(task['task'], values)
    if result['value'] is None:
        return dict(base, status=result['status'])
    base.update(value=result['value'], rounded=result.get('rounded', {}),
                usable_from_date=max(r['usable_from_date'] for i in selected for r in i['references']),
                pdf_sha256=case['pdf_sha256'], status='REFERENCE_QA_PASS')
    if task['task'] == 'EPS_RECOMPUTE':
        printed = next(c['candidate']['value'] for c in parser_checks if c['field'] == 'vendor_basic_eps')
        error = abs(Decimal(result['value']['annual_basic_eps_reference']) - Decimal(printed))
        base['qa'] = dict(check='EPS_PRINTED_ROUNDING', absolute_error=str(error), tolerance='0.5', passed=error <= Decimal('.5'))
    else:
        base['qa'] = dict(check='SAME_PDF_BALANCE_AND_EBIT_BRIDGES', passed=True,
                          external_published_z_score_available=False)
    if not base['qa']['passed']:
        base.update(status='BLOCKED_CALCULATION_QA', value=None)
    return base


def export(root, config_path, output):
    root = Path(root).resolve()
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_bytes())
    if config.get('financial_features_allowed') is not False or config.get('full_universe_allowed') is not False:
        raise ValueError('reference flow cannot grant production or scale eligibility')
    if not 1 <= len(config['cases']) <= min(config['max_cases'], 4) or not 1 <= len(config['decision_dates']) <= min(config['max_decision_dates'], 8):
        raise ValueError('reference flow budget exceeded')
    if len({(c['symbol'],c['year']) for c in config['cases']}) != len(config['cases']):
        raise ValueError('duplicate reference case')
    if any(not 1 <= len(c['cells']) <= min(config['max_cells_per_case'], 32) for c in config['cases']):
        raise ValueError('OCR cell budget exceeded')
    if any(c.get('template_status')!='REVIEWED_EXACT_PDF_TEMPLATE' for c in config['cases']):
        raise ValueError('exact-PDF reviewed template required')
    runs = [root/config[k] for k in ('readiness_run', 'publication_run')]
    all_cases = [variant for c in config['cases'] for variant in [c]+c.get('eps_revision_cases',[])]
    if len(all_cases)>4 or any(len(c['cells'])>32 or c.get('template_status')!='REVIEWED_EXACT_PDF_TEMPLATE' for c in all_cases):
        raise ValueError('revision template budget/status invalid')
    runs.extend(root/p for p in sorted({s['ocr_run'] for c in all_cases for s in c['cells']}))
    for run in runs:
        verify_inventory(run)
    readiness = json.loads((runs[0]/'readiness.json').read_bytes())
    publications = json.loads((runs[1]/'publications.json').read_bytes())
    for pub in publications['documents']:
        if digest(Path(pub['pdf_path']).read_bytes()) != pub['pdf_sha256']:
            raise ValueError('publication PDF mismatch')
        evidence = pub['evidence']
        if digest(Path(evidence['image_path']).read_bytes()) != evidence['image_sha256']:
            raise ValueError('publication evidence mismatch')
    policy_path = root/config['date_pit_policy']
    policy = json.loads(policy_path.read_bytes())
    calendar_path = root/policy['calendar_path']
    if digest(calendar_path.read_bytes()) != policy['calendar_sha256']:
        raise ValueError('calendar hash mismatch')
    calendar = [json.loads(l) for l in calendar_path.read_text(encoding='utf8').splitlines()]
    temporal = overlay(readiness, publications, calendar, policy)
    tasks = matrix(readiness, sorted({c['symbol'] for c in config['cases']}), sorted({c['year'] for c in config['cases']}))
    parsed, results, checks_by_case = [], [], {}
    for case in all_cases:
        pdf = root/case['pdf_path']
        if digest(pdf.read_bytes()) != case['pdf_sha256']:
            raise ValueError('case PDF hash mismatch')
        for alert in case.get('revision_alerts',[]):
            pub = [p for p in publications['documents'] if (p['symbol'],p['pdf_sha256']) ==
                   (case['symbol'],alert['pdf_sha256'])]
            if len(pub)!=1:raise ValueError('revision alert needs exact-PDF publication evidence')
            alert['usable_from_date'], status = next_session(pub[0]['publication_date'],pub[0]['exchange'],calendar)
            if alert['usable_from_date'] is None:raise ValueError('revision alert calendar unresolved: '+status)
            if digest((root/alert['image_path']).read_bytes())!=alert['image_sha256']:
                raise ValueError('revision alert image mismatch')
        checks = []
        for spec in case['cells']:
            ocr_path = root/spec['ocr_run']/spec['ocr_file']
            image_path = ocr_path.with_name(ocr_path.name.replace('.ocr.json', '.png'))
            record = json.loads(ocr_path.read_bytes())
            if digest(image_path.read_bytes()) != record['image_sha256']:
                raise ValueError('OCR image hash mismatch')
            index = json.loads((root/spec['ocr_run']/'index.json').read_bytes())
            document = [d for d in index['documents'] if d.get('sha256', d.get('pdf_sha256')) == case['pdf_sha256']
                        and Path(d.get('path',d.get('pdf_path'))).stem == ocr_path.parent.name]
            if len(document) != 1:
                raise ValueError('OCR/PDF identity mismatch')
            page = int(re.fullmatch(r'page-(\d+)\.ocr\.json', ocr_path.name)[1])
            refs = reviewed_values(readiness, case['symbol'], case['year'], spec['field'], case['pdf_sha256'])
            for f in refs:
                if digest(Path(f['image_path']).read_bytes()) != f['image_sha256']:
                    raise ValueError('reviewed fact image mismatch')
            candidate = extract_cell(record, spec, case['year'])
            comparison = compare_candidate(candidate, refs[0]['value']) if refs else dict(status='REVIEWED_REFERENCE_MISSING', passed=False)
            if any(f['unit'] != spec['unit'] for f in refs):
                comparison = dict(status='REFERENCE_UNIT_MISMATCH', passed=False)
            checks.append(dict(symbol=case['symbol'], year=case['year'], field=spec['field'],
                               pdf_sha256=case['pdf_sha256'], pdf_page=page,
                               ocr_path=str(ocr_path), ocr_sha256=digest(ocr_path.read_bytes()),
                               image_path=str(image_path), image_sha256=record['image_sha256'],
                               reference_on_same_page=bool(refs) and all(f['pdf_page']==page for f in refs),
                               candidate=candidate, reviewed_references=refs, **comparison))
        v = {c['field']: c['candidate']['value'] for c in checks}
        # These checks use independently parsed cells, never reference values as parser output.
        for name, fields, expression in [
            ('BALANCE_IDENTITY', ('total_assets','total_liabilities','total_equity'), lambda x:x['total_assets']==x['total_liabilities']+x['total_equity']),
            ('EBIT_BRIDGE', ('profit_before_tax','interest_expense'), lambda x: x['profit_before_tax']+x['interest_expense']==reviewed_values(readiness,case['symbol'],case['year'],'document_reconciled_ebit',case['pdf_sha256'])[0]['value'])]:
            present = all(v.get(f) is not None for f in fields)
            if not any(f in v for f in fields):
                continue  # EPS-only revision template has no balance/EBIT cells.
            bridge_ok = present and all(c['passed'] for c in checks if c['field'] in fields) and expression(v)
            checks.append(dict(symbol=case['symbol'],year=case['year'],field=name, passed=bool(bridge_ok), candidate=dict(value=None)))
        parsed.extend(checks)
        checks_by_case[case['symbol'],case['year'],case['pdf_sha256']] = checks
    for case in config['cases']:
        for decision_date in config['decision_dates']:
            for task in tasks['rows']:
                if (task['symbol'],task['year']) == (case['symbol'],case['year']):
                    active_case = eps_case_as_of(task, temporal['rows'], [case]+case.get('eps_revision_cases',[]), decision_date) if task['task']=='EPS_RECOMPUTE' else case
                    checks = checks_by_case[active_case['symbol'],active_case['year'],active_case['pdf_sha256']]
                    if task['task']=='F_SCORE' and config.get('f_score_original_pdfs'):
                        result = evaluate_f_score(task['symbol'],task['year'],temporal['rows'],config['f_score_original_pdfs'],decision_date)
                        for item in result['inputs']:
                            for ref in item['references']:
                                fact = ref['fact']
                                for path_key, hash_key in [('pdf_path','pdf_sha256'),('image_path','image_sha256')]:
                                    if digest(Path(fact[path_key]).read_bytes()) != fact[hash_key]:
                                        raise ValueError('F-score evidence hash mismatch')
                        results.append(result)
                    else:
                        results.append(evaluate(task, temporal['rows'], active_case, checks, decision_date))
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    result = dict(version=config['version'], results=results, parsed_cells=parsed,
                  counts=dict(Counter(r['status'] for r in results)), review_queue=[c for c in parsed if not c['passed']],
                  source_mode='IMMUTABLE_PDF_OCR_CACHE_REPLAY_WITH_REVIEWED_REFERENCES',
                  financial_features_allowed=False, full_universe_allowed=False, research_ready=False,
                  input_manifests_sha256={str(p):digest((p/'manifest.json').read_bytes()) for p in runs})
    immutable_write(out/'flow.json', encoded(result))
    immutable_write(out/'config.json', config_path.read_bytes())
    immutable_write(out/'date_policy.json', policy_path.read_bytes())
    for name, source in [('runner.py', Path(__file__)), ('parser.py', Path(__file__).parents[1]/'ingestion/financial_table_parser.py'),
                         ('calculators.py', Path(__file__).parents[1]/'features/financial_reference.py')]:
        immutable_write(out/name, source.read_bytes())
    immutable_write(out/'manifest.json', encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return result
