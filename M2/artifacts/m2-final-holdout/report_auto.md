# Báo cáo Nhiệm vụ 11 — Final Holdout

## A — Cổng đóng băng và thực thi
KMeans Baseline, sklearn, K=2; seed=42, n_init=10, max_iter=300.
Decision: 2026-10-22T05:57:06+00:00; mở holdout: 2026-10-22T08:49:06.592640+00:00.
Nguồn: `CAFEF_C8_COMPLETE_ONLY_V2`, feature version 1.6.0; source hash
`ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`. Input/config/code được khóa trong manifest.
Chạy 24/24 snapshot; skip 0; 30155 assignments;
23/23 cặp nội bộ holdout. Robust Scaling và fit độc lập mỗi tháng,
ngưỡng universe 100, không quét K hoặc chạy comparator. Nhãn bắt đầu chuỗi mới tại
ranh giới Dev/Holdout; không nối qua skip hoặc khoảng trống tháng.

## B — Development so với Holdout
| Metric | Median Development | Median Holdout | Holdout − Development |
| --- | --- | --- | --- |
| silhouette | 0.940837 | 0.949324 | +0.008487 |
| davies_bouldin | 0.403127 | 0.398445 | -0.004682 |
| calinski_harabasz | 1586.371240 | 3476.393786 | +1890.022546 |
| inertia | 376102.139178 | 1340403.029034 | +964300.889855 |
| cluster_balance | 0.020996 | 0.022626 | +0.001630 |
| ari | 0.757047 | 0.843260 | +0.086213 |
| nmi | 0.602909 | 0.721949 | +0.119040 |
| persistence_probability | 0.990071 | 0.993706 | +0.003635 |
| migration_rate | 0.009929 | 0.006294 | -0.003635 |

Delta Silhouette thực tế: **+0.008487**.
Đọc kết quả cùng Balance, quy mô cụm nhỏ, ARI và biến động universe. Rubric trong
kế hoạch không tự chứng minh không overfit, macro regime shift hay lợi ích đầu tư.

![Quỹ đạo 84 mốc](../artifacts/m2-final-holdout/holdout_vs_dev_trajectory.png)

## C — Hồ sơ và giới hạn
`profile_consistency.csv` so tám feature gốc qua mean hồ sơ tháng, xếp vai trò
Higher/Lower mom_63 riêng từng tháng; không giả định nhãn C0/C1 có cùng ý nghĩa
qua ranh giới. Cụm nhỏ nhất holdout: 22 mã.

| Feature | Higher mom63 Dev mean | Higher mom63 Holdout mean | Lower mom63 Dev mean | Lower mom63 Holdout mean |
| --- | --- | --- | --- | --- |
| mom_21 | 0.033360 | 0.036441 | 0.011473 | 0.011307 |
| mom_63 | 0.132994 | 0.129981 | 0.033595 | 0.034405 |
| mom_126 | 0.217049 | 0.181493 | 0.116751 | 0.109548 |
| mom_252 | 0.337644 | 0.295829 | 0.289758 | 0.243622 |
| vol_63 | 0.435945 | 0.388795 | 0.486207 | 0.399978 |
| mdd_126 | -0.253778 | -0.212148 | -0.271317 | -0.213318 |
| beta_126 | 0.932196 | 0.865110 | 0.674028 | 0.773304 |
| liquidity_21 (tỷ VND/phiên) | 222.428658 | 331.004280 | 131.171153 | 160.007902 |

Các Mean trên là tổng hợp không trọng số qua hồ sơ tháng, không phải median cổ phiếu.
Giữ mô tả trung tính; không mặc định nhóm momentum cao phải có thanh khoản lớn.
Migration chỉ tính mã chung, không phải turnover/chi phí danh mục. Không suy nguyên
nhân VN-Index khi chưa có phân tích chỉ số; không retune từ kết quả holdout.
Đây là monthly independent clustering market-only, không phải Dynamic Clustering.
Lần chạy sau chỉ verify checksum/nạp lại, không refit. Task 12/M3 thực hiện riêng.
