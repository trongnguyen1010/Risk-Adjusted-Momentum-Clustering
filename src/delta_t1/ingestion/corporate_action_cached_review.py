"""Reparse scoped cached articles for review; no production reconciliation changes."""
from decimal import Decimal,localcontext
import re
import unicodedata

from .corporate_action_sources import Document,kinds
from .corporate_action_cache_audit import document_view
from .corporate_action_evidence_review import ratios,ratio_relation,vi_decimal,RATIO_HEAD
from .corporate_action_offline_reconcile import date_view

HEAD=re.compile(r"(?<!\S)(?:\d{1,2}(?:\.\d{1,2})*[.)]|[a-z][.)])\s*(?=[^\W\d_])",re.I)
PRICE=re.compile(r"giá (?:phát hành|chào bán|đăng ký mua)\s*[:=]\s*([\d.,]+)\s*đồng(?P<unit>\s*/\s*(?:0*1\s*)?(?:cổ phiếu|cổ phần|cp\b))?",re.I)
COMPATIBLE={"EXACT","SDK_10_DECIMAL_COMPARISON_COMPATIBLE"}


def split_components(text,expected):
    """Keep one terms-bearing numbered block per kind; summary headings cannot win."""
    markers=list(HEAD.finditer(text));candidates={};headers=[]
    for index,marker in enumerate(markers):
        start=marker.end();end=markers[index+1].start() if index+1<len(markers) else len(text)
        fragment=text[start:end]
        heading=re.split(r":|\s+-\s+|\btỷ lệ\b|\bmã quyền\b",fragment,maxsplit=1,flags=re.I)[0].strip()
        detected=kinds(heading)
        has_terms=bool(re.search(RATIO_HEAD,fragment,re.I) or PRICE.search(fragment))
        headers.append({"marker":marker.group().strip(),"heading":heading[:200],"kinds":detected,"has_terms":has_terms})
        if len(detected)!=1 or detected[0] not in expected or not has_terms:continue
        candidates.setdefault(detected[0],[]).append({"start":start,"end":end,"text":fragment,
            "heading":heading,"marker":marker.group().strip()})
    valid=set(candidates)==set(expected) and all(len(v)==1 for v in candidates.values())
    return {"status":"UNIQUE_TERMS_BEARING_COMPONENTS" if valid else "COMPONENT_SCOPE_UNRESOLVED",
        "headers":headers,"sections":{k:v[0] for k,v in candidates.items()} if valid else {},
        "candidate_counts":{k:len(v) for k,v in candidates.items()}}


def primary_prices(fragment):
    result=[]
    for match in PRICE.finditer(fragment):
        try:value=vi_decimal(match[1])
        except ValueError:continue
        if value<=0:continue
        result.append({"value_vnd":str(value),"explicit_per_share_unit":bool(match["unit"]),
            "quote":{"start":match.start(),"end":match.end(),"text":match.group()}})
    return result


def parse_scoped_article(body,url):
    text_body=unicodedata.normalize("NFC",body.decode("utf-8-sig"))
    root=Document(text_body).root;contents=root.find(cls="content-category")
    base=document_view(body,url,["RIGHTS_ISSUE"])
    if len(contents)!=1 or base["layout"]!="VSDC_ARTICLE":raise ValueError("ARTICLE_LAYOUT_REQUIRED")
    text=contents[0].text();expected=base["kinds"]
    if len(expected)>1:
        partition=split_components(text,expected)
    elif len(expected)==1:
        partition={"status":"SINGLE_COMPONENT_ARTICLE","headers":[],"candidate_counts":{expected[0]:1},
            "sections":{expected[0]:{"start":0,"end":len(text),"text":text,"heading":base["title"],"marker":""}}}
    else:partition={"status":"COMPONENT_SCOPE_UNRESOLVED","headers":[],"sections":{},"candidate_counts":{}}
    components={}
    for kind,section in partition["sections"].items():
        fragment=section["text"]
        components[kind]=section|{"ratio":ratios(fragment,kind),"primary_prices":primary_prices(fragment) if kind=="RIGHTS_ISSUE" else []}
    return {"ticker":base["ticker"],"title":base["title"],"kinds":expected,
        "record_dates":base["record_dates"],"ex_dates":base["ex_dates"],
        "partition":{k:v for k,v in partition.items() if k!="sections"},"components":components,
        "article_text":text,"title_revision_candidate":bool(re.search(r"đính chính|điều chỉnh|sửa đổi|hủy bỏ|hủy ngày|thay đổi",base["title"],re.I)),
        "quote_offset_basis":"NFC decoded text; component span=article_text; price quote=component.text; ratio quote=ratio.evidence_text"}


def review_link(row,article):
    original=row["original_sdk_row"];record=date_view(original.get("record_date"));ex=date_view(original.get("ex_right_date"))
    date_conflict=bool((record and article["record_dates"] and article["record_dates"]!=[record]) or
        (ex and article["ex_dates"] and article["ex_dates"]!=[ex]))
    dated=not date_conflict and bool((record and article["record_dates"]==[record]) or (ex and article["ex_dates"]==[ex]))
    identity=article["ticker"]==row["ticker"] and dated and "RIGHTS_ISSUE" in article["kinds"]
    component=article["components"].get("RIGHTS_ISSUE");relation=ratio_relation(original.get("ratio"),component["ratio"]) if component else "COMPONENT_UNRESOLVED"
    prices=component["primary_prices"] if component else []
    values=sorted({p["value_vnd"] for p in prices},key=Decimal)
    unit_ok=bool(prices) and all(p["explicit_per_share_unit"] for p in prices)
    blockers=[]
    if not identity:blockers.append("TICKER_OR_DATE_LINK_UNVERIFIED")
    if not component:blockers.append("COMPONENT_SCOPE_UNRESOLVED")
    if len(values)!=1:blockers.append("PRIMARY_PRICE_MISSING_OR_AMBIGUOUS")
    if prices and not unit_ok:blockers.append("PRIMARY_PRICE_UNIT_EVIDENCE_REQUIRED")
    if relation not in COMPATIBLE:blockers.append("RATIO_TERM_REVIEW_REQUIRED")
    if article["title_revision_candidate"]:blockers.append("REVISION_REVIEW_REQUIRED")
    exact=component["ratio"]["values"][0] if component and component["ratio"]["status"]=="EXPLICIT_RATIO_SUPPORTED" else None
    difference=None
    if exact and original.get("ratio") is not None:
        with localcontext() as context:
            context.prec=50
            difference=str(Decimal(str(original["ratio"]))-Decimal(exact["numerator"])/Decimal(exact["denominator"]))
    return {"ticker_date_anchor_supported":identity,"date_conflict":date_conflict,"raw_ratio_relation":relation,
        "source_ratio_exact":exact,"sdk_ratio_unchanged":original.get("ratio"),"sdk_minus_source_ratio_diagnostic":difference,
        "primary_price_values_vnd":values,"primary_unit_explicit":unit_ok,
        "candidate_price_vnd_pending_review":values[0] if len(values)==1 else None,
        "field_data_supported_pending_review":not blockers,"blockers":blockers,
        "review_status":"MANUAL_REVIEW_REQUIRED","field_approved":False,"event_identity_approved":False,
        "rounding_override_applied":False,"pit_status":"NOT_PROMOTED","historical_identity":"UNVERIFIED"}
