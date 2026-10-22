# BÁO CÁO MILESTONE M2 — NHIỆM VỤ 4: PHƯƠNG ÁN A — K-MEANS BASELINE

**Người thực hiện:** Nhóm nghiên cứu DELTA  
**Tập dữ liệu chuẩn hóa:** `cafef-c8-complete-only-v2` (Bộ dữ liệu thị trường đã vá bù & đối soát dữ liệu hoàn chỉnh)  
**Giai đoạn thực thi:** Development (60 snapshot cuối tháng liên tiếp từ 2019-01-31 đến 2023-12-29)  
**File cấu hình chuẩn:** `configs/experiments/m2_market_only_v2.json`  
**Notebook thực thi:** `M2/notebooks/04_kmeans_baseline.ipynb`  
**Thư mục lưu trữ artifact:** `M2/artifacts/m2-task4-kmeans-baseline-v1/`  
**Thư mục lưu trữ mô hình:** `M2/models/kmeans/` (60 file model JSON)  

---

## 1. Mục đích và Quy tắc thực nghiệm

### 1.1. Mục đích
Nhiệm vụ 4 thiết lập đường cơ sở phân cụm (Baseline) chính thức cho toàn bộ Milestone M2 bằng thuật toán K-Means với số cụm tối ưu **Global K = 2** đã được phê duyệt và đóng băng từ Nhiệm vụ 3.

Kết quả của Nhiệm vụ 4 cung cấp dữ liệu nền tảng cho:
- **Nhiệm vụ 7:** Đánh giá chất lượng cụm (Cluster Quality Evaluation).
- **Nhiệm vụ 8:** Phân tích hồ sơ cụm (Cluster Profiling).
- **Nhiệm vụ 9:** Đánh giá độ ổn định chuỗi thời gian (Temporal Stability & Transition Tracking).
- **Nhiệm vụ 10:** So sánh đa phương án (Model Comparison giữa K-Means, Ward và PCA + K-Means).

### 1.2. Rào chắn học thuật bất biến (Invariants)
1. **Khóa Global K = 2:** Chỉ sử dụng số cụm K = 2 đã đóng băng, tuyệt đối không quét lại K = 2..8.
2. **Không gian thời gian Development:** Thực thi độc lập trên toàn bộ 60 snapshot cuối tháng (2019-01-31 đến 2023-12-29). Niêm phong tuyệt đối 24 snapshot Holdout (2024–2025).
3. **Chuẩn hóa độc lập (Snapshot-level Robust Scaling):** Từng snapshot tính riêng Median và IQR trên tập cổ phiếu đủ điều kiện của chính snapshot đó theo công thức `x_scaled = (x - Median) / IQR`. Tuyệt đối không dùng chung scaler giữa các tháng.
4. **Vũ trụ cổ phiếu linh hoạt:** Lọc theo từng snapshot với `market_feature_ready_v2 == True` và kiểm tra ngưỡng tối thiểu `n_eligible >= 100` mã. Không áp đặt danh sách mã cố định ngược về quá khứ.
5. **Rào chắn mục tiêu:** Đánh giá cụm hoàn toàn dựa trên thước đo hình học và đặc trưng nội tại (Silhouette, Davies-Bouldin, Calinski-Harabasz, Inertia, Cluster Balance). Tuyệt đối không dùng lợi nhuận tương lai, Sharpe ratio, Sortino, ROI hoặc bất kỳ chỉ số danh mục đầu tư nào (thuộc Milestone M3).

---

## 2. Kết quả tổng quan thực thi trên 60 Snapshots Development (Dữ liệu Đã Vá Bù)

- **Số snapshot hoàn thành:** 60 / 60 snapshot (100% đạt ngưỡng, 0 snapshot bị bỏ qua).
- **Số lượng cổ phiếu hợp lệ:** Dao động từ **503 mã** (tháng 11/2020) đến **1,134 mã** (tháng 12/2023), trung bình đạt **760.77 mã / tháng**.
- **Tổng số lượt gán nhãn cụm (Assignments):** **45,646 bản ghi** (tăng hơn 15,700 bản ghi so với bản chạy trước khi vá dữ liệu).
- **Tham số thuật toán K-Means:** `seed = 42`, `n_init = 10`, `max_iter = 300`.

---

## 3. Chỉ số chất lượng cụm (Quality Metrics)

Bảng tổng hợp các chỉ số chất lượng cụm K-Means Baseline (K = 2) qua 60 snapshot development (trích xuất từ `M2/artifacts/m2-task4-kmeans-baseline-v1/metrics.csv` và `manifest.json`):

| Chỉ số chất lượng | Giá trị Nhỏ nhất (Min) | Giá trị Trung vị (Median) | Giá trị Lớn nhất (Max) | Ngưỡng chuẩn đánh giá | Đánh giá học thuật |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Silhouette Score** | 0.8174 | **0.9408** | 0.9782 | > 0.50 | Cực kỳ xuất sắc; ranh giới phân tách giữa 2 cụm rất rõ nét |
| **Davies-Bouldin Index** | 0.0898 | **0.3992** | 0.5846 | < 0.65 | Tối ưu; cụm có độ cô đặc nội bộ cao và khoảng cách tâm lớn |
| **Calinski-Harabasz Index** | 358.12 | **1586.37** | 4512.80 | Càng cao càng tốt | Phương sai liên cụm tăng vọt, phân tách rõ nét |
| **Inertia** | 4,210.50 | **120,531.06** | 6,812,410.15 | Tham chiếu quy mô | Hội tụ ổn định qua 60 tháng |
| **Cluster Balance** | 0.0033 | **0.0207** | 0.0528 | Tỷ lệ quy mô | Tương ứng cấu trúc 1 cụm thiểu số tinh hoa (~15 mã) và 1 cụm đa số (~746 mã) |

---

## 4. Hồ sơ kinh tế và Đặc trưng đại diện 2 Cụm (Cluster Profiling)

Sau khi căn chỉnh chuỗi thời gian để triệt tiêu hiện tượng đảo nhãn (Label Switching), các đặc trưng bình quân của 2 cụm thể hiện rõ nét bản chất dòng tiền thị trường:

| Đặc trưng phân tích | Toàn thị trường (Bình quân) | Cụm 0 (Thiểu số - Thanh khoản cao) | Cụm 1 (Đa số - Thị trường đại trà) | So sánh tương quan giữa 2 cụm |
| :--- | :---: | :---: | :---: | :--- |
| **Quy mô bình quân (`size`)** | 760.77 mã | **14.93 mã (2.0%)** | **745.83 mã (98.0%)** | Cụm 0 là nhóm cổ phiếu hạt nhân, Cụm 1 đại diện số đông |
| **Thanh khoản (`liquidity_21`)** | ~12.0 tỷ VND | **348.56 tỷ VND / phiên** | **5.26 tỷ VND / phiên** | Cụm 0 gấp ~66 lần Cụm 1; dòng tiền tập trung cao độ |
| **Hệ số Beta (`beta_126`)** | 0.37 | **1.2579** | **0.3493** | Cụm 0 rất nhạy sóng VN-Index; nhóm dẫn dắt thị trường |
| **Động lượng 1 tháng (`mom_21`)** | +1.91% | **+2.57%** | **+1.90%** | Cụm 0 có đà tăng ngắn hạn tích cực |
| **Động lượng 3 tháng (`mom_63`)** | +6.03% | **+10.76%** | **+5.93%** | Cụm 0 tăng gấp gần 2 lần thị trường đại trà |
| **Động lượng 6 tháng (`mom_126`)** | +12.13% | **+21.48%** | **+11.94%** | Cụm 0 duy trì hiệu suất nửa năm áp đảo |
| **Động lượng 12 tháng (`mom_252`)** | +23.87% | **+39.17%** | **+23.56%** | Tăng trưởng 1 năm của Cụm 0 vượt trội rõ nét |
| **Biến động 3 tháng (`vol_63`)** | 52.90% | **39.02%** | **53.18%** | Cụm 0 có độ biến động giá thấp và ổn định hơn hẳn |
| **Sụt giảm cực đại (`mdd_126`)** | -27.18% | **-25.23%** | **-27.22%** | Mức rút vốn tối đa của Cụm 0 được kiểm soát tốt hơn |

### Nhận định về sự cải thiện sau khi vá dữ liệu:
1. **Khắc phục tình trạng khuyết sàn HOSE giai đoạn 2021:**
   - Số snapshot có cụm dưới 5 mã đã giảm mạnh từ **11 snapshot** xuống chỉ còn **đúng 2 snapshot** (`2021-05-31` có 4 mã gồm `CTG, HPG, STB, VPB` và `2021-10-29` có 2 mã gồm `HPG, TCB`).
   - Cụm thiểu số giờ đây bao gồm đầy đủ các cổ phiếu Bluechips / VN30 đích thực (Hòa Phát, Techcombank, Vietinbank, Sacombank...), phản ánh chính xác dòng tiền thực của thị trường Việt Nam.
2. **Đặc trưng ổn định và bền vững hơn:**
   - Thanh khoản trung bình cụm dẫn dắt tăng từ 250 tỷ lên **348.56 tỷ VND/phiên**.
   - Biến động rủi ro giảm xuống **39.02%** (thấp hơn nhiều so với Cụm 1 là 53.18%), phản ánh đúng tính chất phòng thủ và ổn định của nhóm vốn hóa lớn.

---

## 5. Kết luận và Danh mục Artifacts bàn giao

Dữ liệu mới đã nâng cao chất lượng thực nghiệm của Nhiệm vụ 4 lên một tầm cao mới: quy mô mẫu lớn hơn (+52%), các chỉ số chất lượng cụm tăng lên (Median Silhouette = 0.9408, Calinski-Harabasz = 1586.37) và hiện tượng cụm suy biến được giải tỏa gần như hoàn toàn.

### Danh mục sản phẩm bàn giao:
1. **60 file Model JSON:** Lưu tại `M2/models/kmeans/` (`2019-01-31.json` đến `2023-12-29.json`).
2. **Bộ Artifacts chuẩn hóa:** Lưu tại `M2/artifacts/m2-task4-kmeans-baseline-v1/`:
   - `assignments.jsonl` & `assignments.csv`: 45,646 bản ghi gán cụm qua 60 tháng.
   - `profiles.jsonl` & `cluster_profiles.csv`: 120 bản ghi tâm cụm unscaled và thông số hồ sơ kinh tế.
   - `diagnostics.jsonl`, `diagnostics.csv` & `metrics.csv`: 60 dòng chẩn đoán chất lượng cụm K=2 sẵn sàng cho Nhiệm vụ 7 và Nhiệm vụ 10.
   - `validation.csv`: Bảng kiểm định 60 snapshot hợp lệ.
   - `manifest.json`: Checksum xác thực toàn vẹn metadata (`total_snapshots: 60`, `global_k: 2`, `total_assignments: 45646`).
