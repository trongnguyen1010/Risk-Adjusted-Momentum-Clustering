# Vnstock Data V2 Discovery Result (Kết quả Khám phá Vnstock Data V2)

**Ngày khám phá:** 2026-09-16  
**Bằng chứng chi tiết:** [VNSTOCK.md](VNSTOCK.md)  
**Vòng đời (Lifecycle):** `ACCESS_TESTED`

## Tóm tắt nhà cung cấp (Provider summary)

| Hạng mục | Kết quả |
|---|---|
| Phiên bản client Vnstock | PyPI hiện tại: 4.0.8; pin adapter repository: 4.0.6; môi trường local: chưa cài đặt |
| Nhà cung cấp chính được thử nghiệm (Primary provider) | KBS |
| Nhà cung cấp thay thế được thử nghiệm | NONE |
| Truy cập live nhà cung cấp chính | YES |
| Quyền tự động hóa dữ liệu của nhà cung cấp | NOT_VERIFIED |
| Nhận diện xuất xứ (provenance) nhà cung cấp | YES |

## Độ sẵn sàng tổng thể theo phân hệ (Overall domain readiness)

| Domain | Kết quả |
|---|---|
| Chứng khoán (Security) | PARTIAL |
| Lịch sử cổ phiếu (Shares history) | PARTIAL |
| Thị trường hàng ngày (Daily market) | PARTIAL |
| Cơ sở giá (Price basis) | VERIFIED |
| Tham chiếu/Trần/Sàn lịch sử | NO |
| Hành động doanh nghiệp (Corporate actions) | NOT_READY |
| Báo cáo tài chính (Financial statements) | PARTIAL |
| PIT tài chính | PARTIAL |
| Ngữ nghĩa Kết quả kinh doanh Q2/Q3 | UNKNOWN |
| Ngữ nghĩa Lưu chuyển tiền tệ Q2/Q3 | UNKNOWN |
| Chỉ số VNINDEX | VERIFIED |
| Lịch giao dịch (Trading calendar) | PARTIAL |
| Cho phép triển khai Adapter tiếp theo | NO |
| Cho phép chạy SOURCE_SMOKE tiếp theo | NO |

## Phạm vi Mã cổ phiếu (Symbol coverage)

| Symbol | Exchange | Provider | Profile | Market | Shares | Actions | Financials | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| FPT | HOSE | KBS | VERIFIED | VERIFIED | PARTIAL | NOT_FOUND | PARTIAL | Mẫu kiểm tra hoàn chỉnh có giới hạn; giá trị LCTT Q2 rỗng |
| VNM | HOSE | KBS | VERIFIED | VERIFIED | PARTIAL | NOT_FOUND | PARTIAL | Đã kiểm tra KQKD theo quý |
| PVS | HNX | KBS | VERIFIED | VERIFIED | PARTIAL | NOT_FOUND | PARTIAL | Xác nhận bao phủ sàn HNX |
| ACV | UPCOM | KBS | VERIFIED | VERIFIED | PARTIAL | NOT_FOUND | PARTIAL | Xác nhận bao phủ sàn UPCOM |

## Độ sẵn sàng của Trường Canonical (Canonical-field readiness)

### Sẵn sàng để ánh xạ (Ready to map)

- `ticker`, `exchange` hiện tại, `listing_date`.
- `listed_shares` hiện tại từ price-board `LS`.
- `trade_date` lịch sử, OHLC đã điều chỉnh và `volume`; giá OHLC của Vnstock phải `×1000` để về đơn vị VNĐ/cổ phiếu.
- Metadata tài chính: `fiscal_year`, `fiscal_quarter`, ranh giới kỳ theo cấp tháng, phạm vi báo cáo (`statement_scope`), trạng thái kiểm toán (`audit_status`) và giá trị tiền tệ `ValueN × 1000` về VNĐ.

### Tìm thấy nhưng CHƯA sẵn sàng ánh xạ (Found but NOT ready to map)

- `reference_price`, `ceiling_price`, `floor_price`, `traded_value`, các trường khớp lệnh/thỏa thuận — chỉ có dưới dạng snapshot hiện tại.
- `trading_status` — từ điển mã `MS` chưa được xác minh.
- Lịch sử vốn điều lệ (`charter_capital`) — không phải lịch sử số lượng cổ phiếu (`share-count history`).
- Metadata tài chính `DatePubDepartment`, `CreatedDate`, `LastUpdate` — ngữ nghĩa PIT/sửa đổi chưa đủ.
- Kết quả kinh doanh Q2/Q3 — Q2 có ranh giới độc lập (standalone), Q3 chưa xác minh; **UNKNOWN — DO NOT MAP YET**.
- Lưu chuyển tiền tệ Q2/Q3 — giá trị Q2 kiểm tra bị rỗng và Q3 chưa xác minh; **UNKNOWN — DO NOT MAP YET**.

### Không tìm thấy / Bị chặn (Not found / blocked)

- Lịch sử cổ phiếu kèm ngày hiệu lực/PIT; cổ phiếu phát hành/cổ phiếu quỹ.
- Giá tham chiếu/trần/sàn lịch sử, trạng thái giao dịch và chuỗi dữ liệu khớp lệnh/thỏa thuận.
- Bản ghi sự kiện doanh nghiệp (corporate actions) cho cả 4 mã.
- Số lượng cổ phiếu bình quân lưu hành tính EPS cơ bản/suy giảm.
- Lịch giao dịch sàn chuẩn xác từ KBS.

## Kết luận về Thị trường (Market conclusion)

- Nhà cung cấp (Provider): KBS; Client thu thập: Vnstock.
- OHLC: Đã xác minh sẵn có cho FPT/VNM/PVS/ACV.
- Tham chiếu / Trần / Sàn: Đã xác minh có snapshot hiện tại, không có lịch sử được kiểm tra.
- Khối lượng (Volume): Đơn vị cổ phiếu, sẵn có trong OHLCV hàng ngày.
- Khớp lệnh vs Thỏa thuận: Phân tách được trong snapshot (`TT/TV` và `PTQ/PTV`), chưa đủ cho lịch sử hàng ngày.
- Giá trị giao dịch: `TV` tính bằng VNĐ trong snapshot; `data_day` lịch sử không có.
- Trạng thái giao dịch: `MS` hiện diện nhưng ngữ nghĩa từ điển mã chưa được xác minh.
- Cơ sở giá (Price basis): `VENDOR_ADJUSTED`; phương pháp điều chỉnh chi tiết không được công bố.
- Đơn vị / Hệ số nhân: Giá KBS raw tính bằng VNĐ/cổ phiếu; OHLC cổ phiếu chuẩn hóa của Vnstock chia cho 1.000 nên phép chuyển đổi canonical là `×1000`.
- Độ sâu lịch sử: Tài liệu client chính thức nêu tối đa khoảng 8 năm dữ liệu ngày; giới hạn tối đa của provider không thực hiện probe.
- Hành vi Request / Chia chunk: `sdate/edate` bao hàm trong mẫu, provider xếp mới nhất trước, client sắp xếp tăng dần; việc chia chunk 180 ngày của repository là lựa chọn triển khai.

## Kết luận về Cổ phiếu (Shares conclusion)

- Trạng thái: `CURRENT_SNAPSHOT_ONLY`.
- Chuỗi lịch sử: Chỉ có lịch sử vốn điều lệ, không phải lịch sử số lượng cổ phiếu.
- Ngày hiệu lực (`effective_date`): Chưa được xác minh cho cổ phiếu.
- `available_at` / PIT: Không tìm thấy.
- Hạn chế chính: Không được suy số lượng cổ phiếu từ vốn điều lệ / mệnh giá hoặc coi `LS`, `TLQ`, `VL` là có thể thay thế cho nhau.

## Kết luận về Tài chính (Financial conclusion)

- Theo quý: Sẵn có; KQKD/CĐKT của FPT có giá trị, các giá trị LCTT Q2 được kiểm tra bị rỗng; KQKD quý của VNM/PVS/ACV sẵn có.
- Theo năm: KQKD/CĐKT/LCTT năm của FPT sẵn có.
- Phạm vi (Scope): `HN/ĐL/CTM` có từ điển phân biệt rõ Hợp nhất / Độc lập / Công ty mẹ.
- Ranh giới kỳ (Period boundaries): `PeriodBegin/PeriodEnd` rõ ràng ở cấp tháng.
- Đơn vị / Tiền tệ: Request KBS sử dụng nghìn VNĐ; client hiện tại nhân 1.000 về VNĐ.
- PIT: Một phần; các ứng viên ngày công bố/tạo/cập nhật chưa đủ định nghĩa `available_at`.
- Bản sửa đổi (Revision): `LastUpdate` có xuất hiện nhưng không có ngữ nghĩa bản sửa đổi/điều chỉnh lại.
- KQKD Q2/Q3: **UNKNOWN — DO NOT MAP YET**; ranh giới độc lập Q2 đã xác minh, Q3 chưa xác minh.
- LCTT Q2/Q3: **UNKNOWN — DO NOT MAP YET**.
- Số lượng cổ phiếu bình quân: Không tìm thấy.

## Mức độ bù đắp khoảng trống hiện tại (Existing-gap coverage)

| Khoảng trống | Kết quả |
|---|---|
| Lịch sử cổ phiếu | CÙNG KHOẢNG TRỐNG (SAME_GAP) |
| Cơ sở giá (Price basis) | LẤP ĐẦY KHOẢNG TRỐNG (FILLS_GAP) |
| Tham chiếu/Trần/Sàn lịch sử | CÙNG KHOẢNG TRỐNG (SAME_GAP) |
| PIT tài chính | MỘT PHẦN (PARTIAL) |
| Ngữ nghĩa Q2/Q3 | MỘT PHẦN (PARTIAL) |
| Lịch giao dịch | MỘT PHẦN (PARTIAL) |

## Trạng thái KBS từ hệ thống cũ (Legacy KBS status)

| Bài học hệ thống cũ | Kết quả hiện tại |
|---|---|
| Quy mô/Đơn vị giá | XÁC MINH LẠI (RE-VERIFIED) |
| Hành vi điều chỉnh giá | XÁC MINH LẠI (RE-VERIFIED) |
| Chỉ số VNINDEX | XÁC MINH LẠI (RE-VERIFIED) |
| Xuất xứ nhà cung cấp (Provenance) | XÁC MINH LẠI (RE-VERIFIED) |
| Hành vi Chunk/Ngày | THAY ĐỔI (CHANGED) |

## Quyết định (Decision)

`READY_FOR_SOURCE_COMPARISON`

**Lý do:** Mối quan hệ KBS-qua-Vnstock, truy cập công khai, đơn vị/basis của OHLCV, cấu trúc tài chính và provenance đã đủ rõ để tiến hành so sánh với CafeF trực tiếp và TCBS-qua-VietFin. Các khoảng trống còn lại được giữ rõ ràng, không ép buộc ánh xạ vào ngữ nghĩa canonical.

## Ghi chú Adapter (Adapter note)

`NO_ADAPTER_YET`

Không triển khai adapter tại bước này.

## Hành động tiếp theo (Next action)

`Chuyển sang bước so sánh nguồn nhận thức nhà cung cấp SOURCE_COMPARISON.md.`
