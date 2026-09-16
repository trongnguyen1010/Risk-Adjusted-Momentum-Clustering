# Báo cáo thí nghiệm experiment-de5f4d68afa0

data_mode = real

**PILOT RESULT — NOT FINAL THESIS RESULT**

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

- **Lãi suất phi rủi ro:** rf_annual=0; risk_free_method=assumption; no historical risk-free series claimed.
- **Chi phí giao dịch và trượt giá:** Giả định nghiên cứu: phí 10 điểm cơ bản (0,10%) cộng trượt giá 5 điểm cơ bản (0,05%) trên giá trị giao dịch, áp dụng cho cả mua và bán.
- **Lợi suất tiền mặt:** Tiền mặt chưa đầu tư có lợi suất bằng 0; không vay, không dùng đòn bẩy hoặc tài trợ vốn.
- **Quy ước lợi suất và mô phỏng:** Real KBS retrospective technically adjusted price returns; vendor_adjusted_price_proxy, not verified total return. Raw prices unavailable; fractional next-close investment-unit simulation only. Corporate-actions table empty; no extra dividends added.
- **Cơ sở lựa chọn số cụm:** k=3 fixed before pilot performance evaluation, seed=42; 10 securities, report k=2..9 diagnostics, no profitability-based selection.
- **identity:** provisional_verified_for_pilot from dated VSD notices, current KBS listing and observed bars; unchanged ticker/exchange in 2023-2025 assumed; selected surviving universe.
- **availability:** EOD 15:00 Asia/Ho_Chi_Minh + 120 minutes; monthly decision at 17:00; execution at next market session close; not a vendor timestamp.
- **calendar:** benchmark_derived from VNINDEX dates; HNX/HOSE synchronized dates assumed; no individual-stock inferred calendar.
