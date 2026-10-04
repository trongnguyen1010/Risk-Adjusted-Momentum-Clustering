# Báo cáo Chuyên đề M2 — Nhiệm vụ 7: Đánh giá Chất lượng Cụm (Cluster Quality Evaluation)
**Mô hình phân tích:** Phương án 2 — Ward Hierarchical Clustering (Cấu hình tối ưu Global K = 2)  
**Khung thời gian thực hiện:** Development Window gồm 15 Snapshots (30/11/2023 – 24/01/2025)  
**Tác giả thực hiện:** Nhánh Ward Hierarchical — Milestone M2  

---

## I. Mục tiêu & Cơ sở Phương pháp luận

Nhiệm vụ 7 tiến hành đánh giá thực chứng chất lượng hình học và độ phân tách toán học của cấu trúc phân nhóm 2 cụm (K = 2) được tạo bởi thuật toán phân cụm thứ bậc Ward (Ward Hierarchical Clustering với tiêu chí liên kết phương sai tối thiểu Ward Linkage). Quá trình đánh giá được thực hiện độc lập hoàn toàn trên 15 snapshots cuối tháng thuộc Cửa sổ phát triển (Development Window: từ 30/11/2023 đến 24/01/2025).

### Các nguyên tắc phương pháp luận bất biến:
1. **Tiêu thụ Artifacts đã đóng băng:** Tầng đánh giá chất lượng chỉ nạp dữ liệu chẩn đoán `diagnostics.csv` sinh ra từ Nhiệm vụ 5 (đã được lưu tại `M2/artifacts/m2-task5-ward-v1/diagnostics.csv`), tuyệt đối không huấn luyện lại mô hình hoặc tinh chỉnh tham số hồi quy.
2. **Khảo sát chuyên sâu cấu hình K = 2:** Trích xuất duy nhất 15 dòng dữ liệu ứng với K = 2 (đã được khóa từ Nhiệm vụ 3) để phân tích diễn biến qua chuỗi thời gian. Các dòng K = 3 đến 8 là bằng chứng đối chiếu lịch sử của pha khảo sát K, không tham gia đánh giá chính thức tại K = 2.
3. **Ranh giới M2 / M3 nghiêm ngặt:** Đánh giá chất lượng cụm hoàn toàn bằng 5 chỉ số không gian nội bộ (Internal Distance Metrics). Tuyệt đối không sử dụng tỷ suất sinh lời, Sharpe ratio, Sortino, ROI hay bất kỳ chỉ số danh mục nào (thuộc Milestone M3).

---

## II. Phân cấp Tiêu chí Đánh giá theo Kế hoạch Dự án

Theo quy chuẩn `DELTA_UNIFIED_PROJECT_PLAN.md` và `M2/Ke_hoach_M2_Phan_cum_co_phieu.md`:
- **Tiêu chí cấp 1 (Primary Criterion):** Median Silhouette cao nhất. Thước đo cao nhất chứng minh mức độ phân tách rõ ràng giữa 2 nhóm cổ phiếu.
- **Tiêu chí phá vỡ thế cân bằng (Secondary Tie-breaker):** Median Davies-Bouldin thấp hơn. Dùng khi Silhouette giữa các mô hình tương đương.
- **Tiêu chí kiểm định an toàn (Sanity Diagnostics):** Calinski-Harabasz và Cluster Balance. Giúp cảnh báo nguy cơ phân cụm bị chi phối bởi các cổ phiếu ngoại lai cá biệt hoặc hiện tượng mất cân bằng cấu trúc.

---

## III. Bảng Số liệu Thực chứng Chuẩn hóa

### Bảng 1: Tóm tắt Thống kê Chất lượng Cụm K=2 (Kích thước 5 dòng x 7 cột chuẩn)
*Nguồn dữ liệu: `M2/artifacts/m2-evaluation-ward/quality_summary.csv`*

| metric | n_total | n_available | mean | median | minimum | maximum |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **silhouette** | 15 | 15 | 0.763118 | **0.755722** | 0.458851 | 0.943929 |
| **davies_bouldin** | 15 | 15 | 0.578858 | **0.534333** | 0.267141 | 1.093217 |
| **calinski_harabasz** | 15 | 15 | 614.645839 | **316.391783** | 118.873252 | 1882.058299 |
| **inertia** | 15 | 15 | 61151.116169 | **2158.608251** | 1304.124507 | 419136.924313 |
| **cluster_balance** | 15 | 15 | 0.080491 | **0.067669** | 0.010292 | 0.223602 |

---

### Bảng 2: Chi tiết Chất lượng qua 15 Snapshots tại K=2 (Kích thước 15 dòng x 6 cột chuẩn)

| Snapshot | Silhouette | DB | CH | Inertia | Balance |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2023-11-30** | 0.762987 | 0.549272 | 210.950916 | 1304.124507 | 0.067669 |
| **2023-12-29** | 0.755722 | 0.493906 | 378.398170 | 1396.643410 | 0.089385 |
| **2024-01-31** | 0.695411 | 0.587799 | 233.930208 | 1520.946055 | 0.094972 |
| **2024-02-29** | 0.723123 | 0.513532 | 316.391783 | 1480.098520 | 0.094972 |
| **2024-03-29** | 0.524664 | 1.093217 | 118.873252 | 1649.370732 | 0.223602 |
| **2024-04-26** | 0.704479 | 0.590603 | 239.277992 | 1674.880177 | 0.075377 |
| **2024-05-31** | 0.558701 | 0.879652 | 164.635080 | 1909.424379 | 0.163158 |
| **2024-06-28** | 0.748492 | 0.534333 | 249.860699 | 2158.608251 | 0.048035 |
| **2024-07-31** | 0.458851 | 1.077800 | 119.007501 | 2464.520666 | 0.204878 |
| **2024-08-30** | 0.903261 | 0.475227 | 919.686722 | 122029.496743 | 0.036585 |
| **2024-09-30** | 0.935512 | 0.267141 | 1882.058299 | 109618.593378 | 0.020202 |
| **2024-10-31** | 0.943929 | 0.287598 | 1680.007440 | 143137.741318 | 0.015025 |
| **2024-11-29** | 0.911055 | 0.606436 | 1027.682234 | 419136.924313 | 0.044177 |
| **2024-12-31** | 0.905533 | 0.391856 | 965.060327 | 53268.069172 | 0.019031 |
| **2025-01-24** | 0.915044 | 0.334505 | 713.866970 | 54517.300914 | 0.010292 |

---

## IV. Phân tích 5 Chỉ số & Trực quan hóa

### 1. Silhouette Score qua 15 tháng
- **Giá trị thực tế:** Median Silhouette đạt **0.7557**, Mean đạt **0.7631**, biên độ dao động từ cực tiểu **0.4589** (31/07/2024) đến cực đại **0.9439** (31/10/2024).
- **So sánh đối ứng:** Median Silhouette của Ward (0.7557) nhỉnh hơn K-Means Baseline (0.7485). Tuy nhiên, độ biến động của Ward lớn hơn, có tháng giảm xuống dưới 0.50 (tháng 07/2024 đạt 0.4589) phản ánh cấu trúc cây phân bậc nhạy cảm với các nhịp phân hóa mạnh của thị trường. Từ tháng 08/2024 khi Universe mở rộng, điểm Silhouette tăng vọt lên trên 0.90 tương tự K-Means.

### 2. Davies-Bouldin Index qua 15 tháng
- **Giá trị thực tế:** Median DB đạt **0.5343**, Mean đạt **0.5789**, biên độ [0.2671, 1.0932].
- **Nhận định:** Chỉ số DB của Ward nhìn chung rất tốt (quanh 0.27 - 0.60 ở phần lớn các tháng), chứng minh các cụm có độ nén cao và tách biệt rõ. Tại một số thời điểm thị trường rung lắc (03/2024 và 07/2024), DB tăng vượt 1.0 do cụm nhỏ tiếp nhận thêm một số cổ phiếu vùng ven.

### 3. Calinski-Harabasz Index qua 15 tháng
- **Giá trị thực tế:** Median CH đạt **316.39**, Mean đạt **614.65**, đỉnh điểm đạt **1,882.06** vào tháng 09/2024.
- **Nhận định:** Tương tự K-Means, chỉ số CH của Ward luôn ở mức hàng trăm đến hàng ngàn, khẳng định phương sai giữa các cụm áp đảo hoàn toàn phương sai nội bộ cụm.

### 4. Quán tính nội cụm Inertia qua 15 tháng
- **Giá trị thực tế:** Median đạt **2,158.61**, Min là **1,304.12** (11/2023), Max lên tới **419,136.92** (11/2024).
- **Rào chắn học thuật (Inertia Caveat Rule):** Tương tự mọi thuật toán hình học, Inertia tỷ lệ thuận với số lượng cổ phiếu quan sát N. Tuyệt đối không so sánh Inertia tuyệt đối giữa giai đoạn N nhỏ (142 - 247 mã) và giai đoạn N lớn (595 - 780 mã).

### 5. Tỷ số Cân bằng Cụm Cluster Balance qua 15 tháng
- **Giá trị thực tế:** Median Balance đạt **0.0677** (6.77%), Mean đạt **0.0805** (8.05%), Min là **0.0103** (01/2025), Max đạt **0.2236** (03/2024).
- **Ưu điểm vượt trội so với K-Means:** Median Cluster Balance của Ward (0.0677) **cao hơn 41%** so với K-Means Baseline (0.0480). Ở giai đoạn nửa đầu năm 2024, Ward có nhiều tháng đạt tỷ lệ cân bằng cụm từ 7.5% đến 22.4%, giúp cụm dẫn dắt bao quát được quy mô cổ phiếu phong phú hơn (trung bình 19 mã/tháng so với 15 mã/tháng của K-Means).

---

## V. Nhận định Kinh tế & Rào chắn Học thuật (Diagnostic Rubrics)

### 1. Phán quyết Kiểm định Cân bằng (Balance Diagnostic Test — Kịch bản A)
- Mặc dù có tỷ số cân bằng tốt hơn K-Means, nhưng với Median Cluster Balance = 0.0677 (< 0.10) và tỷ trọng cụm nhỏ chiếm bình quân khoảng 6.34% toàn thị trường, Ward Hierarchical vẫn thuộc **Kịch bản A — Phân cụm bất đối xứng / Cô lập nhóm ngoại lai (Asymmetric Outlier Isolation)**.
- **Bản chất kinh tế TTCK Việt Nam:**
  1. Ward Linkage tối ưu hóa việc giảm thiểu tổng phương sai gộp khi hợp nhất các cụm (Minimum Variance). Khi đối diện với một thị trường có nhóm cổ phiếu "đầu tàu" sở hữu thanh khoản và quán tính giá vượt trội (heavy-tail), thuật toán sẽ ưu tiên gom toàn bộ các cổ phiếu đại trà vào một cụm lớn để hạn chế tăng phương sai nội cụm, và tách nhóm cổ phiếu thanh khoản cao thành một cụm riêng.
  2. Điểm Silhouette cao (trên 0.75) của Ward phản ánh khoảng cách tách rời rất lớn giữa nhóm cổ phiếu lõi thu hút dòng tiền và đại bộ phận thị trường, không đại diện cho cấu trúc phân chia đồng đều 50-50.

---

## VI. Khung Kết luận 3 Phần Bắt buộc

### 1. Phần A — Phán quyết Kỹ thuật (Technical Verdict)
- **Điểm mạnh toán học:** Ward Hierarchical thể hiện năng lực phân cụm hình học xuất sắc với **Median Silhouette = 0.7557** (cao nhất trong 3 phương án tại K = 2) và **Median Cluster Balance = 0.0677** (cải thiện đáng kể so với mức 0.0480 của K-Means).
- **Điểm hạn chế cần lưu ý:** Cấu trúc phân cụm vẫn tồn tại tính bất đối xứng tự nhiên do đặc thù phân phối dòng tiền lệch phải trên TTCK Việt Nam. Độ biến thiên Silhouette qua các tháng cao hơn K-Means.

### 2. Phần B — Bản chất Thị trường (Market Structure & Economics)
- Ward khắc họa rõ nét sự phân tầng cấu trúc của thị trường: một nhóm cổ phiếu hạt nhân có thanh khoản lớn và biến động theo xu hướng riêng biệt, đối lập với phần lớn cổ phiếu thanh khoản trung bình và thấp. Cơ chế cây phân bậc giúp Ward mở rộng được vùng dung nạp cổ phiếu ở cụm dẫn dắt một cách mượt mà hơn K-Means.

### 3. Phần C — Bàn giao cho Nhiệm vụ 10 (Stage Handoff)
- Mô hình **Ward Hierarchical được xác nhận hoàn thành đầy đủ Nhiệm vụ 7**, dữ liệu chẩn đoán đạt độ toàn vẹn 100%, sẵn sàng bước vào vòng so sánh đối đầu tại Nhiệm vụ 10 cùng K-Means Baseline và PCA + K-Means trên ma trận đánh đổi 5 tiêu chí.
