# Chưa phát hành — Handbook chỉ số và dữ liệu cần crawl (2026-10-09)

- Thêm [handbook](docs/research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md):6financial families EPS/PE/PB/F/M/EMZ, công thức/ý nghĩa,9Fsignals/8Mratios, annual/TTM/share/event variants, raw-field dictionary với nơi lấy/unit/kỳ, source roles, publication/revision và QA/missing rules. Phụ lục11market features và8required features hiện có.
- Đối chiếu calculators/workflow/registry và primary papers; ghi rõ current M accruals dùngend-year assets khác average-assets paper, diluted calculator shared numerator và giới hạn TTM/bulk50 valuation. Không đổi implementation, methodology version hoặc financial gates.
- Nối START HERE/FEATURE_SYSTEM/financial contract/crawl runbook tới handbook; [report/worklog/self-review](artifacts/reports/financial-indicators-handbook-v1/report.md) lưu kiểm links, required-field coverage, synthetic examples và compile checks. Không acquisition/OCR hoặc promote data.

# Chưa phát hành — Publication discovery MWG/VHC (2026-10-08)

- Tìm official MWG post dates FY2025=23/03/2026/FY2024=24/03/2025 qua public API quan sát từ website; lưu HTML/JS/JSON/receipts/PDF evidence. Hash official khác cache, không apply date theo ticker/year. MWG2025 core46/46pages khớp, cache có thêm digital-signature widget; FY2024 resolution khác cần version review.
- VHC official2PDFs khớp SHA cache nhưng chưa ngày công bố; visually kiểm4pages giải trình và No85page1 có document date09/04/2025/publication10/04/2025. Signature không mặc định làm PIT; proxy chỉ đề xuất reference riêng.
- [Report/worklog/self-review](artifacts/reports/financial-mwg-vhc-publication-review-v1/report.md), stage integrity/compile checks và immutable evidence manifest. Không đổi production runtime, reviewed inputs, numerical counts, acquisition counters hoặc gates; cập nhật START HERE/CURRENT_STATUS/retention pointer.

# Chưa phát hành — Hoàn thiện F/M reference MWG/VHC (2026-10-08)

- Full OCR101trang trên hai FY2024 consolidated PDFs đã có; bounded exact-hash stage helper giữ budgets/locks/reservations/runtime, không acquisition/download mới. Thêm26facts/mã vào hai inputv2, support source SHA/page/locator riêng cho TA2023/owned-PPE depreciation2024; originals/v1/PDF/OCR cũ giữ nguyên.
- Tính MWG F4/9/M−1,417454 và VHC F7/9/M−2,863853; replay4EPS/Z values. Cohort24/300FY2025 referencecells(8%),8/50mã, EPS8/Z8/F4/M4/PE0/PB0; production0. F là VAS adaptation, M là sensitivity không classification threshold.
- Phân biệt current portion của long-term debt với noncurrent debt, owned-PPE depreciation với cash-flow total, ESOP issuance với repurchase. Provider50MATCH/22NO_PROVIDER/2VHC2024 sign-basis differences retained; không auto-accept canonical. Publication exact FY2025/supportFY2024 còn thiếu sau primary-web discovery; DATE_ONLY/PIT/gates không nới.
- [Report/worklog/self-review](artifacts/reports/financial-mwg-vhc-fm-review-v1/report.md); independent290pins/18Fsignals/16Mratios/8valuesPASS,23targetedtestsPASS/compilePASS. Giữ initial verification helper count-error log và kết quả sửa theoQA thật; cập nhật START HERE/CURRENT_STATUS/retention pointer. Không đổi plan/market-only/frozen config hoặc mở wave100.

# Chưa phát hành — Review template MWG/VHC financial50 (2026-10-08)

- Xác nhận user FullOcr46MWG/64VHCpages và templates đúng; review18ảnh PDF, tạo hai input riêng11facts/mã, giữ nguyên blank templates/PDF/OCR. Agent visual reference review, human acceptance pending.
- Chạy existing calculator4EPS/Z references; EPSrounded4774MWG/6319VHC, EMZ7.512196/11.957464. Balance2/2, provider18MATCH/4NO_PROVIDER_FIELD; FY2025matrix20/300referencecells trên8/50mã, production0.
- MWG interest tách phí thu xếp vay; VHC giữ caveat quỹ phúc lợi2025 chưa duyệt và EPS2024 trình bày lại. Publicationnull/F/Mnull, không nới PIT/formulas/gates.0new network/download/OCR.
- [Report/worklog/pins](artifacts/reports/financial-mwg-vhc-template-review-v1/report.md), source verification60filesPASS,23targetedtestsPASS/compilePASS. Lượt test đầu lỗi sandboxtemp giữlog; rerun workspace tempPASS. Cập nhật docs START HERE/CURRENT_STATUS và active-retention pointer.

# Chưa phát hành — Inspection user financial50 run (2026-10-08)

- Kiểm kết quả5 bước owner chạy:150listings,91PDF mới/109vintages,64OCR pages DGC/GMD; independent integrity1.354files/309sealedfolders PASS.0new numerical review;6mã/16ô FY2025 reference cũ giữ nguyên.
- Xuất [report và bảng từng mã](artifacts/reports/financial-user-run50-review-v1/report.md), source pins/errors/pending snapshot. Phân biệt123pendingPDF jobs với17attempts còn lại; timeout/404 và scope/vintage scheduling được giữ đầy đủ.
- Sửa ví dụ trong [user guide](docs/crawl/FINANCIAL_READINESS_USER_GUIDE.md):Limit đếm PDF, chạy riêng từng mã để tránh hai vintages chiếm hết batch. Không thay runtime code/frozen config/formulas/gates hoặc rerun network/OCR.

# Chưa phát hành — Financial local user workflow50 (2026-10-08)

- Thêm runner PowerShell/Python và config frozen50: doctor/plan/audit/acquire/extract/run/template/review/verify; FY2025 readiness300 ô, tài liệu2023–2025, cache đúng hash, cumulative transport resume/access latch và OS lock.
- PDF/text/OCR theo batch≤8 PDF/320 trang, tổng≤6.000 trang; durable reservations giữ chi phí khi gián đoạn. Receipt/report immutable, lỗi nguồn/extraction xuất riêng, không tạo source priority hoặc zero imputation.
- Human review template hỗ trợ supporting PDFs/publication per input; gọi calculator EPS/Z/F/M hiện có, giữ variant/basis và QA provider. PE TTM/PB/sector adapters chưa tự hoàn thiện; financial gates đóng.
- [Runbook user](docs/crawl/FINANCIAL_READINESS_USER_GUIDE.md), [report/worklog/self-review](artifacts/reports/financial-user-workflow50-v2/report.md). Kiểm thử30 targeted PASS; handoff offline cache/resume,16 trang OCR MWG và PHP replay PASS; full387/388 tests PASS với known M2 checksum error.

# Chưa phát hành — Financial scale validation frozen50 (2026-10-08)

- Kiểm CafeF listings/candidate diagnostics đủ50 mã,54 annual/history listings;62 physical requests/104.860.206 bytes mới,12 successful PDF records. Thêm bounded acquisition probe, isolated text worker và all50 assessment; không sửa pinned trial/integration modules.
- Chạy render/Windows OCR bằng code trên PHP/VCS/VEA/PAN:8PDF/294trang,401,766giây; generic header-pair/code-band parser đọc khớp27/35statement cells. Layout/note/publication review vẫn có phần thủ công.
- Review44facts:32provider matches,3VEA numeric differences,1PAN interest/issuance-fee semantic mismatch,8note inputs không có trong structured requirements. Tính4basicEPS +4EMZ references,4annualPE arithmetic; exact-PDF date-PIT PHP/PAN, VCS/VEA pending. Giữ fullF/M/TTM/PB null.
- Recovery PAN issuer attachment sauCafeF404; xác nhận SLS FYend30/06/2025 và SHSstandalone;SCS404/PLCHARD_STOP retained. Không followchallenge/guessURLs/relabelscope/fiscalyear.
- Xuất [report/worklog/self-review](artifacts/reports/financial-scale-validation50-v1/report.md), ledger/QA/costs/50-symbol assessment; bảo vệ active retention closure.207financial tests PASS, compile/synthetic/offlineverify PASS; fullproject gate giữknownM2-PREP checksum error. Không mở financialcluster/next100 hoặc thay plan/market-only.

# Chưa phát hành — Nối trial50 với reviewed financial references (2026-10-08)

- Thêm integration/CLI offline nối frozen50 candidate checklist với existing reviewed calculators/adapters; giữ exact evidence pins, output immutable và tách annual/TTM/book-event basis. Không truyền publication theo ticker/year, không crawl/PDF/OCR hoặc accepted HTML facts mới.
- Replay15 annual reference cells (FPT9/ACV6), thêm3 FPT TTM/valuation values; VNM/PVS ngoài50. ACV auxiliary PIT/history/TTM gaps và strict0/900 giữ rõ; không còn hiểu0/900 candidate flags thành0 dòng có thể tính tham khảo.
- Thêm regression tests về ngày không có giờ, future/scope/unit/vintage, metric independence, basis collision, controls và external evidence tamper; active retention pointer giữ integration cùng parents.57 targeted tests, compile/synthetic và offline verify PASS; full gate/log trong [report](artifacts/reports/cafef-financial-reviewed-integration-v1/report.md).
- Giữ financial/cluster/research/full-universe/next100 gatesfalse và plan năm giai đoạn; xuất per-symbol/task assessment, ledger, next-review-plan, worklog và self-review. [Lệnh offline](docs/crawl/README.md#nối-trial50-với-reviewed-references--08102026).

# Chưa phát hành — CafeF-first financial trial50 (2026-10-08)

- Thêm runner CafeF detail riêng cùng CLI/PowerShell doctor/plan/run/verify/feedback; giữ đúng frozen50 membership, nhánh CafeF và plan financial năm giai đoạn. Pilot4/replay giữ78 QA comparisons với72 matches/5 differences/1 unmapped, không tự acceptance.
- Chạy fresh50:600 base +120 gap requests,588/600 base parse được;12 HTTP302 ở BVH không follow redirect.720 attempts/162.610.642 bytes;1.646/1.950 wire statement-periods (84,41%), collection PARTIAL.30 reference cells FPT/ACV:29 matches/1 difference, không suy accuracy toàn50.
- Journal một durable hash-chain JSONL, global counters/deadline/access latch qua resume, OS epoch lock/latest-parent và rawSHA dedup/cache pointers; không tạo per-chunk folders hoặc copy raw parent. External reviewed reference pins cũng được kiểm ở handoff.
- Xuất1950 coverage rows,900 strict task-year checklists và exact notes/PIT/revision/sector queues;0 PDF/OCR mới,0 accepted facts/0 strict tasks-ready trong lượt50. Không mở100 mã hoặc financial cluster; market-only workstream giữ nguyên.
- Targeted24/24, compile/synthetic PASS; full snapshot345/346 PASS với frozen M2-PREP DECISIONS checksum error cũ. [Report/log](artifacts/reports/cafef-financial-trial50-v1/report.md), [PowerShell active](docs/crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md).

# Chưa phát hành — Financial paired source benchmark và cleanup (2026-10-08)

- Benchmark fresh9 mã, cùng targets,297 bounded attempts: CafeF164/186 wire statement-periods/78 MAIN requests; KBS98/186/213. CafeF72/78 numeric reference matches, KBS0/78 theo header; phát hiện213 cross-year signature alerts dù pageSize1, không relabel/merge.
- Thêm benchmark CLI/config, offline analysis và compact durable reservation/hash-chain journal; measured JSON parse nhanh hơn nhưng chưa vượt trội về usable data. Recommendation engineering CafeF detail primary candidate, KBS diagnostic; runner50 legacy chưa tích hợp và financial/cluster/research gates vẫnfalse.
- Cold archive71 inactive roots,53.833 files/642.498.767 bytes; ZIP224.764.886 bytes với member/whole SHA256, refresh active closure và source verification trước native PowerShell prune. Giữ84 active roots và sealed historical reports; restore exact bytes/pins, không reset trial epochs.
- Tests cho null padding/nonfinite/duplicates/sector/budgets/global boundary và retention tamper/source-change/Windows dependencies/restore; compile/synthetic smoke và full test logs giữ trong report. [Report/log](artifacts/reports/financial-source-benchmark-v1/report.md), [runbook](docs/crawl/README.md#financial-source-benchmark-và-retention--08102026).

# Chưa phát hành — Financial trial50 nguồn thật (2026-10-07)

- Chạy đúng nhánh CafeF,50/50 mã; annual150/150 và quarter150/150 responses parse được.409 requests/113.538.490 bytes, không đổi runner/config hoặc market-only protocol.
- Collection PARTIAL: cả150 quarter responses có duplicate periods,90 history responses thiếu Head; FY2025 wire coverage50/50, Q4/2025=0/50.8 PDF/604 text pages,555 low-text, PNJ404 và ba listing gaps được giữ evidence.
- Xuất phân tích theo mã/kỳ/task,900 strict task rows, report/log và source pins;0 accepted facts/0 task-ready/0cluster eligible. Next: quý/history contract, numeric templates/PIT/events và ledger/verify IO trước trial100. [Report](artifacts/reports/financial-crawl-50-live-v1/report.md).

# Chưa phát hành — Flow financial trial50 bàn giao PowerShell (2026-10-06)

- Thêm trial CLI/PowerShell doctor/plan/run/verify/feedback và executable config riêng, pin50 market members/nhánh CafeF; giữ runner pilot10 và market-only protocol.
- Global HTTPS ledger, request/attempt/byte/page reservations,4giờ deadline, epoch registry/OS lock và hard-stop latch giữ qua waves/resume. Annual targets2021–2025, quarter2024–2025, strict task checklist2023–2025; source header/sector/duplicate periods fail-closed.
- Thêm gap-driven history/PDF sample12 đa dạng templates, worker text bounded timeout, wire/field coverage,900 task-input rows và compact feedback ZIP. Scan pages vào review queue, không tự generalize OCR hoặc numeric acceptance.
- 13 new tests PASS qua targeted/full logs; full326/327, còn frozen M2-PREP DECISIONS checksum đã biết. Pilot14/14, PowerShell offline run/verify/feedback, cached exact-PDF73pages và compile/smoke PASS. Live50 chưa chạy; user chạy local và gửi feedback. [Report/log](artifacts/reports/financial-crawl-50-flow-v1/report.md), [runbook](docs/crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md).

# Chưa phát hành — Kế hoạch financial trial 50 mã (2026-10-06)

- Lập plan JSON và report chuẩn bị cho 50 ticker đã đối chiếu market snapshot 28/08/2026: 38 HOSE, 7 HNX, 5 UPCOM; proposed company types 40 Regular/6 Bank/3 Securities/1 Insurance cần source verification.
- Định nghĩa annual/quarter, 5 chặng, global budgets/hard-stop/resume, gap-driven PDF và tiêu chí engineering trước khi xem xét 100 mã; 300 requests cơ bản, tối đa450 gồm bổ sung.
- Validation offline và self-review PASS trong planning scope; chưa chạy network, sửa runner hoặc mở financial/cluster/full-universe gate. [Report/log](artifacts/reports/financial-crawl-50-plan-v1/report.md).

# Chưa phát hành — Financial batch automation/resume (2026-10-05)

- Thêm runner nối discovery/cache → PDF → text/OCR candidate → review queue → offline reference adapters. Checkpoint bất biến từng task, resume interrupted run và transitive receipt/manifest từ run gần nhất; verifier kiểm dependency ngoài run.
- Batch10 mã có10 PDF candidates/691 pages/32 unique prefix OCR pages; bổ sung6 PDF và6 CafeF listings, DGC404 được ghi riêng và tải official HTML/PDF candidate qua discovery độc lập. Giữ lỗi transport sandbox và replay lineage bug trong evidence; đã sửa bug và có regression test.
- Final replay không network/download/text/OCR hoặc checkpoint mới; hai adapter pilot và review queue tái lập.132 targeted financial tests PASS; full301/302, chỉ lỗi frozen M2-PREP checksum cũ. Compile/smoke PASS.
- FIN-D5 engineering validation có evidence nhưng accepted-data scale chưa mở;6 mã mới chưa numeric acceptance, không tăng financial score coverage hoặc sửa market clustering protocol. [Report/log](artifacts/reports/financial-batch-flow-v1/report.md).

# Chưa phát hành — Financial pilot VNM/PVS/ACV (2026-10-05)

- Bổ sung bảy PDF responses/sáu PDF unique và bảy HTML snapshots; VNM annual VAS 2025 có đầy đủ thuyết minh. Tái dùng annual/cache cũ, giữ inventory/hash và các bản revised/future riêng.
- Render/OCR 348 selected pages; nghiệm thu 158 annual reference facts qua visual review, không tự nhận OCR. ACV có trang xoay; reserve chưa estimate và diluted shares chưa xác minh giữ unknown.
- Thêm bounded offline runner, calculation-source pins, per-cell PDF/image/revision provenance, accounting/EPS QA, deterministic replay và basic-only disclosed EPS reference.
- Có 17/18 annual metric cells với arithmetic: F VAS PVS=7/ACV=4, VNM total null (8/9 signals); M sensitivity/Z/EPS/annual valuation trên ba mã. VNM reported TTM EPS≈4.727,57/P-E≈13,18 có mirrored publication, strict production vẫn zero.
- Hai CafeF quote pages riêng cho VNM/PVS tại 28/08; không sửa market canonical hoặc clustering. PVS prior-profit/share restatement và ACV future reviewed H1 tiếp tục fail-closed. [Report/log](artifacts/reports/financial-three-symbol-pilot-v1/report.md).

# Chưa phát hành — FPT financial acceptance và ESOP gross bridge (2026-10-04)

- Đối chiếu hai xác nhận ngân hàng: tiền ESOP 108.193.010.000 VND khớp số cổ phiếu và tăng vốn đăng ký. Tải thêm thông báo đăng ký doanh nghiệp và BCTC riêng bán niên; giữ publication/effective dates riêng.
- Thêm OCR các khoảng trang rời trên cùng PDF để bỏ qua danh sách nhân viên; 49 trang OCR mới, exact-image/PDF hashes. Hai PDF mới có 46 trang; tái dùng bank attachments đã tải.
- Thêm offline gross-capital P/B reference và acceptance runner tổng hợp sáu nhóm F/M/Z/EPS/PE/PB, giữ annual/TTM/book-date basis riêng. P/B gross bridge 28/08/2026 ≈ 3,1404; phí và cash classification chưa xác minh không thành zero hoặc liability fact.
- Execution plan v6 trỏ final acceptance_v5; strict task matrix và mọi production/scale gates giữ nguyên. [Report](artifacts/reports/financial-fpt-acceptance-v2/report.md).

# Chưa phát hành — FPT TTM và share-event reference (2026-10-04)

- Tải 14 issuer PDFs, index 272 pages và OCR 50 trang chọn; đối chiếu EPS H1 2025, ESOP/bonus amendments và FTEL scope. Giữ raw và runs cũ.
- Thêm offline TTM calculator dùng reported numerator/calendar share-days; ledger tách actual issuance, kế hoạch, cash dividend và các loại ngày. Không cộng EPS quý hoặc biến reserve chưa ước tính thành zero.
- FPT từ 24/08/2026: TTM EPS reference ≈ 5.570,36 VND/share. Tại 28/08: P/E ≈ 13,14; current-share/latest-reported-equity P/B ≈ 3,15. Strict normalized TTM và event-adjusted P/B vẫn null; registry riêng không cluster eligible.
- Sáu accounting bridges và 13 artifact checks PASS; final runs v2/v3 deterministic. Task/readiness matrices cũ giữ nguyên; production/full-universe gates đóng. [Report](artifacts/reports/financial-ttm-valuation-v1/report.md).

# Chưa phát hành — Financial source research và VAS references (2026-10-03)

- Thêm15 KBS JSON responses trên FPT/VNM/PVS/ACV và offline normalizer4.796 wire cells. VCI403 hard-stop; EPS unit/revision exceptions giữ riêng, provider dates không thành PIT.
- Hai FPT2026 Q1/H1 PDFs, OCR80 scanned pages; thêm17 annual observations và13 H1 facts reviewed riêng. H1EPS2.967 dùng từ24/08/2026; FTEL scope/reserve/share bridge chặn latest TTM.
- F-score VAS2021–25=4/6/6/7/3, M owned-PPE/receivables sensitivity, reported P/E/P/B20/03/2026≈14,30/3,48. Strict F/M vẫnnull, event coverage pending; registry riêng không cluster eligible.
- Exact-PDF correction hai ô CFO/noncurrent debt2024; rebuild readiness v12=153, datev6=138, taskv8=0/120. Giữ bad observations/excluded lineage.
- Final source_completion_v4/v5 byte-identical; targeted/compile/smoke PASS, full-suite còn lỗi frozen M2 DECISIONS checksum. Không sửa market protocol hoặc mở scale. [Report](artifacts/reports/financial-source-research-v1/report.md).

# Chưa phát hành — FPT EPS revision và F-score reference (2026-10-03)

- Thêm 15 reviewed observations: bốn EPS2024 restated inputs/printed reference, sáu original-maturity loan/finance-lease mappings và năm parent-issuance indicators. Giữ original và revised EPS ở hai exact PDF vintages.
- Config v2/reference flow v9: 25 OCR numeric cells và bốn accounting bridges PASS, review queue zero; EPS2024 4.944 trước 20/03/2026, 4.292 sau đó; EPS2025 5.216. Diluted revised EPS có original no-dilution evidence và bonus-share bridge.
- Offline F-score calculator xuất từng signal; FPT2024/25 có 6/9 known, total null vì strict ordinary earnings chưa reconciled. Không dùng net-profit proxy, không mở financial/research hoặc full-universe gates.
- Pilot readiness v11 đạt 150/1.176 verified cells; date overlay v5 có 135 date references; task readiness v7 vẫn 0/120 production-ready. Report và kiểm chứng: [financial-revision-fscore-v1](artifacts/reports/financial-revision-fscore-v1/report.md).

# Chưa phát hành — FPT executable reference flow (2026-10-03)

- Thêm coordinate OCR table parser, exact-PDF template config, EPS/EM-Z Decimal calculators và offline orchestration CLI từ immutable cache tới QA/PIT/provenance/results.
- FPT2024/25: 22 numeric cells match reviewed evidence, bốn accounting bridges PASS, review queue zero. EPS gốc 2024/25 round 4.944/5.216 VND/share; EM Z reference 6,843186/7,106292.
- Giữ same-PDF inputs, fail-closed trước ngày khả dụng/mixed-vintage/unproved dilution/denominator invalid. Revision alert chặn EPS2024 cũ từ 20/03/2026 vì comparative EPS 4.292 chưa mapped.
- Latest reference_flow_v6: 5 QA-pass executions (4 unique task-years), 6 unavailable, 1 revision blocked, 24 F/M/PE/PB outside reference calculators. Replay v5/v6 deterministic; không thêm value coverage hoặc mở feature/research gate.
- Chín targeted tests/compile/synthetic smoke PASS; full suite 226/227 PASS, lỗi frozen M2-PREP DECISIONS checksum đã biết. Reference registry riêng cluster_eligible=false, market default registry không thay đổi. [Report](artifacts/reports/financial-reference-flow-v1/report.md). FIN-D2 reference slice đạt trong scope; tổng FIN-D2 PARTIAL, scale chưa mở.

# Chưa phát hành — FIN-D3 date-PIT và FIN-D4 publication discovery (2026-10-03)

- Theo owner approval, triển khai DATE_ONLY cho daily/monthly: dùng từ phiên exchange quan sát được đầu tiên sau ngày công bố; không tạo giờ giả. Thêm policy v1/date overlay/as-of selector và evidence policy v2, giữ nguyên score variants.
- Visual-check explicit publication trong 10 exact PDFs: FPT 2019–2025, PVS 2024–2025, ACV 2025. Giữ 11 publication exceptions và revision history chưa đóng.
- OCR thêm 30 prefix pages PVS/ACV; phát hiện PDF provider gắn ACV 2022 thực chất VEAM. Hash quarantine được verify và loại khỏi readiness/workflow, raw giữ nguyên.
- Thêm 17 FPT observations và tám accounting QA PASS; sửa fixed_assets INSTANT. Latest readiness v10: 139 verified; date overlay v4: 124 cells có date reference. FPT Z 2024–2025 đạt 7/7 và EPS 2021–2025 đạt 3/3 value/date inputs; chưa feature/score acceptance.
- Workflow v6 reuse 488 OCR pages/26 annual candidates, 1.224 queue cells và 140 external requirements. FIN-D2/3/4 PARTIAL; FIN-D5 pending.
- 28 financial targeted tests/compile/synthetic smoke PASS; full suite 217/218 PASS, lỗi M2-PREP frozen DECISIONS checksum đã biết. [Report](artifacts/reports/financial-date-pit-v1/report.md).

# Chưa phát hành — FIN-D2 workflow và FPT mapping continuation (2026-10-03)

- Thêm bounded offline workflow planner/CLI/field recipes; deduplicate field-year dependencies, nối document inventory/OCR hints, route acquire/extract/mapping/conflict/publication và tách external temporal requirements.
- Four-symbol queue v4: 1.224 unique cells/140 external requirements, reuse 460 OCR pages/27 annual PDF candidates; VNM full-VAS gaps giữ riêng.
- Review thêm 40 observations, 7 QA records PASS; reconcile EBIT FPT 2024–2025, phân biệt parent ESOP/stock dividend/NCI funding và equity400/410.
- Overlay v7 có 135 verified/PIT-pending; FPT Z annual presence 2024–2025 đạt 7/7, EPS 2021–2025 giữ 3/3. Chưa score/PIT promotion.
- 3 tests mới; 22 financial targeted tests/compile/synthetic smoke PASS. Full suite 211/212 PASS trước final gap/cap hardening, một lỗi immutable M2-PREP DECISIONS checksum cũ. Report: artifacts/reports/financial-workflow-v1/report.md; FIN-D2 PARTIAL.

# Chưa phát hành — Financial execution plan và FPT notes/publication (2026-10-03)

- Lập FIN-D1 → FIN-D5 trong unified plan/config; triển khai task matrix 120 rows cho F/M/Z, EPS recompute, P/E và P/B. FIN-D1 COMPLETE; FIN-D2/FIN-D3 PARTIAL; FIN-D4/FIN-D5 pending.
- Thêm bounded note OCR extractor/CLI và FPT publication-card parser; OCR thêm 352 trang, tổng 658. Sáu original annual PDF 2019–2024 và original audited 2025 đều có OCR đủ trang, chưa đồng nghĩa tất cả values verified.
- Thu listing chính thức và PDF kiểm toán FPT 2025; giữ 57 dated disclosure cards và exact attachment hash với ngày 19/03/2026, DATE_ONLY, available_at null.
- Review thêm 82 observations EPS/PPE/debt/expense/shares; bảy annual EPS rounding checks PASS. Debt/PPE candidates giữ semantics riêng, chưa alias thành score inputs. FPT EPS annual input presence 2021–2025 đạt 5/5, PIT/valuation chưa ready.
- Overlay v6: 133 document-verified/PIT-pending, 703 raw-unverified, 286 note-review, 54 missing trên 1.176 ô; task matrix v3 giữ task_ready false và computed_value null.
- 21/21 targeted tests sau final code change, compile và synthetic smoke PASS; full suite trước final instant-field extension 208/209 PASS, còn lỗi immutable M2-PREP DECISIONS checksum đã biết. Exact inventories và evidence hashes PASS. Report: `artifacts/reports/financial-execution-v1/report.md`.

# Chưa phát hành — FPT annual core và pilot readiness (2026-10-03)

- OCR thêm 108 trang thuộc sáu annual scan FPT 2019–2024; hoàn thành 49/49 ô annual core 2019–2025 với visual/PDF/page/hash evidence.
- Đối chiếu bảng chính/thuyết minh FPT 2025, cổ phiếu và debt candidates; giữ reclassification FPT 2020 và EPS revision 2024 riêng theo document vintage.
- Thêm offline readiness analyzer/CLI, stage contract và 5 tests; overlay v4 có 107 document-verified/PIT-pending, 713 raw-unverified, 302 note-review, 54 missing trên 1.176 ô.
- Phát hiện/sửa đơn vị hai EPS earnings numerators bằng correction run mới; không mutate evidence cũ. Xuất 180 F-Score dependencies, mọi score/PIT promotion vẫn null/false.
- Compile, 5 tests và synthetic smoke PASS; full suite 202/203 PASS trước final hardening, còn lỗi M2-PREP DECISIONS checksum đã biết. Report: `artifacts/reports/financial-pilot-closure-v1/report.md`; stage PARTIAL.

# Chưa phát hành — Financial document evidence và definition contract (2026-10-03)

- Tham khảo literature B6/B7 và primary sources, khóa mục tiêu annual consolidated non-financial: F Table-1 average-assets turnover, M 2013 cash-flow variant và EM Z-double-prime có intercept; EPS/P-E/P-B giữ share basis/vintage, thiếu input trả null.
- Thêm bounded all-vintage annual/gap collector, explicit issuer/public-mirror supplement, PDF text indexing, Windows OCR và annual field checklist; không mở financial PIT/canonical/calculators.
- Crawl thêm 30 PDF + một issuer listing HTML; index 41 PDF/3.101 trang, OCR 198 trang thuộc 11 gap PDF. Đối chiếu trực quan thêm 85 fact, tổng evidence 130 fact observations; 10 arithmetic/accounting checks PASS.
- Có annual document candidates 24/28 mã-năm cho 2019–2025; Vinamilk 2019/2020/2021/2025 còn thiếu full VAS. Annual report VNM 2025 bổ sung chứa bảng IFRS và VAS audit extract, không thay được full VAS.
- Checklist 1.176 mục: 813 raw-present, 55 missing, 308 note-review-required. Report v2 ghi exact runs, failures, reproducibility, quyết định và acceptance còn thiếu.
- Financial targeted 30 tests PASS; full suite 197/198 PASS, một lỗi immutable M2-PREP checksum DECISIONS đã biết; compile và synthetic smoke PASS. Giữ snapshot cũ bất biến.

# Chưa phát hành — Financial detail remediation (2026-10-03)

- Thêm bounded full-statement collector/parser/CLI cho CafeF BSheet/IncSta/CashFlow, giữ raw text, period anchor, codes và hashes; nested charts không vào facts.
- Execute four-symbol 2021–2025 pilot; thêm local gap-document download, field inventory, candidate CSV và summary/detail numeric comparison không resolve canonical.
- Khôi phục ACV annual 2021 qua detail path; giữ quarterly blank gaps và tải được PDF cho 11 unique gap periods. QA 45 sample PDF facts, weighted shares và EPS version differences; chưa full OCR hoặc PIT promotion.
- Tạo report tại `artifacts/reports/financial-remediation-v1/report.md`, cập nhật active financial handoff/source note và thêm 10 parser/transport/verification tests.

# Chưa phát hành — Financial raw coverage pilot (2026-10-02)

- Thêm `cafef_financial.py`, bounded pilot config và CLI dry-run/execute/offline verify trong nhánh CafeF.
- Lưu raw response, metadata/hash, code/config snapshots và coverage theo mã/kỳ/loại báo cáo; phân biệt missing group, empty boundary, lỗi phân trang và cap.
- Giữ financial `PIT_UNRESOLVED`, không thay canonical schema hoặc bật financial features/calculators.
- Thêm regression tests cho null/zero, annual quarter zero, identity, missing LCTT, duplicate pagination, access stop, caps và raw tampering.

# Chưa phát hành — Post-M1 documentation alignment (2026-09-26)

- Ghi nhận C8 `EXECUTED_AND_VERIFIED`, R1 `COMPLETE` và M1-REPORT `COMPLETE FOR MARKET-ONLY EXPERIMENT PREPARATION`; giữ strict research gate `NOT READY`.
- Đồng bộ active docs với CafeF `TradeHistoryNew`, snapshot `2026-08-28`, 952 candidates, 922 feature-complete, 905 market-ready, 47 failures, 148 deferred và identity/research readiness bằng 0.
- Tách `market_experiment_eligible(t)` theo từng snapshot khỏi legacy `eligibility`, `historical_identity_ready` và `research_ready`; 905 không phải terminal-universe filter.
- Chuyển exact next stage thành M2-PREP để freeze protocol trước clustering; monthly readiness discontinuities phải được giải thích trước window freeze.
- Không đổi code, data, methodology behavior hoặc scientific result; không crawl, clustering hay backtest.

# Chưa phát hành — R1 repository consolidation (2026-09-25)

- Hợp nhất active tree sau C8-VERIFY: retire 192 file planning/history/config/runner/module/test superseded và đổi tên một test theo scope CafeF active; Git history là archive, không tạo archive copy.
- Giữ nguyên heavy C8 artifact, compact C8-VERIFY evidence, năm source ZIP, C8/C7/C5 lineage và mọi methodology/result.
- Giữ active C8 verification, expansion/supplemental recovery contracts, CafeF semantics, generic research/product paths và compatibility tối thiểu còn được import.
- Thêm machine-readable before/after/deletion inventory cùng offline R1 verifier tại `artifacts/repository/r1-consolidation-v1/`.
- Không network crawl, supplemental acquisition, C8 rerun, clustering hoặc backtest.

# Chưa phát hành — REPRESENTATIVE_PILOT readiness (2026-09-16)

- Chuẩn bị C8 complete-only: fail-closed scope 500 baseline + 452 COMPLETE expansion,
  ghi riêng 148 `DEFERRED_EXPANSION_ACQUISITION`, thêm offline normalization/audit/
  feature runner với snapshot 2026-08-28 và independent full-history/latest-253 audits.
  Thêm `docs/CURRENT_STATUS.md` làm canonical active handoff. Heavy C8 chưa chạy;
  supplemental crawl, clustering và backtest đều không chạy.

- Chuẩn bị C6 CafeF expansion: freeze pre-crawl 600 mã mới + reserve 100 sau current-500/reviewed-alias exclusion; tạo năm shard cân bằng, acquisition-only runner với exact resume/immutable raw, one-ZIP packager, central tamper verifier và PowerShell worker runbook. Không chạy long crawl, normalization, clustering hoặc backtest.
- C6-R1 sửa observation semantics để mọi null component không bị hiểu thành zero; runner yêu cầu external exact commit SHA trước dry-run/execute/resume, run/handoff ghi actual HEAD, packager chặn dirty/mismatched commit và central verifier chặn old/new/mixed commits.
- C6-R2 giữ nguyên universe/reserve/năm shard và mở rộng frozen CafeF acquisition range thành `2020-01-01 → 2026-09-23`; bump execution contract lên `c6-cafef-expansion-v2`/`BASE_2020`, recompute estimate/hashes offline và giữ provider boundary trung tính, không fabricate history.

- Thêm C3-R1 CafeF canonical market pilot: chấp nhận `GiaDieuChinh` làm
  `vendor_adjusted` research proxy, giữ raw OHLC staging-only, null-safe total activity,
  11-row quarantine, pilot identity/calendar/VNINDEX reuse và đúng một bounded benchmark
  request. Canonical schemas/relations PASS với 33.248 price rows, nhưng stage giữ
  `PARTIAL_MANUAL_REVIEW_REQUIRED`: CafeF thiếu sessions trong cửa sổ 253 phiên nên
  `mom_252` và `market_feature_ready` đạt 0/27; không fill hoặc hạ required-feature gate.

- Hoàn tất offline CafeF C1 hậu crawl/C2/C3 cho pilot 27 mã: 27/27 raw audit PASS,
  33.259 normalized market candidates, 11 provider rows cần quarantine và hai identity
  intervals CTR/SHB không có observation. C3 dùng CafeF self-sufficiency audit theo
  owner decision, không chạy KBS comparator; kết quả `PARTIAL_MANUAL_REVIEW_REQUIRED`
  vì price basis, corporate actions, calendar, benchmark, shares và financial PIT chưa
  đủ cho canonical. Không network, canonical mutation hoặc feature rebuild.

- Tạm thời gỡ repository-level multi-agent Codex orchestration. DELTA dùng single-agent session do người dùng chọn model, self-review và one-stage execution.

- Corrective A5 recovery semantics: CafeF ratio `MATCH` chỉ là diagnostic evidence, không phải canonical acceptance. CafeF OHLC/price-basis contract vẫn fail-closed; cấm zero-return/forward-fill/previous-close/missing-to-zero và không canonical-mutate baseline. A5 chuyển sang remediation gate A5-R1 trước khi B0 được phép bắt đầu.

- Sửa M1 correctness semantics: feature snapshot 1.5 tách feature completeness, market-feature readiness, historical-identity readiness và strict research readiness; identity `provisional` vẫn hiển thị/fail historical research nhưng không tự làm market feature false. M1 QC đổi “usable 3y/5y” thành observed span, thêm session-density/reason distributions và chọn latest completed month (không coi partial 15/09 là month-end). Bỏ implementation-only gate >=300 same-date complete features vì frozen requirement là >=300 collected long-history securities; research sample-size/density policy giữ `UNRESOLVED`, identity/financial PIT tiếp tục fail-closed. Raw/candidate/legacy artifacts không bị sửa và offline regeneration có `network_requests=0`.
- Merge đủ 5 M1 scale handoff/500 mã bằng offline checksum replay; hỗ trợ frozen text LF/CRLF-equivalent nhưng giữ resume strict, exact stored job plan và exact manifest jobs. Central QC quarantine KBS/CafeF constraint violations kèm raw path/hash, không repair raw hoặc canonical-merge. Clean mapping giữ 500/500 mã >=3 năm và 484/500 mã >=5 năm. Thêm reproducible offline EDA/QC report với per-symbol coverage/missing-feature evidence; feature promotion vẫn fail-closed vì latest feature-complete chỉ 168/500.
- Thêm M1 scale multi-machine path cho 500 mã/5 collectors: frozen universe 500 mã đều có bounded evidence >3 năm, deterministic 5×100 assignments, zero-network/execute/resume shard runner, exact union/disjoint/checksum handoff verifier, central canonical mapper/promoter và single-pass market feature build. Range chung 2020-01-01..2026-09-15; gate theo usable >=3 năm, còn usable >=5 năm là reporting metric. Pilot 50–60 guard giữ nguyên; chưa chạy real scale network.
- Hoàn tất real acquisition `representative-pilot-20260916T185530Z-410ffcba` với 839/839 jobs; offline immutable QC replay zero-network PASS, 55/55 mã usable >=5 năm và VNINDEX PASS.
- Thêm versioned exact-hash QC policy: quarantine 51 provider invariant violations, không repair raw; mismatch hoặc rule thiếu/thừa đều fail-closed.
- Khóa KBS primary >=5 năm và CafeF auxiliary non-empty/partial source-qualified; 6 volume conflicts vẫn unmerged, financial PIT vẫn unresolved. `M1_SCALE` chỉ unlock cho planning, chưa chạy.
- Thêm offline canonical-readiness mapper cho frozen 55-symbol pilot: market-table mapping/schema/lineage PASS nhưng promotion fail-closed khi thiếu company name và historical identity intervals; không fabricate raw OHLC hoặc metadata.
- Thêm versioned 55-symbol security master từ KBS direct public metadata và hash-verified promotion từ immutable candidate: canonical pilot có 55 securities, 91.768 prices, 4.455 monthly market snapshots, latest eligibility 55/55 và generic QC 0 issue/quarantine. Identity chỉ `PILOT_OBSERVED_INTERVAL_ONLY`/`provisional_verified_for_pilot`; không overclaim complete historical universe, financial PIT vẫn khóa.
- Pre-execution hardening: raw replay dùng cùng position-aware CafeF snapshot exclusion với acquisition; pagination phân biệt empty/partial source exhaustion, real max-pages, repeated/overlapping/non-progressing pages và phát diagnostics đầy đủ.
- Thêm explicit mapping-diagnostic v2 policy: checkpoint CafeF source exhaustion để full crawl đi tới final QC, nhưng bắt buộc final gate FAIL và liệt kê `reference_source_exhausted_symbols`; không che coverage hoặc nới official PASS.
- Thêm offline raw-corpus preflight kiểm tra checksum/schema/replay/pagination/coverage mà không gọi network hoặc sửa raw evidence.
- Micro-hardening resume: chỉ nhận immutable `REAL_EXECUTION` run cùng `run_id`, verify stored job-plan hash/content và exact manifest job set/definitions trước khi tạo network client; dry-run không thể promote/resume thành real.
- Hardening cuối: real acquisition bắt buộc explicit `--execute`; no-mode, mixed mode và resume không kèm execute đều fail-closed.
- Khóa resume bằng exact config/universe/source-gate/code/job-plan hashes cùng KBS/CafeF adapter versions; cấm mixed-version resume và không migrate run cũ.
- Thêm official pilot runner/config/universe contract dùng đúng KBS direct public HTTP + CafeF direct; dry-run zero-network không thể emit PASS gate hoặc unlock scale.
- Chặn official gate khỏi legacy Vnstock SDK collector; giữ collector cho <=5-symbol reference experiments.
- Tách market pilot gate khỏi financial PIT: `PIT_UNRESOLVED` không chặn market readiness nhưng bắt buộc `financial_features_allowed=false`.
- Sửa volume classifier: chỉ exact equality/documented mapping mới xác định semantic; ACV là `UNRESOLVED`, giữ `KEEP_SOURCE_QUALIFIED`, không merge.
- Chuẩn bị immutable run/job/manifest/gate layout, resume hash guards và pilot gate chỉ unlock `M1_SCALE` sau future real evidence.
- Validation: 137/137 tests, compileall, synthetic smoke và zero-network pilot dry-run pass; GitHub CI không chạy; không thực hiện real pilot.

# Chưa phát hành — M1 Data V2 runtime reset (2026-09-16)

- Cho phép bounded private research/demo collection trên public CafeF/KBS paths theo owner-accepted risk; rights vẫn `RIGHTS_NOT_VERIFIED`, raw không redistribution và production vẫn yêu cầu licensed source.
- Thêm adapter CafeF historical limits/value, KBS/Vnstock OHLCV, financial `RAW_ONLY_PIT_UNRESOLVED`, config và runner cho đúng bốn mã SOURCE_SMOKE.

- Retire legacy runtime `data/` và generated `artifacts/` khỏi active workspace.
- Khôi phục `/data/` và `artifacts/` vào Git ignore.
- Xóa legacy product path assumptions; launcher chỉ dùng explicit config và existing bundle.
- Giữ historical KBS/Vnstock lessons trong documentation, không giữ runtime evidence.
- Active M1 data lifecycle bắt đầu lại từ source discovery và `SOURCE_SMOKE` mới.

# Chưa phát hành — M1 readiness correction (2026-09-16)

- Chuẩn hóa future artifact ID thành `<prefix>-YYYYMMDDTHHMMSSZ-xxxxxxxx` qua một helper trung tâm; giữ compatibility với mọi old immutable ID.
- Thêm local `data/ACTIVE_INDEX.json` và archive manifest; move ba unreferenced synthetic technical artifacts vào `data/archive/legacy-20260916/` mà không xóa hoặc đổi tên real/referenced evidence.
- Thêm optional canonical contract `shares_history`, generic reconciliation key và QC cho security relation, non-empty counts và availability timing; không thay legacy Vnstock promotion.
- Bổ sung discovery/smoke documentation cho capital structure với explicit availability status; chưa crawl hoặc discover endpoint thật.
- Thay gate pilot cũ bằng `SOURCE_SMOKE`, `REPRESENTATIVE_PILOT`, `M1_SCALE`, `EXTENDED_SCALE`; synthetic không thể mở gate thật và extended planner không còn cap 350.
- Đổi tên config thành `synthetic_smoke.example.json`, thêm `source_smoke.example.json` fail-closed không chứa endpoint giả và thêm hướng dẫn collection/handoff nhiều người.
- Nâng market/feature contract lên 1.4: thêm reference/ceiling/floor theo VND/share và loại Sharpe khỏi active feature snapshot; giữ read-only legacy 1.3 compatibility.
- Chuyển reconciliation sang field level với bảy trạng thái match/conflict, semantic financial report key, canonical report identity và decision records có raw hashes.
- Thêm boundary `portfolio_evaluation.enabled`; M2 configs mặc định không sinh backtest/performance.
- Viết lại Literature Matrix thành 22 row riêng với đúng năm cột; field chưa full-text review ghi `PENDING — FULL-TEXT REVIEW`, giữ rõ conflict lịch sử về Sharpe và nhóm F chưa approved.
- Không thực hiện real crawl, storage migration, DBSCAN hoặc Dynamic Clustering.
- Acceptance: baseline 70/70, sau thay đổi 83/83 tests pass; synthetic smoke `run-c10574e177a6` và M2 no-portfolio experiment `experiment-8ecc8caa6dd9` complete.

# Chưa phát hành — refactor kiến trúc DELTA (2026-09-15)

- Tái xác lập DELTA là project Research Core + Product Layer theo milestone M1/M2/M3.
- Tạo documentation onboarding tiếng Việt, Project Map, Roadmap, feature/method/evaluation/product/reproducibility contracts và research review structure.
- Hợp nhất nội dung tài liệu superseded; thay `DEVELOPMENT_RULES.md` bằng `CONTRIBUTING.md` và viết lại `AGENTS.md` cho automated agents.
- Giữ `docs/data/kbs_pilot_semantics.md` tại path cũ vì immutable evidence có thể tham chiếu.
- Tách research runner thành `experiments/protocol.py`, `runner.py`, `artifacts.py`, `reporting.py`; orchestration resolve algorithm qua registry thay vì hard-code K-Means.
- Tạo common clustering interface/registry, Ward comparator và `dynamic/base.py` guard; tách cluster, temporal và portfolio metrics thành ba module độc lập.
- Chuyển Vnstock adapter/verification vào `ingestion/sources`, thêm CafeF/VietFin fail-closed interfaces và nối legacy promotion qua normalization/reconciliation generic có conflict records.
- Tổ chức config theo data/features/experiments/product; thêm PCA snapshot preprocessing và `pca_kmeans.example.json` không fit future/holdout.
- Migrate test suite sang unit/integration/regression theo subsystem, giữ assertion cũ và bổ sung invariant tests; acceptance đạt 70/70 tests, compile/JSON/link/web/diff checks pass.
- Synthetic smoke `run-5016b877990c` và PCA+K-Means technical experiment `experiment-85dd31d7598b` complete; không xem đây là research result.

# 0.5 — product-first restructuring (2026-09-14)

- Reframe the repository as Delta Intelligence: company/ticker intelligence is the product surface and clustering is one bounded analytical capability.
- Add immutable company-detail bundle builder, safe file repository, read-only API edge and responsive web shell.
- Preserve missing fundamentals/news/sentiment as explicit unavailable states; never fabricate zero values.
- Add product requirements and API v1 contract; rewrite architecture and execution plan into product and research tracks.
- Make direct-file opening show a styled server-required message, add one-command PowerShell launcher, and keep asset URLs valid under both file and HTTP contexts.
- Remove superseded KBS unresolved/smoke config and reports whose referenced raw runs were already removed.
- Repair the retained real-pilot latest pointer after generated-data cleanup.
- Consolidate 25 scattered documentation files into a canonical 9-document set plus index and one immutable-manifest evidence file; remove duplicate audits, phase reports, drafts and empty templates.
- Remove legacy real/offline pilot entry scripts and configs; extract the only reused benchmark-calendar helper into the generic ingestion layer.

# 0.4 — research realignment foundation (2026-09-14)

- Add a framework decision report: research framework is not final-standard, engineering core is reusable; recommend `RETAIN CORE / ARCHIVE LEGACY / REBUILD RESEARCH LAYER` rather than deleting the whole repository.
- Re-read the complete 1,266-line instruction attachment and 74-line paper list; revise the roadmap around all 22 papers and their stated purposes across groups A–E. Correct the evidence status: only Aslam is locally full-text reviewed; Han/Nanda/DBSCAN have primary partial review, while the remaining listed works still require full-text review.
- Clean reproducible generated data: remove obsolete synthetic runs/experiments/canonical/offline-pilot outputs, temporary PDF/test extraction, one interrupted vendor run and one incomplete real-pilot folder; retain complete real source/pilot evidence and the referenced regression run.
- Audit leader requirements against local research PDFs, reading list, code, configs, artifacts and Git state; verdict `MAJOR REALIGNMENT REQUIRED`.
- Document that current implementation is a monthly snapshot K-Means baseline, not an Aslam (2025) replication or approved Dynamic Clustering method.
- Enforce three calendar years observed history for real clustering; add eligible/reference/excluded segments and coverage.
- Prevent Sharpe/ROI from clustering inputs and selection; retain Sharpe as portfolio-performance metric.
- Add optional quarterly financial report/fact PIT contracts and percentage/top-N universe capability.
- Add source comparison, reconciliation design, dashboard contract, deliverable folders and P0–P2 roadmap. No large crawl, rename, remote change or commit was performed.

# 0.3 — real KBS pilot (2026-09-12)

- Resolve SDK 1000x price conversion using source/API and independent FPT price; detect vendor historical technical adjustment instead of mislabeling raw.
- Promote explicit vendor_adjusted convention; support raw-close features/backtests when unadjusted mapping is justified.
- Add retrospective availability safety delay, bounded provisional master, benchmark-derived calendar, nullable turnover and assumed rf.
- Add real-pilot runner, 10-symbol 2023-2025 config, source snapshots, lineage and acceptance evidence.
- Add conversion, optional-field, corrupt-OHLC, raw-feature and calendar tests.
- Remove unused Protocol interfaces/app/notebook placeholders; retain old raw evidence and test fixtures.

# Nhật ký thay đổi

## SOURCE_SMOKE failure resolution — 2026-09-16

- Phân loại VNM CafeF `2021-09-09` là `PROVIDER_CORRUPT_ROW`; chỉ exact versioned evidence mới được exclude khỏi constraint promotion, raw/finding được giữ và mismatch fail-closed.
- Phân loại ACV volume là `SOURCE_SEMANTIC_DIFFERENCE`; giữ giá trị source-qualified riêng biệt, không giả định equality hay overwrite.
- Sửa provenance KBS direct HTTP thành `acquisition_client=delta_public_http`, giữ `endpoint_discovered_via=vnstock`.
- Bổ sung machine-readable SOURCE_SMOKE gate, actual CafeF contributing-page hashes, corporate-action/shares evidence và coverage tests.
- Real rerun `source-smoke-20260916T122331Z-79427ec6` PASS và chỉ unlock `REPRESENTATIVE_PILOT`; không chạy pilot hoặc large-scale crawl.

## Bổ sung ngày 12/09/2026 — Báo cáo tiếng Việt

- Chuyển báo cáo triển khai theo giai đoạn và báo cáo rà soát repository sang tiếng Việt.
- Chuyển mẫu sinh report nghiên cứu và phần diễn giải giả định trong cấu hình demo sang tiếng Việt; giữ nguyên tham số và công thức nghiên cứu.
- Sinh bản report pilot tiếng Việt trong một thí nghiệm mới để giữ nguyên báo cáo và checksum của các lần chạy cũ.
- Việt hóa phần nhật ký v0.2 và các quyết định ADR-007 đến ADR-015; bổ sung ADR-016 về ngôn ngữ báo cáo theo yêu cầu người dùng.
- Bản tiếng Việt: `experiment-6436b9f4eb78`. Đối chiếu 9 tệp kết quả số với bản trước: giống nhau từng byte; xác minh toàn bộ checksum đầu ra của cả hai lần chạy và kiểm tra cú pháp thành công. Không chạy lại toàn bộ 44 kiểm thử vì lần này chỉ sửa nội dung báo cáo; kết quả 44/44 thuộc đợt triển khai kỹ thuật trước.

## 0.2.0 — 2026-09-12

- Rà soát repository, SDK đã cài và ý nghĩa các trường dữ liệu nhà cung cấp; ghi rõ đơn vị, phương pháp điều chỉnh giá, múi giờ và dữ liệu tham chiếu còn chưa xác minh. Chưa cho phép chuyển đổi hoặc tải diện rộng dữ liệu thật.
- Bổ sung bộ chuyển đổi có kiểm tra bằng chứng và dữ liệu bất biến, ghép nguồn tham chiếu, cách ly lỗi và đầu vào dùng chung cho pipeline chuẩn; có bộ thử nghiệm giả lập tái lập được.
- Nâng hợp đồng dữ liệu lên 1.1: hỗ trợ UPCOM, cho phép thiếu giá/khối lượng chưa xác minh, bổ sung thời điểm khả dụng và cơ sở của lịch/chỉ số, thông tin sự kiện/lãi suất, số quan sát và lý do thiếu đặc trưng, động lượng điều chỉnh rủi ro và độ biến động giảm giá.
- Bổ sung điều kiện kiểm tra chỉ số tham chiếu, OHLC và tính đúng thời điểm; đặt lại cửa sổ khi đổi cơ sở điều chỉnh giá. Giữ nguyên định nghĩa động lượng, độ biến động, Sharpe, beta và mức sụt giảm tối đa. Tiếp tục một lần chạy đã hoàn tất chỉ kiểm tra, không ghi đè.
- Triển khai KMeans xác định theo từng thời điểm, tiền xử lý, đánh giá số cụm k, nhãn có ý nghĩa kinh tế, độ ổn định không phụ thuộc hoán vị nhãn và ma trận chuyển cụm đã căn chỉnh.
- Bổ sung mô phỏng danh mục trên chuỗi lợi suất với tỷ trọng phân số, khớp sau tín hiệu, chi phí, bốn chiến lược, so sánh chỉ số tham chiếu, bootstrap ghép cặp, phân tích giai đoạn/độ nhạy chi phí và báo cáo/biểu đồ theo phiên bản.
- Bổ sung dữ liệu mẫu và kiểm thử tích hợp/hồi quy ngoại tuyến; chỉ cho tải lớn sau khi bộ thử nghiệm thật đạt. Sổ giao dịch theo số lượng cổ phiếu, nghiệm thu dữ liệu thật và quy trình kiểm định độc lập đã khóa vẫn chưa hoàn tất.
- Phát hiện các file nhà cung cấp có mã băm lệch do đổi định dạng; bổ sung phục hồi đúng bytes từ cache sang snapshot mới có thông tin truy vết, không sửa file gốc.
- Kết quả kiểm chứng cuối đợt triển khai: 44/44 kiểm thử đạt; pilot 6 mã giả lập trong 18 tháng chạy xuyên suốt. Trạng thái validation hiện được hợp nhất tại `docs/REPRODUCIBILITY.md`; báo cáo phase cũ đã được gỡ.

Ghi thay đổi có ảnh hưởng tới người dùng/developer và bằng chứng kiểm thử. Không dùng changelog như bằng chứng kết quả nghiên cứu chưa chạy.

## 0.1.0 - 2026-09-11

### Bổ sung

- Đánh giá năm PDF, kiến trúc module, data contract, feature specification, source evaluation, plan M1/M2/M3, development rules và decision log.
- Core Python CLI: CSV/HTTP JSON → raw snapshot → normalization/QC → clean JSONL → monthly features.
- Crawl checkpoint theo trang, SHA-256, config/code/data hash, bounded retry, rate limit, timeout, pagination và resume.
- Vnstock Community 4.0.6 collector riêng cho sample equity/index và listing; vendor staging không tự được xem là canonical.
- 12 schema JSON theo định dạng table contract; runtime validate cho input, vendor snapshot và feature, interface contracts cho clustering/evaluation/backtest.
- Synthetic fixture 12 mã/18 tháng và 27 test về feature, QC, availability, pagination/retry/resume và cô lập SDK worker.
- Lock dependencies tùy chọn cho môi trường Vnstock đã cài, template model card/strategy spec/weekly report.

### Quyết định và giới hạn

- JSONL là định dạng MVP; chưa có Parquet storage hoặc incremental merge tự động.
- raw_close nullable để ghi nhận dữ liệu thiếu; không tự đồng nhất raw và adjusted.
- M2/M3 là interfaces và schema dự kiến; chưa có trained models, backtest hoặc UI hoàn chỉnh.
- Chưa chứng minh coverage 300 mã/5 năm hoặc hoàn thành nghiệm thu M1. Trạng thái hiện tại xem tại `docs/REPRODUCIBILITY.md`.
# Chưa phát hành — Financial crawler bàn giao người dùng (2026-10-06)

- Thêm CLI/PowerShell launcher `doctor/plan/run/verify`, config portable và gói source bàn giao. Không phụ thuộc các pilot run; output bất biến có raw/JSONL/CSV/coverage/QA/review queue/log/code snapshot.
- Structured KBS trên10 mã:30 responses,8.720 wire cells/2.180 target2025 cells. Report/sector crosswalk và duplicate period headers fail-closed;654 quarterly cells FPT giữ raw nhưng không cấp coverage theo kỳ.
- Selected-page PDF/OCR nối trong cùng runner, exact hash templates và reference QA. Clean4 mã từ network không seed/cache:12 responses/4 PDF/343 pages/1 selected OCR,3 FPT EPS note cells match reference.
- CafeF discovery ghi lại404 FPT/VNM, không sửa URL hoặc bypass; mẫu bàn giao dùng exact issuer/mirror sources đã kiểm tra. Final10 replay32 cache hits/0 network/text/OCR/checkpoints; exports byte-identical.
- 14 tests mới và clean-room source-package tests PASS; full suite315/316, chỉ frozen M2-PREP DECISIONS checksum cũ. Compile/smoke PASS. Lượt crawl mới chưa tự cấp accepted facts/financial cluster/full-universe eligibility. [Report và log](artifacts/reports/financial-crawl-user-v1/report.md).
