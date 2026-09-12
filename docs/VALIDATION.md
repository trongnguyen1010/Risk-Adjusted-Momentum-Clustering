# Bằng chứng kiểm tra v0.2 — 12/09/2026

## Kiểm tra bổ sung sau khi Việt hóa báo cáo

Đã sinh `experiment-6436b9f4eb78` bằng mẫu báo cáo tiếng Việt và cấu hình có phần
diễn giải giả định bằng tiếng Việt. Tham số số học và phương pháp giữ nguyên.
Đối chiếu 9 tệp kết quả số với `experiment-68a6c30d4271`: giống nhau từng byte.
Đã xác minh toàn bộ mã băm đầu ra của cả hai lần chạy và kiểm tra cú pháp phần
sinh báo cáo. Không ghi đè báo cáo hay manifest lịch sử. Không chạy lại toàn bộ
44 kiểm thử cho thay đổi ngôn ngữ này; kết quả ở phần dưới là bằng chứng của
đợt triển khai kỹ thuật trước đó.

## Kiểm thử hiện tại

`.venv/Scripts/python.exe -m unittest discover -s tests -v`: **44/44 ĐẠT**, 115,640 giây.
Kiểm thử dùng môi trường riêng của dự án, chạy ngoài sandbox vì sandbox chặn tạo
tệp tạm. Không phụ thuộc API trực tiếp. Bộ cũ 27 kiểm thử được giữ; bổ sung 17 kiểm
thử cho chuyển đổi/dữ liệu tham chiếu/mã băm/phục hồi, định danh và sàn theo thời gian,
QC/thời điểm khả dụng, cơ sở điều chỉnh/khoảng trống/điều kiện hợp lệ, KMeans xác định
và tiền xử lý, hoán vị nhãn, tỷ trọng/chi phí tự cân đối nguồn vốn, độ trễ khớp lệnh,
chỉ tiêu lợi suất/bootstrap và điều kiện mở rộng.

Bản demo lõi: `run-bce4c382f3e5`, trạng thái `complete`, dữ liệu `synthetic`. Thử
nghiệm chuyển đổi xuyên suốt: `canonical-4c043c70287c` → `run-d7e3c24044ab` →
`experiment-9a30d8e60047`, trạng thái `complete`. Có 6 chứng khoán giả lập, 2.346 dòng
giá, 391 phiên chỉ số tham chiếu, 782 dòng lịch, 108 ảnh chụp đặc trưng, 6 tháng nghiên
cứu đủ điều kiện/36 kết quả gán cụm, 106 phiên định giá mô phỏng và 42 tệp kết quả.
Sự kiện doanh nghiệp rỗng theo thiết kế giả lập công khai; không tuyên bố dữ liệu sự
kiện thật đã đầy đủ. Đã xem trực quan biểu đồ NAV/chuyển cụm. Lần chạy dùng cho bản
trình bày cuối là `experiment-68a6c30d4271`, dùng cùng đầu vào sau khi đổi nhãn vạch
trục cụm thành số nguyên. Các byte của chỉ tiêu hiệu quả/hồ sơ cụm/NAV khớp thử nghiệm
trước; đã kiểm tra các biểu đồ cuối. Thay đổi hiển thị này không sửa công thức nghiên cứu.

Kiểm tra toàn vẹn dữ liệu thật: 5/10 file gốc không đạt SHA-256 theo byte sau khi định
dạng thay đổi; cả năm tải trọng trong bộ nhớ đệm có mã băm gốc của lần chạy mới nhất
đã được phục hồi vào `vendor-recovered-fccfaaa2b061` mà không sửa file ban đầu. Kiểm
thử phục hồi chứng minh các byte cũ không đổi và từ chối khi thiếu byte bộ nhớ đệm
khớp chính xác. Lần chuyển đổi `canonical-98a1440ae1eb` đang **BỊ CHẶN** với lỗi
`missing reference: securities`. Không có đặc trưng hay mô phỏng dữ liệu thật nào
được công bố từ lần chạy này.

Bộ lập kế hoạch thử nghiệm `plan-132d8c9bf4c8.json` đã chặn đúng một thử nghiệm giả
lập hoàn tất dù các kiểm tra kỹ thuật về độ phủ/mã băm đều đạt. Không thực hiện thu
thập khoảng 300 mã. Đã chạy `compileall` và `git diff --check`; không có lỗi cú pháp
hay khoảng trắng.

Mọi biểu đồ và giá trị hiệu quả đều là kết quả phát triển trên dữ liệu giả lập, không
phải bằng chứng hiệu quả thị trường hay nghiệm thu M1/M2/M3. Các giới hạn còn lại nằm
trong `research_limitations.md`; trạng thái theo từng giai đoạn nằm trong
`phase_report.md`.

# Bằng chứng lịch sử v0.1 — 11/09/2026

## Phần lõi

Lệnh: `python -m unittest discover -s tests -v`.

**27/27 kiểm thử đạt**, lần chạy cuối: 29,603 giây. Bao gồm tính tay, NA/giá hằng, beta=1, thiếu lịch sử, tách mã, dữ liệu khả dụng trễ, nối dữ liệu tương lai, trùng lặp/OHLC/khóa ngoại theo thời gian, metadata chồng lấn, đổi đơn vị, tải/tiếp tục/can thiệp mã băm, HTTP 429/403/phân trang/giới hạn trang/kích thước phản hồi, SDK không dùng `count=100` và tiến trình SDK chạy trong thư mục trung gian.

`python -m compileall -q src scripts run.py` thành công. Test tích hợp HTTP chạy với server loopback, không phụ thuộc nhà cung cấp. Test dùng thư mục tạm hệ điều hành; sandbox Windows ban đầu chặn quyền truy cập, sau đó chạy ngoài sandbox thành công. Đây chưa phải xác nhận chạy trên máy đồng đội.

## Demo xuyên suốt

Lệnh: `python run.py run --config configs/demo.json`.

Lần chạy mẫu lưu tại `data/runs/run-0eae8bdb56ab/manifest.json`, trạng thái `complete`, `synthetic=true`:

| Bảng/đầu ra | Số dòng |
|---|---:|
| securities | 12 |
| prices_daily | 4.692 |
| benchmark_daily | 391 |
| trading_calendar | 782 (hai sàn giả lập) |
| risk_free_rate | 1 |
| corporate_actions | 0 |
| đặc trưng theo tháng | 216 |
| đặc trưng đủ điều kiện | 84 |
| phiên bị thiếu | 0 trong lịch giả lập |

Khoảng mẫu 01/01/2024–30/06/2025. Không đại diện dữ liệu thật, không đạt phạm vi M1. `data_version` thay đổi ở lần chạy mới; số lượng với cùng bộ thử nghiệm không đổi.

## Thử nguồn thực tế

Đã cài Vnstock 4.0.6 cùng các phần phụ thuộc trong `.venv` của SourceCode, xuất `requirements-vnstock.lock.txt`. Đã đối chiếu mã nguồn SDK đang cài để xác minh `Market`/`Reference`, nguồn KBS, `count` và xử lý đơn vị.

Lần chạy sau khi sửa giới hạn `count` lưu tại `data/vendor/vendor-26f2e2ce615c/manifest.json`, trạng thái `complete`, `synthetic=false`:

| Job | Dòng nguồn trả về | Phạm vi quan sát |
|---|---:|---|
| Listing | 3.415 | Gồm nhiều loại tài sản, không phải 3.415 cổ phiếu HOSE/HNX |
| FPT | 20 | 03/08/2026–28/08/2026 |
| VNM | 20 | 03/08/2026–28/08/2026 |
| PVS | 20 | 03/08/2026–28/08/2026 |
| VNINDEX | 20 | 03/08/2026–28/08/2026 |

Khoảng yêu cầu là 01/08/2026–31/08/2026. Nguồn không trả ngày 31/08 trong mẫu; chưa kết luận lý do khi chưa có lịch phiên đối chiếu. Tải thành công không đồng nghĩa độ phủ đầy đủ.

Listing quan sát được có 1.524 dòng loại stock: HOSE 405, HNX 299, UPCOM 820. Đây là danh mục nguồn trả tại thời điểm tải, **không chứng minh 704 mã HOSE/HNX đều đủ 5 năm hoặc bao gồm mã đã hủy niêm yết**.

Dữ liệu cổ phiếu có các cột `time`/`open`/`high`/`low`/`close`/`volume`/`va`; VNINDEX có OHLCV. `sdk_metadata.source=KBS`. Mã nguồn KBS 4.0.6 chia OHLC cổ phiếu cho 1.000 trước khi trả DataFrame, giữ chỉ số theo điểm. Trường `va` được giữ nguyên; chưa xác minh đầy đủ phạm vi/đơn vị với nguồn nên chưa tự ánh xạ thành `traded_value`. Chưa có bằng chứng về phương pháp điều chỉnh hoặc chuỗi giá gốc riêng.

Lần thử trong sandbox bị `PermissionError` khi phần phụ thuộc muốn tạo `C:\Users\ASUS\.vnstock`; sau khi cấp quyền chạy ngoài sandbox, đã tải được mẫu. Không cần cung cấp khóa API trong lần thử này. Không coi đây là cam kết API luôn miễn xác thực.

SDK còn tự sinh file onboarding `AGENTS.md` tại working directory. Bộ nền đã thay file ngoài ý muốn ở root bằng quy tắc project và chuyển cwd của worker vào thư mục staging để tránh ảnh hưởng code root trong những lần gọi sau.

## Chưa xác minh hoặc chưa triển khai

Kiểm tra sự kiện doanh nghiệp và giá điều chỉnh/gốc, lịch chính thức, định danh/hủy niêm yết lịch sử, 300 mã/5 năm, tải lại nhiều ngày để đo bản sửa đổi, hiệu năng trên toàn bộ dữ liệu, triển khai ba mô hình/PCA/độ ổn định, mô phỏng có hạch toán, bảng điều khiển và chạy trên máy khác.

Phần lõi và trình thu thập nguồn đều có bằng chứng chạy; việc chuyển mẫu nhà cung cấp thành dữ liệu chuẩn cho nghiên cứu vẫn cần ánh xạ và dữ liệu bổ sung. Không có kết luận lợi nhuận/alpha trong lần bàn giao này.
