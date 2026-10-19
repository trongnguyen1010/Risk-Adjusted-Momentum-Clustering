# Documentation — START HERE

## Plan mở rộng dữ liệu và danh sách mã chung — 19/10/2026

- [Plan market 2016–2025, warm-up 2013–2015, mục tiêu ≥1.500 cổ phiếu lịch sử](crawl/MARKET_HISTORY10Y_1500_PLAN.md).
- [Plan financial annual/quarterly 2013–2025, reference và PIT cho M3](crawl/FINANCIAL_HISTORY_PIT_PLAN.md).
- [Registry 1.522 current discovery candidates cho team](../configs/data/securities_collection_registry_v1.csv),
  [data dictionary và quy ước phân công](crawl/MARKET_HISTORY10Y_1500_PLAN.md#3-registry-contract-và-phối-hợp-team).

Trạng thái **PLANNED, inventory offline**: 952 mã đã qua C8, 148 deferred C7,
422 ngoài C5/C7; không diễn giải thành 1.522 mã đã crawl hoặc đủ mười năm.
Registry pin bằng chứng, tách observed range, verification/PIT, owner và batch cho
hai domain. Cần bổ sung historical discovery/identity trước freeze acquisition mới.
Hai plan chưa tạo successor runner, chưa mở financial/research/backtest gates.

## Flow financial đang thực thi

Flow financial hiện tại là **pilot BRC, FPT, MWG, GMD, VNM**.
Kết quả đã kiểm chứng: **29/30** chỉ số tham chiếu; VNM F-score còn thiếu cách
tách closing current portion của nợ originally-long-term tại 2024/2025.
P/E là annual reference, P/B dùng book snapshot 31/12/2025; chưa phải bộ current TTM.

- [Hướng dẫn chạy pilot bằng PowerShell](crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md).
- [VNM: truy nguồn công ty con](../data/financial/vnm_subsidiary_debt_review_v1/report.md): thêm 7 PDF, tách được MCM/Vilico và Vietsugar theo entity; kỳ hạn gốc còn thiếu, goal vẫn 29/30.
- [VNM: thuyết minh quý bổ sung và replay](../data/financial/vnm_quarter_debt_followup_v1/report.md): thêm Q4/2024 XLSX và Q4/2025 PDF, vẫn thiếu closing current portion để chốt F-score.
- [Đối chiếu quý/năm theo phản hồi owner](../data/financial/cafef_quarter_row_check_v1/report.md): hàng nợ quý tốt hơn ở BRC/VNM, vẫn cần QA field/kỳ/vintage.
- [Closing-debt continuation](../data/financial/pilot5_completion_v1/results/ee79bf4278f3ae944d02/report.md): PDF mẹ đã kiểm; vẫn29/30, gap tại công ty con VNM.
- [Báo cáo kết quả và các xung đột API/PDF](../artifacts/reports/financial-cafef-pilot5-execution-v1/report-v2.md).
- [Config thực thi](../configs/data/financial_cafef_pilot5_execution_v1.json).
- [Plan và tiêu chí hoàn tất](crawl/FINANCIAL_CAFEF_PILOT5_EXECUTION_PLAN_V2.md).
- [Giải thích chỉ số và input](research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md).
- [CafeF source semantics](crawl/sources/CAFEF.md).
- [QA nguồn mới và PDF — TCBS/SSI](crawl/FINANCIAL_PROVIDER_VALIDATION_USER_GUIDE.md).

Ngày 19/10/2026 đã gỡ 48 legacy entry scripts và temporary work khỏi active tree,
sau khi lưu exact bytes và kiểm hash trong
[gói khôi phục](../artifacts/archives/project-cleanup-20261019-v1/inactive-files.zip).
[Danh sách dọn dẹp](../artifacts/repository/current-flow-cleanup-v1/plan.json)
ghi từng file/folder. Shared modules, tests, config và evidence còn dependency được giữ.
Đã dọn thêm 8 thư mục báo cáo superseded (102 file) khỏi `artifacts/reports/`;
exact bytes nằm trong [archive báo cáo](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip).
Tổng hai lượt: 5.548 file. Các lệnh/links lịch sử cần restore để tái hiện nguyên bản.

Hai lượt dọn đã thực thi; không chạy lại prune scripts.
scripts/crawl_cafef_financial.py được giữ vì test còn import hàm verify handoff.

Khôi phục sau khi dọn bằng Python đang dùng cho project:

```powershell
python artifacts/repository/current-flow-cleanup-v1/cleanup.py restore
python artifacts/repository/current-flow-cleanup-v1/artifact_cleanup.py restore
```

Đã probe routes trong VietFin 0.2.0: TCBS15/15HTTP404, SSI catalogHTTP403 và dừng.
Chưa có field mới để QA số học. Flow bổ sung đã ghi235reference facts/12API conflicts,
tính lại29/30; xem [hướng dẫn và kết quả](crawl/FINANCIAL_PROVIDER_VALIDATION_USER_GUIDE.md).
Campaign CafeF cũ giữ nguyên counters/deadline/hard stops, không reset.

## Tài liệu dự án

- [Current status](CURRENT_STATUS.md), [Project map](PROJECT_MAP.md), [Roadmap](ROADMAP.md).
- [Architecture](ARCHITECTURE.md), [Data contract](DATA_CONTRACT.md), [Methodology](METHODOLOGY.md).
- [Feature contract](research/FINANCIAL_FEATURE_CONTRACT.md), [Decisions](DECISIONS.md).
- [Reproducibility](REPRODUCIBILITY.md), [Contributing](../CONTRIBUTING.md).
- [Market foundation report](../artifacts/reports/m1-market-foundation-v1/report.json)
  và [inspection notebook](../notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb).
- [Data collection và legacy commands](crawl/README.md).
- [KBS pilot semantics](data/kbs_pilot_semantics.md), [data usage policy](data/DATA_USAGE_RISK_ACCEPTANCE.md).

Market foundation vẫn có 905 latest-snapshot market-ready securities, strict
research gate đóng. Nhánh financial chưa mở production/financial clustering.
Lịch sử các lượt chạy nằm trong [Changelog](../CHANGELOG.md) và immutable reports.
