# Báo cáo Nhiệm vụ 6: Thực thi PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshot Development (30/11/2023 – 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)
**Notebook:** `M2/notebooks/06_pca_kmeans.ipynb` | **Config:** `configs/experiments/m2_task6_pca.json` | **Artifact:** `M2/artifacts/m2-task6-pca-kmeans-v1/` | **Model:** `M2/models/pca_kmeans/`

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Nhiệm vụ 6 hoàn tất bộ kết quả PCA + K-Means với Global K = 2 trên **15/15 snapshot Development** (universe 142–780 mã, 0 snapshot bị bỏ qua). Notebook kiểm chứng trực tiếp 15 model đã lưu và bộ artifact `m2-task6-pca-kmeans-v1` (khớp config, checksum), không fit lại: **5.615 nhãn khớp dự đoán từ model, 30 hồ sơ cụm trên 8 feature gốc**, điểm số PC1–PC4, 14 cặp temporal aligned. PCA giữ cố định **4 thành phần**, đúng bằng số thành phần tối thiểu cần để mọi snapshot đạt ≥ 90% phương sai; phương sai giữ lại có median **96,86%**, thấp nhất 93,64%, cao nhất 99,84%.

---

## 1. Mục đích

Thực thi phương án C của M2 (PCA + K-Means) trên toàn bộ Development: giữ 8 feature, Global K = 2, Robust Scaling riêng từng snapshot, không impute/clipping, không đọc holdout, không đánh giá danh mục. PCA chỉ thuộc phương án này và là comparator độc lập, không thay đổi tiền xử lý của K-Means baseline hoặc Ward. Pipeline: **Robust Scaling → PCA → K-Means**.

## 2. Đầu vào và cấu hình

| Hạng mục | Giá trị |
|---|---|
| Dữ liệu | `CAFEF_C8_COMPLETE_ONLY_V1`, dữ liệu thực, market-only |
| Development | 15 snapshot: 2023-11-30 đến 2025-01-24 |
| Universe | `market_feature_ready_v2`, tối thiểu 120 mã, lọc độc lập theo snapshot |
| Feature (8) | `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21` |
| Missing/outlier | Fail-closed; không impute; không winsorize/clipping |
| Scaling | Robust Scaling `(x − median) / IQR`, fit riêng mỗi snapshot |
| Quy tắc PCA | Số chiều cố định nhỏ nhất để **mọi** snapshot đạt cumulative explained variance ≥ 90%; kết quả `n_components = 4`; PCA fit trên chính snapshot (`fit_scope = supplied_snapshot_only`) |
| K-Means | Global K = 2 (khóa từ Task 3); `seed = 42`, `n_init = 10`, `max_iter = 300` |
| Model nguồn | `experiment-20261003T113748Z-acb3a2e7`; bộ kiểm chứng/xuất lại lưu tại `m2-task6-pca-kmeans-v1` |

## 3. Quá trình thực hiện theo kế hoạch

**6.1–6.2 – Lấy dữ liệu và kiểm tra.** Notebook nạp config, kiểm tra checksum, 15 model đã lưu và dữ liệu C8 Development; đối chiếu bảng snapshot dưới đây. Mọi snapshot đều `ready` và đạt ngưỡng 120 mã.

| Snapshot | N | Snapshot | N | Snapshot | N |
|---|---:|---|---:|---|---:|
| 2023-11-30 | 142 | 2024-05-31 | 221 | 2024-10-31 | 608 |
| 2023-12-29 | 195 | 2024-06-28 | 240 | 2024-11-29 | 780 |
| 2024-01-31 | 196 | 2024-07-31 | 247 | 2024-12-31 | 589 |
| 2024-02-29 | 196 | 2024-08-30 | 595 | 2025-01-24 | 589 |
| 2024-03-29 | 197 | 2024-09-30 | 606 | | |
| 2024-04-26 | 214 | | | | |

**6.3 – Robust Scaling theo snapshot.** Tám feature được scale bằng median và IQR của chính snapshot; tham số scaler lưu trong từng model và trong bảng `scaler_parameters`. Bước này cần thiết vì `liquidity_21` có đơn vị và biên độ lớn hơn các feature khác.

**6.4–6.5 – Áp dụng và lưu thông tin PCA.** PCA metadata nằm ở `model['scaler']['_reduction']`; notebook chiếu dữ liệu đúng theo mean và loadings đã fit. Explained variance từng thành phần, cumulative và số chiều tối thiểu đạt 90% theo snapshot:

| Snapshot | Số chiều tối thiểu đạt 90% | PC1 | PC2 | PC3 | PC4 | Cumulative (4 PC) |
|---|---:|---:|---:|---:|---:|---:|
| 2023-11-30 | 2 | 79,49% | 10,56% | 5,99% | 1,35% | 97,39% |
| 2023-12-29 | 3 | 79,90% | 9,10% | 4,54% | 3,32% | 96,86% |
| 2024-01-31 | 3 | 70,83% | 14,33% | 6,02% | 4,02% | 95,20% |
| 2024-02-29 | 3 | 75,73% | 11,43% | 4,92% | 3,16% | 95,25% |
| 2024-03-29 | **4** | 62,05% | 20,29% | 7,36% | 3,93% | 93,64% |
| 2024-04-26 | 3 | 68,47% | 16,95% | 7,38% | 3,45% | 96,25% |
| 2024-05-31 | 3 | 67,42% | 16,80% | 7,21% | 3,67% | 95,10% |
| 2024-06-28 | 3 | 70,11% | 14,55% | 6,91% | 4,00% | 95,57% |
| 2024-07-31 | 3 | 60,80% | 20,79% | 8,53% | 4,25% | 94,37% |
| 2024-08-30 | 2 | 87,08% | 12,07% | 0,34% | 0,22% | 99,70% |
| 2024-09-30 | 1 | 98,98% | 0,45% | 0,21% | 0,16% | 99,80% |
| 2024-10-31 | 1 | 99,05% | 0,45% | 0,18% | 0,13% | 99,80% |
| 2024-11-29 | 1 | 99,18% | 0,43% | 0,14% | 0,09% | 99,84% |
| 2024-12-31 | 1 | 95,67% | 2,32% | 0,77% | 0,52% | 99,27% |
| 2025-01-24 | 1 | 94,52% | 3,19% | 0,72% | 0,66% | 99,09% |

| Thống kê cumulative (4 PC) | Giá trị |
|---|---:|
| Thấp nhất | 93,64% |
| Trung vị | 96,86% |
| Trung bình | 97,14% |
| Cao nhất | 99,84% |

Median explained variance từng thành phần: PC1 79,49% – PC2 11,43% – PC3 4,92% – PC4 3,16%. Số chiều cố định 4 là giá trị lớn nhất của cột "số chiều tối thiểu" (xảy ra tại 2024-03-29, nơi 3 PC đầu chỉ đạt 89,71%), nên một số chiều chung cho mọi tháng không thể nhỏ hơn 4; số chiều không được đổi theo từng tháng. Loading 4 × 8 của từng snapshot được lưu trong model và bảng loadings; ở các snapshot hiển thị trong notebook (2023-11 đến 2024-06), hệ số tải của PC1 lên `liquidity_21` nằm trong khoảng 0,97–1,00.

**6.6 – Chạy K-Means với Global K trong không gian PCA.** K-Means chạy trên vector PCA 4 chiều với k = 2; không chọn lại K sau PCA. Notebook kiểm tra nhãn gán gần centroid nhất và inertia khớp với model.

**6.7 – Lưu cluster assignment.** `assignments` gồm `security_id`, `snapshot_date`, `raw_cluster_id`, `aligned_cluster_id` (5.615 dòng); nhãn aligned được nối bằng Hungarian alignment xuyên chuỗi từ tháng đầu, tách biệt với nhãn raw. Điểm PCA PC1–PC4 từng mã lưu trong `pca_scores`.

**6.8 – Centroid trong không gian PCA.** Mỗi model lưu 2 centroid × 4 tọa độ PCA, dùng để kiểm tra mô hình và tái lập K-Means.

**6.9 – Cluster profile trên 8 feature gốc.** `cluster_profiles` (13 cột phẳng, 30 dòng = 2 cụm × 15 snapshot) lưu `size`, `size_ratio` và **trung bình 8 feature gốc của thành viên thực tế** (không dùng inverse transform PCA bị cắt chiều thay cho dữ liệu gốc). Quy mô hai cụm (cụm 0 / cụm 1): 9/133, 16/179, 17/179, 17/179, 15/182, 14/200, 15/206, 11/229, 17/230, 21/574, 16/590, 13/595, 8/772, 11/578, 21/568.

**6.10 – Quality metrics.** Diagnostics lưu Silhouette, Davies–Bouldin, Calinski–Harabasz, inertia và balance theo snapshot/k; metric k = 2 đọc riêng 15 dòng (kết quả ở Task 7). Các metric đo trong không gian PCA 4 chiều dùng để phân cụm.

**6.11 – Lặp lại toàn bộ Development.** Chuỗi hoàn tất cho 15 snapshot: 15 model, 30 profile, 105 diagnostic rows (15 snapshot × k = 2…8), 14 cặp aligned cho temporal inputs.

**6.12 – Lưu artifact.** Assignments, PC1–PC4 scores, loadings, PCA diagnostics, scaler parameters, cluster profiles 13 cột, diagnostics, ba temporal inputs (`temporal_stability`, `transition_matrices`, `centroid_drift`), manifest kiểm tra checksum toàn bộ bộ xuất và 15 model ở `M2/models/pca_kmeans/`. Notebook in kết quả kiểm chứng: *PASS: 15 model, 5.615 assignments, 30 profiles, scores PC1–PC4, 14 cặp aligned*.

## 4. Kết quả đạt được

| Nội dung | Kết quả |
|---|---|
| Snapshot đã xử lý / bị bỏ qua | 15/15 / 0 |
| Số cổ phiếu mỗi snapshot | 142–780 |
| Nhãn cụm | 5.615 (khớp dự đoán từ model) |
| Model PCA + K-Means K = 2 đã lưu | 15 |
| Hồ sơ cụm | 30 (15 tháng × 2 cụm) |
| Diagnostics | 105 dòng (15 snapshot × k = 2…8) |
| Cặp tháng liên tiếp cho Task 9 | 14 |
| Số chiều PCA | 4 (cố định) |
| Phương sai PCA(4) giữ lại | median 96,86%; thấp nhất 93,64%; cao nhất 99,84% |

## 5. Phân tích

PCA đưa 8 feature xuống 4 thành phần trực giao mà vẫn giữ trên 93% phương sai ở mọi snapshot. Từ 2024-08, PC1 giải thích 87–99% phương sai nên cấu trúc phương sai trong không gian PCA bị chi phối bởi một trục; ở các snapshot đầu chuỗi (2023-11 đến 2024-06), trục này chủ yếu tải lên `liquidity_21`. Kết quả hình học của k = 2 rõ nhưng một cụm chỉ có 8–21 mã (chi tiết ở Task 7 và 8). Bộ kết quả chỉ mô tả cấu trúc market-only trong Development, không phải dynamic clustering hay bằng chứng sinh lợi.

## 6. Tổng hợp nhận xét

**A – Thực thi và kiểm chứng:** 15/15 snapshot; universe 142–780 mã; 5.615 nhãn khớp model; 30 profile trên 8 feature gốc; Global K = 2, Robust Scaling độc lập, seed = 42, n_init = 10, max_iter = 300.
**B – Quy tắc PCA:** số chiều cố định 4 là max của số chiều tối thiểu đạt 90% trên từng snapshot; phương sai giữ lại median 96,86%, min 93,64%, max 99,84%; không đổi số chiều theo tháng và không dùng holdout.
**C – Bàn giao Nhiệm vụ 7–9:** assignments, PC1–PC4 scores, loadings, PCA diagnostics, scaler parameters, cluster profiles 13 cột, diagnostics và ba temporal inputs aligned; manifest kiểm tra checksum toàn bộ bộ xuất.

**Bàn giao:** notebook `06_pca_kmeans.ipynb`; `M2/models/pca_kmeans/`; `M2/artifacts/m2-task6-pca-kmeans-v1/`; báo cáo này.
