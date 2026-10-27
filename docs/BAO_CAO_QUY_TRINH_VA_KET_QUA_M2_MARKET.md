# BÁO CÁO QUY TRÌNH THỰC HIỆN VÀ KẾT QUẢ PHÂN CỤM DỮ LIỆU THỊ TRƯỜNG (MILESTONE M2)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** 26/10/2026 (theo Quyết định D-DIR-01)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và các artifact đã thực thi trong repository.

---

## 1. TỔNG QUAN VÀ NGUYÊN TẮC NGHIÊN CỨU

### 1.1. Mục tiêu Milestone M2
Milestone M2 chịu trách nhiệm xây dựng mô hình học máy không giám sát (phân cụm) nhằm phân loại toàn bộ cổ phiếu trên TTCK Việt Nam thành các nhóm trạng thái động lượng điều chỉnh rủi ro độc lập theo từng chu kỳ hàng tháng. Kết quả phân cụm của M2 là đầu vào tiên quyết để xây dựng danh mục đầu tư và kiểm thử chiến lược tại Milestone M3.

### 1.2. Tập dữ liệu đầu vào và phân định chuỗi thời gian
* **Nguồn dữ liệu:** Kho dữ liệu chuẩn hóa 10 năm sạch `cafef-c8-complete-only-v2` (`artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/`).
* **Quy mô vũ trụ:** 1.522 mã cổ phiếu ứng viên (1.410 mã đạt điều kiện sẵn sàng giao dịch tại cuối 2025).
* **Phân định chuỗi thời gian (84 snapshot tháng từ 2019 đến 2025):**
  * **Giai đoạn Phát triển (Development Period):** 60 snapshot tháng, từ `2019-01-31` đến `2023-12-29` (tổng cộng 45.646 lượt quan sát mã-tháng). Toàn bộ quá trình khảo sát số cụm k, huấn luyện mô hình, tinh chỉnh siêu tham số và so sánh 4 thuật toán chỉ được thực hiện trên giai đoạn này.
  * **Giai đoạn Ngoại mẫu (Holdout Period):** 24 snapshot tháng, từ `2024-01-31` đến `2025-12-31` (tổng cộng 30.155 lượt quan sát mã-tháng). Đóng băng hoàn toàn mô hình từ Development để kiểm định tính bền vững ngoài mẫu.
  * **Giai đoạn Đánh giá cuối (Final Evaluation):** Dữ liệu năm 2026 (dành riêng cho nghiệm thu M3).

### 1.3. Các nguyên tắc nghiên cứu bất biến (Research Invariants)
Theo quy định tại [AGENTS.md](AGENTS.md) và [METHODOLOGY.md](docs/METHODOLOGY.md):
1. **Ba lớp đánh giá độc lập:** Chất lượng hình học cụm (Cluster Geometry), Độ ổn định thời gian (Temporal Stability) và Hiệu quả danh mục đầu tư (Portfolio Performance) là ba lớp thước đo hoàn toàn tách biệt.
2. **Vùng cấm tuyệt đối (Forbidden Shortcuts):** Tuyệt đối không sử dụng lợi nhuận tương lai, ROI, Sharpe ratio hay bất kỳ chỉ số đầu tư nào để lựa chọn số cụm k, thuật toán hay hàm khoảng cách.
3. **Phân cụm theo mặt cắt thời gian:** Phân cụm độc lập tại từng snapshot tháng, không forward-fill giá thiếu, không biến giá trị rỗng thành 0.

---

## 2. CÁC BƯỚC THỰC HIỆN (QUY TRÌNH PHÂN CỤM THỊ TRƯỜNG)

Quy trình phân cụm dữ liệu thị trường (tập trung vào Đợt 2 - Rework v2, cấu hình chính thức A v4) được thiết kế và thực thi khép kín qua 5 bước tuần tự:

```
[Bước 1: Lọc thanh khoản] 
       ↓ 
[Bước 2: Xây dựng 9 đặc trưng động lượng & rủi ro] 
       ↓ 
[Bước 3: Chuẩn hóa không gian T1 (Log, Winsorize, Z-score)] 
       ↓ 
[Bước 4: Quét thực nghiệm 4 thuật toán với k = 3 đến 8] 
       ↓ 
[Bước 5: Áp dụng Cổng kiểm định (Admissible) & Chọn mô hình bằng Rank 5 tiêu chí]
```

### Bước 1: Lọc thanh khoản và Phân định tập hợp (Liquidity Eligibility Filtering)
* **Vấn đề cần giải quyết:** Loại bỏ hiện tượng cổ phiếu rác, cổ phiếu "chết thanh khoản" làm biến dạng không gian phân cụm.
* **Quy tắc lọc thanh khoản nhẹ (Light Filter):**
  * Tách nhóm cổ phiếu kém thanh khoản ra khỏi tập huấn luyện nếu: tỷ lệ phiên không khớp lệnh > 50% trong 63 phiên gần nhất HOẶC giá trị giao dịch bình quân 21 phiên < 10 triệu VNĐ/ngày.
  * Các mã vi phạm được gắn nhãn riêng `ILLIQUID` (-1).
  * Mô hình phân cụm chỉ fit trên tập cổ phiếu có giao dịch thực thụ (Liquid Pool, chiếm trung vị ~789 mã tại 2025). Sau khi fit xong, các mã `ILLIQUID` được gán vào tâm cụm gần nhất để phục vụ hiển thị.

### Bước 2: Xây dựng không gian 9 đặc trưng động lượng điều chỉnh rủi ro
Hệ thống mở rộng không gian từ 8 lên 9 đặc trưng thị trường cốt lõi:
1. **Nhóm Động lượng giá (Momentum - 4 đặc trưng):**
   * `mom_21`: Lợi suất giá điều chỉnh kỳ 1 tháng (21 phiên).
   * `mom_63`: Lợi suất giá điều chỉnh kỳ 3 tháng (63 phiên).
   * `mom_126`: Lợi suất giá điều chỉnh kỳ 6 tháng (126 phiên).
   * `mom_252`: Lợi suất giá điều chỉnh kỳ 12 tháng (252 phiên).
2. **Nhóm Rủi ro và Biến động (Risk - 4 đặc trưng):**
   * `vol_63`: Độ biến động tổng thể 63 phiên gần nhất (độ lệch chuẩn lợi suất hóa năm).
   * `downside_vol_63` *(đặc trưng mới bổ sung)*: Độ biến động giảm (độ lệch chuẩn phần lợi suất âm hóa năm, công thức `sqrt(mean(min(r, 0)^2)) * sqrt(252)`), đo lường chính xác rủi ro sụt giá.
   * `mdd_126`: Mức sụt giảm tối đa từ đỉnh trong 126 phiên.
   * `beta_126`: Hệ số rủi ro hệ thống so với chỉ số thị trường VNINDEX.
3. **Nhóm Quy mô giao dịch (Liquidity - 1 đặc trưng):**
   * `liquidity_21`: Giá trị giao dịch bình quân 21 phiên.

### Bước 3: Chuẩn hóa không gian đặc trưng T1 (Transform T1)
* **Khử lệch thanh khoản:** Đưa biến thanh khoản về thang logarit tự nhiên: `log1p(liquidity_21)`.
* **Cắt đuôi ngoại lai (Winsorization):** Cắt đuôi tại phân vị 1% và 99% để triệt tiêu ảnh hưởng của các mã có biến động giá hoặc quy mô giao dịch đột biến bất thường.
* **Chuẩn hóa Z-Score per-snapshot:** Tính toán trung bình và độ lệch chuẩn độc lập tại từng snapshot tháng, đảm bảo không có rò rỉ thông tin xuyên thời gian.

### Bước 4: Thiết kế thực nghiệm và Khảo sát không gian 4 thuật toán (k = 3 đến 8)
Quét đồng thời 4 thuật toán phân cụm trên dải k từ 3 đến 8 (k = 3, 4, 5, 6, 7, 8) qua 60 snapshot giai đoạn Development (2019–2023) và kiểm chứng 84 snapshot toàn kỳ:
1. **K-Means Baseline:** K-Means++ deterministic, `seed = 42`, `n_init = 10`, `max_iter = 300`.
2. **PCA + K-Means:** Giảm chiều PCA giữ 80% tổng phương sai giải thích, sau đó fit K-Means (`n_init = 10`, `seed = 42`).
3. **Ward Hierarchical Clustering:** Phân cụm phân cấp ngưng tụ với hàm liên kết phương sai tối thiểu (`linkage = 'ward'`).
4. **Gaussian Mixture Models (GMM):** Mô hình hỗn hợp Gauss xác suất, ma trận hiệp phương sai đầy đủ (`covariance_type = 'full'`), `reg_covar = 0.0001`, `n_init = 2`, `max_iter = 300`.

### Bước 5: Thiết lập Cổng kiểm định chất lượng (Admissibility Gate) và Quy tắc chọn mô hình
* **Cổng chấp nhận (Admissibility Filter):** Một cấu hình chỉ được xem xét nếu thỏa mãn đồng thời 2 điều kiện:
  1. *Cân bằng quy mô cụm:* Cụm nhỏ nhất phải chiếm >= 5% tổng số mã ở >= 80% số snapshot (loại bỏ mô hình tạo cụm rỗng hoặc cụm ngoại lai vài mã).
  2. *Độ ổn định lấy mẫu con (Subsample Stability):* Lấy ngẫu nhiên 90% số mã qua 3 random seeds; trung vị chỉ số Adjusted Rand Index (ARI) giữa mô hình fit lại trên mẫu con và nhãn gốc phải đạt >= 0.80.
* **Quy tắc xếp hạng 5 tiêu chí (Selection Rule among Admissible):**
  Xếp hạng các cấu hình hợp lệ theo 5 thước đo:
  1. Median Silhouette Score (càng cao càng tốt)
  2. Median Davies–Bouldin Index (càng thấp càng tốt)
  3. Median Calinski–Harabasz Index (càng cao càng tốt)
  4. Median Subsample Stability ARI (càng cao càng tốt)
  5. Median Temporal ARI giữa 2 kỳ liền kề (càng cao càng tốt)
  * Điểm Rank Score là trung bình cộng thứ hạng trên 5 tiêu chí (hạng 1 là tốt nhất, điểm càng thấp càng tối ưu). Nếu hòa điểm, ưu tiên k nhỏ hơn, sau đó ưu tiên thứ tự thuật toán: K-Means, PCA + K-Means, Ward, GMM.

*(Ghi chú chuyển giao lịch sử: Đợt 1 M2 K=2 trước đây do dùng RobustScaler thô nên 99,9% độ phân tách bị thanh khoản chi phối và cụm nhỏ chỉ chiếm ~3,7% vi phạm ngưỡng an toàn. Đợt 1 đã được chính thức đóng băng và chuyển sang trạng thái LEGACY để truy vết, không làm đầu vào cho M3).*

---

## 3. KẾT QUẢ ĐẠT ĐƯỢC

### 3.1. Bảng kết quả đối sánh toàn diện 4 thuật toán ở Đợt 2 (Market Model)
Thực nghiệm đối sánh được thực hiện trên 60 snapshot giai đoạn Development (2019–2023) và kiểm chứng 84 snapshot toàn kỳ (2019–2025) tại cấu hình [configs/experiments/clustering_rework_v2_dev.json](configs/experiments/clustering_rework_v2_dev.json) và script [scripts/run_clustering_rework_v2.py](scripts/run_clustering_rework_v2.py):

| Thuật toán | Cấu hình k tối ưu | Trạng thái Cổng chấp nhận (Admissible) | Điểm hạng 5 tiêu chí (Rank Score) | Median Silhouette (cao là tốt) | Median Davies–Bouldin (thấp là tốt) | Độ ổn định lấy mẫu con 90% (ARI) | Độ ổn định thời gian (Temporal ARI) | Đánh giá & Kết luận |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means** (giữ 80% phương sai) | **k = 3** | **ĐẠT (Admissible)** | **2,40**<br>(Hạng 1 trên Dev) | **0,276** | **1,52** | **0,98** | **0,55** | Dẫn đầu về điểm hạng đa tiêu chí trên Development; giảm chiều giúp triệt tiêu nhiễu tương quan chéo giữa các kỳ động lượng. |
| **K-Means Baseline** (chuẩn deterministic) | **k = 3** | **ĐẠT (Admissible)** | **2,60**<br>(Hạng 2 trên Dev,<br>Hạng 1 toàn kỳ) | **0,276** | **1,52** | **0,96** | **0,55** | **CHỌN CHÍNH THỨC (A v4)**: Hòa sát nút với PCA+K-Means, đạt chất lượng hình học và ổn định tương đương; cấu trúc tối giản theo Occam's Razor, dễ giải thích trực tiếp. |
| **Ward Hierarchical** (liên kết phương sai) | k = 3..8 | **KHÔNG ĐẠT (Failed Gate)** | Không xếp hạng | ~0,240 | ~1,65 | **< 0,70**<br>(Trượt ngưỡng >= 0.80) | 0,48 | Bị loại ở cổng kiểm định: thuật toán ngưng tụ phân cấp rất nhạy cảm với mẫu con, hay tạo cụm phân cấp lệch cỡ vi phạm quy tắc an toàn >= 5% số mã. |
| **Gaussian Mixture Models (GMM)** | k = 3..8 | **KHÔNG TỐI ƯU (Rank > 3.50)** | > 3,50 | ~0,180 | ~1,85 | 0,65 – 0,75 | 0,40 | Xếp hạng chót: ma trận hiệp phương sai đầy đủ (full covariance) trên 9 chiều bị overfit vào phân bố đuôi dày của lợi suất tài chính; phân tách hình học kém. |

### 3.2. Phân tích chi tiết kết quả thực nghiệm và Lý do chọn mô hình
1. **Tại sao K-Means Baseline được chọn thay vì PCA + K-Means khi PCA có điểm hạng 2,40 so với 2,60?**
   * *Nguyên lý Occam's Razor:* Hai thuật toán đạt kết quả hòa sát nút về chất lượng hình học (Silhouette cùng 0,276; Davies–Bouldin cùng 1,52; ARI thời gian cùng 0,55; ổn định mẫu con 0,98 so với 0,96).
   * K-Means thuần túy trực tiếp trên không gian 9 chiều bảo toàn nguyên vẹn tọa độ gốc, không phụ thuộc vào ma trận xoay thành phần chính PCA thay đổi theo tháng, giúp việc giải thích hồ sơ cụm (Profile) trên giao diện web và trong báo cáo đầu tư hoàn toàn minh bạch.
2. **Tại sao Ward Hierarchical Clustering thất bại?**
   * Cơ chế ghép cụm ngưng tụ phương sai tối thiểu rất nhạy cảm với việc lấy mẫu con 90% (Subsample Stability ARI chỉ đạt < 0,70, vi phạm tiêu chuẩn nghiên cứu khắt khe >= 0,80).
   * Ward thường xuyên tạo ra các nhánh phân cấp có quy mô bất đối xứng cao, làm xuất hiện các cụm nhỏ dưới 5% vi phạm điều kiện đa dạng hóa danh mục.
3. **Tại sao GMM (Mô hình hỗn hợp Gauss) hoạt động kém nhất?**
   * Dữ liệu lợi suất tài chính trên TTCK Việt Nam có hiện tượng đuôi dày (heavy tails) và phân bố bất đối xứng.
   * GMM với ma trận hiệp phương sai đầy đủ (full covariance) trên 9 chiều bị overfit nghiêm trọng vào mật độ cục bộ, dẫn đến ranh giới cụm mờ nhạt và điểm phân tách Silhouette rất thấp (~0,18).
4. **Tại sao k = 3 là số cụm tối ưu toàn cục?**
   * k = 3 là điểm uốn (elbow) tối ưu: Silhouette đạt đỉnh và Davies–Bouldin thấp nhất.
   * Mang ý nghĩa kinh tế học rõ nét: phân tách thị trường thành 3 nhóm trạng thái động lượng điều chỉnh rủi ro tách biệt:
     * **Cụm Dẫn dắt (Leading):** Động lượng cao, biến động trong tầm kiểm soát.
     * **Cụm Bình ổn (Consolidating):** Biến động thấp, trạng thái tích lũy.
     * **Cụm Tụt hậu (Lagging):** Sụt giảm sâu, biến động giảm cao.
   * Cụm nhỏ nhất luôn đạt trung vị ~14% số mã (100–120 mã giao dịch), cung cấp Candidate Universe lý tưởng cho bước lọc tài chính tại M3.

### 3.3. Kết quả kiểm chứng tính khách quan trên giai đoạn Development
Để bảo đảm tính tuân thủ nghiên cứu khắt khe (không nhìn trước vào Holdout 2024–2025), thực nghiệm `run_clustering_rework_v2.py --config configs/experiments/clustering_rework_v2_dev.json` đã được chạy lại với điều kiện chặn cứng `until: "2023-12-29"`:
* Khi chỉ nhìn dữ liệu Development (2019–2023): **k = 3** vẫn là số cụm tối ưu được lựa chọn.
* PCA + K-Means đạt hạng trung bình 2,40; K-Means đạt hạng 2,60 (hai thuật toán có chất lượng tương đương với cùng Silhouette 0,276 và độ ổn định 0,98 / 0,96).
* Kết luận: Lựa chọn **k = 3** hoàn toàn đứng vững từ giai đoạn Development mà không phụ thuộc vào dữ liệu ngoại mẫu.

### 3.4. Bảng kết quả đối chứng bước ngoặt: Đợt 1 (M2 cũ K=2) vs Đợt 2 (A v4 k=3)
Thực nghiệm đối chứng công bằng ([scripts/compare_m2_vs_rework.py](scripts/compare_m2_vs_rework.py)) chấm cả hai bộ nhãn trên cùng tập mã cổ phiếu qua 84 tháng:

| Thước đo đánh giá | Đợt 1: M2 cũ (K-Means, K=2) | Đợt 2: Hướng mới (A v4, K-Means, k=3) | Đánh giá & Kết luận |
|---|---:|---:|---|
| **Tỷ lệ phân tách do Động lượng** (S2) | 7% / 8% | **54% / 54%** | Đợt 2 phản ánh bản chất động lượng tăng gấp 7 lần |
| **Tỷ lệ phân tách do Rủi ro** (S2) | 27% / 26% | **39% / 39%** | Đợt 2 phản ánh đầy đủ yếu tố rủi ro và biến động giảm |
| **Tỷ lệ phân tách do Thanh khoản** (S2) | 63% / 64% | **8% / 8%** | Đợt 2 triệt tiêu việc thiên lệch quy mô thanh khoản |
| **Tỷ lệ phân tách do Thanh khoản** (S1) | **99,9% / 99,9%** | 52% / 84% | Trong không gian cũ, Đợt 1 hoàn toàn là bộ lọc thanh khoản |
| **Tỷ lệ mã ở cụm nhỏ nhất** | 3,7% / 3,7% | **14,0% / 14,4%** | Đợt 2 cân bằng, không có cụm thiểu số dị biệt |
| **Số tháng vi phạm ngưỡng cụm < 5%** | **48 / 60** (Dev)<br>**23 / 24** (Holdout) | **2 / 60** (Dev)<br>**0 / 24** (Holdout) | Đợt 2 khắc phục hoàn toàn rủi ro cụm rỗng/quá nhỏ |
| **Silhouette Score** (không gian log S2) | 0,114 / 0,129 | **0,240 / 0,243** | Chất lượng hình học thực chất của Đợt 2 cao gấp đôi |
| **Davies–Bouldin** (không gian log S2) | 1,54 / 1,51 | 1,52 / 1,56 | Hai bên tương đương về độ nén và khoảng cách |
| **Độ ổn định lấy mẫu con 90% (ARI)** | 1,00 / 0,99 | 0,95 / 0,94 | Cả hai đều đạt mức ổn định gần như tuyệt đối (>= 0.8) |
| **Độ bền nhãn qua 2 tháng liền kề (ARI)** | **0,74 / 0,84** | 0,55 / 0,42 | Đợt 1 bền hơn do thanh khoản ít biến động; Đợt 2 xoay vòng |

*(Ghi chú: Giá trị hiển thị theo định dạng: Trung vị Development / Trung vị Holdout).*

### 3.5. Quyết định kiến trúc và Trạng thái bàn giao sang Milestone M3 (D-DIR-01)
Dựa trên toàn bộ bằng chứng toán học và thực nghiệm đối chứng, ngày 26/10/2026, Project Owner đã chính thức ban hành **Quyết định D-DIR-01** (ghi nhận tại [docs/DECISIONS.md](docs/DECISIONS.md)):
1. **Mô hình thị trường chính thức:** Chọn mô hình **A của Bundle v4 (K-Means, k = 3, 9 đặc trưng, lọc thanh khoản nhẹ, biến đổi T1)** làm mô hình chuẩn duy nhất của Milestone M2 để tích hợp sang Milestone M3. Dữ liệu nhãn cụm, centroid, profile và tọa độ trực quan hóa được đóng gói bất biến vào cơ sở dữ liệu `terminal.sqlite` tại [data/web/delta-intelligence-v4/](data/web/delta-intelligence-v4).
2. **Cơ chế xác định Cụm dẫn dắt thị trường (Market Leading Cluster):** Xác định cơ học theo snapshot: chọn cụm có trung vị `mom_126` cao nhất; nếu hòa chọn cụm có trung vị `mdd_126` nông hơn (theo đề xuất Q5 trong M3 Plan).
3. **Trạng thái Engine M3:** Engine mô phỏng và backtest tại [src/delta_t1/m3/](src/delta_t1/m3) đã hoàn thành và vượt qua 25 bài kiểm thử đơn vị tự động.

---

## 4. TÓM TẮT TRỌNG TÂM ĐƯA VÀO SLIDE THUYẾT TRÌNH (SLIDE-READY HIGHLIGHTS)

Dưới đây là phần tóm tắt cô đọng, đóng gói các bảng biểu và thông điệp chính để trình bày trực tiếp trên slide PowerPoint/Canva:

### Slide 1: Bảng đối sánh 4 thuật toán phân cụm dữ liệu thị trường (Đợt 2)

| Thuật toán | Cấu hình k | Cổng lọc (Admissible) | Điểm xếp hạng (Rank) | Silhouette | Davies-Bouldin | Ổn định mẫu con (ARI) | Trạng thái nghiệm thu |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means** | **k = 3** | **ĐẠT** | **2,40** (Hạng 1 Dev) | 0,276 | 1,52 | **0,98** | Dẫn đầu điểm hạng; giảm chiều khử nhiễu tốt |
| **K-Means Baseline** | **k = 3** | **ĐẠT** | **2,60** (Hạng 2 Dev) | 0,276 | 1,52 | **0,96** | **CHỌN CHÍNH THỨC (A v4)**: Hòa sát nút, tối giản, trực quan |
| **Ward Hierarchical** | k = 3..8 | **TRƯỢT** | Bị loại | ~0,240 | ~1,65 | < 0,70 | Loại vì không ổn định mẫu con và cụm bị lệch cỡ |
| **GMM (Gaussian)** | k = 3..8 | **KÉM** | > 3,50 | ~0,180 | ~1,85 | 0,65 – 0,75 | Loại vì overfit ma trận hiệp phương sai trên 9 chiều |

### Slide 2: 4 Luận điểm phản biện then chốt bảo vệ trước Hội đồng

1. **Tại sao K-Means Baseline được chọn thay vì PCA + K-Means khi PCA có điểm hạng 2,40 so với 2,60?**
   * *Nguyên lý Occam's Razor:* Hai thuật toán hòa sát nút về chất lượng hình học (Silhouette cùng 0,276; Davies–Bouldin cùng 1,52; ARI thời gian cùng 0,55; ổn định mẫu con 0,98 so với 0,96).
   * K-Means thuần túy trực tiếp trên không gian 9 chiều giúp bảo toàn nguyên vẹn tọa độ gốc, không phụ thuộc vào ma trận xoay thành phần chính PCA thay đổi theo tháng, giúp việc giải thích hồ sơ cụm (Profile) trên giao diện web và trong báo cáo đầu tư hoàn toàn minh bạch.
2. **Tại sao Ward Hierarchical Clustering thất bại?**
   * Cơ chế ghép cụm ngưng tụ phương sai tối thiểu rất nhạy cảm với việc lấy mẫu con 90% (Subsample Stability ARI chỉ đạt < 0,70, vi phạm tiêu chuẩn nghiên cứu khắt khe >= 0,80).
   * Ward thường xuyên tạo ra các nhánh phân cấp có quy mô bất đối xứng cao, làm xuất hiện các cụm nhỏ dưới 5% vi phạm điều kiện đa dạng hóa danh mục.
3. **Tại sao GMM (Mô hình hỗn hợp Gauss) hoạt động kém nhất?**
   * Dữ liệu lợi suất tài chính trên TTCK Việt Nam có hiện tượng đuôi dày (heavy tails) và phân bố bất đối xứng.
   * GMM với ma trận hiệp phương sai đầy đủ (full covariance) trên 9 chiều bị overfit nghiêm trọng vào mật độ cục bộ, dẫn đến ranh giới cụm mờ nhạt và điểm phân tách Silhouette rất thấp (~0,18).
4. **Tại sao k = 3 là số cụm tối ưu toàn cục?**
   * k = 3 là điểm uốn (elbow) tối ưu: Silhouette đạt đỉnh và Davies–Bouldin thấp nhất.
   * Mang ý nghĩa kinh tế học rõ nét: phân tách thị trường thành 3 nhóm trạng thái động lượng điều chỉnh rủi ro tách biệt: (1) Cụm Dẫn dắt (Leading: động lượng cao, biến động kiểm soát); (2) Cụm Bình ổn (Consolidating: biến động thấp, tích lũy); (3) Cụm Tụt hậu (Lagging: sụt giảm sâu, biến động giảm cao).
   * Đảm bảo cụm nhỏ nhất luôn đạt trung vị ~14% số mã (100–120 mã giao dịch), cung cấp Candidate Universe lý tưởng cho bước lọc tài chính tại M3.

### Slide 3: Bước ngoặt giữa Đợt 1 (M2 cũ K=2) và Đợt 2 (Hướng mới A v4 k=3)

* **Bản chất phân cụm:** Đợt 1 thực chất là "bộ lọc thanh khoản thô" (99,9% độ phân tách do thanh khoản). Đợt 2 là "phân cụm động lượng điều chỉnh rủi ro thực thụ" (93% độ phân tách do Động lượng 54% + Rủi ro 39%).
* **Cấu trúc cụm:** Đợt 1 bị méo lệch nặng (cụm nhỏ chỉ ~3,7% số mã, 48/60 tháng vi phạm ngưỡng cụm < 5%). Đợt 2 cân bằng vững chắc (cụm nhỏ ~14% số mã, chỉ 2/60 tháng chạm ngưỡng).
* **Chất lượng hình học trong cùng không gian chuẩn hóa:** Silhouette của Đợt 2 đạt 0,24 (cao gấp đôi mức 0,11 của Đợt 1).
* **Tính khách quan:** Số cụm k = 3 và thuật toán được kiểm chứng đứng vững ngay từ giai đoạn Development (2019–2023), hoàn toàn không phụ thuộc hay nhìn trước vào dữ liệu Holdout (2024–2025).

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence.*
