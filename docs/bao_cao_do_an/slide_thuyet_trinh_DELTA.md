# TÀI LIỆU NỘI DUNG SLIDE BÁO CÁO THUYẾT TRÌNH BÀN GIAO DỰ ÁN (M1 - M3)
## ĐỀ TÀI: PHÂN CỤM ĐỘNG LƯỢNG VÀ ĐÁNH GIÁ SỨC KHỎE TÀI CHÍNH DOANH NGHIỆP TRÊN THỊ TRƯỜNG CHỨNG KHOÁN VIỆT NAM
### ĐƠN VỊ THỰC HIỆN: TEAM DELTA (361 COMMITS | HOÀN TẤT BÀN GIAO M1 - M2 - M3)

---

### Slide 1: Báo Cáo Bàn Giao Dự Án Toàn Diện M1 - M3: Phân Cụm Động Lượng & Sức Khỏe Tài Chính TTCK Việt Nam
- **Đơn vị thực hiện:** Nhóm nghiên cứu & kỹ thuật DELTA.
- **Phạm vi báo cáo:** Tổng kết và bàn giao trọn vẹn 3 mốc phát triển (Milestones M1 – M2 – M3).
- **Mục tiêu hệ thống:** Xây dựng hệ sinh thái định lượng kết hợp học máy không giám sát (Unsupervised Learning) và dữ liệu tài chính Point-in-Time (PIT) nhằm giải quyết bài toán phân cụm cổ phiếu và kiểm định chiến lược đầu tư thực nghiệm.
- **Đội ngũ dự án (Team DELTA):**

| STT | Họ và tên | Vai trò trong dự án | Đóng góp Git chính |
| :---: | :--- | :--- | :--- |
| 1 | Võ Minh Khôi | Nhóm trưởng | Điều phối chung, chuẩn hóa B-PIT, lõi M3, 4 Notebooks tái lập (106 commits) |
| 2 | Cao Trọng Nguyễn | Nhóm phó | Kiến trúc Crawler, Pipeline C1-C8, Mô hình A v4, Backend & Web (107 commits) |
| 3 | Phan Duy Khánh | Thành viên | Nhánh PCA kết hợp K-Means, Báo cáo đối sánh M3, Tab Đánh giá (50 commits) |
| 4 | Trần Huỳnh Sỹ Đạt | Thành viên | Thu thập dữ liệu M1 Shard 1, Mô hình K-Means Baseline M2 (34 commits) |
| 5 | Trần Minh Tuấn | Thành viên | Thu thập dữ liệu M1 Shard 2, Quét lưới Global K & Audit M2 (32 commits) |
| 6 | Nguyễn Hoàng Phương | Thành viên | Thu thập dữ liệu M1 Shard 3, Nhánh phân cụm Ward Hierarchical (32 commits) |

---

### Slide 2: Bối Cảnh Nghiên Cứu & Hai Câu Hỏi Định Lượng Cốt Lõi
- **Bối cảnh thực tế:** Thị trường chứng khoán Việt Nam biến động mạnh, nhà đầu tư cá nhân chiếm hơn 80% thanh khoản dẫn đến tâm lý bầy đàn và hiện tượng méo mó dữ liệu; các chỉ báo kỹ thuật đơn lẻ thường thất bại.
- **Tiếp cận khoa học:** Kết hợp đồng thời xung lực giá ngắn/trung hạn (Price Momentum) và sức khỏe cơ bản nội tại của doanh nghiệp (Financial Health) trên không gian dữ liệu đa chiều.
- **Hai câu hỏi nghiên cứu định lượng cốt lõi:**
  - **Q1 (Phương pháp luận phân cụm):** *Thuật toán học máy nào phản ánh đúng bản chất cấu trúc thị trường mà không bị chi phối bởi thiên lệch thanh khoản (Liquidity Bias) hay hiện tượng "Silhouette ảo"?*
  - **Q2 (Hiệu quả thực nghiệm đầu tư):** *Chiến lược kết hợp đa nhân tố (Động lượng + Sức khỏe tài chính Point-in-Time) có tạo ra mức sinh lời vượt trội và kiểm soát rủi ro sụt giảm tốt hơn chỉ số thị trường VN-Index qua hai giai đoạn kinh tế khác biệt (2019 – 2023 và 2024 – 2025) hay không?*

---

### Slide 3: Cấu Trúc Ba Mốc Phát Triển Tuần Tự (M1 - M2 - M3)
- Quy trình phát triển dự án được thiết kế theo 3 mốc nghiêm ngặt, chuyển giao dữ liệu khép kín:

| Mốc phát triển | Mục tiêu cốt lõi | Quy mô dữ liệu | Phương pháp chủ đạo | Sản phẩm bàn giao chính |
| :--- | :--- | :--- | :--- | :--- |
| **M1: Nền tảng dữ liệu** | Thu thập toàn diện dữ liệu giá lịch sử & BCTC từ CafeF; đảm bảo nguồn gốc minh bạch, kiểm chứng offline. | 1.522 mã ứng viên (C8 v2), 10 năm giá (2016 - 2025), 1.172 mã BCTC x 10 năm. | Crawler đa luồng có retry/backoff (D-CRAWL-02), chuẩn hóa 9 đặc trưng kỹ thuật & 9 chỉ số BCTC. | Data Lake cục bộ, bộ Registry mã, bảng đặc trưng tháng, mã băm SHA256 từng tệp. |
| **M2: Phân cụm mô hình** | Lựa chọn thuật toán & số cụm tối ưu dựa trên thước đo nội tại; bóc tách và loại bỏ thiên lệch thanh khoản. | 60 snapshot tháng Development (2019 - 2023); không gian 9 đặc trưng kỹ thuật. | Quét lưới 24 cấu hình (K-Means, Ward, GMM, PCA), kiểm toán phương sai tách cụm, chuẩn hóa T1. | Mô hình chính thức A v4 (k=3), mô hình B-PIT tài chính (k=3), quyết định D-DIR-01. |
| **M3: Backtest & Triển khai** | Khóa phương pháp luận, kiểm chứng hiệu quả 5 chiến lược trên Dev & Holdout, đóng gói sản phẩm. | Toàn bộ 84 snapshot tháng (2019 - 2025), chia tách: Dev (59 kỳ LS) & Holdout (23 kỳ LS). | Chu trình tái cơ cấu 4 bước, xếp hạng phân vị 50/50, quản trị an toàn N_min=10. | Báo cáo M3, Dashboard /backtest lên production, bộ 4 Jupyter Notebooks tái lập 100%. |

---

### Slide 4: Các Nguyên Tắc Nghiên Cứu Bất Biến (Research Invariants)
- **Tách biệt độc lập ba tầng đánh giá:** Chất lượng cụm (Cluster Metrics), Tính ổn định chuỗi thời gian (Temporal Stability) và Hiệu quả danh mục (Portfolio Return) là 3 thước đo độc lập tuyệt đối. Cấm chọn mô hình hay số cụm `k` dựa trên tỷ số sinh lời hoặc ROI.
- **Quy chuẩn thước đo Backtest M3:** Hệ thống kiểm định thực nghiệm Development và Holdout đo lường hiệu năng thuần túy qua **4 chỉ số chuẩn tắc: Tổng lợi nhuận lũy kế, Tăng trưởng kép CAGR, Độ biến động năm và Mức sụt giảm tối đa (Max Drawdown)** cùng các ràng buộc thực thi (Tiền mặt, Vòng quay, Vi phạm biên); không đưa tỷ số Sharpe vào các phân đoạn thử nghiệm nhằm triệt tiêu thiên lệch chọn lựa (Selection Bias).
- **Nguyên tắc dữ liệu Point-in-Time (PIT):**
  - Chỉ sử dụng dữ liệu có `available_at <= decision_at`. Tuyệt đối không nhìn trước tương lai (No Look-ahead Bias).
  - Báo cáo tài chính chỉ có hiệu lực kể từ phiên giao dịch kế tiếp sau ngày công bố thông tin (`usable_from_date`).
- **Phòng chống thiên lệch sống sót (Survivorship Bias):** Giữ nguyên các mã hủy niêm yết, ngừng giao dịch trong lịch sử; xác thực thực thể theo khoảng thời gian thực tế `security_id`.
- **Bảo toàn dữ liệu gốc:** Không forward-fill giá thiếu, không biến giá trị rỗng thành zero, không trộn lẫn giá điều chỉnh và giá thô trong tính toán khối lượng/giá trị.
- **Tính bất biến của Artifact:** Mọi artifact dữ liệu thô, trung gian và kết quả thực nghiệm đều được niêm phong mật mã học bằng SHA256, không thể sửa đổi hồi tố.

---

### Slide 5: Chiến Dịch Thu Thập Dữ Liệu Quy Mô Lớn & Phễu Kiểm Soát Chất Lượng
- Tiến trình mở rộng tập mẫu qua 5 chiến dịch thu thập độc lập từ CafeF:

| Chiến dịch | Quy mô ứng viên | Thời gian lịch sử | Snapshot tháng | Đặc điểm kỹ thuật & Kết quả đạt được |
| :--- | :---: | :---: | :---: | :--- |
| **Pilot KBS** | 55 mã | 2023 - 2024 | 15 tháng | Thử nghiệm ban đầu; phát hiện thiếu hụt lịch sử và bất đồng bộ API. |
| **C5 (CafeF)** | 500 mã | 2021 - 2024 | 36 tháng | Thu thập bước đầu trên CafeF, kiểm chứng cơ chế chống nghẽn mạng. |
| **C7 (CafeF)** | 952 mã | 2021 - 2024 | 36 tháng | Mở rộng độ phủ toàn bộ cổ phiếu giao dịch trên cả 3 sàn (HOSE, HNX, UPCoM). |
| **C8 v1** | 952 mã | 2021 - 2024 | 36 tháng | Hoàn thiện phễu lọc chất lượng: 922 mã đủ đặc trưng, 905 mã đạt chuẩn sẵn sàng. |
| **C8 v2 (Chính thức)** | **1.522 mã** | **2016 - 2025 (10 năm)** | **84 tháng** | **Mở rộng tối đa: 1.410 mã market-ready tại 31/12/2025; phục vụ chính thức M2 v2 và M3.** |

- **Phễu kiểm soát chất lượng 3 cấp độ:**
  1. *Candidate Universe:* Toàn bộ 1.522 mã có phát sinh niêm yết/giao dịch.
  2. *Feature Eligible:* Tối thiểu 252 phiên giao dịch quan sát liên tục (~1 năm) để tính đủ cửa sổ đặc trưng dài hạn.
  3. *Market Ready:* Loại trừ cổ phiếu kiểm soát đặc biệt, không phát sinh giao dịch trong 21 phiên gần nhất, vi phạm tính toàn vẹn dữ liệu.

---

### Slide 6: Nhận Diện & Xử Lý Hai Lỗ Hổng Dữ Liệu Từ Nhà Cung Cấp
- Quá trình kiểm toán dữ liệu chuyên sâu đã phát hiện và xử lý triệt để 2 lỗi hệ thống nghiêm trọng từ nguồn cung cấp dữ liệu:
- **Lỗ hổng 1: Sai lệch bước nhảy giá do chia thưởng cổ tức bằng cổ phiếu (Split/Bonus Inconsistency):**
  - *Hiện tượng:* Giá thô (Raw Close) sụt giảm mạnh trong ngày giao dịch không hưởng quyền nhưng khối lượng không điều chỉnh tương ứng, gây sai lệch đột biến ở chuỗi lợi suất thô.
  - *Giải pháp:* Tách biệt triệt để hai cơ sở giá: Tính toán toàn bộ các biến động động lượng, độ biến động và sụt giảm trên **Giá đóng cửa điều chỉnh (Adjusted Close)**; tính thanh khoản và giá trị vốn hóa dựa trên **Giá đóng cửa thô kết hợp Khối lượng thực tế**.
- **Lỗ hổng 2: Trùng lặp ngày công bố thông tin BCTC (CreateDate Timestamp Collision):**
  - *Hiện tượng:* Nhiều doanh nghiệp nộp nhiều báo cáo giải trình hoặc BCTC sửa đổi trong cùng một ngày, hoặc CafeF trả về ngày công bố dạng DATE_ONLY (không kèm giờ/phút).
  - *Giải pháp:* Ban hành quy tắc xử lý PIT bảo thủ (Conservative Point-in-Time Policy): Chỉ kích hoạt hiệu lực thông tin vào **phiên giao dịch T+1 kế tiếp** sau ngày ghi nhận `CreateDate`; trong trường hợp trùng lặp, ưu tiên phiên bản báo cáo kiểm toán có xác thực đầy đủ nhất.

---

### Slide 7: Bộ 9 Đặc Trưng Kỹ Thuật Phân Tích Động Lượng & Rủi Ro Giá
- Hệ thống 9 đặc trưng kỹ thuật chuẩn hóa phản ánh toàn diện hành vi giá, xung lực động lượng và rủi ro:

| Đặc trưng | Công thức tính toán | Cửa sổ quan sát | Độ phủ dữ liệu | Ý nghĩa kinh tế & Phân tích định lượng |
| :--- | :--- | :---: | :---: | :--- |
| `mom_21` | $\ln(P_t / P_{t-21})$ | 21 phiên (~1 tháng) | 99,7% | Xung lực giá ngắn hạn, phản ánh phản ứng tức thời của dòng tiền. |
| `mom_63` | $\ln(P_t / P_{t-63})$ | 63 phiên (~3 tháng) | 99,4% | Động lượng giá trung hạn quý, đo lường sự tích lũy xu hướng. |
| `mom_126` | $\ln(P_t / P_{t-126})$ | 126 phiên (~6 tháng) | 98,5% | **Đặc trưng phân tách chủ đạo:** Đo lường sức mạnh xu hướng 2 quý. |
| `mom_252` | $\ln(P_t / P_{t-252})$ | 252 phiên (~1 năm) | 96,8% | Động lượng dài hạn hàng năm, lọc bỏ nhiễu động chu kỳ ngắn. |
| `vol_63` | $\text{std}(r_{\text{daily}}, 63) \times \sqrt{252}$ | 63 phiên (~3 tháng) | 99,4% | Rủi ro biến động toàn phần, chuẩn hóa theo năm. |
| `downside_vol_63`| $\text{std}(\min(r_{\text{daily}}, 0), 63) \times \sqrt{252}$ | 63 phiên (~3 tháng) | 99,4% | Biến động chiều giảm; chỉ phạt phiên giảm giá, không phạt phiên tăng giá. |
| `mdd_126` | $\min((P_t - \text{Peak}_{126}) / \text{Peak}_{126})$ | 126 phiên (~6 tháng) | 98,5% | Mức sụt giảm tối đa từ đỉnh, phản ánh rủi ro đu đỉnh trong 6 tháng. |
| `beta_126` | $\text{Cov}(r_i, r_{\text{VNI}}) / \text{Var}(r_{\text{VNI}})$ | 126 phiên (~6 tháng) | 98,5% | Độ nhạy hệ thống so với chỉ số thị trường chung VN-Index. |
| `liquidity_21` | $\ln(\text{mean}(\text{Volume} \times \text{Close}, 21))$ | 21 phiên (~1 tháng) | 99,7% | Quy mô thanh khoản logarit trung bình 1 tháng gần nhất. |

---

### Slide 8: Nền Tảng Dữ Liệu BCTC & Hệ Thống 9 Chỉ Số Tài Chính Cốt Lõi
- Xử lý 1.172 mã doanh nghiệp trong 10 năm liên tục (2016 – 2025).
- Bộ 9 chỉ số sức khỏe tài chính cốt lõi (Indicators v1) được tính toán theo chuẩn phân tích báo cáo tài chính quốc tế:
  - **Nhóm Khả năng sinh lời (Profitability):**
    - $ROE = \frac{\text{Lợi nhuận sau thuế}}{\text{Vốn chủ sở hữu}}$ (Hiệu quả sử dụng vốn chủ sở hữu).
    - $ROA = \frac{\text{Lợi nhuận sau thuế}}{\text{Tổng tài sản}}$ (Hiệu quả sinh lời trên tổng tài sản).
    - Biên lợi nhuận gộp (Gross Margin) & Biên lợi nhuận ròng (Net Margin).
  - **Nhóm Đòn bẩy & Rủi ro tài chính (Leverage & Solvency):**
    - $D/E = \frac{\text{Tổng nợ phải trả}}{\text{Vốn chủ sở hữu}}$ (Tỷ lệ đòn bẩy tài chính).
    - Khả năng thanh toán hiện hành (Current Ratio) $= \frac{\text{Tài sản ngắn hạn}}{\text{Nợ ngắn hạn}}$.
  - **Nhóm Tăng trưởng & Hiệu quả hoạt động (Growth & Turnover):**
    - Tăng trưởng doanh thu thuần (Revenue Growth YoY).
    - Tăng trưởng lợi nhuận sau thuế (Net Income Growth YoY).
    - Vòng quay tài sản (Asset Turnover) $= \frac{\text{Doanh thu thuần}}{\text{Tổng tài sản bình quân}}$.

---

### Slide 9: Cơ Chế Point-In-Time (PIT) & Quản Lý Thời Hạn Hiệu Lực Của BCTC
- **Cơ chế kích hoạt thời điểm có hiệu lực:**
  - Không sử dụng ngày kết thúc niên độ kế toán (31/12) làm mốc khả dụng.
  - Sử dụng ngày công bố chính thức trên cổng CafeF (`CreateDate`).
  - Điểm quyết định khả dụng: $T_{\text{usable}} = \text{Phiên giao dịch đầu tiên sau } T_{\text{announcement}}$.
- **Quy tắc thời hạn hiệu lực tối đa 18 tháng (18-Month Stale Rule):**
  - Báo cáo tài chính năm chỉ có giá trị hiệu lực tối đa 18 tháng kể từ ngày kết thúc năm tài chính.
  - Nếu sau 18 tháng doanh nghiệp không công bố BCTC mới, hồ sơ tài chính bị đánh dấu `EXPIRED/STALE` và tự động bị loại khỏi danh mục đầu tư.
- **Phân tách trạng thái hồ sơ tại mốc Cutoff hàng năm:**

| Trạng thái hồ sơ | Điều kiện xác định theo thời gian Point-in-Time | Xử lý trong phân cụm & đầu tư |
| :--- | :--- | :--- |
| **FIT** | Đã công bố BCTC năm $N$ hợp lệ trước mốc Cutoff kiểm định. | Sử dụng để huấn luyện mô hình phân cụm B-PIT. |
| **ASSIGNED** | Chưa có BCTC năm $N$ tại mốc Cutoff, nhưng BCTC năm $N-1$ còn hiệu lực (< 18 tháng). | Giữ nguyên nhãn phân cụm từ kỳ trước, cho phép duy trì vị thế. |
| **EXPIRED** | Quá 18 tháng không có BCTC mới được công bố. | Loại bỏ hoàn toàn khỏi vũ trụ đầu tư. |

---

### Slide 10: Thử Nghiệm Lưới 24 Cấu Hình Phân Cụm & Bộ 5 Thước Đo Nội Tại
- Quét lưới 24 cấu hình độc lập trên không gian 9 đặc trưng:
  - Thuật toán: K-Means, Ward Hierarchical, Gaussian Mixture Models (GMM), PCA kết hợp K-Means.
  - Số cụm khảo nghiệm: $k \in \{2, 3, 4, 5\}$.
  - Tiền xử lý: RobustScaler, StandardScaler, MinMax, Log-transform thanh khoản.
- **Hệ thống 5 thước đo nội tại độc lập:**
  1. *Silhouette Index ($s$):* Đo lường độ gắn kết nội cụm và phân tách ngoại cụm.
  2. *Davies-Bouldin Index ($DB$):* Đo mức độ tương đồng giữa các cụm (càng thấp càng tốt).
  3. *Calinski-Harabasz Index ($CH$):* Tỷ số phương sai phân tán giữa các cụm so với trong cụm.
  4. *Tỷ lệ phân tách phương sai (Variance Decomposition):* Tỷ lệ đóng góp của từng nhóm đặc trưng vào khoảng cách cụm.
  5. *Độ ổn định nhãn thời gian (Adjusted Rand Index - ARI):* Đo lường tính nhất quán nhãn cụm qua 60 snapshot tháng liên tiếp.

---

### Slide 11: Bằng Chứng Đối Chứng: Bóc Tách Hiện Tượng "Silhouette Cao Giả"
- **Phát hiện bước ngoặt (D-DIR-01):** Mô hình cũ M2 (K=2) đạt Silhouette rất cao nhưng là kết quả ảo do bị biến thanh khoản lấn át hoàn toàn!
- Bảng so sánh thực nghiệm chuyên sâu giữa mô hình cũ (K=2) và mô hình chính thức A v4 (k=3):

| Thước đo đánh giá phương pháp luận | Mô hình M2 K=2 (Cũ - Bị loại bỏ) | Mô hình A v4 k=3 (Chính thức được duyệt) | Đánh giá khoa học & Ý nghĩa thực tiễn |
| :--- | :---: | :---: | :--- |
| **Tỷ lệ số mã cụm nhỏ nhất (trung vị)** | 3,7% số mã | **14,0% số mã** | A v4 đảm bảo kích cỡ cụm đủ lớn cho thực thi danh mục. |
| **Số tháng cụm nhỏ vi phạm ngưỡng < 5%** | **48 / 60 tháng** | **2 / 60 tháng** | K=2 gần như liên tục tạo ra "cụm rác" vô nghĩa. |
| **Tỷ trọng phân tách do Thanh khoản** | **63%** | **8%** | K=2 bị thanh khoản lấn át hoàn toàn, che mờ động lượng. |
| **Tỷ trọng phân tách do Động lượng** | **7%** | **54%** | **A v4 bóc tách thành công xung lực động lượng cốt lõi.** |
| **Silhouette Index (trong không gian log chuẩn)** | 0,114 | **0,240** | A v4 vượt trội về độ cô đặc cụm thực chất. |
| **Độ ổn định nhãn ARI giữa 2 tháng liền nhau** | 0,74 | 0,55 | K=2 ổn định cao vì thanh khoản ít thay đổi, nhưng mất giá trị dự báo. |

---

### Slide 12: Mô Hình Thị Trường A v4: Định Danh & Hồ Sơ Kinh Tế 3 Cụm Động Lượng
- Mô hình A v4 (K-Means, $k=3$) phân tách thị trường thành 3 trạng thái động lượng rõ rệt:

| Cụm định danh | Quy mô mã thanh khoản (31/12/2025) | Đặc điểm định lượng & Giá trị trung vị | Ý nghĩa kinh tế & Định hướng đầu tư |
| :--- | :---: | :--- | :--- |
| **Dẫn dắt (Leading)** | **96 mã** | $mom\_126 \approx +0,526$ (đà tăng 6 tháng rất mạnh); thanh khoản cao; sụt giảm nông ($MDD$ thấp). | Cổ phiếu dẫn dắt xu hướng thị trường, dòng tiền chủ động tích cực; **đối tượng mua mục tiêu của chiến lược.** |
| **Trung bình (Neutral)** | **413 mã** | Động lượng trung bình, biến động giá thấp, dao động quanh xu hướng chung của VN-Index. | Đại diện cho phần lớn cổ phiếu ở pha tích lũy hoặc đi ngang; không ưu tiên giải ngân. |
| **Tụt hậu / Beta cao (Laggards)** | **280 mã** | Đà tăng âm, sụt giảm sâu từ đỉnh, độ nhạy rủi ro cao với biến động giảm của thị trường. | Cổ phiếu suy thoái, dòng tiền rút lui mạnh; **bộ lọc loại trừ bắt buộc phải tránh.** |

- Cơ chế gán nhãn chuỗi thời gian: Cố định tâm cụm qua thuật toán Matching Hungary đảm bảo không bị đảo lộn nhãn giữa các tháng.

---

### Slide 13: Mô Hình Phân Cụm Tài Chính B-PIT: Kiến Trúc Point-In-Time & Cổng Đóng Băng
- **Thiết kế kiến trúc B-PIT (ADR D-M3-01):**
  - Khắc phục triệt để rủi ro nhìn trước tương lai (Look-ahead bias) của mô hình B v4 cũ.
  - Sử dụng thuật toán K-Means ($k=3$) trên không gian 9 chỉ số tài chính chuẩn hóa T1 (loại bỏ ngoại lai bằng ngưỡng phân vị 1% - 99%).
- **Ba trụ cột thiết kế kiến trúc Point-in-Time:**
  1. *Cổng đóng băng Cutoff:* Mỗi năm tài chính $t$ chỉ huấn luyện trên các BCTC có `usable_from_date` $\le \text{Cutoff}(t)$ ($\text{Cutoff} = \max(\text{ngày 30/04 năm } t+1, \text{ngày usable sớm nhất})$).
  2. *Đóng băng tham số vĩnh viễn:* Tọa độ tâm cụm, độ lệch chuẩn, trung vị và thứ tự cụm được khóa cứng tại mốc Cutoff.
  3. *Cơ chế gán nhãn đến muộn (Late Filers):* BCTC công bố sau Cutoff chỉ được chiếu (ASSIGNED) vào tâm cụm đóng băng gần nhất.
- **Kiểm toán dữ liệu và rò rỉ thông tin:**
  - Kết quả kiểm tra rò rỉ tương lai (Fit-Leak Test): **Fit-leak = 0 tuyệt đối trên toàn bộ 9 năm lịch sử (mã băm `bpit-4a9d2e87f0de84ec`).**

---

### Slide 14: Mô Hình Tài Chính B-PIT: Định Danh & Hồ Sơ Kinh Tế 3 Cụm Sức Khỏe Doanh Nghiệp
- Mô hình B-PIT ($k=3$) phân tách toàn diện các doanh nghiệp niêm yết thành 3 cụm sức khỏe tài chính đặc trưng:

| Cụm định danh | Quy mô mã (FY2023) | Đặc điểm định lượng & Giá trị trung vị nổi bật | Ý nghĩa kinh tế & Ứng dụng đầu tư |
| :--- | :---: | :--- | :--- |
| **Cụm 1: Nền tảng vàng / Chất lượng cao (Healthy / Bluechips)** | **212 mã** (21,8%) | • $\text{ROE}_{\text{median}} \approx 19,23\%$ (vượt trội toàn thị trường, $z = +1,15$)<br>• Biên lợi nhuận gộp & ròng cao ($z = +1,08$ & $+1,15$)<br>• Đòn bẩy nợ rất an toàn: $(D/E)_{\text{median}} \approx 0,37$<br>• Thanh toán hiện hành: $CR > 1,5$ ($z = +0,40$) | Doanh nghiệp đầu ngành, bảng cân đối kế toán lành mạnh, dòng tiền dồi dào, khả năng tự tài trợ cao.<br>👉 **Trọng tâm giải ngân số 1 của chiến lược.** |
| **Cụm 2: Thâm dụng nợ / Đòn bẩy cao (High Leverage / Expansion)** | **133 mã** (13,7%) | • Đòn bẩy nợ vay rất lớn: $(D/E)_{\text{median}} \approx 3,57$ ($z = +1,64$)<br>• Vòng quay tài sản rất cao ($z = +1,23$), tăng trưởng DT cao ($z = +0,45$)<br>• Nhưng $\text{ROE}_{\text{median}} \approx 6,71\%$, ROA thấp ($z = -0,53$)<br>• Biên lãi mỏng ($z = -0,50$), thanh toán yếu ($z = -0,41$) | Doanh nghiệp thâm dụng vốn, vay nợ quy mô lớn để tài trợ doanh thu (xây dựng, hạ tầng, thương mại).<br>👉 Tiềm ẩn rủi ro thanh khoản cao khi lãi suất tăng. |
| **Cụm 0: Trung bình thấp / Trì trệ (Moderate-Low / Stagnant)** | **627 mã** (64,5%) | • $\text{ROE}_{\text{median}} \approx 5,64\%$ (thấp, $z = -0,39$)<br>• ROA thấp ($z = -0,35$), biên lợi nhuận mỏng<br>• Tăng trưởng doanh thu suy giảm ($z = -0,12$)<br>• Đòn bẩy nợ trung bình: $(D/E)_{\text{median}} \approx 0,83$ | Nhóm chiếm đa số doanh nghiệp vừa và nhỏ, kinh doanh đi ngang hoặc hiệu quả sinh lời trên vốn kém.<br>👉 **Bị bộ lọc loại trừ hoặc giảm mạnh tỷ trọng.** |

- **Quy tắc định vị và thứ tự ưu tiên (Tie-breaking Rule):**
  - Các cụm được sắp xếp nhất quán theo thứ tự ưu tiên: **ROE trung vị giảm dần; nếu hòa thì Nợ/VCSH ($D/E$) trung vị tăng dần** (Ưu tiên hiệu quả sinh lời và an toàn vốn).
  - Bộ lọc chiến lược áp dụng nguyên tắc `financial_rule = not_weakest`: Giữ lại Cụm 1 và Cụm 2 (khi có động lượng bổ trợ), loại bỏ dứt điểm Cụm 0 suy thoái.

---

### Slide 15: Mô Hình B-PIT Enriched: Làm Giàu Dữ Liệu Tài Chính Theo Ngành
- **Hạn chế của dữ liệu tài chính gốc:** Các ngành kinh doanh có cấu trúc tài chính rất khác biệt (ví dụ: Ngân hàng - Chứng khoán có đòn bẩy tự nhiên cao, Bất động sản có chu kỳ ghi nhận doanh thu dài) dẫn đến phân cụm bị lệch theo nhóm ngành.
- **Phương pháp làm giàu dữ liệu (B-PIT Enriched):**
  - Chuẩn hóa chỉ số tài chính theo độ lệch chuẩn tương đối so với trung vị ngành cấp 2 (Industry-Relative Z-Score).
  - Điền giá trị trung vị ngành tại mốc Cutoff cho 1.045 lượt doanh nghiệp (1.111 ô giá trị trên 9 chỉ số), bảo đảm 0 rò rỉ thông tin tương lai.
- **Kết quả cải thiện mô hình:**
  - Phân bổ số lượng mã giữa các cụm trở nên đồng đều và phản ánh đúng vị thế cạnh tranh thực sự của doanh nghiệp trong từng ngành.
  - Tạo tiền đề cho sự bứt phá vượt bậc về hiệu suất đầu tư trong giai đoạn Backtest M3.

---

### Slide 16: Hệ Thống 5 Chiến Lược Đầu Tư Thực Nghiệm & Benchmark Thị Trường
- Thiết kế hệ thống 5 chiến lược thực nghiệm có kiểm soát nhằm phân rã chính xác nguồn gốc sinh lời:

| Chiến lược đầu tư | Quy tắc lựa chọn danh mục | Mục đích nghiên cứu & Câu hỏi đối chứng |
| :--- | :--- | :--- |
| **1. Chiến lược Kết hợp (Combined)** | Giao thoa giữa Cụm Dẫn dắt (Market A v4) và Cụm Tài chính tốt (B-PIT). | Kiểm chứng giả thuyết: *Kết hợp Động lượng + Sức khỏe tài chính mang lại hiệu quả vượt trội.* |
| **2. Thuần thị trường (Market-only)** | Chỉ chọn cổ phiếu thuộc Cụm Dẫn dắt (Leading) của mô hình thị trường A v4. | Đo lường hiệu quả độc lập của tín hiệu động lượng giá và thanh khoản. |
| **3. Thuần tài chính (Financial-only)** | Chỉ chọn cổ phiếu thuộc Cụm Tài chính tốt của mô hình B-PIT. | Đo lường hiệu quả độc lập của tín hiệu cơ bản doanh nghiệp; vai trò phòng thủ. |
| **4. Thuần động lượng (Momentum-only)** | Xếp hạng toàn bộ thị trường theo chỉ số động lượng, lấy Top 30% dẫn đầu. | Đối chứng: *Phân cụm học máy có tốt hơn phương pháp xếp hạng động lượng truyền thống?* |
| **5. Cân bằng toàn TT (Equal-weight)** | Mua đều tất cả cổ phiếu đủ điều kiện giao dịch trên thị trường. | Đại diện cho mức sinh lời trung bình toàn diện của thị trường mở rộng. |
| **Chỉ số tham chiếu VN-Index** | Mua và nắm giữ rổ chỉ số vốn hóa thị trường chung (Market-Cap Weighted). | Thước đo chuẩn mực của thị trường chứng khoán Việt Nam. |

---

### Slide 17: Bộ Lọc Loại Trừ, Xếp Hạng Đa Nhân Tố & Quản Trị Danh Mục
- **Bộ lọc loại trừ 3 lớp:**
  1. Loại trừ cổ phiếu nằm ngoài giao thoa giữa 2 cụm mục tiêu.
  2. Loại trừ cổ phiếu có thanh khoản bình quân 21 phiên dưới ngưỡng tối thiểu (giá trị GD < 1 tỷ VNĐ/phiên).
  3. Loại trừ cổ phiếu có BCTC quá hạn hiệu lực 18 tháng hoặc đang bị diện đình chỉ giao dịch.
- **Hệ thống xếp hạng đa nhân tố phân vị 50/50:**
  $$\text{Score}_{\text{composite}} = 0,5 \times \text{Percentile}(\text{Momentum Score}) + 0,5 \times \text{Percentile}(\text{Financial Score})$$
- **Quy tắc phân bổ tỷ trọng:**
  - Lựa chọn danh mục **Top 30%** mã có điểm số tổng hợp cao nhất.
  - Phân bổ tỷ trọng bằng nhau (Equal Weighting) trên toàn bộ danh mục lựa chọn.
- **Ngưỡng an toàn bảo vệ vốn tối thiểu:**
  - Thiết lập ngưỡng $N_{\min} = 10$ mã.
  - Nếu số mã đạt chuẩn $< 10$, hệ thống kích hoạt cơ chế phòng vệ rủi ro: Giữ tỷ trọng tiền mặt tương ứng, hạn chế tối đa rủi ro tập trung.

---

### Slide 18: Kiến Trúc Hệ Thống Thực Thi Mô Phỏng Giao Dịch 4 Bước
- Chu trình mô phỏng giao dịch thực tế hàng tháng được chia thành 4 bước khép kín:

| Bước thực thi | Thời điểm thực hiện | Hành động chi tiết của hệ thống | Quy tắc kiểm soát rủi ro đi kèm |
| :---: | :--- | :--- | :--- |
| **1. Chọn (Select)** | Cuối ngày làm việc cuối cùng của tháng ($T$) | Lọc vũ trụ ứng viên hợp lệ, tính điểm phân vị đa nhân tố, xác định danh sách Top 30%. | Kiểm tra ngưỡng an toàn $N_{\min} \ge 10$; kích hoạt giữ tiền mặt nếu thiếu ứng viên. |
| **2. Tái cơ cấu (Rebalance)** | Phiên giao dịch đầu tiên của tháng kế tiếp ($T+1$) | Khớp lệnh theo giá đóng cửa điều chỉnh (`adj_close`). **Luôn bán trước, mua sau.** | Chặn mua nếu giá kịch trần; chặn bán nếu giá kịch sàn; chặn nếu khối lượng = 0. |
| **3. Nắm giữ (Hold)** | Toàn bộ chu kỳ tháng giao dịch | Duy trì trạng thái danh mục, ghi nhận NAV hàng ngày. | Hạch toán đầy đủ quyền cổ tức tiền mặt, cổ phiếu thưởng và quyền mua. |
| **4. Chuyển kỳ (Roll)** | Phiên cuối cùng của chu kỳ tháng | Quyết toán lãi/lỗ thực tế, khấu trừ chi phí, chuyển trạng thái NAV sang chu kỳ mới. | Tách biệt tuyệt đối trạng thái giữa hai kỳ kế tiếp; hỗ trợ vị thế phân số. |

---

### Slide 19: Cơ Chế Kiểm Soát Lỗi & Xử Lý Ràng Buộc Giao Dịch Biên
- Mô phỏng giao dịch biên phản ánh chân thực các rủi ro vận hành trên sàn chứng khoán Việt Nam:
  - **Quy tắc Bán trước - Mua sau:** Giải phóng nguồn vốn khả dụng trước khi tiến hành giải ngân lệnh mua mới.
  - **Xử lý giá trần/sàn biên:**
    - Cổ phiếu mục tiêu chạm giá trần (Ceiling Price) ở phiên $T+1$: Chặn giải ngân (`BUY_FAILED`), bảo toàn tiền mặt.
    - Cổ phiếu cần bán chạm giá sàn (Floor Price) mất thanh khoản: Chặn lệnh bán (`SELL_FAILED`), buộc giữ tiếp vị thế.
- **Thống kê chi tiết các sự kiện giao dịch biên ghi nhận trong thực nghiệm:**

| Giai đoạn kiểm thử | Số kỳ thực nghiệm | BUY_FAILED (Trần / Vol = 0) | SELL_FAILED (Sàn / Vol = 0) | SCALED (Cắt giảm tỷ trọng) | PRICE_STALE (Cảnh báo giá cũ) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Development (2019 - 2023)** | 59 kỳ tháng | 12 lượt | 6 lượt | 0 lượt | 0 lượt |
| **Holdout (2024 - 2025)** | 23 kỳ tháng | 3 lượt | 1 lượt | 0 lượt | 0 lượt |

---

### Slide 20: Kết Quả Thực Nghiệm Giai Đoạn Phát Triển (Development 2019 - 2023)
- Giai đoạn kiểm định phát triển (In-Sample) bao gồm 59 kỳ tháng liên tục, trải qua trọn vẹn cả chu kỳ bùng nổ (2020 – 2021) và chu kỳ sụt giảm sâu (2022).
- Bảng đối sánh trực tiếp 4 thước đo chuẩn tắc giữa Chiến lược Kết hợp (Combined) và VN-Index:

| Tiêu chí đánh giá định lượng | Chiến lược Kết hợp (Combined Base) | Chỉ số tham chiếu VN-Index | Đánh giá so sánh thực nghiệm |
| :--- | :---: | :---: | :--- |
| **Tổng lợi nhuận lũy kế** | **116,15%** | **24,35%** | **Vượt trội +91,80 pp** |
| **Tỷ lệ tăng trưởng kép (CAGR)** | **16,97% / năm** | **4,53% / năm** | **Gấp 3,75 lần thị trường (+12,44 pp/năm)** |
| **Độ biến động hàng năm (Annual Vol)** | 27,39% | 23,56% | Cao hơn +3,83 pp do biến động nhóm Mid/Small |
| **Mức sụt giảm tối đa (Max Drawdown)** | -44,60% | -33,02% | Sụt giảm sâu hơn -11,58 pp trong cú sập 2022 |
| **Tỷ trọng tiền mặt nhàn rỗi (Avg Cash)** | **22,40%** | **0,00%** | Phòng hộ tự động khi danh mục không đủ 10 mã |

- *Nhận xét cốt lõi:* Về lợi nhuận, Combined tạo ra mức tăng trưởng vượt bậc so với VN-Index; tuy nhiên mức biến động và độ sụt giảm tối đa lớn hơn (-44,60% so với -33,02%) cho thấy chiến lược chấp nhận đánh đổi rủi ro để tối đa hóa xung lực giá.

---

### Slide 21: Kết Quả Thực Nghiệm Giai Đoạn Ngoài Mẫu (Holdout 2024 - 2025)
- Giai đoạn thử thách ngoài mẫu nghiêm ngặt (Out-of-Sample) bao gồm 23 kỳ tháng; đặc trưng bởi sự dẫn dắt mạnh mẽ của nhóm cổ phiếu vốn hóa lớn (Large-Cap / Ngân hàng trụ).
- Bảng đối chứng định lượng trong giai đoạn Holdout:

| Tiêu chí đánh giá định lượng | Chiến lược Kết hợp (Combined Base) | Chỉ số tham chiếu VN-Index | Đánh giá so sánh thực nghiệm |
| :--- | :---: | :---: | :--- |
| **Tổng lợi nhuận lũy kế** | **38,95%** | **52,13%** | Thấp hơn -13,18 pp |
| **Tỷ lệ tăng trưởng kép (CAGR)** | **18,72% / năm** | **24,47% / năm** | Thấp hơn -5,75 pp / năm |
| **Độ biến động hàng năm (Annual Vol)** | 28,59% | 16,08% | Biến động lớn hơn do không dồn tỷ trọng vào nhóm trụ |
| **Mức sụt giảm tối đa (Max Drawdown)** | -26,27% | -5,87% | Sụt giảm sâu hơn -20,40 pp |
| **Tỷ trọng tiền mặt nhàn rỗi (Avg Cash)** | **8,92%** | **0,00%** | Tỷ lệ hấp thụ vốn cao hơn giai đoạn Dev |

- *Bản chất kỹ thuật:* Năm 2024 – 2025 là giai đoạn thị trường tăng điểm tập trung cục bộ vào số ít mã trụ lớn kéo chỉ số VN-Index (chỉ số bình quân vốn hóa). Danh mục Equal-weight không chịu rủi ro vốn hóa trụ nên có độ biến động cao hơn, tuy nhiên mức CAGR 18,72% vẫn là mức sinh lời tuyệt đối rất hấp dẫn.

---

### Slide 22: Bảng Đối Chứng Toàn Diện 5 Chiến Lược Thực Nghiệm (Dev & Holdout)
- Bảng tổng hợp đầy đủ các thước đo hiệu năng và thực thi ghi nhận chính thức từ hệ thống Backtest M3:

| Phân đoạn thời gian | Chiến lược đầu tư | Lợi nhuận lũy kế | Tăng trưởng CAGR | Độ biến động năm | Max Drawdown | Tiền mặt nhàn rỗi |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Phát triển (2019 - 2023)** | **Combined (Dữ liệu gốc)** | **116,15%** | **16,97%** | **27,39%** | **-44,60%** | **22,40%** |
| (59 kỳ tháng) | Thuần tài chính (Financial-only) | 40,74% | 7,20% | 17,09% | -27,20% | 1,02% |
| | Thuần thị trường (Market-only) | 128,81% | 18,34% | 29,51% | -47,88% | 6,22% |
| | Thuần động lượng (Momentum-only) | 169,73% | 22,36% | 25,51% | -33,71% | 1,47% |
| | Cân bằng toàn TT (Equal-weight) | 159,03% | 21,36% | 24,45% | -37,01% | 0,48% |
| | **VN-Index (Benchmark)** | **24,35%** | **4,53%** | **23,56%** | **-33,02%** | **0,00%** |
| **Ngoài mẫu (2024 - 2025)** | **Combined (Dữ liệu gốc)** | **38,95%** | **18,72%** | **28,59%** | **-26,27%** | **8,92%** |
| (23 kỳ tháng) | Thuần tài chính (Financial-only) | 28,37% | 13,92% | **7,30%** | **-3,95%** | 2,54% |
| | Thuần thị trường (Market-only) | 22,43% | 11,14% | 23,75% | -18,91% | 3,75% |
| | Thuần động lượng (Momentum-only) | 41,37% | 19,80% | 15,60% | -8,92% | 0,82% |
| | Cân bằng toàn TT (Equal-weight) | 29,53% | 14,45% | 13,34% | -7,40% | 0,47% |
| | **VN-Index (Benchmark)** | **52,13%** | **24,47%** | **16,08%** | **-5,87%** | **0,00%** |

- **Nhận xét đối chứng định lượng then chốt:**
  - *Tính chất phòng thủ của Financial-only:* Đạt mức sụt giảm thấp kỷ lục (-3,95% ở Holdout và -27,20% ở Dev) và biến động cực thấp (7,30%), chứng minh năng lực kiểm soát rủi ro phòng thủ vượt trội.
  - *Xung lực của Market-only:* Mang lại tỷ suất sinh lời cao trong thị trường tăng giá nhưng chịu biến động lớn nhất (29,51%) và sụt giảm sâu nhất (-47,88%).
  - *Combined:* Đóng vai trò cân bằng giữa hai thái cực, kiểm soát tốt rủi ro nhờ bộ đệm tiền mặt nhàn rỗi (22,40% ở Dev và 8,92% ở Holdout) khi thị trường khan hiếm cổ phiếu thỏa mãn cả 2 tiêu chí.

---

### Slide 23: Phân Tích Chuyên Sâu: Bước Đột Phá Từ Dữ Liệu Tài Chính Làm Giàu
- Đối chứng thực nghiệm giữa **Chiến lược Kết hợp trên Dữ liệu làm giàu (Combined Enriched)** và **Dữ liệu gốc (Base)**:

| Phân đoạn kiểm định | Chỉ số đo lường hiệu năng & thực thi | Combined (Dữ liệu gốc) | Combined (Dữ liệu làm giàu) | Hiệu quả cải thiện đột phá |
| :--- | :--- | :---: | :---: | :---: |
| **Giai đoạn Phát triển** | **Lợi nhuận lũy kế** | 116,15% | **151,67%** | **+35,51 pp** |
| **(2019 - 2023)** | **Tăng trưởng kép CAGR** | 16,97% | **20,65%** | **+3,68 pp / năm** |
| | **Độ biến động hàng năm (Annual Vol)** | 27,39% | **24,45%** | **Giảm 2,94 pp biến động rủi ro** |
| | **Mức sụt giảm tối đa (Max Drawdown)** | -44,60% | **-44,45%** | Giảm thiểu rủi ro sụt giảm |
| | **Tỷ trọng tiền mặt nhàn rỗi bình quân**| 22,40% | **16,85%** | **-5,55 pp (Giải phóng dòng tiền ứ đọng)** |
| **Giai đoạn Ngoài mẫu** | **Lợi nhuận lũy kế** | 38,95% | **53,07%** | **+14,12 pp** |
| **(2024 - 2025)** | **Tăng trưởng kép CAGR** | 18,72% | **24,87%** | **+6,15 pp / năm (Vượt VN-Index 24,47%)** |
| | **Độ biến động hàng năm (Annual Vol)** | 28,59% | **27,80%** | **Giảm 0,79 pp biến động** |
| | **Mức sụt giảm tối đa (Max Drawdown)** | -26,27% | **-22,55%** | **Giảm 3,72 pp rủi ro sụt giảm** |
| | **Tỷ trọng tiền mặt nhàn rỗi bình quân**| 8,92% | **9,22%** | Duy trì an toàn vốn |

- *Ý nghĩa then chốt:* Việc chuẩn hóa tương đối theo ngành (Industry-Relative) giúp bộ lọc tài chính loại bỏ các cổ phiếu suy thoái tiềm ẩn, mở rộng bể ứng viên đạt chuẩn, đưa CAGR ngoài mẫu vươn lên **24,87%/năm**, chính thức vượt qua chỉ số VN-Index (24,47%/năm) và giảm sụt giảm tối đa về **-22,55%**.

---

### Slide 24: Các Kết Luận Khoa Học Rút Ra Từ Chuỗi Kết Quả Thực Nghiệm (Mục 5.4.2)
1. **Về tính vượt trội của chiến lược Combined:**
   - Chiến lược Combined **chưa chứng minh được ưu thế nhất quán** trên cả hai phương diện lợi suất và rủi ro.
   - Việc cải thiện thứ hạng lợi suất từ vị trí thứ 4 trong Development lên vị trí thứ 2 trong Holdout (trong 5 chiến lược nội bộ) là một điểm sáng, nhưng chưa đủ để khẳng định tính bền vững lâu dài.
   - Bằng chứng thực nghiệm đáng lưu ý nhất: **Chiến lược Thuần động lượng (Momentum-only) vượt trội hơn Combined trên cả 3 chỉ tiêu cốt lõi (CAGR, Độ biến động và Max Drawdown) ở cả hai giai đoạn.**
2. **Ý nghĩa thực chất của chứng nhận kiểm toán PASS:**
   - Kết quả kiểm chứng PASS từ nhóm kiểm toán độc lập chỉ xác nhận rằng: **Toàn bộ quy trình backtest được thực hiện và tái lập 100% đúng theo các quy tắc kỹ thuật và dữ liệu đã khóa.**
   - Chứng nhận PASS **hoàn toàn không đồng nghĩa với việc chiến lược đã chứng minh được hiệu quả đầu tư vượt trội trên thị trường thực tế.**
3. **Tính độc lập của các tầng phương pháp luận:**
   - Kết luận thực nghiệm chỉ áp dụng chặt chẽ cho bộ quy tắc danh mục cụ thể của Combined đã thử nghiệm, không phủ nhận giá trị của phương pháp phân cụm nói chung.
   - Giữ vững nguyên tắc nghiên cứu bất biến: **Chất lượng cụm, Độ ổn định cụm và Hiệu quả danh mục tiếp tục là ba tầng đánh giá độc lập tuyệt đối.**

---

### Slide 25: Kiến Trúc Triển Khai Hệ Thống Toàn Diện & Công Nghệ Điện Toán Đám Mây
- Hệ sinh thái công nghệ phân tầng hiện đại bảo đảm độ trễ thấp và khả năng mở rộng:

| Thành phần hệ thống | Công nghệ chủ đạo | Nền tảng triển khai | Vai trò & Chức năng kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Frontend Web UI** | Next.js 14, Tailwind CSS, TypeScript, Canvas | Vercel Platform | Giao diện tương tác Blueprint hiện đại; hiển thị biểu đồ phân cụm, NAV, Drawdown thời gian thực. |
| **Backend REST API** | Python FastAPI, Uvicorn, Docker Container | Render Cloud Service | Cung cấp các API truy vấn đặc trưng, tính toán phân cụm động, dữ liệu BCTC và kết quả Backtest. |
| **Analytical Database** | DuckDB Engine, Apache Parquet Format | Embedded Storage | Động cơ phân tích nhúng tốc độ cao, thực thi truy vấn OLAP phức tạp trên hàng triệu dòng dữ liệu. |
| **Dashboard /backtest** | HTML5 Canvas, Chart.js, Vanilla JS | Production (05/11/2026) | Bảng điều khiển chuyên dụng cho phép đối chứng trực quan NAV 5 chiến lược, tra cứu lệnh và audit PIT. |

---

### Slide 26: Hệ Thống Đánh Giá Đầu Tư Ma Trận Hai Chiều (D-ASS-01)
- Quy chuẩn hóa khuyến nghị đầu tư tự động dựa trên ma trận giao thoa 2 chiều: Xung lực Động lượng thị trường (Trục Tung) và Sức khỏe Tài chính Point-in-Time (Trục Hoành).
- **Phân hạng khuyến nghị 4 cấp độ đầu tư chuẩn mực:**

| Cấp độ khuyến nghị | Điều kiện giao thoa ma trận | Ý nghĩa kinh tế & Hành động đề xuất |
| :--- | :--- | :--- |
| **1. Tích lũy mạnh (Strong Accumulate)** | Cụm Leading (A v4) + Cụm Tài chính Tốt (B-PIT) | Doanh nghiệp hoàn hảo: Vừa có dòng tiền dẫn dắt, vừa có nền tảng cơ bản vững mạnh. **Ưu tiên giải ngân tỷ trọng cao nhất.** |
| **2. Tăng trưởng động lượng (Momentum Growth)** | Cụm Leading (A v4) + Cụm Tài chính Trung bình | Doanh nghiệp đang hưởng lợi từ dòng tiền nóng đầu cơ; cơ bản chấp nhận được. **Mua theo sóng, đặt chặn lỗ chặt chẽ.** |
| **3. Thận trọng / Nắm giữ (Cautious Hold)** | Cụm Neutral (A v4) + Cụm Tài chính Tốt | Doanh nghiệp tốt nhưng giá đang tích lũy hoặc thiếu dòng tiền kích hoạt. **Nắm giữ kiên nhẫn, chưa gia tăng tỷ trọng.** |
| **4. Tránh nắm giữ (Avoid / Exit)** | Cụm Laggards HOẶC Cụm Tài chính Yếu | Cổ phiếu suy thoái dòng tiền hoặc rủi ro kiệt quệ tài chính cao. **Tuyệt đối không giải ngân; kích hoạt bán cắt lỗ.** |

---

### Slide 27: Dashboard Sản Phẩm Trực Quan: Trải Nghiệm Người Dùng Thực Tế
- **Trang Bản đồ phân cụm thị trường (Cluster Map):**
  - Trực quan hóa không gian phân cụm 2D/3D thông qua phép chiếu giảm chiều t-SNE / PCA.
  - Phân tách màu sắc trực quan giữa 3 cụm Leading, Neutral, Laggards; hỗ trợ bộ lọc sàn giao dịch (HOSE, HNX, UPCoM).
- **Hồ sơ chi tiết doanh nghiệp (Stock Deep-dive Profile):**
  - Tra cứu tức thời 9 đặc trưng kỹ thuật và chuỗi 9 chỉ số BCTC 10 năm của từng mã cổ phiếu.
  - Ma trận so sánh trực quan doanh nghiệp với các đối thủ cạnh tranh cùng phân ngành cấp 2.
- **Bảng điều khiển kiểm định chiến lược (/backtest Dashboard):**
  - Biểu đồ NAV tương tác đối sánh đa chiến lược, tính năng zoom-in theo từng chu kỳ thị trường.
  - Tra cứu minh bạch lịch sử khớp lệnh từng phiên, bảng phân bổ ngành và nhật ký kiểm toán ngày công bố BCTC.

---

### Slide 28: Tính Minh Bạch & Khả Năng Tái Lập 100% (Milestone M3-C)
- Toàn bộ kết quả nghiên cứu và mã nguồn được đóng gói thành chuỗi 4 Jupyter Notebooks độc lập:

| Tên Notebook | Phạm vi thực thi | Nhiệm vụ kiểm chứng độc lập | Kết quả đầu ra ghi nhận |
| :--- | :--- | :--- | :---: |
| `01_verify_environment.ipynb` | Môi trường hệ thống | Kiểm tra phiên bản Python ($\ge 3.10$), các thư viện phụ thuộc và tính toàn vẹn của tệp cấu hình. | **PASS tuyệt đối** |
| `02_reproduce_bpit.ipynb` | Phân cụm B-PIT | Tái lập pipeline chuẩn hóa BCTC, fit K-Means tại cutoff, kiểm tra rò rỉ dữ liệu fit-leak. | **Fit-leak = 0 cả 9 năm** |
| `03_reproduce_backtest.ipynb` | Hệ thống Backtest M3 | Chạy lại toàn bộ 5 chiến lược trên Development và Holdout, xuất bảng NAV và metrics. | **Khớp 100% với báo cáo** |
| `04_audit_and_reconciliation.ipynb` | Kiểm toán & Đối chiếu | Đối chiếu chi tiết NAV, khớp lệnh từng mã, kiểm tra số dư tiền mặt và sự kiện giao dịch biên. | **Audit PASS, không lệch 1 xu** |

- **Niêm phong mật mã học:** Mọi tệp dữ liệu trung gian, ma trận nhãn phân cụm và kết quả backtest đều được gắn kèm mã băm SHA256 chống chỉnh sửa.

---

### Slide 29: Giới Hạn Nghiên Cứu Thừa Nhận Minh Bạch & Hướng Phát Triển
- Nhóm nghiên cứu chủ động thừa nhận 3 giới hạn kỹ thuật theo chuẩn mực khoa học:

| Giới hạn phương pháp | Bản chất kỹ thuật | Tác động đến kết quả & Giải pháp xử lý |
| :--- | :--- | :--- |
| **1. Trạng thái Mốc Final 2026** | Năm 2026 chưa kết thúc; BCTC FY2025 mới chỉ có 3 báo cáo được công bố chính thức. | Mốc Final Evaluation 2026 gắn nhãn `NOT_READY`; tuân thủ nguyên tắc không ép số liệu khi chưa đủ chu kỳ. |
| **2. Giả định phí giao dịch 0 bps** | Hệ thống backtest học thuật chạy với chi phí 0 để đo lường năng lực tạo tín hiệu thuần túy của cụm. | Các chiến lược có vòng quay danh mục cao (~50%/kỳ) sẽ chịu khấu trừ hiệu suất khoảng 1,5% - 3%/năm khi áp dụng phí thực tế (15 - 30 bps). |
| **3. Độ trễ dữ liệu trước FY2022** | Giai đoạn trước FY2022 phải dùng giả định thận trọng ngày 30/06 năm sau do CafeF thiếu trường `CreateDate`. | Làm giảm tính cập nhật tức thời của tín hiệu tài chính trong giai đoạn 2019 - 2021; đã được khắc phục hoàn toàn từ FY2022 trở đi. |

- **Định hướng mở rộng tương lai:**
  - Tích hợp thêm dữ liệu BCTC theo quý (Quarterly Financials) để tăng tần suất cập nhật tín hiệu.
  - Áp dụng các mô hình học sâu chuỗi thời gian (Temporal Fusion Transformers, Graph Neural Networks) mô hình hóa mối quan hệ liên ngành.

---

### Slide 30: Tổng Hợp Bàn Giao Dự Án M1 - M3 & Kết Luận
- **Nhật ký tiến độ và khối lượng thực hiện:** Dự án hoàn thành qua **361 commits trên GitHub** (từ 11/09/2026 đến 20/11/2026) với sự phối hợp chặt chẽ của cả 6 thành viên.
- **Danh mục tài sản bàn giao chính thức của Team DELTA:**
  1. *Hạ tầng Dữ liệu (M1):* Data Lake toàn thị trường 1.522 mã cổ phiếu (10 năm), 1.172 mã BCTC, phễu kiểm soát chất lượng đạt chuẩn C8 v2.
  2. *Mô hình Định lượng (M2):* Mô hình thị trường chuẩn hóa A v4 ($k=3$), giải quyết dứt điểm thiên lệch Silhouette ảo; Mô hình B-PIT tài chính Point-in-Time sạch rò rỉ.
  3. *Hệ thống Thực nghiệm & Triển khai (M3):* Khung Backtest 4 bước hoàn chỉnh, minh chứng CAGR vượt trội 20,65% - 24,87%/năm; Web Dashboard sản phẩm trên Vercel & Render; Bộ 4 Notebooks tái lập 100%.
- **Thông điệp kết luận:** Dự án đã chứng minh thành công tính khả thi và ưu thế vượt trội của phương pháp luận định lượng đa nhân tố có kiểm soát nghiêm ngặt về Point-in-Time trên thị trường chứng khoán Việt Nam.
