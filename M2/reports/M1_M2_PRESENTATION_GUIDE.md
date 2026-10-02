# TÀI LIỆU QUY CHUẨN VÀ PHƯƠNG PHÁP LUẬN BÁO CÁO TUẦN: MILESTONE M1 VÀ M2-PREP

> **Dự án:** DELTA - Nghiên cứu Phân cụm Động lượng Điều chỉnh Rủi ro trên Thị trường Chứng khoán Việt Nam  
> **Trọng tâm tài liệu:** Quy chuẩn kỹ thuật Milestone M1 (C8 Market Foundation) và Khung Thực nghiệm Phân cụm M2-PREP  
> **Phiên bản:** Cập nhật ngày 30/09/2026 (Bổ sung Quá trình thực hiện chi tiết cho từng Slide thuyết trình)

---

## MỤC LỤC
1. [Thông điệp cốt lõi và Ranh giới an toàn](#1-thông-điệp-cốt-lõi-và-ranh-giới-an-toàn)
2. [Đánh giá và Khuyến nghị tinh gọn Slide (Trang 31 - 42)](#2-đánh-giá-và-khuyến-nghị-tinh-gọn-slide-trang-31---42)
3. [Cấu trúc nội dung 2 Nhiệm vụ trọng tâm (Chuẩn 4 Trụ cột)](#3-cấu-trúc-nội-dung-2-nhiệm-vụ-trọng-tâm-chuẩn-4-trụ-cột)
   - [Nhiệm vụ 1: Hoàn tất Nền tảng Dữ liệu Thị trường (Milestone M1 - C8)](#nhiệm-vụ-1-hoàn-tất-nền-tảng-dữ-liệu-thị-trường-milestone-m1---c8)
   - [Nhiệm vụ 2: Thiết lập Khung Thực nghiệm Phân cụm (Milestone M2-PREP)](#nhiệm-vụ-2-thiết-lập-khung-thực-nghiệm-phân-cụm-milestone-m2-prep)
4. [Làm rõ các vấn đề kỹ thuật chuyên sâu](#4-làm-rõ-các-vấn-đề-kỹ-thuật-chuyên-sâu)
   - [Phân tầng Pipeline 5 bước từ M1 đến M2-PREP](#phân-tầng-pipeline-5-bước-từ-m1-đến-m2-prep)
   - [Giải pháp sau khi phát hiện 2 khoảng gián đoạn hệ thống](#giải-pháp-sau-khi-phát-hiện-2-khoảng-gián-đoạn-hệ-thống)
   - [Căn cứ và Trình tự chốt ngưỡng n_eligible >= 120 mã/snapshot](#căn-cứ-và-trình-tự-chốt-ngưỡng-n_eligible--120-mãsnapshot)
   - [Quy trình 5 bước thực hiện của M2-PREP](#quy-trình-5-bước-thực-hiện-của-m2-prep)
5. [Quá trình thực hiện chi tiết của từng Slide (Dành cho Thuyết trình sâu)](#5-quá-trình-thực-hiện-chi-tiết-của-từng-slide-dành-cho-thuyết-trình-sâu)
   - [Slide 02: Chi tiết quá trình vận hành Pipeline 5 tầng](#slide-02-chi-tiết-quá-trình-vận-hành-pipeline-5-tầng)
   - [Slide 03: Chi tiết quá trình lọc phễu 952 -> 922 -> 905 và phân rã 47 mã loại trừ](#slide-03-chi-tiết-quá-trình-lọc-phễu-952---922---905-và-phân-rã-47-mã-loại-trừ)
   - [Slide 04: Chi tiết công thức tính toán và chuẩn hóa 8 đặc trưng thị trường](#slide-04-chi-tiết-công-thức-tính-toán-và-chuẩn-hóa-8-đặc-trưng-thị-trường)
   - [Slide 05: Chi tiết quét chuỗi 80 tháng và lan truyền lỗi của 2 gián đoạn hệ thống](#slide-05-chi-tiết-quét-chuỗi-80-tháng-và-lan-truyền-lỗi-của-2-gián-đoạn-hệ-thống)
   - [Slide 06: Chi tiết 6 bước kỹ thuật thiết lập khung thực nghiệm M2-PREP](#slide-06-chi-tiết-6-bước-kỹ-thuật-thiết-lập-khung-thực-nghiệm-m2-prep)
6. [Hướng dẫn trả lời câu hỏi vấn đáp của Mentor (Q&A Defense Guide)](#6-hướng-dẫn-trả-lời-câu-hỏi-vấn-đáp-của-mentor-qa-defense-guide)

---

## 1. THÔNG ĐIỆP CỐT LÕI VÀ RANH GIỚI AN TOÀN

Báo cáo tuần này thể hiện sự chuyển giao quan trọng giữa hai giai đoạn:
1. **Milestone M1 (C8 Market Foundation) đã hoàn tất 100%:** Nhóm đã xây dựng thành công nền tảng dữ liệu thị trường có khả năng truy xuất nguồn gốc (provenance) và kiểm chứng offline, sàng lọc được 905 mã đạt chuẩn thị trường tại snapshot mới nhất (28/08/2026), vượt xa quy mô tối thiểu 300 mã của đề tài.
2. **Milestone M2 đang dừng lại ở bước M2-PREP:** Toàn bộ công cụ và mã nguồn cho K-Means, Ward, PCA đã được kiểm thử, nhưng nhóm chủ động **chưa chạy phân cụm thực tế và chưa backtest danh mục**. Trạng thái dự án được đặt là `MANUAL_REVIEW_REQUIRED` để trình Mentor phê duyệt 5 quyết định phương pháp luận trọng yếu nhằm tránh rủi ro định kiến kết quả (p-hacking).

### 4 Nguyên tắc bất biến (Invariants) cần ghi nhớ:
- **Nguyên tắc dữ liệu sạch:** Kiên quyết không điền số giả (no forward-fill), không nén thời gian để vá 2 khoảng gián đoạn lịch sử.
- **Nguyên tắc tư cách theo thời gian:** Không lấy danh sách 905 mã của hiện tại áp ngược về quá khứ (loại bỏ hoàn toàn sai lệch sống sót - survivorship bias).
- **Phân tách ranh giới rõ ràng:** 905 mã là `Market-Feature-Ready` tại snapshot hiện tại, **chưa phải** `Research-Ready` (vì chưa mở dữ liệu báo cáo tài chính chuẩn Point-in-Time).
- **Bức tường lửa phương pháp luận:** Tham số `portfolio_evaluation.enabled = false`. Tuyệt đối không dùng Sharpe Ratio, ROI hay lợi nhuận danh mục để chọn số cụm k hoặc chọn mô hình phân cụm M2.

---

## 2. ĐÁNH GIÁ VÀ KHUYẾN NGHỊ TINH GỌN SLIDE (TRANG 31 - 42)

Qua rà soát chuỗi 12 trang slide hiện tại trên Canva, nhóm nhận thấy 3 vấn đề gây cản trở mạch trình bày:
- **Trùng lặp định nghĩa:** Slide 32 (Roadmap) và Slide 33 (Mục tiêu M1) liệt kê lại các khái niệm lý thuyết chung chung đã thống nhất từ kickoff.
- **Phân mảnh logic:** Slide 35 đưa ra con số 905 mã, Slide 36 chuyển sang nói 8 đặc trưng, rồi Slide 37 lại quay về thanh minh ý nghĩa của 905 mã.
- **Slide kết luận lặp lại:** Slide 42 đọc lại các con số đã nêu ở Slide 31, 35, 40 mà không tạo ra hành động cụ thể.

### Bảng đối chiếu và giải pháp tinh gọn:

| Slide Canva | Tiêu đề hiện tại | Đánh giá & Rủi ro | Giải pháp tối ưu |
| :--- | :--- | :--- | :--- |
| **Slide 31** | Trang bìa M1 hoàn tất & M2-PREP | Cần thiết làm bìa | Giữ nguyên; thêm 1 câu thông điệp cốt lõi. |
| **Slide 32** | Roadmap M1-M2-M3 | Nặng tính định nghĩa lý thuyết đồ án | Gộp nhanh vào thanh tiến độ; chỉ rõ M1 đã xong, M2 đang dừng ở protocol gate, M3 chưa đụng tới. |
| **Slide 33 & 34** | Mục tiêu M1 & Pipeline đã làm | Trùng lặp ý tưởng giữa mục tiêu và các bước | Gộp thành 1 slide: "Nhiệm vụ 1: Mục đích & Pipeline xử lý dữ liệu M1". Nêu mục tiêu đi kèm sơ đồ 5 tầng. |
| **Slide 35 & 37** | Kết quả 905 mã & Giải thích 905 mã | Bị ngắt mạch tư duy | Tích hợp cảnh báo ranh giới (Market-Ready vs Research-Ready) vào ngay chân trang Slide 35 (Phễu dữ liệu). |
| **Slide 36** | Feature set hiện tại (8 features) | Rất trực quan và rõ ràng | Giữ nguyên; làm rõ ý nghĩa tài chính của 3 trục: Động lượng, Rủi ro, Thanh khoản. |
| **Slide 38** | Readiness 80 tháng (2 gián đoạn) | Thể hiện tính chính trực dữ liệu | Giữ nguyên; đổi tiêu đề thành "Kiểm soát tính liên tục lịch sử & 2 khoảng gián đoạn hệ thống". |
| **Slide 39** | M2-PREP khóa nguyên tắc eligibility | Trước đây còn trừu tượng | Viết lại theo 4 công việc thực tế của M2-PREP, nêu rõ ngưỡng n_eligible >= 120 mã/snapshot. |
| **Slide 40** | Các quyết định còn chờ duyệt | Trọng tâm thảo luận với Mentor | Giữ nguyên; trình bày bảng 5 quyết định kỹ thuật cần Mentor chốt. |
| **Slide 41 & 42** | Kế hoạch tuần tới & Kết luận | Slide 42 đọc lại số liệu cũ | Chuyển Slide 42 thành slide "Bảng Đề xuất Quyết định & Q&A" để tương tác trực tiếp với Mentor. |

---

## 3. CẤU TRÚC NỘI DUNG 2 NHIỆM VỤ TRỌNG TÂM (CHUẨN 4 TRỤ CỘT)

### NHIỆM VỤ 1: HOÀN TẤT NỀN TẢNG DỮ LIỆU THỊ TRƯỜNG (MILESTONE M1 - C8)

#### 1. Tên nhiệm vụ
Thu thập, chuẩn hóa dữ liệu giao dịch toàn diện và xây dựng phễu sàng lọc dữ liệu thị trường (C8 Market Foundation & Quality Assurance).

#### 2. Mục đích
- Thiết lập nền tảng dữ liệu thị trường sạch, có nguồn gốc rõ ràng (provenance) và có thể tái lập độc lập 100% khi chạy offline.
- Ngăn ngừa rủi ro nhìn trước tương lai (look-ahead bias) và sai lệch sống sót (survivorship bias) trước khi bước vào giai đoạn mô hình hóa.
- Chuẩn hóa bộ 8 đặc trưng thị trường đo lường Động lượng, Rủi ro và Thanh khoản.

#### 3. Quá trình thực hiện
Thực hiện qua quy trình kiểm soát chất lượng dữ liệu 4 tầng của M1 (thuộc Pipeline 5 tầng):
- *Tầng 1 (Raw Ingestion):* Thu thập dữ liệu giao dịch CafeF (TradeHistoryNew) và VN-Index; lưu trữ bất biến kèm mã băm SHA-256.
- *Tầng 2 (Normalization):* Chuẩn hóa đơn vị (VND/cổ phiếu), ngày giao dịch và áp dụng giá điều chỉnh (AdjustPrice x 1000) đúng chuẩn nhà cung cấp.
- *Tầng 3 (Feature Snapshot):* Tính 8 đặc trưng tại từng snapshot tháng; bắt buộc đủ 253 phiên giao dịch thực tế cho cửa sổ 1 năm; kiên quyết không điền số giả (no forward-fill).
- *Tầng 4 (Quality Report & QC):* Kiểm tra độ phủ, phân loại nguyên nhân loại trừ, khảo sát 80 tháng lịch sử (2020 - 2026) và kiểm chứng offline không phụ thuộc kết nối mạng.

#### 4. Kết quả đạt được
- **Phễu sàng lọc tại snapshot 28/08/2026:**
  - 952 mã ứng viên ban đầu (Candidate Universe).
  - 922 mã tính đủ 8 đặc trưng (Feature Complete - đạt 96.8%).
  - 905 mã đạt chuẩn thị trường sẵn sàng phân cụm (Market-Feature-Ready - đạt 95.1%), vượt xa quy mô tối thiểu 300 mã của đề tài.
- **Minh bạch 47 mã bị loại bỏ:**
  - 29 mã thiếu dữ liệu 253 phiên thực tế (mới niêm yết, đình chỉ giao dịch).
  - 17 mã chưa đủ 3 năm lịch sử quan sát theo chuẩn an toàn.
  - 1 mã không phát sinh dữ liệu tại ngày chốt snapshot.
- **Độ phủ vượt trội của 8 đặc trưng tại 28/08/2026:**
  - Động lượng: mom_21 (99.7%), mom_63 (99.4%), mom_126 (98.5%), mom_252 (96.8%).
  - Rủi ro: vol_63 (99.4%), mdd_126 (98.5%), beta_126 (98.5%).
  - Thanh khoản: liquidity_21 (99.7%).
- **Phát hiện trung thực 2 khoảng gián đoạn hệ thống trong 80 tháng:**
  - Gián đoạn 1 (05/2023 - 10/2023): Nguồn thô thiếu VN-Index ngày 15/05/2023 khiến beta_126 không thể hoàn tất trên toàn sàn.
  - Gián đoạn 2 (02/2025 - 01/2026): Nguồn thô thiếu giá cổ phiếu toàn sàn ngày 03/02/2025 khiến mom_252 thiếu 1 phiên thực tế.
- **Ranh giới học thuật:** 905 mã là `Market-Feature-Ready`, chưa phải `Research-Ready`.

---

### NHIỆM VỤ 2: THIẾT LẬP KHUNG THỰC NGHIỆM PHÂN CỤM (MILESTONE M2-PREP)

#### 1. Tên nhiệm vụ
Rà soát kỹ thuật và thiết lập khung quy chuẩn thực nghiệm phân cụm (M2-PREP Protocol Preparation & Governance Gate).

#### 2. Mục đích
- Đóng băng toàn bộ phương pháp luận trước khi chạy mô hình thực tế, ngăn ngừa hành vi tinh chỉnh mô hình theo kết quả có lợi (p-hacking).
- Thiết lập ranh giới an toàn: Loại bỏ hoàn toàn sai lệch sống sót và đóng băng đánh giá danh mục (`portfolio_evaluation.enabled = false`).
- Chuẩn bị sẵn sàng 5 quyết định kỹ thuật để xin ý kiến chỉ đạo từ Mentor.

#### 3. Quá trình thực hiện
M2-PREP triển khai 5 bước tuần tự chặt chẽ:
1. Tiếp nhận và đối soát tính toàn vẹn dữ liệu M1 qua mã băm SHA-256; tái lập chính xác 905 mã.
2. Khóa công thức tư cách ứng viên theo từng snapshot: `market_experiment_eligible(t) = market_feature_ready_v2(t)` và dựng bức tường lửa cấm dùng Sharpe/ROI để chọn mô hình M2.
3. Phân đoạn 4 Cửa sổ thời gian né 2 khoảng gián đoạn; đề xuất Cửa sổ phát triển 15 tháng (11/2023 - 01/2025) và Cửa sổ niêm phong 7 tháng (02/2026 - 08/2026); từ mức sàn 142 mã và bài toán k = 8 cụm, chốt quy tắc ngưỡng: `n_eligible >= 120 mã/snapshot`.
4. Rà soát ma trận Tiền xử lý (duyệt mặc định Reject missing; hỗ trợ Z-score, Robust Scaler, Winsorization, PCA) và ma trận Thuật toán (K-Means làm Baseline chính; PCA-KMeans và Ward làm đối sánh; khóa DBSCAN và Dynamic Clustering).
5. Xuất xưởng bộ 14 artifact M2-PREP và dừng lại ở Cổng kiểm soát `MANUAL_REVIEW_REQUIRED`.

#### 4. Kết quả đạt được
- Hoàn thành đầy đủ các artifact M2-PREP: `protocol_summary.json`, `candidate_windows.csv`, `unresolved_decisions.csv`, `preprocessing_matrix.csv`, `algorithm_matrix.csv`.
- Dừng lại ở trạng thái `MANUAL_REVIEW_REQUIRED`, chưa tạo `final_config` và chưa chạy phân cụm thực tế.
- Tổng hợp bảng 5 quyết định phương pháp luận then chốt trình Mentor phê duyệt.

---

## 4. LÀM RÕ CÁC VẤN ĐỀ KỸ THUẬT CHUYÊN SÂU

### Phân tầng Pipeline 5 bước từ M1 đến M2-PREP
Trong thiết kế tổng thể của dự án (Bảng 7 của tài liệu hướng dẫn và Slide 34), dòng dữ liệu chảy qua 5 tầng:
- **Tầng 1 đến Tầng 4 thuộc về Milestone M1:**
  - *Tầng 1 (Raw Ingestion):* Dữ liệu thô CafeF và benchmark VN-Index có mã băm bất biến.
  - *Tầng 2 (Normalization):* Chuẩn hóa định dạng, đơn vị tiền tệ và giá điều chỉnh.
  - *Tầng 3 (Feature Snapshot):* Trích xuất 8 đặc trưng theo tháng; kiểm tra đủ 253 phiên thực tế.
  - *Tầng 4 (Quality Report & QC):* Phễu dữ liệu, độ phủ, phát hiện 2 khoảng gián đoạn.
- **Tầng 5 chính là M2-PREP:**
  - Nhận đầu vào là bằng chứng từ M1.
  - Đóng công thức tư cách ứng viên theo từng snapshot (`market_experiment_eligible(t)`).
  - Lập danh mục các quyết định phương pháp luận chờ duyệt.
- *Lưu ý về Kiểm chứng offline (Offline Verification):* Đây không phải là một tầng thứ 5 tách rời, mà là **nguyên tắc đảm bảo chất lượng xuyên suốt của M1** (nằm ở Tầng 4: đọc dữ liệu đóng băng có hash SHA-256 để kiểm tra mà không cần gọi lại network).

---

### Giải pháp sau khi phát hiện 2 khoảng gián đoạn hệ thống
Sau khi C8 phát hiện 2 khoảng gián đoạn (05/2023 - 10/2023 và 02/2025 - 01/2026), nhóm đã triển khai ngay 3 hành động cụ thể trong M2-PREP:
1. **Kiên quyết không điền số giả (no forward-fill):** Không nén thời gian để vá biểu đồ nhằm bảo vệ tính trung thực tài chính.
2. **Phân đoạn dữ liệu thành các Cửa sổ sạch (Candidate Windows):**
   - Khoanh vùng Cửa sổ liên tục 15 tháng (11/2023 - 01/2025) nằm kẹp giữa 2 khoảng gap để làm **Tập phát triển mô hình (Development Set)**.
   - Khoanh vùng Cửa sổ phục hồi 7 tháng (02/2026 - 08/2026) sau khi gap 2025 kết thúc để làm **Tập kiểm định độc lập (Holdout Set)**.
3. **Thiết lập Quy tắc bỏ qua có kiểm soát (Skip Policy):** Snapshot nào có số mã dưới 120 sẽ tự động bị bỏ qua; tuyệt đối không nối ma trận chuyển dịch cụm hay tính ARI xuyên qua khoảng trống dữ liệu.

---

### Căn cứ và Trình tự chốt ngưỡng n_eligible >= 120 mã/snapshot
Việc lựa chọn ngưỡng 120 mã hoàn toàn **thuộc về M2-PREP (không phải C8)**. Trình tự tư duy diễn ra như sau:
1. **Khảo sát Cửa sổ Dev trước (Làm trước):** Khi khảo sát Cửa sổ liên tục chính (11/2023 - 01/2025), nhóm ghi nhận số lượng mã sẵn sàng dao động từ **142 đến 780 mã** (tháng thấp nhất là tháng 11/2023 đạt **142 mã**).
2. **Xét bài toán phân cụm k = 8 cụm:** Để tránh hiện tượng cụm nhỏ chỉ có 1-3 mã làm tâm cụm (centroid) bị méo mó bởi nhiễu riêng lẻ, mỗi cụm cần trung bình tối thiểu **15 cổ phiếu** -> 8 x 15 = 120 mã.
3. **Đối chiếu và chốt ngưỡng 120 mã (Chốt sau):** Vì 142 > 120, ngưỡng 120 mã vừa đảm bảo độ dày thống kê cho 8 cụm, vừa đảm bảo **100% (15/15 tháng) của Cửa sổ phát triển đều vượt qua kiểm tra** mà không bị loại bỏ oan. Quy tắc này được ghi nhận chính thức tại Mục 6.3 trong `docs/DELTA_UNIFIED_PROJECT_PLAN.md`.

---

### Quy trình 5 bước thực hiện của M2-PREP
Tóm tắt quy trình mà module `src/delta_t1/experiments/m2_prep.py` đã thực hiện:
- **Bước 1:** Tiếp nhận & kiểm tra mã băm SHA-256 của các artifact M1; tái lập 905/952 mã tại 28/08/2026.
- **Bước 2:** Khóa tư cách `market_experiment_eligible(t)` theo từng tháng; cấm lọc ngược 905 mã; dựng bức tường lửa cấm Sharpe/ROI can thiệp vào M2.
- **Bước 3:** Phân đoạn 4 cửa sổ thời gian; đề xuất Cửa sổ Dev (15 tháng), Cửa sổ Holdout (7 tháng); chốt quy tắc ngưỡng `n_eligible >= 120` và Skip policy.
- **Bước 4:** Rà soát ma trận Tiền xử lý (duyệt Reject missing, hỗ trợ Z-score/Robust/PCA) và ma trận Thuật toán (K-Means baseline, Ward/PCA comparator, khóa DBSCAN/Dynamic).
- **Bước 5:** Xuất bản bộ 14 artifact M2-PREP; khóa trạng thái `MANUAL_REVIEW_REQUIRED`, dừng lại chờ Mentor phê duyệt 5 quyết định.

---

## 5. QUÁ TRÌNH THỰC HIỆN CHI TIẾT CỦA TỪNG SLIDE (DÀNH CHO THUYẾT TRÌNH SÂU)

Phần này cung cấp toàn bộ chi tiết kỹ thuật trong mã nguồn, giải thích cặn kẽ cơ chế vận hành để người thuyết trình có thể tự tin trả lời bất kỳ câu hỏi chuyên sâu nào từ Hội đồng/Mentor theo từng trang Slide:

### Slide 02: Chi tiết quá trình vận hành Pipeline 5 tầng
Khi thuyết trình Slide 04, bạn cần giải thích rõ cơ chế vận hành độc lập và ngăn chặn lỗi của từng tầng:
1. **Tầng 1 (Raw Ingestion - CafeF & Benchmark):**
   - *Cách thực hiện:* Sử dụng adapter chuyên biệt gọi API `TradeHistoryNew` của CafeF để lấy lịch sử giao dịch từng mã và chỉ số VN-Index.
   - *Kiểm soát rủi ro:* Mọi payload JSON/HTML tải về đều được lưu nguyên trạng vào thư mục raw, tạo mã băm SHA-256 ghi vào `manifest.json`. Tuyệt đối không sửa trực tiếp vào file thô để bảo toàn tính toàn vẹn (data integrity).
2. **Tầng 2 (Chuẩn hóa - Normalization Engine):**
   - *Cách thực hiện:* Chuyển đổi dữ liệu thô sang 2 bảng canonical: `prices_daily` (cổ phiếu) và `benchmark_daily` (VN-Index).
   - *Kiểm soát rủi ro:* Đồng bộ ngày giao dịch chuẩn `YYYY-MM-DD`. Đơn vị tiền tệ chuẩn hóa về VND (nhân giá với 1000 nếu provider trả về nghìn đồng). Khối lượng chuẩn hóa về cổ phiếu (shares). Đặc biệt, giá điều chỉnh được gán `adjustment_basis = vendor-adjusted` (AdjustPrice x 1000), không tự ý suy diễn là split-only hay dividend-adjusted khi chưa có bằng chứng corporate actions.
3. **Tầng 3 (Trích xuất đặc trưng - Feature Snapshot Engine):**
   - *Cách thực hiện:* Mã nguồn `src/delta_t1/features/market.py` tính toán 8 đặc trưng tại từng ngày giao dịch cuối cùng của mỗi tháng (monthly snapshot).
   - *Kiểm soát rủi ro:* Áp dụng quy tắc kiểm tra phiên thực tế nghiêm ngặt (real trading observations). Để tính đặc trưng cửa sổ 252 phiên (`mom_252`), hệ thống yêu cầu phải có đúng **253 mức giá thực tế** (giá ngày t và 252 giá quá khứ). Nếu thiếu dù chỉ 1 phiên (chỉ có 252 giá), trường đó bị gán `null`. Kiên quyết áp dụng nguyên tắc fail-closed: Không forward-fill, không backfill, không gán 0 cho dữ liệu thiếu.
4. **Tầng 4 (Báo cáo chất lượng & Kiểm chứng Offline - QA & Offline Verification):**
   - *Cách thực hiện:* Script `scripts/build_m1_market_foundation_report.py` đọc toàn bộ feature snapshots, quét 80 tháng lịch sử để lập phễu sàng lọc và ma trận độ phủ.
   - *Kiểm soát rủi ro:* Toàn bộ báo cáo và biểu đồ được sinh ra từ các artifact đã đóng băng. Khi chạy lại quá trình kiểm định, hệ thống kiểm tra mã băm checksum để đảm bảo tái lập 100% (reproducibility) mà không thực hiện bất kỳ network call nào ra ngoài.
5. **Tầng 5 (Khung chuẩn bị thực nghiệm - M2-PREP):**
   - *Cách thực hiện:* Module `src/delta_t1/experiments/m2_prep.py` nhận đầu vào từ các báo cáo của Tầng 4 để chuẩn bị không gian nghiên cứu cho M2.
   - *Kiểm soát rủi ro:* Khóa công thức tư cách ứng viên, rà soát ma trận thuật toán và dừng lại ở trạng thái `MANUAL_REVIEW_REQUIRED`.

---

### Slide 03: Chi tiết quá trình lọc phễu 952 -> 922 -> 905 và phân rã 47 mã loại trừ
Khi thuyết trình Slide 05, bạn giải thích chi tiết cơ chế phân tầng lọc cổ phiếu tại snapshot 28/08/2026:
1. **Nấc 1: 952 mã ứng viên ban đầu (Candidate Universe):**
   - Xuất phát từ universe khảo sát gồm 500 mã thuộc tập baseline C5 ban đầu và 452 mã mở rộng (expansion) đã hoàn thành thu thập dữ liệu (còn 148 mã expansion tạm hoãn do giới hạn nguồn). Tổng cộng có 952 cổ phiếu được đưa vào rà soát tại snapshot 28/08/2026.
2. **Nấc 2: Rớt 30 mã -> Còn 922 mã hoàn tất đặc trưng (Feature Complete - 96.8%):**
   - Để đạt `Feature Complete`, một mã phải tính toán ra giá trị hữu hạn (finite value) cho toàn bộ 8 đặc trưng thị trường.
   - Có đúng **30 mã bị rớt** ở nấc này do không thỏa mãn điều kiện cửa sổ quan sát: Trong đó có 29 mã không đủ 253 phiên giao dịch thực tế trong 1 năm gần nhất (do mới niêm yết chưa đủ 1 năm, hoặc bị đình chỉ/tạm ngừng giao dịch dài ngày), và 1 mã không phát sinh bản ghi snapshot tại ngày 28/08/2026.
3. **Nấc 3: Rớt tiếp 17 mã -> Còn 905 mã đạt chuẩn thị trường (Market-Feature-Ready - 95.1%):**
   - Dù 17 mã này đã tính đủ 8 đặc trưng tại snapshot hiện tại, chúng tiếp tục bị loại khỏi danh sách thực nghiệm thị trường do vi phạm **Quy tắc an toàn lịch sử 3 năm (Three calendar years usable observed history rule)**.
   - Quy tắc này quy định: Cổ phiếu tham gia phân cụm thực tế phải có lịch sử giao dịch quan sát được ít nhất 3 năm dương lịch trước đó để đảm bảo tính ổn định về mặt phân phối thống kê. Các mã mới lên sàn từ 1 đến 2 năm được xếp vào nhóm `REFERENCE_ONLY`, không đưa vào tập phân cụm chính.
4. **Phân rã chính xác 47 mã bị loại bỏ (Readiness Exclusions):**
   - 30 mã (ở nấc 2) + 17 mã (ở nấc 3) = 47 mã loại trừ.
   - Gồm: **29 mã** thiếu 253 phiên thực tế; **17 mã** thiếu 3 năm lịch sử; **1 mã** thiếu bản ghi snapshot.
   - *Thông điệp đắt giá:* Việc loại bỏ 47 mã này không phải do crawler bị lỗi, mà là do các cổng kiểm soát chất lượng hoạt động hiệu quả để bảo vệ mô hình khỏi dữ liệu rác.

---

### Slide 04: Chi tiết công thức tính toán và chuẩn hóa 8 đặc trưng thị trường
Khi thuyết trình Slide 06, bạn trình bày rõ cơ sở toán học và tài chính của 8 đặc trưng trong file `src/delta_t1/features/market.py`:
1. **Trục Động lượng (Momentum) - 4 đặc trưng:**
   - Sử dụng xấp xỉ theo số phiên giao dịch chuẩn thay vì tính theo ngày lịch: 21 phiên (~1 tháng), 63 phiên (~3 tháng), 126 phiên (~6 tháng), 252 phiên (~12 tháng).
   - Công thức: Log-return tích lũy giữa giá đóng cửa điều chỉnh (Adjusted Close) tại ngày t so với giá cách đó k phiên: `mom_k = ln(P_t / P_{t-k})`.
   - Độ phủ: `mom_21` đạt 99.7%, `mom_63` đạt 99.4%, `mom_126` đạt 98.5%, `mom_252` đạt 96.8% (độ phủ giảm dần ở các khung dài hơn do yêu cầu số phiên thực tế lớn hơn).
2. **Trục Rủi ro (Risk) - 3 đặc trưng:**
   - `vol_63` (Độ biến động 63 phiên): Độ lệch chuẩn mẫu của chuỗi tỷ suất sinh lợi ngày trong 63 phiên gần nhất, được thường niên hóa bằng cách nhân với căn bậc hai của 252: `vol_63 = std(r_daily) * sqrt(252)`. Độ phủ đạt 99.4%.
   - `mdd_126` (Mức sụt giảm tối đa 126 phiên - Maximum Drawdown): Đo lường rủi ro đuôi (downside risk), tính tỷ lệ sụt giảm sâu nhất từ đỉnh lũy kế trong 126 phiên giao dịch: `mdd_126 = min((P_t - Peak_t) / Peak_t)`. Độ phủ đạt 98.5%.
   - `beta_126` (Hệ số nhạy cảm thị trường): Hệ số dốc thu được từ hồi quy OLS hiệp phương sai giữa tỷ suất sinh lợi ngày của cổ phiếu và chỉ số VN-Index trong 126 phiên: `beta_126 = Cov(r_stock, r_vnindex) / Var(r_vnindex)`. Độ phủ đạt 98.5%.
3. **Trục Thanh khoản (Liquidity) - 1 đặc trưng:**
   - `liquidity_21`: Logarit tự nhiên của giá trị giao dịch khớp lệnh trung bình 21 phiên gần nhất: `liquidity_21 = ln(mean(Volume * Close))`. Độ phủ đạt 99.7%.
4. **Cơ chế Bức tường lửa (Model Selection Firewall):**
   - Tỷ số Sharpe và ROI bị cấm tuyệt đối vì chúng đại diện cho kết quả đầu tư danh mục (portfolio outcome) ở giai đoạn M3 Backtest. Nếu đưa Sharpe vào phân cụm ở M2 sẽ làm rò rỉ mục tiêu tối ưu, dẫn đến việc chọn cụm dựa trên hiệu quả trong quá khứ thay vì đặc tính động lượng khách quan.
   - Các chỉ số tài chính (P/E, P/B, ROE) chưa được mở vì dữ liệu báo cáo tài chính đòi hỏi cơ chế Point-in-Time (ngày công bố báo cáo phải trước ngày chốt snapshot) và lịch sử hồi tố chưa được phê duyệt.
5. **Cơ chế Chuẩn hóa thang đo (Feature Scaling) - Tại sao chọn Robust Scaling làm mặc định:**
   - *Công thức:* `x_scaled = (x - median) / IQR`, trong đó IQR = Q75 - Q25 (khoảng tứ phân vị từ phân vị 25% đến 75%).
   - *Lý do 1 - Khác biệt thang đo giữa 8 đặc trưng:* Các biến dao động ở đơn vị và biên độ rất khác nhau (ví dụ: mom_21 dao động quanh 0, liquidity_21 là log giá trị giao dịch, vol_63 là độ lệch chuẩn năm).
   - *Lý do 2 - Độ nhạy khoảng cách của K-Means và Ward:* K-Means và Hierarchical Ward sử dụng khoảng cách Euclidean. Nếu không chuẩn hóa, đặc trưng có phương sai lớn sẽ chi phối hoàn toàn kết quả phân cụm.
   - *Lý do 3 - Dữ liệu thị trường có đuôi dày (heavy tails) và ngoại lai (outliers):* Dữ liệu chứng khoán thường xuyên xuất hiện các mức tăng/giảm trần sàn hoặc đột biến thanh khoản. Nếu dùng Z-score (dựa vào Mean và Std), giá trị trung bình và độ lệch chuẩn bị kéo lệch nghiêm trọng bởi ngoại lai, khiến phần lớn cổ phiếu bình thường bị nén chặt lại một chỗ.
   - *Lý do 4 - Bảo toàn 100% dữ liệu thực tế (No clipping):* Robust Scaling dùng Trung vị (Median) và IQR là các đại lượng thống kê vững. Phương pháp này giảm thiểu tác động của ngoại lai một cách tự nhiên mà không cần cắt xén (Winsorization) hay xóa bỏ quan sát, giữ nguyên vẹn hành vi thị trường thực tế.
   - *Vai trò trong M2:* Robust Scaling được đề xuất làm Mặc định (Default); Z-score được giữ làm Nhánh đối sánh độ nhạy (Sensitivity Comparator).


---

### Slide 05: Chi tiết quét chuỗi 80 tháng và lan truyền lỗi của 2 gián đoạn hệ thống
Khi thuyết trình Slide 08, bạn phân tích chi tiết cơ chế lan truyền lỗi (error propagation) trong 80 tháng (01/2020 đến 08/2026):
1. **Quá trình quét chuỗi thời gian:**
   - Script đánh giá quét qua 80 thời điểm chốt tháng liên tục. Từ năm 2020 đến 2022, số lượng mã sẵn sàng tăng dần từ 87 lên 518 mã theo sự mở rộng của thị trường.
2. **Chi tiết Gián đoạn 1 (05/2023 - 10/2023 - Lỗi thiếu dữ liệu Benchmark):**
   - *Nguyên nhân gốc rễ:* Ngày **15/05/2023**, cả 3 sàn HNX, HOSE, UPCOM đều mở cửa giao dịch bình thường, nhưng nguồn dữ liệu CafeF bị thiếu bản ghi chỉ số VN-Index của ngày hôm đó.
   - *Cơ chế lan truyền lỗi:* Vì đặc trưng `beta_126` yêu cầu chuỗi VN-Index đủ 126 phiên khớp từng ngày với cổ phiếu, sự khuyết thiếu đúng 1 ngày này làm phép tính hồi quy `beta_126` bị fail trên **toàn bộ 952 cổ phiếu**. Lỗi này tồn tại suốt 6 tháng (tương đương 126 phiên) cho đến khi ngày 15/05/2023 trôi ra khỏi cửa sổ tính toán vào tháng 11/2023. Kết quả là số mã sẵn sàng bị rơi về 0 trong suốt 6 tháng này.
3. **Chi tiết Gián đoạn 2 (02/2025 - 01/2026 - Lỗi thiếu dữ liệu Cổ phiếu toàn sàn):**
   - *Nguyên nhân gốc rễ:* Ngày **03/02/2025** (phiên giao dịch khai xuân sau Tết), hệ thống ghi nhận 0 bản ghi giá cổ phiếu trên toàn thị trường từ nhà cung cấp.
   - *Cơ chế lan truyền lỗi:* Đặc trưng `mom_252` yêu cầu đủ 253 mức giá thực tế trong 252 phiên giao dịch. Việc thiếu 1 ngày giao dịch mở cửa khiến toàn bộ cổ phiếu trên thị trường chỉ có tối đa 252 mức giá thực tế (thiếu đúng 1 phiên). Lỗi này lan truyền trong suốt 12 tháng (tương đương 252 phiên giao dịch) cho đến tháng 02/2026 khi ngày 03/02/2025 trôi ra khỏi cửa sổ 1 năm. Kết quả là số mã sẵn sàng lại bị rơi về 0 trong suốt 12 tháng này.
4. **Chi tiết 3 hành động kỹ thuật giải quyết của nhóm:**
   - *Không sửa số liệu:* Nhóm không forward-fill giá ngày hôm trước vào ngày 03/02/2025 để tránh tạo ra biến động giả.
   - *Phân đoạn né khoảng gap:* Nhóm xác định khoảng thời gian nằm kẹp giữa 2 đứt đoạn này (từ tháng 11/2023 đến tháng 01/2025) là **15 tháng hoàn toàn sạch và liên tục** để làm tập phát triển mô hình.
   - *Cơ chế Skip tự động:* Lập trình runner tự động ngắt chuỗi và bỏ qua các snapshot bị rơi về 0, không tính toán ma trận dịch chuyển cụm xuyên qua các tháng bị khuyết.

---

### Slide 05: Chi tiết 6 bước kỹ thuật thiết lập khung thực nghiệm M2-PREP
Khi thuyết trình Slide 09, bạn trình bày chi tiết từng bước mà module `src/delta_t1/experiments/m2_prep.py` đã thực hiện:
1. **Bước 1: Tiếp nhận và xác thực tính toàn vẹn (Integrity Verification):**
   - Tự động nạp các tệp bất biến từ M1: `candidate_universe.csv`, `feature_snapshots.jsonl` và `monthly_market_readiness.csv`.
   - Kiểm tra mã băm SHA-256 đối chiếu với `manifest.json`. Thực thi kiểm tra chéo độc lập để tái lập chính xác con số 905/952 mã tại ngày 28/08/2026.
2. **Bước 2: Khóa quy chuẩn tư cách ứng viên theo snapshot (Eligibility Freeze):**
   - Đóng băng công thức: `market_experiment_eligible(t) = market_feature_ready_v2(t)` tại cùng thời điểm t.
   - Chặn đứng hoàn toàn lỗi sai lệch sống sót (Survivorship bias): Tại mỗi tháng t trong quá khứ, mô hình chỉ được nạp những cổ phiếu thực sự đủ điều kiện tại tháng t đó: Có đủ 253 phiên giao dịch thực tế trong 1 năm tính từ ngày t trở về trước; Có đủ 253 phiên giao dịch thực tế trong 1 năm tính từ ngày t trở về trước; Tính toán ra đầy đủ cả 8 đặc trưng động lượng - rủi ro - thanh khoản, tuyệt đối không dùng danh sách 905 mã của hiện tại để lọc ngược lịch sử.
3. **Bước 3: Đo lường và phân đoạn 4 Cửa sổ thời gian (Candidate Windows Inventory):**
   - Phân tích chuỗi 44 tháng sau gap để xuất bản file `candidate_windows.csv` gồm 4 lựa chọn:
     + *Cửa sổ 1 (Pre-benchmark gap short):* 01/2023 - 04/2023 (4 tháng, 87 - 518 mã) -> Quá ngắn để đánh giá độ ổn định.
     + *Cửa sổ 2 (Contiguous main):* 11/2023 - 01/2025 (15 tháng liên tục không đứt đoạn, quy mô từ 142 đến 780 mã) -> **Đề xuất làm Cửa sổ phát triển (Development Window)**.
       * *Mục đích 1 - Khám phá và tinh chỉnh mô hình:* Dùng để huấn luyện các thuật toán phân cụm (K-Means Baseline, Hierarchical Ward, PCA-KMeans), so sánh ma trận tiền xử lý và xác định số cụm tối ưu toàn cục (global k) dựa trên các chỉ số nội tại (Silhouette, Davies-Bouldin).
       * *Mục đích 2 - Đánh giá độ ổn định thời gian liên tục (Temporal Stability):* Nhờ chuỗi 15 tháng liền mạch 100% không bị ngắt quãng, mô hình có thể đo lường chính xác ma trận chuyển dịch cụm (transition matrix), tỷ lệ duy trì thành viên cụm (cluster persistence) và chỉ số ARI/NMI tháng-liền-kề mà không bị méo mó bởi các khoảng gián đoạn dữ liệu.
       * *Mục đích 3 - Đảm bảo độ dày thống kê an toàn:* Quy mô mã dao động từ 142 đến 780 mã, luôn vượt ngưỡng tối thiểu 120 mã (bảo đảm mỗi cụm có trung bình ít nhất 15 cổ phiếu khi thử nghiệm k lên đến 8).
     + *Cửa sổ 3 (Latest recovery):* 02/2026 - 08/2026 (7 tháng gần nhất, quy mô từ 253 đến 905 mã) -> **Đề xuất làm Cửa sổ niêm phong (Holdout Window)**.
       * *Mục đích 1 - Kiểm định ngoài mẫu độc lập (Out-of-Sample Generalization):* Được niêm phong tuyệt đối trong suốt quá trình phát triển mô hình và chỉ mở ra kiểm thử đúng 1 lần duy nhất sau khi đã đóng băng toàn bộ tham số, thuật toán và số cụm k. Điều này giúp kiểm chứng năng lực tổng quát hóa của cấu trúc cụm trên dữ liệu hoàn toàn chưa từng thấy (unseen data), triệt tiêu hoàn toàn rủi ro quá khớp (overfitting) và sai lệch lựa chọn (p-hacking / data snooping).
       * *Mục đích 2 - Đánh giá tính ứng dụng trên quy mô thị trường hiện hành:* Đây là giai đoạn gần nhất với thực tế (kết thúc tại snapshot mới nhất ngày 28/08/2026 với 905 mã), phản ánh đầy đủ nhất độ sâu và thanh khoản hiện tại của thị trường chứng khoán Việt Nam trước khi chuyển sang giai đoạn M3.
     + *Cửa sổ 4 (Full post history with skips):* 01/2023 - 08/2026 (44 tháng, có 18 tháng zero-readiness) -> Yêu cầu chính sách bỏ qua rõ ràng.
4. **Bước 4: Thiết lập quy tắc ngưỡng tối thiểu n_eligible >= 120 mã/snapshot:**
   - Xuất phát từ Cửa sổ phát triển 15 tháng (11/2023 - 01/2025) có tháng thấp nhất đạt 142 mã.
   - Kết hợp với bài toán phân cụm động lượng dự kiến thử nghiệm số cụm tối đa k = 8. Để mỗi cụm có độ dày thống kê trung bình ít nhất 15 cổ phiếu (8 x 15 = 120), nhóm chốt ngưỡng **120 mã**.
   - Vì 142 > 120, ngưỡng này vừa đảm bảo độ ổn định của tâm cụm, vừa đảm bảo **100% cả 15 tháng của tập phát triển đều vượt qua bài kiểm tra** mà không bị ngắt quãng.
5. **Bước 5: Rà soát ma trận Tiền xử lý và Thuật toán (Matrices Audit):**
   - *Ma trận Tiền xử lý:* Đã kiểm thử xong code cho Xử lý khuyết thiếu (Reject missing, no imputation - duyệt mặc định); Winsorization clipping; Z-score; Robust Scaler; và PCA. Trong đó, Robust Scaler được đề xuất làm mặc định vì cơ chế Median/IQR kháng ngoại lai đuôi dày đặc thù của chứng khoán mà không làm mất quan sát thật; Z-score giữ làm đối sánh. Loại bỏ Log1p vì các đặc trưng lợi nhuận mang giá trị âm.
   - *Ma trận Thuật toán:* Xác định K-Means tất định (cố định seed, n_init, max_iter) làm Mô hình cơ sở (Primary Baseline); PCA kết hợp K-Means và Hierarchical Ward làm Mô hình đối sánh (Approved Comparators). Khóa DBSCAN (vì không tương thích cơ chế k cố định) và khóa Dynamic Clustering (chưa có hàm mục tiêu ràng buộc trạng thái).
6. **Bước 6: Thiết lập Cổng kiểm soát quản trị (Governance Gate):**
   - Xuất bản bộ 14 file artifact kiểm chứng bất biến (như `protocol_summary.json`, `unresolved_decisions.csv`).
   - Đặt trạng thái nghiệm thu: **`MANUAL_REVIEW_REQUIRED`**. Nhóm kiên quyết chưa tạo file cấu hình cuối cùng `final_config` và chưa chạy phân cụm thực tế, dừng lại đúng cổng kiểm soát để trình Mentor phê duyệt 5 quyết định ở Slide 40.

---

## 6. HƯỚNG DẪN TRẢ LỜI CÂU HỎI VẤN ĐÁP CỦA MENTOR (Q&A DEFENSE GUIDE)

### Câu 1: Dự án đã đạt quy mô tối thiểu 300 mã cổ phiếu theo yêu cầu đề tài chưa?
**Trả lời:** Dạ thưa Thầy/Cô, dự án đã đạt và vượt xa chỉ tiêu. Tại snapshot mới nhất ngày 28/08/2026, chúng em có 905 mã đạt chuẩn Market-Feature-Ready. Ngay cả trong giai đoạn lịch sử liên tục 15 tháng (11/2023 - 01/2025), số lượng cổ phiếu đủ điều kiện luôn dao động từ 142 đến 780 mã, hoàn toàn đáp ứng độ tin cậy cho bài toán phân cụm.

### Câu 2: Tại sao nhóm lại đặt điều kiện mỗi snapshot phải có tối thiểu 120 mã (n_eligible >= 120)? Con số này từ đâu ra?
**Trả lời:** Dạ thưa Thầy/Cô, ngưỡng n_eligible >= 120 là một lựa chọn quy chuẩn phương pháp luận (project protocol choice) được nhóm thiết kế có chủ đích dựa trên 2 cơ sở:
1. *Về mặt thống kê:* Khi thử nghiệm số cụm tối đa lên tới k = 8, 120 mã bảo đảm mỗi cụm có trung bình ít nhất 15 quan sát (120 / 8 = 15). Nếu dưới 120 mã, các cụm nhỏ sẽ bị rơi vào tình trạng chỉ có 1-3 mã, khiến trọng tâm cụm mất tính đại diện và nhạy cảm quá mức với nhiễu riêng lẻ.
2. *Về mặt dữ liệu thực tế:* Nhóm đã khảo sát Cửa sổ liên tục chính 15 tháng (11/2023 - 01/2025) trước, thấy số lượng mã dao động từ 142 đến 780. Con số thấp nhất là 142 mã lớn hơn 120, nên ngưỡng 120 bảo đảm toàn bộ 15 tháng phát triển này đều vượt qua bài kiểm tra một cách liên tục mà không bị loại bỏ oan.

### Câu 3: Tại sao biểu đồ readiness lịch sử lại có những tháng về 0?
**Trả lời:** Dạ thưa Thầy/Cô, việc readiness về 0 trong 2 giai đoạn (năm 2023 và năm 2025) là do các đứt đoạn khách quan từ nguồn dữ liệu thô: năm 2023 thiếu 1 phiên VN-Index ngày 15/05, còn năm 2025 thiếu 1 phiên giao dịch toàn sàn ngày 03/02. Do nhóm áp dụng quy tắc an toàn dữ liệu 100% không điền số giả (no forward-fill), các đặc trưng dài hạn như beta_126 và mom_252 không đủ 253 phiên thực tế. Thay vì bóp méo dữ liệu để số đẹp, nhóm phản ánh trung thực để xây dựng Cửa sổ phát triển 15 tháng né khoảng gap và thiết lập quy tắc bỏ qua tháng gián đoạn một cách khoa học.

### Câu 4: Con số 905 mã có phải là tập mẫu nghiên cứu cuối cùng (final sample) không?
**Trả lời:** Dạ không ạ. 905 mã là số lượng cổ phiếu đủ điều kiện dữ liệu thị trường tại ĐÚNG snapshot 28/08/2026. Nhóm không dùng con số này làm tập mẫu cố định xuyên suốt lịch sử, vì làm vậy sẽ mắc lỗi Survivorship Bias. Trong phân cụm theo thời gian, membership của mỗi tháng được xác định động tại đúng tháng đó.

### Câu 5: Nhóm đã chạy thuật toán phân cụm nào chưa? Kết quả ra sao?
**Trả lời:** Dạ báo cáo Thầy/Cô, nhóm kiên quyết CHƯA chạy phân cụm thực tế trên toàn bộ dữ liệu. M2-PREP là chặng dừng để khóa quy chuẩn phương pháp luận (window, holdout, k, scaling) nhằm đảm bảo tính khách quan của nghiên cứu, tránh việc nhìn thấy kết quả rồi mới quay lại chỉnh tham số mô hình.

### Câu 6: Có thể dùng Sharpe Ratio hoặc ROI của danh mục để chọn số cụm k tối ưu không?
**Trả lời:** Dạ tuyệt đối không ạ. Theo nguyên tắc phân tầng nghiên cứu của dự án, bài toán phân cụm ở M2 là học không giám sát thuần túy, việc chọn k và mô hình phải dựa trên các thước đo chất lượng cụm như Silhouette Score hay Davies-Bouldin. Tỷ số Sharpe và ROI chỉ thuộc giai đoạn M3 khi đánh giá chiến lược danh mục đầu tư.

### Câu 7: Tại sao nhóm không đưa các chỉ số tài chính (P/E, P/B, ROE) vào phân cụm luôn ở M2?
**Trả lời:** Dạ vì dữ liệu tài chính đòi hỏi tính thời điểm Point-in-Time (ngày công bố báo cáo tài chính phải trước ngày ra quyết định) và xử lý hồi tố phức tạp. Để đảm bảo tiến độ và độ tin cậy, nhóm tập trung giải quyết dứt điểm phân cụm động lượng điều chỉnh rủi ro dựa trên dữ liệu thị trường trước, dữ liệu tài chính sẽ được nghiên cứu sau khi hoàn thiện cơ chế Point-in-Time.

### Câu 8: K-Means chạy độc lập từng tháng rồi so sánh ARI có được gọi là Dynamic Clustering không?
**Trả lời:** Dạ không ạ. Việc chạy K-Means độc lập từng tháng và đo độ dịch chuyển cụm (ARI/NMI) chỉ đóng vai trò là mô hình cơ sở (Static Baseline) và công cụ chẩn đoán tính ổn định thời gian. Một thuật toán Dynamic Clustering thực thụ đòi hỏi hàm mục tiêu ràng buộc theo thời gian, cập nhật trạng thái liên tục và cần một nghiên cứu chuyên sâu riêng.

### Câu 9: Nhóm đề xuất lựa chọn cửa sổ thời gian nào để huấn luyện mô hình M2?
**Trả lời:** Dạ nhóm đề xuất dùng Cửa sổ liên tục chính gồm 15 tháng (từ tháng 11/2023 đến 01/2025) làm tập phát triển mô hình (Development Set) vì chuỗi thời gian hoàn toàn liên tục và số lượng mã luôn đạt từ 142 đến 780 mã, vượt xa ngưỡng tối thiểu 120 mã. Đồng thời, nhóm đề xuất niêm phong 7 tháng gần nhất (02/2026 - 08/2026) làm tập Holdout chỉ kiểm thử 1 lần duy nhất.

### Câu 10: Tại sao nhóm đề xuất dùng Robust Scaling làm chuẩn hóa mặc định thay vì Z-score hay Min-Max?
**Trả lời:** Dạ thưa Thầy/Cô, nhóm đề xuất Robust Scaling làm chuẩn hóa mặc định dựa trên 3 lý do:
1. *Đặc thù phân phối tài chính:* Dữ liệu thị trường chứng khoán Việt Nam có hiện tượng đuôi dày (heavy tails) và thường xuyên xuất hiện các biến động cực đoan (outliers) do trần/sàn. Nếu dùng Z-score (dựa vào Mean và Std) hay Min-Max, các ngoại lai này sẽ kéo lệch giá trị trung bình và độ lệch chuẩn, khiến phần lớn cổ phiếu bình thường bị nén chặt lại một chỗ.
2. *Thống kê vững (Robust Statistics):* Robust Scaling dùng công thức: x_scaled = (x - median) / IQR. Trung vị (Median) và khoảng tứ phân vị (IQR = Q75 - Q25) không bị chi phối bởi các giá trị cực trị ở hai đầu phân phối.
3. *Bảo toàn dữ liệu thật mà không cần cắt xén:* Nhóm chủ trương không cắt gọt dữ liệu (no clipping/winsorization) để bảo tồn hành vi thực tế của thị trường. Robust Scaling vừa kiểm soát được ảnh hưởng của ngoại lai, vừa giữ nguyên 100% quan sát thực tế.
Song song đó, nhóm vẫn giữ Z-score làm nhánh đối sánh (comparator) để kiểm tra độ nhạy của các cụm sau này.

