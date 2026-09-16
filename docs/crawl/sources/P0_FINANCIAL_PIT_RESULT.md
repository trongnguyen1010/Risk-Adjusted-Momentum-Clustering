# DELTA P0 Financial PIT Result

**Date:** 2026-09-16  
**Detailed evidence:** [P0_FINANCIAL_PIT_RESOLUTION.md](P0_FINANCIAL_PIT_RESOLUTION.md)

## GAP-004

| Item | Result |
|---|---|
| Status | `OPEN` |
| Main reason | Không path nào có verified first-public `available_at`, timezone và revision chain cho đúng report/version |
| Financial PIT gate | `NOT_READY` |
| Canonical mode | `RAW_ONLY_NO_CANONICAL_PIT` |

## CafeF

| Item | Result |
|---|---|
| Public financial documents | VERIFIED cho sáu sample periods ở FPT/VNM |
| `published_at` | NOT_VERIFIED |
| `available_at` | NOT_VERIFIED |
| Filename date/time tokens | `UPLOAD_TIMESTAMP_ONLY` / `DOCUMENT_METADATA_ONLY` |
| UI `Thời gian cập nhật` | Không phải timestamp; response `Time` là period label như `Q2/2026` |
| Report identity | PARTIAL ở document layer; có row `id`, scope/audit trong name |
| Fact-to-document join | NOT_FOUND |
| Revision chronology | PARTIAL evidence of multiple documents; không có supersession chain |
| Timezone | `LOCAL_DISPLAY_TIMEZONE_UNVERIFIED` |
| PIT conclusion | `NOT_READY` |

## KBS via Vnstock

| Field/item | Result |
|---|---|
| `PeriodBegin` / `PeriodEnd` | VERIFIED cho sáu observed report rows |
| `DatePubDepartment` | `PUBLISHED_AT_CANDIDATE`; không map canonical |
| `CreatedDate` | `PROVIDER_RECORD_METADATA_ONLY` |
| `LastUpdate` | `PROVIDER_UPDATE_ONLY`; không phải verified revision |
| `ReportDate` | `REPORT_METADATA_ONLY` |
| Stable provider report id | NOT_FOUND; `Head.ID` lặp giữa reports/pages |
| Timestamp format | `NAIVE_TIMESTAMP`; không có UTC offset |
| `available_at` | NOT_VERIFIED |
| PIT conclusion | `NOT_READY` |

## PIT recommendation

**Decision:** `RAW_ONLY_NO_CANONICAL_PIT`

Canonical timing rules:

- Giữ nguyên provider timestamps và field names ở raw layer.
- `published_at` và `available_at` để unmapped/null.
- `fetched_at` dùng UTC nhưng chỉ là observation time, không thay `available_at`.
- Mỗi payload hash mới là một internal observation; không overwrite prior raw version.
- Không gắn CafeF fact row với document chỉ bằng symbol/quarter.
- Không đổi `LastUpdate` thành restatement/revision timestamp.

## Sample coverage

| # | Sample | CafeF document | KBS period | KBS publication candidate | PIT result |
|---:|---|---|---|---|---|
| 1 | FPT Q1/2026 | VERIFIED | `202601..202603` | `2026-04-28` | RAW_ONLY |
| 2 | FPT Q2/2026 | VERIFIED; initial + reviewed documents | `202604..202606` | `2026-07-28` | RAW_ONLY |
| 3 | FPT Q4/2025 fallback | VERIFIED | `202510..202512` | `2026-01-27` | RAW_ONLY |
| 4 | FPT FY2025 | VERIFIED, audited consolidated document | `202501..202512` | `2026-03-20` | RAW_ONLY |
| 5 | VNM Q2/2026 | VERIFIED, reviewed consolidated document | `202604..202606` | `2026-07-31` | RAW_ONLY |
| 6 | VNM Q1/2026 | VERIFIED, reviewed consolidated document | `202601..202603` | `2026-05-04` | RAW_ONLY |

`DatePubDepartment` values above are raw date candidates, không phải canonical publication/availability timestamps.

Q2 income-statement period boundaries are verified as standalone for the observed FPT/VNM rows. Q3 was not added beyond the six-sample cap and remains **UNKNOWN — DO NOT MAP YET**; FPT Q4/2025 was the permitted fallback.

## SOURCE_SMOKE impact

| Gate | Status | Reason |
|---|---|---|
| Financial PIT gate | `NOT_READY` | Không có safe canonical `available_at` và revision chronology |
| Financial `SOURCE_SMOKE` | `NO` | PIT path chưa đủ semantics |
| `GAP-001 Rights` | `OPEN` — unchanged | Blocker riêng, không được giải quyết trong task này |
| Market gate | Unchanged | Task này không xử lý GAP-001/002/003 |

## Remaining blockers

1. Xác nhận nghĩa chính thức của `DatePubDepartment` và `ReportDate`.
2. Xác nhận timezone/date-only semantics.
3. Chứng minh earliest public availability cho đúng report/version.
4. Có stable report id và explicit revision/supersession chain.
5. Có stable CafeF fact-to-document join.
6. Xác minh Q3 duration/timing nếu Q3 thuộc intended smoke path.
7. Giải quyết riêng `GAP-001 Rights` trước automated collection.

## Next action

`Keep financial data RAW-only until a PIT-capable source is approved.`
