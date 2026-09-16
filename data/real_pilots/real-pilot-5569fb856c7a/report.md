# REAL DATA STATUS

data_mode = real

**PILOT RESULT — NOT FINAL THESIS RESULT**

Vendor run: `vendor-pilot-39fa8ac5e1a1`
Canonical run: `canonical-1d2a54288bfc`
Feature run: `run-4a1a6203dba7`
Experiment: `experiment-de5f4d68afa0`

Symbols: FPT, GAS, HPG, MWG, PVS, REE, SSI, VCB, VHC, VNM
Date range: 2023-01-03 → 2025-12-31
Trading sessions: 748; benchmark: VNINDEX

## SEMANTICS RESOLVED

See [evidence and mapping table](../../../docs/data/kbs_pilot_semantics.md).

- Equity price multiplier=1000; index multiplier=1; volume multiplier=1 shares.
- vendor_adjusted: adj_close present; raw OHLC null. Technical adjusted-price proxy, not certified total return.
- va omitted; traded_value/liquidity_21 null and optional.
- Session day normalized in +07:00; available_at_method=research_assumption, EOD + 120 min, next-session execution.
- calendar_method=benchmark_derived; identity_status=provisional_verified_for_pilot; rf_annual=0 assumption.

## PIPELINE RESULT

Promotion QC PASS: input 8228, accepted 8228, quarantined 0, warnings 8, blocking errors 0.
Reference rows: securities 10, calendar 2192; corporate_actions/risk_free_rate empty.
QC missing sessions: 0; features: 360 rows / 36 monthly snapshots.
Clustering: 24 monthly snapshots, k=3, 240 assignments.
Transitions: 230 shared-security month-to-month observations.
Backtest: 2024-02-01 → 2025-12-31, 477 valuation sessions; next-close fractional return-space.
Acceptance: PASS

Latest eligible securities by feature:

| Feature | Securities |
|---|---:|
| mom_21 | 10 |
| mom_63 | 10 |
| mom_126 | 10 |
| mom_252 | 10 |
| vol_63 | 10 |
| beta_126 | 10 |
| mdd_126 | 10 |
| ram_63 | 10 |

Transition count matrix (aligned cluster labels):

| From / To | 0 | 1 | 2 |
|---|---:|---:|---:|
| 0 | 36 | 13 | 10 |
| 1 | 12 | 65 | 16 |
| 2 | 10 | 16 | 52 |

Performance (development pilot, not investment recommendation):

| Strategy | Cumulative net return | Annualized return | Maximum drawdown |
|---|---:|---:|---:|
| VNINDEX | 52.13% | 24.81% | -18.11% |
| cluster | -14.61% | -8.01% | -29.58% |
| equal_weight_universe | 24.52% | 12.28% | -26.45% |
| momentum_only | 35.96% | 17.62% | -26.85% |
| risk_only | 23.50% | 11.80% | -21.88% |

## REMAINING LIMITATIONS

- PILOT RESULT — NOT FINAL THESIS RESULT
- Retrospective vendor-adjusted price proxy, not verified total return or raw executable prices; adjustment revisions may affect results.
- available_at and calendar availability are research assumptions, not historical vendor timestamps.
- Provisional interval-limited identities and selected surviving universe; no claim of survivorship-free universe.
- VNINDEX-derived calendar; HOSE/HNX synchronization assumed.
- va omitted; traded_value and liquidity_21 null, excluded from required features.
- Corporate-actions and risk-free tables empty; rf_annual=0 is an assumption.
- Fractional return-space simulation excludes lots, settlement, dividends ledger and market impact.

Config, source snapshot and artifact hashes are saved with the experiment. Synthetic fixtures are excluded from this result.
