# Data contract 2.0

## Source of truth

Executable contracts are the JSON files in `src/delta_t1/schemas`; `contracts.py` normalizes and validates them. This document defines cross-table semantics only. Schema changes require a version bump, migration note, tests and `CHANGELOG.md`/`DECISIONS.md` update.

All canonical rows carry `source`, `fetched_at` and `data_version`. Missing nullable fields become `null`, never `""`, NaN or an invented zero. Unknown provider columns remain in immutable raw data.

## Canonical tables

| Table | Key | Core semantics |
|---|---|---|
| `securities` | security_id, valid_from | historical ticker/exchange/issuer interval, status and currency |
| `prices_daily` | security_id, trade_date | raw/adjusted OHLC, price basis, volume/value, status, availability |
| `benchmark_daily` | index_id, trade_date | price/total-return level and basis |
| `trading_calendar` | exchange, trade_date | open/month-end and decision timestamps |
| `corporate_actions` | event_id | announcement/ex/record/effective/payment dates and economic terms |
| `risk_free_rate` | date, tenor | annualized rate, day-count basis and availability |
| `financial_reports` | report_id | fiscal period, scope, audit/revision, publication/availability and document hash |
| `financial_facts` | report_id, item_code | tidy statement fact, duration/instant, currency/scale and taxonomy |
| `feature_snapshots` | security_id, as_of_date | as-of features, history, eligibility segment and NA reasons |
| `assignments` | run/snapshot/security | raw/aligned cluster and optional display projection |
| `transitions` | run/from/to/clusters | counts/rates over shared identities |
| `trades`, `nav` | run-specific | future raw-price ledger contracts; not aliases for return-space simulation |

## Identity and time

- `security_id` is stable; ticker is an attribute with interval `[valid_from, valid_to)`.
- Current listings do not prove historical membership. Ambiguous mappings quarantine.
- `fetched_at` records acquisition; `published_at` records source publication; `available_at` records earliest permitted model use; `as_of_date` is the observation snapshot.
- Financial timing must satisfy `available_at >= published_at >= period_end`.
- Restatements create new report vintages; old snapshots are never overwritten.
- Market/feature input requires `available_at <= decision_at`; execution begins next eligible session.

## Units and price basis

Equity price is VND/share, volume is shares, traded value is VND; index levels remain points. A provider scale is applied only with evidence, never inferred from magnitude.

`raw_close`, split-adjusted, vendor-adjusted and certified total-return series are distinct. `raw_close` may be null; it is never copied from adjusted close. A basis change resets rolling windows. Do not derive traded value from adjusted price × volume unless a separately versioned proxy contract is approved.

## Feature eligibility

Real runs require `minimum_history_years >= 3`, measured from first usable observed price in the same basis.

- `ELIGIBLE_FOR_CLUSTERING`: history, identity, status and required features pass.
- `REFERENCE_ONLY`: valid security lacks required observed history.
- `EXCLUDED`: another eligibility rule fails.

Rows retain `history_start_date`, `history_calendar_days`, `history_observations`, `lookback_observations`, `missing_count`, `na_reason` and `universe_segment`. Gaps are not compressed or forward-filled.

Sharpe fields remain readable for backward compatibility but are forbidden in required/model/selection feature lists. Sharpe is a portfolio-performance metric only; ROI is not a clustering metric.

## Quality and failure behavior

Duplicate keys, invalid types/dates/numbers, overlapping identity intervals, impossible OHLC, timing violations, unknown basis and broken relations are quarantined with rule IDs. Blocking issues prevent downstream features even when clean debug rows are written. Fixing input/mapping creates a new run; raw/canonical artifacts are not overwritten.

Coverage reports missing sessions and segment counts without assuming every missing price is a holiday. Resume is read-only for completed runs and allowed only when config/code/raw hashes match.

Pilot-specific KBS decisions remain only at [data/kbs_pilot_semantics.md](data/kbs_pilot_semantics.md) because immutable legacy manifests reference that path. They do not define the production contract.
