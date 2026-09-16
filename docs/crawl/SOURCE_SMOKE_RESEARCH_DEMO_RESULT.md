# DELTA Research/Demo SOURCE_SMOKE Result

## Execution policy

- Run: `source-smoke-20260916T111529Z-af9bc570`, real data, `synthetic=false`.
- Rights remain `RIGHTS_NOT_VERIFIED`; execution policy is `ACCEPTED_RESEARCH_RISK` under [DATA_USAGE_RISK_ACCEPTANCE.md](../data/DATA_USAGE_RISK_ACCEPTANCE.md).
- Private/local academic research and non-commercial demo only; raw redistribution is prohibited.
- Concurrency `1`, minimum interval `2.0s`, timeout `20s`, attempts `2`; no proxy, credential, session, token, cookie or bypass was used.

## Symbols and windows

Exactly `FPT` (HOSE), `VNM` (HOSE), `PVS` (HNX), `ACV` (UPCOM) and benchmark `VNINDEX` were requested. `WINDOW_RECENT=2026-08-22..2026-09-15` and `WINDOW_OLD=2021-09-03..2021-09-27`; each is 25 calendar days and the old window is approximately five years earlier. No pilot crawl was started.

## Provider/client paths

- KBS via the public path documented by Vnstock: `/iis-server/investment/{stocks|index}/{symbol}/data_day`; provenance is `provider=kbs`, `acquisition_client=vnstock`.
- CafeF direct: `/du-lieu/Ajax/PageNew/TradeHistoryNew.ashx`, deterministic 30-row pages located by bounded binary page search.
- KBS financial raw-only: `/iis-server/investment/stock/finance-info/FPT`, one page and three quarterly observations.

## Market coverage

Every equity and VNINDEX returned `14` recent rows (`2026-08-24..2026-09-15`) and `16` old rows (`2021-09-06..2021-09-27`) from KBS. CafeF returned the same row counts/date spans for every equity. Thus current availability and approximately five-year technical history reach both passed without expanding either requested window.

## Per-symbol results

| Symbol | Recent | Old | Result | Finding |
|---|---:|---:|---|---|
| FPT | 14 | 16 | PASS | OHLCV, limit prices and value components valid; recent volume `MATCH`. |
| VNM | 14 | 16 | FAIL | CafeF old row `2021-09-09` has reference `85,400` but floor `194,400` and ceiling `223,600` VND/share: invalid price-band relation and canonical-corruption risk. |
| PVS | 14 | 16 | PASS | OHLCV, limit prices and value components valid; recent volume `MATCH`. |
| ACV | 14 | 16 | PASS | Required fields valid; recent KBS volume vs CafeF matched volume is `VALUE_CONFLICT` on 13/14 shared dates and is not silently reconciled. |

## VNINDEX result

PASS. Both windows returned valid daily OHLC index levels and provider volume (`14` recent, `16` old). Prices retain `INDEX_POINTS`; no equity price multiplier was applied. Provenance is KBS via Vnstock.

## Units / basis

KBS equity OHLC is `VENDOR_ADJUSTED`, stored as VND/share; volume is shares. VNINDEX uses index-level semantics. CafeF `BasicPrice`, `Ceiling` and `Floor` are multiplied by `1,000` to VND/share; `TotalValue`/`AgreedValue` are raw VND. `traded_value` is derived only when both same-row CafeF components are present. No missing value was changed to zero.

## Reconciliation findings

No averaging or source-priority overwrite occurred. KBS adjusted OHLC was not compared directly with CafeF reference/limit fields; those comparisons are classified `PRICE_BASIS_CONFLICT`/not performed. Recent volumes were `MATCH` for FPT, VNM and PVS. ACV is `VALUE_CONFLICT`; neither adding CafeF put-through volume nor treating it as matched volume consistently explains KBS volume.

## Access-control observations

The completed run received HTTP 200 for all requests and encountered no 401, 403, 429, CAPTCHA, managed challenge or login wall. No bypass was attempted. An earlier local attempt stopped after two KBS requests because the transport rejected CafeF's parseable JSON with a non-JSON content type; this was a local false-positive guard, not provider access control, and a new immutable run was created after correcting the parser.

## Data quality findings

KBS OHLC bounds, date ordering, duplicate-date checks, units and provenance passed in both windows. CafeF field schema, local trade-date conversion and value-component rules passed. The VNM 2021-09-09 limit-price anomaly is a required-field failure. The ACV cross-source volume conflict remains explicit and requires semantic investigation before any later promotion rule.

## Raw artifact summary

The completed run wrote `52` private ignored artifacts/metadata records under `data/raw/`: `41` CafeF pages and `11` KBS responses, each with request metadata, provider/client, adapter version, rights/execution labels, observation time and SHA-256. No raw payload is committed. Raw pages are append-only within the run; the report records summaries only.

## Financial raw-only observations

One bounded FPT KQKD quarterly response preserved three observations (Q2/2026, Q1/2026, Q4/2025) plus facts and source metadata. `ReportDate`, `DatePubDepartment`, `CreatedDate`, `LastUpdate`, period bounds, `YearPeriod`, `TermCode`, `United` and `AuditedStatus` remain raw. `published_at=null`, `available_at=null`, revision is internal observation only, and `pit_status=PIT_UNRESOLVED`. No financial fact entered features, clustering or backtest.

## PASS / PARTIAL / FAIL

**FAIL.** FPT, PVS, ACV and VNINDEX pass their required market checks; VNM fails because a required CafeF old-window price-band row is internally invalid. History depth itself passes. Under the explicit fail-closed criteria, one required-field corruption risk makes the project smoke fail.

## Pilot readiness

`NOT_READY`. Do not run the 50–60-symbol pilot. Blocking field: VNM CafeF historical `reference_price`/`ceiling_price`/`floor_price` consistency on `2021-09-09`. ACV volume reconciliation is also unresolved and must be documented or resolved before promotion policy.

## Next action

Investigate the VNM row using bounded provider evidence and define an explicit policy for provider-corrupt price-band rows; separately investigate ACV KBS-volume semantics. Then run a new four-symbol SOURCE_SMOKE. Do not start the pilot or scale crawl.
