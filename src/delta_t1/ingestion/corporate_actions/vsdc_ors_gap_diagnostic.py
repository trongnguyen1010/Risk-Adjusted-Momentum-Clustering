"""One bounded ORS query against the reviewed V7 HOLD baseline."""
from pathlib import Path
import time

from . import vsdc_recovery_pausefix as collector

CONFIG = 'configs/data/corporate_actions/vsdc_ors_gap_diagnostic_v1.json'
OUTPUT = 'data/corporate_actions/work/vsdc_ors_gap_diagnostic_v1'
REVIEW = 'data/corporate_actions/work/vsdc_v7_offline_review_20261106_v1'
REVIEW_SHA = '61ef5ce67ed1766bdd9037fae7bdff742286728e72117347349acaed984cb3db'
TYPE = 'vsdc-ors-gap-diagnostic-v1'
SCOPE = {'batch_id': 'ORS_DIAGNOSTIC', 'ticker': 'ORS'}
REVIEW_COMPLETE = 'COMPLETE_CURRENT_QUERY_REVIEW_REQUIRED'
REVIEW_PARTIAL = 'PARTIAL_QUERY_HOLD_REVIEW_REQUIRED'


def contract():
    return {'stage': 'VSDC_ORS_GAP_DIAGNOSTIC_V1', 'ticker': 'ORS',
        'business_interval_seconds': 4, 'max_list_pages_per_query': 5,
        'max_context_attempts': 98, 'max_seconds': 180, 'operation_timeout_seconds': 15,
        'retry': False}


def load_inputs(project):
    read, sha = collector.read, collector.sha
    if read(project / CONFIG) != contract():
        raise ValueError('DIAGNOSTIC_EXACT_ORS_CONTRACT_REQUIRED')
    review_dir = project / REVIEW
    if sha((review_dir / 'review.json').read_bytes()) != REVIEW_SHA:
        raise ValueError('DIAGNOSTIC_REVIEWED_ORS_BASELINE_REQUIRED')
    review = read(review_dir / 'review.json')
    if read(review_dir / 'manifest.json')['files'] != {'review.json': REVIEW_SHA}:
        raise ValueError('DIAGNOSTIC_ORS_REVIEW_MANIFEST_CHANGED')
    state = project / review['run'] / 'state'
    if sha((state / 'manifest.json').read_bytes()) != review['state_manifest_sha256']:
        raise ValueError('DIAGNOSTIC_REVIEWED_V7_MANIFEST_CHANGED')
    manifest = read(state / 'manifest.json')['files']
    cache_files = ('known_discovery_after_validated_queries.json', 'reusable_detail_provider_ids.json')
    for name in cache_files:
        if sha((state / name).read_bytes()) != manifest[name]:
            raise ValueError('DIAGNOSTIC_V7_CACHE_CHANGED')
    pins = read(project / collector.PREP / 'runtime.json')
    if collector.runtime(project) != pins:
        raise ValueError('DIAGNOSTIC_COLLECTOR_RUNTIME_CHANGED')
    return review, set(read(state / cache_files[0])), set(read(state / cache_files[1])), pins


class BoundedDriver(collector.HeadlessDriver):
    def next_page(self, number, previous):
        if number > self.config['max_list_pages_per_query']:
            raise ValueError('DIAGNOSTIC_FIVE_PAGE_LIMIT')
        print(f'ORS: đang kiểm tra trang {number}/5', flush=True)
        return super().next_page(number, previous)


def run(project, output, *, dry_run=False, driver_factory=BoundedDriver, clock=time.monotonic):
    read, write = collector.read, collector.write
    review, known, reusable, pins = load_inputs(project)
    baseline = review['ors']
    old_ids = set(baseline['verified_article_ids'])
    if len(old_ids) != 80 or baseline['reported'] != 85:
        raise ValueError('DIAGNOSTIC_ORS_BASELINE_COUNTS_CHANGED')
    config = {**collector.caps(), **contract(), 'batch_ids': [SCOPE['batch_id']],
        'selected_query_count': 1, 'estimated_list_requests': 5,
        'output_base': OUTPUT, 'preparation': REVIEW, 'max_business_requests': 5,
        'max_batch_business_requests': 5, 'max_batch_context_attempts': 98, 'max_batch_seconds': 180}
    readiness = collector.mbs.old.readiness(config)
    if dry_run:
        return {'status': 'OFFLINE_CHECK_PASS' if readiness['ready'] else 'SETUP_REQUIRED',
            'ticker': 'ORS', 'baseline_verified': 80, 'baseline_reported': 85,
            'source_requests': 0, 'browser_launched': False, 'max_list_requests': 5, 'readiness': readiness}
    if not readiness['ready']:
        raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')

    output.mkdir(parents=True)
    write(output / 'baseline.json', {'review_sha256': REVIEW_SHA, **baseline})
    write(output / 'environment.json', readiness)
    query = output / 'query'
    definition = collector.query_definition(SCOPE)
    shared = collector.base.Budget(config, clock)
    shared.begin(SCOPE['batch_id'])

    def check_runtime():
        collector.mbs.old.protected_check(project, pins)

    print('ORS: đang kiểm tra trang 1/5', flush=True)
    acquired = collector.acquire_query(project, query, definition, config, project / REVIEW,
        shared, reusable, known, check_runtime, driver_factory, clock)
    query_zip = output / 'query.zip'
    collector.base.seal(query, query_zip, artifact_type=collector.pilot.QUERY_TYPE)
    checked = None
    if acquired['status'] == 'PASS_SOURCE_BATCH_REQUIRES_AUTOMATED_VALIDATION':
        try:
            checked = collector.pilot._validate_source_query(query, query_zip, definition,
                config, reusable, known, shared.previous_start)
        except (ValueError, OSError) as exc:
            write(output / 'validation_failure.json', {'error_type': type(exc).__name__,
                'reason': collector.pilot.safe_reason(exc)})
        else:
            write(output / 'validation.json', checked)

    pages = [read(path) for path in sorted((query / 'ORS').glob('page[1-5].json'))]
    new_ids = {article_id for page in pages for article_id in page['article_ids']}
    total = pages[0]['coverage']['reported_total'] if pages else None
    result = {'status': REVIEW_COMPLETE if checked else REVIEW_PARTIAL, 'ticker': 'ORS',
        'verified_pages': len(pages), 'reported_total_now': total, 'observed_distinct_now': len(new_ids),
        'baseline_ids_seen': len(old_ids & new_ids), 'ids_not_in_baseline': sorted(new_ids - old_ids),
        'baseline_ids_not_observed': sorted(old_ids - new_ids), 'current_query_exhausted': checked is not None,
        'same_count_gap_closed': checked is not None and total == 85 and old_ids <= new_ids,
        'business_requests': acquired['business_requests'], 'context_attempts': acquired['context_attempts'],
        'source_stop_reason': acquired.get('stop_reason'), 'manual_offline_review_pending': True,
        'canonical_fields_applied': 0, 'full_history_certified': False}
    write(output / 'result.json', result)
    return result


def package(state):
    archive = state.parent / 'delta-vsdc-ors-gap-diagnostic.zip'
    collector.base.seal(state, archive, artifact_type=TYPE)
    collector.verify_zip(state, archive, TYPE)
    return archive
