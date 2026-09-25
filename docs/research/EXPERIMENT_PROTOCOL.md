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

Reporting chỉ render output; không fit model. Product bundle chỉ consume complete experiment artifact.
