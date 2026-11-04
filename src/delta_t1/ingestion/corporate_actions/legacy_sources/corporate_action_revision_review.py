"""Offline contextual revision review; never approve identity or field choices."""
from datetime import datetime
import re

DATE = r"\d{1,2}/\d{1,2}/\d{4}"
BEFORE = re.compile(r"(?:Thông tin đã thông báo(?: tại)?|Thông tin tại)\s*:?", re.I)
AFTER = re.compile(r"Thông tin (?:điều chỉnh|thay đổi|đính chính)\s*:", re.I)
TICKER = re.compile(r"mã chứng khoán\s*:?\s*([A-Z0-9]{3,10})\b", re.I)
RECORD = re.compile(r"ngày đăng ký cuối cùng\s*:?\s*(" + DATE + r")", re.I)
RANGES = {
    "transfer": re.compile(r"Thời gian chuyển nhượng quyền mua(?: cổ phiếu)?\s*:\s*Từ ngày\s*(" + DATE + r")\s*đến(?:\s+ngày)?\s*(" + DATE + r")", re.I),
    "subscription": re.compile(r"Thời gian đăng ký(?: đặt mua và nộp tiền mua cổ phiếu| và đặt mua cổ phiếu)\s*:\s*Từ ngày\s*(" + DATE + r")\s*đến(?:\s+ngày)?\s*(" + DATE + r")", re.I),
    "rights_code_expiry": re.compile(r"ngày hiệu lực hủy mã quyền mua\s*:?\s*(" + DATE + r")", re.I),
    "member_deadline": re.compile(r"Thời hạn (?:thành viên lưu ký|TVLK) nộp (?:Danh sách|Hồ sơ) đặt mua cổ phiếu và chuyển tiền đặt mua cổ phiếu cho (?:VSD|CNVSD)\s*:\s*(?:ngày\s*)?(" + DATE + r")", re.I),
}
ACCOUNT = re.compile(r"Số (?:tài khoản|TK)\s*:\s*([0-9.]+)", re.I)


def quote(text, match, offset=0):
    return {"start": match.start() + offset, "end": match.end() + offset, "text": match.group()}


def date_iso(value):
    return datetime.strptime(value, "%d/%m/%Y").date().isoformat()


def schedule(text, offset=0):
    result = {}
    for key, pattern in RANGES.items():
        matches = list(pattern.finditer(text))
        values = {tuple(date_iso(v) for v in m.groups()) for m in matches}
        if matches:
            result[key] = {"values": [list(v) for v in sorted(values)],
                           "quotes": [quote(text, m, offset) for m in matches]}
    return result


def review_edge(original, previous, revision, ticker, record_date):
    """Link by explicit body anchors AND before/after continuity, never by date alone.

    A matching schedule is contextual evidence, not proof that a provider article
    is the signed notice number cited by another article. Missing intermediate
    documents, ambiguous values, and contradictory notice dates remain holds.
    """
    text = revision["article_text"]
    scope = revision["change_scope_review"]
    tickers = [m for m in TICKER.finditer(text) if m.group(1).upper() == ticker]
    dates = [m for m in RECORD.finditer(text) if date_iso(m.group(1)) == record_date]
    shared = sorted(set(original["rights_codes"]) & set(revision["rights_codes"]))
    reasons = []
    if not tickers or not dates:
        reasons.append("EXPLICIT_BODY_TICKER_RECORD_ANCHOR_MISSING")
    if ({m.group(1).upper() for m in TICKER.finditer(text)} - {ticker}
            or {date_iso(m.group(1)) for m in RECORD.finditer(text)} - {record_date}):
        reasons.append("CONFLICTING_BODY_ENTITY_OR_RECORD_ANCHOR")
    if scope["scope"] not in {"SCHEDULE_WITH_OTHER_TERMS_UNCHANGED", "ADMINISTRATIVE_ACCOUNT_WITH_OTHER_TERMS_UNCHANGED"}:
        reasons.append("UNRESOLVED_CHANGE_SCOPE")
    if not scope["other_terms_unchanged_quote"] or scope["explicit_economic_terms_in_changed_text"]:
        reasons.append("UNCHANGED_ECONOMIC_TERMS_NOT_SUPPORTED")
    if scope["notice_ids_with_conflicting_date_literals"]:
        reasons.append("CONTRADICTORY_NOTICE_DATE_LITERALS")
    before = BEFORE.search(text)
    after = AFTER.search(text)
    comparisons = {}
    after_values = {}
    if not before or not after or before.end() >= after.start():
        reasons.append("BEFORE_AFTER_BOUNDARY_UNRESOLVED")
    elif scope["scope"] == "ADMINISTRATIVE_ACCOUNT_WITH_OTHER_TERMS_UNCHANGED":
        old = list(ACCOUNT.finditer(text, before.end(), after.start()))
        changed = scope["changed_text_for_review"]
        new = list(ACCOUNT.finditer(changed))
        prior = list(ACCOUNT.finditer(previous["article_text"]))
        old_values = {m.group(1) for m in old}
        prior_values = {m.group(1) for m in prior}
        ok = len(old_values) == 1 and old_values.issubset(prior_values) and len({m.group(1) for m in new}) == 1
        comparisons["bank_account"] = {"matches_previous": ok,
            "revision_before_quotes": [quote(text, m) for m in old],
            "previous_quotes": [quote(previous["article_text"], m) for m in prior],
            "new_values": [m.group(1) for m in new]}
        if not ok:
            reasons.append("ACCOUNT_CONTINUITY_UNRESOLVED")
    else:
        old = schedule(text[before.end():after.start()], before.end())
        prior = schedule(previous["article_text"])
        # A prior revision has both before and after values: compare only its
        # explicitly changed section, preserving its full article separately.
        prior_scope = previous.get("change_scope_review", {})
        if prior_scope.get("scope") == "SCHEDULE_WITH_OTHER_TERMS_UNCHANGED":
            changed_prior = prior_scope["changed_text_for_review"]
            prior = schedule(changed_prior, previous["article_text"].index(changed_prior))
        changed = scope["changed_text_for_review"]
        after_values = schedule(changed, text.index(changed))
        if not old or not after_values:
            reasons.append("SCHEDULE_FIELDS_NOT_EXTRACTED")
        for key, value in old.items():
            previous_value = prior.get(key)
            ok = (len(value["values"]) == 1 and previous_value is not None
                  and len(previous_value["values"]) == 1 and value["values"] == previous_value["values"])
            comparisons[key] = {"matches_previous": ok, "revision_before": value,
                                "previous": previous_value}
            if not ok:
                reasons.append("PREDECESSOR_SCHEDULE_GAP:" + key)
        if any(len(v["values"]) != 1 for v in after_values.values()):
            reasons.append("AMBIGUOUS_CHANGED_SCHEDULE")
        if set(old) - set(after_values):
            reasons.append("CHANGED_SCHEDULE_FIELDS_MISSING")
    return {
        "previous_source_url": previous["source_url"], "revision_source_url": revision["source_url"],
        "explicit_body_ticker_quotes": [quote(text, m) for m in tickers],
        "explicit_record_date_quotes": [quote(text, m) for m in dates],
        "shared_rights_codes": shared, "change_scope": scope["scope"],
        "before_after_comparisons": comparisons, "changed_schedule": after_values,
        "other_terms_unchanged_quote": scope["other_terms_unchanged_quote"],
        "notice_references": scope["notice_references"],
        "notice_ids_with_conflicting_date_literals": scope["notice_ids_with_conflicting_date_literals"],
        "contextual_link_supported": not reasons, "hold_reasons": sorted(set(reasons)),
        "official_notice_number_to_article_binding_verified": False,
        "lineage_approved": False, "historical_identity_verified": False,
        "publication_timestamp_inferred": False, "terminal_execution_confirmed": False,
    }


def review_case(request, original, revisions):
    previous = original
    edges = []
    for revision in revisions:
        edges.append(review_edge(original, previous, revision, request["ticker"], request["original_record_date_review_view"]))
        previous = revision
    supported = bool(edges) and all(e["contextual_link_supported"] for e in edges)
    status = "CONTEXTUAL_FIELD_PROPOSAL_PENDING_APPROVAL" if supported else "HOLD_LINEAGE_GAP_OR_ANOMALY"
    fields = {"rights_subscription_price": request["conditional_price_selection_after_lineage_review"]}
    if request["conditional_exact_source_ratio_after_lineage_review"] is not None:
        fields["rights_ratio"] = request["conditional_exact_source_ratio_after_lineage_review"]
    return {"ticker": request["ticker"], "record_date_review_view": request["original_record_date_review_view"],
        "vci_payload_sha256": request["vci_payload_sha256"], "status": status,
        "original_sdk_row": request["original_sdk_row"], "sources": request["sources"],
        "edges": edges, "observed_fields_for_owner_review": fields,
        "hold_reasons": sorted({reason for e in edges for reason in e["hold_reasons"]}),
        "approval_status": "MANUAL_REVIEW_REQUIRED", "owner_decision": None,
        "applied_fields": 0, "canonical_written": False, "revision_flags_preserved": True,
        "scope": "CACHED_CONTEXT_ONLY_NOT_COMPLETE_ARCHIVE_OR_SIGNED_NOTICE_BINDING"}
