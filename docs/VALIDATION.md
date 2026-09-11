# Bằng chứng kiểm tra - 11/09/2026

## Core

Lệnh: `python -m unittest discover -s tests -v`.

**27/27 tests đạt**, lần chạy cuối: 29.603 giây. Bao gồm tính tay, NA/constant price, beta=1, thiếu lịch sử, tách mã, dữ liệu khả dụng trễ, append tương lai, duplicate/OHLC/temporal FK, metadata overlap, đổi đơn vị, download/resume/hash tamper, HTTP 429/403/pagination/page-limit/response-size, SDK không dùng count=100 và SDK worker chạy trong thư mục staging.

`python -m compileall -q src scripts run.py` thành công. Test tích hợp HTTP chạy với server loopback, không phụ thuộc nhà cung cấp. Test dùng thư mục tạm hệ điều hành; sandbox Windows ban đầu chặn quyền truy cập, sau đó chạy ngoài sandbox thành công. Đây chưa phải xác nhận chạy trên máy đồng đội.

## Demo end-to-end

Lệnh: `python run.py run --config configs/demo.json`.

Run sample lưu tại `data/runs/run-0eae8bdb56ab/manifest.json`, status `complete`, synthetic `true`:

| Bảng/đầu ra | Số dòng |
|---|---:|
| securities | 12 |
| prices_daily | 4.692 |
| benchmark_daily | 391 |
| trading_calendar | 782 (hai sàn giả lập) |
| risk_free_rate | 1 |
| corporate_actions | 0 |
| feature monthly | 216 |
| feature eligible | 84 |
| missing sessions | 0 trong lịch giả lập |

Khoảng sample 01/01/2024–30/06/2025. Không đại diện dữ liệu thật, không đạt yêu cầu scope M1. Data_version thay đổi ở run mới; số lượng với cùng fixture không đổi.

## Thử nguồn thực tế

Đã cài Vnstock 4.0.6 cùng dependencies trong `.venv` của SourceCode, xuất `requirements-vnstock.lock.txt`. Đã đối chiếu code SDK đang cài để xác minh `Market`/`Reference`, source KBS, `count` và xử lý đơn vị.

Run sau khi sửa giới hạn count lưu tại `data/vendor/vendor-26f2e2ce615c/manifest.json`, status `complete`, synthetic `false`:

| Job | Dòng nguồn trả về | Phạm vi quan sát |
|---|---:|---|
| Listing | 3.415 | Gồm nhiều loại tài sản, không phải 3.415 cổ phiếu HOSE/HNX |
| FPT | 20 | 03/08/2026–28/08/2026 |
| VNM | 20 | 03/08/2026–28/08/2026 |
| PVS | 20 | 03/08/2026–28/08/2026 |
| VNINDEX | 20 | 03/08/2026–28/08/2026 |

Request là 01/08/2026–31/08/2026. Nguồn không trả ngày 31/08 trong sample; chưa kết luận lý do khi chưa có lịch phiên đối chiếu. Tải thành công không đồng nghĩa coverage đầy đủ.

Listing quan sát được có 1.524 dòng loại stock: HOSE 405, HNX 299, UPCOM 820. Đây là danh mục nguồn trả tại thời điểm tải, **không chứng minh 704 mã HOSE/HNX đều đủ 5 năm hoặc bao gồm mã đã hủy niêm yết**.

Equity có columns time/open/high/low/close/volume/va; VNINDEX có OHLCV. `sdk_metadata.source=KBS`. Code KBS 4.0.6 chia OHLC cổ phiếu cho 1.000 trước khi trả DataFrame, giữ index theo điểm. Trường `va` được giữ nguyên; chưa xác minh đầy đủ phạm vi/đơn vị với nguồn nên chưa tự map thành traded_value. Chưa có bằng chứng adjustment methodology hay raw price riêng.

Lần thử trong sandbox bị `PermissionError` khi dependency muốn tạo `C:\Users\ASUS\.vnstock`; sau khi cấp quyền chạy ngoài sandbox, tải được sample. Không cần cung cấp API key trong lần thử này. Không coi đây là cam kết API luôn miễn xác thực.

SDK còn tự sinh file onboarding `AGENTS.md` tại working directory. Bộ nền đã thay file ngoài ý muốn ở root bằng quy tắc project và chuyển cwd của worker vào thư mục staging để tránh ảnh hưởng code root trong những lần gọi sau.

## Chưa xác minh hoặc chưa triển khai

Audit corporate actions và adjusted/raw, lịch chính thức, historical identities/delistings, 300 mã/5 năm, tải lại nhiều ngày để đo revision, hiệu năng full dataset, triển khai ba mô hình/PCA/stability, backtest kế toán, dashboard và chạy máy khác.

Core và source collector đều có bằng chứng chạy; việc chuyển vendor sample thành canonical nghiên cứu vẫn cần mapping và dữ liệu bổ sung. Không có kết luận lợi nhuận/alpha trong lần bàn giao này.
