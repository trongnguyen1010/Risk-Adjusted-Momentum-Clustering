# Plan phát triển T1

Ngày cập nhật: 11/09/2026. Ba mốc dưới đây dẫn theo năm PDF trong TaiLieu; kickoff gốc chưa có để đối chiếu độc lập. Tình trạng “done” chỉ dùng khi có artifact/test; owner là vai trò dự kiến cần gán tên trong tracker.

## M1 - 19/09/2026: dữ liệu và đặc trưng

| ID | Việc và input | Owner / reviewer | Hạn dự kiến | Đầu ra và điều kiện hoàn thành | Trạng thái |
|---|---|---|---|---|---|
| F01 | Đọc PDF, đối chiếu scope | Lead / QC | 11/09 | DOCUMENT_REVIEW, ARCHITECTURE; phân biệt yêu cầu và giả định | Done trong bộ nền |
| F02 | Tạo contracts và pipeline | DE/QD / QC | 11/09 | schema, CLI, raw/hash/resume, test chạy được | Done trong bộ nền |
| D01 | Tải sample thật 10–20 mã + VNINDEX | DE / DS | 12/09 | vendor manifest, giá/metadata sample, log lỗi | Adapter có; nghiệm thu nguồn còn mở |
| D02 | Xác minh nguồn/adjustment/đơn vị | DE / QC | 12–13/09 | SOURCE_EVALUATION có ví dụ corporate action và bảng field thiếu | Open; phụ thuộc D01 |
| D03 | Historical ID và lịch phiên | DE / QC | 13–15/09 | master, calendar, mapping ticker có interval, test ngày đổi mã | Open |
| D04 | Mở rộng khoảng 6 năm/≥300 mã | DE / Lead | 13–16/09 | coverage theo cả hai cách hiểu 300 mã/5 năm; xử lý job lỗi | Open; phụ thuộc D02/D03 |
| F03 | Tích hợp feature trên dữ liệu thật | DS / QC | 15–17/09 | momentum/risk, NA reasons, sanity checks corporate actions | Hàm có; audit thật chưa làm |
| E01 | EDA M1 | DS / DE | 16–18/09 | notebook, phân phối/correlation/missingness, 3–5 nhận xét có số liệu | Open |
| R01 | Tái lập và demo M1 | QD / người khác trong nhóm | 18–19/09 | chạy máy khác, snapshot/version, checklist đủ scope | Open |

Ước lượng tham khảo: D01 2–4 giờ kỹ thuật cộng chờ API; D02/D03 mỗi việc 4–8 giờ cộng xác minh nguồn; D04 4–8 giờ orchestration cộng thời gian tải; E01 4–6 giờ; R01 2–4 giờ. Không xem đây là cam kết khi chưa biết chất lượng nguồn và quỹ giờ nhóm.

Nếu đến review 12/09 chưa có sample đủ trường, mang gap report và quyết định cần chốt; không tự báo hoàn thành M1 bằng synthetic hoặc âm thầm giảm phạm vi.

## M2 - 17/10/2026: phân cụm và ổn định

| Khoảng | Công việc | Owner / reviewer | Definition of Done |
|---|---|---|---|
| 20–26/09 | Protocol development/holdout, K-Means/Ward và PCA | DS / QD/QC | Cùng input và preprocessing; artifacts/model bundle/metrics có version |
| 27/09–03/10 | GMM, nhiều seed, ablation momentum vs risk-adjusted | DS / QC | Bảng ba thuật toán, convergence, cluster sizes/profiles, lý do giữ/loại |
| 04–10/10 | Rolling snapshot, ARI, mapping, transitions | DS/QD / QC | Hoán vị nhãn ARI=1; tách entry/exit; lưu raw/aligned labels |
| 11–17/10 | Chọn model, model card, stability report, khóa strategy | Lead/DS/QD / mentor hoặc reviewer | Người khác chạy lại; không tuning trên holdout; scope M3 được ghi rõ |

Chỉ triển khai `Protocol` hiện tại thành module thực sau khi input đã ổn định. Thêm schema profiles/experiment/model manifest trước khi FE phụ thuộc chúng. Không tạo metric giả cho phần chưa có.

## M3 - 07/11/2026: backtest, dashboard, bàn giao

| Khoảng | Công việc | Owner / reviewer | Definition of Done |
|---|---|---|---|
| 18–24/10 | Signal/execution/accounting/costs, benchmark | QD / QC | Ledger, cash/holdings/NAV; phí/lô/actions/time có tests; không dùng adj_close làm raw |
| 18–24/10 | Tích hợp UI artifact | FE / DS/QD | Data overview, cụm, transitions, NAV; cùng run_id |
| 25–31/10 | Holdout và sensitivity, audit, báo cáo | DS/QD/QC / Lead | Báo gross/net và đối chứng; không sửa protocol theo holdout |
| 01–07/11 | Freeze, chạy máy khác, report/slide/demo | Cả nhóm / Lead | README, notebook, dashboard, báo cáo ≤20 trang theo cách đếm được xác nhận |

Chưa bắt đầu viết engine giao dịch đầy đủ khi chưa có raw prices và actions. Nếu dữ liệu chỉ đủ return approximation, phải đặc tả phạm vi mô phỏng đó riêng; không tự xem là hoàn thành mọi yêu cầu ledger.

## Mẫu task và báo cáo

Mỗi task: ID, mục tiêu, input/version, owner, reviewer, output path, acceptance checks, ước lượng, deadline, dependencies, trạng thái, link PR/run_id và quyết định liên quan.

Báo cáo tuần: đã xong kèm bằng chứng; con số thực đo; blocker/quyết định cần người trả lời; đầu ra tuần tới. QC/reviewer phải là người khác với owner khi nghiệm thu.

## Điều kiện release

- M1: dữ liệu thật đủ scope đã thống nhất, schema/source/coverage, bốn momentum, EDA và máy khác chạy lại.
- M2: ba thuật toán + PCA, kết quả so sánh, profiles, stability, config/model card, không leakage.
- M3: backtest có phí so VNINDEX và đối chứng, UI, notebook, report, slide, artifact dự phòng.
- T5/realtime/API phức tạp/thuật toán thứ tư chỉ xét sau phần bắt buộc; thay phạm vi phải ghi DECISIONS.
