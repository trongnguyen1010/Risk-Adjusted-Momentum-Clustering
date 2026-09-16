# DELTA Source Selection Result

**Comparison date:** 2026-09-16  
**Detailed comparison:** [SOURCE_COMPARISON.md](SOURCE_COMPARISON.md)

## Acquisition paths

| Path | Current status |
|---|---|
| CafeF direct | `ACCESS_TESTED`; technical candidate cho security/shares current, corporate actions và historical value components; `BLOCKED_RIGHTS`/`BLOCKED_SEMANTICS` tùy domain |
| KBS via Vnstock | `ACCESS_TESTED`; technical candidate cho adjusted daily OHLCV, financial structure và VNINDEX; `BLOCKED_RIGHTS` cùng missing-field/PIT gaps |
| TCBS via VietFin | `DEFERRED`; live path `BLOCKED_ACCESS`, provider rights và core semantics chưa xác minh |

## Selected technical roles

| Domain | PRIMARY | SECONDARY / CROSS_CHECK | Readiness |
|---|---|---|---|
| Security current | CafeF direct | KBS via Vnstock | BLOCKED_RIGHTS |
| Shares current | CafeF direct | KBS via Vnstock | BLOCKED_RIGHTS |
| Shares history | UNRESOLVED | — | BLOCKED_MISSING_FIELDS |
| Daily OHLCV | KBS via Vnstock | CafeF direct | BLOCKED_RIGHTS |
| Price basis | KBS via Vnstock | CafeF direct chỉ sau khi phân loại basis | BLOCKED_RIGHTS |
| Historical ref/ceil/floor | UNRESOLVED | — | BLOCKED_MISSING_FIELDS |
| Corporate actions | CafeF direct | — | BLOCKED_SEMANTICS |
| Financial structure | KBS via Vnstock | CafeF direct | BLOCKED_RIGHTS |
| Financial PIT | UNRESOLVED | KBS/CafeF timestamp candidates | BLOCKED_SEMANTICS |
| VNINDEX | KBS via Vnstock | CafeF direct | BLOCKED_SEMANTICS |
| Trading calendar | UNRESOLVED | CafeF notice / Vnstock dictionary | BLOCKED_MISSING_FIELDS |

Technical role không phải execution approval và không chỉ định một overall source-of-truth.

## P0 blockers

| Gap | Blocker | Required resolution |
|---|---|---|
| GAP-001 | Automation/data rights cho CafeF/KBS chưa xác minh; Vnstock client restricted | Xác minh policy/permission cho đúng provider/client path hoặc chọn approved source |
| GAP-002 | Không có historical reference/ceiling/floor | Targeted gap-source discovery; không suy từ price band |
| GAP-003 | Historical traded-value canonical definition chưa chốt | Xác minh matched/put-through inclusion và unit/transform |
| GAP-004 | Financial `published_at`/`available_at` và PIT semantics chưa đủ | Xác minh timing/timezone trên ít nhất ba quarterly reports |

## P1 blockers

| Gap | Blocker |
|---|---|
| GAP-005 | Historical trading status/code semantics |
| GAP-006 | Historical shares với effective/available dates |
| GAP-007 | Financial revision/restatement lineage |
| GAP-008 | Q2/Q3 income-statement semantics đầy đủ |
| GAP-009 | Q2/Q3 cash-flow semantics |
| GAP-010 | Authoritative structured trading calendar |
| GAP-011 | Historical security identity |
| GAP-012 | Stable provider report ID |
| GAP-013 | Complete corporate-action dates/terms |
| GAP-014 | VNINDEX basis/methodology/PIT |
| GAP-015 | Historical matched-vs-put-through interpretation |

## Active adapter work packages

| WP | Provider/client path | Domain | Status |
|---|---|---|---|
| WP-A | `kbs` / `vnstock` | Adjusted daily OHLCV và VNINDEX raw ingest | BLOCKED |
| WP-B | `cafef` / direct | Current security/shares, corporate-action evidence, historical value components | BLOCKED |
| WP-C | `kbs` / `vnstock` | Financial structure/metadata raw ingest | BLOCKED |

Mỗi WP phải fail-closed cho unresolved fields, giữ provider/client provenance và không được bắt đầu trước khi preconditions tương ứng được giải quyết.

## Deferred

- TCBS via VietFin: access boundary chưa có legitimate route để tiếp tục.
- KBS corporate actions: empty response chưa cung cấp semantic sample.
- CafeF historical OHLC canonical mapping: price basis vẫn unknown.
- Mọi cách dùng current share snapshot như historical series.
- Vnstock client calendar dictionary như canonical exchange calendar.

## SOURCE_SMOKE

**Status:** NOT_READY  
**Reason:** Bốn P0 gap vẫn mở: rights, historical reference/ceiling/floor, traded-value semantics và financial PIT. Các gap này không thể được lấp bằng inference, averaging hoặc current-snapshot backfill trong real SOURCE_SMOKE.

## Next action

`Resolve P0 gaps before adapter implementation and SOURCE_SMOKE.`
