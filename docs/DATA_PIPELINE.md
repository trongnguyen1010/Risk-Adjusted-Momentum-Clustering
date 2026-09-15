# Data pipeline và source policy

## Trạng thái source

| Source | Vai trò dự kiến | Trạng thái |
|---|---|---|
| CafeF | market/company/financial candidate | `DISCOVERED`; endpoint, terms, basis và PIT coverage chưa xác minh |
| VietFin | secondary connector | `DISCOVERED`; underlying provider/rights chưa xác minh |
| Vnstock | connector cho legacy KBS pilot | adapter đã migrate; không phải source of truth cho final universe/financial data |

License của connector không tự cấp quyền với third-party data. Mỗi row/run phải ghi underlying provider, endpoint/request, connector/version, fetched time và raw hash. Không crawl lớn trước bounded smoke review về rights, rate limit và semantics.

Source lifecycle: `DISCOVERED → ACCESS_TESTED → SEMANTICS_VERIFIED → PILOT_APPROVED → PRODUCTION_APPROVED`.

## Các stage

1. **Acquire:** finite timeout/retry/rate, immutable raw response và request metadata.
2. **Normalize:** parse field/type/unit/identity/price basis/time nhưng chưa chọn conflict winner.
3. **Reconcile:** so candidate theo canonical key; giữ decision và unresolved conflict.
4. **Canonicalize:** tạo versioned market và financial PIT tables.
5. **QC/coverage:** quarantine integrity/timing/identity error, đếm eligible/reference/excluded.
6. **Research:** tạo PIT feature, model, evaluation và backtest artifacts.
7. **Product projection:** export immutable company bundle; UI không đọc raw table.

## Reconciliation contract

Candidate giữ canonical key, normalized value/unit/basis, source/provider/version, request/raw hash, fetched/available time và transform version. Identity ambiguity hoặc incompatible price basis luôn conflict, không average. Financial restatement giữ mọi vintage.

Decision record nêu chosen candidate, rule/version, reason và candidate count. Cùng raw hashes/rules phải tái tạo cùng canonical hashes. Source priority chỉ được dùng sau approval và không được che basis conflict.

## Point-in-time rules

- Historical join dùng effective-dated `security_id`, không dùng current ticker membership.
- Không backdate `fetched_at` thành publication time.
- Calendar là reference data độc lập; last API row không tự động là month-end.
- Raw, adjusted và total-return series tách biệt; basis change reset history.
- Missing execution price/status phải block hoặc ghi explicit reason.
- Financial join chọn latest report vintage đã available tại `decision_at`, không chọn latest known today.

## Smoke trước scale

1. Smoke 3–5 symbols đại diện HOSE/HNX/UPCOM, short-history và inactive/identity edge case.
2. So sánh daily range >=5 năm và ít nhất hai known corporate actions giữa source khả dụng.
3. Kiểm tra tối thiểu ba quarterly reports và một restatement nếu có.
4. Lưu request/raw hash/version; báo mismatch, missing date, unit, failure/rate behavior và rights.
5. Reviewer duyệt semantics/reconciliation trước representative pilot 50–60 mã; pilot pass trước scale >=300. Long-term target có thể >1.200 mã và 5–15 năm.

## Commands

```powershell
.venv\Scripts\python.exe scripts/crawl_vnstock.py --symbols FPT VNM PVS --start 2021-01-01 --end 2025-12-31
.venv\Scripts\python.exe scripts/plan_crawl.py --help
.venv\Scripts\python.exe scripts/promote_vnstock.py --help
.venv\Scripts\python.exe run.py run --config configs/data/smoke.example.json
```

Secrets chỉ nằm trong environment variable. Một writer sở hữu một run; resume chỉ khi config/code/raw hashes khớp. JSONL dùng cho smoke/pilot; chỉ cân nhắc partitioned Parquet/DuckDB và serving storage sau khi M1 gates có evidence.
