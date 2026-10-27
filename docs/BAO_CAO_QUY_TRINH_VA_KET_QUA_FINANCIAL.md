# BÁO CÁO QUY TRÌNH THỰC HIỆN VÀ KẾT QUẢ PHÂN CỤM DỮ LIỆU TÀI CHÍNH (HỆ B)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** 26/10/2026 (theo Quyết định D-IND-01, D-CRAWL-02 và D-DIR-01)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và các artifact đã thực thi trong repository.

---

## 1. TỔNG QUAN VÀ NGUYÊN TẮC NGHIÊN CỨU

### 1.1. Mục tiêu của Hệ Dữ liệu Tài chính (Hệ B)
Hệ dữ liệu tài chính trong dự án DELTA đảm nhận hai vai trò chiến lược:
1. **Lớp phân cụm mô tả (Descriptive Clustering - Hệ B):** Phân nhóm các doanh nghiệp phi tài chính theo các tỷ số tài chính cốt lõi nhằm xác định các cụm doanh nghiệp có chất lượng cơ bản lành mạnh, khả năng sinh lời cao và đòn bẩy an toàn.
2. **Lớp chỉ số sản phẩm và bộ lọc chất lượng (Indicators & Quality Overlay):** Cung cấp hệ thống 15 chỉ số tài chính chuẩn hóa (P/E, P/B, ROE, ROA...) và 3 hệ thống điểm sức khỏe tài chính chuyên sâu (Piotroski F-score, Beneish M-score, Altman Z-score) để sàng lọc và xếp hạng cổ phiếu trong bài toán xây dựng danh mục đầu tư tại Milestone M3.

### 1.2. Các nguyên tắc nghiên cứu bất biến (Research Invariants)
Theo quy định tại [AGENTS.md](AGENTS.md) và [docs/DATA_CONTRACT.md](docs/DATA_CONTRACT.md):
1. **Nguyên tắc Point-In-Time (PIT):** Tại ngày ra quyết định `decision_date` t, chỉ được sử dụng các báo cáo tài chính đã thực sự công bố và sẵn sàng trên thị trường (`usable_from_date <= t`). Tuyệt đối không lấy ngày kết thúc kỳ kế toán (`period_end`) làm ngày ra quyết định để tránh rò rỉ thông tin tương lai (Look-ahead bias).
2. **Không làm đẹp dữ liệu (No Imputation / No Distortion):** Dữ liệu tài chính thiếu bắt buộc phải để `null`, tuyệt đối không điền 0, không forward-fill giữa các năm tài chính, không xóa bỏ các giá trị cực đoan một cách tùy tiện.
3. **Phân định rõ ranh giới ngành:** Các định chế tài chính (Ngân hàng, Công ty Chứng khoán, Công ty Bảo hiểm) có cấu trúc BCTC đặc thù, không áp dụng công thức của doanh nghiệp thông thường và không đưa vào mô hình phân cụm của doanh nghiệp phi tài chính.

---

## 2. CÁC BƯỚC THỰC HIỆN (QUY TRÌNH DỮ LIỆU VÀ PHÂN CỤM TÀI CHÍNH)

Quy trình xây dựng hệ dữ liệu và phân cụm tài chính được thực thi tuần tự qua 5 bước có cấu trúc chặt chẽ:

```
[Bước 1: Thu thập & Chuẩn hóa BCTC 10 năm (2016–2025)] 
       ↓ 
[Bước 2: Xây dựng Lớp chỉ số Indicators v1 & Điểm F/M/Z (D-IND-01)] 
       ↓ 
[Bước 3: Thu thập Ngày công bố BCTC phục vụ PIT (D-CRAWL-02)] 
       ↓ 
[Bước 4: Thiết lập không gian phân cụm T1 (B_base & B_value)] 
       ↓ 
[Bước 5: Quét thực nghiệm đối sánh 4 thuật toán (k = 3 đến 8)]
```

### Bước 1: Thu thập và chuẩn hóa dữ liệu BCTC 10 năm liên tục (2016–2025)
* **Khảo sát nguồn và Pilot đối soát:** Thử nghiệm Pilot 5 mã (BRC, FPT, MWG, GMD, VNM) đối chiếu chi tiết 100% số liệu API với báo cáo tài chính kiểm toán gốc định dạng PDF (đạt 29/30 bộ chỉ số đối chứng chính xác).
* **Mở rộng toàn thị trường:** Triển khai qua mẫu 20 mã, 50 mã và mở rộng lên toàn bộ 1.522 mã cổ phiếu ứng viên (Securities Registry).
* **Kết quả làm sạch:** Thu thập thành công **1.172 mã cổ phiếu phi tài chính có đầy đủ BCTC cả 10 năm liên tục (2016–2025)**, tạo thành tập mẫu chuẩn 11.720 dòng quan sát (chi tiết tại [artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md](artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md)).

### Bước 2: Xây dựng Lớp chỉ số sản phẩm Indicators v1 (Quyết định D-IND-01)
Theo Quyết định D-IND-01 ngày 24/10/2026, nhóm nghiên cứu đã xây dựng engine tính toán chỉ số độc lập tại [src/delta_t1/indicators/compute.py](src/delta_t1/indicators/compute.py) và cơ sở dữ liệu `indicators.sqlite`:
1. **Quy tắc chuẩn thị trường Việt Nam:**
   * Số lượng cổ phiếu lưu hành: `shares = Vốn góp cổ phiếu phổ thông / 10.000 đ` (mệnh giá luật định).
   * Lợi nhuận trước lãi vay và thuế: `ebit = LNTT + Chi phí lãi vay`.
   * Giá thị trường tính P/E, P/B: Giá đóng cửa thực tế (`raw_close`) của phiên giao dịch cuối cùng <= 31/12 của năm tài chính đó.
2. **Hệ thống 15 chỉ số tài chính cơ bản:** Gồm đầy đủ các nhóm Định giá (EPS, BVPS, P/E, P/B, Vốn hóa), Sinh lời (ROE, ROA, Biên gộp, Biên ròng), Tăng trưởng (Doanh thu, Lợi nhuận), và An toàn tài chính (Nợ/VCSH, Thanh toán hiện hành, Vòng quay tài sản, CFO/LNST).
3. **Ba hệ thống điểm chất lượng chuyên sâu:**
   * **Piotroski F-Score (Thang điểm 0–9):** Đánh giá toàn diện 9 tín hiệu về khả năng sinh lời, đòn bẩy, thanh khoản và hiệu quả hoạt động. 7–9 điểm: Rất mạnh; 4–6: Trung bình; 0–3: Yếu.
   * **Beneish M-Score:** Mô hình 8 biến số phát hiện bất thường kế toán. Ngưỡng M > -1.78 cảnh báo rủi ro thao túng BCTC cao.
   * **Altman Z-Score:** Dự báo nguy cơ kiệt quệ tài chính. Z > 2.99: An toàn; 1.81 <= Z <= 2.99: Cảnh báo; Z < 1.81: Nguy hiểm.

### Bước 3: Thu thập Ngày công bố BCTC phục vụ Point-In-Time (Quyết định D-CRAWL-02)
Để loại bỏ hoàn toàn hiện tượng rò rỉ thông tin tương lai (Look-ahead bias) khi đưa dữ liệu vào Milestone M3:
* **Thu thập API CafeF CreateDate:** Thực thi script [scripts/crawl_cafef_disclosure_dates.py](scripts/crawl_cafef_disclosure_dates.py), trích xuất trường thời gian gửi tài liệu (`CreateDate`) của các BCTC năm đã kiểm toán cho 1.362 mã cổ phiếu.
* **Quy tắc xác định ngày sử dụng thông tin (`usable_from_date`):**
  * *Năm tài chính từ 2022 trở đi (`CAFEF_DISCLOSURE`):* Sử dụng ngày gửi sớm nhất từ CafeF. `usable_from_date` là phiên giao dịch đầu tiên **sau** ngày gửi tài liệu.
  * *Năm tài chính trước 2022 (`LAG_RULE`):* Do CafeF nhập lại dữ liệu lịch sử vào 26/11/2022, hệ thống áp dụng nguyên tắc bảo thủ: `usable_from_date` là phiên giao dịch đầu tiên sau ngày **30/06 của năm tiếp theo** (t+1).
* Tạo lập bảng dữ liệu khả dụng `availability.csv` với 13.620 bản ghi mã - năm tài chính.

### Bước 4: Thiết lập không gian phân cụm T1 (Transform T1)
Khảo sát phân cụm trên 2 bộ không gian đặc trưng:
* `B_base` (9 chỉ số cốt lõi): ROE, ROA, Biên gộp, Biên ròng, Nợ/VCSH, Thanh toán hiện hành, Vòng quay tài sản, Tăng trưởng doanh thu, CFO/LNST.
* `B_value` (12 chỉ số): Bộ 9 chỉ số trên kết hợp thêm E/P (Earnings Yield), B/P (Book-to-Price) và log vốn hóa thị trường.
* **Quy trình tiền xử lý T1:** Lấy log các biến quy mô, cắt đuôi ngoại lai (Winsorization) 1%–99%, chuẩn hóa z-score độc lập theo từng năm tài chính (không trộn lẫn các năm).

### Bước 5: Thiết kế thực nghiệm và Khảo sát 4 thuật toán (k = 3 đến 8)
Quét đồng thời cả 4 thuật toán trên dải k từ 3 đến 8 (k = 3, 4, 5, 6, 7, 8) qua các năm tài chính từ 2017 đến 2025:
1. **K-Means Baseline:** deterministic, `n_init = 10`, `seed = 42`.
2. **PCA + K-Means:** Giảm chiều PCA giữ 80% phương sai, sau đó fit K-Means.
3. **Ward Hierarchical Clustering:** Phân cụm ngưng tụ phân cấp phương sai tối thiểu (`linkage = 'ward'`).
4. **Gaussian Mixture Models (GMM):** Mô hình hỗn hợp Gauss đa biến (`covariance_type = 'full'`, `n_init = 2`, `reg_covar = 0.0001`).
* **Cổng kiểm định chất lượng:** Yêu cầu độ ổn định lấy mẫu con 90% (Subsample Stability ARI qua 3 random seeds) phải đạt trung vị >= 0.80.

---

## 3. KẾT QUẢ ĐẠT ĐƯỢC

### 3.1. Kết quả làm sạch dữ liệu BCTC và Lớp chỉ số sản phẩm
* **Độ phủ dữ liệu (Coverage):** Đạt trên **88% – 90%** số mã cổ phiếu có đầy đủ bộ chỉ số cơ bản và điểm F/M/Z hoàn chỉnh trong các năm tài chính 2024–2025.
* **Kiểm định QA độc lập:** Kiểm tra tính toán lại độc lập trên 500 ô giá trị ngẫu nhiên, đạt độ khớp tuyệt đối 100%. Tỷ lệ sai lệch EPS tự tính toán so với EPS CafeF công bố dưới 10% đạt trên 92%.
* Cơ sở dữ liệu `indicators.sqlite` đã được đóng gói và xác thực hash bất biến tại [configs/product/indicators_v1.json](configs/product/indicators_v1.json).

### 3.2. Kết quả thu thập ngày công bố BCTC phục vụ Point-In-Time
* Hoàn thành 100% trên toàn bộ **1.362 / 1.362 mã cổ phiếu** (13.620 bản ghi mã-năm).
* Phân phối độ trễ công bố (2022–2025): Trung vị 91 ngày, phân vị 95% là 169 ngày, phân vị 99% là 374 ngày.
* Đối chiếu thực tế với văn bản công bố gốc của UBCKNN/Sở GDCK trên 9 mã-năm: **100% các trường hợp đều không sớm hơn ngày công bố thực tế**, bảo đảm không rò rỉ dữ liệu trước khi thị trường biết.

### 3.3. Bảng kết quả đối sánh toàn diện 4 thuật toán trên Dữ liệu Tài chính (Hệ B)
Kết quả thực nghiệm quét sweep trên 9 năm tài chính (2017–2025) tại [configs/experiments/clustering_rework_v2.json](configs/experiments/clustering_rework_v2.json) và script [scripts/run_clustering_rework_v2.py](scripts/run_clustering_rework_v2.py):

| Thuật toán | Cấu hình k khảo sát | Độ ổn định mẫu con 90% (ARI) | Median Silhouette Score | Median Davies–Bouldin | Cân bằng tỷ lệ cụm (>= 5% số mã) | Trạng thái Cổng lọc (Admissible) | Đánh giá & Phân loại |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **K-Means Baseline** (deterministic) | **k = 3** | **~0,50**<br>(Trượt ngưỡng >= 0.80) | ~0,18 – 0,22 | ~1,65 – 1,80 | **Đạt**<br>(Không có cụm rỗng) | **KHÔNG ĐẠT (None Admissible)** | **Chọn làm Baseline mô tả (B v4)**: Đạt độ ổn định cao nhất trong 4 thuật toán; cụm phân bố tương đối đều, có ý nghĩa phân loại cơ bản. |
| **PCA + K-Means** (giữ 80% phương sai) | k = 3 | ~0,48<br>(Trượt ngưỡng >= 0.80) | ~0,19 – 0,21 | ~1,68 – 1,82 | **Đạt** | **KHÔNG ĐẠT (None Admissible)** | Giảm chiều PCA không giúp tăng độ ổn định do phương sai tài chính phân tán đều giữa các nhóm sinh lời, thanh toán và đòn bẩy. |
| **Ward Hierarchical** (liên kết ngưng tụ) | k = 3..8 | **< 0,40**<br>(Rất thấp) | ~0,15 – 0,18 | ~1,85 – 2,10 | **Trượt**<br>(Hay có cụm < 5%) | **KHÔNG ĐẠT (None Admissible)** | Rất nhạy cảm với các tỷ số tài chính cực đoan (âm vốn, nợ cao); cây phân cấp bị lệch nặng và tính ổn định kém. |
| **Gaussian Mixture Models (GMM)** | k = 3..8 | **< 0,35**<br>(Kém nhất) | ~0,12 – 0,16 | ~2,10 – 2,40 | Không ổn định | **KHÔNG ĐẠT (None Admissible)** | Không hội tụ ổn định; ma trận hiệp phương sai 9 chiều dễ gặp hiện tượng suy biến hoặc đa cộng tuyến kế toán giữa các chỉ số biên lợi nhuận. |

* **Kết luận khoa học chính thức:** **Không có cấu hình nào đạt ngưỡng chấp nhận (None admissible)** ở cả 2 bộ chỉ số (`B_base` và `B_value`), trên cả toàn kỳ (2017–2025) lẫn khi chỉ sàng lọc giai đoạn Development (<= 2023).

### 3.4. Phân tích bản chất kinh tế học của dữ liệu tài chính Việt Nam
1. **Độ phân tán liên ngành tự nhiên:** Các doanh nghiệp thuộc các ngành khác nhau (sản xuất công nghiệp, bất động sản, bán lẻ, công nghệ) có mô hình kinh doanh hoàn toàn khác biệt. Tỷ số nợ, vòng quay tài sản hay biên lợi nhuận phân bố rất rộng và không tạo thành các cụm hình cầu tự nhiên.
2. **Cú sốc kinh tế vĩ mô qua các năm:** Giai đoạn 2017–2025 chứng kiến nhiều biến cố lớn (COVID-19 2020–2021, đóng băng trái phiếu doanh nghiệp và bất động sản 2022–2023, biến động lãi suất). Cấu trúc tài chính của cùng một doanh nghiệp có thể thay đổi đột ngột giữa 2 năm tài chính kế tiếp.
3. **Tính trung thực khoa học của DELTA:** Dự án kiên quyết tuân thủ nguyên tắc không "nắn chỉnh dữ liệu" (không forward-fill, không điền số 0 giả tạo, không cherry-pick mã tốt). Kết quả ARI ~ 0,50 phản ánh đúng bản chất biến động thực tế của nền kinh tế Việt Nam.

### 3.5. Quyết định kiến trúc của DELTA và Bàn giao sang Milestone M3
Dựa trên kết quả thực nghiệm và Quyết định D-DIR-01:
1. **Mô hình tài chính phục vụ thực tế (Model B trong Bundle v4):**
   * Lựa chọn **K-Means Baseline (k = 3, bộ đặc trưng B_base)** làm mô hình phân nhóm tài chính mô tả cơ sở (Descriptive Baseline).
   * Gắn nhãn minh bạch trên giao diện web và tài liệu: *"Mô hình tài chính cơ sở mang tính mô tả, độ ổn định lấy mẫu con đạt ARI 0,50 (chưa đạt ngưỡng tối ưu 0,80)"*.
2. **Chốt chặn chất lượng độc lập tại Milestone M3:**
   * Không dựa duy nhất vào nhãn cụm B để ra quyết định đầu tư.
   * Milestone M3 tích hợp bổ sung hệ thống chỉ số chuẩn hóa D-IND-01 làm bộ lọc chất lượng: yêu cầu cổ phiếu đạt điểm sức khỏe tài chính Piotroski F-Score >= 7 và Altman Z-Score >= 1.81.
3. **Cơ chế xác định Cụm dẫn dắt tài chính (Financial Leading Cluster):**
   * Được chọn cơ học theo từng snapshot: Chọn cụm có **trung vị ROE cao nhất**; nếu hòa điểm chọn cụm có **trung vị Nợ/VCSH thấp hơn**.
4. **Kết hợp danh mục đa tài sản:** Candidate Universe là phần giao giữa Cụm dẫn dắt thị trường (Hệ A) và Cụm dẫn dắt tài chính (Hệ B) sau khi kiểm tra tính sẵn sàng `usable_from_date <= decision_date`.

---

## 4. TÓM TẮT TRỌNG TÂM ĐƯA VÀO SLIDE THUYẾT TRÌNH (SLIDE-READY HIGHLIGHTS)

Dưới đây là phần tóm tắt cô đọng, đóng gói các bảng biểu và thông điệp chính về hệ dữ liệu tài chính để đưa vào slide thuyết trình:

### Slide 1: Bảng đối sánh 4 thuật toán trên Dữ liệu Tài chính (Hệ B)

| Thuật toán | Cấu hình k | Ổn định mẫu con (ARI) | Silhouette Score | Davies–Bouldin | Cân bằng cụm | Kết luận nghiệm thu |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **K-Means Baseline** | **k = 3** | **~0,50** | ~0,18 – 0,22 | ~1,65 – 1,80 | Tốt (>= 5%) | **CHỌN LÀM BASELINE MÔ TẢ (B v4)** kèm cảnh báo |
| **PCA + K-Means** | k = 3 | ~0,48 | ~0,19 – 0,21 | ~1,68 – 1,82 | Tốt (>= 5%) | Trượt cổng ổn định; PCA không cải thiện được độ phân tán |
| **Ward Hierarchical** | k = 3..8 | < 0,40 | ~0,15 – 0,18 | ~1,85 – 2,10 | Kém (< 5%) | Trượt cổng; nhạy cảm với ngoại lai và lệch cỡ cụm |
| **GMM (Gaussian)** | k = 3..8 | < 0,35 | ~0,12 – 0,16 | ~2,10 – 2,40 | Kém | Trượt cổng; không hội tụ ổn định trên 9 chiều kế toán |

* **Kết luận chung:** **Không có thuật toán nào đạt ngưỡng nghiên cứu chuẩn (ARI >= 0.80)**. K-Means k=3 đạt kết quả tốt nhất trong 4 phương án (~0,50).

### Slide 2: Bản chất kinh tế học — Tại sao BCTC không đạt ARI >= 0.80?

1. **Độ phân tán liên ngành tự nhiên:** Các doanh nghiệp thuộc các ngành khác nhau (sản xuất công nghiệp, bất động sản, bán lẻ, công nghệ) có mô hình kinh doanh hoàn toàn khác biệt. Tỷ số nợ, vòng quay tài sản hay biên lợi nhuận phân bố rất rộng và không tạo thành các cụm hình cầu tự nhiên.
2. **Cú sốc kinh tế vĩ mô qua các năm:** Giai đoạn 2017–2025 chứng kiến nhiều biến cố lớn (COVID-19 2020–2021, biến động trái phiếu doanh nghiệp và bất động sản 2022–2023, biến động lãi suất). Cấu trúc tài chính của cùng một doanh nghiệp có thể thay đổi đột ngột giữa 2 năm tài chính kế tiếp.
3. **Tính trung thực khoa học của DELTA:** Dự án kiên quyết tuân thủ nguyên tắc không "nắn chỉnh dữ liệu" (không forward-fill, không điền số 0 giả tạo, không cherry-pick mã tốt). Kết quả ARI ~ 0,50 phản ánh đúng bản chất biến động thực tế của nền kinh tế Việt Nam.

### Slide 3: Giải pháp kiến trúc của DELTA và Ứng dụng thực tiễn cho M3

1. **Phân tách ranh giới rõ ràng:**
   * Mô hình phân cụm tài chính Hệ B (K-Means k=3) chỉ đóng vai trò **phân cụm mô tả sơ bộ (Descriptive Clustering)**.
   * Hệ thống hiển thị minh bạch cảnh báo độ ổn định ARI = 0,50 trên giao diện web và tài liệu kỹ thuật.
2. **Chốt chặn an toàn với Lớp chỉ số sản phẩm (Indicators v1):**
   * Không dựa duy nhất vào nhãn cụm tài chính để ra quyết định đầu tư.
   * Xây dựng độc lập hệ thống chỉ số chuẩn hóa thị trường (D-IND-01) với 15 chỉ số cốt lõi và 3 hệ thống điểm chuyên sâu:
     * **Piotroski F-score:** Sàng lọc chất lượng và đà cải thiện hoạt động (thang điểm 0–9).
     * **Altman Z-score:** Ngăn ngừa rủi ro kiệt quệ tài chính và phá sản.
     * **Beneish M-score:** Cảnh báo gian lận và bóp méo số liệu kế toán.
3. **Chiến lược đầu tư tích hợp tại Milestone M3:**
   * Candidate Universe = Cụm dẫn dắt thị trường (Hệ A) giao với Cụm dẫn dắt tài chính (Hệ B) sau khi kiểm tra tính khả dụng PIT (`usable_from_date <= decision_date`).
   * Xếp hạng cuối cùng kết hợp điểm kỹ thuật và điểm cơ bản vững chắc (ROE + F-score + Z-score) để chọn top 30% cổ phiếu tốt nhất thị trường.

---

## 5. BẢN ĐỒ MÃ NGUỒN VÀ ARTIFACT TÁI LẬP (REPRODUCIBILITY MAP)

Toàn bộ hệ thống dữ liệu tài chính của DELTA đã được hoàn thiện khép kín và có thể tái lập hoàn toàn từ mã nguồn:

| Thành phần | Đường dẫn mã nguồn / Cấu hình | Trách nhiệm |
|---|---|---|
| **Engine tính chỉ số** | [src/delta_t1/indicators/compute.py](src/delta_t1/indicators/compute.py) | Tính toán 15 chỉ số cơ bản và 3 bộ điểm F/M/Z |
| **Pipeline nạp chỉ số** | [scripts/build_indicators.py](scripts/build_indicators.py) | Tạo cơ sở dữ liệu `indicators.sqlite` |
| **Kiểm định QA** | [scripts/verify_indicators.py](scripts/verify_indicators.py) | Kiểm tra tính toán lại độc lập và đối chiếu EPS |
| **Crawl ngày công bố** | [scripts/crawl_cafef_disclosure_dates.py](scripts/crawl_cafef_disclosure_dates.py) | Thu thập ngày gửi BCTC từ CafeF cho 1.362 mã |
| **Tính khả dụng PIT** | [scripts/build_financial_availability.py](scripts/build_financial_availability.py) | Tạo bảng `usable_from_date` phục vụ backtest M3 |
| **Huấn luyện phân cụm** | [scripts/run_clustering_rework_v2.py](scripts/run_clustering_rework_v2.py) | Chạy đối sánh 4 thuật toán (KMeans, PCA, Ward, GMM) |
| **Lõi phân cụm tài chính**| [src/delta_t1/experiments/clustering_rework_v2.py](src/delta_t1/experiments/clustering_rework_v2.py) | Xử lý ma trận `financial_snapshots` và hàm fit |
| **Cấu hình thực nghiệm** | [configs/experiments/clustering_rework_v2.json](configs/experiments/clustering_rework_v2.json) | Cấu hình tham số thực nghiệm phân cụm tài chính |
| **Cấu hình sản phẩm** | [configs/product/indicators_v1.json](configs/product/indicators_v1.json) | Khóa hash và liên kết file `indicators.sqlite` |

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence.*
