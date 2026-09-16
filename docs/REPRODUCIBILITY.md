# Reproducibility

## Artifact policy

Raw, canonical run, feature run, experiment model/output và product bundle là immutable. Thay source revision, mapping, reconciliation rule, feature definition hoặc protocol phải tạo version/run mới. Complete evidence không bị xóa vì kết quả bất lợi.

Manifest ghi config hash, code hash/source snapshot, input artifact hashes, environment, random seed, data/feature/model version và lineage IDs. Resume chỉ được phép khi các hash phù hợp; một writer sở hữu một run.

`data/` và `artifacts/` là runtime storage local, được Git ignore và hiện không chứa active evidence. M1 Data V2 sẽ tạo artifact mới từ source discovery/`SOURCE_SMOKE`; runtime cũ không được tự tái tạo.

Mọi artifact mới dùng ID `<prefix>-YYYYMMDDTHHMMSSZ-xxxxxxxx` với UTC timestamp và token 8 lowercase hex; ví dụ `run-20260916T041530Z-a1b2c3d4`. Source, method, config và các chi tiết dài tiếp tục nằm trong manifest. Old immutable IDs vẫn hợp lệ và không bị đổi tên.

## Kiểm tra chuẩn

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
.venv\Scripts\python.exe run.py run --config configs/data/synthetic_smoke.example.json
node --check web/app.js
```

Ngoài ra parse toàn bộ JSON config/schema, kiểm tra broken Markdown links/imports và `git diff --check`. Trên Windows managed sandbox, test dùng atomic temp file có thể cần chạy ngoài sandbox; đây là giới hạn môi trường, không phải lý do bỏ test.

## Historical engineering evidence

- KBS/Vnstock pilot đã hoàn tất trong tháng 09/2026; các ID cũ như `canonical-1d2a54288bfc`, `run-4a1a6203dba7`, `experiment-de5f4d68afa0` và `real-pilot-5569fb856c7a` chỉ là historical references.
- Các bài học quan trọng về source semantics được giữ tại [KBS pilot semantics](data/kbs_pilot_semantics.md).
- Legacy runtime artifacts đã được retire khỏi active workspace trong M1 Data V2 reset.
- Synthetic architecture validation từng pass; các artifact lịch sử đó không còn thuộc active workspace và không chứng minh M1/M2/M3 hoàn tất.

## Current M1 evidence

Chưa có active real `SOURCE_SMOKE` dataset. M1 chưa hoàn tất.

## Next

1. CafeF source discovery.
2. VietFin source discovery.
3. Chạy `SOURCE_SMOKE` 3–5 securities sau khi source semantics được verify.
