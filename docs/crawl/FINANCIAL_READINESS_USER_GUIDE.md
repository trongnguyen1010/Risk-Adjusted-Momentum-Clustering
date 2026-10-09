# Tự chạy financial readiness cho 50 mã

Trước khi điền template, đọc [handbook chỉ số/data](../research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md)
để biết formula, field keys, kỳ dữ liệu, thuyết minh và PIT/QA của từng chỉ số.

Flow này dùng checkout **`C:\Projects\Intern\SourceCode-CafeF`**, nhánh
`m1-cafef-primary-experiment`. Mục tiêu: kiểm tra từng mã có đủ dữ liệu tính chỉ số
hay chưa, tải phần tài liệu còn thiếu và đưa công việc review thành hàng đợi cụ thể.
Bạn chạy local, không cần mở một phiên Codex trong thời gian chờ crawl/OCR.

V1 tập trung **FY2025**, dùng tài liệu annual **2023–2025** cho history/comparatives.
Bảng gồm 50 mã × 6 task = **300 ô**. Đây là phạm vi nhỏ hơn checklist 900 ô
2023–2025 trước đây; không dùng hai mẫu số để so phần trăm tiến độ trực tiếp.
CafeF tiếp tục là nguồn acquisition chính; official PDF đã có của PAN/DGC và các
scope exceptions được dùng lại qua exact hashes. Không crawl lại market data.

## Chạy nhanh

Mở PowerShell thông thường, chạy từng lệnh. Lệnh `plan` chỉ chạy một lần cho một
Run. `doctor` không tải tài liệu. `acquire` chỉ gọi mạng khi có `-ExecuteNetwork`.

```powershell
Set-Location 'C:\Projects\Intern\SourceCode-CafeF'

# 1. Kiểm Python, branch, input hashes, Poppler, Windows OCR và dung lượng đĩa.
& .\scripts\financial_readiness.ps1 -Action doctor

# 2. Đóng băng 50 mã/config và xuất assessment ban đầu, không network/OCR.
& .\scripts\financial_readiness.ps1 -Action plan

# 3. Tận dụng cache và tải listing/PDF còn thiếu, tối đa 300 jobs trong lệnh này.
& .\scripts\financial_readiness.ps1 -Action acquire -ExecuteNetwork -Limit 300

# 4. Limit đếm PDF, không đếm số mã. Mỗi lệnh kiểm tối đa một PDF của một mã.
# Mặc định OCR 16 trang đầu, chưa toàn bộ notes.
foreach ($financialSymbol in @('MWG','GMD','VHC','DGC')) {
    & .\scripts\financial_readiness.ps1 -Action extract -Symbols $financialSymbol -Limit 1
}

# 5. Xác minh evidence và cập nhật bảng kết quả.
& .\scripts\financial_readiness.ps1 -Action verify
& .\scripts\financial_readiness.ps1 -Action audit
```

Nếu execution policy máy bạn chặn `.ps1`, dùng entrypoint Python tương đương,
không cần đổi execution policy của máy:

```powershell
& .venv\Scripts\python.exe scripts\financial_readiness.py doctor
& .venv\Scripts\python.exe scripts\financial_readiness.py plan
& .venv\Scripts\python.exe scripts\financial_readiness.py acquire --execute-network --limit 300
foreach ($financialSymbol in @('MWG','GMD','VHC','DGC')) {
    & .venv\Scripts\python.exe scripts\financial_readiness.py extract --symbols $financialSymbol --limit 1
}
```

Runner mặc định dùng `.venv\Scripts\python.exe`. Có thể truyền `-Python` là đường
dẫn tuyệt đối tới Python khác đã cài `pypdf`; `pdftoppm` phải ở PATH và Windows phải
có OCR language `en-US`. `doctor` trả `PASS` trước khi chạy. Không cài dependency
hoặc đổi source ngầm trong quá trình chạy.

## Đọc kết quả để biết mã nào tính được

Tất cả output nằm trong **một root**:
`data\financial\user_workflow50_v1`. Report mới nhất được in ở cuối lệnh. Mở tự động:

```powershell
$flowRoot = 'data\financial\user_workflow50_v1'
$latestReport = Get-ChildItem -LiteralPath "$flowRoot\reports" -Directory |
    Sort-Object Name -Descending | Select-Object -First 1
Get-Content -LiteralPath (Join-Path $latestReport.FullName 'report.md')
Invoke-Item -LiteralPath (Join-Path $latestReport.FullName 'readiness.csv')
```

| File | Câu hỏi được trả lời |
|---|---|
| `summary.json` | Bao nhiêu mã/ô có reference, PDF/OCR, jobs còn lại và counters? |
| `readiness.csv` | Mỗi mã, chỉ số, FY2025 đang ở trạng thái nào? |
| `readiness.json` | Input nào thiếu/conflict, giá trị reference và PIT nào đã có? |
| `missing-queue.json` | Công việc tiếp theo cho từng task chưa có reference? |
| `documents.json` | PDF path/hash/vintage nào đã có, đã OCR những trang nào? |
| `pending-acquisition.json` | Các request chưa thực hiện hoặc chưa có receipt? |
| `exceptions.json` | Link lỗi, listing không có annual, lỗi extraction nào cần xử lý? |
| `previous-valuation-references.json` | PE/PB/TTM đã review trước đây, giữ nguyên basis và period |

Các status quan trọng:

- `REFERENCE_CALCULATED`: có kết quả arithmetic dựa trên evidence đã review;
  đọc `publication_review_required` và `references` để biết PIT, không chỉ nhìn số.
- `UNREVIEWED_INPUTS`: đủ số ứng viên nhưng units/scope/notes/vintage chưa xác minh.
- `MISSING_OR_CONFLICTING_INPUTS`: thiếu trường hoặc có nhiều giá trị;
  `missing_fields` chỉ rõ field, năm và nguyên nhân.
- `SECTOR_TEMPLATE_REQUIRED`: cần adapter theo Bank/Securities/Insurance.
- `REFERENCE_OTHER_BASIS_ONLY`: có phép tính PE/PB tham khảo với basis khác,
  chưa đủ strict task được yêu cầu; không đổi annual PE thành PE TTM.

Các candidate Z/printed EPS được giữ riêng trong JSON để chọn công việc ưu tiên.
Chúng không được tính vào số accepted metrics. Baseline dùng lại FPT/ACV và
PHP/VCS/VEA/PAN; không cộng VNM/PVS vào 50 mã. Giá/snapshot vẫn là **28/08/2026**,
không phải giá hiện tại ngày bạn chạy.

## Chạy tiếp, dừng và kiểm soát chi phí

Sau khi tải, có thể chạy batch OCR tiếp trên tất cả tài liệu đã có:

```powershell
# Mỗi lệnh xử lý tối đa 8 PDF, tối đa 320 trang OCR mới.
& .\scripts\financial_readiness.ps1 -Action extract -Limit 8

# OCR đầy đủ notes cho một mã cụ thể, dùng lại các trang đã có.
& .\scripts\financial_readiness.ps1 -Action extract -Symbols MWG -FullOcr -Limit 1

# Hoặc ghép acquire còn lại + một batch extraction + report.
& .\scripts\financial_readiness.ps1 -Action run -ExecuteNetwork -Limit 8
```

Lặp `extract` hoặc `run` trên **cùng Run** để xử lý phần còn lại. Mặc định 16 trang
chỉ giúp tìm statements/header/publication; **không chứng minh notes đã đầy đủ**.
`-FullOcr` đọc phần trang chưa có đến hết PDF, trong giới hạn còn lại; có thể cần
chạy lại cùng lệnh nếu một batch hết 320 trang. Không tự đọc số từ ảnh rồi promote.

Ctrl+C có thể dừng tiến trình. Chạy lại cùng lệnh để tiếp tục. OS lock ngăn hai
terminal ghi cùng Run, tự nhả khi process kết thúc. Receipt hoàn tất/raw hash và
cache commit được dùng lại; counters network không reset. Nếu dừng giữa download
hoặc render/OCR, attempt/page reservation đã tiêu thụ vẫn được tính; partial files
không được nhận là evidence hoàn tất. Phần đó có thể cần xử lý lại, không hứa
resume đúng byte hoặc đúng trang đang thực hiện. Không xóa lock/raw/receipts bằng tay.

Extraction lỗi đã ghi nhận không tự retry tốn CPU; đọc `exceptions.json`, sửa
dependency/input hợp lệ rồi chủ động chạy `extract -RetryFailed` nếu cần. Known
source failures cũ, ví dụ URL404, không bị request lại. Chúng vẫn cần exact official
source recovery; flow không đoán URL hoặc tự chuyển sang KBS.

Giới hạn toàn Run: 300 logical requests/300 attempts, 150 PDF attempts, mỗi response
≤25 MB, tổng tải mới ≤1,5 GB, spacing ≥2 giây, timeout25 giây, tối đa24 giờ từ lần
network đầu. OCR tối đa6.000 trang mới toàn Run; batch≤320; PDF≤250 trang. Cache
không tính vào bytes tải mới; OCR vẫn có thể tạo nhiều GB ảnh, runner yêu cầu ít
nhất3 GB đĩa trống trước mỗi PDF. Đây là caps, không phải dự báo chi phí.

401/403/429/challenge hoặc hết ngân sách sẽ **GLOBAL_STOP** và giữ latch khi chạy
lại; exit code3. Không tạo Run mới/chỉnh budget để né latch. Dừng acquisition và
đọc `summary.json`/transport receipts. `audit`/`verify` vẫn có thể chạy offline.
Lỗi validation/dependency trả exit code2. Một batch thành công trả0 vẫn có thể còn
missing inputs hoặc extraction failures, nên luôn đọc report.

## Review dữ liệu và tính chỉ số

Tạo JSON review cho một mã từ tài liệu đã tải:

```powershell
& .\scripts\financial_readiness.ps1 -Action template -Symbol MWG
```

Nếu có nhiều PDF vintage, runner yêu cầu `-PdfSha '<sha256 từ documents.json>'`;
không chọn nguồn/vintage đầu tiên làm ưu tiên số liệu. Lệnh in đường dẫn JSON trong
`review-inputs`. Bạn mở JSON và ảnh/PDF để kiểm. Giữ field chưa biết ở `null`.

Điền các metadata đã xác minh:

```json
{
  "reviewer": "ten-nguoi-kiem",
  "reviewed_at": "2026-10-08",
  "scope": "CONSOLIDATED",
  "framework": "VAS",
  "vintage_basis": "CURRENT_AND_COMPARATIVE_IN_EXACT_PDF_REVIEWED",
  "ebit_basis": "EBT_PLUS_DISCLOSED_EXPENSED_INTEREST_EXCLUDING_ISSUANCE_FEES",
  "receivables_basis": "GROSS_SHORT_TERM_TRADE"
}
```

Đây là **những khóa cần chỉnh trong template**, không thay toàn bộ JSON bằng đoạn
trên. Chỉ khai báo receivables basis khi đã review cách lấy phải thu. Nếu chưa rõ,
giữ `UNREVIEWED`; M sẽ chưa có giá trị. EBIT có thể chọn
`DIRECT_DOCUMENT_RECONCILED_EBIT` khi đã xác minh giá trị EBIT trực tiếp. Không lấy
code23 kèm phí phát hành làm lãi vay thuần; PAN là ví dụ đã phát hiện.

Với mỗi fact đã kiểm: điền `value` dạng string số VND/SHARES/VND_PER_SHARE đúng
`unit`, `pdf_page` (số trang PDF, không phải số in trên báo cáo), `locator` mô tả
note/dòng/cột, và `review_status="VISUALLY_VERIFIED_REFERENCE_ONLY"`.
Các trường template được lấy theo calculator hiện có:

- EPS basic: numerator sau adjustments, weighted basic shares và printed EPS để
  kiểm làm tròn; chưa tự claim normalized/diluted EPS.
- Z: balance fields, retained earnings và EBIT/lãi vay đã đối chiếu; cần balance
  residual≤1 VND. Không nhập số đã làm tròn theo tỷ đồng để vượt kiểm tra này.
- F: có đủ9 tín hiệu, assets ba năm, debt gồm current portion và bằng chứng parent
  issuance. Với indicator issuance, thêm
  `"derivation":"PARENT_COMMON_ISSUANCE_OCCURRED_VERIFIED"`; không biết không điền0.
- M: current/prior receivables, owned tangible PPE, depreciation không gộp
  amortization, debt và các core fields theo basis đã khai báo.

F/M dùng các **VAS reference/sensitivity variants đã có**, chưa phải strict original
scores hoặc quyết định phân loại rủi ro. Thiếu một tín hiệu F thì total giữnull.

Khi cần lấy một fact từ PDF năm trước, thêm vào `supporting_documents` metadata
`pdf_path`, `pdf_sha256`, `period_start`, `period_end`, `scope`, `framework`,
`vintage_basis`, `publication` của **PDF đó**, rồi thêm `source_pdf_sha256` vào fact.
PDF phải thuộc cùng mã trong `documents.json`; trang của fact phải đã OCR.
Các fact cùng year khác vintage không tự ghi đè; template không tự giải quyết
comparative restatements. Người review phải xác minh compatibility trước khi nhập.

`publication` có thể đểnull để tính arithmetic trước. Muốn xác minh PIT, điền:

```json
{
  "publication_date": "YYYY-MM-DD",
  "precision": "DATE_ONLY",
  "pdf_sha256": "hash-cua-dung-PDF",
  "validation_status": "EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED",
  "evidence_path": "data/financial/.../page-02.png",
  "evidence_sha256": "hash-cua-file-evidence"
}
```

Lấy hash file evidence bằng `(Get-FileHash -LiteralPath '<path>' -Algorithm SHA256).Hash.ToLower()`.
Ngày phải là bằng chứng công bố của đúng attachment, không phải ngày ký/audit,
filename hay ngày tải. Script dùng phiên exchange đầu tiên sau ngày công bố;
không cần giờ. Với F/M, cần publication cho mọi supporting PDF được dùng; không
copy ngày main PDF sang các tài liệu khác.

Sau khi điền, chạy đường dẫn JSON mà lệnh `template` vừa trả:

```powershell
& .\scripts\financial_readiness.ps1 -Action review -ReviewFile 'data/financial/user_workflow50_v1/review-inputs/<file-vua-tao>.json'
& .\scripts\financial_readiness.ps1 -Action verify
```

Runner tính EPS/Z/F/M độc lập, kiểm units/pages/PDF hash và xuất `reviews/.../qa.json`
để đối chiếu số ứng viên CafeF. Canonical value vẫnnull khi chưa quyết định
reconciliation. Trước khi sửa review đã chạy, copy thành file mới và giữ vintage/
reference cũ để replay; report giữ các reference khác basis, không average.

**PE TTM/PB chưa có bulk review calculator trong wrapper v1.** Bảng vẫn ghi các
gap TTM, parent equity, historical/current shares, share events, giá và date
alignment. Các reference advanced trước đây nằm ở file riêng, không dùng annual
EPS để lấp TTM. Tương tự, Securities/Bank/Insurance và SLS fiscal-year30/06 cần
adapter riêng; wrapper không nhận chúng như Regular calendar-year. Các giới hạn
này sẽ hiện trong report, không bị gọi là hoàn tất.

## Gửi kết quả lại để xác định bước scale tiếp theo

Bạn chỉ cần gửi thư mục report mới nhất hoặc nội dung `summary.json`,
`readiness.csv`, `exceptions.json` và `missing-queue.json`. Không cần gửi toàn bộ
PDF/ảnh; giữ chúng local để kiểm/replay khi cần. Cho biết lệnh cuối, exit code và
đường dẫn Run nếu có lỗi. Report xác định số mã/ô arithmetic, PIT gaps, source
exceptions và chi phí; **financial cluster/research/full-universe vẫn đóng**.

Config: [financial_user_workflow50_v1.json](../../configs/data/financial_user_workflow50_v1.json).
Implementation/tests/self-review: [report bàn giao](../../artifacts/reports/financial-user-workflow50-v2/report.md).
