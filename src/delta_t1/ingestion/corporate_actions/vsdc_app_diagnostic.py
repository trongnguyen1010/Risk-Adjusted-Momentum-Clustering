"""Pilot APP một GET, chỉ chẩn đoán; V3 và source/access gates bất biến."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import re
from pathlib import Path
import time

from . import vsdc_headless_chain as prior

read, write, sha, hashes = prior.read, prior.write, prior.sha, prior.hashes
CONFIG = 'configs/data/corporate_actions/vsdc_app_diagnostic_v1.json'
OUTPUT = 'data/corporate_actions/work/vsdc_app_diagnostic_v1'
PREP = 'data/corporate_actions/work/vsdc_app_diagnostic_preparation_20261103_v1'
TYPE = 'vsdc-app-single-get-safe-diagnostic-v1'
PREP_TYPE = 'vsdc-app-single-get-safe-diagnostic-preparation-v1'
PASS = 'PASS_APP_FIRST_PAGE_DIAGNOSTIC_REVIEW_REQUIRED'
STOP = 'STOPPED_APP_DIAGNOSTIC_REVIEW_REQUIRED'
RUN = prior.OUTPUT + '/run-20261103T102550498846Z'
REVIEW = 'data/corporate_actions/work/vsdc_remaining54_headless_live_review_20261103_v1'
PARENTS = {
    prior.PREP: ('12571b36fa82381715801a58062e6970f38fc3580d0b4b577d0c2e23f09c36cf', prior.PREP_TYPE),
    RUN + '/state': ('51f8da9bae8e59464071d2573d5cd1249469d0994a87ce49475df260a7c8e860', prior.TYPE),
    REVIEW: ('d7b901d859135c8ac1c51014956996f935674e9f1192d2674cf32f33549cb251',
             'vsdc-remaining54-headless-partial-stop-offline-review-v1'),
}
MARKERS = {
    'RATE_LIMIT': r'too many requests|rate limit|quá nhiều yêu cầu|tần suất truy cập',
    'SERVICE_UNAVAILABLE': r'service unavailable|temporarily unavailable|dịch vụ tạm thời',
    'SERVER_ERROR': r'internal server error|server error in|runtime error|lỗi hệ thống',
}


def safe_reason(error):
    message = str(error)
    if message in {'V3_ACTIVE_OR_UNCLEAN_LOCK_REVIEW_REQUIRED', 'EXACT_REVIEWED_STOP_RUN_REQUIRED',
            'EXACT_APP_ONE_GET_DIAGNOSTIC_CONTRACT_REQUIRED', 'REVIEWED_APP_STOP_REQUIRED',
            'LOCAL_BROWSER_SETUP_REQUIRED', 'REFUSE_OVERWRITE', 'ACTIVE_OR_UNCLEAN_DIAGNOSTIC_LOCK'}:
        return message
    if len(message) <= 200 and re.fullmatch(
            r'(?:DIAGNOSTIC|HEADLESS|BROWSER|CHAIN|QUERY|RENDERED|FRESH|FIRST_PARTY|BATCH)_'
            r'[A-Z0-9_]+(?:: [A-Z0-9_, ]+)?', message):
        return message
    return 'DIAGNOSTIC_OPERATION_FAILED'


def contract():
    return {**prior.caps(), 'stage': 'VSDC_APP_SINGLE_GET_DIAGNOSTIC_V1',
        'output_base': OUTPUT, 'preparation': PREP, 'ticker': 'APP', 'url': prior.search_url('APP'),
        'batch_ids': ['APP_DIAGNOSTIC'], 'selected_query_count': 1, 'estimated_list_requests': 1,
        'max_business_requests': 1, 'max_context_attempts': 79, 'max_batch_business_requests': 1,
        'max_batch_context_attempts': 79, 'max_context_per_query': 79, 'max_list_pages_per_query': 1,
        'max_seconds': 180, 'max_batch_seconds': 180, 'max_query_seconds': 180,
        'diagnostic_only': True, 'full_query_completion_credit': False,
        'recovery_import': False, 'agent_acquisition': False,
        'response_policy': 'HASH_SIZE_STRUCTURE_AND_FIXED_MARKERS_ONLY_NO_RAW_BODY_DOM_TITLE_OR_TEXT'}


def runtime(project):
    names = [CONFIG, 'src/delta_t1/ingestion/corporate_actions/vsdc_app_diagnostic.py',
        'scripts/corporate_actions/prepare_vsdc_app_diagnostic_v1.py',
        'scripts/corporate_actions/collect_vsdc_app_diagnostic_v1.py']
    return {**prior.runtime(project), **{n: sha((project / n).read_bytes()) for n in names}}


def parents(project):
    _, old = prior.load_preparation(project)
    if (project / prior.OUTPUT / 'active.lock').exists():
        raise ValueError('V3_ACTIVE_OR_UNCLEAN_LOCK_REVIEW_REQUIRED')
    if [p.name for p in (project / prior.OUTPUT).glob('run-*')] != [Path(RUN).name]:
        raise ValueError('EXACT_REVIEWED_STOP_RUN_REQUIRED')
    for name, (digest, kind) in PARENTS.items():
        folder = project / name
        if sha((folder / 'manifest.json').read_bytes()) != digest:
            raise ValueError('DIAGNOSTIC_PARENT_CHANGED')
        prior.base.verify_artifact(folder, {kind})
    prior.verify_zip(project / RUN / 'state', project / RUN / 'delta-vsdc-headless54.zip', prior.TYPE)
    review = read(project / REVIEW / 'review.json')
    if (review['status'] != 'PASS_OFFLINE_REVIEW_OF_PARTIAL_STOP_NOT_ACQUISITION_PASS'
            or review['completed_queries'] != 15 or review['failed_ticker'] != 'APP'):
        raise ValueError('REVIEWED_APP_STOP_REQUIRED')
    return old


def load_preparation(project):
    config = read(project / CONFIG)
    if config != contract():
        raise ValueError('EXACT_APP_ONE_GET_DIAGNOSTIC_CONTRACT_REQUIRED')
    parents(project)
    prep = project / PREP
    prior.base.verify_artifact(prep, {PREP_TYPE})
    if read(prep / 'runtime.json') != runtime(project) or read(prep / 'plan.json')['config'] != config:
        raise ValueError('DIAGNOSTIC_PREPARED_RUNTIME_CHANGED')
    prior.mbs.old.protected_check(project, read(prep / 'protected_old_files.json'))
    return config, prep


def prepare(project):
    project = Path(project).resolve()
    if read(project / CONFIG) != contract():
        raise ValueError('EXACT_APP_ONE_GET_DIAGNOSTIC_CONTRACT_REQUIRED')
    old = parents(project)
    output = project / PREP
    if output.exists():
        raise FileExistsError('REFUSE_OVERWRITE')
    protected = read(old / 'protected_old_files.json')
    for name in PARENTS:
        folder = project / name
        for path in (folder / 'manifest.json', *[folder / n for n in read(folder / 'manifest.json')['files']]):
            protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    archive = project / RUN / 'delta-vsdc-headless54.zip'
    protected[archive.relative_to(project).as_posix()] = sha(archive.read_bytes())
    protected.update(runtime(project))
    output.mkdir(parents=True)
    write(output / 'runtime.json', runtime(project))
    write(output / 'protected_old_files.json', protected)
    write(output / 'plan.json', {'config': contract(), 'status': 'PREPARED_NOT_EXECUTED',
        'source_requests': 0, 'browser_launches': 0, 'readiness': prior.mbs.old.readiness(contract()),
        'purpose': 'One fresh headless APP navigation; response evidence BEFORE result selector wait.',
        'privacy': 'No raw response/DOM/title/free text, cookies, tokens, HAR or private browser state.',
        'source_policy': 'Same V3 network/access/TLS gates, one GET only, no page2/detail/retry/fallback.',
        'completion': 'First-page diagnostics only; no full query credit or recovery import.',
        'limits': 'Hashes/structural flags do not preserve response text or prove the old APP failure cause.',
        'next_step': 'User runs once locally; offline review before any recovery proposal.'})
    write(output / 'manifest.json', {'artifact_type': PREP_TYPE, 'files': hashes(output)})
    load_preparation(project)
    return {'status': 'PREPARED_NOT_EXECUTED', 'ticker': 'APP', 'max_business_requests': 1,
        'protected_files': len(protected), 'source_requests': 0, 'browser_launches': 0, 'output': str(output)}


class Structure(HTMLParser):
    """Chỉ đếm cấu trúc; không trả attributes, text, title hoặc form values."""
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.counts = {'article_containers': 0, 'scripts': 0, 'forms': 0, 'password_inputs': 0}
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') == 'divGlSearchArticles':
            self.counts['article_containers'] += 1
        if tag == 'script': self.counts['scripts'] += 1
        if tag == 'form': self.counts['forms'] += 1
        if tag == 'input' and str(attrs.get('type', '')).casefold() == 'password':
            self.counts['password_inputs'] += 1


def body_evidence(data, limit=2000000):
    result = {'bytes': len(data), 'sha256': None, 'size_limit_exceeded': len(data) > limit,
        'structure': None, 'marker_labels': [], 'raw_archived': False}
    if len(data) > limit:
        return result
    text = data.decode('utf8', errors='replace')
    result['sha256'] = sha(data)
    result['structure'] = Structure(text).counts
    labels = [label for label, pattern in MARKERS.items() if re.search(pattern, text, re.I)]
    if prior.mbs.old.CHALLENGE.search(text): labels.append('ACCESS_CHALLENGE')
    if result['structure']['password_inputs']: labels.append('PASSWORD_FORM')
    result['marker_labels'] = sorted(labels)
    return result


class DiagnosticDriver(prior.HeadlessDriver):
    """Cùng headless/route lifecycle; ghi response trước selector, không sửa V3."""
    def first(self):
        response = self.page.goto(self.config['url'], wait_until='domcontentloaded', timeout=self.guard.timeout_ms())
        if response is None:
            raise ValueError('DIAGNOSTIC_NO_NAVIGATION_RESPONSE')
        return self._snapshot(response, True)

    def _snapshot(self, response, include_scope):
        if response.url != self.config['url'] or self.page.url != self.config['url']:
            raise ValueError('DIAGNOSTIC_QUERY_URL_CHANGED')
        output = self.guard.output
        write(output / 'response_receipt.json', {'url': self.config['url'], 'status': response.status,
            'captured_at': datetime.now(timezone.utc).isoformat(), 'capture_before_selector': True,
            'raw_body_or_DOM_archived': False})
        try:
            data = response.body()
        except Exception as exc:
            write(output / 'body_read_failure.json', {'error_type': type(exc).__name__})
            raise ValueError('DIAGNOSTIC_BODY_READ_FAILED') from None
        evidence = body_evidence(data, self.config['max_html_bytes'])
        write(output / 'body_evidence.json', evidence)
        if evidence['size_limit_exceeded']:
            raise ValueError('DIAGNOSTIC_BODY_SIZE_LIMIT')
        if evidence['marker_labels']:
            raise ValueError('DIAGNOSTIC_RESPONSE_MARKERS_STOP: ' + ','.join(evidence['marker_labels']))
        self.guard.check()
        if response.status != 200:
            raise ValueError('DIAGNOSTIC_HTTP200_REQUIRED')
        types = [r['headers'].get('content-type', '') or '' for r in self.guard.responses]
        if len(types) != 1 or types[0].split(';')[0].strip().casefold() != 'text/html':
            raise ValueError('DIAGNOSTIC_HTML_CONTENT_TYPE_REQUIRED')
        scope = self.page.content()
        dom = body_evidence(scope.encode('utf8'), self.config['max_html_bytes'])
        write(output / 'DOM_evidence_before_selector.json', dom)
        if dom['size_limit_exceeded'] or dom['marker_labels']:
            raise ValueError('DIAGNOSTIC_DOM_SIZE_OR_ACCESS_MARKERS_STOP')
        try:
            fragment = self.page.locator(prior.mbs.old.CONTAINER).evaluate(
                '(el) => el.outerHTML', timeout=self.guard.timeout_ms())
        except Exception as exc:
            write(output / 'selector_check.json', {'outcome': 'LOOKUP_FAILED', 'error_type': type(exc).__name__})
            raise ValueError('DIAGNOSTIC_RESULT_SELECTOR_LOOKUP_FAILED') from None
        write(output / 'selector_check.json', {'outcome': 'FOUND'})
        self.guard.check()
        # JS may have changed the DOM during the bounded selector wait.
        scope = self.page.content()
        final_dom = body_evidence(scope.encode('utf8'), self.config['max_html_bytes'])
        write(output / 'DOM_evidence_after_selector.json', final_dom)
        if final_dom['size_limit_exceeded'] or final_dom['marker_labels']:
            raise ValueError('DIAGNOSTIC_FINAL_DOM_SIZE_OR_ACCESS_MARKERS_STOP')
        return {'url': self.page.url, 'fragment': fragment, 'scope_html': scope,
            'http_body_sha256': evidence['sha256'], 'http_body_bytes': evidence['bytes'], 'http_status': response.status}


def single_run_gate(project):
    root = Path(project) / OUTPUT
    if root.exists() and any(root.glob('run-*')):
        raise ValueError('DIAGNOSTIC_ALREADY_RUN_REVIEW_REQUIRED_NO_RETRY')


def run(project, output, *, dry_run=False, driver_factory=DiagnosticDriver, clock=time.monotonic):
    project, output = Path(project).resolve(), Path(output).resolve()
    config, prep = load_preparation(project)
    single_run_gate(project)
    if output.exists(): raise FileExistsError('REFUSE_OVERWRITE')
    ready = prior.mbs.old.readiness(config)
    if dry_run:
        return {'status': 'OFFLINE_CHECK_PASS' if ready['ready'] else 'SETUP_REQUIRED',
            'ticker': 'APP', 'max_business_requests': 1, 'headless': True, 'source_requests': 0,
            'browser_launched': False, 'readiness': ready}
    if not ready['ready']: raise ValueError('LOCAL_BROWSER_SETUP_REQUIRED')
    output.mkdir(parents=True)
    query = output / 'APP'; query.mkdir(); (query / 'network_ledger.jsonl').touch()
    write(output / 'plan.json', config); write(output / 'runtime.json', runtime(project))
    write(output / 'inputs.json', {'preparation_manifest_sha256': sha((prep / 'manifest.json').read_bytes())})
    protected = read(prep / 'protected_old_files.json')
    check = lambda: prior.mbs.old.protected_check(project, protected)
    shared = prior.base.Budget(config, clock); shared.begin('APP_DIAGNOSTIC')
    local = {**config, 'max_context_request_attempts': 79, 'max_asset_attempts': 78}
    guard = prior.Guard(local, query, check, clock, shared)
    result = {'status': STOP, 'resumable': False, 'diagnostic_only': True, 'headless': True,
        'browser_launch_attempts': 0, 'browser_launches': 0, 'detail_requests': 0,
        'completed_query_count': 0, 'canonical_fields_applied': 0, 'owner_choices_changed': False,
        'pit_or_identity_promoted': False, 'full_history_certified': False, 'openai_api_calls': 0,
        'recovery_imported': False, 'manual_offline_review_pending': True}
    try:
        check(); result['browser_launch_attempts'] = 1
        with driver_factory(local, guard) as driver:
            result['browser_launches'] = 1
            current = driver.first(); guard.check()
            if current['url'] != config['url'] or current['http_status'] != 200:
                raise ValueError('DIAGNOSTIC_EXACT_QUERY_HTTP200_REQUIRED')
            data = prior.mbs.old.fragment_bytes(current['fragment'], config['max_html_bytes'])
            source = prior.source_contract(current['scope_html'], 'APP')
            page = prior.list_page(current['fragment'], 1, 'APP')
            (query / 'page1.html').write_bytes(data)
            write(query / 'page1.json', page); write(query / 'source_contract.json', source)
            write(query / 'fragment_receipt.json', {'sha256': sha(data), 'body_sha256': current['http_body_sha256'],
                'body_bytes': current['http_body_bytes'], 'first_page_only': True})
        guard.check(); check()
        if len(guard.business) != 1 or len(guard.responses) != 1 or guard.responses[0]['status'] != 200:
            raise ValueError('DIAGNOSTIC_EXACT_SINGLE_GET_RECEIPT_REQUIRED')
        result.update(status=PASS, first_page_rows=len(page['article_ids']), reported_total=page['coverage']['reported_total'])
    except KeyboardInterrupt:
        result.update(stop_reason='USER_INTERRUPT_NO_RESUME')
    except Exception as exc:
        # Driver/guard messages are fixed labels; never persist exception body/text.
        reason = safe_reason(guard.stop_reason or exc)
        result.update(stop_reason=reason, error_type=type(exc).__name__)
    finally:
        try: check(); shared.check()
        except Exception as exc: result.update(status=STOP, stop_reason=safe_reason(exc))
        write(query / 'business_requests.json', guard.business)
        write(query / 'business_responses.json', guard.responses)
        result.update(business_requests=len(guard.business), context_attempts=shared.attempts,
            asset_attempts=guard.assets, external_blocks=guard.external_blocked, active_seconds=clock() - shared.started)
        write(output / 'result.json', result)
    return result


def package(state):
    archive = state.parent / 'delta-vsdc-app-diagnostic.zip'
    prior.base.seal(state, archive, artifact_type=TYPE)
    prior.verify_zip(state, archive, TYPE)
    return archive
