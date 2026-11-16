"""
delta_t1.experiments.assessment.peers

Tạo nhóm so sánh cùng ngành/cùng đặc tính (Peers) theo từng đặc trưng (Stage S1: Task R1-15).
Quy tắc:
  - Ưu tiên Peers cùng cả Cụm A (Thị trường) và Cụm B (Tài chính).
  - Nếu số lượng < 3:
      + Đặc trưng tài chính: mở rộng lấy các mã cùng Cụm B.
      + Đặc trưng thị trường: mở rộng lấy các mã cùng Cụm A.
  - Loại trừ chính mình (self-exclusion).
  - Yêu cầu tối thiểu 3 Peers hợp lệ cho từng chỉ số để tính Median và IQR (p25, p75).
  - Dưới 3 Peers: median = None, iqr = None, không tự tạo số giả.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from .inputs import FINANCIAL_FEATURES, MARKET_FEATURES, AssessmentInputRecord

@dataclass
class MetricPeerStats:
    metric: str
    peer_basis: str  # "SAME_A_AND_B", "SAME_B_ONLY", "SAME_A_ONLY", "NONE"
    peer_count: int
    median: Optional[float]
    p25: Optional[float]
    p75: Optional[float]
    peer_tickers: List[str]

class PeerBenchmarkBuilder:
    """Xây dựng dữ liệu benchmark từ nhóm Peers cho một cổ phiếu."""
    def __init__(self, all_records: Dict[str, AssessmentInputRecord]):
        self.records = all_records

    def build_peer_stats_for_ticker(self, target_ticker: str) -> Dict[str, MetricPeerStats]:
        target = self.records.get(target_ticker)
        if not target or not target.is_eligible:
            return {}

        c_a = target.cluster_a
        c_b = target.cluster_b

        # 1. Nhóm cùng cả A và B (trừ chính target_ticker)
        pool_both = [
            r for t, r in self.records.items()
            if t != target_ticker and r.is_eligible and r.cluster_a == c_a and r.cluster_b == c_b
        ]

        # 2. Nhóm cùng B (tài chính)
        pool_b_only = [
            r for t, r in self.records.items()
            if t != target_ticker and r.is_eligible and r.cluster_b == c_b
        ]

        # 3. Nhóm cùng A (thị trường)
        pool_a_only = [
            r for t, r in self.records.items()
            if t != target_ticker and r.is_eligible and r.cluster_a == c_a
        ]

        stats_by_metric: Dict[str, MetricPeerStats] = {}

        # Xử lý 9 đặc trưng tài chính
        for m in FINANCIAL_FEATURES:
            # Ưu tiên pool_both
            vals_both = [(r.ticker, r.financial_features.get(m)) for r in pool_both if r.financial_features.get(m) is not None]
            if len(vals_both) >= 3:
                vals = [v for _, v in vals_both]
                stats_by_metric[m] = MetricPeerStats(
                    metric=m,
                    peer_basis="SAME_A_AND_B",
                    peer_count=len(vals),
                    median=float(np.median(vals)),
                    p25=float(np.percentile(vals, 25)),
                    p75=float(np.percentile(vals, 75)),
                    peer_tickers=[t for t, _ in vals_both],
                )
            else:
                # Mở rộng pool_b_only
                vals_b = [(r.ticker, r.financial_features.get(m)) for r in pool_b_only if r.financial_features.get(m) is not None]
                if len(vals_b) >= 3:
                    vals = [v for _, v in vals_b]
                    stats_by_metric[m] = MetricPeerStats(
                        metric=m,
                        peer_basis="SAME_B_ONLY",
                        peer_count=len(vals),
                        median=float(np.median(vals)),
                        p25=float(np.percentile(vals, 25)),
                        p75=float(np.percentile(vals, 75)),
                        peer_tickers=[t for t, _ in vals_b],
                    )
                else:
                    # Dưới 3 peers -> không tính median
                    stats_by_metric[m] = MetricPeerStats(
                        metric=m,
                        peer_basis="NONE",
                        peer_count=len(vals_b),
                        median=None,
                        p25=None,
                        p75=None,
                        peer_tickers=[t for t, _ in vals_b],
                    )

        # Xử lý 9 đặc trưng thị trường
        for m in MARKET_FEATURES:
            vals_both = [(r.ticker, r.market_features.get(m)) for r in pool_both if r.market_features.get(m) is not None]
            if len(vals_both) >= 3:
                vals = [v for _, v in vals_both]
                stats_by_metric[m] = MetricPeerStats(
                    metric=m,
                    peer_basis="SAME_A_AND_B",
                    peer_count=len(vals),
                    median=float(np.median(vals)),
                    p25=float(np.percentile(vals, 25)),
                    p75=float(np.percentile(vals, 75)),
                    peer_tickers=[t for t, _ in vals_both],
                )
            else:
                # Mở rộng pool_a_only
                vals_a = [(r.ticker, r.market_features.get(m)) for r in pool_a_only if r.market_features.get(m) is not None]
                if len(vals_a) >= 3:
                    vals = [v for _, v in vals_a]
                    stats_by_metric[m] = MetricPeerStats(
                        metric=m,
                        peer_basis="SAME_A_ONLY",
                        peer_count=len(vals),
                        median=float(np.median(vals)),
                        p25=float(np.percentile(vals, 25)),
                        p75=float(np.percentile(vals, 75)),
                        peer_tickers=[t for t, _ in vals_a],
                    )
                else:
                    stats_by_metric[m] = MetricPeerStats(
                        metric=m,
                        peer_basis="NONE",
                        peer_count=len(vals_a),
                        median=None,
                        p25=None,
                        p75=None,
                        peer_tickers=[t for t, _ in vals_a],
                    )

        return stats_by_metric
