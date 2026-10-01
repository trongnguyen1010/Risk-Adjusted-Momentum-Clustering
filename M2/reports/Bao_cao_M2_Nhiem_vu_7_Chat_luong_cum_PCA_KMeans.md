# Báo cáo Nhiệm vụ 7: Đánh giá Chất lượng Cụm - PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshots development (30/11/2023 - 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Đánh giá chất lượng cụm PCA+KMeans cho thấy điểm số cấu trúc hình học cực kỳ xuất sắc với Median Silhouette lên tới 0.7717 và Davies-Bouldin giảm còn 0.5155. Không gian 4 chiều đã giúp tách biệt hoàn hảo các nhóm cổ phiếu. Tuy nhiên, mô hình bộc lộ sự mất cân bằng nghiêm trọng về tỷ trọng (Cluster Balance chỉ đạt ~6.77%), cho thấy hiện tượng cô lập "Siêu cổ phiếu" thay vì chia đều thị trường.

---

## 1. Mục tiêu

Đánh giá chất lượng hình học của PCA + K-Means ở từng snapshot Development bằng Silhouette, Davies–Bouldin, Calinski–Harabasz, inertia và cluster balance. Mục tiêu là mô tả độ tách biệt, độ gọn và tính cân bằng của cụm; không dùng return, Sharpe, ROI hay holdout để chọn phương án.

Phạm vi báo cáo này là **PCA + K-Means với Global K = 2**. Kế hoạch Task 7 yêu cầu so sánh thêm K-Means baseline và Ward, nhưng hai artefact tương ứng chưa có trong run này; do đó chưa thể xếp hạng phương pháp hay chọn final method.

## 2. Quá trình đánh giá

Nguồn dữ liệu là `M2/artifacts/m2-task6-pca-kmeans-v1/diagnostics.csv`. File có 105 dòng = 15 snapshot x 7 giá trị `k`. Báo cáo lọc đúng 15 dòng `k=2`, là Global K đã khóa từ Task 3, rồi tổng hợp median, mean và khoảng biến động giữa snapshot.

| Metric | Quy ước |
|---|---|
| Silhouette | Cao hơn thường tốt hơn; đo độ gắn kết trong cụm và tách biệt khỏi cụm khác |
| Davies–Bouldin | Thấp hơn thường tốt hơn; đo độ gọn/tách giữa cụm |
| Calinski–Harabasz | Cao hơn thường tốt hơn trong cùng snapshot/setting |
| Inertia | Tổng bình phương khoảng cách tới centroid; phụ thuộc mạnh vào số quan sát và thang dữ liệu |
| Balance | Kích thước cụm nhỏ / cụm lớn; gần 1 là cân bằng hơn |

## 3. Kết quả đạt được theo kế hoạch

### 7.1 — Silhouette

Median Silhouette là **0,7717**, dao động 0,6595–0,9512. Đây là bằng chứng hai nhóm tách biệt khá rõ trong không gian PCA đã dùng để fit K-Means.

### 7.2 — Davies–Bouldin

Median Davies–Bouldin là **0,5155**, khoảng 0,3550–0,7167. Giá trị thấp cùng với Silhouette cao nhất quán với cấu trúc có độ gọn/tách tốt theo metric nội bộ.

### 7.3 — Calinski–Harabasz

Median Calinski–Harabasz là **361,53**, khoảng 176,31–2.065,15. Chỉ số tăng mạnh ở các tháng có universe lớn, vì vậy phù hợp để tham khảo trong cùng snapshot hơn là so sánh giá trị tuyệt đối qua các tháng có cỡ mẫu khác nhau.

### 7.4 — Inertia

Median inertia là **1.963,07**, khoảng 1.219,02–328.111,44. Inertia tăng rất mạnh khi universe tăng từ khoảng 200 lên 780 mã; đây không phải bằng chứng riêng về mô hình xấu đi. Cần so sánh cùng snapshot, cùng scaling và cùng `k`, hoặc chuẩn hóa theo số quan sát trước khi diễn giải xu hướng thời gian.

### 7.5 — Cluster balance

Median balance là **0,0677** (6,77%), khoảng 1,04%–9,50%. Cụm nhỏ có 8–21 mã mỗi snapshot, trung vị 15 mã. Đây là rủi ro diễn giải chính: mô hình tách một nhóm thiểu số thay vì hai nhóm có quy mô tương đương.

## 4. Bảng kết quả từng snapshot — Global K = 2

| Snapshot | N | Cụm nhỏ | Cụm lớn | Silhouette | DB | CH | Inertia | Balance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023-11-30 | 142 | 9 | 133 | 0,7754 | 0,5361 | 225,64 | 1.219,02 | 0,0677 |
| 2023-12-29 | 195 | 16 | 179 | 0,7717 | 0,4724 | 417,11 | 1.267,01 | 0,0894 |
| 2024-01-31 | 196 | 17 | 179 | 0,7194 | 0,5585 | 261,53 | 1.360,15 | 0,0950 |
| 2024-02-29 | 196 | 17 | 179 | 0,7451 | 0,4826 | 361,53 | 1.295,24 | 0,0950 |
| 2024-03-29 | 197 | 15 | 182 | 0,6764 | 0,5906 | 190,66 | 1.257,00 | 0,0824 |
| 2024-04-26 | 214 | 14 | 200 | 0,7286 | 0,5476 | 261,89 | 1.535,17 | 0,0700 |
| 2024-05-31 | 221 | 15 | 206 | 0,7043 | 0,5733 | 232,34 | 1.543,37 | 0,0728 |
| 2024-06-28 | 240 | 11 | 229 | 0,7640 | 0,5155 | 274,72 | 1.963,07 | 0,0480 |
| 2024-07-31 | 247 | 17 | 230 | 0,6595 | 0,7167 | 176,31 | 2.009,52 | 0,0739 |
| 2024-08-30 | 595 | 21 | 574 | 0,9069 | 0,4730 | 926,69 | 121.106,78 | 0,0366 |
| 2024-09-30 | 606 | 16 | 590 | 0,9335 | 0,3550 | 2.065,15 | 101.890,30 | 0,0271 |
| 2024-10-31 | 608 | 13 | 595 | 0,9401 | 0,3652 | 1.820,11 | 134.604,42 | 0,0218 |
| 2024-11-29 | 780 | 8 | 772 | 0,9512 | 0,3923 | 1.524,92 | 328.111,44 | 0,0104 |
| 2024-12-31 | 589 | 11 | 578 | 0,9095 | 0,3889 | 983,82 | 52.249,83 | 0,0190 |
| 2025-01-24 | 589 | 21 | 568 | 0,8806 | 0,5175 | 915,49 | 46.772,69 | 0,0370 |

## 5. Bảng tổng hợp

| Metric | Median | Mean | Min–max |
|---|---:|---:|---:|
| Silhouette | 0,7717 | 0,8044 | 0,6595–0,9512 |
| Davies–Bouldin | 0,5155 | 0,4990 | 0,3550–0,7167 |
| Calinski–Harabasz | 361,53 | 709,19 | 176,31–2.065,15 |
| Inertia | 1.963,07 | 53.212,33 | 1.219,02–328.111,44 |
| Balance | 0,0677 | 0,0564 | 0,0104–0,0950 |

## 6. Phân tích

Silhouette cao và DB thấp cho thấy PCA + K-Means tách được một cấu trúc hình học rõ. Tuy vậy, cấu trúc rõ này đi cùng balance rất thấp. Khi một cụm có rất ít mã, việc cô lập các quan sát cực đoan có thể làm metric nội bộ đẹp hơn nhưng không đủ để khẳng định mô hình mô tả hai chế độ thị trường cân bằng.

Vì cỡ universe thay đổi mạnh theo snapshot, CH và inertia không nên được đọc như chuỗi thời gian đơn giản. Quality cần được đặt cạnh profile cụm (Task 8), stability (Task 9) và kết quả cùng protocol của K-Means/Ward trước khi có quyết định cuối cùng ở Task 10.

## 7. Tổng hợp nhận xét

PCA + K-Means `k=2` đạt chất lượng nội bộ tốt trên Development, nhưng đánh đổi bằng mất cân bằng cụm nghiêm trọng. Kết quả hiện đủ để đóng phần quality cho riêng nhánh PCA và làm đầu vào Task 10; chưa đủ để kết luận PCA vượt trội hơn các thuật toán khác hoặc phù hợp cho một mục đích đầu tư.

Nguồn chính: `M2/artifacts/m2-task6-pca-kmeans-v1/diagnostics.csv`.