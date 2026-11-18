# Plan market 10 năm và ít nhất 1.500 cổ phiếu lịch sử

Ngày: 19/10/2026. Trạng thái: **PLANNED — chưa chạy acquisition mới**.
Đầu ra lượt materialize này là tài liệu và inventory offline, không phải dataset
10 năm đã hoàn tất. Owner yêu cầu hai workstream market/financial riêng, cùng một
universe registry. Plan này thay phạm vi market trong đề xuất gộp trước đó;
không thay artifacts C5/C7/C8 hoặc protocol M2 đã freeze.

## 1. Mục tiêu, range và định nghĩa hoàn tất

| Hạng mục | Hợp đồng |
|---|---|
| Cửa sổ nghiên cứu | 01/01/2016–31/12/2025: 10 năm trọn vẹn |
| Warm-up | Thu thêm market 2013–2015 khi có để hỗ trợ lookback và yêu cầu ba calendar years usable history |
| Số lượng | Ít nhất 1.500 cổ phiếu riêng biệt có market observation hợp lệ trong cửa sổ chính |
| Thị trường | HOSE, HNX, UPCoM; gồm cổ phiếu đã rời sàn, đổi mã, chuyển sàn |
| Lịch sử từng mã | Phần thực có; không đòi mỗi mã tồn tại đủ 10 năm |
| Financial | Theo [plan financial riêng](FINANCIAL_HISTORY_PIT_PLAN.md), không chặn market acquisition |
| M3 | Bàn giao evidence/readiness và gaps; chưa chạy backtest |

Một `security_id` đã phân giải và có ít nhất một observation hợp lệ trong
2016–2025 được tính vào acquisition count. Đây không phải tiêu chí feature-ready
hay M3-ready. Ticker tái sử dụng không tự nối lịch sử; đổi ticker/chuyển sàn không
tự đếm thêm cổ phiếu. Không dừng discovery ở 1.500 để loại phần universe lịch sử
còn lại. Mã chỉ xuất hiện sau 2025 không đóng góp mục tiêu, dù có trong discovery.

Giữ riêng ba kết luận: **acquisition delivery**, **feature readiness theo snapshot**,
**M3 readiness**. Mục tiêu nào chưa đạt phải `PARTIAL` kèm số thực và lý do.

## 2. Hiện trạng và danh sách mã duy nhất

Danh sách dùng chung cho cả team:
[securities_collection_registry_v1.csv](../../configs/data/securities_collection_registry_v1.csv).
Không chép một danh sách ticker khác vào plan hoặc assignment.

| Bằng chứng legacy | Số mã |
|---|---:|
| C5 baseline đã đưa qua C8 | 500 |
| C7 complete expansion đã đưa qua C8 | 452 |
| C7 acquisition failed, deferred khỏi C8 | 7 |
| C7 acquisition partial, deferred khỏi C8 | 3 |
| C7 not yet acquired trong campaign đó | 138 |
| Ngoài universe C5/C7 | 422 |
| **Tổng current discovery candidates** | **1.522** |

952 mã đã được xử lý C8; 905 market-ready tại **28/08/2026**. Hai con số không
chứng minh coverage 2016–2025 hoặc historical identity. Current discovery có
405 HOSE, 299 HNX, 818 UPCoM; chưa phải historical census.

Nguồn inventory ban đầu, không fetch lại:

- [KBS discovery snapshot](../../configs/data/cafef_expansion_v1/discovery_snapshot.json)
  và [receipt](../../configs/data/cafef_expansion_v1/discovery_evidence.json), 25/09/2026.
- [C8 candidates](../../artifacts/cafef_primary/cafef-c8-complete-only-v1/candidate_universe.csv),
  [deferred](../../artifacts/cafef_primary/cafef-c8-complete-only-v1/deferred_expansion.csv),
  [readiness](../../artifacts/cafef_primary/cafef-c8-complete-only-v1/feature_readiness.csv).
- C8 canonical price rows để lấy actual observed bounds; không lấy audit-start
  hoặc listing candidate làm observed start. Registry lịch sử cũ được ghi riêng
  khi thấy; đó không tự chứng nhận cache tương thích với campaign mới.

422 mã ngoài C5/C7 giữ trạng thái acquisition ngoài hai campaign là `UNKNOWN`.
Đã kiểm thêm registry lịch sử cũ và ghi evidence tìm thấy; các legacy run khác
chưa được inventory toàn diện. Không viết `NOT_CRAWLED` dựa vào việc thiếu C8.

Registry lịch sử cũ có 27 records: 10 `LONG_HISTORY_COMPLETE`, một `PARTIAL`,
16 `NOT_STARTED` theo contract riêng. Cờ này được giữ ở additional inventory,
không ghi đè observed bounds của C8 hoặc kết luận readiness mới.

## 3. Registry contract và phối hợp team

Registry là UTF-8 CSV, header tiếng Anh, tên công ty giữ Unicode; ngày ISO,
dòng sắp theo ticker/exchange. Dấu `;` phân cách các phần tử trong một ô.
Ô trống là unknown/unassigned, không mặc định false hoặc zero. Cột enum dùng
`UNKNOWN`/`NOT_ASSESSED` khi phù hợp; cờ readiness đã có bằng chứng dùng TRUE/FALSE.

SHA256 registry tại bàn giao v1:
`6d34d2262c7083d1f613046ea777a2a9f1d57d25a2aa3267d10e9fa8c1a877b0`.
Hash khóa exact bytes, không phải lịch sử mã đã được xác minh. Mỗi lần cập nhật
phải repin hash cho assignment mới, không sửa membership của run đang freeze.

| Nhóm cột | Cách đọc/cập nhật |
|---|---|
| `registry_id`, `ticker`, `exchange`, `company_name` | Một record discovery; `registry_id` ổn định, giữ lại sau correction |
| `issuer_id`, `security_id`, `legacy_security_id`, `identity_status` | Hai canonical IDs để trống đến khi phân giải; provider ID cũ không thành canonical ID |
| `discovery_source`, `discovery_evidence`, `legacy_cohort` | Nguồn universe, source hash và nhóm C5/C7; không biến thành dữ liệu giá |
| `selection_status`, `selection_reason` | Khởi tạo `PLANNED_PENDING_IDENTITY_RANGE_CHECK` cho toàn bộ 1.522 candidates |
| `market_target_start/end`, `financial_target_start/end` | Acquisition range 2013–2025, gồm warm-up; không phải observed coverage |
| `market_legacy_acquisition_status`, `market_processing_status` | Trạng thái campaign legacy và xử lý C8 độc lập |
| `market_observed_start/end`, `market_coverage_status` | Min/max actual C8 observations; **không chứng minh liên tục** và không gộp raw-only cache vào đây |
| `market_readiness_snapshot_date`, `market_ready_at_snapshot` | Cờ C8 chỉ tại ngày được ghi; trống nếu ngoài C8 |
| `historical_identity_ready`, `m3_ready` | Khởi tạo FALSE; không tự mở từ acquisition count |
| `market_additional_inventory_status` | Legacy history evidence khác C8 nếu tìm thấy; không thay legacy cohort |
| `financial_inventory_status`, `financial_observed_periods` | Local coverage/candidates hoặc pilot result đã inventory; period có dữ liệu không có nghĩa đủ statement |
| `financial_verification_status`, `financial_pit_status` | Giá trị đã review khác candidate presence; chưa đánh giá khác đã fail |
| `verified_metric_count`, `metric_target_count`, `financial_metric_scope` | Count chỉ pin pilot5 FY2025; còn lại trống, không suy 0 hoặc sáu chỉ số áp dụng mọi ngành |
| `financial_inventory_scope` | Phạm vi quét local exports, còn thiếu other reviews/runs/archives |
| `market_next_action`, `financial_next_action`, `missing_reason` | Việc cụ thể còn cần làm, kể cả đã crawl legacy |
| `market_owner`, `market_batch_id`, `financial_owner`, `financial_batch_id` | Chỉ điền sau khi phân công; ban đầu trống |
| `market_evidence_ref`, `financial_evidence_ref`, `updated_at` | `relative/path@sha256:hash`, hoặc nhiều refs phân cách `;`; ngày cập nhật inventory |

Registry v1 pin `registry_id = SEC-COLLECT-<16 hex SHA256>` từ namespace discovery
25/09/2026 + ticker + exchange. Đây là khóa inventory provisional, không phải
historical security identity. Khi thêm alias/chuyển sàn phải review và giữ ID record
hiện hữu; nếu phát hiện ticker tái sử dụng thì tách identity, lưu lineage và bump
registry version. Không tự gộp vì ticker giống nhau. Thêm ISIN và alias intervals
vào evidence identity của campaign; không suy ISIN từ ticker.

**Team workflow:** một maintainer merge registry; người thực hiện gửi run evidence.
Mỗi assignment pin registry version + SHA256 + domain + registry/security IDs +
range + batch. Không tự copy danh sách và không nhận trùng domain/security/range.
Market/financial có thể có owner khác nhau. Membership đã freeze không sửa giữa
run; thêm mã hoặc correction tạo version/assignment kế tiếp. Không dùng CSV như
distributed lock hay thay journal của runner.

Ví dụ xem nhóm cần làm bằng PowerShell, không phát network:

```powershell
$registryRows = Import-Csv -LiteralPath .\configs\data\securities_collection_registry_v1.csv -Encoding UTF8
$registryRows | Group-Object market_legacy_acquisition_status | Select-Object Name, Count
$registryRows | Where-Object legacy_cohort -eq 'OUTSIDE_C5_C7_UNIVERSE' | Select-Object ticker, exchange, market_next_action
Get-FileHash -LiteralPath .\configs\data\securities_collection_registry_v1.csv -Algorithm SHA256
```

## 4. Discovery lịch sử và source policy

1. Hợp nhất current candidates với listing/delisting, hủy ĐKGD, đổi mã/chuyển sàn
   theo HOSE/HNX và VSDC. Giữ source document, hiệu lực và publication evidence.
2. Tách common stock khỏi ETF, chứng quyền, trái phiếu. Kiểm activity overlap
   2016–2025; không kết luận trước listing từ first API observation.
3. Liên kết issuer/security/venue intervals. Ambiguous mapping quarantine, không
   nối giá qua identity gap hoặc trùng ticker. Current profile không là sector lịch sử.
4. Freeze universe mới, gồm exclusions và lý do; bảo toàn mọi candidate khám phá.

Nguồn public discovery cần probe có giới hạn: [HNX hủy niêm yết](https://www.hnx.vn/vi-vn/co-phieu-etfs/chung-khoan-ny-huy.html),
[UPCoM hủy ĐKGD](https://www.hnx.vn/vi-vn/co-phieu-etfs/chung-khoan-uc-huy-dkgd.html),
[VSDC chuyển sàn](https://www.vsd.vn/tra-cuu-thong-ke/TK_MACK_CHUYENSAN?tab=4).
Chưa tuyên bố các trang đủ historical census hoặc đã tích hợp API. Nếu nguồn
HOSE/identity không truy cập đủ thì giữ gap, không thay bằng suy luận từ provider.

Market primary giữ CafeF `TradeHistoryNew.ashx` theo [source note](sources/CAFEF.md).
Endpoint đang dùng Symbol/PageIndex/PageSize=30; date filter chỉ dùng sau bounded
probe chứng minh hỗ trợ. KBS là cached discovery/cross-check khi được phép,
không auto fallback hoặc đổi nguồn âm thầm.

## 5. Acquisition, chuẩn hóa và QA

```text
registry + cache inventory → historical identity/range tasks
→ acquire missing partitions → normalize candidates → QA/quarantine
→ per-year/session coverage → feature readiness by snapshot → seal/verify
```

Tạo successor có configurable range; không đổi `TARGET_START=2020-01-01` của
runner C6 frozen. Reuse adapters/transport khi semantics và provenance tương thích.
Validate hashes, range, units, price basis trước cache reuse. Không bỏ toàn bộ
cache chỉ vì yêu cầu mới dài hơn; bổ sung partition thiếu và đối chiếu overlaps.

Giữ raw OHLC/close/reference/ceil/floor, matched/negotiated volume/value nếu có;
giữ vendor-adjusted close riêng cùng adjustment basis. Không tạo adjusted OHLC,
không coi vendor-adjusted là total-return series. Volume/value tổng chỉ tính khi
đủ components. Shares history/corporate actions cần các ngày công bố, ex-date,
effective date, record/payment date khi có; current shares không backfill lịch sử.

Pagination phát hiện duplicate pages, non-progress, overlap conflicts và page drift
sau resume. Journal pin payload hashes; không giả định old page index giữ nội dung.
QA khóa units trước scale, OHLC relationships, negatives, zero-volume versus missing,
calendar/session alignment, benchmark gaps, price basis change và quyền. Large jump
chỉ flag. Missing/invalid rows không ffill, không thành zero, không nén timeline.

Calendar cần nêu source/coverage, phân biệt observed benchmark union với authoritative
exchange calendar. Không tự mở research gate từ calendar provisional. Chuyển sàn
có gap không tạo return nối nếu thiếu căn cứ.

M3 handoff phải có shares/events/return basis, historical membership, tradability,
benchmark, terminal event và những holding thiếu exit/recovery value. Không tự
thanh lý ở last observed close, zero-value hoặc xóa mã để hết missing. Quy tắc
execution, costs, terminal positions thuộc protocol M3 review/freeze riêng.

## 6. Stages, vận hành và ngân sách

| Stage | Kết quả bắt buộc trước bước tiếp |
|---|---|
| M0 Offline | Pin registry/cache/source boundaries/config; doctor + dry-run 0 network; discovery task plan |
| M1 Pilot10 | Pilot5 cộng năm trường hợp chuyển sàn/rời sàn/lịch sử ngắn/financial sector; selection deterministic từ registry sau identity check |
| M2 Total50 | Đủ target task coverage, kiểm 2013–2019, đo request/bytes/time; xuất cost projection |
| M3 Total100 | Crash/resume, audit và artifact verification PASS |
| M4 Batch≤100 | Tự nối các batch sau gate, cùng budget/source latch; không tự mở research |
| M5 Consolidate | Dedup identity, coverage theo năm/tháng, actual acquisition count và M3 dependency report |

Các trường hợp pilot được chọn theo category có evidence rồi registry_id tăng dần;
nếu thiếu category thì ghi gap trước scale. Acquisition thử được chạy local qua
PowerShell sau successor contract, không gọi wrapper legacy với registry mới.

**Giao diện cần triển khai ở stage sau, hiện chưa tồn tại:**
`scripts/market_history10y.ps1 -Action doctor|plan|run|resume|qa|report|verify
-Config <frozen-config> [-Run <run-id>]`. `plan`/`verify` không gọi network.
Config/code/policy change tạo version mới; reserve budget trước I/O.

| Budget campaign đầu, dùng cùng scheduler với financial | Cap |
|---|---|
| Frozen candidates | 2.000; vượt thì backlog/new campaign, không silently truncate census |
| Global concurrency | 1 network request; market spacing ≥3 giây, finance/metadata ≥2 giây |
| Attempts/timeout | ≤2 attempts/logical task, transient only; timeout market/API 20 giây, PDF 25 giây |
| Market/security | ≤200 price pages +60 identity/event tasks |
| Financial/issuer | ≤240 structured +80 catalogue tasks (do financial runner tiêu thụ) |
| Discovery/benchmark chung | ≤5.000 logical tasks |
| PDF | ≤50 mới/batch, ≤1.000 mới/campaign, ≤25 MB/file |
| OCR | ≤1.000 trang mới/batch, ≤12.000/campaign, ≤40 trang/PDF |
| Structured response | ≤5 MB/response |
| New artifacts / free disk floor | ≤50 GB / ≥30 GB |
| Absolute deadline | 72 giờ/batch, 90 ngày/campaign từ created_at |

Global structured cap = 260×frozen securities +320×distinct issuers +5.000;
transport cap =2×logical cap, PDF attempts tách riêng tối đa 2×download cap.
Ngân sách là cap, không phải ETA. PDF/text/OCR cùng tính disk quota. Hết cap/deadline
seal backlog `DEFERRED_BUDGET`, không tự tăng hoặc reset qua resume.

Import mọi old source boundary trước network. 401/403/429/challenge latch đúng
source boundary; không đổi client, cookie hoặc hostname để thử vượt. Offline và
nguồn độc lập hợp lệ có thể tiếp tục. Không liên hệ IR hoặc gửi dữ liệu ra ngoài.

Gate batch: task/checkpoint accounted 100%; integrity/replay/resume PASS; không
accepted identity/key conflict; failed-after-retry ≤2% transport attempts;
parser/schema errors ≤1% successful responses; không critical accepted unit/kỳ/
scope/mapping finding; audit và budgets PASS. Với denominator 0 báo N/A, không
gán tỷ lệ 0. Audit ≥5% mã mới, tối thiểu 3 hoặc toàn bộ nếu batch nhỏ hơn; rotation
sàn/era/template theo seed pin trong config. Critical finding quarantine cohort,
dừng promotion và re-QA bằng version mới. Data absence vẫn giảm coverage dù
engineering gate có thể PASS.

## 7. Đầu ra, kiểm thử và acceptance

Output versioned: raw/hash objects, journal/checkpoints, identity intervals,
normalized/quarantine partitions, market coverage theo security/year/session,
anomalies, next-action queue, monthly readiness, batch summary và manifest.
CSV/gzip/JSONL đủ cho v1; không thêm DB/service/dashboard.

Test pagination repeat/drift, partial-cache reuse 0 network, duplicate identity,
rename/transfer/ticker reuse, new listing, delisting, missing/zero volume, OHLC,
units/basis/actions, crash sau reserve, torn journal, source latch, quota/deadline,
config mismatch và future append không đổi snapshot đã seal. Chạy targeted tests,
compile và synthetic smoke khi triển khai runner; full gate trước promotion
quan trọng. Giữ assertions/evidence cũ; báo riêng M2-PREP hash failure đã tồn tại.

Acquisition PASS chỉ khi ≥1.500 resolved securities có actual valid main-window
observations, task inventory đầy đủ và reproducible verification. Báo riêng số
full-10y, shorter-history, ready theo tháng, historical-identity-ready và M3-ready.
Nếu universe thực thu không đạt target hoặc còn phạm vi bắt buộc chưa xử lý:
**PARTIAL**, không dùng số attempts thay số mã có dữ liệu.

Trước thay acceptance liên quan historical identity, price/calendar semantics,
research eligibility hoặc final freeze: tạo review proposal/evidence cụ thể,
`MANUAL_REVIEW_REQUIRED` theo [AGENTS.md](../../AGENTS.md); không tự mở gate.
Market clustering và M3 thực thi sau protocol review riêng.
