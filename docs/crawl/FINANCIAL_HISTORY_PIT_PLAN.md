# Plan financial lịch sử và PIT phục vụ market 10 năm, M3 backtest

**Execution55 — lịch sử đã gom:** data221→59roots, reports57→13. [Archive vàrestore](../../artifacts/archives/financial-history-20261023/README.md). Giữ dependency/control của dataset1.172mã; M2chỉ đọc handoff hiệnhành. Phân cụm chưa chạy.

**Cleanup54 — cache cũ đã lưu lạnh:** 102,504candidatefiles từbốn batch được chuyểnZIPđãverify, raw/receipts/journals giữtrực tiếp. [Guide restore](../../artifacts/archives/financial-cache-20261023/README.md). Chỉdùng [handoff mới nhất](../../data/handoffs/financial-reference-2016-2025/README.md) choM2; dataset1.172full10khôngđổi, chưa phâncụm. Fullhistoricalreplay cóthểcầnrestorecache.

**Execution53 — cleanup trước phân cụm:** đã gỡ2.889file, lưu9reportfolders lịch sử
và74scratchhelpers vàoZIPđãverify; khôngđổi raw/canonical/dataset/counters.
Mở [bộ bàn giao tên dễ tìm](../../data/handoffs/financial-reference-2016-2025/README.md)
và [bảng lệnh](../../scripts/README.md). Dataset50vẫn1.172full10; M2chưa chạy.
Reporttổng mục2.26ghi chi tiết vàkhôi phục. Khôngrename code/configđangđượcpin.

**Execution52 — rà soát bổ sung23/10:** đã review95one-gap trong cache hai nguồn,
chưa nhận thêm mã;4leads API2021/IPA2021/CAP2022/SBD2024 quaQA số học nhưng còn
multiple partitions. [Report52](../../artifacts/reports/financial-one-gap-review-v1/report.md).
Dataset50bên dưới vẫn mới nhất,1.172full10.0network/PDF/OCR. Ưu tiên tiếp theo là
baselinefinancial-only thăm dò trêncohort đãđủ; sáucore ratios đãcó, không đồng
nghĩa EPS/P/E/P/B/F/M/Z hoặcM2/M3hoàn tất. Không tự mởPDFcampaign.

**Execution50 hiện hành (23/10/2026):**1.172full10 annual2016–2025 /13.529core-ratio reference rows; +170mã/+961rows,12.568baseline rows nguyên vẹn. Đã thử hết2.444Regular annual gap cases qua49+50; còn761held/257Regular,95mã9/10 và93candidates ngoài schema. [Report50](../../artifacts/reports/financial-dstock-remaining-v1/report.md), [master](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [cohort delivery](../../artifacts/reports/financial-dstock-remaining-v1/delivery-result-ref.json).47targeted tests/independentPASS;0PDF/OCR;worker đã dừng. Warm-up/quarterly/originalsixfamilies/PIT/M3 chưa hoàn tất.

Ngày cập nhật:23/10/2026. Trạng thái:Execution50 scope API đã hoàn tất; financial delivery/PIT/M3 vẫn PARTIAL. Các execution dưới là snapshots lịch sử, không phải worker hiện hành.

**Report tổng cần đọc/cập nhật mỗi lượt:** [FINANCIAL_DATA_MASTER_REPORT.md](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md). Owner yêu cầu một điểm theo dõi liên tục cho cả quá trình: mỗi execution phải cập nhật hiện trạng, before/after, giai đoạn mới, blockers, PDF backlog và latest result links trong report này. Các report/run đã seal giữ nguyên; report tổng là live documentation, không đưa vào frozen experiment inputs.

Hiện có13.529annual core-ratio reference rows/1.172full10, không đồng nghĩa đủ EPS/P/E/P/B/F/M/Z/PIT. Pilot5 giữ29/30;VNM F còn thiếu basis. Không sửa raw hoặc mở research gates.

## 1. Mục tiêu, range và hai mức bàn giao

| Hạng mục | Hợp đồng |
|---|---|
| Market tiêu thụ | Monthly snapshots trong 2016–2025, daily market theo [plan market](MARKET_HISTORY10Y_1500_PLAN.md) |
| Financial acquisition | Annual + quarterly 2013–2025; bổ sung closing assets cuối 2012 khi dependency cần |
| Universe | Cùng registry market; theo issuer để không tải lặp do đổi mã/chuyển sàn |
| Số lượng | Phục vụ universe mục tiêu ≥1.500 cổ phiếu; số issuer có thể khác số securities |
| Reference delivery | Raw/candidates/accepted facts và mọi applicable metrics đủ inputs; ghi temporal limitations |
| PIT delivery | Tập đủ semantics, vintage, publication/availability và historical dependencies tại từng snapshot |
| M3 | Bàn giao PIT coverage và blockers; chưa chạy backtest hoặc mở financial clustering |

Warm-up tính theo dependency graph: đầu 2016 có thể mới dùng annual FY2014;
F-score so ROA các năm trước cần thêm closing assets 2012. Không mặc định FY2015
đã công bố tại đầu 2016. Mã lịch sử ngắn chỉ lấy actual periods, thiếu giữ reason.
Quarterly có 52 quý trong 2013–2025 nhưng không tuyên bố mọi issuer công bố đủ.
Nguồn có period ngoài target vẫn giữ provenance, không đếm là target coverage.

Baseline clustering giữ market-only; financial dùng phân tích đặc điểm cụm trước.
Financial missing không loại market row hợp lệ. Mixed-feature clustering cần
feature/protocol riêng; không chọn subset bằng holdout return hoặc Sharpe.

## 2. Registry dùng chung và bằng chứng hiện tại

Đọc và cập nhật [registry mã duy nhất](../../configs/data/securities_collection_registry_v1.csv).
Data dictionary và quy tắc khóa nằm ở [mục 3 plan market](MARKET_HISTORY10Y_1500_PLAN.md#3-registry-contract-và-phối-hợp-team).
Không copy ticker list riêng. Có 1.522 current discovery candidates, trong đó
952 đã qua market C8 và 148 C7 deferred; đây chưa phải historical census.

`issuer_id`/canonical `security_id` ban đầu để trống, provider ID giữ
`legacy_security_id`. `registry_id` là provisional inventory key, không phải
identity đã nghiệm thu. Thu financial một lần theo issuer đã resolve rồi liên kết
đúng security interval; chưa resolve thì cache candidate riêng, không gộp ticker.

Registry tách market/financial statuses, observed periods, verification, PIT,
next actions, owners và batch IDs. Mỗi assignment pin registry hash/version +
domain + IDs + range + batch. Một maintainer merge, không nhận trùng cùng
domain/issuer/range; market và financial có thể chạy độc lập qua scheduler chung.
Ban đầu owner/batch trống; selection `PLANNED_PENDING_IDENTITY_RANGE_CHECK`.

SHA256 registry lúc bàn giao v1:
`6d34d2262c7083d1f613046ea777a2a9f1d57d25a2aa3267d10e9fa8c1a877b0`.

Inventory financial v1 kiểm các local `coverage.csv`, `candidates.jsonl` và pinned
[pilot5 result](../../data/financial/pilot5_completion_v1/results/ee79bf4278f3ae944d02/report.md).
Source path/hash nằm trong từng registry row. Period presence không chứng nhận đủ
statement, source accuracy hoặc PIT. Other reviews, runs và cold archives chưa
inventory toàn diện; không coi thiếu local export là `NOT_CRAWLED`, không ghi
zero accepted metrics khi chưa kiểm. Các manifest/exports cũ chỉ đọc, không sửa.

Đã quét 15 coverage exports và 14 candidate JSONL exports. Registry có năm mã
pilot5 reference, 50 mã khác có local candidate exports và 1.467 mã chưa thấy
match trong các exports đã quét. Nhóm cuối vẫn `NOT_INVENTORIED`, không khẳng định
chưa crawl. Numeric review/PIT ngoài pinned pilot chưa được đánh giá lại.

Pilot5: BRC/FPT/MWG/GMD 6/6 families, VNM 5/6. Scope count là FY2025 reference,
P/E và P/B dùng giá **22/04/2026**, P/B book 31/12/2025; không phải historical
snapshot cuối 2025 hoặc current TTM. Ngoài pilot5, accepted metric count để trống
đến khi kiểm đúng reviewed result; không phủ nhận legacy review khác.

## 3. Nguồn, raw contract và QA tự động

### 3.1. Flow hai nguồn API hiện hành — cập nhật 23/10/2026

Hai nguồn structured đã dùng là **CafeF và DStock/VNDIRECT**. CafeF cung cấp
baseline acquisition/history; DStock bổ sung các mã–năm còn thiếu hoặc chưa qua
QA của baseline. Đây là mô tả flow đã thực thi, không mở campaign network mới.
Source boundary CafeF hiện có vẫn được giữ; không tự gọi lại nguồn đang bị chặn.

```text
registry + cache/raw CafeF và các reference đã review
→ chuẩn hóa riêng từng nguồn → QA và coverage baseline
→ lấy danh sách mã–năm chưa có row đạt yêu cầu
→ DStock annual API → mapping/model membership → QA từng complete vector
→ giữ nguyên baseline + thêm mã–năm mới đạt QA, giữ source provenance
→ tính core ratios → coverage/cohorts reference + held queue
→ review API/cache/scope → đề xuất PDF có số lượng → owner duyệt trước tải/OCR
```

Quy tắc đã thực thi ở49–50:

- Không thay baseline row đã có; không ghép từng field CafeF/DStock để tạo một
  vector mới. Mỗi row DStock bổ sung phải đủ input từ chính DStock, qua12
  accounting/finance checks và3cash totals/stock checks, giữ precision đã pin.
- Không lấy trung bình hai nguồn, không tự ưu tiên một giá trị khi conflict.
  Bổ sung complete reference vector chưa phải canonical source-priority policy.
- Đối chiếu từng field chỉ khi cùng issuer, fiscal period, annual/quarter/YTD,
  đơn vị, hợp nhất/riêng lẻ và report vintage. Hai nguồn đều có số không tự
  chứng minh cùng semantics, đúng số hoặc đủ publication evidence/PIT.
- DStock49–50 chỉ bổ sung annual2016–2025 của Regular; không coi warm-up2013–2015,
  quarterly hoặc Bank/Securities/UNKNOWN đã được hoàn thiện qua nguồn thứ hai.
- Giữ source URL/hash, raw receipts, mapping/QA version, budget counters,
  deadlines và checkpoint riêng. Resume không reset; không bypass access controls.

Kết quả đã pin:13.529rows, gồm1.683DStock complete-vector rows,11.835legacy API
baseline rows và11reference rows PDF/HTML. Có1.172mã đủ10annualperiods; còn761
held kỳ của257Regular candidates, cộng93candidates ngoài Regular schema.
**Đã bổ sung từ hai nguồn vẫn chưa đủ theo policy hiện hành**; chưa có kết luận
exhaustive rằng từng field trong761kỳ đều vắng ở cả hai nguồn. Chưa chạy repair
ghép field, chưa reconcile toàn bộ overlap, chưa xác nhận tất cả kỳ thiếu thực sự
có tồn tại trong lịch sử doanh nghiệp.

Queue primary761kỳ (không cộng các reasons overlap):550không có observations
trong truy vấn DStock;103doanh thu không dương;36thiếu inputs;33chưa xác định
model membership/scope;39cần review QA/scope. Số kỳ không phải số mã hoặc sốPDF.
Tiếp theo ưu tiên95mã thiếu1kỳ: kiểm history/fiscal scope, so lại cached API theo
field tương thích, phân loại conflict/missing/not-applicable rồi mới đề xuất tài liệu.
Mọi cross-source field repair về sau phải có policy/version và kiểm chứng riêng;
chưa được dùng để thay counts của run đã seal.

Xem [report tổng — cập nhật flow hai nguồn](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md#224-làm-rõ-flow-hai-nguồn-api--execution51-tài-liệu-2310),
[report50](../../artifacts/reports/financial-dstock-remaining-v1/report.md) và
[thống kê held queue](../../artifacts/reports/financial-dstock-remaining-v1/handoff-summary.json).

### 3.2. Routes, raw contract và QA

Primary structured routes theo [CafeF source note](sources/CAFEF.md):
CDKT v2 `GetReportCDKT`, KQKD v1 `GetReportDetail`, LCTT v1 `GetReportLCTT`.
Giữ NAM/QUY/LUYKE, group/reportType, pageSize=4 và paging độc lập từng group.
Route/ngành chưa live-validated phải bounded probe trước scale. Reported ratios
chỉ đối chiếu, không thay recompute. Source khác chỉ dùng khi route được phép và
semantics đã kiểm; không auto fallback hoặc source priority chưa duyệt.

```text
shared registry + issuer mapping + verified cache
→ structured annual/quarter + disclosure catalogue
→ raw immutable → candidates → QA/coverage/missing dependencies
→ ranked document queue → PDF text → selected OCR → review/accepted facts
→ reference metrics + date-PIT snapshots → seal/verify
```

API/catalogue checkpoint độc lập PDF/OCR. Missing notes không chặn acquisition
issuer khác. Reuse verified cache trước request mới, không reset old campaigns.

Fact contract giữ issuer, provider/report/document identity, source URL/hash,
statement/code/label/group/template fingerprint, fiscal start/end, instant/duration,
annual/quarter/YTD, unit/currency, scope, framework, audit/revision, publication
evidence và mapping/extraction/review versions. Không coi labels UI hoặc magnitude
là bằng chứng multiplier; missing/dash không thành zero.

Giữ full raw ba statements; normalize fields phục vụ sáu families trước. Sector
mapping riêng cho banks/securities/insurance; unsupported formula trả
`NOT_APPLICABLE` khi có evidence, chưa phân loại trả `UNKNOWN`, không ép Regular.

QA gồm schema/template changes, unit/period/scope/framework, accounting identities
khi đủ taxonomy, parent/subtotal, signs, same-period annual/Q4 khi compatible,
YTD reconciliation, large changes và adjacent-row displacement. 5× change chỉ
alert khi base khác zero, không tự loại. Tolerance từ disclosed rounding; exact
integer VND không tùy ý cho tolerance. BRC/VNM annual debt-row regression phải
phát hiện kể cả A=L+E vẫn đúng; không dịch index/hard-code ticker để chữa.

## 4. PDF/OCR chọn lọc và kiểm chứng

Catalogue/publication metadata thu cả khi API QA PASS: số học đúng không chứng
minh thời điểm công bố. Ưu tiên tài liệu có đúng issuer/period/scope/framework;
standalone BCTC trước BCTN dài nếu cùng evidence need. Tên file không là period
hoặc publication proof. PDF doanh nghiệp vẫn phải kiểm units, version, comparative
restatement và interpretation; không mặc định mọi ô đọc từ PDF đều đã accepted.

Queue ưu tiên: systemic mapping/template errors → bổ sung nhiều metrics → mandatory
missing input → audit API-pass sample. Tie-break estimated cost tăng dần rồi
issuer/period/URL. Cache URL/content SHA256, dedup PDF và dùng lại cho nhiều fields.

Text extraction theo trang trước, phân loại mixed/text/scan. Dùng TOC/heading/code/
note anchors để chọn trang. OCR CPU Tesseract `vie+eng`, output text + TSV/bboxes;
pin runtime/models, doctor kiểm executable trước chạy. Không bypass Windows OCR
policy hoặc upload cloud. Tối đa 40 trang OCR mới/PDF tính cả tìm trang; chạm cap
ghi `DEFERRED_BUDGET`, không kết luận note không tồn tại. Template chỉ reuse khi
fingerprint/layout compatible. OCR confidence là ưu tiên review, không acceptance.

Review-import cần source SHA, physical page/bbox, kỳ/unit/scope và reviewed value.
Candidate chỉ thành accepted fact theo policy, không nhờ OCR score. Audit ≥5%
issuer mới/batch, ít nhất 3 hoặc toàn batch nếu nhỏ hơn; mỗi issuer một annual và
một quarterly khi có tài liệu. Rotate sàn/era/template với seed pin. Thiếu audit
document ghi gap; không chứng nhận unsampled facts hoặc mở strict acceptance.

## 5. PIT, revision và các chỉ số

Theo [financial feature contract](../research/FINANCIAL_FEATURE_CONTRACT.md) và
[date-PIT policy](../../configs/data/financial_date_pit_v1.json):

- Timestamp input dùng `available_at <= decision_at`. DATE_ONLY dùng phiên exchange
  quan sát được đầu tiên **sau** publication date; calendar thiếu coverage thì giữ blocker.
- Publication phải liên kết đúng document/version. Không suy từ filename, PDF
  metadata, ngày ký/kiểm toán, provider ObjectId hoặc fetched_at.
- Giữ tất cả vintages, không dùng latest revised comparative áp ngược lịch sử.
  Nguồn chỉ còn số mới mà không khôi phục được vintage cũ thì reference-only/PIT gap.
- Mọi comparator và input notes cũng phải đủ availability. Hiệu YTD chỉ khi
  scope/framework/currency/fiscal basis/vintage compatible; usable date bằng
  input muộn nhất. CFO 9 tháng không gán thành Q3.
- As-of join giữ latest **eligible** fact đến bản mới; không lấp kỳ báo cáo thiếu.
  Xuất tuổi dữ liệu; không tự thêm stale threshold để đổi methodology.

| Chỉ số | Quy tắc |
|---|---|
| EPS | Basic/diluted riêng, numerator có điều chỉnh + weighted shares; TTM cần compatible share basis và corporate actions, không cộng bốn EPS khác basis |
| P/E | Raw price tại snapshot / EPS TTM compatible; EPS≤0 trả null/reason; không dùng current shares backfill |
| P/B | Parent common equity và historical common shares phù hợp; không dùng group equity gồm NCI |
| F | Annual, chỉ total khi 9/9 signals known; giữ named VAS variant và original-maturity current portion |
| M | Annual VAS M8 sensitivity hiện có; công khai denominator discrepancy, không gọi strict reproduction hoặc fraud threshold |
| Z | Annual EM Z″ +3,25 với book equity; quarterly/TTM là variant review riêng, không tự phụ thuộc daily market cap |

P/E/P/B tính tại monthly snapshot là đủ cho v1; không cần lưu hàng tỷ daily ratios.
FY chỉ công bố năm sau có thể xuất reference ex-post, không vào snapshot trước
publication. Giữ reference output khác PIT output; missing một family không chặn
family đủ inputs. Không đổi formula để đạt 30/30 VNM hoặc gán financial scores cho
institutions khi không phù hợp. Không liên hệ IR thành bước chuẩn của flow.

## 6. Stages, giao diện và ngân sách

| Stage | Đầu ra/gate |
|---|---|
| F0 Offline | Registry/issuer graph, dependencies, cache/source boundary inventory, config, doctor/dry-run 0 network |
| F1 Regression | Replay pilot5 giữ 29 metrics/gap VNM và false gates; không acquisition |
| F2 Pilot5 history | Task coverage toàn 2013–2025 + auxiliary 2012; không bắt mọi metric đầy đủ |
| F3 Total20 | Diverse exchange/sector/template; annual+quarter/YTD/PIT vertical slices, cost projection |
| F4 Total50→100 | Audit false negatives, OCR cost, crash/resume và verification |
| F5 Batch≤100 | API/catalogue trước, documents queue xử lý theo priority; tự nối sau engineering gate |
| F6 Consolidate | Reference dataset, PIT eligible subset và M3 dependency report |

Chọn thêm issuer bằng exchange/sector/template categories có evidence rồi
registry_id tăng dần, không chọn bằng portfolio outcomes. Thiếu category phải
báo trước scale. Không truyền universe mới cho frozen pilot/trial50 runner.

**Giao diện F0–F2 đã triển khai:**
[PowerShell](../../scripts/financial_history_pit.ps1) / [Python CLI](../../scripts/financial_history_pit.py),
[config pilot5](../../configs/data/financial_history_pit_v1.json).
Actions hiện có: `doctor|plan|regression|run|resume|qa|report|verify`;
`-MaxNetworkRequests` giới hạn wave, `-Network` chỉ dùng cho run/resume.
`plan`/`verify` không network. Logic ở modules, PowerShell chỉ orchestrate.
Các actions `documents|ocr|review-import|compute|snapshots` vẫn là phần phải triển
khai sau source/candidate gates; không gọi metrics baseline là historical compute.

| Campaign đầu, shared với market | Cap |
|---|---|
| Frozen universe | ≤2.000 candidates; vượt ghi backlog/new campaign |
| Network | Global concurrency 1; financial/metadata ≥2 giây, market ≥3 giây |
| Attempts / timeout | ≤2 attempts/logical task, transient only; API 20 giây, PDF 25 giây |
| Structured/issuer | ≤240 API tasks +80 catalogue tasks |
| Market/security | ≤200 price pages +60 identity/event tasks |
| Discovery/benchmark chung | ≤5.000 logical tasks |
| PDF | ≤50 mới/batch, ≤1.000/campaign, ≤25 MB/file |
| OCR | ≤1.000 trang mới/batch, ≤12.000/campaign, ≤40/PDF |
| Structured response | ≤5 MB/response |
| New artifacts / disk floor | ≤50 GB / ≥30 GB trống |
| Deadline tuyệt đối | 72 giờ/batch, 90 ngày/campaign từ created_at |

Global structured cap =260×frozen securities +320×distinct issuers +5.000;
transport cap =2×logical cap, PDF attempts riêng ≤2×download cap. Resolve issuer
count trước freeze, không dùng blank issuer_id để gộp mọi công ty thành một.
Reserve requests/bytes trước I/O, journals bền vững. Hết cap/deadline thì seal
queue `DEFERRED_BUDGET`; resume không reset counters/created_at/deadline.

Import existing source boundaries. 401/403/429/challenge latch nguồn tương ứng,
không retry hoặc đổi client/hostname/cookies để vượt. Nguồn độc lập được phép và
offline có thể tiếp tục. Chưa có quyền gửi email/IR; không gửi thông tin ra ngoài.

Gate batch: tất cả tasks accounted, hash/replay/resume PASS, không accepted key/
identity conflict; failed-after-retry ≤2% transport attempts, schema/parser failure
≤1% successful responses; không critical accepted unit/period/scope/template error;
audit, disk/deadline/budget PASS. Denominator 0 báo N/A. Critical audit finding
quarantine mapping cohort, pause promotion và re-QA bằng version mới. Missing
public data/N/A/backlog không tự làm engineering FAIL nhưng giảm delivery/PIT coverage.

## 7. Đầu ra, tests và tiêu chí hoàn tất

Mỗi batch có manifest/hash inventory, task/checkpoint journal, raw/candidates,
accepted facts, `financial_coverage.csv`, `anomalies.csv`, `missing_inputs.csv`,
`document_queue.csv`, `metrics.csv`, PIT snapshots và `batch_summary.json`.
Reference metrics giữ variant, input dependencies, price/book dates, temporal
status, verification/PIT flags và missing reason. Không impute hoặc average sources.

Tests: BRC/VNM row shift dù totals cân; quarterly conflicts, independent group
paging, CFO YTD, fiscal exceptions, unknown units, scope/framework mismatch,
revision/late publication/comparator availability, bonus/split/share basis, text/
scan/mixed PDF, rotated/negative/comparative columns, bbox/template mismatch,
dedup/review/OCR cap, missing→null, source boundaries và crash/resume.
Future append/revision phải không đổi snapshot quá khứ đã seal. Thực thi targeted
tests + compile/synthetic smoke khi đổi pipeline; full gate trước promotion.
Giữ old assertions, báo riêng known M2-PREP frozen-document hash failure.

**Reference delivery PASS:** mọi issuer/kỳ mục tiêu có task status, mọi applicable
metric có đủ accepted dependencies đã tính, còn thiếu có reason và source queue.
Không đòi sáu families trên mọi ngành và không dùng task-attempt count thay data count.

**PIT delivery:** xuất tập đủ điều kiện cùng coverage theo tháng/issuer/family,
không đặt số mã PIT tối thiểu tùy ý để tuyên bố full readiness. Full-universe PIT
vẫn `PARTIAL` nếu còn gaps. M3 financial readiness đánh giá trên exact subset và
protocol freeze riêng, không tự mở từ reference PASS. M3 market-only không buộc
chờ mọi financial metric hoàn tất.

Các thay đổi acceptance/methodology-sensitive cần concrete evidence proposal và
`MANUAL_REVIEW_REQUIRED` theo [AGENTS.md](../../AGENTS.md). Không thay market-only
protocol, final research universe hoặc bật backtest trong acquisition workstream.

## 8. Execution hiện hành — pilot5 F0/F1/F2

Runner/config mới chỉ cho BRC/FPT/MWG/GMD/VNM, chưa nhận universe1500 trực tiếp.
F0 đã freeze [contract](../../data/financial/history_pit_v1/contract.json), registry
hash, code pins, dependencies, 1.100 planned request tasks và source-boundary inventory.
Provider partitions vẫn provisional, không gộp blank issuer IDs. Có 19 legacy
journals được audit, 35 cache URLs hợp lệ, 0 cache/boundary audit errors. Conservative
host latch giữ `cafef.vn` và `fiin-core.ssi.com.vn`; API host `apiweb.cafef.vn`
không có latch đã nhập. Catalogue đang deferred, không thử lại EPS/SSI bằng client khác.
Tesseract chưa có trên PATH; không chặn acquisition API nhưng OCR chưa chạy.

Ghi chú cập nhật: trạng thái doctor ở F0 trên là snapshot lịch sử. CPU Tesseract
đã được thiết lập trong project tại mục10; không cần executable trên system PATH.

F1 regression PASS: baseline metrics SHA
`fd875c1ac4a451d9f98b984c18e5952a388d99c6807a27f8e56ca53548b8ad1b`, 29/30 giữ nguyên.
Worker đã kết thúc: 563 new requests/563 attempts, 5.313.164 bytes, 27 cache hits;
không pending, boundary/budget_stop false. 1.100 task statuses gồm 563 ACQUIRED,
27 CACHED, 505 NOT_REQUIRED_AFTER_SERIES_STOP và 5 ACCESS_BLOCKED_IMPORTED.
Không thử lại catalogue host đã latch. [Checkpoint cuối đã verify](../../data/financial/history_pit_v1/reports/4bf06a5671299d42c73f/report.md)
có 71.073 cells, 980 coverage slots: 918 main candidate groups present, 5 auxiliary,
57 không có candidate trong pages đã lấy. Không diễn giải thành không công bố.
`metrics.csv` vẫn là FY2025 reference, chưa tính mới cho lịch sử 13 năm.

[Worker launch/assignment](../../data/financial/history_pit_v1/worker-launch.json) là
bằng chứng khởi chạy cũ; [stdout](../../data/financial/history_pit_v1/worker.stdout.log)
đã có kết quả cuối, không còn worker acquisition active. Registry v1/contract/code
pins không sửa; resume không có việc pending và không được reset budget/latches.

## 9. QA offline và handoff bổ sung chọn lọc

Lớp QA riêng [PowerShell](../../scripts/financial_history_qa.ps1),
[config](../../configs/data/financial_history_qa_v1.json),
[report đã seal — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/1692b3eb579b426c1e2f/report.md).
Không sửa frozen acquisition parser hoặc raw. Run pin input manifest, raw hashes,
reviewed-inputs và code; verify replay deterministic và phát hiện tamper.

- 1.161 unmapped cells đều là zero placeholder của group heading, chứng minh bằng
  `group.code + group.number` của đúng raw template và không phải child row. Giữ raw,
  phân loại STRUCTURAL_GROUP_HEADER_ZERO; không coi là financial fact. Còn 69.912
  nonstructural candidates, không có unexplained orphan. Counts này gồm năm quan sát
  ngoài target; diagnostics giới hạn 2012–2025.
- 7.890 exact code/label diagnostic mappings; không map bằng vị trí hoặc mặc định
  CafeF code bằng mã VAS. Có 1.551 raw accounting equalities, 95 raw differences;
  0 conflicting observation keys trong key partitions đang kiểm.
- 8.645 phép so closing annual–Q4: 6.652 raw equalities, 1.993 raw differences.
  Giữ riêng provider types, unit/scope/vintage chưa verified; khác nhau chưa chứng
  minh provider sai. Detector nhiều distinct nonzero neighbor matches bắt đúng
  BRC/VNM FY2025, chỉ flag, không dịch hàng. Tổng cân không loại trừ lỗi này.
- 150 so sánh với reviewed PDF inputs: 138 raw same-unit hypothesis matches,
  12 conflicts. Đây không phải acceptance, cũng không tự suy multiplier hoặc scope.
- [Queue 90 issuer-periods — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/1692b3eb579b426c1e2f/document_queue.json):
  6 priority1, 84 priority2; 13 có cache PDF candidates cần kiểm đúng period/vintage.
  Queue không phải lệnh tải 90 PDF. Ưu tiên dùng lại cache cho 6 FY conflicts rồi
  bổ sung missing periods theo caps mục6; chưa OCR mới hoặc accept historical facts.

57 slots thiếu thuộc 19 issuer-periods, mỗi period thiếu cả ba statements:

| Mã | Kỳ chưa có candidate trong acquired pages |
|---|---|
| BRC | FY2015; Q1/Q3/Q4 2015; Q2 2024 |
| FPT | Q2 2024 |
| MWG | Q1–Q4 2013; FY2015; Q1/Q3/Q4 2015 |
| GMD | FY2015; Q1/Q3/Q4 2015 |
| VNM | Q2 2024 |

H1/LUYKE income và CF có thể là nguồn đối chiếu, không thay Q2 standalone; CDKT
LUYKE chưa thu. Không gán MWG2013 N/A chỉ theo ngày niêm yết chưa verified.

Discovery leads từ issuer domains (chưa tải/đọc, chưa chứng minh publication date):
[GMD candidate FY2015 audited consolidated](https://www.gemadept.com.vn/wp-content/uploads/2021/01/Bao-cao-tai-chinh-hop-nhat-da-kiem-toan-4.pdf),
[FPT candidate H1/2024 reviewed consolidated](https://fpt.com/-/media/project/fpt-corporation/fpt/ir/information-disclosures/year-report/2024/august/20240820---fpt---bctc-hop-nhat-ban-nien-soat-xet-nam-2024.pdf).
Stage documents phải freeze observed URL/host allowlist và imported source boundaries,
giữ campaign deadline/counters, dùng text trước, OCR chọn trang khi cần. Không suy
historical availability từ URL upload path hoặc filename.

```powershell
# Offline: acquisition đã hoàn tất; không mở thêm worker/network.
.\scripts\financial_history_pit.ps1 -Action verify
.\scripts\financial_history_qa.ps1 -Action run
.\scripts\financial_history_qa.ps1 -Action verify
```

Validation: 59 targeted tests, compile và synthetic smoke PASS; acquisition checkpoint
và QA replay verify kiểm riêng. Xem [validation — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/validation/verification.json).
Full gate chưa được ghi PASS; không mở batch20 trong stage này. F2 data delivery vẫn
PARTIAL: chưa unit/scope/vintage acceptance, publication evidence, historical compute
hoặc PIT snapshots; 0 new accepted/PIT facts. Baseline giữ 29/30, VNM F thiếu input.

## 10. Execution tiếp — selective documents, CPU OCR và reference review

Owner yêu cầu tiếp tục đến goal, không dừng ở checkpoint/report. Goal đang active;
stage hiện tại tiếp tục F2 document/semantic gaps, chưa tự promote batch20.
Entry point mới: [financial_history_process.ps1](../../scripts/financial_history_process.ps1).
Không dùng default v1 của low-level documents wrapper làm active flow.

```powershell
# Thiết lập CPU OCR local, kiểm hashes. Dùng -Network chỉ khi máy chưa có bundle.
.\scripts\financial_history_process.ps1 -Action setup
# Máy mới: .\scripts\financial_history_process.ps1 -Action setup -Network
# Resume giữ terminal receipts/reservations; không tải/OCR lại task đã hoàn tất.
.\scripts\financial_history_process.ps1 -Action process
.\scripts\financial_history_process.ps1 -Action verify
```

Runtime [descriptor](../../configs/data/financial_ocr_runtime_v1.json) và
[lock](../../configs/data/financial_ocr_runtime_v1.lock.json) pin wheel cp312 Windows,
Tesseract5.5.2, Leptonica1.87 và vie+eng tessdata_fast. Cài trong `.tools/financial-ocr`
(Git ignored), không global install/Windows OCR/cloud upload. OCR là worker tự động
theo explicit pages, timeout60s/page, text/TSV/confidence có provenance; confidence
không accept fact. Cumulative reservation không reset khi crash/resume.

Bounded [documents config v2](../../configs/data/financial_history_documents_v2.json)
kế thừa parent network counters/created_at và imported host latches. Hai requests
mới: GMD FY2015 thành công12.979.440bytes; FPT observed H1 URL trả404 một lần,
không retry. Totals kế thừa:565logical/565attempts,18.292.604bytes,2PDFattempts,
boundary/budget_stop false. V1 thiếu `cache_epoch` nên dừng trước REQUEST_RESERVED,
0 I/O mới; v2 là explicit pre-I/O config repair, không reset/retry network evidence.
Giữ receipts/configs/contract v1 để kiểm lineage, không xóa để che lỗi.

[Document snapshot verified](../../data/financial/history_document_supplement_v2/results/596bb28efe24e1e17b54/summary.json).
GMD scan57pages không có text layer; chọn8pages, không OCR cả PDF.
FPT Q2/2024 tìm được trong legacy cache sau khi mở rộng lookup, không tải lại.
[Cache-gap inventory](../../data/financial/history_document_supplement_v2/review/cache-gap-inventory.json)
đối chiếu2legacy inventories:7PDF candidates thuộc3missing issuer-periods
(GMD FY2015/FPT Q2-2024/VNM Q2-2024), không phải exhaustive census hoặc accepted periods.
VNM Q2/2024 đã đánh dấu cache trước discovery/download tiếp.

[GMD OCR8pages — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_selected_ocr_v1/results/60ffb2c44b743778e95e/summary.json),
[FPT OCR8pages — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_selected_ocr_fpt2024q2_v1/results/e709dbb8367ba085a897/summary.json):
16charged/successful pages,0errors. Mỗi PDF dùng8/40pages; batch16/1.000,
không reset8GMDpages khi mở FPT run khác PDF. Dependencies/models pin từ đầu;
setup downloads là tooling acquisition riêng, không financial API/PDF requests.

[Reference review/replay — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reference_review_v1/23253a81aeb4f8980813/report.md):

- Đối chiếu lại12API/PDF conflicts trên7ảnh cache: giữ existing reviewed PDF
  reference, quarantine API values; không sửa raw hoặc thay29metrics baseline.
- GMD:40reviewed reference facts (20fields ×FY2015/2014 comparative),4accounting
  checks PASS. Tính lại2Z annual EM Z″+3,25 bằng calculator/EBIT bridge hiện hành:
  2014=7,16368963;2015=6,65710370. Không cộng2 kết quả lịch sử vào goal30FY2025.
  Source2014 là comparative vintage2015, không là original2014/PIT. Chưa weighted
  shares/notes đủ để tính EPS/F/M; không dùng EPS reported3271 thay tính lại.
- FPT:23facts, giữ INSTANT/Q2_STANDALONE/H1_YTD riêng;4accounting checks PASS.
  Embedded issuer disclosure nêu explicit publication18/07/2024, usable19/07/2024
  theo existing date-only policy/observed HOSE calendar đã pin. Đây là temporal
  overlay, chưa complete PIT metrics hoặc research identity/feature acceptance.
  CFO là H1 YTD, không tự biến thành Q2; không áp annual Z baseline cho lợi nhuận quý.

Tổng63new reviewed reference facts,2new reference metrics,0complete new PIT metrics.
Baseline29/30 giữ nguyên; VNM F còn thiếu input. API missing57slots không sửa ngược;
PDF facts là overlay chọn lọc, chưa đủ để gọi toàn bộ statement/period complete.

Validation:73targetedtests PASS, compile/synthetic smoke PASS, setup/3layers replay
VERIFIED. Full suite trước đó đã chạy xong468tests/782,856s:3failures+3errors;
5localhost HTTP tests rerun ngoài sandbox PASS, bao gồm4case lỗi môi trường trước.
Còn missing matplotlib trong bundled runtime và M2-PREP frozen docs/DECISIONS hash
mismatch; không sửa old assertions/sealed manifest hoặc gọi full gate PASS.
[Validation evidence](../../data/financial/history_document_supplement_v2/validation/verification.json).

Việc tiếp theo của goal: review VNM Q2/2024 từ cache; tiếp EPS/depreciation/debt notes
cho các dependency đã có PDF; discovery có bằng chứng cho16missing issuer-periods
chưa match trong inventory scope trên; tiếp publication/vintage và unit/scope proof.
Không tải lại FPT/VNM Q2 chỉ vì API thiếu. Giữ caps/counters/boundaries, không IR,
không tự mở batch20 hoặc đổi formulas/acceptance để đạt count.

## 11. Execution tiếp — reviewed history bundle và GMD notes

Active config [financial_reviewed_batch_v3.json](../../configs/data/financial_reviewed_batch_v3.json),
[summary verified — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/978c1102715ca262fae3/summary.json),
[annual task grid — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/978c1102715ca262fae3/annual-metrics.csv).
PowerShell mục10 đã bao gồm hai documents configs, sáu OCR runs, original replay
và bundle mới. `process` resume task đã hoàn tất; `verify` không network/OCR mới.

- 102 new reviewed reference facts:56 annual,46 INSTANT/Q2_STANDALONE/H1_YTD.
  Có VNM Q2/2024 từ cache; H1 CFO giữ YTD, không suy ngày công bố từ chữ ký.
- Full annual grid5×13×6=390tasks có35values:29legacy FY2025 và6new historical
  references, không gọi35/30 hoặc full historical completion. GMD2014 EPS4345,96703004,
  Z7,16368963; GMD2015 EPS3271,40404564, F6, M−2,58797959, Z6,65710370.
  F/M dùng đúng existing VAS reference variants, Z annual EM Z″+3,25; không đổi formula.
- EPS2014 original4598 được điều chỉnh thành4346 trong vintage2015. Giữ revision;
  không đưa số điều chỉnh ngược PIT2014. EPS dùng disclosed numerator/weighted basic
  shares, không lấy reported ratio làm kết quả tính. Internal parent-profit discrepancy
  1VND giữa statement và EPS note được giữ ambiguous, không chọn theo thứ tự.
- GMD2015 F sử dụng gốc vay dài hạn mọi kỳ hạn +gốc thuê tài chính, loại future lease
  interest theo explicit maturity/principal schedules trang43–44PDF. Cổ phiếu phổ thông
  tăng116.137.994→119.621.994 chứng minh issuance occurred=1, không suy missing=0.
  Depreciation là flow owned tangible PPE riêng, không combined CF/amortization.
- [Notes bridge review](../../data/financial/history_document_supplement_v2/review/06-gmd2015-model-input-review.json)
  chỉ nhập TA2013 và owned depreciation2014 từ original FY2014; bridge TA/PPE và
  accumulated depreciation2014 khớp exact FY2015 opening/comparative. Không nhập original
  EPS/equity/liabilities2014, không auto-mix vintage hoặc coi joint reference là PIT.
- VNM manual transcription draft có2digits errors được arithmetic QA phát hiện trước
  promotion; giữ draft và version sửa có source image/hash. Không sửa raw/old artifact.
  Baseline CSV có BOM: loader xử lý UTF-8-sig và reject duplicate metric keys.

OCR55charged/successful pages,0errors: GMD2015=27/40, GMD2014=10/40,
FPTQ2=8/40, VNMQ2=10/40; không reset cap khi thêm config cùng PDF. Trang phụ lục
GMD2014 đọc bằng render/visual, không tính thành OCR. Cần campaign-wide coordinator
đọc mọi reservation trước khi mở thêm OCR/batch; hiện chỉ explicit finite six-run scope.

GMD FY2014 tải2.205.921bytes từ exact issuer attachment đã quan sát;69pages scan.
[Document snapshot](../../data/financial/history_document_gmd2014_v1/results/bf9824a7efe1942c6f94/summary.json).
Inherited local counters566logical/566attempts,20.498.525bytes,3PDFattempts;
created_at/boundaries không reset. Web PDF preview trước đó timeout1lần; config local
chỉ cho1attempt còn lại. Web discovery/preview không nằm trong local transport counter,
không cộng giả thành local receipts. Source post30/03/2015 là publication candidate,
chưa đủ chốt PIT; upload path2021 không là availability2015.

Validation mới:21targetedtests PASS, compile PASS, synthetic smoke
`run-20261019T153915Z-02c3f172` COMPLETE; active PowerShell verify tất cả layers PASS.
Full gate trước còn known M2-PREP frozen docs hash mismatch. Đã cung cấp matplotlib
trong optional local .tools/research-runtime; M1 reporting test đang chạy tiến trình16852,
session30364, không restart vì chưa có output. Không gọi full gate PASS khi chưa xong.

Goal ACTIVE/PARTIAL:0complete new PIT metrics, baseline29/30 và VNM F thiếu input;
quarterly/TTM chưa complete, historical identity và batch20/financial/research gates false.
Tiếp public discovery MWG/BRC FY2015 +các quý thiếu, catalogue/publication và
unit/scope acceptance; cache-first, không IR hoặc tải mọi PDF. MWG issuer report page
hiện client-rendered; không kết luận không có lịch sử chỉ vì static response trống.

## 12. Execution tiếp — MWG2015 text-first và handoff

Active [bundle configv4](../../configs/data/financial_reviewed_batch_v4.json),
[latest summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/461acf84c934c72cb025/summary.json),
[annual metrics — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/461acf84c934c72cb025/annual-metrics.csv).
Mục10/11 giữ snapshot trước; latest counts mục này supersede aggregate counts cũ.

Catalogue [MWG issuer](https://mwg.vn/bao-cao) cần chọn2015 rồi nhóm tài chính;
static HTML trống không có nghĩa không có tài liệu. Đã quan sát exact links FY2015
annual report, hợp nhấtFY/Q1/Q3 vàH1; ngày hiển thị giữ candidate, chưa PIT acceptance.
Cache URL scan không thấy2links đã chọn. Tải2PDF trong finite successor:
[config](../../configs/data/financial_history_documents_mwg2015_v1.json),
[document snapshot](../../data/financial/history_document_mwg2015_v1/results/2cdc988527b4b49cdeb0/summary.json).
Annual4.517.681bytes, Q3 scan8.664.959bytes; inherited totals568logical/568attempts,
33.681.165bytes,5PDFattempts, boundary/budget_stopfalse; không reset deadline/counters.

Annual84pages có text, trích75pages theo reservation; không cần OCR. Q3 scan không
text, chưa OCR/promote. [MWG review](../../data/financial/history_document_mwg2015_v1/review/07-mwg2015-reference-review.json)
46facts từ exact text+visual pages43–48/50/59/67,4accounting checks PASS. Tính thêm
EPS/Z2014/2015: đây là vintage2015 current/comparative, không original2014/PIT.
Depreciation2015 đã locator/visual nhưng chưa nhập; thiếu2014, không lấycombinedCF.
Chưa lấy rowabsent làm noncurrent debt=0. Printed signature captions trên2pages ghi
2015 tráiFY2015/audit2016 được giữsource anomaly, không suy ngày công bố từ đó.

Latest148new reviewed facts=102annual+46quarter/instant/YTD;390annualtasks có39values
(29legacyFY2025+10newhistorical). Không cộng vào goal30FY2025. 1ambiguousparent-profit
key vẫn quarantine;PE/PB lịch sử chưareviewedprice/share-event basis.0complete new
PITmetrics, VNM F thiếuinput, mọifinancial/research/batch20 gatesfalse.

Active PowerShell mục10 bao gồm3document configs+6OCRruns+2review layers;verifyPASS.
Loader pin/cache mỗi input một lần trong replay, không đọcPDF lặp theo từngfact;
explicit eligibilitytrue/available_at ở reference-only bundle bịreject, omitted old
quarter eligibility không cấpPITrights.22targetedtests, compile/synthetic
`run-20261019T155037Z-4a1f59bf` PASS; frozen4contracts/registry hashes PASS.
[Validation — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/validation/verification-notes-v1.json).
M1 reporting test session30364/process16852 đang chạy, không restart; fullgate chưaPASS.

Tiếp ngay trong goal: campaign-wide OCR coordinator nhập55reservations/cùngPDF cap
trước khi OCRQ3; reviewMWG quarterly intervals cần schema linh hoạtQ1/Q3/YTD, không
đổi H1 thànhQ2. Discovery/cache BRCFY2015 vàremaining missingquarters; acceptance
unit/scope/report vintages vàpublication exactPDF. Không mở20 trước pilot history gates.

## 13. Execution tiếp — OCR chung, EPS theo kỳ và date-as-of (20/10/2026)

**Goal vẫn ACTIVE/PARTIAL.** Active [config v7](../../configs/data/financial_reviewed_batch_v7.json),
[summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/7d76cba4c3fbe23d3cc2/summary.json),
[EPS theo kỳ — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/7d76cba4c3fbe23d3cc2/quarter-period-eps.json),
[monthly date references — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/7d76cba4c3fbe23d3cc2/monthly-period-date-reference.json).
Mục10–12 giữ các snapshot trước; aggregate counts hiện tại dùng mục này.

### Dữ liệu và phép tính đã bổ sung

- 224 reviewed reference facts mới:102 annual và122 quarter/instant/YTD. Annual grid
  vẫn390tasks,39values=29legacy FY2025+10historical annual. Ngoài ra có6 EPS theo kỳ:
  MWG Q3/9M2014–2015 vàFPT H12023–2024. Không cộng vào target30FY2025; VNM F vẫnnull.
- [MWG Q3 review](../../data/financial/history_document_mwg2015_v1/review/08-mwg2015q3-reference-review.json)
  có70facts và8accounting checks PASS. Ba tháng, chín tháng và closing balances tách
  đúng cột/kỳ; CFO chỉ9M, không tự biến thànhQ3. Weighted shares lấy đúng EPS note,
  không cộng EPS để tạoTTM hoặc suy diluted từ EPSbasic=diluted được in giống nhau.
- Catalogue MWG ghi30/10/2015, nhưng exact PDF nói được lập/soát xét06/11/2015.
  Giữ `DOCUMENT_POSTDATES_CATALOGUE_REQUIRES_VERSION_EVIDENCE`; không lấy ngày
  catalogue hoặc ngày ký thay publication của phiên bản này.
- [FPT H1 EPS note](../../data/financial/history_document_supplement_v2/review/09-fpt2024h1-eps-note-review-v2.json)
  bổ sung6facts từ physical PDF39, đối chiếu adjustment ởPDF40. Không OCR mới.
  Basic EPS dùng disclosed numerator/weighted shares cho6months; reserve dash vẫn
  unknown, strict-normalized/diluted EPSnull. Số so sánh2023 đã chỉnh shares/EPS
  trong vintage2024, không đưa ngược vào original2023.

### Temporal slice và kiểm chứng phiên bản

Dùng exact FPT PDF đã có explicit publication18/07/2024, existing owner-approved
DATE_ONLY policy và observed HOSE calendar có hash. Effective date19/07/2024.
Module [period date view](../../src/delta_t1/experiments/financial_period_date_view.py)
chạy120calendar month ends2016–2025 cho2H1periods:240rows,36date-eligible period
EPS references từ07/2024. Không lộ adjusted2023 trước release2024; same-date value
conflict trảnull; numerator/shares khác document vintage bị chặn. Chỉ tính tuổi
báo cáo khi value đã eligible. Calendar month ends ở đây là information references,
chưa phải trade execution dates hoặc feature snapshots choM3.

`complete_pit_metrics=0`: temporal reference không đồng nghĩa historical security
identity, strict EPS normalization, TTM/share-event acceptance hay research eligibility.
Đây không phải6families/1.500issuers hoặc full financial backtest dataset.

### OCR budget và resume

[Coordinator](../../scripts/financial_ocr_campaign.py),
[config v2](../../configs/data/financial_ocr_campaign_v2.json),
[snapshot — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_ocr_campaign_v1/results/9754efc1b5bd39d78322/summary.json).
Persistent policy/registrations nhập55old reservations rồi thêm8MWGQ3pages:
63charged/successful,0errors,7runs. GMD2015 dùng27/40, GMD2014 10/40,
FPTQ2 8/40, VNMQ2 10/40, MWGQ3 8/40. Global caps40/PDF,1.000/batch,
12.000/campaign và72h/90d từ original anchors; đổi config không quên old runs.
Duplicate PDF-page dưới tên task khác bị chặn; interrupted reservation không reset.
OS lock bảo đảm một coordinator worker; low-level OCR worker cũ không sửa.

Active PowerShell chạy coordinator v2 thay từng OCR entry rời. Offline resume đã
kiểm4network journals và63reservation hashes không đổi:0newrequests/0newOCR.
Local network totals vẫn568logical/568attempts,33.681.165bytes,5PDFattempts.
Source boundaries/registry và acquisition code pins cũ giữ nguyên.

### Đơn vị API có bằng chứng code hiển thị

[Unit contract](../../configs/data/financial_cafef_unit_contract_v1.json) pin3cached
HTML sources: raw monetary values được UI chia1e6/1e9 ra triệu/tỷ đồng.
[Unit overlay — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_candidate_units_v1/fad51d7251c77c3f11b2/summary.json)
đọc7.890exact code/label candidates:7.520rawVND monetary rows có unit proof;
370EPS rows đi formatter riêng, không áp monetary rule. Không suy multiplier từ
magnitude; giữ raw/null/zero/sign, template fingerprint và static-row guard.
Unit proof chưa accept field placement, scope, framework, vintage hoặc publication;
BRC/VNM row-shift quarantine và mọi closed gates giữ nguyên.

### Validation và việc tiếp

47targetedtests PASS; compile PASS; synthetic smoke
`run-20261020T042220Z-548dac11` COMPLETE; active PowerShell verify PASS.
33frozen input/code pins, registry hash và legacy metrics/reviewed inputs PASS.
[Validation — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/validation/verification-units-date-v1.json).
Full gate chưaPASS: M1 reporting session30364/PID16852 không còn tồn tại và không
có terminal result đủ để chứng nhận; không restart chỉ vì mất observation handle.
Known M2-PREP frozen docs fingerprint mismatch vẫn giữ, không waive assertion.

Tiếp: cache/public-source gaps BRCFY2015 vàquarters thiếu; unit/scope/period/vintage
normalization vàaudit coverage theo template, bổ sung EPS/debt/depreciation notes.
Cần engineering/pilot evidence trước batch20; không suy còn một source blocked là
mọi nguồn đều hết dữ liệu. Không IR, không reset campaign hoặc sửa raw/sealed artifacts.

Bổ sung cuối checkpoint20/10: [BRC FY2015 BCTN config](../../configs/data/financial_history_documents_brc2015_v1.json),
[document snapshot](../../data/financial/history_document_brc2015_v1/results/93be30613d9d847f9160/summary.json).
Exact public link đã quan sát và chưa thấy acquired receipt trong scope cache scan;
1request thành công13.220.889bytes. PDF100pages mixed:75pages text extraction có
74.257chars, nhưng phần BCTC từphysical67 là scan nhúng; text footer/header không
chứng minh financial table đã extract được. Chưa OCR/review numerical cells củaBRC2015.
Active PowerShell có4document configs; verifyPASS. Totals mới569logical/569attempts,
46.902.054bytes,6PDFattempts, originalcreated_at/boundaries giữ nguyên. Metadata này
supersede network totals568 ở đoạn checkpoint trước; không gọi cả100pages đã đọc.
Tiếp locator/selective OCR phần financial BRC2015 trong cùng campaign cap còn lại.


## 14. Execution tiếp — BRC company scope và independent audit (20/10/2026)

Checkpoint này supersede active counts mục13, giữ mọi sealed artifact cũ.
[Bundle v8](../../configs/data/financial_reviewed_batch_v8.json),
[summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/ecfd0c0dc07b7ead4894/summary.json).
270new reviewed facts:148annual+122quarter/instant/YTD;224CONSOLIDATED và46COMPANY_REPORTED.
BRC2015 PDF physical67–72,91,92,95 đã selectedOCR9pages, review46facts và8checksPASS.
Note32physical92 cho numerator/weightedshares, tính lại basicEPS2014/15 khớp printed
1335/1155 sau làm tròn. Giữ fund allocation wording/vintage, không normalized/diluted claim.
Scope COMPANY_REPORTED có explicit company statements, chưa chứng minh consolidated
hoặc no-subsidiaries2015. Không dùng scope ISSUER_NO_SUBSIDIARIES2025 ngược lịch sử.
Calculator scope guard chỉ mở2disclosedEPS references;5families khác chặn theo scope.
Annual390tasks/41nonnull=29legacy+12newannual (10consolidated+2companyEPS), thêm6periodEPS.
VNM Fnull, strictPITmetrics0, date references240/36 và units7.520 unchanged.

### Independent API-pass audit

[Seeded sampler](../../scripts/financial_history_audit_plan.py),
[config](../../configs/data/financial_history_audit_plan_v1.json),
[6tasks — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_independent_audit_v1/6d3310d3649647998dfa/audit-tasks.json).
Seed `financial-history-pilot5-audit-v1` pin trước chọn tài liệu;245arithmetic-clean
cohorts đủ9mapped monetary fields/3statements/5checks; exclude knownannual rowshifts.
Chọn3/5issuers bằnghash, mỗi annual/quarter, rotate3eras; GMDannualpreferred2013–15
không có cleancohort nên fallback được ghi rõ. Không chọn mẫu theo có sẵnPDF hoặcreturns.

[Review comparator](../../scripts/financial_history_audit_review.py),
[config v3](../../configs/data/financial_history_audit_review_v3.json),
[result — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_independent_audit_review_v1/34d959dd91b2900e4192/summary.json).
Pin rawQA, providerVNDunit overlay, reviewjson, PDF/render hashes; so exactDecimal,
không averaging/zero-fill/tolerance waiver. Mỗi mẫu9fields với physicalpages/rowlabel,
explicitunit/scope/period. Matching audit không accept providerH/HKscope hoặcPIT.

| Sample | Kết quả field audit |
|---|---|
| FPT FY2023 | 9/9match, exact original FY2023 cachedPDF; selectiveOCR10pages |
| GMD FY2024 | 9/9match; original issuer PDF mới, text-first, không OCR |
| GMD Q4/2019 | 7/9match; currentassets API368/PDF369 vàtotalassets API919/PDF918 đều lệch1VND |
| BRC FY2018 | Pending originalPDF/review |
| BRC Q2/2021 | Pending originalPDF/review |
| FPT Q3/2015 | Pending originalPDF/review; không nhầm FPTTelecom/FOX |

GMDQ4PDF tự có totalcapital919 khác totalassets918 đúng1VND; giữsource anomaly,
không tuyên bố rowshift hoặc materialerror chỉ từchênh1VND. Cashflow column explicit
YTD12months dù reporttitleQ4; không dùng345685906197 như standaloneQ4CFO.
GMDcache candidate fcb5... làFY2025comparative, không chứng minhoriginalFY2024;
[bounded supplement](../../configs/data/financial_history_documents_audit_gmd_v1.json)
đã tải đúng originalFY2024 vàQ42019 từissuer. Textlayer có số nhưng vẫn visuallyreview
trang cófield; không OCR haiPDF chỉ vì làscan nếu embeddedtext dùng được.

### Run, budgets và gates

Active [PowerShell](../../scripts/financial_history_process.ps1) có5documentconfigs,
[globalOCRv4](../../configs/data/financial_ocr_campaign_v4.json), bundle8 và2auditlayers.
GlobalOCR82charged/success/0errors/9runs, cumulative40/PDF–1.000/batch–12.000/campaign;
BRC9/40,FPT2023 10/40; không reset oldpages,72h hoặc90d anchors.
Local totals571logical/571attempts,74.681.871bytes,8PDFattempts; sourceboundaries và
created_at1792414507.836684 giữ nguyên. Web preview GMD2024 bịtool từ chối do
content length17.522.145; [external ledger — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_audit_fpt2023_v1/public-discovery-20261020.json)
charge separately conservatively, local chỉ1remainingattempt, không reset thành2.

```powershell
./scripts/financial_history_process.ps1 -Action verify
./scripts/financial_history_process.ps1 -Action process -Network
```

Chưa mởbatch20: audit3/6documents, provider-scope/vintage normalization vàfullgate
còn gaps. Không đòi mọi metric phảicomplete mớiacquirebatchtiếp nhưng phải cópilot
engineering/source/quality gates theo mục6. Không IR vàkhông nới strictPIT đểqua gate.

### Kiểm tra checkpoint14

71targetedtests PASS, compile PASS, synthetic
`run-20261020T045953Z-84db5ded` COMPLETE, activePowerShellverify PASS.
Offlineprocess replay không thay88journal/reservationfiles (82OCRreservations,
6networkjournals trong inventory),0newrequests/0newOCR.51frozenpins/6contracts,
registry vàlegacy metrics/reviewedinputs unchanged;329localdoclinks PASS.
[Validation — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/validation/verification-brc-company-independent-audit-v1.json).
Fullsuite không được chứng nhậnPASS: giữpreviousM1terminal-result gap vàknownM2-PREP
frozen-doc mismatch; targetedchecks không thayfullrepositorygate.
[Discovery follow-up — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_audit_fpt2023_v1/public-discovery-followup-20261020.json)
chưa tìm exactoriginal3pendingPDFs; issuerBRCwebsite trongphysicalPDF6 khôngaccessible
quawebtool, không tựretry hoặc suy linkfilename. Giữpendingtargets, không thayseed
bằngdocuments tiệncó. Tiếpcache/catalogue khác cóbằngchứng vàselective review/modelnotes;
không suy cảcompanydocumentkhôngtồntại từmộttoolerror.

Browser follow-up catalogue NQS BRC đã mở1page vàclickfinancialtab1lần;
lastURL `#google_vignette`, downloadheading cótrongDOM nhưng chưaverifyoriginallinks.
Đây là UI inspection chưa xong doadvignette, không phảiaccessdenial haychứngminh
báocáokhôngtồntại. [Observation — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_audit_fpt2023_v1/browser-catalogue-observation-20261020.json)
ghi0PDFdownloads; tabtạm đãđóng. Tiếp xửlý UIcatalogue hợp lệ/nguồnkhác, không
nhầm external UI network với571localjournalrequests.


## 15. Execution tiếp — Đối chiếu đủ sáu kỳ audit (20/10/2026)

Checkpoint này cập nhật tiến độ mục14. Đã tìm và tải thêm ba PDF đúng mẫu:
[BRC annual2018 vàQ2/2021](../../configs/data/financial_history_documents_audit_brc_v1.json)
từ các link được quan sát trong catalogue NQS, cùng
[FPT Q3/2015](../../configs/data/financial_history_documents_audit_fpt2015q3_v1.json)
từ đúng hàng tài liệu Stockbiz của Công ty Cổ phần FPT.
[Quan sát BRC](../../data/financial/history_document_audit_brc_v1/catalogue-observation.json)
và [quan sát FPT](../../data/financial/history_document_audit_fpt2015q3_v1/catalogue-observation.json)
giữ đường dẫn, label, issuer và cách tìm. Catalogue FPT chính thức hiện có năm2016–2026;
việc thiếu2015 ở UI đó không được diễn giải thành hết nguồn công khai.
Không gửi IR, không đoán filename hoặc mở lại host đang latched.

### Kết quả mẫu kiểm tra

[Config review v4](../../configs/data/financial_history_audit_review_v4.json),
[summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_independent_audit_review_v1/05ffe9283a1caf74fd81/summary.json),
[chi tiết — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_independent_audit_review_v1/05ffe9283a1caf74fd81/reviews.json).
Mẫu seed giữ nguyên:3issuers × annual/quarter,6/6kỳ đã đối chiếu9field mỗi kỳ.
54so sánh cho49match và5exact conflicts; status `AUDITED_WITH_CONFLICTS`.
Đây là hoàn tất đối chiếu mẫu, chưa chứng nhận toàn bộ lịch sử hoặc accepted facts.

| Kỳ | Kết quả |
|---|---|
| FPT FY2023 | 9/9match |
| GMD FY2024 | 9/9match |
| BRC FY2018 | 9/9match, company-reported scope |
| BRC Q2/2021 | 9/9match, company-reported scope |
| GMD Q4/2019 | 7match; currentassets API−PDF=−1 vàtotalassets=+1VND |
| FPT Q3/2015 | 6match; currentassets=−1, totalassets=−1 vàCFO=+1VND |

[Candidate quarantine — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_independent_audit_review_v1/05ffe9283a1caf74fd81/candidate-quarantine.json)
ghi đúng symbol/year/quarter/mode/provider_type/field, APIvalue, PDFvalue, difference,
PDFhash/page vàsampleID. Không làm tròn sai khác thànhmatch, không average hoặc tự
thay API bằng PDF; review chỉ đối chiếu, chưa accept bất kỳ candidate nào.
Source anomalies được giữ cả khi9fieldmatch: cover BRC Q2/2021 ghi31/03 nhưng core
statements ghi30/06 vàquýII; không dùng cover để suy kỳ hoặc publication.
CFO của cả3quarter samples làYTD (6/9/12months), không standalone quarter.
FPT2015 tổng vốn400 cóotherfunds430; không lấy410 thay400. FPT cũng có dòngPBT
trước/sau developmentfund; audit9field không tự approve các input khác của F/M/Z.

Blueprint sampler cũ giữ trạng thái khởi tạo; completion thực tế lấy từ review summary
v4 bên trên. Không dùng hardcoded counters của blueprint làm current completion gate.
ProviderH/HK/N/K không được suy scope từ mã loại; không dùng54comparisons như54newfacts.
Reference bundle vẫn270facts/41annualvalues (29legacy+12new) và6periodEPS;
VNM Fnull, complete strictPITmetrics0, financial/research/M3gates vẫn đóng.

### OCR, ngân sách và chạy lại

[OCR config v6](../../configs/data/financial_ocr_campaign_v6.json),
[snapshot — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_ocr_campaign_v1/results/ad53c4d5df60f7d4dd50/summary.json).
Thêm17selectedOCRpages: BRC2018 financialspreads35–38 (4), BRCQ2/2021pages1–6 (6),
FPTQ3/2015pages1–7 (7). Đã xem rendered pages để chốt số, không auto-accept OCR.
Cumulative99charged/successful,0errors,11runs; perPDF4/6/7, cap40/PDF,
1.000/batch và12.000/campaign không reset. Text extraction BRC2018 cótext nhưng
numeric tables là ảnh nhúng; page count không chứng minh toàn bộ bảng đã extract.

Local network kế thừa574logical/574attempts,98.083.449bytes,11PDFattempts,
created_at1792414507.836684, boundary/budget_stopfalse. Ba PDF mới tổng23.401.578bytes,
0browserPDFdownloads; external preview17.522.145bytes của checkpoint14 vẫn ghi riêng.
Active [PowerShell](../../scripts/financial_history_process.ps1) có7documentconfigs,
OCRv6, reviewedbundlev8, seededplan vàreviewv4. `process` tái dùng receipts/reservations;
`verify` chạy offline. Frozen pilot/C6/C8/registry không chỉnh.

Tiếp theo: lập engineering gate F2 bằng task accounting, failure/parser rates,
resume/hash/budget và các quarantine hiện có; chuẩn bị selection20 có bằng chứng
exchange/sector/template. Audit xong không tự mở batch20, missing publicdata không
đồng nghĩa engineeringFAIL; cần kết luận gate có evidence, không chỉ hardcodedfalse.
Giữ riêng acquisition readiness và metric/PIT coverage khi scale.


Kiểm tra checkpoint15:73targetedtests PASS, compile PASS, synthetic
`run-20261020T053129Z-938deecc` COMPLETE vàactivePowerShellverify PASS.
Offlineprocess replay giữ nguyên107files (99OCRreservations và8networkjournals),
0newrequests/0newOCR.69frozenpins/8contracts, registry vàbaseline metrics/reviewedinputs
unchanged;343localdoclinks PASS. Disk quan sát96.567.959.552bytes trống, vượt30GBfloor.
[Validation — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/validation/verification-independent-audit6-v1.json).
Không chứng nhậnfullrepo gate từtargetedtests; knownM1/M2limitations giữ nguyên.


## 16. Execution tiếp — Gate F2 và metadata mẫu20 (20/10/2026)

Checkpoint này thay active pointer của mục15, không thay dữ liệu đã seal.
[Engineering gate](../../scripts/financial_history_stage_gate.py),
[config](../../configs/data/financial_history_stage_gate_v1.json),
[kết quả — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_stage_gate_v1/results/4567bb418bfc74712b6a/summary.json)
đạt `PASS_CANDIDATE_STAGE_ENGINEERING`. Gate kiểm tra1.100tasks accounted,
590cached/acquiredrawresponses,563networkresponses không parsererror,
1terminalfailure/574attempts (0,1742%),6/6seededaudits,5quarantinedcells,
hai annual row-shift cohorts được giữ, resume/hash/disk/deadline/budget.
17checks đạt; đây là gate mở bước candidates có giới hạn, không phải metric/PIT PASS.
Deadline live vẫn kiểm lại từ anchor1792414507.836684; decision snapshot không gia hạn deadline.

### Selection và metadata

[Assignment overlay](../../data/financial/history20_metadata_v1/assignment.json)
pin registry1.522rows và legacy50plan, giữ registry gốc bất biến.
15mã bổ sung: **NTP, PLX, HSG, DCM, SLS, SHS, VEA, EIB, ACV, VCS, DBC, FOX, NKG, GAS, STB**;
5controls giữ BRC/FPT/MWG/GMD/VNM. Selection theo exchange/type proposal rồi
registry_id tăng dần, join đồng thời ticker+exchange+legacy_security_id.
Không dùng portfolio outcomes; provisional provider partitions không tự thành canonical identity.
Mẫu20 có3sàn nhưng chưa có insurance, chưa đại diện mọi template/era hoặc final historical universe.

[Metadata collector](../../scripts/financial_history20_metadata.ps1),
[config](../../configs/data/financial_history20_metadata_v1.json),
[kết quả15/15acquired](../../data/financial/history20_metadata_v1/results/0a357b97e15d0fb20bf5/summary.json).
Hồ sơ công khai Stockbiz được lưu rawHTML/hash; parser chỉ lấy quoteheader và hai
labelled provider hierarchy links, không lấy industry từ news/footer.
[Profile parser](../../scripts/financial_history20_profiles.py),
[config](../../configs/data/financial_history20_profiles_v1.json),
[kết quả — archive](../../artifacts/archives/financial-history-20261023/data/financial/history20_profiles_v1/7e1228bef0cca25e4c37/summary.json):
15/15khớp ticker/exchange,7current provider sectors/11industries/3exchanges,
`READY_FOR_BOUNDED_TEMPLATE_PROBES`. EIB/STB ghi ngành ngân hàng, SHS ngành chứng khoán.
Đây là current classification, không xác nhận lịch sử ngành, applicability F/M/Z hay issuer continuity.

Metadata kế thừa589logical/589attempts,100.909.710bytes,11PDFattempts,
0newPDF/0newOCR, boundary/budget_stopfalse. Không reset deadline/counters khi nối child.
[Template probe controller](../../scripts/financial_history20_probes.ps1) và
[config](../../configs/data/financial_history20_probes_v1.json) chỉ cho180request page1:
15mã × NAM/QUY × CDKT(TN/NV), KQKD(KQKD), LCTT(HDKD/HDDT/HDTC).
Ngân sách child kế thừa parent: tối đa769logical/949attempts,≤2attempts/request,
2giây spacing,20giây timeout,1worker,5MB/response; không tảiPDF.
Response parse thành candidates, chưa map/accept; phải giữ actual template của ngân hàng/chứng khoán.
Full-history acquisition và numeric/research/M3 gates vẫn đóng trong controller này.

### Chạy lại

```powershell
.\scripts\financial_history20_metadata.ps1 -Action verify
& $Python scripts/financial_history20_profiles.py verify
.\scripts\financial_history20_probes.ps1 -Action run -Network -MaxNewRequests 180
.\scripts\financial_history20_probes.ps1 -Action verify
```

`$Python` là Python runtime hoạt động của máy, không dùng `.venv` đã hỏng.
Network chỉ xảy ra khi truyền `-Network`; receipt đã hoàn tất không request lại.
Interrupted request không có receipt phải review, không auto retry bằng budget mới.
Workerlock dùng chung cho các collector mới. Không chạy đồng thời old network scripts
và collector mới; old scripts chưa dùng workerlock chung.

Tiếp theo: kiểm chứng toàn bộ180template probes, inventory actual template families và
schema/orphan differences; chỉ sau gate tương ứng mới freeze successor lịch sử cho15mã
và tái dùng page1candidates. Chưa truyền universe mới vào frozenpilot5/trial50 runner.
Reference bundle giữ270facts/41annualvalues/6periodEPS; baseline29/30, VNM Fnull,
complete strictPITmetrics0. Không thay accepted-fact, PIT, reconciliation hoặc formula policy.

### Kết quả template probes và adapter kế thừa

[Probe snapshot](../../data/financial/history20_probes_v1/results/1256b94f3a1a330c9f01/summary.json):
180/180ACQUIRED,0transport failures trong child. Strict parser cũ176parsed/4review:
EIB/STB CDKT NV ởNAM vàQUY có nhiều template rows mang code rỗng. Giữ nguyên
`PARSE_REVIEW_REQUIRED` trong receipts cũ; không sửa parser frozen hoặc evidence cho khớp.
Probe là page1mới nhất, quan sát2021–2026; không coi24.020cells là coverage2013–2025.
Cumulative769logical/769attempts,102.828.239bytes,11PDFattempts; anchor/boundaries giữ nguyên.

[Candidate adapter](../../scripts/financial_template_candidates.py),
[config](../../configs/data/financial_template_candidates_v1.json),
[summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history20_template_candidates_v1/04e643e5d1fb5472bbb1/summary.json),
[template catalogue — archive](../../artifacts/archives/financial-history-20261023/data/financial/history20_template_candidates_v1/04e643e5d1fb5472bbb1/template-catalogue.json).
Replay180/180responses,0parsererrors,24.020rawcells:23.484unique-code label candidates,
176blank-code và360unmapped-code cells bị quarantine. Template fingerprints quan sát:
CDKT6, KQKD3, LCTT12. Đây là fingerprints của response, không số mẫu kế toán chuẩn.
Không suy blankcode0 là structural heading hoặc gán label bằng thứ tự hàng.
Unique-code mapping cũng chỉ candidate: chưa phát hiện/giải quyết được mọi provider value shift.

Adapter lưu mọi raw cell/ordinal và mọi label alternatives, nhưng ordinal chỉ là provenance;
không ánh xạ field bằng vị trí. Duplicate nonblank template/observation codes cũng quarantine,
missing/zero/boolean/nonfinite tách trạng thái, exact decimal strings giữ rawhash.
Bank/securities templates không được đưa qua mapping/formula dành cho regular companies.
Scope/unit/vintage/PIT và F/M/Z applicability vẫn chưa được accept bởi adapter.

Active PowerShell process/verify đã thêm replay offline gate, metadata, profile, probe và
adapter; network vẫn ở CLI có budget riêng. Tiếp review schema/cohorts và freeze successor
history có cache page1, pagination guards, coverage/QA và ledger kế thừa; không gọi probe là
hoàn tất F3 hoặc mở lên50. Baseline/reference/OCR không đổi.


Kiểm tra checkpoint16:120targetedtests PASS, compile PASS, synthetic
`run-20261020T071819Z-ce595cb9` COMPLETE; activePowerShellprocess vàverify PASS.
Offline replay giữ nguyên130evidencefiles (28networkjournals,99OCRreservations,
registry và2baselinefiles),0newrequests/0newOCR.99frozenpins/10contracts verified.
[Validation](../../data/financial/history20_probes_v1/validation/verification.json).
Local links đã kiểm406trước khi thêm dòngvalidation này. Không chứng nhậnfullrepo
PASS từtargetedtests; previousM1/M2limitations giữ nguyên.

Self-review: strictprobeparser có4failures/180successfulresponses (2,22%), vượt
1%parser threshold nếu dùng adapter cũ. Không dùngF2PASS để bỏ qua lỗi này.
Successor adapter giữ4failures cũ, replay180/180 vàquarantine536cells; F3 chưa có
engineering conclusion cho fullhistory acquisition. Cần gate theo adapterversion,
quarantine completeness và actual template inventory trước khi thu phần lịch sử còn lại.


## 17. Execution tiếp — Crawl lịch sử mẫu20 (20/10/2026)

F3 đã bắt đầu thu phần API lịch sử của15mã bổ sung, giữ5controls trong dataset cũ.
[Successor PowerShell](../../scripts/financial_history_batch.ps1),
[config](../../configs/data/financial_history_batch20_v1.json),
[assignment overlay](../../data/financial/history_batch20_v1/assignment.json),
[task plan](../../data/financial/history_batch20_v1/task-plan.json).
Không đổi frozenpilot5 runner hoặc truyền universe mới vào runner đó.

### Gate và phạm vi

[Kiểm tra trước khi chạy](../../data/financial/history_batch20_v1/validation/verification-collector-start-v1.json)
ghi `PASS_BOUNDED_HISTORY_CANDIDATES` dựa trên9checks:
F2engineering,15currentprofiles/3sàn, KQKDtemplate fingerprints tách được3nhóm
Regular/Bank/Securities,180/180adapterreplay,0currentparsererrors và536cells quarantine,
không numeric promotion. Giữ nguyên4strictparserfailures cũ, không đổi denominator
hoặc sửa source evidence để làm gate PASS. Đây là parser version mới cho candidates;
không chấp nhận accounting inputs, source reconciliation, scope, lịch sử ngành hoặc PIT.
221code/inputpins của successor đã kiểm lại trước khi thu network.

Task plan gồm3.300tasks:2.100API và1.200catalogue. API mỗi mã140tasks:
NAM tối đa5pages/group, QUY15 vàLUYKE5 (không LUYKE choCDKT),4headers/page.
Range chính annual/quarter2013–2025, auxiliaryclosing2012; extra observed2026 giữraw,
không tính vào targetcoverage. Cataloguetrêncafef.vn tiếp tục imported latch:
15firstpageblocked và các page sau không cần request; không mở hostname/client khác để retry.
Nguồn catalogue độc lập phải có contract mới và không chạy song song worker này.

Page1cache tái dùng180rawresponses từ probe. Phân trang có trạng thái độc lập
symbol/statement/mode/group, chỉ request page sau khi predecessor accounted;
stop khi hết nguồn, đạt target boundary hoặc period header không tiến triển.
Stop không đồng nghĩa doanh nghiệp không công bố; thiếu kỳ vẫn cần coverage/sourcequeue.
Có mọi receipt sau từng request; interruptedrequest không receipt phải review,
không automatic retry/reset. Candidate shards ghi một lần theo taskid, các snapshot
chỉ pin shardindex/hash để hạn chế nhân bản artifact khi resume.

### Ngân sách và chạy lại

Child kế thừa parent769logical/769attempts,102.828.239bytes,11PDFattempts,
anchor1792414507.836684. Caps:≤2.869logical/4.969attempts,2.102.828.239totalbytes,
5MB/response,2attempts transient/request,20giây timeout,2giây spacing,1worker;
72hbatch/90dcampaign từ anchor cũ, diskfloor30GB. Không có PDF/OCR mới trongcollector.
Ownjournal phải giữ anchor và mọi inheritedrequest không đổi; source/budgetlatch
không mở lại khi resume. Globalworkerlock mới giữ một collector tại một thời điểm.

```powershell
.\scripts\financial_history_batch.ps1 -Action plan
.\scripts\financial_history_batch.ps1 -Action run -Network -MaxNewRequests 2100
# Chỉ chạy lại khi worker trước đã terminal; tái dùng receipts thay vì request lại.
.\scripts\financial_history_batch.ps1 -Action verify
```

`-MaxNewRequests` là cap của một invocation, không reset ledger caps. Không chạy
plan/verify đồng thời collector để kết luận trạng thái cuối. Snapshot khởi tạo
[0candidate/3.300pending](../../data/financial/history_batch20_v1/results/53d6c017f36357773950/summary.json)
là historical plan snapshot, không phải tiến độ hiện tại.
[Observation](../../data/financial/history_batch20_v1/validation/live-observation-20261020.json)
lúc07:33:46UTC có331terminalreceipts:180cache,121newAPI,15importedboundary,
15afterseriesstop. Đây là census tại thời điểm đó, không finaltaskaccounting.
Worker `exec session3321` đã được poll và còn live; chưa seal finalcoverage hoặc promote50.

### Validation và công việc tiếp

129targetedtests PASS, compile PASS, synthetic
`run-20261020T073156Z-edbc708b` COMPLETE. Các test thêm kiểm cache/resume/wavecap,
independentpagination/nonprogress, importedboundary/missingpredecessor,
interruptedrequest, fatalrawhashmismatch, quarantine/parser/template gate.

[Fullsuite follow-up](../../data/financial/history20_probes_v1/validation/full-suite-followup.json):
fullsuite564tests có3failures/3errors;4HTTPcases do localhost sandbox,1missingmatplotlib
import và1knownM2-PREP `docs/DECISIONS.md` frozenhash mismatch. FocusedHTTP5tests
PASS outside sandbox; focusedM1reporting5tests PASS khi nạp existing
`.tools/research-runtime` vàoPYTHONPATH. Không cài package mới hoặc sửa assertions.
KnownM2mismatch giữ nguyên; fullrepository chưa PASS và không numeric/research promotion.
Các kiểm trafocused không được cộng thành tuyên bốfullsuitePASS.

Tiếp tục chờ đúng livehandle, không restart worker chỉ vì tooltimeout. Khi terminal:
verify receipts/candidate shards/counters, QA phần targetrange, anomaly/missinginput
queues và diversity/interval notes; rồi catalogue/PDF có chọn lọc, review và compute.
F3chưa hoàn tất annual/quarter/YTD/PIT verticalslices hoặc cost/audit handoff.
Reference baseline29/30, VNM Fnull,270reviewedfacts/41annualvalues/6periodEPS,
99OCRpages vàcomplete strictPITmetrics0 không đổi. Goal ACTIVE/PARTIAL.


## 18. Execution tiếp — QA preview và queue PDF chọn lọc (20/10/2026)

Collector F3 tại mục17 tiếp tục chạy trên đúng `exec session3321`; đã poll thấy
checkpoint450newrequests, chưa terminal/finalcoverage. Không restart hoặc chạy
collector khác song song. Trong thời gian đó đã triển khai offline QA riêng:
[PowerShell](../../scripts/financial_history_batch_qa.ps1),
[Python CLI](../../scripts/financial_history_batch_qa.py),
[preview config](../../configs/data/financial_history_batch20_qa_preview_v1.json).
Preview pin đúng563receipts (180cache/338newAPI/15importedboundary/30afterstop),
không đọc thêm receipts được append sau đó. Đây là cố định mẫu bằng chứng cho
replay, không phải seal lịch sử hoặc point-in-time financial acceptance.

### Phát hiện từ dữ liệu thật

[Summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_batch20_qa_previews_v1/101af645668c0cf47e6c/summary.json),
[queue — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_batch20_qa_previews_v1/101af645668c0cf47e6c/document_queue.json),
[displacements — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_batch20_qa_previews_v1/101af645668c0cf47e6c/displacements.json).
60.014candidatecells trong inventory; QA chỉ dùng2012–2025, giữ extra years trongraw.
1.007rootgroupzeroheaders có exact template group-number proof;330nonstructural
unresolvedcodes còn giữ, trong đó1nonblankorphan và329blankcodes. Không suy
blankcode0 là heading.5.338exactcode/label aliases chỉ diagnostic cho Regular;
bank/securities không dùng lại scoremapping/formula của doanh nghiệp thường.

1.036rawarithmeticchecks:1.029equal/7difference. Annual–Q4 diagnostic:2.651equal/
649difference. Các check chưa chứng minh unit/scope/vintage/period equivalent.
Ba possible row-displacement cohorts: **DCM, GAS, HSG FY2025**, offset−1,
ít nhất2distinctnonzeroamounts trùng code lân cận Q4. Đây là tín hiệu để review,
không phải kết luận provider sai hoặc giấy phép dịch hàng. Đặc biệt phải xác minh
financialyear/quarter boundaries và fiscal exceptions bằng tài liệu gốc trước khi so.

SHS FY2025 LCTT code`HDKD_1` có680.759.314.148rawunits, không có label; không
được loại như structural zero. Cell này được giữ và queue priority1 để kiểm schema/
sourcePDF, không gán thànhCFO. Không inferVNDmultiplier từ magnitude.

Queue hiện tại8kỳ, chưa gồm finalmissingcoverage hoặc independentfalse-negative audit:

| Priority | Kỳ cần đối chiếu | Lý do |
|---|---|---|
| 1 | DCM/GAS/HSG FY2025 | Possible row displacement |
| 1 | SHS FY2025 | Nonzero unmapped LCTT code |
| 2 | DCM FY2013/FY2014, HSG FY2024, VEA FY2025 | Raw accounting differences |

Queue này hướng tới selectivePDF; không tải toàn bộPDF cho60.014cells.
Cần bổ sung independentAPI-pass audit để đánh giá false negatives, không dùng
anomalyqueue thay randomaudit. Preview không đánh giá thiếu kỳ: `coverage_assessment`
=`NOT_PERFORMED_PREVIEW`; missingcount0 không chứng minh đủ dữ liệu.
Coverage đầy đủ và missinginputs chỉ đánh giá sau khi có sealedacquisitionsnapshot.

### Chạy lại và kiểm chứng

```powershell
.\scripts\financial_history_batch_qa.ps1 -Action run -Config configs/data/financial_history_batch20_qa_preview_v1.json
.\scripts\financial_history_batch_qa.ps1 -Action verify -Config configs/data/financial_history_batch20_qa_preview_v1.json
```

[Validation](../../data/financial/history_batch20_v1/validation/verification-qa-preview-v1.json):
140targetedtests PASS, compile PASS, synthetic
`run-20261020T074640Z-1b2a7419` COMPLETE, PowerShellpreviewverify PASS.
1.126inputpins verified;665fixedevidencefiles giữ nguyên (563receipts,99OCRreservations,
registry và2baselinefiles). Acquisition journal đang append được loại khỏi tuyên bố
unchangedfile; không nói globalrequests bằng0 trong lúccollector vẫn chạy.
Preview vẫn cùng outputhash khi receipt mới xuất hiện ngoài pinnedinventory;
đây là artifactreplay invariant, không phải bằng chứngPIT/backtest.

Fullsuite limitations của mục17 giữ nguyên. Activecoreprocess cũ vẫn replay dataset
đã seal; batchcollector/QA có PowerShell riêng. DefaultfinalQAconfig chưa được tạo:
phải pin finalmanifest sau khi collector terminal, không dùng configpreview thay final.
Chưa mớiPDF/OCR/acceptedfacts/metrics từ preview; baseline29/30, VNM Fnull và
strictPITmetrics0 không thay. Tiếp crawl, finalQA, publiccatalogue/cache lookup cho
8anomalyperiods cùng independentaudit, rồi selective text/OCR/review/compute.


Follow-up cache trước khi tảiPDF mới:
[ACV cache inventory](../../data/financial/history_batch20_v1/validation/acv-legacy-cache-inventory-v2.json)
đã verify2uniquePDFs FY2025/FY2024 và10reviewedimages,18pins. Legacyledger có6nonnull
FY2025references và2TTMnull, chưa import thành metric mới của historydataset.
PDF2024 có2OCRranges; không đếm thành2documents khác nhau.
Cần xem lại sourcepages, receivables/PPE/debt/issuance basis vàEPSnotes rồi tính bằng
variant hiện hành. ACV reported EPS numerator có scope riêng vàunestimatedreserve;
không alias sang`eps_adjusted_earnings_numerator` hoặc gọireserve-normalized chỉ để
fit calculator. Không download/OCR lại nếu cache đủ; sourcevintage2025comparatives
không tự trở thànhoriginal2024PITfacts. Đây là việc offline có thể tiếp tục trong
lúc worker3321 vẫn chạy (đãpoll thấy600newrequests), chưa có finalcoverage.


## 19. Execution tiếp — Sealed history20 và ACV report vintages (20/10/2026)

Worker3321 đã terminal exit0; không còn chờ worker đó. Đây là hoàn tất task
accounting của acquisition15mã bổ sung, **chưa hoàn tất F3 hoặc goal financial/PIT**.
[Acquisition snapshot](../../data/financial/history_batch20_v1/results/55c7c227fa1805a51f65/summary.json),
[final QA — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_batch20_qa_v1/d6d2ebb3241330c7def5/summary.json),
[QA config](../../configs/data/financial_history_batch20_qa_v1.json).

### Acquisition và QA cuối đợt

3.300tasks =1.486newAPI +180cachedprobes +15importedcatalogueboundary +1.619afterseriesstop.
Không pending, không parsererror;198.778raw candidate cell observations, chưa acceptedfacts.
Coverage2.940slots:2.586main candidate-present,339main missing,13auxiliary-present,
2auxiliary-missing.341missing slots thuộc115issuer-periods, chưa phải bằng chứng
không công bố. Dataset5controls cũ vẫn là input riêng, không tải hoặc sửa lại.

QA chỉ dùng target2012–2025:3.116provenstructuralzeros,1.385nonstructuralunresolvedcodes
(1nonblankorphan SHS,1.384blankcodes),17.531exactcode/label diagnostics choRegular.
3.559rawarithmetic equal/84different; annual–Q4 có13.670equal/4.414different.
Giữ3possibleannualdisplacements DCM/GAS/HSG2025; không sửa hàng hoặc tự nhận unit/scope.
Queue193issuer-periods gồm4priority1 và189priority2; không coi193kỳ đều phải tảiPDF.
Tiếp inventory cache/catalogue, xác minh fiscalperiod/identity và originalvintage,
chọn PDF theo lỗi có tác động lớn; thêm independentAPI-pass audit trước gate lên50.

Cumulative2.255logical/2.255attempts,117.066.733bytes,11PDFattempts;
anchor1792414507.836684, boundary/budget_stopfalse. Inherited batchdeadline vẫn
**22/10/2026 12:55:07.836684UTC**. Không reset khi resume hoặc chuyển nguồn.

### ACV: tái dùng cache, tính lại theo đúng phiên bản báo cáo

[Reference PowerShell](../../scripts/financial_reference_cohorts.ps1),
[config](../../configs/data/financial_reference_cohorts_acv_v1.json),
[review115facts](../../data/financial/history_batch20_v1/acv-cache-review/review-v1.json),
[summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reference_cohorts_v1/1bf8cd5e508a82af6750/summary.json),
[metrics — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reference_cohorts_v1/1bf8cd5e508a82af6750/metrics.csv).
Đã xem các trang PDF được pin, kiểm hash2PDFcached, recheck52legacyfactkeys và
review thêm63factkeys. Không tảiPDF/OCR mới;7trang FY2024 được render để đọc,
[render evidence](../../data/financial/history_batch20_v1/acv-cache-review/render-evidence-v1.json).

4cohorts cho24metricrows,12values thuộc10distinct mã–năm–familykeys; không cộng
12vintage rows như12chỉ số lịch sử độc lập.6FY2025values khớp chính xác legacy:

| Family FY2025 | Giá trị tham chiếu |
|---|---:|
| EPS | 3018,836561 VND/share |
| P/E | 14,045146 |
| P/B | 2,174645 |
| F | 4 |
| M | −2,755985 |
| Z″ EM | 9,390905 |

P/E/P/B dùng **rawclose42.400 tại28/08/2026**, annualEPS và book/commonshares31/12/2025;
không TTM, không strictcurrentratios/event-adjusted. Pin C8 canonical pricefile và
exact row; không sửa C6/C8 hoặc dùng EPSweightedshares làm denominatorP/B.
[Legacy comparison](../../data/financial/history_batch20_v1/validation/acv-legacy-recompute-comparison-v1.json)
ghi6/6exactmatch; đây là tái tính lại reference cũ ngoài pilot5, không đóng gap VNM F.

Các vintage lịch sử được giữ riêng:

| Target year | Source vintage | EPS | Z″ EM |
|---|---|---:|---:|
| 2023 | FY2024 comparative | 2953,361745 | 12,023154 |
| 2024 | FY2024 current | 4786,929488 | 12,332774 |
| 2024 | FY2025 restated comparative | 2643,909650 | 12,332774 |

EPS2024 hai giá trị là **hai report vintages**, không average hoặc chọn latest ngược lịch sử.
Note FY2025 xác nhận stockdividend vàrestatement; numerator/WAS phải cùng vintage.
EPSnumerator không phải toàn bộparentNI; không alias reportednumerator chưa normalize
reserve sang field reserve-adjusted. Không tạo fact reserve2025=0 từ dấu gạch ngang.
F dùng explicit closing currentportion+noncurrentloans, không dùng reclassificationflow.
Giữ sourceanomaly1VND giữa hai dòng lợi nhuận có ngữ nghĩa khác nhau, không tự điều chỉnh.

PrimaryFY2025 có explicit issuer websitepublication31/03/2026 trong cùng PDF;
FY2024 mới có cover/signature, publication vẫnUNKNOWN. F/M2025 cần auxiliaryFY2024
nên không lấy ngày primaryreport thay ngày của tất cả dependencies. Metadata mỗi
metric giữ unknown publication hashes. StrictPITmetrics vẫn0, không backfill số
trình bày lại vào2024 hoặc mở M3. Các metric thiếu dependency/valuation giữnull.

### Chạy lại, validation và bước tiếp

Active [core PowerShell](../../scripts/financial_history_process.ps1) đã nối verify
acquisition F3, sealedQA và referencecohorts; không tự mở50 hoặc network mới.

```powershell
.\scripts\financial_history_batch.ps1 -Action verify
.\scripts\financial_history_batch_qa.ps1 -Action verify
.\scripts\financial_reference_cohorts.ps1 -Action verify
.\scripts\financial_history_process.ps1 -Action verify
```

[Validation](../../data/financial/history_batch20_v1/validation/verification-final-batch20-reference-v1.json):
151targetedtests PASS, compile PASS, synthetic`run-20261020T100220Z-690d4975` COMPLETE,
activeverify PASS. Offline `run -MaxNewRequests0` tái tạo cùng acquisitionhash;
11networkjournals và99OCRreservations không đổi,0newrequests/0newOCR.
320frozenpins/11contracts,35referenceinputpins và6.637QAinputpins được verify/replay.
Fullrepository gate vẫn chưaPASS do knownM2-PREP frozen`docs/DECISIONS.md` mismatch;
focusedHTTP/M1rechecks của mục17 không thay fullgate hoặc waiveassertions.

Tiếp theo là publiccatalogue cho15issuer từ nguồn độc lập được phép, reusecache và
seededindependentaudit; chọn PDF cho4criticalperiods trước, phân loại missingperiods
vàintervals. Chưa hoàn tất F3quarter/YTD/PIT slices, cost/audit handoff hoặc scale50.
Baseline29/30 và VNM Fnull không đổi. Bundle5controls270facts/41annualvalues và
ACV115facts/12vintagevalues là hai outputs riêng, chưa seal một mergedPITdataset.
Goal ACTIVE/PARTIAL, không coi acquisition/reporting hoặc referencecounts là hoàn tất.


## 20. Execution tiếp — Catalogue và audit độc lập mẫu20 (20/10/2026)

**F3 vẫn PARTIAL, goal ACTIVE; chưa mở stage50.** Acquisition/QA mục19 giữ nguyên.
Không thay registryv1, baseline29/30, VNM Fnull hoặc công thức hiện hành.

### Catalogue trước PDF

[Collector HTML15issuer](../../scripts/financial_history_catalogues.ps1),
[config](../../configs/data/financial_history_catalogues_v1.json),
[acquisition](../../data/financial/history_catalogues20_v1/results/882bd6b874d5854a6e89/summary.json),
[parser](../../scripts/financial_catalogue_rows.py),
[parsed summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_catalogues20_parsed_v1/0b13e99764984cb87a5c/summary.json).
15/15HTML thu thành công,267rows gồm237financialPDFlinkcandidates và30reviewleads.
Chỉ thấy2013–2017 trong view đầu, pagination chưa exhausted; không kết luận các kỳ
sau không công bố. Prospectus/BCTN/XLS giữ là leads, không tự coi là đúng BCTC.
Không suy ngày công bố từ fiscalyear, footer hoặc filename; không đoán PDFfilename.

FOX tái discovery catalogue chính chủ2017/2024, lưu2rawHTML và exactrow/downloadhref:
[bounded observation script](../../data/financial/history20_public_discovery_v1/acquire-fox-catalogues-v2.py),
[catalogue evidence](../../data/financial/history_document_audit_fox_v1/catalogue-observation.json).
Q12024 có explicit22/04/2024 17:00; FY2017annual row không ngày. Một số row cũ có
migrationdate31/12/2020 nên không blanketaccept historicalpublication.
Scriptv1 fail trước request vì lockdirectory sai, giữ nguyên contract; successorv2
sử dụng đúng campaignworkerlock, không retry/reset failednetwork vì không có networkattemptv1.
[Web metadata observations](../../data/financial/history20_public_discovery_v1/web-metadata-observation-v1.json)
chỉ là discovery ngoài localtransport; không nhận số từ searchsnippet hoặc dùng để bỏ latches.

### Independent audit giữ nguyên mẫu

[Sampler](../../scripts/financial_history_batch_audit.py),
[config](../../configs/data/financial_history_batch20_audit_v1.json),
[six fixed tasks — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_batch20_audit_v1/96424cd3aa460905e541/audit-tasks.json).
Seed `financial-history-F3-independent-audit-v1`, chọnRegularissuer theoexchange/currentprofile
vàregistryid, loạiACV vì đãreview bằng chứng trước. Mộtannual+quarter theo3eras,
chỉ chọn cohort qua5rawchecks và9mappedfields; không chọn theoPDFavailability hoặc reseed.
Bank/securities EIB/STB/SHS chưa được mẫuRegular này xác nhận schema/applicability.

| Mẫu cố định | Trạng thái đối chiếu9fields |
|---|---|
| VCS FY2015 | 9/9match |
| VCS Q3/2019 | PDF chưa thu, giữ nguyên mẫu |
| FOX FY2017 | 9/9match |
| FOX Q1/2024 | 9/9match, CFOexplicitYTD01/01–31/03 |
| DBC FY2022 | 8/9exactmatch,1expensepresentationsign |
| DBC Q4/2013 | PDF chưa thu, giữ nguyên mẫu |

[Unit config F3](../../configs/data/financial_candidate_units_batch20_v1.json),
[unit summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_candidate_units20_v1/c2d7eae97236a16409c7/summary.json):
17.531mappedrows,16.704monetaryrawVND được chứng minh từ displaycontract,827EPSformatter
held. Unitproof không accept row/scope/vintage hoặc biếnreportedEPS thànhrecompute.

[Audit review configv3](../../configs/data/financial_history_batch20_audit_review_v3.json),
[summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_batch20_audit_review_v1/7147b11547c7aea1871d/summary.json),
[quarantine — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_batch20_audit_review_v1/7147b11547c7aea1871d/candidate-quarantine.json).
Đã review4PDF/36fields:35match,1signedrawconflict; vẫn2pendingdocuments và0accepted/PITfacts.
DBC giá vốn PDF physical12 là(10.598.058.965.427), APIpositive cùng độ lớn. PDF dùng
signedexpense:11.557.594.666.247 + (−10.598.058.965.427) =959.535.700.820grossprofit.
Exactcomparison giữ nguyên âm, không tự abs(), không gọi đây là rowshift hoặc lỗi giá trị
kinh tế. Cần explicit source-to-canonical sign normalization trước acceptedcompute.

4PDF là bản báo cáo gốc tải quaobservedURLs; VCS từStockbiz, FOX từissuerwebsite,
DBC làissuerdisclosure trênVietstockmirror. Mỗi review pinPDFSHA,physicalpages,
rowlabels,unit/scope/currentyearcolumn. Tất cảPDFscan: ưu tiêntext trước, sau đó
OCRchọn7VCS+9FOX+5DBC =21newpages; campaign120charged/successful,0errors.
[OCRv9](../../configs/data/financial_ocr_campaign_v9.json),
[OCRsummary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_ocr_campaign_v1/results/3d140bb7633beeea825e/summary.json).
DBC physical1 công bốwebsite31/03/2023; ngày kýBCTC30/03/2023 giữ riêng.
DateOnlypublication vẫn cần PIToverlay/calendar/dependency acceptance; audit không mởM3.

### Replay và công việc tiếp

[Core PowerShell](../../scripts/financial_history_process.ps1) nối10documentconfigs,
OCRv9, catalogue/parser, sampler, unitsoverlay vàauditreviewv3; verify không network.
Dedicated collectionCLI giữ caps/counters và chỉ tiếp job chưa córeceipt.

```powershell
.\scripts\financial_history_catalogues.ps1 -Action verify
.\scripts\financial_history_process.ps1 -Action verify
```

Cumulative2.276logical/2.276attempts,147.695.077bytes,15PDFattempts;
anchor1792414507.836684 và batchdeadline22/10/2026 12:55:07.836684UTC giữ nguyên.
So mục19 thêm21requests gồm17HTML+4PDF; không tải237linkcandidates hoặc193queueperiods.
Caps1worker/2s/2attempts,72hbatch/90dcampaign,50PDFbatch,40OCR/PDF/1000batch/12000campaign
vàsource boundaries không reset khi chuyểnnguồn/resume.

Tiếp tìm đúng2samplePDF còn thiếu và4priorityperiods DCM/GAS/HSGannual2025,
SHS2025orphan; phân loại341missingcoverage slots bằngidentity/fiscalperiod/cache/catalogue.
Quarter/YTD/TTM/PIT delivery, dependencyacceptance vàcostprojection chưa hoàn tất.
Audit4/6 không thayfullF3gate; không coi35fieldmatches là bộ chỉ số đã hoàn thành.


[Checkpoint validation](../../data/financial/history_batch20_v1/validation/verification-f3-catalogue-audit-v1.json):
161targetedtests,compile,synthetic`run-20261020T121533Z-1bfbc455` vàactivePowerShellverify PASS.
Offlinecatalogueresume tái tạo cùnghash;136files gồm16networkjournals và120OCRreservations
không đổi;31historycontracts/569pins đãverify,457localMarkdownlinks tồn tại.
Scopevalidation này không làfullrepositorygate hoặc fullfinancialgoalPASS; knownM2-PREP
frozen`docs/DECISIONS.md` mismatch vẫn tồn tại, không refreeze/waive.


## 21. Execution tiếp — GAS PDF reference và SHS critical quarantine (20/10/2026)

**F3delivery và goal vẫn PARTIAL; không mở50.** Không sửa các output mục20.
Đã có bằng chứng bổ sung cho2priorityperiods, không sửaqueue193periods cũ để che mất findings.

### GAS: xác nhận lệch annual và tính lại reference từ PDF

[Original issuer PDF receipt](../../data/financial/history_document_critical_gas_shs2025_v1/receipts/GAS-FY2025-CRITICAL-REVIEW.json),
[32reviewedfacts](../../data/financial/history_document_critical_gas_shs2025_v1/reference-review-v1.json),
[referenceconfig](../../configs/data/financial_reference_cohorts_gas_v1.json),
[reference summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_reference_cohorts_gas_v1/275b1ffab451b6125b32/summary.json).
Đúng BCTC hợp nhất kiểm toán31/12/2025, physical9–11, VND. Explicit publication04/03/2026
trong công bốphysical1; signature28/02/2026 giữ riêng. Text nhiều trang chỉ có digitalstamp,
không coi đó là numerictext extraction thành công; OCR6selectedpages.

| Family | Target year | Report vintage | Giá trị reference |
|---|---|---|---:|
| Z″EM baseline | 2025 | FY2025current | 10,9312998663 |
| Z″EM baseline | 2024 | FY2025comparative | 11,3484992636 |

2cohorts/12metricrows/2nonnullvalues,8accountingchecks PASS. Giữ nguyên EBITbridge và
annualEMZ″+3.25 hiện hành; không quarterlyannualization hoặc M-scorevariant mới.
EPS/P/E/P/B/F/M vẫnnull do thiếu revieweddependencies/valuation; không dùngreportedEPS làmrecompute.
Đây là2referencevalues, strictPIT0; không backfill comparative2024 vào quá khứ trướcpublication2026.

GAS annualHK `other_short_term_payables`: API1.308.805.721, PDF333.114.428.193;
`short_term_loans_and_finance_leases`: API333.114.428.193, PDF1.439.827.466.686.
Q4H cùngnamedfields khớpPDF. Xác nhận lỗi trong2fields, giữ annualHKCDKT partition
khỏi APIacceptance; không dịch tất cả hàng theooffset hoặc ưu tiênQ4 tự động.
PDFfacts được review theoexactnamedrows và tạo referencecohort riêng.

### SHS: tái dùng cache và phát hiện named zero sai

[CachedPDF inventory](../../data/financial/history_batch20_v1/shs-cache-review/cache-inventory-v1.json),
[review cases](../../data/financial/history_batch20_v1/critical-source-review-v1.json).
Đã bỏ sót cachedPDF10.062.449bytes trước2attempts tải bảnVI/EN từissuerwebsite.
Cả2newfiles chạm25MBcap, giữFAILEDreceipts và50.000.000downloadedbytes trongledger;
khôngnângcap, khôngrange-download/retry cùngfiles. Tái dùngcachedPDFSHA9b9b9262…,
đối chiếu originalinventory; nguồn mới không thaypublication/vintagecủacache.

Physical1 xác nhận BCTC riêng/no subsidiary; cashflowphysical17 choFY2025, VND.
7namedfields cóPDFnonzero nhưngAPIzero: chi phí lãi vay280.317.407.994;
tổngchi phíphi tiền tệ422.770.638.973; phải thu dịch vụ46.222.432.586;
chi phí phải trả6.075.200.260; chi phí trả trước−22.507.904.639;
thuếTNDNđã nộp−169.848.109.078; lãi vay đã trả−237.612.094.939.
CFO PDF−6.222.933.266.678 vàPBT1.649.368.012.380 khớprawAPI.
`HDKD_1=680.759.314.148` vẫn không nhãn/không giải thích được; không suyCFO hoặczeroheading.
Quarantine SHSannualKLCTT cảpartition, không đưaRegularF/M/Z lêncôngty chứng khoán.

Websitepage22/03/2026 không được gán cho cachedPDFdisclosuredated23/03/2026;
khácPDFhash/possiblevintage và inconsistentdate cần giữunknownpublicationlinkage.
Cachetext57pages offline; OCRchọn4pages để review, không OCR toàn57pages.

### Replay quarantine và source gaps

[Criticalreview CLI](../../scripts/financial_critical_review.py),
[config](../../configs/data/financial_critical_review_gas_shs2025_v1.json),
[summary — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_critical_review_v1/4c87c15431782b8e491b/summary.json),
[partition quarantine — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_critical_review_v1/4c87c15431782b8e491b/partition-quarantine.json).
14comparisons:4rawmatches,2rawdifferences,7PDFnonzero/APIzero,1unresolvednonzeroorphan.
9numericconflicts+1orphan,2sourcepartitions held;0APIacceptedfacts/0automaticrepairs.
Rawcomparison không tự chứng minhproviderunits, scopeacceptance hoặc PIT.
F3promotion phảiconsume outputholds cùng QA cũ, không chỉ xét parsererrorcount=0.
6newtests chặn orphan→CFO, namedzeroacceptance, wrongreportyear, quarterthayannual,
duplicatecell vàmatch→unitacceptance.

Đã thu thêmBMSC DBC Q4/2013disclosureHTML: exactattachment trỏlegacyHTTPHNXaction,
khôngguessPDFfilename/upgradeURL để tải. HaiVDSCcatalogue trảHTTP302; khôngfollow
redirect hoặc thửclient khác. Đây là sourceaccessresults, chưa chứng minh không công bố.
Mẫuindependentaudit vẫnVCSQ32019/DBCQ42013 pending, khôngresample.
DCM/HSGFY2025 vẫn cầnoriginalPDFreview; SHSorphancode chưaresolved.

[OCRv10](../../configs/data/financial_ocr_campaign_v10.json):130charged/successfulpages,
0errors; anchor/batch1000/campaign12000/perPDF40 giữ nguyên.
Cumulative2.284logical/2.284attempts,211.688.837bytes,18PDFattempts,0globalboundary/budgetstop.
So mục20 thêm8logicalrequests,1newPDFacquired,2PDFsizecapfailures,1cachedPDFreused,
10newOCRpages. Original72hdeadline22/10/2026 12:55:07.836684UTC khôngreset.
Cácwebmetadatadiscoverycalls giữ riêng trongsourceobservations, không làlocaltransportcount.
CorePowerShellverify nối12documentconfigs, observationreplay, OCRv10, criticalquarantine
vàGASreference; khôngnetwork mặc định. Baseline29/30/VNM Fnull vàoutputsACV/pilot5 giữ riêng.
167targetedtests/compile/synthetic`run-20261020T124500Z-00b60886` PASS;
activePowerShellverify PASS, chưa fullF3/PITdelivery hoặcfullrepositorygate.


[Cache preflight inventory](../../data/financial/history_batch20_v1/cache-preflight/results/18a4740f73d6c3003b99/summary.json)
đãhash209PDFfiles/200uniquePDFhashes. [Builder offline](../../data/financial/history_batch20_v1/cache-preflight/build-v1.py)
để refresh trước documentacquisition tiếp. Filename ticker/year chỉ làsearchhints, khôngcanonicalidentity,
reportperiod/scope/publicationacceptance. Manifest pin registry vàbuilder; khôngcopy hoặc sửaPDFcache.


[Validation checkpoint21](../../data/financial/history_batch20_v1/validation/verification-f3-critical-gas-shs-v1.json):
167targetedtests/compile/synthetic/activeverify PASS;151network/OCRfiles (21journals+130reservations)
unchanged trongoffline replay;37historycontracts/621pins,15criticalreviewpins và19GASreferencepins
đãverify. Cacheinventoryreplay cùnghash; registryv1 không đổi. Không cófullgoal/F3deliveryPASS.


## 22. Owner đổi thứ tự: acquisition trước, review sau (20/10/2026)

Owner đã chấp thuận tách thu thập candidate API khỏi quá trình kiểm chứng chi tiết. Đây là thay đổi sequencing acquisition, không phê duyệt dữ liệu nghi vấn hoặc nới numeric, historical identity, PIT, financial features, research hay M3 gates. Mục này supersede yêu cầu hoàn tất F3 document review/vertical slices trước khi mở candidate acquisition50; các snapshot và quyết định cũ giữ nguyên làm evidence.

### Flow đang chạy

1. Giữ pilot5 và additional15 đã terminal: tổng20 mã có task accounting, không đồng nghĩa đủ coverage 13 năm.
2. Thu thêm30 provider partitions theo registry/legacy identity join có bằng chứng, mục tiêu tổng50. Candidate assignment pin registry hash, domain/range/batch; issuer/security identity vẫn provisional. Không gọi current sample là historical universe.
3. API annual/quý/lũy kế2013–2025, closing annual CDKT2012 nếu endpoint cung cấp. Giữ raw/template/source/hash/receipts từ đầu; không thay bằng reported ratios. Catalogue CafeF đang latched được ghi deferred/access-blocked; không vòng qua boundary.
4. Sau mỗi batch: xuất task accounting/coverage, parser/schema/quarantine findings và missing periods; cập nhật hàng đợi review. Không đợi xử lý hết PDF/OCR mới kết thúc acquisition batch. Nếu access-control, timeout/budget/disk, interrupted requests hoặc integrity lỗi: dừng an toàn, không reset.
5. Batch100 và các batch≤100 chỉ được mở sau evidence acquisition/resume/parser/cost của batch50; chưa tự cấp numeric acceptance hay tuyên bố đã thu thập1.500 mã.

**Tạm dừng tải PDF/OCR và manual field review mới.** Cache DCM/HSG đã tải giữ nguyên. Không xử lý tiếp VNM F bằng suy số; pilot vẫn29/30. Reference/PIT verification là hàng đợi riêng sẽ review cùng owner sau.

### Output/commands

- [Config acquisition-first](../../configs/data/financial_acquisition_first50_v1.json).
- [PowerShell acquisition](../../scripts/financial_acquisition_first.ps1).
- [Assignment30](../../data/financial/history_acquisition_first50_v1/assignment.json).
- [Report các field nghi vấn — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-acquisition-first-review-v1/report.md), [chi tiết JSONL — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-acquisition-first-review-v1/review-items.jsonl).

```powershell
pwsh -File scripts/financial_acquisition_first.ps1 -Action plan -MaxNewRequests 0
pwsh -File scripts/financial_acquisition_first.ps1 -Action run -Network -MaxNewRequests 4200
pwsh -File scripts/financial_acquisition_first.ps1 -Action verify -MaxNewRequests 0
```

Ba mươi mã mới: HCM, BVH, PHP, IDC, BSR, QNS, DGW, SCS, VND, DHC, PAN, TCB, CII, VPB, SIP, VCG, KSB, VHC, KDH, FRT, CEO, PLC, KDC, HDG, SAB, SHB, PNJ, MBB, DGC, ANV. Không gán ticker alias cùng issuer nếu chưa có bằng chứng; không dùng legacy ID như canonical. Hai mã còn lại trong legacy50 pool nằm deferred assignment; nhóm20 trước chứa BRC/VNM ngoài legacy50.

### Budgets/QA

Kế thừa nguyên parent DCM/HSG network:2.286 logical/attempts,236.091.355bytes,20PDFattempts, created_at1792414507.836684; deadline22/10/2026 12:55:07.836684UTC không đổi. Cap additional30≤4.200 API requests/8.400 attempts; toàn journal≤6.486logical/10.686attempts; response≤5MB, total≤2.236.091.355bytes; concurrency1/spacing≥2s/≤2attempts/20s timeout. Không PDF/OCR mới.72hbatch/90dcampaign,30GBdiskfloor, source boundaries và worker lock giữ nguyên.

Acquisition PASS = terminal receipts/explicit stops + intact raw hashes + complete task accounting + checkpoint/replay; thiếu kỳ phải report. Acquisition PARTIAL nếu pending/blocked/interrupted; không đổi missing thành0. Numerical verification/PIT/M3 vẫn PARTIAL cho đến khi đủ evidence riêng.

Validation trước network:14targetedtests PASS, compile PASS, synthetic `run-20261020T131409Z-335d4c67` COMPLETE. Full repo gate chưa PASS do known M2-PREP frozen docs hash mismatch; không sửa/waive old assertion hoặc dùng targeted tests để tuyên bố fullgate PASS.

Worker acquisition-only đã start: exec session3663; log `data/financial/history_acquisition_first50_v1/worker.log`, progress receipts/journal cùng root. Đã nhận raw API đầu tiên; chưa terminal/coverage cuối. Không chạy worker thứ hai cùng lúc. Snapshot backlog có8.385observations/checks (có overlap, không phải8.385lỗi độc lập). Preflight pin/assignment/replay PASS trong `validation/acquisition-first-preflight-v1.json`.


## 23. Acquisition tổng50 đã terminal (20/10/2026)

Additional30 worker session3663 exit0:3.358new API requests,385.792candidate observations,0parsererrors,0pending.6.600tasks=3.358ACQUIRED+30IMPORTED_SOURCE_BOUNDARY+3.212NOT_REQUIRED_AFTER_SERIES_STOP. Final result`b31a3dd1325164117f53`. APIcandidate scope tổng50, không phải50mã đủ13năm/metrics/PIT.

Additional30:5.052/5.850main slots có groups,798main thiếu;auxiliary2012 có23/30,7thiếu. Quarantine6.363unmapped+3.041blankcells, khônggán nhãn bằng vị trí. KhôngPDF/OCR mới. Parent counters5.644logical/attempts,267.795.832bytes,20PDFattempts, originalanchor1792414507.836684, boundary/budget_stopfalse. Networkcuối20/10/2026 15:08:13.796939UTC.

[Report/coverage và next steps — archive](../../artifacts/archives/project-cleanup-20261023/historical-reports-and-scratch.zip). Next: offline QA/schema/coverage backlog → engineeringgate +assignmentadditional50(tổng100) →API batches≤100. Không chờ giải quyết hếtfield/PDF trước candidate acquisition; không mở numeric/PIT gates.


## 24. QA batch50 và mở acquisition tổng100 (20/10/2026)

QA offline additional30 đã hoàn tất tại [snapshot — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_acquisition_first50_qa_v1/01dd746e698cebea9984/summary.json).385.792inputcells;6.072structural headerzeros;2.865unresolvednonstructuralcodes;0invalidtokens/0valueconflicts/0parsererrors.32.529exact-labeldiagnosticcells;accounting6.535equal/232different;annual–Q424.597equal/9.855different;3row-displacementpatterns tạiFRT/SCSFY2025;805missingcoverage slots;42templatevariationcohorts. Không tựrepair/accept. Templatefamily exact fingerprint đểdiagnostic:23Regular,4Bank,2Securities,1UNKNOWN(BVH); không phải ngành/canonicalidentity đượcaccepted.

[Report review mới — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-acquisition-first50-qa-v1/report.md) và [field evidence — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-acquisition-first50-qa-v1/review-items.jsonl) giữ13.802items có overlap; queue473issuer-periods chỉ làreviewqueue, không phải lệnh tải473PDF. Backlog20trước giữ nguyên ởmục22.

[Engineering gate](../../data/financial/history_acquisition_total100_v1/preflight/engineering-gate.json) PASS choadditional50candidates:terminaltaskaccounting,parser,oldacquisitionreplay,QAmanifest/rawhashproof,reviewqueue,unchangedanchor/transportlatches,disk/artifact/deadline/cost. Không promote metrics/PIT/M3. Cost projection khoảng5.597requests, max7.000; khoảng3,4giờnetwork theo2,2s/request, không phảiSLA. Conservativefinancialartifactupperbound7,06GB<50GB, free~98,9GB>30GB.

### Assignment/commands

- [Assignment additional50](../../configs/data/financial_acquisition_total100_assignment_v1.json):15HOSE/13HNX/22UPCoM, loạiprevious50, ưu tiênCTD/VHMdeferred rồiregistry_idstableorder. Candidate pool cóunique current ticker/exchange/legacyID từregistry; chưahistoricaluniverse hoặccanonicalidentity.
- [Config](../../configs/data/financial_acquisition_total100_v1.json); [PowerShell generic batches](../../scripts/financial_acquisition_batches.ps1). Runner mới hỗ trợbounded1..100, giữfrozenrunneradditional30 vàoldartifacts.

```powershell
# Offline QA/replay (verify có thể tốn CPU; không network)
$python = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $python scripts/financial_acquisition_qa.py run --config configs/data/financial_acquisition_first50_qa_v1.json
# Acquisition next batch
pwsh -File scripts/financial_acquisition_batches.ps1 -Action plan -MaxNewRequests 0
pwsh -File scripts/financial_acquisition_batches.ps1 -Action run -Network -MaxNewRequests 7000
pwsh -File scripts/financial_acquisition_batches.ps1 -Action verify -MaxNewRequests 0
# Progress
Get-Content data/financial/history_acquisition_total100_v1/worker.log -Tail 20 -Wait
```

Budgets kế thừa5.644logical/attempts,267.795.832bytes,20PDFattempts. Max12.644logical/19.644attempts/2.267.795.832totalbytes,5MBresponse/20stimeout/≤2attempts/≥2sspacing/1networkworker. PDF/OCR0new. Originalcreated_at1792414507.836684,72hdeadline22/10/2026 12:55:07.836684UTC,90dcampaign khôngreset. Sourceboundaries vàglobalworkerlock giữ nguyên. Acquisition-only sourcegate không thayfullF3quality/PIT.32targetedtests/compile/synthetic`run-20261020T153321Z-369ec6ab`PASS;fullrepo vẫnknownfrozenM2-PREPdocshashmismatch, khôngwaive.

Worker APIadditional50 đã start ởlocalexecsession74783; log `data/financial/history_acquisition_total100_v1/worker.log`. Pre-networkzero-request run vàverify exit0 tái lập cùngsnapshot`3ebdf3f745a61f8c6cb3`:50importedcatalogueboundaries,3.950after-series-stop,7.000pendingAPI. [Preflight validation](../../data/financial/history_acquisition_total100_v1/validation/preflight-v1.json) pin32tests/compile/synthetic/QAmanifest/replay/26contractpins. Batch100 chưa terminal; đang50đãthu+50đangchạy, khôngclaim100complete.


## 25. Tổng 100 đã thu thập, xếp batch thêm 100 mã (21/10/2026)

Batch additional50 đã terminal tại [snapshot](../../data/financial/history_acquisition_total100_v1/results/d7fdfcba18ea2005224e/summary.json): 4.350 requests mới, 464.021 candidate observations, 0 parser errors, 0 pending. Task accounting 11.000 = 4.350 ACQUIRED + 50 IMPORTED_SOURCE_BOUNDARY + 6.600 NOT_REQUIRED_AFTER_SERIES_STOP. Coverage main: 5.979 slots có candidate groups, 3.771 thiếu; auxiliary closing2012: 23 có/27 thiếu. Đây là candidates, không phải 100 mã đủ lịch sử hoặc chỉ số/PIT.

Owner yêu cầu mở thêm batch để tăng số mã. Dùng lại generic runner và QA hiện hành, không sửa frozen source/code/data. [Assignment mới](../../configs/data/financial_acquisition_total200_assignment_v1.json) gồm 100 provider partitions mới: 36 HOSE, 21 HNX, 43 UPCoM; không trùng 100 mã trước. Universe vẫn là current discovery engineering sample, historical identity chưa accepted.

### Pipeline tự nối một batch, có điều kiện

[Continuation script](../../data/financial/history_acquisition_total200_v1/continue-after-qa.ps1) chạy ẩn ở máy local, PID17800: chờ đúng QA và verify của batch100 → lưu logs bền vững → xuất review backlog và kiểm engineering gate → zero-request run/verify → crawl additional100. Nếu QA, hash, source boundary, budget, deadline, disk hoặc process identity lỗi, pipeline ghi HELD/FAILED và không tự restart. Không mở batch thứ hai, không PDF/OCR, không tự tắt máy. Marker hủy chế độ shutdown cũ đã được tạo.

Trạng thái realtime: [pipeline-status.json](../../data/financial/history_acquisition_total200_v1/pipeline-status.json). [Preflight assignment validation](../../data/financial/history_acquisition_total200_v1/preflight/assignment-validation.json) PASS: 100 mã mới, 22.000 tasks/14.000 API task ceilings, không trùng; 16 targeted tests PASS; script AST/dry-run/builder compile PASS. QA và final source gate còn chờ nên chưa claim batch200 RUNNING/COMPLETE. Sau gate PASS, config sẽ được tạo tại `configs/data/financial_acquisition_total200_v1.json`; chưa chạy config chưa freeze.

Counters kế thừa: 9.994 logical/attempts, 306.189.160bytes, 20PDFattempts. Cap sau gate: ≤23.994 logical/37.994 attempts/2.306.189.160total bytes; 1 worker, spacing≥2s, timeout20s, ≤2 attempts, response≤5MB. PDF/OCR0new; budget50GB/diskfloor30GB và deadline gốc22/10/2026 12:55:07.836684UTC/90ngàycampaign không reset. Dự phóng khoảng8.700requests/5,3giờ network theo batch trước; không phải SLA.

```powershell
# Xem pipeline đang chờ QA, tạo gate hay đã crawl
Get-Content data/financial/history_acquisition_total200_v1/pipeline-status.json
# Khi stage đã RUNNING_CANDIDATE_ACQUISITION
Get-Content data/financial/history_acquisition_total200_v1/worker.log -Tail 20 -Wait
```

Full repository gate vẫn chưa PASS do known frozen M2-PREP docs hash mismatch; không waive assertion. Candidate-only engineering gate không thay full financial quality/PIT/M3 acceptance. Findings của batch100 sẽ vào report `artifacts/reports/financial-acquisition-total100-qa-v1/` khi QA hoàn tất; backlog cũ không sửa.


## 26. Owner yêu cầu tăng tốc: successor 1 giây/request (21/10/2026)

Owner yêu cầu gọi API nhanh hơn. Spacing financial được điều chỉnh từ2s xuống1s cho phần còn lại batch200, vẫn concurrency1. Đây là thay đổi rate policy được owner yêu cầu, supersede spacing2s trong các mục trước cho successor này; không tăng retries, không clear access-control latch, không đổi dữ liệu/PIT hoặc deadline. Thời gian chờ lý thuyết giảm một nửa; throughput thực tế còn phụ thuộc latency và I/O.

Crawler cũ PID17984 được tạm dừng rồi dừng hẳn chỉ sau khi journal xác nhận REQUEST_RESERVED attempts0 và reserved_bytes0: chưa gửi HTTP kế tiếp. [Handoff evidence](../../data/financial/history_acquisition_total200_rate1_v1/preflight/handoff.json) giữ source journal hash, pending key, original counters và contract hash. Các receipts/raw cũ được pin và tái sử dụng nguyên bytes trong successor; không sửa source artifacts. Request reserved0 dùng lại cùng cache_epoch/key, không retry request đã attempt và không tăng logical counter cho cùng reservation.

[Config rate1](../../configs/data/financial_acquisition_total200_rate1_v1.json), [runner](../../scripts/financial_acquisition_rate1.ps1), [pipeline status](../../data/financial/history_acquisition_total200_rate1_v1/pipeline-status.json). Phần thu thập vẫn cùng100 mã bổ sung của batch200, không phải thêm100mã nữa. Source batch200 partial không cộng trùng với successor khi tổng hợp.

Budgets giữ nguyên tuyệt đối từ config cũ: max23.994logical/37.994attempts/2.306.189.160bytes,20PDFattempts,5MBresponse,20stimeout,≤2attempts. Created_at1792414507.836684 và deadline22/10/2026 12:55:07.836684UTC không reset. Counters handoff11.220logical/11.219attempts/316.790.771bytes; chênh1 do reservation chưa attempt. HTTP401/403/429/challenge vẫn latch và dừng, không tự retry/bypass. Không PDF/OCR hoặc numeric/PIT acceptance.

Validation:23unique targeted cases (6rate/inheritance +1real transport with fake opener +16existing collector/batch tests), compile PASS; synthetic`run-20261021T041510Z-3bb191ae` COMPLETE. Test transport chứng minh request0 dùng lại key, logical count không tăng, attempt tăng0→1 và sleep đúng1s. Offline checkpoint import/replay phải PASS trước network. Known full-repository M2-PREP frozen-doc mismatch giữ nguyên, không waive.

```powershell
Get-Content data/financial/history_acquisition_total200_rate1_v1/pipeline-status.json
Get-Content data/financial/history_acquisition_total200_rate1_v1/worker.log -Tail 20 -Wait
```

Bản cũ `history_acquisition_total200_v1/pipeline-status.json` trỏ MIGRATED_TO_RATE1_SUCCESSOR; không xem status cũ là crawler mới đang lỗi. Chưa claim resume RUNNING cho đến khi offline replay hoàn tất và worker mới được start. Không tắt máy sau batch này.

Rate1 đã resume ởexecsession11157 sauzero-requestreplayPASS, snapshot`f62f6376fc8aa61c55dd`. Giữ nguyên9.225source receipts và22.000tasks. [Validation](../../data/financial/history_acquisition_total200_rate1_v1/preflight/rate1-validation.json) xác nhận reserved key0 được dùng lại không tăng logical counter, observed54attempts/54responses; mediangap1.005s trong mẫu đầu, chưa phải bảo đảm throughput toàncampaign. Worker đang chạy; boundary/budget_stopfalse ởsnapshotđo.


## 27. Tổng200 terminal; nối batch100 mới hướng tới tổng300 (21/10/2026)

Batch additional100 đã hoàn tất tại [snapshot](../../data/financial/history_acquisition_total200_rate1_v1/results/8c44b0701865404486d3/summary.json): 9.266 ACQUIREDresponses/1.007.884candidatecells/0parsererrors/0pending.22.000tasks=9.266ACQUIRED+100IMPORTED_SOURCE_BOUNDARY+12.634after-series-stop. Maincoverage13.104present/6.396missing; auxiliary2012:54present/46missing. Source checkpoint partial trước rate1 không cộng trùng. Tổng200 mã có task accounting, chưa đủ financial history/PIT.

Owner yêu cầu bước tiếp theo. [Assignment additional100](../../configs/data/financial_acquisition_total300_assignment_v1.json) đã pin registry, loại200mã trước, chọn stable registry_id:33HOSE/25HNX/42UPCoM. Current provider partitions vẫn provisional, không phải historical research universe.

### Acquisition integrity gate và review deferred

Thêm [streaming acquisition audit](../../scripts/financial_acquisition_audit.py), [config](../../configs/data/financial_acquisition_total200_audit_v1.json): verify mỗi manifest/receipt/rawhash, parse lại raw thành candidate shard và so exactbytes, task accounting, structural rootzero proof, invalid/unmapped fields, coverage. Chạy theo shard để không giữ toàn bộ1triệucells trong RAM. Không gọi arithmetic/annual–Q4/PDF/institution-classification hoặc numeric/PIT verification là hoàn tất; các bước semantic review đó được deferred theo owner acquisition-first. Review findings sẽ nằm tại `artifacts/reports/financial-acquisition-total200-v1/` sau audit. Gate mới vẫn yêu cầu exact replay/source integrity và zero invalidtokens, không nới numeric acceptance.

[Continuation pipeline](../../data/financial/history_acquisition_total300_v1/continue-after-audit.ps1), PID3380, tự nối đúng1batch: chờ auditPID7800 → persist audit/review/gate → zero-requestrun/verify → networkadditional100. Nếu source/hash/parser/identity/budget/deadline/disk hoặc audit lỗi thì ghi HELD và không restart. Không PDF/OCR hoặc auto shutdown. [Trạng thái realtime](../../data/financial/history_acquisition_total300_v1/pipeline-status.json) và [preflight assignment validation](../../data/financial/history_acquisition_total300_v1/preflight/assignment-validation.json).

Generic fresh-batch runner rate1 mới: [PowerShell](../../scripts/financial_acquisition_batches_rate1.ps1), [Python](../../scripts/financial_acquisition_batches_rate1.py). Giữ frozen runners cũ; áp dụng policy owner đã duyệt1giây/request, concurrency1, ≤2attempts, timeout20s, response≤5MB, 401/403/429/challenge vẫn hard-stop. Config `configs/data/financial_acquisition_total300_v1.json` chỉ sinh sau gate PASS. Chưa claim tổng300 đã chạy khi pipeline còn chờ audit/gate.

Counters kế thừa19.260logical/attempts,389.061.341bytes,20PDFattempts; cap newbatch≤33.260logical/47.260attempts/2.389.061.341bytes; tối đa14.000APIrequests mới. Originalcreated_at1792414507.836684/72hdeadline22/10/2026 12:55:07.836684UTC/90dcampaign không reset. Diskfloor30GB/artifactcap50GB giữ nguyên. Dự phóng khoảng9.266requests/2,8giờnetwork theo batch trước ở1,1s/request; không phải SLA.

```powershell
Get-Content data/financial/history_acquisition_total300_v1/pipeline-status.json
# Khi stage đã RUNNING_CANDIDATE_ACQUISITION_RATE1
Get-Content data/financial/history_acquisition_total300_v1/worker.log -Tail 20 -Wait
```

Validation:24targetedtests/compile/synthetic`run-20261021T090916Z-b7ccc331`PASS, scripts AST/dry-run và assignment100/22.000unique tasks PASS. Fullrepo gate còn known frozenM2-PREPdocsmismatch, không waive. Numerical/PIT/M3 delivery vẫn PARTIAL và baselineFY2025 vẫn29/30.

Streaming audit đã hoàn tất PASS tại [snapshot — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_acquisition_total200_audit_v1/d2259900423f9cf95c6a/summary.json): replay9.266rawresponses/exactcandidatebytes,1.007.884cells; fieldstatuses `{"PROVEN_STRUCTURAL_HEADER_ZERO": 15547, "UNIQUE_CODE_LABEL_CANDIDATE": 927558, "UNRESOLVED_MAPPING": 4983}`; missing6442slots; review11425items. [Report — archive](../../artifacts/archives/project-cleanup-20261023/historical-reports-and-scratch.zip) và [field evidence — archive](../../artifacts/archives/project-cleanup-20261023/historical-reports-and-scratch.zip) đã ghi. Gate additional100 đã PASS; pipeline chuyển OFFLINE_PLAN_AND_VERIFY, chưa claim network RUNNING/300complete.

## 28. Batch300 và delay0,4s (21/10/2026)

Owner yêu cầu giảm delay dưới0,5s và tăng batch. Lượt hiện tại gồm300 provider partitions:100 từ checkpoint total300 đang dở và200 mới;99HOSE/86HNX/115UPCoM. Cộng200 mã đã terminal hướng tới tổng500, không phải500 đã hoàn tất. [Assignment](../../configs/data/financial_acquisition_total500_bulk_assignment_v1.json) pin registry và giữ chính xác checkpoint membership. Identity vẫn provisional; không nhận historical/PIT readiness từ ticker.

[Config](../../configs/data/financial_acquisition_total500_bulk_v1.json), [runner](../../scripts/financial_acquisition_bulk.ps1), [controller](../../data/financial/history_acquisition_total500_bulk_v1/run-bulk.ps1). Minimum spacing0,4s giữa attempts; một network worker. Tám local I/O workers chỉ đọc file. Indexed cache, streaming journal và aggregated coverage giảm overhead; snapshot fixture được so byte-equivalent với runner cũ. HTTP latency/disk vẫn ảnh hưởng throughput, không cam kết2,5responses/giây.

Cutover bằng suspend→kiểm journal→stop chỉ tại REQUEST_RESERVED attempts0, reserved_bytes0, không HTTP in-flight. [Handoff](../../data/financial/history_acquisition_total500_bulk_v1/preflight/handoff.json) pin source contract/journal và reserved request key. Kế thừa20.381logical/20.380attempts/398.695.110bytes/20PDFattempts; request đã reserve được dùng cùng key/cache epoch, không tính logical lần nữa. Source receipts immutable được hardlink, có fallback byte-copy/hash check. Checkpoint total300 cũ chỉ là nguồn kế thừa, không cộng riêng vào completed200.

Limits được tăng theo200 mã mới:61.260logical/103.260attempts/4.389.061.341bytes; tối đa42.000APIrequests cho wave300. Giữ attempt≤2, timeout20s, response≤5MB,20PDFattempts; original created_at1792414507.836684, deadline22/10/2026 12:55:07.836684UTC,90ngày/campaign không reset. Diskfloor30GB/artifactcap50GB giữ nguyên. 401/403/429/challenge vẫn hard-stop, không tự retry qua latch. No PDF/OCR, numeric acceptance, PIT promotion, automatic restart/batch tiếp hoặc shutdown.

23targetedtests (gồm streaming resume/key/spacing), compileall và synthetic `run-20261021T094639Z-e10e845a` PASS. Offline zero-request snapshot/verify phải PASS trước network. Trạng thái thực tế đọc tại [pipeline-status](../../data/financial/history_acquisition_total500_bulk_v1/pipeline-status.json); log ở [worker.log](../../data/financial/history_acquisition_total500_bulk_v1/worker.log). Numerical/PIT/M3 vẫn PARTIAL, pilotFY2025 giữ29/30; field nghi vấn tiếp tục deferred review theo owner. Full repository gate còn known frozen M2-PREP hash mismatch, không waive.

```powershell
Get-Content data/financial/history_acquisition_total500_bulk_v1/pipeline-status.json
Get-Content data/financial/history_acquisition_total500_bulk_v1/worker.log -Tail 20 -Wait
```

## 29. Audit500 va batch300 tiep theo (21/10/2026)

Owner yêu cầu thực thi audit rồi mở thêm300 mã. [Batch300 terminal](../../data/financial/history_acquisition_total500_bulk_v1/results/6e589b691743f992143f/summary.json):66.000tasks=27.460ACQUIRED+4FAILED_OR_STOPPED+300IMPORTED_SOURCE_BOUNDARY+38.236after-series-stop;3.032.755cells/0parsererrors. Tổng500 provider partitions đã chạy acquisition, không phải500 lịch sử đầy đủ/đã xác minh. Maincoverage39.108present/19.392missing; auxiliary177present/123missing. Source/budget latchfalse.

Journal chứng minh4failed requests là GTX CDKT page1, TN/NV, NAM/QUY:HTTP500 sau2attempts. Không retry/reset cap; giữ quarantine và missing downstream. Gate acquisition cho các mã disjoint chấp nhận riêng4failures này khi exact classification, attempts, sourcejournal và report được pin; mọi lỗi khác hoặc access-control/budget latch vẫn HOLD. Đây không phải acceptance số liệu hoặc bỏ kiểm integrity.

[Audit config](../../configs/data/financial_acquisition_total500_audit_v1.json) chạy streaming replay/rawhash/candidate exactbytes/task accounting; output `data/financial/history_acquisition_total500_audit_v1/`. Sau PASS, controller lưu report tại `artifacts/reports/financial-acquisition-total500-v1/`:review-items.jsonl,failed-requests.json,report.md. Kỳ thiếu không được suy thành doanh nghiệp không công bố. Semantic arithmetic/annual–Q4/template/PDF review tiếp tục deferred theo owner.

[Assignment300 mới](../../configs/data/financial_acquisition_total800_assignment_v1.json) loại toàn bộ500 mã cũ:97HOSE/87HNX/116UPCoM. Stable registry order, exact legacy ID/current ticker uniqueness; historical identity vẫn provisional. Không dùng registry ticker list làm final historical research universe.

[Fresh-wave runner](../../scripts/financial_acquisition_waves.py) dùng shared frozen bulk collector/streaming transport/aggregated snapshot và indexed cache. Taskplan chỉ chứa140REPORTtasks/mã=42.000API task slots; bỏ80 catalogue placeholders/mã vì host này đã bị latch, không mở catalogue network hoặc thay source boundary. Tests so exact REPORT taskdicts với runner cũ. Không đổi candidate parsing, pagination, source/acceptance policy. Không chạm frozen code/config/receipts của batch trước.

[Controller](../../data/financial/history_acquisition_total800_v1/continue-after-audit.ps1):chờ đúng auditPID13060 → persist review và engineering gate → offlineplan/verify → network42000 tối đa. ControllerPID20968; không auto restart hoặc nối batch khác. [Status](../../data/financial/history_acquisition_total800_v1/pipeline-status.json), log `data/financial/history_acquisition_total800_v1/worker.log` khi network đã mở. `WAITING_FOR_ACQUISITION_AUDIT` chưa phải đang crawl API.

Counters parent46.724logical/46.728attempts/636.937.280bytes/20PDFattempts. New caps88.724logical/130.728attempts/2.636.937.280bytes;0,4s spacing/one network worker,attempt≤2/20s timeout/5MB response. Originalcreated_at1792414507.836684,deadline22/10/2026 12:55:07.836684UTC và90dcampaign không reset. Gate kiểm diskfloor30GB/artifactcap50GB (có dự phòng6GB) và cost projection trước mở network; expired deadline hoặc không đủ projected budget thìHOLD. 401/403/429/challenge vẫn hard-stop. Không PDF/OCR, numeric/PIT/M3 promotion hoặc shutdown.

29targetedtests/compileall/synthetic `run-20261021T142718Z-d33ff674` PASS; PowerShell parse/dry-run PASS. Các tests giữ disjoint membership, exact API task compatibility, unchanged0,4s/oneworker/2attempt/20PDF/72h policy, streaming reservation resume và byte-equivalent snapshot. Full repository gate còn known frozen M2-PREP hash mismatch, không waive. BaselineFY2025 vẫn29/30; VNM F chưa đủ input.

```powershell
Get-Content data/financial/history_acquisition_total800_v1/pipeline-status.json
# Sau stage RUNNING_CANDIDATE_ACQUISITION_RATE04
Get-Content data/financial/history_acquisition_total800_v1/worker.log -Tail 20 -Wait
```

## 30. Overnight toan bo registry (21/10/2026)

Owner ủy quyền khi xong thì tự chạy batch tiếp và mở rộng toàn bộ mã, treo máy qua đêm. Scope là đúng1.522 current registry provider candidates, không claim historical universe hoặc đủ lịch sử/financial/PIT. Sau batch hướng tới total800 còn722 mã, chạy tuần tự300+300+122 (total1100/1400/1522), không duplicate registry_id/ticker và không chạy nhiều network workers.

[Campaign config](../../configs/data/financial_acquisition_overnight_v1.json) pin registry/initial assignment và ba assignment:
[total1100](../../configs/data/financial_acquisition_total1100_assignment_v1.json),
[total1400](../../configs/data/financial_acquisition_total1400_assignment_v1.json),
[total1522](../../configs/data/financial_acquisition_total1522_assignment_v1.json).
Coverage test chứng minh union chính xác1.522 registry IDs. Có421 trong722 mã chưa có legacy_security_id, ghi UNKNOWN inventory, không gọi NOT_CRAWLED; giữ provider_partition provisional và exact current ticker/exchange/registry join. Indexed exact-URL cache inventory trước network giúp tái dùng nguồn đã có; không tự phong canonical/historical issuer/security IDs.

[Python orchestration](../../scripts/financial_acquisition_overnight.py) và [PowerShell controller — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_acquisition_overnight_v1/run-after-total800.ps1),PID25696. Chờ đúng parentcontrollerPID20968 hoàn tất total800 → audit exact raw/shard/receipt/coverage → lưu review queue và engineering gate → offlineplan/verify → chạy nextwave. Audit finalwave trước kết thúc registry task accounting. Mỗi wave có root `data/financial/history_acquisition_total{1100,1400,1522}_v1`; không sửa code/config/evidence cũ. Trạng thái REVIEW/FAILED của parent dừng chuỗi, không tự retry/reset các request thất bại.

[Global status — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_acquisition_overnight_v1/pipeline-status.json), global worker log `data/financial/history_acquisition_overnight_v1/worker.log` chỉ xuất hiện khi Python campaign được mở; stderr/controller logs cùng thư mục. Status hiệnWAITING_FOR_TOTAL800, không claim722 mã đang gọiAPI. Mỗi wave ghi riêng pipeline-status/terminal-summary/results, audit parent, report field/kỳ thiếu ở artifacts/reports theo batch_id; final audit result được pin riêng.

Giữ0,4s minimumspacing/one networkworker/2attempts/timeout20s/response5MB/20PDFattempts; cap mỗi wave kế thừa cumulative counters rồi cộng140logical+280attempts mỗi mã và2GB data budget; không resetcreated_at hoặc counters. Originaldeadline22/10/2026 12:55:07.836684UTC và90dcampaign giữ nguyên. Gate kiểm projectedtime/diskfloor30GB/artifactcap50GB (dự phòng6GB) trước từng wave; expired/insufficient budget HOLD, không nới deadline hoặc bypass401/403/429/challenge. Có checkpoint nhưng unreceipted attempted request vẫn cần review trước resume. Không PDF/OCR hoặc numeric/PIT/M3 promotion.

Controller giữ ES_SYSTEM_REQUIRED bằng SetThreadExecutionState chỉ trong phiên, không đổi power plan vĩnh viễn, không buộc màn hình sáng; finally trả trạng thái cũ khi xong/lỗi. Không shutdown. User cần cắm điện, mạng ổn định, giữ nắp laptop mở; sleep/hibernation/shutdown thủ công vẫn có thể ngắt tiến trình. Không cam kết xong toàn bộ trong đêm.

34targetedtests/compileall/synthetic `run-20261021T144219Z-5c81b104`PASS; thêm exact-registry schedule test PASS (722=300+300+122,421unknownlegacy, no duplicates). PowerShell parse/dry-run PASS. Tests bảo vệ deadline/source/budget latches, failed-parent hold và exact previous-membership chain. Full repo frozen M2-PREP mismatch vẫn giữ, không waive. Baseline29/30 và VNM F thiếu input không thay đổi.

```powershell
Get-Content data/financial/history_acquisition_overnight_v1/pipeline-status.json
# Khi campaign đã mở sau total800:
Get-Content data/financial/history_acquisition_overnight_v1/worker.log -Tail 20 -Wait
```

## 31. Audit800 va resume722 (22/10/2026)

Batch800 kết thúc01:15UTC+7 nhưng overnightv1 dừng trước722 mã vì4failed requests. [Source summary](../../data/financial/history_acquisition_total800_v1/results/6295a219e1dbe8c3660f/summary.json):42.000tasks=28.200ACQUIRED+4FAILED_OR_STOPPED+13.796after-series-stop;3.138.736cells/0parsererrors. Counters74.928logical/74.936attempts/891.766.375bytes/20PDFattempts; boundary/budget_stopfalse. OriginalpipelinePARTIAL giữ nguyên, không sửa receipts/summary để giảPASS. Tổng800/1.522=52,6% đã qua acquisition, không phải đủ history/verified metrics.

Owner yêu cầu audit xong mở lại toàn bộ mã còn lại. [Audit800 config](../../configs/data/financial_acquisition_total800_audit_v1.json), output `data/financial/history_acquisition_total800_audit_v1/`; đang replay28.200rawresponses/candidatebytes/hash/coverage. [DTR proof — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_acquisition_overnight_v2/preflight/dtr-failed-request-proof.json) xác nhận4CDKT page1 NAM/QUY TN/NV,terminalHTTP500 sau2attempts và receipt reason bounded transport attempts exhausted. Không retry/reset/repair/accept.

[Recovery configv2](../../configs/data/financial_acquisition_overnight_v2.json), [Python](../../scripts/financial_acquisition_overnight_v2.py), [PowerShell — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_acquisition_overnight_v2/run-after-audit.ps1),controllerPID23772. Chờ đúng auditPID17720 → provefailedreceipts/journal → audit producer pin đúng source800 → persist parentreviewqueue/deferred-failed-requests.json → engineeringgate → offlineplan/verify → network300+300+122. Giữ ba assignment và toàn bộ722 mã đã pin ởexecution30; dùng roots `history_acquisition_total1100_v2`, `total1400_v2`, `total1522_v2` để không sửa evidence cũ. Overnightv1 status trỏ MIGRATED_TO_RECOVERY_V2; source status đã lưu riêng.

Policy mới chỉ cho deferred failure khi sourcejournal/receipt hash khớp,exactrequestidentity,kindstructured,terminalHTTP500,attempts=2,receiptFAILED_OR_STOPPED/no record/reason đúng. Lỗi401/403/429,HTTPkhác,timeout,hash,parser,pending/latch/tornjournal/identity hoặc accounting lệch vẫn HOLD. Helper chứng minh số deferred bằng chính failedcount của snapshot; không dùng số đã hard-code để bỏ qua lỗi. Source/API failures được report riêng, không promote thành dữ liệuđủ; các mã disjoint tiếp tục sau integritygate theo owner acquisition-first. Wave có deferredHTTP500 dùng status COMPLETE_WITH_DEFERRED_HTTP500; các status này không phải numerical completion.

Counterinheritance/created_at/deadline22/10/2026 12:55:07.836684UTC/90dcampaign không reset;0,4s/oneworker/attempt≤2/20s/5MB/20PDFattempts/diskfloor30GB/artifactcap50GB giữ nguyên. Costprojection trước mỗiwave có thểHOLD nếu thời gian còn lại không đủ, không bảo đảm722 mã hoàn tất trướcdeadline. Không bypass sourceboundary/PDF/OCR/numeric/PIT/M3. Giữ máy thức trong phiên, khôngshutdown/đổi powerplan vĩnh viễn.

22targetedtests/compileall/synthetic `run-20261022T021703Z-7df6ae0f`PASS. Tests rejectHTTP401/403/404/429/502,attempt0/1/3,changedURL/key/snapshot,unexpectedrecord/reason,failedcount/latch/deadline violations. Realproof đối chiếu đủ4DTRrequestsPASS; PowerShell parse/dryrunPASS. Fullrepo frozen M2-PREP mismatch giữ nguyên. BaselineFY2025 vẫn29/30, VNM F chưa đủ input.

```powershell
Get-Content data/financial/history_acquisition_overnight_v2/pipeline-status.json
# Khi recovery đã gọi Python campaign:
Get-Content data/financial/history_acquisition_overnight_v2/worker.log -Tail 20 -Wait
```

## 32. Inventory1522 va QA offline (22/10/2026)

Giám sát bằng [dashboard localhost](http://127.0.0.1:8765/monitor/), [PowerShell server](../../scripts/financial_workflow_monitor.ps1). Tự refresh5giây; tách phần trăm acquisition/QA và baselineFY2025, log/checkpoints, cảnh báo sourcefile/lỗi/stale. Download report khi đã có resultseal. Monitor reuse productHTTPedge; read-only, không thay đổi collector/QA hoặc tự chạy stage mới. 9targetedtests/compileall/nodecheckPASS; visual kiểm tra progress1390/1522=91,3% và latestsymbol hiển thị đúng source. ServerPID21492; đóng tab không dừng QA.

Acquisition đã hoàn tất1.522 currentregistry candidates; finalaudit PASS11:10UTC22/10. Owner yêu cầu hợp nhất inventory và QA trước bổ sung PDF. [Config](../../configs/data/financial_inventory1522_qa_v1.json), [Python](../../scripts/financial_inventory_qa.py), [status — archive](../../artifacts/archives/financial-history-20261023/data/financial/history_inventory1522_qa_v1/pipeline-status.json), log `data/financial/history_inventory1522_qa_v1/worker.log`.

Chọn đúng10cohort không trùng:pilot5 +15 +30 +50 +100 +300 +300 +300 +300 +122=1.522. Dùng terminal snapshots, không cộng lại total200partial/total300partial hoặc overnightv1 status. Config pin manifest/contract của từngsource; coverage union phải khớp registry và196distinct slots/mã (2013–2025 annual/quarterly3statements+aux2012CDKT)=298.312slots. Source metadata tổng14.224.659candidatecells, số này phải được replayaccounting xác nhận trướcchốt.

QA đọc per-symbol, eight local I/O threads, không network. Verifyreceipt/rawhash/taskassignment, parse raw bằng frozen candidateparser và so hash canonical candidate với sealed shard đối với9moderncohorts. Pilot5legacy được reparse thành diagnostic structure mới, không sửa raw/candidates/baseline cũ. Các output per-symbol có sourcepins/manifest; resume checkpoint đã seal xác minh sourcehash/outputhash trước reuse, unsealed/tampered checkpoint HOLD. Không giữ14triệucells trong RAM.

Tái dùng exact KQKD template-family classification và frozen diagnose. Unknown/Bank/Securities không áp aliases/công thứcRegular; chưa có sector/historicalidentity acceptance. Accounting và annual–Q4 chỉ rawdiagnostics trongproviderpartition, chưa xác nhận units/scope/vintage; displacement chỉ nghi vấn, khôngrepair. Quarter/LUYKE không suy standalone/YTD hoặcTTM. Source units/publication/share/price/marketcap đầu vào chưa được acceptance bởi stage này.

Output job có symbols.csv/coverage.csv/missing-periods.csv/document-priority-queue.csv/summary.json/symbol-manifests.json. Mỗi mã cófield-presence.csv (táchmode/period/provider_type, giữmulti-values),failedrequests,unresolved/orphans/invalid/conflicts/arithmetic-findings/annual-q4-findings/displacements/schema_changes/document_queue. Alias inventory không phải fullcatalogue của mọiEPS/F/M/Zinput; alias không xuất hiện không chứng minh raw/PDF thiếufield. Coverage nhóm có số không chứng minh đủfield/continuoushistory; missing không chứng minh khôngcôngbố. Auxiliary2012 khôngđếm vàomainrange.

Report cuối dự kiến `artifacts/reports/financial-inventory1522-qa-v1/report.md`, link tới result seal. Priority1 gồm displacement/conflicts/invalid/nonzero orphan; bước sau reviewcache vàPDFtext/OCRtrang chọn lọc, không tảiPDF hàng loạt. Numerical/PIT/M3 deliveryPARTIAL, acceptedfacts mới0; FY2025baseline29/30/VNM F thiếuinput giữ nguyên. Mã/ticker vẫn provisional, chưa historical research universe; registry gốc khôngbị sửa để diễn giải làđủdữliệu.

19targetedtests/compileall/synthetic `run-20261022T113153Z-bfacace9`PASS; testcohortunion,196distinctcoveragegrid,providerpartition/multi-values,receipt/raw/shardtamper,checkpoint/sourcechange vàBank/Unknown noRegularmapping. WorkerPID5732 (offline), có wait-helper giữmáythức trongphiên, khôngđổipowerplan/shutdown. Fullrepo frozenM2-PREP hash mismatch vẫnknown, khôngwaive. Chỉ chốt PASS_INVENTORY_QA_DIAGNOSTICS sau replayaccounting toàn1.522 mã và reportseal.

```powershell
Get-Content data/financial/history_inventory1522_qa_v1/pipeline-status.json
Get-Content data/financial/history_inventory1522_qa_v1/worker.log -Tail 20 -Wait
```

## 33. Compute-first1522 offline (22/10/2026)

Đã hoàn tất acquisition và QA diagnostic cho 1.522 mã; compute-first offline tái tính 85 dòng reference từ input reviewed. Có 11 mã có ít nhất một family, 5 mã đủ 6 family cùng năm/scope/vintage (ACV, BRC, FPT, GMD, MWG); chưa mã nào đủ bộ 10 năm 2016–2025. Không tải PDF/OCR mới hoặc tự nâng API candidate thành dữ liệu đã xác minh. VNM F vẫn thiếu input; PIT/M3 chưa mở.

Owner yêu cầu ưu tiên tính từ input đủ evidence, báo các mã/field thiếu trước khi lập kế hoạch bổ sung PDF. Stage này chỉ đánh giá/tái tính offline; không mở document acquisition. [Config v2](../../configs/data/financial_compute_first1522_v2.json), [runner](../../scripts/financial_compute_first_v2.py), [report kết quả và quá trình — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-compute-first1522-v2/report.md). Report trỏ tới summary, 1.522 symbol readiness rows, 118.716 annual symbol–year–family tasks, numeric values/provenance, grouped blockers và reviewed missing inputs.

Giữ baseline29/30 và các công thức/variant đã chốt. Tái chạy pilot5, reviewed history, ACV/GAS, scale cache PHP/VCS/VEA/PAN và FPT flow; patch network transport fail-closed. Mọi source replay thành công. V1 được giữ nguyên; V2 bổ sung explicit cohort scope cho ACV để không bỏ sót cohort đủ6, giá trị của cả85 dòng không đổi qua so sánh toàn bộ numeric rows. Scope/vintage/year khác nhau không gộp thành bộ6. P/E annual reference không phải TTM hiện tại; 67 khoá annual symbol–year–family khác nhau không được cộng thành67 mã.

1.511 mã chưa có numeric reference trong evidence reviewed hiện tại, không đồng nghĩa không có raw hoặc tất cả cần PDF. QA alias catalogue chưa bao phủ toàn bộ calculator inputs; phân biệt unmapped, not-observed, conflicting và quality clearance. Không zero-impute, tự sửa row, suy weighted shares/debt current portion, hoặc apply F/M/Z cho Bank/Securities/unknown template. Chưa đánh giá/accept toàn bộ API fields nên đây là PASS cho offline assessment, PARTIAL cho mục tiêu lịch sử đầy đủ/PIT/M3.

43 targeted tests PASS; compileall PASS; synthetic `run-20261022T125118Z-370d8310` PASS. Kiểm manifest/output hash, 1.522 mã unique, 118.716 task rows và numeric parity V1/V2 PASS. Known full-repository frozen M2-PREP hash mismatch giữ nguyên, không waive. Không sửa registry/source/raw hoặc artifacts đã seal.

```powershell
Get-Content data/financial/history_compute_first1522_v2/pipeline-status.json
Get-Content artifacts/reports/financial-compute-first1522-v2/report.md
# Chỉ replay offline; không tải PDF:
python scripts/financial_compute_first_v2.py --config configs/data/financial_compute_first1522_v2.json
```

## 34. Expanded API input review1522 (22/10/2026)

Owner yêu cầu mở rộng mapping, kiểm chứng API/cache rồi tính phần đủ điều kiện; báo input thiếu trước khi bàn PDF. Stage này chỉ đọc dữ liệu local, không network/PDF/OCR, không thay score definitions/acceptance/PIT/identity hoặc artifacts cũ. Annual raw 2012–2025 hỗ trợ task annual2013–2025, ưu tiên coverage market2016–2025; quarterly/TTM chưa được xử lý mới trong stage này.

[Config](../../configs/data/financial_api_input_review1522_v1.json), [runner Python](../../scripts/financial_api_input_review.py), [PowerShell](../../scripts/financial_api_input_review.ps1). [Tiến độ — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-api-input-review1522-v1/progress.md); report cuối `artifacts/reports/financial-api-input-review1522-v1/report.md` chỉ có khi đã consolidate/seal. Dashboard cũ vẫn thể hiện acquisition/QA, chưa thể hiện worker stage34; đọc status/log bên dưới để theo dõi đúng lượt này.

Mapping exact code+label bổ sung receivables/PPE, finance income/expense, bridges PBT/tax/attribution, auxiliary capital/NCI/cash/depreciation. Không dùng aggregate D&A hoặc accumulated depreciation thay depreciation flow, vốn góp thay shares, cash group proceeds thay parent issuance, long-term loans thay debt including current portion. Template Bank/Securities/UNKNOWN không reuse Regular mapping/model.

Replay qua frozen parser; source/receipt/hash pin chain, tách provider_type, không chọn latest/equal values thành vintage proof. Missing/ambiguous/invalid/conflicting observations giữ unresolved. 11 accounting checks, giữ annual displacement và anomalous comparators, không tự thay annual bằng Q4 hoặc shift row. Conditional EMZ arithmetic chỉ khi inputs đầy đủ/unique, core accounting checks đủ và equality, không có difference/displacement; input unit/scope/vintage/EBIT vẫn là giả thuyết chưa accept. F chỉ lưu individual signal arithmetic, không partial total hoặc bound. EPS vendor không được chép thành recomputed EPS; P/E/P/B không lấy current shares/adjusted price để điền.

Mỗi mã có checkpoint manifest, field-inputs CSV/JSON, required inputs theo năm/family, accounting, diagnostics, source pins và label catalogue. Source/code/config thay đổi hoặc checkpoint unsealed/tampered thì HOLD, không xóa hoặc tái dùng im lặng. 4 threads chỉ đọc local, không tăng request concurrency. Tổng hợp CSV streaming để tránh giữ toàn bộ matrix trong RAM.

Verified reference stage33 vẫn85 rows/11 mã/5 full6 cohorts/0 full10y; API arithmetic không cộng vào những số này. Financial historical delivery PARTIAL tới khi có evidence acceptance. Không có numeric feature/PIT/M3 promotion. Thiếu alias không chứng minh không công bố hoặc phải tải PDF. Phải báo owner từng nhóm thiếu trước khi lập bổ sung PDF plan.

38 targeted tests PASS; compileall PASS; synthetic `run-20261022T130625Z-6b714315` PASS; PowerShell parser PASS. Tests chống dangerous aliases/provider mixing/missing→zero, giữ diagnostic gates false, reject anomaly/institution và source/checkpoint tampering. Known full-repository frozen M2-PREP hash mismatch giữ nguyên, không waive. Helper chỉ đợi worker rồi verify sealed outputs/manifest/counts/links và cập nhật report/active pointers; không mở stage hoặc download mới.

```powershell
Get-Content data/financial/history_api_input_review1522_v1/pipeline-status.json
Get-Content data/financial/history_api_input_review1522_v1/worker.log -Tail 20 -Wait
# Chạy lại đúng checkpoint, không chạy trùng worker đang hoạt động:
powershell -ExecutionPolicy Bypass -File scripts/financial_api_input_review.ps1
```

<!-- API_INPUT_REVIEW34_RESULT -->

Kết quả cuối: Đã hoàn tất review raw annual cho 1.522 mã / 118.716 tasks; mapping 23→50 fields. Có 7,169 dòng Z có điều kiện cho 1411 mã, chỉ là arithmetic diagnostics, chưa được chấp nhận thành reference. Giữ 11 mã có reference reviewed / 5 mã đủ6 tại một cohort / 0 mã đủ bộ2016–2025. Không PDF/OCR mới; financial/PIT/M3 vẫn PARTIAL.

Output hash/manifest, 1.522 mã unique, 118.716 tasks, no-acceptance/no-PDF guards và report links đã kiểm PASS. Xem `artifacts/reports/financial-api-input-review1522-v1/verification.json`.

## 35. Cached fact verification (22/10/2026)

Đã xác minh557 fact/vintage observations/11 mã:334 khớp,63 khác giá trị hoặc vintage,160 chưa có direct alias. 9 Z reference tái lập khớp giá trị cũ; bổ sung2 kỳ Z reference BRC2024/VNM2024. Có18 đối chiếu CF interest khớp PDF trong khi KQKD gắn nhãn sai khác; chưa sửa mapping chung. Không PDF/OCR mới; full10y/PIT/M3 vẫn PARTIAL.

Owner yêu cầu xác minh API/cache, đánh giá việc tái dùng format từ pilot. [Handoff và2 reference periods mới — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cached-fact-reconciliation-v1/handoff.md), [đối chiếu field — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cached-fact-verification-v1/report.md), [cross-statement — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cached-fact-reconciliation-v1/report.md). Configs `financial_cached_fact_verification_v1.json` và `financial_cached_fact_reconciliation_v1.json`; runners cùng tên trong scripts/.

Pin stage33/34 manifests và transitive source/API/PDF/images. Phạm vi11 mã có reviewed anchors, không phải xác minh toàn1.522 mã hoặc chấp nhận những năm chưa có evidence. Exact value match không xác minh API report vintage/scope/publication. Unit spelling của reviewed packages (`VND_PER_SHARE`, `shares`) được chuẩn hóa tên, không đổi số/hệ số; không infer API units. Nonannual/missing provenance loại riêng.

CF interest bổ sung chỉ cho observation khớp exact reviewed interest cùng PDF/năm/scope; finance-expense value equality chỉ dùng làm evidence alignment, không alias/repair toàn bộ. 11 Z replay rows gồm9 old-value matches+2 new keys; summary false do no-old-value được giải thích trong verification.json. BRC2024 là comparative từ FY2025vintage, không áp ngược PIT. Numeric reference bổ sung không đổi baseline29/30/VNM F hoặc mở acceptance/research.

20 targeted tests PASS; compileall/synthetic `run-20261022T140341Z-fa6aba5b` PASS; source/output hashes, reportlinks,9 Decimal old-value parity PASS. Existing facts/config/artifacts giữ nguyên. Fullrepo frozen M2-PREP mismatch không waive. Không bước PDF/network mới hoặc mở stage mapping repair; muốn generalize cần review exact versioned mapping với controls, không suy từ5 mã.

## 36. Template contract và reference handoff (22/10/2026)

Mapping được trực quan verify24 controls ACV/VNM/GAS, calibration ACV/independent validation VNM+GAS, current2025/comparative2024. Code21 finance income/22 finance expense/23 interest/24 associate; exact template staging, không sửa raw hoặc canonical. Control review-v1 có một digit GAS finance expense đọc nhầm; preflight HOLD trước execute, reread original PNG tạoreview-v2/supersedes, oldfile giữ nguyên.24/24 controls PASS.1.427/1.522 mã exact-template,15.135 partitions,9.339 financebridge equalities,7.796 conditionalZ rows. Conditional không đếm vào verified/PIT.

Bundle87 reference rows/11 mã/5 full6 cohorts giữ riêng. [Report — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-template-contract-v1/report.md), config `financial_template_contract_v1.json`, runner `financial_template_contract.py`. Numerical data/model gates khác nhau; source-template fingerprint không chứng nhận mọi giá trị của1.427 mã.

## 37. Owner-approved financial exploratory baseline (22/10/2026)

Owner duyệt core-ratio financial baseline độc lập. Đã fit static K-Means2016–2025 trên6.976 rows/1.311 registry candidates (51 có đủ10 kỳ reference); FY2025 zscore982/1/1, rank sensitivity395/361/228 cùng984 mã, chưa chọn final model. Reference6families87 rows/11 mã/5 full6 cohorts giữ riêng. Financial/PIT/M3 cuối vẫn PARTIAL; market handoff chờ teammate, không PDF/OCR mới.

Owner trả lời chọn “Chạy baseline thăm dò bằng tỷ số cơ bản (margin, leverage, liquidity, cash flow, turnover); hoàn thiện EPS/P/E/P/B/F/M/Z song song”. Đồng thời xác nhận market đang ở máy teammate, chưa có artifacts. Đây là explicit authorization cho exploratory core financial-only, không phải approval final PIT/M3 hoặc six-family production feature protocol. Không đổi market/model protocol hoặc artifacts bên kia.

[Handoff kết quả — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-exploratory-core-v1/handoff.md), [baseline — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-exploratory-core-v1/report.md), [rank sensitivity — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-exploratory-scale-compare-v1/report.md). Executable exploratory config `configs/experiments/financial_exploratory_core_v1.json`, sensitivity config cùngfolder; strict6 draft `financial_only_protocol_draft_v1.json` vẫn not executable.

Six core features: gross/net margin, liabilities/endingTA,current ratio,CFO/endingTA,revenue/endingTA. Registry exploratory riêng có eligibility đúng scope, không sửa production FEATURE_REGISTRY hoặc promote unreviewed references. Annual reference period không phải investable date; publication null, identity là current registry candidate. Exclude duplicate providerpartitions, missing/nonpositive denominator, accounting/finance bridge/displacement và nonregular/unknown; no imputation. Signed negative profit/CFO vẫn giữ. Zscore/no winsor/PCA baseline cùngk3/seed42/ninit20/maxiter300, minimum30 observations; yearly crosssection scaler, không future-year fit hoặc portfolio outcomes. Static yearly snapshots không gọi Dynamic Clustering.

FY2025 singleton concern được giữ nguyên và versioned rank sensitivity cùng984 mã/k/seed, không thêm/bớt/loại outlier. Rank geometry khác, không tự select bằng silhouette acrossspaces.26 tiny-cluster observations có source refs để review. No final model selection, no portfolio/backtest.

30 targeted/compileall/synthetic `run-20261022T143614Z-4cfce490` PASS. Output/source manifests,6.976 unique registry-year keys,assignments/snapshot counts,scaler/convergence,actual ratio/source arithmetic,984 rank identicalsample PASS. GateM3 false; 11 reference issuers không tăng giả thành1.311 verified issuers. Fullrepo frozen M2-PREP mismatch giữ nguyên. Không network/PDF/OCR hoặc reset campaign budgets. Goal final financial indicators/M2/M3 vẫn PARTIAL.

```powershell
Get-Content "C:/Projects/Intern/SourceCode-CafeF/data/financial/history_exploratory_core_v1/pipeline-status.json"
Get-Content "C:/Projects/Intern/SourceCode-CafeF/artifacts/reports/financial-exploratory-core-v1/verification.json"
```

## 38. Coverage diagnosis: exact-zero QA residual (22/10/2026)

Owner hỏi vì sao51 mã đủ10 kỳ. [Diagnostic report — archive](../../artifacts/archives/project-cleanup-20261023/historical-reports-and-scratch.zip). Offline replay tái lập chính xác6.976 baseline issuer-period keys trước counterfactual. Có1.013 candidates đủ3 nhóm annual2016–2025, trong đó949Regular; chưa chứng minh đủfields/PIT.4.147 finance-bridge differences trong2016–2021,4.137 chỉ lệch1rawunit. Exact-zero gate đang gộp numeric precision residual với sai lệch nội dung.

Giữ missing/denominator/displacement/provider/source gates và khôngfill; sensitivity tolerance1rawunit cho11.618 feature rows/1.419 candidates/505 full10; tolerance2 cho11.779/1.420/550. Đây là what-if, chưa áp policy hoặc recompute model. Raw unit ngoài controls chưa được individual acceptance, không tự gọi tất cả làVND. Không mặc định coi chênh nhỏ làđúng hoặc nới1% để tăngcoverage. Tolerance/precision/materiality policy cần versioned review; actualbaseline vẫn51. Publication/vintage/identity/M3 gates giữ nguyên. Không network/PDF. Chỉ chạy offline analysis và assertion key-parity, không pipeline change nên không rerun model/tests toànrepo.

## 39. Precision QA reference và document triage (22/10/2026)

Owner yêu cầu triển khai remedies, đo số mã phục hồi, report PDF cần bổ sung và không tự tải. [Report đầy đủ — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-precision-review-v1/report.md), [verification — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-precision-review-v1/verification.json).

Đã execute precision QA offline: 11.178 core-ratio reference rows/1.416 candidates; 427 mã đủ10 kỳ2016–2025 (tăng376 từ51). Còn3.112 annual gap cases, chưa phải3.112PDF phải tải; inventory211files/202hashes,7cases cócache filename hints. Không network/PDF/OCR hoặc rerun model. Original6families/PIT/M2/M3 vẫn PARTIAL.

Policy/config version1 `configs/experiments/financial_precision_review_v1.json`, runner `scripts/financial_precision_review.py`: residual≤1rawunit VÀ≤1e-9×max(abs(terms)); exact-zero riêng. Tái lập6.976baseline keys và6ratios cũ không đổi trước khi tạo result mới `data/financial/history_precision_review_v1/results/6ef2c083a4ffc2a9b51c`. Phục hồi4.202rows; relative cap giữ440rows khỏi absolute-only sensitivity. Không sửa raw/facts/canonical, không nguồnưu tiên, khôngfill/missing0, không nới displacement/multiple-provider/sector/denominator gates. Unit/scope/vintage vẫn source hypothesis ngoàicontrols; không đổi rawunit thànhVND. Promotion PIT/research vẫn MANUAL_REVIEW_REQUIRED khi có proposal riêng.

360mã có9/10 kỳ (360gaps),188mã có8/10 (376gaps); queue ưu tiên548mã/736gaps.3.112gaps toànRegular2016–2025 là candidate annual review slots, không sốPDF tải đã xác nhận.7cases cófilename hints cache và3.105chưa cóhint, chưa chứng minhcacheabsence. SốPDF mới bắt buộc cònnull, cầncache/API/identity/catalogue/scope/vintage triage trước; current-doccount khôngbao trùm warmup/quarterly hoặc six-family/PIT. Không lập/acquire bổ sungPDF trongstage này.

26targetedtests,compileall,synthetic `run-20261022T154143Z-e30b90fc`, source/output hashes/counts/key/value parity PASS. LỗiTEMP ngoàiworkspace khi test đầu được sửa bằng TEMP/TMP trongworkspace; rerunPASS. FrozenfullrepoM2-PREP mismatch cũ giữ nguyên, không waive. StagePASS; finalgoalPARTIAL. Modelbaseline cũ6.976rows giữ nguyên, chưafit datasetprecisionmới. Bước tiếp theo: reviewqueue360gaps gầnđủ bằngcache/API/identity, chốt thật documentrequirements để báoowner trướcphầnPDF.

## 40. Direct CFO recovery và coverage trên1.000 mã (22/10/2026)

Owner yêu cầu tiếp tục kiểm tra khả năng đạt hơn1.000mã sửdụng được; giữ noPDFdownload. [Report — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-direct-cashflow-review-v1/report.md), [verification — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-direct-cashflow-review-v1/verification.json).

Đã phục hồi657annual core-ratio rows từ mẫu CFO trực tiếp đã có trongAPIcache: 11.835rows/1.422candidates,459full10 (+32). Có1.365mã≥3kỳ liên tiếp,1.168mã≥5kỳ liên tiếp,1.098mã≥8/10kỳ; chưa phải cùng1.000mã đủ10năm/PIT. Backlog2.455cases, chưa chốt sốPDF cần tải.0network/PDF/OCR; original6families vàM2/M3 cuối PARTIAL.

Parser correction reference-only cho explicit `LCTT/HDKD/HDKD_9` directmethod, total-label chính xác và đủ7signedcomponents codes2–8. Require code+normalizedlabels/unique codes/validnumbers, annualNAMquarter0/issuer/receipt/rawhashchain. Extra nonzero/invalid hoặc component mismatch giữ. Reconcile dưới precisionpolicy cũ1rawunit+1e-9relative, không nới gates hoặc suyunit. Không override CFO observation cũ, mixprovider, infer Q4annual, hoặc sửaraw/canonical/PIT. Các rows cũ11.178giữnguyên;657newvectors tínhlại từsourcePASS.

723cases/181mã được kiểm:657restored,25component-invalid,41cóCFO nhưngvẫnheldaccounting/displacement/core. Result `data/financial/history_direct_cashflow_review_v1/results/a6bf5b2593fa37fb2771`; config `configs/experiments/financial_direct_cashflow_review_v1.json`; offline runner `scripts/financial_direct_cashflow_review.py`.

Không gọi1.365mã3kỳ liên tiếp thànhfull10 hoặcresearch-ready. Cohorts3/5/8/10 và8-of10 xuất riêng để review, không tựfreeze model/observationrule.9năm2017–2025 có>1.000reference rows/năm;2016còn943.480Regularcandidates thiếu toànbộannualmappedfields ởít nhất1năm (1.158cases); conditionalmapped-input bound949full10trướcqualitygates. Muốn>1.000full10 cầnít nhất52candidates nữa đượcbackfill missingperiods, khôngđồngnghĩa52PDF.156cases có3Q4groups, chỉqueuexácminh interval/scope/vintage, chưaacceptannual.

33targetedtests/compileall/synthetic `run-20261022T155740Z-29ce2c9e` PASS; nguồn/outputhash/key/oldvalue/newvectorreplay PASS. Originalsix87reference rows/11issuers/5full6cohorts giữriêng; VNM F vẫnthiếu. Modelcũ khôngrerun. NoPDF/OCR/network/resetbudgets. StagePASS; goal>1.000full10/finalPIT/M2/M3 PARTIAL. Bước kế: cache/API/identity/annual-vs-Q4evidence đểchốt gapcases vàPDFrequirements thực; khôngtảiPDFtheo2455placeholdercases.

## 41. Review412 one-year gaps và report tổng (22/10/2026)

Owner yêu cầu tiếp tục nhóm gần đủ10kỳ và có một report tổng cập nhật liên tục. [Master report](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [report run](../../artifacts/reports/financial-near-full10-review-v1/report.md), [verification](../../artifacts/reports/financial-near-full10-review-v1/verification.json).

Đã review 412 mã thiếu một kỳ, bổ sung BRC/GAS/VNM từ single-document reviewed vectors: 11.838 core-ratio reference rows, 462 mã đủ 10 kỳ; còn 409 mã thiếu một kỳ và 2.452 annual gap cases. Không tải PDF/OCR/network mới; mục tiêu 1.000 full10 và final EPS/P/E/P/B/F/M/Z/PIT/M3 vẫn PARTIAL.

412 targets:223QA-held,125no-annual-partition,57multi-provider,42displacement,12missinginputs,5nonpositive denominator (reasons overlap). BRC/VNM có8reviewed core inputs trong từngPDF; GAS thêm1visually reviewed CFO fact từcached image physical12, annual2025/consolidated/VND, components reconcile exact. KhôngnewOCR/download. Vector gate yêu cầu cùngPDF/year/scope,8fields/VND/uniquevalues/corevalidity, khôngmixedvintage hoặcsourcepriority; nhiềucompletevintages giữheld. API partitions nghi vấn vẫnquarantine, newrows làDOCUMENT_REFERENCE_NOT_API_PARTITION, khôngrepair/nớiAPIQA/PIT.

Result `data/financial/history_near_full10_review_v1/results/c607f9e7f0a2b9185445`; config `configs/experiments/financial_near_full_review_v1.json`; runner `scripts/financial_near_full_review.py`. Giữ nguyên11.835oldrows; thêm3rows→462full10. Cần538mã nữa tới1.000, theo smallest-gap scenario409+129×2=667annualcases, chưa phảiPDFcount/guarantee.409targets chưa cócomplete reviewed vector không cónghĩaPDFcacheabsence.

39targetedtests/compileall/synthetic `run-20261022T162534Z-6cad5fdd`, source/output hashes/keycounts/oldrows/newratio arithmetic PASS. Originalsix87rows/11issuers/5full6cohorts vàVNM Fgap giữriêng; finalgoalPARTIAL. Khôngmodelrerun/market/counter/boundary changes. Khôngxóa/move files; cleanup cầndependency/hashrefs inventory trướcpublic. Các stage sau tiếp nguồn/identity/annual-vs-Q4/fieldQA vàupdate master report, chỉđềnghịPDFsaukhibáoowner đúngnhucầu.

## 42. Annual gap audit125 và issuer HTML reference (22–23/10/2026)

Audit125 annual input gaps đã chốt; thêm PLX2023 từ HTML chính chủ, 11.839 core-ratio reference rows/463full10. Còn408 mã9/10,124annualinputtargets và2.451annualcases; CTD2023 giữ fiscal-period review.0PDF/OCR mới; PIT/M3 vàgoal1.000full10 vẫn PARTIAL.

[Report tổng](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [stage report](../../artifacts/reports/financial-annual-gap-audit-v1/report.md). Frozen125 targets từ409nearfull10:58internal/38before-earliest/29after-latest;0numericNAMtargetheaders,41LUYKEyearcases,37Q4threegroups/29all-four-quarterthreegroups (overlap;notannualacceptance).3legacyHTMLcolumns chỉplaceholdernone;oldcatalogue267rowschưacómatch,khôngkếtluậnnonpublication.

Boundedexternalweblookup2primaryissuerHTML,3webtoolcalls separatelylogged, khôngPDFopen/download/OCR hoặcretrylatchedsource. PLX2023sourcecode/year/unit/value review32fields→unchanged11accounting+financechecksPASS→singleissuerHTMLreference;originalHTTPbytesunavailable,webextractsnapshotSHAonly. Sourcecaptionanomaliesngoàicorefields giữnguyênwarnings. CTDcataloguechínhchủnêu6monthtransition,heldkhôngannualizehoặclấp12monthgap.

Auditresult `data/financial/history_annual_gap_audit_v1/results/0c51f5b71e66a268c225`; datasetresult `data/financial/history_annual_gap_audit_v1/html-reference/c15c48e7682c0685c235`. Configs `financial_annual_gap_audit_v1.json`, `financial_issuer_html_reference_v1.json` trongconfigs/experiments; scriptnames tươngứng.11.838oldrowsgiữnguyên,1newPLXrow→463full10; còn4089-of10/2.451annualcases. Localreplay0networkkhôngđồngnghĩaexternalweb0requests;counts/bytesunknown bêntrongtoolkhôngghi0, sourceboundaries/counterskhôngreset.

24targetedtests/compile/synthetic `run-20261022T165830Z-f0dded10`,source/output hashes/oldvalues/newratio/coveragechecksPASS. Initialauditmissingcsvimport dừngtrướcseal,fix+integrationtest+offlinerereplayPASS;nonfatalResourceWarninglegacyiterator recorded khôngwaivefullrepoM2mismatch. CorecoveragePASS,finalgoalPARTIAL. PhầnPDFneedvẫnnulltrướckhichốtURL/scope/interval/cachestatus;khôngdownloadbygapcount. Stage sau ưu tiên58internal/29quartercomplete sourceverification vàremainingQAcohorts, update masterreport.

## 43. Quarterly evidence triage và đề nghị PDF chọn lọc — 23/10/2026

[Report tổng](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [stage report — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-quarter-gap-triage-v2/report.md), [PDF proposal — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-quarter-gap-triage-v2/pdf-review-proposal.md).124annual-input gaps còn lại gồm57internal/38before/29after. V2duyệt toàn bộ pinned quarterly receipts, khôngcap5pages nhưintermediatev1; source/task/hashcheck, same-provider4groups TN/NV/KQKD/HDKD. 36Q4cases/27four-quartercases, chưaannualconversionaccepted; explicitunits thiếu912/912headers. Khôngcộngcashflowcumulative hoặcghépvintagesđểlấpcộtannual.

11.839reference rows/463full10 khôngđổi,0recovered. PTB2018/PLC2025primarydocumentleads→đềnghịtốiđa2PDFtext-first,checkcachemetadata/deduptrước; ownerchưaduyệt,0PDFopen/download/OCR. Campaign/sourceboundaries/counters/deadlineskhôngreset.4webtoolcalls/9queries/5HTMLopenoperationsriêng,HTTPattempts/bytesunknown.16targetedtests/compile/synthetic `run-20261022T171752Z-c643253f` vàsource/output/unchangedbaselineverificationPASS;knownfullrepoM2-PREP mismatchkhôngwaive. StrictPIT/M3/finalgoalPARTIAL.

Offline: bundledPython `scripts/financial_quarter_gap_triage_v2.py --config configs/experiments/financial_quarter_gap_triage_v2.json`, sauđó `scripts/verify_financial_quarter_gap_triage.py`, PYTHONPATH=src. Result `data/financial/history_quarter_gap_triage_v2/results/a5aa53c01d691667964e`; [resultref — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-quarter-gap-triage-v2/result-ref.json). Intermediatev1giữnguyênkhôngdùnglàmcurrentcoverage. KhôngchạyPDFstagekhiapprovalchưacó.

## 44. Batch phục hồi nhiều mã — 23/10/2026

[Report tổng](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [stage report — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/report.md), [PDF proposal — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/pdf-batch100-proposal.md). Đã tạo queue635 candidates/862 annual dependencies (408 mã9/10,227 mã8/10). Chọn100 mã9/10 chỉ vướng một checkQA và xuất field-level review list. Không nới tolerance, bỏ check, shift rows hoặc chọn source priority ngầm. Dataset giữ11.839rows/463full10;0rows phục hồi ở stage chuẩn bị.

Đề nghị tối đa100 PDF chia hai batch≤50, pilot10 trước, chờ owner duyệt theo chỉ thị hỏi trước PDF. URLs/cache/boundary phải resolve trước download; queue chưa là download-ready manifest. Tuân cap/counters/deadlines gốc, text-first và OCR chọn trang trong cap chỉ sauapproval. Nếu không phục hồi được pilotcase nào thì báo lại trước mởrộng. Không tự mở635 mã. Đề nghị hai tài liệu Execution43 không tự được duyệt/cộngquota. Nếu mọi100targets qua gates thì tối đa563full10; nếu mọi408 mã9/10 đều qua thì871, còn129 mã8/10 để đạt1.000. Đây làbounds, không phải count mới.

Offline: bundledPython `scripts/financial_bulk_recovery_queue.py`, PYTHONPATH=src. [Resultref — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/result-ref.json), [100 mã/fields — archive](../../artifacts/archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/batch100-review.csv).4targeted tests/compile/hash/dependenciesPASS,0network/PDF/OCR,originalmodel/reference/PIT gates giữ nguyên. GoalPARTIAL.

## 45. ReusablePDFworkflow vàpilot10 — 23/10/2026

[Report tổng](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [stage report/runbook](../../artifacts/reports/financial-pdf-pipeline-v1/report.md). Ownerđãduyệtbatch100rồiyêucầuflowcóthểchạylạitrướcmởrộng. TriểnkhaiPowerShellentry `scripts/financial_pdf_workflow.ps1` với prepare/run/status/verify; source/cache/download/text/selectedOCR/reviewreceipt/referenceimport/status cósourcehash/checkpoint vàbudget/sourceboundaries. Counterparentacquisition1522 kếthừa131.928logicalrequests/131.961attempts/1.383.967.209bytes/20PDFattempts; giữcampaigncreated_at, batchPDFmới72giờtrongcampaign90ngày, khôngsửabatchAPIcũđãterminal/deadline.

Actualpilot10:7SOURCE_DISCOVERY_REQUIRED,2catalogueviewschưacóđúngannualdocument,1CNT2018reviewedreferencecomplete. Pipelinekhôngtựđổiissuer/year/sourcepriorityhoặccoi10terminalstateslà10restored. CNTprimaryPDF5.020.705bytes33trang, selectedOCRphysical7–10;31visualreviewedfields/8coreinputs;10availableaccountingchecksexact,2optionalcheckschưađủinputkhôngđiền0, CFOsignedcomponentbridgekhớp. Reuseexisting single-PDFvectorpolicy, khôngrepairAPIquarantine/waiveQA. **11.840rows/464full10(+1)**,11.839oldrowsgiữnguyên;407one-yeargaps/2.450annualcases. Stillreferenceonly,khôngđủ6families/PIT/M3.

Networkthêm4logicalrequests/4attempts/5.799.939bytes/1PDF; externalweb7calls18queriesghi riêng,HTTPtransportcounts/bytesunknown. OCR130→134pages/0errors, oldanchors/reservationspreserved. V2OCRcontrollerfixprepare/runimmutable-resultcollision vàreuseregisteredPDFsha/page;sourceV1/artifactsđãsealgiữ nguyên. ActualPowerShellrerun/verifykhôngtăngrequests/OCR. Statuschungđọcrevieweddatasetrefđểbáo464full10/1of10, khôngdùngacquisition-onlybaseline463cũ.

41targetedtests/compileall/synthetic `run-20261022T180844Z-f9c0dcd1` vàsource/hash/oldrow/independentratioverificationPASS. ChưafullsuitePASSvìknownM2-PREPfreezehashmismatchkhôngwaive. **PilotPARTIAL/next50=false**: adaptercataloguechưaphủ9targets, chọntrang/semanticreviewvẫncóthủcông, cachemetadata183/211filesunknown. Khôngtuyênbốproductionstablehoặcmở1.000mã. Bướctiếp:source/detail/paginationadapterscho9targetscònlại,giữapprovalscope/budgetvàreporttổng.

Lệnhstatus từmọithưmục: `& 'C:/Projects/Intern/SourceCode-CafeF/scripts/financial_pdf_workflow.ps1' -Action status`; đổiActionthànhrunđểreplaylocal, verifyđểkiểmhash/snapshots. Networkphảilàflagriêngvàkhôngvượtfrozenassignment. [Datasetref](../../artifacts/reports/financial-pdf-pipeline-v1/dataset-result-ref.json), [reviewreceipt](../../artifacts/reports/financial-pdf-pipeline-v1/cnt2018-reviewed-vector.json), [verification](../../artifacts/reports/financial-pdf-pipeline-v1/verification.json).


## 46. Execution — Cache provenance và bàn giao coverage (23/10/2026)

Đã chạy [offline recovery readiness](../../scripts/financial_recovery_readiness.ps1), config [v1](../../configs/data/financial_recovery_readiness_v1.json). Exact path/hash/URL resolver đối chiếu legacy inventory/results/receipts: 211/211 PDF files trong snapshot cũ có metadata, trước28/211. Không sửa sealed nguồn và không suy statement identity/PIT từ acquisition provenance.

[Report — archive](../../artifacts/archives/project-cleanup-20261023/historical-reports-and-scratch.zip) xuất cohort/feature CSV cho3/5/8/10kỳ liên tiếp:1.365/1.168/790/464 mã. 11.840reference rows giữ nguyên,0newfull10. Cache overlaps11annualcases trên10mã; ưu tiên4one-gap DCM/VEA/PAN/VHC sau page/year/scope/QA review. Pilot9targets vẫn cần discovery; không tự mở50.

[Dependency queue1.001 — archive](../../artifacts/archives/project-cleanup-20261023/historical-reports-and-scratch.zip):407one-gap +130two-gap =537candidates/667annualdependencies có điều kiện, không phải số PDF hoặc đảm bảo đạt. Chưa cấp quyền download toànqueue. Không chạy model hoặc đổi methodology.0localrequests/PDF/OCR; publicweb1call/4queries ghi riêng.14targeted tests/compile/synthetic/source/export verificationPASS, goalPARTIAL. Report tổng đã cập nhật.


## 47. Execution — Review bốn near-full candidates từ PDF cache (23/10/2026)

[Report](../../artifacts/reports/financial-cached-four-review-v1/report.md), [datasetref](../../artifacts/reports/financial-cached-four-review-v1/dataset-result-ref.json). DCM2025/VEA2025/PAN2024/VHC2024 đủ reviewed8coreinputs từ consolidatedPDFs,131fields/21selectedOCRpages;47exactaccounting/1missingDCMassociate,4CFOcomponentbridges exact. VEAqualifiedauditwarning giữ riêng, code400 gồm430; VHCexpense signs lưu cảraw/canonicalformula semantics. KhôngrepairAPI hoặc thayQA/PIT/identity.

11.840→11.844rows,464→468full10;old11.840rows unchanged/24ratios independentlyrecomputed. OCRcampaign134→155charged/successfulpages/0errors, replay0additionalcharges;0network/download. Stage vẫn cóagentsemanticreview, chưatựđộnghoàntoàn. Còn403one-gap/2.446annualcases; mốc1.001cần663dependencies/533candidates cóđiềukiện, khôngphảisốPDF.27targetedtests/compile/synthetic/source/value/replayPASS; goalPARTIAL.

Current summary: `Get-Content 'C:/Projects/Intern/SourceCode-CafeF/data/financial/history_pdf_cached_four_import_v1/results/ff79f6eed55270156392/summary.json'`. Current [cohortexports](../../artifacts/reports/financial-cached-four-review-v1/cohort-result-ref.json) dùng readinessconfigv2; frozenworkflow45 giữold464snapshot, khôngsửaoldconfig đểđổi số. Khôngcònworkerstage47chạynền, chưamởbatch50; batch100approvalgiữscope. Report tổng đãcậpnhật.

## Execution49 — DStock gap recovery, chốt coverage >1.000 (23/10/2026)

Owner cho phép các phase tiếp theo trong1giờ hoặc đến>1.000. Giữoriginalbaseline48/frozenartifacts. Pin DStockfrontend/models/control; sourceadapteritemCode+label+modelType+membership,rawDecimal vàcompleteprovider vector. Chạy10→20→50→100→tăngtốiđa100mã/phase, group5mã/năm/request.12precisionQAchecks giữnguyên, khôngaverage/fieldmix/abs/sign; khôngpublished_at từcreated/modified.

Đãxửlý600candidates/797gapcases,738core-pass rows/1.017full10sơbộ. Additionalcashgate kiểmCFO+CFI+CFF=netcash,rollforward,cash-to-BS vớiabsolute≤1VNDvàrelative≤1e-9:16kỳheld,5smallresidualpass. Final722newrows/12.568rows/1.002full10;cohort10y10.020rows.11.846oldrowsunchanged,4.332independentratios/23.826sourcevalues/42tests/compile/synthetic/replayPASS.

Budgetamendmenttheoownerscopemới:thêm≤900logical/≤1.800attempts/≤250MB,0PDFcapincrease;inheritedcounters/campaignanchor/sourceboundariesvàcùngdeadlinefixedgiữqualạiv2/v3. Thựctế194requests/194attempts/28.262.575bytes;0PDF/OCR/401/403/429. Networkdừng08:10:24UTC;cashQA/bàngiaooffline. Khôngresumevượtauthorizationdeadlinehoặctựmởthêmbatchsauđạtgoal.

Hiệncòn75held/67candidatesvà1.647unacquiredgapcases,1.722gaps;PDFneedcountnull/chưađịnh. [Fieldsreview](../../artifacts/reports/financial-dstock-gap-recovery-v1/cashflow-field-review.csv),[bàngiao](../../artifacts/reports/financial-dstock-gap-recovery-v1/delivery-cash-result-ref.json). Cohortsreferencecóthểchobaselineđúngprotocol/versionmới;identity/vintage/PIT/marketjoin/M3vàoriginalsixfamiliesvẫnclosed. Khôngthaymodel51mãcũ.

## 50. Execution — Hoàn tất remaining DStock API (23/10/2026)

**Execution50 hiện hành (23/10/2026):**1.172full10 annual2016–2025 /13.529core-ratio reference rows; +170mã/+961rows,12.568baseline rows nguyên vẹn. Đã thử hết2.444Regular annual gap cases qua49+50; còn761held/257Regular,95mã9/10 và93candidates ngoài schema. [Report50](../../artifacts/reports/financial-dstock-remaining-v1/report.md), [master](../../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [cohort delivery](../../artifacts/reports/financial-dstock-remaining-v1/delivery-result-ref.json).47targeted tests/independentPASS;0PDF/OCR;worker đã dừng. Warm-up/quarterly/originalsixfamilies/PIT/M3 chưa hoàn tất.

Thu1.647freshcases/360candidates với15checks trước acceptance; không gọi lại75priorheld. Giữ budgetcaps/counters/campaignanchor, window08:38:50–09:38:50UTC;348core+11metadata requests, tổng41.766.049bytes.11metadata đều empty, không waive schema. Catalogue probe chưa chạy do automatic approval review usage limit;0request, không bypass.761heldcases là review queue, chưa phải PDFcount. Phải báo owner số tài liệu/scope trước tải thêm. Phạm vi50 không bao gồm crawlPDF/OCR, model refit, protocolchange hoặc PITpromotion. Lệnh hiện hành:`scripts/financial_dstock_remaining.ps1 -Mode Status`;Offline replay không network.
