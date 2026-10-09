"""Collect only explicitly discovered issuer URLs from a bounded config."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.financial_supplement import collect

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    p.add_argument("--execute", action="store_true", required=True)
    args = p.parse_args()
    run, result = collect(json.loads((ROOT / args.config).read_bytes()), ROOT / "data/financial/issuer_supplement_v1")
    print(json.dumps({"output": str(run), "statuses": [r["status"] for r in result["requests"]]}))
