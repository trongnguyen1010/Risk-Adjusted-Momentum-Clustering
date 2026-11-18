"""Offline, pinned full-ten-year reference cohort; reuse the approved static model."""
import csv
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from .financial_api_input_review import csv_bytes
from .financial_exploratory import fit_year, validate_mode, CODE
from .financial_history_documents import put
from .financial_acquisition_overnight import state_file
from .financial_direct_cashflow_review import direct_observations, resolve_direct
from .financial_template_candidates import parse_candidates
from ..features.financial_exploratory import FEATURES, REQUIRED, calculate_core
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside

VERSION = 'financial-full10-baseline-v1'


def validate_rows(rows, members, years, expected):
    ids = [r['registry_id'] for r in members]
    if len(ids) != expected or len(set(ids)) != expected:
        raise ValueError('cohort size or duplicate identity')
    symbols = {r['registry_id']: r['symbol'] for r in members}
    seen = set()
    for r in rows:
        key = r['registry_id'], int(r['year'])
        if key in seen or key[0] not in symbols or r['symbol'] != symbols[key[0]]:
            raise ValueError('duplicate key or cohort identity mismatch')
        seen.add(key)
        if any(str(r.get(k)).lower() != 'false' for k in
               ['strict_pit_ready', 'research_ready', 'financial_features_allowed']):
            raise ValueError('reference gates changed')
        for f in FEATURES:
            if not math.isfinite(float(r[f])):
                raise ValueError('nonfinite ratio')
    if seen != {(rid, y) for rid in ids for y in years}:
        raise ValueError('incomplete ten-year cohort')


def extract_values(row, load, raw=None):
    """Read the already-selected source partition; never select another provider."""
    ref = row['source_evidence']
    paths = json.loads(ref) if ref.startswith('[') else [ref]
    fields = []
    year = int(row['year'])
    for path in paths:
        obj = load(path)
        if path.endswith('/manifest.json'):
            facts_path = str(Path(path).parent / 'facts.json').replace('\\', '/')
            obj = load(facts_path, obj['facts.json'])
        if not row['source_kind']:
            fields += [x for x in obj if x['year'] == year and
                       x['provider_type'] == row['provider_type'] and x['value'] is not None]
        elif row['source_kind'] == 'DSTOCK_API_EXPLORATORY_COMPLETE_VECTOR':
            cases = [x for x in obj['cases'] if x['target']['registry_id'] == row['registry_id']
                     and int(x['target']['year']) == year]
            if len(cases) != 1 or not cases[0]['eligible_reference']:
                raise ValueError('DStock selected case differs')
            return cases[0]['values']
        elif 'reviews' in obj:
            reviews = [x for x in obj['reviews'] if x['symbol'] == row['symbol'] and x['year'] == year
                       and x['pdf_sha256'] == row['pdf_sha256']]
            if len(reviews) != 1:
                raise ValueError('reviewed document differs')
            fields += reviews[0]['fields']
        elif 'fields' in obj:
            if obj['symbol'] != row['symbol'] or obj['year'] != year:
                raise ValueError('HTML review identity differs')
            fields += obj['fields']
        else:
            facts = obj if isinstance(obj, list) else obj['facts']
            fields += [x for x in facts if x['symbol'] == row['symbol'] and x['year'] == year
                       and x.get('pdf_sha256', x.get('provenance', {}).get('pdf_sha256')) == row['pdf_sha256']]
    values = defaultdict(set)
    for f in fields:
        if f['field'] in REQUIRED:
            values[f['field']].add(str(f.get('reviewed_value', f.get('value'))))
    if any(len(v) != 1 for v in values.values()):
        raise ValueError('ambiguous source field values')
    result = {k: next(iter(v)) for k, v in values.items()}
    if 'operating_cash_flow' not in result and row.get('cfo_evidence'):
        observations = []
        for path in json.loads(row['cfo_evidence']):
            body = raw(path, Path(path).stem)
            task = dict(symbol=row['symbol'], statement='LCTT', mode='NAM', group='HDKD')
            observations += direct_observations(parse_candidates(body, task, path, digest(body)))
        observations = [x for x in observations if x['year'] == year and x['provider_type'] == row['provider_type']]
        value, status = resolve_direct(observations)
        if value is None:
            raise ValueError('direct CFO no longer resolves: ' + status)
        result['operating_cash_flow'] = value
    return result


def compare_ratios(row, values):
    calc = calculate_core(values)
    if calc['values'] is None:
        raise ValueError('source vector invalid: ' + row['symbol'] + ':' + str(row['year']) + ':' + str(calc))
    for name, expected in calc['values'].items():
        if not math.isclose(float(row[name]), expected, rel_tol=1e-14, abs_tol=1e-13):
            raise ValueError('ratio recomputation differs: ' + row['symbol'] + ':' + name)
    return calc['values']


def run(root, config_path, check_only=False):
    root = Path(root)
    pins = {}

    def pin(path, expected=None):
        body = inside(root, path).read_bytes()
        sha = digest(body)
        if expected is not None and expected != sha:
            raise ValueError('input hash changed: ' + path)
        if path in pins and pins[path] != sha:
            raise ValueError('input changed during run: ' + path)
        pins[path] = sha
        return body

    def load(path, expected=None):
        return json.loads(pin(path, expected))

    c = load(config_path)
    if c['version'] != VERSION:
        raise ValueError('unknown full10 driver contract')
    protocol = load(c['protocol']['path'], c['protocol']['sha256'])
    validate_mode(protocol)
    if (protocol['years'] != list(range(2016, 2026)) or protocol['seed'] != 42
            or protocol['n_init'] != 20 or protocol['max_iter'] != 300
            or protocol.get('reduction') != {'method': 'none'}):
        raise ValueError('approved model specification changed')
    for path in CODE + ['src/delta_t1/experiments/financial_full10_baseline.py',
                        'scripts/financial_full10_baseline.py', 'scripts/financial_full10_baseline.ps1',
                        'src/delta_t1/experiments/financial_direct_cashflow_review.py',
                        'src/delta_t1/experiments/financial_template_candidates.py',
                        'src/delta_t1/experiments/financial_precision_review.py',
                        'src/delta_t1/experiments/financial_history_qa.py',
                        'src/delta_t1/experiments/financial_api_input_review.py']:
        pin(path)
    handoff = load(c['handoff']['path'], c['handoff']['sha256'])
    delivery = handoff['source_delivery']
    dm = load(delivery['path'] + '/manifest.json', delivery['manifest_sha256'])
    tables = []
    for name in ['financial-ratios-1172-symbols-2016-2025.csv', 'securities-1172-symbols.csv']:
        entry = handoff['files'][name]
        body = pin(str(Path(c['handoff']['path']).parent / name).replace('\\', '/'), entry['sha256'])
        original = entry['original_path']
        if pin(original, dm[Path(original).name]) != body:
            raise ValueError('handoff differs from frozen delivery')
        tables.append(list(csv.DictReader(io.StringIO(body.decode('utf-8-sig')))))
    rows, members = tables
    validate_rows(rows, members, protocol['years'], c['expected_candidates'])
    if handoff['strict_pit_ready'] is not False or handoff['research_ready'] is not False:
        raise ValueError('handoff reference mode changed')
    state = inside(root, c['output_root']) / 'pipeline-status.json'
    bysource = defaultdict(list)
    for row in rows:
        bysource[row['source_evidence']].append(row)
    audited = []
    for group in bysource.values():
        cache = {}

        def cached(path, expected=None):
            if path not in cache:
                cache[path] = load(path, expected)
            elif expected is not None and pins[path] != expected:
                raise ValueError('cached evidence pin differs')
            return cache[path]

        for row in group:
            ratios = compare_ratios(row, extract_values(row, cached, pin))
            audited.append(dict(row, year=int(row['year']), **ratios))
        if len(audited) % 500 < len(group):
            state_file(state, 'RECOMPUTING_CORE_RATIOS', completed=len(audited), total=len(rows))
            print(json.dumps(dict(stage='recompute', completed=len(audited), total=len(rows))), flush=True)
    audited.sort(key=lambda r: (r['registry_id'], r['year']))
    validation = dict(status='PASS', candidates=len(members), annual_rows=len(rows), ratios_recomputed=len(rows)*6,
                      source_kinds=dict(Counter(r['source_kind'] or 'CAFEF_API_SELECTED_PARTITION' for r in rows)),
                      claim='ARITHMETIC_REPLAY_OF_SELECTED_REFERENCE_INPUTS_NOT_NEW_SOURCE_VERIFICATION',
                      strict_pit_ready=False, research_ready=False, network_requests=0, pdf_downloads=0, ocr_pages=0)
    identity = digest(encoded(dict(config=c, input_pins=pins)))
    workspace = inside(root, c['output_root']) / 'runs' / identity[:20]
    put(workspace / 'input-pins.json', pins)
    put(workspace / 'validation.json', validation)
    if check_only:
        state_file(state, 'INPUT_VALIDATED_MODEL_NOT_STARTED', completed=len(rows), total=len(rows), run_id=identity[:20])
        return validation
    snapshots = {}; assignments = []; metrics = []
    for year in protocol['years']:
        checkpoint = workspace / ('year-' + str(year) + '.json')
        state_file(state, 'FITTING_EXPLORATORY_STATIC_BASELINE', year=year, completed_years=len(snapshots), total_years=10)
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_bytes())
            if saved['run_identity'] != identity or digest(encoded(saved['result'])) != saved['result_sha256']:
                raise ValueError('checkpoint identity or checksum differs')
            result = saved['result']
        else:
            result = fit_year([r for r in audited if r['year'] == year], protocol)
            put(checkpoint, dict(run_identity=identity, result_sha256=digest(encoded(result)), result=result))
        if result['status'] != 'EXPLORATORY_STATIC_KMEANS_FITTED' or result['n'] != len(members):
            raise ValueError('incomplete fitted year')
        snapshots[str(year)] = result
        assignments += result['assignments']
        metrics.append(dict(year=year, n=result['n'], **result['diagnostics']))
        print(json.dumps(dict(year=year, n=result['n'], diagnostics=result['diagnostics'])), flush=True)
    summary = dict(status='COMPLETE_EXPLORATORY_FULL10_BASELINE', candidates=len(members), annual_rows=len(rows),
                   ratios_recomputed=len(rows)*6, fitted_years=protocol['years'], features=FEATURES,
                   algorithm='INDEPENDENT_ANNUAL_STATIC_KMEANS', k=3, input_validation=validation,
                   original_six_families_complete=False, strict_pit_ready=False, research_ready=False,
                   m3_backtest_allowed=False, market_handoff='PENDING_EXTERNAL_TEAM_ARTIFACTS',
                   small_cluster_years=[y for y, r in snapshots.items() if any(p['small_cluster_warning'] for p in r['profiles'])])
    products = {'summary.json': encoded(summary), 'validation.json': encoded(validation), 'input-pins.json': encoded(pins),
                'config.json': encoded(c), 'protocol.json': encoded(protocol), 'features.csv': csv_bytes(audited),
                'assignments.csv': csv_bytes(assignments), 'metrics.csv': csv_bytes(metrics), 'snapshots.json': encoded(snapshots)}
    manifest = {k: digest(v) for k, v in products.items()}
    out = inside(root, c['output_root']) / 'results' / digest(encoded(manifest))[:20]
    for name, body in products.items():
        put(out / name, body)
    put(out / 'manifest.json', manifest)
    ref = dict(path=out.relative_to(root).as_posix(), manifest_sha256=digest((out / 'manifest.json').read_bytes()))
    put(inside(root, c['report_root']) / 'result-ref.json', ref)
    table = '\n'.join(f"| {r['year']} | {r['n']} | {r['cluster_sizes']} | {r['silhouette']:.4f} | {r['converged']} |" for r in metrics)
    text = f'''# Financial baseline: 1.172 mã đủ annual 2016–2025

Đã kiểm hash handoff/delivery, kiểm cohort, tính lại {len(rows)*6:,} giá trị tỷ số từ input đã chọn và fit 10 cross-sections. Không acquire thêm dữ liệu hoặc xác minh mới bằng PDF. Arithmetic replay không thay thế chứng nhận từng source fact.

| Năm | Số mã | Kích thước cụm | Silhouette | Converged |
|---|---:|---|---:|---|
{table}

Sáu features: gross margin, net margin, liabilities/assets, current ratio, CFO/assets và revenue/ending assets. Protocol giữ k=3, seed42, n_init20, max_iter300, zscore theo từng năm; không PCA, winsorization hoặc imputation. Mỗi scaler chỉ fit trên cross-section cùng năm. Không chọn model bằng returns. Các năm có cụm nhỏ dưới10 mã: {summary['small_cluster_years']}. Giữ nguyên outliers và công bố cảnh báo; silhouette cao không tự chứng minh cụm hữu ích. Cluster IDs chỉ có ý nghĩa trong từng năm, không phải nhãn ngành hoặc nhóm đồng nhất qua thời gian.

Kết quả ở `{ref['path']}`: features.csv, assignments.csv, metrics.csv, snapshots.json (scalers/centroids/profiles), input-pins.json và manifest.json. Đây là independent annual static K-Means, không phải Dynamic Clustering, out-of-sample evaluation hoặc M2/M3 final. Registry IDs còn là candidates; cohort cố định đủ10 năm có survivorship/selection bias, không đại diện historical investable universe. EPS/P/E/P/B/F/M/Z chưa đầy đủ; PIT/research/backtest gates vẫn đóng. Cần review chất lượng cụm, hoàn thiện publication/vintages/identity và nhận bàn giao market trước khi freeze research protocol/M3.
'''
    put(inside(root, c['report_root']) / 'report.md', text.encode('utf-8'))
    state_file(state, summary['status'], completed_years=10, total_years=10, output=ref['path'])
    return dict(summary, output=ref['path'])
