# CafeF Primary C1 Crawl Plan

## Execution status

```yaml
stage: C1-PREP — Five-Worker CafeF Crawl Planning
result: COMPLETED / USER_MANUAL_REVIEW_REQUIRED
plan_id: cafef-c1-prep-v1
priority_policy: CAFEF_ACQUISITION_PRIORITY_V1
pilot_security_count: 71
worker_count: 5
collection_end_date: 2026-09-23
earliest_possible_experiment_date: 2011-09-23
history_policy: FULL_AVAILABLE_UP_TO_MAX_15Y
actual_market_data_requests: 0
actual_crawl_executed: NO
canonical_mutations: 0
feature_rebuild: NO
next_allowed_action: USER MANUAL REVIEW OF C1 CRAWL PLAN
after_explicit_user_approval_only: C1 — Representative CafeF Raw-Market Acquisition
```

C0 đã được người dùng phê duyệt. C1-PREP chỉ đóng băng universe, priority, history,
partition, request, resume, failure và merge contract cho C1. Không worker nào đã chạy.

## 1. Mục tiêu và ranh giới

C1 là representative pilot để kiểm tra:

- CafeF OHLC có ổn định như provider-observed raw market prices hay không;
- history acquisition tối đa 15 năm có complete và resumable hay không;
- pagination/range iteration có deterministic hay không;
- identity interval, exchange transfer và provider history boundary có được giữ đúng;
- raw artifact, checksum, provenance và failure behavior có audit được hay không;
- corporate-action windows có đủ evidence để đánh giá raw semantics ở C2 hay không.

C1-PREP không crawl, không gọi CafeF, không build canonical/research price/adjustment
factor/feature, không EDA và không merge worker output. C1 không phải full current-500;
scale-up vẫn thuộc C4 sau các gate C2, C3 và manual review.

```text
ACQUISITION PRIORITY != RESEARCH ELIGIBILITY
```

Priority chỉ quyết định thứ tự crawl. Nó không thay đổi clustering eligibility,
research readiness, model selection hoặc portfolio selection.

## 2. Offline evidence và input chưa có

Plan dùng duy nhất:

- current 500 universe và KBS current identity metadata;
- representative pilot 55 mã với listing date/sector đã được review;
- CafeF contract/deep-discovery evidence đã lưu cho FPT, VNM, VCB, PVS, ACV, HND,
  KHP;
- A1–A6 missing-session, price-basis và identity-transfer evidence;
- CafeF adapter/contract hiện có về `PriceHistory`, page size và ordering.

Không có artifact offline đủ để xác minh liquidity persistence, active trading
frequency, index membership, market cap/size hoặc một popularity series chung cho toàn
candidate universe. Các cột này ghi `SIGNAL_UNAVAILABLE`; plan không thay bằng zero,
không suy từ tên doanh nghiệp và không gọi web/API để lấp chỗ trống.

Do đó việc chứng minh pilot có đúng các band `very liquid` và
`medium/lower-liquidity`, cũng như index/size representation, được ghi rõ:

```text
PLAN_INPUT_UNRESOLVED
```

Pilot vẫn giữ nhiều project-important names và các sparse/problematic edge cases đã có
evidence, nhưng không gắn liquidity label khi thiếu metric.

```text
POPULARITY_SIGNAL_NOT_AVAILABLE
```

Representative-pilot membership và existing project evidence được dùng như
`OFFLINE_PROJECT_IMPORTANCE_PROXY`, không được trình bày như index membership hoặc
market cap.

## 3. CAFEF_ACQUISITION_PRIORITY_V1

Weights ban đầu và cách xử lý offline:

| Component | Original weight | C1-PREP status | Rule |
|---|---:|---|---|
| Liquidity / traded-value persistence | 30% | `SIGNAL_UNAVAILABLE` | Excluded globally |
| Active trading frequency | 20% | `SIGNAL_UNAVAILABLE` | Excluded globally |
| Index / market importance | 15% | Partial | 100 cho prior representative pilot; 80 cho A5 CafeF evidence-only item; otherwise unavailable |
| Size / market-cap proxy | 10% | `SIGNAL_UNAVAILABLE` | Excluded globally |
| Exchange acquisition preference | 10% | Available | HOSE 100, HNX 60, UPCOM 20 |
| Identity / source confidence | 10% | Available | reviewed listing/transfer 100; current-universe provisional 60; unresolved 0 |
| Strategic relevance / known coverage problem | 5% | Partial | known CafeF/missing/basis/transfer edge 100; prior pilot 60; otherwise unavailable |

Ba component unavailable globally bị loại. Bốn component còn lại giữ tỷ trọng tương đối
15:10:10:5 và được re-normalize trên 40 điểm. Row thiếu evidence cho một partial
component nhận không có evidence credit, đồng thời giữ label `SIGNAL_UNAVAILABLE`; đây
không phải negative quality score.

Threshold deterministic:

- `HIGH`: score `>=75`;
- `MEDIUM`: score `>=60` và `<75`;
- `NORMAL`: score `<60`.

Tie-break: score giảm dần, sau đó `security_id`, ticker tăng dần. Edge-case tag không
thay đổi tier. Mọi row ghi `research_eligibility_effect=NONE_ACQUISITION_ORDER_ONLY`.

### Exchange policy

HOSE/HNX chỉ có operational acquisition preference. Exchange component giữ original
weight 10%; nó không là research-quality rule. UPCOM không bị loại hoặc ép xuống cuối:
ACV, MPC, OIL, QNS, SAS, VEA và VGI đều vào `HIGH` nhờ offline project evidence; các
UPCOM edge cases vẫn vào pilot bằng tag riêng dù score là `NORMAL`.

## 4. Candidate universe và pilot selection

Candidate universe là union deterministic của:

- 500 current securities;
- 55 prior representative-pilot securities;
- VCB từ A5 CafeF evidence, với security identity còn unresolved.

Sau dedup theo ticker, candidate universe có 527 rows. Pilot chọn toàn bộ 55 prior
representative names và mọi current evidence-backed CafeF/missing/basis/transfer edge
case. Kết quả 71 securities, nằm trong envelope 50–75 và là tập nhỏ nhất giữ đủ
representation theo evidence hiện có.

Phân bố:

| Dimension | Count |
|---|---:|
| HIGH | 56 |
| MEDIUM | 5 |
| NORMAL | 10 |
| HOSE | 48 |
| HNX | 9 |
| UPCOM | 14 |

### Exact selected pilot universe

| # | Ticker | Exchange | Tier | Wave | Worker | Est. requests | History boundary | Edge |
|---:|---|---|---|---:|---|---:|---|---|
| 1 | BCM | HOSE | HIGH | 1 | worker_04 | 112 | IDENTITY_BOUNDARY | YES |
| 2 | CTR | HOSE | HIGH | 1 | worker_02 | 117 | IDENTITY_BOUNDARY | YES |
| 3 | FPT | HOSE | HIGH | 1 | worker_02 | 196 | MAX_15Y_BOUNDARY | YES |
| 4 | VNM | HOSE | HIGH | 1 | worker_04 | 196 | MAX_15Y_BOUNDARY | YES |
| 5 | ANV | HOSE | HIGH | 1 | worker_03 | 196 | MAX_15Y_BOUNDARY | NO |
| 6 | BVH | HOSE | HIGH | 1 | worker_04 | 196 | MAX_15Y_BOUNDARY | NO |
| 7 | CII | HOSE | HIGH | 1 | worker_01 | 196 | MAX_15Y_BOUNDARY | NO |
| 8 | DCM | HOSE | HIGH | 1 | worker_03 | 150 | LISTING_BOUNDARY | NO |
| 9 | DGC | HOSE | HIGH | 1 | worker_01 | 158 | LISTING_BOUNDARY | NO |
| 10 | DGW | HOSE | HIGH | 1 | worker_02 | 146 | LISTING_BOUNDARY | NO |
| 11 | FRT | HOSE | HIGH | 1 | worker_01 | 110 | LISTING_BOUNDARY | NO |
| 12 | GAS | HOSE | HIGH | 1 | worker_03 | 187 | LISTING_BOUNDARY | NO |
| 13 | GMD | HOSE | HIGH | 1 | worker_05 | 196 | MAX_15Y_BOUNDARY | NO |
| 14 | HCM | HOSE | HIGH | 1 | worker_02 | 196 | MAX_15Y_BOUNDARY | NO |
| 15 | KDH | HOSE | HIGH | 1 | worker_03 | 196 | MAX_15Y_BOUNDARY | NO |
| 16 | MBB | HOSE | HIGH | 1 | worker_05 | 195 | LISTING_BOUNDARY | NO |
| 17 | MWG | HOSE | HIGH | 1 | worker_01 | 159 | LISTING_BOUNDARY | NO |
| 18 | PLX | HOSE | HIGH | 1 | worker_01 | 123 | LISTING_BOUNDARY | NO |
| 19 | PNJ | HOSE | HIGH | 1 | worker_04 | 196 | MAX_15Y_BOUNDARY | NO |
| 20 | VHC | HOSE | HIGH | 1 | worker_01 | 196 | MAX_15Y_BOUNDARY | NO |
| 21 | CTG | HOSE | HIGH | 1 | worker_05 | 196 | MAX_15Y_BOUNDARY | NO |
| 22 | BID | HOSE | HIGH | 1 | worker_04 | 165 | LISTING_BOUNDARY | NO |
| 23 | DHG | HOSE | HIGH | 1 | worker_03 | 196 | MAX_15Y_BOUNDARY | NO |
| 24 | DPM | HOSE | HIGH | 1 | worker_04 | 196 | MAX_15Y_BOUNDARY | NO |
| 25 | BMP | HOSE | HIGH | 1 | worker_01 | 196 | MAX_15Y_BOUNDARY | NO |
| 26 | GEX | HOSE | HIGH | 1 | worker_04 | 143 | LISTING_BOUNDARY | NO |
| 27 | GVR | HOSE | HIGH | 1 | worker_02 | 111 | LISTING_BOUNDARY | NO |
| 28 | HAH | HOSE | HIGH | 1 | worker_04 | 151 | LISTING_BOUNDARY | NO |
| 29 | HDB | HOSE | HIGH | 1 | worker_05 | 114 | LISTING_BOUNDARY | NO |
| 30 | HPG | HOSE | HIGH | 1 | worker_05 | 196 | MAX_15Y_BOUNDARY | NO |
| 31 | IMP | HOSE | HIGH | 1 | worker_02 | 196 | MAX_15Y_BOUNDARY | NO |
| 32 | MSN | HOSE | HIGH | 1 | worker_03 | 196 | MAX_15Y_BOUNDARY | NO |
| 33 | NT2 | HOSE | HIGH | 1 | worker_04 | 196 | MAX_15Y_BOUNDARY | NO |
| 34 | POW | HOSE | HIGH | 1 | worker_03 | 112 | LISTING_BOUNDARY | NO |
| 35 | PVD | HOSE | HIGH | 1 | worker_01 | 196 | MAX_15Y_BOUNDARY | NO |
| 36 | REE | HOSE | HIGH | 1 | worker_05 | 196 | MAX_15Y_BOUNDARY | NO |
| 37 | SSI | HOSE | HIGH | 1 | worker_02 | 196 | MAX_15Y_BOUNDARY | NO |
| 38 | AAA | HOSE | HIGH | 1 | worker_05 | 129 | LISTING_BOUNDARY | NO |
| 39 | ACB | HOSE | HIGH | 1 | worker_04 | 196 | MAX_15Y_BOUNDARY | NO |
| 40 | CMG | HOSE | HIGH | 1 | worker_01 | 196 | MAX_15Y_BOUNDARY | NO |
| 41 | PVS | HNX | HIGH | 1 | worker_03 | 196 | MAX_15Y_BOUNDARY | YES |
| 42 | IDC | HNX | HIGH | 1 | worker_03 | 116 | LISTING_BOUNDARY | NO |
| 43 | NTP | HNX | HIGH | 1 | worker_05 | 196 | MAX_15Y_BOUNDARY | NO |
| 44 | PVI | HNX | HIGH | 1 | worker_05 | 196 | MAX_15Y_BOUNDARY | NO |
| 45 | VCS | HNX | HIGH | 1 | worker_02 | 196 | MAX_15Y_BOUNDARY | NO |
| 46 | BCC | HNX | HIGH | 1 | worker_02 | 196 | MAX_15Y_BOUNDARY | NO |
| 47 | LAS | HNX | HIGH | 1 | worker_02 | 190 | LISTING_BOUNDARY | NO |
| 48 | TNG | HNX | HIGH | 1 | worker_03 | 196 | MAX_15Y_BOUNDARY | NO |
| 49 | KHP | HOSE | HIGH | 1 | worker_01 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 50 | ACV | UPCOM | HIGH | 1 | worker_01 | 129 | LISTING_BOUNDARY | YES |
| 51 | MPC | UPCOM | HIGH | 1 | worker_02 | 117 | LISTING_BOUNDARY | NO |
| 52 | OIL | UPCOM | HIGH | 1 | worker_05 | 112 | LISTING_BOUNDARY | NO |
| 53 | QNS | UPCOM | HIGH | 1 | worker_03 | 128 | LISTING_BOUNDARY | NO |
| 54 | VEA | UPCOM | HIGH | 1 | worker_04 | 108 | LISTING_BOUNDARY | NO |
| 55 | VGI | UPCOM | HIGH | 1 | worker_04 | 105 | LISTING_BOUNDARY | NO |
| 56 | SAS | UPCOM | HIGH | 1 | worker_05 | 149 | LISTING_BOUNDARY | NO |
| 57 | VCB | HOSE | MEDIUM | 2 | worker_01 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 58 | LPB | HOSE | MEDIUM | 2 | worker_04 | 118 | IDENTITY_BOUNDARY | YES |
| 59 | SHB | HOSE | MEDIUM | 2 | worker_02 | 196 | MAX_15Y_BOUNDARY | YES |
| 60 | VCG | HOSE | MEDIUM | 2 | worker_03 | 196 | MAX_15Y_BOUNDARY | YES |
| 61 | HND | UPCOM | MEDIUM | 2 | worker_05 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 62 | NO1 | HOSE | NORMAL | 3 | worker_03 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 63 | STK | HOSE | NORMAL | 3 | worker_05 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 64 | TVB | HOSE | NORMAL | 3 | worker_01 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 65 | IDV | HNX | NORMAL | 3 | worker_02 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 66 | DDH | UPCOM | NORMAL | 3 | worker_04 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 67 | HLS | UPCOM | NORMAL | 3 | worker_02 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 68 | POM | UPCOM | NORMAL | 3 | worker_03 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 69 | SGB | UPCOM | NORMAL | 3 | worker_05 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 70 | UDC | UPCOM | NORMAL | 3 | worker_01 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |
| 71 | VNZ | UPCOM | NORMAL | 3 | worker_04 | 196 | PARTIAL_IDENTITY_UNRESOLVED | YES |

Full assignment CSVs là execution source of truth. Bảng trên chỉ là review view.

## 5. History và identity policy

Mọi security dùng cùng rule:

```text
target_end = 2026-09-23
target_start = max(verified earliest legitimate listing/identity date, 2011-09-23)
```

Priority không thay đổi history length. Mã listing 2/8/20 năm lần lượt nhắm full
available khoảng 2/8/tối đa 15 năm.

LPB, CTR, SHB, BCM và VCG giữ evidence-backed exchange intervals từ A6; current
exchange không được dùng để cắt history trước transfer. Không nối ticker/exchange khi
không có identity evidence.

13 securities chưa có verified listing/identity start offline. Plan dùng
`2011-09-23` như hard experiment floor để estimate workload và ghi
`PARTIAL_IDENTITY_UNRESOLVED`; worker phải dừng security đó trước request nếu manual
review chưa resolve hoặc approve một plan revision. Riêng VCB còn có
`security_id=PLAN_INPUT_UNRESOLVED:VCB`.

Future record phải phân biệt:

```text
VERIFIED_LISTING_BOUNDARY
VERIFIED_IDENTITY_BOUNDARY
MAX_15Y_BOUNDARY
PROVIDER_HISTORY_BOUNDARY_CONFIRMED
PROVIDER_EMPTY_RESPONSE_UNRESOLVED
ACCESS_ERROR
SCHEMA_ERROR
PAGINATION_ERROR
UNRESOLVED_EARLY_HISTORY
```

Empty response không chứng minh before-listing hoặc provider exhaustion.

## 6. Pagination và request estimates

C1 required surface được freeze là CafeF `DataHistory/PriceHistory.ashx` vì đây là
endpoint có OHLC và date range. Contract:

- one-based `PageIndex`, fixed `PageSize=20`;
- observed ordering `newest-first`;
- non-overlapping calendar-year ranges, chạy oldest range tới newest range;
- page 1 validate envelope và `Data.TotalCount`;
- fetch exact page `1..ceil(TotalCount/20)`;
- empty page trước expected last page là `PAGINATION_ERROR`;
- duplicate date retained raw và flagged;
- out-of-window row retained raw nhưng loại khỏi normalized candidate;
- không silent skip và không empty-page loop.

`TradeHistoryNew.ashx` không nằm trong required C1 plan vì endpoint hiện không có date
range và adapter giới hạn 100 pages. Offline evidence chưa chứng minh cách lấy full
15-year history đúng contract. Đây là `PLAN_INPUT_UNRESOLVED`, không được giải quyết
bằng crawl trong C1-PREP.

Estimate dùng `252/365.2425` trading days theo calendar-day span, sau đó tính page theo
từng annual range. Đây là `REQUEST_ESTIMATE`, không phải request thực tế. Tổng estimate:

- 237.004 history trading-days;
- 12.278 pages;
- 12.278 requests;
- actual requests tại C1-PREP: 0.

## 7. Five-worker partition

Algorithm:

1. Wave 1 → Wave 2 → Wave 3.
2. Trong từng wave, sort `estimated_work_units` giảm dần, tie-break bằng
   `security_id`, ticker.
3. Gán row kế tiếp cho worker có current load thấp nhất; tie-break bằng worker ID.
4. Local execution order là wave, priority score giảm dần, `security_id`, ticker.

`estimated_work_units = estimated_requests + identity/edge/unresolved complexity`.
Không balance theo ticker count hoặc desired research outcome.

| Worker | Tickers | HIGH | MEDIUM | NORMAL | HOSE | HNX | UPCOM | Est. requests/pages | Est. history-years | Edge | First HIGH tickers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| worker_01 | 14 | 11 | 1 | 2 | 12 | 0 | 2 | 2.443 | 186.994 | 5 | CII, DGC, FRT, MWG, PLX |
| worker_02 | 14 | 11 | 1 | 2 | 8 | 4 | 2 | 2.445 | 187.094 | 5 | CTR, FPT, DGW, HCM, GVR |
| worker_03 | 14 | 11 | 1 | 2 | 9 | 3 | 2 | 2.457 | 188.012 | 4 | ANV, DCM, GAS, KDH, DHG |
| worker_04 | 15 | 12 | 1 | 2 | 11 | 0 | 4 | 2.470 | 188.936 | 5 | BCM, VNM, BVH, PNJ, BID |
| worker_05 | 14 | 11 | 1 | 2 | 8 | 2 | 4 | 2.463 | 188.471 | 3 | GMD, MBB, CTG, HDB, HPG |

Estimated work-unit range là 2.505–2.530, spread 25, max/min ratio 1.009980.
Mỗi security xuất hiện đúng một lần; không có `VALIDATION_OVERLAP`.

Workers bắt buộc chạy Wave 1 trước Wave 2 và Wave 3. Retry/resume một request không cho
phép kéo NORMAL work lên trước HIGH work còn lại.

## 8. Frozen worker execution contract

Mọi future worker phải khớp:

- approved execution commit và branch;
- CafeF adapter `cafef-research-demo-4`;
- `CAFEF_C1_PRICE_HISTORY_RAW_CANDIDATE_V1`;
- `CAFEF_ACQUISITION_PRIORITY_V1`;
- collection end `2026-09-23` và maximum 15 years;
- selected universe/assignment hash;
- endpoint/request parameters, timeout, retry/rate policy;
- raw/manifest schema và failure taxonomy.

Worker không được đổi source, endpoint semantics, history boundary, unit transform,
field mapping, priority definition, adjustment policy hoặc identity mapping trong lúc
crawl.

Future request policy: concurrency 1/worker, tối thiểu 5 giây giữa request, timeout 20
giây, tối đa 2 attempts và chỉ retry bounded transient timeout/5xx. HTTP 401/403/429,
CAPTCHA, Cloudflare challenge hoặc auth requirement dừng affected path; không evade.

## 9. Raw-only output và resume

Frozen future layout:

```text
artifacts/cafef_primary/<c1_run_id>/
  plan/
  worker_01/
    raw/
    request_log.jsonl
    failures.jsonl
    resume_state.json
    manifest.json
  worker_02/
  worker_03/
  worker_04/
  worker_05/
  merge/
```

Raw output giữ response bytes, request metadata, hashes, status, provider row count,
earliest/latest date, target window, identity, failures, resume state và manifest.
Không worker nào ghi canonical/research price/adjustment factor/features.
`GiaDieuChinh` luôn là `PROVIDER_ADJUSTED_VALIDATION_ONLY`.

Resume chỉ hợp lệ khi plan ID, assignment hash, config hash, source contract version,
code commit, history boundary, collection end và raw checksum state khớp. Completed
request được verify rồi skip. Transient failure chỉ retry trong budget. Methodology,
identity hoặc access failure không auto-retry; một ticker fail không restart worker.

## 10. Merge plan và C1 success metrics

Merge chỉ bắt đầu khi cả năm workers là `COMPLETED` hoặc
`COMPLETED_WITH_RECORDED_FAILURES`. Merge verify assignment completeness, manifests,
raw hashes, duplicate requests/observations, window coverage, contract/version/cutoff,
15-year compliance, provenance và failure aggregation. Output là unified RAW artifact,
không phải canonical.

C1 sau này sẽ đo planned-request completion, valid responses, schema/identity
consistency, exchange coverage, observed date depth, duplicate-date/invalid-OHLC rate,
request/access/pagination failure và provenance completeness. C1-PREP không đánh giá
metric và không đặt target “CafeF phải nhiều rows hơn KBS”.

Raw-OHLC gate vẫn là: `GiaMoCua`, `GiaCaoNhat`, `GiaThapNhat`, `GiaDongCua` có thật sự
là stable provider-observed raw prices hay không. Corporate-action edges chỉ giúp kiểm
định câu hỏi này; C1-PREP không thiết kế adjustment math.

## 11. Planning artifacts

Directory: `docs/crawl/plans/cafef_c1_prep_v1/`

- `cafef_c1_priority_ranking.csv`
- `cafef_c1_candidate_universe.csv`
- `cafef_c1_selected_pilot.csv`
- `cafef_c1_request_estimates.csv`
- `cafef_c1_worker_01_assignment.csv`
- `cafef_c1_worker_02_assignment.csv`
- `cafef_c1_worker_03_assignment.csv`
- `cafef_c1_worker_04_assignment.csv`
- `cafef_c1_worker_05_assignment.csv`
- `cafef_c1_partition_summary.json`
- `cafef_c1_crawl_contract.json`
- `cafef_c1_failure_policy.json`
- `cafef_c1_merge_plan.md`
- `manifest.json`

Planner reproducible: `scripts/plan_cafef_c1_workers.py`. Script chỉ đọc local files,
không import HTTP client và không chứa crawler.

## 12. Manual review gate

Reviewer cần quyết định:

1. chấp nhận priority model trong bối cảnh liquidity/index/size/popularity signals chưa
   có offline artifact;
2. approve/exclude/resolve 13 `PARTIAL_IDENTITY_UNRESOLVED` securities, đặc biệt VCB;
3. chấp nhận C1 required surface chỉ là `PriceHistory`, còn `TradeHistory` chưa nằm
   trong full-history contract;
4. chấp nhận execution rights risk hoặc yêu cầu thêm rights evidence;
5. freeze execution commit sau approval.

Self-review đạt: đúng branch/base, đúng 5 workers, 71/71 assigned một lần, zero overlap,
HIGH trước MEDIUM/NORMAL, cùng cutoff, history không quá 15 năm, đủ ba sàn, UPCOM quan
trọng không bị loại, edge coverage có, priority không ảnh hưởng eligibility và workload
balance theo requests/complexity.

```text
USER_MANUAL_REVIEW_REQUIRED = YES
NEXT_ALLOWED_ACTION = USER MANUAL REVIEW OF C1 CRAWL PLAN
AFTER_EXPLICIT_APPROVAL_ONLY = C1 — Representative CafeF Raw-Market Acquisition
```

STOP. Không execute C1.
