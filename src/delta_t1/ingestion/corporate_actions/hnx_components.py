"""Offline popup v2: explicit component boundaries and allocation wording only."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re

from ..corporate_action_sources import Document, kinds, terms, vi_number
from ..hnx_announcement_parser import _parse_content
from ..hnx_detail_parser import parse_popup as legacy_popup, _parse_details

VERSION = "hnx-desktop-popup-components-v2"
HEADINGS = {
    "trả cổ phiếu thưởng cho cổ đông hiện hữu": "BONUS_SHARE",
    "phát hành cổ phiếu cho cổ đông hiện hữu": "RIGHTS_ISSUE",
    "trả cổ tức bằng cổ phiếu cho cổ đông hiện hữu": "STOCK_DIVIDEND",
    "trả cổ tức bằng tiền": "CASH_DIVIDEND",
}


def terms_v2(kind, fragment, raw_values=None):
    """Retain OLD:NEW proof; accept the explicit optional word 'thêm'."""
    raw_values = raw_values if raw_values is not None else {}
    values, issues = terms(kind, fragment, raw_values)
    if kind not in {"STOCK_DIVIDEND", "BONUS_SHARE"}:
        return values, issues
    colon = set(re.findall(r"tỷ lệ (?:thực hiện|phát hành|quyền mua)\s*[:=]\s*(\d+(?:,\d+)?)\s*:\s*(\d+(?:,\d+)?)", fragment, re.I))
    percent = re.search(r"tỷ lệ (?:thực hiện|phát hành|cổ tức|thưởng|quyền mua)\s*[:=]\s*[\d.,]+\s*%", fragment, re.I)
    if len(colon) != 1 or percent:
        return values, issues
    pairs = re.findall(r"(?:sở hữu|có)\s*(\d+(?:,\d+)?)\s*cổ phiếu\s+(?:sẽ\s+)?(?:được\s+)?nhận\s+(?:thêm\s+)?(\d+(?:,\d+)?)\s*cổ phiếu\s+mới\b", fragment, re.I)
    old, new = next(iter(colon))
    normalized = lambda pair: tuple(Decimal(vi_number(n)) for n in pair)
    if pairs and {normalized(pair) for pair in pairs} != {normalized((old, new))}:
        field = "stock_dividend_ratio" if kind == "STOCK_DIVIDEND" else "bonus_ratio"
        values.pop(field, None)
        values.pop("ratio_semantics", None)
        raw_values.pop(field, None)
        return values, list(dict.fromkeys([*issues, "RATIO_PARSE_AMBIGUITY"]))
    if "RATIO_PARSE_AMBIGUITY" not in issues or not pairs:
        return values, issues
    field = "stock_dividend_ratio" if kind == "STOCK_DIVIDEND" else "bonus_ratio"
    if Decimal(vi_number(old)) <= 0 or Decimal(vi_number(new)) <= 0:
        return values, issues
    values.update({field: vi_number(old) + ":" + vi_number(new), "ratio_semantics": "OLD:NEW"})
    raw_values[field] = old + ":" + new
    return values, [p for p in issues if p != "RATIO_PARSE_AMBIGUITY"]


def parse_popup_components(html, detail_receipt, list_record, list_receipt):
    # Validate the unmodified full article first, including receipt/article/title/ticker joins.
    legacy = legacy_popup(html, detail_receipt, list_record, list_receipt)
    root = Document(html).root
    raw = root.find(cls="Box-Noidung")[0].text()
    markers = list(re.finditer(r"(?<!\S)\*\s+([^:*]{1,180}):", raw))

    def parse(fragment, title):
        obs = _parse_content(fragment, title, list_record["list_time_raw"], detail_receipt,
            list_record["ticker_filter"], list_record["exchange_filter"], timing_evidence=list_receipt,
            parser_version=VERSION, event_reference=legacy["event_reference"], term_parser=terms_v2)
        obs["observed_at"] = legacy["observed_at"]
        obs["source_timing"].update(provider_article_id=list_record["provider_article_id"],
            clock_location="DISCLOSURE_LIST_NOT_DETAIL_POPUP")
        if legacy["revision_status"] != "ORIGINAL":
            obs["revision_status"] = legacy["revision_status"]
            if "REVISION_OR_CORRECTION_DETECTED" not in obs["parser_issues"]:
                obs["parser_issues"].append("REVISION_OR_CORRECTION_DETECTED")
        return obs

    if len(markers) < 2:
        return [parse(raw, list_record["title"])]
    headings = [" ".join(m[1].casefold().split()) for m in markers]
    component_kinds = [HEADINGS.get(h) for h in headings]
    # Unknown/duplicate headings do not permit partial component extraction.
    if None in component_kinds or len(set(component_kinds)) != len(component_kinds):
        legacy["parser_issues"] = list(dict.fromkeys([*legacy["parser_issues"],
            "MIXED_OR_UNKNOWN_EVENT_TYPE:UNRESOLVED_COMPONENT_BOUNDARIES"]))
        legacy["parser"] = VERSION
        legacy["source_timing"]["parser_version"] = VERSION
        return [legacy]
    prefix = raw[:markers[0].start()]
    prepared = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(raw)
        block = raw[marker.start():end]
        kind = component_kinds[i]
        if set(kinds(block)) != {kind}:
            legacy["parser_issues"] = list(dict.fromkeys([*legacy["parser_issues"],
                "MIXED_OR_UNKNOWN_EVENT_TYPE:COMPONENT_CONTENT_CONFLICT"]))
            legacy["parser"] = VERSION
            legacy["source_timing"]["parser_version"] = VERSION
            return [legacy]
        prepared.append((marker, end, block, kind))
    observations = []
    for marker, end, block, kind in prepared:
        obs = parse(prefix + block, marker[1])
        if obs["fields"]["event_type"]["normalized_value"] != kind:
            raise ValueError("COMPONENT_KIND_SCOPE_MISMATCH")
        obs["component_evidence"] = {"basis": "EXPLICIT_STAR_HEADING_IN_SAME_ARTICLE",
            "provider_article_id": list_record["provider_article_id"], "component_kind": kind,
            "heading_raw": marker[1], "common_prefix_text": prefix, "component_text": block,
            "flattened_body_start": marker.start(), "flattened_body_end": end,
            "full_article_raw_terms": raw, "historical_event_identity_certified": False}
        observations.append(obs)
    return observations


def parse_details_v2(details, output):
    return _parse_details(details, output, popup_parser=parse_popup_components, version=VERSION,
        additional_code_files=[Path(__file__)])
