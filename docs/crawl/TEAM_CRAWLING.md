# Team Crawling Standard

## 1. Mục tiêu

Cho phép nhiều người crawl song song nhưng không tạo nhiều “phiên bản sự thật”.

## 2. Đơn vị phân công

Một assignment nên là:

```text
source
+
dataset
+
symbol set
+
date range
+
adapter/mapping version
```

Ví dụ:

```json
{
  "assignment_id": "M1-CAFEF-MARKET-001",
  "collector": "member_a",
  "source": "CafeF",
  "dataset": "prices_daily",
  "symbols": ["FPT", "VNM", "HPG"],
  "start": "2020-01-01",
  "end": "2025-12-31",
  "adapter_version": "cafef-v1",
  "mapping_version": "market-v1",
  "status": "ASSIGNED"
}
```

## 3. Collector không được tự đổi

- field mapping;
- multiplier;
- timezone;
- price basis;
- financial quarter/YTD semantics;
- canonical names;
- source priority;
- reconciliation rule.

Nếu phát hiện mapping cũ sai:

```text
BLOCK batch
→ record evidence
→ review
→ decision
→ version bump
→ rerun normalization
```

Không sửa raw.

## 4. Cách partition

### Option A — theo symbol

Tốt khi endpoint theo ticker:

```text
batch 001: AAA ... CTG
batch 002: CTR ... HPG
```

### Option B — symbol × year range

Tốt khi source giới hạn range/page:

```text
FPT-2015-2019
FPT-2020-2024
FPT-2025-2026
```

## 5. Không nên chia theo field

Không giao:

```text
A crawl close
B crawl volume
C crawl ceiling/floor
```

cho cùng source/time range.

Nên một batch crawl toàn bộ declared source schema để giữ cùng revision/timestamp.

## 6. Handoff

Mỗi batch:

```text
manifest.json
raw/
checksums.sha256
collector_report.md
```

## 7. Duplicate collection

Hai người chỉ crawl cùng batch khi:

- intentionally cross-checking;
- source comparison;
- recovery/audit.

Phải ghi:

```text
duplicate_reason
```

## 8. Shared storage

Không dùng Git làm data lake.

Nên có shared storage có:

- immutable batch folders;
- write ownership;
- checksums;
- assignment index;
- access controls phù hợp license/source terms.

## 9. Merge

Không merge raw file thủ công.

Canonical merge phải chạy qua:

```text
normalize
→ reconcile
→ QC
→ canonical run
```
