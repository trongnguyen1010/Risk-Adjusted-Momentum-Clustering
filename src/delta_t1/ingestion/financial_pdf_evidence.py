"""Offline PDF text/OCR evidence. OCR is never a canonical financial fact."""
import json
import re
import subprocess
from pathlib import Path

from .cafef_financial import digest, encoded, immutable_write
from .financial_documents import verify_inventory


def validate_pdf(path, expected_sha):
    path = Path(path)
    body = path.read_bytes()
    if digest(body) != expected_sha or not body.startswith(b"%PDF"):
        raise ValueError("PDF source hash/signature mismatch")


def extract_documents(gap_run, output, ocr_script, max_pages=18):
    from pypdf import PdfReader
    gap = Path(gap_run).resolve()
    verify_inventory(gap)
    if type(max_pages) is not int or not 1 <= max_pages <= 30:
        raise ValueError("invalid OCR page cap")
    items = json.loads((gap / "inventory.json").read_bytes())["gaps"]
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    documents = []
    for item in items:
        if item["status"] != "DOWNLOADED":
            continue
        pdf = gap / item["path"]
        validate_pdf(pdf, item["sha256"])
        reader = PdfReader(pdf)
        if reader.is_encrypted:
            raise ValueError("encrypted PDF requires explicit handling")
        folder = output / pdf.stem
        folder.mkdir()
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            immutable_write(folder / f"page-{i+1:03d}.text.txt", text.encode("utf-8"))
            pages.append({"pdf_page": i+1, "embedded_text_characters": len(text), "ocr_planned": i < max_pages})
        count = min(max_pages, len(reader.pages))
        subprocess.run(["pdftoppm", "-f", "1", "-l", str(count), "-scale-to", "2200", "-png", str(pdf), str(folder / "page")], check=True, timeout=180)
        subprocess.run(["powershell.exe", "-NoProfile", "-File", str(Path(ocr_script).resolve()), "-ImageDirectory", str(folder)], check=True, timeout=300)
        for ocr_file in sorted(folder.glob("*.ocr.json")):
            record = json.loads(ocr_file.read_bytes())
            if digest(ocr_file.with_name(ocr_file.name.replace(".ocr.json", ".png")).read_bytes()) != record["image_sha256"]:
                raise ValueError("OCR image hash mismatch")
            page_number = int(re.search(r"page-(\d+)", ocr_file.name)[1])
            record.update(pdf_page=page_number, source_pdf_path=str(pdf), source_pdf_sha256=item["sha256"],
                          symbol=item["symbol"], year=item["year"], quarter=item["quarter"],
                          available_at=None, validation_status="OCR_REQUIRES_VISUAL_VERIFICATION")
            # Original OCR output remains immutable; enrichment is a separate record.
            immutable_write(ocr_file.with_name(ocr_file.name.replace(".ocr.json", ".evidence.json")), encoded(record))
        documents.append({"symbol": item["symbol"], "year": item["year"], "quarter": item["quarter"],
                          "path": str(pdf), "sha256": item["sha256"], "pages": pages,
                          "pages_ocr": count, "total_pages": len(reader.pages)})
        print(f"OCR {pdf.stem}: {count}/{len(reader.pages)} pages", flush=True)
    result = {"version": "financial-pdf-evidence-v1", "documents": documents,
              "scope": f"FIRST_{max_pages}_PAGES_PER_GAP_DOCUMENT", "max_pages": max_pages,
              "financial_features_allowed": False, "financial_pit_gate": "NOT_READY"}
    immutable_write(output / "index.json", encoded(result))
    immutable_write(output / "extractor.py", Path(__file__).read_bytes())
    immutable_write(output / "ocr_script.ps1", Path(ocr_script).read_bytes())
    immutable_write(output / "manifest.json", encoded({"files": {p.relative_to(output).as_posix(): digest(p.read_bytes())
                    for p in sorted(output.rglob("*")) if p.is_file()}}))
    return result


def index_document_text(runs, output):
    """Extract every embedded-text page; scans remain explicit, never blank-to-zero."""
    from pypdf import PdfReader
    records = []
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    sources = {}
    for run_path in runs:
        run = Path(run_path).resolve()
        verify_inventory(run)
        sources[str(run)] = digest((run / "manifest.json").read_bytes())
        inventory = json.loads((run / "inventory.json").read_bytes())
        for item in inventory.get("documents", inventory.get("requests", [])):
            if item["status"] not in {"DOWNLOADED", "REUSED_VERIFIED_RAW"} or item.get("kind") == "html":
                continue
            pdf = Path(item["path"])
            validate_pdf(pdf, item["sha256"])
            reader = PdfReader(pdf)
            folder = output / item["sha256"]
            counts = []
            for number, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                counts.append(len(text))
                file = folder / f"page-{number:03d}.txt"
                if not file.exists():
                    immutable_write(file, text.encode("utf-8"))
            records.append({"symbol": item["symbol"], "year": item["year"], "quarter": item.get("quarter", 0),
                            "pdf_path": str(pdf), "pdf_sha256": item["sha256"], "pages": len(reader.pages),
                            "embedded_text_page_characters": counts, "text_directory": str(folder),
                            "available_at": None, "financial_features_allowed": False})
    result = {"version": "financial-document-text-index-v1", "sources": sources, "documents": records,
              "financial_features_allowed": False, "financial_pit_gate": "NOT_READY"}
    immutable_write(output / "index.json", encoded(result))
    immutable_write(output / "extractor.py", Path(__file__).read_bytes())
    immutable_write(output / "manifest.json", encoded({"files": {p.relative_to(output).as_posix(): digest(p.read_bytes())
                    for p in sorted(output.rglob("*")) if p.is_file()}}))
    return result
