"""Research protocol validation, independent from experiment execution."""
from datetime import date
import math

from ..clustering.registry import get_algorithm
from ..features.registry import FEATURE_REGISTRY


M2_MARKET_ONLY_SCOPE = "m2_market_only_v1"
M2_MARKET_FEATURES = (
    "mom_21", "mom_63", "mom_126", "mom_252",
    "vol_63", "mdd_126", "beta_126", "liquidity_21",
)
M2_DEVELOPMENT_SNAPSHOTS = (
    "2023-11-30", "2023-12-29", "2024-01-31", "2024-02-29",
    "2024-03-29", "2024-04-26", "2024-05-31", "2024-06-28",
    "2024-07-31", "2024-08-30", "2024-09-30", "2024-10-31",
    "2024-11-29", "2024-12-31", "2025-01-24",
)
M2_HOLDOUT_SNAPSHOTS = (
    "2026-02-27", "2026-03-31", "2026-04-29", "2026-05-29",
    "2026-06-30", "2026-07-31", "2026-08-28",
)


def _require_equal(actual, expected, field: str) -> None:
    if actual != expected:
        raise ValueError(f"{field} must be {expected!r}")


def _require_iso_date(value, field: str) -> None:
    if not isinstance(value, str):
        raise ValueError(field + " must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(field + " must be an ISO date") from exc


def _validate_m2_market_only_v1(config: dict) -> None:
    """Validate the frozen M2 Task-1 preregistration without pretending k is selected."""
    required = (
        "stage", "synthetic", "start", "end", "development_end", "holdout_start", "holdout_end",
        "development_snapshots", "holdout_snapshots", "min_eligible_count",
        "eligibility_field", "eligibility_scope", "below_minimum_action",
        "snapshot_frequency", "missing_data_policy", "prohibited_missing_treatments",
        "clustering", "portfolio_evaluation", "holdout_policy", "assumptions",
    )
    missing = [field for field in required if field not in config]
    if missing:
        raise ValueError("missing M2 protocol field(s): " + ", ".join(missing))

    allowed_stages = {"M2_TASK_1_PROTOCOL_FREEZE", "M2_TASK_3_GLOBAL_K_FROZEN"}
    if config["stage"] not in allowed_stages:
        raise ValueError(f"stage must be one of {sorted(allowed_stages)!r}")
    if config["stage"] == "M2_TASK_3_GLOBAL_K_FROZEN":
        _require_equal(config["clustering"].get("k"), 2, "clustering.k")
    _require_equal(config["synthetic"], False, "synthetic")

    for field in ("start", "end", "development_end", "holdout_start", "holdout_end"):
        _require_iso_date(config[field], field)
    _require_equal(config["start"], M2_DEVELOPMENT_SNAPSHOTS[0], "start")
    _require_equal(config["end"], M2_DEVELOPMENT_SNAPSHOTS[-1], "end")
    _require_equal(config["development_end"], M2_DEVELOPMENT_SNAPSHOTS[-1], "development_end")
    _require_equal(config["holdout_start"], M2_HOLDOUT_SNAPSHOTS[0], "holdout_start")
    _require_equal(config["holdout_end"], M2_HOLDOUT_SNAPSHOTS[-1], "holdout_end")
    _require_equal(tuple(config["development_snapshots"]), M2_DEVELOPMENT_SNAPSHOTS,
                   "development_snapshots")
    _require_equal(tuple(config["holdout_snapshots"]), M2_HOLDOUT_SNAPSHOTS,
                   "holdout_snapshots")
    if not config["development_end"] < config["holdout_start"]:
        raise ValueError("final holdout must begin after the development window")

    _require_equal(config["min_eligible_count"], 120, "min_eligible_count")
    _require_equal(config["eligibility_field"], "market_feature_ready_v2", "eligibility_field")
    _require_equal(config.get("eligibility_scope"), "per_snapshot", "eligibility_scope")
    _require_equal(config.get("snapshot_frequency"), "month_end_last_trading_session",
                   "snapshot_frequency")
    _require_equal(config.get("below_minimum_action"), "skip_snapshot", "below_minimum_action")
    _require_equal(config.get("missing_data_policy"), "exclude_security_fail_closed",
                   "missing_data_policy")
    prohibited = set(config.get("prohibited_missing_treatments", ()))
    required_prohibitions = {
        "mean_imputation", "median_imputation", "zero_fill", "forward_fill",
        "backward_fill", "interpolation",
    }
    if not required_prohibitions <= prohibited:
        raise ValueError("prohibited_missing_treatments must freeze all M2 imputations")

    portfolio = config["portfolio_evaluation"]
    if not isinstance(portfolio, dict) or portfolio.get("enabled") is not False:
        raise ValueError("M2 market-only requires portfolio_evaluation.enabled=false")

    cluster = config["clustering"]
    if not isinstance(cluster, dict):
        raise ValueError("clustering must be an object")
    _require_equal(tuple(cluster.get("features", ())), M2_MARKET_FEATURES,
                   "clustering.features")
    FEATURE_REGISTRY.require_cluster_eligible(cluster["features"])
    _require_equal(cluster.get("winsor_quantile"), 0, "clustering.winsor_quantile")
    _require_equal(cluster.get("clipping"), False, "clustering.clipping")
    _require_equal(cluster.get("scaling"), "robust_per_snapshot", "clustering.scaling")
    _require_equal(cluster.get("scaling_formula"), "(x - median) / IQR",
                   "clustering.scaling_formula")
    _require_equal(cluster.get("scaler_fit_scope"), "independent_snapshot",
                   "clustering.scaler_fit_scope")
    _require_equal(cluster.get("input_feature_version"), "1.6.0",
                   "clustering.input_feature_version")
    _require_equal(cluster.get("registry_metadata_version"), "1.5.0",
                   "clustering.registry_metadata_version")
    _require_equal(cluster.get("k_range"), [2, 3, 4, 5, 6, 7, 8], "clustering.k_range")
    _require_equal(cluster.get("methods"), ["kmeans", "ward", "pca_kmeans"],
                   "clustering.methods")

    selection = cluster.get("global_k_selection")
    if not isinstance(selection, dict):
        raise ValueError("clustering.global_k_selection must be an object")
    _require_equal(selection.get("scope"), "development_only", "global_k_selection.scope")
    _require_equal(selection.get("primary"), "median_silhouette_max",
                   "global_k_selection.primary")
    _require_equal(selection.get("tie_break"), "median_davies_bouldin_min",
                   "global_k_selection.tie_break")
    _require_equal(selection.get("supporting_checks"),
                   ["calinski_harabasz", "cluster_balance"],
                   "global_k_selection.supporting_checks")
    forbidden = set(selection.get("forbidden_metrics", ()))
    if not {"return", "sharpe", "roi"} <= {str(item).lower() for item in forbidden}:
        raise ValueError("Global K selection must explicitly prohibit return, Sharpe and ROI")

    pca = cluster.get("pca")
    if not isinstance(pca, dict):
        raise ValueError("clustering.pca must be an object")
    _require_equal(pca.get("role"), "independent_comparator_only", "clustering.pca.role")
    _require_equal(pca.get("applies_to"), ["pca_kmeans"], "clustering.pca.applies_to")
    _require_equal(pca.get("baseline_preprocessing"), False,
                   "clustering.pca.baseline_preprocessing")
    _require_equal(pca.get("component_rule_status"),
                   "must_be_frozen_before_pca_comparator_execution",
                   "clustering.pca.component_rule_status")

    holdout = config.get("holdout_policy")
    if not isinstance(holdout, dict):
        raise ValueError("holdout_policy must be an object")
    _require_equal(holdout.get("sealed_during_development"), True,
                   "holdout_policy.sealed_during_development")
    _require_equal(holdout.get("may_tune"), [], "holdout_policy.may_tune")
    _require_equal(holdout.get("prohibited_changes"),
                   ["k", "scaler", "pca", "algorithm"],
                   "holdout_policy.prohibited_changes")
    _require_equal(holdout.get("access_stage"),
                   "M2_TASK_11_ONLY_AFTER_DEVELOPMENT_FREEZE",
                   "holdout_policy.access_stage")

    assumptions = config["assumptions"]
    for field in ("k_rationale", "feature_version_compatibility", "holdout_isolation"):
        if not isinstance(assumptions, dict) or not assumptions.get(field):
            raise ValueError("explicit research assumption required: " + field)


def validate_protocol(config: dict) -> None:
    """Refuse silent defaults and tuning through the evaluation boundary."""
    if not isinstance(config, dict) or config.get("protocol_version") != "1.0":
        raise ValueError("unsupported experiment protocol version")
    if config.get("protocol_scope") == M2_MARKET_ONLY_SCOPE:
        _validate_m2_market_only_v1(config)
        return
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
