# Báo cáo Nhiệm vụ 9 — Temporal Stability PCA + K-Means

Nguồn: ba CSV phẳng ở `m2-evaluation-pca-kmeans`; 14 cặp development liên tiếp.
Temporal inputs được dựng từ cùng nhãn aligned của task 6 và kiểm tra checksum.

## A — Phán quyết độ ổn định
Median ARI=0.798251, NMI=0.661313; ARI >0,70 ở 11/14 cặp.
ARI thấp nhất 0.575783 tại 2023-11-30 → 2023-12-29;
có 0 cặp ARI <0,50. Phân hoạch khá ổn định, không bất biến.
Không có dữ liệu VN-Index trong notebook nên không khẳng định cú sốc thị trường là nguyên nhân.

## B — Persistence/Migration và tác động tiềm tàng
Median Persistence=98.5618%, Migration=1.4382% trên giao universe.
Tỷ lệ giữ cụm gộp theo lượt: C0=80.9045%
(cơ sở 199 lượt), C1=99.3053%
(cơ sở 4606 lượt); tổng thể bị chi phối bởi nhóm lớn.
Migration thấp không đồng nghĩa chi phí giao dịch thấp: Entry+Exit lớn nhất so với n_common
là 142.2764% tại 2024-07-31 → 2024-08-30.
Chi phí/turnover danh mục còn phụ thuộc weights, size vốn và quy tắc tái cân bằng ở M3.
Drift dùng tâm gốc thật, theo từng feature; không gộp khác đơn vị.

## C — Bàn giao và giới hạn
Đủ bốn bảng và hai biểu đồ; đúng 14 cặp, không nối qua gap 02/2025–01/2026.
Kết quả mô tả development-only, không chứng minh PCA bền hơn phương án khác,
không phải Dynamic Clustering, không dùng để chọn mã hoặc suy diễn lợi nhuận.

## Bảng 1
| Chỉ số (Metric) | Số cặp quan sát | Trung bình (Mean) | Trung vị (Median) | Nhỏ nhất (Min) | Lớn nhất (Max) |
| --- | --- | --- | --- | --- | --- |
| ARI | 14 | 0.7896 | 0.7983 | 0.5758 | 0.9608 |
| NMI | 14 | 0.669 | 0.6613 | 0.4387 | 0.9113 |
| Persistence (%) | 14 | 98.2756 | 98.5618 | 95.5285 | 99.4863 |
| Migration (%) | 14 | 1.7244 | 1.4382 | 0.5137 | 4.4715 |
## Bảng 2
| Từ Cụm (From) | Sang Cụm (To) | Tổng số lượt (Count) | Tổng số cơ sở (Denominator) | Tỷ lệ xác suất (Rate %) |
| --- | --- | --- | --- | --- |
| Cụm 0 | Cụm 0 (Giữ nguyên) | 161 | 199 | 80.9045 |
| Cụm 0 | Cụm 1 (Chuyển cụm) | 38 | 199 | 19.0955 |
| Cụm 1 | Cụm 1 (Giữ nguyên) | 4574 | 4606 | 99.3053 |
| Cụm 1 | Cụm 0 (Chuyển cụm) | 32 | 4606 | 0.6947 |
## Bảng 3
| Đặc trưng | Độ lệch tuyệt đối Cụm 0 (Mean \|Delta\|) | Độ lệch tuyệt đối Cụm 1 (Mean \|Delta\|) |
| --- | --- | --- |
| liquidity_21 (tỷ VND) | 94.1176 | 3.9778 |
| beta_126 | 0.0562 | 0.0493 |
| vol_63 | 0.0283 | 0.0332 |
| mdd_126 | 0.0233 | 0.0153 |
| mom_21 | 0.0587 | 0.0412 |
| mom_63 | 0.0616 | 0.0347 |
| mom_126 | 0.0697 | 0.0416 |
| mom_252 | 0.1075 | 0.0527 |
## Bảng 4
| Cặp Snapshot (From -> To) | Số mã chung (n_common) | Số mã mới (Entry) | Số mã rớt (Exit) | Tỷ lệ luân chuyển (%) |
| --- | --- | --- | --- | --- |
| 2023-11 → 2023-12 | 140 | 55 | 2 | 40.7143 |
| 2023-12 → 2024-01 | 191 | 5 | 4 | 4.712 |
| 2024-01 → 2024-02 | 196 | 0 | 0 | 0.0 |
| 2024-02 → 2024-03 | 196 | 1 | 0 | 0.5102 |
| 2024-03 → 2024-04 | 197 | 17 | 0 | 8.6294 |
| 2024-04 → 2024-05 | 210 | 11 | 4 | 7.1429 |
| 2024-05 → 2024-06 | 221 | 19 | 0 | 8.5973 |
| 2024-06 → 2024-07 | 238 | 9 | 2 | 4.6218 |
| 2024-07 → 2024-08 | 246 | 349 | 1 | 142.2764 |
| 2024-08 → 2024-09 | 591 | 15 | 4 | 3.2149 |
| 2024-09 → 2024-10 | 605 | 3 | 1 | 0.6612 |
| 2024-10 → 2024-11 | 608 | 172 | 0 | 28.2895 |
| 2024-11 → 2024-12 | 584 | 5 | 196 | 34.4178 |
| 2024-12 → 2025-01 | 582 | 7 | 7 | 2.4055 |
![Temporal](../artifacts/m2-evaluation-pca-kmeans/temporal_trends.png)
![Transitions](../artifacts/m2-evaluation-pca-kmeans/transition_heatmap.png)
