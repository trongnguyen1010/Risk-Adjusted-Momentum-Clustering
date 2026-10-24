"""FIN-PIT-2-R1 selective local OCR remediation.

The stage consumes immutable FIN-PIT-1 PDFs and FIN-PIT-2 candidates.  OCR is
page-scoped, derived, and fully provenanced; raw PDFs are never modified.  The
module creates candidates only and cannot write canonical financial rows or
financial features.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .financial_pit_semantic import (
    _assurance,
    _build_summary,
    _document_role,
    _fact_rows,
    _load_json,
    _load_jsonl,
    _page_statement_type,
    _period_from_candidate,
    _scope,
    canonical_bytes,
    evidence,
    evidence_complete,
    jsonl_bytes,
    parse_unit,
    sha256_file,
    validate_input_artifact,
)


STAGE = "FIN-PIT-2-R1"
ARTIFACT_VERSION = "fin-pit-2-r1-ocr-remediation-v1"
OCR_METHOD = "OCR_TESSERACT_5_4_0"
TARGET_DOCUMENT_COUNT = 26
MAX_PRIORITY_PAGES = 12
TEXT_PAGE_MIN_CHARS = 100
OCR_MIN_MEAN_CONFIDENCE = 45.0
OCR_MIN_TEXT_CHARS = 50
OCR_MIN_WORDS = 10
EXPECTED_TICKERS = {"FPT": "HOSE", "VNM": "HOSE", "PVS": "HNX", "ACV": "UPCOM"}
COMPANY_IDENTITY_TERMS = {
    "FPT": ("fpt",),
    "VNM": ("vinamilk", "sua viet nam"),
    "PVS": ("ptsc", "dich vu ky thuat dau khi"),
    "ACV": ("acv", "airports corporation of vietnam", "cang hang khong viet nam"),
}
FINAL_FILES = (
    "ocr_document_inventory.jsonl",
    "ocr_page_results.jsonl",
    "ocr_provenance.jsonl",
    "document_linkage_updated.jsonl",
    "report_candidates_updated.jsonl",
    "fact_candidates_updated.jsonl",
    "period_semantics_review.jsonl",
    "taxonomy_candidates_updated.jsonl",
    "revision_review_updated.jsonl",
    "conflicts.jsonl",
    "quarantine.jsonl",
    "semantic_coverage_before_after.json",
    "semantic_review_report.json",
    "manifest.json",
    "gate.json",
    "checksums.json",
)


def _write_new(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f"immutable output already exists: {path}")
    path.write_bytes(body)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_ocr_text(text: str) -> str:
    lines = []
    for line in unicodedata.normalize("NFKC", text or "").splitlines():
        value = " ".join(line.split())
        if value:
            lines.append(value)
    return "\n".join(lines)


def _find_binary(explicit: Path | None, names: tuple[str, ...], common: tuple[Path, ...]) -> Path:
    if explicit:
        path = explicit.resolve()
        if not path.is_file():
            raise ValueError(f"required binary not found: {path}")
        return path
    for name in names:
        found = shutil.which(name)
        if found:
            return Path(found).resolve()
    for path in common:
        if path.is_file():
            return path.resolve()
    raise ValueError(f"required binary not found: {names[0]}")


def resolve_engine(
    *,
    tesseract: Path | None = None,
    pdftoppm: Path | None = None,
    tessdata_dir: Path,
) -> dict:
    tess = _find_binary(
        tesseract,
        ("tesseract", "tesseract.exe"),
        (Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),),
    )
    poppler = _find_binary(pdftoppm, ("pdftoppm", "pdftoppm.exe"), ())
    tessdata = tessdata_dir.resolve()
    required_models = ("eng.traineddata", "vie.traineddata")
    missing = [name for name in required_models if not (tessdata / name).is_file()]
    if missing:
        raise ValueError(f"missing OCR language models: {missing}")
    version_run = subprocess.run(
        [str(tess), "--version"], capture_output=True, text=True, check=True, encoding="utf-8"
    )
    version = version_run.stdout.splitlines()[0].strip()
    model_hashes = {name: sha256_file(tessdata / name) for name in required_models}
    # The Windows Tesseract build cannot load traineddata through a path that
    # contains Vietnamese characters.  Materialize the exact hashed models in
    # a stable ASCII-only system-temp directory and verify every copy.
    bundle_id = hashlib.sha256(canonical_bytes(model_hashes)).hexdigest()[:16]
    runtime_tessdata = Path(tempfile.gettempdir()) / "delta-fin-pit-tessdata" / bundle_id
    runtime_tessdata.mkdir(parents=True, exist_ok=True)
    for name, expected in model_hashes.items():
        target = runtime_tessdata / name
        if not target.exists():
            shutil.copyfile(tessdata / name, target)
        if sha256_file(target) != expected:
            raise ValueError(f"runtime OCR model hash mismatch: {name}")
    config = {
        "engine": "Tesseract OCR",
        "version": version,
        "languages": "vie+eng",
        "tessdata_source_dir": str(tessdata),
        "tessdata_runtime_dir": str(runtime_tessdata),
        "model_sha256": model_hashes,
        "renderer": str(poppler),
        "dpi": 200,
        "oem": 1,
        "psm": 6,
        "preserve_interword_spaces": 1,
        "tessedit_create_tsv": 1,
        "priority_page_limit": MAX_PRIORITY_PAGES,
        "minimum_mean_word_confidence": OCR_MIN_MEAN_CONFIDENCE,
    }
    config_hash = hashlib.sha256(canonical_bytes(config)).hexdigest()
    return {
        "tesseract_path": tess,
        "pdftoppm_path": poppler,
        "tessdata_dir": runtime_tessdata,
        "engine": "Tesseract OCR",
        "version": version,
        "config": config,
        "config_hash": config_hash,
    }


def validate_fin_pit_2(input_dir: Path, fin_pit_1_dir: Path) -> dict:
    required = (
        "manifest.json", "gate.json", "checksums.json", "report_candidates.jsonl",
        "fact_candidates.jsonl", "document_linkage.jsonl", "timing_candidates.jsonl",
        "taxonomy_candidates.jsonl", "revision_review.jsonl", "quarantine.jsonl",
        "semantic_review_report.json",
    )
    missing = [name for name in required if not (input_dir / name).is_file()]
    if missing:
        raise ValueError(f"missing FIN-PIT-2 inputs: {missing}")
    manifest = _load_json(input_dir / "manifest.json")
    gate = _load_json(input_dir / "gate.json")
    if manifest.get("stage") != "FIN-PIT-2" or gate.get("status") != "PARTIAL":
        raise ValueError("FIN-PIT-2 PARTIAL artifact is required")
    if gate.get("canonical_rows_written") != 0 or gate.get("financial_features_written") != 0:
        raise ValueError("FIN-PIT-2 artifact violates stage boundary")
    if manifest.get("input_checksums_sha256") != sha256_file(fin_pit_1_dir / "checksums.json"):
        raise ValueError("FIN-PIT-2 is not bound to the supplied FIN-PIT-1 artifact")
    checksums = _load_json(input_dir / "checksums.json").get("files", {})
    for relative, expected in checksums.items():
        path = (input_dir / relative).resolve()
        if not path.is_relative_to(input_dir.resolve()) or not path.is_file():
            raise ValueError(f"invalid FIN-PIT-2 checksum path: {relative}")
        if sha256_file(path) != expected:
            raise ValueError(f"FIN-PIT-2 checksum mismatch: {relative}")
    return {"manifest": manifest, "gate": gate, "verified_files": len(checksums)}


def resolve_fin_pit_1(fin_pit_2_dir: Path, explicit: Path | None = None) -> Path:
    if explicit:
        return explicit.resolve()
    local = fin_pit_2_dir.parent / "fin-pit-1-source-document-pilot-v1"
    if local.is_dir():
        return local.resolve()
    manifest = _load_json(fin_pit_2_dir / "manifest.json")
    recorded = Path(manifest.get("input_artifact", ""))
    if recorded.is_dir():
        return recorded.resolve()
    raise ValueError("FIN-PIT-1 artifact not found; pass --fin-pit-1")


def _extract_text_pages(path: Path) -> tuple[list[str], list[int]]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    rotations = [int(page.get("/Rotate", 0) or 0) % 360 for page in reader.pages]
    return pages, rotations


def classify_preflight(pages: list[str] | None, error: str | None = None) -> str:
    if error is not None or pages is None or not pages:
        return "UNSUPPORTED_OR_CORRUPT"
    char_counts = [len(text.strip()) for text in pages]
    text_pages = sum(chars >= TEXT_PAGE_MIN_CHARS for chars in char_counts)
    total_chars = sum(char_counts)
    if text_pages == 0:
        return "SCAN_IMAGE_ONLY"
    if text_pages < len(pages):
        if total_chars >= 500 and text_pages / len(pages) >= 0.5:
            return "TEXT_BASED_USABLE"
        return "MIXED_TEXT_AND_SCAN"
    if total_chars >= 500 and text_pages >= 2:
        return "TEXT_BASED_USABLE"
    return "TEXT_BASED_LOW_QUALITY"


def select_ocr_pages(classification: str, pages: list[str]) -> tuple[list[int], str]:
    if classification not in {"SCAN_IMAGE_ONLY", "MIXED_TEXT_AND_SCAN"}:
        return [], "OCR_NOT_REQUIRED_BY_PREFLIGHT"
    candidate_pages = list(range(1, len(pages) + 1))
    if len(candidate_pages) > 5:
        candidate_pages = candidate_pages[:MAX_PRIORITY_PAGES]
        reason = "SEMANTIC_PRIORITY_WINDOW_FIRST_12_NO_RELIABLE_PAGE_INDEX"
    else:
        reason = "SHORT_DOCUMENT_ALL_PAGES"
    if classification == "MIXED_TEXT_AND_SCAN":
        candidate_pages = [page for page in candidate_pages if len(pages[page - 1].strip()) < TEXT_PAGE_MIN_CHARS]
        reason += "_SKIP_USABLE_TEXT_PAGES"
    return candidate_pages, reason


def build_inventory(fin_pit_1_dir: Path, fin_pit_2_dir: Path) -> tuple[list[dict], dict]:
    fin1 = validate_input_artifact(fin_pit_1_dir)
    fin2 = validate_fin_pit_2(fin_pit_2_dir, fin_pit_1_dir)
    document_rows = _load_jsonl(fin_pit_1_dir / "document_index.jsonl")
    report_rows = _load_jsonl(fin_pit_2_dir / "report_candidates.jsonl")
    report_by_hash = {row["document_hash"]: row for row in report_rows}
    source_by_hash: dict[str, list[dict]] = defaultdict(list)
    for row in document_rows:
        source_by_hash[row["sha256"]].append(row)
    inventory = []
    for digest, rows in sorted(source_by_hash.items()):
        source = rows[0]
        path = (fin_pit_1_dir / source["local_path"]).resolve()
        if not path.is_relative_to(fin_pit_1_dir.resolve()):
            raise ValueError(f"document path escapes input artifact: {source['local_path']}")
        before_hash = sha256_file(path)
        if before_hash != digest:
            raise ValueError(f"raw document hash mismatch: {digest}")
        error = None
        try:
            pages, rotations = _extract_text_pages(path)
        except Exception as exc:  # corrupt/unsupported is an inventory state
            pages, rotations, error = None, [], f"{type(exc).__name__}: {exc}"
        classification = classify_preflight(pages, error)
        report = report_by_hash[digest]
        is_target = report.get("document_role") == "UNKNOWN" and classification in {
            "SCAN_IMAGE_ONLY", "MIXED_TEXT_AND_SCAN"
        }
        selected, selection_reason = select_ocr_pages(classification, pages or []) if is_target else (
            [], "OUTSIDE_EXACT_UNKNOWN_ROLE_REMEDIATION_TARGET"
        )
        char_counts = [len(text.strip()) for text in (pages or [])]
        inventory.append({
            "document_hash": digest,
            "source_document_hash": digest,
            "source_document_path": source["local_path"],
            "absolute_source_path": str(path),
            "ticker": report["ticker"],
            "exchange": report["exchange"],
            "report_period_label": report["report_period_label"],
            "base_report_candidate_id": report["report_candidate_id"],
            "base_document_role": report["document_role"],
            "page_count": len(pages or []),
            "page_rotations": rotations,
            "text_char_count": sum(char_counts),
            "text_pages": sum(chars >= TEXT_PAGE_MIN_CHARS for chars in char_counts),
            "preflight_classification": classification,
            "preflight_error": error,
            "ocr_required": is_target,
            "selected_ocr_pages": selected,
            "page_selection_reason": selection_reason,
            "raw_hash_before": before_hash,
        })
    targets = [row for row in inventory if row["ocr_required"]]
    if len(targets) != TARGET_DOCUMENT_COUNT:
        raise ValueError(
            f"bounded remediation target changed: expected {TARGET_DOCUMENT_COUNT}, got {len(targets)}"
        )
    summary = {
        "documents_reviewed": len(inventory),
        "documents_ocr_required": len(targets),
        "ocr_pages_selected": sum(len(row["selected_ocr_pages"]) for row in targets),
        "classification_counts": dict(sorted(Counter(row["preflight_classification"] for row in inventory).items())),
        "fin_pit_1_verified_files": fin1["verified_files"],
        "fin_pit_2_verified_files": fin2["verified_files"],
    }
    return inventory, summary


def _reconstruct_tsv(tsv_text: str) -> tuple[str, list[dict], list[float]]:
    reader = csv.DictReader(tsv_text.splitlines(), delimiter="\t")
    lines: dict[tuple[int, int, int, int], list[str]] = defaultdict(list)
    regions: list[dict] = []
    confidences: list[float] = []
    for row in reader:
        word = (row.get("text") or "").strip()
        if not word:
            continue
        try:
            confidence = float(row.get("conf", "-1"))
        except ValueError:
            confidence = -1.0
        key = tuple(int(row.get(field, 0) or 0) for field in ("block_num", "par_num", "line_num", "page_num"))
        lines[key].append(word)
        region = {
            "text": word,
            "left": int(row.get("left", 0) or 0),
            "top": int(row.get("top", 0) or 0),
            "width": int(row.get("width", 0) or 0),
            "height": int(row.get("height", 0) or 0),
            "confidence": confidence if confidence >= 0 else "NOT_AVAILABLE",
        }
        regions.append(region)
        if confidence >= 0:
            confidences.append(confidence)
    raw_text = "\n".join(" ".join(lines[key]) for key in sorted(lines))
    return raw_text, regions, confidences


_SUSPICIOUS_NUMERIC = re.compile(r"(?i)(?:\d[\d.,()]*[oO][\d.,()]*|[oO][\d.,()]*\d)")


def numeric_ocr_safety(text: str) -> dict:
    suspicious = sorted(set(_SUSPICIOUS_NUMERIC.findall(text or "")))
    return {
        "parse_status": "UNRESOLVED" if suspicious else "NO_OBVIOUS_OCR_NUMERIC_AMBIGUITY",
        "suspicious_tokens": suspicious,
    }


def ocr_provenance_complete(row: dict) -> bool:
    return bool(
        row.get("document_hash")
        and isinstance(row.get("page"), int)
        and row["page"] >= 1
        and row.get("ocr_engine")
        and row.get("ocr_version")
        and row.get("ocr_config_hash")
        and row.get("raw_ocr_text") is not None
        and row.get("normalized_text_candidate") is not None
        and row.get("confidence") is not None
        and row.get("processing_status")
    )


def semantic_text_allowed(page_result: dict) -> bool:
    return page_result.get("processing_status") == "OCR_SUCCESS" and ocr_provenance_complete(page_result)


def timing_fields_preserved(before: dict, after: dict) -> bool:
    return all(after.get(field) == before.get(field) for field in (
        "publication_date", "eligible_from", "timing_grade",
        "timing_policy_version", "timing_evidence_source",
    ))


def _run_ocr_page(
    *,
    pdf_path: Path,
    document_hash: str,
    page_number: int,
    rotation: int,
    engine: dict,
    run_id: str,
) -> dict:
    # Tesseract 5.4 on Windows cannot reliably open image paths containing
    # non-ASCII workspace characters.  Keep ephemeral rendered pages in the
    # system temp directory; the directory is removed after each page.
    temp_root = (Path(tempfile.gettempdir()) / "delta-fin-pit-pdfs").resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fin-pit-2-r1-", dir=temp_root) as temp_name:
        temp_dir = Path(temp_name)
        prefix = temp_dir / "page"
        subprocess.run(
            [
                str(engine["pdftoppm_path"]), "-f", str(page_number), "-l", str(page_number),
                "-singlefile", "-r", "200", "-png", str(pdf_path), str(prefix),
            ],
            capture_output=True,
            check=True,
        )
        image_path = prefix.with_suffix(".png")
        if not image_path.is_file():
            raise ValueError(f"renderer did not create page image: {document_hash} page {page_number}")
        image_hash = sha256_file(image_path)
        command = [
            str(engine["tesseract_path"]), str(image_path), "stdout",
            "--tessdata-dir", str(engine["tessdata_dir"]),
            "-l", "vie+eng", "--oem", "1", "--psm", "6",
            "-c", "preserve_interword_spaces=1", "-c", "tessedit_create_tsv=1",
        ]
        completed = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"Tesseract failed for {document_hash} page {page_number}: "
                f"{completed.stderr.strip()}"
            )
    raw_text, regions, confidences = _reconstruct_tsv(completed.stdout)
    normalized = _normalize_ocr_text(raw_text)
    mean_confidence = round(statistics.fmean(confidences), 4) if confidences else "NOT_AVAILABLE"
    median_confidence = round(statistics.median(confidences), 4) if confidences else "NOT_AVAILABLE"
    orientation_valid = rotation in {0, 90, 180, 270}
    text_nonempty = len(normalized) >= OCR_MIN_TEXT_CHARS and len(regions) >= OCR_MIN_WORDS
    confidence_ok = isinstance(mean_confidence, float) and mean_confidence >= OCR_MIN_MEAN_CONFIDENCE
    status = "OCR_SUCCESS" if text_nonempty and confidence_ok and orientation_valid else "LOW_CONFIDENCE"
    numeric_safety = numeric_ocr_safety(normalized)
    result_id = f"ocr-page-{document_hash[:16]}-{page_number:04d}"
    return {
        "ocr_page_result_id": result_id,
        "document_hash": document_hash,
        "page": page_number,
        "ocr_engine": engine["engine"],
        "ocr_version": engine["version"],
        "ocr_config": engine["config"],
        "ocr_config_hash": engine["config_hash"],
        "language": "vie+eng",
        "run_id": run_id,
        "created_at": _utc_now(),
        "rendered_page_sha256": image_hash,
        "raw_ocr_text": raw_text,
        "normalized_text_candidate": normalized,
        "confidence": {
            "mean_word_confidence": mean_confidence,
            "median_word_confidence": median_confidence,
            "word_count": len(regions),
        },
        "bounding_boxes": regions,
        "page_rotation": rotation,
        "quality_checks": {
            "ocr_output_not_empty_or_truncated": text_nonempty,
            "page_orientation_valid": orientation_valid,
            "mean_confidence_at_least_threshold": confidence_ok,
            "numeric_text_plausibility": numeric_safety,
        },
        "processing_status": status,
    }


def _run_id(fin_pit_1_dir: Path, fin_pit_2_dir: Path, engine: dict) -> str:
    material = "|".join((
        sha256_file(fin_pit_1_dir / "checksums.json"),
        sha256_file(fin_pit_2_dir / "checksums.json"),
        engine["config_hash"],
    ))
    return "fin-pit-2-r1-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def dry_run(fin_pit_1_dir: Path, fin_pit_2_dir: Path, output_dir: Path, engine: dict) -> dict:
    inventory, summary = build_inventory(fin_pit_1_dir, fin_pit_2_dir)
    return {
        "stage": STAGE,
        "status": "DRY_RUN_PASS",
        "network_requests": 0,
        "output": str(output_dir),
        "ocr_engine": engine["engine"],
        "ocr_version": engine["version"],
        "ocr_config_hash": engine["config_hash"],
        **summary,
    }


def inventory_report(fin_pit_1_dir: Path, fin_pit_2_dir: Path) -> dict:
    inventory, summary = build_inventory(fin_pit_1_dir, fin_pit_2_dir)
    summary["by_ticker"] = {
        ticker: {
            "reviewed": sum(row["ticker"] == ticker for row in inventory),
            "ocr_required": sum(row["ticker"] == ticker and row["ocr_required"] for row in inventory),
            "ocr_pages": sum(
                len(row["selected_ocr_pages"]) for row in inventory if row["ticker"] == ticker
            ),
        }
        for ticker in EXPECTED_TICKERS
    }
    return {"stage": STAGE, "status": "INVENTORY_PASS", "network_requests": 0, **summary}


def execute_ocr(
    fin_pit_1_dir: Path,
    fin_pit_2_dir: Path,
    output_dir: Path,
    engine: dict,
    progress=None,
) -> dict:
    inventory, summary = build_inventory(fin_pit_1_dir, fin_pit_2_dir)
    if (output_dir / "manifest.json").exists():
        raise ValueError("final artifact already exists; use --verify-existing")
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = output_dir / "ocr_document_inventory.jsonl"
    if inventory_path.exists():
        existing = _load_jsonl(inventory_path)
        if canonical_bytes(existing) != canonical_bytes(inventory):
            raise ValueError("existing OCR inventory differs from immutable preflight")
    else:
        _write_new(inventory_path, jsonl_bytes(inventory))
    run_id = _run_id(fin_pit_1_dir, fin_pit_2_dir, engine)
    work_items = [
        (row, page)
        for row in inventory if row["ocr_required"]
        for page in row["selected_ocr_pages"]
    ]
    results: list[dict] = []
    for index, (row, page_number) in enumerate(work_items, 1):
        state_path = output_dir / "ocr_pages" / row["document_hash"] / f"page-{page_number:04d}.json"
        if state_path.exists():
            result = _load_json(state_path)
            if result.get("ocr_config_hash") != engine["config_hash"]:
                raise ValueError(f"OCR resume config mismatch: {state_path}")
        else:
            result = _run_ocr_page(
                pdf_path=Path(row["absolute_source_path"]),
                document_hash=row["document_hash"],
                page_number=page_number,
                rotation=row["page_rotations"][page_number - 1],
                engine=engine,
                run_id=run_id,
            )
            _write_new(state_path, canonical_bytes(result))
        results.append(result)
        if progress:
            progress(index, len(work_items), row, result)
    results.sort(key=lambda item: (item["document_hash"], item["page"]))
    page_results_path = output_dir / "ocr_page_results.jsonl"
    if page_results_path.exists():
        if canonical_bytes(_load_jsonl(page_results_path)) != canonical_bytes(results):
            raise ValueError("existing OCR aggregate differs from page state")
    else:
        _write_new(page_results_path, jsonl_bytes(results))
    provenance = [{
        "ocr_page_result_id": row["ocr_page_result_id"],
        "source_document_hash": row["document_hash"],
        "source_document_path": next(
            item["source_document_path"] for item in inventory
            if item["document_hash"] == row["document_hash"]
        ),
        "page": row["page"],
        "ocr_engine": row["ocr_engine"],
        "ocr_version": row["ocr_version"],
        "ocr_config_hash": row["ocr_config_hash"],
        "run_id": row["run_id"],
        "created_at": row["created_at"],
        "confidence": row["confidence"],
        "processing_status": row["processing_status"],
        "raw_pdf_immutable": True,
    } for row in results]
    provenance_path = output_dir / "ocr_provenance.jsonl"
    if provenance_path.exists():
        if canonical_bytes(_load_jsonl(provenance_path)) != canonical_bytes(provenance):
            raise ValueError("existing OCR provenance differs from page state")
    else:
        _write_new(provenance_path, jsonl_bytes(provenance))
    for row in inventory:
        if sha256_file(Path(row["absolute_source_path"])) != row["raw_hash_before"]:
            raise ValueError(f"raw PDF changed during OCR: {row['document_hash']}")
    return {
        "stage": STAGE,
        "status": "OCR_COMPLETE",
        "network_requests": 0,
        "run_id": run_id,
        "documents_reviewed": summary["documents_reviewed"],
        "documents_ocr_required": summary["documents_ocr_required"],
        "documents_ocr_processed": len({row["document_hash"] for row in results}),
        "ocr_pages": len(results),
        "ocr_pages_success": sum(row["processing_status"] == "OCR_SUCCESS" for row in results),
        "ocr_pages_low_confidence": sum(row["processing_status"] != "OCR_SUCCESS" for row in results),
        "output": str(output_dir),
    }


def _statement_evidence(pages: list[str], methods: list[str]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for number, text in enumerate(pages, 1):
        kind = _page_statement_type(text)
        if kind and kind not in found:
            found[kind] = evidence(number, "PAGE_TEXT", text[:700], methods[number - 1])
    return found


def _searchable_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char)).lower().split()
    )


def _document_quality_checks(
    *,
    ticker: str,
    report_period_label: str,
    pages: list[str],
    statement_evidence: dict[str, dict],
    unit: dict,
    selected_results: list[dict],
) -> dict:
    """Return explicit document-level OCR sanity checks without inventing confidence."""
    combined = _searchable_text("\n".join(pages))
    first_text = next((text.strip() for text in pages if len(text.strip()) >= 20), "")
    identity_terms = COMPANY_IDENTITY_TERMS.get(ticker, (ticker.lower(),))
    years = re.findall(r"(?:19|20)\d{2}", report_period_label or "")
    quarter_match = re.search(r"Q([1-4])", report_period_label or "", re.IGNORECASE)
    period_readable = bool(years and all(year in combined for year in years))
    if quarter_match:
        quarter = quarter_match.group(1)
        period_readable = period_readable and bool(
            re.search(rf"\bquy\s*{quarter}\b|\bquarter\s*{quarter}\b", combined)
        )
    numeric_lines = [
        line for page in pages for line in page.splitlines()
        if len(re.findall(r"[\d()]", line)) >= 4
    ]
    selected_success = [row for row in selected_results if row["processing_status"] == "OCR_SUCCESS"]
    numeric_checks = [
        row["quality_checks"]["numeric_text_plausibility"].get("parse_status")
        == "NO_OBVIOUS_OCR_NUMERIC_AMBIGUITY"
        for row in selected_success
    ]
    return {
        "title_readable": bool(first_text),
        "ticker_company_identity_consistent": any(term in combined for term in identity_terms),
        "period_labels_readable": period_readable,
        "unit_readable": unit["unit_status"] == "VERIFIED",
        "table_rows_non_empty": bool(statement_evidence and numeric_lines),
        "numeric_text_plausible": all(numeric_checks) if numeric_checks else False,
        "page_orientation_valid": all(
            row["quality_checks"]["page_orientation_valid"] for row in selected_results
        ) if selected_results else False,
        "ocr_output_not_empty_or_truncated": bool(selected_success),
    }


def _evidence_uses_page(value, page: int) -> bool:
    if isinstance(value, dict):
        if value.get("page") == page and value.get("extraction_method") == OCR_METHOD:
            return True
        return any(_evidence_uses_page(item, page) for item in value.values())
    if isinstance(value, list):
        return any(_evidence_uses_page(item, page) for item in value)
    return False


def _expected_scope(disclosure: str) -> str:
    if disclosure.endswith("-CONS"):
        return "CONSOLIDATED"
    if disclosure.endswith("-SEP"):
        return "SEPARATE"
    return "UNKNOWN"


def _quarantine_reason(report: dict) -> list[str]:
    reasons = []
    if report["document_role"] == "UNKNOWN":
        reasons.append("DOCUMENT_ROLE_UNKNOWN")
    if not report["period_start"] or not report["period_end"]:
        reasons.append("PERIOD_UNRESOLVED")
    if report["scope"] == "UNKNOWN":
        reasons.append("SCOPE_UNRESOLVED")
    if report["document_role"] == "PRIMARY_FINANCIAL_REPORT" and report["unit"]["unit_status"] != "VERIFIED":
        reasons.append("UNIT_UNRESOLVED")
    if report.get("ocr_status") == "LOW_CONFIDENCE":
        reasons.append("OCR_LOW_CONFIDENCE")
    return reasons or ["SEMANTIC_REQUIREMENTS_INCOMPLETE"]


def _coverage(reports: list[dict], facts: list[dict], links: list[dict], quarantines: list[dict]) -> dict:
    return {
        "documents_classified": sum(row["document_role"] != "UNKNOWN" for row in reports),
        "documents_unclassified": sum(row["document_role"] == "UNKNOWN" for row in reports),
        "linkage_verified": sum(row["linkage_status"] == "VERIFIED" for row in links),
        "linkage_ambiguous": sum(row["linkage_status"] == "AMBIGUOUS" for row in links),
        "linkage_conflict": sum(row["linkage_status"] == "CONFLICT" for row in links),
        "linkage_missing": sum(row["linkage_status"] == "MISSING" for row in links),
        "report_candidates": len(reports),
        "semantic_ready_reports": sum(bool(row["semantic_ready"]) for row in reports),
        "fact_candidates": len(facts),
        "semantic_ready_facts": sum(bool(row["semantic_ready"]) for row in facts),
        "period_verified": sum(bool(row["period_start"] and row["period_end"]) for row in reports),
        "period_unresolved": sum(not (row["period_start"] and row["period_end"]) for row in reports),
        "instant_verified": sum(row["duration_basis"] == "INSTANT" for row in facts),
        "standalone_verified": sum(row["duration_basis"] == "STANDALONE" for row in facts),
        "YTD_verified": sum(row["duration_basis"] == "YTD" for row in facts),
        "duration_unresolved": sum(row["duration_basis"] == "UNKNOWN" for row in facts),
        "scope_verified": sum(row["scope"] != "UNKNOWN" for row in reports),
        "scope_unknown": sum(row["scope"] == "UNKNOWN" for row in reports),
        "assurance_verified": sum(row["assurance"] != "UNKNOWN" for row in reports),
        "assurance_unknown": sum(row["assurance"] == "UNKNOWN" for row in reports),
        "unit_verified": sum(row["unit"]["unit_status"] == "VERIFIED" for row in reports),
        "unit_unresolved": sum(row["unit"]["unit_status"] != "VERIFIED" for row in reports),
        "quarantine_count": len(quarantines),
    }


def _coverage_slices(reports, facts, links, quarantines, field: str, values: list[str]) -> dict:
    result = {}
    report_by_id = {row["report_candidate_id"]: row for row in reports}
    for value in values:
        selected_reports = [row for row in reports if row[field] == value]
        ids = {row["report_candidate_id"] for row in selected_reports}
        selected_hashes = {row["document_hash"] for row in selected_reports}
        selected_facts = [row for row in facts if row["report_candidate_id"] in ids]
        selected_links = [row for row in links if row["document_hash"] in selected_hashes]
        selected_quarantine = [row for row in quarantines if row["report_candidate_id"] in ids]
        result[value] = _coverage(selected_reports, selected_facts, selected_links, selected_quarantine)
    return result


def semantic_reextract(fin_pit_1_dir: Path, fin_pit_2_dir: Path, output_dir: Path, engine: dict) -> dict:
    validate_input_artifact(fin_pit_1_dir)
    validate_fin_pit_2(fin_pit_2_dir, fin_pit_1_dir)
    for name in ("ocr_document_inventory.jsonl", "ocr_page_results.jsonl", "ocr_provenance.jsonl"):
        if not (output_dir / name).is_file():
            raise ValueError(f"OCR execution incomplete: missing {name}")
    if (output_dir / "manifest.json").exists():
        raise ValueError("semantic output already exists; use --verify-existing")
    inventory = _load_jsonl(output_dir / "ocr_document_inventory.jsonl")
    page_results = _load_jsonl(output_dir / "ocr_page_results.jsonl")
    result_by_page = {(row["document_hash"], row["page"]): row for row in page_results}
    inventory_by_hash = {row["document_hash"]: row for row in inventory}
    target_hashes = {row["document_hash"] for row in inventory if row["ocr_required"]}
    base_reports = _load_jsonl(fin_pit_2_dir / "report_candidates.jsonl")
    base_facts = _load_jsonl(fin_pit_2_dir / "fact_candidates.jsonl")
    base_links = _load_jsonl(fin_pit_2_dir / "document_linkage.jsonl")
    base_revisions = _load_jsonl(fin_pit_2_dir / "revision_review.jsonl")
    document_rows = _load_jsonl(fin_pit_1_dir / "document_index.jsonl")
    source_by_hash: dict[str, list[dict]] = defaultdict(list)
    for row in document_rows:
        source_by_hash[row["sha256"]].append(row)

    reports: list[dict] = []
    new_facts: list[dict] = []
    for base in base_reports:
        digest = base["document_hash"]
        if digest not in target_hashes:
            reports.append(base)
            continue
        inv = inventory_by_hash[digest]
        pdf_path = Path(inv["absolute_source_path"])
        text_pages, _ = _extract_text_pages(pdf_path)
        combined_pages: list[str] = []
        methods: list[str] = []
        successful_pages = 0
        low_confidence_pages = 0
        for number, text in enumerate(text_pages, 1):
            result = result_by_page.get((digest, number))
            if len(text.strip()) >= TEXT_PAGE_MIN_CHARS:
                combined_pages.append(text)
                methods.append("PDF_TEXT_LAYER")
            elif result and semantic_text_allowed(result):
                combined_pages.append(result["normalized_text_candidate"])
                methods.append(OCR_METHOD)
                successful_pages += 1
            else:
                combined_pages.append(text)
                methods.append("UNUSABLE_NO_SEMANTIC_PROMOTION")
                if result:
                    low_confidence_pages += 1
        filename = unquote(Path(urlsplit(source_by_hash[digest][0]["source_url"]).path).name)
        usable = any(method == OCR_METHOD for method in methods) or base["extraction"].get("text_layer_usable", False)
        role, role_evidence = _document_role(combined_pages, filename, usable, methods)
        scope, scope_evidence = _scope(combined_pages, methods)
        assurance, assurance_evidence = _assurance(combined_pages, methods)
        period_start, period_end, period_evidence = _period_from_candidate(
            base["report_period_label"], combined_pages, methods
        )
        statement_evidence = _statement_evidence(combined_pages, methods)
        unit = {"raw_unit": None, "normalized_unit": "unknown", "unit_multiplier": None, "unit_status": "UNKNOWN"}
        unit_evidence = None
        for number, text in enumerate(combined_pages, 1):
            parsed = parse_unit(text)
            if parsed["unit_status"] == "VERIFIED":
                unit = parsed
                unit_evidence = evidence(number, "PAGE_TEXT", text[:700], methods[number - 1])
                break
        selected_results = [
            result_by_page[(digest, page)] for page in inv["selected_ocr_pages"]
            if (digest, page) in result_by_page
        ]
        quality_checks = _document_quality_checks(
            ticker=base["ticker"],
            report_period_label=base["report_period_label"],
            pages=combined_pages,
            statement_evidence=statement_evidence,
            unit=unit,
            selected_results=selected_results,
        )
        quality_ok = all(quality_checks.values())
        report_semantic_ready = bool(
            role == "PRIMARY_FINANCIAL_REPORT"
            and statement_evidence
            and period_start
            and period_end
            and scope != "UNKNOWN"
            and unit["unit_status"] == "VERIFIED"
            and quality_ok
            and all(evidence_complete(item) for item in (role_evidence, period_evidence, scope_evidence, unit_evidence))
        )
        updated = dict(base)
        updated.update({
            "document_title": next((text.strip()[:500] for text in combined_pages if text.strip()), None),
            "document_role": role,
            "statement_types_present": sorted(statement_evidence),
            "period_start": period_start,
            "period_end": period_end,
            "scope": scope,
            "assurance": assurance,
            "semantic_ready": report_semantic_ready,
            "semantic_status": "VERIFIED_CANDIDATE" if report_semantic_ready else "UNRESOLVED",
            "evidence_locations": {
                "document_role": role_evidence,
                "statement_types": statement_evidence,
                "period": period_evidence,
                "scope": scope_evidence,
                "assurance": assurance_evidence,
                "unit": unit_evidence,
            },
            "unit": unit,
            "ocr_status": "SUCCESS" if quality_ok else "LOW_CONFIDENCE",
            "ocr_quality_checks": quality_checks,
            "ocr_success_pages": successful_pages,
            "ocr_low_confidence_pages": low_confidence_pages,
            "ocr_config_hash": engine["config_hash"],
            "extraction": {
                **base["extraction"],
                "ocr_used": True,
                "ocr_engine": engine["engine"],
                "ocr_version": engine["version"],
                "ocr_pages_selected": inv["selected_ocr_pages"],
                "ocr_pages_semantically_usable": successful_pages,
                "ocr_reason": inv["page_selection_reason"],
            },
        })
        reports.append(updated)
        if role == "PRIMARY_FINANCIAL_REPORT":
            new_facts.extend(_fact_rows(
                base["report_candidate_id"], base["ticker"], digest, combined_pages,
                base["report_period_label"], period_start, period_end, scope, assurance, methods,
            ))

    report_by_hash = {row["document_hash"]: row for row in reports}
    links = []
    for base in base_links:
        if base["document_hash"] not in target_hashes:
            links.append(base)
            continue
        report = report_by_hash[base["document_hash"]]
        expected = _expected_scope(base["source_disclosure"])
        if report["scope"] == "UNKNOWN" or report["document_role"] == "UNKNOWN" or expected == "UNKNOWN":
            status, reason = "AMBIGUOUS", "OCR_DOCUMENT_CONTENT_SEMANTICS_UNRESOLVED"
        elif report["scope"] != expected:
            status, reason = "CONFLICT", "OCR_DOCUMENT_SCOPE_CONFLICTS_WITH_DISCLOSURE_CANDIDATE"
        else:
            status, reason = "VERIFIED", "EXACT_OFFICIAL_ROUTE_AND_OCR_DOCUMENT_SCOPE_EVIDENCE_AGREE"
        updated = dict(base)
        updated.update({
            "document_title": report["document_title"],
            "period_evidence": report["evidence_locations"]["period"],
            "scope_evidence": report["evidence_locations"]["scope"],
            "linkage_status": status,
            "linkage_reason": reason,
        })
        links.append(updated)

    facts = [row for row in base_facts if row["document_hash"] not in target_hashes] + new_facts
    facts.sort(key=lambda row: row["fact_candidate_id"])
    reports.sort(key=lambda row: row["report_candidate_id"])
    links.sort(key=lambda row: row["candidate_linkage_id"])
    revisions = []
    for base in base_revisions:
        updated = dict(base)
        updated.update({
            "revision_relation": "UNKNOWN",
            "resolved": False,
            "ocr_review_status": "NO_OFFICIAL_DISCLOSURE_CORRECTION_RELATION_PROVEN",
        })
        revisions.append(updated)
    quarantines = [{
        "quarantine_id": "quarantine-" + row["document_hash"][:20],
        "report_candidate_id": row["report_candidate_id"],
        "document_hash": row["document_hash"],
        "ticker": row["ticker"],
        "reasons": _quarantine_reason(row),
        "semantic_ready": False,
    } for row in reports if not row["semantic_ready"]]
    conflicts = [{
        "conflict_id": "conflict-" + row["candidate_linkage_id"],
        "type": "DOCUMENT_SCOPE_CONFLICT",
        "document_hash": row["document_hash"],
        "source_disclosure": row["source_disclosure"],
        "resolution": "NONE_QUARANTINED",
    } for row in links if row["linkage_status"] == "CONFLICT"]
    taxonomy = [{
        "fact_candidate_id": row["fact_candidate_id"],
        "report_candidate_id": row["report_candidate_id"],
        "statement_type": row["statement_type"],
        "raw_label": row["raw_label"],
        "taxonomy_candidate": row["taxonomy_candidate"],
        "taxonomy_status": row["taxonomy_status"],
        "promotion_status": "NOT_FINAL_PROMOTED",
    } for row in facts]
    period_review = [{
        "report_candidate_id": row["report_candidate_id"],
        "ticker": row["ticker"],
        "document_hash": row["document_hash"],
        "period_start": row["period_start"],
        "period_end": row["period_end"],
        "period_evidence": row["evidence_locations"]["period"],
        "duration_counts": dict(sorted(Counter(
            fact["duration_basis"] for fact in facts
            if fact["report_candidate_id"] == row["report_candidate_id"]
        ).items())),
        "q2_q3_global_assumption_used": False,
        "semantic_status": row["semantic_status"],
    } for row in reports]

    base_quarantine = _load_jsonl(fin_pit_2_dir / "quarantine.jsonl")
    before = _coverage(base_reports, base_facts, base_links, base_quarantine)
    after = _coverage(reports, facts, links, quarantines)
    before_after = {
        "before_ocr": before,
        "after_ocr": after,
        "delta": {key: after[key] - before[key] for key in before},
        "by_ticker": {
            ticker: {
                "before": _coverage_slices(base_reports, base_facts, base_links, base_quarantine, "ticker", [ticker])[ticker],
                "after": _coverage_slices(reports, facts, links, quarantines, "ticker", [ticker])[ticker],
            }
            for ticker in EXPECTED_TICKERS
        },
        "by_exchange": {
            exchange: {
                "before": _coverage_slices(base_reports, base_facts, base_links, base_quarantine, "exchange", [exchange])[exchange],
                "after": _coverage_slices(reports, facts, links, quarantines, "exchange", [exchange])[exchange],
            }
            for exchange in ("HOSE", "HNX", "UPCOM")
        },
    }

    raw_immutable = all(
        sha256_file(Path(row["absolute_source_path"])) == row["raw_hash_before"] == row["document_hash"]
        for row in inventory
    )
    timing_preserved = all(
        timing_fields_preserved(base, updated)
        for base, updated in (
            (next(row for row in base_reports if row["report_candidate_id"] == updated["report_candidate_id"]), updated)
            for updated in reports
        )
    )
    provenance_complete = all(ocr_provenance_complete(row) for row in page_results)
    low_confidence_not_promoted = all(
        not _evidence_uses_page(report["evidence_locations"], page["page"])
        for page in page_results if page["processing_status"] != "OCR_SUCCESS"
        for report in reports if report["document_hash"] == page["document_hash"]
    )
    revision_unknown = all(row["revision_relation"] == "UNKNOWN" and not row["resolved"] for row in revisions)
    invariants_ok = all((raw_immutable, timing_preserved, provenance_complete, low_confidence_not_promoted, revision_unknown))
    improvements = (
        after["documents_classified"] > before["documents_classified"]
        or after["linkage_verified"] > before["linkage_verified"]
        or after["semantic_ready_reports"] > before["semantic_ready_reports"]
    )
    representative = all(
        any(row["ticker"] == ticker and row["semantic_ready"] for row in reports)
        for ticker in EXPECTED_TICKERS
    )
    if not invariants_ok:
        gate_status, gate_reason = "FAIL", "OCR_OR_STAGE_INVARIANT_VIOLATION"
    elif not improvements:
        gate_status, gate_reason = "BLOCKED", "OCR_DID_NOT_RESOLVE_DOCUMENT_SEMANTICS"
    elif representative and not quarantines:
        gate_status, gate_reason = "PASS", "BOUNDED_PILOT_OCR_SEMANTIC_REMEDIATION_COMPLETE"
    else:
        gate_status, gate_reason = "PARTIAL", "OCR_IMPROVED_COVERAGE_WITH_REMAINING_UNRESOLVED_SUBSET"
    gate = {
        "stage": STAGE,
        "status": gate_status,
        "reason": gate_reason,
        "network_request_count": 0,
        "ocr_reproducible": provenance_complete,
        "raw_pdfs_immutable": raw_immutable,
        "low_confidence_ocr_fail_closed": low_confidence_not_promoted,
        "q2_q3_global_assumption_used": False,
        "scope_merged": False,
        "revision_unknown_preserved": revision_unknown,
        "timing_preserved": timing_preserved,
        "canonical_rows_written": 0,
        "financial_features_written": 0,
        "financial_features_allowed": False,
    }
    summary = _build_summary(reports, facts, links, revisions, conflicts, quarantines)
    summary.update({
        "stage": STAGE,
        "ocr_engine": engine["engine"],
        "ocr_version": engine["version"],
        "ocr_documents": len({row["document_hash"] for row in page_results}),
        "ocr_pages": len(page_results),
        "ocr_pages_success": sum(row["processing_status"] == "OCR_SUCCESS" for row in page_results),
        "ocr_pages_low_confidence": sum(row["processing_status"] != "OCR_SUCCESS" for row in page_results),
        "coverage": before_after,
    })
    payloads = {
        "document_linkage_updated.jsonl": jsonl_bytes(links),
        "report_candidates_updated.jsonl": jsonl_bytes(reports),
        "fact_candidates_updated.jsonl": jsonl_bytes(facts),
        "period_semantics_review.jsonl": jsonl_bytes(period_review),
        "taxonomy_candidates_updated.jsonl": jsonl_bytes(taxonomy),
        "revision_review_updated.jsonl": jsonl_bytes(revisions),
        "conflicts.jsonl": jsonl_bytes(conflicts),
        "quarantine.jsonl": jsonl_bytes(quarantines),
        "semantic_coverage_before_after.json": canonical_bytes(before_after),
        "semantic_review_report.json": canonical_bytes(summary),
        "gate.json": canonical_bytes(gate),
    }
    for name, body in payloads.items():
        _write_new(output_dir / name, body)
    manifest = {
        "stage": STAGE,
        "artifact_version": ARTIFACT_VERSION,
        "run_id": _run_id(fin_pit_1_dir, fin_pit_2_dir, engine),
        "input_artifacts": {
            "fin_pit_1": str(fin_pit_1_dir),
            "fin_pit_1_manifest_sha256": sha256_file(fin_pit_1_dir / "manifest.json"),
            "fin_pit_1_checksums_sha256": sha256_file(fin_pit_1_dir / "checksums.json"),
            "fin_pit_2": str(fin_pit_2_dir),
            "fin_pit_2_manifest_sha256": sha256_file(fin_pit_2_dir / "manifest.json"),
            "fin_pit_2_checksums_sha256": sha256_file(fin_pit_2_dir / "checksums.json"),
        },
        "ocr_engine": engine["engine"],
        "ocr_version": engine["version"],
        "ocr_config": engine["config"],
        "ocr_config_hash": engine["config_hash"],
        "network_request_count": 0,
        "canonical_rows_written": 0,
        "financial_features_written": 0,
        "output_files": list(FINAL_FILES),
    }
    _write_new(output_dir / "manifest.json", canonical_bytes(manifest))
    checksums = {
        path.relative_to(output_dir).as_posix(): sha256_file(path)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "checksums.json"
    }
    _write_new(output_dir / "checksums.json", canonical_bytes({"algorithm": "sha256", "files": checksums}))
    return {
        "stage": STAGE,
        "status": gate_status,
        "reason": gate_reason,
        "network_requests": 0,
        "output": str(output_dir),
        "before": before,
        "after": after,
    }


def verify_existing(fin_pit_1_dir: Path, fin_pit_2_dir: Path, output_dir: Path) -> dict:
    validate_input_artifact(fin_pit_1_dir)
    validate_fin_pit_2(fin_pit_2_dir, fin_pit_1_dir)
    for name in FINAL_FILES:
        if not (output_dir / name).is_file():
            raise ValueError(f"missing FIN-PIT-2-R1 output: {name}")
    checksums = _load_json(output_dir / "checksums.json").get("files", {})
    for relative, expected in checksums.items():
        path = (output_dir / relative).resolve()
        if not path.is_relative_to(output_dir.resolve()) or not path.is_file():
            raise ValueError(f"invalid FIN-PIT-2-R1 checksum path: {relative}")
        if sha256_file(path) != expected:
            raise ValueError(f"FIN-PIT-2-R1 checksum mismatch: {relative}")
    manifest = _load_json(output_dir / "manifest.json")
    gate = _load_json(output_dir / "gate.json")
    if manifest["input_artifacts"]["fin_pit_1_checksums_sha256"] != sha256_file(fin_pit_1_dir / "checksums.json"):
        raise ValueError("FIN-PIT-1 binding mismatch")
    if manifest["input_artifacts"]["fin_pit_2_checksums_sha256"] != sha256_file(fin_pit_2_dir / "checksums.json"):
        raise ValueError("FIN-PIT-2 binding mismatch")
    if gate.get("canonical_rows_written") != 0 or gate.get("financial_features_written") != 0:
        raise ValueError("forbidden canonical/feature output detected")
    if gate.get("financial_features_allowed") is not False:
        raise ValueError("financial feature gate changed")
    inventory = _load_jsonl(output_dir / "ocr_document_inventory.jsonl")
    for row in inventory:
        if sha256_file(Path(row["absolute_source_path"])) != row["document_hash"]:
            raise ValueError(f"raw document changed: {row['document_hash']}")
    for path in output_dir.iterdir():
        if path.suffix == ".json":
            _load_json(path)
        elif path.suffix == ".jsonl":
            _load_jsonl(path)
    return {
        "stage": STAGE,
        "status": gate["status"],
        "network_requests": 0,
        "verified_file_count": len(checksums),
        "output": str(output_dir),
    }
