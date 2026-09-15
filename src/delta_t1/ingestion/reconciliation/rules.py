"""Deterministic reconciliation rules over normalized candidates."""
from collections import defaultdict

from .conflicts import ConflictRecord


def reconcile_candidates(candidates, source_priority: tuple[str, ...] = ()) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    groups = defaultdict(list)
    for candidate in candidates:
        groups[(candidate.table, candidate.key)].append(candidate)
    output = defaultdict(list)
    decisions, conflicts = [], []
    priority = {source: index for index, source in enumerate(source_priority)}
    for (table, key), values in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1])):
        bases = {candidate.row.get("adjustment_basis") or candidate.row.get("index_basis") for candidate in values}
        bases.discard(None)
        if len(bases) > 1:
            conflicts.append(ConflictRecord(table, key, "incompatible_price_basis",
                                            tuple(sorted({item.source for item in values}))).as_dict())
            continue
        unique_rows = {repr(sorted(candidate.row.items())) for candidate in values}
        ranked = sorted(values, key=lambda item: (priority.get(item.source, len(priority)),
                                                   item.source, item.fetched_at, item.raw_hash or ""))
        if len(unique_rows) > 1 and (not priority or len(ranked) > 1
                                     and priority.get(ranked[0].source, len(priority))
                                     == priority.get(ranked[1].source, len(priority))):
            conflicts.append(ConflictRecord(table, key, "conflicting_values_without_unique_priority",
                                            tuple(sorted({item.source for item in values}))).as_dict())
            continue
        chosen = ranked[0]
        output[table].append(chosen.row)
        decisions.append(dict(table=table, key=list(key), chosen_source=chosen.source,
                              rule="identical_or_source_priority_v1", candidate_count=len(values)))
    return dict(output), decisions, conflicts
