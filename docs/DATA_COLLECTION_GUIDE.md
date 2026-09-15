# Hướng dẫn thu thập dữ liệu DELTA

Tài liệu này là quy trình làm việc chung cho mọi collector ở M1. Mục tiêu không chỉ là “lấy được dữ liệu”, mà là tạo raw evidence bất biến, hiểu đúng source semantics và chỉ promotion sang canonical sau review. Không dùng synthetic smoke làm bằng chứng source thật và không crawl quy mô lớn trước khi `REPRESENTATIVE_PILOT` PASS.

## 1. Ba lớp dữ liệu

- **RAW:** response/file đúng bytes nhận từ source cùng request, header được phép lưu, thời điểm fetch và SHA-256. Không sửa, làm tròn, đổi tên cột hoặc ghi đè.
- **Normalized candidate:** giá trị đã parse theo mapping/version, có unit, timezone, price basis và provenance; chưa phải winner.
- **Canonical:** field chuẩn của DELTA sau schema validation, field-level reconciliation và QC. Feature được tính sau từ canonical, không lưu như sự thật do vendor cung cấp.

## 2. Các data family bắt buộc

### 2.1 Security master

- **Fields cần thu thập:** provider security ID, ticker, exchange, issuer name, listing/delisting date, effective interval, status, sector/industry nếu có, currency và source timestamps.
- **Vì sao cần:** tạo historical universe và join theo `security_id`; current ticker membership không chứng minh thành viên lịch sử.
- **Giữ RAW:** toàn bộ listing response, provider ID, tên/cột gốc và delisted/inactive flags.
- **Canonical:** stable `security_id`, ticker/exchange theo `[valid_from, valid_to)`, listing/delisting, identity status và provenance.
- **Tính sau:** universe eligibility, listing age và coverage. Không để vendor tự quyết định cluster eligibility.

### 2.2 Daily market data

- **Fields cần thu thập:** date/time, open, high, low, close, reference, ceiling, floor, volume, traded value, trading status; adjusted close chỉ khi source định nghĩa rõ; source/available/fetched metadata.
- **Vì sao cần:** price path, liquidity, QC biên độ, corporate-action review, feature và backtest.
- **Giữ RAW:** provider field names/values, response timestamp, adjustment flags, pagination và request parameters.
- **Canonical:** `raw_open`, `raw_high`, `raw_low`, `raw_close`, `reference_price`, `ceiling_price`, `floor_price`, `adj_close`, `adjustment_basis`, `volume`, `traded_value`, `trading_status`, `available_at` và provenance. Price dùng VND/share, volume dùng shares, traded value dùng VND.
- **Tính sau:** momentum, volatility, downside risk, drawdown, beta và liquidity feature. Không coi vendor-computed momentum/volatility là source of truth.

Provider multiplier chỉ được cấu hình khi có evidence về unit. Không suy multiplier từ magnitude. Không tạo adjusted OHLC nếu source không cung cấp và không copy adjusted close sang raw close.

### 2.3 Corporate actions

- **Fields cần thu thập:** provider event ID, security, event type, announcement/ex/record/effective/payment date, cash amount, ratio, currency, status/revision và source document.
- **Vì sao cần:** giải thích gap/price basis, kiểm tra adjustment và tránh đếm dividend/split hai lần.
- **Giữ RAW:** notice/document và toàn bộ terms gốc.
- **Canonical:** versioned event với dates và economic terms đã normalize; ambiguous events phải quarantine.
- **Tính sau:** adjustment factor hoặc total-return series chỉ theo methodology riêng đã duyệt.

### 2.4 Quarterly financial reports và facts

- **Fields cần thu thập:** provider report/document ID, security, fiscal year/quarter, period start/end, statement scope, audit/accounting status, publication/availability, revision/restatement; facts gồm statement type, item code/name, instant/duration, value, currency và unit scale.
- **Vì sao cần:** financial feature point-in-time và kiểm soát look-ahead/restatement.
- **Giữ RAW:** PDF/JSON/HTML được phép lưu, provider IDs, taxonomy labels, presentation unit và revision metadata.
- **Canonical:** canonical report identity, period/scope/vintage, `available_at`; tidy facts theo taxonomy version. Provider ID không bị xóa mà ở provenance.
- **Tính sau:** ROE, ROA, growth và leverage ratios từ canonical facts khi denominator, annual/quarter/YTD/TTM, sector treatment và citation đã được duyệt. Vendor ratio chỉ là candidate để đối chiếu, không là source of truth.

### 2.5 Benchmark

- **Fields cần thu thập:** index ID, date, close/level, index basis, exchange/session, available/fetched time và source.
- **Vì sao cần:** beta, relative performance và M3 benchmark comparison.
- **Giữ RAW:** index response và provider basis description.
- **Canonical:** index points cùng `price`/`total_return` basis rõ ràng.
- **Tính sau:** benchmark returns, alpha/beta và information ratio. Không trộn price index với total-return index.

### 2.6 Trading calendar

- **Fields cần thu thập:** exchange, trade date, open/closed, session open/close, month-end, decision time, exceptional holidays/halts và evidence version.
- **Vì sao cần:** không nén missing session, xác định month-end snapshot và next eligible execution session.
- **Giữ RAW:** exchange/source calendar notice.
- **Canonical:** effective-dated session table với timezone-aware timestamps.
- **Tính sau:** rebalance schedule, missing-session coverage và session-based lookback.

### 2.7 Provenance và raw metadata

- **Fields cần thu thập:** source/provider, connector/adapter version, request URL pattern không chứa secret, parameters, page/cursor, HTTP status, fetched time, content type/size, source terms review, raw path/hash và transform version.
- **Vì sao cần:** reproducibility, audit, retry/resume và giải thích mọi canonical decision.
- **Giữ RAW:** request/response envelope và checksum.
- **Canonical:** chỉ các provenance fields cần truy vết; decision record liên kết mọi raw hash.
- **Tính sau:** coverage, freshness, conflict rate và data-quality report.

## 3. Workflow khám phá source thủ công

1. Đọc Terms of Service, robots/access policy, licensing và tài liệu API/SDK. Ghi source owner, ngày review và quyền được phép. Nếu cần login, API key, cookie, subscription hoặc có điều khoản hạn chế, **dừng** và yêu cầu permission/review.
2. Chọn 3–5 securities đại diện HOSE/HNX/UPCOM khi có thể; thêm short-history, inactive hoặc identity edge case. Yêu cầu ít nhất 5 năm nếu source hỗ trợ.
3. Mở trang công khai trong browser, mở DevTools → **Network**, lọc **Fetch/XHR**. Reload trang và thay đổi symbol/date để xác định request nào thực sự trả dữ liệu.
4. Ghi method, host/path, query/body parameters, headers thực sự cần, content type và response schema. Redact secret; không commit token/cookie.
5. Thử date range nhỏ rồi lớn hơn để xác định inclusive/exclusive boundary, sort order, maximum range, pagination/cursor/page size, duplicate page và empty-response semantics.
6. So sánh timestamp với giờ Việt Nam, session close và timezone offset. Không đổi `fetched_at` thành `available_at` nếu chưa có rule được review.
7. Đối chiếu open/high/low/close/reference/ceiling/floor, volume và traded value với 2–3 ngày hiển thị công khai. Ghi unit nguyên gốc; chỉ đề xuất multiplier kèm evidence.
8. Chọn known corporate action và ít nhất ba quarterly reports; kiểm tra raw/adjusted basis, publication date, revision/restatement và statement scope.
9. Ghi rate limit, retryable status, timeout và pagination behavior. 401/403, anti-bot challenge, paywall hoặc access control là điểm dừng; không bypass, giả mạo credential hay né rate limit.
10. Lưu source note, sample raw bytes, SHA-256 và collector report. Reviewer phê duyệt mapping/policy version trước khi agent viết adapter hoặc chạy `SOURCE_SMOKE` thật.

## 4. Gate workflow

1. `configs/data/synthetic_smoke.example.json`: chỉ kiểm thử plumbing; không thể pass gate thật.
2. `configs/data/source_smoke.example.json`: safe template `synthetic=false`, mặc định fail-closed. Chỉ enable sau rights/semantics review; PASS chỉ mở `REPRESENTATIVE_PILOT`.
3. `REPRESENTATIVE_PILOT`: 50–60 securities, >=5 năm, representative exchange/sector, historical identity, corporate actions, multi-source reconciliation, PIT financial và QC evidence. Chỉ PASS gate này mới mở planning >=300.
4. `M1_SCALE`: >=300 securities, >=5 năm. Không chạy trong pass tài liệu/readiness này.
5. `EXTENDED_SCALE`: historical eligible universe, 5–15 năm, có thể >1.200 securities; không có cap 350.

## 5. Phân công nhiều collector

Mỗi phần việc có một immutable assignment manifest:

```json
{
  "assignment_id": "M1-SMOKE-CAFEF-001",
  "collector": "REPLACE_WITH_NAME",
  "source": "CafeF",
  "dataset": "prices_daily",
  "symbols": ["FPT", "REPLACE_SYMBOL"],
  "start": "2020-01-01",
  "end": "2025-12-31",
  "adapter_version": "PENDING_REVIEW",
  "created_at": "2026-09-16T00:00:00+07:00",
  "status": "ASSIGNED"
}
```

Một collector chỉ thu thập đúng assignment. Collector **không tự đổi** field mapping, multiplier, timezone, price basis, financial period semantics hoặc canonical naming. Thay đổi semantics phải có reviewer, decision record, version bump và test fixture mới.

## 6. Handoff artifacts

Mỗi handoff gồm:

```text
manifest.json
raw/
checksums.sha256
collector_report.md
```

`manifest.json` ghi assignment/config/adapter/source review; `raw/` giữ bytes; `checksums.sha256` bao phủ từng file; `collector_report.md` theo mẫu:

```markdown
# Collector report — <assignment_id>

## Phạm vi
- Collector:
- Source/dataset/symbol/date range:
- Adapter/version:

## Access và rights
- Terms/API/login restriction:
- Permission/reviewer:

## Semantics quan sát được
- Endpoint/request/pagination:
- Unit/timezone/price basis:
- Corporate action/financial vintage cases:

## Kết quả
- Raw files/rows/checksum:
- Missing/duplicate/rate-limit/error:
- Cross-source mismatch:

## Đề xuất cần review
- Mapping/multiplier/rule/version:
- Blocker và câu hỏi mở:
```

## 7. Directory và artifact policy

Logical workspace ngoài Git có thể tổ chức:

```text
data_collection/
  assignments/
  raw/
  source_notes/
  handoff/
```

Khi nhập vào repository workflow, assignment/source note được liên kết tới immutable `data/vendor/<vendor-run>/raw`, promotion tạo `data/canonical/<canonical-run>`, và research chỉ đọc `data/runs/<run>`. Không sửa run cũ; config/code/policy/raw hash đổi thì tạo run mới.

Không commit large real datasets hoặc licensed content vào Git. JSON/JSONL phù hợp cho smoke, pilot và audit. Khi semantics M1 đã ổn định và quy mô đạt >=300 đến >1.200 securities × 5–15 năm, có thể review partitioned Parquet/DuckDB. Task này không migration storage.

## 8. Checklist trước handoff

- Raw bytes bất biến, đủ request/pagination metadata và SHA-256.
- Không có secret/cookie/token trong file.
- Unit, timezone, price basis và availability có evidence hoặc ghi `PENDING`.
- Không magnitude-based multiplier, zero-fill, forward-fill hoặc row averaging.
- Known corporate action và quarterly report samples đã đối chiếu.
- Collector report nêu cả mismatch/unfavorable evidence.
- Reviewer chưa duyệt thì status vẫn `BLOCKED`/`PENDING`; không tự nâng gate.
