"""Run or verify the CafeF full-statement remediation pilot."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.cafef_financial_detail import collect, validate_config, verify, detail_jobs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/data/cafef_financial_detail_v1.json")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify")
    args = p.parse_args()
    if args.verify:
        result = verify(ROOT / args.verify)
        print(json.dumps({"verification": "PASS", "coverage_status": result["coverage_status"]}))
        return 0
    c = validate_config(json.loads((ROOT / args.config).read_text(encoding="utf-8")))
    if args.dry_run:
        print(json.dumps({"network_requests": 0, "detail_jobs": len(detail_jobs(c)),
                          "document_jobs": len(c["symbols"]) * (c["end_year"] - c["start_year"] + 1)}))
        return 0
    run, result = collect(c, ROOT / "data/financial/cafef_detail_v1")
    verify(run)
    print(json.dumps({"run_directory": str(run), "execution_status": result["execution_status"],
                      "coverage_status": result["coverage_status"], "logical_requests": result["logical_requests"]}))
    return 0 if result["execution_status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
