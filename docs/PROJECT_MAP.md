# Project Map

**Integration market + financial — 23/10/2026.** Nhánh `integration/market-financial`
kế thừa financial checkpoint `819cd82` và market `340519d`. C8 V2 đã nhập từ
`DELTA_02_ACTIVE_M2_M3.zip`, giữ đúng hashes và path. Market có 84 snapshots
2019–2025, K=2/robust; financial có 1.172 mã × annual 2016–2025, K=3/zscore.
Đây là hai baseline độc lập. Cả hai cần review chất lượng cụm; strict PIT/research/M3
chưa được nghiệm thu. Giao ticker tại cuối 2025 là 1.148 mã, chưa phải historical PIT join.

Chạy `scripts/verify_market_financial_integration.py --publish` để kiểm current
60+24 artifacts và tạo manifest tham chiếu có version; script này không fit.
`verify_m2_task12.py` và `generate_m2_task13_handoff.py` là historical V1,
không dùng chúng để tái tạo current84. Xem `M2/artifacts/market-financial-integration-v1/`.

## Ghi chú và lineage từ các giai đoạn trước

**Execution56:** [kết quả financial baseline](../artifacts/reports/financial-full10-baseline-v1/report.md)
ở `data/financial/financial_full10_baseline_v1/results/4d521e71139a48340d3d`.
1.172 mã/10 năm, sáu core ratios, independent annual static K-Means. Kiểm tra thực thi PASS;
review chất lượng cụm còn mở, PIT/M3 chưa đạt. Các section chưa chạy bên dưới là lịch sử.

**Execution55 — lịch sử đã gom:** data221→59roots, reports57→13. [Archive vàrestore](../artifacts/archives/financial-history-20261023/README.md). Giữ dependency/control của dataset1.172mã; M2chỉ đọc handoff hiệnhành. Phân cụm chưa chạy.

**Cleanup54 — cache cũ đã lưu lạnh:** 102,504candidatefiles từbốn batch được chuyểnZIPđãverify, raw/receipts/journals giữtrực tiếp. [Guide restore](../artifacts/archives/financial-cache-20261023/README.md). Chỉdùng [handoff mới nhất](../data/handoffs/financial-reference-2016-2025/README.md) choM2; dataset1.172full10khôngđổi, chưa phâncụm. Fullhistoricalreplay cóthểcầnrestorecache.

**Bắt đầu với bộ financial hiện hành:** [Dataset1.172mã/2016–2025](../data/handoffs/financial-reference-2016-2025/README.md) · [Report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md) · [Lệnh đang dùng](../scripts/README.md).

**Cleanup53 đã hoàn tất, phân cụm chưa chạy:** 2,889file đãgỡ khỏiworkingtree; report/helpers lịch sử giữZIP cóhash vàrestore, cachetái tạo đượcxóa. Không đổi raw/canonical, counter, dataset13.529rows/1.172full10 hoặc model. Chi tiếttạiExecution53 trongreporttổng. Các sectioncũ dướiđây làlineage, khôngđại diệnworker đangchạy.

**Báo cáo tổng financial:** [Mở lịch sử và tiến độ hiện tại](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md). Cập nhật liên tục qua các giai đoạn; đọc trước các report theo run.

**Ưu tiên hiện tại — Execution50 (23/10/2026): 1.172 mã đủ annual 2016–2025 / 13.529 core-ratio reference rows.** Đã thử hết 2.444 Regular gap cases qua49+50; tăng170full10 và961rows, giữ12.568baseline rows. Còn761held kỳ/257Regular candidates và93candidates ngoài Regular schema;95mã thiếu1kỳ. [Report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [report50/runbook](../artifacts/reports/financial-dstock-remaining-v1/report.md), [1.172mã](../artifacts/reports/financial-dstock-remaining-v1/full10-candidates.csv), [cohort/features](../artifacts/reports/financial-dstock-remaining-v1/delivery-result-ref.json), [field review](../artifacts/reports/financial-dstock-remaining-v1/field-review.csv). 47targeted tests/independent verification PASS;0PDF/0OCR. Worker đã dừng. EPS/P/E/P/B/F/M/Z toàn lịch sử và PIT/M3 vẫn PARTIAL. Xem `scripts/financial_dstock_remaining.ps1 -Mode Status`; dashboard acquisition cũ không phải counter DStock.


## Planning market/financial history — 19/10/2026

- [Market plan](crawl/MARKET_HISTORY10Y_1500_PLAN.md): 2016–2025, warm-up2013–2015,
  ≥1.500 cổ phiếu lịch sử; source/identity/cache/QA/M3 handoff.
- [Financial plan](crawl/FINANCIAL_HISTORY_PIT_PLAN.md): annual+quarterly2013–2025,
  closing2012 theo dependency, selective PDF/OCR và reference/PIT deliveries.
- [Registry team](../configs/data/securities_collection_registry_v1.csv): 1.522 discovery
  candidates, legacy statuses/evidence và next actions, owner/batch riêng mỗi domain.

Market vẫn PLANNED. Financial đã có [history successor](../scripts/financial_history_pit.ps1)
và [config fixedpilot5](../configs/data/financial_history_pit_v1.json), F0/F1PASS,
F2 acquisition đã kết thúc: 71.073 candidate cells, 57 missing coverage slots.
Có [QA runner riêng](../scripts/financial_history_qa.ps1) và
[sealed QA report — archive](../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/1692b3eb579b426c1e2f/report.md):
structural-heading classification, code/label diagnostics, arithmetic, annual–Q4,
reviewed-PDF conflicts và selective document queue. Xem mục9 financial plan.
[Selective documents/OCR/reference process](../scripts/financial_history_process.ps1) đã chạy:
270new reviewed facts trong bundle5controls,130OCRpages/0errors toàn campaign,12annual+6period EPS references và FPTQ2 publication
overlay theo policy cũ. F2 engineering PASS;15profiles/180template probes đã acquired cho mẫu20, [collector lịch sử15mã bổ sung](../scripts/financial_history_batch.ps1) đã terminal; finalQA341missing slots, ACVreferencecohorts được tính riêng; còn historical/PIT delivery; giữ baseline pilot29/30 và frozen M2/C8 contracts.

Audit F3 mới4/6documents,35/36fieldmatch;1khác biệt dấu giá vốn DBC được giữ để chuẩn hóa có bằng chứng. [Checkpoint catalogue/audit](crawl/FINANCIAL_HISTORY_PIT_PLAN.md#21-execution-tiếp--gas-pdf-reference-và-shs-critical-quarantine-20102026).

GAS PDFreference32facts/2annualZ″EM; criticalreviewGAS/SHS giữ9rawdifferences và1unresolvedorphan, không acceptAPI hoặc mởPIT.

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

## Financial flow hiện tại

Closing-debt successor: `scripts/financial_pilot_completion.ps1`,
`configs/data/financial_pilot5_completion_v1.json`,
`data/financial/pilot5_completion_v1`; offline reviewed closing-stock pair →
QA → recompute → immutable result/verify. Hiện29/30, VNM F chưa đủ input.

Runner: `scripts/financial_cafef_pilot.ps1` / `.py`;
config: `configs/data/financial_cafef_pilot5_execution_v1.json`;
run: `data/financial/cafef_pilot5_execution_v1`;
report: `artifacts/reports/financial-cafef-pilot5-execution-v1/report-v2.md`.
Shared modules/tests và dependency evidence giữ nguyên. Các entry scripts
legacy không được code/tests/config gọi đã chuyển vào
`artifacts/archives/project-cleanup-20261019-v1/inactive-files.zip`.
Prune đã hoàn tất; thêm 8 report folders superseded được lưu vào `superseded-reports.zip`
trong cùng archive directory. Sections financial cũ bên dưới chỉ mô tả lineage; cần restore để chạy lại.

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

Trong critical path M2, next stage là **M2-R1 — Protocol Freeze v1**; project map này không cấp quyền chạy real clustering, mở holdout, sửa market-only runner hoặc chạy backtest. Sau khi M2-R1 PASS mới chuyển sang M2-R2. Workstream mở rộng dữ liệu mới đi theo M0/F0 của hai plan ở đầu tài liệu; registry chưa thay acquisition/source gates.

Task 11 đã được owner yêu cầu và thực thi sau Task 10 freeze. Exact next stage là
M2 Nhiệm vụ 12; project map này không cấp quyền chạy Task 12, backtest hoặc supplemental crawl.

## Tài liệu canonical

`docs/README.md` là index; `docs/CURRENT_STATUS.md` là active handoff; `docs/METHODOLOGY.md` và `docs/DECISIONS.md` giữ invariant/decision; `docs/REPRODUCIBILITY.md` định nghĩa cách verify. Git history giữ tài liệu superseded, không tạo archive song song trong working tree.

Financial reference slice: `ingestion/financial_table_parser.py` đọc coordinate
OCR candidates; `features/financial_reference.py` tính EPS/EM-Z reference qua
registry riêng; `experiments/financial_reference_flow.py` kiểm chứng và orchestrate;
CLI `scripts/run_financial_reference_flow.py`, config `financial_reference_flow_v1.json`.
Các module này không tự promote financial features hoặc thay market runner.
