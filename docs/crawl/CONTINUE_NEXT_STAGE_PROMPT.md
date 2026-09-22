You are working inside the repository:

`Risk-Adjusted-Momentum-Clustering`

Current branch/workstream:

`m1-scale-500-team-crawl`

Your task is to execute EXACTLY ONE DELTA stage: chính xác stage được ghi tại
`Execution Progress / Handoff → Next allowed stage` trong Master Plan; không suy ra
B0 hoặc bất kỳ stage nào từ chuỗi stage tĩnh.
Sau khi self-review và test stage đó, cập nhật handoff và STOP.

---

# 0. Mandatory project context

Before changing anything, read:

```text
AGENTS.md
README.md
docs/crawl/M1_DATA_ENRICHMENT_AND_UNIVERSE_EXPANSION_MASTER_PLAN.md
docs/DATA_CONTRACT.md
docs/DATA_PIPELINE.md
docs/FEATURE_SYSTEM.md
```

Also inspect only the code/config/tests/artifacts necessary to understand the current M1 canonical market dataset and market-feature readiness.

Follow `AGENTS.md` single-agent execution policy. Read the current
`Execution Progress / Handoff`, identify its `Next allowed stage`, and do not
infer a stage from this template's historical examples.

---

# 1. Current source-of-truth state

Treat the current immutable baseline as approximately:

```text
Selected securities: 500
Daily market rows: 614,430
Observed span >=3 years: 500
Observed span >=5 years: 484

Momentum21 available: 213
Momentum63 available: 193
Momentum126 available: 184
Momentum252 available: 169
Market-feature-ready: 169

Latest completed research snapshot:
2026-08-28

Canonical Market Data:
PASS

Strict Research Readiness:
PARTIAL
```

Do NOT silently replace these values with another legacy snapshot.

If repository artifacts contain a different value such as 168 vs 169:

* identify the exact artifact;
* identify the exact policy/snapshot producing it;
* explain the discrepancy;
* choose the canonical A1 baseline using current approved evidence;
* do not rewrite historical evidence.

Do not say `M1 PASS`.

---

# 2. Hard A1 scope

A1 is an AUDIT stage.

STRICTLY FORBIDDEN:

```text
NETWORK ACCESS
SOURCE CRAWLING
RECOVERY
BACKFILL
UNIVERSE EXPANSION
CANONICAL MUTATION
BASELINE OVERWRITE

forward-fill
backward-fill
interpolation
previous-close substitution
missing -> 0
synthetic OHLC
synthetic volume
fake zero-return sessions
timeline compression
```

No real missing row may be manufactured.

No canonical baseline artifact may be modified.

---

# 3. Core methodological requirement

A missing canonical row is NOT automatically a provider gap.

Expected-session reasoning must consider:

```text
exchange session
AND
active listing interval
AND
effective identity interval
```

Also account for uncertainty around:

```text
listing date
delisting date
exchange transfer
ticker rename
historical identity
suspension/halt
calendar provenance
parser/normalization problems
```

If only an observed-union calendar is available:

```text
calendar_status = PROVISIONAL_OBSERVED
```

Never call it an official exchange calendar.

Do not classify:

```text
PROVIDER_GAP_CONFIRMED
```

solely because canonical data is missing.

When evidence is insufficient, preserve uncertainty.

---

# 4. First inspect and reuse existing architecture

Before creating new modules, inspect relevant existing functionality such as:

```text
src/delta_t1/ingestion/calendar.py
src/delta_t1/ingestion/m1_scale.py
src/delta_t1/ingestion/m1_scale_quality.py
src/delta_t1/ingestion/planning.py
src/delta_t1/ingestion/quality.py
src/delta_t1/ingestion/recovery.py

scripts/report_m1_scale_quality.py
scripts/verify_m1_scale_handoff.py

configs/data/*
tests/unit/*
tests/integration/*
tests/regression/*
```

These paths are hints, not a requirement to modify all of them.

Prefer existing reusable utilities.

Avoid broad refactoring.

A focused module such as:

```text
src/delta_t1/ingestion/session_audit.py
```

is acceptable if needed.

A focused config for enrichment is acceptable if needed.

Do not introduce a new framework or service.

---

# 5. Build Expected Session Grid

For every baseline security, construct the best defensible expected-session representation available from current LOCAL evidence.

Recommended fields:

```text
security_id
ticker
exchange

session_date

listing_date
delisting_date

identity_effective_from
identity_effective_to

expected_session

calendar_status
identity_status
```

If historical identity information is unresolved, represent that uncertainty explicitly.

Do not invent identity intervals.

Do not infer listing boundaries merely from first/last canonical row unless an existing approved policy explicitly permits that interpretation.

---

# 6. Compare Expected vs Observed

For relevant security/session pairs determine:

```text
expected_session
observed_session
missing_flag
```

Preserve enough evidence for the result to be audited.

---

# 7. Missing classification

Use only project-approved classifications when applicable:

```text
PROVIDER_GAP_CANDIDATE
PROVIDER_GAP_CONFIRMED
PARSER_OR_NORMALIZATION_CANDIDATE
IDENTITY_GAP_CANDIDATE
NOT_LISTED
DELISTED
SUSPENDED_OR_HALTED
CALENDAR_UNCERTAIN
MISSING_ON_PRIMARY
MISSING_ON_SECONDARY
MISSING_ALL_SOURCES
VALUE_CONFLICT
UNIT_CONFLICT
PRICE_BASIS_CONFLICT
TIMING_CONFLICT
IDENTITY_CONFLICT
UNRESOLVED_MISSING
```

A1 has NO NETWORK and NO RECOVERY.

Therefore do not manufacture confirmations that require source querying.

Use conservative classifications.

---

# 8. Missing audit dataset

The detailed audit should support fields equivalent to:

```text
security_id
ticker
exchange
trading_date

expected_session
observed_session

missing_classification

latest_21_relevant
latest_63_relevant
latest_126_relevant
latest_252_relevant
latest_300_relevant

canonical_source
identity_status
calendar_status
```

---

# 9. Per-security metrics

Calculate:

```text
expected_sessions_total
observed_sessions_total
missing_sessions_total
coverage_ratio
```

Latest-window missing counts:

```text
missing_last_21
missing_last_63
missing_last_126
missing_last_252
missing_last_300
```

Gap structure:

```text
max_consecutive_missing
first_missing_date
last_missing_date
missing_range_count
```

Readiness:

```text
mom21_complete
mom63_complete
mom126_complete
mom252_complete
market_feature_ready
```

The 100% required-real-observation rule is mandatory.

Do not weaken it.

---

# 10. Recovery priority

Every non-ready security should receive a recovery/investigation bucket when defensible:

```text
P0:
1–5 missing sessions inside latest required 252-session window

P1:
6–20

P2:
21–63

P3:
>63

P4:
structural / identity / calendar / extreme sparsity investigation
```

Examples appropriate for P4:

```text
extreme sparse history
identity uncertainty
listing mismatch
exchange transfer
provider-symbol mismatch
calendar anomaly
very low coverage despite long calendar span
```

Do not blindly classify structurally ambiguous securities as recoverable.

---

# 11. Market-priority handling

The report asks for important non-ready securities.

Do NOT create an ad-hoc investment score.

If an approved deterministic acquisition/market-priority field already exists, use it and cite its source.

If B1-style deterministic market priority does not yet exist, clearly state that this question cannot yet be answered with a formally frozen priority score.

You may report available factual proxies only if already present in the baseline evidence, while clearly labeling them as descriptive rather than research eligibility.

Popularity must never determine research eligibility.

---

# 12. Required immutable outputs

Create a NEW versioned A1 artifact directory under the existing enrichment artifact convention, for example:

```text
artifacts/data_enrichment/<run_id>/
```

Do not overwrite an existing run.

Generate:

```text
missing_session_audit.parquet
missing_session_by_symbol.csv
missing_session_by_date.csv
recovery_priority.csv
missing_classification_summary.json
stage_a1_report.md
```

Where practical, also include enough manifest/hash metadata to identify the baseline inputs used by A1.

Do not copy large baseline datasets unnecessarily.

Reference immutable existing artifacts when possible.

---

# 13. stage_a1_report.md mandatory questions

The report MUST answer, using actual evidence:

1. P0 count
2. P1 count
3. P2 count
4. P3 count
5. P4 count
6. Number of securities missing exactly 1 session
7. Number missing <=5 sessions
8. Number missing <=20 sessions
9. Exchange distribution of missing observations/securities
10. Year/month concentration of missing observations
11. Whether any provider-specific pattern is supported by current LOCAL evidence
12. Top 50 easiest recoveries
13. Market-important non-ready securities, only where deterministic evidence exists
14. Securities that appear structural rather than simple recoveries
15. Theoretical maximum readiness under explicitly stated and defensible assumptions
16. Securities not worth blind recovery and why

Do not overstate certainty.

If a mandatory question cannot be answered from A1's no-network evidence, explicitly say:

```text
NOT DETERMINABLE IN A1
```

and explain what later stage/evidence is required.

That is preferable to guessing.

---

# 14. Critical consistency check

Reconcile the A1 result with the current baseline feature-readiness artifact.

Specifically verify why current market-feature-ready is expected to be approximately 169.

If A1 independently derives a different number:

DO NOT force it to 169.

Investigate and report whether the difference comes from:

```text
different latest snapshot
calendar assumptions
identity assumptions
feature formula semantics
required-session counting semantics
artifact version mismatch
legacy report mismatch
```

Preserve both pieces of evidence until reconciled.

---

# 15. Minimum critical tests

Add only methodology-protecting tests that are required by the new A1 implementation.

At minimum cover relevant cases for:

```text
expected sessions respect listing/delisting evidence
missing-session detection
missing is not zero
no forward/back fill
no interpolation
baseline cannot be overwritten
Momentum252 completeness requires complete required observations
structural/uncertain cases do not become confirmed provider gaps
deterministic audit/recovery-priority output
```

Reuse existing fixtures and tests when possible.

Avoid cosmetic over-testing.

---

# 16. Required project gates

Follow AGENTS.md.

Before implementation record the baseline test state.

Use the repository Python environment when available:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

After implementation run the mandatory relevant gates again.

Also run targeted A1 tests separately so failures are easy to diagnose.

Do not delete or weaken tests to obtain PASS.

Record exact commands and outcomes in the stage report.

---

# 17. Mandatory self-review

After implementation and artifact generation, self-review the exact assigned stage:

```text
stage scope
baseline/artifact immutability
research and data invariants
provenance and deterministic outcomes
test and artifact evidence
truthfulness of stage result and handoff
```

Fix concrete findings, rerun relevant tests/artifacts, then update progress. If a
methodology-sensitive decision needs approval, record `MANUAL_REVIEW_REQUIRED` and
STOP; do not silently approve or substitute a model-specific review requirement.

---

# 18. Persistent Progress / Handoff

We need the repository to remain transferable between people and sessions.

DO NOT create a separate floating status document.

Use the existing master plan:

```text
docs/crawl/M1_DATA_ENRICHMENT_AND_UNIVERSE_EXPANSION_MASTER_PLAN.md
```

Add an `Execution Progress / Handoff` section near the beginning of the document if one does not already exist.

If it exists, update it rather than duplicating it.

Use a compact structure equivalent to:

```markdown
## Execution Progress / Handoff

Last updated: <timestamp>
Branch: <branch>
Base commit: <commit before stage, if available>

Current initiative:
M1 Data Enrichment & Universe Expansion

Last completed stage:
A1 — Missing Session Audit

Stage result:
PASS | PARTIAL | FAIL | BLOCKED

Latest run/artifact:
<run_id/path>

Key evidence:
- baseline securities: ...
- market-feature-ready baseline: ...
- P0: ...
- P1: ...
- P2: ...
- P3: ...
- P4: ...
- exact-1-missing: ...
- <=5 missing: ...
- <=20 missing: ...
- theoretical max readiness: ...
- self-review result: ...

Unresolved blockers:
- ...

Next allowed stage:
A2 — Local Raw / Quarantine Salvage
```

Also maintain a compact stage table:

```markdown
| Stage | Status | Evidence / Run | Notes |
|---|---|---|---|
| A1 Missing Session Audit | PASS/PARTIAL/... | <run> | <short note> |
| A2 Local Salvage | NOT_STARTED | — | — |
...
```

Rules:

* NEVER retroactively mark a prior stage PASS without explicit evidence.
* NEVER mark A2 completed.
* Do not fabricate commit hashes or artifact IDs.
* If A1 is BLOCKED/FAIL, `Next allowed stage` remains A1 remediation, not A2.
* If A1 is PARTIAL but sufficient to proceed, explain exactly why.
* Progress records are pointers to evidence, not replacements for immutable stage artifacts.
* Keep this section concise so future agents can read it cheaply.

Do not create another standalone status/audit/archive Markdown file.

---

# 19. Final report to user

Return a concise Vietnamese report with:

```text
Stage:
Result:

Self-review:

Files changed:

Artifact run:
Artifact files:

Baseline:
Market-feature-ready:

P0:
P1:
P2:
P3:
P4:

Exactly 1 missing:
<=5 missing:
<=20 missing:

Main findings:

Unresolved:

Progress/Handoff updated:
YES/NO

Next allowed stage:
```

If A1 PASSes:

```text
Next allowed stage:
A2 — Local Raw / Quarantine Salvage
```

Do NOT implement A2.

Do NOT crawl.

Do NOT recover any observation.

STOP.
