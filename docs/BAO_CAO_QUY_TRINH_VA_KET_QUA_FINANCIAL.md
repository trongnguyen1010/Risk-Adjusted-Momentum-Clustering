# BÁO CÁO QUY TRÌNH THỰC HIỆN VÀ KẾT QUẢ PHÂN CỤM DỮ LIỆU TÀI CHÍNH (HỆ B)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** 26/10/2026 (theo Quyết định D-DIR-01)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và các artifact đã thực thi trong repository.

---

## 1. TỔNG QUAN VÀ BỐI CẢNH NGHIÊN CỨU

### 1.1. Mục tiêu của Hệ Dữ liệu Tài chính (Hệ B)
Hệ dữ liệu tài chính trong dự án DELTA đảm nhận hai vai trò chiến lược:
1. **Lớp phân cụm mô tả (Descriptive Clustering - Hệ B):** Phân nhóm các doanh nghiệp phi tài chính theo các tỷ số tài chính cốt lõi nhằm xác định các cụm doanh nghiệp có chất lượng cơ bản lành mạnh, khả năng sinh lời cao và đòn bẩy an toàn.
2. **Lớp chỉ số sản phẩm và bộ lọc chất lượng (Indicators & Quality Overlay):** Cung cấp hệ thống chỉ số tài chính chuẩn hóa và các hệ thống điểm sức khỏe tài chính chuyên sâu (Piotroski F-score, Altman Z-score, Beneish M-score) để làm chốt chặn an toàn khi lựa chọn danh mục đầu tư tại Milestone M3.

### 1.2. Tập dữ liệu đầu vào và phân định thời gian
* **Dữ liệu đầu vào:** Ma trận các tỷ số tài chính của 1.172 doanh nghiệp phi tài chính niêm yết có đầy đủ báo cáo tài chính qua 9 năm tài chính (2017–2025), gồm 2 không gian khảo sát:
  * `B_base` (9 chỉ số cốt lõi): ROE, ROA, Biên gộp, Biên ròng, Nợ/VCSH, Thanh toán hiện hành, Vòng quay tài sản, Tăng trưởng doanh thu, CFO/LNST.
  * `B_value` (12 chỉ số): Bộ 9 chỉ số trên kết hợp thêm E/P (Earnings Yield), B/P (Book-to-Price) và log vốn hóa thị trường.
* **Nguyên tắc nghiên cứu bất biến:**
  1. *Nguyên tắc Point-In-Time (PIT):* Chỉ sử dụng báo cáo tài chính đã thực sự công bố ra thị trường (`usable_from_date <= decision_date`). Tuyệt đối không lấy ngày kết thúc niên độ kế toán (`period_end`) để tránh rò rỉ thông tin tương lai.
  2. *Không làm đẹp dữ liệu:* Dữ liệu thiếu giữ nguyên null, không điền 0, không forward-fill giữa các năm tài chính, không xóa bỏ giá trị cực đoan tùy tiện.
  3. *Phân định ranh giới ngành:* Chỉ phân cụm trên nhóm doanh nghiệp phi tài chính; các định chế tài chính (Ngân hàng, Chứng khoán, Bảo hiểm) có cấu trúc tài sản đặc thù được tách riêng.

---

## 2. CÁC BƯỚC THỰC HIỆN (QUY TRÌNH PHÂN CỤM TÀI CHÍNH)

Quy trình phân cụm tài chính tập trung vào chuỗi xử lý học máy từ tiền xử lý không gian tỷ số, huấn luyện thuật toán đến đánh giá độ ổn định và lựa chọn mô hình:

```
[Bước 1: Tiền xử lý dữ liệu tài chính (Transform T1 per fiscal year)]
                           ↓
[Bước 2: Huấn luyện & Quét 4 thuật toán (K-Means, PCA, Ward, GMM với k = 3..8)]
                           ↓
[Bước 3: Đánh giá & So sánh các thuật toán (Cổng kiểm định độ ổn định mẫu con)]
                           ↓
[Bước 4: Chọn mô hình mô tả & Thiết lập chốt chặn chất lượng sang Milestone M3]
```

### Bước 1: Tiền xử lý dữ liệu tài chính (Transform T1)
1. **Thiết lập không gian tỷ số tài chính:**
   * Khảo sát độc lập 2 bộ đặc trưng: `B_base` (9 chỉ số tài chính thuần túy) và `B_value` (12 chỉ số kết hợp yếu tố định giá thị trường).
2. **Quy trình chuẩn hóa T1 (Transform T1 per fiscal year):**
   * *Log quy mô:* Lấy log tự nhiên các biến quy mô: `log(market_cap)`.
   * *Cắt đuôi ngoại lai (Winsorization):* Cắt đuôi tại phân vị 1% và 99% theo từng năm để triệt tiêu ảnh hưởng của các trường hợp âm vốn chủ sở hữu nặng hoặc tỷ lệ nợ/tài sản đột biến dị biệt.
   * *Chuẩn hóa Z-Score per-snapshot:* Chuẩn hóa trung bình và độ lệch chuẩn độc lập theo từng năm tài chính, không trộn lẫn dữ liệu giữa các năm để bảo đảm nguyên tắc Point-In-Time.

### Bước 2: Khảo sát số cụm k và Huấn luyện 4 thuật toán phân cụm (Algorithm Training)
Quét đồng thời 4 thuật toán phân cụm trên dải số cụm k từ 3 đến 8 (k = 3, 4, 5, 6, 7, 8) qua 9 năm tài chính (2017–2025), thực hiện độc lập trên cả giai đoạn Development (<= 2023) và toàn kỳ:
1. **Khảo sát số cụm k (k = 3 đến 8):**
   * *Mức k = 3:* Đạt độ ổn định tương đối cao nhất (ARI ~ 0,50) và là mức k duy nhất duy trì được tính cân bằng cụm (tỷ lệ cụm nhỏ nhất luôn >= 5% số mã qua các năm, không có cụm rác).
   * *Mức k >= 4:* Độ ổn định suy giảm mạnh (ARI < 0,40); bắt đầu xuất hiện các cụm manh mún dưới 5% số doanh nghiệp do dữ liệu tài chính bị kéo lệch bởi các trường hợp cá biệt.
   -> **Lựa chọn k = 3** làm số cụm cơ sở cho mô hình phân cụm tài chính.
2. **Huấn luyện 4 họ thuật toán tại k khảo sát:**
   * **K-Means Baseline:** K-Means++ deterministic, `seed = 42`, `n_init = 10`, `max_iter = 300`.
   * **PCA + K-Means:** Giảm chiều PCA giữ 80% tổng phương sai giải thích, sau đó fit K-Means (`seed = 42`, `n_init = 10`).
   * **Ward Hierarchical Clustering:** Phân cụm ngưng tụ phân cấp phương sai tối thiểu (`linkage = 'ward'`).
   * **Gaussian Mixture Models (GMM):** Mô hình hỗn hợp Gauss đa biến xác suất (`covariance_type = 'full'`, `n_init = 2`, `reg_covar = 0.0001`, `max_iter = 300`).

### Bước 3: Đánh giá và So sánh các thuật toán (Comparison Framework)
1. **Cổng kiểm định độ ổn định (Admissibility Gate):**
   * Yêu cầu độ ổn định khi lấy mẫu con 90% (Subsample Stability): Lấy ngẫu nhiên 90% số doanh nghiệp qua 3 random seeds; trung vị chỉ số Adjusted Rand Index (ARI) giữa mô hình fit lại trên mẫu con và nhãn gốc phải đạt >= 0.80.
   * Cụm nhỏ nhất phải chiếm >= 5% số doanh nghiệp ở >= 80% số năm tài chính (không chấp nhận cụm rỗng hoặc cụm ngoại lai).
2. **Hệ thống thước đo so sánh:**
   * *Subsample Stability ARI (cao là tốt):* Đo lường tính vững chắc của ranh giới cụm trước các biến động chọn mẫu.
   * *Silhouette Score (cao là tốt):* Đo độ nén nội cụm và mức độ phân tách giữa các cụm tài chính.
   * *Davies–Bouldin Index (thấp là tốt):* Đo tỷ lệ khoảng cách nội cụm trên khoảng cách tâm cụm.
   * *Tỷ lệ cân bằng cụm:* Kiểm tra sự xuất hiện của các cụm thiểu số dị biệt.

---

## 3. KẾT QUẢ ĐẠT ĐƯỢC VÀ CHỌN THUẬT TOÁN TỐT NHẤT

### 3.1. Bảng kết quả đối sánh toàn diện 4 thuật toán trên Hệ B (k = 3..8)
Kết quả thực nghiệm quét sweep trên 9 năm tài chính (2017–2025) tại [configs/experiments/clustering_rework_v2.json](configs/experiments/clustering_rework_v2.json) và script [scripts/run_clustering_rework_v2.py](scripts/run_clustering_rework_v2.py):

| Thuật toán | Cấu hình k khảo sát | Độ ổn định mẫu con 90% (ARI) | Median Silhouette Score | Median Davies–Bouldin | Cân bằng tỷ lệ cụm (>= 5% số mã) | Trạng thái Cổng lọc (Admissible) | Đánh giá kỹ thuật |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **K-Means Baseline** (deterministic) | **k = 3** | **~0,50**<br>(Trượt ngưỡng >= 0.80) | ~0,18 – 0,22 | ~1,65 – 1,80 | **Đạt**<br>(Không có cụm rỗng) | **KHÔNG ĐẠT (None Admissible)** | **Chọn làm Baseline mô tả (B v4)**: Đạt độ ổn định cao nhất trong 4 thuật toán; cụm phân bố tương đối đều, có ý nghĩa phân loại cơ bản. |
| **PCA + K-Means** (giữ 80% phương sai) | k = 3 | ~0,48<br>(Trượt ngưỡng >= 0.80) | ~0,19 – 0,21 | ~1,68 – 1,82 | **Đạt** | **KHÔNG ĐẠT (None Admissible)** | Giảm chiều PCA không giúp tăng độ ổn định do phương sai tài chính phân tán đều giữa các nhóm sinh lời, thanh toán và đòn bẩy. |
| **Ward Hierarchical** (liên kết ngưng tụ) | k = 3..8 | **< 0,40**<br>(Rất thấp) | ~0,15 – 0,18 | ~1,85 – 2,10 | **Trượt**<br>(Hay có cụm < 5%) | **KHÔNG ĐẠT (None Admissible)** | Rất nhạy cảm với các tỷ số tài chính cực đoan (âm vốn, nợ cao); cây phân cấp bị lệch nặng và tính ổn định kém. |
| **Gaussian Mixture Models (GMM)** | k = 3..8 | **< 0,35**<br>(Kém nhất) | ~0,12 – 0,16 | ~2,10 – 2,40 | Không ổn định | **KHÔNG ĐẠT (None Admissible)** | Không hội tụ ổn định; ma trận hiệp phương sai 9 chiều dễ gặp hiện tượng suy biến hoặc đa cộng tuyến kế toán giữa các chỉ số biên lợi nhuận. |

* **Kết luận khoa học chính thức:** **Không có cấu hình nào đạt ngưỡng chấp nhận (None admissible)** ở cả 2 bộ chỉ số (`B_base` và `B_value`), trên cả toàn kỳ (2017–2025) lẫn khi chỉ sàng lọc giai đoạn Development (<= 2023).

### 3.2. Phân tích nguyên nhân kinh tế học tại sao BCTC không đạt ARI >= 0.80
1. **Độ phân tán liên ngành tự nhiên:** Các doanh nghiệp thuộc các ngành khác nhau (sản xuất công nghiệp, bất động sản, bán lẻ, công nghệ) có mô hình kinh doanh hoàn toàn khác biệt. Tỷ số nợ, vòng quay tài sản hay biên lợi nhuận phân bố rất rộng và không tạo thành các cụm hình cầu tự nhiên.
2. **Cú sốc kinh tế vĩ mô qua các năm:** Giai đoạn 2017–2025 chứng kiến nhiều biến cố lớn (COVID-19 2020–2021, đóng băng trái phiếu doanh nghiệp và bất động sản 2022–2023, biến động lãi suất). Cấu trúc tài chính của cùng một doanh nghiệp có thể thay đổi đột ngột giữa 2 năm tài chính kế tiếp.
3. **Tính trung thực khoa học của DELTA:** Dự án kiên quyết tuân thủ nguyên tắc không "nắn chỉnh dữ liệu" (không forward-fill, không điền số 0 giả tạo, không cherry-pick mã tốt). Kết quả ARI ~ 0,50 phản ánh đúng bản chất biến động thực tế của nền kinh tế Việt Nam.

### 3.3. Quyết định kiến trúc và Chọn thuật toán tốt nhất (Architectural Decision)
Dựa trên kết quả thực nghiệm và Quyết định D-DIR-01:
1. **Thuật toán được chọn:** **K-Means Baseline (k = 3, bộ đặc trưng B_base)**.
2. **Vai trò mô hình:** Đóng vai trò là **Mô hình phân cụm tài chính mô tả cơ sở (Descriptive Baseline - Model B v4)**.
3. **Gắn nhãn minh bạch:** Ghi chú rõ ràng trên giao diện web và tài liệu: *"Mô hình tài chính cơ sở mang tính mô tả, độ ổn định lấy mẫu con đạt ARI 0,50 (chưa đạt ngưỡng tối ưu 0,80)"*.
4. **Giải pháp bù đắp chất lượng cho Milestone M3:**
   * Không phụ thuộc duy nhất vào nhãn cụm tài chính để ra quyết định đầu tư.
   * Milestone M3 tích hợp bổ sung hệ thống chỉ số chuẩn hóa độc lập (D-IND-01) làm chốt chặn chất lượng: yêu cầu cổ phiếu đạt điểm sức khỏe tài chính Piotroski F-Score >= 7 (đà tăng trưởng mạnh) và Altman Z-Score >= 1.81 (vùng an toàn tài chính, phòng tránh kiệt quệ).

### 3.4. Bàn giao sang Milestone M3
1. **Xác định Cụm dẫn dắt tài chính (Financial Leading Cluster):** Được chọn cơ học theo từng snapshot dựa vào hồ sơ trung vị: Chọn cụm có **trung vị ROE cao nhất**; nếu hòa điểm chọn cụm có **trung vị Nợ/VCSH thấp hơn**.
2. **Kết hợp danh mục:** Candidate Universe là phần giao giữa Cụm dẫn dắt thị trường (Hệ A) và Cụm dẫn dắt tài chính (Hệ B) đã thỏa mãn kiểm tra tính sẵn sàng `usable_from_date <= decision_date`.

---

## 4. TÓM TẮT TRỌNG TÂM ĐƯA VÀO SLIDE THUYẾT TRÌNH (SLIDE-READY HIGHLIGHTS)

### Slide 1: Quy trình phân cụm dữ liệu tài chính (Financial Pipeline)
* **Tiền xử lý Transform T1:** Lấy log quy mô, cắt đuôi ngoại lai (Winsorize 1%–99%), chuẩn hóa z-score độc lập từng năm tài chính (giữ vững nguyên tắc Point-In-Time).
* **Huấn luyện thuật toán:** Quét đồng thời 4 thuật toán (K-Means, PCA+K-Means, Ward, GMM) với k từ 3 đến 8 trên 1.172 doanh nghiệp phi tài chính qua 9 năm tài chính (2017–2025).
* **Đánh giá & Kết luận:** Kiểm định độ ổn định lấy mẫu con 90% (ngưỡng chuẩn ARI >= 0.80).

### Slide 2: Bảng đối sánh 4 thuật toán trên Dữ liệu Tài chính (Hệ B)

| Thuật toán | Cấu hình k | Ổn định mẫu con (ARI) | Silhouette Score | Davies–Bouldin | Cân bằng cụm | Kết luận nghiệm thu |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **K-Means Baseline** | **k = 3** | **~0,50** | ~0,18 – 0,22 | ~1,65 – 1,80 | Tốt (>= 5%) | **CHỌN LÀM BASELINE MÔ TẢ (B v4)** kèm cảnh báo |
| **PCA + K-Means** | k = 3 | ~0,48 | ~0,19 – 0,21 | ~1,68 – 1,82 | Tốt (>= 5%) | Trượt cổng ổn định; PCA không cải thiện được độ phân tán |
| **Ward Hierarchical** | k = 3..8 | < 0,40 | ~0,15 – 0,18 | ~1,85 – 2,10 | Kém (< 5%) | Trượt cổng; nhạy cảm với ngoại lai và lệch cỡ cụm |
| **GMM (Gaussian)** | k = 3..8 | < 0,35 | ~0,12 – 0,16 | ~2,10 – 2,40 | Kém | Trượt cổng; không hội tụ ổn định trên 9 chiều kế toán |

* **Kết luận chung:** **Không có thuật toán nào đạt ngưỡng nghiên cứu chuẩn (ARI >= 0.80)**. K-Means k=3 đạt kết quả tốt nhất trong 4 phương án (~0,50).

### Slide 3: Bản chất kinh tế học — Tại sao BCTC không đạt ARI >= 0.80?
1. **Độ phân tán liên ngành tự nhiên:** Các doanh nghiệp thuộc các ngành khác nhau (sản xuất công nghiệp, bất động sản, bán lẻ, công nghệ) có mô hình kinh doanh hoàn toàn khác biệt. Tỷ số nợ, vòng quay tài sản hay biên lợi nhuận phân bố rất rộng và không tạo thành các cụm hình cầu tự nhiên.
2. **Cú sốc kinh tế vĩ mô qua các năm:** Giai đoạn 2017–2025 chứng kiến nhiều biến cố lớn (COVID-19 2020–2021, biến động trái phiếu doanh nghiệp và bất động sản 2022–2023, biến động lãi suất). Cấu trúc tài chính của cùng một doanh nghiệp có thể thay đổi đột ngột giữa 2 năm tài chính kế tiếp.
3. **Tính trung thực khoa học của DELTA:** Dự án kiên quyết tuân thủ nguyên tắc không "nắn chỉnh dữ liệu" (không forward-fill, không điền số 0 giả tạo, không cherry-pick mã tốt). Kết quả ARI ~ 0,50 phản ánh đúng bản chất biến động thực tế của nền kinh tế Việt Nam.

### Slide 4: Giải pháp kiến trúc của DELTA và Ứng dụng thực tiễn cho M3
1. **Phân tách ranh giới rõ ràng:** Mô hình B (K-Means k=3) chỉ đóng vai trò phân cụm mô tả (Descriptive Clustering) với cảnh báo minh bạch trên hệ thống.
2. **Chốt chặn an toàn với Lớp chỉ số sản phẩm:** Tích hợp độc lập hệ thống điểm sức khỏe tài chính Piotroski F-score (>= 7) và Altman Z-score (>= 1.81) làm chốt chặn an toàn tại M3.
3. **Chiến lược đầu tư tích hợp:** Candidate Universe là giao giữa Cụm dẫn dắt thị trường (Hệ A) và Cụm dẫn dắt tài chính (Hệ B) sau khi kiểm tra tính khả dụng PIT (`usable_from_date <= decision_date`).

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence.*
