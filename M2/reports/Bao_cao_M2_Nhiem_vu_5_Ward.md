# Nhiệm vụ 5 — Ward Hierarchical trên C8 v2

**Trạng thái: PASS.** Ward Hierarchical (phương án B) được fit độc lập trên 60 snapshot development (2019-01-31 đến 2023-12-29) của `cafef-c8-complete-only-v2`. Global K=2 lấy từ quyết định đã khóa ở Nhiệm vụ 3; không thử lại K, không mở holdout.

## Phương pháp

- Input: `configs/experiments/m2_ward_market_only_v2.json` và `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/feature_snapshots.jsonl`.
- Dữ liệu sạch 10 năm `cafef-c8-complete-only-v2` chuẩn hóa đầy đủ theo M1 V2 (1.522 mã cổ phiếu).
- Universe: `market_feature_ready_v2=true` theo từng snapshot, ít nhất 100 mã; đúng 8 feature market.
- Robust Scaling fit riêng từng snapshot, sau đó thực hiện phân cụm phân cấp liên kết Ward (`scipy.cluster.hierarchy.linkage(method="ward")` và cắt tại K = 2 bằng `fcluster`).
- Notebook thực thi: `M2/notebooks/05_ward_hierarchical.ipynb`; model và linkage: `M2/models/ward/`.
- Artifact đúng tên kế hoạch: `M2/artifacts/m2-task5-ward-v1/`.

## Kết quả

- 60/60 snapshot hoàn thành, **45.646 assignments**, **120 cluster profiles**, 60 model theo tháng.
- **Median Silhouette: 0.946262**; **Davies-Bouldin: 0.373575**; **Calinski-Harabasz: 1525.513880**; **cluster balance: 0.019054**.
- Phân bổ quy mô cụm: Cụm 0 trung bình 743.9 mã/tháng (đại chúng thị trường), Cụm 1 trung bình 16.9 mã/tháng (cổ phiếu trụ / thanh khoản cao).
- `diagnostics.csv` có 60 dòng K=2 và các cột bắt buộc của Nhiệm vụ 7; `cluster_profiles.csv` có 120 dòng, 13 cột bắt buộc của Nhiệm vụ 8.
- `assignments.jsonl`, `profiles.jsonl`, `diagnostics.jsonl`, `manifest.json`, các CSV đối chiếu và SHA-256 nằm trong artifact v1.
- Dữ liệu temporal được xuất đầy đủ sang `M2/artifacts/m2-evaluation-ward/` phục vụ Nhiệm vụ 9; không fit lại model.
- `manifest.json` ghi SHA-256 của manifest và feature snapshot C8, cùng protocol 60 tháng, để kiểm tra lineage.

## Self-review

Kiểm tra đủ 60 ngày development, không trùng cặp snapshot/security_id, đúng K=2, tám feature, eligibility tối thiểu, model/linkage từng tháng và metric hữu hạn. Kết quả deterministic, đảm bảo tính lặp lại độc lập. Không thay file hoặc artifact của Nhiệm vụ 1–4.

Toàn bộ kiểm tra tính toàn vẹn PASS. Kết quả sẵn sàng bàn giao cho các nhiệm vụ đánh giá tiếp theo (Nhiệm vụ 7, 8, 9, 10).
