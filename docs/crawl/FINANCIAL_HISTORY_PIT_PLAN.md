# Plan financial lịch sử và PIT phục vụ market 10 năm, M3 backtest

Ngày: 19/10/2026. Trạng thái: **PLANNED — chưa chạy acquisition mới**.
Lượt materialize chỉ lập plan/inventory offline. Giữ pilot5 **29/30 reference
metrics**, VNM F-score còn thiếu closing current portion của originally-long-term
debt tại 2024/2025. Không đổi công thức, kết quả hoặc financial/research gates.

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

**Giao diện cần triển khai ở stage sau, chưa có trong lượt materialize:**
`scripts/financial_history_pit.ps1 -Action doctor|plan|run|resume|qa|documents|ocr|
review-import|compute|snapshots|report|verify -Config <frozen-config> [-Run <run-id>]`.
`plan`/`verify` không network. Logic ở modules, PowerShell chỉ orchestrate.

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
