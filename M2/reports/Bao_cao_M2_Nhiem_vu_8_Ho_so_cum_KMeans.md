# Báo cáo M2 Nhiệm vụ 8 — Hồ sơ cụm K-Means

## Nguồn và phạm vi

Đọc duy nhất [Task 4 cluster_profiles.csv](../artifacts/m2-task4-kmeans-baseline-v1/cluster_profiles.csv) và scaler đã fit trong `M2/models/kmeans/`. Gồm 60 snapshot phát triển, 2019-01-31 đến 2023-12-29; mỗi tháng có hai cụm. Không fit lại mô hình hay trích xuất feature.

`aligned_cluster_id` là nhãn đã căn chỉnh. Trung bình và trung vị bên dưới tính **theo 60 giá trị hồ sơ tháng của từng cụm**, không gộp cổ phiếu xuyên tháng. Thanh khoản đổi từ VND/phiên sang tỷ VND/phiên.

## Bảng 1 — Hồ sơ theo cụm (4 × 10)

| aligned_cluster_id | size | liquidity_21_ty_vnd | beta_126 | vol_63 | mdd_126 | mom_21 | mom_63 | mom_126 | mom_252 |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cụm 0 (Mean) | 14.9000 | 348.3368 | 1.2568 | 0.3903 | -0.2529 | 0.0259 | 0.1072 | 0.2144 | 0.3919 |
| Cụm 0 (Median) | 14.0000 | 253.3292 | 1.2719 | 0.4029 | -0.2167 | 0.0223 | 0.0798 | 0.0887 | 0.1194 |
| Cụm 1 (Mean) | 745.8667 | 5.2630 | 0.3494 | 0.5318 | -0.2722 | 0.0189 | 0.0594 | 0.1194 | 0.2355 |
| Cụm 1 (Median) | 706.5000 | 3.8038 | 0.3537 | 0.5275 | -0.2580 | 0.0189 | 0.0450 | 0.0830 | 0.1187 |

## Bảng 2 — Chênh lệch trung bình (9 × 4)

| Đặc trưng | Cụm 0 (Mean) | Cụm 1 (Mean) | Chênh lệch (Cụm 0 - Cụm 1) |
|:---|---:|---:|---:|
| size | 14.9000 | 745.8667 | -730.9667 |
| liquidity_21_ty_vnd | 348.3368 | 5.2630 | 343.0738 |
| beta_126 | 1.2568 | 0.3494 | 0.9075 |
| vol_63 | 0.3903 | 0.5318 | -0.1415 |
| mdd_126 | -0.2529 | -0.2722 | 0.0192 |
| mom_21 | 0.0259 | 0.0189 | 0.0069 |
| mom_63 | 0.1072 | 0.0594 | 0.0478 |
| mom_126 | 0.2144 | 0.1194 | 0.0949 |
| mom_252 | 0.3919 | 0.2355 | 0.1563 |

## Nhận xét học thuật

1. **Về Thanh khoản và Beta:** Cụm 0 gồm nhóm cổ phiếu trụ / vốn hóa lớn thanh khoản cao vượt trội (trung bình 348 tỷ VND/phiên) với Beta nhạy cảm với thị trường (1.26). Cụm 1 là đại chúng thị trường với thanh khoản trung bình 5.26 tỷ VND/phiên và Beta trung bình 0.35.
2. **Về Động lượng (Momentum):** Cụm 0 có động lượng vượt trội hơn Cụm 1 ở mọi kỳ hạn (1T, 3T, 6T, 12T).
3. **Về Rủi ro (Volatility & MDD):** Cụm 1 gồm nhiều cổ phiếu thanh khoản thấp/vừa có độ biến động giá 63 ngày (`vol_63`) cao hơn (0.53 so với 0.39 của Cụm 0).
