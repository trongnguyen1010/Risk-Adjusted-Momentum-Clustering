# Báo cáo Nhiệm vụ 7: Đánh giá Chất lượng Cụm – PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshot Development (30/11/2023 – 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)
**Nguồn:** `M2/artifacts/m2-task6-pca-kmeans-v1/diagnostics.csv` | **Notebook:** `M2/notebooks/07_cluster_quality_evaluation_pca_kmeans.ipynb` | **Artifact xuất ra:** `M2/artifacts/m2-evaluation-pca-kmeans/quality_summary.csv`

**TÓM TẮT KẾT QUẢ:**
Tại Global K = 2, PCA + K-Means đạt chất lượng hình học nội bộ tốt: median Silhouette **0,7717** (vượt ngưỡng xuất sắc 0,7; 13/15 tháng > 0,7, không tháng nào dưới 0,5), median Davies–Bouldin **0,5155**. Điểm cần thận trọng là Cluster Balance: median **0,0677** nhưng **7/15 tháng thấp hơn ngưỡng cảnh báo 0,05**, cụm nhỏ chỉ có 8–21 mã. Chất lượng chia thành hai giai đoạn rõ rệt: Silhouette trung bình ~0,73 khi universe 142–247 mã và ~0,92 khi universe 589–780 mã (từ 08/2024), đồng thời balance giảm mạnh. Kết quả mô tả cấu trúc "một nhóm đại trà + một nhóm cực đoan nhỏ", không phải hai chế độ thị trường cân bằng.

---

## 1. Mục tiêu

- Đánh giá chất lượng hình học và độ tách biệt của cụm PCA + K-Means tại **K = 2** (đã khóa từ Nhiệm vụ 3) qua 15 snapshot Development bằng 5 chỉ số nội bộ: Silhouette, Davies–Bouldin (DB), Calinski–Harabasz (CH), Inertia, Cluster Balance.
- Theo dõi biến thiên theo thời gian, nhận diện giai đoạn chất lượng thay đổi mạnh và hiện tượng phân mảnh (fragmentation / outlier cluster).
- Giữ cùng cấu trúc bảng, biểu đồ và schema `quality_summary.csv` với hai phương án còn lại (K-Means Baseline, Ward) để Nhiệm vụ 10 có thể so sánh.
- Tuân thủ ranh giới M2: không dùng return, Sharpe, ROI hay holdout để đánh giá chất lượng cụm.

## 2. Dữ liệu và quá trình thực hiện

| Bước | Thực hiện |
|---|---|
| 1. Đọc dữ liệu | `pandas` đọc `diagnostics.csv` của Task 6 (105 dòng = 15 snapshot × 7 giá trị k) |
| 2. Lọc K = 2 | Giữ 15 dòng `k == 2`, chuẩn hóa `snapshot_date`, sắp xếp theo thời gian. Notebook xác nhận: *"Đã nạp 15 snapshots cho K=2"* |
| 3. Bảng 1 | Tính mean, median, min, max cho 5 chỉ số; xuất `quality_summary.csv` (7 cột: `metric`, `n_total`, `n_available`, `mean`, `median`, `minimum`, `maximum`) |
| 4. Bảng 2 | Hiển thị chi tiết 15 snapshot × 5 chỉ số |
| 5. Biểu đồ | 5 biểu đồ đường 7.1–7.5, đường Median nét đứt đỏ; biểu đồ 7.5 thêm ngưỡng 0,05 |
| 6. Nhận định | Diễn giải kinh tế và ranh giới phương pháp luận (mục 5–6 dưới đây) |

Notebook chỉ đọc diagnostics đã có, **không huấn luyện lại mô hình**. Các chỉ số được tính ở Task 6 trên không gian dữ liệu dùng để fit K-Means (vector PCA 4 chiều sau Robust Scaling); vì vậy khi so với K-Means/Ward (không gian 8 chiều) ở Task 10 cần lưu ý hai phương án không đo trên cùng một không gian.

**Quy ước đọc chỉ số**

| Chỉ số | Hướng tốt | Ghi chú |
|---|---|---|
| Silhouette | Cao hơn | Ngưỡng chấp nhận > 0,5; xuất sắc > 0,7 |
| Davies–Bouldin | Thấp hơn | Cụm gọn và cách xa nhau |
| Calinski–Harabasz | Cao hơn | Chỉ so trong cùng snapshot/setting |
| Inertia | Không xếp hạng theo thời gian | Phụ thuộc số quan sát N và thang dữ liệu |
| Cluster Balance | Gần 1 hơn | `min_size / max_size`; < 0,05 là ngưỡng cảnh báo phân mảnh |

## 3. Kết quả đạt được

### Bảng 1 – Tóm tắt thống kê chất lượng K = 2

| Chỉ số | n_total | n_available | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| Silhouette | 15 | 15 | 0,8044 | **0,7717** | 0,6595 | 0,9512 |
| Davies–Bouldin | 15 | 15 | 0,4990 | **0,5155** | 0,3550 | 0,7167 |
| Calinski–Harabasz | 15 | 15 | 709,19 | **361,53** | 176,31 | 2.065,15 |
| Inertia | 15 | 15 | 53.212,33 | **1.963,07** | 1.219,02 | 328.111,44 |
| Cluster Balance | 15 | 15 | 0,0564 | **0,0677** | 0,0104 | 0,0950 |

### Bảng 2 – Chi tiết 15 snapshot (K = 2)

| Snapshot | N | Cụm nhỏ / lớn | Silhouette | DB | CH | Inertia | Balance |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023-11-30 | 142 | 9 / 133 | 0,7754 | 0,5361 | 225,64 | 1.219,02 | 0,0677 |
| 2023-12-29 | 195 | 16 / 179 | 0,7717 | 0,4724 | 417,11 | 1.267,01 | 0,0894 |
| 2024-01-31 | 196 | 17 / 179 | 0,7194 | 0,5585 | 261,53 | 1.360,15 | 0,0950 |
| 2024-02-29 | 196 | 17 / 179 | 0,7451 | 0,4826 | 361,53 | 1.295,24 | 0,0950 |
| 2024-03-29 | 197 | 15 / 182 | 0,6764 | 0,5906 | 190,66 | 1.257,00 | 0,0824 |
| 2024-04-26 | 214 | 14 / 200 | 0,7286 | 0,5476 | 261,89 | 1.535,17 | 0,0700 |
| 2024-05-31 | 221 | 15 / 206 | 0,7043 | 0,5733 | 232,34 | 1.543,37 | 0,0728 |
| 2024-06-28 | 240 | 11 / 229 | 0,7640 | 0,5155 | 274,72 | 1.963,07 | 0,0480 |
| 2024-07-31 | 247 | 17 / 230 | 0,6595 | 0,7167 | 176,31 | 2.009,52 | 0,0739 |
| 2024-08-30 | 595 | 21 / 574 | 0,9069 | 0,4730 | 926,69 | 121.106,78 | 0,0366 |
| 2024-09-30 | 606 | 16 / 590 | 0,9335 | 0,3550 | 2.065,15 | 101.890,30 | 0,0271 |
| 2024-10-31 | 608 | 13 / 595 | 0,9401 | 0,3652 | 1.820,11 | 134.604,42 | 0,0218 |
| 2024-11-29 | 780 | 8 / 772 | 0,9512 | 0,3923 | 1.524,92 | 328.111,44 | 0,0104 |
| 2024-12-31 | 589 | 11 / 578 | 0,9095 | 0,3889 | 983,82 | 52.249,83 | 0,0190 |
| 2025-01-24 | 589 | 21 / 568 | 0,8806 | 0,5175 | 915,49 | 46.772,69 | 0,0370 |

*(Cột N và kích thước cụm lấy từ `cluster_sizes` trong diagnostics; notebook hiển thị 6 cột chuẩn của Bảng 2 theo kế hoạch.)*

### 7.1 – Silhouette

![Silhouette](../artifacts/m2-evaluation-pca-kmeans/plot_7.1.png)


Median **0,7717**, dao động 0,6595–0,9512. Cả 15 tháng đều vượt ngưỡng chấp nhận 0,5; 13/15 tháng vượt ngưỡng xuất sắc 0,7, chỉ hai tháng thấp hơn là 2024-03 (0,6764) và 2024-07 (0,6595). Từ 2024-08 Silhouette nhảy lên 0,88–0,95. Đây là tiêu chí cấp 1: hai nhóm tách biệt rõ trong không gian PCA.

### 7.2 – Davies–Bouldin

![Davies-Bouldin](../artifacts/m2-evaluation-pca-kmeans/plot_7.2.png)


Median **0,5155**, khoảng 0,3550–0,7167. 14/15 tháng ≤ 0,6; điểm xấu nhất là 2024-07 (0,7167), tốt nhất là 2024-09 (0,3550). DB thấp và Silhouette cao nhất quán với nhau; hai chỉ số cùng xấu nhất tại 2024-07 và cùng tốt lên từ 2024-08.

### 7.3 – Calinski–Harabasz

![Calinski-Harabasz](../artifacts/m2-evaluation-pca-kmeans/plot_7.3.png)


Median **361,53**, khoảng 176,31–2.065,15. CH thấp nhất tại 2024-07 (176,31) và cao nhất tại 2024-09 (2.065,15), tăng mạnh ở các tháng universe lớn. CH phụ thuộc cỡ mẫu nên chỉ dùng làm kiểm định an toàn, so trong cùng snapshot.

### 7.4 – Inertia

![Inertia](../artifacts/m2-evaluation-pca-kmeans/plot_7.4.png)


Median **1.963,07**, khoảng 1.219,02–328.111,44. Inertia gần như phẳng (1.219–2.010) khi N = 142–247, rồi tăng vọt sau 2024-08 và đạt đỉnh 328.111 tại 2024-11 (N = 780). Không dùng Inertia để xếp hạng chất lượng theo thời gian (xem mục 6).

### 7.5 – Cluster Balance

![Cluster Balance](../artifacts/m2-evaluation-pca-kmeans/plot_7.5.png)


Median **0,0677**, khoảng 0,0104–0,0950. Median nằm trên ngưỡng 0,05 nhưng **7/15 tháng dưới ngưỡng**: 2024-06 (0,0480) và toàn bộ sáu tháng từ 2024-08 đến 2025-01 (thấp nhất 0,0104 tại 2024-11, cụm nhỏ chỉ 8 mã trên 780 mã). Cụm nhỏ luôn chỉ 8–21 mã. Median một mình che khuất việc balance xấu đi hệ thống ở nửa sau chuỗi.

## 4. Tổng hợp theo hai giai đoạn

| Giai đoạn | Số snapshot | N | Silhouette TB | DB | Balance |
|---|---:|---|---:|---|---|
| 11/2023 – 07/2024 | 9 | 142–247 | ~0,727 | 0,47–0,72 | 0,048–0,095 |
| 08/2024 – 01/2025 | 6 | 589–780 | ~0,920 | 0,36–0,52 | 0,010–0,037 |

Chất lượng nội bộ **tốt lên** ở giai đoạn sau (Silhouette cao hơn, DB thấp hơn) nhưng balance **xấu đi**. Hai xu hướng này đi cùng nhau, không độc lập.

## 5. Nhận định kinh tế – cấu trúc vi mô thị trường

**Phân cấp tiêu chí (theo kế hoạch dự án).** Tiêu chí cấp 1 là median Silhouette cao nhất; tiêu chí phá thế cân bằng là median DB thấp hơn; CH và Balance là kiểm định an toàn. Theo thứ tự này, PCA + K-Means có Silhouette 0,7717 và DB 0,5155 ở mức tốt, nhưng kiểm định an toàn (Balance) phát tín hiệu cảnh báo. Việc xếp hạng so với hai phương án khác thuộc Nhiệm vụ 10, vì artefact của K-Means và Ward chưa có trong báo cáo này.

**Balance thấp = nhóm cực đoan nhỏ.** Với cụm nhỏ chỉ 8–21 mã, thuật toán đang tách một nhóm đại trà khỏi một nhóm cực đoan. Hồ sơ cụm ở Nhiệm vụ 8 nhất quán với cách đọc này: cụm nhỏ có thanh khoản trung vị ~359 tỷ so với ~14 tỷ, beta ~1,26 so với ~0,62 và momentum cao hơn. Đây là đặc tính của dữ liệu tài chính đuôi dài (heavy tails), không phải lỗi thuật toán. Tuy nhiên, Silhouette cao nhất đúng lúc balance thấp nhất (2024-11: 0,9512 và 0,0104) cho thấy điểm số nội bộ đang được nâng bởi việc cô lập vài quan sát cực đoan, nên không đồng nghĩa với việc hai nhóm có ý nghĩa kinh tế cân bằng.

**Tháng 07/2024 (điểm yếu nhất).** Cả ba chỉ số Silhouette (0,6595), DB (0,7167) và CH (176,31) cùng đạt mức xấu nhất tại tháng này, trong khi balance (0,0739) không thấp bất thường. Nghĩa là cụm nhỏ 17 mã tách kém rõ hơn so với phần còn lại của chuỗi. Dữ liệu hiện có chưa đủ để kết luận nguyên nhân thị trường; cần đối chiếu thêm với profile cụm theo snapshot.

**Bước nhảy 08/2024 (universe tăng từ 247 lên 595 mã).** Silhouette tăng từ 0,6595 lên 0,9069 và balance giảm từ 0,0739 xuống 0,0366. Theo Nhiệm vụ 9, có 349 mã mới vào universe ở chuyển tiếp này. Profile Nhiệm vụ 8 cho thấy ngay tháng đó cụm lớn có thanh khoản trung vị giảm từ 20,24 xuống 6,73 tỷ và beta từ 0,66 xuống 0,47, nhất quán với việc nhóm mã mới có thanh khoản thấp làm phần đại trà đồng nhất hơn và đẩy các mã thanh khoản cao ra xa hơn. Đây là diễn giải dựa trên số liệu hiện có, chưa phải kiểm định nguyên nhân.

## 6. Ranh giới phương pháp luận

- **Inertia không dùng để so sánh giữa các tháng.** N tăng từ 142 lên 780 làm Inertia tăng cơ học. Lưu ý thêm: Inertia chia cho N cũng không phẳng, khoảng 6,4–8,6 khi N ≤ 247 nhưng khoảng 79–421 từ 08/2024. Như vậy mức tăng không chỉ do N mà còn do phân bố dữ liệu của universe mở rộng (nhiều giá trị cực đoan hơn sau Robust Scaling). Đây là quan sát cần kiểm tra thêm, không phải kết luận.
- **CH chỉ so trong cùng snapshot** vì phụ thuộc cỡ mẫu.
- **Metric nội bộ không phải bằng chứng kinh tế.** Silhouette và DB đo khoảng cách hình học trong không gian PCA, không chứng minh cụm có khả năng sinh lời hay phân biệt rủi ro.
- **Không dùng return, Sharpe, ROI hay holdout** để đánh giá chất lượng; đánh giá hoàn toàn độc lập với bài toán danh mục (M3).
- **So sánh liên phương án** cần lưu ý PCA đo trong không gian 4 chiều còn K-Means/Ward đo trong không gian gốc; chỉ nên xếp hạng ở Nhiệm vụ 10 với cùng protocol và có chú thích này.

## 7. Khung kết luận ba phần (theo notebook 07)

**Phần A – Phán quyết kỹ thuật.** PCA + K-Means (K = 2) đạt điểm tách biệt tốt: median Silhouette 0,7717 và median DB 0,5155 đều ở mức tốt. Cluster Balance là điểm yếu: median 0,0677 vượt ngưỡng 0,05 nhưng 7/15 tháng nằm dưới ngưỡng, cụm nhỏ chỉ có 8–21 mã. Chưa thể nói hiện tượng này "giống K-Means Baseline" vì artifact của K-Means Baseline chưa có trong báo cáo này; việc đối chiếu thuộc Nhiệm vụ 10.

**Phần B – Bản chất thị trường.** Cách đọc phù hợp nhất với số liệu là dữ liệu có đuôi dày: một nhóm nhỏ mã có thanh khoản và beta cao khác biệt rõ so với phần còn lại (Nhiệm vụ 8). PCA giữ 96,86% phương sai nên không xóa bỏ sự bất đối xứng này. Đây là phù hợp với giả thuyết cô lập nhóm ngoại lai bất đối xứng, chưa phải bằng chứng chứng minh giả thuyết, vì báo cáo chưa kiểm tra riêng vai trò của từng quan sát.

**Phần C – Bàn giao cho Nhiệm vụ 10.** Với Silhouette và DB tốt, nhánh PCA đủ điều kiện vào vòng so sánh ở Nhiệm vụ 10 (qua `quality_summary.csv`). Mất cân bằng cụm là đặc tính cần mang theo khi so sánh, không phải lý do loại. Không xếp hạng phương pháp ở báo cáo này.

## 8. Tổng hợp nhận xét

PCA + K-Means K = 2 đạt chất lượng hình học nội bộ tốt trên Development (Silhouette median 0,7717; DB median 0,5155), nhưng đánh đổi bằng mất cân bằng cụm: 7/15 tháng dưới ngưỡng 0,05 và cụm nhỏ chỉ 8–21 mã. Kết quả đủ để đóng phần đánh giá chất lượng cho nhánh PCA và làm đầu vào Nhiệm vụ 10, chưa đủ để kết luận PCA vượt trội so với K-Means hay Ward, càng không đủ để khẳng định giá trị đầu tư.

**Bàn giao:** notebook `07_cluster_quality_evaluation_pca_kmeans.ipynb`; `M2/artifacts/m2-evaluation-pca-kmeans/quality_summary.csv` (7 cột) và `plot_7.1.png` … `plot_7.5.png`; báo cáo này.

## 9. Lưu ý kiểm tra notebook (không ảnh hưởng số liệu ở Bảng 1 và Bảng 2)

1. **Notebook không lưu output**; số liệu trong báo cáo khớp với kết quả lần chạy trước của chính notebook này và với `diagnostics.csv`.
2. **Ô kết luận Markdown viết chung chung, chưa gắn số liệu.** Câu "Cluster Balance Median đôi lúc trượt xuống dưới 0.05" chưa chính xác: median là 0,0677; chính xác là 7/15 từng tháng dưới 0,05.
3. **Các nhận định chưa có bằng chứng trong notebook:** "giống với K-Means Baseline" (không có artifact đối chiếu) và "PCA giúp K-Means bắt tụ điểm nhiễu nhanh hơn" (không có phép đo tốc độ hội tụ).
4. **Biểu đồ 7.1–7.4 chỉ có đường Median**, chỉ biểu đồ 7.5 có đường ngưỡng 0,05; nếu muốn đọc Silhouette theo ngưỡng thì cần thêm đường 0,5 và 0,7.
5. **Bảng 2 trong notebook chưa có cột N và kích thước cụm**; hai cột này trong báo cáo lấy từ `cluster_sizes` của diagnostics. Notebook cũng chưa kiểm tra cột `converged`.
6. Đường dẫn `project_root` trong notebook là đường dẫn tuyệt đối trên máy cục bộ.
