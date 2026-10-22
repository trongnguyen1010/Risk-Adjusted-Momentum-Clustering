# Nhiệm vụ 9 — Độ ổn định theo thời gian của K-Means trên C8 v2

**Trạng thái: PASS.** Đánh giá 59 cặp tháng liên tiếp của 60 snapshot development 2019-01-31 đến 2023-12-29. Nguồn là assignments và profiles của Nhiệm vụ 4; notebook Nhiệm vụ 9 chỉ đọc ba CSV temporal, không fit lại model.

| Metric | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| ARI | 0.727974 | 0.757047 | 0.316106 | 1.000000 |
| NMI | 0.606640 | 0.602909 | 0.250430 | 1.000000 |
| Persistence | 98.9790% | 99.0071% | 95.8801% | 100.0000% |
| Migration | 1.0210% | 0.9929% | 0.0000% | 4.1199% |

ARI/NMI đo độ giống nhau của partition trên tập mã chung; persistence/migration đo tỷ lệ giữ hoặc đổi cụm sau label alignment. Chúng không phải portfolio turnover, chi phí giao dịch hay hiệu quả đầu tư. `n_common` dao động từ 114 đến hơn 1.000 mã theo sự mở rộng tự nhiên của thị trường. Đây là monthly independent K-Means cộng temporal tracking, không phải Dynamic Clustering.

Evidence đầu vào đúng schema: `M2/artifacts/m2-evaluation-kmeans/temporal_stability.csv` (59 dòng), `transition_matrices.csv` (236 dòng) và `centroid_drift.csv` (944 dòng). Notebook `M2/notebooks/09_temporal_stability_kmeans.ipynb` đã tạo `temporal_trends.png` và `transition_heatmap.png` cùng thư mục. Không nối development sang holdout.
