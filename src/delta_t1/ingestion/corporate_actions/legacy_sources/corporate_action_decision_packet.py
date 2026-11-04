"""Evidence-backed field selection requests; never sign or apply decisions."""
from decimal import Decimal,InvalidOperation
from fractions import Fraction
import re
import unicodedata

from .corporate_action_sources import Document
from .corporate_action_cache_audit import document_view,provider_id
from .corporate_action_offline_reconcile import date_view

TITLE_CHANGE=re.compile(r"đính chính|điều chỉnh|sửa đổi|hủy|tạm dừng|hoãn|gia hạn|thay đổi|ngừng",re.I)
BODY_CHANGE=re.compile(r"hủy (?:bỏ )?(?:ngày đăng ký cuối cùng|đợt chào bán|đợt phát hành|thông báo thực hiện quyền)|đính chính thông báo|tạm dừng.{0,100}(?:đợt chào bán|đợt phát hành|thực hiện quyền)|thông báo về việc gia hạn thời gian thực hiện quyền mua cổ phiếu",re.I)
OUTCOME=re.compile(r"kết quả.{0,60}(?:phát hành|chào bán)|hoàn (?:tất|thành).{0,60}(?:phát hành|chào bán)|đăng ký (?:chứng khoán )?bổ sung",re.I)
RIGHTS_CODE=re.compile(r"\bMIR[A-Z0-9]{4,16}\b")
NOTICE=re.compile(r"thông báo\s*(?:số)?\s*:?\s*(\d+/TB-[\w/-]+)(?:\s+ngày\s*(\d{1,2}/\d{1,2}/\d{4}))?",re.I)


def precision_diagnostic(sdk_value,source_ratio):
    """Prove decimal rounding consistency using fractions, without tolerance."""
    try:
        if sdk_value is None or isinstance(sdk_value,bool):raise ValueError("BAD_SDK_RATIO")
        sdk=Decimal(str(sdk_value))
        if not sdk.is_finite() or sdk<=0:raise ValueError("BAD_SDK_RATIO")
        numerator,denominator=source_ratio["numerator"],source_ratio["denominator"]
        if any(not isinstance(x,int) or isinstance(x,bool) or x<=0 for x in [numerator,denominator]):raise ValueError("BAD_SOURCE_FRACTION")
        source=Fraction(numerator,denominator)
        if source<=0:raise ValueError("BAD_SOURCE_RATIO")
        scale=max(0,-sdk.as_tuple().exponent)
        if scale>18:raise ValueError("SDK_SCALE_OUT_OF_DIAGNOSTIC_SCOPE")
    except (InvalidOperation,KeyError,ZeroDivisionError,TypeError,ValueError) as exc:
        return {"status":"UNRESOLVED","reason":str(exc),"override_applied":False}
    sdk_fraction=Fraction(sdk);scaled=source*10**scale
    integer=(2*scaled.numerator+scaled.denominator)//(2*scaled.denominator)
    rounded=Fraction(integer,10**scale);difference=sdk_fraction-source
    return {"status":"EXACT" if sdk_fraction==source else "CONSISTENT_WITH_RECORDED_DECIMAL_ROUNDING" if rounded==sdk_fraction else "DIFFERENT_AT_RECORDED_SDK_SCALE",
        "sdk_value_unchanged":str(sdk),"recorded_sdk_decimal_scale":scale,
        "source_exact":{"numerator":source.numerator,"denominator":source.denominator},
        "sdk_minus_source_exact":{"numerator":difference.numerator,"denominator":difference.denominator},
        "rounded_source_at_recorded_scale":format(Decimal(integer).scaleb(-scale),"f"),
        "provider_rounding_method_verified":False,"override_applied":False,"comparison_tolerance_applied":False}


def quote(text,match,padding=35):
    start=max(0,match.start()-padding);end=min(len(text),match.end()+padding)
    return {"start":start,"end":end,"text":text[start:end]}


def change_scope(text,title):
    unchanged=re.search(r"các nội dung khác.{0,250}?không thay đổi",text,re.I)
    after=re.search(r"thông tin (?:thay đổi|điều chỉnh|đính chính)\s*:?",text,re.I)
    changed_text=""
    if after:
        tail=text[after.end():]
        end=re.search(r"các nội dung khác|lý do đính chính|đề nghị",tail,re.I)
        changed_text=tail[:end.start()] if end else tail
    economic=bool(re.search(r"giá (?:phát hành|chào bán|đăng ký mua)|tỷ lệ (?:thực hiện|phát hành|quyền mua)",changed_text,re.I))
    account=bool(re.search(r"tài khoản",title,re.I) and re.search(r"số tài khoản|tên chủ tài khoản|ngân hàng",changed_text,re.I))
    # Some provider titles are generic; the explicit purpose sentence in the
    # article body can identify a schedule revision. This remains a preview:
    # before/after continuity, unchanged clauses and owner approval are separate.
    body_schedule=re.search(r"thông báo về việc gia hạn thời gian thực hiện quyền mua cổ phiếu",text,re.I)
    schedule=bool((re.search(r"thời gian|thời hạn",title,re.I) or body_schedule) and re.search(r"thời gian|thời hạn|ngày hiệu lực",changed_text,re.I))
    scope="ADMINISTRATIVE_ACCOUNT_WITH_OTHER_TERMS_UNCHANGED" if unchanged and account and not economic else "SCHEDULE_WITH_OTHER_TERMS_UNCHANGED" if unchanged and schedule and not economic else "CHANGE_SCOPE_OR_LINEAGE_UNRESOLVED"
    references=[];by_id={}
    for m in NOTICE.finditer(text):
        references.append({"notice_id_literal":m[1],"notice_date_literal":m[2],"quote":quote(text,m,0)})
        if m[2]:by_id.setdefault(m[1].upper(),set()).add(m[2])
    return {"scope":scope,"other_terms_unchanged_quote":quote(text,unchanged,0) if unchanged else None,
        "changed_text_for_review":changed_text,"explicit_economic_terms_in_changed_text":economic,
        "notice_references":references,"notice_ids_with_conflicting_date_literals":sorted(k for k,v in by_id.items() if len(v)>1),
        "price_ratio_revision_ruled_out":False,"lineage_approved":False}


def inspect_history_document(body,url):
    text_body=unicodedata.normalize("NFC",body.decode("utf-8-sig"))
    root=Document(text_body).root;content=root.find(cls="content-category")
    if len(content)!=1:raise ValueError("HISTORY_ARTICLE_LAYOUT_REQUIRED")
    text=content[0].text();base=document_view(body,url)
    info=content[0].find(cls="item-info")
    labels={info[i].text().rstrip(":").casefold():info[i+1].text() for i in range(0,len(info)-1,2)}
    return {"ticker":base["ticker"],"title_ticker_hint":base.get("title_ticker_hint"),"title":base["title"],
        "provider_article_id":provider_id(url),"kinds":base["kinds"],"record_dates":base["record_dates"],"ex_dates":base["ex_dates"],
        "issuer_name_literal":labels.get("tên tổ chức phát hành"),"isin_literal":labels.get("mã isin"),"exchange_literal":labels.get("sàn giao dịch"),
        "rights_codes":sorted(set(RIGHTS_CODE.findall(text))),
        "title_change_markers":[m.group() for m in TITLE_CHANGE.finditer(base["title"])],
        "body_change_quotes":[quote(text,m) for m in BODY_CHANGE.finditer(text)],
        "change_scope_review":change_scope(text,base["title"]),
        "possible_outcome_title":bool(OUTCOME.search(base["title"])),"article_text":text,
        "normal_rights_code_expiry_mentioned":bool(re.search(r"hiệu lực hủy mã quyền mua",text,re.I))}


def link_history(row,article,selected_provider_ids,target_rights_codes):
    record=date_view(row["original_sdk_row"].get("record_date"));ex=date_view(row["original_sdk_row"].get("ex_right_date"))
    declared=article["ticker"]==row["ticker"]
    provider=article["provider_article_id"] in selected_provider_ids
    shared=sorted(set(article["rights_codes"])&set(target_rights_codes))
    dated=declared and bool(record and article["record_dates"]==[record]) and "RIGHTS_ISSUE" in article["kinds"]
    conflict=bool((record and article["record_dates"] and article["record_dates"]!=[record]) or
        (ex and article["ex_dates"] and article["ex_dates"]!=[ex]))
    strong=provider or bool(shared) or (dated and not conflict)
    date_text=bool(record and any(token in article["article_text"] for token in [f"{int(record[8:])}/{int(record[5:7])}/{record[:4]}",f"{record[8:]}/{record[5:7]}/{record[:4]}"]))
    entity_hint=declared or article["title_ticker_hint"]==row["ticker"]
    changed=bool(article["title_change_markers"] or article["body_change_quotes"])
    weak=not strong and entity_hint and changed and date_text
    return {"relationship":"SELECTED_PROVIDER_ARTICLE" if provider else "EXPLICIT_RIGHTS_CODE_REFERENCE" if shared else
        "DECLARED_TICKER_RECORD_COMPONENT_ANCHOR" if dated and not conflict else "POSSIBLE_CHANGE_DATE_REFERENCE_ONLY" if weak else "OTHER_OR_UNLINKED",
        "strong_event_reference":strong,"weak_reference_only":weak,"shared_rights_codes":shared,
        "date_conflict":conflict,"revision_or_cancellation_candidate":(strong or weak) and changed,
        "possible_outcome_candidate":strong and article["possible_outcome_title"],"event_identity_approved":False}


def disposition(was_supported,diagnostics,history_checks,source_consistent=True):
    if not source_consistent:return "HOLD_SOURCE_VALUE_CONFLICT"
    if any(h["revision_or_cancellation_candidate"] for h in history_checks):return "HOLD_LINKED_CHANGE_REVIEW"
    if was_supported:return "EXISTING_RULE_PRICE_SELECTION_PROPOSAL"
    if diagnostics and all(d["status"]=="CONSISTENT_WITH_RECORDED_DECIMAL_ROUNDING" for d in diagnostics):
        return "CASE_SPECIFIC_EXACT_SOURCE_SELECTION_PROPOSAL"
    return "HOLD_RATIO_REQUIRES_ADDITIONAL_PRIMARY_EVIDENCE"


def make_request(row,sources,history_checks):
    diagnostics=[precision_diagnostic(row["original_sdk_row"].get("ratio"),s["ratio_exact"]) for s in sources]
    prices={s["price_vnd"] for s in sources};ratios={(s["ratio_exact"]["numerator"],s["ratio_exact"]["denominator"]) for s in sources}
    consistent=bool(sources) and len(prices)==len(ratios)==1 and all(s["primary_unit_explicit"] and s["ticker_record_supported"] for s in sources)
    consistent=consistent and not any(h.get("observed_terms_conflict") or (h["strong_event_reference"] and h.get("date_conflict")) for h in history_checks)
    decision=disposition(row["field_data_supported_pending_review"],diagnostics,history_checks,consistent)
    selectable=decision in {"EXISTING_RULE_PRICE_SELECTION_PROPOSAL","CASE_SPECIFIC_EXACT_SOURCE_SELECTION_PROPOSAL"}
    price=next(iter(prices)) if len(prices)==1 else None
    needs_case_approval=decision=="CASE_SPECIFIC_EXACT_SOURCE_SELECTION_PROPOSAL"
    changes=[h for h in history_checks if h["revision_or_cancellation_candidate"]]
    conditional=decision=="HOLD_LINKED_CHANGE_REVIEW" and bool(changes) and all(h.get("change_scope_review",{}).get("scope") in {
        "ADMINISTRATIVE_ACCOUNT_WITH_OTHER_TERMS_UNCHANGED","SCHEDULE_WITH_OTHER_TERMS_UNCHANGED"} for h in changes)
    return {"ticker":row["ticker"],"vci_payload_sha256":row["vci_payload_sha256"],"original_sdk_row":row["original_sdk_row"],
        "original_record_date_review_view":date_view(row["original_sdk_row"].get("record_date")),
        "decision_class":decision,"review_status":"MANUAL_REVIEW_REQUIRED","owner_decision":None,"signature_created":False,
        "price_observation_supported":consistent,"observed_price_vnd":price,
        "proposed_fields_pending_approval":{"rights_subscription_price":{"value":price,"unit":"VND/share","source_document_ids":[s["document_id"] for s in sources]}} if selectable else {},
        "proposed_exact_ratio_selection_pending_approval":sources[0]["ratio_exact"] if needs_case_approval else None,
        "existing_rule_ratio_evidence":[s["ratio_exact"] for s in sources] if row["field_data_supported_pending_review"] else [],
        "conditional_price_selection_after_lineage_review":{"value":price,"unit":"VND/share","source_document_ids":[s["document_id"] for s in sources],
            "approval_conditions":["CONFIRM_DOCUMENT_LINEAGE","CONFIRM_CHANGE_SCOPE_AND_UNCHANGED_PRICE_RATIO","SEPARATE_PIT_AND_HISTORICAL_IDENTITY_GATES"]} if conditional else None,
        "conditional_exact_source_ratio_after_lineage_review":sources[0]["ratio_exact"] if conditional and not row["field_data_supported_pending_review"] else None,
        "sources":sources,"precision_diagnostics":diagnostics,"cached_history_checks":history_checks,
        "economic_difference_ruled_out":False,"provider_transformation_inferred":False,
        "lifecycle_status":"CACHED_CHANGE_REFERENCE_REQUIRES_REVIEW" if any(h["revision_or_cancellation_candidate"] for h in history_checks) else "CACHED_RIGHTS_SCHEDULE_ONLY_TERMINAL_EXECUTION_NOT_CERTIFIED",
        "history_scope":"ENTITY_OR_TITLE_HINT_DOCUMENTS_IN_SEALED_VSDC_CACHE; NOT_COMPLETE_SOURCE_ARCHIVE_OR_ALL_PROVIDERS",
        "approval_scope":"OBSERVED_FIELD_SELECTION_ONLY; NO_PIT_IDENTITY_RESEARCH_FREEZE_OR_GLOBAL_TOLERANCE",
        "case_specific_ratio_selection_approval_required":needs_case_approval,
        "automatic_approval":False,"canonical_written":False,"sdk_values_overwritten":False,
        "pit_status":"NOT_PROMOTED","historical_identity":"UNVERIFIED"}
