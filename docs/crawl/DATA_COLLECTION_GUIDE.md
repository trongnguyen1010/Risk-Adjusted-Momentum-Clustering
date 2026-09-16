# Data Collection Guide

## 1. Mục tiêu

DELTA thu thập dữ liệu để tạo evidence có thể kiểm tra và canonical data có thể tái tạo. Crawler chỉ acquire dữ liệu và provenance; không phải feature engine và không tự quyết định canonical winner.

Pipeline chuẩn:

```text
Source
  ↓
RAW immutable evidence
  ↓
Normalized candidates
  ↓
Field-level reconciliation
  ↓
Canonical data
  ↓
QC / coverage
  ↓
Features
  ↓
Clustering / evaluation / backtest
```

## 2. Ba lớp dữ liệu

- **RAW:** bytes/payload đúng như source cung cấp, kèm request và fetch metadata. Không rename, scale, round, sửa hoặc ghi đè.
- **Normalized candidate:** giá trị đã parse theo mapping version, có unit, timezone, basis, provider identity và provenance. Đây vẫn chỉ là một candidate, chưa phải winner.
- **Canonical:** field chuẩn của DELTA sau schema validation, reconciliation, QC và explicit decision rule đã được duyệt/versioned.

Raw, canonical run và experiment artifact đều bất biến. Thay đổi code, mapping, policy hoặc input evidence phải tạo version/run mới.

## 3. Ranh giới theo data family

| Data family | RAW phải giữ | Normalized candidate | Canonical | Chỉ tính sau |
|---|---|---|---|---|
| Security master | Provider ID, listing payload, tên/cột gốc, inactive/delisted flags | Identity và effective interval được map nhưng vẫn gắn provider | Stable `security_id`, ticker/exchange theo thời gian, listing/delisting và provenance | Historical-universe eligibility, listing age, coverage |
| Shares / capital structure | Provider IDs/descriptions và current/historical snapshots | Listed/outstanding/issued/treasury counts theo unit, effective/available timing và provenance | Nullable non-negative share counts theo `security_id + effective_date` | Historical market cap, valuation và future size feature |
| Daily market | Provider fields/values, adjustment flags, request, pagination và timestamps | OHLC, reference/ceiling/floor, volume/value đã normalize unit, timezone và price basis | Raw-price fields và adjusted fields tách biệt, trading status, availability và provenance | Return, momentum, volatility, drawdown, beta, liquidity |
| Corporate actions | Notice/document và toàn bộ terms gốc | Event dates và economic terms đã parse; ambiguity chưa được che giấu | Versioned event đã normalize; trường hợp mơ hồ phải quarantine | Adjustment factor hoặc total-return series theo methodology đã duyệt |
| Financial reports/facts | Document/payload, provider report ID, taxonomy label, presentation unit và revision metadata | Facts và report metadata giữ rõ period semantics, scope, unit scale và vintage | Canonical report identity, point-in-time availability, revision-aware facts theo taxonomy version | ROE/ROA, growth, leverage và các ratio khác |
| Benchmark | Provider payload và mô tả index basis | Index observations đã normalize nhưng vẫn gắn basis | Versioned index series có `price` hoặc `total_return` basis rõ ràng | Benchmark return, alpha/beta, information ratio |
| Trading calendar | Calendar/notice của exchange hoặc source | Session và ngoại lệ đã parse cùng timezone/effective date | Effective-dated session table | Month-end snapshot, rebalance schedule, missing-session coverage |

Danh mục field chi tiết nằm trong [FIELD_CATALOG.md](FIELD_CATALOG.md).

## 4. Invariant về semantics

### Market units và price basis

- Canonical price dùng VND/share, volume dùng shares và traded value dùng VND.
- Provider multiplier chỉ được cấu hình khi có evidence về unit. **Không bao giờ suy multiplier từ magnitude.**
- Raw, adjusted và total-return series là các basis khác nhau và không được trộn.
- Không tạo adjusted OHLC nếu source không cung cấp hoặc methodology chưa được duyệt.
- Không bao giờ copy adjusted close vào raw close.

### Financial period semantics

Mỗi report/fact phải giữ rõ:

- standalone quarter, YTD hay TTM; các kỳ này không tương đương và không được reconcile trực tiếp;
- consolidated hay separate;
- currency và unit scale;
- publication/availability time;
- revision/restatement và report vintage.

Financial join chỉ được dùng vintage mới nhất đã `available_at <= decision_at`, không dùng bản mới nhất biết ở hiện tại. Provider report ID phải được giữ trong provenance, tách biệt với canonical report identity và reconciliation comparison key.

### Share-count semantics

Listed, outstanding, issued và treasury shares không được giả định bằng nhau. Current snapshot không được áp dụng ngược về lịch sử; source chỉ có current snapshot phải được ghi đúng limitation. `available_at` có thể trước hoặc sau `effective_date`, và provider IDs/descriptions chưa được duyệt phải ở RAW/provenance.

### Provenance

Mọi batch và mọi quyết định canonical phải truy ngược được tới:

- source/underlying provider và provider identity;
- endpoint hoặc document, request parameters và page/cursor;
- adapter, mapping và transform version;
- fetch/availability timestamp, status/error và content metadata;
- raw path, raw SHA-256 và các evidence/decision record liên quan.

Request metadata không được chứa secret. Khác biệt về `source`, `fetched_at` hoặc raw hash không tự tạo economic value conflict.

## 5. Multi-source rule

Reconciliation diễn ra theo canonical entity/key và theo từng field. Không average conflict. Source priority chỉ được dùng khi policy đã approved, versioned và documented; unit, price-basis, timing hoặc identity conflict chưa được policy giải quyết phải giữ unresolved.

Vendor-computed feature hoặc ratio có thể giữ ở RAW để cross-check nhưng không mặc định là canonical. Features và research metrics phải được tính từ canonical data theo methodology đã duyệt.

Market cap, BVPS, P/E, P/B và F/M/Z score variants là derived analytics. EPS cần weighted-average basic/diluted shares hoặc documented vendor basis; end-of-period outstanding shares không đủ để tái tạo standard EPS.

## 6. Storage và scale

Không commit large real datasets hoặc licensed source dumps vào Git. Git chỉ giữ code, schemas, configs, docs, source semantics, manifest/evidence nhỏ và decision records. Real raw/canonical data phải nằm trong immutable local/shared run storage có checksum và access control phù hợp.

Các gate không được bỏ qua:

- `SOURCE_SMOKE`: 3–5 mã thật; PASS chỉ mở representative pilot.
- `REPRESENTATIVE_PILOT`: 50–60 mã, >=5 năm; PASS mới mở planning M1 scale.
- `M1_SCALE`: >=300 mã, >=5 năm.
- `EXTENDED_SCALE`: historical eligible universe, 5–15 năm, có thể >1.200 mã.

Mã có dưới ba năm usable observed history là `REFERENCE_ONLY`, không được ép vào clustering universe. Synthetic data chỉ kiểm thử plumbing và không thể pass real-data gate.

## 7. Hướng dẫn chuyên biệt

- [SOURCE_DISCOVERY.md](SOURCE_DISCOVERY.md): khám phá source, quyền truy cập và semantics.
- [SOURCE_SMOKE.md](SOURCE_SMOKE.md): scope, evidence và PASS/BLOCKED criteria.
- [TEAM_CRAWLING.md](TEAM_CRAWLING.md): assignment và phối hợp collector.
- [HANDOFF_TEMPLATE.md](HANDOFF_TEMPLATE.md): manifest, report và checklist bàn giao.
