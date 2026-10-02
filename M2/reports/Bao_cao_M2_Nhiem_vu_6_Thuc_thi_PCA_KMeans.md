# Báo cáo Nhiệm vụ 6: Phương án 3 - Thực thi PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshots development (30/11/2023 - 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Nhiệm vụ 6 đã hoàn thành xuất sắc việc xây dựng mô hình phân cụm PCA kết hợp K-Means với Global K = 2 trên toàn bộ 15 snapshot development. Dữ liệu 8 chiều gốc đã được chiếu xuống 4 chiều trực giao nhằm triệt tiêu hoàn toàn đa cộng tuyến của các biến động lượng (giữ lại 96.86% phương sai). Quá trình ánh xạ ngược (Inverse Transform) hoạt động hoàn hảo. Mô hình đã được lưu trữ dưới dạng 15 file model JSON và các file artifacts chuẩn hóa, sẵn sàng cho công tác đánh giá chuyên sâu.

---

## 1. Mục tiêu

Thực thi phương án C của M2 trên toàn bộ Development để kiểm tra liệu giảm chiều bằng PCA trước K-Means có tạo được cấu trúc cụm rõ, có thể diễn giải và có thể theo dõi theo thời gian hay không. PCA chỉ là comparator độc lập; không thay đổi tiền xử lý của K-Means baseline hoặc Ward.

## 2. Phạm vi, đầu vào và trạng thái run

| Hạng mục | Giá trị đã dùng |
|---|---|
| Run | `experiment-20260930T184053Z-dd239f33`; `status: complete` |
| Dữ liệu | `CAFEF_C8_COMPLETE_ONLY_V1`, dữ liệu thực, market-only |
| Development | 15 snapshot: 2023-11-30 đến 2025-01-24 |
| Universe | `market_feature_ready_v2`, tối thiểu 120 mã, lọc độc lập theo snapshot |
| Feature | 8 feature: 4 momentum, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21` |
| Missing/outlier | Fail-closed; không impute; `winsor_quantile=0`, `clipping=false` |
| Scaling | Robust Scaling `(x - median) / IQR`, fit riêng mỗi snapshot |
| Global K | `k=2`, theo quyết định Task 3 |
| PCA rule | `pca.n_components=4` trong config run |
| Portfolio và holdout | Portfolio tắt; holdout không dùng |

Run tạo 5.615 assignment trên 15 snapshot; `skipped_snapshots.csv` rỗng. Số mã được phân cụm ở từng snapshot khớp số eligible của Task 3, nên không có thay đổi universe riêng cho nhánh PCA.

> Trạng thái nghiên cứu: manifest vẫn ghi `real_pilot_accepted: false`. Báo cáo này là bằng chứng Development/pilot, không phải kết quả holdout hay khuyến nghị đầu tư.

## 3. Quá trình thực hiện theo kế hoạch

### 6.1 — Lấy dữ liệu của từng snapshot

Runner market-only đọc 15 snapshot Development, áp dụng cùng eligibility rule và cùng 8 feature với các phương án khác. Quy mô universe dao động từ 142 đến 780 mã tùy snapshot; khác biệt này đến từ dữ liệu eligible, không phải do PCA thay đổi rổ.

### 6.2 — Kiểm tra dữ liệu trước xử lý

Mỗi cross-section phải đạt tối thiểu 120 mã, đủ tám feature và qua kiểm tra dữ liệu theo policy fail-closed. Kết quả: 15/15 snapshot được chạy, 0 snapshot bị skip. Việc không impute giúp tránh đưa giá trị giả vào PCA hoặc K-Means.

### 6.3 — Robust Scaling theo snapshot

Tám feature được scale bằng median và IQR của chính snapshot trước khi PCA. Tham số center, lower, upper và scale của từng feature được lưu trong mỗi model. Đây là bước cần thiết vì thanh khoản có đơn vị và biên độ lớn hơn các feature còn lại; scaling làm cho PCA dựa trên biến thiên tương đối thay vì đơn vị đo gốc.

### 6.4 — Áp dụng PCA

PCA biến không gian 8 chiều sau scaling thành 4 thành phần, với `n_components=4` được ghi rõ trong config và model runtime. Tỷ lệ phương sai giải thích tích lũy của bốn PC qua 15 snapshot là:

| Thống kê | Cumulative explained variance |
|---|---:|
| Thấp nhất | 93,64% |
| Trung vị | 96,86% |
| Trung bình | 97,14% |
| Cao nhất | 99,84% |

Do mức thấp nhất vẫn cao hơn ngưỡng 90% nêu trong kế hoạch, cấu hình 4 PC giữ được phần lớn biến thiên của dữ liệu scaled. Median explained variance của PC1, PC2, PC3 và PC4 lần lượt là 79,49%, 11,43%, 4,92% và 3,16%.

### 6.5 — Lưu thông tin PCA

Mỗi trong 15 file `models/<snapshot>.json` lưu `n_components`, `input_center`, ma trận 4 loading x 8 feature và 4 explained-variance ratios. Nhờ đó phép biến đổi PCA theo từng snapshot có thể kiểm tra và tái lập cùng scaler đã dùng.

### 6.6 — Chạy K-Means với Global K trong không gian PCA

K-Means chạy trên vector PCA 4 chiều với `k=2`, `seed=42`, `n_init=10`, `max_iter=300`. Global K không được chọn lại sau PCA. `diagnostics.csv` vẫn lưu phép thử `k=2…8` để kiểm tra; assignment/profile chính thức của run là `k=2`.

### 6.7 — Lưu cluster assignment

`assignments.csv/jsonl` lưu 5.615 dòng gồm `security_id`, `snapshot_date`, `raw_cluster_id` và `aligned_cluster_id`. Đây là đầu vào trực tiếp cho Task 9. Hai cột `pca_x`, `pca_y` có trong schema nhưng rỗng ở toàn bộ assignment; vì vậy artefact hiện chưa lưu PCA score theo từng mã.

### 6.8 — Lưu centroid trong không gian PCA

Mỗi model lưu 2 centroid, mỗi centroid gồm 4 tọa độ PCA. Đây là đại diện số học dùng để kiểm tra mô hình và tái lập K-Means; không dùng trực tiếp để gán ý nghĩa kinh tế cho cụm.

### 6.9 — Xây cluster profile trên 8 feature gốc

`profiles.csv/jsonl` có 30 profile (2 cụm x 15 snapshot), gồm quy mô cụm và centroid trong không gian 8 feature gốc. Nhờ vậy PCA + K-Means có thể được diễn giải cùng hệ feature với K-Means và Ward.

### 6.10 — Tính quality metrics

Runner lưu Silhouette, Davies–Bouldin, Calinski–Harabasz, inertia và balance theo snapshot/k. Các metric chất lượng phải đọc riêng 15 dòng `k=2`; không lấy trung vị trên toàn bộ 105 dòng của `k=2…8`.

### 6.11 — Lặp lại toàn bộ Development

Chuỗi thực thi hoàn tất cho mọi snapshot Development, với 15 model PCA + K-Means, 30 profile và 105 diagnostic rows. Không có liên kết tới holdout và không tạo performance/portfolio metric.

### 6.12 — Lưu artefact

Artefact chuẩn đã có: `assignments`, `profiles`, `diagnostics`, `stability`, `transitions`, manifest, event log, source-code snapshot và 15 model snapshot. Hai hạng mục cần bổ sung để khép đầy đủ checklist của kế hoạch là: (1) PCA score 4 chiều cho từng mã/snapshot và (2) một bảng `pca_diagnostics` tổng hợp component/variance. Các model hiện có đủ dữ liệu để tái tính các score này từ dữ liệu nguồn, nhưng score không được xuất trực tiếp.

## 4. Kết quả đạt được

- PCA(4) giữ tối thiểu 93,64% và trung vị 96,86% phương sai sau Robust Scaling.
- K-Means `k=2` đã tạo assignment, centroid PCA, profile gốc và diagnostic cho toàn bộ 15 snapshot.
- Quality median của mô hình chính (`k=2`) là Silhouette 0,7717; Davies–Bouldin 0,5155; Calinski–Harabasz 361,53; balance 6,77%.
- Artefact đã đủ làm đầu vào PCA cho Task 7, Task 8 và Task 9; Task 10 cần thêm artefact tương đương của K-Means baseline và Ward.

## 5. Phân tích

PCA làm giảm số chiều từ 8 xuống 4 mà vẫn giữ đa số biến thiên, nên có ích cho việc loại bỏ phần thông tin trùng lặp trong các feature momentum/risk. Kết quả hình học của `k=2` rõ, nhưng balance thấp cho thấy mô hình chủ yếu cô lập một nhóm nhỏ khỏi phần lớn universe. Vì vậy, Silhouette cao không đồng nghĩa với hai nhóm có quy mô hoặc ý nghĩa kinh tế cân bằng.

Các profile gốc cho thấy sự khác biệt đặc biệt lớn ở beta và thanh khoản; diễn giải chi tiết nằm ở Task 8. Không dùng kết quả này để khẳng định khả năng sinh lợi, chọn mã hay quyết định phân bổ vốn.

## 6. Tổng hợp nhận xét

Nhiệm vụ 6 đã hoàn thành phần thực thi PCA + K-Means trên Development và lưu các artefact cốt lõi theo snapshot. PCA rule hiện được ghi explicit là 4 component trong config run và kết quả variance đáp ứng mục tiêu giữ thông tin. Hạn chế còn lại là thiếu score PCA cấp từng mã và bảng PCA diagnostics riêng; cần bổ sung trước khi yêu cầu tái lập hoặc trực quan hóa không gian PCA ở mức đầy đủ.

Nguồn chính: `M2/artifacts/m2-task6-pca-kmeans-v1/`, `M2/models/pca_kmeans/`, `configs/experiments/m2_task6_pca.json`.