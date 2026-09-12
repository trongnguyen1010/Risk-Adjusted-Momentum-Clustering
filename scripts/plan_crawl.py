"""Check a real pilot before generating a large crawl plan; never downloads."""
import argparse
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.planning import pilot_report, plan_large_crawl
from delta_t1.io import read_json, write_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot_experiment")
    parser.add_argument("--config")
    args = parser.parse_args()
    output = ROOT / "data/plans" / ("plan-" + uuid.uuid4().hex[:12] + ".json")
    try:
        report = pilot_report(Path(args.pilot_experiment))
        result = plan_large_crawl(read_json(args.config), report) if args.config else report
        write_json(output, result)
        print(f"{report['status']}: {output}")
        raise SystemExit(0 if report["status"] == "PASS" else 2)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        write_json(output, dict(status="BLOCKED", error=str(exc)))
        print(f"BLOCKED: {output}")
        raise SystemExit(2)
