"""Normalized candidate records retain provenance before conflict resolution."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateRecord:
    table: str
    key: tuple
    row: dict
    source: str
    fetched_at: str
    raw_hash: str | None = None
    transform_version: str = "1.0"


KEY_FIELDS = {
    "prices_daily": ("security_id", "trade_date"),
    "benchmark_daily": ("index_id", "trade_date"),
    "securities": ("security_id", "valid_from"),
    "financial_reports": ("report_id",),
    "financial_facts": ("report_id", "item_code"),
}


def candidate_from_row(table: str, row: dict, *, raw_hash: str | None = None,
                       transform_version: str = "1.0") -> CandidateRecord:
    try:
        key = tuple(row[field] for field in KEY_FIELDS[table])
    except KeyError as exc:
        raise ValueError("candidate table/key is unsupported or incomplete: " + table) from exc
    return CandidateRecord(table=table, key=key, row=dict(row), source=row["source"],
                           fetched_at=row["fetched_at"], raw_hash=raw_hash,
                           transform_version=transform_version)
