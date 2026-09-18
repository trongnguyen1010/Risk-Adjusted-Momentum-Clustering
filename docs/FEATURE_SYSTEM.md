# Hệ thống feature

## Registry là source of truth

Mỗi feature phải có metadata: `name`, `family`, `version`, `formula/description`, `required_source`, `lookback`, `point_in_time_rule`, `missing_policy`, `transform`, `cluster_eligible` và `reference/citation`.

Validation dùng registry metadata, không suy đoán từ prefix tên cột. Feature chưa có citation/definition được phép tồn tại ở trạng thái research candidate nhưng không được tự động `cluster_eligible`.

Active registry/snapshot 1.5 không chứa Sharpe. Formula market giữ nguyên baseline 1.4; version tăng vì readiness contract được tách rõ. ROI vẫn là tên bị cấm rõ ràng. Sharpe, ROI và mọi portfolio outcome không được đi vào `required_features`, scaler, PCA, clustering, cluster profile ranking hoặc `k` selection.

## Module boundaries

- `features/market.py`: momentum 1M/3M/6M/12M, volatility, downside risk, drawdown, beta, liquidity và công thức market đã duyệt; không tính Sharpe.
- `features/fundamentals.py`: financial feature definitions đã được paper/taxonomy approval; chưa tự tạo ratio từ fact không tương thích.
- `features/point_in_time.py`: chọn report vintage có `available_at <= decision_at` và xử lý restatement.
- `features/preprocessing.py`: transform/winsorize/scale/PCA theo development snapshot, không fit future/holdout.
- `features/registry.py`: đăng ký, resolve và validate eligibility.

## Missing và time rules

Missing session giữ `None`; cửa sổ không được nén hay forward-fill. Basis change reset history. Với real run, security cần ba calendar years usable observed history để vào clustering; mã còn lại là `REFERENCE_ONLY` nếu không có lỗi loại trừ khác.

`feature_complete` và `market_feature_ready` không bị làm false chỉ vì identity `provisional`. `historical_identity_ready` và strict `research_ready` vẫn false cho identity này. `eligibility` cũ được giữ như scoped compatibility; historical-universe/backtest phải dùng strict readiness và approved methodology.

Financial feature phải nêu period type (instant/duration), annual/quarter/YTD/TTM, statement scope, currency/unit, denominator, sector treatment, publication/availability và restatement rule.

## Versioning

Đổi formula, lookback, source semantics, missing policy, PIT rule hoặc transform là thay đổi feature version. Experiment artifact lưu feature names/version cùng preprocessing parameters để reproducible và để Product Layer giải thích đúng definition.

Schema `feature_snapshots_legacy_1_3_0`, `feature_snapshots_legacy_1_4_0` và `features/compatibility.py` chỉ dùng đọc/validate immutable evidence cũ. Compatibility 1.3 loại Sharpe khỏi projection mà không mutate artifact. Không được dùng legacy contract để tạo research snapshot mới.
