# Nhiệm vụ 4 — K-Means Baseline trên C8 v2

**Trạng thái: PASS.** K-Means được fit lại độc lập trên 60 snapshot development (2019-01-31 đến 2023-12-29) của `cafef-c8-complete-only-v2`. Global K=2 lấy từ quyết định đã khóa ở Nhiệm vụ 3; không thử lại K, không mở holdout.

## Phương pháp

- Input: `configs/experiments/m2_market_only_v2.json` và `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/feature_snapshots.jsonl`.
- Dữ liệu sạch 10 năm `cafef-c8-complete-only-v2` chuẩn hóa đầy đủ theo M1 V2 (1.522 mã cổ phiếu).
- Universe: `market_feature_ready_v2=true` theo từng snapshot, ít nhất 100 mã; đúng 8 feature market.
- Robust Scaling fit riêng từng snapshot, sau đó `sklearn.cluster.KMeans(n_clusters=2, random_state=42, n_init=10, max_iter=300)`.
- Notebook thực thi: `M2/notebooks/04_kmeans_baseline.ipynb`; model và scaler: `M2/models/kmeans/`.
- Artifact đúng tên kế hoạch: `M2/artifacts/m2-task4-kmeans-baseline-v1/`.

## Kết quả

- 60/60 snapshot hoàn thành, **45.646 assignments**, **120 cluster profiles**, 60 model theo tháng.
- **Median Silhouette: 0.940837**; **Davies-Bouldin: 0.403127**; **Calinski-Harabasz: 1586.371240**; **cluster balance: 0.020996**.
- Phân bổ quy mô cụm: Cụm 0 trung bình 14.9 mã/tháng (nhóm biến động mạnh/đặc thù), Cụm 1 trung bình 745.9 mã/tháng (đại chúng thị trường).
- `diagnostics.csv` có 60 dòng K=2 và các cột bắt buộc của Nhiệm vụ 7; `cluster_profiles.csv` có 120 dòng, 13 cột bắt buộc của Nhiệm vụ 8.
- `assignments.jsonl`, `profiles.jsonl`, `diagnostics.jsonl`, `manifest.json`, các CSV đối chiếu và SHA-256 nằm trong artifact v1.
- Bước hậu xử lý trong notebook Nhiệm vụ 4 tạo ba CSV temporal tại `M2/artifacts/m2-evaluation-kmeans/` cho Nhiệm vụ 9; không fit lại model.
- Cùng notebook đồng bộ `cluster_profiles.csv` (120 dòng), `cluster_profile_members.csv` (45.646 dòng) và `profile_scaler_reference.csv` (960 dòng) trong thư mục evaluation K-Means từ artifact Nhiệm vụ 4.
- `manifest.json` ghi SHA-256 của manifest và feature snapshot C8, cùng protocol 60 tháng, để kiểm tra lineage.

## Self-review

Kiểm tra đủ 60 ngày development, không trùng cặp snapshot/security_id, đúng K=2, tám feature, eligibility tối thiểu, model/scaler từng tháng và metric hữu hạn. Kết quả khớp partition K=2 của Nhiệm vụ 3 khi cùng dùng scikit-learn. Không thay file hoặc artifact của Nhiệm vụ 1–3.

Toàn bộ kiểm tra tính toàn vẹn và synthetic smoke PASS. Kết quả sẵn sàng bàn giao cho các nhiệm vụ tiếp theo.
