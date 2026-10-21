# Báo cáo Nhiệm vụ 6 — Thực thi và kiểm chứng PCA + K-Means với dữ liệu mới V2

<!-- PCA_KMEANS_V2_FULL_REPORT -->

**Ngày biên soạn:** 21/10/2026. **Phạm vi:** 60 snapshot development từ
2019-01-31 đến 2023-12-29; Global K=2; PCA 2 chiều.

Bản báo cáo này phát triển bố cục A/B/C, bảng số liệu và cách biện luận của mẫu
PCA + K-Means cũ trong lịch sử Git, sử dụng hoàn toàn kết quả V2 đã lưu.
**Cập nhật báo cáo và đồng bộ Git:** 22/10/2026. Bản đầy đủ này thay bản
xuất tự động ở đường dẫn báo cáo chính. Bản trước được giữ trong Git history;
checksum báo cáo và tham chiếu manifest được cập nhật, model/số liệu gốc
giữ nguyên. Số liệu trong bảng dùng dấu chấm thập phân; giá trị trình bày
được làm tròn, dữ liệu nguồn giữ độ chính xác gốc.

## A — Thực thi và kiểm chứng

### 1. Mục tiêu và dữ liệu đầu vào

Nhiệm vụ 6 xây dựng phương án PCA + K-Means trên cùng tám market features của
protocol đã freeze, nhằm cung cấp một phương án giảm chiều cho đối chiếu ở M2.
Đây là lần huấn luyện với dữ liệu mới `CAFEF_C8_COMPLETE_ONLY_V2`, khác bộ kiểm
chứng cũ 15 tháng/PCA 4 chiều. Không coi chênh lệch kết quả giữa hai bộ là tác
động thuần của PCA vì giai đoạn, thành viên và dữ liệu đã thay đổi.

Tám đầu vào theo thứ tự là `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`,
`mdd_126`, `beta_126`, `liquidity_21`. Universe được xác định theo eligibility ở
từng snapshot, không dùng một danh sách cổ phiếu hiện tại áp ngược cho cả lịch sử.

### 2. Cấu hình và quy mô thực thi

| Hạng mục | Cấu hình hoặc kết quả |
| --- | --- |
| Bộ dữ liệu | CAFEF_C8_COMPLETE_ONLY_V2 |
| Development | 2019-01-31 → 2023-12-29; 60 snapshot |
| Holdout V2 | 2024–2025; không dùng trong Nhiệm vụ 6–9 |
| Eligibility | market_feature_ready_v2; xét riêng từng snapshot |
| Số mã tối thiểu theo protocol | 100 |
| Quy mô quan sát thực tế | 116–955 mã/snapshot; trung bình 498.45 |
| Assignments / Profiles / Models | 29907 / 120 / 60 |
| Scaler | Robust Scaling riêng từng snapshot: (x − median) / IQR |
| Missing / Outlier | Không impute; winsor_quantile=0; clipping=false |
| Global K | 2 |
| PCA | 2 chiều cố định; ngưỡng phương sai tích lũy ≥90% |
| seed / n_init / max_iter | 42 / 10 / 300 |
| K=2 hội tụ | 60/60 snapshot |

Manifest ghi nhận phiên chạy từ 19:27:21 đến 19:40:26 ngày
21/10/2026, múi giờ UTC+7; trạng thái `complete` và
`task6_exports_complete=true`. Số mã thấp nhất là 116 tại 2021-12-31 và 2022-01-28;
cao nhất là 955 tại 2023-12-29. Tổng 29.907 assignments là tổng số dòng cổ
phiếu–snapshot qua 60 tháng, không phải 29.907 cổ phiếu riêng biệt.

### 3. Quy trình và nội dung kiểm chứng

1. Đọc feature market-only và kiểm tra Global K=2 đã được phê duyệt cùng các hash nguồn.
2. Với từng tháng, fit Robust Scaler trên universe của chính tháng đó; không fit
   chung toàn bộ giai đoạn, không dùng dữ liệu tương lai hoặc holdout.
3. Đánh giá số PC cần để giữ ít nhất 90% phương sai trên development, ghi freeze
   trước lần huấn luyện; sau đó áp dụng cùng số chiều 2 cho mọi tháng.
4. Fit K-Means trong không gian PCA với K=2 và cấu hình cố định. Lưu scaler,
   input center, PCA components/variance và centroids cho từng snapshot.
5. Lưu nhãn raw và nhãn aligned riêng. Hồ sơ kinh tế lấy mean của thành viên
   trên tám feature gốc; không thay mean gốc bằng inverse transform của PCA đã cắt chiều.
6. Đối chiếu PCA scores với input/scaler/components đã lưu, nhãn gần centroid
   nhất, kích thước cụm, hồ sơ gốc và bản sao 60 model xuất ra ngoài task directory.

`diagnostics.csv` có 420 dòng cho K=2…8 do runner lưu chẩn đoán các K đó.
Phần kết luận của báo cáo này và Nhiệm vụ 7 chỉ lấy đúng 60 dòng **K=2**, phù hợp
Global K đã freeze; không chọn lại K từ bảng chẩn đoán của Nhiệm vụ 6.

## B — Quy tắc PCA và cấu trúc giảm chiều

### 1. Vì sao freeze hai thành phần chính?

Đặt r(t) là số PC nhỏ nhất để cumulative explained variance của tháng t đạt
90%. Quy tắc chung là **r = max r(t)** trên development. Có 53/60 tháng chỉ cần
một PC và 7/60 tháng cần hai PC, nên freeze r=2 cho toàn bộ chuỗi.

Với hai PC, phương sai giữ lại thấp nhất **91.948110%**, trung vị **99.233131%**
và cao nhất **99.973090%**. Mức thấp nhất ở 2022-03-31 vẫn vượt ngưỡng 90%;
không có tháng nào phải thay số chiều riêng. Freeze này chỉ phản ánh development;
không được tự thay đổi sau khi xem holdout.

### 2. Kiểm chứng theo từng tháng

| Snapshot | Số mã | Số PC tối thiểu ≥90% | Số PC đã freeze | Phương sai PC1 (%) | Phương sai PC1+PC2 (%) |
| --- | --- | --- | --- | --- | --- |
| 2019-01-31 | 656 | 1 | 2 | 98.837557 | 99.444682 |
| 2019-02-28 | 656 | 1 | 2 | 99.091407 | 99.501801 |
| 2019-03-29 | 662 | 1 | 2 | 96.401625 | 98.269073 |
| 2019-04-26 | 669 | 1 | 2 | 96.848809 | 98.417765 |
| 2019-05-31 | 680 | 1 | 2 | 98.386036 | 99.232659 |
| 2019-06-28 | 695 | 1 | 2 | 98.556257 | 99.285380 |
| 2019-07-31 | 706 | 1 | 2 | 96.691234 | 99.166801 |
| 2019-08-30 | 761 | 1 | 2 | 98.160728 | 99.102708 |
| 2019-09-30 | 781 | 1 | 2 | 97.992332 | 99.112861 |
| 2019-10-31 | 771 | 2 | 2 | 87.149281 | 98.545819 |
| 2019-11-29 | 773 | 1 | 2 | 96.552829 | 99.207664 |
| 2019-12-31 | 673 | 1 | 2 | 99.284438 | 99.719337 |
| 2020-01-31 | 613 | 1 | 2 | 99.457493 | 99.762644 |
| 2020-02-28 | 631 | 1 | 2 | 99.714810 | 99.861693 |
| 2020-03-31 | 495 | 1 | 2 | 99.423316 | 99.723575 |
| 2020-04-29 | 454 | 1 | 2 | 98.109762 | 99.041827 |
| 2020-05-29 | 453 | 1 | 2 | 96.974878 | 98.594987 |
| 2020-06-30 | 401 | 2 | 2 | 85.377422 | 92.656022 |
| 2020-07-31 | 403 | 1 | 2 | 90.065924 | 95.883333 |
| 2020-08-31 | 403 | 1 | 2 | 91.198725 | 95.752921 |
| 2020-09-30 | 394 | 1 | 2 | 93.700442 | 96.481058 |
| 2020-10-30 | 395 | 1 | 2 | 98.630785 | 99.233603 |
| 2020-11-30 | 315 | 1 | 2 | 95.535787 | 98.162907 |
| 2020-12-31 | 362 | 2 | 2 | 89.491685 | 94.286211 |
| 2021-01-29 | 470 | 1 | 2 | 92.795300 | 96.747251 |
| 2021-02-26 | 401 | 1 | 2 | 93.711165 | 97.686768 |
| 2021-03-31 | 262 | 1 | 2 | 98.934150 | 99.641671 |
| 2021-04-29 | 273 | 1 | 2 | 98.611453 | 99.505853 |
| 2021-05-31 | 250 | 1 | 2 | 98.831210 | 99.655604 |
| 2021-06-30 | 322 | 1 | 2 | 99.563473 | 99.778965 |
| 2021-07-30 | 311 | 1 | 2 | 99.418506 | 99.750053 |
| 2021-08-31 | 241 | 1 | 2 | 98.740554 | 99.418537 |
| 2021-09-30 | 166 | 1 | 2 | 96.091421 | 98.294921 |
| 2021-10-29 | 145 | 1 | 2 | 95.811899 | 98.207340 |
| 2021-11-30 | 173 | 1 | 2 | 96.381181 | 98.905107 |
| 2021-12-31 | 116 | 2 | 2 | 89.570367 | 96.099311 |
| 2022-01-28 | 116 | 2 | 2 | 85.303705 | 95.297790 |
| 2022-02-28 | 156 | 1 | 2 | 97.765944 | 98.803624 |
| 2022-03-31 | 261 | 2 | 2 | 83.248674 | 91.948110 |
| 2022-04-29 | 253 | 2 | 2 | 88.842440 | 97.056270 |
| 2022-05-31 | 267 | 1 | 2 | 97.186449 | 98.509594 |
| 2022-06-30 | 269 | 1 | 2 | 98.781349 | 99.435816 |
| 2022-07-29 | 238 | 1 | 2 | 95.039965 | 97.403317 |
| 2022-08-31 | 264 | 1 | 2 | 90.642699 | 94.186027 |
| 2022-09-30 | 313 | 1 | 2 | 92.750295 | 96.416454 |
| 2022-10-31 | 377 | 1 | 2 | 99.416969 | 99.771367 |
| 2022-11-30 | 366 | 1 | 2 | 99.385167 | 99.691607 |
| 2022-12-30 | 473 | 1 | 2 | 99.594460 | 99.823205 |
| 2023-01-31 | 608 | 1 | 2 | 99.838557 | 99.907584 |
| 2023-02-28 | 605 | 1 | 2 | 99.788770 | 99.884550 |
| 2023-03-31 | 608 | 1 | 2 | 99.806522 | 99.897727 |
| 2023-04-28 | 896 | 1 | 2 | 99.788992 | 99.889984 |
| 2023-05-31 | 891 | 1 | 2 | 99.744836 | 99.860654 |
| 2023-06-30 | 846 | 1 | 2 | 99.729618 | 99.852447 |
| 2023-07-31 | 895 | 1 | 2 | 99.637387 | 99.822962 |
| 2023-08-31 | 899 | 1 | 2 | 99.721878 | 99.868435 |
| 2023-09-29 | 726 | 1 | 2 | 99.945298 | 99.970739 |
| 2023-10-31 | 796 | 1 | 2 | 99.939661 | 99.971383 |
| 2023-11-30 | 897 | 1 | 2 | 99.951160 | 99.973090 |
| 2023-12-29 | 955 | 1 | 2 | 99.767886 | 99.888431 |

### 3. Vai trò của các feature trong không gian PCA

Bảng sau lấy trung bình trị tuyệt đối loading qua 60 PCA đã lưu. Lấy trị tuyệt
đối để tránh dấu của eigenvector giữa các tháng triệt tiêu nhau; đây là thống kê
loading, không phải kiểm định nhân quả hoặc tỷ lệ đóng góp lợi nhuận.

| Feature | Mean \|loading PC1\| | Mean \|loading PC2\| |
| --- | --- | --- |
| mom_21 | 0.005972 | 0.448238 |
| mom_63 | 0.009674 | 0.514009 |
| mom_126 | 0.010138 | 0.476908 |
| mom_252 | 0.007248 | 0.411907 |
| vol_63 | 0.004528 | 0.086735 |
| mdd_126 | 0.003398 | 0.072082 |
| beta_126 | 0.013820 | 0.064631 |
| liquidity_21 | 0.998794 | 0.015441 |

Mean |loading PC1| của `liquidity_21` là 0.998794, vượt rõ các
feature còn lại. PC1 có median explained variance 98.471146%. Hai kết quả cho
thấy phương sai sau Robust Scaling tập trung mạnh theo trục thanh khoản.
Việc giữ được trên 90% phương sai không đồng nghĩa mọi chiều kinh tế được đại
diện cân bằng; Robust Scaling theo median/IQR vẫn giữ ảnh hưởng của phần đuôi.
Hồ sơ và mức chênh lệch của hai cụm được phân tích riêng ở Nhiệm vụ 8.

## C — Bàn giao, kết luận và giới hạn

### 1. Kết quả sẵn sàng cho Nhiệm vụ 7–9

| Nhóm đầu ra | Nội dung và quy mô |
| --- | --- |
| Nhãn và điểm PCA | 29907 assignments; 29907 dòng PC1–PC2; có CSV/JSONL |
| Hồ sơ cụm gốc | 120 profile; `cluster_profiles.csv` 13 cột |
| Kiểm chứng giảm chiều | 60 dòng PCA diagnostics; loadings; centroids PCA; scaler parameters |
| Model | 60 file trong task directory và 60 bản xuất ở `M2/models/pca_kmeans/` |
| Chất lượng | 60 chẩn đoán K=2 dùng cho Nhiệm vụ 7 |
| Temporal | Assignments/profiles/transitions/stability dùng chuẩn hóa Nhiệm vụ 9 |
| Tái lập | Config, freeze, input features, source snapshot, run metadata và manifest checksum |

Median chất lượng K=2 là Silhouette **0.939741**, DB
**0.383600**, CH **1177.053847**, Inertia
**81023.955397**, Balance **0.023814**. Đây là đầu ra
đo lường; biện luận về mất cân bằng và singleton nằm ở
[báo cáo Nhiệm vụ 7](Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_PCA_KMeans_v2.md).

### 2. Phán quyết

Nhiệm vụ 6 hoàn tất về thực thi và xuất kết quả: 60/60 snapshot, 60 model K=2
hội tụ, toàn bộ tháng đạt ngưỡng phương sai và manifest hoàn chỉnh. Đầu ra đã
được Nhiệm vụ 7, 8, 9 sử dụng và các manifest tương ứng đều `complete`.

Giới hạn vẫn là market-only: không nâng thành historical-identity/research-ready
universe, không kết luận hiệu quả đầu tư hoặc lựa chọn phương án thắng. Đây là
phân cụm độc lập từng tháng kết hợp theo dõi nhãn, chưa phải Dynamic Clustering.
Task 10 V2 trên Git đã hoàn tất đối chiếu cùng dữ liệu/universe/60 tháng và
chọn **KMeans_Baseline, K=2**; PCA + K-Means được giữ làm comparator. Xem
[quyết định Task 10 V2](../artifacts/m2-evaluation-v2/final_method_decision.json).
Việc cập nhật báo cáo này không thay quyết định đã freeze và không thực thi holdout V2.

## Nguồn và khả năng kiểm chứng

- [Kế hoạch M2](../Ke_hoach_M2_Phan_cum_co_phieu.md), phần Nhiệm vụ 6.
- [Notebook thực thi](../notebooks/06_pca_kmeans_v2_rerun.ipynb).
- [Config PCA V2](../../configs/experiments/m2_pca_market_only_v2.json).
- [PCA freeze](../artifacts/m2-task6-pca-freeze-v2/freeze.json).
- [Manifest Nhiệm vụ 6](../artifacts/m2-task6-pca-kmeans-v2/manifest.json).
- [PCA diagnostics](../artifacts/m2-task6-pca-kmeans-v2/pca_diagnostics.csv).
- [PCA loadings](../artifacts/m2-task6-pca-kmeans-v2/pca_loadings.csv).
- [Mẫu báo cáo cũ trong notebook ở commit a436eb8](https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/a436eb83214c18219da4a990851b8121df0a3e94/M2/notebooks/06_pca_kmeans.ipynb).

Trước khi biên soạn đã đối chiếu checksum các đầu ra được manifest Nhiệm vụ
6–9 tham chiếu, cấu hình, số dòng và phạm vi ngày. Quá trình viết báo cáo chỉ
đọc kết quả đã lưu; không huấn luyện lại, không sửa model/scaler/PCA và không
truy cập dữ liệu holdout 2024–2025.
