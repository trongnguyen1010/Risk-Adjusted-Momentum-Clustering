# Chạy thử financial crawler 50 mã bằng PowerShell

## Flow CafeF-first active — 08/10/2026

Runner active là `scripts/crawl_cafef_financial.ps1`, config
`configs/data/cafef_financial_trial50_v1.json`. [Report lượt chạy](../../artifacts/reports/cafef-financial-trial50-v1/report.md)
ghi kết quả thực tế; hướng dẫn legacy KBS bên dưới giữ để phục hồi evidence cũ.

Flow: kiểm pin plan/market snapshot và pilot → CafeF detail HTML → kiểm ticker,
header kỳ, số cột và raw number → candidate crosswalk → crawl bù kỳ thiếu trong cap
→ coverage/task-input checklist/review queue → seal/verify → feedback ZIP.
Không tải PDF, OCR hoặc tính score production trong lượt structured này.

```powershell
Set-Location C:\Projects\Intern\SourceCode-CafeF
git branch --show-current
.\scripts\crawl_cafef_financial.ps1 -Action doctor
.\scripts\crawl_cafef_financial.ps1 -Action plan
```

Nhánh cần là `m1-cafef-primary-experiment`. Python ≥3.11, standard library + pypdf
do verifier dependency hiện có; launcher mặc định `.venv\Scripts\python.exe`, có thể
truyền `-Python 'C:\path\to\python.exe'`. Doctor/plan không gọi mạng. Cần giữ pilot,
benchmark và các reference inputs đúng pin: config này là handoff của workspace đã
kiểm chứng, chưa phải package chạy trên máy sạch thiếu evidence.

Lượt 50 mã của stage này dùng `data/financial/cafef_trial50_20261008_v1`.
**Không chạy fresh lần nữa với epoch này.** Xem report, verify hoặc feedback:

```powershell
.\scripts\crawl_cafef_financial.ps1 -Action verify -Run data/financial/cafef_trial50_20261008_v1
.\scripts\crawl_cafef_financial.ps1 -Action feedback -Run data/financial/cafef_trial50_20261008_v1 -Output artifacts/financial_crawler/cafef50_feedback_user_01.zip
```

Nếu bị ngắt, resume từ output gần nhất, tạo output mới:

```powershell
.\scripts\crawl_cafef_financial.ps1 -Action run -Output data/financial/cafef_trial50_user_resume_01 -ResumeFrom data/financial/cafef_trial50_20261008_v1 -ExecuteNetwork
```

Không sửa config/code/epoch giữa lineage. OS lock ngăn chạy đồng thời, registry
bắt buộc parent gần nhất. Cache được kiểm SHA và đọc trước deadline check để vẫn
replay được offline sau hạn; request mới giữ deadline/counters và access latch từ
START. Không đổi epoch để né 401/403/429/challenge hoặc các cap.

- Mẫu đúng 50 mã trong frozen plan; bốn mã QA gồm FPT/VNM/PVS/ACV là cohort riêng,
  VNM/PVS không được thêm vào market-ready membership của trial50.
- Annual2021–2025, quarter2024–2025, checklist score2023–2025; 600 base requests
  (12/mã), thêm tối đa120 gap requests. Một request tại một thời điểm, interval≥2s,
  ≤900 physical attempts, ≤2 attempts/URL qua lineage, timeout≤20s.
- ≤3MB/response, ≤300MB download, deadline2h từ START kể cả thời gian tạm dừng.
  Bytes tải không bằng dung lượng toàn run; exports có thể lớn hơn raw.
- Append-only `transport.jsonl` có hash chain + fsync reservations; không tạo file
  cho mỗi response chunk. Raw deduplicate theo SHA; resume không copy raw parent.
- HTTP302 giữ lỗi, không follow redirect/workaround. Missing raw không thành zero;
  request đã thử trong lượt không bị gọi lại ở gap phase.
- Regular mapping là proposed template candidate; Bank/Securities/Insurance giữ
  raw và sector review queue. Không suy units từ magnitude, fiscal year từ target
  hay PIT từ ngày crawl. `unit_scale`, `published_at`, `available_at` chưa xác minh.

| Output | Cách đọc |
|---|---|
| `results.json`, `work-log.jsonl` | Status/counters/request errors và provenance |
| `coverage.csv` | 1.950 target statement-periods, tách non-null wire và mapped fields |
| `requirements.csv` | Exact annual input presence/conflicts/missing notes |
| `feature-readiness.csv` | 900 task-year rows, candidate inputs và strict blockers |
| `qa.json`, `review-queue.json` | Known reference exceptions, gaps, sector/notes/PIT/revisions |
| `raw/`, `candidates.jsonl`, `transport.jsonl` | Raw HTML, candidate cells và durable journal |
| `manifest.json`, `dependencies.json` | Local và transitive checksum verification |

Exit0 chỉ nói command đã xuất artifact; **đọc `engineering_status` riêng**:
PARTIAL/BUDGET_STOP/HARD_STOP không phải complete data. Exit2 là config/path/integrity
error. Ctrl+C/crash có thể chưa có manifest, dùng latest resume. Feedback ZIP chỉ có
compact outputs, không thay full raw/manifests; giữ local lineage để debug/verifier.

Kiểm tra tái lập toàn bộ exports offline, không tạo data root hoặc reset epoch:

```powershell
.venv\Scripts\python.exe scripts\replay_cafef_financial_exports.py --run data/financial/cafef_trial50_20261008_v1 --output artifacts/financial_crawler/cafef50_reparse_user_01.json
```

Output phải mới. Command kiểm manifest/raw/reference pins và pinned core code rồi
so tám exports byte-identical. Đây là raw reparse/export check, không phải resume
journal mới. Lượt50 hiện có đã đạt kiểm tra này; sealed report giữ exact hashes.

Wire coverage không phải accuracy hoặc PIT. Candidate input count không phải số
score tính được; strict task/value giữ false/null và financial/cluster/research/
full-universe gates đóng. Sau trial50 cần review numeric templates/units/scope,
exact notes, DATE_ONLY publication/revisions/share events và công review trước100 mã.

## Legacy KBS trial50 — chỉ phục hồi/đối chiếu

Update08/10/2026: [paired benchmark](../../artifacts/reports/financial-source-benchmark-v1/report.md)
đề xuất CafeF detail primary candidate. Runner này vẫn là legacy KBS flow và còn
header/value blockers; chưa phải flow CafeF-first mới. Raw run07/10 đã cold-archived
theo owner cleanup; muốn verify/feedback phải [restore trước](README.md#financial-source-benchmark-và-retention--08102026).
Restore không gia hạn deadline hoặc reset epoch/counters. Report kết quả vẫn đọc
được ngay, không cần restore. Không rerun cấu hình cũ để kỳ vọng giải quyết lỗi kỳ.

Flow: preflight → annual/quarter theo chặng → history gaps → PDF/text chọn lọc →
coverage/task-input gaps → verify → feedback ZIP. Dữ liệu và logs nằm trên máy chạy;
không cần mở chat trong lúc job hoạt động. Không tạo scheduled task hoặc cloud job.

## Kết quả chạy thật hiện có

Ngày07/10/2026 đã chạy production epoch trong
`data/financial/crawl_50_live_20261007_v1`; xem
[report kết quả/log](../../artifacts/reports/financial-crawl-50-live-v1/report.md).
50 mã có300 base responses parse được, nhưng quarterly duplicate headers/history
payload thiếu Head và PDF gaps khiến collection PARTIAL. Không chạy lại lệnh fresh
run bên dưới với cùng epoch: registry sẽ yêu cầu parent gần nhất. Đọc/verify/feedback
run hiện có bằng `-Run data/financial/crawl_50_live_20261007_v1`. Nếu cần resume,
dùng output mới và `-ResumeFrom` path này theo quy tắc bên dưới; cached malformed
payload không tự sửa bằng resume. Cần sửa source/parser contract ở version được
kiểm thử trước một đợt acquisition bổ sung.

## Chuẩn bị và chạy

Mở PowerShell tại `C:\Projects\Intern\SourceCode-CafeF`, nhánh
`m1-cafef-primary-experiment`. Nếu `.venv` đã có Python ≥3.11 thì dùng môi trường đó:

```powershell
Set-Location C:\Projects\Intern\SourceCode-CafeF
git branch --show-current
.venv\Scripts\python.exe -m pip install -r configs/data/financial_crawl_requirements.txt
.\scripts\crawl_financial_trial.ps1 -Action doctor
.\scripts\crawl_financial_trial.ps1 -Action plan
```

Nếu chưa có `.venv`, tạo bằng `python -m venv .venv` trước khi cài dependency.
Doctor không gọi network. Structured dùng standard library; PDF text cần pypdf đã pin.
Trial v1 không yêu cầu Poppler/Windows OCR vì chỉ tạo scan-page queue. Có thể truyền
`-Python 'C:\path\to\python.exe'` khi launcher không chọn được runtime phù hợp.

Lệnh chạy thật (output mới, không được ghi đè):

```powershell
.\scripts\crawl_financial_trial.ps1 -Action run -Output data/financial/crawl_50_user_01 -ExecuteNetwork
```

`-ExecuteNetwork` cho phép các request công khai có giới hạn. Không có switch này thì
chỉ dùng cache; một run không cache sẽ báo thiếu, không giả kết quả đủ. Console in tiến
trình từng report/chặng, còn `work-log.jsonl` giữ log. Có thể không truyền `-Output`;
launcher tạo tên theo thời gian và in path, hãy lưu path đó.

Sau khi command kết thúc, kể cả exit 2/4 khi run đã sealed:

```powershell
.\scripts\crawl_financial_trial.ps1 -Action verify -Run data/financial/crawl_50_user_01
.\scripts\crawl_financial_trial.ps1 -Action feedback -Run data/financial/crawl_50_user_01
```

Feedback in đường dẫn ZIP mới dưới `artifacts/financial_crawler/`. Gửi ZIP này lại chat
để đánh giá kết quả và chọn công việc tiếp theo. ZIP có report/metrics/coverage/readiness/
review queue/config; không chứa raw JSON hoặc PDF. Giữ nguyên run local để truy raw khi
cần debug; feedback ZIP không thay thế full immutable run hoặc verifier của nó.

## Tiếp tục khi bị ngắt

Ctrl+C/crash không tạo full manifest; task và ledger đã sealed vẫn dùng được. Resume
từ **run gần nhất**, dùng output mới:

```powershell
.\scripts\crawl_financial_trial.ps1 -Action run -Output data/financial/crawl_50_user_02 -ResumeFrom data/financial/crawl_50_user_01 -ExecuteNetwork
.\scripts\crawl_financial_trial.ps1 -Action verify -Run data/financial/crawl_50_user_02
.\scripts\crawl_financial_trial.ps1 -Action feedback -Run data/financial/crawl_50_user_02
```

Không sửa config giữa các lần resume. Epoch registry bắt buộc parent gần nhất để các
counter không reset; OS lock ngăn hai process chạy cùng epoch, tự nhả khi process kết
thúc. Run mới chỉ đọc parent/task/ledger có checksum. Nếu integrity lỗi, giữ evidence
và gửi thông báo lỗi; không sửa raw/manifest để verify pass.

Hard-stop do 401/403/429/challenge được giữ qua resume; không còn request network mới.
Không đổi config/epoch/nguồn để né chặn. Cần xử lý quyền truy cập nguồn trước khi quyết
định trial khác. Thời hạn trial là **4 giờ từ START đầu tiên**, gồm thời gian tạm dừng;
resume không reset deadline/attempt/bytes/PDF caps. Sau deadline vẫn có thể đọc/replay
task hoàn chỉnh từ cache, nhưng không acquisition/extraction mới. Interrupted read
giữ byte reservation chưa xác nhận để budget được tính thận trọng.

Nếu run dừng vì chặng có dưới90% responses parse được: xem HTTP/payload errors trước,
không chạy tiếp các chặng khác một cách độc lập. Retry toàn request tối đa2 attempts
qua cả lineage; request hết attempts không tự reset. Missing/malformed raw đã cache
cần phân tích parser/vintage, không re-fetch để xóa evidence lỗi.

## Phạm vi và giới hạn

[Runtime config](../../configs/data/financial_crawl_50_trial_v1.json) pin
[plan 50 mã](../../configs/data/financial_crawl_50_plan_v1.json) và market snapshot SHA.
50 mã được thử theo năm chặng, mỗi chặng tối đa10; không sửa runner pilot cũ.

- Annual targets2021–2025; quarter targets2024–2025; score-input checklist2023–2025.
  FY2021 bổ sung làm năm nền cho asset comparison của F-score2023. KBS years là
  target coverage, không phải tham số buộc nguồn trả đủ history.
- 300 base logical requests; history thêm tối đa90; document branch thêm tối đa60;
  tổng450 logical requests,900 physical attempts, một request tại một thời điểm,
  interval≥2giây, timeout≤20giây. Counters gồm failures/retries và giữ qua resume.
- Tối đa20 physical PDF attempts, response50MB/tổng600MB, PDF250pages/tài liệu,
  1.000 text pages toàn lineage. Run tạo raw copies/images/ledger nên dung lượng đĩa
  không bằng bytes tải; preflight cần ít nhất2GB trống.
- Document selection mặc định12 mã: exact FPT/ACV URLs trước, sau đó ưu tiên annual
  gaps trong mẫu đề xuất8 Regular/2 Bank/1 Securities/1 Insurance để các financial
  mapping gaps không chiếm toàn bộ slots. CafeF listing giữ các annual consolidated vintages trong cap; không chọn
  latest rồi áp ngược lịch sử, không tự fallback sau access boundary.
- PDF parser chạy worker có timeout theo deadline còn lại. Scan/low-text pages vào
  review queue; **chưa tự OCR hoặc map numeric notes** trên50 mã. Selected-page OCR
  với exact-PDF templates dùng runner pilot sau khi chọn trang/review phù hợp.

Worker text giữ page reservation trước khi chạy; timeout/crash giữ reservation chưa
xác nhận qua resume để không vượt page cap. `trial_totals.text_pages` và
`reserved_text_pages` trong results phân biệt pages đã xử lý với pages dự phòng.

Company type trong plan là đề xuất. Regular numeric crosswalk chỉ tạo candidate khi
header nguồn có integer `BusinessType=1`; thiếu/mismatch metadata giữ raw và queue.
Đây là metadata hiện tại, không xác minh historical sector. Bank/Securities/Insurance
không nhận mapping Regular. Duplicate period headers không được tính coverage.

## Đọc kết quả

| File | Ý nghĩa |
|---|---|
| `report.md`, `results.json` | Collection/targets/counters/errors và việc còn phải làm |
| `period-coverage.csv` | Wire periods theo mã/year/quarter/report, tách mapped fields |
| `coverage.csv` | Missing core fields và candidate mappings |
| `feature-readiness.csv`, `.json` | Strict F/M/Z/EPS/P-E/P-B input dependencies, missing inputs và blockers |
| `review-queue.json`, `next-actions.json` | Ưu tiên sửa lỗi nguồn/header, templates, notes, publication/revisions |
| `candidates.jsonl`, `.csv`, `raw/`, `tasks/` | Raw values/header/provenance, text và task checkpoints |
| `ledger/`, `work-log.jsonl` | Journal sealed cho counters/reservations, log tiến trình |
| `manifest.json`, `resume-dependencies.json` | Integrity của run và transitive parents |

Các năm trên header không chứng minh đủ usable history; annual EPS không thay EPS TTM.
Financial-sector variants cần contract riêng. Data thu được là raw/candidates; task
ready/score/value giữ false/null đến khi semantics, ground truth, PIT/revisions và
valuation basis được nghiệm thu. Numeric accuracy và manual review minutes chưa đo
thì báo chưa đo, không biến thành0. Financial/cluster/research/full-universe gates đóng.

| Exit code | Cách xử lý |
|---|---|
| 0 | Command/collection hoàn thành trong scope; đọc coverage và readiness riêng |
| 1 | Config/path/integrity/epoch lỗi; giữ thông báo để chẩn đoán |
| 2 | PARTIAL/QUALITY_STOP/BUDGET_STOP; verify + feedback nếu đã có manifest |
| 3 | Doctor/runtime thiếu dependency |
| 4 | HARD_STOP nguồn; không retry/bypass |
| 130 | Bị ngắt; dùng resume từ output vừa chạy |

## Sau khi gửi kết quả

Đánh giá tỷ lệ annual/quarter responses, từng năm/quý có ba statement wire headers,
gaps/ambiguous headers, bytes/time/PDF/review cost. Tách raw coverage và mapped input
coverage, không gộp thành tỷ lệ hoàn thành financial. Engineering targets đạt chưa tự
mở100 mã; cần đóng template numeric QA và đo công review. Sau đó quyết định sửa nguồn/
parser, bổ sung exact notes/PIT/events hoặc mở trial100 với config/version được review.
