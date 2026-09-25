# Reproducibility

## Quy tắc artifact

Raw acquisition, canonical run, feature run, experiment output và verification evidence là immutable. Thay source revision, mapping, reconciliation rule, feature definition hoặc protocol phải tạo version/run mới. Resume chỉ hợp lệ khi config, code, input và job-plan hash khớp; một writer sở hữu một run.

Heavy C8 artifact nằm local tại `artifacts/cafef_primary/cafef-c8-complete-only-v1/`. Compact verification evidence được track tại `artifacts/cafef_primary/cafef-c8-verify-v1/`. Không copy heavy data vào archive khác và không sửa artifact để làm gate pass.

## Kiểm chứng C8 không rerun

`scripts/verify_cafef_c8_results.py` là generator của compact verification artifact, không phải idempotent current-tree command: không chạy lại khi `cafef-c8-verify-v1` đã tồn tại. Full test suite và M1-REPORT verifier đọc artifact bất biến, kiểm tra output/upstream hashes mà không gọi network, supplemental acquisition hay feature rebuild.

Kết quả đã khóa: 952 candidates; 922 feature-complete; 905 market-ready; 30 latest-253 incomplete; 47 market-readiness failures; 148 deferred expansion; 0 historical-identity-ready; 0 research-ready.

## Kiểm chứng R1

Artifact `artifacts/repository/r1-consolidation-v1/` chứa before/after inventory, deletion inventory có category/reason, verification summary và SHA256 manifest. Parent inventory cố định ở C8-VERIFY commit `e149198986345bb02610e53d8a330f641b89df22`. `scripts/verify_repository_r1.py --verify-existing` so exact Git inventory của frozen R1 tree; vì vậy chỉ dùng tại revision đó, không coi mismatch sau các commit M1/D1 là R1 evidence regression.

## Kiểm chứng M1-REPORT

```powershell
.venv\Scripts\python.exe scripts\build_m1_market_foundation_report.py --verify-existing
```

Artifact `artifacts/reports/m1-market-foundation-v1/` tái tính và assert headline C8, coverage, exclusions và monthly readiness từ immutable evidence. Notebook `notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb` chỉ đọc explicit report directory. Verification không crawl, không rebuild C8 và không chạy clustering/backtest. Các discontinuities theo tháng là evidence cần M2-PREP giải thích, không phải lý do để sửa artifact trong D1.

## Gate kỹ thuật

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
.venv\Scripts\python.exe run.py run --config configs/data/synthetic_smoke.example.json
node --check web/app.js
git diff --check
```

Synthetic smoke là regression kỹ thuật, không phải research evidence. Khi chỉ thay documentation/repository structure, không tái tạo artifact khoa học.

## Provenance lịch sử

KBS/Vnstock pilot và các C1–C7 planning files đã bị retire khỏi active tree khi superseded. Source caveat cần cho immutable evidence vẫn ở `docs/data/kbs_pilot_semantics.md`; các chi tiết khác truy xuất qua Git history. Không diễn giải historical artifact thành current readiness.
