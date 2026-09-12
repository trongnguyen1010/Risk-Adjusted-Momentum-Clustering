# Báo cáo triển khai theo giai đoạn — 12/09/2026

Đã triển khai và kiểm chứng phần lớn luồng nghiên cứu ngoại tuyến. **Giai đoạn dữ liệu thật chưa được nghiệm thu.** Chưa tải dữ liệu diện rộng, chưa gán danh mục niêm yết hiện tại ngược về quá khứ và không tạo giá trị thay cho thông tin chưa xác minh.

Báo cáo này phân biệt việc đã hoàn thành về kỹ thuật với điều kiện nghiệm thu nghiên cứu. Các giới hạn chi tiết được ghi tại [giới hạn nghiên cứu](research_limitations.md).

## Trạng thái từng giai đoạn

| Giai đoạn | Phần đã hoàn thành | Tệp thay đổi chính | Kiểm thử và kết quả | Vấn đề còn lại | Thông tin chưa xác minh | Bước tiếp theo |
|---|---|---|---|---|---|---|
| 1. Rà soát repository | Đã rà soát mô-đun, cấu hình, lược đồ, script, kiểm thử, tài liệu và cấu trúc dữ liệu nhà cung cấp | project_audit.md | Bộ 27 kiểm thử kế thừa đạt sau nhóm thay đổi lược đồ | Chưa có sổ giao dịch theo cổ phiếu thực tế, PCA và bộ so sánh nhiều mô hình | Thiếu dữ liệu tham chiếu lịch sử | Rà soát ý nghĩa dữ liệu |
| 2. Xác minh ý nghĩa dữ liệu | Đã lập bảng bằng chứng; vẫn chặn sử dụng dữ liệu thật | data/vendor_semantics.md, data/vendor_integrity.json | Đối chiếu mã băm, mã nguồn SDK và tài liệu chính thức | 5/10 file gốc đã đổi định dạng; phục hồi dữ liệu khớp mã băm sang bản mới | Giá gốc/điều chỉnh, đơn vị, va/volume, múi giờ và thời điểm công bố lịch sử | Bổ sung bằng chứng trước khi ánh xạ trường |
| 3. Mô hình dữ liệu chuẩn | Đã hoàn thiện phần kỹ thuật của hợp đồng dữ liệu 1.1 | schemas, quality.py, compute.py, data_dictionary.md | Kiểm thử lược đồ, chỉ số tham chiếu, OHLC, phiên thiếu, định danh và cơ sở điều chỉnh đều đạt | Chưa có đủ dữ liệu tham chiếu thật | Quy ước lịch, lãi suất và mức độ đầy đủ của sự kiện doanh nghiệp | Chuyển đổi dữ liệu nhà cung cấp |
| 4. Chuyển đổi và phục hồi dữ liệu | Đã có bộ chuyển đổi ngoại tuyến và phục hồi nguyên bản theo mã băm | promotion.py, recovery.py, scripts, configs | Kiểm thử chuyển đổi, toàn vẹn, quan hệ thời gian và dữ liệu tham chiếu đạt; bản phục hồi thật đã qua xác minh | Vẫn chặn chuyển đổi dữ liệu thật vì thiếu danh mục lịch sử và lịch giao dịch | Các trường chưa rõ ý nghĩa vẫn để chưa xác minh | Chạy thử dữ liệu thật khi đủ bằng chứng |
| 5. Bộ dữ liệu thử nghiệm | Hoàn thành một phần: 6 mã giả lập, 18 tháng, chạy xuyên suốt | synthetic.py, run_offline_pilot.py | Luồng nhà cung cấp → chuyển đổi → QC → đặc trưng → phân cụm → mô phỏng đạt | Chưa có bộ thử nghiệm thật hợp lệ gồm 3–10 mã | Lịch giả lập không thay thế lịch giao dịch Việt Nam | Thu thập nguồn và dữ liệu tham chiếu thật |
| 6. Đặc trưng nghiên cứu | Đã triển khai kỹ thuật, giữ nguyên các định nghĩa công thức cũ | compute.py, lược đồ và đặc tả đặc trưng | Kiểm thử cửa sổ 252 phiên cần 253 giá, điều kiện hợp lệ, phiên thiếu, dữ liệu đến trễ, cơ sở điều chỉnh và thêm dữ liệu tương lai đều đạt | Chính sách dữ liệu đến trễ còn bảo thủ; chưa phát lại từng phiên bản lịch sử | Việc nhà cung cấp điều chỉnh lại dữ liệu quá khứ | Đối chiếu với sự kiện doanh nghiệp thật |
| 7. Phân cụm | Đã có luồng nghiên cứu KMeans | clustering/kmeans.py, evaluation/stability.py | Tính xác định, đồng hạng, cụm suy biến, hoán vị nhãn và ma trận chuyển cụm đều được kiểm thử đạt | Chưa hoàn thành PCA/GMM/Ward và thẩm định mô hình độc lập | k và bộ đặc trưng hiện phục vụ minh họa kỹ thuật | Chốt quy trình phát triển và kiểm định độc lập cho dữ liệu thật |
| 8. Mô phỏng danh mục | Hoàn thành một phần: mô phỏng trên chuỗi lợi suất | portfolio.py, returns_engine.py, performance.py | Tỷ trọng, chi phí/tiền mặt, khớp phiên kế tiếp, phiên thiếu, tính bất biến trước dữ liệu tương lai, chỉ tiêu tính tay và bootstrap đều đạt | Chưa có sổ giao dịch đầy đủ theo số cổ phiếu, thanh toán và quyền lợi | Phí, lãi suất phi rủi ro và lợi suất tiền mặt đang là giả định công khai | Thiết kế kế toán giao dịch sau khi xác minh nguồn |
| 9. Mở rộng dữ liệu | Đã có bộ lập kế hoạch và điều kiện chặn; chưa tải diện rộng | planning.py, plan_crawl.py, điều kiện trong crawler | Dữ liệu giả lập không thể mở điều kiện tải lớn; chưa thực hiện yêu cầu mạng để mở rộng | Chưa có tập khoảng 300 mã theo lịch sử được xác minh | Chưa chứng minh đã loại bỏ thiên lệch sống sót | Chỉ mở rộng sau bộ thử nghiệm thật đạt |
| 10. Kết quả nghiên cứu | Đã sinh kết quả trên tập phát triển giả lập | research.py, script chạy, cấu hình, README và tài liệu phương pháp | Chạy lặp lại cho kết quả số giống nhau; đã sinh và xem biểu đồ | Chưa có kết luận từ dữ liệu thật, ý nghĩa thống kê hoặc nghiệm thu khóa luận | Mẫu nhỏ và nhân tạo | Tái lập độc lập và tiếp tục nghiên cứu trên dữ liệu thật |

## Bằng chứng đã thực hiện

- **Báo cáo thử nghiệm tiếng Việt:** [experiment-6436b9f4eb78](../data/experiments/experiment-6436b9f4eb78/report.md). Lần sửa ngôn ngữ giữ nguyên kết quả số: 9 tệp chỉ tiêu, đặc trưng cụm, đánh giá k, độ ổn định, độ nhạy chi phí và mô phỏng của 4 chiến lược khớp từng byte với bản trước. Toàn bộ mã băm đầu ra của cả bản cũ và bản mới đều hợp lệ.

- Các đợt kiểm thử lần lượt đạt 27, 41 và 43 bài. Đợt cuối của phần triển khai kỹ thuật, có kiểm thử phục hồi dữ liệu: **44/44 đạt, 115,640 giây**. Xem [bằng chứng kiểm thử](VALIDATION.md). Đây là kết quả đã chạy ở lượt triển khai trước, không phải tuyên bố chạy lại toàn bộ kiểm thử trong lần sửa ngôn ngữ.
- Kết quả nghiên cứu đầu tiên: `experiment-68f00ca6a296`, từ CSV giả lập 12 mã.
- Bộ thử nghiệm 6 mã qua chuyển đổi đã được lưu tại `experiment-d4d7bd22dead`; thông tin truy vết nằm trong manifest và `data/offline_pilots/*/result.json`.
- Luồng kiểm chứng xuyên suốt cuối đợt triển khai: `canonical-4c043c70287c` → `run-d7e3c24044ab` → `experiment-9a30d8e60047`. Kết quả gồm 108 bản ghi đặc trưng, 36 bản ghi gán cụm, 106 dòng giá trị danh mục theo ngày và 42 tệp đầu ra.
- Bản biểu đồ đã chỉnh nhãn trục: `experiment-68a6c30d4271`. Kết quả số không đổi so với lần chạy trước.
- Dữ liệu thật `vendor-26f2e2ce615c` → `canonical-19eac94c626f`: bị chặn do mã băm dữ liệu gốc không khớp, trước khi xử lý các trường phụ thuộc vào ý nghĩa dữ liệu.
- Bản phục hồi `vendor-recovered-fccfaaa2b061`: cả 5 file dữ liệu gốc đều khớp mã băm ban đầu. Các file cũ được giữ nguyên. Lần chuyển đổi bản phục hồi `canonical-98a1440ae1eb` vẫn bị chặn vì thiếu dữ liệu tham chiếu.
- Bộ lập kế hoạch tải dữ liệu từ thử nghiệm giả lập vẫn bị chặn. Chưa gọi API để mở rộng dữ liệu.

## Điều kiện để tiếp tục với dữ liệu thật

Cần bổ sung bằng chứng về đơn vị, phương pháp điều chỉnh giá, quy ước ngày và múi giờ; danh mục chứng khoán có lịch sử niêm yết, hủy niêm yết, chuyển sàn; lịch giao dịch độc lập và đầy đủ; thời điểm thông tin thực sự được công bố cùng trạng thái giao dịch.

Cần có dữ liệu sự kiện doanh nghiệp và lãi suất, hoặc thu hẹp rõ phạm vi phương pháp lợi suất/lãi suất bằng giả định đã ghi nhận. Phải chốt tập phát triển, tập kiểm định độc lập và cách hạch toán trước khi đưa ra kết luận hiệu quả trên thị trường thật.

Bộ chuyển đổi, kiểm tra dữ liệu và chương trình nghiên cứu đã sẵn sàng tiếp nhận các đầu vào đó. Những dữ kiện còn thiếu không được tự tạo để làm cho hệ thống báo đạt.
