"""Chạy/tiếp tục54batch Chromeẩn với tiến độ1.073mã;Ctrl+C hoặc --pause yêu cầu lưu checkpoint."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.corporate_actions import vsdc_headless_chain as p


def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf8')
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument('--check',action='store_true',help='Chỉ kiểm tra offline,không mởbrowser')
    group.add_argument('--pause',action='store_true',help='Yêu cầu lượt đang chạy tạm dừng từ terminal khác')
    args=parser.parse_args()
    try:
        if args.pause:print(json.dumps(p.request_pause(ROOT),ensure_ascii=False,indent=2));return 0
        base=ROOT/p.OUTPUT
        if (base/'active.lock').exists():raise ValueError('ACTIVE_OR_UNCLEAN_RUN:chờ lượt đang chạy hoặc gửi output review;không xóa lock')
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');name='run-'+stamp;output=base/name/'state'
        print('Đang kiểm tra offline và checkpoint. Chrome chạy ẩn;phạm vi54batch/1.073mã.',flush=True)
        if args.check:
            result=p.run(ROOT,output,dry_run=True);print(json.dumps(result,ensure_ascii=False,indent=2))
            return 0 if result['status']=='OFFLINE_CHECK_PASS' else 2
        pause=p.Pause(output.parent/'PAUSE_REQUEST')
        with p.execution_lock(base,name),p.pause_signals(pause):
            result=p.run(ROOT,output,pause=pause)
            print('Đang đóng gói checkpoint/evidence;chờ OUTPUT_ZIP trước khi đóng terminal...',flush=True)
            archive=p.seal_run(output)
            print('OUTPUT_STATE:',str(output));print('OUTPUT_ZIP:',str(archive))
            print('OUTPUT_PROGRESS_LOG:',str(output/'progress.log'));print('OUTPUT_PROGRESS_JSONL:',str(output/'progress.jsonl'))
            print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['status'] in {p.PAUSED,p.COMPLETE} else 2
    except (Exception,KeyboardInterrupt) as exc:
        print(json.dumps({'status':'BLOCKED_REVIEW_REQUIRED','reason':str(exc),
            'instruction':'Không xóa output/lock;gửi thông báo và output để review.'},ensure_ascii=False,indent=2));return 2


if __name__=='__main__':raise SystemExit(main())
