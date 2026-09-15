# Đóng góp cho DELTA

## Nguyên tắc làm việc

Thay đổi theo lát cắt nhỏ và giữ Research Core tách khỏi Product Layer. Logic nằm trong `src/delta_t1`; script/CLI chỉ điều phối. Schema JSON là executable contract. Không sửa immutable evidence để làm kết quả đẹp hơn.

## Quy trình

1. Đọc [documentation index](docs/README.md), [Project Map](docs/PROJECT_MAP.md) và tài liệu domain liên quan.
2. Ghi rõ milestone, input/output và invariant bị ảnh hưởng.
3. Chạy test baseline.
4. Thực hiện focused change; nếu đổi contract thì thêm migration note, tests và version.
5. Chạy test, compile, config/schema parse và link/import check.
6. Cập nhật [Decisions](docs/DECISIONS.md) và `CHANGELOG.md` nếu đổi behavior/assumption.

## Lệnh kiểm tra

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
.venv\Scripts\python.exe run.py run --config configs/data/synthetic_smoke.example.json
node --check web/app.js
git diff --check
```

## Data và research review

- Đối chiếu ít nhất một output với input/formula khi sửa feature, reconciliation hoặc backtest.
- Test các failure mode có thể đổi kết luận: gap, late availability, basis change, historical identity, label permutation, transaction cost và future append.
- Không dùng synthetic để tuyên bố coverage/performance; không chọn model bằng holdout return.
- Provider request phải có finite timeout/retry/rate limit; không retry 401/403 hoặc né rate limit.

## Security và dependency

Không commit API key, token hoặc licensed raw content. Config chỉ chứa tên environment variable. Chỉ thêm dependency có version/lock khi standard library không đủ và milestone thực sự cần.

## Review và release

PR/commit cần mô tả vấn đề, behavior mới, contract/data ảnh hưởng, test đã chạy và giới hạn còn lại. Tag M1/M2/M3 chỉ khi acceptance gate tương ứng có reproducible evidence.
