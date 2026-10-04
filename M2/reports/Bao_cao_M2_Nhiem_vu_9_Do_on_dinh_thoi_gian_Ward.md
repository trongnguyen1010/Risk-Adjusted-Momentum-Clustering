# Báo cáo Chuyên đề M2 — Nhiệm vụ 9: Đánh giá Độ ổn định theo Thời gian (Temporal Stability)
**Mô hình phân tích:** Phương án 2 — Ward Hierarchical Clustering (Cấu hình tối ưu Global K = 2)  
**Khung thời gian thực hiện:** Development Window gồm 14 Cặp Snapshot liên tiếp (30/11/2023 – 24/01/2025)  
**Tác giả thực hiện:** Nhánh Ward Hierarchical — Milestone M2  

---

## I. Mục tiêu & Cơ sở Phương pháp luận

Nhiệm vụ 9 tiến hành đánh giá tính bền vững cấu trúc và độ ổn định của phân hoạch 2 cụm (K = 2) tạo bởi thuật toán Ward Hierarchical Clustering qua 14 cặp snapshot hàng tháng liên tiếp thuộc Cửa sổ phát triển (từ 30/11/2023 đến 24/01/2025).

### Các nguyên tắc phương pháp luận bất biến:
1. **Tiêu thụ Artifacts đã đóng băng:** Tầng đánh giá chỉ đọc trực tiếp các file kết quả độ ổn định thời gian đã xuất xưởng tại `M2/artifacts/m2-evaluation-ward/` (`temporal_stability.csv`, `transition_matrices.csv`, `centroid_drift.csv`). Tuyệt đối không gọi lại backend module hay fit lại mô hình.
2. **Không đánh đồng với Dynamic Clustering:** Việc theo dõi K-Means hay Ward độc lập qua từng tháng kèm theo đo lường ARI/NMI là kỹ thuật "Temporal Stability Tracking trên Static Model", nghiêm cấm gọi đây là Dynamic Clustering (vốn đòi hỏi mô hình thích ứng động trực tiếp).
3. **Reset chuỗi tại Gap hệ thống:** Chuỗi đánh giá dừng lại trước khoảng đứt gãy tháng 02/2025, tuyệt đối không tạo liên kết giả định qua điểm gián đoạn dữ liệu và không truy cập vào Final Holdout.

---

## II. Bảng Số liệu Thực chứng Chuẩn hóa

### Bảng 1: Tổng hợp Chỉ số Temporal Toàn kỳ (Kích thước 4 dòng x 6 cột chuẩn)
*Nguồn dữ liệu: `M2/artifacts/m2-evaluation-ward/temporal_stability.csv`*

| metric | mean | median | minimum | maximum |
| :--- | :---: | :---: | :---: | :---: |
| **ari** | 0.528468 | **0.540134** | 0.201402 | 0.814349 |
| **nmi** | 0.444265 | **0.490710** | 0.165997 | 0.702758 |
| **persistence_probability** | 0.978135 | **0.985918** | 0.923077 | 0.995807 |
| **migration_rate** | 0.021865 | **0.014082** | 0.004193 | 0.076923 |

---

### Bảng 2: Ma trận Chuyển dịch Cụm Tích lũy 2x2 (Kích thước 4 dòng x 5 cột chuẩn)
*Nguồn dữ liệu: `M2/artifacts/m2-evaluation-ward/transition_matrices.csv`*

| from_cluster | to_cluster | transition_count | total_from | transition_rate |
| :---: | :---: | :---: | :---: | :---: |
| **0** | **0** | **172** | 231 | **74.45%** (Quán tính Cụm 0) |
| **0** | **1** | **59** | 231 | **25.55%** (Cổ phiếu rớt khỏi Cụm 0) |
| **1** | **0** | **59** | 4,586 | **1.29%** (Cổ phiếu thăng hạng vào Cụm 0) |
| **1** | **1** | **4,527** | 4,586 | **98.71%** (Quán tính Cụm 1) |

---

### Bảng 3: Độ lệch Tâm Tuyệt đối Trung bình trên 8 Đặc trưng (Centroid Drift Summary)
*Nguồn dữ liệu: `M2/artifacts/m2-evaluation-ward/centroid_drift.csv`*

| feature | mean_absolute_drift |
| :--- | :---: |
| **mom_21** | 0.0215 |
| **mom_63** | 0.0381 |
| **mom_126** | 0.0482 |
| **mom_252** | 0.0694 |
| **vol_63** | 0.0341 |
| **mdd_126** | 0.0258 |
| **beta_126** | 0.1124 |
| **liquidity_21 (tỷ VND)** | 85.12 |

---

### Bảng 4: Theo dõi Biến động Universe qua 14 Cặp tháng (Kích thước 14 dòng x 5 cột chuẩn)

| transition_pair | n_common | n_entry | n_exit | universe_turnover |
| :---: | :---: | :---: | :---: | :---: |
| **2023-11-30 -> 2023-12-29** | 142 | 53 | 0 | 27.18% |
| **2023-12-29 -> 2024-01-31** | 195 | 1 | 0 | 0.51% |
| **2024-01-31 -> 2024-02-29** | 196 | 0 | 0 | 0.00% |
| **2024-02-29 -> 2024-03-29** | 196 | 1 | 0 | 0.51% |
| **2024-03-29 -> 2024-04-26** | 197 | 17 | 0 | 7.94% |
| **2024-04-26 -> 2024-05-31** | 214 | 7 | 0 | 3.17% |
| **2024-05-31 -> 2024-06-28** | 221 | 19 | 0 | 7.92% |
| **2024-06-28 -> 2024-07-31** | 240 | 7 | 0 | 2.83% |
| **2024-07-31 -> 2024-08-30** | 247 | 348 | 0 | 58.49% |
| **2024-08-30 -> 2024-09-30** | 595 | 11 | 0 | 1.82% |
| **2024-09-30 -> 2024-10-31** | 606 | 2 | 0 | 0.33% |
| **2024-10-31 -> 2024-11-29** | 608 | 172 | 0 | 22.05% |
| **2024-11-29 -> 2024-12-31** | 589 | 0 | 191 | 24.49% |
| **2024-12-31 -> 2025-01-24** | 589 | 0 | 0 | 0.00% |

---

## III. Cơ chế Reset Temporal Chain tại Gap Dữ liệu

- Chuỗi thực nghiệm nối tiếp liên tục qua 14 cặp tháng và được ngắt chuỗi nghiêm ngặt tại mốc 24/01/2025 (trước điểm đứt gãy hệ thống tháng 02/2025 do chuyển đổi nguồn dữ liệu C8).
- Không thực hiện tính nối chỉ số ARI/NMI qua khoảng đứt gãy này nhằm đảm bảo tính toàn vẹn của chuỗi thời gian thực chứng.

---

## IV. Trực quan hóa Chuẩn hóa (Visualization Contract)

### 1. Biểu đồ Đường Xu hướng Ổn định Đa bảng (Multi-panel Temporal Trends)
- **Đường dẫn lưu trữ:** `M2/artifacts/m2-evaluation-ward/temporal_trends.png`
- **Hình thái thể hiện:** Biểu đồ gồm 4 bảng hiển thị: Quỹ đạo ARI/NMI qua 14 cặp tháng; Xác suất bền vững Persistence; Tỷ lệ chuyển cụm Migration Rate; và Biến động số lượng Entry/Exit.
- **Điểm nhấn:** Đường Persistence duy trì ổn định trên 92% ở toàn bộ các tháng. Đường ARI có xu hướng dao động mạnh quanh mức 0.54, đặc biệt chịu ảnh hưởng tại các cặp tháng có thị trường biến động hoặc Universe mở rộng đột biến.

### 2. Heatmap Ma trận Chuyển dịch Cụm (Transition Matrix Heatmap)
- **Đường dẫn lưu trữ:** `M2/artifacts/m2-evaluation-ward/transition_heatmap.png`
- **Đặc điểm hình thái:** Ma trận xác suất chuyển đổi 2x2. Đường chéo chính thể hiện tính lưu giữ thành viên mạnh mẽ: Cụm 0 giữ lại 74.45% và Cụm 1 giữ lại 98.71%. Tỷ lệ rớt cụm từ 0 sang 1 là 25.55%, phản ánh cơ chế chọn lọc tự nhiên của dòng tiền.

---

## V. Nhận định Tài chính & Rào chắn Học thuật (Stability Rubrics)

### 1. Đánh giá Quán tính Cụm (Persistence Diagnostic Rule)
- **Số liệu:** Median Persistence đạt **98.59%**, Mean đạt **97.81%**, thấp nhất đạt **92.31%**.
- **Nhận định:** Cấu trúc phân cụm của Ward thể hiện quán tính thành viên rất cao. Khi một cổ phiếu đã được gán vào Cụm 1 (đại trà), xác suất ở lại Cụm 1 trong tháng kế tiếp lên tới 98.71%. Đối với Cụm 0 (dẫn dắt), tỷ lệ giữ chân đạt 74.45%, khẳng định nhóm dẫn dắt có tính kế thừa ổn định qua chu kỳ kinh doanh.

### 2. Đánh giá Chi phí Giao dịch Tiềm tàng ở M3 (Turnover Impact Rule)
- **Số liệu:** Median Migration Rate chỉ là **1.41%**, Maximum Migration Rate chỉ là **7.69%** (toàn bộ 14 cặp tháng đều nằm dưới ngưỡng cảnh báo rủi ro 15%).
- **Ý nghĩa đối với M3:** Tỷ lệ đổi nhãn giữa các tháng rất thấp là tín hiệu ban đầu thuận lợi cho việc kiểm soát chi phí giao dịch và vòng quay danh mục (Turnover) khi thiết kế chiến lược đầu tư ở Milestone M3.

### 3. Phân tích Cú sốc Thị trường (Market Shock Analysis)
Năm cặp tháng ghi nhận chỉ số ARI thấp hơn 0.50 gắn liền với các biến cố vĩ mô và nhịp điều chỉnh của thị trường:
1. **Cặp 03/2024 -> 04/2024 (ARI = 0.4437):** Trùng với tháng VN-Index sụt giảm 5.8% (tháng giảm mạnh nhất trong 6 tháng đầu năm 2024 theo báo cáo Vietcap), làm tái cơ cấu mạnh mẽ nhóm cổ phiếu dẫn dắt.
2. **Cặp 06/2024 -> 07/2024 (ARI = 0.4079):** Trùng nhịp điều chỉnh 4.8% của VN-Index sau khi tiệm cận mốc tâm lý 1.300 điểm.
3. **Cặp 10/2024 -> 11/2024 (ARI = 0.3541):** Trùng giai đoạn biến động mạnh trước bầu cử Mỹ và nhịp điều chỉnh giảm 4.7% của thị trường Việt Nam.
4. **Cặp 07/2024 -> 08/2024 (ARI = 0.2014):** Điểm trũng ARI phản ánh việc Universe mở rộng đột biến từ 247 mã lên 595 mã (bổ sung hơn 348 mã mới từ nguồn dữ liệu C8), làm xáo trộn cấu trúc phân hoạch ban đầu.

---

## VI. Khung Kết luận 3 Phần Bắt buộc

### 1. Phần A — Phán quyết Độ ổn định (Stability Verdict)
- **Kết luận:** Ward Hierarchical thể hiện **độ bền vững thành viên xuất sắc** (Median Persistence = 98.59%, Median Migration = 1.41%). Mức độ ổn định nhãn phân hoạch (Median ARI = 0.5401, Median NMI = 0.4907) đạt mức khá, phản ánh đúng nhịp co giãn tự nhiên của cấu trúc cây phân bậc khi thị trường biến động.

### 2. Phần B — Độ bền Dòng tiền & Tác động Turnover (Cash Flow Persistence & Turnover)
- Cụm 0 duy trì tỷ lệ kế thừa thành viên đạt 74.45% qua 14 cặp tháng. Điều này chứng minh dòng tiền lớn không rút đi đột ngột mà duy trì sự hiện diện bền bỉ ở nhóm cổ phiếu hạt nhân. Tỷ lệ luân chuyển thấp (1.41%) là tiền đề rất tốt để giảm thiểu chi phí tái cơ cấu danh mục ở M3.

### 3. Phần C — Bàn giao cho Nhiệm vụ 10 (Stage Handoff)
- Mô hình **Ward Hierarchical được xác nhận hoàn thành đầy đủ Nhiệm vụ 9**, bộ dữ liệu đo lường độ ổn định thời gian đạt chuẩn toàn vẹn 100%, sẵn sàng bàn giao làm nguyên liệu đầu vào cho Nhiệm vụ 10 để so sánh đối đầu trực diện cùng K-Means Baseline và PCA + K-Means.
