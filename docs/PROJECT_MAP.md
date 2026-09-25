# Bản đồ repository

## Active CafeF path — C5 → C6 → C7 → C8

| Bước | Evidence / entry point | Trạng thái |
|---|---|---|
| C5 current evidence | `artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2/` | 500 current; 490 `market_feature_ready_v2`; 10 mã gắn `DEFERRED_MISSING_SESSION_REVIEW` |
| C6-R2 frozen expansion | `configs/data/cafef_expansion_v1/` | 600 selected pre-crawl, reserve 100, 5 assignment disjoint; `BASE_2020`, range 2020-01-01 → 2026-09-23 |
| Worker acquisition | `scripts/run_cafef_expansion_worker.py` | Acquisition-only; external exact-commit guard; immutable raw; dry-run/execute/exact resume |
| One-ZIP handoff | `scripts/package_cafef_expansion_handoff.py` | Một portable ZIP/worker, internal checksums |
| Central verification | `scripts/verify_cafef_expansion_handoffs.py` | Verify năm shard; chưa merge/normalize |
| C7 partial consolidation | `artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1/` | Offline inventory 600 mã từ năm ZIP bất biến; 452 COMPLETE được giữ nguyên |
| Supplemental acquisition | `configs/data/cafef_supplemental_v1/`, `scripts/run_cafef_supplemental_worker.py` | 141 mã runnable chia ba shard mới; 7 FAILED giữ `MANUAL_REVIEW`; raw ghi namespace mới |
| Worker instructions | `docs/crawl/CAFEF_EXPANSION_5_WORKERS.md` | PowerShell runbook active |
| C8 audit tương lai | contract ở cuối worker runbook | Full-history và latest-253 audit độc lập; chưa execute |

> **HISTORICAL / DO NOT USE FOR CAFEF EXPANSION V1:** các planner/runners C1,
> M1-scale/KBS và worker docs dưới `docs/crawl/m1_scale/` chỉ được giữ để tái lập
> C1–C5. Worker expansion v1 chỉ dùng các entry points trong bảng trên.

Đây là migration map canonical được tạo từ audit R0. “Có” nghĩa là foundation đã chạy; “khung” nghĩa là interface đã có nhưng methodology/source semantics chưa được duyệt.

| Component | Directory/file | Milestone | Trạng thái | Dependency chính |
|---|---|---|---|---|
| IO + executable contracts | `src/delta_t1/io.py`, `contracts.py`, `schemas/` | M1 | Có; market contract 1.4, feature snapshot 1.5; `shares_history` là optional input cho compatibility | JSON schema, immutable write policy |
| Source acquisition + gates | `ingestion/representative_pilot.py`, `planning.py`, source runners | M1 | `SOURCE_SMOKE` và real 55-symbol pilot PASS; M1 scale chỉ unlock cho planning, chưa chạy | versioned scale universe/config và approved execution |
| Source adapters | `ingestion/sources/` | M1 | Official pilot: KBS direct HTTP + CafeF direct; Vnstock SDK chỉ legacy/reference | accepted-risk research use; production rights chưa verified |
| Normalization | `ingestion/normalization/` | M1 | Generic architecture | source candidates, identity/unit/basis rules |
| Reconciliation | `ingestion/reconciliation/` | M1 | Field-level decisions; tách match/missing/value/unit/basis/timing/identity conflict | semantic comparison key, normalized candidates, approved priority rules |
| Quality + promotion | `ingestion/quality.py`, compatibility promotion path | M1 | Có; legacy Vnstock path được giữ qua adapter | canonical schema và reconciliation |
| Feature registry | `features/registry.py` | M1/M2 | Metadata-driven; active registry không chứa Sharpe | approved feature definitions/citations |
| Market features | `features/market.py` | M1/M2 | Snapshot 1.4 không sinh Sharpe | canonical price/calendar/benchmark |
| Financial/PIT features | `features/fundamentals.py`, `point_in_time.py` | M1/M2 | Khung an toàn; feature cụ thể chờ approval | financial taxonomy + availability rules |
| Preprocessing | `features/preprocessing.py` | M2 | Snapshot-only foundation | development protocol, registry eligibility |
| Clustering registry | `clustering/base.py`, `registry.py` | M2 | Common interface | algorithm config, preprocessing output |
| K-Means baseline | `clustering/kmeans.py` | M2 | Có, deterministic | common interface + cluster metrics |
| PCA/K-Means | `features/preprocessing.py`, experiment config | M2 | Snapshot-only implementation có loadings/explained variance; real comparison chưa chạy | approved experiment protocol/data |
| Hierarchical/DBSCAN/GMM | `clustering/hierarchical.py`, `dbscan.py`, `gmm.py` | M2 | Ward deterministic đã có; DBSCAN/GMM fail closed chờ methodology/dependency | comparator protocol approval |
| Dynamic clustering | `clustering/dynamic/base.py` | M2 | Chỉ interface, không concrete algorithm | `research/DYNAMIC_CLUSTERING_REVIEW.md` approval |
| Cluster evaluation | `evaluation/cluster_metrics.py` | M2 | Tách khỏi model | assignments/vectors |
| Temporal evaluation | `evaluation/temporal_metrics.py` | M2 | Có từ stability baseline | consecutive snapshots/shared identities |
| Portfolio evaluation | `evaluation/portfolio_metrics.py` | M3 | Có từ performance baseline | realized returns/backtest; không vào clustering |
| Backtest | `backtest/portfolio.py`, `returns_engine.py` | M3 | Có return-space simulator | frozen signals, next-session execution, costs |
| Experiment protocol | `experiments/protocol.py` | M2/M3 | Tách khỏi runner, multi-algorithm-aware | feature/model registry, holdout rules |
| Experiment runner | `experiments/runner.py` | M2/M3 | M2 mặc định tắt portfolio; M3 phải bật rõ `portfolio_evaluation.enabled` | complete data run + protocol |
| Artifact/reporting | `experiments/artifacts.py`, `reporting.py` | M2/M3 | Version/hash/export responsibility | runner outputs |
| Artifact IDs | `artifact_ids.py` | Cross-cutting | Future IDs dùng UTC timestamp + 8 lowercase hex; old IDs vẫn hợp lệ | immutable manifests + local active index |
| Product projection/API | `product/`, `web/` | Product/M3 | Có, phải giữ hoạt động | complete versioned experiment bundle |
| CLI/scripts | `cli.py`, `run.py`, `scripts/` | Cross-cutting | `run_representative_pilot.py` là active M1 pilot; `crawl_vnstock.py` là legacy SDK experiment | package APIs/configs, PASS source gate |
| Config | `configs/data|features|experiments|product/` | Cross-cutting | Reorganized examples | registries + protocol schemas |
| Human collection guide | `docs/crawl/README.md` | M1 | START HERE cho workflow manual/multi-person; chưa thay source approval | assignment, rights review, raw hashes |
| Tests | `tests/unit|integration|regression|fixtures/` | Cross-cutting | Assertion cũ được migrate | all layers |
| Immutable evidence | `data/`, `artifacts/` | Evidence | `data/` local/gitignored; active evidence không rename, technical output chỉ archive có manifest | hashes/manifests/provenance, `data/ACTIVE_INDEX.json` |

## Dependency flow

`sources → normalization → reconciliation → canonical/QC → features → clustering → evaluation/backtest → experiment artifacts → product bundle/API/web`.

Dependency chỉ đi theo chiều này. Product không gọi ngược vào feature/model; portfolio metrics không quay lại chọn clustering.

M1 canonical/core target gồm `securities`, `shares_history`, `prices_daily`, `corporate_actions`, `trading_calendar`, `benchmark_daily`, `financial_reports` và `financial_facts`. `risk_free_rate` vẫn là optional support data; legacy Vnstock promotion không sở hữu domain `shares_history` mới.
