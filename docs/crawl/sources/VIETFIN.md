# Source Note — VietFin

## 1. Trạng thái vòng đời (Lifecycle status)

```text
ACCESS_TESTED
```

Tài liệu công khai, repository và package metadata của VietFin truy cập được không cần đăng nhập. Tuy nhiên, request dữ liệu trực tiếp tới provider mặc định TCBS gặp Cloudflare managed challenge trong lần kiểm tra ngày 2026-09-16. Theo access rules, path này được ghi `BLOCKED` và không được thử vượt qua. Vì chưa có response live hợp lệ cho bốn mã yêu cầu, lifecycle chưa đạt `SEMANTICS_VERIFIED`. `VietFinSource.verification_status` vẫn là `DISCOVERED`; không có adapter nào được sửa.

## 2. Phạm vi và ngày khám phá (Discovery scope and date)

- Ngày discovery: `2026-09-16` (`Asia/Saigon`).
- Phiên bản công khai được quan sát: VietFin `0.2.0`, phát hành trên PyPI ngày 2024-04-22 và được đánh dấu Development Status `Alpha`.
- Exact symbol set: `FPT` (HOSE), `VNM` (HOSE), `PVS` (HNX), `ACV` (UPCOM). Không dùng replacement.
- Evidence chính: tài liệu VietFin/Read the Docs, repository công khai `vietfin/vietfin`, PyPI, và một lần access test giới hạn tới các route TCBS được chính source VietFin công bố.
- Không cài package, không chạy VietFin, không tải lịch sử, không inspect Vnstock và không crawl dataset.
- Cần phân biệt rõ: VietFin là open-source client/wrapper; dữ liệu thực tế đến từ các provider như TCBS, SSI, DNSE và CafeF. License của client không tự động cấp quyền dùng dữ liệu provider.

## 3. Quyền sở hữu / Truy cập / Quyền hạn (Ownership / access / rights)

| Hạng mục | Quan sát | Kết quả |
|---|---|---|
| Code VietFin | Repository GitHub công khai và package PyPI; Apache-2.0 | Xác minh truy cập code công khai |
| Mục đích sử dụng | README nêu rõ dành cho sử dụng cá nhân, nghiên cứu và giáo dục | Áp dụng cho client, không phải giấy phép dữ liệu provider |
| Quan hệ với nhà cung cấp | README ghi rõ VietFin không liên kết, bảo trợ hay kiểm duyệt bởi các công ty provider | Chưa xác lập ủy quyền từ nhà cung cấp |
| Quyền sử dụng dữ liệu | README chỉ dẫn rõ người dùng đến điều khoản của từng provider | `NOT_VERIFIED` |
| Đăng nhập/Trả phí | Tài liệu, repository và PyPI không cần đăng nhập/trả phí để đọc | Truy cập tài liệu công khai |
| Nhà cung cấp mặc định live | Các route GET TCBS công bố trả về Cloudflare managed challenge khi kiểm tra truy cập giới hạn | `BLOCKED`; dừng đường dẫn |
| Quyền tự động hóa | Apache-2.0 chỉ bao gồm code; không có chính sách nhà cung cấp được duyệt nào cho phép thu thập dữ liệu tự động | `NOT_VERIFIED` |
| Giới hạn tần suất (Rate limits) | Không có tài liệu trong các trang kiểm tra; không thực hiện kiểm thử | UNKNOWN |

Phân loại quyền hạn: `NOT_VERIFIED`. Phân loại truy cập là một phần (partial): tài liệu công khai sẵn có, nhưng đường dẫn dữ liệu live TCBS dự định bị `BLOCKED` trong môi trường quan sát.

## 4. Định danh chứng khoán (Security identity)

VietFin mô tả `equity.profile()` với TCBS là mặc định và một model profile đã chuẩn hóa. Ví dụ VNM công khai hiển thị kết quả chuẩn hóa cùng với các key provider raw và provenance nhà cung cấp.

| Nhãn/Key nguồn | Ý nghĩa được bằng chứng hỗ trợ | Mã mẫu | Giá trị mẫu | Ứng viên Canonical | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|---|---|
| `symbol` chuẩn hóa; `ticker` raw | Ticker yêu cầu/hiện tại | VNM | `VNM` | `ticker` | Profile reference và ví dụ Basic Response công khai thống nhất | HIGH |
| `legal_name` chuẩn hóa; `companyName` raw | Tên pháp lý công ty | VNM | `Công ty Cổ phần Sữa Việt Nam` | `company_name` | Model chuẩn hóa rõ ràng và mẫu response raw | HIGH |
| `name` chuẩn hóa; `shortName` raw | Tên viết tắt/thông dụng công ty | VNM | `VINAMILK` | Chỉ dành cho alias RAW | Model profile và mẫu rõ ràng | HIGH |
| `exchange` chuẩn hóa/raw | Sàn giao dịch hiện tại nơi mã niêm yết | VNM | `HOSE` | `exchange` | Định nghĩa profile và mẫu raw rõ ràng | HIGH |
| `industry` chuẩn hóa/raw | Phân ngành của nhà cung cấp | VNM | `Thực phẩm và đồ uống` | `industry` | Định nghĩa profile và mẫu raw rõ ràng | HIGH |
| `industryID` raw và các ID ngành liên quan | Mã định danh phân loại của nhà cung cấp | VNM | `218` cho `industryID` trong mẫu công bố | provider taxonomy provenance | Mẫu raw công khai; thiếu định nghĩa phân cấp | MEDIUM |

Chưa xác minh / Không tìm thấy:

- `provider_security_id`: mẫu profile raw có `id: null`; `code` trong ví dụ tìm kiếm SSI riêng biệt giống như mã đăng ký kinh doanh và chưa được xác minh là ID chứng khoán.
- `sector`: không có trường sector riêng biệt nào được xác minh.
- `listing_date`, `delisting_date`, `listing_status`: không có trong model profile chuẩn hóa được kiểm tra.
- `ticker_history`, `exchange_history`: không tìm thấy.
- Bằng chứng profile VNM hiện tại không được dùng để suy ra định danh lịch sử.
- Xác minh profile live cho FPT, PVS và ACV bị `BLOCKED`; cùng các route profile TCBS cho cả 4 mã yêu cầu đều gặp managed challenge.

## 5. Cổ phiếu / Cấu trúc vốn (Shares / capital structure)

Trạng thái:

```text
CURRENT_SNAPSHOT_ONLY
```

Ví dụ profile VNM raw được công bố chứa `outstandingShare: 2090.0` và `issueShare: 2090.0`. Đây chỉ là các ứng viên snapshot profile hiện tại. Tài liệu VietFin không định nghĩa đơn vị, ngày hiệu lực, ngày công bố hay tính sẵn có PIT của chúng. Không tìm thấy lệnh lịch sử cổ phiếu được chuẩn hóa, chuỗi lịch sử số lượng cổ phiếu hay mốc thời gian biến động vốn chính xác.

| Trường nguồn | Ý nghĩa ứng viên | Mẫu | Mục tiêu Canonical | Kết quả | Độ tin cậy |
|---|---|---|---|---|---|
| `outstandingShare` raw | Snapshot cổ phiếu đang lưu hành hiện tại | VNM `2090.0` | `outstanding_shares` | Tìm thấy, đơn vị/thời gian chưa rõ; không ánh xạ | LOW |
| `issueShare` raw | Snapshot cổ phiếu phát hành hiện tại | VNM `2090.0` | `issued_shares` | Tìm thấy, đơn vị/thời gian chưa rõ; không ánh xạ | LOW |
| `listed_shares` | Không tìm thấy trong model/docs VietFin được kiểm tra | — | `listed_shares` | NOT_FOUND | — |
| `treasury_shares` | Không tìm thấy | — | `treasury_shares` | NOT_FOUND | — |
| Số liệu lịch sử | Không tìm thấy lệnh/model nào | — | `shares_history` | HISTORICAL_UNAVAILABLE | — |

Không được coi `issueShare == outstandingShare` theo nghĩa tổng quát, không suy treasury shares bằng phép trừ, và không backfill snapshot hiện tại về lịch sử. Vì chỉ có ứng viên snapshot VNM trong tài liệu và route live bị block, các hạng mục LOW này nằm trong unresolved mappings.

## 6. Dữ liệu thị trường hàng ngày (Daily market data)

VietFin mô tả `equity.price.historical()` với các nhà cung cấp TCBS, SSI và DNSE. Model dữ liệu chuẩn hóa hiển thị rõ ràng `date`, `open`, `high`, `low`, `close`, `volume`. Các ví dụ công khai hiển thị bản ghi theo ngày của VNM và so sánh 5 quan sát khối lượng FPT trên 3 nhà cung cấp. Các quan sát này xác minh tính sẵn có của trường và provenance nhà cung cấp, nhưng không định nghĩa rõ ràng đơn vị nguồn hay cơ sở điều chỉnh (adjustment basis).

| Trường nguồn | Ý nghĩa | Đơn vị nguồn | Mục tiêu Canonical | Chuyển đổi (Transform) | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|---|---|
| `date` | Ngày của nến ngày | calendar date | `trade_date` | Parse dạng ngày; ngữ nghĩa múi giờ chưa giải quyết | Model reference rõ ràng & các ví dụ VNM/FPT | HIGH |
| `open` | Giá mở cửa nến | UNKNOWN | `raw_open` hoặc `adj_open` không có trong schema | Không ánh xạ cho đến khi xác minh đơn vị và basis | Chỉ có nhãn reference rõ ràng | LOW |
| `high` | Giá cao nhất nến | UNKNOWN | `raw_high` | Không ánh xạ cho đến khi xác minh đơn vị và basis | Chỉ có nhãn reference rõ ràng | LOW |
| `low` | Giá thấp nhất nến | UNKNOWN | `raw_low` | Không ánh xạ cho đến khi xác minh đơn vị và basis | Chỉ có nhãn reference rõ ràng | LOW |
| `close` | Giá đóng cửa nến | UNKNOWN | `raw_close` hoặc `adj_close` | Không ánh xạ cho đến khi xác minh đơn vị và basis | Chỉ có nhãn reference rõ ràng | LOW |
| `volume` | Khối lượng giao dịch nến | UNKNOWN | `volume` | Không tự coi là cổ phiếu cho đến khi nhà cung cấp định nghĩa/UI khớp | Nhãn rõ ràng và giá trị FPT trên 3 provider; thiếu đơn vị | LOW |

Các trường bắt buộc không có trong model lịch sử được kiểm tra:

- `reference_price`, `ceiling_price`, `floor_price`;
- `traded_value`, `trading_status`;
- `matched_volume`, `matched_value`, `put_through_volume`, `put_through_value`.

Bảng so sánh FPT công bố cũng chứng minh khối lượng TCBS lệch nhẹ so với SSI/DNSE vào cùng các ngày. VietFin không đưa ra tài liệu nào giải thích sự khác biệt đó là do lô lẻ, khớp lệnh, thỏa thuận, điều chỉnh hay chính sách đưa vào dữ liệu khác. Không có chuỗi dữ liệu nhà cung cấp nào được đưa lên làm canonical volume của DELTA chỉ dựa vào so sánh này.

Bằng chứng theo mã:

| Mã | Quan sát |
|---|---|
| FPT | Hướng dẫn sử dụng chính thức hiển thị 5 ngày khối lượng cho TCBS, DNSE và SSI; tính sẵn có của trường PARTIAL, đơn vị/chính sách gộp chưa giải quyết |
| VNM | Hướng dẫn chính thức hiển thị OHLCV chuẩn hóa và đoạn dữ liệu TCBS raw cho truy vấn mặc định 60 ngày; tính sẵn có PARTIAL |
| PVS | Đường dẫn request nhà cung cấp mặc định live bị BLOCKED trước khi thu được payload hợp lệ |
| ACV | Đường dẫn request nhà cung cấp mặc định live bị BLOCKED trước khi thu được payload hợp lệ |

## 7. Cơ sở giá (Price basis)

```text
UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET
```

Cả tài liệu lịch sử giá lẫn các ví dụ đều không dán nhãn giá là chưa điều chỉnh (unadjusted), nhà cung cấp tự điều chỉnh (vendor-adjusted), điều chỉnh chia tách (split-adjusted) hay tổng lợi nhuận (total-return). Các ví dụ VNM raw và chuẩn hóa hiển thị giá trị nhà cung cấp nhưng không có định nghĩa điều chỉnh. Không có hệ số nhân nào được duyệt: giá trị hiển thị không phải là bằng chứng cho đơn vị VNĐ/cổ phiếu, và so sánh số học không thay thế được định nghĩa rõ ràng từ nhà cung cấp/UI.

## 8. Thời gian / Múi giờ / Độ sẵn sàng (Time / timezone / availability)

- Đầu vào `start_date` và `end_date` được ghi dưới dạng `YYYY-MM-DD`; mặc định là ngày hiện tại và 60 ngày trước đó.
- Trường `date` thị trường chuẩn hóa là một ngày, không có múi giờ sàn rõ ràng.
- `extra.command_run_at` của VietFin hiển thị với `+00:00` trong các ví dụ công khai và chỉ phù hợp làm client execution/fetch provenance, không phải thời điểm công bố của nguồn.
- Code nguồn lịch sử TCBS chuyển đổi datetime ngày kết thúc chưa có múi giờ sang epoch bằng `datetime.timestamp()`. Do đó mốc thời gian hiệu lực phụ thuộc vào môi trường runtime trừ khi được kiểm soát; ngữ nghĩa ranh giới nhà cung cấp chưa được giải quyết.
- Ngày sự kiện doanh nghiệp được mô tả dưới dạng datetime, nhưng múi giờ và ngữ nghĩa cuối ngày chưa được định nghĩa.
- Báo cáo tài chính chỉ hiển thị nhãn năm/quý tài chính; không tìm thấy thời điểm công bố hay ngữ nghĩa available-at.
- `fetched_at` cho adapter tương lai phải được DELTA tự ghi độc lập; không nhầm lẫn với thời điểm công bố báo cáo.

## 9. Quyền mua & Cổ tức / Hành động doanh nghiệp (Corporate actions)

VietFin hiển thị 2 lệnh TCBS liên quan:

1. `equity.calendar.events(symbol, limit=100)` cho lịch sử sự kiện công ty.
2. `equity.fundamental.dividends(symbol, limit=100)` cho lịch sử cổ tức.

| Trường nguồn | Ý nghĩa ứng viên | Ứng viên Canonical | Bằng chứng / Kết quả | Độ tin cậy |
|---|---|---|---|---|
| `event_code` | Mã sự kiện của nhà cung cấp | `event_id` provenance | Định nghĩa reference rõ ràng | HIGH |
| `event_name`, `event_desc` | Loại/tên sự kiện và mô tả | Ứng viên `event_type` / mô tả raw | Định nghĩa reference rõ ràng; ánh xạ sang enum canonical chưa giải quyết | MEDIUM |
| `date_notify` | Ngày thông báo | Ứng viên `announcement_date` | Định nghĩa reference rõ ràng | HIGH |
| `date_execute` | Ngày thực thi sự kiện | Ứng viên `effective_date` | Nhãn rõ ràng; ngữ nghĩa từng sự kiện cụ thể chưa giải quyết | MEDIUM |
| `date_register` | Ngày đăng ký | Ứng viên `record_date` | Định nghĩa reference rõ ràng | HIGH |
| `date_ex_right` | Ngày GDKHQ | Ứng viên `ex_date` | Định nghĩa reference rõ ràng | HIGH |
| `dividend_type` | Cổ tức `cash` hoặc `stock` | Phân loại phụ sự kiện | Model cổ tức rõ ràng | HIGH |
| `payment_date` | Ngày thanh toán cổ tức | `payment_date` | Model cổ tức rõ ràng | HIGH |
| `cash_dividend_percentage` | Chưa rõ trong tài liệu của chính VietFin | Không | Docs nêu rõ mô tả chưa xác định | LOW |

FPT là ví dụ cổ tức được mô tả trong tài liệu, nhưng không có dòng/giá trị sự kiện cụ thể nào được công bố trên trang kiểm tra và route live bị block. Do đó mức độ bao phủ sự kiện FPT là PARTIAL, không phải VERIFIED. Tỷ lệ quyền mua, giá phát hành, chuẩn hóa tỷ lệ cổ phiếu thưởng/cổ tức, tài liệu/tham chiếu nguồn và ngữ nghĩa sửa đổi không được tìm thấy. Không có hệ số điều chỉnh nào được tính toán.

## 10. Báo cáo tài chính (Financial statements)

Tính sẵn có được VietFin ghi nhận trong tài liệu:

- Các kỳ Quý và Năm.
- Báo cáo kết quả kinh doanh, Bảng cân đối kế toán và Báo cáo lưu chuyển tiền tệ.
- Các nhà cung cấp TCBS và SSI cho cả 3 báo cáo.
- Cấu trúc request TCBS: GET `/tcanalysis/v1/finance/{symbol}/{incomestatement|balancesheet|cashflow}` với các tham số không bảo mật `yearly=0|1` và `isAll=true`.

Model chuẩn hóa:

| Trường | Kết quả | Độ sẵn sàng Canonical | Độ tin cậy |
|---|---|---|---|
| `fiscal_year` | Trường model TCBS rõ ràng | Ứng viên `fiscal_year` | HIGH |
| `fiscal_quarter` | Trường model TCBS rõ ràng | Ứng viên `fiscal_quarter` | HIGH |
| `period` | Người dùng chọn `annual` hoặc `quarter`, được thêm bởi client | Query provenance, không phải ranh giới kỳ | HIGH |
| `items` | Tên chỉ tiêu riêng của nhà cung cấp | Nhãn chỉ tiêu RAW | HIGH |
| `values` | Giá trị chỉ tiêu riêng của nhà cung cấp | Giá trị RAW | HIGH |
| `symbol` | Ticker yêu cầu | ticker provenance | HIGH |
| `fiscal_period` SSI | Nhãn như năm hoặc `Q1 2021` | Ứng viên nhãn kỳ | HIGH |

Metadata quan trọng không có trong model chuẩn hóa được mô tả:

- `provider_report_id`, `period_start`, `period_end`;
- Phạm vi hợp nhất vs công ty mẹ;
- `published_at`, ứng viên `available_at` canonical;
- Trạng thái kiểm toán/soát xét;
- Định danh sửa đổi/điều chỉnh lại;
- Đơn vị tiền tệ và quy mô đơn vị (`unit_scale`).

VietFin cảnh báo rõ ràng rằng các chỉ tiêu, nhãn và giá trị báo cáo thay đổi theo từng nhà cung cấp. Vì không thu được response live hợp lệ nào cho FPT/VNM/PVS/ACV, các ứng viên raw-fact yêu cầu không được đưa lên riêng lẻ. Các chỉ tiêu Kết quả kinh doanh, Cân đối kế toán và Lưu chuyển tiền tệ thường được mở qua `items`/`values` động, nhưng tính sẵn có và ngữ nghĩa của doanh nghiệp, nợ, TSCĐ, dòng tiền, capex, EPS và cổ phiếu bình quân vẫn là NOT_CHECKED cho tập mã yêu cầu. Đặc biệt, nợ phải trả không được ánh xạ thành nợ vay, và snapshot cổ phiếu cuối kỳ không được thay thế cổ phiếu bình quân.

Ngữ nghĩa khoảng thời gian (Duration semantics):

- Kết quả kinh doanh Q2/Q3: `UNKNOWN — DO NOT MAP YET`.
- Lưu chuyển tiền tệ Q2/Q3: `UNKNOWN — DO NOT MAP YET`.

Bộ chọn `period="quarter"` chỉ chứng minh độ mịn truy vấn; không chứng minh dữ liệu fact là quý độc lập hay lũy kế từ đầu năm. Không sử dụng suy đoán số học.

## 11. Chỉ số Benchmark / Lịch giao dịch (Benchmark / trading-calendar availability)

| Domain | Trạng thái | Quan sát | Độ tin cậy |
|---|---|---|---|
| Mức chỉ số VNINDEX lịch sử | AVAILABLE | VietFin mô tả `index.price.historical()` và nêu hỗ trợ TCBS/DNSE bao gồm VNINDEX; các trường chuẩn hóa là nến chỉ số dạng OHLCV | HIGH cho tính sẵn có; ngữ nghĩa/đơn vị chưa ánh xạ sâu |
| Lịch giao dịch sàn HOSE/HNX/UPCOM rõ ràng | NOT_FOUND | Không thấy lệnh lịch sàn giao dịch/ngày nghỉ/phiên nào trong bảng thành phần triển khai | MEDIUM |

Không có request VNINDEX live nào được thực hiện sau khi ranh giới truy cập nhà cung cấp xuất hiện. Lịch sự kiện công ty không phải lịch giao dịch sàn.

## 12. Request / Phân trang / Phản ứng Rate (Request / pagination / rate behavior)

| Đường dẫn bằng chứng | Trạng thái công khai | Phương thức / host / path | Tham số quan trọng (không bảo mật) | Content type | Phân trang / Khoảng ngày / Thứ tự | Dấu thời gian / Hành vi truy cập |
|---|---|---|---|---|---|---|
| Các trang VietFin Read the Docs | Công khai; không cần đăng nhập/trả phí | GET `vietfin.readthedocs.io/...` | đường dẫn trang | `text/html` | Tài liệu tĩnh; N/A | Truy cập bình thường |
| Repository/Code GitHub | Công khai; không cần đăng nhập để đọc | GET `github.com/vietfin/vietfin/...` | branch/path | `text/html` | Điều hướng repository | Truy cập bình thường |
| Trang PyPI `vietfin` | Công khai | GET `pypi.org/project/vietfin/` | path phiên bản | `text/html` | Metadata phát hành | Truy cập bình thường |
| Profile TCBS (theo công bố VietFin) | Dự định công khai; truy cập live bị block | GET `apipubaws.tcbs.com.vn/tcanalysis/v1/company/{symbol}/overview` và `/ticker/{symbol}/overview` | chỉ cần đúng ticker | Dự kiến JSON; quan sát thấy Cloudflare HTML challenge | Không phân trang | Quan sát thấy managed challenge cho FPT/VNM/PVS/ACV; dừng lại |
| Lịch sử ngày TCBS (từ code VietFin) | Không request lại sau ranh giới | GET `apipubaws.tcbs.com.vn/stock-insight/v2/stock/bars-long-term` | `ticker`, `type=stock`, `resolution=D`, `to`, `countBack` | Dự kiến JSON | Comment trong code ghi tối đa 365 ngày count-back mỗi chunk; client lọc ngày chuẩn hóa bao hàm; raw boundary/order chưa xác minh live | `to` là epoch giây tạo từ datetime chưa múi giờ; múi giờ chưa giải quyết |
| Báo cáo tài chính TCBS (từ code VietFin) | Không request lại sau ranh giới | GET `apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{symbol}/{statement}` | `yearly=0|1`, `isAll=true` | Dự kiến JSON | Không có phân trang trong tài liệu; lấy tất cả các dòng | Hành vi live bị BLOCKED/không quan sát được |
| Sự kiện/Cổ tức TCBS | Được mô tả, không request live sau ranh giới | Route GET có sẵn trong bản triển khai client công khai | `symbol`, `limit` (`0` nghĩa là lấy tất cả) | Dự kiến JSON | Dựa trên limit, mặc định 100; hành vi sắp xếp/khi rỗng chưa xác minh | Không thử lại |

Hành vi client thị trường thấy được trong code nguồn:

- Chỉ chấp nhận khung thời gian daily cho TCBS.
- Request ngày được chia chunk với tối đa 365 ngày count-back mỗi request.
- Client lọc các dòng chuẩn hóa trả về bằng `start_date <= date <= end_date`.
- Dòng dữ liệu rỗng từ upstream dừng vòng lặp; kết quả cuối rỗng đẩy ra `EmptyDataError` chứ không trả về trang rỗng canonical.
- Tính bao hàm API raw, lịch sử thực sự tối đa, size trang, hướng sắp xếp và giới hạn rate chưa được xác minh live.

## 13. Mappings đã xác minh (Verified mappings)

Chỉ có các ánh xạ được hỗ trợ bởi tài liệu/ví dụ VietFin công khai rõ ràng mới sẵn sàng ở giai đoạn này:

| Trường chuẩn hóa VietFin | Ứng viên Canonical | Điều kiện |
|---|---|---|
| `symbol` | `ticker` | Giữ nguyên provenance nhà cung cấp và mã yêu cầu |
| `legal_name` | `company_name` | Chỉ dành cho profile hiện tại |
| `exchange` | `exchange` | Chỉ cho profile hiện tại; không suy lịch sử |
| `industry` | `industry` | Giữ nguyên phân loại/phiên bản nhà cung cấp |
| `date` thị trường | `trade_date` | Chỉ ngày; múi giờ nguồn vẫn được ghi nhận chưa rõ |
| `fiscal_year` tài chính | `fiscal_year` | Chỉ ứng viên metadata |
| `fiscal_quarter` tài chính | `fiscal_quarter` | Chỉ ứng viên metadata |
| `date_notify` | `announcement_date` | Ngày thông báo sự kiện; cần xác minh provenance live trước khi thu thập |
| `date_register` | `record_date` | Vẫn cần đánh giá theo từng sự kiện |
| `date_ex_right` | `ex_date` | Vẫn cần đánh giá theo từng sự kiện |
| `payment_date` cổ tức | `payment_date` | Vẫn cần đánh giá theo từng sự kiện |

Các ánh xạ này là ứng viên ở mức độ tài liệu. Vì truy cập dữ liệu live bị block, chúng **không cho phép** thực hiện SOURCE_SMOKE.

## 14. Mappings chưa rõ / bị chặn (Unknown / blocked mappings)

- Payload live cho cả 4 mã yêu cầu: `BLOCKED` tại Cloudflare managed challenge của TCBS.
- Quyền tự động hóa/dữ liệu nhà cung cấp: `NOT_VERIFIED`.
- ID chứng khoán nhà cung cấp, sector, niêm yết/hủy niêm yết/trạng thái và lịch sử định danh: không tìm thấy hoặc chưa giải quyết.
- `outstandingShare`, `issueShare`: chỉ là ứng viên hiện tại; đơn vị/thời gian hiệu lực/công bố chưa rõ.
- Lịch sử số lượng cổ phiếu: không có trong giao diện mô tả.
- Đơn vị/hệ số nhân OHLC và volume: LOW; không ánh xạ.
- `reference_price`, `ceiling_price`, `floor_price`, `traded_value`, `trading_status`, các trường khớp lệnh/thỏa thuận: không tìm thấy trong model lịch sử.
- Price basis: `UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET`.
- Loại sự kiện doanh nghiệp canonical, số tiền tiền mặt/tỷ lệ, tỷ lệ cổ phiếu thưởng/cổ tức, điều khoản quyền mua, giá phát hành, tài liệu nguồn và bản sửa đổi: chưa giải quyết.
- Định danh báo cáo tài chính, ranh giới kỳ, phạm vi, thời điểm công bố/PIT, trạng thái kiểm toán, sửa đổi/điều chỉnh lại, đơn vị tiền tệ và quy mô đơn vị: chưa giải quyết.
- Kết quả kinh doanh Q2/Q3: `UNKNOWN — DO NOT MAP YET`.
- Lưu chuyển tiền tệ Q2/Q3: `UNKNOWN — DO NOT MAP YET`.
- EPS cơ bản/suy giảm và cổ phiếu bình quân cơ bản/suy giảm: chưa xác minh.
- Tất cả mục LOW ở trên phải giữ nguyên dạng raw/unmapped và duy trì fail closed.

## 15. Vai trò ứng viên theo domain (Candidate role by domain)

| Domain | Tính sẵn có | Độ tin cậy | Vai trò ứng viên | Hạn chế chính |
|---|---|---|---|---|
| Chứng khoán (Security) | PARTIAL | MEDIUM | SECONDARY_CANDIDATE | Có ví dụ VNM mạnh trong tài liệu, nhưng phủ live 4 mã bị block và thiếu các trường lịch sử |
| Lịch sử cổ phiếu | CURRENT_SNAPSHOT_ONLY | LOW | NOT_READY | Không có lịch sử; đơn vị/thời gian PIT/hiệu lực của snapshot chưa rõ |
| Thị trường hàng ngày | PARTIAL | LOW | NOT_READY | OHLCV có trong tài liệu, nhưng truy cập live, đơn vị, price basis và các trường QC chưa giải quyết |
| Hành động doanh nghiệp | PARTIAL | MEDIUM | NOT_READY | Model ngày có sẵn, nhưng không có dòng FPT cụ thể, tỷ lệ/điều khoản/nguồn/sửa đổi chưa giải quyết |
| Báo cáo tài chính | PARTIAL | LOW | NOT_READY | Có 3 báo cáo/bộ chọn kỳ, nhưng thiếu PIT, ranh giới, phạm vi, đơn vị và ngữ nghĩa Q2/Q3 |
| Chỉ số Benchmark | AVAILABLE | MEDIUM | SECONDARY_CANDIDATE | Giao diện VNINDEX có trong tài liệu; chưa kiểm tra live và ngữ nghĩa basis/thời gian chưa ánh xạ |
| Lịch giao dịch | NOT_FOUND | MEDIUM | NOT_READY | Không tìm thấy giao diện lịch sàn/ngày nghỉ/phiên giao dịch rõ ràng |

Đây chỉ là đánh giá khả năng làm ứng viên của VietFin, không chọn nguồn sự thật cuối cùng cho DELTA.

## 16. Bù đắp khoảng trống so với CafeF (CafeF gap coverage)

| Khoảng trống chưa giải quyết của CafeF | Kết quả tại VietFin | Trạng thái |
|---|---|---|
| Lịch sử cổ phiếu | Docs VietFin chỉ mở các ứng viên snapshot raw hiện tại, không có chuỗi ngày | CÙNG KHOẢNG TRỐNG (SAME_GAP) |
| Cơ sở giá (Price basis) | Không có định nghĩa rõ ràng raw/adjusted | SAME_GAP |
| Tham chiếu/Trần/Sàn lịch sử | Không có trong model lịch sử được mô tả | SAME_GAP |
| Trạng thái giao dịch lịch sử | Không có | SAME_GAP |
| Ngữ nghĩa tổng khối lượng vs khớp lệnh/thỏa thuận | Chỉ mô tả volume chung chung; khác biệt giữa nhà cung cấp không được giải thích | SAME_GAP |
| Ranh giới kỳ tài chính period_start/period_end | Chỉ có nhãn năm/quý; thiếu ranh giới chính xác | SAME_GAP |
| published_at/available_at tài chính | Không có | SAME_GAP |
| Sửa đổi/Điều chỉnh lại | Không có | SAME_GAP |
| Ngữ nghĩa KQKD Q2/Q3 | `UNKNOWN — DO NOT MAP YET` | SAME_GAP |
| Ngữ nghĩa LCTT Q2/Q3 | `UNKNOWN — DO NOT MAP YET` | SAME_GAP |
| Cổ phiếu bình quân lưu hành | Chưa xác minh | SAME_GAP |
| Quyền tự động hóa | Giấy phép client công khai, nhưng quyền tự động hóa dữ liệu provider chưa được xác minh | SAME_GAP |

Không có khoảng trống nào của CafeF được phân loại là đã lấp đầy. Bảng này không phải là so sánh nguồn cuối cùng.

## 17. Phụ lục bằng chứng (Evidence appendix)

| ID | Nguồn công khai | Quan sát đã dùng |
|---|---|---|
| E1 | `https://github.com/vietfin/vietfin` | Mô tả wrapper công khai, giấy phép Apache-2.0, miễn trừ trách nhiệm nhà cung cấp và cảnh báo quyền hạn |
| E2 | `https://pypi.org/project/vietfin/` | Phiên bản 0.2.0, phân loại alpha, ngày phát hành và package metadata công khai |
| E3 | `https://vietfin.readthedocs.io/en/stable/usage/response.html` | Mẫu raw/chuẩn hóa profile VNM, xuất xứ nhà cung cấp, dấu thời gian UTC lệnh và URL API provenance |
| E4 | `https://vietfin.readthedocs.io/en/stable/usage/historical.html` | Ví dụ OHLCV VNM và so sánh khối lượng FPT giữa các nhà cung cấp |
| E5 | `https://vietfin.readthedocs.io/en/stable/reference/equity/profile.html` | Ý nghĩa các trường profile chuẩn hóa rõ ràng |
| E6 | `https://vietfin.readthedocs.io/en/stable/reference/equity/price/historical.html` | Model OHLCV lịch sử và tham số truy vấn |
| E7 | `https://vietfin.readthedocs.io/en/v0.2.0/reference/equity/calendar/events.html` | Các trường sự kiện doanh nghiệp và hành vi limit |
| E8 | `https://vietfin.readthedocs.io/en/v0.2.0/reference/equity/fundamental/dividends.html` | Ví dụ FPT, các trường cổ tức và ngữ nghĩa tỷ lệ tiền mặt chưa rõ ràng |
| E9 | `https://vietfin.readthedocs.io/en/stable/usage/financial.html` | Hỗ trợ năm/quý, 3 báo cáo và các chỉ tiêu phụ thuộc nhà cung cấp |
| E10 | `https://vietfin.readthedocs.io/en/stable/reference/equity/fundamental/{income,balance,cash}.html` | Các trường tài chính chuẩn hóa và hỗ trợ TCBS/SSI |
| E11 | `https://vietfin.readthedocs.io/en/stable/reference/index/price/historical.html` | Giao diện/model chỉ số lịch sử |
| E12 | `https://github.com/vietfin/vietfin/blob/main/src/vietfin/providers/tcbs/utils/equity_price_historical.py` | Route GET chính xác, tham số, chia chunk, lọc client bao hàm và hành vi khi kết quả rỗng |
| E13 | `https://github.com/vietfin/vietfin/blob/main/src/vietfin/providers/tcbs/utils/equity_profile.py` | Cấu trúc request profile TCBS 2-route chính xác |
| E14 | `https://github.com/vietfin/vietfin/blob/main/src/vietfin/providers/tcbs/utils/equity_fundamental_income.py` | Route GET tài chính, ánh xạ tên báo cáo và tham số năm/quý |
| E15 | Access test giới hạn, 2026-09-16 | Các route GET profile cho FPT/VNM/PVS/ACV trả về managed challenge; không giữ lại dữ liệu challenge, cookie, token hay định danh phiên |

Không có bản ghi bằng chứng nào chứa cookie, access token, header xác thực, giá trị fingerprint hay session ID.

## 18. Trạng thái phê duyệt (Approval state)

| Hạng mục | Trạng thái |
|---|---|
| Vòng đời (Lifecycle) | `ACCESS_TESTED` |
| Truy cập hợp lệ | PARTIAL: docs công khai, đường dẫn dữ liệu live nhà cung cấp mặc định bị `BLOCKED` |
| Ngữ nghĩa thị trường | NOT_READY |
| Lịch sử cổ phiếu | `CURRENT_SNAPSHOT_ONLY` |
| Hành động doanh nghiệp | PARTIAL / NOT_READY |
| Ngữ nghĩa tài chính | NOT_READY |
| Quyền hạn | `NOT_VERIFIED` |
| Cho phép làm Adapter tiếp theo | NO |
| Cho phép làm Source Smoke tiếp theo | NO |

Việc triển khai Adapter bị chặn vì truy cập dữ liệu live hợp lệ chưa được xác lập và không có domain dữ liệu DELTA hữu ích nào có cả đường dẫn request dùng được lẫn đơn vị/ngữ nghĩa được xác minh đủ. Adapter hiện có phải giữ nguyên trạng thái fail-closed. Không cấp trạng thái `PILOT_APPROVED` hay `PRODUCTION_APPROVED`.
