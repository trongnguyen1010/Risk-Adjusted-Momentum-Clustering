"""Offline, reference-only precision QA; never changes reviewed facts or PIT gates."""
import csv
import io
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from .financial_api_input_review import FORMULAS, accounting, csv_bytes
from .financial_template_contract import finance_bridge
from .financial_history_documents import put
from ..features.financial_exploratory import calculate_core, REQUIRED
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside

CORE = {'ASSETS_CAPITAL', 'ASSETS_LIABILITIES_EQUITY', 'ASSET_PARTS',
        'LIABILITY_PARTS', 'GROSS_PROFIT', 'PRETAX_BRIDGE', 'AFTERTAX_BRIDGE'}
BRIDGE_FIELDS = ['reported_operating_profit', 'gross_profit', 'finance_income',
                 'finance_expense', 'associate_profit', 'selling_expense', 'administrative_expense']
VERSION = 'financial-precision-review-v1'


def residual_decision(difference, terms, absolute_cap='1', relative_cap='1e-9'):
    """Both caps must pass. Raw scale is not a canonical monetary-unit assertion."""
    if difference is None or not terms or any(type(x) is bool for x in terms):
        return 'HELD_MISSING_OR_INVALID'
    try:
        d = Decimal(str(difference))
        numbers = [Decimal(str(x)) for x in terms]
    except (ValueError, ArithmeticError):
        return 'HELD_MISSING_OR_INVALID'
    if not d.is_finite() or any(not n.is_finite() for n in numbers):
        return 'HELD_MISSING_OR_INVALID'
    if d == 0:
        return 'EXACT_EQUALITY'
    scale = max(abs(n) for n in numbers)
    if abs(d) <= Decimal(absolute_cap) and abs(d) <= scale * Decimal(relative_cap):
        return 'SMALL_RAW_RESIDUAL_REFERENCE_ONLY'
    return 'HELD_MATERIAL_OR_ABSOLUTE_DIFFERENCE'


def evaluate(values, displaced=False, absolute_cap='1', relative_cap='1e-9'):
    decisions = []
    for check, (_, lhs, rhs) in zip(accounting(values), FORMULAS):
        terms = [values[k] for k in [lhs, *rhs] if k in values]
        status = residual_decision(check['difference'], terms, absolute_cap, relative_cap)
        decisions.append(dict(check=check['check'], difference=check['difference'], status=status))
    bridge = finance_bridge(values)
    decisions.append(dict(check='FINANCE_BRIDGE', difference=bridge['difference'],
        status=residual_decision(bridge['difference'], [values[k] for k in BRIDGE_FIELDS if k in values],
                                 absolute_cap, relative_cap)))
    passed = {r['check'] for r in decisions if not r['status'].startswith('HELD')}
    # Optional checks may be absent, but any observed difference must pass both caps.
    bad = any(r['difference'] is not None and r['status'].startswith('HELD') for r in decisions)
    accepted = not displaced and CORE | {'FINANCE_BRIDGE'} <= passed and not bad
    return dict(quality_gate=accepted, displaced=displaced, checks=decisions)


def annual_filename_key(name):
    """Inventory hint only; not accepted document scope, vintage or issuer identity."""
    if re.search(r'(?:Q[1-4]|q[1-4]|quy)', name):
        return None
    match = re.match(r'^(?:\d+-)?([A-Z0-9]{3})[-_](?:FY)?((?:19|20)\d{2})(?:[-_.]|$)', name)
    return (match[1], int(match[2])) if match else None


def validate(c):
    if c.get('version') != VERSION or c.get('scope') != 'EXPLORATORY_REFERENCE_ONLY':
        raise ValueError('reference-only precision contract required')
    if any(c.get(k) is not False for k in ['network_allowed', 'pdf_download_allowed', 'ocr_allowed', 'research_promotion_allowed']):
        raise ValueError('network/PDF/OCR/research promotion forbidden')
    if c.get('absolute_raw_cap') != '1' or c.get('relative_cap') != '1e-9':
        raise ValueError('versioned precision caps differ')
    if c.get('years') != list(range(2016, 2026)):
        raise ValueError('unexpected coverage range')


def run(root, config_path):
    root = Path(root); c = json.loads(inside(root, config_path).read_bytes()); validate(c)
    pins = {}
    def pin(path, expected=None):
        body = inside(root, path).read_bytes(); sha = digest(body)
        if expected is not None and sha != expected:
            raise ValueError('input hash changed: ' + path)
        pins[path] = sha
        return body
    def read(path, expected=None):
        return json.loads(pin(path, expected))
    for path in [config_path, 'src/delta_t1/experiments/financial_precision_review.py',
                 'scripts/financial_precision_review.py', 'src/delta_t1/features/financial_exploratory.py',
                 'src/delta_t1/experiments/financial_api_input_review.py',
                 'src/delta_t1/experiments/financial_template_contract.py']:
        pin(path)
    manifests = {}
    for domain in ['api', 'template', 'baseline']:
        source = c[domain + '_result']; path = source['path']
        manifests[domain] = read(path + '/manifest.json', source['manifest_sha256'])
    api = c['api_result']['path']; template = c['template_result']['path']; baseline = c['baseline_result']['path']
    ams = read(api + '/symbol-manifests.json', manifests['api']['symbol-manifests.json'])
    tms = read(template + '/symbol-manifests.json', manifests['template']['symbol-manifests.json'])
    members = list(csv.DictReader(io.StringIO(pin(api + '/symbols-readiness.csv', manifests['api']['symbols-readiness.csv']).decode())))
    old = list(csv.DictReader(io.StringIO(pin(baseline + '/features.csv', manifests['baseline']['features.csv']).decode())))
    old_keys = {(r['registry_id'], int(r['year'])) for r in old}
    exact_keys = set(); dataset = []; checks = []; gaps = []; coverage = []
    for index, member in enumerate(sorted(members, key=lambda r: r['registry_id']), 1):
        rid = member['registry_id']; symbol = member['symbol']; regular = member['diagnostic_template_family'] == 'Regular'
        if not regular:
            coverage.append(dict(symbol=symbol, registry_id=rid, before_periods=0, after_periods=0,
                status='SECTOR_OR_TEMPLATE_REVIEW_REQUIRED', missing_years=c['years']))
            continue
        ae = ams[rid]; ap = Path(ae['path']); ma = read(ae['path'], ae['sha256'])
        source = (ap.parent / 'field-inputs.json').as_posix()
        fields = read(source, ma['field-inputs.json'])
        te = tms[rid]; tp = Path(te['path']); mt = read(te['path'], te['sha256'])
        changes = read((tp.parent / 'proposed-finance-fields.json').as_posix(), mt['proposed-finance-fields.json'])
        candidates = read((tp.parent / 'candidate-z-and-bridges.json').as_posix(), mt['candidate-z-and-bridges.json'])
        localpins = read((tp.parent / 'input-pins.json').as_posix(), mt['input-pins.json'])
        shifts = []
        for path, sha in localpins.items():
            if path.endswith('/displacements.json'): shifts.extend(read(path, sha))
        values = defaultdict(dict); overlay = defaultdict(set); by_year = defaultdict(list)
        for row in fields:
            if row['value'] is not None: values[row['year'], row['provider_type']][row['field']] = row['value']
        for row in changes:
            overlay[row['year'], row['provider_type'], row['proposed_field']].add(Decimal(row['value']))
        for (year, provider, field), vs in overlay.items():
            if len(vs) == 1: values[year, provider][field] = str(next(iter(vs)))
        for row in candidates: by_year[row['year']].append(row)
        ready = []
        for year in c['years']:
            parts = by_year[year]; base = dict(symbol=symbol, registry_id=rid, year=year)
            reasons = []; missing = []; decisions = None; feature = None
            if not parts: reasons.append('NO_ANNUAL_PARTITION_IN_ACQUIRED_PAGES')
            elif len(parts) != 1: reasons.append('MULTIPLE_PROVIDER_PARTITIONS_NO_SOURCE_PRIORITY')
            else:
                provider = parts[0]['provider_type']; v = values[year, provider]
                displaced = any(r['year'] == year and r['annual_provider_type'] == provider for r in shifts)
                decisions = evaluate(v, displaced, c['absolute_raw_cap'], c['relative_cap'])
                feature = calculate_core(v)
                if evaluate(v, displaced, '0', '0')['quality_gate'] and feature['values'] is not None:
                    exact_keys.add((rid, year))
                checks.extend(dict(**base, provider_type=provider, displaced=displaced, **r) for r in decisions['checks'])
                if displaced: reasons.append('DISPLACEMENT_REVIEW_REQUIRED')
                if not decisions['quality_gate']: reasons.append('ACCOUNTING_OR_FINANCE_QA_HELD')
                if feature['values'] is None: reasons.append(feature['status'])
                missing = sorted(REQUIRED - v.keys())
                if not reasons:
                    ready.append(year)
                    dataset.append(dict(**base, provider_type=provider, **feature['values'],
                        restored_vs_exact=(rid, year) not in old_keys, source_evidence=source,
                        qa_policy=VERSION, strict_pit_ready=False, research_ready=False,
                        financial_features_allowed=False, published_at=None,
                        scope='EXPLORATORY_RAW_UNIT_SCOPE_VINTAGE_HYPOTHESIS_NOT_FACT_ACCEPTANCE'))
            if reasons:
                gaps.append(dict(**base, reasons=reasons, missing_core_fields=missing,
                    next_action='CACHE_API_IDENTITY_AND_VINTAGE_REVIEW_BEFORE_DOCUMENT_REQUEST',
                    pdf_required_confirmed=False, document_candidate_key=f'{rid}:ANNUAL:{year}:SCOPE_UNRESOLVED',
                    primary_pdf_need_count=1, count_interpretation='ONE_CANDIDATE_ANNUAL_REVIEW_DOCUMENT_NOT_A_CONFIRMED_DOWNLOAD'))
        coverage.append(dict(symbol=symbol, registry_id=rid,
            before_periods=sum((rid, y) in old_keys for y in c['years']), after_periods=len(ready),
            status='FULL10_EXPLORATORY_REFERENCE' if len(ready) == 10 else 'PARTIAL_HISTORY_REFERENCE',
            missing_years=sorted(set(c['years']) - set(ready))))
        if index % 300 == 0: print(json.dumps(dict(completed=index, total=len(members))), flush=True)
    if exact_keys != old_keys: raise ValueError('exact-zero replay differs from sealed baseline')
    new_keys = {(r['registry_id'], r['year']) for r in dataset}
    if not old_keys <= new_keys: raise ValueError('new policy removed previously eligible observations')
    if len(new_keys) != len(dataset): raise ValueError('duplicate registry/year key')
    # Filename matching deliberately does not accept issuer identity/scope/vintage.
    cache = []; cache_by_key = defaultdict(list)
    for path in sorted((root / 'data/financial').rglob('*.pdf')):
        rel = path.relative_to(root).as_posix(); body = pin(rel); key = annual_filename_key(path.name)
        row = dict(path=rel, sha256=digest(body), bytes=len(body), symbol_hint=key[0] if key else None,
                   year_hint=key[1] if key else None, match_basis='FILENAME_HINT_ONLY_SCOPE_VINTAGE_UNVERIFIED')
        cache.append(row)
        if key: cache_by_key[key].append(rel)
    cov = {r['registry_id']: r for r in coverage}
    for gap in gaps:
        same = cache_by_key[gap['symbol'], gap['year']]
        comparative = cache_by_key[gap['symbol'], gap['year'] + 1]
        gap.update(cached_same_year_filename_candidates=same, cached_next_year_comparative_candidates=comparative,
            cache_status='CACHED_CANDIDATE_REVIEW_FIRST' if same or comparative else 'NO_FILENAME_MATCH_NOT_PROOF_OF_CACHE_ABSENCE',
            priority='NEAR_FULL10_9_OF10' if cov[gap['registry_id']]['after_periods'] == 9 else
                     'NEAR_FULL10_8_OF10' if cov[gap['registry_id']]['after_periods'] == 8 else 'GENERAL_GAP_TRIAGE')
    counts = Counter(r['registry_id'] for r in dataset)
    summary = dict(status='COMPLETE_OFFLINE_EXPLORATORY_PRECISION_QA_AND_DOCUMENT_TRIAGE',
        baseline_rows=len(old), feature_rows=len(dataset), restored_rows=len(new_keys-old_keys),
        baseline_candidates=len({r['registry_id'] for r in old}), distinct_candidates=len(counts),
        baseline_full10=sum(r['before_periods'] == 10 for r in coverage), full10=sum(n == 10 for n in counts.values()),
        rows_by_year=dict(sorted(Counter(r['year'] for r in dataset).items())),
        coverage_histogram=dict(sorted(Counter(r['after_periods'] for r in coverage).items())),
        small_residual_checks=sum(r['status'] == 'SMALL_RAW_RESIDUAL_REFERENCE_ONLY' for r in checks),
        regular_annual_gap_review_cases=len(gaps), gap_reason_counts=dict(Counter(reason for r in gaps for reason in r['reasons'])),
        candidate_primary_annual_documents=len(gaps),
        candidate_cases_with_cache_filename_hints=sum(r['cache_status']=='CACHED_CANDIDATE_REVIEW_FIRST' for r in gaps),
        candidate_cases_without_cache_filename_hints=sum(r['cache_status']!='CACHED_CANDIDATE_REVIEW_FIRST' for r in gaps),
        near_full10_9of10_gap_cases=sum(r['priority']=='NEAR_FULL10_9_OF10' for r in gaps),
        near_full10_8of10_gap_cases=sum(r['priority']=='NEAR_FULL10_8_OF10' for r in gaps),
        cached_pdf_files=len(cache), cached_unique_pdf_hashes=len({r['sha256'] for r in cache}),
        confirmed_new_pdf_downloads_required=None,
        pdf_count_scope='CORE_RATIO_ANNUAL_GAP_TRIAGE_ONLY;NOT_SIX_FAMILY_OR_PIT_DOCUMENT_COUNT',
        pdf_count_limitation='Gaps may resolve through API/cache or represent unavailable history; scope/vintage/issuer and document URLs not accepted. One candidate primary report per case is a planning scenario, neither lower nor upper bound on final PDF files.',
        nonregular_candidates_not_covered=sum(r['status']=='SECTOR_OR_TEMPLATE_REVIEW_REQUIRED' for r in coverage),
        network_requests=0, pdf_downloads=0, ocr_pages=0, model_recomputed=False,
        exact_zero_key_parity=True, baseline_preserved=True, strict_pit_ready=False, research_ready=False,
        original_six_metric_goal='PARTIAL_UNCHANGED_87_REFERENCE_ROWS_11_ISSUERS_5_FULL6_COHORTS')
    products = {'summary.json':encoded(summary), 'features.csv':csv_bytes(dataset),
                'coverage-by-symbol.csv':csv_bytes(coverage), 'qa-checks.csv':csv_bytes(checks),
                'document-review-candidates.csv':csv_bytes(gaps), 'cached-pdf-inventory.csv':csv_bytes(cache),
                'config.json':encoded(c), 'input-pins.json':encoded(pins)}
    manifest = {n:digest(b) for n,b in products.items()}
    out = inside(root, c['output_root']) / 'results' / digest(encoded(manifest))[:20]
    for name, body in products.items(): put(out/name, body)
    put(out/'manifest.json', manifest)
    report = inside(root, c['report_root'])
    put(report/'result-ref.json', dict(path=out.relative_to(root).as_posix(), manifest_sha256=digest((out/'manifest.json').read_bytes())))
    return dict(summary, output=out.relative_to(root).as_posix())
