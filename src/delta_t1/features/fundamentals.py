"""Financial feature registration boundary; no unapproved ratio definitions."""
from .registry import FeatureDefinition, FeatureRegistry


def register_financial_feature(registry: FeatureRegistry, definition: FeatureDefinition) -> None:
    """Register an approved, cited PIT financial definition."""
    if definition.family != "fundamental":
        raise ValueError("financial feature family must be fundamental")
    if definition.point_in_time_rule.strip().lower() in ("", "none", "n/a"):
        raise ValueError("financial feature requires an explicit point-in-time rule")
    if definition.reference.strip().lower() in ("", "pending", "n/a"):
        raise ValueError("financial feature requires an approved reference/citation")
    registry.register(definition)


def build_fundamental_features(*, definitions: list[FeatureDefinition], reports: list[dict],
                               facts: list[dict], security_id: str, decision_at: str) -> dict:
    """Fail closed until concrete paper-backed calculators are approved."""
    if definitions:
        raise NotImplementedError(
            "Concrete fundamental calculators require approved taxonomy, formula and PIT methodology"
        )
    return {}
