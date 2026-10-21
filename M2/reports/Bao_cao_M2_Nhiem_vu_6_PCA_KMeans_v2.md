# Báo cáo Nhiệm vụ 6 — PCA + K-Means V2

Run `m2-task6-pca-kmeans-v2`; dữ liệu `artifacts/cafef_primary/cafef-c8-complete-only-v2`. Huấn luyện mới trên 60/60 development snapshots
2019-01-31 đến 2023-12-29; 29,907 assignments;
universe 116–955 mã.

Global K=2 đã phê duyệt; seed=42, n_init=10, max_iter=300.
Robust Scaling per snapshot; không impute/clipping. Số chiều cố định 2 là max của
số chiều tối thiểu đạt 90% từng tháng. Phương sai giữ lại min/median/max:
91.9481%/99.2331%/99.9731%.
Evidence ghi trước huấn luyện: `M2/artifacts/m2-task6-pca-freeze-v2/freeze.json`.

Quality trong không gian PCA, chỉ K=2: median Silhouette=0.939741,
Davies–Bouldin=0.383600, Calinski–Harabasz=1177.053847,
inertia=81023.955397, balance=0.023814.
Balance thấp nhất=0.006452; cụm nhỏ nhất=1 mã.
Đây là thống kê mô tả, không dùng chọn lại K sau PCA.

Đã kiểm chứng scaler, PCA, labels gần centroid nhất, inertia, cluster sizes, mean 8 feature gốc,
model mirror; xuất 120 profiles (13 cột), scores/loadings/variance, centroids PCA,
scaler parameters, input features/eligible universe, config và run metadata.
Quyết định K được kiểm chứng bằng hash master config, hash bảng metrics, universe từng tháng;
không suy thêm source hash vắng mặt trong quyết định đã có. Manifest ghi hashes dữ liệu hiện tại.

Kết quả mô tả development market-only, không phải dynamic clustering hoặc bằng chứng sinh lợi.
Chưa mở holdout. Nhiệm vụ 7–10 cần cấu hình đọc bộ artifact v2 này.
