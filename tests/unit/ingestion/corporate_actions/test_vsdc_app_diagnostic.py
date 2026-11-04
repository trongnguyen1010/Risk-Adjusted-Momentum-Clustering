from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch
import unittest
import zipfile

from delta_t1.ingestion.corporate_actions import vsdc_app_diagnostic as p
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_browser_html as fixture

ROOT = fixture.ROOT
SCOPE = fixture.old.PAGE1.replace('MBS', 'APP')
FRAGMENT = fixture.FIRST.replace('MBS', 'APP')


class FakeDriver(p.DiagnosticDriver):
    def __init__(self, config, guard, clock, *, mode=None, body=None, status=200, content_type='text/html; charset=utf-8'):
        super().__init__(config, guard)
        self.mode, self.clock, self.closed = mode, clock, False
        self.page = MagicMock(); self.page.url = config['url']
        self.page.content.return_value = SCOPE
        self.response = MagicMock(); self.response.url = config['url']; self.response.status = status
        self.response.body.return_value = (SCOPE.encode() if body is None else body)
        if mode == 'body_read': self.response.body.side_effect = ValueError('secret-token-DO-NOT-SAVE')
        def navigate(*args, **kwargs):
            if mode == 'interrupt': raise KeyboardInterrupt()
            if mode == 'navigation': raise ValueError('secret-token-DO-NOT-SAVE')
            self.clock.sleep(.2)
            allowed = guard.admit(config['url'], 'GET', 'document')
            if not allowed: guard.check()
            guard.response(config['url'], 'GET', status, {'content-type': content_type, 'retry-after': '10' if mode == 'retry_after' else None})
            return self.response
        self.page.goto.side_effect = navigate
        def evaluate(*args, **kwargs):
            if not (guard.output / 'body_evidence.json').is_file():
                raise AssertionError('RESPONSE_EVIDENCE_MUST_EXIST_BEFORE_SELECTOR')
            if mode == 'missing':
                self.clock.sleep(15)
                raise TimeoutError('secret-token-DO-NOT-SAVE')
            return '<div id="divGlSearchArticles">invalid</div>' if mode == 'layout' else FRAGMENT
        self.page.locator.return_value.evaluate.side_effect = evaluate

    def __enter__(self): return self
    def __exit__(self, *args):
        self.closed = True
        if self.mode == 'cleanup':
            self.guard.fail('HEADLESS_QUERY_CLEANUP_FAILED')
            raise ValueError('HEADLESS_QUERY_CLEANUP_FAILED')


class DiagnosticTests(unittest.TestCase):
    def invoke(self, folder, *, dry=False, ready=True, **options):
        root = Path(folder); prep = root / 'prep'; prep.mkdir()
        p.write(prep / 'protected_old_files.json', {})
        p.write(prep / 'manifest.json', {'files': {}})
        clock = fixture.old.Clock(); drivers = []
        def factory(config, guard):
            driver = FakeDriver(config, guard, clock, **options); drivers.append(driver); return driver
        state = root / p.OUTPUT / 'run-test/state'
        with patch.object(p, 'load_preparation', return_value=(p.contract(), prep)), \
                patch.object(p, 'runtime', return_value={'test_only': 'frozen'}), \
                patch.object(p.prior.mbs.old, 'readiness', return_value={'ready': ready}):
            result = p.run(root, state, dry_run=dry, driver_factory=factory, clock=clock.now)
        return result, drivers, state

    def test_single_GET_valid_first_page_has_evidence_before_selector_and_no_completion_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, drivers, state = self.invoke(tmp)
            self.assertEqual(p.PASS, result['status'], result)
            self.assertEqual(1, result['business_requests']); self.assertEqual(1, result['browser_launches'])
            self.assertEqual(20, result['first_page_rows']); self.assertEqual(0, result['completed_query_count'])
            self.assertFalse(result['recovery_imported']); self.assertFalse(result['resumable'])
            self.assertTrue(drivers[0].closed); drivers[0].page.goto.assert_called_once()
            self.assertTrue(p.read(state / 'APP/response_receipt.json')['capture_before_selector'])
            self.assertEqual(p.sha(SCOPE.encode()), p.read(state / 'APP/body_evidence.json')['sha256'])
            self.assertEqual(20, len(p.read(state / 'APP/page1.json')['article_ids']))
            self.assertFalse((state / 'APP/complete_query.json').exists())
            self.assertFalse((state / 'APP/page2.html').exists())

    def test_missing_selector_still_preserves_response_hash_structure_before_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, drivers, state = self.invoke(tmp, mode='missing', body=b'<html><title>Error</title><p>Unavailable</p></html>')
            self.assertEqual(p.STOP, result['status']); self.assertTrue(drivers[0].closed)
            evidence = p.read(state / 'APP/body_evidence.json')
            self.assertEqual(0, evidence['structure']['article_containers'])
            self.assertIsNotNone(evidence['sha256'])
            self.assertEqual('LOOKUP_FAILED', p.read(state / 'APP/selector_check.json')['outcome'])
            self.assertEqual('DIAGNOSTIC_RESULT_SELECTOR_LOOKUP_FAILED', result['stop_reason'])
            self.assertFalse((state / 'APP/page1.html').exists())

    def test_DOM_changed_to_access_boundary_during_selector_wait_is_not_accepted(self):
        for scope in ['<html>Verify you are human</html>', '<html><input type="password"></html>']:
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); query = root / 'APP'; query.mkdir()
                clock = fixture.old.Clock(); config = {**p.contract(),
                    'max_context_request_attempts': 79, 'max_asset_attempts': 78}
                shared = p.prior.base.Budget(config, clock.now); shared.begin('APP_DIAGNOSTIC')
                guard = p.prior.Guard(config, query, lambda: None, clock.now, shared)
                driver = FakeDriver(config, guard, clock)
                driver.page.content.side_effect = [SCOPE, scope]
                with self.assertRaisesRegex(ValueError, 'FINAL_DOM'):
                    driver.first()
                self.assertTrue(p.read(query / 'DOM_evidence_after_selector.json')['marker_labels'])

    def test_access_rate_error_and_password_markers_STOP_before_selector_and_never_archive_secrets(self):
        for text, label in [('Verify you are human captcha', 'ACCESS_CHALLENGE'),
                ('Too many requests', 'RATE_LIMIT'), ('Service unavailable', 'SERVICE_UNAVAILABLE'),
                ('Internal server error', 'SERVER_ERROR'), ('<input type="password" value="secret">', 'PASSWORD_FORM')]:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                body = ('<html><form><input name="csrf" value="secret-token-DO-NOT-SAVE"></form>' + text + '</html>').encode()
                result, drivers, state = self.invoke(tmp, body=body)
                self.assertEqual(p.STOP, result['status']); drivers[0].page.locator.assert_not_called()
                self.assertIn(label, p.read(state / 'APP/body_evidence.json')['marker_labels'])
                all_text = ''.join(f.read_text(encoding='utf8') for f in state.rglob('*') if f.is_file())
                self.assertNotIn('secret-token-DO-NOT-SAVE', all_text)
                self.assertNotIn('<html>', all_text)

    def test_HTTP403_429_500_and_retry_after_have_receipt_and_no_selector_or_retry(self):
        for status, mode in [(403, None), (429, None), (500, None), (200, 'retry_after')]:
            with self.subTest(status=status, mode=mode), tempfile.TemporaryDirectory() as tmp:
                result, drivers, state = self.invoke(tmp, status=status, mode=mode, body=b'<html>error</html>')
                self.assertEqual(p.STOP, result['status']); self.assertEqual(1, result['business_requests'])
                drivers[0].page.locator.assert_not_called(); drivers[0].page.goto.assert_called_once()
                self.assertEqual(status, p.read(state / 'APP/response_receipt.json')['status'])
                self.assertTrue((state / 'APP/body_evidence.json').is_file())

    def test_body_failure_oversize_wrong_type_and_invalid_layout_fail_closed(self):
        for options in [{'mode': 'body_read'}, {'body': b'x' * 2000001},
                {'body': b'{}', 'content_type': 'application/json'}, {'mode': 'layout'}]:
            with self.subTest(options=list(options)), tempfile.TemporaryDirectory() as tmp:
                result, drivers, state = self.invoke(tmp, **options)
                self.assertEqual(p.STOP, result['status']); self.assertTrue(drivers[0].closed)
                self.assertEqual(0, result['completed_query_count'])
                self.assertNotIn('secret-token-DO-NOT-SAVE', (state / 'result.json').read_text())
                if options.get('mode') == 'body_read':
                    self.assertTrue((state / 'APP/body_read_failure.json').exists())
                if 'body' in options and len(options['body']) > 2000000:
                    self.assertIsNone(p.read(state / 'APP/body_evidence.json')['sha256'])

    def test_interrupt_navigation_and_cleanup_errors_never_succeed_or_resume(self):
        for mode in ['interrupt', 'navigation', 'cleanup']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                result, drivers, state = self.invoke(tmp, mode=mode)
                self.assertEqual(p.STOP, result['status']); self.assertFalse(result['resumable'])
                self.assertTrue(drivers[0].closed)
                self.assertNotIn('secret-token-DO-NOT-SAVE', json.dumps(result))

    def test_offline_check_and_missing_setup_do_not_create_browser_or_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, drivers, state = self.invoke(tmp, dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS', result['status']); self.assertEqual([], drivers)
            self.assertFalse(state.exists())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'LOCAL_BROWSER_SETUP_REQUIRED'):
                self.invoke(tmp, ready=False)
            self.assertFalse((Path(tmp) / p.OUTPUT).exists())

    def test_single_execution_gate_blocks_second_diagnostic_or_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p.single_run_gate(tmp)
            (Path(tmp) / p.OUTPUT / 'run-unsealed').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'NO_RETRY'): p.single_run_gate(tmp)

    def test_partial_and_success_ZIP_preserve_exact_state_and_diagnostics(self):
        for mode in [None, 'missing']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                _, _, state = self.invoke(tmp, mode=mode)
                archive = p.package(state)
                p.prior.verify_zip(state, archive, p.TYPE)
                with zipfile.ZipFile(archive) as z:
                    self.assertIn('APP/body_evidence.json', z.namelist())
                    self.assertIsNone(z.testzip())
                    self.assertEqual((state / 'result.json').read_bytes(), z.read('result.json'))


class ContractAndGateTests(unittest.TestCase):
    def test_exact_contract_rejects_ticker_pages_retry_identity_and_timeout_expansion(self):
        for key, value in [('ticker', 'MBS'), ('max_business_requests', 2), ('max_seconds', 181),
                ('max_list_pages_per_query', 2), ('headless', False), ('retry', True), ('resume', True),
                ('details', True), ('ignore_https_errors', True), ('workers', 2), ('recovery_import', True),
                ('operation_timeout_seconds', 30), ('response_policy', 'RAW_BODY'), ('custom_headers', {})]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); path = root / p.CONFIG; path.parent.mkdir(parents=True)
                p.write(path, {**p.contract(), key: value})
                with patch.object(p, 'parents') as parent, self.assertRaisesRegex(ValueError, 'EXACT_APP'):
                    p.load_preparation(root)
                parent.assert_not_called()
        self.assertIs(p.DiagnosticDriver.__enter__, p.prior.HeadlessDriver.__enter__)
        self.assertIs(p.DiagnosticDriver._route, p.prior.HeadlessDriver._route)
        self.assertIs(p.DiagnosticDriver.__exit__, p.prior.HeadlessDriver.__exit__)

    def test_guard_admits_only_one_fresh_APP_GET_no_POST_other_query_or_details(self):
        for second_url, method, resource, payload in [
                (p.contract()['url'], 'GET', 'document', None),
                (p.contract()['url'], 'POST', 'xhr', '{"SearchKey":4,"CurrentPage":2}'),
                (p.prior.search_url('MBS'), 'GET', 'document', None),
                ('https://vsdc.vn/vi/ad/123456', 'GET', 'document', None)]:
            with tempfile.TemporaryDirectory() as tmp:
                c = p.contract(); clock = fixture.old.Clock()
                shared = p.prior.base.Budget(c, clock.now); shared.begin('APP_DIAGNOSTIC')
                guard = p.prior.Guard({**c, 'max_context_request_attempts': 79, 'max_asset_attempts': 78},
                    Path(tmp), lambda: None, clock.now, shared)
                self.assertTrue(guard.admit(c['url'], 'GET', 'document'))
                clock.sleep(2)
                self.assertFalse(guard.admit(second_url, method, resource, payload))
                self.assertEqual(1, shared.business); self.assertIsNotNone(guard.stop_reason)

    def test_body_summary_has_fixed_fields_and_no_body_title_attributes_or_text(self):
        data = b'<html><title>secret-title</title><form action="secret-url"><input name="token" value="secret-token"></form><div id="divGlSearchArticles"></div></html>'
        evidence = p.body_evidence(data)
        self.assertEqual({'bytes', 'sha256', 'size_limit_exceeded', 'structure', 'marker_labels', 'raw_archived'}, set(evidence))
        self.assertEqual(1, evidence['structure']['article_containers'])
        self.assertFalse(evidence['raw_archived']); self.assertNotIn('secret', json.dumps(evidence))

    def test_CLI_has_no_force_resume_headed_interval_or_bulk_flags(self):
        spec = importlib.util.spec_from_file_location('app_cli', ROOT / 'scripts/corporate_actions/collect_vsdc_app_diagnostic_v1.py')
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        for flag in ['--force', '--resume', '--headed', '--batch', '--interval', '--retry']:
            with self.subTest(flag=flag), patch('sys.argv', ['cli', flag]), patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                cli.main()


if __name__ == '__main__': unittest.main()
