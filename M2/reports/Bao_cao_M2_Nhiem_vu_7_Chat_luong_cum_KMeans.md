# Báo cáo Chuyên đề M2 — Nhiệm vụ 7: Đánh giá Chất lượng Cụm (Cluster Quality Evaluation)
**Mô hình phân tích:** Phương án 1 — K-Means Baseline (Cấu hình tối ưu Global K = 2)  
**Khung thời gian thực hiện:** Development Window gồm 15 Snapshots (30/11/2023 – 24/01/2025)  
**Tác giả thực hiện:** Nhánh K-Means Baseline — Milestone M2  

---

## I. Mục tiêu & Cơ sở Phương pháp luận

Nhiệm vụ 7 tiến hành đánh giá thực chứng chất lượng hình học và độ phân tách toán học của cấu trúc phân nhóm 2 cụm ($K=2$) được tạo bởi thuật toán K-Means Baseline. Việc đánh giá được thực hiện độc lập hoàn toàn trên 15 snapshots cuối tháng thuộc Cửa sổ phát triển (Development Window: từ 30/11/2023 đến 24/01/2025).

### Các nguyên tắc phương pháp luận bắt biến:
1. **Tiêu thụ Artifacts đã đóng băng:** Tầng đánh giá chất lượng chỉ nạp dữ liệu chẩn đoán `diagnostics.csv` sinh ra từ Nhiệm vụ 4, tuyệt đối không huấn luyện lại mô hình hoặc tinh chỉnh tham số hồi quy.
2. **Khảo sát chuyên sâu cấu hình K = 2:** Trích xuất duy nhất 15 dòng dữ liệu ứng với $K=2$ (đã được khóa từ Nhiệm vụ 3) để phân tích diễn biến qua chuỗi thời gian.
3. **Ranh giới M2 / M3 nghiêm ngặt:** Đánh giá chất lượng cụm hoàn toàn bằng 5 chỉ số không gian nội bộ (Internal Distance Metrics). Tuyệt đối không sử dụng tỷ suất sinh lời, Sharpe ratio, Sortino, ROI hay bất kỳ chỉ số danh mục nào (thuộc Milestone M3).

---

## II. Phân cấp Tiêu chí Đánh giá theo Kế hoạch Dự án

Theo chuẩn `DELTA_UNIFIED_PROJECT_PLAN.md` và `M2/Ke_hoach_M2_Phan_cum_co_phieu.md`:
- **Tiêu chí cấp 1 (Primary Criterion):** `Median Silhouette cao nhất`. Thước đo cao nhất chứng minh mức độ phân tách rõ ràng giữa 2 nhóm cổ phiếu.
- **Tiêu chí phá vỡ thế cân bằng (Secondary Tie-breaker):** `Median Davies-Bouldin thấp hơn`. Dùng khi Silhouette giữa các mô hình tương đương.
- **Tiêu chí kiểm định an toàn (Sanity Diagnostics):** `Calinski-Harabasz` và `Cluster Balance`. Giúp cảnh báo nguy cơ phân cụm bị chi phối bởi các cổ phiếu dị biệt hoặc hiện tượng phân mảnh cụm (fragmentation).

---

## III. Bảng Số liệu Thực chứng Chuẩn hóa

### Bảng 1: Tóm tắt Thống kê Chất lượng Cụm K=2 (Kích thước 5 dòng x 7 cột chuẩn)
*Nguồn dữ liệu: `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv`*

| metric | n_total | n_available | mean | median | minimum | maximum |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **silhouette** | 15 | 15 | 0.791753 | **0.748492** | 0.636868 | 0.949859 |
| **davies_bouldin** | 15 | 15 | 0.506540 | **0.521899** | 0.356337 | 0.747218 |
| **calinski_harabasz** | 15 | 15 | 686.291244 | **316.391783** | 160.006764 | 2046.647682 |
| **inertia** | 15 | 15 | 66497.669865 | **1706.906717** | 1304.124507 | 329664.086867 |
| **cluster_balance** | 15 | 15 | 0.054942 | **0.048035** | 0.010363 | 0.094972 |

---

### Bảng 2: Chi tiết Chất lượng qua 15 Snapshots tại K=2 (Kích thước 15 dòng x 6 cột chuẩn)

| Snapshot | Silhouette | DB | CH | Inertia | Balance |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2023-11-30** | 0.762987 | 0.549272 | 210.950916 | 1304.124507 | 0.067669 |
| **2023-12-29** | 0.755722 | 0.493906 | 378.398170 | 1396.643410 | 0.089385 |
| **2024-01-31** | 0.695411 | 0.587799 | 233.930208 | 1520.946055 | 0.094972 |
| **2024-02-29** | 0.723123 | 0.513532 | 316.391783 | 1480.098520 | 0.094972 |
| **2024-03-29** | 0.650054 | 0.627474 | 168.131090 | 1425.637654 | 0.082418 |
| **2024-04-26** | 0.712929 | 0.564229 | 241.057790 | 1668.300555 | 0.070000 |
| **2024-05-31** | 0.684901 | 0.599560 | 210.151850 | 1706.906717 | 0.072816 |
| **2024-06-28** | 0.748492 | 0.534333 | 249.860699 | 2158.608251 | 0.048035 |
| **2024-07-31** | 0.636868 | 0.747218 | 160.006764 | 2215.034630 | 0.073913 |
| **2024-08-30** | 0.903261 | 0.475227 | 919.686722 | 122029.496743 | 0.036585 |
| **2024-09-30** | 0.931137 | 0.356337 | 2046.647682 | 102811.933750 | 0.027119 |
| **2024-10-31** | 0.937810 | 0.366466 | 1805.755625 | 135674.584196 | 0.021849 |
| **2024-11-29** | 0.949859 | 0.392866 | 1517.755371 | 329664.086867 | 0.010363 |
| **2024-12-31** | 0.905533 | 0.391856 | 965.060327 | 53268.069172 | 0.019031 |
| **2025-01-24** | 0.874242 | 0.521899 | 894.552010 | 47868.556473 | 0.036972 |

---

## IV. Phân tích 5 Chỉ số & Trực quan hóa

### 1. Silhouette Score qua 15 tháng (Biểu đồ 7.1)
- **Giá trị thực tế:** Median Silhouette đạt **0.7485**, Mean đạt **0.7918**, biến động từ cực tiểu **0.6369** (31/07/2024) đến cực đại **0.9499** (29/11/2024).
- **Nhận định:** Điểm Silhouette luôn duy trì vượt trội so với ngưỡng chấp nhận học thuật (> 0.50) và ngưỡng xuất sắc (> 0.70) ở 11/15 tháng. Sự bùng nổ điểm Silhouette từ tháng 08/2024 (> 0.90) gắn liền với việc Universe mở rộng mạnh (hơn 570 mã), khiến khoảng cách giữa nhóm thiểu số siêu thanh khoản và nhóm đại trà càng trở nên cực đoan.

### 2. Davies-Bouldin Index qua 15 tháng (Biểu đồ 7.2)
- **Giá trị thực tế:** Median DB đạt **0.5219**, Mean đạt **0.5065**, biên độ [0.3563, 0.7472].
- **Nhận định:** DB Index càng thấp chứng tỏ cụm càng gọn và xa nhau. K-Means đạt chỉ số DB rất thấp và ổn định quanh mức 0.36 - 0.55, khẳng định độ nén nội cụm cao.

### 3. Calinski-Harabasz Index qua 15 tháng (Biểu đồ 7.3)
- **Giá trị thực tế:** Median CH đạt **316.39**, Mean đạt **686.29**, đỉnh điểm đạt **2,046.65** vào tháng 09/2024.
- **Nhận định:** Phương sai liên cụm (between-cluster variance) áp đảo hoàn toàn phương sai nội cụm (within-cluster variance), phản ánh sự phân tách không gian cực kỳ mạnh mẽ.

### 4. Quán tính nội cụm Inertia qua 15 tháng (Biểu đồ 7.4)
- **Giá trị thực tế:** Median đạt **1,706.91**, Min là **1,304.12** (11/2023), Max lên tới **329,664.09** (11/2024).
- **Rào chắn học thuật (Inertia Caveat Rule):** Inertia tỷ lệ thuận với số lượng cổ phiếu quan sát $N$. Trong giai đoạn đầu ($N \approx 142 - 247$ mã), Inertia rất thấp (< 2,300). Từ tháng 08/2024, khi dữ liệu C8 mở rộng $N$ lên $595 - 780$ mã, Inertia vọt lên hàng chục ngàn. Đây là hiện tượng toán học tự nhiên do số lượng điểm dữ liệu tăng, **tuyệt đối không so sánh Inertia tuyệt đối giữa các tháng có $N$ khác nhau**.

### 5. Tỷ số Cân bằng Cụm Cluster Balance qua 15 tháng (Biểu đồ 7.5)
- **Giá trị thực tế:** Median Balance đạt **0.0480** (4.80%), Mean đạt **0.0549**, Min là **0.0104** (11/2024), Max là **0.0950** (01/2024 và 02/2024).
- **Cảnh báo học thuật:** Tỷ số Balance luôn dưới 0.10 ở toàn bộ 15 tháng, và có 8/15 tháng nằm dưới ngưỡng cảnh báo tối thiểu 5% (0.05). Cụm nhỏ chỉ tập hợp từ 8 đến 21 cổ phiếu, trong khi cụm lớn chứa từ 133 đến 772 cổ phiếu.

---

## V. Nhận định Kinh tế & Rào chắn Học thuật (Diagnostic Rubrics)

### 1. Phán quyết Kiểm định Cân bằng (Balance Diagnostic Test — Kịch bản A)
- Căn cứ bộ quy tắc phân tích theo điều kiện, với `Cluster Balance < 0.10` và tỷ trọng cụm nhỏ chiếm `< 5%` toàn thị trường, kết luận chính thức: K-Means Baseline rơi vào **Kịch bản A — Phân cụm bất đối xứng / Cô lập nhóm ngoại lai (Asymmetric Outlier Isolation)**.
- **Bản chất kinh tế TTCK Việt Nam:**
  1. Thị trường chứng khoán Việt Nam có mức độ tập trung dòng tiền rất cao. Một nhóm nhỏ khoảng 10 – 20 cổ phiếu vốn hóa lớn/siêu thanh khoản (VN30, các mã dẫn dắt ngành ngân hàng, chứng khoán, thép) chiếm phần lớn giá trị giao dịch của toàn bộ sàn giao dịch.
  2. Các cổ phiếu này có các chỉ số động lượng, biến động và thanh khoản vượt xa nhiều lần mức trung vị thị trường (heavy tails).
  3. Do nguyên tắc thiết kế của dự án là **không sử dụng Clipping/Winsorization** (để giữ nguyên bản chất thực của dữ liệu), thuật toán K-Means vốn tối ưu tổng bình phương khoảng cách Euclid bị "kéo tâm" mạnh mẽ về phía các quan sát ngoại lai này, dẫn đến việc tách nhóm 10 - 20 mã này thành Cụm 0 riêng biệt và đẩy toàn bộ thị trường còn lại vào Cụm 1.
- **Cảnh báo học thuật về Silhouette:** Điểm Silhouette cao kỷ lục (0.75 - 0.95) phản ánh **khoảng cách hình học cực xa giữa nhóm ngoại lai và phần còn lại của thị trường**, không thể ngộ nhận rằng thị trường đang phân hóa thành 2 nửa cân bằng đồng đều.

---

## VI. Khung Kết luận 3 Phần Bắt buộc

### 1. Phần A — Phán quyết Kỹ thuật (Technical Verdict)
- **Điểm mạnh toán học:** K-Means Baseline thể hiện năng lực phân tách hình học vượt trội với **Median Silhouette = 0.7485** và **Median DB Index = 0.5219**. Ranh giới giữa 2 cụm sắc nét, độ nén nội cụm rất cao.
- **Điểm yếu cố hữu:** Tính mất cân bằng quy mô cực đoan (**Median Balance = 0.0480**). Thuật toán không tạo ra cấu trúc phân đôi đồng đều mà hoạt động như một cơ chế phát hiện và cô lập nhóm ngoại lai.

### 2. Phần B — Bản chất Thị trường (Market Structure & Economics)
- K-Means phản ánh chân thực cấu trúc dòng tiền "đầu cá mập" trên TTCK Việt Nam: sự phân hóa sâu sắc giữa một nhóm thiểu số cổ phiếu dẫn dắt thị trường (High Momentum / High Liquidity / High Beta) và đại bộ phận cổ phiếu phổ thông ít được chú ý.

### 3. Phần C — Bàn giao cho Nhiệm vụ 10 (Stage Handoff)
- Mô hình **K-Means Baseline được xác nhận hoàn thành đầy đủ Nhiệm vụ 7**, dữ liệu chẩn đoán đạt độ toàn vẹn 100%, sẵn sàng bước vào vòng so sánh đối đầu tại Nhiệm vụ 10 với Ward Hierarchical và PCA + K-Means trên ma trận đánh đổi 5 tiêu chí.
