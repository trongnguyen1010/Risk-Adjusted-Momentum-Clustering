# DELTA — Continue Exactly One Stage

Work in the current repository and branch.

1. Read `AGENTS.md`.
2. Read `Execution Progress / Handoff` in
   `docs/crawl/M1_DATA_ENRICHMENT_AND_UNIVERSE_EXPANSION_MASTER_PLAN.md`.
3. Identify the exact `Next allowed stage` from that Handoff. Do not infer a stage
   from a historical sequence or begin any later stage.
4. Read only that stage's exact Master Plan section and the project context it names.
5. Execute exactly one stage, preserving all DELTA data-contract, provenance,
   no-imputation, PIT and safety rules.
6. Run the targeted tests required by that stage and the repository-wide static
   checks required by `AGENTS.md`.
7. Self-review scope, evidence, artifacts, methodology-sensitive decisions and test
   results; fix only concrete blockers.
8. Update only the Master Plan's `Execution Progress / Handoff` with the evidence-backed
   result and next allowed action.
9. STOP. Do not execute the next stage.
