# Đánh giá lại tài liệu - 11/09/2026

## Kết luận

**Phù hợp để bắt đầu triển khai nền tảng T1, chưa đủ để coi thiết kế nghiên cứu và nguồn dữ liệu đã được xác nhận.** Năm PDF thống nhất về pipeline dữ liệu → feature → phân cụm cổ phiếu → ổn định qua thời gian → backtest → dashboard. Không thấy mâu thuẫn lớn về mục tiêu hoặc ba mốc; điểm cần sửa chủ yếu là chuyển đề xuất thành contract, bằng chứng và quyết định có người chịu trách nhiệm.

Khi kiểm tra, `SourceCode` chưa có code ứng dụng. Do đó đây là đối chiếu giữa các tài liệu và việc thiết kế project mới, chưa phải audit một hệ thống đang chạy.

## Vai trò của từng tài liệu

| PDF trong `TaiLieu` | Căn cứ đã đọc | Đánh giá và cách áp dụng |
|---|---|---|
| `Delta_T1_Ke_hoach_nhom.pdf` (11 trang) | Tr. 1–2 scope/mốc; 3–7 kỹ thuật; 8 kiến trúc; 9–11 phân vai/quyết định | Dùng làm kế hoạch kỹ thuật tổng thể; tách phần đề xuất khỏi yêu cầu nghiệm thu |
| `Delta_T1_Ke_hoach_nhom_gui_mentor.pdf` (14 trang) | Tr. 1–4 mục tiêu/dữ liệu; 5–11 đầu ra; 12 phân công; 13–14 câu hỏi | Phù hợp trao đổi mentor; không dùng thay data contract chi tiết |
| `Delta_T1_Lo_trinh_Data_Scientist_Quant_Developer.pdf` (10 trang) | Tr. 2–3 M1/test; 4–5 M2; 6–8 backtest/contracts; 9–10 lịch và nguồn | Có test và ranh giới DS/QD rõ; task ước lượng cần gán lại theo năng lực thực tế |
| `Delta_T1_Cam_nang_doc_va_ap_dung_hai_ke_hoach.pdf` (9 trang) | Tr. 1–3 cách đọc/mốc; 5–7 feature/model/backtest; 8–9 tracker | Phù hợp onboarding; không có bằng chứng dữ liệu thật hay kết quả mô hình |
| `Delta_T1_Huong_dan_du_lieu_va_cach_lam_project.pdf` (11 trang) | Tr. 3–7 dữ liệu/schema/crawler/QC; 8–10 feature và bàn giao | Sát nhu cầu triển khai nhất; schema cần thêm kiểu, nullable, temporal join và version có thực thi |

File `internship-2026-kickoff.pdf` được các PDF viện dẫn nhưng **không có trong folder**. Các mốc/yêu cầu bên dưới là thông tin nhất quán được các PDF dẫn lại; chưa xác minh độc lập với kickoff gốc.

## Những điểm đã hợp lý

- M1 ưu tiên dữ liệu đúng và momentum, không dành phần lớn thời gian tinh chỉnh clustering.
- Phân cụm theo mặt cắt cổ phiếu ở mỗi snapshot; không nhầm với phân cụm chế độ thị trường.
- Tách raw/adjusted, cảnh báo survivorship bias, thiếu phiên, corporate actions và leakage.
- M2 dùng ba thuật toán với PCA, so sánh cùng universe; ARI trên tập mã chung và tách entry/exit.
- M3 có phí, benchmark VNINDEX, ledger, holdout và người khác chạy lại. Không hứa lợi nhuận.

## Khoảng trống cần bổ sung

| Điểm | Ảnh hưởng | Cách xử lý trong bộ nền |
|---|---|---|
| PDF giả định có nguồn mentor cấp hoặc xác nhận | Không có API/CSV cụ thể để crawl | Người dùng xác nhận tự tìm nguồn; thêm khảo sát Vnstock và adapter CSV/HTTP độc lập |
| Chưa rõ “300 mã/5 năm” | Không thể tự đặt kết luận đạt M1 | Xuất coverage theo mã/năm/sàn/snapshot; giữ `m1_accepted=false` |
| Chưa có định danh lịch sử đáng tin cậy | Đổi ticker/chuyển sàn gây join sai | `security_id`, khoảng `[valid_from,valid_to)`, `identity_status`, `available_at`; QC temporal join |
| Schema giá chưa có `available_at`/ý nghĩa adjusted | Có thể dùng dữ liệu chưa biết hoặc sai lợi suất | Bổ sung cả hai, giữ `fetched_at` riêng |
| `raw_close` bắt buộc trong PDF nhưng nguồn có thể chỉ có chuỗi điều chỉnh | Dễ gán giả giá gốc | Cho nullable để thể hiện thiếu thật; backtest giao dịch phải yêu cầu raw riêng |
| Không chốt lịch phiên/tháng chưa kết thúc | Snapshot sai khi dataset dừng giữa tháng | Calendar có `is_month_end`, `close_at`, `decision_at`; không lấy ngày cuối file làm cuối tháng |
| Chưa chốt rf/holdout/khớp/phí/quyền lợi | Không thể coi kết quả M3 là xác nhận | Đưa vào decision log và protocol; demo rf=0 có nhãn |
| Chưa có code/test/version thực tế | Plan chưa tái lập được | Tạo CLI, raw checkpoint, hash, schema thực thi và tests |
| Lịch 08–10/09 đã qua, nguồn thật chưa có | M1 ngày 19/09 có rủi ro tiến độ | Điều chỉnh plan bắt đầu 11/09; không đánh dấu task quá hạn là xong |

## Phạm vi chốt để viết code

Core Python chạy local, một pipeline batch có module. JSONL làm định dạng trao đổi đầu tiên để inspect và test không cần dependency; Parquet là bước tối ưu sau đo tải thật. Đây là thay đổi triển khai so với Parquet đề xuất trong PDF, không thay đổi tên/ý nghĩa schema.

Phiên bản này có ingestion và feature chạy được, không tuyên bố hoàn tất M1/M2/M3. Chưa có EDA nghiên cứu trên dữ liệu thật, ba mô hình, stability, engine backtest hay UI hoàn chỉnh. Không mở rộng intraday, giao dịch thật, T5 hoặc hệ thống phân tán.
