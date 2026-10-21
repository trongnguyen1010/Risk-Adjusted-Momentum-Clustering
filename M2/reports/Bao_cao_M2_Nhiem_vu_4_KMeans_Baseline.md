# Nhiệm vụ 4 — K-Means Baseline trên C8 v2

**Trạng thái: PASS.** K-Means được fit lại độc lập trên 60 snapshot development (2019-01-31 đến 2023-12-29) của `cafef-c8-complete-only-v2`. Global K=2 lấy từ quyết định đã khóa ở Nhiệm vụ 3; không thử lại K, không mở holdout.

## Phương pháp

- Input: `configs/experiments/m2_market_only_v2.json` và `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/feature_snapshots.jsonl`.
- ZIP `DELTA_02_ACTIVE_M2_M3.zip` trong Downloads đã được giải nén đúng đường dẫn: 18/18 file đóng gói khớp checksum; `feature_snapshots.jsonl` khớp hash trong C8 manifest. ZIP không đóng gói `canonical/normalized_expansion.jsonl` và `canonical/prices_daily.jsonl` dù C8 manifest liệt kê; hai file đó không được dùng làm input của lần chạy K-Means này.
- Universe: `market_feature_ready_v2=true` theo từng snapshot, ít nhất 100 mã; đúng 8 feature market.
- Robust Scaling fit riêng từng snapshot, sau đó `sklearn.cluster.KMeans(n_clusters=2, random_state=42, n_init=10, max_iter=300)`.
- Notebook thực thi: `M2/notebooks/04_kmeans_baseline.ipynb`; model và scaler: `M2/models/kmeans/`.
- Artifact đúng tên kế hoạch: `M2/artifacts/m2-task4-kmeans-baseline-v1/`.

## Kết quả

- 60/60 snapshot hoàn thành, 29.907 assignments, 120 cluster profiles, 60 model theo tháng.
- Median Silhouette 0,931935; Davies-Bouldin 0,396416; Calinski-Harabasz 1122,325007; cluster balance 0,023814.
- `diagnostics.csv` có 60 dòng K=2 và các cột bắt buộc của Nhiệm vụ 7; `cluster_profiles.csv` có 120 dòng, 13 cột bắt buộc của Nhiệm vụ 8.
- `assignments.jsonl`, `profiles.jsonl`, `diagnostics.jsonl`, `manifest.json`, các CSV đối chiếu và SHA-256 nằm trong artifact v1.
- Bước hậu xử lý trong notebook Nhiệm vụ 4 tạo ba CSV temporal tại `M2/artifacts/m2-evaluation-kmeans/` cho Nhiệm vụ 9; không fit lại model.
- Cùng notebook đồng bộ `cluster_profiles.csv` (120 dòng), `cluster_profile_members.csv` (29.907 dòng) và `profile_scaler_reference.csv` (960 dòng) trong thư mục evaluation K-Means từ artifact Nhiệm vụ 4. Đây là đầu vào K-Means cho bước đối chiếu sau; `assignments.csv` có thêm cột tương thích `snapshot_date` bên cạnh `snapshot`.
- `manifest.json` ghi SHA-256 của manifest và feature snapshot C8, cùng protocol 60 tháng, để kiểm tra lineage với dữ liệu ZIP mới.

## Self-review

Kiểm tra đủ 60 ngày development, không trùng cặp snapshot/security_id, đúng K=2, tám feature, eligibility tối thiểu, model/scaler từng tháng và metric hữu hạn. Kết quả khớp partition K=2 của Nhiệm vụ 3 khi cùng dùng scikit-learn; đây là một phép kiểm tra tái lập, không tái sử dụng fitted model Nhiệm vụ 3. Không thay file hoặc artifact của Nhiệm vụ 1–3.

29 targeted tests clustering/runner/protocol PASS; `python -m compileall -q src tests scripts run.py` PASS; synthetic smoke `configs/data/synthetic_smoke.example.json` PASS. Mã K-Means tự viết vẫn là mặc định cho các nơi không chọn backend; Nhiệm vụ 4 chọn scikit-learn bằng config riêng `configs/experiments/m2_task4_kmeans_sklearn_v1.json`.
