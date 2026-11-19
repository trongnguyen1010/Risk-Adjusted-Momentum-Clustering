# Assessment UI UAT and regression - Task 14

## Result

**Acceptance: PASS for the automated Task 14 gates, with the environment boundary documented below.** Frontend typecheck, production build, endpoint integration tests, and Playwright browser UAT passed. Generated screenshots are paired with the release pins in `response-pins.json`. No failed case was relabeled as passing.

## Release and environment pins

- Assessment release: `assessment_v1_run01`
- Revision: `assessment-v1-run01-20261116`
- Context / as of: `SIMULATED_AS_OF` / `2026-01-02`
- Required price session: `2025-12-31`
- Manifest SHA-256: `63a0b747d200638151052e0168b542316e013d8561916860416d1e4118bd09a8`
- Deterministic content SHA-256: `418def26a0db719205f01b73d71467adcd6d1930bd549bc509c9183309f3f8bb`
- Catalog / supporting stock API version: `delta-intelligence-v1`
- Exact response pins and source boundary: [response-pins.json](response-pins.json)

The UI ran from the local Task 14 frontend. Catalog, overview, and fundamentals requests were proxied to the live Render API. Assessment responses were served from the local verified `assessment_v1_run01` artifact because the deployed Assessment endpoint is not available. This validates the UI against the pinned response contract and real supporting APIs; it does not claim a deployed Assessment API end-to-end test. The stale state is an explicitly synthetic presentation fixture derived from a pinned A32 response.

## Acceptance checks

| Check | Result | Evidence |
|---|---|---|
| Frontend typecheck | PASS - `npm.cmd --prefix web/frontend run typecheck` | Completed 2026-11-19 |
| Frontend production build | PASS - `DELTA_BUILD_DIR=.next-task14-acceptance npm.cmd --prefix web/frontend run build` | Completed 2026-11-19 |
| Assessment endpoint integration | PASS - 2 tests | `$env:PYTHONPATH="web/backend;src"; python -m unittest tests.integration.test_assessment_endpoints -v` |
| Browser UAT | PASS - Playwright/Edge; no uncaught page errors | [ui-result.json](ui-result.json) |
| FPT current release and valid alternative A32 | PASS - both render from pinned release | [FPT screenshot](screenshots/fpt-current.png), [A32 screenshot](screenshots/a32-desktop.png) |
| 18-feature selector; one chart; 5/10-year history and URL Back/Forward | PASS | Browser assertions in [verify_assessment_ui.cjs](../../verify_assessment_ui.cjs) |
| Insufficient evidence and missing VCB | PASS - AAM shows `INSUFFICIENT_EVIDENCE`; VCB reports missing/404 | [AAM screenshot](screenshots/aam-insufficient.png), [VCB screenshot](screenshots/vcb-missing.png) |
| Revision mismatch and invalid lookback | PASS - HTTP 409 and 422 respectively | API assertions in [verify_assessment_ui.cjs](../../verify_assessment_ui.cjs) and endpoint integration tests |
| Stale presentation state | PASS as a synthetic fixture, explicitly labeled | [stale fixture screenshot](screenshots/a32-stale-fixture.png) |
| Mobile, keyboard, and theme | PASS - 390 px viewport has no horizontal overflow; focus order and light theme assertions pass | [mobile screenshot](screenshots/a32-mobile.png), [light theme screenshot](screenshots/a32-mobile-light.png), [ui-result.json](ui-result.json) |
| Response pins | PASS - revision, manifest hash, deterministic hash, context, and `as_of` match release pointer and artifact | [response-pins.json](response-pins.json) |

## Fixes made while completing UAT

- Added Playwright as a frontend development dependency and made the UAT script resolve it from `web/frontend`.
- Fixed an actual narrow-screen overflow caused by a long SHA-256 value in provenance details.
- Added accessible names to the theme toggle buttons for keyboard and assistive technology users.
- Updated the UI regression gate to verify that the real supporting API catalog is used and to write release/support API pins into its evidence.

## Remaining boundary

There are no failing automated Task 14 acceptance checks. A full deployment-level Assessment endpoint/browser run remains unavailable because the deployed Assessment API route returns 404 and the matching local `data/web/delta-intelligence-v4/manifest.json` bundle is absent. This does not invalidate the pinned local endpoint integration tests or UI tests above, but the evidence must not be described as a full production Assessment API test. The stale case is fixture-based, not a naturally stale production response. No human usability session was performed; the listed interaction cases are automated browser checks with saved screenshots.