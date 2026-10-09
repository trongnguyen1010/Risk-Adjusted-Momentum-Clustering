"""Run or verify the raw-only CafeF financial coverage pilot."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.cafef_financial import collect, validate_config, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/data/cafef_financial_pilot_v1.json")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", metavar="RUN_DIRECTORY")
    args = parser.parse_args()
    if args.verify:
        result = verify(ROOT / args.verify)
        print(json.dumps({"verification": "PASS", "coverage_status": result["coverage_status"],
                          "financial_pit_gate": result["financial_pit_gate"]}, indent=2))
        return 0
    config = validate_config(json.loads((ROOT / args.config).read_text(encoding="utf-8")))
    if args.dry_run:
        print(json.dumps({"readiness": "PASS", "network_requests": 0, "config": config}, indent=2))
        return 0
    run, result = collect(config, ROOT / "data/financial/cafef_raw_pilot_v1")
    verify(run)
    print(json.dumps({"run_directory": str(run), "execution_status": result["execution_status"],
                      "coverage_status": result["coverage_status"],
                      "logical_requests": result["logical_requests"],
                      "financial_pit_gate": result["financial_pit_gate"]}, indent=2))
    return 0 if result["execution_status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
