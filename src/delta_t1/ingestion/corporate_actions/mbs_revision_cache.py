"""Offline cache limits and revision triage; no negative-history certification."""
import re

from ..corporate_action_sources import Document
from ..corporate_action_decision_packet import link_history


def vsdc_search_coverage(html):
    text = Document(html).root.text()
    matches = list(re.finditer(r"Hiển thị:\s*(\d+)\s*-\s*(\d+)\s*/\s*(\d+)\s*bản ghi", text, re.I))
    if len(matches) != 1:
        raise ValueError("EXPLICIT_VSDC_SEARCH_COVERAGE_REQUIRED")
    first, last, total = map(int, matches[0].groups())
    if not 1 <= first <= last <= total:
        raise ValueError("INCONSISTENT_VSDC_SEARCH_COUNTS")
    return {"first": first, "last": last, "total_reported": total, "rows_on_page": last - first + 1,
        "rows_outside_saved_page": total - (last - first + 1), "quote": matches[0].group(),
        "reported_count_is_query_rows_not_event_count": True}


def classify_document(article, target, *, selected_provider_ids=(), target_rights_codes=()):
    """Reuse existing contextual linker and keep distinct securities/rounds separate."""
    if article.get("ticker") not in {None, "", target["ticker"]}:
        return {"provider_article_id": article["provider_article_id"], "status": "EXCLUDED_OTHER_SECURITY",
            "declared_ticker": article["ticker"], "event_identity_approved": False}
    link = link_history(target, article, selected_provider_ids, target_rights_codes)
    if link["revision_or_cancellation_candidate"]:
        status = "LINKED_CHANGE_REVIEW_REQUIRED"
    elif link["strong_event_reference"] and link["date_conflict"]:
        status = "LINKED_DATE_CONFLICT_REVIEW_REQUIRED"
    elif link["strong_event_reference"]:
        prices = article.get("isolated_rights_prices_vnd", [])
        status = ("LINKED_PRICE_CONFLICT_REVIEW_REQUIRED" if any(p != target["expected_price_vnd"] for p in prices)
            else "TARGET_DOCUMENT_IN_CACHE")
    elif article.get("title_change_markers") or article.get("body_change_quotes"):
        status = "UNLINKED_CHANGE_CANDIDATE_REQUIRES_SCOPE_REVIEW"
    else:
        status = "OTHER_OR_UNLINKED_DOCUMENT"
    return {"provider_article_id": article["provider_article_id"], "status": status,
        "source_url": article["source_url"], "title": article["title"], "declared_ticker": article.get("ticker"),
        "record_dates": article["record_dates"], "contextual_link": link,
        "change_scope_review": article.get("change_scope_review"),
        "event_identity_approved": False, "field_approved": False}


def recommendation(document_reviews, gaps):
    holds = [r for r in document_reviews if r["status"] in {
        "LINKED_CHANGE_REVIEW_REQUIRED", "LINKED_DATE_CONFLICT_REVIEW_REQUIRED", "LINKED_PRICE_CONFLICT_REVIEW_REQUIRED",
        "UNLINKED_CHANGE_CANDIDATE_REQUIRES_SCOPE_REVIEW"}]
    status = ("HOLD_LINKED_CHANGE_OR_SCOPE_CONFLICT" if holds else "HOLD_CACHE_COVERAGE_GAP" if gaps else
        "READY_FOR_OWNER_REVIEW_WITHIN_DECLARED_CACHE_SCOPE" if any(r["status"] == "TARGET_DOCUMENT_IN_CACHE" for r in document_reviews)
        else "HOLD_NO_TARGET_DOCUMENT")
    return {"status": status, "ready_to_recommend_owner_price_approval": status.startswith("READY_"),
        "linked_or_possible_changes_requiring_review": len(holds), "coverage_gaps": gaps,
        "no_revision_exists_certified": False, "source_selection_approved": False,
        "canonical_written": False, "historical_identity_verified": False, "pit_promoted": False}
