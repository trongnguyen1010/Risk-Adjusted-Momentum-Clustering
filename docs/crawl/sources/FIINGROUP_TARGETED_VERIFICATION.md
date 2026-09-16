# DELTA FiinGroup Targeted Verification

## 1. Scope

Tài liệu này chỉ thực hiện targeted verification cho **FiinGroup API Datafeed** nhằm đánh giá access, rights, coverage và khả năng thay thế market-data source của DELTA M1. Phạm vi không bao gồm tạo account/API key, chấp nhận Terms, liên hệ sales, gọi authenticated API, crawl lịch sử, chạy `SOURCE_SMOKE` hay implement adapter.

Ngày kiểm tra evidence: **2026-09-16**. Chỉ official FiinGroup/API Datafeed pages và official FiinGroup documents được dùng. Search engine chỉ được dùng để locate các nguồn chính thức.

## 2. Existing project context

Các kết luận project đã khóa và không được mở lại trong task này:

- `GAP-002 historical reference/ceiling/floor = RESOLVED`.
- `GAP-003 traded_value semantics = RESOLVED`.
- CafeF rights và KBS rights chưa đủ evidence.
- Current acquisition outcome là `REPLACEMENT_SOURCE_REQUIRED`.
- FiinGroup đang là `SHORTLIST_PENDING_LICENSE`, chưa phải approved source.

Mục tiêu còn lại của `GAP-001` là tìm một acquisition path có written permission cho bounded automation, local immutable raw storage, derived research dataset, thesis use và internal reproducibility, đồng thời đáp ứng market coverage tối thiểu của DELTA.

## 3. Official product / API family

Official product page mô tả API Datafeed có Price Feed, Corporate Reference Data, Corporate Financials và Corporate Actions; brochure mô tả Cloud API/data delivery vào hệ thống hoặc database của khách hàng. Đây là evidence rằng FiinGroup cung cấp một machine-oriented data product, không phải là evidence rằng mọi intended use của DELTA đã được cấp quyền. Evidence: `FG-01`, `FG-02`; confidence `HIGH`.

Các endpoint families liên quan trực tiếp đến market gate:

| Domain | Official API family | Public schema evidence | Kết luận |
|---|---|---|---|
| HOSE stocks | `/Market/GetHoseStockv2` | HOSE Stock V2: EOD, raw/adjusted prices, volume/value và status flags | `VERIFIED` (`FG-04`, `HIGH`) |
| HNX stocks | `/Market/GetHnxStockv2` | HNX Stock V2: EOD, raw/adjusted prices, volume/value và status candidates | `VERIFIED` (`FG-05`, `HIGH`) |
| UPCOM stocks | `/Market/GetUpcomStockv2` | UPCoM Stock V2: EOD, raw/adjusted prices, volume/value và status candidates | `VERIFIED` (`FG-06`, `HIGH`) |
| VNINDEX | `/Market/GetHoseIndex` với `ComGroupCode=VNINDEX` | Index date, OHLC, matched/deal/total volume và value | `VERIFIED` (`FG-07`, `HIGH`) |
| Corporate actions | `/CorporateAction/GetEvent` và các event-specific families | Event type/title, dates, value/ratio và source-reference candidates | `PARTIAL` (`FG-09`, `HIGH` cho schema; `MEDIUM` cho cross-event consistency) |

Public documentation exposes schema pages and examples, nhưng không công bố request authentication flow, quota, purchased-plan entitlements hoặc production base URL/credential lifecycle đủ để triển khai an toàn. Những phần này cần contract/onboarding package.

## 4. Rights and license

Official API/product materials cho thấy API integration là intended product use. Tuy nhiên, chúng không phải data license cho DELTA. FiinGroup website Terms chỉ cấp limited website access cho personal purposes và yêu cầu prior written consent đối với copying/transmission/distribution của website content; Terms đó không mô tả quyền reuse của contracted API payloads. Vì vậy không được suy quyền storage/research từ product marketing. Evidence: `FG-01`, `FG-02`, `FG-03`; confidence `HIGH`.

| Use case | Status | Evidence |
|---|---|---|
| Manual/API access | `CONTRACT_DEPENDENT` | Public docs có thể đọc, nhưng live data entitlement và permitted API use không được public terms cấp (`FG-01`, `FG-03`; `HIGH`) |
| Automated API requests | `CONTRACT_DEPENDENT` | API là machine-oriented product, nhưng automation scope/quota phải nằm trong written contract (`FG-01`, `FG-02`; `HIGH`) |
| Local raw response storage | `CONTRACT_DEPENDENT` | Brochure minh họa delivery vào client system/database nhưng không phải explicit storage grant cho DELTA (`FG-02`; `MEDIUM`) |
| Immutable raw archival/hash | `CONTRACT_DEPENDENT` | Không tìm thấy public clause cho retention, immutable snapshots hoặc hashes (`FG-03`; `HIGH`) |
| Derived research dataset | `CONTRACT_DEPENDENT` | Không tìm thấy public clause cho transformation/derived dataset (`FG-03`; `HIGH`) |
| Academic/thesis analysis | `CONTRACT_DEPENDENT` | Product page nhắc research houses như customer group, nhưng không cấp academic-use right (`FG-01`; `HIGH`) |
| Publication of derived results | `CONTRACT_DEPENDENT` | Không có public clause phân biệt derived results với raw content (`FG-03`; `HIGH`) |
| Internal reproducibility/replay | `CONTRACT_DEPENDENT` | Không có public clause cho replay hoặc retention sau khi subscription kết thúc (`FG-03`; `HIGH`) |
| Raw redistribution | `RESTRICTED` | Website Terms yêu cầu prior written consent cho copying/transmission/distribution; exact API-data restriction vẫn phải ghi trong contract. DELTA không cần redistribute raw data (`FG-03`; `HIGH` cho website content, `MEDIUM` cho API applicability) |

Rights conclusion: official public materials mở ra một **contract-capable path**, nhưng không đủ để approve acquisition. Tất cả rights quan trọng phải được FiinGroup xác nhận bằng văn bản cho exact plan.

## 5. Market coverage

| Market/index | Status | Endpoint/product family | Documented scope | History capability | Authentication requirement |
|---|---|---|---|---|---|
| HOSE | `VERIFIED` | `/Market/GetHoseStockv2` | EOD OHLC, reference/ceiling/floor, matched/deal/total volume/value, raw/adjusted prices, flags | `PLAN_DEPENDENT` | Exact mechanism `NOT_VERIFIED`; access/onboarding requires user action |
| HNX | `VERIFIED` | `/Market/GetHnxStockv2` | EOD OHLC, reference/ceiling/floor, matched/deal/total volume/value, raw/adjusted prices, status candidates | `PLAN_DEPENDENT` | Exact mechanism `NOT_VERIFIED`; access/onboarding requires user action |
| UPCOM | `VERIFIED` | `/Market/GetUpcomStockv2` | EOD OHLC, reference/ceiling/floor, matched/deal/total volume/value, raw/adjusted prices, status candidates | `PLAN_DEPENDENT` | Exact mechanism `NOT_VERIFIED`; access/onboarding requires user action |
| VNINDEX | `VERIFIED` | `/Market/GetHoseIndex`, `ComGroupCode=VNINDEX` | Date, open/high/low/close, reference index, matched/deal/total volume/value | `PLAN_DEPENDENT` | Exact mechanism `NOT_VERIFIED`; access/onboarding requires user action |

Sources: `FG-04`–`FG-07`; evidence date 2026-09-16; confidence `HIGH` cho endpoint/schema existence, `LOW` cho unprovided plan/auth details.

## 6. Required field coverage

`DOCUMENTED` ở bảng dưới chỉ xác nhận field và label tồn tại trong official schema. Nó không tự động xác nhận purchased-plan entitlement, unit/multiplier, null behavior hoặc canonical mapping.

| DELTA field/domain | Official field(s) | Status | Mapping note | Evidence / confidence |
|---|---|---|---|---|
| `trade_date` | `TradingDate` | `DOCUMENTED` | Datetime label là trading date; timezone chưa public | `FG-04`–`FG-07`; `HIGH` |
| `open` | `OpenPrice`; index `OpenIndex` | `DOCUMENTED` | Raw price candidate; unit/multiplier cần data dictionary | `FG-04`–`FG-07`; `HIGH` |
| `high` | `HighestPrice`; index `HighestIndex` | `DOCUMENTED` | Raw price candidate | `FG-04`–`FG-07`; `HIGH` |
| `low` | `LowestPrice`; index `LowestIndex` | `DOCUMENTED` | Raw price candidate | `FG-04`–`FG-07`; `HIGH` |
| `close` | `ClosePrice`; index `CloseIndex` | `DOCUMENTED` | Raw price candidate | `FG-04`–`FG-07`; `HIGH` |
| `volume` | `TotalVolume` | `DOCUMENTED` | Official label là total volume; share unit chưa được explicit public schema định nghĩa | `FG-04`–`FG-07`; `HIGH` field, `LOW` unit |
| `reference_price` | `ReferencePrice` | `DOCUMENTED` | Raw reference candidate | `FG-04`–`FG-06`; `HIGH` |
| `ceiling_price` | `CeilingPrice` | `DOCUMENTED` | Raw ceiling candidate | `FG-04`–`FG-06`; `HIGH` |
| `floor_price` | `FloorPrice` | `DOCUMENTED` | Raw floor candidate | `FG-04`–`FG-06`; `HIGH` |
| `trading_status` | HOSE: `Suspension`, `Delist`, `HaltResumeFlag`; HNX/UPCOM: `SecurityTradingStatus`, `ListingStatus`; record `Status` | `PARTIAL` | HOSE flag labels/codes rõ hơn; cross-exchange status codebook và distinction giữa security status với record status chưa đủ | `FG-04`–`FG-06`; `MEDIUM` |
| `matched_volume` | `TotalMatchVolume` | `DOCUMENTED` | Không dùng `MatchVolume`, vì field đó là latest match | `FG-04`–`FG-07`; `HIGH` |
| `matched_value` | `TotalMatchValue` | `DOCUMENTED` | Total order-matching value | `FG-04`–`FG-07`; `HIGH` |
| `put_through_volume` | `TotalDealVolume` | `DOCUMENTED` | Total put-through volume | `FG-04`–`FG-07`; `HIGH` |
| `put_through_value` | `TotalDealValue` | `DOCUMENTED` | Total put-through value | `FG-04`–`FG-07`; `HIGH` |
| `total_traded_value` | `TotalValue` | `DOCUMENTED` | Official label là total value; VND unit/multiplier cần written data dictionary | `FG-04`–`FG-07`; `HIGH` field, `LOW` unit |
| VNINDEX date/OHLC | `TradingDate`, `OpenIndex`, `HighestIndex`, `LowestIndex`, `CloseIndex` | `DOCUMENTED` | `ComGroupCode=VNINDEX` example | `FG-07`; `HIGH` |
| VNINDEX volume/value | `TotalVolume`, `TotalValue` cùng matched/deal components | `DOCUMENTED` | Exact plan and unit confirmation vẫn cần | `FG-07`; `HIGH` field, `LOW` unit |

Field conclusion:

- OHLCV: `DOCUMENTED`.
- `reference/ceiling/floor`: `DOCUMENTED`.
- matched/put-through fields: `DOCUMENTED`.
- `total_traded_value`: `DOCUMENTED`.
- `trading_status`: `PARTIAL` vì cross-exchange codebook chưa hoàn chỉnh.
- Price/volume/value units và multiplier: chưa đủ evidence để map canonical; phải yêu cầu exact data dictionary/sample under contract.

## 7. Historical depth

**Status: `PLAN_DEPENDENT`.**

Official schema examples có records ngày 2020-03-17, chứng minh documentation dùng historical-looking EOD records nhưng **không** chứng minh exact retained depth hoặc purchased plan sẽ trả về ít nhất năm năm dữ liệu. Official product materials nói packages linh hoạt và có thể customize API; không công bố start date, retention window hay per-plan history entitlement. Evidence: `FG-02`, `FG-04`–`FG-07`; confidence `HIGH` cho sample dates, `LOW` cho exact depth.

Do đó:

- Không gắn `VERIFIED_GE_5Y`.
- Không dùng sample 2020 như proof của contract coverage.
- Exact earliest date cho HOSE/HNX/UPCOM/VNINDEX và quota cho `>=300 symbols × >=5y` phải được ghi trong quote/contract hoặc plan specification.

## 8. Price adjustment basis

**Kết luận: `BOTH_AVAILABLE`.**

Stock V2 schemas công bố đồng thời raw fields (`ReferencePrice`, `OpenPrice`, `ClosePrice`, `HighestPrice`, `LowestPrice`) và adjusted fields (`ReferencePriceAdjusted`, `OpenPriceAdjusted`, `ClosePriceAdjusted`, `HighestPriceAdjusted`, `LowestPriceAdjusted`, `RateAdjusted`). Endpoint `/Market/GetAdjustedRatio` còn công bố `AdjustedDate`, `RateAdjusted` và `IsReverse`. Evidence: `FG-04`–`FG-06`, `FG-08`; confidence `HIGH`.

Giới hạn quan trọng: public docs gọi đây là “adjusted price/adjusting rate” nhưng không định nghĩa đầy đủ event coverage, backward/forward convention, split-only hay total-return methodology. Vì vậy có thể xác nhận **raw và vendor-adjusted series cùng tồn tại**, nhưng chưa được gọi vendor adjustment là split-adjusted hoặc total-return. Canonical adjustment basis cần data dictionary/contract clarification trước adapter mapping.

## 9. Corporate actions

`/CorporateAction/GetEvent` document các candidates sau:

| Required concept | Official candidate | Status | Limitation |
|---|---|---|---|
| Event type | `EventListCode`, `EventTitle` | `DOCUMENTED` | Full codebook/plan entitlement chưa public |
| Announcement/publication date | `PublicDate` | `DOCUMENTED` | — |
| Ex-right date | `ExrightDate` | `DOCUMENTED` | — |
| Record date | `RecordDate` | `DOCUMENTED` | — |
| Payment/effective date | `IssueDate`, `BalanceFixingDate`; payment date có trong event description example | `PARTIAL` | Không có một generic dedicated `PaymentDate` với semantics đồng nhất cho mọi event |
| Cash amount / ratio / rights terms | `Value`, `Ratio`, `ExecutionRate`, event description | `PARTIAL` | Unit và interpretation phụ thuộc event code |
| Source document/reference | `AttachFile`, `SourceUrl` | `DOCUMENTED` | Sample có thể rỗng; availability theo event chưa được test |

Overall corporate-actions status: `PARTIAL`. Evidence: `FG-09`; confidence `HIGH` cho field labels, `MEDIUM` cho cross-event semantics. Đây là optional domain cho first market smoke, nhưng một known event vẫn phải được verified sau khi licensed access tồn tại.

## 10. Authentication / onboarding / pricing

| Item | Result | Evidence / confidence |
|---|---|---|
| Account required? | `NOT_VERIFIED`; user action cần thiết để provider xác nhận onboarding model | Public docs không nêu self-service account flow (`FG-01`; `HIGH`) |
| API key/token? | `NOT_VERIFIED` | Public schema không công bố auth method hoặc credential lifecycle (`FG-04`–`FG-07`; `HIGH`) |
| Contract required? | `CONTRACT_DEPENDENT` | Rights cần thiết không có trong public terms; written order/contract phải được review (`FG-03`; `HIGH`) |
| Sales/contact required? | `YES` | Official product page dùng “Request for Services” form/contact path thay vì self-service activation (`FG-01`; `HIGH`) |
| Trial? | `UNKNOWN` | Không tìm thấy official public API Datafeed trial entitlement |
| Free tier? | `UNKNOWN` | Không tìm thấy official public free tier |
| Paid? | `UNKNOWN` | Không có public price/plan table; không suy giá từ commercial positioning |
| Cost category | `CONTACT_REQUIRED` | Exact plan, quote, quota và contract chỉ có thể lấy qua provider contact (`FG-01`; `HIGH`) |

Không account, key, trial, subscription hoặc payment nào được tạo; không form nào được submit.

## 11. Replacement capability

**Current mode: `INSUFFICIENT`.**

FiinGroup có một technical path duy nhất document HOSE, HNX, UPCOM, VNINDEX, OHLCV, reference/ceiling/floor và traded-value components. Vì vậy, nếu exact plan xác nhận `>=5y`, units/status codebooks/quota và written rights, candidate có thể được reclassified thành `FULL_REPLACEMENT` cho KBS + CafeF market path.

Tuy nhiên, rule của task chỉ cho `FULL_REPLACEMENT` khi `>=5y capability` đã documented. Public evidence hiện chỉ đạt `PLAN_DEPENDENT`, đồng thời rights chưa approved. Vì vậy không được gọi `FULL_REPLACEMENT` trong task này; `REPLACE_KBS_ONLY`, `REPLACE_CAFEF_ONLY` và `HYBRID_REQUIRED` cũng không có evidence phù hợp.

## 12. SOURCE_SMOKE suitability

**Status: `NOT_READY`.**

Không chạy smoke. Dù endpoint/field coverage mạnh, remaining blockers không chỉ là credentials:

1. Exact `>=5y` history entitlement chưa được documented.
2. Automation, raw storage, derived dataset, thesis use và replay rights chưa có written approval.
3. Unit/multiplier và cross-exchange `trading_status` codebook chưa đủ để canonical mapping không bị corruption.
4. Exact auth, quota và plan coverage chưa biết.

Sau written approval và data dictionary/sample review, một task riêng mới được phép đánh giá lại `READY_AFTER_ACCESS`.

## 13. Contract questions requiring user action

1. DELTA có được gọi API tự động cho mục đích thesis/research không?
2. Có được lưu raw API responses locally không?
3. Có được giữ immutable raw snapshots + hashes cho reproducibility không?
4. Có được tạo derived research dataset/features không?
5. Có được dùng derived results trong thesis/report/demo không?
6. Có được giữ dữ liệu nội bộ sau khi subscription kết thúc để reproducibility không?
7. Có cấm raw redistribution không? DELTA có thể cam kết không redistribute raw data.
8. Plan nào cover HOSE/HNX/UPCOM/VNINDEX?
9. History depth chính xác bao nhiêu năm và earliest available date của từng market/index là ngày nào?
10. Plan có OHLCV + reference/ceiling/floor + matched/put-through + total traded value + trading status không; unit/multiplier và codebook là gì?
11. Raw và adjusted prices có cả hai không; adjustment methodology và event coverage là gì?
12. Quota, pagination/batch limits và rate limits cho khoảng `>=300 symbols × >=5y` là gì?
13. Corporate-action history, source documents và event codebook có nằm trong plan không?
14. Có academic/research pricing không?

## 14. Final decision

**Decision: `SUITABLE_IF_CONTRACT_APPROVED`.**

FiinGroup API Datafeed technically phù hợp nhất trong shortlisted path vì official schemas cover cả ba markets, VNINDEX và phần lớn required fields trong một product family. Nhưng public materials không cấp rights cho DELTA và không document exact five-year entitlement, units/status codebooks, auth/quota hoặc price. Chỉ được chuyển sang approved source khi written contract/order form trả lời đầy đủ checklist trên và project review xác nhận không có restriction làm hỏng raw archival, derived research hoặc reproducibility.

**GAP-001 impact:** `YES` — FiinGroup có thể resolve `GAP-001` sau written approval, với điều kiện approval xác nhận toàn bộ intended rights, `>=5y` coverage, exact fields/units/status semantics và quota. Chưa có approval đó ở thời điểm hiện tại.

## 15. Evidence appendix

| ID | Official source | Page/section used | Evidence date | Confidence |
|---|---|---|---|---|
| `FG-01` | [FiinGroup API Datafeed product page](https://dff.fiingroup.vn/ApiDataFeed?lang=vi-vn) | Product scope, integration positioning, “Request for Services” contact path | 2026-09-16 | `HIGH` |
| `FG-02` | [FiinGroup API Datafeed brochure](https://fiingroup.vn/upload/docs/FiinGroup_API_Datafeed.pdf) | Cloud API/client database delivery model, flexible data packages, market/corporate data scope | 2026-09-16 | `HIGH` for product description; `LOW` as a rights grant |
| `FG-03` | [FiinGroup Terms and Conditions](https://fiingroup.vn/en/terms-and-conditions.html) | §§2, 4, 5: website purpose, content ownership, limited website license and prior written consent restrictions | 2026-09-16 | `HIGH` for website terms; `LOW` for unprovided API-contract terms |
| `FG-04` | [HOSE Stock V2](https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/hose-stock-v2) | `/Market/GetHoseStockv2`; EOD raw/adjusted prices, matched/deal/total values, status flags | 2026-09-16 | `HIGH` |
| `FG-05` | [HNX Stock V2](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hnx-stock-v2) | `/Market/GetHnxStockv2`; EOD raw/adjusted prices, volume/value, status candidates | 2026-09-16 | `HIGH` |
| `FG-06` | [UPCoM Stock V2](https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/upcom-stock-v2) | `/Market/GetUpcomStockv2`; EOD raw/adjusted prices, volume/value, status candidates | 2026-09-16 | `HIGH` |
| `FG-07` | [HOSE Index](https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/hose-index) | `/Market/GetHoseIndex`; `VNINDEX`, date/OHLC and matched/deal/total volume/value | 2026-09-16 | `HIGH` |
| `FG-08` | [Tỷ lệ điều chỉnh giá](https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/ty-le-dieu-chinh-gia) | `/Market/GetAdjustedRatio`; adjusted date/rate/reversal candidate | 2026-09-16 | `HIGH` for fields; `LOW` for complete methodology |
| `FG-09` | [Sự kiện doanh nghiệp](https://datafeed.fiingroup.vn/api-doanh-nghiep/lich-su-kien/su-kien) | `/CorporateAction/GetEvent`; event type/title, public/record/ex-right/execution dates, ratio/value and source candidates | 2026-09-16 | `HIGH` for schema; `MEDIUM` for cross-event semantics |

Không có conflict giữa các official pages đã dùng. Public product/marketing materials và public website Terms không resolve API contract rights; đây là thiếu contract evidence, không phải permission. Không provider khác được kiểm tra trong task này.
