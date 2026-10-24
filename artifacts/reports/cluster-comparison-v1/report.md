# Đối chiếu cụm market, financial và kết hợp — 24/10/2026

Đã giữ nguyên A market-only (168 cụm/84 tháng), B financial-only (30 cụm/10 năm)
và thêm C combined reference (21 cụm/7 năm). Có 5,593 quan sát common cohort.
Nhãn A/B/C là ba namespace độc lập; cùng số nhãn không đồng nghĩa cùng ý nghĩa.

## Cấu hình C đã được owner duyệt và thực thi

14 features = 8 market + 6 core ratios. Z-score độc lập từng năm trên cohort chung;
nhân mỗi chiều market với sqrt(0,5/8), financial với sqrt(0,5/6). KMeans k=3,
seed=42, n_init=20, max_iter=300; không clipping/PCA/imputation, không chọn bằng returns.
Trọng số này cân bằng variance đầu vào của hai block, không bảo đảm mỗi block
đóng góp đúng50% vào khoảng cách giữa các cụm sau fit.

| Năm | A native n | B native n | C common n | Kích thước C giảm dần | Silhouette C |
|---|---:|---:|---:|---|---:|
| 2019 | 673 | 1172 | 597 | [532, 62, 3] | 0.3666 |
| 2020 | 523 | 1172 | 464 | [311, 152, 1] | 0.1684 |
| 2021 | 683 | 1172 | 603 | [527, 75, 1] | 0.3554 |
| 2022 | 921 | 1172 | 794 | [437, 356, 1] | 0.1859 |
| 2023 | 1134 | 1172 | 954 | [805, 148, 1] | 0.2829 |
| 2024 | 1258 | 1172 | 1033 | [928, 104, 1] | 0.3730 |
| 2025 | 1410 | 1172 | 1148 | [663, 479, 6] | 0.1657 |

Cả7năm vẫn có cụm dưới10mã: kỹ thuật hội tụ không đồng nghĩa chất lượng đã đạt.
Không so trực tiếp silhouette A/B/C để chọn winner vì feature space, cohort,
tần suất và preprocessing khác nhau. Chưa chạy thêm comparator hoặc đổi k.

## Kết quả review dữ liệu A/B

Market: median phần tách centroid theo metric đã fit của liquidity_21 là99,997%.
Điều này mô tả sự chi phối của feature trong geometry hiện hành, không chứng minh
nguồn liquidity sai. Robust scaling không tự chặn tails.

Financial:180dòng outlier/157vectors tính lại đúng selected inputs từ cache.
56dòng review có liabilities>assets trong selected inputs;27dòng có revenue<1%assets.
Đây là cờ diagnostic, không tự quarantine hoặc sửa số. QBS2025: netprofit
-78.365.108.636 / revenue150.000.000 = net_margin-522,434. CAD2025: liabilities
1.521.403.252.068 / assets11.571.353.867 =131,480. VTI2025:218.704.147.614 /
1.721.287.069 =127,058. Scope/unit/source facts vẫn cần kiểm độc lập với BCTC gốc;
arithmetic replay không thay thế source-fact acceptance. Không tải PDF/OCR mới.

## Các bảng để sử dụng

- `memberships-a-b-c-year-end.csv`: union các mã A/B tại cuối năm; có nhãn C khi đủ cả hai input.
- `cluster-catalog-a-b-c.csv`:219profiles, giữ original-scale means và source path.
- `contingency-a-b-c.csv`: đếm giao các cụm trên common cohort, không ép nhãn tương đương.
- `annual-comparison.csv`: quy mô native A/B và common C, cùng diagnostics của C.
- `combined-separation-drivers.csv`, `combined-small-cluster-members.csv`: queue review C.
- A/B source-input review và prepared14features ở `../dual-cluster-review-v1/`.
- C independent verification và result pointer ở `../combined-reference-v1/`.

## Phạm vi sử dụng

Financial11.720rows hiện không có published_at trong bảng bàn giao. Join same-fiscal-year
với December là EX_POST_REFERENCE, có thể dùng thông tin công bố sau ngày snapshot.
Chỉ phục vụ mô tả; không historical PIT, không historical identity được chứng nhận,
không backtest/M3 và không claim holdout mới. Sáu core ratios không phải bộ
EPS/P/E/P/B/F/M/Z hoàn chỉnh. A/B không refit; C là run mới có pins và manifest.
