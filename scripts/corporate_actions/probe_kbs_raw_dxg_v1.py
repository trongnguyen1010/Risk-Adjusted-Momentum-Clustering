"""Chẩn đoán tối đa hai public KBS requests cho DXG; không cần API key."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.kbs_raw_probe import probe, verify_inputs, digest, seal_raw
from delta_t1.ingestion.corporate_actions.kbs_pilot import write_json


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra config/input offline")
    args = parser.parse_args()
    config_path = ROOT / "configs/data/corporate_actions/kbs_raw_dxg_probe_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = verify_inputs(ROOT, config)
    if args.check:
        print(json.dumps({"status": "OFFLINE_INPUT_CHECK_PASS", **inputs})); return 0
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    base = ROOT / "data/corporate_actions/work/kbs_raw_dxg_v1"
    output = base / ("run-" + stamp) / "state"
    output.mkdir(parents=True, exist_ok=False)
    archive = base / ("delta-kbs-raw-dxg-" + stamp + ".zip")
    write_json(output, "plan.json", config)
    write_json(output, "runtime.json", {"script_sha256": digest(Path(__file__).read_bytes()),
        "collector_sha256": digest((ROOT / "src/delta_t1/ingestion/corporate_actions/kbs_raw_probe.py").read_bytes()),
        "config_sha256": digest(config_path.read_bytes()), "api_key_used": False})
    execution = {"status": "STOPPED_LOCAL_ERROR"}
    try:
        result = probe(output, config, inputs)
        execution["status"] = result["status"]
    except KeyboardInterrupt:
        execution["status"] = "CANCELLED_BY_USER"
    except Exception as exc:
        execution["error_type"] = type(exc).__name__
    finally:
        seal_raw(output, archive, execution)
        print("STATUS:", execution["status"])
        print("OUTPUT_ZIP:", str(archive))
    return 0 if execution["status"] == "RAW_DIAGNOSTIC_READY_FOR_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
