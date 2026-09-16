# DELTA P0 Market Gate Result

**Date:** 2026-09-16  
**Detailed evidence:** [P0_MARKET_GATE_RESOLUTION.md](P0_MARKET_GATE_RESOLUTION.md)

## P0 status

| Gap | Result | Main reason |
|---|---|---|
| GAP-001 Rights | OPEN | CafeF/KBS provider data rights vẫn `NOT_VERIFIED`; Vnstock client license không cấp third-party data rights |
| GAP-002 Historical ref/ceil/floor | RESOLVED | CafeF UI-linked `TradeHistoryNew.ashx` có direct historical `BasicPrice`, `Ceiling`, `Floor` trên HOSE/HNX/UPCOM |
| GAP-003 Traded value semantics | RESOLVED | CafeF UI source cộng matched `TotalValue` với put-through `AgreedValue` trên cùng historical row, đơn vị raw VND |

## CafeF current vs historical

| Field | Current snapshot | Historical daily | Status |
|---|---|---|---|
| reference_price | UI `Giá tham chiếu`; FPT 72.70 nghìn VND/share | `BasicPrice`, `×1,000`; four-symbol verification | HISTORICAL_AVAILABLE |
| ceiling_price | UI `Giá trần`; FPT 77.70 nghìn VND/share | `Ceiling`, `×1,000`; four-symbol verification | HISTORICAL_AVAILABLE |
| floor_price | UI `Giá sàn`; FPT 67.70 nghìn VND/share | `Floor`, `×1,000`; four-symbol verification | HISTORICAL_AVAILABLE |
| matched_volume | Current `Khối lượng` visible | `Volume` shares / `KhoiLuongKhopLenh` shares | HISTORICAL_AVAILABLE |
| matched_value | NOT_CHECKED as standalone current label | `TotalValue` VND / `GiaTriKhopLenh` billion VND | HISTORICAL_AVAILABLE |
| put_through_volume | NOT_CHECKED | `AgreedVolume` shares / `KLThoaThuan` shares | HISTORICAL_AVAILABLE |
| put_through_value | NOT_CHECKED | `AgreedValue` VND / `GtThoaThuan` billion VND | HISTORICAL_AVAILABLE |
| total_traded_value | Current table total not used as proof | UI-derived `TotalValue + AgreedValue`, VND | COMPONENTS_PLUS_DERIVED_TOTAL |

`PriceHistory.ashx` và XLSX export vẫn không có historical limit fields; historical proof đến từ một company-page request khác được UI gọi trực tiếp, không từ current snapshot hoặc derivation.

## KBS current vs historical

| Field | Current snapshot | Historical daily | Status |
|---|---|---|---|
| reference_price | `RE`, VND/share | Không có trong `data_day` | CURRENT_SNAPSHOT_ONLY |
| ceiling_price | `CL`, VND/share | Không có trong `data_day` | CURRENT_SNAPSHOT_ONLY |
| floor_price | `FL`, VND/share | Không có trong `data_day` | CURRENT_SNAPSHOT_ONLY |
| volume | `TT` accumulated snapshot | `v`, shares | HISTORICAL_AVAILABLE |
| traded_value | `TV`, VND snapshot | Không có trong bounded `data_day` rows | CURRENT_SNAPSHOT_ONLY |
| put_through_volume | `PTQ`, shares snapshot | Không có trong `data_day` | CURRENT_SNAPSHOT_ONLY |
| put_through_value | `PTV`, VND snapshot | Không có trong `data_day` | CURRENT_SNAPSHOT_ONLY |

## Rights

| Path | Bounded automation | Local storage | Research use | Raw redistribution |
|---|---|---|---|---|
| CafeF direct | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| KBS provider | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| Vnstock client | RESTRICTED | NOT_VERIFIED for provider data | ALLOWED_BY_PUBLIC_POLICY for client software; provider rights separate | NOT_VERIFIED for provider data |

## Traded-value decision

**Decision:** COMPONENTS_PLUS_DERIVED_TOTAL

**Reason:** CafeF historical rows expose matched value as raw `TotalValue` in VND and put-through value as `AgreedValue` in VND. Public CafeF client source explicitly renders daily total as their sum; two UI-response samples agree after formatting. Components remain separate and `traded_value` is derived only within the same provider row/trade date.

## Market SOURCE_SMOKE

**Status:** NOT_READY

Important:  
This status is only for the MARKET side.  
Financial PIT GAP-004 is outside this task.

GAP-002 and GAP-003 are resolved, but GAP-001 remains OPEN; therefore the market gate stays fail-closed.

## Next action

`Resolve rights/policy blocker before any automated collection.`
