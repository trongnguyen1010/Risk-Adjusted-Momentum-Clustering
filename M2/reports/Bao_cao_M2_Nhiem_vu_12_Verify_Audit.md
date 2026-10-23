# BÁO CÁO M2 — NHIỆM VỤ 12: KIỂM TOÁN TÍNH TOÀN VẸN VÀ RÀO CHẮN HỌC THUẬT (VERIFICATION & AUDIT)

**Mã tài liệu:** `M2-REP-TASK12-VERIFY-AUDIT`  
**Milestone:** `M2_CLUSTERING_RESEARCH`  
**Ngày kiểm toán:** 23/10/2026  
**Đơn vị thực hiện:** Đội ngũ Kiểm định Tự động Milestone M2 (`M2_AUTOMATED_VERIFICATION_SUITE`)  
**Trạng thái phán quyết:** `VERIFIED_PASS`  

---

## 1. Mục đích và Phạm vi Kiểm toán

Căn cứ theo quy định tại `M2/Ke_hoach_M2_Phan_cum_co_phieu.md` (Nhiệm vụ 12) và các nguyên tắc bất biến tại `docs/DELTA_UNIFIED_PROJECT_PLAN.md` (Mục 4 và Mục 9), cuộc kiểm toán độc lập này nhằm đánh giá toàn diện tính toàn vẹn kỹ thuật, rào chắn học thuật, và tính bất biến của dữ liệu trước khi nghiệm thu Milestone M2 và bàn giao cho Milestone M3 (Portfolio / Backtest).

Quá trình kiểm toán được thực thi tự động thông qua notebook `M2/notebooks/12_m2_verification_audit.ipynb`, xuất hồ sơ kiểm toán tại `M2/artifacts/m2-verify-v1/`.

---

## 2. Bảng Tổng kết 8 Tiêu chí Kiểm toán Bắt buộc (8-point Audit Checklist)

| Tiêu chí | Tên tiêu chí | Phạm vi đối chiếu | Giá trị kỳ vọng | Giá trị thực tế quan sát được | Phán quyết |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **Audit 1** | **Config & Input Lineage** | Feature Store 1.6.0 & Config | SHA-256 khớp manifest C8 (`ab1a34a8...`) | Trùng khớp 100% SHA-256 (`ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`) | **PASS** |
| **Audit 2** | **Global K Selection Integrity** | Development (60 snapshots, 420 runs) | K=2 đạt Median Silhouette cao nhất trên Dev | K=2 đạt Median Silhouette = 0.9408, DB = 0.4031 (cao nhất trong K=2..8); K=2 đã đóng băng | **PASS** |
| **Audit 3** | **Zero Future / Holdout Leakage** | Dấu thời gian & ranh giới Dev/Holdout | `decision_timestamp < holdout_opened_at` | Quyết định đóng băng: `2026-10-22T05:57:06+00:00`; Mở Holdout: `2026-10-22T08:49:06.592640+00:00` | **PASS** |
| **Audit 4** | **Train/Holdout Boundary Verification** | Chuỗi 84 snapshots liên tục (Zero gaps) | Ngắt chuỗi dịch chuyển tại ranh giới Dev-Holdout | Không tồn tại cặp `2023-12-29 -> 2024-01-31`; Dev gồm 59 cặp, Holdout gồm 23 cặp hoàn toàn độc lập | **PASS** |
| **Audit 5** | **Per-Snapshot Universe Integrity** | Toàn bộ 84 snapshots | `market_feature_ready_v2 = true` & `n_eligible >= 100` | Min eligible = 503, Max = 1.410, Mean = 902.4; 84/84 snapshots thỏa mãn, không áp đặt vũ trụ terminal | **PASS** |
| **Audit 6** | **Strict Single Model Holdout** | Holdout (24 snapshots) | Chỉ chạy duy nhất mô hình chiến thắng | `methods_executed = ["kmeans"]`, `k_values_executed = [2]`; Ward và PCA bị loại trừ khỏi Holdout | **PASS** |
| **Audit 7** | **No Portfolio Metrics in Selection** | Bảng so sánh & tiêu chí lựa chọn | Không có Sharpe, CAGR, ROI, Alpha trong chọn mô hình | Bảng so sánh 100% hình học/thống kê; `portfolio_evaluation_enabled = false` trên Holdout | **PASS** |
| **Audit 8** | **Deterministic Reproducibility** | Unit & Regression Fixtures | Trùng khớp 100% nhãn cụm (ARI = 1.0) và tâm cụm | 3/3 tests passed (`AlgorithmTests`); ARI = 1.000000; Sai số tâm cụm tuyệt đối = 0.0000000000 | **PASS** |

---

## 3. Chi tiết Kết quả Kiểm toán Từng Tiêu chí

### 3.1. Audit 1 — Tính toàn vẹn cấu hình và nguồn dữ liệu (Config & Input Lineage)
- **Tập tin dữ liệu đặc trưng:** `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/feature_snapshots.jsonl` (Kích thước: 234.435.324 bytes).
- **Mã băm SHA-256 thực tế:** `ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`.
- **Mã băm lưu trong Manifest C8:** `ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`.
- **File cấu hình thực nghiệm:** `configs/experiments/m2_market_only_v2.json` có mã băm `473ee518cee8d663c9719df1de3f0d18e579f51dbcf99f86f828575696d037cf`, trùng khớp 100% với giá trị ghi nhận trong `global_k_decision.json`.
- **Kết luận:** Dữ liệu đầu vào M1 (C8) hoàn toàn bất biến (immutable), không bị chỉnh sửa tại chỗ (in-place mutation).

### 3.2. Audit 2 — Tính liêm chính trong lựa chọn Global K (Global K Selection Integrity)
- Quét ma trận chẩn đoán từ 420 lượt chạy thực nghiệm (`60 snapshots x 7 giá trị K từ 2 đến 8`) tại `M2/artifacts/m2-task3-development-v1/aggregate_by_k.csv`:
  - $K=2$: Median Silhouette = **0.9408** (Cao nhất), Median DB = **0.4031**, Calinski-Harabasz = 1586.37.
  - $K=3$: Median Silhouette = 0.9064, Median DB = 0.3882.
  - $K=4$: Median Silhouette = 0.8869, Median DB = 0.4005.
  - $K=5$: Median Silhouette = 0.8614, Median DB = 0.4012.
  - $K=6$: Median Silhouette = 0.8345, Median DB = 0.4069.
  - $K=7$: Median Silhouette = 0.8003, Median DB = 0.4030.
  - $K=8$: Median Silhouette = 0.7517, Median DB = 0.4119.
- Quyết định đóng băng $K=2$ tuân thủ nghiêm ngặt nguyên tắc hình học (Median Silhouette cực đại), không sử dụng bất kỳ chỉ số lợi nhuận hay holdout nào.

### 3.3. Audit 3 — Ngăn chặn rò rỉ dữ liệu tương lai và ngoài mẫu (Zero Leakage Audit)
- Kiểm tra dấu thời gian chuỗi quyết định:
  - Biên bản đóng băng lựa chọn mô hình (`final_method_decision.json`): `2026-10-22T05:57:06+00:00`.
  - Thời điểm bắt đầu mở tập Holdout (`manifest.json`): `2026-10-22T08:49:06.592640+00:00`.
  - Thời điểm hoàn thành chạy Holdout: `2026-10-22T08:50:31.050457+00:00`.
- Biên bản quyết định phương pháp hoàn thành trước khi dữ liệu Holdout được nạp vào bộ nhớ gần 3 giờ đồng hồ. Không có bất kỳ quan sát hay scaler nào của Holdout bị rò rỉ ngược về Development.

### 3.4. Audit 4 — Xác thực phân định ranh giới Train/Holdout (Train/Holdout Boundary Audit)
- Toàn bộ chuỗi 84 snapshots liên tục từ `31/01/2019` đến `31/12/2025` không bị gián đoạn dữ liệu (zero gaps).
- Chuỗi Development gồm 60 snapshots: kết thúc tại `2023-12-29`, với cặp dịch chuyển cuối cùng là `2023-11-30 -> 2023-12-29` (59 cặp).
- Chuỗi Holdout gồm 24 snapshots: bắt đầu tại `2024-01-31`, với cặp dịch chuyển đầu tiên là `2024-01-31 -> 2024-02-29` (23 cặp).
- Quét các bảng `temporal_stability.csv` khẳng định không tồn tại cặp nối `2023-12-29 -> 2024-01-31`. Cơ chế ngắt chuỗi chuyển dịch tại khoảng phân định hoạt động chính xác 100%.

### 3.5. Audit 5 — Tính toàn vẹn vũ trụ đầu tư theo từng snapshot (Per-Snapshot Universe Integrity)
- Không áp dụng vũ trụ terminal 1.410 mã tại 12/2025 ngược về quá khứ (loại bỏ hoàn toàn survivorship bias).
- Tại mỗi tháng trong 84 tháng, chỉ các cổ phiếu thỏa mãn đồng thời:
  1. `market_feature_ready_v2 = true` (đủ lịch sử giao dịch và chuẩn hóa đặc trưng).
  2. `n_eligible >= 100` (đảm bảo mật độ thống kê cụm).
- Thống kê quan sát thực tế: Tháng thấp nhất có 503 mã cổ phiếu đủ điều kiện (tháng 01/2019), tháng cao nhất đạt 1.410 mã (tháng 12/2025), trung bình đạt 902,4 mã/tháng.

### 3.6. Audit 6 — Rào chắn duy nhất một mô hình trên Holdout (Strict Single Winning Model Holdout)
- Trên tập dữ liệu Holdout (24 tháng), chỉ duy nhất mô hình chiến thắng tại Development là `KMeans_Baseline` với $K=2$ được phép thực thi.
- Manifest Holdout ghi nhận:
  - `selected_method: "KMeans_Baseline"`
  - `methods_executed: ["kmeans"]`
  - `k_values_executed: [2]`
- Hai phương án đối chứng (`Ward_Hierarchical` và `PCA_KMeans`) tuyệt đối không được thực thi trên Holdout.

### 3.7. Audit 7 — Loại trừ hoàn toàn chỉ số danh mục khỏi khâu chọn mô hình (No Portfolio Metrics)
- Kiểm tra toàn bộ 12 cột trong bảng đối chiếu phương pháp `methodology_comparison.csv`:
  `method`, `global_k`, `median_silhouette`, `mean_silhouette`, `median_davies_bouldin`, `median_calinski_harabasz`, `median_cluster_balance`, `median_ari`, `median_nmi`, `median_persistence`, `median_migration_rate`, `pipeline_complexity`.
- Hoàn toàn không xuất hiện các cột: Sharpe, CAGR, ROI, Calmar, Sortino, Alpha, hay PnL.
- Cấu hình Holdout ghi nhận tường minh: `portfolio_evaluation_enabled: false`.

### 3.8. Audit 8 — Kiểm toán tính tái lập xác định (Deterministic Reproducibility Audit)
- Kiểm thử unit test hệ thống (`tests/unit/clustering/test_algorithms.py`): Chạy thành công 3/3 tests trong 2,014 giây (`AlgorithmTests.test_explicit_sklearn_kmeans_matches_library`, `test_registry_has_static_baseline_and_comparator`, `test_ward_is_deterministic`).
- Tái lập xác định in-memory trực tiếp: So sánh 2 lần chạy độc lập của `sklearn.cluster.KMeans` với cùng `random_state=42`, `n_init=10`, `max_iter=300`:
  - Adjusted Rand Index (ARI): **1.000000** (Trùng khớp 100%).
  - Độ lệch tuyệt đối tâm cụm lớn nhất: **0.0000000000** (Zero tolerance difference).

---

## 4. Danh mục 22 Artifacts Cốt lõi được Kiểm chứng và Đóng băng

1. `configs/experiments/m2_market_only_v2.json`
2. `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/feature_snapshots.jsonl`
3. `artifacts/cafef_primary/cafef-c8-complete-only-v2/manifest.json`
4. `M2/artifacts/m2-task3-development-v1/per_snapshot_k_metrics.csv`
5. `M2/artifacts/m2-task3-development-v1/aggregate_by_k.csv`
6. `M2/artifacts/m2-task3-development-v1/global_k_decision.json`
7. `M2/artifacts/m2-task4-kmeans-baseline-v1/manifest.json`
8. `M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv`
9. `M2/artifacts/m2-task5-ward-v1/manifest.json`
10. `M2/artifacts/m2-task6-pca-freeze/manifest.json`
11. `M2/artifacts/m2-evaluation-kmeans/cluster_profiles.csv`
12. `M2/artifacts/m2-evaluation-kmeans/temporal_stability.csv`
13. `M2/artifacts/m2-evaluation-ward/cluster_profiles.csv`
14. `M2/artifacts/m2-evaluation-ward/temporal_stability.csv`
15. `M2/artifacts/m2-evaluation-pca-kmeans/cluster_profiles.csv`
16. `M2/artifacts/m2-evaluation-pca-kmeans/temporal_stability.csv`
17. `M2/artifacts/m2-evaluation-v2/final_method_decision.json`
18. `M2/artifacts/m2-evaluation-v2/methodology_comparison.csv`
19. `M2/artifacts/m2-final-holdout/manifest.json`
20. `M2/artifacts/m2-final-holdout/assignments.csv`
21. `M2/artifacts/m2-final-holdout/diagnostics.csv`
22. `M2/artifacts/m2-final-holdout/temporal_stability.csv`

---

## 5. Kết luận và Bàn giao sang Nhiệm vụ 13 (M3 Handoff)

- **Phán quyết chính thức:** `VERIFIED_PASS` (100% tiêu chí đạt yêu cầu rào chắn học thuật).
- **Hồ sơ kiểm toán được xuất tại:**
  - Biên bản máy đọc: `M2/artifacts/m2-verify-v1/verification_summary.json`
  - Bảng bằng chứng chi tiết: `M2/artifacts/m2-verify-v1/audit_evidence.csv`
  - Notebook kiểm toán tái lập: `M2/notebooks/12_m2_verification_audit.ipynb`
- **Ủy quyền chuyển tiếp:** Hệ thống chính thức đủ điều kiện mở niêm phong gói bàn giao sang Milestone M3 (Portfolio / Backtest) thông qua Nhiệm vụ 13.
