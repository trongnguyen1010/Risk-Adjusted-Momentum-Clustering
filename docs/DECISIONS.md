# Active decisions

Updated 14/09/2026. Historical discussion was consolidated to remove obsolete phase/audit documents. `CHANGELOG.md` retains chronology; this file contains decisions that still constrain implementation.

| ID | Decision |
|---|---|
| ADR-001 | Delta Intelligence is a company/ticker intelligence product; clustering is one analytical capability. |
| ADR-002 | UI/API read immutable product projections and never recompute research logic or scan raw tables. |
| ADR-003 | Preserve immutable raw/canonical/model artifacts and field/run provenance. Missing data remains null/unavailable. |
| ADR-004 | Current model is monthly snapshot K-Means with temporal tracking, not an approved Dynamic Clustering algorithm. |
| ADR-005 | Aslam (2025) is a separate replication arm; current features/model are not that replication. |
| ADR-006 | Real clustering requires three years of observed usable history; short history is `REFERENCE_ONLY`. |
| ADR-007 | Sharpe/ROI are forbidden as clustering inputs/quality/selection metrics; Sharpe remains valid for portfolio evaluation. |
| ADR-008 | CafeF is primary candidate; VietFin/Vnstock are connectors. Store underlying provider/version/terms, not connector name alone. |
| ADR-009 | Financial data is point-in-time and revision-aware; no ratios enter models before period/scope/taxonomy rules are approved. |
| ADR-010 | Raw, vendor-adjusted and total-return price semantics stay separate. No synthetic raw price or double-counted dividend. |
| ADR-011 | KBS 10-symbol pilot is legacy engineering evidence, never thesis/product-production evidence. |
| ADR-012 | Scale only after source smoke, reconciliation and representative 20–50 security pilot pass. |
| ADR-013 | Backtest universe supports all/percentage/top-N, but final 20% semantics and ranking stage remain open. |
| ADR-014 | JSONL is for pilots; accepted large-scale design is Parquet/DuckDB plus production database/object storage. |
| ADR-015 | Do not rename rolling K-Means, tune on final holdout, fabricate publication times or silently remove failed securities. |

## Open decisions

| ID | Owner decision needed |
|---|---|
| OPEN-01 | Final product/research title and research questions |
| OPEN-02 | Paper-backed definition/objective of Dynamic Clustering |
| OPEN-03 | Data rights, primary-provider priority and source-specific semantics |
| OPEN-04 | Historical 1.200+ universe and delisted/security-master authority |
| OPEN-05 | Financial feature families, taxonomy and sector treatment |
| OPEN-06 | Percentage vs top-N policy, ranking feature and tie behavior |
| OPEN-07 | Development/validation/holdout dates and purging/embargo rule |
| OPEN-08 | Production stack, authentication, freshness SLA and deployment ownership |

New decisions use: problem → alternatives → choice/reason → evidence → owner/date → affected contract/config/tests → remaining limits.
