from contextlib import ExitStack
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions import vsdc_recovery_ors_hold as p
from tests.unit.ingestion.corporate_actions import test_vsdc_five_query4s_pilot as fixture

ROOT = fixture.ROOT
SELECTED = [{'batch_id': 'proposed-002', 'tickers': ['IMPORTED'], 'estimated_list_requests': 1},
    {'batch_id': 'proposed-003', 'tickers': ['APP', 'APS'], 'estimated_list_requests': 5},
    {'batch_id': 'proposed-004', 'tickers': ['ARM'], 'estimated_list_requests': 2}]


class RecoveryTests(unittest.TestCase):
    def setup(self, tmp, totals=None):
        root = Path(tmp); prep = root / 'prep'; prep.mkdir()
        costs = totals or p.initial_totals(SELECTED)
        if totals is None:
            costs.update(business=45, context=1155, active_seconds=159.719)
            costs['batches']['proposed-002'] = {'business': 45, 'context': 1155, 'active_seconds': 159.719}
        for name, data in [('manifest.json', {'files': {}}), ('protected_old_files.json', {}),
                ('selected_batches.json', SELECTED), ('reusable_detail_provider_ids.json', ['100001']),
                ('known_discovery_provider_ids.json', ['100001']), ('cache_policy.json', {}),
                ('query_inventory_before_chain.json', []), ('seed.json', {'completed': p.flatten(SELECTED)[:1],
                'sources': [], 'totals': costs, 'durations': []})]: p.write(prep / name, data)
        folder = p.query_folder(prep, 0); folder.mkdir(parents=True)
        (folder / 'source-evidence.bin').write_bytes(b'IMMUTABLE_ORIGINAL_2S_OR_4S_PREFIX')
        original = json.loads(json.dumps(SELECTED)); original[1]['tickers'].insert(0, 'ORS')
        hold_folder = prep / 'holds/ORS'; hold_folder.mkdir(parents=True)
        (hold_folder / 'partial80of85.txt').write_text('PRESERVED_ORS80ROWS_NOT_COMPLETE', encoding='utf8')
        p.write(prep / 'held_query.json', {'ticker': 'ORS', 'status': 'HOLD_SOURCE_COUNT_GAP',
            'reported_total': 85, 'observed_distinct_rows': 80, 'unresolved_reported_row_slots': 5,
            'query_complete': False, 'evidence_files': p.hashes(hold_folder)})
        p.write(prep / 'original_selected_batches.json', original)
        return root, prep

    def invoke(self, root, prep, number=1, trigger=None, mode=None, start=1000, dry=False, fail_validation=False):
        output = root / p.OUTPUT / f'run-{number:03d}' / 'state'
        pause = p.Pause(output.parent / 'PAUSE_REQUEST'); clock = fixture.fixture.old.Clock()
        clock.sleep(start-clock.now()); drivers = []
        def factory(config, guard):
            driver = fixture.Driver(config, guard, clock, mode); drivers.append(driver)
            original = driver.respond
            def respond(n):
                response = original(n)
                if trigger == (config['ticker'], n): pause.request()
                return response
            driver.respond = respond
            return driver
        with ExitStack() as stack:
            stack.enter_context(patch.object(p, 'load_preparation', return_value=(p.contract(), prep)))
            stack.enter_context(patch.object(p, 'runtime', return_value={'test_only': 'frozen'}))
            stack.enter_context(patch.object(p.mbs.old, 'readiness', return_value={'ready': True}))
            if fail_validation: stack.enter_context(patch.object(p, 'validate_batch', side_effect=ValueError('TEST_VALIDATION_FAIL')))
            result = p.run(root, output, pause=pause, driver_factory=factory, clock=clock.now,
                emit=lambda *a, **k: None, dry_run=dry)
            if not dry: p.seal_run(output)
        return result, drivers, output

    def test_imported_prefix_never_refetched_costs_preserved_and_all_remaining_batches_run_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = self.setup(tmp); prefix = p.hashes(p.query_folder(prep, 0))
            result, drivers, state = self.invoke(root, prep)
            self.assertEqual(p.COMPLETE, result['status'], result)
            self.assertEqual(['APP', 'APS', 'ARM'], [d.config['ticker'] for d in drivers])
            self.assertEqual(4, result['completed_query_count']); self.assertEqual(7, result['source_requests_this_segment'])
            self.assertEqual(52, result['totals']['business']); self.assertEqual(1162, result['totals']['context'])
            self.assertGreater(result['totals']['active_seconds'], 159.719)
            self.assertEqual(prefix, p.hashes(p.query_folder(state, 0)))
            progress = p.mbs.old.rows(state / 'progress.jsonl')
            self.assertEqual(1, progress[0]['completed_queries']); self.assertEqual(3, progress[0]['remaining_queries'])
            self.assertEqual(1, progress[0]['completed_batches']); self.assertEqual(2, progress[0]['batch_index'])
            self.assertIsNone(progress[0]['ETA_seconds'])
            calls = [r for file in sorted((state / 'queries').glob('*/state/*/business_requests.json')) for r in p.read(file)]
            self.assertTrue(all(b['at_monotonic']-a['at_monotonic'] >= 4 for a, b in zip(calls, calls[1:])))
            with self.assertRaisesRegex(ValueError, 'ONLY_USER_PAUSED_RUN'): self.invoke(root, prep, 2)

    def test_user_pause_mid_query_then_skip_completed_restart_partial_page1_costs_carry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = self.setup(tmp)
            a, drivers, s1 = self.invoke(root, prep, trigger=('APS', 1))
            self.assertEqual(p.PAUSED, a['status'], a); self.assertEqual(2, a['completed_query_count'])
            self.assertEqual(49, a['totals']['business'])
            copied = p.hashes(p.query_folder(s1, 1))
            b, drivers, s2 = self.invoke(root, prep, 2, start=100000)
            self.assertEqual(p.COMPLETE, b['status'], b)
            self.assertEqual(['APS', 'ARM'], [d.config['ticker'] for d in drivers])
            self.assertEqual(53, b['totals']['business']); self.assertEqual(4, b['source_requests_this_segment'])
            self.assertLess(b['totals']['active_seconds'], 300)
            self.assertEqual(copied, p.hashes(p.query_folder(s2, 1)))
            rows = p.mbs.old.rows(s2 / 'progress.jsonl'); self.assertEqual(2, rows[0]['completed_queries'])
            self.assertEqual('GET', p.read(s2 / 'queries/0003/state/APS/business_requests.json')[0]['method'])

    def test_source_error_even_with_simultaneous_pause_never_allows_retry(self):
        for trigger in [None, ('APS', 1)]:
            with self.subTest(trigger=trigger), tempfile.TemporaryDirectory() as tmp:
                root, prep = self.setup(tmp)
                result, _, state = self.invoke(root, prep, mode='429', trigger=trigger)
                self.assertEqual(p.STOPPED, result['status']); self.assertFalse(result['resumable'])
                self.assertEqual(2, result['completed_query_count']); self.assertEqual(49, result['totals']['business'])
                self.assertTrue((state / 'queries/0003/state/APS/diagnostics/page1/body_evidence.json').exists())
                with self.assertRaisesRegex(ValueError, 'ONLY_USER_PAUSED_RUN'): self.invoke(root, prep, 2)

    def test_resealed_imported_copy_progress_and_new_query_tamper_rejected_before_browser(self):
        for mode in ('imported', 'progress', 'query'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root, prep = self.setup(tmp); _, _, state = self.invoke(root, prep, trigger=('APS', 1))
                if mode == 'imported': (p.query_folder(state, 0) / 'source-evidence.bin').write_bytes(b'CHANGED')
                elif mode == 'progress':
                    file = state / 'progress.jsonl'; rows = p.mbs.old.rows(file); rows[0]['completed_queries'] = 0
                    file.write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf8')
                else:
                    folder = p.query_folder(state, 1); file = folder / 'state/APP/page1.json'; data = p.read(file); data['page'] = 9
                    file.write_text(json.dumps(data), encoding='utf8'); (folder / 'state/manifest.json').unlink(); (folder / 'query.zip').unlink()
                    p.base.seal(folder / 'state', folder / 'query.zip', artifact_type=p.pilot.QUERY_TYPE)
                (state / 'manifest.json').unlink(); (state.parent / 'delta-vsdc-recovery-ORS-HOLD.zip').unlink(); p.seal_run(state)
                with self.assertRaises(ValueError): self.invoke(root, prep, 2)

    def test_budget_not_reset_after_import_including_request_and_batch_time(self):
        for mode in ('global', 'batch_time'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                totals = p.initial_totals(SELECTED)
                if mode == 'global': totals['business'] = 5399
                else: totals['batches']['proposed-003']['active_seconds'] = 1199.9
                root, prep = self.setup(tmp, totals)
                result, drivers, state = self.invoke(root, prep)
                self.assertEqual(p.STOPPED, result['status']); self.assertFalse(result['resumable'])
                self.assertEqual(1, result['completed_query_count'])
                if mode == 'global': self.assertEqual(5400, result['totals']['business'])

    def test_validation_failure_accounts_requests_without_false_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = self.setup(tmp); result, _, _ = self.invoke(root, prep, fail_validation=True)
            self.assertEqual(p.STOPPED, result['status']); self.assertEqual(1, result['completed_query_count'])
            self.assertEqual(3, result['source_requests_this_segment']); self.assertEqual(48, result['totals']['business'])

    def test_dryrun_and_unsealed_crash_never_open_new_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = self.setup(tmp); result, drivers, state = self.invoke(root, prep, dry=True)
            self.assertEqual('OFFLINE_CHECK_PASS', result['status']); self.assertEqual(1, result['completed_queries'])
            self.assertEqual(2, result['remaining_batches']); self.assertEqual([], drivers); self.assertFalse(state.exists())
            _, _, state = self.invoke(root, prep, trigger=('APP', 1)); (state / 'manifest.json').unlink()
            with self.assertRaises(Exception): self.invoke(root, prep, 2)

    def test_pause_control_and_exclusive_lock_target_only_V4(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); output = root / p.OUTPUT; (output / 'run-test/state').mkdir(parents=True)
            with p.execution_lock(output, 'run-test'):
                self.assertEqual('PAUSE_REQUESTED', p.request_pause(root)['status'])
                self.assertTrue((output / 'run-test/PAUSE_REQUEST').exists())
                with self.assertRaises(FileExistsError):
                    with p.execution_lock(output, 'run-other'): pass
            self.assertFalse((output / 'active.lock').exists())

    def test_scoped_completion_keeps_ORS_unresolved_and_original_batch_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = self.setup(tmp); result, drivers, state = self.invoke(root, prep)
            self.assertEqual(p.COMPLETE, result['status']); self.assertFalse(result['original_full_scope_complete'])
            self.assertEqual(1, result['held_query_count']); self.assertEqual(['ORS'], result['held_tickers'])
            self.assertEqual(1, result['original_unresolved_query_count'])
            self.assertEqual(5, result['original_total_queries']); self.assertEqual(4, result['scoped_total_queries'])
            self.assertNotIn('proposed-003', result['original_fully_completed_batch_ids'])
            self.assertIn('proposed-003', result['validated_batch_ids'])
            self.assertNotIn('ORS', [d.config['ticker'] for d in drivers])
            self.assertEqual(p.hashes(prep / 'holds/ORS'), p.hashes(state / 'holds/ORS'))
            lines = (state / 'progress.log').read_text(encoding='utf8').splitlines()
            self.assertTrue(all('ORS HOLD 1 (80/85)' in line for line in lines))
            self.assertEqual(0, result['remaining_query_count'])

    def test_resealed_HOLD_partial_or_metadata_or_original_scope_tamper_cannot_resume(self):
        for mode in ('partial', 'metadata', 'original'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root, prep = self.setup(tmp); _, _, state = self.invoke(root, prep, trigger=('APP', 1))
                if mode == 'partial': (state / 'holds/ORS/partial80of85.txt').write_text('ALTERED', encoding='utf8')
                elif mode == 'metadata':
                    f = state / 'held_query.json'; x = p.read(f); x['query_complete'] = True; f.write_text(json.dumps(x), encoding='utf8')
                else:
                    f = state / 'original_selected_batches.json'; x = p.read(f); x[1]['tickers'].remove('ORS'); f.write_text(json.dumps(x), encoding='utf8')
                (state / 'manifest.json').unlink(); (state.parent / 'delta-vsdc-recovery-ORS-HOLD.zip').unlink(); p.seal_run(state)
                with self.assertRaisesRegex(ValueError, 'HOLD_EVIDENCE_OR_SCOPE'): self.invoke(root, prep, 2)

    def test_pause_before_any_new_query_keeps_prefix_costs_and_HOLD(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = self.setup(tmp)
            original_run = p.run
            def preset_pause(*args, **kwargs):
                kwargs['pause'].request(); return original_run(*args, **kwargs)
            with patch.object(p, 'run', side_effect=preset_pause): result, drivers, state = self.invoke(root, prep)
            self.assertEqual(p.PAUSED, result['status']); self.assertEqual([], drivers)
            self.assertEqual(45, result['totals']['business']); self.assertEqual(1, result['completed_query_count'])
            self.assertEqual(4, result['original_unresolved_query_count']); self.assertEqual(1, result['held_query_count'])
            result2, drivers, _ = self.invoke(root, prep, 2, start=100000)
            self.assertEqual(p.COMPLETE, result2['status']); self.assertEqual(1, result2['original_unresolved_query_count'])

    def test_hold_count_cannot_be_relabelled_complete_even_after_resealing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = self.setup(tmp); _, _, state = self.invoke(root, prep, trigger=('APP', 1))
            file = state / 'result.json'; result = p.read(file); result['held_query_count'] = 0
            result['original_full_scope_complete'] = True; file.write_text(json.dumps(result), encoding='utf8')
            (state / 'manifest.json').unlink(); (state.parent / 'delta-vsdc-recovery-ORS-HOLD.zip').unlink(); p.seal_run(state)
            with self.assertRaisesRegex(ValueError, 'HOLD_COUNTS_OR_ORIGINAL_SCOPE'): self.invoke(root, prep, 2)


class ContractTests(unittest.TestCase):
    def test_contract_rejects_unreviewed_import_rate_identity_or_gate_override(self):
        for key, val in [('reviewed_import_count', 19), ('remaining_queries_before_first_run', 498),
                ('recovery_import', 'ANY_ERROR'), ('source_error_resume', True), ('automatic_retry', True),
                ('scope_and_source_caps', {**p.caps(), 'business_interval_seconds': 2})]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); (root / p.CONFIG).parent.mkdir(parents=True); p.write(root / p.CONFIG, {**p.contract(), key: val})
                with patch.object(p, 'parents') as parent, self.assertRaisesRegex(ValueError, 'EXACT_RECOVERY'):
                    p.load_preparation(root)
                parent.assert_not_called()
        self.assertEqual(4, p.caps()['business_interval_seconds']); self.assertEqual(5400, p.caps()['max_business_requests'])
        self.assertEqual(100, p.contract()['max_segments']); self.assertIs(p.Guard, p.pilot.Guard)

    def test_CLI_has_no_force_retry_headed_rate_subset_or_error_resume(self):
        spec = importlib.util.spec_from_file_location('recovery_cli', ROOT / 'scripts/corporate_actions/collect_vsdc_recovery_ors_hold_v5.py')
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        for args in [['--force'], ['--retry'], ['--headed'], ['--interval', '2'], ['--batch', '11'], ['--check', '--pause']]:
            with patch('sys.argv', ['cli', *args]), patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit): cli.main()


class ParentIntegrityTests(unittest.TestCase):
    def check_mutation(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); previous = root / p.old.PREP; previous.mkdir(parents=True)
            p.write(previous / 'runtime.json', {}); p.write(previous / 'protected_old_files.json', {})
            state = root / p.RUN / 'state'; state.mkdir(parents=True)
            (state / 'public.txt').write_bytes(b'ORIGINAL_PUBLIC_EVIDENCE')
            p.write(state / 'manifest.json', {'artifact_type': p.old.TYPE,
                'files': {'public.txt': p.sha((state / 'public.txt').read_bytes())}})
            archive = state.parent / 'delta-vsdc-recovery4s.zip'; archive.write_bytes(b'PINNED_REVIEWED_ZIP_BYTES')
            digest = p.sha((state / 'manifest.json').read_bytes()); zip_digest = p.sha(archive.read_bytes())
            review = root / p.REVIEW; review.mkdir(parents=True)
            p.write(review / 'review.json', {'status': 'PASS_OFFLINE_REVIEW_OF_PARTIAL_V4_STOP_ORS_SOURCE_COUNT_GAP',
                'manifest_sha256': digest, 'ZIP_sha256': zip_digest, 'completed_original_selected_queries': 575})
            with patch.object(p, 'PARENTS', {}), patch.object(p.old, 'runtime', return_value={}), \
                    patch.object(p, 'RUN_DIGEST', digest), patch.object(p, 'ZIP_DIGEST', zip_digest):
                self.assertEqual(previous, p.parents(root))
                if mode == 'ZIP': archive.write_bytes(b'CHANGED')
                else: (state / 'public.txt').write_bytes(b'CHANGED')
                with self.assertRaises(Exception): p.parents(root)

    def test_changed_sealed_V4_ZIP_is_rejected_before_acquisition(self): self.check_mutation('ZIP')
    def test_changed_individual_V4_raw_file_is_rejected_at_preflight(self): self.check_mutation('raw')


if __name__ == '__main__': unittest.main()
