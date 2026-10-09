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

Financial CafeF-first trial50: `scripts/crawl_cafef_financial.py` và `.ps1` cung cấp
doctor/plan/run/verify/feedback/prepare50; module
`src/delta_t1/experiments/cafef_financial_trial.py` và durable journal
`src/delta_t1/ingestion/financial_compact_trial.py`. Config pilot4/trial50 dưới
`configs/data/`; report ở `artifacts/reports/cafef-financial-trial50-v1/`.
`data/financial/cafef_pilot4*_20261008_v1` và `cafef_trial50_20261008_v1` giữ sealed
raw/candidate lineage; epoch registry và dependencies quyết định retention closure.
Đọc [runbook active](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md) trước dùng runner cũ.
`configs/data/cafef_financial_trial50_handoff_v1.json` ghi bounded execution complete,
candidate data PARTIAL và next document/template review; không rewrite plan v9 hoặc
source-selection snapshot cũ, không tự bắt đầu stage100/financial clustering.

Financial source review: `scripts/benchmark_financial_sources.py` chạy so sánh bounded
CafeF/KBS; `scripts/analyze_financial_source_benchmark.py` phân tích sealed raw offline.
Config `financial_source_benchmark_v1.json` giữ mẫu/targets/budgets, còn
`financial_source_selection_v1.json` ghi recommendation engineering và closed gates.
`scripts/financial_retention.py` inventory/archive/verify/restore exact bytes;
`scripts/prune_financial_archives.ps1` chỉ gỡ direct financial leaf đã verify.
Cold data nằm tại `artifacts/archives/financial-cleanup-20261008-v1/`, index là
`prune-plan.json`; reports vẫn ở `artifacts/reports/`. Runbook trong docs/crawl/README.

| Path | Vai trò |
|---|---|
| `artifacts/cafef_primary/cafef-c8-complete-only-v1/` | Heavy C8 output local bất biến, không track đầy đủ trong Git |
| `artifacts/cafef_primary/cafef-c8-verify-v1/` | Compact C8-VERIFY evidence được track |
| `artifacts/repository/r1-consolidation-v1/` | Before/after inventory, deletion inventory và R1 verification manifest |
| `artifacts/reports/m1-market-foundation-v1/` | Compact M1 market-foundation report, report-level tables và deterministic plots |
| `scripts/run_cafef_c8_complete_only.py` | Heavy C8 runner; không dùng cho verify thông thường |
| `scripts/verify_cafef_c8_results.py` | One-time compact C8 verification artifact generator; không rerun khi output tồn tại |
| `scripts/verify_repository_r1.py` | Exact-inventory verifier cho frozen R1 revision; không phải current-tree gate hậu M1/D1 |
| `scripts/build_m1_market_foundation_report.py` | Offline deterministic M1 report generator/verifier |
| `scripts/run_cafef_expansion_worker.py` | Frozen C6 acquisition runner |
| `scripts/run_cafef_supplemental_worker.py` | Deferred supplemental acquisition runner |
| `scripts/consolidate_cafef_expansion_handoffs.py` | Central offline consolidation |

## Product Layer

`src/delta_t1/product/`, `configs/product/`, `scripts/generate_demo.py`, `scripts/start_product.ps1` và `web/` tạo/serve read-only projection từ versioned research artifact. Product không quyết định research eligibility và không tự chạy clustering.

Notebook human-facing duy nhất của M1 report là
`notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb`; notebook đọc explicit report
artifact và không chứa acquisition hoặc scientific gate logic riêng.

Exact next stage là **M2-R1 — Protocol Freeze v1**; project map này không cấp quyền chạy real clustering, mở holdout, sửa market-only runner, chạy backtest hoặc supplemental crawl. Sau khi M2-R1 PASS mới chuyển sang M2-R2.

## Tài liệu canonical

`docs/README.md` là index; `docs/CURRENT_STATUS.md` là active handoff; `docs/METHODOLOGY.md` và `docs/DECISIONS.md` giữ invariant/decision; `docs/REPRODUCIBILITY.md` định nghĩa cách verify. Git history giữ tài liệu superseded, không tạo archive song song trong working tree.

Financial reference slice: `ingestion/financial_table_parser.py` đọc coordinate
OCR candidates; `features/financial_reference.py` tính EPS/EM-Z reference qua
registry riêng; `experiments/financial_reference_flow.py` kiểm chứng và orchestrate;
CLI `scripts/run_financial_reference_flow.py`, config `financial_reference_flow_v1.json`.
Các module này không tự promote financial features hoặc thay market runner.
