# Kế hoạch triển khai Financial Point-in-Time

## 1. Mục đích và trạng thái

Tài liệu này là kế hoạch thực thi cho workstream thu thập và chuẩn hóa báo cáo tài
chính point-in-time (PIT) của DELTA. Đối tượng đọc là project owner, researcher,
developer và automated coding/research agent. Mục tiêu là để một session mới có thể
xác định đúng stage, input, output, gate và điểm dừng mà không tự suy diễn methodology.

Trạng thái tại thời điểm lập kế hoạch:

```text
FINANCIAL_DATA                  = NOT_READY
FINANCIAL_PIT_POLICY_DESIGN_V1 = APPROVED_WITH_CONDITIONS
CAFEF_IMPLEMENTATION_MAPPING   = NOT_YET_APPROVED
FINANCIAL_FEATURES_ALLOWED     = false
NEXT_FINANCIAL_STAGE           = FIN-PIT-1A HISTORICAL TIMESTAMP FEASIBILITY PILOT
MANUAL_REVIEW_REQUIRED         = true
```

Workstream này độc lập với stage M2 market-only đang active. Nó không thay đổi kết
quả C8, không nâng `historical_identity_ready` hoặc `research_ready`, không mở
holdout/backtest và không cho phép thêm financial feature vào M2 hiện tại.

## 2. Kết quả mong muốn

Sau khi hoàn tất toàn bộ workstream, DELTA phải có khả năng:

1. Lưu raw financial evidence bất biến và truy ngược được đến tài liệu nguồn.
2. Xác định report identity, scope, audit status, kỳ kế toán và report vintage.
3. Chứng minh `published_at` và `available_at` đủ để ngăn look-ahead.
4. Phân biệt fact `instant`, standalone duration và year-to-date duration.
5. Chuẩn hóa fact bằng taxonomy được version hóa, không fuzzy-promote.
6. Chọn đúng report vintage tại mỗi `decision_at`.
7. Quarantine mọi trường hợp thiếu hoặc mâu thuẫn evidence.
8. Chỉ mở từng financial feature sau một approval riêng về taxonomy, formula và PIT.

## 3. Ngoài phạm vi

Kế hoạch này không cho phép:

- crawl số lượng lớn trước khi pilot gate PASS/PARTIAL có phạm vi rõ ràng;
- dùng CafeF API summary làm canonical source duy nhất;
- suy `available_at` từ `period_end`, deadline pháp luật hoặc tên file;
- coi mọi Q2/Q3 là standalone hoặc mọi Q2/Q3 là YTD;
- overwrite báo cáo cũ khi xuất hiện file/value mới;
- average hai nguồn hoặc dùng source priority chưa được phê duyệt;
- tự động map taxonomy bằng fuzzy label;
- tính EPS lịch sử từ current outstanding shares;
- bật financial feature, clustering selection hoặc backtest trong pilot;
- bypass login, CAPTCHA, paywall, anti-bot hoặc access control;
- triển khai nhiều FIN-PIT stage trong một session nếu owner không yêu cầu rõ.

## 4. Nguồn quy chuẩn và thứ tự ưu tiên evidence

### 4.1. Nguồn quy chuẩn

- `docs/DATA_CONTRACT.md`: timing, report identity, immutable vintage và reconciliation.
- `docs/METHODOLOGY.md`: PIT, restatement và feature approval.
- `docs/DECISIONS.md`: financial PIT/revision-aware và risk acceptance hiện hành.
- `docs/crawl/sources/CAFEF.md`: semantics CafeF đã quan sát và blocker còn mở.
- `src/delta_t1/schemas/financial_reports.json`: contract report hiện tại.
- `src/delta_t1/schemas/financial_facts.json`: contract fact hiện tại.
- `src/delta_t1/features/point_in_time.py`: selector report vintage fail-closed.
- `src/delta_t1/features/fundamentals.py`: financial feature gate hiện tại.

Tài liệu bên ngoài phải ưu tiên nguồn chính thức và kiểm tra tình trạng hiệu lực tại
ngày freeze policy:

- [Thông tư 96/2020/TT-BTC](https://vbpl.vn/botaichinh/Pages/vbpq-thuoctinh.aspx?ItemID=146048)
  và các văn bản sửa đổi hiện hành về công bố thông tin trên thị trường chứng khoán;
- [Thông tư 08/2026/TT-BTC](https://vbpl.vn/botaichinh/Pages/vbpq-thuoctinh.aspx?ItemID=186989&dvid=281)
  trong chuỗi sửa đổi hiện hành tại thời điểm lập kế hoạch;
- [VAS 27 trong Quyết định 12/2005/QĐ-BTC](https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=18466);
- [Thông tư 20/2006/TT-BTC](https://vbpl.vn/botaichinh/Pages/vbpq-print.aspx?ItemID=16244)
  hướng dẫn báo cáo tài chính giữa niên độ;
- [IAS 34](https://www.ifrs.org/issued-standards/list-of-standards/ias-34-interim-financial-reporting/)
  chỉ dùng làm nguồn đối chiếu khái niệm hoặc khi doanh nghiệp tuyên bố áp dụng IFRS.

Văn bản quy định deadline không tự chứng minh `available_at` của một report cụ thể.
Timestamp thực tế của disclosure/document vẫn là evidence bắt buộc.

### 4.2. Thứ tự ưu tiên evidence theo mục đích

| Mục đích | Nguồn ưu tiên | Vai trò CafeF |
|---|---|---|
| Fact candidate | PDF gốc và bảng trong report | API summary hỗ trợ discovery/đối chiếu |
| Kỳ và duration | Tiêu đề cột/nội dung PDF | Nhãn `Qn-YYYY` chỉ là candidate |
| Scope | PDF/disclosure chính thức | Tiêu đề tài liệu là candidate |
| Audit status | Báo cáo kiểm toán/soát xét trong PDF | Tiêu đề là candidate |
| `published_at`/`available_at` | Cổng công bố chính thức có timestamp | Timestamp CafeF phải được kiểm chứng |
| Revision/restatement | Disclosure quan hệ thay thế/sửa đổi + document hash | Dùng để phát hiện candidate, không tự kết luận |
| Taxonomy | Mã số, nhãn và context trong PDF/chế độ kế toán | Label API là candidate |

Nếu không có historical timestamp đáng tin cậy, có thể dùng `first_observed_at` làm
`available_at` bảo thủ cho sử dụng prospective. Report đó không được backdate vào
snapshot trước lần quan sát đầu tiên.

## 5. Pilot universe và sampling contract

Pilot đề xuất:

| Thành phần | Phạm vi |
|---|---|
| Securities | `FPT`, `VNM`, `PVS`, `ACV` |
| Exchange coverage | HOSE, HNX, UPCOM |
| Kỳ | Tối đa 8 quý gần nhất có đủ evidence tại ngày freeze pilot |
| CafeF modes | `QUY`, `LUYKE`, `NAM` |
| Statements | KQKD, CĐKT, LCTT trực tiếp/gián tiếp nếu có |
| Scope | Hợp nhất và riêng lẻ nếu cùng tồn tại |
| Assurance | Unaudited, reviewed và audited nếu mẫu có sẵn |

Sampling phải ưu tiên có ít nhất:

- một Q1, Q2, Q3 và Q4/report năm;
- một report bán niên được soát xét;
- một doanh nghiệp có cả consolidated và separate report;
- một trường hợp document/value thay đổi nếu quan sát được;
- một PDF text-based và một PDF scan nếu nguồn thực tế có cả hai.

Thiếu một loại mẫu phải được ghi là coverage limitation; không tạo placeholder result.

## 6. Data zones và trạng thái record

```text
RAW_IMMUTABLE
    ↓ parse có provenance
CANDIDATE_PIT_UNRESOLVED
    ↓ semantic/linkage/timing checks
VERIFIED_CANDIDATE hoặc QUARANTINED
    ↓ policy + schema + reconciliation gates
CANONICAL_FINANCIAL_PIT
    ↓ feature-specific approval riêng
FINANCIAL_FEATURE_READY
```

Pilot FIN-PIT-1 chỉ được tạo ba trạng thái đầu. Không tạo
`CANONICAL_FINANCIAL_PIT` hoặc `FINANCIAL_FEATURE_READY`.

Mỗi raw artifact tối thiểu phải có:

- source/provider;
- source URL/request parameters không chứa secret;
- retrieval status và content type;
- `fetched_at` timezone-aware;
- SHA-256;
- byte size;
- immutable relative path;
- collector/config/code version;
- parent artifact/run ID;
- access/result classification;
- lỗi parse riêng, không làm mất raw evidence.

## 7. Kế hoạch theo stage

Mỗi stage dưới đây là một đơn vị thực thi độc lập. Agent phải dừng sau đúng stage,
self-review và cập nhật handoff. Không tự động chuyển sang stage tiếp theo.

### 7.0. Terminal execution contract cho mọi stage

Không mặc định rằng project owner phải tự chạy mọi command. Mỗi prompt/session phải
phân loại rõ một trong ba execution mode trước khi thực thi:

1. `AI_EXECUTES`: agent tự chạy command, test, bounded acquisition và verifier trong
   session khi thời lượng, quyền truy cập và sandbox cho phép.
2. `OWNER_EXECUTES`: agent hoàn tất implementation/preflight, sau đó bàn giao command
   để owner chạy local; phù hợp với long-running crawl, multi-shard job, tác vụ cần
   theo dõi ngoài session hoặc khi owner yêu cầu tự chạy.
3. `HYBRID`: agent chạy implementation, unit/integration tests, dry-run và bounded
   preflight; owner chỉ chạy real acquisition dài; agent đọc output/artifact ở session
   tiếp theo để verify và kết luận gate.

Mode khuyến nghị theo stage:

| Stage | Mode mặc định | Ghi chú |
|---|---|---|
| FIN-PIT-0 | `AI_EXECUTES` | Documentation-only |
| FIN-PIT-1A | `AI_EXECUTES` hoặc `HYBRID` | AI có thể chạy pilot nhỏ; owner chạy nếu discovery kéo dài |
| FIN-PIT-1 | `HYBRID` | AI implement/test/dry-run; bounded real pilot có thể do AI hoặc owner chạy tùy thời lượng/quyền |
| FIN-PIT-2 | `AI_EXECUTES` | Chủ yếu offline parse/linkage trên artifact FIN-PIT-1 |
| FIN-PIT-3 | `AI_EXECUTES` | Offline evidence review; dừng ở manual decision nếu cần |
| FIN-PIT-4 | `AI_EXECUTES` | Analysis/design; thay schema vẫn cần approval trước implementation |
| FIN-PIT-5 | `AI_EXECUTES` | Code, tests và offline verifier trên pilot |
| FIN-PIT-6 | `HYBRID` | AI chuẩn bị; owner có thể chạy representative acquisition dài |
| FIN-PIT-7 | `OWNER_EXECUTES` hoặc `HYBRID` | Scaled/long-running acquisition chạy local, không continuously poll |
| FIN-PIT-8 | `AI_EXECUTES` | Approval/implementation từng feature, không tự mở crawl |

Mỗi prompt thực thi stage phải yêu cầu agent cung cấp mục `TERMINAL RUNBOOK` kể cả khi
agent đã tự chạy command. Runbook phải bao gồm:

- shell và working directory chính xác;
- prerequisite/preflight commands;
- dry-run command;
- real execution command nếu stage cho phép;
- verify/resume command;
- targeted tests và repository gates cần chạy;
- expected artifact paths;
- expected success markers/exit code;
- dấu hiệu `PARTIAL`, `BLOCKED` hoặc `FAIL`;
- cách dừng an toàn và cách resume;
- cảnh báo command nào có network hoặc có thể chạy lâu;
- không chứa secret, private token hoặc placeholder bị hiểu nhầm là kết quả thật.

Command phải là PowerShell copy-paste được từ workspace root. Agent không được đưa tên
script/flag giả định trước khi implementation thực tế tồn tại và `--help`/test đã xác
minh. Nếu command chưa tồn tại, agent phải implement và verify trước khi bàn giao.

Nếu owner chạy command, agent phải yêu cầu owner giữ nguyên toàn bộ output artifact và
gửi lại tối thiểu:

- command thực tế đã chạy;
- exit code;
- stdout/stderr hoặc log path;
- run/artifact directory;
- `manifest.json`/`gate.json`/checksum result nếu được sinh;
- thời điểm bắt đầu/kết thúc;
- mọi interruption, retry hoặc manual modification.

Ở session verify tiếp theo, agent phải đọc artifact/log thay vì yêu cầu owner tự diễn
giải. Agent phải mô tả bằng ngôn ngữ dễ hiểu:

1. command đã làm gì;
2. kết quả nào được tạo;
3. tiêu chí nào PASS/PARTIAL/BLOCKED/FAIL;
4. dữ liệu nào chưa thu được hoặc bị quarantine;
5. có được phép sang stage tiếp theo hay phải dừng;
6. exact next command chỉ khi next stage đã được owner yêu cầu.

Mẫu bắt buộc để chèn vào mọi prompt stage:

```text
TERMINAL EXECUTION REQUIREMENTS

1. Trước khi chạy, xác định EXECUTION_MODE = AI_EXECUTES | OWNER_EXECUTES | HYBRID
   và giải thích ngắn gọn lý do.
2. Nếu AI_EXECUTES, hãy tự chạy các command phù hợp và vẫn cung cấp lại exact commands
   đã chạy, exit codes, output/artifact paths và kết quả.
3. Nếu OWNER_EXECUTES hoặc HYBRID, sau khi implementation/preflight pass hãy cung cấp
   một TERMINAL RUNBOOK PowerShell copy-paste được từ workspace root, theo đúng thứ tự:
   prerequisite → dry-run → execute → verify → resume (nếu có) → tests.
4. Với từng command, ghi rõ:
   - mục đích;
   - có gọi network hay không;
   - thời lượng dự kiến ở mức định tính (ngắn/có thể dài), không bịa ETA;
   - output/artifact dự kiến;
   - dấu hiệu thành công;
   - lỗi thường gặp và cách dừng/resume an toàn.
5. Chỉ cung cấp command đã được xác minh từ code/CLI thực tế; không phát minh script,
   flag hoặc placeholder output.
6. Sau khi chạy xong, mô tả kết quả dễ hiểu và kết luận stage bằng evidence:
   PASS | PARTIAL | BLOCKED | FAIL. Không coi exit code 0 là đủ nếu gate/artifact fail.
7. Nếu owner phải chạy command ngoài session, hãy nêu chính xác những log/artifact
   owner cần gửi lại để AI verify; không yêu cầu owner tự phán đoán kết quả khoa học.
8. Long-running crawl phải chạy local, không continuously poll và không tự động mở
   stage kế tiếp sau khi command hoàn tất.
```

### FIN-PIT-0 — Freeze kế hoạch và policy baseline

Mục tiêu:

- khóa phạm vi, terminology, source hierarchy và checklist review;
- không thu thập network và không thay schema/code runtime.

Output:

- kế hoạch này;
- link từ documentation index;
- changelog entry;
- không có data artifact.

Gate:

```text
PASS khi tài liệu nhất quán với DATA_CONTRACT/METHODOLOGY/DECISIONS
và không ngầm approve CafeF implementation mapping.
```



### FIN-PIT-1A — Historical timestamp feasibility pilot

> **Bổ sung từ GPT — mục đích:** kiểm tra sớm xem historical financial data có thực sự có khả năng trở thành PIT-ready hay không trước khi đầu tư nhiều công sức vào crawl, parse và taxonomy. Stage này không thay thế FIN-PIT-1..8 và không tự approve bất kỳ financial feature nào.

#### Mục tiêu

- kiểm tra trên mẫu nhỏ xem có thể tìm được bằng chứng lịch sử đáng tin cậy cho `published_at` và `available_at`;
- xác định nguồn nào thực sự cung cấp timestamp có thể dùng để đặt report lên historical timeline;
- phát hiện sớm trường hợp PDF/fact có tồn tại nhưng không thể chứng minh khi nào thị trường đã biết thông tin;
- tránh việc crawl/parse quy mô lớn rồi mới phát hiện dữ liệu không thể dùng cho historical PIT.

#### Phạm vi pilot

Dùng chính pilot universe đã freeze ở Mục 5, nhưng chỉ chọn một tập report đại diện theo thời gian, ví dụ:

- đủ HOSE, HNX, UPCOM;
- đủ Q1, Q2, Q3, Q4/năm;
- có report hợp nhất và riêng lẻ nếu khả dụng;
- ưu tiên nhiều năm để kiểm tra tính recoverable của historical timestamp, không chỉ dữ liệu gần hiện tại.

Không yêu cầu parse toàn bộ financial facts tại stage này. Trọng tâm là **timing evidence**.

#### Trường cần kiểm tra cho mỗi report

Tối thiểu:

- `ticker`;
- `report_period`;
- `document_found`;
- `official_disclosure_found`;
- `published_at_candidate`;
- `published_at_verified`;
- `available_at_candidate`;
- `available_at_verified`;
- `timestamp_source`;
- `timezone_known`;
- `revision_evidence_found`;
- `pit_timing_usable`;
- `failure_reason`.

#### Nguyên tắc bắt buộc

- không suy `available_at` từ `period_end`;
- không suy từ deadline pháp luật;
- không suy từ tên file nếu semantics chưa được nguồn xác nhận;
- không dùng timestamp hiện tại để backdate lịch sử;
- nếu chỉ biết `first_observed_at`, report chỉ được dùng prospective từ thời điểm quan sát đó trở đi;
- thiếu timing evidence phải đánh dấu `PIT timing unresolved`, không tự nội suy.

#### Output gợi ý

```text
artifacts/financial_pit/fin-pit-1a-timing-feasibility-v1/
    timing_feasibility.csv
    timing_evidence.jsonl
    timing_coverage_report.json
    gate.json
```

Ví dụ `timing_feasibility.csv`:

```text
ticker,period,document_found,published_at_verified,available_at_verified,pit_timing_usable
FPT,2024Q2,true,true,true,true
VNM,2024Q2,true,true,true,true
PVS,2024Q2,true,true,true,true
ACV,2024Q2,true,false,false,false
```

#### Gate

Không freeze một ngưỡng phần trăm tùy ý nếu chưa có methodology decision riêng. Gate phải dựa vào tính chất evidence:

- `PASS`: historical timestamp có thể được xác minh ổn định trên phạm vi pilot và có nguồn/semantics đủ rõ để tiếp tục;
- `PARTIAL`: chỉ một số exchange/kỳ/source pattern đủ timing evidence; phạm vi downstream phải bị giới hạn tương ứng;
- `BLOCKED`: report/document có thể tồn tại nhưng historical timing evidence không thể recover đủ để dùng PIT;
- `FAIL`: timestamp mapping tạo look-ahead hoặc không tái lập được.

`PASS` của FIN-PIT-1A chỉ nói **timing feasibility có cơ sở**. Nó không chứng minh period semantics, taxonomy, revision hay fact mapping đã đúng.

#### FIN-PIT-1A-R1 — HNX/UPCOM timestamp semantics remediation

> **Mục đích:** kiểm tra xem timestamp đã quan sát được trên HNX/UPCOM có đủ semantics để
> dùng trực tiếp làm historical `available_at` hay không.

##### Bối cảnh mở R1

FIN-PIT-1A ban đầu đã thu được HNX/UPCOM document và civil-time candidate, nhưng chưa
chứng minh được hai điều kiện bắt buộc:

1. timestamp dùng timezone/epoch nào;
2. timestamp đó có thực sự đại diện cho first public availability hay chỉ là
   record/upload/update/approval time.

R1 vì vậy không crawl financial fact, không canonicalize và không chạy FIN-PIT-1.
Phạm vi khóa ở đúng 12 mẫu hiện hành:

- PVS/HNX: 4 mẫu;
- ACV/UPCOM: 8 mẫu.

##### Câu hỏi cần trả lời

R1 chỉ được promote khi official HNX/CIMS evidence chứng minh đồng thời:

- source-specific timezone hoặc epoch standard của timestamp field;
- field là first public availability, không chỉ record/upload/update time.

Giờ pháp lý quốc gia, deadline công bố và vị trí trụ sở chỉ là supporting evidence,
không tự động chứng minh timezone hay semantics của một field cụ thể.

##### Kết quả R1 — `PARTIAL`

Kết quả thực thi ngày 30/09/2026:

- field identity đã được xác định;
- public context của CIMS/HNX đã được xác nhận;
- UTC+7 của Việt Nam chỉ được ghi nhận là `SUPPORTING_ONLY`;
- chưa có HNX-specific evidence xác nhận timezone của `PUBLICTIME` / “Ngày đăng tin”;
- chưa chứng minh field đó là first-public timestamp;
- 0/12 mẫu HNX/UPCOM được mở khóa.

Kết luận:

```text
R1_STATUS = PARTIAL
HNX_SPECIFIC_TIMEZONE = UNRESOLVED
FIRST_PUBLIC_SEMANTICS = UNRESOLVED
USABLE_HNX_UPCOM_ROWS = 0/12
```

##### Vì sao phải mở R2

R1 cho thấy vấn đề không nằm ở việc thiếu field timestamp, mà nằm ở thiếu **authoritative
field semantics**. Vì vậy R2 chuyển trọng tâm sang tài liệu chính thức HNX/VNX/SSC để
tìm bằng chứng trực tiếp cho timezone, first-public semantics và revision behavior.


#### FIN-PIT-1A-R2 — HNX authoritative timestamp evidence

> **Mục đích:** tìm authoritative evidence từ HNX/VNX/SSC cho các blocker mà R1 chưa
> giải quyết được.

##### Phạm vi

R2 chỉ tìm bằng chứng cho ba câu hỏi:

1. timezone/epoch cụ thể của `PUBLICTIME` / “Ngày đăng tin”;
2. quan hệ trực tiếp giữa field này và first-public availability;
3. behavior khi correction/replacement/withdrawal/supplement:
   - timestamp có bị overwrite hay không;
   - record cũ có được giữ hay không;
   - revision có version/timestamp riêng hay không.

Trước network execution, R2 freeze:

- 10 exact discovery queries;
- tối đa 12 candidate/direct fetches;
- official-domain allowlist;
- single-threaded one-attempt requests;
- no redirect;
- exact 12 PVS/ACV samples.

Search snippet chỉ dùng để discovery. Generic Vietnam timezone, legacy IDS behavior và
empirical alignment không được promote thành HNX timing evidence.

##### Kết quả R2 — `PARTIAL`

Kết quả ngày 30/09/2026:

- acquisition v3 có 8 direct attempts;
- 6 requests thành công;
- 2 fail-closed errors;
- tổng raw evidence 4.268.849 bytes;
- final artifact v6 verify/replay offline từ v3 checksums;
- replay dùng 0 network request mới;
- HNX public dissemination context được xác nhận;
- field identity được xác nhận;
- official SSC IDS Plus guide cho thấy approval state, resend và overwrite behavior;
- HNX-hosted correction material được quan sát.

Tuy nhiên:

- chưa có tài liệu HNX ràng buộc field với timezone cụ thể;
- chưa có tài liệu HNX chứng minh field là first-public accessibility;
- chưa có rule chính thức mô tả revision/version lineage;
- approval/resend/overwrite evidence chỉ được xếp `SUPPORTING_ONLY`;
- 0/12 mẫu được mở khóa.

Kết luận:

```text
R2_STATUS = PARTIAL
AUTHORITATIVE_TIMEZONE = NOT_FOUND
AUTHORITATIVE_FIRST_PUBLIC_SEMANTICS = NOT_FOUND
AUTHORITATIVE_REVISION_VERSION_RULE = NOT_FOUND
USABLE_HNX_UPCOM_ROWS = 0/12
```

##### Vì sao phải mở R3

Sau R2, exact HNX timestamp contract vẫn không thể chứng minh trực tiếp từ tài liệu
official. R3 vì vậy thử một hướng bảo thủ khác: không cần dựa vào semantics của
`PUBLICTIME`, mà tìm **external historical evidence** cho biết một exact document đã tồn
tại công khai không muộn hơn một thời điểm lịch sử nào đó.


#### FIN-PIT-1A-R3 — Alternative conservative availability evidence

> **Mục đích:** kiểm tra xem official mirror hoặc historical web archive có thể tạo một
> conservative upper bound cho historical availability hay không.

##### Phạm vi

R3 giữ nguyên đúng 12 PVS/ACV samples và chỉ kiểm tra hai pattern:

1. exact-document official mirror;
2. historical archive capture.

Archive timestamp chỉ có thể được xem là conservative upper-bound candidate nếu:

- archive payload được lấy thành công;
- payload có thể đối chiếu với current HNX document;
- SHA-256/document identity đủ mạnh để chứng minh cùng tài liệu;
- methodology approval riêng chấp nhận cách sử dụng archive timestamp.

Các nguồn sau không được promote:

- search snippet;
- filename;
- period end;
- deadline pháp luật;
- current observation time;
- HNX civil-time field chưa verify.

##### Kết quả R3 — `BLOCKED`

Kết quả ngày 30/09/2026:

- exact mirror discovery chạy 12 query, 0 result;
- Wayback CDX gặp HTTP 429 ngay request đầu và dừng fail-closed;
- Wayback Availability API gặp HTTP 429 ngay request đầu và dừng fail-closed;
- Common Crawl chạy đủ 12 exact collection-index attempts nhưng không nhận response
  usable;
- không được diễn giải access/service failure thành archive absence;
- không có archive payload để hash-verify.

Coverage usable:

```text
HNX   = 0/4
UPCOM = 0/8
TOTAL = 0/12
```

Artifact tổng hợp offline:

```text
artifacts/financial_pit/fin-pit-1a-r3-alternative-availability-final-v1/
```

Kết luận:

```text
R3_STATUS = BLOCKED
OFFICIAL_MIRROR_EVIDENCE = 0
ARCHIVE_HASH_VERIFIED_PAYLOAD = 0
USABLE_HNX_UPCOM_ROWS = 0/12
```

##### Vì sao phải mở R4

R3 cho thấy public archive/mirror không cung cấp được historical availability evidence
đủ mạnh. Vì vậy R4 thử hai đường khác:

1. khai thác sâu hơn public HNX historical endpoints để tìm hidden metadata;
2. đánh giá licensed/commercial provider có field timing tốt hơn hay không.


#### FIN-PIT-1A-R4 — HNX historical API + licensed-provider qualification

> **Mục đích:** kiểm tra xem public HNX endpoints hoặc licensed provider có thể cung cấp
> historical timing contract mà R1–R3 không tìm được hay không.

##### Track A — Public HNX historical API

R4 chạy 24/24 bounded POST requests cho đúng 12 PVS/ACV samples:

- 12 request `PopupTinCongBoDetail`;
- 12 request `ArticlesFileAttach`.

Các response HTTP 200 chỉ chứa:

- rendered title/detail;
- HTML content;
- attachment filename/path.

Không có:

- `record_id`;
- `document_id`;
- `created_at`;
- `published_at`;
- `updated_at`;
- `revision_id`;
- timezone;
- revision/version lineage;
- field semantics đủ để tạo historical PIT contract.

Kết luận track A:

```text
HNX_PUBLIC_API_METADATA_SUFFICIENT = false
```

##### Track B — Licensed/commercial provider qualification

R4 đánh giá bốn provider candidates:

1. FiinGroup/FiinPro;
2. VietstockFinance;
3. FinancialFilings;
4. WiData.

FiinGroup/FiinPro là candidate tốt nhất vì official schema có:

- `Ticker`;
- `YearReport`;
- `LengthReport`;
- `ReportFormTypeCode`;
- `SourceName`;
- `PublicDate`;
- `Status`;
- `CreateDate`;
- `UpdateDate`.

Tuy nhiên chưa đủ qualification vì:

- `PublicDate` chỉ là date-only;
- chưa chứng minh `PublicDate` là official first-public date;
- `CreateDate`/`UpdateDate`/`Status` có thể chỉ phản ánh provider record lifecycle;
- chưa có stable `revision_id`;
- chưa có official PDF identity/hash contract;
- chưa có credential/license để chạy licensed API;
- chưa có crosswalk provider report ↔ official document ↔ official disclosure.

Các provider khác:

- VietstockFinance: chưa có field-level publication/revision contract;
- FinancialFilings: official fetch bị HTTP 403;
- WiData: chưa tìm thấy official field-level schema trong frozen discovery.

##### Kết quả R4 — `BLOCKED`

Gate ngày 30/09/2026:

```text
HNX_SAMPLES_USABLE = 0/12
PROVIDERS_QUALIFIED = 0/4
LICENSED_API_CALLS = 0
OFFICIAL_CROSSWALKS = 0
FIINGROUP_STATUS = PROMISING_BUT_NOT_QUALIFIED
R4_STATUS = BLOCKED
```

Muốn mở lại full timestamp qualification cho FiinGroup cần authorized trial/license và
exact 16-sample crosswalk gồm:

- 4 HOSE controls;
- 12 HNX/UPCOM samples.

Artifact final:

```text
artifacts/financial_pit/fin-pit-1a-r4-historical-qualification-final-v1/
```


#### FIN-PIT-1A-R1 → R4 — Tổng hợp nguyên nhân chưa thể chạy FIN-PIT-1

R1–R4 không cho thấy financial document của HNX/UPCOM không tồn tại. Ngược lại, project
đã tìm được document, disclosure page, attachment và civil-time candidate. Blocker nằm ở
việc **exact historical timestamp contract** chưa đủ evidence.

Tổng hợp:

| Stage | Câu hỏi chính | Kết quả | Blocker còn lại |
|---|---|---|---|
| R1 | Timestamp HNX/UPCOM có timezone + first-public semantics rõ không? | `PARTIAL` | Chưa có HNX-specific timezone và first-public semantics |
| R2 | Có authoritative HNX/VNX/SSC documentation giải thích field/revision không? | `PARTIAL` | Không có tài liệu ràng buộc timezone, first-public accessibility, revision-version rule |
| R3 | Mirror/archive có chứng minh historical availability không? | `BLOCKED` | Không có payload hash-verified usable |
| R4 | Public HNX API hoặc licensed provider có đủ metadata không? | `BLOCKED` | Public API thiếu lifecycle metadata; provider chưa qualified |

Trạng thái sau R4:

```text
EXACT_HISTORICAL_TIMESTAMP_PIT_HNX_UPCOM = BLOCKED
HNX_UPCOM_DOCUMENT_EXISTENCE = OBSERVED
HNX_UPCOM_PUBLIC_DISCLOSURE_CONTEXT = OBSERVED
HNX_UPCOM_DATE_CANDIDATE = OBSERVED
HNX_UPCOM_EXACT_AVAILABLE_AT = UNRESOLVED
FIN_PIT_1_ALLOWED_FOR_HNX_UPCOM = false
```

Nếu tiếp tục yêu cầu exact `YYYY-MM-DD hh:mm:ss + timezone + first-public semantics` cho
mọi HNX/UPCOM report thì project có nguy cơ mất toàn bộ HNX/UPCOM financial coverage,
trong khi M1/M2 cần universe gồm HOSE, HNX và UPCOM.

Vì vậy cần một remediation mới không giả định giờ/phút/giây, nhưng vẫn giữ nguyên
nguyên tắc chống look-ahead.


#### FIN-PIT-1A-R5 — Conservative date-level PIT qualification

> **Bổ sung từ GPT — mục đích:** kiểm tra xem historical HNX/UPCOM có thể được sử dụng ở
> độ phân giải **ngày** thay vì exact timestamp hay không. R5 không làm yếu nguyên tắc
> PIT: report chỉ được promote nếu ngày công bố ra công chúng có evidence đủ mạnh; nếu
> chỉ biết ngày mà không biết giờ, report được dùng từ ngày giao dịch kế tiếp để tránh
> intraday look-ahead.

##### 1. Mục tiêu

R5 trả lời câu hỏi hẹp hơn R1–R4:

> Với một HNX/UPCOM report cụ thể, có đủ evidence để chứng minh `YYYY-MM-DD` là ngày
> report/disclosure đã được công khai cho thị trường hay không?

R5 **không yêu cầu** phải chứng minh:

- exact hour/minute/second;
- exact UTC offset cho civil-time field;
- exact intraday first-public instant.

R5 vẫn **bắt buộc** chứng minh:

- đúng report/document;
- đúng ticker/period/scope;
- ngày candidate gắn với public disclosure, không phải period end/deadline/provider ingest;
- revision không được back-propagate vào quá khứ;
- document/value mới không overwrite historical vintage trong canonical timeline.

##### 2. Lý do mở R5

R1–R4 đã cho thấy:

```text
Exact timestamp semantics
        ↓
không đủ authoritative evidence
        ↓
HNX/UPCOM = 0/12 exact-PIT usable
```

Nhưng project dùng monthly/month-end snapshots. Vì vậy exact intraday precision có thể
không cần thiết nếu có thể chứng minh một **official publication date** và áp dụng một
eligibility rule bảo thủ.

R5 không phủ nhận kết quả R1–R4. Nó tạo một contract mới yếu hơn về độ phân giải thời
gian nhưng vẫn fail-closed về look-ahead.

##### 3. Input bắt buộc

R5 phải tái sử dụng immutable artifact đã có, không crawl lại từ đầu nếu không cần:

- FIN-PIT-1A base artifacts;
- R1 artifact;
- R2 artifact;
- R3 artifact;
- R4 artifact;
- exact 12 PVS/ACV samples hiện hành;
- HNX/UPCOM disclosure page và attachment đã thu được;
- provider candidate metadata đã discovery;
- checksum/hash đã có.

Nếu mở FiinGroup qualification bằng authorized trial/license, có thể bổ sung exact
16-sample crosswalk:

- 4 HOSE controls;
- 4 PVS/HNX samples;
- 8 ACV/UPCOM samples.

##### 4. Khái niệm mới

R5 tách ba khái niệm:

```text
period_end
    = ngày kết thúc kỳ kế toán

publication_date
    = ngày report/disclosure được công khai ra thị trường

eligible_from
    = ngày đầu tiên project cho phép dùng report trong historical snapshot
```

Ví dụ:

```text
period_end       = 2024-06-30
publication_date = 2024-07-29
eligible_from    = next_trading_day(2024-07-29)
```

Không được suy `publication_date` từ `period_end`, deadline pháp luật hoặc filename.

##### 5. Conservative D+1 rule

Nếu `publication_date = D` đã được verify nhưng intraday timestamp chưa đủ evidence:

```text
eligible_from = next_trading_day(D)
```

Quy tắc:

- snapshot trước `eligible_from` → không được thấy report;
- snapshot tại hoặc sau `eligible_from` → report có thể eligible nếu các semantic/revision
  gate khác đều pass;
- nếu publication date trùng snapshot date → không dùng report trong snapshot đó;
- weekend/holiday phải dùng canonical trading calendar để tìm next trading day;
- không cộng cơ học `D + 1 calendar day`.

Ví dụ:

```text
Publication date = Friday 2024-07-26
Monday 2024-07-29 = next open session

eligible_from = 2024-07-29
```

##### 6. Điều kiện để một publication date được verify

Một date candidate chỉ được promote nếu có evidence đủ mạnh cho **public disclosure
date**.

Evidence ưu tiên:

1. official HNX/CIMS/UPCOM disclosure page gắn trực tiếp với exact document/report;
2. official document index hoặc official metadata mô tả đây là ngày đăng/công bố;
3. licensed provider field có semantics chính thức và crosswalk được với official
   disclosure/document;
4. independent official mirror nếu exact document identity được verify.

Không đủ để promote nếu chỉ có:

- report period;
- deadline pháp luật;
- filename date;
- PDF creation metadata không có source semantics;
- search snippet;
- current observation time;
- provider `CreateDate`/`UpdateDate` chưa chứng minh;
- date candidate không link được với exact document.

##### 7. FiinGroup qualification trong R5

R5 có thể hạ mục tiêu qualification của FiinGroup từ:

```text
exact available_at timestamp provider
```

xuống:

```text
qualified historical publication_date provider
```

Qualification Level 1 — đủ cho date-level PIT:

- `PublicDate` có official field definition;
- definition chứng minh đây là public disclosure/report publication date;
- crosswalk đúng ticker/period/report form/source;
- provider date không sớm hơn official public evidence trong HOSE controls;
- HNX/UPCOM samples link được với official document/disclosure;
- missing/mismatch bị quarantine;
- revision cases không được backfill.

Qualification Level 2 — exact timestamp PIT:

- timezone;
- first-public timestamp;
- revision/version lineage;
- exact lifecycle semantics.

R5 chỉ cần Level 1 để thử D+1 methodology. Level 2 vẫn deferred.

##### 8. Revision/restatement rule ở date-level PIT

Nếu nhiều document cùng ticker/period/scope xuất hiện ở các publication date khác nhau:

```text
Vintage A:
publication_date = D1
hash = AAA

Vintage B:
publication_date = D2
hash = BBB
```

thì:

```text
A eligible từ next_trading_day(D1)
B eligible từ next_trading_day(D2)
```

Vintage B không được overwrite hoặc back-propagate vào snapshot trước D2.

Nếu quan hệ correction/replacement chưa rõ:

```text
revision_relation = UNKNOWN
```

thì record liên quan phải quarantine hoặc giữ riêng từng immutable vintage cho tới khi
policy được approve.

##### 9. Output gợi ý

```text
artifacts/financial_pit/fin-pit-1a-r5-date-level-pit-v1/
    date_level_candidates.csv
    publication_date_evidence.jsonl
    official_document_crosswalk.jsonl
    provider_crosswalk.jsonl
    revision_candidates.jsonl
    quarantine.jsonl
    date_level_coverage_report.json
    gate.json
```

Ví dụ `date_level_candidates.csv`:

```text
ticker,period,exchange,publication_date,date_verified,eligible_from,pit_date_usable,reason
PVS,2024Q2,HNX,2024-07-29,true,2024-07-30,true,official_publication_date_verified
ACV,2024Q2,UPCOM,2024-08-30,true,2024-09-04,true,next_open_session_after_holiday
PVS,2023Q3,HNX,,false,,false,public_disclosure_date_unresolved
```

##### 10. Coverage report bắt buộc

R5 phải báo riêng:

- HNX date-verified coverage;
- UPCOM date-verified coverage;
- provider-assisted coverage;
- official-only coverage;
- unresolved coverage;
- revision-conflict count;
- number of rows that become usable only because of D+1 rule.

Không được chỉ báo aggregate percentage.

##### 11. Gate

`PASS`:

- publication-date semantics được chứng minh ổn định cho toàn bộ preregistered pattern;
- exact-document linkage đủ evidence;
- D+1 rule tái lập được bằng trading calendar;
- boundary tests chứng minh không có same-day leakage;
- revision future vintage không back-propagate;
- coverage đủ cho phạm vi nghiên cứu đã freeze.

`PARTIAL`:

- chỉ một subset exchange/source/report pattern có verified publication date;
- downstream scope phải freeze đúng subset đó;
- unresolved rows vẫn quarantine.

`BLOCKED`:

- không thể chứng minh ngay cả date candidate là public disclosure date;
- provider `PublicDate` không có semantics đủ mạnh;
- official crosswalk không tái lập được;
- D+1 không giải quyết được ambiguity về ngày.

`FAIL`:

- date mapping làm report xuất hiện trước public evidence;
- provider date có systematic early-date conflict;
- revision handling làm future value xuất hiện trong past snapshot;
- implementation không tái lập được.

##### 12. Boundary tests bắt buộc

Với một report có:

```text
publication_date = D
eligible_from = T_next
```

phải test:

```text
decision_at < T_next  → report absent
decision_at = T_next  → report eligible
decision_at > T_next  → report eligible
```

Nếu snapshot date bằng D:

```text
report absent
```

Nếu D là ngày nghỉ:

```text
eligible_from = first open trading session strictly after D
```

##### 13. Trạng thái readiness đề xuất

R5 có thể bổ sung timing grade machine-readable:

```text
A_EXACT_TIMESTAMP
B_OFFICIAL_DATE_D1
C_FIRST_OBSERVED
UNRESOLVED
```

Ý nghĩa:

- `A_EXACT_TIMESTAMP`: exact timestamp PIT đã verify;
- `B_OFFICIAL_DATE_D1`: official publication date verify, dùng next-trading-day rule;
- `C_FIRST_OBSERVED`: chỉ prospective từ `first_observed_at`, không backdate;
- `UNRESOLVED`: không được dùng historical PIT.

Timing grade không tự động làm record `PIT_READY=true`; semantic, revision, taxonomy,
scope và provenance gates vẫn phải pass.

##### 14. Quyết định sau R5

```text
R5 PASS
    ↓
cho phép FIN-PIT-1 chạy trong phạm vi date-level PIT đã approve
    ↓
FIN-PIT-2..5 tiếp tục xử lý document semantics, taxonomy, revision và canonical PIT

R5 PARTIAL
    ↓
FIN-PIT-1 chỉ chạy cho exchange/source/report patterns đã date-verified
    ↓
phần còn lại giữ quarantine/prospective-only

R5 BLOCKED
    ↓
không backdate HNX/UPCOM
    ↓
duy trì market-only critical path
    ↓
chạy prospective first_observed_at collector nếu được approve

R5 FAIL
    ↓
reject date-level mapping gây leakage
    ↓
quay lại authoritative/provider evidence path
```

##### 15. Điều R5 không được làm

R5 không được:

- coi mọi “Ngày đăng tin” là publication date mà không có evidence;
- xóa phần giờ rồi mặc định ngày còn lại là đúng;
- dùng period end hoặc legal deadline thay publication date;
- dùng current scrape time để backdate historical report;
- dùng provider date nếu chưa crosswalk với official evidence;
- overwrite prior vintage bằng corrected report;
- tự bật financial feature;
- tự thay đổi M2 market-only protocol;
- tự mở scaled acquisition.

##### 16. Kết luận methodology của R5

R5 tồn tại vì R1–R4 đã chứng minh exact historical timestamp PIT cho HNX/UPCOM chưa đủ
evidence, nhưng chưa chứng minh date-level PIT là bất khả thi.

R5 kiểm tra một giả thuyết bảo thủ hơn:

```text
Nếu exact intraday availability không xác minh được
nhưng official publication date xác minh được,
thì dùng report từ next trading day thay vì loại toàn bộ HNX/UPCOM.
```

Đây là một methodology branch mới và phải được review/approve trước khi sử dụng trong
historical financial feature construction.



#### FIN-PIT-1A-R5 — Kết quả thực thi thực tế và handoff downstream

> **Trạng thái thực thi:** R5 đã hoàn tất về mặt kỹ thuật với `PASS`. Việc sử dụng
> methodology `B_OFFICIAL_DATE_D1` trong các stage downstream vẫn là
> `MANUAL_REVIEW_REQUIRED` và cần project owner phê duyệt rõ trước khi FIN-PIT-1 sử dụng
> rule này trong construction pipeline.

##### 1. Kết quả thực thi R5

Phạm vi đã chạy:

```text
PVS / HNX   = 4 samples
ACV / UPCOM = 8 samples
TOTAL       = 12 samples
```

Kết quả:

```text
HNX:
date_verified = 4/4
D+1_usable    = 4/4

UPCOM:
date_verified = 8/8
D+1_usable    = 8/8

TOTAL:
official-only       = 12/12
provider-assisted   = 0/12
unresolved          = 0
revision_conflict   = 0
quarantine          = 0
```

FiinGroup giữ trạng thái:

```text
PROMISING_BUT_NOT_QUALIFIED
```

R5 không dùng provider-assisted evidence để đạt gate.

##### 2. Exact scope đã thực hiện

R5 thực hiện offline immutable replay trên đúng frozen samples và prior artifacts.

Input artifact hashes đã ghi nhận:

```text
FIN-PIT-1A = 77ff2dde...
R1          = 3f1576be...
R2          = dc1dd9e1...
R3          = a59382bd...
R4          = 8cd46b2d...
C8 calendar = 5876d794...
```

Output artifact hashes đã ghi nhận:

```text
checksums.json = 2ab6d1c5...
gate.json      = 7ec7a062...
manifest.json  = 0cb0f0e9...
```

Network request count:

```text
0
```

Tests:

```text
39 targeted tests
compileall
JSON parse
diff check
offline verifier
```

Kết quả test:

```text
PASS
```

##### 3. Điều R5 đã chứng minh được

Trong đúng frozen HNX/UPCOM patterns, R5 đã chứng minh được:

1. Có thể xác định `publication_date` ở cấp ngày từ official evidence.
2. Không cần dựa vào FiinGroup để xác minh 12/12 pilot samples.
3. Nếu exact intraday timing chưa đủ evidence, có thể tạo conservative eligibility:

```text
publication_date = D
eligible_from    = first open trading session strictly after D
```

4. Same-day use bị cấm.
5. Trading-calendar rule dùng first open session, không dùng calendar `D + 1`.
6. Offline replay và artifact provenance tái lập được.
7. R1–R4 không bị phủ nhận:
   - exact timestamp vẫn unresolved;
   - source-specific timezone vẫn unresolved;
   - authoritative first-public intraday semantics vẫn unresolved;
   - full revision/version timestamp semantics vẫn unresolved.

Machine-readable timing grade được đề xuất cho pattern này:

```text
B_OFFICIAL_DATE_D1
```

##### 4. Điều R5 chưa chứng minh và không được suy diễn

R5 **không chứng minh**:

- exact `hh:mm:ss`;
- HNX/UPCOM timezone semantics của `PUBLICTIME`;
- exact first-public instant;
- authoritative revision/version lifecycle đầy đủ;
- full official PDF binary identity/hash cho mọi downstream report;
- Q2/Q3 standalone hay YTD;
- consolidated/separate semantics;
- audit/review status;
- taxonomy mapping;
- canonical report/fact representation;
- representative-market coverage;
- financial-feature readiness.

R5 cũng không:

```text
- chạy FIN-PIT-1;
- ghi canonical financial rows;
- bật financial features;
- chạy scaled acquisition.
```

Trạng thái sau R5 vẫn là:

```text
FINANCIAL_FEATURES_ALLOWED = false
```

##### 5. Manual methodology decision cần freeze trước FIN-PIT-1

Project owner cần quyết định rõ có chấp nhận policy sau hay không:

```text
POLICY_ID = B_OFFICIAL_DATE_D1_V1

Nếu report thuộc một official publication-date pattern đã được R5 verify:

publication_date = D

eligible_from =
first open trading session strictly after D

Same-day historical use = prohibited
```

Policy này chỉ áp dụng cho:

```text
verified official publication-date patterns
```

Không được hiểu thành:

```text
mọi HNX/UPCOM report đều mặc định D+1 usable
```

Nếu một report mới không match pattern đã approve:

```text
date_verified = false
pit_date_usable = false
→ quarantine / unresolved
```

##### 6. Handoff từ R5 sang FIN-PIT-1

FIN-PIT-1 được phép kế thừa từ R5:

```text
- approved date-level timing policy nếu owner đã approve;
- official publication-date evidence pattern;
- eligible_from = next open trading session;
- frozen pilot identities;
- immutable prior artifacts;
- provenance/checksum references;
- timing grade B_OFFICIAL_DATE_D1.
```

FIN-PIT-1 **không cần chứng minh lại** exact intraday time cho các pattern đã được
methodology approve.

FIN-PIT-1 vẫn phải tự thực hiện và chứng minh:

```text
- exact source/document acquisition;
- correct disclosure ↔ attachment linkage;
- raw PDF/document retrieval khi access hợp lệ;
- immutable file storage;
- SHA-256 cho successful document/file;
- raw metadata/provenance;
- request bounds/access contract;
- partial failure manifest;
- no canonical rows;
- no financial features.
```

FIN-PIT-1 phải giữ riêng:

```text
publication_date
eligible_from
timing_grade
timing_evidence_source
```

và không biến `B_OFFICIAL_DATE_D1` thành exact timestamp.

##### 7. Handoff từ R5 sang FIN-PIT-2

FIN-PIT-2 được phép dùng:

```text
publication_date
eligible_from
timing_grade = B_OFFICIAL_DATE_D1
```

như timing context đã được approve cho exact pattern.

FIN-PIT-2 phải tự chứng minh:

```text
- document linkage;
- statement type;
- period_start / period_end;
- instant vs duration;
- Q2/Q3 standalone vs YTD;
- current vs comparative column;
- consolidated vs separate;
- audit/review status;
- unit/sign;
- fact candidate provenance;
- API/PDF mismatch;
- taxonomy candidate evidence.
```

Nếu semantic extraction fail:

```text
SEMANTIC_READY = false
```

dù R5 timing đã pass.

R5 timing pass không tự động tạo:

```text
PIT_READY = true
```

##### 8. Handoff từ R5 sang FIN-PIT-3

FIN-PIT-3 phải review timing và semantics như hai evidence dimensions riêng.

Đối với record dùng R5:

```text
timing policy = B_OFFICIAL_DATE_D1
```

FIN-PIT-3 cần kiểm tra:

```text
- record có match exact approved R5 pattern không;
- publication-date evidence có provenance đầy đủ không;
- same-day exclusion có được giữ không;
- revision candidate có làm thay đổi timing context không;
- semantic evidence từ FIN-PIT-2 có đủ không.
```

FIN-PIT-3 không được nâng:

```text
B_OFFICIAL_DATE_D1 → A_EXACT_TIMESTAMP
```

trừ khi có evidence mới và methodology approval riêng.

##### 9. Handoff từ R5 sang FIN-PIT-4

FIN-PIT-4 phải đảm bảo schema/canonical contract biểu diễn được tối thiểu:

```text
publication_date
eligible_from
timing_grade
timing_policy_version
timing_evidence_source
source_document_hash
report vintage identity
revision relation/status
```

Nếu schema hiện tại không đủ, phải đánh giá schema change theo đúng FIN-PIT-4 contract.

Schema phải phân biệt rõ:

```text
A_EXACT_TIMESTAMP
B_OFFICIAL_DATE_D1
C_FIRST_OBSERVED
UNRESOLVED
```

hoặc một representation tương đương có version hóa.

Không được ép mọi timing grade thành một trường `available_at` giả có `00:00:00`,
`23:59:59` hoặc một giờ mặc định.

##### 10. Handoff từ R5 sang FIN-PIT-5

FIN-PIT-5 PIT verifier phải hiểu `B_OFFICIAL_DATE_D1`.

Đối với date-level report:

```text
publication_date = D
eligible_from = T_next
```

Verifier phải chứng minh:

```text
decision_at < T_next  → report absent
decision_at = T_next  → report eligible
decision_at > T_next  → report eligible
```

Nếu `decision_at` nằm trong ngày D:

```text
report absent
```

Future revision không được thay đổi snapshot trước thời điểm revision đủ eligibility.

FIN-PIT-5 cũng phải giữ fail-closed nếu:

```text
timing_grade = UNRESOLVED
```

##### 11. Handoff sang FIN-PIT-6/7 representative và scaled acquisition

R5 PASS trên 12/12 pilot không được diễn giải là toàn bộ HNX/UPCOM đã verified.

Khi scale, mỗi new report phải:

```text
1. match approved official publication-date pattern;
2. có document/disclosure linkage đủ evidence;
3. pass date verification;
4. tính eligible_from bằng canonical trading calendar;
5. fail-closed nếu pattern không match.
```

Coverage funnel phải tách riêng:

```text
date_candidate_found
date_verified
D1_usable
semantic_ready
revision_safe
pit_ready
```

Phải báo coverage riêng cho:

```text
HOSE
HNX
UPCOM
```

và không dùng kết quả 12/12 pilot làm proxy cho market-wide coverage.

##### 12. Handoff sang FIN-PIT-8 financial feature approval

R5 không approve bất kỳ financial feature nào.

FIN-PIT-8 chỉ được bật feature nếu record đầu vào đã:

```text
SEMANTIC_READY = true
PIT_READY      = true
```

Đối với report timing grade:

```text
B_OFFICIAL_DATE_D1
```

feature construction phải dùng `eligible_from`, không dùng `period_end` hoặc same-day
publication date làm availability boundary.

##### 13. Trạng thái tổng hợp sau R5

```text
FIN-PIT-1A-R5_TECHNICAL_GATE = PASS
DOWNSTREAM_METHODOLOGY_STATUS = MANUAL_REVIEW_REQUIRED

HNX_DATE_LEVEL_PIT_FEASIBLE   = true   # frozen pilot pattern
UPCOM_DATE_LEVEL_PIT_FEASIBLE = true   # frozen pilot pattern

EXACT_INTRADAY_PIT            = UNRESOLVED
AUTHORITATIVE_REVISION_TIMING = UNRESOLVED

FIINGROUP = PROMISING_BUT_NOT_QUALIFIED

FINANCIAL_FEATURES_ALLOWED = false
CANONICAL_FINANCIAL_ROWS_WRITTEN = 0
FIN_PIT_1_EXECUTED = false
```


##### 13A. Owner methodology approval — bounded pilot use

Project owner đã phê duyệt methodology R5 cho **bounded pilot use**, không phải
market-wide approval.

```text
OWNER_METHODOLOGY_APPROVAL = APPROVED_FOR_BOUNDED_PILOT_USE

APPROVED_POLICY = B_OFFICIAL_DATE_D1_V1

APPROVED_SCOPE:
- PVS/HNX: 4 frozen samples
- ACV/UPCOM: 8 frozen samples

ELIGIBILITY_RULE:
eligible_from =
first open trading session strictly after publication_date

SAME_DAY_USE = PROHIBITED

EXACT_TIMESTAMP_PIT = UNRESOLVED

MARKET_WIDE_HNX_UPCOM_APPROVAL = false

FINANCIAL_FEATURES_ALLOWED = false

R5_HANDOFF_STATUS =
APPROVED_FOR_BOUNDED_FIN_PIT_1_USE
```

Ý nghĩa của approval này:

- owner chấp nhận dùng `B_OFFICIAL_DATE_D1_V1` trong đúng frozen scope đã được R5
  technical gate kiểm chứng;
- FIN-PIT-1 được phép kế thừa `publication_date`, `eligible_from`, `timing_grade`,
  `timing_policy_version` và timing evidence trong bounded pilot;
- approval này không được suy rộng thành mọi report HNX/UPCOM đều D+1 usable;
- report/pattern mới không match R5-approved evidence phải fail-closed và giữ
  `UNRESOLVED`/quarantine;
- exact intraday timestamp, HNX-specific timezone và authoritative revision/version
  timing semantics vẫn unresolved;
- approval này không bật canonical financial rows hoặc financial features;
- market-wide generalization chỉ có thể được xem xét ở representative/scaled stages sau
  khi coverage và pattern stability được kiểm chứng riêng.


##### 14. Điều kiện được phép bắt đầu FIN-PIT-1

Điều kiện manual approval đã được hoàn tất ở Mục 13A:

```text
OWNER_METHODOLOGY_APPROVAL = APPROVED_FOR_BOUNDED_PILOT_USE
R5_HANDOFF_STATUS = APPROVED_FOR_BOUNDED_FIN_PIT_1_USE
```

FIN-PIT-1 hiện được phép bắt đầu **bounded source/document pilot** và dùng R5 timing
result trong đúng approved scope.

Approval phải nêu rõ:

- scope áp dụng;
- same-day exclusion;
- next-open-session rule;
- fail-closed cho unmatched pattern;
- exact timestamp vẫn unresolved;
- revision semantics chưa được coi là hoàn tất;
- financial features vẫn disabled.

Nếu owner không approve:

```text
FIN-PIT-1 downstream timing use = BLOCKED
```

Nếu owner approve:

```text
R5_HANDOFF_STATUS = APPROVED_FOR_BOUNDED_FIN_PIT_1_USE
```

và FIN-PIT-1 được phép dùng R5 timing result trong đúng approved scope.


#### Quyết định chung sau FIN-PIT-1A remediation

- nếu exact timestamp path `PASS`: tiếp tục FIN-PIT-1 với exact timing contract;
- nếu R5 `PASS`: tiếp tục FIN-PIT-1 với approved date-level D+1 contract;
- nếu `PARTIAL`: freeze downstream scope đúng phần đã chứng minh;
- nếu `BLOCKED`: giữ market-only critical path hoặc prospective-only financial data;
- không được ép historical feature coverage bằng estimated timestamp/date;
- không stage nào trong R1–R5 tự động bật financial features.

### FIN-PIT-1 — Source/document pilot

Mục tiêu:

- triển khai bounded collector cho pilot universe;
- lấy CafeF summary, document index, linked PDF và metadata/timestamp từ nguồn công bố
  chính thức khi truy cập hợp lệ;
- bảo toàn raw evidence, chưa canonicalize fact.

Trước network execution phải freeze:

- config pilot và exact universe;
- request bounds, pagination, retry/backoff, rate limit và timeout;
- allowed hosts/routes;
- raw directory layout;
- manifest schema;
- resume/checksum behavior;
- dry-run behavior;
- user-agent/provenance policy;
- access-control fail-closed behavior.

Runner bắt buộc có:

- dry-run zero-network;
- explicit `--execute` cho real acquisition;
- immutable resume theo exact config/code/job-plan hashes;
- bounded page/report/document count;
- không ghi đè raw file tồn tại;
- partial failure manifest;
- checksum verification offline;
- không mở canonical promotion.

Output artifact gợi ý:

```text
artifacts/financial_pit/fin-pit-1-source-document-pilot-v1/
    manifest.json
    job_plan.json
    raw/...
    documents/...
    source_index.jsonl
    document_index.jsonl
    acquisition_findings.jsonl
    checksums.json
    gate.json
```

Acceptance gate:

- exact pilot membership;
- mọi successful response/file có hash và provenance;
- không request ngoài allowlist/bounds;
- resume không thay đổi byte của artifact cũ;
- không bypass access control;
- raw replay/checksum verification PASS;
- mọi missing/blocked source được ghi riêng;
- `canonical_rows_written = 0`;
- `financial_features_written = 0`.

Status hợp lệ: `PASS`, `PARTIAL`, `BLOCKED`, `FAIL`. `PASS` chỉ nói acquisition
pilot đúng contract, không nói PIT semantics đã được phê duyệt.

#### FIN-PIT-1 — Kết quả thực thi thực tế và handoff downstream

> **Trạng thái thực thi:** FIN-PIT-1 đã hoàn tất bounded source/document pilot với
> gate `PASS`. Kết quả chỉ chứng minh acquisition contract trong exact pilot scope;
> không semantic-approve document, không tạo canonical financial fact và không bật
> financial feature.

##### 1. Execution mode và exact scope

```text
EXECUTION_MODE = HYBRID

PILOT UNIVERSE:
FPT — HOSE
VNM — HOSE
PVS — HNX
ACV — UPCOM

REPORT CANDIDATES = 16
PLANNED OFFICIAL DOCUMENT REQUESTS = 36
PAGINATION = 0
DISCOVERY REQUESTS NGOÀI FROZEN PLAN = 0
```

FIN-PIT-1 tái sử dụng đúng 4 HOSE timing controls từ FIN-PIT-1A và 12 exact
HNX/UPCOM patterns đã được R5 approve. Không mở rộng sang ticker, period hoặc source
pattern khác.

##### 2. Acquisition contract đã freeze

Trước real network execution, stage đã freeze:

```text
allowed hosts:
- staticfile.hsx.vn
- owa.hnx.vn

allowed routes:
- /Uploads/FinancialReport/
- /ftp/

method                  = GET only
maximum_requests        = 40
maximum_documents       = 40
actual_planned_requests = 36
attempts                = 2
minimum_interval        = 1 second
timeout                 = 30 seconds
maximum_response_bytes  = 50 MiB
follow_redirects        = false
pagination_allowed      = false
access_control          = FAIL_CLOSED_NO_BYPASS
```

Runner yêu cầu explicit `--execute`; `--dry-run` chỉ build/validate job plan và tạo
`network_requests = 0`. Resume chỉ được phép khi config, code và job-plan hashes giữ
nguyên; existing artifact hash mismatch phải fail closed.

##### 3. Kết quả network và document acquisition

```text
NETWORK REQUEST COUNT     = 36
SUCCESSFUL REQUEST COUNT  = 36
FAILED REQUEST COUNT      = 0

SUCCESSFUL DOWNLOADS      = 36
CONTENT-UNIQUE DOCUMENTS  = 32
DOCUMENT INDEX ROWS       = 40
DISCLOSURES FOUND         = 16
LINKAGE CANDIDATES        = 40
QUARANTINE                = 0
```

`DOCUMENT INDEX ROWS = 40` lớn hơn số request vì một số exact official documents được
link với nhiều scope candidates, ví dụ consolidated/separate candidates cùng thuộc một
official disclosure. Content-addressed storage deduplicate identical bytes theo SHA-256
nhưng không làm mất các candidate linkage riêng.

Mọi successful document/response đều giữ:

- source URL;
- retrieval time;
- content type;
- byte size;
- SHA-256;
- immutable relative path;
- collector/config/code version;
- parent run/job linkage.

##### 4. Timing handoff từ R5

```text
A_EXACT_TIMESTAMP   = 4
B_OFFICIAL_DATE_D1  = 12
C_FIRST_OBSERVED    = 0
UNRESOLVED          = 0
```

Bốn HOSE controls giữ exact timing đã được FIN-PIT-1A verify. Mười hai HNX/UPCOM
candidates giữ riêng:

```text
publication_date
eligible_from
timing_grade = B_OFFICIAL_DATE_D1
timing_policy_version = B_OFFICIAL_DATE_D1_V1
timing_evidence_source
```

FIN-PIT-1 không tạo `00:00:00`, `23:59:59` hoặc timestamp mặc định để biểu diễn D+1.
Same-day use tiếp tục bị cấm. Kết quả 12/12 không được suy rộng thành market-wide
HNX/UPCOM approval.

##### 5. Linkage và revision candidates

```text
LINKAGE STATUS:
MATCHED   = 40
AMBIGUOUS = 0
MISSING   = 0
CONFLICT  = 0

REVISION CANDIDATE GROUPS = 7
REVISION RELATION          = UNKNOWN cho toàn bộ 7 groups
```

`MATCHED` tại FIN-PIT-1 chỉ có nghĩa official disclosure/attachment route đã được nối
với document candidate bằng frozen source evidence. Nó không semantic-approve statement
type, period column, scope, assurance hoặc taxonomy.

Bảy revision candidate groups được tạo vì có nhiều official attachment hashes dưới
cùng ticker/period/report-type candidate key. FIN-PIT-1 không kết luận đây là
correction, restatement hoặc replacement; detailed classification được defer sang
FIN-PIT-2 và review downstream.

##### 6. CafeF financial summary

```text
CAFEF FINANCIAL SUMMARY REQUESTS = 0
STATUS = NOT_REQUESTED
REASON = NO_VERIFIED_CAFEF_FINANCIAL_SUMMARY_ENDPOINT_IN_REPOSITORY
```

Repository có CafeF market adapters nhưng chưa có verified financial-summary endpoint
và semantics phù hợp. FIN-PIT-1 không phát minh endpoint, không fuzzy-map và không dùng
CafeF summary làm canonical source.

##### 7. Output artifact và hashes

```text
artifacts/financial_pit/fin-pit-1-source-document-pilot-v1/
```

Top-level artifact hashes:

```text
manifest.json             e3964360ac4903015b1eafb5ffe33f150dcac11ac7be23541a99af106c5e66a8
job_plan.json             86b3f95beb5925b83e7950c133aca2832cb064d93d095e7f013250689bdc3b1b
checksums.json             7e3077b37e2d70325b0d1cf9e9bac212c7dc01d9bb7936e28d29d17c49126fd7
gate.json                  b210b8dacb2ec08dd8e78c80dd48eb9ea6bddfa091e252b660ad1cb07fb93ac6
source_index.jsonl         22bb3f20f438a13260720d3183b97d222fc456df775395aec48b911fb7b5ff48
document_index.jsonl       d0b41c19a05ca34da9ef49200a97059f05b37ce9398ef30108454bf9f1ce6b55
acquisition_findings.jsonl 5d5ce4a458f2cfb35bb0c711cba137ce1293a552e446af5a7be909053b4b462f
timing_index.jsonl         4874fc1fdc9e9699b62c5a9df78709b82bf7501015d70efb3f972abb446a8186
linkage_candidates.jsonl   e9ad7eb4dff152b4b02fdd8c9dec1b80419275bba7c2fd1ffe48df6456e7d615
revision_candidates.jsonl  c30b37ce0317378c730a70f6dd32149a0032b6046341e01d3188a8e2370987b3
quarantine.jsonl           e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

`checksums.json` bao phủ raw evidence, stored documents và các indexes. Offline verifier
đã verify 57 files mà không gọi network.

##### 8. Tests và repository gates

```text
Targeted FIN-PIT/timing tests = 29/29 PASS
Dry-run                       = PASS, network_requests = 0
Offline artifact verifier     = PASS, verified_file_count = 57
Compileall                    = PASS
Synthetic smoke               = PASS, status = complete, synthetic = true
JSON config parse             = PASS
git diff --check              = PASS
```

Full repository discovery chạy 199 tests: 196 test bodies PASS và 3 `setUpClass`
errors do isolated worktree không chứa các heavy ignored C5/C8/M1/M2 artifacts. Không
có FIN-PIT-1 assertion failure. Heavy market artifacts không được copy hoặc recompute
chỉ để ép full-suite environment gate.

##### 9. Gate conclusion

```text
FIN_PIT_1_GATE = PASS

canonical_rows_written     = 0
financial_features_written = 0
financial_features_allowed = false
access_control_bypass      = false
```

Gate `PASS` dựa trên exact membership, bounded requests, complete hash/provenance,
immutable storage, resume guard, zero-network dry-run, offline verification và timing
handoff đúng R5 policy. Gate không dựa riêng vào process exit code.

##### 10. Handoff sang FIN-PIT-2

FIN-PIT-2 có thể dùng immutable FIN-PIT-1 artifact để review:

- official disclosure ↔ attachment linkage;
- statement/document type;
- period và column semantics;
- consolidated/separate;
- unaudited/reviewed/audited;
- KQKD/CĐKT/LCTT;
- standalone/YTD;
- document roles trong 7 revision candidate groups.

FIN-PIT-2 vẫn phải fail closed cho ambiguity và không được coi `MATCHED` ở FIN-PIT-1
là semantic approval. Exact next financial stage là:

```text
FIN-PIT-2 — Document linkage và semantic extraction
```

Stage này chỉ được mở trong một session riêng khi owner yêu cầu. FIN-PIT-1 dừng tại
đây và không tự động thực hiện FIN-PIT-2.

### FIN-PIT-2 — Document linkage và semantic extraction

Mục tiêu:

- nối CafeF summary candidate với disclosure/PDF cụ thể;
- trích period, scope, assurance, unit và fact candidates;
- không promote khi linkage hoặc semantics mơ hồ.

Yêu cầu:

- PDF text extraction; OCR chỉ khi cần và phải ghi engine/version/confidence;
- page/region provenance cho field trích xuất;
- phân biệt current-period, YTD và comparative columns;
- statement-specific period semantics;
- source label và raw numeric value được giữ nguyên;
- normalized candidate không làm mất raw representation;
- API/PDF mismatch tạo conflict, không average;
- document linkage có confidence/evidence reason, không chỉ dựa tên gần giống.

Output:

```text
report_candidates.jsonl
fact_candidates.jsonl
document_linkage.jsonl
timing_candidates.jsonl
taxonomy_candidates.jsonl
conflicts.jsonl
quarantine.jsonl
semantic_review_report.json
gate.json
```

Gate tối thiểu:

- 100% promoted-to-verified candidate có PDF/document provenance;
- 100% field period/scope/unit có evidence location;
- Q2/Q3 không dùng global default;
- statement type được kiểm tra độc lập;
- ambiguity đi vào quarantine;
- chưa ghi canonical table.

#### Kết quả thực thi FIN-PIT-2 — 2026-10-01

```text
EXECUTION_MODE = AI_EXECUTES
STATUS = PARTIAL
NETWORK_REQUEST_COUNT = 0
```

Stage đã chạy offline trên immutable FIN-PIT-1 artifact cho pilot `FPT`, `VNM`,
`PVS`, `ACV`. Output được ghi tại:

```text
artifacts/financial_pit/fin-pit-2-semantic-extraction-v1/
```

Kết quả chính:

- xử lý 32 document unique-content, tạo 32 report candidates và đánh giá 40
  document-linkage candidates;
- document linkage gồm 6 `VERIFIED`, 34 `AMBIGUOUS`, 0 `CONFLICT`, 0 `MISSING`;
- nhận diện 4 `PRIMARY_FINANCIAL_REPORT` và 2 supporting/explanatory documents;
- 3 report PVS năm 2022 đạt `SEMANTIC_READY`; FPT, VNM và ACV chưa có report
  semantic-ready vì PDF scan không có usable text layer và environment không có OCR
  engine phù hợp;
- statement evidence gồm 4 balance sheets, 3 income statements, 3 cash-flow
  statements và 3 notes;
- tạo 220 fact candidates, toàn bộ từ PVS: 216 balance-sheet facts có
  `duration_basis=INSTANT` và đạt `SEMANTIC_READY`, 4 facts unresolved;
- không gán Q2/Q3 bằng global assumption: `standalone_verified=0`,
  `YTD_verified=0`; document thiếu wording evidence tiếp tục unresolved/quarantine;
- scope giữ riêng 5 `CONSOLIDATED`, 1 `SEPARATE`, 26 `UNKNOWN`; không merge hoặc
  average;
- assurance gồm 3 `AUDITED`, 29 `UNKNOWN`; unit evidence được verify cho 9
  document candidates, 23 còn `UNKNOWN`;
- tạo 220 taxonomy candidates nhưng không final-promote mapping;
- cả 7 revision candidate groups chưa có official evidence đủ mạnh: 0 resolved,
  7 tiếp tục giữ `revision_relation=UNKNOWN` dưới dạng immutable vintages;
- có 0 semantic conflict và 29 report candidates bị quarantine vì evidence chưa đủ;
- timing handoff được preserve: 4 `A_EXACT_TIMESTAMP`, 28
  `B_OFFICIAL_DATE_D1`, 0 `C_FIRST_OBSERVED`, 0 timing unresolved;
- `canonical_rows_written=0` và `financial_features_written=0`.

Gate là `PARTIAL`, không phải `PASS`: subset PVS text-based có evidence đủ cho
review downstream giới hạn, nhưng coverage pilot chưa đầy đủ. FIN-PIT-3 không được
tự động mở; chỉ bắt đầu nếu owner chấp nhận scope giới hạn được freeze rõ, hoặc sau
một OCR run có provenance `engine/version/page/confidence` để đánh giá lại phần scan.

Verification đã hoàn tất với 13/13 targeted contract tests, JSON parse, offline
artifact verifier, `compileall`, synthetic smoke và `git diff --check`. Full suite
không được gọi là `PASS` vì collection gặp setup/import error do runtime thiếu
optional dependency `matplotlib`; chưa quan sát assertion failure trước setup error.

### FIN-PIT-2-R1 — OCR remediation for scanned financial documents

> **Bổ sung sau FIN-PIT-2 PARTIAL — mục đích:** xử lý các tài liệu scan không có text layer khiến FIN-PIT-2 chưa đủ semantic evidence cho toàn bộ bounded pilot. Stage này chỉ remediation cho semantic extraction; không thay timing methodology, không canonicalize financial facts và không mở FIN-PIT-3 tự động.

#### 1. Bối cảnh mở FIN-PIT-2-R1

FIN-PIT-2 kết thúc với trạng thái:

```text
FIN_PIT_2_STATUS = PARTIAL
```

Kết quả chính:

```text
documents_processed = 32
document_linkage_candidates = 40

primary_financial_reports = 4
supporting_documents = 2
unclassified_or_uncertain_documents = 26

linkage_verified = 6
linkage_ambiguous = 34
linkage_conflict = 0
linkage_missing = 0

fact_candidates = 220
semantic_ready_reports = 3
semantic_ready_facts = 216

quarantine_report_candidates = 29
```

Các báo cáo PVS năm 2022 có semantic evidence tương đối đầy đủ, nhưng FPT/VNM/ACV và một phần tài liệu khác chưa đủ evidence chủ yếu vì PDF scan không có text layer.

FIN-PIT-2 đã chứng minh semantic extraction pipeline hoạt động trên tài liệu text-based, nhưng coverage chưa đủ để mở FIN-PIT-3 cho toàn bounded pilot.

#### 2. Blocker cần remediation

Blocker chính:

```text
scanned PDF
    ↓
no usable text layer
    ↓
document role unresolved
period/scope/assurance/unit unresolved
    ↓
document linkage ambiguous
    ↓
semantic_ready = false
    ↓
quarantine
```

Đây là extraction blocker, không phải timing blocker.

R5 timing vẫn được bảo toàn:

```text
HOSE:
A_EXACT_TIMESTAMP

HNX/UPCOM:
B_OFFICIAL_DATE_D1
```

Không được mở lại hoặc thay đổi timing methodology trong stage này.

#### 3. Mục tiêu

FIN-PIT-2-R1 phải:

1. xác định chính xác tài liệu nào thực sự cần OCR;
2. chạy OCR chỉ trên tài liệu/page không có usable text layer;
3. giữ provenance đầy đủ của OCR output;
4. không ghi đè raw PDF;
5. chạy lại semantic extraction trên OCR text;
6. cập nhật:
   - document classification;
   - document linkage;
   - period semantics;
   - scope;
   - assurance;
   - unit;
   - fact candidates;
   - taxonomy candidates;
   - semantic readiness;
7. giảm số lượng `AMBIGUOUS` và `quarantine` nếu evidence mới đủ mạnh;
8. giữ fail-closed nếu OCR không đủ tin cậy.

#### 4. Scope

Không chạy lại toàn bộ financial workstream.

Input chính là artifact đã tạo ở FIN-PIT-1 và FIN-PIT-2.

Ưu tiên remediation cho:

```text
26 documents
```

đang chưa phân loại chắc chắn hoặc không có usable text layer.

Đặc biệt tập trung vào các report candidates thuộc:

```text
FPT
VNM
PVS
ACV
```

trong bounded pilot hiện tại.

Không tự mở rộng ticker, period hoặc market-wide scope.

#### 5. Preflight classification trước OCR

Không được OCR toàn bộ 32 documents một cách mặc định.

Trước tiên phải phân loại:

```text
TEXT_BASED_USABLE
TEXT_BASED_LOW_QUALITY
SCAN_IMAGE_ONLY
MIXED_TEXT_AND_SCAN
UNSUPPORTED_OR_CORRUPT
```

Chỉ OCR khi:

```text
SCAN_IMAGE_ONLY
```

hoặc page cụ thể của:

```text
MIXED_TEXT_AND_SCAN
```

thực sự cần OCR.

Nếu text layer hiện tại đã đủ cho semantic extraction thì không OCR lại.

#### 6. Immutable evidence

Raw PDF từ FIN-PIT-1 phải giữ nguyên byte/hash.

OCR output phải là artifact dẫn xuất mới:

```text
raw PDF
    ↓
OCR process
    ↓
derived OCR artifact
```

Không được:

```text
overwrite PDF
replace PDF
modify original hash
```

Mỗi OCR artifact phải liên kết ngược về:

```text
source_document_hash
source_document_path
page number
OCR engine
OCR engine version
OCR config
run ID
created_at
```

#### 7. OCR provenance

Mỗi OCR result tối thiểu phải có:

```text
document_hash
page
ocr_engine
ocr_version
ocr_config_hash
raw_ocr_text
normalized_text_candidate
confidence nếu engine hỗ trợ
bounding box/region nếu có
language/config
processing status
```

Nếu confidence không có thì ghi rõ:

```text
confidence = NOT_AVAILABLE
```

Không được tự tạo confidence giả.

#### 8. OCR engine policy

Ưu tiên engine đã có sẵn trong repository/environment.

Không được tự thêm cloud OCR service hoặc external paid OCR nếu chưa có owner approval.

Nếu cần cài thêm OCR dependency:

- ghi rõ dependency;
- giải thích lý do;
- không thay đổi raw data contract;
- chạy targeted tests.

OCR phải hỗ trợ tiếng Việt đủ để đọc:

```text
- tiêu đề báo cáo;
- kỳ báo cáo;
- đơn vị;
- consolidated/separate;
- audited/reviewed wording;
- table labels.
```

#### 9. Page-level OCR

Không mặc định OCR toàn bộ pages nếu chỉ một số page cần semantic evidence.

Ưu tiên page chứa:

```text
cover/title
auditor/review report
balance sheet
income statement
cash flow statement
unit/header
period labels
```

Nếu document không có page index đủ tin cậy, có thể OCR rộng hơn nhưng phải ghi scope thực tế.

#### 10. Semantic extraction sau OCR

OCR text chỉ là evidence candidate.

Sau OCR phải chạy lại các bước FIN-PIT-2:

```text
document classification
        ↓
document linkage review
        ↓
statement classification
        ↓
period semantics
        ↓
scope
        ↓
assurance
        ↓
unit
        ↓
fact extraction
        ↓
taxonomy candidate
        ↓
semantic readiness
```

Không được coi OCR success đồng nghĩa semantic success.

#### 11. Period semantics

Stage này phải đặc biệt cố gắng giải quyết:

```text
Q2/Q3 standalone vs YTD
```

bằng evidence OCR từ:

```text
column title
statement heading
period wording
current/comparative columns
```

Không dùng global assumption.

Nếu OCR text vẫn không đủ rõ:

```text
duration_basis = UNKNOWN
semantic_ready = false
```

#### 12. Scope

Dùng OCR evidence để xác định:

```text
CONSOLIDATED
SEPARATE
UNKNOWN
```

Nếu cả hai tồn tại:

```text
giữ riêng
```

Không merge.

#### 13. Assurance

Dùng OCR để tìm:

```text
AUDITED
REVIEWED
UNAUDITED
UNKNOWN
```

Ưu tiên:

```text
auditor/review report
document title
official wording
```

Không suy assurance chỉ từ loại kỳ.

#### 14. Unit

Dùng OCR để xác định:

```text
VND
thousand VND
million VND
billion VND
shares
percentage
other
unknown
```

Phải giữ:

```text
raw_unit
normalized_unit
unit_multiplier
```

Nếu OCR unit mơ hồ:

```text
unit_status = UNKNOWN
```

#### 15. Fact candidates

Stage được phép bổ sung fact candidates mới từ OCR.

Mỗi fact candidate phải có:

```text
source_document_hash
page
OCR provenance
raw_label
raw_value
raw_unit
statement_type
period context
column role
scope
taxonomy candidate
semantic status
```

Không final-promote taxonomy.

#### 16. OCR quality controls

Phải có sanity checks tối thiểu:

```text
- document title readable;
- ticker/company identity consistent;
- period labels plausible;
- numeric table rows parseable;
- unit header consistent;
- no obvious page rotation/inversion issue;
- OCR output not empty/truncated.
```

Nếu OCR output nghi ngờ:

```text
OCR_STATUS = LOW_CONFIDENCE
```

và không semantic-promote.

#### 17. Numeric extraction safety

OCR numeric error là rủi ro lớn.

Ví dụ:

```text
1.000.000
→ không được đọc nhầm thành
1.000.00O
```

hoặc:

```text
(1,234)
```

không được mất dấu âm/bracket semantics.

Phải giữ:

```text
raw_ocr_numeric_text
parsed_numeric_candidate
parse_status
```

Nếu parse không chắc chắn:

```text
parse_status = UNRESOLVED
```

#### 18. Revision candidates

7 revision groups từ FIN-PIT-2 phải tiếp tục giữ:

```text
revision_relation = UNKNOWN
```

trừ khi OCR đọc được explicit official wording như:

```text
đính chính
thay thế
bổ sung
công bố lại
```

và document/disclosure evidence đủ mạnh.

Hash khác nhau vẫn không tự động đồng nghĩa revision.

#### 19. Timing preservation

Stage này không được thay timing:

```text
A_EXACT_TIMESTAMP
B_OFFICIAL_DATE_D1
```

OCR không được dùng để suy exact timestamp.

Không tạo:

```text
00:00:00
23:59:59
```

hoặc timezone giả.

#### 20. Output artifact

Đề xuất:

```text
artifacts/financial_pit/fin-pit-2-r1-ocr-remediation-v1/
```

Tối thiểu:

```text
ocr_document_inventory.jsonl
ocr_page_results.jsonl
ocr_provenance.jsonl

document_linkage_updated.jsonl
report_candidates_updated.jsonl
fact_candidates_updated.jsonl

period_semantics_review.jsonl
taxonomy_candidates_updated.jsonl
revision_review_updated.jsonl

conflicts.jsonl
quarantine.jsonl

semantic_coverage_before_after.json
semantic_review_report.json

manifest.json
checksums.json
gate.json
```

#### 21. Before/after coverage report

Bắt buộc so sánh:

```text
BEFORE OCR
AFTER OCR
```

Tối thiểu:

```text
documents_classified
documents_unclassified

linkage_verified
linkage_ambiguous

report_candidates
semantic_ready_reports

fact_candidates
semantic_ready_facts

period_verified
period_unresolved

standalone_verified
YTD_verified

scope_verified
scope_unknown

assurance_verified
assurance_unknown

unit_verified
unit_unresolved

quarantine_count
```

Phải báo riêng theo:

```text
FPT
VNM
PVS
ACV
```

và:

```text
HOSE
HNX
UPCOM
```

#### 22. Gate

Status hợp lệ:

```text
PASS
PARTIAL
BLOCKED
FAIL
```

##### PASS

Khi:

- OCR processing reproducible;
- provenance đầy đủ;
- raw PDFs không bị sửa;
- semantic coverage tăng đủ để bounded pilot có representative evidence;
- critical period/scope/unit fields được verify cho preregistered pilot patterns;
- unresolved OCR vẫn fail-closed;
- no canonical rows;
- financial features remain false.

PASS không yêu cầu mọi page/fact đều semantic-ready.

##### PARTIAL

Khi:

- OCR cứu được một phần đáng kể;
- nhưng một số ticker/report pattern vẫn semantic unresolved;
- downstream scope có thể freeze rõ.

##### BLOCKED

Khi:

- scan quality quá thấp;
- OCR không đọc được period/scope/unit;
- OCR dependency không khả dụng;
- document content không đủ để resolve semantics.

##### FAIL

Khi:

- raw PDF bị sửa/overwrite;
- OCR output mất provenance;
- OCR numeric error được promote thành fact;
- standalone/YTD bị suy sai;
- scope bị merge;
- revision bị fake-resolve;
- canonical rows được ghi ngoài stage.

#### 23. Điều kiện mở FIN-PIT-3 sau R1

FIN-PIT-3 chỉ nên mở khi:

```text
semantic evidence đủ cho một scope được freeze rõ
```

Có hai khả năng:

```text
R1 PASS
→ mở FIN-PIT-3 cho bounded pilot scope phù hợp
```

hoặc:

```text
R1 PARTIAL
→ chỉ mở FIN-PIT-3 cho verified subset
```

Nếu R1 vẫn BLOCKED trên FPT/VNM/ACV thì không được giả định coverage toàn pilot.

#### 24. Không được làm

FIN-PIT-2-R1 không được:

```text
- chạy FIN-PIT-3;
- canonicalize facts;
- final-promote taxonomy;
- bật financial features;
- mở FIN-PIT-6/7;
- crawl thêm toàn thị trường;
- sửa R5 timing methodology;
- dùng OCR output thay raw document;
- tự resolve revision không đủ evidence;
- dùng fuzzy matching để ép semantic coverage.
```

#### 25. Handoff format

Sau stage phải báo:

```text
STAGE:
FIN-PIT-2-R1

STATUS:

SCOPE EXECUTED:
SCOPE NOT EXECUTED:

INPUT ARTIFACTS + HASHES:
OUTPUT ARTIFACTS + HASHES:

OCR ENGINE:
OCR VERSION:
OCR DOCUMENTS:
OCR PAGES:

BEFORE COVERAGE:
AFTER COVERAGE:

DOCUMENT LINKAGE:
- verified:
- ambiguous:
- conflict:
- missing:

PERIOD SEMANTICS:
- instant:
- standalone:
- YTD:
- unresolved:

SCOPE:
- consolidated:
- separate:
- unknown:

ASSURANCE:
- audited:
- reviewed:
- unaudited:
- unknown:

UNITS:
- verified:
- unresolved:

FACT CANDIDATES:
SEMANTIC_READY_FACTS:

REVISION GROUPS:
- total:
- resolved:
- unknown:

QUARANTINE:
CONFLICTS:

TIMING PRESERVATION:

CANONICAL_ROWS_WRITTEN:
must equal 0

FINANCIAL_FEATURES_WRITTEN:
must equal 0

TESTS RUN:
TEST RESULTS:

GATE REASONING:

REMAINING LIMITS:

EXACT NEXT STAGE:
FIN-PIT-3 only if gate permits.
Do not execute it.

STOP CONDITION CONFIRMED:
YES
```

#### Kết quả thực thi FIN-PIT-2-R1 — 2026-10-01

```text
STAGE: FIN-PIT-2-R1
EXECUTION_MODE: AI_EXECUTES
STATUS: PARTIAL

OCR ENGINE: Tesseract OCR
OCR VERSION: v5.4.0.20240606
DOCUMENTS REVIEWED: 32
DOCUMENTS OCR_REQUIRED / OCR_PROCESSED: 26 / 26
OCR PAGES: 209 (205 OCR_SUCCESS, 4 LOW_CONFIDENCE)

BEFORE → AFTER:
documents classified: 6 → 32
linkage verified: 6 → 27
linkage ambiguous: 34 → 4
linkage conflict: 0 → 9
semantic-ready reports: 3 → 6
fact candidates: 220 → 242
semantic-ready facts: 216 → 216
period verified: 3 → 12
scope verified: 6 → 29
assurance verified: 3 → 8
unit verified: 9 → 30
quarantine: 29 → 26

PERIOD SEMANTICS AFTER:
instant: 216
standalone: 0
YTD: 0
unresolved: 26

REVISION GROUPS: 7 total, 0 resolved, 7 UNKNOWN
TIMING: 4 A_EXACT_TIMESTAMP, 28 B_OFFICIAL_DATE_D1
CANONICAL_ROWS_WRITTEN: 0
FINANCIAL_FEATURES_WRITTEN: 0
```

Gate `PARTIAL` vì OCR cải thiện đáng kể document identity/scope/unit/linkage nhưng
vẫn còn 26 quarantines, 9 scope conflicts và Q2/Q3 duration chưa đủ evidence để gắn
`STANDALONE`/`YTD`. Bốn trang `LOW_CONFIDENCE` không được dùng làm semantic evidence;
raw PDF, R5 timing và 7 revision relations được giữ bất biến. Artifact:
`artifacts/financial_pit/fin-pit-2-r1-ocr-remediation-v1/`.

FIN-PIT-3 không được chạy trong session này. Nếu owner mở FIN-PIT-3 bằng session riêng,
scope phải được freeze theo verified subset; không được suy coverage cho toàn bounded pilot.

### FIN-PIT-2-R2 — Period semantics and scope conflict remediation

> **Bổ sung sau FIN-PIT-2-R1 PARTIAL — mục đích:** xử lý hai blocker semantic còn lại sau khi OCR đã cải thiện mạnh document coverage:  
> 1. chưa xác minh được Q2/Q3 là standalone hay YTD;  
> 2. còn 9 scope conflicts giữa consolidated/separate hoặc evidence scope chưa nhất quán.  
> Stage này chỉ remediation semantics; không canonicalize financial facts, không thay timing methodology và không tự mở FIN-PIT-3.

#### 1. Bối cảnh mở FIN-PIT-2-R2

FIN-PIT-2-R1 kết thúc với:

```text
STATUS = PARTIAL
```

Kết quả sau OCR:

```text
documents_reviewed = 32
documents_ocr_processed = 26
ocr_pages = 209

ocr_quality_pass = 205
ocr_low_confidence = 4

documents_classified:
6 → 32

linkage_verified:
6 → 27

linkage_ambiguous:
34 → 4

unit_verified:
9 → 30

scope_verified:
6 → 29

semantic_ready_reports:
3 → 6

fact_candidates:
220 → 242

semantic_ready_facts:
216 → 216

quarantine:
29 → 26
```

Timing vẫn được giữ nguyên:

```text
A_EXACT_TIMESTAMP = 4
B_OFFICIAL_DATE_D1 = 28
```

Revision:

```text
revision_groups = 7
revision_relation = UNKNOWN
```

Hai blocker chính còn lại:

```text
Q2/Q3 STANDALONE verified = 0
Q2/Q3 YTD verified        = 0

scope_conflicts = 9
```

Do đó FIN-PIT-2 chưa đủ semantic coverage để mở FIN-PIT-3 cho toàn bounded pilot.

#### 2. Mục tiêu của FIN-PIT-2-R2

R2 phải tập trung đúng hai mục tiêu:

```text
A. PERIOD SEMANTICS
B. SCOPE CONFLICT RESOLUTION
```

Không chạy lại toàn bộ OCR.

Không crawl thêm dữ liệu ngoài bounded pilot nếu không có evidence gap được preregistered rõ.

#### 3. Mục tiêu A — Period semantics

R2 phải xác định, trên từng statement/document/column:

```text
INSTANT
STANDALONE
YTD
FULL_YEAR
COMPARATIVE
UNKNOWN
```

Đặc biệt với Q2/Q3:

```text
Q2:
- 3 tháng → STANDALONE
- 6 tháng → YTD

Q3:
- 3 tháng / quarter-only → STANDALONE nếu document chứng minh
- 9 tháng → YTD
```

Không dùng global assumption theo quarter number.

#### 4. Evidence hierarchy cho period semantics

Ưu tiên evidence theo thứ tự:

1. exact column heading trong PDF/OCR;
2. statement heading;
3. explicit wording như:
   - `3 tháng kết thúc ngày...`;
   - `6 tháng đầu năm...`;
   - `9 tháng đầu năm...`;
4. comparative column heading;
5. notes trong cùng financial report;
6. accounting period description trong report cover/auditor section.

Không đủ để promote:

```text
- filename;
- quarter number;
- provider label Q2/Q3;
- period_end duy nhất;
- assumption từ loại statement;
- suy luận từ giá trị numeric.
```

#### 5. Statement-specific period policy

##### Balance sheet

Luôn xử lý như:

```text
duration_basis = INSTANT
```

chỉ khi as-of date được verify.

##### Income statement

Phải xác minh độc lập:

```text
STANDALONE
YTD
FULL_YEAR
UNKNOWN
```

##### Cash flow statement

Không mặc định giống income statement.

Phải kiểm tra wording riêng.

Thông thường có thể YTD, nhưng chỉ promote nếu document chứng minh.

#### 6. Column-level context

Mỗi financial column cần giữ tối thiểu:

```text
column_role
period_start
period_end
duration_basis
comparative_relation
source_heading
evidence_location
```

Ví dụ:

```text
CURRENT_3M
CURRENT_6M_YTD
PRIOR_3M
PRIOR_6M_YTD
OPENING_BALANCE
CLOSING_BALANCE
```

Nếu cùng document có cả standalone và YTD columns, phải giữ riêng.

#### 7. Derived standalone values

Không được tự động tính:

```text
Q2 standalone = H1 YTD - Q1
Q3 standalone = 9M YTD - H1 YTD
```

trong R2.

Nếu muốn dùng phép trừ YTD sau này phải có methodology riêng chứng minh:

```text
same scope
same unit
same taxonomy
same vintage compatibility
same statement context
```

R2 chỉ xác minh semantics của source columns hiện có.

#### 8. Mục tiêu B — Scope conflict remediation

R2 phải review đúng 9 scope conflicts hiện tại.

Scope chuẩn:

```text
CONSOLIDATED
SEPARATE
UNKNOWN
```

Phải xác minh bằng evidence trong document.

#### 9. Evidence hierarchy cho scope

Ưu tiên:

1. document/report title;
2. financial statement heading;
3. auditor/reviewer report;
4. company declaration inside report;
5. disclosure metadata nếu semantics rõ.

Không đủ để promote:

```text
- filename alone;
- provider default;
- ticker;
- report period;
- neighboring document scope.
```

#### 10. Scope conflict classification

Mỗi conflict phải được classify thành một trong:

```text
TRUE_CONSOLIDATED_VS_SEPARATE_PAIR
LINKAGE_MISMATCH
SUPPORTING_ATTACHMENT_SCOPE_MISMATCH
OCR_SCOPE_AMBIGUITY
DUPLICATE_SCOPE_LABEL
UNKNOWN
```

Nếu hai reports cùng ticker/period nhưng một consolidated, một separate:

```text
không phải conflict cần merge
```

mà phải giữ thành hai report identities riêng.

#### 11. Report identity key

R2 phải kiểm tra candidate identity tối thiểu theo:

```text
ticker
period
scope
statement/report type
document hash
vintage candidate
```

Không dùng key thiếu `scope`.

#### 12. Scope pair handling

Nếu tồn tại:

```text
FPT Q2 consolidated
FPT Q2 separate
```

thì output phải giữ:

```text
report_candidate_A.scope = CONSOLIDATED
report_candidate_B.scope = SEPARATE
```

Không merge facts.

Không average.

Không chọn một scope mặc định.

#### 13. OCR low-confidence pages

4 pages `LOW_CONFIDENCE` từ R1 phải được review riêng nếu chúng liên quan trực tiếp tới:

```text
period heading
scope
unit
assurance
```

Không cần OCR lại tất cả 209 pages.

Có thể:

```text
- rerun OCR với rotation/preprocessing phù hợp;
- inspect neighboring page;
- use alternate local OCR config.
```

Nhưng mọi rerun phải có provenance riêng.

#### 14. Semantic conflict matrix

R2 phải tạo machine-readable matrix cho từng unresolved candidate:

```text
candidate_id
ticker
document_hash
field
candidate_value_A
candidate_value_B
evidence_A
evidence_B
resolution
resolution_reason
confidence/status
```

Không được resolve chỉ dựa trên majority vote.

#### 15. Fact readiness recomputation

Sau khi period/scope được resolve, recompute:

```text
SEMANTIC_READY
```

cho report/facts bị ảnh hưởng.

Một fact chỉ được semantic-ready khi tối thiểu:

```text
statement_type verified
period context verified
scope verified
unit verified
document provenance present
column role verified
```

Nếu duration bắt buộc nhưng unresolved:

```text
SEMANTIC_READY = false
```

#### 16. Taxonomy

R2 không final-promote taxonomy.

Taxonomy chỉ được reevaluate nếu period/scope resolution thay đổi context.

Ví dụ:

```text
same label
different scope
```

phải vẫn giữ context riêng.

#### 17. Revision groups

7 revision groups tiếp tục:

```text
UNKNOWN
```

trừ khi period/scope review cung cấp official evidence đủ mạnh để phân biệt:

```text
same report different scope
supporting attachment
actual revision candidate
```

Hash khác không đủ để gọi revision.

#### 18. Timing preservation

Không thay:

```text
A_EXACT_TIMESTAMP
B_OFFICIAL_DATE_D1
```

Không tạo exact timestamp mới.

Không thay publication_date.

Không thay eligible_from.

#### 19. Output artifact

Đề xuất:

```text
artifacts/financial_pit/fin-pit-2-r2-period-scope-remediation-v1/
```

Tối thiểu:

```text
period_semantics_review.jsonl
scope_conflict_review.jsonl
column_contexts.jsonl

report_candidates_updated.jsonl
fact_candidates_updated.jsonl
document_linkage_updated.jsonl

revision_review_updated.jsonl
taxonomy_candidates_updated.jsonl

conflicts.jsonl
quarantine.jsonl

semantic_coverage_before_after.json
semantic_review_report.json

manifest.json
checksums.json
gate.json
```

#### 20. Before/after report

Bắt buộc so sánh:

```text
BEFORE R2
AFTER R2
```

Tối thiểu:

```text
period_verified
period_unresolved

standalone_verified
YTD_verified
instant_verified

scope_verified
scope_conflicts
scope_unknown

semantic_ready_reports
semantic_ready_facts

linkage_verified
linkage_ambiguous

quarantine_count
```

Phân tách theo:

```text
FPT
VNM
PVS
ACV
```

và:

```text
HOSE
HNX
UPCOM
```

#### 21. Gate

Status:

```text
PASS
PARTIAL
BLOCKED
FAIL
```

##### PASS

Khi:

- critical period semantics của bounded pilot đã đủ evidence;
- 9 scope conflicts được resolve hoặc fail-closed thành explicit unresolved records;
- không merge consolidated/separate;
- no global Q2/Q3 assumptions;
- provenance đầy đủ;
- no canonical rows;
- financial features remain false;
- verified subset đủ rõ để FIN-PIT-3 review.

PASS không yêu cầu mọi candidate đều usable.

##### PARTIAL

Khi:

- một subset period/scope đã resolve;
- vẫn còn unresolved subset;
- FIN-PIT-3 chỉ có thể mở trên verified subset được freeze rõ.

##### BLOCKED

Khi:

- source documents không chứa đủ period/scope evidence;
- OCR không thể phục hồi headings cần thiết;
- critical report patterns vẫn semantic unknown.

##### FAIL

Khi:

- Q2/Q3 bị gán theo assumption;
- scope bị merge sai;
- consolidated/separate bị trộn;
- provenance mất;
- revision bị fake-resolve;
- canonical data bị ghi ngoài stage.

#### 22. Điều kiện mở FIN-PIT-3

FIN-PIT-3 chỉ được mở nếu có một subset với:

```text
document linkage verified
period semantics verified
scope verified
unit verified
semantic provenance complete
```

Nếu toàn bounded pilot đạt:

```text
→ FIN-PIT-3 bounded pilot
```

Nếu chỉ subset đạt:

```text
→ freeze verified subset
→ FIN-PIT-3 chỉ review subset đó
```

Không được gọi subset result là market-wide readiness.

#### 23. Không được làm

FIN-PIT-2-R2 không được:

```text
- chạy FIN-PIT-3;
- canonicalize facts;
- final-promote taxonomy;
- bật financial features;
- scale market-wide;
- sửa R5 timing;
- tự tính standalone từ YTD subtraction;
- merge consolidated/separate;
- fake-resolve revision.
```

#### 24. Handoff format

```text
STAGE:
FIN-PIT-2-R2

STATUS:

SCOPE EXECUTED:
SCOPE NOT EXECUTED:

INPUT ARTIFACTS + HASHES:
OUTPUT ARTIFACTS + HASHES:

NETWORK REQUEST COUNT:

PERIOD REVIEW:
- candidates reviewed:
- instant:
- standalone:
- YTD:
- full_year:
- unresolved:

Q2/Q3:
- standalone verified:
- YTD verified:
- unresolved:

SCOPE REVIEW:
- conflicts reviewed:
- consolidated:
- separate:
- resolved conflicts:
- unresolved conflicts:

SEMANTIC_READY:
- reports before:
- reports after:
- facts before:
- facts after:

LINKAGE:
- verified:
- ambiguous:

REVISION GROUPS:
- total:
- resolved:
- unknown:

QUARANTINE:
CONFLICTS:

TIMING PRESERVATION:

CANONICAL_ROWS_WRITTEN:
must equal 0

FINANCIAL_FEATURES_WRITTEN:
must equal 0

TESTS RUN:
TEST RESULTS:

GATE REASONING:

VERIFIED SUBSET FOR FIN-PIT-3:

REMAINING LIMITS:

EXACT NEXT STAGE:
FIN-PIT-3 only if gate permits.
Do not execute it.

STOP CONDITION CONFIRMED:
YES
```

### FIN-PIT-3 — Evidence review và policy decision

Mục tiêu:

- áp checklist tại mục 8;
- kết luận phạm vi mapping nào đủ bằng chứng để implement canonical adapter.

AI/reviewer phải sinh:

- executive summary;
- coverage/conflict distributions;
- representative evidence cho Q1/Q2/Q3/Q4;
- source-by-source timing assessment;
- API/PDF agreement theo field;
- revision cases;
- đề xuất `APPROVE`, `CONDITIONAL`, `DEFER` hoặc `REJECT` cho từng policy;
- machine-readable decision matrix.

Kết luận stage:

- `PASS`: đủ evidence cho toàn phạm vi preregistered;
- `PARTIAL`: chỉ một tập statement/field/source pattern được approve;
- `BLOCKED`: cần source/evidence/quyền truy cập mới;
- `FAIL`: mapping tạo leakage, sai semantics hoặc không tái lập được.

Đây là `MANUAL_REVIEW_REQUIRED`. Reviewer có thể là AI do owner chỉ định, nhưng mọi
quyết định phải dẫn đến evidence cụ thể và được ghi vào `docs/DECISIONS.md` nếu thay
đổi contract/methodology. Không chấp nhận kết luận chỉ dựa trên confidence tự khai.

### FIN-PIT-4 — Schema và canonical contract decision

Chỉ bắt đầu nếu FIN-PIT-3 là `PASS` hoặc `PARTIAL` có phạm vi rõ.

Phải quyết định liệu schema hiện tại có biểu diễn được đồng thời:

- balance-sheet instant column;
- income-statement standalone duration;
- income-statement YTD duration;
- cash-flow YTD duration;
- comparative columns trong cùng document.

Hai phương án phải được đánh giá:

1. Tạo report/canonical context riêng cho mỗi period column được chọn.
2. Nâng schema fact với period/column context, ví dụ `fact_period_start`,
   `fact_period_end`, `duration_basis`, `column_role`.

Không chọn phương án chỉ vì dễ code. Quyết định phải xem identity, primary key,
reconciliation, snapshot selection và backward compatibility.

Nếu đổi contract:

- bump schema version;
- migrate assertion cũ thay vì xóa test;
- cập nhật `docs/DATA_CONTRACT.md`, `docs/METHODOLOGY.md`, `docs/DECISIONS.md`,
  `CHANGELOG.md`, config và tests;
- kiểm tra import/config/schema/Markdown links;
- ghi rõ `MANUAL_REVIEW_REQUIRED` trước implementation.

### FIN-PIT-5 — Canonical adapter và PIT verifier

Chỉ implement đúng mapping đã approve; phần deferred luôn fail-closed.

Yêu cầu adapter:

- provider identity, canonical identity và comparison key tách biệt;
- timezone-aware timing;
- immutable vintage, không overwrite;
- report/fact foreign keys hợp lệ;
- exact taxonomy version;
- source document hash bắt buộc;
- quarantine conflict/unknown revision;
- reconciliation theo field-level value và semantic key;
- không source priority/average chưa approved.

PIT verifier phải chứng minh:

- report chưa available không xuất hiện ở snapshot;
- report xuất hiện từ đúng first eligible decision time;
- revision tương lai không thay snapshot quá khứ;
- separate/consolidated không trộn;
- standalone/YTD không trộn;
- missing timing/timezone fail-closed;
- canonical output tái lập byte/hash từ immutable pilot input.

### FIN-PIT-6 — Representative scale gate

Mục tiêu:

- mở rộng có kiểm soát sang một mẫu đại diện lớn hơn, không phải toàn thị trường;
- đo coverage theo exchange, sector, scope, report type, PDF type và thời gian.

Quy mô chỉ được freeze sau FIN-PIT-5. Không dùng sample size tùy ý để che coverage
thấp. Stage này phải tái sử dụng exact adapter/policy versions và không thêm mapping
mới giữa run.

Gate phải báo riêng:

- acquisition coverage;
- document-linkage coverage;
- timing coverage;
- semantic/taxonomy coverage;
- conflict/quarantine rate;
- revision coverage;
- PIT-ready coverage.



### Coverage funnel bổ sung

> **Bổ sung từ GPT — mục đích:** không dùng số lượng raw rows hoặc số report crawl được như proxy cho research readiness.

Ngoài các coverage ở trên, report nên trình bày dạng funnel để nhìn thấy dữ liệu rơi ở stage nào:

```text
raw_reports
    ↓
document_linked
    ↓
semantic_ready
    ↓
timing_verified
    ↓
revision_safe
    ↓
pit_ready
```

Ví dụ:

```text
Total reports                  20,000
Document linked                18,500
Semantic ready                 17,200
Timing verified                14,000
Revision safe                  13,200
PIT ready                      13,000
```

Phải báo tỷ lệ theo exchange, sector, report type, scope và thời gian để tránh một aggregate coverage tốt che mất một phân khúc không usable.


Code existence hoặc nhiều rows không đồng nghĩa `PASS`.

### FIN-PIT-7 — Scaled acquisition

Chỉ chạy sau representative gate và owner approval phạm vi/risk.

Yêu cầu:

- immutable, resumable, sharded acquisition nếu cần;
- exact union/disjoint verification;
- bounded long-running local jobs;
- không continuously poll;
- source rate/access gates;
- raw redistribution policy;
- central offline consolidation;
- versioned canonical run và complete manifest/hash verification.

### FIN-PIT-8 — Financial feature approval

Mỗi feature là một approval riêng, sau khi PIT canonical data đủ coverage. Mỗi
definition phải có:

- canonical input item codes;
- formula và sign convention;
- scope policy;
- point-in-time rule;
- lookback/staleness policy;
- denominator/null/zero policy;
- industry-specific exclusions nếu có;
- paper/standard citation;
- feature registry metadata;
- unit, PIT và leakage tests.

Không mở đồng thời market cap, P/E, P/B, EPS-derived, Piotroski, Beneish hoặc Altman
chỉ vì raw facts đã tồn tại. Share-dependent feature vẫn cần `shares_history` hoặc
weighted-average shares có evidence riêng.



## 7A. Trạng thái readiness bổ sung cho report/fact

> **Bổ sung từ GPT — mục đích:** tránh nhầm giữa dữ liệu đã parse đúng nội dung và dữ liệu thực sự được phép dùng tại historical snapshot.

Mỗi report/fact cần tách tối thiểu hai trạng thái:

### `SEMANTIC_READY`

`true` khi các semantics cần thiết cho record đã được chứng minh trong phạm vi áp dụng, ví dụ:

- đúng statement type;
- đúng period/column context;
- đúng scope;
- đúng unit/sign;
- taxonomy mapping đủ evidence;
- provenance về document/page/region rõ ràng.

### `PIT_READY`

`true` chỉ khi record đã `SEMANTIC_READY` **và** đáp ứng timing/revision requirements để sử dụng ở historical decision time, tối thiểu:

- `available_at` đủ evidence;
- timezone/timing policy đã verify;
- report vintage đúng;
- future revision không back-propagate vào snapshot quá khứ;
- không trộn consolidated/separate hoặc standalone/YTD;
- record không ở trạng thái conflict/quarantine.

Ví dụ:

```text
Revenue       = verified
Net Income    = verified
Scope         = consolidated
Period        = verified
Unit          = verified

SEMANTIC_READY = true
available_at   = unknown
PIT_READY      = false
```

Record trên **không được dùng** cho historical snapshot dù nội dung tài chính đã parse đúng.

Có thể biểu diễn trạng thái machine-readable theo một trong hai cách:

```text
semantic_ready: true|false
pit_ready: true|false
```

hoặc reason-coded state nếu schema hiện tại cần chi tiết hơn. Quyết định schema cuối cùng vẫn thuộc FIN-PIT-4.


## 8. Checklist phê duyệt bắt buộc

### 8.1. Timing/PIT

- [ ] Timestamp đến từ disclosure/document cụ thể, không từ deadline.
- [ ] Timestamp có timezone hoặc source-timezone policy đã verify.
- [ ] `available_at >= published_at >= period_end`.
- [ ] `available_at <= decision_at` được test ở boundary trước/sau công bố.
- [ ] Không backdate `first_observed_at`.
- [ ] Timestamp CafeF không được promote nếu chỉ là filename/upload candidate.

### 8.2. Period semantics

- [ ] `period_start` và `period_end` có evidence trong tài liệu.
- [ ] Balance sheet được gắn `instant`.
- [ ] Mỗi duration column có khoảng thời gian riêng được chứng minh.
- [ ] Q2/Q3 không dùng global standalone/YTD assumption.
- [ ] KQKD và LCTT được xét riêng.
- [ ] Phép trừ YTD chỉ được dùng khi scope/unit/taxonomy/vintage tương thích.

### 8.3. Scope và assurance

- [ ] Consolidated/separate lấy từ tài liệu nguồn.
- [ ] API fact nối được tới đúng scope.
- [ ] Audited/reviewed/unaudited lấy từ assurance document.
- [ ] Không trộn scope hoặc assurance state.

### 8.4. Identity và revision

- [ ] Provider document ID/URL được giữ nguyên.
- [ ] Canonical report ID chỉ sinh sau semantic normalization.
- [ ] Comparison key đủ period/scope/revision context.
- [ ] Mọi document có SHA-256.
- [ ] File mới không overwrite file cũ.
- [ ] Hash khác không tự động đồng nghĩa revision.
- [ ] Unknown revision relation bị quarantine.

### 8.5. Fact và taxonomy

- [ ] Raw label/value/unit/sign được giữ.
- [ ] Mapping ưu tiên item code + statement context.
- [ ] Không fuzzy-promote.
- [ ] `Nợ ngắn hạn` không mặc định là short-term debt.
- [ ] `Lợi nhuận hoạt động` không mặc định là EBIT.
- [ ] CapEx/EPS/share-dependent item chưa đủ evidence bị defer.
- [ ] Null không đổi thành zero.
- [ ] API/PDF conflict không được average.

### 8.6. Reproducibility và access

- [ ] Raw artifact immutable và hash-verified.
- [ ] Config/universe/job plan/code version được freeze.
- [ ] Dry-run là zero-network.
- [ ] Real acquisition cần explicit execute.
- [ ] Không bypass access control.
- [ ] Request nằm trong bounds/rate policy.
- [ ] Offline replay không gọi network.
- [ ] Raw redistribution không vượt quyền được chấp nhận.

Nếu một checkbox bắt buộc không đạt, record hoặc mapping liên quan không được promote.

## 9. Test plan

### Unit tests

- request/config bounds và pagination;
- content hash, immutable write và resume guard;
- date/timezone parsing;
- period-column classification;
- unit/sign parsing;
- document linkage;
- taxonomy exact mapping;
- revision candidate handling;
- quarantine reason codes;
- PIT boundary selection.

### Integration tests

- raw CafeF summary → linked document candidate;
- disclosure timestamp → report timing candidate;
- PDF → report/fact candidates với page provenance;
- API/PDF conflict → quarantine;
- report/facts → schema validation;
- multiple vintages → snapshot-correct selection;
- consolidated/separate isolation;
- standalone/YTD isolation.

### Regression tests

- giữ assertion cũ của normalization/PIT/reconciliation;
- financial workstream không thay market C8/M2 artifacts;
- `financial_features_allowed=false` cho đến FIN-PIT-8;
- source/access failures tiếp tục fail-closed;
- JSON configs/schemas parse được;
- legacy imports cần giữ không bị phá.

### Repository gates khi có code change

Chạy targeted tests cho subsystem bị ảnh hưởng và:

```powershell
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

Nếu thay pipeline, chạy thêm:

```powershell
.venv\Scripts\python.exe run.py --config configs/data/synthetic_smoke.example.json
```

Full repository suite chỉ chạy khi stage/code/schema/data/research change warrant;
không lặp full suite cho documentation-only stage.

## 10. Review matrix và quyền quyết định

| Loại quyết định | AI/reviewer được kết luận | Owner action |
|---|---|---|
| Field có evidence rõ, test pass | Approve theo policy đã freeze | Không cần duyệt từng row |
| Mapping thiếu/mâu thuẫn evidence | Defer/Reject/Quarantine | Không cần ép lựa chọn |
| Thay schema/primary key | Đề xuất + impact analysis | Approval bắt buộc |
| Chọn source hierarchy mới | Đề xuất từ evidence | Approval bắt buộc |
| Chấp nhận source/right risk mới | Không tự mở rộng | Approval bắt buộc |
| Mở crawl representative/scaled | Chỉ sau gate | Approval phạm vi/execution |
| Bật financial feature | Đề xuất riêng từng feature | Approval methodology |

AI reviewer có thể thực hiện technical approval thay owner khi owner chỉ định, nhưng
không được biến thiếu evidence thành approval. Kết luận hợp lệ phải dẫn đến raw
artifact, source location, test và policy version.

## 11. Mẫu handoff sau mỗi stage

```text
STAGE:
STATUS: PASS | PARTIAL | BLOCKED | FAIL | MANUAL_REVIEW_REQUIRED

SCOPE EXECUTED:
SCOPE NOT EXECUTED:

INPUT ARTIFACTS + HASHES:
OUTPUT ARTIFACTS + HASHES:
NETWORK REQUEST COUNT:

KEY FINDINGS:
QUARANTINE/CONFLICT COUNTS:
TESTS RUN:
TEST RESULTS:

POLICY DECISIONS PROPOSED:
MANUAL DECISIONS REQUIRED:
REMAINING LIMITS:

EXACT NEXT STAGE:
STOP CONDITION CONFIRMED: YES
```

## 12. Điều kiện hoàn tất workstream

Financial PIT workstream chỉ được coi là complete khi:

- canonical report/fact contract được approve và version hóa;
- representative gate chứng minh coverage đủ cho phạm vi tuyên bố;
- immutable raw/canonical lineage tái lập được offline;
- timing, period, scope, revision và taxonomy tests PASS;
- unknown/conflict records vẫn quarantine;
- không có look-ahead ở PIT boundary tests;
- rights/risk label phù hợp với mục đích sử dụng;
- financial feature vẫn tắt trừ các definition đã được approve riêng;
- documentation, decisions, changelog, config và tests đồng bộ.

Hoàn tất workstream không tự động làm strict `research_ready=true`. Historical identity,
sample-density policy và các gate research khác vẫn phải được giải quyết độc lập.
