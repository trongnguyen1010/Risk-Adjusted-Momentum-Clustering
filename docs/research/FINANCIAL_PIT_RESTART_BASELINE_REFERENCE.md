# Tham chiếu baseline Financial PIT restart

Tài liệu này là reference không thay thế hoặc sửa `docs/DECISIONS.md` trên branch
`m2-clustering-experiment`. Nó không cấp approval mới và không promote stage.

## Immutable local Git source

- Restart cycle: `fin-pit-restart-20261003T083918Z-87c88ae1`.
- Baseline branch recorded: `m1-cafef-primary-experiment`.
- Baseline parent HEAD: `5723843cb773aa7eaa0afcd4267f0f10835abea4`.
- Local stash commit containing the uncommitted FIN-PIT-0 handoff:
  `06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8`.
- Plan V3 Git blob: `567d016756097401fd059d17eceaffc12f46b223`.
- Decisions Git blob: `3eee51d236e043206ceabef6d9c8ea4304d8033a`.
- Current-status Git blob: `9803b0a211d7abaff432a06d5f30341352db0179`.

Exact sources:

```text
06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8:docs/research/FINANCIAL_PIT_IMPLEMENTATION_PLAN_V3_UPDATED.md
06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8:docs/DECISIONS.md
06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8:docs/CURRENT_STATUS.md
```

Verify from workspace root without switching branch or applying the stash:

```powershell
git cat-file -e 06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8^{commit}
git rev-parse 06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8^1
git rev-parse 06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8:docs/research/FINANCIAL_PIT_IMPLEMENTATION_PLAN_V3_UPDATED.md
git show 06eb1c5ad97426c6ac6520be14bc01d1fe7fa0a8:docs/research/FINANCIAL_PIT_IMPLEMENTATION_PLAN_V3_UPDATED.md
```

## Baseline facts retained for the current cycle

- Policy: `FULL_RESTART_NO_INHERITANCE`.
- FIN-PIT-0: `PASS`, documentation-only.
- FIN-PIT-1A and later stages were `NOT_STARTED` at handoff.
- `FINANCIAL_DATA=NOT_READY`.
- `FINANCIAL_FEATURES_ALLOWED=false`.
- Every FIN-PIT-1A run requires a new run ID, same-cycle parent lineage and the full
  section 7B output/checksum/gate contract.
- Historical Financial PIT artifacts, gates, approvals and qualification are not
  inherited as execution evidence.

The restart ADR in the baseline used ID ADR-047. On the current M2 branch ADR-047 is
already used for the M2 Task 1 protocol. This reference therefore uses no ADR number and
does not modify either decision. If the histories are later reconciled, a new non-conflicting
ADR ID must be allocated under the repository's then-current sequence.
