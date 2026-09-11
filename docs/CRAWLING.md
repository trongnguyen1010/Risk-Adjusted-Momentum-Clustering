# Crawl dữ liệu ban đầu và vận hành

## Ba đường nhập dữ liệu

| Đường nhập | Khi sử dụng | Đầu ra |
|---|---|---|
| CSV canonical hoặc CSV có mapping | Đã có file từ nguồn tự thu thập | raw bytes → QC → clean → features |
| HTTP JSON có cấu hình | Có API trả array hoặc `{items,next_cursor}` | raw theo page → QC → clean → features |
| Vnstock SDK | Khảo sát nguồn công khai lần đầu | vendor snapshot, listing hiện tại, OHLCV cổ phiếu/VNINDEX; cần audit tiếp |

Không có nguồn do mentor cấp. Chọn Vnstock để bắt đầu khảo sát; không coi ứng viên này mặc nhiên đáp ứng đầy đủ T1. [Tài liệu Market](https://www.vnstocks.com/docs/vnstock/du-lieu-thi-truong-market-data) mô tả các lệnh lấy equity/index OHLCV; [Reference](https://vnstocks.com/docs/vnstock/tra-cuu-thong-tin-tham-chieu-reference) mô tả danh mục cổ phiếu.

## Bước 1: chạy sample

```powershell
python scripts/generate_demo.py
python run.py run --config configs/demo.json
```

Đọc manifest, một dòng prices/securities/features, và coverage trước khi đổi input. Cách chạy này hoàn toàn offline.

## Bước 2: lấy vendor sample thật

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

Giữ nguyên tham số và code để resume. Mỗi file vendor gồm job, fetched_at, version SDK, columns, records. Tên nguồn routing được ghi theo adapter; các field vendor chưa được xem là `prices_daily`. File raw bất biến; worker viết file tạm riêng trước khi snapshot được lưu.

Nếu worker lỗi, xem job status; thử import `vnstock` trong môi trường vừa cài để kiểm tra thiếu dependency/quyền truy cập. Collector không in stdout/stderr SDK vào manifest vì SDK có thể in thông tin môi trường ngoài ý muốn. Chưa tự đăng ký hoặc cấp API key; tài khoản nếu cần do người dùng quản lý.

## Bước 3: audit trước canonical

DE/QC cần ghi bằng chứng trong `SOURCE_EVALUATION.md`:

1. Kiểm tra columns, first/last day, số dòng và số mã/sàn so với yêu cầu request. Không chỉ tin HTTP 200.
2. Xác minh đơn vị OHLC, volume và traded_value, riêng VNINDEX dùng điểm chỉ số.
3. Chọn ít nhất vài ngày có cổ tức/chia tách để hiểu adjusted bao gồm gì. Nếu chỉ có một chuỗi close chưa rõ nghĩa, giữ staging; không chế thêm raw/adjusted.
4. Bổ sung security master có ID ổn định và khoảng hiệu lực. Listing hiện tại chỉ là danh sách khảo sát, không tự suy ngày niêm yết/delisting quá khứ.
5. Bổ sung lịch giao dịch từ nguồn đã kiểm chứng. Không dùng weekday generator của demo cho dữ liệu thật.
6. Xác minh available_at lịch sử hoặc ghi rõ đây là giả định công bố, ai chấp nhận và phạm vi nghiên cứu. fetched_at chỉ là thời điểm tải hôm nay.
7. Xuất CSV canonical hoặc viết mapping nguồn với tests. Đổi `synthetic=false`, accepted_adjustments đúng loại và nguồn phù hợp. Chạy sample qua QC trước khi mở rộng.

## CSV mapping

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

Chỉ dùng multiplier/basis ví dụ khi có bằng chứng phù hợp với nguồn. Mọi field bắt buộc còn lại cần có trong CSV hoặc defaults hợp lệ; không tự sinh stable ID/available_at/trading_status. Sao chép config demo để có đủ jobs securities, prices, benchmark và calendar rồi thay path/source/mapping.

## HTTP JSON

`configs/http.example.json` là cấu hình mẫu, không trỏ tới nhà cung cấp thật. Endpoint phải HTTPS, ngoại trừ HTTP loopback dùng test. `params` chứa các tham số nguồn hỗ trợ; token truyền qua biến môi trường mà `token_env` chỉ tên, không nằm trong config. `.env` không được tự load.

```powershell
$env:DELTA_DATA_TOKEN = '<token-tren-may-ban>'
python run.py run --config configs/your-source.json
```

Response được hỗ trợ: JSON array một trang, hoặc object `items` array và `next_cursor` scalar/null. Đổi items_key/next_key/cursor_param nếu API dùng tên khác. Không tự hỗ trợ số trang, GraphQL, POST hoặc cấu trúc nested khác: viết provider riêng và tests khi cần.

HTTP dùng timeout 30 giây, tối đa 3 attempts, khoảng cách tối thiểu 2 giây. Retry lỗi mạng và 429/500/502/503/504, có backoff/Retry-After; 401/403 không retry. Nếu server yêu cầu chờ hơn 60 giây, dừng để resume sau. Giới hạn bytes/page và max_pages; cursor lặp gây lỗi. Redirect không được theo để tránh đổi nguồn hoặc chuyển credential ngầm.

Mỗi job trong config là một batch: chia danh sách ticker và khoảng ngày theo giới hạn API đã xác minh. Ghi các tham số đó vào params để manifest truy vết được. Không có bộ chia batch chung cho mọi API vì mỗi nguồn có quy tắc riêng.

## Tải lại, incremental và revision

- Lỗi download: giữ run_id và `--resume`; đọc lại raw đã tải, verify hash; tải trang còn thiếu. Config/CSV/code khác thì từ chối resume.
- Lỗi schema/QC: xem issues + quarantine, sửa mapping hoặc input, tạo **run mới**. Không chỉnh raw.
- Dữ liệu mới: cấu hình khoảng ngày mới, tạo run khác; cần đủ warm-up cho feature. Phiên bản hiện tại **chưa tự merge** run cũ/mới.
- Revision nguồn: tải lại khoảng lịch sử liên quan trong run mới, so checksum và giá quanh sự kiện. Phải phân biệt revision dữ liệu với leakage thuật toán.
- HTTP pagination yêu cầu cursor/thứ tự ổn định. Nếu nguồn thay trang khi có bản ghi mới, chốt cutoff request hoặc tạo run mới; không hứa resume tạo snapshot nhất quán cho mọi nguồn.
- Không có job chạy nền định kỳ hay lệnh thật. Scheduler là phần tùy chọn sau khi dữ liệu đã ổn định.
