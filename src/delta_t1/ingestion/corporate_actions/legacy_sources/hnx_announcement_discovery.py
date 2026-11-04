"""Bounded discovery through the observed public HNX desktop disclosure filter."""
from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
import re
from urllib.parse import urlencode

from .corporate_action_sources import Document, PublicTransport, SourceLimitation, now, sha

SEARCH_URL = "https://www.hnx.vn/ModuleIssuer/List/ThongTinCongBo"
DETAIL_URL = "https://www.hnx.vn/ModuleArticles/ArticlesCPEtfs/PopupTinCongBoDetail"
GROUP = "CORPORATE_NEWS"


def profile_context(html, ticker, exchange):
    root = Document(html).root
    expected = {"StockCode": ticker, "MarketCode": {"HNX": "NY", "UPCOM": "UC"}[exchange]}
    for key, value in expected.items():
        nodes = root.find("input", id=key)
        if len(nodes) != 1 or nodes[0].attrs.get("value") != value:
            raise SourceLimitation("HNX_DESKTOP_SCOPE_CONTEXT_MISMATCH")
    if SEARCH_URL.split("www.hnx.vn")[1] not in html or not root.find(id="txtTuNgayTinCB") or not root.find(id="txtDenNgayTinCB"):
        raise SourceLimitation("HNX_DESKTOP_SEARCH_LAYOUT_CHANGED")
    return expected["MarketCode"]


def search_payload(ticker, market, page, start, end):
    return urlencode({"pMarketCode": market, "pNumPage": page, "pAction": 1,
                      "pNhomTin": "'" + GROUP + "'", "pTieuDeTin": "", "pStockCode": ticker,
                      "pFromDate": date.fromisoformat(start).strftime("%d/%m/%Y"),
                      "pToDate": date.fromisoformat(end).strftime("%d/%m/%Y"),
                      "pOrderBy": "", "pNumRecord": 20}).encode()


def parse_search_page(html, ticker, exchange, page):
    root = Document(html).root
    tables = [t for t in root.find("table") if "Ngày đăng tin" in t.text() and "Tiêu đề tin" in t.text()]
    totals = re.findall(r"Tổng số\s+([\d.,]+)\s+bản ghi", root.text())
    if len(tables) == 1 and not totals and "Tổng số" not in root.text():
        # Observed HNX empty-query fragment omits a numeric total. Accept only
        # this complete DOM contract, never a shell/error page or contradictory rows.
        table = tables[0]
        bodies = table.find("tbody")
        markers = root.find(id="d_total_rec")
        pages = root.find(id="d_number_of_page")
        loaded = root.find("input", id="idCheckLoadTinCBTV")
        if (table.attrs.get("id") == "_tableDatas"
                and [h.text() for h in table.find("th")] == ["STT", "Ngày đăng tin", "Tiêu đề tin"]
                and len(bodies) == 1 and not bodies[0].text() and not bodies[0].find("tr") and not table.find("td")
                and len(markers) == 1 and markers[0].text() == "Không tìm thấy dữ liệu"
                and "_clsstotal_rec" in markers[0].attrs.get("class", "").split()
                and len(pages) == 1 and not pages[0].text() and not pages[0].find("a")
                and len(loaded) == 1 and loaded[0].attrs.get("type") == "hidden"):
            return [], 0  # Query result only; never a NO_EVENT historical attestation.
    if len(tables) != 1 or len(totals) != 1:
        raise SourceLimitation("HNX_DISCLOSURE_LIST_LAYOUT_CHANGED")
    total = int(totals[0].replace(",", "").replace(".", ""))
    records = []
    for tr in tables[0].find("tr"):
        cells = tr.find("td")
        if not cells:
            continue
        if len(cells) != 3:
            raise SourceLimitation("HNX_DISCLOSURE_ROW_LAYOUT_CHANGED")
        anchors = [a for a in cells[2].find("a") if "XemChiTietDetailArticlesByID" in a.attrs.get("onclick", "")]
        if len(anchors) != 1:
            raise SourceLimitation("HNX_DISCLOSURE_ARTICLE_REFERENCE_UNRESOLVED")
        hit = re.fullmatch(r"\s*return\s+XemChiTietDetailArticlesByID\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*;?\s*", anchors[0].attrs["onclick"])
        if not hit:
            raise SourceLimitation("HNX_DISCLOSURE_ARTICLE_REFERENCE_UNRESOLVED")
        raw_time = cells[1].text()
        parsed = None
        for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S"]:
            try:
                parsed = datetime.strptime(raw_time, fmt)
                break
            except ValueError:
                pass
        if parsed is None:
            raise SourceLimitation("HNX_DISCLOSURE_INVALID_LIST_TIME")
        article_id, file_attach = hit.groups()
        title = anchors[0].text()
        records.append({"ticker_filter": ticker, "exchange_filter": exchange,
                        "identity_basis": "REQUEST_AND_PROFILE_CONTEXT_NOT_HISTORICAL_SECURITY_ID",
                        "provider_article_id": article_id, "file_attach": int(file_attach), "title": title,
                        "list_time_raw": raw_time, "publication_date_candidate": parsed.date().isoformat(),
                        "timezone": None, "list_time_not_accepted_for_pit": True, "search_page": page,
                        "price_action_title_candidate": bool(re.search(r"cổ tức|quyền mua|thưởng|chia tách|gộp|đính chính|điều chỉnh|hủy", title, re.I)),
                        "detail_request": {"url": DETAIL_URL, "method": "POST",
                                           "form": {"pArticlesID": article_id, "pFileAttach": file_attach}},
                        "detail_content_fetched": False})
    if not records and total != 0:
        raise SourceLimitation("HNX_DISCLOSURE_EMPTY_PAGE_WITH_NONZERO_TOTAL")
    return records, total


def discover(scopes, start, end, output, *, max_pages=2, max_requests=6, dry_run=False, transport_factory=PublicTransport,
             scope_evidence=None):
    return _discover(scopes, start, end, output, max_pages=max_pages, max_requests=max_requests,
                     dry_run=dry_run, transport_factory=transport_factory, scope_evidence=scope_evidence)


def discover_for_batch(scope, start, end, output, *, max_pages=50, max_requests=51,
                       transport_factory=PublicTransport, scope_evidence=None):
    """One symbol per immutable work unit; pilot CLI caps remain unchanged."""
    return _discover([scope], start, end, output, max_pages=max_pages, max_requests=max_requests,
                     transport_factory=transport_factory, scope_evidence=scope_evidence, batch=True)


def _discover(scopes, start, end, output, *, max_pages=2, max_requests=6, dry_run=False,
              transport_factory=PublicTransport, scope_evidence=None, batch=False):
    if not 1 <= len(scopes) <= (1 if batch else 2) or len({s["ticker"] for s in scopes}) != len(scopes):
        raise ValueError("PILOT_REQUIRES_ONE_OR_TWO_DISTINCT_TICKERS")
    if (not 1 <= max_pages <= (50 if batch else 3) or not 1 <= max_requests <= (1000 if batch else 8)
            or date.fromisoformat(start).isoformat() != start or date.fromisoformat(end).isoformat() != end
            or date.fromisoformat(start) > date.fromisoformat(end)):
        raise ValueError("INVALID_PILOT_BUDGET_OR_DATES")
    if any(not re.fullmatch(r"[A-Z0-9]{2,10}", s["ticker"]) or s["exchange"] not in {"HNX", "UPCOM"} for s in scopes):
        raise ValueError("INVALID_PILOT_SCOPE")
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    plan = {"stage": "HNX_DESKTOP_DISCLOSURE_DISCOVERY_BATCH_UNIT" if batch else "HNX_DESKTOP_DISCLOSURE_DISCOVERY_PILOT", "scopes": scopes,
            "scope_evidence": scope_evidence,
            "published_start": start, "published_end": end, "date_filter_basis": "PUBLICATION_LIST_DATE_NOT_EX_DATE",
            "group": GROUP, "max_pages_per_ticker": max_pages, "page_size": 20,
            "max_requests": max_requests, "scope_limit": "DISCOVERY_ONLY_NO_EVENT_COMPLETENESS_OR_PIT_CLAIM"}
    if dry_run:
        return dict(plan, status="DRY_RUN", network_requests=0)
    output.mkdir(parents=True, exist_ok=False)
    client = transport_factory(output, max_requests=max_requests, interval=2, timeout=15)
    occurrences, checks, limitations = [], [], []
    for scope in scopes:
        ticker, exchange = scope["ticker"], scope["exchange"]
        market = {"HNX": "NY", "UPCOM": "UC"}[exchange]
        profile = f"https://www.hnx.vn/vi-vn/cophieu-etfs/chi-tiet-chung-khoan-{'ny' if market == 'NY' else 'uc'}-{ticker}.html"
        seen, reported_total, prior_fingerprints = set(), None, set()
        try:
            html, _ = client.fetch(profile)
            profile_context(html, ticker, exchange)
            for page in range(1, max_pages + 1):
                html, receipt = client.fetch(SEARCH_URL, search_payload(ticker, market, page, start, end),
                                             content_type="application/x-www-form-urlencoded; charset=UTF-8")
                records, total = parse_search_page(html, ticker, exchange, page)
                if reported_total is not None and total != reported_total:
                    raise SourceLimitation("HNX_DISCLOSURE_TOTAL_CHANGED_DURING_PILOT")
                reported_total = total
                fingerprint = tuple(r["provider_article_id"] for r in records)
                if records and fingerprint in prior_fingerprints:
                    raise SourceLimitation("HNX_DISCLOSURE_REPEATED_PAGE")
                prior_fingerprints.add(fingerprint)
                for record in records:
                    record["list_receipt"] = receipt
                    occurrences.append(record)
                if any(not start <= r["publication_date_candidate"] <= end for r in records):
                    raise SourceLimitation("HNX_DISCLOSURE_DATE_FILTER_NOT_HONORED")
                if any(r["provider_article_id"] in seen for r in records):
                    raise SourceLimitation("HNX_DISCLOSURE_OVERLAPPING_PAGES")
                seen.update(r["provider_article_id"] for r in records)
                if len(seen) > total:
                    raise SourceLimitation("HNX_DISCLOSURE_TOTAL_INCONSISTENT")
                if len(seen) == total:
                    break
            checks.append({"ticker": ticker, "reported_query_total": reported_total, "distinct_article_ids": len(seen),
                           "query_list_exhausted_within_filter": reported_total == len(seen), "full_history_coverage": "NOT_CERTIFIED",
                           "empty_query_requires_scope_review": reported_total == 0})
        except SourceLimitation as exc:
            limitations.append({"ticker": ticker, "reason": str(exc)})
            break  # no retries or further symbols after source/layout/access failure
    unique = {}
    for record in occurrences:
        unique.setdefault(record["provider_article_id"], record)
    for name, values in [("discovered_articles.jsonl", unique.values()), ("article_occurrences.jsonl", occurrences)]:
        with (output / name).open("x", encoding="utf-8") as f:
            for value in values:
                f.write(json.dumps(value, ensure_ascii=False) + "\n")
    result = {"status": "PARTIAL_DISCOVERY_ONLY", "network_requests": len(client.requests),
              "discovered_article_ids": len(unique), "price_action_title_candidates": sum(r["price_action_title_candidate"] for r in unique.values()),
              "checks": checks, "limitations": limitations, "details_fetched": 0, "canonical_build": False,
              "meaning": "Query result exhaustion does not certify event, revision, historical identity or PIT completeness."}
    for name, value in [("plan.json", plan), ("requests.json", client.requests), ("result.json", result)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"artifact_type": "hnx-disclosure-discovery-v1" if batch else "hnx-disclosure-discovery-pilot-v1", "created_at": now(), "status": result["status"],
                "code_hashes": {p.name: sha(p.read_bytes()) for p in [Path(__file__), Path(__file__).with_name("corporate_action_sources.py")]},
                "files": {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
