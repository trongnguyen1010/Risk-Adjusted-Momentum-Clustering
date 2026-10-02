# Báo cáo Nhiệm vụ 8: Xây dựng Hồ sơ Cụm - PCA + K-Means
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 15 snapshots development (30/11/2023 - 24/01/2025) | **Mô hình:** PCA + K-Means (Global K = 2)

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Phân tích hồ sơ cụm sau khi giải mã ngược (Inverse Transform) từ 4D về 8D cho thấy PCA đã dồn toàn bộ phương sai vào yếu tố Thanh khoản và Rủi ro. Cụm 0 trở thành tập hợp thiểu số của các "Siêu Cổ Phiếu" với thanh khoản khổng lồ (~359 tỷ VNĐ/phiên), Beta cao (~1.26) và động lượng cực mạnh. Ngược lại, Cụm 1 chứa đại đa số thị trường với thanh khoản thấp và an toàn hơn.

---

## BẢNG TỔNG HỢP VÀ CHI TIẾT ĐẶC TRƯNG TÀI CHÍNH

### 1. Bảng Tổng hợp Đặc trưng
| Đặc trưng | Cụm 0 (Siêu cổ phiếu) | Cụm 1 (Đại đa số) | Phân tích |
| :--- | :--- | :--- | :--- |
| Thanh khoản (Median) | ~359 Tỷ VNĐ | ~14 Tỷ VNĐ | Cụm 0 là nơi hút dòng tiền khổng lồ |
| Momentum 63 (Median)| ~7.48% | Thấp hơn | Cụm 0 có đà tăng trưởng giá rất mạnh |
| Beta 126 (Median) | ~1.25 | < 1.0 | Cụm 0 nhạy cảm với thị trường, rủi ro cao |
| Volatility 63 | Biến động lớn | Biến động thấp | Cụm 0 mang tính chất đầu cơ |
| Vai trò | Nhóm dẫn dắt | Nhóm nền tảng | Phù hợp cho chiến lược Momentum |

### 2. Bảng Đặc trưng chi tiết từng Snapshot
| Snapshot | Cụm | Thanh khoản (Tỷ VNĐ) | Mom 63 (%) | Beta 126 | Volatility 63 | MDD 126 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2023-11-30 | Cụm 0 | 201.23 | -1.32% | 1.2675 | 0.4109 | -0.2380 |
| 2023-11-30 | Cụm 1 | 8.90 | -6.13% | 0.6163 | 0.3349 | -0.2159 |
| 2023-12-29 | Cụm 1 | 14.51 | 1.09% | 0.7630 | 0.3276 | -0.2355 |
| 2023-12-29 | Cụm 0 | 332.43 | 13.46% | 1.4714 | 0.3941 | -0.2682 |
| 2024-01-31 | Cụm 1 | 14.27 | 7.10% | 0.7401 | 0.2695 | -0.2308 |
| 2024-01-31 | Cụm 0 | 295.17 | 20.65% | 1.4877 | 0.3047 | -0.2765 |
| 2024-02-29 | Cụm 1 | 16.68 | 8.43% | 0.7188 | 0.2651 | -0.2193 |
| 2024-02-29 | Cụm 0 | 359.15 | 16.43% | 1.4970 | 0.2526 | -0.2666 |
| 2024-03-29 | Cụm 1 | 26.10 | 9.48% | 0.6848 | 0.2694 | -0.1741 |
| 2024-03-29 | Cụm 0 | 492.02 | 18.88% | 1.4264 | 0.2715 | -0.1939 |
| 2024-04-26 | Cụm 1 | 23.67 | 1.54% | 0.7109 | 0.3111 | -0.1741 |
| 2024-04-26 | Cụm 0 | 475.61 | 3.86% | 1.3492 | 0.3364 | -0.1747 |
| 2024-05-31 | Cụm 0 | 419.72 | 7.56% | 1.2510 | 0.3401 | -0.1566 |
| 2024-05-31 | Cụm 1 | 24.66 | 6.05% | 0.6200 | 0.3205 | -0.1665 |
| 2024-06-28 | Cụm 1 | 29.33 | 2.85% | 0.6414 | 0.3348 | -0.1700 |
| 2024-06-28 | Cụm 0 | 576.26 | 7.49% | 1.2112 | 0.3018 | -0.1368 |
| 2024-07-31 | Cụm 1 | 20.24 | 5.16% | 0.6611 | 0.3242 | -0.1866 |
| 2024-07-31 | Cụm 0 | 323.08 | 8.67% | 1.2635 | 0.3119 | -0.1773 |
| 2024-08-30 | Cụm 1 | 6.73 | 3.95% | 0.4659 | 0.5002 | -0.2439 |
| 2024-08-30 | Cụm 0 | 288.10 | -1.12% | 1.2562 | 0.2959 | -0.2023 |
| 2024-09-30 | Cụm 1 | 7.29 | -2.95% | 0.4793 | 0.4634 | -0.2442 |
| 2024-09-30 | Cụm 0 | 371.03 | 5.15% | 1.1981 | 0.2764 | -0.1928 |
| 2024-10-31 | Cụm 1 | 7.66 | -0.36% | 0.4795 | 0.4333 | -0.2431 |
| 2024-10-31 | Cụm 0 | 421.11 | 13.05% | 1.1898 | 0.2690 | -0.1554 |
| 2024-11-29 | Cụm 1 | 7.83 | -0.19% | 0.4806 | 0.4056 | -0.2440 |
| 2024-11-29 | Cụm 0 | 462.59 | 1.48% | 1.1594 | 0.2327 | -0.1636 |
| 2024-12-31 | Cụm 1 | 10.12 | 3.79% | 0.5457 | 0.3694 | -0.2170 |
| 2024-12-31 | Cụm 0 | 357.88 | 0.98% | 1.2554 | 0.2386 | -0.1530 |
| 2025-01-24 | Cụm 0 | 201.76 | 2.49% | 1.2357 | 0.2219 | -0.1364 |
| 2025-01-24 | Cụm 1 | 6.19 | 3.66% | 0.5132 | 0.3772 | -0.1980 |

---


## 1. Mục tiêu

Diễn giải ý nghĩa của hai cụm PCA + K-Means bằng 8 feature thị trường gốc, thay vì chỉ diễn giải các principal component. Mục tiêu là xác định đặc điểm đại diện, so sánh khác biệt giữa cụm và nêu rõ giới hạn diễn giải; không biến kết quả M2 thành khuyến nghị mua, bán hoặc phân bổ vốn.

## 2. Dữ liệu và quá trình

Nguồn là `M2/artifacts/m2-task6-pca-kmeans-v1/profiles.csv`, gồm 30 profile = 2 cụm x 15 snapshot. Mỗi profile lưu `aligned_cluster_id`, quy mô cụm và centroid trên tám feature gốc. Báo cáo tính **trung vị qua 15 centroid theo snapshot** cho mỗi cụm; đây là mô tả điển hình theo thời gian, không phải centroid của toàn bộ mẫu gộp.

Các cụm được gọi là “cụm 0” và “cụm 1” theo `aligned_cluster_id`. Không dùng các `semantic_label` thay đổi theo snapshot làm nhãn kinh tế cố định.

## 3. Kết quả đạt được theo kế hoạch

### 8.1 — Tổng hợp feature theo cụm

| Đặc trưng | Cụm 0 | Cụm 1 | Cách đọc |
|---|---:|---:|---|
| Số mã trong cụm | 15 | 229 | Trung vị quy mô theo snapshot |
| `mom_21` | 3,07% | 0,96% | Động lượng 1 tháng |
| `mom_63` | 7,49% | 3,66% | Động lượng 3 tháng |
| `mom_126` | 10,16% | 3,97% | Động lượng 6 tháng |
| `mom_252` | 41,23% | 18,13% | Động lượng 12 tháng |
| `vol_63` | 0,296 | 0,335 | Biến động 3 tháng |
| `mdd_126` | -0,177 | -0,217 | Drawdown cực đại 6 tháng |
| `beta_126` | 1,256 | 0,620 | Độ nhạy thị trường |
| `liquidity_21` | 359,2 tỷ | 14,3 tỷ | Thanh khoản 21 ngày, đơn vị tiền tệ gốc |

### 8.2 — So sánh giữa các cụm

Cụm 0 là nhóm rất nhỏ nhưng có beta và thanh khoản điển hình cao hơn rõ rệt: thanh khoản trung vị cao khoảng 25 lần, beta cao khoảng 2 lần so với cụm 1. Các chỉ số động lượng 21/63/126/252 ngày cũng cao hơn ở cụm 0.

Tuy nhiên, `vol_63` của cụm 0 thấp hơn (0,296 so với 0,335) và `mdd_126` ít âm hơn (-0,177 so với -0,217). Vì vậy không thể gắn nhãn đơn giản “cụm 0 rủi ro cao, cụm 1 an toàn”: beta, volatility và drawdown không đưa ra cùng một tín hiệu. Diễn giải chính xác hơn là cụm 0 là nhóm **thanh khoản cao, beta cao, momentum cao và quy mô nhỏ** trong sample này.

### 8.3 — Giới hạn diễn giải

- Profile mô tả cấu trúc dữ liệu lịch sử Development, không phải dự báo lợi nhuận tương lai.
- Balance thấp khiến profile cụm 0 nhạy hơn với số ít mã và sự thay đổi universe.
- Các feature ở đơn vị khác nhau; heatmap dùng trực tiếp giá trị gốc sẽ bị `liquidity_21` chi phối. Nếu trực quan hóa, cần chuẩn hóa theo feature hoặc tách panel, không dùng một thang màu chung.
- PCA là cách tạo cụm; profile được đọc trong 8 feature gốc để giữ ý nghĩa kinh tế. Không diễn giải một PC như một “tín hiệu đầu tư”.

## 4. Phân tích

Kết quả cho thấy PCA + K-Means không chia universe thành hai cụm đối xứng. Thay vào đó, mô hình nhận diện một nhánh nhỏ có dòng tiền và beta nổi bật, còn cụm 1 chiếm phần lớn universe. Điều này nhất quán với balance thấp trong Task 7.

Các động lượng dài hơn của cụm 0 cao hơn khá rõ, nhưng rủi ro không phải một chiều: beta cao hơn, trong khi volatility và MDD không xấu hơn. Do đó, cụm này có thể được xem là một profile thị trường khác biệt để nghiên cứu tiếp, chứ không phải danh sách mã nên giao dịch.

## 5. Tổng hợp nhận xét

Task 8 đã tạo được profile dễ đọc trên cùng 8 feature gốc, bảo đảm PCA + K-Means có thể so sánh công bằng với K-Means baseline và Ward ở Task 10. Phát hiện nổi bật là sự phân hóa theo thanh khoản và beta, đi kèm chênh lệch momentum. Cần giữ kết luận ở mức mô tả, đồng thời dùng Task 9 để kiểm tra liệu profile đó có bền theo thời gian hay không.

Nguồn chính: `M2/artifacts/m2-task6-pca-kmeans-v1/profiles.csv`.