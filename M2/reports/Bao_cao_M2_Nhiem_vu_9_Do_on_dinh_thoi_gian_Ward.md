# Báo cáo M2 — Nhiệm vụ 9: Độ ổn định theo thời gian của Ward

## Phạm vi và nguồn bằng chứng

- Ward Hierarchical, Global K=2, 15 development snapshots tạo 14 cặp liên tiếp.
- Đọc trực tiếp `temporal_stability.csv`, `transition_matrices.csv`, `centroid_drift.csv` trong `M2/artifacts/m2-evaluation-ward/`.
- Không fit lại model, không gọi backend temporal metrics, không mở final holdout, không gọi đây là Dynamic Clustering và không đánh giá lợi nhuận.

## Bảng 1 — Temporal summary

| Chỉ số (Metric) | Số cặp quan sát | Trung bình (Mean) | Trung vị (Median) | Nhỏ nhất (Min) | Lớn nhất (Max) |
| --- | --- | --- | --- | --- | --- |
| ARI | 14 | 0.580252 | 0.537278 | 0.327645 | 0.960785 |
| NMI | 14 | 0.487593 | 0.439157 | 0.276156 | 0.911286 |
| Persistence (%) | 14 | 94.603320 | 96.228371 | 87.815126 | 99.504132 |
| Migration (%) | 14 | 5.396680 | 3.771629 | 0.495868 | 12.184874 |

## Bảng 2 — Transition matrix tích lũy

| Từ Cụm (From) | Sang Cụm (To) | Tổng số lượt (Count) | Tổng số cơ sở (Denominator) | Tỷ lệ xác suất (Rate %) |
| --- | --- | --- | --- | --- |
| 0 | 0 | 166 | 278 | 59.712230 |
| 0 | 1 | 112 | 278 | 40.287770 |
| 1 | 1 | 4435 | 4527 | 97.967749 |
| 1 | 0 | 92 | 4527 | 2.032251 |

## Bảng 3 — Centroid drift theo feature

| Đặc trưng | Độ lệch tuyệt đối Cụm 0 (Mean \|Delta\|) | Độ lệch tuyệt đối Cụm 1 (Mean \|Delta\|) |
| --- | --- | --- |
| liquidity_21 (tỷ VND) | 149.501683 | 5.826965 |
| beta_126 | 0.094747 | 0.067585 |
| vol_63 | 0.026861 | 0.032704 |
| mdd_126 | 0.036305 | 0.015978 |
| mom_21 | 0.056957 | 0.041083 |
| mom_63 | 0.073246 | 0.033462 |
| mom_126 | 0.104734 | 0.036704 |
| mom_252 | 0.128807 | 0.047873 |

## Bảng 4 — Entry/Exit

| Cặp Snapshot (From -> To) | Số mã chung (n_common) | Số mã mới (Entry) | Số mã rớt (Exit) | Tỷ lệ luân chuyển (%) |
| --- | --- | --- | --- | --- |
| 2023-11-30 -> 2023-12-29 | 140 | 55 | 2 | 28.934010 |
| 2023-12-29 -> 2024-01-31 | 191 | 5 | 4 | 4.500000 |
| 2024-01-31 -> 2024-02-29 | 196 | 0 | 0 | 0.000000 |
| 2024-02-29 -> 2024-03-29 | 196 | 1 | 0 | 0.507614 |
| 2024-03-29 -> 2024-04-26 | 197 | 17 | 0 | 7.943925 |
| 2024-04-26 -> 2024-05-31 | 210 | 11 | 4 | 6.666667 |
| 2024-05-31 -> 2024-06-28 | 221 | 19 | 0 | 7.916667 |
| 2024-06-28 -> 2024-07-31 | 238 | 9 | 2 | 4.417671 |
| 2024-07-31 -> 2024-08-30 | 246 | 349 | 1 | 58.724832 |
| 2024-08-30 -> 2024-09-30 | 591 | 15 | 4 | 3.114754 |
| 2024-09-30 -> 2024-10-31 | 605 | 3 | 1 | 0.656814 |
| 2024-10-31 -> 2024-11-29 | 608 | 172 | 0 | 22.051282 |
| 2024-11-29 -> 2024-12-31 | 584 | 5 | 196 | 25.605096 |
| 2024-12-31 -> 2025-01-24 | 582 | 7 | 7 | 2.348993 |

`Universe turnover = (Entry + Exit) / (n_common + Entry + Exit)`. Đây là biến động tập đủ điều kiện, không phải turnover danh mục.

## Các cặp ARI dưới 0,50

| from_date | to_date | ari | nmi | persistence_probability | migration_rate |
| --- | --- | --- | --- | --- | --- |
| 2024-03-29 | 2024-04-26 | 0.407266 | 0.344020 | 0.883249 | 0.116751 |
| 2024-05-31 | 2024-06-28 | 0.432254 | 0.353444 | 0.909502 | 0.090498 |
| 2024-06-28 | 2024-07-31 | 0.327645 | 0.276156 | 0.878151 | 0.121849 |
| 2024-10-31 | 2024-11-29 | 0.397350 | 0.314277 | 0.960526 | 0.039474 |
| 2024-11-29 | 2024-12-31 | 0.478220 | 0.380636 | 0.964041 | 0.035959 |

## Reset gap và bối cảnh thị trường

Chuỗi development liên tục từ 2023-11-30 đến 2025-01-24 và dừng trước gap hệ thống tháng 02/2025. Notebook không tạo liên kết qua gap và không nạp holdout.

- 03/2024→04/2024 trùng tháng VN-Index giảm 5,8% theo [Vietcap](https://www.vietcap.com.vn/trung-tam-phan-tich/bao-cao-thang-4-2024-vn-index-giam-manh-nhat-trong-6-thang).
- 06/2024→07/2024 trùng nhịp VN-Index lùi 4,8% trong hai tuần sau khi tiến gần 1.300 điểm theo [Vietcap](https://www.vietcap.com.vn/en/research-center/market-recap-july-2024-vn-index-trades-sideways-in-july).
- 10/2024→11/2024 trùng nhịp giảm 4,7% đến 19/11 rồi phục hồi 3,8% theo [Vietcap](https://www.vietcap.com.vn/api/cms-api/uploads/file/202412/Monthly-20241203-November2024.pdf).
- 11/2024→12/2024 vẫn có ARI thấp dù VN-Index cuối tháng tăng 1,31% so với cuối tháng 11 theo [SSC](https://ssc.gov.vn/webcenter/portal/ubck/pages_r/l/chitit?dDocName=APPSSCGOVVN1620151252&dID=156472).
- 05/2024→06/2024 chưa có bằng chứng sự kiện riêng đủ mạnh trong các nguồn đã kiểm tra.

Các liên hệ trên là đối chiếu bối cảnh, không chứng minh cú sốc VN-Index gây ra thay đổi cụm.

## Nhận định

- Median ARI = **0.537278**, Median NMI = **0.439157**: phân hoạch chỉ ổn định ở mức trung bình và biến thiên đáng kể.
- Median Persistence = **96.2284%**, Median Migration = **3.7716%**; maximum Migration = **12.1849%**, nên cả 14 cặp đều không vượt ngưỡng 15% của rubric.
- Migration đo tỷ lệ thành viên chung đổi cụm. Nó là proxy/lower bound cho áp lực tái phân loại nếu M3 bám theo cụm, không phải turnover có trọng số hay chi phí giao dịch thực tế.
- Cụm 0 giữ lại **59.71%** thành viên tích lũy, thấp hơn Cụm 1 (**97.97%**). Persistence tổng thể cao chịu ảnh hưởng lớn của Cụm 1 có quy mô lớn.

## Phán quyết ba phần

**A — Độ ổn định:** Ward có persistence cao nhưng Median ARI/NMI ở mức trung bình và 5 cặp ARI dưới 0,50.

**B — Độ bền và turnover:** Migration quan sát được thấp hơn 15% ở mọi cặp, cho thấy áp lực đổi nhãn thấp theo rubric. Chi phí giao dịch vẫn phải kiểm định bằng trọng số và lệnh giao dịch ở M3.

**C — Handoff:** Ward đủ dữ liệu để vào Nhiệm vụ 10, kèm cảnh báo về độ bền của cụm nhỏ và chưa đủ cơ sở chọn final method.
