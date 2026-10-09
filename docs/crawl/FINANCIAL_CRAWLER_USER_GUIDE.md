# Financial crawler — hướng dẫn bàn giao

Flow: config → preflight → structured KBS → CafeF document discovery/PDF →
embedded text/selected-page OCR → candidates/coverage/accounting QA → review queue → verify.
Runner dùng được từ checkout hoặc gói source bàn giao; không cần các run pilot trên máy tác giả.

## Cài môi trường

Python 3.11 trở lên. Structured acquisition chỉ dùng standard library. Để trích text PDF,
cài dependency đã pin; không dùng một `.venv` được copy từ máy khác.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r configs/data/financial_crawl_requirements.txt
```

Selected-page OCR cần Windows, Windows en-US OCR và Poppler `pdftoppm` trên PATH.
Doctor kiểm tra runtime và OCR engine khi config có chọn trang OCR. Linux/macOS có
thể chạy structured acquisition và PDF text; chưa có OCR backend cho hai hệ điều hành này.
Không cần Vnstock SDK, tài khoản broker hoặc dữ liệu market để crawl candidates.

## Chạy từ thư mục dự án

```powershell
.\scripts\crawl_financial.ps1 -Action doctor
.\scripts\crawl_financial.ps1 -Action plan
.\scripts\crawl_financial.ps1 -Action run -Output data/financial/my_run_01 -ExecuteNetwork
.\scripts\crawl_financial.ps1 -Action verify -Run data/financial/my_run_01
```

Nếu launcher báo Python không chạy được, dùng `-Python 'C:\path\to\python.exe'`.
Có thể gọi Python trực tiếp trên mọi hệ điều hành:

```powershell
python scripts/crawl_financial.py doctor --config configs/data/financial_crawl_user.example.json
python scripts/crawl_financial.py run --config configs/data/financial_crawl_user.example.json --output data/financial/my_run_01 --execute-network
```

Không có `--execute-network`/`-ExecuteNetwork` thì chỉ dùng cache. Output phải mới;
không ghi đè run cũ. Config/output/resume/seed là path trong checkout; output dưới `data/`.

## Config cần chỉnh

Copy `configs/data/financial_crawl_user.example.json` thành config riêng:

Config mẫu đã pin bốn URL PDF annual 2025 FPT/VNM/PVS/ACV và template EPS trang55
FPT đúng exact hash; `pdf_discovery=false` để không phụ thuộc hai link CafeF 404 đã
quan sát. Đây là ví dụ FY2025, không tự chuyển sang báo cáo mới nhất. Với mã/năm mới,
xóa/cập nhật `documents`, bật discovery và bổ sung exact issuer URL khi queue báo link lỗi.

- `symbols`: tối đa 10 mã mỗi batch pilot; chưa mở full-universe unattended acceptance.
- `company_types`: khai báo cho từng mã. `Regular` có candidate crosswalk; Bank,
  Securities, Insurance giữ wire values và yêu cầu review template, không mượn mapping Regular.
- `years`: target coverage, không khiến provider tự trả đủ lịch sử.
- `periods`: `year`, `quarter` hoặc cả hai. Quarterly cashflow/income chưa tự gán standalone/YTD.
- `structured_pages`: các trang 1–3 cần probe; giữ overlap/conflict, không suy số cột từ pageSize/Head.
  Các cột có cùng period identity bị đánh dấu mơ hồ và không tính vào target coverage.
- `cache_epoch`: giữ cố định để replay cùng vintage; tạo epoch/run mới khi lấy snapshot mới.
- `pdf_discovery`: lấy danh sách tài liệu hợp nhất cho mã/năm; `pdf_quarters` chọn 0=năm, 1–4=quý.
- `documents`: URL chính xác của tài liệu bổ sung, hữu ích khi listing thiếu hoặc link lỗi.
- `budgets`: request/PDF/page/byte/time caps. Job vượt cap ghi `DEFERRED_*`; không được báo đủ dữ liệu.

Một nguồn structured chính và một nhánh document evidence; không gọi nhiều provider cho
mỗi ô. KBS được chọn sau probe thực tế; CafeF/issuer PDF giữ vai trò đối chiếu/thuyết minh.
Không có cấu hình tự fallback để vượt 401/403/429/challenge.

## Chọn trang thuyết minh và template OCR

Sau lượt đầu, đọc `review-queue.json` và tài liệu gốc để chọn **trang vật lý PDF**, từ 1.
Thêm document chính xác vào config mới; entry explicit ưu tiên page selection khi URL
trùng discovery, nhưng không có ưu tiên giá trị giữa các bản báo cáo.

```json
{
  "symbol": "FPT",
  "year": 2025,
  "quarter": 0,
  "url": "https://issuer.example/report.pdf",
  "pdf_sha256": "SHA256_THAT_DOCUMENT",
  "ocr_pages": [55],
  "cell_templates": [
    {
      "field": "weighted_average_basic_shares",
      "year": 2025,
      "pdf_page": 55,
      "box": [0.60, 0.43, 0.76, 0.455],
      "unit": "SHARES",
      "reference_value": 1699740091
    }
  ]
}
```

Ví dụ trên minh họa schema, không dùng URL/hash placeholder để chạy. Thêm hostname thật
vào `approved_hosts` sau khi kiểm tra nguồn. Template có `box` theo tỷ lệ ảnh 0–1 hoặc
`row_code`; chỉ áp dụng cho exact PDF hash đã review. Ô không rõ trả missing/ambiguous,
không sửa chữ thành số. `reference_value` do người review cung cấp để QA, không tự cấp
production acceptance. Không lấy vị trí của template FPT áp cho mã/PDF khác.

```powershell
.\scripts\crawl_financial.ps1 -Action run -Config configs/data/my_selected_pages.json -Output data/financial/my_run_02 -ResumeFrom data/financial/my_run_01
.\scripts\crawl_financial.ps1 -Action verify -Run data/financial/my_run_02
```

Resume từ run gần nhất theo transitive checkpoint, kể cả parent bị ngắt chưa sealed;
chỉ checkpoint đã sealed được dùng. Run đã hard-stop giữ network latch trên resume.
Không dùng resume để vượt access boundary; cần xử lý quyền nguồn trước khi chạy lại.

## Đọc kết quả và exit code

| File | Nội dung |
|---|---|
| `report.md` | Kết quả collection và coverage, giới hạn còn lại |
| `results.json` | Requests, documents, QA, metrics và provenance checkpoint |
| `candidates.jsonl` | Wire cells, null, raw header, mapping candidate và source hash |
| `candidates.csv`, `coverage.csv` | Bản xem thuận tiện theo mã/kỳ/field |
| `raw/` | Structured response copies đi cùng export, hash-verified |
| `review-queue.json` | Missing fields/periods, conflicts, scan pages, semantics/publication |
| `tasks/` | Raw/text/ảnh/OCR và checkpoint manifest bất biến |
| `work-log.jsonl` | Tiến trình từng bước; `code/` giữ source snapshot |

JSONL/raw giữ đúng kiểu dữ liệu; CSV chỉ để xem, có escape spreadsheet formulas.
Publication provider/fetched_at không thành ngày công bố PIT. Các vintage/conflict giữ
riêng; không average hoặc missing=0. Accounting QA có tolerance 1.500 VND cho residual
ba khoản mục theo candidate unit=1.000 VND; arithmetic pass không chứng minh unit/scope.

| Exit | Ý nghĩa |
|---:|---|
| 0 | Command thành công; với run, toàn bộ acquisition/parsing được yêu cầu đã thực hiện |
| 1 | Config/path/integrity hoặc lỗi không thể chạy |
| 2 | Run PARTIAL: thiếu response, document, dependency hoặc hết cap |
| 3 | Doctor/launcher thiếu runtime |
| 4 | HARD_STOP do access/rate-limit boundary |

`Collection COMPLETE` **không đồng nghĩa** coverage đầy đủ hoặc financial-ready. Scan không
được chọn OCR vẫn nằm trong review queue. Crawler chưa tự nghiệm thu facts, publication,
revisions hay score. Reference calculators đã review là bước riêng của dự án; financial
clustering còn cần usable history, identity/sector và protocol được freeze.

## Trước khi tăng số mã

Hoàn thiện mapping và review pilot, benchmark parser theo template trên ground truth
độc lập, khóa tiêu chí accuracy/coverage/review-cost trước test, rồi nghiệm thu batch
20–30. V1 giới hạn 10 mã để không ngầm mở full-universe crawl; không chia 1.000 mã
thành batches để vượt gate. Có thể mở feature subset được review trước.
