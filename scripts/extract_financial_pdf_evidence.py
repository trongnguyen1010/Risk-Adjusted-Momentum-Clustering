"""Extract offline PDF evidence using Poppler and installed Windows OCR."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.financial_pdf_evidence import extract_documents

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gap-run", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--max-pages", type=int, default=18, help="Bounded prefix per PDF, 1..30; use 2 for disclosure discovery")
    args = p.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "data"):
        raise ValueError("PDF evidence output must be under data")
    result = extract_documents(ROOT / args.gap_run, output, ROOT / "scripts/ocr_financial_pages.ps1", max_pages=args.max_pages)
    print(json.dumps({"output": str(output), "documents": len(result["documents"])}))
