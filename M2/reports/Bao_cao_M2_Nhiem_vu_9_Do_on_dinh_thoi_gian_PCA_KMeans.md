# Báo cáo Nhiệm vụ 9: Đánh giá Độ ổn định Thời gian – PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 14 cặp snapshot liên tiếp trong Development (30/11/2023 – 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)
**Nguồn:** `M2/artifacts/m2-evaluation-pca-kmeans/` (`temporal_stability.csv` 14 × 10, `transition_matrices.csv` 56 × 6, `centroid_drift.csv` 224 × 7) | **Notebook:** `M2/notebooks/09_temporal_stability_pca_kmeans.ipynb`

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Trên 14 cặp tháng liên tiếp, median ARI là **0,7983** (ARI > 0,70 ở 11/14 cặp, không cặp nào dưới 0,50) và median NMI là **0,6613**. Median Persistence **98,56%**, tức Migration **1,44%** (tối đa 4,47%) trên giao universe. Tỷ lệ giữ cụm gộp theo lượt là **80,90%** với Cụm 0 (cơ sở 199 lượt) và **99,31%** với Cụm 1 (cơ sở 4.606 lượt), nên tổng thể bị chi phối bởi nhóm lớn. Migration thấp không đồng nghĩa chi phí giao dịch thấp: tỷ lệ luân chuyển membership (Entry + Exit) lên tới 142,28% ở 2024-07 → 2024-08. Chuỗi 15 snapshot liên tục, không có liên kết vượt gap 02/2025–01/2026.

---

## 1. Mục đích

Đánh giá độ ổn định cấu trúc hai cụm qua 14 cặp snapshot hàng tháng: độ tương đồng nhãn (ARI, NMI), tính bền vững thành viên (Persistence, Migration), ma trận chuyển dịch cụm, độ trôi tâm cụm, biến động universe (Entry/Exit) và cơ chế ngắt chuỗi tại gap. Dùng cùng bốn bảng và hai biểu đồ chuẩn với K-Means Baseline và Ward. Đây là phân cụm độc lập theo tháng rồi đo chẩn đoán temporal, **không phải Dynamic Clustering**; không fit lại, không đọc holdout.

## 2. Dữ liệu và quá trình

Notebook đọc ba CSV phẳng đã được Nhiệm vụ 6 tái lập từ `assignments` và `cluster_profiles` với cùng nhãn aligned xuyên chuỗi, kiểm tra manifest và checksum (fail-closed). Chỉ so sánh cổ phiếu chung giữa hai tháng (`n_common`); Entry và Exit được tách riêng. Migration = 1 − Persistence trên giao universe. Drift dùng tâm cụm gốc thật (`value_from`, `value_to`) theo từng feature.

## 3. Kết quả đạt được

### 9.1–9.4 – Bảng 1: Chỉ số temporal toàn kỳ

| Chỉ số (Metric) | Số cặp quan sát | Trung bình (Mean) | Trung vị (Median) | Nhỏ nhất (Min) | Lớn nhất (Max) |
|---|---:|---:|---:|---:|---:|
| ARI | 14 | 0,7896 | **0,7983** | 0,5758 | 0,9608 |
| NMI | 14 | 0,6690 | **0,6613** | 0,4387 | 0,9113 |
| Persistence (%) | 14 | 98,2756 | **98,5618** | 95,5285 | 99,4863 |
| Migration (%) | 14 | 1,7244 | **1,4382** | 0,5137 | 4,4715 |

ARI thấp nhất là 0,5758 tại 2023-11-30 → 2023-12-29; hai cặp thấp tiếp theo là 2024-07 → 2024-08 (0,6432) và 2024-12 → 2025-01 (0,6672). Persistence thấp nhất là 95,53% (2024-07 → 2024-08).

### 9.5 – Bảng 2: Ma trận chuyển dịch cụm tích lũy (aligned IDs)

| Từ Cụm (From) | Sang Cụm (To) | Tổng số lượt (Count) | Tổng số cơ sở (Denominator) | Tỷ lệ xác suất (Rate %) |
|---|---|---:|---:|---:|
| Cụm 0 | Cụm 0 (Giữ nguyên) | 161 | 199 | 80,9045 |
| Cụm 0 | Cụm 1 (Chuyển cụm) | 38 | 199 | 19,0955 |
| Cụm 1 | Cụm 1 (Giữ nguyên) | 4.574 | 4.606 | 99,3053 |
| Cụm 1 | Cụm 0 (Chuyển cụm) | 32 | 4.606 | 0,6947 |

### 9.6 – Bảng 3: Độ lệch tâm tuyệt đối trung bình giữa hai tháng liền kề (8 feature gốc)

| Đặc trưng | Cụm 0 (Mean \|Delta\|) | Cụm 1 (Mean \|Delta\|) |
|---|---:|---:|
| liquidity_21 (tỷ VNĐ) | 94,1176 | 3,9778 |
| beta_126 | 0,0562 | 0,0493 |
| vol_63 | 0,0283 | 0,0332 |
| mdd_126 | 0,0233 | 0,0153 |
| mom_21 | 0,0587 | 0,0412 |
| mom_63 | 0,0616 | 0,0347 |
| mom_126 | 0,0697 | 0,0416 |
| mom_252 | 0,1075 | 0,0527 |

Drift giữ đơn vị gốc theo từng feature; không cộng các feature khác đơn vị thành một số.

### 9.7 – Bảng 4: Biến động Universe (Entry / Exit)

| Cặp snapshot (From → To) | Số mã chung (n_common) | Số mã mới (Entry) | Số mã rớt (Exit) | Tỷ lệ luân chuyển (%) |
|---|---:|---:|---:|---:|
| 2023-11 → 2023-12 | 140 | 55 | 2 | 40,7143 |
| 2023-12 → 2024-01 | 191 | 5 | 4 | 4,7120 |
| 2024-01 → 2024-02 | 196 | 0 | 0 | 0,0000 |
| 2024-02 → 2024-03 | 196 | 1 | 0 | 0,5102 |
| 2024-03 → 2024-04 | 197 | 17 | 0 | 8,6294 |
| 2024-04 → 2024-05 | 210 | 11 | 4 | 7,1429 |
| 2024-05 → 2024-06 | 221 | 19 | 0 | 8,5973 |
| 2024-06 → 2024-07 | 238 | 9 | 2 | 4,6218 |
| 2024-07 → 2024-08 | 246 | 349 | 1 | 142,2764 |
| 2024-08 → 2024-09 | 591 | 15 | 4 | 3,2149 |
| 2024-09 → 2024-10 | 605 | 3 | 1 | 0,6612 |
| 2024-10 → 2024-11 | 608 | 172 | 0 | 28,2895 |
| 2024-11 → 2024-12 | 584 | 5 | 196 | 34,4178 |
| 2024-12 → 2025-01 | 582 | 7 | 7 | 2,4055 |

Tỷ lệ luân chuyển universe = (Entry + Exit) / `n_common` × 100; mẫu số là `n_common` nên tỷ lệ có thể vượt 100% khi universe mở rộng mạnh. Đây là biến động membership, **không phải portfolio turnover**; Migration chỉ đo trên giao universe.

### 9.8 – Reset Temporal Chain tại Gap

Notebook in kết quả kiểm tra: *PASS GAP RESET: đúng 15 tháng liên tục / 14 cặp; không có liên kết vượt 24/01/2025 vào gap 02/2025–01/2026.* Phép kiểm này xác minh chain của bộ Development hiện tại và không mở holdout.

## 4. Nhận định tài chính và rào chắn học thuật (9.10)

### 4.1 Độ ổn định cấu trúc
Median ARI 0,7983 và NMI 0,6613 cho thấy phân hoạch khá ổn định nhưng không bất biến; ARI > 0,70 ở 11/14 cặp, không cặp nào dưới 0,50. NMI thấp hơn ARI và dao động rộng hơn (0,4387–0,9113).

### 4.2 Persistence và Migration
Persistence median 98,56%, thấp nhất 95,53%: vượt ngưỡng 95% của tiêu chuẩn học thuật; Migration median 1,44%, tối đa 4,47%, thấp hơn ngưỡng 15%. Tỷ lệ giữ cụm gộp theo lượt là 80,90% (Cụm 0, 199 lượt) và 99,31% (Cụm 1, 4.606 lượt); tổng thể bị chi phối bởi nhóm lớn, nên không suy ra hai cụm bền như nhau từ Persistence tổng hợp.

### 4.3 Tác động tiềm tàng và chi phí giao dịch
Migration thấp không đồng nghĩa chi phí giao dịch thấp: Entry + Exit lớn nhất so với `n_common` là 142,28% tại 2024-07 → 2024-08; các cặp khác có luân chuyển cao là 2023-11 → 2023-12 (40,71%), 2024-11 → 2024-12 (34,42%) và 2024-10 → 2024-11 (28,29%). Chi phí và turnover danh mục còn phụ thuộc trọng số, size vốn và quy tắc tái cân bằng ở M3.

### 4.4 Các cặp ARI thấp
ARI thấp nhất 0,5758 tại 2023-11-30 → 2023-12-29 (55 mã vào, `n_common` = 140). Không có dữ liệu VN-Index trong notebook nên không khẳng định cú sốc thị trường là nguyên nhân.

### 4.5 Centroid drift
Drift theo từng feature gốc; Cụm 0 có drift tuyệt đối lớn hơn Cụm 1 ở 7/8 feature (kể cả `liquidity_21`: 94,12 so với 3,98 tỷ), Cụm 1 lớn hơn ở `vol_63` (0,0332 so với 0,0283). Drift thanh khoản tính theo đơn vị tiền tệ nên không dùng riêng để kết luận mức độ ổn định.

### 4.6 Giới hạn
Phân cụm độc lập rồi đo temporal diagnostics không phải Dynamic Clustering; không dùng chỉ số ổn định để chọn mã hay suy diễn lợi nhuận.

## 5. Khung kết luận ba phần

**Phần A – Phán quyết độ ổn định.** Median ARI = 0,7983, NMI = 0,6613; ARI > 0,70 ở 11/14 cặp; ARI thấp nhất 0,5758 tại 2023-11-30 → 2023-12-29; 0 cặp ARI < 0,50. Phân hoạch khá ổn định, không bất biến. Không khẳng định cú sốc thị trường là nguyên nhân vì không có dữ liệu VN-Index.

**Phần B – Persistence/Migration và tác động tiềm tàng.** Median Persistence 98,5618%, Migration 1,4382% trên giao universe. Tỷ lệ giữ cụm gộp: Cụm 0 = 80,9045% (cơ sở 199 lượt), Cụm 1 = 99,3053% (cơ sở 4.606 lượt). Entry + Exit lớn nhất 142,2764% tại 2024-07 → 2024-08. Drift dùng tâm gốc thật theo từng feature.

**Phần C – Bàn giao và giới hạn.** Đủ bốn bảng và hai biểu đồ; đúng 14 cặp, không nối qua gap 02/2025–01/2026. Kết quả mô tả Development, không chứng minh PCA bền hơn phương án khác, không phải Dynamic Clustering, không dùng để chọn mã hoặc suy diễn lợi nhuận.

