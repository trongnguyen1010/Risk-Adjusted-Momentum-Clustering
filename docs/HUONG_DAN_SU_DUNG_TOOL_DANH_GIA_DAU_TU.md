# Hướng dẫn sử dụng DELTA Investment Assessment

## Trạng thái và phạm vi

Assessment là giao diện chỉ đọc một release artifact đã được xác minh. Frontend không fit mô hình, không tính lại verdict và không đổi kết luận khi người dùng đổi feature hoặc lookback.

Trạng thái hồ sơ Task 14 hiện tại:

- Typecheck, production build, integration API local và Playwright regression: **PASS**. Evidence nằm trong [report Task 14](../tests/integration/evidence/assessment-uat/report.md).
- API Assessment trên deployment và UAT thủ công: **BLOCKED / NOT RUN**. Lần kiểm tra production được ghi nhận ngày 2026-11-19 trả `404` cho route FPT Assessment. Cần deploy route cùng artifact đã được owner duyệt trước khi chạy UAT production.
- Bản release được kiểm thử là demo `SIMULATED_AS_OF`, `as_of=2026-01-02`; không phải đánh giá tại ngày hiện tại.

Giữ nguyên dữ liệu và mô hình M2/M3. Không dùng hướng dẫn này để chạy lại pipeline, promote artifact hoặc phát hành dữ liệu. Việc phát hành production cần approval theo [kế hoạch triển khai](plans/KE_HOACH_TRIEN_KHAI_B_PIT_VA_DANH_GIA_DAU_TU.md).

## Chuẩn bị môi trường local

1. Mở PowerShell tại repo `Risk-Adjusted-Momentum-Clustering-git`.
2. Cần có artifact dữ liệu đã được bàn giao riêng. Thư mục `data/` phần lớn không commit lên Git. Khi giải nén gói dữ liệu, kiểm tra tối thiểu có:
   - `data/web/delta-intelligence-v4/manifest.json` và `terminal.sqlite`;
   - `data/experiments/assessment/assessment_v1_run01/manifest.json`, `assessments.jsonl`, `peer_benchmarks.csv`, `coverage.csv`, `feature_history.jsonl`.
3. Cài backend và frontend dependencies:

   ```powershell
   python -m venv --system-site-packages .venv-web
   .\.venv-web\Scripts\Activate.ps1
   python -m pip install -r web/backend/requirements.txt
   npm --prefix web/frontend ci
   ```

   Cần cài Node.js và Python trước. Không commit thư mục `.venv-web`, `node_modules` hoặc artifact dữ liệu.

## Chạy ứng dụng local

Từ repo root, chạy:

```powershell
python scripts/start_delta_terminal.py
```

Mở giao diện tại `http://127.0.0.1:3000`; API docs tại `http://127.0.0.1:8010/docs`. Dừng cả hai tiến trình bằng `Ctrl+C` trong terminal đã chạy lệnh.

Script cần presentation bundle `data/web/delta-intelligence-v4`. Nếu thiếu bundle, ứng dụng dừng và yêu cầu chuẩn bị dữ liệu; không chạy export hoặc dựng dữ liệu mới chỉ để bỏ qua kiểm tra này. Nếu Assessment artifact thiếu hoặc hash không khớp, endpoint không được coi là sẵn sàng.

## Tra cứu và đọc kết quả

1. Mở `/stocks?ticker=FPT&tab=assessment` hoặc nhập mã trong tìm kiếm rồi chọn tab **Đánh giá đầu tư**.
2. Đọc ticker, trạng thái khả dụng, verdict, ngữ cảnh và ngày `as_of` trước khi xem các đặc trưng.
3. Bốn verdict được hiển thị:
   - `RESEARCH_FAVORABLE` — Tích cực để nghiên cứu.
   - `WATCH` — Theo dõi.
   - `CAUTION` — Cần thận trọng.
   - `INSUFFICIENT_EVIDENCE` — Chưa đủ bằng chứng.
4. Hai profile cụm A/B, bảng 18 đặc trưng, Peers, lý do/rủi ro và nguồn được trình bày từ response/artifact. Giá trị thiếu giữ là thiếu; không tự đổi thành 0.
5. Selector feature đổi đặc trưng đang xem trong một chart. Lookback 5/10 năm chỉ đổi history; không chọn `as_of`, không đổi verdict.
6. Khi đổi mã, kiểm tra tiêu đề và nội dung cùng mã. Nếu response cũ không khớp ticker đang chọn, giao diện không được hiển thị response đó.

Đối với release đã pin trong Task 14, các mã mẫu là FPT/A32 (record có dữ liệu), AAM (insufficient evidence) và VCB (không có record trong release). VCB trả 404 là trạng thái thiếu mã dự kiến, không phải dữ liệu thay thế.

## API và mã phản hồi

Endpoint chính:

```text
GET /api/v2/stocks/{ticker}/assessment?lookback_years=10
```

`lookback_years` chỉ nhận `5` hoặc `10`. Có thể gửi `revision` để khóa release. Ý nghĩa phản hồi:

| HTTP | Ý nghĩa |
|---|---|
| `200` | Có response cho mã; response vẫn có thể là `INSUFFICIENT_EVIDENCE`. |
| `404` | Mã không có trong release. Nếu FPT trả `{"detail":"Not Found"}`, có thể đang gọi service chưa deploy route hoặc nhầm API URL. |
| `409` | Revision yêu cầu không khớp release Assessment đang phục vụ. |
| `422` | Ticker hoặc query không hợp lệ; lookback ngoài 5/10 bị từ chối. |
| `503` | Route có nhưng Assessment artifact chưa được phát hành/nạp hoặc không qua xác minh. |

`/api/v2/health` trả `200` chỉ xác nhận service đang chạy; cần gọi endpoint Assessment riêng. Hợp đồng đầy đủ ở [Assessment OpenAPI spec](api/OPENAPI_ASSESSMENT_SPEC.json).

## Release pins và evidence

Các giá trị cần đối chiếu khi kiểm tra release hiện tại:

| Pin | Giá trị |
|---|---|
| Release ID | `assessment_v1_run01` |
| Revision | `assessment-v1-run01-20261116` |
| Context / `as_of` | `SIMULATED_AS_OF` / `2026-01-02` |
| Required price session | `2025-12-31` |
| Manifest SHA-256 | `63a0b747d200638151052e0168b542316e013d8561916860416d1e4118bd09a8` |
| Deterministic content SHA-256 | `418def26a0db719205f01b73d71467adcd6d1930bd549bc509c9183309f3f8bb` |

Nguồn chuẩn của pins là [release pointer](../configs/product/assessment_release_v1.json) và [response pins của UAT](../tests/integration/evidence/assessment-uat/response-pins.json). Không sửa pin trong tài liệu để làm cho kết quả khác khớp.

## Kiểm tra và UAT

Các lệnh kiểm tra frontend/API đã dùng trong Task 14:

```powershell
npm --prefix web/frontend run typecheck
npm --prefix web/frontend run build
$env:PYTHONPATH="web/backend;src"
python -m unittest tests.integration.test_assessment_endpoints -v
```

Playwright regression được chạy bằng script [verify_assessment_ui.cjs](../tests/integration/verify_assessment_ui.cjs); kết quả và screenshots lưu trong [assessment-uat](../tests/integration/evidence/assessment-uat/). Các test tự động local không thay thế production API check hoặc UAT thủ công.

Khi production endpoint phục vụ đúng pins, người kiểm tra làm từng ca trong [manual UAT checklist](../tests/integration/evidence/assessment-uat/manual-uat-checklist.md), ghi reviewer/ngày giờ/URL/commit, PASS/FAIL/BLOCKED và lưu screenshot/response. Stale hiện tại là fixture tổng hợp; không báo cáo nó là stale production. Không đánh dấu UAT PASS nếu FPT trả 404/503 hoặc pins không khớp.

## Giới hạn, phát hành và rollback

- Bản hiện tại là dữ liệu mô phỏng tại `2026-01-02`; không tự đổi sang ngày hiện tại và không có điều khiển chọn `as_of` công khai.
- Artifact nằm trong `data/` bị Git ignore. Docker hiện tải các file được liệt kê trong `deploy/render/data-files.txt`; danh sách hiện chưa có Assessment artifact. Cần xác nhận owner approval, quy trình lưu trữ, hash và quyền truy cập trước khi thêm/phát hành dữ liệu.
- Không chạy publisher có thể tạo kho dữ liệu công khai trước khi được duyệt. Không deploy production thay cho người sở hữu service hoặc khi chưa đạt điều kiện approval trong kế hoạch.
- Khi rollback, khôi phục một tổ hợp frontend, backend và dataset đã biết là tương thích. Không ghi đè artifact lịch sử, không sửa M2/M3 và không thay release pointer chỉ để làm API chạy.

## Hồ sơ nghiệm thu

- [Task 14 report](../tests/integration/evidence/assessment-uat/report.md)
- [Manual UAT checklist](../tests/integration/evidence/assessment-uat/manual-uat-checklist.md)
- [Response pins](../tests/integration/evidence/assessment-uat/response-pins.json)
- [UI regression result](../tests/integration/evidence/assessment-uat/ui-result.json)
- [Assessment API spec](api/OPENAPI_ASSESSMENT_SPEC.json)
