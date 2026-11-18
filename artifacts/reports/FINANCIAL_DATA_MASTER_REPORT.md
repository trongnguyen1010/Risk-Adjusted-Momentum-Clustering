# Báo cáo tổng quá trình xây dựng dữ liệu financial

**Execution58 — 24/10/2026:** A/B giữ riêng và đã có bảng đối chiếu; C14features
đã chạy theo owner-approved protocol (7models/5.593assignments). IndependentverificationPASS;
2025chia663/479/6, chất lượngREVIEW_REQUIRED. KhôngPIT/M3. [Report A/B/C](cluster-comparison-v1/report.md).

**Execution57 — integration market/financial:** checkpointfinancial819cd82 + market340519d; dữ liệuC8V2 nhập đúnghash. Hai baseline giữ độc lập, technicalverificationPASS; fullrepositorygate chưaPASS, quality/PIT/M3cònreview. Chi tiết cuối report.

**Cập nhật gần nhất:23/10/2026 — Execution56 đã chạy baseline financial.** 1.172 mã ×
10 năm, tính lại 70.320 core ratios, 10 static models hội tụ. [Report56](financial-full10-baseline-v1/report.md).
Verification kỹ thuật PASS; cả 10 năm có cụm nhỏ, chất lượng cần review. EPS/P/E/P/B/F/M/Z,
PIT/M3 vẫn PARTIAL. Dataset50 rộng hơn giữ nguyên 13.529 reference rows.

**Latest50 — toàn bộ Regular API gaps đã được thử:** **1.172 mã đủ10 annual periods2016–2025 /13.529 reference rows**, tăng170full10/961rows so với49. [Report50](financial-dstock-remaining-v1/report.md), [1.172mã](financial-dstock-remaining-v1/full10-candidates.csv), [cohort/features](financial-dstock-remaining-v1/delivery-result-ref.json), [field review](financial-dstock-remaining-v1/field-review.csv). Còn761held kỳ/257Regular và93candidates ngoài Regular schema;95mã thiếu1kỳ. 0PDF/0OCR;47targeted tests vàindependent verification PASS. Worker đã dừng. Core ratios reference; originalsixfamilies/PIT/M3 vẫn PARTIAL.

## Mục lục

- [1. Hiện trạng và mục tiêu](#1-hiện-trạng-và-mục-tiêu)
- [2. Quá trình qua từng giai đoạn](#2-quá-trình-qua-từng-giai-đoạn)
- [3. Các mốc cải thiện định lượng](#3-các-mốc-cải-thiện-định-lượng)
- [4. Kết quả từng nhóm sản phẩm](#4-kết-quả-từng-nhóm-sản-phẩm)
- [5. Những lỗi và giới hạn đã xác định](#5-những-lỗi-và-giới-hạn-đã-xác-định)
- [6. Việc còn lại để đạt 1.000 mã đủ 10 kỳ](#6-việc-còn-lại-để-đạt-1000-mã-đủ-10-kỳ)
- [7. PDF, OCR và nguồn bổ sung](#7-pdf-ocr-và-nguồn-bổ-sung)
- [8. Bản đồ file và lệnh chạy](#8-bản-đồ-file-và-lệnh-chạy)
- [9. Nhật ký cập nhật report tổng](#9-nhật-ký-cập-nhật-report-tổng)
- [10. Quy tắc cập nhật và chuẩn bị cleanup](#10-quy-tắc-cập-nhật-và-chuẩn-bị-cleanup)

## 1. Hiện trạng và mục tiêu

| Đo lường | Kết quả hiện tại | Cần hiểu đúng |
|---|---:|---|
| Current discovery candidates đã qua acquisition/inventory | 1.522 | Chưa phải historical universe đã xác nhận identity |
| Dòng annual core ratios 2016–2025 | **13.529** | Dataset reference thăm dò, gồm API hypotheses và các vector PDF/HTML có scope riêng |
| Candidates có ít nhất một kỳ core ratios | **1.428** | Không dùng số này để gọi 1.428 mã đủ lịch sử |
| Candidates có ít nhất 3 kỳ annual liên tiếp | **1.408** | Thống kê coverage, chưa freeze mẫu nghiên cứu |
| Candidates có ít nhất 5 kỳ annual liên tiếp | **1.366** | Reference cohort |
| Candidates có ít nhất 8/10 kỳ, có thể đứt đoạn | **1.320** | Không phải 8 kỳ liên tiếp |
| Candidates có ít nhất 8 kỳ liên tiếp | **1.283** | Reference cohort |
| Candidates đủ cả 10 kỳ 2016–2025 | **1.172** | Chưa phải cả 10 kỳ đều đã kiểm chứng PDF/PIT hoặc đủ sáu chỉ số ban đầu |
| Pilot5 EPS/P/E/P/B/F/M/Z FY2025 | **29/30** | VNM F còn thiếu basis; không làm tròn thành hoàn tất |
| Bundle sáu chỉ số đã review | **87 reference rows / 11 mã / 5 full-six cohorts** | Nhiều vintage/snapshot; không phải 87 mã hoặc full history |
| Mã đủ sáu chỉ số ở toàn bộ 2016–2025 | **0** | Goal này vẫn PARTIAL |
| Strict PIT / final M3 readiness | **Chưa đạt** | Cần publication/vintage/identity, market handoff và protocol acceptance |

**Mốc coverage đã đạt trong Execution49, mở rộng thêm ở50:** hơn1.000candidates đủ10annualperiods2016–2025 sau precision vàcashQA. Không đổi denominator, không missing→0 và không nới QA. Bộ core ratios phục vụ baseline thăm dò; EPS/P/E/P/B/F/M/Z và PIT/M3 vẫn PARTIAL. Chưa tự refit hoặc ghi đè model/run cũ.

Plan financial vẫn đặt annual và quarterly 2013–2025, cùng số dư cuối 2012 khi công thức cần. Các mốc full10 trong report này chỉ nói về **annual 2016–2025**, không tự chứng nhận warm-up, quarterly, TTM hoặc PIT đã hoàn chỉnh. Market do teammate thu thập/chạy model riêng; chưa có handoff trên máy này.

## 2. Quá trình qua từng giai đoạn

### 2.1. Discovery, đối chiếu nguồn và workflow đầu tháng 10

Đã khảo sát CafeF summary/detail statements, tài liệu công bố, PDF và thuyết minh; thử so sánh nguồn và xây calculators EPS/F/M/Z, valuation references. Phát hiện summary thiếu dòng không có nghĩa nguồn không có dữ liệu: deep tabs và disclosure routes có nội dung riêng. Có cả trường hợp parser/adapter chưa lấy đúng dữ liệu sẵn có.

Pilot50 và các continuation đầu tiên cung cấp cache, template evidence, PDF vintages và OCR pages. Snapshot 09/10 có **32/300 annual family reference cells trên 10/50 mã**, production-ready 0. Wire presence 1.646/1.950 periods không phải accuracy hoặc metric readiness. Counts này có denominator khác pilot5 và các history runs về sau.

Checkpoint 03/10 đã đối chiếu **FPT annual core 7 fields × 7 năm 2019–2025 = 49/49 ô** với PDF. Việc sửa unit của EPS numerator được ghi bằng correction version thay vì sửa artifact cũ; 49 ô core đã đối chiếu không đồng nghĩa đủ input F/M/Z hoặc PIT. [Report FPT annual core — archive](../archives/financial-history-20261023/artifacts/reports/financial-pilot-closure-v1/report.md).

Ngày 18/10 bổ sung disclosure/UI routes và BRC deep audit: 192 document links, 6 PDF/215 pages trong scope audit, 51 visual candidates. Không gọi tất cả 215 trang đã review hoặc cộng candidates vào metric scorecard. [BRC deep audit — archive](../archives/financial-history-20261023/artifacts/reports/financial-cafef-brc-deep-audit-v1/report.md).

Bằng chứng: [handoff tổng hợp 18/10 — archive](../archives/financial-history-20261023/artifacts/reports/financial-cafef-pilot5-handoff-v2/report.md), [CafeF50 — archive](../archives/financial-history-20261023/artifacts/reports/cafef-financial-trial50-v1/report.md), [continuation50 — archive](../archives/financial-history-20261023/artifacts/reports/financial-continuation50-v2/report.md), [UI/API correction — archive](../archives/financial-history-20261023/artifacts/reports/financial-cafef-disclosure-ui-correction-v1/report.md).

### 2.2. Thu nhỏ pilot5 để tính lại đúng input — 18–19/10

Chọn **BRC, FPT, MWG, GMD, VNM**, thay việc chỉ lấy reported ratios bằng tính lại từng family từ input. PDF/note references được dùng khi API sai hoặc không có input cần thiết. BRC/FPT/MWG/GMD đạt 6/6; VNM đạt 5/6, tổng **29/30**. Đây là practical reference variants có khai báo giới hạn, không production/strict PIT.

Đối chiếu phát hiện annual rows của CafeF có thể gắn sai giá trị, dù bảng nhìn cùng format. Các ví dụ BRC debt, VNM assets/equity/debt cho thấy không thể áp kết quả pilot sang mọi mã mà bỏ QA. Thiếu original-maturity current debt portion của VNM không được thay bằng tổng vay ngắn hạn hoặc missing=0.

VietFin/TCBS/SSI đã được thử theo routes và budgets có kiểm soát: 15 TCBS requests trả 404, SSI public catalog trả 403 và hard-stop; chưa có field financial mới được QA từ các probes này. Không kết luận toàn bộ nguồn thiếu/sai chỉ từ HTTP failures, không vòng qua access controls, không dùng liên hệ IR làm bước mặc định.

Bằng chứng: [pilot5 execution](financial-cafef-pilot5-execution-v1/report-v2.md), [source/VietFin pilot — archive](../archives/financial-history-20261023/artifacts/reports/financial-vietfin-pilot5-v1/report.md), [plan pilot5 v2](../../docs/crawl/FINANCIAL_CAFEF_PILOT5_EXECUTION_PLAN_V2.md).

### 2.3. Thiết kế history và PIT — 19/10

Tách hai plan market/financial; dùng registry chung **1.522 current candidates** thay vì dùng 905 mã market-ready cuối kỳ làm historical universe. Financial lấy annual/quarterly 2013–2025, warm-up cho market 2016–2025. Lưu raw hashes, receipts, source boundaries, report versions và publication evidence từ đầu.

Historical identity, publication và revision giữ thành gate riêng. Ngày kết thúc kỳ, ngày ký, filename hoặc fetched_at không được tự coi là ngày thông tin đã có trên thị trường. Không áp comparative restated mới nhất ngược lịch sử.

Bằng chứng: [plan financial](../../docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md), [plan market](../../docs/crawl/MARKET_HISTORY10Y_1500_PLAN.md), [registry](../../configs/data/securities_collection_registry_v1.csv).

### 2.4. Pilot history: cache, text, OCR chọn trang và review — Execution 8–15

Pilot5 history đã có task accounting nhưng còn 57 API coverage slots thiếu. Triển khai cache-first, text extraction, OCR CPU theo trang, review physical pages và source hashes. Tái dùng tài liệu FPT/VNM đã có; bổ sung tài liệu GMD/MWG/BRC có chọn lọc theo source/budget gates thời điểm đó.

Xử lý annual vs instant vs quarter standalone vs YTD; không lấy CFO bán niên làm CFO quý. Giữ BRC COMPANY_REPORTED năm 2015 riêng với scope no-subsidiaries năm 2025, không suy ngược cấu trúc tập đoàn. Revision EPS và comparative vintage được giữ riêng. Đã xây coordinator OCR để resume không reset page reservations/caps. Publication date references chỉ mở temporal references, chưa mở toàn bộ PIT metrics.

Checkpoint pilot history có 270 reviewed facts trong bundle riêng, 41 annual reference values gồm 29 legacy và 12 historical, cùng 6 period EPS references. Đây không phải cộng thêm vào denominator 30 của pilot5. Independent API-pass audit bổ sung kiểm tra false negatives, không chỉ review anomaly queue; GMD Q4/2019 còn lệch 1 VND ngay trong nguồn.

Bằng chứng và replay: [Execution 8–15 trong plan](../../docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#8-execution-hiện-hành--pilot5-f0f1f2), [history reference bundle — archive](../archives/financial-history-20261023/data/financial/history_reviewed_batch_v1/ecfd0c0dc07b7ead4894/summary.json).

### 2.5. Mẫu20, catalogue và audit độc lập — Execution 16–21

Thu thêm 15 mã sau pilot5; acquisition additional15 có 198.778 raw candidate observations, 341 missing coverage slots. Catalogue parser thấy 267 rows/237 PDF-link candidates trong view đã lấy, chưa exhausted pagination; không biến link candidates thành lệnh tải PDF hàng loạt.

Audit độc lập được pin seed và giữ mẫu khi thiếu tài liệu. F3 kiểm 4/6 samples, 35/36 fields exact match và một khác biệt presentation sign ở DBC. GAS annual có hai named debt fields khác PDF, Q4 khớp; SHS có nhiều named PDF nonzero nhưng API zero và orphan chưa giải thích. Quarantine source partitions, không tự dịch hàng hoặc áp công thức Regular lên công ty chứng khoán.

ACV cache replay bổ sung cohorts theo document vintage, giữ EPS2024 original/restated riêng. GAS PDF bổ sung Z references. Cumulative OCR của campaign history tại checkpoint21 là **130 selected pages/0 errors**; không phải tổng OCR của mọi campaign cũ trong project. Các network counters/caps ở mỗi checkpoint là snapshot được kế thừa, không cộng các cumulative snapshots với nhau.

Bằng chứng: [Execution 16–21](../../docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#16-execution-tiếp--gate-f2-và-metadata-mẫu20-20102026), [GAS/SHS quarantine — archive](../archives/financial-history-20261023/data/financial/history_critical_review_v1/4c87c15431782b8e491b/summary.json).

### 2.6. Owner đổi thứ tự: thu thập trước, review sau — Execution 22–31

Để tránh toàn bộ tiến độ bị chặn bởi PDF/notes của vài mã, owner duyệt tách acquisition khỏi verification. Các mã đủ input có thể được xử lý trước; các field nghi vấn đi vào queue. Thay đổi thứ tự không cho phép nhận dữ liệu sai hoặc mở PIT/research gates.

Quy mô đi qua **20 → 50 → 100 → 200 → 300 → 500 → 800 → 1.100 → 1.400 → 1.522** current candidates. Các successors có assignment, kiểm không trùng, checkpoint, audit/QA và task accounting. Owner yêu cầu tăng tốc; spacing được version từ 2 giây sang 1 giây rồi 0,4 giây cho các flow tương ứng, vẫn concurrency một request và giữ source boundaries/counters/deadlines. Có interrupted overnight flow và audit/resume phần còn lại, không reset ledger.

Dashboard local được bổ sung để đọc tiến độ, log, checkpoint và reports. Hoàn tất acquisition không đồng nghĩa 1.522 mã đủ historical metrics.

Bằng chứng: [Execution 22–31](../../docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#22-owner-đổi-thứ-tự-acquisition-trước-review-sau-20102026), [first50 — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip), [total100 QA — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip), [total500 — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip), [additional122 cuối registry — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip).

### 2.7. Inventory/QA toàn bộ 1.522 mã — Execution 32

Hợp nhất các cohort disjoint, kiểm raw integrity/task accounting, field presence, conflicts, arithmetic, possible row displacements và coverage. Diagnostic templates: **1.429 Regular, 42 Securities, 29 Bank, 22 UNKNOWN**. Đây là phân loại template, chưa phải historical sector acceptance.

Có 14.224.659 candidate cells trong inventory mọi mode; độ lớn raw không được coi là số facts đúng. Chưa chứng nhận historical identity, monetary values, report scope/vintage hoặc PIT cho toàn universe.

Bằng chứng: [inventory/QA report — archive](../archives/financial-history-20261023/artifacts/reports/financial-inventory1522-qa-v1/report.md).

### 2.8. Compute-first và mở rộng mapping — Execution 33–34

Tính phần đã có input reviewed trước, không khởi động một chiến dịch PDF mới. Bundle đầu có **85 reference rows/11 mã**, 5 same-cohort full-six issuers là ACV/BRC/FPT/GMD/MWG; 0 mã đủ sáu family cả 10 năm.

Mở exact statement/group/code/normalized-label mapping từ **23 lên 50 fields**, đọc 31.791 annual raw responses/3.352.158 cells. Tách các field nhìn tương tự nhưng khác nghĩa: weighted shares khác vốn góp, current debt portion khác tổng vay ngắn hạn, owned-PPE depreciation khác accumulated depreciation/aggregate D&A. Các Z arithmetic/F signals conditional vẫn không thành metrics đã kiểm chứng.

Bằng chứng: [compute-first v2 — archive](../archives/financial-history-20261023/artifacts/reports/financial-compute-first1522-v2/report.md), [expanded API input review — archive](../archives/financial-history-20261023/artifacts/reports/financial-api-input-review1522-v1/report.md).

### 2.9. Cached facts, template contract và reference reconciliation — Execution 35–36

Đối chiếu 557 annual fact/vintage observations trên 11 mã: **334 exact match, 63 difference/vintage, 160 chưa có comparable direct alias**. Không kết luận cùng format thì mọi ô đều đúng. Bổ sung 2 Z period references BRC2024/VNM2024, bundle thành **87 rows**, không cộng trùng các replay cũ.

Xác định mismatch giữa labels và values của finance rows; staging exact-template contract dùng 24 calibration/independent controls. Có 1.427 mã match template, 15.135 annual provider partitions; số partitions/conditional arithmetic không phải số mã đã verified. Giữ proposal/raw, không sửa API hoặc promote canonical.

Bằng chứng: [cached fact verification — archive](../archives/financial-history-20261023/artifacts/reports/financial-cached-fact-verification-v1/report.md), [reconciliation — archive](../archives/financial-history-20261023/artifacts/reports/financial-cached-fact-reconciliation-v1/report.md), [template contract — archive](../archives/financial-history-20261023/artifacts/reports/financial-template-contract-v1/report.md).

### 2.10. Baseline financial-only thăm dò — Execution 37

Owner chọn core ratios để chạy exploratory baseline trong khi hoàn thiện sáu family ban đầu song song; market/model của teammate chưa có handoff. Sáu features: gross margin, net margin, liabilities/ending assets, current ratio, CFO/ending assets và revenue/ending assets.

Dataset đầu: **6.976 rows/1.311 candidates/51 full10**. Đã fit static K-Means mỗi năm với k=3 và seed/protocol pin; không gọi là Dynamic Clustering hay backtest. FY2025 zscore cho cluster sizes 982/1/1; rank sensitivity cùng 984 mã cho 395/361/228. Giữ outliers và báo rõ, chưa chọn final model bằng việc so metric giữa hai không gian biến đổi hoặc bằng portfolio returns.

Bằng chứng: [baseline — archive](../archives/financial-history-20261023/artifacts/reports/financial-exploratory-core-v1/report.md), [scale/rank sensitivity — archive](../archives/financial-history-20261023/artifacts/reports/financial-exploratory-scale-compare-v1/report.md).

### 2.11. Vì sao chỉ 51 full10: precision diagnosis — Execution 38

Exact-zero QA gộp lỗi số học rất nhỏ với sai lệch nội dung. Trong 4.147 finance-bridge differences năm 2016–2021, 4.137 chỉ lệch 1 raw unit. Replay tolerance0 tái lập baseline trước khi thử sensitivity.

Absolute-only tolerance1 cho **505 full10**, tolerance2 cho 550, nhưng đây là **what-if, chưa áp dụng**. Không đưa 505/550 vào cột kết quả thực thi. Provider unit ngoài các controls/overlays có phạm vi chứng minh riêng vẫn chưa đủ individual acceptance cho toàn universe.

Bằng chứng: [diagnosis — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip).

### 2.12. Precision QA thực thi, có hai cap — Execution 39

Version mới chỉ cho reference: residual phải đồng thời ≤1 raw unit và ≤1e-9 × max(abs(các số hạng)). Giữ missing, ambiguity, displacement, provider partition, sector và denominator gates; không sửa numeric values. Relative cap giữ 440 rows khỏi what-if absolute-only.

Phục hồi **4.202 rows**, đạt **11.178 rows/1.416 candidates/427 full10**. Toàn bộ 6.976 vectors cũ giữ nguyên. Inventory 211 local PDFs/202 unique hashes; backlog 3.112 annual cases không được gọi là 3.112 PDF cần tải. Không network/PDF/OCR mới.

Bằng chứng: [precision QA report — archive](../archives/financial-history-20261023/artifacts/reports/financial-precision-review-v1/report.md).

### 2.13. Sửa nhận diện CFO phương pháp trực tiếp — Execution 40

723 cases thiếu CFO được kiểm trên 181 mã. Raw đã có mẫu trực tiếp với total `HDKD_9`, trong khi alias cũ nhận `HDKD_20`. Chỉ nhận code+label chính xác, annual/provider đúng, components numeric, extra code không có số bất thường và tổng 7 signed components khớp total theo precision policy cũ; không suy field bằng vị trí.

**657 rows được phục hồi**, 25 cases component-invalid và 41 có CFO nhưng vẫn held do gate khác. Dataset thành **11.835 rows/1.422 candidates/459 full10**. Toàn bộ 11.178 rows trước giữ nguyên; model chưa rerun. Thống kê cohorts và nguồn thiếu cho thấy không thể gọi hơn 1.000 mã đủ 10 kỳ chỉ vì đã có hơn 1.000 mã ở các mức lịch sử ngắn hơn.

Bằng chứng: [direct CFO report — archive](../archives/financial-history-20261023/artifacts/reports/financial-direct-cashflow-review-v1/report.md).

### 2.14. Review nhóm 412 mã thiếu một kỳ; tạo report tổng — Execution 41

Review toàn bộ 412 one-year gaps. Reasons có overlap: 223 QA-held, 125 no annual mapped partition, 57 multiple-provider, 42 displacement, 12 missing inputs, 5 nonpositive denominator. Không đổi source priority hoặc bỏ gate để tăng số.

Từ facts đã review, BRC/VNM có đủ tám input core trong từng PDF riêng. GAS thiếu CFO trong facts nhưng trang 12 đã có sẵn image/OCR cache; đọc trực quan current-year CFO 13.040.237.870.138 VND, reconcile signed components, lưu **một reviewed fact mới**. Không chạy OCR/download mới. Tính ba vector **single-document reference**, không overlay/repair các API partitions đang bị giữ.

Phục hồi **BRC2025/GAS2025/VNM2025**, thành **11.838 rows/462 full10**; toàn bộ 11.835 rows cũ giữ nguyên. Còn 409 mã thiếu một kỳ, backlog 2.452 annual cases. Không diễn giải “409 chưa có đủ reviewed vector” thành “409 PDF chưa có trong cache”.

Report tổng này được tạo làm điểm theo dõi liên tục; index/active pointers trỏ về đây. 39 targeted tests, compile/synthetic và source/value replay PASS; final goal vẫn PARTIAL. Bằng chứng: [near-full10 review](financial-near-full10-review-v1/report.md).

### 2.15. Audit 125 annual gaps và nguồn HTML chính chủ — Execution 42 (22–23/10)

Đã đối chiếu receipts và raw headers NAM/LUYKE của 125 mã có 9/10 kỳ nhưng thiếu annual input: **58 gaps nằm giữa các năm có dữ liệu, 38 trước năm sớm nhất, 29 sau năm muộn nhất**. Không có numeric annual target-year header trong responses đã pin. Có 41 cases có LUYKE headers trong năm, 37 có đủ ba nhóm Q4 và 29 có đủ ba nhóm ở cả bốn quý; các tập có overlap và chưa được coi là annual 12 tháng.

Ba cột legacy HTML cho PLX2023/CTD2023/PLC2025 đều chỉ là placeholder trống. View catalogue cũ chưa có exact annual links trùng targets; không kết luận doanh nghiệp không công bố hoặc toàn bộ cache/Internet đã được kiểm hết.

Mở rộng lookup có giới hạn sang hai nguồn HTML chính chủ, không mở PDF. [Petrolimex 2023](https://www.petrolimex.com.vn/bctn-2023-baocaotaichinh.html) có bảng financial bằng HTML; [Coteccons annual catalogue](https://www.coteccons.vn/annual-report-vn/) nêu rõ FY2023 chỉ từ 01/01 đến 30/06 nên CTD giữ fiscal-period hold. PLX có 32 fields được đối chiếu theo row code/year/unit/value; accounting checks và finance bridge theo precision policy cũ PASS, bổ sung một issuer-HTML reference vector. Các caption anomalies ở dòng khác được ghi warnings, không chấp nhận cả trang. Source lưu là web-tool extracted text có hash; chưa có original HTTP response bytes hoặc publication/version acceptance.

Kết quả **462 → 463 full10**, 11.839 rows/1.422 candidates; giữ nguyên 11.838 old rows. Còn 408 one-year gaps, 124 annual-input targets trong nhóm 125 trước, 2.451 annual gap cases. 24 targeted tests, compile/synthetic, source/value checks PASS. Local replay 0 network; ba external web-tool calls được ghi riêng, không nói toàn bộ lượt làm việc có 0 network. Không PDF/OCR mới, không sửa API/counters/boundaries/model hoặc mở six-family/PIT/M3. [Report, audit và dataset mới](financial-annual-gap-audit-v1/report.md).

### 2.16. Rà soát dữ liệu quý của124 annual gaps — Execution43 (23/10)

Duyệt toàn bộ pinned quarterly receipts, kiểm task URL, source hash và provider partition; tách đủ CDKT/TN, CDKT/NV, KQKD/KQKD, LCTT/HDKD. Có **36** cases đủ bốn nhóm tạiQ4 cùng provider token và **27** cases ở cả bốn quý. Đây mới là numeric header coverage: chưa chứng minh đủ tám fields, kỳ, scope, unit hoặc vintage. Cả912 header observations thiếu explicit unit. Không tự ghép quý/CFO lũy kế thành annual. Dataset giữ11.839rows/463full10, **tăng0 mã**.

Đã tìm được primary document leads choPTB2018 vàPLC2025; [đề nghị tối đa hai PDF — archive](../archives/financial-history-20261023/artifacts/reports/financial-quarter-gap-triage-v2/pdf-review-proposal.md) đang chờ owner duyệt. Cần kiểm cache URL/metadata trước khi tải. Chưa mở/tải PDF hoặc OCR; bốn external web-tool calls được ghi riêng, HTTP attempts/bytes nội bộ chưa biết. V1 giới hạn năm pages chỉ giữ làm intermediate; V2 quét mọi receipt, có regression test page7.16tests/compile/synthetic/source checks PASS; goal1.000full10 vẫnPARTIAL. [Stage report — archive](../archives/financial-history-20261023/artifacts/reports/financial-quarter-gap-triage-v2/report.md), [audit ref — archive](../archives/financial-history-20261023/artifacts/reports/financial-quarter-gap-triage-v2/result-ref.json).

### 2.17. Queue phục hồi theo batch lớn — Execution44 (23/10)

Owner muốn phục hồi nhiều hơn. Đã gom **635 candidates gần đủ lịch sử /862 annual dependencies**, gồm408 mã9/10 và227 mã8/10. Blocker chính độc quyền của408 mã:181 QA,124 thiếu annual,57 nhiều providers,39 displacement,5 thiếu input,2 denominator không dương. Original reasons và direct-CFO review vẫn được giữ, không cộng trùng các lỗi chồng lấn.

Chọn **batch100 mã9/10**, mỗi mã chỉ vướng một accounting check, có danh sách field/chênh lệch cần xác thực. Phân bổ31profit attribution,25aftertax,19other profit,12liability parts,6net revenue,4PPE,2asset parts,1assets/capital. **Chưa phục hồi thêm dòng: coverage vẫn463full10.** Mức trần nếu cả batch qua gates là563, không bảo đảm thành công. Không nới QA để tăng count.

[Đề nghị bổ sung tối đa100PDF — archive](../archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/pdf-batch100-proposal.md), chia hai batch≤50, pilot10 trước, **chờ owner duyệt**. Catalogue URLs/cache status của100 targets chưa resolve nên queue chưa phải download manifest. Dùng HTML/cache nếu đủ, không mặc định mỗi gap cần mộtPDF. Không network/PDF/OCR ở lượt này;4tests/compile/hash/dependency checksPASS. [Report — archive](../archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/report.md), [100 mã và fields — archive](../archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/batch100-review.csv), [resultref — archive](../archives/financial-history-20261023/artifacts/reports/financial-bulk-recovery-queue-v1/result-ref.json). Goal vẫnPARTIAL.

### 2.18. FlowPDF cócheckpoint vàpilot10 — Execution45 (23/10)

Owner đã duyệt batch100 rồi yêu cầu hoàn thiện flow có thể chạy lại trước khi mở rộng. Đã triển khai một entryPowerShell: catalogue/cache → boundeddownload → text → selectedOCR → reviewreceipt → referenceQA/compute → coverage/status. Giữcounters/sourceboundaries cũ; batchPDF mới có72giờ và không reset90ngàycampaign. Chỉ chạy10target đã chốt, chưa mởbatch50.

**Phục hồiCNT2018**, toàn bộ8coreinputs từ mộtPDFhợpnhất chínhchủ, OCR4trang vật lý7–10 vàreview31fields trênảnh.10accountingchecks đủdòngexact; haioptionalchecks chưađủinput khôngđược biếnmissingthành0. Dùngexisting single-document reviewed-vector policy, khôngrepair APIpartition hoặc thayQA. Dataset **11.840rows/464full10 (+1)**;11.839oldrows giữ nguyên, independentratio recomputePASS. Còn407mã9/10 và2.450annualcases. Pipeline chưa hoàn toàn tự động: tìmnguồn/chọntrang/semanticreview vẫn có phầnagent làm.

Pilot đã duyệtqua10states nhưng chỉ **1/10=10%** referencecomplete:7targets cần source discovery,2catalogueviews chưa có đúngannualdocument. Không diễn giải thành10/10 hoặc không công bố. Sourceadapters chưa đủ bằngchứng scale1.000mã; next50_allowed=false. Boundedlocalnetwork thêm4requests/4attempts/5.799.939bytes,1PDF; webdiscovery7calls/18queries ghi riêng, HTTPbytes/attempts bêntrongtoolunknown. OCR130→134pages/0errors; resume không tăngthêmrequest/OCR. Cachemetadata chỉ resolve được28/211files;183unknown vẫn là backlog, không khẳngđịnh cacheabsence.

41tests/compile/synthetic/realPowerShellrun+verify vàsource/unchangedrowchecksPASS. [Stage report vàrunbook](financial-pdf-pipeline-v1/report.md), [reviewreceipt](financial-pdf-pipeline-v1/cnt2018-reviewed-vector.json), [datasetref](financial-pdf-pipeline-v1/dataset-result-ref.json), [verification](financial-pdf-pipeline-v1/verification.json). Điểmstatuschung đọc datasetref để báo464full10; acquisition-onlysnapshot vẫn giữbaselinecũ463, không dùng làmmetricstatus. Chưa đủsáufamilies/PIT/M3; finalgoalPARTIAL.

### 2.19. Khôi phục cache provenance và bàn giao coverage — Execution46 (23/10)

Owner cần hơn 1.000 mã gấp cho báo cáo. Đã xuất riêng các reference cohorts **1.365 mã ≥3 kỳ liên tiếp; 1.168 mã ≥5 kỳ; 790 mã ≥8 kỳ; 464 full10**, kèm feature rows và coverage từng năm. Đây là bộ core ratios thăm dò hiện có, không phải tăng số mã đủ lịch sử hoặc bộ EPS/P/E/P/B/F/M/Z/PIT. Không đổi tiêu chuẩn 10 kỳ; không chạy fit/model hoặc freeze mẫu nghiên cứu.

Khắc phục resolver chỉ đọc sibling receipts: đối chiếu thêm legacy inventories/results/receipt directories theo exact PDF path + SHA256 + URL trong cùng record. **28→211/211 PDF files có acquisition metadata; 183→0 unresolved trong inventory cũ**, 358 receipt entries/1.295 metadata files, không suy identity bằng filename. Giữ mọi raw/code/config/results đã seal. Chưa xác minh nội dung statement của toàn bộ cache; CNT2018 nằm ngoài inventory snapshot này.

Cache có ứng viên cho **11 annual gap cases trên 10 mã**; ưu tiên DCM2025/VEA2025/PAN2024/VHC2024 vì mỗi mã chỉ thiếu một kỳ. Vẫn cần text/page/year/scope/vintage review và QA trước import. Chín target pilot chưa resolve từ cache; không mở batch50. **Full10 464→464, rows 11.840→11.840**, không có accepted facts mới, 0 local requests/downloads/OCR. Public web discovery 1 call/4 queries ghi riêng; chưa resolve exact primary target mới, 0 HTML/PDF opens, internal attempts/bytes unknown.

Mốc hơn 1.000 được cụ thể hóa thành dependency queue cho **1.001**: 464 +407 one-gap +130 two-gap, cần **667 annual dependencies cho 537 candidates nếu tất cả được giải quyết**. Chưa phải số PDF cần tải hoặc bảo đảm phục hồi; two-gap selection deterministic, chưa tối ưu độ dễ nguồn. Approval batch100 giữ nguyên; queue không tự cấp quyền tải phần còn lại.

14 targeted tests/compile/synthetic và independent source/export checks PASS; 13 result files/1.309 input pins, 358 receipt JSON pointers/PDF hashes được kiểm. Full suite chưa được tuyên bố PASS. [Report và cohort exports — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip), [result ref — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip), [cache review queue — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip), [verification — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip). Goal full10/PIT/M3 vẫn PARTIAL.

### 2.20. Phục hồi DCM/VEA/PAN/VHC từ cache — Execution47 (23/10)

Review đúng bốn targets ưu tiên từ Execution46: DCM2025, VEA2025, PAN2024, VHC2024. Text-first không đủ usable content, xem preview xác định physical pages và chỉOCR21trang trên bốn consolidatedPDF có sẵn. Review **131fields**, đủ8coreinputs mỗi vector;47accounting equalities exact,1DCMfinancebridge chưa đủ associate row, không zero-fill. CFO signed-component reconciliation của cả4exact; giữ CFOâm của3mã.

**Full10 464→468 (+4), rows11.840→11.844 (+4)**, tất cả11.840oldrows giữ nguyên.24ratio values tính lại độc lập bằngDecimal vàkhớp. VEA dùng đúng tổng400 bao gồm430; cóýkiếnkiểmtoánngoạitrừ, giữsourcewarning vàreference-only, không audit/research clearance. VHC giữraw parentheses vàchuẩnhóa expense magnitude theoexisting subtractionformula, deferredtaxincome lànegativeexpense. APIpartitions vẫnquarantine; rawcomparison trướcoverlay khôngtựkếtluậnwebsite sai.

Draftpreimport đầu dùng sai namespacefinancefields; giữV1, tạoV2 trướcimport, khôngdatasetnào dùngV1. Explicit whitelist/source/code/column checks được kiểm lại. OCRcampaign134→155charged/successfulpages,0errors;run/verifyreplay khôngtăngpages, importtrảđúngmanifest.0network/PDFdownloads. Đâyvẫn làflow cósemanticreviewdoagent, chưatựđộnghoàntoàn cho hàngtrămmã.

Còn **403one-gap/2.446annualcases**. Mốc1.001cần663annualdependencies trên533candidates theo phương án cóđiềukiện403one-gap+130two-gap; chưachốtsốPDFmới. 27targeted tests/compile/synthetic/source/oldrows/CFO/ratios/replayPASS; finalgoal/PIT/M3vẫnPARTIAL. [Report](financial-cached-four-review-v1/report.md), [datasetref](financial-cached-four-review-v1/dataset-result-ref.json), [468full10](financial-cached-four-review-v1/full10-candidates.csv), [verification](financial-cached-four-review-v1/verification.json), [currentcohortexports](financial-cached-four-review-v1/cohort-result-ref.json). Workflow45/dashboardacquisitioncũkhôngphảicurrentdatasetcounter; dùngsummary47 trongrunbook.

### 2.21. HSG cache và source pilot DStock — Execution48 (23/10)

HSG FY2024/FY2025 giữ fiscalend30/09,64reviewedfields/8OCRpages/22exactaccounting/2CFObridges;11.844oldrows unchanged,12ratios independentlychecked. 468→469full10,11.844→11.846rows. VDT2019 tải1PDF trongapprovedpilot10 nhưngscopeheld,0import. Shadow sign audit chỉ3potential/0accepted. Source DStock đượcowner đề nghị:6cases/4tickers,5cases11/11exact,TCM2013held,VHC2024control8/8exactPDF;0DStockaccepted. [Report48](financial-pilot-cache-recovery-v1/report.md), [DStock source](financial-dstock-source-pilot-v1/report.md).

### 2.22. DStock source recovery và cash QA — Execution49 (23/10)

Owner cho phép tự chạy các phase trong1giờ hoặc đến>1.000. Adapter itemCode/model/label/membership,rawDecimal,finitebounds/checkpoint; giữ mọi baseline rows vàsources. Pilot10 phục hồi9mã;20→50→100→200→300→400→500→600candidates cho lần lượt487/516/564/657/751/846/932/1.017full10sơbộ. Network tự dừng08:10:24UTC. Ba cash totals/stockchecks bổ sung giữ16kỳ, giảm15full10: **bàn giao1.002full10 /12.568rows**, tăng533full10/722rows so với48.

11.846oldrows unchanged;8.664exactaccounting/financechecks,2.166cashchecks trênnewrows (2.161exact/5smallresidualđúng2caps);4.332ratios/23.826sourcevalues kiểm độc lập.194requests/194attempts/28.262.575bytes,0PDF/0OCR/0sourceboundary.42targeted/compile/synthetic/manifest/replayPASS; offlinejournalhashunchanged. Còn75heldcases/67candidates và1.647cases chưa acquire, tổng1.722annualgaps;59candidates9/10. Không biến sốgaps thànhPDFcount. Giữ123providerCFOcomponent-completenesswarnings,publication/identity/PITgatesfalse. [Report49](financial-dstock-gap-recovery-v1/report.md), [dataset cuối](financial-dstock-gap-recovery-v1/cash-result-ref.json), [bàn giao cohorts](financial-dstock-gap-recovery-v1/delivery-cash-result-ref.json), [verification](financial-dstock-gap-recovery-v1/verification-cash.json).

### 2.23. Hoàn tất API gaps còn lại — Execution50 (23/10)

Theo yêu cầu hoàn thiện phần còn lại, tiếp tục baseline49; không gọi lại797cases đã thử (gồm75held). Các phase50→100→200→300→360candidates xử lý1.647cases mới:961pass/686held. Cả2.444Regular gaps đã thử; kết quả **1.172full10 (+170),13.529rows (+961),1.428candidates có dữ liệu**. Giữ12.568oldrows; QA12accounting+3cashchecks chạy trước nhậnrow, không nới precision/formulas/scope. Cohorts3/5/8/10năm liên tiếp1.408/1.366/1.283/1.172.

Independent verification replay31.713source values,5.766ratios,11.532exactchecks vàcashQA;47targeted tests/compile/syntheticPASS. Core348requests/41.765.268bytes;11metadata requests/781bytes đều trả metadata rỗng, không waive membership. Window08:38:50–09:38:50UTC; giữ absolutecaps/campaignanchor/counters.0PDF/0OCR, khôngsourceboundary. Catalogue probe **chưa thực thi** vì automatic approval review usage limit;0request, không bypass. Còn761heldcases/257Regular (95mã9/10) và93sector/unknown táchschema. SốPDF thật chưa xác định; không đồng nhất761gaps vớiPDFcount. [Report50](financial-dstock-remaining-v1/report.md), [verification](financial-dstock-remaining-v1/verification.json), [handoff](financial-dstock-remaining-v1/delivery-result-ref.json).

### 2.24. Làm rõ flow hai nguồn API — Execution51 tài liệu (23/10)

Owner yêu cầu cập nhật plan theo flow CafeF+DStock và giải thích vì sao vẫn còn
thiếu. Lượt này chỉ kiểm tra evidence offline và sửa tài liệu;0request,0PDF/OCR,
không thay raw, dataset, policy, công thức, model hoặc gates. [Plan mục3.1](../../docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#31-flow-hai-nguồn-api-hiện-hành--cập-nhật-23102026).

**Hai nguồn đã được dùng để mở rộng coverage, theo mã–năm; chưa ghép từng ô.**
CafeF là baseline API/history; các reference PDF/HTML đã review giữ provenance.
DStock49bổ sung722rows và50thêm961rows: tổng**1.683DStock rows**. Kiểm
`source_kind`/`provider_type` trong frozen features50 cho thấy còn11.835legacy API
baseline rows và11reference PDF/HTML rows, tổng13.529. Không sửa baseline row;
chỉ nhận complete input vector của DStock cho key còn thiếu sau QA15checks.
Một mã có thể có các năm từ các nguồn khác nhau, nhưng row DStock không được
vá bằng field CafeF. Không coi1.172full10 là toàn bộ đã cross-check độc lập ở cả
hai nguồn hoặc đã xác thực PDF/PIT.

| Nguyên nhân primary của kỳ còn held | Số kỳ | Ý nghĩa và hướng xử lý |
|---|---:|---|
| Không có observations trong truy vấn DStock | 550 | Cần kiểm cache nguồn nền, range, fiscal period và lịch sử doanh nghiệp; chưa chứng minh không tồn tại ở mọi route/nguồn |
| Net revenue không dương | 103 | Không đủ denominator theo công thức hiện hành; không mặc định là crawl thiếu hoặc PDF sẽ sửa được |
| Thiếu inputs, sau các nhóm ưu tiên trên | 36 | Một số field cần thiết chưa đủ; kiểm semantics và nguồn phù hợp trước bổ sung |
| Model membership/scope chưa rõ | 33 |11tickers; metadata follow-up rỗng, không waive mapping hoặc tự suy schema |
| QA/scope cần review khác | 39 | Có checks/fiscal scope chưa đạt; giữ chênh lệch và source evidence để review |
| **Tổng** | **761** | **257Regular candidates chưa full10** |

Đây là phân loại primary có thứ tự ưu tiên, không phải tổng của tất cả flags.
Ví dụ619cases có flag MISSING_INPUTS gốc có thể đồng thời nằm trong550cases
NO_OBSERVATIONS; không cộng chồng. Ngoài257Regular còn93Bank/Securities/UNKNOWN
tách schema, nên1.522−1.172=350candidates chưa full10 theo baseline này.

**Có kết hợp hai nguồn nhưng chưa đủ theo acceptance hiện hành.** Chưa thực hiện
exhaustive cross-source field repair/reconciliation cho761kỳ; không được nói cả
hai API chắc chắn đều thiếu mọi field. Nguồn có thể trùng nhà cung cấp upstream,
hoặc khác report scope/vintage; có hai số giống nhau cũng chưa đủ chứng nhận đúng.
Không quy mọi kỳ chưa đủ thành lỗi crawl, cũng chưa gán nguyên nhân doanh nghiệp
chưa thành lập/niêm yết khi chưa có evidence.

Next action: review95mã thiếu1kỳ trước; kiểm lịch sử/fiscal semantics, cached
CafeF và DStock theo cùng key, tách missing/conflict/không áp dụng; lập đề xuất
PDF có số tài liệu và lợi ích dự kiến khi cần.761kỳ không phải761PDF. Source
boundaries/counters/deadlines giữ nguyên; không tự mở network hoặc PDF campaign.

Bằng chứng: [frozen dataset50](financial-dstock-remaining-v1/dataset-result-ref.json),
[phân loại tổng](financial-dstock-remaining-v1/handoff-summary.json),
[95mã thiếu1kỳ](financial-dstock-remaining-v1/one-year-gap-candidates.csv),
[field review](financial-dstock-remaining-v1/field-review.csv),
[report50 đã seal](financial-dstock-remaining-v1/report.md).
Kiểm tra offline: cộng nguồn13.529rows, primary761cases,257held candidates,
full10=1.172; không thay source manifests. Kết luận:PASS cập nhật tài liệu;
full financial families/PIT/M3 vẫn PARTIAL. Không tạo thêm thư mục report.

### 2.25. Rà soát cache95one-gap — Execution52 (23/10)

Theo owner tìm thêm trước khi ưu tiên M2 trên1.100mã đã đủ, rà95keys thiếu một
năm, pin761inputs/178rawfiles và replay CafeF mapping/precisionQA theo từng
partition, so raw fields vớiDStock mà không ghép input.43cases thiếu2016,
15thiếu2025;59không có numeric CafeF partition trong cache năm mục tiêu,
26có complete core inputs,4cóQA/corepass. API2021/IPA2021/SBD2024 đềuH+HK,
CAP2022K+N; chưa đủ evidence chọnscope/vintage/priority. Không nhận thêm4leads.

95DStock cases phân loại primary:45no-observations,26QA/scope,11denominator,
10missinginputs,2membership,1fiscalcalendar.46cases có đủ tên core fields nếu
union các nguồn chỉ làdiagnostic, không46recovered.0metadataPDFhints trong
cache index đã pin không chứng minh website không có tài liệu. Khôngnetwork,
PDF/OCR hoặc acceptance/policychange; baseline vẫn13.529rows/1.172full10.

[Report52 và hướng chuyển ưu tiên M2](financial-one-gap-review-v1/report.md),
[review95keys](financial-one-gap-review-v1/one-gap-review.csv),
[partitionQA](financial-one-gap-review-v1/cafef-partition-review.csv),
[summary](financial-one-gap-review-v1/summary.json),
[verification](financial-one-gap-review-v1/verification.json).
Chốt rà soátcachePASS, gain0. Sáucore ratios của1.172mã đã tính; ưu tiên tiếp
theo làpincohort/QAphân phối vàbaseline financial-only thăm dò theo protocol,
không trì hoãn vì95gaps. Lượt52chưa chạy/refitmodel, không tuyên bốM2hoàn tất;
originalsixfamilies/PIT/M3vẫnPARTIAL. PDFneedcountnull; phải báoownertrướctải.

### 2.26. Dọn project trước phân cụm — Execution53 (23/10)

Owner yêu cầu gỡfile không dùng, đặt tên dễtìm vàgộp báo cáo trước M2. Kiểm kê
banđầu (không tính.venv/.tools/.git):data/financial594.314files/~29,39GB,
artifacts/reports66folders/1.081files/~353,78MB,.tmp2.364files. Phầnlớn là
cache/bằngchứng crawl, khôngđượcxem làrác chỉvìcũ. Scan11,420metadata,
code/config/docs đểgiữconsumer vàfrozenpins. Khôngxóa nguyênraw/canonical/campaign.

Đãgỡ **2,889files /184,257,666bytes** khỏiworkingtree:
110report/helperfiles đượclưuZIP nguyênbytes trướcgỡ;
planbao gồm2779cachefiles cóthểtái tạo. ZIP4,203,135bytes;
khôngcoibytesgỡ làdisknetgain vìvẫn giữarchive vàthêmhandoffcopies. Đãđưa
9reportfolderslịch sửra khỏi `artifacts/reports`; còn
57reportfolderstrực tiếp.
Không gỡ các file đangthamchiếuhoặcpin. Danh sách exactpaths/hashes/held ở
[cleanupplan](../repository/project-cleanup-20261023/plan.json),
[kếtquảprune](../repository/project-cleanup-20261023/prune-result.json),
[ZIP](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip).

Tênmới chođiểm bàn giao: [financial-reference-2016-2025](../../data/handoffs/financial-reference-2016-2025/README.md),
`financial-ratios-1172-symbols-2016-2025.csv`, `securities-1172-symbols.csv`,
`missing-periods-review.csv`; handoffmanifest pinguồn/hash. Đây làcopyđúngbytes,
khôngrename hoặcdi chuyển frozenresult. [Bảnglệnh](../../scripts/README.md) tách
entrypoints đangdùngkhỏilegacylineage; khôngrename source/config đangđượcpin.
Update16liveMarkdownlinks sangarchive; linksgốc đượcghi trong
[updated-links](../repository/project-cleanup-20261023/updated-links.json).
Report đãseal giữnguyênbytes; muốnđọclinklineage lạnhthìrestore trước.

Khôiphụcexactpaths: `scripts/project_cleanup.py restore` từprojectroot;
kiểmZIP: `scripts/project_cleanup.py check`. Scriptkhôngoverwrite filekháchash,
khôngresetcounter/sourceboundary, khôngnetwork/PDF/OCR. Deletion chỉnative
PowerShellLiteralPath saucheckabsolute workspacepaths/hash vàverifyZIP.
CachePython/test cóthểtái tạo; khôngthaytestassertions hoặcacceptancepolicy.

Chốtstage **PASS**: compileall/Python+PowerShellsyntax/path-boundary checks,
ZIPCRC+SHA256 từngentry, activeanchors vànamedhandoffhashes. Restorefixture
trảđúngbytes, từchốioverwrite vàplanđổihash. [Verification](../repository/project-cleanup-20261023/verification.json).
Coveragegiữ1.172full10/13.529rows,originalsixfamilies/PIT/M3PARTIAL.
**Chưa chạy/refit phân cụm**; việc tiếp theo làbaselinefinancial-only M2
trêncohortđủ, saukhicleanupđãbàngiao. Khôngtuyênbốpublic-readyhoặcđãxóa hết
legacy dependencies:594kfinancialsourcefiles vàcácconsumerpins đượcgiữ cóchủđích.

### 2.27. Clean sâu: lưu lạnh normalized caches — Execution54 (23/10)

Owner hỏi vì sao vẫn giữ nhiều phiên bản cũ và yêu cầu clean sâu hơn. Để chạy
M2, chỉ dùng handoff mới nhất; không cần giữ mọi intermediate candidates ở dạng
file rời. Tuy nhiên dataset50 kế thừa các reference rows trước đó, nên không xóa
raw/receipt/journal hoặc dùng report tóm tắt thay evidence.

Đã chuyển **102,504file /11,058,805,949bytes**
trong bốn thư mục candidates batch 500/800/1100/1400sang bốn ZIP. ZIP tổng
**661,305,882bytes**; giảm net phầncache khoảng
**10,397,500,067bytes**, chưa tính metadata nhỏ của audit.
Đã kiểm SHA256 từng member, CRC qua đọcZIP, inventory size/mtime trước prune,
archive/plan hashes, workspacepaths và reparse guards. Chỉ nativePowerShell
LiteralPathRemove-Item chính xác cây `candidates` sau verify; không xóa raw,
receipts, networkjournals, contracts hoặc kết quả đã seal. Historical PARTIAL
của batch 800 giữ nguyên; lưu lạnh không promote source/data quality.

Trong orchestration, invocation đầu đã prune500 rồi dừng an toàn ở800 vì ZIP800
còn đang được tiến trình nén độc lập ghi. Source800 giữ nguyên; chờ archiveverified
rồi resume từ checkpoint, không overwrite ZIP hoặc nén lại500. Các batch chỉ
prune tuần tự sau verify; lỗi orchestration không biến thành mất source/evidence.

713 direct input pins của result 50 còn nguyên và đều kiểm hash PASS; không pin nào
nằm trong bốn candidates được lưu lạnh. Handoff1.172 mã/11.720rows giữ đúngbytes.
Raw/receipts/network/results của bốn batch vẫn có tại chỗ; controller/journal
hashes không đổi. Full replay historical acquisition/QA cần restore cache khi
đến bước dùng candidates; không tuyên bố mọi historical runner chạy ngay không
cần restore. Sourcecode/configs giữ nguyên các pinned paths.

[Plan](../repository/financial-cache-archive-20261023/plan.json),
[verification](../repository/financial-cache-archive-20261023/verification.json),
[availability index](../archives/financial-cache-20261023/availability.json),
[hướng dẫn restore](../archives/financial-cache-20261023/README.md).
Root README vàSTART HERE được rút gọn theo tác vụ; bản trước đó lưu ở
[documentation snapshot](../repository/financial-cache-archive-20261023/documentation-before.zip).
`data/README.md` và`artifacts/README.md` giải thích vai trò từng nhóm; M2đọc
`data/handoffs/financial-reference-2016-2025/`, không gộp các versionfolders.

Kiểm chức năng archive/restore trênfixture: roundtripbytes/emptyfile,
source-mutation detection, từ chối destinationđãcó vàpathescapePASS. Compile,
PowerShellparse, activeanchors vànamedhandoffchecksPASS.0request/PDF/OCR,
khôngrefitmodel hoặc mởPIT/research gates. **PASS clean sâu trong scope bốn
normalized caches**; không tuyên bố toàn bộ project đã sẵn sàng public hoặc mọi
legacy raw đều có thểxóa. Nguyên tắc: hotdataset đểlàmviệc, sourceevidence để
kiểmchứng, coldcache chỉrestore khi cần.

### 2.28. Gom lịch sử vào archive — Execution55 (23/10)

Owner cho phép đưa các lượt không cần mở trực tiếp vàoarchive vàyêu cầu giữ
phần cần cho giai đoạn tiếp. Đã chuyển **206cây thư mục**:
**162data roots và44report roots**, chứa **41,526files /
5,209,548,640bytes**. `data/financial`:**221→59**; `artifacts/reports`:
**57→13**. Đây làsame-volumeMove-Item, khôngcopy/nén vàkhôngclaimdiskspacegain.

Giữ hot: các roots chứa797anchors của kết quả/bàn giao hiện hành, source references
trongfeature rows, controls, boundarypins, registry/epochs vàmapping/backlog
cần cho bước tiếp.59roots không phải59bộ dữ liệu dùngđồngthời. M2đọcduynhất
handoff1.172mã/11.720rows; các roots còn lại phục vụprovenance/control. Trongreview
trước move đã bổ sung58boundaryfiles vàgiữthêm32roots, tránh làm mất trạng thái
blockedhosts/counters. Bảnplan banđầu đượcgiữ trong `plan-review-initial.json`.

Kho: [financial-history-20261023](../archives/financial-history-20261023/README.md),
[catalogue](../archives/financial-history-20261023/catalogue.csv),
[verification](../repository/financial-history-storage-20261023/verification.json),
[plan vàlýdo keep](../repository/financial-history-storage-20261023/plan.json).
Update161liveMarkdownlinks sangđúngvịtrí archived report/data đểđọc trực tiếp;
khôngsửa nội dung/report/manifests đãseal. Changelog/old immutable links cóthể cần
restore trước replay; availabilityindex giữoriginalprefix→archiveprefix.

Kiểm chứng: đủtấtcả tênfile/size/mtime theo inventory, metadata vànetworkhashes
khôngđổi,797anchors hiện hànhPASS.205directoryIDs giữ nguyên. RiêngBRCdeepaudit
directoryIDkhác; kiểm đủ136memberhashes theo manifest đãpin trước move, cộnghash
củachínhmanifest, tấtcảPASS; khôngbỏqua nội dung chỉvìmetadata khác.
Restore/rearchive một report đã được thử thực tế, content proof khớp. Replay
DStock offline **PASS**, trả cùng result manifest và giữ nguyên network journal.
[Self-review55](../repository/financial-history-storage-20261023/self-review.json).

Khôngđổi sampling/formula/PIT/researchgates, khôngcrawl/PDF/OCR/fitmodel. Khi
replay giai đoạncũ phảirestoređủdependencies; trướcnetworkphảikếthừacounters,
sourceboundaries/deadlineshot/cold, khôngreset vìrootđãarchive. CácconfigM2 mới
phảipin delivery50/handoff hiệnhành, khôngtựdùngconfigpilottrỏvàoarchive.

## 3. Các mốc cải thiện định lượng

Chỉ so các mốc cùng bộ sáu **core ratios annual reference**, không cộng với sáu family EPS/P/E/P/B/F/M/Z.

| Execution | Thay đổi | Rows | Candidates có ≥1 kỳ | Full10 | Full10 tăng so mốc trước |
|---|---|---:|---:|---:|---:|
| 37 | Baseline exact-zero | 6.976 | 1.311 | 51 | — |
| 38 | What-if precision | Không thay dataset | Không thay | Không thay | 0; 505/550 chỉ sensitivity |
| 39 | Absolute + relative precision QA | 11.178 | 1.416 | 427 | +376 |
| 40 | Direct-method CFO parser correction | 11.835 | 1.422 | 459 | +32 |
| 41 | Single-document reviewed references cho ba gaps | 11.838 | 1.422 | 462 | +3 |
| 42 | Annual source audit; issuer HTML reference PLX2023 | **11.839** | **1.422** | **463** | **+1** |
| 43 | Full quarterly receipt triage; đề nghị2PDF chờ duyệt | 11.839 | 1.422 | 463 | +0 |
| 44 | Queue635 candidates; batch100 ưu tiên, PDF chờ duyệt | 11.839 | 1.422 | 463 | +0 |
| 45 | ReusablePDFpilot10; CNT2018 reviewed vector | **11.840** | **1.422** | **464** | **+1** |
| 46 | Resolve cache211/211; xuất reference cohorts và dependency queue | **11.840** | **1.422** | **464** | **0** |
| 47 | CachePDFreview DCM/VEA/PAN/VHC;131fields/21OCRpages | **11.844** | **1.422** | **468** | **+4** |
| 48 | HSG2reviewedcachevectors;DStocksourcepilot | **11.846** | **1.422** | **469** | **+1** |
| 49 | DStock722newrows sau additional cashQA | **12.568** | **1.422** | **1.002** | **+533** |
| 50 | Hoàn tất remaining API,15QAchecks trước nhậnrow | **13.529** | **1.428** | **1.172** | **+170** |

Từ baseline: **+5.592 rows, +111 candidates có ít nhất một kỳ, +951 full10 candidates**. Số full10 reference tăng không đồng nghĩa toàn bộ các năm của từng mã đều đã được đối chiếu tài liệu hoặc có publication evidence.

| Annual year | Rows hiện tại |
|---|---:|
| 2016 | 1.128 |
| 2017 | 1.203 |
| 2018 | 1.212 |
| 2019 | 1.240 |
| 2020 | 1.230 |
| 2021 | 1.233 |
| 2022 | 1.345 |
| 2023 | 1.334 |
| 2024 | 1.357 |
| 2025 | 1.286 |

## 4. Kết quả từng nhóm sản phẩm

### Core-ratio reference dataset

Đã có dataset tính được và source refs, thay vì chỉ lưu raw. Source kinds và mức xác minh khác nhau được giữ trong metadata. Các PDF vectors mới dùng toàn bộ input từ cùng document/year/scope; các API rows khác vẫn mang unit/scope/vintage hypotheses ngoài phần được review.

Không tự thay dataset của model đã fit ở Execution37 bằng dataset hiện tại. Nếu fit lại, phải dùng version mới và protocol phù hợp; reference counts không tự mở research eligibility.

### EPS, P/E, P/B, F, M, Z

Giữ 87 reviewed reference rows/11 issuers/5 full-six cohorts và pilot5 29/30. Nút thắt thường gồm weighted shares/numerator, original-maturity debt current portion, parent issuance, owned-PPE depreciation, dated price/common shares và comparative dependencies. Không dùng provider ratios thay tính lại, không lấy aggregate D&A/capital amount thay input khác nghĩa.

### PIT và M3

Vẫn cần report identity, publication/usable date theo observed exchange calendar, scope/vintage, historical security identity, revision-aware comparators và market handoff. Bản annual reference có thể dùng thông tin ex-post nên chưa được mang nguyên vào backtest. Không có final financial M3 PASS trong report này.

## 5. Những lỗi và giới hạn đã xác định

| Vấn đề | Đã làm | Còn giữ |
|---|---|---|
| API/UI annual gắn sai hàng | Named field/PDF comparisons, quarantine | Không auto-shift toàn bảng; Q4 không tự thay annual |
| Summary/deep route khác nhau | Bổ sung adapter/discovery theo đúng tab | Không coi summary thiếu là nguồn không có |
| Finance labels và raw codes không đồng nhất | Exact-template controls và staging | Không global-map theo label hoặc ordinal đơn lẻ |
| Precision residual nhỏ | Versioned two-cap exploratory QA | Không waive mismatch lớn hoặc mở PIT |
| CFO trực tiếp chưa được nhận diện | Exact code+label + component checks | Indirect/direct, annual/YTD và signs vẫn tách |
| Nhiều provider/vintage | Giữ partitions và mọi observations | Không chọn latest/average/source priority ngầm |
| Ngành có cấu trúc khác | Bank/Securities/Unknown tách riêng | Không áp score Regular đại trà |
| Lịch sử thiếu | Coverage theo năm và theo mã | Không missing→0, không ép doanh nghiệp chưa tồn tại có BCTC |
| Tài liệu đã cache bị bỏ sót | Cache inventory/hashes và reuse | Filename chỉ là hint, không period/scope proof |
| Project nhiều artifacts | Report tổng và index hiện hành | Chưa xóa evidence, chưa cleanup/public project |

## 6. Mốc hơn1.000 và việc còn lại

**Execution50:1.172full10.** [Dataset](financial-dstock-remaining-v1/dataset-result-ref.json), [delivery](financial-dstock-remaining-v1/delivery-result-ref.json),11.720full10rows. Đã thử hết2.444Regular gaps; còn761heldcases/257Regular,95mã9/10.93Bank/Securities/UNKNOWN táchschema. Không còn1.647cases chưa thử như mốc49. [Queue vàfields](financial-dstock-remaining-v1/report.md); sốPDF cần bổ sung chưa xác định. Ưu tiên review95one-gap vàAPI/cache/scope trước đề xuất tài liệu; không tự tảiPDF.

Bước tiếp là dùngreferencecohorts cho baselinefinancial theo protocol/version mới và xử lý publication/vintage/historicalidentity/market handoff choPIT/M3; EPS/P/E/P/B/F/M/Z còn dependencies riêng. DStockcreated/modified không làpublished_at. Network hiện đãdừng vìđạtmốc owner giao.

<details>
<summary>Phương án phục hồi trước DStock — lưu lịch sử, không phải kế hoạch chạy hiện hành</summary>


Tại Execution47 có **468 full10**, còn **532 mã** để đạt 1.000. Nhóm gần nhất còn **403 mã 9/10**, sau đó có 227 mã 8/10. Nếu mọi trường hợp chọn đều khắc phục được, phương án ít missing periods nhất là:

1. Phục hồi 403 mã thiếu một kỳ: tổng thành 871 full10.
2. Phục hồi 129 mã trong nhóm 8/10: tổng thành 1.000.
3. Tổng **661 kỳ mã–năm** cần phục hồi theo phương án lý thuyết này: 403 + 129 × 2. Đây không phải số PDF và không bảo đảm mọi mã đều khắc phục được.

Audit trước cho thấy 480 Regular candidates thiếu toàn bộ annual mapped fields ở ít nhất một năm, tổng 1.158 cases. Trong tập mapped inputs đó chỉ còn 949 candidates có khả năng full10 nếu mọi gate khác được giải; đây là bound có điều kiện của inventory hiện tại. So với bound 949 của mapped API inputs, đã bổ sung PLX bằng nguồn HTML độc lập; ít nhất 50 candidates khác ngoài tập này vẫn phải có missing annual input được resolve nếu muốn đạt 1.000, cùng việc chốt quality gates khác. 949/950 là bound có điều kiện, không phải số mã hiện sẵn. Không chỉ tăng tolerance.

Trong 1.158 annual gaps, 156 cases có đủ ba nhóm Q4 trong cache, gồm 19 cases2016 và 60 cases2025. Queue này cần xác minh interval/scope/vintage; không dùng Q4 income làm annual hoặc cộng EPS quý sai basis. Thiếu lịch sử trên API không chứng minh không công bố; niêm yết muộn cũng không tự chứng minh công ty không có BCTC trước niêm yết.

Ưu tiên tiếp: chốt nguồn/period/identity cho 124 one-year gaps không có annual mapped input; review QA lớn và multi-provider trên nhóm còn lại; kiểm catalogue/cache để xác định đúng document requirements. Nếu dữ liệu công khai không đủ hoặc doanh nghiệp chưa hoạt động ở đầu cửa sổ, giữ PARTIAL có lý do và xem xét historical discovery phù hợp thay vì tạo dữ liệu.

PilotPDF đã phục hồiCNT2018; tiếp theo xử lýsource/catalogue vàreview của chín targetcòn lại trongpilot. Approvalbatch100 còn hiệu lực trong scope/budgets, nhưng không tự mở50 khi pilot chưa có đủ source/extraction gates. [Flow vàtrạng thái](financial-pdf-pipeline-v1/report.md).

Yêu cầu mới nhất là **hơn 1.000 mã**. Để đạt mốc 1.001 theo cùng phương án có điều kiện, cần thêm một mã two-gap: **533 candidates/663 annual dependencies** hiện tại. [Queue Execution46 — archive](../archives/project-cleanup-20261023/historical-reports-and-scratch.zip) là snapshot trước khi bốn mã được giải quyết; loại DCM/VEA/PAN/VHC khi phân công tiếp. Chưa bảo đảm mọi kỳ tồn tại hoặc khôi phục được.

</details>

## 7. PDF, OCR và nguồn bổ sung

**Latest50 — toàn bộ Regular API gaps đã được thử:** **1.172 mã đủ10 annual periods2016–2025 /13.529 reference rows**, tăng170full10/961rows so với49. [Report50](financial-dstock-remaining-v1/report.md), [1.172mã](financial-dstock-remaining-v1/full10-candidates.csv), [cohort/features](financial-dstock-remaining-v1/delivery-result-ref.json), [field review](financial-dstock-remaining-v1/field-review.csv). Còn761held kỳ/257Regular và93candidates ngoài Regular schema;95mã thiếu1kỳ. 0PDF/0OCR;47targeted tests vàindependent verification PASS. Worker đã dừng. Core ratios reference; originalsixfamilies/PIT/M3 vẫn PARTIAL.

**Chỉ thị hiện hành:** owner đã duyệt đề nghị tối đa100PDF trong danh sáchbatch100, hai batch≤50 vàpilot10 trước. Execution45 mới dùng1PDF/4OCRpages; không xin lại cùngapproval, không tự mởngoài scope hoặc bỏpilotgates. Nội dungPENDING trong proposalExecution44 là snapshottrước approval, không phải trạng thái hiện hành.

| Mốc | Annual gap review cases | PDF mới tải trong mốc |
|---|---:|---:|
| Execution39 | 3.112 | 0 |
| Execution40 | 2.455 | 0 |
| Execution41 | 2.452 | 0 |
| Execution42 | **2.451** | **0** |
| Execution43 | **2.451** | **0**; đề nghị tối đa2PDF chờ duyệt |
| Execution44 | **2.451** | **0**; đề nghị batch100 thay ưu tiên2PDF, chờ duyệt |
| Execution45 | **2.450** | **1**; CNT2018, OCR4trang, pilot1/10referencecomplete |
| Execution46 | **2.450** | **0**; cache metadata211/211, 11case candidates; chưa review/accept |
| Execution47 | **2.446** | **0**; thêm4reference vectors từcache, OCR21trang |
| Execution48 | **2.444** | **1**; VDT2019scopeheld;HSG2cachevectors/OCR8trang |
| Execution49 | **1.722** | **0**;DStock722rows,0OCR;cashheld16 |
| Execution50 | **761** | **0**;DStock961newrows,0OCR;PDF requirement chưa xác định |

Inventory trướcExecution45:211 local PDF files/202 unique hashes. Execution45 thêm mộtPDFCNT2018 cóhash khôngnằmtrongsnapshot này. Execution46 resolve acquisition metadata toàn bộ211/211files (trướcđó28/211), không đồng nghĩa xác minh statement identity/content. Cache review queue46 có11annualcases; Execution47 đãnhận4vectors, còn7case chưanhận. Khôngsửainventorysnapshotcũđãseal. Số cases có filename hints là một phép tìm cache sơ bộ, không phải tài liệu đã xác minh đúng scope/vintage. **Số PDF mới xác nhận bắt buộc tải vẫn chưa xác định (`null`)**, không ghi 0 hoặc 2.452 như thể đã chốt. Một PDF có thể phục vụ nhiều fields/kỳ so sánh, hoặc một case có thể cần nhiều documents/notes; một số gaps giải được bằng API/cache hoặc không có lịch sử hợp lệ để lấp.

Mọi proposed supplement phải có issuer/report/year/scope/vintage, observed URL nếu có, cache status, fields cần bổ sung, lý do và budget. Giữ imported access boundaries; không retry 401/403/429/challenge bằng host/client/cookies khác. Resume không reset counters/deadlines; network/PDF/OCR cũ không được xóa khỏi ledger để làm đẹp totals.

## 8. Bản đồ file và lệnh chạy

| Cần xem | File/điểm vào |
|---|---|
| Tổng quan và lịch sử | **File hiện tại** |
| Plan, contracts, execution log kỹ thuật | [Financial history plan](../../docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md) |
| Danh sách candidates dùng chung | [Registry](../../configs/data/securities_collection_registry_v1.csv) |
| Cohort exports hiện tại | [Execution50](financial-dstock-remaining-v1/report.md),1.366≥5năm liên tiếp/1.172full10; [delivery](financial-dstock-remaining-v1/delivery-result-ref.json) |
| FlowPDF / pilot hiện tại | [Execution45 vàPowerShellrunbook](financial-pdf-pipeline-v1/report.md); batch100đãduyệt, pilot còn9targets |
| Dataset/counters/gaps mới nhất | [Ref50](financial-dstock-remaining-v1/dataset-result-ref.json), [verification](financial-dstock-remaining-v1/verification.json) |
| Review 412 mã ở Execution41 | [Near-full10 report](financial-near-full10-review-v1/report.md) |
| Source facts, trang PDF và quyết định | [Near-full10 audit — archive](../archives/financial-history-20261023/data/financial/history_near_full10_review_v1/results/c607f9e7f0a2b9185445/near-full10-audit.csv) |
| Full10 candidates hiện tại | [1.172mã](financial-dstock-remaining-v1/full10-candidates.csv) |
| Feature rows hiện tại | [13.529rows](../../data/financial/history_dstock_recovery_v4/results/6f72b963ca4391f4ea13/features.csv); [full10:11.720rows](../../data/financial/history_dstock_remaining_delivery_v1/results/6eadc4924d41c2de1f9f/features-10y-reference.csv) |
| Dashboard thu thập/QA cũ | [Local monitor](http://127.0.0.1:8765/monitor/); không thay report coverage hiện tại |

Lệnh pilot45 (snapshotcũ464, khôngphảicurrentdatasetcounter): `& 'C:/Projects/Intern/SourceCode-CafeF/scripts/financial_pdf_workflow.ps1' -Action status`. Chi tiếtprepare/run/verify trong [runbookExecution45](financial-pdf-pipeline-v1/report.md#powershell-dùng-chung).

Lệnh chạy lại **offline** reference replay Execution42 từ mọi thư mục PowerShell:

```powershell
& "C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" "C:/Projects/Intern/SourceCode-CafeF/scripts/financial_issuer_html_reference.py" --config configs/experiments/financial_issuer_html_reference_v1.json
```

Không chạy lại crawler/PDF/OCR chỉ vì đọc report hoặc muốn xem trạng thái. Các lệnh process/network trong execution cũ là lịch sử, không tự trở thành lệnh hiện hành. Report tổng không được đưa vào frozen experiment inputs; đây là live documentation.

Lệnh xem snapshot coverage47 từ mọi thư mục: `Get-Content 'C:/Projects/Intern/SourceCode-CafeF/data/financial/history_pdf_cached_four_import_v1/results/ff79f6eed55270156392/summary.json'`. [Runbook47](financial-cached-four-review-v1/report.md#flow-đã-thực-thi-và-khả-năng-chạy-lại).

**Lệnh coverage snapshot48:** `Get-Content 'C:/Projects/Intern/SourceCode-CafeF/data/financial/history_pdf_pilot_cache_import_v1/results/148d9f8a83f81e41cd6e/summary.json'`. Kết quả kiểm DStock: `Get-Content 'C:/Projects/Intern/SourceCode-CafeF/artifacts/reports/financial-dstock-source-pilot-v1/summary.json'`. Các lệnh47 phía trên giữ scope snapshot cũ.

**Lệnh số hiện hành50 từ mọi thư mục:** `& 'C:/Projects/Intern/SourceCode-CafeF/scripts/financial_dstock_remaining.ps1' -Mode Status`. `-Mode Offline` replay, không network. Worker đã hoàn tất; các runbook47/48/49 là lịch sử.

## 9. Nhật ký cập nhật report tổng

Execution48: HSG2 annual rows/64fields,8OCRpages; counters155→163. 11.844baseline rows unchanged;12ratios và2CFObridges kiểm độc lập. VDT2019 tải1PDF trong approvedpilot10 nhưng giữ scope review,0import. Shadow sign audit3potential/0accepted; theo owner chuyển sang DStock,6cases/4tickers,5cases11/11exact,TCM2013held,VHCcontrol8/8exact. DStock0PDF/0OCR/0accepted. 4unit tests,compileall,offline source/value audits và synthetic `run-20261023T074414Z-40b6d811` PASS; không fullsuite claim. GoalPARTIAL, kế tiếp DStocksourcecontract/pilot gapinventory. [Report48](financial-pilot-cache-recovery-v1/report.md), [DStock48](financial-dstock-source-pilot-v1/report.md).

| Ngày | Execution | Thay đổi | Coverage full10 | Kiểm tra và giới hạn |
|---|---|---|---:|---|
| 22/10/2026 | 41 | Tạo report tổng, tổng hợp lịch sử trước đây; review412 gaps, thêm3 PDF-scoped vectors | 459 → **462** | 39 targeted tests/compile/synthetic/source/value checks PASS; final goal PARTIAL |
| 22–23/10/2026 | 42 | Audit125annualholes;3emptyHTMLcolumns;PLXprimaryHTMLreference;CTDfiscalexception | 462 → **463** | 24tests/compile/synthetic/source/valuechecksPASS;0PDF/OCR;external3webtoolcalls riêng;goalPARTIAL |
| 23/10/2026 | 43 | Quarterly receipts125→124targets; boundedprimarylookup;2PDFproposal | 463 → **463** | 16tests/compile/synthetic/sourcechecksPASS;0PDF/OCR;goalPARTIAL |
| 23/10/2026 | 44 | Queue635/862cases; batch100 một-gap/một-check, PDF chờ duyệt | 463 → **463** | 4tests/compile/hash/dependenciesPASS;0network/PDF/OCR;goalPARTIAL |
| 23/10/2026 | 45 | PDFworkflow/pilot10; CNT2018;1PDF/4OCRpages; realresume | 463 → **464** | 41tests/compile/synthetic/sourceandvaluechecksPASS; pilotPARTIAL;next50closed |
| 23/10/2026 | 46 | Cache provenance28→211/211; cohort exports; queue667dependencies cho mốc1.001 | 464 → **464** | 14tests/compile/synthetic/source/exportchecksPASS;0download/OCR;goalPARTIAL |
| 23/10/2026 | 47 | DCM/VEA/PAN/VHC cache recovery;131fields/21OCRpages | 464 → **468** | 27tests/compile/synthetic/source/values/replayPASS;0download;goalPARTIAL |
| 23/10/2026 | 48 | HSG cache2rows; VDT scope held; DStock source pilot6cases | 468 → **469** | 4tests/compile/synthetic/offline auditsPASS; DStock0accepted;goalPARTIAL |
| 23/10/2026 | 49 | DStock600candidates/797cases;722rows saucashQA;cohortexports | 469 → **1.002** | Coverage>1.000đạt;42tests/independent/replayPASS;0PDF/OCR;originalfamilies/PIT/M3PARTIAL |
| 23/10/2026 | 50 | Thử hết remaining API1.647cases;961rows;15QAchecks vàcohort handoff | 1.002 → **1.172** | 761held/257Regular;47tests/independentPASS;0PDF/OCR;originalfamilies/PIT/M3PARTIAL |
| 23/10/2026 | 51 | Làm rõ flow CafeF+DStock vàprimary reasons; chỉ tài liệu | **1.172 → 1.172** | Offline evidence/link checks;0request/PDF/OCR;không field mixing hoặc policy change |
| 23/10/2026 | 52 | Review95one-gap,178rawfiles;4arithmetic-pass leads còn multiple partitions | **1.172 → 1.172** | 761inputpins/self-reviewPASS;0request/PDF/OCR;ưu tiên baselineM2tiếp, chưa fitmodel |
| 23/10/2026 | 53 | Cleanup:archive verified+cache removal+readable handoff | **1.172 → 1.172** | 2,889filesgỡ;no raw/counter/modelchange;M2chưachạy |
| 23/10/2026 | 54 | Lưu lạnh bốn normalized candidate caches | **1.172 → 1.172** | 102,504files gỡ; raw/receipts/journals giữ; 713 direct pins PASS; 0 model/network |
| 23/10/2026 | 55 | Chuyển162data/44report roots vào kho lịch sử | **1.172 → 1.172** | Data221→59;reports57→13;797anchorsPASS;0model/network |
| 23/10/2026 | 56 | Push checkpoint, tính lại 70.320 core ratios; fit 10 annual static models | **1.172 → 1.172** | Verification PASS; cả10năm có cụm nhỏ; chất lượng REVIEW_REQUIRED;0newPDF/OCR |

Các Execution8–40 được tổng hợp hồi cứu từ report/plan đã lưu, không giả rằng report tổng này đã tồn tại ở các ngày trước. Khi có sửa nhầm số hoặc scope, thêm ghi chú correction và trỏ source snapshot; không âm thầm sửa bằng chứng cũ.



## 10. Quy tắc cập nhật và chuẩn bị cleanup

Mỗi execution financial tiếp theo phải cập nhật file này cùng report run:

1. Cập nhật phần hiện trạng, latest result links và bảng định lượng theo đúng scope.
2. Thêm giai đoạn mới: vấn đề, cách xử lý, số trước/sau, tests, evidence và việc còn lại.
3. Ghi rõ số nào là actual/counterfactual/reference/verified/PIT; không đổi denominator để báo đạt.
4. Cập nhật PDF backlog và số downloads/OCR mới; nếu chưa xác định số tài liệu cần tải thì giữ null có lý do.
5. Thêm hàng nhật ký, đồng bộ active pointers; giữ report và artifacts đã seal nguyên vẹn.

**Cleanup53 đã thực hiện phần an toàn trước phân cụm; public packaging còn là việc riêng.** Trước khi xóa cần inventory dependency/hash refs và phân biệt source evidence, immutable run outputs, active code/configs/tests, cache/render có thể tái tạo và files tạm. Chỉ loại file không còn được tham chiếu sau khi verify; không xóa raw/manifest/receipt hoặc sửa frozen hashes để rút gọn project. Public documentation nên bắt đầu từ report tổng và các active plans thay vì buộc người đọc lần từng thư mục cũ.

## Checkpoint Git trước baseline financial — 23/10/2026

Owner yêu cầu commit/push trước tính lại tỷ số và chạy model trêncohort1.172mã.
Checkpoint gồmcode/config/docs vàreporttổng; rawdata/archives giữlocaltheo.gitignore.
26targetedtests choexploratory/DStock/remaining/dashboardPASS (HTTP localhost rerun
ngoài sandboxPASS), compileall vànode--check web/app.js/monitor/app.jsPASS.
Fullsuite chưaPASS: chạy trongvàngoàisandbox khônghoàn tất, stdout cuối ởPDFcache
fixtures; đãdừng cókiểmsoát, log ở.tmp/precommit-tests*/test.log. Khôngsửa/skip
assertions đểđạtgreen. Checkpointkhôngphải release/M2/M3acceptance; bướcmodel
chỉlàbaselinefinancial-only thăm dò theo protocolk3/zscore từngnămđãchốt.

Commit `f1a5ba7` đã tạo và push thành công lên
`origin/research/financial-data` của repository `trongnguyen1010/Risk-Adjusted-Momentum-Clustering`.
Automatic approval review ban đầu chặn push do cần xác nhận repository/payload;
owner đã xác nhận rõ trước khi retry đúng remote/branch. Không đổi giao thức để né chặn.

## Execution56 — tính lại core ratios và chạy baseline full10 — 23/10/2026

### Input và cách thực hiện

Sau checkpoint Git, dùng named handoff hiện hành và kiểm khớp frozen delivery
`6eadc4924d41c2de1f9f`, không rebuild acquisition hoặc sửa bản đã seal. Cohort đúng
1.172 registry candidates × 10 năm 2016–2025 = 11.720 dòng, không duplicate/missing.
Đối chiếu sáu tỷ số với tám input đã chọn; phục hồi đúng đường evidence cho CFO
trực tiếp và reviewed document vectors thay vì suy/điền missing.

| Nguồn vector trong cohort full10 | Dòng annual |
|---|---:|
| CafeF API selected partition, gồm direct-CFO recovery | 10.400 |
| DStock complete vector | 1.309 |
| Reviewed PDF đã có từ trước | 10 |
| Reviewed issuer HTML đã có từ trước | 1 |
| Tổng | **11.720** |

**70.320 giá trị core ratios tính lại khớp.** Đây là arithmetic replay trên
reference input đã chọn, không phải xác thực độc lập lại mọi fact với BCTC gốc.
Không mở thêm source priority, không mix provider trong một vector, không crawl
hoặc tải PDF/OCR mới. Không thay bằng EPS/P/E/P/B/F/M/Z.

Reuse static K-Means: k=3, seed42, n_init20, max_iter300, sáu core features,
zscore theo từng cross-section năm; không winsorize, PCA hoặc imputation.
Không dùng future-year rows để fit scaler; không gọi independent annual models
là Dynamic Clustering hoặc out-of-sample backtest. Cohort full10 cố định còn có
selection/survivorship bias, chưa phải universe đầu tư lịch sử.

### Kết quả model và vấn đề chất lượng

| Năm | Kích thước ba cụm (sắp giảm dần, không phải nhãn cố định) | Silhouette |
|---|---|---:|
| 2016 | 1.169 / 2 / 1 | 0,9255 |
| 2017 | 1.170 / 1 / 1 | 0,9398 |
| 2018 | 1.048 / 119 / 5 | 0,4349 |
| 2019 | 1.168 / 2 / 2 | 0,9079 |
| 2020 | 1.165 / 5 / 2 | 0,8851 |
| 2021 | 1.154 / 17 / 1 | 0,7695 |
| 2022 | 1.169 / 2 / 1 | 0,9125 |
| 2023 | 1.170 / 1 / 1 | 0,9406 |
| 2024 | 1.170 / 1 / 1 | 0,9269 |
| 2025 | 1.168 / 3 / 1 | 0,9045 |

10/10 models hội tụ nhưng **10/10 năm có cụm dưới 10 mã**. Kết quả hiện chủ yếu
tách các điểm cực trị; silhouette cao không đủ chứng minh cấu trúc cụm hữu ích.
Năm 2025: cụm ba mã VTI/CAD/JOS, singleton QBS và cụm 1.168 mã còn lại.
Ví dụ cần review: QBS net_margin=-522,434; CAD liabilities/assets=131,480;
VTI liabilities/assets=127,058 (đều là ratios, chưa nhân100%). Giá trị cực trị
không tự chứng minh lỗi nguồn: cần xem tử/mẫu, scope, đơn vị và tình trạng doanh nghiệp.

Đã lưu [180 dòng review top3 absolute zscore cho từng feature/năm](financial-full10-baseline-v1/outlier-review.csv)
và [33 memberships trong các cụm nhỏ](financial-full10-baseline-v1/small-cluster-members.csv).
Giữ nguyên dữ liệu và kết quả, không tự loại mã/cắt tails để cải thiện metric.

### Kiểm tra, bàn giao và bước tiếp theo

- **11 targeted tests PASS**, compileall và synthetic smoke PASS
  (`run-20261023T154334Z-8bc948c5`). Full repository suite từ checkpoint trước vẫn
  chưa có kết quả PASS; không diễn giải targeted tests thành toàn bộ gate.
- [Independent verification PASS](financial-full10-baseline-v1/verification.json):
  1.786 input pins; đúng 11.720 keys; scaler mean/population std tính theo từng năm;
  toàn bộ labels là nearest centroid; inertia/profile means/sizes khớp; checkpoint
  identity/checksum khớp. Không refit model trong review.
- [Report và thông số](financial-full10-baseline-v1/report.md),
  [result pointer](financial-full10-baseline-v1/result-ref.json).
  Output: `data/financial/financial_full10_baseline_v1/results/4d521e71139a48340d3d`;
  manifest SHA256 `4d521e71139a48340d3d00f5e505ab3f07613ed9754d5e5ceaf33172c99b1da3`.
  Có features, assignments, metrics và snapshots (scaler/centroid/profiles), pins/config/protocol.
- `scripts/financial_full10_baseline.ps1 -Mode Status` xem tiến độ;
  `-Mode Check` kiểm lại inputs; `-Mode Run` resume đúng pins/checkpoint hoặc tạo
  run mới nếu pins đổi. `scripts/financial_full10_review.py` kiểm không refit.

**Execution kỹ thuật COMPLETE; chất lượng clustering REVIEW_REQUIRED; final M2/M3 PARTIAL.**
Bước tiếp theo: review outlier queue từ cache và nguyên nhân tử/mẫu; đề xuất một
protocol preprocessing comparator (ví dụ rank hoặc robust transform, hoặc clipping
có policy rõ), giữ baseline này làm đối chứng. Thay preprocessing cần owner duyệt
và version mới trước khi chạy; không chọn bằng returns hoặc sửa model cũ. Còn cần
publication/vintages/historical identity và bàn giao market của team để mở PIT/M3.
Không tải PDF mới trong bước review nếu chưa hỏi owner.

**Bàn giao khi chuyển session:** [Execution56 handoff](../../docs/FINANCIAL_SESSION_HANDOFF.md)
giữ kết quả, trạng thái Git, lệnh kiểm tra và phạm vi cần owner duyệt trước bước mới.


## Execution57 — hợp repository market và financial — 23/10/2026

## Integration market–financial — 23/10/2026

Financial Execution56 checkpoint `819cd82` đã merge cùng market `340519d` trên
`integration/market-financial`. C8 V2 giữ19/19hashes; current market verifier kiểm84models,
75.801assignments, nearest centroid và eligibility, tạo reference handoff có version.
Financial vẫn11.720annualrows/1.172symbols; model không refit.

Shared KMeans/preprocessing hiện kế thừa market. Hai file source đã pin của Execution56
được lưu exact bytes tại `M2/artifacts/financial-execution56-frozen-source-v1/`;
historical review dùng explicit source overlay và output mới, không sửa frozen input hashes.

```powershell
python scripts/import_market_bundle.py 'C:/Users/ASUS/Downloads/DELTA_02_ACTIVE_M2_M3.zip'
python scripts/verify_market_financial_integration.py --publish
python scripts/financial_full10_review.py --source-root M2/artifacts/financial-execution56-frozen-source-v1 --output M2/artifacts/financial-execution56-integration-review-v1
```

Tại cuối2025 có1.148financialsymbols đồng thời market-ready; giao theo snapshot thay đổi.
Chưa có availability-aware historical join hoặc model kết hợp. Quality REVIEW_REQUIRED,
strict PIT/research/M3 vẫn false. Tests/gates integration được ghi ở Current status.


### Kiểm chứng integration đã thực hiện

- Market:19/19C8outputs,68holdoutoutputs,9frozenpins,84models và75.801assignments PASS;
  kiểm sourceeligibility và nearestcentroid, không refit.
- Financial:1.786inputpins,11.720rows, scaler/assignment/inertia/profiles/checkpoints PASS
  với hai frozen source files đúng hash trong sourceoverlay có version; output review riêng.
- 76 targeted tests: OK,4Streamlittests skipped do thiếu optionaldashboarddependency;
  6 PCAartifacttests PASS. Importer/immutability tests bổ sung PASS.
- compileall, synthetic smoke (`run-20261023T161947Z-e04ef3b8`), `node --check web/app.js` PASS.
- Full repository suite chưa PASS: sandboxtimeout240giây; lượt ngoàisandbox được giới hạn360giây,
  xem `.tmp/integration-full-suite-unsandboxed.json` và log. Không bỏ assertions.
- Plain diffcheck toàn nhánh có inheritedCRLF/Markdownhardbreak warnings từ market artifacts;
  scoped integrationdiffcheck với `cr-at-eol` không có whitespace errors. Không sửa sealedbytes để làm sạch warnings.



### Chốt integration — 24/10/2026

Đã xử lý toàn bộ merge conflicts; imported data giữ local theo ignore policy.
Financial checkpoint `819cd82`, market parent `340519d`; active branch `integration/market-financial`.
PowerShell wrapper `scripts/market_financial_integration.ps1 -Mode Verify` đã PASS:
market19C8outputs/68holdoutoutputs/84models/75.801assignments; financial1.786pins/11.720rows.
Targeted76tests OK (4optionalStreamlit skips), PCA6tests PASS, importer/immutability5tests PASS
(suite5 gồm4tests đã có trong targeted76 và1test bổ sung, không cộng trùng).
Compile, synthetic smoke và webJS syntax PASS; importer replay20files PASS.

Full repository gate vẫn PARTIAL: sandbox timeout240,2giây; ngoài sandbox timeout360,1giây,
ít nhất250testlines kết thúcok, chưa cóFAIL/ERRORtrước timeout; cuối log ở
`unit.experiments.test_financial_crawl_trial.TrialTests.test_invalid_payload_stops_next_wave_with_all_symbol_gap_rows`.
Không khẳng định suite treo hoặc xác định nguyên nhân từ việc timeout; không bỏ assertions.
Logs `.tmp/integration-full-suite*.log`, summaries `.tmp/integration-full-suite*.json`.

Không fit lại model thực, không acquisition/PDF/OCR mới, không backtest; PIT/research/M3
vẫn false, chất lượng cụm REVIEW_REQUIRED. Commit tích hợp chỉ local; chưa push remote.



### Portable financial replay — 24/10/2026

Kiểm thử Git export phát hiện nhiều financial source pins cũ còn phụ thuộc LF/CRLF.
Đã thêm frozen-source-v2 giữ exact bytes toàn bộ16trackedsource/config/scriptpins từ
checkpoint819cd82, không bỏ bất kỳ hashcheck nào. Overlay chỉ áp src/scripts/configs;
raw/data pins vẫn kiểm tại path gốc. Review outputv2 giữ bảnv1 nguyên vẹn; explicitLF
cho reviewscript giữ checksum ổn định khi checkout. Đây là packaging/provenancefix,
không thay phép tính, sourcefacts hoặc model. Lệnh Verify hiện dùng overlay/reviewv2.


## Execution58 — A/B đối chiếu và C kết hợp đã chạy — 24/10/2026

Đã giữ A market-only (168 profiles/84tháng) và B financial-only (30 profiles/10năm)
riêng, tạo bảng đối chiếu và chạy C theo cấu hình owner đã duyệt trong chat.
C:14features, z-score từng năm trên common cohort, blockweights50/50,
KMeans k3/seed42/n_init20/max_iter300, no clipping/PCA/imputation. 7 models hội tụ,
5.593assignments trên2019–2025; independent verification PASS. C2025 có663/479/6mã;
cả7năm có cụm dưới10, quality REVIEW_REQUIRED. Không sửa A/B hoặc tối ưu bằng returns.

- [Report A/B/C](../reports/cluster-comparison-v1/report.md).
- [Bảng nhãn A/B/C cuối năm](../reports/cluster-comparison-v1/memberships-a-b-c-year-end.csv):9.213unionrows,5.593BOTH có C.
- [Catalog219profiles](../reports/cluster-comparison-v1/cluster-catalog-a-b-c.csv).
- [Protocol C](../../configs/experiments/combined_reference_v1.json).
- [C verification](../reports/combined-reference-v1/verification.json).
- [C result pointer](../reports/combined-reference-v1/result-ref.json).

Market liquidity_21 chiếm median99,997% phần tách centroid theo fittedmetric;
không tự chứng minh dataerror. Financial180outlierrows/157vectors replay đúng
selected inputs; scope/unit/facts chưa tự nghiệm thu. 0/11.720rows có published_at
trong delivery: C là EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT, khônghistoricalPIT,
khôngbacktest/M3, khôngnewholdout. Historical C vẫn cần gates theoUnifiedPlan§15–16.

Integration tới efb7104 đã push; Execution58 là công việc mới local, chưa push.
Full repository gate vẫn chưa có PASS; targeted và numerical verification ghi riêng.



### Execution58 verification và phạm vi còn lại

27 targeted tests PASS (8tests mới + financial/integration/clustering regression),
compileall PASS; synthetic smoke `run-20261024T021711Z-30619c75` PASS. Independent
C review kiểm lại scalers, weights, nearest-centroid, inertia, raw profile means và
centroids cho5593assignments/7models PASS. RerunC giữ nguyên bytes và timestamps
của numericaloutputs, khôngrefit; comparison idempotent và coverage9213/5593 PASS.
C kế thừa financialfull10fixedcohort, còn selection/survivorshipbias. Sourcefacts
không tự accepted, khôngclaimPIT hoặcnewholdout. Fullsuitegate vẫn PARTIAL;
lượtstage58 có log `.tmp/dual-combined-full-suite.log` và summaryJSON cùngprefix.


C2025 separation driver bổ sung: market block chiếm96,11% phần tách centroid,
financial3,89%, dù inputblockvariance cân bằng50/50. Đây là kết quả geometry thực tế,
không phải đặt weight sai; dominant features là mom126, mom252, mdd126, mom63 vàvol63.
Không đổi preprocessing hoặc weight sau khi xem kết quả. Queue cụm nhỏC2025 gồm
DNN/GTD/NVP/TVH/VEC/VIC; giữ evidence, chưa source-fact accept hoặc quarantine.


### Execution58 final gate — 24/10/2026

Fullsuite timeout 240.1giây, ít nhất254testlines kết thúcok,
không FAIL/ERROR trước timeout. Cuối log ở financial_crawl_trial fixture50;
không diễn giải timeout thành suitePASS hoặc xác định nguyên nhân treo.
Targeted27tests/compile/smoke/independentCverification đềuPASS. A/Bsourceartifacts giữnguyên.
Execution58 đã hoàn tất chạy và đối chiếu ở phạm vi descriptive reference; quality
REVIEW_REQUIRED và PIT/M3gates false. Không tự thay preprocessing sau kết quả.
