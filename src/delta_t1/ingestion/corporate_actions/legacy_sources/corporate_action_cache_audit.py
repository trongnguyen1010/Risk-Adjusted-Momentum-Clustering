"""Offline cache triage. Raw presence, event linkage and field approval stay separate."""
from datetime import date
import re
import unicodedata
from urllib.parse import urljoin,urlsplit

from .corporate_action_sources import Document,kinds,component_sections,vn_date
from .corporate_action_evidence_review import ratios,ratio_relation,vi_decimal
from .corporate_action_offline_reconcile import date_view


def provider_id(url):
    p=urlsplit(url)
    m=re.fullmatch(r"/vi/ad1?/(\d+)",p.path)
    return m[1] if p.hostname=="vsdc.vn" and m else None


def document_view(body,url,wanted_kinds=()):
    root=Document(unicodedata.normalize("NFC",body.decode("utf-8-sig"))).root
    contents,titles=root.find(cls="content-category"),root.find(cls="title-category")
    if len(contents)!=1 or len(titles)!=1:
        return {"layout":"UNRECOGNIZED","ticker":None,"title":"","kinds":[],"components":{},"record_dates":[],"ex_dates":[],"date_hint":None,"attachments":[]}
    content=contents[0];text=content.text();title=titles[0].text();info=content.find(cls="item-info")
    pairs=[(info[i].text().rstrip(":").casefold(),info[i+1].text()) for i in range(0,len(info)-1,2)]
    labels=dict(pairs)
    ticker_values={v.strip().upper() for k,v in pairs if k=="mã chứng khoán"}
    ticker=next(iter(ticker_values)) if len(ticker_values)==1 else ""
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}",ticker):ticker=None
    title_hint=re.match(r"^\s*([A-Z][A-Z0-9]{1,9})\s*:",title)
    detected=kinds(title+" "+labels.get("lý do mục đích",""))
    role="PRICE_ACTION_NOTICE" if detected else "NON_PRICE_ACTION_NOTICE" if re.search(r"đại hội|lấy ý kiến|họp",title,re.I) else "TYPE_UNRESOLVED"
    dates={}
    for field,label in [("record_dates","ngày đăng ký cuối cùng"),("ex_dates","ngày giao dịch không hưởng quyền")]:
        values=[vn_date(m.group()) for m in re.finditer(label+r"\s*:\s*\d{1,2}/\d{1,2}/\d{4}",text,re.I)]
        if field=="record_dates" and labels.get(label):values.append(vn_date(labels[label]))
        dates[field]=sorted({d for d in values if d})
    times=root.find(cls="time-newstcph");hint=vn_date(times[0].text()) if len(times)==1 else None
    sections=component_sections(text);components={}
    for kind in set(detected)&set(wanted_kinds):
        fragment=sections.get(kind,text if len(detected)==1 else "")
        prices=[]
        if kind=="RIGHTS_ISSUE":
            for m in re.finditer(r"giá (?:phát hành|chào bán|đăng ký mua)\s*[:=]\s*([\d.,]+)\s*đồng(?P<unit>\s*/\s*(?:0*1\s*)?(?:cổ phiếu|cổ phần|cp\b))?",fragment,re.I):
                try:amount=str(vi_decimal(m[1]))
                except ValueError:continue
                if vi_decimal(m[1])>0:
                    prices.append({"amount_vnd":amount,"unit_explicit":bool(m["unit"]),"raw_text":m.group()})
        components[kind]={"scope":"EXPLICIT_OR_SINGLE_COMPONENT" if fragment else "COMPONENT_SCOPE_UNRESOLVED",
            "prices":prices,"ratio":ratios(fragment,kind)}
    attachments=sorted({urljoin(url,a.attrs["href"]) for a in content.find("a") if a.attrs.get("href") and re.search(r"\.pdf(?:$|[?#])|/upload|/download",a.attrs["href"],re.I)})
    return {"layout":"VSDC_ARTICLE","ticker":ticker,"title_ticker_hint":title_hint[1] if title_hint else None,
        "title":title,"document_role":role,"kinds":detected,"record_dates":dates["record_dates"],"ex_dates":dates["ex_dates"],
        "date_hint":hint,"date_hint_semantics":"UPDATE_OR_UNVERIFIED_TIME_NOT_PUBLICATION",
        "components":components,"attachments":attachments}


def search_links(body,url):
    root=Document(body.decode("utf-8-sig")).root;out=[]
    for a in root.find("a"):
        link=urljoin(url,a.attrs.get("href",""))
        if provider_id(link):
            title=a.text();m=re.match(r"^\s*([A-Z][A-Z0-9]{1,9})\s*:",title)
            out.append({"url":link,"provider_article_id":provider_id(link),"title":title,
                "ticker_title_hint":m[1] if m else None,"kind_hints":kinds(title)})
    return out


def candidate(task,doc,days=120):
    kind=task["category"];row=task["original_sdk_row"]
    if doc.get("ticker")!=task["ticker"] or kind not in doc.get("components",{}):return None
    record=date_view(row.get("record_date"));ex=date_view(row.get("ex_right_date"))
    conflict=bool((record and doc["record_dates"] and doc["record_dates"]!=[record]) or (ex and doc["ex_dates"] and doc["ex_dates"]!=[ex]))
    exact=not conflict and bool((record and doc["record_dates"]==[record]) or (ex and doc["ex_dates"]==[ex]))
    relation=ratio_relation(row.get("ratio"),doc["components"][kind]["ratio"])
    hint=date_view(row.get("public_date"));source_hint=doc.get("date_hint")
    near=bool(hint and source_hint and abs((date.fromisoformat(hint)-date.fromisoformat(source_hint)).days)<=days)
    mode="EXPLICIT_DATE_CONFLICT_REVIEW" if conflict else "EXPLICIT_DATED_ANCHOR" if exact else "TERMS_AND_TIME_HINT_CANDIDATE_ONLY" if relation in {"EXACT","SDK_10_DECIMAL_COMPARISON_COMPATIBLE"} and near else "SAME_TICKER_KIND_WITHOUT_EVENT_LINK"
    legacy=doc.get("legacy",{}).get(kind,[])
    return {"document_id":doc["document_id"],"source_url":doc["source_url"],"mode":mode,"raw_ratio_relation":relation,
        "legacy_normalized_rows":len(legacy),"legacy_price_valid":any(x.get("rights_subscription_price") is not None for x in legacy),
        "record_dates":doc["record_dates"],"ex_dates":doc["ex_dates"],"prices":doc["components"][kind]["prices"],
        "component_scope":doc["components"][kind]["scope"],"event_identity_approved":False}


def assess_field(field,candidates,uncached_count=0,same_ticker_count=0):
    dated=[c for c in candidates if c["mode"]=="EXPLICIT_DATED_ANCHOR"]
    weak=[c for c in candidates if c["mode"]=="TERMS_AND_TIME_HINT_CANDIDATE_ONLY"]
    def explicit(c):
        if field=="rights_subscription_price":return any(p["unit_explicit"] for p in c["prices"])
        return bool(c["record_dates"] if field=="record_date" else c["ex_dates"])
    found=[c for c in dated if explicit(c)]
    if found:
        status="RAW_FIELD_PRESENT_OFFLINE_MATCH_OR_PARSER_REVIEW"
    elif field=="rights_subscription_price" and any(c["prices"] for c in dated):
        status="RAW_AMOUNT_PRESENT_PRIMARY_UNIT_NOT_EXPLICIT"
    elif dated:
        status="MATCHED_CACHED_DOCUMENT_FIELD_NOT_EXPLICIT"
    elif any(explicit(c) for c in weak):
        status="CACHED_FIELD_CANDIDATE_EVENT_LINK_UNVERIFIED"
    elif weak:
        status="CACHED_EVENT_CANDIDATE_FIELD_AND_LINK_REVIEW"
    elif uncached_count:
        status="UNCACHED_DISCOVERED_DOCUMENT_CANDIDATES_RELEVANCE_UNVERIFIED"
    elif candidates or same_ticker_count:
        status="ONLY_OTHER_OR_UNLINKED_CACHED_DOCUMENTS"
    else:
        status="NO_RELEVANT_DOCUMENT_IDENTIFIED_IN_AUDITED_CACHE"
    return {"status":status,"dated_cache_candidates":len(dated),"time_hint_candidates_only":len(weak),
        "raw_field_support_document_ids":[c["document_id"] for c in found],
        "price_already_in_normalized_cache":field=="rights_subscription_price" and any(c["legacy_price_valid"] for c in found),
        "network_action":"NONE_IN_THIS_STAGE","field_approved":False}
