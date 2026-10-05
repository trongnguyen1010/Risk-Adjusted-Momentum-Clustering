# Báo cáo Nhiệm vụ 11: Final Holdout (Out-of-Sample Validation)
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro trên thị trường chứng khoán Việt Nam
**Phạm vi:** 7 snapshot Holdout (27/02/2026 – 28/08/2026) | **Mô hình đã đóng băng:** `KMeans_Baseline` (K-Means, Global K = 2)
**Notebook:** `M2/notebooks/11_final_holdout_execution.ipynb` | **Artifact:** `M2/artifacts/m2-final-holdout-v1/` | **Model:** `M2/models/holdout/` | **Logic:** `src/delta_t1/experiments/final_holdout.py`

**TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC:**
Sau khi cổng đóng băng được xác nhận (`status = FROZEN_FOR_HOLDOUT`), Final Holdout chỉ chạy **duy nhất mô hình thắng ở Nhiệm vụ 10 là `KMeans_Baseline`** với Global K = 2 trên 7 snapshot năm 2026: **7/7 snapshot hợp lệ, 0 snapshot bị bỏ qua, 4.624 nhãn cụm, 6/6 cặp tháng**. Median Silhouette Holdout đạt **0,9527**, cao hơn Development **+0,1970**, tức Delta_Silhouette ≥ −0,05 (kịch bản A của kế hoạch). Median ARI Holdout là 0,8955 và Persistence 99,58%. Điểm cần giữ cảnh báo là Cluster Balance giảm từ 0,0677 (Development) xuống **0,0214** (Holdout), cụm nhỏ chỉ có 10–19 mã mỗi tháng; thanh khoản đóng góp median 99,998% vào bình phương khoảng cách hai centroid. Kết quả là kiểm định một chiều, không dùng để retune phương pháp đã khóa.

---

## 1. Mục đích

Kiểm định độc lập năng lực tổng quát hóa ngoài mẫu của **duy nhất một mô hình** đã được chọn và đóng băng ở Nhiệm vụ 10 trên giai đoạn dữ liệu 2026. Holdout là bài kiểm tra một chiều: không dùng để tìm mô hình tốt hơn, không chạy lại hai phương án đã bị loại, không quét lại K và không điều chỉnh siêu tham số. Giữ nguyên công thức, feature set, seed và số lần khởi tạo; Robust Scaling fit riêng cho từng tháng, không dùng scaler Development.

## 2. Quá trình thực hiện theo kế hoạch (7 bước)

**Bước 1 – Kiểm định cổng đóng băng (11.1).** Notebook nạp quyết định đóng băng, kiểm tra trạng thái, timestamp, 15 model/checksum, cấu hình và bảng Task 10 (chưa đọc holdout ở bước này); dừng nếu không đạt (fail-closed).

| Mục | Giá trị |
|---|---|
| selected_method | `KMeans_Baseline` |
| algorithm | `kmeans` |
| global_k / k_range | 2 / [2] |
| seed / n_init / max_iter | 42 / 10 / 300 |
| decision_timestamp | 2026-10-04T08:01:06+00:00 |
| status | `FROZEN_FOR_HOLDOUT` (PASS: chỉ phương án được chọn mới mở được holdout) |

**Bước 2 – Nạp 7 snapshot từ Feature Store 1.6.0.** Loader C8 kiểm tra hash trước khi trả đúng 7 ngày holdout; pipeline được gọi một lần và đóng băng các export. Holdout mở lúc 2026-10-04T08:14:18Z; manifest `status = complete`, `methods_executed = [kmeans]`, `k_values_executed = [2]`.

**Bước 3 – Universe riêng từng tháng và ngưỡng 120 (11.2).** Không lấy membership tháng 08/2026 áp cho các tháng trước:

| Snapshot | Trạng thái | n_eligible |
|---|---|---:|
| 2026-02-27 | ready | 253 |
| 2026-03-31 | ready | 520 |
| 2026-04-29 | ready | 521 |
| 2026-05-29 | ready | 782 |
| 2026-06-30 | ready | 782 |
| 2026-07-31 | ready | 861 |
| 2026-08-28 | ready | 905 |

Kết quả: 7 snapshot sẵn sàng, 0 snapshot bị bỏ qua; mọi tháng đạt ngưỡng 120 mã.

**Bước 4 – Robust Scaling độc lập (11.3).** `center` là median của snapshot, `scale` là IQR (scale = 1 nếu IQR = 0 theo preprocessing đã đóng băng). Bảng `scaler_parameters` có 56 dòng (7 snapshot × 8 feature), phương pháp `robust_per_snapshot`, mọi `scale > 0`. Ví dụ snapshot 2026-02-27:

| Feature | center (median) | scale (IQR) |
|---|---:|---:|
| mom_21 | -0,0110 | 0,0695 |
| mom_63 | -0,0086 | 0,1451 |
| mom_126 | -0,0277 | 0,1888 |
| mom_252 | 0,0114 | 0,3136 |
| vol_63 | 0,3028 | 0,1574 |
| mdd_126 | -0,1910 | 0,1421 |
| beta_126 | 0,3836 | 0,5991 |
| liquidity_21 (VND) | 2,0845 × 10⁹ | 2,3837 × 10¹⁰ |

**Bước 5 – Chạy mô hình thắng (11.4).** Gán nhãn cụm cho từng mã; model/centroid/scaler lưu tại `M2/models/holdout/` và trong artifact (7 file model). Có 4.624 assignment không trùng (snapshot, mã), 14 profile (7 tháng × 2 cụm); profile là trung bình 8 feature gốc của thành viên thực tế; nhãn raw khác nhãn aligned.

| Snapshot | Size Cụm 0 | Size Cụm 1 | Tỷ trọng Cụm 0 |
|---|---:|---:|---:|
| 2026-02-27 | 10 | 243 | 3,95% |
| 2026-03-31 | 14 | 506 | 2,69% |
| 2026-04-29 | 12 | 509 | 2,30% |
| 2026-05-29 | 13 | 769 | 1,66% |
| 2026-06-30 | 13 | 769 | 1,66% |
| 2026-07-31 | 13 | 848 | 1,51% |
| 2026-08-28 | 19 | 886 | 2,10% |

**Bước 6 – Chất lượng, ổn định và khoảng cách suy thoái (11.5–11.8).** Xem mục 3.

**Bước 7 – Biểu đồ 22 mốc, manifest và báo cáo (11.9–11.10).** Biểu đồ quỹ đạo Silhouette có hai đường trung vị (Development, Holdout) và đường đứt đỏ ghi chú Systemic Data Gap; không nối đường Development tới Holdout. Manifest kiểm tra toàn bộ export, bản sao model, source snapshot và báo cáo; chạy lại notebook chỉ xác minh checksum và nạp evidence, không refit. Notebook in: *TASK 11 VERIFIED: KMeans_Baseline | snapshots: 7 | temporal pairs: 6*.

## 3. Kết quả đạt được

### 11.5 – Chất lượng phân cụm trên Holdout (K = 2)

| Snapshot | Silhouette | DB | CH | Inertia | Cụm (0 / 1) | Balance |
|---|---:|---:|---:|---:|---|---:|
| 2026-02-27 | 0,8434 | 0,4539 | 448,30 | 4.849,91 | 243 / 10 | 0,0412 |
| 2026-03-31 | 0,9290 | 0,4337 | 1.493,21 | 86.901,99 | 506 / 14 | 0,0277 |
| 2026-04-29 | 0,9392 | 0,3149 | 1.393,39 | 118.867,26 | 509 / 12 | 0,0236 |
| 2026-05-29 | 0,9573 | 0,2919 | 2.479,28 | 486.130,33 | 769 / 13 | 0,0169 |
| 2026-06-30 | 0,9585 | 0,4316 | 2.330,38 | 432.647,47 | 13 / 769 | 0,0169 |
| 2026-07-31 | 0,9632 | 0,3610 | 2.838,85 | 702.188,31 | 848 / 13 | 0,0153 |
| 2026-08-28 | 0,9527 | 0,4382 | 2.526,86 | 677.822,83 | 886 / 19 | 0,0214 |

Tổng hợp Holdout (7 snapshot):

| Chỉ số | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| silhouette | 0,9348 | **0,9527** | 0,8434 | 0,9632 |
| davies_bouldin | 0,3893 | **0,4316** | 0,2919 | 0,4539 |
| calinski_harabasz | 1.930,04 | **2.330,38** | 448,30 | 2.838,85 |
| inertia | 358.486,87 | **432.647,47** | 4.849,91 | 702.188,31 |
| cluster_balance | 0,0233 | **0,0214** | 0,0153 | 0,0412 |

Cả 7 tháng Holdout có Balance dưới ngưỡng cảnh báo 0,05. Inertia phụ thuộc quy mô universe nên không dùng để so hạng giữa các tháng.

### 11.6 – Độ ổn định thời gian giữa 6 cặp tháng Holdout

| Cặp | n_common | ARI | NMI | Persistence | Migration | Entry | Exit |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-02-27 → 2026-03-31 | 253 | 0,8522 | 0,7516 | 98,81% | 1,19% | 267 | 0 |
| 2026-03-31 → 2026-04-29 | 520 | 0,6734 | 0,4870 | 98,46% | 1,54% | 1 | 0 |
| 2026-04-29 → 2026-05-29 | 520 | 0,8717 | 0,7513 | 99,42% | 0,58% | 262 | 1 |
| 2026-05-29 → 2026-06-30 | 781 | 0,9193 | 0,8311 | 99,74% | 0,26% | 1 | 1 |
| 2026-06-30 → 2026-07-31 | 781 | 0,9193 | 0,8311 | 99,74% | 0,26% | 80 | 1 |
| 2026-07-31 → 2026-08-28 | 861 | 1,0000 | 1,0000 | 100,00% | 0,00% | 44 | 0 |

Median Holdout: ARI 0,8955; NMI 0,7914; Persistence 99,58%; Migration 0,42%. Chỉ nối các tháng Holdout liên tiếp hợp lệ; **không có cặp 2025-01-24 → 2026-02-27** (Gap Reset Rule), không nối qua snapshot bị skip. ARI/NMI đo cấu trúc, Migration/Persistence đo trên mã chung, Entry/Exit báo riêng; Migration không phải chi phí hay turnover danh mục. Ma trận chuyển dịch và centroid drift của 6 cặp lưu trong `transition_matrices` và `centroid_drift`; notebook kiểm tra tổng lượt chuyển bằng `n_common` và Persistence khớp ma trận.

### 11.7 – Khoảng cách suy thoái ngoài mẫu (Generalization Gap)

| Metric | N Dev | N Holdout | Median Development | Median Holdout | Holdout − Development |
|---|---:|---:|---:|---:|---:|
| silhouette | 15 | 7 | 0,7557 | 0,9527 | **+0,1970** |
| davies_bouldin | 15 | 7 | 0,5219 | 0,4316 | -0,0903 |
| calinski_harabasz | 15 | 7 | 316,39 | 2.330,38 | +2.013,99 |
| inertia | 15 | 7 | 2.158,61 | 432.647,47 | +430.488,86 |
| cluster_balance | 15 | 7 | 0,0677 | 0,0214 | -0,0462 |
| ari | 14 | 6 | 0,7983 | 0,8955 | +0,0973 |
| nmi | 14 | 6 | 0,6613 | 0,7914 | +0,1301 |
| persistence_probability | 14 | 6 | 0,9856 | 0,9958 | +0,0102 |
| migration_rate | 14 | 6 | 0,0144 | 0,0042 | -0,0102 |

`Delta_Silhouette = 0,952683 − 0,755722 = +0,196961`. Theo rubric kế hoạch, Delta_Silhouette ≥ −0,05 thuộc kịch bản A (thích ứng xuất sắc) và Silhouette Holdout (0,9527) lớn hơn ngưỡng 0,50 nên không rơi vào kịch bản C. Các ngưỡng này là bộ quy tắc chẩn đoán; khoảng cách được ghi nhận từ số liệu và chưa đủ để kết luận về chế độ vĩ mô hoặc khả năng sinh lợi. Chất lượng Holdout cao hơn Development vì cả Silhouette lẫn DB đều cải thiện, nhưng Balance giảm và Inertia tăng theo quy mô universe lớn hơn (253–905 mã).

### 11.8 – Tính bền vững của hồ sơ cụm (Profile Consistency Test)

Hồ sơ so sánh đủ 8 feature gốc theo vai trò "Higher mom63" và "Lower mom63" tại từng tháng (không giả định Cụm 0/Cụm 1 có cùng identity xuyên gap). Giá trị là trung bình các mean của cụm theo tháng:

| Feature | Higher mom63 – Development | Higher mom63 – Holdout | Lower mom63 – Development | Lower mom63 – Holdout |
|---|---:|---:|---:|---:|
| mom_21 | 0,0218 | -0,0071 | 0,0185 | -0,0085 |
| mom_63 | 0,0845 | 0,0543 | 0,0229 | -0,0291 |
| mom_126 | 0,1344 | 0,0312 | 0,0546 | -0,0207 |
| mom_252 | 0,3837 | 0,2939 | 0,1978 | 0,0653 |
| vol_63 | 0,3299 | 0,4197 | 0,3211 | 0,3803 |
| mdd_126 | -0,2039 | -0,2595 | -0,1997 | -0,2462 |
| beta_126 | 1,1531 | 0,7115 | 0,7562 | 0,4976 |
| liquidity_21 (tỷ VNĐ) | 316,83 | 404,21 | 69,92 | 115,47 |

- Nhóm "Higher mom63" vẫn là nhóm có thanh khoản lớn hơn nhóm còn lại (404,21 so với 115,47 tỷ) và momentum cao hơn ở `mom_63`, `mom_126`, `mom_252`, nhưng khoảng cách momentum thu hẹp so với Development (ví dụ `mom_126`: 3,12% so với 13,44%) và `mom_21` âm ở cả hai nhóm.
- Nhóm "Lower mom63" duy trì momentum yếu (mom_63 = −2,91%, mom_126 = −2,07%) và thanh khoản thấp hơn; tuy nhiên biến động `vol_63` của nhóm này (0,3803) thấp hơn nhóm Higher (0,4197), nên đặc tính "biến động cao" của nhóm bám sau không được xác nhận trong Holdout.
- Không có đảo chiều thứ tự về thanh khoản và `mom_63` giữa hai vai trò; do đó chưa phát sinh nhu cầu đối chiếu với xu hướng VN-Index để giải thích đảo chiều. Notebook không đọc dữ liệu chỉ số nên không đưa ra nhận định về bối cảnh vĩ mô năm 2026.

### Phân rã khoảng cách giữa hai centroid (diễn giải hình học độc lập, không fit lại)

Phần trăm đóng góp của từng feature vào bình phương khoảng cách hai centroid trong không gian Robust Scaling, tính từ model đã lưu:

| Snapshot | liquidity_21 | beta_126 | vol_63 | mom_63 | mom_252 | Các feature còn lại |
|---|---:|---:|---:|---:|---:|---|
| 2026-02-27 | 98,8584% | 0,0801% | 0,0274% | 0,4999% | 0,2828% | < 0,2% mỗi feature |
| 2026-03-31 | 99,9803% | 0,0043% | 0,0012% | 0,0019% | 0,0030% | < 0,01% mỗi feature |
| 2026-04-29 | 99,9841% | 0,0059% | 0,0001% | 0,0007% | 0,0058% | < 0,01% mỗi feature |
| 2026-05-29 | 99,9984% | 0,0010% | ≈ 0 | ≈ 0 | 0,0005% | ≈ 0 |
| 2026-06-30 | 99,9980% | 0,0009% | ≈ 0 | 0,0003% | 0,0007% | ≈ 0 |
| 2026-07-31 | 99,9991% | 0,0006% | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 |
| 2026-08-28 | 99,9981% | 0,0015% | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 |

Thanh khoản đóng góp **median 99,9980%**. Đây là phép phân rã khoảng cách, không phải tỷ lệ lợi nhuận, explained variance hay chứng minh nguyên nhân về mặt cơ chế.

## 4. Nhận định và rào chắn học thuật

- **Kịch bản tổng quát hóa:** Delta_Silhouette = +0,1970, vượt ngưỡng kịch bản A (≥ −0,05); cấu trúc phân tách hình học được bảo toàn ngoài mẫu (Silhouette 0,84–0,96, DB 0,29–0,45). Kết quả tương ứng một chế độ trong đó nhóm cực thanh khoản tách xa phần còn lại.
- **Mất cân bằng cần giữ cảnh báo:** Balance median 0,0214 (so với 0,0677), cụm nhỏ 10–19 mã (1,5–4,0% universe). Silhouette cao phản ánh khoảng cách hình học xa của một nhóm nhỏ và không đồng nghĩa hai chế độ cân bằng.
- **Ổn định thời gian:** Persistence 98,46–100% ở cả 6 cặp; ARI thấp nhất là 0,6734 (2026-03-31 → 2026-04-29).
- **Không retune:** không đổi feature set, K hay thuật toán dựa trên kết quả Holdout; mọi suy giảm nếu có sẽ ghi vào Giới hạn.

## 5. Giới hạn học thuật

- Đây là monthly independent clustering trong phạm vi market-only, không phải dynamic clustering, strict research universe hay bằng chứng hiệu quả đầu tư.
- Ý nghĩa của Migration chỉ là chuyển nhãn trên tập mã chung, không phải turnover/chi phí danh mục.
- Mean/Median trong bảng profile là tổng hợp các mean của cụm theo tháng, không phải median từng cổ phiếu.
- Universe Holdout (253–905 mã) khác Development (142–780 mã); Inertia và Calinski–Harabasz phụ thuộc quy mô nên chỉ đọc cùng bối cảnh.
- Nhiệm vụ 12 (kiểm toán M2) và M3 chưa thực hiện trong lần chạy này.

## 6. Khung kết luận ba phần

**Phần A – Gate và thực thi một chiều.** Mô hình `KMeans_Baseline`, K = 2, seed 42, n_init 10, max_iter 300; freeze `2026-10-04T08:01:06+00:00`, mở holdout `2026-10-04T08:14:18Z`; 7/7 snapshot, 4.624 assignment, 6/6 cặp tháng; universe riêng mỗi tháng 253–905 mã, 0 snapshot bị skip; Robust Scaling fit mới từng snapshot; chỉ algorithm thắng và K = 2.

**Phần B – Development so với Holdout.** Median Silhouette 0,7557 → 0,9527 (Delta = +0,1970); DB 0,5219 → 0,4316; ARI 0,7983 → 0,8955; Balance 0,0677 → 0,0214. Khoảng cách chỉ được ghi nhận từ số liệu, các ngưỡng kế hoạch là rubric chẩn đoán.

**Phần C – Hồ sơ cụm, gap reset và giới hạn.** Hồ sơ theo vai trò Higher/Lower `mom_63` giữ thứ tự về thanh khoản và momentum; cụm nhỏ nhất 10 mã; chuỗi Holdout bắt đầu mới, không có cặp 2025-01-24 → 2026-02-27. Giữ nguyên phương pháp sau Holdout, không retune.
