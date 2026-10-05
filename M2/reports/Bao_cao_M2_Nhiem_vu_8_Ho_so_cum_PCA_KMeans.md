# Báo cáo Nhiệm vụ 8: Xây dựng Hồ sơ Cụm – PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshot Development (30/11/2023 – 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)
**Nguồn:** `M2/artifacts/m2-task6-pca-kmeans-v1/cluster_profiles.csv` (13 cột phẳng) | **Notebook:** `M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb`

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Hồ sơ hai cụm được đọc trên 8 đặc trưng gốc. **Cụm 0** là nhóm nhỏ (trung vị 15 mã) có thanh khoản `liquidity_21` ~359 tỷ VNĐ/phiên, beta ~1,26 và động lượng cao hơn ở mọi kỳ hạn; **Cụm 1** là phần lớn universe (trung vị 229 mã) với thanh khoản ~14 tỷ VNĐ/phiên và beta ~0,62. Trên thang Robust Z-Score (chuẩn hóa theo median/IQR thị trường của từng tháng), **động lực phân tách chính là `liquidity_21`** (ΔZ = 64,51), tiếp theo là `beta_126` (0,77) và `mom_252` (0,50). Cụm 0 có thanh khoản cao hơn ở 15/15 tháng và `mom_63` cao hơn ở 12/15 tháng. Kết quả chỉ mô tả phân hóa đặc trưng, chưa chứng minh cơ chế dòng tiền hay quan hệ nhân quả, và không phải khuyến nghị đầu tư.

---

## 1. Mục đích

Khắc họa tính chất kinh tế của hai cụm (K = 2) bằng 8 đặc trưng gốc: động lượng (21/63/126/252 phiên), rủi ro hệ thống (beta), biến động và sụt giảm (`vol_63`, `mdd_126`) và thanh khoản (`liquidity_21`); xác định động lực phân tách chính; kiểm tra tính nhất quán theo thời gian; dùng cùng cấu trúc bảng và biểu đồ với K-Means Baseline và Ward. Nhãn kỹ thuật "Cụm 0" và "Cụm 1" được giữ trung tính; không đưa lợi nhuận, Sharpe hay khuyến nghị đầu tư vào M2.

## 2. Dữ liệu và quá trình

- Input chính là `cluster_profiles.csv` của bộ `m2-task6-pca-kmeans-v1` (đúng 13 cột phẳng, không chứa JSON centroid; mỗi dòng lưu `snapshot_date`, `aligned_cluster_id`, `size`, `size_ratio` và trung bình 8 feature gốc của thành viên cụm). Notebook kiểm tra manifest, checksum và config trước khi đọc.
- Thanh khoản trình bày bằng tỷ VNĐ/phiên (chia 10⁹). Mean/Median là thống kê **qua 15 profile theo tháng** của từng cụm, không phải median của mọi cổ phiếu gộp chung.
- Scaler trong model chỉ được đọc để chuẩn hóa biểu đồ, không fit lại. Robust Z-Score `Z = (mean feature của cụm − median thị trường tháng đó) / IQR thị trường tháng đó`; không fit scaler trên 30 centroid hay toàn bộ Development. Radar chỉ giới hạn **hiển thị** trong [−3, 3] (điểm vượt biên đánh dấu `*`), không clipping dữ liệu; giá trị thật giữ trong bảng Z.

## 3. Kết quả đạt được

### 8.1 – Bảng 1: Tổng hợp hồ sơ đặc trưng theo cụm

| Cụm | size | liquidity_21 (tỷ VNĐ/phiên) | beta_126 | vol_63 | mdd_126 | mom_21 | mom_63 | mom_126 | mom_252 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cụm 0 (Mean) | 14,73 | 371,81 | 1,3013 | 0,2972 | -0,1928 | 2,65% | 7,85% | 13,35% | 39,38% |
| Cụm 0 (Median) | 15 | 359,15 | 1,2562 | 0,2959 | -0,1773 | 3,07% | 7,49% | 10,16% | 41,23% |
| Cụm 1 (Mean) | 359,60 | 14,94 | 0,6080 | 0,3537 | -0,2109 | 1,38% | 2,90% | 5,55% | 18,77% |
| Cụm 1 (Median) | 229 | 14,27 | 0,6200 | 0,3348 | -0,2170 | 0,96% | 3,66% | 3,97% | 18,13% |

### 8.2 – Bảng 2: So sánh đối đầu giữa Cụm 0 và Cụm 1 (Mean)

| Đặc trưng | Cụm 0 (Mean) | Cụm 1 (Mean) | Chênh lệch (Cụm 0 − Cụm 1) |
|---|---:|---:|---:|
| size | 14,73 | 359,60 | -344,87 |
| liquidity_21 (tỷ VNĐ) | 371,81 | 14,94 | +356,87 |
| beta_126 | 1,3013 | 0,6080 | +0,6933 |
| vol_63 | 0,2972 | 0,3537 | -0,0565 |
| mdd_126 | -0,1928 | -0,2109 | +0,0181 |
| mom_21 | 2,65% | 1,38% | +1,27 điểm % |
| mom_63 | 7,85% | 2,90% | +4,95 điểm % |
| mom_126 | 13,35% | 5,55% | +7,80 điểm % |
| mom_252 | 39,38% | 18,77% | +20,61 điểm % |

### Bảng 3: Chuỗi thời gian quy mô và thanh khoản qua 15 snapshot

| Snapshot | Size Cụm 0 | Size Cụm 1 | Liquidity Cụm 0 (tỷ VNĐ) | Liquidity Cụm 1 (tỷ VNĐ) |
|---|---:|---:|---:|---:|
| 2023-11-30 | 9 | 133 | 201,23 | 8,90 |
| 2023-12-29 | 16 | 179 | 332,43 | 14,51 |
| 2024-01-31 | 17 | 179 | 295,17 | 14,27 |
| 2024-02-29 | 17 | 179 | 359,15 | 16,68 |
| 2024-03-29 | 15 | 182 | 492,02 | 26,10 |
| 2024-04-26 | 14 | 200 | 475,61 | 23,67 |
| 2024-05-31 | 15 | 206 | 419,72 | 24,66 |
| 2024-06-28 | 11 | 229 | 576,26 | 29,33 |
| 2024-07-31 | 17 | 230 | 323,08 | 20,24 |
| 2024-08-30 | 21 | 574 | 288,10 | 6,73 |
| 2024-09-30 | 16 | 590 | 371,03 | 7,29 |
| 2024-10-31 | 13 | 595 | 421,11 | 7,66 |
| 2024-11-29 | 8 | 772 | 462,59 | 7,83 |
| 2024-12-31 | 11 | 578 | 357,88 | 10,12 |
| 2025-01-24 | 21 | 568 | 201,76 | 6,19 |

### 8.3 – Robust Z-Score và trực quan hóa

**Robust Z-Score trung bình 15 tháng (không cắt dữ liệu):**

| Cụm | mom_21 | mom_63 | mom_126 | mom_252 | vol_63 | mdd_126 | beta_126 | liquidity_21 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Cụm 0 | 0,2710 | 0,4893 | 0,4910 | 0,6658 | -0,0274 | 0,0289 | 0,8071 | 66,0005 |
| Cụm 1 | 0,1046 | 0,1338 | 0,1442 | 0,1687 | 0,1320 | -0,1002 | 0,0380 | 1,4934 |

**Chênh lệch chuẩn hóa (Cụm 0 − Cụm 1) và động lực phân tách chính:**

| Đặc trưng | ΔZ (Cụm 0 − Cụm 1) |
|---|---:|
| liquidity_21 | **64,5071** |
| beta_126 | 0,7691 |
| mom_252 | 0,4970 |
| mom_63 | 0,3555 |
| mom_126 | 0,3467 |
| mom_21 | 0,1664 |
| vol_63 | -0,1594 |
| mdd_126 | 0,1291 |

**Primary Driver: `liquidity_21` (ΔZ = 64,5071).** Độ lớn này phản ánh việc thanh khoản trung bình của Cụm 0 (~372 tỷ) cách rất xa median thị trường tính theo IQR thị trường của chính tháng đó.

Giá trị Z trên Heatmap tại 2025-01-24:

| Cụm | mom_21 | mom_63 | mom_126 | mom_252 | vol_63 | mdd_126 | beta_126 | liquidity_21 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Cụm 0 | 0,20 | 0,13 | 0,49 | 0,43 | -0,37 | 0,28 | 0,88 | 61,85 |
| Cụm 1 | 0,00 | 0,22 | 0,18 | 0,21 | 0,26 | -0,19 | 0,08 | 1,84 |

Ô thanh khoản của Cụm 0 (61,85) vượt biên [−3, 3] nên được tô màu bão hòa và đánh dấu `*` trên Radar; số liệu thật nằm trong bảng.

## 4. Nhận định kinh tế tài chính và rào chắn học thuật

### 4.1 Động lực phân tách chính (Primary Driver Test)

`liquidity_21` có chênh lệch chuẩn hóa lớn nhất (ΔZ = 64,5071; Z trung bình Cụm 0 = 66,0005, Cụm 1 = 1,4934), vượt xa `beta_126` (0,7691), `mom_252` (0,4970) và `mom_21` (0,1664). Trong ba ứng viên kế hoạch nêu (thanh khoản, `mom_21`, beta), thanh khoản là yếu tố đứng đầu. Kết quả mô tả phân hóa đặc trưng, chưa chứng minh cơ chế dòng tiền hay quan hệ nhân quả.

### 4.2 Chân dung kinh tế (Economic Persona Mapping)

Đối chiếu với Trung vị thị trường (Z = 0):
- **Cụm 0:** thanh khoản cao hơn thị trường rất xa (Z = 66,00), beta cao (0,81), động lượng dương ở mọi kỳ hạn (Z từ 0,27 đến 0,67); `vol_63` (−0,03) và `mdd_126` (+0,03) gần với median thị trường. Phù hợp kịch bản **Nhóm Cổ phiếu Dẫn dắt / Thu hút dòng tiền**.
- **Cụm 1:** thanh khoản gần mức thị trường (Z = 1,49), beta thấp (0,04), động lượng chỉ nhỉnh hơn median (Z từ 0,10 đến 0,17), `vol_63` cao hơn median (+0,13), `mdd_126` âm hơn (−0,10). Phù hợp kịch bản **Nhóm Đại trà**.

Hai cụm vẫn mang nhãn trung tính "Cụm 0" và "Cụm 1"; không gán nhãn đầu tư từ một feature đơn lẻ.

### 4.3 Nhất quán theo thời gian (Profile Temporal Consistency)

- Cụm 0 có thanh khoản cao hơn Cụm 1 ở **15/15 tháng**; `mom_63` cao hơn ở **12/15 tháng**.
- Kiểm tra cụ thể hai tháng điều chỉnh mà kế hoạch nêu:

| Snapshot | Cụm | beta_126 | mom_63 | mdd_126 |
|---|---:|---:|---:|---:|
| 2024-04-26 | Cụm 1 | 0,7109 | 1,54% | -0,1741 |
| 2024-04-26 | Cụm 0 | 1,3492 | 3,86% | -0,1747 |
| 2024-07-31 | Cụm 1 | 0,6611 | 5,16% | -0,1866 |
| 2024-07-31 | Cụm 0 | 1,2635 | 8,67% | -0,1773 |

  Cụm 0 có beta gấp khoảng 1,9 lần Cụm 1 ở cả hai tháng nhưng không có `mdd_126` xấu hơn rõ rệt (04/2024: −0,1747 so với −0,1741; 07/2024: −0,1773 so với −0,1866). Notebook không đọc dữ liệu chỉ số nên không kết luận về VN-Index.

### 4.4 Giới hạn diễn giải học thuật

- Mean nhạy với quan sát cực đoan, nhất là khi Cụm 0 chỉ có 8–21 mã; luôn đối chiếu với dòng Median.
- Hồ sơ chỉ mô tả dữ liệu lịch sử Development, không suy diễn thành khuyến nghị mua cụm nào; tỷ suất sinh lời và Sharpe thuộc M3.

## 5. Khung kết luận ba phần

**Phần A – Chân dung kinh tế.** Cụm 0: size mean 14,73 (median 15); thanh khoản mean 371,81 và median 359,15 tỷ VNĐ/phiên; beta mean 1,3013, median 1,2562. Cụm 1: size mean 359,60 (median 229); thanh khoản mean 14,94 và median 14,27 tỷ VNĐ/phiên; beta mean 0,6080, median 0,6200. Giữ nhãn Cụm 0/Cụm 1.

**Phần B – Động lực phân tách chính và tính nhất quán.** Chênh lệch chuẩn hóa lớn nhất là `liquidity_21` (ΔZ = 64,5071). Cụm 0 có thanh khoản cao hơn ở 15/15 tháng và `mom_63` cao hơn ở 12/15 tháng. Mô tả phân hóa đặc trưng, chưa chứng minh cơ chế dòng tiền hay quan hệ nhân quả.

**Phần C – Tính khả thi cho M3.** Thanh khoản là thông tin mô tả về khả năng giao dịch; Mean chịu ảnh hưởng các mã cực đoan. M2 chưa có size vốn, tỷ lệ tham gia volume, trọng số hay mô phỏng thực thi nên chưa thể khẳng định đủ sức chứa hoặc không có slippage; kiểm chứng chi phí thuộc M3. Không khuyến nghị mua cụm nào, không dùng Sharpe/lợi nhuận hay holdout.

