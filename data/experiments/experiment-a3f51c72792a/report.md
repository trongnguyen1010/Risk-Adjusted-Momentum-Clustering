# Báo cáo thí nghiệm experiment-a3f51c72792a

data_mode = real

**KẾT QUẢ PILOT — KHÔNG PHẢI KẾT QUẢ CUỐI CÙNG CỦA LUẬN VĂN**

Mô phỏng danh mục trên chuỗi lợi suất với tỷ trọng phân số, khớp tại giá đóng cửa phiên kế tiếp. Chưa mô phỏng sổ giao dịch theo số lượng cổ phiếu thực tế.
Không đánh giá trên tập kiểm định độc lập (holdout), không chọn mô hình dựa trên lợi nhuận.

Số thời điểm phân cụm: 24; số thời điểm bỏ qua: 0; số bản ghi gán cụm: 240.

## Các tệp kết quả

- [Chỉ tiêu hiệu quả](performance.csv)
- [Đặc trưng từng cụm](profiles.csv)
- [Chỉ tiêu đánh giá số cụm](diagnostics.csv)
- [Ma trận chuyển cụm](transitions.csv)
- [Độ ổn định qua thời gian](stability.jsonl)

Khoảng tin cậy bootstrap được tính với chiến lược đã cố định; kết quả này không chứng minh ý nghĩa thống kê của chiến lược.

## Các giả định được khai báo

- **Lãi suất phi rủi ro:** Đặt rf_annual=0 và risk_free_method=assumption; không tuyên bố đã có chuỗi risk-free lịch sử.
- **Chi phí giao dịch và trượt giá:** Giả định nghiên cứu: phí 10 điểm cơ bản (0,10%) cộng trượt giá 5 điểm cơ bản (0,05%) trên giá trị giao dịch, áp dụng cho cả mua và bán.
- **Lợi suất tiền mặt:** Tiền mặt chưa đầu tư có lợi suất bằng 0; không vay, không dùng đòn bẩy hoặc tài trợ vốn.
- **Quy ước lợi suất và mô phỏng:** Lợi suất hồi cứu từ giá điều chỉnh kỹ thuật của KBS, với return_method=vendor_adjusted_price_proxy; chưa xác nhận là total_return. Không có raw price; chỉ mô phỏng đơn vị đầu tư phân số với execution=next_close. Bảng corporate_actions rỗng và không cộng thêm cổ tức.
- **Cơ sở lựa chọn số cụm:** Cố định k=3 và seed=42 trước khi đánh giá hiệu quả pilot; universe gồm 10 security, báo cáo diagnostics cho k=2..9 và không chọn mô hình theo lợi nhuận.
- **identity:** Dùng identity_status=provisional_verified_for_pilot từ thông báo VSD có ngày, danh sách KBS hiện tại và các bar đã quan sát; giả định ticker/exchange không đổi trong 2023–2025; universe gồm các mã còn tồn tại được chọn trước.
- **availability:** EOD 15:00 Asia/Ho_Chi_Minh + 120 phút; decision hàng tháng lúc 17:00; execution ở giá đóng cửa phiên kế tiếp; đây không phải vendor timestamp.
- **calendar:** calendar_method=benchmark_derived từ ngày có VNINDEX; giả định ngày phiên HNX/HOSE đồng bộ; không suy lịch từ một cổ phiếu riêng lẻ.
