# Roadmap DELTA

## M1 — Market Data Foundation

M1 market foundation đã hoàn tất cho **market-only experiment preparation**; strict research gate vẫn `NOT READY`.

- [x] C5 baseline 500 securities được giữ trong lineage bất biến.
- [x] CafeF-primary migration/validation chấp nhận `TradeHistoryNew` và `AdjustPrice × 1000` như `vendor_adjusted` proxy với giới hạn được ghi rõ.
- [x] C6 freeze/acquisition contract và five-shard expansion foundation.
- [x] C7 thu được 452 complete expansion securities; 148 còn `DEFERRED_EXPANSION_ACQUISITION`.
- [x] C8 complete-only chạy trên 952 candidates tại snapshot `2026-08-28`.
- [x] C8-VERIFY xác minh offline hashes và lineage, không rebuild feature.
- [x] R1 hợp nhất active repository mà không thay dữ liệu, methodology hoặc kết quả.
- [x] M1-REPORT tạo artifact `artifacts/reports/m1-market-foundation-v1/` và notebook inspection.

Kết quả khóa: 922 `feature_complete`, 905 `market_feature_ready_v2`, 47 market-readiness failures, 30 latest-253 incomplete, 0 `historical_identity_ready` và 0 `research_ready`. 905 chỉ là latest-snapshot count, không phải final historical universe.

Supplemental acquisition cho 148 deferred rows là optional future stage, không phải điều kiện để bắt đầu M2-PREP. Financial taxonomy/PIT, historical identity authority và final research sample-size/density vẫn là workstream riêng, fail-closed.

## M2 — Clustering Research

- [x] Static K-Means deterministic baseline và label alignment/transition tracking.
- [x] Tách cluster quality khỏi temporal/portfolio metrics ở architecture.
- [ ] **M2-PREP — exact next stage:** freeze `market_experiment_eligible(t)`, development/validation windows, treatment of readiness discontinuities, preprocessing/PCA, comparator set, `k` policy và evaluation contract. Không chạy clustering trong stage preparation này.
- [ ] Freeze feature registry và development/validation protocol; active snapshot 1.5 không chứa Sharpe và tách readiness, còn formula market giữ nguyên baseline 1.4.
- [x] Có implementation PCA + K-Means snapshot-only, lưu scaler/PCA parameters và explained variance; chưa có real comparison evidence.
- [x] Có Ward/Agglomerative comparator deterministic; DBSCAN/GMM chờ protocol. Chưa có real comparator evidence.
- [ ] Đánh giá cluster quality: Silhouette, Davies-Bouldin, Calinski-Harabasz, inertia, balance.
- [ ] Đánh giá temporal stability: ARI, NMI, persistence, transition, migration rate, centroid drift.
- [ ] Chỉ triển khai Dynamic Clustering sau explicit approval trong review tương ứng.
- [ ] Thiết kế variable-cluster/noise-label interface trước khi cân nhắc DBSCAN; không ép DBSCAN vào fixed-`k` abstraction.

## M3 — Backtest + Product

- [ ] Freeze methodology trước final backtest và dùng holdout đúng protocol; chỉ M3/frozen config bật `portfolio_evaluation.enabled=true`.
- [ ] So sánh cluster strategy với VNINDEX, equal-weight universe và momentum-only.
- [x] Transaction cost, turnover và return-space portfolio foundation.
- [ ] Báo cáo CAGR, volatility, Sharpe, Sortino, MDD, Calmar, alpha/beta, information ratio theo availability.
- [x] Immutable product bundle, read API và dashboard foundation.
- [ ] Thesis dashboard hoàn chỉnh cho cluster, transitions, feature explanation, PCA/UMAP, quality/provenance.

## Gates chung

Mỗi phase phải chạy tests, compile/static checks, JSON parse, broken link/import check và ghi changed files. Regression chưa giải thích thì dừng. M2-PREP không được promote identity/research readiness, không chạy clustering/backtest và không chọn model bằng portfolio return. Không mở rộng auth, news/sentiment, watchlist, alert, microservice hoặc database migration trong active stage.
