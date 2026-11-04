"""Đối chiếu candidate facts offline; không tạo canonical hay tự phê duyệt field."""
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json

KINDS = {"STOCK_DIVIDEND": "stock_dividend_ratio", "BONUS_SHARE": "bonus_ratio",
         "RIGHTS_ISSUE": "rights_ratio"}


def key(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def date_view(value):
    if not value:
        return None
    if len(value) == 10:
        return date.fromisoformat(value).isoformat()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone(timedelta(hours=7))).date().isoformat()


def category(row):
    if row["event_type"] == "DIV":
        return "CASH_DIVIDEND"
    title = row["event_title"].casefold()
    for text, kind in [("trả cổ tức bằng cổ phiếu", "STOCK_DIVIDEND"),
                       ("cổ phiếu thưởng", "BONUS_SHARE"), ("quyền mua", "RIGHTS_ISSUE")]:
        if text in title:
            return kind
    return "OTHER_ISSUANCE_REVIEW"


def valid_fields(observation):
    return {name: field["normalized_value"] for name, field in observation["fields"].items()
            if field.get("parse_status") == "VALID" and field.get("normalized_value") is not None}


def term_agreement(left, right):
    if left is None or right is None:
        return "NOT_COMPARABLE"
    try:
        a, b = Decimal(str(left)), Decimal(str(right))
        if not a.is_finite() or not b.is_finite() or a <= 0 or b <= 0:
            return "NOT_COMPARABLE"
        if a == b:
            return "EXACT"
        quantum = Decimal("0.0000000001")
        if a.quantize(quantum) == b.quantize(quantum):
            return "SDK_SERIALIZATION_PRECISION_COMPATIBLE"
        return "DIFFERENT"
    except (InvalidOperation, ValueError):
        return "NOT_COMPARABLE"


def near(left, right, days):
    return bool(left and right and abs((date.fromisoformat(left) - date.fromisoformat(right)).days) <= days)


def fact(observation, reference):
    values = valid_fields(observation)
    kind = values.get("event_type")
    return {"evidence_id": key({"source": observation["source_type"], "id": observation["observation_id"],
                               "hash": observation["source_hash"], "fields": observation["fields"]}),
            "observation_id": observation["observation_id"], "source_type": observation["source_type"],
            "source_url": observation["source_url"], "source_hash": observation["source_hash"],
            "parser": observation["parser"], "parser_issues": list(observation.get("parser_issues", [])),
            "ticker": values.get("ticker"), "kind": kind, "values": values,
            "term": values.get(KINDS.get(kind, "cash_dividend_per_share")),
            "date_hint": values.get("announcement_date"),
            "fields": observation["fields"], "source_evidence": observation.get("source_evidence", []),
            "locations": [reference]}


def vci_facts(row):
    return {"record_date": date_view(row.get("record_date")),
            "ex_date": date_view(row.get("ex_right_date"))}


def reconcile_row(row, officials, siblings, *, hint_days=120):
    """All output remains provisional, even an exact-date/terms agreement.

    Time hints only retrieve alternatives. No nearest-date/source priority or
    previous-session inference, and no public_date -> available_at conversion.
    """
    kind = category(row)
    existing = vci_facts(row)
    hint = date_view(row.get("public_date"))
    related, sibling_links, conflicts = {}, {}, []

    def attach(source, mode, agreement):
        entry = related.setdefault(source["evidence_id"], {"evidence_id": source["evidence_id"],
            "observation_id": source["observation_id"], "source_type": source["source_type"],
            "modes": [], "term_agreement": agreement, "values": source["values"],
            "parser_issues": source["parser_issues"]})
        if mode not in entry["modes"]:
            entry["modes"].append(mode)

    def consider(source, allow_hint):
        if source["ticker"] != row["symbol"] or source["kind"] != kind:
            return
        values = source["values"]
        agreement = term_agreement(row.get("ratio"), source["term"])
        modes = []
        if existing["record_date"] and values.get("record_date") == existing["record_date"]:
            modes.append("EXACT_RECORD_DATE")
        if existing["ex_date"] and values.get("ex_date") == existing["ex_date"]:
            modes.append("EXACT_EX_DATE")
        if modes and agreement == "DIFFERENT":
            conflicts.append({"evidence_id": source["evidence_id"], "reason": "DATED_EVENT_DIFFERENT_ECONOMIC_TERM"})
            return
        if modes:
            for mode in modes:
                attach(source, mode, agreement)
        elif allow_hint and not any(existing.values()) and agreement in {"EXACT", "SDK_SERIALIZATION_PRECISION_COMPATIBLE"} and near(hint, source["date_hint"], hint_days):
            attach(source, "TIME_HINT_AND_TERMS_CANDIDATE_ONLY", agreement)

    for source in officials:
        consider(source, True)
    if not any(existing.values()):
        for sibling in siblings:
            if key(sibling) == key(row) or sibling["symbol"] != row["symbol"] or category(sibling) != kind:
                continue
            if sibling["event_title"] != row["event_title"]:
                continue
            agreement = term_agreement(row.get("ratio"), sibling.get("ratio"))
            if agreement not in {"EXACT", "SDK_SERIALIZATION_PRECISION_COMPATIBLE"}:
                continue
            if not near(hint, date_view(sibling.get("public_date")), hint_days):
                continue
            values = vci_facts(sibling)
            if not all(values.values()):
                continue
            sibling_links[key(sibling)] = {"vci_payload_sha256": key(sibling), "values": values,
                "mode": "SAME_SDK_TITLE_TERMS_TIME_HINT_NOT_CANONICAL_ID", "term_agreement": agreement}

    # A matching explicit record date can link separate official observations.
    # This never manufactures an ex-date from a record date/calendar lag.
    records = {existing["record_date"]} - {None}
    records.update(x["values"]["record_date"] for x in related.values() if x["values"].get("record_date"))
    records.update(x["values"]["record_date"] for x in sibling_links.values())
    for source in officials:
        if source["ticker"] != row["symbol"] or source["kind"] != kind or source["values"].get("record_date") not in records:
            continue
        agreement = term_agreement(row.get("ratio"), source["term"])
        if agreement == "DIFFERENT":
            conflicts.append({"evidence_id": source["evidence_id"], "reason": "LINKED_RECORD_DATE_DIFFERENT_TERM"})
        else:
            attach(source, "LINKED_EXPLICIT_RECORD_DATE_CANDIDATE_ONLY", agreement)

    explicit_ex_dates = {existing["ex_date"]} - {None}
    explicit_ex_dates.update(x["values"]["ex_date"] for x in related.values() if x["values"].get("ex_date"))
    explicit_ex_dates.update(x["values"]["ex_date"] for x in sibling_links.values())
    for source in officials:
        if source["ticker"] != row["symbol"] or source["kind"] != kind or source["values"].get("ex_date") not in explicit_ex_dates:
            continue
        agreement = term_agreement(row.get("ratio"), source["term"])
        if agreement == "DIFFERENT":
            conflicts.append({"evidence_id": source["evidence_id"], "reason": "LINKED_EX_DATE_DIFFERENT_TERM"})
        else:
            attach(source, "LINKED_EXPLICIT_EX_DATE_CANDIDATE_ONLY", agreement)

    options = {name: defaultdict(list) for name in ("ex_date", "record_date", "rights_subscription_price")}
    for name, value in existing.items():
        if value:
            options[name][value].append({"source": "ORIGINAL_VCI_REVIEW_DATE_VIEW"})
    for entry in related.values():
        for name in ("ex_date", "record_date"):
            value = entry["values"].get(name)
            if value:
                options[name][value].append({"evidence_id": entry["evidence_id"]})
    for entry in sibling_links.values():
        for name, value in entry["values"].items():
            options[name][value].append({"vci_payload_sha256": entry["vci_payload_sha256"]})
    date_ambiguous = any(len(options[name]) > 1 for name in ("ex_date", "record_date"))
    event_ambiguous = date_ambiguous or bool(conflicts)
    # Price evidence must belong to the single possible explicit record date.
    if kind == "RIGHTS_ISSUE" and not event_ambiguous and len(options["record_date"]) == 1:
        for entry in related.values():
            values = entry["values"]
            price = values.get("rights_subscription_price")
            if values.get("record_date") not in options["record_date"] or values.get("currency") != "VND":
                continue
            if price is not None and not isinstance(price, bool) and Decimal(str(price)).is_finite() and price >= 0:
                normalized_key = format(Decimal(str(price)).normalize(), "f")
                options["rights_subscription_price"][normalized_key].append({"evidence_id": entry["evidence_id"]})
    fields = {}
    for name, values in options.items():
        original = existing.get(name)
        single = len(values) == 1 and not event_ambiguous
        proposed = next(iter(values)) if single and not original else None
        if proposed is not None and name == "rights_subscription_price":
            proposed = float(proposed)
        fields[name] = {"original_review_value": original,
            "proposed_value_pending_review": proposed,
            "candidate_values": [{"value": float(value) if name == "rights_subscription_price" else value,
                                  "evidence": refs} for value, refs in sorted(values.items())],
            "status": "ORIGINAL_PRESENT_WITH_CONFLICT" if original and event_ambiguous else
                      "ORIGINAL_PRESENT" if original else "SINGLE_VALUE_PROPOSAL" if proposed is not None else
                      "AMBIGUOUS_EVENT_OR_FIELD" if values or event_ambiguous else "NO_EVIDENCE"}
    return {"vci_payload_sha256": key(row), "ticker": row["symbol"], "category_candidate": kind,
            "original_sdk_row": row, "fields": fields, "official_links": list(related.values()),
            "sdk_sibling_links": list(sibling_links.values()), "economic_term_conflicts": conflicts,
            "event_match_ambiguous": event_ambiguous,
            "all_linked_source_issues": sorted({issue for entry in related.values() for issue in entry["parser_issues"]}),
            "review_status": "MANUAL_REVIEW_REQUIRED", "identity_status": "UNVERIFIED",
            "pit_status": "NOT_PROMOTED", "canonical_promoted": False,
            "date_basis": "UTC_PLUS_7_REVIEW_VIEW_ONLY_CANONICAL_CONVERSION_NOT_APPROVED",
            "time_hint_is_publication_or_available_at": False}
