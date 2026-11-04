"""Public HOSE security search/event JSON and optional official PDF text evidence."""
from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlencode

from .corporate_action_sources import Document, SourceLimitation, kinds, terms, vn_date

API = "https://api.hsx.vn"


def json_data(text):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise SourceLimitation("HOSE_JSON_LAYOUT_CHANGED") from exc
    if not isinstance(data, dict) or data.get("success") is False:
        raise SourceLimitation("HOSE_JSON_APPLICATION_ERROR")
    return data


def collect_hose(client, ticker, max_pages=2, page_size=10):
    search = API + "/q/api/v1/search?" + urlencode(dict(indexName="securities", field="code^2,isin,figi,introduction", query=ticker, page=1, pageSize=100))
    text, lookup = client.fetch(search)
    payload = json_data(text)
    matches = [r for r in payload.get("items", []) if r.get("code") == ticker]
    if len(matches) != 1:
        raise SourceLimitation("HOSE_SECURITY_MATCH_NOT_UNIQUE")
    security = matches[0]
    result = []
    for page in range(1, max_pages+1):
        url = API + f"/n/api/v1/1/news/securities/{int(security['id'])}/3?" + urlencode(dict(pageIndex=page, pageSize=page_size))
        text, evidence = client.fetch(url)
        data = json_data(text).get("data", {})
        if not isinstance(data.get("list"), list) or not isinstance(data.get("paging"), dict):
            raise SourceLimitation("HOSE_EVENT_LAYOUT_CHANGED")
        for item in data["list"]:
            if item.get("code") != ticker:
                raise SourceLimitation("HOSE_EVENT_IDENTITY_CONFLICT")
            label = item.get("catName") or item.get("title") or ""
            if not re.search(r"không hưởng|quyền mua|cổ tức|cổ phiếu thưởng|chia tách|gộp cổ", label, re.I):
                continue
            detected = kinds(label)
            ambiguous = "cổ phiếu thưởng" in label.lower() and "cổ tức bằng cổ phiếu" in label.lower()
            kind = detected[0] if len(detected) == 1 and not ambiguous else "OTHER"
            try:
                # On this calendar route the frontend renders postedDate as event date,
                # never publication time. Keep the provider epoch and route as evidence.
                ex = datetime.fromtimestamp(item["postedDate"], timezone.utc).date().isoformat() if item.get("postedDate") is not None else None
            except (ValueError, OverflowError, TypeError):
                ex = None
            result.append(dict(ticker=ticker, exchange="HOSE", isin=security.get("isin"),
                               event_type=kind, possible_event_types=detected, ex_date=ex,
                               raw_terms=json.dumps(item, ensure_ascii=False, sort_keys=True),
                               primary_source_type="HOSE", primary_source_url=url, source_hash=evidence["source_hash"],
                               available_at=evidence["fetched_at"], available_at_evidence="FIRST_OBSERVED_AT_ONLY",
                               primary_source_published_at=None, parser="hose-public-event-json-v1", evidence=[lookup, evidence],
                               provider_event_id=str(item["id"]), revision_status="ORIGINAL",
                               raw_field_values={"event_type": label, "ex_date": item.get("postedDate")},
                               parser_issues=["SOURCE_PUBLIC_TIME_UNVERIFIED"] + (["AMBIGUOUS_EVENT_TYPE"] if kind == "OTHER" else [])))
        if page >= data["paging"].get("totalPages", page):
            break
    return result, {"ticker": ticker, "source": "HOSE", "status": "PARTIAL", "reason": "BOUNDED_PUBLIC_EVENT_SCHEDULE; ANNOUNCEMENT_AND_DOCUMENT_COVERAGE_NOT_EXHAUSTED"}


def parse_hose_document(data, evidence, ticker):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SourceLimitation("PDF_TEXT_DEPENDENCY_UNAVAILABLE") from exc
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted or len(reader.pages) > 20:
            raise SourceLimitation("PDF_ENCRYPTED_OR_PAGE_LIMIT")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except SourceLimitation:
        raise
    except Exception as exc:
        raise SourceLimitation("PDF_TEXT_EXTRACTION_FAILED") from exc
    if len(text.strip()) < 50:
        raise SourceLimitation("PDF_SCAN_OR_NO_TEXT_LAYER_MANUAL_REVIEW")
    if not re.search(r"\b" + re.escape(ticker) + r"\b", text):
        raise SourceLimitation("PDF_TICKER_NOT_CONFIRMED")
    detected = kinds(text)
    result = []
    for kind in detected or ["OTHER"]:
        values, problems = terms(kind, text) if len(detected) == 1 else ({}, ["MIXED_EVENT_AMBIGUITY"])
        for phrase, field in (("ngày giao dịch không hưởng quyền", "ex_date"), ("ngày đăng ký cuối cùng", "record_date"), ("ngày thanh toán", "payment_date")):
            found = re.findall(phrase + r"\s*[:：]\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.I)
            if len(set(found)) == 1:
                values[field] = vn_date(found[0])
        result.append(values | dict(ticker=ticker, exchange="HOSE", event_type=kind, raw_terms=text,
                                    primary_source_type="HOSE", primary_source_url=evidence["url"], source_hash=evidence["source_hash"],
                                    available_at=evidence["fetched_at"], primary_source_published_at=None,
                                    available_at_evidence="FIRST_OBSERVED_AT_ONLY", parser="hose-pdf-text-v1", evidence=[evidence],
                                    parser_issues=problems + ["SOURCE_PUBLIC_TIME_UNVERIFIED"], revision_status="ORIGINAL"))
    return result
