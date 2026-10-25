# Trạng thái hiện tại — M1 market foundation reported

## Indicators v1 — Giai đoạn 1–4 xong, local (25/10/2026)

Nhánh `feature/indicators-v1`. Input `data/financial/indicators_v1/inputs/inputs-5b4836454b70d737/`
(1.510 mã, 14.738 mã-năm; ngân hàng/CK/bảo hiểm từ raw CafeF; DStock lấp 616 mã-năm CafeF thiếu;
CFO của 181 mã từ LCTT trực tiếp). Kết quả `data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/`
(`indicators.sqlite`, 319.620 ô, `qa-report.md`). QA độc lập 800 ô PASS. Mục tiêu 2025 đạt hết:
EPS 92,5%, P/E 91,8%, P/B 91,5%, ROE 99,9%, F 88,4%, M 80,0% (sát ngưỡng; 114 ô dùng khấu hao
dự phòng từ hao mòn lũy kế), Z 91,2%. EPS khớp EPS công bố ±10%: 75%.
Giai đoạn 4 xong: 4 endpoint `/api/v2/stocks/{ticker}/{overview,fundamentals,scores/{year},peers}`
(`web/backend/app/fundamentals.py`, pointer `configs/product/indicators_v1.json`), 7 API tests mới PASS.
Tiếp theo: Giai đoạn 5 (UI trang cổ phiếu).

## Bổ sung EPS theo kỳ và UX chỉ số — local, chưa release (24/10/2026)

Đã chạy offline trên inventory 1.522 mã: đối chiếu raw code/label/đơn vị EPS,
period/provider và raw value, giữ 53.716 reported EPS observations/1.427 mã
(12.782 annual, 40.934 quý/lũy kế). Serving source có 47.208 EPS/1.426 mã sau
khi giữ 6.508 source-zero chưa xác nhận ở trạng thái chờ đối chiếu; không gọi
reported EPS là EPS tự tính hoặc independently verified. Ledger gồm 85.212
period/mode slots × 6 families = 511.272 cells, có cả kỳ chưa có số.
79.566 calculator evaluations/13.261 annual provider partitions vẫn chưa sinh
score mới đủ điều kiện release: weighted shares/EPS numerator, đủ9 F signals,
owned PPE depreciation, reconciled EBIT và dated valuation basis còn thiếu.
Không dùng inferred shares/proxy EBIT hoặc ghép giá để tạo coverage giả.
UI đổi sang năm/kỳ báo cáo và giải thích mục đích từng chỉ số; technical package
IDs/vintages/hashes xuống source details. API đọc SQLite EPS theo ticker, không
load 53k evidence rows mỗi request. 26 targeted tests, compile/synthetic smoke và
production build PASS ở lượt kiểm này. Chưa đóng research/PIT gates hoặc deploy.
[Runbook và artifacts](../web/README.md#bổ-sung-eps-theo-nămquý-và-trải-nghiệm-chỉ-số).

## Nâng cấp DELTA — triển khai local, chưa release (24/10/2026)

Đã triển khai D0/D1/U1–U3, diagnostics R0 và bounded R1 theo yêu cầu thực hiện
hoàn chỉnh plan. [Kết quả từng stage, pins/tests và gates còn mở](DELTA_UPGRADE_PLAN.md#11-thực-thi-nâng-cấp--24102026).
87 unique numeric observations/11 mã; hai Z FY2024 đã nối đúng vintage. UI năm trang
đã tổ chức lại, 25 responsive cases PASS; R1 757 models được independent replay PASS. Có selector P1/P3 preview (202 snapshots), baseline vẫn mặc định.
Chưa promote model, chưa đóng source/usefulness/PIT hoặc public release. Full suite
984 tests còn một error do thiếu immutable legacy fixture, bốn Streamlit skips.


## Rà soát demo: sáu chỉ số và đồ thị phân cụm — 24/10/2026

Đã sửa omission product: EPS/P/E/P/B/F/M/Z đã review có panel riêng tại Tra cứu cổ phiếu,
API v2 indicators, pin hai nguồn (85 numeric rows/11 mã và pilot5 29/30 subset; không cộng trùng).
FPT pilotFY2025: EPS5216,068015; PE14,301961; PB3,483579; F3/9; M−2,279981; Z7,106292.
PE/PB dùng raw22/04/2026, book31/12/2025; không gán vào market31/12/2025 như PIT.
Snapshot/vintage và YTD/quarter được giữ riêng; VNM F thiếu vẫnnull. Không tính lại/model mới.

Review source `dual-cluster-review-v1/separation-drivers.csv`: A31/12/2025 liquidity share
0,9999658458053156; native groups26/1384. Atlas cảnh báo rõ baseline bị liquidity chi phối.
Website owner gửi (`cafz.phuongquan.vn/companyDetail/FPT`) có tab Tech Peers Clustering,
quan sát7mã/3màu/trụcPE–ROE, chưa có protocol/scaler/cohort đầy đủ để chứng nhận chất lượng.
Không lấy giá trị hoặc labels của website làm research input.

Giao diện demo đã Việt hóa theo yêu cầu owner: 5 màn hình, nhãn đặc trưng, trạng thái, hướng dẫn và định dạng `vi-VN`; giữ mã feature, công thức và protocol gốc để đối chiếu. Không thay dữ liệu hoặc mô hình.

## Execution59 — Demo web A/B/C đã triển khai — 24/10/2026

Web mới `web/frontend` (Next.js/TypeScript/ECharts/TanStack) + `web/backend` (FastAPI)
đọc SQLite presentation local, giữ dashboard cũ. Adapter không fit/scaler/research metric.
Bundle thật có 75.801 A, 11.720 B, 5.593 C observations và 3.214.287 daily price rows.
API verify checksum, read-only; missing/ambiguous fail closed, không forward-fill hoặc
trộn price basis. Migration alignment chỉ đổi display target labels; original labels giữ nguyên.

10 API contract tests PASS; compileall + legacy JS syntax PASS; production build PASS.
Verifier thực PASS: 101 snapshots/219 profiles/7 matrices/22 hashes, sample price replay.
Full suite 240s: PARTIAL, 254 tests OK trước fixture crawl 50 mã bị timeout; không có full-suite PASS.
Browser QA đã kiểm Overview, Atlas C/tiny cluster/FPT drawer, Stock Explorer,
Financial matrix/FY2016 empty state và Research Lab; responsive 390px.

Chạy `python scripts/start_delta_terminal.py`; [setup và giới hạn](../web/README.md).
Code stage59 đang local; chưa push. Data, node_modules và .next bị ignore.
Financial published_at vẫn 0/11.720; fixed full10 survivorship bias và tiny clusters chưa giải quyết.

## Execution58 — A/B đối chiếu và C kết hợp đã chạy — 24/10/2026

Đã giữ A market-only (168 profiles/84tháng) và B financial-only (30 profiles/10năm)
riêng, tạo bảng đối chiếu và chạy C theo cấu hình owner đã duyệt trong chat.
C:14features, z-score từng năm trên common cohort, blockweights50/50,
KMeans k3/seed42/n_init20/max_iter300, no clipping/PCA/imputation. 7 models hội tụ,
5.593assignments trên2019–2025; independent verification PASS. C2025 có663/479/6mã;
cả7năm có cụm dưới10, quality REVIEW_REQUIRED. Không sửa A/B hoặc tối ưu bằng returns.

- [Report A/B/C](../artifacts/reports/cluster-comparison-v1/report.md).
- [Bảng nhãn A/B/C cuối năm](../artifacts/reports/cluster-comparison-v1/memberships-a-b-c-year-end.csv):9.213unionrows,5.593BOTH có C.
- [Catalog219profiles](../artifacts/reports/cluster-comparison-v1/cluster-catalog-a-b-c.csv).
- [Protocol C](../configs/experiments/combined_reference_v1.json).
- [C verification](../artifacts/reports/combined-reference-v1/verification.json).
- [C result pointer](../artifacts/reports/combined-reference-v1/result-ref.json).

Market liquidity_21 chiếm median99,997% phần tách centroid theo fittedmetric;
không tự chứng minh dataerror. Financial180outlierrows/157vectors replay đúng
selected inputs; scope/unit/facts chưa tự nghiệm thu. 0/11.720rows có published_at
trong delivery: C là EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT, khônghistoricalPIT,
khôngbacktest/M3, khôngnewholdout. Historical C vẫn cần gates theoUnifiedPlan§15–16.

Integration tới efb7104 đã push; Execution58 là công việc mới local, chưa push.
Full repository gate vẫn chưa có PASS; targeted và numerical verification ghi riêng.


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


**Integration market + financial — 23/10/2026.** Nhánh `integration/market-financial`
kế thừa financial checkpoint `819cd82` và market `340519d`. C8 V2 đã nhập từ
`DELTA_02_ACTIVE_M2_M3.zip`, giữ đúng hashes và path. Market có 84 snapshots
2019–2025, K=2/robust; financial có 1.172 mã × annual 2016–2025, K=3/zscore.
Đây là hai baseline độc lập. Cả hai cần review chất lượng cụm; strict PIT/research/M3
chưa được nghiệm thu. Giao ticker tại cuối 2025 là 1.148 mã, chưa phải historical PIT join.

Chạy `scripts/verify_market_financial_integration.py --publish` để kiểm current
60+24 artifacts và tạo manifest tham chiếu có version; script này không fit.
`verify_m2_task12.py` và `generate_m2_task13_handoff.py` là historical V1,
không dùng chúng để tái tạo current84. Xem `M2/artifacts/market-financial-integration-v1/`.

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

## Ghi chú và lineage từ các giai đoạn trước

**Execution56 — baseline financial đã chạy (23/10/2026):** 1.172 candidates × 10 annual
periods, 70.320 core ratios tính lại khớp, 10 static K-Means models hội tụ. [Report](../artifacts/reports/financial-full10-baseline-v1/report.md),
[verification](../artifacts/reports/financial-full10-baseline-v1/verification.json).
1.786 input pins, scaler từng năm, assignments/inertia/profiles và checkpoints đã kiểm độc lập.
11 targeted tests/compile/synthetic smoke PASS. Chất lượng **REVIEW_REQUIRED**: mọi năm có cụm
dưới 10 mã, năm 2025 là 1.168/3/1; không gọi M2/M3 final PASS. Giữ protocol hiện tại,
không tự loại outliers hoặc đổi scaling. Checkpoint trước chạy `f1a5ba7` đã push lên
`origin/research/financial-data`. Các section dưới là lịch sử.

**Execution55 — lịch sử đã gom:** data221→59roots, reports57→13. [Archive vàrestore](../artifacts/archives/financial-history-20261023/README.md). Giữ dependency/control của dataset1.172mã; M2chỉ đọc handoff hiệnhành. Phân cụm chưa chạy.

**Cleanup54 — cache cũ đã lưu lạnh:** 102,504candidatefiles từbốn batch được chuyểnZIPđãverify, raw/receipts/journals giữtrực tiếp. [Guide restore](../artifacts/archives/financial-cache-20261023/README.md). Chỉdùng [handoff mới nhất](../data/handoffs/financial-reference-2016-2025/README.md) choM2; dataset1.172full10khôngđổi, chưa phâncụm. Fullhistoricalreplay cóthểcầnrestorecache.

**Bắt đầu với bộ financial hiện hành:** [Dataset1.172mã/2016–2025](../data/handoffs/financial-reference-2016-2025/README.md) · [Report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md) · [Lệnh đang dùng](../scripts/README.md).

**Cleanup53 đã hoàn tất, phân cụm chưa chạy:** 2,889file đãgỡ khỏiworkingtree; report/helpers lịch sử giữZIP cóhash vàrestore, cachetái tạo đượcxóa. Không đổi raw/canonical, counter, dataset13.529rows/1.172full10 hoặc model. Chi tiếttạiExecution53 trongreporttổng. Các sectioncũ dướiđây làlineage, khôngđại diệnworker đangchạy.

**Báo cáo tổng financial:** [Mở lịch sử và tiến độ hiện tại](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md). Cập nhật liên tục qua các giai đoạn; đọc trước các report theo run.

**Ưu tiên hiện tại — Execution50 (23/10/2026): 1.172 mã đủ annual 2016–2025 / 13.529 core-ratio reference rows.** Đã thử hết 2.444 Regular gap cases qua49+50; tăng170full10 và961rows, giữ12.568baseline rows. Còn761held kỳ/257Regular candidates và93candidates ngoài Regular schema;95mã thiếu1kỳ. [Report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [report50/runbook](../artifacts/reports/financial-dstock-remaining-v1/report.md), [1.172mã](../artifacts/reports/financial-dstock-remaining-v1/full10-candidates.csv), [cohort/features](../artifacts/reports/financial-dstock-remaining-v1/delivery-result-ref.json), [field review](../artifacts/reports/financial-dstock-remaining-v1/field-review.csv). 47targeted tests/independent verification PASS;0PDF/0OCR. Worker đã dừng. EPS/P/E/P/B/F/M/Z toàn lịch sử và PIT/M3 vẫn PARTIAL. Xem `scripts/financial_dstock_remaining.ps1 -Mode Status`; dashboard acquisition cũ không phải counter DStock.


**20/10/2026 — Financial F3 critical review/reference PARTIAL; goal ACTIVE.**
[Execution hiện tại](crawl/FINANCIAL_HISTORY_PIT_PLAN.md#21-execution-tiếp--gas-pdf-reference-và-shs-critical-quarantine-20102026),
[PowerShell](../scripts/financial_history_process.ps1),
[critical review — archive](../artifacts/archives/financial-history-20261023/data/financial/history_critical_review_v1/4c87c15431782b8e491b/summary.json).
GAS PDF32reviewedfacts,2Z″EM referencevalues cho2025/2024 từ FY2025vintage;8accountingchecksPASS.
GASannualHKCDKT:2namedfields sai lệch, Q4 đúng theoPDF. SHSannualKLCTT:7namedPDFnonzero/APIzero,
1unresolvednonzeroorphan;2APIpartitionsquarantine, khôngrepair/accept. SHSreusePDFcache10MB,
publication website22/03/2026 không gán sangcachedPDFcover23/03/2026. GASexplicitpub04/03/2026.
OCR130pages/0errors. Cumulative2.284requests/211.688.837bytes/18PDFattempts;2SHSfileschạpcap25MB
vẫn được tính, khôngretry/reset. VDSC2HTTP302 khôngfollow; BMSCDBC2013linklegacyHTTP chưa dùng.
IndependentF3audit vẫn4/6/35fieldmatches+1signconflict; DCM/HSG2025 và2auditPDF cònmở.
Baseline29/30/VNM Fnull, strictPIT0, chưa50/M3.167targeted/compile/syntheticPASS;activeverify PASS;cachepreflight209PDFfiles/200uniquehashes.
Fullrepo gate chưaPASS; knownM2-PREP frozenhash mismatch giữ nguyên, không waiveassertion.

**19/10/2026 — Financial history pilot5: acquisition COMPLETE, QA/delivery PARTIAL.**
[Flow/commands](crawl/FINANCIAL_HISTORY_PIT_PLAN.md#9-qa-offline-và-handoff-bổ-sung-chọn-lọc),
[final acquisition](../data/financial/history_pit_v1/reports/4bf06a5671299d42c73f/report.md),
[offline QA — archive](../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/1692b3eb579b426c1e2f/report.md).
Worker đã kết thúc: 563 new requests/attempts, 5.313.164 bytes, 27 cache hits,
71.073 candidate cells, không pending. Coverage980: 918 main candidate-present,
5 auxiliary, 57 missing (19 issuer-periods). Catalogue host latch giữ nguyên.
QA riêng không sửa acquisition code/raw: 1.161 structural group-header zeros được
chứng minh từ đúng template, 69.912 nonstructural cells; 7.890 code/label mappings
chỉ diagnostic. 1.551 raw accounting equalities/95 differences; annual–Q4 có
6.652 equalities/1.993 differences, giữ provider partitions và unknown vintage/scope.
Detector bắt BRC/VNM FY2025 row shifts dù tổng cân, không sửa vị trí. Reviewed
PDF raw-value comparisons:138match/12conflict; không suy unit hoặc acceptance.
Queue90issuer-periods (6priority1/84priority2),13có cache PDF candidates. H1 không
tự thay Q2. 0 new accepted/PIT facts; chưa historical compute/batch20. Baseline29/30,
VNM F thiếu input. 59 targeted tests/compile/synthetic smoke PASS; acquisition và
QA replay kiểm độc lập; [validation — archive](../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/validation/verification.json).
Registry/code pins và counters cũ giữ nguyên; không tiếp resume acquisition đã hết task.

**19/10/2026 — Materialize hai plan và registry team: OFFLINE INVENTORY COMPLETE; acquisition PLANNED.**
[Market ≥1.500 cổ phiếu lịch sử](crawl/MARKET_HISTORY10Y_1500_PLAN.md),
[financial history/PIT](crawl/FINANCIAL_HISTORY_PIT_PLAN.md),
[registry dùng chung](../configs/data/securities_collection_registry_v1.csv).
Market chính2016–2025 +warm-up2013–2015; financial2013–2025 +closing2012 khi cần.
Registry1.522 current candidates =500C5+452C7complete+7failed+3partial+138not-yet+422outside.
952C8processed/905ready tại28/08/2026; identity/M3 chưa verified. Current discovery
không phải historical census. Local financial exports/pilot5 được inventory, phần
khác giữ UNKNOWN/NOT_INVENTORIED; counts reference chỉ FY2025 pilot5, không full history.
Không network/OCR/crawl mới, không sửa sealed data hoặc reset boundaries; pilot vẫn29/30.
Next work theo stageM0/F0 của hai plan, không chạy scale từ CSV ngay.
Offline checks PASS:1.522unique/45columns,37pinned source files, C8price SHA khớp
sealed manifest và17local links của hai plan. Financial:5pilot references+50other
candidate exports;1.467not-inventoried trong scope quét, không kết luận chưa crawl.

**19/10/2026 — VNM subsidiary debt review: PARTIAL 29/30.**
[Evidence/replay](../data/financial/vnm_subsidiary_debt_review_v1/report.md).
Thêm 7 PDF: MCM/Vilico 2025, Vietsugar 2024/2025 + AGM, VNM Q1/2025;
50.239.615 bytes, 54 trang render/40 ảnh xem/0 OCR thành công. MCM/Vilico
cùng nhóm vay 4–6 tháng, chỉ loại một lần trong diagnostic bounds. Vietsugar
đối chiếu được 587.715.602.250/420.793.498.260 VND nhưng kỳ hạn gốc chưa rõ;
không loại chỉ theo nhãn ngắn hạn. Hai kết quả leverage vẫn có thể xảy ra.
0 accepted metric inputs; giữ 29/30/gates false. Đã soạn yêu cầu IR, chưa gửi.
34 targeted tests PASS; offline replay/compile kiểm riêng, không lặp full gate.

**19/10/2026 — VNM quarterly-debt follow-up: PARTIAL 29/30.**
[Evidence và replay](../data/financial/vnm_quarter_debt_followup_v1/report.md).
Tải thêm Q4/2024 XLSX và Q4/2025 PDF từ observed links: 2 requests,
4.179.903 bytes; 16 trang render/8 ảnh xem/0 OCR. Workbook chỉ ba statement sheets;
Q4/2025 và cached H1/2025/H1/2026 chưa tách closing original-maturity current
portion 2024/2025. PDF xác nhận tổng vay Q4/2025 cao hơn QUY API 1 triệu VND.
Primary Piotroski Table 1 xác nhận phải gồm current portion; không đổi công thức.
0 new accepted metric inputs; giữ nguyên result, 29/30 và các gates false.

**19/10/2026 — Kiểm tra nhận xét dữ liệu quý/năm của owner.**
[Report](../data/financial/cafef_quarter_row_check_v1/report.md).
11QUYCDKTrequests cho5mã;2.876cells; annual dùng pinned cache, BRCUIlive xác nhận.
Các hàng vay/quỹ BRCQ4/2025 đặt đúng nhóm hơn annual2025; VNMcũng có mẫu lệch
annual319–323. Chưa kết luận mọi quarterlyfield đúng:64arithmetic checks có4conflicts,
gồm BRCQ1/2026totalassets0, BRCQ4/2025chênh50triệu và VNMQ4/2025chênh1triệu.
Quarter/reviewedPDF có revision differences; không dịch hàng hoặc accept toàn bảng.
Không thay29metrics/gates; gap original-maturity VNM chưa đóng.

**19/10/2026 — Closing-debt continuation: PARTIAL29/30.**
[Flow](crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md),
[result](../data/financial/pilot5_completion_v1/results/ee79bf4278f3ae944d02/report.md).
Acquire1PDF mẹ VNM2.626.709bytes; note16/PDF40 xác nhận vay mẹ1–12tháng.
Closing current portion tại công ty con vẫn thiếu2024/2025. Không lấp bằng flow
phân loại lại hay số2023. Runner nhận reviewed closing-stock pair, QA components,
PDF/image pins; PowerShellrun/replay/verify và terminal cache thực chạy.
29giá trị baseline không đổi; goal30chưa đạt; financial/research/cluster gatesfalse.
46targeted tests/compile/synthetic smokePASS; full448tests447PASS/1pre-existing
M2-PREPdocs hasherror, không thay assertion hoặc frozen artifact.

**19/10/2026 — Provider/PDF validation:**
[runbook](crawl/FINANCIAL_PROVIDER_VALIDATION_USER_GUIDE.md),
[report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-vietfin-pilot5-v1/report.md).
Đã kiểm wheel VietFin0.2.0; controlled routes TCBS15/15HTTP404 và SSI1catalogHTTP403
rồi stop, chưa chạySDK và0new provider fields đượcQA. Reuse235pinned reviewed facts,
176comparisons=164MATCH/12conflicts; selected PDF references và recompute29/30
giữ nguyên. VNM F chưa rõ current portion2024/2025.0newPDF/OCR, không resetCafeF.
34targeted tests/compile/synthetic smoke/PowerShell review+verifyPASS.
Full436tests435PASS/1pre-existingM2-PREP docs hasherror; không thay assertion/evidence.

**19/10/2026 — Dọn entry scripts:** flow financial hiện tại là
[pilot5](crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md). 48 legacy entry scripts
được gói vào verified ZIP rồi gỡ khỏi `scripts/`. Đã dọn thêm 8 thư mục báo cáo cũ; tổng 5.548 file. Xem
[inventory](../artifacts/repository/current-flow-cleanup-v1/plan.json) và
[restore](README.md). Các entry có ngày cũ bên dưới là lịch sử.
Shared code/tests/config và evidence dependencies được giữ; chỉ số vẫn 29/30.
Provider/PDF validation mới nhất ở entry trên; cleanup không thay số reference.

**18/10/2026 — CafeF pilot5 thực chạy:PARTIAL_WITH_RESULTS29/30.**
[Report](../artifacts/reports/financial-cafef-pilot5-execution-v1/report-v2.md),
[runbook](crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md).
BRC/FPT/MWG/GMD đủEPS/annualPE/book-snapshotPB/F/M/Z; VNM có5families,
F8/9signals interval4–5 vì closing original-long-term current portion2024/2025
chưa rõ dù đã đọc full VAS VN/EN.158unique field-periodMATCH; giáraw22/04/2026.
48attempts/38logical/3PDFattempts/7.103.375bytes/0newOCR; legacyEPSlatch nguyên.
PowerShell flow, immutable inputs/results,48targeted tests, compile/smoke,
Decimal QA/replay/resumePASS. Full421tests420PASS/1pre-existingM2-PREP hasherror.
Goal30chưa đạt; financial/research/cluster gatesfalse và cohort50baseline32/300
không đổi. Entry plan chưa execute bên dưới được giữ làm lịch sử.

**18/10/2026 — Financial pilot5 plan v2 (chưa execute):** [plan](crawl/FINANCIAL_CAFEF_PILOT5_EXECUTION_PLAN_V2.md),
[tổng hợp/handoff — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cafef-pilot5-handoff-v2/report.md).
Owner yêu cầu giao agent crawl lại vài mã tới actual metrics; chốt BRC/FPT/MWG/
GMD/VNM, annualFY2025/supporting2024/assets2023. Target5×6=30primary recomputed+
checked cells;3complete workflows chỉ checkpoint. Dedicated APIs/disclosure,
PDF/BCTNnotes, BRC row mismatch và per-group LCTT paging phải vào implementation.
Future agent thực hiện toànP0–P5, không dừng sau discovery/report/provider ratios.
Caps5mã/16PDF/400newOCR/6hnetwork, cache reuse; nguyên source/policy/gates và
old hard stops. Lượt này chỉ plan/verification,0newnetwork/OCR/metrics. Baseline
32/300references/production0 giữ nguyên; active handoff đổi từplan12 sangv2.

**18/10/2026 — BRC document deep audit:** [report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cafef-brc-deep-audit-v1/report.md),
[source cập nhật](crawl/sources/CAFEF.md). Computer-use đủ5document groups192links;
5disclosure pages92records exactURL/title/datejoins92/92. Tải6PDF/215pages, đọc
selected statement/notes,51visual candidates; đã có EPS numerator/WA, owned-PPE
DEP, capital no-change disclosure và supportingassets2023. Xác nhận annual2025
website debt sub-row mismatch1,18tỷ vsPDF24,14tỷ; cần code/label/template QA.
13scripted CDN attempts gồm6sandboxDNSfail,52.318.132successful PDFbytes;1browser
downloadtimeout giữ riêng. Owner xác nhận normal access trước UI audit; oldEPS
campaign latch không reset.0OCR/productionmetrics; strict acceptance/integration,
full history và TTM còn PARTIAL; baseline32/300/gatesfalse giữ nguyên.

**18/10/2026 — CafeF rediscovery BRC:** đã cập nhật trực tiếp
[source note](crawl/sources/CAFEF.md), [report/worklog](../artifacts/reports/financial-cafef-rediscovery-v2/report.md)
và route/field inventory. Đã khảo sát6main tabs/6financial tabs;5FinancialAjax
bodies chỉ ra CDKTv2/KQKDdetail/LCTT/ratios/plans; EPS detail UI có numerator,
weighted shares và share-days. Disclosure dates FPT/QNP LCTT dùng verified cache
lượt correction. **Live API validation PARTIAL:** scripted13attempts/1.528.364bytes,
11HTML thành công, EPS canonical gặp challenge; latch giữ true, không fetch tiếp.
12tasks chưa attempt, sector/history chưa verify.0PDF/OCR/acceptedmetrics mới;
baseline32/300referencecells và gatesfalse giữ nguyên. Bước sau: adapter/sample
validation của routes mới, không mặc định mở rộng OCR hoặc scale50/100.

**18/10/2026 — CafeF UI/API correction:** [report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cafef-disclosure-ui-correction-v1/report.md),
[source addendum cho agent](crawl/sources/CAFEF_DISCLOSURE_AND_FINANCIAL_TABS.md).
Sau phản hồi owner, kiểm trực tiếp FPT disclosure UI/API: `CreateDate`→ngày gửi,
20records cóID/link/date; FY2025audited ID/link khớp FileBCTC cũ. QNP LCTT tab
có dedicated GetReportLCTT JSON3groups, không phải chỉ summary hoặc PDF.
Current Python crawler thiếu cả disclosure/FinancialAjax/GetReportLCTT routes.
Discovery trước chưa đủ sâu ở các routes này; nguồn có metadata/data chưa tích hợp,
không gọi chung là “không có PIT/LCTT”.5scripted requests/473.570bytes,0PDF/OCR/
metrics mới; runtime/strict PIT/gates giữ nguyên. Agent đọc addendum trướcR1 của
plan12 đã lập; original sealed plan/report giữ nguyên.

**18/10/2026 — Financial replan / handoff:** [Tổng hợp — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-replan-20261018-v1/report.md)
và [plan thực thi R0–R5](crawl/FINANCIAL_CAFEF_REVALIDATION_PLAN.md) đã viết cho agent.
Goal: audit lại CafeF trên12 mã đại diện, crawl thử, sửa parser/mapping có evidence,
tính metrics thật và giao flow PowerShell tái chạy được. Profile thực dụng cho phép
reported EPS/PE/PB, QA theo template, thiếu publication không chặn số học và named
proxies/partial outputs; strict historical PIT/research/market-only giữ riêng.
Plan JSON **PLANNED_NOT_EXECUTED**, chưa đổi runtime hoặc chạy crawl mới.
Baseline gần nhất vẫn32/300 ô reference,10/50 mã, EPS10/Z10/F6/M6, PE/PB0 trong
assessment FY2025, production0. Snapshot nguồn50 từng có84,41% wire coverage;
không đồng nhất với metric/PIT readiness hoặc kết luận nguồn đủ/thiếu toàn bộ.
Đọc prompt cuối plan để giao trọn công việc; không bắt agent dừng xin làm tiếp
sau từng checkpoint trong scope. Các entry dưới giữ nguyên lịch sử.

Financial publication follow-up09/10/2026: **DISCOVERY VERIFIED / ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-publication-followup-v1/report.md).
GMD issuer posts ghi30/03/2026(FY2025),31/03/2025(FY2024), direct attachments exact SHA2/2.
Hai dates là candidates; đề xuất evidence class mới cầnMANUAL_REVIEW_REQUIRED theoAGENTS,
runtime explicit-publication-statement chưa đổi. MWG32postrecords/VHC408PDFanchors vẫn nguyên;
không chứng minh sameURL bytes unchanged. DGC notice screenshot có access challenge, không bypass.
Campaign evidence riêng7requests/28.096.954bytes,0OCR;21tests/compile/active workflow verifyPASS.
Old counters/deadline/facts giữ nguyên; deadline09/10/2026 11:26:53UTC đã hết.
32/300referencecells,10/50mã, production0/gatesfalse; periodic refresh/TTM/PE/PB/cluster chưa mở.
Các entry dưới là lịch sử.

Financial continuation09/10/2026: **RECOVERY_REFERENCE_COMPLETE / BOUNDED_OFFLINE_HANDOFF_VERIFIED**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-continuation50-v2/report.md).
GMD2024 đã tải đúng một lần,55pages OCR97,688s; thêm TA2023 và owned-PPE depreciation2024.
GMD FY2025 F5/9/M−2,330411, EPS/Z giữ nguyên. Cohort32/300referencecells(10,67%),
10/50mã,EPS10/Z10/F6/M6/PE0/PB0; production0/gatesfalse. Successor runV2 trên
`research/financial-data`, config riêng doctorPASS;110PDF/812OCRpages/706reservations,
230transport/134PDFattempts,965.495.640downloaded bytes, deadline vẫn09/10/2026
11:26:53UTC. Owner wrapper `scripts/financial_resume.ps1` + sealed adapterV3 giải quyết
inherited result thiếu pdf_sha256 mà không rewrite pinned V2.37targeted tests,
52pins/Decimal/cache replay/verify/smokePASS. Full suite có environment failures được
recheck10testsPASS; còn pre-existing M2-PREP docs/DECISIONS hash mismatch, không full-gatePASS.
Next: exact publication/human acceptance và bounded incremental discovery5–10,
sau đó TTM/events/PE/PB/sector/history; chưa periodic unattended refresh/next100/cluster.
Các entry dưới là lịch sử.

Financial DGC/GMD09/10/2026: **REFERENCE REVIEW COMPLETE / ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-dgc-gmd-review-v1/report.md). DGC37facts cho EPS7.402/EMZ13,817568/F5/9/M−1,919528; GMD35facts cho EPS3.839/EMZ9,305095, Fnull với6/9signals và Mnull vì thiếu depreciation2024; GMD2024PDF terminal download failure giữ nguyên. FY2025 cohort30/300referencecells(10%):EPS10/Z10/F5/M5/PE0/PB0,10/50mã có reference, production0. DGC audit ngoại trừ và restatedTA2023 (CafeF còn số cũ; mechanical sensitivity F5→4) giữ explicit lineage;50providerMATCH/21NO_PROVIDER/1VINTAGE_DIFFERENCE, canonicalnull.188unique OCRpages mới;3sandboxfailed records và3successfulretry, reservations376mới/651total,757pagescache.125pins/independentDecimal/23tests/compile/fullworkflowverifyPASS,0network mới. PIT exact publication/human acceptance/TTM/sector/scale gates còn đóng. Branch `research/financial-data`, frozenV1 doctor branch mismatch chưa đổi policy. Next: bounded GMD2024 recovery và publication/human acceptance, không tự100/cluster. Các entry dưới là lịch sử.

Documentation09/10/2026: **FINANCIAL INDICATOR HANDBOOK COMPLETE**.
[Handbook](research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md), [report/self-review](../artifacts/reports/financial-indicators-handbook-v1/report.md). Đã gom6financial families, EPS/TTM/valuation variants,9Fsignals/8Mcomponents, data dictionary/nguồn/kỳ/notes/PIT/QA/code và11market features. Existing contract/source note/runbook đã có nền tảng nhưng chưa bảng tra cứu liền mạch. Ghi rõ M accruals dùngTAcuối năm trong code khác average-assets của paper; không đổi runtime/formula/inputs/gates. Documentation và synthetic arithmetic examples được kiểm offline; các entry dưới là tiến độ data trước đó.

Publication discovery MWG/VHC08/10/2026: **DISCOVERY COMPLETE / ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-mwg-vhc-publication-review-v1/report.md). MWG official PostAPI liên kết BCTC FY2025 với23/03/2026 và FY2024 với24/03/2025; distinct PDF hashes, version association chưa accepted. FY2025 images/content/geometry46/46khớp, full fingerprint45/46 vì digital signature annotation; FY2024 official higher resolution chưa all-page equivalence. VHC2/2official PDFs khớp cache, chưa publication date. Giải trình30/03/2026 chỉ document date; landing-page date không được propagate. VHC notice No85 đề09/04/2025 nhưng explicit publication10/04/2025. Signed-at proxy chỉ là đề xuất reference riêng; runtime/DATE_ONLY/inputs/counters/gates không đổi. Latest references24/300, production0. Next: exact-version publication acceptance và VHC disclosure date; chưa date-overlay/crawl100.

Financial MWG/VHC F/M review08/10/2026: **REFERENCE CALCULATION COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-mwg-vhc-fm-review-v1/report.md). Full OCR101trang FY2024 cache, bổ sung26facts/mã vào v2 riêng; MWG F4/9/M−1,417454, VHC F7/9/M−2,863853; EPS/Z không đổi. Mỗi mã có4/6groups reference; latest cohort24/300FY2025cells(8%):EPS8/Z8/F4/M4/PE0/PB0,8/50symbols có ít nhất một reference.290pins/inventories và independent18Fsignals/16Mratios/8valuesPASS;23testsPASS/compilePASS. Provider50MATCH/22NO_PROVIDER/2VHC2024 signed-expense flags, canonical null. Exact-PDF publication FY2025+support FY2024 vẫn thiếu; human acceptance pending, all gatesfalse/production0.0acquisition requests/download mới; manual primary-web discovery riêng có candidate links chưa accepted. Exact-hash extraction selector là local bounded workaround, chưa production CLI scheduling. Next: publication/human/sign-basis acceptance rồi review DGC/GMD notes từ cache; không tự wave acquisition/100. Plan năm giai đoạn/market-only giữ nguyên; các entry dưới là lịch sử stage trước.

Financial MWG/VHC template review08/10/2026: **OFFLINE REFERENCE REVIEW COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Report/worklog — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-mwg-vhc-template-review-v1/report.md). User FullOcr46MWG/64VHCpages và tạo blank templates; agent đối chiếu18ảnh, điền11facts/mã trong input riêng, chạy4EPS/Z references. Latest FY2025 assessment20/300cells (EPS8/Z8/F2/M2),8/50symbols với ít nhất một reference. EPS printed rounding2/2, balance identities2/2, provider18MATCH/4NO_PROVIDER_FIELD; independent60pins/2reviewinventories/report PASS,23testsPASS/compilePASS. Không network/OCR mới; publication exact-PDF MWG/VHC thiếu, F/M còn chưa-review/history/semantics; tất cả gates đóng. VHC EPS current-vintage có caveat quỹ phúc lợi chưa duyệt; không gọi final-revision/TTM EPS.

Financial user run inspection08/10/2026: **INTEGRITY PASS / COLLECTION PARTIAL / NO NEW NUMERICAL REFERENCES**.
[Report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-user-run50-review-v1/report.md), [runbook](crawl/FINANCIAL_READINESS_USER_GUIDE.md). User Run `data/financial/user_workflow50_v1`:150 listings,91PDF mới,109vintages;2025 cóPDF41/50mã,2024 có27/50,2023 chưa tải.44PDF failure jobs (28timeout/14live404/2known404),123pendingPDF jobs;229attempts/947,97MB,17PDFattempts còn lại. OCR4PDF DGC/GMD/64trang mới, không có review/calculation mới; baseline6mã/16ô FY2025 giữ nguyên. Acquisition routing/cache/recovery cần hoàn thiện; không sửa code/config đã frozen, không mở financial cluster.

Financial local user handoff08/10/2026: **WORKFLOW HANDOFF COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Runbook](crawl/FINANCIAL_READINESS_USER_GUIDE.md), [report/tests/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-user-workflow50-v2/report.md).
Một runner PowerShell/Python: doctor/plan/audit/acquire/extract/run/template/review/verify; frozen50, FY2025 task matrix300 ô, history2023–2025. Durable network counters/access latch, OS lock, bounded OCR, immutable receipts/reports và human-attested reference calculator EPS/Z/F/M. Handoff QA không network: dùng lại cache, OCR mới16 trang MWG, replay2 PHP references; không mở cluster hoặc gọi PE annual là TTM. Bulk TTM/PB/sector adapters còn gap.

Financial scale validation08/10/2026: **MEASUREMENT COMPLETE / ACCEPTANCE PARTIAL**.
[Report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-scale-validation50-v1/report.md),
[50-symbol assessment — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-scale-validation50-v1/per-symbol.csv).
Đã kiểm50 annual listings:44 consolidated candidates,5 annual unlabeled,1 annual
listing gap.12 PDFs text-tested,11 predominantly scan/unreadable; code OCR294pages
cho4 mã mới. PHP/VCS/VEA/PAN tính8 EPS/Z references; PHP/PAN có DATE_ONLY exact-PDF
publication. Còn full F/M/TTM/PB, VCS/VEA publication, provider reconciliation,
scope/fiscal/sector layouts và unattended/resume integration.27/35 OCR statement
cells khớp visual review. Gates financial/cluster/research/next100 vẫnfalse.
Market-only và plan năm giai đoạn giữ nguyên; các đoạn dưới là kết quả stage trước.

Financial reference integration08/10/2026: **OFFLINE INTEGRATION COMPLETE / ACCEPTANCE PARTIAL**.
[Report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/cafef-financial-reviewed-integration-v1/report.md),
[config](../configs/data/financial_trial_integration_v1.json).15/900 ô annual có reference:
FPT9 ô2023–2025, ACV6 ô2025; thêm3 FPT TTM/valuation bridge values, tổng18 trong50.
VNM/PVS controls ngoài cohort. ACV có arithmetic nhưng thiếu auxiliary date-PIT và
TTM/event basis; không gọi6 metrics của ACV là production/PIT-ready. Strict0/900,
không accepted HTML facts mới, không network/PDF/OCR mới. Bước tiếp theo: review
notes/publication/vintage cho wave Regular PHP/VCS/VEA/PAN, đóng ACV/FPT gaps và
template10 mã financial-sector; chưa tự chạy wave/100 hoặc mở financial cluster.

Financial CafeF-first trial50,08/10/2026: **BOUNDED RUN COMPLETE / CANDIDATE DATA PARTIAL**.
[Report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/cafef-financial-trial50-v1/report.md),
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
[Report/log và cleanup — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-source-benchmark-v1/report.md),
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
[Report kết quả/log — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip),
[runbook](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md). Đã thử50/50 mã,300/300 base responses
parse được;90 history responses thiếu Head. FY2025 có ba statement wire headers rõ
trên50 mã, Q4/2025 đạt0/50 vì duplicate headers.409 requests/113.538.490 bytes;
8 PDF/604 text pages,555 low-text pages,0OCR,0accepted facts,0/900 strict task-ready.
Next: đóng quý/history contract, numeric templates/ground truth, PIT/notes/events
và đo ledger/verify cost trước trial100. Market-only workstream giữ nguyên.

Lineage chuẩn bị: [implementation/testing report — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip),
[planning report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-crawl-50-plan-v1/report.md),
[plan50](../configs/data/financial_crawl_50_plan_v1.json). Reports cũ giữ nguyên trạng
thái tại thời điểm bàn giao. Financial/cluster/full-universe gates vẫn đóng.

Financial user crawler update 06/10/2026: [report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-crawl-user-v1/report.md),
[hướng dẫn bàn giao](crawl/FINANCIAL_CRAWLER_USER_GUIDE.md), execution plan v9.
Runner mới không cần pilot artifacts: config mẫu chạy clean4 mã với12 structured
responses/4 PDF/343 text pages/1 selected OCR page. Batch10 mã có30 structured
responses/8.720 wire cells/2.180 target2025 cells; replay32 cache hits,0 network/
text/OCR/new checkpoints và exports byte-identical. Structured quarter FPT có
duplicate period columns,654 cells bị quarantine khỏi target coverage; raw giữ nguyên.
Discovery4 mã ghi hai CafeF404 FPT/VNM, exact issuer/mirror URLs trong config bàn giao.
Crawler handoff COMPLETE ở bounded candidate collection; mới0 accepted facts,
financial/cluster/full-universe gates vẫnfalse. Market-only workstream không thay đổi.

Financial automation update 05/10/2026: [report quá trình — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-batch-flow-v1/report.md),
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

Financial update 05/10/2026: [pilot ba mã/report và log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-three-symbol-pilot-v1/report.md).
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

Financial update 04/10/2026: [FPT acceptance/ESOP report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-fpt-acceptance-v2/report.md).
Latest acceptance_v5, equity_review_v1 và execution plan v6: sáu metric families có
reference values từ 24/08/2026. F/M/Z dùng annual 2025; EPS/PE dùng TTM đến 30/06/2026;
P/B là latest June equity + verified gross ESOP capital increment, không current net equity.
Bank proceeds = registered capital increase = 108.193.010.000 VND; registration effective
16/07, công bố 17/07. Tại 28/08, gross-capital P/B ≈ 3,1404; previous reported-equity
P/B ≈ 3,1489 giữ riêng. Phí, cash classification và subsequent movements chưa đủ evidence.
FPT reference handoff complete; FIN-D4 four-symbol closure vẫn PARTIAL, FIN-D5 pending.
Không tăng readiness 153/1.176/date 138/task 0/120 hoặc mở financial/research/scale gates.
Các update bên dưới là lineage, không phải latest blockers đã được giải quyết.

Financial update 04/10/2026: [FPT TTM/share-event report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-ttm-valuation-v1/report.md).
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

Financial update 03/10/2026: [source research/VAS report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-source-research-v1/report.md).
`source_completion_v5` là latest financial handoff. KBS trả15 JSON trên bốn mã;
4.796 wire cells chưa accepted. Thêm17 annual observations và13 H1 facts riêng;
readiness v12 đạt 153/1.176, date v6 có 138 date references; strict task v8 vẫn 0/120.
Hai transcription errors CFO/noncurrent debt 2024 đã có exact-PDF correction.
FPT2021–25 F-score VAS=4/6/6/7/3; strict F vẫn sáu known signals/totalnull.
M2024/25 có eight-ratio sensitivity, strictnull. Reported P/E/P/B20/03/2026≈14,30/3,48,
event coverage pending. H12026 EPS2.967 khả dụng24/08/2026; FTEL scope/reserve/share
bridge chặn latest TTM. EPS/Z flowv9 giữ revision handling. Các phần dưới là lineage
từng đợt. FIN-D2/3/4 PARTIAL, FIN-D5 pending; financial/research gates vẫnfalse.

## Cập nhật 2026-10-23 — Commit/push dashboard theo yêu cầu owner

Owner yêu cầu commit/push phần dashboard và handoff cần thiết trên branch
`m2-clustering-experiment`. Phạm vi 14 files: app/theme/test, dependency,
Git attributes, README/docs/changelog và 4 files handoff hiện hành. Không
đưa C8 gửi riêng, `.venv`, các legacy deletions/archive, notebook/report M2
hoặc thư mục models chưa tracked ngoài phạm vi dashboard vào commit.

Pre-commit validation: 22/22 dashboard tests PASS; full gate chạy 272 tests,
271 PASS và 1 ERROR do thiếu immutable Financial PIT evidence
`artifacts/financial_pit/fin-pit-1a-20261004T015420Z-continuation-preflight-v2/next_network_proposal.json`.
Đây là blocker cũ đã ghi nhận, không sửa test hoặc tạo evidence thay thế.
Compileall, `node --check web/app.js`, staged diff check PASS. Staged CSV bytes
khớp working copy và cả 3 hashes trong staged manifest; C8/venv không staged.
Self-review: dashboard scope PASS, toàn repository gate PARTIAL vì thiếu
Financial PIT evidence. Remote trước commit `6aadc1d0`, local `6a78a626`,
ahead 2 / behind 0; push thông thường, không force hoặc sửa lịch sử.

## Cập nhật 2026-10-23 — Bàn giao dashboard qua Git, dữ liệu gửi riêng

Owner xác nhận gửi riêng ba file C8 (`manifest.json`,
`canonical/feature_snapshots.jsonl`, `canonical/securities.jsonl`) dưới
`artifacts/cafef_primary/cafef-c8-complete-only-v2/`. Các file tiếp tục bị
ignore; không upload hoặc thay nội dung. Hướng dẫn cài đặt/chạy/verify offline
được đặt ngay START HERE tại [docs README](README.md); root README có link.

Thêm `.gitattributes -text` cho handoff hiện hành để bảo toàn checksum trên
Windows/Linux; pin pandas 2.3.3 cùng Streamlit 1.66.1 trong extra dashboard.
Người chia sẻ vẫn cần add/commit các file code/theme/config/docs và bộ handoff
hiện hành trước khi push. Phiên này không stage/commit/push hoặc sửa legacy
deletions ngoài phạm vi.

Validation/self-review: **PASS** — 22/22 dashboard tests; compileall; config
TOML parse; scoped diff check. Git clean filter với `core.autocrlf` lần lượt
true/false/input đều giữ đúng blob bytes của labels/profiles, hashes nguồn
khớp manifest. Không đổi runtime/model/data. Chưa thử clone/install mới trên
máy người nhận; hướng dẫn yêu cầu bộ C8 đúng lineage, không dùng bộ cũ 2026.

## Cập nhật 2026-10-23 — Cố định trục thanh khoản/beta, bỏ Stock Detail

Theo yêu cầu owner, mọi snapshot dùng X=`liquidity_21`, Y=`beta_126`. X symlog
với constant cố định 1.000.000.000 VND, Y tuyến tính; không chọn trục bằng
correlation hoặc thay theo từng snapshot. X lấy raw VND từ ticker JSONL, chỉ
nhãn trục quy đổi tỷ VND/phiên; tooltip giữ VND gốc. Giá trị zero giữ nguyên,
không epsilon/zero-fill/clipping. Missing đúng một trong hai tọa độ được báo
rõ, không dùng feature momentum cũ để quyết định row có được vẽ hay không.

Lựa chọn mô tả từ 168 monthly cluster profiles/84 snapshot: Cluster 0 có
liquidity và beta cao hơn Cluster 1 ở 84/84 tháng (60/60 development, 24/24
holdout). Median profile liquidity 307,46 tỷ so với 5,18 tỷ VND/phiên; beta
1,244 so với 0,383. Đây là mô tả profile, không phải feature importance hoặc
khẳng định mọi ticker của hai nhóm tách hoàn toàn trong 2D.

Đã bỏ phần chọn Chế độ xem và toàn bộ renderer Chi tiết cổ phiếu. Người dùng
xem ticker features trong bảng thành viên có tìm kiếm/phân trang; helper query
offline được giữ để bảo toàn source-consistency assertions. Các tests UI cũ
được migrate sang member table, bao gồm đủ 8 features và trạng thái MISSING.
Ô tìm kiếm có viền 1px cùng focus ring xanh. Lệnh chạy app giữ nguyên.

Validation: **22/22 targeted dashboard tests PASS**, bao gồm UI tại development
và holdout, cặp trục cố định, giữ zero thật, đủ 8 ticker features và các trạng
thái missing. `compileall` và `node --check web/app.js` PASS. Browser QA xác
nhận trục liquidity/beta, viền ô tìm kiếm và không còn Chế độ xem/Chi tiết cổ
phiếu. Source artifacts không thay đổi; không rerun full suite cho thay đổi UI
này (blocker evidence Financial PIT cũ đã ghi ở phần validation trước).

Self-review M3-B: **PASS** — chỉ đổi presentation/read-only queries; không có
fit/predict, network hoặc ghi artifact trong dashboard. SHA-256 labels và
profiles khớp trạng thái trước sửa. Git trước/sau: local `6a78a626`, remote
branch `m2-clustering-experiment` `6aadc1d0`, ahead 2 / behind 0; giữ nguyên
11 modified, 15 deleted và 6 untracked entries đã có. Không commit/push và
không xử lý các legacy deletions ngoài phạm vi.

## Cập nhật 2026-10-23 — Thiết kế lại giao diện M3-B theo ảnh owner

Giữ entry point `m3_dashboard.py`, bố cục bộ lọc trái / nội dung Market phải,
nền sáng và các panel bo góc. Bốn thẻ tổng quan lấy trực tiếp size/profile của
snapshot đang chọn. Biểu đồ scatter dùng `mom_252` và `mom_63` từ từng ticker,
màu theo assignments M2; giữ toàn bộ outliers, không tạo PCA/projection/model mới.
Các đám điểm không được ép giống tọa độ minh họa trong ảnh owner.

Tên hiển thị thay cho Cụm + số: **Dẫn đầu thanh khoản** là nhóm có liquidity_21
profile cao hơn; **Đại trà** là nhóm còn lại khi có nhiều thành viên hơn. Thiếu
hoặc bằng liquidity thì dùng Nhóm A/B; nếu nhóm còn lại không lớn hơn thì dùng
Thanh khoản thấp hơn. Quy tắc chỉ mô tả snapshot, không đổi label/membership,
không phải M3-A ranking hoặc khuyến nghị. Raw labels vẫn có trong provenance.
Audit cả 84 snapshot hiện hành xác nhận nhóm có liquidity cao hơn nhỏ hơn về size.

Bảng members có ticker, tên công ty, đủ 8 ticker features, tìm theo ticker/tên,
phân trang và chọn 10/25/50/100 rows. Company names đọc bằng unique security_id
từ `canonical/securities.jsonl`: 1.522 rows, checksum khớp C8 manifest; chỉ là tên
tham chiếu, không nâng historical identity/PIT. Null giữ MISSING. Số thực trong
bảng được định dạng để dễ đọc; Stock Detail giữ precision nguồn.

`.streamlit/config.toml` đặt light theme cho native controls/canvas; cần restart
Streamlit nếu đang chạy trước khi thêm theme. Không thêm dependency hoặc frontend
riêng. Lệnh chạy giữ nguyên: `.\.venv\Scripts\python.exe -m streamlit run .\m3_dashboard.py`.
Kiểm tra UI mới: đổi ngày, chọn từng tên nhóm, tìm FPT, đổi page size, chuyển trang
và so sánh feature/member count với nguồn. Bộ targeted mở rộng có 21 tests PASS;
giữ/migrate toàn bộ assertions cũ khi thay layout/column names, thêm kiểm tra tên
theo profile, raw scatter values, tìm kiếm và phân trang. Full-suite blocker
Financial ở ghi chú stage trước không thuộc thay đổi UI này.

Browser visual QA PASS ở desktop theo ảnh mẫu với light theme: snapshot
2025-12-31 có 1.410 mã, Dẫn đầu thanh khoản 26 và Đại trà 1.384. Thử chuyển nhóm,
next page (11–20 / 1.384, trang 2/139), tìm AAA (1/1) và reset search đều đúng.
Ảnh giao diện thật lưu local tại `tmp/m3_dashboard_redesign.jpg`; không phải mockup.

## Cập nhật 2026-10-23 — M3-B Market-only Streamlit

Entry point duy nhất: [`m3_dashboard.py`](../m3_dashboard.py), visualization
read-only trên `m2-final-handoff-v1`, manifest version 2.0.0. Tên thư mục không
đồng nghĩa bộ legacy 22 snapshot. Dashboard không sửa artifacts, gọi model,
tính lại features/clustering hoặc nâng historical identity/research readiness.
Bộ dữ liệu đến tháng 08/2026 là legacy và không được đọc trong M3-B hiện hành.

### Data contract

- Labels: 75.801 rows, gồm 45.646 development + 30.155 holdout.
- Profiles: 168 monthly + 6 summary rows. `MEDIAN_DEVELOPMENT_60M`,
  `MEDIAN_HOLDOUT_24M`, `MEDIAN_OVERALL_84M` được giữ trong source, không phải
  decision dates và không dùng thay monthly profile.
- Feature source: 179.880 rows / 120 snapshot, 2016-01-29–2025-12-31.
- Selector: đúng 84 manifest dates; 60 development 2019-01-31–2023-12-29 và
  24 holdout 2024-01-31–2025-12-31. Không tạo cluster cho 2016–2018 hoặc nội suy
  ngày/gap. Không áp systemic gap của bộ legacy lên bộ hiện hành.
- Join one-to-one: labels `(snapshot_date, security_id)` bằng features
  `(as_of_date, security_id)`. Không duplicate key, ticker ambiguity/mismatch.
  Cả 75.801 assignments có feature row và đủ 8 numeric finite values.
- Có 104.079 feature-only rows trên toàn file, gồm 50.115 ở các ngày M2. Source
  rộng hơn membership; không thêm các row này vào cluster universe. Audit trước
  implementation xác nhận không bỏ sót market-ready row tại 84 ngày M2.
- Labels khớp aligned assignments gốc, profiles khớp số liệu/member counts nguồn;
  ba handoff CSV cùng 84 model hashes/mirrors đã được kiểm tra. Feature hash
  `ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e` khớp
  C8/development/holdout hiện hành. Sai khác hash của bộ cũ đã được giải quyết.

Schema labels:
`snapshot_date, security_id, ticker, cluster_label, membership_period`.

Schema profiles:
`snapshot_date, cluster_label, size, size_ratio, membership_period, mom_21,
mom_63, mom_126, mom_252, vol_63, mdd_126, beta_126, liquidity_21`.

<details>
<summary>Exact schema 34 fields của feature JSONL</summary>

```text
adjustment_basis, as_of_date, available_at, beta_126, canonical_run_id,
data_mode, data_version, downside_vol_63, eligibility, feature_complete,
feature_version, historical_identity_ready, history_calendar_days,
history_observations, history_start_date, liquidity_21, listing_age_days,
lookback_observations, market_feature_ready, mdd_126, missing_count,
mom_126, mom_21, mom_252, mom_63, na_reason, ram_63, research_ready,
security_id, ticker, universe_segment, vendor_run_id, vol_126, vol_63
```

Dashboard chỉ chọn ngày, identity và 8 Market features; không triển khai logic
availability hoặc Financial từ các field khác đã có trong source JSONL.

</details>

### Chạy trên Windows

1. Mở PowerShell:

   ```powershell
   cd "C:\Users\HP\Downloads\Phân cụm động lượng TTCK"
   ```

2. Dùng Python >=3.11. Tạo virtualenv nếu chưa có, cài extra `dashboard` của
   project (Streamlit pin 1.66.1). Phiên implementation đã cài extra vào `.venv`:

   ```powershell
   if (!(Test-Path ".venv\Scripts\python.exe")) { python -m venv .venv }
   .\.venv\Scripts\python.exe -m pip install -e ".[dashboard]"
   .\.venv\Scripts\python.exe -m streamlit --version
   ```

3. Khởi chạy:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run .\m3_dashboard.py
   ```

4. Mở [http://localhost:8501](http://localhost:8501). Lần đầu cần đọc/xác minh
   source 234 MB. Đổi selectors dùng cache in-memory. **Đọc lại dữ liệu** xóa
   cache dashboard và reset date/ticker. Cache tự invalidate theo size/mtime/ctime
   source hoặc code; loader offline không cache. Đọc khi source đang đổi sẽ bị chặn.
5. Dừng bằng **Ctrl+C** ở PowerShell.

Nếu lỗi môi trường, kiểm tra `Get-Location`, `Test-Path .\m3_dashboard.py`,
`.\.venv\Scripts\python.exe --version` và Streamlit version trước khi sửa code.
Không thay methodology để xử lý environment error.

### Checklist kiểm tra thủ công

- **Overview:** chọn `2019-01-31`. Dẫn đầu thanh khoản (source label 0): 12 members,
  size_ratio `0.0182926829268292`; Đại trà (source label 1): 644 members,
  size_ratio `0.9817073170731708`.
  Mở hai member lists. Bảng 8 features phải có nhãn **CLUSTER PROFILE**.
- **Holdout:** đổi sang `2025-12-31`. Dẫn đầu thanh khoản: 26 members; Đại trà: 1.384;
  tổng 1.410. Selector chỉ có 84 ngày M2, không có năm 2026.
- **Stock Detail/date change:** chọn FPT, `2025-12-31`: security_id
  `KBS:HOSE:FPT`, Dẫn đầu thanh khoản (source label 0), giai đoạn `holdout`, đủ 8 features.
  Đổi sang `2019-01-31`: FPT thuộc Đại trà (source label 1), features đổi theo snapshot.
- **Missing/error:** không sửa source thật để thử lỗi. Tests bên dưới dùng
  fixture tạm cho unknown ticker/date, missing cluster/feature row, null,
  malformed session state và tamper. UI hiện trạng thái rõ, không crash/zero-fill.
- **Provenance/reset:** mở Data source / snapshot / version để xem nguồn,
  version, audit counts; thử nút Đọc lại dữ liệu.
- **Source comparison:** từ repository root chạy:

  ```powershell
  Import-Csv ".\M2\artifacts\m2-final-handoff-v1\m2_cluster_labels_for_m3.csv" |
      Where-Object { $_.ticker -eq "FPT" -and $_.snapshot_date -eq "2025-12-31" }

  Get-Content ".\artifacts\cafef_primary\cafef-c8-complete-only-v2\canonical\feature_snapshots.jsonl" |
      Select-Object -Skip 50519 -First 1 |
      ConvertFrom-Json |
      Select-Object as_of_date, security_id, ticker, mom_21, mom_63, mom_126, mom_252, vol_63, mdd_126, beta_126, liquidity_21
  ```

  Labels row ở dòng 74801 (tính cả header), feature row ở dòng 50520 của source
  hiện hành. Kiểm tra ngày/identity của row vừa mở trước khi so sánh:

  | Feature | FPT, 2025-12-31 |
  |---|---:|
  | mom_21 | -0.008281367081487079 |
  | mom_63 | 0.03637059556397837 |
  | mom_126 | -0.09133035242078935 |
  | mom_252 | -0.25055833135062255 |
  | vol_63 | 0.31045166899069365 |
  | mdd_126 | -0.2239070145700931 |
  | beta_126 | 0.5259396975653587 |
  | liquidity_21 | 564969927952.381 |

### Kiểm thử M3-B và giới hạn

18 targeted tests PASS, gồm AppTest với dữ liệu thật/fixture: import/load,
schema/hash/lineage, uniqueness/many-to-many, official selector, Overview
development/holdout, ticker feature equality, missing/malformed states, cache
invalidation và reset. Server Streamlit startup PASS ở port thử 8517:
`HTTP 200 /_stcore/health = ok`; đã dừng sau kiểm tra. Không có browser visual QA;
dùng checklist trên để demo trên trình duyệt thật.

Full repository gate chạy 268 tests: 262 PASS, 6 errors ở Financial continuation.
Năm errors do thiếu thư mục tạm `.tmp`; sau tạo thư mục môi trường và rerun nhóm
11 tests, 10 PASS và còn một error do thiếu immutable evidence
`artifacts/financial_pit/fin-pit-1a-20261004T015420Z-continuation-preflight-v2/next_network_proposal.json`.
Vì vậy full gate chưa PASS; không sửa/xóa assertion hoặc dựng evidence thay thế.
Lỗi này nằm ngoài đường đọc M3-B. Log full run: `tmp/m3_full_suite.log` (local,
ignored). Compile, TOML/JSON parse và Markdown links mới PASS. Diff check trên
files của task PASS; global diff còn CRLF/trailing whitespace trong handoff và
báo cáo đã được owner cập nhật trước task, giữ nguyên byte/hash của các file đó.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_m3_dashboard.py" -v
.\.venv\Scripts\python.exe -m compileall -q src tests scripts run.py m3_dashboard.py
```

Sandbox của phiên này chặn Windows asyncio/socketpair loopback; AppTest/server
PASS ngoài sandbox. Đây là environment limitation, không đổi code/methodology.
Handoff chưa pin trực tiếp feature path/hash; dashboard verify qua manifests
C8/development/holdout. Model là reference only, dashboard không load model files.
Transition Screen và kiến trúc backend/frontend riêng không thuộc stage này.

**FINANCIAL NOT IMPLEMENTED YET.** Dừng ở M3-B Market-only; next step là owner
chạy manual checklist, không tự mở Financial/M3-A/backtest.

## Hiện tại 2026-10-22 — Nhiệm vụ 11 hoàn tất trên dữ liệu mới, báo cáo đầy đủ

Người dùng đã chạy xong notebook `11_final_holdout_execution.ipynb`. Bộ
`M2/artifacts/m2-final-holdout/` ghi complete: 24/24 tháng 2024–2025, không
skip, 30.155 assignments, 48 profiles, 24 model và 23 cặp thời gian nội bộ.
Chỉ KMeans Baseline/sklearn/K=2; quyết định đóng băng lúc 12:57:06, mở holdout
15:49:06 và hoàn tất 15:50:31 ngày 22/10/2026 (UTC+7).

Nguồn C8 feature SHA-256
`ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`
khớp lineage Task 10. Median Silhouette holdout 0,949324 so với development
0,940837 (delta +0,008487); ARI median 0,843260, Persistence 99,370574%,
Migration 0,629426%. Giữ cảnh báo 24/24 tháng Balance <0,05, cụm nhỏ 22–41 mã;
khoảng cách tâm cụm chủ yếu theo thanh khoản, không suy hiệu quả đầu tư.

[Báo cáo Nhiệm vụ 11](../M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md)
được mở rộng theo mẫu A/B/C với bảng 24 tháng, so sánh Dev/Holdout, biểu đồ
84 mốc, temporal/universe, hồ sơ mean/median và giới hạn diễn giải. Bản xuất
tự động gốc giữ tại `report_auto.md` trong artifact để đối chiếu provenance.
Chỉ cập nhật report/checksum và metadata revision; model, numerical outputs,
input, code và timestamps thực nghiệm giữ nguyên. Rerun bộ complete chỉ verify
và nạp artifacts, không refit. Nhiệm vụ 12/M3 chưa thực hiện trong lần này;
audit/generator 12–13 lịch sử cần context riêng. Các mục dưới đây là lịch sử.

## Lịch sử 2026-10-22 — Chuẩn bị nhiệm vụ 11 trên dữ liệu mới, chưa chạy holdout

Người dùng yêu cầu hướng dẫn chạy nhiệm vụ 11 sau khi đồng bộ Git và giải nén
lại dữ liệu mới. Tạo notebook `11_final_holdout_execution.ipynb`, config
`m2_final_holdout.json`, module `final_holdout.py` và các kiểm thử bằng fixture.
Không khôi phục số liệu/model/outputs holdout cũ, không tạo tên có hậu tố.

Quyết định Task 10 hiện hành: FROZEN_FOR_HOLDOUT, KMeans Baseline/sklearn/K=2,
timestamp `2026-10-22T05:57:06+00:00`, nguồn C8 feature SHA-256
`ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`.
Config mới chỉ được tạo khi chưa có đầu ra; pin đúng chín development inputs
hiện tại, không tái gán hash cho bất kỳ evidence holdout cũ nào. Chín hash khớp
Git bytes. Preflight kiểm chứng 60 model và 70 input refs mà không đọc feature
holdout. Giữ nguyên 60 tháng development / 24 tháng holdout, threshold 100,
seed 42/n_init 10/max_iter 300, Robust Scaling per snapshot, không retune.

Người dùng chạy Bước 2 trong notebook để thực thi holdout thật. Các bước 3–7
hiển thị và kiểm chứng outputs; không fit thêm. Bộ complete chỉ được verify
khi chạy lại; run dở hoặc checksum đổi bị chặn. Kết quả sẽ nằm ở
`M2/artifacts/m2-final-holdout/`, models `M2/models/holdout/`, báo cáo
`M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`. Hiện chưa có các đầu ra đó.
Audit 12 và generator bàn giao 13 lịch sử vẫn phải dùng context riêng, không
tự động tiếp tục sau nhiệm vụ 11. Các mục trước bên dưới là lịch sử.


## Hiện tại 2026-10-22 — Tên chuẩn PCA + K-Means và xóa toàn bộ nhiệm vụ 11

Theo yêu cầu mới nhất, giữ bộ PCA + K-Means 6–9 đã khôi phục từ Git và đổi tên
không có hậu tố phiên bản: notebook `06_pca_kmeans.ipynb`, các notebook 07–09
`*_pca_kmeans.ipynb`, config `m2_pca_market_only.json`, artifacts
`m2-task6-pca-kmeans/`, freeze `m2-task6-pca-freeze/`, đánh giá
`m2-evaluation-pca-kmeans/`, bốn báo cáo `*PCA_KMeans.md`. Models vẫn ở
`M2/models/pca_kmeans/`. Kế hoạch và notebook 10 dùng các đường dẫn này.

Đã cập nhật metadata đường dẫn và checksum theo thứ tự phụ thuộc; sửa ba hash
báo cáo 7–9 không khớp manifest đã phát hiện ở lần kiểm tra trước. Manifest nhiệm
vụ 6 ghi `storage_migration` và hash manifest trước đổi tên. Các file khoa học và source snapshot PCA giữ nguyên bytes; toàn bộ payload số của 120 bản model PCA
(60 bản trong artifacts và 60 bản mirror) giữ nguyên. Không fit lại hoặc dùng
holdout. Bộ PCA vẫn complete, 60 tháng, 45.646 assignments, K=2, PCA 2 chiều.

Yêu cầu xóa nhiệm vụ 11 đến sau yêu cầu đổi tên/thay thế: đã xóa toàn bộ bản cũ,
bản mới và các file trung gian vừa chuyển tên của Task 11, bao gồm notebook,
config, implementation/helpers, kiểm thử riêng, artifacts/model/report. Không
backup. Task 12/13 giữ lại như lịch sử; script dừng trước mutation do thiếu
đầu vào Task 11. Nguồn C8 mới và kết quả riêng K-Means/Ward/Task 10 giữ nguyên.

Các mục bên dưới là ghi chú tại thời điểm trước, không thay đổi yêu cầu hiện tại.
Phạm vi đồng bộ GitHub: đổi tên PCA 6–9, sửa checksum báo cáo và xóa Task 11 theo yêu cầu owner.


## Cập nhật 2026-10-22 — Nhiệm vụ 11 V2 hoàn tất và có báo cáo đầy đủ

Holdout thật đã chạy xong: KMeans Baseline/sklearn/K=2 trên 24/24 tháng
2024–2025, không skip; 28.110 assignments, 48 profiles, 24 model và 23 cặp
tháng nội bộ. Manifest `m2-final-holdout` ghi `complete`; freeze timestamp
đứng trước lúc mở holdout. Không chạy Ward/PCA hoặc retune bằng kết quả ngoài mẫu.

Median Silhouette 0,945927 so với development 0,931935 (delta +0,013992);
ARI median 0,849616, Persistence 99,358974%, Migration 0,641026%. Vẫn giữ
cảnh báo 24/24 tháng Balance <0,05, cụm nhỏ 22–41 mã; không suy hiệu quả đầu tư.

Báo cáo Nhiệm vụ 11 V2 (`../M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`, đã xóa nhiệm vụ 11)
đã được viết đầy đủ theo bố cục A/B/C của mẫu cũ, kèm bảng, biểu đồ 84 mốc và
biện luận từ số liệu thực tế. Bản tự động gốc được giữ tại `report_auto.md`
trong artifact; chỉ cập nhật report/checksum và metadata ghi nhận sửa báo cáo.
Numerical artifacts, model, input, source code và quyết định Task 10 không đổi.
Rerun xác minh/nạp lại bộ complete, không refit; Task 12/M3 chưa thực hiện ở đây.

## Cập nhật 2026-10-22 — Nhiệm vụ 11 V2 đã chuẩn bị, chưa mở holdout thật

Đã chuẩn bị `11_final_holdout_execution.ipynb`, config
`m2_final_holdout.json` và runner `experiments/final_holdout.py` theo kế hoạch:
60 development/24 holdout 2024–2025, universe tối thiểu 100 mã theo tháng,
chỉ KMeans Baseline/sklearn/K=2 từ quyết định Task 10 V2, giữ seed=42,
n_init=10, max_iter=300, Robust Scaling độc lập; không chạy comparator/quét K.

Gate đã kiểm chứng 60 model và development inputs; chưa đọc feature holdout.
Đã khôi phục đúng LF của selected-model exports để khớp byte hash đã freeze,
thêm Git attributes bảo toàn định dạng và pin development inputs theo Git bytes.
JSON/CSV values và quyết định Task 10 không đổi. Bộ legacy V1 và source runner
legacy giữ nguyên. Đầu ra V2, model `holdout` và báo cáo V2 chưa được tạo.

Notebook trình bày đúng bảy bước. Bước 2 do người dùng thực hiện mới mở holdout;
run complete được verify-only khi chạy lại. Run dở/failed hoặc checksum đổi
phải dừng và giữ evidence. Test dùng fixture giả riêng, không fit dữ liệu thật.

## Cập nhật 2026-10-22 — Báo cáo PCA V2 đầy đủ và đồng bộ Git

Theo yêu cầu owner, bốn báo cáo chính Nhiệm vụ 6–9 PCA + K-Means tên hậu tố
`_v2.md` trong `M2/reports/` đã được thay bằng bản đầy đủ có bố cục A/B/C,
bảng chi tiết và biểu đồ. Không giữ bản trùng `_v2_day_du.md` trong active tree;
các bản trước vẫn có trong Git history. Đường dẫn tại [START HERE](README.md).

Checksum báo cáo trong manifest Task 6–9 cùng tham chiếu metadata phụ thuộc
được cập nhật. Model, scaler/PCA, CSV/JSONL, biểu đồ, source snapshot và toàn bộ
kết quả/quyết định Task 10 giữ nguyên. Notebook đánh giá 7–9 kiểm tra checksum
báo cáo đầy đủ trước khi tái sử dụng, không ghi đè bằng phần tóm tắt tự động.

Đã lấy hai commit `2d8ac27` và `3caf7c9` từ Git: KMeans 4/7/8/9 đã làm lại và
Task 10 V2 đã chọn **KMeans_Baseline, K=2**, trạng thái `FROZEN_FOR_HOLDOUT`;
PCA và Ward là comparator. Các báo cáo mới phản ánh trạng thái này, không
thực thi lại Task 10 hoặc mở holdout V2. Các ghi chú cũ bên dưới giữ bối cảnh
tại thời điểm được viết.

## Cập nhật 2026-10-21 — nhánh K-Means M2 trên C8 v2

Nhiệm vụ 4, 7, 8 và 9 của **K-Means** đã chạy lại trên 60 development snapshot 2019–2023 từ `cafef-c8-complete-only-v2`; Global K=2 giữ theo quyết định Nhiệm vụ 3. Nhiệm vụ 4 fit lại bằng scikit-learn, có 29.907 assignments, 120 profiles, 60 model/scaler. Output active đúng tên kế hoạch ở `M2/artifacts/m2-task4-kmeans-baseline-v1/` và `M2/models/kmeans/`.

Nhiệm vụ 7 xuất `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv` từ 60 diagnostics; median Silhouette 0,931935, Davies-Bouldin 0,396416, balance 0,023814. Nhiệm vụ 9 đọc 59 cặp tháng, xuất 236 transitions và 944 feature drift rows; median ARI 0,768741, NMI 0,624996, persistence 98,9313%, migration 1,0687%. Bốn báo cáo đúng tên trong `M2/reports/`; đã đối chiếu offline schema, checksum, metrics và biểu đồ. Các chỉ số này chỉ phản ánh cluster quality và temporal stability, không phải portfolio performance.

Nhiệm vụ 8 K-Means hiển thị 3 bảng (4×10, 9×4, 60×5) trong notebook và xuất radar, heatmap, báo cáo từ 60 snapshot mới; đã đối chiếu offline bảng với nguồn và scaler. Artifact K-Means dùng tiếp gồm `cluster_profiles.csv` 120 dòng, `cluster_profile_members.csv` 29.907 dòng và `profile_scaler_reference.csv` 960 dòng ở `M2/artifacts/m2-evaluation-kmeans/`, được đồng bộ từ Task 4. Manifest Task 4 có hash nguồn C8; 18 file giải nén khớp ZIP trong Downloads. ZIP không gồm hai output lớn mà C8 manifest liệt kê (`canonical/normalized_expansion.jsonl`, `canonical/prices_daily.jsonl`); K-Means dùng feature snapshots có hash hợp lệ. Không sửa Nhiệm vụ 1–3 hoặc nhánh Ward/PCA. So sánh ba model/holdout không thuộc lần chạy này.

Gate: targeted clustering/runner/protocol 29 tests PASS, synthetic smoke PASS, compile PASS và offline checks K-Means Task 4/7/8/9 PASS. Full repository suite chạy 234 tests, còn 5 errors ở holdout/ingestion evidence ngoài nhánh K-Means; không sửa các nhánh đó trong lần chạy này.


## Cập nhật 2026-10-21 — PCA V2 thay bộ cũ trong active Git tree

Nhiệm vụ 6–9 PCA + K-Means với dữ liệu mới đã hoàn tất: 60 tháng development
2019-01-31–2023-12-29, 29.907 assignments, Global K=2 và PCA 2 chiều. Các mục
ngày trước bên dưới là lịch sử, không phải kết quả tái xác nhận cho bộ V2.

- Notebook active: `06_pca_kmeans.ipynb`,
  `07_cluster_quality_evaluation_pca_kmeans.ipynb`,
  `08_cluster_profiling_pca_kmeans.ipynb`,
  `09_temporal_stability_pca_kmeans.ipynb` trong `M2/notebooks/`.
- Artifact: `M2/artifacts/m2-task6-pca-freeze/`,
  `M2/artifacts/m2-task6-pca-kmeans/`,
  `M2/artifacts/m2-evaluation-pca-kmeans/`; 60 model mới trong
  `M2/models/pca_kmeans/`, config `configs/experiments/m2_pca_market_only.json`.
- Theo yêu cầu owner, xóa bộ PCA cũ 15 tháng khỏi active tree: bốn notebook
  không có hậu tố V2, config `m2_task6_pca.json`, artifact
  `m2-task6-pca-kmeans-v1` và `m2-evaluation-pca-kmeans`. Git history là archive.
  Backend PCA/K-Means và các phương án khác vẫn được giữ.
- Task 9 đã chạy chính thức: manifest `complete`, đủ 59 cặp tháng, ba CSV
  59×10/236×6/944×7, hai biểu đồ và báo cáo V2. Median ARI 0,743427,
  NMI 0,592307, persistence 98,827471%, migration 1,172529%.

Task 10 mới chỉ được chuẩn bị đường dẫn V2 và guard cùng nguồn/cùng 60 tháng;
chưa chạy lại hoặc quyết định phương án thắng. Task 10–13 lịch sử và runner
`final_holdout.py` giữ nguyên context cũ; không xem kết quả đó là holdout/handoff
cho V2. Audit Task 12 lịch sử cần checkout cũ có đầy đủ bằng chứng PCA cũ.
Giữ code backend được source snapshot/holdout manifest tham chiếu để bảo toàn
khả năng kiểm chứng bằng chứng lịch sử; config V2 chỉ định output mới tường minh.

## Cập nhật 2026-10-21 — Nhiệm vụ 7 PCA + K-Means trên bộ dữ liệu V2

Đã thực thi đánh giá chất lượng từ diagnostics của Nhiệm vụ 6 V2: đúng 60 tháng
development 2019-01-31–2023-12-29, Global K=2, PCA 2 chiều. Nhiệm vụ 7 chỉ đọc
diagnostics và metadata kiểm tra nguồn; không fit model, không mở holdout.

- Notebook đã chạy đủ hai bảng và năm biểu đồ:
  [07_cluster_quality_evaluation_pca_kmeans.ipynb](../M2/notebooks/07_cluster_quality_evaluation_pca_kmeans.ipynb).
- Bộ mới nằm trong M2/artifacts/m2-evaluation-pca-kmeans/; chỉ có một CSV
  quality_summary.csv đúng 5 dòng × 7 cột, mọi n_total/n_available bằng 60,
  kèm năm PNG và manifest checksum. Bộ đánh giá cũ 15 tháng đã được đưa về Git history.
- Median Silhouette 0,939741; DB 0,383600; CH 1177,053847; Inertia 81023,955397;
  Balance 0,023814. Có 50/60 tháng Balance < 0,05, toàn bộ 60 tháng đạt rubric
  phân cụm bất đối xứng; ba singleton tại 2021-10-29, 2022-01-28, 2022-02-28.
- [Báo cáo Nhiệm vụ 7 V2](../M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_PCA_KMeans.md)
  trình bày phán quyết A/B/C và giới hạn suy luận. Silhouette cao không chứng minh
  hai chế độ cân bằng, nguyên nhân dòng tiền hoặc hiệu quả đầu tư.

Đã kiểm tra thực thi notebook, schema, thống kê, biểu đồ và checksum; toàn bộ
artifact/model Nhiệm vụ 6 V2 và bộ legacy được bảo toàn. Bàn giao quality metrics
cho Nhiệm vụ 10 với điều kiện các phương án dùng cùng dữ liệu/cửa sổ development.
Chưa thực hiện Nhiệm vụ 8–10 V2 trong phiên đánh giá này.

### Nhiệm vụ 8 PCA + K-Means V2 đã được người dùng chạy

Đã chuẩn bị [08_cluster_profiling_pca_kmeans.ipynb](../M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb)
để người dùng tự chạy trên 120 hồ sơ/60 tháng của Nhiệm vụ 6 V2. Đã kiểm tra
ba bảng đúng kích thước 4×10, 9×4, 60×5; dùng scaler đã lưu của đúng tháng,
Radar/Heatmap và dropdown 60 tháng. Chỉ giới hạn hiển thị Z ở ±3, giữ Z thật
trong bảng/Heatmap và bằng chứng; không fit lại hoặc đọc holdout.

Người dùng đã chạy notebook: task8_manifest.json ghi complete, đủ 60 tháng/120
hồ sơ, Primary Driver là liquidity_21, chênh lệch Mean Robust Z C0−C1 = 240,887454.
Hai PNG, bằng chứng và báo cáo Nhiệm vụ 8 tên hậu tố v2 đã được kiểm tra checksum.
Kết quả ở M2/artifacts/m2-evaluation-pca-kmeans/; manifest và CSV Nhiệm vụ 7
được bảo toàn. Các kết luận vẫn giữ nhãn trung tính, không suy chi phí thực thi từ
thanh khoản trung bình hoặc coi cụm thanh khoản thấp hơn là dưới market median.

### Nhiệm vụ 9 PCA + K-Means V2 đã hoàn tất

Đã chuẩn bị [09_temporal_stability_pca_kmeans.ipynb](../M2/notebooks/09_temporal_stability_pca_kmeans.ipynb)
đã được người dùng chạy. Bước đầu chuẩn hóa artifact Task 6 đã có sang ba CSV phẳng
đúng 59×10, 236×6, 944×7; ARI/NMI giữ nguyên, transition dùng nhãn aligned xuyên
chuỗi, drift có hai đầu tâm cụm gốc thật và được đối chiếu mapping đã lưu.
Phần đánh giá đọc ba CSV để tạo bốn bảng và hai biểu đồ; không fit hoặc mở holdout.

Đã kiểm tra toàn luồng và rerun trong thư mục tạm, cùng checksum và bảng số liệu;
đã có CSV/ảnh/báo cáo Task 9 chính thức với manifest `complete`. Đích là
M2/artifacts/m2-evaluation-pca-kmeans/ và báo cáo Nhiệm vụ 9 hậu tố v2.
Notebook 7 chỉ kiểm tra CSV thuộc Task 7, cho phép ba CSV Task 9 dùng chung thư mục;
không thay số liệu hoặc manifest của Task 7/8.

Khi bàn giao Task 10 cần thống nhất mẫu số tỷ lệ Entry/Exit giữa các phương án:
bản PCA V2 dùng (Entry+Exit)/n_common; các notebook legacy có công thức khác.
Không đồng nhất tỷ lệ membership này hoặc migration với turnover/chi phí danh mục.

## Cập nhật 2026-10-04 — nhiệm vụ 11 Final Holdout đã thực thi

Người dùng yêu cầu thực hiện nhiệm vụ 11 sau khi tự chạy Task 10. Quyết định active
freeze `KMeans_Baseline`, K=2 lúc `2026-10-04T08:01:06+00:00`; holdout mở lúc
`2026-10-04T08:14:18.565783+00:00` sau kiểm tra gate/model hashes. C8 và Task 10
giữ nguyên. Đây là single winning method, monthly independent fitting/scaling;
không chạy comparators hoặc quét K.

- 7/7 holdout snapshots; universe 253–905 mã mỗi tháng; 4.624 assignments, 14 profiles,
  7 fitted models, 6 cặp temporal, 24 transitions và 96 feature drift rows; không skip.
- Median Silhouette 0,952683 so với Development 0,755722; Delta +0,196961.
  DB 0,431560; ARI 0,895529; NMI 0,791375; Persistence 99,5835%; Migration 0,4165%.
- Balance median 0,021445, cụm nhỏ 10–19 mã. Phân rã bình phương khoảng cách hai
  centroid cho thấy liquidity median đóng góp 99,9980%; Silhouette cao cần đọc
  cùng cảnh báo mất cân bằng/phân tách thanh khoản, không suy hiệu quả đầu tư.
- Gap reset giữ đúng; không nối 2025-01-24 với 2026-02-27 và không nối qua skip.

Mở `M2/notebooks/11_final_holdout_execution.ipynb`, chọn kernel Python M2 rồi Run All;
root tự tìm từ repo hoặc thư mục notebook. Core ở `src/delta_t1/experiments/final_holdout.py`,
config `configs/experiments/m2_final_holdout_v1.json`; output `M2/artifacts/m2-final-holdout-v1/`,
model `M2/models/holdout/`, report `M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`.
Rerun chỉ kiểm tra checksum/nạp evidence, không fit lại. Không sửa decision/input
sau khi đã mở holdout. 11 targeted tests đã qua, gồm frozen gate, tamper, late data,
skip/reset, label permutation, kiểm chứng scaler/nhãn/profile từ C8 và verify-only rerun.
Synthetic smoke/compile đã qua. Stage tiếp theo là Task 12; chưa thực hiện Task 12/M3.

## Cập nhật 2026-10-04 — chuẩn hóa lại PCA notebooks nhiệm vụ 6–9 về v1

Bốn notebook `06_pca_kmeans`, `07_cluster_quality_evaluation_pca_kmeans`,
`08_cluster_profiling_pca_kmeans`, `09_temporal_stability_pca_kmeans` đã chạy trên
development và lưu output. Theo yêu cầu mới của người dùng, bộ sửa lỗi trước đó
mang tên v2 đã thay thế bộ v1 cũ và dùng các đường dẫn chuẩn:
`M2/artifacts/m2-task6-pca-kmeans-v1/`, `M2/artifacts/m2-evaluation-pca-kmeans/`
và `M2/models/pca_kmeans/`. Chạy 06 → 07 → 08 → 09 từ repo root hoặc thư mục
notebook. Notebook 06 kiểm chứng trực tiếp bộ hiện hành, không phụ thuộc file cũ.
Manifest giữ lineage gốc và ghi rõ migration theo ADR-051; không đổi model/số liệu.

Giữ 15 snapshot, 5.615 assignments, Global K=2 và fixed PCA=4; toàn bộ model/scaler
được tái dùng và kiểm chứng, không refit. Explained variance median 96,8639%, min
93,6424%. ARI median 0,798251, NMI 0,661313, Persistence 98,5618%, Migration
1,4382%. Transition probabilities dùng cùng aligned IDs: C0 giữ 80,9045% trên
199 lượt, C1 giữ 99,3053% trên 4.606 lượt; tỷ lệ tổng hợp che bớt khác biệt giữa cụm.
Drift giữ tọa độ gốc thật, không có placeholder `value_from=0`.

Không mở nhiệm vụ 10/final holdout/backtest. Kiểm chứng số chiều trên development
không tạo bằng chứng preregistration trước run v1; giới hạn này được giữ ở ADR-050.

Notebook/code/output nhiệm vụ 10 không bị sửa hoặc chạy lại trong migration này.
Các đường dẫn PCA mà notebook 10 đang đọc nay chứa bộ kết quả đã sửa; kết quả
Task 10 lưu từ lần chạy trước vẫn là kết quả lịch sử, cần người dùng tự chạy lại.
Bản sao khôi phục trước replacement ở `tmp/pca_notebook_repair/pca_before_replacement.zip`
đã kiểm tra checksum, nằm ngoài artifacts active và được Git ignore.

Kiểm tra sau replacement: bốn notebook chạy thành công, 19 targeted tests qua;
51 file số liệu/model/biểu đồ giữ nguyên từng byte so với bộ sửa v2, chỉ config và
manifest đổi metadata/đường dẫn. Toàn bộ 24 file Task 10 được đối chiếu vẫn nguyên
checksum. Các thư mục v2, file legacy và report Task 6 tên cũ đã được loại khỏi active tree.

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
[Report quá trình — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip).

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
[Report v2 — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-remediation-v2/report.md) và
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
Config `configs/data/financial_pilot_closure_v1.json`; [report hiện hành — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-pilot-closure-v1/report.md).
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
PASS. [Execution report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-execution-v1/report.md),
config `configs/data/financial_execution_plan_v1.json`; features false, PIT NOT_READY.
Next financial stage: nghiệm thu FPT notes/mappings và publication history, sau
đó xử lý ba mã pilot còn lại, full VAS VNM và quarter/TTM trước expansion.

**M2-R1 — PROTOCOL FREEZE v1**: tạo `configs/experiments/m2_market_only_v1.json`, ADR/decision artifact, validation và tests cho toàn bộ quyết định Protocol v1 đã được owner review. Không chạy real clustering, không mở holdout, không sửa market-only runner/input adapter và không mutate C8/M1/M2-PREP evidence. Sau khi M2-R1 PASS, exact next stage là **M2-R2 — MARKET-ONLY RUNNER ADAPTER**.

### Financial FIN-D2 continuation — 03/10/2026

Handoff hiện hành: [workflow runbook](crawl/README.md),
[report — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip).
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

[Report hiện hành — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-date-pit-v1/report.md) thay handoff
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

[Report — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip): chạy code từ
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

## M2 Nhiệm vụ 1 — protocol freeze

Owner đã phê duyệt và khóa protocol market-only v1 trong
`configs/experiments/m2_market_only_v1.json`: 15 development snapshots
`2023-11-30..2025-01-24`, 7 holdout snapshots niêm phong
`2026-02-27..2026-08-28`, minimum eligibility 120, 8 market features,
fail-closed missing, no clipping/winsorization, Robust Scaling theo từng snapshot
và `k_range=2..8`. Global K chỉ được chọn trên development bằng
cluster-quality metrics; `portfolio_evaluation.enabled=false`. PCA chỉ là
comparator độc lập, không phải preprocessing chung. Chưa fit model,
không mở holdout, không backtest và không thay data/evidence.

Acceptance gate sau khi phục hồi đúng immutable C5 local artifact: C5 manifest
SHA-256 `869512c66fceee02f9b5801af3c24724309b508013a607158085dd7e9b50d256`,
20/20 C5 output hashes khớp và full repository suite 173/173 tests pass.
Ba file recovery WIP untracked ngoài active R1 tree được giữ nguyên trong
`tmp/full_recovery_wip_20260926/`; không phục hồi recovery stack superseded.

## M2 Nhiệm vụ 2 — runner preparation/testing

Runner market-only đã có adapter xác minh checksum và đọc trực tiếp
`canonical/feature_snapshots.jsonl` của C8 mà không đi qua strict historical-identity
gate dành cho M3. Adapter chỉ tạo alias in-memory
`market_feature_ready_v2 = market_feature_ready` cho C8 v2, không mutate artifact;
legacy `eligibility` không được dùng thay thế.

Snapshot `2023-11-30` tái lập đúng 142 securities eligible. Runner kiểm tra
đúng 8 feature là numeric finite, skip khi `n_eligible < 120`, và output được
common `build_snapshot` interface chấp nhận. Terminal-universe guard dùng snapshot
membership độc lập, không retrospective-filter. Nhiệm vụ này không chạy
Global K, không mở holdout và không backtest.

## M2 Nhiệm vụ 3 — Global K selection (Completed & Approved)

Đã chạy hoàn tất 105 lượt K-Means (15 development snapshots nhân 7 cấu hình `k=2..8`).
105/105 lượt chạy hội tụ và tính đủ 5 metrics.
Cấu hình K = 2 đạt median Silhouette cao nhất (0.7557), median Davies-Bouldin thấp nhất (0.5219)
và Calinski-Harabasz cao nhất (316.39). Nhóm đã phê duyệt chính thức Global K = 2 (ADR-049),
khóa `k: 2` vào `configs/experiments/m2_market_only_v1.json`.
Hiện tượng cụm nhỏ (8-21 mã) siêu thanh khoản được ghi nhận và phân tích đầy đủ.

## Stage tiếp theo

## FIN-PIT-2 — document linkage và semantic extraction

FIN-PIT-2 đã chạy offline trên immutable FIN-PIT-1 artifact với gate `PARTIAL`.
Stage xử lý 32 document unique-content và 40 linkage candidates, nhận diện 4 primary
financial reports và 2 supporting explanatory documents. Ba báo cáo năm 2022 của
PVS có text layer đủ evidence đạt `SEMANTIC_READY`; 29 report candidates còn lại bị
quarantine do scan/semantic chưa đủ và không có OCR engine trong environment.

Kết quả candidate gồm 220 facts (216 balance-sheet instant semantic-ready, 4
unresolved), 220 taxonomy candidates chưa final-promote, 6 linkage `VERIFIED`, 34
`AMBIGUOUS`, 0 conflict. Cả 7 revision groups vẫn giữ `revision_relation=UNKNOWN`.
Timing được preserve ở cấp report candidate: 4 `A_EXACT_TIMESTAMP`, 28
`B_OFFICIAL_DATE_D1`; không tạo timestamp giả. Artifact nằm tại
`artifacts/financial_pit/fin-pit-2-semantic-extraction-v1/`.

FIN-PIT-2 không ghi canonical financial row, không bật financial feature và không
tự mở FIN-PIT-3. Phần scan cần một OCR run riêng có engine/version/page/confidence
provenance trước khi có thể nâng coverage.

## FIN-PIT-2-R1 — OCR remediation

FIN-PIT-2-R1 đã chạy offline bằng Tesseract OCR `v5.4.0.20240606` trên đúng 26
tài liệu scan/mixed chưa phân loại chắc chắn. Preflight review 32 tài liệu, chọn 209
trang; 205 trang đạt OCR quality gate và 4 trang `LOW_CONFIDENCE` bị loại khỏi
semantic evidence. Raw PDF và timing handoff không đổi.

Gate là `PARTIAL`. OCR tăng document classified từ 6 lên 32, linkage `VERIFIED`
từ 6 lên 27 và giảm `AMBIGUOUS` từ 34 xuống 4. Đồng thời evidence mới phát hiện 9
`CONFLICT` scope giữa disclosure candidate và nội dung attachment; các conflict này
được giữ fail-closed. Quarantine giảm 29 xuống 26, semantic-ready reports tăng 3 lên
6, fact candidates tăng 220 lên 242 nhưng semantic-ready facts giữ 216. Unit verified
tăng 9 lên 30; scope verified tăng 6 lên 29; assurance verified tăng 3 lên 8.

Q2/Q3 duration vẫn chưa đủ evidence để promote: 0 `STANDALONE`, 0 `YTD`, 26 facts
duration `UNKNOWN`. Cả 7 revision groups tiếp tục `UNKNOWN`; timing vẫn 4
`A_EXACT_TIMESTAMP` và 28 `B_OFFICIAL_DATE_D1`. Artifact nằm tại
`artifacts/financial_pit/fin-pit-2-r1-ocr-remediation-v1/`. Stage không ghi canonical
row, không bật financial feature và không tự mở FIN-PIT-3; nếu mở stage sau chỉ được
review một verified subset được freeze rõ.

**M2 Nhiệm vụ 4 — CHẠY PHƯƠNG ÁN A: K-MEANS BASELINE**: Đóng gói và hoàn thiện
kết quả K-Means chính thức với Global K = 2 trên 15 development snapshots, chuẩn bị cho
Nhiệm vụ 5 (Ward) và Nhiệm vụ 6 (PCA + K-Means). Không mở holdout và không backtest.



### Portable financial replay — 24/10/2026

Kiểm thử Git export phát hiện nhiều financial source pins cũ còn phụ thuộc LF/CRLF.
Đã thêm frozen-source-v2 giữ exact bytes toàn bộ16trackedsource/config/scriptpins từ
checkpoint819cd82, không bỏ bất kỳ hashcheck nào. Overlay chỉ áp src/scripts/configs;
raw/data pins vẫn kiểm tại path gốc. Review outputv2 giữ bảnv1 nguyên vẹn; explicitLF
cho reviewscript giữ checksum ổn định khi checkout. Đây là packaging/provenancefix,
không thay phép tính, sourcefacts hoặc model. Lệnh Verify hiện dùng overlay/reviewv2.


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
