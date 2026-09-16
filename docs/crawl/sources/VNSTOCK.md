# Source Note — Vnstock Data V2

## 1. Trạng thái vòng đời (Lifecycle status)

```text
ACCESS_TESTED
```

KBS, nhà cung cấp chính phía sau Vnstock trong phạm vi này, đã được access-test bằng một số request công khai rất nhỏ cho đúng bốn mã FPT, VNM, PVS, ACV và VNINDEX. Một số ngữ nghĩa quan trọng đã được xác minh, nhưng nguồn chưa đạt `SEMANTICS_VERIFIED`: quyền tự động hóa dữ liệu của nhà cung cấp chưa được xác minh, lịch sử số lượng cổ phiếu chưa có, sự kiện doanh nghiệp trả về rỗng, giá tham chiếu/trần/sàn lịch sử chưa có, và ngữ nghĩa Lưu chuyển tiền tệ Q2/Q3 còn chưa rõ.

Trạng thái này không làm thay đổi `src/delta_t1/ingestion/sources/vnstock.py`; adapter hiện tại vẫn giữ nguyên và không được phê duyệt trong task này.

## 2. Phạm vi và ngày khám phá (Discovery scope and date)

- Ngày khám phá: **2026-09-16** (`Asia/Saigon`).
- Client thu thập: **Vnstock**.
- Nhà cung cấp chính: **KBS** (KB Securities Vietnam / KBSV host `kbbuddywts.kbsec.com.vn`).
- Nhà cung cấp thay thế được thử nghiệm: **NONE**.
- Các mã cổ phiếu: FPT (HOSE), VNM (HOSE), PVS (HNX), ACV (UPCOM).
- Phân hệ (Domains): định danh chứng khoán, cổ phiếu/vốn, thị trường hàng ngày, sự kiện doanh nghiệp, báo cáo tài chính, VNINDEX, hỗ trợ lịch giao dịch, xuất xứ (provenance) và quyền hạn.
- Không thực hiện: crawl tập dữ liệu, `SOURCE_SMOKE`, chạy test suite, `compileall`, synthetic smoke hay product build.

Bối cảnh phiên bản (Version context):

| Hạng mục | Quan sát | Hệ quả |
|---|---|---|
| Bản phát hành PyPI công khai mới nhất | `vnstock 4.0.8`, phát hành 2026-09-15 | Đây là phiên bản công khai hiện tại tại ngày khám phá. |
| Nhãn tài liệu cộng đồng | `vnstock v4.0.6` | Tài liệu có thể cập nhật chậm hơn bản phát hành PyPI. |
| Kỳ vọng của adapter repository | `vnstock 4.0.6` | Đây là phiên bản được ghim (pin) trong code hiện tại. |
| Môi trường Python local | package `vnstock` không được cài | Không có gọi SDK live; access test dùng các endpoint/phương thức công khai do nguồn Vnstock hiện tại khai báo. |

## 3. Client thu thập Vnstock vs Nhà cung cấp bên dưới (Vnstock client vs underlying providers)

Vnstock là client/wrapper thu thập dữ liệu, không phải nhà cung cấp dữ liệu (data provider). Provenance tối thiểu của Data V2 phải là:

```json
{
  "provider": "kbs",
  "acquisition_client": "vnstock"
}
```

README chính thức của Vnstock mô tả các request chạy từ hạ tầng của người dùng tới nguồn bên thứ ba và liệt kê KBS cho `Reference`, `Market` và `Fundamental`. Mã nguồn công khai của Vnstock khai báo rõ các host/path của KBS, ánh xạ trường raw và phép chuyển đổi. Vì vậy **không được** ghi `source=vnstock` làm xuất xứ duy nhất.

Một manifest raw trong tương lai có thể và nên lưu tối thiểu:

| Trường manifest bắt buộc | Tính khả thi | Ghi chú |
|---|---|---|
| `provider` | YES | `kbs` từ routing nhà cung cấp và host endpoint. |
| `acquisition_client` | YES | `vnstock`. |
| `provider_endpoint_or_method` | YES | Ví dụ `GET /iis-server/investment/stocks/{symbol}/data_day` và `Market().equity(...).ohlcv(...)`. |
| `symbol` | YES | Đường dẫn request và response đều chứa symbol. |
| `date_range` | YES | `sdate`, `edate`; không áp dụng cho snapshot. |
| `fetched_at` | YES | Ghi tại ranh giới ingestion, múi giờ UTC. |
| `client_version` | YES | Phải ghi phiên bản thực tế, không chỉ phiên bản kỳ vọng. |
| `provider/raw response hash` | YES | Hash các byte của response raw trước khi normalize; adapter repository hiện tại chưa lưu response này. |

Adapter repository hiện tại lưu snapshot và metadata dạng SDK, không phải HTTP wire response của nhà cung cấp. Checksum file sau khi ghi không thay thế được raw response hash.

## 4. Lý do lựa chọn nhà cung cấp (Provider selection rationale)

KBS được chọn làm `PRIMARY_PROVIDER` vì:

1. Repository cũ đã sử dụng `source="kbs"` thành công.
2. Cấu trúc API Vnstock hiện tại vẫn điều hướng KBS cho OHLCV cổ phiếu/chỉ số, bảng giá, profile công ty/lịch sử vốn và báo cáo tài chính.
3. Các endpoint KBS công khai khai báo trong nguồn Vnstock trả về dữ liệu cho cả HOSE, HNX và UPCOM trong các đợt kiểm tra live có giới hạn.
4. KBS không bị chặn bởi đăng nhập, CAPTCHA hay thách thức truy cập trong các request đã thực hiện.

Không thử nghiệm nhà cung cấp thay thế vì nhà cung cấp chính vẫn truy cập được và cung cấp mức độ bao phủ có ý nghĩa cho các phân hệ thị trường và tài chính quan trọng. Việc thử nghiệm nhà cung cấp thứ hai chỉ để "cho đủ" sẽ đi ngược lại ranh giới sử dụng của task.

## 5. Quyền sở hữu / Truy cập / Quyền hạn (Ownership / access / rights)

| Cấp độ | Chủ sở hữu / Đơn vị vận hành | Ghi nhận truy cập | Quyền tự động hóa | Bằng chứng / Hạn chế |
|---|---|---|---|---|
| Client thu thập | Vnstock | Tài liệu công khai, repository nguồn công khai và metadata package PyPI | **RESTRICTED** | Giấy phép custom source-available; có các điều kiện về phạm vi, quota/tier và sử dụng bị cấm. Giấy phép phần mềm không cấp quyền dữ liệu. |
| Nhà cung cấp bên dưới | KBS / KBSV | Các endpoint JSON công khai không cần xác thực; không đăng nhập, cookie hay token | **NOT_VERIFIED** | Không tìm thấy chính sách công khai nào của KBS cấp quyền tự động hóa, lưu trữ, phân phối lại hay tái sử dụng sản xuất cho các endpoint này. Truy cập công khai không phải là sự phép. |

Các bước kiểm tra không sử dụng cookie, header xác thực, token riêng tư, session ID, proxy, xoay IP hay vượt qua rào cản chống bot. Không kiểm tra giới hạn tần suất tải (rate test). `SOURCE_SMOKE` chưa được phép vì quyền dữ liệu của nhà cung cấp vẫn là `NOT_VERIFIED`.

## 6. Định danh chứng khoán (Security identity)

### Quan sát thực tế

| Trường nhà cung cấp | Ý nghĩa | Mẫu | Ứng viên Canonical | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|---|
| `SB` | Ticker hiện tại | FPT → `FPT` | `ticker` | Response profile và response bảng giá đồng nhất | HIGH |
| `EX` | Nhãn sàn hiện tại | FPT `HOSE`; PVS `HNX`; ACV `UPCoM`/`UPCOM` | `exchange` sau khi chuẩn hóa chữ hoa | Đối chiếu profile + bảng giá | HIGH |
| `LD` | Nhãn ngày niêm yết | FPT `13/12/2006`; ACV `21/11/2016` | `listing_date` sau khi parse `DD/MM/YYYY` | Response profile + ánh xạ Vnstock hiện tại | HIGH |
| `CompanyID` | Mã công ty KBS trong header tài chính | FPT `191` | Chỉ là ứng viên `provider_security_id` | Một response tài chính; chưa chứng minh tính duy nhất/ổn định/ngữ nghĩa chứng khoán vs công ty | LOW |
| `name` / `nameEn` | Tên công ty trong route danh sách tất cả mã của KBS | Route có trong tài liệu, không gọi vì trả về toàn thị trường | `company_name` | Chỉ dựa vào tài liệu nguồn Vnstock hiện tại, không có mẫu live chính xác cho từng mã | LOW |
| Mã/Tên ngành KBS | Phân nhóm ngành riêng của nhà cung cấp | Không kiểm tra live | Chỉ là ứng viên `industry` | Nguồn hiện tại nêu đây không phải phân loại ICB | LOW |

### Mức độ bao phủ mã (Symbol coverage)

| Mã | Sàn yêu cầu | Sàn quan sát trên profile | Tìm thấy ngày niêm yết | Ghi chú |
|---|---|---|---|---|
| FPT | HOSE | HOSE | YES | Profile và thị trường đều trả dữ liệu. |
| VNM | HOSE | HOSE | YES | Profile và thị trường đều trả dữ liệu. |
| PVS | HNX | HNX | YES | Profile và thị trường đều trả dữ liệu. |
| ACV | UPCOM | UPCoM/UPCOM | YES | Chỉ cần chuẩn hóa cách viết/chữ hoa; không đổi ngữ nghĩa sàn. |

Không tìm thấy ngữ nghĩa đủ để ánh xạ `sector`, phân loại ngành lịch sử, `delisting_date`, `listing_status`, `ticker_history` hay `exchange_history`. Profile hiện tại không được dùng để suy ra định danh lịch sử.

## 7. Cổ phiếu / Cấu trúc vốn (Shares / capital structure)

**Trạng thái nhà cung cấp: CURRENT_SNAPSHOT_ONLY**

### Snapshot hiện tại

| Trường nhà cung cấp | Ý nghĩa | Dữ liệu mẫu | Ứng viên Canonical | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|---|
| Price-board `LS` | Cổ phiếu niêm yết | FPT `1,714,326,422`; VNM `2,089,955,445`; PVS `511,420,099`; ACV `3,582,847,523` | Snapshot `listed_shares` hiện tại | Nguồn hiện tại ánh xạ `LS → listed_shares`; một response công khai cho cả 4 mã | HIGH |
| Price-board `TLQ` | Tổng khối lượng niêm yết | Bằng `LS` trong 4 mẫu | Unmapped | Tên trường khác `LS`; bằng nhau trong mẫu không chứng minh đồng nghĩa | LOW |
| Profile `VL` | Khối lượng niêm yết | FPT `1714`; VNM `2090`; PVS `511`; ACV `3583` | Unmapped | Đơn vị/làm tròn không rõ ràng; không suy hệ số nhân từ độ lớn | LOW |
| Profile `KLCPLH` | Cổ phiếu lưu hành theo ánh xạ nguồn hiện tại | Không xuất hiện trong 4 response profile live | Ứng viên `outstanding_shares` | Ánh xạ tồn tại trong nguồn, tính sẵn có live chưa được xác nhận | LOW |

`LS` và `TLQ` không được giả định bằng nhau về ngữ nghĩa chỉ vì 4 giá trị hiện tại trùng nhau. Không suy `issued_shares`, `outstanding_shares` hay `treasury_shares` bằng phép trừ.

### Lịch sử vốn điều lệ không phải lịch sử số lượng cổ phiếu

Profile trả về `CharterCapital[{D,V,C}]` cho cả 4 mã:

| Mã | Số điểm dữ liệu vốn quan sát được | Điểm dữ liệu gần nhất quan sát được |
|---|---:|---|
| FPT | 26 | `09/07/2026`, `17,413,264,220,000 VNĐ` |
| VNM | 14 | `28/10/2020`, `20,899,554,450,000 VNĐ` |
| PVS | 8 | `12/01/2026`, `5,114,200,990,000 VNĐ` |
| ACV | 2 | `15/08/2025`, `35,828,475,230,000 VNĐ` |

Đây là lịch sử vốn điều lệ (charter-capital history), không phải chuỗi lịch sử số lượng cổ phiếu đã xác minh. Không chia cho mệnh giá để tạo lịch sử cổ phiếu vì sự thay đổi mệnh giá, mốc thời gian sự kiện và thời điểm công bố chưa được chứng minh. `D` có thể là ngày hiệu lực/cập nhật của bản ghi vốn nhưng không có dấu thời gian công bố rõ ràng. Do đó:

- Chuỗi lịch sử số lượng cổ phiếu: **NOT FOUND**.
- `effective_date`: chỉ có ứng viên `D` cho vốn điều lệ, không phải cổ phiếu canonical.
- `published_at` / `available_at`: **NOT FOUND**.
- `issued_shares`, `treasury_shares`: **NOT FOUND**.

## 8. Dữ liệu thị trường hàng ngày (Daily market data)

### Lịch sử OHLCV

Endpoint raw của KBS trả về `data_day` cho cả 4 mã, với cửa sổ chính xác 2 ngày `2025-01-02..2025-01-03`.

| Trường nhà cung cấp | Ý nghĩa | Đơn vị nguồn | Mục tiêu Canonical | Chuyển đổi (Transform) | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|---|---|
| `t` | Dấu thời gian/ngày nến | Chuỗi ngày `YYYY-MM-DD 07:00` | `trade_date` | Lấy ngày lịch; không gán múi giờ | Response 4 mã + ánh xạ hiện tại | HIGH cho ngày; LOW cho múi giờ |
| `o` | Giá mở cửa điều chỉnh | KBS raw: VNĐ/cổ phiếu | `open` VNĐ/cổ phiếu | Nếu qua DataFrame Vnstock: `value * 1000`; endpoint raw: giữ nguyên | Nguồn chia cổ phiếu cho 1000; tài liệu chính thức dán nhãn điều chỉnh kỹ thuật | HIGH |
| `h` | Giá cao nhất điều chỉnh | KBS raw: VNĐ/cổ phiếu | `high` VNĐ/cổ phiếu | Giống `o` | Giống trên | HIGH |
| `l` | Giá thấp nhất điều chỉnh | KBS raw: VNĐ/cổ phiếu | `low` VNĐ/cổ phiếu | Giống `o` | Giống trên | HIGH |
| `c` | Giá đóng cửa điều chỉnh | KBS raw: VNĐ/cổ phiếu | `close` VNĐ/cổ phiếu | Giống `o` | Giống trên | HIGH |
| `v` | Khối lượng hàng ngày | cổ phiếu | `volume` cổ phiếu | Giữ nguyên | Response công khai + docs OHLCV | HIGH |

Dữ liệu mẫu (giá trị nhà cung cấp raw, không phải toàn bộ lịch sử):

| Mã | Ngày | Mở cửa | Cao nhất | Thấp nhất | Đóng cửa | Khối lượng |
|---|---|---:|---:|---:|---:|---:|
| FPT | 2025-01-03 | 127392 | 127392 | 125456 | 125456 | 4,336,100 |
| VNM | 2025-01-03 | 56550 | 56640 | 56282 | 56372 | 1,776,700 |
| PVS | 2025-01-03 | 26489 | 26723 | 26411 | 26489 | 2,252,344 |
| ACV | 2025-01-03 | 77272.2192 | 77697.4594 | 74842.2752 | 75024.5210 | 563,556 |

### Chỉ dành cho Snapshot phiên hiện tại

Một request `POST /stock/iss` công khai cho 4 mã trả về các trường sau. Đây là snapshot tại thời điểm request, không phải chuỗi lịch sử theo ngày.

| Trường nhà cung cấp | Ý nghĩa | Đơn vị nguồn | Mục tiêu Canonical | Độ sẵn sàng | Độ tin cậy |
|---|---|---|---|---|---|
| `RE` | Giá tham chiếu | VNĐ/cổ phiếu | `reference_price` | Sẵn sàng cho snapshot; CHƯA sẵn sàng cho lịch sử ngày | HIGH |
| `CL` | Giá trần | VNĐ/cổ phiếu | `ceiling_price` | Chỉ cho snapshot | HIGH |
| `FL` | Giá sàn | VNĐ/cổ phiếu | `floor_price` | Chỉ cho snapshot | HIGH |
| `OP`,`HI`,`LO`,`CP` | Giá mở/cao/thấp/hiện tại trong phiên | VNĐ/cổ phiếu | Các trường phiên | Không thay thế nến hàng ngày | HIGH |
| `TT` | Khối lượng khớp lệnh lũy kế | cổ phiếu | Ứng viên `matched_volume` | Chỉ snapshot; changelog nguồn sửa nhãn từ `total_trades` | HIGH |
| `TV` | Tổng giá trị lũy kế | VNĐ | Ứng viên `traded_value` | Chỉ snapshot | HIGH |
| `CV` | Khối lượng khớp gần nhất | cổ phiếu | Không phải khối lượng ngày | Không ánh xạ sang volume hàng ngày | HIGH |
| `PTQ` | Khối lượng thỏa thuận | cổ phiếu | Ứng viên `put_through_volume` | Chỉ snapshot | MEDIUM |
| `PTV` | Giá trị thỏa thuận | VNĐ | Ứng viên `put_through_value` | Chỉ snapshot | MEDIUM |
| `MS` | Mã trạng thái thị trường/giao dịch | Mã (`O`, `5` quan sát được) | `trading_status` | Từ điển mã chưa xác minh; không ánh xạ | LOW |
| `t` | Dấu thời gian snapshot | Unix miligiây | Ứng viên `observed_at` | Ngữ nghĩa múi giờ/đồng hồ nguồn chưa có tài liệu | LOW |

Các trường lịch sử `reference_price`, `ceiling_price`, `floor_price`, `traded_value`, `trading_status`, phân rã khớp lệnh vs thỏa thuận không xuất hiện trong các response `data_day` được kiểm tra. Changelog phiên bản Community hiện tại ghi nhận việc lấy dữ liệu thỏa thuận thuộc bản mở rộng. Không đưa các trường snapshot lên làm lịch sử hàng ngày.

## 9. Cơ sở giá (Price basis)

```text
VENDOR_ADJUSTED
```

Tài liệu Vnstock Data chính thức mô tả `Quote.history` lịch sử là "đã được điều chỉnh kỹ thuật (adjusted price)" để sử dụng cho biểu đồ kỹ thuật. Đường dẫn nguồn KBS hiện tại và các response trực tiếp có giới hạn khớp với đường dẫn đó. Do đó, kết luận từ hệ thống cũ về lịch sử giá đã điều chỉnh được **XÁC MINH LẠI (RE-VERIFIED)** ở mức nhãn của nhà cung cấp.

Hạn chế:

- Không có chuỗi hệ số điều chỉnh (adjustment factor) hay phương pháp luận của nhà cung cấp.
- Không chứng minh được việc điều chỉnh bao gồm cổ tức tiền mặt, chỉ chia tách/thưởng, hay sự kết hợp nào.
- Không được gọi là `SPLIT_ADJUSTED` hay `TOTAL_RETURN`.
- Các trường snapshot `RE/CL/FL/OP/HI/LO/CP` là dữ liệu phiên hiện tại và không được tự động trộn với các nến lịch sử đã điều chỉnh.

## 10. Thời gian / Múi giờ / Độ sẵn sàng (Time / timezone / availability)

- `data_day.t` có dạng `YYYY-MM-DD 07:00`; múi giờ không được response hay tài liệu khai báo. Chỉ có `trade_date` được xác minh.
- `sdate` và `edate` dùng dạng `DD-MM-YYYY`. Lần kiểm tra 2 ngày trả về cả ngày bắt đầu và ngày kết thúc, do đó ranh giới quan sát được là bao gồm/bao gồm (inclusive/inclusive) cho các mẫu này.
- Nhà cung cấp trả về mới nhất xếp trước; client Vnstock hiện tại sắp xếp tăng dần theo `time`.
- Snapshot `t` là Unix miligiây nhưng hành vi múi giờ/đồng hồ nguồn chưa được định nghĩa.
- Các trường tài chính `ReportDate`, `CreatedDate`, `DatePubDepartment`, `LastUpdate` là các chuỗi ISO không chứa múi giờ; không tự gán UTC/Asia-Saigon khi chưa có tài liệu.
- Tài liệu công khai nêu window lịch sử hàng ngày cấp client có thể lên tới 8 năm; chưa kiểm chứng giới hạn tối đa của provider và không probe sâu.
- Không đo độ trễ latency hay độ trễ công bố sau khi đóng cửa phiên.

## 11. Quyền mua & Cổ tức / Hành động doanh nghiệp (Corporate actions)

Nguồn Vnstock hiện tại có phương thức `Reference.company.events()` điều hướng KBS và schema ứng viên bao gồm ID/loại sự kiện, `public_date`, `exright_date`, `record_date`, `issue_date`, `payout_date`, tỷ lệ và giá trị mỗi cổ phiếu.

Tuy nhiên, request live `GET /stockinfo/event/{symbol}?l=1&p=1&s=10` trả về mảng rỗng cho **cả 4 mã FPT, VNM, PVS và ACV**. Tài liệu hiện tại cũng cảnh báo sự kiện KBS có thể rỗng đối với các mã phổ biến.

Kết luận:

- Tính sẵn có: **NOT_READY**.
- Ví dụ FPT: **NOT FOUND**.
- `event_id`, loại sự kiện, ngày thông báo/GDKHQ/đăng ký/hiệu lực/thanh toán, số tiền tiền mặt, tỷ lệ cổ phiếu/thưởng, tỷ lệ quyền mua, giá phát hành, tài liệu nguồn, bản sửa đổi: **không có trường nào được xác minh bằng bản ghi sự kiện live**.
- Không tính toán hệ số điều chỉnh.

## 12. Báo cáo tài chính (Financial statements)

### Tính sẵn có

| Domain | FPT | VNM | PVS | ACV | Bằng chứng |
|---|---|---|---|---|---|
| Kết quả kinh doanh quý | YES | YES | YES | YES | `termtype=2`, trang 1, một kỳ |
| Kết quả kinh doanh năm | YES | NOT_CHECKED | NOT_CHECKED | NOT_CHECKED | FPT `termtype=1` |
| Bảng cân đối kế toán quý | YES | NOT_CHECKED | NOT_CHECKED | NOT_CHECKED | FPT `CDKT` |
| Bảng cân đối kế toán năm | YES | NOT_CHECKED | NOT_CHECKED | NOT_CHECKED | FPT `CDKT` |
| Lưu chuyển tiền tệ quý | CẤU TRÚC CÓ, GIÁ TRỊ Q2 RỖNG | NOT_CHECKED | NOT_CHECKED | NOT_CHECKED | FPT `LCTT` |
| Lưu chuyển tiền tệ năm | YES | NOT_CHECKED | NOT_CHECKED | NOT_CHECKED | FPT `LCTT` |

### Ngữ nghĩa metadata

| Trường nhà cung cấp | Ý nghĩa quan sát được | Ứng viên Canonical | Bằng chứng | Độ tin cậy |
|---|---|---|---|---|
| `CompanyID` | Mã công ty KBS | Ứng viên `provider_security_id` | Header FPT | LOW |
| `YearPeriod` | Năm tài chính/báo cáo | `fiscal_year` | 2025 năm, 2026 quý | HIGH |
| `TermCode` / `TermName` | `N`, `Q2`, "Năm", "Quý 2" | `fiscal_quarter` / Cờ năm | Header trực tiếp | HIGH |
| `PeriodBegin` | Tháng bắt đầu `YYYYMM` | Ứng viên `period_start` | FPT Q2 `202604` | HIGH |
| `PeriodEnd` | Tháng kết thúc `YYYYMM` | Ứng viên `period_end` | FPT Q2 `202606` | HIGH |
| `United` | Mã phạm vi báo cáo | `statement_scope` | `HN`; từ điển phân biệt ghi "Hợp nhất/Consolidated" | HIGH |
| `AuditedStatus` | Mã trạng thái kiểm toán | `audit_status` | `KT`, `SX`, `CKT` kèm từ điển response | HIGH |
| `ReportDate` | Ngày báo cáo dán nhãn bởi nhà cung cấp | Chỉ metadata | Trường rõ ràng, ý nghĩa PIT chưa định nghĩa | MEDIUM |
| `DatePubDepartment` | Ngày công bố phòng ban | Ứng viên `published_at` | Có mặt trên tất cả các header Q2 được kiểm tra | MEDIUM |
| `CreatedDate` | Dấu thời gian tạo bản ghi | Chỉ là ứng viên `available_at` | Có mặt; không có định nghĩa sẵn có rõ ràng | LOW |
| `LastUpdate` | Dấu thời gian cập nhật gần nhất | Ứng viên bản sửa đổi | Có mặt; không có ID sửa đổi/cờ điều chỉnh lại | LOW |
| `ReportTermID` | Mã loại kỳ | Không phải ID báo cáo | Lặp lại theo kỳ; không đủ làm `provider_report_id` | HIGH |

PIT tài chính vẫn ở mức **PARTIAL**. Không đưa `CreatedDate`, `DatePubDepartment` hay `LastUpdate` lên làm `available_at` canonical trước khi ngữ nghĩa nhà cung cấp được xác nhận.

### Tiền tệ và quy mô đơn vị

Client KBS hiện tại gửi `unit=1000` ("ngàn đồng") và nhân giá trị response với `1000.0`. Pipeline ứng viên:

`Giá trị KBS ValueN (nghìn VNĐ) × 1.000 → canonical VNĐ`

Mã nguồn và hợp đồng request hỗ trợ phép chuyển đổi này, nhưng một số dòng live có `Unit=null`. Do đó phép chuyển đổi số có độ tin cậy **HIGH** cho đường dẫn client KBS hiện tại; nhãn tiền tệ có độ tin cậy **MEDIUM** và phải lưu metadata đơn vị raw.

### Ngữ nghĩa Q2/Q3 quan trọng

Kết quả kinh doanh (Income Statement):

- Header Q2 2026 cho cả 4 mã ghi `TermCode=Q2`, `PeriodBegin=202604`, `PeriodEnd=202606`; đây là metadata trực tiếp hỗ trợ **STANDALONE_QUARTER** cho Q2 được kiểm tra.
- Mẫu Q3 hiện tại chưa được xác minh. Phân trang nhẹ cho FPT cho thấy header Q4 bị lặp/trộn lẫn ở trang 4/5, đúng với cảnh báo trong nguồn client hiện tại; việc khám phá dừng lại thay vì duyệt vét toàn bộ trang.
- Kết quả chung Q2/Q3: **UNKNOWN — DO NOT MAP YET**.

Lưu chuyển tiền tệ (Cash Flow):

- Header Q2 FPT được kiểm tra cũng ghi `202604..202606`, nhưng tất cả các giá trị `Value1` được kiểm tra đều null.
- Q3 chưa được quan sát.
- Kết quả: **UNKNOWN — DO NOT MAP YET**.

Không dùng tính toán số học để suy đoán độc lập/lũy kế.

### Ứng viên raw-fact

| Nhóm | Các ứng viên tìm thấy / hỗ trợ | Chưa được xác minh đầy đủ |
|---|---|---|
| Kết quả kinh doanh | Doanh thu, giá vốn, lợi nhuận gộp live; các ánh xạ hiện tại cũng mở lợi nhuận hoạt động, LNTT, LNST, chi phí bán hàng/quản lý, EPS | Chi phí lãi vay, thuế TNDN, LNST công ty mẹ, EPS suy giảm |
| Cân đối kế toán | Tiền/tương đương tiền live; ánh xạ hiện tại bao phủ tài sản ngắn hạn, tổng tài sản, nợ ngắn hạn, tổng nợ phải trả, nợ dài hạn, vốn chủ sở hữu, LNST chưa phân phối | Phải thu, hàng tồn kho, nợ vay ngắn hạn, nợ vay dài hạn dạng nợ vay, dòng TSCĐ chính xác |
| Lưu chuyển tiền tệ | Mẫu năm có LNTT và khấu hao; ánh xạ hiện tại bao phủ CFO, CFI, CFF, lưu chuyển tiền thuần, tiền đầu/cuối kỳ | Ngữ nghĩa khoảng thời gian Q2/Q3, capex, cổ tức đã trả |
| Chỉ tiêu theo cổ phiếu | Không có | Cổ phiếu bình quân lưu hành tính EPS cơ bản/suy giảm |

`long_term_liabilities` không được ánh xạ thành `long_term_debt`. Cổ phiếu cuối kỳ không thay thế cổ phiếu bình quân.

## 13. Chỉ số Benchmark / Lịch giao dịch (Benchmark / trading-calendar availability)

| Domain | Trạng thái | Bằng chứng | Hạn chế |
|---|---|---|---|
| Mức chỉ số VNINDEX lịch sử | **AVAILABLE** | Request `GET /index/VNINDEX/data_day` KBS công khai trả về OHLCV 2 ngày 2025-01-02 và 2025-01-03; client hiện tại giữ giá chỉ số theo điểm | Phương pháp luận chỉ số giá vs tổng lợi nhuận và thời điểm công bố chính thức chưa xác minh |
| Lịch giao dịch sàn KBS rõ ràng | **NOT_FOUND** | Không thấy phương thức lịch nhà cung cấp nào | Không tự suy ra phiên giao dịch từ các nến bị thiếu |
| Từ điển sự kiện thị trường client Vnstock | **AVAILABLE** | Changelog hiện tại mô tả các ngày nghỉ lễ, sự cố hệ thống, tạm ngừng toàn bộ/một phần từ năm 2000 | Từ điển mở do client tự duy trì, không phải lịch chính thức của HOSE/HNX/UPCOM và không phải lịch tương lai |

Độ sẵn sàng của lịch giao dịch do đó ở mức **PARTIAL** tại cấp độ client và **NOT_FOUND** tại cấp độ nhà cung cấp.

## 14. Request / Phân trang chia chunk / Phản ứng Rate (Request / chunking / rate behavior)

| Domain | Phương thức / host/path | Tham số quan trọng (không bảo mật) | Dạng / Cấu trúc Content | Phân trang / Khoảng ngày | Thứ tự / Hành vi khi rỗng | Hành vi truy cập |
|---|---|---|---|---|---|---|
| Cổ phiếu ngày | `GET kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_day` | `sdate`, `edate` | JSON công khai gồm `symbol`, `data_day[]` | Không có tham số trang; kiểm tra 2 ngày bao hàm cả 2 đầu | Provider xếp mới nhất trước; client sắp xếp tăng dần; client báo lỗi khi thiếu/rỗng | Không đăng nhập/thách thức trong 4 mã kiểm tra |
| VNINDEX | `GET .../index/VNINDEX/data_day` | `sdate`, `edate` | JSON công khai | Giống cổ phiếu | Giống trên | Không có thách thức |
| Bảng giá | `POST .../stock/iss` | Danh sách `code` dạng JSON | Mảng JSON công khai | Snapshot; không phân trang | Một dòng/mã trong kiểm tra | Không có thách thức |
| Profile/Vốn | `GET .../stockinfo/profile/{symbol}` | `l=1` | JSON công khai | Không phân trang | Thứ tự `CharterCapital[]` có vẻ mới nhất trước; không đảm bảo | Không có thách thức |
| Sự kiện doanh nghiệp | `GET .../stockinfo/event/{symbol}` | `l`, `p`, `s`, tùy chọn `eID` | Mảng JSON công khai | Trang + size trang | Mảng rỗng cho cả 4 mã | Không có thách thức |
| Báo cáo tài chính | `GET .../stock/finance-info/{symbol}` | `type`, `termtype`, `page`, `pageSize`, `unit`, `languageid`; lưu chuyển tiền thêm `code`, `termType` | JSON công khai `Audit/Unit/Head/Content` | Client hiện tại dùng page size 1 do lỗi lặp/trộn trang của provider | Kỳ gần nhất xếp trước; thấy tiêu đề Q4 lặp lại khi kiểm tra trang | Không có thách thức |

Adapter repository hiện tại chia chunk OHLCV theo 180 ngày lịch. Đây là lựa chọn triển khai trong code hiện tại, không phải giới hạn tối đa của nhà cung cấp đã được xác minh. Nguồn công khai hiện tại có đường dẫn request `start/end` trực tiếp. Không thực hiện probe số dòng/khoảng ngày tối đa hoặc trần giới hạn rate. Chính sách client Vnstock công khai nêu tốc độ cho tài khoản guest/community, nhưng giới hạn rate riêng của provider chưa được xác minh.

## 15. Mappings đã xác minh (Verified mappings)

| Provider | Client thu thập | Trường nhà cung cấp | Ứng viên Canonical | Chuyển đổi / Điều kiện | Độ tin cậy |
|---|---|---|---|---|---|
| KBS | vnstock | Profile `SB` | `ticker` | Chữ hoa | HIGH |
| KBS | vnstock | Profile/bảng giá `EX` | `exchange` hiện tại | Chỉ chuẩn hóa `UPCoM` → `UPCOM` | HIGH |
| KBS | vnstock | Profile `LD` | `listing_date` | Parse `DD/MM/YYYY` | HIGH |
| KBS | vnstock | Bảng giá `LS` | `listed_shares` hiện tại | Số nguyên, chỉ snapshot | HIGH |
| KBS | vnstock | Ngày `t` | `trade_date` | Chỉ ngày lịch | HIGH |
| KBS | vnstock | Ngày `o/h/l/c` qua Vnstock | OHLC VNĐ/cổ phiếu | Nhân giá trị chuẩn hóa Vnstock với 1.000; basis=`VENDOR_ADJUSTED` | HIGH |
| KBS | vnstock | Ngày `v` | `volume` cổ phiếu | Giữ nguyên | HIGH |
| KBS | vnstock | Bảng giá `RE/CL/FL` | tham chiếu/trần/sàn | Giữ nguyên VNĐ; chỉ snapshot | HIGH |
| KBS | vnstock | Bảng giá `TV` | Ứng viên giá trị giao dịch | Giữ nguyên VNĐ; chỉ snapshot | HIGH |
| KBS | vnstock | Tài chính `YearPeriod`, `TermCode` | năm/quý tài chính | Parse nhãn rõ ràng | HIGH |
| KBS | vnstock | Tài chính `PeriodBegin/PeriodEnd` | bắt đầu/kết thúc kỳ | Parse `YYYYMM`; chỉ ranh giới tháng | HIGH |
| KBS | vnstock | Tài chính `United` | phạm vi báo cáo | Giải mã qua từ điển response | HIGH |
| KBS | vnstock | Tài chính `AuditedStatus` | trạng thái kiểm toán | Giải mã qua từ điển response | HIGH |
| KBS | vnstock | Tài chính `ValueN` qua client | fact tiền tệ VNĐ | Nhân giá trị raw nghìn VNĐ với 1.000 | HIGH |

Các ánh xạ snapshot **không được** sử dụng như các ánh xạ lịch sử hàng ngày.

## 16. Mappings chưa rõ / bị chặn (Unknown / blocked mappings)

- Ánh xạ live `company_name` cho mã cụ thể — route danh sách trả về toàn bộ thị trường nên không gọi trong phạm vi giới hạn.
- `sector`, `industry` canonical, `delisting_date`, `listing_status`, `ticker_history`, `exchange_history`.
- Ngữ nghĩa `provider_security_id` ổn định.
- Snapshot live `outstanding_shares`, `issued_shares`, `treasury_shares`; lịch sử số lượng cổ phiếu và ngày PIT.
- Sự phân biệt `TLQ` vs `LS`; đơn vị/hệ số nhân của profile `VL`.
- Giá tham chiếu/trần/sàn lịch sử, giá trị giao dịch lịch sử, trạng thái giao dịch lịch sử, các trường khớp lệnh/thỏa thuận.
- Từ điển mã trạng thái `MS`.
- Phương pháp luận/hệ số điều chỉnh chính xác mặc dù nhãn vendor-adjusted đã được xác minh.
- Các bản ghi sự kiện doanh nghiệp và mọi ngữ nghĩa sự kiện cho các mã được kiểm tra.
- `published_at`/`available_at` tài chính canonical, ID báo cáo ổn định, ngữ nghĩa sửa đổi/điều chỉnh lại.
- Kết quả kinh doanh Q2/Q3 tổng thể: **UNKNOWN — DO NOT MAP YET** vì Q3 chưa được xác minh.
- Lưu chuyển tiền tệ Q2/Q3: **UNKNOWN — DO NOT MAP YET**.
- Cổ phiếu bình quân cơ bản/suy giảm.
- Lịch giao dịch sàn chính thức.
- Quyền tự động hóa/sử dụng dữ liệu của nhà cung cấp: **NOT_VERIFIED**.

Không có đường dẫn nào gặp thách thức truy cập kỹ thuật; nhãn `BLOCKED` không được dùng để che giấu một trường chưa rõ ngữ nghĩa (semantic unknown).

## 17. Bù đắp khoảng trống so với CafeF + VietFin (CafeF + VietFin gap coverage)

| Khoảng trống chưa giải quyết hiện tại | Kết quả Vnstock/provider | Trạng thái |
|---|---|---|
| Lịch sử cổ phiếu | Chỉ có snapshot `LS` hiện tại và lịch sử vốn điều lệ; không có chuỗi cổ phiếu/PIT | CÙNG KHOẢNG TRỐNG (SAME_GAP) |
| Cơ sở giá (Price basis) | Tài liệu chính thức hiện tại dán nhãn rõ giá lịch sử là điều chỉnh kỹ thuật | LẤP ĐẦY KHOẢNG TRỐNG (FILLS_GAP) |
| Tham chiếu/Trần/Sàn lịch sử | Chỉ có snapshot bảng giá KBS hiện tại | SAME_GAP |
| Trạng thái giao dịch lịch sử | Chỉ có mã `MS` hiện tại, từ điển chưa xác minh | SAME_GAP |
| Ngữ nghĩa khớp lệnh vs thỏa thuận | Snapshot hiện tại tách `TT/TV` và `PTQ/PTV`; không có lịch sử ngày được kiểm tra; có giới hạn Community | MỘT PHẦN (PARTIAL) |
| Ranh giới kỳ tài chính | `PeriodBegin/PeriodEnd` rõ ràng trong response nhà cung cấp | FILLS_GAP |
| `published_at`/`available_at` tài chính | Có nhiều ứng viên ngày nhưng chưa định nghĩa PIT canonical | PARTIAL |
| Sửa đổi/Điều chỉnh lại | `LastUpdate` có mặt nhưng không có ID sửa đổi/ngữ nghĩa điều chỉnh lại | PARTIAL |
| Ngữ nghĩa KQKD Q2/Q3 | Q2 có ranh giới độc lập rõ ràng; Q3 chưa xác minh | PARTIAL |
| Ngữ nghĩa LCTT Q2/Q3 | Giá trị Q2 được kiểm tra bị rỗng; Q3 chưa xác minh | SAME_GAP |
| Cổ phiếu bình quân lưu hành | Không tìm thấy | SAME_GAP |
| Ngữ nghĩa VNINDEX | Mức giá sẵn có theo điểm; phương pháp chỉ số/PIT chưa xác minh | PARTIAL |
| Lịch giao dịch | Từ điển sự kiện quá khứ do client duy trì, không phải lịch nhà cung cấp chính thức | PARTIAL |
| Quyền tự động hóa | Giấy phép client rõ ràng nhưng quyền dữ liệu KBS chưa xác minh | SAME_GAP |

Đây chỉ là đánh giá khoảng trống; không lựa chọn nguồn sự thật cuối cùng.

## 18. Vai trò ứng viên theo nhà cung cấp/domain (Candidate role by provider/domain)

| Provider | Client thu thập | Domain | Tính sẵn có | Độ tin cậy | Vai trò ứng viên | Hạn chế chính |
|---|---|---|---|---|---|---|
| KBS qua vnstock | Security | PARTIAL | MEDIUM | CROSS_CHECK | Định danh hiện tại tốt; tên/lịch sử/trạng thái chưa đủ |
| KBS qua vnstock | Shares history | CURRENT_SNAPSHOT_ONLY | HIGH cho snapshot, LOW cho history | NOT_READY | Không có lịch sử số lượng cổ phiếu/PIT |
| KBS qua vnstock | Daily market | PARTIAL | HIGH cho OHLCV/đơn vị/basis | PRIMARY_CANDIDATE | Thiếu tham chiếu/trần/sàn/giá trị/trạng thái lịch sử |
| KBS qua vnstock | Corporate actions | NOT_READY | HIGH về kết quả rỗng | NOT_READY | Cả 4 mã được kiểm tra đều rỗng |
| KBS qua vnstock | Financial statements | PARTIAL | HIGH cho cấu trúc, MEDIUM tổng thể | SECONDARY_CANDIDATE | PIT, bản sửa đổi, Q3 và LCTT chưa đủ |
| KBS qua vnstock | Benchmark | AVAILABLE | MEDIUM | SECONDARY_CANDIDATE | Phương pháp luận/PIT VNINDEX chưa xác minh |
| Từ điển client Vnstock | Trading calendar | PARTIAL | MEDIUM | CROSS_CHECK | Không chính thức và không phải lịch nhà cung cấp |

Không có một dòng chung "Vnstock = PRIMARY"; vai trò luôn gắn liền với nhà cung cấp + domain.

## 19. So sánh với KBS hệ thống cũ (Legacy KBS comparison)

| Bài học hệ thống cũ | Kết quả hiện tại | Bằng chứng / Thay đổi hiện tại |
|---|---|---|
| Quy mô/Đơn vị giá | XÁC MINH LẠI (RE-VERIFIED) | Giá cổ phiếu daily raw của KBS là VNĐ; client hiện tại chia OHLC cổ phiếu cho 1.000, nên DELTA phải nhân kết quả client với 1.000 về VNĐ. Chỉ số không chia. |
| Hành vi điều chỉnh giá lịch sử | RE-VERIFIED | Tài liệu chính thức hiện tại dán nhãn rõ dữ liệu lịch sử là điều chỉnh kỹ thuật; phương pháp chi tiết vẫn chưa rõ. |
| Tính sẵn có của VNINDEX | RE-VERIFIED | Response KBS công khai 2 ngày trả về OHLCV VNINDEX. |
| Xuất xứ nhà cung cấp | RE-VERIFIED | Nguồn hiện tại điều hướng đúng host/path KBS và các thuộc tính response định danh KBS; provenance phải là KBS + vnstock. |
| Hành vi Ngày/Chunk | THAY ĐỔI (CHANGED) | Ranh giới 2 ngày bao hàm và thứ tự mới nhất trước của provider được xác minh lại; chia chunk 180 ngày được hạ xuống thành lựa chọn triển khai trong repository, không còn xem là sự thật của provider. |
| Tính sẵn có của sự kiện doanh nghiệp | KHÔNG CÒN SẴN CÓ (NO_LONGER_AVAILABLE) | Phương thức vẫn tồn tại nhưng mẫu live 4 mã, bao gồm FPT, đều trả rỗng; các kết luận sự kiện cũ không dùng cho Data V2. |

Mọi chi tiết hệ thống cũ ngoài bảng trên là **LEGACY_ONLY — NOT RE-VERIFIED**.

## 20. Phụ lục bằng chứng (Evidence appendix)

### Bằng chứng tài liệu/mã nguồn công khai

| ID | Trạng thái công khai | URL | Quan sát |
|---|---|---|---|
| DOC-1 | Công khai, không đăng nhập | [Vnstock GitHub README](https://github.com/thinh-vu/vnstock) | Vnstock là client; các route KBS cho Reference/Market/Fundamental; quota client và miễn trừ quyền nhà cung cấp. |
| DOC-2 | Công khai, không đăng nhập | [Giấy phép Vnstock](https://vnstocks.com/onboard/giay-phep-su-dung) | Giấy phép phần mềm riêng; không cấp quyền dữ liệu bên thứ ba. |
| DOC-3 | Công khai, không đăng nhập | [Tài liệu thị trường Cộng đồng](https://www.vnstocks.com/docs/vnstock/du-lieu-thi-truong-market-data) | Cấu trúc Community API và các trường OHLCV. |
| DOC-4 | Công khai, không đăng nhập | [Tài liệu giao dịch Vnstock Data](https://www.vnstocks.com/docs/vnstock-data/du-lieu-giao-dich) | Giá lịch sử được mô tả là điều chỉnh kỹ thuật; KBS là nhà cung cấp được hỗ trợ. |
| DOC-5 | Công khai, không đăng nhập | [Triển khai báo giá KBS](https://github.com/thinh-vu/vnstock/blob/main/vnstock/explorer/kbs/quote.py) | Route/tham số chính xác, phép chuyển đổi cổ phiếu `/1000`, sắp xếp client tăng dần, hành vi khi rỗng. |
| DOC-6 | Công khai, không đăng nhập | [Hằng số trường KBS](https://github.com/thinh-vu/vnstock/blob/main/vnstock/explorer/kbs/const.py) | Ánh xạ raw, đơn vị/ghi chú, định danh, ánh xạ tài chính. |
| DOC-7 | Công khai, không đăng nhập | [Triển khai tài chính KBS](https://github.com/thinh-vu/vnstock/blob/main/vnstock/explorer/kbs/financial.py) | `unit=1000`, `×1000`, metadata kỳ/kiểm toán/phạm vi và giải pháp tạm thời page-size=1. |
| DOC-8 | Công khai, không đăng nhập | [Changelog Vnstock](https://github.com/thinh-vu/vnstock/blob/main/CHANGELOG.md) | Sửa ánh xạ bảng giá; giới hạn tính năng Community; từ điển sự kiện thị trường. |
| DOC-9 | Công khai, không đăng nhập | [PyPI vnstock 4.0.8](https://pypi.org/project/vnstock/4.0.8/) | Metadata phiên bản/phát hành công khai hiện tại tại ngày khám phá. |

### Bằng chứng request live

Tất cả các response live đều là `application/json` qua HTTPS; không cung cấp hay ghi lại thông tin xác thực/cookie/header auth nào.

| ID | Phương thức | Host/path | Tham số/Body | Kết quả | Ghi chú dấu thời gian/múi giờ |
|---|---|---|---|---|---|
| LIVE-1 | GET ×4 | `kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{FPT,VNM,PVS,ACV}/data_day` | `sdate=02-01-2025`, `edate=03-01-2025` | 2 dòng/mã, bao hàm cả 2 ranh giới, mới nhất trước | `07:00` không múi giờ; múi giờ chưa rõ |
| LIVE-2 | POST ×1 | `.../stock/iss` | `{"code":"FPT,VNM,PVS,ACV"}` | 4 dòng snapshot chứa RE/CL/FL/TV/TT/PTQ/PTV/LS/MS | Có trường Unix-ms; ngữ nghĩa múi giờ chưa rõ |
| LIVE-3 | GET ×4 | `.../stockinfo/profile/{symbol}` | `l=1` | 4 profile và `CharterCapital[]` | Ngày profile/vốn không có múi giờ |
| LIVE-4 | GET ×4 | `.../stockinfo/event/{symbol}` | `l=1&p=1&s=10` | Mảng rỗng | Không quan sát được dấu thời gian sự kiện |
| LIVE-5 | GET ×6 | `.../stock/finance-info/FPT` | 3 loại báo cáo × năm/quý, `page=1&pageSize=1&unit=1000` | KQKD/CĐKT năm+quý; LCTT năm; giá trị LCTT Q2 rỗng | Dấu thời gian tài chính không có múi giờ |
| LIVE-6 | GET ×3 | `.../stock/finance-info/{VNM,PVS,ACV}` | KQKD quý, 1 kỳ | Cấu trúc/dữ liệu Q2 cho cả 3 mã | Giống trên |
| LIVE-7 | GET giới hạn | `.../stock/finance-info/FPT` | Tìm kiếm Q3 dừng lại sau khi trang 4/5 trả về tiêu đề Q4 bị lặp | Xác nhận bất thường phân trang; không brute force | Giống trên |
| LIVE-8 | GET ×1 | `.../index/VNINDEX/data_day` | Cùng cửa sổ 2 ngày | 2 dòng OHLCV VNINDEX | `07:00` không múi giờ |

Hành vi truy cập/rate quan sát được: các response thành công không gặp thách thức đăng nhập. Số lượng request nhỏ và tuần tự; không đủ để xác định giới hạn rate và không có kiểm tra tải (stress test).

## 21. Trạng thái phê duyệt (Approval state)

- Vòng đời (Lifecycle): **ACCESS_TESTED**.
- So sánh nguồn (Source comparison): **READY_FOR_SOURCE_COMPARISON**.
- Adapter: **NO_ADAPTER_YET**.
- `SOURCE_SMOKE`: **NO**.

Lý do: mối quan hệ nhà cung cấp, truy cập live, tính sẵn có của các phân hệ cốt lõi, chuyển đổi giá/đơn vị và xuất xứ đều đủ rõ để so sánh nhận thức nhà cung cấp với CafeF trực tiếp và TCBS-qua-VietFin. Adapter vẫn chưa được phép vì quyền tự động hóa dữ liệu của KBS chưa được xác minh, đường dẫn package/version hiện tại khác với pin của repository, sự kiện doanh nghiệp/lịch sử cổ phiếu còn thiếu, và ngữ nghĩa PIT tài chính / LCTT Q2-Q3 chưa đủ.
