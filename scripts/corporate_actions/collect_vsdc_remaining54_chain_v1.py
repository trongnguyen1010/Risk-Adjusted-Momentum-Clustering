"""User chạy local một lượt batch002–055; kiểm tra từng batch, dừng toàn chuỗi khi lỗi."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions.vsdc_remaining_chain import CONFIG, TYPE, read, run, seal


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'): stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Chỉ kiểm tra offline, không mở browser')
    args = parser.parse_args()
    config = read(ROOT / CONFIG)
    base = ROOT / config['output_base']
    if not args.check and base.exists() and any(base.glob('run-*')):
        parser.error('Chuỗi đã có output; gửi ZIP review, không chạy lại/xóa output hoặc resume.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = base / ('run-' + stamp) / 'state'
    result = run(ROOT, output, dry_run=args.check)
    if not args.check:
        archive = base / ('delta-vsdc-remaining54-chain-' + stamp + '.zip')
        seal(output, archive, artifact_type=TYPE)
        print('OUTPUT_STATE:', str(output))
        print('OUTPUT_BATCH_ZIPS:', str(output.parent / 'batch_zips'))
        print('OUTPUT_ZIP:', str(archive))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] in {
        'OFFLINE_CHECK_PASS', 'PASS_ALL_SELECTED_BATCHES_AUTOMATED_VALIDATION_REVIEW_REQUIRED'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
