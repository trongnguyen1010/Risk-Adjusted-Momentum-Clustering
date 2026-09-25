# Source Note — CafeF

## CURRENT ACTIVE MARKET DECISION (post-C8)

- Active market source là CafeF `TradeHistoryNew` cho C8 market foundation.
- `AdjustPrice × 1000` được dùng như `adj_close` với `adjustment_basis=vendor_adjusted`; đây là research-price proxy, không được gọi là split-only hoặc total-return series.
- Source semantics hiện đủ về mặt vận hành cho market-only pipeline đã execute/verify, trong đúng phạm vi contract C8 và các assumptions được version hóa.
- Corporate-action rights/terms vẫn chưa verified; provider rights vẫn `RIGHTS_NOT_VERIFIED`.
- Financial PIT chưa ready và financial features không active.
- Current profile/listing metadata không chứng minh historical identity hoặc final historical universe.

## OLDER DISCOVERY FINDINGS (2026-09-16)

Các mục bên dưới bảo toàn discovery evidence tại thời điểm ghi nhận. Trạng thái và khuyến nghị cũ không được đọc như current post-C8 decision.

### 1. Trạng thái vòng đời tại thời điểm discovery (Lifecycle status)

```text
ACCESS_TESTED
```

CafeF có thể truy cập được thông qua các trang web công khai thông thường và các request do trình duyệt thực hiện. Quá trình khám phá (discovery) này **chưa** đáp ứng tiêu chuẩn `SEMANTICS_VERIFIED`: cơ sở tính giá (price basis), múi giờ (timezone), quyền tự động hóa (automation rights), mốc thời gian lịch sử cổ phiếu, mốc thời gian Point-in-Time (PIT) tài chính, và ngữ nghĩa khoảng thời gian của một số chỉ tiêu tài chính vẫn chưa được giải quyết. Trạng thái `CafeFSource.verification_status` vẫn giữ nguyên là `DISCOVERED`; chưa có code adapter nào thay đổi.

## 2. Phạm vi và ngày khám phá (Discovery scope and date)

- Ngày khám phá: `2026-09-16` (múi giờ máy trạm `Asia/Saigon`).
- Các mã cổ phiếu được kiểm tra, không thay thế: `FPT` (HOSE), `VNM` (HOSE), `PVS` (HNX), và `ACV` (UPCOM).
- Phạm vi: profile công khai, snapshot cổ phiếu hiện tại, mẫu nhỏ thị trường hiện tại/lịch sử, một ví dụ sự kiện doanh nghiệp của FPT, tính sẵn có của bảng/tài liệu tài chính, dữ liệu VNINDEX, và kiểm tra nhẹ lịch giao dịch.
- Không thực hiện: tải lịch sử hàng loạt (bulk history), tập dữ liệu nghiên cứu, đăng nhập, CAPTCHA, cookie/token riêng tư, kiểm tra VietFin, triển khai adapter, hoặc thực thi `SOURCE_SMOKE`.

## 3. Quyền sở hữu / Truy cập / Quyền hạn (Ownership / access / rights)

| Hạng mục | Quan sát thực tế | Kết quả / Mức độ tin cậy |
|---|---|---|
| Website/nhà cung cấp | CafeF, bản quyền ở chân trang ghi nhận VCCorp | HIGH |
| Công khai/riêng tư | Các trang và request JSON do trang tạo ra đều truy cập được không cần đăng nhập | Đã xác minh truy cập công khai, HIGH |
| Yêu cầu đăng nhập | Không yêu cầu đăng nhập đối với profile, lịch sử, sự kiện, tài chính, tài liệu, VNINDEX, chính sách hay lịch giao dịch | Không, HIGH |
| Đăng ký trả phí (Subscription) | Không có tường trả phí trên các đường dẫn dữ liệu được kiểm tra; widget giải thưởng riêng ghi `hasSubscription = false`, nhưng nằm ngoài phạm vi khám phá | Không thấy yêu cầu trả phí trong phạm vi kiểm tra, HIGH |
| Ranh giới truy cập | Không gặp CAPTCHA, 401, 403, paywall, hay thách thức chống bot trong các bước kiểm tra có giới hạn | Không ghi nhận, HIGH |
| Chính sách công khai | `https://cafef.vn/robots.txt` trả về `User-agent: *` và `Allow: /`; chính sách bảo mật thảo luận về dữ liệu khách truy cập/cookie, không đề cập quyền tự động hóa dữ liệu | Quan sát thực tế rõ ràng, HIGH |
| Quyền tự động hóa | Không tìm thấy điều khoản hay giấy phép nào của CafeF cho phép khai thác dữ liệu tự động. `robots.txt` không được coi là sự cho phép | `NOT_VERIFIED` |
| Phản ứng về giới hạn tần suất (Rate behavior) | Các request tuần tự nhỏ đều thành công không bị lỗi 429 hay cảnh báo giới hạn. UI lịch sử áp dụng debounce 700 ms phía client khi chuyển trang. Chưa kiểm tra giới hạn tải tối đa | Chỉ là hành vi quan sát được, MEDIUM |

**Kết luận về quyền hạn:** Truy cập hợp lệ qua trình duyệt công khai đã được xác lập cho việc khám phá. Quyền tự động hóa là `NOT_VERIFIED`; điều này ngăn cản việc phê duyệt `SOURCE_SMOKE` thực tế tại đây.

## 4. Định danh chứng khoán (Security identity)

### Phạm vi mã cổ phiếu quan sát (Observed symbol coverage)

| Mã (Ticker) | Tên công ty hiển thị | Sàn hiển thị | Ngày giao dịch đầu tiên hiển thị | Kết quả profile hiện tại |
|---|---|---|---|---|
| FPT | Công ty Cổ phần FPT | HOSE | 13/12/2006 | VERIFIED |
| VNM | Công ty Cổ phần Sữa Việt Nam | HOSE | 19/01/2006 | VERIFIED |
| PVS | Tổng Công ty Cổ phần Dịch vụ Kỹ thuật Dầu khí Việt Nam | HNX | 20/09/2007 | VERIFIED |
| ACV | Tổng công ty Cảng hàng không Việt Nam - CTCP | UpCOM | 21/11/2016 | VERIFIED |

Các ghi nhận trên chỉ áp dụng cho profile hiện tại, không xác lập lịch sử mã chứng khoán hay lịch sử niêm yết trên sàn.

### Ngữ nghĩa các trường (Field semantics)

| Nhãn/Key nguồn | Ý nghĩa | Mã mẫu | Giá trị mẫu | Ứng viên Canonical | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|---|---|
| URL symbol & `Mã cổ phiếu` | Giá trị tra cứu/hiển thị mã cổ phiếu hiện tại của CafeF | FPT | `FPT` | `ticker` | Đồng nhất giữa URL, tiêu đề trang, nhãn profile và các dòng lịch sử | HIGH |
| Tiêu đề profile / `Name` trong renderer `CompanyIntro` | Tên hiển thị hiện tại của công ty | FPT | `Công ty Cổ phần FPT` | `company_name` | Tiêu đề trang và bảng thông tin profile | HIGH |
| `Sàn giao dịch`; renderer ánh xạ `CenterId` 1/2/9 sang HoSE/HNX/UpCOM | Nhãn sàn giao dịch hiện tại | PVS | `HNX` | `exchange` | Nhãn UI kết hợp logic renderer; nhất quán trên 4 mã | HIGH |
| `Nhóm ngành` | Phân nhóm ngành của CafeF | FPT | `Dịch vụ công nghệ thông tin` | `industry` | UI thông tin cơ bản của FPT | HIGH |
| Tiêu đề cùng danh mục | Danh mục rộng hơn của CafeF (khi hiển thị) | FPT | `Công nghệ / Dịch vụ công nghệ thông tin` | Ứng viên `sector` (`Công nghệ`) | Chỉ có trên UI tổng quan hiện tại | MEDIUM |
| `Ngày giao dịch đầu tiên` | Ngày giao dịch đầu tiên CafeF hiển thị cho profile hiện tại | FPT | `13/12/2006` | Ứng viên `listing_date` | Nhãn profile rõ ràng; cả 4 mã đều có giá trị | HIGH |
| ID chứng khoán/công ty dạng số của nhà cung cấp | Không thấy mã định danh dạng số nào xuất hiện trên UI profile hoặc tham số request | FPT | NOT_FOUND | `provider_security_id` | Request dùng `Symbol=FPT`; ID bài viết là dành cho tài liệu/sự kiện, không phải chứng khoán | HIGH cho quan sát không tìm thấy |
| Trạng thái niêm yết/hủy niêm yết | Trạng thái trong phiên hiện tại như `Tạm nghỉ` có hiển thị, nhưng không thấy trường trạng thái vòng đời niêm yết | FPT | NOT_FOUND | `status`, `delisting_date` | Văn bản phiên giao dịch hiện tại không phải trạng thái vòng đời chứng khoán | HIGH |

## 5. Cổ phiếu / Cấu trúc vốn (Shares / capital structure)

Trạng thái domain:

```text
CURRENT_SNAPSHOT_ONLY
```

| Mã | `KL CP đang niêm yết` | `KL CP đang lưu hành` | Quan sát |
|---|---:|---:|---|
| FPT | 1,714,326,422 | 1,714,326,422 | Snapshot profile hiện tại |
| VNM | 2,089,955,445 | 2,089,955,445 | Snapshot profile hiện tại |
| PVS | 511,420,099 | 613,704,118 | Hai trường có giá trị khác nhau; không được đánh đồng |
| ACV | 3,582,847,523 | 3,582,324,023 | Hai trường có giá trị khác nhau; không tự suy đoán là cổ phiếu quỹ |

| Khái niệm yêu cầu | Quan sát trên CafeF | Độ sẵn sàng Canonical | Độ tin cậy |
|---|---|---|---|
| `listed_shares` | Nhãn rõ ràng `KL CP đang niêm yết` | Ngữ nghĩa giá trị đã xác minh, nhưng chưa sẵn sàng cho `shares_history` vì thiếu ngày hiệu lực/ngày công bố đi kèm | HIGH |
| `outstanding_shares` | Nhãn rõ ràng `KL CP đang lưu hành` | Ngữ nghĩa giá trị đã xác minh, nhưng chưa sẵn sàng cho `shares_history` cùng lý do thiếu mốc thời gian | HIGH |
| `issued_shares` | Không thấy trường số lượng cổ phiếu phát hành rõ ràng | NOT_FOUND | HIGH |
| `treasury_shares` | Không thấy trường cổ phiếu quỹ rõ ràng | NOT_FOUND; không suy ra bằng phép trừ | HIGH |
| `effective_date` | Không có ngày hiệu lực bên cạnh số lượng hiện tại | NOT_READY | HIGH |
| Thời điểm công bố / `available_at` | Không có dấu thời gian công bố gắn liền với số lượng hiện tại | NOT_READY | HIGH |
| Biến động số lượng cổ phiếu lịch sử | Có `Biểu đồ biến đổi vốn điều lệ`, số cổ phiếu niêm yết ban đầu, tin tức sự kiện/phát hành, nhưng không có chuỗi dữ liệu cổ phiếu lịch sử kèm mốc thời gian | NOT_READY; không tự tái tạo hoặc backfill | HIGH |

Các số lượng hiện tại tính bằng đơn vị cổ phiếu (không có hệ số nhân). Chúng chỉ là snapshot hiện tại và **không được phép** backfill vào lịch sử.

## 6. Dữ liệu thị trường hàng ngày (Daily market data)

### Request lịch sử công khai quan sát từ trang

```text
GET https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx
    ?ExchangeType={HOSE|HNX|UPCOM}
    &Symbol={symbol}
    &StartDate={MM/DD/YYYY}
    &EndDate={MM/DD/YYYY}
    &PageIndex={1-based page}
    &PageSize=20
```

Trang gọi `response.json()`. Các đường dẫn UI thiết lập đúng tham số sàn bao gồm:

- `https://cafef.vn/du-lieu/Lich-su-giao-dich/hose/fpt-1.chn`
- `https://cafef.vn/du-lieu/lich-su-gia/vnm.chn` (mặc định HOSE đã đúng)
- `https://cafef.vn/du-lieu/Lich-su-giao-dich/hnx/pvs-1.chn`
- `https://cafef.vn/du-lieu/Lich-su-giao-dich/upcom/acv-1.chn`

### Field semantics và đơn vị (units)

| Key nguồn / Nhãn UI | Ý nghĩa quan sát | Đơn vị nguồn | Mục tiêu Canonical | Trạng thái chuyển đổi / ánh xạ | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|---|---|
| `Ngay` / `Ngày` | Ngày phiên giao dịch | Ngày `DD/MM/YYYY` | `trade_date` | Parse ngày; không có múi giờ đi kèm | Renderer và các dòng dữ liệu 4 mã | HIGH |
| `GiaMoCua` / `Mở cửa` | Giá mở cửa | nghìn VNĐ/cổ phiếu | Ứng viên price | Nhân 1.000 ra VNĐ/cổ phiếu, nhưng chưa ánh xạ sang `raw_open` khi chưa chứng minh được price basis | Đơn vị bảng rõ ràng & key của renderer | HIGH cho ý nghĩa/đơn vị; LOW cho canonical basis |
| `GiaCaoNhat` / `Cao nhất` | Giá cao nhất phiên | nghìn VNĐ/cổ phiếu | Ứng viên price | ×1.000; giữ nguyên chưa ánh xạ cho đến khi xác định basis | Giống trên | HIGH / LOW |
| `GiaThapNhat` / `Thấp nhất` | Giá thấp nhất phiên | nghìn VNĐ/cổ phiếu | Ứng viên price | ×1.000; giữ nguyên chưa ánh xạ | Giống trên | HIGH / LOW |
| `GiaDongCua` / `Đóng cửa` | Giá đóng cửa hiển thị | nghìn VNĐ/cổ phiếu | Ứng viên price | ×1.000; chưa chọn `raw_close` hay `adj_close` | Nhãn/key rõ ràng | HIGH cho ý nghĩa/đơn vị; LOW cho basis |
| `GiaDieuChinh` / `Điều chỉnh` | Cột điều chỉnh của CafeF | nghìn VNĐ/cổ phiếu | Ứng viên `adj_close` | ×1.000, nhưng phương pháp điều chỉnh không được mô tả trong bằng chứng quan sát; không ánh xạ | Nhãn/key rõ ràng; mẫu kiểm tra vô tình bằng giá đóng cửa | HIGH cho định danh cột; LOW cho ngữ nghĩa |
| `KhoiLuongKhopLenh` / `GD khớp lệnh - Khối lượng` | Chỉ khối lượng khớp lệnh | cổ phiếu (cp) | Ứng viên `volume` | Giữ nguyên giá trị, nhưng chính sách gộp canonical so với khối lượng thỏa thuận chưa quyết định | Nhóm UI, key renderer, dữ liệu mẫu | HIGH cho ý nghĩa nguồn; MEDIUM cho mục tiêu canonical |
| `GiaTriKhopLenh` / `Giá trị` khớp lệnh | Chỉ giá trị khớp lệnh | tỷ VNĐ | Ứng viên `traded_value` | ×1.000.000.000; không đưa lên canonical cho đến khi chính sách khớp lệnh vs tổng giá trị được chốt | Tiêu đề bảng rõ ràng và mẫu | HIGH cho ý nghĩa/đơn vị; MEDIUM cho mục tiêu |
| `KLThoaThuan` | Khối lượng thỏa thuận | cổ phiếu | Chỉ dành cho RAW | Giữ nguyên | Nhóm UI riêng biệt rõ ràng | HIGH |
| `GtThoaThuan` | Giá trị thỏa thuận | tỷ VNĐ | Chỉ dành cho RAW | ×1.000.000.000 | Nhóm UI riêng biệt rõ ràng | HIGH |
| `Giá tham chiếu` trên trang tổng quan | Giá tham chiếu phiên hiện tại | nghìn VNĐ/cổ phiếu | Ứng viên `reference_price` | ×1.000; endpoint lịch sử không trả về trường này | Tổng quan FPT: `72.70` ngày 16/09/2026 | HIGH cho snapshot hiện tại; LOW cho lịch sử |
| `Giá trần` trên trang tổng quan | Giá trần phiên hiện tại | nghìn VNĐ/cổ phiếu | Ứng viên `ceiling_price` | ×1.000; không có trong response lịch sử | Tổng quan FPT: `77.70` | HIGH cho snapshot hiện tại; LOW cho lịch sử |
| `Giá sàn` trên trang tổng quan | Giá sàn phiên hiện tại | nghìn VNĐ/cổ phiếu | Ứng viên `floor_price` | ×1.000; không có trong response lịch sử | Tổng quan FPT: `67.70` | HIGH cho snapshot hiện tại; LOW cho lịch sử |
| Văn bản phiên trên trang tổng quan | Trạng thái trong ngày hiện tại, ví dụ `Tạm nghỉ` | Văn bản | Ứng viên `trading_status` | Chưa thấy chuỗi lịch sử trạng thái hoặc ánh xạ sang enum canonical | Tổng quan FPT lúc 11:29 ngày 16/09/2026 | MEDIUM |

### Mẫu kiểm tra chéo nhỏ giữa các mã (Small cross-symbol sample)

Mỗi dòng dưới đây là phiên hoàn thành đầu tiên quan sát được; đây là bằng chứng, không phải tập dữ liệu. Giá hiển thị theo đơn vị gốc CafeF (nghìn VNĐ), giá trị khớp lệnh tính theo tỷ VNĐ.

| Mã | Ngày | Đóng cửa | Điều chỉnh | KL khớp lệnh | Giá trị khớp | Mở cửa | Cao nhất | Thấp nhất |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| FPT | 15/09/2026 | 72.70 | 72.70 | 3,977,500 | 289.88 | 72.70 | 73.40 | 72.50 |
| VNM | 15/09/2026 | 59.70 | 59.70 | 1,835,300 | 109.64 | 59.50 | 60.20 | 59.40 |
| PVS | 15/09/2026 | 34.20 | 34.20 | 8,111,800 | 274.05 | 33.60 | 34.40 | 32.00 |
| ACV | 15/09/2026 | 39.40 | 39.40 | 229,900 | 9.02 | 39.20 | 39.50 | 38.90 |

Việc giá đóng cửa và giá điều chỉnh bằng nhau trong các mẫu này không chứng minh được cơ sở điều chỉnh (adjustment basis).

### Khoảng ngày, phân trang, thứ tự và kết quả rỗng

#### OBSERVED / OPERATIONAL CONTRACT — giới hạn khoảng PriceHistory

Quan sát live ngày `2026-09-24` cho ACB/HOSE cho thấy request
`2012-01-01 → 2012-12-31` trả HTTP/envelope hợp lệ nhưng chỉ có 65 dòng từ
`2012-10-01 → 2012-12-28`, tức xấp xỉ quý cuối. Bốn trang khớp nhất quán với
`TotalCount=65`; vấn đề nằm ở khoảng request bị cắt ngầm, không phải phép tính phân
trang. UI CafeF cũng chỉ cho chọn tối đa xấp xỉ ba tháng.

Đây là ràng buộc vận hành **đã quan sát**, không phải bảo đảm API chính thức hay mô tả
chính xác thuật toán server. Khoảng dài có thể bị truncate im lặng; HTTP 200 và
`Success=true` không chứng minh completeness của khoảng được yêu cầu. Vì vậy DELTA
phải acquisition bằng các giao cắt quý lịch
`NON_OVERLAPPING_CALENDAR_QUARTER_INTERSECTIONS_OLDEST_TO_NEWEST`, sau khi giao target
window với identity interval đã xác minh.

- Khoảng ngày mặc định trên UI: 1 tháng tính đến hôm nay; script ép ngày kết thúc trong tương lai về hôm nay và ngày bắt đầu lớn hơn ngày kết thúc về bằng ngày kết thúc.
- Khoảng ngày request: `StartDate` và `EndDate` rõ ràng; ngữ nghĩa ranh giới (bao gồm/không bao gồm) chưa được kết luận chắc chắn.
- Thứ tự sắp xếp: mới nhất xếp trước (`DESC`) trong tất cả kết quả quan sát.
- Phân trang: `PageIndex` bắt đầu từ 1, `PageSize=20` cố định, tổng số trang tính từ `TotalCount`.
- Kết quả rỗng: UI hiển thị chính xác `KHÔNG CÓ KẾT QUẢ PHÙ HỢP`; dữ liệu rỗng/sai định dạng cũng chuyển về trạng thái rỗng.
- Export file: UI từ chối khoảng thời gian dài hơn 1 tháng; đây là hạn chế xuất file, không phải bằng chứng về giới hạn ngày tối đa của request lịch sử thông thường.
- Hành vi ngày hiện tại: dòng VNINDEX ngày 16/09/2026 hiển thị `--` cho giá đóng cửa/điều chỉnh khi phiên chưa kết thúc. Dữ liệu mã cổ phiếu trong ngày không đủ nhất quán để đưa ra quy tắc.

## 7. Cơ sở giá (Price basis)

```text
UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET
```

Bằng chứng tìm thấy:

- Bảng lịch sử có hai cột riêng biệt `Đóng cửa` (`GiaDongCua`) và `Điều chỉnh` (`GiaDieuChinh`).
- Trang tổng quan công ty ghi `Đồ thị vẽ theo giá điều chỉnh`.
- Không thấy tài liệu nào của CafeF định nghĩa việc điều chỉnh là chỉ chia tách (split-only), nhà cung cấp tự điều chỉnh (vendor-adjusted), tổng lợi nhuận (total-return), hay phương pháp nào khác.
- Một số dòng gần đây có giá đóng cửa bằng giá điều chỉnh, nhưng điều này không phải bằng chứng về ngữ nghĩa.

Do đó, cả `GiaDongCua` và `GiaDieuChinh` đều **không được phép** đưa lên DELTA `raw_close`/`adj_close`, và sự không chắc chắn này cũng áp dụng cho các giá OHLC.

## 8. Thời gian / Múi giờ / Độ sẵn sàng (Time / timezone / availability)

- `trade_date`: nhãn ngày phiên giao dịch; định dạng đã xác minh nhưng không có múi giờ đính kèm trong response lịch sử.
- Trang giá hiện tại: hiển thị giá trị giống giờ địa phương như `Cập nhật: 11:29, Thứ 4, 16/09/2026`, không có múi giờ rõ ràng.
- Trang tin tức/sự kiện doanh nghiệp: hiển thị dấu thời gian công bố như `Thứ 6, 22/05/2026, 00:00`, không có múi giờ rõ ràng.
- Link tài liệu tài chính: tên file chứa ngày/giờ dạng upload, nhưng UI không dán nhãn là `published_at` hay `available_at`; chỉ là ứng viên độ tin cậy LOW.
- `available_at`: chưa được xác minh chuẩn hoá cho thị trường, cổ phiếu, sự kiện doanh nghiệp hay chỉ tiêu tài chính.
- Xử lý Adapter nếu triển khai tiếp theo: lưu thời điểm thu thập `fetched_at` theo UTC, giữ nguyên chuỗi ngày hiển thị/request gốc, và để trống `available_at` nguồn cho đến khi ngữ nghĩa múi giờ và thời điểm công bố được xác minh.

## 9. Quyền mua & Cổ tức / Hành động doanh nghiệp (Corporate actions)

### Tính sẵn có

CafeF hiển thị `Lịch trả cổ tức & tăng vốn`, các trang tin tức/sự kiện, và đường dẫn tài liệu nguồn công khai. Giao diện cũ nêu rõ:

- Ngày hiển thị cho cổ tức/quyền là ngày giao dịch không hưởng quyền (`ngày GD không hưởng quyền`);
- Ngày hiển thị cho các đợt phát hành là ngày phát hành.

Lịch sử FPT quan sát được bao gồm cổ tức tiền mặt, thưởng/cổ tức bằng cổ phiếu, và phát hành cho ESOP. Không kiểm tra điều khoản phát hành quyền mua cho FPT.

### Ví dụ mã FPT

| Trường yêu cầu | Quan sát thực tế | Trạng thái ánh xạ | Độ tin cậy |
|---|---|---|---|
| ID sự kiện/tham chiếu của nhà cung cấp | URL bài viết chứa `fpt-2893107` | Giữ lại dưới dạng ứng viên tài liệu/tham chiếu nguồn; không nhầm lẫn với ID chứng khoán | HIGH |
| Loại sự kiện | `trả cổ tức ... bằng tiền mặt` | Ứng viên `cash_dividend` | HIGH |
| Ngày thông báo/công bố | Dấu thời gian bài viết `22/05/2026 00:00` | Chỉ là ứng viên ngày công bố; múi giờ chưa xác minh | MEDIUM |
| Ngày GDKHQ (ex-date) | Tiêu đề và bài viết: `28/05/2026` | Ứng viên `ex_date` | HIGH |
| Ngày chốt danh sách (record date) | Không có trong quan sát HTML | NOT_FOUND trong ví dụ này | HIGH |
| Ngày hiệu lực (effective date) | Không được định nghĩa rõ ràng là ngày hiệu lực canonical | NOT_READY | HIGH |
| Ngày thanh toán (payment date) | Không có trong quan sát HTML | NOT_FOUND trong ví dụ này | HIGH |
| Cổ tức tiền mặt | `1.000 đ/cp` | Ứng viên `cash_amount=1000`, `currency=VND` | HIGH |
| Tỷ lệ cổ phiếu | Các mục lịch sử FPT khác ghi `Cổ tức/Thưởng bằng Cổ phiếu, tỷ lệ 15%` | Tìm thấy, nhưng việc chuẩn hoá tỷ lệ chưa được định nghĩa | MEDIUM |
| Điều khoản quyền mua / giá phát hành | Không quan sát được trong ví dụ FPT | NOT_FOUND | HIGH |
| Tài liệu nguồn | File PDF HOSE đính kèm có link `20260522 - FPT - TB NDKCC tra co tuc con lai nam 2025 bang tien.pdf` | Giữ URL/tham chiếu; không tải file hàng loạt | HIGH |

Không có hệ số điều chỉnh (adjustment factors) nào được tính toán.

## 10. Báo cáo tài chính (Financial statements)

### Tính sẵn có và cấu trúc request

Cả 4 mã đều hiển thị các bảng quý hiện tại. FPT hiển thị báo cáo năm và điều hướng chi tiết cho Bảng cân đối kế toán, Báo cáo kết quả kinh doanh, Lưu chuyển tiền tệ trực tiếp/gián tiếp. Trang tóm tắt hiện tại thực hiện request JSON công khai:

```text
GET https://apiweb.cafef.vn/api/v1/BCTC/GetReportSummary
    ?symbol=FPT
    &pageIndex={1-based page}
    &pageSize=4
    &reportType={ALL|statement code}
    &TypeTime={QUY|NAM|LUYKE}
```

Trang gọi `response.json()`. Các bộ chọn UI quan sát được là `Theo quý`, `Theo năm`, và `Lũy kế 6 tháng`; đơn vị có thể là `Tỷ đồng` hoặc `Triệu đồng`. Renderer chia giá trị fact gốc cho `1.000.000.000` hoặc `1.000.000` để hiển thị theo đơn vị đã chọn.

| Khả năng | Quan sát | Kết quả | Độ tin cậy |
|---|---|---|---|
| Theo quý | Q3-2025 đến Q2-2026 xuất hiện trên trang FPT, VNM, PVS, ACV | AVAILABLE | HIGH |
| Theo năm | `Theo năm`, danh sách tài liệu năm và trang báo cáo đầy đủ năm đều thấy rõ | AVAILABLE | HIGH |
| Kết quả kinh doanh | `Kết quả KD` / báo cáo kết quả kinh doanh chi tiết | AVAILABLE | HIGH |
| Cân đối kế toán | `Cân đối kế toán` | AVAILABLE | HIGH |
| Lưu chuyển tiền tệ | `Lưu chuyển tiền tệ`, kèm điều hướng trực tiếp/gián tiếp | AVAILABLE | HIGH |
| Hợp nhất vs Công ty mẹ | Tiêu đề tài liệu FPT phân biệt rõ `hợp nhất` và `công ty mẹ` | AVAILABLE dưới dạng metadata tài liệu | HIGH |
| Trạng thái kiểm toán/soát xét | Tiêu đề tài liệu hiển thị rõ `đã kiểm toán` và `đã soát xét` | AVAILABLE dưới dạng metadata tài liệu | HIGH |
| Sửa đổi / điều chỉnh lại (Revision/restatement) | Không thấy cờ hoặc số bản sửa đổi rõ ràng | UNKNOWN | HIGH |
| Tiền tệ | Đơn vị UI `tỷ đồng` / `triệu đồng` chỉ VNĐ | Ứng viên VND | HIGH |
| Quy mô đơn vị (Unit scale) | Renderer chia giá trị gốc cho `1e9` hoặc `1e6` một cách rõ ràng | VERIFIED cho UI tóm tắt hiện tại | HIGH |

### Ngữ nghĩa metadata báo cáo

| Khái niệm yêu cầu | Quan sát thực tế | Trạng thái ánh xạ | Độ tin cậy |
|---|---|---|---|
| `fiscal_year` | Tiêu đề như `Q2-2026`, `2025` | Ứng viên parse | HIGH |
| `fiscal_quarter` | Tiêu đề `Q1`...`Q4` | Ứng viên parse | HIGH |
| `period_end` | Không có ngày kết thúc lịch rõ ràng trong payload tóm tắt | NOT_READY | HIGH |
| `period_start` | Không hiển thị | NOT_FOUND | HIGH |
| Phạm vi báo cáo | Tiêu đề tài liệu (`hợp nhất` / `công ty mẹ`) | Sẵn sàng cho metadata tài liệu, chưa liên kết với fact tóm tắt | HIGH |
| `published_at` | Dấu thời gian tài liệu/tin tức có trên các bài công bố; bản thân danh sách tài liệu chỉ hiển thị nhãn kỳ | Chỉ là ứng viên | MEDIUM |
| `available_at` | Dấu thời gian tên file như hậu tố dạng upload của tài liệu FPT Q2 thấy được nhưng CafeF không định nghĩa | NOT_READY | LOW |
| Trạng thái kiểm toán | `đã kiểm toán` / `đã soát xét` trong tiêu đề | Ứng viên parse | HIGH |
| Sửa đổi / điều chỉnh lại | Không có ngữ nghĩa rõ ràng | NOT_READY | HIGH |
| ID báo cáo của nhà cung cấp | Tên file/URL tài liệu có thể giữ làm định danh tài liệu nguồn, nhưng không có ngữ nghĩa ID báo cáo ổn định | Chỉ dành cho RAW provenance | MEDIUM |

### Kiểm tra ngữ nghĩa khoảng thời gian Q2/Q3 (Q2/Q3 duration-fact check)

```text
UNKNOWN — DO NOT MAP YET
```

Lý do:

- CafeF có các chế độ UI riêng biệt `Theo quý` và `Lũy kế 6 tháng`.
- Các giá trị Kết quả kinh doanh `Theo quý` hoạt động như các quý độc lập (standalone) và trang tổng quan cũ hiển thị giá trị lũy kế 6 tháng riêng.
- Trên cùng giao diện `Theo quý`, các dòng Lưu chuyển tiền tệ FPT lại có vẻ là lũy kế đến Q2 (ví dụ Lợi nhuận trước thuế Q2 là `5.714,32` so với Q1 `2.803,84`, trong khi Kết quả kinh doanh Q2 lợi nhuận trước thuế là `2.910,48`). Chỉ dựa vào tính toán số học không đủ làm bằng chứng, và UI quan sát được không định nghĩa rõ ngữ nghĩa quý của lưu chuyển tiền tệ.
- Không tìm thấy tài liệu nào của CafeF định nghĩa ngữ nghĩa khoảng thời gian Q2/Q3 một cách nhất quán giữa các loại báo cáo.

Do đó, các fact khoảng thời gian Q2/Q3 không thể gắn nhãn chung là `STANDALONE_QUARTER` hay `YTD_CUMULATIVE`. Không ánh xạ chúng cho đến khi tài liệu nguồn hoặc tài liệu của CafeF xác lập ngữ nghĩa cho từng loại báo cáo/fact.

### Ứng viên raw-fact thực tế quan sát được

| Nhóm | Các ứng viên quan sát được | Chưa quan sát / Chưa an toàn để đưa lên |
|---|---|---|
| Kết quả kinh doanh | Doanh thu, giá vốn hàng bán, lợi nhuận gộp, chi phí bán hàng, chi phí quản lý doanh nghiệp, lợi nhuận hoạt động, lợi nhuận trước thuế, lợi nhuận sau thuế, lợi nhuận sau thuế công ty mẹ | Chi phí lãi vay và thuế TNDN riêng chưa được xác minh trên tóm tắt; sự tương đương EBIT chưa được định nghĩa |
| Cân đối kế toán | Tiền và tương đương tiền, các khoản phải thu, hàng tồn kho, tài sản ngắn hạn, tổng tài sản, nợ ngắn hạn, tổng nợ phải trả, vốn chủ sở hữu, lợi nhuận sau thuế chưa phân phối, tài sản cố định | `Nợ ngắn hạn` / `Nợ dài hạn` là nợ phải trả (liabilities) trên tóm tắt, không được tự coi là nợ vay ngắn/dài hạn (short/long-term debt) |
| Lưu chuyển tiền tệ | Lưu chuyển tiền từ hoạt động kinh doanh, đầu tư, tài chính; khấu hao; tiền chi mua sắm/xây dựng TSCĐ và tài sản dài hạn khác | Ánh xạ CapEx chỉ là ứng viên; cơ sở khoảng thời gian Q2/Q3 chưa giải quyết |
| Cổ phiếu | EPS cơ bản và suy giảm thấy được | Số lượng cổ phiếu bình quân lưu hành tính EPS cơ bản/suy giảm là NOT_FOUND |

Các chỉ tiêu tài chính chưa sẵn sàng cho việc thu thập PIT chuẩn hoá vì ranh giới kỳ, liên kết báo cáo nguồn, `available_at`, xử lý bản sửa đổi và ngữ nghĩa khoảng thời gian Q2/Q3 chưa hoàn thiện.

## 11. Chỉ số Benchmark / Lịch giao dịch (Benchmark / trading-calendar availability)

| Domain | Trạng thái | Quan sát | Hạn chế | Độ tin cậy |
|---|---|---|---|---|
| Mức chỉ số VNINDEX lịch sử | AVAILABLE | `VNINDEX` là một mã lịch sử có thể chọn; các dòng lịch sử công khai trả về mức chỉ số theo ngày | Quan sát thấy các dòng hiện tại/chưa hoàn thành và ít nhất một dòng có vẻ bất thường; các trường giá trị và basis chưa được ánh xạ sâu | MEDIUM |
| Lịch giao dịch sàn rõ ràng | AVAILABLE | Thông báo công khai CafeF/HOSE `HOSE: Thông báo lịch nghỉ giao dịch năm 2026` liệt kê các ngày nghỉ cụ thể và đính kèm PDF nguồn | Chỉ ở dạng tài liệu/tin tức, không phải lịch giao dịch theo ngày có cấu trúc của sàn; mới chỉ kiểm tra nhẹ | MEDIUM |

## 12. Request / Phân trang / Phản ứng Rate (Request / pagination / rate behavior)

| Khu vực | Phương thức / Nội dung | Tham số quan trọng (không bảo mật) | Phân trang / Khoảng ngày | Thứ tự / Hành vi khi rỗng | Hành vi truy cập quan sát được |
|---|---|---|---|---|---|
| Trang Profile | GET HTML; trang khởi tạo các GET JSON | `Symbol=fpt` trên `CompanyIntro.ashx`, `PriceRealTimeHeader.ashx`, `RealtimePrice.ashx`, `LichSuKien.ashx` | Không thấy phân trang profile | Snapshot hiện tại | Công khai, không đăng nhập; JSON được parse bởi trang |
| Lịch sử thị trường | GET HTML + GET JSON | `ExchangeType`, `Symbol`, `StartDate`, `EndDate`, `PageIndex`, `PageSize=20` | Bắt đầu từ 1; mặc định 1 tháng; xuất file max 1 tháng; giới hạn tối đa của request thường chưa rõ | Mới nhất xếp trước; thông báo trạng thái rỗng rõ ràng | Công khai; không lỗi trong phạm vi kiểm tra; debounce 700 ms phía client khi đổi trang |
| Tóm tắt tài chính | GET HTML + GET JSON | `symbol`, `pageIndex`, `pageSize=4`, `reportType`, `TypeTime` | Bắt đầu từ 1, 4 kỳ/trang | UI đảo ngược mảng kỳ trả về để hiển thị; chưa kiểm tra hợp đồng rỗng rõ ràng | Công khai, không đăng nhập |
| Tài liệu tài chính | GET HTML; link PDF công khai | Bộ lọc thể loại/năm | Danh sách dài rendered từ server | Tài liệu mới nhất xếp trước trên trang quan sát | Công khai; không bắt buộc tải về để khám phá |
| Bài viết sự kiện doanh nghiệp | GET HTML + link đính kèm công khai | ID bài viết trong slug | N/A | Dấu thời gian bài viết và nội dung sự kiện | Công khai, không đăng nhập |
| Chính sách | GET text/HTML | Không có | N/A | N/A | Công khai |

Không có header bảo mật, cookie, token, session ID, giá trị fingerprint hay tài liệu xác thực riêng tư nào được ghi lại.

## 13. Mappings đã xác minh (Verified mappings)

Các ánh xạ này có đủ bằng chứng nhãn nguồn. Một trường được xác minh không có nghĩa là một dòng canonical hoàn chỉnh có thể được xuất ra khi thiếu các trường đồng hành bắt buộc.

| Nguồn | Ứng viên Canonical | Chuyển đổi (Transform) | Độ sẵn sàng | Độ tin cậy |
|---|---|---|---|---|
| Ticker hiển thị / `Symbol` request | `ticker` | Chữ hoa | Ready | HIGH |
| Tiêu đề profile / renderer `Name` | `company_name` | Giữ nguyên văn bản Unicode | Ready | HIGH |
| `Sàn giao dịch` / Ánh xạ `CenterId` | `exchange` | Chuẩn hoá HoSE→HOSE, HNX→HNX, UpCOM→UPCOM | Ready cho định danh hiện tại | HIGH |
| `Nhóm ngành` | `industry` | Giữ nguyên phân loại nhà cung cấp | Ready kèm xuất xứ phân loại CafeF | HIGH |
| `Ngày giao dịch đầu tiên` | Ứng viên `listing_date` | Parse `DD/MM/YYYY` | Ready dưới dạng metadata profile hiện tại; không phải lịch sử sàn | HIGH |
| `Ngay` | `trade_date` | Parse `DD/MM/YYYY` | Ready dưới dạng trường ngày | HIGH |
| Tài liệu `hợp nhất` / `công ty mẹ` | `statement_scope` | consolidated / separate | Ready cho metadata tài liệu | HIGH |
| Tài liệu `đã kiểm toán` / `đã soát xét` | `audit_status` | audited / reviewed | Ready cho metadata tài liệu | HIGH |
| Tiêu đề kỳ tài chính | `fiscal_year`, `fiscal_quarter` | Parse `Qn-YYYY` | Ready dưới dạng nhãn kỳ; định danh báo cáo đầy đủ vẫn chưa xong | HIGH |
| Bộ chọn đơn vị và hệ số chia tóm tắt | `currency=VND`, `unit_scale` | 1e9 cho `Tỷ đồng`, 1e6 cho `Triệu đồng` | Ready cho các giá trị tóm tắt hiện tại, phụ thuộc vào rào cản kỳ/PIT | HIGH |

## 14. Mappings chưa rõ / bị chặn (Unknown / blocked mappings)

Không có đường dẫn nào bị chặn bởi cơ chế kiểm soát truy cập của CafeF. Những mục sau đây vẫn chưa rõ hoặc cố tình để trống (unmapped):

- `provider_security_id`: NOT_FOUND.
- Lịch sử mã cổ phiếu/sàn giao dịch, ngày hủy niêm yết và trạng thái vòng đời chứng khoán: NOT_FOUND.
- Ngày hiệu lực `effective_date` và thời điểm công bố/sẵn có của snapshot cổ phiếu hiện tại: UNKNOWN.
- Cổ phiếu phát hành, cổ phiếu quỹ và chuỗi số liệu cổ phiếu lịch sử: NOT_FOUND.
- Cơ sở giá `GiaDongCua`/OHLC so với `GiaDieuChinh`: `UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET`.
- Giá tham chiếu, trần, sàn lịch sử và trạng thái giao dịch lịch sử: NOT_FOUND trong response lịch sử.
- Quy tắc đưa `volume`/`traded_value` khớp lệnh vs thỏa thuận vào canonical: UNKNOWN.
- Múi giờ nguồn của giá, bài viết và dấu thời gian upload: UNKNOWN.
- Ngày chốt danh sách/hiệu lực/thanh toán và tỷ lệ cổ phiếu/quyền chuẩn hoá của sự kiện doanh nghiệp: Chưa hoàn thiện.
- Ngày bắt đầu kỳ `period_start`, ngày kết thúc chính xác `period_end`, `published_at`/`available_at` canonical, sửa đổi/điều chỉnh lại và ID báo cáo ổn định: UNKNOWN.
- Fact khoảng thời gian Q2/Q3: `UNKNOWN — DO NOT MAP YET`.
- Số lượng cổ phiếu bình quân lưu hành tính EPS cơ bản và suy giảm: NOT_FOUND.
- Quyền tự động hóa: `NOT_VERIFIED`.

Mọi diễn giải độ tin cậy LOW ở trên đều chưa được giải quyết và **không được phép** đưa lên chính thức.

## 15. Vai trò ứng viên theo domain (Candidate role by domain)

Đây chỉ là đánh giá khả năng làm ứng viên của CafeF. CafeF **chưa** được tuyên bố là nguồn sự thật (source of truth) cuối cùng của DELTA trước khi đối chiếu với VietFin sau này.

| Domain | Tính sẵn có | Độ tin cậy | Vai trò ứng viên | Hạn chế chính |
|---|---|---|---|---|
| Chứng khoán (Security) | Profile hiện tại có sẵn cho cả 4 mã | HIGH | PRIMARY_CANDIDATE | Không có ID chứng khoán nhà cung cấp hay lịch sử sàn/trạng thái |
| Lịch sử cổ phiếu | Chỉ có snapshot niêm yết/lưu hành hiện tại | HIGH cho snapshot | NOT_READY | Không có mốc thời gian hiệu lực/công bố hay lịch sử hoàn chỉnh |
| Thị trường hàng ngày | Có sẵn OHLC, đóng cửa/điều chỉnh, khối lượng/giá trị khớp lệnh & thỏa thuận | MEDIUM | SECONDARY_CANDIDATE | Price basis và chính sách tổng khối lượng/giá trị chưa giải quyết; tham chiếu/trần/sàn/trạng thái không có lịch sử |
| Hành động doanh nghiệp | Có sẵn danh sách sự kiện, bài viết và tài liệu nguồn | MEDIUM | SECONDARY_CANDIDATE | Ngày canonical và tỷ lệ chuẩn hoá chưa hoàn thiện |
| Báo cáo tài chính | Có sẵn KQKD, CĐKT, LCTT hàng quý/năm và các tài liệu | MEDIUM | NOT_READY | Mốc thời gian PIT, định danh/sửa đổi báo cáo, và ngữ nghĩa khoảng thời gian Q2/Q3 chưa giải quyết |
| Chỉ số Benchmark | Có sẵn các dòng chỉ số VNINDEX | MEDIUM | NOT_READY | Chưa ánh xạ sâu; quan sát thấy hành vi dòng rỗng/bất thường |
| Lịch giao dịch | Có sẵn thông báo nghỉ giao dịch HOSE năm 2026 | MEDIUM | NOT_READY | Chỉ ở dạng tài liệu, không phải lịch giao dịch cấu trúc của sàn |

## 16. Phụ lục bằng chứng (Evidence appendix)

Mọi quan sát dưới đây đều công khai và không yêu cầu đăng nhập/trả phí. Trừ khi có ghi chú khác, phương thức là GET, nội dung trang là HTML, thứ tự sắp xếp do trang định nghĩa, dấu thời gian không có múi giờ rõ ràng và không gặp lỗi truy cập/giới hạn tần suất nào.

| ID bằng chứng | URL trang UI | Host/path hoặc request công khai | Tham số quan trọng / Content type | Phân trang / Ngày / Thứ tự quan sát | Bằng chứng cụ thể đã dùng |
|---|---|---|---|---|---|
| E1 | `https://cafef.vn/du-lieu/hose/fpt-cong-ty-co-phan-fpt.chn` | `cafef.vn/du-lieu/hose/...`; JSON trang dưới `/du-lieu/Ajax/PageNew/` | `Symbol=fpt`; HTML + JSON do UI parse | Snapshot hiện tại | Ticker/tên/sàn FPT, giá hiện tại, trần/sàn, số lượng cổ phiếu, nhãn đồ thị điều chỉnh, tài chính tóm tắt |
| E2 | `https://cafef.vn/du-lieu/hose/fpt-thong-tin-co-ban.chn` | HTML profile render từ server | Không | Profile hiện tại | Ngành, ngày giao dịch đầu tiên, cổ phiếu niêm yết/lưu hành hiện tại, nhãn biểu đồ vốn |
| E3 | `https://cafef.vn/du-lieu/vnm/thong-tin-chung.chn` | HTML profile render từ server | symbol trong path | Profile hiện tại | Định danh VNM, HOSE, ngày giao dịch đầu tiên, cổ phiếu hiện tại |
| E4 | `https://cafef.vn/du-lieu/pvs/thong-tin-chung.chn` | HTML profile render từ server | symbol trong path | Profile hiện tại | Định danh PVS, HNX, ngày giao dịch đầu tiên, số cổ phiếu chênh lệch |
| E5 | `https://cafef.vn/du-lieu/acv/thong-tin-chung.chn` | HTML profile render từ server | symbol trong path | Profile hiện tại | Định danh ACV, UPCOM, ngày giao dịch đầu tiên, số cổ phiếu chênh lệch |
| E6 | Các route lịch sử FPT/VNM/PVS/ACV nêu tại mục 6 | `/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx` | `ExchangeType`, `Symbol`, `StartDate`, `EndDate`, `PageIndex`, `PageSize`; JSON | Bắt đầu từ 1, 20 dòng/trang, mới nhất trước, UI hiển thị rỗng rõ ràng | Key, nhãn, đơn vị, mẫu, kiểm tra khoảng ngày, hành vi khi rỗng |
| E7 | `https://cafef.vn/du-lieu/hose/fpt-tai-chinh.chn` | `apiweb.cafef.vn/api/v1/BCTC/GetReportSummary` | `symbol=FPT`, `pageIndex`, `pageSize=4`, `reportType`, `TypeTime`; JSON | 4 kỳ/trang; bộ chọn quý/năm/lũy kế | Tính sẵn có KQKD/CĐKT/LCTT, fact, hệ số chia đơn vị, sự chưa rõ ràng của LCTT Q2 |
| E8 | `https://cafef.vn/du-lieu/hose/vnm-tai-chinh.chn` | cùng họ API tài chính | `symbol=VNM`; JSON | Giống trên | Mức độ bao phủ tài chính quý VNM |
| E9 | `https://cafef.vn/du-lieu/hnx/pvs-tai-chinh.chn` | cùng họ API tài chính | `symbol=PVS`; JSON | Giống trên | Mức độ bao phủ tài chính quý PVS |
| E10 | `https://cafef.vn/du-lieu/upcom/acv-tai-chinh.chn` | cùng họ API tài chính | `symbol=ACV`; JSON | Giống trên | Mức độ bao phủ tài chính quý ACV |
| E11 | `https://cafef.vn/du-lieu/bao-cao-tai-chinh/fpt/bsheet/2024/0/-1/0/bao-cao-tai-chinh-.chn` | `cafef.vn/du-lieu/bao-cao-tai-chinh/...` | tham số đường dẫn loại báo cáo/năm; HTML | Giao diện 4 cột theo năm | Điều hướng báo cáo đầy đủ và cảnh báo sự không nhất quán đơn vị raw/hiển thị |
| E12 | `https://cafef.vn/du-lieu/hose/fpt-tai-lieu.chn` | HTML + link PDF công khai `cafefnew.mediacdn.vn/.../BCTC/...pdf` | bộ lọc năm/thể loại; link PDF không tải về | danh sách tài liệu mới nhất trước | Nhãn tài liệu hợp nhất/công ty mẹ, quý/năm, đã kiểm toán/soát xét |
| E13 | `https://cafef.vn/du-lieu/fpt-2893107/fpt-2852026-ngay-gdkhq-tra-co-tuc-con-lai-nam-2025-bang-tien-mat-1000-dcp.chn` | HTML bài viết + link PDF HOSE đính kèm | ID bài viết trong path | N/A | Loại cổ tức tiền mặt FPT, dấu thời gian bài viết, ngày GDKHQ, số tiền, tham chiếu nguồn |
| E14 | `https://cafef.vn/du-lieu/DuLieu.aspx?cat_id=1009&san=hose&symbol=FPT` | HTML | `cat_id`, `san`, `symbol` | danh sách sự kiện mới nhất trước | Lịch sử sự kiện FPT và ghi chú rõ ràng về ngày GDKHQ/ngày phát hành |
| E15 | `https://cafef.vn/du-lieu/lich-su-gia/vnindex.chn` | cùng họ request lịch sử thị trường | `Symbol=VNINDEX` | mới nhất trước; quan sát thấy dòng ngày hiện tại chưa đầy đủ | Tính sẵn có của mức chỉ số VNINDEX lịch sử |
| E16 | `https://cafef.vn/du-lieu/hose-2876128/hose-thong-bao-lich-nghi-giao-dich-nam-2026.chn` | HTML bài viết + PDF công khai | ID bài viết trong path | N/A | Ngày nghỉ giao dịch cụ thể năm 2026 của HOSE; bằng chứng lịch dạng tài liệu |
| E17 | `https://cafef.vn/du-lieu/cong-bo-thong-tin.chn` | HTML | bộ lọc mã, đơn vị, khoảng thời gian gửi, loại báo cáo | bảng kết quả | Các khái niệm bộ lọc thời gian công bố, phạm vi báo cáo, kiểm toán; không đưa dòng FPT nào lên |
| E18 | `https://cafef.vn/robots.txt` | GET `text/plain` | Không | N/A | `User-agent: *`, `Allow: /`, sitemaps |
| E19 | `https://cafef.vn/static/chinh-sach-bao-mat.html` | GET `text/html` | Không | N/A | Chính sách bảo mật/cookie; không có giấy phép tự động hóa |

Việc mở trực tiếp các URL JSON riêng lẻ bị chặn bởi trình duyệt nội bộ local của app, không phải do phản hồi 401/403 từ CafeF. Cấu trúc request JSON thay vào đó được quan sát từ logic trang công khai và các giá trị được đối chiếu với UI hiển thị. Hạn chế trình duyệt local này không được xếp vào loại bị chặn truy cập nguồn.

## 17. Trạng thái phê duyệt (Approval state)

| Hạng mục | Trạng thái |
|---|---|
| Vòng đời (Lifecycle) | `ACCESS_TESTED` |
| Ngữ nghĩa thị trường | PARTIAL; trường và đơn vị đã tìm thấy, price basis chưa giải quyết |
| Ngữ nghĩa tài chính | PARTIAL; tính sẵn có/nhãn đơn vị đã tìm thấy, PIT và ngữ nghĩa khoảng thời gian chưa giải quyết |
| Quyền hạn (Rights) | `NOT_VERIFIED` |
| Cho phép làm Adapter tiếp theo | YES, dành cho bản triển khai giới hạn chỉ ánh xạ các trường đã xác minh và fail closed cho mọi domain/trường chưa giải quyết |
| Cho phép làm Source Smoke tiếp theo | NO |

Ghi chú phê duyệt:

- Bản triển khai tiếp theo có thể mã hóa cấu trúc request công khai và định danh/metadata tài liệu đã xác minh trong khi **cố tình để trống** (unmapped) đối với fact giá, lịch sử cổ phiếu, dòng canonical sự kiện doanh nghiệp và fact PIT tài chính.
- Adapter phải duy trì cơ chế fail-closed đối với `SOURCE_SMOKE` thực tế cho đến khi các trường smoke dự định, price basis, hành vi múi giờ/thời điểm công bố và quyền hạn được xác minh đầy đủ.
- Không cấp trạng thái `PILOT_APPROVED` hay `PRODUCTION_APPROVED`.
