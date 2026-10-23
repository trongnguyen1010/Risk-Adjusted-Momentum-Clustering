# DELTA — dữ liệu và phân cụm cổ phiếu Việt Nam

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
chưa chạy trong các lượt cleanup. Bước tiếp theo là baseline thăm dò trêncohort đủ.

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
Market do teammate xử lý riêng; chưa có đầy đủ handoff trên máy này.

Lịch sử chi tiết ở [CHANGELOG](CHANGELOG.md), [Project Map](docs/PROJECT_MAP.md)
và report tổng. Hướng dẫn đóng góp: [CONTRIBUTING](CONTRIBUTING.md).
