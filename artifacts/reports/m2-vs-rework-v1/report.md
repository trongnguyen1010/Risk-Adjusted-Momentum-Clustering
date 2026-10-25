# So sánh hướng M2 cũ (K=2) và hướng mới (A v4) — 26/10/2026

Hai câu hỏi: (1) chọn mô hình chỉ trên giai đoạn development thì có ra kết quả khác không; (2) trên cùng tập mã,
cùng không gian đặc trưng, mô hình nào phân cụm tốt hơn. Chỉ dùng thước đo cụm, **không dùng lợi suất**.

## 1. Chọn lại mô hình chỉ trên 2019–2023

`python scripts/run_clustering_rework_v2.py --config configs/experiments/clustering_rework_v2_dev.json`
→ `data/experiments/clustering_rework_v2/rework2dev-4b1932af18ada34f/report.md`. Quy tắc giống hệt rework v2
(4 thuật toán × k = 3–8, lọc cụm nhỏ nhất ≥ 5% và độ ổn định ≥ 0,8, xếp hạng 5 thước đo), chỉ khác: kỳ sàng lọc
≤ 2023-12-29, năm tài chính ≤ 2023.

| Nhóm | Chọn trên 2019–2025 (đang phục vụ) | Chọn trên 2019–2023 |
|---|---|---|
| A – lọc nhẹ, 9 đặc trưng (mô hình web) | K-Means k=3 | PCA + K-Means k=3 (hạng 2,40); K-Means k=3 hạng 2,60 — silhouette cùng 0,276, ổn định 0,98 / 0,96 |
| A – lọc nhẹ, 8 đặc trưng | K-Means k=3 | K-Means k=4 |
| B – tài chính (cả hai bộ chỉ số) | không cấu hình nào đạt | không cấu hình nào đạt |
| C – kết hợp, lọc nhẹ | PCA + K-Means k=4 | PCA + K-Means k=4 |

**Kết luận:** với mô hình A đang dùng, **k = 3 giữ nguyên** khi chỉ nhìn development; K-Means và PCA + K-Means gần
như hòa (PCA giữ 80% phương sai nên nhãn gần trùng). C giữ nguyên. Vì vậy có thể ghi: *số cụm và họ thuật toán được
chọn trên development; holdout 2024–2025 không làm thay đổi lựa chọn*. B vẫn chưa đạt ngưỡng ổn định ở cả hai cách.

## 2. So sánh công bằng M2 K=2 và A v4

`python scripts/compare_m2_vs_rework.py` → `data/experiments/m2_vs_rework/cmp-*/` (`monthly.json`, `summary.json`).
84 tháng; mỗi tháng chấm cả hai bộ nhãn trên **cùng tập mã** (thuộc vũ trụ M2 và có giao dịch theo v4, trung vị 417 mã
ở development, 768 ở holdout) trong **hai không gian**: S1 = cách chuẩn hóa của M2 (median/IQR, thanh khoản thô);
S2 = cách của hướng mới (log thanh khoản, cắt đuôi 1–99%, z-score). Tái lập: refit từng quy trình khớp nhãn đang
phục vụ (ARI = 1,00 cho cả hai), nên so sánh dùng đúng mô hình thật.

Trung vị theo tháng (development / holdout):

| Thước đo | M2 K=2 | A v4 k=3 | Ghi chú |
|---|---|---|---|
| Cụm nhỏ nhất (tỷ lệ mã) | 3,7% / 3,7% | 14,0% / 14,4% | M2 có cụm < 5% ở **48/60** tháng dev và 23/24 tháng holdout; A v4 chỉ 2/60 và 0/24 |
| Phần tách cụm do thanh khoản, S1 | 99,9% / 99,9% | 52% / 84% | Trong không gian M2, nhãn M2 gần như chỉ là "thanh khoản rất lớn" |
| Phần tách cụm do thanh khoản, S2 | 63% / 64% | **8% / 8%** | |
| Phần tách do động lượng (4 đặc trưng), S2 | 7% / 8% | **54% / 54%** | |
| Phần tách do rủi ro (biến động, sụt giảm, beta), S2 | 27% / 26% | 39% / 39% | |
| Silhouette S2 (log) | 0,114 / 0,129 | **0,240 / 0,243** | Cùng tập mã, cùng không gian |
| Davies–Bouldin S2 | 1,54 / 1,51 | 1,52 / 1,56 | Ngang nhau |
| Silhouette S1 (thanh khoản thô) | **0,852 / 0,897** | −0,01 / −0,03 | Cao vì vài mã thanh khoản cực lớn tách xa phần còn lại; không phản ánh cấu trúc động lượng/rủi ro |
| Ổn định khi lấy mẫu con 90% | 1,00 / 0,99 | 0,95 / 0,94 | Cả hai đạt ngưỡng 0,8 |
| ARI giữa hai tháng liền nhau | **0,74 / 0,84** | 0,55 / 0,42 | M2 bền theo thời gian hơn vì thanh khoản/quy mô ít đổi |

## 3. Đánh giá

**Hướng mới tốt hơn cho mục tiêu của dự án** (phân nhóm cổ phiếu theo động lượng điều chỉnh rủi ro):

- Cụm cân bằng và dùng được: cụm nhỏ nhất ~14% so với ~4%; M2 vi phạm ngưỡng 5% gần như mọi tháng.
- Cụm được tách bởi động lượng và rủi ro (54% + 39%), không bởi thanh khoản (8%). Nhãn M2 trong chính không gian của
  nó là 99,9% thanh khoản — tức một bộ lọc quy mô, không phải phân cụm động lượng.
- Trên cùng tập mã và không gian log, silhouette cao gấp đôi (0,24 so với 0,11), Davies–Bouldin ngang.
- Lựa chọn k = 3 đứng vững khi chỉ dùng development.

**Điểm M2 cũ hơn, phải ghi trong báo cáo:**

- Nhãn bền theo thời gian hơn (ARI 0,74 so với 0,55). Đó là hệ quả của việc tách theo thanh khoản/quy mô — đặc tính
  ít thay đổi — chứ không phải vì phân cụm tốt hơn; nhưng với M3 nghĩa là danh mục theo A v4 sẽ xoay vòng nhiều hơn.
- Silhouette rất cao trong không gian thanh khoản thô; không dùng con số này để so vì hai bên dùng không gian khác nhau.

**Giới hạn chung:** phân cụm độc lập từng tháng (chưa phải Dynamic Clustering); B chưa đạt ổn định ở cả hai hướng;
ngưỡng lọc thanh khoản là lựa chọn nghiệp vụ đặt từ phân phối 31/12/2025.
