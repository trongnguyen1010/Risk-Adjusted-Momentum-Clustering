# DELTA P0 Rights and Acquisition Source Decision

## 1. Scope

Tài liệu này chỉ xử lý `GAP-001` cho market track: quyền acquisition, automation, local storage, tạo derived research dataset, academic/thesis use và internal reproducibility trước bounded adapter và real `SOURCE_SMOKE`.

Các semantics đã khóa và không được mở lại:

- `GAP-002 historical reference/ceiling/floor = RESOLVED`.
- `GAP-003 traded_value semantics = RESOLVED`.
- KBS qua Vnstock là technical path hiện tại cho adjusted daily OHLCV và VNINDEX.
- CafeF direct là technical path hiện tại cho historical reference/ceiling/floor và matched/put-through value components.

Task không crawl dataset, không gọi live market-data API của fallback candidates, không tạo account/API key, không đăng ký trial, không mua gói, không accept Terms, không implement adapter, không chạy `SOURCE_SMOKE` và không xử lý financial PIT.

Evidence date: **2026-09-16**.

Decision vocabulary cho rights:

- `ALLOWED`
- `ALLOWED_WITH_CONDITIONS`
- `RESTRICTED`
- `NOT_VERIFIED`
- `PROHIBITED`
- `BLOCKED_ACCESS`

`HTTP 200`, public endpoint, `robots.txt`, source-visible client code, README example, quota hoặc im lặng trong Terms không được dùng làm permission.

## 2. Existing baseline

| Path/layer | Baseline technical state | Rights baseline | Materially changed? |
|---|---|---|---|
| CafeF direct | Public pages và bounded UI-linked requests hoạt động | Automation/storage/research-data rights `NOT_VERIFIED` | NO |
| KBS provider | Public KBS responses hoạt động trong bounded checks | Provider automation/storage/research-data rights `NOT_VERIFIED` | NO |
| Vnstock client | Client hỗ trợ research và tự động gửi request theo tier/quota | Software rights có điều kiện; không cấp third-party provider-data rights | NO |
| TCBS qua VietFin | Deferred; live path từng gặp access challenge | `BLOCKED_ACCESS` | NO; không revisit |

Phase A chỉ re-check official/public policy paths. Không tìm thấy CafeF Terms/API/data-use grant hoặc KBS API/data-use grant mới làm thay đổi baseline. Search được dừng tại đây theo early decision rule; không tiếp tục “đọc Terms vô hạn”.

## 3. CafeF rights

Official/public evidence được giữ ở đúng phạm vi:

- [CafeF privacy policy](https://cafef.vn/static/chinh-sach-bao-mat.html): privacy/cookie notice, không phải data license.
- [CafeF robots.txt](https://cafef.vn/robots.txt): crawler-path signal, không phải grant cho automation/storage/reuse.
- Public data-page disclaimer: dữ liệu mang tính tham khảo và limitation of liability; không cấp data rights.
- Official-domain policy search ngày 2026-09-16 không locate được Terms of Use, API policy hoặc data-use license có explicit grant cho intended use.

| Use case | Status | Official policy/section summary | Evidence date | Confidence |
|---|---|---|---|---|
| Manual access | `NOT_VERIFIED` | Public browsing hoạt động; không có explicit data-use grant | 2026-09-16 | HIGH |
| Bounded automation | `NOT_VERIFIED` | `robots.txt: Allow` không phải automation/data license | 2026-09-16 | HIGH |
| Local raw storage | `NOT_VERIFIED` | Privacy policy không cấp quyền lưu market data | 2026-09-16 | HIGH |
| Derived research dataset | `NOT_VERIFIED` | Không tìm thấy official reuse/derivation grant | 2026-09-16 | HIGH |
| Academic/thesis use | `NOT_VERIFIED` | Không tìm thấy official research-use grant | 2026-09-16 | HIGH |
| Internal reproducibility | `NOT_VERIFIED` | Không có policy cho lưu immutable raw evidence/replay | 2026-09-16 | HIGH |
| Raw redistribution | `NOT_VERIFIED` | Không tìm thấy redistribution grant; use case này không bắt buộc cho DELTA | 2026-09-16 | HIGH |

CafeF conclusion:

```text
CafeF direct = INSUFFICIENT_RIGHTS_EVIDENCE
```

Public technical access và resolved field semantics không đủ để chọn `USE_CAFEF`.

## 4. KBS rights

Official/public evidence được giữ ở đúng phạm vi:

- [KBSV robots.txt](https://www.kbsec.com.vn/robots.txt): path/crawler signal, không phải data license.
- Official KBS/KBSV-domain search ngày 2026-09-16 không locate được public API terms, market-data license, research-data policy hoặc copyright/reuse terms cấp các intended rights.
- KBS data host accessibility không được dùng làm permission.

| Use case | Status | Official policy/section summary | Evidence date | Confidence |
|---|---|---|---|---|
| Manual access | `NOT_VERIFIED` | Public response hoạt động nhưng không có explicit provider-data grant | 2026-09-16 | HIGH |
| Bounded automation | `NOT_VERIFIED` | Không tìm thấy public API/data policy cho direct KBS path | 2026-09-16 | HIGH |
| Local raw storage | `NOT_VERIFIED` | Không có public storage grant | 2026-09-16 | HIGH |
| Derived research dataset | `NOT_VERIFIED` | Không có public reuse/derivation grant | 2026-09-16 | HIGH |
| Academic/thesis use | `NOT_VERIFIED` | Không có provider-data research grant | 2026-09-16 | HIGH |
| Internal reproducibility | `NOT_VERIFIED` | Không có permission cho raw evidence retention/replay | 2026-09-16 | HIGH |
| Raw redistribution | `NOT_VERIFIED` | Không có public redistribution grant; không bắt buộc cho DELTA | 2026-09-16 | HIGH |

KBS conclusion:

```text
KBS provider = INSUFFICIENT_RIGHTS_EVIDENCE
```

Không thể chọn `USE_KBS`, kể cả khi Vnstock client software được dùng hợp lệ.

## 5. Vnstock client conditions

[Vnstock license `license-2026.09`](https://vnstocks.com/onboard/giay-phep-su-dung) là official client-software policy và nêu rõ:

- Community software dành cho personal/learning/research.
- Client tự động gửi request từ hạ tầng người dùng tới third-party source.
- Usage phải tuân theo license/tier/quota; cấm né limit, multiple fake accounts và abnormal load.
- Research publication phải cite Vnstock.
- Software license không cấp quyền truy cập, sao chép, lưu, hiển thị, phân phối hoặc khai thác dữ liệu của provider.
- Người dùng phải tự xác minh provider terms.

[Vnstock disclaimer](https://vnstocks.com/onboard/mien-tru-trach-nhiem) lặp lại ranh giới này; [Vnstock operating principle](https://vnstocks.com/onboard/nguyen-ly-hoat-dong) nói rõ endpoint không cần login không tự tạo data license.

| Use case | Status | Official policy/section summary | Evidence date | Confidence |
|---|---|---|---|---|
| Manual client use | `ALLOWED_WITH_CONDITIONS` | Community software cho personal/learning/research, phải accept đúng license | 2026-09-16 | HIGH |
| Bounded automation | `RESTRICTED` | Client automation tồn tại nhưng chịu tier/quota, no-evasion/no-abnormal-load và provider terms | 2026-09-16 | HIGH |
| Local raw provider-data storage | `NOT_VERIFIED` | Vnstock expressly does not grant third-party data storage rights | 2026-09-16 | HIGH |
| Derived provider dataset | `NOT_VERIFIED` | Client license không chuyển giao provider-data reuse rights | 2026-09-16 | HIGH |
| Academic/thesis use | `ALLOWED_WITH_CONDITIONS` | Software research use được phép với citation; provider-data rights vẫn riêng | 2026-09-16 | HIGH |
| Internal reproducibility | `NOT_VERIFIED` | Software có thể chạy lại theo license, nhưng provider raw retention/replay chưa được grant | 2026-09-16 | HIGH |
| Raw provider-data redistribution | `NOT_VERIFIED` | Vnstock không sở hữu hoặc cấp redistribution right cho KBS data | 2026-09-16 | HIGH |

Vnstock là acquisition client, không phải rights-clearing intermediary. Client conditions không chữa được KBS provider layer.

## 6. Existing-path decision

Early decision result:

| Path | Rights sufficient for intended plan? | Selection outcome |
|---|---|---|
| CafeF direct | NO | Không được chọn `USE_CAFEF` |
| KBS via Vnstock | NO | Không được chọn `USE_KBS` |

Vì cả hai path đều thiếu explicit permission cho bounded automation + local raw storage + derived research dataset + academic/thesis use + internal reproducibility, fallback discovery là bắt buộc.

## 7. Fallback candidates

Bounded discovery dừng ở hai realistic candidates; không thêm scraping-only/unofficial sources.

### 7.1 Candidate A — FiinGroup API Datafeed

Official documentation:

- [API trading index](https://datafeed.fiingroup.vn/api-giao-dich) liệt kê separate HOSE, HNX và UPCoM stock/index APIs.
- [HOSE Stock V2](https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/hose-stock-v2) khai báo `/Market/GetHoseStockv2` và fields EOD/adjusted prices.
- [HNX Stock V2](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hnx-stock-v2) khai báo `/Market/GetHnxStockv2`.
- [HOSE Index](https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/hose-index) có `ComGroupCode=VNINDEX` và OHLC/index volume/value fields.
- [Corporate-action API example](https://datafeed.fiingroup.vn/api-doanh-nghiep/lich-su-kien/phat-hanh-co-phieu) có event dates, ratios/price và source URL.
- [FiinGroup API Datafeed contact](https://datafeed.fiingroup.vn/lien-he) yêu cầu liên hệ provider; không có self-serve/free plan hoặc public contract terms được locate.

| Criterion | Result |
|---|---|
| Provider | FiinGroup Vietnam |
| Access path/API | Commercial `API Datafeed`; documented REST-like endpoint families |
| Official / licensed | Official provider product; actual license/contract not obtained |
| Bounded automation allowed | `ALLOWED_WITH_CONDITIONS` only after contract/credentials; API product establishes intended machine access, not current permission |
| Local storage allowed | `NOT_VERIFIED` pending contract |
| Research/thesis use allowed | `NOT_VERIFIED`; brochure identifies researchers as customers but is not a license grant |
| Derived dataset allowed | `NOT_VERIFIED` pending contract |
| Internal reproducibility | `NOT_VERIFIED` pending contract |
| Raw redistribution allowed | `NOT_VERIFIED`; not required for DELTA |
| HOSE | YES — documented Stock V2 endpoint |
| HNX | YES — documented Stock V2 endpoint |
| UPCOM | YES — official API index lists UPCoM Stock V2 |
| VNINDEX | YES — documented HOSE Index endpoint |
| `>=5y` history | PARTIAL — current docs show 2020 EOD samples, older than five years at evidence date; contracted retention/depth not stated |
| OHLCV | YES |
| reference/ceiling/floor | YES — explicit fields |
| traded_value | YES — matched, put-through and total fields |
| trading_status | YES/PARTIAL — HOSE V2 documents suspension/halt/delist flags; cross-exchange consistency requires contract test |
| corporate actions | YES — dedicated corporate-action API families documented |
| authentication required | `ACCESS_REQUIRES_USER_ACTION`; account/contract/credentials not created |
| pricing/free tier | No public self-serve tier verified |
| cost category | `CONTACT_REQUIRED` |
| Exact FPT/VNM/PVS/ACV/VNINDEX smoke test | NOT_RUN; credentials required |
| Compatibility label | `FULL_REPLACEMENT` technically, if contract clears all intended rights and fields |
| Major limitations | No public license terms for storage/derived research/reproducibility; history depth and exact plan/SLA unknown |
| Confidence | HIGH for documented fields/coverage; LOW for unprovided contract rights |

Candidate A is the strongest technical shortlist, but is not currently rights-cleared.

### 7.2 Candidate B — Official exchange feeds (HOSE + HNX)

Official documentation:

- [HOSE information-service fee schedule](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406141/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf) identifies Market Data Feed and HOSE Index Feed; delivery note states Webservice data are provided by API.
- [HNX information-service introduction](https://www.upboard.hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html) offers listed/HNX and UPCoM data, online Message/XML delivery, automated EOD/disclosure delivery, historical-data products and a two-week free trial.
- [HNX registration workflow](https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html) requires application, fee schedule, contract negotiation/signature, then implementation.
- [HNX 2026 product/fee schedule](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf) lists EOD per-stock packages with reference/open/close/high/low, matched/put-through/total volume and value.

| Criterion | Result |
|---|---|
| Provider | HOSE + HNX official exchanges |
| Access path/API | HOSE Webservice/API; HNX Message/XML/InfoFile + historical-data packages |
| Official / licensed | YES, subject to separate exchange service contracts |
| Bounded automation allowed | `ALLOWED_WITH_CONDITIONS` after signed contract; machine/automatic delivery is an explicit product feature |
| Local storage allowed | `NOT_VERIFIED` until contract terms are reviewed |
| Research/thesis use allowed | `NOT_VERIFIED` until contract terms are reviewed |
| Derived dataset allowed | `NOT_VERIFIED` until contract terms are reviewed |
| Internal reproducibility | `NOT_VERIFIED` until contract terms are reviewed |
| Raw redistribution allowed | `NOT_VERIFIED`; likely contract-specific and not required for DELTA |
| HOSE | YES via HOSE service |
| HNX | YES via HNX service |
| UPCOM | YES via HNX service |
| VNINDEX | YES via HOSE Index Feed |
| `>=5y` history | UNKNOWN — HNX advertises historical-data products, but public pages do not state exact retained depth; HOSE depth also not established |
| OHLCV | YES/PARTIAL — HNX fields explicit; HOSE feed scope is official but exact public field catalog not fully inspected |
| reference/ceiling/floor | PARTIAL — HNX EOD schedule explicitly includes reference; public evidence for all three fields across both exchange feeds is incomplete |
| traded_value | YES/PARTIAL — HNX explicitly lists matched/put-through/total values; HOSE field-level public evidence incomplete |
| trading_status | PARTIAL — official feeds are authoritative candidates; exact per-date codebooks not reviewed |
| corporate actions | PARTIAL — HNX disclosure/rights information exists; full cross-exchange contract scope not verified |
| authentication required | `ACCESS_REQUIRES_USER_ACTION`; application and signed contracts required |
| pricing/free tier | Paid packages; HNX advertises two-week trial, but trial was not requested |
| cost category | `PAID` |
| Exact FPT/VNM/PVS/ACV/VNINDEX smoke test | NOT_RUN; contracts/connections required |
| Compatibility label | `HYBRID` official path across two exchange services |
| Major limitations | Two contracts/integrations; storage/research/derived rights and history depth absent from public pages |
| Confidence | HIGH for official service existence and HNX coverage; MEDIUM/LOW for unprovided contract rights and complete HOSE field set |

Candidate B is authoritative but operationally heavier and still not rights-cleared for DELTA without reviewing signed terms.

## 8. Candidate comparison

| Provider/path | Rights | Coverage | History | Cost category | Decision |
|---|---|---|---|---|---|
| FiinGroup API Datafeed | Machine access is contract-capable; storage/derived research/reproducibility `NOT_VERIFIED` | Strongest single-vendor coverage for HOSE/HNX/UPCoM/VNINDEX and required market fields | PARTIAL; 2020 samples, no contracted depth | `CONTACT_REQUIRED` | `SHORTLIST_PENDING_LICENSE` |
| HOSE + HNX official feeds | Automation explicit after contracts; other intended rights `NOT_VERIFIED` | Official combined coverage; field catalogs uneven in public evidence | UNKNOWN; historical products exist, depth unstated | `PAID` | `SHORTLIST_PENDING_CONTRACTS` |

No numeric score is assigned. Neither candidate is rejected technically; neither has enough public rights evidence to become the active acquisition plan today.

## 9. Selected acquisition plan

```text
NO_RIGHTS_CLEARED_PLAN_SELECTED
```

Current domain state:

| Domain | Provider | Client/API | Rights status | Role |
|---|---|---|---|---|
| OHLCV | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |
| reference/ceiling/floor | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |
| traded_value | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |
| VNINDEX | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |

Preferred next licensing target is FiinGroup API Datafeed because it is the only bounded-search candidate with one documented API family covering all exchanges, VNINDEX and the required market fields. This is a shortlist priority, not selection or permission.

Before it can become `USE_LICENSED_SOURCE`, written terms must explicitly cover:

1. Bounded automated API requests for FPT/VNM/PVS/ACV/VNINDEX.
2. Local immutable raw-response storage and hashes.
3. Creation/storage of a derived research dataset.
4. Academic/thesis analysis and publication of derived results.
5. Internal reproducibility/replay by the project team.
6. At least five years of daily history for HOSE/HNX/UPCoM and VNINDEX.
7. Required fields, units, adjustment basis and API quota for the intended smoke.
8. No raw redistribution requirement; DELTA can keep raw data private.

If FiinGroup cannot grant these terms, the next target is the official HOSE+HNX contracted `HYBRID` path with the same written-rights checklist.

## 10. Market SOURCE_SMOKE readiness

| Requirement | Status | Reason |
|---|---|---|
| At least one legitimate acquisition plan | BLOCKED | No current path has all intended rights |
| Rights sufficient for every source in plan | BLOCKED | No plan selected |
| Required semantics | READY_IN_EXISTING_EVIDENCE | GAP-002 and GAP-003 resolved; KBS/CafeF semantics remain evidence only, not authorized acquisition paths |
| Exact symbol API access | `ACCESS_REQUIRES_USER_ACTION` | Fallback candidates require contract/account/credentials |

```text
Market adapter gate = NOT_READY
SOURCE_SMOKE = NOT_RUN
```

`READY_FOR_ADAPTER` is not granted. No API account, trial, key or subscription was created.

## 11. Adapter work packages

```text
NONE — NOT_READY
```

Không tạo active WP giả khi chưa có rights-cleared provider. Sau khi user obtains và project reviews a license, một task khác mới được phép tạo WP dựa trên exact licensed plan, field catalog, auth method và quotas.

## 12. Residual risks

1. Contract may forbid or constrain local raw storage even when API calls are allowed.
2. “Research customer” or trial availability is marketing/access evidence, not a research-data license.
3. Derived dataset and internal reproducibility rights may differ from raw redistribution rights.
4. FiinGroup history samples from 2020 do not prove the purchased plan exposes the full retained history.
5. Official-exchange path requires two integrations/contracts and may have different field/code conventions.
6. Adjustment basis, timestamp behavior and quota must be re-verified on the licensed path; existing CafeF/KBS mappings cannot be silently transferred.
7. Financial `GAP-004` remains separate and unchanged.

## 13. Final decision

```text
REPLACEMENT_SOURCE_REQUIRED
```

```text
GAP-001 = OPEN
Market adapter gate = NOT_READY
SOURCE_SMOKE = NOT_RUN
```

Reason: CafeF/KBS remain insufficient and no fallback candidate exposes public terms granting the complete intended rights set. The required replacement is a licensed API/data-service plan with written permission for bounded automation, local immutable storage, derived research dataset creation, thesis use and internal reproducibility, plus documented five-year Vietnam market coverage. FiinGroup API Datafeed is the first licensing target; HOSE+HNX official feeds are the second.

## 14. Evidence appendix

| ID | Source URL | Official section/wording summary | Evidence date | Confidence |
|---|---|---|---|---|
| R-CF-1 | `https://cafef.vn/static/chinh-sach-bao-mat.html` | Privacy/cookie policy; no market-data automation/storage/reuse grant | 2026-09-16 | HIGH |
| R-CF-2 | `https://cafef.vn/robots.txt` | Allows paths for crawlers; not a data license | 2026-09-16 | HIGH |
| R-KBS-1 | `https://www.kbsec.com.vn/robots.txt` | Path signal only; no market-data rights grant | 2026-09-16 | HIGH |
| R-VNS-1 | `https://vnstocks.com/onboard/giay-phep-su-dung` | Sections I–III: software research scope, automation nature, tier/quota restrictions, no third-party data rights | 2026-09-16 | HIGH |
| R-VNS-2 | `https://vnstocks.com/onboard/mien-tru-trach-nhiem` | Provider data rights remain with provider; client license does not grant access/copy/storage/display/distribution | 2026-09-16 | HIGH |
| R-VNS-3 | `https://vnstocks.com/onboard/nguyen-ly-hoat-dong` | Public/no-login endpoint is not a license; client does not bypass source controls | 2026-09-16 | HIGH |
| F-FG-1 | `https://datafeed.fiingroup.vn/api-giao-dich` | Official API index lists HOSE/HNX/UPCoM stock and index families | 2026-09-16 | HIGH |
| F-FG-2 | `https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/hose-stock-v2` | HOSE EOD schema: OHLC, reference/ceiling/floor, matched/deal/total volume/value, status and adjusted prices | 2026-09-16 | HIGH |
| F-FG-3 | `https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hnx-stock-v2` | HNX EOD schema with same core market concepts | 2026-09-16 | HIGH |
| F-FG-4 | `https://datafeed.fiingroup.vn/api-giao-dich/co-phieu/co-phieu/hose-index` | VNINDEX/HOSE index level, OHLC, volume/value fields | 2026-09-16 | HIGH |
| F-FG-5 | `https://datafeed.fiingroup.vn/api-doanh-nghiep/lich-su-kien/phat-hanh-co-phieu` | Corporate-action endpoint with dates/terms/source metadata | 2026-09-16 | HIGH |
| F-FG-6 | `https://datafeed.fiingroup.vn/lien-he` | Contact-only route; no public self-serve plan/contract terms located | 2026-09-16 | HIGH |
| F-HOSE-1 | `https://staticfile.hsx.vn/Uploads/UploadDocuments/2406141/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf` | Paid Market Data Feed/HOSE Index Feed; Webservice delivery by API | 2026-09-16 | HIGH |
| F-HNX-1 | `https://www.upboard.hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-sgtc.html` | HNX/HNX-listed/UPCoM automatic and historical data products; two-week trial | 2026-09-16 | HIGH |
| F-HNX-2 | `https://hnx.vn/vi-vn/dich-vu-cctt/huong-dan-yeu-cau-ky-thuat-shdk.html` | Application → fee schedule/model contract → agreement/signature → implementation | 2026-09-16 | HIGH |
| F-HNX-3 | `https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf` | 2026 EOD packages include per-stock prices and matched/put-through/total values | 2026-09-16 | HIGH |

Search boundary notes:

- Official provider/exchange/API/policy pages only were used for conclusions.
- Search engine was used only to locate official pages.
- No blog, forum, Reddit, random dump, GitHub dataset, mirror or anonymous API was used.
- No login, API key, payment, registration, trial request, sales contact or Terms acceptance occurred.
- No old-date market-data request was made because fallback APIs require user action; history was assessed only from official documentation.
