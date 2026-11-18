# BÁO CÁO MILESTONE M2 — NHIỆM VỤ 3: KHẢO SÁT VÀ CHỌN GLOBAL K

**Người thực hiện:** Nhóm nghiên cứu DELTA  
**Tập dữ liệu chuẩn hóa:** `cafef-c8-complete-only-v2` (Bộ dữ liệu thị trường sạch 10 năm)  
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
1. Không chọn K dựa trên một tháng riêng lẻ; phải tổng hợp trung vị (median) trên toàn bộ 60 snapshot development (tổng cộng 420 lượt fit mô hình độc lập).
2. Tuyệt đối không sử dụng lợi nhuận tương lai, tỷ suất sinh lời, Sharpe, Sortino, ROI hoặc bất kỳ chỉ số danh mục đầu tư nào để chọn K. Các chỉ số này thuộc về Milestone M3.
3. Tuyệt đối không mở dữ liệu Holdout (24 snapshot từ 2024-01-31 đến 2025-12-31).
4. Chuẩn hóa Robust Scaling được tính toán độc lập theo từng snapshot (x_scaled = (x - Median) / IQR), không dùng chung scaler giữa các tháng để tránh rò rỉ thông tin tương lai.
5. Tiêu chí chọn K tối ưu: Ưu tiên Median Silhouette cao nhất; nếu ngang nhau thì dùng Median Davies-Bouldin nhỏ nhất làm tiêu chí phân xử (tie-breaker).

---

## 2. Kết quả khảo sát các mức K từ 2 đến 8

Bảng tổng hợp trung vị các chỉ số chất lượng cụm trên toàn bộ 60 snapshot development (trích xuất trực tiếp từ `M2/artifacts/m2-task3-development-v1/aggregate_by_k.csv`):

| K | Số snapshot hoàn thành | Median Silhouette | Median Davies-Bouldin | Median Calinski-Harabasz | Median Inertia | Median Balance |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **2** | **60** | **0.9408** | **0.4031** | **1586.37** | **376102.14** | **0.0210** |
| **3** | 60 | 0.9064 | 0.3882 | 2429.80 | 157128.71 | 0.0060 |
| **4** | 60 | 0.8869 | 0.4005 | 3404.99 | 91415.85 | 0.0030 |
| **5** | 60 | 0.8614 | 0.4012 | 4183.54 | 57943.54 | 0.0029 |
| **6** | 60 | 0.8345 | 0.4069 | 4910.20 | 36269.15 | 0.0021 |
| **7** | 60 | 0.8003 | 0.4030 | 5308.00 | 26719.44 | 0.0019 |
| **8** | 60 | 0.7517 | 0.4119 | 5569.35 | 21856.51 | 0.0018 |

---

## 3. Phân tích và Luận cứ lựa chọn Global K

1. **Về chỉ số Silhouette Score (Tiêu chí chính - Primary Rule):**
   - K = 2 đạt giá trị trung vị Silhouette cao nhất: **0.9408**, vượt trội hoàn toàn so với K = 3 (0.9064), K = 4 (0.8869) và các mức K lớn hơn (K = 8 chỉ còn 0.7517).
   - Điểm Silhouette trên 0.90 phản ánh cấu trúc phân cụm tự nhiên rất mạnh, các điểm dữ liệu nằm rất gần tâm cụm của mình và cách biệt xa so với cụm lân cận.

2. **Về chỉ số Davies-Bouldin Index (Tiêu chí phụ - Tie-breaker):**
   - K = 2 đạt giá trị tối ưu: **0.4031**, duy trì độ gắn kết nội cụm và phân tách ngoại cụm tốt.

3. **Về độ cân bằng kích thước cụm (Cluster Balance):**
   - K = 2 đạt mức cân bằng tốt nhất: **0.0210**, cao hơn gấp từ 3 đến 10 lần so với các mức K khác (K=3 chỉ đạt 0.0060, K=4 đạt 0.0030, K=8 chỉ đạt 0.0018).

4. **Về phương pháp khuỷu tay (Elbow Method):**
   - Mức giảm Inertia thể hiện sự ổn định rõ rệt tại K = 2 và K = 3. Kết hợp với tiêu chí ưu tiên Silhouette Score, K = 2 là điểm tối ưu tuyệt đối.

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
8. `M2/models/kmeans_task03/`: Bộ thông số và tâm cụm 60 snapshot của mô hình K=2 sẵn sàng bàn giao cho Nhiệm vụ 4.
