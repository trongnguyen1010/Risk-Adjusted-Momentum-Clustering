"""Collect bounded annual/report revision evidence for the verified four-symbol pilot."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.financial_documents import collect_vintages

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--detail-run", required=True)
    p.add_argument("--gap-run", required=True)
    p.add_argument("--policy", default="configs/data/financial_evidence_policy_v1.json")
    p.add_argument("--execute", action="store_true", required=True)
    args = p.parse_args()
    policy = json.loads((ROOT / args.policy).read_bytes())
    if policy.get("financial_features_allowed") is not False or policy.get("financial_pit_gate") != "NOT_READY":
        raise ValueError("acquisition policy cannot promote PIT")
    detail_config = json.loads((ROOT / args.detail_run / "config.json").read_bytes())
    if policy["symbols"] != detail_config["symbols"]:
        raise ValueError("policy must match verified pilot symbols")
    run, result = collect_vintages(ROOT / args.detail_run, ROOT / args.gap_run, ROOT / "data/financial/document_vintages_v1",
        start_year=policy["annual_document_start_year"], end_year=policy["annual_document_end_year"],
        max_downloads=policy["max_pdf_downloads"])
    print(json.dumps({"output": str(run), "status": result["execution_status"], "documents": len(result["documents"]),
                      "requests": result["logical_requests"]}))
