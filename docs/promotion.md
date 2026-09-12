# Chính sách chuyển đổi và nhập dữ liệu chuẩn

Lệnh `scripts/promote_vnstock.py <run-id-or-path> --policy <json>` tạo một thư mục
`data/canonical/canonical-*/` mới. Lần chạy bị chặn vẫn giữ lỗi trong manifest và dữ
liệu cách ly theo từng dòng. Đầu vào của nhà cung cấp không thay đổi. Ngay cả khi có
một số dòng sạch, `run_canonical` chỉ chấp nhận `status=complete`.

Chính sách ràng buộc `policy_version=1.0`, `envelope_schema_version=1.0.0`, cờ dữ
liệu giả lập, định tuyến, phiên bản SDK và các mã băm trình thu thập đã được rà soát.
Ảnh chụp dữ liệu cũ không nhúng phiên bản schema: kiểm tra vỏ dữ liệu theo hợp đồng
1.0.0 đã khóa, không tự tạo một trường gốc của nhà cung cấp. Mã băm của mã nguồn lịch
sử được đối chiếu với danh sách phê duyệt, không phải mã băm bộ chuyển đổi hiện tại.
Đây là thông tin truy vết, không phải bằng chứng mật mã rằng nhà cung cấp thực sự đã
chạy đoạn mã đó.

Mỗi mục ngữ nghĩa có `status`, `value` và `evidence` không rỗng:

| Mục | Cách xử lý |
|---|---|
| timezone_offset_minutes | Độ lệch UTC có bằng chứng; chuẩn hóa dấu thời gian có múi giờ hoặc gắn múi giờ cho dấu thời gian chưa có |
| price_multiplier | Hệ số dương bắt buộc để quy đổi sang VND/cổ phiếu đã xác minh |
| adjustment_basis | `unadjusted` → chỉ giá gốc; `split_adjusted`/`total_return` → chỉ giá điều chỉnh; `unknown` → không loại nào; `synthetic` chỉ dùng trong bộ thử nghiệm |
| volume_multiplier | Tùy chọn; nếu chưa xác minh thì trả về `null` |
| traded_value_multiplier | Tùy chọn; chỉ ánh xạ `va` khi đã xác minh, nếu không trả về `null` |
| index_multiplier | Hệ số riêng để quy đổi sang điểm chỉ số |
| index_basis | `price`/`total_return`; `synthetic` chỉ dùng trong bộ thử nghiệm |
| index_exchange | Sàn của chỉ số tham chiếu được khai báo rõ |
| availability_policy | Dùng `fetched_at` theo hướng bảo thủ, hoặc dữ liệu tham chiếu cho dấu thời gian lịch sử đã có bằng chứng |

Dữ liệu tham chiếu dùng JSONL; mỗi `references.<table>` có đường dẫn tương đối so với
chính sách, `sha256` và bằng chứng. Bắt buộc có `securities`/`calendar`; `actions`/`rates`
và `observations` là tùy chọn. Dữ liệu tham chiếu giữ `source`/`fetched_at`; các dòng
nhận `data_version` mới. Quan sát phải duy nhất theo `(kind,symbol,trade_date)` và có
`available_at`, `trading_status`. Nếu không có bằng chứng trạng thái, dùng `unknown`.
Một thanh giá không chứng minh giao dịch bình thường. Lịch thật cần `available_at`.
Định danh tạm thời có thể được kiểm tra nhưng không đủ điều kiện sử dụng. Danh sách
niêm yết hiện tại không bao giờ tự động tạo các khoảng lịch sử.

Kiểm tra bao gồm mã băm cấu hình, mã băm của từng file gốc, kế hoạch công việc chính
xác, nguồn/SDK, dấu thời gian, các cột trong vỏ/bản ghi, số lượng và giới hạn đường
dẫn. Dữ liệu tham chiếu được băm trước khi ghép theo thời gian. Bộ phân tích từ chối
ngày ngoài phạm vi và định danh mơ hồ. Kiểm soát chất lượng thực thi schema, kiểm tra
trùng lặp, OHLC, vòng đời, lịch và thời điểm khả dụng. Con trỏ bằng chứng phải dẫn tới
nguồn đã được rà soát thực tế; một chuỗi ghi “đã xác minh” không phải bằng chứng. Ví
dụ KBS được chủ ý giữ ở trạng thái chưa giải quyết. Chính sách cho bộ thử nghiệm ngoại
tuyến không bao giờ mở điều kiện nghiệm thu thử nghiệm thật.

## Phục hồi đúng từng byte

Lỗi toàn vẹn không bao giờ làm thay đổi mã băm kỳ vọng. Lệnh
`scripts/recover_vendor_snapshot.py <vendor-id> --policy <policy>` đối chiếu dữ liệu
gốc và các ứng viên trong bộ nhớ đệm làm việc của SDK với mã băm manifest ban đầu.
Chỉ các byte khớp hoàn toàn mới được sao chép vào một lần chạy `vendor-recovered` MỚI,
đồng thời ghi lại mã băm manifest, ID lần chạy gốc và đường dẫn ứng viên. Công cụ kiểm
tra đầy đủ metadata phục hồi theo chính sách đã rà soát. Không có yêu cầu API, tuần
tự hóa lại, ghi đè dữ liệu gốc hay xóa file. Thiếu byte khớp chính xác sẽ gây lỗi; bộ
nhớ đệm chưa kiểm tra không bao giờ được tin cậy. Đây là bản sao phục hồi, không phải
tiếp tục lần chạy hay thu thập mới. Nó khôi phục tính toàn vẹn lưu trữ, không bổ sung
bằng chứng ngữ nghĩa.
