"""Export offline raw-candidate inventory and unresolved comparison evidence."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.financial_data_report import export

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--detail-run", required=True)
    p.add_argument("--summary-run", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "data"):
        raise ValueError("candidate financial exports must stay in local data/")
    result = export(ROOT / args.detail_run, ROOT / args.summary_run, output)
    print(json.dumps({"output": str(output), "comparison_counts": result["comparison_counts"],
                      "candidate_fields": len(result["field_inventory"]), "financial_features_allowed": False}))
