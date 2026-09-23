# CafeF Primary Data Foundation Experiment Plan

## Execution Progress / Handoff

```yaml
branch: m1-cafef-primary-experiment
forked_from_branch: m1-scale-500-team-crawl
fork_base_commit: e886f68875fb5c079e57c9b51cae9e6bf5a8047b
current_experiment: CafeF Primary Data Foundation Experiment
last_completed_stage: C1-SOLO-FINAL-CLEANUP
c0_result: COMPLETED / USER_APPROVED
c1_prep_v1_status: SUPERSEDED / HISTORICAL_ONLY
c1_execution_model: SINGLE_LOCAL_RUNNER
c1_solo_plan_version: cafef_c1_solo_v2
pilot_security_count: 27
collection_end_date: 2026-09-23
history_policy: FULL_AVAILABLE_UP_TO_MAX_15Y
priority_policy: CAFEF_C1_SOLO_PRIORITY_V2
c1_actual_crawl_executed: NO
data_crawl_executed: NO
market_data_requests_for_experiment: 0
market_data_requests_in_corrective_stage: 0
actual_market_data_requests: 0
actual_crawl_executed: NO
c1_solo_runner_contract_corrected: YES
exchange_type_contract_aligned: YES
historical_identity_interval_routing: YES
envelope_success_validation: YES
verified_pricehistory_endpoint_aligned: YES
failed_response_evidence_preserved: YES
canonical_mutation: NO
canonical_mutations: 0
feature_rebuild: NO
five_worker_execution: DEFERRED_TO_C4_PREP_SCALE
why: C1-PREP v1 was preserved as history; the active representative pilot now uses one frozen resumable local run
next_allowed_action: USER MANUAL REVIEW BEFORE C1-SOLO EXECUTION
after_explicit_user_approval: USER MAY RUN C1-SOLO LOCALLY
c1_prep_solo_crawl_execution: NO
user_manual_review_required: YES
```

Tài liệu này là source of truth cho nhánh thử nghiệm. Không được suy approval từ việc
branch tồn tại, từ việc C0 đã commit, hoặc từ kết quả thuận lợi của bất kỳ bằng chứng cũ
nào.

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
| C1-SOLO | Representative CafeF raw-market acquisition | NOT AUTHORIZED | reviewed solo plan + explicit approval |
| C2 | Corporate-action evidence and DELTA adjustment prototype | NOT AUTHORIZED | reviewed event/policy contract |
| C3 | KBS-vs-CafeF comparative audit | NOT AUTHORIZED | measured comparable outputs |
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

## 17. Current status / Handoff

```yaml
stage: C1-SOLO-FINAL-CLEANUP
status: COMPLETED / USER_MANUAL_REVIEW_REQUIRED
documents:
  - docs/crawl/CAFEF_PRIMARY_EXPERIMENT_PLAN.md
  - docs/crawl/CAFEF_PRIMARY_MIGRATION_AUDIT.md
  - docs/crawl/CAFEF_PRIMARY_C1_CRAWL_PLAN.md
planning_artifact_directory: docs/crawl/plans/cafef_c1_solo_v2
historical_planning_artifact_directory: docs/crawl/plans/cafef_c1_prep_v1
offline_planner: scripts/plan_cafef_c1_solo.py
solo_runner: scripts/run_cafef_c1_solo.py
execution_model: SINGLE_LOCAL_RUNNER
data_crawl_executed: NO
market_data_requests_for_experiment: 0
actual_market_data_requests: 0
actual_crawl_executed: NO
c1_solo_runner_contract_corrected: YES
exchange_type_contract_aligned: YES
historical_identity_interval_routing: YES
envelope_success_validation: YES
verified_pricehistory_endpoint_aligned: YES
failed_response_evidence_preserved: YES
canonical_mutations: 0
feature_rebuild: NO
five_worker_execution: DEFERRED_TO_C4_PREP_SCALE
pilot_security_count: 27
parallel_requests: NO
collection_end_date: 2026-09-23
history_policy: FULL_AVAILABLE_UP_TO_MAX_15Y
priority_policy: CAFEF_C1_SOLO_PRIORITY_V2
next_allowed_action: USER MANUAL REVIEW BEFORE C1-SOLO EXECUTION
forbidden_until_explicit_approval:
  - any crawl
  - C1-SOLO
after_explicit_user_approval: USER MAY RUN C1-SOLO LOCALLY
```

STOP after C1-SOLO-FINAL-CLEANUP. Do not execute C1-SOLO without explicit user approval.
