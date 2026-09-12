# Báo cáo rà soát repository — 11/09/2026

Phạm vi: toàn bộ mô-đun ứng dụng, hợp đồng dữ liệu thực thi, script, cấu hình, kiểm thử và tài liệu dự án. Cấu trúc dữ liệu và manifest của nhà cung cấp được kiểm tra ở chế độ chỉ đọc. Không sửa các PDF gốc; bản đánh giá tài liệu đã có nằm tại DOCUMENT_REVIEW.md.

Bảng dưới ghi nhận trạng thái tại thời điểm rà soát ban đầu, kèm phát hiện toàn vẹn dữ liệu bổ sung. Trạng thái sau triển khai nằm trong [báo cáo theo giai đoạn](phase_report.md).

| Trạng thái ban đầu | Thành phần | Phát hiện hoặc việc cần làm |
|---|---|---|
| ĐÃ CÓ | Nhập dữ liệu CSV/HTTP | Lưu trang dữ liệu bất biến, SHA-256, thử lại, phân trang và tiếp tục đúng lần chạy |
| ĐÃ CÓ | Lớp lưu dữ liệu nhà cung cấp | SDK 4.0.6, `count=None` khai báo rõ, chia lô, giới hạn thời gian và tiếp tục tải |
| ĐÃ CÓ | Định danh theo thời gian | Khoảng hiệu lực nửa kín; cách ly lỗi chồng lấn, khóa ngoại và vòng đời niêm yết |
| ĐÃ CÓ | Công thức đặc trưng | Động lượng 21/63/126/252 phiên, độ biến động và Sharpe mẫu, beta, mức sụt giảm tối đa; giữ nguyên phiên thiếu theo lịch |
| MỘT PHẦN | Hợp đồng dữ liệu chuẩn | Đã có 6 bảng đầu vào; còn thiếu UPCOM, giá điều chỉnh/khối lượng cho phép `null`, thời điểm biết lịch, thông tin thanh toán/tiền tệ của sự kiện và quy ước lãi suất |
| MỘT PHẦN | Kiểm soát chất lượng | Chưa kiểm tra lịch và thời điểm khả dụng của chỉ số tham chiếu; thông tin cách ly lỗi chưa đủ ngữ cảnh |
| MỘT PHẦN | Tính đúng thời điểm | Đã kiểm soát thời điểm khả dụng theo chính sách bảo thủ từng ngày; chưa chặn lịch chưa biết và việc trộn cơ sở điều chỉnh giá |
| MỘT PHẦN | Khả năng tái lập | Có mã băm mã nguồn/cấu hình/dữ liệu gốc; thiếu thông tin môi trường thư viện và kết quả nghiên cứu |
| CHƯA CÓ | Chuyển đổi dữ liệu nhà cung cấp | Chưa có điều kiện kiểm tra manifest/bằng chứng, bộ phân tích bản ghi và phép ghép dữ liệu tham chiếu |
| CHƯA CÓ | Phân cụm và đánh giá | Mới có giao diện; chưa có mô hình đã khớp, chỉ tiêu đánh giá, căn chỉnh nhãn hoặc chuyển cụm |
| CHƯA CÓ | Mô phỏng danh mục | Mới có giao diện; chưa có tỷ trọng, độ trễ tín hiệu, chi phí hoặc chỉ tiêu hiệu quả |
| CHƯA CÓ | Quy trình nghiên cứu | Chưa chốt tập phát triển/kiểm định độc lập, giả định, phân tích độ nhạy và báo cáo |
| RỦI RO | Ý nghĩa dữ liệu nhà cung cấp | Chưa xác minh đơn vị, giá gốc/điều chỉnh, `va`, múi giờ và thời điểm công bố lịch sử |
| RỦI RO | Tập chứng khoán nghiên cứu | Danh mục hiện tại gồm 3.415 bản ghi không phải danh mục định danh lịch sử |
| RỦI RO | Độ phủ dữ liệu | Mẫu thật chỉ có 3 cổ phiếu và VNINDEX, mỗi chuỗi 20 dòng; không đủ kiểm tra đặc trưng 252 phiên |
| RỦI RO | Lịch và sự kiện doanh nghiệp | Chưa có bộ dữ liệu tham chiếu lịch sử thật được xác minh; không được tự tạo |
| RỦI RO | Kết luận thống kê | Minh họa 18 tháng bằng dữ liệu giả lập chỉ kiểm chứng kỹ thuật |
| RỦI RO | Toàn vẹn ảnh chụp có sẵn | Kiểm tra byte sau đó phát hiện 5/10 file gốc đã đổi định dạng và lệch mã băm. Đã phục hồi các byte khớp bản gốc từ bộ nhớ đệm sang ảnh chụp mới, giữ nguyên file cũ |

Triển khai tiếp theo giữ luồng xử lý dữ liệu chuẩn và các định nghĩa đặc trưng đang hoạt động. Phần chuyển đổi dữ liệu thật có thể bị chặn trong khi các phần kỹ thuật ngoại tuyến độc lập vẫn được thực hiện. Chỉ chấp nhận bộ thử nghiệm thật và mở rộng dữ liệu khi đủ bằng chứng về ý nghĩa dữ liệu và nguồn tham chiếu.
