# Đặc tả đặc trưng 1.1.0

Giữ nguyên công thức/cửa sổ 1.0 bên dưới. Thêm `downside_vol_63` (RMS của lợi suất âm
so với 0, năm hóa bằng sqrt(252)), `ram_63=mom_63/vol_63`, trả `null` nếu độ biến động
bằng 0; số quan sát/khoảng trống trong 253 phiên, `listing_age_days` cho phép `null`
và `adjustment_basis`. Nếu lịch có `available_at` thì lịch phải được biết tại thời
điểm quyết định; thay cơ sở điều chỉnh sẽ đặt lại cửa sổ trượt. Cấu hình
`minimum_listing_age_days`/`maximum_missing_sessions` bổ sung điều kiện hợp lệ. Chế
độ bảng lãi suất thật yêu cầu lãi suất hiệu dụng năm theo 252 phiên giao dịch đã được
chuẩn hóa, không tự coi báo giá ACT/360 hay ACT/365 là tương đương. `methodology.md`
mô tả bước tiền xử lý.

# Công thức nền 1.0.0 được giữ nguyên

## Đầu vào và thời gian

`build_features(tables, config, data_version)` nhận các bảng chuẩn đã qua QC. Tính riêng từng `security_id` trên các ngày mở cửa của sàn có hiệu lực. Dòng thiếu phiên để `null`, không nén thành chuỗi quan sát liên tiếp và không điền xuôi.

Chỉ xuất ngày lịch có `is_month_end=true`. `as_of_date` là ngày đó; `available_at` là `decision_at` cấu hình trong lịch. Giá đóng cửa chỉ được chấp nhận khi `available_at` không muộn hơn `decision_at` của phiên tương ứng và cơ sở điều chỉnh thuộc `accepted_adjustments`. Chính sách hiện tại bảo thủ: giá công bố trễ hơn `decision_at` của phiên đó bị coi là thiếu trong cửa sổ dù một ảnh chụp sau đã có thể biết; chưa phát lại dữ liệu đến trễ theo hai chiều thời gian.

Đây là phép tính tại thời điểm chốt trên **một phiên bản dữ liệu đã đóng băng**, không chứng minh dữ liệu lịch sử của nhà cung cấp là đúng theo từng thời điểm. Bản sửa đổi từ nhà cung cấp phải giữ phiên bản riêng.

## Công thức

P là adj_close nhất quán về basis. `r_t=P_t/P_(t-1)-1`. Lợi suất ở hai bên gap là null.

| Đặc trưng | Công thức | Số quan sát tối thiểu |
|---|---|---|
| mom_21/63/126/252 | P_t/P_(t-L)-1 | L+1 giá liên tiếp theo lịch |
| vol_63/126 | sample_std(r, ddof=1) × sqrt(252) | L lợi suất, tức L+1 mức giá |
| sharpe_63/126 | sqrt(252) × mean(r-rf_daily) / sample_std(r-rf_daily) | L lợi suất hợp lệ và L giá trị `rf_daily` |
| mdd_126 | min(P_u / running_max(P trong cửa sổ)-1) | 126 mức giá; **126 quan sát giá**, không phải 126 lợi suất |
| beta_126 | sample_cov(r_stock,r_VNINDEX) / sample_var(r_VNINDEX) | 126 cặp lợi suất cùng phiên |
| liquidity_21 | mean(traded_value) | 21 giá trị giao dịch hợp lệ |

Đơn vị động lượng/độ biến động là thập phân, mức sụt giảm không dương, Sharpe/beta không có đơn vị, thanh khoản là VND/phiên. Giá tăng 10% cho kết quả 0,1, không phải 10.

rf_daily = `(1 + annual_rate)^(1/252) - 1`. Nếu `rf_annual` được cấu hình thì dùng hằng số đó (demo = 0). Nếu null thì dùng bảng risk_free_rate theo `rf_tenor`, chọn dòng date mới nhất đã khả dụng vào 00:00 giờ Việt Nam của ngày lợi suất; không dùng rf được công bố sau đó. Rate có thể được giữ tới ngày công bố kế tiếp theo convention này.

## Thiếu dữ liệu và eligibility

- Thiếu cửa sổ/khoảng trống/giá chưa khả dụng/cơ sở điều chỉnh chưa chấp nhận: `null`, có `na_reason`.
- Độ biến động bằng 0 là hợp lệ; Sharpe có mẫu số ≤1e-12 thì trả `null`.
- Phương sai chỉ số tham chiếu ≤1e-16: beta là `null`; không đổi chỉ số bị thiếu thành 0.
- Thanh khoản thiếu `traded_value`: `null`, hiện không có đại diện ngầm.
- Điều kiện hợp lệ: đủ toàn bộ `required_features`, trạng thái `normal`, metadata đã khả dụng, định danh không phải `provisional`.
- Giữ lại dòng không đủ điều kiện để báo độ phủ; mô hình về sau phải lọc rõ theo điều kiện hợp lệ.
- Lý do NA hiện nhóm các trường hợp kỹ thuật chung; chưa phân loại sâu từng nguyên nhân theo từng ô. Vấn đề dữ liệu nghiêm trọng có `rule_id` riêng ở QC.

## Kiểm thử bắt buộc đã có

Giá 100 → 110 → 99 cho lợi suất +10%/-10%, động lượng hai phiên -1%, MDD -10%; giá hằng; thiếu phiên; L+1 quan sát; tách hai mã; beta≈1 khi cổ phiếu bằng chỉ số tham chiếu; nối dữ liệu tương lai không đổi ảnh chụp cũ; dữ liệu công bố trễ không được dùng sớm. Chạy `python -m unittest discover -s tests -v`.

M2 sẽ áp `log1p(liquidity)` trước khi co giãn; không sửa thanh khoản gốc trong bảng đặc trưng. Bộ co giãn/PCA phải khớp đúng ảnh chụp, không khớp trên toàn bộ lịch sử hoặc tập kiểm định độc lập.
