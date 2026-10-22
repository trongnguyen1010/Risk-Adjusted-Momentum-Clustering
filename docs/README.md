# Documentation — START HERE

Repository đang ở trạng thái **C8 executed and verified; R1 consolidated; M1-REPORT complete**. M1 market foundation đủ cho market-only experiment preparation, còn strict research gate vẫn `NOT READY`. Bắt đầu bằng:

1. [Current status](CURRENT_STATUS.md) — số liệu, gate, lineage và stage tiếp theo.
2. [Project map](PROJECT_MAP.md) — đường dẫn active và ownership.
3. [Architecture](ARCHITECTURE.md) và [Data contract](DATA_CONTRACT.md).
4. [Methodology](METHODOLOGY.md), [Feature system](FEATURE_SYSTEM.md) và [Experiment protocol](research/EXPERIMENT_PROTOCOL.md).
5. [Reproducibility](REPRODUCIBILITY.md) — kiểm chứng offline bằng manifest/hash.
6. [M1 report artifact](../artifacts/reports/m1-market-foundation-v1/report.json) và [inspection notebook](../notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb).

M2 Nhiệm vụ 1 đã freeze protocol và Nhiệm vụ 2 đã hoàn tất runner preparation/testing. Stage chính xác tiếp theo là **M2 Nhiệm vụ 3 — GLOBAL K TRÊN DEVELOPMENT**; chưa chạy trong stage hiện tại. Eligibility vẫn theo từng snapshot; 905 chỉ là latest-snapshot count và không phải strict research universe.

**Cập nhật 2026-10-22:** Dữ liệu C8 đã được thay bằng gói mới; các kết quả
M2 trước đây là lịch sử. PCA V2 và Nhiệm vụ 11 đã được gỡ;
Task 10/12/13 giữ lại chưa được tái xác nhận trên dữ liệu hiện tại.

## Theo mục đích

- **PCA + K-Means V2 và Nhiệm vụ 11 đã được gỡ theo yêu cầu người dùng.**
  Không còn notebook 06–09 PCA V2, config/model/artifacts/báo cáo của nhánh này.
  Nhiệm vụ 11 V1/V2 cũng đã xóa notebook, runner, config, model và đầu ra.
  Bộ dữ liệu C8 mới, backend phân cụm dùng chung và kết quả K-Means/Ward giữ nguyên.
  Không có workflow PCA V2/Task 11 để chạy trong checkout hiện tại; xem
  [Current status](CURRENT_STATUS.md) để biết phạm vi và các phần phụ thuộc.
- Thu thập CafeF có kiểm soát: [Data collection](crawl/README.md) và [CafeF semantics](crawl/sources/CAFEF.md).
- Quyết định methodology: [Decisions](DECISIONS.md), [Research questions](research/RESEARCH_QUESTIONS.md), [Literature matrix](research/LITERATURE_MATRIX.md), [Dynamic clustering review](research/DYNAMIC_CLUSTERING_REVIEW.md).
- Evaluation/product: [Evaluation and backtest](EVALUATION_AND_BACKTEST.md), [Product](PRODUCT.md).
- Governance: [Roadmap](ROADMAP.md), [Reproducibility](REPRODUCIBILITY.md), [Contributing](../CONTRIBUTING.md).
- Historical source caveat còn được artifact tham chiếu: [KBS pilot semantics](data/kbs_pilot_semantics.md) và [data usage risk acceptance](data/DATA_USAGE_RISK_ACCEPTANCE.md).

Các plan, handoff và audit superseded đã được loại khỏi active tree trong R1; Git history là archive duy nhất của chúng.
