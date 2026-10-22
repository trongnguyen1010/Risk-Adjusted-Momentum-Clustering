"""Task 11: one-way validation of the frozen winner, independent monthly fits."""
from collections import defaultdict
import copy
import csv
from datetime import datetime, timezone
import io
import math
from pathlib import Path
from statistics import mean, median
import zipfile

from ..clustering.registry import get_algorithm
from ..evaluation.temporal_metrics import compare
from ..io import digest, encoded, now, read_json, read_rows, write_json, write_rows
from .artifacts import load_verified_market_only_features
from .protocol import (
    M2_DEVELOPMENT_SNAPSHOTS, M2_HOLDOUT_SNAPSHOTS, M2_MARKET_FEATURES,
    validate_protocol,
)
from .runner import _with_c8_market_readiness_alias, prepare_snapshot_rows

METHODS = {
    "KMeans_Baseline": ("kmeans", "m2-task4-kmeans-baseline-v1", "m2-evaluation-kmeans"),
    "Ward_Hierarchical": ("ward", "m2-task5-ward-v1", "m2-evaluation-ward"),
    "PCA_KMeans": ("pca_kmeans", "m2-task6-pca-kmeans-v1", "m2-evaluation-pca-kmeans"),
}
QUALITY = ("silhouette", "davies_bouldin", "calinski_harabasz", "inertia", "cluster_balance")
TEMPORAL = ("ari", "nmi", "persistence_probability", "migration_rate")
TEMPORAL_FIELDS = ("from_date", "to_date", "n_common", *TEMPORAL,
                   "entered_count", "exited_count", "status")
TRANSITION_FIELDS = ("from_date", "to_date", "from_cluster", "to_cluster", "count", "rate")
DRIFT_FIELDS = ("from_date", "to_date", "aligned_cluster_id", "feature", "value_from", "value_to", "delta")


def _path(root, relative):
    path = (root / str(relative).replace("\\", "/")).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Task 11 path must stay inside repository")
    return path


def _csv_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path, rows, fields=None):
    fields = list(fields or (list(rows[0]) if rows else []))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_bytes(stream.getvalue().encode("utf-8"))


def freeze_gate(root: Path) -> dict:
    """Verify Task 10 and frozen model parameters before reading any holdout rows."""
    root = Path(root).resolve()
    task_config_path = root / "configs/experiments/m2_final_holdout_v1.json"
    task_config = read_json(task_config_path)
    expected = dict(stage="M2_TASK_11_HOLDOUT", holdout_snapshots=list(M2_HOLDOUT_SNAPSHOTS),
                    min_eligible_count=120, eligibility_field="market_feature_ready_v2",
                    portfolio_evaluation_enabled=False, gap_reset=True, k_scan_enabled=False,
                    rerun_policy="verify_existing_complete_artifacts_without_refit")
    for key, value in expected.items():
        if task_config.get(key) != value:
            raise ValueError("Task 11 config conflicts with frozen plan: " + key)
    decision_path = _path(root, task_config["decision_path"])
    decision = read_json(decision_path)
    if decision.get("status") != "FROZEN_FOR_HOLDOUT":
        raise ValueError("Final method must be FROZEN_FOR_HOLDOUT before opening data")
    selected = decision.get("selected_method")
    if selected not in METHODS or type(decision.get("global_k")) is not int or decision["global_k"] != 2:
        raise ValueError("One supported winning method with Global K=2 is required")
    if set(decision.get("comparator_methods", [])) != set(METHODS) - {selected}:
        raise ValueError("Task 10 must retain exactly two development comparators")
    frozen_at = datetime.fromisoformat(decision["decision_timestamp"])
    if frozen_at.tzinfo is None or frozen_at > datetime.now(timezone.utc):
        raise ValueError("Decision timestamp must be aware and before holdout access")
    protocol_path = _path(root, task_config["protocol_path"])
    protocol = read_json(protocol_path)
    validate_protocol(protocol)
    if protocol["stage"] != "M2_TASK_3_GLOBAL_K_FROZEN":
        raise ValueError("Global K protocol has not been frozen")
    bundle = decision["frozen_artifacts_manifest"]
    model_dir = _path(root, bundle["selected_model_directory"])
    model_index_path = model_dir / "model_file_manifest.json"
    model_index = read_json(model_index_path)
    if (model_index["selected_method"] != selected
            or tuple(model_index["development_snapshots"]) != M2_DEVELOPMENT_SNAPSHOTS
            or sorted(f["name"] for f in model_index["files"])
            != [day + ".json" for day in M2_DEVELOPMENT_SNAPSHOTS]):
        raise ValueError("Selected-model manifest does not match frozen decision")
    fingerprints = {}
    configs = []
    for item in model_index["files"]:
        path = _path(model_dir, item["name"])
        if digest(path.read_bytes()) != item["sha256"]:
            raise ValueError("Frozen model checksum mismatch: " + item["name"])
        configs.append(read_json(path)["config"])
        fingerprints[path.relative_to(root).as_posix()] = item["sha256"]
    cluster = configs[0]
    if any(config != cluster for config in configs):
        raise ValueError("Frozen development models use different parameters")
    if (cluster["k"] != 2 or tuple(cluster["features"]) != M2_MARKET_FEATURES
            or cluster["scaling"] != "robust_per_snapshot" or cluster["winsor_quantile"] != 0
            or cluster.get("clipping") is not False
            or cluster.get("eligibility_field") != "market_feature_ready_v2"):
        raise ValueError("Frozen model violates market-only preprocessing contract")
    algorithm, task_name, evaluation_name = METHODS[selected]
    if cluster.get("algorithm", cluster.get("baseline")) != algorithm:
        raise ValueError("Frozen model algorithm differs from selected method")
    if algorithm != "pca_kmeans" and cluster.get("reduction", {}).get("method", "none") != "none":
        raise ValueError("Unexpected PCA preprocessing in selected model")
    # Removing diagnostic alternatives implements the plan's no-K-scan rule;
    # it does not change selected K or any fit/preprocessing hyperparameter.
    runtime = copy.deepcopy(cluster)
    runtime.update(algorithm=algorithm, k_range=[2])
    get_algorithm(algorithm).validate_config(runtime)
    comparison_path = _path(root, bundle["comparison_table"])
    comparison = _csv_rows(comparison_path)
    if len(comparison) != 3 or {r["method"] for r in comparison} != set(METHODS):
        raise ValueError("Frozen comparison must contain exactly three development methods")
    task_dir = root / "M2/artifacts" / task_name
    evaluation_dir = root / "M2/artifacts" / evaluation_name
    diagnostics_path = task_dir / "diagnostics.csv"
    dev_diagnostics = [r for r in _csv_rows(diagnostics_path) if int(r["k"]) == 2]
    if [r["snapshot_date"] for r in dev_diagnostics] != list(M2_DEVELOPMENT_SNAPSHOTS):
        raise ValueError("Development diagnostics must contain exactly 15 dates at K=2")
    winning_row = next(r for r in comparison if r["method"] == selected)
    if not math.isclose(median(float(r["silhouette"]) for r in dev_diagnostics),
                        float(winning_row["median_silhouette"]), rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError("Task 10 comparison differs from frozen development diagnostics")
    files = [task_config_path, decision_path, protocol_path, model_index_path,
             comparison_path, diagnostics_path, evaluation_dir / "cluster_profiles.csv",
             evaluation_dir / "temporal_stability.csv"]
    fingerprints.update({p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in files})
    return dict(selected_method=selected, algorithm=algorithm, decision=decision,
                protocol=protocol, task_config=task_config, clustering=runtime,
                frozen_model_config=cluster, input_sha256=fingerprints,
                dev_diagnostics=dev_diagnostics, evaluation_dir=evaluation_dir)


def prepare_holdout(root, gate):
    """Open only seven holdout dates after gate verification, preserving C8 bytes."""
    source, rows = load_verified_market_only_features(
        _path(root, gate["task_config"]["feature_store"]), M2_HOLDOUT_SNAPSHOTS)
    grouped = defaultdict(list)
    for raw in rows:
        if raw.get("feature_version") != "1.6.0":
            raise ValueError("Holdout input must use frozen feature version 1.6.0")
        day = raw["as_of_date"]
        available = datetime.fromisoformat(raw["available_at"])
        cutoff = datetime.fromisoformat(day + "T23:59:59+07:00")
        if available.tzinfo is None or available > cutoff:
            raise ValueError("Future feature availability in holdout: " + day)
        grouped[day].append(_with_c8_market_readiness_alias(raw, "market_feature_ready_v2"))
    prepared = [prepare_snapshot_rows(grouped[day], gate["protocol"], day)
                for day in M2_HOLDOUT_SNAPSHOTS]
    return source, prepared


def fit_holdout(prepared, clustering, algorithm_name):
    """Fit only the frozen algorithm and K; reset alignment at start/skip/month gap."""
    if clustering["k"] != 2 or clustering["k_range"] != [2] or clustering["algorithm"] != algorithm_name:
        raise ValueError("Holdout may execute only the frozen algorithm at K=2")
    algorithm = get_algorithm(algorithm_name)
    snapshots, temporal, transitions, drift = [], [], [], []
    previous, aligned_ids = None, None
    for prep in prepared:
        if prep["status"] == "skipped":
            previous, aligned_ids = None, None
            continue
        day = prep["snapshot_date"]
        current = algorithm.fit_snapshot(prep["rows"], clustering)
        if len(current["diagnostics"]) != 1 or current["diagnostics"][0]["k"] != 2:
            raise ValueError("Holdout performed an unexpected K scan")
        month = lambda value: int(value[:4]) * 12 + int(value[5:7])
        if previous and month(day) != month(previous["snapshot_date"]) + 1:
            previous, aligned_ids = None, None
        if previous:
            result = compare(previous, current)
            if result["mapping"] is None:
                raise ValueError("No shared securities for a holdout transition")
            old_ids = aligned_ids
            aligned_ids = {raw: old_ids[old] for raw, old in result["mapping"].items()}
            pair = dict(from_date=previous["snapshot_date"], to_date=day)
            temporal.append(dict(pair, n_common=result["n_common"],
                **{metric: result[metric] for metric in TEMPORAL},
                entered_count=len(result["entered"]), exited_count=len(result["exited"]), status="OK"))
            transitions.extend(dict(pair, from_cluster=old_ids[r["from_cluster"]],
                to_cluster=old_ids[r["to_cluster"]], count=r["count"], rate=r["rate"])
                for r in result["transitions"])
            for raw, old in result["mapping"].items():
                for feature in M2_MARKET_FEATURES:
                    before = previous["profiles"][old]["centroid"][feature]
                    after = current["profiles"][raw]["centroid"][feature]
                    drift.append(dict(pair, aligned_cluster_id=aligned_ids[raw], feature=feature,
                                      value_from=before, value_to=after, delta=after-before))
        else:
            aligned_ids = {p["raw_cluster_id"]: p["economic_rank"] for p in current["profiles"]}
        current["aligned_ids"] = dict(aligned_ids)
        snapshots.append(current)
        previous = current
    if not snapshots:
        raise ValueError("All holdout snapshots were skipped")
    return snapshots, temporal, transitions, drift


def _summary(values):
    values = [float(value) for value in values if value is not None]
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError("Unavailable/nonfinite holdout summary")
    return dict(mean=mean(values), median=median(values), minimum=min(values), maximum=max(values))


def verify_existing(root, gate):
    target = _path(root, gate["task_config"]["output_dir"])
    manifest = read_json(target / "manifest.json")
    if manifest.get("status") != "complete":
        raise ValueError("Existing holdout is incomplete; preserve evidence and investigate")
    if manifest["input_sha256"] != gate["input_sha256"] or manifest["clustering"] != gate["clustering"]:
        raise ValueError("Frozen inputs changed after holdout opening; refusing a new fit")
    for relative, expected in manifest["artifacts"].items():
        if digest(_path(root, relative).read_bytes()) != expected:
            raise ValueError("Holdout artifact checksum mismatch: " + relative)
    store = _path(root, gate["task_config"]["feature_store"])
    if digest((store / "manifest.json").read_bytes()) != manifest["c8_manifest_sha256"]:
        raise ValueError("C8 source manifest changed after holdout execution")
    if digest((store / "canonical/feature_snapshots.jsonl").read_bytes()) != manifest["c8_feature_sha256"]:
        raise ValueError("C8 feature source changed after holdout execution")
    return target, manifest


def _plot(target, dev, holdout):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    dates = list(M2_DEVELOPMENT_SNAPSHOTS) + list(M2_HOLDOUT_SNAPSHOTS)
    by_date = {r["snapshot_date"]: r["silhouette"] for r in holdout}
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(range(15), [float(r["silhouette"]) for r in dev], "o-", label="Development")
    ax.plot(range(15, 22), [by_date.get(day, float("nan")) for day in M2_HOLDOUT_SNAPSHOTS],
            "s-", label="Final Holdout")
    ax.hlines(median(float(r["silhouette"]) for r in dev), 0, 14, colors="tab:blue",
              linestyles=":", label="Development median")
    ax.hlines(median(r["silhouette"] for r in holdout), 15, 21, colors="tab:orange",
              linestyles=":", label="Holdout median")
    ax.axvline(14.5, linestyle="--", color="red")
    ax.text(14.5, .03, "Systemic Data Gap (2025-02 to 2026-01) — Temporal Chain Reset",
            rotation=90, color="darkred", ha="right", va="bottom", fontsize=8)
    ax.set(ylim=(0, 1), ylabel="Silhouette", xlabel="Snapshot",
           title="Final Holdout — frozen winner, independent monthly fits")
    ax.set_xticks(range(22), dates, rotation=60, ha="right")
    ax.grid(axis="y", alpha=.25)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(target / "holdout_vs_dev_trajectory.png", dpi=160)
    plt.close(fig)


def run_final_holdout(root: Path):
    """Execute once; subsequent invocations only verify existing frozen evidence."""
    root = Path(root).resolve()
    gate = freeze_gate(root)
    config = gate["task_config"]
    target = _path(root, config["output_dir"])
    if target.exists():
        return verify_existing(root, gate)
    model_dir, report_path = _path(root, config["model_dir"]), _path(root, config["report_path"])
    if (model_dir.exists() and any(model_dir.iterdir())) or report_path.exists():
        raise FileExistsError("Existing holdout models/report must not be overwritten")
    target.mkdir(parents=True, exist_ok=False)
    opened_at = now()
    manifest = dict(stage="M2_TASK_11_HOLDOUT", artifact_id=target.name, status="running",
        selected_method=gate["selected_method"], algorithm=gate["algorithm"], global_k=2,
        clustering=gate["clustering"], frozen_development_model_config=gate["frozen_model_config"],
        input_sha256=gate["input_sha256"], decision_timestamp=gate["decision"]["decision_timestamp"],
        holdout_opened_at=opened_at, portfolio_evaluation_enabled=False, gap_reset=True,
        synthetic=False, market_only=True, historical_identity_verified=False,
        holdout_snapshots=list(M2_HOLDOUT_SNAPSHOTS), methods_executed=[gate["algorithm"]],
        k_values_executed=[2])
    write_json(target / "manifest.json", manifest)
    try:
        source, prepared = prepare_holdout(root, gate)
        store = _path(root, config["feature_store"])
        manifest.update(c8_manifest_sha256=digest((store / "manifest.json").read_bytes()),
            c8_feature_sha256=source["outputs"]["canonical/feature_snapshots.jsonl"],
            feature_version="1.6.0", data_version=source["data_version"])
        snapshots, temporal, transitions, drift = fit_holdout(prepared, gate["clustering"], gate["algorithm"])
        model_dir.mkdir(parents=True, exist_ok=True)
        assignments, profiles, flat_profiles, diagnostics, scalers = [], [], [], [], []
        for snap in snapshots:
            day, ids = snap["snapshot_date"], snap["aligned_ids"]
            write_json(target / "models" / (day + ".json"), snap["model"])
            write_json(model_dir / (day + ".json"), snap["model"])
            assignments.extend(dict(snapshot_date=day, security_id=row["security_id"],
                raw_cluster_id=raw, aligned_cluster_id=ids[raw], run_id=target.name,
                data_version=source["data_version"]) for row, raw in zip(snap["rows"], snap["labels"]))
            for profile in snap["profiles"]:
                ratio = profile["size"] / len(snap["rows"])
                profiles.append(dict(profile, snapshot_date=day, aligned_cluster_id=ids[profile["raw_cluster_id"]], size_ratio=ratio))
                flat_profiles.append(dict(snapshot_date=day, raw_cluster_id=profile["raw_cluster_id"],
                    aligned_cluster_id=ids[profile["raw_cluster_id"]], size=profile["size"], size_ratio=ratio,
                    **{f: profile["centroid"][f] for f in M2_MARKET_FEATURES}))
            diagnostics.append(dict(snapshot_date=day, **snap["diagnostics"][0]))
            scalers.extend(dict(snapshot_date=day, feature=f, **snap["model"]["scaler"][f]) for f in M2_MARKET_FEATURES)
        for name, rows in [("assignments", assignments), ("profiles", profiles), ("diagnostics", diagnostics)]:
            write_rows(target / (name + ".jsonl"), rows)
        for name, rows in [("assignments", assignments), ("cluster_profiles", flat_profiles), ("diagnostics", diagnostics)]:
            # Nested diagnostic cluster sizes remain readable JSON in CSV.
            serial = [{k: encoded(v).decode() if isinstance(v, (dict, list)) else v for k, v in r.items()} for r in rows]
            _write_csv(target / (name + ".csv"), serial)
        eligibility = [dict(snapshot_date=p["snapshot_date"], status=p["status"], n_eligible=p["eligible_count"], reason=p["reason"])
                       for p in prepared]
        _write_csv(target / "snapshot_validation.csv", eligibility)
        write_rows(target / "skipped_snapshots.jsonl", [r for r in eligibility if r["status"] == "skipped"])
        _write_csv(target / "scaler_parameters.csv", [{k:v for k,v in r.items() if k != "rank_reference"} for r in scalers])
        _write_csv(target / "temporal_stability.csv", temporal, TEMPORAL_FIELDS)
        _write_csv(target / "transition_matrices.csv", transitions, TRANSITION_FIELDS)
        _write_csv(target / "centroid_drift.csv", drift, DRIFT_FIELDS)
        summary = [dict(metric=m, n_total=7, n_available=len(diagnostics), **_summary(r[m] for r in diagnostics)) for m in QUALITY]
        _write_csv(target / "quality_summary.csv", summary)
        dev_temporal = _csv_rows(gate["evaluation_dir"] / "temporal_stability.csv")
        gaps = []
        for metric in (*QUALITY, *TEMPORAL):
            dev_rows, hold_rows = (gate["dev_diagnostics"], diagnostics) if metric in QUALITY else (dev_temporal, temporal)
            if not hold_rows:
                continue
            a = median(float(r[metric]) for r in dev_rows)
            b = median(float(r[metric]) for r in hold_rows)
            gaps.append(dict(metric=metric, development_n=len(dev_rows), holdout_n=len(hold_rows),
                             development_median=a, holdout_median=b, delta_holdout_minus_development=b-a))
        _write_csv(target / "holdout_generalization_gap.csv", gaps)
        dev_profiles = _csv_rows(gate["evaluation_dir"] / "cluster_profiles.csv")
        profile_check = []
        for label, rows in [("development", dev_profiles), ("holdout", flat_profiles)]:
            grouped = defaultdict(list)
            for row in rows:
                grouped[row["snapshot_date"]].append(row)
            feature_name = lambda f: f if f in rows[0] else f + "_mean"
            ranked = defaultdict(list)
            for members in grouped.values():
                ordered = sorted(members, key=lambda r: -float(r[feature_name("mom_63")]))
                for role, row in zip(("Higher_mom63", "Lower_mom63"), ordered):
                    ranked[role].append(row)
            for role, members in ranked.items():
                for feature in M2_MARKET_FEATURES:
                    profile_check.append(dict(period=label, role=role, feature=feature, n_snapshots=len(members),
                        **_summary(float(r[feature_name(feature)]) for r in members)))
        _write_csv(target / "profile_consistency.csv", profile_check)
        write_json(target / "execution_config.json", dict(config, clustering=gate["clustering"]))
        code_files = [Path(__file__), root / "src/delta_t1/clustering/base.py",
            root / "src/delta_t1/clustering" / (gate["algorithm"] + ".py"),
            root / "src/delta_t1/features/preprocessing.py", root / "src/delta_t1/evaluation/cluster_metrics.py",
            root / "src/delta_t1/evaluation/temporal_metrics.py", root / "src/delta_t1/experiments/artifacts.py",
            root / "src/delta_t1/experiments/runner.py", root / "src/delta_t1/experiments/protocol.py"]
        manifest["code_sha256"] = {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in code_files}
        with zipfile.ZipFile(target / "source_snapshot.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for path in code_files:
                archive.write(path, path.relative_to(root).as_posix())
        _plot(target, gate["dev_diagnostics"], diagnostics)
        gap = next(r for r in gaps if r["metric"] == "silhouette")
        h = gap["holdout_median"]
        delta = gap["delta_holdout_minus_development"]
        details = "\n".join(f"| {r['metric']} | {r['development_median']:.6f} | {r['holdout_median']:.6f} | {r['delta_holdout_minus_development']:+.6f} |" for r in gaps)
        warning = ("Có suy giảm hình học đáng kể cần ghi nhận." if delta < -.20 or h < .50
                   else "Khoảng cách hình học được ghi nhận từ số liệu; chưa đủ để kết luận về chế độ vĩ mô hoặc sinh lợi.")
        profile_cells = {(r["period"], r["role"], r["feature"]): r["mean"] for r in profile_check}
        profile_lines = []
        for feature in M2_MARKET_FEATURES:
            divisor = 1e9 if feature == "liquidity_21" else 1
            title = feature + (" (tỷ VND)" if divisor == 1e9 else "")
            values = [profile_cells[period, role, feature] / divisor
                      for role in ("Higher_mom63", "Lower_mom63") for period in ("development", "holdout")]
            profile_lines.append("| " + title + " | " + " | ".join(f"{v:.6f}" for v in values) + " |")
        profile_details = "\n".join(profile_lines)
        minimum_cluster = min(p["size"] for p in profiles)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(f'''# Báo cáo Nhiệm vụ 11 — Final Holdout

## A — Gate và thực thi một chiều
Mô hình: **{gate['selected_method']}**, Global K=2; seed={gate['clustering'].get('seed')},
n_init={gate['clustering'].get('n_init')}, max_iter={gate['clustering'].get('max_iter')}.
Decision freeze: `{manifest['decision_timestamp']}`; mở holdout: `{opened_at}`.
Chạy {len(snapshots)}/7 snapshots, {len(assignments)} assignments và {len(temporal)}/6 cặp tháng.
Universe riêng mỗi tháng: {min(p['eligible_count'] for p in prepared)}–{max(p['eligible_count'] for p in prepared)} mã;
skip {7-len(snapshots)} snapshot. Robust Scaling fit mới từng snapshot;
chỉ algorithm thắng và K=2, không quét K hoặc chạy comparator.
Nguồn Feature Store 1.6.0: C8 checksummed `canonical/feature_snapshots.jsonl`;
không tạo bản sao hoặc sửa nguồn thành `data/canonical/market/`.

## B — Development so với Holdout
| Metric | Median Development | Median Holdout | Holdout − Development |
| --- | ---: | ---: | ---: |
{details}

Delta_Silhouette = {h:.6f} − {gap['development_median']:.6f} = **{delta:+.6f}**.
{warning} Các ngưỡng trong kế hoạch là rubric chẩn đoán, không tự chứng minh
không overfit hoặc Macro Regime Shift. Inertia phụ thuộc universe size.
Migration là chuyển nhãn trên tập mã chung, không phải turnover/chi phí danh mục.

![Development và Holdout](../artifacts/{target.name}/holdout_vs_dev_trajectory.png)

## C — Hồ sơ cụm, gap reset và giới hạn
`profile_consistency.csv` so sánh đủ 8 feature gốc, theo vai trò Higher/Lower mom_63
tại từng tháng; không giả định C0/C1 có cùng identity xuyên gap. Mean/Median ở đây
là tổng hợp các mean của cụm theo tháng, không phải median từng cổ phiếu.
Quy mô cụm nhỏ nhất trên holdout: **{minimum_cluster} mã**.

| Feature | Higher mom63 Dev mean | Higher mom63 Holdout mean | Lower mom63 Dev mean | Lower mom63 Holdout mean |
| --- | ---: | ---: | ---: | ---: |
{profile_details}

Thanh khoản trong artifact lưu VND, bảng trên đổi sang tỷ VND; momentum/risk ở thang gốc.
Không mặc định cụm momentum cao
phải thanh khoản lớn; không suy nguyên nhân vĩ mô chỉ từ profile.
Chuỗi holdout bắt đầu mới; không có cặp 2025-01-24 → 2026-02-27, không nối qua skip.
Đây là monthly independent clustering trong phạm vi market-only;
không phải dynamic clustering, strict research universe hoặc bằng chứng hiệu quả đầu tư.
Giữ nguyên phương pháp sau holdout; không retune bằng kết quả này.

## Cách mở và chạy lại
Mở `M2/notebooks/11_final_holdout_execution.ipynb`, chọn kernel Python đã dùng ở M2,
chạy từ repo hoặc thư mục notebook bằng Run All. Root được tìm tự động.
Lần chạy sau chỉ kiểm tra checksum và nạp artifacts đã hoàn tất, không fit lại.
Nếu inputs/checksum thay đổi hoặc run chưa complete, chương trình dừng để giữ evidence.
Nhiệm vụ 12/M3 chưa được thực hiện trong lần chạy này.
''', encoding="utf-8")
        # Freeze only after all exports exist; include model copies and the report.
        outputs = [p for p in target.rglob("*") if p.is_file() and p.name != "manifest.json"]
        outputs.extend(p for p in model_dir.glob("*.json"))
        outputs.append(report_path)
        manifest.update(status="complete", completed_at=now(), n_snapshots=len(snapshots),
            n_assignments=len(assignments), n_temporal_pairs=len(temporal), n_skipped=7-len(snapshots),
            delta_silhouette=delta, artifacts={p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in outputs})
        write_json(target / "manifest.json", manifest)
    except Exception as exc:
        manifest.update(status="failed", error=type(exc).__name__ + ": " + str(exc), finished_at=now())
        write_json(target / "manifest.json", manifest)
        raise
    return verify_existing(root, gate)
