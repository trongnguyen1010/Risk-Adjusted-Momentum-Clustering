# Các giới hạn còn lại và điều kiện nghiệm thu

1. **Thử nghiệm thật đang bị chặn:** chưa xác minh giá gốc/điều chỉnh, `volume`/`va`,
   múi giờ và thời điểm khả dụng ban đầu của KBS. Riêng phép đổi tỷ lệ trong SDK không
   đủ xác lập đơn vị chuẩn VND/cổ phiếu. Chưa thu thập dữ liệu diện rộng.
2. Chưa có danh mục lịch sử đã xác minh bao phủ hủy niêm yết, tái niêm yết, chuyển sàn
   và mã cũ. Danh sách hiện tại không thể loại bỏ thiên lệch sống sót.
3. Chưa tích hợp lịch có thẩm quyền hoặc nguồn sự kiện doanh nghiệp đầy đủ. Trường cho
   phép `null` chỉ biểu đạt thiếu bằng chứng, không có nghĩa yêu cầu dữ liệu đã đạt.
4. Dữ liệu lịch sử đã tải có thể chứa các bản sửa đổi dùng thông tin tương lai. Kiểm
   thử thuật toán không nhìn trước không chứng minh dữ liệu gốc là đúng theo từng thời điểm.
5. Mô phỏng trong không gian lợi suất bỏ qua số cổ phiếu/lô thực tế, thanh toán, từng
   loại thuế, chi trả cổ tức, quyền mua, khớp một phần, giới hạn giá và thu hồi khi hủy
   niêm yết.
6. Đã có KMeans; PCA/GMM/Ward/DBSCAN và điều kiện nghiệm thu ba mô hình trong PDF cũ
   chưa hoàn tất. Quy trình cho tập kiểm định độc lập cần được rà soát; không chọn mô
   hình theo lợi nhuận.
7. Mẫu giả lập có tính nhân tạo và quy mô nhỏ. Bootstrap không bao gồm bất định do lựa
   chọn; không tuyên bố lợi thế kinh tế hay ý nghĩa thống kê.
8. `rf`, chi phí và lợi suất tiền mặt trong bản demo là các giả định công khai. Nguồn
   và quy ước `rf` thật cần được xác minh; không âm thầm dùng `rf=0`.
9. KMeans dùng JSONL trong bộ nhớ và thư viện chuẩn chưa được đo hiệu năng với 300 mã
   trong 6 năm. Chưa có phép hợp nhất gia tăng/hai chiều thời gian hoặc khóa nhiều bộ
   ghi; mỗi lần chạy chỉ có một bộ ghi.
10. Việc tái lập trên máy độc lập, sổ dữ liệu gốc đầy đủ, độ phủ dữ liệu thật, kết luận
    khóa luận và nghiệm thu M1/M2/M3 vẫn chưa hoàn thành.

Dữ liệu giả lập không bao giờ có thể mở điều kiện thử nghiệm hay mở rộng dữ liệu.
Kết quả chạy thành công chỉ là bằng chứng kỹ thuật, không phải nghiệm thu nghiên cứu
hoặc khóa luận. Xem `phase_report.md` để biết các lần chạy thực tế.
