# Kế hoạch phát triển T1

Ngày cập nhật: 11/09/2026. Ba mốc dưới đây dẫn theo năm PDF trong `TaiLieu`; tài liệu khởi động gốc chưa có để đối chiếu độc lập. Trạng thái “đã hoàn thành” chỉ dùng khi có tệp kết quả/kiểm thử; người phụ trách là vai trò dự kiến cần gán tên trong công cụ theo dõi.

## M1 - 19/09/2026: dữ liệu và đặc trưng

| ID | Việc và đầu vào | Người phụ trách / người rà soát | Hạn dự kiến | Đầu ra và điều kiện hoàn thành | Trạng thái |
|---|---|---|---|---|---|
| F01 | Đọc PDF, đối chiếu phạm vi | Trưởng nhóm / QC | 11/09 | DOCUMENT_REVIEW, ARCHITECTURE; phân biệt yêu cầu và giả định | Đã hoàn thành trong bộ nền |
| F02 | Tạo hợp đồng và pipeline | DE/QD / QC | 11/09 | schema, CLI, dữ liệu gốc/mã băm/tiếp tục, kiểm thử chạy được | Đã hoàn thành trong bộ nền |
| D01 | Tải mẫu thật 10–20 mã + VNINDEX | DE / DS | 12/09 | manifest nhà cung cấp, mẫu giá/metadata, nhật ký lỗi | Đã có bộ chuyển đổi; nghiệm thu nguồn còn mở |
| D02 | Xác minh nguồn/cơ sở điều chỉnh/đơn vị | DE / QC | 12–13/09 | SOURCE_EVALUATION có ví dụ sự kiện doanh nghiệp và bảng trường thiếu | Chưa hoàn thành; phụ thuộc D01 |
| D03 | Định danh lịch sử và lịch phiên | DE / QC | 13–15/09 | danh mục, lịch, ánh xạ ticker có khoảng hiệu lực, kiểm thử ngày đổi mã | Chưa hoàn thành |
| D04 | Mở rộng khoảng 6 năm/≥300 mã | DE / trưởng nhóm | 13–16/09 | độ phủ theo cả hai cách hiểu 300 mã/5 năm; xử lý công việc lỗi | Chưa hoàn thành; phụ thuộc D02/D03 |
| F03 | Tích hợp đặc trưng trên dữ liệu thật | DS / QC | 15–17/09 | động lượng/rủi ro, lý do NA, kiểm tra hợp lý sự kiện doanh nghiệp | Đã có hàm; chưa kiểm tra dữ liệu thật |
| E01 | EDA M1 | DS / DE | 16–18/09 | notebook, phân phối/tương quan/mức thiếu, 3–5 nhận xét có số liệu | Chưa hoàn thành |
| R01 | Tái lập và demo M1 | QD / người khác trong nhóm | 18–19/09 | chạy máy khác, ảnh chụp/phiên bản, danh sách kiểm đủ phạm vi | Chưa hoàn thành |

Ước lượng tham khảo: D01 2–4 giờ kỹ thuật cộng chờ API; D02/D03 mỗi việc 4–8 giờ cộng xác minh nguồn; D04 4–8 giờ orchestration cộng thời gian tải; E01 4–6 giờ; R01 2–4 giờ. Không xem đây là cam kết khi chưa biết chất lượng nguồn và quỹ giờ nhóm.

Nếu đến buổi rà soát 12/09 chưa có mẫu đủ trường, cần trình bày báo cáo khoảng trống và quyết định cần chốt; không tự báo hoàn thành M1 bằng dữ liệu giả lập hoặc âm thầm giảm phạm vi.

## M2 - 17/10/2026: phân cụm và ổn định

| Khoảng | Công việc | Người phụ trách / người rà soát | Điều kiện hoàn thành |
|---|---|---|---|
| 20–26/09 | Quy trình tập phát triển/kiểm định độc lập, K-Means/Ward và PCA | DS / QD/QC | Cùng đầu vào và tiền xử lý; tệp kết quả/gói mô hình/chỉ tiêu có phiên bản |
| 27/09–03/10 | GMM, nhiều seed, loại bỏ từng thành phần động lượng so với điều chỉnh rủi ro | DS / QC | Bảng ba thuật toán, độ hội tụ, kích thước/hồ sơ cụm, lý do giữ/loại |
| 04–10/10 | Ảnh chụp trượt, ARI, ánh xạ, chuyển cụm | DS/QD / QC | Hoán vị nhãn ARI=1; tách mã vào/ra; lưu nhãn gốc/đã căn chỉnh |
| 11–17/10 | Chọn mô hình, phiếu mô hình, báo cáo ổn định, khóa chiến lược | Trưởng nhóm/DS/QD / mentor hoặc người rà soát | Người khác chạy lại; không tinh chỉnh trên tập kiểm định độc lập; phạm vi M3 được ghi rõ |

Chỉ triển khai `Protocol` hiện tại thành mô-đun thực sau khi đầu vào đã ổn định. Thêm schema hồ sơ cụm/thí nghiệm/manifest mô hình trước khi FE phụ thuộc chúng. Không tạo chỉ tiêu giả cho phần chưa có.

## M3 - 07/11/2026: mô phỏng quá khứ, bảng điều khiển, bàn giao

| Khoảng | Công việc | Người phụ trách / người rà soát | Điều kiện hoàn thành |
|---|---|---|---|
| 18–24/10 | Tín hiệu/khớp lệnh/hạch toán/chi phí, chỉ số tham chiếu | QD / QC | Sổ giao dịch, tiền mặt/vị thế/NAV; phí/lô/sự kiện/thời gian có kiểm thử; không dùng `adj_close` làm giá gốc |
| 18–24/10 | Tích hợp tệp kết quả vào UI | FE / DS/QD | Tổng quan dữ liệu, cụm, chuyển cụm, NAV; cùng `run_id` |
| 25–31/10 | Tập kiểm định độc lập và phân tích độ nhạy, rà soát, báo cáo | DS/QD/QC / trưởng nhóm | Báo kết quả gộp/ròng và đối chứng; không sửa quy trình theo tập kiểm định độc lập |
| 01–07/11 | Đóng băng, chạy máy khác, báo cáo/trang chiếu/demo | Cả nhóm / trưởng nhóm | README, notebook, bảng điều khiển, báo cáo ≤20 trang theo cách đếm được xác nhận |

Chưa bắt đầu viết chương trình giao dịch đầy đủ khi chưa có giá gốc và sự kiện doanh nghiệp. Nếu dữ liệu chỉ đủ xấp xỉ theo lợi suất, phải đặc tả riêng phạm vi mô phỏng đó; không tự xem là hoàn thành mọi yêu cầu về sổ giao dịch.

## Mẫu công việc và báo cáo

Mỗi công việc: ID, mục tiêu, đầu vào/phiên bản, người phụ trách, người rà soát, đường dẫn đầu ra, kiểm tra nghiệm thu, ước lượng, hạn, phần phụ thuộc, trạng thái, liên kết PR/`run_id` và quyết định liên quan.

Báo cáo tuần: đã xong kèm bằng chứng; con số thực đo; trở ngại/quyết định cần người trả lời; đầu ra tuần tới. Khi nghiệm thu, QC/người rà soát phải khác người phụ trách.

## Điều kiện phát hành

- M1: dữ liệu thật đủ phạm vi đã thống nhất, schema/nguồn/độ phủ, bốn đặc trưng động lượng, EDA và máy khác chạy lại.
- M2: ba thuật toán + PCA, kết quả so sánh, hồ sơ cụm, độ ổn định, cấu hình/phiếu mô hình, không rò rỉ dữ liệu.
- M3: mô phỏng quá khứ có phí so với VNINDEX và các phương án đối chứng, UI, notebook, báo cáo, trang chiếu, tệp kết quả dự phòng.
- T5/realtime/API phức tạp/thuật toán thứ tư chỉ xét sau phần bắt buộc; thay phạm vi phải ghi DECISIONS.
