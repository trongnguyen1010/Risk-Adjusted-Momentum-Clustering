from contextlib import ExitStack
import importlib.util
import inspect
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from delta_t1.ingestion.corporate_actions import vsdc_five_query4s_pilot as p
from tests.unit.ingestion.corporate_actions import test_vsdc_mbs_browser_html as fixture

ROOT = fixture.ROOT


class Driver(p.Driver):
    def __init__(self, config, guard, clock, mode=None):
        super().__init__(config, guard)
        self.clock, self.mode, self.closed = clock, mode, False
        self.version = 'MOCK_HEADLESS_CHROME'; self.page = MagicMock(); self.page.url = config['url']
        self.page.goto.side_effect = lambda *a, **k: self.respond(1)
        self.page.content.side_effect = lambda: self.scope
        button = MagicMock(); button.filter.return_value = button; button.count.return_value = 1
        button.click.side_effect = lambda **k: self.respond(self.number)
        container = MagicMock(); container.evaluate.side_effect = self.evaluate
        self.page.locator.side_effect = lambda selector: container if selector == '#divGlSearchArticles' else button
        self.pending = MagicMock(); self.pending.__enter__.return_value = self.pending
        self.page.expect_response.return_value = self.pending
        def wait(*a, **k):
            assert (guard.output / 'diagnostics' / f'page{self.number}' / 'body_evidence.json').exists()
            if mode == 'timeout' and config['ticker'] == 'APP' and self.number == 2:
                raise TimeoutError('secret-token-DO-NOT-SAVE')
        self.page.wait_for_function.side_effect = wait

    def respond(self, number):
        method = 'GET' if number == 1 else 'POST'
        payload = None if number == 1 else json.dumps({'SearchKey': 4, 'CurrentPage': number})
        assert self.guard.admit(self.config['url'], method, 'document' if number == 1 else 'xhr', payload)
        self.guard.business[-1].update(request_header_names=['content-type', 'x-requested-with'],
            request_content_type=None if number == 1 else 'application/json;charset=UTF-8',
            x_requested_with=None if number == 1 else 'XMLHttpRequest')
        ticker = self.config['ticker']; total = p.EXPECTED_ROWS[ticker]
        first, last = (number-1)*20+1, min(number*20, total)
        offset = 100000 + p.TICKERS.index(ticker)*1000
        self.fragment = fixture.second(first, last, total, list(range(offset+first, offset+last+1))).replace('MBS', ticker)
        self.scope = fixture.old.PAGE1.replace('MBS', ticker).replace(fixture.FIRST.replace('MBS', ticker), self.fragment)
        self.clock.sleep(.2)
        status = 429 if self.mode == '429' and ticker == 'APS' else 200
        self.guard.response(self.config['url'], method, status,
            {'content-type': 'text/html; charset=utf-8', 'content-length': None, 'retry-after': None})
        response = MagicMock(); response.url = self.config['url']; response.status = status
        data = self.scope.encode() if number == 1 else self.fragment.encode()
        if self.mode == 'challenge' and ticker == 'APP' and number == 2: data = b'<html>captcha secret-token-DO-NOT-SAVE</html>'
        response.body.return_value = data; self.pending.value = response
        return response

    def evaluate(self, *a, **k):
        assert (self.guard.output / 'diagnostics' / f'page{self.number}' / 'body_evidence.json').exists()
        if self.mode == 'missing' and self.config['ticker'] == 'APP': raise TimeoutError('secret-token-DO-NOT-SAVE')
        return self.fragment

    def pace(self, seconds):
        self.clock.sleep(seconds); self.guard.check()
    def __enter__(self): return self
    def __exit__(self, *args):
        self.closed = True
        if self.mode == 'cleanup':
            self.guard.fail('HEADLESS_QUERY_CLEANUP_FAILED'); raise ValueError('HEADLESS_QUERY_CLEANUP_FAILED')


class PilotTests(unittest.TestCase):
    def invoke(self, tmp, mode=None, dry=False, ready=True):
        root = Path(tmp); prep = root / 'prep'; prep.mkdir()
        for name, value in [('manifest.json', {'files': {}}), ('protected_old_files.json', {}),
                ('known_discovery_provider_ids.json', ['100001']), ('reusable_detail_provider_ids.json', ['100001'])]:
            p.write(prep / name, value)
        clock = fixture.old.Clock(); drivers = []
        def factory(config, guard):
            driver = Driver(config, guard, clock, mode); drivers.append(driver); return driver
        state = root / p.OUTPUT / 'run-test/state'
        with patch.object(p, 'load_preparation', return_value=(p.contract(), prep)), \
                patch.object(p, 'runtime', return_value={'test_only': 'frozen'}), \
                patch.object(p.mbs.old, 'readiness', return_value={'ready': ready}):
            result = p.run(root, state, driver_factory=factory, clock=clock.now, dry_run=dry, emit=lambda *a, **k: None)
        return result, drivers, state

    def test_five_full_queries11requests_and4s_across_pages_and_tickers(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, drivers, state = self.invoke(tmp)
            self.assertEqual(p.PASS, result['status'], result)
            self.assertEqual(list(p.TICKERS), result['completed_tickers'])
            self.assertEqual(5, result['completed_query_count']); self.assertEqual(11, result['business_requests'])
            self.assertEqual(5, result['browser_launches']); self.assertTrue(all(d.closed for d in drivers))
            calls = [r for f in sorted((state / 'queries').glob('*/state/*/business_requests.json')) for r in p.read(f)]
            self.assertEqual(11, len(calls))
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic'] >= 4 for a, b in zip(calls, calls[1:])))
            self.assertEqual(150, sum(sum(p.read(f)['query_rows'].values()) for f in (state / 'queries').glob('*/validation.json')))
            self.assertFalse(result['recovery_imported']); self.assertEqual(0, result['detail_requests'])
            p.prior.verify_zip(state, p.package(state), p.TYPE)
            rows = p.mbs.old.rows(state / 'progress.jsonl')
            self.assertEqual([1, 2, 3, 4, 5], [r['completed_queries'] for r in rows if r['event'] == 'QUERY_VALIDATED'])

    def test_every_page_has_diagnostics_before_wait_and_public_reparse(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _, state = self.invoke(tmp)
            folders = list((state / 'queries').glob('*/state/*/diagnostics/page*'))
            self.assertEqual(11, len(folders))
            self.assertTrue(all(p.read(f / 'response_receipt.json')['capture_before_DOM_wait'] for f in folders))
            self.assertTrue(all(not p.read(f / 'body_evidence.json')['raw_archived'] for f in folders))

    def test_429_on_second_query_stops_before_later_queries_and_preserves_APP(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, drivers, state = self.invoke(tmp, mode='429')
            self.assertEqual(p.STOP, result['status']); self.assertEqual(['APP'], result['completed_tickers'])
            self.assertEqual(2, len(drivers)); self.assertEqual(4, result['business_requests'])
            receipt = state / 'queries/0002/state/APS/diagnostics/page1/response_receipt.json'
            self.assertEqual(429, p.read(receipt)['status']); self.assertFalse((state / 'queries/0003').exists())
            p.prior.verify_zip(state, p.package(state), p.TYPE)

    def test_page2_challenge_timeout_missing_selector_and_cleanup_stop_with_evidence(self):
        for mode in ('challenge', 'timeout', 'missing', 'cleanup'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                result, drivers, state = self.invoke(tmp, mode=mode)
                self.assertEqual(p.STOP, result['status']); self.assertEqual([], result['completed_tickers'])
                self.assertTrue(all(d.closed for d in drivers)); self.assertEqual(1, len(drivers))
                expected_page = 2 if mode in ('challenge', 'timeout') else 1
                diag = state / f'queries/0001/state/APP/diagnostics/page{expected_page}'
                self.assertTrue((diag / 'body_evidence.json').exists())
                self.assertNotIn('secret-token-DO-NOT-SAVE', ''.join(f.read_text(encoding='utf8') for f in state.rglob('*.json')))
                self.assertFalse(result['resumable']); p.package(state)

    def test_resealed_2s_interval_or_diagnostic_extra_file_is_rejected(self):
        for mode in ('pace', 'extra', 'structure', 'binding'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                _, _, state = self.invoke(tmp); folder = state / 'queries/0001'; query = folder / 'state/APP'
                if mode == 'pace':
                    file = query / 'business_requests.json'; rows = p.read(file)
                    rows[1]['at_monotonic'] = rows[0]['at_monotonic']+2; file.write_text(json.dumps(rows), encoding='utf8')
                elif mode == 'extra': (query / 'diagnostics/page1/raw_body.txt').write_text('private', encoding='utf8')
                else:
                    file = query / 'diagnostics/page1/body_evidence.json'; obj = p.read(file)
                    if mode == 'structure': obj['structure']['private_text'] = 'private'
                    else: obj['sha256'] = '0'*64
                    file.write_text(json.dumps(obj), encoding='utf8')
                (folder / 'state/manifest.json').unlink(); (folder / 'query.zip').unlink()
                p.base.seal(folder / 'state', folder / 'query.zip', artifact_type=p.QUERY_TYPE)
                with self.assertRaises(ValueError):
                    p.validate_query(folder, p.read(folder / 'context.json')['definition'], {'100001'}, {'100001'}, None)

    def test_dryrun_setup_and_single_run_gate_never_launch_real_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, drivers, state = self.invoke(tmp, dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS', result['status']); self.assertFalse(state.exists()); self.assertEqual([], drivers)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'SETUP_REQUIRED'): self.invoke(tmp, ready=False)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / p.OUTPUT / 'run-crash/state').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'NO_RETRY'): p.single_run_gate(tmp)


class ContractTests(unittest.TestCase):
    def test_exact_contract_no_bulk_identity_retry_resume_or_rate_override(self):
        for key, val in [('business_interval_seconds', 2), ('pilot_tickers', ['APP']), ('headless', False),
                ('retry', True), ('resume', True), ('recovery_import', True), ('details', True),
                ('max_business_requests', 100), ('ignore_https_errors', True), ('user_agent', 'spoof')]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); (root / p.CONFIG).parent.mkdir(parents=True); p.write(root / p.CONFIG, {**p.contract(), key: val})
                with patch.object(p, 'parents') as parent, self.assertRaisesRegex(ValueError, 'EXACT_FIVE_QUERY4S'):
                    p.load_preparation(root)
                parent.assert_not_called()
        self.assertIs(p.Driver.__enter__, p.diagnostic.DiagnosticDriver.__enter__)
        self.assertIs(p.Driver._route, p.diagnostic.DiagnosticDriver._route)
        self.assertIs(p.Driver.__exit__, p.diagnostic.DiagnosticDriver.__exit__)

    def test_literal_source_loop_assertions_preserved_except4s(self):
        expected = inspect.getsource(p.prior.acquire_query).replace('max(0,2-(clock()-shared.last))', 'max(0,4-(clock()-shared.last))').replace("'business_interval_seconds':2", "'business_interval_seconds':4")
        self.assertEqual(expected, inspect.getsource(p.acquire_query))
        expected = inspect.getsource(p.base.validate_batch).replace('def validate_batch(', 'def _validate_source_query(').replace("result['business_interval_seconds']!=2", "result['business_interval_seconds']!=4").replace('any(b-a<2 for a,b in zip(starts,starts[1:]))', 'any(b-a<4 for a,b in zip(starts,starts[1:]))').replace('CHAIN_PACING_BELOW_TWO_SECONDS', 'PILOT_PACING_BELOW_FOUR_SECONDS')
        self.assertEqual(expected, inspect.getsource(p._validate_source_query))

    def test_guard_rejects_just_under4seconds_even_if_above_old2seconds(self):
        for gap, allowed in [(2, False), (3.999, False), (4, True)]:
            with self.subTest(gap=gap), tempfile.TemporaryDirectory() as tmp:
                c = p.contract(); clock = fixture.old.Clock(); shared = p.base.Budget(c, clock.now); shared.begin('PILOT4S')
                guard = p.Guard({**c, 'url': p.search_url('APP'), 'max_context_request_attempts': 98}, Path(tmp), lambda: None, clock.now, shared)
                self.assertTrue(guard.admit(p.search_url('APP'), 'GET', 'document'))
                clock.sleep(gap)
                self.assertEqual(allowed, guard.admit(p.search_url('APP'), 'POST', 'xhr', '{"SearchKey":4,"CurrentPage":2}'))

    def test_global_request_and_context_budgets_do_not_reset_on_new_query(self):
        for key in ('max_business_requests', 'max_context_attempts'):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                config = {**p.contract(), key: 1}; clock = fixture.old.Clock()
                shared = p.base.Budget(config, clock.now)
                for index, ticker in enumerate(p.TICKERS[:2]):
                    output = Path(tmp) / ticker; output.mkdir(); shared.begin('PILOT4S')
                    guard = p.Guard({**config, 'url': p.search_url(ticker), 'max_context_request_attempts': 98},
                        output, lambda: None, clock.now, shared)
                    self.assertEqual(index == 0, guard.admit(p.search_url(ticker), 'GET', 'document'))
                    if index == 0: shared.end(); clock.sleep(4)
                self.assertEqual(1, shared.business); self.assertIsNotNone(guard.stop_reason)

    def test_CLI_has_no_interval_subset_retry_resume_or_headed_flags(self):
        spec = importlib.util.spec_from_file_location('pilot4_cli', ROOT / 'scripts/corporate_actions/collect_vsdc_five_query4s_pilot_v1.py')
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        for flag in ('--interval', '--force', '--resume', '--headed', '--tickers'):
            with patch('sys.argv', ['cli', flag]), patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit): cli.main()


if __name__ == '__main__': unittest.main()
