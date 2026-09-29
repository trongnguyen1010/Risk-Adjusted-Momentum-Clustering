"""Offline experiment orchestration over complete, checksummed data runs."""
from collections import defaultdict
import math
from pathlib import Path
import time

from ..backtest.portfolio import make_targets
from ..backtest.returns_engine import simulate
from ..clustering.registry import get_algorithm
from ..contracts import normalize, validate_rows
from ..evaluation.portfolio_metrics import bootstrap, metrics
from ..evaluation.temporal_metrics import compare
from ..io import read_json, read_rows, write_json, write_rows
from .artifacts import (
    finish_experiment,
    load_verified_data_run,
    load_verified_market_only_features,
    start_experiment,
)
from .protocol import validate_protocol
from .reporting import plot_artifacts, table_csv, write_report


def _with_c8_market_readiness_alias(row: dict, eligibility_field: str) -> dict:
    """Expose the frozen M2 v2 name without mutating the immutable C8 row."""
    if eligibility_field != "market_feature_ready_v2":
        return row
    if eligibility_field in row:
        return row
    if "market_feature_ready" not in row:
        raise ValueError("C8 row missing market_feature_ready for v2 eligibility alias")
    return dict(row, market_feature_ready_v2=row["market_feature_ready"])


def prepare_snapshot_rows(rows: list[dict], config: dict, snapshot_date: str) -> dict:
    """Filter and validate one snapshot using only its own eligibility observations."""
    eligibility_field = config["eligibility_field"]
    features = config["clustering"]["features"]
    minimum = config["min_eligible_count"]
    if not rows or any(row.get("as_of_date") != snapshot_date for row in rows):
        raise ValueError("one nonempty snapshot date is required")
    if len({row["security_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate security in M2 snapshot: " + snapshot_date)
    for row in rows:
        if eligibility_field not in row or type(row[eligibility_field]) is not bool:
            raise ValueError("missing or invalid configured eligibility field: " + eligibility_field)
    eligible = sorted(
        (row for row in rows if row[eligibility_field] is True),
        key=lambda row: row["security_id"],
    )
    for row in eligible:
        for feature in features:
            value = row.get(feature)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)):
                raise ValueError(
                    f"nonfinite M2 feature at {snapshot_date}/{row['security_id']}: {feature}"
                )
    if len(eligible) < minimum:
        return dict(
            snapshot_date=snapshot_date,
            status="skipped",
            reason=f"eligible_count_below_minimum: {len(eligible)} < {minimum}",
            eligible_count=len(eligible),
            rows=[],
        )
    return dict(
        snapshot_date=snapshot_date,
        status="ready",
        reason=None,
        eligible_count=len(eligible),
        rows=eligible,
    )


def prepare_m2_market_only_snapshots(
        data_run: Path, config: dict, snapshot_dates=None) -> tuple[dict, list[dict]]:
    """Prepare M2 inputs only; this function never fits clustering or opens holdout by default."""
    validate_protocol(config)
    requested = tuple(snapshot_dates or config["development_snapshots"])
    development = set(config["development_snapshots"])
    if not requested or not set(requested) <= development:
        raise ValueError("M2 preparation may read only frozen development snapshots")
    source, raw_rows = load_verified_market_only_features(data_run, requested)
    eligibility_field = config["eligibility_field"]
    grouped = defaultdict(list)
    for raw in raw_rows:
        row = _with_c8_market_readiness_alias(raw, eligibility_field)
        grouped[row["as_of_date"]].append(row)
    prepared = [prepare_snapshot_rows(grouped[day], config, day) for day in requested]
    return source, prepared


def m2_clustering_config(config: dict, **runtime_parameters) -> dict:
    """Translate the frozen root-level eligibility rule to the common clustering interface."""
    cluster = dict(config["clustering"])
    cluster["eligibility_field"] = config["eligibility_field"]
    cluster.update(runtime_parameters)
    return cluster


def _run_portfolio_evaluation(target, snapshots, tables, config):
    """Run M3-only portfolio evaluation after clustering choices are frozen."""
    backtests, performance, sensitivity = {}, {}, []
    for strategy in ("cluster", "equal_weight_universe", "momentum_only", "risk_only"):
        targets = [make_targets(snapshot, config["portfolio"], strategy) for snapshot in snapshots]
        write_rows(target / "targets" / (strategy + ".jsonl"), targets)
        result = simulate(targets, tables, config["backtest"])
        rows = result["nav"]
        backtests[strategy] = result
        write_rows(target / "backtests" / (strategy + ".jsonl"), rows)
        write_json(target / "backtests" / (strategy + "_execution.json"),
                   {key: value for key, value in result.items() if key != "nav"})
        table_csv(target / "backtests" / (strategy + ".csv"), rows)
        returns, benchmark, turnover = (
            [row[key] for row in rows] for key in ("net_return", "benchmark_return", "turnover")
        )
        performance[strategy] = metrics(returns, benchmark, config["rf_annual"], turnover)
        performance[strategy]["bootstrap"] = bootstrap(returns, benchmark, **config["bootstrap"])
        performance[strategy]["subperiods"] = {}
        for year in sorted({row["date"][:4] for row in rows}):
            subperiod = [row for row in rows if row["date"].startswith(year)]
            if len(subperiod) >= 2:
                performance[strategy]["subperiods"][year] = metrics(
                    [row["net_return"] for row in subperiod],
                    [row["benchmark_return"] for row in subperiod],
                    config["rf_annual"],
                    [row["turnover"] for row in subperiod],
                )
        for bps in config["cost_sensitivity_bps"]:
            alternative = simulate(targets, tables, dict(config["backtest"], transaction_cost_bps=bps))
            sensitivity.append({"strategy": strategy, "transaction_cost_bps": bps,
                                "net_nav": alternative["nav"][-1]["net_nav"]})
    first = next(iter(backtests.values()))["nav"]
    benchmark = [row["benchmark_return"] for row in first]
    performance[config["backtest"]["benchmark_id"]] = metrics(
        benchmark, benchmark, config["rf_annual"], [0] * len(benchmark)
    )
    write_json(target / "performance.json", performance)
    table_csv(target / "performance.csv", [dict(strategy=name, **value)
                                             for name, value in performance.items()])
    write_rows(target / "cost_sensitivity.jsonl", sensitivity)
    return backtests


def experiment(data_run: Path, config_path: Path, root: Path) -> tuple[Path, dict]:
    """Create a new immutable experiment for every invocation."""
    data_run = Path(data_run).resolve()
    config = read_json(config_path)
    validate_protocol(config)
    source, tables = load_verified_data_run(data_run, config)
    target, manifest = start_experiment(root, data_run, source, config)
    algorithm = get_algorithm(config["clustering"]["algorithm"])
    started = time.monotonic()
    features = []
    try:
        by_date = defaultdict(list)
        features = read_rows(data_run / "features/monthly.jsonl")
        validate_rows("feature_snapshots", features)
        for row in features:
            if config["start"] <= row["as_of_date"] <= config["end"]:
                by_date[row["as_of_date"]].append(row)
        snapshots, assignments, profiles = [], [], []
        diagnostic_rows, comparisons, transition_rows, skipped = [], [], [], []
        aligned_ids = None
        previous = None
        eligibility_field = config.get("eligibility_field", "eligibility")
        clustering_config = dict(config["clustering"], eligibility_field=eligibility_field)
        minimum = config.get("min_eligible_count", config["clustering"]["k"] + 1)
        for day, rows in sorted(by_date.items()):
            if any(eligibility_field not in row or type(row[eligibility_field]) is not bool
                   for row in rows):
                raise ValueError("missing or invalid configured eligibility field: "
                                 + eligibility_field)
            eligible_count = sum(row[eligibility_field] is True for row in rows)
            if eligible_count < minimum:
                skipped.append(dict(
                    date=day,
                    reason="eligible_count_below_minimum",
                    eligible_count=eligible_count,
                    min_eligible_count=minimum,
                ))
                previous, aligned_ids = None, None
                continue
            snapshot = algorithm.fit_snapshot(rows, clustering_config)
            previous_month = (int(previous["snapshot_date"][:4]) * 12
                              + int(previous["snapshot_date"][5:7])) if previous else None
            current_month = int(day[:4]) * 12 + int(day[5:7])
            if previous_month is not None and current_month != previous_month + 1:
                previous, aligned_ids = None, None
            if previous is not None:
                result = compare(previous, snapshot)
                comparisons.append(dict(from_date=previous["snapshot_date"], to_date=day, **result))
                if result["mapping"] is not None:
                    mapping = {current: aligned_ids[old] for current, old in result["mapping"].items()}
                    for row in result["transitions"]:
                        transition_rows.append(normalize("transitions", dict(
                            row,
                            from_cluster=aligned_ids[row["from_cluster"]],
                            to_cluster=aligned_ids[row["to_cluster"]],
                            run_id=manifest["run_id"],
                            from_date=previous["snapshot_date"],
                            to_date=day,
                            data_version=source["data_version"],
                        )))
                    aligned_ids = mapping
                else:
                    aligned_ids = None
            if aligned_ids is None:
                aligned_ids = {profile["raw_cluster_id"]: profile["economic_rank"]
                               for profile in snapshot["profiles"]}
            for row, label in zip(snapshot["rows"], snapshot["labels"]):
                assignments.append(normalize("assignments", dict(
                    run_id=manifest["run_id"],
                    snapshot_date=day,
                    security_id=row["security_id"],
                    raw_cluster_id=label,
                    aligned_cluster_id=aligned_ids[label],
                    data_version=source["data_version"],
                )))
            profiles.extend(dict(profile, snapshot_date=day,
                                 aligned_cluster_id=aligned_ids[profile["raw_cluster_id"]])
                            for profile in snapshot["profiles"])
            diagnostic_rows.extend(dict(row, snapshot_date=day) for row in snapshot["diagnostics"])
            write_json(target / "models" / (day + ".json"), snapshot["model"])
            if config.get("protocol_scope") == "m2_market_only_v1" or str(config.get("stage", "")).startswith("M2_"):
                algo = config.get("clustering", {}).get("algorithm") or config.get("clustering", {}).get("baseline")
                if algo in ("kmeans", "ward", "pca_kmeans"):
                    m2_models_dir = Path(root).resolve() / "M2" / "models" / algo
                    m2_models_dir.mkdir(parents=True, exist_ok=True)
                    write_json(m2_models_dir / (day + ".json"), snapshot["model"])
            snapshots.append(snapshot)
            previous = snapshot
        for name, rows in (("assignments", assignments), ("transitions", transition_rows)):
            validate_rows(name, rows)
            write_rows(target / (name + ".jsonl"), rows)
            table_csv(target / (name + ".csv"), rows)
        for name, rows in (("profiles", profiles), ("diagnostics", diagnostic_rows),
                           ("stability", comparisons), ("skipped_snapshots", skipped)):
            write_rows(target / (name + ".jsonl"), rows)
            table_csv(target / (name + ".csv"), rows)
        if not snapshots:
            raise ValueError("no eligible clustering snapshots")
        portfolio_enabled = config["portfolio_evaluation"]["enabled"]
        backtests = {}
        if portfolio_enabled:
            for name in ("prices_daily", "benchmark_daily", "trading_calendar"):
                tables[name] = [row for row in tables[name] if row["trade_date"] <= config["end"]]
            backtests = _run_portfolio_evaluation(target, snapshots, tables, config)
        if config.get("plots", False):
            plot_artifacts(target / "plots", backtests, transition_rows, diagnostic_rows, config["synthetic"])
        write_report(target / "report.md", manifest["run_id"], manifest["data_mode"],
                     config["assumptions"], len(snapshots), len(skipped), len(assignments),
                     portfolio_enabled)
        manifest.update(status="complete", n_snapshots=len(snapshots), n_assignments=len(assignments),
                        portfolio_evaluation_enabled=portfolio_enabled)
        if portfolio_enabled:
            manifest["backtest_mode"] = "fractional_return_space"
        manifest["real_pilot_accepted"] = False
    except (ValueError, KeyError, TypeError, OSError, ImportError) as exc:
        manifest.update(status="failed", error=type(exc).__name__ + ": " + str(exc))
    write_rows(target / "events.jsonl", [dict(
        run_id=manifest["run_id"],
        stage="research",
        records_in=len(features),
        records_out=manifest.get("n_assignments", 0),
        records_failed=int(manifest["status"] == "failed"),
        elapsed=time.monotonic() - started,
        source=source["run_id"],
        data_version=source["data_version"],
    )])
    finish_experiment(target, manifest)
    return target, manifest
