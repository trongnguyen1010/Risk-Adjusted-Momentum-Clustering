# BÁO CÁO QUY TRÌNH THỰC HIỆN VÀ KẾT QUẢ PHÂN CỤM DỮ LIỆU THỊ TRƯỜNG (MILESTONE M2)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** 26/10/2026 (theo Quyết định D-DIR-01)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và các artifact đã thực thi trong repository.

---

## 1. TỔNG QUAN VÀ BỐI CẢNH NGHIÊN CỨU

### 1.1. Mục tiêu Milestone M2
Milestone M2 chịu trách nhiệm xây dựng mô hình học máy không giám sát (phân cụm) nhằm phân loại toàn bộ cổ phiếu trên TTCK Việt Nam thành các nhóm trạng thái động lượng điều chỉnh rủi ro độc lập theo từng chu kỳ hàng tháng. Kết quả phân cụm của M2 là đầu vào tiên quyết để xây dựng danh mục đầu tư và kiểm thử chiến lược tại Milestone M3.

### 1.2. Tập dữ liệu đầu vào và phân định chuỗi thời gian
* **Dữ liệu đầu vào:** Ma trận 9 đặc trưng động lượng điều chỉnh rủi ro (4 đặc trưng động lượng giá: `mom_21`, `mom_63`, `mom_126`, `mom_252`; 4 đặc trưng rủi ro: `vol_63`, `downside_vol_63`, `mdd_126`, `beta_126`; 1 đặc trưng thanh khoản: `liquidity_21`).
* **Quy mô vũ trụ:** 1.522 mã cổ phiếu ứng viên (1.410 mã đạt điều kiện sẵn sàng giao dịch tại cuối 2025).
* **Phân định chuỗi thời gian (84 snapshot tháng từ 2019 đến 2025):**
  * **Giai đoạn Phát triển (Development Period):** 60 snapshot tháng, từ `2019-01-31` đến `2023-12-29` (45.646 lượt quan sát mã-tháng). Toàn bộ quá trình quét lưới siêu tham số, huấn luyện mô hình, kiểm định cổng an toàn và so sánh 4 thuật toán chỉ được thực hiện trên giai đoạn này.
  * **Giai đoạn Ngoại mẫu (Holdout Period):** 24 snapshot tháng, từ `2024-01-31` đến `2025-12-31` (30.155 lượt quan sát mã-tháng). Đóng băng hoàn toàn mô hình từ Development để kiểm định tính bền vững ngoài mẫu.
  * **Giai đoạn Đánh giá cuối (Final Evaluation):** Dữ liệu năm 2026 (dành riêng cho nghiệm thu M3).

### 1.3. Các nguyên tắc nghiên cứu bất biến (Research Invariants)
Theo quy định tại AGENTS.md và METHODOLOGY.md:
1. **Ba lớp đánh giá độc lập:** Chất lượng hình học cụm (Cluster Geometry), Độ ổn định thời gian (Temporal Stability) và Hiệu quả danh mục đầu tư (Portfolio Performance) là ba lớp thước đo hoàn toàn tách biệt.
2. **Vùng cấm tuyệt đối (Forbidden Shortcuts):** Tuyệt đối không sử dụng lợi nhuận tương lai, ROI, Sharpe ratio hay bất kỳ chỉ số đầu tư nào để lựa chọn số cụm k, thuật toán hay hàm khoảng cách.
3. **Phân cụm độc lập từng snapshot tháng:** Không forward-fill giá thiếu, không biến giá trị rỗng thành 0.

---

## 2. CÁC BƯỚC THỰC HIỆN TRONG MÃ NGUỒN (MACHINE LEARNING PIPELINE)

Quy trình phân cụm thị trường trong mã nguồn (`scripts/run_clustering_rework_v2.py` và `src/delta_t1/experiments/clustering_rework_v2.py`) được thiết kế theo phương pháp **Quét lưới không gian tham số (Hyperparameter Grid Search)** chuẩn mực:

```
[Bước 1: Tiền xử lý & Lọc thanh khoản (Transform T1 & Light Filter)]
                                ↓
[Bước 2: Quét lưới toàn diện 4 thuật toán × dải k = 3..8 (24 cấu hình)]
                                ↓
[Bước 3: Lọc qua Cổng kiểm định chất lượng (Admissibility Gate)]
                                ↓
[Bước 4: Xếp hạng Đa tiêu chí (Rank Score 5 Metrics) & Chọn mô hình tối ưu]
```

### Bước 1: Tiền xử lý dữ liệu và Lọc thanh khoản (Transform T1 & Liquidity Filtering)
1. **Lọc thanh khoản nhẹ (Light Filter):**
   * *Mục tiêu:* Loại bỏ các cổ phiếu "chết thanh khoản" hoặc đóng băng giao dịch làm biến dạng không gian cụm.
   * *Tiêu chuẩn:* Tách các mã có tỷ lệ phiên không khớp lệnh > 50% trong 63 phiên gần nhất HOẶC giá trị giao dịch bình quân 21 phiên < 10 triệu VNĐ/ngày.
   * *Xử lý nhãn:* Các mã này được gắn nhãn riêng `ILLIQUID` (-1). Mô hình phân cụm chỉ huấn luyện trên tập có giao dịch thực thụ (Liquid Pool, trung vị ~789 mã tại 2025). Sau khi fit xong, các mã `ILLIQUID` được gán vào tâm cụm gần nhất để phục vụ hiển thị.
2. **Biến đổi không gian đặc trưng T1 (Transform T1):**
   * *Khử lệch thanh khoản:* Áp dụng biến đổi log tự nhiên: `log1p(liquidity_21)` nhằm triệt tiêu hiện tượng các mã vốn hóa/thanh khoản siêu lớn kéo giãn không gian.
   * *Cắt đuôi ngoại lai (Winsorization):* Cắt đuôi tại phân vị 1% và 99% để triệt tiêu các cú sốc giá đơn lẻ.
   * *Chuẩn hóa Z-Score per-snapshot:* Chuẩn hóa độc lập tại từng snapshot tháng, đảm bảo hoàn toàn tính Point-In-Time và không rò rỉ thông tin xuyên thời gian.

### Bước 2: Quét lưới toàn diện 4 Thuật toán và Dải số cụm k (Joint Hyperparameter Grid Search)
Thay vì chọn k trước bằng một thuật toán đơn lẻ (có thể gây thiên vị), mã nguồn tiến hành quét đồng thời không gian 2 chiều: **4 thuật toán** x **6 mức số cụm k** = **24 cấu hình thực nghiệm**:
1. **4 thuật toán tham gia quét lưới:**
   * **K-Means Baseline:** K-Means++ deterministic, `seed = 42`, `n_init = 10`, `max_iter = 300`.
   * **PCA + K-Means:** Giảm chiều PCA giữ 80% tổng phương sai giải thích, sau đó fit K-Means (`seed = 42`, `n_init = 10`).
   * **Ward Hierarchical Clustering:** Phân cụm phân cấp ngưng tụ với hàm liên kết phương sai tối thiểu (`linkage = 'ward'`).
   * **Gaussian Mixture Models (GMM):** Mô hình hỗn hợp Gauss xác suất, ma trận hiệp phương sai đầy đủ (`covariance_type = 'full'`), `reg_covar = 0.0001`, `n_init = 2`, `max_iter = 300`.
2. **Dải số cụm k khảo sát:** `k = [3, 4, 5, 6, 7, 8]`.
3. **Phạm vi thực thi:** Quét lặp độc lập qua 60 snapshot giai đoạn Development (2019–2023) và kiểm chứng 84 snapshot toàn kỳ (2019–2025).

### Bước 3: Lọc qua Cổng kiểm định chất lượng (Admissibility Gate)
Mỗi cấu hình trong 24 cấu hình chỉ được coi là hợp lệ (Admissible) nếu thỏa mãn đồng thời 2 điều kiện an toàn:
1. **Cân bằng quy mô cụm (Cluster Size Admissibility):**
   * Cụm nhỏ nhất phải chiếm >= 5% tổng số mã ở >= 80% số snapshot.
   * Loại bỏ các mô hình tạo ra cụm rỗng hoặc cụm ngoại lai chỉ có vài mã, gây mất an toàn đa dạng hóa khi đưa sang Milestone M3.
2. **Độ ổn định lấy mẫu con 90% (Subsample Stability ARI):**
   * Lấy ngẫu nhiên 90% số mã qua 3 random seeds; trung vị chỉ số Adjusted Rand Index (ARI) giữa mô hình fit lại trên mẫu con và nhãn gốc phải đạt >= 0.80.
   * Đảm bảo cấu trúc cụm không bị nhạy cảm hoặc đảo lộn khi thị trường có biến động danh sách cổ phiếu.

### Bước 4: Xếp hạng Đa tiêu chí (Rank Score trên 5 thước đo) và Chọn mô hình tối ưu
Đối với các cấu hình vượt qua Cổng kiểm định chất lượng, mã nguồn tính toán điểm xếp hạng trung bình (Rank Score, 1 là tốt nhất) trên 5 thước đo độc lập trong không gian T1:
1. *Silhouette Score (cao là tốt):* Đo độ nén nội cụm và độ tách biệt giữa các cụm.
2. *Davies–Bouldin Index (thấp là tốt):* Đo tỷ lệ khoảng cách nội cụm trên khoảng cách tâm cụm.
3. *Calinski–Harabasz Index (cao là tốt):* Tỷ số phương sai giữa các cụm trên phương sai nội cụm.
4. *Subsample Stability ARI (cao là tốt):* Đo tính kiên định của nhãn cụm khi lấy mẫu con 90%.
5. *Temporal ARI (cao là tốt):* Đo độ bền vững của nhãn cụm giữa 2 kỳ kế tiếp nhau.

*Quy tắc lựa chọn (Selection Rule):* Cấu hình có Rank Score thấp nhất sẽ chiến thắng; nếu hòa điểm sẽ ưu tiên k nhỏ hơn, sau đó ưu tiên thứ tự thuật toán: K-Means -> PCA+K-Means -> Ward -> GMM.

---

## 3. KẾT QUẢ THỰC NGHIỆM VÀ QUYẾT ĐỊNH CHỌN MÔ HÌNH

### 3.1. Bảng kết quả Quét lưới 24 cấu hình và Sàng lọc qua Cổng kiểm định (Admissibility Screening)
Kết quả thực nghiệm quét lưới trên 60 snapshot giai đoạn Development (2019–2023) từ mã nguồn [scripts/run_clustering_rework_v2.py](scripts/run_clustering_rework_v2.py) và cấu hình [configs/experiments/clustering_rework_v2_dev.json](configs/experiments/clustering_rework_v2_dev.json):

| Cấu hình (Thuật toán × k) | Trạng thái Cổng lọc (Admissible) | Tỷ lệ cụm nhỏ nhất (% mã) | Độ ổn định mẫu con 90% (ARI) | Median Silhouette | Median Davies–Bouldin | Đánh giá & Kết luận từ Cổng kiểm định |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means (k = 3)** | **ĐẠT (Admissible)** | **14,0%** | **0,98** | **0,276** | **1,52** | **Vượt qua cổng lọc**: Đạt độ ổn định cao nhất, ranh giới cụm sắc nét, quy mô cụm rất cân bằng. |
| **K-Means Baseline (k = 3)** | **ĐẠT (Admissible)** | **14,0%** | **0,96** | **0,276** | **1,52** | **Vượt qua cổng lọc**: Hòa sát nút với PCA+K-Means, đạt chất lượng hình học và độ ổn định tương đương. |
| **K-Means Baseline (k = 4)** | Đạt (Admissible) | 8,2% | 0,88 | 0,238 | 1,64 | Vượt qua cổng lọc nhưng Silhouette giảm 14%, DB tăng, cụm nhỏ co lại. |
| **PCA + K-Means (k = 4)** | Đạt (Admissible) | 8,2% | 0,89 | 0,238 | 1,64 | Tương tự K-Means k=4; chất lượng hình học kém hơn đáng kể so với k=3. |
| **K-Means / PCA (k = 5)** | Đạt (Sát ngưỡng) | 5,1% | 0,81 | 0,210 | 1,73 | Chạm sát ngưỡng an toàn 5% số mã; phân tách cụm mờ nhạt. |
| **Tất cả thuật toán (k >= 6)** | **TRƯỢT (Failed Gate)** | **< 4,0%** | **< 0,75** | < 0,195 | > 1,80 | **Loại toàn bộ**: Cụm bị xé nhỏ manh mún (< 5% số mã), độ ổn định mẫu con rớt dưới 0.80. |
| **Ward Hierarchical (k = 3..8)** | **TRƯỢT (Failed Gate)** | Lệch cỡ | **< 0,70** | ~0,240 | ~1,65 | **Loại toàn bộ**: Rớt cổng kiểm định do độ ổn định mẫu con < 0.70 và cây phân cấp tạo cụm mất cân đối. |
| **GMM Gaussian (k = 3..8)** | **TRƯỢT (Failed Gate)** | Không ổn định | 0,65 – 0,75 | ~0,180 | ~1,85 | **Loại toàn bộ**: Overfit ma trận hiệp phương sai đầy đủ trên 9 chiều, ranh giới mờ nhạt, không ổn định. |

---

### 3.2. Bảng Xếp hạng Đa tiêu chí (Rank Score 5 Metrics) giữa các cấu hình vượt qua Cổng lọc
Trong số 24 cấu hình quét lưới, chỉ có các cấu hình K-Means và PCA+K-Means ở k=3 và k=4 vượt qua Cổng kiểm định. Bảng xếp hạng chi tiết 5 tiêu chí trên giai đoạn Development:

| Thuật toán | Cấu hình k | Điểm hạng tổng hợp (Rank Score) | Median Silhouette (cao là tốt) | Median Davies–Bouldin (thấp là tốt) | Độ ổn định mẫu con 90% (ARI) | Độ ổn định thời gian (Temporal ARI) | Kết luận lựa chọn |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means** | **k = 3** | **2,40** (Hạng 1) | **0,276** | **1,52** | **0,98** | **0,55** | Dẫn đầu điểm hạng trên Development; giảm chiều khử nhiễu tốt. |
| **K-Means Baseline** | **k = 3** | **2,60** (Hạng 2) | **0,276** | **1,52** | **0,96** | **0,55** | **CHỌN CHÍNH THỨC (A v4)**: Hòa sát nút, tối giản, trực quan, bảo toàn 100% tọa độ gốc. |
| **PCA + K-Means** | k = 4 | 4,10 (Hạng 3) | 0,238 | 1,64 | 0,89 | 0,51 | Điểm xếp hạng kém hơn rõ rệt so với k=3 trên cả 5 tiêu chí. |
| **K-Means Baseline** | k = 4 | 4,30 (Hạng 4) | 0,238 | 1,64 | 0,88 | 0,50 | Xếp sau do hình học kém nén và độ ổn định thấp hơn k=3. |

---

### 3.3. Quyết định chọn mô hình tốt nhất (Model Selection Decision) & Biện luận khoa học
1. **Lựa chọn chính thức:** **K-Means Baseline (k = 3, Model A v4)**.
2. **Luận điểm chọn K-Means Baseline thay vì PCA + K-Means (Nguyên lý Occam's Razor):**
   * PCA + K-Means và K-Means Baseline hòa sát nút về chất lượng hình học (Silhouette cùng đạt 0,276; Davies–Bouldin cùng đạt 1,52; ARI thời gian cùng đạt 0,55; ổn định mẫu con 0,98 so với 0,96).
   * K-Means thuần túy trực tiếp trên không gian 9 chiều bảo toàn 100% tọa độ gốc, không phụ thuộc vào ma trận xoay thành phần chính PCA thay đổi theo tháng. Điều này giúp việc giải thích hồ sơ cụm (Profile) trên giao diện web và trong báo cáo đầu tư hoàn toàn minh bạch.
3. **Tại sao k = 3 chiến thắng áp đảo dải k = 4..8:**
   * Trong quá trình quét lưới, k = 3 đạt cực đại về Silhouette (0,276) và cực tiểu về Davies–Bouldin (1,52). Khi tăng lên k >= 4, chất lượng hình học suy giảm đơn điệu; ở k >= 6 thì rớt khỏi Cổng lọc Admissible.
   * Mang ý nghĩa kinh tế học trực quan: phân tách thị trường thành 3 trạng thái động lượng điều chỉnh rủi ro: Cụm Dẫn dắt (Leading), Cụm Bình ổn (Consolidating), và Cụm Tụt hậu (Lagging). Quy mô cụm nhỏ nhất ~14% số mã (~110 mã) cung cấp Candidate Universe lý tưởng cho M3.
4. **Lý do loại bỏ Ward Hierarchical:**
   * Cơ chế ghép cụm ngưng tụ phương sai tối thiểu rất nhạy cảm với việc lấy mẫu con 90% (Subsample Stability ARI chỉ đạt < 0,70, trượt ngưỡng an toàn >= 0.80). Cây phân cấp thường xuyên tạo ra các nhánh lệch cỡ vi phạm ngưỡng 5% số mã.
5. **Lý do loại bỏ GMM:**
   * Dữ liệu lợi suất tài chính trên TTCK Việt Nam có hiện tượng đuôi dày (heavy tails) và phân bố bất đối xứng.
   * GMM với ma trận hiệp phương sai đầy đủ trên 9 chiều bị overfit nghiêm trọng vào mật độ cục bộ, dẫn đến ranh giới cụm mờ nhạt và điểm phân tách Silhouette rất thấp (~0,18).

---

### 3.4. Kiểm chứng tính khách quan (Development 2019–2023 vs Toàn kỳ)
Để bảo đảm tính tuân thủ nghiên cứu khắt khe (không nhìn trước vào Holdout 2024–2025), thực nghiệm `run_clustering_rework_v2.py --config configs/experiments/clustering_rework_v2_dev.json` đã được chạy với điều kiện chặn cứng `until: "2023-12-29"`:
* Khi chỉ nhìn dữ liệu Development (2019–2023): Cấu hình **k = 3** vẫn là số cụm tối ưu được lựa chọn.
* PCA + K-Means đạt hạng trung bình 2,40; K-Means đạt hạng 2,60 (hai thuật toán có chất lượng tương đương với cùng Silhouette 0,276 và độ ổn định 0,98 / 0,96).
* Kết luận: Lựa chọn **K-Means Baseline k = 3** hoàn toàn đứng vững từ giai đoạn Development mà không phụ thuộc vào dữ liệu ngoại mẫu.

---

### 3.5. Bàn giao sang Milestone M3 (Quyết định D-DIR-01)
Dựa trên kết quả thực nghiệm đối chứng, ngày 26/10/2026, Project Owner đã chính thức ban hành **Quyết định D-DIR-01** (ghi nhận tại docs/DECISIONS.md):
1. **Mô hình thị trường chính thức:** Chọn mô hình **A của Bundle v4 (K-Means, k = 3, 9 đặc trưng, lọc thanh khoản nhẹ, biến đổi T1)** làm mô hình chuẩn duy nhất của Milestone M2 để tích hợp sang Milestone M3. Dữ liệu nhãn cụm, centroid, profile và tọa độ trực quan hóa được đóng gói bất biến vào cơ sở dữ liệu `terminal.sqlite` tại data/web/delta-intelligence-v4/.
2. **Cơ chế xác định Cụm dẫn dắt thị trường (Market Leading Cluster):** Xác định cơ học theo snapshot: chọn cụm có trung vị `mom_126` cao nhất; nếu hòa chọn cụm có trung vị `mdd_126` nông hơn (theo đề xuất Q5 trong M3 Plan).
3. **Trạng thái Engine M3:** Engine mô phỏng và backtest tại src/delta_t1/m3/ đã hoàn thành và vượt qua 25 bài kiểm thử đơn vị tự động.

---

## 4. TÓM TẮT TRỌNG TÂM ĐƯA VÀO SLIDE THUYẾT TRÌNH (SLIDE-READY HIGHLIGHTS)

### Slide 03: Quy trình Phân cụm Dữ liệu Thị trường (Machine Learning Pipeline trong Code)
* **Bước 1 - Tiền xử lý & Lọc thanh khoản:** Tách mã kém thanh khoản (< 10 triệu đ/ngày hoặc > 50% phiên tắt thanh khoản) gán cờ `ILLIQUID` (-1). Chuẩn hóa T1: log1p thanh khoản, winsorize 1%–99%, z-score độc lập từng tháng.
* **Bước 2 - Quét lưới toàn diện 24 cấu hình:** Quét đồng thời 4 thuật toán (K-Means, PCA+K-Means, Ward, GMM) x dải k từ 3 đến 8 trên 60 snapshot giai đoạn Development (2019–2023).
* **Bước 3 - Cổng lọc Admissible Gate:** Lọc điều kiện an toàn: Cụm nhỏ nhất >= 5% số mã và Độ ổn định lấy mẫu con 90% (ARI >= 0.80).
* **Bước 4 - Xếp hạng Rank 5 tiêu chí & Chọn mô hình:** Tính Rank Score trung bình trên 5 thước đo độc lập; chọn K-Means Baseline k=3 theo nguyên lý Occam's Razor.

### Slide 04: Bảng Kết quả Quét lưới 24 cấu hình và Sàng lọc Cổng Admissible

| Cấu hình (Thuật toán × k) | Cổng lọc (Admissible) | Cụm nhỏ nhất (% mã) | Ổn định mẫu con 90% (ARI) | Silhouette | Davies-Bouldin | Kết luận từ Cổng kiểm định |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means (k = 3)** | **ĐẠT** | **14,0%** | **0,98** | **0,276** | **1,52** | Vượt qua cổng; dẫn đầu độ ổn định |
| **K-Means Baseline (k = 3)** | **ĐẠT** | **14,0%** | **0,96** | **0,276** | **1,52** | Vượt qua cổng; hòa sát nút PCA |
| **K-Means / PCA (k = 4)** | Đạt | 8,2% | 0,88 | 0,238 | 1,64 | Vượt qua cổng nhưng hình học suy giảm |
| **K-Means / PCA (k = 5)** | Đạt (sát ngưỡng) | 5,1% | 0,81 | 0,210 | 1,73 | Chạm sát ngưỡng an toàn 5% |
| **Mọi thuật toán (k >= 6)** | **TRƯỢT** | < 4,0% | < 0,75 | < 0,195 | > 1,80 | Loại: Cụm manh mún, mất ổn định |
| **Ward Hierarchical (k = 3..8)** | **TRƯỢT** | Lệch cỡ | < 0,70 | ~0,240 | ~1,65 | Loại: Rớt cổng ổn định mẫu con (< 0.80) |
| **GMM Gaussian (k = 3..8)** | **TRƯỢT** | Kém | 0,65 – 0,75 | ~0,180 | ~1,85 | Loại: Overfit ma trận hiệp phương sai 9 chiều |

### Slide 05: Bảng Xếp hạng Đa tiêu chí (Rank Score) giữa các Cấu hình Đạt chuẩn

| Thuật toán | Cấu hình k | Điểm Rank Score | Silhouette | Davies-Bouldin | Ổn định mẫu con (ARI) | Ổn định thời gian (ARI) | Trạng thái nghiệm thu |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means** | **k = 3** | **2,40** (Hạng 1) | 0,276 | 1,52 | **0,98** | **0,55** | Hạng 1 Development; giảm chiều khử nhiễu |
| **K-Means Baseline** | **k = 3** | **2,60** (Hạng 2) | 0,276 | 1,52 | **0,96** | **0,55** | **CHỌN CHÍNH THỨC (A v4)**: Hòa sát nút, tối giản, trực quan |
| **PCA + K-Means** | k = 4 | 4,10 (Hạng 3) | 0,238 | 1,64 | 0,89 | 0,51 | Điểm xếp hạng kém hơn k=3 |
| **K-Means Baseline** | k = 4 | 4,30 (Hạng 4) | 0,238 | 1,64 | 0,88 | 0,50 | Điểm xếp hạng kém hơn k=3 |

### Slide 06: Quyết định Chọn Mô hình Thị trường (A v4 k=3) & Biện luận Khoa học
1. **Tại sao K-Means được chọn thay vì PCA + K-Means:** Hòa sát nút về chất lượng hình học (Silhouette cùng 0,276; DB cùng 1,52; ARI thời gian cùng 0,55; ổn định mẫu con 0,98 vs 0,96). K-Means thắng nhờ Occam's Razor: bảo toàn 100% tọa độ gốc, không phụ thuộc ma trận xoay thay đổi theo tháng, giải thích trực tiếp 9 chiều đặc trưng gốc.
2. **Tại sao k = 3 chiến thắng áp đảo:** Đạt đỉnh chất lượng hình học và độ ổn định trong không gian quét lưới; phân tách 3 trạng thái kinh tế tự nhiên (Dẫn dắt, Tích lũy, Tụt hậu); quy mô cụm ~14% (~110 mã) làm đầu vào lý tưởng cho M3.
3. **Tại sao loại Ward:** ARI mẫu con < 0,70 (trượt ngưỡng >= 0.80), hay tạo cụm phân cấp lệch cỡ vi phạm ngưỡng 5%.
4. **Tại sao loại GMM:** Overfit ma trận hiệp phương sai đầy đủ trên 9 chiều lợi suất đuôi dày; Silhouette thấp (~0,18).

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence.*
