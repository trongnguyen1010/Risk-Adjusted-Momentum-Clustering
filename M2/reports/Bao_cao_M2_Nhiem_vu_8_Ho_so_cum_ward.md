# Báo cáo M2 — Nhiệm vụ 8: Hồ sơ cụm Ward

## Phạm vi và nguồn bằng chứng

- Phần Ward của Phương trong nhiệm vụ 8; chưa phải báo cáo tổng hợp cả ba phương án.
- Theo [kế hoạch M2](../Ke_hoach_M2_Phan_cum_co_phieu.md), nhiệm vụ 8.
- Run nguồn: `experiment-20260929T153217Z-31d14d96`, development `2023-11-30` → `2025-01-24`, Global K=2.
- [Manifest Ward](../artifacts/m2-task5-ward-v1/manifest.json), SHA-256 `c69ffb178e966dd77db7430ca02a26390f82be54d3a02adbd04649755fabc3e7`.
- K=2 đã khóa trong [decision nhiệm vụ 3](../../artifacts/experiments/m2-task3-development-v1/global_k_decision.json) và [ADR-049](../../docs/DECISIONS.md).
- Bản báo cáo này chỉ đọc artifact development đã có; không fit model/scaler/PCA, không đọc file feature M1 hoặc final holdout, không backtest.
- Output báo cáo lưu trực tiếp tại `M2/artifacts/m2-evaluation-ward/` theo kế hoạch; artifact nguồn Ward được giữ nguyên.

## 8.1 — Phương pháp tổng hợp hồ sơ

`clustering/base.py` tạo profile bằng **trung bình feature gốc của thành viên trong từng cụm**, cùng size và nhãn.
Có 30 profile = 15 tháng × 2 cụm, trên 5.615 assignment tháng–mã; đây không phải 5.615 mã riêng biệt.
Không trộn thành viên các tháng để tính một centroid chung. Mean khác median và không mô tả được phân phối trong cụm.

Output giữ cả `raw_cluster_id` và `aligned_cluster_id`. Raw ID chỉ có ý nghĩa trong snapshot;
aligned ID là nhãn được nối bằng overlap membership qua các tháng. ID 0/1 không phải thứ hạng hay khuyến nghị đầu tư.

Đơn vị: momentum và MDD là tỷ lệ; `vol_63` là volatility annualized; `beta_126` là beta;
`liquidity_21` là giá trị giao dịch bình quân 21 phiên, VND/phiên theo feature M1.

## 8.2 — So sánh tám feature ở snapshot 2025-01-24

Cụm aligned 0 có **6 mã**, cụm aligned 1 có **583 mã**.

| Feature | Cụm 0 — mean | Cụm 1 — mean |
| --- | --- | --- |
| mom_21 | 0.016696 | -0.004418 |
| mom_63 | 0.059198 | 0.035927 |
| mom_126 | 0.105737 | 0.019098 |
| mom_252 | 0.331001 | 0.150804 |
| vol_63 | 0.220825 | 0.373244 |
| mdd_126 | -0.117614 | -0.196575 |
| beta_126 | 1.329170 | 0.530866 |
| liquidity_21 | 353,985,167,944.841248 | 9,653,002,827.667238 |

Thành viên cụm 0 tại snapshot này: KBS:HOSE:FPT, KBS:HOSE:KBC, KBS:HOSE:MBB, KBS:HOSE:MWG, KBS:HOSE:STB, KBS:HOSE:TCB.

Ở tháng này, mean của cả bốn momentum và liquidity của cụm 0 cao hơn cụm 1; mean volatility thấp hơn,
MDD gần 0 hơn, còn beta cao hơn. Đây là so sánh mô tả tại snapshot, không phải đặc tính vĩnh viễn của một nhãn.
Beta cao hơn không chứng minh nhóm dẫn dắt chỉ số; volatility thấp hơn không chứng minh có dòng tiền tổ chức bảo trợ.

## Quy mô và mean liquidity qua toàn development

| Snapshot | Size cụm 0 | Size cụm 1 | Liquidity cụm 0 — tỷ VND/phiên | Liquidity cụm 1 — tỷ VND/phiên |
| --- | --- | --- | --- | --- |
| 2023-11-30 | 9 | 133 | 201.227713 | 8.895114 |
| 2023-12-29 | 16 | 179 | 332.434746 | 14.506566 |
| 2024-01-31 | 17 | 179 | 295.174249 | 14.266154 |
| 2024-02-29 | 17 | 179 | 359.151771 | 16.682277 |
| 2024-03-29 | 36 | 161 | 275.235007 | 13.797159 |
| 2024-04-26 | 15 | 199 | 459.191122 | 22.633075 |
| 2024-05-31 | 31 | 190 | 280.601066 | 14.085956 |
| 2024-06-28 | 11 | 229 | 576.264143 | 29.329016 |
| 2024-07-31 | 42 | 205 | 194.936897 | 9.567566 |
| 2024-08-30 | 21 | 574 | 288.095511 | 6.731501 |
| 2024-09-30 | 12 | 594 | 423.177525 | 8.686030 |
| 2024-10-31 | 9 | 599 | 499.896620 | 9.235917 |
| 2024-11-29 | 33 | 747 | 214.751630 | 3.562014 |
| 2024-12-31 | 11 | 578 | 357.878668 | 10.118749 |
| 2025-01-24 | 6 | 583 | 353.985168 | 9.653003 |

Notebook hiển thị đủ 30 profile trên tám feature và biểu đồ diễn biến từng feature theo aligned ID.
Biểu đồ mỗi feature có trục riêng theo đơn vị gốc; chỉ đổi đơn vị % hoặc tỷ VND khi hiển thị.
Không fit Global Min-Max, không đổi Robust Scaling của mô hình và không gọi việc đổi đơn vị biểu đồ là xử lý nhiễu.

## 8.3 — Giới hạn diễn giải

- Mean nhạy với quan sát cực đoan. Chưa có bảng median/dispersion hoặc phân phối feature từng cổ phiếu trong artifact profile;
  không suy ra các thống kê đó từ hai centroid.
- Chênh lệch profile không tự chứng minh nguyên nhân kinh tế, dòng tiền tổ chức, đầu cơ, chất lượng doanh nghiệp hay hiệu quả đầu tư.
- Nhãn như “siêu cổ phiếu”, “tinh hoa”, “penny” không được xác lập bởi tám feature này; bản báo cáo dùng tên trung tính “cụm 0/1”.
- MDD gần 0 hơn là drawdown lịch sử nhỏ hơn, không đồng nghĩa an toàn tương lai. Beta và volatility phản ánh hai khía cạnh khác nhau.
- Profile thay đổi theo tháng do cả feature và membership. Cần đọc cùng entry/exit và drift của nhiệm vụ 9.
- Không kết luận cụm nào nên mua; giữ đúng giới hạn nhiệm vụ 8 trong kế hoạch.

## Đầu ra bàn giao

- [Notebook nhiệm vụ 8](../notebooks/08_cluster_profiling.ipynb).
- [Đủ 30 hồ sơ trên tám feature gốc](../artifacts/m2-evaluation-ward/cluster_profiles.csv).
- [Thành viên từng cụm theo tháng](../artifacts/m2-evaluation-ward/cluster_profile_members.csv).
- [Đối chiếu mean với scaler/centroid đã lưu](../artifacts/m2-evaluation-ward/profile_scaler_reference.csv).

## Kiểm chứng và giới hạn

- Notebook đã chạy đủ 5/5 code cells và lưu output thực tế; không có cell lỗi. Bộ kiểm thử helper reporting đạt 8/8 trên fixture tổng hợp, compileall thành công.
- Đối chiếu 30/30 checksum của run nguồn; kiểm tra coverage ngày, assignment duy nhất, size profile/diagnostics và K đã khóa.
- Đối chiếu scaler/centroid đã lưu; ARI/NMI dùng lại module metrics hiện có, cùng kiểm tra membership, transition và drift từ assignments/profiles.
- Đây là xác nhận tính toàn vẹn và tính nhất quán của artifact, chưa phải kiểm chứng độc lập implementation Ward hoặc dữ liệu M1.
- [Manifest báo cáo nhiệm vụ 8](../artifacts/m2-evaluation-ward/task8_manifest.json) ghi input/output hashes và checksum helper.
- Không kết luận hiệu quả đầu tư, không chọn lại K và không chọn final method từ riêng phần Ward.
## 5. Đầu ra Bàn giao
Tất cả các tệp đánh giá chi tiết lưu tại `M2/artifacts/m2-evaluation-ward/`:
- `cluster_profiles.csv`: Đủ 30 hồ sơ (15 tháng x 2 cụm) trên 8 feature gốc.
- `cluster_profile_members.csv`: Trích xuất chi tiết mã cổ phiếu thuộc cụm nào theo từng tháng.
- `profile_scaler_reference.csv`: Đối chiếu raw mean với scaler model.
