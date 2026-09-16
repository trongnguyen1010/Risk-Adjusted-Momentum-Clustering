# Agent Prompt — DELTA Real Source Discovery + SOURCE_SMOKE

Copy toàn bộ prompt này cho coding/research agent.

---

You are working on:

`trongnguyen1010/Risk-Adjusted-Momentum-Clustering`

The repository has already completed architecture cleanup and M1 readiness refactoring.

Your task is **NOT** another architecture refactor.

Your task is to perform the first controlled **real-source discovery + SOURCE_SMOKE preparation/execution** for DELTA.

==================================================
0. HARD BOUNDARIES
==================================================

DO NOT:

- crawl >=50 symbols;
- run the representative pilot;
- run >=300-symbol collection;
- bypass authentication;
- bypass CAPTCHA;
- bypass anti-bot protections;
- evade rate limits;
- scrape paywalled/private data without permission;
- commit secrets;
- commit large real datasets;
- guess undocumented units;
- infer a multiplier only from magnitude;
- silently forward-fill;
- convert missing to zero;
- average source conflicts;
- call current listings a historical universe;
- modify immutable legacy raw evidence;
- implement Dynamic Clustering;
- expand product features.

If CafeF or VietFin requires access not legitimately available,
record the blocker and stop that source.

==================================================
1. READ BEFORE CODE
==================================================

Read:

README.md
AGENTS.md
CONTRIBUTING.md

docs/README.md
docs/PROJECT_MAP.md
docs/ROADMAP.md
docs/DATA_CONTRACT.md
docs/DATA_PIPELINE.md
docs/FEATURE_SYSTEM.md

docs/crawl/README.md
docs/crawl/DATA_COLLECTION_GUIDE.md
docs/crawl/FIELD_CATALOG.md
docs/crawl/SOURCE_DISCOVERY.md
docs/crawl/SOURCE_SMOKE.md
docs/crawl/TEAM_CRAWLING.md
docs/crawl/HANDOFF_TEMPLATE.md
docs/crawl/sources/SOURCE_NOTE_TEMPLATE.md

Inspect:

configs/data/source_smoke.example.json

src/delta_t1/ingestion/sources/
src/delta_t1/ingestion/normalization/
src/delta_t1/ingestion/reconciliation/
src/delta_t1/ingestion/planning.py
src/delta_t1/schemas/shares_history.json
src/delta_t1/schemas/prices_daily.json
src/delta_t1/schemas/financial_reports.json
src/delta_t1/schemas/financial_facts.json

Run baseline tests before changes.

==================================================
2. REORGANIZE CRAWL DOCS FIRST
==================================================

Use `docs/crawl/README.md` as the only data-collection navigation entry point from outside the crawl folder.

Create/ensure:

docs/crawl/
  README.md
  DATA_COLLECTION_GUIDE.md
  FIELD_CATALOG.md
  SOURCE_DISCOVERY.md
  SOURCE_SMOKE.md
  TEAM_CRAWLING.md
  HANDOFF_TEMPLATE.md
  AGENT_SOURCE_SMOKE_PROMPT.md
  sources/
    SOURCE_NOTE_TEMPLATE.md

Update all Markdown links.

Do not keep duplicate copies of DATA_COLLECTION_GUIDE.md.

Update docs/README.md so `docs/crawl/README.md` is the entry point for data collection.

==================================================
3. SOURCE TARGETS
==================================================

Primary source candidates:

A. CafeF
B. VietFin

Existing Vnstock/KBS is legacy engineering evidence and may be used only as:
- a comparison source where appropriate;
- an example of source-semantics handling.

Do not treat Vnstock/KBS as the final source of truth.

==================================================
4. DISCOVERY BEFORE AUTOMATION
==================================================

For each source separately:

1. Identify the public UI/page/document that exposes:
   - historical market data;
   - company/security metadata;
   - share/capital structure data;
   - financial statements if available;
   - corporate actions if available.

2. Inspect public browser requests using legitimate access.

3. Record:
   - method;
   - host/path;
   - query/body params;
   - pagination;
   - date boundary;
   - sort order;
   - response schema;
   - content type;
   - source timestamps;
   - rate behavior.

4. Review:
   - Terms/access policy;
   - login/subscription requirement;
   - automation restrictions.

5. If access is blocked or restricted:
   STOP.
   Write the blocker.
   Do not work around it.

==================================================
5. CREATE SOURCE NOTES
==================================================

Create:

docs/crawl/sources/CAFEF.md
docs/crawl/sources/VIETFIN.md

Use SOURCE_NOTE_TEMPLATE.md.

Each file must include explicit lifecycle status:

DISCOVERED
ACCESS_TESTED
SEMANTICS_VERIFIED
PILOT_APPROVED
PRODUCTION_APPROVED

Do not mark a later state without evidence.

==================================================
6. SOURCE_SMOKE SYMBOL SET
==================================================

Target 3–5 real securities.

Preferred initial candidates:

- FPT — HOSE, long history, known corporate-action case;
- VNM — HOSE, long history;
- PVS — HNX;
- ACV — UPCOM;
- one short-history or inactive/identity edge case discovered and documented.

If a symbol is unsupported by a source, replace it with a documented equivalent.

Do not silently change the set.

==================================================
7. MARKET FIELDS TO VERIFY
==================================================

Required for the new real smoke:

trade_date

open
high
low
close

reference_price
ceiling_price
floor_price

volume
traded_value

trading_status if source provides it

price/adjustment basis
available/fetched semantics
source provenance

Canonical units:

price = VND/share
volume = shares
traded_value = VND

A source field is not considered verified until:
- UI/source evidence exists;
- unit is understood;
- mapping is documented;
- transform is explicit.

==================================================
7A. SHARE / CAPITAL-STRUCTURE AVAILABILITY
==================================================

For each source, check:

- current listed shares available;
- current outstanding shares available;
- issued/treasury shares available;
- historical changes available;
- effective date available;
- publication/available time available.

Record exactly one status:

VERIFIED_AVAILABLE
CURRENT_SNAPSHOT_ONLY
HISTORICAL_UNAVAILABLE
BLOCKED

Do not assume share counts are equal and do not backfill current counts into history. A market-price source does not fail solely because it lacks historical shares; another approved source may supply the domain, but the limitation must be explicit.

==================================================
8. RAW FIRST
==================================================

Do not code a parser that throws away unknown provider fields.

Preserve raw response/document bytes.

Every raw object/page must be tied to:

source
underlying provider if any
request metadata
symbol
date range
fetched_at
adapter version
page/cursor
raw SHA-256
raw path
HTTP/error state

Do not mutate raw after checkpoint.

==================================================
9. IMPLEMENT SOURCE ADAPTER ONLY AFTER SEMANTICS
==================================================

Only after a source reaches SEMANTICS_VERIFIED:

implement/complete the adapter under:

src/delta_t1/ingestion/sources/

Preferred files:

cafef.py
vietfin.py

Use the existing source abstraction.

Adapter responsibilities:

- acquire;
- checkpoint;
- retain provenance;
- respect retry/rate settings;
- return source records.

Adapter must NOT:

- choose canonical winner;
- compute features;
- silently repair source data;
- hide conflicts.

==================================================
10. NORMALIZATION
==================================================

Map source-specific fields into normalized candidates.

Explicitly define:

source field
canonical candidate field
source unit
canonical unit
transform/multiplier
timezone
price basis
mapping version

Unknown semantics remain unresolved/null/raw-only.

Never infer raw_close from adjusted close.

==================================================
11. CROSS-SOURCE RECONCILIATION
==================================================

Use the existing field-level reconciliation architecture.

For matching:

security_id + trade_date

compare at least:

open
high
low
close
reference_price
ceiling_price
floor_price
volume
traded_value

Classification:

MATCH
MISSING_ON_SOURCE
VALUE_CONFLICT
UNIT_CONFLICT
PRICE_BASIS_CONFLICT
TIMING_CONFLICT
IDENTITY_CONFLICT

Do not average conflicts.

If source priority is needed:
- do not invent one;
- leave unresolved until an approved versioned policy exists.

==================================================
12. CORPORATE ACTION CHECK
==================================================

Use at least one known corporate-action case.

For example, FPT may be used if the relevant source period is supported.

Verify:

announcement/ex/record/effective date
event type
ratio/cash terms
whether historical price series is adjusted

Do not attempt to reconstruct unadjusted prices without an approved methodology.

==================================================
13. FINANCIAL REPORT CHECK
==================================================

Inspect at least three quarterly reports.

For each, verify where possible:

security
fiscal year
fiscal quarter
period start/end
consolidated/separate
published_at
available_at
revision/restatement
currency
unit scale

Check sample raw facts from:
income statement
balance sheet
cash-flow statement

Important:

YTD != standalone quarter.

Do not reconcile them as equivalent.

==================================================
14. LOCAL DATA ARTIFACTS
==================================================

Do NOT commit large real raw data.

Use the repository's immutable vendor/run design or a local data_collection workspace.

Each smoke collection must produce:

manifest.json
raw/
checksums.sha256
collector_report.md

Record exact locations in the final report.

==================================================
15. SOURCE_SMOKE GATE
==================================================

Build the evidence object required by:

source_smoke_report(...)

The gate must remain fail-closed.

PASS requires:

- synthetic == false;
- 3–5 symbols;
- representative exchange evidence;
- >=5-year request or documented source history limitation;
- required market fields verified;
- corporate action inspected;
- shares/capital-structure availability status documented;
- >=3 quarterly reports inspected;
- collection semantics verified;
- rights reviewed;
- evidence hashes present.

If either source cannot satisfy requirements:
return BLOCKED for that source.

Do not fake PASS.

==================================================
16. CONFIG
==================================================

Create a real local smoke config derived from:

configs/data/source_smoke.example.json

Do not put secrets in it.

If committing an example config:
use placeholders only.

Real tokens/credentials, if legitimately required, belong in environment variables and must never be committed.

==================================================
17. TESTS
==================================================

Add/update tests for:

- adapter field parsing;
- unit transforms;
- new source mapping;
- pagination edge cases;
- empty response;
- duplicate page/cursor;
- raw hash/checkpoint;
- field-level reconciliation;
- source smoke evidence;
- fail-closed restrictions.

Use captured minimal fixtures only when license/terms permit.

Do not commit large or restricted raw samples.

==================================================
18. DOCUMENTATION OUTPUT
==================================================

Update:

docs/crawl/sources/CAFEF.md
docs/crawl/sources/VIETFIN.md

and relevant:

docs/DATA_PIPELINE.md
docs/PROJECT_MAP.md
docs/REPRODUCIBILITY.md
docs/DECISIONS.md
CHANGELOG.md

Only update lifecycle status to what evidence supports.

==================================================
19. ACCEPTANCE
==================================================

Run:

python -m unittest discover -s tests -v
python -m compileall -q src tests scripts run.py
node --check web/app.js

Check:

JSON parsing
Markdown links
git diff --check
no committed secrets
no large real dataset files
no unauthorized access workaround

If legitimate source access is available, execute only the bounded SOURCE_SMOKE.

Do not continue to representative pilot.

==================================================
20. FINAL REPORT
==================================================

Return:

A. Sources attempted
B. Access/rights status
C. Exact endpoints/documents discovered
D. Exact fields verified
E. Unit/timezone/price-basis decisions
F. Corporate-action evidence
G. Financial-report evidence
H. Cross-source MATCH/conflicts
I. SOURCE_SMOKE gate result for each source
J. Exact files created/modified
K. Tests before/after
L. Local raw artifact paths and hashes
M. Unresolved blockers
N. Explicit confirmation that no >=50-symbol or large crawl was run

==================================================
21. STOP CONDITION
==================================================

After producing the SOURCE_SMOKE result:

STOP.

Do not start:

REPRESENTATIVE_PILOT
M1_SCALE
EXTENDED_SCALE

without a separate explicit task.
