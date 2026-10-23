# Documentation — START HERE

**Hiện tại — Execution56:** [baseline 1.172 mã × 2016–2025 đã chạy](../artifacts/reports/financial-full10-baseline-v1/report.md).
70.320 tỷ số được tính lại; kiểm tra độc lập PASS, nhưng cả 10 năm có cụm nhỏ.
Đọc [report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md) để xem kết quả,
outlier queue và giới hạn M2/M3. Các ghi chú chưa phân cụm bên dưới thuộc các lượt cũ.

**Cleanup55:** `data/financial` còn **59** thư mục (trước221), `artifacts/reports` còn **13** (trước57). Các lượt cũ đã gom vào [kho lịch sử](../artifacts/archives/financial-history-20261023/README.md); chỉ dùng handoff hiện hành cho M2.

## Công việc hiện hành

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
