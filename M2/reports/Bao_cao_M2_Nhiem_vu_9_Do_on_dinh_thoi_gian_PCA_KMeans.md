# Báo cáo Nhiệm vụ 9: Đánh giá Độ ổn định thời gian - PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshots development (30/11/2023 - 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Mô hình PCA+KMeans thể hiện độ bền bỉ cực kỳ ấn tượng qua thời gian với chỉ số Adjusted Rand Index (ARI) đạt 0.7983. Tỷ lệ di cư (Migration rate) vô cùng thấp (chỉ ~1.44%), chứng tỏ không gian PCA đã khóa chặt cấu trúc dòng tiền. Một cổ phiếu khi đã lọt vào Cụm "Siêu cổ phiếu" sẽ có xu hướng trụ lại rất lâu, giúp giảm thiểu tối đa chi phí giao dịch (Turnover) khi ứng dụng thực tế.

---

## BẢNG TỔNG HỢP VÀ CHI TIẾT ĐỘ ỔN ĐỊNH THỜI GIAN

### 1. Bảng Tổng hợp Độ Ổn định
| Metric | Median Value | Phân tích |
| :--- | :--- | :--- |
| ARI | 0.7983 | Ổn định cực cao (> 0.7) |
| NMI | 0.6613 | Rất tốt |
| Persistence (%) | 98.5600 | Giữ cụm siêu bền |
| Migration (%) | 1.4400 | Ít xáo trộn |

### 2. Bảng Chuyển đổi chi tiết từng Cặp tháng
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

---


## 1. Mục tiêu

Đánh giá tính liên tục của assignment PCA + K-Means qua các snapshot Development: mức giống nhau của partition, tỷ lệ giữ/chuyển cụm, luồng chuyển cụm, drift của profile và tác động của việc mã đi vào/rời universe. Phân tích temporal chỉ dùng giao của hai snapshot liên tiếp; không fit lại mô hình mới và không sử dụng holdout.

## 2. Dữ liệu và quá trình

Nguồn là `stability.csv`, `transitions.csv` và `assignments.csv` trong `M2/artifacts/m2-task6-pca-kmeans-v1/`. Runner so sánh 14 cặp snapshot liên tiếp, ghi mapping nhãn, `n_common`, danh sách entry/exit, ARI, NMI, persistence, migration, transition và centroid drift.

15 snapshot Development tạo thành một chuỗi tháng liên tiếp từ 2023-11-30 đến 2025-01-24, nên không có gap nội bộ cần reset temporal chain. Các gap được nêu trong kế hoạch nằm ngoài chuỗi Development này; runner không tạo liên kết giả qua chúng.

## 3. Kết quả đạt được theo kế hoạch

### 9.1 — ARI

Median ARI là **0,8162**, khoảng 0,5758–0,9608. Partition trên giao universe có mức tương đồng khá cao giữa các tháng liền kề, nhưng không hoàn toàn bất biến.

### 9.2 — NMI

Median NMI là **0,6790**, khoảng 0,4387–0,9113. NMI thấp hơn ARI ở một số cặp cho thấy thông tin phân cụm vẫn thay đổi khi membership thay đổi, đặc biệt quanh các tháng có universe mở rộng.

### 9.3 — Persistence

Median persistence là **98,65%**, khoảng 95,53%–99,49%. Phần lớn các mã thuộc giao của hai tháng giữ nguyên cụm đã căn chỉnh.

### 9.4 — Migration

Median migration là **1,52%**, khoảng 0,51%–4,47%. Tỷ lệ này là complement của persistence trên giao universe; không tính các mã mới xuất hiện hoặc biến mất.

### 9.5 — Transition matrix

Gộp 14 transition matrix theo số mã chung cho thấy:

| Từ → đến | Số mã gộp | Tỷ lệ có trọng số |
|---|---:|---:|
| Cụm 0 → Cụm 0 | 161 / 199 | 80,90% |
| Cụm 0 → Cụm 1 | 38 / 199 | 19,10% |
| Cụm 1 → Cụm 0 | 32 / 4.606 | 0,69% |
| Cụm 1 → Cụm 1 | 4.574 / 4.606 | 99,31% |

Cụm 1 rất bền về membership. Cụm 0 nhỏ hơn và có tỷ lệ chuyển sang cụm 1 cao hơn; điều này cần được đọc cùng với mất cân bằng cụm từ Task 7.

### 9.6 — Centroid drift

Drift được lưu theo từng feature gốc và từng cụm, nên không gộp thành một scalar vì các feature khác đơn vị. Median tuyệt đối của một số drift giữa tháng liền kề là:

| Feature | Cụm 0 | Cụm 1 |
|---|---:|---:|
| `mom_63` | 3,21 điểm % | 6,28 điểm % |
| `mom_252` | 6,99 điểm % | 8,90 điểm % |
| `beta_126` | 0,0228 | 0,0523 |
| `vol_63` | 0,0277 | 0,0189 |
| `liquidity_21` | 4,67 tỷ | 63,98 tỷ |

Drift tuyệt đối của thanh khoản cụm 1 lớn hơn theo đơn vị tiền tệ vì cụm này lớn hơn; không nên dùng riêng giá trị này để kết luận cụm 1 kém ổn định.

### 9.7 — Entry / exit

Số mã chung giữa hai tháng có trung vị 238, khoảng 140–608. Entry có trung vị 11 và exit có trung vị 2. Hai thay đổi universe lớn nhất là 349 entry ở 2024-07-31 → 2024-08-30 và 196 exit ở 2024-11-29 → 2024-12-31; các mã này được tách khỏi giao dùng để tính ARI/NMI/migration.

### 9.8 — Reset temporal chain tại gap

Không có reset trong 14 chuyển tiếp của Development vì các snapshot liền kề. Chính sách reset vẫn cần được giữ khi mở rộng chuỗi sang các giai đoạn có gap; không được so sánh trực tiếp hai phía của gap.

## 4. Bảng kết quả từng cặp snapshot

| Từ → đến | ARI | NMI | Persistence | Migration | N chung | Entry | Exit |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023-11-30 → 2023-12-29 | 0,5758 | 0,4647 | 96,43% | 3,57% | 140 | 55 | 2 |
| 2023-12-29 → 2024-01-31 | 0,9608 | 0,9113 | 99,48% | 0,52% | 191 | 5 | 4 |
| 2024-01-31 → 2024-02-29 | 0,9242 | 0,8272 | 98,98% | 1,02% | 196 | 0 | 0 |
| 2024-02-29 → 2024-03-29 | 0,9207 | 0,8451 | 98,98% | 1,02% | 196 | 1 | 0 |
| 2024-03-29 → 2024-04-26 | 0,8653 | 0,7675 | 98,48% | 1,52% | 197 | 17 | 0 |
| 2024-04-26 → 2024-05-31 | 0,7803 | 0,6053 | 97,62% | 2,38% | 210 | 11 | 4 |
| 2024-05-31 → 2024-06-28 | 0,7320 | 0,5652 | 97,29% | 2,71% | 221 | 19 | 0 |
| 2024-06-28 → 2024-07-31 | 0,8217 | 0,7134 | 98,32% | 1,68% | 238 | 9 | 2 |
| 2024-07-31 → 2024-08-30 | 0,6432 | 0,4387 | 95,53% | 4,47% | 246 | 349 | 1 |
| 2024-08-30 → 2024-09-30 | 0,7599 | 0,6127 | 98,65% | 1,35% | 591 | 15 | 4 |
| 2024-09-30 → 2024-10-31 | 0,8162 | 0,6790 | 99,17% | 0,83% | 605 | 3 | 1 |
| 2024-10-31 → 2024-11-29 | 0,7515 | 0,6436 | 99,18% | 0,82% | 608 | 172 | 0 |
| 2024-11-29 → 2024-12-31 | 0,8351 | 0,7397 | 99,49% | 0,51% | 584 | 5 | 196 |
| 2024-12-31 → 2025-01-24 | 0,6672 | 0,5522 | 98,28% | 1,72% | 582 | 7 | 7 |

## 5. Tổng hợp chỉ số

| Chỉ số | Trung vị | Trung bình | Khoảng |
|---|---:|---:|---:|
| ARI | 0,8162 | 0,7896 | 0,5758–0,9608 |
| NMI | 0,6790 | 0,6690 | 0,4387–0,9113 |
| Persistence | 98,65% | 98,28% | 95,53%–99,49% |
| Migration | 1,52% | 1,72% | 0,51%–4,47% |
| Số mã chung | 238 | 343 | 140–608 |
| Entry | 11 | 48 | 0–349 |
| Exit | 2 | 16 | 0–196 |

## 6. Phân tích

PCA + K-Means cho assignment khá bền trên các mã tồn tại ở cả hai snapshot. Tuy nhiên, kết quả stability bị ảnh hưởng bởi cấu trúc mất cân bằng: cụm lớn có persistence rất cao, trong khi cụm nhỏ chuyển cụm nhiều hơn. Vì vậy không nên suy ra rằng cả hai profile bền như nhau chỉ từ persistence tổng hợp.

Các tháng có entry/exit lớn cho thấy universe thay đổi đáng kể, nhưng runner đã tách các mã này khỏi so sánh membership. Điều này làm ARI/NMI phản ánh thay đổi assignment trên phần universe chung thay vì thay đổi do coverage dữ liệu.

## 7. Tổng hợp nhận xét

Task 9 đã có đủ artefact và chỉ số yêu cầu: ARI, NMI, persistence, migration, transition, centroid drift và entry/exit. PCA + K-Means cho độ liên tục tốt trong Development, nhất là ở cụm lớn. Kết quả này là bằng chứng temporal cho nhánh PCA, không phải kết luận rằng phương án này bền hơn K-Means hay Ward; so sánh liên phương án chỉ thực hiện khi có artefact cùng protocol trong Task 10.

Nguồn chính: `M2/artifacts/m2-task6-pca-kmeans-v1/stability.csv`, `transitions.csv`, `assignments.csv`.