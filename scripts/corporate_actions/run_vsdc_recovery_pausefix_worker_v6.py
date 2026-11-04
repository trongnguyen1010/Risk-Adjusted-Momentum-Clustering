"""Internal isolated worker; use public collect_vsdc_recovery_pausefix_v6.py."""
import json
import os
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions import vsdc_recovery_pausefix as p

def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, 'reconfigure'): s.reconfigure(encoding='utf8')
    if len(sys.argv) != 2 or not re.fullmatch(r'run-\d{8}T\d{12}Z', sys.argv[1]): raise ValueError('PUBLIC_SUPERVISOR_REQUIRED')
    name = sys.argv[1]; base = ROOT / p.OUTPUT; lock = p.read(base / 'active.lock')
    if (os.environ.get('DELTA_V6_SUPERVISOR_RUN') != name or lock['run'] != name
            or str(lock['pid']) != os.environ.get('DELTA_V6_SUPERVISOR_PID')): raise ValueError('PUBLIC_SUPERVISOR_REQUIRED')
    folder = base / name; state = folder / 'state'
    result = p.run(ROOT, state, pause=p.Pause(folder / 'PAUSE_REQUEST'))
    print('Đang đóng gói checkpoint; chờ OUTPUT_ZIP...', flush=True)
    archive = p.seal_run(state)
    print('OUTPUT_STATE:', state); print('OUTPUT_ZIP:', archive)
    print('OUTPUT_PROGRESS_LOG:', state / 'progress.log')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] in {p.PAUSED, p.COMPLETE} else 2

if __name__ == '__main__': raise SystemExit(main())
