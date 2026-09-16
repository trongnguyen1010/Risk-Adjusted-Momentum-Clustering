# REPRESENTATIVE_PILOT — Canonical Guide

## Mục đích và trạng thái

`REPRESENTATIVE_PILOT` là real market-data gate 50–60 mã, request tối thiểu 5 năm, dùng để chứng minh acquisition, provenance, QC, coverage và reconciliation trước khi lập kế hoạch `M1_SCALE`. Đây là guide vận hành, không phải archive.

Trạng thái hiện tại:

- `SOURCE_SMOKE`: **PASS**, canonical run `source-smoke-20260916T122331Z-79427ec6`;
- `REPRESENTATIVE_PILOT`: **PASS**, real acquisition run `representative-pilot-20260916T185530Z-410ffcba`;
- `M1_SCALE`: **UNLOCKED FOR PLANNING / NOT EXECUTED**;
- financial PIT: `PIT_UNRESOLVED`, raw-only, không được dùng trong historical analytics.

```text
SOURCE_SMOKE PASS
        ↓
REPRESENTATIVE_PILOT 50–60 × >=5 năm
        ↓
REPRESENTATIVE_PILOT PASS
        ↓
M1_SCALE planning >=300
```

`SOURCE_SMOKE` và dry-run không thể mở `M1_SCALE`.

## Scope và universe contract

Universe thật phải được review riêng; repository không chọn hoặc đoán 50–60 ticker. Mỗi row theo contract `representative_pilot_universe` phải có `security_id` nếu có, `ticker`, `exchange`, `sector` hoặc `sector_status`, `listing_date` nếu có, `history_eligibility`, `selection_reason` và `reference_only`.

Rules fail-closed:

- 50–60 symbol duy nhất;
- đủ HOSE, HNX và UPCOM;
- nhiều sector, hoặc limitation đã review và ghi rõ;
- acquisition target >=5 năm;
- real clustering về sau yêu cầu >=3 năm usable observed history;
- `SHORT_HISTORY`/unknown history phải `REFERENCE_ONLY`;
- current exchange membership không được coi là historical-universe truth.

Template [representative_pilot.example.json](../../configs/data/representative_pilot.example.json) cố ý fail-closed với `LOCAL_OR_REVIEWED_PATH` và ngày placeholder cho tới khi universe thật được review.

## Active acquisition path

Official pilot dùng đúng path đã qua smoke:

| Domain | Provider | Acquisition client | Discovery provenance | Basis |
|---|---|---|---|---|
| Equity OHLCV | kbs | `delta_public_http` | `vnstock` | `VENDOR_ADJUSTED` |
| VNINDEX | kbs | `delta_public_http` | `vnstock` | `INDEX_POINTS`; volume unit giữ `PROVIDER_INDEX_VOLUME` |
| Reference/limits/value | cafef | `direct` | N/A | VND/share và raw VND value components |

`scripts/crawl_vnstock.py` là **LEGACY / SDK EXPERIMENT**, không phải official pilot evidence và không được dùng `SOURCE_SMOKE` gate để chạy 50–60 mã.

CafeF giữ độc lập `reference_price`, `ceiling_price`, `floor_price`, `matched_volume`, `matched_value`, `put_through_volume`, `put_through_value`. `traded_value` chỉ bằng cùng-row `matched_value + put_through_value` khi cả hai có mặt; missing không đổi thành zero.

## Volume roles và reconciliation

- KBS `volume` là provider-reported OHLCV volume đi cùng KBS historical OHLCV và là canonical candidate có provenance KBS.
- CafeF `matched_volume` và `put_through_volume` là hai provider fields độc lập.
- `MATCHED_VOLUME` chỉ khi exact equality; `TOTAL_VOLUME` chỉ khi exact equality với matched plus put-through; `OTHER_DOCUMENTED_SEMANTIC` cần mapping được trích dẫn; còn lại là `UNRESOLVED`.
- Với ACV evidence hiện tại: `UNRESOLVED`, `storage_policy=KEEP_SOURCE_QUALIFIED`, `equality_assumption=false`, `canonical_merge_allowed=false`, `market_collection_safe=true`.
- Không average, overwrite, đổi tên KBS volume thành CafeF matched volume hoặc suy equality từ approximate ratio.

## Invalid rows và price basis

VNM CafeF `2021-09-09` chỉ được `EXCLUDE_ROW` khi provider/symbol/date và exact raw evidence khớp policy versioned. Raw và finding vẫn bất biến; không repair/backfill. Evidence mismatch phải `FAIL_SYMBOL_WINDOW`.

KBS `VENDOR_ADJUSTED` không được đổi tên thành split-adjusted/total-return-adjusted. KBS adjusted OHLC không được merge trực tiếp với CafeF reference/limit basis. Không forward-fill price.

## Market gate và financial PIT là hai track

Market pilot có thể PASS khi financial còn `PIT_UNRESOLVED`. Khi unresolved:

- `financial_features_allowed=false`;
- raw financial side-track mặc định tắt và không tham gia market gate;
- historical financial clustering/backtest bị chặn;
- không gọi PIT là verified và không xóa financial track khỏi roadmap.

## Runner, dry-run và execution lock

Runner active:

```powershell
.venv\Scripts\python.exe scripts\run_representative_pilot.py `
  --config <reviewed-local-config.json> `
  --gate-report data/raw/source_smoke/source-smoke-20260916T122331Z-79427ec6/gate.json `
  --dry-run
```

`--dry-run` validate gate, universe, >=5 năm, exchanges/sectors, routing, batches, gitignore, financial lock và secret-like keys; nó tạo plan local với `network_requests=0`, không tạo provider raw, không tạo pilot PASS gate và không unlock scale.

Real pilot luôn yêu cầu explicit `--execute`; invocation không có mode hoặc có đồng thời `--dry-run --execute` sẽ bị từ chối. `--resume <run_id>` chỉ hợp lệ cùng `--execute`:

```powershell
.venv\Scripts\python.exe scripts\run_representative_pilot.py `
  --config <reviewed-local-config.json> `
  --gate-report <source-smoke-gate.json> `
  --execute
```

Mỗi `run.json` khóa exact `config_hash`, `universe_hash`, `source_gate_hash`, `code_hash`, deterministic `job_plan_hash`, KBS adapter version và CafeF adapter version. Resume recompute và so khớp toàn bộ identity; thiếu hoặc mismatch bất kỳ field nào đều fail-closed và yêu cầu run immutable mới. Mixed-version resume bị cấm, không migrate run cũ.

Resume chỉ chấp nhận artifact có cùng `run_id` và `mode=REAL_EXECUTION` trong cả `run.json` lẫn `manifest.json`; dry-run artifact không thể promote hoặc resume thành real execution. Trước khi tạo network client, runner verify hash và exact content của stored `job_plan.json`, exact manifest job-ID set và exact job definition cho từng ID. Mismatch dừng trước execution và không mutate run.

Trước một manual real run, quét lại toàn bộ local raw corpus mà không gọi network:

```powershell
.venv\Scripts\python.exe scripts\preflight_representative_pilot.py
```

Preflight kiểm tra JSON/envelope/schema/identity/checksum, position-aware CafeF snapshot replay, date mapping, price bands, duplicate dates/pages, pagination progress và requested-start coverage. Đây là reliability check, không phải official research gate. CafeF empty/partial page trước requested start được báo `SOURCE_EXHAUSTED`; chỉ hết đúng `max_pages` mới được báo `MAX_PAGES_REACHED`. Raw payload không bị sửa.

Config `representative_pilot.mapping_diagnostic.v2.json` cho phép hoàn tất acquisition để quan sát mapping/QC khi CafeF auxiliary history bị source-truncate. Acquisition gate ban đầu vẫn fail-closed. Sau review, policy v1 khóa KBS làm primary OHLCV yêu cầu >=5 năm và CafeF làm reference source bắt buộc non-empty nhưng được partial nếu giữ source-qualified. Offline finalizer verify toàn bộ raw checksum và chỉ exclude invalid row theo exact provider/symbol/date/raw-row hash; mismatch dừng. Max-pages, repeated page, overlap và non-progress vẫn dừng acquisition.

```powershell
.venv\Scripts\python.exe scripts\finalize_representative_pilot.py `
  --config configs/data/representative_pilot.mapping_diagnostic.v2.json `
  --gate-report data/raw/source_smoke/source-smoke-20260916T122331Z-79427ec6/gate.json `
  --qc-policy configs/data/representative_pilot.qc_policy.v1.json `
  --run-id representative-pilot-20260916T185530Z-410ffcba
```

Finalizer là zero-network immutable replay, không sửa raw và không được áp policy cho run ID khác. Kết quả canonical nằm tại [REPRESENTATIVE_PILOT_RESULT.md](REPRESENTATIVE_PILOT_RESULT.md).

## Raw layout và provenance

```text
data/raw/representative_pilot/<run_id>/
    run.json
    source_gate_reference.json
    job_plan.json
    manifest.json
    gate.json                 # chỉ future real execution
data/raw/kbs/<run_id>/...
data/raw/cafef/<run_id>/...
```

Run ID có dạng `representative-pilot-YYYYMMDDTHHMMSSZ-xxxxxxxx`. Mỗi provider artifact có provider/client/discovery provenance, symbol/range, endpoint/method, UTC fetch time, adapter version, rights/execution labels, SHA-256, raw path và HTTP state. Raw local được gitignore; không commit payload.

## QC, manifest và PASS criteria

Manifest per symbol ghi exchange/sector, requested/observed range, KBS/CafeF row counts, cross-source date gaps, duplicates, invalid rows, price basis, volume semantic status, provenance/hashes, history usability, `REFERENCE_ONLY` và QC. Aggregate ghi selected, usable >=5y, usable >=3y, exchange/sector coverage, failures, quarantines và conflicts.

Real PASS yêu cầu:

- PASS `SOURCE_SMOKE` evidence và real provider hashes;
- 50–60 unique symbols, >=5 năm requested, representative exchanges và sectors/reviewed limitation;
- source routing đúng KBS direct HTTP + CafeF direct;
- benchmark, market QC và configured coverage threshold pass;
- provenance/hash đầy đủ, price basis an toàn;
- invalid rows fail-closed; conflicts source-qualified và unmerged;
- không missing-to-zero, price forward-fill hoặc current-shares backfill;
- financial safety lock active khi PIT unresolved.

PASS chỉ unlock `M1_SCALE` planning. Nó không có nghĩa financial PIT/features ready, M2 methodology frozen, backtest ready, production licensed hoặc `EXTENDED_SCALE` đã được mở.

## Readiness evidence

Focused dry-run `representative-pilot-20260916T130831Z-78d8f2d2`: `PASS`, 50 fake fixture symbols, 713 planned jobs, zero network requests, không provider raw, không gate/unlock. Validation: 137/137 unit/integration/regression tests PASS; `compileall` PASS; synthetic smoke `run-20260916T141124Z-0b92997d` complete; tracked JSON và Markdown links PASS; `git diff --check` PASS. GitHub CI `NOT_RUN`.

Real acquisition và exact-hash QC replay đã hoàn tất; result gate PASS unlock planning `M1_SCALE`, không unlock financial features hoặc tự cho phép scale execution. Local raw/derived artifacts vẫn gitignored.
