# Báo cáo Chuyên đề M2 — Nhiệm vụ 8: Phân tích Hồ sơ Cụm (Cluster Profiling)
**Mô hình phân tích:** Phương án 2 — Ward Hierarchical Clustering (Cấu hình tối ưu Global K = 2)  
**Khung thời gian thực hiện:** Development Window gồm 15 Snapshots (30/11/2023 – 24/01/2025)  
**Tác giả thực hiện:** Nhánh Ward Hierarchical — Milestone M2  

---

## I. Mục tiêu & Nguyên tắc Thực hiện

Nhiệm vụ 8 tiến hành giải mã bản chất kinh tế và cấu trúc vi mô của 2 cụm cổ phiếu (K = 2) được hình thành từ thuật toán Ward Hierarchical Clustering dựa trên **8 đặc trưng tài chính cốt lõi ở thang đo gốc (Unscaled Features)**.

### Nguyên tắc học thuật bất biến:
1. **Tiêu thụ Artifacts đã đóng băng:** Phân tích hoàn toàn trên file hồ sơ `cluster_profiles.csv` và tham số chuẩn hóa thị trường trích xuất trực tiếp từ `M2/artifacts/m2-task5-ward-v1/models/*.json` (đồng bộ hoàn toàn với K-Means), không chạy lại quá trình huấn luyện hay trích xuất đặc trưng.
2. **Đối chiếu đa chiều:** Đánh giá động lực phân cụm qua 4 nhóm yếu tố: Thanh khoản (`liquidity_21`), Rủi ro hệ thống (`beta_126`), Rủi ro biến động (`vol_63`, `mdd_126`) và Động lượng chuỗi thời gian (`mom_21`, `mom_63`, `mom_126`, `mom_252`).
3. **Ranh giới M2 / M3:** Hồ sơ cụm thuần túy mô tả hành vi thị trường và cấu trúc thanh khoản trong quá khứ, tuyệt đối không suy diễn thành khuyến nghị đầu tư danh mục (thuộc M3).

---

## II. Bảng Số liệu Thực chứng Chuẩn hóa

### Bảng 1: Tổng hợp Hồ sơ Đặc trưng theo Cụm (Kích thước 4 dòng x 10 cột chuẩn)
*Thanh khoản `liquidity_21_ty_vnd` tính theo tỷ VNĐ/phiên*

| aligned_cluster_id | size | liquidity_21_ty_vnd | beta_126 | vol_63 | mdd_126 | mom_21 | mom_63 | mom_126 | mom_252 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cụm 0 (Mean)** | 19.07 | **340.80** | 1.2842 | 0.2962 | -0.1921 | 0.0337 | 0.0847 | 0.1317 | **0.4068** |
| **Cụm 0 (Median)** | 16.00 | **332.43** | 1.2657 | 0.2959 | -0.1831 | 0.0307 | 0.0749 | 0.1057 | **0.4123** |
| **Cụm 1 (Mean)** | 355.27 | **12.78** | 0.5961 | 0.3534 | -0.2106 | 0.0130 | 0.0271 | 0.0532 | **0.1798** |
| **Cụm 1 (Median)** | 205.00 | **10.12** | 0.6031 | 0.3348 | -0.2170 | 0.0096 | 0.0359 | 0.0389 | **0.1712** |

---

### Bảng 2: So sánh Đối đầu giữa Cụm 0 và Cụm 1 (Kích thước 9 dòng x 4 cột chuẩn)

| Đặc trưng | Cụm 0 (Mean) | Cụm 1 (Mean) | Chênh lệch (Cụm 0 - Cụm 1) | Ý nghĩa kinh tế |
| :--- | :---: | :---: | :---: | :--- |
| **size** | 19.07 | 355.27 | **-336.20** | Cụm 0 là nhóm hạt nhân tinh gọn (bình quân 19 mã/tháng) |
| **liquidity_21 (tỷ VND)** | 340.80 | 12.78 | **+328.02** | Cụm 0 gấp gần 27 lần Cụm 1, áp đảo về thanh khoản |
| **beta_126** | 1.2842 | 0.5961 | **+0.6881** | Cụm 0 có tính đại diện và nhạy cảm cao với VNINDEX |
| **vol_63** | 0.2962 | 0.3534 | **-0.0572** | Cụm 0 ít rủi ro biến động phi hệ thống hơn Cụm 1 |
| **mdd_126** | -0.1921 | -0.2106 | **+0.0185** | Cụm 0 có mức sụt giảm tối đa nhẹ hơn |
| **mom_21** | 0.0337 | 0.0130 | **+0.0207** | Động lượng ngắn hạn 1 tháng vượt trội (+3.37% so với +1.30%) |
| **mom_63** | 0.0847 | 0.0271 | **+0.0576** | Động lượng trung hạn 3 tháng gấp hơn 3 lần (+8.47% so với +2.71%) |
| **mom_126** | 0.1317 | 0.0532 | **+0.0785** | Động lượng 6 tháng gấp 2.5 lần (+13.17% so với +5.32%) |
| **mom_252** | 0.4068 | 0.1798 | **+0.2270** | Động lượng dài hạn 1 năm vượt trội mạnh (+40.68% so với +17.98%) |

---

### Bảng 3: Chuỗi Thời gian Quy mô & Thanh khoản qua 15 Snapshots (Kích thước 15 dòng x 5 cột)

| Snapshot | Size Cụm 0 | Size Cụm 1 | Liquidity Cụm 0 (tỷ VND) | Liquidity Cụm 1 (tỷ VND) |
| :---: | :---: | :---: | :---: | :---: |
| **2023-11-30** | 9 | 133 | 201.23 | 8.90 |
| **2023-12-29** | 16 | 179 | 332.43 | 14.51 |
| **2024-01-31** | 17 | 179 | 295.17 | 14.27 |
| **2024-02-29** | 17 | 179 | 359.15 | 16.68 |
| **2024-03-29** | 36 | 161 | 275.24 | 13.80 |
| **2024-04-26** | 15 | 199 | 459.19 | 22.63 |
| **2024-05-31** | 31 | 190 | 280.60 | 14.09 |
| **2024-06-28** | 11 | 229 | 576.26 | 29.33 |
| **2024-07-31** | 42 | 205 | 194.94 | 9.57 |
| **2024-08-30** | 21 | 574 | 288.10 | 6.73 |
| **2024-09-30** | 12 | 594 | 423.18 | 8.69 |
| **2024-10-31** | 9 | 599 | 499.90 | 9.24 |
| **2024-11-29** | 33 | 747 | 214.75 | 3.56 |
| **2024-12-31** | 11 | 578 | 357.88 | 10.12 |
| **2025-01-24** | 6 | 583 | 353.99 | 9.65 |

---

## III. Trực quan hóa Chuẩn hóa (Visualization Contract)

### 1. Biểu đồ Radar (Radar Chart)
- **Đường dẫn lưu trữ:** `M2/artifacts/m2-evaluation-ward/radar_chart.png`
- **Thang đo:** Robust Z-Score giới hạn trong [-3, 3] kèm đường tròn nét đứt y = 0 biểu diễn Trung vị thị trường.
- **Đặc điểm hình thái:** Cụm 0 (màu đỏ) phình rộng vượt bậc ở các đỉnh `liquidity_21` (+61.62 trước khi clip), `beta_126` (+0.79), `mom_252` (+0.69) và `mom_63` (+0.53). Ngược lại, Cụm 1 (màu xanh) nằm bám sát tâm và đường trung vị thị trường y = 0.

### 2. Bản đồ nhiệt (Heatmap 2D)
- **Đường dẫn lưu trữ:** `M2/artifacts/m2-evaluation-ward/heatmap.png`
- **Cấu trúc:** Ma trận 2 hàng x 8 cột, hiển thị trực quan độ phân cách Z-Score:
  - Cụm 0 đạt sắc đỏ đậm ở thanh khoản (+3.00* clamped), hệ số beta (+0.79) và động lượng 1 năm (+0.69).
  - Cụm 1 giữ sắc xanh trung tính hoặc nhạt ở toàn bộ các đặc trưng (quanh 0.02 - 0.15).

---

## IV. Nhận định Tài chính & Rào chắn Học thuật (Profiling Rubrics)

### 1. Động lực Phân cụm Chính (Primary Driver Test)
- **Số liệu thực chứng:** Độ chênh lệch giữa Cụm 0 và Cụm 1 tập trung chủ yếu ở:
  1. **Thanh khoản (`liquidity_21`):** Cụm 0 đạt bình quân **340.80 tỷ VNĐ/phiên**, Cụm 1 chỉ đạt **12.78 tỷ VNĐ/phiên** (chênh lệch **+328.02 tỷ VNĐ/phiên**). Trên thang Robust Z-Score, Cụm 0 vượt trội với giá trị trung bình **+61.62**.
  2. **Động lượng dài hạn (`mom_252`):** Cụm 0 đạt **+40.68%**, Cụm 1 đạt **+17.98%** (chênh lệch **+22.70%**).
  3. **Hệ số rủi ro hệ thống (`beta_126`):** Cụm 0 đạt **1.28**, Cụm 1 đạt **0.60** (chênh lệch **+0.69**).
- **Phán quyết:** **Thanh khoản giao dịch (Liquidity)** là động lực phân cụm chi phối số 1, tiếp nối bởi Động lượng 12 tháng và Rủi ro hệ thống Beta.

### 2. Định danh Chân dung Kinh tế (Economic Persona Mapping)
- Căn cứ vị trí đối chiếu với đường trung vị thị trường (Z = 0):
  - **Cụm 0:** Được định danh là **"Nhóm Cổ phiếu Lõi Dẫn dắt / Siêu Thanh khoản & Động lượng Vượt trội (Core High-Momentum & High-Liquidity Leaders)"**. Đây là nhóm cổ phiếu trụ cột thu hút dòng tiền lớn nhất của thị trường.
  - **Cụm 1:** Được định danh là **"Nhóm Cổ phiếu Phổ thông Đại trà / Thanh khoản Thấp (Broad Market / Low-Liquidity Majority)"**. Chiếm đại đa số mã trên sàn nhưng giá trị giao dịch phân tán và quán tính giá khiêm tốn.

### 3. Tính Nhất quán theo Thời gian (Profile Temporal Consistency)
- Cụm 0 duy trì vị thế dẫn dắt thanh khoản và động lượng dài hạn ở toàn bộ 15 tháng. 
- Tại các giai đoạn thị trường điều chỉnh (tháng 04/2024 và 07/2024), quy mô Cụm 0 của Ward mở rộng linh hoạt lên 36 - 42 mã (thay vì co cụm quá mức như K-Means). Dù động lượng 1 tháng có nhịp suy giảm tạm thời do Beta cao (1.28), nhưng động lượng trung dài hạn (6 tháng, 12 tháng) của Cụm 0 vẫn luôn vượt trội so với Cụm 1.

---

## V. Khung Kết luận 3 Phần Bắt buộc

### 1. Phần A — Chân dung Kinh tế (Economic Persona)
- Ward Hierarchical đã tách bạch thị trường thành 2 tầng cấu trúc rõ rệt: Cụm 0 (bình quân 19 mã) là nhóm tinh hoa dẫn dắt thanh khoản và xu hướng giá; Cụm 1 (bình quân 355 mã) là tầng lớp phổ thông của thị trường chứng khoán Việt Nam.
- So với K-Means (15 mã), Ward mở rộng tập cổ phiếu dẫn dắt lên 19 mã, mang lại độ bao phủ tốt hơn cho các cơ hội đầu tư.

### 2. Phần B — Động lực Phân tách Chính (Core Driver)
- Bằng chứng thực nghiệm khẳng định Thanh khoản (`liquidity_21`) kết hợp với Động lượng dài hạn (`mom_252`) và Beta là 3 trụ cột phân định nhóm cổ phiếu dẫn dắt. Ward phản ánh xuất sắc sự kết hợp giữa quy mô dòng tiền và quán tính tăng giá.

### 3. Phần C — Tính Khả thi cho Milestone M3 (M3 Feasibility)
- Cụm 0 của Ward đạt thanh khoản trung bình 340.8 tỷ VNĐ/phiên với số lượng mã bình quân 19 mã. Đây là tiền đề cực kỳ thuận lợi cho việc thiết kế danh mục đầu tư ở M3, đảm bảo quy mô hấp thụ vốn tốt, giảm thiểu nguy cơ trượt giá (slippage) và rủi ro thanh khoản kém.
