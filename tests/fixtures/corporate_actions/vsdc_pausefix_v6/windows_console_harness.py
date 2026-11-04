"""Own hidden test console receives CTRL_C_EVENT;never target user's console."""
from pathlib import Path
import ctypes
import json
import os
import sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions import vsdc_local_supervisor as p

run = Path(sys.argv[1]); run.mkdir()
sent = False
def on_line(line):
    global sent
    if line == 'LOCAL_BROWSER_READY' and not sent:
        sent = True
        if not ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, 0):
            raise OSError('OWN_TEST_CONSOLE_CTRL_C_FAILED')

result = p.supervise([os.environ.get('DELTA_TEST_WORKER_PYTHON', sys.executable), '-X', 'utf8',
    str(Path(__file__).with_name('local_browser_worker.py')), str(run)], run, on_line=on_line)
browser_result = json.loads((run / 'local_browser_pause_result.json').read_text(encoding='utf8'))
assert sent and result['pause_requested'] and result['returncode'] == 0
assert browser_result['no_console'] and browser_result['driver_alive_after_parent_CtrlC']
(run / 'integration_result.json').write_text(json.dumps({'status': 'PASS_REAL_WINDOWS_CTRL_C_ISOLATION',
    'actual_CTRL_C_EVENT_sent_to_own_test_console': sent, 'supervisor': result,
    'browser': browser_result, 'source_requests': 0}), encoding='utf8')
print('PASS_REAL_WINDOWS_CTRL_C_ISOLATION', flush=True)
