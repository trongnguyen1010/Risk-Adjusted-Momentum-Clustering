# Đánh giá nguồn dữ liệu - 11/09/2026

## Kết luận khảo sát

Người dùng xác nhận mentor không cung cấp nguồn; nhóm tự tìm hiểu. Chọn **Vnstock Community 4.0.6** làm ứng viên lấy mẫu, giữ bộ chuyển đổi CSV/HTTP độc lập để thay nguồn. Đây là lựa chọn kỹ thuật cho khảo sát, chưa kết luận nguồn đáp ứng M1 hay mô phỏng quá khứ đầy đủ.

Theo [giới thiệu chính thức](https://www.vnstocks.com/docs/vnstock/gioi-thieu-vnstock), bản cộng đồng truy vấn nguồn từ máy người dùng, trả pandas DataFrame; trang nêu lịch sử ngày tối đa 8 năm và hạn mức tối đa 60 request/phút khi dùng API key. Đây là thông tin công bố, không phải kết quả đo độ phủ thực tế của project; 6 năm dữ liệu vẫn cần kiểm tra theo từng mã.

[Market API](https://www.vnstocks.com/docs/vnstock/du-lieu-thi-truong-market-data) cung cấp `Market().equity(symbol).ohlcv(...)` và `Market().index('VNINDEX').ohlcv(...)`. [Reference API](https://vnstocks.com/docs/vnstock/tra-cuu-thong-tin-tham-chieu-reference) cung cấp danh mục niêm yết theo sàn. Code adapter dùng giao diện 4.x và khóa version, không copy ví dụ Quote 3.x đã cũ.

Tài liệu [Quote của gói mở rộng](https://www.vnstocks.com/docs/vnstock-data/du-lieu-giao-dich) gọi chuỗi history là giá đã điều chỉnh kỹ thuật. Đây là lý do phải kiểm tra ý nghĩa cột cụ thể; không dùng mô tả của gói mở rộng để mặc định Community có cùng quyền lợi và semantics.

## So sánh hướng tiếp cận

| Nguồn/hướng | Giá trị với project | Giới hạn cần xác minh | Quyết định |
|---|---|---|---|
| Vnstock Community | Có SDK công khai, giao diện cổ phiếu/chỉ số và niêm yết; đã viết trình thu thập | Độ phủ mã rời sàn, quyền sử dụng, bản sửa đổi, giá gốc so với điều chỉnh, metadata PIT, hạn mức thực tế | Ưu tiên mẫu |
| API/CSV trực tiếp từ công ty chứng khoán hoặc nhà cung cấp khác | Có thể bổ sung OHLC gốc/sự kiện/định danh lịch sử | Chưa chọn điểm cuối hay hợp đồng cụ thể | Hỗ trợ qua giao diện nhà cung cấp, chưa khẳng định khả năng |
| Công bố của sàn/doanh nghiệp | Ứng viên đối chiếu sự kiện/niêm yết | Chưa có bộ tải hệ thống, chưa xác minh độ phủ | Công việc kiểm tra tiếp theo |

Không đề xuất mua gói trả phí trước khi mẫu và báo cáo khoảng trống chỉ ra nhu cầu. SDK công khai hoặc miễn phí không mặc nhiên cho quyền tái phân phối mọi dữ liệu nhà cung cấp.

## Ma trận kiểm tra thực nghiệm

| Tiêu chí | Cần bằng chứng | Hiện trạng |
|---|---|---|
| ≥300 security_id và ≥5 năm | Coverage theo mã/năm/sàn, cả trước warm-up và sau warm-up | Chưa chứng minh |
| HOSE/HNX và mã đã rời sàn | Historical security master, interval và nguồn | Chưa chứng minh |
| Giá điều chỉnh | Đối chiếu ít nhất vài sự kiện doanh nghiệp, mô tả phương pháp điều chỉnh | Chưa xác minh đầy đủ |
| OHLC gốc | Bằng chứng giá giao dịch không bị điều chỉnh ngược | Chưa xác minh |
| `traded_value` | Đơn vị và phạm vi giao dịch khớp/toàn phần | Chưa xác minh |
| VNINDEX | Cùng lịch, phân biệt chỉ số giá/lợi suất toàn phần | Đã tải mẫu 20 dòng; cần kiểm tra lịch và ngữ nghĩa |
| Lịch | Ngày nghỉ, phiên mở, cuối tháng thực | Chưa có nguồn chính thức tích hợp |
| Đúng theo từng thời điểm | `available_at` và lịch sử bản sửa đổi | Chưa chứng minh |
| Tái lập vận hành | Dữ liệu gốc, mã băm, thử lại, tiếp tục, phiên bản | Đã có trong mã nguồn; mẫu KBS qua SDK tải thành công; xem VALIDATION.md |

Kết quả cài SDK và thử nguồn thực tế được ghi riêng ở [VALIDATION.md](VALIDATION.md). Không nâng trạng thái trong bảng này chỉ vì tải sample thành công.

## Biểu mẫu cho mỗi nguồn mới

Tên/ID nguồn; URL tài liệu và ngày truy cập; điểm cuối/phiên bản SDK; `run_id` mẫu; số mã và ngày đầu/cuối; đơn vị giá/khối lượng/giá trị; phương pháp điều chỉnh; dữ liệu mã rời sàn; lịch và sự kiện doanh nghiệp; quyền lưu/chia sẻ; giới hạn tốc độ; kết quả kiểm tra lại; các trường thiếu; người rà soát; kết luận dùng/không dùng theo từng giai đoạn.
