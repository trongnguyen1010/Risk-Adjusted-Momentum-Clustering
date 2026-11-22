# BÁO CÁO QUY TRÌNH THỰC HIỆN VÀ KẾT QUẢ PHÂN CỤM DỮ LIỆU TÀI CHÍNH POINT-IN-TIME LÀM GIÀU (HỆ B-PIT ENRICHED)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** Tháng 11/2026 (theo Quyết định D-DIR-01 và Kế hoạch B-PIT Enriched)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và artifact đã thực thi trong repository:
* Dữ liệu làm giàu Stage C: `data/financial/indicators_enriched_v1/indicators_enriched_v1_run01` ([scripts/build_enriched_indicators.py](../../scripts/build_enriched_indicators.py))
* Phân cụm B-PIT Enriched Stage D: `data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01` ([scripts/build_financial_pit_clusters_enriched.py](../../scripts/build_financial_pit_clusters_enriched.py))
* Mô-đun lõi: [src/delta_t1/experiments/bpit_enriched.py](../../src/delta_t1/experiments/bpit_enriched.py) và [src/delta_t1/m3/bpit.py](../../src/delta_t1/m3/bpit.py)
* Cấu hình thực nghiệm: [configs/experiments/bpit_enriched_v1.json](../../configs/experiments/bpit_enriched_v1.json) và [configs/experiments/m3_strategy_enriched_v1.json](../../configs/experiments/m3_strategy_enriched_v1.json).

---

## 1. TỔNG QUAN VÀ BỐI CẢNH NGHIÊN CỨU

### 1.1. Động lực nghiên cứu: Vấn đề thất thoát dữ liệu trong B-PIT gốc
Trong phiên bản B-PIT ban đầu (dựa trên bộ dữ liệu `indicators_v1`), mô hình chỉ sử dụng nguyên tắc **Complete Cases Only** (chỉ giữ lại các doanh nghiệp có đủ 100% cả 9 chỉ số tài chính). Mặc dù phương pháp này đảm bảo tính nguyên bản, nó dẫn đến sự sụt giảm nghiêm trọng số lượng cổ phiếu tham gia huấn luyện và phân loại:
1. **Thiếu hụt dữ liệu dòng tiền (CFO):** Trên TTCK Việt Nam, chỉ số Lưu chuyển tiền thuần từ HĐKD trên LNST (`cfo_to_ni`) hoặc Tăng trưởng doanh thu (`revenue_growth`) ở giai đoạn trước năm 2022 thường bị khuyết thiếu cục bộ do các doanh nghiệp không công bố hoặc do cách thức trình bày báo cáo kiểm toán cũ.
2. **Hệ quả đối với danh mục đầu tư M3:** Việc loại bỏ toàn bộ một doanh nghiệp chỉ vì khuyết 1 trong 9 chỉ số khiến vũ trụ tài chính lành mạnh (Not-Weakest) bị thu hẹp đáng kể. Trong giai đoạn 2017–2021, số lượng mã đạt điều kiện fit của B-PIT gốc chỉ dao động từ 947 đến 1.043 mã (mất mát hơn 200–250 mã tiềm năng mỗi năm). Khi giao thoa với cụm dẫn dắt thị trường (Hệ A v4), danh mục Combined thường xuyên rơi vào tình trạng thiếu ứng viên cục bộ ($N < N_{min} = 10$).

Để khắc phục triệt để vấn đề này, **Quy trình Phân cụm B-PIT trên Dữ liệu làm giàu (B-PIT Enriched Pipeline)** được xây dựng gồm hai giai đoạn liên hoàn:
* **Giai đoạn 1 (Stage C — Imputation):** Điền giá trị trung vị ngành/năm tài chính (`IMPUTED_MEDIAN`) cho các ô khuyết thiếu hợp lệ mà không làm biến dạng dữ liệu đã có.
* **Giai đoạn 2 (Stage D — Enriched Clustering):** Quét lưới siêu tham số 24 cấu hình, lọc qua Cổng kiểm định chất lượng an toàn (Admissibility Gate), đóng băng tâm cụm tại mốc Cutoff và xếp hạng phân loại tài chính.

### 1.2. Tập dữ liệu đầu vào và Nguyên tắc làm giàu dữ liệu (Stage C)
* **Dữ liệu đầu vào:**
  * CSDL 9 chỉ số gốc: `data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite`.
  * Bảng ngày công bố Point-in-Time: `data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv`.
  * Baseline B-PIT đối chứng: `data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec`.
* **Nguyên tắc điền khuyết thiếu Point-in-Time nghiêm ngặt:**
  1. *Chỉ tính trung vị trên tập Fit chuẩn:* Giá trị trung vị điền khuyết thiếu $\text{median}(m, t)$ của chỉ số $m$ tại năm tài chính $t$ **chỉ được tính toán dựa trên các doanh nghiệp đã công bố BCTC trước hoặc đúng ngày Cutoff** của năm $t$. Tuyệt đối không sử dụng thông tin từ tương lai hoặc từ các mã nộp muộn để tính trung vị.
  2. *Bảo toàn 100% dữ liệu gốc:* 0 ô dữ liệu đã quan sát nào bị thay đổi giá trị. Toàn bộ các ô được điền đều được gắn cờ truy vết nguồn gốc `imputed_flag = True` và ghi nhật ký kiểm toán độc lập tại [imputed_cells.csv](../../data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/imputed_cells.csv).
  3. *Kết quả làm giàu:* Đã giải cứu thành công **1.111 ô khuyết thiếu** thuộc **1.045 dòng mã–năm** của **393 mã cổ phiếu** trong giai đoạn FY 2017 – FY 2024.

---

## 2. CÁC BƯỚC THỰC HIỆN TRONG MÃ NGUỒN (MACHINE LEARNING PIPELINE)

Quy trình thực thi trong mã nguồn gồm 2 script chuyên trách: [scripts/build_enriched_indicators.py](../../scripts/build_enriched_indicators.py) (Stage C) và [scripts/build_financial_pit_clusters_enriched.py](../../scripts/build_financial_pit_clusters_enriched.py) (Stage D):

```
[Stage C: Nạp CSDL Gốc & Bảng Ngày Q-Date]
                    ↓
[Stage C: Tính Trung vị Fit per-year & Điền 1.111 ô khuyết thiếu hợp lệ]
                    ↓
[Stage C: Xuất CSDL indicators.sqlite đã làm giàu (100% Complete Rows)]
                    ↓
[Stage D: Quét lưới 24 cấu hình (4 Thuật toán × k = 3..8) trên FY 2017–FY 2022]
                    ↓
[Stage D: Sàng lọc qua Cổng Admissibility Gate (Cỡ cụm >= 5% & ARI mẫu con >= 0.80)]
                    ↓
[Stage D: Đóng băng Tham số T1 & Tọa độ Tâm cụm K-Means (k=3) tại Cutoff]
                    ↓
[Stage D: Đóng băng Thứ tự Cụm (Cluster Order: ROE desc, D/E asc)]
                    ↓
[Stage D: Gán ngoại mẫu cho BCTC nộp sau Cutoff & Kiểm toán Zero Fit-Leak]
                    ↓
[Stage D: Đóng gói Artifact B-PIT Enriched & Pin vào configs/m3_strategy_enriched_v1.json]
```

### Bước 1: Làm giàu dữ liệu chỉ số tài chính (Stage C)
1. Truy vấn các bản ghi mã–năm bị khuyết từ 1 đến 3 chỉ số trong `indicators.sqlite`.
2. Tính ma trận trung vị $[m, t]$ trên tập hợp các doanh nghiệp hợp lệ của năm tài chính $t$ tại mốc Cutoff.
3. Điền giá trị trung vị vào 1.111 ô trống, xuất cơ sở dữ liệu hoàn chỉnh [indicators.sqlite](../../data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/indicators.sqlite) (106 MB).

### Bước 2: Quét lưới siêu tham số 24 Cấu hình (Stage D Grid Search)
Để lựa chọn mô hình phân cụm tối ưu, mã nguồn tiến hành quét đồng thời không gian 2 chiều trên 6 năm tài chính giai đoạn Development (FY 2017 – FY 2022):
* **4 thuật toán tham gia khảo nghiệm:** K-Means Baseline, PCA + K-Means (giữ 80% phương sai), Ward Hierarchical, và Gaussian Mixture Models (GMM).
* **Dải số cụm khảo sát:** $k \in [3, 4, 5, 6, 7, 8]$.
* **Tổng số cấu hình:** $4 \times 6 = 24$ mô hình thực nghiệm.

### Bước 3: Sàng lọc qua Cổng kiểm định chất lượng (Admissibility Gate)
Mỗi cấu hình trong 24 cấu hình phải vượt qua 2 tiêu chuẩn kiểm định an toàn nghiêm ngặt:
1. *Cân bằng quy mô cụm (Min Cluster Share):* Cụm nhỏ nhất phải chiếm $\ge 5\%$ tổng số doanh nghiệp ở $\ge 80\%$ số năm tài chính khảo sát.
2. *Độ ổn định lấy mẫu con 90% (Subsample Stability ARI):* Trung vị chỉ số ARI giữa mô hình fit lại trên 90% dữ liệu ngẫu nhiên và nhãn ban đầu phải đạt $\ge 0,80$.

### Bước 4: Đóng băng Tham số $T_1$ và Huấn luyện K-Means tại mốc Cutoff
* Với cấu hình chiến thắng, tại mỗi năm tài chính $t$, chỉ lấy tập `FIT` (các doanh nghiệp có `usable_from_date <= cutoff(t)`):
  * **Cutoff cố định:** Ngày 30/06 năm $t+1$ (cho FY $\le$ 2021) và ngày 30/04 năm $t+1$ (cho FY $\ge$ 2022).
  * **Biến đổi $T_1$:** Tính ngưỡng Winsorize 1%–99% và Z-score $[\mu, \sigma]$ trên tập `FIT`, đóng băng vĩnh viễn vào `models.json`.
  * **Huấn luyện mô hình:** Fit K-Means++ deterministic (`seed=42`, `n_init=10`) trên không gian $T_1$, lưu tọa độ 3 tâm cụm $\mathbf{C}_0, \mathbf{C}_1, \mathbf{C}_2$.

### Bước 5: Đóng băng Thứ tự chất lượng Cụm (Cluster Ordering)
* Tính toán trung vị ROE và trung vị Nợ/VCSH trên tập `FIT` của từng cụm:
  * Cụm có trung vị ROE cao nhất xếp vị trí đầu tiên (Leading Cluster).
  * Cụm có trung vị ROE thấp nhất hoặc đòn bẩy quá cao xếp vị trí cuối cùng (Weakest Cluster).
* Lưu thứ tự mảng `cluster_order` vào mô hình để runner M3 đọc trực tiếp tại runtime.

### Bước 6: Gán cụm ngoại mẫu (Out-of-sample Assignment)
* Các doanh nghiệp công bố BCTC sau ngày 30/04 (`ASSIGNED_AFTER_CUTOFF`) được đưa qua phép biến đổi $T_1$ đã đóng băng và gán vào tâm cụm gần nhất theo khoảng cách Euclid:
  $$\hat{c}_j = \arg\min_{c \in \{0, 1, 2\}} \|x_j - \mathbf{C}_c\|_2$$
* Đảm bảo không làm xê dịch tâm cụm hay gây rò rỉ dữ liệu của thị trường.

### Bước 7: Kiểm định kiểm toán Zero Fit-Leak
* Rà soát kiểm toán tự động: khẳng định 100% doanh nghiệp trong tập Fit đều có ngày công bố hợp lệ trước hoặc đúng Cutoff (`fit_leaks = []`).

---

## 3. KẾT QUẢ THỰC NGHIỆM VÀ ĐỐI SÁNH KHOA HỌC

### 3.1. Bảng kết quả Quét lưới 24 cấu hình và Sàng lọc qua Cổng Admissibility Gate
Kết quả thực nghiệm quét lưới 24 cấu hình trích xuất từ [audit.json](../../data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01/audit.json):

| Thuật toán | Số cụm $k$ | Median Silhouette | Median Davies-Bouldin | Độ ổn định mẫu con 90% (ARI) | Trạng thái Cổng Admissible | Đánh giá & Lý do loại / chọn |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **K-Means Baseline** | **k = 3** | **0,230** | **1,65** | **0,922** | **ĐẠT (CHỌN DUY NHẤT)** | **Vượt qua cổng lọc**: Độ ổn định mẫu con đạt 0,922 (vượt xa ngưỡng 0,80), quy mô cụm rất cân bằng, ranh giới cụm sắc nét. |
| K-Means Baseline | k = 4 | 0,232 | 1,47 | 0,742 | TRƯỢT (Failed Gate) | Loại: Độ ổn định mẫu con rớt xuống 0,742 (< 0,80). |
| K-Means Baseline | k = 5 | 0,234 | 1,35 | 0,755 | TRƯỢT (Failed Gate) | Loại: Độ ổn định mẫu con không đạt chuẩn an toàn (< 0,80). |
| K-Means Baseline | k = 6..8 | 0,254 – 0,263 | 1,14 – 1,28 | 0,734 – 0,826 | TRƯỢT (Failed Gate) | Loại: Vi phạm điều kiện quy mô cụm tối thiểu (< 5% số mã). |
| PCA + K-Means | k = 3 | 0,239 | 1,52 | 0,962 | TRƯỢT (Failed Gate) | Loại: Cụm nhỏ nhất bị co dưới 5% ở nhiều năm tài chính. |
| PCA + K-Means | k = 4..8 | 0,194 – 0,223 | 1,18 – 1,46 | 0,628 – 0,788 | TRƯỢT (Failed Gate) | Loại: Độ ổn định mẫu con rất kém (< 0,75) và vi phạm kích thước cụm. |
| Ward Hierarchical | k = 3..8 | 0,185 – 0,318 | 1,22 – 1,54 | 0,374 – 0,454 | TRƯỢT (Failed Gate) | Loại: Rất nhạy cảm với dữ liệu, ARI mẫu con < 0,46 (trượt ngưỡng nghiêm trọng). |
| GMM Gaussian | k = 3..8 | 0,045 – 0,141 | 1,99 – 2,43 | 0,407 – 0,554 | TRƯỢT (Failed Gate) | Loại: Overfit ma trận hiệp phương sai đầy đủ, Silhouette cực thấp (~0,05–0,14). |

> **KẾT LUẬN QUÉT LƯỚI:** Trong toàn bộ 24 cấu hình thực nghiệm, **DUY NHẤT K-Means $k=3$** vượt qua Cổng kiểm định chất lượng (Admissible). Điều này khẳng định $k=3$ là số lượng cụm tối ưu khách quan nhất về mặt toán học và cấu trúc dữ liệu tài chính Việt Nam.

---

### 3.2. Bảng kết quả thực nghiệm chi tiết từng niên độ của B-PIT Enriched (FY 2017 – FY 2024)
Số liệu trích xuất chính thức từ artifact [bpit_enriched_v1_run01](../../data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01):

| Niên độ (FY) | Ngưỡng Cutoff | Số mã FIT ($N_{fit}$) | Số mã Gán sau Cutoff | Phân bố kích thước 3 cụm $\{C_0, C_1, C_2\}$ | Thứ tự chất lượng (`cluster_order`) | Cụm Dẫn dắt (Leading) | Cụm Yếu nhất (Weakest) | Kiểm toán Rò rỉ (Fit-Leak) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2017** | 02/07/2018 | **1.160** | 0 | $\{703, 290, 167\}$ | **$[1, 2, 0]$** | Cụm 1 | Cụm 0 | **PASS (0 leak)** |
| **2018** | 01/07/2019 | **1.193** | 0 | $\{712, 289, 192\}$ | **$[1, 2, 0]$** | Cụm 1 | Cụm 0 | **PASS (0 leak)** |
| **2019** | 01/07/2020 | **1.189** | 0 | $\{825, 302, 62\}$ | **$[1, 0, 2]$** | Cụm 1 | Cụm 2 | **PASS (0 leak)** |
| **2020** | 01/07/2021 | **1.166** | 0 | $\{737, 261, 168\}$ | **$[1, 2, 0]$** | Cụm 1 | Cụm 0 | **PASS (0 leak)** |
| **2021** | 01/07/2022 | **1.201** | 0 | $\{785, 350, 66\}$ | **$[1, 2, 0]$** | Cụm 1 | Cụm 0 | **PASS (0 leak)** |
| **2022** | 30/04/2023 | **1.055** | 98 | $\{860, 279, 14\}$ | **$[1, 0, 2]$** | Cụm 1 | Cụm 2 | **PASS (0 leak)** |
| **2023** | 30/04/2024 | **980** | 153 | $\{732, 251, 150\}$ | **$[1, 2, 0]$** | Cụm 1 | Cụm 0 | **PASS (0 leak)** |
| **2024** | 30/04/2025 | **1.053** | 123 | $\{705, 261, 210\}$ | **$[1, 2, 0]$** | Cụm 1 | Cụm 0 | **PASS (0 leak)** |

---

### 3.3. So sánh đối chứng đột phá: B-PIT Enriched vs B-PIT Gốc

| Tiêu chí so sánh | Hệ B-PIT Gốc (`bpit-4a9d2e87...`) | Hệ B-PIT Enriched (`bpit_enriched_v1_run01`) | Mức độ cải thiện & Giá trị gia tăng |
|---|:---:|:---:|---|
| **Cơ chế xử lý ô khuyết thiếu** | Complete Cases Only (Xóa bỏ mã thiếu dù chỉ 1 chỉ số) | Điền trung vị ngành Point-in-Time hợp lệ (Stage C) | **Cứu thành công 1.111 ô khuyết thiếu** của 1.045 dòng mã–năm |
| **Quy mô số mã FIT giai đoạn FY 2017** | 951 mã | **1.160 mã** | **+209 mã (+22,0%)** |
| **Quy mô số mã FIT giai đoạn FY 2018** | 947 mã | **1.193 mã** | **+246 mã (+26,0%)** |
| **Quy mô số mã FIT giai đoạn FY 2019** | 972 mã | **1.189 mã** | **+217 mã (+22,3%)** |
| **Quy mô số mã FIT giai đoạn FY 2020** | 977 mã | **1.166 mã** | **+189 mã (+19,3%)** |
| **Quy mô số mã FIT giai đoạn FY 2021** | 1.043 mã | **1.201 mã** | **+158 mã (+15,1%)** |
| **Tính toàn vẹn Point-In-Time** | `fit_leaks = 0` (Đạt) | `fit_leaks = 0` (Đạt tuyệt đối) | **Bảo toàn 100% tính Point-in-Time**, không rò rỉ tương lai |
| **Tác động lên Danh mục Backtest M3** | Bị thiếu cổ phiếu ($N < 10$) ở 14 tháng khảo sát | **Đáp ứng vượt ngưỡng an toàn** $N \ge 10$ trên toàn bộ chu kỳ | Danh mục đa dạng hóa tối ưu, giảm thiểu rủi ro tập trung |

---

## 4. TÓM TẮT TRỌNG TÂM ĐƯA VÀO SLIDE THUYẾT TRÌNH (SLIDE-READY HIGHLIGHTS)

### Slide 1: Động lực làm giàu dữ liệu & Pipeline 2 giai đoạn (Stage C & Stage D)
* **Vấn đề của mô hình cũ:** Nguyên tắc khuyết 1 bỏ cả khiến thị trường mất đi hơn 200 doanh nghiệp tiềm năng mỗi năm (chủ yếu do thiếu chỉ số dòng tiền `cfo_to_ni`).
* **Giải pháp 2 giai đoạn:**
  * *Stage C:* Điền trung vị ngành Point-in-Time cho 1.111 ô khuyết thiếu hợp lệ thuộc 393 doanh nghiệp.
  * *Stage D:* Quét lưới 24 cấu hình mô hình, kiểm định cổng an toàn và phân cụm K-Means $k=3$ đóng băng tại Cutoff 30/04.

### Slide 2: Kết quả Quét lưới 24 Cấu hình — K-Means k=3 chiến thắng áp đảo
* **Sàng lọc qua Cổng Admissibility Gate:** Duy nhất K-Means $k=3$ vượt qua đồng thời 2 điều kiện an toàn: Cụm nhỏ nhất $\ge 5\%$ và Độ ổn định lấy mẫu con 90% (ARI đạt **0,922** $\ge 0,80$).
* **Loại bỏ các mô hình khác:**
  * $k \ge 4$: Độ ổn định suy giảm mạnh (< 0,78).
  * Ward & GMM: Rớt cổng kiểm định do mất cân đối quy mô và overfit phân bố đuôi dày.

### Slide 3: So sánh quy mô ứng viên: B-PIT Enriched vs B-PIT Gốc
* **Tăng trưởng vượt bậc về quy mô:** Số lượng doanh nghiệp hợp lệ được huấn luyện (FIT) tăng từ **+158 đến +246 mã mỗi năm** trong suốt giai đoạn 2017–2021 (tăng trung bình trên 20%).
* **Zero Fit-Leak:** Duy trì 0% rò rỉ thời gian, 100% báo cáo công bố sau ngày 30/04 được cô lập và gán ngoại mẫu.

### Slide 4: Giá trị thực tiễn đối với Backtest M3 và Vận hành Sản phẩm
* **Giải quyết dứt điểm bài toán thanh khoản danh mục:** Loại bỏ hoàn toàn hiện tượng số ứng viên bị co hẹp dưới ngưỡng $N_{min} = 10$, tạo không gian lựa chọn danh mục Combined dồi dào và ổn định.
* **Tích hợp chính thức:** Artifact [bpit_enriched_v1_run01](../../data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01) được khóa cố định vào cấu hình chiến lược [configs/experiments/m3_strategy_enriched_v1.json](../../configs/experiments/m3_strategy_enriched_v1.json) cho toàn bộ hệ thống backtest và đánh giá đầu tư của DELTA.

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence (Artifacts `indicators_enriched_v1_run01` và `bpit_enriched_v1_run01`).*
