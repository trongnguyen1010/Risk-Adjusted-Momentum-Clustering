"""Offline query coverage diagnostics; query exhaustion is not event coverage."""
import re
from pathlib import Path
from ..corporate_action_sources import Document
from ..corporate_action_sources import sha


def is_deferred_pagination(reason):
    return isinstance(reason, str) and reason.startswith("PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400")


def snapshot_coverage(body, discovered_ids):
    html = body.decode("utf-8-sig")
    # Keep parsing bounded to the displayed footer; scripts elsewhere are not evidence.
    hit = html.find("Hiển thị:")
    excerpt = html[max(0, hit - 100):hit + 1500] if hit >= 0 else html
    text = Document(excerpt).root.text()
    matches = list(re.finditer(r"Hiển thị:\s*(\d+)\s*-\s*(\d+)\s*/\s*(\d+)\s*bản ghi", text, re.I))
    result = {"query_status": "SEARCH_LAYOUT_UNVERIFIED", "reported_total": None,
        "known_list_ids": len(set(discovered_ids)), "unseen_query_row_slots": None,
        "historical_event_coverage_certified": False, "source_requests_authorized": False}
    if len(matches) != 1:
        return result
    first, last, total = map(int, matches[0].groups())
    result.update(first=first, last=last, reported_total=total, coverage_quote=matches[0].group())
    if total == 0 and first == last == 0 and not discovered_ids:
        return dict(result, query_status="EMPTY_QUERY_NOT_NO_EVENTS", unseen_query_row_slots=0)
    if not (1 <= first <= last <= total) or last - first + 1 != len(set(discovered_ids)):
        return dict(result, query_status="SEARCH_COUNT_OR_LINKS_INCONSISTENT")
    unseen = total - len(set(discovered_ids))
    return dict(result, query_status="QUERY_LIST_INCOMPLETE" if unseen else "SAVED_QUERY_EXHAUSTED_NOT_HISTORY_CERTIFIED",
        unseen_query_row_slots=unseen)


def physical_failures(failures):
    """One archived request can occur in parent/child/replay ledgers; retain refs."""
    grouped = {}
    for row in failures:
        receipt = row["receipt"]
        if "/vi/search" not in receipt.get("url", ""):
            continue
        key = tuple(receipt.get(k) for k in ("url", "method", "request_body", "fetched_at", "status", "source_hash"))
        record = grouped.setdefault(key, {"receipt": receipt, "ledger_references": []})
        record["ledger_references"].append({"path": row["ledger"], "index": row["index"]})
    return list(grouped.values())


def supplementation_scope(coverage, known_urls, cached_urls):
    return {"requires_pagination_protocol_review": coverage["query_status"] == "QUERY_LIST_INCOMPLETE",
        "query_rows_not_yet_discovered": coverage["unseen_query_row_slots"],
        "known_url_count": len(set(known_urls)), "known_urls_without_raw": sorted(set(known_urls) - set(cached_urls)),
        "known_urls_reusable_from_cache": len(set(known_urls) & set(cached_urls)),
        "redownload_existing_details": False, "bulk_acquisition_authorized": False,
        "new_detail_request_count": "UNKNOWN_UNTIL_NEW_PAGES_ARE_DISCOVERED_DEDUPED_AND_SCOPED"}


def locate_receipt_body(candidates, expected_hash):
    """Merged parent ledgers can retain child-relative raw names; verify all refs."""
    rejected = []
    for candidate in dict.fromkeys(map(Path, candidates)):
        if not candidate.is_file():
            continue
        actual = sha(candidate.read_bytes())
        if actual == expected_hash:
            return candidate, rejected
        rejected.append({"path": str(candidate), "sha256": actual,
            "reason": "RELATIVE_CANDIDATE_DOES_NOT_MATCH_RECEIPT_HASH_NOT_SELECTED_AS_ORIGIN"})
    raise ValueError("NO_RECEIPT_BODY_WITH_EXPECTED_HASH")
