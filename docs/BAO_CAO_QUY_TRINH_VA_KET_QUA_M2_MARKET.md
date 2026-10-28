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
  * **Giai đoạn Phát triển (Development Period):** 60 snapshot tháng, từ `2019-01-31` đến `2023-12-29` (45.646 lượt quan sát mã-tháng). Toàn bộ quá trình khảo sát số cụm k, huấn luyện mô hình, tinh chỉnh siêu tham số và so sánh 4 thuật toán chỉ được thực hiện trên giai đoạn này.
  * **Giai đoạn Ngoại mẫu (Holdout Period):** 24 snapshot tháng, từ `2024-01-31` đến `2025-12-31` (30.155 lượt quan sát mã-tháng). Đóng băng hoàn toàn mô hình từ Development để kiểm định tính bền vững ngoài mẫu.
  * **Giai đoạn Đánh giá cuối (Final Evaluation):** Dữ liệu năm 2026 (dành riêng cho nghiệm thu M3).

### 1.3. Các nguyên tắc nghiên cứu bất biến (Research Invariants)
Theo quy định tại AGENTS.md và METHODOLOGY.md:
1. **Ba lớp đánh giá độc lập:** Chất lượng hình học cụm (Cluster Geometry), Độ ổn định thời gian (Temporal Stability) và Hiệu quả danh mục đầu tư (Portfolio Performance) là ba lớp thước đo hoàn toàn tách biệt.
2. **Vùng cấm tuyệt đối (Forbidden Shortcuts):** Tuyệt đối không sử dụng lợi nhuận tương lai, ROI, Sharpe ratio hay bất kỳ chỉ số đầu tư nào để lựa chọn số cụm k, thuật toán hay hàm khoảng cách.
3. **Phân cụm độc lập từng snapshot tháng:** Không forward-fill giá thiếu, không biến giá trị rỗng thành 0.

---

## 2. CÁC BƯỚC THỰC HIỆN (QUY TRÌNH PHÂN CỤM THỊ TRƯỜNG)

Quy trình phân cụm thị trường tập trung vào chuỗi xử lý học máy từ tiền xử lý dữ liệu, khảo sát số cụm k tối ưu, huấn luyện đối sánh 4 thuật toán đến đánh giá và chọn mô hình tối ưu:

```
[Bước 1: Tiền xử lý & Lọc thanh khoản (Transform T1 & Light Filter)]
                           ↓
[Bước 2: Khảo sát & Chọn số cụm k tối ưu (k = 3..8, tìm điểm uốn Elbow)]
                           ↓
[Bước 3: Huấn luyện đối sánh 4 thuật toán tại k tối ưu (K-Means, PCA, Ward, GMM)]
                           ↓
[Bước 4: Đánh giá Cổng lọc Admissible, Chấm điểm Rank & Chọn mô hình bàn giao M3]
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

### Bước 2: Khảo sát và Lựa chọn số cụm k tối ưu (k = 3 đến 8)
1. **Phương pháp kiểm định điểm uốn (Elbow Method & Geometric Analysis):**
   * Tiến hành quét dải số cụm k từ 3 đến 8 (k = 3, 4, 5, 6, 7, 8) trên tập dữ liệu chuẩn hóa T1 qua 60 snapshot giai đoạn Development (2019–2023).
   * Đánh giá sự biến thiên của 2 chỉ số hình học nòng cốt: Silhouette Score (đo độ tách biệt cụm) và Davies–Bouldin Index (đo độ nén nội cụm trên khoảng cách liên cụm).
2. **Kiểm định tính khả thi vận hành danh mục (Cluster Size Admissibility):**
   * Kiểm tra tỷ lệ cổ phiếu của cụm nhỏ nhất: phải đạt tối thiểu >= 5% số lượng mã (tương đương >= 35–40 mã) ở tối thiểu 80% số snapshot.
   * Loại bỏ ngay các mức k làm xuất hiện các cụm manh mún hoặc cụm rác ngoại lai chỉ có vài mã, gây mất an toàn đa dạng hóa khi đưa sang Milestone M3.

### Bước 3: Huấn luyện đối sánh 4 thuật toán tại k tối ưu (Algorithm Training)
Fit đồng thời 4 thuật toán phân cụm trên số cụm k đã chọn (k = 3) qua 60 snapshot giai đoạn Development (2019–2023) và kiểm chứng 84 snapshot toàn kỳ (2019–2025):
1. **K-Means Baseline:** K-Means++ deterministic, `seed = 42`, `n_init = 10`, `max_iter = 300`.
2. **PCA + K-Means:** Giảm chiều PCA giữ 80% tổng phương sai giải thích (thường giữ lại 3 đến 5 thành phần chính), sau đó fit K-Means (`seed = 42`, `n_init = 10`).
3. **Ward Hierarchical Clustering:** Phân cụm phân cấp ngưng tụ với hàm liên kết phương sai tối thiểu (`linkage = 'ward'`).
4. **Gaussian Mixture Models (GMM):** Mô hình hỗn hợp Gauss xác suất, ma trận hiệp phương sai đầy đủ (`covariance_type = 'full'`), `reg_covar = 0.0001`, `n_init = 2`, `max_iter = 300`.

### Bước 4: Đánh giá và Chọn thuật toán tốt nhất (Comparison Framework)
1. **Cổng kiểm định chất lượng (Admissibility Gate):**
   Một cấu hình chỉ được xem xét nếu thỏa mãn đồng thời 2 điều kiện an toàn:
   * *Cân bằng quy mô cụm:* Cụm nhỏ nhất phải chiếm >= 5% tổng số mã ở >= 80% số snapshot (loại bỏ mô hình tạo cụm rỗng hoặc cụm ngoại lai vài mã).
   * *Độ ổn định lấy mẫu con (Subsample Stability):* Lấy ngẫu nhiên 90% số mã qua 3 random seeds; trung vị chỉ số Adjusted Rand Index (ARI) giữa mô hình fit lại trên mẫu con và nhãn gốc phải đạt >= 0.80.
2. **Quy tắc xếp hạng đa tiêu chí (Rank Score 5 Metrics):**
   Trong các cấu hình vượt qua Cổng chấp nhận, tiến hành chấm điểm và xếp hạng (1 là tốt nhất) trên 5 thước đo độc lập:
   * *Silhouette Score (cao là tốt):* Đo độ nén nội cụm và độ tách biệt giữa các cụm.
   * *Davies–Bouldin Index (thấp là tốt):* Đo tỷ lệ khoảng cách nội cụm trên khoảng cách tâm cụm.
   * *Calinski–Harabasz Index (cao là tốt):* Tỷ số phương sai giữa các cụm trên phương sai nội cụm.
   * *Subsample Stability ARI (cao là tốt):* Đo tính kiên định của nhãn cụm khi lấy mẫu con 90%.
   * *Temporal ARI (cao là tốt):* Đo độ bền vững của nhãn cụm giữa 2 kỳ kế tiếp nhau.
   * *Điểm Rank Score:* Trung bình cộng thứ hạng trên 5 tiêu chí (điểm càng thấp càng tối ưu).

---

## 3. KẾT QUẢ ĐẠT ĐƯỢC VÀ CHỌN THUẬT TOÁN TỐT NHẤT

### 3.1. Kết quả khảo sát lựa chọn số cụm k tối ưu (k = 3 đến 8)
Kết quả thực nghiệm quét sweep số cụm k trên tập dữ liệu thị trường chuẩn hóa T1 qua 60 snapshot giai đoạn Development (2019–2023):

| Số cụm k | Silhouette (cao là tốt) | Davies–Bouldin (thấp là tốt) | Độ ổn định mẫu con 90% (ARI) | Tỷ lệ cụm nhỏ nhất (% mã) | Trạng thái Cổng lọc (Admissible) | Đánh giá kỹ thuật & Kết luận |
|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **k = 3** | **0,276** | **1,52** | **0,96** | **14,0%** | **ĐẠT (Admissible)** | **CHỌN K = 3 TỐI ƯU**: Silhouette đạt đỉnh toàn cục, DB thấp nhất, độ ổn định vượt trội, quy mô cụm cân bằng hoàn hảo. |
| **k = 4** | 0,238 | 1,64 | 0,88 | 8,2% | Đạt | Silhouette sụt giảm 14% so với k=3; độ nén cụm suy giảm; cụm nhỏ bắt đầu co hẹp. |
| **k = 5** | 0,210 | 1,73 | 0,81 | 5,1% | Đạt (sát ngưỡng) | Silhouette tiếp tục giảm; độ phân tách hình học mờ nhạt; quy mô cụm nhỏ chạm sát ngưỡng an toàn 5%. |
| **k = 6** | 0,192 | 1,81 | 0,74 | 3,8% | **TRƯỢT (Failed)** | **Loại**: Vi phạm Cổng lọc (độ ổn định < 0.80 và xuất hiện cụm manh mún < 5% số mã). |
| **k = 7, 8** | < 0,180 | > 1,88 | < 0,70 | < 3,0% | **TRƯỢT (Failed)** | **Loại**: Cụm bị phân mảnh nghiêm trọng; ranh giới cụm mất hoàn toàn tính ổn định. |

**Kết luận bước chọn k:**
1. **Điểm uốn hình học (Geometric Peak):** Mức k = 3 đạt cực đại về Silhouette (0,276) và cực tiểu về Davies–Bouldin (1,52). Khi tăng k >= 4, chất lượng hình học suy giảm đơn điệu.
2. **Ý nghĩa kinh tế học trực quan:** k = 3 phân tách thị trường một cách tự nhiên thành 3 nhóm trạng thái động lượng điều chỉnh rủi ro:
   * *Cụm Dẫn dắt (Leading Cluster):* Động lượng giá trung - dài hạn vượt trội, biến động được kiểm soát.
   * *Cụm Bình ổn / Tích lũy (Consolidating Cluster):* Biến động thấp, sụt giảm tối đa nông, trạng thái phòng thủ.
   * *Cụm Tụt hậu (Lagging Cluster):* Sụt giảm sâu, biến động giảm cao, động lượng tiêu cực.
3. **An toàn thanh khoản & Đa dạng hóa:** Tại k = 3, cụm nhỏ nhất chiếm trung vị 14,0% số mã (~100–120 cổ phiếu giao dịch), cung cấp Universe đủ dày để lọc tài chính và phân bổ danh mục tại M3 mà không lo bị nghẽn thanh khoản.

---

### 3.2. Bảng kết quả đối sánh toàn diện 4 thuật toán tại k = 3
Sau khi đã xác định k = 3 là số cụm tối ưu, tiến hành đối sánh đồng thời 4 thuật toán phân cụm trên 60 snapshot giai đoạn Development (2019–2023) và kiểm chứng 84 snapshot toàn kỳ (2019–2025):

| Thuật toán | Cấu hình k | Trạng thái Cổng lọc (Admissible) | Điểm hạng 5 tiêu chí (Rank Score) | Median Silhouette (cao là tốt) | Median Davies–Bouldin (thấp là tốt) | Độ ổn định mẫu con 90% (ARI) | Độ ổn định thời gian (Temporal ARI) | Đánh giá kỹ thuật |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means** (giữ 80% phương sai) | **k = 3** | **ĐẠT (Admissible)** | **2,40**<br>(Hạng 1 trên Dev) | **0,276** | **1,52** | **0,98** | **0,55** | Dẫn đầu điểm hạng trên Development; giảm chiều giúp lọc bớt tương quan chéo giữa các kỳ động lượng. |
| **K-Means Baseline** (deterministic) | **k = 3** | **ĐẠT (Admissible)** | **2,60**<br>(Hạng 2 trên Dev,<br>Hạng 1 toàn kỳ) | **0,276** | **1,52** | **0,96** | **0,55** | **CHỌN CHÍNH THỨC (A v4)**: Hòa sát nút với PCA+K-Means, đạt chất lượng hình học và độ ổn định tương đương; cấu trúc tối giản theo Occam's Razor, dễ giải thích trực tiếp. |
| **Ward Hierarchical** (liên kết phương sai) | k = 3 | **KHÔNG ĐẠT (Failed Gate)** | Không xếp hạng | ~0,240 | ~1,65 | **< 0,70**<br>(Trượt ngưỡng >= 0.80) | 0,48 | Bị loại ở cổng kiểm định: thuật toán ngưng tụ phân cấp rất nhạy cảm với mẫu con, hay tạo cụm phân cấp lệch cỡ vi phạm quy tắc an toàn >= 5% số mã. |
| **Gaussian Mixture Models (GMM)** | k = 3 | **KHÔNG TỐI ƯU (Rank > 3.50)** | > 3,50 | ~0,180 | ~1,85 | 0,65 – 0,75 | 0,40 | Xếp hạng chót: ma trận hiệp phương sai đầy đủ (full covariance) trên 9 chiều bị overfit vào phân bố đuôi dày của lợi suất tài chính; phân tách hình học kém. |

---

### 3.3. Quyết định chọn thuật toán tốt nhất (Model Selection Decision)
1. **Lựa chọn chính thức:** **K-Means Baseline (k = 3, Model A v4)**.
2. **Luận điểm chọn K-Means Baseline thay vì PCA + K-Means (Occam's Razor):**
   * PCA + K-Means và K-Means Baseline hòa sát nút về chất lượng hình học (Silhouette cùng đạt 0,276; Davies–Bouldin cùng đạt 1,52; ARI thời gian cùng đạt 0,55; ổn định mẫu con 0,98 so với 0,96).
   * K-Means thuần túy trực tiếp trên không gian 9 chiều bảo toàn 100% tọa độ gốc, không phụ thuộc vào ma trận xoay thành phần chính PCA thay đổi theo tháng, giúp việc giải thích hồ sơ cụm (Profile) trên giao diện web và trong báo cáo đầu tư hoàn toàn minh bạch.
3. **Lý do loại bỏ Ward Hierarchical:**
   * Cơ chế ghép cụm ngưng tụ phương sai tối thiểu rất nhạy cảm với việc lấy mẫu con 90% (Subsample Stability ARI chỉ đạt < 0,70, vi phạm tiêu chuẩn nghiên cứu khắt khe >= 0,80).
   * Ward thường xuyên tạo ra các nhánh phân cấp có quy mô bất đối xứng cao, làm xuất hiện các cụm nhỏ dưới 5% vi phạm điều kiện đa dạng hóa danh mục.
4. **Lý do loại bỏ GMM:**
   * Dữ liệu lợi suất tài chính trên TTCK Việt Nam có hiện tượng đuôi dày (heavy tails) và phân bố bất đối xứng.
   * GMM với ma trận hiệp phương sai đầy đủ trên 9 chiều bị overfit nghiêm trọng vào mật độ cục bộ, dẫn đến ranh giới cụm mờ nhạt và điểm phân tách Silhouette rất thấp (~0,18).

---

### 3.4. Kết quả kiểm chứng tính khách quan (Development 2019–2023 vs Toàn kỳ)
Để bảo đảm tính tuân thủ nghiên cứu khắt khe (không nhìn trước vào Holdout 2024–2025), thực nghiệm `run_clustering_rework_v2.py --config configs/experiments/clustering_rework_v2_dev.json` đã được chạy với điều kiện chặn cứng `until: "2023-12-29"`:
* Khi chỉ nhìn dữ liệu Development (2019–2023): **k = 3** vẫn là số cụm tối ưu được lựa chọn.
* PCA + K-Means đạt hạng trung bình 2,40; K-Means đạt hạng 2,60 (hai thuật toán có chất lượng tương đương với cùng Silhouette 0,276 và độ ổn định 0,98 / 0,96).
* Kết luận: Lựa chọn **k = 3** hoàn toàn đứng vững từ giai đoạn Development mà không phụ thuộc vào dữ liệu ngoại mẫu.

---

### 3.5. Bàn giao sang Milestone M3 (Quyết định D-DIR-01)
Dựa trên kết quả thực nghiệm đối chứng, ngày 26/10/2026, Project Owner đã chính thức ban hành **Quyết định D-DIR-01** (ghi nhận tại docs/DECISIONS.md):
1. **Mô hình thị trường chính thức:** Chọn mô hình **A của Bundle v4 (K-Means, k = 3, 9 đặc trưng, lọc thanh khoản nhẹ, biến đổi T1)** làm mô hình chuẩn duy nhất của Milestone M2 để tích hợp sang Milestone M3. Dữ liệu nhãn cụm, centroid, profile và tọa độ trực quan hóa được đóng gói bất biến vào cơ sở dữ liệu `terminal.sqlite` tại data/web/delta-intelligence-v4/.
2. **Cơ chế xác định Cụm dẫn dắt thị trường (Market Leading Cluster):** Xác định cơ học theo snapshot: chọn cụm có trung vị `mom_126` cao nhất; nếu hòa chọn cụm có trung vị `mdd_126` nông hơn (theo đề xuất Q5 trong M3 Plan).
3. **Trạng thái Engine M3:** Engine mô phỏng và backtest tại src/delta_t1/m3/ đã hoàn thành và vượt qua 25 bài kiểm thử đơn vị tự động.

---

## 4. TÓM TẮT TRỌNG TÂM ĐƯA VÀO SLIDE THUYẾT TRÌNH (SLIDE-READY HIGHLIGHTS)

### Slide 03: Quy trình phân cụm dữ liệu thị trường (M2 Pipeline)
* **Bước 1 - Tiền xử lý & Lọc thanh khoản:** Tách mã kém thanh khoản (< 10 triệu đ/ngày hoặc > 50% phiên tắt thanh khoản) gán cờ `ILLIQUID` (-1). Chuẩn hóa T1: log1p thanh khoản, winsorize 1%–99%, z-score độc lập từng tháng.
* **Bước 2 - Khảo sát & Chọn k tối ưu (k = 3..8):** Quét dải k từ 3 đến 8 để tìm điểm uốn (Elbow) tối đa hóa Silhouette, tối thiểu hóa Davies-Bouldin và đảm bảo cụm cân bằng >= 5% số mã.
* **Bước 3 - Huấn luyện đối sánh 4 thuật toán tại k = 3:** Fit đồng thời K-Means, PCA + K-Means (giữ 80% phương sai), Ward Hierarchical và GMM (full covariance) trên số cụm k đã chọn.
* **Bước 4 - Cổng lọc Admissible & Chấm điểm Rank 5 tiêu chí:** Lọc điều kiện bền vững (ARI mẫu con 90% >= 0.80), sau đó xếp hạng đa tiêu chí (Rank Score) để chọn ra thuật toán chiến thắng.

### Slide 04: Khảo sát & Lựa chọn Số cụm k Tối ưu (k = 3 đến 8)
* **Số liệu thực nghiệm:**
  * k = 3: Silhouette = 0,276 (Đỉnh); Davies–Bouldin = 1,52 (Thấp nhất); Độ ổn định = 0,96; Cụm nhỏ nhất = 14,0% -> **CHỌN K = 3 TỐI ƯU**.
  * k = 4: Silhouette = 0,238 (-14%); DB = 1,64; Cụm nhỏ co lại 8,2%.
  * k = 5: Silhouette = 0,210; DB = 1,73; Cụm nhỏ chạm sát ngưỡng 5,1%.
  * k >= 6: Silhouette < 0,195; DB > 1,80; Độ ổn định < 0,74; Cụm rác < 4% -> **TRƯỢT CỔNG LỌC**.
* **Ý nghĩa kinh tế:** Phân tách thị trường thành 3 trạng thái rõ nét: Cụm Dẫn dắt (Leading), Cụm Tích lũy (Consolidating), và Cụm Tụt hậu (Lagging).

### Slide 05: Bảng ma trận đối sánh 4 thuật toán thị trường tại k = 3

| Thuật toán | Cấu hình k | Cổng lọc (Admissible) | Điểm xếp hạng (Rank) | Silhouette | Davies-Bouldin | Ổn định mẫu con (ARI) | Trạng thái nghiệm thu |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means** | **k = 3** | **ĐẠT** | **2,40** (Hạng 1 Dev) | 0,276 | 1,52 | **0,98** | Dẫn đầu điểm hạng; giảm chiều khử nhiễu tốt |
| **K-Means Baseline** | **k = 3** | **ĐẠT** | **2,60** (Hạng 2 Dev) | 0,276 | 1,52 | **0,96** | **CHỌN CHÍNH THỨC (A v4)**: Hòa sát nút, tối giản, trực quan |
| **Ward Hierarchical** | k = 3 | **TRƯỢT** | Bị loại | ~0,240 | ~1,65 | < 0,70 | Loại vì không ổn định mẫu con và cụm bị lệch cỡ |
| **GMM (Gaussian)** | k = 3 | **KÉM** | > 3,50 | ~0,180 | ~1,85 | 0,65 – 0,75 | Loại vì overfit ma trận hiệp phương sai 9 chiều |

### Slide 06: Quyết định chọn mô hình thị trường & 4 Luận điểm phản biện
1. **Tại sao K-Means được chọn thay vì PCA + K-Means:** Hòa sát nút về chất lượng hình học (Silhouette cùng 0,276; DB cùng 1,52; ARI thời gian cùng 0,55; ổn định mẫu con 0,98 vs 0,96). K-Means thắng nhờ Occam's Razor: bảo toàn 100% tọa độ gốc, không phụ thuộc ma trận xoay thay đổi theo tháng, giải thích trực tiếp 9 chiều đặc trưng gốc.
2. **Tại sao loại Ward:** ARI mẫu con < 0,70 (trượt ngưỡng >= 0.80), hay tạo cụm phân cấp lệch cỡ vi phạm ngưỡng 5%.
3. **Tại sao loại GMM:** Overfit ma trận hiệp phương sai đầy đủ trên 9 chiều lợi suất đuôi dày; Silhouette thấp (~0,18).
4. **Tại sao chọn k = 3:** Điểm uốn tối ưu hình học; mang ý nghĩa kinh tế 3 trạng thái rõ nét (Dẫn dắt, Tích lũy, Tụt hậu); quy mô cụm ~14% (100–120 mã) làm đầu vào dày dặn cho M3.

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence.*
