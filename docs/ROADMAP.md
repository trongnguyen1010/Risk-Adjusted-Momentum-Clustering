# Roadmap DELTA

## M1 — Data Foundation

Mục tiêu là canonical data có historical identity, price basis, point-in-time availability và multi-source provenance.

- [x] Immutable ingestion, schema validation, QC, recovery và synthetic regression foundation.
- [x] Ba năm usable observed history và `REFERENCE_ONLY` policy.
- [ ] **SOURCE_SMOKE:** 3–5 securities thật, HOSE/HNX/UPCOM và edge case khi có thể; request >=5 năm nếu source hỗ trợ; review endpoint, field/unit/timezone/basis, pagination/rate/rights, corporate action và quarterly reports. PASS chỉ mở representative pilot, không mở scale.
- [ ] **REPRESENTATIVE_PILOT:** 50–60 securities, >=5 năm, representative exchange/sector; historical identity, multi-source field-level reconciliation, PIT financial và QC/coverage evidence. Chỉ PASS gate này mở scale planning.
- [ ] **M1_SCALE:** >=300 securities, >=5 năm; chưa chạy.
- [ ] **EXTENDED_SCALE:** historical eligible universe, 5–15 năm, có thể >1.200 securities; không có cap 350 và chưa chạy.
- [ ] Chốt financial taxonomy, publication/revision rules và paper-backed financial feature.
- [ ] Xuất EDA, coverage và data-quality report.

## M2 — Clustering Research

- [x] Static K-Means deterministic baseline và label alignment/transition tracking.
- [x] Tách cluster quality khỏi temporal/portfolio metrics ở architecture.
- [ ] Freeze feature registry và development/validation protocol; active snapshot 1.4 không chứa Sharpe.
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

Mỗi phase phải chạy tests, compile/static checks, JSON parse, broken link/import check và ghi changed files. Regression chưa giải thích thì dừng. Không mở rộng auth, news/sentiment, watchlist, alert, microservice hoặc database migration trong refactor này.
