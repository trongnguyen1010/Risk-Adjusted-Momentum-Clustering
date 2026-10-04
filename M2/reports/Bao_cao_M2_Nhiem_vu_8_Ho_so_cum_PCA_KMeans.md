# Báo cáo Nhiệm vụ 8 — Hồ sơ cụm PCA + K-Means

Nguồn profile và scaler: `m2-task6-pca-kmeans-v1`; không fit lại model/scaler.
Các thống kê Mean/Median tính qua profile tháng, không phải phân phối từng cổ phiếu.

## A — Chân dung kinh tế
Cụm 0: size mean=14.73, median=15.00;
thanh khoản mean=371.81, median=359.15 tỷ VND/phiên;
beta mean=1.3013, median=1.2562.
Cụm 1: size mean=359.60, median=229.00;
thanh khoản mean=14.94, median=14.27 tỷ VND/phiên;
beta mean=0.6080, median=0.6200.
Giữ nhãn Cụm 0/Cụm 1; không gán nhãn đầu tư từ một feature đơn lẻ.

## B — Động lực phân tách chính và tính nhất quán
Chênh lệch chuẩn hóa lớn nhất là liquidity_21: ΔZ=64.5071;
Z mean C0=66.0005, C1=1.4934.
Cụm 0 có liquidity cao hơn ở 15/15 tháng và mom_63 cao hơn ở 12/15 tháng.
Điều này mô tả phân hóa đặc trưng, chưa chứng minh cơ chế dòng tiền hay quan hệ nhân quả.
Kiểm tra tháng 04/2024 và 07/2024 qua beta/momentum/MDD trong bảng riêng;
không kết luận về VN-Index khi notebook không đọc dữ liệu chỉ số.

## C — Tính khả thi cho M3
Thanh khoản là thông tin mô tả về khả năng giao dịch; mean chịu ảnh hưởng các mã cực đoan.
Chưa có size vốn, tỷ lệ tham gia volume, weights hoặc mô phỏng thực thi nên chưa thể
khẳng định đủ sức chứa hay không có slippage. Kiểm chứng chi phí thuộc M3.
Không khuyến nghị mua cụm nào, không sử dụng Sharpe/lợi nhuận hoặc holdout.

## Bảng 1
| aligned_cluster_id | size | liquidity_21_ty_vnd | beta_126 | vol_63 | mdd_126 | mom_21 | mom_63 | mom_126 | mom_252 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cụm 0 (Mean) | 14.7333 | 371.8099 | 1.3013 | 0.2972 | -0.1928 | 0.0265 | 0.0785 | 0.1335 | 0.3938 |
| Cụm 0 (Median) | 15.0 | 359.1518 | 1.2562 | 0.2959 | -0.1773 | 0.0307 | 0.0749 | 0.1016 | 0.4123 |
| Cụm 1 (Mean) | 359.6 | 14.9442 | 0.608 | 0.3537 | -0.2109 | 0.0138 | 0.029 | 0.0555 | 0.1877 |
| Cụm 1 (Median) | 229.0 | 14.2662 | 0.62 | 0.3348 | -0.217 | 0.0096 | 0.0366 | 0.0397 | 0.1813 |
## Bảng 2
| Đặc trưng | Cụm 0 (Mean) | Cụm 1 (Mean) | Chênh lệch (Cụm 0 - Cụm 1) |
| --- | --- | --- | --- |
| size | 14.7333 | 359.6 | -344.8667 |
| liquidity_21_ty_vnd | 371.8099 | 14.9442 | 356.8657 |
| beta_126 | 1.3013 | 0.608 | 0.6933 |
| vol_63 | 0.2972 | 0.3537 | -0.0565 |
| mdd_126 | -0.1928 | -0.2109 | 0.0181 |
| mom_21 | 0.0265 | 0.0138 | 0.0127 |
| mom_63 | 0.0785 | 0.029 | 0.0495 |
| mom_126 | 0.1335 | 0.0555 | 0.078 |
| mom_252 | 0.3938 | 0.1877 | 0.2061 |
## Bảng 3
| Snapshot | Size Cụm 0 | Size Cụm 1 | Liquidity Cụm 0 (tỷ VND) | Liquidity Cụm 1 (tỷ VND) |
| --- | --- | --- | --- | --- |
| 2023-11-30 | 9.0 | 133.0 | 201.2277 | 8.8951 |
| 2023-12-29 | 16.0 | 179.0 | 332.4347 | 14.5066 |
| 2024-01-31 | 17.0 | 179.0 | 295.1742 | 14.2662 |
| 2024-02-29 | 17.0 | 179.0 | 359.1518 | 16.6823 |
| 2024-03-29 | 15.0 | 182.0 | 492.0194 | 26.0962 |
| 2024-04-26 | 14.0 | 200.0 | 475.6056 | 23.6669 |
| 2024-05-31 | 15.0 | 206.0 | 419.7187 | 24.6562 |
| 2024-06-28 | 11.0 | 229.0 | 576.2641 | 29.329 |
| 2024-07-31 | 17.0 | 230.0 | 323.0802 | 20.2449 |
| 2024-08-30 | 21.0 | 574.0 | 288.0955 | 6.7315 |
| 2024-09-30 | 16.0 | 590.0 | 371.0342 | 7.29 |
| 2024-10-31 | 13.0 | 595.0 | 421.114 | 7.6587 |
| 2024-11-29 | 8.0 | 772.0 | 462.588 | 7.8328 |
| 2024-12-31 | 11.0 | 578.0 | 357.8787 | 10.1187 |
| 2025-01-24 | 21.0 | 568.0 | 201.7611 | 6.1877 |
## Z trung bình theo scaler tháng
| aligned_cluster_id | mom_21 | mom_63 | mom_126 | mom_252 | vol_63 | mdd_126 | beta_126 | liquidity_21 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.271 | 0.4893 | 0.491 | 0.6658 | -0.0274 | 0.0289 | 0.8071 | 66.0005 |
| 1 | 0.1046 | 0.1338 | 0.1442 | 0.1687 | 0.132 | -0.1002 | 0.038 | 1.4934 |
![Radar](../artifacts/m2-evaluation-pca-kmeans/radar_chart.png)
![Heatmap](../artifacts/m2-evaluation-pca-kmeans/heatmap.png)
