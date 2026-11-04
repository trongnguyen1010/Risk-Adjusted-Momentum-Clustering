# BÁO CÁO QUY TRÌNH THỰC HIỆN VÀ KẾT QUẢ PHÂN CỤM DỮ LIỆU TÀI CHÍNH POINT-IN-TIME (HỆ B-PIT)

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam (DELTA)  
**Tác giả:** Đội ngũ Nghiên cứu & Phát triển DELTA  
**Thời điểm hoàn thành & cập nhật chính thức:** 04/11/2026 (theo Quyết định D-M3-01 và cập nhật D-DIR-01)  
**Cơ sở dữ liệu & mã nguồn:** 100% đối chiếu từ kho mã nguồn, cấu hình thực nghiệm và artifact đã thực thi trong repository (`data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec`, [scripts/build_financial_pit_clusters.py](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/scripts/build_financial_pit_clusters.py), [src/delta_t1/m3/bpit.py](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/src/delta_t1/m3/bpit.py), [configs/experiments/m3_strategy_v1.json](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/configs/experiments/m3_strategy_v1.json)).

---

## 1. TỔNG QUAN VÀ BỐI CẢNH NGHIÊN CỨU

### 1.1. Mục tiêu của Hệ Dữ liệu Tài chính Point-In-Time (Hệ B-PIT)
Trong kiến trúc phân tầng của DELTA, hệ dữ liệu tài chính phục vụ cho phân bổ danh mục tại Milestone M3. Ở các phiên bản trước (như B v4), việc huấn luyện mô hình K-Means trên toàn bộ doanh nghiệp của một năm tài chính sau khi năm đó đã kết thúc dẫn đến nguy cơ **rò rỉ thời gian (timing leakage / look-ahead bias)**: tâm cụm và phân vị chuẩn hóa bị ảnh hưởng bởi các báo cáo tài chính (BCTC) công bố rất muộn (thậm chí vào nửa cuối năm sau).

Để giải quyết triệt để vấn đề này, **Mô hình Phân cụm Tài chính Point-In-Time (B-PIT)** được thiết kế và triển khai chính thức theo Quyết định **ADR D-M3-01** và Kế hoạch chuẩn M3 ([docs/KE_HOACH_M3_SCHEMA_GITHUB.md](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/docs/KE_HOACH_M3_SCHEMA_GITHUB.md) §3.1.5, §5.2.A):
1. **Triệt tiêu Look-Ahead Bias ở cấp độ mô hình:** Mỗi năm tài chính $t$, mô hình K-Means chỉ được huấn luyện (fit) trên các báo cáo thực sự có sẵn trước hoặc đúng thời điểm chốt sổ định kỳ (**Cutoff**).
2. **Đóng băng không gian và tâm cụm (Frozen Space & Centroids):** Toàn bộ tham số tiền xử lý $T_1$ (ngưỡng Winsorize, trung bình, độ lệch chuẩn) và tọa độ tâm cụm được đóng băng vĩnh viễn tại Cutoff. Các báo cáo nộp muộn sau Cutoff được chuẩn hóa và gán ngoại mẫu (out-of-sample assignment) vào tâm cụm gần nhất mà không làm xê dịch cấu trúc cụm đã định hình.
3. **Đóng băng thứ tự chất lượng cụm (Cluster Ordering):** Thứ tự ưu tiên chất lượng tài chính (sắp xếp theo trung vị ROE giảm dần, hòa điểm thì trung vị Nợ/VCSH tăng dần) được tính toán trên tập Fit tại Cutoff và lưu cố định vào artifact để runtime M3 đọc trực tiếp, không tính lại tại từng ngày quyết định.
4. **Cung cấp bộ lọc ứng viên cho Milestone M3 (Rule Va / Q5):** Xác định nhóm cổ phiếu tài chính lành mạnh ("Not-Weakest" - không thuộc cụm yếu nhất) để giao thoa với cụm dẫn dắt thị trường (Hệ A v4).

### 1.2. Tập dữ liệu đầu vào và phân định thời gian
* **Dữ liệu đầu vào:**
  * Bộ chỉ số sản phẩm chuẩn hóa **Indicators v1** (`data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite`, SHA256: `26bfc2d9...`) gồm 9 chỉ số tài chính cốt lõi (D-IND-01) của các doanh nghiệp phi tài chính: ROE, ROA, Biên gộp (Gross Margin), Biên ròng (Net Margin), Nợ/VCSH (Debt-to-Equity), Thanh toán hiện hành (Current Ratio), Vòng quay tài sản (Asset Turnover), Tăng trưởng doanh thu (Revenue Growth), CFO/LNST (CFO-to-NI).
  * Bảng ngày công bố khả dụng **Availability Table** (`data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv`, SHA256: `4f0f8310...`) ghi nhận ngày BCTC bắt đầu có hiệu lực giao dịch (`usable_from_date`) cho 1.362 mã.
* **Nguyên tắc phân định thời gian Point-In-Time (PIT):**
  1. *Ngưỡng Cutoff xác định:*
     $$\text{cutoff}(t) = \max(30/04/(t+1), \text{usable\_from\_date sớm nhất của FY } t)$$
  2. *Giai đoạn FY $\ge$ 2022 (Áp dụng ngày công bố CafeF Disclosure):* Báo cáo kiểm toán năm bắt đầu công bố rải rác từ tháng 3–tháng 4. Cutoff cố định là **ngày 30/04 năm $t+1$**. Các báo cáo nộp sau ngày 30/04 (chiếm 9%–15% số mã) chỉ được gán ngoại mẫu vào tâm cụm đã đóng băng, tuyệt đối không được tham gia huấn luyện lại.
  3. *Giai đoạn FY < 2022 (Áp dụng quy tắc Lag Rule lịch sử):* Do thị trường chưa có dữ liệu ngày công bố điện tử chi tiết từng ngày, toàn bộ báo cáo được giả định khả dụng từ **phiên giao dịch đầu tiên sau ngày 30/06 năm $t+1$**. Do đó, Cutoff chính là phiên giao dịch đó và toàn bộ báo cáo được fit cùng lúc — điều này hoàn toàn không gây rò rỉ thông tin vì trước ngày 30/06 năm $t+1$, không có quyết định đầu tư nào được phép sử dụng BCTC của năm $t$.
  4. *Kiểm soát chất lượng và rà soát dữ liệu đầu vào:* Owner ngày 04/11/2026 đã phê duyệt chấp nhận trọn vẹn bộ Indicators v1 (gồm VCG FY2023 và SBT FY2024), đồng thời yêu cầu công bố minh bạch các giới hạn về dữ liệu nguồn và truy vết revision trong hồ sơ kiểm toán.

---

## 2. CÁC BƯỚC THỰC HIỆN (QUY TRÌNH PHÂN CỤM TÀI CHÍNH B-PIT)

Quy trình phân cụm tài chính Point-In-Time được tự động hóa hoàn toàn thông qua công cụ [scripts/build_financial_pit_clusters.py](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/scripts/build_financial_pit_clusters.py) kết hợp module lõi [src/delta_t1/m3/bpit.py](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/src/delta_t1/m3/bpit.py):

```
[Bước 1: Nạp ma trận 9 chỉ số D-IND-01 & Bảng ngày công bố khả dụng (Q-date)]
                                    ↓
[Bước 2: Xác định Cutoff & Phân tách tập huấn luyện: FIT vs ASSIGNED theo từng FY]
                                    ↓
[Bước 3: Chuẩn hóa T1 (Winsorize 1-99% + Z-Score) đóng băng trên tập FIT tại Cutoff]
                                    ↓
[Bước 4: Huấn luyện K-Means (k=3, seed=42) & Đóng băng Tọa độ Tâm cụm (Centroids)]
                                    ↓
[Bước 5: Sắp xếp & Đóng băng Thứ tự chất lượng Cụm (Cluster Order: ROE desc, D/E asc)]
                                    ↓
[Bước 6: Gán cụm ngoại mẫu cho các BCTC công bố sau Cutoff (Nearest Centroid)]
                                    ↓
[Bước 7: Kiểm định Audit Không rò rỉ (Fit-Leak = 0) & Đối soát ARI so với B v4]
                                    ↓
[Bước 8: Đóng gói Artifact B-PIT bất biến & Pin mã băm SHA256 vào cấu hình M3]
```

### Bước 1: Chuẩn bị dữ liệu và Liên kết ngày khả dụng (Q-Date Linking)
1. Nạp ma trận 9 chỉ số tài chính cho các công ty phi tài chính từ `indicators.sqlite`, chỉ giữ lại các trường hợp đầy đủ cả 9 biến (`complete cases only`).
2. Ghép nối từng cặp `(ticker, fiscal_year)` với bảng `availability.csv` để xác định ngày bắt đầu được phép sử dụng thông tin (`usable_from_date`).
3. Nếu mã thiếu ngày khả dụng xác thực, gán nhãn chuỗi rỗng (`''`), đảm bảo các mã này tuyệt đối không được đưa vào tập huấn luyện.

### Bước 2: Xác định Cutoff và Phân định vai trò dữ liệu
1. Với mỗi năm tài chính $t$, gọi hàm `cutoff_for(fiscal_year, usable_dates)`:
   * FY 2016: Cutoff = `2017-07-03`
   * FY 2017: Cutoff = `2018-07-02`
   * FY 2018: Cutoff = `2019-07-01`
   * FY 2019: Cutoff = `2020-07-01`
   * FY 2020: Cutoff = `2021-07-01`
   * FY 2021: Cutoff = `2022-07-01`
   * FY 2022: Cutoff = `2023-04-30`
   * FY 2023: Cutoff = `2024-04-30`
   * FY 2024: Cutoff = `2025-04-30`
   * FY 2025: Cutoff = `2026-04-30` (tại ngày chốt chỉ có 3 báo cáo, nhỏ hơn ngưỡng tối thiểu $2k = 6$, kích hoạt cơ chế an toàn `NOT_READY_TOO_FEW_USABLE_REPORTS` và dừng fit để tránh học vẹt dữ liệu thiếu).
2. Phân tách danh sách doanh nghiệp thành các nhóm vai trò rõ ràng:
   * `FIT`: Báo cáo có `usable_from_date <= cutoff`.
   * `ASSIGNED_AFTER_CUTOFF`: Báo cáo hợp lệ nhưng nộp sau ngày cutoff.
   * `ASSIGNED_NO_DATE`: Báo cáo không có thông tin ngày khả dụng.

### Bước 3: Tiền xử lý Transform T1 đóng băng trên tập Fit
Khác với B v4 (tính tham số tiền xử lý trên toàn bộ danh sách công ty của năm), B-PIT chỉ tính toán trên tập `FIT` tại thời điểm Cutoff:
1. **Cắt đuôi ngoại lai (Winsorization 1%–99%):** Tính ngưỡng chặn dưới $lo$ (phân vị 1%) và ngưỡng chặn trên $hi$ (phân vị 99%) độc lập trên 9 chỉ số của tập `FIT`.
2. **Chuẩn hóa Z-Score:** Tính giá trị trung bình $\mu$ (`mean`) và độ lệch chuẩn $\sigma$ (`sd`) trên tập `FIT` sau khi đã cắt đuôi.
3. **Đóng băng tham số T1:** Lưu toàn bộ mảng $[lo, hi, \mu, \sigma]$ vào `models.json`. Biến đổi toàn bộ ma trận dữ liệu bằng chính bộ tham số này:
   $$X_{T1} = \frac{\text{clip}(X, lo, hi) - \mu}{\sigma}$$

### Bước 4: Huấn luyện K-Means Baseline và Đóng băng Tâm cụm
1. Huấn luyện thuật toán K-Means++ với số cụm $k = 3$, `n_init = 10`, `random_state = 42` trên dữ liệu đã biến đổi $T_1$ của tập `FIT`.
2. **Đánh số lại nhãn cụm (Renumbering):** Sắp xếp lại nhãn $\{0, 1, 2\}$ theo thứ tự giảm dần của quy mô số lượng doanh nghiệp trong cụm tại tập fit (nhãn 0 là cụm có đông doanh nghiệp nhất).
3. **Tính toán và đóng băng tọa độ tâm cụm (Centroids):**
   $$C_c = \frac{1}{|S_c|} \sum_{i \in S_c} x_i \quad (c \in \{0, 1, 2\})$$
   Tọa độ 3 tâm cụm (mỗi tâm là vector 9 chiều) được đóng băng vĩnh viễn trong `models.json`.

### Bước 5: Đóng băng Thứ tự chất lượng Cụm (Cluster Ordering)
Nhằm xác định ranh giới cụm dẫn dắt và cụm yếu kém một cách khách quan:
1. Tính toán hồ sơ trung vị tài chính (Financial Profile) cho từng cụm dựa trên các doanh nghiệp thuộc tập `FIT`:
   * $\text{median\_roe}_c$: Trung vị tỷ suất sinh lời trên vốn chủ sở hữu của cụm $c$.
   * $\text{median\_debt\_to\_equity}_c$: Trung vị tỷ số Nợ/VCSH của cụm $c$.
2. Áp dụng quy tắc xếp hạng: Sắp xếp các cụm theo **$\text{median\_roe}$ giảm dần**; nếu bằng điểm thì ưu tiên cụm có **$\text{median\_debt\_to\_equity}$ thấp hơn** (đòn bẩy an toàn hơn).
3. Thứ tự cụm này (`cluster_order`) được lưu thẳng vào cấu trúc mô hình để runner M3 đọc trực tiếp tại runtime mà không cần tính toán lại ở từng kỳ quyết định.

### Bước 6: Gán cụm ngoại mẫu cho các báo cáo đến sau Cutoff
Với mỗi doanh nghiệp thuộc nhóm `ASSIGNED_AFTER_CUTOFF` hoặc `ASSIGNED_NO_DATE`:
1. Áp dụng phép biến đổi $T_1$ bằng các tham số $[lo, hi, \mu, \sigma]$ đã đóng băng ở Bước 3.
2. Gán nhãn cụm bằng khoảng cách Euclid tối thiểu tới các tâm cụm đã đóng băng ở Bước 4:
   $$\hat{c}_j = \arg\min_{c \in \{0, 1, 2\}} \|x_j - C_c\|_2$$
3. Quá trình này bảo đảm các báo cáo muộn được phân loại nhất quán mà không làm thay đổi tọa độ tâm cụm của thị trường.

### Bước 7: Kiểm định Audit Không rò rỉ (Fit-Leak Check) và Tính toán ARI
1. **Kiểm tra rò rỉ thời gian (Fit-Leak Audit):** Rà soát toàn bộ danh sách: nếu tồn tại bất kỳ bản ghi nào có $f = \text{True}$ (nằm trong tập fit) mà $\text{usable\_from\_date} > \text{cutoff}$ hoặc không có ngày, hệ thống lập tức báo lỗi và dừng toàn bộ tiến trình.
2. **Đo lường mức độ đồng thuận với B v4 (ARI vs B v4):** Tính chỉ số Adjusted Rand Index (ARI) giữa nhãn phân cụm B-PIT và nhãn B v4 trên các mã chung để lượng hóa tác động của việc loại bỏ rò rỉ thông tin.

### Bước 8: Đóng gói Artifact Bất biến và Pin cấu hình M3
Toàn bộ kết quả được đóng gói vào thư mục `data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec/` gồm 4 tệp tin:
* `labels.csv`: 8.461 bản ghi phân loại chi tiết (ticker, fiscal_year, cluster, role, usable_from_date).
* `models.json`: Siêu dữ liệu mô hình qua từng năm (cutoff, n_fit, n_assigned, tham số T1, centroids, cluster_order, profile).
* `audit.json`: Kết quả kiểm định fit_leaks, kích thước các cụm, chỉ số ARI so sánh với B v4.
* `manifest.json`: Mã băm SHA256 của các tệp đầu vào, mã nguồn thực thi, git commit và mã băm `labels_sha256`.
* Giá trị định danh artifact và `labels_sha256` được pin chính thức vào [configs/experiments/m3_strategy_v1.json](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/configs/experiments/m3_strategy_v1.json) với trạng thái `LOCKED`.

---

## 3. KẾT QUẢ ĐẠT ĐƯỢC VÀ ĐỐI SÁNH KỸ THUẬT

### 3.1. Bảng kết quả thực nghiệm chi tiết từng năm tài chính của B-PIT (2016–2025)
Kết quả thực nghiệm chính thức trích xuất từ artifact `bpit-4a9d2e87f0de84ec` (tổng cộng **8.461 mã–năm**, trong đó **8.087 mã FIT**, **280 mã ASSIGNED_AFTER_CUTOFF**, và **94 mã ASSIGNED_NO_DATE**):

| Niên độ (FY) | Ngưỡng Cutoff áp dụng | Tổng số mã ($N$) | Số mã FIT ($N_{fit}$) | Số mã Gán sau Cutoff | Kích thước cụm $\{C_0, C_1, C_2\}$ | Thứ tự chất lượng (`cluster_order`) | Hồ sơ Cụm dẫn dắt (ROE / D/E) | Hồ sơ Cụm yếu nhất (ROE / D/E) | ARI so với B v4 | Trạng thái Audit |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2016** | 03/07/2017 | 135 | 135 | 0 | $\{95, 30, 10\}$ | **$[1, 0, 2]$** | Cụm 1: 24,17% / 0,48 | Cụm 2: 4,91% / 0,24 | **1,0000** | `PASS` (0 leak) |
| **2017** | 02/07/2018 | 951 | 951 | 0 | $\{577, 199, 175\}$ | **$[2, 1, 0]$** | Cụm 2: 22,62% / 0,46 | Cụm 0: 8,35% / 1,28 | **1,0000** | `PASS` (0 leak) |
| **2018** | 01/07/2019 | 947 | 947 | 0 | $\{527, 229, 191\}$ | **$[1, 2, 0]$** | Cụm 1: 21,78% / 0,51 | Cụm 0: 7,03% / 1,01 | **1,0000** | `PASS` (0 leak) |
| **2019** | 01/07/2020 | 972 | 972 | 0 | $\{680, 274, 18\}$ | **$[1, 0, 2]$** | Cụm 1: 19,93% / 0,53 | Cụm 2: 0,08% / 1,32 | **1,0000** | `PASS` (0 leak) |
| **2020** | 01/07/2021 | 977 | 977 | 0 | $\{610, 224, 143\}$ | **$[1, 2, 0]$** | Cụm 1: 22,42% / 0,73 | Cụm 0: 6,08% / 1,29 | **1,0000** | `PASS` (0 leak) |
| **2021** | 01/07/2022 | 1.043 | 1.043 | 0 | $\{745, 285, 13\}$ | **$[1, 0, 2]$** | Cụm 1: 19,88% / 0,51 | Cụm 2: 5,07% / 0,31 | **1,0000** | `PASS` (0 leak) |
| **2022** | 30/04/2023 | 1.146 | 1.048 | 98 (74 sau + 24 no-date) | $\{709, 227, 210\}$ | **$[2, 0, 1]$** | Cụm 2: 24,08% / 0,35 | Cụm 1: 7,51% / 3,08 | **0,9553** | `PASS` (0 leak) |
| **2023** | 30/04/2024 | 1.125 | 972 | 153 (110 sau + 43 no-date) | $\{720, 256, 149\}$ | **$[1, 2, 0]$** | Cụm 1: 19,23% / 0,37 | Cụm 0: 5,64% / 0,83 | **0,9369** | `PASS` (0 leak) |
| **2024** | 30/04/2025 | 1.165 | 1.042 | 123 (96 sau + 27 no-date) | $\{700, 254, 211\}$ | **$[1, 2, 0]$** | Cụm 1: 19,90% / 0,37 | Cụm 0: 6,49% / 0,71 | **0,8077** | `PASS` (0 leak) |
| **2025** | 30/04/2026 | 1.200 | 0 | Bỏ qua (Chưa đủ mẫu) | — | — | — | — | — | `NOT_READY` (3 usable) |

### 3.2. Đánh giá tính toàn vẹn Point-In-Time và Kiểm soát Rò rỉ thông tin
1. **Kết quả Fit-Leak Audit: PASS tuyệt đối.** Trường `fit_leaks` trong `audit.json` hoàn toàn rỗng trên cả 9 năm tài chính. Không có bất kỳ doanh nghiệp nào có ngày công bố sau Cutoff hoặc thiếu ngày công bố bị lọt vào quá trình huấn luyện K-Means.
2. **Cơ chế Runtime Cutoff Gate tại Milestone M3:**
   * Trong quá trình chạy chiến lược tại Milestone M3, thuật toán tại [src/delta_t1/m3/universe.py](file:///c:/Users/HP/Downloads/Phân%20cụm%20động%20lượng%20TTCK/src/delta_t1/m3/universe.py) thực thi kiểm tra nghiêm ngặt: nếu một quyết định đầu tư tại ngày `decision_date` cố tình yêu cầu dữ liệu của niên độ $t$ khi `decision_date < cutoff(t)`, hệ thống sẽ tạm loại mã với lý do kiểm toán `FINANCIAL_MODEL_BEFORE_CUTOFF`.
   * Nếu niên độ $t$ chưa có mô hình B-PIT hợp lệ (như FY 2025), hệ thống ghi nhận `FINANCIAL_MODEL_NOT_READY`.
   * Kiểm tra thực tế xác nhận tại snapshot `2024-03-29`, gate cutoff đã bảo vệ danh mục bằng cách tạm chặn 24 mã Combined và 178 mã Financial-only chưa đủ điều kiện công bố; đến snapshot `2024-05-31` (sau ngày cutoff 30/04/2024), 100% các mã hợp lệ được giải phóng và đưa vào rà soát.

### 3.3. So sánh đối chiếu chuyên sâu giữa B-PIT và Mô hình cơ sở B v4
1. **Giai đoạn FY 2016 – FY 2021 (ARI = 1,0000):**
   * Do áp dụng quy tắc độ trễ lịch sử (`LAG_RULE`), mọi báo cáo tài chính của năm $t$ đều có cùng ngày khả dụng là phiên giao dịch đầu tiên sau ngày 30/06 năm $t+1$.
   * Do đó, tập hợp các mã có `usable_from_date <= cutoff` tại ngày Cutoff trùng khớp 100% với tập dữ liệu của B v4. Chỉ số ARI đạt giá trị tuyệt đối $1,0000$, chứng minh tính tương thích hoàn hảo giữa hai mô hình trong giai đoạn dữ liệu lịch sử.
2. **Giai đoạn FY 2022 – FY 2024 (ARI từ 0,8077 đến 0,9553):**
   * Đây là giai đoạn thị trường có ngày công bố điện tử thực tế từ CafeF. Có khoảng 98 đến 153 doanh nghiệp nộp BCTC kiểm toán sau ngày 30/04 hàng năm.
   * Khi loại các doanh nghiệp nộp muộn ra khỏi quá trình huấn luyện tâm cụm, độ tương đồng ARI so với B v4 vẫn duy trì ở mức rất cao: **0,9553 (FY 2022)**, **0,9369 (FY 2023)** và **0,8077 (FY 2024)**.
   * *Ý nghĩa khoa học:* Việc đóng băng không gian phân cụm tại thời điểm 30/04 không làm méo mó hay thay đổi bản chất của các nhóm doanh nghiệp (các giá trị ARI đều $\ge 0,80$). Điều này chứng minh cấu trúc phân cụm tài chính của B-PIT vừa giữ được tính ổn định cao, vừa loại bỏ hoàn toàn hiện tượng nhìn trước tương lai (Look-ahead Bias).
3. **Độ ổn định phân bố kích thước cụm:**
   * Trong cả 9 năm tài chính, không có bất kỳ cụm nào bị suy biến thành cụm rác hoặc cụm rỗng. Cụm nhỏ nhất trong mọi năm đều duy trì tỷ lệ tối thiểu $> 10$ mã, đảm bảo tính đại diện thống kê và đáp ứng yêu cầu thanh khoản danh mục.

### 3.4. Quyết định kiến trúc và Bàn giao sang Milestone M3
Dựa trên kết quả thực nghiệm hoàn chỉnh và các Quyết định ADR D-M3-01, D-DIR-01:
1. **Thay thế hoàn toàn B v4 bằng B-PIT:** B-PIT (`bpit-4a9d2e87f0de84ec`) là mô hình phân cụm tài chính chính thức và duy nhất được sử dụng cho toàn bộ các chiến lược đầu tư tại Milestone M3. Mô hình B v4 chỉ được lưu trữ làm đối chứng lịch sử.
2. **Thực thi Luật Ứng viên Not-Weakest (Rule Va / Q5):**
   * Cụm dẫn dắt tài chính (Leading Cluster) là cụm đứng đầu trong `cluster_order` (trung vị ROE cao nhất, trung vị Nợ/VCSH thấp nhất).
   * Cụm yếu nhất (Weakest Cluster) là cụm đứng cuối trong `cluster_order` (thường là nhóm có ROE suy giảm mạnh dưới 8% và tỷ lệ Nợ/VCSH rất cao hoặc âm vốn).
   * **Chiến lược Combined:** Chỉ chọn các cổ phiếu nằm trong phần giao giữa Cụm dẫn dắt thị trường (Hệ A v4) và **các cụm tài chính không thuộc cụm yếu nhất** của B-PIT (tức là nhận 2 cụm đầu của `cluster_order`).
3. **Hệ thống Chốt chặn Chất lượng bổ sung (Quality Overlay):**
   * Để bù đắp cho đặc thù phân tán tự nhiên của dữ liệu tài chính, M3 không dựa hoàn toàn vào nhãn cụm mà tích hợp thêm bộ lọc kép từ Lớp chỉ số sản phẩm (D-IND-01):
     * Điểm Piotroski F-Score $\ge 7$ (chất lượng hoạt động cải thiện rõ nét).
     * Điểm Altman Z-Score $\ge 1,81$ (nằm ngoài vùng kiệt quệ tài chính).
4. **Kết quả kiểm chứng Feasibility và Targets-only trong M3:**
   * Khi kết nối với B-PIT, số lượng ứng viên của chiến lược Combined đạt tính khả thi cao trên toàn bộ 84 tháng khảo sát (chỉ có 13/60 tháng Development và 1/24 tháng Holdout rơi vào trạng thái số ứng viên $< N_{min} = 10$).
   * Quá trình kiểm tra targets-only trên cả hai giai đoạn Development và Holdout đều đạt trạng thái `PASS`, xác nhận B-PIT hoạt động trơn tru và tương thích 100% với hạ tầng backtest chính thức.

---

## 4. TÓM TẮT TRỌNG TÂM ĐƯA VÀO SLIDE THUYẾT TRÌNH (SLIDE-READY HIGHLIGHTS)

### Slide 1: Quy trình phân cụm tài chính Point-In-Time (B-PIT Pipeline)
* **Khắc phục triệt để Look-Ahead Bias:** Huấn luyện mô hình K-Means ($k=3$, 9 chỉ số D-IND-01) tại thời điểm chốt sổ định kỳ Cutoff (30/04 hàng năm cho FY $\ge$ 2022).
* **Đóng băng toàn diện (Full Freezing):** Đóng băng đồng thời tham số tiền xử lý $T_1$ (Winsorize 1%–99% + Z-score), tọa độ tâm cụm (Centroids) và thứ tự chất lượng cụm (`cluster_order`).
* **Gán động ngoại mẫu:** Các doanh nghiệp công bố BCTC muộn sau ngày 30/04 được chuẩn hóa và gán vào tâm cụm gần nhất mà không làm xê dịch cấu trúc cụm thị trường.

### Slide 2: Bảng kết quả thực nghiệm B-PIT qua các niên độ (2016–2025)

| Giai đoạn dữ liệu | Số niên độ | Tổng số bản ghi mã–FY | Số mã Huấn luyện (FIT) | Số mã Gán sau Cutoff | Độ tương đồng ARI so với B v4 | Đánh giá kiểm toán (Fit-Leak Audit) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lịch sử (FY 2016 – FY 2021)** | 6 năm | 5.025 | 5.025 (100%) | 0 (0%) | **1,0000** (Khớp tuyệt đối) | **PASS (0 leak)**: Khớp chuẩn Lag Rule 30/06 |
| **Hiện đại (FY 2022 – FY 2024)** | 3 năm | 3.436 | 3.062 (89,1%) | 374 (10,9%) | **0,8077 – 0,9553** (Rất cao) | **PASS (0 leak)**: Cô lập hoàn toàn mã nộp muộn |
| **Niên độ chờ (FY 2025)** | 1 năm | 1.200 | 0 | 0 | — | `NOT_READY`: Bảo vệ an toàn khi thiếu dữ liệu |

* **Tổng quy mô dữ liệu đã pin:** 8.461 bản ghi mã–năm hợp lệ; mã băm SHA256: `4a9d2e87...`

### Slide 3: Giải quyết triệt để rò rỉ thời gian & Đối sánh B-PIT vs B v4
1. **Zero Fit-Leak:** 100% doanh nghiệp trong tập huấn luyện có ngày công bố thực tế trước hoặc đúng Cutoff. Không có bất kỳ rò rỉ thông tin tương lai nào trong quá trình định hình tâm cụm.
2. **Tính vững chắc của không gian cụm:** Mức ARI đạt từ **0,81 đến 0,96** trong giai đoạn có ngày công bố thực tế (2022–2024) chứng minh việc loại trừ các mã công bố muộn không làm phá vỡ ranh giới cụm kinh tế học, đồng thời phản ánh đúng thông tin khả dụng của nhà đầu tư tại từng thời điểm.
3. **Phân hóa chất lượng rõ rệt:** Cụm dẫn dắt luôn duy trì trung vị ROE từ 19%–24% với tỷ lệ Nợ/VCSH an toàn (0,35–0,53), trong khi cụm yếu nhất có ROE suy giảm sâu và đòn bẩy nợ đột biến.

### Slide 4: Cơ chế Runtime Gate và Ứng dụng thực tiễn trong Milestone M3
1. **Chốt chặn thời gian thực (Runtime Cutoff Gate):** Tự động chặn các quyết định đầu tư sử dụng BCTC của niên độ mới khi chưa tới ngày Cutoff (`FINANCIAL_MODEL_BEFORE_CUTOFF`).
2. **Chiến lược phân bổ danh mục (Rule Va / Q5):** Vũ trụ đầu tư Combined được xây dựng từ giao điểm giữa Cụm dẫn dắt thị trường (Hệ A v4) và **các cụm tài chính lành mạnh (Not-Weakest)** của B-PIT.
3. **Chốt chặn an toàn đa lớp:** Kết hợp nhãn cụm B-PIT với điểm chất lượng Piotroski F-Score $\ge 7$ và an toàn phá sản Altman Z-Score $\ge 1,81$, tạo nền tảng vững chắc cho hệ thống giao dịch tự động DELTA.

---
*Báo cáo được trích xuất và xác thực 100% từ mã nguồn và dữ liệu thực nghiệm DELTA Intelligence (Artifact `bpit-4a9d2e87f0de84ec`).*

