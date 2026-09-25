# Các quyết định còn hiệu lực

Cập nhật 24/09/2026. Git history giữ thảo luận cũ; file này chỉ chứa quyết định đang ràng buộc implementation.

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

## Open decisions

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
