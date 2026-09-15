# Validation status — 14/09/2026

## Current code checks

- `.venv\\Scripts\\python.exe -m unittest discover -s tests -v`: **54/54 PASS** in 57.964 seconds after documentation consolidation, legacy pilot-code removal and calendar-helper migration. Run outside the Windows sandbox because sandbox ACLs block `tempfile`/SDK subprocess directories.
- After the final `quote_state=partial` contract adjustment, the three product tests were rerun: **3/3 PASS** in 0.117 seconds.
- `python run.py product-build ...`: **PASS**, immutable bundle `artifacts/product/pilot-v1` contains 10 companies and hashes every public JSON artifact.
- HTTP smoke on port 8765: **PASS**. `/api/v1/health` returned `ok`; `/api/v1/companies/FPT` returned 748 price points and peers `HPG, SSI, VHC, VNM`; `/` returned HTTP 200 with the Delta Intelligence shell. The server process was stopped after the check.
- `node --check web/app.js` and `python -m compileall -q src tests`: **PASS**.
- `python run.py run --config configs/demo.json`: completed successfully before cleanup. Its generated run was deliberately deleted because it is reproducible synthetic output.
- All JSON files under `src/delta_t1/schemas` and `configs` parsed successfully.
- `python -m compileall -q src scripts tests`: PASS.
- `git diff --check`: no whitespace errors; CRLF conversion warnings only.

## Research-evidence status

- Complete retained real chains include `vendor-pilot-39fa8ac5e1a1` → `canonical-1d2a54288bfc` → `run-4a1a6203dba7` → `experiment-de5f4d68afa0`, summarized by `real-pilot-5569fb856c7a`; the later canonical/run/experiment chain is also retained as immutable evidence.
- Retained regression fixture: `run-f55b550e942d`, used only as reproducible synthetic test evidence.
- The real pilot is engineering evidence only and remains `LEGACY_NONCOMPLIANT_PILOT` for thesis use because its early clustering snapshots did not satisfy the new three-year observed-history rule.
- No large-scale or new live-source crawl was run during the audit.

## Cleanup status

Removed reproducible synthetic runs/experiments/canonical/offline pilots, temporary PDF/test extraction, one interrupted vendor run and one incomplete real-pilot folder. During product restructuring, also removed the superseded unresolved KBS config, old phase report and smoke vendor semantics/integrity documents after verifying they had no live code dependency and referenced evidence runs already removed. Complete real raw/vendor/canonical evidence was retained. The broken `data/real_pilots/latest.json` pointer was repaired to `real-pilot-5569fb856c7a` / `experiment-de5f4d68afa0`.

Documentation cleanup reduced `docs/` from 25 files to nine active documents, one index and one KBS evidence file required by immutable manifests. Duplicate audit/method/feature/backtest/source/phase documents, empty templates, four legacy pilot configs, three obsolete orchestration/generator scripts and four empty deliverable placeholder directories were removed. The benchmark-calendar helper was migrated from the deleted pilot module to `ingestion/calendar.py`.

The next valid evidence run is a representative multi-source pilot created only after source semantics and reconciliation rules pass Phase 1–3 of `PLAN.md`.

Pending explicit destructive-data approval: the following unreferenced directories total about 13.9 MB but were not deleted because the operation includes immutable research evidence:

- `data/vendor/vendor-26f2e2ce615c`
- `data/vendor/vendor-eb4e8568e275`
- `data/vendor/vendor-recovered-fccfaaa2b061`
- `data/canonical/canonical-19eac94c626f` (blocked)
- `data/canonical/canonical-98a1440ae1eb` (blocked)
- duplicate chain `canonical-bd5873e9eed2` → `run-563d11a7cc13` → `experiment-a3f51c72792a`

The active chain `vendor-pilot-39fa8ac5e1a1` → `canonical-1d2a54288bfc` → `run-4a1a6203dba7` → `experiment-de5f4d68afa0`, pinned `evidence-kbs-20260912`, `real-pilot-5569fb856c7a` summary and synthetic regression fixture must remain.
