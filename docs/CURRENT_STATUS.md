# Trạng thái hiện tại — C8 đã execute và verify

## Mục tiêu và lineage

DELTA xây data foundation point-in-time cho nghiên cứu clustering cổ phiếu Việt Nam; market readiness, tradability, historical identity và research readiness là các gate độc lập. Nhánh active là `m1-cafef-primary-experiment`. Lineage active: C6-R2 → C7 `0fe5ddf724618a418331785e35c36e030cfc00ea` → C8 implementation `d60c8cba49c90b3b36c346dfea463a1e4f659ee1` → C8-VERIFY.

Nguồn market active là CafeF `TradeHistoryNew`; `AdjustPrice × 1000` được dùng như `adj_close` với `adjustment_basis=vendor_adjusted`, không tuyên bố split-only hoặc total-return.

## Dataset evolution và trạng thái C8

**C8 = `EXECUTED_AND_VERIFIED`.** C8-VERIFY đọc offline artifact bất biến, không rerun heavy feature build. Manifest C8 tồn tại; 19/19 output hash, C5 manifest hash, C7 manifest hash, identity-review hash và năm source ZIP SHA256 đều khớp. Manifest ghi đúng implementation commit `d60c8cba49c90b3b36c346dfea463a1e4f659ee1`, `network_requests=0` và `supplemental_acquisition_executed=false`.

- Candidate: 952 = 500 `C5_BASELINE_500` + 452 `C7_COMPLETE_EXPANSION`; 148/600 expansion còn lại tiếp tục `DEFERRED_EXPANSION_ACQUISITION`.
- `feature_complete=922`; `market_feature_ready_v2=905`; 47 mã không market-ready.
- `latest253_complete=922`; `latest253_incomplete=30`.
- Tradability báo riêng: 675 `ACTIVE`, 276 `OBSERVED_ZERO_VOLUME`, 1 `UNKNOWN`.
- `historical_identity_ready=0` và `research_ready=0` là kết quả chủ ý của strict identity gate, không có nghĩa market features thất bại và không được promote trong stage này.
- C8 quality vẫn `PARTIAL` vì 30 latest-window fail, 47 market-readiness fail và 934 observed window full-history incomplete; execution integrity đã `PASS`.

### Baseline so với expansion

| Gate | C5 baseline 500 | C7 complete expansion 452 |
|---|---:|---:|
| `feature_complete` | 490 | 432 |
| `market_feature_ready_v2` | 490 | 415 |
| `latest253_complete` | 490 | 432 |
| `latest253_incomplete` | 10 | 20 |
| `ACTIVE` | 381 | 294 |
| `OBSERVED_ZERO_VOLUME` | 119 | 157 |
| `UNKNOWN` | 0 | 1 |
| full-history `INCOMPLETE` | 500 | 434 |
| full-history `UNCERTAIN_BOUNDARY` | 0 | 18 |
| `historical_identity_ready` | 0 | 0 |
| `research_ready` | 0 | 0 |

C8 baseline tái lập đúng C5: 490/500 market-ready và file diff security-level rỗng. Không có baseline regression.

### Decomposition các gate

- 30 latest-253 failures: 14 mã có 227 session `CALENDAR_UNCERTAIN`; 16 mã có 2.266 session `IDENTITY_OR_PROVIDER_BOUNDARY`. Không có confirmed `MISSING_ON_TRADEHISTORYNEW`, invalid hoặc conflict trong latest-253 failures.
- 47 market-readiness failures có primary cause không chồng lặp: 29 `INSUFFICIENT_LATEST253_REAL_OBSERVATIONS`, 17 `INSUFFICIENT_THREE_YEAR_HISTORY`, 1 `NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE` (GTX; provider-observed interval bắt đầu 2026-09-11, sau snapshot 2026-08-28).
- 17 mã `feature_complete=true` nhưng market readiness false là AAH, AIG, AVG, BGE, BHH, BMK, DKG, DSE, F88, GDA, HNA, QNP, RYG, SBG, TAL, TD6 và VPL. Tất cả có 253/253 observation và đủ required features; điều kiện duy nhất làm readiness fail là chưa đủ ba calendar years observed history. `trading_status` reason ở một số row không phải blocker dưới V2.
- Crosstab: latest complete + market ready = 905; latest complete + market not ready = 17; latest incomplete + market ready = 0; latest incomplete + market not ready = 30. Feature complete có cùng split 905/17; feature incomplete có split 0/30.
- Không có failure chỉ do benchmark window hoặc liquidity activity component: các `beta_126`/`liquidity_21` null xuất hiện cùng insufficient observation window, không được gán nguyên nhân mạnh hơn evidence.

## Full-history interpretation

Full-history status là 0 `COMPLETE`, 0 `COMPLETE_WITHIN_OBSERVED_BOUNDARY`, 18 `UNCERTAIN_BOUNDARY`, 934 `INCOMPLETE`. Đây không phải kết luận toàn dataset unusable.

- Calendar vẫn là `kbs_observed_session_union`, không phải independently reviewed authoritative calendar; 932 mã có tổng 13.159 session `CALENDAR_UNCERTAIN`.
- 641 mã có tổng 3.781 invalid provider rows; conflict trong full-history window = 0 mã/0 session.
- 18 mã có `UNCERTAIN_BOUNDARY`; ngoài ra audit ghi 244 reviewed identity-boundary và 74 provider-boundary deferred-review cases.
- Full-history failure chủ yếu là giới hạn calendar evidence theo conservative C8-R1 policy, có đóng góp từ invalid provider evidence. `CALENDAR_UNCERTAIN` không được đổi thành confirmed missing; provider boundary không được diễn giải thành listing date.

## Proposed market-only experimental universe

C8-VERIFY tạo proposed freeze candidate gồm đúng 905 row thỏa duy nhất `market_feature_ready_v2=true`. Theo semantics hiện tại, tập này có thể dùng làm `MARKET_ONLY_EXPERIMENTAL_UNIVERSE`, với tradability được báo riêng và không loại zero-volume chỉ vì volume bằng 0.

Tập 905 **không phải** `research_ready`, final research universe, canonical production universe hay historically identity-verified universe. Cả 905 vẫn có `historical_identity_ready=false` và `research_ready=false` dưới strict gate hiện tại. Không có performance-based selection.

Sample composition mô tả, không tuyên bố representativeness: candidate/market-ready theo exchange là HNX 249/248, HOSE 319/297, UPCOM 384/360; theo source là baseline 500/490 và expansion complete 452/415.

## Methodology invariants

- Snapshot chung: `2026-08-28`; row provider muộn hơn được giữ làm evidence nhưng không vào feature/readiness.
- Zero provider là observation thật; `0+0` không làm market readiness fail chỉ vì zero. Nếu một activity component null thì total null.
- Không ffill, bfill, interpolate, missing-to-zero, synthetic OHLC/return hoặc timeline compression.
- Full-history audit độc lập với exact latest-253 calendar-aligned audit.
- Session có trong non-authoritative union nhưng không có valid CafeF observation được fail-closed thành `CALENDAR_UNCERTAIN`; chỉ calendar `INDEPENDENTLY_REVIEWED_AUTHORITATIVE` mới cho phép `MISSING_ON_TRADEHISTORYNEW`.
- Expansion giữ truthful metadata `available_at=2026-09-25`; opt-in `OBSERVED_PROVIDER_INTERVAL` chỉ route observed provider rows, không xác minh historical identity.
- Chỉ 452 acquisition COMPLETE được xử lý; original ZIP/C4/C5/C7/C8 bất biến. Supplemental crawl, clustering và backtest không chạy.

## Active file map

| Vai trò | Active path |
|---|---|
| Baseline C5 | `artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2/` |
| C7 inventory | `artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1/` |
| Immutable heavy C8 | `artifacts/cafef_primary/cafef-c8-complete-only-v1/` |
| Compact C8 verification | `artifacts/cafef_primary/cafef-c8-verify-v1/` |
| C8 contract | `configs/data/cafef_c8_complete_only_v1.json` |
| Active identity review | `configs/data/identity_review_v1.json` |
| C8 implementation | `src/delta_t1/ingestion/cafef_c8.py` |
| C8-VERIFY implementation | `src/delta_t1/ingestion/cafef_c8_verify.py` |
| Offline verifier | `scripts/verify_cafef_c8_results.py` |
| Focused tests | `tests/unit/ingestion/test_cafef_c8.py`, `tests/unit/ingestion/test_cafef_c8_verify.py` |

Mọi path C1/KBS/representative-pilot cũ là **HISTORICAL/LEGACY**, không phải active entry point.

## Blocker, next stage và deferred work

C8-VERIFY đã hoàn tất, không có integrity regression hoặc baseline regression cần manual review. Stage kế tiếp riêng biệt là **R1 — REPOSITORY CONSOLIDATION**; không tự chuyển sang clustering/backtest. Supplemental acquisition 148 mã, historical identity review, financial PIT và research-sample freeze vẫn deferred.

## Post-C8 Repository Consolidation

R1 nhắm khoảng 190–220 tracked files và 20–25 Markdown. C8-VERIFY không xóa file.

- `KEEP_ACTIVE`: C5/C7/C8/C8-VERIFY artifacts, contracts, verifier/modules/tests, feature engine, market semantics, calendar, manifest verification và tài liệu này.
- `KEEP_MINIMAL_EVIDENCE`: `docs/DECISIONS.md`, `CHANGELOG.md`, `docs/data/kbs_pilot_semantics.md`, manifest/hash và contract cần để giải thích lineage.
- `SAFE_DELETE_CANDIDATE`: sau migration test/reference sweep ở R1, xem xét `docs/crawl/plans/cafef_c1_*`, `docs/crawl/m1_scale/WORKER_*.md`, phần lớn `docs/crawl/sources/*`, old source-smoke/representative-pilot docs, old C1 migration/planner docs, obsolete KBS recovery/M1 crawlers, old CafeF C1/C2/C3 runners và test/config chỉ phục vụ các path đó.
- `REVIEW_BEFORE_DELETE`: generic ingestion/reconciliation modules, old C2/C3 references còn được test dùng, old EDA notebook và Product/web layer; Product/web chỉ xóa nếu được xác nhận ngoài thesis scope.

Git history/tags giữ implementation cũ. R1 phải kiểm tra dependency/import/Markdown link trước khi xóa và là stage riêng, chưa được thực thi.
