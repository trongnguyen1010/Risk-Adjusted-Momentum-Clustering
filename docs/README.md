# Documentation — START HERE

**Tra cứu chỉ số và data cần crawl:** [Handbook chỉ số/data](research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md) — EPS/TTM, PE/PB/BVPS,9 F-signals,8 M-components, EMZ; field dictionary, nguồn/kỳ/notes/PIT/QA/code và11market features. [Report bổ sung tài liệu09/10/2026](../artifacts/reports/financial-indicators-handbook-v1/report.md). Handbook diễn giải implementation, không thay financial feature contract hoặc mở gate.

Publication discovery MWG/VHC08/10/2026: [report/evidence/self-review](../artifacts/reports/financial-mwg-vhc-publication-review-v1/report.md).
MWG website post dates FY2025=23/03/2026, FY2024=24/03/2025; official/cache hashes khác, chưa tự apply PIT. MWG2025 core content46/46pages khớp nhưng cache thêm digital-signature widget; MWG2024 resolution khác. VHC2/2 exact hashes khớp, ngày đăng chưa xác minh. Primary VHC notice có ngày ký09/04 khác công bố10/04 chứng minh không mặc định dùng signature. Không thay inputs/counters/gates;24/300referencecells, production0. Các mục dưới là kết quả stage trước.

Financial MWG/VHC F/M review08/10/2026: [report/worklog/self-review](../artifacts/reports/financial-mwg-vhc-fm-review-v1/report.md).
Full OCR hai FY2024 PDF cache101trang; bổ sung26facts/mã vào v2 riêng. MWG F4/9/M−1,417454; VHC F7/9/M−2,863853, EPS/Z replay nguyên vẹn. Latest FY2025 references24/300(8%):EPS8/Z8/F4/M4,8/50mã có reference; production0. Independent290pins/18Fsignals/16MratiosPASS,23testsPASS; provider50MATCH/22NO_PROVIDER/2VHC2024 expense-sign flags. Exact publication bốn input PDFs chưa xác minh; DATE_ONLY policy giữ nguyên, financial cluster đóng.0acquisition mới, có manual primary-web discovery riêng. Các mục dưới ghi kết quả stage trước.

Financial MWG/VHC template review08/10/2026: [report và worklog](../artifacts/reports/financial-mwg-vhc-template-review-v1/report.md).
User FullOcr46/64pages và template đúng; agent review11facts/mã, chạy4EPS/Z references mới. FY2025 matrix20/300referencecells,8/50mã; EPSrounding2/2,18providerMATCH,60evidencepinsPASS,23testsPASS. Không network/OCR mới. Publication MWG/VHC chưa xác minh; F/M còn chưa-review/history/semantic gaps, cluster đóng. Template gốc giữ nguyên, reviewed inputs riêng trong report.

Financial user live-run review08/10/2026: [kết quả5 bước](../artifacts/reports/financial-user-run50-review-v1/report.md).
150/150 listings,91 PDF mới,109 tài liệu/vintage;41/50 mã có PDF gắn2025 (scope chưa accepted). OCR64 trang trên DGC/GMD,0new review/calculator. Integrity PASS; còn123 PDF jobs nhưng17 PDF attempts. Runbook đã sửa Limit theo PDF; ưu tiên full notes/review MWG/VHC từ cache trước wave acquisition mới.

Financial user workflow08/10/2026: [hướng dẫn tự chạy PowerShell/Python](crawl/FINANCIAL_READINESS_USER_GUIDE.md) và [report bàn giao](../artifacts/reports/financial-user-workflow50-v2/report.md).
Frozen50, assessment300 ô FY2025; acquisition/history2023–2025, cache/resume, batch PDF/OCR và manual reference review. Wrapper tính EPS/Z/F/M khi đủ reviewed inputs; PE TTM/PB và sector adapters còn gaps riêng, gates đóng. Không cần treo Codex khi chạy local.

Financial scale validation08/10/2026: [report và log](../artifacts/reports/financial-scale-validation50-v1/report.md),
[assessment từng mã](../artifacts/reports/financial-scale-validation50-v1/per-symbol.csv),
[lệnh kiểm offline](crawl/README.md#kiểm-tra-scale-financial-frozen50--08102026).
Đã kiểm listing/candidates đủ50 mã và chạy PDF/OCR/calculator trên PHP/VCS/VEA/PAN:
294 trang,8 EPS/Z references mới,2 exact-PDF date-PIT. Phát hiện3 ô VEA khác PDF,
PAN interest kèm phí phát hành, SLS noncalendar và SHS standalone. Flow có manual
review; chưa đủ full financial panel/unattended numeric acceptance/financial cluster.

Financial reviewed integration08/10/2026: [report/log](../artifacts/reports/cafef-financial-reviewed-integration-v1/report.md)
và [lệnh offline](crawl/README.md#nối-trial50-với-reviewed-references--08102026).
Đã nối sealed50 với reviewed facts/calculators:15 annual reference cells và3 FPT
nonannual values trên2/50 mã. FPT6/6 families theo các basis đã khai báo; ACV6 annual
arithmetic references còn auxiliary PIT/history/TTM gaps.0/900 cũ là strict candidate
checklist, không phải0 dòng có thể tính tham khảo. Gates financial/cluster vẫnfalse.

Financial CafeF-first trial50,08/10/2026: [report/log](../artifacts/reports/cafef-financial-trial50-v1/report.md)
và [PowerShell active](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md#flow-cafef-first-active--08102026).
Runner CafeF detail riêng, frozen50 membership, pilot4/replay consistency gate và
compact durable journal; raw candidates khác accepted facts. KBS runner bên dưới
là legacy lineage. Financial/cluster/research/full-universe gates vẫn đóng; đọc
report mới để biết coverage/gaps, không dùng status cũ như kết quả lượt mới.
Live50:588/600 base parse,1.646/1.950 wire periods (84,41%), collection PARTIAL;
0 accepted facts/0 strict tasks-ready, cần document/PIT/notes QA trước100 mã.

Financial update08/10/2026: [benchmark CafeF–KBS và cleanup/report](../artifacts/reports/financial-source-benchmark-v1/report.md),
[lệnh benchmark/restore](crawl/README.md#financial-source-benchmark-và-retention--08102026).
Mẫu9 mã: CafeF164/186 wire statement-periods với78 requests; KBS98/186 với213 requests.
QA theo header: CafeF72/78 numeric matches, KBS0/78; KBS còn dấu hiệu đảo giá trị giữa
kỳ ngay cả `pageSize=1`. Đề xuất engineering: CafeF detail chính, KBS diagnostic;
không tự source-merge hoặc mở financial cluster. Các run cũ được chuyển cold archive;
report cũ giữ nguyên và raw có lệnh restore khi cần.

Financial trial50 đã chạy nguồn thật ngày07/10/2026:
[report kết quả/log](../artifacts/reports/financial-crawl-50-live-v1/report.md),
[hướng dẫn PowerShell](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md).
50 mã/300 base responses parse được, nhưng quarter/history metadata còn blockers;
collection PARTIAL,8 PDF/604 text pages,0 accepted facts, chưa mở financial cluster.

Lineage: [implementation/testing](../artifacts/reports/financial-crawl-50-flow-v1/report.md),
[planning report](../artifacts/reports/financial-crawl-50-plan-v1/report.md) và
[plan JSON](../configs/data/financial_crawl_50_plan_v1.json). Giữ reports cũ bất biến;
live run dùng trial runner riêng, pilot v1 vẫn tối đa10.

Financial user handoff 06/10/2026: [hướng dẫn chạy crawler](crawl/FINANCIAL_CRAWLER_USER_GUIDE.md)
và [report/log](../artifacts/reports/financial-crawl-user-v1/report.md). Runner không cần
pilot artifacts; collection/coverage/acceptance được báo riêng. Gate financial cluster
và full-universe chưa mở. Các report bên dưới giữ lineage của các giai đoạn trước.

Repository đang ở trạng thái **C8 executed and verified; R1 consolidated; M1-REPORT complete**. M1 market foundation đủ cho market-only experiment preparation, còn strict research gate vẫn `NOT READY`. Bắt đầu bằng:

1. [Current status](CURRENT_STATUS.md) — số liệu, gate, lineage và stage tiếp theo.
2. [Project map](PROJECT_MAP.md) — đường dẫn active và ownership.
3. [Architecture](ARCHITECTURE.md) và [Data contract](DATA_CONTRACT.md).
4. [Methodology](METHODOLOGY.md), [Feature system](FEATURE_SYSTEM.md) và [Experiment protocol](research/EXPERIMENT_PROTOCOL.md).
5. [Reproducibility](REPRODUCIBILITY.md) — kiểm chứng offline bằng manifest/hash.
6. [M1 report artifact](../artifacts/reports/m1-market-foundation-v1/report.json) và [inspection notebook](../notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb).

Stage chính xác tiếp theo là **M2-PREP — MARKET-ONLY EXPERIMENT PROTOCOL**. Eligibility phải được freeze theo từng snapshot; 905 chỉ là latest-snapshot count và không phải strict research universe.

Financial handoff hiện hành: [batch flow/report quá trình](../artifacts/reports/financial-batch-flow-v1/report.md)
và [workflow runbook](crawl/README.md). Batch10 mã có acquisition/text/OCR candidates,
checkpoint/resume và transitive verifier;691 PDF pages/32 unique prefix OCR pages.
Replay offline không network/text/OCR mới; chỉ số production/cluster vẫn0.
Execution plan v8 phân biệt engineering automation với FIN-D5 acceptance pending.

Financial calculation lineage: [pilot VNM/PVS/ACV và log](../artifacts/reports/financial-three-symbol-pilot-v1/report.md)
và [workflow runbook](crawl/README.md). Execution plan v7 giữ năm stages; pilot mới có
158 annual reference facts, 17/18 annual metric cells có arithmetic; VNM F còn 8/9 signals.
VNM có reported TTM EPS ≈ 4.727,57 và P/E ≈ 13,18 với publication mirror;
PVS restatement và ACV interim scope còn chặn TTM. Strict acceptance/scale chưa mở.
[FPT acceptance/ESOP report](../artifacts/reports/financial-fpt-acceptance-v2/report.md) giữ nguyên lineage.

Financial lineage trước: [workflow runbook](crawl/README.md) và
[FPT TTM/share-event report](../artifacts/reports/financial-ttm-valuation-v1/report.md).
Execution plan v5 thêm `fpt_ttm_valuation_v3`: TTM EPS reported-numerator ≈ 5.570,36;
P/E/P/B reference 28/08/2026 ≈ 13,14/3,15. Strict normalized TTM và event-adjusted
equity còn pending; slice này không thay task matrix hoặc market-only protocol.

Lineage trước:
[source research/VAS report](../artifacts/reports/financial-source-research-v1/report.md).
KBS structured candidates có trên cả bốn mã. FPT source_completion_v5 tính đủ
chín F-score VAS signals (2024=7,2025=3), M sensitivity và reported P/E/P/B riêng.
Strict F/M, latest TTM và event-complete valuation còn pending. Readiness v12/date v6 đạt153/138; hai transcription corrections có exact-PDF QA.
Strict task v8 vẫn0/120, supplemental H1 observations giữ riêng.
Production variants cần review. FIN-D2/3/4 PARTIAL; FIN-D5 pending.

## Theo mục đích

- Thu thập CafeF có kiểm soát: [Data collection](crawl/README.md) và [CafeF semantics](crawl/sources/CAFEF.md).
- Financial evidence đợt trước: [plan FIN-D1 → FIN-D5](DELTA_UNIFIED_PROJECT_PLAN.md), [execution report](../artifacts/reports/financial-execution-v1/report.md) và [feature contract](research/FINANCIAL_FEATURE_CONTRACT.md). FIN-D1 COMPLETE, FIN-D2/3 PARTIAL; overlay v6 có 133/1.176 cells document-verified/PIT-pending, FPT EPS annual input presence 2021–2025 đạt 5/5; chưa score/PIT-ready. [FPT core report](../artifacts/reports/financial-pilot-closure-v1/report.md) và [acquisition v2](../artifacts/reports/financial-remediation-v2/report.md) giữ evidence trước đó.
- Quyết định methodology: [Decisions](DECISIONS.md), [Research questions](research/RESEARCH_QUESTIONS.md), [Literature matrix](research/LITERATURE_MATRIX.md), [Dynamic clustering review](research/DYNAMIC_CLUSTERING_REVIEW.md).
- Evaluation/product: [Evaluation and backtest](EVALUATION_AND_BACKTEST.md), [Product](PRODUCT.md).
- Governance: [Roadmap](ROADMAP.md), [Reproducibility](REPRODUCIBILITY.md), [Contributing](../CONTRIBUTING.md).
- Historical source caveat còn được artifact tham chiếu: [KBS pilot semantics](data/kbs_pilot_semantics.md) và [data usage risk acceptance](data/DATA_USAGE_RISK_ACCEPTANCE.md).

Các plan, handoff và audit superseded đã được loại khỏi active tree trong R1; Git history là archive duy nhất của chúng.
