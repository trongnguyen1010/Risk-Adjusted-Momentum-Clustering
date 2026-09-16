# DELTA P0 Rights and Acquisition Source Result

**Date:** 2026-09-16  
**Detailed evidence:** [P0_RIGHTS_AND_SOURCE_DECISION.md](P0_RIGHTS_AND_SOURCE_DECISION.md)

## Final outcome

**Decision:** `REPLACEMENT_SOURCE_REQUIRED`

CafeF và KBS không có explicit sufficient rights. Fallback search tìm thấy technically viable licensed candidates, nhưng public materials không cấp đủ local storage, derived research dataset và internal reproducibility rights để chọn một executable plan.

## Existing paths

| Path | Automation | Storage | Research use | Result |
|---|---|---|---|---|
| CafeF direct | `NOT_VERIFIED` | `NOT_VERIFIED` | `NOT_VERIFIED` | INSUFFICIENT |
| KBS provider | `NOT_VERIFIED` | `NOT_VERIFIED` | `NOT_VERIFIED` | INSUFFICIENT |
| Vnstock client | `RESTRICTED` by license/tier/quota; provider rights separate | `NOT_VERIFIED` for provider data | `ALLOWED_WITH_CONDITIONS` for software; provider data separate | INSUFFICIENT end-to-end |

## Selected acquisition plan

No rights-cleared plan is selected.

| Domain | Provider | Client/API | Rights status | Role |
|---|---|---|---|---|
| OHLCV | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |
| reference/ceiling/floor | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |
| traded_value | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |
| VNINDEX | UNSELECTED | — | `NOT_VERIFIED` | BLOCKED |

Preferred licensing target: FiinGroup API Datafeed, but only after written terms grant every intended use and exact plan coverage is verified.

## Replacement candidates

| Provider | Rights | Coverage | History | Cost category | Decision |
|---|---|---|---|---|---|
| FiinGroup API Datafeed | API automation contract-capable; storage/derived research/reproducibility `NOT_VERIFIED` | Strong HOSE/HNX/UPCoM/VNINDEX + required fields | PARTIAL; 2020 samples, plan depth unstated | `CONTACT_REQUIRED` | SHORTLIST_PENDING_LICENSE |
| HOSE + HNX official feeds | Automation explicit after signed contracts; other intended rights contract-specific | Official combined markets/index; public field evidence incomplete across both | UNKNOWN; historical products exist, depth unstated | `PAID` | SHORTLIST_PENDING_CONTRACTS |

Compatibility:

- FiinGroup: `FULL_REPLACEMENT` if licensed terms/coverage pass review.
- HOSE + HNX: `HYBRID` official fallback if both contracts pass review.

No account, API key, trial or subscription was created. Exact FPT/VNM/PVS/ACV/VNINDEX requests were not run because access requires user action.

## GAP-001

**Status:** `OPEN`

Required closure evidence: a written license/contract granting bounded automation, local immutable raw storage, derived research dataset creation, thesis use and internal reproducibility for a source with at least five years of required Vietnam market coverage.

## Market adapter gate

**Status:** `NOT_READY`

Không tạo active implementation work package trước khi license được project review và approve.

## SOURCE_SMOKE

**Status:** `NOT_RUN`

## Next action

`Continue targeted replacement-source discovery; do not implement adapters yet.`
