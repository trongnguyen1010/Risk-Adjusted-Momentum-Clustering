"""User chạy local một lần: APP một GET bằng Chrome ẩn; không tiếp tục 54 batch."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions import vsdc_app_diagnostic as p


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'): stream.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Kiểm tra offline, không mở browser')
    args = parser.parse_args()
    base = ROOT / p.OUTPUT
    try:
        if (base / 'active.lock').exists(): raise ValueError('ACTIVE_OR_UNCLEAN_DIAGNOSTIC_LOCK')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        name = 'run-' + stamp; state = base / name / 'state'
        print('APP diagnostic: tối đa một GET, Chrome ẩn; không chạy tiếp 54 batch.', flush=True)
        if args.check:
            result = p.run(ROOT, state, dry_run=True)
        else:
            p.single_run_gate(ROOT)
            with p.prior.execution_lock(base, name):
                result = p.run(ROOT, state)
                archive = p.package(state)
                print('OUTPUT_STATE:', str(state)); print('OUTPUT_ZIP:', str(archive))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] in {'OFFLINE_CHECK_PASS', p.PASS} else 2
    except (Exception, KeyboardInterrupt) as exc:
        print(json.dumps({'status': 'BLOCKED_DIAGNOSTIC_REVIEW_REQUIRED', 'error_type': type(exc).__name__,
            'reason': p.safe_reason(exc),
            'instruction': 'Giữ output/lock; gửi thông báo và output để review.'}, ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__': raise SystemExit(main())
