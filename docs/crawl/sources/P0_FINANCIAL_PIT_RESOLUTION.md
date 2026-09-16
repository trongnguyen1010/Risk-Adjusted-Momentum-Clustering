# DELTA P0 Financial PIT Resolution

## 1. Scope

Tài liệu này chỉ xử lý `GAP-004 Financial PIT`: xác định liệu CafeF direct hoặc KBS qua Vnstock có cung cấp timing đủ an toàn để xây dựng báo cáo tài chính point-in-time (PIT) cho DELTA hay không.

Phạm vi kiểm chứng được giới hạn ở sáu report observations:

1. FPT Q1/2026.
2. FPT Q2/2026.
3. FPT Q4/2025, dùng thay Q3/2025 vì path KBS đã ghi nhận pagination bất thường ở Q3.
4. FPT FY2025.
5. VNM Q2/2026.
6. VNM Q1/2026, là quý liền kề.

Không crawl lịch sử, không kiểm tra symbol khác, không sửa source note cũ, không giải quyết `GAP-001`, không chạy `SOURCE_SMOKE` và không triển khai adapter.

Ngày kiểm chứng: **2026-09-16** (`Asia/Saigon`).

## 2. PIT definitions used by DELTA

| Khái niệm | Định nghĩa làm việc | Quy tắc fail-closed |
|---|---|---|
| `period_start`, `period_end` | Ranh giới kỳ kinh tế mà fact đo lường | Không thay bằng ngày lập/công bố báo cáo |
| `report_date` | Ngày gắn với bản báo cáo theo metadata của provider | Không mặc định là ngày công bố hoặc first-public |
| `published_at` | Thời điểm nguồn/đơn vị công bố tuyên bố rõ | Cần label/docs hoặc UI-response agreement |
| `available_at` | Thời điểm sớm nhất có bằng chứng rằng đúng report/version đã công khai cho người dùng | Không được lấy `fetched_at`, upload token hoặc provider-created time để thay thế nếu chưa chứng minh |
| `created_at` | Thời điểm provider tạo record nội bộ | Chỉ giữ raw metadata nếu nguồn không định nghĩa |
| `updated_at` | Thời điểm provider cập nhật record | Không tự coi là revision/restatement hoặc publication time |
| `revision` | Version có identity và chronology đủ để biết bản nào thay/sửa bản nào | Không overwrite bản raw cũ khi quan hệ supersession chưa rõ |
| `fetched_at` | Thời điểm DELTA quan sát response | Chỉ là observation time/upper bound; **never** là `available_at` |

Một path chỉ PIT-capable khi có đồng thời report identity dùng được, period bounds, publication/availability rule, timezone handling và revision safety. Việc một timestamp có thứ tự hợp lý không tự chứng minh ngữ nghĩa của timestamp đó.

## 3. Sample reports

Các giá trị KBS dưới đây là raw response từ `Head[]`; timestamp ISO đều không có UTC offset. CafeF chỉ đối chiếu document row hợp nhất phù hợp với symbol/kỳ, không coi filename token là thời điểm công bố đã xác minh.

| # | Report observation | KBS period/scope/audit | KBS `ReportDate` | KBS `DatePubDepartment` | KBS `CreatedDate` | KBS `LastUpdate` | CafeF document evidence |
|---:|---|---|---|---|---|---|---|
| 1 | FPT Q1/2026 | `202601..202603`, `HN`, `CKT` | `2026-04-21T00:00:00` | `2026-04-28T00:00:00` | `2026-04-28T14:36:58.677` | `2026-05-05T09:00:36.48` | Consolidated Q1 row; document id `69f07307d02b4661764f99bf`; filename starts `20260424_...` |
| 2 | FPT Q2/2026 | `202604..202606`, `HN`, `CKT` | `2026-07-21T00:00:00` | `2026-07-28T00:00:00` | `2026-07-28T09:40:14.127` | `2026-07-31T23:00:17.6` | Initial consolidated row id `6a6819e6015b429ee29cd16b`, filename token `28072026095429`; a separate reviewed consolidated row id `6a8946580763ddca1c4addbb`, token `22082026134854` |
| 3 | FPT Q4/2025 | `202510..202512`, `HN`, `CKT` | `2026-01-23T00:00:00` | `2026-01-27T00:00:00` | `2026-01-27T14:54:53.62` | `2026-03-06T11:38:14.393` | Consolidated Q4 row id `69782530dd24a1ce9f55a5bd`; filename starts `20260126_...` |
| 4 | FPT FY2025 | `202501..202512`, `HN`, `KT` | `2026-03-18T00:00:00` | `2026-03-20T00:00:00` | `2026-03-20T15:35:57.453` | `2026-03-23T23:00:03.453` | Audited consolidated annual row id `69bd0630b51797afb2ee4752`; filename starts `20260319_...` |
| 5 | VNM Q2/2026 | `202604..202606`, `HN`, `SX` | `2026-07-30T00:00:00` | `2026-07-31T00:00:00` | `2026-08-01T09:40:01.36` | `2026-08-04T23:00:04.14` | Reviewed consolidated Q2 row id `6a6c4a2c015b429ee29cd7df`; filename contains source-date token `20260730` và upload-like token `31072026140931` |
| 6 | VNM Q1/2026 | `202601..202603`, `HN`, `SX` | `2026-04-29T00:00:00` | `2026-05-04T00:00:00` | `2026-05-04T16:28:00.14` | `2026-05-07T23:00:05.26` | Reviewed consolidated Q1 row id `69f8036afd4848eba8a89c6a`; filename starts `20260429_...` |

Quan sát chronology chỉ cho thấy các field thường tăng theo thứ tự `ReportDate` → `DatePubDepartment`/`CreatedDate` → `LastUpdate`. Thứ tự lặp lại này là bằng chứng về pattern, không phải định nghĩa first-public.

## 4. CafeF timing evidence

### 4.1 Timestamp candidates

| CafeF field/label | Giá trị quan sát | Phân loại | Canonical readiness | Confidence | Lý do |
|---|---|---|---|---|---|
| UI column `Thời gian cập nhật` + response `Time` | `Q1/2026`, `Q2/2026`, `CN/2025` | `DOCUMENT_METADATA_ONLY` | Không map timestamp | HIGH | Giá trị là period label, không phải ngày/giờ dù column header nói “cập nhật” |
| Response `Year`, `Quarter` | `2026`, `2`; annual dùng `Quarter=5` | `DOCUMENT_METADATA_ONLY` | Có thể giữ làm document-period metadata | HIGH | Explicit response values, nhưng không phải timing công bố |
| Date/time-like token trong PDF filename/path | Ví dụ `28072026095429`, `22082026134854` | `UPLOAD_TIMESTAMP_ONLY` | Không map `published_at`/`available_at` | LOW | Không có label/docs định nghĩa; token có thể phản ánh upload hoặc file naming convention |
| Date-like prefix trong filename | Ví dụ `20260424`, `20260319` | `DOCUMENT_METADATA_ONLY` | Không map | LOW | Có thể là document date, exchange filing date hoặc upload date; nguồn không định nghĩa |
| Query parameter `v` trên CDN URL | Số dài | `UNKNOWN` | Không map | LOW | Không có bằng chứng đây là timestamp, version hay cache key |
| Response `id` | Chuỗi hex-like khác nhau theo document row | `DOCUMENT_METADATA_ONLY` | Giữ raw làm `provider_document_id` candidate | MEDIUM | Dùng được để phân biệt row quan sát; không có stability/version contract |
| HTTP/UI fetch time | Thời điểm kiểm chứng | Observation metadata | Chỉ `fetched_at` | HIGH | Là thời điểm DELTA quan sát, không phải first-public |

Không có CafeF field nào đạt `PUBLISHED_AT_VERIFIED`. Filename token chỉ đạt `UPLOAD_TIMESTAMP_ONLY`; bản thân upload time cũng không chứng minh thời điểm công khai đầu tiên.

### 4.2 First-public analysis

Public UI tải danh sách qua:

```text
GET /du-lieu/Ajax/PageNew/FileBCTC.ashx
    ?Symbol={symbol}
    &Type=1
    &Year={year}
```

Response trả document rows với `id`, `Type`, `Quarter`, `Year`, `Time`, `Name`, `IconFile`, `Link`. Nó không trả explicit `published_at`, `available_at`, upload time, revision number hoặc `supersedes_id`.

Cross-source chronology không chữa được thiếu định nghĩa. Ví dụ:

- FPT Q2 initial consolidated document có filename token `28/07/2026 09:54:29` trong khi KBS `DatePubDepartment` là `2026-07-28` và `CreatedDate` là `2026-07-28 09:40:14.127`.
- VNM Q2 document có upload-like token `31/07/2026 14:09:31`; KBS `DatePubDepartment` là `2026-07-31`, nhưng KBS `CreatedDate` là `2026-08-01 09:40:01.36`.
- FPT Q1/FY và VNM Q1 có date-like filename prefixes sớm hơn KBS candidate dates.

Các chênh lệch cho thấy provider ingestion timing khác nhau và filename có ích cho audit, nhưng không xác định nguồn nào là first-public. Không có observation liên tục tại thời điểm phát hành, source label rõ nghĩa hoặc tài liệu CafeF xác nhận public availability time.

Kết luận first-public CafeF: **không xác minh được**.

### 4.3 Report identity

CafeF document list phân biệt được:

- symbol;
- year/quarter;
- statement scope qua `Name` (`công ty mẹ`, `hợp nhất`);
- audit/review state khi tên tài liệu ghi rõ;
- từng document row qua `id` và `Link`.

FPT Q2/2026 có cả initial documents và separate reviewed documents. Đây là bằng chứng rằng nhiều document versions/states có thể cùng tồn tại cho một kỳ. Tuy nhiên:

1. Không có explicit revision number hoặc supersession relation.
2. `id` chưa có stability contract.
3. Financial summary/fact response CafeF không expose document id để nối một fact row với đúng PDF/version.
4. Không có first-seen/publication timestamp cho từng document row.

Vì vậy identity ở document layer đủ để lưu raw document observations, nhưng chưa đủ cho canonical fact-version identity.

### 4.4 CafeF PIT conclusion

```text
CafeF PIT = NOT_READY
```

CafeF có document-level evidence hữu ích và cho thấy chronology nhiều trạng thái của cùng kỳ. Tuy nhiên không có verified publication/availability timestamp, không có timezone, và không có join chắc chắn giữa document version với financial facts. CafeF không cung cấp canonical `available_at` an toàn trong evidence hiện có.

## 5. KBS via Vnstock timing evidence

### 5.1 Timestamp candidates

| KBS field | Observed shape | Phân loại | Canonical readiness | Confidence |
|---|---|---|---|---|
| `ReportDate` | ISO-like date at `00:00:00`, no offset | `REPORT_METADATA_ONLY` | Không map `published_at`/`available_at` | MEDIUM |
| `DatePubDepartment` | ISO-like date at `00:00:00`, no offset | `PUBLISHED_AT_CANDIDATE` | Raw candidate only | MEDIUM |
| `CreatedDate` | ISO-like datetime with fractional seconds, no offset | `PROVIDER_RECORD_METADATA_ONLY` | Raw `provider_created_at` only | HIGH cho classification, LOW cho business meaning |
| `LastUpdate` | ISO-like datetime with fractional seconds, no offset | `PROVIDER_UPDATE_ONLY` | Raw `provider_updated_at` only | MEDIUM |
| Request observation time | Client clock | Observation metadata | `fetched_at` only | HIGH |

Không field nào được nâng thành `available_at`.

### 5.2 DatePubDepartment

`DatePubDepartment` là `PUBLISHED_AT_CANDIDATE`, không phải `PUBLISHED_AT_VERIFIED`:

- Tên field gợi ý ngày một department công bố.
- Sáu observations có chronology hợp lý so với `ReportDate`.
- Một số dates gần date/upload-like tokens của CafeF.

Nhưng evidence chưa trả lời được:

- department nào công bố;
- công bố nội bộ, công bố lên KBS hay công bố chính thức ra thị trường;
- date có phải lần công bố đầu tiên hay không;
- `00:00:00` là actual time hay date coerced thành midnight;
- timezone nào áp dụng;
- field có thay đổi khi report được sửa hay không.

Do đó không map `DatePubDepartment` trực tiếp thành canonical `published_at` hoặc `available_at`.

### 5.3 CreatedDate

`CreatedDate` được phân loại `PROVIDER_RECORD_METADATA_ONLY`. Pattern `CreatedDate >= DatePubDepartment` trong các samples phù hợp với provider ingestion/record creation, nhưng không chứng minh public availability. FPT Q2 còn cho thấy `CreatedDate` của KBS sớm hơn upload-like token CafeF cùng ngày; VNM Q2 thì `CreatedDate` KBS muộn hơn CafeF token một ngày. Vì acquisition paths có ingestion clock khác nhau, `CreatedDate` không thể làm market-wide first-public timestamp.

Không map `CreatedDate` thành canonical `available_at`.

### 5.4 LastUpdate / revision behavior

`LastUpdate` luôn sau `CreatedDate` trong sáu observations, nhưng response chỉ trả current row:

- Không có revision id/version number.
- Không có prior `LastUpdate` values hoặc immutable version history.
- Không có reason code cho sửa dữ liệu.
- Không biết update chỉ là provider ETL refresh, sửa metadata hay financial restatement.
- Không có `supersedes_id` hoặc changed-fields payload.

FPT Q2 cho thấy hạn chế thực tế: CafeF có separate reviewed document ngày 22/08/2026, trong khi current KBS income-statement row vẫn là `AuditedStatus=CKT` với `LastUpdate=2026-07-31T23:00:17.6`. Không thể suy KBS row hiện tại đại diện latest reviewed version trên toàn thị trường.

Vì vậy `LastUpdate` là `PROVIDER_UPDATE_ONLY`, không phải revision chronology đã xác minh. Có thể giữ nó làm raw metadata và deduplication aid, nhưng không dùng để overwrite hoặc label restatement.

### 5.5 Report identity

Observed `Head.ID` không phải stable report id độc lập: giá trị `1` lặp lại cho FPT Q2, FPT Q4, FPT annual, VNM Q2 và các response page-1 khác. `CompanyID` phân biệt company nhưng chưa đủ phân biệt report/version.

Raw storage có thể tạo observation key nội bộ từ:

```text
provider=kbs
company_id
statement_type
year_period
term_code
period_begin
period_end
united
audited_status
report_date
provider_created_date
response_hash
```

Đây là DELTA raw observation identity, không phải provider report id và không được trình bày như canonical revision id.

### 5.6 KBS PIT conclusion

```text
KBS PIT = NOT_READY
```

KBS là path mạnh hơn về period boundaries, scope và audit metadata. Tuy nhiên `DatePubDepartment` mới là publication candidate; `CreatedDate` là provider-record metadata; `LastUpdate` không có revision semantics; tất cả timestamps đều thiếu offset/timezone. KBS chưa cung cấp canonical `available_at` an toàn.

## 6. Cross-source comparison

| Criterion | CafeF direct | KBS via Vnstock | PIT consequence |
|---|---|---|---|
| Report/period labels | Year/quarter ở document layer | `YearPeriod`, `TermCode`, `PeriodBegin`, `PeriodEnd` | KBS mạnh hơn cho period identity |
| Scope/audit | Trong document name, có initial/reviewed rows | Explicit `United`, `AuditedStatus` | KBS dễ normalize hơn; CafeF hữu ích để audit versions |
| Publication candidate | Filename/path tokens only | `DatePubDepartment` | Không path nào verified first-public |
| Provider-created time | Không explicit | `CreatedDate` | KBS metadata only; không phải availability |
| Provider-update time | Không explicit | `LastUpdate` | Không đủ revision chronology |
| Version evidence | Multiple documents cùng kỳ | Chỉ current row trong bounded response | CafeF cho thấy plurality; cả hai thiếu supersession chain |
| Fact-to-document join | Không tìm thấy stable join | Facts nằm trong cùng response với `Head`, nhưng report id không stable | Không thể tạo cross-provider canonical version chain |
| Timezone | Không explicit | ISO timestamps không offset | Không được gán UTC hoặc `Asia/Ho_Chi_Minh` |
| Earliest public availability | Không xác minh | Không xác minh | Canonical `available_at` phải để null/unmapped |

Không chọn timestamp sớm nhất giữa hai provider. Provider ingestion clocks khác nhau; min/max arithmetic không tạo ra first-public evidence.

## 7. Timezone handling

- CafeF UI/document tokens không khai báo timezone: `LOCAL_DISPLAY_TIMEZONE_UNVERIFIED`.
- KBS ISO-like timestamps không có offset: `NAIVE_TIMESTAMP`.
- `DatePubDepartment` và `ReportDate` có `00:00:00`; đây có thể chỉ là date serialized thành datetime, nên không coi midnight là actual public time.
- Raw layer phải giữ nguyên string và field name, không append `Z`, không tự gán UTC, không tự gán `Asia/Ho_Chi_Minh`.
- Nếu parser cần typed value, lưu `local_datetime_naive` hoặc `date` cùng `timezone_status`, đồng thời giữ raw string.
- `fetched_at` do DELTA tạo phải dùng UTC có offset, nhưng vẫn chỉ là observation time.

## 8. Revision-safe storage recommendation

Cho đến khi PIT được giải quyết, ingestion tài chính nếu được phép ở task sau phải append-only ở raw layer:

1. Lưu `provider`, `acquisition_client`, endpoint/method, non-secret params, symbol và statement type.
2. Lưu nguyên `Head[]`, document row và fact payload; không chỉ normalized values.
3. Ghi `fetched_at` UTC, response/document hash và raw field strings.
4. Giữ `provider_document_id`, `CompanyID`, raw `ID`, `ReportDate`, `DatePubDepartment`, `CreatedDate`, `LastUpdate`, `United`, `AuditedStatus` mà không đổi nhãn ngữ nghĩa.
5. Mỗi response hash mới tạo một observation/version nội bộ; không overwrite bản cũ chỉ vì composite period trùng nhau.
6. Nếu content không đổi nhưng fetch lặp lại, deduplicate payload bytes nhưng vẫn có thể ghi observation manifest riêng.
7. Không gắn fact CafeF summary với PDF chỉ bằng symbol/quarter nếu không có stable join.
8. Không phát sinh canonical `available_at`; để null và đánh dấu `PIT_UNRESOLVED`.

Khuyến nghị này bảo vệ chronology raw nhưng không biến source thành PIT-capable.

## 9. Canonical PIT recommendation

```text
RAW_ONLY_NO_CANONICAL_PIT
```

Canonical timing rule:

- `period_start`/`period_end`: KBS explicit month bounds có thể được giữ cho đúng observed report row.
- `report_date`: giữ raw KBS candidate, không đổi thành publication time.
- `published_at`: **unmapped** cho cả CafeF và KBS.
- `available_at`: **unmapped/null** cho cả CafeF và KBS.
- `created_at`/`updated_at`: chỉ provider raw metadata.
- `revision`: chỉ internal observation/version based on immutable payload hash; không gọi là provider restatement.
- `fetched_at`: UTC observation time, không thay thế `available_at`.

Q2/Q3 duration/timing rule:

- FPT và VNM Q2 income-statement observations có explicit `PeriodBegin=YYYY04`, `PeriodEnd=YYYY06`; đây là direct evidence cho standalone Q2 period boundaries của các rows đó.
- FPT Q1/VNM Q1 có `YYYY01..YYYY03`; FPT Q4 fallback có `202510..202512`; FY2025 có `202501..202512`.
- KBS Q3 không được thêm request trong task này do giới hạn sáu samples và pagination issue đã biết. Q3 remains: **UNKNOWN — DO NOT MAP YET**.
- CafeF quarter document labels không tự chứng minh standalone-vs-YTD fact semantics.
- Publication timing của Q2 và mọi quarter vẫn unresolved dù period boundaries rõ.

## 10. GAP-004 decision

```text
GAP-004 = OPEN
```

Lý do: không acquisition path nào đáp ứng đủ năm điều kiện PIT. KBS có report identity composite và period bounds hữu ích nhưng thiếu verified availability rule, timezone và revision chain. CafeF có document-version evidence nhưng thiếu first-public timestamp và stable fact-to-document join. Mapping bất kỳ candidate nào thành `available_at` lúc này có thể gây look-ahead bias.

Financial PIT gate:

```text
NOT_READY
```

`GAP-001 Rights` là blocker riêng và không bị thay đổi bởi quyết định này.

## 11. Remaining blockers

1. Cần provider documentation hoặc UI/response evidence xác nhận nghĩa chính xác của KBS `DatePubDepartment`.
2. Cần biết timezone và liệu midnight values là date-only hay actual timestamp.
3. Cần chứng minh earliest public availability cho đúng report/version, không chỉ provider ingestion time.
4. Cần stable report/version identity hoặc explicit supersession/revision chain.
5. Cần join rõ giữa CafeF financial facts và document version.
6. Cần xác minh Q3 duration facts nếu Q3 là smoke path dự kiến; hiện tại **UNKNOWN — DO NOT MAP YET**.
7. `GAP-001 Rights` vẫn OPEN độc lập trước mọi automated collection.

## 12. Next action

`Keep financial data RAW-only until a PIT-capable source is approved.`

Nếu tiếp tục discovery, chỉ nên làm targeted verification với provider/source documentation hoặc một disclosure path có explicit publication timestamp, timezone và immutable report identity. Không mở rộng thành lịch sử hoặc adapter implementation.

## 13. Evidence appendix

### 13.1 Public request inventory

| ID | Public/login state | Method | Host/path | Important non-secret params | Content type | Behavior observed |
|---|---|---|---|---|---|---|
| C-UI-1 | Public, no login | GET | `cafef.vn/du-lieu/hose/fpt-tai-lieu.chn` | symbol encoded in path | HTML | UI header `Thời gian cập nhật`; inline JS exposes document request and rendering |
| C-UI-2 | Public, no login | GET | `cafef.vn/du-lieu/hose/vnm-tai-lieu.chn` | symbol encoded in path | HTML | Same public document UI structure |
| C-DOC-1 | Public, no login | GET | `cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx` | `Symbol=fpt`, `Type=1`, `Year=2026` | JSON-shaped response | Q2 then Q1; multiple scope/review rows; no pagination token observed |
| C-DOC-2 | Public, no login | GET | same | `Symbol=fpt`, `Type=1`, `Year=2025` | JSON-shaped response | Annual, Q4, Q3, Q2, Q1 order; no explicit publication timestamp |
| C-DOC-3 | Public, no login | GET | same | `Symbol=vnm`, `Type=1`, `Year=2026` | JSON-shaped response | Q2 then Q1; no explicit publication timestamp |
| K-FIN-1 | Public response, no auth supplied | GET | `kbbuddywts.kbsec.com.vn/iis-server/investment/stock/finance-info/{symbol}` | `type=KQKD`, `termtype=1/2`, `page`, `pageSize=1`, `unit=1000`, `languageid=1` | JSON | Six exact report observations; one row/request; current metadata only |

Date-range behavior không áp dụng cho các request này. KBS page number chọn current period rows; CafeF year filter trả toàn bộ document rows trong năm. Không probe maximum page size/rate limit. Requests nhỏ, tuần tự, không gặp login/CAPTCHA/rate challenge; điều này không cấp automation/data rights.

### 13.2 Evidence classification

| Claim | Evidence | Confidence |
|---|---|---|
| CafeF `Time` là period label, không phải update timestamp | UI header + response values `Q1/2026`, `Q2/2026`, `CN/2025` + renderer uses `item.Time` | HIGH |
| CafeF filename contains timing-like tokens | Public document response `Link` values | HIGH cho sự tồn tại; LOW cho semantics |
| CafeF có multiple Q2 document states | Initial and reviewed document rows for FPT Q2/2026 | HIGH |
| KBS period bounds/scope/audit present | Six public `Head[]` observations | HIGH |
| `DatePubDepartment` is publication candidate only | Field name + repeated chronology; no definition/timezone | MEDIUM |
| `CreatedDate` is provider-record metadata | Repeated relation to other fields; no first-public definition | HIGH cho classification |
| `LastUpdate` is provider-update only | Always later in samples, but no version chain/reason | MEDIUM |
| No safe canonical `available_at` | Neither path has first-public rule + timezone + revision identity | HIGH |

### 13.3 Access and rights boundary

Mọi request đều dùng public pages/paths đã được UI hoặc project evidence ghi nhận; không dùng cookie riêng, token, auth header, session id, proxy hoặc kỹ thuật né hạn chế. Không download bulk history hoặc PDF contents. Trạng thái rights không được tái đánh giá trong task này: `GAP-001` giữ nguyên `OPEN`.
