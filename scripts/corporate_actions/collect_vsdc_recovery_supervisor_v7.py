"""Supervisor V7 for the frozen V6 collector and its reviewed 616-query prefix."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions import vsdc_recovery_pausefix as collector
from delta_t1.ingestion.corporate_actions import vsdc_local_supervisor_v7 as supervisor

PREPARATION = 'data/corporate_actions/work/vsdc_supervisor_v7_preparation_20261104_v1'


def verify_runtime():
    manifest = collector.read(ROOT / PREPARATION / 'manifest.json')
    if manifest['artifact_type'] != 'vsdc-supervisor-v7-runtime-v1':
        raise ValueError('V7_RUNTIME_MANIFEST_REQUIRED')
    expected = set(collector.runtime(ROOT)) | {
        'scripts/corporate_actions/collect_vsdc_recovery_supervisor_v7.py',
        'src/delta_t1/ingestion/corporate_actions/vsdc_local_supervisor_v7.py',
    }
    if set(manifest['files']) != expected:
        raise ValueError('V7_RUNTIME_FILE_SET_MISMATCH')
    preparation = ROOT / collector.PREP / 'manifest.json'
    if collector.sha(preparation.read_bytes()) != manifest['collector_preparation_manifest_sha256']:
        raise ValueError('V6_PREPARATION_MANIFEST_CHANGED')
    for name, digest in manifest['files'].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or collector.sha(path.read_bytes()) != digest:
            raise ValueError('V7_RUNTIME_CHECKSUM_MISMATCH')


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--pause', action='store_true')
    args = parser.parse_args()
    try:
        verify_runtime()
        if args.pause:
            result = supervisor.request_pause(ROOT, collector)
        elif args.check:
            result = collector.run(ROOT, ROOT / collector.OUTPUT / 'offline-check/state', dry_run=True)
        else:
            print('Supervisor V7. Worker V6 chạy ẩn, Ctrl+C gửi yêu cầu pause.', flush=True)
            return supervisor.run(ROOT, collector, collector.WORKER)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] in {'PAUSE_REQUESTED', 'OFFLINE_CHECK_PASS'} else 2
    except (Exception, KeyboardInterrupt) as exc:
        print(json.dumps({'status': 'BLOCKED_REVIEW_REQUIRED', 'error_type': type(exc).__name__,
            'reason': collector.pilot.safe_reason(exc), 'instruction': 'Giữ output và lock để review.'},
            ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
