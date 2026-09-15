# Delta Intelligence execution plan

Updated 14/09/2026 after reading the 1,266-line instruction, the complete purpose list in `CacBaiBaoLienQuan.txt`, auditing the repository, and reviewing the reference company-detail experience.

Two tracks run together: **Product** delivers usable company intelligence; **Research** protects thesis validity. Product delivery need not wait for every paper, but no unvalidated pilot/model may be presented as a final research result.

## Gate 0 — completed foundation

- [x] Repository audit: `MAJOR REALIGNMENT REQUIRED`.
- [x] Full instruction TXT and all 22 stated paper purposes read.
- [x] Three-year observed-history policy for real clustering inputs.
- [x] Financial PIT foundation contracts.
- [x] Sharpe/ROI separated from clustering input and cluster-quality selection.
- [x] Regenerable/incomplete data removed; complete real evidence preserved.
- [x] Product-first architecture, company payload, API edge and web shell.

## P1 — product vertical slice

| ID | Task | Acceptance |
|---|---|---|
| P01 | Immutable product bundle | complete experiment required; hashes and lineage recorded |
| P02 | Catalog/detail API | health/catalog/detail, ticker validation, explicit 404 |
| P03 | Responsive ticker page | price, metrics, peers, cluster history, warnings/missing states |
| P04 | Product contract tests | no fabricated domains/path traversal/incomplete-run checks |
| P05 | Representative data upgrade | 20–50 securities, >=5 years, segment counts visible |

## P2 — source and canonical completeness

| ID | Task | Dependency | Acceptance |
|---|---|---|---|
| S01 | Verify CafeF access/terms/endpoints/semantics | data-rights decision | fields, units, basis, limits, rights evidence |
| S02 | Map VietFin/Vnstock to providers | — | provider/version/endpoint/terms per table |
| S03 | Smoke 3–5 tickers, actions, quarterly reports | S01,S02 | raw hashes, mismatches, publication dates |
| C01 | Historical security master | S03 | delisted/current/ticker reuse/effective intervals |
| C02 | Complete market contract | S03 | raw/adjusted OHLC, bands, volume/value semantics |
| C03 | Financial mapping + PIT builder | S03 | IS/BS/CF, annual/quarter/YTD/TTM, scope/revisions |
| C04 | Field-level reconciliation | C01–C03 | candidate/conflict/decision retained |

No 1,200-security crawl before this gate passes.

## R1 — literature completion and method lock

The purpose list is fully read, but full-text review status stays explicit. Complete all groups with page/section, dataset, formulas, findings and project decision:

- Momentum/Vietnam: Jegadeesh–Titman; Võ–Trương; Phan–Zhou; Lê–Bertrand; Butt et al.
- Clustering/portfolio: Han; Nanda; Ebrahimi; Ban et al.
- Algorithms/metrics: MacQueen; Ward; Ester; Rousseeuw; Davies–Bouldin; Hubert–Arabie.
- Reduction/visualization: Pearson; McInnes et al.
- Portfolio/backtest: Markowitz; Sharpe; Lo; Bailey et al.; López de Prado.
- Replication arm: Aslam, separate from Delta baseline.

Acceptance: one method-synthesis packet and approved meaning of “Dynamic Clustering”. Monthly K-Means plus label tracking must not be renamed dynamic clustering.

## R2 — feature/model experiment

1. Lock paper-backed market and PIT financial feature registry.
2. Compare snapshot scaling with no-PCA vs PCA; publish loadings/explained variance.
3. Freeze K-Means baseline; Ward/DBSCAN only if synthesis retains them.
4. Implement an approved temporal objective, not a renamed rerun loop.
5. Separate Silhouette/DBI/CH, ARI/transitions and portfolio metrics.
6. Lock development/validation/holdout and purging/embargo before backtest.
7. Decide percentage vs top-N universe, ties and ranking stage.

## P3 — product expansion

- Annual/quarterly financial trends and PIT report viewer.
- Verified quality/distress scores with applicability warnings.
- Correlation heatmap and relative-value peer chart.
- Licensed news/events and evaluated Vietnamese sentiment.
- Cluster explanations, transition alerts, field-level trust panel.
- Authentication, watchlists and alerts after privacy/security design.

## Scale/release gate

- Representative pilot before 1,200+ incremental crawl.
- Parquet/DuckDB analytics; production database/object-store serving.
- One-time final holdout; clean-machine reproduction/checksums.
- CI/MR, security review, monitoring, freshness SLA and rollback.
- Reports trace claims to paper/page/config/run.

## Cleanup policy

Delete temporary extraction, incomplete runs, regenerated synthetic outputs and superseded configs/docs with no live dependency. Preserve complete raw/vendor/canonical evidence and final experiment artifacts. Move reproducibility material only after imports/tests/links migrate; never delete evidence merely because its result is unfavorable.
