"""Explicit long-only portfolio policies, independent of numeric cluster IDs."""
from datetime import datetime
import math


def select_backtest_universe(rows: list[dict], specification: dict | None) -> list[dict]:
    """Apply a declared universe rule before a strategy selects holdings."""
    if not specification:
        return list(rows)
    mode = specification.get("mode")
    filters = specification.get("filters", {})
    if mode not in ("all", "top_n", "percentage") or not isinstance(filters, dict):
        raise ValueError("invalid backtest_universe specification")
    selected = [
        row for row in rows
        if all(row.get(field) in (allowed if isinstance(allowed, list) else [allowed]) for field, allowed in filters.items())
    ]
    if mode == "all":
        return selected
    rank_by = specification.get("rank_by")
    if not rank_by or any(row.get(rank_by) is None or not math.isfinite(row[rank_by]) for row in selected):
        raise ValueError("rank_by must name a finite feature for top_n/percentage universe selection")
    selected.sort(key=lambda row: ((-row[rank_by]) if specification.get("descending", True) else row[rank_by], row["security_id"]))
    value = specification.get("value")
    if mode == "top_n":
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("top_n universe value must be a positive integer")
        count = min(value, len(selected))
    else:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 1:
            raise ValueError("percentage universe value must be in (0, 1]")
        count = min(len(selected), math.ceil(len(selected) * value))
    return selected[:count]


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
    rows = select_backtest_universe(snapshot["rows"], config.get("backtest_universe"))
    if not rows or any(not r["eligibility"] for r in rows):
        raise ValueError("targets require eligible snapshot")
    if strategy == "cluster":
        candidates = [p for p in snapshot["profiles"] if p["semantic_label"] == config["semantic_label"]]
        winner = min(candidates, key=lambda p: (-p["centroid"][config["selection_feature"]], p["raw_cluster_id"])) if candidates else None
        label_by_security = {r["security_id"]: label for r, label in zip(snapshot["rows"], snapshot["labels"])}
        rows = [r for r in rows if winner and label_by_security[r["security_id"]] == winner["raw_cluster_id"]]
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
