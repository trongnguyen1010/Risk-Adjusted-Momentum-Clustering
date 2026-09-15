# Experiment protocol

## Pre-registration

Config phải khai báo protocol version, development/evaluation dates, synthetic flag, algorithm, feature list/version, preprocessing/PCA, model parameters/seed, `k` rationale và `portfolio_evaluation.enabled`. Portfolio rule, return semantics, risk-free rate, cash/cost và bootstrap/sensitivity chỉ bắt buộc khi portfolio evaluation được bật.

Runner chỉ nhận complete checksummed data run có synthetic label phù hợp. Real experiment còn cần verified historical identity, point-in-time evidence, calendar availability và resolved benchmark/price basis.

## Leakage controls

- `available_at <= decision_at` cho mọi input.
- Scaler/PCA/model không fit future hoặc holdout row.
- Final holdout chỉ dùng một lần sau methodology freeze.
- `k`/algorithm không được chọn bằng return, Sharpe hoặc ROI.
- Portfolio metrics không được chuyển vào feature list.

## Outputs

M2 artifact tối thiểu gồm manifest/source snapshot, model per snapshot, assignments, profiles, cluster diagnostics, temporal metrics/transitions, assumptions, skipped snapshots, events và human-readable report. Khi `portfolio_evaluation.enabled=false`, targets/backtests/performance không được sinh. M3/frozen config bật rõ mới bổ sung portfolio targets/backtests/metrics.

Reporting chỉ render output; không fit model. Product bundle chỉ consume complete experiment artifact.
