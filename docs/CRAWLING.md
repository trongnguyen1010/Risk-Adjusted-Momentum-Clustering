# Thu thập dữ liệu ban đầu và vận hành

## Ba đường nhập dữ liệu

| Đường nhập | Khi sử dụng | Đầu ra |
|---|---|---|
| CSV chuẩn hoặc CSV có ánh xạ | Đã có file từ nguồn tự thu thập | byte gốc → QC → dữ liệu sạch → đặc trưng |
| HTTP JSON có cấu hình | Có API trả mảng hoặc `{items,next_cursor}` | dữ liệu gốc theo trang → QC → dữ liệu sạch → đặc trưng |
| Vnstock SDK | Khảo sát nguồn công khai lần đầu | ảnh chụp nhà cung cấp, niêm yết hiện tại, OHLCV cổ phiếu/VNINDEX; cần kiểm tra tiếp |

Không có nguồn do mentor cấp. Chọn Vnstock để bắt đầu khảo sát; không coi ứng viên này mặc nhiên đáp ứng đầy đủ T1. [Tài liệu Market](https://www.vnstocks.com/docs/vnstock/du-lieu-thi-truong-market-data) mô tả các lệnh lấy equity/index OHLCV; [Reference](https://vnstocks.com/docs/vnstock/tra-cuu-thong-tin-tham-chieu-reference) mô tả danh mục cổ phiếu.

## Bước 1: chạy mẫu

```powershell
python scripts/generate_demo.py
python run.py run --config configs/demo.json
```

Đọc manifest, một dòng giá/chứng khoán/đặc trưng và báo cáo độ phủ trước khi đổi đầu vào. Cách chạy này hoàn toàn ngoại tuyến.

## Bước 2: lấy mẫu thật từ nhà cung cấp

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-vnstock.lock.txt
.venv\Scripts\python.exe scripts/crawl_vnstock.py --symbols FPT VNM PVS --start 2026-08-01 --end 2026-08-31
```

Lock là snapshot dependencies đã cài ở môi trường Windows/Python 3.12 của lần triển khai; máy/hệ điều hành khác cần resolve và kiểm tra lại. Core không phụ thuộc lock này.

Collector chia mỗi ticker thành khoảng tối đa 180 ngày lịch, thêm VNINDEX và một lần lấy listing. Nghỉ tối thiểu 5 giây giữa các job ở cấu hình mặc định; mỗi job tối đa 3 lần thử và 90 giây/lần. SDK có thể có thêm request nội bộ/hạn mức tài khoản. Nếu bị hạn mức, dừng và resume sau; không đổi proxy/tài khoản để lách hạn mức.

```powershell
.venv\Scripts\python.exe scripts/crawl_vnstock.py --symbols FPT VNM PVS --start 2026-08-01 --end 2026-08-31 --resume <vendor_run_id>
```

Giữ nguyên tham số và mã nguồn để tiếp tục. Mỗi file nhà cung cấp gồm công việc,
`fetched_at`, phiên bản SDK, các cột và bản ghi. Tên nguồn định tuyến được ghi theo bộ
chuyển đổi; các trường nhà cung cấp chưa được xem là `prices_daily`. File gốc bất
biến; tiến trình làm việc ghi file tạm riêng trước khi lưu ảnh chụp.

Nếu tiến trình làm việc lỗi, xem trạng thái công việc; thử nhập `vnstock` trong môi
trường vừa cài để kiểm tra phần phụ thuộc hoặc quyền truy cập bị thiếu. Trình thu thập
không đưa đầu ra chuẩn/đầu ra lỗi của SDK vào manifest vì SDK có thể in thông tin môi
trường ngoài ý muốn. Chưa tự đăng ký hoặc cấp khóa API; tài khoản nếu cần do người dùng quản lý.

## Bước 3: audit trước canonical

DE/QC cần ghi bằng chứng trong `SOURCE_EVALUATION.md`:

1. Kiểm tra các cột, ngày đầu/cuối, số dòng và số mã/sàn so với yêu cầu. Không chỉ tin HTTP 200.
2. Xác minh đơn vị OHLC, volume và traded_value, riêng VNINDEX dùng điểm chỉ số.
3. Chọn ít nhất vài ngày có cổ tức/chia tách để hiểu giá điều chỉnh bao gồm gì. Nếu chỉ có một chuỗi đóng cửa chưa rõ nghĩa, giữ ở vùng trung gian; không chế thêm giá gốc/điều chỉnh.
4. Bổ sung danh mục chứng khoán có ID ổn định và khoảng hiệu lực. Danh sách hiện tại chỉ phục vụ khảo sát, không tự suy ngày niêm yết/hủy niêm yết quá khứ.
5. Bổ sung lịch giao dịch từ nguồn đã kiểm chứng. Không dùng weekday generator của demo cho dữ liệu thật.
6. Xác minh available_at lịch sử hoặc ghi rõ đây là giả định công bố, ai chấp nhận và phạm vi nghiên cứu. fetched_at chỉ là thời điểm tải hôm nay.
7. Xuất CSV chuẩn hoặc viết ánh xạ nguồn kèm kiểm thử. Đổi `synthetic=false`, đặt `accepted_adjustments` đúng loại và nguồn phù hợp. Chạy mẫu qua QC trước khi mở rộng.

## Ánh xạ CSV

Mỗi job đọc một file UTF-8/UTF-8 BOM có header. Ví dụ đoạn config của bảng giá:

```json
{
  "id": "prices_sample",
  "table": "prices_daily",
  "provider": "csv",
  "path": "data/import/prices.csv",
  "source": "ten_nguon_da_xac_minh",
  "mapping": {"trade_date": "date", "adj_close": "adjusted_close"},
  "multipliers": {"adj_close": 1000},
  "defaults": {"adjustment_basis": "split_adjusted"}
}
```

Chỉ dùng hệ số/cơ sở ví dụ khi có bằng chứng phù hợp với nguồn. Mọi trường bắt buộc
còn lại cần có trong CSV hoặc giá trị mặc định hợp lệ; không tự sinh ID ổn định,
`available_at` hay `trading_status`. Sao chép cấu hình demo để có đủ công việc cho
chứng khoán, giá, chỉ số tham chiếu và lịch rồi thay đường dẫn/nguồn/ánh xạ.

## HTTP JSON

`configs/http.example.json` là cấu hình mẫu, không trỏ tới nhà cung cấp thật. Endpoint phải HTTPS, ngoại trừ HTTP loopback dùng test. `params` chứa các tham số nguồn hỗ trợ; token truyền qua biến môi trường mà `token_env` chỉ tên, không nằm trong config. `.env` không được tự load.

```powershell
$env:DELTA_DATA_TOKEN = '<token-tren-may-ban>'
python run.py run --config configs/your-source.json
```

Phản hồi được hỗ trợ: mảng JSON một trang, hoặc đối tượng có mảng `items` và
`next_cursor` là giá trị vô hướng/`null`. Đổi `items_key`/`next_key`/`cursor_param` nếu
API dùng tên khác. Không tự hỗ trợ số trang, GraphQL, POST hoặc cấu trúc lồng nhau
khác: viết trình cung cấp riêng và kiểm thử khi cần.

HTTP dùng timeout 30 giây, tối đa 3 attempts, khoảng cách tối thiểu 2 giây. Retry lỗi mạng và 429/500/502/503/504, có backoff/Retry-After; 401/403 không retry. Nếu server yêu cầu chờ hơn 60 giây, dừng để resume sau. Giới hạn bytes/page và max_pages; cursor lặp gây lỗi. Redirect không được theo để tránh đổi nguồn hoặc chuyển credential ngầm.

Mỗi job trong config là một batch: chia danh sách ticker và khoảng ngày theo giới hạn API đã xác minh. Ghi các tham số đó vào params để manifest truy vết được. Không có bộ chia batch chung cho mọi API vì mỗi nguồn có quy tắc riêng.

## Tải lại, incremental và revision

- Lỗi tải: giữ `run_id` và `--resume`; đọc lại dữ liệu gốc đã tải, kiểm tra mã băm; tải trang còn thiếu. Cấu hình/CSV/mã nguồn khác thì từ chối tiếp tục.
- Lỗi schema/QC: xem vấn đề + dữ liệu cách ly, sửa ánh xạ hoặc đầu vào, tạo **lần chạy mới**. Không chỉnh dữ liệu gốc.
- Dữ liệu mới: cấu hình khoảng ngày mới, tạo lần chạy khác; cần đủ giai đoạn khởi động cho đặc trưng. Phiên bản hiện tại **chưa tự hợp nhất** lần chạy cũ/mới.
- Bản sửa đổi nguồn: tải lại khoảng lịch sử liên quan trong lần chạy mới, so mã băm và giá quanh sự kiện. Phải phân biệt bản sửa đổi dữ liệu với rò rỉ thuật toán.
- HTTP pagination yêu cầu cursor/thứ tự ổn định. Nếu nguồn thay trang khi có bản ghi mới, chốt cutoff request hoặc tạo run mới; không hứa resume tạo snapshot nhất quán cho mọi nguồn.
- Không có job chạy nền định kỳ hay lệnh thật. Scheduler là phần tùy chọn sau khi dữ liệu đã ổn định.
