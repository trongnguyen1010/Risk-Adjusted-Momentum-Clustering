# CafeF Primary Data Foundation Experiment Plan

## Execution Progress / Handoff

```yaml
branch: m1-cafef-primary-experiment
forked_from_branch: m1-scale-500-team-crawl
fork_base_commit: e886f68875fb5c079e57c9b51cae9e6bf5a8047b
current_experiment: CafeF Primary Data Foundation Experiment
last_completed_stage: C6-R2-EXTEND-CAFEF-EXPANSION-HISTORY-TO-2020
c0_result: COMPLETED / USER_APPROVED
c1_prep_v1_status: SUPERSEDED / HISTORICAL_ONLY
c1_execution_model: SINGLE_LOCAL_RUNNER
c1_solo_plan_version: cafef_c1_solo_v2
pilot_security_count: 27
collection_end_date: 2026-09-23
history_policy: HISTORY_POLICY_V3
c1_history_policy: HISTORY_POLICY_V3_BASE_5Y
expansion_history_policy: BASE_2020
expansion_target_start: 2020-01-01
deep_history_tier: DEEP_10Y_DETERMINISTIC_STRATIFIED
long_history_tier: LONG_15Y_VALIDATION_ONLY
old_15y_for_all_policy: SUPERSEDED
old_v2_3_run: STOPPED_NOT_RESUMABLE_AS_V3
valid_completed_old_history: REUSED_WHERE_COMPLETE
partial_old_history: NOT_AUTOMATICALLY_REUSED
active_plan: cafef-c1-history-v3
priority_policy: CAFEF_C1_SOLO_PRIORITY_V2
c1_actual_crawl_executed: COMPLETED_CAFEF_C1_BASE5Y_MAIN
data_crawl_executed: YES
market_data_requests_for_experiment: 1259
market_data_requests_in_corrective_stage: 0
actual_market_data_requests_in_corrective_stage: 0
actual_crawl_executed_in_corrective_stage: NO
actual_valid_c1_crawl_executed: YES
c1_solo_runner_contract_corrected: YES
exchange_type_contract_aligned: YES
historical_identity_interval_routing: YES
envelope_success_validation: YES
verified_pricehistory_endpoint_aligned: YES
failed_response_evidence_preserved: YES
range_contract_finding: LONG_RANGE_SILENT_TRUNCATION_CONFIRMED_BY_LIVE_ACB_SAMPLE
old_range_policy: NON_OVERLAPPING_CALENDAR_YEAR_CHUNKS
old_range_policy_status: INVALID_FOR_C1_COMPLETENESS
new_range_policy: NON_OVERLAPPING_CALENDAR_QUARTER_INTERSECTIONS
existing_long_history_complete_count: 10
base5y_reused_count: 10
base5y_crawl_required_count: 17
base5y_quarter_range_count: 359
base5y_estimated_requests: 1360
request_estimate_label: ESTIMATE_NOT_ACTUAL
old_local_crawl_artifacts: STOPPED_V2_3_SOURCE_ARTIFACT_PRESERVED
canonical_mutation: NO
canonical_mutations: 0
feature_rebuild: NO
five_worker_execution: PREPARED_NOT_EXECUTED
expansion_id: cafef-expansion-v1
expansion_selected: 600
expansion_reserve: 100
expansion_workers: 5
long_expansion_crawl_executed: NO
old_incomplete_security_count: 10
old_incomplete_status: DEFERRED_MISSING_SESSION_REVIEW
next_allowed_action: OWNER_PUSHES_FINAL_C6_R2_COMMIT_TO_FIVE_HUMAN_WORKERS
after_explicit_user_approval: FIVE_WORKERS_CLONE_EXACT_COMMIT_AND_EXECUTE_FROZEN_SHARDS
c1_prep_solo_crawl_execution: NO
user_manual_review_required: YES
```

Tài liệu này là source of truth cho nhánh thử nghiệm. Không được suy approval từ việc
branch tồn tại, từ việc C0 đã commit, hoặc từ kết quả thuận lợi của bất kỳ bằng chứng cũ
nào.

## C6 handoff

C5 manifest hashes đã được replay thành công. C6 không retry 10 mã incomplete, không
mutate C4/C5 và không chạy crawl expansion. Universe mới được chọn trước acquisition
từ KBS current-listing evidence; current 500 và reviewed historical aliases bị loại.
Mọi index/market-importance signal không có reliable evidence đều ghi `UNAVAILABLE`.

Active contracts nằm tại `configs/data/cafef_expansion_v1/`; worker runbook tại
`docs/crawl/CAFEF_EXPANSION_5_WORKERS.md`. C8 sau này phải verify/merge tập trung và
audit full history tách khỏi latest-253; C6 không normalize hoặc promote dữ liệu.

C6-R2 giữ nguyên 600 mã, reserve và worker ownership, nhưng mở rộng acquisition
target thành `2020-01-01 → 2026-09-23` dưới contract
`c6-cafef-expansion-v2`/`BASE_2020`. Provider boundary thật được giữ trung tính;
không fabricate history trước listing hoặc sau khi CafeF hết history.

## 1. Purpose

Thử nghiệm một data foundation thay thế, trong đó CafeF là **ứng viên primary raw
market provider**, còn DELTA tự định nghĩa research-price semantics bằng corporate
action evidence và adjustment policy được version hóa.

Mục tiêu là đo xem kiến trúc này có thể tạo ra:

- historical coverage tốt hơn;
- ít unresolved missing sessions hơn;
- raw-market provenance tái lập được;
- research-price semantics không phụ thuộc định nghĩa đóng của một vendor;
- corporate-action adjustment giải thích và audit được;
- research readiness tốt hơn;

mà vẫn giữ đúng identity, point-in-time, no-imputation, completeness và provenance.
CafeF không mặc nhiên tốt hơn KBS; kết quả của các stage sau mới quyết định.

## 2. Branch isolation

- Nhánh thử nghiệm: `m1-cafef-primary-experiment`.
- Fork từ `m1-scale-500-team-crawl` tại
  `e886f68875fb5c079e57c9b51cae9e6bf5a8047b`.
- `m1-scale-500-team-crawl` tiếp tục là KBS-primary track được bảo toàn.
- Không sửa, rebase, merge hoặc force-push source branch trong experiment này.
- Mọi raw, normalized, corporate-action, research-price và feature artifact mới phải có
  run/version riêng; không overwrite immutable evidence hay canonical hiện tại.

## 3. Current evidence

Các kết luận A5-R1, A5-R1.1 và A5-R4 là historical truth của KBS track, không bị C0
viết lại:

- KBS canonical hiện tại có basis `vendor_adjusted` và phương pháp điều chỉnh chi tiết
  của vendor vẫn không được chứng minh là split-only hay total-return.
- CafeF `GiaDieuChinh` / `AdjustPrice` là provider-adjusted field có phương pháp kinh tế
  chưa được tài liệu hóa; nó chỉ là validation reference, không phải DELTA research
  price.
- CafeF không thể được promote vào KBS `vendor_adjusted` canonical hiện tại vì
  `PRICE_BASIS_UNRESOLVED`.
- CafeF `PriceHistory` cung cấp date, OHLC, close, adjusted price, matched và negotiated
  components; `TradeHistoryNew` bổ sung reference/ceiling/floor và raw-VND components.
  Hai endpoint bổ sung cho nhau, không tương đương.
- January-2020 rows trên sample là tín hiệu 5+ năm, không chứng minh coverage của 500
  securities.
- CafeF corporate-action pages/documents có bằng chứng hữu ích nhưng event dates,
  normalized terms, revision chain và complete coverage chưa đủ.
- Automation/data-use rights của CafeF vẫn `RIGHTS_NOT_VERIFIED`.
- VCI và DNSE có real OHLCV nhưng không tương thích ổn định với KBS basis trong sample;
  FiinGroup chỉ là documented/contract-dependent validation candidate.

C0 đặt câu hỏi mới: **nếu KBS compatibility không còn là điều kiện định nghĩa
canonical, một raw-first architecture có khả thi không?** Điều này không đảo ngược kết
luận của KBS track.

## 4. Non-goals and hard C0 boundary

C0 chỉ audit và planning. C0 không:

- gọi market-data endpoint hoặc chạy bounded smoke;
- crawl lịch sử, current 500 hay representative securities;
- fetch missing sessions;
- tạo hoặc mutate canonical/data artifact;
- rebuild feature hoặc EDA;
- implement recovery, corporate-action adjustment engine hay production schema;
- thực hiện C1-PREP, C1, C2, C3, C4, C5 hoặc C6;
- tạo ticker assignment hoặc executable five-worker crawl plan.

Existing docs, source code và immutable evidence chỉ được đọc.

## 5. Architecture hypothesis

```text
CafeF provider payloads
        ↓ preserve bytes, request, fetched_at, hash
Normalized raw-market observations
        ↓ identity/unit/date validation; no adjustment
RAW MARKET CANONICAL CANDIDATE
        ├──────────────→ provider cross-checks (KBS / VCI / DNSE / FiinGroup)
        ↓
Versioned corporate-action event evidence
        ↓ reviewed economic semantics
DELTA adjustment policy + deterministic engine
        ↓ raw-row refs + event refs + factor lineage
RESEARCH PRICE SERIES
        ↓ complete-session and PIT gates
FEATURES / EDA / research readiness
```

Hai invariant trung tâm:

1. `RAW MARKET OBSERVATION` không phải `RESEARCH-ADJUSTED PRICE`.
2. Provider-adjusted series chỉ dùng để validate/cross-check; không được silently định
   nghĩa policy của DELTA.

## 6. Proposed price layers

Tên dưới đây là conceptual; physical schema chỉ được freeze ở stage implementation sau
manual review.

### Layer 1 — `prices_daily_raw`

Một row là observation do provider công bố, không corporate-action back-adjustment.
Candidate key nên bao gồm `provider + provider_security_identity + trade_date +
observation_version`, thay vì ép một value duy nhất cho mỗi security/date quá sớm.

Required lineage:

- `security_id`, provider symbol/exchange và identity-interval reference;
- `trade_date`, date parser/version và source timezone semantics;
- raw OHLC, matched volume/value, negotiated volume/value và optional
  reference/ceiling/floor theo đúng field contract;
- `provider`, `acquisition_client`, endpoint, request parameters;
- `fetched_at`, raw artifact path/hash, raw row hash, adapter/contract version;
- unit transform và transform evidence;
- row classification, duplicate/conflict status và `available_at` policy nếu verified.

Không chứa DELTA adjustment factor. Không copy `AdjustPrice` vào raw close.

### Layer 2 — `corporate_actions`

Giữ event evidence và normalized semantics, không mutate price. Cần giữ cả
provider/document identity và canonical event identity; conflicting documents/events
không bị overwrite.

### Layer 3 — `prices_daily_research`

Derived output của:

```text
one accepted raw observation
+ versioned DELTA adjustment policy
+ reviewed corporate-action event set
```

Mỗi row phải giữ `raw_observation_id`, `research_price`, factor/factor-chain reference,
policy version/hash, event IDs/hashes, `derived_at`, code revision và derivation status.
Không đủ event evidence thì row/window là unresolved, không fallback sang provider
adjusted value.

## 7. CafeF raw contract assessment

Chỉ dựa trên A5-R1/A5-R1.1 evidence hiện có:

| Field | Surface / endpoint | Unit / date semantics | Classification | Confidence | Blocker | Candidate target |
|---|---|---|---|---|---|---|
| `Ngay` | `PriceHistory.ashx` | `DD/MM/YYYY`, session date | RAW_OBSERVABLE | HIGH | exact range/completeness contract chưa freeze | `trade_date` |
| `TradeDate` | `TradeHistoryNew.ashx` | UTC-like/legacy timestamp → ICT session date; leading page-1 snapshot excluded | RAW_OBSERVABLE | HIGH | endpoint-specific parser/version | `trade_date` |
| `GiaMoCua` | PriceHistory | nghìn VND/share, ×1,000 | RAW_CANDIDATE | MEDIUM | cần xác nhận đây là unadjusted market observation trên event windows | `raw_open` |
| `GiaCaoNhat` | PriceHistory | nghìn VND/share, ×1,000 | RAW_CANDIDATE | MEDIUM | như trên | `raw_high` |
| `GiaThapNhat` | PriceHistory | nghìn VND/share, ×1,000 | RAW_CANDIDATE | MEDIUM | như trên | `raw_low` |
| `GiaDongCua` / `ClosePrice` | both | nghìn VND/share, ×1,000 | RAW_CANDIDATE | MEDIUM | phải phân biệt rõ với provider-adjusted series qua event evidence | `raw_close` |
| `GiaDieuChinh` / `AdjustPrice` | both | nghìn VND/share, ×1,000 | PROVIDER_ADJUSTED | HIGH field identity / LOW methodology | adjustment method undocumented | validation-only provider series |
| `BasicPrice` | TradeHistory | nghìn VND/share, ×1,000 | RAW_OBSERVABLE | MEDIUM | identity/date validation; unavailable on PriceHistory | `reference_price` |
| `Ceiling`, `Floor` | TradeHistory | nghìn VND/share, ×1,000 | RAW_OBSERVABLE | HIGH | identity/date validation | `ceiling_price`, `floor_price` |
| `Volume` / `KhoiLuongKhopLenh` | both | shares | RAW_OBSERVABLE | HIGH | matched-only semantics phải giữ | `matched_volume` |
| `TotalValue` | TradeHistory | VND | RAW_OBSERVABLE | HIGH | không cộng ngầm với negotiated value | `matched_value` |
| `GiaTriKhopLenh` | PriceHistory | billion VND, ×1e9 | RAW_OBSERVABLE | HIGH | rounded/display precision | `matched_value` |
| `AgreedVolume` / `KLThoaThuan` | both | shares | RAW_OBSERVABLE | HIGH | component riêng | `negotiated_volume` |
| `AgreedValue` | TradeHistory | VND | RAW_OBSERVABLE | HIGH | component riêng | `negotiated_value` |
| `GtThoaThuan` | PriceHistory | billion VND, ×1e9 | RAW_OBSERVABLE | HIGH | rounded/display precision | `negotiated_value` |
| Current reference/ceiling/floor UI | company page | nghìn VND/share | RAW_SNAPSHOT_ONLY | HIGH current / LOW historical | không thay historical series | separate current snapshot evidence |

`traded_value` không được tự tạo bằng matched + negotiated cho đến khi policy field được
review; hai components phải được giữ riêng.

## 8. Corporate-action requirements

### 8.1 Common evidence contract

Mọi event cần, khi applicable:

- `event_id`, `security_id`, provider event/document ID;
- `event_type`, raw label và normalized taxonomy version;
- `announcement_date`, `published_at`, `available_at`, timezone semantics;
- `ex_date`, `record_date`, `effective_date`, `payment_date`;
- ratio numerator/denominator, cash amount, subscription price, currency;
- affected instrument/share class và before/after unit semantics;
- source document URL/reference, immutable content hash, `fetched_at`;
- evidence extractor/version, confidence, review status và conflict state.

Không suy adjustment factor từ tỷ lệ KBS/CafeF.

### 8.2 Event-specific economic rules to define before implementation

| Event type | Required terms | Rule that must be documented and tested |
|---|---|---|
| Stock split | old/new share ratio, ex/effective date | share-unit change và price continuity convention |
| Reverse split | old/new share ratio, ex/effective date | inverse share-unit change, fractional-share handling |
| Stock dividend | entitlement ratio, ex-date, delivery/effective date | whether/when new shares enter economic denominator |
| Bonus shares | entitlement ratio, ex-date, effective date | distinguish from stock dividend while defining same/different factor semantics explicitly |
| Cash dividend | cash/share, currency, ex-date | price-return versus total-return treatment; tax assumption if any |
| Rights issue | entitlement ratio, subscription price, ex/record dates, exercise window | theoretical economic dilution rule and unexercised-right treatment |
| Additional issuance | issuance type, quantity/ratio, issue price, eligibility, effective/listing date | whether it affects existing-holder price continuity; many issuances may be evidence-only |
| Ticker/exchange event | stable security ID, old/new ticker/exchange, interval dates | continuity only when same economic security is proven; no price factor by default |

An event with incomplete economic terms may explain a discontinuity diagnostically but
must not generate an adjustment factor.

## 9. Multi-provider roles and conflict policy

| Source | Proposed experiment role |
|---|---|
| CafeF | `PRIMARY_RAW_MARKET_CANDIDATE` |
| KBS | `VALIDATION_CROSS_CHECK` and legacy-track comparator |
| VCI | `SECONDARY_DIAGNOSTIC_CROSS_CHECK` |
| DNSE | `SECONDARY_DIAGNOSTIC_CROSS_CHECK` |
| FiinGroup | `OPTIONAL_DOCUMENTED_VALIDATION_SOURCE` only with legitimate future access |

Conflict handling is deterministic:

1. retain every raw observation and provenance;
2. normalize only with documented unit/date/identity rules;
3. compare like-for-like fields and basis;
4. exact equivalent values may be marked `MATCH`;
5. conflict is preserved as `VALUE_CONFLICT`, `UNIT_CONFLICT`,
   `PRICE_BASIS_CONFLICT`, `TIMING_CONFLICT` or `IDENTITY_CONFLICT`;
6. no majority vote, averaging, silent provider fallback or inferred transform;
7. selection, if ever allowed, requires a versioned field-level policy and remains
   reproducible from retained candidates.

## 10. Missing-session strategy

Future audit classifications:

```text
CAFEF_REAL_ROW
CAFEF_NO_ROW
SECONDARY_REAL_ROW
MULTI_PROVIDER_REAL_ROW
PROVIDER_CONFLICT
IDENTITY_CONFLICT
CALENDAR_OR_STATUS_STRUCTURAL
NOT_LISTED
DELISTED
SUSPENDED_OR_HALTED
UNRESOLVED_MISSING
```

The future audit will build an expected-session grid from exchange calendar plus
effective identity/listing intervals, then record independently:

- KBS missing + CafeF has row;
- KBS missing + CafeF/VCI/DNSE have row;
- CafeF missing + KBS has row;
- all providers missing;
- provider/security identity mismatch;
- official structural no-trade, suspension or listing boundary.

Row absence alone never proves halt/suspension. A secondary real row is evidence, not
automatic canonical promotion. This audit is not run in C0.

## 11. No-imputation and failure rules

Forbidden at every stage:

- forward/back fill, interpolation, previous-close substitution;
- missing price/volume → zero;
- synthetic OHLC, fake zero-return session or timeline compression;
- worker-level source switch, field semantic change or adjustment-policy change;
- dropping a failed ticker/request from denominators.

A failed request remains failed with evidence. Missing remains missing. Methodology
uncertainty stops the affected path.

## 12. Artifact and provenance requirements

Every run records `run_id`, stage, UTC creation time, git commit, frozen config hash,
contract/policy version, input artifact IDs/hashes, provider/adapter versions, request
counts and output hashes.

Raw artifacts are immutable and worker-specific. Normalized candidates reference raw
hashes. Corporate actions reference source documents. Research prices reference raw
rows, event inputs and adjustment policy. Features reference the exact research-price
artifact. Completed/resumed runs are valid only when config, plan, code and raw hashes
match.

No crawl worker writes canonical or research-price tables.

## 13. Stages and manual review gates

| Stage | Scope | Execution in this task | Exit condition |
|---|---|---|---|
| C0 | Architecture audit, raw contract assessment, migration/test plan | COMPLETED AS PLAN | `USER_MANUAL_REVIEW_REQUIRED` |
| C1-PREP v1 | Historical five-worker planning evidence | SUPERSEDED / HISTORICAL_ONLY | retained; do not execute |
| C1-PREP-SOLO | Freeze 25–30 security plan and prepare one resumable local runner | COMPLETED AS PLAN | user manual review |
| C1-SOLO | Representative CafeF raw-market acquisition | COMPLETED | offline quarter/page/checksum audit PASS for 27/27 |
| C2 | Normalized CafeF candidates and corporate-action diagnostics | PARTIAL | 33,259 candidates built; event documents/terms not acquired |
| C3 | CafeF-primary self-sufficiency and field-coverage audit | COMPLETED / MANUAL_REVIEW_REQUIRED | KBS comparator waived by user; canonical readiness remains fail-closed |
| C4-PREP-SCALE | Multi-worker scale planning for approximately 500+ securities | NOT AUTHORIZED | C1–C3 methodology gates pass + explicit approval |
| C4 | Five-worker scale acquisition | NOT AUTHORIZED | approved C4-PREP-SCALE assignments |
| C5 | Research-price/feature rebuild and comparative EDA | NOT AUTHORIZED | versioned derivation and complete QA |
| C6 | Architecture decision | NOT AUTHORIZED | evidence-backed GO/NO-GO |

Required control flow:

```text
C0
 ↓ GATE 0 — USER MANUAL REVIEW; no inferred approval
explicit user approval
 ↓
C1-PREP v1 — superseded historical five-worker plan; never execute for C1
 ↓
C1-PREP-SOLO — one frozen pilot + one resumable local runner; performs zero crawl
 ↓ GATE 2 — USER MANUAL REVIEW OF SOLO PLAN AND RUNNER
explicit user approval
 ↓ GATE 3
actual C1-SOLO crawl may begin locally
```

Later stage order may be refined by evidence, but no crawl stage is authorized
automatically.

## 14. Future five-worker workflow design — C4-PREP-SCALE only

Five-worker planning is explicitly deferred until the CafeF-primary path survives C1,
C2 and C3 methodology gates and the target expands to approximately 500+ securities.
Only `C4-PREP-SCALE` may create executable worker assignments. The deterministic
work-estimation and bin-packing ideas in `scripts/plan_cafef_c1_workers.py` may be
reused then; that script and its v1 artifacts are not active C1 execution inputs.

C0 defines construction principles only; it creates no executable assignment and no
ticker lists.

C4-PREP-SCALE must:

- freeze universe, exact `security_id`/ticker/exchange snapshot, date range, endpoint,
  raw contract and config hash;
- estimate work per security using expected request count, history depth, exchange,
  known sparse/problematic cases, runtime and resume cost;
- construct **exactly five** deterministic partitions with a documented balancing
  algorithm and stable tie-breaker;
- prohibit overlap except a small, explicit validation overlap whose rows are labeled
  and excluded from unique coverage counts;
- emit per-worker manifest, checksum set, retry budget, log path, raw directory and
  failure-list path;
- use bounded retries and fail closed on access, schema or semantics errors;
- keep outputs raw and immutable; no canonical writes during crawl;
- permit merge only after all five workers reach a terminal state;
- run global assignment uniqueness, deduplication, coverage and provenance checks
  before any normalization/promotion proposal.

Không dùng contiguous ticker blocks `1–100`, `101–200`, ... trước khi workload được
phân tích. Không balance theo research outcome hoặc desired feature readiness.

## 15. Success metrics

Legacy KBS track và CafeF-primary experiment sẽ được so theo cùng definitions:

- total real raw price rows và unique provider observations;
- securities acquired;
- observed/usable history `>=3Y`, `>=5Y`;
- expected-session missing count, missing rate và streak distribution;
- complete 21/63/126/252-session windows;
- market-feature-ready, identity-ready và research-ready counts;
- provider conflicts, duplicate rows và invalid OHLC rows;
- corporate-action discontinuities detected;
- adjustment events covered và unresolved;
- feature distribution shifts, with event-linked diagnostics;
- runtime, request count, retry/failure count and storage size;
- source access, rights and contract limitations.

Không đặt target giả như “CafeF phải vượt 169”. Metrics phải phân biệt raw coverage,
research-price eligibility và strict research readiness.

## 16. GO / NO-GO framework

C6 chỉ được chọn một trong:

- `GO_CAFEF_PRIMARY`;
- `GO_PROVIDER_NEUTRAL_RAW`;
- `KEEP_KBS_PRIMARY`;
- `HYBRID_REDESIGN_REQUIRED`;
- `EXPERIMENT_INCONCLUSIVE`.

Quyết định dựa trên measured coverage, adjustment completeness, reproducibility,
identity/calendar integrity, rights/access viability, conflict burden và feature impact.
C0 không chọn outcome.

## 17. Kết quả C1 hậu crawl, C2 và C3 offline

Run `cafef-c1-base5y-main` đã hoàn tất 1.259 request cho 17 mã; 10 mã còn lại dùng
long-history V2.3 đã checksum-validate. Pipeline offline
`scripts/run_cafef_c2_c3_offline.py` không gọi mạng, không sửa raw và không ghi
canonical.

Kết quả local `artifacts/cafef_primary/cafef-c2-c3-offline-20260924/`:

- 27/27 mã PASS audit quarter/page/progress/raw SHA/sidecar SHA;
- 33.259 provider-qualified market candidates, 0 conflicting duplicate date;
- 15 mã `PASS_RAW_CANDIDATE`, 12 mã cần review;
- 11 row phải quarantine vì OHLC bất khả thi, gồm bốn row có `high=0` dù vẫn có
  volume; raw giữ nguyên và không repair;
- CTR không có observation cho interval UPCOM `2021-09-23 → 2022-02-22`; SHB không
  có observation cho interval HNX `2021-09-23 → 2021-10-10` dù request hợp lệ;
- 27/27 có observed-span evidence ít nhất ba năm; đây không thay thế official-session
  calendar hay price-basis approval;
- 183 discontinuity candidates chỉ là diagnostic, không phải corporate-action proof.

C3 không chạy comparator KBS theo quyết định người dùng. Thay vào đó, C3 kiểm tra
khả năng tự cung cấp dữ liệu của raw `PriceHistory` hiện có:

| Table | Evidence hiện có | Canonical-fillable fields | Kết luận |
|---|---:|---:|---|
| `securities` | 12/17 | 10/17 | thiếu company name, authoritative availability/identity metadata |
| `prices_daily` | 17/20 | 9/20 | candidate-only; OHLC basis, adjusted method và component policy chưa duyệt |
| `trading_calendar` | 6/11 diagnostic | 0/11 | observed union không phải official calendar |
| `shares_history` | 0/10 | 0/10 | không có trong PriceHistory |
| `benchmark_daily` | 0/10 | 0/10 | page snapshot VNINDEX không phải historical benchmark series |
| `corporate_actions` | 0/16 | 0/16 | chưa acquire event document/terms |
| `financial_reports` | 0/18 | 0/18 | chưa acquire PIT report metadata |
| `financial_facts` | 0/12 | 0/12 | chưa acquire financial facts |

Kết luận: CafeF `PriceHistory` hiện đủ tốt để làm **primary raw market candidate** sau
row quarantine, nhưng chưa đủ để một mình fill toàn bộ M1 canonical tables. Việc bỏ KBS
comparison không tự giải quyết price basis, calendar, corporate actions, shares hoặc
financial PIT. Mapping OHLC vào `raw_*` là methodology-sensitive và tiếp tục cần manual
approval.

## 18. Current status / Handoff

```yaml
stage: C3-CAFEF-PRIMARY-SELF-SUFFICIENCY-AUDIT
status: PARTIAL / MANUAL_REVIEW_REQUIRED
documents:
  - docs/crawl/CAFEF_PRIMARY_EXPERIMENT_PLAN.md
  - docs/crawl/CAFEF_PRIMARY_MIGRATION_AUDIT.md
  - docs/crawl/CAFEF_PRIMARY_C1_CRAWL_PLAN.md
planning_artifact_directory: docs/crawl/plans/cafef_c1_solo_v2
historical_planning_artifact_directory: docs/crawl/plans/cafef_c1_prep_v1
offline_planner: scripts/plan_cafef_c1_solo.py
solo_runner: scripts/run_cafef_c1_solo.py
execution_model: SINGLE_LOCAL_RUNNER
data_crawl_executed: YES
market_data_requests_for_experiment: 1259
actual_market_data_requests_in_corrective_stage: 0
actual_crawl_executed_in_corrective_stage: NO
actual_valid_c1_crawl_executed: YES
c1_solo_runner_contract_corrected: YES
exchange_type_contract_aligned: YES
historical_identity_interval_routing: YES
envelope_success_validation: YES
verified_pricehistory_endpoint_aligned: YES
failed_response_evidence_preserved: YES
range_contract_finding: LONG_RANGE_SILENT_TRUNCATION_CONFIRMED_BY_LIVE_ACB_SAMPLE
old_range_policy: NON_OVERLAPPING_CALENDAR_YEAR_CHUNKS
old_range_policy_status: INVALID_FOR_C1_COMPLETENESS
new_range_policy: NON_OVERLAPPING_CALENDAR_QUARTER_INTERSECTIONS
existing_long_history_complete_count: 10
base5y_reused_count: 10
base5y_crawl_required_count: 17
base5y_quarter_range_count: 359
base5y_estimated_requests: 1360
request_estimate_label: ESTIMATE_NOT_ACTUAL
old_local_crawl_artifacts: STOPPED_V2_3_SOURCE_ARTIFACT_PRESERVED
canonical_mutations: 0
feature_rebuild: NO
five_worker_execution: DEFERRED_TO_C4_PREP_SCALE
pilot_security_count: 27
parallel_requests: NO
collection_end_date: 2026-09-23
history_policy: HISTORY_POLICY_V3
default_history_tier: BASE_5Y
base_history_lower_bound: 2021-09-23
deep_history_tier: DEEP_10Y_DETERMINISTIC_STRATIFIED
long_history_tier: LONG_15Y_VALIDATION_ONLY
old_15y_for_all_policy: SUPERSEDED
old_v2_3_run: STOPPED_NOT_RESUMABLE_AS_V3
valid_completed_old_history: REUSED_WHERE_COMPLETE
partial_old_history: NOT_AUTOMATICALLY_REUSED
active_plan: cafef-c1-history-v3
priority_policy: CAFEF_C1_SOLO_PRIORITY_V2
postcrawl_raw_audit: PASS_27_OF_27
normalized_market_candidates: 33259
raw_candidate_pass_tickers: 15
raw_candidate_warning_tickers: 12
quarantined_provider_rows: 11
identity_intervals_without_observations: 2
c2_status: PARTIAL_EVENT_DOCUMENTS_NOT_ACQUIRED
c3_kbs_comparison: WAIVED_BY_USER_NOT_EXECUTED
c3_status: COMPLETED_MANUAL_REVIEW_REQUIRED
cafef_primary_market_candidate_viable: YES
cafef_canonical_ready: NO
full_m1_table_coverage: NO
next_allowed_action: USER MANUAL REVIEW OF C3 FIELD READINESS AND PRICE BASIS
forbidden_until_explicit_approval:
  - canonical promotion of CafeF OHLC
  - research-price derivation
  - feature rebuild
after_explicit_user_approval: APPROVE_OR_REJECT_CAFEF_RAW_OHLC_MAPPING_AND_PLAN_MISSING_DOMAINS
```

STOP after C3. Do not promote CafeF candidates or rebuild features without explicit
price-basis and missing-domain decisions.

## 19. Kết quả C3-R1 — Canonical market contract và 27-security pilot

Owner đã phê duyệt price-basis và missing-domain decisions cho đúng stage C3-R1.
Builder mới tạo immutable local artifact
`artifacts/cafef_primary/cafef-canonical-market-pilot-v1/` mà không overwrite baseline:

- `GiaDieuChinh × 1000 → adj_close`, `adjustment_basis=vendor_adjusted`; canonical
  `raw_open/high/low/close=null`, provider OHLC vẫn ở staging;
- 33.248 canonical price rows; 11 quarantine rows không giao với canonical;
- 30 security interval rows cho 27 stable securities, giữ nguyên BCM/CTR/SHB history;
- 3.738 shared-session calendar rows và 1.244 VNINDEX price-index rows;
- calendar/security/benchmark reuse reviewed local evidence; đúng một public VNINDEX
  extension request, không crawl lại CafeF và không dùng KBS equity comparator;
- schemas, uniqueness, identity relation, calendar relation và no-imputation đều PASS;
- CTR old UPCOM và SHB old HNX vẫn là
  `UNRESOLVED_IDENTITY_INTERVAL_NO_OBSERVATIONS`;
- shares/corporate-actions/financial reports/facts là
  `DEFERRED_NOT_REQUIRED_FOR_CURRENT_MARKET_PIPELINE`.

Feature dry-run chạy đủ 27 mã và giữ nguyên tám required features. Bảy feature có
27/27 non-null; `mom_252` có 0/27 vì CafeF thiếu open sessions 29–30/01/2026 cho mọi
mã, và ACV/QNS/VEA/VGI còn thiếu 02–13 cùng 23–25/02/2026. Missing giữ `None`, không
fill hoặc nén timeline. Vì vậy `market_feature_ready=0/27`, `research_ready=0/27` và
stage là `PARTIAL_MANUAL_REVIEW_REQUIRED`, không được ép PASS.

```yaml
stage: C3-R1_CAFEF_CANONICAL_MARKET_CONTRACT
status: PARTIAL_MANUAL_REVIEW_REQUIRED
canonical_prices_daily: 33248
quarantined_rows: 11
security_interval_rows: 30
trading_calendar_rows: 3738
benchmark_rows: 1244
network_requests: 1
feature_dry_run: PASS
market_feature_ready: 0/27
research_ready: 0/27
canonical_baseline_overwritten: NO
scale_crawl: NO
next_allowed_action: RESOLVE_ONLY_REPORTED_CAFEF_MISSING_SESSION_BLOCKERS
```
# C3-R2 LOCAL TRADEHISTORY RAW REUSE

This evidence-only stage reuses pre-existing M1 shard, representative-pilot,
and source-smoke CafeF `TradeHistoryNew.ashx` raw pages from the reviewed
external local evidence root before considering any recrawl. Missing rows on
`PriceHistory.ashx` are therefore not treated as missing at the CafeF provider
level. Exact copies from older runs are collapsed; differing same-date provider
observations remain fail-closed and are excluded from automatic endpoint
recommendations. Network fallback is planned only, never executed in C3-R2.
The resulting index is an external-local-evidence dependency, not canonical
data and not a portable raw-data dependency.
# C4 — TRADEHISTORYNEW 500-SECURITY MARKET SOURCE EVALUATION

C4 treats the reviewed 500-security M1 universe as the breadth evaluation and
keeps the 27-security PriceHistory comparison as a deep-validation subset.
Complete PriceHistory-to-TradeHistory reconciliation is no longer a prerequisite
for measuring TradeHistoryNew breadth. `AdjustPrice` is the frozen vendor-adjusted
research-price field; `ClosePrice` is the provider-published raw close. Historical
Open, High, and Low are unavailable on TradeHistoryNew, are not required by the
current feature set, and may be supplied only by a future versioned enrichment.
The evaluation uses no imputation, keeps strict missing sessions and conflicts,
and has no arbitrary readiness target. C4 is offline and does not promote its
experimental candidate into production canonical data.

# C5 — MARKET OBSERVATION SEMANTICS AND TARGETED RECOVERY

A provider-published `Volume=0` row remains an observed market row and is
usable by price-based research features. Zero published volume does not prove
suspension, halting, or delisting. C5 therefore versions readiness as
`MARKET_FEATURE_READINESS_V2`: market-data readiness is independent of the
separate tradability status (`ACTIVE`, `OBSERVED_ZERO_VOLUME`, or
`UNKNOWN_ACTIVITY_COMPONENTS`). No null component becomes zero and no price or
session is imputed. Same-provider recovery is bounded to the exact latest-253
blockers identified offline. Historical identity remains an independent strict
research gate and is not promoted by C5.
