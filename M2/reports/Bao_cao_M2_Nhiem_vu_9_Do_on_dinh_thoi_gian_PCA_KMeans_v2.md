# Báo cáo Nhiệm vụ 9 — Độ ổn định thời gian PCA + K-Means với dữ liệu mới V2

<!-- PCA_KMEANS_V2_FULL_REPORT -->

**Ngày biên soạn:** 21/10/2026. **Phạm vi:** 60 snapshot development từ
2019-01-31 đến 2023-12-29; Global K=2; PCA 2 chiều.

Bản báo cáo này phát triển bố cục A/B/C, bảng số liệu và cách biện luận của mẫu
PCA + K-Means cũ trong lịch sử Git, sử dụng hoàn toàn kết quả V2 đã lưu.
**Cập nhật báo cáo và đồng bộ Git:** 22/10/2026. Bản đầy đủ này thay bản
xuất tự động ở đường dẫn báo cáo chính. Bản trước được giữ trong Git history;
checksum báo cáo và tham chiếu manifest được cập nhật, model/số liệu gốc
giữ nguyên. Số liệu trong bảng dùng dấu chấm thập phân; giá trị trình bày
được làm tròn, dữ liệu nguồn giữ độ chính xác gốc.

## A — Phán quyết độ ổn định

### 1. Đầu vào, nhãn và phạm vi so sánh

Nhiệm vụ 9 sử dụng ba CSV đã chuẩn hóa từ artifact Nhiệm vụ 6:

| File | Số dòng × cột dữ liệu | Nội dung |
| --- | --- | --- |
| temporal_stability.csv | 59 × 10 | ARI, NMI, persistence, migration và Entry/Exit |
| transition_matrices.csv | 236 × 6 | Bốn ô chuyển cụm cho mỗi cặp tháng |
| centroid_drift.csv | 944 × 7 | Hai đầu tâm gốc và delta: 59 cặp × 2 cụm × 8 feature |

Chuỗi 60 tháng development liên tục tạo đúng **59 cặp**, từ 2019-01-31 →
2019-02-28 đến 2023-11-30 → 2023-12-29, không có gap hoặc cặp nối qua holdout.
Các phép so sánh nhãn chỉ dùng **cổ phiếu chung** của hai tháng; số mã chung
dao động **114–895**. Thành viên vào/ra được ghi riêng, không ép vào migration.

ARI/NMI đo tương đồng hai phân hoạch và không phụ thuộc tên nhãn. Persistence,
Migration và transitions dùng aligned ID đã nối nhất quán từ Nhiệm vụ 6, tránh
coi việc hoán vị raw label là chuyển cụm. Drift dùng mean feature gốc thật của
cùng aligned ID ở hai tháng, không dùng khoảng cách centroids trong không gian PCA.

### 2. Bảng 1 — Bốn chỉ số ổn định

| Chỉ số (Metric) | Số cặp quan sát | Trung bình (Mean) | Trung vị (Median) | Nhỏ nhất (Min) | Lớn nhất (Max) |
| --- | --- | --- | --- | --- | --- |
| ARI | 59 | 0.747575 | 0.743427 | 0.230167 | 1 |
| NMI | 59 | 0.636082 | 0.592307 | 0.182405 | 1.000000 |
| Persistence (%) | 59 | 98.640468 | 98.827471 | 95.614035 | 100 |
| Migration (%) | 59 | 1.359532 | 1.172529 | 0 | 4.385965 |

Mean/Median ARI là **0.747575/0.743427**, Mean/Median NMI là
**0.636082/0.592307**. Có **38/59 cặp ARI >0.70**, tám cặp ARI bằng 1 và
**năm cặp ARI <0.50**. Theo rubric mô tả, kết quả cho thấy phân hoạch thường
khá bền trên phần universe chung, đồng thời có những cặp biến động đáng kể;
không gọi toàn bộ chuỗi là bất biến.

NMI lớn nhất trong artifact là `1.0000000000000016`, lệch 1 khoảng 1.6×10⁻¹⁵
do số thực máy tính. Bảng làm tròn hiển thị 1; không cắt hoặc sửa dữ liệu nguồn.

### 3. Năm cặp cần lưu ý

| Từ ngày | Đến ngày | Mã chung | ARI | Persistence (%) | Migration (%) |
| --- | --- | --- | --- | --- | --- |
| 2019-12-31 | 2020-01-31 | 597 | 0.450166 | 98.827471 | 1.172529 |
| 2021-10-29 | 2021-11-30 | 145 | 0.230167 | 95.862069 | 4.137931 |
| 2021-11-30 | 2021-12-31 | 114 | 0.408190 | 95.614035 | 4.385965 |
| 2022-05-31 | 2022-06-30 | 267 | 0.482463 | 95.880150 | 4.119850 |
| 2023-05-31 | 2023-06-30 | 843 | 0.485201 | 98.339265 | 1.660735 |

ARI thấp nhất **0.230167** tại 2021-10-29 → 2021-11-30, với 145 mã chung,
Persistence 95.862069% và Migration 4.137931%. Một tỷ lệ giữ nhãn cao vẫn có
thể đi cùng ARI thấp khi cấu trúc hai nhóm rất lệch; cần đọc cả thước đo phân
hoạch lẫn tỷ lệ giữ/chuyển nhãn. Ba CSV không có bằng chứng để quy kết những
suy giảm này cho cú sốc VN-Index, dòng tiền hoặc sự kiện thị trường cụ thể.

### 4. Bảng 2 — Chuyển cụm tích lũy theo lượt

| Từ Cụm (From) | Sang Cụm (To) | Tổng số lượt (Count) | Tổng số cơ sở (Denominator) | Tỷ lệ xác suất (Rate %) |
| --- | --- | --- | --- | --- |
| Cụm 0 | Cụm 0 (Giữ nguyên) | 498 | 670 | 74.3284 |
| Cụm 0 | Cụm 1 (Chuyển cụm) | 172 | 670 | 25.6716 |
| Cụm 1 | Cụm 1 (Giữ nguyên) | 26492 | 26669 | 99.3363 |
| Cụm 1 | Cụm 0 (Chuyển cụm) | 177 | 26669 | 0.6637 |

Ma trận count theo thứ tự C0, C1 là `[[498, 172], [177, 26492]]`. Mỗi rate bằng
count gộp chia tổng số lượt xuất phát từ chính cụm đó: mẫu số C0 là **670**, C1
là **26669**. Đây là tỷ lệ gộp theo lượt cổ phiếu–cặp tháng; một cổ phiếu có thể
được đếm ở nhiều cặp. Không lấy trung bình các rate tháng để thay tỷ lệ gộp này.

### 5. Bảng 3 — Mean |Delta| của tâm cụm trên feature gốc

| Đặc trưng | Độ lệch tuyệt đối Cụm 0 (Mean \|Delta\|) | Độ lệch tuyệt đối Cụm 1 (Mean \|Delta\|) |
| --- | --- | --- |
| liquidity_21 (tỷ VND) | 73.555190 | 1.635837 |
| beta_126 | 0.150382 | 0.037246 |
| vol_63 | 0.076999 | 0.026047 |
| mdd_126 | 0.043221 | 0.014494 |
| mom_21 | 0.111403 | 0.049092 |
| mom_63 | 0.232845 | 0.058394 |
| mom_126 | 0.335038 | 0.059247 |
| mom_252 | 0.396687 | 0.080186 |

Trong cả tám feature, drift trung bình của C0 cao hơn C1 khi so cùng feature.
Ví dụ thanh khoản C0/C1 thay đổi tuyệt đối trung bình **73.555190/1.635837
tỷ VND/phiên**; beta là **0.150382/0.037246**. Điều này cho thấy chân dung nhóm
nhỏ biến thiên mạnh hơn, nhưng drift phản ánh đồng thời thay đổi giá trị feature
và thành phần thành viên, chưa phân tách được hai nguyên nhân.

Không cộng drift thanh khoản, beta, volatility và momentum thành một điểm chung:
đơn vị khác nhau. Đây là drift của mean cụm trên feature gốc; không mô tả đường
đi giá của từng cổ phiếu hoặc sự bền vững của từng trục PCA.

## B — Persistence/Migration và tác động tiềm tàng

### 1. Độ bám nhãn tổng thể và bất đối xứng giữa hai cụm

Median Persistence **98.827471%** và Median Migration **1.172529%** trên giao
universe. Cả 59/59 cặp có Persistence ≥80% theo rubric mô tả. Tuy nhiên ma trận
gộp cho thấy C0 giữ nhãn **74.3284%**, chuyển sang C1 **25.6716%**; C1 giữ nhãn
**99.3363%**, chuyển sang C0 **0.6637%**.

Nhóm lớn chi phối tỷ lệ giữ nhãn tổng thể. Vì thế kết luận “gần 99% giữ nguyên”
một mình sẽ che bớt xáo trộn của nhóm nhỏ. Cảnh báo này phù hợp với mất cân bằng
đã thấy ở Nhiệm vụ 7 và drift lớn hơn của C0; không được suy rằng mỗi thành viên
C0 đều có cùng xác suất thay đổi hoặc cụm có một tập thành viên cố định.

### 2. Bảng 4 — Entry/Exit và thay đổi universe

Quy ước dùng trong bộ V2:

`Tỷ lệ thay đổi universe (%) = 100 × (Entry + Exit) / n_common`.

Mẫu số là số mã chung, nên chỉ số có thể vượt 100%; đó không phải lỗi xác suất.
Entry/Exit phản ánh thay đổi membership/eligibility giữa snapshot, không đủ để
kết luận một mã mới niêm yết hoặc bị hủy niêm yết.

| Cặp Snapshot (From -> To) | Số mã chung (n_common) | Số mã mới (Entry) | Số mã rớt (Exit) | Tỷ lệ luân chuyển (%) |
| --- | --- | --- | --- | --- |
| 2019-01 → 2019-02 | 655 | 1 | 1 | 0.3053 |
| 2019-02 → 2019-03 | 656 | 6 | 0 | 0.9146 |
| 2019-03 → 2019-04 | 660 | 9 | 2 | 1.6667 |
| 2019-04 → 2019-05 | 661 | 19 | 8 | 4.0847 |
| 2019-05 → 2019-06 | 676 | 19 | 4 | 3.4024 |
| 2019-06 → 2019-07 | 693 | 13 | 2 | 2.1645 |
| 2019-07 → 2019-08 | 705 | 56 | 1 | 8.0851 |
| 2019-08 → 2019-09 | 761 | 20 | 0 | 2.6281 |
| 2019-09 → 2019-10 | 746 | 25 | 35 | 8.0429 |
| 2019-10 → 2019-11 | 764 | 9 | 7 | 2.0942 |
| 2019-11 → 2019-12 | 631 | 42 | 142 | 29.1601 |
| 2019-12 → 2020-01 | 597 | 16 | 76 | 15.4104 |
| 2020-01 → 2020-02 | 612 | 19 | 1 | 3.2680 |
| 2020-02 → 2020-03 | 490 | 5 | 141 | 29.7959 |
| 2020-03 → 2020-04 | 451 | 3 | 44 | 10.4213 |
| 2020-04 → 2020-05 | 445 | 8 | 9 | 3.8202 |
| 2020-05 → 2020-06 | 394 | 7 | 59 | 16.7513 |
| 2020-06 → 2020-07 | 394 | 9 | 7 | 4.0609 |
| 2020-07 → 2020-08 | 394 | 9 | 9 | 4.5685 |
| 2020-08 → 2020-09 | 394 | 0 | 9 | 2.2843 |
| 2020-09 → 2020-10 | 378 | 17 | 16 | 8.7302 |
| 2020-10 → 2020-11 | 309 | 6 | 86 | 29.7735 |
| 2020-11 → 2020-12 | 312 | 50 | 3 | 16.9872 |
| 2020-12 → 2021-01 | 360 | 110 | 2 | 31.1111 |
| 2021-01 → 2021-02 | 401 | 0 | 69 | 17.2070 |
| 2021-02 → 2021-03 | 207 | 55 | 194 | 120.2899 |
| 2021-03 → 2021-04 | 235 | 38 | 27 | 27.6596 |
| 2021-04 → 2021-05 | 249 | 1 | 24 | 10.0402 |
| 2021-05 → 2021-06 | 241 | 81 | 9 | 37.3444 |
| 2021-06 → 2021-07 | 309 | 2 | 13 | 4.8544 |
| 2021-07 → 2021-08 | 240 | 1 | 71 | 30 |
| 2021-08 → 2021-09 | 166 | 0 | 75 | 45.1807 |
| 2021-09 → 2021-10 | 143 | 2 | 23 | 17.4825 |
| 2021-10 → 2021-11 | 145 | 28 | 0 | 19.3103 |
| 2021-11 → 2021-12 | 114 | 2 | 59 | 53.5088 |
| 2021-12 → 2022-01 | 116 | 0 | 0 | 0 |
| 2022-01 → 2022-02 | 116 | 40 | 0 | 34.4828 |
| 2022-02 → 2022-03 | 156 | 105 | 0 | 67.3077 |
| 2022-03 → 2022-04 | 215 | 38 | 46 | 39.0698 |
| 2022-04 → 2022-05 | 253 | 14 | 0 | 5.5336 |
| 2022-05 → 2022-06 | 267 | 2 | 0 | 0.7491 |
| 2022-06 → 2022-07 | 234 | 4 | 35 | 16.6667 |
| 2022-07 → 2022-08 | 237 | 27 | 1 | 11.8143 |
| 2022-08 → 2022-09 | 264 | 49 | 0 | 18.5606 |
| 2022-09 → 2022-10 | 303 | 74 | 10 | 27.7228 |
| 2022-10 → 2022-11 | 362 | 4 | 15 | 5.2486 |
| 2022-11 → 2022-12 | 352 | 121 | 14 | 38.3523 |
| 2022-12 → 2023-01 | 471 | 137 | 2 | 29.5117 |
| 2023-01 → 2023-02 | 603 | 2 | 5 | 1.1609 |
| 2023-02 → 2023-03 | 605 | 3 | 0 | 0.4959 |
| 2023-03 → 2023-04 | 600 | 296 | 8 | 50.6667 |
| 2023-04 → 2023-05 | 886 | 5 | 10 | 1.6930 |
| 2023-05 → 2023-06 | 843 | 3 | 48 | 6.0498 |
| 2023-06 → 2023-07 | 841 | 54 | 5 | 7.0155 |
| 2023-07 → 2023-08 | 893 | 6 | 2 | 0.8959 |
| 2023-08 → 2023-09 | 721 | 5 | 178 | 25.3814 |
| 2023-09 → 2023-10 | 724 | 72 | 2 | 10.2210 |
| 2023-10 → 2023-11 | 794 | 103 | 2 | 13.2242 |
| 2023-11 → 2023-12 | 895 | 60 | 2 | 6.9274 |

Median tỷ lệ thay đổi universe là **10.220994%**, cao nhất
**120.289855%** tại 2021-02-26 → 2021-03-31: 207 mã chung, 55 lượt vào và
194 lượt ra. Ngay ở cặp này ARI/NMI và Persistence bằng 1, Migration bằng 0
trên giao universe. Đây là ví dụ trực tiếp cho thấy **ổn định trên mã chung không
đồng nghĩa ổn định toàn bộ danh sách đủ điều kiện**.

Tổng qua 59 cặp có **1912 lượt vào** và **1613 lượt ra**. Đây là số lượt, không
phải số cổ phiếu riêng biệt; một mã có thể vào/ra nhiều lần. Migration chỉ tính
trên mã chung, còn Entry/Exit đo phần nằm ngoài giao; cần tách hai lớp này.

### 3. Hai biểu đồ chuẩn

![ARI, NMI và tỷ lệ giữ/chuyển cụm](../artifacts/m2-evaluation-pca-kmeans-v2/temporal_trends.png)

![Ma trận chuyển cụm gộp](../artifacts/m2-evaluation-pca-kmeans-v2/transition_heatmap.png)

### 4. Hàm ý cho M3

Migration thấp gợi ý ít thay đổi nhãn trên phần universe chung; nó chưa phải
portfolio turnover hoặc chi phí giao dịch thấp. Giao dịch thực còn phụ thuộc
thành viên vào/ra, cụm được dùng, trọng số, thay đổi tỷ trọng trong cùng cụm,
quy mô vốn và quy tắc tái cân bằng. Thuế, phí và slippage cần mô phỏng riêng ở M3.
Không suy khả năng bảo toàn lợi nhuận hoặc sức chứa vốn từ Persistence.

## C — Bàn giao và giới hạn

Nhiệm vụ 9 hoàn tất 59/59 cặp, bốn bảng, hai biểu đồ, CSV đúng schema và manifest
`complete`. Bước chuẩn hóa không fit model, không tính lại ARI/NMI hoặc matching
nhãn; sử dụng kết quả đã lưu, kiểm tra transitions theo assignments aligned và
drift theo hai đầu profile gốc thật.

Bàn giao Task 10 cần giữ cảnh báo **năm cặp ARI <0.50**, tỷ lệ chuyển gộp của
C0 **25.6716%**, cùng mức thay đổi universe. Các phương án đối chứng phải cùng
60 tháng, nguồn, universe và định nghĩa metric. Đặc biệt thống nhất mẫu số
Entry/Exit/n_common trước khi so tỷ lệ membership với notebook legacy.

Báo cáo Nhiệm vụ 9 không tự xếp hạng PCA so với KMeans/Ward. Task 10 V2
đã đối chiếu và chọn **KMeans_Baseline, K=2**, PCA là comparator; xem
[quyết định Task 10](../artifacts/m2-evaluation-v2/final_method_decision.json).
Việc thay báo cáo không sửa lựa chọn hoặc mở holdout V2. Đây là **Temporal Stability Diagnostic** của các mô hình phân cụm độc lập
từng tháng, không phải Dynamic Clustering. Không dùng return/Sharpe/backtest
hoặc dữ liệu holdout để kết luận trong báo cáo này.

## Nguồn và khả năng kiểm chứng

- [Kế hoạch M2](../Ke_hoach_M2_Phan_cum_co_phieu.md), phần Nhiệm vụ 9.
- [Notebook thực thi](../notebooks/09_temporal_stability_pca_kmeans_v2.ipynb).
- [Temporal stability](../artifacts/m2-evaluation-pca-kmeans-v2/temporal_stability.csv).
- [Transition matrices](../artifacts/m2-evaluation-pca-kmeans-v2/transition_matrices.csv).
- [Centroid drift](../artifacts/m2-evaluation-pca-kmeans-v2/centroid_drift.csv).
- [Bằng chứng bốn bảng](../artifacts/m2-evaluation-pca-kmeans-v2/task9_temporal_evidence.json).
- [Manifest Nhiệm vụ 9](../artifacts/m2-evaluation-pca-kmeans-v2/task9_manifest.json).
- [Mẫu báo cáo cũ trong notebook ở commit a436eb8](https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/a436eb83214c18219da4a990851b8121df0a3e94/M2/notebooks/09_temporal_stability_pca_kmeans.ipynb).

Trước khi biên soạn đã đối chiếu checksum các đầu ra được manifest Nhiệm vụ
6–9 tham chiếu, cấu hình, số dòng và phạm vi ngày. Quá trình viết báo cáo chỉ
đọc kết quả đã lưu; không huấn luyện lại, không sửa model/scaler/PCA và không
truy cập dữ liệu holdout 2024–2025.
