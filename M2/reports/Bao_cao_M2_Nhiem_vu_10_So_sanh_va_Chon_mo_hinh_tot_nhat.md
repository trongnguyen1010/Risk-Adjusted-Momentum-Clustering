# Báo cáo M2 — Nhiệm vụ 10: So sánh và chọn mô hình tốt nhất

## 1. Phạm vi, dữ liệu và rào chắn phương pháp

Báo cáo này tổng hợp **chỉ dữ liệu development** của 60 snapshot từ `2019-01-31` đến `2023-12-29` trên tập dữ liệu chuẩn hóa sạch `cafef-c8-complete-only-v2` (1.522 mã, tổng 45.646 lượt gán). Ba phương án dùng cùng Global K = 2, cùng 8 market features, cùng universe theo từng snapshot. Không nạp Final Holdout, không dùng return, Sharpe, ROI hay bất kỳ chỉ số đầu tư nào để chọn mô hình.

| Hạng mục kiểm định | Kết quả |
|---|---|
| Snapshot development | 60/60 cho từng phương án |
| Cặp tháng liên tiếp | 59/59 cho từng phương án |
| Số cụm mỗi snapshot | 2 |
| Feature gốc | `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21` |
| Feature SHA-256 | `ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e` |
| Manifest SHA-256 | `c5bcd72dfc454671d56f7d3b72e4537a67cb11b0da1a5e2fe61d72ac158b8abd` |
| Holdout | Không được đọc trong Task 10 |

Nguồn bảng: `methodology_comparison.csv`, `methodology_metric_statistics.csv`, `profile_sanity_check.csv`, `method_selection_trace.csv` và `final_method_decision.json` trong `M2/artifacts/m2-evaluation-v2/`.

## 2. Ma trận quyết định chính thức

| Phương án | Median Silhouette ↑ | Median DB ↓ | Median CH ↑ | Median Balance ↑ | Median ARI ↑ | Median Migration ↓ | Pipeline |
|---|---:|---:|---:|---:|---:|---:|---|
| KMeans Baseline | 0.940837 | 0.403127 | 1586.371 | 0.020996 | 0.757047 | 0.9929% | Low |
| Ward Hierarchical | 0.946262 | 0.373575 | 1525.514 | 0.019054 | 0.740645 | 1.0649% | Medium |
| PCA + KMeans | 0.946855 | 0.397056 | 1631.467 | 0.020684 | 0.769164 | 0.9509% | High |

- Silhouette là tiêu chí chính; Davies–Bouldin là chỉ số xác nhận khi cần tie-break.
- ARI/Migration là kiểm tra độ bền theo thời gian; không phải tiêu chí thay thế Silhouette.
- Balance nhỏ (~0.02) cho thấy cấu trúc cụm bất đối xứng (nhóm cổ phiếu trụ thanh khoản cao tách khỏi đại chúng), phản ánh đặc thù cấu trúc dòng tiền thị trường TTCK Việt Nam.

## 3. Bảng chất lượng cụm qua 60 snapshot

| Chỉ số | KMeans Baseline | Ward Hierarchical | PCA + KMeans |
|---|---|---|---|
| Silhouette | median 0.940837; mean 0.941310; min–max 0.886026–0.980371 | median 0.946262; mean 0.940077; min–max 0.872083–0.980371 | median 0.946855; mean 0.946822; min–max 0.903889–0.981342 |
| Davies–Bouldin | median 0.403127; mean 0.397471; min–max 0.203519–0.506836 | median 0.373575; mean 0.372546; min–max 0.018141–0.599072 | median 0.397056; mean 0.392388; min–max 0.203106–0.502464 |
| Calinski–Harabasz | median 1586.371; mean 1729.885; min–max 677.981–3805.766 | median 1525.514; mean 1550.577; min–max 555.580–3004.561 | median 1631.467; mean 1750.124; min–max 679.358–3823.662 |
| Cluster Balance | median 0.020996; mean 0.020708; min–max 0.003252–0.050794 | median 0.019054; mean 0.023793; min–max 0.001473–0.067460 | median 0.020684; mean 0.020535; min–max 0.003252–0.050794 |

PCA + KMeans có Median Silhouette cao nhất (`0.946855`), Ward có Median Davies–Bouldin thấp nhất (`0.373575`), trong khi KMeans Baseline có chất lượng hình học bám rất sát (`0.940837`).

## 4. Bảng ổn định thời gian qua 59 cặp tháng

| Chỉ số | KMeans Baseline | Ward Hierarchical | PCA + KMeans |
|---|---|---|---|
| ARI | median 0.757047; mean 0.727974; min–max 0.257268–1.000000 | median 0.740645; mean 0.634786; min–max 0.058918–0.947165 | median 0.769164; mean 0.731593; min–max 0.257268–1.000000 |
| NMI | median 0.602909; mean 0.606640; min–max 0.205420–1.000000 | median 0.602753; mean 0.561663; min–max 0.102781–0.887829 | median 0.602909; mean 0.609822; min–max 0.205420–1.000000 |
| Persistence Probability | median 99.0071%; mean 98.9790%; min–max 97.1212%–100.0000% | median 98.9351%; mean 98.4067%; min–max 95.0884%–99.8971% | median 99.0491%; mean 98.9970%; min–max 97.1212%–100.0000% |
| Migration Rate | median 0.9929%; mean 1.0210%; min–max 0.0000%–2.8788% | median 1.0649%; mean 1.5933%; min–max 0.1029%–4.9116% | median 0.9509%; mean 1.0030%; min–max 0.0000%–2.8788% |
| |Centroid Drift| | median 0.051148 | median 0.051963 | median 0.050665 |

Cả ba phương án đều đạt độ bám dính rất cao (Persistence > 98.9%, Migration < 1.1%). PCA + KMeans và KMeans Baseline duy trì sự ổn định phân hoạch theo thời gian cao hơn Ward.

## 5. Sanity check: cụm nhỏ và mất cân bằng

| Phương án | Cụm nhỏ nhất | Snapshot có cụm <5 mã | Ngày bị cảnh báo | Trạng thái |
|---|---:|---:|---|---|
| KMeans Baseline | 2 | 2/60 | 2021-05-31<br>2021-10-29 | WARNING |
| Ward Hierarchical | 1 | 7/60 | 2019-05-31<br>2019-11-29<br>2019-12-31<br>2020-02-28<br>2021-05-31<br>2021-11-30<br>2023-08-31 | WARNING |
| PCA + KMeans | 2 | 2/60 | 2021-05-31<br>2021-10-29 | WARNING |

Trên dữ liệu sạch V2, hiện tượng cụm nhỏ (<5 mã) giảm mạnh so với dữ liệu cũ (KMeans và PCA chỉ còn 2 snapshot bị cảnh báo, thay vì 11; Ward còn 7 snapshot, thay vì 17). Cả ba đều mang nhãn WARNING minh bạch theo rubric phương pháp, không có phương án nào bị loại riêng lẻ ở tầng này.

## 6. Decision trace theo năm tầng

| Phương án | Sanity | Có cảnh báo cụm nhỏ | Dẫn đầu chất lượng trước Occam | Được chọn cuối cùng |
|---|---|---:|---:|---:|
| KMeans Baseline | WARNING | Có (2/60) | Không | Có |
| Ward Hierarchical | WARNING | Có (7/60) | Không | Không |
| PCA + KMeans | WARNING | Có (2/60) | Có | Không |

1. **Chất lượng hình học:** PCA + KMeans dẫn đầu Silhouette (`0.946855`).
2. **Xác nhận DB:** Ward có DB thấp nhất (`0.373575`), nhưng không đảo thứ hạng vì không có tie tuyệt đối ở Silhouette.
3. **Sanity:** Cả ba cùng mang nhãn WARNING nên không loại phương án nào.
4. **Temporal stability:** PCA + KMeans và KMeans Baseline dẫn đầu độ ổn định thời gian (Persistence > 99%).
5. **Occam's Razor:** Chênh lệch Silhouette giữa PCA + KMeans và KMeans Baseline là `0.006018` (< 0.03). Lợi thế hình học nhỏ hơn ngưỡng quy định 0.03, không đủ để bù đắp việc tăng độ phức tạp của pipeline (giảm chiều 2 giai đoạn và diễn giải ngược). Do đó, **KMeans Baseline** được chọn.

## 7. Quyết định và ba luận điểm bắt buộc

### Luận điểm 1 — Vì sao KMeans Baseline được chọn?
**KMeans Baseline, Global K = 2** được chọn theo nguyên lý Occam's Razor. Chênh lệch Silhouette so với mô hình dẫn đầu PCA + KMeans chỉ là `0.006018` (thấp hơn nhiều so với ngưỡng 0.03 quy định trong đề cương). KMeans giữ pipeline ở mức `Low` complexity, tính toán trực tiếp trên 8 feature gốc và đạt tính ổn định cao.

### Luận điểm 2 — Vì sao hai comparator không được chọn?
- **PCA + KMeans:** Dẫn đầu Silhouette (`0.946855`) nhưng khoảng cách với KMeans Baseline (`0.006018`) không đạt ngưỡng biện minh cho pipeline `High` complexity và mất mát thông tin khi nén chiều.
- **Ward Hierarchical:** Đạt Silhouette `0.946262`, có DB tốt nhất nhưng ARI thấp hơn (`0.7406`) và có tới 7 snapshot cụm nhỏ (<5 mã) — nhiều hơn đáng kể so với KMeans (2 snapshot). Pipeline `Medium` complexity không có ưu thế rõ ràng.

### Luận điểm 3 — Cam kết đóng băng phương pháp
Quyết định đã được đóng băng tại `M2/artifacts/m2-evaluation-v2/final_method_decision.json` với trạng thái `FROZEN_FOR_HOLDOUT`. Toàn bộ 60 model development đã được kiểm tra SHA-256 và lưu trữ tại `M2/models/final_selected_model_v2/`. Nếu mở Final Holdout V2, chỉ được chạy duy nhất **KMeans Baseline** với Global K = 2; tuyệt đối không retune K, scaler, PCA hay thay đổi thuật toán.
