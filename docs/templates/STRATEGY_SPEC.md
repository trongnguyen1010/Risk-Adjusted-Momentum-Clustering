# Strategy specification [version]

Trạng thái: đề xuất chưa khóa. Không chạy đánh giá holdout trước khi điền đủ.

- Mục tiêu, data version, ngày development/holdout.
- Tín hiệu: snapshot, available_at, ranking cụm, tie-break.
- Universe: history, status, thanh khoản; missing data/identity policy.
- Weights: equal-weight, số mã tối thiểu, cap/mã, cash rule.
- Execution: open/close phiên tiếp theo, lịch, lô, thanh khoản, reject/partial fill.
- Accounting: initial capital, cash, holdings, mark price, delisting/suspension.
- Corporate actions: split/cash/rights, ngày áp dụng, tránh đếm đôi.
- Costs: fee/tax/slippage theo bps, nguồn/ngày hiệu lực hoặc giả định sensitivity.
- Benchmarks: VNINDEX, equal-weight và momentum không clustering cùng điều kiện.
- Tests: flat round-trip phí, tăng 10% không phí, signal lag, không âm cash, split conservation, future append.
- Owner/reviewer, ngày khóa, hash config, giới hạn mô phỏng.
