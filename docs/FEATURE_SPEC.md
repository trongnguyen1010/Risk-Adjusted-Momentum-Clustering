# Feature specification 1.0.0

## Input và thời gian

`build_features(tables, config, data_version)` nhận các bảng canonical đã QC. Tính riêng từng security_id trên các ngày mở của sàn có hiệu lực. Dòng thiếu phiên để null, không nén thành chuỗi quan sát liên tiếp và không forward-fill.

Chỉ xuất ngày calendar có `is_month_end=true`. `as_of_date` là ngày đó; `available_at` là `decision_at` cấu hình trong lịch. Giá đóng cửa chỉ được chấp nhận khi available_at không muộn hơn decision_at của phiên tương ứng, và basis thuộc accepted_adjustments. Policy hiện tại bảo thủ: giá công bố trễ hơn decision_at của phiên đó bị coi thiếu trong cửa sổ dù một snapshot sau đã có thể biết; chưa có bitemporal replay cho dữ liệu đến trễ.

Đây là tính as-of trên **một phiên bản dữ liệu đã đóng băng**, không chứng minh vendor lịch sử là point-in-time. Revision từ nhà cung cấp phải giữ version riêng.

## Công thức

P là adj_close nhất quán về basis. `r_t=P_t/P_(t-1)-1`. Lợi suất ở hai bên gap là null.

| Feature | Công thức | Số quan sát tối thiểu |
|---|---|---|
| mom_21/63/126/252 | P_t/P_(t-L)-1 | L+1 giá liên tiếp theo calendar |
| vol_63/126 | sample_std(r, ddof=1) × sqrt(252) | L returns, tức L+1 giá |
| sharpe_63/126 | sqrt(252) × mean(r-rf_daily) / sample_std(r-rf_daily) | L returns hợp lệ và L rf_daily |
| mdd_126 | min(P_u / running_max(P trong cửa sổ)-1) | 126 giá; **126 quan sát giá**, không phải 126 returns |
| beta_126 | sample_cov(r_stock,r_VNINDEX) / sample_var(r_VNINDEX) | 126 cặp returns cùng phiên |
| liquidity_21 | mean(traded_value) | 21 giá trị giao dịch hợp lệ |

Đơn vị momentum/vol là thập phân, drawdown không dương, Sharpe/beta không đơn vị, liquidity là VND/phiên. Giá tăng 10% xuất 0.1, không phải 10.

rf_daily = `(1 + annual_rate)^(1/252) - 1`. Nếu `rf_annual` được cấu hình thì dùng hằng số đó (demo = 0). Nếu null thì dùng bảng risk_free_rate theo `rf_tenor`, chọn dòng date mới nhất đã khả dụng vào 00:00 giờ Việt Nam của ngày lợi suất; không dùng rf được công bố sau đó. Rate có thể được giữ tới ngày công bố kế tiếp theo convention này.

## Thiếu dữ liệu và eligibility

- Thiếu cửa sổ/gap/giá chưa khả dụng/adjustment chưa chấp nhận: null, có na_reason.
- Volatility bằng 0 hợp lệ; Sharpe có denominator ≤1e-12 là null.
- Phương sai benchmark ≤1e-16: beta null; không đổi benchmark thiếu thành 0.
- Liquidity thiếu traded_value: null, hiện không có proxy ngầm.
- Eligibility: đủ toàn bộ required_features, status normal, metadata đã khả dụng, identity không provisional.
- Giữ lại dòng không eligible để báo coverage; model về sau phải lọc eligibility rõ ràng.
- Lý do NA hiện nhóm các trường hợp kỹ thuật chung; chưa phân loại sâu từng nguyên nhân theo từng ô. Issue dữ liệu nghiêm trọng có rule_id riêng ở QC.

## Test bắt buộc đã có

Giá 100 → 110 → 99 cho returns +10%/-10%, momentum hai phiên -1%, MDD -10%; giá hằng số; thiếu phiên; L+1 quan sát; tách hai mã; beta≈1 khi stock=benchmark; append tương lai không đổi snapshot cũ; dữ liệu công bố trễ không được dùng sớm. Chạy `python -m unittest discover -s tests -v`.

M2 sẽ áp `log1p(liquidity)` trước scale; không sửa liquidity gốc trong feature table. Scaler/PCA phải fit đúng snapshot, không fit toàn bộ lịch sử hoặc holdout.
