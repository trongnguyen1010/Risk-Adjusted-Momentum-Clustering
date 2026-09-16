# DELTA FiinGroup Targeted Result

**Date:** 2026-09-16  
**Detailed evidence:** [FIINGROUP_TARGETED_VERIFICATION.md](FIINGROUP_TARGETED_VERIFICATION.md)

## Decision

**Status:** `SUITABLE_IF_CONTRACT_APPROVED`

## Replacement capability

**Mode:** `INSUFFICIENT`

Technical coverage có thể hỗ trợ `FULL_REPLACEMENT` cho KBS + CafeF, nhưng public evidence chưa document exact `>=5y` entitlement và intended rights. Vì vậy chưa được dùng `FULL_REPLACEMENT` trong task này.

## Market coverage

| Domain | Status |
|---|---|
| HOSE | `VERIFIED` |
| HNX | `VERIFIED` |
| UPCOM | `VERIFIED` |
| VNINDEX | `VERIFIED` |
| >=5y history | `PLAN_DEPENDENT` |

## Required fields

| Field/domain | Status |
|---|---|
| OHLCV | `DOCUMENTED` |
| reference/ceiling/floor | `DOCUMENTED` |
| matched/put-through | `DOCUMENTED` |
| total traded_value | `DOCUMENTED` |
| trading_status | `PARTIAL` |
| adjusted price | `DOCUMENTED` — `BOTH_AVAILABLE`; methodology chưa đủ để gọi split/total-return |
| corporate actions | `PARTIAL` |

## Rights

| Use | Status |
|---|---|
| Automated API requests | `CONTRACT_DEPENDENT` |
| Local raw storage | `CONTRACT_DEPENDENT` |
| Derived research dataset | `CONTRACT_DEPENDENT` |
| Thesis use | `CONTRACT_DEPENDENT` |
| Internal reproducibility | `CONTRACT_DEPENDENT` |
| Raw redistribution | `RESTRICTED` |

## Access

| Item | Result |
|---|---|
| Account | `NOT_VERIFIED`; user action required |
| API credentials | `NOT_VERIFIED`; auth mechanism not public |
| Contract | `CONTRACT_DEPENDENT`; written terms required |
| Trial | `UNKNOWN` |
| Cost category | `CONTACT_REQUIRED` |

## Market SOURCE_SMOKE

**Status:** `NOT_READY`

## User action required

- Yêu cầu FiinGroup trả lời written checklist dưới đây và cung cấp exact plan specification/data dictionary; không tạo adapter hoặc chạy smoke trước project review.

## Contract questions

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

## GAP-001 impact

**Can FiinGroup resolve GAP-001 after written approval?** YES

Điều kiện: written approval phải xác nhận intended rights, `>=5y` coverage, required fields/units/status semantics và quota của exact plan.

## Next action

`User should request FiinGroup access/contract clarification using the prepared checklist.`
