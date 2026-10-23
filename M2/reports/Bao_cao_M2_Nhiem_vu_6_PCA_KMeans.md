# Báo cáo Nhiệm vụ 6 — PCA + K-Means

Run `m2-task6-pca-kmeans`; dữ liệu `artifacts/cafef_primary/cafef-c8-complete-only-v2`. Huấn luyện mới trên 60/60 development snapshots
2019-01-31 đến 2023-12-29; 45,646 assignments;
universe 503–1134 mã.

Global K=2 đã phê duyệt; seed=42, n_init=10, max_iter=300.
Robust Scaling per snapshot; không impute/clipping. Số chiều cố định 2 là max của
số chiều tối thiểu đạt 90% từng tháng. Phương sai giữ lại min/median/max:
97.8203%/99.7216%/99.9631%.
Evidence ghi trước huấn luyện: `M2/artifacts/m2-task6-pca-freeze/freeze.json`.

Quality trong không gian PCA, chỉ K=2: median Silhouette=0.946855,
Davies–Bouldin=0.397056, Calinski–Harabasz=1631.466715,
inertia=372878.404927, balance=0.020684.
Balance thấp nhất=0.003252; cụm nhỏ nhất=2 mã.
Đây là thống kê mô tả, không dùng chọn lại K sau PCA.

Đã kiểm chứng scaler, PCA, labels gần centroid nhất, inertia, cluster sizes, mean 8 feature gốc,
model mirror; xuất 120 profiles (13 cột), scores/loadings/variance, centroids PCA,
scaler parameters, input features/eligible universe, config và run metadata.
Quyết định K được kiểm chứng bằng hash master config, hash bảng metrics, universe từng tháng;
không suy thêm source hash vắng mặt trong quyết định đã có. Manifest ghi hashes dữ liệu hiện tại.

Kết quả mô tả development market-only, không phải dynamic clustering hoặc bằng chứng sinh lợi.
Chưa mở holdout. Nhiệm vụ 7–10 cần cấu hình đọc bộ artifact v2 này.
