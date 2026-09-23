# CafeF Primary Migration Audit

## 1. Scope and result

Stage C0 is a static architecture/migration audit. It read repository docs, source and
existing evidence only. No market request, crawl, canonical mutation, feature rebuild,
schema migration or executable adjustment logic was performed.

Audit result: the existing system has strong reusable provenance, immutability,
identity, reconciliation and complete-window foundations, but its active market
canonical and downstream consumers encode a single-row `raw_close/adj_close +
adjustment_basis` model. The M1 scale path is concretely KBS-primary. A CafeF-primary
experiment therefore requires a separate raw observation table and a separately
derived research-price table; changing source priority is insufficient.

## 2. Current pipeline map

```text
KBS public HTTP / CafeF direct
  ↓ representative_pilot.py / m1_scale.py
immutable per-request raw bytes + hashes + run/resume identity
  ↓ map_kbs_wire_ohlcv_row / map_trade_history_row
source-qualified normalized rows
  ↓ representative_pilot_canonical.py / m1_scale.map_scale_handoff_candidates
prices_daily candidate
  - KBS close → adj_close
  - adjustment_basis → vendor_adjusted
  - raw OHLC → null
  - CafeF → traded_value/reference evidence only
  ↓ schema/QC + offline promotion
immutable canonical prices_daily + benchmark + observed-union calendar
  ↓ session_audit.py
expected-vs-observed missing audit (calendar/identity uncertainty retained)
  ↓ primary_recovery.py / secondary_recovery.py / identity_recovery.py
KBS retry + CafeF diagnostic reconciliation + identity evidence
  ↓ canonical_enriched_v2.py
new immutable KBS-basis canonical version
  ↓ features.market.build_features / features.rebuild
price selected by adjustment_basis; returns/momentum/risk/features
  ↓ m1_scale_quality.py / product.builder / experiments
readiness, EDA and dashboard-facing artifacts
```

## 3. Dependency classification vocabulary

- `SOURCE_AGNOSTIC`: no provider or price-layer assumption.
- `KBS_SPECIFIC_BUT_ISOLATED`: KBS code can remain as a validation adapter.
- `KBS_BASIS_DEPENDENT`: behavior assumes KBS `vendor_adjusted` semantics.
- `CANONICAL_SCHEMA_DEPENDENT`: tied to current `prices_daily` shape/key.
- `FEATURE_ASSUMES_ADJUSTED_PRICE`: calculates from `adj_close` for non-unadjusted basis.
- `REUSABLE_WITH_SMALL_CHANGE`: sound abstraction needs explicit new fields/table.
- `REQUIRES_REDESIGN`: current responsibility conflates raw and research semantics.
- `DO_NOT_REUSE`: unsafe for new layer without replacing the relevant behavior.

## 4. File/module architecture audit

| File / symbol | Classification | Current role and assumption | CafeF-primary action | Complexity |
|---|---|---|---|---|
| `src/delta_t1/ingestion/sources/cafef.py::CafeFSource` | REUSABLE_WITH_SMALL_CHANGE | bounded endpoint access and envelope validation | retain acquisition; add a raw-only mapping contract and stop deriving combined `traded_value` by default | MEDIUM |
| `cafef.py::map_trade_history_row` | REQUIRES_REDESIGN | maps close/adjusted diagnostics and sums matched+put-through into `traded_value` | emit separate components; never label provider adjusted as DELTA price | MEDIUM |
| `cafef_contract_validation.py::field_contract` | REUSABLE_WITH_SMALL_CHANGE | precise field/unit/status evidence | preserve as historical input; new contract version only after approved stage evidence | LOW |
| `cafef_deep_discovery.py` | KBS_BASIS_DEPENDENT | compares CafeF to KBS and declares cross-check-only for KBS canonical | preserve evidence; do not reuse KBS compatibility as CafeF-primary acceptance rule | LOW |
| `additional_market_source_discovery.py` | KBS_BASIS_DEPENDENT | classifies candidates against KBS `adj_close` | reuse provider catalog only; redesign comparison around same-layer raw fields | MEDIUM |
| `sources/vnstock.py` / KBS public adapter | KBS_SPECIFIC_BUT_ISOLATED | produces `VENDOR_ADJUSTED` KBS OHLCV | keep as validation/legacy comparator | LOW |
| `representative_pilot.py` raw store/resume helpers | REUSABLE_WITH_SMALL_CHANGE | immutable artifacts, exact run identity; jobs fixed to KBS OHLCV + CafeF auxiliary data | extract/reuse generic raw store and resume contract for CafeF-only jobs | MEDIUM |
| `m1_scale.py` shard/run/handoff verification | KBS_SPECIFIC_BUT_ISOLATED; REUSABLE_WITH_SMALL_CHANGE | exactly five KBS-identified shards, fixed source roles and 100 symbols/shard | reuse checksum/resume/merge gates; C1-PREP must generate balanced CafeF partitions, not copy assignments | HIGH |
| `normalization/market.py::map_record` | CANONICAL_SCHEMA_DEPENDENT | one `adjustment_basis`; writes `raw_*` only for unadjusted and `adj_close` otherwise | split raw normalization from research-price derivation | HIGH |
| `reconciliation/candidates.py::CandidateRecord` | REUSABLE_WITH_SMALL_CHANGE | retains canonical/comparison keys, source, raw hash and field semantics | add observation ID/provider key and raw-vs-research layer semantics | LOW |
| `reconciliation/rules.py::reconcile_candidates` | REUSABLE_WITH_SMALL_CHANGE | field conflicts, no averaging, approved source priority | raw conflicts should remain multi-observation records; selection policy must be layer-aware | MEDIUM |
| `promotion.py::promote` | CANONICAL_SCHEMA_DEPENDENT | legacy verified-vendor → current canonical tables | do not use for raw-to-research derivation; create experiment-specific promotion boundaries | HIGH |
| `representative_pilot_canonical.py::map_canonical_candidates` | KBS_BASIS_DEPENDENT | KBS close → `adj_close`; raw OHLC null; CafeF only traded value | preserve KBS branch behavior; do not reuse for experiment canonical | HIGH |
| `m1_scale.py::map_scale_handoff_candidates` | KBS_BASIS_DEPENDENT | same KBS mapping at 500 scale | preserve legacy; new raw-market canonicalizer required | HIGH |
| `m1_scale.py::promote_scale_candidate` | KBS_BASIS_DEPENDENT / CANONICAL_SCHEMA_DEPENDENT | promotes KBS candidate then immediately builds features | experiment must decouple raw promotion, adjustment, and feature build | HIGH |
| `schemas/prices_daily.json` | CANONICAL_SCHEMA_DEPENDENT | one row/security/date contains optional raw OHLC and `adj_close` with one basis | keep for legacy; design distinct raw/research contracts with lineage | HIGH |
| `schemas/corporate_actions.json` | CANONICAL_SCHEMA_DEPENDENT; REUSABLE_WITH_SMALL_CHANGE | basic event dates, cash/ratio and optional `adjustment_factor` | extend terms/provenance/version/confidence; derived factor should not be source event truth | MEDIUM |
| `quality.py::clean_tables` | CANONICAL_SCHEMA_DEPENDENT; REUSABLE_WITH_SMALL_CHANGE | duplicate/FK/OHLC/band/timing checks on current schema | add raw observation uniqueness and research derivation lineage/factor checks | MEDIUM |
| `session_audit.py::build_a1_audit` | REUSABLE_WITH_SMALL_CHANGE | offline expected grid and no-imputation; current taxonomy/source aggregation limited | add provider matrix and required CafeF-primary classes | MEDIUM |
| `primary_recovery.py` | KBS_SPECIFIC_BUT_ISOLATED | KBS retry accepts only `VENDOR_ADJUSTED` evidence | retain for legacy validation; not raw recovery implementation | LOW |
| `secondary_recovery.py` | KBS_BASIS_DEPENDENT | `canonical adj_close / CafeF AdjustPrice` 20+20 diagnostics | preserve evidence; raw conflict audit must compare raw-to-raw, not ratios to KBS basis | HIGH |
| `recovery.py::recover_vendor` | SOURCE_AGNOSTIC | exact-byte recovery into a new run | reuse as-is for immutable bytes where manifest shape matches | LOW |
| `identity_recovery.py` | SOURCE_AGNOSTIC | evidence-hashed identity intervals and human review | reuse as-is; connect raw rows by interval | LOW |
| `transition_recovery.py::build_transition_recovery` | DO_NOT_REUSE | writes KBS adjusted OHLC into both `raw_*` and `adj_close` | retain only request/provenance patterns; replace price mapping | HIGH |
| `canonical_enriched_v2.py` | KBS_BASIS_DEPENDENT / CANONICAL_SCHEMA_DEPENDENT | mutates exchange/source metadata on KBS-basis price rows in a new artifact | preserve interim evidence; new experiment merge must use raw observation refs | HIGH |
| `features/market.py::build_features` | FEATURE_ASSUMES_ADJUSTED_PRICE | chooses `raw_close` only for `unadjusted`, otherwise `adj_close`; resets on basis change | consume one explicit research-price field/artifact and policy version | HIGH |
| `features/market.py::{momentum,returns,drawdown,full_window}` | SOURCE_AGNOSTIC | strict complete windows and no fill | reuse formulas after input contract changes | LOW |
| `features/registry.py` | REUSABLE_WITH_SMALL_CHANGE | versioned metadata and no-fill rule | register required `prices_daily_research` and adjustment policy lineage | LOW |
| `features/rebuild.py` | CANONICAL_SCHEMA_DEPENDENT | reads current canonical and hard-coded comparison context | parameterize research-price artifact, collection end and attribution | MEDIUM |
| `m1_scale_quality.py` | REUSABLE_WITH_SMALL_CHANGE | coverage/readiness from current canonical/features | add raw coverage, factor coverage, unresolved adjustment and provider conflict metrics | MEDIUM |
| `product/builder.py::build_company_detail` | REQUIRES_REDESIGN | uses `raw_close or adj_close`, which silently changes semantics | expose explicit raw quote and research analytics series separately | MEDIUM |
| `backtest/returns_engine.py` | CANONICAL_SCHEMA_DEPENDENT | chooses current raw/adj field from `return_basis` | require frozen research-price policy; execution-price work remains separate | MEDIUM |
| `artifact_ids.py`, `io.py` | SOURCE_AGNOSTIC | sortable IDs, hashes, atomic deterministic writes | reuse as-is | LOW |

## 5. Hard-coded price-basis findings

| File / symbol | Current assumption | Why it matters | CafeF-primary impact | Recommended migration | Risk | Required test |
|---|---|---|---|---|---|---|
| `representative_pilot_canonical.py::map_canonical_candidates` | KBS `row["close"]` is canonical `adj_close`; basis hard-coded `vendor_adjusted` | canonical price is defined by KBS output | cannot represent provider-observed raw OHLC | new raw canonicalizer; keep function legacy-only | HIGH | KBS legacy output byte/semantic regression |
| `m1_scale.py::map_scale_handoff_candidates` | same assumption at scale; CafeF contributes only `traded_value` | all 500 canonical prices inherit KBS basis | source switch alone still yields KBS-shaped data | separate provider observations and component fields | HIGH | raw CafeF row never enters `adj_close` |
| `normalization/market.py::map_record` | adjusted basis → `adj_close`; unadjusted → `raw_*` | one row/basis controls both observation and research use | cannot preserve raw plus independently derived research value | two mapping stages and two contracts | HIGH | raw normalization invariant independent of adjustment |
| `features/market.py::build_features` | non-unadjusted accepted basis always uses `adj_close` | Momentum, volatility, MDD and beta share this selector | provider adjusted values silently become research prices | accept only explicit research-price rows | HIGH | every feature row references policy/raw lineage |
| `configs/features/market.example.json` | `unadjusted`, `split_adjusted`, `vendor_adjusted` are all accepted | raw prices can feed return features across corporate actions | discontinuities can distort momentum/risk | CafeF experiment config requires DELTA research basis only | HIGH | unadjusted discontinuity blocks research feature |
| `secondary_recovery.py::build_request_plan/_validate_target` | primary series is `adj_close`; CafeF compatibility measured by ratio | KBS is governing canonical definition | inappropriate acceptance test for raw-first architecture | compare raw fields separately; adjusted series remain diagnostics | HIGH | provider-basis conflict retained, never transformed |
| `additional_market_source_discovery.py::build_stage_a5_r4` | candidate close compared with canonical `adj_close` | discovery ranking is KBS-relative | cannot select raw truth | keep only legacy comparator report | MEDIUM | raw-source evaluation does not require KBS ratio |
| `transition_recovery.py::build_transition_recovery` | KBS mapped values populate both raw OHLC and `adj_close` | fabricates a raw/adjusted equivalence | contaminates raw layer | do not reuse mapping; remap from evidenced semantics | HIGH | vendor-adjusted row cannot populate raw fields |
| `product/builder.py::build_company_detail` | `raw_close or adj_close` fallback | dashboard may change basis row by row | misleading quote/history | explicit `market_raw_quote` and `research_price` fields | HIGH | no fallback across layers |
| `backtest/returns_engine.py` | `return_basis` maps directly to raw/adj current columns | backtest shares conflated table | research policy lineage is lost | consume frozen research-price artifact | HIGH | wrong/mixed policy blocks run |
| `schemas/prices_daily.json` | `adj_close` is the sole adjusted research-capable field | no factor/event/policy lineage | DELTA adjustment is unauditable | new research-price schema | HIGH | schema requires raw ref + policy + event inputs |

### Feature-specific impact

- `Momentum21/63/126/252`: formulas are reusable, but input must be 22/64/127/253
  consecutive real **research-price** observations under one policy version.
- `Volatility63/126` and downside volatility: return calculation is reusable; any
  missing/unresolved factor keeps the affected return/window null.
- `Max Drawdown126`: must use the same research-price policy across the whole window.
- `Beta126`: both stock research prices and benchmark basis must be explicit and
  compatible; KBS VNINDEX must not silently inherit a new equity policy.
- Liquidity can remain raw-market based if its matched/total value definition is
  separately versioned; it must not borrow adjusted price semantics.

## 6. Canonical and corporate-action schema gaps

Current `prices_daily` supports nullable raw OHLC and `adj_close`, but lacks:

- provider observation ID and observation version;
- separate matched/negotiated volume/value components;
- raw artifact/row references in-table or required lineage relation;
- adjustment factor/policy/event references;
- derivation status and unresolved reason;
- ability to retain multiple conflicting provider observations for one security/date.

Current `corporate_actions` has useful event/date/cash/ratio foundations, but
`adjustment_factor` is attached to source-of-truth event rows and can blur evidence
with derivation. It lacks ratio numerator/denominator, subscription price, provider
event ID, source-document hash, confidence/review state and normalized-policy version.
The experiment should store event evidence first and generate factors in a separate
versioned derivation artifact.

## 7. Proposed new components

Names remain provisional:

| Component | Responsibility | Complexity |
|---|---|---|
| `ingestion/cafef_primary.py` | orchestrate approved CafeF raw acquisition only | MEDIUM |
| `ingestion/raw_market_canonical.py` | normalize immutable provider observations without adjustment | HIGH |
| `ingestion/corporate_actions.py` | normalize/version event evidence and conflicts | HIGH |
| `features/price_adjustment.py` | deterministic DELTA factor derivation and research-price output | HIGH |
| raw-market schema | multi-provider observation key, components and provenance | HIGH |
| research-price schema | raw ref, factor/policy/event lineage | HIGH |
| `configs/cafef_primary_experiment.yaml` | frozen experiment-only contracts; never production defaults | MEDIUM |

No component above is implemented in C0.

## 8. Migration / reuse matrix

`YES` trong cột deprecated nghĩa là component chỉ bị loại khỏi **new experiment
path**; file/logic KBS legacy vẫn được giữ nguyên để so sánh.

| Area | Current component | Reuse as-is | Reuse with change | New component | Deprecated only on experiment branch | Rationale | Complexity |
|---|---|---:|---:|---|---:|---|---|
| Source adapters | `sources/cafef.py`, `sources/vnstock.py` | NO | YES | CafeF raw mapper; KBS validator role | NO | transport is useful, semantics need separation | MEDIUM |
| Raw artifact handling | `PilotRawStore`, m1 shard raw dirs, `io.py` | `io.py` | YES | generic CafeF run store | NO | immutable hashes/resume are sound | MEDIUM |
| Provenance | manifests + lineage JSONL | NO | YES | observation/event/research refs | NO | extend, do not replace provenance | MEDIUM |
| Artifact IDs | `artifact_ids.py` | YES | NO | — | NO | deterministic sortable ID convention | LOW |
| Resume logic | representative pilot / m1 scale identity checks | NO | YES | CafeF frozen-plan identity | NO | currently coupled to KBS jobs/config | MEDIUM |
| Missing-session audit | `session_audit.py` | NO | YES | provider presence matrix/taxonomy | NO | expected-grid logic is sound | MEDIUM |
| Identity history | `identity_recovery.py` | YES | NO | raw-row interval link | NO | evidence/review rules already fail closed | LOW |
| Calendar logic | observed union + calendar quality rules | NO | YES | official/provisional source state | NO | absence cannot imply market closure | MEDIUM |
| Canonicalization | pilot/scale candidate mappers | NO | NO | raw-market canonicalizer | YES | legacy mappers remain for KBS comparison | HIGH |
| Recovery reconciliation | primary/secondary recovery | NO | YES, algorithms only | raw-row conflict audit | YES, current acceptance path | current acceptance is KBS-basis dependent | HIGH |
| Corporate actions | schema + CafeF evidence | NO | YES | event evidence store + factor derivation | NO | evidence and factor must separate | HIGH |
| Feature computation | formulas in `features/market.py` | formulas only | YES | research-price input adapter | YES, current selector | formulas good; selector unsafe | HIGH |
| EDA | `m1_scale_quality.py` reports | NO | YES | raw/factor/conflict metrics | NO | current report lacks adjustment coverage | MEDIUM |
| Dashboard artifacts | `product/builder.py` | NO | YES | separate raw quote/research series | YES, fallback selector | current fallback mixes basis | MEDIUM |
| Tests | ingestion/feature regression suites | legacy tests | YES | layer/lineage/adjustment tests | NO | preserve all legacy assertions | HIGH |
| Config | current M1/feature configs | legacy only | NO | experiment-only config/version | YES for experiment execution | isolate methodology | MEDIUM |
| Documentation | current KBS source/master docs | YES | NO | two C0 docs; later ADR only if convention exists | NO | historical truth remains intact | LOW |

## 9. Migration risks

| Risk | Consequence | Control | Complexity |
|---|---|---|---|
| CafeF OHLC is not proven unadjusted | false raw canonical | C1 contract gate around documented corporate-action windows | HIGH |
| Incomplete corporate-action coverage | wrong factor chain | unresolved factors block research prices/windows | HIGH |
| Event timing/look-ahead | future information leakage | retain announcement/publication/availability separately; derive by approved timing rule | HIGH |
| Conflicting event documents | nondeterministic adjustment | immutable candidates + explicit review/version | HIGH |
| Identity/ticker transfer errors | cross-entity splicing | reuse evidence-backed interval contract | HIGH |
| Calendar/status ambiguity | false missing classifications | official evidence hierarchy; absence remains unresolved | MEDIUM |
| Matched vs negotiated semantics | inconsistent liquidity/value | store components; policy-defined aggregates only | MEDIUM |
| Raw/research fallback in consumers | silent basis mixing | separate schemas and fail-closed APIs | HIGH |
| Benchmark basis mismatch | invalid beta/backtest | explicit benchmark research policy | HIGH |
| Rights/access unresolved | experiment not legally/operationally scalable | manual access/right gate before crawl | HIGH |
| Legacy artifacts accidentally rewritten | loss of auditability | new run IDs, path containment, hash regression tests | HIGH |

## 10. Required future tests

Minimum methodology tests:

1. raw OHLC remains provider-observed and unadjusted;
2. no source basis is mixed silently;
3. corporate-action factor is deterministic for identical inputs/policy;
4. factor/policy version is preserved in every research-price row;
5. no-event factor is neutral under the approved policy;
6. event applies at the approved ex/effective-date boundary;
7. announcement/publication timing does not create look-ahead where relevant;
8. derived research price references an immutable raw observation;
9. raw artifact bytes/hash are immutable;
10. provider and acquisition-client provenance survive every layer;
11. missing remains missing through adjustment and features;
12. identity interval and listing/delisting boundaries are enforced;
13. duplicate provider rows resolve or conflict deterministically;
14. cross-provider conflict is preserved, never averaged;
15. `Momentum252` requires 253 consecutive real research-price observations under one
    policy version;
16. volatility, MDD and beta fail closed on unresolved factor/basis gaps;
17. benchmark policy compatibility is required for beta;
18. dashboard never falls back between raw and research layers;
19. legacy KBS artifacts and outputs remain unchanged;
20. CafeF `AdjustPrice` never becomes DELTA research price without explicit derivation.

## 11. Recommended implementation order

1. **C1-PREP after explicit approval:** freeze contracts and produce reviewed
   five-worker plan only; zero requests.
2. Define raw observation schema, provider identity/key and immutable artifact manifest.
3. Run approved representative CafeF raw acquisition (C1) and validate OHLC raw status.
4. Extend corporate-action evidence schema and collect a reviewed representative event
   set (C2).
5. Implement adjustment-policy prototype with golden economic examples and factor
   lineage; do not modify raw data.
6. Build comparative KBS/CafeF diagnostics (C3).
7. Only after gates pass, plan/execute current-500 acquisition (C4).
8. Produce research prices, rebuild features and comparative EDA in new artifacts (C5).
9. Run C6 decision framework; do not merge architecture automatically.

## 12. C0 self-review

- Branch verified as `m1-cafef-primary-experiment`: YES.
- Fork/base commit exactly `e886f68875fb5c079e57c9b51cae9e6bf5a8047b`: YES.
- Source branch modified: NO.
- Data crawl or market-data request for experiment: NO / 0.
- Canonical/artifact mutation: NO / 0.
- Feature rebuild: NO.
- Adjustment engine implemented: NO.
- Five-worker assignment/ticker list created: NO.
- KBS track and A5 conclusions preserved: YES.
- CafeF `AdjustPrice` treated as DELTA canonical: NO.
- Raw and research prices separated: YES.
- Manual gates explicit: YES.
- Next allowed action: `USER MANUAL REVIEW OF C0`.

`USER_MANUAL_REVIEW_REQUIRED = YES`
