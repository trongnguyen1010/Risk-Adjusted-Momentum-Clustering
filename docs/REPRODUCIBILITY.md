# Reproducibility

## Artifact policy

Raw, canonical run, feature run, experiment model/output và product bundle là immutable. Thay source revision, mapping, reconciliation rule, feature definition hoặc protocol phải tạo version/run mới. Complete evidence không bị xóa vì kết quả bất lợi.

Manifest ghi config hash, code hash/source snapshot, input artifact hashes, environment, random seed, data/feature/model version và lineage IDs. Resume chỉ được phép khi các hash phù hợp; một writer sở hữu một run.

## Kiểm tra chuẩn

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
.venv\Scripts\python.exe run.py run --config configs/data/smoke.example.json
node --check web/app.js
```

Ngoài ra parse toàn bộ JSON config/schema, kiểm tra broken Markdown links/imports và `git diff --check`. Trên Windows managed sandbox, test dùng atomic temp file có thể cần chạy ngoài sandbox; đây là giới hạn môi trường, không phải lý do bỏ test.

## Evidence hiện tại

Baseline audit ngày 15/09/2026: 54/54 tests pass và `compileall` pass trước migration. Acceptance ngày 16/09/2026: 70/70 tests pass, compile/JSON/Markdown links/web syntax/diff checks pass; synthetic smoke pipeline `run-5016b877990c` và PCA+K-Means technical experiment `experiment-85dd31d7598b` complete. Đây chỉ là technical evidence, không phải research result. Retained KBS/Vnstock pilot chỉ là legacy engineering evidence, không đạt thesis universe/history gate. Path [data/kbs_pilot_semantics.md](data/kbs_pilot_semantics.md) phải giữ nguyên vì immutable manifests có thể tham chiếu.

Generated synthetic run có thể tái tạo và không chứng minh M1/M2/M3. Không mutate/xóa thư mục `data/` hoặc `artifacts/` trong architecture refactor nếu chưa xác minh reference graph và quyền xóa.
