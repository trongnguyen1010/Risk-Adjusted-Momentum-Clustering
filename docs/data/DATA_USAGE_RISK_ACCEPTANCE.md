# DELTA Data Usage Risk Acceptance

## Scope

- Academic/thesis research.
- Private/local development and analysis.
- Non-commercial demo.
- No raw redistribution.

## Sources covered

- CafeF direct public paths.
- KBS public paths documented by the Vnstock acquisition client.

## Known uncertainty

Provider rights for automation, storage and reuse have not been explicitly verified. Public accessibility is not a license. CafeF and KBS therefore remain `RIGHTS_NOT_VERIFIED`; Vnstock software use is `ALLOWED_WITH_CONDITIONS` for research.

Governance keeps three labels distinct: `RIGHTS_VERIFIED` requires affirmative provider/license evidence; `RIGHTS_NOT_VERIFIED` describes the current CafeF/KBS rights state; `ACCEPTED_RESEARCH_RISK` is an execution decision and never upgrades the rights state.

## Accepted risk

The project owner accepts bounded use for private academic research/thesis development and non-commercial demo. The execution label is `ACCEPTED_RESEARCH_RISK`. This does not mean rights are verified, commercial or production use is approved, or raw redistribution is allowed.

## Technical guardrails

- Use low request rates, finite timeouts and bounded retries with single-threaded or very low concurrency.
- Do not bypass login, authentication, CAPTCHA, Cloudflare/managed challenge, paywall, 401/403, or rate limits; stop the affected path on access-control change.
- Respect `Retry-After` on 429 when it fits the bounded run; otherwise stop the path. Do not rotate proxies or identities.
- Preserve raw responses immutably with request provenance, UTC `fetched_at` and SHA-256 hash.
- Do not convert missing values to zero, mix price bases, infer units from magnitude, or backfill current snapshots into history.
- Derive CafeF `traded_value` only as same-row, same-provider, same-local-trade-date `TotalValue + AgreedValue`, and only when both components are present.

## Distribution guardrails

- Raw provider payloads remain private and local.
- Do not commit `data/`, publish raw provider datasets, or include raw payloads in a public thesis/demo.
- Public outputs may contain derived statistics, features, charts, clusters and results, with provider/source citation.

## Financial PIT restriction

Raw financial collection is allowed only as `RAW_ONLY_PIT_UNRESOLVED`. Preserve `ReportDate`, `DatePubDepartment`, `CreatedDate`, `LastUpdate`, `PeriodBegin`, `PeriodEnd`, `YearPeriod`, `TermCode`, `United`, `AuditedStatus`, document metadata and facts. Keep canonical `published_at` and `available_at` null/unmapped; revisions are internal raw observations only; set `pit_status=PIT_UNRESOLVED`. Financial facts must not enter historical clustering or backtests until a PIT-capable timing rule is approved.

## Production boundary

Commercial or production use requires a licensed/approved source and a separate reviewed decision.
