# Delta T1 - Phân cụm động lượng điều chỉnh rủi ro

Bộ nền Python cho cổ phiếu HOSE/HNX, dữ liệu cuối ngày và snapshot cuối tháng. Phiên bản 0.1.0 tập trung ingestion, data contract, QC và feature. M2/M3 có ranh giới module và schema; chưa có mô hình đã huấn luyện, backtest hay dashboard hoàn chỉnh.

## Đọc theo thứ tự

1. [Đánh giá các PDF](docs/DOCUMENT_REVIEW.md): phù hợp đến đâu, còn thiếu gì.
2. [Kiến trúc và tổ chức code](docs/ARCHITECTURE.md): luồng xử lý, ownership và điểm mở rộng.
3. [Data contract và quan hệ schema](docs/DATA_CONTRACT.md).
4. [Crawl dữ liệu ban đầu](docs/CRAWLING.md) và [đánh giá nguồn](docs/SOURCE_EVALUATION.md).
5. [Đặc tả feature](docs/FEATURE_SPEC.md), [plan](docs/PLAN.md), [quy tắc phát triển](DEVELOPMENT_RULES.md), [decision log](docs/DECISIONS.md), [changelog](CHANGELOG.md).

## Chạy ngay, không cần API key hay thư viện ngoài

Python 3.11 trở lên. Chạy từ thư mục `SourceCode`:

```powershell
python scripts/generate_demo.py
python run.py run --config configs/demo.json
python -m unittest discover -s tests -v
```

Demo tạo 12 mã `SYN00`–`SYN11`, dữ liệu **giả lập**, trong 18 tháng. Lịch chỉ gồm ngày trong tuần để kiểm thử; không phải lịch giao dịch Việt Nam. Không dùng sample này để chứng minh M1 hoặc kết luận nghiên cứu.

Nếu máy chưa nhận lệnh `python`, dùng đường dẫn tới Python đã cài thay cho `python`. Core không cần `pip install`. Có thể cài package với `python -m pip install -e .` để dùng CLI `delta`.

Đầu ra nằm ở `data/runs/<run_id>/`:

```text
manifest.json                 # trạng thái, nguồn, cấu hình, hash, môi trường
raw/<job_id>/page-00000.csv    # nguyên bản bytes CSV; HTTP dùng .json
clean/*.jsonl                 # các bảng đã chuẩn hóa
quality/issues.jsonl          # lỗi có rule_id; rỗng khi không có lỗi
quality/quarantine.jsonl      # dòng bị cách ly
quality/coverage.json         # số mã/năm/sàn, phiên thiếu, eligible theo tháng
features/monthly.jsonl        # chỉ tạo khi tải và QC bắt buộc thành công
```

CLI in `run_id` và đường dẫn manifest. Mã thoát `0` là luồng dữ liệu hoàn tất; `2` là lỗi tải/QC/config. `complete` không đồng nghĩa đạt M1: xem coverage, nguồn và tiêu chí nghiệm thu riêng.

## Tải thử nguồn công khai

Ứng viên ban đầu: Vnstock Community 4.0.6. Cài riêng để không làm nặng core:

Trên workspace bàn giao, `.venv` đã có SDK và sample thật trong `data/vendor/vendor-26f2e2ce615c`; có thể dùng thẳng lệnh crawler. Các bước cài dưới đây dành cho môi trường mới.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install "vnstock==4.0.6"
.venv\Scripts\python.exe scripts/crawl_vnstock.py --symbols FPT VNM PVS --start 2026-08-01 --end 2026-08-31
```

Bỏ `--symbols` để tải bộ mẫu 12 ticker cấu hình trong script, cùng danh mục niêm yết hiện tại và VNINDEX. Không mặc định các ticker mẫu đại diện đầy đủ thị trường hoặc sàn lịch sử.

Crawler ghi vào `data/vendor/<vendor_run_id>/`, lưu checkpoint, chia khoảng ngày và timeout mỗi tác vụ SDK. **Kết quả ở lớp vendor cần audit trước khi chuyển thành canonical**: chưa tự coi `close` là cả `raw_close` và `adj_close`, chưa gán danh sách mã hiện tại ngược về quá khứ. Xem [hướng dẫn crawl](docs/CRAWLING.md).

Không có tài khoản/nguồn do mentor cấp. Các giả định kỹ thuật ở đây là lựa chọn triển khai của project; các tiêu chí học thuật chưa chốt vẫn ghi trong decision log.

## Tiếp tục và tái lập

```powershell
python run.py run --config configs/demo.json --resume <run_id>
python run.py inspect data/runs/<run_id>/manifest.json
```

Resume chỉ dùng khi config, file CSV và code/schema không đổi; đối chiếu checksum từng raw page. Sửa input/code hoặc kiểm tra revision từ nguồn: tạo run mới. Các run độc lập; chưa tự merge dữ liệu tăng dần. Không ghi đè raw để sửa lỗi.

Các thư mục `data/`, `artifacts/`, `.venv/`, `tmp/` bị loại khỏi Git. Chỉ commit sample giả lập được phép chia sẻ, code, config không có secret và tài liệu. Xem [bằng chứng kiểm thử](docs/VALIDATION.md) để biết phần nào thực sự đã chạy.
