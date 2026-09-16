# Source Discovery Guide

## 1. Mục tiêu

Trước khi code adapter cho CafeF, VietFin hoặc source khác, team phải hiểu source đang trả dữ liệu gì.

Discovery phải trả lời:

1. Endpoint/document nào cung cấp dữ liệu?
2. Field nào có nghĩa gì?
3. Unit là gì?
4. Timestamp/timezone là gì?
5. Price là raw hay adjusted?
6. Pagination/date boundary thế nào?
7. Source có cho automation không?
8. Có rate limit/access restriction không?
9. Source có đủ history không?
10. Có corporate actions/financial publication metadata không?
11. Có current/historical share hoặc capital-structure data không?

## 2. Workflow bằng browser

### Step 1 — review quyền truy cập

Đọc:

- Terms;
- robots/access policy;
- API docs nếu có;
- login/subscription requirement.

Nếu gặp:

- CAPTCHA;
- login wall;
- paywall;
- anti-bot challenge;
- token/cookie không được phép chia sẻ;
- 401/403 cố định;

**dừng**. Không bypass.

### Step 2 — chọn mã mẫu

Khuyến nghị ban đầu:

- FPT — HOSE, có corporate-action case dễ đối chiếu;
- VNM — HOSE, lịch sử dài;
- PVS — HNX;
- ACV — UPCOM;
- 1 mã short-history/inactive edge case được source xác minh.

Danh sách có thể thay đổi nếu source không hỗ trợ; mọi thay đổi phải ghi rationale.

### Step 3 — DevTools

Chrome/Edge:

```text
F12
→ Network
→ Fetch/XHR
```

Thực hiện:

- reload;
- đổi ticker;
- đổi date range;
- chuyển page;
- mở financial tab.

Ghi:

- method;
- host/path;
- query/body;
- pagination;
- response content type;
- required headers không chứa secret.

### Step 4 — sample nhỏ

Không tự động hóa ngay.

Lấy:

- 5–10 market rows;
- current share snapshot và historical change sample nếu source có;
- 1 corporate-action case;
- ít nhất 3 quarterly reports.

So khớp với UI/source display.

### Step 5 — semantics

Ghi rõ:

```text
field: close
source_name: ...
unit: ...
canonical_unit: ...
multiplier: ...
basis: raw/vendor_adjusted/...
timezone: ...
evidence: ...
confidence: ...
```

Không suy multiplier chỉ vì “giá có vẻ nhỏ 1000 lần”.

### Capital-structure check

Với mỗi source, ghi rõ:

- current listed shares có không;
- current outstanding shares có không;
- issued/treasury shares có không;
- historical changes có không;
- effective date có không;
- publication/available time có không.

Kết luận bằng đúng một status: `VERIFIED_AVAILABLE`, `CURRENT_SNAPSHOT_ONLY`, `HISTORICAL_UNAVAILABLE` hoặc `BLOCKED`. Thiếu share history ở một market-price source không tự động loại source đó; domain này có thể do source khác đã được duyệt cung cấp, nhưng limitation phải explicit. Không backfill current counts về lịch sử.

### Step 6 — pagination/range

Xác minh:

- inclusive/exclusive start/end;
- max page size;
- sort ascending/descending;
- duplicate page;
- empty page;
- repeated cursor;
- max range/request.

### Step 7 — source note

Tạo:

```text
docs/crawl/sources/CAFEF.md
docs/crawl/sources/VIETFIN.md
```

theo `SOURCE_NOTE_TEMPLATE.md`.

## 3. Discovery completion criteria

Source chỉ được chuyển từ:

```text
DISCOVERED
```

sang:

```text
ACCESS_TESTED
```

khi request/document có thể truy cập hợp lệ.

Chỉ được chuyển sang:

```text
SEMANTICS_VERIFIED
```

khi:

- field mapping;
- unit;
- timezone;
- price basis;
- date semantics;
- pagination;
- rights/rate limit

đã có evidence.

Adapter chỉ được dùng cho real `SOURCE_SMOKE` sau bước này.
