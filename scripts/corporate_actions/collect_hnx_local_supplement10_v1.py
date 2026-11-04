"""Thu bổ sung HNX local đúng 10 mã đã freeze; không gọi AI."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import run, seal, BASE, TYPE


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra offline, không TLS/network")
    parser.add_argument("--resume", type=Path, help="State mới đã seal và resumable=true; output mới")
    args = parser.parse_args()
    base = ROOT / BASE
    if not args.check and not args.resume and base.exists() and any(base.glob("run-*")):
        parser.error("Job đã có output. Review ZIP trước; chỉ --resume checkpoint đủ điều kiện, không tự chạy lại.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = base / ("run-" + stamp) / "state"
    result = run(ROOT, output, resume=args.resume, dry_run=args.check)
    if not args.check:
        archive = base / ("delta-hnx-local-supplement10-" + stamp + ".zip")
        seal(output, archive, artifact_type=TYPE)
        print("OUTPUT_STATE:", str(output))
        print("OUTPUT_ZIP:", str(archive))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"OFFLINE_CHECK_PASS", "FINISHED_BOUNDED_REVIEW_REQUIRED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
