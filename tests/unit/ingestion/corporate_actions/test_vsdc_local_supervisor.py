import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from delta_t1.ingestion.corporate_actions import vsdc_local_supervisor as p
from delta_t1.ingestion.corporate_actions import vsdc_recovery_pausefix as recovery

ROOT = Path(__file__).resolve().parents[4]


class SupervisorTests(unittest.TestCase):
    def test_worker_options_hide_window_and_separate_process_group_and_console(self):
        options = p.isolated_options()
        self.assertTrue(options['creationflags'] & subprocess.CREATE_NEW_PROCESS_GROUP)
        self.assertTrue(options['creationflags'] & subprocess.CREATE_NO_WINDOW)
        self.assertEqual(subprocess.SW_HIDE, options['startupinfo'].wShowWindow)
        with patch.object(p.sys, 'platform', 'linux'), self.assertRaisesRegex(ValueError, 'WINDOWS'):
            p.isolated_options()

    def test_CtrlC_and_CtrlBreak_handlers_only_set_event_and_restore_previous(self):
        event = threading.Event(); previous = signal.getsignal(signal.SIGINT)
        with p.pause_handlers(event) as handler:
            handler(signal.SIGINT, None); self.assertTrue(event.is_set()); event.clear()
            handler(signal.SIGINT, None); self.assertTrue(event.is_set())
        self.assertIs(previous, signal.getsignal(signal.SIGINT))

    def test_repeated_parent_CtrlC_creates_marker_never_terminates_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp); event = threading.Event(); worker = MagicMock()
            worker.pid = 123; worker.stdout = io.StringIO('READY\nMORE\nDONE\n'); worker.wait.return_value = 0
            def line(value):
                if value in {'READY', 'MORE'}: event.set()
            popen = MagicMock(return_value=worker)
            result = p.supervise(['python', 'fixture'], run, event=event, popen=popen, on_line=line, emit=lambda *a, **k: None)
            self.assertEqual(0, result['returncode']); self.assertTrue(result['pause_requested'])
            self.assertTrue((run / 'PAUSE_REQUEST').exists()); worker.terminate.assert_not_called(); worker.kill.assert_not_called()
            self.assertEqual(subprocess.DEVNULL, popen.call_args.kwargs['stdin'])
            self.assertEqual(run.name, popen.call_args.kwargs['env']['DELTA_V6_SUPERVISOR_RUN'])
            events = [json.loads(x) for x in (run / 'supervisor_events.jsonl').read_text().splitlines()]
            self.assertEqual(1, sum(x['event'] == 'COOPERATIVE_PAUSE_REQUESTED' for x in events))

    def test_worker_crash_or_unsealed_exit_leaves_review_lock_not_auto_retry(self):
        for code in (3, 0):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); module = SimpleNamespace(OUTPUT='output')
                with patch.object(p, 'supervise', return_value={'returncode': code}), self.assertRaisesRegex(ValueError, 'UNSEALED_OR_CRASH'):
                    p.run(root, module, 'not-executed.py')
                self.assertTrue((root / 'output/active.lock').exists())

    def test_sealed_STOP_exits_without_retry_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); module = SimpleNamespace(OUTPUT='out', PAUSED=recovery.PAUSED, COMPLETE=recovery.COMPLETE,
                STOPPED=recovery.STOPPED, read=recovery.read, write=recovery.write, sha=recovery.sha)
            def stopped(command, folder, **kwargs):
                state = folder / 'state'; state.mkdir()
                recovery.write(state / 'manifest.json', {'fixture': True})
                recovery.write(state / 'result.json', {'status': recovery.STOPPED})
                (folder / 'delta-vsdc-recovery-pausefix.zip').write_bytes(b'SEALED_FIXTURE')
                return {'returncode': 2, 'worker_pid': 123, 'pause_requested': False}
            with patch.object(p, 'supervise', side_effect=stopped) as child:
                self.assertEqual(2, p.run(root, module, 'not-executed.py'))
            child.assert_called_once(); self.assertFalse((root / 'out/active.lock').exists())

    def test_internal_worker_cannot_be_invoked_without_supervisor(self):
        spec = importlib.util.spec_from_file_location('private_worker', ROOT / recovery.WORKER)
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        with patch('sys.argv', ['worker']), patch.object(recovery, 'run') as run, self.assertRaisesRegex(ValueError, 'PUBLIC_SUPERVISOR'):
            cli.main()
        run.assert_not_called()

    def test_browser_launch_disables_own_SIGINT_and_preserves_identity_TLS_options(self):
        from tests.unit.ingestion.corporate_actions import test_vsdc_shared_browser_pilot as fixture
        with tempfile.TemporaryDirectory() as tmp:
            _, api, manager, browser, guards = fixture.LifecycleTests().harness(tmp)
            with patch.dict('sys.modules', {'playwright.sync_api': api}):
                with recovery.HeadlessDriver(guards[0].config, guards[0]): pass
            kwargs = manager.chromium.launch.call_args.kwargs
            self.assertEqual({'channel','headless','handle_sigint','timeout'}, set(kwargs))
            self.assertFalse(kwargs['handle_sigint']); self.assertTrue(kwargs['headless'])
            self.assertEqual({'ignore_https_errors':False,'accept_downloads':False,'service_workers':'block'}, browser.new_context.call_args.kwargs)


@unittest.skipUnless(sys.platform == 'win32' and os.environ.get('DELTA_RUN_REAL_PAUSE_TEST') == '1',
    'Explicit isolated local about:blank test,never source acquisition')
class WindowsRealPauseTests(unittest.TestCase):
    def test_actual_hidden_test_console_CtrlC_keeps_Playwright_driver_alive_until_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / 'run-test'; harness = ROOT / 'tests/fixtures/corporate_actions/vsdc_pausefix_v6/windows_console_harness.py'
            startup = subprocess.STARTUPINFO(); startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow = subprocess.SW_HIDE
            env = dict(os.environ, DELTA_TEST_WORKER_PYTHON=sys.executable)
            result = subprocess.run([getattr(sys, '_base_executable', sys.executable), '-X', 'utf8', str(harness), str(run)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf8',
                timeout=45, creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=startup, env=env)
            self.assertEqual(0, result.returncode, result.stdout)
            report = json.loads((run / 'integration_result.json').read_text(encoding='utf8'))
            self.assertEqual('PASS_REAL_WINDOWS_CTRL_C_ISOLATION', report['status'])
            self.assertTrue(report['browser']['driver_alive_after_parent_CtrlC'])
            self.assertEqual(0, report['source_requests'])


if __name__ == '__main__': unittest.main()
