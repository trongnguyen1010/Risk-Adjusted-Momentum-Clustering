"""Index all embedded PDF text from verified document-vintage/supplement runs."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.financial_pdf_evidence import index_document_text

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True, action="append")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "data"):
        raise ValueError("text index output must be under data")
    result = index_document_text([ROOT / r for r in args.run], output)
    print(json.dumps({"documents": len(result["documents"]), "pages": sum(r["pages"] for r in result["documents"])}))
