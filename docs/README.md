# Documentation — START HERE

### Chốt integration — 24/10/2026

Đã xử lý toàn bộ merge conflicts; imported data giữ local theo ignore policy.
Financial checkpoint `819cd82`, market parent `340519d`; active branch `integration/market-financial`.
PowerShell wrapper `scripts/market_financial_integration.ps1 -Mode Verify` đã PASS:
market19C8outputs/68holdoutoutputs/84models/75.801assignments; financial1.786pins/11.720rows.
Targeted76tests OK (4optionalStreamlit skips), PCA6tests PASS, importer/immutability5tests PASS
(suite5 gồm4tests đã có trong targeted76 và1test bổ sung, không cộng trùng).
Compile, synthetic smoke và webJS syntax PASS; importer replay20files PASS.

Full repository gate vẫn PARTIAL: sandbox timeout240,2giây; ngoài sandbox timeout360,1giây,
ít nhất250testlines kết thúcok, chưa cóFAIL/ERRORtrước timeout; cuối log ở
`unit.experiments.test_financial_crawl_trial.TrialTests.test_invalid_payload_stops_next_wave_with_all_symbol_gap_rows`.
Không khẳng định suite treo hoặc xác định nguyên nhân từ việc timeout; không bỏ assertions.
Logs `.tmp/integration-full-suite*.log`, summaries `.tmp/integration-full-suite*.json`.

Không fit lại model thực, không acquisition/PDF/OCR mới, không backtest; PIT/research/M3
vẫn false, chất lượng cụm REVIEW_REQUIRED. Commit tích hợp chỉ local; chưa push remote.


**Integration market + financial — 23/10/2026.** Nhánh `integration/market-financial`
kế thừa financial checkpoint `819cd82` và market `340519d`. C8 V2 đã nhập từ
`DELTA_02_ACTIVE_M2_M3.zip`, giữ đúng hashes và path. Market có 84 snapshots
2019–2025, K=2/robust; financial có 1.172 mã × annual 2016–2025, K=3/zscore.
Đây là hai baseline độc lập. Cả hai cần review chất lượng cụm; strict PIT/research/M3
chưa được nghiệm thu. Giao ticker tại cuối 2025 là 1.148 mã, chưa phải historical PIT join.

Chạy `scripts/verify_market_financial_integration.py --publish` để kiểm current
60+24 artifacts và tạo manifest tham chiếu có version; script này không fit.
`verify_m2_task12.py` và `generate_m2_task13_handoff.py` là historical V1,
không dùng chúng để tái tạo current84. Xem `M2/artifacts/market-financial-integration-v1/`.

### Kiểm chứng integration đã thực hiện

- Market:19/19C8outputs,68holdoutoutputs,9frozenpins,84models và75.801assignments PASS;
  kiểm sourceeligibility và nearestcentroid, không refit.
- Financial:1.786inputpins,11.720rows, scaler/assignment/inertia/profiles/checkpoints PASS
  với hai frozen source files đúng hash trong sourceoverlay có version; output review riêng.
- 76 targeted tests: OK,4Streamlittests skipped do thiếu optionaldashboarddependency;
  6 PCAartifacttests PASS. Importer/immutability tests bổ sung PASS.
- compileall, synthetic smoke (`run-20261023T161947Z-e04ef3b8`), `node --check web/app.js` PASS.
- Full repository suite chưa PASS: sandboxtimeout240giây; lượt ngoàisandbox được giới hạn360giây,
  xem `.tmp/integration-full-suite-unsandboxed.json` và log. Không bỏ assertions.
- Plain diffcheck toàn nhánh có inheritedCRLF/Markdownhardbreak warnings từ market artifacts;
  scoped integrationdiffcheck với `cr-at-eol` không có whitespace errors. Không sửa sealedbytes để làm sạch warnings.

## Ghi chú và lineage từ các giai đoạn trước

**Hiện tại — Execution56:** [baseline 1.172 mã × 2016–2025 đã chạy](../artifacts/reports/financial-full10-baseline-v1/report.md).
70.320 tỷ số được tính lại; kiểm tra độc lập PASS, nhưng cả 10 năm có cụm nhỏ.
Đọc [report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md) để xem kết quả,
outlier queue và giới hạn M2/M3. Các ghi chú chưa phân cụm bên dưới thuộc các lượt cũ.

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

**Cleanup55:** `data/financial` còn **59** thư mục (trước221), `artifacts/reports` còn **13** (trước57). Các lượt cũ đã gom vào [kho lịch sử](../artifacts/archives/financial-history-20261023/README.md); chỉ dùng handoff hiện hành cho M2.

## Công việc hiện hành

M2 Nhiệm vụ 1 đã freeze protocol và Nhiệm vụ 2 đã hoàn tất runner preparation/testing. Stage chính xác tiếp theo là **M2 Nhiệm vụ 3 — GLOBAL K TRÊN DEVELOPMENT**; chưa chạy trong stage hiện tại. Eligibility vẫn theo từng snapshot; 905 chỉ là latest-snapshot count và không phải strict research universe.

Chuyển session: đọc [bản bàn giao Execution56](FINANCIAL_SESSION_HANDOFF.md)
để biết trạng thái Git, kết quả model, tests và bước review tiếp theo.

| Nội dung | Tài liệu |
|---|---|
| Dữ liệu financial dùng cho baseline | [Handoff1.172 mã/2016–2025](../data/handoffs/financial-reference-2016-2025/README.md) |
| Lịch sử, kết quả và backlog | [Report tổng financial](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md) |
| Financial acquisition/QA/PIT | [Plan financial](crawl/FINANCIAL_HISTORY_PIT_PLAN.md) |
| Market history10năm | [Plan market](crawl/MARKET_HISTORY10Y_1500_PLAN.md) |
| Universe và phân công team | [Registry](../configs/data/securities_collection_registry_v1.csv) |
| Lệnh hiện hành | [scripts/README](../scripts/README.md) |
| Cách bố trí dữ liệu/kết quả | [data/README](../data/README.md) · [artifacts/README](../artifacts/README.md) |

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

Dataset mới nhất là kết quả50:1.172 full10/13.529 reference rows; lượt52 review 95 gaps
chưa tăng coverage. Cleanup53–54 chỉ thay cách lưu trữ/điểm truy cập, không thay
data, công thức hoặcmodel. Sáu core ratios đã tính; bộ sáu families gốc/PIT/M3
chưa hoàn tất. Phân cụm financial chưa chạy trong các lượt cleanup.

## Plans, kiến trúc và protocol

- [Current status](CURRENT_STATUS.md), [Project Map](PROJECT_MAP.md), [Roadmap](ROADMAP.md).
- [Decisions](DECISIONS.md), [Contributing](../CONTRIBUTING.md), [AGENTS](../AGENTS.md).
- [Data collection và legacy commands](crawl/README.md).
- [Financial feature contract](research/FINANCIAL_FEATURE_CONTRACT.md).
- [Dynamic clustering review](research/DYNAMIC_CLUSTERING_REVIEW.md).
- [KBS semantics](data/kbs_pilot_semantics.md), [data usage policy](data/DATA_USAGE_RISK_ACCEPTANCE.md).

## Evidence và archive

Chỉ dùng mộtcohort bàn giao cho baseline; không chọn dataset bằng kết quả model.
Raw/receipt/journal giữ trực tiếp để truy nguồn và bảo toàn budget/source boundary.
Candidates của bốn batch cũ đã lưu lạnh, xem
[restore cache](../artifacts/archives/financial-cache-20261023/README.md).
Các cleanup cũ có guide riêng tại `artifacts/archives/`; root README trước lượt54
được lưu exactbytes trong `artifacts/repository/financial-cache-archive-20261023/documentation-before.zip`.

Report đã seal giữ nguyên hash. Khi cần replay historical acquisition/QA, restore
đúng cache/path trước; không crawl lại hoặc sửa frozen hashes vì file đang lưu lạnh.
Không cần restore để đọc handoff và tính baseline M2 thăm dò.
