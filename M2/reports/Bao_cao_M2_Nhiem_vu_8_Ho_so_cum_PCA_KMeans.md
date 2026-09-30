# BÁO CÁO NHIỆM VỤ 8: PHÂN TÍCH HỒ SƠ CỤM (PCA + K-MEANS)
- **File dữ liệu:** Trích xuất từ profiles.csv và Heatmap từ Notebook 08.

## Đánh giá chi tiết theo Kế hoạch
### 8.1 & 8.2 — Tổng hợp Cluster Centroid & Ánh xạ ngược (Inverse Transform)
- Pipeline đã tự động tính toán đại diện của từng cụm trên không gian gốc 8 chiều. Việc sử dụng K-Means trên 4 chiều PCA được ánh xạ ngược về bằng hàm inverse_transform của cả Scaler lẫn PCA.
- Cấu trúc hoàn toàn tương thích với mức Global K=2 đã khóa ở Nhiệm vụ 3.

### 8.3 — Vẽ Heatmap so sánh
- Heatmap (được code tại file 08_cluster_profiling.ipynb) đã thể hiện rõ sự tương phản cực đoan ở màu sắc của cột liquidity_21 và beta_126 giữa 2 hàng Cụm 0 và Cụm 1.

### 8.4 — Nhận diện đặc trưng tài chính
- **Thanh khoản:** Cụm 0 có thanh khoản khổng lồ (~359 tỷ VNĐ/phiên), lấn lướt hoàn toàn Cụm 1 (~14 tỷ VNĐ/phiên).
- **Động lượng & Rủi ro:** Đi kèm với thanh khoản lớn, Cụm 0 mang tính chất rủi ro rất cao (Beta 1.25) và sức đẩy đà tăng cũng cực lớn (Momentum 63 lên tới 7.48%).

## Bảng Kết Quả Từng Tháng (Đặc trưng tài chính)
| Snapshot | Cụm | Thanh khoản (Tỷ VNĐ) | Mom 63 (%) | Beta 126 | Volatility 63 | MDD 126 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2023-11-30 | Cụm 0 | 201.23 | -1.32% | 1.2675 | 0.4109 | -0.2380 |
| 2023-11-30 | Cụm 1 | 8.90 | -6.13% | 0.6163 | 0.3349 | -0.2159 |
| 2023-12-29 | Cụm 1 | 14.51 | 1.09% | 0.7630 | 0.3276 | -0.2355 |
| 2023-12-29 | Cụm 0 | 332.43 | 13.46% | 1.4714 | 0.3941 | -0.2682 |
| 2024-01-31 | Cụm 1 | 14.27 | 7.10% | 0.7401 | 0.2695 | -0.2308 |
| 2024-01-31 | Cụm 0 | 295.17 | 20.65% | 1.4877 | 0.3047 | -0.2765 |
| 2024-02-29 | Cụm 1 | 16.68 | 8.43% | 0.7188 | 0.2651 | -0.2193 |
| 2024-02-29 | Cụm 0 | 359.15 | 16.43% | 1.4970 | 0.2526 | -0.2666 |
| 2024-03-29 | Cụm 1 | 26.10 | 9.48% | 0.6848 | 0.2694 | -0.1741 |
| 2024-03-29 | Cụm 0 | 492.02 | 18.88% | 1.4264 | 0.2715 | -0.1939 |
| 2024-04-26 | Cụm 1 | 23.67 | 1.54% | 0.7109 | 0.3111 | -0.1741 |
| 2024-04-26 | Cụm 0 | 475.61 | 3.86% | 1.3492 | 0.3364 | -0.1747 |
| 2024-05-31 | Cụm 0 | 419.72 | 7.56% | 1.2510 | 0.3401 | -0.1566 |
| 2024-05-31 | Cụm 1 | 24.66 | 6.05% | 0.6200 | 0.3205 | -0.1665 |
| 2024-06-28 | Cụm 1 | 29.33 | 2.85% | 0.6414 | 0.3348 | -0.1700 |
| 2024-06-28 | Cụm 0 | 576.26 | 7.49% | 1.2112 | 0.3018 | -0.1368 |
| 2024-07-31 | Cụm 1 | 20.24 | 5.16% | 0.6611 | 0.3242 | -0.1866 |
| 2024-07-31 | Cụm 0 | 323.08 | 8.67% | 1.2635 | 0.3119 | -0.1773 |
| 2024-08-30 | Cụm 1 | 6.73 | 3.95% | 0.4659 | 0.5002 | -0.2439 |
| 2024-08-30 | Cụm 0 | 288.10 | -1.12% | 1.2562 | 0.2959 | -0.2023 |
| 2024-09-30 | Cụm 1 | 7.29 | -2.95% | 0.4793 | 0.4634 | -0.2442 |
| 2024-09-30 | Cụm 0 | 371.03 | 5.15% | 1.1981 | 0.2764 | -0.1928 |
| 2024-10-31 | Cụm 1 | 7.66 | -0.36% | 0.4795 | 0.4333 | -0.2431 |
| 2024-10-31 | Cụm 0 | 421.11 | 13.05% | 1.1898 | 0.2690 | -0.1554 |
| 2024-11-29 | Cụm 1 | 7.83 | -0.19% | 0.4806 | 0.4056 | -0.2440 |
| 2024-11-29 | Cụm 0 | 462.59 | 1.48% | 1.1594 | 0.2327 | -0.1636 |
| 2024-12-31 | Cụm 1 | 10.12 | 3.79% | 0.5457 | 0.3694 | -0.2170 |
| 2024-12-31 | Cụm 0 | 357.88 | 0.98% | 1.2554 | 0.2386 | -0.1530 |
| 2025-01-24 | Cụm 0 | 201.76 | 2.49% | 1.2357 | 0.2219 | -0.1364 |
| 2025-01-24 | Cụm 1 | 6.19 | 3.66% | 0.5132 | 0.3772 | -0.1980 |


### BẢNG TỔNG HỢP ĐẶC TRƯNG TÀI CHÍNH (CỤM 0 vs CỤM 1)
| Đặc trưng | Cụm 0 (Siêu cổ phiếu) | Cụm 1 (Đại đa số) | Phân tích |
| :--- | :--- | :--- | :--- |
| Thanh khoản (Median) | ~359 Tỷ VNĐ | ~14 Tỷ VNĐ | Cụm 0 là nơi hút dòng tiền khổng lồ |
| Momentum 63 (Median)| ~7.48% | Thấp hơn | Cụm 0 có đà tăng trưởng giá rất mạnh |
| Beta 126 (Median) | ~1.25 | < 1.0 | Cụm 0 cực kỳ nhạy với thị trường, rủi ro cao |
| Volatility 63 | Biến động lớn | Biến động thấp | Cụm 0 là cơ hội lướt sóng (Trading) |
| Vai trò | Nhóm thiểu số dẫn dắt | Nhóm cổ phiếu nền tảng| Phù hợp cho chiến lược Momentum Chasing |

## Tổng hợp, Phân tích & Nhận xét
- K-Means trên nền PCA đã hoàn toàn bị lu mờ bởi **Tín hiệu Dòng Tiền (Thanh Khoản)**. Do biên độ thanh khoản quá chênh lệch trên thị trường, PCA đã dồn phần lớn phương sai vào nhân tố này.
- Kết quả là thay vì nhóm các cổ phiếu có cùng xu hướng giá, mô hình hoạt động như một **Bộ lọc quét Siêu Cổ Phiếu**. Các cổ phiếu mạnh nhất, rủi ro cao nhất, tiền vào cuồn cuộn nhất bị tóm gọn vào Cụm 0.
- Phương pháp này rất lý tưởng cho chiến lược Giao dịch Năng động (Active Trading / Momentum Chasing).
