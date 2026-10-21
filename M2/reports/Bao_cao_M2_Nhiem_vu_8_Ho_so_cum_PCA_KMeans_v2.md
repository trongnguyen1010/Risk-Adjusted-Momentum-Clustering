# Báo cáo Nhiệm vụ 8 — Hồ sơ kinh tế của cụm PCA + K-Means với dữ liệu mới V2

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

## A — Chân dung kinh tế

### 1. Đầu vào và nguyên tắc diễn giải

Nguồn chính là 120 profile/60 tháng trong `cluster_profiles.csv`, schema 13 cột:
ngày snapshot, raw ID, aligned ID, size, size ratio và tám feature gốc. Mean của
cụm được tính từ thành viên thực tế trên feature gốc, không thay bằng centroids
PCA hoặc inverse transform bị mất chiều. Báo cáo dùng **aligned ID** để nối
nhất quán Cụm 0/Cụm 1 qua thời gian; raw ID có thể khác giữa các tháng.

Mean/Median ở Bảng 1 là thống kê không trọng số qua **60 hồ sơ tháng của mỗi cụm**.
Đó không phải median của toàn bộ cổ phiếu gộp lại, cũng không phải thống kê được
gia quyền theo số mã hay vốn hóa. Mỗi tháng có trọng số như nhau trong bảng.

Thanh khoản `liquidity_21` được đổi VND/phiên sang **tỷ VND/phiên** chỉ khi trình
bày. Các momentum giữ đơn vị tỷ lệ, ví dụ 0.240630 tương đương 24.0630%.
`vol_63` là độ lệch chuẩn lợi suất ngày 63 phiên đã annualize bằng sqrt(252);
MDD giữ dấu âm, giá trị âm hơn thể hiện drawdown sâu hơn.

### 2. Bảng 1 — Mean/Median qua 60 tháng

| Cụm / thống kê | Size (mã) | Liquidity (tỷ VND/phiên) | Beta 126 | Vol 63 | MDD 126 | Mom 21 | Mom 63 | Mom 126 | Mom 252 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cụm 0 (Mean) | 12.116667 | 249.983935 | 1.377735 | 0.455133 | -0.281996 | 0.038937 | 0.240630 | 0.478703 | 0.656330 |
| Cụm 0 (Median) | 12 | 211.375599 | 1.401596 | 0.446606 | -0.264809 | 0.028224 | 0.082456 | 0.098634 | 0.110857 |
| Cụm 1 (Mean) | 486.333333 | 5.019220 | 0.386404 | 0.509499 | -0.271313 | 0.017761 | 0.061301 | 0.130076 | 0.253186 |
| Cụm 1 (Median) | 439 | 3.985669 | 0.376399 | 0.511969 | -0.250859 | 0.013843 | 0.047075 | 0.083046 | 0.118693 |

Cụm 0 là nhóm nhỏ: size mean **12.1167** mã, median 12 mã, dao động 1–32 mã;
thanh khoản mean **249.983935**, median **211.375599 tỷ VND/phiên**. Cụm 1 có
size mean **486.3333**, median 439 mã, dao động 114–931 mã; thanh khoản mean
**5.019220**, median **3.985669 tỷ VND/phiên**.

Beta mean C0/C1 là **1.377735/0.386404**, nhưng vol annualized mean C0/C1 lại
**0.455133/0.509499**. MDD mean tương ứng **−0.281996/−0.271313**. Cụm 0 có
beta cao hơn và MDD trung bình sâu hơn, trong khi volatility trung bình thấp hơn;
không gộp ba thước đo thành nhận định rằng mọi mặt rủi ro của một cụm đều cao hơn.

### 3. Bảng 2 — Chênh lệch mean Cụm 0 trừ Cụm 1

| Đặc trưng | Cụm 0 — Mean | Cụm 1 — Mean | Chênh lệch C0−C1 |
| --- | --- | --- | --- |
| size | 12.116667 | 486.333333 | -474.216667 |
| liquidity_21_ty_vnd | 249.983935 | 5.019220 | 244.964715 |
| beta_126 | 1.377735 | 0.386404 | 0.991332 |
| vol_63 | 0.455133 | 0.509499 | -0.054366 |
| mdd_126 | -0.281996 | -0.271313 | -0.010682 |
| mom_21 | 0.038937 | 0.017761 | 0.021176 |
| mom_63 | 0.240630 | 0.061301 | 0.179329 |
| mom_126 | 0.478703 | 0.130076 | 0.348627 |
| mom_252 | 0.656330 | 0.253186 | 0.403145 |

Thanh khoản chênh **244.964715 tỷ VND/phiên** là khác biệt kinh tế lớn. C0 có
mean momentum cao hơn ở cả bốn kỳ hạn. Tuy nhiên mean `mom_252` C0/C1 là
0.656330/0.253186, trong khi median là **0.110857/0.118693**, đảo thứ tự giữa
hai cụm. Điều này cho thấy mean chịu ảnh hưởng các tháng có giá trị cao; không
được dùng mean để mô tả mọi tháng hoặc mọi cổ phiếu của cụm.

Giữ tên trung tính: **Cụm 0 — nhóm nhỏ có thanh khoản bình quân cao hơn** và
**Cụm 1 — nhóm đông có thanh khoản bình quân thấp hơn tương đối**. Không gán
nhãn “dẫn dắt”, “bị lãng quên” hoặc “an toàn” chỉ từ các trung bình này.

## B — Động lực phân tách chính và tính nhất quán

### 1. Chuẩn hóa hồ sơ bằng scaler đúng tháng

Với feature f và tháng t, Robust Z của mean cụm được tính:

`Z(c,t,f) = (mean_feature(c,t,f) − saved_market_median(t,f)) / saved_market_IQR(t,f)`.

Median/IQR được đọc từ model đã fit trên universe của chính tháng đó. Không fit
scaler trên 120 hồ sơ cụm, không fit chung 60 tháng. Vì mean cụm không phải
median cụm, Z của mean có thể rất lớn dù median thị trường bằng 0 sau chuẩn hóa.

### 2. Primary Driver theo chênh lệch chuẩn hóa

| Feature | Mean Z C0 | Mean Z C1 | Delta Z C0−C1 |
| --- | --- | --- | --- |
| liquidity_21 | 244.562158 | 3.674704 | 240.887454 |
| beta_126 | 1.544584 | 0.121445 | 1.423140 |
| mom_126 | 0.939383 | 0.215348 | 0.724035 |
| mom_63 | 0.863373 | 0.189404 | 0.673969 |
| mom_252 | 0.635242 | 0.244107 | 0.391135 |
| mom_21 | 0.323650 | 0.139262 | 0.184388 |
| vol_63 | -0.042093 | 0.090247 | -0.132340 |
| mdd_126 | -0.091906 | -0.072072 | -0.019834 |

`liquidity_21` có |Delta Mean Z| lớn nhất: **240.887454**, với Mean Z C0/C1
**244.562158/3.674704**. Feature này cũng đứng đầu độ lớn chênh lệch chuẩn hóa
ở **60/60 tháng**. Bằng chứng loading PC1 của Nhiệm vụ 6 phù hợp với mô tả này.
“Primary Driver” ở đây là đặc trưng phân biệt nổi bật của hồ sơ đã quan sát,
không phải bằng chứng dòng tiền ròng hoặc tác động nhân quả.

Z thanh khoản của mean **cả hai cụm đều dương ở 60/60 tháng**. Vì vậy thanh khoản
C1 thấp hơn C0 không có nghĩa mean thanh khoản C1 thấp hơn median thị trường.
Đồng thời, nhận định về mean cụm không áp dụng cho từng mã trong cụm đó.

### 3. Nhất quán qua thời gian

C0 có thanh khoản cao hơn C1 ở 60/60 tháng. Số tháng C0 có momentum cao hơn C1:

| Feature | Số tháng C0 > C1 | Tỷ lệ trên 60 tháng |
| --- | --- | --- |
| mom_21 | 33 | 55.00% |
| mom_63 | 41 | 68.33% |
| mom_126 | 38 | 63.33% |
| mom_252 | 33 | 55.00% |

Thanh khoản phân biệt nhất quán hơn thứ tự momentum. Vì vậy không diễn giải C0
là nhóm luôn dẫn dắt giá hoặc luôn có động lượng tốt hơn. Nhất quán về hồ sơ
khác với việc giữ nguyên thành viên; nội dung sau được kiểm tra ở Nhiệm vụ 9.

### 4. Bảng 3 — Quy mô và thanh khoản từng snapshot

| Snapshot | Size Cụm 0 | Size Cụm 1 | Liquidity Cụm 0 (tỷ VND) | Liquidity Cụm 1 (tỷ VND) |
| --- | --- | --- | --- | --- |
| 2019-01-31 | 12 | 644 | 87.9333 | 1.6633 |
| 2019-02-28 | 15 | 641 | 106.7544 | 2.0799 |
| 2019-03-29 | 32 | 630 | 74.3385 | 1.7347 |
| 2019-04-26 | 17 | 652 | 76.1523 | 2.0044 |
| 2019-05-31 | 15 | 665 | 88.9821 | 1.9839 |
| 2019-06-28 | 15 | 680 | 78.8361 | 1.6793 |
| 2019-07-31 | 19 | 687 | 76.4571 | 1.6189 |
| 2019-08-30 | 18 | 743 | 79.4675 | 1.7693 |
| 2019-09-30 | 24 | 757 | 58.2802 | 1.4375 |
| 2019-10-31 | 25 | 746 | 56.2292 | 1.3437 |
| 2019-11-29 | 11 | 762 | 102.9090 | 1.8720 |
| 2019-12-31 | 7 | 666 | 111.1440 | 1.8308 |
| 2020-01-31 | 6 | 607 | 128.0645 | 1.9872 |
| 2020-02-28 | 8 | 623 | 145.8215 | 2.0593 |
| 2020-03-31 | 7 | 488 | 163.5798 | 2.5762 |
| 2020-04-29 | 15 | 439 | 87.2454 | 2.1234 |
| 2020-05-29 | 14 | 439 | 113.9286 | 2.9865 |
| 2020-06-30 | 26 | 375 | 82.2978 | 2.5521 |
| 2020-07-31 | 16 | 387 | 78.9356 | 2.7032 |
| 2020-08-31 | 23 | 380 | 78.5602 | 2.4472 |
| 2020-09-30 | 13 | 381 | 136.8871 | 4.4974 |
| 2020-10-30 | 9 | 386 | 270.2212 | 5.8463 |
| 2020-11-30 | 16 | 299 | 152.8349 | 4.4797 |
| 2020-12-31 | 21 | 341 | 191.0924 | 6.9893 |
| 2021-01-29 | 23 | 447 | 258.4950 | 7.9129 |
| 2021-02-26 | 20 | 381 | 251.7186 | 7.5124 |
| 2021-03-31 | 3 | 259 | 218.2952 | 1.8739 |
| 2021-04-29 | 3 | 270 | 220.6214 | 2.5351 |
| 2021-05-31 | 3 | 247 | 203.2782 | 1.6378 |
| 2021-06-30 | 3 | 319 | 396.9151 | 3.3158 |
| 2021-07-30 | 4 | 307 | 220.4655 | 1.8851 |
| 2021-08-31 | 3 | 238 | 309.8432 | 4.0846 |
| 2021-09-30 | 3 | 163 | 282.5735 | 5.4070 |
| 2021-10-29 | 1 | 144 | 323.4210 | 5.6159 |
| 2021-11-30 | 7 | 166 | 181.3142 | 4.1239 |
| 2021-12-31 | 2 | 114 | 389.7296 | 8.5712 |
| 2022-01-28 | 1 | 115 | 517.1426 | 8.9414 |
| 2022-02-28 | 1 | 155 | 427.1304 | 4.7126 |
| 2022-03-31 | 10 | 251 | 537.1740 | 21.1277 |
| 2022-04-29 | 7 | 246 | 590.6734 | 19.1773 |
| 2022-05-31 | 6 | 261 | 463.3797 | 13.9143 |
| 2022-06-30 | 17 | 252 | 244.5886 | 7.4075 |
| 2022-07-29 | 14 | 224 | 204.4560 | 7.1877 |
| 2022-08-31 | 13 | 251 | 314.6587 | 11.9161 |
| 2022-09-30 | 12 | 301 | 276.7757 | 9.8723 |
| 2022-10-31 | 14 | 363 | 287.8079 | 7.3284 |
| 2022-11-30 | 12 | 354 | 272.2993 | 6.8612 |
| 2022-12-30 | 9 | 464 | 360.6020 | 6.7403 |
| 2023-01-31 | 21 | 587 | 172.3536 | 2.5342 |
| 2023-02-28 | 15 | 590 | 201.0367 | 3.4368 |
| 2023-03-31 | 15 | 593 | 196.8088 | 2.8225 |
| 2023-04-28 | 8 | 888 | 289.1438 | 3.8868 |
| 2023-05-31 | 23 | 868 | 187.0260 | 2.8221 |
| 2023-06-30 | 7 | 839 | 465.5382 | 6.3648 |
| 2023-07-31 | 6 | 889 | 506.6537 | 6.7877 |
| 2023-08-31 | 8 | 891 | 642.8754 | 6.8811 |
| 2023-09-29 | 6 | 720 | 769.4840 | 8.0761 |
| 2023-10-31 | 11 | 785 | 368.5299 | 4.6535 |
| 2023-11-30 | 8 | 889 | 465.1167 | 5.5669 |
| 2023-12-29 | 24 | 931 | 354.1577 | 5.3928 |

### 5. Radar và Heatmap tại 2023-12-29

Hai hình lưu mặc định cho tháng cuối development; notebook có dropdown để xem
60 tháng. Radar giới hạn **hiển thị** ở ±3, đánh dấu các điểm ngoài biên; Heatmap
giữ annotation Z thật. Đây không phải clipping feature khi huấn luyện.

![Radar hồ sơ tại 2023-12-29](../artifacts/m2-evaluation-pca-kmeans-v2/radar_chart.png)

![Heatmap hồ sơ tại 2023-12-29](../artifacts/m2-evaluation-pca-kmeans-v2/heatmap.png)

Tại tháng này, Z thanh khoản thật C0/C1 là **382.583514/5.791490**; cả hai vượt
biên Radar. Chỉ nhìn độ dài hai trục đã giới hạn có thể bỏ sót chênh lệch lớn.
Không lấy 04/2024 hoặc 07/2024 làm ví dụ như mẫu cũ: hai thời điểm này thuộc
holdout của protocol V2 và nằm ngoài phạm vi hồ sơ đang báo cáo.

## C — Tính khả thi cho M3 và giới hạn

Nhiệm vụ 8 hoàn tất ba bảng chuẩn, bằng chứng Robust Z, bảng Primary Driver,
Radar, Heatmap và widget snapshot; `task8_manifest.json` ghi `complete` với
60 snapshot, 120 profile và không fit lại. Kết quả cung cấp mô tả kinh tế nhất
quán với cấu trúc bất đối xứng đã thấy ở Nhiệm vụ 7.

Thanh khoản là dữ liệu đầu vào để M3 thiết kế giả định thực thi. Mean thanh
khoản của một cụm chưa chứng minh đủ sức chứa vốn hoặc slippage thấp: còn cần
vốn, trọng số từng mã, thanh khoản từng thành viên, tỷ lệ tham gia giao dịch,
quy tắc tái cân bằng và mô hình chi phí. Cụm nhỏ hoặc các mean lệch cần được
đọc cùng phân phối chi tiết; không suy khả năng giao dịch của từng mã từ mean cụm.

Không khuyến nghị lựa chọn cổ phiếu hay gắn nhãn đầu tư. Task 10 V2 đã hoàn tất và chọn
**KMeans_Baseline, K=2**, còn PCA + K-Means là comparator; xem
[quyết định đã freeze](../artifacts/m2-evaluation-v2/final_method_decision.json).
Kết quả đó không phải backtest/holdout để kết luận hiệu quả đầu tư. [Nhiệm vụ 9](Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_PCA_KMeans_v2.md) bổ sung bằng chứng về giữ/chuyển cụm
và biến động universe; hai nhóm kết quả cần được đọc cùng nhau.

## Nguồn và khả năng kiểm chứng

- [Kế hoạch M2](../Ke_hoach_M2_Phan_cum_co_phieu.md), phần Nhiệm vụ 8.
- [Notebook thực thi](../notebooks/08_cluster_profiling_pca_kmeans_v2.ipynb).
- [Hồ sơ gốc 120 dòng](../artifacts/m2-task6-pca-kmeans-v2/cluster_profiles.csv).
- [Model và scaler theo tháng](../models/pca_kmeans/).
- [Bằng chứng bảng và Robust Z](../artifacts/m2-evaluation-pca-kmeans-v2/task8_profile_evidence.json).
- [Manifest Nhiệm vụ 8](../artifacts/m2-evaluation-pca-kmeans-v2/task8_manifest.json).
- [Mẫu báo cáo cũ trong notebook ở commit a436eb8](https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/a436eb83214c18219da4a990851b8121df0a3e94/M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb).

Trước khi biên soạn đã đối chiếu checksum các đầu ra được manifest Nhiệm vụ
6–9 tham chiếu, cấu hình, số dòng và phạm vi ngày. Quá trình viết báo cáo chỉ
đọc kết quả đã lưu; không huấn luyện lại, không sửa model/scaler/PCA và không
truy cập dữ liệu holdout 2024–2025.
