"""Public supervisor V6:616đãđạt,456pending,ORS HOLD;Ctrl+C chỉ gửi pause."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions import vsdc_recovery_pausefix as p

def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, 'reconfigure'): s.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true'); group.add_argument('--pause', action='store_true')
    args = parser.parse_args()
    try:
        if args.pause: print(json.dumps(p.request_pause(ROOT), ensure_ascii=False, indent=2)); return 0
        if args.check:
            result = p.run(ROOT, ROOT / p.OUTPUT / 'offline-check/state', dry_run=True)
            print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['status'] == 'OFFLINE_CHECK_PASS' else 2
        print('V6 supervisor: worker chạy ẩn/tách console. Ctrl+C gửi pause; chờ OUTPUT_ZIP.', flush=True)
        return p.supervisor.run(ROOT, p, p.WORKER)
    except (Exception, KeyboardInterrupt) as exc:
        print(json.dumps({'status': 'BLOCKED_REVIEW_REQUIRED', 'error_type': type(exc).__name__,
            'reason': p.pilot.safe_reason(exc), 'instruction': 'Giữ output/lock,không chạy lại/xóa lock;gửi thông báo review.'}, ensure_ascii=False, indent=2)); return 2

if __name__ == '__main__': raise SystemExit(main())
