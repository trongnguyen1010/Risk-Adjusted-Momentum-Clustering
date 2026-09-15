# Evaluation và backtest

## Ba lớp metric độc lập

| Lớp | Metric | Không được dùng để |
|---|---|---|
| Cluster quality | Silhouette, Davies-Bouldin, Calinski-Harabasz, inertia, size/balance | suy ra portfolio performance |
| Temporal stability | ARI, NMI, persistence, transition matrix, migration rate, centroid drift | gọi static rerun là Dynamic Clustering |
| Portfolio performance | CAGR, volatility, Sharpe, Sortino, MDD, Calmar, alpha/beta, information ratio, turnover/cost | chọn `k` hoặc chứng minh cluster quality |

Metric implementation nằm trong ba module riêng. Model không duplicate metric logic.

## Backtest protocol

Methodology, feature set, `k`/algorithm, development/validation/holdout, purging/embargo và portfolio rule phải freeze trước final backtest. Tín hiệu chỉ khớp từ eligible session sau `decision_at`; realized data sau evaluation boundary không được dùng để fit.

So sánh bắt buộc gồm cluster strategy, VNINDEX, equal-weight universe và momentum-only. Engine ghi gross/net return, transaction cost, turnover, cash và benchmark riêng. Current foundation là fractional return-space simulation, chưa phải share/lot/settlement ledger.

Không làm biến mất holding khi price thiếu; execution phải block/ghi reason theo contract. Return basis phải rõ raw/adjusted/total return và tránh cộng dividend hai lần.

## Báo cáo

Cluster report và portfolio report tách bảng/section. Kết quả bất lợi vẫn là evidence và không được xóa nếu artifact hoàn chỉnh. Synthetic/legacy pilot phải có nhãn giới hạn rõ ràng và không được dùng làm investment claim.
