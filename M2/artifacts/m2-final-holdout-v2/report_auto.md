# Báo cáo Nhiệm vụ 11 — Final Holdout V2

## A — Cổng đóng băng và thực thi
KMeans Baseline, sklearn, K=2; seed=42, n_init=10, max_iter=300.
Decision: 2026-10-21T16:42:25+00:00; mở holdout: 2026-10-21T17:31:03.218171+00:00.
Nguồn: `CAFEF_C8_COMPLETE_ONLY_V2`, feature version 1.6.0; source hash
`414ed8102b1b18039eb35aa07615d55353941b641feeea60106fb3d120cac131`. Input/config/code được khóa trong manifest.
Chạy 24/24 snapshot; skip 0; 28110 assignments;
23/23 cặp nội bộ holdout. Robust Scaling và fit độc lập mỗi tháng,
ngưỡng universe 100, không quét K hoặc chạy comparator. Nhãn bắt đầu chuỗi mới tại
ranh giới Dev/Holdout; không nối qua skip hoặc khoảng trống tháng.

## B — Development so với Holdout
| Metric | Median Development | Median Holdout | Holdout − Development |
| --- | --- | --- | --- |
| silhouette | 0.931935 | 0.945927 | +0.013992 |
| davies_bouldin | 0.396416 | 0.399988 | +0.003572 |
| calinski_harabasz | 1122.325007 | 3191.392380 | +2069.067373 |
| inertia | 82143.837336 | 1290877.594618 | +1208733.757282 |
| cluster_balance | 0.023814 | 0.024941 | +0.001128 |
| ari | 0.768741 | 0.849616 | +0.080874 |
| nmi | 0.624996 | 0.723712 | +0.098715 |
| persistence_probability | 0.989313 | 0.993590 | +0.004277 |
| migration_rate | 0.010687 | 0.006410 | -0.004277 |

Delta Silhouette thực tế: **+0.013992**.
Đọc kết quả cùng Balance, quy mô cụm nhỏ, ARI và biến động universe. Rubric trong
kế hoạch không tự chứng minh không overfit, macro regime shift hay lợi ích đầu tư.

![Quỹ đạo 84 mốc](../artifacts/m2-final-holdout-v2/holdout_vs_dev_trajectory.png)

## C — Hồ sơ và giới hạn
`profile_consistency.csv` so tám feature gốc qua mean hồ sơ tháng, xếp vai trò
Higher/Lower mom_63 riêng từng tháng; không giả định nhãn C0/C1 có cùng ý nghĩa
qua ranh giới. Cụm nhỏ nhất holdout: 22 mã.

| Feature | Higher mom63 Dev mean | Higher mom63 Holdout mean | Lower mom63 Dev mean | Lower mom63 Holdout mean |
| --- | --- | --- | --- | --- |
| mom_21 | 0.046239 | 0.036617 | 0.011683 | 0.011783 |
| mom_63 | 0.267779 | 0.131048 | 0.037829 | 0.034560 |
| mom_126 | 0.483932 | 0.182279 | 0.127664 | 0.109478 |
| mom_252 | 0.625512 | 0.295601 | 0.286994 | 0.242701 |
| vol_63 | 0.471170 | 0.390745 | 0.493977 | 0.402170 |
| mdd_126 | -0.270279 | -0.212414 | -0.283261 | -0.213341 |
| beta_126 | 1.085649 | 0.860597 | 0.681168 | 0.769899 |
| liquidity_21 (tỷ VND/phiên) | 169.392821 | 331.659360 | 85.747618 | 160.445105 |

Các Mean trên là tổng hợp không trọng số qua hồ sơ tháng, không phải median cổ phiếu.
Giữ mô tả trung tính; không mặc định nhóm momentum cao phải có thanh khoản lớn.
Migration chỉ tính mã chung, không phải turnover/chi phí danh mục. Không suy nguyên
nhân VN-Index khi chưa có phân tích chỉ số; không retune từ kết quả holdout.
Đây là monthly independent clustering market-only, không phải Dynamic Clustering.
Lần chạy sau chỉ verify checksum/nạp lại, không refit. Task 12/M3 thực hiện riêng.
