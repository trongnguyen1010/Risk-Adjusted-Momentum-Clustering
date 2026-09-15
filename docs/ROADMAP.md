# Roadmap DELTA

## M1 — Data Foundation

Mục tiêu là canonical data có historical identity, price basis, point-in-time availability và multi-source provenance.

- [x] Immutable ingestion, schema validation, QC, recovery và synthetic regression foundation.
- [x] Ba năm usable observed history và `REFERENCE_ONLY` policy.
- [ ] Xác minh endpoint semantics, rate/rights cho CafeF, VietFin và Vnstock.
- [ ] Smoke 3–5 symbols đại diện HOSE/HNX/UPCOM và edge cases.
- [ ] Representative pilot 50–60 symbols, >=5 năm.
- [ ] Sau khi pilot pass, scale >=300; long-term target có thể >1.200 và 5–15 năm.
- [ ] Chốt financial taxonomy, publication/revision rules và paper-backed financial feature.
- [ ] Xuất EDA, coverage và data-quality report.

## M2 — Clustering Research

- [x] Static K-Means deterministic baseline và label alignment/transition tracking.
- [x] Tách cluster quality khỏi temporal/portfolio metrics ở architecture.
- [ ] Freeze feature registry và development/validation protocol.
- [x] Có implementation PCA + K-Means snapshot-only, lưu scaler/PCA parameters và explained variance; chưa có real comparison evidence.
- [x] Có Ward/Agglomerative comparator deterministic; DBSCAN/GMM chờ protocol. Chưa có real comparator evidence.
- [ ] Đánh giá cluster quality: Silhouette, Davies-Bouldin, Calinski-Harabasz, inertia, balance.
- [ ] Đánh giá temporal stability: ARI, NMI, persistence, transition, migration rate, centroid drift.
- [ ] Chỉ triển khai Dynamic Clustering sau explicit approval trong review tương ứng.

## M3 — Backtest + Product

- [ ] Freeze methodology trước final backtest và dùng holdout đúng protocol.
- [ ] So sánh cluster strategy với VNINDEX, equal-weight universe và momentum-only.
- [x] Transaction cost, turnover và return-space portfolio foundation.
- [ ] Báo cáo CAGR, volatility, Sharpe, Sortino, MDD, Calmar, alpha/beta, information ratio theo availability.
- [x] Immutable product bundle, read API và dashboard foundation.
- [ ] Thesis dashboard hoàn chỉnh cho cluster, transitions, feature explanation, PCA/UMAP, quality/provenance.

## Gates chung

Mỗi phase phải chạy tests, compile/static checks, JSON parse, broken link/import check và ghi changed files. Regression chưa giải thích thì dừng. Không mở rộng auth, news/sentiment, watchlist, alert, microservice hoặc database migration trong refactor này.
