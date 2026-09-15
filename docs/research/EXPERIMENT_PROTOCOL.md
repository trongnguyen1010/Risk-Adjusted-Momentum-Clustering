# Experiment protocol

## Pre-registration

Config phải khai báo protocol version, development/evaluation dates, synthetic flag, algorithm, feature list/version, preprocessing/PCA, model parameters/seed, `k` rationale, portfolio rule, return semantics, risk-free rate, cash/cost assumptions và bootstrap/sensitivity nếu dùng.

Runner chỉ nhận complete checksummed data run có synthetic label phù hợp. Real experiment còn cần verified historical identity, point-in-time evidence, calendar availability và resolved benchmark/price basis.

## Leakage controls

- `available_at <= decision_at` cho mọi input.
- Scaler/PCA/model không fit future hoặc holdout row.
- Final holdout chỉ dùng một lần sau methodology freeze.
- `k`/algorithm không được chọn bằng return, Sharpe hoặc ROI.
- Portfolio metrics không được chuyển vào feature list.

## Outputs

Artifact tối thiểu gồm manifest/source snapshot, model per snapshot, assignments, profiles, cluster diagnostics, temporal metrics/transitions, portfolio targets/backtests, portfolio metrics, assumptions, skipped snapshots, events và human-readable report.

Reporting chỉ render output; không fit model. Product bundle chỉ consume complete experiment artifact.
