"""Chẩn đoán riêng ORS bằng Chrome ẩn, tối đa năm request danh sách."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions import vsdc_ors_gap_diagnostic as diagnostic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Chỉ kiểm tra đầu vào offline')
    args = parser.parse_args()
    base = ROOT / diagnostic.OUTPUT
    name = datetime.now(timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ')
    state = base / name / 'state'
    if args.check:
        result = diagnostic.run(ROOT, state, dry_run=True)
    else:
        with diagnostic.collector.execution_lock(base, name):
            if any(base.glob('run-*')):
                print('DIAGNOSTIC_EXISTING_RUN_REVIEW_REQUIRED', flush=True)
                return 2
            result = diagnostic.run(ROOT, state)
            print('OUTPUT_ZIP:', diagnostic.package(state), flush=True)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0 if result['status'] in {'OFFLINE_CHECK_PASS', diagnostic.REVIEW_COMPLETE} else 2


if __name__ == '__main__':
    raise SystemExit(main())
