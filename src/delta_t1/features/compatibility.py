"""Explicit read-only compatibility for legacy feature snapshots."""
from ..contracts import validate_rows


LEGACY_SNAPSHOT_CONTRACT = "feature_snapshots_legacy_1_3_0"
LEGACY_1_4_SNAPSHOT_CONTRACT = "feature_snapshots_legacy_1_4_0"
LEGACY_PORTFOLIO_FIELDS = {"sharpe_63", "sharpe_126"}


def validate_legacy_feature_snapshots(rows: list[dict]) -> None:
    """Validate immutable 1.3 snapshots without treating them as active features."""
    validate_rows(LEGACY_SNAPSHOT_CONTRACT, rows)


def validate_legacy_1_4_feature_snapshots(rows: list[dict]) -> None:
    """Validate immutable 1.4 snapshots created before readiness separation."""
    validate_rows(LEGACY_1_4_SNAPSHOT_CONTRACT, rows)


def project_legacy_snapshot(row: dict) -> dict:
    """Return a non-mutating research projection with portfolio fields removed."""
    return {key: value for key, value in row.items() if key not in LEGACY_PORTFOLIO_FIELDS}
