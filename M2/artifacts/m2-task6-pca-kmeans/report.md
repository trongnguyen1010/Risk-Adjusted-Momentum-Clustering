# Báo cáo thí nghiệm m2-task6-pca-kmeans

data_mode = real

**KẾT QUẢ PILOT — KHÔNG PHẢI KẾT QUẢ CUỐI CÙNG CỦA LUẬN VĂN**

Portfolio evaluation đã tắt: đây là M2 clustering/diagnostic run, không sinh backtest hoặc performance metric.
Không đánh giá trên tập kiểm định độc lập (holdout), không chọn mô hình dựa trên lợi nhuận.

Số thời điểm phân cụm: 60; số thời điểm bỏ qua: 0; số bản ghi gán cụm: 45646.

## Các tệp kết quả

- [Đặc trưng từng cụm](profiles.csv)
- [Chỉ tiêu đánh giá số cụm](diagnostics.csv)
- [Ma trận chuyển cụm](transitions.csv)
- [Độ ổn định qua thời gian](stability.jsonl)

Run này chỉ xuất cluster diagnostics và temporal diagnostics; không có Sharpe, ROI hoặc portfolio return.

## Các giả định được khai báo

- **Cơ sở lựa chọn số cụm:** Chọn một Global K duy nhất chỉ từ diagnostics trên 60 snapshot development (2019-2023); không dùng holdout hoặc portfolio performance.
