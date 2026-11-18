"""Offline assessment of a sealed candidate cohort and reviewed reference adapters.

The join attaches calculations to the assessment, never publication dates or
accepted values to current provider HTML. Annual and interim bases stay separate.
"""
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

from .financial_batch_flow import references, verify_pins
from .cafef_financial_trial import verify as verify_trial
from ..features.financial_reference import calculate
from ..features.financial_vas_reference import calculate_vas_f_score, calculate_vas_m_score
from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside, seal
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.financial_crawl_candidates import csv_bytes
from ..ingestion.financial_pilot_readiness import eligible_fact

VERSION = 'financial-trial-reviewed-integration-v1'
CLOSED = dict(financial_features_allowed=False, research_ready=False,
              full_universe_allowed=False, financial_cluster_allowed=False,
              unattended_numeric_acceptance_allowed=False, next_100_allowed=False)
PRODUCTION_BLOCKERS = ['REFERENCE_VARIANT_NOT_PRODUCTION_ACCEPTED',
                       'HISTORICAL_IDENTITY_SECTOR_UNVERIFIED', 'REVISION_EVENT_COVERAGE_INCOMPLETE']


def evidence_pins(root, tree, pins=None):
    """Verify exact external proof files, including nested derivation originals."""
    pins = {} if pins is None else pins
    if isinstance(tree, list):
        for item in tree:
            evidence_pins(root, item, pins)
    elif isinstance(tree, dict):
        for key, value in tree.items():
            if key.endswith('_path') and isinstance(value, str):
                expected = tree.get(key[:-5] + '_sha256')
                if isinstance(expected, str):
                    path = inside(root, value)
                    relative = path.relative_to(root).as_posix()
                    if relative in pins and pins[relative] != expected:
                        raise ValueError('competing evidence pins: ' + relative)
                    if relative not in pins and digest(path.read_bytes()) != expected:
                        raise ValueError('external reviewed evidence changed: ' + relative)
                    pins[relative] = expected
            evidence_pins(root, value, pins)
    return pins


def values_at(refs, year, day):
    values = {}
    for r in refs:
        f = r['fact']
        if (not eligible_fact(f) or r.get('date_pit_status') != 'DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR'
                or not r.get('usable_from_date') or r['usable_from_date'] > day):
            raise ValueError('reviewed calculation has unreviewed/future/date-unverified input')
        key = (f['item'], f['year'] - year)
        if key in values and values[key] != f['value']:
            raise ValueError('competing reviewed values; no source priority')
        values[key] = f['value']
    return values


def history_rows(source, source_path, decision_day, years):
    rows = []
    for name, task, result_key in [('f_score', 'F_SCORE', 'vas_reference'),
                                    ('m_score', 'M_SCORE', 'gross_trade_reference')]:
        for year in years:
            matches = [r for r in source[name] if r['year'] == year and r['decision_date'] <= decision_day
                       and r[result_key]['value'] is not None]
            if not matches:
                continue
            latest = max(r['decision_date'] for r in matches)
            chosen = [r for r in matches if r['decision_date'] == latest]
            if len(chosen) != 1:
                raise ValueError('ambiguous reviewed calculation snapshot')
            r = chosen[0]
            values = values_at(r['inputs'], year, r['decision_date'])
            if task == 'M_SCORE':
                # Same explicit note aliases as financial_source_completion;
                # no new definition or provider-field substitution.
                for target, original in [('receivables', 'gross_short_term_trade_receivables'),
                                         ('owned_tangible_ppe_depreciation', 'tangible_owned_ppe_depreciation_in_year')]:
                    for offset in [0, -1]:
                        if (original, offset) in values:
                            values[target, offset] = values[original, offset]
            calculated = (calculate_vas_f_score(values) if task == 'F_SCORE' else
                          calculate_vas_m_score(values, 'GROSS_SHORT_TERM_TRADE'))
            if calculated['value'] != r[result_key]['value'] or calculated['variant'] != r[result_key]['variant']:
                raise ValueError('reviewed annual replay differs')
            rows.append(dict(symbol='FPT', year=year, task=task, period=str(year),
                basis=calculated['variant'], value=calculated['value'],
                decision_date=r['decision_date'], usable_from_date=max(x['usable_from_date'] for x in r['inputs']),
                pit_status='DATE_ONLY_ALL_CALCULATION_INPUTS_VERIFIED',
                calculation_mode='RECOMPUTED_FROM_PINNED_REVIEWED_INPUTS', source_result_path=source_path,
                source_record=dict(collection=name, year=year, decision_date=r['decision_date']),
                blockers=list(PRODUCTION_BLOCKERS)))
    for r in source['existing_eps_z']:
        if r['year'] not in years or r['decision_date'] > decision_day or r['value'] is None:
            continue
        if r['status'] != 'REFERENCE_QA_PASS' or r['qa']['passed'] is not True:
            raise ValueError('reviewed EPS/Z calculation QA failed')
        refs = [ref for item in r['inputs'] for ref in item['references']]
        values_at(refs, r['year'], r['decision_date'])
        values = {item['field']: item['references'][0]['fact']['value'] for item in r['inputs']}
        calculated = calculate(r['task'], values)
        if calculated['value'] != r['value']:
            raise ValueError('reviewed EPS/Z replay differs')
        field = 'annual_basic_eps_reference' if r['task'] == 'EPS_RECOMPUTE' else 'em_z_double_prime_reference'
        rows.append(dict(symbol='FPT', year=r['year'], task=r['task'], period=str(r['year']),
            basis=field, value=calculated['value'][field], decision_date=r['decision_date'],
            usable_from_date=r['usable_from_date'], pit_status='DATE_ONLY_ALL_CALCULATION_INPUTS_VERIFIED',
            calculation_mode='RECOMPUTED_FROM_PINNED_REVIEWED_INPUTS', source_result_path=source_path,
            source_record=dict(collection='existing_eps_z', year=r['year'], task=r['task']),
            blockers=list(PRODUCTION_BLOCKERS)))
    return rows


def assess(tasks, members, ledger):
    """Reference arithmetic never satisfies the strict original task checklist."""
    kinds = {r['ticker']: r['proposed_company_type'] for r in members}
    index = {}
    for i, r in enumerate(ledger):
        if r['value'] is not None and not Decimal(str(r['value'])).is_finite():
            raise ValueError('nonfinite reference value')
        if r['year'] is not None:
            key = (r['symbol'], r['year'], r['task'])
            if key in index:
                raise ValueError('duplicate annual reference; no basis priority')
            index[key] = i
    rows = []
    keys = set()
    for t in tasks:
        key = (t['symbol'], t['year'], t['task'])
        if key in keys or t['symbol'] not in kinds:
            raise ValueError('invalid candidate task membership or duplicate')
        keys.add(key)
        i = index.get(key)
        ref = ledger[i] if i is not None else None
        status = ('REVIEWED_REFERENCE_VALUE_AVAILABLE' if ref and ref['value'] is not None else
                  'SECTOR_TEMPLATE_REVIEW_REQUIRED' if kinds[t['symbol']] != 'Regular' else
                  'REVIEWED_INPUTS_REQUIRED')
        rows.append(dict(symbol=t['symbol'], year=t['year'], task=t['task'],
            proposed_company_type=kinds[t['symbol']], candidate_input_cells=t['candidate_input_cells'],
            required_input_cells=t['required_input_cells'], missing_candidate_inputs=t['missing_inputs'],
            candidate_all_inputs_present=t['candidate_input_cells'] == t['required_input_cells'],
            reference_status=status, reference_value=ref['value'] if ref else None,
            reference_ledger_index=i, reference_basis=ref['basis'] if ref else None,
            reference_pit_status=ref['pit_status'] if ref else 'EXACT_DOCUMENT_PUBLICATION_NOT_REVIEWED',
            strict_task_ready=False, strict_computed_value=None,
            blockers=list(ref['blockers']) if ref else list(t['blockers']), **CLOSED))
    summaries = []
    for member in members:
        symbol = member['ticker']
        annual = [r for r in rows if r['symbol'] == symbol]
        refs = [r for r in ledger if r['symbol'] == symbol]
        families = {r['task'] for r in refs if r['value'] is not None}
        summaries.append(dict(symbol=symbol, proposed_company_type=kinds[symbol],
            annual_reference_cells=sum(r['reference_value'] is not None for r in annual),
            reference_families_with_any_basis=len(families),
            nonannual_reference_values=sum(r['year'] is None and r['value'] is not None for r in refs),
            strict_ready_cells=0, financial_cluster_allowed=False,
            next_action='CLOSE_VARIANT_IDENTITY_REVISION_EVENT_ACCEPTANCE' if families else
                'REVIEW_SECTOR_SPECIFIC_TEMPLATE' if kinds[symbol] != 'Regular' else
                'REVIEW_EXACT_REPORT_NOTES_UNITS_SCOPE_AND_PUBLICATION'))
    return rows, summaries


def export(root, config_path, output):
    root = Path(root).resolve()
    c = json.loads(inside(root, config_path, 'configs').read_bytes())
    if c.get('version') != VERSION or any(c.get(k) is not False for k in CLOSED):
        raise ValueError('offline integration contract/gates required')
    day = date.fromisoformat(c['decision_date']).isoformat()
    verify_pins(root, c['input_pins'])
    verify_pins(root, c['code_pins'])
    trial = inside(root, c['trial_run'], 'data')
    verify_trial(root, c['trial_run'])
    evidence_pins(root, json.loads((trial/'references.json').read_bytes()))
    for path, pin in json.loads((trial/'references.json').read_bytes())['source_pins'].items():
        verify_pins(root, {path: pin})
    members = json.loads((trial/'plan.json').read_bytes())['members']
    tasks = json.loads((trial/'feature-readiness.json').read_bytes())
    trial_config = json.loads((trial/'config.json').read_bytes())
    if ([m['ticker'] for m in members] != trial_config['symbols'] or len(members) != 50
            or len({m['ticker'] for m in members}) != 50 or len(tasks) != 900
            or sorted(c['years']) != trial_config['score_years']):
        raise ValueError('exact frozen50/900 task scope required')
    source_path = c['annual_run'] + '/result.json'
    source = json.loads(inside(root, source_path, 'data').read_bytes())
    if any(source.get(k) is not False for k in ['financial_features_allowed', 'research_ready', 'full_universe_allowed']):
        raise ValueError('annual input attempted promotion')
    external = evidence_pins(root, source)
    for run, expected in source['input_manifest_sha256'].items():
        path = run + '/manifest.json'
        verify_pins(root, {path: expected})
        external[path] = expected
    ledger = history_rows(source, source_path, day, c['years'])
    out = inside(root, output, 'data')
    out.mkdir(parents=True, exist_ok=False)
    adapters, adapter_rows = references(root, c, out)
    adapter_results = {}
    for adapter in adapters:
        result_path = inside(root, adapter['output'] + '/results.json', 'data')
        data = json.loads(result_path.read_bytes())
        external.update(evidence_pins(root, data))
        adapter_results[result_path.relative_to(root).as_posix()] = data
    for r in adapter_rows:
        if r['decision_at'][:10] != day:
            continue
        if r['symbol'] == 'FPT' and r['period'] == '2025':
            continue  # historical replay already contains the exact annual metric
        annual = r['period'] == '2025'
        payload = adapter_results[Path(r['source_result_path']).as_posix()]
        source_rows = [x for x in payload['results'] if x.get('symbol', 'FPT') == r['symbol']
                       and x['decision_at'][:10] == day]
        if len(source_rows) != 1:
            raise ValueError('ambiguous reference adapter decision')
        original = source_rows[0]
        pit = ('DATE_ONLY_ADAPTER_INPUT_AVAILABILITY_CHECKED' if r['symbol'] == 'FPT' else
               'DATE_ONLY_ALL_ANNUAL_AUXILIARY_INPUTS_VERIFIED' if annual and original['all_auxiliary_publications_verified'] else
               'DATE_REFERENCE_PARTIAL_OR_TTM_BRIDGE_UNVERIFIED')
        ledger.append(dict(symbol=r['symbol'], year=2025 if annual else None,
            task={'EPS_TTM': 'EPS_RECOMPUTE', 'PE_TTM': 'PE'}.get(r['task'], r['task']),
            period=r['period'], basis=r['basis'], value=r['value'], decision_date=day,
            usable_from_date=original.get('usable_from_date') if annual else None, pit_status=pit,
            calculation_mode='EXISTING_REVIEWED_ADAPTER_REPLAY', source_result_path=r['source_result_path'],
            source_record=dict(task=r['task'], decision_at=r['decision_at'], period=r['period']),
            blockers=list(dict.fromkeys(PRODUCTION_BLOCKERS + r['blockers']))))
    for r in ledger:
        r.update(production_accepted=False, **CLOSED)
    rows, summaries = assess(tasks, members, ledger)
    member_symbols = {m['ticker'] for m in members}
    result = dict(version=VERSION, status='REFERENCE_INTEGRATION_COMPLETE_ACCEPTANCE_PARTIAL',
        decision_date=day, trial_run=c['trial_run'], reference_runs=adapters,
        source_result_path=source_path, source_evidence_pins=external,
        symbols=50, annual_task_rows=len(rows),
        annual_reference_cells=sum(r['reference_value'] is not None for r in rows),
        symbols_with_reference_values=sum(r['reference_families_with_any_basis'] > 0 for r in summaries),
        in_cohort_reference_values=sum(r['symbol'] in member_symbols and r['value'] is not None for r in ledger),
        out_of_cohort_controls=sorted({r['symbol'] for r in ledger} - member_symbols),
        annual_reference_counts=dict(Counter(r['task'] for r in rows if r['reference_value'] is not None)),
        strict_ready_cells=0, accepted_new_html_facts=0, new_network_requests=0,
        new_pdf_downloads=0, new_ocr_pages=0,
        join_policy='ASSESSMENT_ONLY_NO_PUBLICATION_OR_FACT_PROMOTION_TO_HTML', **CLOSED)
    for name, obj in [('config.json', c), ('results.json', result), ('reference-ledger.json', ledger),
                      ('assessment.json', rows), ('per-symbol.json', summaries)]:
        immutable_write(out/name, encoded(obj))
    for name, data in [('assessment.csv', rows), ('per-symbol.csv', summaries)]:
        fields = [k for k in data[0] if k not in ('blockers', 'missing_candidate_inputs')]
        immutable_write(out/name, csv_bytes(data, fields))
    for path in c['code_pins']:
        immutable_write(out/'code'/path, inside(root, path).read_bytes())
    seal(out)
    return result


def verify(root, run):
    root = Path(root).resolve()
    out = inside(root, run, 'data')
    verify_inventory(out)
    c = json.loads((out/'config.json').read_bytes())
    r = json.loads((out/'results.json').read_bytes())
    verify_pins(root, c['input_pins'])
    verify_pins(root, c['code_pins'])
    verify_pins(root, r['source_evidence_pins'])
    verify_trial(root, c['trial_run'])
    trial_refs = json.loads((inside(root, c['trial_run'], 'data')/'references.json').read_bytes())
    verify_pins(root, trial_refs['source_pins'])
    for a in r['reference_runs']:
        verify_pins(root, {a['output']+'/manifest.json': a['manifest_sha256']})
    tasks = json.loads((inside(root, c['trial_run'], 'data')/'feature-readiness.json').read_bytes())
    members = json.loads((inside(root, c['trial_run'], 'data')/'plan.json').read_bytes())['members']
    rows, summaries = assess(tasks, members, json.loads((out/'reference-ledger.json').read_bytes()))
    if rows != json.loads((out/'assessment.json').read_bytes()) or summaries != json.loads((out/'per-symbol.json').read_bytes()):
        raise ValueError('assessment replay differs')
    if any(r.get(k) is not False for k in CLOSED):
        raise ValueError('integration gate violation')
    return dict(status='PASS', annual_reference_cells=r['annual_reference_cells'],
        replay='BYTE_SEMANTIC_ASSESSMENT_MATCH', external_evidence_files=len(r['source_evidence_pins']),
        new_network_requests=0, gates_closed=True)
