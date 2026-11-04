"""Scoped offline candidate review; never resolves historical identity or applies fields."""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
import re

from ..corporate_action_offline_reconcile import (
    KINDS, category, date_view, fact, key, term_agreement, valid_fields,
)
from ..corporate_action_owner_packet import field_choice
from ..corporate_action_sources import vi_number

PENDING = "EVIDENCE_AVAILABLE_PENDING_OWNER_REVIEW"
MISSING = "STILL_MISSING_NO_MATCHING_SCOPED_EVIDENCE"


def compare(observation, row):
    """Both exact dates plus same component and economic term, for review only."""
    values = valid_fields(observation)
    kind = values.get("event_type")
    reasons = []
    if values.get("ticker") != row.get("symbol"):
        reasons.append("TICKER_DIFFERENT")
    if kind != category(row):
        reasons.append("COMPONENT_TYPE_DIFFERENT")
    for field, source in (("ex_date", "ex_right_date"), ("record_date", "record_date")):
        left, right = values.get(field), date_view(row.get(source))
        if not left or not right:
            reasons.append(field.upper() + "_NOT_COMPARABLE")
        elif left != right:
            reasons.append(field.upper() + "_DIFFERENT")
    source_term = values.get(KINDS.get(kind, "cash_dividend_per_share"))
    sdk_term = row.get("value") if kind == "CASH_DIVIDEND" else row.get("ratio")
    agreement = term_agreement(source_term, sdk_term)
    if agreement not in {"EXACT", "SDK_SERIALIZATION_PRECISION_COMPATIBLE"}:
        reasons.append("ECONOMIC_TERM_" + agreement)
    return {"vci_payload_sha256": key(row), "original_sdk_row": deepcopy(row),
        "status": "EXACT_DATES_COMPONENT_TERMS_CANDIDATE" if not reasons else "NOT_MATCHING_PAYLOAD",
        "reasons": reasons, "term_agreement": agreement,
        "date_basis": "EXISTING_UTC_PLUS_7_REVIEW_VIEW_ONLY_NOT_CANONICAL_TRANSFORMATION"}


def review_observations(observations, sdk_rows, missing_payloads):
    reviews = []
    for obs in observations:
        comparisons = [compare(obs, row) for row in sdk_rows]
        candidates = [r for r in comparisons if r["status"] == "EXACT_DATES_COMPONENT_TERMS_CANDIDATE"]
        status = ("UNIQUE_PAYLOAD_COUNTERPART_CANDIDATE" if len(candidates) == 1 else
            "AMBIGUOUS_PAYLOAD_COUNTERPART" if candidates else "NO_EXACT_PAYLOAD_COUNTERPART")
        reviews.append({"observation_id": obs["observation_id"],
            "provider_article_id": obs["source_timing"]["provider_article_id"],
            "fields": valid_fields(obs), "status": status, "comparisons": comparisons,
            "candidate_payload_hashes": [c["vci_payload_sha256"] for c in candidates],
            "candidate_in_missing_queue": [c["vci_payload_sha256"] for c in candidates
                if c["vci_payload_sha256"] in missing_payloads],
            "parser_issues_preserved": deepcopy(obs["parser_issues"]),
            "event_identity_certified": False, "pit_promoted": False, "review_status": "MANUAL_REVIEW_REQUIRED"})
    return reviews


def field_queue(queue, observations, observation_reviews):
    """Add review dispositions without changing any original queue column or row."""
    by_id = {o["observation_id"]: o for o in observations}
    eligible = {}
    for review in observation_reviews:
        if review["status"] == "UNIQUE_PAYLOAD_COUNTERPART_CANDIDATE":
            payload, = review["candidate_payload_hashes"]
            eligible.setdefault(payload, []).append(by_id[review["observation_id"]])
    revised, tasks = [], []
    for original in queue:
        row = deepcopy(original)
        payload = original["vci_payload_sha256"]
        if key(original["original_sdk_row"]) != payload:
            raise ValueError("QUEUE_PAYLOAD_HASH_MISMATCH")
        reviews = {}
        for field in original["missing_fields"]:
            candidates = []
            for obs in eligible.get(payload, []):
                value = valid_fields(obs).get(field)
                if value is not None:
                    candidates.append({"observation_id": obs["observation_id"], "value": value,
                        "provider_article_id": obs["source_timing"]["provider_article_id"],
                        "parser_issues_preserved": deepcopy(obs["parser_issues"])})
            values = {format(Decimal(str(c["value"])).normalize(), "f")
                if isinstance(c["value"], (int, float)) and not isinstance(c["value"], bool)
                else str(c["value"]) for c in candidates}
            status = PENDING if len(values) == 1 else "CONFLICTING_CANDIDATES_PENDING_REVIEW" if values else MISSING
            entry = {"status": status, "candidates": candidates, "owner_decision": None,
                "field_approved": False, "field_applied": False, "canonical_missing_unchanged": True}
            reviews[field] = entry
            tasks.append({"ticker": row["ticker"], "vci_payload_sha256": payload, "field": field, **entry})
        row["scoped_hnx_review_v2"] = reviews
        revised.append(row)
    return revised, tasks


def price_proposal(task, observation, source_location, original_sdk_row):
    """Unsigned existing-rule price proposal with an explicit primary unit quote."""
    values = valid_fields(observation)
    if (key(original_sdk_row) != task["vci_payload_sha256"]
            or compare(observation, original_sdk_row)["status"] != "EXACT_DATES_COMPONENT_TERMS_CANDIDATE"):
        raise ValueError("EXACT_PAYLOAD_COMPONENT_DATES_TERMS_REQUIRED")
    if (task["field"] != "rights_subscription_price" or task["status"] != PENDING
            or values.get("event_type") != "RIGHTS_ISSUE" or values.get("currency") != "VND"
            or {c["observation_id"] for c in task["candidates"]} != {observation["observation_id"]}):
        raise ValueError("EXACT_UNIQUE_RIGHTS_PRICE_TASK_REQUIRED")
    component = observation.get("component_evidence", {}).get("component_text")
    if not component or observation["component_evidence"]["component_kind"] != "RIGHTS_ISSUE":
        raise ValueError("ISOLATED_RIGHTS_COMPONENT_REQUIRED")
    pattern = r"giá (?:phát hành|chào bán|đăng ký mua)\s*[:=]\s*([\d.,]+)\s*đồng\s*/\s*(?:cổ phiếu|cổ phần|cp\b)"
    hits = list(re.finditer(pattern, component, re.I))
    price = Decimal(str(values.get("rights_subscription_price")))
    if not price.is_finite() or price <= 0 or price != price.to_integral_value():
        raise ValueError("POSITIVE_EXPLICIT_VND_SHARE_PRICE_REQUIRED")
    if any(Decimal(str(c["value"])) != price for c in task["candidates"]):
        raise ValueError("TASK_PRICE_DIFFERS_FROM_SOURCE")
    if not hits or {Decimal(vi_number(h[1])) for h in hits} != {price}:
        raise ValueError("PRIMARY_PRICE_AND_UNIT_NOT_SUPPORTED_IN_COMPONENT")
    evidence = fact(observation, source_location)
    choice = field_choice(task["vci_payload_sha256"], task["field"], str(int(price)), [evidence["evidence_id"]],
        conditions=["CONFIRM_EXACT_PAYLOAD_COMPONENT_AND_BOTH_DATES", "CONFIRM_PRIMARY_PRICE_QUOTE_AND_UNIT",
            "CONFIRM_NO_UNRESOLVED_REVISION_OR_COMPETING_FIELD_EVIDENCE", "PIT_AND_HISTORICAL_IDENTITY_REMAIN_SEPARATE"])
    return {"ticker": values["ticker"], "vci_payload_sha256": task["vci_payload_sha256"],
        "decision_class": "EXISTING_RULE_PRICE_SELECTION_PROPOSAL", "proposed_fields": [choice],
        "evidence": {**evidence, "component_evidence": deepcopy(observation["component_evidence"]),
            "primary_price_quotes": [h.group() for h in hits], "observed_at": observation["observed_at"]},
        "owner_decision": None, "signature_created": False, "canonical_written": False,
        "importable_as_production_decisions": False, "historical_identity": "UNVERIFIED",
        "pit_status": "NOT_PROMOTED", "review_status": "MANUAL_REVIEW_REQUIRED"}


def disposition_counts(tasks):
    return dict(Counter(t["status"] for t in tasks))
