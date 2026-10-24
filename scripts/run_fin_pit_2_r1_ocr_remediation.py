"""Run FIN-PIT-2-R1 selective OCR remediation offline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from delta_t1.ingestion.financial_pit_ocr import (
    dry_run,
    execute_ocr,
    inventory_report,
    resolve_engine,
    resolve_fin_pit_1,
    semantic_reextract,
    verify_existing,
)


DEFAULT_FIN_PIT_2 = ROOT / "artifacts/financial_pit/fin-pit-2-semantic-extraction-v1"
DEFAULT_OUTPUT = ROOT / "artifacts/financial_pit/fin-pit-2-r1-ocr-remediation-v1"
DEFAULT_TESSDATA = ROOT / "tools/tessdata"


def _progress(index: int, total: int, inventory: dict, result: dict) -> None:
    print(
        json.dumps({
            "event": "OCR_PROGRESS",
            "completed": index,
            "total": total,
            "ticker": inventory["ticker"],
            "document_hash": inventory["document_hash"],
            "page": result["page"],
            "status": result["processing_status"],
        }, ensure_ascii=False, sort_keys=True),
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FIN-PIT-2-R1 selective local OCR remediation (zero acquisition network)"
    )
    parser.add_argument("--fin-pit-1", type=Path, help="FIN-PIT-1 artifact; defaults to FIN-PIT-2 recorded input")
    parser.add_argument("--fin-pit-2", type=Path, default=DEFAULT_FIN_PIT_2)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tesseract", type=Path)
    parser.add_argument("--pdftoppm", type=Path)
    parser.add_argument("--tessdata-dir", type=Path, default=DEFAULT_TESSDATA)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--inventory", action="store_true", help="read-only PDF preflight inventory")
    modes.add_argument("--dry-run", action="store_true", help="validate inputs/engine/page plan; write nothing")
    modes.add_argument("--ocr-execute", action="store_true", help="render and OCR only selected pages")
    modes.add_argument("--semantic-reextract", action="store_true", help="reuse FIN-PIT-2 semantics on OCR evidence")
    modes.add_argument("--execute", action="store_true", help="run OCR then semantic re-extraction")
    modes.add_argument("--resume", action="store_true", help="resume OCR/semantic work or verify final artifact")
    modes.add_argument("--verify-existing", action="store_true", help="offline checksums/contracts/raw hash verification")
    args = parser.parse_args(argv)

    fin_pit_2 = args.fin_pit_2.resolve()
    fin_pit_1 = resolve_fin_pit_1(fin_pit_2, args.fin_pit_1)
    output = args.output.resolve()

    if args.inventory:
        result = inventory_report(fin_pit_1, fin_pit_2)
    elif args.verify_existing or (args.resume and (output / "manifest.json").is_file()):
        result = verify_existing(fin_pit_1, fin_pit_2, output)
    else:
        engine = resolve_engine(
            tesseract=args.tesseract,
            pdftoppm=args.pdftoppm,
            tessdata_dir=args.tessdata_dir,
        )
        if args.dry_run:
            result = dry_run(fin_pit_1, fin_pit_2, output, engine)
        elif args.semantic_reextract:
            result = semantic_reextract(fin_pit_1, fin_pit_2, output, engine)
        elif args.ocr_execute:
            result = execute_ocr(fin_pit_1, fin_pit_2, output, engine, _progress)
        else:
            ocr_result = execute_ocr(fin_pit_1, fin_pit_2, output, engine, _progress)
            result = semantic_reextract(fin_pit_1, fin_pit_2, output, engine)
            result["ocr"] = ocr_result
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in {
        "PASS", "PARTIAL", "BLOCKED", "DRY_RUN_PASS", "INVENTORY_PASS", "OCR_COMPLETE"
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
