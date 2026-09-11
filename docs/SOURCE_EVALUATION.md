# Đánh giá nguồn dữ liệu - 11/09/2026

## Kết luận khảo sát

Người dùng xác nhận mentor không cung cấp nguồn; nhóm tự tìm hiểu. Chọn **Vnstock Community 4.0.6** làm ứng viên lấy sample, giữ CSV/HTTP adapter độc lập để thay nguồn. Đây là lựa chọn engineering cho khảo sát, chưa kết luận nguồn đáp ứng M1 hay backtest đầy đủ.

Theo [giới thiệu chính thức](https://www.vnstocks.com/docs/vnstock/gioi-thieu-vnstock), bản cộng đồng truy vấn nguồn từ máy người dùng, trả pandas DataFrame; trang nêu lịch sử ngày tối đa 8 năm và hạn mức tối đa 60 request/phút khi dùng API key. Đây là thông tin công bố, không phải kết quả đo độ phủ thực tế của project; 6 năm dữ liệu vẫn cần kiểm tra theo từng mã.

[Market API](https://www.vnstocks.com/docs/vnstock/du-lieu-thi-truong-market-data) cung cấp `Market().equity(symbol).ohlcv(...)` và `Market().index('VNINDEX').ohlcv(...)`. [Reference API](https://vnstocks.com/docs/vnstock/tra-cuu-thong-tin-tham-chieu-reference) cung cấp danh mục niêm yết theo sàn. Code adapter dùng giao diện 4.x và khóa version, không copy ví dụ Quote 3.x đã cũ.

Tài liệu [Quote của gói mở rộng](https://www.vnstocks.com/docs/vnstock-data/du-lieu-giao-dich) gọi chuỗi history là giá đã điều chỉnh kỹ thuật. Đây là lý do phải kiểm tra ý nghĩa cột cụ thể; không dùng mô tả của gói mở rộng để mặc định Community có cùng quyền lợi và semantics.

## So sánh hướng tiếp cận

| Nguồn/hướng | Giá trị với project | Giới hạn cần xác minh | Quyết định |
|---|---|---|---|
| Vnstock Community | Có SDK công khai, giao diện equity/index và listing; đã viết collector | Độ phủ mã rời sàn, quyền sử dụng, revision, raw vs adjusted, metadata PIT, hạn mức thực tế | Ưu tiên sample |
| API/CSV trực tiếp từ công ty chứng khoán hoặc nhà cung cấp khác | Có thể bổ sung raw OHLC/actions/historical identity | Chưa chọn endpoint hay hợp đồng cụ thể | Hỗ trợ qua provider interface, chưa khẳng định khả năng |
| Công bố của sàn/doanh nghiệp | Ứng viên đối chiếu sự kiện/niêm yết | Chưa có bộ tải hệ thống, chưa xác minh coverage | Công việc audit tiếp theo |

Không đề xuất mua gói trả phí trước khi sample và gap report chỉ ra nhu cầu. SDK công khai hoặc miễn phí không mặc nhiên cho quyền tái phân phối mọi dữ liệu vendor.

## Ma trận kiểm tra thực nghiệm

| Tiêu chí | Cần bằng chứng | Hiện trạng |
|---|---|---|
| ≥300 security_id và ≥5 năm | Coverage theo mã/năm/sàn, cả trước warm-up và sau warm-up | Chưa chứng minh |
| HOSE/HNX và mã đã rời sàn | Historical security master, interval và nguồn | Chưa chứng minh |
| Adjusted price | Đối chiếu ít nhất vài corporate actions, mô tả adjustment | Chưa xác minh đầy đủ |
| Raw OHLC | Bằng chứng giá giao dịch không bị back-adjusted | Chưa xác minh |
| traded_value | Đơn vị và phạm vi matched/total giao dịch | Chưa xác minh |
| VNINDEX | Cùng lịch, phân biệt price index/total return | Đã tải sample 20 dòng; cần audit lịch và semantics |
| Calendar | Ngày nghỉ, phiên mở, cuối tháng thực | Chưa có nguồn chính thức tích hợp |
| Point-in-time | available_at và lịch sử revisions | Chưa chứng minh |
| Tái lập vận hành | Raw, checksum, retry, resume, version | Đã có trong code; sample KBS qua SDK tải thành công; xem VALIDATION.md |

Kết quả cài SDK và thử nguồn thực tế được ghi riêng ở [VALIDATION.md](VALIDATION.md). Không nâng trạng thái trong bảng này chỉ vì tải sample thành công.

## Biểu mẫu cho mỗi nguồn mới

Tên/source ID; URL tài liệu và ngày truy cập; endpoint/SDK version; sample run_id; số mã và first/last date; price/volume/value unit; adjustment methodology; dữ liệu mã rời sàn; lịch và corporate actions; quyền lưu/chia sẻ; rate limit; kết quả kiểm tra lại; các field thiếu; người audit; kết luận dùng/không dùng theo từng stage.
