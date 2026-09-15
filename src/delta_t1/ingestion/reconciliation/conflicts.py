"""Serializable conflict records; unresolved conflicts are never silently averaged."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConflictRecord:
    table: str
    key: tuple
    reason: str
    sources: tuple[str, ...]

    def as_dict(self) -> dict:
        value = asdict(self)
        value["key"] = list(self.key)
        value["sources"] = list(self.sources)
        return value
