"""Research protocol validation, independent from experiment execution."""
import math

from ..clustering.registry import get_algorithm
from ..features.registry import FEATURE_REGISTRY


def validate_protocol(config: dict) -> None:
    """Refuse silent defaults and tuning through the evaluation boundary."""
    if config["protocol_version"] != "1.0":
        raise ValueError("unsupported experiment protocol version")
    cluster = config["clustering"]
    algorithm = get_algorithm(cluster["algorithm"])
    algorithm.validate_config(cluster)
    portfolio_evaluation = config.get("portfolio_evaluation")
    if (not isinstance(portfolio_evaluation, dict)
            or not isinstance(portfolio_evaluation.get("enabled"), bool)):
        raise ValueError("portfolio_evaluation.enabled must be explicitly true or false")
    if not config["start"] <= config["end"] <= config["development_end"]:
        raise ValueError("this runner evaluates development only; freeze a reviewed holdout protocol separately")
    for field in ("k_rationale",):
        if not config["assumptions"].get(field):
            raise ValueError("explicit research assumption required: " + field)
    FEATURE_REGISTRY.require_cluster_eligible(cluster["features"])
    reduction = cluster.get("reduction", {"method": "none"})
    if reduction.get("method", "none") not in ("none", "pca"):
        raise ValueError("unsupported dimensionality reduction")
    if reduction.get("method") == "pca" and (isinstance(reduction.get("n_components"), bool)
                                               or not isinstance(reduction.get("n_components"), int)
                                               or not 1 <= reduction["n_components"] <= len(cluster["features"])):
        raise ValueError("PCA n_components must be within the registered feature space")
    for key in ("momentum_feature", "risk_feature"):
        if cluster[key] not in cluster["features"]:
            raise ValueError("semantic feature must be in model space")
    if portfolio_evaluation["enabled"]:
        if not config["synthetic"] and config["backtest"]["return_basis"] == "synthetic":
            raise ValueError("real experiment cannot accept synthetic returns")
        for field in ("risk_free", "costs", "cash_return", "return_semantics"):
            if not config["assumptions"].get(field):
                raise ValueError("explicit portfolio assumption required: " + field)
        if config["portfolio"]["selection_feature"] not in cluster["features"]:
            raise ValueError("portfolio selection feature must be in profile")
        if config["portfolio"]["top_n"] < 1:
            raise ValueError("baseline top_n must be positive")
        universe = config["portfolio"].get("backtest_universe")
        if universe:
            mode, value = universe.get("mode"), universe.get("value")
            if mode not in ("all", "top_n", "percentage"):
                raise ValueError("unsupported backtest_universe mode")
            if mode == "top_n" and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
                raise ValueError("top_n backtest universe requires a positive integer value")
            if mode == "percentage" and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 1):
                raise ValueError("percentage backtest universe requires value in (0, 1]")
            if mode != "all" and not universe.get("rank_by"):
                raise ValueError("rank_by is required for top_n/percentage backtest universe")
        if not math.isfinite(config["rf_annual"]) or config["rf_annual"] <= -1:
            raise ValueError("explicit valid research rf_annual required")
