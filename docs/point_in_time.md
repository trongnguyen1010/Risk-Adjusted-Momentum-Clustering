# Ranh giới dữ liệu đúng theo từng thời điểm

- Định danh được ghép theo khoảng `[valid_from,valid_to)`, giữ quy ước của kho mã rằng
  `delisting_date` là ngày đầu tiên không còn giao dịch. Danh sách hiện tại không xác
  lập được lịch sử.
- Lịch là dữ liệu tham chiếu độc lập, không phải danh sách ngày giá duy nhất. Ngày cuối
  tháng đòi hỏi một tháng đầy đủ đã được xác minh. Không thể dùng chính các thanh giá
  chưa đầy đủ của nhà cung cấp để chứng minh bản ghi lịch bị thiếu thực sự không tồn
  tại; cần thông tin truy vết của nguồn tham chiếu.
- Đặc trưng đòi hỏi giá, metadata và lịch đã được biết tại thời điểm quyết định mỗi
  ngày. Chính sách bảo thủ không phục hồi về sau các thanh giá đến muộn. Khoảng trống
  vẫn là `null`; không điền xuôi hoặc tính lợi suất qua thanh giá bị bỏ qua. Khi cơ sở
  điều chỉnh bị trộn, lịch sử cửa sổ trượt được đặt lại.
- Một phiên bản lịch sử được tải xuống không phải kho dữ liệu hai chiều thời gian. Các
  bản sửa đổi sau này của nhà cung cấp có thể ảnh hưởng quan sát cũ ngay cả trong cùng
  một cơ sở điều chỉnh. Dữ liệu PIT thực sự cần các phiên bản có ngày hoặc phương pháp
  sửa đổi có bằng chứng, không phải dấu thời gian tự tạo.
- Thời điểm khả dụng của cổ phiếu/chỉ số không thể trước giờ đóng cửa. Dấu thời gian
  không có múi giờ cần múi giờ đã được chứng minh. `fetched_at` là phương án dự phòng
  bảo thủ, thường làm ảnh chụp tháng cũ không đủ điều kiện; trường này không bao giờ
  được lùi về phiên gốc.
- Việc chọn lãi suất dùng các bản ghi đã biết lúc 00:00 giờ Việt Nam vào ngày tính lợi
  suất. Lãi suất thật ở chế độ bảng trước hết phải được chuẩn hóa thành lãi suất hiệu
  dụng năm theo 252 phiên giao dịch. Báo giá thị trường tiền tệ ACT/360 hoặc ACT/365
  cần phép quy đổi có tài liệu trước khi sử dụng.
- Bộ co giãn và mô hình chỉ nhìn thấy các dòng đủ điều kiện trong cùng một ảnh chụp.
  Thời điểm mục tiêu là thời điểm khả dụng muộn nhất của các đầu vào. Lệnh chỉ được
  khớp sau đó, tại giá đóng cửa phiên kế tiếp. Các mức định giá sau đó là kết quả đã
  xảy ra, không bao giờ là đầu vào cho mục tiêu trước đó.
- Giá định giá bị thiếu/do hủy niêm yết hoặc mã không thể giao dịch khi tái cân bằng sẽ
  chặn mô phỏng; chúng không âm thầm biến mất khỏi danh mục hay trở thành thanh lợi
  suất bằng 0.

Kiểm thử hồi quy xác minh tính bất biến khi nối dữ liệu tương lai, đầu vào đến muộn,
đặt lại cơ sở điều chỉnh, thời điểm khả dụng của lịch, khoảng ticker/sàn và độ trễ
khớp lệnh. Các kiểm thử này xác minh thuật toán, không xác minh mức độ đầy đủ của các
phiên bản lịch sử từ nhà cung cấp vốn không có sẵn.
