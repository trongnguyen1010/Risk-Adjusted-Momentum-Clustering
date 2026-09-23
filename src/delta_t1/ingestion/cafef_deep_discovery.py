"""Bounded evidence expansion for Stage A5-R1.1; never writes canonical data."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from delta_t1.artifact_ids import new_artifact_id
from delta_t1.io import atomic_write, write_json, write_rows
from delta_t1.ingestion.sources.cafef import (
    ADAPTER_VERSION,
    PRICE_HISTORY_ENDPOINT,
    RIGHTS_STATUS,
    TRADE_HISTORY_ENDPOINT,
    CafeFSource,
)

STAGE = "A5-R1.1"
CONTRACT_VERSION = "cafef-a5-r1-1-discovery-1.0.0"
FINANCIAL_ENDPOINT = "https://apiweb.cafef.vn/api/v1/BCTC/GetReportSummary"
DOCUMENT_ENDPOINT = "https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx"
PRIOR_A5_R1 = "m1-a5-r1-cafef-contract-20260922T174031Z-35a27f92"
STATUS_VALUES = ["APPROVED", "SUPPORTED_WITH_LIMITATION", "DIAGNOSTIC_ONLY", "UNRESOLVED", "REJECTED"]


def sample_securities():
    return [
        {"ticker": "FPT", "exchange": "HOSE", "reason": "liquid technology issuer; prior price-basis divergence and rich document history"},
        {"ticker": "VNM", "exchange": "HOSE", "reason": "liquid non-bank issuer; cross-company financial and document coverage"},
        {"ticker": "VCB", "exchange": "HOSE", "reason": "bank taxonomy comparison"},
        {"ticker": "PVS", "exchange": "HNX", "reason": "HNX market and financial coverage"},
        {"ticker": "ACV", "exchange": "UPCOM", "reason": "UPCOM market and prior price-basis regime"},
        {"ticker": "HND", "exchange": "UPCOM", "reason": "provider-published zero-volume precedent and UPCOM depth"},
        {"ticker": "KHP", "exchange": "HOSE", "reason": "share-dividend/additional-listing and capital evidence"},
    ]


def market_plan():
    plan = []
    for item in sample_securities():
        symbol, exchange = item["ticker"], item["exchange"]
        plan.append({"id": f"trade-{symbol.lower()}-recent", "kind": "trade", "symbol": symbol,
                     "exchange": exchange, "page_index": 1, "page_size": 30})
        plan.append({"id": f"price-{symbol.lower()}-2020", "kind": "price", "symbol": symbol,
                     "exchange": exchange, "start_date": "01/01/2020", "end_date": "01/31/2020",
                     "page_index": 1, "page_size": 20})
    return plan


def financial_symbols():
    return [item for item in sample_securities() if item["ticker"] in {"FPT", "VNM", "VCB", "PVS", "ACV"}]


def financial_initial_plan():
    plan = []
    for item in financial_symbols():
        symbol = item["ticker"]
        for report_type, time_type, suffix in (("ALL", "QUY", "quarter-all"),
                                               ("LCTT", "QUY", "quarter-cf"),
                                               ("ALL", "NAM", "annual-all")):
            plan.append({"id": f"financial-{symbol.lower()}-{suffix}", "kind": "financial",
                         "symbol": symbol, "exchange": item["exchange"], "page_index": 1,
                         "page_size": 4, "report_type": report_type, "time_type": time_type})
    return plan


def document_plan():
    plan = [{"id": f"documents-{item['ticker'].lower()}-2026", "kind": "documents",
             "symbol": item["ticker"], "exchange": item["exchange"], "year": 2026}
            for item in financial_symbols()]
    plan.append({"id": "documents-fpt-2025", "kind": "documents", "symbol": "FPT",
                 "exchange": "HOSE", "year": 2025})
    return plan


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _git_head(root):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _params(request):
    if request["kind"] == "financial":
        return {"symbol": request["symbol"], "pageIndex": request["page_index"],
                "pageSize": request["page_size"], "reportType": request["report_type"],
                "TypeTime": request["time_type"]}
    if request["kind"] == "documents":
        return {"Symbol": request["symbol"], "Type": 1, "Year": request["year"]}
    raise ValueError("unsupported direct request kind")


def _save_response(output, request, response):
    raw_rel = f"raw/{request['id']}.json"
    atomic_write(output / raw_rel, response["body"])
    return {
        "request_id": request["id"], "domain": request["kind"], "ticker": request["symbol"],
        "exchange": request["exchange"], "source_url": response["url"],
        "request_params": {k: v for k, v in request.items() if k not in {"id", "kind"}},
        "http_status": response["status"], "fetched_at": _now(), "sha256": _sha(response["body"]),
        "raw_path": raw_rel, "provider": "CafeF", "adapter_version": ADAPTER_VERSION,
        "acquisition_method": "PUBLIC_HTTP_JSON", "row_count": _row_count(request, response["payload"]),
    }


def _row_count(request, payload):
    if request["kind"] == "trade":
        return len(payload.get("Data", []))
    if request["kind"] == "price":
        return len((payload.get("Data") or {}).get("Data", []))
    if request["kind"] == "documents":
        return len(payload.get("Data", []))
    value = payload.get("value") or {}
    return sum(len(group.get("data", [])) for group in value.get("data", []))


def _financial_periods(payload):
    periods = []
    value = payload.get("value") or {}
    for group in value.get("data", []):
        for period in group.get("data", []):
            periods.append({"statement": group.get("code"), "time": period.get("time"),
                            "year": period.get("year"), "quarter": period.get("quater"),
                            "type": period.get("type")})
    return periods


def _financial_count(payload):
    value = payload.get("value") or {}
    count = value.get("count")
    return count if isinstance(count, int) else 0


def _financial_families(payload):
    value = payload.get("value") or {}
    return sorted({row.get("code") for row in value.get("templace", []) if row.get("code")})


def _period_key(period):
    year = period.get("year")
    quarter = period.get("quarter")
    return (year if isinstance(year, int) else -1,
            quarter if isinstance(quarter, int) else 0)


def _edge_period(periods, *, newest):
    valid = [period for period in periods if isinstance(period.get("year"), int)]
    if not valid:
        return ""
    return (max(valid, key=_period_key) if newest else min(valid, key=_period_key)).get("time") or ""


def _scope(name):
    lowered = name.lower()
    if "hợp nhất" in lowered:
        return "CONSOLIDATED"
    if "công ty mẹ" in lowered or "riêng" in lowered:
        return "SEPARATE_OR_PARENT"
    return "UNKNOWN"


def _assurance(name):
    lowered = name.lower()
    if "soát xét" in lowered:
        return "REVIEWED"
    if "kiểm toán" in lowered:
        return "AUDITED"
    return "UNSPECIFIED"


def _filename_token(url):
    name = Path(urlsplit(url).path).name
    matches = re.findall(r"(?<!\d)(\d{8,14})(?!\d)", name)
    return matches[-1] if matches else None


def _ui_observations(observed_at):
    return [
        {"id": "UI-MARKET-FPT", "domain": "historical_market", "ticker": "FPT", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/lich-su-giao-dich/hose/fpt-1.chn",
         "visible_label": "Giá (nghìn VNĐ): Đóng cửa / Điều chỉnh; khớp lệnh; thỏa thuận; Mở cửa/Cao nhất/Thấp nhất",
         "visible_value": "18/09/2026 close 71.70, adjusted 65.18; exchange/ticker/date controls and Xem/Xuất Excel visible",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH", "evidence_source": "UI_OBSERVATION",
         "limitations": "Custom date picker retained typed dates but table did not visibly refresh; range-control behavior is unresolved.", "observed_at": observed_at},
        {"id": "UI-FINANCE-FPT", "domain": "financial_statements", "ticker": "FPT", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/hose/fpt-tai-chinh.chn",
         "visible_label": "BCTC tóm tắt; Cân đối kế toán; Kết quả KD; Lưu chuyển tiền tệ; Theo quý/Theo năm/Lũy kế 6 tháng; Tỷ đồng",
         "visible_value": "Quarter Q3-2025..Q2-2026; annual 2022..2025 marked Đã kiểm toán; CF Q2 PBT 5,714.32 versus Q1 2,803.84 while IS Q2 PBT 2,910.48",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH", "evidence_source": "UI_OBSERVATION",
         "limitations": "Arithmetic pattern suggests CF quarterly display may be YTD, but no authoritative CafeF definition was found.", "observed_at": observed_at},
        {"id": "UI-DOC-FPT", "domain": "financial_documents", "ticker": "FPT", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/hose/fpt-tai-lieu.chn",
         "visible_label": "Loại báo cáo / Thời gian cập nhật / Định dạng / Tải về; year selector 2005..2026",
         "visible_value": "Q2/2026 initial and reviewed rows coexist for parent and consolidated reports; Thời gian cập nhật values are Q2/2026, Q1/2026, CN/2025 rather than datetimes",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH", "evidence_source": "UI_OBSERVATION",
         "limitations": "No first-public timestamp, timezone, revision number or supersession relation is displayed.", "observed_at": observed_at},
        {"id": "UI-BANK-VCB", "domain": "financial_statements", "ticker": "VCB", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/hose/vcb-tai-chinh.chn", "visible_label": "Thu nhập lãi thuần; Tiền gửi của khách hàng",
         "visible_value": "Bank-specific rows are visible under the same statement-family navigation",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH", "evidence_source": "UI_OBSERVATION",
         "limitations": "Taxonomy differs from non-financial issuers and requires a separate item mapping.", "observed_at": observed_at},
        {"id": "UI-IDENTITY-FPT", "domain": "identity_capital", "ticker": "FPT", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/hose/fpt-thong-tin-co-ban.chn",
         "visible_label": "Ngày giao dịch đầu tiên; Vốn điều lệ; KL CP đang niêm yết; KL CP đang lưu hành; KL cổ phiếu niêm yết lần đầu",
         "visible_value": "13/12/2006; 18,858 tỷ đồng; 1,714,326,422; 1,885,759,064; 60,810,230",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH", "evidence_source": "UI_OBSERVATION",
         "limitations": "Current snapshot fields must not be backfilled historically; chart label exists but no auditable dated capital series was extracted.", "observed_at": observed_at},
        {"id": "UI-CA-FPT", "domain": "corporate_actions", "ticker": "FPT", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/fpt-2893107/fpt-2852026-ngay-gdkhq-tra-co-tuc-con-lai-nam-2025-bang-tien-mat-1000-dcp.chn",
         "visible_label": "FPT: 28.5.2026, ngày GDKHQ trả cổ tức còn lại năm 2025 bằng tiền mặt (1.000 đ/cp)",
         "visible_value": "Attached HOSE document: 20260522 - FPT - TB NDKCC tra co tuc con lai nam 2025 bang tien.pdf",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH", "evidence_source": "UI_OBSERVATION",
         "limitations": "Useful event evidence; no price adjustment factor or CafeF adjustment methodology is stated.", "observed_at": observed_at},
        {"id": "UI-CA-KHP", "domain": "corporate_actions", "ticker": "KHP", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/hose/khp-cong-ty-co-phan-dien-luc-khanh-hoa.chn",
         "visible_label": "KHP news/event list", "visible_value": "30.7.2026 GDKHQ stock dividend 100:3; 21.8.2026 additional listing 1,809,772 shares; circulating voting shares 62,186,518",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "MEDIUM", "evidence_source": "UI_OBSERVATION",
         "limitations": "Event headlines are evidence candidates; effective/publication/share-count chronology is not fully linked.", "observed_at": observed_at},
        {"id": "UI-CALENDAR-HOSE", "domain": "status_calendar", "ticker": "HOSE", "exchange": "HOSE",
         "page_url": "https://cafef.vn/du-lieu/hose-2876128/hose-thong-bao-lich-nghi-giao-dich-nam-2026.chn",
         "visible_label": "HOSE: Thông báo lịch nghỉ giao dịch năm 2026",
         "visible_value": "Displayed 24/04/2026 08:00; explicit 2026 holiday dates and two attached source PDFs",
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH", "evidence_source": "UI_OBSERVATION",
         "limitations": "Document/article evidence, not a structured authoritative exchange calendar feed.", "observed_at": observed_at},
    ]


def _field_catalog_rows():
    rows = [
        ("historical_market", "PriceHistory", "Ngay", "trade_date", "date", "session date", "APPROVED", "HIGH", "DD/MM/YYYY; exact provider row"),
        ("historical_market", "PriceHistory", "GiaMoCua", "open", "thousand VND/share", "same session", "SUPPORTED_WITH_LIMITATION", "HIGH", "price basis not promotable"),
        ("historical_market", "PriceHistory", "GiaCaoNhat", "high", "thousand VND/share", "same session", "SUPPORTED_WITH_LIMITATION", "HIGH", "price basis not promotable"),
        ("historical_market", "PriceHistory", "GiaThapNhat", "low", "thousand VND/share", "same session", "SUPPORTED_WITH_LIMITATION", "HIGH", "price basis not promotable"),
        ("historical_market", "TradeHistory/PriceHistory", "ClosePrice/GiaDongCua", "close", "thousand VND/share", "same session", "SUPPORTED_WITH_LIMITATION", "HIGH", "price basis not promotable"),
        ("historical_market", "TradeHistory/PriceHistory", "AdjustPrice/GiaDieuChinh", "adjusted_price", "thousand VND/share", "same session", "DIAGNOSTIC_ONLY", "LOW", "PRICE_BASIS_UNRESOLVED"),
        ("historical_market", "TradeHistory", "BasicPrice", "reference_price", "thousand VND/share", "same session", "APPROVED", "MEDIUM", "identity match still required"),
        ("historical_market", "TradeHistory", "Ceiling/Floor", "price_bands", "thousand VND/share", "same session", "APPROVED", "HIGH", "identity match still required"),
        ("historical_market", "TradeHistory/PriceHistory", "Volume/KhoiLuongKhopLenh", "matched_volume", "shares", "same session", "APPROVED", "HIGH", "explicit zero preserved; missing remains missing"),
        ("historical_market", "TradeHistory/PriceHistory", "TotalValue/GiaTriKhopLenh", "matched_value", "VND/billion VND", "same session", "APPROVED", "HIGH", "endpoint-specific scale"),
        ("financial", "GetReportSummary", "code", "item_code", "text", "statement taxonomy", "SUPPORTED_WITH_LIMITATION", "HIGH", "bank mapping differs"),
        ("financial", "GetReportSummary", "value", "fact_value", "raw VND", "period label only", "SUPPORTED_WITH_LIMITATION", "HIGH", "UI scales by 1e9 or 1e6; PIT blocked"),
        ("financial", "GetReportSummary", "year/quater/time", "fiscal_period", "year/quarter/text", "period label", "SUPPORTED_WITH_LIMITATION", "HIGH", "period_start/end unavailable"),
        ("financial", "GetReportSummary", "type", "statement_scope_candidate", "code", "unknown", "UNRESOLVED", "LOW", "not linked to a source document"),
        ("financial_documents", "FileBCTC", "id", "provider_document_id_candidate", "text", "document row", "SUPPORTED_WITH_LIMITATION", "MEDIUM", "stability/version contract absent"),
        ("financial_documents", "FileBCTC", "Time", "display_period_label", "text", "Qn/YYYY or CN/YYYY", "APPROVED", "HIGH", "not a timestamp"),
        ("financial_documents", "FileBCTC", "Name", "scope_and_assurance_metadata", "text", "document title", "SUPPORTED_WITH_LIMITATION", "HIGH", "raw metadata only"),
        ("financial_documents", "FileBCTC", "Link", "pdf_url", "URL", "document link", "SUPPORTED_WITH_LIMITATION", "HIGH", "public URL; PDF content not bulk-downloaded"),
        ("financial_documents", "filename token", "8-14 digit token", "upload_timestamp_candidate", "unknown", "unknown", "DIAGNOSTIC_ONLY", "LOW", "never published_at/available_at"),
        ("identity_capital", "profile UI", "Ngày giao dịch đầu tiên", "first_trading_date", "date", "listing identity", "SUPPORTED_WITH_LIMITATION", "HIGH", "single UI observation"),
        ("identity_capital", "profile UI", "Vốn điều lệ/share counts", "current_capital_snapshot", "VND/shares", "current snapshot", "SUPPORTED_WITH_LIMITATION", "HIGH", "never backfill historically"),
        ("status_calendar", "HOSE notice UI", "Ngày nghỉ giao dịch", "calendar_notice_date", "date", "notice-listed non-trading date", "SUPPORTED_WITH_LIMITATION", "HIGH", "document evidence only"),
    ]
    keys = ["domain", "surface", "raw_field", "concept", "unit", "date_semantics", "status", "confidence", "limitations"]
    return [dict(zip(keys, row)) for row in rows]


def _write_csv(path, rows, fields=None):
    fields = fields or (list(rows[0]) if rows else ["status"])
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader(); writer.writerows(rows)
    atomic_write(path, buf.getvalue().encode("utf-8"))


def _surface_catalog(ui):
    return {"contract_version": CONTRACT_VERSION, "status_values": STATUS_VALUES,
            "samples": sample_securities(), "surfaces": [
                {"domain": "historical_market", "page": "/du-lieu/lich-su-giao-dich/{exchange}/{ticker}-1.chn", "endpoint": PRICE_HISTORY_ENDPOINT, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH"},
                {"domain": "historical_market", "page": "company page inline request", "endpoint": TRADE_HISTORY_ENDPOINT, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH"},
                {"domain": "financial_statements", "page": "/du-lieu/{exchange}/{ticker}-tai-chinh.chn", "endpoint": FINANCIAL_ENDPOINT, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH"},
                {"domain": "financial_documents", "page": "/du-lieu/{exchange}/{ticker}-tai-lieu.chn", "endpoint": DOCUMENT_ENDPOINT, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH"},
                {"domain": "corporate_actions", "page": "CafeF issuer event/article pages", "endpoint": None, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "MEDIUM"},
                {"domain": "identity_capital", "page": "/du-lieu/{exchange}/{ticker}-thong-tin-co-ban.chn", "endpoint": None, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "MEDIUM"},
                {"domain": "status_calendar", "page": "CafeF exchange notice/article pages", "endpoint": None, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "MEDIUM"},
            ], "ui_observations": ui}


def _endpoint_catalog(request_evidence):
    return {"contract_version": CONTRACT_VERSION, "request_count": len(request_evidence),
            "endpoints": [
                {"url": TRADE_HISTORY_ENDPOINT, "params": ["Symbol", "PageIndex", "PageSize"], "pagination": "one-based; pageSize=30", "ordering": "newest-first with possible leading current snapshot", "role": "reference/bands/raw-VND volume/value and adjusted/close diagnostics"},
                {"url": PRICE_HISTORY_ENDPOINT, "params": ["ExchangeType", "Symbol", "StartDate", "EndDate", "PageIndex", "PageSize"], "pagination": "one-based; pageSize=20", "ordering": "newest-first", "role": "OHLC/adjusted and market-depth probe"},
                {"url": FINANCIAL_ENDPOINT, "params": ["symbol", "pageIndex", "pageSize", "reportType", "TypeTime"], "pagination": "one-based; UI pageSize=4", "ordering": "newest-first response; UI renders oldest-to-newest", "role": "financial summary facts"},
                {"url": DOCUMENT_ENDPOINT, "params": ["Symbol", "Type", "Year"], "pagination": "year filter; no pagination token observed", "ordering": "newest document state first", "role": "document/PDF metadata"},
            ], "requests": request_evidence}


def _market_contract(request_evidence, responses, ui):
    depth = []
    for request_id, pair in responses.items():
        request, response = pair
        if request["kind"] != "price":
            continue
        rows = (response["payload"].get("Data") or {}).get("Data", [])
        depth.append({"ticker": request["symbol"], "exchange": request["exchange"],
                      "window": "2020-01", "row_count": len(rows),
                      "oldest_observed": rows[-1].get("Ngay") if rows else None,
                      "newest_observed": rows[0].get("Ngay") if rows else None,
                      "five_plus_year_signal": bool(rows), "status": "SUPPORTED_WITH_LIMITATION" if rows else "UNRESOLVED"})
    return {
        "contract_version": CONTRACT_VERSION, "prior_contract_run": PRIOR_A5_R1,
        "status": "DIAGNOSTIC_ONLY", "decision": "CAFEF_MARKET_CROSSCHECK_ONLY",
        "price_basis_status": "PRICE_BASIS_UNRESOLVED",
        "adjust_price_methodology_documented": False,
        "price_basis_evidence": {
            "prior_diagnostics": "FPT canonical/CafeF-adjusted ratio near 1.10 while BAB/ACV regimes were near 1.00; ratios do not establish an economic transform.",
            "new_ui_observation": next(row for row in ui if row["id"] == "UI-MARKET-FPT"),
            "prohibited_inference": ["constant multiplier", "split factor", "cash-dividend factor", "total-return transform", "vendor-specific transform"],
        },
        "safe_independent_fields": ["trade_date", "reference_price", "ceiling_price", "floor_price", "matched_volume", "matched_value", "put_through_volume", "put_through_value"],
        "missing_behavior": "No-row/empty provider response remains missing. Never convert to zero.",
        "zero_behavior": "Explicit provider numeric zero is preserved as source evidence only; A5-R1 HND zero-volume observation remains historical evidence.",
        "historical_depth_probe": depth,
        "ohlc_recovery_allowed": False, "canonical_mutations": 0, "synthetic_rows": 0,
        "limitations": ["PRICE_BASIS_UNRESOLVED", "RIGHTS_NOT_VERIFIED", "custom UI date-picker behavior unresolved", "sample does not prove 500-ticker coverage"],
    }


def _document_rows(responses):
    rows = []
    for _, (request, response) in responses.items():
        if request["kind"] != "documents":
            continue
        for doc in response["payload"].get("Data", []):
            rows.append({"ticker": request["symbol"], "exchange": request["exchange"],
                         "provider_document_id": doc.get("id"), "document_title": doc.get("Name"),
                         "year": doc.get("Year"), "quarter": doc.get("Quarter"), "display_period": doc.get("Time"),
                         "statement_scope": _scope(doc.get("Name", "")), "audit_review_status": _assurance(doc.get("Name", "")),
                         "pdf_url": doc.get("Link"), "filename_timestamp_candidate": _filename_token(doc.get("Link", "")),
                         "timestamp_classification": "UPLOAD_TIMESTAMP_ONLY" if _filename_token(doc.get("Link", "")) else "UNKNOWN",
                         "published_at": None, "available_at": None, "timezone": None,
                         "revision": None, "supersedes_id": None, "fact_document_join_id": None,
                         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH",
                         "limitations": "Document metadata only; no first-public timing, timezone, stable fact join or supersession semantics."})
    return rows


def _coverage(responses, documents):
    rows = []
    by_symbol = defaultdict(dict)
    for request, response in (pair for pair in responses.values()):
        if request["kind"] == "financial":
            by_symbol[request["symbol"]][request["id"]] = response["payload"]
    docs_by_symbol = defaultdict(list)
    for doc in documents:
        docs_by_symbol[doc["ticker"]].append(doc)
    exchanges = {x["ticker"]: x["exchange"] for x in sample_securities()}
    reasons = {x["ticker"]: x["reason"] for x in sample_securities()}
    for symbol in [x["ticker"] for x in financial_symbols()]:
        data = by_symbol[symbol]
        q = data.get(f"financial-{symbol.lower()}-quarter-all", {})
        cf = data.get(f"financial-{symbol.lower()}-quarter-cf", {})
        annual = data.get(f"financial-{symbol.lower()}-annual-all", {})
        q_last = data.get(f"financial-{symbol.lower()}-quarter-oldest", {})
        a_last = data.get(f"financial-{symbol.lower()}-annual-oldest", {})
        families = set(_financial_families(q)) | set(_financial_families(cf))
        q_periods = _financial_periods(q) + _financial_periods(cf)
        a_periods = _financial_periods(annual)
        q_old = _financial_periods(q_last)
        a_old = _financial_periods(a_last)
        docs = docs_by_symbol[symbol]
        scopes = sorted({d["statement_scope"] for d in docs if d["statement_scope"] != "UNKNOWN"})
        rows.append({
            "ticker": symbol, "exchange": exchanges[symbol], "reason_selected": reasons[symbol],
            "available_quarterly_periods_reported": _financial_count(q),
            "available_annual_periods_reported": _financial_count(annual),
            "quarterly_newest_visible": _edge_period(q_periods, newest=True),
            "quarterly_oldest_visible": _edge_period(q_old, newest=False),
            "annual_newest_visible": _edge_period(a_periods, newest=True),
            "annual_oldest_visible": _edge_period(a_old, newest=False),
            "balance_sheet_api": "CDKT" in families, "income_statement_api": "KQKD" in families,
            "cash_flow_api": "LCTT" in families, "cash_flow_ui_surface": True,
            "cash_flow_status": "API_AVAILABLE" if "LCTT" in families else "UI_ONLY_LIVE_API_EMPTY",
            "statement_families_api": ";".join(sorted(families)),
            "missing_statement_families_api": "" if "LCTT" in families else "LCTT",
            "document_scopes_2025_2026": ";".join(scopes),
            "audited_or_reviewed_documents": any(d["audit_review_status"] != "UNSPECIFIED" for d in docs),
            "bank_taxonomy_different": symbol == "VCB", "coverage_status": "SAMPLE_ONLY",
            "limitations": "Counts are provider/UI pagination counts from a bounded sample; not a 500-ticker completeness claim.",
        })
    return rows


def _financial_contract(coverage, ui):
    return {
        "contract_version": CONTRACT_VERSION, "status": "SUPPORTED_WITH_LIMITATION",
        "decision": "CAFEF_FINANCIAL_RAW_ONLY",
        "financial_data_availability": "PARTIAL",
        "financial_history_coverage": "SAMPLE_ONLY",
        "financial_pit_readiness": "NOT_READY",
        "statement_families": {"balance_sheet_api": True, "income_statement_api": True,
                               "cash_flow_ui_surface": True, "cash_flow_live_summary_api": False},
        "modes": ["QUY", "NAM", "LUYKE"], "currency_candidate": "VND",
        "raw_fact_unit": "VND; UI renderer offers tỷ đồng/triệu đồng scaling",
        "period_semantics": {"balance_sheet": "instant candidate", "income_statement_quarter": "standalone supported by UI behavior, not source-documented",
                             "cash_flow_q2_q3": "UNKNOWN; observed values appear cumulative/YTD", "period_start": None, "period_end": None},
        "scope": "Document titles distinguish consolidated and parent/separate; fact payload is not stably joined to those documents.",
        "assurance": "Document titles expose audited/reviewed labels; fact payload is not stably joined to those versions.",
        "publication_timing": "NOT DETERMINABLE IN A5-R1.1",
        "available_at": None, "timezone": None, "revision_safety": "REVISION_CHAIN_UNRESOLVED",
        "fact_document_join": "FACT_DOCUMENT_JOIN_UNRESOLVED",
        "historical_research_allowed": False,
        "blockers": ["period_start/period_end absent from summary payload", "stable report/version identity absent",
                     "first-public available_at absent", "timezone absent", "revision/supersession absent",
                     "fact-to-document join absent", "Q2/Q3 cash-flow duration semantics unresolved"],
        "coverage_probe": coverage,
        "ui_observations": [x for x in ui if x["domain"] in {"financial_statements", "financial_documents"}],
    }


def _pit_rows(documents):
    if not documents:
        return [{"status": "UNRESOLVED", "classification": "UNKNOWN", "limitations": "No document evidence returned."}]
    return [{**doc, "display_period_classification": "DOCUMENT_METADATA_ONLY",
             "filename_token_classification": doc["timestamp_classification"],
             "first_public_timestamp": "UNKNOWN"} for doc in documents]


def _revision_rows(documents):
    groups = defaultdict(list)
    for doc in documents:
        groups[(doc["ticker"], doc["year"], doc["quarter"], doc["statement_scope"])].append(doc)
    rows = []
    for key, docs in groups.items():
        assurance = {d["audit_review_status"] for d in docs}
        if len(docs) > 1 and (len(assurance) > 1 or len({d["provider_document_id"] for d in docs}) > 1):
            rows.append({"ticker": key[0], "year": key[1], "quarter": key[2], "statement_scope": key[3],
                         "documents": [{"id": d["provider_document_id"], "title": d["document_title"],
                                        "assurance": d["audit_review_status"], "pdf_url": d["pdf_url"]} for d in docs],
                         "revision_number": None, "supersedes_id": None,
                         "conclusion": "REVISION_CHAIN_UNRESOLVED", "status": "UNRESOLVED", "confidence": "HIGH",
                         "limitations": "Multiple documents coexist, but filename/order does not establish supersession."})
    return rows or [{"status": "UNRESOLVED", "conclusion": "REVISION_CHAIN_UNRESOLVED", "confidence": "HIGH",
                     "limitations": "No explicit revision or supersession relation observed."}]


def _join_rows():
    return [{"ticker": item["ticker"], "exchange": item["exchange"],
             "fact_endpoint": FINANCIAL_ENDPOINT, "document_endpoint": DOCUMENT_ENDPOINT,
             "fact_identifiers_observed": ["symbol", "year", "quater", "time", "statement code", "item code"],
             "document_identifiers_observed": ["id", "Year", "Quarter", "Time", "Name", "Link"],
             "shared_stable_identifier": None, "ticker_period_join_allowed": False,
             "conclusion": "FACT_DOCUMENT_JOIN_UNRESOLVED", "status": "UNRESOLVED", "confidence": "HIGH",
             "limitations": "Ticker+quarter alone is not a provider-explicit stable version join."}
            for item in financial_symbols()]


def _corporate_action_contract(ui):
    return {"contract_version": CONTRACT_VERSION, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "MEDIUM",
            "events_observed": [x for x in ui if x["domain"] == "corporate_actions"],
            "fields_supported_as_evidence": ["event headline", "ex-right date in title", "cash amount or stock ratio in title", "attached exchange document reference"],
            "fields_unresolved": ["machine-stable event id", "full effective/record/payment date contract", "publication timestamp semantics", "CafeF price adjustment factor"],
            "price_transform_approved": False,
            "conclusion": "Corporate-action evidence may explain regime changes diagnostically, but cannot authorize a CafeF-to-KBS price transform."}


def _identity_rows(ui):
    fpt = next(x for x in ui if x["id"] == "UI-IDENTITY-FPT")
    khp = next(x for x in ui if x["id"] == "UI-CA-KHP")
    return [
        {"ticker": "FPT", "exchange": "HOSE", "evidence": fpt, "current_snapshot_only": True,
         "historical_series_verified": False, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH",
         "limitations": "Do not backfill current listed/outstanding shares or charter capital into the past."},
        {"ticker": "KHP", "exchange": "HOSE", "evidence": khp, "current_snapshot_only": False,
         "historical_series_verified": False, "status": "SUPPORTED_WITH_LIMITATION", "confidence": "MEDIUM",
         "limitations": "Individual event headlines exist, but no complete effective/publication-dated capital series was established."},
        {"ticker": None, "exchange": None, "evidence": "exchange transfer, ticker rename and delisting history",
         "current_snapshot_only": None, "historical_series_verified": False, "status": "UNRESOLVED", "confidence": "LOW",
         "limitations": "NOT DETERMINABLE IN A5-R1.1 from the bounded sample."},
    ]


def _status_rows(ui):
    calendar = next(x for x in ui if x["id"] == "UI-CALENDAR-HOSE")
    return [
        {"domain": "trading_calendar", "ticker": "HOSE", "exchange": "HOSE", "evidence": calendar,
         "status": "SUPPORTED_WITH_LIMITATION", "confidence": "HIGH",
         "limitations": "May explain an exchange-wide non-trading date only when the notice explicitly covers it."},
        {"domain": "trading_status", "ticker": "KHP", "exchange": "HOSE",
         "evidence": "No explicit suspension/halt/restricted-trading notice was observed on the bounded KHP page check.",
         "status": "UNRESOLVED", "confidence": "MEDIUM",
         "limitations": "Absence of a price row or absence of a notice in this sample must never be classified as suspension."},
    ]


def _report(run_id, request_count, coverage):
    depth = ", ".join(f"{r['ticker']} Q={r['available_quarterly_periods_reported']} A={r['available_annual_periods_reported']}" for r in coverage)
    return f"""# A5-R1.1 — CafeF Deep Discovery & Evidence Expansion

- Run: `{run_id}`
- Result: `PARTIAL / MANUAL_REVIEW_REQUIRED`
- Computer Use: `USED`
- Public network requests represented in this run: `{request_count}`
- Canonical mutations / synthetic rows / imputed rows: `0 / 0 / 0`
- Sample: `FPT, VNM, VCB, PVS, ACV, HND, KHP`

## Market questions

1. Surfaces: public market-history UI, `TradeHistoryNew.ashx`, and `DataHistory/PriceHistory.ashx`.
2. `TradeHistoryNew` provides date, close/adjusted, reference/ceiling/floor and raw-VND matched/negotiated fields. `PriceHistory` provides OHLC, adjusted price and rounded billion-VND value fields.
3. Preferred: TradeHistory for approved non-OHLC fields; PriceHistory for OHLC diagnostics. They are complementary, not equivalent.
4. CafeF AdjustPrice methodology: **NOT DETERMINABLE IN A5-R1.1**. No authoritative split/bonus/cash-dividend/total-return definition was found.
5. Safe transformation to KBS/canonical basis: **NO**; `PRICE_BASIS_UNRESOLVED`.
6. Missing OHLC recovery: **NO** under the current contract.
7. Independently safe fields: exact date, reference/ceiling/floor, matched and negotiated volume/value, subject to identity/date/source-row checks.
8. Provider zero-volume rows are explicit numeric zeros; preserve them as evidence, never synthesize them.
9. No-row sessions are empty responses and remain missing.
10. A January-2020 row window was found for the sampled symbols where returned; this is a 5+ year signal, not a completeness guarantee.

**MARKET DECISION: `CAFEF_MARKET_CROSSCHECK_ONLY`.** A5-R2 remains blocked; next market action is A5-R4 after manual review.

## Financial questions

1–3. Balance Sheet and Income Statement are populated in the sampled live summary API. Cash Flow is visible in the UI, but `reportType=LCTT` returned a successful empty payload for every sampled issuer; a CF fact endpoint is therefore not established.
4–6. Quarterly and annual history is available. Bounded provider pagination counts: {depth}. This is sample-only.
7. Consolidated vs parent/separate metadata exists on document titles; facts are not stably joined to those documents.
8. Audited/reviewed labels exist on document titles; facts are not stably joined to those versions.
9. VCB exposes bank-specific taxonomy such as net interest income and customer deposits; separate mapping is required.
10. IS quarterly values behave as standalone in the observed FPT UI, while CF Q2 appears cumulative. Authoritative Q2/Q3 duration semantics: **NOT DETERMINABLE IN A5-R1.1**.
11–12. Explicit `period_start` and `period_end` are unavailable from the summary payload.
13. Document rows expose an `id` candidate, but no stability/version contract exists.
14. Fact-to-document mapping: `FACT_DOCUMENT_JOIN_UNRESOLVED`.
15–16. First-public time and timezone: unavailable.
17. Multiple same-period documents coexist, but chronology/supersession is `REVISION_CHAIN_UNRESOLVED`.
18. `available_at` cannot be safely derived.
19. Financial facts cannot enter historical research/backtest.
20. Exact blockers: period boundaries, stable report/version identity, first-public availability time, timezone, revision safety, fact-document join, and CF duration semantics.

- `FINANCIAL_DATA_AVAILABILITY`: `PARTIAL`
- `FINANCIAL_HISTORY_COVERAGE`: `SAMPLE_ONLY` (BS/IS counts are strong pilot signals; CF API coverage is unresolved)
- `FINANCIAL_PIT_READINESS`: `NOT_READY`

**FINANCIAL DECISION: `CAFEF_FINANCIAL_RAW_ONLY`.** Next financial action: `F0 — Financial Source Re-discovery`; F1/F2 remain planned gates, not executed.

## Other domains

- Corporate actions: cash dividend, stock-dividend and additional-listing evidence was observed, but no adjustment transform is approved.
- Identity/capital: current snapshots and first-trading date are useful; a complete effective/publication-dated capital history was not established.
- Status/calendar: a public HOSE 2026 holiday notice is useful documentary evidence. No session is classified as suspended merely because a price row is absent.
- Rights: `{RIGHTS_STATUS}`; discovery access was public and bounded, but automated recovery rights are not verified.

## Decision and manual gate

`PARTIAL / MANUAL_REVIEW_REQUIRED`. No methodology-sensitive policy changed. The 20-before + 20-after rule, 100% real-observation rule, `available_at <= decision_at`, no-imputation rules and revision fail-closed policy remain unchanged.
"""


def build_stage_a5_r1_1(*, root, client=None, prior_public_request_count=0, progress=None,
                        reuse_raw_from=None):
    root = Path(root)
    run_id = new_artifact_id("m1-a5-r1-1-cafef-deep-discovery")
    output = root / "artifacts" / "data_enrichment" / run_id
    output.mkdir(parents=True, exist_ok=False)
    responses, request_evidence = {}, []
    reuse_raw_from = Path(reuse_raw_from) if reuse_raw_from else None
    reuse_metadata = {}
    if reuse_raw_from:
        catalog = json.loads((reuse_raw_from / "cafef_endpoint_catalog.json").read_text(encoding="utf-8"))
        reuse_metadata = {row["request_id"]: row for row in catalog.get("requests", [])}

    def reused_response(request):
        body = (reuse_raw_from / "raw" / f"{request['id']}.json").read_bytes()
        if request["kind"] == "trade":
            endpoint = TRADE_HISTORY_ENDPOINT
            params = {"Symbol": request["symbol"], "PageIndex": request["page_index"], "PageSize": request["page_size"]}
        elif request["kind"] == "price":
            endpoint = PRICE_HISTORY_ENDPOINT
            params = {"ExchangeType": request["exchange"], "Symbol": request["symbol"],
                      "StartDate": request["start_date"], "EndDate": request["end_date"],
                      "PageIndex": request["page_index"], "PageSize": request["page_size"]}
        else:
            endpoint = FINANCIAL_ENDPOINT if request["kind"] == "financial" else DOCUMENT_ENDPOINT
            params = _params(request)
        return {"url": endpoint + "?" + urlencode(params), "status": 200, "headers": {},
                "body": body, "payload": json.loads(body)}

    def acquire(request):
        if progress:
            progress(f"request {request['id']}")
        if reuse_raw_from:
            response = reused_response(request)
        elif request["kind"] in {"trade", "price"}:
            provider = CafeFSource(client)
            response = (provider.acquire_trade_history_page(request) if request["kind"] == "trade"
                        else provider.acquire_price_history_page(request))
        else:
            endpoint = FINANCIAL_ENDPOINT if request["kind"] == "financial" else DOCUMENT_ENDPOINT
            response = client.get_json(endpoint, _params(request))
        responses[request["id"]] = (request, response)
        evidence = _save_response(output, request, response)
        if reuse_raw_from:
            original = reuse_metadata.get(request["id"], {})
            evidence["fetched_at"] = original.get("fetched_at")
            evidence["acquisition_method"] = "REUSED_IMMUTABLE_PUBLIC_HTTP_RAW"
            evidence["original_acquisition_method"] = original.get("acquisition_method", "PUBLIC_HTTP_JSON")
            evidence["reused_from"] = reuse_raw_from.name
        request_evidence.append(evidence)
        return response

    for request in market_plan() + financial_initial_plan():
        acquire(request)
    for item in financial_symbols():
        symbol = item["ticker"]
        for time_type, suffix in (("QUY", "quarter"), ("NAM", "annual")):
            first = responses[f"financial-{symbol.lower()}-{suffix}-all"][1]["payload"]
            last_page = max(1, math.ceil(_financial_count(first) / 4))
            acquire({"id": f"financial-{symbol.lower()}-{suffix}-oldest", "kind": "financial",
                     "symbol": symbol, "exchange": item["exchange"], "page_index": last_page,
                     "page_size": 4, "report_type": "KQKD", "time_type": time_type})
    for request in document_plan():
        acquire(request)

    observed_at = _now()
    ui = _ui_observations(observed_at)
    documents = _document_rows(responses)
    coverage = _coverage(responses, documents)
    total_requests = len(request_evidence) + int(prior_public_request_count)

    write_json(output / "cafef_surface_catalog.json", _surface_catalog(ui))
    write_json(output / "cafef_endpoint_catalog.json", _endpoint_catalog(request_evidence))
    _write_csv(output / "cafef_field_catalog.csv", _field_catalog_rows())
    write_json(output / "cafef_market_contract_extension.json", _market_contract(request_evidence, responses, ui))
    write_json(output / "cafef_financial_contract_draft.json", _financial_contract(coverage, ui))
    _write_csv(output / "cafef_financial_coverage_probe.csv", coverage)
    write_rows(output / "cafef_pit_timing_evidence.jsonl", _pit_rows(documents))
    write_rows(output / "cafef_revision_evidence.jsonl", _revision_rows(documents))
    write_rows(output / "cafef_fact_document_join_evidence.jsonl", _join_rows())
    write_json(output / "cafef_corporate_action_contract.json", _corporate_action_contract(ui))
    write_rows(output / "cafef_identity_capital_evidence.jsonl", _identity_rows(ui))
    write_rows(output / "cafef_status_calendar_evidence.jsonl", _status_rows(ui))
    atomic_write(output / "cafef_deep_discovery_report.md", _report(run_id, total_requests, coverage).encode("utf-8"))

    artifact_files = sorted(str(path.relative_to(output)).replace("\\", "/")
                            for path in output.rglob("*") if path.is_file())
    manifest = {
        "run_id": run_id, "stage": STAGE, "result": "PARTIAL / MANUAL_REVIEW_REQUIRED",
        "created_at": _now(), "git_commit": _git_head(root), "contract_version": CONTRACT_VERSION,
        "computer_use": "USED", "sample_securities": sample_securities(),
        "network_request_count": total_requests, "artifact_network_request_count": len(request_evidence),
        "network_requests_executed_by_this_build": 0 if reuse_raw_from else len(request_evidence),
        "raw_reused_from": reuse_raw_from.name if reuse_raw_from else None,
        "preflight_public_request_count": int(prior_public_request_count),
        "market_decision": "CAFEF_MARKET_CROSSCHECK_ONLY",
        "financial_decision": "CAFEF_FINANCIAL_RAW_ONLY",
        "financial_data_availability": "PARTIAL", "financial_history_coverage": "SAMPLE_ONLY",
        "financial_pit_readiness": "NOT_READY", "price_basis_status": "PRICE_BASIS_UNRESOLVED",
        "rights_status": RIGHTS_STATUS, "manual_review_required": True,
        "unresolved_blockers": ["PRICE_BASIS_UNRESOLVED", "RIGHTS_NOT_VERIFIED", "FACT_DOCUMENT_JOIN_UNRESOLVED",
                                "REVISION_CHAIN_UNRESOLVED", "available_at/timezone unavailable", "financial period boundaries unresolved"],
        "next_allowed_market_action": "A5-R4 — Additional Market Source Discovery (after manual review); A5-R2 remains BLOCKED",
        "next_allowed_financial_action": "F0 — Financial Source Re-discovery",
        "canonical_mutations": 0, "synthetic_rows": 0, "imputed_rows": 0,
        "input_references": [PRIOR_A5_R1, "docs/crawl/sources/CAFEF.md", "docs/crawl/sources/P0_FINANCIAL_PIT_RESOLUTION.md"],
        "artifacts": {name: _sha((output / name).read_bytes()) for name in artifact_files},
    }
    write_json(output / "manifest.json", manifest)
    return output, manifest
