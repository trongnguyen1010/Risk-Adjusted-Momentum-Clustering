# Kiểm chứng lại CafeF financial và bàn giao agent

Ngày lập **18/10/2026**. Trạng thái **PLANNED_NOT_EXECUTED**.
Workspace `C:\Projects\Intern\SourceCode-CafeF`; nhánh hiện quan sát
`research/financial-data`. [Bản tổng hợp quá trình](../../artifacts/reports/financial-replan-20261018-v1/report.md).
[Plan JSON](../../configs/data/financial_cafef_revalidation_plan_v1.json) để agent đọc
scope/goals; **chưa phải config có thể truyền cho crawler cũ**.

## 1. Goal và câu hỏi phải trả lời

**Tạo được một flow chạy local có bằng chứng thực tế: CafeF cung cấp được những
field/chỉ số financial nào trên mẫu12 mã, bao nhiêu lấy trực tiếp dạng bảng,
bao nhiêu phải lấy PDF/thuyết minh, bao nhiêu thực sự cần nguồn ngoài; tính ra
giá trị khi đủ input và giao runner/runbook để owner tái chạy.**

Phải trả lời riêng bốn câu:

1. CafeF có đủ **báo cáo và field đầu vào** hay chỉ hiển thị một số ratios?
2. Field tồn tại nhưng crawler/parser/map/unit/kỳ sai, hay nguồn thực sự trống?
3. Dùng quy tắc thực dụng thì tính/đọc được EPS, PE, PB, F, M, Z bao nhiêu?
4. Phần nào vẫn chưa thể dùng cho historical PIT/backtest, dù có giá trị số?

Thông tin “CafeF có đủ hết” là **giả thuyết cần kiểm chứng**, không phải kết luận
được hard-code. Goal hoàn thành là một kết luận đo được cùng flow và bảng gaps,
không phải ép mọi mã/ô thành100%. Không kết luận nguồn thiếu chỉ từ task-ready0.

## 2. Đọc nhanh — không đọc toàn bộ lịch sử

Thứ tự này là handoff active cho workstream financial; Project Map/M2 có thể nói
next stage market-only, không dùng chỉ dẫn đó để chuyển sang công việc của đội cluster.

| Thứ tự | File | Cần nắm |
|---|---|---|
|1|[AGENTS.md](../../AGENTS.md), [CONTRIBUTING](../../CONTRIBUTING.md)|Invariants, immutable evidence, tests, access controls.|
|2|[Bản tổng hợp hiện trạng](../../artifacts/reports/financial-replan-20261018-v1/report.md)|Đã làm gì,32/300 nghĩa gì, các chỗ chưa kiểm xong.|
|3|Plan này + [JSON scope](../../configs/data/financial_cafef_revalidation_plan_v1.json)|Goal, quyền nới rule,12mã,outputs,termination.|
|4|[CafeF source discovery](sources/CAFEF.md)|Summary/detail/FileBCTC, kỳ bị trống và khác biệt nguồn với parser. Ưu tiên các section financial đầu file; phần older discovery là lịch sử.|
|5|[Handbook chỉ số/data](../research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md), sections3–11|Công thức, biến thể, dictionary, scope/units/notes.|
|6|[Financial feature contract](../research/FINANCIAL_FEATURE_CONTRACT.md)|Strict baseline và những khác biệt cần đặt tên khi practical profile thay thế.|
|7|[Literature matrix](../research/LITERATURE_MATRIX_COMPLETE.md), B6/B7 và Feature space|Cơ sở ghép fundamentals với market; matrix không chứa công thức F/M/Z. Dùng handbook/contract cho score formulas.|
|8|[Benchmark CafeF–KBS](../../artifacts/reports/financial-source-benchmark-v1/report.md), [CafeF50](../../artifacts/reports/cafef-financial-trial50-v1/report.md)|Lý do CafeF primary; wire gaps và QA exceptions.|
|9|[Latest continuation](../../artifacts/reports/financial-continuation50-v2/report.md), [publication follow-up](../../artifacts/reports/financial-publication-followup-v1/report.md)|Cache/runner hiện hành, expired budgets, pending publication.|

Chỉ đọc tiếp [docs index](../README.md), [CURRENT_STATUS](../CURRENT_STATUS.md),
[PROJECT_MAP](../PROJECT_MAP.md), [ROADMAP](../ROADMAP.md), [DECISIONS](../DECISIONS.md)
khi cần kiểm boundary hoặc thay contract. Những entry ngày cũ trong status/index
không phải instruction checkout nhánh cũ. Không yêu cầu chạy full historical
verifier trước mọi bước discovery nếu verifier không thuộc input của bước đó.

## 3. Scope và mẫu thử đã chốt

Mẫu chính **12 mã**, tất cả có trong frozen50 engineering sample:

| Mã | Vai trò cần kiểm |
|---|---|
|FPT|Control có đủ4referencefamilies; quarterly/LCTT gaps đã biết.|
|MWG|Scan PDF, weighted shares/issuance, expensed interest và thuyết minh.|
|GMD|Control exact issuer/cache PDF joins và đủ4references.|
|VHC|Reported EPS/restatement, expense sign và publication gaps.|
|DGC|Qualified audit, restated comparative khác provider; giữ flag.|
|ACV|UPCOM, summary pagination overlap từng có, định giá.|
|VEA|Các chênh structured/PDF đã quan sát để kiểm mapping/vintage.|
|CTD|Stress test fiscal-year boundary; xác minh actual start/end.|
|SLS|Báo cáo annual không theo calendar, không ép31/12.|
|TCB|Bank, schema/ratio applicability riêng.|
|HCM|Securities, schema/ratio applicability riêng.|
|BVH|Insurance và HTTP302 từng gặp; kiểm link public từ UI, không workaround boundary.|

VNM/PVS là optional controls ngoài sample chính, chỉ dùng cache hoặc thay control
theo lý do ghi trước; không tự thêm vào frozen market membership. Không loại mã
khó để làm coverage đẹp. Không crawl lại toàn bộ market hoặc chạy cluster.

Hai lát cắt cần tách:

- **Annual comparable:** target FY2025, tài liệu2024/2025 và balance2023 khi F cần;
  fiscal2025 của CTD/SLS là kỳ thực tế của doanh nghiệp. Không ép mọi source cùng
  header year; latest-restated view ghi rõ được tải ở thời điểm nào.
- **Current valuation/interim:** xác định latest actually published interim2026
  tại ngày execute, cùng comparative để thử TTM. Freeze `valuation_date` từ giá
  raw có ngày thật. Không lấy ratios fresh rồi gán cho snapshot28/08/2026. Market
  cache hết28/08 thì cần price observation nhỏ riêng hoặc ghi gap; không dùng
  adjusted close thay raw chỉ vì có sẵn.

Known gap controls tối thiểu: Q2/2024, Q1/2025, Q2/2025 tại những mã từng trống;
kiểm đúng quarter riêng/YTD/6M. LCTT YTD không được gọi là standalone quarter.
Đây là12mã đại diện engineering, không phải mẫu ngẫu nhiên để ước lượng chắc chắn
coverage của1.000mã.

## 4. Cách hiểu “đủ data CafeF”

Giữ source tier trong mọi fact/metric:

| Tier | Gồm gì | Được kết luận |
|---|---|---|
|A — structured|Summary/detail CDKT,KQKD,LCTT, các API/table thật từ UI công khai|Có thể tự động đọc field/period đó từ bảng CafeF.|
|B — CafeF-linked document|PDF/notes có link từ CafeF, có source listing pin; file có thể host ở CDN/issuer|CafeF giúp lấy đủ qua attachment; không gọi là structured đủ.|
|C — CafeF reported ratios|EPS/PE/PB hiển thị, kèm basis/date metadata quan sát được|Provider-as-reported; không chứng minh recomputation đúng.|
|D — external supplement|Tìm được ở issuer/exchange nhưng không chứng minh có link trên CafeF|Nguồn ngoài bổ sung, không cộng vào CafeF-only coverage.|

PDF cache từ issuer không tự biến thành TierB khi năm/ticker trùng. Phải tìm và
pin đường dẫn CafeF→attachment hoặc SHA association; bytes giống không cần tải/OCR
lại. Đánh giá field-level và metric-level; “một kỳ có một số” không nghĩa đủ score.

## 5. Rule thực dụng và rule giữ nguyên

Owner18/10 cho phép nới rules khi cần. Agent được triển khai **profile mới**
`PRACTICAL_FINANCIAL_V1`, ghi config/ADR/tests/diff acceptance, không sửa retroactive
strict runs. Những nới lỏng dưới đây đã nằm trong phạm vi được bàn giao; không
xin lại chỉ vì thiếu giờ công bố, chưa human-review toàn bộ ô, hoặc không đạt100%.
Historical research/backtest và market-only methodology vẫn tách biệt.

| Hạng mục | Default practical được phép | Giới hạn phải ghi |
|---|---|---|
|EPS|Đọc `EPS_REPORTED_FY` từ provider sau unit/period/scope checks; recompute khi numerator/WA có.|Reported không đổi tên thành EPS_RECOMPUTED; closing shares không thay weighted average.|
|PE/PB|Thu reported provider ratios riêng; recompute annual PE/BVPS/PB khi đủ input cùng ngày/basis.|PE_ANNUAL khác PE_TTM; current vendor ratio không gán historical as-of hoặc coi đã audit công thức.|
|Publication|Thiếu publication vẫn tính numerical reference; issuer/CafeF dated post với attachment join có thể lưu DATE_ONLY evidence cho exploration.|Không tự gán `STRICT_PIT_VERIFIED`; xử lý `POST_DATE_LINKED`, `PUBLICATION_UNKNOWN` riêng.|
|Ngày ký|Được chạy sensitivity riêng với `SIGNATURE_DATE_PROXY`, ghi ngày ký và giả định rõ.|Không gọi proxy là ngày công bố; thêm1phiên không chứng minh đã available lịch sử. Không đưa vào strict backtest.|
|Numeric acceptance|QA theo template/field groups trên mẫu, deterministic checks và review exception; không bắt ảnh/PDF/manual attestation cho từng structured cell.|Chỉ nhóm units/labels đã có evidence mới normalize; confidence categorical, không bịa tỷ lệ accuracy.|
|Rounding|Tolerance dựa displayed precision của hai nguồn; balance checks dùng propagated rounding bound.|Không ép1VND cho bảng triệu/tỷ đã làm tròn; không dùng arbitrary tolerance để che sai kỳ hoặc multiplier.|
|Expense sign|Sau khi xác minh template trình bày expense âm/positive cost, normalize theo rule versioned.|Không `abs()` mọi cột hoặc sửa individual discrepancy không có cơ sở.|
|F thiếu signal|Xuất known signals, `F_lower=sum(known)`, `F_upper=F_lower+unknown_count`, coverage `k/9`.|Không gọi F9 hoàn chỉnh khi8/9; unknown không bằng0; thay equity delta cho issuance phải là variant riêng.|
|M/Z/F proxies|Chỉ thử variant có tên/fields/formula/deviation rõ, ví dụ D&A toànCF thay owned-PPEDEP như sensitivity; ưu tiên đủ fields thật.|Original score giữ null nếu thiếu; không partial-sum M8, không trộn proxy và chuẩn trong một cluster column.|
|Sector|F/M/Z Regular có thể N/A với Bank/Securities/Insurance; vẫn kiểm EPS/PE/PB và basic fields.|N/A theo model applicability; không N/A chỉ vì source trống hoặc parser chưa viết.|
|Audit/revision|Qualified audit/restated values vẫn lưu và tính reference kèm flag; latest-as-reported view được phép.|Không gọi clean audit; không xóa older version hoặc ghép hai conflicting vintages để đủ input.|
|Completeness|Tính metric nào đủ trước, xuất mask/gap metric nào thiếu; không chặn toàn symbol/batch.|Chưa cho imputation để tạo score gốc hoặc chấp nhận partial row vào strict clustering.|

Phân hạng output tối thiểu: `CHECKED_REFERENCE`, `PROVIDER_AS_REPORTED`,
`PROXY_REFERENCE`, `PARTIAL`, `MISSING_SOURCE`, `PARSER_OR_MAPPING_GAP`,
`ACCESS_BLOCKED`, `BUDGET_DEFERRED`, `NOT_APPLICABLE`.
Thêm flags publication/audit/revision/scope riêng, không một boolean fail tất cả.
`PROVISIONAL` dùng khi có số nhưng template QA chưa đủ. Coverage reported, proxy,
partial và checked phải xuất riêng; không cộng tất cả thành một tỷ lệ “đã đúng”.

Không nới: ticker/period/unit identity; không missing→0; không zero/negative invalid
denominators; không trộn consolidated/standalone/VAS/IFRS; không biến latest-restated
thành lịch sử first-public; không future leak, bypass access, thay immutable evidence,
hoặc thay market-only research protocol. Nếu phát hiện muốn đổi ngoài phạm vi này,
ghi đề xuất cụ thể và tiếp tục các task độc lập, chỉ chặn dependency thật sự cần quyết định.

## 6. Các bước agent phải thực hiện đến khi ra kết quả

### R0 — Freeze task và kiểm cache

- Xác minh cwd/branch/git status; giữ modifications hiện có, không reset/checkout
  nhánh cũ. Lưu source hashes,12sample,profile,periods,valuation date convention.
- Kiểm [active pointer](../../configs/data/financial_active_integration_v1.json),
  latest summary, input PDF/OCR cần dùng; chọn cache theo exact SHA và actual scope.
- Tạo execution contract **mới**, có branch hiện tại và bounded small-sample scope;
  budgets của run cũ đã hết, không mutate để restart. Không chạy nguyên wrapper50
  rồi mong nó nhận12mã: module cũ enforce membership/time/pilot/source pins.
- Xuất `execution-state.json`: goal,stage,attempted routes,remaining caps,decisions,
  next action,paths. Cập nhật sau mỗi checkpoint để resume không phải đọc toàn lịch sử.

**Done:** hợp đồng mới được validate, không network bất ngờ; baseline snapshot đã pin.

### R1 — Audit source thật trước khi viết thêm parser

- Với từng mã, mở financial UI công khai, quan sát request/link thực tế. Kiểm
  summary, detail3statements, annual/interim/quarter vs cumulative, FileBCTC và
  reported ratios nếu có. Không đoán hidden/private endpoint.
- Khi table trống: đối chiếu raw payload và DOM/header trước; ghi rõ HTTPerror,
  blanksource,unsupported fiscal layout,wrong anchor,parserreject hay row mapping.
- LCTT indirect/direct là hai route phải kiểm theo mẫu source; chỉ thử alternate
  cho gap mới, không lặp known failed route vô hạn. Với redirect thông thường,
  chỉ accept URL canonical công khai đã quan sát/allowlist và ghi chain; không
  follow challenge/login redirect hoặc sửa NoRedirect global của frozen code.
- Lập `source-audit.csv`: ticker,route,statement,requested/observed period,scope,
  fiscal interval,unit label,row count,presence,status,url,fetched_at,raw SHA,error.

**Done:**12mã có kết quả mọi route liên quan, mọi gap có evidence hoặc explicit
access/budget status. Không dừng ở “API trả200” hoặc viết report discovery rồi thôi.

### R2 — Lấy data và sửa gaps có giới hạn

- Crawl fresh structured observation cho sample; dùng cache cũ làm comparison,
  không gọi cache replay là live fresh success. Tái sử dụng PDF/OCR đã khớp.
- Chuẩn hóa row codes+labels+template version và units theo field group; kiểm
  column periods theo actual headers, không mặc định index0 là năm mới nhất.
- Ưu tiên CFO,WA shares/printed EPS,PPE/DEP,receivables,debt maturities,issuance,
  parent equity và pure interest; đây là fields từng khiến exact calculator thiếu.
- Dùng native text trước; OCR đúng pages chứa gap/notes, không FullOcr mọi file.
  Nếu không biết locator thì bounded text/OCR search rồi review các ô ambiguous.
- Sau mỗi vòng sửa, reparse raw offline. Tối đa một lần thử route thay thế có
  căn cứ cho từng gap; không tải lại cùng URL/hash để “thử thêm” khi raw vẫn blank.
- `field-coverage.csv` phân biệt raw present,mapped,normalized,QA checked/proxy,
  source missing,missing extraction và rule blocked. Mỗi fact có provenance.

**Done:** dependency inventory cho6families trên12mã và source tier của từng input;
những fields không có được ghi nguyên nhân chính, không đứng chung “missing”.

### R3 — Tính giá trị thật, không dừng ở readiness

- Tạo72family rows (12×6). Với9Regular, thử6families;3financial-type mã có EPS/PE/PB,
  F/M/Z Regular mặc định N/A có lý do. Mask tạm63applicable/9N/A, xác minh template
  trước khi freeze; không thay mẫu số để che field thiếu ởRegular.
- EPS_REPORTED vàEPS_RECOMPUTED xuất riêng. F_VAS9/M_sensitivity/EMZ dùng công thức
  handbook hiện hành; phiên bản thực dụng khác thì tên khác, ghi delta.
- PE annual/TTM/provider và PB recomputed/provider là các variants, không chọn
  variant nào có số để báo “recompute complete”. PE khiEPS≤0 trả N/M có lý do;
  không zero/divide by negative rồi coi là valuation comparison hợp lệ.
- TTM cần compatibleFY+currentYTD−priorYTD và WA/share-event basis; không cộng
  rounded quarterlyEPS hoặc nhân6M×2. Chưa đủ thì vẫn publish annual/provider
  diagnostics riêng và ghi TTM gap.
- Đối chiếu actual metrics với independent arithmetic, các PDF/cache đã review
  và website. Nếu khác version, giữ cảvalue+vintage và giải thích, không sửa ground truth.

**Done:** mọi72rows có giá trị thật hoặc terminal status; định lượng số full,
reported,proxy,partial,N/A riêng; chỉ số nào tính được phải được tính chứ không
để placeholder rồi viết “cần chạy thêm”.

Quy ước mẫu số: `row_kind=FAMILY` có đúng72 unique `(symbol, family)`; các biến
thể là `row_kind=VARIANT` riêng, có key `(symbol, family, variant, period, as_of)`.
Một family có2–3variants không được tính thành2–3ô coverage. Family reported-only
không làm tăng số recomputed/checked; N/A có lý do không đồng nghĩa đã tính số.

### R4 — QA, replay/resume và owner handoff

- MỗiRegular: ít nhất20 unique field-period comparisons giữa structured và exact
  compatiblePDF/verified reference nếu có, gồmTA,liabilities,equity,revenue,NI,CFO,
  EPS; thiếugroundtruth ghi count thật. Với3sector mã: tối thiểu10cells/mã ở fields
  hợp lệ. Không dùng provider so chính nó làm independentQA.
- QA units/currency/period/scope; balance equation theo rounding bound; EPS denominator;
  date/basis valuation; issuer-vintage conflicts và nhữngknown exceptions không được bỏ.
- Với template/fieldgroup chưa có evidence đủ, chỉ `PROVIDER_AS_REPORTED` hoặc
  `PROVISIONAL` cóflag, không auto-upgrade `CHECKED_REFERENCE`. Tỷ lệ matches dùng
  denominator thực tế; công bố unavailable comparisons.
- Tests cho parser/header/fiscal/YTD,units,negative/blank,partial signals,variant
  isolation,PITvsnumeric,budget/access,resume,tamperedhash và sameURLchangedbytes.
  Thay pipeline phải chạy synthetic smoke; synthetic không chứng minh live coverage.
- Replay offline phải0new requests/OCR. Thử interrupted-resume bằng fixture/local
  snapshot, không cố tình ngắt một large live download làm mất budget.
- Bàn giao **một** CLI/PowerShell entry với modes doctor/plan/run/report/verify,
  optional resume và explicit network switch; lệnh phải chạy thật trong QA. Các
  tên CLI dưới đây là deliverable phải implement, không phải command đã tồn tại.
- Local long run không cần mở Codex để chờ; lưu progress/counters/feedback JSON/ZIP.

**Done:** owner có user-runbook với đường dẫn config,Python,expected outputs/exit
statuses; actual executed commands/logs,sha,tests và rerun verification có sẵn.

### R5 — Kết luận và quyết định scale

Xuất verdict theo **từng family/variant** và tổng phạm vi mẫu:

1. `CAFEF_STRUCTURED_SUFFICIENT_FOR_SAMPLE`: tất cả required applicable inputs của
   phạm vi được nêu có từTierA/C, đủ kiểm tra; ghi provider-vsrecompute coverage riêng.
2. `CAFEF_WITH_ATTACHMENTS_SUFFICIENT_FOR_SAMPLE`: phảiTierB/PDF nhưng khôngTierD
   mới đủ. Chỉ gọi sufficient đầy đủ nếu cảrequired cells của phạm vi đó đạt.
3. `CAFEF_PARTIAL_EXTERNAL_SUPPLEMENT_NEEDED`: ít nhất mộtrequired input thiếu sau
   route/parser checks; chỉ rõ field/mã/kỳ,sourcepath,ảnh hưởng metric. Nếu phảiTierD
   hoặcproxy thay field thì không gọi CafeF-original complete.
4. `INCONCLUSIVE_ACCESS_OR_BUDGET`: access/time/cap không cho kiểm đủ; không quy
   thành “nguồn không có”. Lưu pending để owner có thể quyết định campaign tiếp.

**Success target:** chạy được ít nhất3Regular mã end-to-end đủ6families dưới
variants thực dụng đã khai báo, cóQA và replay; toàn12mã/72family rows đã phân
loại. Kèm bảng strict/recomputed cho biết mức practical đạt được nhờ nới gì.
Đạt target này không chứng minh CafeF đủ cho mọi mã hoặc cho1.000mã.

Nếu target không đạt, không bịa score hoặc hạ denominator: stage vẫn có thể
**hoàn tất kiểm chứng với kết luận thiếu có bằng chứng** sau khi các route hữu
ích đã thử trong cap, xuất giá trị thực đã có,gaps,effort,cost và hướng sửa khả thi.
Không coi “đã viết code/plan/report” là thay thế lần chạy live và metric output.

Chỉ đề xuất50 kế tiếp nếu parser/QA không còn critical unresolved error cho
templates địnhscale,3complete workflows đạt,phầnmissing không bị silent fill và
đã đo intervention cost. Báo explicit phầnmã/ngành chưa hỗ trợ. Không tựmở100,
canonical/research/financial cluster chỉ vì experimental practical profile chạy.

## 7. Budgets, thời gian và điều kiện dừng thật

[Plan JSON](../../configs/data/financial_cafef_revalidation_plan_v1.json) chốt cap
đề xuất:12mã,600logicalrequests/750transportattempts tổng,36PDFattempts trong
tổng,1GBdownload,8h từSTART kể cả nghỉ,timeout25s,spacing≥2s,≤2attempts/URL cho
transient errors,1000newOCRpages/250PDF/160batch. Structured≤3MB/PDF≤25MB.
Đây là **hạn mức**, không phải dự đoán cần8h hoặc quyền tự tăng khi hết.

401/403/429/challenge/login/paywall: latch và dừng theo source/campaign contract;
không proxy/cookies/đổihost để né. Network campaign cũ hết hạn hoặc latch không
được reset; tạo small-sample contract mới với lý do/scope/codepins và ghi cost riêng,
không xóa lỗi cũ. Vấn đề access cũ chỉ được kiểm lại nếu có căn cứ truy cập hợp lệ,
không tự đổiepoch để bỏ latches. Các tác vụ offline khác vẫn tiếp tục.

Agent làm quaR0–R5 khi được owner giao trọn plan, không dừng để xin “làm tiếp”
sau mỗi stage nhỏ. Đây là phạm vi nhiều checkpoint mà owner đang yêu cầu; giữ
single-agent execution, không spawn agent khác. Progress brief khi active, tránh
continuous polling long crawls. Chỉ kết thúc khi:

- Goal đã có kết quả và đầy đủ handoff; hoặc
- Hard access/budget/tool/input dependency thật sự chặn tiếp: ghi chính xác phần
  đãxong,pending,attempts,bằngchứng và lệnh resume/điều kiện cần thêm.

Không lặp discovery/source search vô hạn để theo đuổi100%. Với mỗi unresolved
cell, route chain đã thử+reason+next useful action phải đủ để agent khác không
lặp lại. Thời gian thực tế phải đo: network/OCR/QA/manual riêng,p50/p95 mỗi mã;
ước tính50/1000 theo template và cache-hit thực tế, không nhân tổng12mã mù quáng.

## 8. Files code/config cần tham chiếu

| Phần | File sẵn có | Cách dùng |
|---|---|---|
|Structured parser/URL|[cafef_financial_detail.py](../../src/delta_t1/ingestion/cafef_financial_detail.py)|`parse_detail`, `detail_url`; review header/unit/row assumptions.|
|Summary pilot|[cafef_financial.py](../../src/delta_t1/ingestion/cafef_financial.py)|Summary protocol và nguyên nhân không đủLCTT; không chọn riêng path này để kết luận nguồn.|
|CafeF50 orchestration|[cafef_financial_trial.py](../../src/delta_t1/experiments/cafef_financial_trial.py)|Routing,cache,coverage,QA; frozen config enforce4hoặc exact50, phải version mới để sample12.|
|Old structured CLI|[crawl_cafef_financial.ps1 — archived](../../artifacts/archives/project-cleanup-20261019-v1/inactive-files.zip), [Python — archived](../../artifacts/archives/project-cleanup-20261019-v1/inactive-files.zip)|Tham khảo launcher/feedback, không execute oldrun như new12.|
|Transport|[financial_trial_transport.py](../../src/delta_t1/ingestion/financial_trial_transport.py), [compact journal](../../src/delta_t1/ingestion/financial_compact_trial.py)|Durable reservations/caps/latches; reuse logic qua module mới, không bỏ guards.|
|PDF/manifest|[financial_documents.py](../../src/delta_t1/ingestion/financial_documents.py), [financial_batch_evidence.py](../../src/delta_t1/ingestion/financial_batch_evidence.py)|FileBCTC/verify/scope/source evidence; cache exact bytes.|
|OCR|[ocr_financial_pages.ps1](../../scripts/ocr_financial_pages.ps1), [analysis worker](../../scripts/analyze_financial_scale.py)|WindowsOCR,render và page locators; selected notes trước.|
|Current offline workflow|[financial_user_workflow.py](../../src/delta_t1/experiments/financial_user_workflow.py), [resume adapter](../../src/delta_t1/experiments/financial_resume.py), [launcher](../../scripts/financial_resume.ps1)|Review/PDF/page inputs và existing references; metadata compatibility trongsealedV3.|
|Calculators|[financial_reference.py](../../src/delta_t1/features/financial_reference.py), [VAS](../../src/delta_t1/features/financial_vas_reference.py), [TTM](../../src/delta_t1/features/financial_ttm_reference.py)|Giữ original APIs/variant names; nới thì calculator/adapter mới cótests, không đổi pinned behavior.|
|DATE_ONLY|[financial_date_pit.py](../../src/delta_t1/ingestion/financial_date_pit.py)|Keep strict historical path; practical flags riêng.|
|Existing configs|[source selection](../../configs/data/financial_source_selection_v1.json), [old trial50](../../configs/data/cafef_financial_trial50_v1.json), [current workflow](../../configs/data/financial_user_workflow50_v2.json)|Tham khảo source roles,targets,pins; không mutate frozen config để doctorpass.|

Đường dẫn mới đề xuất khi triển khai: `src/delta_t1/experiments/financial_cafef_revalidation.py`,
`scripts/financial_cafef_revalidate.py`, `.ps1`, `configs/data/financial_cafef_revalidation_run_v1.json`,
`tests/unit/experiments/test_financial_cafef_revalidation.py`,
`data/financial/cafef_revalidation12_v1/<run_id>/`,
`artifacts/reports/financial-cafef-revalidation12-v1/`.
**Các path mới này chưa có runner implement trong lượt lập plan.** Nếu tạo tên
khác, cập nhật execution-state/runbook và tránh nhiều wrapper gần giống nhau.

Tests tham khảo: `tests/unit/ingestion/test_cafef_financial_detail.py`,
`tests/unit/experiments/test_cafef_financial_trial.py`,
`tests/unit/experiments/test_financial_user_workflow.py`,
`tests/unit/ingestion/test_financial_date_pit.py`,
`tests/unit/features/test_financial_vas_reference.py`,
`tests/unit/features/test_financial_ttm_reference.py`.

## 9. Deliverables và Definition of Done

| Output | Nội dung bắt buộc |
|---|---|
|`source-audit.csv`|12mã×routes, actual periods/units/scope/HTTP/observedURLs/rawpins.|
|`field-coverage.csv`|Từng required field-period/source tier,found/mapped/QA/missing reason.|
|`metrics.csv`|72family rows cóstatus + variant rows riêng,value,unit,period/asof,basis,quality/publicationflags.|
|`metric-dependencies.json`|Mỗi value phụ thuộc fact/sourceSHA nào; current vs restated vsproxy tách.|
|`qa.csv`|Actual independent comparisons,quantizationtolerance,mismatches và resolution; sample size thật.|
|`exceptions.csv`|Source/parser/mapping/units/PIT/notes/sector/access/budget taxonomy và next action.|
|`policy-deviations.csv`|Rule nào nới,reason,variant,source evidence,ảnh hưởng output; strict counterpart giữ riêng.|
|`costs.json`|Requests/bytes/cache/OCR/mã,wall/network/OCR/manualminutes/retries; projection có caveats.|
|`report.md`|Source verdict,matrixcoverage với denominators riêng,actual example values,remaining gaps/scale decision.|
|`manifest.json`|Raw/code/config/reference lineage và checksums; không thêm pycache vào sealed runs.|
|`user-runbook.md`|Lệnh PowerShell đã test,doctor/run/resume/report/verify,exitstatuses,feedbackpackage.|
|`execution-state.json`|Goal/checkpoints/currentoutputs,remainingcost,nextaction; resume không suy từ chat.|

Giữ artifacts nhỏ: raw content-addressed,OCR/index dùng lại,logs append-only hợp lý;
không tạocopytree mỗi lầnresume. Chỉ prune cache khi không còntransitive references;
report không thay raw cần cho reproducibility. Cập nhật docs index/current/changelog/
DECISIONS đúng scope mới, không viết nhiều statusfile song song.

## 10. Prompt có thể giao nguyên văn cho agent

> Làm việc tại `C:\Projects\Intern\SourceCode-CafeF`, kiểm nhánh hiện tại
> `research/financial-data` và giữ thay đổi có sẵn. Đọc
> `docs/crawl/FINANCIAL_CAFEF_REVALIDATION_PLAN.md` và
> `configs/data/financial_cafef_revalidation_plan_v1.json`, sau đó đọc các tài liệu
> theo bảng “Đọc nhanh”. Tôi giao bạn thực hiện trọn R0–R5: kiểm chứng CafeF trên
> 12mã đã chốt, crawl thử thật có giới hạn, sửa flow/parser khi có evidence, lấy
> PDF/notes chỉ cho gaps, tính ra metrics thật và giao runner PowerShell/runbook.
> Tôi cho phép profile PRACTICAL_FINANCIAL_V1 và các nới lỏng có ghi tên/flags
> trong plan; không để PIT hoặc thiếu human-review từngcell chặn numerical work.
> Giữ STRICT_HISTORICAL_PIT/research/backtest và market-only độc lập, không giả
> missing thành0, không proxy thành originalscore, không bỏ mã khó, không bypass
> access hoặc reset expired budgets. Kết luận CafeF đủ structured,đủ nhờattachment,
> thiếu cầnnguồnngoài, hoặc inconclusive theo số đo, không theo giả định ban đầu.
> Làm liên tục qua checkpoints đến khi có outputs/QA/report/handoff hoặc blocker
> thật có bằng chứng; không dừng sau discovery hay xin “làm tiếp” mỗi bước. Ghi
> execution-state để resume, test phần thay đổi và synthetic smoke nếu sửa pipeline,
> cập nhật report/changelog. Không spawn subagent hoặc tự chạy cluster/100mã.
