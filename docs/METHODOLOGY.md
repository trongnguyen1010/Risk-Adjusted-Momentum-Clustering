# Methodology

## Phạm vi hiện tại

DELTA có ba nhánh phân biệt:

1. **Static baseline:** monthly cross-section, snapshot-only preprocessing, deterministic K-Means, label alignment và temporal tracking.
2. **Comparator experiments:** PCA + K-Means và ít nhất một trong Ward/Agglomerative, DBSCAN, GMM sau khi protocol nêu rõ giả định.
3. **Approved temporal method:** chưa triển khai; chỉ được bắt đầu sau explicit approval trong [Dynamic Clustering Review](research/DYNAMIC_CLUSTERING_REVIEW.md).

Nhánh static baseline không được gọi là Dynamic Clustering dù có ARI, transition hoặc rolling month.

## Universe và point-in-time

Historical universe được tạo từ effective-dated `security_id`, không từ current ticker membership. Input tại snapshot phải có `available_at <= decision_at`. Real clustering yêu cầu ít nhất ba calendar years usable observed history; short history là `REFERENCE_ONLY`. Observed calendar span không tự chứng minh usable density; M1 báo span, session coverage, required-feature completeness, market readiness và identity readiness riêng. Monthly research gate chỉ dùng latest completed collection month.

Ngoại lệ hẹp cho M2 market-only development không tạo historical-universe claim: tại mỗi snapshot `t`, candidate membership là `market_experiment_eligible(t) = market_feature_ready_v2(t)` sau khi M2-PREP freeze windows và preprocessing. Latest count 905 không được áp ngược làm terminal filter. Strict research/M3 vẫn yêu cầu effective-dated identity, PIT evidence và `research_ready` theo protocol tương lai được duyệt.

Không forward-fill giá, không đổi missing thành zero và không splice raw với adjusted price. Quarterly financial data dùng publication/availability và giữ restatement vintage.

## Model protocol

- Fit transform/scaler/PCA chỉ trên development data được phép của snapshot/fold.
- K-Means giữ seed, `n_init`, `max_iter`, convergence và deterministic tie behavior.
- Chọn `k` bằng pre-registration hoặc cluster-quality criteria trên development set, không bằng portfolio return.
- UMAP chủ yếu để visualization; không mặc định dùng làm model input.
- Cluster label alignment phục vụ diễn giải transition, không thay thế permutation-invariant metric.

## Feature protocol

Market feature nền gồm momentum 21/63/126/252 sessions, volatility, downside volatility, maximum drawdown, beta và liquidity. Risk-adjusted momentum là research hypothesis và phải có version. Financial feature chỉ được bật sau paper-backed definition và taxonomy/PIT approval.

Market-only M2 dùng đúng required set đã khóa trong C8 (`mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21`); không tự thêm financial feature. Snapshot preprocessing không được fit future/holdout. Static clustering theo tháng cộng ARI/transition tracking không được gọi là Dynamic Clustering.

Sharpe và ROI không phải clustering feature hay cluster-quality metric. Sharpe chỉ được tính ở portfolio evaluation.

## Boundary M2/M3

M2-PREP chỉ freeze protocol; chưa chạy clustering. Khi một M2 development stage riêng được phê duyệt, config vẫn phải có `portfolio_evaluation.enabled=false` và chỉ được sinh cluster/temporal diagnostics, không tạo backtest/performance artifact. Chỉ M3/frozen protocol bật portfolio evaluation; kết quả đó không quay lại chọn `k`, algorithm, PCA components hoặc feature set.

## Technical debt cho variable-cluster method

Common interface hiện giả định fixed `k`: bắt buộc `config["k"]`, quét `k_range`, profile IDs `0..k-1`, và temporal alignment yêu cầu cùng số cluster. DBSCAN không được triển khai bằng cách ép vào contract này. Một design được review phải hỗ trợ noise label, số cluster thay đổi theo snapshot, diagnostics phù hợp density method và temporal comparison khi cluster birth/death/noise xảy ra. Đây là preparation note, không phải approval DBSCAN hoặc Dynamic Clustering.
