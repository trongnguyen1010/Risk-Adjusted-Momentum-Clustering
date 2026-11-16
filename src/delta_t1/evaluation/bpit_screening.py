"""
delta_t1.evaluation.bpit_screening

Đo lường chất lượng và độ ổn định của các cấu hình phân cụm B-PIT (Stage D: Task R1-10).
Bao gồm:
  1. Thước đo nội bộ trong không gian T1:
     - Silhouette Score (càng cao càng tốt)
     - Davies-Bouldin Score (càng thấp càng tốt)
     - Calinski-Harabasz Score (càng cao càng tốt)
  2. Kích thước và tỷ trọng cụm nhỏ nhất (min_cluster_share).
  3. Độ ổn định lấy mẫu con (subsample stability 90% với các seed đã pin: ARI).
  4. Độ ổn định thời gian (temporal ARI giữa 2 FY liên tiếp trên tập mã chung).
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
)

def compute_cluster_quality_metrics(
    x_t1: np.ndarray,
    labels: np.ndarray,
    k: int,
) -> Dict[str, Any]:
    """
    Tính Silhouette, Davies-Bouldin, Calinski-Harabasz và phân bố kích thước cụm.
    Tất cả đo trong không gian T1.
    """
    n = len(x_t1)
    unique_labels = np.unique(labels)
    n_unique = len(unique_labels)

    counts = np.bincount(labels, minlength=k)
    shares = counts / float(n) if n > 0 else np.zeros(k)
    min_share = float(np.min(shares)) if len(shares) > 0 else 0.0

    # Nếu số cụm thực tế < 2 hoặc mọi mẫu cùng 1 cụm thì không đo được
    if n_unique < 2 or n_unique >= n:
        return {
            "silhouette": None,
            "davies_bouldin": None,
            "calinski_harabasz": None,
            "cluster_sizes": {c: int(counts[c]) for c in range(k)},
            "cluster_shares": {c: float(shares[c]) for c in range(k)},
            "min_cluster_share": min_share,
            "valid": False,
        }

    try:
        sil = float(silhouette_score(x_t1, labels))
    except Exception:
        sil = None

    try:
        db = float(davies_bouldin_score(x_t1, labels))
    except Exception:
        db = None

    try:
        ch = float(calinski_harabasz_score(x_t1, labels))
    except Exception:
        ch = None

    return {
        "silhouette": sil,
        "davies_bouldin": db,
        "calinski_harabasz": ch,
        "cluster_sizes": {c: int(counts[c]) for c in range(k)},
        "cluster_shares": {c: float(shares[c]) for c in range(k)},
        "min_cluster_share": min_share,
        "valid": True,
    }

def compute_subsample_stability(
    adapter_cls: Any,
    adapter_kwargs: Dict[str, Any],
    x_fit: np.ndarray,
    raw_fit: np.ndarray,
    features: Tuple[str, ...],
    full_labels: np.ndarray,
    subsample_ratio: float = 0.9,
    seeds: Tuple[int, ...] = (1, 2, 3),
) -> Tuple[float, List[float]]:
    """
    Đo độ ổn định bằng ARI giữa fit đầy đủ và refit trên mẫu con (subsample 90%)
    với danh sách các seed đã pin.
    """
    n = len(x_fit)
    n_sub = int(np.floor(n * subsample_ratio))
    if n_sub < 10:
        return 0.0, []

    aris: List[float] = []
    for s in seeds:
        rng = np.random.RandomState(s)
        sub_indices = rng.choice(n, size=n_sub, replace=False)
        sub_indices.sort()

        # Tạo bản sao adapter mới cho subsample
        kw = dict(adapter_kwargs)
        if "seed" in kw:
            kw["seed"] = s  # pin seed theo lượt
        sub_adapter = adapter_cls(**kw)

        try:
            sub_labels = sub_adapter.fit(
                x_fit[sub_indices],
                raw_fit[sub_indices],
                features,
            )
            ari = float(adjusted_rand_score(full_labels[sub_indices], sub_labels))
            aris.append(ari)
        except Exception:
            aris.append(0.0)

    med_ari = float(np.median(aris)) if aris else 0.0
    return med_ari, aris

def compute_temporal_ari(
    tickers_prev: List[str],
    labels_prev: np.ndarray,
    tickers_curr: List[str],
    labels_curr: np.ndarray,
) -> Optional[float]:
    """
    Tính ARI giữa hai năm tài chính liên tiếp trên tập các mã FIT chung.
    """
    common_tickers = sorted(set(tickers_prev).intersection(set(tickers_curr)))
    if len(common_tickers) < 2:
        return None

    prev_map = {t: lab for t, lab in zip(tickers_prev, labels_prev)}
    curr_map = {t: lab for t, lab in zip(tickers_curr, labels_curr)}

    y_prev = [prev_map[t] for t in common_tickers]
    y_curr = [curr_map[t] for t in common_tickers]

    return float(adjusted_rand_score(y_prev, y_curr))
