# Crawl Handoff Templates

## 1. Assignment manifest

```json
{
  "assignment_id": "M1-CAFEF-MARKET-001",
  "collector": "NAME",
  "source": "CafeF",
  "dataset": "prices_daily",
  "symbols": ["FPT", "VNM"],
  "start": "2020-01-01",
  "end": "2025-12-31",
  "adapter_version": "cafef-v1",
  "mapping_version": "market-v1",
  "created_at": "YYYY-MM-DDTHH:MM:SS+07:00",
  "status": "ASSIGNED"
}
```

## 2. Collector report

```markdown
# Collector Report — <assignment_id>

## Collector
- Name:
- Date:
- Source:
- Dataset:
- Adapter version:
- Mapping version:

## Scope
- Symbols:
- Date range:
- Files/pages:
- Rows:

## Access / rights
- Public/login/API:
- Terms reviewed:
- Rate-limit notes:
- Reviewer:

## Semantics
- Price unit:
- Volume unit:
- Traded-value unit:
- Timezone:
- Price basis:
- Date boundaries:
- Pagination:
- Financial period semantics:

## Manual spot checks
| Symbol | Date/Period | Field | Source value | UI/reference | Status |
|---|---|---|---|---|---|

## Errors / gaps
- Missing:
- Duplicates:
- Rate limits:
- 4xx/5xx:
- Parsing errors:

## Cross-source conflicts
...

## Handoff
- Raw checksum complete: YES/NO
- Secrets removed: YES/NO
- READY/BLOCKED:
- Blocking reasons:
```

## 3. Pre-handoff checklist

- [ ] assignment_id đúng;
- [ ] source đúng;
- [ ] symbols/range đúng;
- [ ] raw bytes không bị sửa;
- [ ] checksum đủ;
- [ ] fetched_at có;
- [ ] request/page metadata có;
- [ ] không có token/cookie/API key;
- [ ] unit semantics có evidence;
- [ ] price basis có evidence;
- [ ] không forward-fill;
- [ ] không zero-fill;
- [ ] không tự average source conflict;
- [ ] collector report hoàn chỉnh;
- [ ] blocker được ghi rõ.
