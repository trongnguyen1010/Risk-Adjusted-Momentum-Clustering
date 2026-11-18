"""
delta_t1.clustering.bpit_adapters

Bộ Adapter thuật toán phân cụm cho B-PIT M3 (Stage D).
Hỗ trợ:
  - K-Means (k = 3..8, n_init, seed)
  - PCA + K-Means (giữ 80% phương sai, n_init, seed)
  - Ward (AgglomerativeClustering linkage='ward') [Task R1-09]
  - GMM (GaussianMixture covariance='full') [Task R1-09]

Nguyên tắc:
  - Fit duy nhất trên tập FIT cohort.
  - Gán sau cutoff (late assignment) sử dụng transform và model đã đóng băng, không refit.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture

from delta_t1.clustering.robust_transforms import nearest_centroid

def renumber_by_size(labels: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Đánh lại nhãn theo thứ tự kích thước cụm giảm dần (cụm 0 là cụm đông nhất).
    Trả về: (remapped_labels, mapping_array)
    """
    counts = np.bincount(labels, minlength=k)
    order = np.argsort(-counts, kind="stable")
    remap = np.empty(k, dtype=int)
    remap[order] = np.arange(k)
    return remap[labels], remap

def compute_cluster_order(
    raw_fit: np.ndarray,
    labels_fit: np.ndarray,
    features: Tuple[str, ...],
    k: int,
) -> List[int]:
    """
    Xác định thứ tự chất lượng cụm theo quy tắc B-PIT:
    Trung vị ROE giảm dần, hòa thì trung vị Debt-to-Equity tăng dần.
    """
    roe_idx = features.index("roe") if "roe" in features else None
    de_idx = features.index("debt_to_equity") if "debt_to_equity" in features else None

    cluster_stats = []
    for c in range(k):
        mask = labels_fit == c
        if not mask.any():
            cluster_stats.append((c, -np.inf, np.inf))
            continue
        c_raw = raw_fit[mask]
        med_roe = float(np.median(c_raw[:, roe_idx])) if roe_idx is not None else 0.0
        med_de = float(np.median(c_raw[:, de_idx])) if de_idx is not None else 0.0
        cluster_stats.append((c, med_roe, med_de))

    # Sắp xếp: ROE desc (-med_roe), DE asc (med_de)
    sorted_stats = sorted(cluster_stats, key=lambda x: (-x[1], x[2]))
    return [c for c, _, _ in sorted_stats]

class BpitKMeansAdapter:
    """Adapter cho thuật toán K-Means tiêu chuẩn."""
    def __init__(self, k: int, seed: int = 42, n_init: int = 10):
        self.k = k
        self.seed = seed
        self.n_init = n_init
        self.model: Optional[KMeans] = None
        self.centroids: Optional[np.ndarray] = None
        self.cluster_order: Optional[List[int]] = None

    def fit(self, x_fit: np.ndarray, raw_fit: np.ndarray, features: Tuple[str, ...]) -> np.ndarray:
        km = KMeans(n_clusters=self.k, n_init=self.n_init, random_state=self.seed)
        raw_labels = km.fit_predict(x_fit)
        labels_fit, _ = renumber_by_size(raw_labels, self.k)
        
        # Tính lại centroids theo nhãn đã renumber
        centroids = np.array([x_fit[labels_fit == c].mean(axis=0) for c in range(self.k)])
        
        self.model = km
        self.centroids = centroids
        self.cluster_order = compute_cluster_order(raw_fit, labels_fit, features, self.k)
        return labels_fit

    def assign_late(self, x_late: np.ndarray) -> np.ndarray:
        if self.centroids is None:
            raise ValueError("Mô hình chưa được fit.")
        return nearest_centroid(x_late, self.centroids)

class BpitPcaKMeansAdapter:
    """Adapter cho thuật toán PCA + K-Means (giữ variance 80%)."""
    def __init__(self, k: int, variance: float = 0.8, seed: int = 42, n_init: int = 10):
        self.k = k
        self.variance = variance
        self.seed = seed
        self.n_init = n_init
        self.pca: Optional[PCA] = None
        self.kmeans: Optional[KMeans] = None
        self.centroids_pca: Optional[np.ndarray] = None
        self.centroids_t1: Optional[np.ndarray] = None
        self.cluster_order: Optional[List[int]] = None

    def fit(self, x_fit: np.ndarray, raw_fit: np.ndarray, features: Tuple[str, ...]) -> np.ndarray:
        pca = PCA(n_components=self.variance, random_state=self.seed)
        x_pca = pca.fit_transform(x_fit)

        km = KMeans(n_clusters=self.k, n_init=self.n_init, random_state=self.seed)
        raw_labels = km.fit_predict(x_pca)
        labels_fit, _ = renumber_by_size(raw_labels, self.k)

        centroids_pca = np.array([x_pca[labels_fit == c].mean(axis=0) for c in range(self.k)])
        centroids_t1 = np.array([x_fit[labels_fit == c].mean(axis=0) for c in range(self.k)])

        self.pca = pca
        self.kmeans = km
        self.centroids_pca = centroids_pca
        self.centroids_t1 = centroids_t1
        self.cluster_order = compute_cluster_order(raw_fit, labels_fit, features, self.k)
        return labels_fit

    def assign_late(self, x_late: np.ndarray) -> np.ndarray:
        if self.pca is None or self.centroids_pca is None:
            raise ValueError("Mô hình chưa được fit.")
        x_late_pca = self.pca.transform(x_late)
        return nearest_centroid(x_late_pca, self.centroids_pca)

class BpitWardAdapter:
    """Adapter cho thuật toán phân cụm phân cấp Ward (linkage='ward')."""
    def __init__(self, k: int):
        self.k = k
        self.model: Optional[AgglomerativeClustering] = None
        self.centroids: Optional[np.ndarray] = None
        self.cluster_order: Optional[List[int]] = None

    def fit(self, x_fit: np.ndarray, raw_fit: np.ndarray, features: Tuple[str, ...]) -> np.ndarray:
        ward = AgglomerativeClustering(n_clusters=self.k, linkage="ward")
        raw_labels = ward.fit_predict(x_fit)
        labels_fit, _ = renumber_by_size(raw_labels, self.k)

        # Trọng tâm cụm trong không gian T1
        centroids = np.array([x_fit[labels_fit == c].mean(axis=0) for c in range(self.k)])

        self.model = ward
        self.centroids = centroids
        self.cluster_order = compute_cluster_order(raw_fit, labels_fit, features, self.k)
        return labels_fit

    def assign_late(self, x_late: np.ndarray) -> np.ndarray:
        if self.centroids is None:
            raise ValueError("Mô hình chưa được fit.")
        # Ward gán late bằng trọng tâm gần nhất trong không gian T1
        return nearest_centroid(x_late, self.centroids)

class BpitGmmAdapter:
    """Adapter cho mô hình Gaussian Mixture Model (GMM)."""
    def __init__(
        self,
        k: int,
        seed: int = 42,
        covariance_type: str = "full",
        n_init: int = 2,
        reg_covar: float = 1e-4,
        max_iter: int = 300,
    ):
        self.k = k
        self.seed = seed
        self.covariance_type = covariance_type
        self.n_init = n_init
        self.reg_covar = reg_covar
        self.max_iter = max_iter
        self.model: Optional[GaussianMixture] = None
        self.remap: Optional[np.ndarray] = None
        self.centroids: Optional[np.ndarray] = None
        self.cluster_order: Optional[List[int]] = None

    def fit(self, x_fit: np.ndarray, raw_fit: np.ndarray, features: Tuple[str, ...]) -> np.ndarray:
        gmm = GaussianMixture(
            n_components=self.k,
            covariance_type=self.covariance_type,
            n_init=self.n_init,
            reg_covar=self.reg_covar,
            max_iter=self.max_iter,
            random_state=self.seed,
        )
        raw_labels = gmm.fit_predict(x_fit)
        labels_fit, remap = renumber_by_size(raw_labels, self.k)

        # Tính centroids theo nhãn đã renumber
        centroids = np.array([x_fit[labels_fit == c].mean(axis=0) for c in range(self.k)])

        self.model = gmm
        self.remap = remap
        self.centroids = centroids
        self.cluster_order = compute_cluster_order(raw_fit, labels_fit, features, self.k)
        return labels_fit

    def assign_late(self, x_late: np.ndarray) -> np.ndarray:
        if self.model is None or self.remap is None:
            raise ValueError("Mô hình chưa được fit.")
        raw_preds = self.model.predict(x_late)
        return self.remap[raw_preds]

