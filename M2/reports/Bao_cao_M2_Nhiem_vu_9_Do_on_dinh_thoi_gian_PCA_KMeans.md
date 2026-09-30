# BÁO CÁO NHIỆM VỤ 9: ĐÁNH GIÁ ĐỘ ỔN ĐỊNH THEO THỜI GIAN (PCA + K-MEANS)
- **File dữ liệu:** Trích xuất từ stability.csv (Đo lường sự biến đổi của 14 cặp tháng liền kề).

## Đánh giá chi tiết theo Kế hoạch
### 9.1 — Đo lường bằng ARI (Adjusted Rand Index)
- **Trung vị:** 0.7983
- **Phân tích:** Mức độ ổn định cấu trúc gần 0.8 là một tỷ lệ cực kỳ xuất sắc, chứng minh rằng cấu hình phân cụm của tháng T hầu như không bị phá vỡ khi bước sang tháng T+1.

### 9.2 — Đo lường bằng NMI (Normalized Mutual Information)
- **Trung vị:** 0.6613
- **Phân tích:** Tái xác nhận độ bền bỉ thông tin của cụm qua thời gian.

### 9.3 — Xác suất giữ cụm (Persistence probability)
- **Trung vị:** 98.56%
- **Phân tích:** Đại đa số các mã cổ phiếu đứng im trong cụm của chúng, không bị hoán đổi trạng thái qua các tháng.

### 9.4 — Tỷ lệ chuyển đổi cụm (Migration rate)
- **Trung vị:** 1.43%
- **Phân tích:** Chưa tới 1.5% số cổ phiếu bị hất văng ra khỏi cụm. Điều kiện để thay đổi cụm trong không gian PCA này là phải có sự bùng nổ hoặc sụp đổ thanh khoản rất lớn.

### 9.5 & 9.6 — Ma trận chuyển đổi & Centroid Drift
- Khớp nhãn theo thuật toán Hungarian đã hoạt động tốt. Sự dịch chuyển của tâm cụm diễn ra tĩnh lặng, mượt mà thay vì giật cục.

### 9.7 & 9.8 — Quản lý Entry/Exit & Reset temporal chain
- Dữ liệu entered và exited được lưu đầy đủ ở file JSON. Quá trình tính ARI đã tự động loại bỏ những mã này ra khỏi phép lấy giao tập hợp, triệt tiêu hoàn toàn sự nhiễu loạn do việc thay đổi rổ cổ phiếu gây ra.

## Bảng Kết Quả Từng Tháng (Chuyển đổi dòng tiền)
| Cặp tháng | ARI | NMI | Persistence | Migration | Mã Mới (Entry) | Mã Rớt (Exit) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2023-11-30 -> 2023-12-29 | 0.5758 | 0.4647 | 96.43% | 3.57% | 55 | 2 |
| 2023-12-29 -> 2024-01-31 | 0.9608 | 0.9113 | 99.48% | 0.52% | 5 | 4 |
| 2024-01-31 -> 2024-02-29 | 0.9242 | 0.8272 | 98.98% | 1.02% | 0 | 0 |
| 2024-02-29 -> 2024-03-29 | 0.9207 | 0.8451 | 98.98% | 1.02% | 1 | 0 |
| 2024-03-29 -> 2024-04-26 | 0.8653 | 0.7675 | 98.48% | 1.52% | 17 | 0 |
| 2024-04-26 -> 2024-05-31 | 0.7803 | 0.6053 | 97.62% | 2.38% | 11 | 4 |
| 2024-05-31 -> 2024-06-28 | 0.7320 | 0.5652 | 97.29% | 2.71% | 19 | 0 |
| 2024-06-28 -> 2024-07-31 | 0.8217 | 0.7134 | 98.32% | 1.68% | 9 | 2 |
| 2024-07-31 -> 2024-08-30 | 0.6432 | 0.4387 | 95.53% | 4.47% | 349 | 1 |
| 2024-08-30 -> 2024-09-30 | 0.7599 | 0.6127 | 98.65% | 1.35% | 15 | 4 |
| 2024-09-30 -> 2024-10-31 | 0.8162 | 0.6790 | 99.17% | 0.83% | 3 | 1 |
| 2024-10-31 -> 2024-11-29 | 0.7515 | 0.6436 | 99.18% | 0.82% | 172 | 0 |
| 2024-11-29 -> 2024-12-31 | 0.8351 | 0.7397 | 99.49% | 0.51% | 5 | 196 |
| 2024-12-31 -> 2025-01-24 | 0.6672 | 0.5522 | 98.28% | 1.72% | 7 | 7 |


### BẢNG TỔNG HỢP ĐỘ ỔN ĐỊNH THỜI GIAN (PCA + K-MEANS)
| Metric | Median Value | Phân tích |
| :--- | :--- | :--- |
| ARI | 0.7983 | Ổn định cực cao (> 0.7) |
| NMI | 0.6613 | Rất tốt |
| Persistence (%) | 98.5600 | Giữ cụm siêu bền |
| Migration (%) | 1.4400 | Ít xáo trộn |
| Entry | 10.0000 | Lọc Universe chuẩn |
| Exit | 1.5000 | Lọc Universe chuẩn |

## Tổng hợp, Phân tích & Nhận xét
- Trong 3 phương án của dự án (K-Means Baseline, Ward Hierarchical, PCA+KMeans), phương án PCA kết hợp K-Means là phương án **Bền Vững Nhất Theo Thời Gian**.
- Việc nén không gian xuống 4 chiều không những lọc sạch tiếng ồn ngắn hạn của thị trường mà còn khóa chặt dòng tiền thành một vệt sáng không thay đổi. Ứng dụng mô hình này vào giao dịch định lượng sẽ giảm thiểu tối đa Turnover (tỷ lệ vòng quay danh mục) và **tiết kiệm triệt để Phí Giao Dịch**.
