"""V7 supervises the frozen V6 collector without precreating its run directory."""
from contextlib import contextmanager
from pathlib import Path
import json
import os
import queue
import signal
import shutil
import subprocess
import sys
import threading
import time

from .vsdc_resumable_chain import execution_lock


def isolated_options():
    if sys.platform != 'win32': raise ValueError('WINDOWS_SUPERVISOR_REQUIRED')
    startup = subprocess.STARTUPINFO(); startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
        'startupinfo': startup}


@contextmanager
def pause_handlers(event):
    signals = [signal.SIGINT] + ([signal.SIGBREAK] if hasattr(signal, 'SIGBREAK') else [])
    previous = {s: signal.getsignal(s) for s in signals}
    def request(*args): event.set()
    for s in signals: signal.signal(s, request)
    try: yield request
    finally:
        for s, handler in previous.items(): signal.signal(s, handler)


def supervise(command, run, *, emit=print, event=None, popen=subprocess.Popen, on_line=None):
    """Never terminate/retry a worker on Ctrl+C; wait for its sealed result."""
    run = Path(run); event = event or threading.Event(); messages = queue.Queue()
    env = dict(os.environ, PYTHONUTF8='1', DELTA_V6_SUPERVISOR_RUN=run.name,
        DELTA_V6_SUPERVISOR_PID=str(os.getpid()))
    metadata = run.parent / '.supervisors_v7' / run.name
    metadata.mkdir(parents=True, exist_ok=True)
    marker = metadata / 'PAUSE_REQUEST'
    pause_announced = False
    worker = None
    def audit(name, **fields):
        with (metadata / 'supervisor_events.jsonl').open('a', encoding='utf8') as f:
            f.write(json.dumps({'event': name, **fields}, ensure_ascii=False)+'\n')
    with pause_handlers(event):
        options = isolated_options()
        worker = popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf8', errors='replace', bufsize=1, env=env, **options)
        audit('ISOLATED_WORKER_STARTED', pid=worker.pid, parent_pid=os.getpid(),
            new_process_group=True, no_console=True, hidden=True)
        def drain():
            try:
                for line in worker.stdout: messages.put(line.rstrip('\r\n'))
            finally: messages.put(None)
        thread = threading.Thread(target=drain, daemon=True); thread.start()
        try:
            while True:
                if event.is_set() or marker.exists() or (run / 'PAUSE_REQUEST').exists():
                    if not marker.exists():
                        try:
                            with marker.open('x', encoding='utf8') as f: f.write('USER_REQUESTED_PAUSE\n')
                        except FileExistsError: pass
                    if run.is_dir() and not (run / 'PAUSE_REQUEST').exists():
                        try:
                            with (run / 'PAUSE_REQUEST').open('x', encoding='utf8') as f:
                                f.write('USER_REQUESTED_PAUSE\n')
                        except FileExistsError:
                            pass
                    if not pause_announced:
                        audit('COOPERATIVE_PAUSE_REQUESTED')
                        emit('Đã yêu cầu pause. Chờ worker kiểm tra và lưu checkpoint/ZIP.', flush=True)
                        pause_announced = True
                try: line = messages.get(timeout=.2)
                except queue.Empty: continue
                if line is None: break
                emit(line, flush=True)
                if on_line: on_line(line)
            code = worker.wait(); thread.join(timeout=2)
            audit('WORKER_EXITED', returncode=code, pause_requested=pause_announced)
            return {'returncode': code, 'worker_pid': worker.pid, 'pause_requested': pause_announced,
                'worker_isolated_new_group_and_no_console': True}
        finally:
            # No force-kill in normal supervisor shutdown: an unhandled failure
            # leaves execution_lock for explicit review,never silent replay.
            if worker.stdout: worker.stdout.close()


def run(project, module, worker_script, *, emit=print):
    project = Path(project).resolve(); base = project / module.OUTPUT
    from datetime import datetime, timezone
    name = 'run-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if (base / 'active.lock').exists(): raise ValueError('ACTIVE_OR_UNCLEAN_RUN_REVIEW_REQUIRED')
    with execution_lock(base, name):
        folder = base / name
        if folder.exists():
            raise FileExistsError('REFUSE_EXISTING_RUN_DIRECTORY')
        result = supervise([sys.executable, '-X', 'utf8', str(project / worker_script), name], folder, emit=emit)
        state = folder / 'state'; archive = folder / 'delta-vsdc-recovery-pausefix.zip'
        if result['returncode'] not in {0, 2} or not (state / 'manifest.json').exists() or not archive.exists():
            raise ValueError('WORKER_UNSEALED_OR_CRASH_REVIEW_REQUIRED')
        status = module.read(state / 'result.json')['status']
        expected = {module.PAUSED, module.COMPLETE} if result['returncode'] == 0 else {module.STOPPED}
        if status not in expected: raise ValueError('WORKER_EXIT_STATUS_MISMATCH')
        metadata = base / '.supervisors_v7' / name
        shutil.copyfile(metadata / 'supervisor_events.jsonl', folder / 'supervisor_events.jsonl')
        module.write(folder / 'supervisor_receipt.json', {**result, 'status': status,
            'supervisor_version': 7, 'supervisor_metadata': metadata.relative_to(project).as_posix(),
            'state_manifest_sha256': module.sha((state / 'manifest.json').read_bytes()),
            'ZIP_sha256': module.sha(archive.read_bytes())})
        return result['returncode']


def request_pause(project, module):
    base = Path(project).resolve() / module.OUTPUT
    lock = module.read(base / 'active.lock')
    name = lock['run']
    if not isinstance(name, str) or not name.startswith('run-') or Path(name).name != name:
        raise ValueError('INVALID_ACTIVE_RUN')
    run = base / name
    if (run / 'state/manifest.json').exists():
        raise ValueError('NO_ACTIVE_UNSEALED_RUN')
    metadata = base / '.supervisors_v7' / name
    if not metadata.is_dir():
        raise ValueError('V7_SUPERVISOR_METADATA_REQUIRED')
    marker = metadata / 'PAUSE_REQUEST'
    try:
        with marker.open('x', encoding='utf8') as stream:
            stream.write('USER_REQUESTED_PAUSE\n')
    except FileExistsError:
        pass
    return {'status': 'PAUSE_REQUESTED', 'run': name, 'source_requests': 0, 'browser_launched': False}
