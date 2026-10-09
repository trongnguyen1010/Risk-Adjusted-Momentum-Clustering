# Trạng thái hiện tại — M1 market foundation reported

Documentation09/10/2026: **FINANCIAL INDICATOR HANDBOOK COMPLETE**.
[Handbook](research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md), [report/self-review](../artifacts/reports/financial-indicators-handbook-v1/report.md). Đã gom6financial families, EPS/TTM/valuation variants,9Fsignals/8Mcomponents, data dictionary/nguồn/kỳ/notes/PIT/QA/code và11market features. Existing contract/source note/runbook đã có nền tảng nhưng chưa bảng tra cứu liền mạch. Ghi rõ M accruals dùngTAcuối năm trong code khác average-assets của paper; không đổi runtime/formula/inputs/gates. Documentation và synthetic arithmetic examples được kiểm offline; các entry dưới là tiến độ data trước đó.

Publication discovery MWG/VHC08/10/2026: **DISCOVERY COMPLETE / ACCEPTANCE PARTIAL**.
[Report/worklog/self-review](../artifacts/reports/financial-mwg-vhc-publication-review-v1/report.md). MWG official PostAPI liên kết BCTC FY2025 với23/03/2026 và FY2024 với24/03/2025; distinct PDF hashes, version association chưa accepted. FY2025 images/content/geometry46/46khớp, full fingerprint45/46 vì digital signature annotation; FY2024 official higher resolution chưa all-page equivalence. VHC2/2official PDFs khớp cache, chưa publication date. Giải trình30/03/2026 chỉ document date; landing-page date không được propagate. VHC notice No85 đề09/04/2025 nhưng explicit publication10/04/2025. Signed-at proxy chỉ là đề xuất reference riêng; runtime/DATE_ONLY/inputs/counters/gates không đổi. Latest references24/300, production0. Next: exact-version publication acceptance và VHC disclosure date; chưa date-overlay/crawl100.

Financial MWG/VHC F/M review08/10/2026: **REFERENCE CALCULATION COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Report/worklog/self-review](../artifacts/reports/financial-mwg-vhc-fm-review-v1/report.md). Full OCR101trang FY2024 cache, bổ sung26facts/mã vào v2 riêng; MWG F4/9/M−1,417454, VHC F7/9/M−2,863853; EPS/Z không đổi. Mỗi mã có4/6groups reference; latest cohort24/300FY2025cells(8%):EPS8/Z8/F4/M4/PE0/PB0,8/50symbols có ít nhất một reference.290pins/inventories và independent18Fsignals/16Mratios/8valuesPASS;23testsPASS/compilePASS. Provider50MATCH/22NO_PROVIDER/2VHC2024 signed-expense flags, canonical null. Exact-PDF publication FY2025+support FY2024 vẫn thiếu; human acceptance pending, all gatesfalse/production0.0acquisition requests/download mới; manual primary-web discovery riêng có candidate links chưa accepted. Exact-hash extraction selector là local bounded workaround, chưa production CLI scheduling. Next: publication/human/sign-basis acceptance rồi review DGC/GMD notes từ cache; không tự wave acquisition/100. Plan năm giai đoạn/market-only giữ nguyên; các entry dưới là lịch sử stage trước.

Financial MWG/VHC template review08/10/2026: **OFFLINE REFERENCE REVIEW COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Report/worklog](../artifacts/reports/financial-mwg-vhc-template-review-v1/report.md). User FullOcr46MWG/64VHCpages và tạo blank templates; agent đối chiếu18ảnh, điền11facts/mã trong input riêng, chạy4EPS/Z references. Latest FY2025 assessment20/300cells (EPS8/Z8/F2/M2),8/50symbols với ít nhất một reference. EPS printed rounding2/2, balance identities2/2, provider18MATCH/4NO_PROVIDER_FIELD; independent60pins/2reviewinventories/report PASS,23testsPASS/compilePASS. Không network/OCR mới; publication exact-PDF MWG/VHC thiếu, F/M còn chưa-review/history/semantics; tất cả gates đóng. VHC EPS current-vintage có caveat quỹ phúc lợi chưa duyệt; không gọi final-revision/TTM EPS.

Financial user run inspection08/10/2026: **INTEGRITY PASS / COLLECTION PARTIAL / NO NEW NUMERICAL REFERENCES**.
[Report](../artifacts/reports/financial-user-run50-review-v1/report.md), [runbook](crawl/FINANCIAL_READINESS_USER_GUIDE.md). User Run `data/financial/user_workflow50_v1`:150 listings,91PDF mới,109vintages;2025 cóPDF41/50mã,2024 có27/50,2023 chưa tải.44PDF failure jobs (28timeout/14live404/2known404),123pendingPDF jobs;229attempts/947,97MB,17PDFattempts còn lại. OCR4PDF DGC/GMD/64trang mới, không có review/calculation mới; baseline6mã/16ô FY2025 giữ nguyên. Acquisition routing/cache/recovery cần hoàn thiện; không sửa code/config đã frozen, không mở financial cluster.

Financial local user handoff08/10/2026: **WORKFLOW HANDOFF COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Runbook](crawl/FINANCIAL_READINESS_USER_GUIDE.md), [report/tests/self-review](../artifacts/reports/financial-user-workflow50-v2/report.md).
Một runner PowerShell/Python: doctor/plan/audit/acquire/extract/run/template/review/verify; frozen50, FY2025 task matrix300 ô, history2023–2025. Durable network counters/access latch, OS lock, bounded OCR, immutable receipts/reports và human-attested reference calculator EPS/Z/F/M. Handoff QA không network: dùng lại cache, OCR mới16 trang MWG, replay2 PHP references; không mở cluster hoặc gọi PE annual là TTM. Bulk TTM/PB/sector adapters còn gap.

Financial scale validation08/10/2026: **MEASUREMENT COMPLETE / ACCEPTANCE PARTIAL**.
[Report/log](../artifacts/reports/financial-scale-validation50-v1/report.md),
[50-symbol assessment](../artifacts/reports/financial-scale-validation50-v1/per-symbol.csv).
Đã kiểm50 annual listings:44 consolidated candidates,5 annual unlabeled,1 annual
listing gap.12 PDFs text-tested,11 predominantly scan/unreadable; code OCR294pages
cho4 mã mới. PHP/VCS/VEA/PAN tính8 EPS/Z references; PHP/PAN có DATE_ONLY exact-PDF
publication. Còn full F/M/TTM/PB, VCS/VEA publication, provider reconciliation,
scope/fiscal/sector layouts và unattended/resume integration.27/35 OCR statement
cells khớp visual review. Gates financial/cluster/research/next100 vẫnfalse.
Market-only và plan năm giai đoạn giữ nguyên; các đoạn dưới là kết quả stage trước.

Financial reference integration08/10/2026: **OFFLINE INTEGRATION COMPLETE / ACCEPTANCE PARTIAL**.
[Report/log](../artifacts/reports/cafef-financial-reviewed-integration-v1/report.md),
[config](../configs/data/financial_trial_integration_v1.json).15/900 ô annual có reference:
FPT9 ô2023–2025, ACV6 ô2025; thêm3 FPT TTM/valuation bridge values, tổng18 trong50.
VNM/PVS controls ngoài cohort. ACV có arithmetic nhưng thiếu auxiliary date-PIT và
TTM/event basis; không gọi6 metrics của ACV là production/PIT-ready. Strict0/900,
không accepted HTML facts mới, không network/PDF/OCR mới. Bước tiếp theo: review
notes/publication/vintage cho wave Regular PHP/VCS/VEA/PAN, đóng ACV/FPT gaps và
template10 mã financial-sector; chưa tự chạy wave/100 hoặc mở financial cluster.

Financial CafeF-first trial50,08/10/2026: **BOUNDED RUN COMPLETE / CANDIDATE DATA PARTIAL**.
[Report/log](../artifacts/reports/cafef-financial-trial50-v1/report.md),
[PowerShell active](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md). Đã thử đúng50/50 mã,
600 base +120 gap requests;588/600 base parse được,12 HTTP302 BVH giữ lỗi.
720 attempts/162.610.642 bytes,1.646/1.950 wire statement-periods (84,41%),
169.448 raw candidate cells gồm overlapping/out-of-target columns. QA reference
trong mẫu50 chỉ có FPT/ACV:29/30 matches,1 difference; không suy accuracy toàn50.
Journal/cache compact, sealed run verified;0 PDF/OCR mới,0 accepted facts và0/900
strict tasks-ready trong lượt này. Prior arithmetic reference pilot giữ lineage riêng.
Next: exact document/template QA cho gaps/units/scope/notes, publication/PIT/revisions/
share events và cost review trước100 mã. Giữ plan financial năm giai đoạn, market-only
workstream và tất cả financial/cluster/research/full-universe gates false.

Financial source review08/10/2026: **PAIRED BENCHMARK COMPLETED; SOURCE QA PARTIAL**.
[Report/log và cleanup](../artifacts/reports/financial-source-benchmark-v1/report.md),
[engineering selection](../configs/data/financial_source_selection_v1.json).
297 bounded attempts trên9 mã gồm6 KBS page12 diagnostics; CafeF164/186 kỳ-báo cáo
wire hiện diện, KBS98/186;78 so với213 requests MAIN. CafeF72/78 numeric reference
matches; KBS0/78 theo header,213 cross-year signature alerts không được relabel.
KBS JSON parse nhanh hơn nhưng chưa đủ QA kỳ/giá trị. CafeF cũng còn6 HTTP302 ở BVH,
16 wire gaps khác,5 numeric differences và1 unmapped cell. Reference matches không
phải PIT/production acceptance. Đề xuất CafeF-first cho flow mới; runner50 cũ chưa
đổi nguồn/tham số và không nên rerun nguyên config để giải quyết blockers này.
Next: adapter CafeF-first và gap queue, original-document QA cho units/scope/notes/
publication/revisions, rồi thử lại bounded50. Cold archives giữ exact bytes của run
cũ; active transitive reference inputs/reports và trial epoch registry còn local.
Market-only workstream và financial/cluster/research gates giữ nguyên.

Financial live trial50, 07/10/2026: **COLLECTION PARTIAL / ENGINEERING TARGETS NOT_MET**.
[Report kết quả/log](../artifacts/reports/financial-crawl-50-live-v1/report.md),
[runbook](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md). Đã thử50/50 mã,300/300 base responses
parse được;90 history responses thiếu Head. FY2025 có ba statement wire headers rõ
trên50 mã, Q4/2025 đạt0/50 vì duplicate headers.409 requests/113.538.490 bytes;
8 PDF/604 text pages,555 low-text pages,0OCR,0accepted facts,0/900 strict task-ready.
Next: đóng quý/history contract, numeric templates/ground truth, PIT/notes/events
và đo ledger/verify cost trước trial100. Market-only workstream giữ nguyên.

Lineage chuẩn bị: [implementation/testing report](../artifacts/reports/financial-crawl-50-flow-v1/report.md),
[planning report](../artifacts/reports/financial-crawl-50-plan-v1/report.md),
[plan50](../configs/data/financial_crawl_50_plan_v1.json). Reports cũ giữ nguyên trạng
thái tại thời điểm bàn giao. Financial/cluster/full-universe gates vẫn đóng.

Financial user crawler update 06/10/2026: [report/log](../artifacts/reports/financial-crawl-user-v1/report.md),
[hướng dẫn bàn giao](crawl/FINANCIAL_CRAWLER_USER_GUIDE.md), execution plan v9.
Runner mới không cần pilot artifacts: config mẫu chạy clean4 mã với12 structured
responses/4 PDF/343 text pages/1 selected OCR page. Batch10 mã có30 structured
responses/8.720 wire cells/2.180 target2025 cells; replay32 cache hits,0 network/
text/OCR/new checkpoints và exports byte-identical. Structured quarter FPT có
duplicate period columns,654 cells bị quarantine khỏi target coverage; raw giữ nguyên.
Discovery4 mã ghi hai CafeF404 FPT/VNM, exact issuer/mirror URLs trong config bàn giao.
Crawler handoff COMPLETE ở bounded candidate collection; mới0 accepted facts,
financial/cluster/full-universe gates vẫnfalse. Market-only workstream không thay đổi.

Financial automation update 05/10/2026: [report quá trình](../artifacts/reports/financial-batch-flow-v1/report.md),
[runbook](crawl/README.md), execution plan v8/config batch v6. Latest run
`batch_flow_v9_final`, replay v10:10 mã có10 PDF candidates,691 embedded-text pages,
32 unique prefix OCR pages. Acquisition/extraction/checkpoint/queue/reference adapters
đã nối thành runner; resume từ run gần nhất lần theo exact external receipt/manifest.
HTTP404 DGC được ghi lại; nguồn official discovery tạo candidate riêng, không source
priority/value acceptance. Intermediate replay v6 phát hiện resume lineage bug, đã
sửa và thêm regression test. Final replay0 network/text/OCR/new checkpoints;
hai reference adapters và queue tái lập.132 financial tests/compile/smoke PASS;
full301/302 PASS với frozen M2-PREP DECISIONS checksum error cũ.
Sáu mã mới chưa có numeric facts được nghiệm thu; four-symbol calculation coverage
giữ nguyên. OCR prefix không bao phủ thuyết minh. Engineering COMPLETE ở10 mã;
FIN-D5 acceptance/financial/research/full-universe gates vẫn pending/false.
Next: pilot semantic/PIT/TTM/event closure, ground-truth template parsers và batch
20–30 với acceptance/cost thresholds được review trước khi mở accepted-data scale.

Financial update 05/10/2026: [pilot ba mã/report và log](../artifacts/reports/financial-three-symbol-pilot-v1/report.md).
Latest `three_symbol_pilot_v3`/replay v4, execution plan v7. Có 158 annual facts được
visual review riêng; không cộng trực tiếp vào matrix v12. VNM/PVS/ACV có 5/6/6 annual
reference families với arithmetic. F VAS PVS=7, ACV=4; VNM 8/9 known signals, total null.
Ba mã có M sensitivity/Z/EPS annual; P/E/P/B dùng raw close 28/08 và annual 2025 snapshot,
không current TTM/book equity. VNM thêm reported TTM EPS≈4.727,57, P/E≈13,18;
annual và interim publication là mirrored-exchange DATE_ONLY, primary vẫn pending.
PVS H1 parent profit/bonus-share restatement chưa có FY bridge; ACV reviewed H1 công bố
03/09 là future tại cutoff 28/08, bản Q2 unaudited đã tải nhưng EPS scope chưa nghiệm thu.
Auxiliary publication dates VNM/ACV còn thiếu. Quotes VNM/PVS lưu riêng dưới financial,
không sửa canonical market/M2. FIN-D4 annual reference slice hoàn thành, acceptance PARTIAL;
FIN-D5 pending. Strict tasks 0/120; financial/research/full-universe gates false.

Financial update 04/10/2026: [FPT acceptance/ESOP report](../artifacts/reports/financial-fpt-acceptance-v2/report.md).
Latest acceptance_v5, equity_review_v1 và execution plan v6: sáu metric families có
reference values từ 24/08/2026. F/M/Z dùng annual 2025; EPS/PE dùng TTM đến 30/06/2026;
P/B là latest June equity + verified gross ESOP capital increment, không current net equity.
Bank proceeds = registered capital increase = 108.193.010.000 VND; registration effective
16/07, công bố 17/07. Tại 28/08, gross-capital P/B ≈ 3,1404; previous reported-equity
P/B ≈ 3,1489 giữ riêng. Phí, cash classification và subsequent movements chưa đủ evidence.
FPT reference handoff complete; FIN-D4 four-symbol closure vẫn PARTIAL, FIN-D5 pending.
Không tăng readiness 153/1.176/date 138/task 0/120 hoặc mở financial/research/scale gates.
Các update bên dưới là lineage, không phải latest blockers đã được giải quyết.

Financial update 04/10/2026: [FPT TTM/share-event report](../artifacts/reports/financial-ttm-valuation-v1/report.md).
Latest supplemental slice: `fpt_ttm_valuation_v3`, execution plan v5.
14 issuer PDFs mới, 50 selected OCR pages; 6 accounting QA và 13 artifact checks PASS.
Reported-numerator/share-days TTM EPS ≈ 5.570,36 từ 24/08/2026; P/E/P/B reference
28/08 ≈ 13,14/3,15. P/B dùng current common count 1.714.326.422 và latest reported
parent equity 39.851.463.524.930 VND tại 30/06; chưa event-adjusted equity.
FTEL bridge chỉ đủ parent earnings; total-NI/revenue bridge chưa approved.
Interim reserve và historical issuance-date basis giữ blockers; strict normalized
TTM/event-adjusted P/B null. FIN-D4 PARTIAL_REFERENCE_TTM, FIN-D5 pending.
Readiness 153/date 138/task 0/120 không tăng vì slice riêng. Market-only protocol
và financial/research/scale gates giữ nguyên. Phần dưới là lineage các đợt trước.

Financial update 03/10/2026: [source research/VAS report](../artifacts/reports/financial-source-research-v1/report.md).
`source_completion_v5` là latest financial handoff. KBS trả15 JSON trên bốn mã;
4.796 wire cells chưa accepted. Thêm17 annual observations và13 H1 facts riêng;
readiness v12 đạt 153/1.176, date v6 có 138 date references; strict task v8 vẫn 0/120.
Hai transcription errors CFO/noncurrent debt 2024 đã có exact-PDF correction.
FPT2021–25 F-score VAS=4/6/6/7/3; strict F vẫn sáu known signals/totalnull.
M2024/25 có eight-ratio sensitivity, strictnull. Reported P/E/P/B20/03/2026≈14,30/3,48,
event coverage pending. H12026 EPS2.967 khả dụng24/08/2026; FTEL scope/reserve/share
bridge chặn latest TTM. EPS/Z flowv9 giữ revision handling. Các phần dưới là lineage
từng đợt. FIN-D2/3/4 PARTIAL, FIN-D5 pending; financial/research gates vẫnfalse.

## Lineage và phạm vi

Nhánh active: `m1-cafef-primary-experiment`.

Lineage trước R1: C7 `0fe5ddf724618a418331785e35c36e030cfc00ea` → C8 implementation `d60c8cba49c90b3b36c346dfea463a1e4f659ee1` → C8-VERIFY `e149198986345bb02610e53d8a330f641b89df22`. R1 chỉ hợp nhất repository; không thay methodology, dữ liệu hoặc kết quả C8.

Nguồn market active là CafeF `TradeHistoryNew`. `AdjustPrice × 1000` được dùng như `adj_close` với `adjustment_basis=vendor_adjusted`; không tuyên bố split-only hoặc total-return.

## Kết quả bất biến

C8 = `EXECUTED_AND_VERIFIED`. C8-VERIFY đã xác minh offline 19/19 output hash, upstream C5/C7/identity hashes và năm source ZIP. Không network request, supplemental acquisition, clustering hoặc backtest được thực hiện.

| Gate | Tổng | C5 baseline | C7 complete expansion |
|---|---:|---:|---:|
| Candidate | 952 | 500 | 452 |
| `feature_complete` | 922 | 490 | 432 |
| `market_feature_ready_v2` | 905 | 490 | 415 |
| `latest253_complete` | 922 | 490 | 432 |
| `latest253_incomplete` | 30 | 10 | 20 |
| `historical_identity_ready` | 0 | 0 | 0 |
| `research_ready` | 0 | 0 | 0 |

Tradability được báo riêng: 675 `ACTIVE`, 276 `OBSERVED_ZERO_VOLUME`, 1 `UNKNOWN`. 47 securities chưa market-ready. 148/600 expansion securities còn `DEFERRED_EXPANSION_ACQUISITION`.

Proposed `MARKET_ONLY_EXPERIMENTAL_UNIVERSE` có đúng 905 rows thỏa `market_feature_ready_v2=true`. Đây không phải final research universe, canonical production universe hoặc historically identity-verified universe. Zero volume là observation thật và không tự loại khỏi market readiness.

Cho M2-PREP, khái niệm cần freeze là `market_experiment_eligible(t) = market_feature_ready_v2(t)` theo từng snapshot. Con số 905 chỉ mô tả snapshot mới nhất `2026-08-28`; không được dùng như terminal-universe filter cho các tháng trước và không phải alias của legacy `eligibility` hay strict `research_ready`.

## Invariant còn hiệu lực

- Snapshot chung: `2026-08-28`; observation muộn hơn giữ làm evidence nhưng không vào feature/readiness.
- Không ffill, bfill, interpolate, missing-to-zero, synthetic OHLC/return hoặc timeline compression.
- Null activity component làm total tương ứng null; không zero-fill.
- Full-history audit và latest-253 audit độc lập.
- Non-authoritative calendar gap giữ `CALENDAR_UNCERTAIN`; không đổi thành confirmed missing.
- Historical identity và financial PIT vẫn fail-closed; không promote trong R1.
- C8 baseline tái lập C5, security-level readiness diff rỗng.

Full-history status: 934 `INCOMPLETE`, 18 `UNCERTAIN_BOUNDARY`, 0 complete. Đây chủ yếu phản ánh conservative calendar/boundary evidence, không phủ định 905 market-ready rows.

## Repository sau R1

R1 bỏ 192 file planning/history/config/runner/module/test superseded khỏi active tree. Git history là archive; không tạo archive copy. Active tree giữ:

- C8 runner, C8 verifier, C8 config, C8 implementation/tests và compact verification artifact;
- C6 expansion + supplemental contracts/runners/consolidation để xử lý 148 deferred rows khi có stage riêng;
- CafeF source semantics, generic promotion/reconciliation và Product Layer;
- C5 builder vì C8 lineage/test vẫn phụ thuộc;
- minimal KBS/Vnstock compatibility path còn được generic integration dùng;
- machine-readable R1 artifact tại `artifacts/repository/r1-consolidation-v1/`.

Hai đường dẫn C1 cũ còn xuất hiện trong frozen C8 provenance/config hash fields chỉ là Git-history identifiers; chúng không phải active input path.

## M1-REPORT

Artifact `artifacts/reports/m1-market-foundation-v1/` và notebook
`notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb` là lớp report/inspection
offline trên evidence C8 đã verify. Report tái tính và assert toàn bộ headline,
feature coverage, source/exchange composition, 30 latest-253 incomplete rows,
47 market-readiness exclusions và 80 monthly snapshots từ `2020-01-31` đến
`2026-08-28`. Notebook chỉ đọc explicit immutable report directory; business
logic và integrity checks nằm trong generator.

Readiness theo tháng có các đoạn gián đoạn lớn và zero-readiness periods. M2-PREP phải giải thích chúng trước khi freeze development/validation windows; D1 chỉ ghi nhận evidence, không diễn giải nguyên nhân và không thay methodology.

**M1 MARKET DATA FOUNDATION: COMPLETE FOR MARKET-ONLY EXPERIMENT PREPARATION.**
Strict research gate vẫn `NOT READY`; `historical_identity_ready=0` và
`research_ready=0`.

## Kiểm chứng offline

```powershell
.venv\Scripts\python.exe scripts\build_m1_market_foundation_report.py --verify-existing
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

Không rerun `run_cafef_c8_complete_only.py` hoặc C8 verifier-generator để kiểm chứng artifact đã tồn tại. R1 exact-inventory verifier thuộc frozen R1 tree và đương nhiên không đại diện cho current tree sau M1/D1. Heavy artifact và năm ZIP phải giữ nguyên hash.

## M2-PREP

Artifact `artifacts/experiments/m2-prep-v1/` đã audit eligibility, 80 snapshot, implementation, feature/preprocessing, algorithms, metrics và literature mà không chạy clustering. Kết quả cuối là **`MANUAL_REVIEW_REQUIRED`**; không tạo `configs/experiments/m2_market_only_v1.json`.

Hai discontinuity hệ thống được giải thích từ evidence hiện có:

- `2023-05` đến `2023-10`: session `2023-05-15` có trong calendar của cả ba exchange nhưng thiếu VNINDEX row; strict `beta_126` làm toàn bộ cross-section chưa complete cho tới khi gap ra khỏi 126-return window. Phân loại: benchmark/calendar propagation, không phải clustering result.
- `2025-02` đến `2026-01`: canonical market có 0 equity price row ở open session `2025-02-03`; strict `mom_252` cần 253 real prices nên toàn bộ cross-section fail cho tới khi gap ra khỏi window. Không impute hoặc timeline-compress.

Latest snapshot vẫn tái lập đúng `market_experiment_eligible=905/952`, với membership tính độc lập ở từng tháng; historical identity và research readiness vẫn bằng 0.

## M2-PREP-REVIEW

Owner review ngày `2026-09-26` đã chấp thuận các đề xuất Protocol v1 trong
`docs/DELTA_UNIFIED_PROJECT_PLAN.md` làm input cho M2-R1:

- development `2023-11-30 → 2025-01-24`;
- sealed holdout `2026-02-27 → 2026-08-28`;
- minimum `120` eligible securities mỗi snapshot, thấp hơn thì skip với reason;
- đúng 8 market features của M1;
- không winsorize/clipping; RobustScaler theo snapshot là default và z-score là sensitivity;
- `k=2..8`, chọn một global `k` trên development bằng median Silhouette, tie-break bằng median Davies–Bouldin;
- PCA chỉ là comparator, component count được chọn trên development theo ngưỡng cumulative explained variance `>=90%` rồi freeze;
- C8 feature snapshot `1.6.0` là active M2 input contract, registry `1.5.0` giữ legacy compatibility;
- Dynamic Clustering vẫn `NOT APPROVED`; `portfolio_evaluation.enabled=false`.

Quyết định này giải quyết owner-review gate của M2-PREP nhưng không sửa artifact
`m2-prep-v1`, không tự tạo final config và không làm M2-R1 thành `PASS`. Artifact
M2-PREP tiếp tục giữ status lịch sử `MANUAL_REVIEW_REQUIRED`; stage active chuyển
sang M2-R1 để materialize quyết định thành contract có thể kiểm thử.

## Stage tiếp theo

### Nhánh financial độc lập — 2026-10-02

Owner giao market-only cho nhóm khác và yêu cầu session này triển khai financial
trong `SourceCode-CafeF`. Financial raw coverage pilot đã IMPLEMENTED/EXECUTED,
nhưng stage giữ **PARTIAL** vì coverage failures; không đánh dấu PIT resolved.
Runner: `scripts/run_cafef_financial_pilot.py`; config:
`configs/data/cafef_financial_pilot_v1.json`; collector:
`src/delta_t1/ingestion/cafef_financial.py`.

Evidence local `data/financial/cafef_raw_pilot_v1/run-20261002T155840Z-652f827b/`:
72 logical calls, 24 streams, exact hashes/offline replay PASS. FPT/VNM có 19/20
quý mỗi KQKD/CDKT (thiếu Q2-2024), PVS/ACV có 20/20. FPT/VNM/PVS có 5/5 năm;
ACV có 4/5 do annual page 2 overlap. LCTT không trả group ở summary cho cả bốn mã.
Period presence không chứng minh đủ đầu vào score. PIT NOT_READY; không canonical
financial, không bật financial features và không thay market artifacts/protocol.

Validation: 59 targeted CafeF tests PASS (gồm 9 financial tests); full suite chạy
177 tests có 176 PASS và 1 ERROR tại immutable M2-PREP verifier do
`docs/DECISIONS.md` có owner-review edits từ trước session (HEAD hash khớp frozen
manifest, working tree không khớp). Không rewrite historical manifest để làm PASS.
Compile và dry-run PASS. Self-review giữ null/zero, raw evidence, finite limits,
pagination failure, access stop và research isolation.

Financial update 03/10/2026: detail remediation acquisition và report COMPLETE;
historical financial readiness vẫn PARTIAL, PIT NOT_READY. 108 calls cho 88 detail
pages/20 document lists, 19.644 cell observations; annual presence 60/60,
quarterly presence 225/240. ACV annual 2021 recovered qua detail. Có PDF cho cả
11 unique quarterly gaps, nhưng chưa tự động trích toàn bộ scanned PDFs. Đã QA
45 PDF sample facts FPT/VNM, tìm được weighted shares và EPS version differences.
Private `analysis_v2` xuất CSV/candidate checklist và 1.047 numeric comparisons
khớp, không promote unit/scope/PIT. 69 targeted CafeF tests và compile PASS;
full suite snapshot 185 tests vẫn chỉ lỗi immutable M2-PREP docs hash đã biết.
[Report quá trình](../artifacts/reports/financial-remediation-v1/report.md).

Financial next stage: hoàn thiện document extraction/taxonomy và verified
fact-to-document vintage/timing trước canonical PIT hoặc calculators. Market
next stage bên dưới thuộc nhánh nhóm market-only.

Financial evidence update 03/10/2026: thêm 30 PDF và issuer listing; all-document
text index v2 có 41 PDF/3.101 trang, OCR v3 có 198 trang thuộc 11 gap documents.
Thêm 85 visual-validated observations, tổng 130 cùng evidence cũ; 10 arithmetic
checks PASS. Có CFO YTD evidence cho 11 gap periods và BS/IS Q2-2024 FPT/VNM,
nhưng không tự biến thành full quarter/PIT coverage. Annual document candidates
24/28 mã-năm 2019–2025; VNM 2019/2020/2021/2025 full VAS còn thiếu. Annual report
VNM 2025 tải được chứa IFRS tables và VAS audit extract, không đóng full-VAS gap.
Checklist 1.176 mục: 813 raw-present/55 missing/308 note-review-required.
[Report v2](../artifacts/reports/financial-remediation-v2/report.md) và
[financial contract](research/FINANCIAL_FEATURE_CONTRACT.md) là handoff hiện hành.
Financial targeted 30 tests PASS, compile/synthetic smoke PASS; full suite
197/198 PASS, một lỗi M2-PREP DECISIONS checksum đã biết. Stage PARTIAL,
financial_features_allowed=false; chưa canonical/score/backtest hoặc mở rộng universe.

Financial pilot closure update 03/10/2026: FPT annual core 2019–2025 đạt 49/49 ô
được visual-verified; OCR thêm 108 trang, tổng 306. Overlay hiện hành
`data/financial/pilot_readiness_v4` có 107 document-verified/PIT-pending, 713
raw-unverified, 302 note-review và 54 missing trên 1.176 ô. Giữ riêng số liệu
2020 reclassified và EPS 2024 restated; correction run sửa hai numerator về VND.
FPT có document inputs cho 4/9 nhóm F-Score mỗi năm 2021–2025, chưa tính signal.
Config `configs/data/financial_pilot_closure_v1.json`; [report hiện hành](../artifacts/reports/financial-pilot-closure-v1/report.md).
Stage PARTIAL; PIT NOT_READY. 5 tests mới/compile/synthetic smoke PASS;
full suite 202/203 PASS trước final unit/hash hardening, lỗi M2-PREP cũ không đổi.
Next financial stage: hoàn thiện FPT notes/mapping và publication-version
evidence; sau đó mở workflow sang ba mã pilot còn lại. Không crawl 1.000 mã.

Financial execution update 03/10/2026: [plan Section 26](DELTA_UNIFIED_PROJECT_PLAN.md)
đã được triển khai đợt đầu. FIN-D1 COMPLETE với `task_readiness_v3` 120 rows;
FIN-D2/3 PARTIAL, FIN-D4/5 pending. OCR thêm 352 trang, tổng 658; review thêm
82 observations EPS/PPE/debt/expense/shares. Bảy annual EPS rounding checks PASS;
FPT EPS recompute có annual input presence 2021–2025 đạt 5/5, chưa compatible
vintage/PIT acceptance. FPT core vẫn 49/49, F-Score presence vẫn 4/9 nhóm mỗi năm.
Overlay hiện hành `pilot_readiness_v6`: 133 document-verified/PIT-pending, 703 raw,
286 note-review, 54 missing trên 1.176 cells. Thu issuer HTML và original audited
FPT 2025 PDF: exact attachment/date 19/03/2026, DATE_ONLY, available_at null;
không gán publication này cho annual-report vintage. 21 targeted tests, compile,
synthetic smoke PASS; full suite trước final instant-field extension 208/209 PASS,
còn lỗi M2-PREP frozen DECISIONS checksum đã biết. Exact inventory/PDF/image hashes
PASS. [Execution report](../artifacts/reports/financial-execution-v1/report.md),
config `configs/data/financial_execution_plan_v1.json`; features false, PIT NOT_READY.
Next financial stage: nghiệm thu FPT notes/mappings và publication history, sau
đó xử lý ba mã pilot còn lại, full VAS VNM và quarter/TTM trước expansion.

**M2-R1 — PROTOCOL FREEZE v1**: tạo `configs/experiments/m2_market_only_v1.json`, ADR/decision artifact, validation và tests cho toàn bộ quyết định Protocol v1 đã được owner review. Không chạy real clustering, không mở holdout, không sửa market-only runner/input adapter và không mutate C8/M1/M2-PREP evidence. Sau khi M2-R1 PASS, exact next stage là **M2-R2 — MARKET-ONLY RUNNER ADAPTER**.

### Financial FIN-D2 continuation — 03/10/2026

Handoff hiện hành: [workflow runbook](crawl/README.md),
[report](../artifacts/reports/financial-workflow-v1/report.md).
Thêm 40 observations, 7 accounting QA records PASS; overlay pilot_readiness_v7 có
135 document-verified/PIT-pending, 703 raw, 284 note-review và 54 missing.
FPT Z annual input presence 2024–2025 đạt 7/7 sau EBIT reconciliation;
EPS 2021–2025 giữ 3/3, mọi task_ready false/computed_value null. Workflow_v4 có
1.224 unique field-year cells, 140 external requirements; reuse 460 OCR pages và
27 annual PDF candidates. VNM full-VAS gaps giữ riêng, không coi candidate đủ scope.
22 financial targeted tests/compile/synthetic smoke PASS; full suite 211/212 PASS
trước final framework-gap/cap hardening, lỗi M2-PREP frozen DECISIONS checksum cũ.
FIN-D2 PARTIAL/PIT NOT_READY; chưa unattended multi-symbol full-universe pipeline.
Next: đóng ordinary-income/debt/PPE/net-receivables/issuance/common-equity mappings
và accounting QA theo vintage, rồi publication/quarters/TTM và pilot closure.
Owner thông báo nhóm market đã bắt đầu cluster; workstream này chỉ xử lý financial,
không audit/certify lại tiến độ clustering hoặc thay market methodology.

### Financial date-PIT handoff hiện hành — 03/10/2026

[Report hiện hành](../artifacts/reports/financial-date-pit-v1/report.md) thay handoff
financial v7 bên trên. Owner đã duyệt dùng ngày: từ phiên exchange quan sát được
đầu tiên sau publication_date; thiếu giờ không còn chặn date-PIT daily/monthly.
10 exact PDFs có publication evidence; 11 prefix exceptions chưa đóng. Phát hiện
ACV2022 candidate là VEAM và loại đúng hash, giữ raw/candidate ACV2022 khác.
Latest pilot_readiness_v10: 139 verified/699 raw/284 note/54 missing trên 1.176 ô;
date_pit_v4: 124 cells có exact-vintage date references. FPT 139/294 value và
124/294 date cells; Z2024–25 7/7, EPS2021–25 3/3 value/date inputs. Chưa score
acceptance: task_readiness_v6 giữ 120 task_ready=false. Workflow_v6: 1.224 cells,
140 external requirements, 26 PDF candidates, 488 OCR pages reused.
28 targeted tests/compile/synthetic smoke PASS; full 217/218 PASS, lỗi M2-PREP
immutable DECISIONS checksum cũ. FIN-D2/3/4 PARTIAL, FIN-D5 pending. Calendar observed
không authoritative; chưa unattended full-universe financial pipeline.
Next: đóng FPT semantic/joint-vintage QA, revision/publication exceptions, statements
ba mã còn lại/full VAS VNM, quarters/YTD/TTM/share events, rồi bounded scale gate.
Market clustering do nhóm khác phụ trách; workstream này không sửa market protocol.

### Financial executable reference flow — handoff mới nhất 03/10/2026

[Report](../artifacts/reports/financial-reference-flow-v1/report.md): chạy code từ
cached PDF/OCR → 22 parsed cells → reviewed-reference/accounting QA → date-PIT →
EPS/EM-Z reference outputs. FPT2024 original EPS 4.944/Z 6,843186 tại 17/03/2025;
FPT2025 EPS 5.216/Z 7,106292 tại snapshot 28/08/2026. EPS2024 tại snapshot này bị
chặn vì known revised comparative 4.292 trong original2025 chưa mapped; không dùng
số cũ hoặc backfill số mới. Latest reference_flow_v6, deterministic replay v5/v6.
36 task/decision rows: 5 QA-pass executions/4 unique task-years, 6 unavailable,
1 revision blocked, 24 F/M/PE/PB outside calculators. Chín targeted tests/compile/
synthetic smoke PASS; full 226/227 PASS, frozen M2-PREP checksum cũ còn lỗi.
Value/date coverage giữ 139/124 cells; không có feature production promotion.
Reference slice chạy được; tổng FIN-D2 PARTIAL, full-universe pipeline chưa đạt.
Next: revised-comparative acceptance, F/M semantics/inputs, TTM/share basis và
unseen-template pilot trước scale. Market-only work không thay đổi.
