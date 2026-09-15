"""Create a read-only M1 or extended crawl plan from an approved pilot report."""
import argparse
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.planning import plan_extended_scale, plan_m1_scale
from delta_t1.io import read_json, write_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("representative_pilot_report")
    parser.add_argument("--config", required=True)
    parser.add_argument("--extended", action="store_true")
    args = parser.parse_args()
    output = ROOT / "data/plans" / ("plan-" + uuid.uuid4().hex[:12] + ".json")
    try:
        pilot = read_json(args.representative_pilot_report)
        planner = plan_extended_scale if args.extended else plan_m1_scale
        result = planner(read_json(args.config), pilot)
        write_json(output, result)
        print(f"{result['status']}: {output}")
        raise SystemExit(0 if result["status"] == "PLANNED" else 2)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        write_json(output, {"status": "BLOCKED", "gate": "PLAN", "error": str(exc)})
        print(f"BLOCKED: {output}")
        raise SystemExit(2)
