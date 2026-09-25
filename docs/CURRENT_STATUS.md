# Trạng thái hiện tại — C8 complete-only

## Mục tiêu và lineage

DELTA xây data foundation point-in-time cho nghiên cứu clustering cổ phiếu Việt Nam; market readiness, tradability, historical identity và research readiness là các gate độc lập. Nhánh active là `m1-cafef-primary-experiment`. Lineage quan trọng: C6-R2 → C7 `0fe5ddf724618a418331785e35c36e030cfc00ea` → C8 complete-only (implementation ở HEAD sau commit stage này).

Nguồn market active là CafeF `TradeHistoryNew`; `AdjustPrice × 1000` được dùng như `adj_close` với `adjustment_basis=vendor_adjusted`, không tuyên bố split-only hoặc total-return.

## Dataset evolution và trạng thái C8

- Baseline: 500 mã; C5 có 490 `market_feature_ready_v2`, 10 mã còn deferred missing-session review.
- Expansion: frozen 600 mã; C7 xác nhận 452 COMPLETE và 148 chưa complete.
- C8 candidate trước quality gate: 500 + 452 = 952 unique ticker/security_id, không có reviewed-alias overlap.
- 148 mã còn lại (3 partial, 138 not acquired, 7 failed) được ghi `DEFERRED_EXPANSION_ACQUISITION`; không phải provider gap, suspension, delisting hay not-listed.
- C8 hiện ở trạng thái `PREPARED_NOT_EXECUTED`. Full normalization/audit/feature rebuild là job local nặng; chưa có kết quả C8 để diễn giải.

## Methodology invariants

- Snapshot chung: `2026-08-28`; row provider muộn hơn được giữ làm evidence nhưng không vào feature/readiness.
- Zero provider là observation thật; `0+0` không làm market readiness fail chỉ vì zero. Nếu một activity component null thì total null.
- Không ffill, bfill, interpolate, missing-to-zero, synthetic OHLC/return hoặc timeline compression.
- Full-history audit độc lập với exact latest-253 calendar-aligned audit.
- Calendar C5 hiện có provenance `kbs_observed_session_union`, không phải official independently reviewed exchange calendar. Vì vậy session có trong union nhưng không có valid CafeF observation được fail-closed thành `CALENDAR_UNCERTAIN`; chỉ calendar được đánh dấu `INDEPENDENTLY_REVIEWED_AUTHORITATIVE` mới cho phép `MISSING_ON_TRADEHISTORYNEW`.
- Full-history báo hai lớp: `observed_window_complete` và `full_history_status`. `COMPLETE` chỉ khi bắt đầu từ target 2020 và observed window đủ; provider boundary muộn hơn target là `UNCERTAIN_BOUNDARY`, không phải listing proof. Reviewed identity boundary có thể là `COMPLETE_WITHIN_OBSERVED_BOUNDARY`; gap/conflict/invalid/uncertain trong window là `INCOMPLETE`.
- `execution_integrity=PASS` chỉ nói output/count/hash đã sinh đúng. `data_quality_gate=FAIL` khi output audit/readiness thiếu hoặc lệch count; `PARTIAL` khi có latest-253/market-readiness fail hoặc observed window `INCOMPLETE`; `PASS` không đòi mọi mã có full target-period `COMPLETE`, nên `UNCERTAIN_BOUNDARY`/`COMPLETE_WITHIN_OBSERVED_BOUNDARY` vẫn được báo riêng và không tự promote `research_ready`.
- Expansion giữ nguyên truthful metadata `available_at=2026-09-25`; không backdate về snapshot/audit start. C8/V2 dùng opt-in hai lớp `market_observation_routing=OBSERVED_PROVIDER_INTERVAL` (feature config và expansion metadata) chỉ để route raw provider rows đã quan sát trong provisional interval vào market features. Baseline hoặc dataset không có cả hai marker vẫn dùng strict metadata PIT. Routing này không xác minh historical identity: expansion vẫn `historical_identity_ready=false` và `research_ready=false`, dù `market_feature_ready_v2` có thể true.
- Chỉ 452 acquisition COMPLETE được xử lý; original ZIP/C4/C5/C7 bất biến.
- Historical identity và `research_ready` không được tự động promote.

## Active file map

| Vai trò | Active path |
|---|---|
| Baseline C5 | `artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2/` |
| C7 inventory | `artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1/` |
| Frozen supplemental recovery | `configs/data/cafef_supplemental_v1/` |
| C8 contract | `configs/data/cafef_c8_complete_only_v1.json` |
| Active identity review | `configs/data/identity_review_v1.json` |
| C8 implementation | `src/delta_t1/ingestion/cafef_c8.py` |
| C8 runner | `scripts/run_cafef_c8_complete_only.py` |
| Expected C8 output | `artifacts/cafef_primary/cafef-c8-complete-only-v1/` |
| Focused tests | `tests/unit/ingestion/test_cafef_c8.py` |

Mọi path C1/KBS/representative-pilot cũ là **HISTORICAL/LEGACY**, không phải entry point cho C8.

## Lệnh thành viên cần dùng

```powershell
git checkout m1-cafef-primary-experiment
git pull --ff-only
git status --short
git rev-parse HEAD

.venv\Scripts\python.exe scripts/run_cafef_c8_complete_only.py `
  --expected-commit <C8_COMMIT_SHA> `
  --validate-only

.venv\Scripts\python.exe scripts/run_cafef_c8_complete_only.py `
  --expected-commit <C8_COMMIT_SHA> `
  --execute
```

`--execute` là job nặng, chỉ owner chạy local một lần trên clean exact commit. Không chạy supplemental shard song song với C8.

## Blocker, next stage và deferred work

Blocker hiện tại là C8 heavy run chưa được owner thực thi. Stage kế tiếp chính xác là **C8-VERIFY**: kiểm tra manifest/hash, counts, audit methodology và kết quả readiness trong artifact đã sinh; không tự chuyển sang clustering/backtest. Supplemental acquisition 148 mã, historical identity review, financial PIT và research-sample freeze đều deferred.

## Post-C8 Repository Consolidation

Trước C8, HEAD có khoảng 377 tracked files và 71 Markdown; sau C8-R1 dự kiến khoảng 383 files và 72 Markdown. Cleanup stage riêng nhắm khoảng 190–220 files và 20–25 Markdown. C8-R1 không xóa file.

- `KEEP_ACTIVE`: C5/C7/C8 artifacts/contracts/modules/tests, feature engine, market semantics, calendar, manifest verification và tài liệu này.
- `KEEP_MINIMAL_EVIDENCE`: `docs/DECISIONS.md`, `CHANGELOG.md`, `docs/data/kbs_pilot_semantics.md`, manifest/hash và contract cần để giải thích lineage.
- `SAFE_DELETE`: active C8 đã chuyển reviewed alias dependency sang `configs/data/identity_review_v1.json`, có source path/commit/hash provenance. Sau migration test/reference sweep ở cleanup stage, ưu tiên 28 file dưới `docs/crawl/plans/cafef_c1_*` (gồm legacy identity CSV), 5 `docs/crawl/m1_scale/WORKER_*.md`, phần lớn 17 file `docs/crawl/sources/*`, bốn C1 planner/runner scripts và test/config chỉ phục vụ các path đó. Runtime C8 không import các nhóm này.
- `REVIEW_BEFORE_DELETE`: generic ingestion/reconciliation modules, old C2/C3 runners còn được test tham chiếu, EDA notebook, và Product/web layer; chỉ xóa sau dependency/import/thesis-scope review.

Git history/tags giữ implementation cũ; cleanup không cần duy trì hàng chục tài liệu obsolete trong HEAD.
