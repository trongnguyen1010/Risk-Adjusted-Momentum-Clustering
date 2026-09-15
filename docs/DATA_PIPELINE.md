# Data pipeline and source policy

## Source status

| Source | Role | Current status |
|---|---|---|
| CafeF | primary candidate for market/company/financial data | feasibility only; API/terms/basis/PIT coverage unresolved |
| VietFin | secondary connector | underlying provider and terms must be recorded |
| Vnstock | secondary/pilot connector | KBS price pilot exists; not source of truth for final finance/universe |

Connector license does not grant rights to third-party data. Each row/run records underlying provider, endpoint/request, connector/version, fetched time and raw hash. No large crawl before rights, rate limits and semantics pass a bounded smoke review.

Source lifecycle: `DISCOVERED → ACCESS_TESTED → SEMANTICS_VERIFIED → PILOT_APPROVED → PRODUCTION_APPROVED`.

## Stages

1. **Acquire:** bounded retries/timeouts/rate, immutable raw response and request metadata.
2. **Normalize:** parse fields, units, identity, price basis and timestamps without resolving conflicts.
3. **Reconcile:** compare candidates by canonical key; preserve conflicts and signed decisions.
4. **Canonicalize:** create versioned market, financial PIT and event tables.
5. **QC/coverage:** quarantine integrity/timing/identity errors and count eligible/reference/excluded rows.
6. **Research:** build as-of features/model/backtest artifacts.
7. **Product projection:** export compact immutable company bundles; UI never reads raw tables.

## Reconciliation contract

Each candidate retains canonical key, field, raw/normalized value and unit, price basis, connector/provider/version, request ID, source/fetched timestamps, raw hash and transform version.

| Domain | Key | Conflict behavior |
|---|---|---|
| Identity | security + validity interval | quarantine ambiguous issuer/ticker/exchange mapping |
| Price | security/date/basis | detect scale; never mix raw and adjusted basis |
| Volume/value | security/date/scope | preserve candidates; never average incompatible scopes |
| Calendar | exchange/date | unresolved open/closed day blocks month-end |
| Financial report | security/period/scope/revision | retain all vintages |
| Financial fact | report/item/period type | quarantine incompatible taxonomy/currency/scale |

Decision records store chosen candidate, rule/version, reason, confidence, reviewer and time. Restatement changes later snapshots only. Identical raw hashes/rules must reproduce identical canonical hashes.

## Point-in-time rules

- Historical identity joins use `[valid_from, valid_to)` and stable `security_id`.
- `fetched_at` is not a historical publication time and may not be backdated.
- Calendar is independent reference data; last row in a response is not automatically month-end.
- Raw, split-adjusted, vendor-adjusted and total-return series remain distinct.
- Adjustment-basis changes reset rolling history.
- Missing price/trading status at rebalance blocks simulation; a holding never silently disappears.
- Financial as-of joins select the latest report vintage available at `decision_at`, not the latest known today.

## Smoke before scale

1. Use 3–5 symbols across HOSE/HNX/UPCOM, including short-history and inactive identity cases.
2. Compare five-year daily ranges and at least two known corporate actions across usable providers.
3. Pull at least three quarterly reports and one restatement if available.
4. Save request/raw hash/version; report mismatches, missing dates, units, failure/rate behavior and rights.
5. Reviewer accepts reconciliation rules before 20–50 ticker pilot; pilot passes before 1.200+ crawl.

## Operational commands

```powershell
.venv\Scripts\python.exe scripts/crawl_vnstock.py --symbols FPT VNM PVS --start 2021-01-01 --end 2025-12-31
.venv\Scripts\python.exe scripts/plan_crawl.py --help
.venv\Scripts\python.exe scripts/promote_vnstock.py --help
.venv\Scripts\python.exe run.py run --config configs/demo.json
```

HTTP jobs require finite timeout/retry/page/response-size limits. Resume only when config/code/raw hashes match. One writer owns one run. Authentication secrets stay in environment variables and never enter config/log/Git.

## Scale target

JSONL is a reproducible pilot format. At 1.200+ securities and 5–15 years, use partitioned Parquet/DuckDB for analytics and database/object storage for product serving. Crawl incrementally with checkpoints; product/API receives compact projections rather than scanning raw history.
