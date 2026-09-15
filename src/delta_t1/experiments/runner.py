"""Offline experiment orchestration over complete, checksummed data runs."""
from collections import defaultdict
from pathlib import Path
import time

from ..backtest.portfolio import make_targets
from ..backtest.returns_engine import simulate
from ..clustering.registry import get_algorithm
from ..contracts import normalize, validate_rows
from ..evaluation.portfolio_metrics import bootstrap, metrics
from ..evaluation.temporal_metrics import compare
from ..io import read_json, read_rows, write_json, write_rows
from .artifacts import finish_experiment, load_verified_data_run, start_experiment
from .protocol import validate_protocol
from .reporting import plot_artifacts, table_csv, write_report


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
        for day, rows in sorted(by_date.items()):
            if sum(row["eligibility"] for row in rows) <= config["clustering"]["k"]:
                skipped.append(dict(date=day, reason="insufficient_eligible_universe"))
                previous, aligned_ids = None, None
                continue
            snapshot = algorithm.fit_snapshot(rows, config["clustering"])
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
        for name in ("prices_daily", "benchmark_daily", "trading_calendar"):
            tables[name] = [row for row in tables[name] if row["trade_date"] <= config["end"]]
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
                sensitivity.append(dict(strategy=strategy, transaction_cost_bps=bps,
                                        net_nav=alternative["nav"][-1]["net_nav"]))
        first = next(iter(backtests.values()))["nav"]
        benchmark = [row["benchmark_return"] for row in first]
        performance[config["backtest"]["benchmark_id"]] = metrics(
            benchmark, benchmark, config["rf_annual"], [0] * len(benchmark)
        )
        write_json(target / "performance.json", performance)
        table_csv(target / "performance.csv", [dict(strategy=name, **value)
                                                 for name, value in performance.items()])
        write_rows(target / "cost_sensitivity.jsonl", sensitivity)
        if config.get("plots", False):
            plot_artifacts(target / "plots", backtests, transition_rows, diagnostic_rows, config["synthetic"])
        write_report(target / "report.md", manifest["run_id"], manifest["data_mode"],
                     config["assumptions"], len(snapshots), len(skipped), len(assignments))
        manifest.update(status="complete", n_snapshots=len(snapshots), n_assignments=len(assignments),
                        backtest_mode="fractional_return_space")
        manifest["real_pilot_accepted"] = bool(
            not config["synthetic"] and config.get("pilot") and len(snapshots) >= 12
            and len({row["security_id"] for row in assignments}) >= 10 and transition_rows and first
        )
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
