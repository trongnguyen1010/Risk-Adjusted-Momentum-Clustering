# Báo cáo Nhiệm vụ 7: Đánh giá Chất lượng Cụm – PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshot Development (30/11/2023 – 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)
**Nguồn:** `M2/artifacts/m2-task6-pca-kmeans-v1/diagnostics.csv` | **Notebook:** `M2/notebooks/07_cluster_quality_evaluation_pca_kmeans.ipynb` | **Artifact xuất ra:** `M2/artifacts/m2-evaluation-pca-kmeans/quality_summary.csv`

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Tại K = 2, PCA + K-Means có độ tách biệt và độ gọn tốt: median Silhouette **0,7717** (vượt ngưỡng xuất sắc 0,7) và median Davies–Bouldin **0,5155**. Điểm yếu cố hữu là Cluster Balance: median **0,0677** (thấp hơn 0,10), 7/15 tháng dưới ngưỡng cảnh báo 0,05 và cụm nhỏ chỉ chiếm 1–9% thị trường (8–21 mã). Theo Balance Diagnostic Test, đây là hiện tượng Phân cụm bất đối xứng / Cô lập nhóm ngoại lai (Asymmetric Outlier Isolation).

---

## 1. Mục đích

Đánh giá chất lượng hình học và độ phân tách của cụm PCA + K-Means tại cấu hình K = 2 (đã khóa từ Nhiệm vụ 3) trên 15 snapshot Development bằng 5 chỉ số nội bộ: Silhouette, Davies–Bouldin, Calinski–Harabasz, Inertia và Cluster Balance; theo dõi biến thiên theo thời gian và hiện tượng phân mảnh cụm; dùng cùng cấu trúc bảng, biểu đồ và schema `quality_summary.csv` với K-Means Baseline và Ward. Chất lượng cụm được đánh giá hoàn toàn bằng thước đo khoảng cách trong không gian đặc trưng, không dùng return, Sharpe hay ROI.

## 2. Quá trình thực hiện

| Bước | Thực hiện |
|---|---|
| 1. Đọc dữ liệu chẩn đoán | Kiểm tra manifest `status = complete`, checksum và config (fail-closed), rồi đọc `diagnostics.csv` của Task 6 (105 dòng = 15 snapshot × 7 giá trị k). Metric được đo trong không gian PCA 4 chiều dùng để phân cụm |
| 2. Trích xuất K = 2 | Lọc 15 dòng `k == 2`, chuẩn hóa `snapshot_date`, sắp xếp theo thời gian; tính Mean, Median, Min, Max cho 5 chỉ số và xuất `quality_summary.csv` (7 cột: `metric`, `n_total`, `n_available`, `mean`, `median`, `minimum`, `maximum`) |
| 3. Hiển thị 2 bảng chuẩn | Bảng 1 (5 × 7) và Bảng 2 (15 × 6) |
| 4. Trực quan hóa | 5 biểu đồ đường 7.1–7.5, đường Median nét đứt đỏ; biểu đồ 7.5 thêm ngưỡng 0,05 |
| 5. Nhận định | Phân tích kinh tế và giới hạn phương pháp luận trong các ô Markdown, tổng hợp thành báo cáo này |

Quy ước đọc chỉ số: Silhouette cao hơn tốt hơn (chấp nhận > 0,5; xuất sắc > 0,7); Davies–Bouldin thấp hơn tốt hơn; Calinski–Harabasz cao hơn tốt hơn; Inertia tỷ lệ thuận với số cổ phiếu N; Balance = `min_size / max_size`.

## 3. Kết quả đạt được

### Bảng 1 – Tóm tắt thống kê chất lượng cụm K = 2

| Chỉ số | n_total | n_available | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| silhouette | 15 | 15 | 0,8044 | **0,7717** | 0,6595 | 0,9512 |
| davies_bouldin | 15 | 15 | 0,4990 | **0,5155** | 0,3550 | 0,7167 |
| calinski_harabasz | 15 | 15 | 709,19 | **361,53** | 176,31 | 2.065,15 |
| inertia | 15 | 15 | 53.212,33 | **1.963,07** | 1.219,02 | 328.111,44 |
| cluster_balance | 15 | 15 | 0,0564 | **0,0677** | 0,0104 | 0,0950 |

### Bảng 2 – Chi tiết chất lượng qua 15 snapshot tại K = 2

| Snapshot | Silhouette | DB | CH | Inertia | Balance |
|---|---:|---:|---:|---:|---:|
| 2023-11-30 | 0,7754 | 0,5361 | 225,64 | 1.219,02 | 0,0677 |
| 2023-12-29 | 0,7717 | 0,4724 | 417,11 | 1.267,01 | 0,0894 |
| 2024-01-31 | 0,7194 | 0,5585 | 261,53 | 1.360,15 | 0,0950 |
| 2024-02-29 | 0,7451 | 0,4826 | 361,53 | 1.295,24 | 0,0950 |
| 2024-03-29 | 0,6764 | 0,5906 | 190,66 | 1.257,00 | 0,0824 |
| 2024-04-26 | 0,7286 | 0,5476 | 261,89 | 1.535,17 | 0,0700 |
| 2024-05-31 | 0,7043 | 0,5733 | 232,34 | 1.543,37 | 0,0728 |
| 2024-06-28 | 0,7640 | 0,5155 | 274,72 | 1.963,07 | 0,0480 |
| 2024-07-31 | 0,6595 | 0,7167 | 176,31 | 2.009,52 | 0,0739 |
| 2024-08-30 | 0,9069 | 0,4730 | 926,69 | 121.106,78 | 0,0366 |
| 2024-09-30 | 0,9335 | 0,3550 | 2.065,15 | 101.890,30 | 0,0271 |
| 2024-10-31 | 0,9401 | 0,3652 | 1.820,11 | 134.604,42 | 0,0218 |
| 2024-11-29 | 0,9512 | 0,3923 | 1.524,92 | 328.111,44 | 0,0104 |
| 2024-12-31 | 0,9095 | 0,3889 | 983,82 | 52.249,83 | 0,0190 |
| 2025-01-24 | 0,8806 | 0,5175 | 915,49 | 46.772,69 | 0,0370 |

### 7.1 – Silhouette Score


Median **0,7717**, dao động 0,6595–0,9512. Cả 15 tháng vượt ngưỡng chấp nhận 0,5; 13/15 tháng vượt ngưỡng xuất sắc 0,7 (hai tháng thấp hơn: 2024-03 với 0,6764 và 2024-07 với 0,6595). Từ 2024-08 Silhouette tăng lên 0,88–0,95. Hai nhóm tách biệt rõ trong không gian PCA.

### 7.2 – Davies–Bouldin Index


Median **0,5155**, khoảng 0,3550–0,7167; 14/15 tháng ≤ 0,6. Tháng xấu nhất là 2024-07 (0,7167), tháng tốt nhất là 2024-09 (0,3550). Giá trị thấp, nhất quán với Silhouette cao.

### 7.3 – Calinski–Harabasz Index

Median **361,53**, khoảng 176,31–2.065,15; thấp nhất tại 2024-07 và cao nhất tại 2024-09. CH tăng mạnh ở các tháng universe lớn nên chỉ dùng làm kiểm định an toàn, so sánh trong cùng snapshot.

### 7.4 – Quán tính nội cụm (Inertia)


Median **1.963,07**, khoảng 1.219,02–328.111,44. Inertia biến thiên tỷ lệ thuận với số cổ phiếu quan sát N: gần như phẳng (1.219–2.010) khi N = 142–247, rồi tăng vọt sau 2024-08 và đạt đỉnh 328.111 tại 2024-11 (N = 780).

### 7.5 – Cluster Balance


Median **0,0677**, khoảng 0,0104–0,0950. Median nằm trên ngưỡng 0,05 nhưng **7/15 tháng dưới ngưỡng**: 2024-06 (0,0480) và toàn bộ sáu tháng từ 2024-08 đến 2025-01 (thấp nhất 0,0104 tại 2024-11).

## 4. Nhận định kinh tế tài chính và rào chắn học thuật

### 4.1 Kiểm định mức độ cân bằng cụm (Balance Diagnostic Test)

`pct_small = min_size / N` và `Cluster Balance = min_size / max_size`:

| Snapshot | N | Cụm nhỏ | pct_small | Snapshot | N | Cụm nhỏ | pct_small |
|---|---:|---:|---:|---|---:|---:|---:|
| 2023-11-30 | 142 | 9 | 6,3% | 2024-08-30 | 595 | 21 | 3,5% |
| 2023-12-29 | 195 | 16 | 8,2% | 2024-09-30 | 606 | 16 | 2,6% |
| 2024-01-31 | 196 | 17 | 8,7% | 2024-10-31 | 608 | 13 | 2,1% |
| 2024-02-29 | 196 | 17 | 8,7% | 2024-11-29 | 780 | 8 | 1,0% |
| 2024-03-29 | 197 | 15 | 7,6% | 2024-12-31 | 589 | 11 | 1,9% |
| 2024-04-26 | 214 | 14 | 6,5% | 2025-01-24 | 589 | 21 | 3,6% |
| 2024-05-31 | 221 | 15 | 6,8% | | | | |
| 2024-06-28 | 240 | 11 | 4,6% | | | | |
| 2024-07-31 | 247 | 17 | 6,9% | | | | |

Cả 15 tháng đều có Balance < 0,10 và cụm nhỏ chiếm < 10% thị trường, tức thuộc **Kịch bản A**. Kết luận: đây là hiện tượng **Phân cụm bất đối xứng / Cô lập nhóm ngoại lai (Asymmetric Outlier Isolation)**. Thuật toán không chia thị trường thành hai nửa cân bằng mà đang tách một nhóm nhỏ (8–21 mã) ra khỏi phần lớn thị trường.

**Giải thích nguyên nhân (theo kế hoạch; notebook ghi rõ chưa chứng minh riêng nguyên nhân dòng tiền/đầu cơ).** Thị trường chứng khoán Việt Nam có tính đầu cơ cao, tạo ra các cổ phiếu động lượng hoặc biến động cực đại (phân phối đuôi dày). Dự án thống nhất không dùng Clipping/Winsorization (`winsor_quantile = 0`, `clipping = false`), nên các giá trị cực đoan được giữ nguyên; Robust Scaling chỉ giảm nhẹ ảnh hưởng của chúng. PCA giữ khoảng 96,86% phương sai nên không xóa bỏ sự bất đối xứng này.

**Cảnh báo học thuật.** Silhouette cao trong trường hợp này phản ánh khoảng cách hình học xa của nhóm ngoại lai, không đồng nghĩa thị trường có hai chế độ cân bằng. Minh họa: tại 2024-11, Silhouette đạt 0,9512 cao nhất chuỗi trong khi Balance chỉ 0,0104 (8 mã trên 780 mã).

### 4.2 Kiểm định Quán tính nội cụm (Inertia Caveat Rule)

Inertia tỷ lệ thuận với N, nên không so sánh Inertia tuyệt đối giữa tháng 142 mã và tháng gần 800 mã. Giá trị Inertia chỉ có ý nghĩa khi so cùng snapshot, cùng scaling và cùng k, hoặc sau khi chuẩn hóa theo số quan sát. Vì vậy Inertia không dùng để xếp hạng chất lượng theo thời gian.

### 4.3 Phân cấp ưu tiên tiêu chí

- **Tiêu chí cấp 1:** median Silhouette cao nhất – nhánh PCA đạt 0,7717.
- **Tiêu chí phá vỡ thế cân bằng:** median Davies–Bouldin thấp hơn – nhánh PCA đạt 0,5155.
- **Kiểm định an toàn:** Calinski–Harabasz (median 361,53) và Cluster Balance (median 0,0677; cảnh báo cô lập ngoại lai).

Việc xếp hạng với K-Means Baseline và Ward thực hiện ở Nhiệm vụ 10 khi có artifact cùng protocol.

### 4.4 Ranh giới phương pháp luận

Không đưa return, Sharpe hay ROI vào Nhiệm vụ 7; đánh giá chất lượng cụm độc lập hoàn toàn với bài toán danh mục (M3).

## 5. Khung kết luận ba phần

**Phần A – Phán quyết kỹ thuật.** Median Silhouette 0,7717 (vượt ngưỡng 0,70), DB 0,5155, CH 361,53, Inertia 1.963,07, Balance 0,0677. Có 7/15 tháng Balance < 0,05; cụm nhỏ 8–21 mã. Median Balance không thay thế việc kiểm tra từng tháng.

**Phần B – Bản chất cấu trúc quan sát.** Hai nhóm có quy mô bất đối xứng. Silhouette cao chỉ chứng minh phân tách trong không gian PCA; không chứng minh mọi cổ phiếu có hành vi giống nhau hoặc nguyên nhân là dòng tiền/đầu cơ. Hồ sơ gốc và động lực phân tách được kiểm tra riêng ở Nhiệm vụ 8. Inertia chịu ảnh hưởng của N và độ phân tán, không phải tiêu chí xếp hạng độc lập theo thời gian.

**Phần C – Bàn giao và giới hạn.** Bàn giao đủ hai bảng, năm biểu đồ và `quality_summary` schema 5 × 7. Giữ cảnh báo mất cân bằng; không kết luận PCA cải thiện độ ổn định hay giá trị đầu tư. Không chọn lại K, không fit model, không dùng holdout hay chỉ số danh mục. Nhánh PCA đủ điều kiện vào vòng so sánh ở Nhiệm vụ 10.
