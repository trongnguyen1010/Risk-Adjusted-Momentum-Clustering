"""Build a deterministic recovery work queue; never relax QA or download documents."""
import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

from delta_t1.experiments.financial_api_input_review import FORMULAS, csv_bytes
from delta_t1.experiments.financial_history_documents import put
from delta_t1.experiments.financial_precision_review import BRIDGE_FIELDS
from delta_t1.ingestion.cafef_financial import digest, encoded

BASE = 'data/financial/history_annual_gap_audit_v1/html-reference/c15c48e7682c0685c235'
QA = 'data/financial/history_precision_review_v1/results/6ef2c083a4ffc2a9b51c'
CFO = 'data/financial/history_direct_cashflow_review_v1/results/a6bf5b2593fa37fb2771'
REPORT = 'artifacts/reports/financial-bulk-recovery-queue-v1'
REASON_ORDER = ['NO_ANNUAL_PARTITION_IN_ACQUIRED_PAGES', 'MULTIPLE_PROVIDER_PARTITIONS_NO_SOURCE_PRIORITY', 'DISPLACEMENT_REVIEW_REQUIRED', 'ACCOUNTING_OR_FINANCE_QA_HELD', 'MISSING_INPUTS', 'NONPOSITIVE_DENOMINATOR']


def primary_reason(reasons, cfo_status):
    if reasons == ['MISSING_INPUTS'] and cfo_status == 'HELD_UNCHANGED_ACCOUNTING_DISPLACEMENT_OR_CORE_GATES':
        return 'CFO_ALREADY_FOUND_OTHER_GATES_HELD'
    return next((r for r in REASON_ORDER if r in reasons), 'OTHER_REVIEW')


def rank(item):
    # Existing annual data and isolated QA cases are cheaper to review as a group.
    cost = {'ACCOUNTING_OR_FINANCE_QA_HELD': 0, 'CFO_ALREADY_FOUND_OTHER_GATES_HELD': 1, 'MISSING_INPUTS': 2, 'MULTIPLE_PROVIDER_PARTITIONS_NO_SOURCE_PRIORITY': 3, 'DISPLACEMENT_REVIEW_REQUIRED': 4, 'NO_ANNUAL_PARTITION_IN_ACQUIRED_PAGES': 5, 'NONPOSITIVE_DENOMINATOR': 6}
    return (sum(cost.get(g['primary_blocker'], 7) for g in item['gaps']), sum(len(g['failed_checks']) for g in item['gaps']), item['registry_id'])


def run(root):
    pins = {}
    def pin(path, expected=None):
        body = (root / path).read_bytes()
        sha = digest(body)
        if expected is not None and expected != sha:
            raise ValueError('source changed: ' + path)
        pins[path] = sha
        return body
    def table(folder, name):
        manifest = json.loads(pin(folder + '/manifest.json'))
        return list(csv.DictReader(io.StringIO(pin(folder + '/' + name, manifest[name]).decode('utf-8-sig'))))
    # Pin the upstream manifest digests rather than trusting a replaced manifest.
    pin(BASE + '/manifest.json', 'c15c48e7682c0685c2358959be89f8dc5da3eb3f816541d2295dd7dfc8b784a0')
    pin(QA + '/manifest.json', '6ef2c083a4ffc2a9b51c18caad0c905a01c2047ab6ea571fb0fc43e41fcb6b52')
    coverage = table(BASE, 'coverage-by-symbol.csv')
    gaps = table(BASE, 'remaining-document-review-candidates.csv')
    checks = table(QA, 'qa-checks.csv')
    cfo_manifest = json.loads(pin(CFO + '/manifest.json', 'a6bf5b2593fa37fb2771a67f88656f2bd52a210c153a120956b8eb766806b88c'))
    attempts = list(csv.DictReader(io.StringIO(pin(CFO + '/recovery-attempts.csv', cfo_manifest['recovery-attempts.csv']).decode('utf-8-sig'))))
    for path in ['scripts/financial_bulk_recovery_queue.py', 'src/delta_t1/experiments/financial_api_input_review.py', 'src/delta_t1/experiments/financial_precision_review.py']:
        pin(path)
    cfo = {(r['registry_id'], int(r['year'])): r for r in attempts}
    qa = defaultdict(list)
    for r in checks:
        if r['status'].startswith('HELD'):
            qa[r['registry_id'], int(r['year'])].append(r)
    fields = {name: [lhs, *rhs] for name, lhs, rhs in FORMULAS}
    fields['FINANCE_BRIDGE'] = BRIDGE_FIELDS
    byid = defaultdict(list)
    selected = {r['registry_id']: r for r in coverage if int(r['after_periods']) in [8, 9]}
    for r in gaps:
        rid, year = r['registry_id'], int(r['year'])
        if rid not in selected:
            continue
        failures = qa[rid, year]
        checks_failed = sorted({x['check'] for x in failures})
        reasons = json.loads(r['reasons'])
        attempt = cfo.get((rid, year), {})
        suggested = sorted(set(json.loads(r['missing_core_fields'])) | {f for ch in checks_failed for f in fields[ch]})
        byid[rid].append(dict(year=year, original_reasons=reasons, primary_blocker=primary_reason(reasons, attempt.get('status')), failed_checks=checks_failed, qa_observations=failures, fields_to_verify=suggested, direct_cfo_attempt_status=attempt.get('status'), direct_cfo_component_status=attempt.get('cfo_status'), direct_cfo_post_feature_status=attempt.get('feature_status'), direct_cfo_post_quality_gate=attempt.get('quality_gate'), source_document_url=None, document_url_status='PRIMARY_CATALOGUE_DISCOVERY_REQUIRED', cache_status='DOCUMENT_METADATA_REVIEW_REQUIRED_NOT_CONFIRMED_ABSENT', pdf_download_authorized=False, expected_gain_if_all_gates_pass=1))
    candidates = []
    for rid, c in selected.items():
        local = sorted(byid[rid], key=lambda r: r['year'])
        missing = set(json.loads(c['missing_years']))
        if {r['year'] for r in local} != missing:
            raise ValueError('missing-year dependency mismatch')
        candidates.append(dict(symbol=c['symbol'], registry_id=rid, current_period_count=int(c['after_periods']), missing_years=sorted(missing), gaps=local, full10_gain_if_all_missing_years_verified=1, pdf_download_authorized=False, strict_pit_ready=False, research_ready=False))
    nine = sorted([r for r in candidates if r['current_period_count'] == 9], key=rank)
    eight = sorted([r for r in candidates if r['current_period_count'] == 8], key=rank)
    batch = nine[:100]
    minimal = nine + eight[:129]
    flat = []
    for i, r in enumerate(nine + eight, 1):
        for g in r['gaps']:
            flat.append(dict(priority=i, symbol=r['symbol'], registry_id=r['registry_id'], current_period_count=r['current_period_count'], year=g['year'], primary_blocker=g['primary_blocker'], failed_checks=g['failed_checks'], fields_to_verify=g['fields_to_verify'], direct_cfo_attempt_status=g['direct_cfo_attempt_status'], batch100=r in batch, minimum_1000_scenario=r in minimal, source_document_url=None, cache_status=g['cache_status'], pdf_download_authorized=False, strict_pit_ready=False, research_ready=False))
    summary = dict(status='COMPLETE_BULK_RECOVERY_QUEUE_GOAL_PARTIAL', full10_current=463, nine_period_candidates=len(nine), eight_period_candidates=len(eight), target_candidates=len(candidates), target_annual_cases=len(flat), batch100_candidates=len(batch), batch100_annual_cases=sum(len(r['gaps']) for r in batch), batch100_primary_blockers=dict(Counter(g['primary_blocker'] for r in batch for g in r['gaps'])), exclusive_nine_period_primary_blockers=dict(Counter(g['primary_blocker'] for r in nine for g in r['gaps'])), minimum_scenario_candidate_dependencies=len(minimal), minimum_scenario_annual_dependencies=sum(len(r['gaps']) for r in minimal), theoretical_full10_after_all_nine=463+len(nine), theoretical_full10_after_batch100=463+len(batch), recovered_rows=0, confirmed_pdf_downloads_required=None, proposed_pdf_cap=100, proposed_pilot_pdf_cap=10, pdf_downloads=0, network_requests=0, ocr_pages=0, qa_policy_changed=False, strict_pit_ready=False, research_ready=False)
    products = {'summary.json': encoded(summary), 'candidates.json': encoded(nine + eight), 'batch100.json': encoded(batch), 'recovery-queue.csv': csv_bytes(flat), 'input-pins.json': encoded(pins)}
    manifest = {n: digest(b) for n, b in products.items()}
    out = root / 'data/financial/history_bulk_recovery_queue_v1/results' / digest(encoded(manifest))[:20]
    for n, b in products.items():
        put(out / n, b)
    put(out / 'manifest.json', encoded(manifest))
    ref = dict(path=out.relative_to(root).as_posix(), manifest_sha256=digest(encoded(manifest)))
    put(root / REPORT / 'result-ref.json', encoded(ref))
    print(json.dumps(dict(result=ref, summary=summary)))
    return ref


if __name__ == '__main__':
    run(Path(__file__).resolve().parents[1])
