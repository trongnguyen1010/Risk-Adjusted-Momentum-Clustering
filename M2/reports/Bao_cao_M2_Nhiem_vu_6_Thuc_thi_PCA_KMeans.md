# Báo cáo Nhiệm vụ 6: Thực thi PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshot Development (30/11/2023 – 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)
**Notebook:** `M2/notebooks/06_pca_kmeans.ipynb` | **Config:** `configs/experiments/m2_task6_pca.json` | **Artifact:** `M2/artifacts/m2-task6-pca-kmeans-v1/` | **Model:** `M2/models/pca_kmeans/`

**TÓM TẮT KẾT QUẢ:**
Nhiệm vụ 6 đã chạy xong pipeline Robust Scaling → PCA → K-Means với Global K = 2 trên **15/15 snapshot Development, 0 snapshot bị bỏ qua**. PCA đưa 8 đặc trưng xuống 4 thành phần trực giao, giữ **median 96,86% phương sai** (thấp nhất 93,64%, cao hơn ngưỡng 90% của kế hoạch). Run lưu 15 model JSON, 5.615 lượt gán nhãn, 30 hồ sơ cụm và 105 dòng diagnostics (k = 2…8), đủ làm đầu vào cho Nhiệm vụ 7, 8, 9. Hai hạng mục còn thiếu so với checklist kế hoạch: PCA score theo từng mã và bảng `pca_diagnostics` tổng hợp. Ngoài ra, quy tắc "số component tối thiểu đạt 90%" nêu trong notebook chưa được chứng minh (xem mục 6).

---

## 1. Mục tiêu

- Tạo kết quả phân cụm PCA + K-Means chính thức trên toàn bộ Development, và kiểm tra việc giảm chiều trước K-Means có tạo được cấu trúc cụm rõ, diễn giải được và theo dõi được theo thời gian hay không.
- PCA chỉ thuộc phương án C (không áp dụng cho K-Means baseline hay Ward), nên PCA là comparator độc lập và không thay đổi tiền xử lý của hai phương án còn lại.
- Chuẩn bị đầy đủ artifact để Nhiệm vụ 7 (chất lượng cụm), 8 (hồ sơ cụm), 9 (độ ổn định) và 10 (so sánh phương án) dùng mà không phải huấn luyện lại.

## 2. Đầu vào và cấu hình run

| Hạng mục | Giá trị |
|---|---|
| Run | `experiment-20260930T184053Z-dd239f33`; `status: complete` |
| Dữ liệu | `CAFEF_C8_COMPLETE_ONLY_V1`, dữ liệu thực, market-only |
| Development | 15 snapshot, 2023-11-30 đến 2025-01-24 |
| Universe | `market_feature_ready_v2`, tối thiểu 120 mã, lọc độc lập theo snapshot |
| Feature (8) | `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21` |
| Missing/outlier | Fail-closed, không impute; `winsor_quantile = 0`, `clipping = false` |
| Scaling | Robust Scaling `(x − median) / IQR`, fit riêng mỗi snapshot |
| PCA | `pca.n_components = 4` (ghi explicit trong config) |
| K-Means | Global K = 2 (khóa từ Task 3); `seed = 42`, `n_init = 10`, `max_iter = 300` |
| Portfolio / holdout | Portfolio tắt; không dùng holdout |

> Trạng thái nghiên cứu: manifest vẫn ghi `real_pilot_accepted: false`. Báo cáo này là bằng chứng Development/pilot, không phải kết quả holdout hay khuyến nghị đầu tư.

## 3. Quá trình thực hiện

Notebook 06 không tự huấn luyện mà gọi runner: (1) đọc config và in thuật toán, danh sách feature, cấu hình PCA; (2) gọi `experiment(data_run, config, root)` để chạy toàn bộ 15 snapshot và ghi artifact; (3) mở một file model (`2023-11-30.json`) để xem `n_components` và explained variance; (4) kiểm tra `assignments.csv` / `profiles.csv` đã được tạo.

| Phần | Nội dung thực hiện | Kết quả |
|---|---|---|
| 6.1–6.2 Dữ liệu và kiểm tra | Đọc 15 snapshot, cùng eligibility rule và 8 feature với các phương án khác; mỗi cross-section ≥ 120 mã, đủ 8 feature | 15/15 chạy, 0 skipped; số mã khớp số eligible của Task 3 (142–780 mã) |
| 6.3 Robust Scaling | Scale bằng median và IQR của chính snapshot; lưu center/lower/upper/scale trong từng model | Cần thiết vì `liquidity_21` có đơn vị và biên độ lớn hơn các feature khác |
| 6.4–6.5 PCA | 8 chiều → 4 thành phần; lưu `n_components`, `input_center`, loading 4 × 8, 4 explained-variance ratios | Xem mục 4.1 |
| 6.6 K-Means | Chạy trên vector PCA 4 chiều với k = 2; không chọn lại K sau PCA; diagnostics vẫn thử k = 2…8 | 15 model K-Means |
| 6.7–6.8 Assignment, centroid | `assignments.csv/jsonl` (`security_id`, `snapshot_date`, `raw_cluster_id`, `aligned_cluster_id`); 2 centroid × 4 tọa độ PCA mỗi model | 5.615 dòng |
| 6.9 Profile gốc | Centroid cụm trong không gian 8 feature gốc để diễn giải cùng hệ feature với K-Means và Ward | 30 profile (2 cụm × 15) |
| 6.10–6.11 Metric, lặp | Silhouette, DB, CH, inertia, balance theo snapshot/k | 105 dòng diagnostics |
| 6.12 Artifact | assignments, profiles, diagnostics, stability, transitions, manifest, event log, source snapshot, 15 model | Xem mục 5 |

## 4. Kết quả đạt được

### 4.1 Phương sai PCA giải thích

| Thống kê (15 snapshot) | Cumulative explained variance (4 PC) |
|---|---:|
| Thấp nhất | 93,64% |
| Trung vị | 96,86% |
| Trung bình | 97,14% |
| Cao nhất | 99,84% |

Median explained variance từng thành phần: **PC1 79,49% – PC2 11,43% – PC3 4,92% – PC4 3,16%**. PC1 một mình chiếm khoảng bốn phần năm biến thiên, cho thấy các feature sau scaling có chung một trục biến thiên chi phối.

### 4.2 Kết quả chạy

| Nội dung | Kết quả |
|---|---|
| Snapshot đã xử lý / bị bỏ qua | 15/15 / 0 |
| Số mã mỗi snapshot | 142–780 |
| Lượt gán nhãn | 5.615 |
| Model PCA + K-Means đã lưu | 15 |
| Hồ sơ cụm | 30 (15 tháng × 2 cụm) |
| Diagnostics | 105 dòng (15 snapshot × k = 2…8) |
| Cặp tháng liên tiếp cho Task 9 | 14 |

### 4.3 Quy mô hai cụm theo snapshot (k = 2)

| Snapshot | N | Cụm 0 | Cụm 1 | Snapshot | N | Cụm 0 | Cụm 1 |
|---|---:|---:|---:|---|---:|---:|---:|
| 2023-11-30 | 142 | 9 | 133 | 2024-08-30 | 595 | 21 | 574 |
| 2023-12-29 | 195 | 16 | 179 | 2024-09-30 | 606 | 16 | 590 |
| 2024-01-31 | 196 | 17 | 179 | 2024-10-31 | 608 | 13 | 595 |
| 2024-02-29 | 196 | 17 | 179 | 2024-11-29 | 780 | 8 | 772 |
| 2024-03-29 | 197 | 15 | 182 | 2024-12-31 | 589 | 11 | 578 |
| 2024-04-26 | 214 | 14 | 200 | 2025-01-24 | 589 | 21 | 568 |
| 2024-05-31 | 221 | 15 | 206 | | | | |
| 2024-06-28 | 240 | 11 | 229 | | | | |
| 2024-07-31 | 247 | 17 | 230 | | | | |

Cụm 0 luôn là nhóm nhỏ (8–21 mã), cụm 1 chứa phần lớn universe.

### 4.4 Chất lượng k = 2 (trung vị, chi tiết ở Task 7)
Silhouette 0,7717; Davies–Bouldin 0,5155; Calinski–Harabasz 361,53; balance 6,77%.

## 5. Phân tích

- **Giảm chiều hiệu quả:** 4 thành phần giữ ≥ 93,64% phương sai ở mọi snapshot, nên PCA loại được phần thông tin trùng lặp giữa các feature động lượng/rủi ro mà không mất đáng kể thông tin. Các thành phần trực giao nên K-Means chạy trên không gian không còn tương quan tuyến tính giữa các trục.
- **Cấu trúc cụm rõ nhưng lệch:** k = 2 cho cấu trúc hình học tách biệt, song cụm nhỏ chỉ 8–21 mã. Mô hình chủ yếu cô lập một nhóm nhỏ khỏi phần lớn universe, nên Silhouette cao không đồng nghĩa hai nhóm có quy mô hay ý nghĩa kinh tế cân bằng.
- **Quy mô universe do dữ liệu, không do PCA:** universe tăng từ 142 lên 780 mã tùy snapshot vì số mã eligible thay đổi; nhánh PCA không đổi rổ so với Task 3.
- **Ranh giới:** kết quả là bằng chứng mô tả cấu trúc Development; không dùng để khẳng định khả năng sinh lợi, chọn mã hay phân bổ vốn.

## 6. Hạn chế và lưu ý kiểm tra

1. **Thiếu PCA score theo từng mã.** Cột `pca_x`, `pca_y` có trong schema nhưng rỗng ở toàn bộ assignment; kế hoạch yêu cầu PCA-transformed data. Các model đã lưu đủ thông tin để tái tính nhưng score chưa được xuất trực tiếp.
2. **Thiếu bảng `pca_diagnostics`** (kế hoạch nêu `pca_diagnostics.jsonl`) tổng hợp component/variance theo snapshot; hiện chỉ đọc được từ từng model JSON.
3. **Quy tắc chọn số component chưa được chứng minh.** Ô Mục đích trong notebook nêu "số component tối thiểu sao cho cumulative explained variance ≥ 90%", còn config cố định `n_components = 4`. Tổng median của ba PC đầu là 79,49 + 11,43 + 4,92 = 95,84% (cộng median từng thành phần chỉ là xấp xỉ), nghĩa là 3 thành phần có thể đã đạt 90% ở nhiều snapshot. Cần kiểm tra cumulative EVR của 3 PC theo từng snapshot; nếu muốn giữ 4 thì nên ghi rõ đây là lựa chọn cố định chứ không phải "tối thiểu".
4. **Notebook không lưu output.** Số liệu trong báo cáo lấy từ artifact của run và báo cáo run; ô kiểm tra explained variance chỉ in kết quả khi file model có khóa `pca_explained_variance_ratio`, nếu tên khóa khác sẽ không in gì và không báo lỗi.
5. Đường dẫn trong notebook (vòng lặp `os.chdir('..')` tới thư mục `m2-clustering-experiment`) phụ thuộc cấu trúc thư mục máy cục bộ.

## 7. Tổng hợp nhận xét

Nhiệm vụ 6 đã hoàn thành phần thực thi PCA + K-Means trên toàn bộ Development và lưu các artifact cốt lõi theo snapshot. PCA giữ được phần lớn biến thiên và K-Means cho cấu trúc hai cụm rõ nhưng mất cân bằng quy mô. Cần bổ sung PCA score cấp từng mã, bảng `pca_diagnostics` và làm rõ quy tắc chọn số component trước khi yêu cầu tái lập hoặc trực quan hóa không gian PCA ở mức đầy đủ.

**Bàn giao:** notebook `06_pca_kmeans.ipynb`; `M2/models/pca_kmeans/` (15 model JSON); `M2/artifacts/m2-task6-pca-kmeans-v1/` (assignments, profiles, diagnostics, stability, transitions, manifest); báo cáo này.
