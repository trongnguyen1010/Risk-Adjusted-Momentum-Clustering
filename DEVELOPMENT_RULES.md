# Quy tắc phát triển

## Tổ chức và ownership

1. Tất cả code, config, docs và artifact phát triển của project nằm dưới `SourceCode`. Không sửa PDF nguồn để che sự khác biệt giữa plan và triển khai.
2. Logic tính toán ở `src/delta_t1`; notebook chỉ gọi module và giải thích. CLI điều phối, provider chỉ tải dữ liệu, feature không tự gọi mạng.
3. Task có owner/reviewer và đầu ra kiểm chứng được. Không đánh dấu done chỉ vì có folder hoặc interface.
4. Các module M2/M3 hiện là contract mở rộng. Không trả nhãn/metrics/NAV placeholder để UI hiểu nhầm đó là kết quả nghiên cứu.

## Dữ liệu và nghiên cứu

5. Raw bất biến. Tạo version mới khi source revision hoặc thay mapping/policy; không ghi đè snapshot cũ.
6. Schema là contract thực thi. Đổi type/key/unit/semantics phải cập nhật schema version, docs, migration và tests trong cùng PR.
7. Dùng security_id có lịch sử; không join dài hạn chỉ bằng ticker. Không gán metadata hiện tại cho quá khứ khi thiếu bằng chứng.
8. Phân biệt fetched_at, available_at và as_of_date. Không coi dữ liệu đến muộn là đã biết tại thời điểm cũ.
9. Không forward-fill để tạo giao dịch/returns giả, không đổi NA thành 0, không tùy tiện xóa duplicate/outlier.
10. Raw price, adjusted price và total return phải tách rõ. Không cộng cổ tức hai lần; thiếu raw thì chặn mô phỏng quantities/cash cần raw.
11. Development/holdout, rf, phí và khớp phải được đặc tả trước khi chạy đánh giá tương ứng. Không chọn model bằng lợi nhuận holdout.
12. Synthetic luôn có nhãn, prefix mã riêng và `synthetic=true`. Không dùng synthetic để báo đủ 300 mã/5 năm hay lợi nhuận.

## Code và kiểm thử

13. Validate ở biên module; exceptions phải giúp tìm job/table/field. Giữ lỗi và quarantine, không bỏ lỗi rồi báo success.
14. Cấu hình cửa sổ/chính sách thay vì rải hardcode. Những công thức/cửa sổ chuẩn của feature schema 1.0 đang nằm trong compute; thay chúng cần đổi feature version, không chỉ đổi tên cột.
15. Test phần sai sẽ đổi kết luận: công thức, gap, temporal join, future append, phí/cash/NAV, permutation labels. Không thêm tests chỉ để đếm số lượng.
16. HTTP phải timeout, retry hữu hạn và rate limit; không retry 401/403, không lách hạn mức bằng proxy/account rotation.
17. Một writer cho một run. Resume chỉ khi hash config/code/raw khớp; không chạy hai process resume cùng run.
18. Core không thêm dependency nếu thư viện chuẩn đã đủ. Optional dependencies có version và lock môi trường; kiểm tra lại lock khi nâng version.
19. Không đưa API key vào config/URL/notebook/log/Git. Chỉ tên biến môi trường trong config; `.env.example` không có giá trị thật.

## Git, review và release

20. Gợi ý branch `feat/<task-id>-<description>`, `fix/<task-id>-<description>`, commit mô tả thay đổi. Workspace ban đầu chưa có Git; bộ nền không tự tạo remote/commit.
21. PR gồm vấn đề, hành vi mới, input/output ảnh hưởng, test đã chạy và giới hạn. Một thay đổi review được; không trộn formatting toàn repo với sửa công thức.
22. Reviewer đối chiếu ít nhất một giá trị đầu ra với input. Khi release phải có người khác chạy README trên môi trường khác.
23. Cập nhật CHANGELOG và DECISIONS cùng code nếu thay hành vi hoặc giả định. Tag M1/M2/M3 chỉ khi checklist tương ứng đạt.
24. Chỉ công bố dữ liệu/code theo quyền thực có; nội dung raw/vendor không được commit mặc định. Không tự gửi báo cáo cho mentor từ code.
