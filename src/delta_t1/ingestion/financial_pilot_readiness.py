"""Offline document evidence overlay; no canonical promotion or score calculation."""
import csv
import io
import json
import math
from collections import Counter
from pathlib import Path

from .cafef_financial import digest, encoded, immutable_write
from .financial_documents import verify_inventory
from .financial_document_review import rejected_hashes

ALIASES = {'basic_eps': 'vendor_basic_eps', 'diluted_eps': 'vendor_diluted_eps',
           'weighted_average_common_shares': 'weighted_average_basic_shares',
           'eps_adjusted_numerator': 'eps_adjusted_earnings_numerator'}
INSTANT = {'current_assets', 'total_assets', 'current_liabilities', 'total_liabilities',
           'total_equity', 'retained_earnings', 'net_tangible_ppe', 'net_intangible_assets',
           'net_finance_lease_assets', 'fixed_assets', 'cash_and_equivalents', 'non_controlling_interests',
           'inventory', 'contributed_capital', 'long_term_borrowings',
           'short_term_borrowings_and_leases', 'parent_common_equity',
           'historical_common_shares_outstanding', 'long_term_debt_including_current_portion',
           'customer_receivables_short_term', 'gross_short_term_trade_receivables',
           'all_short_term_receivables_allowance', 'noncurrent_loans_and_finance_leases',
           'outstanding_common_shares', 'long_term_borrowings_including_current_portion',
           'long_term_finance_lease_balance_including_current_portion',
           'long_term_borrowings_and_leases_including_current_portion',
           'long_term_loan_current_portion', 'long_term_borrowings_and_leases_current_portion'}
SIGNALS = {
 'positive_roa': [('income_before_extraordinary_items', 0), ('total_assets', -1)],
 'positive_cfo': [('operating_cash_flow', 0), ('total_assets', -1)],
 'improved_roa': [('income_before_extraordinary_items', 0), ('income_before_extraordinary_items', -1), ('total_assets', -1), ('total_assets', -2)],
 'cash_accrual_quality': [('operating_cash_flow', 0), ('income_before_extraordinary_items', 0), ('total_assets', -1)],
 'reduced_leverage': [('long_term_debt_including_current_portion', 0), ('long_term_debt_including_current_portion', -1), ('total_assets', 0), ('total_assets', -1), ('total_assets', -2)],
 'improved_liquidity': [('current_assets', 0), ('current_assets', -1), ('current_liabilities', 0), ('current_liabilities', -1)],
 'no_parent_issuance': [('parent_common_equity_issuance_verified', 0)],
 'improved_gross_margin': [('gross_profit', 0), ('gross_profit', -1), ('net_revenue', 0), ('net_revenue', -1)],
 'improved_turnover': [('net_revenue', 0), ('net_revenue', -1), ('total_assets', 0), ('total_assets', -1), ('total_assets', -2)]}
CORE_FIELDS = ('current_assets', 'total_assets', 'current_liabilities',
               'net_revenue', 'gross_profit', 'net_profit', 'operating_cash_flow')


def eligible_fact(fact):
    """Calendar annual/instant only; do not backfill original vintages from later quotes."""
    year = fact.get('year')
    if type(year) is not int or fact.get('statement_scope') != 'CONSOLIDATED':
        return False
    if fact.get('validation_status') != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED':
        return False
    if fact.get('accounting_framework') != 'VAS':
        return False
    value = fact.get('value')
    if type(value) not in (int, float) or not math.isfinite(value):
        return False
    if fact.get('unit') not in ('VND', 'VND_PER_SHARE', 'SHARES', 'INDICATOR'):
        return False
    if fact.get('period_end') != f'{year}-12-31':
        return False
    if any(x in fact.get('vintage', '') for x in ['PREVIOUSLY_REPORTED', 'ADJUSTMENT_DISCLOSED']):
        return False
    field = ALIASES.get(fact.get('item'), fact.get('item'))
    if field == 'parent_common_equity_issuance_verified':
        if type(value) is not int or value not in (0, 1) or fact.get('derivation', {}).get('rule') != 'PARENT_COMMON_ISSUANCE_OCCURRED_VERIFIED':
            return False
    expected_unit = ('INDICATOR' if field == 'parent_common_equity_issuance_verified'
                     else 'VND_PER_SHARE' if field in ('vendor_basic_eps', 'vendor_diluted_eps')
                     else 'SHARES' if field in ('weighted_average_basic_shares', 'weighted_average_diluted_shares',
                                                'historical_common_shares_outstanding', 'outstanding_common_shares', 'parent_new_common_shares_issued')
                     else 'VND')
    if fact['unit'] != expected_unit:
        return False
    if field in INSTANT:
        return fact.get('period_start') is None and fact.get('period_semantics') == 'INSTANT'
    return fact.get('period_start') == f'{year}-01-01'


def reconcile(baseline, facts, target_years=(2021, 2022, 2023, 2024, 2025), rejected_pdf_hashes=()):
    if baseline.get('financial_features_allowed') is not False:
        raise ValueError('baseline cannot approve financial features')
    accepted = [f for f in facts if eligible_fact(f) and f.get('pdf_sha256') not in rejected_pdf_hashes]
    rows = []
    for original in baseline['rows']:
        row = dict(original)
        selected = [f for f in accepted if f['symbol'] == row['symbol'] and f['year'] == row['year']
                    and ALIASES.get(f['item'], f['item']) == row['field']]
        # Different PDF vintages stay separate; differences are not resolved by latest.
        groups = {}
        for fact in selected:
            key = (fact['pdf_sha256'], fact.get('vintage', 'DOCUMENT_CURRENT'))
            groups.setdefault(key, set()).add((str(fact['value']), fact['unit']))
        conflict = any(len(v) > 1 for v in groups.values())
        row.update(document_evidence=selected,
                   document_vintages=len(groups),
                   evidence_status='DOCUMENT_VALUE_CONFLICT' if conflict else
                   'DOCUMENT_VALUE_VERIFIED_PIT_PENDING' if selected else
                   'RAW_UNVERIFIED' if row['candidate_values'] else
                   'NOTE_REVIEW_REQUIRED' if row['presence_status'] == 'DOCUMENT_NOTE_REVIEW_REQUIRED' else 'MISSING_UNRESOLVED',
                   financial_features_allowed=False, available_at=None,
                   selected_canonical_value=None)
        rows.append(row)
    by_key = {(r['symbol'], r['year'], r['field']): r for r in rows}
    dependencies = []
    for symbol in sorted({r['symbol'] for r in rows}):
        for year in target_years:
            for signal, fields in SIGNALS.items():
                required = [dict(field=f, year=year+offset,
                     value_status=by_key.get((symbol, year+offset, f), {}).get('evidence_status', 'MISSING_UNRESOLVED')) for f, offset in fields]
                dependencies.append(dict(symbol=symbol, year=year, signal=signal, dependencies=required,
                    document_inputs_present=all(r['value_status'] == 'DOCUMENT_VALUE_VERIFIED_PIT_PENDING' for r in required),
                    compatible_vintage_status='UNVERIFIED', pit_status='NOT_READY', signal_value=None, score_value=None))
    core_coverage = []
    for symbol in sorted({r['symbol'] for r in rows}):
        core = [r for r in rows if r['symbol'] == symbol and r['field'] in CORE_FIELDS]
        core_coverage.append(dict(symbol=symbol, required_cells=len(core),
            document_verified_cells=sum(r['evidence_status'] == 'DOCUMENT_VALUE_VERIFIED_PIT_PENDING' for r in core),
            pit_ready_cells=0))
    return dict(version='financial-pilot-readiness-v1', rows=rows, f_score_dependencies=dependencies,
                core_fields=list(CORE_FIELDS), core_coverage=core_coverage,
                accepted_annual_observations=len(accepted), excluded_observations=len(facts)-len(accepted),
                quarantined_observations=sum(f.get('pdf_sha256') in rejected_pdf_hashes for f in facts),
                counts=dict(Counter(r['evidence_status'] for r in rows)),
                financial_features_allowed=False, financial_pit_gate='NOT_READY')


def export(baseline_run, fact_runs, output, document_review_run=None, correction_run=None):
    baseline_run = Path(baseline_run).resolve()
    verify_inventory(baseline_run)
    inputs = {str(baseline_run): digest((baseline_run / 'manifest.json').read_bytes())}
    rejected = rejected_hashes(document_review_run)
    if document_review_run is not None:
        review = Path(document_review_run).resolve()
        inputs[str(review)] = digest((review / 'manifest.json').read_bytes())
    facts = []
    for run in map(Path, fact_runs):
        run = run.resolve(); verify_inventory(run)
        inputs[str(run)] = digest((run / 'manifest.json').read_bytes())
        data = json.loads((run / 'facts.json').read_bytes())
        if data.get('financial_features_allowed') is not False:
            raise ValueError('evidence cannot grant eligibility')
        for fact in data['facts']:
            if eligible_fact(fact):
                for kind in ['pdf', 'image']:
                    if digest(Path(fact[f'{kind}_path']).read_bytes()) != fact[f'{kind}_sha256']:
                        raise ValueError('visual evidence reference hash mismatch')
                framework = fact.get('framework_evidence', {})
                if framework.get('image_path') and digest(Path(framework['image_path']).read_bytes()) != framework['image_sha256']:
                    raise ValueError('framework evidence reference hash mismatch')
            facts.append(fact)
    excluded_review=[]
    if correction_run is not None:
        from .financial_review_corrections import apply_review_corrections, verify_correction_evidence
        review=Path(correction_run).resolve();verify_inventory(review)
        inputs[str(review)]=digest((review/'manifest.json').read_bytes())
        data=json.loads((review/'corrections.json').read_bytes())
        verify_correction_evidence(data)
        facts,excluded_review=apply_review_corrections(facts,data)
    result = reconcile(json.loads((baseline_run / 'requirements.json').read_bytes()), facts, rejected_pdf_hashes=rejected)
    result['excluded_review_transcriptions']=excluded_review
    result['rejected_pdf_hashes'] = sorted(rejected)
    result['input_manifests_sha256'] = inputs
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=False)
    immutable_write(output / 'readiness.json', encoded(result))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=['symbol','year','field','presence_status','evidence_status','document_vintages','financial_features_allowed'], extrasaction='ignore')
    writer.writeheader(); writer.writerows(result['rows'])
    immutable_write(output / 'readiness.csv', stream.getvalue().encode('utf-8-sig'))
    immutable_write(output / 'analyzer.py', Path(__file__).read_bytes())
    immutable_write(output / 'manifest.json', encoded({'files': {p.name:digest(p.read_bytes()) for p in output.iterdir() if p.is_file()}}))
    return result
