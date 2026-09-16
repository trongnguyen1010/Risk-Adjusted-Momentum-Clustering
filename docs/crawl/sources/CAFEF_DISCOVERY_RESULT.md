# CafeF Discovery Result (Kết quả Khám phá CafeF)

**Ngày khám phá:** 2026-09-16  
**Bằng chứng chi tiết:** [CAFEF.md](CAFEF.md)  
**Vòng đời (Lifecycle):** `ACCESS_TESTED`

## Tổng quan (Overall)

| Hạng mục | Kết quả |
|---|---|
| Truy cập công khai hợp lệ (Legitimate public access) | YES |
| Dữ liệu thị trường (Market data) tìm thấy | YES |
| Đơn vị thị trường (Market units) được xác minh | PARTIAL |
| Cơ sở giá (Price basis) được xác minh | NO |
| Snapshot cổ phiếu hiện tại (Shares current snapshot) | YES |
| Chuỗi lịch sử cổ phiếu (Shares historical series) | NO |
| Hành động doanh nghiệp (Corporate actions) | PARTIAL |
| Báo cáo tài chính theo quý (Quarterly financials) | PARTIAL |
| Thời điểm công bố PIT (Financial PIT publication timing) | NO |
| Ngữ nghĩa Q2/Q3 độc lập vs lũy kế (Standalone vs YTD) | UNKNOWN |
| Chỉ số VNINDEX | PARTIAL |
| Lịch giao dịch (Trading calendar) | PARTIAL |
| Cho phép triển khai Adapter tiếp theo | YES |
| Cho phép chạy SOURCE_SMOKE tiếp theo | NO |

## Phạm vi Mã cổ phiếu (Symbol coverage)

| Symbol | Exchange | Profile | Market | Shares | Actions | Financials | Ghi chú |
|---|---|---|---|---|---|---|---|
| FPT | HOSE | VERIFIED | PARTIAL | VERIFIED | PARTIAL | PARTIAL | Mẫu ngữ nghĩa chính; chỉ có cổ phiếu hiện tại; ngữ nghĩa giá/PIT chưa hoàn thiện |
| VNM | HOSE | VERIFIED | PARTIAL | VERIFIED | NOT_CHECKED | PARTIAL | Mẫu đối chiếu lịch sử và tài chính HOSE thứ hai |
| PVS | HNX | VERIFIED | PARTIAL | VERIFIED | NOT_CHECKED | PARTIAL | Route HNX hoạt động; số lượng cổ phiếu niêm yết và lưu hành khác nhau |
| ACV | UPCOM | VERIFIED | PARTIAL | VERIFIED | NOT_CHECKED | PARTIAL | Route UPCOM hoạt động; số lượng cổ phiếu niêm yết và lưu hành khác nhau |

## Độ sẵn sàng của Trường Canonical (Canonical-field readiness)

### Sẵn sàng để ánh xạ (Ready to map)

- `ticker`, `company_name`, `exchange` hiện tại, `industry` của CafeF, và `listing_date` trên profile hiện tại.
- Ngày giao dịch thị trường (`trade_date`).
- Metadata tài liệu tài chính: `fiscal_year`, `fiscal_quarter`, phạm vi hợp nhất/công ty mẹ (`statement_scope`), trạng thái kiểm toán/soát xét (`audit_status`), đơn vị tiền tệ VND, và quy mô đơn vị hiển thị.

### Tìm thấy nhưng CHƯA sẵn sàng ánh xạ (Found but NOT ready to map)

- `listed_shares`, `outstanding_shares` — giá trị hiện tại rõ ràng, nhưng thiếu mốc thời gian hiệu lực (`effective_date`) và thời điểm công bố (`publication_at`).
- Giá OHLC, giá đóng cửa (`close`), giá điều chỉnh (`adjusted close`) — đơn vị rõ ràng nhưng cơ sở tính giá (price basis) chưa xác định.
- Giá tham chiếu, giá trần, giá sàn và trạng thái giao dịch — chỉ tìm thấy dạng snapshot cho phiên hiện tại, không có trong lịch sử theo ngày.
- Khối lượng/Giá trị khớp lệnh và thỏa thuận — ngữ nghĩa nguồn rõ ràng nhưng chính sách gộp/bao hàm chuẩn hoá (canonical inclusion policy) chưa được quyết định.
- Giá trị hành động doanh nghiệp — ngày chót đăng ký/hiệu lực/thanh toán và tỷ lệ chuẩn hoá chưa hoàn thiện.
- Các chỉ tiêu tài chính (financial facts) — ranh giới kỳ báo cáo, việc liên kết báo cáo với fact, tính sẵn có PIT, các bản sửa đổi (revisions), và ngữ nghĩa khoảng thời gian Q2/Q3 chưa hoàn thiện.
- Chỉ số VNINDEX — có dữ liệu lịch sử nhưng cơ sở tính toán và hành vi dòng dữ liệu bất thường/chưa hoàn thành chưa được ánh xạ.
- Lịch giao dịch sàn — có thông báo ngày nghỉ lễ công khai nhưng không có lịch giao dịch theo ngày dạng cấu trúc.

### Không tìm thấy (Not found)

- Mã định danh chứng khoán/công ty của nhà cung cấp (`provider_security_id`).
- Chuỗi lịch sử số lượng cổ phiếu kèm ngày hiệu lực và ngày công bố.
- Các trường rõ ràng cho số lượng cổ phiếu phát hành (`issued_shares`) và cổ phiếu quỹ (`treasury_shares`).
- Dữ liệu lịch sử niêm yết / hủy niêm yết / trạng thái chứng khoán.
- Số lượng cổ phiếu bình quân lưu hành tính EPS cơ bản và suy giảm.

## Kết luận về Cổ phiếu (Shares conclusion)

**Trạng thái:**  
`CURRENT_SNAPSHOT_ONLY`

CafeF hiển thị rõ ràng số lượng cổ phiếu niêm yết và lưu hành hiện tại cho cả 4 mã, và hai mã PVS/ACV chứng minh rằng hai trường này không được tự ý coi là bằng nhau. Không tìm thấy chuỗi lịch sử số lượng cổ phiếu hoàn chỉnh hoặc thời điểm hiệu lực/công bố đáng tin cậy, do đó các snapshot này **không được phép** xuất ra dưới dạng `shares_history` hoặc backfill ngược về quá khứ.

## Kết luận về Tài chính (Financial conclusion)

- **Theo quý:** Sẵn có cho cả 4 mã, nhưng việc ánh xạ fact chuẩn hoá mới đạt một phần.
- **Theo năm:** Sẵn có cho FPT thông qua giao diện năm và các tài liệu kiểm toán năm.
- **Hợp nhất / Công ty mẹ:** Phân biệt rõ ràng trong tiêu đề tài liệu.
- **Quy mô đơn vị:** UI tóm tắt hiện tại hỗ trợ rõ ràng đơn vị Tỷ/Triệu VNĐ và hàm dựng (renderer) áp dụng hệ số chia `1e9`/`1e6`.
- **Thời điểm công bố:** Dấu thời gian tài liệu/tin tức chỉ là ứng viên; canonical `published_at`/`available_at` chưa được xác minh.
- **Ngữ nghĩa Q2/Q3:** `UNKNOWN — DO NOT MAP YET`.
- **Các hạng mục chính còn thiếu/chưa rõ:** Ngày bắt đầu/kết thúc kỳ, mốc thời gian PIT, định danh bản sửa đổi/điều chỉnh (revision/restatement), liên kết giữa báo cáo và fact, và ngữ nghĩa khoảng thời gian nhất quán giữa các báo cáo.

## Kết luận về Thị trường (Market conclusion)

- **OHLC:** Tìm thấy với đơn vị nghìn VNĐ/cổ phiếu rõ ràng; tạm thời giữ nguyên chưa ánh xạ vì chưa xác định được price basis.
- **Tham chiếu / Trần / Sàn:** Chỉ có trên trang tổng quan phiên hiện tại, không có trong dữ liệu lịch sử.
- **Khối lượng giao dịch:** Khối lượng khớp lệnh và thỏa thuận được tách biệt bằng đơn vị cổ phiếu; chính sách đưa vào canonical chưa quyết định.
- **Giá trị giao dịch:** Giá trị khớp lệnh và thỏa thuận được tách biệt bằng đơn vị tỷ VNĐ; chính sách đưa vào canonical chưa quyết định.
- **Trạng thái giao dịch:** Có văn bản hiển thị trạng thái phiên hiện tại; không có lịch sử trạng thái chuẩn hoá.
- **Price basis:** `UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET`.
- **Đơn vị / Hệ số nhân:** Giá ×1.000 ra VNĐ/cổ phiếu và Giá trị ×1.000.000.000 ra VNĐ được xác nhận bởi nhãn UI rõ ràng, nhưng chỉ áp dụng sau khi ngữ nghĩa của trường mục tiêu được duyệt.
- **Phân trang / Hành vi ngày:** Request JSON công khai, trang bắt đầu từ 1, 20 dòng/trang, mới nhất xếp trước, mặc định khoảng thời gian 1 tháng, hiển thị rõ ràng khi kết quả rỗng; ranh giới bao hàm và khoảng ngày tối đa của request thông thường chưa được chứng minh.

## Rào cản trước Adapter (Blockers before adapter)

`NONE`

## Quyết định (Decision)

`READY_FOR_ADAPTER_IMPLEMENTATION`

**Lý do:** Truy cập công khai và cấu trúc request đã được xác lập; định danh chứng khoán cùng các trường metadata được chọn đã được xác minh đủ để xây dựng một adapter giới hạn theo nguyên tắc fail-closed. Các trường chưa rõ về giá, lịch sử cổ phiếu, hành động doanh nghiệp và tài chính có thể tiếp tục để trống (unmapped) mà không làm sai lệch ngữ nghĩa của DELTA; quyết định này **không đồng nghĩa với việc cho phép** chạy real SOURCE_SMOKE.

## Hành động tiếp theo (Next action)

Triển khai adapter CafeF theo cơ chế fail-closed dựa trên các mapping đã được xác minh trong [CAFEF.md](CAFEF.md).
