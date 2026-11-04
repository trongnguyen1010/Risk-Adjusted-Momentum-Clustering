from contextlib import ExitStack
import io
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

from delta_t1.ingestion.corporate_actions import vsdc_local_supervisor_v7 as supervisor
from delta_t1.ingestion.corporate_actions import vsdc_recovery_pausefix as collector
from tests.unit.ingestion.corporate_actions import test_vsdc_recovery_pausefix as recovery_tests


class SupervisorV7Tests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows isolated worker regression')
    def test_real_hidden_child_process_uses_actual_worker_CLI_and_seals_first_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = recovery_tests.RecoveryTests().setup(tmp)
            helper = recovery_tests.ROOT / 'tests/fixtures/corporate_actions/vsdc_supervisor_v7/fixture_worker.py'
            with patch.dict(os.environ, {'DELTA_V7_TEST_PROJECT': str(root)}):
                result = supervisor.run(root, collector, helper, emit=lambda *args, **kwargs: None)
            self.assertEqual(0, result)
            run, = (root / collector.OUTPUT).glob('run-*')
            collector.verify_zip(run / 'state', run / 'delta-vsdc-recovery-pausefix.zip', collector.TYPE)
            self.assertEqual(collector.COMPLETE, collector.read(run / 'state/result.json')['status'])
            self.assertEqual(7, collector.read(run / 'supervisor_receipt.json')['supervisor_version'])

    def invoke(self, root, prep, pause=False):
        clock = recovery_tests.fixture.fixture.old.Clock()
        drivers = []

        def driver_factory(config, guard):
            driver = recovery_tests.fixture.Driver(config, guard, clock, None)
            drivers.append(driver)
            return driver

        def worker(command, folder, **kwargs):
            self.assertFalse(folder.exists())
            metadata = folder.parent / '.supervisors_v7' / folder.name
            metadata.mkdir(parents=True)
            (metadata / 'supervisor_events.jsonl').write_text('test-worker\n', encoding='utf8')
            token = collector.Pause(folder / 'PAUSE_REQUEST')
            if pause:
                metadata.joinpath('PAUSE_REQUEST').write_text('USER_REQUESTED_PAUSE\n', encoding='utf8')
            with patch.object(token, 'requested', return_value=pause):
                result = collector.run(root, folder / 'state', pause=token,
                    driver_factory=driver_factory, clock=clock.now, emit=lambda *args, **kwargs: None)
            collector.seal_run(folder / 'state')
            return {'returncode': 0, 'worker_pid': 123, 'pause_requested': pause}

        with ExitStack() as stack:
            stack.enter_context(patch.object(collector, 'load_preparation', return_value=(collector.contract(), prep)))
            stack.enter_context(patch.object(collector, 'runtime', return_value={'test_only': 'frozen'}))
            stack.enter_context(patch.object(collector.mbs.old, 'readiness', return_value={'ready': True}))
            stack.enter_context(patch.object(supervisor, 'supervise', side_effect=worker))
            result = supervisor.run(root, collector, collector.WORKER)
        return result, drivers

    def test_public_supervisor_worker_history_and_sealing_work_on_first_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = recovery_tests.RecoveryTests().setup(tmp)
            result, drivers = self.invoke(root, prep)
            self.assertEqual(0, result)
            self.assertEqual(['APP', 'APS', 'ARM'], [driver.config['ticker'] for driver in drivers])
            self.assertFalse((root / collector.OUTPUT / 'active.lock').exists())
            run, = (root / collector.OUTPUT).glob('run-*')
            receipt = collector.read(run / 'supervisor_receipt.json')
            self.assertEqual(7, receipt['supervisor_version'])
            self.assertEqual(collector.COMPLETE, receipt['status'])

    def test_resume_checks_previous_paused_run_and_excludes_current_uncreated_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = recovery_tests.RecoveryTests().setup(tmp)
            result, drivers = self.invoke(root, prep, pause=True)
            self.assertEqual(0, result)
            self.assertEqual([], drivers)
            result, drivers = self.invoke(root, prep)
            self.assertEqual(0, result)
            self.assertEqual(['APP', 'APS', 'ARM'], [driver.config['ticker'] for driver in drivers])

    def test_unsealed_previous_crash_still_blocks_before_any_driver(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, prep = recovery_tests.RecoveryTests().setup(tmp)
            (root / collector.OUTPUT / 'run-previous-crash/state').mkdir(parents=True)
            with self.assertRaises(FileNotFoundError):
                self.invoke(root, prep)
            self.assertTrue((root / collector.OUTPUT / 'active.lock').exists())

    def test_pause_during_preflight_does_not_create_run_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'out'
            name = 'run-20261104T000000000000Z'
            metadata = base / '.supervisors_v7' / name
            metadata.mkdir(parents=True)
            collector.write(base / 'active.lock', {'run': name, 'pid': 123})
            with patch.object(collector, 'OUTPUT', 'out'):
                self.assertEqual('PAUSE_REQUESTED', supervisor.request_pause(Path(tmp), collector)['status'])
            self.assertFalse((base / name).exists())
            self.assertTrue((metadata / 'PAUSE_REQUEST').exists())

    def test_early_CtrlC_is_forwarded_after_worker_creates_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / 'run-test'
            event = threading.Event()
            event.set()
            worker = MagicMock()
            worker.pid = 123
            worker.stdout = io.StringIO('PREFLIGHT\nCOPYING\nDONE\n')
            worker.wait.return_value = 0

            def on_line(line):
                if line == 'PREFLIGHT':
                    self.assertFalse(run.exists())
                    run.mkdir()
                if line == 'COPYING':
                    self.assertTrue((run / 'PAUSE_REQUEST').exists())

            result = supervisor.supervise(['fake-worker'], run, event=event,
                popen=MagicMock(return_value=worker), on_line=on_line, emit=lambda *args, **kwargs: None)
            self.assertTrue(result['pause_requested'])
            worker.kill.assert_not_called()
            worker.terminate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
