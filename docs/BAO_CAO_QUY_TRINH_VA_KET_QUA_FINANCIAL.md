# BÁO CÁO TOÀN DIỆN QUY TRÌNH XÂY DỰNG, CHUẨN HÓA VÀ PHÂN CỤM DỮ LIỆU TÀI CHÍNH (HỆ B)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** 26/10/2026 (theo Quyết định D-IND-01, D-CRAWL-02 và D-DIR-01)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và các artifact đã thực thi trong repository.

---

## 1. TỔNG QUAN, MỤC TIÊU VÀ NGUYÊN TẮC BẤT BIẾN

### 1.1. Mục tiêu của Hệ Dữ liệu Tài chính (Hệ B)
Hệ dữ liệu tài chính trong dự án DELTA đảm nhận hai vai trò chiến lược:
1. **Lớp phân cụm mô tả (Descriptive Clustering - Hệ B):** Phân nhóm các doanh nghiệp phi tài chính theo các tỷ số tài chính cốt lõi nhằm xác định các cụm doanh nghiệp có chất lượng cơ bản lành mạnh, khả năng sinh lời cao và đòn bẩy an toàn.
2. **Lớp chỉ số sản phẩm và bộ lọc chất lượng (Indicators & Quality Overlay):** Cung cấp hệ thống 15 chỉ số tài chính chuẩn hóa (P/E, P/B, ROE, ROA...) và 3 hệ thống điểm sức khỏe tài chính chuyên sâu (Piotroski F-score, Beneish M-score, Altman Z-score) để sàng lọc và xếp hạng cổ phiếu trong bài toán xây dựng danh mục đầu tư tại Milestone M3.

### 1.2. Các nguyên tắc nghiên cứu bất biến (Research Invariants)
Theo quy định tại AGENTS.md và docs/DATA_CONTRACT.md:
1. **Nguyên tắc Point-In-Time (PIT):** Tại ngày ra quyết định `decision_date` t, chỉ được sử dụng các báo cáo tài chính đã thực sự công bố và sẵn sàng trên thị trường (`usable_from_date <= t`). Tuyệt đối không lấy ngày kết thúc kỳ kế toán (`period_end`) làm ngày ra quyết định.
2. **Không làm đẹp dữ liệu (No Imputation/No Distortion):** Dữ liệu tài chính thiếu bắt buộc phải để `null`, tuyệt đối không điền 0, không forward-fill giữa các năm tài chính, không xóa bỏ các giá trị cực đoan một cách tùy tiện.
3. **Phân định rõ ranh giới ngành:** Các định chế tài chính (Ngân hàng, Công ty Chứng khoán, Công ty Bảo hiểm) có cấu trúc BCTC đặc thù, không áp dụng công thức của doanh nghiệp thông thường và không đưa vào mô hình phân cụm của doanh nghiệp phi tài chính.

---

## 2. QUÁ TRÌNH THU THẬP VÀ XỬ LÝ DỮ LIỆU BCTC NỀN TẢNG (GIAI ĐOẠN 1)

Chi tiết quá trình khảo sát và thu thập được ghi nhận tại artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md.

### 2.1. Khảo sát nguồn dữ liệu và Thử nghiệm Pilot
* **Nguồn dữ liệu:** Khảo sát toàn diện hệ thống báo cáo CafeF (tóm tắt, chi tiết, web service, tài liệu công bố thông tin, bản quét PDF), DStock (VNDirect), VietFin, TCBS và SSI.
* **Thử nghiệm Pilot 5 mã (BRC, FPT, MWG, GMD, VNM):** Đối chiếu chi tiết 100% số liệu API với báo cáo tài chính kiểm toán gốc định dạng PDF.
  * Đạt 29/30 bộ chỉ số đối chứng chính xác (BRC, FPT, MWG, GMD đạt 6/6; VNM đạt 5/6 do thiếu phân tách nợ gốc ngắn hạn trong nguồn API).
  * Phát hiện các lỗi sai số phổ biến từ nhà cung cấp dữ liệu: gán sai dòng chỉ tiêu, nhầm lẫn chi phí tài chính với chi phí lãi vay, gộp nợ thuê tài chính vào nợ vay dài hạn, hoặc đặt giá trị `-1` cho các dòng thực chất là vắng mặt.
* **Mở rộng mẫu kiểm định:** Triển khai qua Mẫu 20 mã, Mẫu 50 mã và mở rộng lên toàn bộ danh mục 1.522 mã cổ phiếu ứng viên (Securities Registry).

### 2.2. Kết quả thu thập dữ liệu 10 năm liên tục (2016–2025)
* Hệ thống đạt mốc **1.172 mã cổ phiếu có đầy đủ báo cáo tài chính cả 10 năm liên tục (2016–2025)**, tạo thành tập mẫu 11.720 dòng quan sát (Execution 50/56).
* Tổng số dòng dữ liệu BCTC thu thập đạt **13.529 dòng quan sát năm** trên 1.428 mã cổ phiếu.

---

## 3. MÔ HÌNH PHÂN CỤM TÀI CHÍNH CƠ SỞ ĐỢT 1 (FINANCIAL FULL10 BASELINE)

Chi tiết thực thi lưu tại src/delta_t1/experiments/financial_full10_baseline.py và báo cáo tại docs/FINANCIAL_SESSION_HANDOFF.md.

### 3.1. Thiết kế thực nghiệm
* **Tập dữ liệu:** 1.172 mã cổ phiếu doanh nghiệp phi tài chính x 10 năm tài chính (2016–2025) = 11.720 dòng quan sát.
* **6 tỷ số tài chính cốt lõi (Core Ratios):**
  1. `gross_margin`: Biên lợi nhuận gộp (Lợi nhuận gộp / Doanh thu thuần).
  2. `net_margin`: Biên lợi nhuận ròng (LNST / Doanh thu thuần).
  3. `liabilities_to_assets`: Tỷ lệ Nợ trên Tổng tài sản.
  4. `current_ratio`: Chỉ số thanh toán hiện hành (Tài sản ngắn hạn / Nợ ngắn hạn).
  5. `operating_cashflow_to_assets`: Dòng tiền kinh doanh trên Tổng tài sản (CFO / Tổng tài sản).
  6. `asset_turnover_ending_assets`: Vòng quay tài sản (Doanh thu thuần / Tổng tài sản cuối kỳ).
* **Quy trình:** Chuẩn hóa z-score độc lập từng năm tài chính; fit 10 mô hình K-Means tĩnh độc lập tương ứng với 10 năm với k = 3, seed = 42, n_init = 10, max_iter = 300.

### 3.2. Đánh giá chất lượng và Giới hạn phương pháp luận
* **Kết quả kỹ thuật:** Toàn bộ 10 mô hình đều hội tụ thành công, hoàn thành 70.320 phép tính tỷ số.
* **Khiếm khuyết phát hiện:**
  1. **Tồn tại cụm thiểu số (< 10 mã):** Cả 10 năm tài chính đều xuất hiện cụm nhỏ do các doanh nghiệp có tỷ số tài chính cực đoan (âm vốn chủ sở hữu nặng, nợ vượt xa tài sản như trường hợp QBS, CAD, VTI).
  2. **Độ ổn định thấp:** Độ ổn định khi lấy mẫu con (subsample stability) chỉ đạt ARI xấp xỉ `0.50`, không đạt ngưỡng tin cậy thống kê (yêu cầu tối thiểu >= 0.80).
  3. **Chưa có ngày công bố:** Toàn bộ 11.720 dòng quan sát tại đợt 1 chưa gắn kèm ngày công bố BCTC (`published_at`), do đó mô hình chỉ mang tính chất tham chiếu mô tả ngoại suy (EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT), chưa đủ điều kiện đưa vào backtest M3.

---

## 4. CHUẨN HÓA LỚP CHỈ SỐ SẢN PHẨM INDICATORS V1 (QUYẾT ĐỊNH D-IND-01)

Ngày 24/10/2026, Project Owner đã phê duyệt **Quyết định D-IND-01** (kế hoạch tại docs/INDICATORS_PRODUCT_PLAN.md và ghi nhận tại docs/DECISIONS.md) nhằm xây dựng engine tính toán chỉ số tài chính chuẩn hóa phục vụ trực quan hóa web và làm bộ lọc chất lượng cho M3.

### 4.1. Quy tắc tính toán chuẩn thị trường Việt Nam
1. **Số cổ phiếu lưu hành:** `shares = Vốn góp cổ phiếu phổ thông / 10.000 đ` (mệnh giá 10.000 đ/CP theo luật định). Fallback: `paid_in_capital_amount / 10.000`.
2. **Lợi nhuận trước lãi vay và thuế (EBIT):** `ebit = Lợi nhuận trước thuế + Chi phí lãi vay`.
3. **Giá thị trường tính P/E, P/B:** Sử dụng giá đóng cửa thực tế (`raw_close`) của phiên giao dịch cuối cùng <= 31/12 của năm tài chính đó (phiên giao dịch không cách quá 30 ngày).
4. **Phân định nhóm ngành:**
   * Doanh nghiệp thông thường (Regular): Tính toán toàn bộ 15 chỉ số và 3 hệ thống điểm F/M/Z.
   * Ngân hàng / Chứng khoán / Bảo hiểm: Tính toán các chỉ số cơ bản (EPS, BVPS, P/E, P/B, ROE, ROA, Vốn hóa); các điểm F-score, M-score, Z-score trả về trạng thái `NOT_APPLICABLE`.

### 4.2. Hệ thống 15 chỉ số tài chính cơ bản
Được cài đặt thuần túy tại module src/delta_t1/indicators/compute.py và tạo ra cơ sở dữ liệu `indicators.sqlite`:
* **Nhóm định giá:** EPS, BVPS, Vốn hóa thị trường, P/E (khi EPS <= 0 trả về null + `NEGATIVE_EARNINGS`), P/B (khi BVPS <= 0 trả về null + `NEGATIVE_EQUITY`).
* **Nhóm sinh lời:** ROE (LNST công ty mẹ / VCSH mẹ bình quân), ROA (Tổng LNST / Tổng tài sản bình quân), Biên lãi gộp, Biên lãi ròng.
* **Nhóm tăng trưởng:** Tăng trưởng doanh thu thuần, Tăng trưởng lợi nhuận mẹ (so với cùng kỳ năm trước).
* **Nhóm an toàn tài chính:** Nợ / VCSH, Thanh toán hiện hành, Vòng quay tài sản, Tỷ lệ Dòng tiền kinh doanh trên Lợi nhuận thuần (CFO / LNST).

### 4.3. Ba hệ thống điểm chất lượng tài chính chuyên sâu

#### 1. Piotroski F-Score (Thang điểm 0 đến 9)
Đánh giá sức khỏe tài chính toàn diện qua 9 tín hiệu nhị phân (1 đạt, 0 không đạt):
* *Sinh lời (4 điểm):* (1) ROA > 0; (2) CFO > 0; (3) ROA năm nay > ROA năm trước; (4) CFO / Tổng tài sản > ROA (chất lượng lợi nhuận).
* *Đòn bẩy & Thanh khoản (3 điểm):* (5) Nợ dài hạn / Tổng tài sản giảm; (6) Thanh toán hiện hành tăng; (7) Số lượng cổ phiếu không tăng (không phát hành pha loãng).
* *Hiệu quả hoạt động (2 điểm):* (8) Biên lãi gộp tăng; (9) Vòng quay tài sản tăng.
* *Xếp loại:* 7–9 điểm: Rất mạnh; 4–6 điểm: Trung bình; 0–3 điểm: Yếu.

#### 2. Beneish M-Score (Đánh giá rủi ro thao túng BCTC)
Mô hình 8 biến số phát hiện bất thường kế toán:
* Công thức:  
  `M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI`
* Trong đó: DSRI (Chỉ số thu tiền khách hàng), GMI (Chỉ số suy giảm biên gộp), AQI (Chỉ số chất lượng tài sản), SGI (Tăng trưởng doanh thu), DEPI (Tỷ lệ khấu hao), SGAI (Chi phí bán hàng & QLDN), TATA (Tổng biến dồn tích trên tổng tài sản), LVGI (Chỉ số đòn bẩy).
* *Ngưỡng đánh giá:* M > -1.78 cảnh báo có rủi ro cao về việc bóp méo số liệu kế toán.

#### 3. Altman Z-Score (Dự báo nguy cơ kiệt quệ tài chính)
* Công thức cho doanh nghiệp sản xuất/thông thường:  
  `Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5`  
  Với X1 = Vốn lưu động / Tổng tài sản; X2 = Lợi nhuận giữ lại / Tổng tài sản; X3 = EBIT / Tổng tài sản; X4 = Vốn hóa thị trường / Tổng nợ phải trả; X5 = Doanh thu / Tổng tài sản.
* *Vùng đánh giá:* Z > 2.99: An toàn; 1.81 <= Z <= 2.99: Vùng cảnh báo; Z < 1.81: Vùng nguy hiểm.

### 4.4. Kiểm định chất lượng độc lập (QA Verification)
* File thực thi: `scripts/verify_indicators.py`
* Độc lập tính toán lại ngẫu nhiên trên 500 ô giá trị, đạt độ khớp tuyệt đối 100%.
* Đối chiếu EPS tự tính toán với EPS nguồn công bố của CafeF: tỷ lệ sai lệch dưới 10% đạt trên 92% (các trường hợp lệch chủ yếu do cổ phiếu quỹ hoặc điều chỉnh chia tách cổ phiếu).
* Độ phủ (Coverage) thực tế năm tài chính 2024–2025: đạt trên **88% – 90%** số mã có dữ liệu BCTC hoàn chỉnh.

---

## 5. THU THẬP NGÀY CÔNG BỐ BCTC PHỤC VỤ POINT-IN-TIME (D-CRAWL-02)

Để phục vụ Milestone M3 loại bỏ hoàn toàn hiện tượng rò rỉ thông tin tương lai (Look-ahead bias), ngày 25/10/2026, chiến dịch thu thập ngày công bố BCTC đã được triển khai theo quy định D-CRAWL-02.

### 5.1. Quy trình và Công nghệ thu thập
* **Mã nguồn:** `scripts/crawl_cafef_disclosure_dates.py` và `scripts/build_financial_availability.py`.
* **Cơ chế thu thập:** Khai thác API Công bố thông tin CafeF (`ajaxcongbothongtin.ashx`), trích xuất trường thời gian gửi tài liệu (`CreateDate`) của các báo cáo tài chính năm đã kiểm toán (ưu tiên BCTC hợp nhất kiểm toán HK, sau đó đến kiểm toán riêng lẻ K/MK).
* **Kết quả:** Thu thập thành công **1.362 / 1.362 mã cổ phiếu** (100% hoàn tất, không phát sinh lỗi chặn truy cập), tạo lập bảng cơ sở dữ liệu `availability.csv` với **13.620 bản ghi mã - năm tài chính** (2016–2025).

### 5.2. Nguyên tắc xác định ngày sử dụng thông tin (usable_from_date)
Bảng ánh xạ tính sẵn sàng của dữ liệu tài chính được chuẩn hóa theo 2 cơ chế:
1. **Năm tài chính từ 2022 trở đi (`CAFEF_DISCLOSURE`):**  
   Sử dụng ngày gửi sớm nhất từ API CafeF. Ngày bắt đầu được phép sử dụng thông tin (`usable_from_date`) là phiên giao dịch đầu tiên **sau** ngày gửi tài liệu.
2. **Năm tài chính trước 2022 (`LAG_RULE`):**  
   Do CafeF nhập lại dữ liệu lịch sử vào ngày 26/11/2022 nên toàn bộ bản ghi cũ mang ngày này. Để đảm bảo tính bảo thủ và không rò rỉ thông tin, hệ thống áp dụng quy tắc trễ: `usable_from_date` là phiên giao dịch đầu tiên sau ngày **30/06 của năm tiếp theo** (t+1).

### 5.3. Thống kê và Đối chiếu kiểm chứng thực tế
* **Phân phối độ trễ công bố (2022–2025):** Độ trễ từ 31/12 đến ngày gửi có trung vị là **91 ngày**, phân vị 95% là **169 ngày**, phân vị 99% là **374 ngày**.
* **Kiểm tra đối chiếu thủ công (Spot-check):** Đối chiếu 9 mã-năm đã kiểm tra tài liệu công bố gốc của UBCKNN/Sở GDCK (FPT 2022–2025, PVS 2024–2025, ACV 2025, BRC 2024–2025):
  * Ngày ghi nhận trên CafeF lệch từ 0 đến +62 ngày so với ngày công bố thực tế.
  * **100% các trường hợp đều không sớm hơn thực tế**, bảo đảm dữ liệu hoàn toàn an toàn về mặt Point-In-Time (không bao giờ dùng thông tin trước khi thị trường biết).

---

## 6. THỰC NGHIỆM PHÂN CỤM TÀI CHÍNH ĐỐI SÁNH (CLUSTERING REWORK V2)

Ngày 25/10/2026, toàn bộ 4 thuật toán phân cụm đã được quét đối sánh trên hệ dữ liệu tài chính tại [scripts/run_clustering_rework_v2.py](scripts/run_clustering_rework_v2.py) và [src/delta_t1/experiments/clustering_rework_v2.py](src/delta_t1/experiments/clustering_rework_v2.py).

### 6.1. Thiết kế thực nghiệm Đợt 2
* **Tập đặc trưng khảo sát:**
  * `B_base` (9 chỉ số): ROE, ROA, biên gộp, biên ròng, Nợ/VCSH, thanh toán hiện hành, vòng quay tài sản, tăng trưởng doanh thu, CFO/LNST.
  * `B_value` (12 chỉ số): Bộ 9 chỉ số trên kết hợp thêm E/P (Earnings Yield), B/P (Book-to-Price) và log vốn hóa thị trường.
* **Không gian tiền xử lý T1:** Lấy log các biến quy mô, cắt đuôi ngoại lai (winsorize 1%–99%), chuẩn hóa z-score theo từng năm.
* **Không gian thuật toán:** Quét đồng thời cả 4 thuật toán:
  1. K-Means (n_init = 10, seed = 42).
  2. PCA + K-Means (giữ 80% phương sai + K-Means).
  3. Ward Hierarchical (linkage = 'ward').
  4. Gaussian Mixture Models (GMM, full covariance, n_init = 2).
* **Không gian số cụm k:** Khảo sát k từ 3 đến 8 trên các năm tài chính từ 2017 đến 2025.

### 6.2. Kết quả nghiệm thu thực nghiệm
Kết quả sweep được ghi nhận tại [configs/experiments/clustering_rework_v2.json](configs/experiments/clustering_rework_v2.json) và [artifacts/reports/m2-vs-rework-v1/report.md](artifacts/reports/m2-vs-rework-v1/report.md):

* **Kết luận chính thức:** **Không có cấu hình nào đạt ngưỡng chấp nhận (None admissible)** ở cả 2 bộ chỉ số (`B_base` và `B_value`), trên cả toàn kỳ (2017–2025) lẫn khi chỉ sàng lọc giai đoạn Development (<= 2023).
* **Nguyên nhân cốt lõi:**
  * Quy chuẩn nghiên cứu yêu cầu độ ổn định lấy mẫu con (subsample stability với 90% mẫu qua các random seed) phải đạt trung vị ARI >= `0.80`.
  * Thực tế trên dữ liệu tài chính doanh nghiệp Việt Nam, tất cả 4 thuật toán và các mức k từ 3 đến 8 chỉ đạt độ ổn định trung vị **ARI xấp xỉ 0.50**.
  * Các chỉ số tài chính có độ phân tán cực kỳ lớn giữa các ngành nghề, đồng thời các cú sốc vĩ mô (chu kỳ kinh tế, dịch bệnh, biến động lãi suất) làm cấu trúc phân bố tài chính thay đổi mạnh qua từng năm.
  * Thuật toán Ward và GMM trên dữ liệu tài chính thậm chí có độ ổn định và chỉ số cân bằng cụm kém hơn K-Means.

### 6.3. Mô hình phục vụ thực tế (Model B trong Bundle v4)
Mặc dù không đạt tiêu chuẩn nghiên cứu khắt khe để tuyên bố một mô hình phân cụm ổn định dài hạn, hệ thống vẫn cần một mô hình phân nhóm tài chính cơ sở phục vụ hiển thị trực quan hóa trên giao diện web và tạo bộ lọc sơ bộ cho Milestone M3:
* **Thuật toán được chọn:** **K-Means**
* **Số cụm k:** **k = 3**
* **Tập đặc trưng:** 9 chỉ số chuẩn `B_base` (chuẩn hóa T1).
* **Gắn nhãn minh bạch:** Ghi chú rõ trên giao diện và tài liệu: *"Mô hình tài chính cơ sở mang tính mô tả, độ ổn định lấy mẫu con đạt ARI 0,50 (chưa đạt ngưỡng tối ưu 0,80)"*.

---

## 7. ỨNG DỤNG HỆ TÀI CHÍNH VÀO BACKTEST VÀ DANH MỤC (MILESTONE M3)

Theo Kế hoạch M3 tại docs/M3_PLAN.md, hệ tài chính được tích hợp vào quy trình đầu tư một cách độc lập:

1. **Xác định Cụm dẫn dắt tài chính (Financial Leading Cluster):**
   * Được chọn cơ học theo từng snapshot dựa vào hồ sơ trung vị (profile), không chọn theo số nhãn: Chọn cụm có **trung vị ROE cao nhất**; nếu hòa điểm chọn cụm có **trung vị Nợ/VCSH thấp hơn**.
2. **Bộ tiêu chí xếp hạng tài chính (FC1 – FC3):**
   * `FC1`: ROE (Khả năng sinh lời trên vốn chủ sở hữu).
   * `FC2`: Piotroski F-Score (Sức khỏe và cải thiện tài chính từ 0 đến 9 điểm).
   * `FC3`: Altman Z-Score (Mức độ an toàn tài chính và phòng tránh rủi ro phá sản).
3. **Nguyên tắc kết hợp với Hệ thị trường (Combined Universe):**
   * Tập ứng viên hợp lệ (Candidate Universe) là phần giao giữa **Cụm dẫn dắt thị trường (Hệ A)** và **Cụm dẫn dắt tài chính (Hệ B)** đã thỏa mãn kiểm tra ngày công bố (`usable_from_date <= decision_date`).
   * Điểm tổng hợp cuối cùng: `S = 0.5 * S_market + 0.5 * S_financial`.
   * Chiến lược chọn top 30% cổ phiếu có điểm cao nhất để phân bổ danh mục đầu tư đều tỷ trọng.

---

## 8. TỔNG KẾT VÀ BẢN ĐỒ MÃ NGUỒN LIÊN QUAN

Toàn bộ hệ thống dữ liệu tài chính của DELTA đã được hoàn thiện khép kín và có thể tái lập hoàn toàn từ mã nguồn:

| Thành phần | Đường dẫn mã nguồn / Cấu hình | Trách nhiệm |
|---|---|---|
| **Engine tính chỉ số** | `src/delta_t1/indicators/compute.py` | Tính toán 15 chỉ số cơ bản và 3 bộ điểm F/M/Z |
| **Pipeline nạp chỉ số** | `scripts/build_indicators.py` | Tạo cơ sở dữ liệu `indicators.sqlite` |
| **Kiểm định QA** | `scripts/verify_indicators.py` | Kiểm tra tính toán lại độc lập và đối chiếu EPS |
| **Crawl ngày công bố** | `scripts/crawl_cafef_disclosure_dates.py` | Thu thập ngày gửi BCTC từ CafeF cho 1.362 mã |
| **Tính khả dụng PIT** | `scripts/build_financial_availability.py` | Tạo bảng `usable_from_date` phục vụ backtest M3 |
| **Huấn luyện phân cụm** | `scripts/run_clustering_rework_v2.py` | Chạy đối sánh 4 thuật toán (KMeans, PCA, Ward, GMM) |
| **Lõi phân cụm tài chính**| `src/delta_t1/experiments/clustering_rework_v2.py` | Xử lý ma trận `financial_snapshots` và hàm fit |
| **Cấu hình thực nghiệm** | `configs/experiments/clustering_rework_v2.json` | Cấu hình tham số thực nghiệm phân cụm tài chính |
| **Cấu hình sản phẩm** | `configs/product/indicators_v1.json` | Khóa hash và liên kết file `indicators.sqlite` |

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence.*
