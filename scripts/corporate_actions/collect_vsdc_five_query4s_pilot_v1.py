"""User chạy local một lần:APP/APS/ARM/ART/ASG,đủ trang,Chrome ẩn,min4s."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions import vsdc_five_query4s_pilot as p


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'): stream.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Chỉ kiểm tra offline')
    args = parser.parse_args(); base = ROOT / p.OUTPUT
    try:
        if (base / 'active.lock').exists(): raise ValueError('PILOT_ACTIVE_OR_UNCLEAN_LOCK')
        name = 'run-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'); state = base / name / 'state'
        print('Pilot 5 mã đủ trang,min4s,Chrome ẩn;chưa chạy recovery1.058mã.', flush=True)
        if args.check: result = p.run(ROOT, state, dry_run=True)
        else:
            p.single_run_gate(ROOT)
            with p.prior.execution_lock(base, name):
                result = p.run(ROOT, state); archive = p.package(state)
                print('OUTPUT_STATE:', str(state)); print('OUTPUT_ZIP:', str(archive))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] in {'OFFLINE_CHECK_PASS', p.PASS} else 2
    except (Exception, KeyboardInterrupt) as exc:
        print(json.dumps({'status': 'BLOCKED_FIVE_QUERY4S_REVIEW_REQUIRED', 'error_type': type(exc).__name__,
            'reason': p.safe_reason(exc), 'instruction': 'Giữ output/lock,gửi thông báo để review.'}, ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__': raise SystemExit(main())
