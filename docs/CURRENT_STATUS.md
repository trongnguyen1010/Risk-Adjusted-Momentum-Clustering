# Trạng thái hiện tại — M1 market foundation reported

## Lineage và phạm vi

Nhánh active: `m1-cafef-primary-experiment`.

Lineage trước R1: C7 `0fe5ddf724618a418331785e35c36e030cfc00ea` → C8 implementation `d60c8cba49c90b3b36c346dfea463a1e4f659ee1` → C8-VERIFY `e149198986345bb02610e53d8a330f641b89df22`. R1 chỉ hợp nhất repository; không thay methodology, dữ liệu hoặc kết quả C8.

Nguồn market active là CafeF `TradeHistoryNew`. `AdjustPrice × 1000` được dùng như `adj_close` với `adjustment_basis=vendor_adjusted`; không tuyên bố split-only hoặc total-return.

## Kết quả bất biến

C8 = `EXECUTED_AND_VERIFIED`. C8-VERIFY đã xác minh offline 19/19 output hash, upstream C5/C7/identity hashes và năm source ZIP. Không network request, supplemental acquisition, clustering hoặc backtest được thực hiện.

| Gate | Tổng | C5 baseline | C7 complete expansion |
|---|---:|---:|---:|
| Candidate | 952 | 500 | 452 |
| `feature_complete` | 922 | 490 | 432 |
| `market_feature_ready_v2` | 905 | 490 | 415 |
| `latest253_complete` | 922 | 490 | 432 |
| `latest253_incomplete` | 30 | 10 | 20 |
| `historical_identity_ready` | 0 | 0 | 0 |
| `research_ready` | 0 | 0 | 0 |

Tradability được báo riêng: 675 `ACTIVE`, 276 `OBSERVED_ZERO_VOLUME`, 1 `UNKNOWN`. 47 securities chưa market-ready. 148/600 expansion securities còn `DEFERRED_EXPANSION_ACQUISITION`.

Proposed `MARKET_ONLY_EXPERIMENTAL_UNIVERSE` có đúng 905 rows thỏa `market_feature_ready_v2=true`. Đây không phải final research universe, canonical production universe hoặc historically identity-verified universe. Zero volume là observation thật và không tự loại khỏi market readiness.

Cho M2-PREP, khái niệm cần freeze là `market_experiment_eligible(t) = market_feature_ready_v2(t)` theo từng snapshot. Con số 905 chỉ mô tả snapshot mới nhất `2026-08-28`; không được dùng như terminal-universe filter cho các tháng trước và không phải alias của legacy `eligibility` hay strict `research_ready`.

## Invariant còn hiệu lực

- Snapshot chung: `2026-08-28`; observation muộn hơn giữ làm evidence nhưng không vào feature/readiness.
- Không ffill, bfill, interpolate, missing-to-zero, synthetic OHLC/return hoặc timeline compression.
- Null activity component làm total tương ứng null; không zero-fill.
- Full-history audit và latest-253 audit độc lập.
- Non-authoritative calendar gap giữ `CALENDAR_UNCERTAIN`; không đổi thành confirmed missing.
- Historical identity và financial PIT vẫn fail-closed; không promote trong R1.
- C8 baseline tái lập C5, security-level readiness diff rỗng.

Full-history status: 934 `INCOMPLETE`, 18 `UNCERTAIN_BOUNDARY`, 0 complete. Đây chủ yếu phản ánh conservative calendar/boundary evidence, không phủ định 905 market-ready rows.

## Repository sau R1

R1 bỏ 192 file planning/history/config/runner/module/test superseded khỏi active tree. Git history là archive; không tạo archive copy. Active tree giữ:

- C8 runner, C8 verifier, C8 config, C8 implementation/tests và compact verification artifact;
- C6 expansion + supplemental contracts/runners/consolidation để xử lý 148 deferred rows khi có stage riêng;
- CafeF source semantics, generic promotion/reconciliation và Product Layer;
- C5 builder vì C8 lineage/test vẫn phụ thuộc;
- minimal KBS/Vnstock compatibility path còn được generic integration dùng;
- machine-readable R1 artifact tại `artifacts/repository/r1-consolidation-v1/`.

Hai đường dẫn C1 cũ còn xuất hiện trong frozen C8 provenance/config hash fields chỉ là Git-history identifiers; chúng không phải active input path.

## M1-REPORT

Artifact `artifacts/reports/m1-market-foundation-v1/` và notebook
`notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb` là lớp report/inspection
offline trên evidence C8 đã verify. Report tái tính và assert toàn bộ headline,
feature coverage, source/exchange composition, 30 latest-253 incomplete rows,
47 market-readiness exclusions và 80 monthly snapshots từ `2020-01-31` đến
`2026-08-28`. Notebook chỉ đọc explicit immutable report directory; business
logic và integrity checks nằm trong generator.

Readiness theo tháng có các đoạn gián đoạn lớn và zero-readiness periods. M2-PREP phải giải thích chúng trước khi freeze development/validation windows; D1 chỉ ghi nhận evidence, không diễn giải nguyên nhân và không thay methodology.

**M1 MARKET DATA FOUNDATION: COMPLETE FOR MARKET-ONLY EXPERIMENT PREPARATION.**
Strict research gate vẫn `NOT READY`; `historical_identity_ready=0` và
`research_ready=0`.

## Kiểm chứng offline

```powershell
.venv\Scripts\python.exe scripts\build_m1_market_foundation_report.py --verify-existing
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

Không rerun `run_cafef_c8_complete_only.py` hoặc C8 verifier-generator để kiểm chứng artifact đã tồn tại. R1 exact-inventory verifier thuộc frozen R1 tree và đương nhiên không đại diện cho current tree sau M1/D1. Heavy artifact và năm ZIP phải giữ nguyên hash.

## M2-PREP

Artifact `artifacts/experiments/m2-prep-v1/` đã audit eligibility, 80 snapshot, implementation, feature/preprocessing, algorithms, metrics và literature mà không chạy clustering. Kết quả cuối là **`MANUAL_REVIEW_REQUIRED`**; không tạo `configs/experiments/m2_market_only_v1.json`.

Hai discontinuity hệ thống được giải thích từ evidence hiện có:

- `2023-05` đến `2023-10`: session `2023-05-15` có trong calendar của cả ba exchange nhưng thiếu VNINDEX row; strict `beta_126` làm toàn bộ cross-section chưa complete cho tới khi gap ra khỏi 126-return window. Phân loại: benchmark/calendar propagation, không phải clustering result.
- `2025-02` đến `2026-01`: canonical market có 0 equity price row ở open session `2025-02-03`; strict `mom_252` cần 253 real prices nên toàn bộ cross-section fail cho tới khi gap ra khỏi window. Không impute hoặc timeline-compress.

Latest snapshot vẫn tái lập đúng `market_experiment_eligible=905/952`, với membership tính độc lập ở từng tháng; historical identity và research readiness vẫn bằng 0.

## M2 Nhiệm vụ 1 — protocol freeze

Owner đã phê duyệt và khóa protocol market-only v1 trong
`configs/experiments/m2_market_only_v1.json`: 15 development snapshots
`2023-11-30..2025-01-24`, 7 holdout snapshots niêm phong
`2026-02-27..2026-08-28`, minimum eligibility 120, 8 market features,
fail-closed missing, no clipping/winsorization, Robust Scaling theo từng snapshot
và `k_range=2..8`. Global K chỉ được chọn trên development bằng
cluster-quality metrics; `portfolio_evaluation.enabled=false`. PCA chỉ là
comparator độc lập, không phải preprocessing chung. Chưa fit model,
không mở holdout, không backtest và không thay data/evidence.

Acceptance gate sau khi phục hồi đúng immutable C5 local artifact: C5 manifest
SHA-256 `869512c66fceee02f9b5801af3c24724309b508013a607158085dd7e9b50d256`,
20/20 C5 output hashes khớp và full repository suite 173/173 tests pass.
Ba file recovery WIP untracked ngoài active R1 tree được giữ nguyên trong
`tmp/full_recovery_wip_20260926/`; không phục hồi recovery stack superseded.

## M2 Nhiệm vụ 2 — runner preparation/testing

Runner market-only đã có adapter xác minh checksum và đọc trực tiếp
`canonical/feature_snapshots.jsonl` của C8 mà không đi qua strict historical-identity
gate dành cho M3. Adapter chỉ tạo alias in-memory
`market_feature_ready_v2 = market_feature_ready` cho C8 v2, không mutate artifact;
legacy `eligibility` không được dùng thay thế.

Snapshot `2023-11-30` tái lập đúng 142 securities eligible. Runner kiểm tra
đúng 8 feature là numeric finite, skip khi `n_eligible < 120`, và output được
common `build_snapshot` interface chấp nhận. Terminal-universe guard dùng snapshot
membership độc lập, không retrospective-filter. Nhiệm vụ này không chạy
Global K, không mở holdout và không backtest.

## M2 Nhiệm vụ 3 — Global K selection (Completed & Approved)

Đã chạy hoàn tất 105 lượt K-Means (15 development snapshots nhân 7 cấu hình `k=2..8`).
105/105 lượt chạy hội tụ và tính đủ 5 metrics.
Cấu hình K = 2 đạt median Silhouette cao nhất (0.7557), median Davies-Bouldin thấp nhất (0.5219)
và Calinski-Harabasz cao nhất (316.39). Nhóm đã phê duyệt chính thức Global K = 2 (ADR-049),
khóa `k: 2` vào `configs/experiments/m2_market_only_v1.json`.
Hiện tượng cụm nhỏ (8-21 mã) siêu thanh khoản được ghi nhận và phân tích đầy đủ.

## Stage tiếp theo

**M2 Nhiệm vụ 4 — CHẠY PHƯƠNG ÁN A: K-MEANS BASELINE**: Đóng gói và hoàn thiện
kết quả K-Means chính thức với Global K = 2 trên 15 development snapshots, chuẩn bị cho
Nhiệm vụ 5 (Ward) và Nhiệm vụ 6 (PCA + K-Means). Không mở holdout và không backtest.

