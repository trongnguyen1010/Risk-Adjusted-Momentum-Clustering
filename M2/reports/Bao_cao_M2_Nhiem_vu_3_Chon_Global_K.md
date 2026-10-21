# BÁO CÁO MILESTONE M2 — NHIỆM VỤ 3: KHẢO SÁT VÀ CHỌN GLOBAL K

**Người thực hiện:** Nhóm nghiên cứu DELTA  
**Tập dữ liệu chuẩn hóa:** `cafef-c8-complete-only-v2` (Bộ dữ liệu 10 năm)  
**Giai đoạn khảo sát:** Development (60 snapshot cuối tháng liên tiếp từ 2019-01-31 đến 2023-12-29)  
**File cấu hình chuẩn:** `configs/experiments/m2_market_only_v2.json`  
**Notebook thực thi:** `M2/notebooks/03_choose_global_k.ipynb`  
**Thư mục lưu trữ artifact:** `M2/artifacts/m2-task3-development-v1/`  
**Thư mục lưu trữ mô hình:** `M2/models/kmeans/` và `M2/models/kmeans_task03/`  

---

## 1. Mục đích và Quy tắc thực nghiệm

### 1.1. Mục đích
Dùng thuật toán K-Means trên 60 snapshot giai đoạn Development để quét không gian số cụm K từ 2 đến 8 nhằm chọn ra một Global K duy nhất cho toàn bộ Milestone M2. Số cụm Global K sau khi được phê duyệt và đóng băng (freeze) sẽ được áp dụng thống nhất cho tất cả các phương án phân cụm:
- Phương án A: K-Means Baseline (Nhiệm vụ 4)
- Phương án B: Ward Hierarchical Clustering (Nhiệm vụ 5)
- Phương án C: PCA + K-Means (Nhiệm vụ 6)

### 1.2. Rào chắn học thuật bất biến (Invariants)
1. Không chọn K dựa trên một tháng riêng lẻ; phải tổng hợp trung vị (median) trên toàn bộ 60 snapshot development (tổng cộng 420 lượt fit mô hình).
2. Tuyệt đối không sử dụng lợi nhuận tương lai, tỷ suất sinh lời, Sharpe, Sortino, ROI hoặc bất kỳ chỉ số danh mục đầu tư nào để chọn K. Các chỉ số này thuộc về Milestone M3.
3. Tuyệt đối không mở dữ liệu Holdout (24 snapshot từ 2024-01-31 đến 2025-12-31).
4. Chuẩn hóa Robust Scaling được tính toán độc lập theo từng snapshot (x_scaled = (x - Median) / IQR), không dùng chung scaler giữa các tháng để tránh rò rỉ thông tin tương lai.
5. Tiêu chí chọn K tối ưu: Ưu tiên Median Silhouette cao nhất; nếu ngang nhau thì dùng Median Davies-Bouldin nhỏ nhất làm tiêu chí phân xử (tie-breaker).

---

## 2. Kết quả khảo sát các mức K từ 2 đến 8

Bảng tổng hợp trung vị các chỉ số chất lượng cụm trên toàn bộ 60 snapshot development (trích từ `M2/artifacts/m2-task3-development-v1/aggregate_by_k.csv`):

| K | Số snapshot hoàn thành | Median Silhouette | Median Davies-Bouldin | Median Calinski-Harabasz | Median Inertia | Median Balance |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **2** | **60** | **0.9319** | **0.3964** | **1122.33** | 82143.84 | **0.0238** |
| **3** | 60 | 0.8831 | 0.4123 | 1630.56 | 33083.94 | 0.0082 |
| **4** | 60 | 0.8530 | 0.4225 | 1932.75 | 19443.94 | 0.0064 |
| **5** | 60 | 0.7867 | 0.4239 | 2205.15 | 11804.38 | 0.0045 |
| **6** | 60 | 0.7410 | 0.4247 | 2700.70 | 9077.84 | 0.0039 |
| **7** | 60 | 0.6945 | 0.4575 | 3033.67 | 6817.07 | 0.0036 |
| **8** | 60 | 0.6135 | 0.4762 | 3337.37 | 5400.79 | 0.0035 |

---

## 3. Phân tích và Luận cứ lựa chọn Global K

1. **Về chỉ số Silhouette Score (Tiêu chí chính - Primary Rule):**
   - K = 2 đạt giá trị trung vị Silhouette cao nhất: **0.9319**, vượt trội hoàn toàn so với K = 3 (0.8831), K = 4 (0.8530) và các mức K lớn hơn (K = 8 chỉ còn 0.6135).
   - Điểm Silhouette trên 0.90 phản ánh cấu trúc phân cụm cực kỳ tự nhiên, rõ nét, các điểm dữ liệu nằm rất gần tâm cụm của mình và cách biệt xa so với cụm lân cận.

2. **Về chỉ số Davies-Bouldin Index (Tiêu chí phụ - Tie-breaker):**
   - K = 2 đạt giá trị thấp nhất và tối ưu nhất: **0.3964** (nhỏ hơn K = 3 là 0.4123 và tăng dần lên 0.4762 ở K = 8).
   - Chỉ số Davies-Bouldin càng nhỏ chứng tỏ sự phân tách liên cụm càng tốt và độ gắn kết nội cụm càng cao.

3. **Về độ cân bằng kích thước cụm (Cluster Balance):**
   - K = 2 đạt mức cân bằng tốt nhất: **0.0238**, cao gấp khoảng 3 đến 6 lần so với các mức K khác (K=3 chỉ đạt 0.0082, K=4 đạt 0.0064, K=8 chỉ đạt 0.0035).

4. **Về phương pháp khuỷu tay (Elbow Method):**
   - Mức giảm Inertia lớn nhất diễn ra khi chuyển từ K=2 sang K=3 và K=4, tuy nhiên xét theo quy tắc chính thức đã được khóa trong Protocol thì Silhouette Score là thước đo quyết định tối thượng.

---

## 4. Quyết định chính thức và Đóng băng cấu hình

* **Số cụm Global K được chọn:** **K = 2**
* **Trạng thái:** `APPROVED_GLOBAL_K` (Đã phê duyệt và đóng băng chính thức)
* **Quy ước chuyển tiếp:**
  - Nhiệm vụ 4 (K-Means Baseline): Khóa cố định K = 2.
  - Nhiệm vụ 5 (Ward): Khóa cố định K = 2.
  - Nhiệm vụ 6 (PCA + K-Means): Khóa cố định K = 2.
  - Không được phép thay đổi số cụm K trong suốt toàn bộ quá trình thực nghiệm còn lại của Milestone M2.

---

## 5. Danh mục Artifacts lưu trữ

Toàn bộ kết quả thực nghiệm được lưu trữ bất biến tại:
1. `M2/notebooks/03_choose_global_k.ipynb`: Notebook thực thi độc lập, tích hợp đầy đủ mã nguồn, bảng số liệu và biểu đồ trực quan.
2. `M2/artifacts/m2-task3-development-v1/per_snapshot_k_metrics.csv`: Bảng chi tiết 420 lượt chạy (60 snapshot nhân 7 mức K).
3. `M2/artifacts/m2-task3-development-v1/aggregate_by_k.csv`: Bảng tổng hợp trung vị các chỉ số theo K.
4. `M2/artifacts/m2-task3-development-v1/global_k_decision.json`: Biên bản quyết định khóa Global K kèm mã kiểm tra sha256.
5. `M2/artifacts/m2-task3-development-v1/silhouette_curve.png`: Đồ thị đường cong trung vị Silhouette Score.
6. `M2/artifacts/m2-task3-development-v1/elbow_inertia_curve.png`: Đồ thị phương pháp khuỷu tay Inertia.
7. `M2/artifacts/m2-task3-development-v1/silhouette_and_elbow_curves.png`: Đồ thị kết hợp hai trục Silhouette và Inertia.
8. `M2/models/kmeans/kmeans_k2_development_models.json`: Bộ thông số và tâm cụm 60 snapshot của mô hình K=2 sẵn sàng bàn giao cho Nhiệm vụ 4.
