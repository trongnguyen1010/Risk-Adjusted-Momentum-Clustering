# CafeF data collection

Đây là entry point duy nhất cho acquisition/recovery còn active. Source semantics chi tiết nằm tại [CafeF](sources/CAFEF.md); trạng thái dataset nằm tại [Current status](../CURRENT_STATUS.md).

## Active contracts

- `configs/data/cafef_expansion_v1/`: frozen C6 expansion universe, five worker shards và acquisition contract.
- `configs/data/cafef_supplemental_v1/`: 148 deferred expansion candidates; chỉ chạy trong stage supplemental được phê duyệt.
- `configs/data/cafef_c8_complete_only_v1.json`: C8 complete-only offline build contract; không dùng để rerun khi chỉ verify.
- `configs/data/identity_review_v1.json`: reviewed identity aliases/evidence dùng bởi C8.

## Active commands

```powershell
.venv\Scripts\python.exe scripts\run_cafef_expansion_worker.py --help
.venv\Scripts\python.exe scripts\package_cafef_expansion_handoff.py --help
.venv\Scripts\python.exe scripts\verify_cafef_expansion_handoffs.py --help
.venv\Scripts\python.exe scripts\consolidate_cafef_expansion_handoffs.py --help
.venv\Scripts\python.exe scripts\run_cafef_supplemental_worker.py --help
```

Acquisition phải dùng explicit execute/resume contract, immutable raw pages, exact hashes và fail-closed access handling. Không bypass login, anti-bot, paywall hoặc access control. Không coi provider boundary là listing date; không fabricate missing history.

## Current boundary

C8 đã dùng 500 baseline + 452 complete expansion. 148 expansion rows còn deferred. R1 không crawl network, không chạy supplemental và không thay data result. Planning/runbook superseded đã rời active tree và chỉ còn trong Git history.
