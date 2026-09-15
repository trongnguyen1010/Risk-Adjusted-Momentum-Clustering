"""Deterministic field-level reconciliation over normalized candidates."""
from collections import defaultdict
from dataclasses import dataclass
import json

from .candidates import canonical_report_id
from .conflicts import ConflictRecord


MATCH = "MATCH"
MISSING_ON_SOURCE = "MISSING_ON_SOURCE"
VALUE_CONFLICT = "VALUE_CONFLICT"
UNIT_CONFLICT = "UNIT_CONFLICT"
PRICE_BASIS_CONFLICT = "PRICE_BASIS_CONFLICT"
TIMING_CONFLICT = "TIMING_CONFLICT"
IDENTITY_CONFLICT = "IDENTITY_CONFLICT"

PROVENANCE_FIELDS = {
    "source", "fetched_at", "data_version", "source_document_id",
    "source_document_hash",
}
TIMING_FIELDS = {"available_at", "published_at"}
IDENTITY_FIELDS = {"security_id", "ticker", "exchange", "valid_from", "valid_to"}
PRICE_FIELDS = {
    "raw_open", "raw_high", "raw_low", "raw_close", "adj_close",
    "reference_price", "ceiling_price", "floor_price", "close",
}


@dataclass(frozen=True)
class SourcePriorityPolicy:
    sources: tuple[str, ...]
    approved: bool
    rule_id: str
    version: str
    reason: str

    @classmethod
    def from_dict(cls, value: dict) -> "SourcePriorityPolicy":
        policy = cls(
            sources=tuple(value.get("sources", ())),
            approved=value.get("approved") is True,
            rule_id=value.get("rule_id", ""),
            version=value.get("version", ""),
            reason=value.get("reason", ""),
        )
        if (not policy.approved or not policy.sources or len(policy.sources) != len(set(policy.sources))
                or not policy.rule_id or not policy.version or not policy.reason):
            raise ValueError("source-priority policy must be explicitly approved and versioned")
        return policy


def _encoded(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _semantics(candidate, field: str) -> dict:
    explicit = candidate.field_semantics.get(field, {})
    unit = explicit.get("unit")
    if field == "value":
        unit = unit or (candidate.row.get("currency"), candidate.row.get("unit_scale"))
    basis = explicit.get("price_basis")
    if field in PRICE_FIELDS or field == "adjustment_basis":
        basis = basis or candidate.row.get("adjustment_basis") or candidate.row.get("index_basis")
    return {"unit": unit, "price_basis": basis}


def _status(values, field: str) -> str:
    present = [candidate.row.get(field) for candidate in values]
    semantics = [_semantics(candidate, field) for candidate in values]
    units = {_encoded(item["unit"]) for item in semantics if item["unit"] is not None}
    bases = {_encoded(item["price_basis"]) for item in semantics if item["price_basis"] is not None}
    distinct = {_encoded(value) for value in present}
    if len(bases) > 1:
        return PRICE_BASIS_CONFLICT
    if len(units) > 1:
        return UNIT_CONFLICT
    if any(value is None for value in present) and any(value is not None for value in present):
        return MISSING_ON_SOURCE
    if len(distinct) <= 1:
        return MATCH
    if field in TIMING_FIELDS:
        return TIMING_CONFLICT
    if field in IDENTITY_FIELDS:
        return IDENTITY_CONFLICT
    if field in ("adjustment_basis", "index_basis"):
        return PRICE_BASIS_CONFLICT
    return VALUE_CONFLICT


def _rank(values, policy: SourcePriorityPolicy | None):
    priority = ({source: index for index, source in enumerate(policy.sources)}
                if policy else {})
    return sorted(values, key=lambda item: (
        priority.get(item.source, len(priority)), item.source, item.fetched_at,
        item.raw_hash or "",
    ))


def _canonical_key(table: str, values) -> tuple:
    if table == "financial_facts" and len(values[0].comparison_key) < 8:
        return values[0].canonical_key
    if table in ("financial_reports", "financial_facts"):
        report_key = values[0].comparison_key[:6]
        if table == "financial_reports":
            return (canonical_report_id(report_key),)
        return (canonical_report_id(report_key), *values[0].comparison_key[6:])
    return values[0].canonical_key


def reconcile_candidates(candidates, source_priority: SourcePriorityPolicy | None = None
                         ) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    """Compare economic fields, retaining a decision record for every field."""
    if source_priority is not None and not isinstance(source_priority, SourcePriorityPolicy):
        raise ValueError("source priority requires an explicit approved SourcePriorityPolicy")
    groups = defaultdict(list)
    for candidate in candidates:
        groups[(candidate.table, candidate.comparison_key)].append(candidate)
    output = defaultdict(list)
    decisions, conflicts = [], []
    for (table, comparison_key), values in sorted(
            groups.items(), key=lambda item: (item[0][0], repr(item[0][1]))):
        ranked = _rank(values, source_priority)
        canonical_key = _canonical_key(table, ranked)
        base = ranked[0]
        row = dict(base.row)
        fields = sorted(set().union(*(candidate.row for candidate in values)) - PROVENANCE_FIELDS)
        if table in ("financial_reports", "financial_facts"):
            fields.remove("report_id")
            row["report_id"] = canonical_key[0]
        unresolved = False
        for field in fields:
            status = _status(values, field)
            available = [candidate for candidate in ranked if candidate.row.get(field) is not None]
            chosen = available[0] if available else ranked[0]
            resolution = "RESOLVED"
            reason = "normalized values match"
            if status == MISSING_ON_SOURCE:
                reason = "field is missing on at least one source; retained available normalized value"
            elif status == VALUE_CONFLICT:
                priority_sources = source_priority.sources if source_priority else ()
                can_choose = (source_priority is not None and chosen.source in priority_sources
                              and sum(item.source == chosen.source for item in values) == 1)
                if not can_choose:
                    resolution, unresolved = "UNRESOLVED", True
                    reason = "different compatible values require an approved source-priority policy"
                else:
                    reason = source_priority.reason
            elif status in (UNIT_CONFLICT, PRICE_BASIS_CONFLICT, TIMING_CONFLICT, IDENTITY_CONFLICT):
                resolution, unresolved = "UNRESOLVED", True
                reason = "incompatible semantics cannot be resolved by source priority"
            rule_id = source_priority.rule_id if status == VALUE_CONFLICT and resolution == "RESOLVED" else "field_reconciliation"
            rule_version = source_priority.version if status == VALUE_CONFLICT and resolution == "RESOLVED" else "2.0"
            candidate_values = []
            for candidate in sorted(values, key=lambda item: (item.source, item.fetched_at)):
                semantic = _semantics(candidate, field)
                candidate_values.append({
                    "source": candidate.source,
                    "value": candidate.row.get(field),
                    "unit": semantic["unit"],
                    "price_basis": semantic["price_basis"],
                    "available_at": candidate.row.get("available_at"),
                    "raw_hash": candidate.raw_hash,
                    "provider_identity": candidate.provider_identity,
                })
            decisions.append({
                "table": table,
                "canonical_key": list(canonical_key),
                "comparison_key": list(comparison_key),
                "field": field,
                "status": status,
                "resolution_status": resolution,
                "candidate_sources": sorted({item.source for item in values}),
                "normalized_candidate_values": candidate_values,
                "chosen_source": chosen.source if resolution == "RESOLVED" else None,
                "chosen_value": chosen.row.get(field) if resolution == "RESOLVED" else None,
                "rule_id": rule_id,
                "rule_version": rule_version,
                "reason": reason,
                "raw_hashes": sorted({item.raw_hash for item in values if item.raw_hash}),
            })
            if resolution == "RESOLVED":
                row[field] = chosen.row.get(field)
            else:
                conflicts.append(ConflictRecord(
                    table=table,
                    canonical_key=canonical_key,
                    comparison_key=comparison_key,
                    field=field,
                    status=status,
                    reason=reason,
                    sources=tuple(sorted({item.source for item in values})),
                    raw_hashes=tuple(sorted({item.raw_hash for item in values if item.raw_hash})),
                ).as_dict())
        if not unresolved:
            if len({item.source for item in values}) > 1:
                row["source"] = "reconciled"
                row["fetched_at"] = max(item.fetched_at for item in values)
            output[table].append(row)
    return dict(output), decisions, conflicts
