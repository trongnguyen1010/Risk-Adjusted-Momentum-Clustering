"""Pilot PVS local tối đa ba requests, không gọi AI; xuất ZIP để kiểm tra."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.hnx_local_pvs import run, seal


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"): stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra offline, không gửi request")
    args = parser.parse_args()
    config = json.loads((ROOT / "configs/data/corporate_actions/hnx_pvs_local_pilot_v1.json").read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    base = ROOT / "data/corporate_actions/work/hnx_pvs_local_pilot_v1"
    output = base / ("run-" + stamp) / "state"
    result = run(ROOT, output, config, dry_run=args.check)
    if args.check:
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    archive = base / ("delta-hnx-pvs-local-" + stamp + ".zip")
    seal(output, archive)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("OUTPUT_ZIP:", str(archive))
    return 0 if result["status"] == "PILOT_FINISHED_REVIEW_REQUIRED" else 2


if __name__ == "__main__": raise SystemExit(main())
