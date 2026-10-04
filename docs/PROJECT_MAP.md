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
| `configs/experiments/m2_market_only_v1.json` | Frozen preregistration cho M2 market-only; portfolio evaluation tắt |
| `configs/experiments/m2_final_holdout_v1.json` | Task 11 paths/gates; algorithm và fit parameters lấy từ frozen winning models |
| `src/delta_t1/experiments/final_holdout.py` | Single-winner holdout execution và verify-only rerun |
| `tests/` | Unit/integration/regression tests còn hiệu lực |

## Evidence và runner

| Path | Vai trò |
|---|---|
| `artifacts/cafef_primary/cafef-c8-complete-only-v1/` | Heavy C8 output local bất biến, không track đầy đủ trong Git |
| `artifacts/cafef_primary/cafef-c8-verify-v1/` | Compact C8-VERIFY evidence được track |
| `artifacts/repository/r1-consolidation-v1/` | Before/after inventory, deletion inventory và R1 verification manifest |
| `artifacts/reports/m1-market-foundation-v1/` | Compact M1 market-foundation report, report-level tables và deterministic plots |
| `M2/artifacts/m2-final-holdout-v1/` | Task 11 complete: 7 holdout snapshots, selected K-Means only, models/metrics/gap/manifest |
| `M2/notebooks/11_final_holdout_execution.ipynb` | Notebook Task 11 bảy bước; đọc lại evidence khi rerun, không refit |
| `artifacts/financial_pit/fin-pit-2-semantic-extraction-v1/` | FIN-PIT-2 report/fact/linkage/taxonomy/revision candidates và gate `PARTIAL`; không phải canonical financial data |
| `artifacts/financial_pit/fin-pit-2-r1-ocr-remediation-v1/` | FIN-PIT-2-R1 derived OCR/page provenance, updated semantic candidates, before/after coverage và gate `PARTIAL`; raw PDF không bị thay thế |
| `scripts/run_cafef_c8_complete_only.py` | Heavy C8 runner; không dùng cho verify thông thường |
| `scripts/verify_cafef_c8_results.py` | One-time compact C8 verification artifact generator; không rerun khi output tồn tại |
| `scripts/verify_repository_r1.py` | Exact-inventory verifier cho frozen R1 revision; không phải current-tree gate hậu M1/D1 |
| `scripts/build_m1_market_foundation_report.py` | Offline deterministic M1 report generator/verifier |
| `scripts/run_fin_pit_2_semantic_extraction.py` | Dry-run, offline semantic extraction, resume-as-verify và verifier FIN-PIT-2 |
| `scripts/run_fin_pit_2_r1_ocr_remediation.py` | Preflight inventory, selective local OCR, semantic re-extraction, resume và offline verifier FIN-PIT-2-R1 |
| `src/delta_t1/ingestion/financial_pit_ocr.py` | Page-scoped OCR/provenance, quality controls, numeric fail-closed và before/after coverage cho FIN-PIT-2-R1 |
| `scripts/run_cafef_expansion_worker.py` | Frozen C6 acquisition runner |
| `scripts/run_cafef_supplemental_worker.py` | Deferred supplemental acquisition runner |
| `scripts/consolidate_cafef_expansion_handoffs.py` | Central offline consolidation |

## Product Layer

`src/delta_t1/product/`, `configs/product/`, `scripts/generate_demo.py`, `scripts/start_product.ps1` và `web/` tạo/serve read-only projection từ versioned research artifact. Product không quyết định research eligibility và không tự chạy clustering.

Notebook human-facing duy nhất của M1 report là
`notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb`; notebook đọc explicit report
artifact và không chứa acquisition hoặc scientific gate logic riêng.

Task 11 đã được owner yêu cầu và thực thi sau Task 10 freeze. Exact next stage là
M2 Nhiệm vụ 12; project map này không cấp quyền chạy Task 12, backtest hoặc supplemental crawl.

## Tài liệu canonical

`docs/README.md` là index; `docs/CURRENT_STATUS.md` là active handoff; `docs/METHODOLOGY.md` và `docs/DECISIONS.md` giữ invariant/decision; `docs/REPRODUCIBILITY.md` định nghĩa cách verify. Git history giữ tài liệu superseded, không tạo archive song song trong working tree.
