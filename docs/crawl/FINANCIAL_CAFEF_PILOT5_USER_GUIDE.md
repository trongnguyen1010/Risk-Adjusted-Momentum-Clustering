# Chạy lại pilot CafeF 5 mã — FY2025

Đã crawl/tính ngày 18/10/2026, chốt offline replay/seal ngày 19/10/2026; trạng thái **PARTIAL_WITH_RESULTS: 29/30 ô**.
BRC/FPT/MWG/GMD đủ 6 families; VNM có EPS/PE/PB/M/Z và F còn 8/9 signals,
khoảng 4–5/9. Hai dư nợ theo kỳ hạn gốc tại cuối 2024/2025 chưa rõ trong notes.

## Lệnh đã kiểm tra trên máy này

```powershell
Set-Location 'C:\Projects\Intern\SourceCode-CafeF'
.\scripts\financial_cafef_pilot.ps1 -Action doctor
.\scripts\financial_cafef_pilot.ps1 -Action plan
.\scripts\financial_cafef_pilot.ps1 -Action run
.\scripts\financial_cafef_pilot.ps1 -Action report
.\scripts\financial_cafef_pilot.ps1 -Action resume
.\scripts\financial_cafef_pilot.ps1 -Action verify
```

Các lệnh trên dùng cache/review đã pin; replay không tạo network hoặc OCR mới.
`verify` kiểm hash tài liệu/ảnh/raw/code, journal và tái tính bằng calculators hiện
có. `VERIFIED` là integrity/replay PASS; goal vẫn PARTIAL khi chỉ có 29/30 giá trị.

Config mặc định `configs/data/financial_cafef_pilot5_execution_v1.json` là executable
contract riêng. Planning JSON v2 và wrapper50 cũ giữ vai trò riêng.
Run nằm ở `data/financial/cafef_pilot5_execution_v1`; đọc `execution-state.json`
để lấy `latest_result`. Folder đó có metrics/inputs/dependencies/QA/manifests.
Report bàn giao tại `artifacts/reports/financial-cafef-pilot5-execution-v1/report-v2.md`.

Chỉ acquisition được opt in bằng lệnh đã thực chạy sau đây:

```powershell
.\scripts\financial_cafef_pilot.ps1 -Action resume -Network
```

Receipt hoàn tất/lỗi terminal được giữ, nên lặp lệnh không tải lại mọi file.
Pending request mới chỉ chạy trong request plan hợp lệ và ngân sách/deadline ban
đầu. `plan` hiển thị 38 logical tasks đã khai báo, counters và dependency còn lại.
401/403/429/challenge latch; EPS route/campaign bị chặn trước đó giữ nguyên.
Không dùng run ID, query hoặc cookie mới để retry cùng một request đã hết cap.

Network deadline là 6 giờ từ `created_at` trong journal, không từ thời điểm
resume. Sau deadline, report/verify/tính từ cache tiếp tục dùng được.
Đợt đã chạy dùng 48 transport attempts/38 logical requests/3 PDF attempts,
7.103.375 bytes, 0 OCR pages mới; có 21 DNS errors sandbox và 1 HTTP404 được giữ.

## Runtime và khôi phục

Wrapper ưu tiên Python bundled của Codex trên máy này; truyền executable khác
khi cần, ví dụ:

```powershell
.\scripts\financial_cafef_pilot.ps1 -Action doctor -Python 'C:\Projects\Intern\SourceCode-CafeF\.venv\Scripts\python.exe'
```

Doctor kiểm branch `research/financial-data`, source pins, reviewed cache,
`pdftoppm` và OCR script. Sandbox không khởi động được WindowsApps Python của
`.venv` trong lượt này; bundled Python đã chạy thành công. Môi trường không có
PowerShell có thể gọi `python scripts/financial_cafef_pilot.py verify`.

Journal là source of truth. OS lock ngăn chạy song song; counters, bytes reserved,
deadline và latch được khôi phục sau process restart. Torn journal hoặc request
gián đoạn trước khi có receipt dừng ở review rõ ràng; không tự xóa tail/reset.
Initial projection thiếu ở lần đầu đã được ghi vào `policy-deviations.csv` và
được sửa trong `prepare`; journal/task graph/contract lúc đó đã tồn tại.

Review packages `reviews/01...04` là các phiên bản bất biến. Khi có chứng cứ mới,
thêm package kế tiếp với source/page hashes, facts compatible và `supersedes`;
runner tính lại mọi metric đủ input rồi tạo result folder mới. Đây là flow cho
pilot đã chốt; notes chưa được tự động accepted từ OCR cho mã/kỳ khác.

## Đọc đúng kết quả và đóng ô còn thiếu

Giá raw chung ngày **22/04/2026**: BRC 12.500, FPT 74.600, MWG 86.400,
GMD 73.500, VNM 61.800 VND/share. PE dùng annual EPS từ numerator/WA cơ bản;
PB dùng **book snapshot 31/12/2025**, parent common equity và common shares cuối
năm đã loại treasury/NCI. Event bridge sau balance date chưa certified; các số
này là annual/snapshot references, không phải latest TTM hoặc production PIT.

VNM cần schedule nêu rõ **dư nợ cuối kỳ** của phần originally-long-term đến hạn
trả tại 31/12/2025 và 31/12/2024. Đã kiểm cache, API mới, full CafeF VAS PDF và
issuer audited English note15 pp47–48. Số phân loại lại 20.750.493.750 VND là
flow trong năm; không thay cho closing current portion. M vẫn tính được vì
variant M8 đã khai báo dùng current liabilities + noncurrent loans/leases.

Financial/research/cluster gates và baseline cohort50 32/300 giữ nguyên.

## Bổ sung closing debt và replay pilot5

[Completion config](../../configs/data/financial_pilot5_completion_v1.json) và
[runner](../../scripts/financial_pilot_completion.ps1) nhận closing stock còn thiếu.
Kết quả thực chạy vẫn **29/30**, xem
[result và queue](../../data/financial/pilot5_completion_v1/results/ee79bf4278f3ae944d02/report.md).

```powershell
.\scripts\financial_pilot_completion.ps1 -Action run -Review data/financial/pilot5_completion_v1/reviews/01-supporting-notes.json
.\scripts\financial_pilot_completion.ps1 -Action verify -Output data/financial/pilot5_completion_v1/results/ee79bf4278f3ae944d02
```

Hai lệnh offline trả cùng immutable result khi input không đổi; kiểm baseline,
source pins, số học và dependencies. `review-queue.json` ghi2field-period còn thiếu.
Đã acquire1PDF công ty mẹ mới2.626.709bytes từ observed disclosure URL.
`acquire -Network` chạy lại đọc terminal receipt, không gửi request; không reset
campaign cũ.11trang render,9trang đã xem,0OCR; web queries không tính vào counters.

TrangPDF40/trang in39, note16 BCTC riêng xác nhận vay mẹ kỳ hạn1–12tháng;
dư cuối2025 là8.841tỷVND. Không thay consolidated input bằng standalone.
BCTC hợp nhất2023/PDF47 tách current portion; không dùng số2023 hay flow phân loại
lại cho2024/2025. [Findings và hashes](../../data/financial/pilot5_completion_v1/reviews/01-supporting-notes.json).

Khi có evidence, tạo review mới theo schema `pilot5-closing-debt-review-v1` với
`source_pins` và2`observations` VNM2024/2025. Mỗi dòng cần cuối năm`balance_date`,
`scope=CONSOLIDATED`, `framework=VAS`, `unit=VND`,
`basis=ORIGINAL_LONG_TERM_CLOSING_STOCK`, `review_status=REVIEWED_REFERENCE_ONLY`,
`reviewed_by`, `current_portion`, `noncurrent_portion`, `total_original_long_term_debt`,
`evidence` có`pdf_path`, `image_path`, `pdf_page`, `locator`; paths phải có SHA256
trong`source_pins`. Tổng phải bằng2components. Không nhận null/NaN/flow/IFRS/riêng.
Chạy`run -Review <file mới>` rồi`verify -Output <result mới>`. Không sửa evidence cũ.
Runner chỉ thêm2facts, kiểm29metrics khác không đổi, tính lại và seal theo hash.
Chỉ đủ30giá trị mới có`GOAL_ACHIEVED`; hiện cần closing debt split của công ty con.
