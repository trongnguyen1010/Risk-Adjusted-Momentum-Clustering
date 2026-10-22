# Báo cáo M2 — Nhiệm vụ 7: Chất lượng cụm Ward

## Phạm vi và nguồn bằng chứng

- Ward Hierarchical, Global K=2 đã khóa ở Nhiệm vụ 3; 60 development snapshots từ 2019-01-31 đến 2023-12-29.
- Nguồn duy nhất: `M2/artifacts/m2-task5-ward-v1/diagnostics.csv`.
- Không fit lại model, không chọn lại K, không dùng return/Sharpe/ROI và không truy cập final holdout.

## Quy trình

Diagnostics Ward V2 đã được xuất trực tiếp tại Global K=2; toàn bộ 60 dòng đều tham gia đánh giá và tính toán các chỉ số thống kê chất lượng cụm.

## Kết quả tổng hợp

| Metric | n_total | n_available | Mean | Median | Minimum | Maximum |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Silhouette** | 60 | 60 | 0.940077 | 0.946262 | 0.872083 | 0.980371 |
| **Davies-Bouldin** | 60 | 60 | 0.372546 | 0.373575 | 0.018141 | 0.599072 |
| **Calinski-Harabasz** | 60 | 60 | 1550.576858 | 1525.513880 | 555.580181 | 3004.561000 |
| **Inertia** | 60 | 60 | 917114.822229 | 390270.700207 | 62729.223311 | 4017944.000000 |
| **Cluster balance** | 60 | 60 | 0.023793 | 0.019054 | 0.001473 | 0.067460 |

## Nhận xét học thuật

1. **Về Silhouette Score:** Ward đạt Median Silhouette rất cao (0.9463), nhỉnh hơn một chút so với K-Means Baseline (0.9408). Toàn bộ 60 snapshot đều có Silhouette > 0.87, cho thấy sự gắn kết nội cụm phân cấp rất chặt chẽ.
2. **Về Davies-Bouldin Index:** Ward đạt giá trị trung vị 0.3736, thấp hơn và tối ưu hơn K-Means (0.4031).
3. **Về Calinski-Harabasz:** Đạt trung vị 1525.51, phản ánh độ nén của cụm tốt.
4. **Về độ cân bằng cụm:** Cluster balance đạt trung vị 0.0191, tương đồng với K-Means trong việc tách nhóm cổ phiếu biến động mạnh.

Notebook `M2/notebooks/07_cluster_quality_evaluation_ward.ipynb` xuất `quality_summary.csv` đúng chuẩn tại `M2/artifacts/m2-evaluation-ward/`.
