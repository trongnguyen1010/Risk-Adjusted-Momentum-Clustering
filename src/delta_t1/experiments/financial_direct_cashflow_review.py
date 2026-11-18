"""Recover explicit direct-method CFO from cached annual API, reference scope only."""
import csv
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from .financial_api_input_review import csv_bytes
from .financial_history_documents import put
from .financial_history_qa import norm
from .financial_precision_review import evaluate, residual_decision
from .financial_template_candidates import parse_candidates
from ..features.financial_exploratory import calculate_core
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside

VERSION = 'financial-direct-cashflow-review-v1'
LABELS = {
    'HDKD_2': '1. Tiền thu từ bán hàng, cung cấp dịch vụ và doanh thu khác',
    'HDKD_3': '2. Tiền chỉ trả cho người cung cấp hàng hóa và dịch vụ',
    'HDKD_4': '3. Tiền chỉ trả cho người lao động',
    'HDKD_5': '4. Tiền chi trả lãi vay',
    'HDKD_6': '5. Tiến chỉ nộp thuê thu nhập doanh nghiệp',
    'HDKD_7': '6. Tiền thu khác từ hoạt động kinh doanh',
    'HDKD_8': '7. Tiền chi khác cho hoạt động kinh doanh',
    'HDKD_9': 'Lưu chuyển tiền thuần từ hoạt động kinh doanh',
}


def direct_observations(rows):
    """No positional inference: require eight exact code+normalized-label pairs."""
    grouped = defaultdict(list)
    for row in rows:
        if row['statement'] == 'LCTT' and row['group'] == 'HDKD' and row['mode'] == 'NAM' and row['quarter'] == 0:
            grouped[row['year'], row['provider_type'], row['source_path'], row['period_occurrence']].append(row)
    result = []
    for (year, provider, path, occurrence), cells in sorted(grouped.items(), key=str):
        codes = defaultdict(list)
        for row in cells: codes[row['raw_code']].append(row)
        if 'HDKD_9' not in codes: continue
        base = dict(year=year, provider_type=provider, source_path=path, period_occurrence=occurrence)
        if any(len(codes[code]) != 1 for code in LABELS):
            result.append(dict(**base, status='HELD_MISSING_OR_DUPLICATE_CODE', value=None)); continue
        selected = [codes[code][0] for code in LABELS]
        extra = [r for r in cells if r['raw_code'] not in LABELS]
        if any(r['value_status'] != 'NUMERIC_CANDIDATE' or r['value'] is None or Decimal(r['value']) != 0 for r in extra):
            result.append(dict(**base, status='HELD_NONZERO_OR_INVALID_EXTRA_CODE', value=None)); continue
        if any(r['mapping_status'] != 'UNIQUE_CODE_LABEL_CANDIDATE' or norm(r['label']) != norm(LABELS[r['raw_code']]) for r in selected):
            result.append(dict(**base, status='HELD_CODE_LABEL_OR_TEMPLATE', value=None)); continue
        if any(r['value_status'] != 'NUMERIC_CANDIDATE' or r['value'] is None for r in selected):
            result.append(dict(**base, status='HELD_MISSING_INVALID_COMPONENT', value=None)); continue
        numbers = {r['raw_code']: Decimal(r['value']) for r in selected}
        difference = numbers['HDKD_9'] - sum(numbers[c] for c in LABELS if c != 'HDKD_9')
        decision = residual_decision(str(difference), list(numbers.values()))
        total = codes['HDKD_9'][0]
        result.append(dict(**base, status='DIRECT_CFO_COMPONENT_SUM_CHECKED' if not decision.startswith('HELD') else 'HELD_COMPONENT_SUM',
            value=total['value'] if not decision.startswith('HELD') else None,
            raw_total=total['value'], component_difference=str(difference), component_decision=decision,
            source_sha256=total['source_sha256'], template_sha256=total['template_sha256'],
            provider_unit=total['provider_unit'], raw_code='HDKD_9', label=total['label'],
            raw_cell_ordinal=total['raw_cell_ordinal'], accepted=False, strict_pit_ready=False))
    return result


def resolve_direct(observations):
    if not observations: return None, 'NO_EXACT_DIRECT_TEMPLATE_OBSERVATION'
    if any(r['value'] is None for r in observations): return None, 'INVALID_OR_FAILED_COMPONENT_OBSERVATION'
    unique = {Decimal(r['value']) for r in observations}
    if len(unique) != 1: return None, 'CONFLICTING_CFO_OBSERVATIONS_NO_SELECTION'
    return str(next(iter(unique))), 'DIRECT_CFO_RAW_VALUE_REFERENCE_ONLY'


def longest_run(years):
    best = current = 0; previous = None
    for year in sorted(set(years)):
        current = current + 1 if previous is not None and year == previous + 1 else 1
        best = max(best, current); previous = year
    return best


def run(root, config_path):
    root = Path(root); c = json.loads(inside(root, config_path).read_bytes())
    if c.get('version') != VERSION or c.get('scope') != 'EXPLORATORY_REFERENCE_ONLY' or any(c.get(k) is not False for k in ['network_allowed', 'pdf_download_allowed', 'ocr_allowed', 'research_promotion_allowed']):
        raise ValueError('explicit offline reference-only contract required')
    pins = {}
    def pin(path, expected=None):
        body = inside(root, path).read_bytes(); sha = digest(body)
        if expected is not None and sha != expected: raise ValueError('input hash changed: ' + path)
        pins[path] = sha; return body
    def read(path, expected=None): return json.loads(pin(path, expected))
    def csvread(path, expected=None): return list(csv.DictReader(io.StringIO(pin(path, expected).decode('utf-8-sig'))))
    for path in [config_path, 'scripts/financial_direct_cashflow_review.py',
                 'src/delta_t1/experiments/financial_direct_cashflow_review.py',
                 'src/delta_t1/experiments/financial_precision_review.py',
                 'src/delta_t1/experiments/financial_template_candidates.py',
                 'src/delta_t1/experiments/financial_history_qa.py',
                 'src/delta_t1/features/financial_exploratory.py']:
        pin(path)
    inputs = {}
    for name in ['precision', 'api', 'template']:
        s = c[name + '_result']; inputs[name] = read(s['path']+'/manifest.json', s['manifest_sha256'])
    p = c['precision_result']['path']; a = c['api_result']['path']; t = c['template_result']['path']
    features = csvread(p+'/features.csv', inputs['precision']['features.csv'])
    gaps = csvread(p+'/document-review-candidates.csv', inputs['precision']['document-review-candidates.csv'])
    previous_coverage = csvread(p+'/coverage-by-symbol.csv', inputs['precision']['coverage-by-symbol.csv'])
    asm = read(a+'/symbol-manifests.json', inputs['api']['symbol-manifests.json'])
    tsm = read(t+'/symbol-manifests.json', inputs['template']['symbol-manifests.json'])
    old_keys = {(r['registry_id'], int(r['year'])) for r in features}
    targets = defaultdict(list)
    for gap in gaps:
        if 'MISSING_INPUTS' in json.loads(gap['reasons']): targets[gap['registry_id']].append(gap)
    observations = []; attempts = []; recovered = []
    for index, (rid, issues) in enumerate(sorted(targets.items()), 1):
        symbol = issues[0]['symbol']; ae = asm[rid]; ap = Path(ae['path']).parent
        am = read(ae['path'], ae['sha256'])
        fields = read((ap/'field-inputs.json').as_posix(), am['field-inputs.json'])
        sourcepins = read((ap/'input-pins.json').as_posix(), am['input-pins.json'])['sources']
        parsed = []; seenraw = set()
        for path, sha in sorted(sourcepins.items()):
            if '/receipts/' not in path: continue
            receipt = read(path, sha); task = receipt['task']
            if task['symbol'] != symbol or Path(path).stem != task['id']: raise ValueError('receipt identity mismatch')
            if (task.get('kind'), task.get('mode'), task.get('statement'), task.get('group')) != ('REPORT','NAM','LCTT','HDKD'): continue
            rec = receipt.get('record')
            if not rec or rec['path'] in seenraw: continue
            if sourcepins.get(rec['path']) != rec['sha256']: raise ValueError('raw outside source pin chain')
            body = pin(rec['path'], rec['sha256']); seenraw.add(rec['path'])
            parsed.extend(parse_candidates(body, task, rec['path'], rec['sha256']))
        direct = direct_observations(parsed)
        observations.extend(dict(symbol=symbol, registry_id=rid, **r) for r in direct)
        te = tsm[rid]; tp = Path(te['path']).parent; tm = read(te['path'], te['sha256'])
        changes = read((tp/'proposed-finance-fields.json').as_posix(), tm['proposed-finance-fields.json'])
        partitions = read((tp/'candidate-z-and-bridges.json').as_posix(), tm['candidate-z-and-bridges.json'])
        localpins = read((tp/'input-pins.json').as_posix(), tm['input-pins.json']); shifts = []
        for path, sha in localpins.items():
            if path.endswith('/displacements.json'): shifts.extend(read(path, sha))
        values = defaultdict(dict); overlay = defaultdict(set)
        for r in fields:
            if r['value'] is not None: values[r['year'], r['provider_type']][r['field']] = r['value']
        for r in changes: overlay[r['year'], r['provider_type'], r['proposed_field']].add(Decimal(r['value']))
        for (year, provider, field), vs in overlay.items():
            if len(vs) == 1: values[year, provider][field] = str(next(iter(vs)))
        for gap in issues:
            year = int(gap['year']); parts = [r for r in partitions if r['year'] == year]
            row = dict(symbol=symbol, registry_id=rid, year=year, restored=False)
            if len(parts) != 1:
                attempts.append(dict(**row, status='HELD_PROVIDER_PARTITION_COUNT')); continue
            provider = parts[0]['provider_type']; v = dict(values[year, provider])
            obs = [r for r in direct if r['year'] == year and r['provider_type'] == provider]
            value, status = resolve_direct(obs)
            row.update(provider_type=provider, cfo_status=status, observation_count=len(obs))
            # Do not replace existing ambiguous/invalid CFO or overrule any original value.
            existing = [r for r in fields if r['year'] == year and r['provider_type'] == provider and r['field']=='operating_cash_flow']
            if existing:
                attempts.append(dict(**row, status='HELD_EXISTING_CFO_OBSERVATIONS_NO_OVERRIDE')); continue
            if value is None:
                attempts.append(dict(**row, status=status)); continue
            v['operating_cash_flow'] = value
            displaced = any(r['year'] == year and r['annual_provider_type'] == provider for r in shifts)
            qa = evaluate(v, displaced); calc = calculate_core(v)
            if not qa['quality_gate'] or calc['values'] is None:
                attempts.append(dict(**row, status='HELD_UNCHANGED_ACCOUNTING_DISPLACEMENT_OR_CORE_GATES',
                    quality_gate=qa['quality_gate'], feature_status=calc['status'])); continue
            required_finance = {'finance_income','finance_expense','interest_expense','associate_profit'}
            if any(len(overlay[year, provider, f]) != 1 for f in required_finance):
                attempts.append(dict(**row, status='HELD_FINANCE_TEMPLATE_CONTRACT')); continue
            new = dict(symbol=symbol, registry_id=rid, year=year, provider_type=provider,
                **calc['values'], restored_vs_exact=True, source_evidence=(ap/'field-inputs.json').as_posix(),
                cfo_evidence=sorted({r['source_path'] for r in obs}), qa_policy='financial-precision-review-v1',
                recovery_policy=VERSION, strict_pit_ready=False, research_ready=False, financial_features_allowed=False,
                published_at=None, scope='EXPLORATORY_RAW_UNIT_SCOPE_VINTAGE_HYPOTHESIS_NOT_FACT_ACCEPTANCE')
            recovered.append(new)
            row['restored'] = True
            attempts.append(dict(**row, status='RESTORED_REFERENCE_CORE_RATIOS', cfo_raw_value=value))
        if index % 40 == 0: print(json.dumps(dict(completed=index, total=len(targets), restored=len(recovered))), flush=True)
    # CSV strings are retained for old observations; no old values or scope flags changed.
    dataset = sorted(features + recovered, key=lambda r:(r['registry_id'], int(r['year'])))
    keys = {(r['registry_id'], int(r['year'])) for r in dataset}
    if len(keys) != len(dataset) or not old_keys <= keys: raise ValueError('key duplication or old row loss')
    byid = defaultdict(set)
    for row in dataset: byid[row['registry_id']].add(int(row['year']))
    coverage = []
    for row in previous_coverage:
        rid = row['registry_id']; years = sorted(byid[rid]); longest = longest_run(years)
        coverage.append(dict(symbol=row['symbol'], registry_id=rid, before_periods=int(row['after_periods']),
            after_periods=len(years), valid_years=years, missing_years=sorted(set(range(2016,2026))-set(years)),
            longest_consecutive_annual_periods=longest, full10=len(years)==10,
            coverage_only_not_model_or_pit_acceptance=True))
    remaining = [r for r in gaps if (r['registry_id'], int(r['year'])) not in keys]
    summary = dict(status='COMPLETE_OFFLINE_DIRECT_CFO_REFERENCE_RECOVERY',
        baseline_feature_rows=len(features), restored_feature_rows=len(recovered), feature_rows=len(dataset),
        distinct_candidates=sum(bool(y) for y in byid.values()),
        full10_before=sum(int(r['after_periods'])==10 for r in previous_coverage),
        full10_after=sum(len(y)==10 for y in byid.values()),
        rows_by_year=dict(sorted(Counter(int(r['year']) for r in dataset).items())),
        consecutive_history_counts={str(n):sum(longest_run(y)>=n for y in byid.values()) for n in [3,5,8,10]},
        min_period_counts={str(n):sum(len(y)>=n for y in byid.values()) for n in [3,5,8,10]},
        recovery_attempts=len(attempts), targeted_symbols=len(targets),
        attempt_status_counts=dict(Counter(r['status'] for r in attempts)),
        direct_observation_status_counts=dict(Counter(r['status'] for r in observations)),
        remaining_regular_annual_gap_cases=len(remaining),
        remaining_cache_hint_cases=sum(r['cache_status']=='CACHED_CANDIDATE_REVIEW_FIRST' for r in remaining),
        confirmed_new_pdf_downloads_required=None, pdf_downloads=0, network_requests=0, ocr_pages=0,
        strict_pit_ready=False, research_ready=False, model_recomputed=False,
        original_six_metric_goal='PARTIAL_UNCHANGED',
        over1000_full10_achieved=sum(len(y)==10 for y in byid.values())>1000,
        coverage_is_not_research_eligibility=True)
    products = {'summary.json':encoded(summary), 'features.csv':csv_bytes(dataset),
                'coverage-by-symbol.csv':csv_bytes(coverage), 'cfo-observations.csv':csv_bytes(observations),
                'recovery-attempts.csv':csv_bytes(attempts), 'recovered-rows.csv':csv_bytes(recovered),
                'remaining-document-review-candidates.csv':csv_bytes(remaining),
                'input-pins.json':encoded(pins), 'config.json':encoded(c)}
    manifest = {name:digest(body) for name,body in products.items()}
    out = inside(root,c['output_root'])/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items(): put(out/name,body)
    put(out/'manifest.json',manifest)
    put(inside(root,c['report_root'])/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    return dict(summary,output=out.relative_to(root).as_posix())
