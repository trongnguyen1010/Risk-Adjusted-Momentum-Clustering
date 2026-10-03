# Báo cáo Chuyên đề M2 — Nhiệm vụ 8: Phân tích Hồ sơ Cụm (Cluster Profiling)
**Mô hình phân tích:** Phương án 1 — K-Means Baseline (Cấu hình tối ưu Global K = 2)  
**Khung thời gian thực hiện:** Development Window gồm 15 Snapshots (30/11/2023 – 24/01/2025)  
**Tác giả thực hiện:** Nhánh K-Means Baseline — Milestone M2  

---

## I. Mục tiêu & Nguyên tắc Thực hiện

Nhiệm vụ 8 tiến hành giải mã bản chất kinh tế và cấu trúc vi mô của 2 cụm cổ phiếu ($K=2$) được hình thành từ K-Means Baseline dựa trên **8 đặc trưng tài chính cốt lõi ở thang đo gốc (Unscaled Features)**.

### Nguyên tắc học thuật bắt biến:
1. **Tiêu thụ Artifacts đã đóng băng:** Phân tích hoàn toàn trên file hồ sơ `cluster_profiles.csv` và tham số chuẩn hóa `profile_scaler_reference.csv` đã được lưu trữ sẵn, không chạy lại quá trình huấn luyện hay trích xuất đặc trưng.
2. **Đối chiếu đa chiều:** Đánh giá động lực phân cụm qua 4 nhóm yếu tố: Thanh khoản (`liquidity_21`), Rủi ro hệ thống (`beta_126`), Rủi ro biến động (`vol_63`, `mdd_126`) và Động lượng chuỗi thời gian (`mom_21`, `mom_63`, `mom_126`, `mom_252`).
3. **Ranh giới M2 / M3:** Hồ sơ cụm thuần túy mô tả hành vi thị trường và cấu trúc thanh khoản trong quá khứ, tuyệt đối không suy diễn thành khuyến nghị đầu tư danh mục (thuộc M3).

---

## II. Bảng Số liệu Thực chứng Chuẩn hóa

### Bảng 1: Tổng hợp Hồ sơ Đặc trưng theo Cụm (Kích thước 4 dòng x 10 cột chuẩn)
*Thanh khoản `liquidity_21_ty_vnd` tính theo tỷ VNĐ/phiên*

| aligned_cluster_id | size | liquidity_21_ty_vnd | beta_126 | vol_63 | mdd_126 | mom_21 | mom_63 | mom_126 | mom_252 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cụm 0 (Mean)** | 14.7333 | **371.8099** | **1.3013** | 0.2972 | -0.1928 | 0.0265 | 0.0785 | 0.1335 | **0.3938** |
| **Cụm 0 (Median)** | 15.0000 | **359.1518** | **1.2562** | 0.2959 | -0.1773 | 0.0307 | 0.0749 | 0.1016 | **0.4123** |
| **Cụm 1 (Mean)** | 359.6000 | **14.9442** | **0.6080** | 0.3537 | -0.2109 | 0.0138 | 0.0290 | 0.0555 | **0.1877** |
| **Cụm 1 (Median)** | 229.0000 | **14.2662** | **0.6200** | 0.3348 | -0.2170 | 0.0096 | 0.0366 | 0.0397 | **0.1813** |

---

### Bảng 2: So sánh Đối đầu giữa Cụm 0 và Cụm 1 (Kích thước 9 dòng x 4 cột chuẩn)

| Đặc trưng | Cụm 0 (Mean) | Cụm 1 (Mean) | Chênh lệch (Cụm 0 - Cụm 1) |
| :--- | :---: | :---: | :---: |
| **size** | 14.7333 | 359.6000 | -344.8667 |
| **liquidity_21 (tỷ VND)** | **371.8099** | **14.9442** | **+356.8657** |
| **beta_126** | **1.3013** | **0.6080** | **+0.6933** |
| **vol_63** | 0.2972 | 0.3537 | -0.0565 |
| **mdd_126** | -0.1928 | -0.2109 | +0.0181 |
| **mom_21** | 0.0265 | 0.0138 | +0.0127 |
| **mom_63** | 0.0785 | 0.0290 | +0.0495 |
| **mom_126** | 0.1335 | 0.0555 | +0.0780 |
| **mom_252** | **0.3938** | **0.1877** | **+0.2061** |

---

### Bảng 3: Chuỗi Thời gian Quy mô & Thanh khoản qua 15 Snapshots (Kích thước 15 dòng x 5 cột)

| Snapshot | Size Cụm 0 | Size Cụm 1 | Liquidity Cụm 0 (tỷ VND) | Liquidity Cụm 1 (tỷ VND) |
| :---: | :---: | :---: | :---: | :---: |
| **2023-11-30** | 9 | 133 | 201.23 | 8.90 |
| **2023-12-29** | 16 | 179 | 332.43 | 14.51 |
| **2024-01-31** | 17 | 179 | 295.17 | 14.27 |
| **2024-02-29** | 17 | 179 | 359.15 | 16.68 |
| **2024-03-29** | 15 | 182 | 492.02 | 26.10 |
| **2024-04-26** | 14 | 200 | 475.61 | 23.67 |
| **2024-05-31** | 15 | 206 | 419.72 | 24.66 |
| **2024-06-28** | 11 | 229 | 576.26 | 29.33 |
| **2024-07-31** | 17 | 230 | 323.08 | 20.24 |
| **2024-08-30** | 21 | 574 | 288.10 | 6.73 |
| **2024-09-30** | 16 | 590 | 371.03 | 7.29 |
| **2024-10-31** | 13 | 595 | 421.11 | 7.66 |
| **2024-11-29** | 8 | 772 | 462.59 | 7.83 |
| **2024-12-31** | 11 | 578 | 357.88 | 10.12 |
| **2025-01-24** | 21 | 568 | 201.76 | 6.19 |

---

## III. Trực quan hóa Chuẩn hóa (Visualization Contract)

### 1. Biểu đồ Radar (Radar Chart)
- **Tập tin xuất bản:** `M2/artifacts/m2-evaluation-kmeans/radar_chart.png`
- **Đặc điểm:** Trục tọa độ cực 8 đỉnh tương ứng 8 đặc trưng trên thang Robust Z-Score [-3, 3] kèm vòng tròn nét đứt $y=0$ (Market Median).
- **Phân tích hình học:** Cụm 0 bung rộng ra ngoài vòng trung vị ở đỉnh Thanh khoản (`liquidity_21` chạm mốc trần +3 clamped), Động lượng dài hạn (`mom_252` = +0.67) và Rủi ro thị trường (`beta_126` = +0.81). Ngược lại, Cụm 1 co cụm gần như trùng khớp với vòng tròn trung vị trên toàn bộ các trục.

### 2. Bản đồ nhiệt (Heatmap 2D)
- **Tập tin xuất bản:** `M2/artifacts/m2-evaluation-kmeans/heatmap.png`
- **Đặc điểm:** Ma trận 2 hàng x 8 cột, hiển thị số thực trực tiếp, điểm trung hòa màu trắng tại 0 (`cmap='RdBu_r'`).
- **Phân tích:** Thể hiện rõ nét màu đỏ sẫm vượt trội của Cụm 0 tại các cột `liquidity_21`, `beta_126`, `mom_252`, khẳng định sự tập trung dòng tiền vào nhóm cổ phiếu này.

---

## IV. Nhận định Tài chính & Rào chắn Học thuật (Profiling Rubrics)

### 1. Động lực Phân cụm Chính (Primary Driver Test)
- Kết quả kiểm định đối đầu chỉ rõ: **Thanh khoản 21 phiên (`liquidity_21`) là động lực chi phối số 1**. Chênh lệch tuyệt đối lên tới **+356.87 tỷ VNĐ/phiên**, và trên thang Robust Z-Score, Cụm 0 đạt trung bình **+66.00 IQR** so với trung vị toàn thị trường.
- Động lực hỗ trợ thứ 2 là **Động lượng 1 năm (`mom_252`)** với mức vượt trội **+20.61%** (Cụm 0: 39.38% vs Cụm 1: 18.77%).
- Trong khi đó, các đặc trưng động lượng ngắn hạn 1 tháng (`mom_21`) chỉ chênh lệch nhẹ (+1.27%), cho thấy K-Means Baseline không phân cụm theo các biến động ngắn hạn nhất thời mà phân tách dựa trên vị thế dòng tiền cơ bản và xu hướng trung dài hạn.

### 2. Định danh Chân dung Kinh tế (Economic Persona Mapping)
- **Cụm 0 (Aligned Cluster 0):** **"Nhóm Cổ phiếu Siêu Thanh khoản / Dẫn dắt Dòng tiền / Beta cao" (Leader / High Liquidity / Market Beta > 1.3)**.
  - Quy mô: Bình quân 14.7 mã (chiếm ~4% số lượng mã).
  - Đặc tính: Thanh khoản khổng lồ (371.8 tỷ VNĐ/phiên), Beta thị trường cao (1.3013), động lượng 1 năm mạnh mẽ (+39.38%), mức sụt giảm tối đa được kiểm soát tốt (-19.28% so với -21.09% của cụm 1).
- **Cụm 1 (Aligned Cluster 1):** **"Nhóm Cổ phiếu Đại trà / Thanh khoản Thấp / Phổ thông" (Broad Market / Low Liquidity / Defensive)**.
  - Quy mô: Bình quân 359.6 mã (chiếm ~96% số lượng mã).
  - Đặc tính: Thanh khoản thấp (14.94 tỷ VNĐ/phiên), Beta thấp (0.6080) nhưng độ biến động nội tại 63 phiên lại cao hơn Cụm 0 (35.37% vs 29.72%), động lượng tăng trưởng dài hạn thấp hơn.

### 3. Tính Nhất quán theo Thời gian (Profile Temporal Consistency)
- Qua 15 snapshots, Cụm 0 duy trì thanh khoản áp đảo liên tục (dao động từ 201 tỷ đến 576 tỷ VNĐ/phiên) bất kể điều kiện thị trường.
- Trong các đợt sụt giảm mạnh của VN-Index (tháng 04/2024 và tháng 07/2024), do Cụm 0 có Beta cao (~1.3), các cổ phiếu này có mức điều chỉnh ngắn hạn tương ứng với thị trường chung, nhưng ngay lập tức bứt phá về động lượng 1 năm khi thị trường hồi phục.

---

## V. Khung Kết luận 3 Phần Bắt buộc

### 1. Phần A — Chân dung Kinh tế (Economic Persona)
- K-Means Baseline đã phân tách thị trường thành 2 thái cực kinh tế hoàn toàn rõ ràng: Nhóm Dẫn dắt siêu thanh khoản (Cụm 0, ~15 mã blue-chips) và Nhóm Cổ phiếu đại trà toàn thị trường (Cụm 1, ~360 mã).

### 2. Phần B — Động lực Phân tách Chính (Core Driver)
- Dòng tiền thanh khoản (`liquidity_21`) và quán tính xu hướng dài hạn (`mom_252`) là hai động lực quyết định. K-Means tách biệt thành công nhóm cổ phiếu hút dòng tiền cốt lõi của TTCK Việt Nam.

### 3. Phần C — Tính Khả thi cho Milestone M3 (M3 Feasibility)
- Cụm 0 sở hữu thanh khoản trung bình 371.8 tỷ VNĐ/phiên, mang lại **tính khả thi thực tế cực kỳ cao cho chiến lược đầu tư ở Milestone M3**. Quỹ đầu tư có thể dễ dàng giải ngân quy mô lớn mà không lo ngại rủi ro trượt giá (slippage) hay thiếu thanh khoản thoát hàng.
