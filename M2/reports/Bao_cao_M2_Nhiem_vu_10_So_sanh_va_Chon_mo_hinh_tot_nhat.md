# Báo cáo M2 — Nhiệm vụ 10: So sánh và chọn mô hình tốt nhất

## 1. Phạm vi, dữ liệu và rào chắn phương pháp

Báo cáo này tổng hợp **chỉ dữ liệu development** của 60 snapshot từ `2019-01-31` đến `2023-12-29`. Ba phương án dùng cùng Global K = 2, cùng 8 market features, cùng universe theo từng snapshot và cùng feature-source SHA-256 `414ed8102b1b18039eb35aa07615d55353941b641feeea60106fb3d120cac131`. Không nạp Final Holdout, không dùng return, Sharpe, ROI hay bất kỳ chỉ số đầu tư nào.

| Hạng mục kiểm định | Kết quả |
|---|---|
| Snapshot development | 60/60 cho từng phương án |
| Cặp tháng liên tiếp | 59/59 cho từng phương án |
| Số cụm mỗi snapshot | 2 |
| Feature gốc | `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21` |
| Source manifest SHA-256 | `d15f8f0b7ec87c4e883cf5b7762b9ca22127cadb703f55a48d2f6ad7caaad614` |
| Holdout | Không được đọc trong Task 10 |

Nguồn bảng: `quality_summary.csv`, `cluster_profiles.csv`, `temporal_stability.csv`, `diagnostics.csv`, `centroid_drift.csv` và model JSON của từng phương án. Đường dẫn/lineage đầy đủ được ghi trong `M2/artifacts/m2-evaluation-v2/final_method_decision.json`.

## 2. Ma trận quyết định chính thức

| Phương án | Median Silhouette ↑ | Median DB ↓ | Median CH ↑ | Median Balance ↑ | Median ARI ↑ | Median Migration ↓ | Pipeline |
|---|---:|---:|---:|---:|---:|---:|---|
| KMeans Baseline | 0.931935 | 0.396416 | 1122.325 | 0.023814 | 0.768741 | 1.0687% | Low |
| Ward Hierarchical | 0.933990 | 0.317552 | 1020.405 | 0.018855 | 0.679335 | 1.0582% | Medium |
| PCA + KMeans | 0.939741 | 0.383600 | 1177.054 | 0.023814 | 0.743427 | 1.1725% | High |

- Silhouette là tiêu chí chính; Davies–Bouldin là chỉ số xác nhận khi cần tie-break.
- ARI/Migration là kiểm tra độ bền; không phải tiêu chí thay thế Silhouette.
- Balance nhỏ cho thấy cấu trúc cụm rất bất đối xứng, cần đọc cùng bảng sanity ở mục 5.

## 3. Bảng chất lượng cụm qua 60 snapshot

| Chỉ số | KMeans Baseline | Ward Hierarchical | PCA + KMeans |
|---|---|---|---|
| Silhouette | median 0.931935; mean 0.918276; min–max 0.808108–0.974962 | median 0.933990; mean 0.918957; min–max 0.789259–0.973818 | median 0.939741; mean 0.929575; min–max 0.851754–0.977565 |
| Davies–Bouldin | median 0.396416; mean 0.375066; min–max 0.021757–0.549972 | median 0.317552; mean 0.335354; min–max 0.018141–0.580500 | median 0.383600; mean 0.365570; min–max 0.019136–0.528348 |
| Calinski–Harabasz | median 1122.325; mean 1212.608; min–max 239.394–3327.930 | median 1020.405; mean 1083.213; min–max 239.394–2461.383 | median 1177.054; mean 1253.617; min–max 279.010–3344.686 |
| Cluster Balance | median 0.023814; mean 0.027176; min–max 0.006452–0.069333 | median 0.018855; mean 0.028914; min–max 0.001473–0.116183 | median 0.023814; mean 0.027240; min–max 0.006452–0.069333 |

PCA + KMeans có Median Silhouette cao nhất (`0.939741`), Ward có Median Davies–Bouldin thấp nhất (`0.317552`), còn KMeans Baseline có Median CH nằm giữa hai comparator. Các chỉ số này chỉ mô tả hình học của cụm; không phải bằng chứng lợi suất hoặc chất lượng danh mục.

## 4. Bảng ổn định thời gian qua 59 cặp tháng

| Chỉ số | KMeans Baseline | Ward Hierarchical | PCA + KMeans |
|---|---|---|---|
| ARI | median 0.768741; mean 0.755838; min–max 0.316106–1.000000 | median 0.679335; mean 0.632621; min–max 0.058918–1.000000 | median 0.743427; mean 0.747575; min–max 0.230167–1.000000 |
| NMI | median 0.624996; mean 0.644135; min–max 0.250429–1.000000 | median 0.579373; mean 0.565780; min–max 0.102781–1.000000 | median 0.592307; mean 0.636082; min–max 0.182405–1.000000 |
| Persistence Probability | median 98.9313%; mean 98.7216%; min–max 95.8801%–100.0000% | median 98.9418%; mean 97.9382%; min–max 89.7436%–100.0000% | median 98.8275%; mean 98.6405%; min–max 95.6140%–100.0000% |
| Migration Rate | median 1.0687%; mean 1.2784%; min–max 0.0000%–4.1199% | median 1.0582%; mean 2.0618%; min–max 0.0000%–10.2564% | median 1.1725%; mean 1.3595%; min–max 0.0000%–4.3860% |
| |Centroid Drift| | median 0.056165; n=944 | median 0.058573; n=944 | median 0.054428; n=944 |

KMeans Baseline có Median ARI cao nhất (`0.768741`). Ward có Median Migration thấp nhất (`1.0582%`), nhưng có ARI thấp hơn. `|Centroid Drift|` được giữ làm evidence bổ sung vì tám feature có đơn vị khác nhau; không dùng giá trị gộp đó để xếp hạng trực tiếp giữa các phương án.

## 5. Sanity check: cụm nhỏ và mất cân bằng

| Phương án | Cụm nhỏ nhất | Snapshot có cụm <5 mã | Ngày bị cảnh báo | Trạng thái |
|---|---:|---:|---|---|
| KMeans Baseline | 1 | 11/60 | 2021-03-31<br>2021-04-29<br>2021-05-31<br>2021-06-30<br>2021-07-30<br>2021-08-31<br>2021-09-30<br>2021-10-29<br>2021-12-31<br>2022-01-28<br>2022-02-28 | WARNING |
| Ward Hierarchical | 1 | 17/60 | 2019-05-31<br>2019-11-29<br>2019-12-31<br>2020-02-28<br>2021-03-31<br>2021-04-29<br>2021-05-31<br>2021-06-30<br>2021-07-30<br>2021-08-31<br>2021-09-30<br>2021-10-29<br>2021-12-31<br>2022-01-28<br>2022-02-28<br>2022-07-29<br>2023-08-31 | WARNING |
| PCA + KMeans | 1 | 11/60 | 2021-03-31<br>2021-04-29<br>2021-05-31<br>2021-06-30<br>2021-07-30<br>2021-08-31<br>2021-09-30<br>2021-10-29<br>2021-12-31<br>2022-01-28<br>2022-02-28 | WARNING |

Cả ba phương án đều có ít nhất một cụm nhỏ hơn 5 mã. Theo chính sách Task 10 V2 đã được phê duyệt, đây là `WARNING` bắt buộc phải công bố, không tự động loại toàn bộ phương án khi hiện tượng xuất hiện ở cả ba. Các ngày cảnh báo được giữ để kiểm toán; không tự gán cụm nhỏ là “cụm rác” nếu chưa có bằng chứng kinh tế bổ sung.

## 6. Decision trace theo năm tầng

| Phương án | Sanity | Có cảnh báo cụm nhỏ | Dẫn đầu chất lượng trước Occam | Được chọn cuối cùng |
|---|---|---:|---:|---:|
| KMeans Baseline | WARNING | Có | Không | Có |
| Ward Hierarchical | WARNING | Có | Không | Không |
| PCA + KMeans | WARNING | Có | Có | Không |

1. **Chất lượng hình học:** PCA + KMeans dẫn đầu Silhouette.
2. **Xác nhận DB:** Ward có DB thấp nhất, nhưng không đảo thứ hạng Silhouette vì đây không phải tình huống tie tuyệt đối.
3. **Sanity:** cả ba mang `WARNING`, do đó không có phương án nào bị loại riêng lẻ ở tầng này.
4. **Temporal stability:** KMeans có ARI cao nhất; Ward có migration thấp nhất. Đây là bằng chứng kiểm tra độ bền, không thay thế tiêu chí Silhouette.
5. **Occam:** PCA + KMeans hơn KMeans Baseline `0.007806` Silhouette và Ward hơn `0.002055`; cả hai đều nhỏ hơn 0.03. Vì không có lợi thế hình học đủ lớn để biện minh cho pipeline phức tạp hơn, chọn KMeans Baseline.

## 7. Quyết định và ba luận điểm bắt buộc

### Luận điểm 1 — Vì sao KMeans Baseline được chọn?

**KMeans Baseline, Global K = 2** được chọn. Chênh lệch Silhouette với phương án dẫn đầu PCA + KMeans là `0.007806`, thấp hơn ngưỡng 0.03 của Occam. KMeans giữ pipeline `Low` complexity, diễn giải trực tiếp trên 8 feature gốc và đạt Median ARI cao nhất. Vì vậy lợi ích hình học của PCA không đủ lớn để bù cho bước giảm chiều bổ sung.

### Luận điểm 2 — Vì sao hai comparator không được chọn?

- **PCA + KMeans:** có Silhouette và CH cao nhất, nhưng cải thiện Silhouette so với KMeans không đáng kể theo rule Occam; pipeline `High` complexity và cần diễn giải ngược từ không gian PCA về feature gốc.
- **Ward Hierarchical:** có DB và Migration tốt nhất, nhưng Silhouette không dẫn đầu, ARI thấp nhất trong ba phương án và có 17 snapshot cảnh báo cụm nhỏ — nhiều hơn KMeans/PCA (11 snapshot). Pipeline `Medium` complexity không có bằng chứng vượt trội đủ mạnh để thắng KMeans.

### Luận điểm 3 — Cam kết đóng băng phương pháp

Quyết định đã được đóng băng tại `M2/artifacts/m2-evaluation-v2/final_method_decision.json` với trạng thái `FROZEN_FOR_HOLDOUT`. Bộ 60 model development đã được kiểm tra SHA-256 và lưu tại `M2/models/final_selected_model_v2/`. Nếu mở Final Holdout V2, chỉ được chạy KMeans Baseline với K = 2; không retune K, scaler, PCA hay thuật toán sau khi nhìn dữ liệu holdout.

## 8. Giới hạn diễn giải và bàn giao

- Cảnh báo cụm nhỏ và balance thấp là giới hạn cấu trúc chung của cả ba phương án, phải tiếp tục xuất hiện trong mọi báo cáo/handoff sau này.
- Không được suy diễn khả năng đầu tư, chi phí giao dịch hoặc hiệu quả danh mục từ kết quả Task 10.
- Quyết định này chỉ freeze phương pháp cho Holdout; không xác nhận `research_ready`, historical identity hoặc quyền sử dụng dữ liệu.
- Artifact bàn giao gồm `methodology_comparison.csv`, `methodology_metric_statistics.csv`, `profile_sanity_check.csv`, `method_selection_trace.csv`, `model_comparison_radar_or_bar.png`, `final_method_decision.json` và thư mục model đã freeze.
