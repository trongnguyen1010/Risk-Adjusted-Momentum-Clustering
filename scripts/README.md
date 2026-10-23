# Lệnh làm việc hiện tại

Đọc [documentation index](../docs/README.md) trước. Tên có số phiên bản trong
script/config cũ là lineage cần giữ, không phải lời mời chạy lại campaign.

| Việc cần làm | Điểm vào |
|---|---|
| Xem tiến độ baseline financial | `financial_full10_baseline.ps1 -Mode Status` |
| Kiểm input / chạy lại đúng protocol baseline | `financial_full10_baseline.ps1 -Mode Check` / `-Mode Run` (thêm `-Python` nếu cần) |
| Kiểm độc lập baseline, không refit | `python scripts/financial_full10_review.py` |
| Lấy dataset tài chính hiện hành để bàn giao | [Financial reference2016–2025](../data/handoffs/financial-reference-2016-2025/README.md) |
| Xem trạng thái DStock đã hoàn tất | `financial_dstock_remaining.ps1 -Mode Status` |
| Replay DStock offline | `financial_dstock_remaining.ps1 -Mode Offline` từprojectroot |
| Theo dõi campaign qua dashboard | `financial_workflow_monitor.ps1` — dashboard acquisition cũ không thay counter DStock |
| Kiểm gói dọn dẹp23/10 | `project_cleanup.py check` |
| Khôi phục report/helper đã lưu ZIP | `project_cleanup.py restore` — không ghi đè nội dung khác hash |

Python của runtime hiện có:

Baseline đã hoàn tất; [report](../artifacts/reports/financial-full10-baseline-v1/report.md).
Run giữ checkpoint theo năm và pins của config/code/input; resume chỉ tái sử dụng
checkpoint khớp identity/checksum. Đổi input/protocol sinh run khác, không ghi đè.
Log của lượt này: `.tmp/financial-full10-baseline.log`; trạng thái bền vững nằm ở
`data/financial/financial_full10_baseline_v1/pipeline-status.json`.

```powershell
& 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' scripts/project_cleanup.py check
```

`project_cleanup.ps1 -Mode Prune` chỉ gỡ đúng các file trong plan đã verify,
kiểm archive hash, input anchors, đường dẫn tuyệt đối và hash từng file trước
khi xóa. Không dùng để xóa campaign khác. `plan`/`pack` là bước chuẩn bị một lần;
không tạo lại plan sau khi đã prune. Cache Python/test có thể tái tạo.

Các runner/config tài chính cũ còn ở project vì đang là import, dependency hoặc
implementation pin. Đổi tên/move chúng cần migration riêng; không dùng việc
đổi tên để sửa frozen hashes. Bước phân cụm chưa chạy trong lượt cleanup.
