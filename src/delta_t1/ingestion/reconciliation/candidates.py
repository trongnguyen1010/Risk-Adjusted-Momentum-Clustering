"""Field-level candidates retain provider and canonical identities separately."""
from dataclasses import dataclass, field
import hashlib
import json


@dataclass(frozen=True)
class CandidateRecord:
    table: str
    canonical_key: tuple
    comparison_key: tuple
    row: dict
    source: str
    fetched_at: str
    raw_hash: str | None = None
    transform_version: str = "1.0"
    provider_identity: str | None = None
    field_semantics: dict[str, dict] = field(default_factory=dict)

    @property
    def key(self) -> tuple:
        """Compatibility alias: reconciliation groups by semantic comparison key."""
        return self.comparison_key


KEY_FIELDS = {
    "prices_daily": ("security_id", "trade_date"),
    "benchmark_daily": ("index_id", "trade_date"),
    "securities": ("security_id", "valid_from"),
    "financial_reports": ("report_id",),
    "financial_facts": ("report_id", "statement_type", "item_code"),
}

FINANCIAL_REPORT_COMPARISON_FIELDS = (
    "security_id", "fiscal_year", "fiscal_quarter", "period_end",
    "statement_scope", "revision",
)


def financial_report_comparison_key(row: dict) -> tuple:
    """Semantic report identity after fiscal/vintage semantics are normalized."""
    try:
        return tuple(row[field] for field in FINANCIAL_REPORT_COMPARISON_FIELDS)
    except KeyError as exc:
        raise ValueError("financial report comparison key is incomplete") from exc


def canonical_report_id(report_key: tuple) -> str:
    """Stable canonical ID; provider IDs remain candidate provenance."""
    payload = json.dumps(list(report_key), ensure_ascii=False, separators=(",", ":"))
    return "DELTA-REPORT-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def candidate_from_row(table: str, row: dict, *, raw_hash: str | None = None,
                       transform_version: str = "1.0",
                       report_comparison_key: tuple | None = None,
                       field_semantics: dict[str, dict] | None = None,
                       provider_identity: str | None = None) -> CandidateRecord:
    try:
        canonical_key = tuple(row[field] for field in KEY_FIELDS[table])
    except KeyError as exc:
        raise ValueError("candidate table/key is unsupported or incomplete: " + table) from exc
    if table == "financial_reports":
        comparison_key = financial_report_comparison_key(row)
        provider_identity = provider_identity or row["report_id"]
    elif table == "financial_facts" and report_comparison_key is not None:
        comparison_key = tuple(report_comparison_key) + (
            row["statement_type"], row["item_code"]
        )
        provider_identity = provider_identity or row["report_id"]
    else:
        comparison_key = canonical_key
        if table == "financial_facts":
            provider_identity = provider_identity or row["report_id"]
    return CandidateRecord(
        table=table,
        canonical_key=canonical_key,
        comparison_key=comparison_key,
        row=dict(row),
        source=row["source"],
        fetched_at=row["fetched_at"],
        raw_hash=raw_hash,
        transform_version=transform_version,
        provider_identity=provider_identity,
        field_semantics=dict(field_semantics or {}),
    )
