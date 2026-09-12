"""Explicit long-only portfolio policies, independent of numeric cluster IDs."""
from datetime import datetime
import math


def weights(rows: list[dict], method: str, risk_feature: str) -> dict[str, float]:
    if method not in ("equal", "inverse_volatility", "diagonal_risk_parity"):
        raise ValueError("unsupported portfolio weighting")
    if not rows:
        return {}
    if method == "equal":
        scores = {r["security_id"]: 1.0 for r in rows}
    else:
        if any(r[risk_feature] is None or not math.isfinite(r[risk_feature]) or r[risk_feature] <= 0 for r in rows):
            raise ValueError("positive volatility required for inverse volatility weights")
        scores = {r["security_id"]: 1 / r[risk_feature] for r in rows}
    if len(scores) != len(rows):
        raise ValueError("duplicate portfolio security")
    total = sum(scores.values())
    return {sid: value / total for sid, value in sorted(scores.items())}


def make_targets(snapshot: dict, config: dict, strategy: str = "cluster") -> dict:
    rows = snapshot["rows"]
    if not rows or any(not r["eligibility"] for r in rows):
        raise ValueError("targets require eligible snapshot")
    if strategy == "cluster":
        candidates = [p for p in snapshot["profiles"] if p["semantic_label"] == config["semantic_label"]]
        winner = min(candidates, key=lambda p: (-p["centroid"][config["selection_feature"]], p["raw_cluster_id"])) if candidates else None
        rows = [r for r, c in zip(rows, snapshot["labels"]) if winner and c == winner["raw_cluster_id"]]
    elif strategy == "momentum_only":
        rows = sorted(rows, key=lambda r: (-r[config["momentum_feature"]], r["security_id"]))[:config["top_n"]]
    elif strategy == "risk_only":
        rows = sorted(rows, key=lambda r: (r[config["risk_feature"]], r["security_id"]))[:config["top_n"]]
    elif strategy != "equal_weight_universe":
        raise ValueError("unsupported strategy")
    allocation = weights(rows, config["weighting"], config["risk_feature"])
    return dict(snapshot_date=snapshot["snapshot_date"], decision_time=max((r["available_at"] for r in snapshot["rows"]), key=datetime.fromisoformat),
                strategy_id=strategy, weights=allocation, cash_weight=1 - sum(allocation.values()),
                reason="selected_by_preregistered_policy" if allocation else "no_matching_semantic_cluster_cash")
