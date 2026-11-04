"""Kiểm tra raw fields độc lập với normalized terms cũ; chỉ evidence review."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction
import json
import re
import unicodedata
from urllib.parse import urljoin

from .corporate_action_sources import Document, component_sections, kinds
from .corporate_action_offline_reconcile import term_agreement

NUMBER = r"\d+(?:[.,]\d+)*"
RATIO_HEAD = r"t[ỷỉ]\s*lệ\s+(?:thực hiện(?: quyền mua)?|phát hành|cổ tức|thưởng|quyền mua)\s*[:=]\s*"


def vi_decimal(value):
    """Chỉ vi-VN explicit; không đoán dot-decimal, multiplier hoặc số thiếu."""
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", value):
        return Decimal(value.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d+(?:,\d+)?", value):
        return Decimal(value.replace(",", "."))
    raise ValueError("AMBIGUOUS_VI_NUMBER")


def quote(text, match, padding=55):
    start, end = max(0, match.start()-padding), min(len(text), match.end()+padding)
    return {"start": start, "end": end, "text": text[start:end]}


def fraction_record(value):
    with localcontext() as ctx:
        ctx.prec = 40
        decimal = str(Decimal(value.numerator) / Decimal(value.denominator))
    return {"numerator": value.numerator, "denominator": value.denominator, "decimal": decimal}


def ratios(fragment, kind):
    heads = list(re.finditer(RATIO_HEAD, fragment, re.I))
    if not heads:
        return {"status": "RATIO_NOT_EXTRACTED", "values": [], "evidence": []}
    start = heads[0].start()
    tail = fragment[start:]
    stop = re.search(r"phương án|ví dụ|địa điểm|thời gian|thời hạn", tail, re.I)
    text = tail[:stop.start()] if stop else tail[:2200]
    found, declared, evidence = set(), set(), []
    for m in re.finditer(RATIO_HEAD + rf"({NUMBER})\s*%", text, re.I):
        try:
            value = Fraction(vi_decimal(m[1])) / 100
        except ValueError:
            continue
        declared.add(value)
        evidence.append({"role": "DECLARED_PERCENT", "ratio": fraction_record(value), "quote": quote(text, m)})
    share = r"(?:cổ phiếu|cổ phần)"
    direct = rf"(?:sở hữu|có)\s+({NUMBER})\s+{share}(?:\s+(?:hiện hữu|phổ thông))?\s+(?:thì\s+)?(?:sẽ\s+)?(?:được\s+)?(?:quyền\s+)?(?:nhận|mua)(?:\s+thêm)?\s+({NUMBER})\s+{share}"
    for m in re.finditer(direct, text, re.I):
        try:
            old, new = map(vi_decimal, m.groups())
            if old <= 0:
                continue
            value = Fraction(new) / Fraction(old)
        except ValueError:
            continue
        found.add(value)
        evidence.append({"role": "EXPLICIT_EXISTING_TO_NEW_SHARES", "ratio": fraction_record(value), "quote": quote(text, m)})
    if kind == "RIGHTS_ISSUE":
        allocation, execution = set(), set()
        annotation = r"(?:\s*\((?:một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười)\))?"
        for pattern, pool, role in [
            (rf"({NUMBER}){annotation}\s+{share}(?:(?!\d|[,;()]).){{0,140}}?(?:hưởng(?:\s+được|\s+tương ứng)?|nhận(?:\s+được)?|phân bổ|được|tương ứng(?:\s+với)?|có)\s+({NUMBER}){annotation}\s+quyền", allocation, "RIGHTS_PER_EXISTING_SHARE"),
            (rf"({NUMBER}){annotation}\s+quyền(?:\s+mua)?\s+(?:thì\s+)?(?:sẽ\s+)?(?:được\s+)?(?:quyền\s+)?mua(?:\s+thêm)?\s+({NUMBER}){annotation}\s+{share}", execution, "NEW_SHARES_PER_RIGHT"),
        ]:
            for m in re.finditer(pattern, text, re.I):
                try:
                    old, new = map(vi_decimal, m.groups())
                    if old <= 0:
                        continue
                    value = Fraction(new) / Fraction(old)
                except ValueError:
                    continue
                pool.add(value)
                evidence.append({"role": role, "ratio": fraction_record(value), "quote": quote(text, m)})
        if len(allocation) == len(execution) == 1:
            found.add(next(iter(allocation)) * next(iter(execution)))
        elif (allocation or execution) and not found:
            # A lone OLD-rights:NEW-shares leg does not prove allocation per share.
            return {"status": "INCOMPLETE_OR_AMBIGUOUS_RIGHTS_LEGS", "values": [], "evidence": evidence, "evidence_text": text}
    # A colon declaration alone has no guaranteed unit direction. Keep it as a
    # quote, never turn it into a ratio unless explicit share/right legs exist.
    for m in re.finditer(RATIO_HEAD + rf"({NUMBER})\s*:\s*({NUMBER})", text, re.I):
        evidence.append({"role": "COLON_DECLARATION_REVIEW_ONLY", "quote": quote(text, m)})
        if found:
            try:
                old, new = map(vi_decimal, m.groups())
                if old > 0:
                    declared.add(Fraction(new) / Fraction(old))
            except ValueError:
                pass
    values = found | declared
    return {"status": "EXPLICIT_RATIO_SUPPORTED" if len(values) == 1 else
                      "RAW_INTERNAL_RATIO_DIFFERENCE" if len(values) > 1 else "RATIO_NOT_EXTRACTED",
            "values": [fraction_record(v) for v in sorted(values)], "evidence": evidence, "evidence_text": text}


def inspect_article(body, source_type, kind, source_url):
    root = Document(unicodedata.normalize("NFC", body.decode("utf-8-sig"))).root
    if source_type == "VSDC":
        contents, titles = root.find(cls="content-category"), root.find(cls="title-category")
    elif source_type == "HNX":
        contents, titles = root.find(cls="Box-Noidung"), root.find(cls="Box-TieuDe")
    else:
        raise ValueError("UNSUPPORTED_RAW_SOURCE_LAYOUT")
    if len(contents) != 1 or len(titles) != 1:
        raise ValueError("RAW_ARTICLE_LAYOUT_AMBIGUOUS")
    content, title = contents[0], titles[0].text()
    text = content.text()
    labels = content.find(cls="item-info")
    label_map = {labels[i].text().rstrip(":").casefold(): labels[i+1].text() for i in range(0, len(labels)-1, 2)}
    tickers = []
    for m in re.finditer(r"mã chứng khoán\s*:\s*([A-Z][A-Z0-9]{1,9})\b", text, re.I):
        tickers.append({"value": m[1].upper(), "quote": quote(text, m)})
    if source_type == "HNX":
        for m in re.finditer(r"đối với cổ phiếu\s+([A-Z][A-Z0-9]{1,9})\b", text, re.I):
            tickers.append({"value": m[1].upper(), "quote": quote(text, m)})
    dates = {}
    from datetime import date
    for field, label in [("record_date", "ngày đăng ký cuối cùng"), ("ex_date", "ngày giao dịch không hưởng quyền")]:
        values = []
        for m in re.finditer(label + r"\s*:\s*(\d{1,2})/(\d{1,2})/(\d{4})\b", text, re.I):
            try:
                value = date(int(m[3]), int(m[2]), int(m[1])).isoformat()
            except ValueError:
                continue
            values.append({"value": value, "quote": quote(text, m)})
        dates[field] = values
    detected = kinds(title + " " + label_map.get("lý do mục đích", ""))
    fragment = text
    scope = "SINGLE_COMPONENT_ARTICLE"
    sections = component_sections(text)
    if kind in sections:
        fragment, scope = sections[kind], "EXPLICIT_COMPONENT_SECTION"
    elif len(detected) > 1:
        fragment = ""
        scope = "EXPLICIT_COMPONENT_SECTION" if fragment else "COMPONENT_UNRESOLVED"
    elif detected != [kind]:
        fragment = ""
        scope = "COMPONENT_UNRESOLVED"
    prices = []
    for m in re.finditer(rf"giá (?:phát hành|chào bán|đăng ký mua|bán)\s*[:=]\s*({NUMBER})\s*đồng(?P<unit>\s*/\s*(?:0*1\s*)?(?:cổ phiếu|cổ phần|cp\b))?", fragment, re.I):
        try:
            number = vi_decimal(m[1])
        except ValueError:
            continue
        prices.append({"value_vnd": str(number), "explicit_per_share_unit": bool(m["unit"]), "quote": quote(fragment, m)})
    revision = bool(re.search(r"đính chính|điều chỉnh|sửa đổi|hủy bỏ|hủy ngày|thay đổi", title, re.I))
    revision_kind = "SCHEDULE_REVISION_CANDIDATE" if revision and re.search(r"thời gian|thời hạn|ngày", title, re.I) else "OTHER_REVISION_REVIEW" if revision else "NO_TITLE_REVISION_MARKER"
    attachment_links = sorted({urljoin(source_url, a.attrs["href"]) for a in content.find("a")
        if a.attrs.get("href") and re.search(r"\.pdf(?:$|[?#])|/upload|/download|/file/", a.attrs["href"], re.I)})
    return {"article_title": title, "component_scope": scope, "detected_kinds": detected,
        "tickers": tickers, "dates": dates, "prices": prices, "ratio": ratios(fragment, kind),
        "revision_diagnostic": revision_kind, "attachment_links_not_fetched": attachment_links,
        "component_text_for_review": fragment, "article_text_for_review": text,
        "quote_offset_basis": "Decoded NFC text: ticker/dates=article, prices=component, ratio=ratio.evidence_text; not byte offsets"}


def inspect_hose_calendar(body, archived):
    """Verify exact JSON literals; epoch date is the existing UTC review view."""
    from datetime import datetime, timezone
    payload = json.loads(body)
    values, fields = archived["values"], archived["fields"]
    epoch = fields["ex_date"]["raw_value"]
    label = fields["event_type"]["raw_value"]
    matches = [(i, r) for i, r in enumerate(payload["data"]["list"])
               if r.get("code") == archived["ticker"] and r.get("postedDate") == epoch
               and (r.get("catName") or r.get("title")) == label]
    if len(matches) != 1:
        raise ValueError("HOSE_RAW_EVENT_NOT_UNIQUE")
    index, record = matches[0]
    review_date = datetime.fromtimestamp(epoch, timezone.utc).date().isoformat()
    if review_date != values["ex_date"]:
        raise ValueError("HOSE_PRIOR_DATE_PROJECTION_MISMATCH")
    return {"article_title": label, "component_scope": "JSON_CALENDAR_ROW_NO_ECONOMIC_TERMS",
        "raw_json_record": record, "json_pointer": f"/data/list/{index}",
        "tickers": [{"value": record["code"], "json_pointer": f"/data/list/{index}/code"}],
        "dates": {"record_date": [], "ex_date": [{"value": review_date, "raw_epoch": epoch,
            "basis": "EXISTING_UTC_REVIEW_PROJECTION_NOT_PUBLICATION_OR_CANONICAL_APPROVAL"}]},
        "prices": [], "ratio": {"status": "RATIO_NOT_EXTRACTED", "values": [], "evidence": []},
        "revision_diagnostic": "NO_TITLE_REVISION_MARKER", "attachment_links_not_fetched": [],
        "component_text_for_review": "", "article_text_for_review": ""}


def ratio_relation(sdk_ratio, raw_ratio):
    if raw_ratio["status"] != "EXPLICIT_RATIO_SUPPORTED":
        return "RAW_RATIO_UNRESOLVED"
    raw = raw_ratio["values"][0]
    value = Fraction(raw["numerator"], raw["denominator"])
    if sdk_ratio is None or isinstance(sdk_ratio, bool) or Decimal(str(sdk_ratio)) <= 0:
        return "SDK_RATIO_UNRESOLVED"
    if Fraction(Decimal(str(sdk_ratio))) == value:
        return "EXACT"
    if term_agreement(sdk_ratio, raw["decimal"]) == "SDK_SERIALIZATION_PRECISION_COMPATIBLE":
        return "SDK_10_DECIMAL_COMPARISON_COMPATIBLE"
    left, right = Decimal(str(sdk_ratio)), Decimal(raw["decimal"])
    # Diagnosis only: never relax matching or rewrite either number.
    places = max(0, -left.as_tuple().exponent)
    quantum = Decimal(1).scaleb(-places)
    if right.quantize(quantum, rounding=ROUND_HALF_UP) == left:
        return "POSSIBLE_PROVIDER_ROUNDING_REVIEW_ONLY"
    raw_places = max(0, -right.as_tuple().exponent)
    if raw_places < places and left.quantize(Decimal(1).scaleb(-raw_places), rounding=ROUND_HALF_UP) == right:
        return "POSSIBLE_SOURCE_PRECISION_DIFFERENCE_REVIEW_ONLY"
    return "DIFFERENT"


def review_price(row, articles):
    proposed = row["fields"]["rights_subscription_price"]["proposed_value_pending_review"]
    evidence_ids = {r["evidence_id"] for option in row["fields"]["rights_subscription_price"]["candidate_values"] for r in option["evidence"] if "evidence_id" in r}
    results = []
    for identifier in sorted(evidence_ids):
        article = articles[identifier]
        record = row["fields"]["record_date"]["original_review_value"] or row["fields"]["record_date"]["proposed_value_pending_review"]
        prices = {Decimal(p["value_vnd"]) for p in article["prices"]}
        ticker_ok = {t["value"] for t in article["tickers"]} == {row["ticker"]}
        record_ok = {d["value"] for d in article["dates"]["record_date"]} == {record}
        amount_ok = prices == {Decimal(str(proposed))}
        unit_ok = bool(article["prices"]) and all(p["explicit_per_share_unit"] for p in article["prices"])
        price_ok = amount_ok and unit_ok
        relation = ratio_relation(row["original_sdk_row"]["ratio"], article["ratio"])
        results.append({"evidence_id": identifier, "ticker_supported": ticker_ok, "record_date_supported": record_ok,
            "price_amount_supported": amount_ok, "explicit_per_share_unit_supported": unit_ok,
            "price_and_unit_supported": price_ok, "ratio_relation": relation,
            "raw_price_supported": ticker_ok and record_ok and price_ok})
    linked_revision = any(articles[ref["evidence_id"]]["revision_diagnostic"] != "NO_TITLE_REVISION_MARKER" for ref in row["official_links"])
    strong = {"EXACT", "SDK_10_DECIMAL_COMPARISON_COMPATIBLE"}
    status = "RAW_PRICE_SUPPORTED_EVENT_TERMS_SUPPORTED" if results and all(x["raw_price_supported"] and x["ratio_relation"] in strong for x in results) else "NEEDS_EVENT_TERM_REVIEW"
    if any(not x["raw_price_supported"] for x in results):
        status = "RAW_PRICE_OR_EVENT_ANCHOR_NOT_CONFIRMED"
        if results and all(x["ticker_supported"] and x["record_date_supported"] and x["price_amount_supported"] for x in results):
            status = "PRICE_AMOUNT_SUPPORTED_UNIT_REVIEW_REQUIRED"
    if linked_revision:
        status = "REVISION_REVIEW_REQUIRED"
    return {"status": status, "evidence_checks": results, "linked_revision": linked_revision,
        "canonical_approved": False, "review_status": "MANUAL_REVIEW_REQUIRED"}


def diagnose_conflict(sdk_ratio, raw, peer_ratios):
    relation = ratio_relation(sdk_ratio, raw)
    diagnosis = relation
    values = {Fraction(Decimal(str(v))) for v in peer_ratios if v is not None}
    if relation not in {"EXACT", "SDK_10_DECIMAL_COMPARISON_COMPATIBLE"} and raw["status"] == "EXPLICIT_RATIO_SUPPORTED":
        target = raw["values"][0]
        total = sum(values, Fraction())
        if len(values) > 1 and term_agreement(float(total), target["decimal"]) in {"EXACT", "SDK_SERIALIZATION_PRECISION_COMPATIBLE"}:
            diagnosis = "COHORT_COMPONENT_SUM_CANDIDATE_REVIEW_ONLY"
        elif re.search(r"trong đó|t[ỷỉ]\s*lệ thực hiện năm\s+20\d{2}", raw.get("evidence_text", ""), re.I):
            # Explicit component wording takes precedence over the weak fact
            # that rounding 5% to one decimal fraction could produce 10%.
            diagnosis = "RAW_ARTICLE_COMPONENTS_REQUIRE_REVIEW"
    return {"ratio_relation": relation, "diagnosis": diagnosis,
        "cohort_distinct_ratio_values": [str(v) for v in sorted(values)],
        "no_aggregation_or_tolerance_applied": True}
