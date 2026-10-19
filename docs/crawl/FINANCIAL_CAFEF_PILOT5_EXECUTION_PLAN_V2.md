# Plan v2 — crawl lại 5 mã và tính chỉ số financial đến kết quả thực tế

Ngày **18/10/2026**. Trạng thái **PLANNED_NOT_EXECUTED**; đây là plan giao agent,
chưa phải kết quả chạy pilot. Thay active handoff12mã trước bằng pilot nhỏ5mã,
không sửa hoặc hủy evidence của plan/run cũ.

- Workspace: `C:\Projects\Intern\SourceCode-CafeF`.
- Nhánh hiện tại: `research/financial-data`; kiểm lại git status trước khi làm,
  giữ local changes, không checkout/reset nhánh cũ.
- [Tổng hợp hiện trạng và lý do đổi plan](../../artifacts/reports/financial-cafef-pilot5-handoff-v2/report.md).
- [Goal/scope JSON](../../configs/data/financial_cafef_pilot5_plan_v2.json): planning
  contract **executable=false**, không truyền cho crawler50 cũ.

## 1. Goal, scope và tiêu chí thành công

**Goal: triển khai, chạy và bàn giao một flow local dùng CafeF để thu thập đúng
input, tính ra EPS, P/E, P/B, F-score, M-score và EM Z'' cho BRC/FPT/MWG/GMD/VNM;
có số thật, provenance, QA, replay/resume và hướng dẫn PowerShell cho user.**

Primary target là **5mã × 6families = 30family cells được recompute và kiểm chứng**
theo các practical variants đã khai báo. Có ít nhất3mã hoàn chỉnh6families là
checkpoint chứng minh flow hoạt động, **không phải lý do dừng khi2mã còn có thể
khắc phục trong scope/budget**. Reported ratios không thay mục tiêu recomputation.
Nếu access/budget/source ambiguity ngăn goal, xuất số đã tính và blockers có
bằng chứng; status PARTIAL/BLOCKED, không gọi goal hoàn thành chỉ vì đủ30statuses.

Đây là một stage `CAFEF_FINANCIAL_PILOT5_EXECUTION`, gồm các checkpoints P0–P5.
Prompt giao việc cuối tài liệu cho phép agent làm trọn stage, không xin “làm
tiếp” sau từng checkpoint. Không tự chuyển sang50/100, cluster hoặc stage khác.

| Mã | Vai trò và công việc riêng |
|---|---|
|BRC|Fresh control từ deep audit:192links/92datejoins/6PDF/51candidates; xử lý confirmed web debt-row mismatch, notes EPS/PPE/capital và original maturity. Không giả BRC thuộc frozen50. |
|FPT|Control có annual EPS/F/M/Z references, disclosure dates, share/TTM history; kiểm dedicated financial routes và annual valuation. |
|MWG|Control scan/notes/issuance; dùng verified cache, kiểm row mapping và valuation equity/share basis. |
|GMD|Control đủ4references, owned-PPE DEP/supporting TA2023 đã tìm, exact document cache. |
|VNM|Control pilot cũ, gap quarterly/LCTT, annual PDF/accounting framework VAS/IFRS; không trộn scope/framework để đủ số. |

Annual target **FY2025**, supporting2024 và balances cuối2023 cho F; lấy đúng
fiscal start/end theo tài liệu. Primary valuation dùng annual EPS/common-equity
snapshot và actual dated raw price. Current interim/TTM là **extension trong mẫu**
sau khi annual flow ra số, không được để TTM chặn annual completion. Không
backfill financial2020 hoặc crawl mọi tài liệu trong listing ở pilot này.
Không thêm sector/đổi mã khó; Bank/Securities/Insurance thuộc bước sau.

## 2. Đọc nhanh và code cần tham chiếu

Đọc lần lượt các nguồn sau; không đọc lại toàn bộ lịch sử hay chạy full crawl
chỉ để lấy context. Repo instructions vẫn áp dụng.

| Thứ tự | File | Dùng để làm gì |
|---|---|---|
|1|[AGENTS](../../AGENTS.md), [CONTRIBUTING](../../CONTRIBUTING.md), [START HERE](../README.md), [CURRENT_STATUS](../CURRENT_STATUS.md)|Boundaries, tests, active stage; market/cluster thuộc đội khác. |
|2|[Report tổng hợp mới](../../artifacts/reports/financial-cafef-pilot5-handoff-v2/report.md), plan này, [JSON](../../configs/data/financial_cafef_pilot5_plan_v2.json)|Goal, baseline, scope5 và completion contract. |
|3|[CAFEF.md](sources/CAFEF.md), sections deep audit/rediscovery đầu file|Exact routes/versions, FileBCTC/disclosure, units/modes, group pagination và known mismatch. |
|4|[BRC deep audit](../../artifacts/reports/financial-cafef-brc-deep-audit-v1/report.md), [inventory](../../artifacts/reports/financial-cafef-brc-deep-audit-v1/document-inventory.json), [candidates](../../artifacts/reports/financial-cafef-brc-deep-audit-v1/visual-candidates.json)|Fixture/independent comparison, actual PDF SHA/page, dates; chưa là canonical facts. |
|5|[UI/API correction](../../artifacts/reports/financial-cafef-disclosure-ui-correction-v1/report.md), [rediscovery analysis](../../artifacts/reports/financial-cafef-rediscovery-v2/analysis.json)|FPT CreateDate+file association, QNP LCTT JSON fixture, scripts+UI evidence levels, access stop. |
|6|[Handbook](../research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md), sections3–12; [feature contract](../research/FINANCIAL_FEATURE_CONTRACT.md)|Formula, dictionary, units, EPS/issuance/debt/PPE notes, declared variants. |
|7|[Literature matrix](../research/LITERATURE_MATRIX_COMPLETE.md), relevant financial/feature-space entries; [DECISIONS](../DECISIONS.md)|Research rationale; không tự dùng matrix thay score formula. |
|8|[Active integration pointers](../../configs/data/financial_active_integration_v1.json), [continuation](../../artifacts/reports/financial-continuation50-v2/report.md), [runbook](FINANCIAL_READINESS_USER_GUIDE.md)|Cache110PDF/812OCRpages, assessed controls, paths; expired old network budgets. |

Code map để reuse, không copy thành parallel calculator:

| File | Vai trò |
|---|---|
|[cafef_financial.py](../../src/delta_t1/ingestion/cafef_financial.py), [cafef_financial_detail.py](../../src/delta_t1/ingestion/cafef_financial_detail.py)|Acquire/parse cũ; header/unit semantics khác deep API mới. |
|[financial_compact_trial.py](../../src/delta_t1/ingestion/financial_compact_trial.py), [financial_trial_transport.py](../../src/delta_t1/ingestion/financial_trial_transport.py)|Durable counters, cache, deadline/access hard-stops. |
|[financial_pdf_evidence.py](../../src/delta_t1/ingestion/financial_pdf_evidence.py), [financial_note_evidence.py](../../src/delta_t1/ingestion/financial_note_evidence.py), [OCR script](../../scripts/ocr_financial_pages.ps1)|PDF/text/render/OCR/locator evidence; scan recognition trước mapping. |
|[financial_reference.py](../../src/delta_t1/features/financial_reference.py)|F9 và EMZ reference; `calculate('EPS_RECOMPUTE')` cũ yêu cầu diluted, không chọn sai entry cho basic-only. |
|[financial_vas_reference.py](../../src/delta_t1/features/financial_vas_reference.py)|`calculate_disclosed_basic_eps`, `calculate_vas_f_score`, `calculate_vas_m_score`, `calculate_reported_valuation`. |
|[financial_ttm_reference.py](../../src/delta_t1/features/financial_ttm_reference.py), [financial_equity_reference.py](../../src/delta_t1/features/financial_equity_reference.py)|Optional TTM/equity bridge với named bases; không bắt TTM làm primary. |
|[cafef_financial_trial.py](../../src/delta_t1/experiments/cafef_financial_trial.py), [financial_user_workflow.py](../../src/delta_t1/experiments/financial_user_workflow.py), [financial_resume.py](../../src/delta_t1/experiments/financial_resume.py)|Orchestration/cache/resume patterns; runner cũ không mặc định nhận5mã/new API. |

Khi cần thay architecture, đọc thêm [README](../../README.md), [PROJECT_MAP](../PROJECT_MAP.md),
[ROADMAP](../ROADMAP.md). Feature code không network; CLI chỉ điều phối. Agent
được tạo adapter/runner mới khi cần, phải giữ existing behaviors/tests/frozen runs.

## 3. Những findings bắt buộc đưa vào implementation

1. **Disclosure** `ajaxcongbothongtin.ashx`: CreateDate/Id/LinkFile, paging, title,
   period/scope/type; DATE_ONLY đã được owner cho phép, thiếu giờ không chặn.
2. **FinancialAjax** loader: CDKTv2/GetReportCDKT, KQKDv1/GetReportDetail,
   LCTTv1/GetReportLCTT, FinancialIndicatorsv2. Không dùng summary thay deep flow.
3. `QUY/NAM/LUYKE` cần actual interval metadata. LUYKE UI đã thấy H1reviewed;
   QUY LCTT có thể YTD. Parse headers **từng group**; HDKD/HDDT/HDTC paging độc lập.
4. Monetary table units khác EPS VND/share, EPS detail nghìn/share, percentages/
   ratios. Giữ raw precision; dash có thể là zero **hoặc** missing trong UI.
5. **BRC FY2025 debt:** web1,18tỷ tương ứng other payables PDF; actual debt24,14tỷ.
   Phải tái hiện discrepancy bằng fixture, xác định raw code/label/template issue;
   quarantine cell chưa rõ. Không dịch index/hard-code ticker hoặc chữa bằng magnitude.
6. **Documents**5groups/FileBCTC: full BCTC và BCTN có notes quan trọng. BCTN mixed
   text/scanned financial pages; text extraction trống không phải thiếu report.
   BCTC “Time” là kỳ, khác disclosure date. Không tải mọi nghị quyết mặc định.
7. **EPS** provider-adjusted/current khác annual disclosed và recomputed/TTM.
   BRC FY2025note30 có numerator/WA; provisions chưa estimated phải giữ limitation.
8. **Depreciation/capital/debt:** owned-PPE roll-forward khác combined CF D&A;
   BCTN no-capital-change statement là evidence candidate, mạnh hơn current shares
   bằng nhau. Long-term debt gồm current portion cần original maturity review.
9. **Dead links**: BRC old CDN link404, exact observed viewer URL tải được. Không
   rewrite host hàng loạt hoặc suy path trùng=bytes trùng; giữ alias chain + hash.
10. **Price/date:** current overview có thể last price16/10 nhưng Q3report gửi17/10.
    Không gọi provider ratio là available tại close16/10; actual valuation decision
    phải đứng sau availability hoặc chỉ labeled current snapshot diagnostic.

## 4. Execution checkpoints P0–P5

### P0 — Freeze pilot, cache và baseline (không dừng sau checkpoint này)

- Verify branch/status, sample5, required families, source/contract hashes và
  baseline32/300. Không đưa BRC vào market/frozen50 membership để hợp thức runner.
- Tạo **executable config mới** sau khi validate schema/code; planning JSON này
  không phải executable config. Output root mới, input caches read-only/hash-verified.
- Import BRC51observations làm comparison fixtures; controls reuse exact PDF/OCR
  cache. Phân biệt `REUSED_VERIFIED_CACHE` và `FRESH_ACQUIRED` ở mọi acquisition.
- Lưu execution-state/task/dependency journal trước network/OCR; byte/page budget
  reservations và deadline phải bền vững qua crash/resume/process restart.

**Output:** frozen executable contract, cache manifest và task graph cho30cells.

### P1 — Adapter/disclosure integration và sample reacquisition

- Implement/extend dedicated adapters từ routes đã quan sát; lưu raw JSON/HTML,
  source IDs, unit/template/raw codes và per-group headers, không chỉ export UI text.
- Fresh structured observation cho cả5mã khi access hợp lệ; nếu chỉ replay cache
  vì access thì ghi rõ. Tái dùng PDF/OCR thay vì tải lại để tạo vẻ “fresh”.
- BRC disclosure fixtures92joins + FPT CreateDate fixture kiểm parser; live lists
  chỉ tới annual2024/2025 và gaps, không mặc định đọc hết mọi lịch sử của5mã.
- Với mismatch BRC, so raw payload↔UI↔PDF; field crosswalk phải code+label+
  template/version. Nếu raw API chưa giải thích được, dùng reviewed PDF field
  trong reference với explicit conflict flag và giữ raw UI riêng.
- Không ép mọi row hợp nhất/standalone: BRC không có subsidiaries được kiểm riêng;
  chọn compatible issuer/scope/framework và khai báo rule trước normalize.

**Output:** source-audit, normalized candidates, disclosure associations, regression
fixture debt-row và independent LCTT group paging; tiếp tục P2 ngay.

### P2 — Đủ dependency bằng tài liệu/notes và xử lý gaps

Lập queue theo **field/period/metric**, không theo “ticker còn thiếu” chung chung:

| Nhóm | Inputs phải resolve |
|---|---|
|EPS basic FY|Numerator disclosed/deductions context, WA basic, printed EPS; diluted riêng nếu có. |
|PE annual/PB|Raw price/date, annual eligible EPS, parent common equity/shares, scope/treasury/events và basis rõ. |
|F-VAS9|NI/CFO, assets3dates, CA/CL2years, revenue/GP2years, original-maturity LTD2years, actual parent issuance. |
|M sensitivity8|Gross trade REC/revenue/GP/CA/TA/net owned PPE/owned DEP/SGA/debt/NI/CFO2years, declared basis. |
|EMZ|CA/CL/TA/RE/total liabilities/equity/EBIT bridge từ PBT+pure interest đúng variant. |

- Dùng full annual/supporting PDF, BCTN và notice đúng residual; reuse110PDF/
  812OCRpages có hash/period/scope phù hợp. Không OCR lại các trang đã verify.
- Native text trước; nhận diện text/scan **từng trang**. OCR targeted pages; thiếu
  locator thì bounded search. Agent render/visual review ambiguous cells và ghi
  review decisions có locator; không giao user nhập lại templates chỉ vì chưa map.
- Phân biệt `SOURCE_NOT_FOUND`, `NOT_EXTRACTED`, `MAPPING_CONFLICT`,
  `BASIS_UNRESOLVED`, `TEMPORAL_ONLY_GAP`, `ACCESS_BLOCKED`, `BUDGET_DEFERRED`.
- Khi thiếu field: kiểm existing cache → dedicated structured route → annual notes/
  BCTN/linked notice. Nếu CafeF thiếu thật, bounded issuer/exchange supplement có
  source tier riêng; không cộng external-only vào CafeF-only sufficiency.
- Reparse offline sau fix; không download/OCR lại cùng unchanged bytes để thử may rủi.

**Output:** field-coverage + exact input rows/provenance và remaining dependency
queue; đủ metric nào chuyển P3 metric đó, không chờ publication hoàn hảo toàn batch.

### P3 — Tính thật và đối chiếu, tiếp tục đóng gaps

- Dùng calculators đã có, adapter input map đúng fields/years; Decimal arithmetic.
  Annual EPS basic không bị chặn chỉ vì thiếu diluted. Giữ disclosed deductions
  limitation; không đổi tên thành strict normalized EPS.
- Primary family variants: `DISCLOSED_BASIC_EPS_FY_REFERENCE`,
  `ANNUAL_REPORTED_BASIS_PE_REFERENCE`, `DECLARED_BOOK_SHARE_BASIS_PB_REFERENCE`,
  `VAS_F9_REFERENCE`, `VAS_M8_SENSITIVITY`, `EM_Z_DOUBLE_PRIME_REFERENCE`.
  Đây là output labels cần map về implementation registry, không tạo công thức
  mới chỉ để có số. PB phải ghi snapshot/current-shares/event bridge cụ thể.
- Chọn actual dated **unadjusted/raw close** từ market cache sau annual sources
  usable date. Ưu tiên cùng ngày cho5mã nếu có; nếu không, ghi per-symbol dates,
  không giả comparable snapshot. Có thể lấy một bounded public price observation
  nhỏ cho mã thiếu cache; không recrawl/rebuild market foundation của đội khác.
- Provider EPS/PE/PB, proxies và current TTM là variants phụ. Không thay `*_RECOMPUTED`
  bằng provider-only. Không dùng EPS quarterly đã rounded để cộng/annualize.
- Với F,9signals known mới ra full score; unknown xuất interval/known count.
  Không partial-sum M8/Z thành full. EPS≤0 hoặc equity≤0 xuất N/M nếu đúng math,
  không fabricate valuation. Reference có số vẫn tách temporal/audit/revision flags.
- So ít nhất20unique field-period cells/mã nếu có ground truth, gồm critical
  inputs notes; không lấy provider so chính provider làm independent QA. Thiếu
 20checked comparisons thì report count thật/PROVISIONAL, tiếp tục review trong cap.
- Giải thích discrepancy do vintage/scope/rounding/mapping; preserve values và
  conflicts. Tolerance theo displayed precision, không arbitrary % để che debt shift.

**Output bắt buộc:**30unique `(symbol,family)` rows, variants riêng, actual metric
values cùng dependency IDs/input values/formula/version/units/price+period/date.
Goal30recomputed cells là target;30status rows không thay target. Chưa đạt thì
quay lại dependency queue P2 trong budget, không kết thúc bằng “cần chạy calculator”.

### P4 — Flow user chạy được, tests/replay/resume

- Một PowerShell entrypoint gọi Python runner; đề xuất tên
  `scripts/financial_cafef_pilot.ps1` + `.py` (**chưa tồn tại khi lập plan**).
  Modes cần có: doctor/plan/run/report/verify; explicit network opt-in và resume.
- Doctor kiểm runtime/OCR/render/cache/config/branch; plan xuất requests/dependencies
  và cap trước run; report/verify default offline. Existing wrapper50 giữ nguyên.
- Chạy thật command mẫu của runbook với config executable mới. Replay cùng raw/
  inputs → cùng metric values/hash semantics, **0new network/OCR**. Tests simulate
  interruption/resume bằng fixtures; không cố phá large live downloads.
- Targeted tests: code/label mismatch, per-group header paging, QUY/YTD/LUYKE,
  zero-vs-missing, mixed units/EPS, scope/revision, original debt/PPE variants,
  basic-only EPS, raw-vs-adjusted price, numerical-vs-PIT, access/budget/cache/tamper.
- Chạy compileall; sửa pipeline chạy synthetic smoke theo CONTRIBUTING; full suite
  khi warranted. Không xóa assertion cũ hoặc waive hash checks vì thay living docs:
  pin source snapshot đúng version, ghi supersession và verified closure.

**Output:** runnable commands/logs/runbook, tests và immutable run manifest.

### P5 — Verdict và bàn giao khi goal đạt hoặc blocker thật

- Summary riêng: recomputed/QA-checked/provider-only/proxy/partial/N/M/missing;
  denominator primary30 cố định. Một family nhiều variants chỉ đếm1cell.
- `GOAL_ACHIEVED`:5mã đủ6primary families thực sự recomputed và QA đạt, runner
  được live chạy/replay/resume verify. Giá trị cần N/M đúng math không thể gọi là
  30numeric success; giải thích riêng và đánh giá target honest.
- `PARTIAL_WITH_RESULTS`: đã có real metrics nhưng chưa đủ goal. Liệt kê remaining
  dependency, action đã thử, evidence và next action cụ thể. Không đổi goal thành
  “đã viết report”, không dừng ở3mã nếu còn sửa được2mã trong cap.
- `BLOCKED_ACCESS_OR_BUDGET`: nguồn còn inconclusive vì hard stop; numerical/cache
  work độc lập vẫn hoàn tất. Không gọi blocked=source thiếu, không reset để retry.
- Source verdict theo family: structured đủ / CafeF+attachments đủ / external cần
  bổ sung / inconclusive. Không suy5mã đại diện chắc chắn1.000mã.
- Chỉ **đề xuất** pilot50 nếu ít nhất3complete workflows, no critical silent
  mapping issue trong enabled templates, QA và manual-intervention cost đo được.
  Không tự crawl50/100 hoặc mở canonical/research/financial cluster.

## 5. Quyền quyết định và rules thực dụng

Owner đã cho phép profile thực dụng: thiếu publication không chặn số học;
DATE_ONLY khi có ngày, reported ratios riêng, QA theo template/field groups,
named proxies/partial outputs và audit/revision flags. Agent không xin lại vì
thiếu giờ, một metric chưa đủ hoặc cần đọc/OCR thêm file trong cap.

Giữ nguyên correctness: ticker/unit/period/scope/version, missing≠0, denom valid,
price/share basis, no lookahead. Signature-date proxy chỉ là sensitivity riêng,
**không ưu tiên** khi disclosure có ngày đúng file. Không đổi strict historical
PIT/research/backtest/market protocol. Nếu cần methodology khác ngoài phạm vi đã
duyệt, ghi `MANUAL_REVIEW_REQUIRED` cho dependency đó và tiếp tục công việc độc lập.

Source roles: A structured CafeF; B CafeF-linked document; C provider ratios;
D external supplement. `CHECKED_REFERENCE`, `PROVIDER_AS_REPORTED`, `PROXY_REFERENCE`,
`PARTIAL`, `PROVISIONAL`, `NOT_MEANINGFUL`, `SOURCE_NOT_FOUND`, `MAPPING_CONFLICT`,
`ACCESS_BLOCKED`, `BUDGET_DEFERRED` tách nhau; applicability phải có lý do, không
đặt Regular thành N/A vì parse khó. Financial/research/cluster gates giữ false.

## 6. Budgets, persistence và điểm dừng

Caps frozen trong [planning JSON](../../configs/data/financial_cafef_pilot5_plan_v2.json):
250logical/350transport attempts tổng,16PDFattempts,25MB/PDF,3MB/structured,
500MBtotal,6h **network deadline** từ START, spacing≥2s, timeout25s,≤2attempts/URL
chỉ cho transient failures;400newOCRpages/80perPDF/80perbatch. Cache đọc không
consume download budget; OCR chỉ charge trang mới, reservation giữ qua crash.
Local coding/replay/report tiếp tục sau network deadline nếu không acquire thêm.

Đây là cap, không ETA hoặc mục tiêu dùng hết. Không tự tăng cap, rotate cache
epoch/runID/client/cookie/host/proxy để reset.401/403/429/login/challenge latch
và stop acquisition liên quan; không reclassify thành transient. Old EPS campaign
latched giữ nguyên; không dùng plan mới để retry bị chặn. User confirmation của
normal UI access chỉ là evidence cho UI audit đã làm, không tự chứng minh scripted
EPS access được khôi phục. Các public documents/observed redirects hợp lệ lưu rõ
chain; không bypass boundary bằng client khác.

Durable journal là source of truth, execution-state là projection; khi restart
phải dựng counters từ journal và validate cache/hash trước request. Sau checkpoint
publish stage/remaining tasks/counts để agent resume không đọc lại toàn chat.

## 7. Deliverables và checklist kết thúc

Required output trong một versioned run mới:

- `execution-contract.json`, `execution-state.json`, acquisition journal,
  raw/doc/OCR manifests và source snapshots.
- `source-audit.csv`, `document-index.json`, `field-coverage.csv`,
  `metric-inputs.jsonl`, `metric-dependencies.json`, `metrics.csv` (30family rows),
  `metric-variants.csv`, `qa.csv`, `exceptions.csv`, `policy-deviations.csv`.
- `costs.json`: requests/bytes/PDF/OCR/cache hit/time, per-symbol/manual-review
  counts; không gộp uninstrumented browser traffic vào scripted counters.
- `report.md`: values5×6 + gaps, exact source comparison, strict/practical flags,
  source verdict và scale recommendation; `user-runbook.md` với commands thực chạy.
- `tests.log`, smoke/compile/replay verification và `manifest.json`.

Không kết thúc ở trạng thái chỉ có adapter/config hoặc tài liệu. Goal phải được
đánh giá bằng run artifacts và metric values. Mọi required metric đủ input phải
được tính ngay, không để TODO. Khi chưa goal, status giữ PARTIAL kèm runnable
handoff và evidence blocker, không “COMPLETE” do sắp hết context/usage.

## 8. Prompt copy giao agent

> Bạn làm trong C:\Projects\Intern\SourceCode-CafeF, nhánh hiện tại
> research/financial-data; kiểm lại branch/status, không reset local changes.
> Đọc docs/crawl/FINANCIAL_CAFEF_PILOT5_EXECUTION_PLAN_V2.md và các file trong mục
> Đọc nhanh. Tôi giao bạn **thực thi toàn stage P0–P5**, gồm code adapter/runner,
> crawl lại BRC,FPT,MWG,GMD,VNM có giới hạn, xử lý gaps bằng CafeF structured +
> documents/notes/cache, tính thật EPS/PE/PB/F/M/Z và giao flow PowerShell/runbook.
> Goal primary là5×6=30family cells recomputed+QA dưới practical variants khai báo;
>3mã complete là checkpoint, không phải lý do dừng. Không dừng sau discovery,
> report hoặc chỉ đọc ratios web; đủ input là phải chạy calculator. Tôi cho phép
> tiếp tục các checkpoints không hỏi “làm tiếp” từng bước và profile thực dụng
> trong plan; thiếu giờ/PIT không chặn numerical work. Đọc kỹ BRC debt-row mismatch,
> LCTT group paging, unit/EPS, audit vintages và mixed PDF. Dùng calculators sẵn,
> reuse verified raw/PDF/OCR; không hard-code đáp án từ51BRC observations.
> Giữ missing/basis/provenance và reported/proxy/recomputed riêng. Không thay strict
> research/market methodology, không reset hard stops, không bypass access hoặc
> tự mở50/100/cluster. Làm đến actual goal hoặc blocker access/budget/source có
> bằng chứng sau khi đã làm hết việc độc lập. Nếu chưa goal thì báo PARTIAL với
> real values/dependency gaps, không giả COMPLETE. Lưu durable execution state,
> test/smoke/replay/resume, cập nhật report/changelog và commands user đã verify.
> Không spawn subagent. Các tên runner mới trong plan là deliverables cần viết,
> không giả chúng đã tồn tại; planning JSON không truyền cho wrapper50 cũ.
