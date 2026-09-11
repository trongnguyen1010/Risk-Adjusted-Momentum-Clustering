# Dashboard - phạm vi M3

Chưa có UI chạy trong v0.1.0. FE phát triển app đọc artifacts, không tải nguồn hay fit model trực tiếp khi đổi filter.

Trang cần có: data overview/coverage/QC; cluster scatter có explained variance; profiles; transition và entry/exit; backtest NAV/gross/net/benchmark/costs. Tất cả phải đọc cùng run_id/data_version; missing artifact hiện “chưa có kết quả”, không dùng số 0 hoặc synthetic không gắn nhãn.

Input hiện có: clean tables, monthly features, coverage. Input M2/M3 theo schemas assignments/transitions/trades/nav; cần bổ sung profiles, holdings và model manifest khi implementation bắt đầu. Đối chiếu số trên UI với artifact gốc trong review.
