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
3. **Reconcile:** group cùng semantic comparison key và so từng field; giữ decision và unresolved conflict. Metadata fetch khác nhau không che hoặc tạo economic mismatch.
4. **Canonicalize:** tạo versioned market và financial PIT tables.
5. **QC/coverage:** quarantine integrity/timing/identity error, đếm eligible/reference/excluded.
6. **Research:** tạo PIT feature, model, evaluation và backtest artifacts.
7. **Product projection:** export immutable company bundle; UI không đọc raw table.

## Field-level reconciliation contract

Candidate giữ provider identity, canonical key, semantic comparison key, normalized field value/unit/basis, source/provider/version, request/raw hash, fetched/available time và transform version. Reconciliation chỉ group cùng entity/key rồi phân loại từng field:

- `MATCH`
- `MISSING_ON_SOURCE`
- `VALUE_CONFLICT`
- `UNIT_CONFLICT`
- `PRICE_BASIS_CONFLICT`
- `TIMING_CONFLICT`
- `IDENTITY_CONFLICT`

`source`, `fetched_at`, `data_version` và document hash là provenance, không được đưa vào economic row equality. Không average. Source priority chỉ resolve `VALUE_CONFLICT` khi semantics compatible và policy có `approved`, ordered sources, rule ID/version và reason. Unit/basis/timing/identity conflict vẫn unresolved.

Mỗi field decision giữ table, canonical key, comparison key, field, candidate sources, normalized values + unit/basis, chosen source/value nếu resolved, rule/version/reason và raw hashes. Financial report dùng provider ID làm provenance, canonical report ID làm FK, và comparison key theo security/fiscal period/scope/revision semantics; `financial_facts` thêm `statement_type` + `item_code`.

## Point-in-time rules

- Historical join dùng effective-dated `security_id`, không dùng current ticker membership.
- Không backdate `fetched_at` thành publication time.
- Calendar là reference data độc lập; last API row không tự động là month-end.
- Raw, adjusted và total-return series tách biệt; basis change reset history.
- Missing execution price/status phải block hoặc ghi explicit reason.
- Financial join chọn latest report vintage đã available tại `decision_at`, không chọn latest known today.

## Gate trước scale

1. **SOURCE_SMOKE:** 3–5 securities thật, HOSE/HNX/UPCOM và short-history/inactive/identity edge case khi có thể; request >=5 năm nếu source hỗ trợ. Kiểm tra required market fields, known corporate actions, ít nhất ba quarterly reports, unit/timezone/basis/pagination/rate/rights. PASS chỉ mở pilot.
2. **REPRESENTATIVE_PILOT:** 50–60 securities, >=5 năm, representative exchange/sector; official KBS direct HTTP + CafeF direct, field reconciliation và market QC/coverage evidence. Financial PIT là track riêng; unresolved giữ feature lock nhưng không chặn market pilot. Chỉ PASS bước này mở M1 scale planning.
3. **M1_SCALE:** >=300 securities và >=5 năm; chưa chạy.
4. **EXTENDED_SCALE:** historical eligible universe, 5–15 năm, có thể >1.200; không cap 350 và chưa chạy.

Mọi report có `status`, `gate`, `checks`, `blocking_reasons`, `scope` và input evidence hashes. Synthetic không pass gate thật. Bắt đầu quy trình manual và handoff cho nhiều collector tại [crawl/README.md](crawl/README.md).

## Commands

```powershell
.venv\Scripts\python.exe scripts/run_representative_pilot.py --help
.venv\Scripts\python.exe scripts/map_representative_pilot_canonical.py --help
.venv\Scripts\python.exe scripts/crawl_vnstock.py --help  # LEGACY SDK experiment only
.venv\Scripts\python.exe scripts/plan_crawl.py --help
.venv\Scripts\python.exe scripts/promote_vnstock.py --help
.venv\Scripts\python.exe run.py run --config configs/data/synthetic_smoke.example.json
```

`configs/data/representative_pilot.example.json` là active fail-closed template; cần reviewed local universe và PASS SOURCE_SMOKE gate. `configs/data/source_smoke.example.json` vẫn là safe smoke template. Legacy `pilot.example.json` không phải active runner config.

Canonical-readiness mapper của representative pilot chỉ đọc checksummed raw + PASS QC assessment, không gọi network. Nó ghi versioned candidate tables và lineage dưới `data/canonical/`, nhưng không promote khi `securities` identity contract còn thiếu. Vendor-adjusted KBS chỉ vào `adj_close`; CafeF bands không được trộn vào adjusted price basis và missing giữ `null`.

Secrets chỉ nằm trong environment variable. Một writer sở hữu một run; resume chỉ khi config/code/raw hashes khớp. JSONL dùng cho smoke/pilot; chỉ cân nhắc partitioned Parquet/DuckDB và serving storage sau khi M1 gates có evidence.

`data/` là local/gitignored runtime storage; `data/ACTIVE_INDEX.json` là local navigation index. Future generated artifact IDs theo `<prefix>-YYYYMMDDTHHMMSSZ-xxxxxxxx`, còn source/method/config nằm trong manifest. Existing real/referenced artifacts không bị rename; unreferenced synthetic/failed technical artifacts chỉ được archive nguyên trạng dưới `data/archive/<batch>/`, không silently delete.
