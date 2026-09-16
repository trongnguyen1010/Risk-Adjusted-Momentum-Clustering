# DELTA P0 Market Gate Resolution

## 1. Scope

Tài liệu này xử lý đúng ba market-side P0 gap trước real `SOURCE_SMOKE`:

- `GAP-001`: automation/data rights;
- `GAP-002`: historical `reference_price` / `ceiling_price` / `floor_price`;
- `GAP-003`: historical `traded_value` và matched/put-through inclusion.

Phạm vi symbol chỉ gồm FPT, VNM, PVS và ACV. Verification dùng một số ít public request đi theo đúng UI/documented paths, gồm hai normal trading days cho mỗi symbol và một mẫu FPT gần ngày ex-right đã có trong source note. Không tải full history, không rate-test, không bypass access control, không lưu raw response thành dataset và không xử lý `GAP-004 Financial PIT`.

Kết quả gate:

| Gap | Result | Confidence | Tóm tắt |
|---|---|---|---|
| GAP-001 | OPEN | HIGH | Không có end-to-end market acquisition path nào có public policy evidence cho phép bounded automated research collection và các quyền dữ liệu cần thiết |
| GAP-002 | RESOLVED | HIGH | CafeF có UI-linked historical response với `TradeDate`, `BasicPrice`, `Ceiling`, `Floor`; đã kiểm tra trên HOSE/HNX/UPCOM |
| GAP-003 | RESOLVED | HIGH | CafeF public UI source định nghĩa total hiển thị bằng matched `TotalValue` + put-through `AgreedValue`, cùng row/date và cùng đơn vị VND |

## 2. Existing evidence and current-vs-historical distinction

Discovery cũ đã đúng khi kết luận endpoint/table lịch sử `PriceHistory.ashx` không có reference/ceiling/floor. Tuy nhiên, kết luận cấp provider khi đó chưa bao phủ một public request thứ hai được trang tổng quan công ty gọi trực tiếp:

```text
GET /du-lieu/Ajax/PageNew/TradeHistoryNew.ashx
    ?Symbol={symbol}
    &PageIndex={1-based page}
    &PageSize={size}
```

Distinction sau verification:

- Current company snapshot FPT ngày 2026-09-16 hiển thị `Giá tham chiếu=72.70`, `Giá trần=77.70`, `Giá sàn=67.70`, đơn vị nghìn VND/share.
- Historical table và export của `PriceHistory.ashx` vẫn không có ba fields này.
- Historical request `TradeHistoryNew.ashx`, được inline client source của chính company page gọi, có `BasicPrice`, `Ceiling`, `Floor` trên từng `TradeDate`.
- KBS current board có `RE`, `CL`, `FL`; documented historical `data_day` chỉ có `t,o,h,l,c,v`.

Do đó, current screenshot không được dùng để suy ra history. Historical availability của CafeF được xác minh độc lập bằng historical rows; KBS vẫn là `CURRENT_SNAPSHOT_ONLY` cho ba limit-price fields.

## 3. GAP-001 Rights and access

Quyền được đánh giá riêng cho provider và acquisition client. `HTTP 200`, endpoint public, `robots.txt: Allow`, source-visible code hoặc open-source availability không tự tạo permission.

### 3.1 CafeF direct

Technical access trong bounded verification là public, không login/subscription/CAPTCHA. Public evidence đã kiểm tra:

- [CafeF robots.txt](https://cafef.vn/robots.txt): `User-agent: *`, `Allow: /`;
- [CafeF privacy policy](https://cafef.vn/static/chinh-sach-bao-mat.html): mô tả visitor data/cookie, không cấp quyền automation, storage, dataset creation hoặc redistribution;
- footer/disclaimer trên public data pages: dữ liệu mang tính tham khảo và CafeF không chịu trách nhiệm rủi ro sử dụng; đây không phải data license.

| Use case | Status | Evidence | Confidence |
|---|---|---|---|
| Manual research access | NOT_VERIFIED | Public browsing hoạt động, nhưng không tìm thấy public policy cấp data-use right; không suy permission từ public access | HIGH |
| Bounded automated requests | NOT_VERIFIED | `robots.txt` cho phép crawler path nhưng không phải automation/data license | HIGH |
| Local raw storage | NOT_VERIFIED | Privacy policy không cấp quyền lưu provider data | HIGH |
| Derived research dataset | NOT_VERIFIED | Không tìm thấy public data-reuse policy/license | HIGH |
| Thesis/reproducibility use | NOT_VERIFIED | Không tìm thấy public grant cho use case này | HIGH |
| Redistribution of raw provider data | NOT_VERIFIED | Không tìm thấy public redistribution grant | HIGH |

Kết luận path: public/manual access đã quan sát, nhưng rights status cho intended automated collection vẫn `NOT_VERIFIED`.

### 3.2 KBS provider

Technical access của documented KBS JSON paths hoạt động không login/token trong bounded checks. [KBS website robots.txt](https://www.kbsec.com.vn/robots.txt) cho phép `/` và loại trừ login/admin/editor paths; data host trả HTTP 400 cho `/robots.txt`. Public search trên official KBS domain không tìm thấy Terms/API/data policy cấp các quyền dưới đây. Robots và response accessibility không được dùng như permission evidence.

| Use case | Status | Evidence | Confidence |
|---|---|---|---|
| Manual research access | NOT_VERIFIED | Public provider response hoạt động nhưng không có explicit data-use grant | HIGH |
| Bounded automated requests | NOT_VERIFIED | Không tìm thấy public API/data policy cho direct KBS path | HIGH |
| Local raw storage | NOT_VERIFIED | Không có public storage grant | HIGH |
| Derived research dataset | NOT_VERIFIED | Không có public reuse/dataset grant | HIGH |
| Thesis/reproducibility use | NOT_VERIFIED | Không có public provider-data grant cho thesis/reproducibility | HIGH |
| Redistribution of raw provider data | NOT_VERIFIED | Không có public redistribution grant | HIGH |

Kết luận provider: technical access không bị chặn trong sample, nhưng data rights vẫn `NOT_VERIFIED`.

### 3.3 Vnstock client

[Vnstock license `license-2026.09`](https://www.vnstocks.com/onboard/giay-phep-su-dung) phân biệt rõ software rights và third-party data rights:

- Community software dành cho personal/learning/research;
- software tự động gửi request từ hạ tầng người dùng tới third-party provider;
- client usage có tier/quota và cấm né limit hoặc tạo abnormal load;
- công bố research phải cite Vnstock;
- license không cấp quyền truy cập, lưu, hiển thị, phân phối hoặc khai thác provider data;
- provider terms vẫn áp dụng trực tiếp.

[Vnstock README](https://github.com/thinh-vu/vnstock) công bố client quotas: Guest 20 calls/minute, Community 60 và Sponsor 180–600; quota không phải data license.

| Use case | Status | Evidence | Confidence |
|---|---|---|---|
| Manual research access | ALLOWED_BY_PUBLIC_POLICY | Community software được cấp cho personal/learning/research | HIGH |
| Bounded automated requests | RESTRICTED | Client automation được mô tả nhưng phải đúng license/tier/quota, không abnormal load; provider permission vẫn riêng | HIGH |
| Local raw storage | NOT_VERIFIED | Vnstock nói rõ license không cấp third-party data storage rights | HIGH |
| Derived research dataset | NOT_VERIFIED | Client license không chuyển giao third-party data reuse rights | HIGH |
| Thesis/reproducibility use | ALLOWED_BY_PUBLIC_POLICY | Research/publication use của software được cho phép với citation; không thay thế provider-data permission | HIGH |
| Redistribution of raw provider data | NOT_VERIFIED | Vnstock không cấp raw provider-data redistribution right | HIGH |

Kết luận client: software use có thể hợp lệ theo điều kiện, nhưng không chữa được `NOT_VERIFIED` ở KBS provider layer.

### 3.4 GAP-001 decision

```text
GAP-001 = OPEN
```

Không intended path nào đạt end-to-end public policy evidence cho bounded automated research collection:

- CafeF direct: provider automation/storage/research-data rights `NOT_VERIFIED`.
- KBS via Vnstock: client software automation `RESTRICTED`, còn KBS provider data rights `NOT_VERIFIED`.

Required next action: nhận policy/permission clarification cho đúng provider path hoặc chọn replacement source có explicit automation/data rights. Không được chuyển `NOT_VERIFIED` thành `ALLOWED_BY_PUBLIC_POLICY` chỉ vì verification requests thành công.

## 4. GAP-002 Historical reference/ceiling/floor

### 4.1 CafeF current snapshot

Public FPT company page ngày 2026-09-16 hiển thị:

| UI label | Displayed value | Source unit | Canonical transform | Evidence type | Confidence |
|---|---:|---|---|---|---|
| Giá tham chiếu | 72.70 | nghìn VND/share | `×1,000` | UI_LABEL | HIGH |
| Giá trần | 77.70 | nghìn VND/share | `×1,000` | UI_LABEL | HIGH |
| Giá sàn | 67.70 | nghìn VND/share | `×1,000` | UI_LABEL | HIGH |

Đây chỉ là current-session snapshot evidence.

### 4.2 CafeF historical investigation

#### Historical table, JSON/XHR và export

Public history page [FPT lịch sử giao dịch](https://cafef.vn/du-lieu/Lich-su-giao-dich/hose/fpt-1.chn) dẫn tới `PriceHistory.ashx`.

`PriceHistory.ashx` trả 12 fields:

```text
Symbol, Ngay, GiaDieuChinh, GiaDongCua, ThayDoi,
KhoiLuongKhopLenh, GiaTriKhopLenh, KLThoaThuan, GtThoaThuan,
GiaMoCua, GiaCaoNhat, GiaThapNhat
```

UI table và UI-exposed XLSX export có cùng 12 columns. Không nơi nào trong path này có reference/ceiling/floor. Export được đọc in-memory, không lưu file.

#### Company-page historical request

Public FPT company page inline client source khai báo:

```text
var path = `/du-lieu/Ajax/PageNew/`;
TradeHistoryNew.ashx?Symbol=${symbol}&PageIndex=1&PageSize=30
```

Response row fields:

```text
Symbol, TradeDate, BasicPrice, ClosePrice, Volume, AdjustPrice,
Ceiling, Floor, TotalValue, AgreedVolume, AgreedValue
```

Mapping:

| Source field | Meaning | Source unit | Canonical target | Transform | Evidence | Confidence |
|---|---|---|---|---|---|---|
| `TradeDate` | Timestamp đại diện trade date | ISO UTC timestamp; observed `17:00:00Z` ngày trước local date | `trade_date` | Convert sang `Asia/Ho_Chi_Minh`, lấy local calendar date | PUBLIC_RESPONSE + UI cross-check | HIGH |
| `BasicPrice` | Historical reference price | nghìn VND/share | `reference_price` | `×1,000` | Repeated four-symbol response, current UI terminology/value consistency | MEDIUM |
| `Ceiling` | Historical ceiling price | nghìn VND/share | `ceiling_price` | `×1,000` | Explicit response key, repeated four-symbol rows | HIGH |
| `Floor` | Historical floor price | nghìn VND/share | `floor_price` | `×1,000` | Explicit response key, repeated four-symbol rows | HIGH |

Date semantics được xác minh bằng UI-response agreement: response `2026-09-14T17:00:00Z` được UI hiển thị là `15/09/2026`, tương ứng local `UTC+07`. Không dùng timestamp này làm publication/availability time.

Bounded samples:

| Symbol | Exchange | Local trade date | BasicPrice | Ceiling | Floor | Evidence type |
|---|---|---|---:|---:|---:|---|
| FPT | HOSE | 2026-09-15 | 72.4 | 77.4 | 67.4 | PUBLIC_RESPONSE |
| VNM | HOSE | 2026-09-15 | 59.3 | 63.4 | 55.2 | PUBLIC_RESPONSE |
| PVS | HNX | 2026-09-15 | 32.6 | 35.8 | 29.4 | PUBLIC_RESPONSE |
| ACV | UPCOM | 2026-09-15 | 38.9 | 44.7 | 33.1 | PUBLIC_RESPONSE |
| FPT | HOSE | 2026-05-28, ex-right-adjacent sample | 72.6 | 77.6 | 67.6 | PUBLIC_RESPONSE |
| FPT | HOSE | 2026-05-29 | 71.2 | 76.1 | 66.3 | PUBLIC_RESPONSE |

Các giá trị trên là đơn vị nguồn nghìn VND/share. Chúng thay đổi theo historical row/date và do source trả trực tiếp; không có field nào được derive từ previous close hoặc price-band formula.

CafeF conclusion:

```text
HISTORICAL_AVAILABLE
```

### 4.3 KBS current snapshot

Documented current board `POST /iis-server/investment/stock/iss` trả:

| Source field | Meaning | Unit | FPT sample 2026-09-16 | Evidence type | Confidence |
|---|---|---|---:|---|---|
| `RE` | Current reference price | VND/share | 72,700 | PUBLIC_RESPONSE + CLIENT_SOURCE | HIGH |
| `CL` | Current ceiling price | VND/share | 77,700 | PUBLIC_RESPONSE + CLIENT_SOURCE | HIGH |
| `FL` | Current floor price | VND/share | 67,700 | PUBLIC_RESPONSE + CLIENT_SOURCE | HIGH |

Current board cũng trả đúng ba fields trên cho VNM/PVS/ACV trong một bounded request. Đây vẫn là snapshot, không phải historical rows.

### 4.4 KBS historical investigation

Documented KBS/Vnstock historical path:

```text
GET kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_day
    ?sdate=02-01-2025
    &edate=03-01-2025
```

Hai rows trên mỗi FPT/VNM/PVS/ACV đều chỉ có:

```text
t, o, h, l, c, v
```

[Current Vnstock KBS constants](https://github.com/thinh-vu/vnstock/blob/main/vnstock/explorer/kbs/const.py) cũng định nghĩa `_OHLC_MAP` chỉ cho `t,o,h,l,c,v`. `RE/CL/FL` nằm riêng trong price-board mapping. Không inspect hoặc đoán KBS endpoint khác.

KBS conclusion:

```text
CURRENT_SNAPSHOT_ONLY
```

### 4.5 GAP-002 decision

```text
GAP-002 = RESOLVED
```

CafeF `TradeHistoryNew.ashx` là public UI-linked path có `trade_date`, `reference_price`, `ceiling_price`, `floor_price` theo historical row, với unit/transform và local-date semantics đủ rõ. KBS không được dùng để fill gap này; KBS vẫn current-only.

Việc resolve semantic availability không resolve CafeF rights. Collection vẫn bị chặn riêng bởi `GAP-001`.

## 5. GAP-003 Traded-value semantics

### 5.1 CafeF historical fields

Hai public historical responses cung cấp cross-check độc lập:

| Concept | `PriceHistory.ashx` | Source unit | `TradeHistoryNew.ashx` | Source unit | Meaning confidence |
|---|---|---|---|---|---|
| Matched volume | `KhoiLuongKhopLenh` | shares | `Volume` | shares | HIGH |
| Matched value | `GiaTriKhopLenh` | billion VND | `TotalValue` | VND | HIGH |
| Put-through volume | `KLThoaThuan` | shares | `AgreedVolume` | shares | HIGH |
| Put-through value | `GtThoaThuan` | billion VND | `AgreedValue` | VND | HIGH |

Tên raw `TotalValue` không được hiểu bằng field-name intuition. Cross-response agreement chứng minh nó là matched component trong path này:

| Local date | `GiaTriKhopLenh` | `TotalValue` | `GtThoaThuan` | `AgreedValue` |
|---|---:|---:|---:|---:|
| 2026-09-15 | 289.88 billion VND | 289,875,000,000 VND | 68.16 billion VND | 68,159,160,000 VND |
| 2026-09-14 | 352.47 billion VND | 352,466,950,000 VND | 131.04 billion VND | 131,037,600,000 VND |

CafeF inline client source tạo cột UI `Giá trị (tỷ VNĐ)` bằng:

```text
(item.TotalValue + item.AgreedValue) / 1_000_000_000
```

UI hiển thị 358.03 và 483.50 billion VND cho hai dates trên, khớp phép cộng raw components sau formatting. Đây là explicit source-owned inclusion rule, không phải DELTA tự cộng từ tên field.

Không có explicit raw `total_traded_value` field trong hai responses đã kiểm tra. Total là derived value theo public CafeF client mapping.

### 5.2 KBS current cross-check

KBS current board tách:

- `TT`: accumulated matched volume candidate;
- `TV`: current total/matched-value candidate theo client mapping;
- `PTQ`: put-through volume;
- `PTV`: put-through value.

FPT current sample có `TV=562,717,730,000 VND` và `PTV=1,528,800,000 VND`. Đây chỉ là current snapshot cross-check rằng components được tách; documented historical `data_day` không có các fields này. Không dùng KBS snapshot để chứng minh historical inclusion rule và không dùng KBS naming để ghi đè CafeF semantics.

### 5.3 Canonical recommendation

```text
COMPONENTS_PLUS_DERIVED_TOTAL
```

Recommended mapping từ CafeF `TradeHistoryNew.ashx`:

| Canonical/RAW concept | Source field(s) | Unit transform | Rule |
|---|---|---|---|
| `matched_volume` | `Volume` | none; shares | Giữ component riêng |
| `matched_value` | `TotalValue` | none; VND | Giữ component riêng; không để tên raw gây hiểu là all-in total |
| `put_through_volume` | `AgreedVolume` | none; shares | Giữ component riêng |
| `put_through_value` | `AgreedValue` | none; VND | Giữ component riêng |
| `traded_value` | `TotalValue + AgreedValue` | none; VND | Chỉ cộng trong cùng row/local trade date/provider scope |

Alternative `PriceHistory.ashx` mapping dùng `×1,000,000,000` cho hai value components vì endpoint đó trả billion VND. Không trộn rounded billion-VND components với raw-VND components khi raw precision có sẵn.

Không average. Không double-count `AgreedValue`. Không áp dụng rule CafeF cho provider khác. Nếu một component missing/null, không tự đổi thành zero trừ khi source row trả explicit numeric zero.

### 5.4 GAP-003 decision

```text
GAP-003 = RESOLVED
```

Canonical definition, source fields, unit transforms và inclusion rule đều explicit với `PUBLIC_RESPONSE + CLIENT_SOURCE + UI_LABEL + CROSS_CHECK`, confidence HIGH. Rights vẫn là blocker độc lập.

## 6. Evidence table

| ID | Evidence type | Public path | Bounded observation | Confidence |
|---|---|---|---|---|
| R-01 | PUBLIC_POLICY | `https://cafef.vn/robots.txt` | `Allow: /`; không phải data/automation license | HIGH |
| R-02 | PUBLIC_POLICY | `https://cafef.vn/static/chinh-sach-bao-mat.html` | Privacy/cookie policy; không cấp rights cần cho collection/storage/reuse | HIGH |
| R-03 | UI_LABEL | CafeF public data pages/footer | Data-for-reference disclaimer; không phải permission grant | HIGH |
| R-04 | PUBLIC_POLICY | `https://www.kbsec.com.vn/robots.txt` | Allow public paths, disallow login/admin/editor; không phải data license | HIGH |
| R-05 | PUBLIC_POLICY | Vnstock `license-2026.09` | Research software use/automation conditions; third-party data rights excluded | HIGH |
| R-06 | PUBLIC_DOC | Vnstock GitHub README | Guest/community/sponsor client quotas; provider terms remain separate | HIGH |
| C-01 | UI_LABEL | CafeF FPT company page | Current ref 72.70, ceiling 77.70, floor 67.70; nghìn VND/share | HIGH |
| C-02 | UI_LABEL | CafeF historical page | Table headers omit reference/ceiling/floor; matched/negotiated groups explicit | HIGH |
| C-03 | PUBLIC_RESPONSE | `PriceHistory.ashx`, FPT/VNM/PVS/ACV | Two normal days each; 12-field response has no limit-price fields | HIGH |
| C-04 | PUBLIC_RESPONSE | `PriceHistory.ashx`, FPT 2026-05-27..29 | Ex-right-adjacent bounded sample; same field set | HIGH |
| C-05 | PUBLIC_RESPONSE | UI-exposed `Type=EXPORT` request | Two-day XLSX, 12 headers; no limit-price fields; inspected in-memory only | HIGH |
| C-06 | CLIENT_SOURCE | CafeF FPT public company HTML | UI calls `TradeHistoryNew.ashx`; total display formula adds `TotalValue + AgreedValue` | HIGH |
| C-07 | PUBLIC_RESPONSE | `TradeHistoryNew.ashx`, FPT | Historical `BasicPrice/Ceiling/Floor` plus value components | HIGH |
| C-08 | PUBLIC_RESPONSE | `TradeHistoryNew.ashx`, VNM/PVS/ACV | Same field set across HOSE/HNX/UPCOM, two recent rows each | HIGH |
| C-09 | PUBLIC_RESPONSE | `TradeHistoryNew.ashx`, FPT page 3 | Historical rows around local 2026-05-28/29 contain direct limit fields | HIGH |
| C-10 | CROSS_CHECK | CafeF two public historical responses + UI | Rounded billion components match raw-VND components and UI derived total | HIGH |
| K-01 | PUBLIC_RESPONSE | KBS `/stocks/{symbol}/data_day` | Two rows × four symbols; keys only `t,o,h,l,c,v` | HIGH |
| K-02 | CLIENT_SOURCE | Vnstock KBS `quote.py`/`const.py` | Historical map only OHLCV; price-board map separately contains `RE/CL/FL` | HIGH |
| K-03 | PUBLIC_RESPONSE | KBS `POST /stock/iss` | Four current rows with `RE/CL/FL/TV/PTQ/PTV` | HIGH |

Request behavior:

- Requests were HTTPS, sequential and bounded; no login, cookie, auth header, token, proxy or fingerprint value was supplied or recorded.
- CafeF `PriceHistory.ashx`: JSON, date range + page parameters, newest-first; normal checks used two rows/symbol.
- CafeF `TradeHistoryNew.ashx`: JSON, symbol + page parameters, newest-first; two rows/symbol plus one 30-row UI-sized page to locate the known FPT adjacent date.
- KBS `data_day`: JSON, inclusive two-day range in the verified sample, newest-first.
- KBS current board: one public POST for four symbols.
- Không stress-test rate behavior; không gặp provider rate response trong bounded successful requests.

## 7. Remaining blockers

1. `GAP-001` remains OPEN: CafeF and KBS provider automation/data rights are `NOT_VERIFIED`.
2. Vnstock client permission does not grant KBS provider data rights.
3. `GAP-004 Financial PIT` remains outside this task and unchanged.
4. Other P1 gaps from `SOURCE_COMPARISON.md` remain unchanged.

`GAP-002` and `GAP-003` are resolved by new evidence, but the prior comparison/source notes were intentionally not edited in this bounded task.

## 8. Market SOURCE_SMOKE gate

| Requirement | Status | Reason |
|---|---|---|
| GAP-001 Rights | OPEN | No end-to-end path has sufficient public permission evidence |
| GAP-002 Historical ref/ceil/floor | RESOLVED | CafeF historical row fields verified across HOSE/HNX/UPCOM |
| GAP-003 Traded value | RESOLVED | CafeF component and inclusion rule verified |
| Existing OHLC/volume/price-basis/provenance evidence | VERIFIED_IN_SOURCE_COMPARISON | Không re-opened trong task này |

```text
Market SOURCE_SMOKE = NOT_READY
```

Chỉ market side được đánh giá. `GAP-004 Financial PIT` không nằm trong quyết định này. Một P0 còn OPEN là đủ để gate fail-closed.

## 9. Next action

`Resolve rights/policy blocker before any automated collection.`

