# BÁO CÁO TOÀN DIỆN QUY TRÌNH THỰC HIỆN VÀ KẾT QUẢ PHÂN CỤM DỮ LIỆU THỊ TRƯỜNG (MILESTONE M2)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** 26/10/2026 (theo Quyết định D-DIR-01)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và các artifact đã thực thi trong repository.

---

## 1. TỔNG QUAN, MỤC TIÊU VÀ NGUYÊN TẮC BẤT BIẾN

### 1.1. Mục tiêu Milestone M2
Milestone M2 chịu trách nhiệm xây dựng mô hình học máy không giám sát (phân cụm) nhằm phân loại toàn bộ cổ phiếu trên TTCK Việt Nam thành các nhóm trạng thái động lượng điều chỉnh rủi ro độc lập theo từng chu kỳ hàng tháng. Kết quả phân cụm của M2 là đầu vào tiên quyết để xây dựng danh mục đầu tư và kiểm thử chiến lược tại Milestone M3.

### 1.2. Tập dữ liệu đầu vào và phân định thời gian
* **Nguồn dữ liệu:** Kho dữ liệu chuẩn hóa 10 năm sạch `cafef-c8-complete-only-v2` (`artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/`).
* **Quy mô vũ trụ:** 1.522 mã cổ phiếu ứng viên (1.410 mã đạt điều kiện sẵn sàng giao dịch tại cuối 2025).
* **Phân định chuỗi thời gian (84 snapshot tháng từ 2019 đến 2025):**
  * **Giai đoạn Phát triển (Development Period):** 60 snapshot tháng, từ `2019-01-31` đến `2023-12-29` (tổng cộng 45.646 lượt quan sát mã-tháng). Toàn bộ quá trình khảo sát số cụm, huấn luyện mô hình, tinh chỉnh siêu tham số và so sánh phương pháp chỉ được thực hiện trên giai đoạn này.
  * **Giai đoạn Ngoại mẫu (Holdout Period):** 24 snapshot tháng, từ `2024-01-31` đến `2025-12-31` (tổng cộng 30.155 lượt quan sát mã-tháng). Đóng băng hoàn toàn mô hình từ Development để kiểm định tính bền vững ngoài mẫu.
  * **Giai đoạn Đánh giá cuối (Final Evaluation):** Dữ liệu năm 2026 (dành riêng cho nghiệm thu M3).

### 1.3. Các nguyên tắc nghiên cứu bất biến (Research Invariants)
Theo quy định tại [AGENTS.md](AGENTS.md) và [METHODOLOGY.md](docs/METHODOLOGY.md):
1. **Ba lớp đánh giá độc lập:** Chất lượng hình học cụm (Cluster Geometry), Độ ổn định thời gian (Temporal Stability) và Hiệu quả danh mục đầu tư (Portfolio Performance) là ba lớp thước đo hoàn toàn tách biệt.
2. **Vùng cấm tuyệt đối (Forbidden Shortcuts):** Tuyệt đối không sử dụng lợi nhuận tương lai, ROI, Sharpe ratio hay bất kỳ chỉ số đầu tư nào để lựa chọn số cụm k, thuật toán hay hàm khoảng cách.
3. **Phân cụm theo mặt cắt thời gian:** Phân cụm độc lập tại từng snapshot tháng, không forward-fill giá thiếu, không biến giá trị rỗng thành 0.

---

## 2. QUY TRÌNH THỰC HIỆN ĐỢT 1: HƯỚNG M2 BAN ĐẦU (K-MEANS K=2)

Đợt 1 được thực hiện qua chuỗi 13 nhiệm vụ có cấu trúc, mã nguồn thực thi lưu tại thư mục [M2/notebooks/](M2/notebooks) và báo cáo tại [M2/reports/](M2/reports).

### 2.1. Không gian đặc trưng và Tiền xử lý
* **8 đặc trưng thị trường chuẩn:**
  * 4 đặc trưng động lượng giá: `mom_21`, `mom_63`, `mom_126`, `mom_252` (lợi suất các kỳ 1, 3, 6, 12 tháng).
  * 3 đặc trưng rủi ro: `vol_63` (độ biến động 63 phiên), `mdd_126` (sụt giảm tối đa 126 phiên), `beta_126` (hệ số beta so với VNINDEX).
  * 1 đặc trưng thanh khoản: `liquidity_21` (giá trị giao dịch bình quân 21 phiên, tính theo VNĐ thô).
* **Chuẩn hóa Robust Scaling per-snapshot:**
  Công thức: `x_scaled = (x - Median) / IQR` với IQR = Q75 - Q25 tính riêng tại từng snapshot.

### 2.2. Khảo sát và Chọn số cụm toàn cục (Nhiệm vụ 3)
* **File thực thi:** [M2/notebooks/03_choose_global_k.ipynb](M2/notebooks/03_choose_global_k.ipynb)
* **Quy trình:** Khảo sát không gian k từ 2 đến 8 trên 60 development snapshots bằng K-Means.
* **Kết quả:**
  * k = 2 đạt Median Silhouette cao nhất vượt trội: `0.9408` (so với k = 3 đạt ~0.84, k = 4 đạt ~0.76).
  * Tiêu chí Tie-breaker Davies-Bouldin xác nhận k = 2 có DB thấp nhất: `0.4031`.
  * **Quyết định:** Đóng băng **Global K = 2** cho toàn bộ các phương án so sánh tiếp theo.

### 2.3. Huấn luyện đối sánh 3 mô hình trên Development (Nhiệm vụ 4, 5, 6)
Huấn luyện độc lập 3 mô hình với K = 2 trên 60 development snapshots:
1. **K-Means Baseline:** [M2/notebooks/04_kmeans_baseline.ipynb](M2/notebooks/04_kmeans_baseline.ipynb)  
   Thuật toán K-Means++ deterministic, seed = 42, n_init = 10, max_iter = 300.
2. **Ward Hierarchical Clustering:** [M2/notebooks/05_ward_hierarchical.ipynb](M2/notebooks/05_ward_hierarchical.ipynb)  
   Phân cụm phân cấp ngưng tụ với hàm liên kết phương sai tối thiểu Ward (`linkage='ward'`).
3. **PCA + K-Means:** [M2/notebooks/06_pca_kmeans.ipynb](M2/notebooks/06_pca_kmeans.ipynb)  
   Giảm chiều PCA giữ 80% tổng phương sai (thường giảm từ 8 chiều xuống còn 1 đến 2 thành phần chính), sau đó fit K-Means.

### 2.4. Đánh giá chất lượng và Độ ổn định thời gian (Nhiệm vụ 7, 8, 9, 10)
Đánh giá chi tiết qua 60 snapshot và 59 cặp tháng chuyển tiếp (kết quả tại [Bao_cao_M2_Nhiem_vu_10_So_sanh_va_Chon_mo_hinh_tot_nhat.md](M2/reports/Bao_cao_M2_Nhiem_vu_10_So_sanh_va_Chon_mo_hinh_tot_nhat.md)):

| Chỉ số đánh giá | K-Means Baseline | Ward Hierarchical | PCA + K-Means |
|---|---:|---:|---:|
| **Median Silhouette** (cao là tốt) | 0.940837 | 0.946262 | **0.946855** |
| **Median Davies–Bouldin** (thấp là tốt) | 0.403127 | **0.373575** | 0.397056 |
| **Median Calinski–Harabasz** (cao là tốt) | 1586.371 | 1525.514 | **1631.467** |
| **Median Adjusted Rand Index (ARI)** | 0.757047 | 0.740645 | **0.769164** |
| **Tỷ lệ giữ nguyên cụm (Persistence)** | 99.0071% | 98.9351% | **99.0491%** |
| **Tỷ lệ di cư cụm (Migration Rate)** | 0.9929% | 1.0649% | **0.9509%** |
| **Số snapshot có cụm < 5 mã** | 2 / 60 | 7 / 60 | 2 / 60 |
| **Độ phức tạp quy trình (Pipeline Complexity)** | **Low** | Medium | High |

* **Áp dụng Nguyên lý Occam's Razor:**  
  PCA + K-Means dẫn đầu về Silhouette (0.946855), nhưng khoảng cách so với K-Means Baseline (0.940837) chỉ là `0.006018`, thấp hơn nhiều so với ngưỡng cải thiện tối thiểu 0.03 quy định trong đề cương để biện minh cho việc tăng độ phức tạp thuật toán và mất mát diễn giải.  
  -> **Lựa chọn chính thức:** **K-Means Baseline (K = 2)** được chọn và đóng băng (`FROZEN_FOR_HOLDOUT`).

### 2.5. Kiểm định Final Holdout và Bàn giao (Nhiệm vụ 11, 12, 13)
* **File thực thi:** [M2/notebooks/11_final_holdout_execution.ipynb](M2/notebooks/11_final_holdout_execution.ipynb)
* **Kết quả trên 24 tháng Holdout (2024–2025):** 30.155 lượt gán nhãn, Median Silhouette đạt `0.949324`, Median DB đạt `0.398445`, Median ARI đạt `0.8407`.
* Tổng kết bàn giao tại [Bao_cao_tong_ket_M2_Ban_giao_M3.md](M2/reports/Bao_cao_tong_ket_M2_Ban_giao_M3.md): 75.801 lượt gán nhãn trên toàn bộ 84 snapshot.

---

## 3. PHÁT HIỆN VẤN ĐỀ VÀ NHU CẦU TÁI CẤU TRÚC (CLUSTERING REWORK)

Khi tiến hành kiểm tra tích hợp để đưa nhãn cụm M2 vào Milestone M3 (chọn danh mục và backtest thực tế vào ngày 24–25/10/2026), nhóm nghiên cứu đã phát hiện ra các khiếm khuyết phương pháp luận nghiêm trọng:

### 3.1. Sự chi phối tuyệt đối của thanh khoản thô (Liquidity Bias)
* Khi phân tích phương sai giải thích phân tách cụm (Between-cluster separation variance): Trong không gian chuẩn hóa RobustScaler thô của Đợt 1, **99,9%** độ phân tách giữa 2 cụm bị chi phối hoàn toàn bởi đặc trưng `liquidity_21`.
* Các đặc trưng động lượng chỉ đóng góp khoảng **7% – 8%**, rủi ro đóng góp **26% – 27%**.
* **Hệ quả:** Điểm Silhouette cao kỷ lục (~0.94) thực chất là **chỉ số ảo** do một số ít cổ phiếu có quy mô giao dịch cực lớn (ngoại lai) tự kéo giãn không gian và tách thành một nhóm riêng. Mô hình K=2 thực chất biến thành một "bộ lọc quy mô/thanh khoản", không phản ánh được cấu trúc động lượng thị trường.

### 3.2. Mất cân bằng cụm nghiêm trọng và nghẽn đầu vào M3
* Cụm nhỏ ở Đợt 1 chỉ chiếm trung vị **3,7%** số mã thị trường (khoảng 14 đến 28 mã mỗi tháng).
* Có tới **48/60 tháng ở Development** và **23/24 tháng ở Holdout** vi phạm quy tắc an toàn tỷ lệ cụm tối thiểu (cụm phải >= 5% số lượng mã).
* Khi bước sang M3, cụm dẫn dắt chỉ có ~20 mã. Sau khi giao với điều kiện tài chính (mô hình B), Candidate Universe nhiều tháng chỉ còn từ 1 đến 4 mã, khiến việc xây dựng danh mục đầu tư đa dạng hóa (top 30%) bị phá sản.

---

## 4. QUY TRÌNH THỰC HIỆN ĐỢT 2: PHÂN CỤM LẠI V2 VÀ HƯỚNG CHÍNH THỨC A V4 (K=3)

Nhằm khắc phục triệt để các sai lệch trên, ngày 25/10/2026, Project Owner đã phê duyệt kế hoạch phân cụm lại (Clustering Rework v2).

### 4.1. Mã nguồn và Kiến trúc thực thi
* **Module lõi:** [src/delta_t1/experiments/clustering_rework_v2.py](src/delta_t1/experiments/clustering_rework_v2.py)
* **Script điều phối:** [scripts/run_clustering_rework_v2.py](scripts/run_clustering_rework_v2.py)
* **Cấu hình thực nghiệm toàn kỳ:** [configs/experiments/clustering_rework_v2.json](configs/experiments/clustering_rework_v2.json)
* **Cấu hình kiểm chứng Development:** [configs/experiments/clustering_rework_v2_dev.json](configs/experiments/clustering_rework_v2_dev.json)

### 4.2. Bốn cải tiến phương pháp cốt lõi
1. **Lọc thanh khoản trước khi phân cụm (Liquidity Eligibility Filter):**
   * Tách nhóm cổ phiếu kém thanh khoản (>50% phiên không khớp trong 63 phiên gần nhất hoặc giá trị giao dịch bình quân 21 phiên < 10 triệu VNĐ/ngày) ra khỏi tập huấn luyện.
   * Các mã này được gắn nhãn riêng `ILLIQUID` (-1). Mô hình chỉ fit trên các mã có giao dịch thực thụ (liquid pool), sau đó gán các mã kém thanh khoản về tâm cụm gần nhất.
2. **Bổ sung đặc trưng động lượng giảm:**
   * Mở rộng từ 8 lên 9 đặc trưng: bổ sung `downside_vol_63` (đo độ lệch chuẩn phần lợi suất âm hóa năm, công thức `sqrt(mean(min(r, 0)^2)) * sqrt(252)`).
3. **Không gian biến đổi T1 (Transform T1):**
   * Đưa đặc trưng thanh khoản về thang log: `log1p(liquidity_21)`.
   * Cắt đuôi ngoại lai (Winsorization) tại phân vị 1% và 99% để triệt tiêu ảnh hưởng của các mã đột biến.
   * Chuẩn hóa z-score per-snapshot.
4. **Khảo sát mở rộng 4 thuật toán với k từ 3 đến 8:**
   * Huấn luyện quét đồng thời: K-Means, PCA (giữ 80% phương sai) + K-Means, Ward Hierarchical, và Gaussian Mixture Models (GMM).
   * Lựa chọn mô hình tối ưu theo tổng hợp thứ hạng trung bình của 5 tiêu chí: Median Silhouette, Median Davies-Bouldin, Median Calinski-Harabasz, Độ ổn định lấy mẫu con 90% (Subsample Stability ARI >= 0.8), và Độ ổn định thời gian (Temporal ARI).

### 4.3. Xác nhận tính khách quan trên giai đoạn Development
Để bảo đảm tính tuân thủ nghiên cứu (không nhìn trước vào Holdout 2024–2025), thực nghiệm `run_clustering_rework_v2.py --config configs/experiments/clustering_rework_v2_dev.json` đã được chạy lại với điều kiện chặn cứng `until: "2023-12-29"`:
* Khi chỉ nhìn dữ liệu Development (2019–2023): **k = 3** vẫn là số cụm tối ưu được lựa chọn.
* PCA + K-Means đạt hạng trung bình 2,40; K-Means đạt hạng 2,60 (hai thuật toán có chất lượng tương đương với cùng Silhouette 0,276 và độ ổn định 0,98 / 0,96).
* Kết luận: Lựa chọn **k = 3** hoàn toàn đứng vững từ giai đoạn Development mà không phụ thuộc vào dữ liệu ngoại mẫu.

### 4.4. Bảng tổng hợp đối sánh chi tiết 4 thuật toán ở Đợt 2 (Market Model)
Toàn bộ 4 thuật toán phân cụm đã được quét đối sánh độc lập trên không gian đặc trưng T1 (9 đặc trưng thị trường sau lọc thanh khoản nhẹ `A_light_dvol`) qua 60 snapshot giai đoạn Development (2019–2023) và kiểm chứng toàn kỳ 84 snapshot (2019–2025):

| Thuật toán | Cấu hình k tối ưu | Trạng thái Cổng chấp nhận (Admissible) | Điểm hạng 5 tiêu chí (Rank Score) | Median Silhouette (cao là tốt) | Median Davies–Bouldin (thấp là tốt) | Độ ổn định lấy mẫu con 90% (ARI) | Độ ổn định thời gian (Temporal ARI) | Đánh giá & Kết luận |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **PCA + K-Means** (giữ 80% phương sai) | **k = 3** | **ĐẠT (Admissible)** | **2,40**<br>(Hạng 1 trên Dev) | **0,276** | **1,52** | **0,98** | **0,55** | Dẫn đầu về điểm hạng đa tiêu chí trên Development; giảm chiều giúp triệt tiêu nhiễu tương quan chéo giữa các kỳ động lượng. |
| **K-Means Baseline** (chuẩn deterministic) | **k = 3** | **ĐẠT (Admissible)** | **2,60**<br>(Hạng 2 trên Dev,<br>Hạng 1 toàn kỳ) | **0,276** | **1,52** | **0,96** | **0,55** | **CHỌN CHÍNH THỨC (A v4)**: Hòa sát nút với PCA+K-Means, đạt chất lượng hình học và ổn định tương đương; cấu trúc tối giản theo Occam's Razor, dễ giải thích trực tiếp. |
| **Ward Hierarchical** (liên kết phương sai) | k = 3..8 | **KHÔNG ĐẠT (Failed Gate)** | Không xếp hạng | ~0,240 | ~1,65 | **< 0,70**<br>(Trượt ngưỡng >= 0.80) | 0,48 | Bị loại ở cổng kiểm định: thuật toán ngưng tụ phân cấp rất nhạy cảm với mẫu con, hay tạo cụm phân cấp lệch cỡ vi phạm quy tắc an toàn >= 5% số mã. |
| **Gaussian Mixture Models (GMM)** | k = 3..8 | **KHÔNG TỐI ƯU (Rank > 3.50)** | > 3,50 | ~0,180 | ~1,85 | 0,65 – 0,75 | 0,40 | Xếp hạng chót: ma trận hiệp phương sai đầy đủ (full covariance) trên 9 chiều bị overfit vào phân bố đuôi dày của lợi suất tài chính; phân tách hình học kém. |

* **Giải thích quy tắc xếp hạng 5 tiêu chí:** Trong các cấu hình vượt qua Cổng chấp nhận (Admissible: cụm nhỏ nhất >= 5% số mã ở >= 80% số snapshot và Độ ổn định lấy mẫu con trung vị >= 0.80), mỗi cấu hình được tính thứ hạng (1 là tốt nhất) trên 5 chỉ số: Silhouette (cao), Davies–Bouldin (thấp), Calinski–Harabasz (cao), Độ ổn định lấy mẫu con (cao), và ARI thời gian (cao). Điểm Rank Score là trung bình cộng thứ hạng của 5 chỉ số (điểm càng thấp xếp hạng càng cao).

---

## 5. KẾT QUẢ ĐỐI CHỨNG CÔNG BẰNG GIỮA ĐỢT 1 VÀ ĐỢT 2

Thực nghiệm đối chứng công bằng được xây dựng tại script [scripts/compare_m2_vs_rework.py](scripts/compare_m2_vs_rework.py), đánh giá trên cùng tập mã cổ phiếu hợp lệ qua 84 tháng trong 2 không gian đặc trưng S1 và S2.

Báo cáo kết quả chi tiết tại [artifacts/reports/m2-vs-rework-v1/report.md](artifacts/reports/m2-vs-rework-v1/report.md):

### 5.1. Bảng đối chiếu số liệu tổng hợp

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

### 5.2. Đánh giá chuyên sâu về kết quả

1. **Về cấu trúc hình học và tính thực chất:**  
   Trong không gian log S2, Silhouette của Đợt 2 đạt **0,24**, cao hơn gấp đôi so với **0,11** của Đợt 1. Cấu trúc cụm của Đợt 2 có **93% độ phân tách đến từ Động lượng và Rủi ro** (54% + 39%), chứng minh mô hình đã phân loại đúng bản chất trạng thái thị trường của cổ phiếu chứ không còn bị chi phối bởi quy mô giao dịch.
2. **Về tính khả dụng cho Milestone M3:**  
   Với cụm nhỏ nhất chiếm trung vị 14,0% – 14,4% (khoảng 100 đến 120 mã trong tập giao dịch), mô hình Đợt 2 cung cấp một tập ứng viên (Candidate Universe) đủ dày và phân phối đều qua 84 tháng, loại bỏ hiện tượng thiếu hụt cổ phiếu khi áp dụng các bộ lọc tài chính ở M3.
3. **Về tính ổn định thời gian (ARI):**  
   Đợt 1 có ARI thời gian cao hơn (0,74 so với 0,55) vì quy mô vốn hóa/thanh khoản của doanh nghiệp là yếu tố quán tính ít thay đổi theo tháng. Ngược lại, Đợt 2 phản ánh động lượng giá và rủi ro biến động, do đó việc các cổ phiếu chuyển dịch giữa cụm dẫn dắt (Leading) và cụm tụt hậu (Lagging) qua các chu kỳ thị trường là diễn biến tự nhiên, hợp lý về mặt kinh tế học tài chính.

---

## 6. QUYẾT ĐỊNH KIẾN TRÚC VÀ TRẠNG THÁI BÀN GIAO (D-DIR-01)

Dựa trên toàn bộ bằng chứng toán học và thực nghiệm đối chứng, ngày 26/10/2026, Project Owner đã chính thức ban hành **Quyết định D-DIR-01** (ghi nhận tại [docs/DECISIONS.md](docs/DECISIONS.md)):

1. **Mô hình thị trường chính thức:**
   * Chọn mô hình **A của Bundle v4 (K-Means, k = 3, 9 đặc trưng, lọc thanh khoản nhẹ, biến đổi T1)** làm mô hình chuẩn duy nhất của Milestone M2 để tích hợp sang Milestone M3.
   * Dữ liệu nhãn cụm, centroid, profile và tọa độ trực quan hóa được đóng gói bất biến vào cơ sở dữ liệu `terminal.sqlite` tại [data/web/delta-intelligence-v4/](data/web/delta-intelligence-v4).
2. **Lưu trữ hướng cũ (LEGACY Archive):**
   * Toàn bộ kết quả bàn giao của Đợt 1 (M2 K=2) trong thư mục [M2/](M2) được đánh dấu là **LEGACY**.
   * Giữ nguyên mã nguồn, notebook và artifact của Đợt 1 để phục vụ mục đích truy vết khoa học, đối chứng và tái lập kết quả lịch sử; không sử dụng làm đầu vào cho các phát triển mới.
3. **Bàn giao sang Milestone M3:**
   * Kế hoạch M3 tại [docs/M3_PLAN.md](docs/M3_PLAN.md) kế thừa trực tiếp nhãn cụm A v4 (k = 3).
   * Cụm dẫn dắt thị trường được xác định cơ học theo snapshot: chọn cụm có trung vị `mom_126` cao nhất; nếu hòa chọn cụm có trung vị `mdd_126` nông hơn (theo đề xuất Q5 trong M3 Plan).
   * Engine mô phỏng và backtest tại [src/delta_t1/m3/](src/delta_t1/m3) đã hoàn thành và vượt qua 25 bài kiểm thử đơn vị tự động.

---

## 7. TỔNG HỢP NỘI DUNG ĐƯA VÀO SLIDE BÁO CÁO (SLIDE-READY HIGHLIGHTS)

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
   * *Nguyên lý Occam's Razor:* Hai thuật toán hòa sát nút về chất lượng hình học (Silhouette cùng 0,276; Davies–Bouldin cùng 1,52; ARI thời gian cùng 0,55; ổn định mẫu con 0,98 vs 0,96).
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
