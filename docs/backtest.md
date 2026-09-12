# Phạm vi và chỉ tiêu mô phỏng quá khứ

Chương trình sử dụng **không gian lợi suất với tỷ trọng phân số**, không hạch toán
theo số cổ phiếu gốc. Các đơn vị đầu tư đã điều chỉnh biểu diễn giá trị danh mục.
Không trường nào được xem là giá khớp gốc hoặc số cổ phiếu thực tế. Các hợp đồng
`trades`/`nav` hiện có vẫn dành cho chương trình hạch toán dữ liệu gốc có lô giao dịch,
thanh toán và sự kiện doanh nghiệp. Đầu ra hiện tại gồm `backtests/*.jsonl` và các báo
cáo khớp lệnh.

Tín hiệu dùng các cụm đủ điều kiện; các phương án đối chứng toàn thị trường tỷ trọng
bằng nhau, chỉ dùng động lượng và chỉ dùng rủi ro có cùng điều kiện hợp lệ và thời điểm.
Hỗ trợ tỷ trọng bằng nhau, nghịch đảo độ biến động và cân bằng rủi ro đường chéo.
Cân bằng rủi ro đường chéo là phép xấp xỉ nghịch đảo độ biến động với hiệp phương sai
chéo bằng 0, không phải bộ giải cân bằng rủi ro dùng toàn bộ ma trận hiệp phương sai.

Lệnh được khớp tại giá đóng cửa của phiên đầu tiên sau cả ngày phát tín hiệu và thời
điểm tín hiệu khả dụng. Lần khớp đầu tiên là mốc bắt đầu cho khoản đầu tư và chỉ số
tham chiếu; chiến lược không nhận lợi suất sớm hơn trong cùng ngày. Chi phí ban đầu
phát sinh tại mốc này; lợi suất chỉ số tham chiếu tại mốc là 0. Tín hiệu cuối cùng
không có phiên sau đó sẽ giữ trạng thái chờ. Tỷ trọng nắm giữ tự trôi trước khi tái
cân bằng; tiền mặt được quy ước sinh lợi 0. Mã đang nắm giữ hoặc được nhắm tới phải có
giá định giá hợp lệ, giá đóng cửa đồng bộ giữa các sàn và trạng thái giao dịch bình
thường tại thời điểm tái cân bằng. Giá bị thiếu, đình chỉ hoặc hủy niêm yết sẽ chặn mô
phỏng; không giả định thanh lý hay thu hồi. Mục tiêu vi phạm số lượng nắm giữ tối thiểu
sẽ bị từ chối.

Áp dụng `rate=(cost_bps+slippage_bps)/10000` lên toàn bộ giá trị giao dịch ở cả hai
chiều. Giải `cost = rate * sum(abs(target_weight*(NAV-cost)-old_value))` bằng phương
pháp chia đôi. Tiền mặt không âm và hạch toán tự cân đối nguồn vốn. Vòng quay là toàn
bộ giá trị danh nghĩa L1/NAV, không phải một nửa L1. NAV gộp là một sổ không tính chi
phí, được tái cân bằng riêng theo cùng mục tiêu.

`split_adjusted` tạo lợi suất giá không bao gồm cổ tức tiền mặt; `total_return` đã xác
minh dùng trực tiếp mức lợi suất toàn phần được cung cấp và không cộng lại cổ tức. Dữ
liệu chỉ có giá chưa điều chỉnh hoặc chưa rõ cơ sở sẽ bị chặn. Sự kiện doanh nghiệp
được nhập và kiểm soát chất lượng, nhưng chưa được áp dụng như một sổ tiền mặt, thanh
toán và quyền lợi gốc. Đầu ra giả lập luôn được gắn nhãn rõ ràng.

Các chỉ tiêu dùng 252 phiên/năm, lợi suất đơn hằng ngày và
`rf=(1+rf_annual)^(1/252)-1`:

| Chỉ tiêu | Định nghĩa / đơn vị |
|---|---|
| Lợi suất tích lũy | product(1+r)-1; dạng thập phân |
| Lợi suất năm hóa | NAV^(252/n)-1; dạng thập phân/năm |
| Độ biến động | sample std(r)*sqrt(252) |
| Sharpe | mean(r-rf)/sample std(r-rf)*sqrt(252) |
| Sortino | mean(r-rf)/sqrt(mean(min(r-rf,0)^2))*sqrt(252) |
| Mức sụt giảm tối đa | min(NAV/đỉnh lũy kế-1), bao gồm NAV ban đầu bằng 1 |
| Calmar | lợi suất năm hóa/giá trị tuyệt đối của MDD |
| Tỷ lệ phiên tăng | Tỷ lệ lợi suất ngày lớn hơn 0 |
| Vòng quay | Tổng toàn bộ giá trị giao dịch/NAV trước giao dịch; đồng thời được năm hóa |
| Beta | sample cov(strategy,benchmark)/sample var(benchmark) |
| Alpha | 252*(mean(strategy excess)-beta*mean(benchmark excess)), CAPM số học |
| Tỷ số thông tin | mean(active)/sample std(active)*sqrt(252) |

Tỷ số không xác định được ghi là `null`. Các phép so sánh dùng chung ngày bắt đầu,
ngày kết thúc và lịch. Các giai đoạn con theo năm và bootstrap khối trượt theo cặp
chỉ mang tính mô tả, không xác lập ý nghĩa thống kê.
