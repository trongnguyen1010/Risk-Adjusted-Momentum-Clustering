# Báo cáo thí nghiệm experiment-20260929T153217Z-31d14d96

data_mode = real

**KẾT QUẢ PILOT — KHÔNG PHẢI KẾT QUẢ CUỐI CÙNG CỦA LUẬN VĂN**

Portfolio evaluation đã tắt: đây là M2 clustering/diagnostic run, không sinh backtest hoặc performance metric.
Không đánh giá trên tập kiểm định độc lập (holdout), không chọn mô hình dựa trên lợi nhuận.

Số thời điểm phân cụm: 15; số thời điểm bỏ qua: 0; số bản ghi gán cụm: 5615.

## Các tệp kết quả

- [Đặc trưng từng cụm](profiles.csv)
- [Chỉ tiêu đánh giá số cụm](diagnostics.csv)
- [Ma trận chuyển cụm](transitions.csv)
- [Độ ổn định qua thời gian](stability.jsonl)

Run này chỉ xuất cluster diagnostics và temporal diagnostics; không có Sharpe, ROI hoặc portfolio return.

## Các giả định được khai báo

- **Cơ sở lựa chọn số cụm:** Chọn một Global K duy nhất chỉ từ diagnostics trên 15 snapshot development; không dùng holdout hoặc portfolio performance.
