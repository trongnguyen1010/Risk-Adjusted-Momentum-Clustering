# Nhật ký thay đổi

## Bổ sung ngày 12/09/2026 — Báo cáo tiếng Việt

- Chuyển báo cáo triển khai theo giai đoạn và báo cáo rà soát repository sang tiếng Việt.
- Chuyển mẫu sinh report nghiên cứu và phần diễn giải giả định trong cấu hình demo sang tiếng Việt; giữ nguyên tham số và công thức nghiên cứu.
- Sinh bản report pilot tiếng Việt trong một thí nghiệm mới để giữ nguyên báo cáo và checksum của các lần chạy cũ.
- Việt hóa phần nhật ký v0.2 và các quyết định ADR-007 đến ADR-015; bổ sung ADR-016 về ngôn ngữ báo cáo theo yêu cầu người dùng.
- Bản tiếng Việt: `experiment-6436b9f4eb78`. Đối chiếu 9 tệp kết quả số với bản trước: giống nhau từng byte; xác minh toàn bộ checksum đầu ra của cả hai lần chạy và kiểm tra cú pháp thành công. Không chạy lại toàn bộ 44 kiểm thử vì lần này chỉ sửa nội dung báo cáo; kết quả 44/44 thuộc đợt triển khai kỹ thuật trước.

## 0.2.0 — 2026-09-12

- Rà soát repository, SDK đã cài và ý nghĩa các trường dữ liệu nhà cung cấp; ghi rõ đơn vị, phương pháp điều chỉnh giá, múi giờ và dữ liệu tham chiếu còn chưa xác minh. Chưa cho phép chuyển đổi hoặc tải diện rộng dữ liệu thật.
- Bổ sung bộ chuyển đổi có kiểm tra bằng chứng và dữ liệu bất biến, ghép nguồn tham chiếu, cách ly lỗi và đầu vào dùng chung cho pipeline chuẩn; có bộ thử nghiệm giả lập tái lập được.
- Nâng hợp đồng dữ liệu lên 1.1: hỗ trợ UPCOM, cho phép thiếu giá/khối lượng chưa xác minh, bổ sung thời điểm khả dụng và cơ sở của lịch/chỉ số, thông tin sự kiện/lãi suất, số quan sát và lý do thiếu đặc trưng, động lượng điều chỉnh rủi ro và độ biến động giảm giá.
- Bổ sung điều kiện kiểm tra chỉ số tham chiếu, OHLC và tính đúng thời điểm; đặt lại cửa sổ khi đổi cơ sở điều chỉnh giá. Giữ nguyên định nghĩa động lượng, độ biến động, Sharpe, beta và mức sụt giảm tối đa. Tiếp tục một lần chạy đã hoàn tất chỉ kiểm tra, không ghi đè.
- Triển khai KMeans xác định theo từng thời điểm, tiền xử lý, đánh giá số cụm k, nhãn có ý nghĩa kinh tế, độ ổn định không phụ thuộc hoán vị nhãn và ma trận chuyển cụm đã căn chỉnh.
- Bổ sung mô phỏng danh mục trên chuỗi lợi suất với tỷ trọng phân số, khớp sau tín hiệu, chi phí, bốn chiến lược, so sánh chỉ số tham chiếu, bootstrap ghép cặp, phân tích giai đoạn/độ nhạy chi phí và báo cáo/biểu đồ theo phiên bản.
- Bổ sung dữ liệu mẫu và kiểm thử tích hợp/hồi quy ngoại tuyến; chỉ cho tải lớn sau khi bộ thử nghiệm thật đạt. Sổ giao dịch theo số lượng cổ phiếu, nghiệm thu dữ liệu thật và quy trình kiểm định độc lập đã khóa vẫn chưa hoàn tất.
- Phát hiện các file nhà cung cấp có mã băm lệch do đổi định dạng; bổ sung phục hồi đúng bytes từ cache sang snapshot mới có thông tin truy vết, không sửa file gốc.
- Kết quả kiểm chứng cuối đợt triển khai: 44/44 kiểm thử đạt; pilot 6 mã giả lập trong 18 tháng chạy xuyên suốt. Chi tiết và mã lần chạy nằm trong docs/VALIDATION.md và docs/phase_report.md.

Ghi thay đổi có ảnh hưởng tới người dùng/developer và bằng chứng kiểm thử. Không dùng changelog như bằng chứng kết quả nghiên cứu chưa chạy.

## 0.1.0 - 2026-09-11

### Bổ sung

- Đánh giá năm PDF, kiến trúc module, data contract, feature specification, source evaluation, plan M1/M2/M3, development rules và decision log.
- Core Python CLI: CSV/HTTP JSON → raw snapshot → normalization/QC → clean JSONL → monthly features.
- Crawl checkpoint theo trang, SHA-256, config/code/data hash, bounded retry, rate limit, timeout, pagination và resume.
- Vnstock Community 4.0.6 collector riêng cho sample equity/index và listing; vendor staging không tự được xem là canonical.
- 12 schema JSON theo định dạng table contract; runtime validate cho input, vendor snapshot và feature, interface contracts cho clustering/evaluation/backtest.
- Synthetic fixture 12 mã/18 tháng và 27 test về feature, QC, availability, pagination/retry/resume và cô lập SDK worker.
- Lock dependencies tùy chọn cho môi trường Vnstock đã cài, template model card/strategy spec/weekly report.

### Quyết định và giới hạn

- JSONL là định dạng MVP; chưa có Parquet storage hoặc incremental merge tự động.
- raw_close nullable để ghi nhận dữ liệu thiếu; không tự đồng nhất raw và adjusted.
- M2/M3 là interfaces và schema dự kiến; chưa có trained models, backtest hoặc UI hoàn chỉnh.
- Chưa chứng minh coverage 300 mã/5 năm hoặc hoàn thành nghiệm thu M1. Chi tiết kết quả chạy ở `docs/VALIDATION.md`.
