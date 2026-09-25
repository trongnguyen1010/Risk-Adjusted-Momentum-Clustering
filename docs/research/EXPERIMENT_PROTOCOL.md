# Experiment protocol

## Pre-registration

Config phải khai báo protocol version, development/evaluation dates, synthetic flag, algorithm, feature list/version, preprocessing/PCA, model parameters/seed, `k` rationale và `portfolio_evaluation.enabled`. Portfolio rule, return semantics, risk-free rate, cash/cost và bootstrap/sensitivity chỉ bắt buộc khi portfolio evaluation được bật.

Runner chỉ nhận complete checksummed data run có synthetic label phù hợp. Hai lớp experiment không được nhập làm một:

1. **Market-only M2 development:** membership tại mỗi snapshot là `market_experiment_eligible(t) = market_feature_ready_v2(t)` sau khi M2-PREP freeze windows, preprocessing, comparator và evaluation rules. Lớp này chỉ phục vụ market-structure/clustering development; nó không xác nhận historical identity, không tạo final historical universe, không cho identity-sensitive inference, không chạy portfolio/backtest và không phải investment output. 905 chỉ là count tại `2026-08-28`, không phải terminal filter áp cho mọi snapshot.
2. **Strict research/M3:** tiếp tục yêu cầu verified historical identity, point-in-time evidence, calendar availability, resolved benchmark/price basis và protocol tương lai được freeze. Lớp này vẫn `NOT READY` sau M1.

## Leakage controls

- `available_at <= decision_at` cho mọi input.
- Scaler/PCA/model không fit future hoặc holdout row.
- Final holdout chỉ dùng một lần sau methodology freeze.
- `k`/algorithm không được chọn bằng return, Sharpe hoặc ROI.
- Portfolio metrics không được chuyển vào feature list.

## Outputs

M2 artifact tối thiểu gồm manifest/source snapshot, model per snapshot, assignments, profiles, cluster diagnostics, temporal metrics/transitions, assumptions, skipped snapshots, events và human-readable report. Khi `portfolio_evaluation.enabled=false`, targets/backtests/performance không được sinh. M3/frozen config bật rõ mới bổ sung portfolio targets/backtests/metrics.

M2-PREP chỉ định nghĩa contract và không được sinh M2 experiment artifact. Trước khi freeze development window, phải giải thích các discontinuities và zero-readiness periods trong monthly M1 report; không được chữa chúng bằng terminal-universe filtering, imputation hoặc timeline compression.

## Kết quả M2-PREP v1

`market_experiment_eligible(t) = market_feature_ready_v2(t)` tại chính snapshot `t` đã được freeze; latest snapshot tái lập 905/952. Required feature set gồm `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21`. `portfolio_evaluation.enabled=false`, Dynamic Clustering `NOT APPROVED`, DBSCAN không tương thích fixed-k flow hiện tại.

Protocol execution chưa được freeze. Các lựa chọn còn `MANUAL_REVIEW_REQUIRED` gồm:

- development window: `2023-01..2023-04`, contiguous main `2023-11..2025-01`, latest recovery `2026-02..2026-08`, hoặc full post-history range với explicit skipped months;
- final holdout boundary và one-use access rule;
- minimum eligible cross-section, consecutive-month và low-coverage thresholds;
- fixed/development-selected `k` và temporal comparability rule;
- no clipping so với fixed winsorization/robust transform, default scaler;
- PCA component count hoặc development-only variance threshold;
- registry version `1.5.0` so với C8 snapshot version `1.6.0`.

Runner hiện vẫn lọc legacy `eligibility`; loader strict-research yêu cầu verified identity và layout data-run cũ. Vì chưa có owner decisions, M2-PREP không tạo fake config và không sửa rộng strict research path. Chi tiết machine-readable nằm tại `artifacts/experiments/m2-prep-v1/`.

Reporting chỉ render output; không fit model. Product bundle chỉ consume complete experiment artifact.
