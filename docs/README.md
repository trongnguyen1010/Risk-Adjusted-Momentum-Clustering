# Documentation — START HERE

**M3-B Market-only (2026-10-23):** dashboard Streamlit tại
[`m3_dashboard.py`](../m3_dashboard.py), đọc bộ handoff hiện hành 84 snapshot
2019–2025 trên dữ liệu nền 2016–2025. Hướng dẫn Windows, checklist và ví dụ đối
chiếu source ở đầu [Current status](CURRENT_STATUS.md). Giao diện chỉ còn Overview
và bảng thành viên tìm kiếm/phân trang, trục cố định liquidity_21/beta_126;
không Financial, ranking hoặc backtest. Các mốc cũ bên dưới giữ bối cảnh
lịch sử, không phải next stage của phiên M3-B này.

## Chạy dashboard sau khi pull Git và nhận dữ liệu riêng

Yêu cầu Python >=3.11 (môi trường đã kiểm tra: Python 3.12). Người chia sẻ cần
commit `m3_dashboard.py`, `.streamlit/config.toml`, `pyproject.toml`,
`.gitattributes`, tests/docs và bộ `M2/artifacts/m2-final-handoff-v1/` hiện hành.
Hai manifest development/holdout dưới `M2/artifacts/` đã nằm trong Git. Không
commit `.venv/` hoặc bỏ ignore của toàn bộ `artifacts/`.

Người nhận đặt **đúng ba file của bộ C8 hiện hành** do owner gửi riêng vào:

```text
<repository>/artifacts/cafef_primary/cafef-c8-complete-only-v2/
├── manifest.json
└── canonical/
    ├── feature_snapshots.jsonl
    └── securities.jsonl
```

Giữ nguyên bytes, không mở rồi lưu lại CSV/JSONL bằng Excel/editor. Không dùng
bộ C8 cũ đến 28/08/2026 hoặc chỉ đổi tên thư mục để thay thế. Dashboard kiểm
tra checksum và lineage với handoff/development/holdout hiện hành; dữ liệu thiếu
hoặc sai phiên bản sẽ bị chặn. Không cần chạy lại crawl, features hoặc model.

Từ thư mục gốc repository, chạy PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dashboard]"
.\.venv\Scripts\python.exe -m streamlit run .\m3_dashboard.py
```

Mở `http://localhost:8501`. Những lần sau chỉ chạy lệnh cuối; Ctrl+C để dừng.
Extra `dashboard` pin Streamlit 1.66.1 và pandas 2.3.3, tương ứng API/table
Styler đang dùng. Không cần cài extra `research` để xem dashboard.

Kiểm tra offline bộ dữ liệu trước khi mở giao diện:

```powershell
.\.venv\Scripts\python.exe -c "from m3_dashboard import load_market_data; d = load_market_data(); print(d['audit'])"
```

Kỳ vọng audit `status=PASS`, 84 snapshot/75.801 assignments và không thiếu
feature rows/values. Git handoff dùng `-text` để tránh tự chuyển đổi xuống dòng
làm sai checksum khi clone trên Windows/Linux. Hướng dẫn này chưa thay thế một
lần thử clone/install trên máy người nhận.

Repository đang ở trạng thái **C8 executed and verified; R1 consolidated; M1-REPORT complete**. M1 market foundation đủ cho market-only experiment preparation, còn strict research gate vẫn `NOT READY`. Bắt đầu bằng:

1. [Current status](CURRENT_STATUS.md) — số liệu, gate, lineage và stage tiếp theo.
2. [Project map](PROJECT_MAP.md) — đường dẫn active và ownership.
3. [Architecture](ARCHITECTURE.md) và [Data contract](DATA_CONTRACT.md).
4. [Methodology](METHODOLOGY.md), [Feature system](FEATURE_SYSTEM.md) và [Experiment protocol](research/EXPERIMENT_PROTOCOL.md).
5. [Reproducibility](REPRODUCIBILITY.md) — kiểm chứng offline bằng manifest/hash.
6. [M1 report artifact](../artifacts/reports/m1-market-foundation-v1/report.json) và [inspection notebook](../notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb).

M2 Nhiệm vụ 1 đã freeze protocol và Nhiệm vụ 2 đã hoàn tất runner preparation/testing. Stage chính xác tiếp theo là **M2 Nhiệm vụ 3 — GLOBAL K TRÊN DEVELOPMENT**; chưa chạy trong stage hiện tại. Eligibility vẫn theo từng snapshot; 905 chỉ là latest-snapshot count và không phải strict research universe.

## Theo mục đích

- **PCA + K-Means nhiệm vụ 6–9:** dùng bộ kết quả đã khôi phục từ Git, nay đổi
  về tên chuẩn không có hậu tố phiên bản. Tất cả đều complete trên 60 tháng
  development 2019–2023, 45.646 assignments; kết quả số và trọng số giữ nguyên.
  Notebook:
  [06](../M2/notebooks/06_pca_kmeans.ipynb),
  [07](../M2/notebooks/07_cluster_quality_evaluation_pca_kmeans.ipynb),
  [08](../M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb),
  [09](../M2/notebooks/09_temporal_stability_pca_kmeans.ipynb).
  Báo cáo:
  [NV6](../M2/reports/Bao_cao_M2_Nhiem_vu_6_PCA_KMeans.md),
  [NV7](../M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_PCA_KMeans.md),
  [NV8](../M2/reports/Bao_cao_M2_Nhiem_vu_8_Ho_so_cum_PCA_KMeans.md),
  [NV9](../M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_PCA_KMeans.md).
  Kết quả tại `M2/artifacts/m2-task6-pca-kmeans/` và
  `M2/artifacts/m2-evaluation-pca-kmeans/`, models tại `M2/models/pca_kmeans/`.
- **Nhiệm vụ 11 đã hoàn tất trên nguồn C8 mới:** mở
  [11_final_holdout_execution.ipynb](../M2/notebooks/11_final_holdout_execution.ipynb),
  dùng kernel Python >=3.11 đã chạy M2. Kết quả complete: 24/24 tháng holdout
  2024–2025, không skip, 30.155 assignments, 24 model và 23 cặp thời gian;
  duy nhất KMeans Baseline/sklearn/K=2. Median Silhouette 0,949324,
  delta so với development +0,008487; vẫn giữ cảnh báo lệch kích thước cụm.
  Config [m2_final_holdout.json](../configs/experiments/m2_final_holdout.json) khóa
  chín đầu vào development hiện tại, 60 model; seed=42, n_init=10, max_iter=300,
  Robust Scaling độc lập từng tháng, threshold 100, không quét K hoặc comparator.
  Kết quả tại `M2/artifacts/m2-final-holdout/`, models `M2/models/holdout/`;
  [báo cáo đầy đủ](../M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md)
  giữ bố cục A/B/C của mẫu cũ và dùng số liệu mới.
  Lần chạy lại chỉ verify/nạp bộ complete; run dở/failed hoặc input đổi phải dừng.
  Task 12/13 lịch sử chưa áp dụng cho workflow hiện tại, thực hiện riêng.
- Thu thập CafeF có kiểm soát: [Data collection](crawl/README.md) và [CafeF semantics](crawl/sources/CAFEF.md).
- Quyết định methodology: [Decisions](DECISIONS.md), [Research questions](research/RESEARCH_QUESTIONS.md), [Literature matrix](research/LITERATURE_MATRIX.md), [Dynamic clustering review](research/DYNAMIC_CLUSTERING_REVIEW.md).
- Evaluation/product: [Evaluation and backtest](EVALUATION_AND_BACKTEST.md), [Product](PRODUCT.md).
- Governance: [Roadmap](ROADMAP.md), [Reproducibility](REPRODUCIBILITY.md), [Contributing](../CONTRIBUTING.md).
- Historical source caveat còn được artifact tham chiếu: [KBS pilot semantics](data/kbs_pilot_semantics.md) và [data usage risk acceptance](data/DATA_USAGE_RISK_ACCEPTANCE.md).

Các plan, handoff và audit superseded đã được loại khỏi active tree trong R1; Git history là archive duy nhất của chúng.
