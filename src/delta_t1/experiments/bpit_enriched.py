"""
delta_t1.experiments.bpit_enriched

Thực nghiệm phân cụm tài chính B-PIT trên tập dữ liệu làm giàu (Stage D).
Task R1-07: Chuẩn hóa cohort và loader enriched.
- Đọc dữ liệu từ SQLite dẫn xuất với opt-in status = ('OK', 'IMPUTED_MEDIAN').
- Tạo cohort FIT gồm: các mã FIT gốc + các mã hoàn tất 9/9 nhờ làm giàu có usable_from_date <= cutoff.
- Bảo đảm bất biến: fit_leaks = 0, cutoff và availability giữ nguyên.
"""

import sqlite3
import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, NamedTuple, Any
import numpy as np

from delta_t1.m3 import bpit
from delta_t1.clustering.robust_transforms import fit_t1, apply_t1
from delta_t1.clustering.bpit_adapters import (
    BpitKMeansAdapter,
    BpitPcaKMeansAdapter,
    BpitWardAdapter,
    BpitGmmAdapter,
)
from delta_t1.evaluation.bpit_screening import (
    compute_cluster_quality_metrics,
    compute_subsample_stability,
    compute_temporal_ari,
)

class EnrichedSnapshot(NamedTuple):
    fiscal_year: int
    tickers: List[str]
    raw: np.ndarray
    usable_dates: List[str]
    cutoff: str
    fit_mask: np.ndarray  # bool mask indicating which tickers belong to FIT cohort
    features: Tuple[str, ...]

def load_enriched_indicators(
    sqlite_path: Path,
    features: Tuple[str, ...] = bpit.FEATURES,
    sector: str = "NON_FINANCIAL",
    years: range = range(2016, 2026),
    opt_in_statuses: Tuple[str, ...] = ("OK", "IMPUTED_MEDIAN"),
) -> Dict[int, Dict[str, Dict[str, float]]]:
    """
    Đọc dữ liệu tài chính từ SQLite dẫn xuất.
    Chỉ nạp các ô có status nằm trong opt_in_statuses.
    Trả về: dict {fiscal_year: {ticker: {metric: value}}}
    """
    sqlite_path = Path(sqlite_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"Không tìm thấy SQLite tại {sqlite_path}")

    marks_features = ",".join("?" * len(features))
    marks_statuses = ",".join("?" * len(opt_in_statuses))

    db = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        allowed_tickers = {
            t for (t,) in db.execute(
                "SELECT ticker FROM company WHERE sector_group = ?", (sector,)
            )
        }
        query = f"""
            SELECT ticker, fiscal_year, metric, value
            FROM indicator_values
            WHERE status IN ({marks_statuses})
              AND metric IN ({marks_features})
              AND value IS NOT NULL
        """
        rows = db.execute(query, (*opt_in_statuses, *features)).fetchall()
    finally:
        db.close()

    data: Dict[int, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for t, y, m, v in rows:
        if t in allowed_tickers and y in years:
            data[y][t][m] = float(v)

    return dict(data)

def load_availability_map(availability_csv_path: Path) -> Dict[Tuple[str, int], str]:
    """
    Đọc bảng ngày công bố báo cáo tài chính (availability.csv).
    Áp dụng đúng logic M3: LAG_RULE trước FY2022 và CAFEF_DISCLOSURE từ FY2022.
    """
    avail = {}
    with open(availability_csv_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            y = int(r["fiscal_year"])
            source_req = "LAG_RULE" if y < 2022 else "CAFEF_DISCLOSURE"
            if r.get("date_source") == source_req:
                avail[(r["ticker"], y)] = r.get("usable_from_date", "")
    return avail

def build_enriched_snapshots(
    sqlite_path: Path,
    availability_path: Path,
    features: Tuple[str, ...] = bpit.FEATURES,
    years: range = range(2017, 2025),
    opt_in_statuses: Tuple[str, ...] = ("OK", "IMPUTED_MEDIAN"),
    sector: str = "NON_FINANCIAL",
    pinned_cutoffs: Optional[Dict[int, str]] = None,
) -> List[EnrichedSnapshot]:
    """
    Xây dựng danh sách các Snapshot hoàn chỉnh (đủ 9/9 đặc trưng) theo từng FY.
    Xác định cohort FIT và kiểm tra fit_leaks = 0.
    """
    data = load_enriched_indicators(
        sqlite_path=sqlite_path,
        features=features,
        sector=sector,
        years=years,
        opt_in_statuses=opt_in_statuses,
    )
    avail_map = load_availability_map(availability_path)

    snapshots: List[EnrichedSnapshot] = []

    for y in sorted(years):
        if y not in data:
            continue
        y_data = data[y]
        
        # Lọc các công ty có đủ 9/9 đặc trưng
        complete_tickers = sorted(
            [t for t, mdict in y_data.items() if len(mdict) == len(features) and all(m in mdict for m in features)]
        )
        if not complete_tickers:
            continue

        raw_matrix = np.array(
            [[y_data[t][m] for m in features] for t in complete_tickers],
            dtype=float,
        )
        usable_dates = [avail_map.get((t, y), "") for t in complete_tickers]

        # Xác định cutoff
        if pinned_cutoffs and y in pinned_cutoffs:
            cutoff = pinned_cutoffs[y]
        else:
            cutoff = bpit.cutoff_for(y, usable_dates)

        # Xác định FIT cohort: có usable_from_date và usable_from_date <= cutoff
        fit_mask = np.array([bool(d) and d <= cutoff for d in usable_dates], dtype=bool)

        # Kiểm tra bất biến fit_leaks = 0
        leaks = [
            complete_tickers[i]
            for i, (is_fit, d) in enumerate(zip(fit_mask, usable_dates))
            if is_fit and (not d or d > cutoff)
        ]
        if leaks:
            raise ValueError(f"FY{y} phát hiện fit_leaks: {leaks}")

        snapshots.append(
            EnrichedSnapshot(
                fiscal_year=y,
                tickers=complete_tickers,
                raw=raw_matrix,
                usable_dates=usable_dates,
                cutoff=cutoff,
                fit_mask=fit_mask,
                features=features,
            )
        )

    return snapshots

def create_adapter(algo: str, k: int, config: Optional[Dict[str, Any]] = None) -> Any:
    """Tạo instance adapter theo thuật toán, k và config tham chiếu."""
    cfg = config or {}
    seed = cfg.get("seed", 42)
    algos_cfg = cfg.get("algorithms", {})

    if algo == "kmeans":
        n_init = algos_cfg.get("kmeans", {}).get("n_init", 10)
        return BpitKMeansAdapter(k=k, seed=seed, n_init=n_init)
    elif algo == "pca_kmeans":
        pk_cfg = algos_cfg.get("pca_kmeans", {})
        variance = pk_cfg.get("variance", 0.8)
        n_init = pk_cfg.get("n_init", 10)
        return BpitPcaKMeansAdapter(k=k, variance=variance, seed=seed, n_init=n_init)
    elif algo == "ward":
        return BpitWardAdapter(k=k)
    elif algo == "gmm":
        g_cfg = algos_cfg.get("gmm", {})
        return BpitGmmAdapter(
            k=k,
            seed=seed,
            covariance_type=g_cfg.get("covariance_type", "full"),
            n_init=g_cfg.get("n_init", 2),
            reg_covar=g_cfg.get("reg_covar", 1e-4),
            max_iter=g_cfg.get("max_iter", 300),
        )
    else:
        raise ValueError(f"Thuật toán không hỗ trợ: {algo}")

def evaluate_candidate(
    algo: str,
    k: int,
    snapshots: List[EnrichedSnapshot],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Đánh giá một cặp (thuật toán, k) trên danh sách snapshots (FY2017–FY2022).
    Đo 5 thước đo: Silhouette, Davies-Bouldin, Calinski-Harabasz, Subsample Stability, Temporal ARI.
    """
    cfg = config or {}
    stability_cfg = cfg.get("stability", {})
    subsample_ratio = stability_cfg.get("subsample", 0.9)
    stability_seeds = tuple(stability_cfg.get("seeds", [1, 2, 3]))

    admissible_cfg = cfg.get("admissible", {})
    min_cluster_share_thresh = admissible_cfg.get("min_cluster_share", 0.05)
    share_of_snapshots_thresh = admissible_cfg.get("share_of_snapshots", 0.8)
    median_stability_thresh = admissible_cfg.get("median_stability", 0.8)

    fy_metrics: Dict[int, Dict[str, Any]] = {}
    prev_tickers: Optional[List[str]] = None
    prev_labels: Optional[np.ndarray] = None
    temporal_aris: List[float] = []

    for snap in snapshots:
        y = snap.fiscal_year
        fit_idx = np.where(snap.fit_mask)[0]
        if len(fit_idx) < 2 * k:
            continue

        raw_fit = snap.raw[fit_idx]
        t1_params = fit_t1(raw_fit, snap.features)
        x_t1 = apply_t1(snap.raw, t1_params)
        x_fit = x_t1[fit_idx]

        adapter = create_adapter(algo, k, cfg)
        labels_fit = adapter.fit(x_fit, raw_fit, snap.features)

        # 1. Thước đo nội bộ
        q_metrics = compute_cluster_quality_metrics(x_fit, labels_fit, k)

        # 2. Độ ổn định lấy mẫu con
        adapter_cls = type(adapter)
        # Khởi tạo kwargs cho adapter_cls
        adapter_kwargs = {"k": k}
        if hasattr(adapter, "seed"):
            adapter_kwargs["seed"] = adapter.seed
        if hasattr(adapter, "n_init"):
            adapter_kwargs["n_init"] = adapter.n_init
        if hasattr(adapter, "variance"):
            adapter_kwargs["variance"] = adapter.variance

        med_stab, _ = compute_subsample_stability(
            adapter_cls=adapter_cls,
            adapter_kwargs=adapter_kwargs,
            x_fit=x_fit,
            raw_fit=raw_fit,
            features=snap.features,
            full_labels=labels_fit,
            subsample_ratio=subsample_ratio,
            seeds=stability_seeds,
        )

        # 3. Temporal ARI với FY trước
        fit_tickers = [snap.tickers[i] for i in fit_idx]
        if prev_tickers is not None and prev_labels is not None:
            t_ari = compute_temporal_ari(prev_tickers, prev_labels, fit_tickers, labels_fit)
            if t_ari is not None:
                temporal_aris.append(t_ari)

        prev_tickers = fit_tickers
        prev_labels = labels_fit

        fy_metrics[y] = {
            "silhouette": q_metrics["silhouette"],
            "davies_bouldin": q_metrics["davies_bouldin"],
            "calinski_harabasz": q_metrics["calinski_harabasz"],
            "min_cluster_share": q_metrics["min_cluster_share"],
            "subsample_stability": med_stab,
        }

    # Tổng hợp median của 5 thước đo
    sil_vals = [m["silhouette"] for m in fy_metrics.values() if m["silhouette"] is not None]
    db_vals = [m["davies_bouldin"] for m in fy_metrics.values() if m["davies_bouldin"] is not None]
    ch_vals = [m["calinski_harabasz"] for m in fy_metrics.values() if m["calinski_harabasz"] is not None]
    stab_vals = [m["subsample_stability"] for m in fy_metrics.values()]
    shares_ok = [m["min_cluster_share"] >= min_cluster_share_thresh for m in fy_metrics.values()]

    med_sil = float(np.median(sil_vals)) if sil_vals else None
    med_db = float(np.median(db_vals)) if db_vals else None
    med_ch = float(np.median(ch_vals)) if ch_vals else None
    med_stab_all = float(np.median(stab_vals)) if stab_vals else 0.0
    med_temp_ari = float(np.median(temporal_aris)) if temporal_aris else 0.0

    # Kiểm tra cổng Admissibility
    share_of_snapshots_ok = (sum(shares_ok) / float(len(shares_ok))) >= share_of_snapshots_thresh if shares_ok else False
    stability_ok = med_stab_all >= median_stability_thresh
    is_admissible = bool(share_of_snapshots_ok and stability_ok)

    return {
        "algo": algo,
        "k": k,
        "median_silhouette": med_sil,
        "median_davies_bouldin": med_db,
        "median_calinski_harabasz": med_ch,
        "median_stability": med_stab_all,
        "median_temporal_ari": med_temp_ari,
        "share_of_snapshots_ok": share_of_snapshots_ok,
        "stability_ok": stability_ok,
        "is_admissible": is_admissible,
        "fy_metrics": fy_metrics,
    }

def rank_and_select_candidates(
    eval_results: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Xếp hạng các ứng viên đạt admissibility theo trung bình hạng của 5 thước đo.
    Quy tắc hòa: k nhỏ hơn -> K-Means -> PCA+K-Means -> Ward -> GMM.
    """
    algo_priority = {"kmeans": 1, "pca_kmeans": 2, "ward": 3, "gmm": 4}
    admissible = [r for r in eval_results if r["is_admissible"]]

    if not admissible:
        # Nếu không có ứng viên nào đạt, trả về None (sẽ fallback đối chứng k=3)
        return None, eval_results

    m = len(admissible)
    # Tính rank (1 = tốt nhất) cho từng thước đo
    # 1. Silhouette: cao tốt -> xếp giảm dần
    sil_order = np.argsort([- (r["median_silhouette"] or -np.inf) for r in admissible])
    sil_ranks = np.empty(m)
    sil_ranks[sil_order] = np.arange(1, m + 1)

    # 2. Davies-Bouldin: thấp tốt -> xếp tăng dần
    db_order = np.argsort([(r["median_davies_bouldin"] or np.inf) for r in admissible])
    db_ranks = np.empty(m)
    db_ranks[db_order] = np.arange(1, m + 1)

    # 3. Calinski-Harabasz: cao tốt -> xếp giảm dần
    ch_order = np.argsort([- (r["median_calinski_harabasz"] or -np.inf) for r in admissible])
    ch_ranks = np.empty(m)
    ch_ranks[ch_order] = np.arange(1, m + 1)

    # 4. Stability: cao tốt -> xếp giảm dần
    stab_order = np.argsort([- r["median_stability"] for r in admissible])
    stab_ranks = np.empty(m)
    stab_ranks[stab_order] = np.arange(1, m + 1)

    # 5. Temporal ARI: cao tốt -> xếp giảm dần
    temp_order = np.argsort([- r["median_temporal_ari"] for r in admissible])
    temp_ranks = np.empty(m)
    temp_ranks[temp_order] = np.arange(1, m + 1)

    for i, r in enumerate(admissible):
        r["mean_rank"] = float(
            (sil_ranks[i] + db_ranks[i] + ch_ranks[i] + stab_ranks[i] + temp_ranks[i]) / 5.0
        )

    # Sắp xếp chọn người thắng:
    # 1. mean_rank tăng dần
    # 2. k tăng dần (ưu tiên k nhỏ)
    # 3. algo priority
    sorted_admissible = sorted(
        admissible,
        key=lambda r: (r["mean_rank"], r["k"], algo_priority.get(r["algo"], 99)),
    )

    winner = sorted_admissible[0]
    return winner, sorted_admissible

