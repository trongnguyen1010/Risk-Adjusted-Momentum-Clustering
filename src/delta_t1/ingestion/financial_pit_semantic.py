"""FIN-PIT-2 offline document linkage and semantic candidate extraction.

This module deliberately produces candidates, never canonical financial rows.
It preserves FIN-PIT-1 timing fields and fails closed when a PDF has no usable
text layer. OCR is an explicit, separately-provenanced operation and is not
silently substituted here.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit


STAGE = "FIN-PIT-2"
ARTIFACT_VERSION = "fin-pit-2-semantic-extraction-v1"
EXPECTED_TICKERS = {"FPT": "HOSE", "VNM": "HOSE", "PVS": "HNX", "ACV": "UPCOM"}
OUTPUT_FILES = (
    "report_candidates.jsonl",
    "fact_candidates.jsonl",
    "document_linkage.jsonl",
    "timing_candidates.jsonl",
    "taxonomy_candidates.jsonl",
    "revision_review.jsonl",
    "conflicts.jsonl",
    "quarantine.jsonl",
    "semantic_review_report.json",
    "manifest.json",
    "gate.json",
)


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _ascii(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    folded = "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()
    folded = folded.replace("đ", "d")
    return " ".join(folded.split())


def evidence(page: int, region: str, source_text: str, method: str = "PDF_TEXT_LAYER") -> dict:
    return {
        "page": page,
        "region": region,
        "source_text": source_text[:1000],
        "extraction_method": method,
    }


def evidence_complete(item: dict | None) -> bool:
    return bool(
        item
        and isinstance(item.get("page"), int)
        and item["page"] >= 1
        and item.get("region")
        and item.get("source_text")
        and item.get("extraction_method")
    )


def classify_duration(statement_type: str, source_text: str) -> str:
    """Classify only from statement-local wording, never from quarter number."""
    text = _ascii(source_text)
    if statement_type == "BALANCE_SHEET":
        return "INSTANT" if re.search(
            r"(tai\W*ngay|as of|ngay\s+(?:31|30|01|1)\s+thang)", text
        ) else "UNKNOWN"
    if re.search(r"\b(3|ba) thang (ket thuc|ended)\b|\b3 months? ended\b", text):
        return "STANDALONE"
    if re.search(r"\b(6|sau) thang (ket thuc|dau nam|ended)\b|\b6 months? ended\b", text):
        return "YTD"
    if re.search(r"\b(9|chin) thang (ket thuc|dau nam|ended)\b|\b9 months? ended\b", text):
        return "YTD"
    if re.search(r"(nam tai chinh ket thuc|year ended|for the year ended)", text):
        return "FULL_YEAR"
    return "UNKNOWN"


def classify_column_role(label: str) -> str:
    text = _ascii(label)
    if any(marker in text for marker in ("opening", "dau nam", "01/01", "1/1/")):
        return "OPENING_BALANCE"
    if any(marker in text for marker in ("closing", "cuoi nam", "31/12", "30/06", "30/09", "31/03")):
        return "CLOSING_BALANCE"
    if any(marker in text for marker in ("prior year", "previous year", "nam truoc", "trinh bay lai")):
        return "PRIOR_YEAR_COMPARATIVE"
    if any(marker in text for marker in ("prior period", "ky truoc", "cung ky")):
        return "PRIOR_PERIOD"
    if any(marker in text for marker in ("current", "ky nay", "nam nay")):
        return "CURRENT_PERIOD"
    return "UNKNOWN"


def parse_unit(source_text: str) -> dict:
    text = _ascii(source_text)
    patterns = (
        (r"(don vi(?: tinh)?|unit)\s*:?\s*(ty dong|billion vnd)", "billion VND", 1_000_000_000),
        (r"(don vi(?: tinh)?|unit)\s*:?\s*(trieu dong|million vnd)", "million VND", 1_000_000),
        (r"(don vi(?: tinh)?|unit)\s*:?\s*(nghin dong|thousand vnd)", "thousand VND", 1_000),
        (r"\b(vnd|dong)\b", "VND", 1),
        (r"(co phieu|shares?)", "shares", 1),
        (r"(%|phan tram|percentage)", "percentage", 0.01),
    )
    for pattern, unit, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            return {
                "raw_unit": match.group(0),
                "normalized_unit": unit,
                "unit_multiplier": multiplier,
                "unit_status": "VERIFIED",
            }
    return {"raw_unit": None, "normalized_unit": "unknown", "unit_multiplier": None, "unit_status": "UNKNOWN"}


def parse_numeric_candidate(raw: str) -> dict:
    text = (raw or "").strip()
    compact = text.replace(" ", "")
    parenthetical = compact.startswith("(") and compact.endswith(")")
    core = compact[1:-1] if parenthetical else compact
    if not core or not re.fullmatch(r"[0-9][0-9.,]*", core):
        return {
            "raw_value": text,
            "raw_sign": "UNKNOWN",
            "normalized_numeric_candidate": None,
            "parse_status": "UNRESOLVED",
        }
    groups = re.split(r"[.,]", core)
    if len(groups) > 1 and all(len(group) == 3 for group in groups[1:]):
        value = int("".join(groups))
    elif len(groups) == 2 and len(groups[1]) <= 2:
        value = float(groups[0] + "." + groups[1])
    else:
        value = int("".join(groups))
    return {
        "raw_value": text,
        "raw_sign": "PARENTHETICAL" if parenthetical else "UNMARKED",
        "normalized_numeric_candidate": -value if parenthetical else value,
        "parse_status": "VERIFIED",
    }


def taxonomy_candidate(item_code: str | None, raw_label: str, statement_type: str) -> dict:
    """Return a non-promoted candidate; labels alone never become canonical codes."""
    if item_code:
        return {
            "taxonomy_candidate": {
                "provider_item_code": item_code,
                "statement_type": statement_type,
                "raw_label": raw_label,
            },
            "taxonomy_status": "CANDIDATE_EXACT_CODE_CONTEXT",
        }
    return {"taxonomy_candidate": None, "taxonomy_status": "UNRESOLVED"}


def review_revision_group(group: dict, documents: dict[str, dict]) -> dict:
    rows = [documents[item] for item in group.get("document_candidate_ids", []) if item in documents]
    roles = {row.get("document_role", "UNKNOWN") for row in rows}
    classification = "UNKNOWN"
    if rows and roles <= {"PRIMARY_FINANCIAL_REPORT", "EXPLANATORY_NOTE", "OTHER", "UNKNOWN"} and len(roles) > 1:
        classification = "SAME_REPORT_MULTIPLE_ATTACHMENTS"
    elif len({row.get("document_hash") for row in rows}) > 1:
        classification = "POSSIBLE_REVISION"
    return {
        "revision_group_id": "revision-" + hashlib.sha256(canonical_bytes(group)).hexdigest()[:16],
        "ticker": group.get("ticker"),
        "report_period_candidate": group.get("period_candidate"),
        "document_hashes": sorted({row.get("document_hash") for row in rows if row.get("document_hash")}),
        "document_roles": sorted(roles),
        "classification": classification,
        "official_correction_evidence": False,
        "revision_relation": "UNKNOWN",
        "resolved": False,
        "reason": "NO_OFFICIAL_CORRECTION_RESTATEMENT_OR_REPLACEMENT_EVIDENCE",
    }


def _extract_pdf(path: Path) -> tuple[list[str], dict]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("pypdf is required for FIN-PIT-2 text-layer extraction") from exc
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    chars = sum(len(text.strip()) for text in pages)
    nonempty = sum(bool(text.strip()) for text in pages)
    return pages, {
        "page_count": len(pages),
        "text_char_count": chars,
        "text_pages": nonempty,
        "text_layer_usable": chars >= 500 and nonempty >= 2,
        "ocr_used": False,
        "ocr_engine": None,
        "ocr_version": None,
        "ocr_reason": "OCR_ENGINE_UNAVAILABLE_NOT_RUN" if chars < 500 or nonempty < 2 else None,
    }


def _page_statement_type(text: str) -> str | None:
    value = _ascii(text)
    if "bang can" in value or "balance sheet" in value:
        return "BALANCE_SHEET"
    if "ket qua ho" in value or "income statement" in value or "statement of income" in value:
        return "INCOME_STATEMENT"
    if re.search(r"lu\W*u chuyen tien", value) or "cash flow" in value:
        return "CASH_FLOW_STATEMENT"
    if "thuyet minh bao cao" in value or "notes to" in value:
        return "NOTES"
    if "bao cao kiem toan" in value or "independent auditor" in value:
        return "AUDITOR_REPORT"
    return None


def _page_method(page_methods: list[str] | None, page_number: int) -> str:
    if page_methods and page_number <= len(page_methods):
        return page_methods[page_number - 1]
    return "PDF_TEXT_LAYER"


def _document_role(
    pages: list[str], filename: str, usable: bool, page_methods: list[str] | None = None
) -> tuple[str, dict | None]:
    for number, text in enumerate(pages, 1):
        statement = _page_statement_type(text)
        if statement in {"BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT"}:
            return "PRIMARY_FINANCIAL_REPORT", evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
    if usable:
        combined = _ascii("\n".join(pages[:5]))
        if "giai trinh" in combined or "explanation" in combined:
            return "EXPLANATORY_NOTE", evidence(
                1, "PAGE_TEXT", pages[0][:700], _page_method(page_methods, 1)
            )
        if "bao cao kiem toan" in combined or "independent auditor" in combined:
            return "AUDITOR_REVIEW_REPORT", evidence(
                1, "PAGE_TEXT", pages[0][:700], _page_method(page_methods, 1)
            )
        return "OTHER", evidence(1, "PAGE_TEXT", pages[0][:700], _page_method(page_methods, 1))
    # Filename remains provenance, but cannot verify the role by itself.
    return "UNKNOWN", None


def _scope(pages: list[str], page_methods: list[str] | None = None) -> tuple[str, dict | None]:
    for number, text in enumerate(pages[:15], 1):
        value = _ascii(text)
        has_consolidated = "hop nhat" in value or "consolidated" in value
        has_separate = "bao cao tai chinh rieng" in value or "separate financial" in value or "cong ty me" in value
        if has_consolidated and not has_separate:
            return "CONSOLIDATED", evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
        if has_separate and not has_consolidated:
            return "SEPARATE", evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
    return "UNKNOWN", None


def _assurance(pages: list[str], page_methods: list[str] | None = None) -> tuple[str, dict | None]:
    for number, text in enumerate(pages[:15], 1):
        value = _ascii(text)
        if "bao cao soat xet" in value or "review report" in value:
            return "REVIEWED", evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
        if "chua duoc kiem toan" in value or "unaudited" in value:
            return "UNAUDITED", evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
        if "bao cao kiem toan doc lap" in value or "independent auditor" in value:
            return "AUDITED", evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
    return "UNKNOWN", None


def _period_from_candidate(
    period: str, pages: list[str], page_methods: list[str] | None = None
) -> tuple[str | None, str | None, dict | None]:
    year_match = re.match(r"(\d{4})(Q[1-4]|FY)$", period or "")
    if not year_match:
        return None, None, None
    year, kind = int(year_match.group(1)), year_match.group(2)
    for number, text in enumerate(pages[:20], 1):
        value = _ascii(text)
        if kind == "FY" and str(year) in value and (
            "31 thang 12" in value or "31 december" in value or "year ended" in value
        ):
            return f"{year}-01-01", f"{year}-12-31", evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
        quarter_dates = {
            "Q1": (f"{year}-01-01", f"{year}-03-31", ("31 thang 3", "31 march")),
            "Q2": (f"{year}-01-01", f"{year}-06-30", ("30 thang 6", "30 june")),
            "Q3": (f"{year}-01-01", f"{year}-09-30", ("30 thang 9", "30 september")),
            "Q4": (f"{year}-01-01", f"{year}-12-31", ("31 thang 12", "31 december")),
        }
        if kind in quarter_dates and str(year) in value and any(x in value for x in quarter_dates[kind][2]):
            start, end, _ = quarter_dates[kind]
            return start, end, evidence(
                number, "PAGE_TEXT", text[:700], _page_method(page_methods, number)
            )
    return None, None, None


_NUMBER = r"\(?\d[\d .]*(?:[.,]\d+)*\)?"
_ROW = re.compile(rf"^\s*(\d{{2,3}})\s+(.+?)\s+({_NUMBER})\s+({_NUMBER})\s*$")


def _fact_rows(
    report_id: str,
    ticker: str,
    document_hash: str,
    pages: list[str],
    report_period: str,
    period_start: str | None,
    period_end: str | None,
    scope: str,
    assurance: str,
    page_methods: list[str] | None = None,
) -> list[dict]:
    rows: list[dict] = []
    for page_number, text in enumerate(pages, 1):
        statement_type = _page_statement_type(text)
        if statement_type not in {"BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT"}:
            continue
        duration = classify_duration(statement_type, text)
        unit = parse_unit(text)
        if unit["unit_status"] != "VERIFIED":
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            match = _ROW.match(" ".join(line.split()))
            if not match:
                continue
            item_code, raw_label, current_raw, prior_raw = match.groups()
            # Avoid treating headers/dates as facts.
            if len(raw_label) < 3 or not re.search(r"[A-Za-zÀ-ỹ]", raw_label):
                continue
            for role, raw_value, year_offset in (
                ("CURRENT_PERIOD" if statement_type != "BALANCE_SHEET" else "CLOSING_BALANCE", current_raw, 0),
                ("PRIOR_YEAR_COMPARATIVE" if statement_type != "BALANCE_SHEET" else "OPENING_BALANCE", prior_raw, -1),
            ):
                start, end = period_start, period_end
                if year_offset and start and end:
                    start = f"{int(start[:4]) + year_offset}{start[4:]}"
                    end = f"{int(end[:4]) + year_offset}{end[4:]}"
                if statement_type == "BALANCE_SHEET" and end:
                    start = end
                numeric = parse_numeric_candidate(raw_value)
                taxonomy = taxonomy_candidate(item_code, raw_label, statement_type)
                extraction_method = _page_method(page_methods, page_number)
                source_location = evidence(
                    page_number, f"TEXT_LINE_{line_number}", line, extraction_method
                )
                fact_id = "fact-" + hashlib.sha256(
                    f"{report_id}|{page_number}|{line_number}|{role}|{raw_value}".encode("utf-8")
                ).hexdigest()[:20]
                semantic_ready = bool(
                    duration != "UNKNOWN"
                    and start
                    and end
                    and scope != "UNKNOWN"
                    and unit["unit_status"] == "VERIFIED"
                    and evidence_complete(source_location)
                    and taxonomy["taxonomy_status"] != "UNRESOLVED"
                    and numeric["parse_status"] == "VERIFIED"
                )
                rows.append({
                    "fact_candidate_id": fact_id,
                    "report_candidate_id": report_id,
                    "ticker": ticker,
                    "document_hash": document_hash,
                    "statement_type": statement_type,
                    "raw_label": raw_label,
                    "raw_value": raw_value,
                    "raw_numeric_text": raw_value,
                    "raw_ocr_numeric_text": (
                        raw_value if extraction_method.startswith("OCR_") else None
                    ),
                    "raw_sign": numeric["raw_sign"],
                    "raw_unit": unit["raw_unit"],
                    "normalized_unit": unit["normalized_unit"],
                    "unit_multiplier": unit["unit_multiplier"],
                    "normalized_numeric_candidate": numeric["normalized_numeric_candidate"],
                    "parse_status": numeric["parse_status"],
                    "period_start": start,
                    "period_end": end,
                    "duration_basis": duration,
                    "column_role": role,
                    "scope": scope,
                    "assurance": assurance,
                    "page": page_number,
                    "region/table": f"TEXT_LINE_{line_number}",
                    "source_location": source_location,
                    "ocr_provenance": (
                        {
                            "document_hash": document_hash,
                            "page": page_number,
                            "ocr_page_result_id": f"ocr-page-{document_hash[:16]}-{page_number:04d}",
                        }
                        if extraction_method.startswith("OCR_")
                        else None
                    ),
                    **taxonomy,
                    "semantic_ready": semantic_ready,
                    "semantic_status": "VERIFIED_CANDIDATE" if semantic_ready else "UNRESOLVED",
                    "report_period_label": report_period,
                })
    return rows


def validate_input_artifact(input_dir: Path) -> dict:
    required = (
        "manifest.json", "gate.json", "checksums.json", "document_index.jsonl",
        "linkage_candidates.jsonl", "timing_index.jsonl", "revision_candidates.jsonl",
    )
    missing = [name for name in required if not (input_dir / name).is_file()]
    if missing:
        raise ValueError(f"missing FIN-PIT-1 inputs: {missing}")
    manifest = _load_json(input_dir / "manifest.json")
    gate = _load_json(input_dir / "gate.json")
    if manifest.get("stage") != "FIN-PIT-1" or gate.get("status") != "PASS":
        raise ValueError("FIN-PIT-1 PASS artifact is required")
    if gate.get("canonical_rows_written") != 0 or gate.get("financial_features_written") != 0:
        raise ValueError("input artifact violates FIN-PIT stage boundary")
    checksums = _load_json(input_dir / "checksums.json").get("files", {})
    for relative, expected in checksums.items():
        path = (input_dir / relative).resolve()
        if not path.is_relative_to(input_dir.resolve()) or not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"FIN-PIT-1 checksum mismatch: {relative}")
    return {"manifest": manifest, "gate": gate, "verified_files": len(checksums)}


def dry_run(input_dir: Path, output_dir: Path) -> dict:
    verified = validate_input_artifact(input_dir)
    rows = _load_jsonl(input_dir / "document_index.jsonl")
    return {
        "stage": STAGE,
        "status": "DRY_RUN_PASS",
        "network_requests": 0,
        "document_linkage_candidates": len(rows),
        "unique_documents": len({row["sha256"] for row in rows}),
        "verified_input_files": verified["verified_files"],
        "output": str(output_dir),
    }


def _write_new(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f"immutable output already exists: {path}")
    path.write_bytes(body)


def execute(input_dir: Path, output_dir: Path) -> dict:
    input_meta = validate_input_artifact(input_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("output exists; use --verify-existing")
    document_rows = _load_jsonl(input_dir / "document_index.jsonl")
    linkage_input = _load_jsonl(input_dir / "linkage_candidates.jsonl")
    timing_input = _load_jsonl(input_dir / "timing_index.jsonl")
    revision_input = _load_jsonl(input_dir / "revision_candidates.jsonl")
    timing_by_sample = {row["sample_id"]: row for row in timing_input}
    linkage_by_candidate = defaultdict(list)
    for row in linkage_input:
        linkage_by_candidate[row["document_candidate_id"]].append(row)
    grouped = defaultdict(list)
    for row in document_rows:
        grouped[row["sha256"]].append(row)

    reports: list[dict] = []
    facts: list[dict] = []
    linkages: list[dict] = []
    quarantines: list[dict] = []
    conflicts: list[dict] = []
    document_by_candidate: dict[str, dict] = {}
    timing_candidates: list[dict] = []

    for digest, source_rows in sorted(grouped.items()):
        first = source_rows[0]
        pdf_path = input_dir / first["local_path"]
        pages, extraction = _extract_pdf(pdf_path)
        filename = unquote(Path(urlsplit(first["source_url"]).path).name)
        role, role_evidence = _document_role(pages, filename, extraction["text_layer_usable"])
        scope, scope_evidence = _scope(pages)
        assurance, assurance_evidence = _assurance(pages)
        period_start, period_end, period_evidence = _period_from_candidate(first["period_candidate"], pages)
        statement_evidence: dict[str, dict] = {}
        for page_number, text in enumerate(pages, 1):
            kind = _page_statement_type(text)
            if kind and kind not in statement_evidence:
                statement_evidence[kind] = evidence(page_number, "PAGE_TEXT", text[:700])
        statements = sorted(statement_evidence)
        report_id = "report-" + digest[:20]
        candidate_ids = sorted(row["document_candidate_id"] for row in source_rows)
        sample_ids = sorted({link["sample_id"] for candidate in candidate_ids for link in linkage_by_candidate[candidate]})
        timings = [timing_by_sample[sample] for sample in sample_ids if sample in timing_by_sample]
        timing = timings[0] if timings else {}
        revision_group_id = None
        for group in revision_input:
            if set(group.get("document_candidate_ids", [])) & set(candidate_ids):
                revision_group_id = "revision-" + hashlib.sha256(canonical_bytes(group)).hexdigest()[:16]
                break
        unit_evidence = None
        unit = {"raw_unit": None, "normalized_unit": "unknown", "unit_multiplier": None, "unit_status": "UNKNOWN"}
        for page_number, text in enumerate(pages, 1):
            parsed = parse_unit(text)
            if parsed["unit_status"] == "VERIFIED":
                unit, unit_evidence = parsed, evidence(page_number, "PAGE_TEXT", text[:700])
                break
        report_semantic_ready = bool(
            role == "PRIMARY_FINANCIAL_REPORT"
            and statements
            and period_start
            and period_end
            and scope != "UNKNOWN"
            and unit["unit_status"] == "VERIFIED"
            and all(evidence_complete(item) for item in (role_evidence, period_evidence, scope_evidence, unit_evidence))
        )
        report = {
            "report_candidate_id": report_id,
            "ticker": first["ticker"],
            "exchange": first["exchange"],
            "document_hash": digest,
            "document_filename": filename,
            "document_title": (pages[0].strip()[:500] if pages and pages[0].strip() else None),
            "source_disclosure_id": sample_ids[0] if sample_ids else None,
            "source_disclosure_ids": sample_ids,
            "source_document_candidate_ids": candidate_ids,
            "document_role": role,
            "statement_types_present": statements,
            "period_start": period_start,
            "period_end": period_end,
            "report_period_label": first["period_candidate"],
            "scope": scope,
            "assurance": assurance,
            "publication_date": timing.get("publication_date"),
            "eligible_from": timing.get("eligible_from"),
            "timing_grade": timing.get("timing_grade", "UNRESOLVED"),
            "timing_policy_version": timing.get("timing_policy_version"),
            "timing_evidence_source": timing.get("timing_evidence_source"),
            "semantic_ready": report_semantic_ready,
            "semantic_status": "VERIFIED_CANDIDATE" if report_semantic_ready else "UNRESOLVED",
            "pit_candidate_status": "NOT_FINAL_PROMOTED",
            "evidence_locations": {
                "document_role": role_evidence,
                "statement_types": statement_evidence,
                "period": period_evidence,
                "scope": scope_evidence,
                "assurance": assurance_evidence,
                "unit": unit_evidence,
            },
            "unit": unit,
            "extraction": extraction,
            "revision_group_id": revision_group_id,
            "revision_relation": "UNKNOWN" if revision_group_id else "NOT_APPLICABLE",
        }
        reports.append(report)
        for candidate_id in candidate_ids:
            document_by_candidate[candidate_id] = report
            for link in linkage_by_candidate[candidate_id]:
                expected_scope = "CONSOLIDATED" if link["sample_id"].endswith("-CONS") else "SEPARATE"
                if scope == "UNKNOWN" or role == "UNKNOWN":
                    status = "AMBIGUOUS"
                    reason = "DOCUMENT_CONTENT_SEMANTICS_UNRESOLVED"
                elif scope != expected_scope:
                    status = "CONFLICT"
                    reason = "DOCUMENT_SCOPE_CONFLICTS_WITH_DISCLOSURE_CANDIDATE"
                else:
                    status = "VERIFIED"
                    reason = "EXACT_OFFICIAL_ROUTE_AND_DOCUMENT_SCOPE_EVIDENCE_AGREE"
                linkage = {
                    "candidate_linkage_id": link["candidate_linkage_id"],
                    "source_disclosure": link["sample_id"],
                    "source_disclosure_evidence": link.get("evidence_source"),
                    "document_hash": digest,
                    "document_filename": filename,
                    "document_title": report["document_title"],
                    "ticker_evidence": {"value": first["ticker"], "source": "FIN-PIT-1_FROZEN_DISCLOSURE"},
                    "period_evidence": period_evidence,
                    "scope_evidence": scope_evidence,
                    "attachment_evidence": {
                        "source_url": first["source_url"],
                        "document_candidate_id": candidate_id,
                        "fin_pit_1_reason": link.get("linkage_reason"),
                    },
                    "linkage_status": status,
                    "linkage_reason": reason,
                }
                linkages.append(linkage)
                if status == "CONFLICT":
                    conflicts.append({
                        "conflict_id": "conflict-" + link["candidate_linkage_id"],
                        "type": "DOCUMENT_SCOPE_CONFLICT",
                        "report_candidate_id": report_id,
                        "source_disclosure": link["sample_id"],
                        "resolution": "NONE_QUARANTINED",
                    })
        report_facts = _fact_rows(
            report_id, first["ticker"], digest, pages, first["period_candidate"],
            period_start, period_end, scope, assurance,
        ) if extraction["text_layer_usable"] and role == "PRIMARY_FINANCIAL_REPORT" else []
        facts.extend(report_facts)
        if not report_semantic_ready:
            reasons = []
            if not extraction["text_layer_usable"]:
                reasons.append("PDF_TEXT_LAYER_UNUSABLE_OCR_NOT_RUN")
            if role == "UNKNOWN":
                reasons.append("DOCUMENT_ROLE_UNKNOWN")
            if not period_start or not period_end:
                reasons.append("PERIOD_UNRESOLVED")
            if scope == "UNKNOWN":
                reasons.append("SCOPE_UNRESOLVED")
            if unit["unit_status"] != "VERIFIED" and role == "PRIMARY_FINANCIAL_REPORT":
                reasons.append("UNIT_UNRESOLVED")
            quarantines.append({
                "quarantine_id": "quarantine-" + digest[:20],
                "report_candidate_id": report_id,
                "document_hash": digest,
                "ticker": first["ticker"],
                "reasons": reasons or ["SEMANTIC_REQUIREMENTS_INCOMPLETE"],
                "semantic_ready": False,
            })
        timing_candidates.append({
            "report_candidate_id": report_id,
            "ticker": first["ticker"],
            "exchange": first["exchange"],
            "publication_date": timing.get("publication_date"),
            "eligible_from": timing.get("eligible_from"),
            "timing_grade": timing.get("timing_grade", "UNRESOLVED"),
            "timing_policy_version": timing.get("timing_policy_version"),
            "timing_evidence_source": timing.get("timing_evidence_source"),
            "preservation_status": "PRESERVED_FROM_FIN_PIT_1",
        })

    revision_rows = [review_revision_group(group, document_by_candidate) for group in revision_input]
    taxonomy_rows = [{
        "fact_candidate_id": row["fact_candidate_id"],
        "report_candidate_id": row["report_candidate_id"],
        "statement_type": row["statement_type"],
        "raw_label": row["raw_label"],
        "taxonomy_candidate": row["taxonomy_candidate"],
        "taxonomy_status": row["taxonomy_status"],
        "promotion_status": "NOT_FINAL_PROMOTED",
    } for row in facts]
    summary = _build_summary(reports, facts, linkages, revision_rows, conflicts, quarantines)
    verified_links = sum(row["linkage_status"] == "VERIFIED" for row in linkages)
    promoted_fields_have_evidence = all(
        not report["semantic_ready"] or all(
            evidence_complete(report["evidence_locations"].get(field))
            for field in ("document_role", "period", "scope", "unit")
        )
        for report in reports
    )
    if not promoted_fields_have_evidence:
        gate_status, gate_reason = "FAIL", "VERIFIED_SEMANTIC_FIELD_LACKS_PROVENANCE"
    elif not reports or verified_links == 0:
        gate_status, gate_reason = "BLOCKED", "NO_SEMANTICALLY_VERIFIED_DOCUMENT_LINKAGE"
    elif quarantines:
        gate_status, gate_reason = "PARTIAL", "TEXT_BASED_SUBSET_USABLE_SCANNED_OR_AMBIGUOUS_DOCUMENTS_QUARANTINED"
    else:
        gate_status, gate_reason = "PASS", "BOUNDED_SEMANTIC_EXTRACTION_COMPLETE"
    gate = {
        "stage": STAGE,
        "status": gate_status,
        "reason": gate_reason,
        "network_request_count": 0,
        "q2_q3_global_assumption_used": False,
        "statement_semantics_evaluated_independently": True,
        "ambiguous_records_quarantined": True,
        "revision_unknown_preserved": all(row["revision_relation"] == "UNKNOWN" for row in revision_rows),
        "verified_fields_have_provenance": promoted_fields_have_evidence,
        "canonical_rows_written": 0,
        "financial_features_written": 0,
        "financial_features_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "report_candidates.jsonl": jsonl_bytes(reports),
        "fact_candidates.jsonl": jsonl_bytes(facts),
        "document_linkage.jsonl": jsonl_bytes(linkages),
        "timing_candidates.jsonl": jsonl_bytes(timing_candidates),
        "taxonomy_candidates.jsonl": jsonl_bytes(taxonomy_rows),
        "revision_review.jsonl": jsonl_bytes(revision_rows),
        "conflicts.jsonl": jsonl_bytes(conflicts),
        "quarantine.jsonl": jsonl_bytes(quarantines),
        "semantic_review_report.json": canonical_bytes(summary),
        "gate.json": canonical_bytes(gate),
    }
    for name, body in payloads.items():
        _write_new(output_dir / name, body)
    manifest = {
        "stage": STAGE,
        "artifact_version": ARTIFACT_VERSION,
        "input_artifact": str(input_dir),
        "input_checksums_sha256": sha256_file(input_dir / "checksums.json"),
        "input_manifest_sha256": sha256_file(input_dir / "manifest.json"),
        "input_verified_file_count": input_meta["verified_files"],
        "network_request_count": 0,
        "extraction_policy": "TEXT_LAYER_FIRST_OCR_ONLY_WHEN_EXPLICITLY_AVAILABLE_V1",
        "canonical_rows_written": 0,
        "financial_features_written": 0,
        "output_files": list(OUTPUT_FILES) + ["checksums.json"],
    }
    _write_new(output_dir / "manifest.json", canonical_bytes(manifest))
    checksums = {
        path.relative_to(output_dir).as_posix(): sha256_file(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name != "checksums.json"
    }
    _write_new(output_dir / "checksums.json", canonical_bytes({"algorithm": "sha256", "files": checksums}))
    return {
        "stage": STAGE,
        "status": gate_status,
        "output": str(output_dir),
        "documents_processed": len(reports),
        "report_candidates": len(reports),
        "fact_candidates": len(facts),
        "quarantine_count": len(quarantines),
        "conflicts": len(conflicts),
        "network_requests": 0,
    }


def _build_summary(reports, facts, linkages, revisions, conflicts, quarantines) -> dict:
    def counts(rows, key):
        return dict(sorted(Counter(row.get(key, "UNKNOWN") for row in rows).items()))

    def scoped(rows, field):
        result = {}
        for value in ("HOSE", "HNX", "UPCOM"):
            result[value] = sum(row.get(field) == value for row in rows)
        return result

    by_exchange = {}
    by_ticker = {}
    quarantined_report_ids = {row["report_candidate_id"] for row in quarantines}
    for exchange in ("HOSE", "HNX", "UPCOM"):
        subset = [row for row in reports if row["exchange"] == exchange]
        by_exchange[exchange] = {
            "documents": len(subset),
            "reports_semantic_ready": sum(row["semantic_ready"] for row in subset),
            "quarantine": sum(row["report_candidate_id"] in quarantined_report_ids for row in subset),
        }
    for ticker in EXPECTED_TICKERS:
        subset = [row for row in reports if row["ticker"] == ticker]
        by_ticker[ticker] = {
            "documents": len(subset),
            "reports_semantic_ready": sum(row["semantic_ready"] for row in subset),
            "facts": sum(row["ticker"] == ticker for row in facts),
        }
    return {
        "documents_total": len(reports),
        "documents_primary_financial": sum(row["document_role"] == "PRIMARY_FINANCIAL_REPORT" for row in reports),
        "documents_supporting": sum(
            row["document_role"] in {"SUPPORTING_ATTACHMENT", "AUDITOR_REVIEW_REPORT", "EXPLANATORY_NOTE", "OTHER"}
            for row in reports
        ),
        "reports_identified": sum(row["document_role"] != "UNKNOWN" for row in reports),
        "statement_counts": Counter(kind for row in reports for kind in row["statement_types_present"]),
        "scope_counts": counts(reports, "scope"),
        "assurance_counts": counts(reports, "assurance"),
        "period_verified": sum(bool(row["period_start"] and row["period_end"]) for row in reports),
        "period_unresolved": sum(not (row["period_start"] and row["period_end"]) for row in reports),
        "standalone_verified": sum(row["duration_basis"] == "STANDALONE" for row in facts),
        "YTD_verified": sum(row["duration_basis"] == "YTD" for row in facts),
        "instant_verified": sum(row["duration_basis"] == "INSTANT" for row in facts),
        "duration_unresolved": sum(row["duration_basis"] == "UNKNOWN" for row in facts),
        "facts_extracted": len(facts),
        "facts_semantic_ready": sum(row["semantic_ready"] for row in facts),
        "facts_unresolved": sum(not row["semantic_ready"] for row in facts),
        "taxonomy_candidates": len(facts),
        "taxonomy_unresolved": sum(row["taxonomy_status"] == "UNRESOLVED" for row in facts),
        "revision_groups_total": len(revisions),
        "revision_groups_resolved": sum(row["resolved"] for row in revisions),
        "revision_groups_unknown": sum(row["revision_relation"] == "UNKNOWN" for row in revisions),
        "linkage_counts": counts(linkages, "linkage_status"),
        "conflicts": len(conflicts),
        "quarantine_count": len(quarantines),
        "reports_semantic_ready": sum(row["semantic_ready"] for row in reports),
        "unit_counts": {
            "VERIFIED": sum(row["unit"]["unit_status"] == "VERIFIED" for row in reports),
            "UNKNOWN": sum(row["unit"]["unit_status"] != "VERIFIED" for row in reports),
        },
        "timing_grade_counts": counts(reports, "timing_grade"),
        "by_exchange": by_exchange,
        "by_ticker": by_ticker,
        "canonical_rows_written": 0,
        "financial_features_written": 0,
    }


def verify_existing(input_dir: Path, output_dir: Path) -> dict:
    validate_input_artifact(input_dir)
    checksums = _load_json(output_dir / "checksums.json").get("files", {})
    for relative, expected in checksums.items():
        path = (output_dir / relative).resolve()
        if not path.is_relative_to(output_dir.resolve()) or not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"FIN-PIT-2 checksum mismatch: {relative}")
    gate = _load_json(output_dir / "gate.json")
    manifest = _load_json(output_dir / "manifest.json")
    if gate.get("canonical_rows_written") != 0 or gate.get("financial_features_written") != 0:
        raise ValueError("forbidden FIN-PIT-2 output detected")
    if gate.get("financial_features_allowed") is not False:
        raise ValueError("financial feature gate changed")
    if manifest.get("input_checksums_sha256") != sha256_file(input_dir / "checksums.json"):
        raise ValueError("input artifact binding mismatch")
    # Validate every JSON/JSONL file during offline replay.
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
