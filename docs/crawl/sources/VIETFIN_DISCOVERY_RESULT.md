# VietFin Discovery Result (Kết quả Khám phá VietFin)

**Ngày khám phá:** 2026-09-16  
**Bằng chứng chi tiết:** [VIETFIN.md](VIETFIN.md)  
**Vòng đời (Lifecycle):** `ACCESS_TESTED`

## Tổng quan (Overall)

| Hạng mục | Kết quả |
|---|---|
| Truy cập công khai hợp lệ (Legitimate public access) | PARTIAL |
| Dữ liệu thị trường (Market data) tìm thấy | PARTIAL |
| Đơn vị thị trường (Market units) được xác minh | NO |
| Cơ sở giá (Price basis) được xác minh | NO |
| Tham chiếu/Trần/Sàn lịch sử (Historical reference/ceiling/floor) | NO |
| Snapshot cổ phiếu hiện tại (Shares current snapshot) | YES |
| Chuỗi lịch sử cổ phiếu (Shares historical series) | NO |
| Mốc thời gian hiệu lực của cổ phiếu (Shares effective timing) | NO |
| Hành động doanh nghiệp (Corporate actions) | PARTIAL |
| Báo cáo tài chính theo quý (Quarterly financials) | PARTIAL |
| Ranh giới kỳ tài chính (Financial period boundaries) | NO |
| Thời điểm công bố PIT (Financial PIT publication timing) | NO |
| Ngữ nghĩa sửa đổi/điều chỉnh lại (Revision/restatement semantics) | NO |
| Ngữ nghĩa Kết quả kinh doanh Q2/Q3 (Q2/Q3 Income Statement) | UNKNOWN |
| Ngữ nghĩa Lưu chuyển tiền tệ Q2/Q3 (Q2/Q3 Cash Flow) | UNKNOWN |
| Số lượng cổ phiếu bình quân (Weighted-average shares) | NO |
| Chỉ số VNINDEX | YES |
| Lịch giao dịch (Trading calendar) | NO |
| Cho phép triển khai Adapter tiếp theo | NO |
| Cho phép chạy SOURCE_SMOKE tiếp theo | NO |

## Phạm vi Mã cổ phiếu (Symbol coverage)

| Symbol | Exchange | Profile | Market | Shares | Actions | Financials | Ghi chú |
|---|---|---|---|---|---|---|---|
| FPT | HOSE | NOT_CHECKED | PARTIAL | NOT_CHECKED | PARTIAL | NOT_CHECKED | Tài liệu chính thức chứa ví dụ thị trường & cổ tức; route nhà cung cấp live bị BLOCKED |
| VNM | HOSE | VERIFIED | PARTIAL | PARTIAL | NOT_CHECKED | NOT_CHECKED | Có ví dụ profile/OHLCV chính thức; ứng viên cổ phiếu hiện tại thiếu đơn vị/mốc thời gian |
| PVS | HNX | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Managed challenge chặn việc xác minh live |
| ACV | UPCOM | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Managed challenge chặn việc xác minh live |

## Độ sẵn sàng của Trường Canonical (Canonical-field readiness)

### Sẵn sàng để ánh xạ (Ready to map)

- Các ứng viên định danh ở mức độ tài liệu: `ticker`, `company_name` hiện tại, `exchange` hiện tại, và `industry` của nhà cung cấp.
- `trade_date` dưới dạng trường ngày, giữ nguyên hạn chế về múi giờ.
- Metadata nhãn tài chính: `fiscal_year`, `fiscal_quarter`.
- Các ứng viên ngày sự kiện doanh nghiệp: ngày thông báo (`announcement_date`), ngày chốt danh sách (`record_date`), ngày GDKHQ (`ex_date`) và ngày thanh toán (`payment_date`), phụ thuộc vào việc xác minh xuất xứ (provenance) live.

### Tìm thấy nhưng CHƯA sẵn sàng ánh xạ (Found but NOT ready to map)

- OHLC và khối lượng (`volume`) — đơn vị/hệ số nhân nguồn, chính sách đưa vào canonical và cơ sở tính giá (price basis) chưa được xác minh.
- `outstandingShare`, `issueShare` — chỉ là ứng viên raw hiện tại; đơn vị, ngày hiệu lực và thời điểm công bố chưa xác định.
- Các loại/số tiền/tỷ lệ hành động doanh nghiệp — việc ánh xạ sự kiện canonical, ý nghĩa phần trăm tiền mặt, điều khoản quyền mua và bản sửa đổi chưa giải quyết.
- Các chỉ tiêu tài chính (financial facts) — nhãn phụ thuộc nhà cung cấp mà không có định danh báo cáo, ranh giới kỳ, phạm vi hợp nhất/công ty mẹ, đơn vị tiền tệ/quy mô đơn vị hay mốc thời gian PIT.
- VNINDEX — có giao diện nhưng cơ sở tính chỉ số và hành vi live chưa được ánh xạ sâu.

### Không tìm thấy (Not found)

- Lịch sử cổ phiếu kèm mốc thời gian hiệu lực/PIT.
- Giá tham chiếu/trần/sàn lịch sử, trạng thái giao dịch và phân rã khớp lệnh/thỏa thuận.
- Metadata tài chính: `period_start`, `period_end`, `published_at`, `available_at`, trạng thái kiểm toán và sửa đổi/điều chỉnh lại (revision/restatement).
- Số lượng cổ phiếu bình quân lưu hành tính EPS cơ bản/suy giảm.
- Lịch giao dịch sàn rõ ràng.

## Kết luận về Cổ phiếu (Shares conclusion)

**Trạng thái:**  
`CURRENT_SNAPSHOT_ONLY`

**Thời gian lịch sử:**  
`UNKNOWN`

Ví dụ profile VNM công khai hiển thị các ứng viên `outstandingShare` và `issueShare` hiện tại, nhưng không có đơn vị, ngày hiệu lực hay thời điểm công bố đi kèm. Không tìm thấy lệnh/chuỗi dữ liệu lịch sử số lượng cổ phiếu nào, do đó các giá trị này **không được phép** đưa vào `shares_history` hoặc backfill.

## Kết luận về Tài chính (Financial conclusion)

- **Theo quý:** PARTIAL; bộ chọn và 3 bộ báo cáo được mô tả trong tài liệu, nhưng payload live cho từng mã cụ thể bị block.
- **Theo năm:** PARTIAL; được mô tả cho kết quả kinh doanh, bảng cân đối kế toán và lưu chuyển tiền tệ.
- **Hợp nhất / Công ty mẹ:** UNKNOWN.
- **period_start / period_end:** NOT_FOUND.
- **Quy mô đơn vị (Unit scale):** UNKNOWN.
- **Thời điểm công bố / PIT:** NOT_FOUND.
- **Sửa đổi / Điều chỉnh lại:** NOT_FOUND.
- **Kết quả kinh doanh Q2/Q3:** `UNKNOWN — DO NOT MAP YET`.
- **Lưu chuyển tiền tệ Q2/Q3:** `UNKNOWN — DO NOT MAP YET`.
- **Số lượng cổ phiếu bình quân:** NOT_FOUND.
- **Các hạng mục chính chưa giải quyết:** Định danh báo cáo, phạm vi, ranh giới chính xác, đơn vị tiền tệ/quy mô đơn vị, tính sẵn có PIT, bản sửa đổi và ngữ nghĩa fact raw.

## Kết luận về Thị trường (Market conclusion)

- **OHLC:** Tìm thấy trong model chuẩn hoá của tài liệu; chưa sẵn sàng cho canonical.
- **Tham chiếu / Trần / Sàn:** NOT_FOUND trong model lịch sử.
- **Khối lượng:** Tìm thấy, nhưng đơn vị và sự chênh lệch gộp giữa các nhà cung cấp chưa được giải quyết.
- **Khớp lệnh vs Thỏa thuận:** NOT_FOUND.
- **Giá trị giao dịch:** NOT_FOUND.
- **Trạng thái giao dịch:** NOT_FOUND.
- **Price basis:** `UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET`.
- **Đơn vị / Hệ số nhân:** UNKNOWN; chưa có hệ số nhân nào được duyệt.
- **Phân trang / Hành vi ngày:** Nguồn TCBS dùng các chunk lùi tối đa 365 ngày và bộ lọc ngày bao hàm phía client; ranh giới/thứ tự raw và hành vi khi rỗng/giới hạn tần suất live chưa được xác minh vì truy cập bị block.

## Tóm tắt mức độ bù đắp khoảng trống so với CafeF (CafeF gap coverage summary)

| Khoảng trống tại CafeF | Kết quả tại VietFin | Trạng thái |
|---|---|---|
| Lịch sử cổ phiếu | CÙNG KHOẢNG TRỐNG | SAME_GAP |
| Cơ sở giá (Price basis) | CÙNG KHOẢNG TRỐNG | SAME_GAP |
| Tham chiếu/Trần/Sàn lịch sử | CÙNG KHOẢNG TRỐNG | SAME_GAP |
| PIT tài chính | CÙNG KHOẢNG TRỐNG | SAME_GAP |
| Ngữ nghĩa Q2/Q3 | CÙNG KHOẢNG TRỐNG | SAME_GAP |
| Sửa đổi/Điều chỉnh lại | CÙNG KHOẢNG TRỐNG | SAME_GAP |

## Rào cản trước Adapter (Blockers before adapter)

1. Đường dẫn nhà cung cấp mặc định live bị `BLOCKED` bởi managed challenge; không được phép tìm cách vượt qua.
2. Quyền tự động hóa/sử dụng dữ liệu của nhà cung cấp vẫn là `NOT_VERIFIED` mặc dù code client có giấy phép Apache-2.0.
3. Mức độ bao phủ live chính xác cho FPT, VNM, PVS và ACV chưa hoàn thiện.
4. Đơn vị/hệ số nhân thị trường và price basis chưa giải quyết; các trường QC bắt buộc bị thiếu trong model lịch sử được mô tả.
5. Ranh giới kỳ tài chính, phạm vi, đơn vị, thời điểm PIT, bản sửa đổi và ngữ nghĩa khoảng thời gian Q2/Q3 chưa giải quyết.
6. Lịch sử cổ phiếu không có sẵn và mốc thời gian/đơn vị của snapshot hiện tại chưa giải quyết.

## Quyết định (Decision)

`NOT_READY_FOR_ADAPTER_IMPLEMENTATION`

**Lý do:** Tài liệu công khai giúp hiểu được cấu trúc wrapper, nhưng truy cập dữ liệu live hợp lệ hiện chưa được xác lập và không có domain dữ liệu DELTA hữu ích nào kết hợp được đường dẫn request dùng được với đơn vị/ngữ nghĩa đã xác minh đầy đủ. Adapter **bắt buộc** phải giữ nguyên cơ chế fail-closed.

## Quyết định về SOURCE_SMOKE (SOURCE_SMOKE decision)

`NOT_READY_FOR_SOURCE_SMOKE`

**Lý do:** Quyền hạn/truy cập, mức độ bao phủ mã chính xác, các trường thị trường bắt buộc, đơn vị, price basis và ngữ nghĩa mốc thời gian không đáp ứng tiêu chuẩn cổng kiểm soát real-smoke.

## Hành động tiếp theo (Next action)

`Giải quyết các rào cản khám phá của VietFin trước khi tiếp tục so sánh nguồn.`
