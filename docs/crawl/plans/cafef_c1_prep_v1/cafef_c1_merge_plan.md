# CafeF C1 Raw Merge Plan

## Phạm vi

Đây chỉ là merge plan. C1-PREP không chạy worker và không merge dữ liệu. Merge C1 sau này chỉ tạo unified RAW acquisition artifact; không ghi canonical, research price, adjustment factor hoặc feature.

## Điều kiện bắt đầu

Chỉ bắt đầu khi cả năm worker ở trạng thái `COMPLETED` hoặc `COMPLETED_WITH_RECORDED_FAILURES`, đồng thời plan ID, assignment hash, contract version, code commit và `collection_end_date` khớp tuyệt đối.

## Trình tự deterministic

1. Verify đủ năm worker manifest và terminal state.
2. Verify assignment completeness, raw file checksums và request-log checksums.
3. Đối chiếu request thực tế với security/range/page đã giao; request ngoài plan bị quarantine.
4. Phát hiện duplicate request và duplicate security/date observation. Không average hoặc silently select.
5. Kiểm tra date-window coverage, maximum 15 years, identity interval và một cutoff chung.
6. Aggregate failure taxonomy mà không đổi classification của worker.
7. Ghi unified raw index theo `worker_id`, `security_id`, range start, range end, page index và raw hash.
8. Xuất merge manifest mới tham chiếu immutable worker manifests.

## Cấm tại merge C1

- Không promote canonical.
- Không xây DELTA research price hoặc adjustment factor.
- Không dùng `GiaDieuChinh` làm research price.
- Không suy listing/provider boundary từ empty response.
- Không loại raw conflict chỉ để tạo một row duy nhất.

## C1 success metrics sẽ đo sau execution

Planned-request completion, valid raw response rate, schema consistency, identity consistency, exchange coverage, observed earliest/latest date, observed history depth, duplicate-date rate, invalid-OHLC rate, request/access-control failure rate, pagination completeness, provenance completeness và confidence về raw semantics. C1-PREP không đánh giá các metric này.
