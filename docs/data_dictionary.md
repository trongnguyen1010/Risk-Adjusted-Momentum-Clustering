# Từ điển dữ liệu chuẩn — hợp đồng 1.1.0

Được sinh từ các schema thực thi bởi `scripts/build_data_dictionary.py`.
Việc một trường cho phép `null` không bao giờ cho phép tự tạo giá trị. Dữ liệu tham chiếu giữ thông tin nguồn và thời điểm tải; bước chuyển đổi lưu các mã băm.

## securities

Khóa chính: `security_id`, `valid_from`

| Trường | Kiểu | Mô tả | Đơn vị | Cho phép null | Nguồn |
|---|---|---|---|---|---|
| security_id | string | Định danh kinh tế ổn định từ danh mục thời gian có bằng chứng | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| ticker | string | Mã có hiệu lực vào ngày bản ghi, không phải định danh vĩnh viễn | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| company_name | string | Tên công ty từ bản ghi tham chiếu có hiệu lực | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| exchange | string | Sàn có hiệu lực; hỗ trợ UPCOM rõ ràng | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| listing_date | date | Ngày niêm yết có thể giao dịch đầu tiên theo quy ước nguồn có bằng chứng | YYYY-MM-DD | có | dữ liệu tham chiếu đã xác minh |
| delisting_date | date | Ngày đầu tiên không thể giao dịch theo quy ước của kho mã | YYYY-MM-DD | có | dữ liệu tham chiếu đã xác minh |
| valid_from | date | Ngày bắt đầu khoảng, có tính ngày này | YYYY-MM-DD | không | dữ liệu tham chiếu đã xác minh |
| valid_to | date | Ngày kết thúc khoảng, không tính ngày này; null nghĩa là chưa có điểm kết thúc | YYYY-MM-DD | có | dữ liệu tham chiếu đã xác minh |
| available_at | datetime | Thời điểm khả dụng sớm nhất có bằng chứng; không bao giờ âm thầm lùi ngày | ISO-8601 có độ lệch múi giờ | không | dữ liệu tham chiếu đã xác minh |
| sector | string | Lĩnh vực có hiệu lực nếu nguồn cung cấp | nhãn/cờ | có | dữ liệu tham chiếu đã xác minh |
| industry | string | Ngành có hiệu lực nếu nguồn cung cấp | nhãn/cờ | có | dữ liệu tham chiếu đã xác minh |
| currency | string | Tiền tệ của chứng khoán/sự kiện | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| price_unit | string | VND/cổ phiếu chuẩn; bắt buộc có bằng chứng nguồn | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| identity_status | string | verified/provisional/synthetic; provisional không đủ điều kiện | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| source | string | Định danh nguồn gốc được giữ lại khi chuyển đổi | nhãn/cờ | không | thông tin truy vết pipeline |
| fetched_at | datetime | Thời điểm tải, khác với thời điểm khả dụng trong lịch sử | ISO-8601 có độ lệch múi giờ | không | thông tin truy vết pipeline |
| data_version | string | Định danh ảnh chụp/lần chạy bất biến; quan hệ truy vết nằm trong manifest | nhãn/cờ | không | thông tin truy vết pipeline |

## prices_daily

Khóa chính: `security_id`, `trade_date`

| Trường | Kiểu | Mô tả | Đơn vị | Cho phép null | Nguồn |
|---|---|---|---|---|---|
| security_id | string | Định danh kinh tế ổn định từ danh mục thời gian có bằng chứng | nhãn/cờ | không | ánh xạ nhà cung cấp đã xác minh |
| ticker | string | Mã có hiệu lực vào ngày bản ghi, không phải định danh vĩnh viễn | nhãn/cờ | không | ánh xạ nhà cung cấp đã xác minh |
| exchange | string | Sàn có hiệu lực; hỗ trợ UPCOM rõ ràng | nhãn/cờ | không | ánh xạ nhà cung cấp đã xác minh |
| trade_date | date | Ngày phiên theo giờ địa phương của sàn, dùng múi giờ có bằng chứng | YYYY-MM-DD | không | ánh xạ nhà cung cấp đã xác minh |
| raw_open | number | Giá mở cửa chưa điều chỉnh | VND/cổ phiếu | có | ánh xạ nhà cung cấp đã xác minh |
| raw_high | number | Giá cao nhất trong phiên chưa điều chỉnh | VND/cổ phiếu | có | ánh xạ nhà cung cấp đã xác minh |
| raw_low | number | Giá thấp nhất trong phiên chưa điều chỉnh | VND/cổ phiếu | có | ánh xạ nhà cung cấp đã xác minh |
| raw_close | number | Giá đóng cửa chưa điều chỉnh, không bao giờ sao chép từ giá điều chỉnh | VND/cổ phiếu | có | ánh xạ nhà cung cấp đã xác minh |
| adj_close | number | Giá đóng cửa điều chỉnh đã xác minh; null khi nguồn chưa rõ hoặc chỉ có giá chưa điều chỉnh | VND/cổ phiếu | có | ánh xạ nhà cung cấp đã xác minh |
| adjustment_basis | string | unadjusted/split_adjusted/total_return/unknown/synthetic | nhãn/cờ | không | ánh xạ nhà cung cấp đã xác minh |
| volume | number | Số cổ phiếu trong phạm vi giao dịch đã xác minh; null nếu chưa rõ | cổ phiếu | có | ánh xạ nhà cung cấp đã xác minh |
| traded_value | number | Giá trị danh nghĩa đã xác minh; không bao giờ dùng giá điều chỉnh nhân khối lượng làm đại diện | VND | có | ánh xạ nhà cung cấp đã xác minh |
| trading_status | string | normal/suspended/halted/unknown; có thanh giá không chứng minh trạng thái bình thường | nhãn/cờ | không | ánh xạ nhà cung cấp đã xác minh |
| available_at | datetime | Thời điểm khả dụng sớm nhất có bằng chứng; không bao giờ âm thầm lùi ngày | ISO-8601 có độ lệch múi giờ | không | ánh xạ nhà cung cấp đã xác minh |
| source | string | Định danh nguồn gốc được giữ lại khi chuyển đổi | nhãn/cờ | không | thông tin truy vết pipeline |
| fetched_at | datetime | Thời điểm tải, khác với thời điểm khả dụng trong lịch sử | ISO-8601 có độ lệch múi giờ | không | thông tin truy vết pipeline |
| data_version | string | Định danh ảnh chụp/lần chạy bất biến; quan hệ truy vết nằm trong manifest | nhãn/cờ | không | thông tin truy vết pipeline |

## benchmark_daily

Khóa chính: `index_id`, `trade_date`

| Trường | Kiểu | Mô tả | Đơn vị | Cho phép null | Nguồn |
|---|---|---|---|---|---|
| index_id | string | VNINDEX/VN30/HNXINDEX hoặc chỉ số được cấu hình rõ | nhãn/cờ | không | ánh xạ nhà cung cấp đã xác minh |
| trade_date | date | Ngày phiên theo giờ địa phương của sàn, dùng múi giờ có bằng chứng | YYYY-MM-DD | không | ánh xạ nhà cung cấp đã xác minh |
| close | number | Mức đóng cửa của chỉ số theo index_basis đã khai báo | điểm chỉ số | không | ánh xạ nhà cung cấp đã xác minh |
| total_return_level | number | Mức lợi suất toàn phần do nguồn cung cấp riêng, không tự tạo | điểm chỉ số | có | ánh xạ nhà cung cấp đã xác minh |
| available_at | datetime | Thời điểm khả dụng sớm nhất có bằng chứng; không bao giờ âm thầm lùi ngày | ISO-8601 có độ lệch múi giờ | không | ánh xạ nhà cung cấp đã xác minh |
| source | string | Định danh nguồn gốc được giữ lại khi chuyển đổi | nhãn/cờ | không | thông tin truy vết pipeline |
| fetched_at | datetime | Thời điểm tải, khác với thời điểm khả dụng trong lịch sử | ISO-8601 có độ lệch múi giờ | không | thông tin truy vết pipeline |
| data_version | string | Định danh ảnh chụp/lần chạy bất biến; quan hệ truy vết nằm trong manifest | nhãn/cờ | không | thông tin truy vết pipeline |
| exchange | string | Sàn có hiệu lực; hỗ trợ UPCOM rõ ràng | nhãn/cờ | có | ánh xạ nhà cung cấp đã xác minh |
| index_basis | string | price/total_return/unknown/synthetic | nhãn/cờ | có | ánh xạ nhà cung cấp đã xác minh |

## trading_calendar

Khóa chính: `exchange`, `trade_date`

| Trường | Kiểu | Mô tả | Đơn vị | Cho phép null | Nguồn |
|---|---|---|---|---|---|
| exchange | string | Sàn có hiệu lực; hỗ trợ UPCOM rõ ràng | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| trade_date | date | Ngày phiên theo giờ địa phương của sàn, dùng múi giờ có bằng chứng | YYYY-MM-DD | không | dữ liệu tham chiếu đã xác minh |
| is_open | boolean | Cờ phiên giao dịch từ nguồn độc lập có thẩm quyền | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| is_month_end | boolean | Phiên mở cửa cuối cùng đã xác minh của một tháng đầy đủ | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| close_at | datetime | Thời điểm đóng cửa sàn | ISO-8601 có độ lệch múi giờ | không | dữ liệu tham chiếu đã xác minh |
| decision_at | datetime | Thời điểm chốt nghiên cứu đã cấu hình, tại hoặc sau giờ đóng cửa | ISO-8601 có độ lệch múi giờ | không | dữ liệu tham chiếu đã xác minh |
| source | string | Định danh nguồn gốc được giữ lại khi chuyển đổi | nhãn/cờ | không | thông tin truy vết pipeline |
| fetched_at | datetime | Thời điểm tải, khác với thời điểm khả dụng trong lịch sử | ISO-8601 có độ lệch múi giờ | không | thông tin truy vết pipeline |
| data_version | string | Định danh ảnh chụp/lần chạy bất biến; quan hệ truy vết nằm trong manifest | nhãn/cờ | không | thông tin truy vết pipeline |
| open_at | datetime | Thời điểm mở cửa sàn; null với lịch giả lập cũ | ISO-8601 có độ lệch múi giờ | có | dữ liệu tham chiếu đã xác minh |
| available_at | datetime | Thời điểm khả dụng sớm nhất có bằng chứng; không bao giờ âm thầm lùi ngày | ISO-8601 có độ lệch múi giờ | có | dữ liệu tham chiếu đã xác minh |

## corporate_actions

Khóa chính: `event_id`

| Trường | Kiểu | Mô tả | Đơn vị | Cho phép null | Nguồn |
|---|---|---|---|---|---|
| event_id | string | Định danh sự kiện ổn định từ nguồn | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| security_id | string | Định danh kinh tế ổn định từ danh mục thời gian có bằng chứng | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| event_type | string | cash_dividend/stock_dividend/split/reverse_split/rights_issue/bonus_share/other | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| announcement_date | date | Ngày công bố; available_at kiểm soát thời điểm biết trong ngày | YYYY-MM-DD | không | dữ liệu tham chiếu đã xác minh |
| available_at | datetime | Thời điểm khả dụng sớm nhất có bằng chứng; không bao giờ âm thầm lùi ngày | ISO-8601 có độ lệch múi giờ | không | dữ liệu tham chiếu đã xác minh |
| ex_date | date | Ngày giao dịch không hưởng quyền | YYYY-MM-DD | không | dữ liệu tham chiếu đã xác minh |
| record_date | date | Ngày đăng ký cuối cùng nếu biết | YYYY-MM-DD | có | dữ liệu tham chiếu đã xác minh |
| effective_date | date | Ngày sự kiện có hiệu lực theo quy ước nguồn | YYYY-MM-DD | không | dữ liệu tham chiếu đã xác minh |
| adjustment_factor | number | Hệ số của nhà cung cấp, cần bằng chứng riêng về quy ước | không thứ nguyên | có | dữ liệu tham chiếu đã xác minh |
| cash_amount | number | Khoản phân phối tiền mặt trên mỗi cổ phiếu | VND/cổ phiếu | có | dữ liệu tham chiếu đã xác minh |
| ratio | number | Số cổ phiếu mới trên mỗi cổ phiếu cũ; cần xác minh quy ước sự kiện | cổ phiếu mới/cổ phiếu cũ | có | dữ liệu tham chiếu đã xác minh |
| source | string | Định danh nguồn gốc được giữ lại khi chuyển đổi | nhãn/cờ | không | thông tin truy vết pipeline |
| fetched_at | datetime | Thời điểm tải, khác với thời điểm khả dụng trong lịch sử | ISO-8601 có độ lệch múi giờ | không | thông tin truy vết pipeline |
| data_version | string | Định danh ảnh chụp/lần chạy bất biến; quan hệ truy vết nằm trong manifest | nhãn/cờ | không | thông tin truy vết pipeline |
| payment_date | date | Ngày thanh toán nếu biết, không giả định bằng ex_date | YYYY-MM-DD | có | dữ liệu tham chiếu đã xác minh |
| currency | string | Tiền tệ của chứng khoán/sự kiện | nhãn/cờ | có | dữ liệu tham chiếu đã xác minh |

## risk_free_rate

Khóa chính: `date`, `tenor`, `available_at`

| Trường | Kiểu | Mô tả | Đơn vị | Cho phép null | Nguồn |
|---|---|---|---|---|---|
| date | date | Ngày hiệu lực của quan sát lãi suất phi rủi ro | YYYY-MM-DD | không | dữ liệu tham chiếu đã xác minh |
| annual_rate | number | Lãi suất năm hiệu dụng dạng thập phân sau khi chuẩn hóa nguồn rõ ràng | thập phân/năm | không | dữ liệu tham chiếu đã xác minh |
| tenor | string | Định danh kỳ hạn hoặc đại diện lãi suất | nhãn/cờ | không | dữ liệu tham chiếu đã xác minh |
| available_at | datetime | Thời điểm khả dụng sớm nhất có bằng chứng; không bao giờ âm thầm lùi ngày | ISO-8601 có độ lệch múi giờ | không | dữ liệu tham chiếu đã xác minh |
| source | string | Định danh nguồn gốc được giữ lại khi chuyển đổi | nhãn/cờ | không | thông tin truy vết pipeline |
| fetched_at | datetime | Thời điểm tải, khác với thời điểm khả dụng trong lịch sử | ISO-8601 có độ lệch múi giờ | không | thông tin truy vết pipeline |
| data_version | string | Định danh ảnh chụp/lần chạy bất biến; quan hệ truy vết nằm trong manifest | nhãn/cờ | không | thông tin truy vết pipeline |
| day_count_basis | string | Quy ước lãi suất; đặc trưng ở chế độ bảng thật cần chuẩn hóa theo 252 phiên giao dịch/năm | nhãn/cờ | có | dữ liệu tham chiếu đã xác minh |
