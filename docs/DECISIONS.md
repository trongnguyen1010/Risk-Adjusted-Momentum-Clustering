# Các quyết định còn hiệu lực

Cập nhật 26/09/2026. Git history giữ thảo luận cũ; file này chỉ chứa quyết định đang ràng buộc implementation. Khi quyết định mới thu hẹp quyết định cũ, ID mới có ưu tiên cho active stage; historical rationale vẫn được giữ nguyên.

| ID | Quyết định |
|---|---|
| ADR-001 | DELTA có Research Core và Product Layer; research validity là ưu tiên hiện tại. |
| ADR-002 | Product/API/web chỉ đọc immutable projections và không recompute research. |
| ADR-003 | Raw/canonical/model artifact bất biến; missing giữ null/unavailable. |
| ADR-004 | Monthly snapshot K-Means + temporal tracking không phải Dynamic Clustering. |
| ADR-005 | Static K-Means deterministic là baseline; algorithm được chọn qua common registry. |
| ADR-006 | Real clustering cần ba calendar years usable observed history; short history là `REFERENCE_ONLY`. |
| ADR-007 | Sharpe/ROI bị cấm trong clustering input/quality/selection; Sharpe chỉ thuộc portfolio evaluation. |
| ADR-008 | CafeF/VietFin/Vnstock là source candidates; không source nào complete trước khi semantics và rights được verify. |
| ADR-009 | Financial data point-in-time và revision-aware; ratio chờ taxonomy/formula approval. |
| ADR-010 | Raw/vendor-adjusted/total-return price semantics tách biệt; basis change reset window. |
| ADR-011 | KBS 10-symbol pilot là legacy engineering evidence, không phải thesis evidence. |
| ADR-012 | Scale theo gate 3–5 smoke → 50–60 representative pilot → >=300 securities. |
| ADR-013 | Cluster quality, temporal stability và portfolio performance có module/decision riêng. |
| ADR-014 | JSONL dùng cho pilot; large-scale storage chỉ đổi sau M1 evidence. |
| ADR-015 | Tài liệu Markdown viết tiếng Việt, giữ project terms bằng English khi rõ nghĩa hơn. |
| ADR-016 | Không thêm concrete dynamic algorithm trước explicit approval trong `research/DYNAMIC_CLUSTERING_REVIEW.md`. |
| ADR-017 | Gate thật theo hierarchy `SOURCE_SMOKE → REPRESENTATIVE_PILOT → M1_SCALE`; source smoke không mở scale và synthetic không pass gate thật. `EXTENDED_SCALE` không có cap 350. |
| ADR-018 | Market contract 1.4 thêm nullable `reference_price`, `ceiling_price`, `floor_price`; mọi equity price là VND/share, volume là shares, traded value là VND; multiplier cần evidence. |
| ADR-019 | Reconciliation diễn ra ở field level theo semantic comparison key; không average. Source priority chỉ dùng khi compatible và policy approved/versioned; mọi decision giữ raw hashes. |
| ADR-020 | Active feature snapshot 1.5 không sinh Sharpe và tách `feature_complete`, `market_feature_ready`, `historical_identity_ready`, `research_ready`. Snapshot 1.3/1.4 chỉ đọc qua explicit legacy compatibility; Sharpe tiếp tục ở portfolio metrics. |
| ADR-021 | M2 configs mặc định `portfolio_evaluation.enabled=false`; chỉ M3/frozen protocol được bật backtest/performance. |
| ADR-022 | `shares_history` là optional canonical input với key `security_id + effective_date`; share counts khác nhau không bị giả định bằng nhau và current count không được backfill về lịch sử. |
| ADR-023 | Market cap, valuation ratios và F/M/Z scores là derived/versioned analytics; vendor ratio chỉ để đối chiếu. EPS cần weighted-average shares hoặc documented vendor basis. |
| ADR-024 | **Research/demo collection under accepted provider-rights uncertainty:** dùng public CafeF/KBS paths cho bounded private academic research/demo theo `ACCEPTED_RESEARCH_RISK`; provider rights vẫn `RIGHTS_NOT_VERIFIED`, không bypass access control, không raw redistribution, financial chỉ `RAW_ONLY_PIT_UNRESOLVED`, và production/commercial vẫn licensed-source-only. Owner quyết định ngày 16/09/2026; ảnh hưởng source adapters, smoke config/tests và risk policy. |
| ADR-025 | **SOURCE_SMOKE anomaly policy và gate:** provider-corrupt market row chỉ được exclude khi provider/symbol/date/raw fields khớp exact versioned evidence; raw/finding luôn giữ, không repair/backfill. Cross-source volume khác semantic phải giữ riêng, không giả định equality. Direct KBS HTTP ghi `acquisition_client=delta_public_http`, Vnstock chỉ là discovery provenance. Chỉ machine gate PASS mới unlock `REPRESENTATIVE_PILOT`. |
| ADR-026 | **REPRESENTATIVE_PILOT path alignment và financial-track separation:** official pilot dùng KBS direct HTTP + CafeF direct như SOURCE_SMOKE; Vnstock SDK chỉ legacy. Market pilot không đòi PIT-ready financial; `PIT_UNRESOLVED` bắt buộc `financial_features_allowed=false`. Cross-source volume unresolved giữ source-qualified, không merge. |
| ADR-027 | **Pilot canonical identity scope:** current KBS stock/name/exchange snapshot chỉ bổ sung display name và exact pilot membership. `valid_from` lấy first accepted pilot price, không lấy listing date; status luôn `provisional_verified_for_pilot`. Scope này cho phép validate market features trên frozen pilot nhưng không được dùng như complete historical universe cho scale/backtest. |
| ADR-028 | **M1 scale multi-machine contract:** 500 reviewed securities có tối thiểu 3 năm usable history được chia deterministic thành 5 immutable shard × 100 stable `security_id`; range thu thập chung dài 5–15 năm và đúng một shard sở hữu benchmark. Mỗi shard khóa config/universe/pilot-gate/assignment/code/job-plan/adapter hashes. Central verifier bắt buộc exact disjoint union và raw checksums; mapper/promoter chạy offline tập trung, fail khi duplicate canonical key và chỉ tính features sau merge. |
| ADR-029 | **M1 cross-machine handoff và central QC replay:** resume vẫn exact byte-identity; handoff chỉ chấp nhận LF/CRLF-equivalent frozen text sau semantic equality, exact stored job plan/manifest jobs và full raw checksum replay. KBS row vi phạm OHLC constraint và CafeF auxiliary row vi phạm price-band bị quarantine với raw path/hash, không repair và không canonical-merge. Shard gate gốc được giữ nguyên; central feature gate không được hạ để ép PASS. |
| ADR-030 | **M1 readiness/QC semantics:** collection coverage >=300, observed calendar span, feature completeness, market-feature readiness, historical-identity readiness, strict research readiness và financial PIT là trạng thái độc lập. `provisional` không tự làm market feature false nhưng luôn giữ historical identity/research false. Monthly M1 gate dùng latest completed collection month; partial current-month row vẫn được giữ. Không có quyết định frozen yêu cầu >=300 row đủ 252-session features cùng một ngày, nên threshold đó bị bỏ thay vì hạ; final research sample-size/density policy để `UNRESOLVED` và gate fail-closed. |
| ADR-031 | **`market_feature_stage_ready` vs `research_stage_ready` semantics:** `market_feature_stage_ready = true` khi và chỉ khi canonical promotion = PASS VÀ market feature artifact được sinh thành công. Không phụ thuộc vào historical identity, financial PIT, sample-size policy hay research gate. `feature_stage_ready` (deprecated alias) = strict research gate = False khi còn blocker. `research_stage_ready` = strict gate tương đương. Hai khái niệm độc lập và phải được test độc lập. `market_feature_stage_ready = true` KHÔNG mở M2, KHÔNG xác nhận identity, KHÔNG resolve PIT, KHÔNG approve sample-size. `observed_session_coverage` trong machine field giữ nguyên nhưng label trong report phải là `coverage_vs_observed_exchange_sessions` và phải ghi rõ đây là relative to *observed canonical exchange-session union*, KHÔNG phải official HOSE/HNX/UPCOM exchange calendar. |
| ADR-032 | **A5 recovery acceptance restoration:** CafeF `diagnostic_status=MATCH` chỉ là evidence ratio tương thích, không phải canonical acceptance. Khi field/price-basis contract chưa approved, candidate phải fail-closed dù provider có row hoặc volume bằng 0. Cấm zero-return imputation, forward/back-fill, interpolation, previous-close substitution, missing-to-zero và synthetic market rows. A5-R1 phải version contract trước A5-R2/R3; B0 bị block đến khi recovery semantics/determinism/evidence được chốt. |
| ADR-033 | **CafeF-primary C3 không dùng KBS comparator:** theo quyết định owner ngày 24/09/2026, branch CafeF đánh giá self-sufficiency trực tiếp từ raw CafeF và không dùng KBS làm acceptance comparator vì KBS thiếu phiên. Quyết định này không approve CafeF price basis. `PriceHistory` chỉ tạo provider-qualified candidates; 11 row OHLC lỗi bị quarantine, CTR/SHB có old-exchange coverage gap, corporate-action/calendar/benchmark/shares/financial domains còn thiếu. Canonical promotion và feature rebuild tiếp tục fail-closed chờ manual review. |
| ADR-034 | **CafeF C3-R1 canonical market contract:** owner chấp nhận `GiaDieuChinh × 1000` làm `adj_close` với `adjustment_basis=vendor_adjusted`, chỉ như research-price proxy; provider OHLC giữ staging-only và canonical `raw_* = null`. Total volume/value là tổng matched + negotiated chỉ khi cả hai component non-null/non-negative. 11 row lỗi bị loại không repair. Historical market availability dùng giả định 17:00 +07; identity pilot dùng effective-from availability và vẫn provisional. Reviewed shared-session calendar và VNINDEX price index được reuse, chỉ extension benchmark có đúng một public request. Non-market domains được defer. Pilot C3-R1 là `PARTIAL_MANUAL_REVIEW_REQUIRED` vì gap phiên CafeF làm `mom_252` và market-feature gate đạt 0/27; cấm fill hoặc nén timeline. |
| ADR-035 | **C6 expansion freeze và acquisition-only workers:** chọn 600 security trước crawl từ current KBS listing evidence sau khi loại current 500 và reviewed aliases; index/market importance thiếu evidence được ghi `UNAVAILABLE`. CafeF `TradeHistoryNew` là primary acquisition path, 5 shard cân bằng estimate, raw immutable và mỗi worker gửi một checksummed ZIP. C6-R1 yêu cầu owner truyền exact commit SHA bên ngoài frozen JSON; runner kiểm tra branch/HEAD/clean worktree trước dry-run/execute/resume, run và handoff ghi actual HEAD, central verifier từ chối mixed/mismatched commit. Null activity component luôn là `OBSERVED_WITH_NULL_VOLUME_COMPONENTS`, không suy zero. Worker không normalize/chọn lại ticker; C8 audit full history và latest-253 tập trung, độc lập. |
| ADR-036 | **C6-R2 expansion history policy:** giữ nguyên frozen 600, reserve 100 và ownership năm shard; CafeF expansion dùng `c6-cafef-expansion-v2`/`BASE_2020`, target `2020-01-01 → 2026-09-23`, comparison snapshot `2026-08-28`. Crawl lùi đến target hoặc neutral provider/listing-history boundary; empty/short history không chứng minh suspension/not-listed và không được fabricate missing 2020 rows. |
| ADR-037 | **C8 complete-only owner decision:** current C8 giữ 500 baseline và chỉ xử lý 452 expansion có C7 acquisition `COMPLETE`; 148 mã còn lại là `DEFERRED_EXPANSION_ACQUISITION`, không tham gia active audit/features và không được diễn giải thành provider gap/suspension/listing state. Snapshot feature giữ `2026-08-28`; full-history và latest-253 là audit độc lập; market readiness tách tradability/identity/research readiness. Supplemental config được freeze cho future recovery và không chạy trong C8. |
| ADR-038 | **C8-R1 conservative audit semantics:** calendar C5 là `kbs_observed_session_union`, không phải independently reviewed authoritative exchange calendar; absence vì vậy là `CALENDAR_UNCERTAIN`, chỉ authoritative marker mới mở `MISSING_ON_TRADEHISTORYNEW`. Full-history tách `observed_window_complete` khỏi target-period status; provider boundary sau 2020 là `UNCERTAIN_BOUNDARY`, không chứng minh listing/full target history. `valid_to` là exclusive. `execution_integrity` độc lập với `data_quality_gate`. Active reviewed aliases chuyển sang `configs/data/identity_review_v1.json` với legacy commit/hash provenance. |
| ADR-039 | **CafeF active market source hậu C8:** `TradeHistoryNew` là active market source; `AdjustPrice × 1000` là `vendor_adjusted` proxy, không phải split-only/total-return. Quyết định này thu hẹp ADR-008 cho active market path; rights, financial PIT và historical identity vẫn unresolved. |
| ADR-040 | **Market-only M2 eligibility:** M2-PREP được phép freeze `market_experiment_eligible(t) = market_feature_ready_v2(t)` theo từng snapshot, không promote `historical_identity_ready`/`research_ready`. Đây là ngoại lệ hẹp so với câu “không mở M2” của ADR-031: chỉ mở preparation/development market-only sau protocol approval, không mở strict research hay backtest. |
| ADR-041 | **Không terminal-filter 905:** 905 chỉ là count tại snapshot `2026-08-28`; membership tháng trước phải lấy readiness tại chính snapshot đó. Không áp latest membership ngược lịch sử. |
| ADR-042 | **M2 không portfolio:** M2-PREP và market-only M2 giữ `portfolio_evaluation.enabled=false`; không backtest/performance và không dùng return/Sharpe/ROI để chọn model. |
| ADR-043 | **Readiness discontinuity gate:** các đoạn gián đoạn lớn và zero-readiness periods trong monthly report phải được giải thích trước khi freeze development/validation windows. D1 chỉ ghi nhận, không diễn giải hoặc sửa dữ liệu. |
| ADR-044 | **M2 market-only eligibility freeze:** `market_experiment_eligible(t) = market_feature_ready_v2(t)` tại cùng snapshot; legacy `eligibility`, tradability, historical identity và research readiness giữ tách biệt. Latest 905 không được retrospective-filter. |
| ADR-045 | **Monthly readiness diagnosis:** gap VNINDEX `2023-05-15` lan qua `beta_126` gây zero readiness 2023-05..10; 0 canonical equity rows tại open session `2025-02-03` lan qua strict `mom_252` gây zero readiness 2025-02..2026-01. Giữ missing, không impute/timeline-compress. |
| ADR-046 | **M2-PREP v1 status:** feature set, no-imputation, portfolio firewall và Dynamic `NOT APPROVED` được khóa; development/holdout, coverage/skip rules, `k`, outlier/scaling, PCA components và feature-version resolution cần owner/mentor review. Không tạo final M2 config; status `MANUAL_REVIEW_REQUIRED`. |
| ADR-047 | **M2 Protocol v1 owner review và stage transition:** owner ngày `2026-09-26` chấp thuận development `2023-11-30..2025-01-24`, sealed holdout `2026-02-27..2026-08-28`, minimum eligible `>=120`, 8 market features, no winsorization/clipping, RobustScaler per snapshot với z-score sensitivity, one global `k` chọn trong `2..8` bằng median Silhouette rồi median Davies–Bouldin tie-break, PCA comparator với cumulative explained variance `>=90%`, C8 feature snapshot `1.6.0` active và registry `1.5.0` legacy-compatible. Dynamic vẫn `NOT APPROVED`, portfolio OFF. Quyết định này giải quyết owner-review gate của ADR-046 và mở M2-R1 để materialize contract; không sửa historical M2-PREP artifact, không tự tạo config, không chạy clustering/holdout và không cho phép M2-R2 trước khi M2-R1 PASS. |

## Open decisions

### CafeF-first bounded trial50 — 08/10/2026

Owner yêu cầu triển khai lượt kiểm tra50 mã sau paired benchmark. Dùng runner/version
riêng `cafef-financial-trial-v1`, giữ nguyên frozen market-ready membership và plan
năm giai đoạn. Bốn mã reference pilot là cohort validation riêng; VNM/PVS không tự
trở thành market-ready trial members. Pilot gate kiểm consistency với78 ô benchmark
(kể cả exceptions), không phải numeric acceptance. Trial50 phải fresh CafeF detail,
không seed traffic hoặc fallback KBS. Candidate raw/field mapping không có multiplier
approved; sector proposed, fiscal scope, PIT/revisions và exact notes vẫn review.

600 base/≤120 gap requests,≤900 attempts/300MB/2h; spacing≥2s, no boundary retries,
OS epoch lock và counters/deadline persist qua resume. Thay journal sang một hash-
chained JSONL durable, cache pointer tới immutable raw, tránh per-chunk small files.
Giữ raw source conflicts và302 errors; không suy thiếu thành0 hoặc relabel kỳ.
PDF/OCR không chạy trong structured scope; xuất document/PIT/notes queue rõ ràng.
Financial/cluster/research/full-universe gates false; không tự mở trial100. Báo cáo
ở [report](../artifacts/reports/cafef-financial-trial50-v1/report.md),
[runbook](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md#flow-cafef-first-active--08102026).

### Financial raw pilot — 2026-10-02

Update 03/10/2026: thêm bounded detail remediation contract
`cafef-financial-detail-v1` cho existing four-symbol pilot, document inspection
và comparison-only field inventory. Giữ HTML display number là candidate với
unit_scale null; header presence khác numeric period coverage; failed summary
pages không tham gia comparison. File lựa chọn để PDF inspection không phải
canonical vintage policy. Các manual PDF facts giữ page/hash và exact column
period, nhưng availability vẫn null; không generalize FPT EPS/duration rules.
Không đổi canonical schema/taxonomy/PIT methodology hoặc bật calculator.
Evidence/report: `artifacts/reports/financial-remediation-v1/`.

Owner yêu cầu triển khai nhánh financial trong `SourceCode-CafeF`, kế thừa existing
CafeF discovery. Stage hiện tại chỉ acquisition và coverage pilot bounded cho
FPT/VNM/PVS/ACV, 2021–2025, KQKD/CDKT/LCTT, QUY/NAM. Contract
`cafef-financial-raw-pilot-v1` giữ nguyên provider payload và tạo immutable local run,
code/config snapshot, UTC fetch metadata, hashes và offline coverage replay.
Missing report group, missing periods, pagination overlap và request/page caps phải
được báo rõ; không suy completeness từ HTTP success hoặc provider count.
ADR-009/023/024/026 tiếp tục áp dụng: PIT unresolved, không canonical financial,
không financial features, không ratio/score calculator. Không thay financial timing,
taxonomy, canonical schema, market-only protocol hoặc historical identity.
PIT/taxonomy/formula approval là bước riêng sau khi coverage evidence đủ.

| ID | Cần quyết định |
|---|---|
| OPEN-01 | Final thesis wording và research questions |
| OPEN-02 | Approved Dynamic Clustering objective/method |
| OPEN-03 | CafeF/VietFin/Vnstock rights, endpoint semantics, field mappings/multipliers và source-priority approval |
| OPEN-04 | Historical universe/delisted security master authority |
| OPEN-05 | Financial feature taxonomy, sector treatment và citations |
| OPEN-06 | Final development/validation/holdout và purging/embargo |
| OPEN-07 | Comparator set và PCA protocol |
| OPEN-08 | Final portfolio universe/ranking/tie policy |
| OPEN-09 | Authority, history coverage và field semantics cho listed/outstanding/issued/treasury shares |
| OPEN-10 | Approved usable-density và final research sample-size threshold cho clustering universe |

Quyết định mới ghi: problem → alternatives → choice/reason → evidence → owner/date → affected contract/config/tests → remaining limits.

## ADR — Post-M1 market-only experiment preparation

Problem: C8/R1/M1-REPORT chứng minh 905 securities market-ready ở latest snapshot nhưng strict identity/research gate vẫn 0; dùng 905 như fixed historical universe sẽ tạo survivorship/terminal-membership error. Choice: owner chấp nhận bước M2-PREP giới hạn để freeze eligibility theo snapshot, windows, preprocessing, comparator và evaluation contract. `market_experiment_eligible(t)` bằng `market_feature_ready_v2(t)` tại chính snapshot `t`; readiness discontinuities phải được giải thích trước window freeze. Evidence: immutable C8 verification và M1 report với 80 monthly snapshots, snapshot cuối `2026-08-28`. Owner/date: project owner, 26/09/2026. Affected: active documentation và future M2 protocol only. Remaining limits: D1 không thay code/data/artifact, không chạy clustering/backtest, không resolve historical identity/financial PIT/rights, và không approve final research universe.

## ADR — Research/demo collection under accepted provider-rights uncertainty

Project owner quyết định dùng public CafeF/KBS paths cho bounded private academic research/demo. Provider rights vẫn `RIGHTS_NOT_VERIFIED`; execution label là `ACCEPTED_RESEARCH_RISK`. Không bypass access control, không raw redistribution, financial data chỉ `RAW_ONLY_PIT_UNRESOLVED`, và production/commercial vẫn chỉ dùng licensed/approved source. Quyết định ngày 16/09/2026; affected: source adapters, smoke config/tests và data-usage risk policy. Remaining limit: quyết định này không xác minh copyright, provider rights hoặc PIT timing.

## ADR — SOURCE_SMOKE anomaly resolution và executable gate

Problem: một CafeF row VNM có price band bất khả thi và KBS/CafeF ACV volume khác nhau nhưng không có bằng chứng unit/mapping error. Alternatives gồm sửa/điền row, ưu tiên một source, fail toàn smoke, hoặc áp policy evidence-bounded. Choice: exact raw-evidence match mới cho phép gắn `INVALID_REQUIRED_MARKET_ROW` và exclude khỏi CafeF constraint promotion; raw giữ nguyên, KBS cùng ngày không bị xóa. Volume khác semantic được source-qualify và giữ riêng. Direct public HTTP provenance được ghi đúng client; machine gate fail-closed và chỉ PASS mới unlock representative pilot. Evidence: canonical run `source-smoke-20260916T122331Z-79427ec6`, gate/hash manifest và unit tests. Owner/date: project owner, 16/09/2026. Affected: source adapters, smoke config/runner, planning gate, tests, manifest. Remaining limits: rights vẫn chưa xác minh, corporate action còn partial, shares chỉ current snapshot, financial PIT unresolved; quyết định không mở M1/extended scale.

## ADR — REPRESENTATIVE_PILOT source alignment và financial separation

Problem: legacy pilot dùng Vnstock SDK khác với acquisition path đã smoke-validate; gate cũ cũng biến financial PIT thành market blocker và classifier ACV overclaim semantic từ approximate ratio. Choice: official pilot chỉ dùng KBS direct HTTP (`delta_public_http`, discovered via Vnstock) và CafeF direct; SDK path giữ legacy <=5-symbol reference only. Market gate tách financial track: `PIT_UNRESOLVED` không chặn market collection nhưng luôn khóa financial features/historical analytics. Volume chỉ nhận `MATCHED`/`TOTAL` bằng exact equality hoặc `OTHER_DOCUMENTED_SEMANTIC` bằng mapping rõ; còn lại `UNRESOLVED`, source-qualified và unmerged. Evidence: canonical smoke run, zero-network dry-run, config/universe contracts và targeted tests. Owner/date: project owner, 16/09/2026. Affected: pilot runner/config/schema, planning gate, source classifier, docs/tests. Limits: rights vẫn chưa verified; M1 scale chưa chạy.

## ADR — Representative pilot primary/reference coverage và exact-hash QC

Real run `representative-pilot-20260916T185530Z-410ffcba` cho thấy KBS có >=5 năm OHLCV cho 55/55 mã, trong khi CafeF direct trả non-empty nhưng source-truncated history cho 53 mã. Choice: KBS là primary market history/benchmark; CafeF là auxiliary limits/value/volume source được phép partial nhưng luôn source-qualified và không canonical-merge. Provider invariant violation chỉ được exclude nếu versioned policy khớp exact provider, ticker, trade date và raw-row SHA-256 trên đúng immutable run; thiếu/thừa/mismatch fail-closed. Offline replay phải verify mọi artifact checksum, không network và không mutate raw. Evidence: policy v1, assessment/gate và result report ngày 17/09/2026. `REPRESENTATIVE_PILOT=PASS` chỉ unlock planning M1 scale; financial PIT và production rights vẫn unresolved.

## ADR — Pilot canonical identity scope

Problem: frozen pilot universe có stable provider security ID, ticker/exchange/sector/listing date nhưng thiếu company name; current metadata không tự chứng minh complete historical identity. Choice: exact-match 55 KBS `stock` rows cung cấp current display name/exchange, còn interval chỉ bắt đầu tại first accepted pilot market observation và mang `provisional_verified_for_pilot`. Promotion phải verify immutable parent hashes, exact ticker/exchange set, schema/FK và 55/55 latest market feature eligibility. Evidence: security master v1 và canonical run `canonical-pilot-20260917T062832Z-6748ac02`, 17/09/2026. Affected: canonical pilot mapper/promoter, tests, result/status docs. Remaining limit: không đóng `OPEN-04`, không biến current membership thành historical universe truth, không mở financial features và không tự cho phép M1 scale execution.

## ADR — M1 scale multi-machine execution và merge

Problem: representative runner bị khóa đúng 50–60 mã và raw trên năm máy không thể ghép an toàn bằng copy/concatenate. Alternatives gồm chạy pilot năm lần, chia theo field, hoặc tạo scale-specific shard contract. Choice: giữ pilot bất biến; M1 scale dùng master universe 500 stable `security_id` đã có bounded evidence >3 năm, deterministic 5×100 assignment, một benchmark owner, explicit dry-run/execute/resume và exact identity hashes. Range request chung phải dài 5–15 năm; `usable >=5y` vẫn được báo cáo nhưng không phải per-symbol gate, vì contract clustering là tối thiểu ba calendar years usable observed history. Handoff chỉ được map khi năm shard pairwise-disjoint, union đúng master universe, job definitions/status và raw checksums hợp lệ. Duplicate canonical key fail-closed; canonical promotion và feature calculation chỉ chạy một lần tại coordinator. Evidence: `m1_scale.py`, five CLI entry points và targeted tests, 17/09/2026. Affected: M1 config, acquisition, handoff, canonical mapping/promotion và team runbook. Remaining limits: real five-shard network run chưa thực hiện; identity vẫn observed-interval provisional, financial PIT vẫn unresolved.

## ADR — M1 cross-machine handoff và central QC replay

Problem: Windows checkout có thể đổi LF/CRLF của frozen JSON/source, làm byte hash khác dù assignment và deterministic job plan không đổi; shard-local gate cũng coi CafeF auxiliary truncation/price-band finding như primary-market failure. Choice: resume tiếp tục strict và không migrate run; central handoff chỉ chấp nhận hash của original/LF/CRLF form, đồng thời bắt buộc semantic equality, stored job-plan hash/content, exact manifest job set/definitions, adapter provenance và checksum của mọi raw artifact. Central mapper replay raw: invalid KBS/CafeF rows bị exclude có raw path/hash trong quarantine, không sửa hoặc backfill; CafeF không được dùng cho row đó. Shard gate FAIL vẫn giữ immutable và chỉ acquisition-complete handoff mới được central replay. Evidence: five runs của `m1-scale-20260917T080125Z-ad8cebe3`, handoff/candidate manifests ngày 18/09/2026. Remaining limit: historical identity và financial PIT chưa verified; usable-density/research sample-size policy chưa được phê duyệt.

## ADR — M1 readiness, calendar span và completed-month semantics

Problem: M1 scale cố ý dùng identity `provisional`, nhưng feature builder gộp trạng thái này vào lỗi `metadata`, làm mọi market feature bị loại; QC gọi calendar range là “usable”; và row 15/09 của collection kết thúc 15/09 bị coi như completed month-end. Implementation cũng dùng threshold >=300 latest feature-complete dù ADR-012 chỉ khóa >=300 securities collected với long-history coverage. Alternatives là đổi identity thành verified, hạ threshold xuống kết quả hiện có, hoặc tách state đúng nghĩa. Choice: giữ nguyên identity provisional; feature snapshot 1.5 thêm bốn flag độc lập; legacy/scoped `eligibility` không bị silently redefine. Calendar range đổi tên `observed_span_3y/5y` và report thêm row/session density. M1 monthly research snapshot chỉ chọn tháng collection đã hoàn tất; partial-month row vẫn immutable. Threshold >=300 same-date complete features bị bỏ vì không có frozen-methodology backing, còn sample-size/density policy ghi `UNRESOLVED`. Gate vẫn fail-closed do identity, financial PIT và policy chưa duyệt. Evidence: code/tests và offline artifact mới sinh từ candidate immutable ngày 18/09/2026. Affected: feature snapshot 1.5, M1 promotion/gate/QC, docs/config/tests. Remaining limits: không đóng OPEN-04/05/10, không cho phép backtest và không thay raw/provider data.

## ADR — market_feature_stage_ready vs feature_stage_ready và session coverage label

Problem: `feature_stage_ready` trong canonical manifest M1 bị gắn với strict research gate (`gate_status == "PASS"`), tạo ra sự nhầm lẫn: khi feature artifact đã được sinh thành công mà gate vẫn FAIL (do historical identity provisional / financial PIT unresolved / sample-size policy unresolved), field này = False dù market feature analysis hoàn toàn khả thi. Ngoài ra, `observed_session_coverage` không ghi rõ denominator là observed canonical session union, không phải official exchange calendar, có thể hiểu nhầm là coverage hoàn toàn của HOSE/HNX/UPCOM. Alternatives: đổi gate thành PASS (bị cấm—hạ gate), xóa field (phá compatibility), hoặc tách thành hai concept rõ ràng. Choice: thêm `market_feature_stage_ready` = canonical promotion PASS AND feature artifact generated; giữ `feature_stage_ready` như deprecated alias = strict gate (không thay đổi giá trị); `research_stage_ready` giữ nguyên = strict gate. Hai khái niệm độc lập và được test độc lập. Session coverage label trong report markdown đổi thành `coverage_vs_observed_exchange_sessions` kèm disclaimer; machine field name `observed_session_coverage` giữ nguyên để không phá per_symbol.jsonl schema. Evidence: canonical run `canonical-m1-scale-20260918T141019Z-7c003543`, focused tests A-G, và offline regeneration ngày 18/09/2026. Owner/date: project owner, 18/09/2026. Affected: `m1_scale.py`, `m1_scale_quality.py`, tests, `DECISIONS.md`, quality report markdown. Remaining limits: `market_feature_stage_ready = true` KHÔNG mở M2, KHÔNG approve research sample-size, KHÔNG unlock backtest; ba research blockers vẫn fail-closed.

## ADR — CafeF-primary C3 self-sufficiency thay KBS comparator

Problem: KBS thiếu phiên nên owner không muốn dùng KBS làm acceptance comparator cho
nhánh CafeF. Alternatives gồm tiếp tục KBS-vs-CafeF, coi CafeF tự động canonical-ready,
hoặc đánh giá self-sufficiency theo contract hiện tại. Choice: bỏ comparator KBS riêng
trên branch này và chạy offline C3 field-by-field trên checksummed CafeF raw. CafeF được
coi là primary **candidate** khi C1 integrity pass, nhưng không tự động thành canonical
source. Evidence: run `cafef-c2-c3-offline-20260924` có 27/27 raw audit PASS, 33.259
candidate rows, 11 row OHLC cần quarantine, và hai identity intervals CTR/SHB không có
observation. C2 chỉ tạo 183 discontinuity diagnostics vì chưa có event documents/terms.
Owner/date: project owner, 24/09/2026. Affected: CafeF offline audit config/module/script,
tests và experiment handoff. Remaining limits: price basis, volume/value policy,
authoritative calendar, benchmark, corporate actions, shares history và financial PIT
vẫn unresolved; canonical promotion, research-price derivation và feature rebuild phải
fail-closed đến manual review.

## ADR — CafeF C3-R1 vendor-adjusted canonical market pilot

Problem: C3 đã chứng minh raw integrity nhưng chưa có price basis, total-activity,
availability, calendar và benchmark contract đủ để thử canonical market pipeline.
Alternatives gồm tiếp tục chặn toàn bộ, tự tái dựng corporate actions, hoặc chấp nhận
bounded vendor-adjusted proxy. Choice: `GiaDieuChinh × 1000` được map vào `adj_close`
với `vendor_adjusted`; không tuyên bố split-only/total-return. Provider OHLC không đi vào
canonical `raw_*`. Volume và traded value chỉ cộng matched + negotiated khi cả hai
component có evidence; missing giữ null. Eleven invalid rows bị quarantine và không sửa.
Historical `available_at` là 17:00 +07 theo
`CAFEF_EOD_AVAILABILITY_ASSUMPTION_V1`; identity vẫn
`provisional_verified_for_pilot` theo effective-from assumption.

Reviewed canonical security/calendar/VNINDEX evidence được reuse; VNINDEX chỉ được nối
đến 23/09/2026 bằng một bounded public benchmark request. Calendar là
`BENCHMARK_DERIVED_RESEARCH_CALENDAR_V1`, áp shared sessions cho HOSE/HNX/UPCOM và
không được gọi là official. Shares, corporate actions và financial domains được defer
vì active market features không phụ thuộc chúng. Dry-run tạo đủ snapshot cho 27 mã,
nhưng CafeF thiếu hai open sessions 29–30/01/2026 ở mọi mã và còn thiếu 13 sessions
02–25/02/2026 ở ACV/QNS/VEA/VGI. Vì `mom_252` yêu cầu full real window, coverage là
0/27 và stage giữ `PARTIAL_MANUAL_REVIEW_REQUIRED`; không ffill, interpolate, zero
return hay timeline compression. Evidence: immutable local artifact
`cafef-canonical-market-pilot-v1`, quality report và output hashes ngày 24/09/2026.
Affected: canonical builder/config/tests, CafeF experiment plan và feature readiness.
Remaining limits: cần resolve đúng các missing sessions; CTR old UPCOM và SHB old HNX
vẫn là structural coverage exceptions; historical identity, financial PIT và rights
không được nâng cấp bởi quyết định này.

## ADR — Financial annual evidence, score variants và publication gate (03/10/2026)

Problem: CafeF summary thiếu cash flow/quarter gaps; full detail vẫn không chứng
minh đơn vị, duration, revision và actual availability. Literature B6/B7 hỗ trợ
fundamentals/valuation nhưng chưa định nghĩa F/M/Z. Owner giao tiếp tục acquisition,
tham khảo literature và chọn hợp lý. Choice: giới hạn pilot FPT/VNM/PVS/ACV,
documents 2019–2025, annual consolidated non-financial; giữ mọi document vintage,
PDF/hash/page provenance và null missing. Chọn F theo Table 1 average-assets
turnover, M eight-variable cash-flow variant 2013, EM Z-double-prime có intercept;
chưa threshold M/Z. EPS cần adjusted numerator/weighted shares và revision;
P/E raw price phải compatible share basis, P/B cần parent common equity.

Các lựa chọn là acquisition/implementation targets, không phê duyệt PIT hoặc
M2 protocol. Không suy availability từ ngày ký/filename/fetch; VAS và IFRS giữ
riêng. PDF/OCR/raw present không phải canonical-ready. Chưa full-universe crawl.
Evidence: [contract](research/FINANCIAL_FEATURE_CONTRACT.md), executable policy
`configs/data/financial_evidence_policy_v1.json` và [report v2](../artifacts/reports/financial-remediation-v2/report.md).
Affected: document collectors, PDF/OCR evidence, annual checklist, configs/tests/docs.
Remaining: full VAS VNM bốn năm, full annual/notes extraction, exact publication
version/timezone, historical identity/sector/shares, taxonomy/reconciliation.
PIT NOT_READY; promotion khi cần approval vẫn MANUAL_REVIEW_REQUIRED.

## ADR — Annual document acceptance và FPT core evidence (03/10/2026)

Problem: raw presence và visual observations trước đây gồm quarterly, thiếu explicit
framework hoặc khác vintage; không thể dùng chung để xác nhận annual score inputs.
Choice: thêm acceptance overlay yêu cầu consolidated VAS, annual calendar duration
hoặc year-end instant, giá trị finite, unit đúng field và PDF/image hashes. Giữ zero
thật, mọi revision và canonical value null; không infer publication từ audit date.
Không alias net profit/debt cash-flow/issuance proceeds thành score definitions.

FPT core 49/49 ô 2019–2025 có document evidence. Hai comparative 2020 reclassified
và EPS 2024 revised vẫn riêng; sửa unit EPS earnings numerator qua append-only
correction run. Presence dependency không phê duyệt compatible vintage hoặc PIT.
Evidence: [report](../artifacts/reports/financial-pilot-closure-v1/report.md),
`configs/data/financial_pilot_closure_v1.json`, local `pilot_readiness_v4`.
Affected: offline readiness analyzer/CLI/tests và financial handoff. Full pilot
PARTIAL; remaining: notes/mapping, actual publication version/timezone, VNM full
VAS gaps, other pilot symbols và historical identity/share basis. Không thay
definition contract hoặc mở financial canonical/score/runtime.

## ADR — Financial execution matrix, note evidence và exact publication linkage (03/10/2026)

Owner yêu cầu lập plan và triển khai financial; quyết định dùng FIN-D1 → FIN-D5
trong unified plan, ưu tiên hoàn thiện FPT reference trước four-symbol closure
và bounded expansion. Task matrix ghi riêng annual field-year presence với
semantic/vintage/PIT/identity/TTM/price/share-basis blockers; không đồng nhất
coverage với task readiness hoặc financial feature validity.

Bounded offline OCR tái sử dụng prefix main pages, chỉ render phần notes còn lại,
kiểm tra PDF/image hashes và exact inventory. Original EPS notes cho thấy parent
profit phải trừ reward/welfare reserve; diluted denominator chỉ derive bằng basic
khi note cùng vintage explicitly xác nhận không có potentially dilutive shares.
Debt/current portion và owned-PPE depreciation giữ candidate fields riêng,
chưa alias vào score debt hoặc toàn bộ depreciation; cần reconciliation.

Publication evidence phải đi từ observed issuer disclosure card tới exact
attachment URL/content hash. Ngày 19/03/2026 gắn original audited FPT 2025 PDF;
DATE_ONLY/timezone null/available_at null, không inherit sang annual report PDF,
không suy từ audit date/filename. Không nới PIT hoặc approved score variants.

Evidence: [execution report](../artifacts/reports/financial-execution-v1/report.md),
`configs/data/financial_execution_plan_v1.json`, local `pilot_readiness_v6` và
`task_readiness_v3`. FIN-D1 COMPLETE; FIN-D2/3 PARTIAL; FIN-D4/5 pending.
Remaining: FPT semantic mapping/publication history, other symbols/full VAS VNM,
quarters/TTM và historical identity/sector/share basis. Financial PIT NOT_READY;
không thay market-only protocol, không crawl full universe.

## ADR — FIN-D2 reusable work queue và EBIT/equity bridges (03/10/2026)

Owner yêu cầu tiếp tục reference stage và workflow dùng khi scale. Chọn offline
queue deduplicate theo symbol/year/field, nối all-document inventory với OCR
hints và task consumers. Tách acquire, full-framework gaps, extraction, semantic
mapping, same-vintage conflict và publication; external TTM/price/identity riêng.
VNM annual-report candidate không đóng full-VAS gap. Không automatic acceptance
qua OCR/search hints; caps four-symbol/32 PDFs/800 reused OCR pages/2.000 queue cells.

FPT EBIT 2024/2025 dùng EBT + expensed interest, kiểm tra độc lập printed operating
profit, financial income/expense, associate và other income/expense cùng PDF/column.
Đây là reconciliation theo contract đã chốt, không alias VAS code30 thành EBIT.
Notes cho thấy parent ESOP khác stock dividend và NCI capital; equity code400-NCI
khác parent note do funding430 nên không tự approve parent common equity. Debt
current loan portion không đủ bridge combined loan/lease với code338; giữ pending.
No-issuance/ordinary-income/PPE/net-receivables/common-equity mapping chưa approved.
Evidence: [report](../artifacts/reports/financial-workflow-v1/report.md),
configs/data/financial_workflow_v1.json, local mapping_review/readiness_v7/workflow_v4.
Financial features false/PIT NOT_READY; không thay approved score formulas,
availability policy hoặc market clustering protocol.

## ADR — Owner-approved DATE_ONLY financial PIT và issuer quarantine (03/10/2026)

Owner chấp thuận dùng ngày khi nguồn không có giờ và yêu cầu triển khai các giai
đoạn tiếp theo. Chọn exact-PDF publication DATE_ONLY cho daily/monthly; predicate
`decision_date >= usable_from_date`, usable_from_date là phiên exchange đầu tiên
sau ngày công bố theo C8 observed calendar, timezone policy Asia/Ho_Chi_Minh.
Source timestamp/timezone và legacy available_at vẫn null; không dựng timestamp
hoặc dùng cùng ngày. Đây là date overlay riêng, chưa nối feature registry consumers.
Calendar observed union không chứng nhận authoritative sessions; thiếu exchange/
ngoài coverage fail-closed. Giữ các bản riêng, as-of không backfill; cùng ngày khác
value/unit unresolved. Thiếu giờ không còn blocker date-PIT. Approved rule này thay
yêu cầu publication-hour trong financial evidence v1 cho daily/monthly, không mở
research/financial feature gates hoặc thay F/M/Z/valuation definitions.

Publication phải explicit website disclosure statement hoặc source-linked listing,
khớp exact PDF hash. FPT cover dates 2019–2025, PVS 2024/25 và ACV 2025 đã review;
không inherit cho annual-report PDF khác hoặc mọi revision. Candidate ACV2022
hash 398a9f8668e229bbaa8d86698f2b2696c034a2de83dc45b2b10d912f348460bd là VEAM:
quarantine exact hash sau evidence integrity checks, giữ raw, không reject toàn năm.

Policy: [date-PIT v1](../configs/data/financial_date_pit_v1.json),
[evidence v2](../configs/data/financial_evidence_policy_v2.json).
[Report](../artifacts/reports/financial-date-pit-v1/report.md): 139 value cells,
124 date cells, Z2024/25 và EPS2021–25 đủ date input coverage; joint vintage,
semantics, identity/sector, TTM/share basis còn riêng. FIN-D2/3/4 PARTIAL, D5 pending.

## ADR — Executable FPT EPS/Z reference slice (03/10/2026)

Owner yêu cầu chạy giai đoạn tiếp để hoàn thiện flow. Chọn hai original audited
FPT2024/25 đã có verified facts/publication làm calibration cohort. OCR parser
chọn ô bằng row code/current-year column hoặc reviewed note rectangle; không dùng
reference value để chọn token. So với evidence đã review, same-PDF/units/period,
accounting bridges rồi mới Decimal-calculation theo frozen EPS/EM-Z formulas.
Reference registry riêng cluster_eligible=false; không thêm financial vào M2.

Đây là offline cache replay, chưa unattended unseen-PDF parser. Ground truth và
semantics vẫn được review trực quan; zero review queue không chứng nhận accuracy
ngoài 22 ô calibration. Acquisition/render/OCR upstream giữ nguyên/cached.
Known EPS2024 restatement trong original2025 page55 được gắn exact hash/date:
chặn dùng old original EPS từ phiên 20/03/2026 khi comparative share-basis mapping
chưa được nghiệm thu. Không backfill revised EPS về 17/03/2025.

[Config](../configs/data/financial_reference_flow_v1.json),
[report](../artifacts/reports/financial-reference-flow-v1/report.md), reference_flow_v6.
EPS2024/25 và Z2024/25 có reference outputs; F/M/PE/PB missing/unsupported rõ ràng.
FIN-D2 tổng thể PARTIAL; financial_features_allowed/research_ready vẫn false.

## ADR — EPS comparative revision và F-score partial signals (03/10/2026)

Owner yêu cầu triển khai bước tiếp theo. Giữ strict F-score earnings definition;
VAS net profit và other income chưa có reconciliation nên không tạo proxy hoặc
partial total. Chốt nợ F-score theo original maturity: loan + finance lease,
đã gồm current portion, không cộng lại current borrowings. Scope này không tự
áp cho Beneish LEVI. Parent issuance indicator có unit INDICATOR, 1 là actual
issuance đã verified, 0 là verified absence; missing vẫn null. ESOP của công ty
mẹ làm no-issuance signal bằng 0; stock dividend/NCI capital không thay thế.

EPS2024 restated thuộc fiscal year2024 nhưng publication exact original2025 PDF
19/03/2026, dùng từ 20/03/2026. Numerator 7.231.780.632.599 VND không đổi;
denominator 1.462.653.544 + 222.176.999 = 1.684.830.543 shares. Revised diluted
denominator nối original FY2024 explicit no-dilution note với cùng bonus-share
adjustment; lineage/hash của cả hai PDF giữ nguyên. Chọn latest eligible date
reference và exact reviewed template, không sửa snapshot cũ hoặc backfill.

[Config v2](../configs/data/financial_reference_flow_v2.json),
[report](../artifacts/reports/financial-revision-fscore-v1/report.md): FPT2024/25
EPS revision reference PASS; F-score 6/9 signals, total null. Reference registry
riêng; chưa production acceptance hoặc mở scale. Việc đổi strict earnings sang
VAS net-profit adaptation là methodology change riêng cần review cụ thể.

## ADR — Structured candidates và explicit VAS references (03/10/2026)

Owner yêu cầu hoàn thiện data/tính chỉ số, research project và nguồn khác. Chọn
bounded KBS public candidates và exact issuer PDF notes/publication. VCI403
hard-stop, không workaround. Provider dates không thành PIT; monetary unit1000
là candidate, tolerance500VND chỉ rounding QA; EPS giữ unit/revision exceptions.

Tạo riêng PIOTROSKI_VAS_REPORTED_NET_PROFIT_REFERENCE với reported consolidated
net profit; giữ assets/debt/issuance definitions, canonical strict ordinary-income
field vẫnnull. BENEISH_2013_VAS_REPORTED_PROFIT_OWNED_PPE_SENSITIVITY dùng gross
short trade receivables, owned-only PPE/depreciation, CL+noncurrent loan/lease và
reported profit. Four allowance-allocation scenarios là conditional sensitivity,
không strict bounds hoặc classification threshold. Không thay original score.

Reported valuation dùng raw_close VND/share, exact12-month FY2025 EPS và same-date
parent common equity/outstanding common shares; không weighted shares cho BVPS.
Event coverage/historical identity còn pending. H12026 EPS explicit6-month,
không annualize/sum quarterlyEPS; reserve chưa ước tính không thành zero.
FTEL scope change và TT99/TT43 presentation trong PDF cần bridge cho latestTTM.

Named variants chỉ research reference theo owner scope; production promotion vẫn
MANUAL_REVIEW_REQUIRED, registry riêng clustereligiblefalse. Final runs v4/v5
identical, strict task matrix vẫn0/120 và full-universe chưa mở.
[Config](../configs/data/financial_source_completion_v3.json),
[report](../artifacts/reports/financial-source-research-v1/report.md).

Review correction: CFO2024 đúng11.703.777.188.868 và noncurrent loan/lease2024
đúng501.115.537.075 VND. Hai giá trị cũ chép sai được exclude bằng exact identity/
PDF hash/incorrect value; artifacts gốc giữ nguyên. Đây là transcription correction,
không corporate restatement hoặc source priority; publication date không đổi.
CFO+CFI+CFF=net cash change và noncurrent-liability component sum PASS. Readiness
v12/datev6/taskv8/workflowv8 dùng correction run, strict gates không đổi.

## ADR — Reported-numerator TTM và issuer share-event ledger (04/10/2026)

Owner yêu cầu bước financial tiếp theo. Thực hiện một stage FPT TTM/valuation
reference, chưa scale full universe. Ghép reported numerators và calendar share-days
trên disclosed bonus-adjusted basis; không ghép rounded EPS. H1 chưa estimate welfare
reserve không thành verified zero, normalized TTM vẫn null. FTEL statement và H1
comparison chỉ bridge parent earnings/EPS, không bridge revenue/total-NI cho strict F/M.

ESOP2026 cùng common count 1.714.326.422 nhưng issuance/charter/accounting dates
khác nhau. Latest Aug24/28 có reviewed after-event evidence; historical interval
phải block thay vì chọn source priority. Approved plan không actual issuance;
snapshot đã gồm 2025 events không cộng lại. P/B reference dùng current shares/latest
reported equity, disclose book date và post-balance issuance; chưa pro-forma claim.
381,75B internal capital transfer không ESOP cash; dividend reflected không trừ lại.
Production promotion vẫn MANUAL_REVIEW_REQUIRED, gates false. Market-only M2 protocol
và raw/canonical artifacts không đổi. [Config](../configs/data/financial_fpt_ttm_valuation_v1.json),
[report](../artifacts/reports/financial-ttm-valuation-v1/report.md).

## ADR — FPT metric contract và gross ESOP capital bridge (04/10/2026)

Owner yêu cầu tiến hành stage tiếp theo. Chốt reference contract có sáu families,
giữ named VAS F, M sensitivity, EM Z và reported-numerator TTM đã review; không
alias strict fields hoặc áp threshold fraud/distress. Literature matrix B6/B7
hỗ trợ firm characteristics, không chứng minh VAS mappings của F/M/Z; primary
score definitions trong financial contract vẫn là căn cứ công thức.

Hai bank attachments xác nhận 23.020.000.000 + 85.173.010.000 = 108.193.010.000 VND.
Thông báo đăng ký doanh nghiệp xác nhận gross capital increment này hiệu lực
16/07, công bố 17/07; không biến ngày đăng ký vốn thành ngày mọi share event.
Giữ historical common-share effective interval unresolved, không backfill.

Chọn `GROSS_ESOP_CAPITAL_BRIDGE_PB_REFERENCE`: reported consolidated parent equity
30/06 + verified registered capital increase. Đây là gross contribution reference;
phí chưa xác minh, cash classification tại balance date, subsequent earnings và
complete event coverage không được coi là zero. Assets/liability deltas giữ null;
không suy khoản ESOP nằm trong aggregate other payables. BCTC riêng chỉ hỗ trợ
discovery vốn/phải trả, không thay consolidated parent equity. Strict P/B vẫn null.

Acceptance xuất từng basis/period/provenance và hai mức calculation/production.
Sáu reference values không đồng nghĩa sáu production-ready tasks; date-PIT policy,
strict task matrix và market-only protocol giữ nguyên. Production promotion vẫn
`MANUAL_REVIEW_REQUIRED`; FPT reference stage bàn giao, pilot ba mã còn pending.
[Config](../configs/data/financial_fpt_acceptance_v1.json),
[report](../artifacts/reports/financial-fpt-acceptance-v2/report.md).

## ADR — Bounded VNM/PVS/ACV financial reference pilot (05/10/2026)

Owner yêu cầu triển khai và giữ report/log. Chốt một stage pilot annual 2025 trên
ba mã; giữ FIN-D1→FIN-D5 và không thay market-only protocol của nhóm khác. Chỉ
visual-reviewed exact PDF/image cells vào slice riêng; raw OCR/provider candidates
không tự nghiệm thu. Runner pin source/PDF/image/calculation hashes và replay offline.

Disclosed basic EPS được tính độc lập khi numerator/weighted basic shares đủ;
unknown diluted denominator và reserve chưa estimate giữ null. ACV dùng reported
EPS numerator loại KCHTHK/airport security, không alias total parent NI.
P/E/P/B annual dùng 2025 EPS/common-share book snapshot với raw close 28/08; không
gọi current TTM/event-adjusted valuation. Hai quote pages bổ sung lưu financial
reference riêng, không thêm vào market canonical.

VNM current/prior H1 parent earnings, reserve và weighted shares khớp exact 2025
note; source numeric TTM prior là comparative trong H1 2026, chỉ biết từ release
2026. FY2025 và H1 2026 dùng exact-attachment publication mirror, gắn quality
MIRRORED_EXCHANGE_DATE_REFERENCE_PRIMARY_PENDING; không nâng thành primary PIT.
TTM dùng reported numerators/share-days, normalized allocation và production null.
PVS parent H1 thay đổi từ 690.128.896.555 thành 687.363.021.076, reserve và bonus
share basis cũng revised; không ghép FY cũ mà chưa có earnings/share bridge.
ACV reviewed H1 release 03/09 không được backfill vào cutoff 28/08.

17/18 annual arithmetic cells không phải 94% project progress hoặc production
acceptance; VNM F total null, ACV/VNM auxiliary dates pending. Strict F/M và
full-universe/research vẫn fail-closed, promotion MANUAL_REVIEW_REQUIRED.
[Config](../configs/data/financial_three_symbol_pilot_v3.json),
[report/log](../artifacts/reports/financial-three-symbol-pilot-v1/report.md).

## Financial batch checkpoint/resume và engineering gate — 05/10/2026

Owner yêu cầu triển khai các bước tới khi có flow ổn định để scale và ghi report.
Cho phép batch engineering10 mã FY2025 với candidate-only discovery/extraction;
không lấy đó làm approval financial methodology hoặc accepted-data full-universe.
Runner nối exact-URL frozen cache, immutable task checkpoints, embedded text,
bounded scan-prefix OCR, review queue và hai reviewed offline pilot adapters.
Checkpoint kết thúc task có manifest riêng; resume interrupted parent bỏ unsealed
files, sealed parent lần theo exact external receipt/manifest từ run gần nhất.
Verifier kiểm transitive raw/text/image hashes, JSONL và reference artifacts.

403/429/challenge giữ hard boundary cả qua deferred→resume nhiều lượt. Không tự
retry access boundary hoặc redirect. Transport failures có retry hữu hạn;404 không
retry/bẻ URL. DGC official PDF là candidate discovery độc lập sau URL CafeF404,
không source priority hoặc value/PIT acceptance. Config source-resolution pin cả
HTML/attachment và failed lineage; không suy publication từ tên file.

Cache epoch biểu thị frozen discovery snapshot. Refresh phải có epoch/run mới và
giữ mọi vintage; không dùng cached latest hoặc ticker hiện tại như PIT/identity.
Extraction fingerprint gồm code/tool/OCR script; đổi code có thể tạo extraction
mới nhưng không tăng unique coverage. OCR prefix không đầy đủ notes và không có
automatic numeric acceptance. Missing giữ null; annual/TTM/book-date basis riêng.

Engineering COMPLETE10 mã và replay0 network/text/OCR mới chỉ mở sử dụng runner
bounded cho acquisition/extraction/review assistance. Accepted facts scale cần
pilot closure, ground-truth parser QA từng template, thresholds review độc lập và
cost/exception evidence từ batch20–30; không tự đặt threshold để làm pass.
Financial clustering cần approved feature subset, exact availability/revisions,
historical identity/sector,≥3 năm usable history và financial protocol riêng.
Production variants tiếp tục MANUAL_REVIEW_REQUIRED. Không sửa M2 market-only,
feature/research/full-universe flags vẫn false; numeric coverage pilot không tăng.
[Report và log](../artifacts/reports/financial-batch-flow-v1/report.md),
[config active](../configs/data/financial_batch_flow_v6.json),
[execution plan v8](../configs/data/financial_execution_plan_v8.json).
# Financial crawler user v1 — 06/10/2026

- Thêm điểm chạy portable nối acquisition candidates và PDF evidence, tối đa10 mã
  pilot. Không thay source/canonical/PIT/feature/market-only acceptance policy.
- Structured source KBS theo probes có evidence; request giữ annual/quarter/page/unit.
  Report/sector crosswalk chỉ tạo candidate. Duplicate period headers không cấp target
  coverage. Metadata provider và fetched_at không được chuyển thành publication.
- PDF template có hash chính xác; OCR page selection tường minh. Reference QA và
  A=L+E arithmetic không cấp financial acceptance; missing/conflicts giữ reason.
- Network flag, budget, hard-stop/resume latch và immutable manifests giữ nguyên.
  Full-universe/financial cluster cần acceptance policy và protocol riêng trước khi mở.
# Financial bounded trial50 — 06/10/2026

Owner yêu cầu triển khai flow/script PowerShell để tự chạy50 mã local và trả feedback.
Tạo trial contract riêng `financial-crawl-trial-v1`, giữ runner pilot tối đa10 và
financial/research/cluster/full-universe gates đóng. Pin plan membership50 vào market
snapshot; global budget/ledger và access latch giữ qua waves/resume, epoch registry
không cho fresh run reset counter. Không chạy full-universe bằng independent batches.

Annual target2021–2025 (thêm2021 làm asset denominator comparator cho F-score2023),
quarter2024–2025 và strict dependency checklist2023–2025. Đây là acquisition targets,
không thay score variants. Provider Regular header chỉ cấp candidate crosswalk,
historical sector và numeric facts vẫn chưa nghiệm thu. PDF text chạy worker có
deadline; scan pages tạo queue, selected numeric OCR không tự generalize FPT template.
Flow không tự mở100 mã; cần review engineering, independent template QA và cost từ
feedback. Runbook: [trial50](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md).

## Financial paired source review và cold retention — 08/10/2026

Owner yêu cầu benchmark KBS với CafeF và clean financial data sau nhiều lượt chạy.
So sánh engineering9 mã, cùng annual2021–2025/quarter2024–2025 trên4 pilot và
FY2025/Q42025 trên5 diversity controls. Wire header presence, numeric PDF-reference
QA, latency/requests và parser cost là các phép đo riêng; không suy coverage từ
requested page hoặc numeric accuracy từ A=L+E. `pageSize=1` thử theo implementation
Vnstock, nhưng live data còn cross-year signatures; không tự đảo/relabel kỳ.

Recommendation engineering là CafeF detail primary candidate, KBS diagnostic pending
header/value QA. Đây không phải approved canonical source priority hoặc automatic
fallback; giữ conflicts/missing/scope-vintage unknown và exact PDF notes/publication/
revision/event evidence. Mẫu9 mã/một lượt không chứng minh full-universe uptime hay PIT.
Runner legacy50/config cũ chưa chuyển nguồn; thay flow là stage kế tiếp. Score variants,
DATE_ONLY policy, market-only protocol và financial/cluster/research flags không đổi.

Theo explicit cleanup request, archive inactive financial roots bằng ZIP có SHA256
từng file và whole-archive pin; kiểm source bytes trước native PowerShell pruning.
Giữ active execution-plan transitive closure, cả Windows escaped paths; refresh closure
ngay trước prune để không gỡ input mới active. Không sửa sealed reports/manifests/raw;
restore tái tạo exact bytes ở path gốc, từ chối overwrite/tampered archives. Registry
epoch của closed trial50 còn local; raw trial cold-archived, verify cần restore trước,
deadline/counters không reset. Chỉ nhận invariant của archive khi verifier PASS.
[Report](../artifacts/reports/financial-source-benchmark-v1/report.md),
[runbook](crawl/README.md#financial-source-benchmark-và-retention--08102026).

## Financial trial50 reviewed integration — 08/10/2026

Stage nối reference dùng existing variants/calculators và DATE_ONLY policy đã owner
duyệt; không thay phương pháp score hoặc mở research/cluster gates. Candidate-only
strict readiness không đại diện cho reference arithmetic coverage. Assessment chỉ
nối metric/provenance vào cohort, không gán publication hoặc accepted values cho
HTML theo ticker/year. Annual task-year, TTM EPS/PE và equity-event PB có ledger
riêng; controls VNM/PVS ngoài50 không tăng denominator coverage. Unknown giữnull;
reference values không tự thỏa strict original task inputs. ACV thiếu auxiliary
publication được giữ partial dù có annual arithmetic.

Active retention đọc thêm versioned financial_active_integration_v1 config cùng
execution plan v9, bảo vệ integration và transitive dependencies. Không sửa sealed
runs để cải thiện0/900 cũ; không thay five-stage plan/market-only workstream.
[Report](../artifacts/reports/cafef-financial-reviewed-integration-v1/report.md),
[runbook](crawl/README.md#nối-trial50-với-reviewed-references--08102026).
## Financial scale diagnostics và reviewed reference — 08/10/2026

Stage mới kiểm frozen50 và4 mã ngoài FPT/ACV; configs `financial_scale_probe_v1`,
`financial_scale_ocr_v1`, `financial_scale_review_v1` giữ closed gates. Provider-only
Z (EBT+code23), printed EPS và annual PE là diagnostic, không tự thành accepted fact.
Review phải giữ exact PDF hash/current-prior columns/unit/scope/fiscal period và
comparative vintage. Combined lãi vay/phí phát hành cần note tách trước EBIT reference;
không dùng numerical match để bỏ qua semantic mismatch. PDF scan dùng code render/OCR,
ambiguous tokens giữnull; visual transcription có locator/pins và chỉreference-only.
DATE_ONLY policy đã duyệt tiếp tục áp dụng; thiếu ngày công bố đúng vintage không thay
bằng ngày ký/audit/file. SLS noncalendar/SHSstandalone không relabel để vượt gate.
Không thay formulas, source-priority, strict feature/PIT/research acceptance hoặc
five-stage plan. Unattended acceptance/financial cluster vẫnMANUAL_REVIEW_REQUIRED.
[Evidence/report](../artifacts/reports/financial-scale-validation50-v1/report.md).



## Financial local user workflow frozen50 — 2026-10-08

Đóng gói operational handoff cho owner chạy local, không đổi five-stage plan hoặc market-only. V1 đo FY2025 trên50 mã (300 task cells), acquire annual2023–2025 cho history/comparatives; mẫu số300 không thay checklist900 đã frozen. Snapshot giá/calendar vẫn28/08/2026.

Workflow dùng immutable frozen pins/receipts/reports, cumulative transport counters và global boundary/budget latch; OCR page reservations tính cả attempt gián đoạn. Local batch giới hạn, cache đúngURL/hash, không re-request known source failures hoặc bypass challenge. Reviewed facts có PDF/page/units/vintage/reviewer và exact publication per source; calculator output là reference, không canonical promotion/source priority.

PE TTM/PB với basis khác giữ ledger riêng; bulk wrapper chưa tự chốt TTM/event coverage. Sector/fiscal exceptions không ép Regular. Supporting comparative source thiếu ngày công bố làm metric đó PIT-pending; không copy ngày main PDF. Gates financial/cluster/research/full-universe/next100 giữfalse. Runbook ở `docs/crawl/FINANCIAL_READINESS_USER_GUIDE.md`, evidence ở `artifacts/reports/financial-user-workflow50-v2/`.
