# Project Map

## Research Core

| Khu vực | Nội dung active |
|---|---|
| `src/delta_t1/ingestion/` | CafeF C8 normalization/audit/verification, expansion consolidation, source semantics, generic promotion/reconciliation |
| `src/delta_t1/features/` | Feature contracts và snapshot builders dùng bởi experiment path |
| `src/delta_t1/clustering/` | Interface, registry và comparator methods |
| `src/delta_t1/experiments/` | Protocol, runner, immutable artifact và reporting |
| `src/delta_t1/evaluation/` | Cluster/temporal/portfolio metrics được tách biệt |
| `configs/data/` | C8 complete-only, C6 expansion, supplemental recovery, identity review, minimal M1 universe compatibility và synthetic smoke |
| `tests/` | Unit/integration/regression tests còn hiệu lực |

## Evidence và runner

| Path | Vai trò |
|---|---|
| `artifacts/cafef_primary/cafef-c8-complete-only-v1/` | Heavy C8 output local bất biến, không track đầy đủ trong Git |
| `artifacts/cafef_primary/cafef-c8-verify-v1/` | Compact C8-VERIFY evidence được track |
| `artifacts/repository/r1-consolidation-v1/` | Before/after inventory, deletion inventory và R1 verification manifest |
| `scripts/run_cafef_c8_complete_only.py` | Heavy C8 runner; không dùng cho verify thông thường |
| `scripts/verify_cafef_c8_results.py` | Offline C8 verification |
| `scripts/verify_repository_r1.py` | Offline R1 repository/integrity verification |
| `scripts/run_cafef_expansion_worker.py` | Frozen C6 acquisition runner |
| `scripts/run_cafef_supplemental_worker.py` | Deferred supplemental acquisition runner |
| `scripts/consolidate_cafef_expansion_handoffs.py` | Central offline consolidation |

## Product Layer

`src/delta_t1/product/`, `configs/product/`, `scripts/generate_demo.py`, `scripts/start_product.ps1` và `web/` tạo/serve read-only projection từ versioned research artifact. Product không quyết định research eligibility và không tự chạy clustering.

## Tài liệu canonical

`docs/README.md` là index; `docs/CURRENT_STATUS.md` là active handoff; `docs/METHODOLOGY.md` và `docs/DECISIONS.md` giữ invariant/decision; `docs/REPRODUCIBILITY.md` định nghĩa cách verify. Git history giữ tài liệu superseded, không tạo archive song song trong working tree.
