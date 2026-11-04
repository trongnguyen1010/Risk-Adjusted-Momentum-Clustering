"""User chạy local một lần:Chrome ẩn,A32/AAA/IDJ,2s,tiến độ rõ vàlog mỗi trang/mã."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.corporate_actions import vsdc_headless_progress_pilot as p


def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Chỉ kiểm tra offline,không mở browser')
    args=parser.parse_args();config=p.read(ROOT/p.CONFIG);base=ROOT/config['output_base']
    if not args.check and base.exists() and any(base.glob('run-*')):
        parser.error('Đã có output;gửi ZIP review,không chạy lại/xóa output hoặc resume.')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');output=base/('run-'+stamp)/'state'
    print('Đang kiểm tra offline. Đây là pilot 3 mã; chưa chạy 54 batch.',flush=True)
    result=p.run(ROOT,output,dry_run=args.check)
    if not args.check:
        print('Đang đóng gói evidence và log tiến độ...',flush=True)
        archive=base/('delta-vsdc-headless-progress2s-'+stamp+'.zip');receipt=p.package(output,archive)
        print('OUTPUT_STATE:',str(output));print('OUTPUT_ZIP:',str(archive));print('OUTPUT_PACKAGING_TIMINGS:',str(receipt))
        print('OUTPUT_PROGRESS_LOG:',str(output/'progress.log'));print('OUTPUT_PROGRESS_JSONL:',str(output/'progress.jsonl'))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status'] in {'OFFLINE_CHECK_PASS',p.PASS} else 2


if __name__=='__main__':raise SystemExit(main())
