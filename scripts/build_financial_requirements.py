"""Produce an offline field/year checklist from existing immutable raw evidence."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.financial_requirements import export_requirements

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--detail-run", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "data"):
        raise ValueError("requirements output must be under data")
    result = export_requirements(ROOT / args.detail_run, ROOT / "configs/data/financial_evidence_policy_v1.json", output)
    print(json.dumps({"rows": len(result["rows"]), "statuses": dict(Counter(r["presence_status"] for r in result["rows"]))}))
