# Nhiệm vụ 7 — Chất lượng cụm K-Means trên C8 v2

**Trạng thái: PASS.** Báo cáo chỉ đọc 60 dòng K=2 trong `M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv`; không fit lại K-Means, không dùng return hoặc portfolio metrics.

| Metric | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| Silhouette | 0.941310 | 0.940837 | 0.886026 | 0.980371 |
| Davies-Bouldin | 0.397471 | 0.403127 | 0.203519 | 0.506836 |
| Calinski-Harabasz | 1729.885377 | 1586.371240 | 677.981134 | 3805.766000 |
| Inertia | 852145.312130 | 376102.139178 | 60452.188108 | 3975051.321248 |
| Cluster balance | 0.020708 | 0.020996 | 0.003252 | 0.050794 |

Median Silhouette cao (0.9408) đi cùng balance thấp (0.0210): K-Means Baseline tách rõ rệt một nhóm nhỏ các mã có biến động/động lượng đột biến khỏi phần lớn đại chúng thị trường. Không coi Silhouette cao là bằng chứng về hai nhóm cân bằng hoặc khả năng sinh lời. Inertia tăng theo quy mô số mã niêm yết của universe qua các năm.

Notebook `M2/notebooks/07_cluster_quality_evaluation_kmeans.ipynb` tạo `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv` đúng schema 5 dòng x 7 cột và 5 biểu đồ trong `figures/quality_7_1.png` đến `quality_7_5.png`.

Toàn bộ các giá trị trung vị và phân vị trong báo cáo khớp 100% với `diagnostics.csv` và dữ liệu thực chứng.
