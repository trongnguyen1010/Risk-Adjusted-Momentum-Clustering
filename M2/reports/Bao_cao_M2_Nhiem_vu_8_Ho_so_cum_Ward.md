# Báo cáo M2 — Nhiệm vụ 8: Hồ sơ cụm Ward

## Phạm vi và nguồn bằng chứng

- Ward Hierarchical, Global K=2, 15 development snapshots.
- Input chính: `M2/artifacts/m2-evaluation-ward/cluster_profiles.csv` (30 dòng × 13 cột), đúng schema cố định của kế hoạch M2.
- Scaler trong `M2/artifacts/m2-task5-ward-v1/models/*.json` chỉ được đọc để chuyển tâm cụm sang Robust Z-score; không fit scaler hay model mới.
- Không dùng return/Sharpe/ROI và không truy cập final holdout.

## Bảng 1 — Hồ sơ Mean/Median

| aligned_cluster_id | size | liquidity_21_ty_vnd | beta_126 | vol_63 | mdd_126 | mom_21 | mom_63 | mom_126 | mom_252 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cụm 0 (Mean) | 19.066667 | 340.800122 | 1.284245 | 0.296220 | -0.192114 | 0.033691 | 0.084696 | 0.131739 | 0.406759 |
| Cụm 0 (Median) | 16.000000 | 332.434746 | 1.265687 | 0.295873 | -0.183128 | 0.030720 | 0.074871 | 0.105737 | 0.412317 |
| Cụm 1 (Mean) | 355.266667 | 12.783340 | 0.596136 | 0.353428 | -0.210587 | 0.013030 | 0.027128 | 0.053204 | 0.179782 |
| Cụm 1 (Median) | 205.000000 | 10.118749 | 0.603057 | 0.334801 | -0.216970 | 0.009575 | 0.035927 | 0.038861 | 0.171240 |

## Bảng 2 — So sánh đối đầu

| Đặc trưng | Cụm 0 (Mean) | Cụm 1 (Mean) | Chênh lệch (Cụm 0 - Cụm 1) |
| --- | --- | --- | --- |
| size | 19.066667 | 355.266667 | -336.200000 |
| liquidity_21 (tỷ VND) | 340.800122 | 12.783340 | 328.016783 |
| beta_126 | 1.284245 | 0.596136 | 0.688109 |
| vol_63 | 0.296220 | 0.353428 | -0.057207 |
| mdd_126 | -0.192114 | -0.210587 | 0.018473 |
| mom_21 | 0.033691 | 0.013030 | 0.020661 |
| mom_63 | 0.084696 | 0.027128 | 0.057568 |
| mom_126 | 0.131739 | 0.053204 | 0.078535 |
| mom_252 | 0.406759 | 0.179782 | 0.226977 |

## Bảng 3 — Quy mô và thanh khoản theo thời gian

| Snapshot | Size Cụm 0 | Size Cụm 1 | Liquidity Cụm 0 (tỷ VND) | Liquidity Cụm 1 (tỷ VND) |
| --- | --- | --- | --- | --- |
| 2023-11-30 | 9 | 133 | 201.227713 | 8.895114 |
| 2023-12-29 | 16 | 179 | 332.434746 | 14.506566 |
| 2024-01-31 | 17 | 179 | 295.174249 | 14.266154 |
| 2024-02-29 | 17 | 179 | 359.151771 | 16.682277 |
| 2024-03-29 | 36 | 161 | 275.235007 | 13.797159 |
| 2024-04-26 | 15 | 199 | 459.191122 | 22.633075 |
| 2024-05-31 | 31 | 190 | 280.601066 | 14.085956 |
| 2024-06-28 | 11 | 229 | 576.264143 | 29.329016 |
| 2024-07-31 | 42 | 205 | 194.936897 | 9.567566 |
| 2024-08-30 | 21 | 574 | 288.095511 | 6.731501 |
| 2024-09-30 | 12 | 594 | 423.177525 | 8.686030 |
| 2024-10-31 | 9 | 599 | 499.896620 | 9.235917 |
| 2024-11-29 | 33 | 747 | 214.751630 | 3.562014 |
| 2024-12-31 | 11 | 578 | 357.878668 | 10.118749 |
| 2025-01-24 | 6 | 583 | 353.985168 | 9.653003 |

## Bảng 4 — Mean Robust Z-score chưa clip

| aligned_cluster_id | mom_21 | mom_63 | mom_126 | mom_252 | vol_63 | mdd_126 | beta_126 | liquidity_21 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.363852 | 0.533461 | 0.493973 | 0.691997 | -0.022154 | 0.032961 | 0.787497 | 61.615269 |
| 1 | 0.094407 | 0.121573 | 0.132359 | 0.152436 | 0.128775 | -0.097713 | 0.023838 | 1.409773 |

## Nhận định

- Cụm 0 có Mean size **19.07 mã**, liquidity **340.80 tỷ VND/phiên**, beta **1.284245**; Cụm 1 tương ứng **355.27 mã**, **12.78 tỷ VND/phiên**, **0.596136**.
- `liquidity_21` là động lực phân tách lớn nhất theo chênh lệch Mean Robust Z (**60.205496** trước clipping), tiếp theo là beta và động lượng 12 tháng. Giá trị cực lớn phản ánh thanh khoản lệch mạnh trong bối cảnh không winsorize; chart clip ở 3 chỉ để hiển thị.
- Tháng 04/2024 và 07/2024, Cụm 0 có momentum ngắn hạn không vượt Cụm 1 nhưng vẫn cao hơn về beta, thanh khoản và phần lớn momentum dài hạn. Chân dung cụm có tính nhất quán tương đối, không tuyệt đối ở mọi kỳ hạn.
- Thanh khoản cấp cụm cho thấy khả năng giao dịch tương đối tốt hơn, nhưng chưa đủ để kết luận trượt giá hoặc capacity. M3 cần position size, trọng số, ADV participation và mô hình chi phí giao dịch.

## Phán quyết ba phần

**A — Chân dung kinh tế:** Cụm 0 là nhóm nhỏ, thanh khoản và beta cao, động lượng dài hạn cao hơn; Cụm 1 là phần lớn universe với hồ sơ gần trung tâm thị trường hơn.

**B — Động lực phân tách:** Thanh khoản là yếu tố chi phối số 1 theo Delta Robust Z; beta và momentum 12 tháng là các yếu tố kế tiếp.

**C — Tính khả thi cho M3:** Có tín hiệu thuận lợi về thanh khoản tương đối của Cụm 0, nhưng chưa thể phán quyết capacity hoặc slippage trước backtest M3.
