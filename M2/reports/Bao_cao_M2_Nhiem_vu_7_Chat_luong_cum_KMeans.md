# Nhiệm vụ 7 — Chất lượng cụm K-Means trên C8 v2

**Trạng thái: PASS.** Báo cáo chỉ đọc 60 dòng K=2 trong `M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv`; không fit lại K-Means, không dùng return hoặc portfolio metrics.

| Metric | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| Silhouette | 0,918276 | 0,931935 | 0,808108 | 0,974962 |
| Davies-Bouldin | 0,375066 | 0,396416 | 0,021757 | 0,549972 |
| Calinski-Harabasz | 1212,607802 | 1122,325007 | 239,393615 | 3327,930048 |
| Inertia | 413867,196225 | 82143,837336 | 2085,426538 | 5017235,321248 |
| Cluster balance | 0,027176 | 0,023814 | 0,006452 | 0,069333 |

Median Silhouette cao đi cùng balance rất thấp: K-Means thường tách một nhóm mã nhỏ khỏi phần lớn universe. Không coi Silhouette cao là bằng chứng về hai nhóm cân bằng hoặc khả năng sinh lời. Inertia thay đổi cùng quy mô universe nên không so trực tiếp giữa các tháng.

Notebook `M2/notebooks/07_cluster_quality_evaluation_kmeans.ipynb` tạo `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv` đúng schema 5 dòng × 7 cột và 5 biểu đồ trong `figures/quality_7_1.png` đến `quality_7_5.png`. Đây là evidence riêng cho K-Means; chưa so sánh Ward/PCA hoặc chọn mô hình cuối.

Đã đối chiếu offline: các median trong báo cáo khớp `diagnostics.csv` và không thiếu snapshot.
