# Real SOURCE_SMOKE Guide

## 1. Mục tiêu

`SOURCE_SMOKE` là real-data gate nhỏ để chứng minh **source semantics và crawler mechanics**, không phải để tạo dataset nghiên cứu cuối cùng.

PASS `SOURCE_SMOKE` chỉ được phép mở:

```text
REPRESENTATIVE_PILOT
```

Nó không được phép unlock >=300 mã.

## 2. Scope

3–5 mã thật.

Khuyến nghị:

- FPT;
- VNM;
- PVS;
- ACV;
- 1 edge case short-history/inactive.

Cố gắng phủ:

- HOSE;
- HNX;
- UPCOM;
- corporate-action case;
- history >=5 năm nếu source hỗ trợ.

## 3. Data cần test

### Daily market

Bắt buộc verify:

- open;
- high;
- low;
- close;
- reference;
- ceiling;
- floor;
- volume;
- traded value;
- price basis;
- date/time semantics.

### Corporate actions

Ít nhất 1 known action.

### Shares / capital structure

Kiểm tra current listed/outstanding shares, issued/treasury shares, historical changes, effective date và publication/available time. Ghi một status: `VERIFIED_AVAILABLE`, `CURRENT_SNAPSHOT_ONLY`, `HISTORICAL_UNAVAILABLE` hoặc `BLOCKED`.

Market source không tự động fail chỉ vì thiếu historical share counts; source khác đã được duyệt có thể cung cấp domain này. Limitation phải explicit và current snapshot không được backfill về quá khứ.

### Financial

Ít nhất 3 quarterly reports cho một hoặc nhiều mã.

Kiểm tra:

- quarter;
- period end;
- publication/available date;
- consolidated/separate;
- unit scale;
- revision.

## 4. Cross-source table

Với một vài ngày:

| ticker | date | field | CafeF | VietFin | Kết luận |
|---|---|---|---:|---:|---|
| FPT | YYYY-MM-DD | close | | | MATCH/CONFLICT |
| FPT | YYYY-MM-DD | volume | | | |
| FPT | YYYY-MM-DD | reference | | | |
| FPT | YYYY-MM-DD | ceiling | | | |
| FPT | YYYY-MM-DD | floor | | | |

Conflict classification:

- MATCH;
- MISSING_ON_SOURCE;
- VALUE_CONFLICT;
- UNIT_CONFLICT;
- PRICE_BASIS_CONFLICT;
- TIMING_CONFLICT;
- IDENTITY_CONFLICT.

Không average.

## 5. Raw artifact

Mỗi request/page phải có:

```text
assignment_id
source
dataset
symbol
date_range
request metadata
fetched_at
adapter_version
raw SHA-256
raw path
page/cursor
HTTP/error state
```

## 6. PASS criteria

`SOURCE_SMOKE` chỉ PASS khi:

- real data;
- 3–5 symbols;
- representative exchange evidence;
- >=5y request hoặc documented source limitation;
- market required fields verified;
- >=1 corporate action inspected;
- shares/capital-structure availability status documented;
- >=3 quarterly reports inspected;
- unit/timezone/basis/pagination/rate behavior documented;
- access/rights reviewed;
- evidence hashes exist.

Nếu một required criterion chưa đạt:

```text
BLOCKED
```

Không “pass tạm”.

## 7. Kết quả cần sinh

- `docs/crawl/sources/CAFEF.md`;
- `docs/crawl/sources/VIETFIN.md`;
- source comparison report;
- immutable raw local run;
- smoke manifest;
- gate report;
- exact unresolved blockers;
- không crawl lớn.
