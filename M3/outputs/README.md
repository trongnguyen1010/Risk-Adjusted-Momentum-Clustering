# CSV kết quả backtest M3

Bản sao giữ nguyên byte của hai run đã seal; không chạy lại hoặc thay đổi backtest.
Có 62 CSV canonical bên dưới thư mục này và hai CSV Combined dễ đọc tại thư mục M3,
tổng cộng 64 CSV, khoảng 33,43 MiB. Các file JSON/Markdown đi kèm chỉ là danh mục và hướng dẫn.

| Bộ kết quả | Đường dẫn | Số tệp CSV |
|---|---|---:|
| Development: 60 quyết định, 59 kỳ thực thi | [20261104T121107Z-5557288c](development/20261104T121107Z-5557288c/) | 31 |
| Holdout: 24 quyết định, 23 kỳ thực thi | [20261104T133507Z-5557288c](holdout/20261104T133507Z-5557288c/) | 31 |
| Combined Development dễ đọc | [BACKTEST_DEV_COMBINED.csv](../BACKTEST_DEV_COMBINED.csv) | 1 |
| Combined Holdout dễ đọc | [BACKTEST_HOLDOUT_COMBINED_V2.csv](../BACKTEST_HOLDOUT_COMBINED_V2.csv) | 1 |

Mỗi segment có sáu CSV cho mỗi strategy: `targets`, `universe_audit`, `trade_ledger`,
`holdings`, `nav`, `turnover`; năm strategy là `combined`, `market_only`, `financial_only`,
`equal_weight`, `momentum_only`. CSV thứ 31 là `benchmark_vnindex.csv`.
Ngoài các CSV, mỗi thư mục run lưu trữ đầy đủ bộ ba tệp chứng thực:
manifest.json (môi trường & tham số), metrics.json (chỉ số hiệu suất) và seal.json (chữ ký niêm phong SHA256 chính thức).

Hai CSV dễ đọc diễn giải từng kỳ của Combined; không thay thế các CSV canonical để kiểm chứng.

[manifest.json](manifest.json) ghi đường dẫn nguồn, đường dẫn bản sao, kích thước và SHA256
của đủ 64 tệp. Source code backtest là commit `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf`.
Các seal/config nguồn được pin trong [sources.json](../sources.json).
Tệp trong `data/experiments/m3/` tại máy nguồn giữ nguyên; `.gitignore` vẫn bỏ qua dữ liệu thô.
Git attributes ngăn tự chuyển đổi xuống dòng để duy trì SHA256 khi clone qua các hệ điều hành.

## Cách đọc kết quả và giới hạn

NAV chuẩn hóa từ vốn ban đầu bằng 1; tỷ trọng là tỷ lệ 0–1. Dev và Holdout là hai đoạn riêng,
không nối NAV. Combined dùng vendor-adjusted close proxy, VNINDEX là price index;
khác biệt cơ sở giá ảnh hưởng cả return và drawdown. Drawdown đo theo kỳ, phí/slippage bằng 0;
giữ các giới hạn financial vintage/PIT và mark stale trong [báo cáo](../../docs/REPORT_BACKTEST.md).
Final Evaluation vẫn NOT_READY do chưa đủ dữ liệu 2026.
