#!/usr/bin/env python3
"""
scripts/build_financial_pit_clusters_enriched.py

Pipeline huấn luyện và xuất artifact phân cụm tài chính B-PIT Enriched (Stage D: Task R1-12).
Thực hiện:
  1. Nạp dữ liệu tài chính làm giàu từ Stage C (indicators_enriched_v1).
  2. Sàng lọc 24 ứng viên (K-Means, PCA+K-Means, Ward, GMM với k=3..8) trên FY2017–FY2022.
  3. Chọn cấu hình tối ưu theo quy tắc đa tiêu chí (hoặc fallback đối chứng K-Means k=3).
  4. Đóng băng và fit mô hình cho từng FY2017–FY2024 (bao gồm tập kiểm định FY2023–FY2024).
  5. Xuất artifact B-PIT: labels.csv, models.json, audit.json, manifest.json.
  6. Kiểm tra bất biến fit_leaks = 0.
"""

import argparse
import csv
import json
import subprocess
import hashlib
from pathlib import Path
import numpy as np

from delta_t1.m3 import bpit
from delta_t1.clustering.robust_transforms import fit_t1, apply_t1
from delta_t1.experiments.bpit_enriched import (
    build_enriched_snapshots,
    create_adapter,
    evaluate_candidate,
    rank_and_select_candidates,
    EnrichedSnapshot,
)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"

def main():
    parser = argparse.ArgumentParser(description="Build B-PIT Enriched Artifacts")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/experiments/bpit_enriched_v1.json"),
        help="Đường dẫn file cấu hình bpit_enriched_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01"),
        help="Thư mục xuất artifact B-PIT",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    config_path = (repo_root / args.config).resolve()
    output_dir = (repo_root / args.output_dir).resolve()

    print("======================================================================")
    print(" B-PIT ENRICHED CLUSTERING & ARTIFACT GENERATOR (STAGE D)")
    print("======================================================================")
    print(f"Config:     {config_path}")
    print(f"Output dir: {output_dir}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs_cfg = config["inputs"]
    indicators_db = (repo_root / inputs_cfg["indicators_enriched_path"]).resolve()
    availability_csv = (repo_root / inputs_cfg["availability_path"]).resolve()
    baseline_bpit_dir = (repo_root / inputs_cfg["baseline_bpit_path"]).resolve()

    assert indicators_db.exists(), f"Không tìm thấy {indicators_db}"
    assert availability_csv.exists(), f"Không tìm thấy {availability_csv}"
    assert baseline_bpit_dir.exists(), f"Không tìm thấy {baseline_bpit_dir}"

    # 1. Nạp snapshots
    features = tuple(config.get("features", bpit.FEATURES))
    scope = config.get("scope", {})
    selection_years = scope.get("fiscal_years_selection", list(range(2017, 2023)))
    validation_years = scope.get("fiscal_years_validation", [2023, 2024])
    all_years = sorted(selection_years + validation_years)

    print(f"\n[1/4] Đang nạp snapshots cho {len(all_years)} năm ({all_years})...")
    snapshots = build_enriched_snapshots(
        sqlite_path=indicators_db,
        availability_path=availability_csv,
        features=features,
        years=range(min(all_years), max(all_years) + 1),
        opt_in_statuses=tuple(config.get("loader", {}).get("opt_in_statuses", ("OK", "IMPUTED_MEDIAN"))),
    )
    snap_by_year = {s.fiscal_year: s for s in snapshots}
    print(f"  -> Đã nạp thành công {len(snapshots)} snapshots.")

    # 2. Sàng lọc 24 ứng viên trên selection_years
    selection_snaps = [s for s in snapshots if s.fiscal_year in selection_years]
    k_candidates = config.get("k_candidates", [3, 4, 5, 6, 7, 8])
    algorithms = ["kmeans", "pca_kmeans", "ward", "gmm"]

    print(f"\n[2/4] Đang chạy sàng lọc {len(algorithms) * len(k_candidates)} ứng viên trên FY{selection_years[0]}–FY{selection_years[-1]}...")
    eval_results = []
    for algo in algorithms:
        for k in k_candidates:
            res = evaluate_candidate(algo, k, selection_snaps, config)
            eval_results.append(res)
            status_str = "ADMISSIBLE" if res["is_admissible"] else "REJECTED"
            print(f"  - {algo:10s} k={k} | Stab={res['median_stability']:.3f} | Sil={res['median_silhouette'] or 0:.3f} | DB={res['median_davies_bouldin'] or 0:.3f} -> {status_str}")

    # 3. Chọn mô hình thắng cuộc
    winner, ranked = rank_and_select_candidates(eval_results)
    if winner is not None:
        winning_algo = winner["algo"]
        winning_k = winner["k"]
        print(f"\n[3/4] KẾT QUẢ SÀNG LỌC: Cấu hình chiến thắng là {winning_algo} (k={winning_k}) với mean_rank = {winner['mean_rank']:.2f}")
    else:
        print("\n[3/4] Không có ứng viên nào vượt qua ngưỡng Admissibility! Fallback về đối chứng K-Means k=3.")
        winning_algo = "kmeans"
        winning_k = 3

    # 4. Fit và sinh nhãn toàn diện cho mọi năm
    print(f"\n[4/4] Đang fit mô hình {winning_algo} (k={winning_k}) và xuất artifact...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    label_rows = []
    models_dict = {}
    audit_dict = {
        "status": "OK",
        "winning_algo": winning_algo,
        "winning_k": winning_k,
        "screening_results": eval_results,
        "fit_leaks": {},
        "years": {},
    }

    for snap in snapshots:
        y = snap.fiscal_year
        fit_idx = np.where(snap.fit_mask)[0]
        late_idx = np.where(~snap.fit_mask)[0]

        raw_fit = snap.raw[fit_idx]
        t1_params = fit_t1(raw_fit, snap.features)
        x_t1 = apply_t1(snap.raw, t1_params)
        x_fit = x_t1[fit_idx]

        adapter = create_adapter(winning_algo, winning_k, config)
        labels_fit = adapter.fit(x_fit, raw_fit, snap.features)

        # Gán cho các mã late (sau cutoff hoặc thiếu ngày)
        all_labels = np.empty(len(snap.tickers), dtype=int)
        all_labels[fit_idx] = labels_fit
        if len(late_idx) > 0:
            x_late = x_t1[late_idx]
            labels_late = adapter.assign_late(x_late)
            all_labels[late_idx] = labels_late

        # Kiểm tra fit_leaks
        leaks = [
            snap.tickers[i]
            for i in fit_idx
            if not snap.usable_dates[i] or snap.usable_dates[i] > snap.cutoff
        ]
        if leaks:
            audit_dict["fit_leaks"][str(y)] = leaks

        # Ghi labels.csv
        for i, t in enumerate(snap.tickers):
            d = snap.usable_dates[i]
            role = "FIT" if snap.fit_mask[i] else ("ASSIGNED_AFTER_CUTOFF" if d else "ASSIGNED_NO_DATE")
            label_rows.append({
                "ticker": t,
                "fiscal_year": y,
                "cluster": int(all_labels[i]),
                "role": role,
                "usable_from_date": d,
            })

        # Ghi models.json
        models_dict[str(y)] = {
            "cutoff": snap.cutoff,
            "n_fit": len(fit_idx),
            "n_assigned": len(late_idx),
            "features": list(snap.features),
            "k": winning_k,
            "algorithm": winning_algo,
            "t1": {
                "lo": t1_params["lo"].tolist(),
                "hi": t1_params["hi"].tolist(),
                "mean": t1_params["mean"].tolist(),
                "sd": t1_params["sd"].tolist(),
            },
            "centroids": adapter.centroids.tolist() if adapter.centroids is not None else [],
            "cluster_order": adapter.cluster_order or list(range(winning_k)),
        }

        audit_dict["years"][str(y)] = {
            "cutoff": snap.cutoff,
            "n_fit": len(fit_idx),
            "n_assigned": len(late_idx),
            "sizes": {str(c): int(np.sum(all_labels == c)) for c in range(winning_k)},
            "cluster_order": adapter.cluster_order,
        }

    # Xuất các tệp
    labels_path = output_dir / "labels.csv"
    with open(labels_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticker", "fiscal_year", "cluster", "role", "usable_from_date"])
        writer.writeheader()
        writer.writerows(label_rows)

    models_path = output_dir / "models.json"
    models_path.write_text(json.dumps(models_dict, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_path = output_dir / "audit.json"
    audit_path.write_text(json.dumps(audit_dict, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "version": "bpit_enriched_v1",
        "git_commit": get_git_commit(),
        "inputs": {
            "indicators_enriched_sha256": sha256_file(indicators_db),
            "availability_sha256": sha256_file(availability_csv),
            "config_sha256": sha256_file(config_path),
        },
        "outputs": {
            "labels_csv_sha256": sha256_file(labels_path),
            "models_json_sha256": sha256_file(models_path),
            "audit_json_sha256": sha256_file(audit_path),
        },
        "selected_model": {
            "algorithm": winning_algo,
            "k": winning_k,
        },
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n----------------------------------------------------------------------")
    print("HOÀN THÀNH XUẤT ARTIFACT B-PIT ENRICHED:")
    print(f"  - Labels CSV:   {labels_path} (SHA-256: {manifest['outputs']['labels_csv_sha256'][:16]}...)")
    print(f"  - Models JSON:  {models_path}")
    print(f"  - Audit JSON:   {audit_path}")
    print(f"  - Manifest:     {manifest_path}")
    print(f"  - Fit Leaks:    {len(audit_dict['fit_leaks'])} lỗi")
    print("======================================================================")

if __name__ == "__main__":
    main()
