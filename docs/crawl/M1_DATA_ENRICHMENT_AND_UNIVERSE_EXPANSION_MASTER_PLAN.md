# DELTA — M1 Data Enrichment & Universe Expansion Master Plan

> **Project:** Risk-Adjusted Momentum Clustering for Vietnamese Stocks  
> **Scope:** M1 Data Foundation → M2 Research Dataset  
> **Document type:** Master Execution Plan / Source of Truth  
> **Execution model:** Read handoff → Implement one stage → Test → Self-review → Update handoff → Stop
> **Core principle:** mở rộng dữ liệu mạnh nhất có thể nhưng không đánh đổi tính đúng đắn, khả năng audit và methodology.

---

## Execution Progress / Handoff

Last updated: 2026-09-23 (A5-R1.1 CafeF deep discovery)
Branch: `m1-scale-500-team-crawl`
Reference HEAD: `d424de63d2cfe1197e9f3c96a505e3d17b8723f2`

Current initiative: M1 Data Enrichment & Universe Expansion
Last completed stage: A5-R1.1 CafeF Deep Discovery & Evidence Expansion
Stage result: `PARTIAL / MANUAL_REVIEW_REQUIRED`

Latest run/artifact: `m1-a5-r1-1-cafef-deep-discovery-20260922T185753Z-326612f7`

Key evidence:

- Baseline: `canonical-m1-scale-20260918T141019Z-7c003543`; 500 securities; 614,430 daily rows.
- Baseline/latest market-feature-ready: 169 at completed snapshot `2026-08-28`; no recovery gain is accepted.
- A2 executed: local salvage produced no accepted recovery. A3 pilot executed: no scalable primary path established.
- A4 executed: 9 CafeF provider rows have diagnostic ratio matches, but remain non-promotable pending field/price-basis contract.
- A5-R1 executed 11 bounded public CafeF requests across HOSE/HNX/UPCOM, an older corporate-action window, page 2, an explicit provider-published zero-volume row and invalid tickers.
- `TradeHistoryNew.ashx` and `DataHistory/PriceHistory.ashx` are complementary, not equivalent. Field names/units/date behavior are versioned in `cafef-a5-r1-contract-1.0.0`.
- A5-R1.1 used Computer Use plus 47 bounded public requests in total (45 immutable raw responses in the final artifact and two schema-confirmation GETs) across FPT, VNM, VCB, PVS, ACV, HND and KHP.
- Sample market history returned January-2020 rows across HOSE/HNX/UPCOM. This is a 5+ year signal for the sample, not a current-500 completeness claim.
- Price-basis result remains `DIAGNOSTIC_ONLY`: CafeF adjusted values are not demonstrably equivalent to the current KBS/canonical `vendor_adjusted` basis, and no multiplier or transformation is approved. `PRICE_BASIS_UNRESOLVED` remains in force.
- Financial BS/IS summary history is substantial in the five-company probe (44–86 quarterly periods and 14–21 annual periods). Cash Flow is visible in the UI, but the live `reportType=LCTT` summary request returned an empty payload for every sample.
- CafeF document rows expose document IDs, scope and audit/review labels, including same-period initial/reviewed documents. They do not expose verified first-public time, timezone, supersession, or a stable fact-to-document join.
- Financial conclusions are separate: `FINANCIAL_DATA_AVAILABILITY=PARTIAL`, `FINANCIAL_HISTORY_COVERAGE=SAMPLE_ONLY`, `FINANCIAL_PIT_READINESS=NOT_READY`; historical facts remain excluded from research/backtest.
- Corporate-action, first-trading-date/current-capital and HOSE holiday-notice evidence is useful with limitations; no complete historical capital/status series or price transform is approved.
- CafeF rows remain non-promotable; canonical mutations, synthetic rows and imputed rows are all zero. The 20-before + 20-after rule is unchanged.
- A6/A6.1 artifacts, Canonical Enriched v2, Feature Rebuild and EDA are preserved as interim current-500 / identity-corrected evidence; they are not final initiative outputs.
- No forward/back-fill, interpolation, previous-close substitution, missing-to-zero, synthetic OHLC/volume, or zero-return session is allowed.
- B0–B5 are NOT STARTED and B0 is blocked by the A5 remediation gate.
- Prior A5-R1 corrective verifier/methodology-auditor PASS evidence is preserved; A5-R1.1 was self-reviewed without delegating or executing another stage.

Unresolved blockers:
- CafeF OHLC/adjusted-price basis is not approved; CafeF adjustment methodology is undocumented in available evidence.
- CafeF automated recovery/data rights remain `RIGHTS_NOT_VERIFIED`.
- `FACT_DOCUMENT_JOIN_UNRESOLVED` and `REVISION_CHAIN_UNRESOLVED`.
- Financial `available_at`, timezone, stable report/version identity and complete period boundaries remain unresolved.
- Cash Flow fact endpoint/coverage and Q2/Q3 duration semantics remain unresolved.

Manual review required: `YES` — price-basis/source-use acceptance is methodology-sensitive.

Next allowed market action: `A5-R4 — Additional Market Source Discovery`, after manual review. A5-R2 remains `BLOCKED` because no promotable CafeF market-recovery contract exists.

Next allowed financial action: `F0 — Financial Source Re-discovery`. F1/F2 are planned gates only and were not executed.

| Stage | Status | Evidence / Run | Notes |
|---|---|---|---|
| A1 Missing Session Audit | PASS | `m1-a1-missing-session-audit-20260921T045214Z-b0e8d931` | Baseline evidence retained. |
| A2 Local Salvage | EXECUTED | A2 evidence | No accepted recovery. |
| A3 Primary Recovery Pilot | EXECUTED | A3 evidence | No scalable primary-recovery path established. |
| A4 Secondary Recovery Pilot | EXECUTED; REMEDIATION REQUIRED | A4 evidence | Nine diagnostic CafeF candidates; no approved canonical promotion. |
| A5-R1 CafeF Contract Validation | PARTIAL / MANUAL_REVIEW_REQUIRED | `m1-a5-r1-cafef-contract-20260922T174031Z-35a27f92` | 11 requests; field contract versioned; price basis and rights unresolved; no promotion. |
| A5-R1.1 CafeF Deep Discovery | PARTIAL / MANUAL_REVIEW_REQUIRED | `m1-a5-r1-1-cafef-deep-discovery-20260922T185753Z-326612f7` | Computer Use + bounded public evidence; market cross-check only; financial raw only; PIT not ready. |
| A5-R2 Multi-source Near-Ready Pilot | BLOCKED | — | No explicit, versioned and promotable market-recovery contract exists. |
| A5-R3 Full Current-500 Recovery | NOT_STARTED | — | May follow only a successful A5-R2. |
| A5-R4 Additional Market Source Discovery | NOT_STARTED / NEXT_ALLOWED_AFTER_MANUAL_REVIEW | — | Selected next market action; not executed in A5-R1.1. |
| A5 Full Recovery Current 500 | BLOCKED / REMEDIATION REQUIRED | — | A5-R2/A5-R3 not executed. |
| A6 / A6.1 Identity work | EXECUTED / EVIDENCE RETAINED | A6 evidence | Preserve identity evidence and audit it; not an A5 bypass. |
| Canonical Enriched v2 / Feature Rebuild / EDA | INTERIM EVIDENCE | `canonical-m1-scale-enriched-v2-20260921T141356Z-ec87b5d8` | Current-500 identity-corrected outputs only. |
| F0–F2 Financial/PIT remediation | NOT_STARTED | — | F0 is next allowed financial action; financial raw remains PIT-ineligible. |
| B0–B5 | NOT_STARTED / BLOCKED BY A5 GATE | — | B0 remains blocked. |

---

# 1. Mục đích

Tài liệu này là master plan chính thức cho toàn bộ giai đoạn tiếp theo của Data Foundation.

Mọi agent thực hiện task liên quan đến Data Enrichment, Missing Session Recovery, Universe Expansion, Canonicalization, Feature Rebuild hoặc Data Quality phải đọc tài liệu này trước khi code.

Tài liệu giải quyết đồng thời hai vấn đề:

1. Universe hiện tại chỉ có 500 securities và chưa đáp ứng đủ yêu cầu mở rộng dữ liệu.
2. Nhiều securities hiện tại bị thiếu trading-session observations nên không đủ điều kiện tính feature theo hard rule 100% required observations.

Initiative phải giải quyết cả hai:

```text
CURRENT DATASET
500 securities
169 market-feature-ready
        │
        ├── Workstream A: enrich/recover current 500
        │
        └── Workstream B: expand universe
                    ↓
                ~1,000
                    ↓
                 1,200+
                    ↓
        Canonical Enriched Dataset
                    ↓
             Feature Rebuild
                    ↓
                   EDA
                    ↓
          Freeze M2 Research Sample
```

---

# 2. Current Baseline

Baseline hiện tại phải được giữ immutable.

Current statistics:

| Metric | Current |
|---|---:|
| Selected securities | 500 |
| Daily market rows | 614,430 |
| Observed span ≥ 3 years | 500 |
| Observed span ≥ 5 years | 484 |
| Momentum 21 available | 213 |
| Momentum 63 available | 193 |
| Momentum 126 available | 184 |
| Momentum 252 available | 169 |
| Market-feature-ready | 169 |
| Canonical Market Data | PASS |
| Strict Research Gate | PARTIAL |

Latest completed research snapshot:

```text
2026-08-28
```

Known unresolved blockers:

```text
Historical Identity
Financial PIT
Final Research Sample Policy
```

Baseline phải được xem là:

```text
READ ONLY
```

Không stage nào được overwrite hoặc mutate baseline canonical.

---

# 3. Initiative Objectives

## 3.1 Recover current dataset

Phục hồi tối đa các real observations đang bị thiếu trong 500 securities hiện tại.

Nguồn phục hồi có thể đến từ:

- existing raw payloads;
- quarantine;
- failed/interrupted runs;
- primary provider retry;
- alternate acquisition path;
- CafeF;
- validated secondary providers;
- historical identity recovery.

Không tạo synthetic rows.

---

## 3.2 Expand universe

Current:

```text
500
```

Intermediate target:

```text
~1,000 securities
```

Extended target:

```text
1,200+ securities
```

Target 1,000 là checkpoint chính.

1,200+ chỉ thực hiện nếu:

- candidate pool đủ lớn;
- provider coverage ổn;
- identity mapping đủ chắc;
- runtime/storage hợp lý;
- additional securities vẫn tăng research usability.

Không được hiểu:

```text
1,000 acquired
=
1,000 research-ready
```

Phải luôn báo cáo theo funnel:

```text
DISCOVERED
↓
ACQUIRED
↓
CANONICAL VALID
↓
>=3 YEARS
↓
>=5 YEARS
↓
COMPLETE REQUIRED SESSIONS
↓
MARKET FEATURE READY
↓
RESEARCH READY
```

---

# 4. Market Representation Objective

Current universe có khả năng đang thiếu nhiều mã quan trọng hoặc nhiều mã "hot" trên thị trường.

Vì vậy acquisition/recovery phải ưu tiên các securities:

- high liquidity;
- high traded value;
- active trading frequency cao;
- major index constituents;
- market-important names;
- long listing history;
- good provider coverage;
- currently missing but relevant names;
- securities đã có partial raw data.

Tuy nhiên:

```text
HOT / POPULAR / HIGH LIQUIDITY
```

chỉ dùng để:

```text
ACQUISITION PRIORITY
```

Không được dùng trực tiếp để:

```text
RESEARCH ELIGIBILITY
CLUSTER MEMBERSHIP
MODEL SELECTION
PORTFOLIO SELECTION
```

---

# 5. Hard Methodology Rules

Các rule dưới đây là non-negotiable trong initiative này.

---

## 5.1 100% Required Session Observations

Rolling feature chỉ hợp lệ khi có 100% required real observations.

Ví dụ:

```text
Momentum 21
→ required 21-session observation structure complete

Momentum 63
→ required 63-session observation structure complete

Momentum 126
→ required 126-session observation structure complete

Momentum 252
→ required 252-session observation structure complete
```

Không được tự thay thành:

```text
80%
90%
95%
min_periods
partial windows
```

để tăng sample.

---

## 5.2 No Market Data Imputation

Forbidden:

```text
forward-fill
backward-fill
linear interpolation
spline interpolation
previous-close substitution
missing price -> 0
missing volume -> 0
synthetic OHLC
synthetic volume
fake zero-return day
timeline compression
```

Không được:

```text
100
missing
104
→ 102
```

Không được:

```text
100
missing
→ 100
```

chỉ để complete feature window.

---

## 5.3 Recovery Must Use Real Evidence

Một missing observation chỉ được phục hồi trong hai trường hợp.

### Case A — Provider evidence

Một provider khác có valid real observation.

Ví dụ:

```text
KBS       missing
CafeF     valid row
Provider2 valid matching row
```

Nếu:

- date đúng;
- identity đúng;
- unit đúng;
- price basis compatible;
- provenance đầy đủ;

thì có thể promote.

### Case B — Existing raw observation

Raw observation thực sự đã tồn tại nhưng bị mất do:

```text
parser bug
timezone bug
unit conversion
snapshot classification
duplicate handling
identity mapping
adapter bug
normalization bug
```

Nếu raw evidence chứng minh được row thật tồn tại thì được salvage.

---

# 6. Baseline Immutability

Architecture:

```text
OLD CANONICAL
    │
    └── READ ONLY

RECOVERY DATA
    ↓
RECONCILIATION
    ↓
NEW CANONICAL VERSION
```

Naming:

```text
m1-enrichment-<timestamp>-<id>

canonical-m1-enriched-<timestamp>-<id>
```

Không overwrite old artifacts.

---

# 7. Provenance Requirements

Mỗi recovered observation phải trace được nguồn.

Required metadata tối thiểu:

```text
security_id
source_symbol
exchange
trading_date

provider
client_or_adapter
endpoint_or_acquisition_path

fetched_at
raw_hash
adapter_version

recovery_run_id
recovery_reason
reconciliation_rule_id
```

Không provenance:

```text
DO NOT PROMOTE
```

---

# 8. Source Roles

## 8.1 KBS

KBS là data provider.

Current role:

```text
Primary market OHLCV candidate
VNINDEX / benchmark candidate
Financial structure candidate
```

KBS có thể được access thông qua client/library khác.

---

## 8.2 Vnstock

Vnstock là acquisition client/library.

Không coi Vnstock là provider nếu underlying source thực tế là KBS.

Preferred provenance:

```text
provider = KBS
client = Vnstock
```

---

## 8.3 CafeF

Useful roles:

```text
historical cross-check
reference price
ceiling
floor
traded value
put-through fields
corporate-action evidence
secondary historical observations
```

CafeF-specific date/unit semantics phải tuân theo adapter rules hiện tại.

---

## 8.4 Additional Provider

Có thể sử dụng SSI hoặc nguồn khác nếu được validate.

Provider mới phải qua:

```text
SOURCE DISCOVERY
↓
ACCESS TEST
↓
FIELD MAPPING
↓
DATE VALIDATION
↓
UNIT VALIDATION
↓
PRICE BASIS VALIDATION
↓
SOURCE SMOKE
↓
PILOT
```

Không scale provider chưa được validate.

---

# 9. Provider Rights / Access Rule

Initiative nằm trong:

```text
bounded academic research
```

Không implement:

```text
CAPTCHA bypass
Cloudflare bypass
authentication bypass
session-token bypass
proxy evasion
anti-bot evasion
```

Nếu provider chặn automated access:

```text
ACCESS_BLOCKED
```

và dừng source đó.

---

# 10. Expected Session Definition

Missing-session recovery phụ thuộc vào expected-session definition.

Không được định nghĩa:

```text
exchange session exists
+
security row missing
=
provider gap
```

Expected session phải dựa trên:

```text
exchange session
AND
active listing interval
AND
effective identity interval
```

---

# 11. Exchange Calendar

Preferred hierarchy:

```text
official exchange calendar
↓
validated provider calendar
↓
canonical observed exchange-session union
```

Nếu chỉ sử dụng observed union:

```text
calendar_status = PROVISIONAL_OBSERVED
```

Không gọi nó là official calendar.

---

# 12. Listing Boundary

Nếu:

```text
date < listing_date
```

→

```text
NOT_LISTED
```

Không tính là missing.

Nếu:

```text
date > delisting_date
```

→

```text
DELISTED
```

Không tính là missing.

---

# 13. Suspension / Halt

Không tạo synthetic observation cho suspended security.

Nếu exchange session tồn tại nhưng không có real valid row:

```text
feature remains incomplete
```

trừ khi official/provider source publish valid daily observation.

---

# 14. No-Trade Session

Không tự tạo:

```text
close = previous_close
volume = 0
```

Nếu provider thật sự publish daily record:

→ validate và dùng.

Nếu không:

```text
missing remains missing
```

---

# 15. Missing Classification Taxonomy

Allowed classes:

```text
PROVIDER_GAP_CANDIDATE

PROVIDER_GAP_CONFIRMED

PARSER_OR_NORMALIZATION_CANDIDATE

IDENTITY_GAP_CANDIDATE

NOT_LISTED

DELISTED

SUSPENDED_OR_HALTED

CALENDAR_UNCERTAIN

MISSING_ON_PRIMARY

MISSING_ON_SECONDARY

MISSING_ALL_SOURCES

VALUE_CONFLICT

UNIT_CONFLICT

PRICE_BASIS_CONFLICT

TIMING_CONFLICT

IDENTITY_CONFLICT

UNRESOLVED_MISSING
```

Không được classify thành:

```text
PROVIDER_GAP_CONFIRMED
```

chỉ vì canonical hiện tại thiếu.

---

# 16. Overall Architecture

```text
                         SECURITY MASTER
                               │
                               ▼
                        SESSION CALENDAR
                               │
                               ▼
CURRENT CANONICAL ─────► EXPECTED SESSION GRID
                               │
                               ▼
                       MISSING SESSION AUDIT
                               │
        ┌──────────────────────┼───────────────────────┐
        │                      │                       │
        ▼                      ▼                       ▼
 LOCAL RAW SALVAGE      PRIMARY RECOVERY       IDENTITY RECOVERY
        │                      │                       │
        └──────────────┬───────┴──────────┬────────────┘
                       │                  │
                       ▼                  ▼
                 SECONDARY RECOVERY
                       │
                       ▼
               FIELD RECONCILIATION
                       │
                       ▼
                ENRICHED CANONICAL
                       │
                       ▼
                 FEATURE REBUILD
                       │
                       ▼
                  READINESS EDA
                       │
                       ▼
                M2 SAMPLE FREEZE
```

Universe expansion song song:

```text
UNIVERSE DISCOVERY
       ↓
CANDIDATE FILTERING
       ↓
MARKET PRIORITY RANKING
       ↓
SOURCE SMOKE
       ↓
REPRESENTATIVE PILOT
       ↓
SCALE ~1,000
       ↓
OPTIONAL 1,200+
       ↓
CANONICAL MERGE
```

---

# 17. Workstream A — Current 500 Enrichment

---

# Stage A0 — Freeze Baseline

## Goal

Tạo immutable benchmark để đo before/after.

## Record

```text
canonical artifact id
quality artifact id

collection start
collection end

latest completed snapshot

security count
price rows
benchmark rows
feature snapshot rows

feature availability
market_feature_ready
```

## Hash

Hash critical inputs:

```text
canonical manifest
market-data artifact
feature artifact
quality artifact
```

## Outputs

```text
artifacts/data_enrichment/<run_id>/
    baseline_summary.json
    baseline_hashes.json
    stage_a0_report.md
```

## Gate

PASS nếu:

- baseline uniquely identified;
- hashes recorded;
- zero mutation;
- zero network.

---

# Stage A1 — Missing Session Audit

## Goal

Giải thích chính xác 331 current non-ready securities.

Hard scope:

```text
NO NETWORK
NO RECOVERY
NO BACKFILL
NO CANONICAL MUTATION
```

---

## A1.1 Build Expected Session Grid

For every security:

```text
active identity interval
×
exchange sessions
```

Recommended schema:

```text
security_id
ticker
exchange

session_date

listing_date
delisting_date

identity_effective_from
identity_effective_to

expected_session

calendar_status
identity_status
```

---

## A1.2 Compare Expected vs Observed

Create:

```text
expected_session
observed_session
missing_flag
```

---

## A1.3 Missing Audit Schema

```text
security_id
ticker
exchange
trading_date

expected_session
observed_session

missing_classification

latest_21_relevant
latest_63_relevant
latest_126_relevant
latest_252_relevant
latest_300_relevant

canonical_source
identity_status
calendar_status
```

---

## A1.4 Per-Security Metrics

Calculate:

```text
expected_sessions_total

observed_sessions_total

missing_sessions_total

coverage_ratio
```

Latest feature windows:

```text
missing_last_21

missing_last_63

missing_last_126

missing_last_252

missing_last_300
```

Gap structure:

```text
max_consecutive_missing

first_missing_date

last_missing_date

missing_range_count
```

Readiness:

```text
mom21_complete

mom63_complete

mom126_complete

mom252_complete

market_feature_ready
```

---

# 18. Recovery Priority Buckets

Every non-ready security phải được rank.

## P0 — Near Ready

```text
1–5 missing sessions
within latest required 252-session window
```

Highest priority.

---

## P1

```text
6–20 missing
```

---

## P2

```text
21–63 missing
```

---

## P3

```text
>63 missing
```

---

## P4 — Structural Investigation

Examples:

```text
extreme sparse history

identity uncertainty

listing mismatch

exchange transfer

provider-symbol mismatch

calendar anomaly

coverage extremely low
```

Example:

```text
>5 calendar years
but ~55 observed rows
```

Không blind-backfill.

---

# 19. Stage A1 Outputs

```text
missing_session_audit.parquet

missing_session_by_symbol.csv

missing_session_by_date.csv

recovery_priority.csv

missing_classification_summary.json

stage_a1_report.md
```

---

# 20. Stage A1 Mandatory Questions

Report phải trả lời:

1. P0 count?
2. P1 count?
3. P2 count?
4. P3 count?
5. P4 count?
6. Bao nhiêu security chỉ thiếu 1 session?
7. Bao nhiêu thiếu <=5?
8. Bao nhiêu thiếu <=20?
9. Exchange nào missing nhiều?
10. Missing tập trung ở year/month nào?
11. Có provider-specific pattern không?
12. Top 50 easiest recoveries?
13. Top market-important non-ready securities?
14. Securities nào gần như structural?
15. Theoretical max readiness nếu confirmed provider gaps được recover?
16. Securities nào không đáng tiếp tục recovery?

Sau report:

```text
STOP
```

---

# Stage A2 — Local Raw / Quarantine Salvage

## Goal

Cứu real observations đã tồn tại local trước khi gọi network.

Audit:

```text
data/raw

quarantine

failed runs

interrupted runs

old source-smoke runs

old pilot runs

old scale runs

secondary raw payloads
```

---

# 21. Local Salvage Investigation

Known issue classes:

```text
legacy date parsing

UTC/local date conversion

DateTime.MinValue snapshot sentinel

snapshot-position classification

unit normalization

duplicate provider rows

security-symbol mapping

provider-specific row format

old adapter behavior
```

---

# 22. Salvage Acceptance Rule

Accept only when:

```text
real raw evidence exists

AND

date semantics supported

AND

unit supported

AND

security identity supported

AND

price basis supported
```

Otherwise:

```text
REJECT
```

---

# 23. Stage A2 Outputs

```text
local_salvage_candidates.parquet

local_salvage_accepted.parquet

local_salvage_rejected.parquet

stage_a2_report.md
```

Report:

```text
candidate rows

accepted rows

rejected rows

symbols improved

newly complete windows

root causes
```

STOP.

---

# Stage A3 — Primary Provider Recovery Pilot

## Goal

Determine how many missing observations are recoverable from primary provider.

Sample:

```text
10–20 securities
```

Must include:

```text
P0
P1
P2

HOSE
HNX
UPCOM

HIGH market-priority names

normal controls

1–2 sparse/P4 controls
```

---

# 24. Request Strategy

Do not refetch entire history if only a few sessions are missing.

Example:

```text
Missing:
2025-03-10
2025-03-11
2025-04-02
```

Convert to:

```text
2025-03-10 -> 2025-03-11
2025-04-02 -> 2025-04-02
```

Use bounded recovery ranges.

---

# 25. Primary Recovery Hierarchy

Preferred:

```text
PRIMARY PROVIDER RETRY
↓
SAME PROVIDER ALTERNATE ACQUISITION PATH
```

before switching provider.

Example:

```text
KBS via current client
↓
KBS via validated alternate path
```

---

# 26. Stage A3 Outputs

```text
primary_recovery_requests.jsonl

primary_recovery_raw/

primary_recovery_candidates.parquet

primary_recovery_results.csv

stage_a3_report.md
```

Metrics:

```text
requests attempted

requests successful

rows requested

rows recovered

rows unresolved

recovery rate

securities improved

securities newly ready
```

STOP.

---

# Stage A4 — Secondary Source Recovery Pilot

## Goal

Recover rows primary source cannot recover.

Default order:

```text
PRIMARY RETRY
↓
SAME-PROVIDER ALTERNATE PATH
↓
CAFEF
↓
VALIDATED SECONDARY PROVIDER
↓
UNRESOLVED
```

Do not hardcode a secondary provider before validation.

---

# 27. Secondary Candidate Validation

Each candidate row must validate:

```text
security identity

trading date

open

high

low

close

volume

units

price basis

provider timestamp

provenance
```

---

# 28. Reconciliation Status

Allowed statuses:

```text
MATCH

RECOVERED_PRIMARY

RECOVERED_SECONDARY_CONFIRMED

MISSING_ON_SOURCE

VALUE_CONFLICT

UNIT_CONFLICT

PRICE_BASIS_CONFLICT

TIMING_CONFLICT

IDENTITY_CONFLICT

UNRESOLVED_MISSING
```

Never:

```text
average(provider A, provider B)
```

---

# 29. Price Basis Validation

Critical for Momentum.

Before promotion, compare overlapping regions:

```text
~20 sessions before gap
+
~20 sessions after gap
```

Check:

```text
primary_close / secondary_close
```

If relationship is consistent:

```text
compatible candidate
```

If ratio shifts around corporate action or differs structurally:

```text
PRICE_BASIS_CONFLICT
```

Do not promote.

---

# 30. Stage A4 Outputs

```text
secondary_recovery_requests.jsonl

secondary_recovery_evidence.jsonl

secondary_recovery_candidates.parquet

reconciliation_report.json

stage_a4_report.md
```

STOP.

---

# Stage A5 — Full Recovery Current 500

After pilots PASS:

```text
P0
↓
P1
↓
P2
↓
P3
↓
P4 investigation
```

Within each bucket:

```text
HIGH market priority
↓
MEDIUM
↓
NORMAL
```

---

# 31. Recovery Pass 1 — Latest Window First

Prioritize:

```text
latest ~300 exchange sessions
```

Reason:

Current largest latest-feature bottleneck:

```text
Momentum 252
```

Fast objective:

```text
169 market-feature-ready
↓
NEW MEASURED COUNT
```

No artificial target.

---

# 32. Recovery Pass 2 — Historical Repair

After latest-window recovery:

Deep-repair history only for securities that:

- have valid identity;
- have adequate provider support;
- have sufficient history;
- have likely research value;
- can realistically enter final sample.

Do not spend disproportionate resources repairing unusable symbols.

---

# 33. Stage A5 Outputs

```text
recovery_evidence.jsonl

recovery_summary.csv

unresolved_missing.csv

current500_enriched_candidate.parquet

stage_a5_report.md
```

---

# 34. Current-500 Before/After Report

Required:

| Metric | Before | After |
|---|---:|---:|
| Price rows | 614,430 | ? |
| Momentum 21 | 213 | ? |
| Momentum 63 | 193 | ? |
| Momentum 126 | 184 | ? |
| Momentum 252 | 169 | ? |
| Market-feature-ready | 169 | ? |

Do not force:

```text
ready = 300
```

Final value must result from real evidence.

---

# A5 Remediation Track — mandatory before Workstream B

Stage A5 is **BLOCKED / REMEDIATION REQUIRED**. It must not mutate canonical data,
infer rows, or use imputation. B0 remains blocked until the applicable remediation,
manual-decision and pilot/report gates establish a deterministic, versioned recovery
system.

Effective remediation sequence:

```text
A5-R1 CafeF Contract & Endpoint Validation
  -> A5-R1.1 CafeF Deep Discovery & Evidence Expansion
  -> MANUAL REVIEW / DECISION GATE
       -> promotable market contract exists: A5-R2 -> successful pilot: A5-R3
       -> no promotable market contract: A5-R4
```

## A5-R1 — CafeF Contract & Endpoint Validation

**No canonical mutation.** Validate each known public historical path, including
`TradeHistoryNew.ashx` and `DataHistory/PriceHistory.ashx` where applicable; do not
assume their semantics are equivalent. Record ticker/exchange identity, trade-date
meaning, open/high/low/close/adjusted price, matched volume/value, negotiated
volume/value, units, pagination, snapshot-versus-historical rows, corporate-action
behavior and relation to the KBS canonical adjusted-price basis. Required outputs:
`cafef_endpoint_comparison.json`, `cafef_field_contract.json`,
`cafef_validation_evidence.jsonl`, `cafef_price_basis_diagnostics.csv`, and
`stage_a5_r1_report.md`. PASS means the permitted fields, basis, limitations and
acceptance contract are precise and versioned; it does not promote any row.

## A5-R1.1 — CafeF Deep Discovery & Evidence Expansion

### Goal

Expand CafeF evidence across historical market data; financial statements; financial
documents and PIT timing; corporate actions; security identity and capital history;
suspension, delisting and trading-status evidence; and trading-calendar notices.
This is an evidence/discovery stage. It does not mutate canonical data, recover missing
market rows, approve price transformations, crawl the full current-500 universe, start
universe expansion, or create PIT financial facts without verified timing.

### Inputs

- A5-R1 artifacts and the current canonical baseline;
- existing CafeF source documentation and P0 Financial PIT evidence;
- legitimate public CafeF UI and endpoints.

### Required outputs

`cafef_surface_catalog.json`, `cafef_endpoint_catalog.json`,
`cafef_field_catalog.csv`, `cafef_market_contract_extension.json`,
`cafef_financial_contract_draft.json`, `cafef_financial_coverage_probe.csv`,
`cafef_pit_timing_evidence.jsonl`, `cafef_revision_evidence.jsonl`,
`cafef_fact_document_join_evidence.jsonl`,
`cafef_corporate_action_contract.json`, `cafef_identity_capital_evidence.jsonl`,
`cafef_status_calendar_evidence.jsonl`, `cafef_deep_discovery_report.md`, and
`manifest.json`.

### Market decision gate

A5-R2 may start only if discovery plus manual review establishes an explicit,
versioned and promotable recovery contract. If CafeF remains non-promotable, A5-R2
stays BLOCKED and the next market action is A5-R4 — Additional Market Source
Discovery. Historical A5-R1 evidence remains immutable and is not rewritten.

### Financial decision gate

Financial findings are evaluated separately from market recovery. The stage reports
`FINANCIAL_DATA_AVAILABILITY`, `FINANCIAL_HISTORY_COVERAGE` and
`FINANCIAL_PIT_READINESS` independently. Historical financial facts may not enter
research/backtest until period identity, report identity, `available_at`, timezone
semantics, and revision/version safety are sufficiently resolved.

## A5-R2 — Multi-source Near-Ready Recovery Pilot

Derive the full near-ready cohort from latest A1/A5 evidence: all non-ready securities
with <=20 missing sessions in the relevant latest feature window; never hard-code the
count or choose 12 arbitrary symbols. For every target, try KBS first, then an
**approved** CafeF historical path if no valid real KBS row exists, and validate it.
Every target ends deterministically as `PRIMARY_REAL_ROW`, `SECONDARY_REAL_ROW`,
`SECONDARY_PROVIDER_PUBLISHED_ZERO_VOLUME_ROW`, `NO_ROW_PRIMARY`,
`NO_ROW_SECONDARY`, `PRICE_BASIS_CONFLICT`, `IDENTITY_CONFLICT`,
`FIELD_CONTRACT_UNSUPPORTED`, `CALENDAR_OR_STATUS_STRUCTURAL`, or `UNRESOLVED`.
Report target gaps, real rows per source, provider-published zero-volume rows, full
contract passes, rejections, unresolved rows, securities improved, new
Momentum252-complete securities, and market-feature-ready before/after. The existing
20-before + 20-after rule remains fail-closed; any one-sided or corporate-action
alternative needs explicit methodology justification, tests, versioned policy and
`MANUAL_REVIEW_REQUIRED` before it may accept a row.

## A5-R3 — Full Current-500 Recovery

May run only after A5-R2 demonstrates a valid deterministic path. Apply exactly the
approved pilot rules to remaining recoverable current-500 gaps; do not change rules to
improve yield. Attribute baseline ready + local salvage gain + KBS primary gain + CafeF
secondary gain + identity recovery gain = current-500 final ready. No universe
expansion gain belongs in this stage.

## A5-R4 — Additional Market Source Discovery, only if required

If KBS and approved CafeF paths remain insufficient, validate one additional provider
at a time through source discovery, access/rights review, field/date/unit/price-basis
validation, source smoke and recovery pilot. A provider is never active merely because
it has more rows; do not bypass login, access control, anti-bot, CAPTCHA or paywalls.

## Gate to Workstream B

B0 may begin only when multi-source recovery semantics are frozen, no synthetic or
imputed market rows are used, provider contracts are versioned, recovery/rejection is
deterministic, unresolved gaps have explicit classifications, the near-ready pilot is
complete, current-500 cost/yield is measured, and an A5 final report exists.

# Stage A6 — Historical Identity Recovery

## Goal

Recover history lost because of:

```text
ticker rename

exchange transfer

historical ticker alias

provider symbol change
```

---

# 35. Identity History Schema

```text
security_id

ticker

exchange

effective_from

effective_to

evidence_source

evidence_reference

identity_confidence
```

Example:

```text
SEC001 | OLD | HNX  | 2019-01-01 | 2022-07-10
SEC001 | NEW | HOSE | 2022-07-11 | NULL
```

Both map to:

```text
SEC001
```

---

# 36. Identity Rules

Never merge based on company-name similarity alone.

Need evidence.

Never use:

```text
current ticker
```

as historical identity for entire history.

---

# 37. Stage A6 Outputs

```text
security_identity_history.parquet

identity_recovery_candidates.csv

identity_recovery_evidence.jsonl

stage_a6_report.md
```

STOP.

---

# 38. Workstream B — Universe Expansion

Current 500 universe must be expanded substantially.

Main target:

```text
~1,000
```

Extended target:

```text
1,200+
```

---

# Stage B0 — Candidate Universe Discovery

## Goal

Build candidate pool larger than final target.

Recommended candidate pool:

```text
1,300–1,500 securities
```

before filtering/ranking.

---

# 39. Candidate Sources

Possible sources:

```text
provider security master

exchange security lists

existing partial raw symbols

validated index memberships

recent market universe

other validated symbol lists
```

---

# 40. Supported Instrument Scope

Primary scope:

```text
Vietnam listed equities
```

Separate or exclude:

```text
ETFs

funds

bonds

derivatives

warrants

invalid/test symbols
```

unless explicitly added to research scope.

---

# 41. Candidate Deduplication

Do not deduplicate using ticker only.

Preferred:

```text
security_id
```

Need account for:

```text
ticker rename

exchange transfer

historical ticker reuse
```

---

# 42. Stage B0 Outputs

```text
universe_candidates.parquet

universe_candidate_summary.json

stage_b0_report.md
```

Report:

```text
candidate count

exchange distribution

estimated old/new listings

baseline overlap

identity uncertainty

provider availability
```

STOP.

---

# Stage B1 — Market Priority Ranking

## Goal

Ensure relevant/active securities are acquired first.

This is:

```text
ACQUISITION PRIORITY SCORE
```

It is NOT:

```text
investment score

clustering feature

portfolio score

research eligibility
```

---

# 43. Priority Signals

## Liquidity

Possible measures:

```text
median traded value 60d

median traded value 120d

mean traded value

median volume
```

---

## Traded Value Persistence

Prefer persistent high activity over one-day spikes.

---

## Active Trading Frequency

Possible:

```text
active sessions / expected sessions
```

---

## Market Importance

Possible signals:

```text
major index membership

persistent market-turnover contribution

market-cap rank if reliable

large listed company status
```

---

## History Depth

Prefer:

```text
>=5 years
```

then:

```text
>=3 years
```

New listings can still be acquired but marked:

```text
REFERENCE_ONLY
```

if insufficient history.

---

## Source Confidence

Higher if:

```text
provider supports symbol

multiple validated providers

identity known

price basis known

existing raw data exists
```

---

# 44. Suggested Priority Formula

Config-driven initial formula:

```text
PriorityScore =

0.35 * LiquidityScore
+
0.20 * TradedValuePersistence
+
0.15 * ActiveTradingFrequency
+
0.10 * MarketImportance
+
0.10 * HistoryDepth
+
0.10 * SourceConfidence
-
Penalties
```

Weights must be versioned.

---

# 45. Priority Penalties

Possible penalties:

```text
very recent listing

identity uncertainty

provider instability

extreme sparse trading

unknown price basis

insufficient history
```

---

# 46. Priority Categories

```text
HIGH

MEDIUM

NORMAL
```

HIGH likely includes:

```text
very liquid securities

persistent high traded value

large/important names

long history

good source support
```

---

# 47. Anti-Bias Rule

Never:

```text
HIGH priority
→ automatically research eligible
```

Priority decides:

```text
which security gets collected/recovered first
```

Research eligibility remains quality-based.

---

# 48. Stage B1 Outputs

```text
universe_priority.csv

stage_b1_report.md
```

Suggested columns:

```text
security_id

ticker

exchange

liquidity_score

traded_value_score

activity_score

market_importance_score

history_score

source_confidence_score

penalty_score

priority_score

market_priority

priority_reason
```

STOP.

---

# Stage B2 — Expansion Source Smoke

Before scaling:

```text
5–10 NEW securities
```

Sample must cover:

```text
HOSE

HNX

UPCOM

HIGH priority

NORMAL priority

old listing

new listing

high liquidity

lower liquidity
```

---

# 49. Source Smoke Validation

Validate:

```text
identity

exchange

listing metadata

dates

OHLCV

units

pagination

history depth

price basis

provenance

retry behavior

error handling
```

If smoke FAIL:

```text
DO NOT SCALE
```

---

# Stage B3 — Representative Expansion Pilot

Acquire:

```text
50–100 NEW securities
```

Requirements:

```text
deterministic assignment

immutable raw

resume support

bounded retry/backoff

manifest

checksums

QC

missing-session audit
```

---

# 50. Pilot Metrics

Report:

```text
assigned securities

acquired securities

failed securities

canonical-valid securities

>=3 years

>=5 years

latest21 complete

latest63 complete

latest126 complete

latest252 complete

market-feature-ready
```

Also:

```text
rows-per-symbol distribution

coverage distribution

provider failures

quarantine count
```

PASS required before scale.

---

# Stage B4 — Scale to Approximately 1,000 Securities

Current:

```text
500
```

Need approximately:

```text
+500 unique securities
```

Possible sharding:

```text
5 workers × ~100
```

Actual shard count may be tuned by runtime.

---

# 51. Worker Contract

Every worker receives frozen assignment.

No overlap:

```text
security_id
```

Same:

```text
config

collection range

code revision

adapter version
```

Each worker outputs:

```text
immutable raw

worker manifest

checksums

errors
```

---

# 52. Scale Report

Do not report only:

```text
1,000 downloaded
```

Report:

```text
total acquired

canonical valid

>=3 years

>=5 years

complete 21

complete 63

complete 126

complete 252

market-feature-ready
```

STOP after scale for audit.

---

# Stage B5 — Optional Scale to 1,200+

Proceed only if:

```text
~1,000 scale stable

candidate pool healthy

provider quality acceptable

identity quality acceptable

runtime acceptable

storage acceptable

marginal usable-security gain remains useful
```

If additional securities mostly produce:

```text
short history

sparse data

bad identity

provider errors
```

stop scaling.

---

# 53. Acquisition vs Research Count

Always expose:

```text
DISCOVERED
↓
ACQUIRED
↓
CANONICAL
↓
>=3Y
↓
>=5Y
↓
252 COMPLETE
↓
MARKET FEATURE READY
↓
RESEARCH READY
```

Do not collapse these into one ticker count.

---

# 54. Workstream C — Financial / PIT

Financial data is separate.

Current:

```text
financial raw may exist
PIT unresolved
```

Financial data cannot enter historical clustering/backtest until the system validates:

```text
period_end

available_at

report type

quarter

year

scope

revision/version

stable report identity
```

Required rule:

```text
available_at <= decision_at
```

## Financial/PIT Remediation Track — planned, not executed by A5-R1.1

### F0 — Financial Source Re-discovery

Compare CafeF and other legitimate candidate sources for historical coverage,
publication timing, report identity, revision semantics and PIT capability.

### F1 — Historical Financial Coverage Pilot

Measure actual representative-sample coverage before any large crawl. Required
metrics include securities tested; quarterly and annual periods; BS, IS and CF
coverage; consolidated/separate availability; oldest/newest period; and
missing-period distribution.

### F2 — Financial PIT Timing & Revision Validation

Validate `published_at`, `available_at`, timezone, report/version identity,
revision/restatement chronology and the fact-to-document relationship before any
historical financial features are allowed.

F3/F4 are intentionally not designed or executed until later evidence justifies
them. The existing rule remains: financial raw may exist while PIT is unresolved,
and financial work does not block current market enrichment unless M2 explicitly
requires fundamental features.

---

# 55. Financial Work Does Not Block Market Enrichment

Unless M2 later explicitly requires financial features, current initiative should prioritize:

```text
market-data completeness
+
universe expansion
```

Financial PIT remains a separate research blocker.

---

# 56. Canonical Enriched Dataset v2

After approved Workstream A and B results, merge:

```text
baseline valid observations

local salvaged observations

primary recovered observations

secondary recovered observations

identity-recovered observations

new-universe observations
```

Create:

```text
NEW IMMUTABLE CANONICAL
```

---

# 57. Canonical v2 Requirements

Must be:

```text
deterministic

immutable

versioned

auditable

provenance-preserving

duplicate-safe

unit-safe

identity-safe

price-basis-safe
```

---

# 58. Canonical v2 Manifest

Required:

```text
canonical_id

parent_canonical_id

created_at

code_revision

config_hash

baseline_security_count

new_security_count

total_security_count

baseline_price_rows

salvaged_rows

primary_recovered_rows

secondary_recovered_rows

new_universe_rows

rejected_recovery_rows

unresolved_missing_rows

provider_counts

exchange_counts

identity_recovered_count
```

---

# 59. Feature Rebuild

After Canonical v2:

Recompute existing market features:

```text
Momentum 21

Momentum 63

Momentum 126

Momentum 252

Volatility

Max Drawdown

Beta

Liquidity
```

Do not alter formulas.

---

# 60. Feature Integrity

No:

```text
partial windows

missing compression

fake returns

synthetic sessions

raw/adjusted silent mixing
```

Hard rule:

```text
100% required real observations
```

remains unchanged.

---

# 61. Before/After Readiness

Required comparison:

| Metric | Baseline | Enriched |
|---|---:|---:|
| Total securities | 500 | ? |
| Price rows | 614,430 | ? |
| ≥3y history | 500 | ? |
| ≥5y history | 484 | ? |
| Momentum 21 | 213 | ? |
| Momentum 63 | 193 | ? |
| Momentum 126 | 184 | ? |
| Momentum 252 | 169 | ? |
| Market-feature-ready | 169 | ? |

---

# 62. Readiness Gain Attribution

Must separate gains:

```text
gain_from_local_salvage

gain_from_primary_recovery

gain_from_secondary_recovery

gain_from_identity_recovery

gain_from_universe_expansion
```

Example:

```text
169 baseline

+ A local salvage

+ B primary recovery

+ C secondary recovery

+ D identity recovery

+ E new-universe ready securities

= final ready count
```

---

# 63. Expanded EDA

After enrichment and expansion run full EDA.

---

# 64. Universe EDA

Analyze:

```text
securities by exchange

baseline vs new securities

listing age

history length

provider coverage
```

---

# 65. Session Coverage EDA

Analyze:

```text
observed-session coverage

missing count distribution

missing streak distribution

missing by exchange

missing by year/month

missing by provider
```

---

# 66. Feature Availability EDA

Analyze:

```text
Momentum21 availability

Momentum63 availability

Momentum126 availability

Momentum252 availability

Volatility availability

Beta availability

MDD availability

Liquidity availability
```

---

# 67. Market Representation EDA

Analyze:

```text
liquidity distribution

traded-value distribution

market-priority distribution

HIGH-priority coverage

exchange composition

major-name coverage
```

---

# 68. Exclusion EDA

Top reasons:

```text
missing sessions

history too short

identity unresolved

provider gap

price-basis conflict

trading status

calendar uncertainty

financial PIT

other blockers
```

---

# 69. Required Charts

At minimum:

```text
1. Securities by exchange

2. Baseline vs expanded universe

3. History-length distribution

4. Session coverage distribution

5. Missing-session bucket distribution

6. Feature availability before vs after

7. Market-feature-ready before vs after

8. Liquidity distribution

9. Readiness by exchange

10. Readiness by market-priority bucket

11. Top exclusion reasons
```

---

# 70. M2 Research Sample Freeze

Do not freeze final M2 sample before:

```text
current-500 enrichment complete

universe expansion audited

canonical v2 generated

features rebuilt

EDA completed
```

---

# 71. M2 Sample Eligibility

Eligibility should depend on:

```text
minimum historical duration

100% required observations

valid identity

canonical quality

price-basis validity

required feature availability

research protocol
```

---

# 72. M2 Sample Must Not Be Selected Using

```text
hotness

popularity

current volume alone

market cap alone

nice clustering results

arbitrary target count
```

Market priority is acquisition assistance only.

---

# 73. Recommended Modules

Avoid rewriting engineering core.

Recommended focused modules:

```text
src/delta_t1/ingestion/session_audit.py

src/delta_t1/ingestion/recovery_plan.py

src/delta_t1/ingestion/recovery_runner.py

src/delta_t1/ingestion/recovery_reconcile.py

src/delta_t1/ingestion/identity_history.py

src/delta_t1/ingestion/universe_expansion.py

src/delta_t1/ingestion/universe_priority.py
```

Reuse existing abstractions when available.

---

# 74. Config Files

```text
configs/m1_enrichment.yaml

configs/m1_universe_expansion.yaml
```

---

# 75. Suggested Enrichment Config

```yaml
policy:
  require_complete_sessions: true

  allow_forward_fill: false
  allow_backward_fill: false
  allow_interpolation: false
  allow_missing_zero: false

session_audit:
  latest_priority_window: 300

recovery_priority:
  p0_max_missing: 5
  p1_max_missing: 20
  p2_max_missing: 63

recovery:
  source_order:
    - primary_retry
    - same_provider_alternate_path
    - cafef
    - validated_secondary_provider

reconciliation:
  average_sources: false

  reject_unit_conflict: true
  reject_price_basis_conflict: true
  reject_identity_conflict: true
```

---

# 76. Suggested Universe Expansion Config

```yaml
universe:
  intermediate_target: 1000
  extended_target: 1200

candidate_pool:
  target_min: 1300
  target_max: 1500

priority:
  liquidity_weight: 0.35

  traded_value_persistence_weight: 0.20

  active_frequency_weight: 0.15

  market_importance_weight: 0.10

  history_depth_weight: 0.10

  source_confidence_weight: 0.10

  popularity_is_research_filter: false
```

Weights are acquisition configuration only.

---

# 77. Artifact Structure

Recommended:

```text
artifacts/

  data_enrichment/
    <run_id>/

      baseline_summary.json
      baseline_hashes.json

      missing_session_audit.parquet
      missing_session_by_symbol.csv
      missing_session_by_date.csv
      recovery_priority.csv

      local_salvage_candidates.parquet
      local_salvage_accepted.parquet
      local_salvage_rejected.parquet

      primary_recovery_results.csv

      secondary_recovery_evidence.jsonl

      reconciliation_report.json

      unresolved_missing.csv

      recovery_summary.csv

      report.md


  universe_expansion/
    <run_id>/

      universe_candidates.parquet

      universe_priority.csv

      source_smoke/

      pilot/

      shards/

      manifests/

      quality/

      report.md
```

---

# 78. Critical Tests

Minimum methodology-protection tests:

```text
test_expected_sessions_respect_listing_date

test_expected_sessions_respect_delisting_date

test_missing_session_detected

test_no_forward_fill

test_no_backward_fill

test_no_interpolation

test_missing_not_converted_to_zero

test_recovered_row_retains_provenance

test_unit_conflict_rejected

test_price_basis_conflict_rejected

test_identity_conflict_rejected

test_identity_alias_requires_evidence

test_momentum252_requires_complete_observations

test_baseline_cannot_be_overwritten

test_expansion_candidates_unique_by_security_id

test_baseline_and_new_universe_do_not_overlap

test_priority_ranking_is_deterministic

test_market_priority_does_not_set_research_eligibility

test_canonical_merge_is_deterministic
```

Do not create excessive cosmetic tests.

---

# 79. Reproducibility Requirements

Every run must record:

```text
run_id

created_at

git_commit

config_hash

input_artifact_ids

provider_versions

adapter_versions

output_hashes
```

Future researcher must be able to answer:

```text
Why is this row here?
```

and:

```text
Where did this value come from?
```

---

# 80. Single-agent Execution Contract

Every session must:

```text
1. Read this master plan.

2. Read AGENTS.md.

3. Inspect current stage inputs.

4. Identify `Next allowed stage` from Execution Progress / Handoff and implement ONLY that stage.

5. Run minimal relevant tests.

6. Generate required artifacts.

7. Self-review the stage contract, evidence, invariants and result.

8. Update Execution Progress / Handoff and STOP.
```

Agent must not automatically continue to next stage.

---

# 81. Session Must Not

```text
change methodology

change feature formulas

loosen 100% observation rule

start full crawl before pilot PASS

overwrite baseline

delete immutable artifacts

invent source semantics

invent recovered values

silently merge identities

use hotness as research eligibility
```

---

# 82. Stage Report Contract

Every stage report must contain:

## Scope

What was implemented.

## Files Changed

Exact paths.

## Commands Executed

Exact commands.

## Tests

```text
test_name
PASS/FAIL
```

## Artifacts

Exact output paths / IDs.

## Metrics

Measured values only.

## Findings

Important findings.

## Unresolved Issues

Everything uncertain.

## Stage Result

One of:

```text
PASS
PARTIAL
BLOCKED
FAIL
DEFERRED
MANUAL_REVIEW_REQUIRED
```

## Self-review and STOP

Record self-review findings and update handoff. Do not automatically continue.

---

# 83. Manual-review trigger

Before treating any methodology-sensitive proposal as approved, assess:

```text
Did agent stay inside stage scope?

Was baseline mutated?

Was synthetic data introduced?

Was 100% session rule preserved?

Do recovered rows have evidence?

Are dates correct?

Are units correct?

Is price basis compatible?

Is identity supported?

Is provenance complete?

Are results deterministic?

Are metrics calculated rather than hard-coded?

Did market priority only affect acquisition?

Were unresolved issues reported honestly?
```

If approval is needed for a change to methodology, price basis, identity, expected
sessions, PIT semantics, research eligibility, or a final freeze, mark
`MANUAL_REVIEW_REQUIRED` and STOP. The user decides whether and how to review it.

---

# 84. Official Execution Sequence

```text
READ EXECUTION PROGRESS / HANDOFF
        ↓
READ NEXT ALLOWED STAGE
        ↓
IMPLEMENT EXACTLY ONE STAGE
        ↓
RUN RELEVANT TESTS
        ↓
SELF-REVIEW AGAINST STAGE CONTRACT
        ↓
UPDATE HANDOFF
        ↓
STOP
```

---

# 85. Why Missing Audit Must Come First

Current 500 dataset already contains enough evidence to determine:

```text
which securities are nearly ready

which securities have structural problems

which dates repeatedly fail

which providers/exchanges have concentrated gaps

which important securities should be recovered first
```

Blindly crawling before audit may:

```text
waste requests

duplicate data

repeat parsing errors

repair unusable symbols

ignore easy P0 recoveries
```

Therefore first implementation stage is A1.

A0 may be performed as setup if baseline artifact IDs are already known.

---

# 86. Immediate First Task

First agent implementation after this plan:

> **Build Missing Session Audit for current 500-security baseline.**

Hard scope:

```text
NO NETWORK

NO RECOVERY

NO UNIVERSE EXPANSION

NO CANONICAL MUTATION
```

Required outputs:

```text
missing_session_audit.parquet

missing_session_by_symbol.csv

missing_session_by_date.csv

recovery_priority.csv

missing_classification_summary.json

stage_a1_report.md
```

Stage A1 must produce enough evidence to determine recovery strategy.

---

# 87. Recovery Efficiency Rule

Recovery priority should maximize:

```text
new research-usable securities
/
recovery cost
```

Example:

```text
Ticker A
missing 2 sessions
```

usually has higher priority than:

```text
Ticker B
missing 800 sessions
```

unless B has one obvious recoverable identity/provider bug.

---

# 88. Market-Priority Recovery Rule

Within same recovery difficulty:

```text
HIGH market-priority
```

should be recovered before:

```text
NORMAL
```

Example:

```text
Stock A
missing 3
high liquidity

Stock B
missing 3
very low liquidity
```

recover Stock A first.

Research rules remain identical afterward.

---

# 89. Individual Security Stop Conditions

Stop recovery for a security if:

```text
multiple validated providers have no observations

gap is structural

identity cannot be resolved

price basis cannot be reconciled

history is too short

recovery cost is disproportionate
```

Possible status:

```text
REFERENCE_ONLY

UNRESOLVED

EXCLUDED_FROM_RESEARCH
```

Do not endlessly chase one ticker.

---

# 90. Universe Expansion Stop Conditions

Stop or pause scale if:

```text
candidate quality declines materially

provider error rate increases materially

new securities mostly have short histories

new securities are extremely sparse

usable-sample gain becomes very small

runtime/storage cost becomes disproportionate
```

Ticker count alone is not success.

---

# 91. Expansion Success Metrics

Track:

```text
incremental securities acquired

incremental canonical-valid securities

incremental >=3y

incremental >=5y

incremental latest252-complete

incremental market-feature-ready

incremental storage

incremental runtime

provider failure rate
```

Important ratio:

```text
new market-feature-ready
/
new securities acquired
```

---

# 92. Enrichment Success Metrics

Track:

```text
missing observations before

missing observations after

rows recovered

local-salvage rows

primary-provider recovered rows

secondary-provider recovered rows

identity-recovered rows

securities improved

newly market-ready securities

remaining unresolved gaps
```

---

# 93. Before/After Attribution

Never report only:

```text
169 → X
```

Report:

```text
169 baseline

+ A due to local salvage

+ B due to primary-provider recovery

+ C due to secondary-provider recovery

+ D due to identity recovery

+ E due to universe expansion

= X final
```

---

# 94. Research Bias Checks

After expansion inspect bias toward:

```text
HOSE only

large-cap only

high-liquidity only

specific sectors

specific provider coverage

older listings only

newer listings only
```

Document bias.

Do not "fix" bias using low-quality or fabricated data.

---

# 95. M2 Separation

This initiative is Data Foundation.

Do not implement during this initiative:

```text
K-Means model selection

Hierarchical clustering

DBSCAN

GMM

PCA tuning

UMAP tuning

Dynamic Clustering algorithm

portfolio construction

backtesting
```

Those belong to M2/M3.

---

# 96. Sharpe / ROI Separation

Sharpe and ROI are NOT:

```text
data-quality metrics

recovery metrics

universe-priority metrics

cluster-selection metrics
```

They remain portfolio/backtest metrics.

Do not recover/select securities based on future portfolio performance.

---

# 97. Expected Final Deliverables

At completion:

```text
M1_DATA_ENRICHMENT_AND_UNIVERSE_EXPANSION_MASTER_PLAN.md

baseline freeze artifacts

missing-session audit artifacts

recovery artifacts

identity-history artifact

universe candidates

market-priority ranking

source smoke reports

expansion pilot reports

scale reports

canonical enriched v2

feature snapshots v2

before-after readiness report

expanded EDA

final M2 sample manifest
```

---

# 98. Completion Criteria

Initiative is complete only when:

1. Current 500 securities have full missing-session audit.
2. Recoverable observations are recovered from real evidence.
3. No synthetic market observations are introduced.
4. Historical identity has been improved where possible.
5. Universe expands materially beyond 500.
6. ~1,000 total securities target has been attempted and audited.
7. Architecture is capable of continuing to 1,200+.
8. Important/high-liquidity securities have better representation.
9. Popularity affects acquisition priority only.
10. Canonical v2 is immutable and versioned.
11. Feature formulas remain unchanged.
12. 100% required-session rule remains unchanged.
13. Feature availability is recomputed from real data.
14. Before/after readiness gains are attributed correctly.
15. Expanded EDA is complete.
16. Final M2 sample is selected using data-quality evidence.
17. All unresolved limitations are documented.

---

# 99. Core Principle

The goal is not:

> Collect the largest number of tickers at any cost.

The goal is:

> **Build the largest possible dataset of real, auditable, research-usable Vietnamese securities without weakening methodological integrity.**

Always separate:

```text
ACQUISITION SIZE
```

from:

```text
RESEARCH-USABLE SIZE
```

A smaller clean research sample is better than a larger sample containing fabricated or invalid observations.

At the same time, acquisition must be broad enough so that the final research sample is not artificially small simply because major or actively traded Vietnamese securities were never collected.

---

# 100. Decision Priority

Whenever implementation decisions are unclear, use this order:

```text
1. Data correctness

2. Auditability

3. Research methodology

4. Coverage / completeness

5. Market representation

6. Runtime efficiency

7. Convenience
```

Never reverse this order only to increase ticker count.

---

# 101. Final Session Instruction

This document is the authoritative master plan.

One session must never execute the entire initiative in a single task.

Every future task will explicitly specify one stage.

Execution pattern:

```text
READ MASTER PLAN
↓
READ CURRENT HANDOFF
↓
READ NEXT ALLOWED STAGE
↓
IMPLEMENT ONLY THAT STAGE
↓
RUN RELEVANT TESTS
↓
SELF-REVIEW
↓
GENERATE ARTIFACTS
↓
REPORT EVIDENCE
↓
STOP
```

Only the current Handoff may identify a subsequent stage.
