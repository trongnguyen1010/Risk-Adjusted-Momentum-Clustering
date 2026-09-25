# Báo cáo cleanup repository C6

## Kết quả

C6 thực hiện cleanup theo hướng bảo toàn lineage. Không tracked file nào đáp ứng đồng thời toàn bộ điều kiện `SAFE_DELETE`, vì vậy không xóa và không di chuyển file. Git history không được dùng làm lý do duy nhất để loại evidence đang được test hoặc tài liệu đang tham chiếu.

| Phân loại | Số file | Quyết định |
|---|---:|---|
| `SAFE_DELETE` | 0 | Không có candidate đủ bằng chứng để xóa |
| `HISTORICAL_ARCHIVE` | 0 | Không mass-move vì sẽ làm hỏng stable references/manifest hashes |
| `UNCERTAIN_KEEP` | 6 | Giữ các entry point cũ đã review |

## Candidate đã review và giữ lại

- `scripts/plan_cafef_c1_workers.py`: được unit test, C1 plan và immutable manifest tham chiếu; cần cho reproducibility C1.
- `scripts/plan_cafef_c1_solo.py`: được CafeF primary experiment plan tham chiếu; giữ lineage single-run C1.
- `scripts/prepare_m1_scale_assignments.py`, `scripts/run_m1_scale_shard.py`, `scripts/verify_m1_scale_handoff.py`: vẫn là contract tái lập M1 scale/C4 500 mã và được runbook cũ tham chiếu.
- `scripts/run_cafef_c5_targeted_recovery.py`: là exact C5 acquisition entry point; giữ để giải thích evidence 64 requests và 10 mã deferred.

Các thư mục plan C1 và `docs/crawl/m1_scale/` cũng được kiểm tra nhưng không đưa vào số file `UNCERTAIN_KEEP`: manifest/hash và tài liệu active còn trỏ tới chúng, nên đây là `ACTIVE_KEEP` cho lineage, không phải clutter có thể xóa an toàn.

## Dependency checks

C6 đã kiểm tra exact path references bằng `rg`, imports, unit tests, active configs, C1/C4/C5 manifests và documentation links. Việc di chuyển các file trên sang `docs/archive/` sẽ phá stable path hoặc làm mất khả năng replay; lợi ích cleanup không đủ lớn. Không file nào dưới ignored raw data bị sửa/xóa.

Active path mới được làm rõ tại [PROJECT_MAP.md](PROJECT_MAP.md); historical tooling được gắn nhãn rõ thay vì xóa.
