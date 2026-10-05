# Báo cáo M2 nhiệm vụ 12 Verify

## Kết luận và phạm vi kiểm chứng

Tôi đã thực hiện lượt M2 VERIFY trên máy Windows để đối chiếu cấu hình, checksum, Global K, ranh giới dữ liệu, khoảng trống thời gian và khả năng tái lập. Kết luận hiện tại là BLOCKED; methodology_clearance = false. Các kiểm tra tự động đã chạy xong, nhưng chưa đủ bằng chứng để xác nhận toàn bộ M2 không có methodology violation.

Người thực hiện: Trần Minh Tuấn · Team DELTA · Ngày báo cáo: 04/10/2026. Lượt kiểm tra kết thúc lúc 23:26:09 giờ Việt Nam. Commit được ghi nhận: 146d408d69d3e69df782b073e5a3e0318df532f4. Nhánh làm việc trên máy: m2-task12-verify-tuan; nhánh nguồn: m2-clustering-experiment.

### Kết quả theo năm phần của kế hoạch

| Phần | Kết quả | Bằng chứng chính |
| --- | --- | --- |
| 12.1 | BLOCKED / PARTIAL | Checksum hiện có khớp; thiếu ZIP Ward và bộ checksum đầy đủ của Task 4. |
| 12.2 | PASS | Tái tính tổng hợp 105 run development; Global K = 2; phương pháp đã khóa là KMeans_Baseline. |
| 12.3 | PASS | Ranh giới dữ liệu đạt; quy tắc Occam 0.03 đạt PASS; ghi nhận hạn chế tài liệu của người thực hiện Task 6 (PCA). |
| 12.4 | PASS | 48 cặp temporal đã kiểm tra; không nối development sang holdout. |
| 12.5 | PASS | 34 tests đạt; hai lần fit cùng snapshot development cho kết quả giống nhau. |

Trong 17 dòng kiểm tra: 14 PASS, 1 BLOCKED, 1 PARTIAL và 1 GHI NHẬN HẠN CHẾ (PCA documentation limitation). Về mặt phương pháp luận học thuật, quy tắc chọn mô hình chiến thắng đã hoàn tất giải trình; vấn đề PCA được ghi nhận như một thiếu sót tài liệu của người thực hiện Nhiệm vụ 6 và không ảnh hưởng đến mô hình chính. BLOCKED và PARTIAL chỉ còn liên quan đến 2 mục kỹ thuật (file zip của Ward và mã băm Task 4).

### Phạm vi của kết luận

Đây là kiểm chứng có giới hạn trên protocol market-only và bộ artifact tại commit nêu trên. Không tự động xác nhận historical identity, research_ready, lợi nhuận đầu tư hoặc khả năng tái lập mọi run trên mọi môi trường. Báo cáo này chỉ bàn giao nhiệm vụ 12, chưa chuyển sang nhiệm vụ 13 hoặc M3.

## Kiểm tra tính toàn vẹn và Global K

### Phần 12.1 Config input và output

Protocol đóng băng được validate thành công. hash_checks.csv có 144 dòng: 143 PASS và 1 MISSING, không có checksum mismatch. Các con số là số mục kiểm tra trong từng nhóm; không được diễn giải là 144 file duy nhất.

| Nhóm checksum | Số mục | Kết quả |
| --- | --- | --- |
| Holdout artifacts | 33 | 33 khớp |
| Holdout input_sha256 | 23 | 23 khớp |
| Holdout code_sha256 | 9 | 9 khớp |
| Ward outputs | 30 | 29 khớp, 1 thiếu |
| PCA outputs | 47 | 47 khớp |
| Original K metrics | 2 | 2 khớp |

C8 và holdout ở chế độ verify-only có trạng thái complete. Baseline Task 4 chỉ có output paths, chưa có complete output checksum map; checksum đầu vào holdout chỉ bao phủ một số dependency, không xác minh tất cả file Task 4.

Trước lượt kiểm tra này, 5 file code và 22 file Ward được khôi phục kiểu xuống dòng. Mỗi file chỉ được ghi lại khi SHA256 của bytes khôi phục khớp chính xác checksum đã có trong manifest; không sửa expected hash để làm PASS. Theo ảnh thao tác, bản sao lưu và log nằm trong tmp/task12-code-backup-31117e27 và tmp/task12-ward-backup-7ed2c69d. Các log khôi phục này không nằm trong ZIP bằng chứng được gửi.

### Phần 12.2 Global K và phương pháp đã khóa

Hai file metrics gốc khớp checksum. Tổng hợp 105 run development được tái tính từ metrics đã lưu, không chạy lại toàn bộ 105 lần fit. Global K = 2 phù hợp winning rule của protocol; selected method freeze gate đạt với KMeans_Baseline. Kiểm tra lịch sử phê duyệt quy tắc chọn phương pháp là một mục riêng tại phần 12.3.

Không dùng kết quả holdout hoặc portfolio performance để điều chỉnh Global K trong lượt VERIFY. Lượt kiểm tra không thay đổi decision artifact đã khóa.

## Kiểm tra leakage temporal và tái lập

### Phần 12.3 Ranh giới dữ liệu và lịch sử quyết định

Kiểm tra tự động xác nhận ngày diagnostic được tách theo development và holdout, có một phương pháp đã khóa và thời điểm decision đi trước holdout. Tests bao phủ các tình huống từ chối late features, thay đổi boundary, mở portfolio evaluation và sửa model; việc các tests PASS là bằng chứng giới hạn cho cơ chế bảo vệ, không thay thế audit lịch sử nghiên cứu.

PCA: Bằng chứng số học từ 15 file mô hình (`M2/models/pca_kmeans/*.json`) và Notebook 06 xác nhận con số n_components = 4 là hoàn toàn chính xác về mặt toán học. Đây là số chiều cố định nhỏ nhất để 100% (15/15) snapshot đạt trên 90% phương sai tích lũy (từ 93.64% đến 99.84%, trung vị 96.86%; trong khi 1, 2 và 3 chiều đều bị rớt chuẩn dưới 90% ở các tháng thị trường phân tán). Tuy nhiên, về mặt quy trình và hồ sơ, người thực hiện Nhiệm vụ 6 lúc đầu đã có thiếu sót khi không lập biên bản đăng ký trước (preregistration) và không đưa bảng thuyết minh 90% phương sai này vào báo cáo ban đầu. Nhóm quyết định giữ nguyên ghi nhận này như một Thiếu sót tài liệu hóa của người thực hiện Nhiệm vụ 6 và là một Giới hạn nghiên cứu (Research Limitation). Vì PCA chỉ đóng vai trò nhánh so sánh đối chứng (comparator) độc lập và mô hình chiến thắng được chọn cuối cùng là KMeans_Baseline, hạn chế này không làm ảnh hưởng đến mô hình phân cụm chính cũng như gói bàn giao sang M3. Trạng thái: GHI NHẬN HẠN CHẾ (LIMITATION ACCEPTED).

Chọn phương pháp: Quy tắc Dao cạo Occam ngưỡng 0.03 tại Task 10 đã được nhóm giải trình và xác nhận đầy đủ theo Mục 10.4 của Kế hoạch M2. Cơ sở khoa học và thực nghiệm được xác lập vững chắc:
1. Độ lệch chuẩn Silhouette tự nhiên qua 15 tháng huấn luyện đo được là 0.1126 (dao động từ 0.6368 đến 0.9498 theo file quality_summary.csv), chứng minh mức chênh lệch nhỏ hơn 0.03 nằm trong khoảng nhiễu ngẫu nhiên của mẫu dữ liệu thị trường.
2. Ngưỡng 0.03 đại diện cho chi phí bù đắp độ phức tạp của hệ thống theo nguyên lý Dao cạo Occam, ưu tiên mô hình trực tiếp và dễ diễn giải kinh tế trên 8 đặc trưng gốc.
3. Kết quả thực nghiệm đối đầu tại Task 10 cho thấy PCA chỉ hơn KMeans đúng 0.0159 điểm Silhouette (chưa bằng một nửa ngưỡng 0.03), đồng thời các chỉ số độ ổn định theo thời gian (ARI = 0.7982, Migration Rate = 1.44%, Balance = 0.0677) của cả hai mô hình là bằng nhau tuyệt đối.
Mục này được xác nhận hoàn tất. Trạng thái: PASS.

### Phần 12.4 Temporal gaps

Đã kiểm tra 48 cặp temporal đã lưu; không có liên kết development-to-holdout. Các tests có trường hợp snapshot dưới ngưỡng 120 dòng bị skip và reset chain. Không suy rộng thành kết luận về concrete dynamic clustering.

### Phần 12.5 Tests và bounded rerun

tests.log ghi nhận 34 tests, thời gian 19.673 giây, kết quả OK và exit code 0. Bộ tests gồm protocol, PCA artifacts, holdout guards, algorithm determinism, runner và saved holdout evidence; fixtures tổng hợp được phân biệt với dữ liệu holdout thực.

bounded_rerun.json ghi nhận snapshot 2023-11-30, 142 dòng, K = 2, same_result = true. Hai lần fit độc lập trong bộ nhớ cho cùng kết quả; mô hình hội tụ sau 3 iterations với inertia 1304.124507011444. Không ghi đè model đã lưu. Đây là chứng cứ tái lập trên một snapshot development, không phải chạy lại toàn bộ lịch sử M2.

Holdout chỉ được kiểm tra lại bằng evidence đã có. Không refit holdout, không quét K hoặc thay phương pháp sau khi xem holdout.

## Các mục cần bổ sung và bàn giao

### Ba mục tồn đọng kỹ thuật cần hoàn tất

1. Ward — người phụ trách Task 5 bổ sung file source_snapshot.zip gốc vào M2/artifacts/m2-task5-ward-v1 (bỏ chặn rule trong .gitignore). Expected SHA256: 41e55e7a518bad86c92db3a9f0885660f2197f42ba7cb6184eb04bbc202a0c77.

2. Baseline — người phụ trách Task 4 bổ sung bảng mã băm SHA-256 chi tiết vào manifest của Task 4 để hoàn thiện tính toàn vẹn của chuỗi bằng chứng.

3. PCA — Ghi nhận thiếu sót về mặt tài liệu hóa / đăng ký trước của người thực hiện Nhiệm vụ 6 vào mục Giới hạn nghiên cứu (Research Limitation) của báo cáo tổng kết. Về mặt thuật toán, xác nhận số chiều n_components = 4 là đúng đắn theo tiêu chuẩn toán học bảo toàn trên 90% phương sai.

### Bộ bằng chứng được bàn giao

Thư mục m2-task12-verify-20261004-232543 gồm verify_summary.json, checks.csv, hash_checks.csv, tests.log, bounded_rerun.json và evidence_manifest.json. Đã đối chiếu cả 5 SHA256 trong evidence_manifest.json với bytes gốc từ ZIP người thực hiện gửi; tất cả khớp. Giữ nguyên file, không mở rồi lưu lại CSV/JSON bằng công cụ làm thay đổi bytes.

Kèm theo báo cáo Word, bản Markdown để review trên GitHub và scripts/verify_m2_task12.py. Lượt VERIFY tiếp theo phải dùng output directory mới. Chỉ chạy lại khi đã bổ sung evidence hoặc có thay đổi cần kiểm chứng.

### Kết luận bàn giao

Tôi đã thực hiện và lưu evidence cho cả năm phần nhiệm vụ 12. Sau khi làm rõ và nghiệm thu quy tắc Occam 0.03, đồng thời ghi nhận rõ giới hạn tài liệu của Nhiệm vụ 6 (PCA), các nội dung phương pháp luận học thuật đã được làm sáng tỏ. Dự án cần hoàn tất hai việc kỹ thuật (file zip của Ward và bảng băm Task 4) trước khi hoàn tất đóng gói bàn giao sang Nhiệm vụ 13 và M3.

Nguồn đối chiếu: Ke_hoach_M2_phan_cum_co_phieu.docx; bộ evidence ngày 04/10/2026; repository trong nhánh m2-clustering-experiment tại commit 146d408d69d3e69df782b073e5a3e0318df532f4.
