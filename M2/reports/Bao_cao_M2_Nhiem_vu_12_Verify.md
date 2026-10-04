# Báo cáo M2 nhiệm vụ 12 Verify

## Kết luận và phạm vi kiểm chứng

Tôi đã thực hiện lượt M2 VERIFY trên máy Windows để đối chiếu cấu hình, checksum, Global K, ranh giới dữ liệu, khoảng trống thời gian và khả năng tái lập. Kết luận hiện tại là BLOCKED; methodology_clearance = false. Các kiểm tra tự động đã chạy xong, nhưng chưa đủ bằng chứng để xác nhận toàn bộ M2 không có methodology violation.

Người thực hiện: Trần Minh Tuấn · Team DELTA · Ngày báo cáo: 04/10/2026. Lượt kiểm tra kết thúc lúc 23:26:09 giờ Việt Nam. Commit được ghi nhận: 146d408d69d3e69df782b073e5a3e0318df532f4. Nhánh làm việc trên máy: m2-task12-verify-tuan; nhánh nguồn: m2-clustering-experiment.

### Kết quả theo năm phần của kế hoạch

| Phần | Kết quả | Bằng chứng chính |
| --- | --- | --- |
| 12.1 | BLOCKED / PARTIAL | Checksum hiện có khớp; thiếu ZIP Ward và bộ checksum đầy đủ của Task 4. |
| 12.2 | PASS | Tái tính tổng hợp 105 run development; Global K = 2; phương pháp đã khóa là KMeans_Baseline. |
| 12.3 | PASS một phần | Ranh giới dữ liệu đạt; lịch sử đăng ký PCA và quy tắc chọn phương pháp cần review. |
| 12.4 | PASS | 48 cặp temporal đã kiểm tra; không nối development sang holdout. |
| 12.5 | PASS | 34 tests đạt; hai lần fit cùng snapshot development cho kết quả giống nhau. |

Trong 17 dòng kiểm tra: 13 PASS, 1 BLOCKED, 1 PARTIAL và 2 MANUAL_REVIEW_REQUIRED. BLOCKED phản ánh thiếu evidence; chưa phải bằng chứng kết luận có leakage. Hai mục review thủ công vẫn phải được xử lý trước khi cấp methodology clearance.

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

PCA: ADR-050 và OPEN-07 còn ghi nhận thiếu preregistration evidence của PCA v1. Việc cấu hình 4 components hiện được validate không chứng minh cấu hình đã đăng ký trước thí nghiệm. Trạng thái: MANUAL_REVIEW_REQUIRED.

Chọn phương pháp: Task 10 dùng ngưỡng Occam 0.03. Cần bằng chứng có ngày và nội dung cụ thể, cho thấy rule được phê duyệt trước quyết định chọn phương pháp; báo cáo/code hiện có không tự chứng minh điều này. Phần bổ sung trong kế hoạch là đề xuất cần mentor/owner phê duyệt. Trạng thái: MANUAL_REVIEW_REQUIRED.

### Phần 12.4 Temporal gaps

Đã kiểm tra 48 cặp temporal đã lưu; không có liên kết development-to-holdout. Các tests có trường hợp snapshot dưới ngưỡng 120 dòng bị skip và reset chain. Không suy rộng thành kết luận về concrete dynamic clustering.

### Phần 12.5 Tests và bounded rerun

tests.log ghi nhận 34 tests, thời gian 19.673 giây, kết quả OK và exit code 0. Bộ tests gồm protocol, PCA artifacts, holdout guards, algorithm determinism, runner và saved holdout evidence; fixtures tổng hợp được phân biệt với dữ liệu holdout thực.

bounded_rerun.json ghi nhận snapshot 2023-11-30, 142 dòng, K = 2, same_result = true. Hai lần fit độc lập trong bộ nhớ cho cùng kết quả; mô hình hội tụ sau 3 iterations với inertia 1304.124507011444. Không ghi đè model đã lưu. Đây là chứng cứ tái lập trên một snapshot development, không phải chạy lại toàn bộ lịch sử M2.

Holdout chỉ được kiểm tra lại bằng evidence đã có. Không refit holdout, không quét K hoặc thay phương pháp sau khi xem holdout.

## Các mục cần bổ sung và bàn giao

### Bốn mục chưa thể đóng

1. Ward — người phụ trách Task 5 bổ sung source_snapshot.zip gốc vào M2/artifacts/m2-task5-ward-v1. Expected SHA256: 41e55e7a518bad86c92db3a9f0885660f2197f42ba7cb6184eb04bbc202a0c77. Kiểm tra nhánh nguồn đã fetch ngày 04/10/2026 không thấy file ở đường dẫn này. ZIP trong m2-final-holdout-v1 có checksum khác, không thể dùng thay thế.

2. Baseline — người phụ trách Task 4 cung cấp checksum manifest hoặc evidence gốc đầy đủ của lần chạy. Có thể lập hash inventory hiện tại để bảo toàn từ thời điểm audit, nhưng phải ghi rõ thời điểm mới; inventory này không chứng minh toàn vẹn lịch sử.

3. PCA — owner/mentor review bằng chứng đăng ký component rule trước PCA comparator execution. Nếu không có evidence, giữ finding mở và ghi limitation; phê duyệt hiện tại không tạo lại preregistration trong quá khứ.

4. Final method — owner/mentor review bằng chứng phê duyệt rule Occam 0.03 trước selection. Không sửa hoặc backdate decision sau holdout. Nếu cần thay methodology, xử lý bằng protocol/version mới theo quy trình nhóm.

### Bộ bằng chứng được bàn giao

Thư mục m2-task12-verify-20261004-232543 gồm verify_summary.json, checks.csv, hash_checks.csv, tests.log, bounded_rerun.json và evidence_manifest.json. Đã đối chiếu cả 5 SHA256 trong evidence_manifest.json với bytes gốc từ ZIP người thực hiện gửi; tất cả khớp. Giữ nguyên file, không mở rồi lưu lại CSV/JSON bằng công cụ làm thay đổi bytes.

Kèm theo báo cáo Word, bản Markdown để review trên GitHub và scripts/verify_m2_task12.py. Lượt VERIFY tiếp theo phải dùng output directory mới. Chỉ chạy lại khi đã bổ sung evidence hoặc có thay đổi cần kiểm chứng; hai mục review lịch sử cần kết luận và dẫn chiếu evidence của owner, script hiện tại không tự cấp approval.

### Kết luận bàn giao

Tôi đã thực hiện và lưu evidence cho cả năm phần nhiệm vụ 12. Kết luận hiện tại là BLOCKED, methodology_clearance = false. Chưa đạt điều kiện đóng nhiệm vụ với khẳng định toàn bộ M2 không có methodology violation. Đề nghị nhóm bổ sung bốn mục trên và mentor/owner review trước khi chấp thuận bàn giao methodology.

Nguồn đối chiếu: Ke_hoach_M2_phan_cum_co_phieu.docx; bộ evidence ngày 04/10/2026; repository trong nhánh m2-clustering-experiment tại commit 146d408d69d3e69df782b073e5a3e0318df532f4.
