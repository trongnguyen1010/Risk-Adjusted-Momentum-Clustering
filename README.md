# DELTA — dữ liệu và phân cụm cổ phiếu Việt Nam

## Demo web — DELTA Intelligence (Execution59)

Đã thêm web local đọc cả A market, B financial và C combined: Overview, Cluster Atlas,
Stock Explorer, Financial Lens và Research Lab. Chạy `python scripts/start_delta_terminal.py`.
Xem [setup, so sánh prompt và phạm vi dữ liệu](web/README.md). Không fit lại model;
financial/combined vẫn ex-post reference, không PIT/backtest. Dữ liệu lớn giữ local.

**Execution58 (24/10/2026):** có A market-only, B financial-only riêng và bảng đối chiếu;
C kết hợp14features đã chạy theo owner-approved protocol:7models/5.593assignments,
2025 chia663/479/6. Đây là descriptive reference, không PIT/backtest; quality REVIEW_REQUIRED.
[Report và bảng A/B/C](artifacts/reports/cluster-comparison-v1/report.md).


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

Cài research dependencies: `python -m pip install -r requirements-market-integration.lock.txt`.
Nhập bundle: `python scripts/import_market_bundle.py <ZIP_PATH>` (idempotent, từ chối ghi đè khác hash).
Dashboard: `python -m pip install ".[dashboard]"`, sau đó `python -m streamlit run m3_dashboard.py`.
Dashboard đọc market artifacts; financial reference có entry point riêng bên dưới.


**Execution56 (23/10/2026):** đã tính lại 70.320 tỷ số và chạy baseline K-Means cho
1.172 mã × 10 năm. [Kết quả và giới hạn](artifacts/reports/financial-full10-baseline-v1/report.md).
Kiểm tra thực thi PASS; chất lượng cần review vì cả 10 năm có cụm dưới 10 mã.
EPS/P/E/P/B/F/M/Z, PIT và M3 vẫn PARTIAL. Các ghi chú cleanup bên dưới là lịch sử.

**Cleanup55:** `data/financial` còn **59** thư mục (trước221), `artifacts/reports` còn **13** (trước57). Các lượt cũ đã gom vào [kho lịch sử](artifacts/archives/financial-history-20261023/README.md); chỉ dùng handoff hiện hành cho M2.

## Bắt đầu tại đây

| Cần tìm | Mở |
|---|---|
| Dataset financial đang dùng | [Bộ bàn giao2016–2025](data/handoffs/financial-reference-2016-2025/README.md) |
| Quá trình và kết quả financial | [Report tổng](artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md) |
| Plan financial / market | [Financial](docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md) · [Market](docs/crawl/MARKET_HISTORY10Y_1500_PLAN.md) |
| Danh sách mã chung cho team | [Registry](configs/data/securities_collection_registry_v1.csv) |
| Lệnh chạy và kiểm tra | [Bảng lệnh](scripts/README.md) |
| Kiến trúc, protocol và tài liệu | [START HERE](docs/README.md) |

Financial hiện có **1.172 mã đủ10 annual periods2016–2025**, gồm11.720 dòng trong
cohort bàn giao. Dataset rộng hơn có13.529 reference rows. Sáu tỷ số cơ bản đã
tính; EPS/P/E/P/B/F/M/Z toàn lịch sử, PIT và M3 vẫn PARTIAL. Phân cụm financial
đã chạy sau cleanup ở Execution56; cần review outliers/preprocessing trước protocol tiếp theo.

## Thư mục nào cần dùng

- `data/handoffs/financial-reference-2016-2025/`: input financial để làm việc.
- `src/`, `configs/`, `scripts/`, `tests/`: code, cấu hình và kiểm tra.
- `data/financial/`: raw API/PDF, receipts, journals và provenance cần giữ.
- `artifacts/reports/`: report tổng và evidence của từng lượt.
- `artifacts/archives/`: bản ZIP giữ exactbytes của evidence/cache không cần mở trực tiếp.
- `docs/`: plans, decisions, architecture và research protocol.

Không nối tất cả các phiên bản trong `data/financial` khi chạy M2. Dataset mới
nhất kế thừa dữ liệu từ các lượt trước; tên phiên bản cũ không có nghĩa source
evidence đã vô dụng. Bốn normalized caches cũ đã chuyển sang cold archive;
[hướng dẫn restore](artifacts/archives/financial-cache-20261023/README.md).

## Ranh giới nghiên cứu

M1 market C8 có905 market-ready tại snapshot legacy; không phải historical
research universe đã nghiệm thu. M2 market-only protocol và M3 backtest tuân theo
[roadmap](docs/ROADMAP.md), [decisions](docs/DECISIONS.md) và [AGENTS](AGENTS.md).
Không đổi research/PIT gates chỉ vì đủ số mã; không chọn model bằng return/Sharpe.
Market handoff và C8 V2 đã hợp nhất trong integration branch; readiness gates giữ nguyên.

Lịch sử chi tiết ở [CHANGELOG](CHANGELOG.md), [Project Map](docs/PROJECT_MAP.md)
và report tổng. Hướng dẫn đóng góp: [CONTRIBUTING](CONTRIBUTING.md).
