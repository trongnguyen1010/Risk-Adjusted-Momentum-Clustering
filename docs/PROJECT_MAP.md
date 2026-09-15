# Bản đồ repository

Đây là migration map canonical được tạo từ audit R0. “Có” nghĩa là foundation đã chạy; “khung” nghĩa là interface đã có nhưng methodology/source semantics chưa được duyệt.

| Component | Directory/file | Milestone | Trạng thái | Dependency chính |
|---|---|---|---|---|
| IO + executable contracts | `src/delta_t1/io.py`, `contracts.py`, `schemas/` | M1 | Có, giữ nguyên behavior | JSON schema, immutable write policy |
| Source acquisition | `ingestion/crawler.py`, `planning.py`, `recovery.py`, `calendar.py` | M1 | Có | source rights/semantics, HTTP policy |
| Source adapters | `ingestion/sources/` | M1 | Vnstock migrated; CafeF/VietFin là incomplete interface | endpoint semantics và rights approval |
| Normalization | `ingestion/normalization/` | M1 | Generic architecture | source candidates, identity/unit/basis rules |
| Reconciliation | `ingestion/reconciliation/` | M1 | Generic deterministic rules + conflict records | normalized candidates, approved priority rules |
| Quality + promotion | `ingestion/quality.py`, compatibility promotion path | M1 | Có; legacy Vnstock path được giữ qua adapter | canonical schema và reconciliation |
| Feature registry | `features/registry.py` | M1/M2 | Metadata-driven; chặn non-cluster feature | approved feature definitions/citations |
| Market features | `features/market.py` | M1/M2 | Có từ baseline | canonical price/calendar/benchmark |
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
| Experiment runner | `experiments/runner.py` | M2/M3 | Orchestrates immutable run | complete data run + protocol |
| Artifact/reporting | `experiments/artifacts.py`, `reporting.py` | M2/M3 | Version/hash/export responsibility | runner outputs |
| Product projection/API | `product/`, `web/` | Product/M3 | Có, phải giữ hoạt động | complete versioned experiment bundle |
| CLI/scripts | `cli.py`, `run.py`, `scripts/` | Cross-cutting | Có; import path được migrate | package APIs/configs |
| Config | `configs/data|features|experiments|product/` | Cross-cutting | Reorganized examples | registries + protocol schemas |
| Tests | `tests/unit|integration|regression|fixtures/` | Cross-cutting | Assertion cũ được migrate | all layers |
| Immutable evidence | `data/`, `artifacts/` | Evidence | Không mutate trong refactor | hashes/manifests/provenance |

## Dependency flow

`sources → normalization → reconciliation → canonical/QC → features → clustering → evaluation/backtest → experiment artifacts → product bundle/API/web`.

Dependency chỉ đi theo chiều này. Product không gọi ngược vào feature/model; portfolio metrics không quay lại chọn clustering.
