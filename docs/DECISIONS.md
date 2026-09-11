# Decision log

Ngày khởi tạo: 11/09/2026. “Đã chọn cho code nền” không đồng nghĩa “mentor duyệt”. Ghi ngày/người xác nhận khi quyết định học thuật được chốt.

| ID | Câu hỏi | Quyết định / trạng thái | Căn cứ / người xác nhận | Phần ảnh hưởng |
|---|---|---|---|---|
| ADR-001 | Có nguồn mentor cấp? | Không; tự tìm hiểu | Người dùng xác nhận trong yêu cầu | SOURCE_EVALUATION, crawler |
| ADR-002 | Stack ban đầu | Python 3.11+, core stdlib, JSONL, batch local | Chọn triển khai bộ nền ngày 11/09 | package, IO, CLI |
| ADR-003 | Nguồn khảo sát đầu tiên | Vnstock Community 4.0.6; chưa xác nhận đủ T1 | Tài liệu API và adapter; xem VALIDATION | Optional SDK/staging |
| ADR-004 | Nullable raw_close | Cho thiếu thật ở data contract; engine raw cần chặn riêng | Tránh giả tạo raw từ adjusted | prices schema, M3 |
| ADR-005 | Metadata interval | [valid_from, valid_to), null = mở; provisional không eligible | Chọn engineering, cần map đúng nguồn | QC, feature |
| ADR-006 | NA/calendar | Không fill; calendar chỉ rõ cuối tháng; delayed data policy bảo thủ | Feature spec 1.0 | feature và coverage |
| OPEN-01 | Cách đếm 300 mã/5 năm | Chưa chốt; báo coverage đa chiều, chưa auto accept | Lead cần xác nhận khi nghiệm thu | M1 |
| OPEN-02 | Adjusted gồm quyền lợi nào? | Chưa xác minh trên nguồn thật | DE/QC audit sample | accepted_adjustments, M3 |
| OPEN-03 | Nguồn historical IDs/calendar/actions | Chưa chọn đủ | DE phụ trách khảo sát | PIT, listing lifetime, execution |
| OPEN-04 | rf | Demo=0 chỉ minh họa; nghiên cứu dùng nguồn/tenor hoặc giả định đã ghi rõ | DS/QC chưa chốt | Sharpe |
| OPEN-05 | M1 risk features/baseline | Code risk features đã có; yêu cầu nghiệm thu cụ thể chưa xác nhận | Các PDF xem baseline M1 là đề xuất | Plan M1 |
| OPEN-06 | Development/holdout dates | Chưa chốt khi chưa biết dataset coverage | DS/mentor hoặc reviewer chuyên môn | M2/M3 |
| OPEN-07 | Vốn/phí/thuế/lô/slippage/khớp/quyền lợi | Chưa chốt | Strategy spec phải có trước holdout | Engine M3 |
| OPEN-08 | Scope M3/UI/report | Theo phạm vi tối thiểu trong PDF đến khi có thay đổi | Thiếu kickoff gốc để đối chiếu | Delivery |

Mẫu quyết định mới: ID → vấn đề → các lựa chọn → lựa chọn chốt và lý do → bằng chứng → ai xác nhận/ngày → file/config/test cần đổi → giới hạn còn lại.
