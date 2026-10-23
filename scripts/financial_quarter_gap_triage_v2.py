"""Offline header triage. Presence never authorizes quarterly-to-annual conversion."""
import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

from delta_t1.experiments.financial_annual_gap_audit import GROUPS, headers
from delta_t1.experiments.financial_api_input_review import csv_bytes
from delta_t1.experiments.financial_history_documents import put
from delta_t1.ingestion.cafef_financial import digest, encoded
from delta_t1.ingestion.cafef_financial_deep import report_url
from delta_t1.ingestion.financial_batch_evidence import inside

VERSION = 'financial-quarter-gap-triage-v2'
NEEDED = {('CDKT', 'TN'), ('CDKT', 'NV'), ('KQKD', 'KQKD'), ('LCTT', 'HDKD')}


def partition_coverage(rows):
    """Require the same provider token; do not silently combine HS/K partitions."""
    groups = defaultdict(set)
    for r in rows:
        if r['numeric_cells'] and r.get('provider_type'):
            groups[r['provider_type'], r['quarter']].add((r['statement'], r['group']))
    providers = sorted({p for p, q in groups})
    return {
        'q4_same_provider_tokens': [p for p in providers if NEEDED <= groups[p, 4]],
        'four_quarters_same_provider_tokens': [p for p in providers if all(NEEDED <= groups[p, q] for q in range(1, 5))],
        'provider_tokens': providers,
        'annual_conversion_accepted': False,
        'cashflow_interval_status': 'UNRESOLVED_NOT_ASSUMED_DISCRETE_OR_YTD',
    }


def run(root, config_path):
    root = Path(root)
    pins = {}

    def pin(path, expected=None):
        body = inside(root, path).read_bytes()
        sha = digest(body)
        if expected is not None and sha != expected:
            raise ValueError('source changed: ' + path)
        pins[path] = sha
        return body

    def read(path, expected=None):
        return json.loads(pin(path, expected))

    def rows(path, expected=None):
        return list(csv.DictReader(io.StringIO(pin(path, expected).decode('utf-8-sig'))))

    c = read(config_path)
    if c['version'] != VERSION or any(c.get(k) is not False for k in ['network_allowed', 'pdf_download_allowed', 'annual_conversion_allowed', 'research_promotion_allowed']):
        raise ValueError('explicit offline no-conversion contract required')
    for p in ['scripts/financial_quarter_gap_triage_v2.py', 'src/delta_t1/experiments/financial_annual_gap_audit.py', 'src/delta_t1/experiments/financial_api_input_review.py', 'src/delta_t1/experiments/financial_history_documents.py', 'src/delta_t1/ingestion/cafef_financial.py', 'src/delta_t1/ingestion/cafef_financial_deep.py', 'src/delta_t1/ingestion/financial_batch_evidence.py']:
        pin(p)
    manifests = {}
    for name in ['baseline', 'audit', 'qa']:
        spec = c[name]
        manifests[name] = read(spec['path'] + '/manifest.json', spec['manifest_sha256'])
    b, a, q = [c[n]['path'] for n in ['baseline', 'audit', 'qa']]
    coverage = rows(b + '/coverage-by-symbol.csv', manifests['baseline']['coverage-by-symbol.csv'])
    near = {r['registry_id']: set(json.loads(r['missing_years'])) for r in coverage if int(r['after_periods']) == 9}
    old = read(a + '/target-audit.json', manifests['audit']['target-audit.json'])
    targets = [r for r in old if r['registry_id'] in near and r['year'] in near[r['registry_id']]]
    sm = read(q + '/symbol-manifests.json', manifests['qa']['symbol-manifests.json'])
    audit, observations, receipts = [], [], []
    for index, target in enumerate(targets, 1):
        rid, symbol, year = target['registry_id'], target['symbol'], target['year']
        entry = sm[rid]
        manifest = read(entry['path'], entry['sha256'])
        folder = Path(entry['path']).parent.as_posix()
        sourcepins = read(folder + '/input-pins.json', manifest['input-pins.json'])['sources']
        receipt_index = defaultdict(list)
        for path, sha in sourcepins.items():
            if '/receipts/' in path:
                receipt_index[Path(path).stem].append((path, sha))
        selected, seen = [], set()
        missing_slots = 0
        observed_series = set()
        for matches in receipt_index.values():
            for path, sha in matches:
                receipt = read(path, sha)
                task = receipt['task']
                if task.get('mode') != 'QUY':
                    continue
                statement, group, page = task['statement'], task['group'], task['page']
                if statement not in GROUPS or group not in GROUPS[statement] or type(page) is not int or page < 1:
                    raise ValueError('invalid quarterly task')
                url = report_url(symbol, statement, 'QUY', group, page)
                if task['symbol'] != symbol or task['url'] != url or Path(path).stem != digest(url.encode()):
                    raise ValueError('receipt task mismatch')
                observed_series.add((statement, group))
                record = receipt.get('record')
                receipts.append(dict(symbol=symbol, target_year=year, statement=statement, group=group, page=page, status=receipt['status'], receipt_path=path, source_path=record['path'] if record else None))
                if not record:
                    continue
                if sourcepins.get(record['path']) != record['sha256']:
                    raise ValueError('raw missing from source pin chain')
                key = statement, group, record['path']
                if key in seen:
                    continue
                seen.add(key)
                raw = pin(record['path'], record['sha256'])
                payload = json.loads(raw)
                for h in headers(raw, statement, group, symbol):
                    if h['year'] != year:
                        continue
                    item = dict(symbol=symbol, target_year=year, statement=statement, group=group, provider_unit=payload.get('value', {}).get('unit'), source_path=record['path'], source_sha256=record['sha256'], **h)
                    selected.append(item)
        missing_slots = len({(s,g) for s,gs in GROUPS.items() for g in gs} - observed_series)
        observations.extend(selected)
        audit.append(dict(symbol=symbol, registry_id=rid, year=year, position=target['position'], missing_quarter_receipt_series=missing_slots, numeric_header_observations=sum(bool(r['numeric_cells']) for r in selected), **partition_coverage(selected), next_action='VERIFY_FISCAL_INTERVAL_UNIT_SCOPE_AND_VINTAGE_FROM_ORIGINAL_SOURCE', recovered=False, strict_pit_ready=False, research_ready=False))
        if index % 25 == 0:
            print(json.dumps(dict(completed=index, total=len(targets))), flush=True)
    summary = dict(status='COMPLETE_OFFLINE_TRIAGE_GOAL_PARTIAL', targets=len(audit), position_counts=dict(Counter(r['position'] for r in audit)), q4_same_provider_cases=sum(bool(r['q4_same_provider_tokens']) for r in audit), four_quarters_same_provider_cases=sum(bool(r['four_quarters_same_provider_tokens']) for r in audit), missing_quarter_receipt_series_cases=sum(bool(r['missing_quarter_receipt_series']) for r in audit), headers_with_unknown_unit=sum(r['provider_unit'] is None for r in observations), target_header_observations=len(observations), recovered_rows=0, full10_before=sum(int(r['after_periods']) == 10 for r in coverage), full10_after=sum(int(r['after_periods']) == 10 for r in coverage), local_network_requests=0, pdf_downloads=0, ocr_pages=0, annual_conversion_accepted=False, strict_pit_ready=False, research_ready=False)
    products = {'summary.json': encoded(summary), 'quarter-triage.json': encoded(audit), 'quarter-triage.csv': csv_bytes(audit), 'quarter-headers.csv': csv_bytes(observations), 'receipt-evidence.csv': csv_bytes(receipts), 'input-pins.json': encoded(pins), 'config.json': encoded(c)}
    manifest = {n: digest(body) for n, body in products.items()}
    out = inside(root, c['output_root']) / 'results' / digest(encoded(manifest))[:20]
    for name, body in products.items():
        put(out / name, body)
    put(out / 'manifest.json', encoded(manifest))
    result = dict(path=out.relative_to(root).as_posix(), manifest_sha256=digest(encoded(manifest)))
    put(inside(root, c['report_root']) / 'result-ref.json', encoded(result))
    print(json.dumps(dict(result=result, summary=summary)), flush=True)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.config)
