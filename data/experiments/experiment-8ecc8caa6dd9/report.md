# Báo cáo thí nghiệm experiment-8ecc8caa6dd9

data_mode = synthetic

**KIỂM CHỨNG KỸ THUẬT BẰNG DỮ LIỆU GIẢ LẬP (SYNTHETIC)**

Portfolio evaluation đã tắt: đây là M2 clustering/diagnostic run, không sinh backtest hoặc performance metric.
Không đánh giá trên tập kiểm định độc lập (holdout), không chọn mô hình dựa trên lợi nhuận.

Số thời điểm phân cụm: 6; số thời điểm bỏ qua: 0; số bản ghi gán cụm: 72.

## Các tệp kết quả

- [Đặc trưng từng cụm](profiles.csv)
- [Chỉ tiêu đánh giá số cụm](diagnostics.csv)
- [Ma trận chuyển cụm](transitions.csv)
- [Độ ổn định qua thời gian](stability.jsonl)

Run này chỉ xuất cluster diagnostics và temporal diagnostics; không có Sharpe, ROI hoặc portfolio return.

## Các giả định được khai báo

- **Cơ sở lựa chọn số cụm:** Cố định k=3 trước đánh giá để kiểm chứng kỹ thuật. Các chỉ tiêu cho k=2..10, ý nghĩa kinh tế và độ cân bằng giữa các cụm còn cần được thẩm định trong nghiên cứu thực tế.
