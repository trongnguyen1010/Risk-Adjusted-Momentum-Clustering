# Báo cáo thí nghiệm experiment-85dd31d7598b

data_mode = synthetic

**KIỂM CHỨNG KỸ THUẬT BẰNG DỮ LIỆU GIẢ LẬP (SYNTHETIC)**

Mô phỏng danh mục trên chuỗi lợi suất với tỷ trọng phân số, khớp tại giá đóng cửa phiên kế tiếp. Chưa mô phỏng sổ giao dịch theo số lượng cổ phiếu thực tế.
Không đánh giá trên tập kiểm định độc lập (holdout), không chọn mô hình dựa trên lợi nhuận.

Số thời điểm phân cụm: 6; số thời điểm bỏ qua: 0; số bản ghi gán cụm: 72.

## Các tệp kết quả

- [Chỉ tiêu hiệu quả](performance.csv)
- [Đặc trưng từng cụm](profiles.csv)
- [Chỉ tiêu đánh giá số cụm](diagnostics.csv)
- [Ma trận chuyển cụm](transitions.csv)
- [Độ ổn định qua thời gian](stability.jsonl)

Khoảng tin cậy bootstrap được tính với chiến lược đã cố định; kết quả này không chứng minh ý nghĩa thống kê của chiến lược.

## Các giả định được khai báo

- **Lãi suất phi rủi ro:** Giả định nghiên cứu: lãi suất hiệu dụng năm bằng 0, chỉ dùng cho minh họa trên dữ liệu giả lập.
- **Chi phí giao dịch và trượt giá:** Giả định nghiên cứu: phí 10 điểm cơ bản (0,10%) cộng trượt giá 5 điểm cơ bản (0,05%) trên giá trị giao dịch, áp dụng cho cả mua và bán.
- **Lợi suất tiền mặt:** Tiền mặt chưa đầu tư có lợi suất bằng 0; không vay, không dùng đòn bẩy hoặc tài trợ vốn.
- **Quy ước lợi suất và mô phỏng:** Lợi suất đơn trên dữ liệu giả lập; khớp tại giá đóng cửa phiên kế tiếp bằng tỷ trọng phân số trên chuỗi lợi suất; chưa mô phỏng lô giao dịch và thời gian thanh toán của sàn.
- **Cơ sở lựa chọn số cụm:** Cố định k=3 trước đánh giá để kiểm chứng kỹ thuật. Các chỉ tiêu cho k=2..10, ý nghĩa kinh tế và độ cân bằng giữa các cụm còn cần được thẩm định trong nghiên cứu thực tế.
