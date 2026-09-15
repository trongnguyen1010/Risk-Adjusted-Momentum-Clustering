"""Serializable unresolved field conflicts; values are never averaged."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConflictRecord:
    table: str
    canonical_key: tuple
    comparison_key: tuple
    field: str
    status: str
    reason: str
    sources: tuple[str, ...]
    raw_hashes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        value = asdict(self)
        value["canonical_key"] = list(self.canonical_key)
        value["comparison_key"] = list(self.comparison_key)
        value["sources"] = list(self.sources)
        value["raw_hashes"] = list(self.raw_hashes)
        return value
