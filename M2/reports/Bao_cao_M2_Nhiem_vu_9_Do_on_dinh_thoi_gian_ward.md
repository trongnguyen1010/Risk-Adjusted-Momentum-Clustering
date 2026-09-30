# Báo cáo M2 — Nhiệm vụ 9: Độ ổn định theo thời gian của Ward

## Phạm vi và nguồn bằng chứng

- Phần Ward của Phương trong nhiệm vụ 9; chưa phải báo cáo tổng hợp cả ba phương án.
- Theo [kế hoạch M2](../Ke_hoach_M2_Phan_cum_co_phieu.md), nhiệm vụ 9.
- Run nguồn: `experiment-20260929T153217Z-31d14d96`, development `2023-11-30` → `2025-01-24`, Global K=2.
- [Manifest Ward](../artifacts/m2-task5-ward-v1/manifest.json), SHA-256 `c69ffb178e966dd77db7430ca02a26390f82be54d3a02adbd04649755fabc3e7`.
- K=2 đã khóa trong [decision nhiệm vụ 3](../../artifacts/experiments/m2-task3-development-v1/global_k_decision.json) và [ADR-049](../../docs/DECISIONS.md).
- Bản báo cáo này chỉ đọc artifact development đã có; không fit model/scaler/PCA, không đọc file feature M1 hoặc final holdout, không backtest.
- Output báo cáo lưu trực tiếp tại `M2/artifacts/m2-evaluation-ward/` theo kế hoạch; artifact nguồn Ward được giữ nguyên.

## 9.1–9.4 — Định nghĩa và bảng temporal

15 snapshot liên tiếp tạo **14 cặp tháng**. ARI/NMI tính trên giao tập mã của hai tháng;
ARI không phụ thuộc hoán vị nhãn và có thể âm, NMI dùng chuẩn hóa theo trung bình entropy của hai phân hoạch.
Persistence là tỷ lệ mã chung giữ cụm sau alignment; migration là tỷ lệ đổi cụm và bằng 1 − persistence.
Không đưa các mã mới vào/rời tập đủ điều kiện vào mẫu số migration.

| Từ tháng | Đến tháng | Mã chung | ARI | NMI | Persistence | Migration | Entry | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-11-30 | 2023-12-29 | 140 | 0.575783 | 0.464672 | 0.964286 | 0.035714 | 55 | 2 |
| 2023-12-29 | 2024-01-31 | 191 | 0.960785 | 0.911286 | 0.994764 | 0.005236 | 5 | 4 |
| 2024-01-31 | 2024-02-29 | 196 | 0.924173 | 0.827212 | 0.989796 | 0.010204 | 0 | 0 |
| 2024-02-29 | 2024-03-29 | 196 | 0.517407 | 0.435036 | 0.903061 | 0.096939 | 1 | 0 |
| 2024-03-29 | 2024-04-26 | 197 | 0.407266 | 0.344020 | 0.883249 | 0.116751 | 17 | 0 |
| 2024-04-26 | 2024-05-31 | 210 | 0.543097 | 0.446462 | 0.923810 | 0.076190 | 11 | 4 |
| 2024-05-31 | 2024-06-28 | 221 | 0.432254 | 0.353444 | 0.909502 | 0.090498 | 19 | 0 |
| 2024-06-28 | 2024-07-31 | 238 | 0.327645 | 0.276156 | 0.878151 | 0.121849 | 9 | 2 |
| 2024-07-31 | 2024-08-30 | 246 | 0.531458 | 0.443277 | 0.910569 | 0.089431 | 349 | 1 |
| 2024-08-30 | 2024-09-30 | 591 | 0.602379 | 0.451682 | 0.979695 | 0.020305 | 15 | 4 |
| 2024-09-30 | 2024-10-31 | 605 | 0.850276 | 0.757726 | 0.995041 | 0.004959 | 3 | 1 |
| 2024-10-31 | 2024-11-29 | 608 | 0.397350 | 0.314277 | 0.960526 | 0.039474 | 172 | 0 |
| 2024-11-29 | 2024-12-31 | 584 | 0.478220 | 0.380636 | 0.964041 | 0.035959 | 5 | 196 |
| 2024-12-31 | 2025-01-24 | 582 | 0.575432 | 0.420422 | 0.987973 | 0.012027 | 7 | 7 |

Persistence/migration trong bảng là tỷ lệ 0–1; nhân 100 để đọc theo %.

## Tổng hợp — mỗi cặp tháng trọng số bằng nhau

| Metric | Số quan sát | Mean | Median | Min | Max |
| --- | --- | --- | --- | --- | --- |
| ari | 14 | 0.580252 | 0.537278 | 0.327645 | 0.960785 |
| nmi | 14 | 0.487593 | 0.439157 | 0.276156 | 0.911286 |
| persistence_probability | 14 | 0.946033 | 0.962284 | 0.878151 | 0.995041 |
| migration_rate | 14 | 0.053967 | 0.037716 | 0.004959 | 0.121849 |

Persistence trung bình **94,603320%**, migration **5,396680%**; ARI trung bình **0,580252**,
dao động **0,327645–0,960785**. Bản cũ ghi “trên 95%”, “dưới 5%” và khoảng ARI 0,60–0,80 không khớp cách tổng hợp này.
Trung bình không trọng số theo cặp tháng khác với việc gộp số lần xuất hiện của tất cả mã; báo cáo không trộn hai cách tính.

## 9.5 — Transition matrix và mất cân bằng quy mô

Dùng `transitions.jsonl` của runner, nơi ID đã căn chỉnh xuyên chuỗi. Không gán ID của transitions lồng
trong `stability.jsonl` trực tiếp cho aligned profiles, vì trường lồng đó dùng hệ nhãn raw tháng trước.
Mỗi hàng chuẩn hóa theo số mã thuộc cụm nguồn và tồn tại ở cả hai tháng.

Ví dụ `2024-12-31` → `2025-01-24`:

| Aligned nguồn | Aligned đích | Số mã | Mã chung ở nguồn | Tỷ lệ theo hàng |
| --- | --- | --- | --- | --- |
| 0 | 0 | 5 | 11 | 0.454545 |
| 0 | 1 | 6 | 11 | 0.545455 |
| 1 | 0 | 1 | 571 | 0.001751 |
| 1 | 1 | 570 | 571 | 0.998249 |

Trong cặp cuối, persistence toàn bộ là 98.797251%, nhưng cụm aligned 0
chỉ giữ 5/11 mã chung (45,4545%); cụm aligned 1 giữ 570/571 mã (99,8249%).
Vì cụm lớn chiếm đa số, persistence toàn bộ cao chưa chứng minh cụm nhỏ ổn định.
Transition phản ánh **thành viên đổi nhãn**, không đo giá trị dòng tiền và không xác lập mô hình Markov dự báo.

## 9.6 — Representative / centroid drift

Drift được đọc và đối chiếu theo `mean feature gốc tháng sau − mean feature gốc tháng trước`, sau matching.
Key raw trong `centroid_drift` được ánh xạ qua profile tháng sau sang aligned ID trước khi xuất bảng.
Có **224 dòng** = 14 cặp × 2 cụm × 8 feature, mỗi dòng giữ before/after/delta và đơn vị.
Không cộng các feature khác đơn vị thành một khoảng cách chung; không so tâm đã Robust Scale bằng hai scaler khác tháng.

Drift ở cặp cuối, theo đơn vị gốc (liquidity: VND/phiên):

| Feature | Δ aligned 0 | Δ aligned 1 |
| --- | --- | --- |
| mom_21 | -0.012217 | -0.038160 |
| mom_63 | 0.049411 | -0.001936 |
| mom_126 | 0.044251 | 0.013914 |
| mom_252 | 0.033008 | -0.012590 |
| vol_63 | -0.017820 | 0.003826 |
| mdd_126 | 0.035435 | 0.020396 |
| beta_126 | 0.073727 | -0.014804 |
| liquidity_21 | -3,893,500,217.886047 | -465,745,892.780941 |

Profile mỗi tháng sử dụng toàn bộ thành viên tháng đó, nên drift bao gồm cả tác động đổi membership và thay đổi feature;
không diễn giải như thay đổi của một danh mục cố định.

## 9.7 — Entry / Exit

- Entry/exit là vào/ra tập cổ phiếu đủ điều kiện phân cụm; không tự suy thành niêm yết/hủy niêm yết.
- Output giữ danh sách security ID theo từng cặp; có **889 sự kiện** entry/exit,
  không phải số mã duy nhất, vì một mã có thể vào/ra nhiều lần.
- Cặp cuối: entry = KBS:HNX:HMR, KBS:HOSE:ORS, KBS:HOSE:SFC, KBS:HOSE:SZC, KBS:HOSE:VHC, KBS:HOSE:VSC, KBS:UPCOM:BIG; exit = KBS:HNX:CST, KBS:HOSE:BSR, KBS:HOSE:DC4, KBS:HOSE:PTC, KBS:HOSE:TV2, KBS:HOSE:VCA, KBS:UPCOM:GMC.

## 9.8 — Gap và reset chuỗi

Helper yêu cầu cặp temporal phải là hai tháng lịch liên tiếp và coverage khớp các snapshot thực sự chạy.
Thiếu snapshot không có lý do skip, thiếu cặp hợp lệ hoặc xuất hiện cặp bắc qua gap đều làm kiểm tra thất bại.
Run hiện tại không skip, có đủ 14 cặp. Hai gap 2023-05–10 và 2025-02–2026-01 ở ngoài cửa sổ này;
không nối development sang holdout. Kiểm thử fixture có tháng bị skip kiểm tra reset tại gap,
không dùng dữ liệu holdout thật.

## Đầu ra bàn giao

- [Notebook nhiệm vụ 9](../notebooks/09_temporal_stability.ipynb).
- [Temporal theo cặp](../artifacts/m2-evaluation-ward/temporal_stability.csv), [thống kê tổng hợp](../artifacts/m2-evaluation-ward/temporal_summary.csv).
- [Transition matrices](../artifacts/m2-evaluation-ward/transition_matrices.jsonl), [persistence từng cụm](../artifacts/m2-evaluation-ward/cluster_persistence.csv).
- [Centroid drift đầy đủ](../artifacts/m2-evaluation-ward/centroid_drift.csv), [entry/exit từng mã](../artifacts/m2-evaluation-ward/entry_exit.csv).
- [Kiểm tra các cặp tháng](../artifacts/m2-evaluation-ward/temporal_pair_audit.csv).

## Kết luận có giới hạn

Ward có mức ổn định thay đổi giữa các cặp tháng; persistence toàn bộ cao đi cùng mất cân bằng quy mô cụm.
Không có kiểm định random walk, phân tích dòng tiền hoặc đánh giá lợi nhuận trong nhiệm vụ này.
Chưa đủ cơ sở chọn Ward làm final method hoặc tuyên bố đưa vào đầu tư. Đây vẫn là static clustering
độc lập theo tháng cộng temporal tracking, không phải Dynamic Clustering.

## Kiểm chứng và giới hạn

- Notebook đã chạy đủ 6/6 code cells và lưu output thực tế; không có cell lỗi. Bộ kiểm thử helper reporting đạt 8/8 trên fixture tổng hợp, compileall thành công.
- Đối chiếu 30/30 checksum của run nguồn; kiểm tra coverage ngày, assignment duy nhất, size profile/diagnostics và K đã khóa.
- Đối chiếu scaler/centroid đã lưu; ARI/NMI dùng lại module metrics hiện có, cùng kiểm tra membership, transition và drift từ assignments/profiles.
- Đây là xác nhận tính toàn vẹn và tính nhất quán của artifact, chưa phải kiểm chứng độc lập implementation Ward hoặc dữ liệu M1.
- [Manifest báo cáo nhiệm vụ 9](../artifacts/m2-evaluation-ward/task9_manifest.json) ghi input/output hashes và checksum helper.
- Không kết luận hiệu quả đầu tư, không chọn lại K và không chọn final method từ riêng phần Ward.
