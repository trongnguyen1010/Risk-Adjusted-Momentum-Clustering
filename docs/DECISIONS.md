# Nhật ký quyết định

## v0.2 — 12/09/2026

- ADR-007: Chuyển đổi dữ liệu phải qua kiểm tra bằng chứng; đơn vị, cơ sở điều chỉnh và múi giờ chưa rõ vẫn giữ trạng thái chưa xác minh. Danh mục niêm yết hiện tại không thay thế danh mục lịch sử. Xem data/vendor_semantics.md.
- ADR-008: Áp dụng hợp đồng dữ liệu và đặc trưng 1.1; hỗ trợ UPCOM và giá trị thiếu khai báo rõ. Giữ khoảng định danh nửa kín. Kết quả mới dùng lần chạy mới, không di chuyển hoặc ghi đè dữ liệu vendor/raw cũ.
- ADR-009: Giữ nguyên cửa sổ và công thức đặc trưng hiện có; bổ sung các trường riêng cho rủi ro giảm giá và tỷ số động lượng/độ biến động. Tiền xử lý mặt cắt ngang được cấu hình và thực hiện riêng từng tháng.
- ADR-010: KMeans xác định bằng thư viện chuẩn; các chỉ tiêu đánh giá k không tự chọn mô hình. Căn chỉnh theo thành viên chung để tránh so trực tiếp tâm cụm đã chuẩn hóa trong các hệ tọa độ khác nhau.
- ADR-011: Triển khai mô phỏng trên chuỗi lợi suất bằng tỷ trọng phân số và giả định công khai. Sổ giao dịch theo cổ phiếu thực tế vẫn phụ thuộc bằng chứng giá gốc và sự kiện doanh nghiệp; không trình bày tỷ trọng mô phỏng như số cổ phiếu hoặc giá khớp thật.
- ADR-012: Chỉ đánh giá trên tập phát triển. Quy trình kiểm định độc lập đã khóa và xác thực thống kê trên dữ liệu thật còn mở. Chi phí và lợi suất tiền mặt bằng 0 là lựa chọn cho nghiên cứu giả lập.
- ADR-013: Điều kiện nghiệm thu thử nghiệm/mở rộng không chấp nhận dữ liệu giả lập. Tải hơn 10 mã cần bộ thử nghiệm thật đạt; chưa mở rộng trong đợt triển khai này.
- ADR-014: Tiếp tục lần chạy đã hoàn tất chỉ đọc sau khi mã băm hợp lệ. Giữ thông tin từng lần chạy; thời gian thực thi giữa các lần chạy mới không được kỳ vọng giống nhau tuyệt đối.
- ADR-015: Không sửa lỗi mã băm dữ liệu nhà cung cấp bằng cách cập nhật giá trị băm kỳ vọng. Chỉ được sao chép bytes trong cache khớp mã băm gốc sang snapshot mới có thông tin phục hồi. Giữ nguyên file cũ; vẫn cần bằng chứng về ý nghĩa dữ liệu.
- ADR-016: Theo yêu cầu người dùng ngày 12/09/2026, báo cáo bàn giao, báo cáo rà soát, mẫu sinh báo cáo và diễn giải giả định của demo dùng tiếng Việt. Giữ tên trường, mã quyết định, mã lần chạy và thuật toán khi cần truy vết. Sinh thí nghiệm mới cho báo cáo tiếng Việt để không làm sai mã băm lịch sử. Đây là thay đổi ngôn ngữ, không đổi giả định số hoặc phương pháp nghiên cứu.

Đây là các quyết định kỹ thuật theo yêu cầu người dùng, chưa phải xác nhận nghiệm thu của mentor.

Ngày khởi tạo: 11/09/2026. “Đã chọn cho code nền” không đồng nghĩa “mentor duyệt”. Ghi ngày/người xác nhận khi quyết định học thuật được chốt.

| ID | Câu hỏi | Quyết định / trạng thái | Căn cứ / người xác nhận | Phần ảnh hưởng |
|---|---|---|---|---|
| ADR-001 | Có nguồn mentor cấp? | Không; tự tìm hiểu | Người dùng xác nhận trong yêu cầu | SOURCE_EVALUATION, crawler |
| ADR-002 | Nền tảng ban đầu | Python 3.11+, phần lõi dùng thư viện chuẩn, JSONL, xử lý lô cục bộ | Chọn triển khai bộ nền ngày 11/09 | gói mã nguồn, IO, CLI |
| ADR-003 | Nguồn khảo sát đầu tiên | Vnstock Community 4.0.6; chưa xác nhận đủ T1 | Tài liệu API và bộ chuyển đổi; xem VALIDATION | SDK tùy chọn/vùng trung gian |
| ADR-004 | `raw_close` cho phép null | Cho phép thiếu thật trong hợp đồng dữ liệu; chương trình dùng giá gốc cần chặn riêng | Tránh tạo giả giá gốc từ giá điều chỉnh | schema giá, M3 |
| ADR-005 | Khoảng hiệu lực metadata | `[valid_from, valid_to)`, `null` = mở; `provisional` không đủ điều kiện | Lựa chọn kỹ thuật, cần ánh xạ đúng nguồn | QC, đặc trưng |
| ADR-006 | NA/lịch | Không điền; lịch chỉ rõ cuối tháng; chính sách dữ liệu đến trễ theo hướng bảo thủ | Đặc tả đặc trưng 1.0 | đặc trưng và độ phủ |
| OPEN-01 | Cách đếm 300 mã/5 năm | Chưa chốt; báo độ phủ đa chiều, chưa tự động nghiệm thu | Trưởng nhóm cần xác nhận khi nghiệm thu | M1 |
| OPEN-02 | Giá điều chỉnh gồm quyền lợi nào? | Chưa xác minh trên nguồn thật | DE/QC kiểm tra mẫu | `accepted_adjustments`, M3 |
| OPEN-03 | Nguồn định danh/lịch/sự kiện lịch sử | Chưa chọn đủ | DE phụ trách khảo sát | PIT, vòng đời niêm yết, khớp lệnh |
| OPEN-04 | rf | Demo=0 chỉ minh họa; nghiên cứu dùng nguồn/tenor hoặc giả định đã ghi rõ | DS/QC chưa chốt | Sharpe |
| OPEN-05 | Đặc trưng rủi ro/phương án đối chứng M1 | Mã nguồn đặc trưng rủi ro đã có; yêu cầu nghiệm thu cụ thể chưa xác nhận | Các PDF xem phương án đối chứng M1 là đề xuất | Kế hoạch M1 |
| OPEN-06 | Ngày của tập phát triển/kiểm định độc lập | Chưa chốt khi chưa biết độ phủ bộ dữ liệu | DS/mentor hoặc người rà soát chuyên môn | M2/M3 |
| OPEN-07 | Vốn/phí/thuế/lô/trượt giá/khớp/quyền lợi | Chưa chốt | Đặc tả chiến lược phải có trước tập kiểm định độc lập | Chương trình M3 |
| OPEN-08 | Phạm vi M3/UI/báo cáo | Theo phạm vi tối thiểu trong PDF đến khi có thay đổi | Thiếu tài liệu khởi động gốc để đối chiếu | Bàn giao |

Mẫu quyết định mới: ID → vấn đề → các lựa chọn → lựa chọn chốt và lý do → bằng chứng → ai xác nhận/ngày → file/config/test cần đổi → giới hạn còn lại.
