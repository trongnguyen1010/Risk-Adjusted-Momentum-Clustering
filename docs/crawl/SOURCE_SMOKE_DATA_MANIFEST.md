# SOURCE_SMOKE Data Manifest

> Private/local academic research và non-commercial demo. `RIGHTS_NOT_VERIFIED` / `ACCEPTED_RESEARCH_RISK`. Raw provider payload không được commit hoặc tái phân phối.

## Canonical run

| Thuộc tính | Giá trị |
|---|---|
| Run ID | `source-smoke-20260916T122331Z-79427ec6` |
| Gate | `SOURCE_SMOKE=PASS` |
| Unlock | `REPRESENTATIVE_PILOT` only |
| Symbols | FPT/HOSE, VNM/HOSE, PVS/HNX, ACV/UPCOM; VNINDEX benchmark |
| Windows | recent `2026-08-22..2026-09-15`; old `2021-09-03..2021-09-27` |
| Inventory | 52 JSON + 52 metadata: 41 CafeF, 10 KBS market, 1 KBS financial |
| KBS provenance | `provider=kbs`; `acquisition_client=delta_public_http`; `endpoint_discovered_via=vnstock` |
| CafeF provenance | `provider=cafef`; `acquisition_client=direct` |
| Gate artifact | `data/raw/source_smoke/source-smoke-20260916T122331Z-79427ec6/gate.json` |

## Coverage và policy result

| Symbol | Recent rows | Old raw / eligible | Status | Bounded finding |
|---|---:|---:|---|---|
| FPT | 14 | 16 / 16 | PASS | volume `MATCHED_VOLUME` |
| VNM | 14 | 16 / 15 | PASS | `PROVIDER_CORRUPT_ROW`; exact evidence-pinned `EXCLUDE_ROW` |
| PVS | 14 | 16 / 16 | PASS | volume `MATCHED_VOLUME` |
| ACV | 14 | 16 / 16 | PASS | `SOURCE_SEMANTIC_DIFFERENCE`; keep source-qualified values separate |
| VNINDEX | 14 | 16 / 16 | PASS | index points; provider volume retained |

All observed date ranges are `2026-08-24..2026-09-15` and `2021-09-06..2021-09-27`. KBS hashes remain in the machine gate; the table below records the exact CafeF pages that actually contributed rows to each requested window.

## CafeF contributing-page traceability

| Symbol | Window | Page | SHA-256 |
|---|---|---:|---|
| FPT | recent | 1 | `953a2e4aab1fd0fc7e5c6f3210f596738f96259d5861e148bb8dc825c35af977` |
| FPT | old | 42 | `1e35a64d5ea38f9b62a53aaac3030b6b7ff26d5c4c78201425d7c847845f08e6` |
| VNM | recent | 1 | `f0e21c1356f2378782593036ec7576b7dbc8b567f3f056e9401bfdb3be0d045c` |
| VNM | old | 42 | `edfd56564be347f8a408c358720ec2790c5ea985bf0d55af296b863a37dae1ef` |
| PVS | recent | 1 | `b26b350f5cd7d105aa657bf45b2f1b8e86081b44bc4e72736f363fbd96953166` |
| PVS | old | 41 | `e3186d89e37e3d8e450cc0178919a3dd8cc18f40a02788a89f8945912cbd7d57` |
| PVS | old | 42 | `e3b182b5e248ea54fcde99c96ed4648c722822d0c6c0b2a868a3079c6e84306f` |
| ACV | recent | 1 | `a90cb58d14f72ee51642e480bff99470fa2676a3b5ae379232951e3879a89acb` |
| ACV | old | 42 | `af14c91dfb4fee4a1f7069cf3313ec90774106cc7df8b217f0e4c6e94e1044bb` |

Paths follow `data/raw/cafef/source-smoke-20260916T122331Z-79427ec6/{SYMBOL}-page-{NNN}.json`; each has a sidecar metadata record. Search-only pages are hashed in `gate.json` but are not falsely presented as window contributors.

## Anomaly and semantic evidence

| Finding | Evidence | Policy |
|---|---|---|
| VNM `2021-09-09` | CafeF reference `85,400`, floor `194,400`, ceiling `223,600` VND/share; adjacent rows coherent | raw retained; row status `INVALID_REQUIRED_MARKET_ROW`; exclude only exact pinned row; mismatch fails window |
| ACV latest five shared dates | KBS differs from both CafeF matched and matched+put-through volume; no stable multiplier | `SOURCE_SEMANTIC_DIFFERENCE`; `KEEP_SEPARATE_NO_EQUALITY_ASSUMPTION` |
| Price basis, all equities | KBS `VENDOR_ADJUSTED`; CafeF reference/limit basis | no direct comparison, average or overwrite |

## Supporting evidence

| Domain | Scope | Status |
|---|---|---|
| Corporate action | FPT cash dividend; announcement `2026-05-22`, ex-right `2026-05-28`, 1,000 VND/share | `PARTIAL`; record/payment date unavailable |
| Shares/capital structure | FPT, VNM, PVS, ACV | `CURRENT_SNAPSHOT_ONLY`; no historical backfill |
| Financial raw-only | FPT KQKD Q4/2025, Q1/2026, Q2/2026; hash `29a5b8e7f0e4ab8397a01a66505b92d21eac5d05cf2b7e695ee4703f3068ef79` | `RAW_ONLY_PIT_UNRESOLVED`; excluded from analytics |

## Non-canonical runs

`source-smoke-20260916T111529Z-af9bc570` is the earlier failed evidence run that exposed the VNM and ACV issues. `source-smoke-20260916T120608Z-e1282509` failed closed on transient JSON retry exhaustion and emitted a FAIL gate with no unlocks. Neither run is promoted or overwritten.

Known unknowns remain explicit: VNINDEX volume unit, FPT corporate-action record/payment dates, historical shares, and financial `published_at`/`available_at`. This manifest contains metadata and hashes only, never raw payload.
