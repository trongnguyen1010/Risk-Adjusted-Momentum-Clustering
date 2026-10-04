# Báo cáo Nhiệm vụ 7 — Chất lượng cụm PCA + K-Means

Nguồn: `m2-task6-pca-kmeans-v1/diagnostics.csv`, chỉ K=2, 15 snapshot development.

## A — Phán quyết kỹ thuật
Median Silhouette=0.771666 (vượt ngưỡng 0,70), DB=0.515502,
CH=361.5279, Inertia=1963.0651, Balance=0.067669.
Có 7/15 tháng Balance <0,05; cụm nhỏ 8–21 mã.
Median Balance không thay thế việc kiểm tra từng tháng.

## B — Bản chất cấu trúc quan sát
Hai nhóm có quy mô bất đối xứng. Silhouette cao chỉ chứng minh phân tách trong không gian PCA;
không chứng minh mọi cổ phiếu có hành vi giống nhau hoặc nguyên nhân là dòng tiền/đầu cơ.
Hồ sơ gốc và động lực phân tách được kiểm tra riêng ở nhiệm vụ 8.
Inertia chịu ảnh hưởng N và phân tán, không phải tiêu chí xếp hạng độc lập theo thời gian.

## C — Bàn giao và giới hạn
Bàn giao đủ hai bảng, năm biểu đồ và quality_summary schema 5×7.
Giữ cảnh báo mất cân bằng; không kết luận PCA cải thiện độ ổn định hay giá trị đầu tư.
Không chọn lại K, không fit model, không dùng holdout/portfolio metrics.

## Bảng 1
| metric | n_total | n_available | mean | median | minimum | maximum |
| --- | --- | --- | --- | --- | --- | --- |
| silhouette | 15 | 15 | 0.80441 | 0.771666 | 0.659505 | 0.951234 |
| davies_bouldin | 15 | 15 | 0.49901 | 0.515502 | 0.354967 | 0.716695 |
| calinski_harabasz | 15 | 15 | 709.194537 | 361.52794 | 176.314178 | 2065.151594 |
| inertia | 15 | 15 | 53212.333977 | 1963.065124 | 1219.015572 | 328111.440073 |
| cluster_balance | 15 | 15 | 0.056407 | 0.067669 | 0.010363 | 0.094972 |
## Bảng 2
| Snapshot | Silhouette | DB | CH | Inertia | Balance |
| --- | --- | --- | --- | --- | --- |
| 2023-11-30 | 0.775353 | 0.536114 | 225.635234 | 1219.015572 | 0.067669 |
| 2023-12-29 | 0.771666 | 0.472406 | 417.106858 | 1267.010612 | 0.089385 |
| 2024-01-31 | 0.71943 | 0.558519 | 261.530664 | 1360.147611 | 0.094972 |
| 2024-02-29 | 0.745119 | 0.482618 | 361.52794 | 1295.238398 | 0.094972 |
| 2024-03-29 | 0.676387 | 0.590633 | 190.663829 | 1257.003284 | 0.082418 |
| 2024-04-26 | 0.728588 | 0.547559 | 261.89371 | 1535.166794 | 0.07 |
| 2024-05-31 | 0.70428 | 0.573273 | 232.343692 | 1543.374428 | 0.072816 |
| 2024-06-28 | 0.763995 | 0.515502 | 274.715119 | 1963.065124 | 0.048035 |
| 2024-07-31 | 0.659505 | 0.716695 | 176.314178 | 2009.521186 | 0.073913 |
| 2024-08-30 | 0.906888 | 0.472977 | 926.687158 | 121106.779768 | 0.036585 |
| 2024-09-30 | 0.93345 | 0.354967 | 2065.151594 | 101890.301694 | 0.027119 |
| 2024-10-31 | 0.940062 | 0.36519 | 1820.107423 | 134604.423691 | 0.021849 |
| 2024-11-29 | 0.951234 | 0.392294 | 1524.924713 | 328111.440073 | 0.010363 |
| 2024-12-31 | 0.909545 | 0.388929 | 983.822099 | 52249.830012 | 0.019031 |
| 2025-01-24 | 0.880644 | 0.517479 | 915.493842 | 46772.691415 | 0.036972 |
