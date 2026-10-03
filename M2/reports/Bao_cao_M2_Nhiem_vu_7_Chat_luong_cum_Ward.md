# Báo cáo M2 — Nhiệm vụ 7: Chất lượng cụm Ward

## Phạm vi và nguồn bằng chứng

- Ward Hierarchical, Global K=2 đã khóa ở Nhiệm vụ 3; 15 development snapshots từ 2023-11-30 đến 2025-01-24.
- Nguồn duy nhất: `M2/artifacts/m2-task5-ward-v1/diagnostics.csv`.
- Không fit lại model, không chọn lại K, không dùng return/Sharpe/ROI và không truy cập final holdout.

## Quy trình

Notebook đọc 105 dòng diagnostics K=2..8, lọc đúng 15 dòng K=2, kiểm tra hội tụ và tổng hợp năm metric với trọng số mỗi snapshot bằng nhau. Các giá trị K=3..8 là bằng chứng của giai đoạn khảo sát K; chúng không tham gia đánh giá Ward chính thức tại K=2.

## Kết quả tổng hợp

| metric | n_total | n_available | mean | median | minimum | maximum |
| --- | --- | --- | --- | --- | --- | --- |
| silhouette | 15 | 15 | 0.763118 | 0.755722 | 0.458851 | 0.943929 |
| davies_bouldin | 15 | 15 | 0.578858 | 0.534333 | 0.267141 | 1.093217 |
| calinski_harabasz | 15 | 15 | 614.645839 | 316.391783 | 118.873252 | 1882.058299 |
| inertia | 15 | 15 | 61151.116169 | 2158.608251 | 1304.124507 | 419136.924313 |
| cluster_balance | 15 | 15 | 0.080491 | 0.067669 | 0.010292 | 0.223602 |

## Kết quả từng snapshot

| Snapshot | Silhouette | DB | CH | Inertia | Balance |
| --- | --- | --- | --- | --- | --- |
| 2023-11-30 | 0.762987 | 0.549272 | 210.950916 | 1304.124507 | 0.067669 |
| 2023-12-29 | 0.755722 | 0.493906 | 378.398170 | 1396.643410 | 0.089385 |
| 2024-01-31 | 0.695411 | 0.587799 | 233.930208 | 1520.946055 | 0.094972 |
| 2024-02-29 | 0.723123 | 0.513532 | 316.391783 | 1480.098520 | 0.094972 |
| 2024-03-29 | 0.524664 | 1.093217 | 118.873252 | 1649.370732 | 0.223602 |
| 2024-04-26 | 0.704479 | 0.590603 | 239.277992 | 1674.880177 | 0.075377 |
| 2024-05-31 | 0.558701 | 0.879652 | 164.635080 | 1909.424379 | 0.163158 |
| 2024-06-28 | 0.748492 | 0.534333 | 249.860699 | 2158.608251 | 0.048035 |
| 2024-07-31 | 0.458851 | 1.077800 | 119.007501 | 2464.520666 | 0.204878 |
| 2024-08-30 | 0.903261 | 0.475227 | 919.686722 | 122029.496743 | 0.036585 |
| 2024-09-30 | 0.935512 | 0.267141 | 1882.058299 | 109618.593378 | 0.020202 |
| 2024-10-31 | 0.943929 | 0.287598 | 1680.007440 | 143137.741318 | 0.015025 |
| 2024-11-29 | 0.911055 | 0.606436 | 1027.682234 | 419136.924313 | 0.044177 |
| 2024-12-31 | 0.905533 | 0.391856 | 965.060327 | 53268.069172 | 0.019031 |
| 2025-01-24 | 0.915044 | 0.334505 | 713.866970 | 54517.300914 | 0.010292 |

## Nhận định

- Median Silhouette = **0.755722**, Median Davies–Bouldin = **0.534333**. Silhouette thấp nhất là **0.458851** tại `2024-07-31`.
- Median Cluster Balance = **0.067669**; mức thấp nhất **0.010292**. Ward tạo cấu trúc bất đối xứng, nên Silhouette cao không đồng nghĩa hai cụm cân bằng.
- Median tỷ trọng cụm nhỏ trên toàn universe là khoảng **6.34%**. Dữ liệu xác nhận mất cân bằng; heavy-tail hoặc hành vi dòng tiền chỉ là giả thuyết cần bằng chứng riêng.
- Không so sánh Inertia tuyệt đối giữa các tháng có quy mô và phân tán khác nhau.

## Phán quyết và handoff

Ward đủ điều kiện kỹ thuật để đưa vào Nhiệm vụ 10, kèm cảnh báo mất cân bằng. Báo cáo chưa xếp hạng ba phương án, chưa chọn final method và không đưa ra khuyến nghị đầu tư.
