# Các quyết định còn hiệu lực

Cập nhật 16/09/2026. Git history giữ thảo luận cũ; file này chỉ chứa quyết định đang ràng buộc implementation.

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
| ADR-020 | Active feature snapshot 1.4 không sinh Sharpe. Snapshot 1.3 chỉ đọc qua explicit legacy compatibility; Sharpe tiếp tục ở portfolio metrics. |
| ADR-021 | M2 configs mặc định `portfolio_evaluation.enabled=false`; chỉ M3/frozen protocol được bật backtest/performance. |
| ADR-022 | `shares_history` là optional canonical input với key `security_id + effective_date`; share counts khác nhau không bị giả định bằng nhau và current count không được backfill về lịch sử. |
| ADR-023 | Market cap, valuation ratios và F/M/Z scores là derived/versioned analytics; vendor ratio chỉ để đối chiếu. EPS cần weighted-average shares hoặc documented vendor basis. |
| ADR-024 | **Research/demo collection under accepted provider-rights uncertainty:** dùng public CafeF/KBS paths cho bounded private academic research/demo theo `ACCEPTED_RESEARCH_RISK`; provider rights vẫn `RIGHTS_NOT_VERIFIED`, không bypass access control, không raw redistribution, financial chỉ `RAW_ONLY_PIT_UNRESOLVED`, và production/commercial vẫn licensed-source-only. Owner quyết định ngày 16/09/2026; ảnh hưởng source adapters, smoke config/tests và risk policy. |
| ADR-025 | **SOURCE_SMOKE anomaly policy và gate:** provider-corrupt market row chỉ được exclude khi provider/symbol/date/raw fields khớp exact versioned evidence; raw/finding luôn giữ, không repair/backfill. Cross-source volume khác semantic phải giữ riêng, không giả định equality. Direct KBS HTTP ghi `acquisition_client=delta_public_http`, Vnstock chỉ là discovery provenance. Chỉ machine gate PASS mới unlock `REPRESENTATIVE_PILOT`. |
| ADR-026 | **REPRESENTATIVE_PILOT path alignment và financial-track separation:** official pilot dùng KBS direct HTTP + CafeF direct như SOURCE_SMOKE; Vnstock SDK chỉ legacy. Market pilot không đòi PIT-ready financial; `PIT_UNRESOLVED` bắt buộc `financial_features_allowed=false`. Cross-source volume unresolved giữ source-qualified, không merge. |

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

Quyết định mới ghi: problem → alternatives → choice/reason → evidence → owner/date → affected contract/config/tests → remaining limits.

## ADR — Research/demo collection under accepted provider-rights uncertainty

Project owner quyết định dùng public CafeF/KBS paths cho bounded private academic research/demo. Provider rights vẫn `RIGHTS_NOT_VERIFIED`; execution label là `ACCEPTED_RESEARCH_RISK`. Không bypass access control, không raw redistribution, financial data chỉ `RAW_ONLY_PIT_UNRESOLVED`, và production/commercial vẫn chỉ dùng licensed/approved source. Quyết định ngày 16/09/2026; affected: source adapters, smoke config/tests và data-usage risk policy. Remaining limit: quyết định này không xác minh copyright, provider rights hoặc PIT timing.

## ADR — SOURCE_SMOKE anomaly resolution và executable gate

Problem: một CafeF row VNM có price band bất khả thi và KBS/CafeF ACV volume khác nhau nhưng không có bằng chứng unit/mapping error. Alternatives gồm sửa/điền row, ưu tiên một source, fail toàn smoke, hoặc áp policy evidence-bounded. Choice: exact raw-evidence match mới cho phép gắn `INVALID_REQUIRED_MARKET_ROW` và exclude khỏi CafeF constraint promotion; raw giữ nguyên, KBS cùng ngày không bị xóa. Volume khác semantic được source-qualify và giữ riêng. Direct public HTTP provenance được ghi đúng client; machine gate fail-closed và chỉ PASS mới unlock representative pilot. Evidence: canonical run `source-smoke-20260916T122331Z-79427ec6`, gate/hash manifest và unit tests. Owner/date: project owner, 16/09/2026. Affected: source adapters, smoke config/runner, planning gate, tests, manifest. Remaining limits: rights vẫn chưa xác minh, corporate action còn partial, shares chỉ current snapshot, financial PIT unresolved; quyết định không mở M1/extended scale.

## ADR — REPRESENTATIVE_PILOT source alignment và financial separation

Problem: legacy pilot dùng Vnstock SDK khác với acquisition path đã smoke-validate; gate cũ cũng biến financial PIT thành market blocker và classifier ACV overclaim semantic từ approximate ratio. Choice: official pilot chỉ dùng KBS direct HTTP (`delta_public_http`, discovered via Vnstock) và CafeF direct; SDK path giữ legacy <=5-symbol reference only. Market gate tách financial track: `PIT_UNRESOLVED` không chặn market collection nhưng luôn khóa financial features/historical analytics. Volume chỉ nhận `MATCHED`/`TOTAL` bằng exact equality hoặc `OTHER_DOCUMENTED_SEMANTIC` bằng mapping rõ; còn lại `UNRESOLVED`, source-qualified và unmerged. Evidence: canonical smoke run, zero-network dry-run, config/universe contracts và targeted tests. Owner/date: project owner, 16/09/2026. Affected: pilot runner/config/schema, planning gate, source classifier, docs/tests. Limits: rights vẫn chưa verified; M1 scale chưa chạy.

## ADR — Representative pilot primary/reference coverage và exact-hash QC

Real run `representative-pilot-20260916T185530Z-410ffcba` cho thấy KBS có >=5 năm OHLCV cho 55/55 mã, trong khi CafeF direct trả non-empty nhưng source-truncated history cho 53 mã. Choice: KBS là primary market history/benchmark; CafeF là auxiliary limits/value/volume source được phép partial nhưng luôn source-qualified và không canonical-merge. Provider invariant violation chỉ được exclude nếu versioned policy khớp exact provider, ticker, trade date và raw-row SHA-256 trên đúng immutable run; thiếu/thừa/mismatch fail-closed. Offline replay phải verify mọi artifact checksum, không network và không mutate raw. Evidence: policy v1, assessment/gate và result report ngày 17/09/2026. `REPRESENTATIVE_PILOT=PASS` chỉ unlock planning M1 scale; financial PIT và production rights vẫn unresolved.
