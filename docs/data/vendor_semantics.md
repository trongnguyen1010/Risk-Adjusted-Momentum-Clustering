# Kiểm tra ngữ nghĩa KBS / Vnstock — 11/09/2026

Quyết định: **CHẶN chuyển đổi dữ liệu thật và thu thập diện rộng**. Bằng chứng dưới
đây không cho phép tự gán đơn vị, định danh lịch sử hoặc dấu thời gian còn thiếu.

Kiểm tra toàn vẹn bổ sung ngày 12/09/2026: 5 trong 10 file gốc của hai lần chạy ban
đầu đã thay đổi định dạng và không đạt mã băm theo byte. Khi mã hóa lại JSON đã phân
tích, mã băm khớp giá trị kỳ vọng ban đầu; các byte trong bộ nhớ đệm làm việc của SDK
cũng khớp hoàn toàn. Không chỉnh sửa file gốc hay mã băm kỳ vọng. Lần chạy mới nhất
được phục hồi vào `vendor-recovered-fccfaaa2b061` bằng cách chỉ sao chép các byte khớp
mã băm gốc; cả năm vỏ dữ liệu phục hồi đều qua kiểm tra. Việc chuyển đổi vẫn bị chặn
do thiếu dữ liệu tham chiếu và ngữ nghĩa chưa được giải quyết. Xem
`vendor_integrity.json` và `promotion.md`.

Lần chạy được quan sát: `vendor-26f2e2ce615c`, SDK 4.0.6, định tuyến KBS, 3 cổ phiếu
và VNINDEX trong tháng 8/2026, mỗi loại 20 bản ghi, cùng 3.415 bản ghi niêm yết (bao
gồm UPCOM). Ảnh chụp là đầu ra SDK, không phải phản hồi HTTP nguyên bản trên đường truyền.

| Trường | Nguồn / giá trị quan sát | Ý nghĩa / đơn vị đã xác minh | Độ tin cậy | Bằng chứng | Quyết định |
|---|---|---|---|---|---|
| open | FPT 67.4 | Trường giá mở cửa OHLC của SDK; chưa rõ cơ sở kinh tế | Ánh xạ trung bình, cơ sở chưa rõ | E1/E2 | Không ánh xạ sang giá gốc |
| high | FPT 71.7 | Trường giá cao nhất OHLC của SDK; chưa rõ cơ sở kinh tế | Trung bình | E1/E2 | Không ánh xạ sang giá gốc |
| low | FPT 67.3 | Trường giá thấp nhất OHLC của SDK; chưa rõ cơ sở kinh tế | Trung bình | E1/E2 | Không ánh xạ sang giá gốc |
| close | FPT 71.7 | SDK chia giá cổ phiếu của nhà cung cấp cho 1.000; đơn vị/cơ sở bên dưới chưa được xác minh độc lập | Chỉ phép biến đổi SDK có độ tin cậy cao | E2 | Chưa xác định `price_multiplier` sang VND chuẩn |
| volume | FPT 16279100 | SDK ép `volume` sang int64; chưa rõ đơn vị cổ phiếu hay lô và phạm vi giao dịch | Chưa xác minh | E2 | Cho phép `null`; không tự giả định hệ số |
| va | FPT 474963630000 | Giữ nguyên trường nhà cung cấp chưa ánh xạ; chưa rõ giá trị/phạm vi/đơn vị | Chưa xác minh | E2/E3 | `traded_value=null` |
| VNINDEX close | 1762.84 | Mức chỉ số từ SDK, không chia như cổ phiếu; chưa xác minh đây là chỉ số giá hay lợi suất toàn phần | Trường có độ tin cậy trung bình, cơ sở chưa rõ | E1/E2 | Chính sách chỉ số riêng; không bao giờ dùng hệ số cổ phiếu |
| time | 2026-08-03T07:00:00.000 | Dấu thời gian không kèm múi giờ sau khi pandas chuyển đổi; chưa rõ múi giờ và quy ước ngày giao dịch | Chưa xác minh | E1/E2 | Bắt buộc khai báo múi giờ có bằng chứng |
| available_at | Không có | Không có thời điểm công bố lịch sử | Chưa xác minh | Các khóa trong ảnh chụp | Dùng thời gian tải theo hướng bảo thủ hoặc dấu thời gian từng bản ghi có bằng chứng; không lùi ngày |
| adjustment_basis | Không có | Chưa xác lập giá gốc/điều chỉnh chia tách/lợi suất toàn phần | Chưa xác minh | Ảnh chụp + E2 | `unknown`; chặn nghiên cứu dùng giá điều chỉnh |
| listing | F88 / UPCOM / id=1 | Chỉ là danh sách hiện tại, không có khoảng lịch sử | Giới hạn có độ tin cậy cao | Vỏ dữ liệu niêm yết | Không tái sử dụng ID nhà cung cấp làm định danh kinh tế |

E1: [API Thị trường chính thức của bản Community](https://www.vnstocks.com/docs/vnstock/du-lieu-thi-truong-market-data),
truy cập ngày 11/09/2026. Tài liệu mô tả API OHLCV/chỉ số và minh họa dấu thời gian
07:00 không kèm múi giờ; không xác lập thời điểm công bố lịch sử hoặc phương pháp xử
lý sự kiện doanh nghiệp.

E2: file đã cài `.venv/Lib/site-packages/vnstock/explorer/kbs/quote.py`, SHA-256
`0c32a30d6d20b942ec5291bce84a6ffadb10975baba119396e92eddab88dff55`.
Các dòng 307–348 giữ trường thừa, phân tích thời gian, ép kiểu `volume` và chia OHLC
cổ phiếu cho 1.000. `const.py` ánh xạ o/h/l/c/v nhưng không ánh xạ `va` sang giá trị
giao dịch chuẩn đã xác minh. [Mã nguồn thượng nguồn](https://raw.githubusercontent.com/thinh-vu/vnstock/main/vnstock/explorer/kbs/quote.py)
là nhánh `main` luôn thay đổi, không phải bằng chứng các byte trùng với bản đã cài.

E3: Bản ghi FPT đầu tiên có `va/volume` xấp xỉ 29.176 VND nếu giả định `va` tính bằng
VND và `volume` tính bằng cổ phiếu, nằm ngoài khoảng OHLC giả định 67.300–71.700 VND.
Đây là cảnh báo về tính nhất quán, không phải bằng chứng trường nào sai. Không khớp hệ
số dựa trên quan sát này.

Chính sách chuyển đổi yêu cầu bằng chứng cho mọi ánh xạ ngữ nghĩa khác `null`, mã băm
trình thu thập được phê duyệt rõ ràng, phiên bản và nguồn của vỏ dữ liệu, danh mục/lịch
tham chiếu cùng bản ghi trạng thái/thời điểm khả dụng. Bằng chứng là dữ liệu đã được
người dùng rà soát, không phải bộ phán định chân lý tự động. Chính sách cho bộ thử
nghiệm giả lập phải khai báo `synthetic` và không bao giờ mở điều kiện thử nghiệm thật
hay mở rộng. Trường chưa xác minh giữ `null` khi schema cho phép; cơ sở giá `unknown`
vẫn không đủ điều kiện.

Bằng chứng cần bổ sung tiếp theo: đặc tả có ngày về đơn vị/phương pháp điều chỉnh của
nhà cung cấp; OHLC và sự kiện độc lập quanh ngày giao dịch không hưởng quyền; quy ước
múi giờ/ngày đã xác minh; danh mục lịch sử có hủy niêm yết/chuyển sàn; lịch sàn độc
lập và thời điểm công bố. Chưa có thử nghiệm thật nào được mở rộng qua các điều kiện
còn chưa giải quyết này.
