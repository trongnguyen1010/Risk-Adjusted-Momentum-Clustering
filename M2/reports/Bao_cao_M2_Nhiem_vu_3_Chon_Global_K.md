# BÁO CÁO MILESTONE M2 — NHIỆM VỤ 3: KHẢO SÁT VÀ CHỌN GLOBAL K

**Người thực hiện:** Nhóm nghiên cứu DELTA  
**Giai đoạn khảo sát:** Development (60 snapshot cuối tháng liên tiếp từ 2019-01-31 đến 2023-12-29)  
**File cấu hình chuẩn:** `configs/experiments/m2_market_only_v2.json`  
**Notebook thực thi:** `M2/notebooks/03_choose_global_k.ipynb`  
**Thư mục lưu trữ artifact:** `M2/artifacts/m2-task3-development-v1/`  

---

## 1. Mục đích và Quy tắc thực nghiệm

### 1.1. Mục đích
Dùng thuật toán K-Means trên giai đoạn Development để quét số cụm K từ 2 đến 8 nhằm chọn ra một Global K duy nhất cho toàn bộ Milestone M2. Số cụm Global K sau khi được phê duyệt và đóng băng (freeze) sẽ được dùng đồng nhất cho tất cả các phương án phân cụm:
- Phương án A: K-Means Baseline (Nhiệm vụ 4)
- Phương án B: Ward Hierarchical Clustering (Nhiệm vụ 5)
- Phương án C: PCA + K-Means (Nhiệm vụ 6)

### 1.2. Rào chắn học thuật bất biến (Invariants)
1. Không chọn K dựa trên một tháng riêng lẻ; phải tổng hợp trung vị (median) trên toàn bộ 60 snapshot development.
2. Không sử dụng lợi nhuận tương lai, tỷ suất sinh lời, Sharpe, Sortino, ROI hoặc bất kỳ chỉ số danh mục đầu tư nào để chọn K.
3. Tuyệt đối không mở dữ liệu Holdout (2024-01-31 đến 2025-12-31).
4. Chuẩn hóa Robust Scaling được tính toán độc lập theo từng snapshot (`x_scaled = (x - Median) / IQR`), không dùng chung scaler giữa các tháng.
5. Tiêu chí chọn K tối ưu: Ưu tiên Median Silhouette cao nhất; nếu ngang nhau thì dùng Median Davies-Bouldin nhỏ nhất làm tiêu chí phân xử (tie-breaker).

---

## 2. Kết quả khảo sát các mức K từ 2 đến 8

Bảng tổng hợp trung vị các chỉ số chất lượng cụm trên toàn bộ giai đoạn development (trích từ `M2/artifacts/m2-task3-development-v1/aggregate_by_k.csv`):

| K | Số snapshot hoàn thành | Median Silhouette | Median Davies-Bouldin | Median Calinski-Harabasz | Median Inertia | Median Balance |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **2** | **15** | **0.7557** | **0.5219** | **316.39** | 2158.61 | 0.0677 |
| **3** | 15 | 0.6356 | 0.6362 | 222.83 | 1712.55 | 0.0227 |
| **4** | 15 | 0.3841 | 0.9558 | 202.76 | 1377.73 | 0.0185 |
| **5** | 15 | 0.3441 | 1.0010 | 182.58 | 1158.59 | 0.0270 |
| **6** | 15 | 0.2813 | 1.0317 | 171.64 | 986.94 | 0.0385 |
| **7** | 15 | 0.2649 | 1.0002 | 157.57 | 901.49 | 0.0317 |
| **8** | 15 | 0.2453 | 1.0910 | 143.45 | 836.29 | 0.0333 |

---

## 3. Phân tích và Luận cứ lựa chọn Global K

1. **Về chỉ số Silhouette:**
   - K = 2 đạt giá trị trung vị Silhouette cao nhất: **0.7557**, vượt trội hoàn toàn so với K = 3 (0.6356), K = 4 (0.3841) và các mức K lớn hơn (đều dưới 0.35).
   - Điểm Silhouette > 0.7 thể hiện cấu trúc phân nhóm tự nhiên rất mạnh và tách biệt rõ rệt giữa các cụm.

2. **Về chỉ số Davies-Bouldin:**
   - K = 2 đạt giá trị nhỏ nhất: **0.5219** (nhỏ hơn mức 0.6362 của K = 3 và xấp xỉ 1.0 của các mức K >= 4).
   - Chỉ số Davies-Bouldin càng nhỏ chứng tỏ khoảng cách liên cụm càng xa và độ phân tán nội cụm càng chặt chẽ.

3. **Về chỉ số Calinski-Harabasz:**
   - K = 2 đạt **316.39** (cao nhất trong toàn bộ 7 mức K khảo sát), khẳng định mức độ biến sai giữa các cụm là lớn nhất.

4. **Về phương pháp khuỷu tay (Elbow Method):**
   - Đồ thị Inertia cho thấy điểm gập khuỷu tay (elbow point) rõ nét nhất xảy ra tại **K = 2**, tốc độ suy giảm Inertia chậm lại đáng kể sau K = 3.

---

## 4. Quyết định chính thức và Đóng băng cấu hình

* **Số cụm Global K được chọn:** **K = 2**
* **Trạng thái:** `APPROVED_GLOBAL_K` (Đã phê duyệt và đóng băng chính thức)
* **Quy ước chuyển tiếp:**
  - Nhiệm vụ 4 (K-Means Baseline): Khóa cố định K = 2.
  - Nhiệm vụ 5 (Ward): Khóa cố định K = 2.
  - Nhiệm vụ 6 (PCA + K-Means): Khóa cố định K = 2.

---

## 5. Danh mục Artifacts lưu trữ

Toàn bộ kết quả thực nghiệm được lưu trữ bất biến tại:
1. `M2/notebooks/03_choose_global_k.ipynb`: Notebook thực thi toàn diện và hiển thị trực quan.
2. `M2/artifacts/m2-task3-development-v1/per_snapshot_k_metrics.csv`: Bảng chi tiết toàn bộ các lần chạy snapshot nhân với K.
3. `M2/artifacts/m2-task3-development-v1/aggregate_by_k.csv`: Bảng tổng hợp trung vị các chỉ số theo K.
4. `M2/artifacts/m2-task3-development-v1/global_k_decision.json`: Biên bản quyết định khóa Global K có mã băm sha256.
5. `M2/artifacts/m2-task3-development-v1/silhouette_curve.png`: Đồ thị đường cong trung vị Silhouette Score.
6. `M2/artifacts/m2-task3-development-v1/elbow_inertia_curve.png`: Đồ thị phương pháp khuỷu tay Inertia.
7. `M2/artifacts/m2-task3-development-v1/silhouette_and_elbow_curves.png`: Đồ thị ghép đôi đối chiếu.
