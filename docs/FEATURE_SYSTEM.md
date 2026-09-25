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

Các thuật ngữ readiness không được dùng thay thế nhau:

| Thuật ngữ | Ý nghĩa |
|---|---|
| `feature_complete` | Đủ toàn bộ required feature tại snapshot. |
| `market_feature_ready_v2` | Đủ feature, history và market/status/metadata rules của C8; identity provisional không tự làm false. |
| `market_experiment_eligible(t)` | Khái niệm M2-PREP: bằng `market_feature_ready_v2(t)` tại chính snapshot `t`, subject to frozen market-only protocol; chưa phải field mới trong C8 artifact. |
| `historical_identity_ready` | Identity đủ thẩm quyền cho historical research universe; provisional luôn false. |
| `research_ready` | Strict gate kết hợp market readiness và historical identity readiness. |
| `eligibility` | Legacy/scoped compatibility; không được silently reinterpret thành một gate ở trên. |

Required market-only set hiện tại gồm `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126` và `liquidity_21`. Financial features chưa active. Con số 905 chỉ là latest-snapshot count, không phải terminal membership cho mọi tháng. Historical-universe/backtest vẫn cần strict readiness và approved methodology.

Financial feature phải nêu period type (instant/duration), annual/quarter/YTD/TTM, statement scope, currency/unit, denominator, sector treatment, publication/availability và restatement rule.

## Versioning

Đổi formula, lookback, source semantics, missing policy, PIT rule hoặc transform là thay đổi feature version. Experiment artifact lưu feature names/version cùng preprocessing parameters để reproducible và để Product Layer giải thích đúng definition.

Schema `feature_snapshots_legacy_1_3_0`, `feature_snapshots_legacy_1_4_0` và `features/compatibility.py` chỉ dùng đọc/validate immutable evidence cũ. Compatibility 1.3 loại Sharpe khỏi projection mà không mutate artifact. Không được dùng legacy contract để tạo research snapshot mới.
