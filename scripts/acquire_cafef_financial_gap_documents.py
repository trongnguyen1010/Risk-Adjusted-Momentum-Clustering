"""Download a bounded PDF inspection sample from verified detail-pilot gaps."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.cafef_financial_detail import acquire_gap_documents

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--detail-run", required=True)
    p.add_argument("--execute", action="store_true", required=True)
    args = p.parse_args()
    output, inventory = acquire_gap_documents(ROOT / args.detail_run, ROOT / "data/financial/gap_documents_v1")
    print(json.dumps({"output": str(output), "documents_downloaded": sum(i["status"] == "DOWNLOADED" for i in inventory),
                      "gaps": len(inventory), "financial_pit_gate": "NOT_READY"}))
