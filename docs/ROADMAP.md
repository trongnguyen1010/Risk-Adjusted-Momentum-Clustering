# Roadmap DELTA

## M1 — Data Foundation

Mục tiêu là canonical data có historical identity, price basis, point-in-time availability và multi-source provenance.

- [x] Immutable ingestion, schema validation, QC, recovery và synthetic regression foundation.
- [x] Ba năm usable observed history và `REFERENCE_ONLY` policy.
- [x] **SOURCE_SMOKE:** canonical run `source-smoke-20260916T122331Z-79427ec6` PASS; chỉ mở representative pilot, không mở scale.
- [x] **REPRESENTATIVE_PILOT:** real run `representative-pilot-20260916T185530Z-410ffcba`, 55/55 securities usable >=5 năm; exact-hash QC replay PASS. Canonical pilot `canonical-pilot-20260917T062832Z-6748ac02` có 55/55 latest market snapshots eligible dưới `PILOT_OBSERVED_INTERVAL_ONLY`; financial PIT vẫn khóa feature.
- [ ] **M1_SCALE:** acquisition 5 shard/500 mã, central mapping và EDA/QC đã chạy; 500/500 mã có observed calendar span >=3 năm, 484/500 có span >=5 năm. Collection coverage >=300 đã đạt và không bị đồng nhất với số row đủ 252-session feature tại một ngày. Latest completed-month market-feature readiness, historical identity readiness và strict research readiness được báo độc lập; identity provisional, financial PIT và research sample-size/density policy chưa duyệt nên M1 vẫn `PARTIAL`/research gate `FAIL`.
- [ ] **EXTENDED_SCALE:** historical eligible universe, 5–15 năm, có thể >1.200 securities; không có cap 350 và chưa chạy.
- [ ] Chốt financial taxonomy, publication/revision rules và paper-backed financial feature.
- [ ] Chốt source mapping/version cho market và share counts sau real source evidence; không backfill current share count về lịch sử.
- [x] Xuất offline EDA/coverage/data-quality artifact cho M1 scale; report legacy `m1-scale-quality-20260918T130735Z-54038c13` được giữ immutable. Report mới dùng thuật ngữ observed span, session-density evidence, latest completed month và readiness tách biệt.

## M2 — Clustering Research

- [x] Static K-Means deterministic baseline và label alignment/transition tracking.
- [x] Tách cluster quality khỏi temporal/portfolio metrics ở architecture.
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

Mỗi phase phải chạy tests, compile/static checks, JSON parse, broken link/import check và ghi changed files. Regression chưa giải thích thì dừng. Không mở rộng auth, news/sentiment, watchlist, alert, microservice hoặc database migration trong refactor này.
