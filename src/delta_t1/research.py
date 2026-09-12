"""Versioned offline research experiments consuming completed canonical runs."""
from collections import defaultdict
import csv
import importlib.metadata
import io
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

from .backtest.portfolio import make_targets
from .backtest.returns_engine import simulate
from .clustering.kmeans import fit_snapshot
from .contracts import normalize, validate_rows
from .evaluation.performance import metrics, bootstrap
from .evaluation.stability import compare
from .ingestion.crawler import code_hash
from .ingestion.promotion import contained_file
from .io import atomic_write, digest, encoded, now, read_json, read_rows, write_json, write_rows


def validate_protocol(config: dict) -> None:
    """Refuse silent defaults and tuning through the evaluation boundary."""
    if config["protocol_version"] != "1.0" or config["clustering"]["algorithm"] != "kmeans":
        raise ValueError("unsupported experiment protocol/algorithm")
    if not config["start"] <= config["end"] <= config["development_end"]:
        raise ValueError("this runner evaluates development only; freeze a reviewed holdout protocol separately")
    if not config["synthetic"] and config["backtest"]["return_basis"] == "synthetic":
        raise ValueError("real experiment cannot accept synthetic returns")
    for field in ("risk_free", "costs", "cash_return", "return_semantics", "k_rationale"):
        if not config["assumptions"].get(field):
            raise ValueError("explicit research assumption required: " + field)
    cluster = config["clustering"]
    if not 2 <= cluster["k"] <= 10 or not cluster["k_range"] or any(not 2 <= k <= 10 for k in cluster["k_range"]):
        raise ValueError("cluster range must be 2..10")
    if not cluster["features"] or cluster["n_init"] < 1 or cluster["max_iter"] < 1:
        raise ValueError("invalid model parameters")
    for key in ("momentum_feature", "risk_feature"):
        if cluster[key] not in cluster["features"]:
            raise ValueError("semantic feature must be in model space")
    if config["portfolio"]["selection_feature"] not in cluster["features"]:
        raise ValueError("portfolio selection feature must be in profile")
    if config["portfolio"]["top_n"] < 1:
        raise ValueError("baseline top_n must be positive")
    if not math.isfinite(config["rf_annual"]) or config["rf_annual"] <= -1:
        raise ValueError("explicit valid research rf_annual required")


def table_csv(path: Path, rows: list[dict]) -> None:
    """Export inspectable tables alongside JSONL; nested data serialized as JSON."""
    if not rows:
        atomic_write(path, b"")
        return
    stream = io.StringIO(newline="")
    fields = sorted({k for row in rows for k in row})
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: encoded(v).decode("utf-8") if isinstance(v, (dict, list)) else v for k, v in row.items()})
    atomic_write(path, stream.getvalue().encode("utf-8"))


def plot_artifacts(directory: Path, backtests: dict, transitions: list[dict], diagnostics: list[dict], synthetic: bool) -> None:
    """Optional standard plotting backend; no raw data or model fit in the view."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    label = "SYNTHETIC | " if synthetic else "DEVELOPMENT | "
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    benchmark_drawn = False
    for name, result in backtests.items():
        rows = result["nav"]
        ax.plot(range(len(rows)), [r["net_nav"] for r in rows], label=name)
        if not benchmark_drawn:
            level, curve = 1.0, []
            for row in rows:
                level *= 1 + row["benchmark_return"]
                curve.append(level)
            ax.plot(range(len(rows)), curve, label="benchmark", linestyle="--")
            benchmark_drawn = True
    ax.set(xlabel="Trading session after first execution", ylabel="Normalized NAV", title=label + "Return-space simulation")
    ax.legend(fontsize=8)
    fig.savefig(directory / "nav.png", dpi=150)
    plt.close(fig)
    if transitions:
        k = max(r["from_cluster"] for r in transitions) + 1
        counts = [[sum(r["count"] for r in transitions if r["from_cluster"] == i and r["to_cluster"] == j) for j in range(k)] for i in range(k)]
        fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
        im = ax.imshow(counts, cmap="Blues")
        for i in range(k):
            for j in range(k):
                ax.text(j, i, counts[i][j], ha="center", va="center")
        ax.set(xlabel="To aligned cluster", ylabel="From aligned cluster", title=label + "Transition counts")
        ax.set_xticks(range(k))
        ax.set_yticks(range(k))
        fig.colorbar(im, ax=ax)
        fig.savefig(directory / "transitions.png", dpi=150)
        plt.close(fig)
    valid = [r for r in diagnostics if r.get("silhouette") is not None]
    if valid:
        ks = sorted({r["k"] for r in valid})
        fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
        ax.plot(ks, [sum(r["silhouette"] for r in valid if r["k"] == k) / sum(r["k"] == k for r in valid) for k in ks], marker="o")
        ax.set(xlabel="k", ylabel="Mean monthly silhouette", title=label + "k diagnostics")
        fig.savefig(directory / "k_diagnostics.png", dpi=150)
        plt.close(fig)


def experiment(data_run: Path, config_path: Path, root: Path) -> tuple[Path, dict]:
    """New experiment every invocation, with input/config/code/environment hashes."""
    data_run = Path(data_run).resolve()
    config = read_json(config_path)
    validate_protocol(config)
    source = read_json(data_run / "manifest.json")
    if source["status"] != "complete" or source["synthetic"] != config["synthetic"]:
        raise ValueError("completed data run with matching synthetic label required")
    feature_rf = source.get("config", {}).get("features", {}).get("rf_annual")
    if feature_rf is not None and feature_rf != config["rf_annual"]:
        raise ValueError("feature and performance risk-free assumptions must agree")
    required_paths = {"features/monthly.jsonl", "clean/prices_daily.jsonl", "clean/securities.jsonl", "clean/trading_calendar.jsonl", "clean/benchmark_daily.jsonl"}
    if not required_paths <= source["artifacts"].keys():
        raise ValueError("data run missing required checksummed artifacts")
    for relative, expected in source["artifacts"].items():
        if digest(contained_file(data_run, relative).read_bytes()) != expected:
            raise ValueError("data artifact checksum mismatch: " + relative)
    tables = {p.stem: read_rows(p) for p in (data_run / "clean").glob("*.jsonl")}
    for name, rows in tables.items():
        validate_rows(name, rows)
    if not source["synthetic"]:
        if not config.get("point_in_time_evidence") or any(m["identity_status"] != "verified" or not m["listing_date"] for m in tables["securities"]):
            raise ValueError("real research needs verified historical master and PIT evidence")
        if any(not s.get("available_at") for s in tables["trading_calendar"]):
            raise ValueError("real calendar requires available_at")
        if any(b.get("index_basis") not in ("price", "total_return") for b in tables["benchmark_daily"]):
            raise ValueError("real benchmark convention unresolved")
    run_id = "experiment-" + uuid.uuid4().hex[:12]
    target = Path(root).resolve() / "data/experiments" / run_id
    target.mkdir(parents=True, exist_ok=False)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unversioned"
    manifest = dict(run_id=run_id, status="running", config=config, config_hash=digest(encoded(config)),
                    data_version=source["data_version"], data_run_path=str(data_run), vendor_run_id=source.get("vendor_run_id"), source_manifest_hash=digest((data_run / "manifest.json").read_bytes()),
                    code_hash=code_hash(), git_commit=commit, random_seed=config["clustering"]["seed"], timestamp=now(),
                    environment=dict(python=sys.version, platform=platform.platform(), packages={d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}),
                    synthetic=config["synthetic"], real_pilot_accepted=False)
    write_json(target / "manifest.json", manifest)
    started = time.monotonic()
    events = []
    try:
        by_date = defaultdict(list)
        features = read_rows(data_run / "features/monthly.jsonl")
        validate_rows("feature_snapshots", features)
        for row in features:
            if config["start"] <= row["as_of_date"] <= config["end"]:
                by_date[row["as_of_date"]].append(row)
        snapshots, assignments, profiles, diagnostic_rows, comparisons, transition_rows, skipped = [], [], [], [], [], [], []
        aligned_ids = None
        previous = None
        for day, rows in sorted(by_date.items()):
            if sum(r["eligibility"] for r in rows) <= config["clustering"]["k"]:
                skipped.append(dict(date=day, reason="insufficient_eligible_universe"))
                previous, aligned_ids = None, None
                continue
            snapshot = fit_snapshot(rows, config["clustering"])
            previous_month = int(previous["snapshot_date"][:4]) * 12 + int(previous["snapshot_date"][5:7]) if previous else None
            current_month = int(day[:4]) * 12 + int(day[5:7])
            if previous_month is not None and current_month != previous_month + 1:
                previous, aligned_ids = None, None
            if previous is not None:
                result = compare(previous, snapshot)
                comparisons.append(dict(from_date=previous["snapshot_date"], to_date=day, **result))
                if result["mapping"] is not None:
                    mapping = {current: aligned_ids[old] for current, old in result["mapping"].items()}
                    for r in result["transitions"]:
                        transition_rows.append(normalize("transitions", dict(r, from_cluster=aligned_ids[r["from_cluster"]], to_cluster=aligned_ids[r["to_cluster"]],
                                                run_id=run_id, from_date=previous["snapshot_date"], to_date=day, data_version=source["data_version"])))
                    aligned_ids = mapping
                else:
                    aligned_ids = None
            if aligned_ids is None:
                aligned_ids = {p["raw_cluster_id"]: p["economic_rank"] for p in snapshot["profiles"]}
            for r, label in zip(snapshot["rows"], snapshot["labels"]):
                assignments.append(normalize("assignments", dict(run_id=run_id, snapshot_date=day, security_id=r["security_id"], raw_cluster_id=label,
                                               aligned_cluster_id=aligned_ids[label], data_version=source["data_version"])))
            profiles.extend(dict(p, snapshot_date=day, aligned_cluster_id=aligned_ids[p["raw_cluster_id"]]) for p in snapshot["profiles"])
            diagnostic_rows.extend(dict(r, snapshot_date=day) for r in snapshot["diagnostics"])
            write_json(target / "models" / (day + ".json"), snapshot["model"])
            snapshots.append(snapshot)
            previous = snapshot
        for name, rows in (("assignments", assignments), ("transitions", transition_rows)):
            validate_rows(name, rows)
            write_rows(target / (name + ".jsonl"), rows)
            table_csv(target / (name + ".csv"), rows)
        for name, rows in (("profiles", profiles), ("diagnostics", diagnostic_rows), ("stability", comparisons), ("skipped_snapshots", skipped)):
            write_rows(target / (name + ".jsonl"), rows)
            table_csv(target / (name + ".csv"), rows)
        if not snapshots:
            raise ValueError("no eligible clustering snapshots")
        # Restrict realized returns to the prespecified development evaluation end.
        for name in ("prices_daily", "benchmark_daily", "trading_calendar"):
            tables[name] = [r for r in tables[name] if r["trade_date"] <= config["end"]]
        backtests, performance, sensitivity = {}, {}, []
        for strategy in ("cluster", "equal_weight_universe", "momentum_only", "risk_only"):
            targets = [make_targets(s, config["portfolio"], strategy) for s in snapshots]
            write_rows(target / "targets" / (strategy + ".jsonl"), targets)
            result = simulate(targets, tables, config["backtest"])
            rows = result["nav"]
            backtests[strategy] = result
            write_rows(target / "backtests" / (strategy + ".jsonl"), rows)
            write_json(target / "backtests" / (strategy + "_execution.json"), {k: v for k, v in result.items() if k != "nav"})
            table_csv(target / "backtests" / (strategy + ".csv"), rows)
            r, b, turnover = ([row[key] for row in rows] for key in ("net_return", "benchmark_return", "turnover"))
            performance[strategy] = metrics(r, b, config["rf_annual"], turnover)
            performance[strategy]["bootstrap"] = bootstrap(r, b, **config["bootstrap"])
            performance[strategy]["subperiods"] = {}
            for year in sorted({row["date"][:4] for row in rows}):
                sub = [row for row in rows if row["date"].startswith(year)]
                if len(sub) >= 2:
                    performance[strategy]["subperiods"][year] = metrics([r["net_return"] for r in sub], [r["benchmark_return"] for r in sub], config["rf_annual"], [r["turnover"] for r in sub])
            for bps in config["cost_sensitivity_bps"]:
                alternative = simulate(targets, tables, dict(config["backtest"], transaction_cost_bps=bps))
                sensitivity.append(dict(strategy=strategy, transaction_cost_bps=bps, net_nav=alternative["nav"][-1]["net_nav"]))
        first = next(iter(backtests.values()))["nav"]
        b = [r["benchmark_return"] for r in first]
        performance[config["backtest"]["benchmark_id"]] = metrics(b, b, config["rf_annual"], [0] * len(b))
        write_json(target / "performance.json", performance)
        table_csv(target / "performance.csv", [dict(strategy=k, **v) for k, v in performance.items()])
        write_rows(target / "cost_sensitivity.jsonl", sensitivity)
        if config.get("plots", False):
            plot_artifacts(target / "plots", backtests, transition_rows, diagnostic_rows, config["synthetic"])
        report = ["# Báo cáo thí nghiệm " + run_id, "", "**KIỂM CHỨNG KỸ THUẬT BẰNG DỮ LIỆU GIẢ LẬP (SYNTHETIC)**" if config["synthetic"] else "**NGHIÊN CỨU TRÊN TẬP PHÁT TRIỂN — cần xem xét giới hạn nguồn dữ liệu và tính đúng thời điểm**", "",
                  "Mô phỏng danh mục trên chuỗi lợi suất với tỷ trọng phân số, khớp tại giá đóng cửa phiên kế tiếp. Chưa mô phỏng sổ giao dịch theo số lượng cổ phiếu thực tế.",
                  "Không đánh giá trên tập kiểm định độc lập (holdout), không chọn mô hình dựa trên lợi nhuận.", "",
                  f"Số thời điểm phân cụm: {len(snapshots)}; số thời điểm bỏ qua: {len(skipped)}; số bản ghi gán cụm: {len(assignments)}.", "",
                  "## Các tệp kết quả", "",
                  "- [Chỉ tiêu hiệu quả](performance.csv)",
                  "- [Đặc trưng từng cụm](profiles.csv)",
                  "- [Chỉ tiêu đánh giá số cụm](diagnostics.csv)",
                  "- [Ma trận chuyển cụm](transitions.csv)",
                  "- [Độ ổn định qua thời gian](stability.jsonl)", "",
                  "Khoảng tin cậy bootstrap được tính với chiến lược đã cố định; kết quả này không chứng minh ý nghĩa thống kê của chiến lược.", "",
                  "## Các giả định được khai báo", ""]
        assumption_labels = {"risk_free": "Lãi suất phi rủi ro", "costs": "Chi phí giao dịch và trượt giá", "cash_return": "Lợi suất tiền mặt", "return_semantics": "Quy ước lợi suất và mô phỏng", "k_rationale": "Cơ sở lựa chọn số cụm"}
        report.extend(f"- **{assumption_labels.get(k, k)}:** {v}" for k, v in config["assumptions"].items())
        atomic_write(target / "report.md", ("\n".join(report) + "\n").encode("utf-8"))
        manifest.update(status="complete", n_snapshots=len(snapshots), n_assignments=len(assignments), backtest_mode="fractional_return_space")
    except (ValueError, KeyError, TypeError, OSError, ImportError) as exc:
        manifest.update(status="failed", error=type(exc).__name__ + ": " + str(exc))
    events.append(dict(run_id=run_id, stage="research", records_in=len(features) if "features" in locals() else 0,
                       records_out=manifest.get("n_assignments", 0), records_failed=int(manifest["status"] == "failed"), elapsed=time.monotonic() - started,
                       source=source["run_id"], data_version=source["data_version"]))
    write_rows(target / "events.jsonl", events)
    manifest["finished_at"] = now()
    manifest["artifacts"] = {p.relative_to(target).as_posix(): digest(p.read_bytes()) for p in sorted(target.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    write_json(target / "manifest.json", manifest)
    return target, manifest
