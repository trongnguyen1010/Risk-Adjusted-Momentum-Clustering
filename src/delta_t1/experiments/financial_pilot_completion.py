"""Add explicit closing debt components to the immutable pilot, then replay QA.

PDF text/OCR are candidates. Only a reviewed, pinned consolidated closing-stock
observation can close the residual F9 input; cash reclassification is not a stock.
"""
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_cafef_pilot import (CLOSED, SYMBOLS, PilotTransport, compute,
                                    csv_data, pins, read, verify_result)
from .financial_user_workflow import exclusive

VERSION = 'financial-pilot5-completion-v1'
FIELD = 'long_term_debt_including_current_portion'


def number(value):
    if value is None or isinstance(value, bool):
        raise ValueError('explicit reviewed number required; missing is not zero')
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError('invalid debt value') from error
    if not result.is_finite() or result < 0:
        raise ValueError('nonnegative finite debt required')
    return result


def validate(config):
    if config['version'] != VERSION or config['symbols'] != SYMBOLS:
        raise ValueError('fixed pilot5 scope required')
    if any(config.get(k) is not False for k in CLOSED):
        raise ValueError('closed gates required')
    caps = dict(max_logical_requests=1, max_transport_attempts=1,
        max_pdf_download_attempts=1, max_response_bytes=25_000_000,
        max_total_downloaded_bytes=25_000_000, max_wall_seconds=1800,
        max_attempts_per_request=1, timeout_seconds=25)
    if any(type(config['budgets'].get(k)) is not int or
           not 0 < config['budgets'][k] <= limit for k, limit in caps.items()):
        raise ValueError('bounded new-document campaign required')
    if config['budgets'].get('min_seconds_between_transport_attempts', 0) < 2:
        raise ValueError('spacing required')
    if config['approved_hosts'] != ['cafef1.mediacdn.vn'] or len(config['documents']) != 1:
        raise ValueError('only the observed new parent document is enabled')


def acquire(root, config, transport_class=PilotTransport):
    validate(config)
    run = inside(root, config['output_root'])
    run.mkdir(parents=True, exist_ok=True)
    with exclusive(run):
        contract = run/'acquisition-contract.json'
        if contract.exists():
            if contract.read_bytes() != encoded(config):
                raise ValueError('frozen acquisition contract changed')
        else:
            immutable_write(contract, encoded(config))
        receipt = run/'document-receipt.json'
        if receipt.exists():
            result = read(receipt)
            if result.get('path'):
                pins(root, {result['path']: result['sha256']})
            return result
        job = config['documents'][0]
        if (job['symbol'] != 'VNM' or job['scope'] != 'SEPARATE_SUPPORTING_EVIDENCE_ONLY'
                or urlparse(job['url']).hostname not in config['approved_hosts']):
            raise ValueError('supporting-document scope/host mismatch')
        source = read(inside(root, job['discovered_on']))
        matches = [r for r in source['Data']['BctcList'] if
            urlparse(job['url']).path == r['LinkFile'] and r['Symbol'] == 'VNM'
            and r['Year'] == 2025 and r['ReportType'] == 'MK']
        if len(matches) != 1:
            raise ValueError('document must be observed in the existing disclosure receipt')
        old_network = inside(root, config['baseline_inputs']).parents[1]/'network'
        if any(row['url'] == job['url'] for row in read_compact(old_network)['state']['requests'].values()):
            raise ValueError('cannot reset a previously attempted URL in a new campaign')
        network = run/'network'
        network.mkdir(exist_ok=True)
        if (network/'transport.jsonl').exists():
            state = read_compact(network)
            if state['torn_tail_bytes'] or state['state']['requests']:
                raise ValueError('interrupted attempt retained; no automatic retry')
        transport = transport_class(root, network, config)
        transport.context = dict(kind='pdf', symbol='VNM', report='PARENT_NOTE_SUPPORT')
        try:
            body, status = transport.get(job['url'])
            if not body.startswith(b'%PDF-'):
                raise ValueError('PDF signature absent')
            path = run/'documents'/(digest(body)+'.pdf')
            immutable_write(path, body)
            result = dict(job, status='ACQUIRED_SUPPORT_ONLY', http_status=status,
                path=path.relative_to(root).as_posix(), sha256=digest(body), bytes=len(body))
            transport.commit_cache(job['url'], result)
        except Exception as error:
            result = dict(job, status='ACCESS_STOP' if transport.state['boundary'] else
                'BUDGET_STOP' if transport.state['budget_stop'] else 'ACQUISITION_FAILED', error=str(error))
        immutable_write(receipt, encoded(result))
        return result


def supplemental_facts(root, package):
    """Validate a complete closing-stock pair; never infer a current portion."""
    if package['version'] != 'pilot5-closing-debt-review-v1':
        raise ValueError('closing-stock review schema required')
    observations = package['observations']
    pins(root, package['source_pins'])
    if not observations:
        return []
    if len(observations) != 2 or {r['year'] for r in observations} != {2024, 2025}:
        raise ValueError('both closing periods required')
    output = []
    for row in observations:
        if (row.get('symbol') != 'VNM' or row.get('scope') != 'CONSOLIDATED'
                or row.get('framework') != 'VAS' or row.get('unit') != 'VND'
                or row.get('balance_date') != str(row['year'])+'-12-31'
                or row.get('review_status') != 'REVIEWED_REFERENCE_ONLY'
                or row.get('basis') != 'ORIGINAL_LONG_TERM_CLOSING_STOCK'
                or not row.get('reviewed_by') or not row.get('evidence')):
            raise ValueError('reviewed consolidated original-maturity closing stock required')
        for evidence in row['evidence']:
            if (type(evidence.get('pdf_page')) is not int or evidence['pdf_page'] < 1
                    or not evidence.get('locator')):
                raise ValueError('exact PDF page and locator required')
            for key in ['pdf_path', 'image_path']:
                path = evidence[key]
                expected = package['source_pins'].get(path)
                if not expected or digest(inside(root, path).read_bytes()) != expected:
                    raise ValueError('PDF/image provenance absent or changed')
        current = number(row['current_portion'])
        noncurrent = number(row['noncurrent_portion'])
        total = number(row['total_original_long_term_debt'])
        if total != current + noncurrent:
            raise ValueError('closing debt components fail arithmetic QA')
        output.append(dict(id=f'VNM:{FIELD}:{row["year"]}', symbol='VNM', field=FIELD,
            year=row['year'], value=str(total), unit='VND', framework='VAS', scope='CONSOLIDATED',
            review_status='REVIEWED_REFERENCE_ONLY', provenance=dict(
                derivation='EXPLICIT_CLOSING_CURRENT_PLUS_NONCURRENT', components=row,
                source_tier='REVIEWED_PDF_NOTE')))
    return output


def run(root, config, review_path=None):
    validate(config)
    baseline = verify_result(root, inside(root, config['baseline_result']))
    if baseline['metric_values_sha256'] != config['baseline_metrics_sha256']:
        raise ValueError('baseline value hash differs from completion contract')
    package = read(inside(root, config['baseline_inputs']))
    semantics = read(inside(root, config['baseline_result'])/'replay-semantics.json')
    if package['facts'] != semantics['facts']:
        raise ValueError('baseline reviewed facts differ from the sealed result')
    pins(root, package['source_pins'])
    base_config = read(root/'configs/data/financial_cafef_pilot5_execution_v1.json')
    facts = package['facts']
    rows, _, _ = compute(facts, package['valuation'], base_config['primary_metric_variants'])
    metric_projection = [{k:r[k] for k in ['symbol','family','value']} for r in rows]
    # Baseline verifier is authoritative; retain the existing sealed value hash.
    supplement = read(inside(root, review_path)) if review_path else dict(
        version='pilot5-closing-debt-review-v1', observations=[], source_pins={})
    additions = supplemental_facts(root, supplement)
    old_keys = {(f['symbol'], f['field'], f['year']) for f in facts}
    if any((f['symbol'], f['field'], f['year']) in old_keys for f in additions):
        raise ValueError('supplement cannot overwrite a baseline fact')
    result_rows, details, dependencies = compute(facts+additions, package['valuation'], base_config['primary_metric_variants'])
    unchanged = [r for r in result_rows if r['family'] != 'F_SCORE' or r['symbol'] != 'VNM']
    if [{k:r[k] for k in ['symbol','family','value']} for r in unchanged] != [r for r in metric_projection
            if r['family'] != 'F_SCORE' or r['symbol'] != 'VNM']:
        raise ValueError('supplement changed unrelated metrics')
    completed = sum(r['value'] is not None for r in result_rows)
    input_paths = [config['baseline_inputs'], config['baseline_result']+'/manifest.json',
        'configs/data/financial_cafef_pilot5_execution_v1.json',
        'src/delta_t1/experiments/financial_pilot_completion.py']
    if review_path:
        input_paths.append(review_path)
    source_pins = {p:digest(inside(root, p).read_bytes()) for p in input_paths}
    source_pins.update(supplement['source_pins'])
    contract = dict(config=config, source_pins=source_pins, supplement=supplement)
    result_id = digest(encoded(contract))[:20]
    output = inside(root, config['output_root'])/'results'/result_id
    summary = dict(status='GOAL_ACHIEVED' if completed == 30 else 'PARTIAL_WITH_RESULTS',
        completed=completed, target=30, baseline=baseline, additions=len(additions),
        baseline_expected_metrics_sha256=config['baseline_metrics_sha256'], **CLOSED)
    pending = [r for r in dependencies if r['missing']]
    report = '\n'.join(['# Pilot5 — kết quả tính lại', '',
        f'**{summary["status"]}: {completed}/30**. FY2025; P/E annual; P/B book snapshot; giá raw 22/04/2026.', '',
        '| Mã | Chỉ số | Giá trị | Trạng thái |', '|---|---|---:|---|'] +
        [f'| {r["symbol"]} | {r["family"]} | {r["value"] if r["value"] is not None else "Chưa đủ input"} | {r["status"]} |'
            for r in result_rows] + ['',
        'Input còn thiếu xem `review-queue.json`; OCR/text chưa review không được dùng để đóng gap.',
        'Giữ nguyên 29 giá trị baseline; không thay công thức, không mở financial/research/cluster gate.', ''])
    files = {'contract.json':encoded(contract), 'summary.json':encoded(summary),
        'metrics.csv':csv_data(result_rows), 'details.json':encoded(details),
        'dependencies.json':encoded(dependencies), 'reviewed-inputs.json':encoded(facts+additions),
        'review-queue.json':encoded(pending), 'report.md':report.encode('utf-8')}
    with exclusive(inside(root, config['output_root'])):
        for name, body in files.items():
            path = output/name
            if path.exists():
                if path.read_bytes() != body:
                    raise ValueError('immutable result mismatch')
            else:
                immutable_write(path, body)
        manifest = encoded({name:digest(body) for name,body in files.items()})
        if (output/'manifest.json').exists():
            if (output/'manifest.json').read_bytes() != manifest:
                raise ValueError('manifest changed')
        else:
            immutable_write(output/'manifest.json', manifest)
    return dict(summary, output=output.relative_to(root).as_posix())


def verify(root, output_path):
    output = inside(root, output_path)
    for name, expected in read(output/'manifest.json').items():
        if Path(name).name != name or digest((output/name).read_bytes()) != expected:
            raise ValueError('result tamper: '+name)
    contract = read(output/'contract.json')
    validate(contract['config'])
    if output.name != digest(encoded(contract))[:20]:
        raise ValueError('result identity mismatch')
    pins(root, contract['source_pins'])
    additions = supplemental_facts(root, contract['supplement'])
    package = read(inside(root, contract['config']['baseline_inputs']))
    pins(root, package['source_pins'])
    if read(output/'reviewed-inputs.json') != package['facts']+additions:
        raise ValueError('inputs differ from pinned baseline and validated supplement')
    base = read(root/'configs/data/financial_cafef_pilot5_execution_v1.json')
    rows, details, dependencies = compute(read(output/'reviewed-inputs.json'),
        read(inside(root, contract['config']['baseline_inputs']))['valuation'], base['primary_metric_variants'])
    if (csv_data(rows) != (output/'metrics.csv').read_bytes() or
            encoded(details) != (output/'details.json').read_bytes() or
            encoded(dependencies) != (output/'dependencies.json').read_bytes()):
        raise ValueError('calculation replay mismatch')
    baseline = verify_result(root, inside(root, contract['config']['baseline_result']))
    if baseline['metric_values_sha256'] != contract['config']['baseline_metrics_sha256']:
        raise ValueError('baseline value hash mismatch')
    summary = read(output/'summary.json')
    completed = sum(r['value'] is not None for r in rows)
    if any(summary.get(k) is not False for k in CLOSED) or summary['completed'] != completed or summary['status'] != (
            'GOAL_ACHIEVED' if completed == 30 else 'PARTIAL_WITH_RESULTS'):
        raise ValueError('completion status mismatch')
    return dict(status='VERIFIED', completed=completed, target=30, output=output_path, **CLOSED)
