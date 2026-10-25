# Chưa phát hành — Baseline financial full10 (2026-10-23)

## Indicators v1 — Giai đoạn 4: backend API (2026-10-25)

Thêm `web/backend/app/fundamentals.py` (đọc read-only, kiểm hash) và 4 endpoint
`/api/v2/stocks/{ticker}/overview|fundamentals|scores/{year}|peers`. % thay đổi giá dùng
adj_close, giá hiển thị dùng raw_close. Pointer `configs/product/indicators_v1.json`,
thêm vào `publish_hf_data.py` và `deploy/render/data-files.txt` (chỉ dry-run, chưa upload).
Tests: `FundamentalsApiTests` trong `tests/unit/test_terminal_api.py`.


## Indicators v1 — LCTT trực tiếp cho F/M (2026-10-25)

Map CFO từ mẫu lưu chuyển tiền tệ trực tiếp (kiểm cân đối dòng tiền), khấu hao dự phòng từ
mức tăng hao mòn lũy kế cho M-score (gắn cờ, có mục kiểm trong qa-report). Coverage 2025:
F 77,7% → 88,4%, M 71,9% → 80,0%. Run mới `inputs-5b4836454b70d737`, `indicators-2c4a24e3830d325f`.


## Indicators v1 — Giai đoạn 3: QA độc lập (2026-10-25)

Thêm `scripts/verify_indicators.py`: tự viết lại công thức (không import engine), tính lại
800 ô ngẫu nhiên (PASS), đối chiếu EPS công bố, outliers, spot-check 10 mã, coverage và mục
tiêu 2025 kèm nguyên nhân theo field; ghi `qa-report.md` + CSV vào thư mục results.


## Indicators v1 — Giai đoạn 2: engine tính chỉ số (2026-10-25)

Thêm `src/delta_t1/indicators/compute.py` (hàm thuần: 15 chỉ số hiển thị, giá/số CP,
Piotroski F, Beneish M, Altman Z và Z''), `scripts/build_indicators.py` (SQLite
`indicator_values`/`company`/`latest`, wide CSV, coverage, manifest) và
`tests/unit/test_indicators_compute.py`. DStock giờ lấp cả mã-năm CafeF thiếu (ngưỡng 85%).


## Indicators v1 — Giai đoạn 1: bảng input chuẩn (2026-10-25)

Thêm `src/delta_t1/indicators/inputs.py`, `scripts/build_indicator_inputs.py`,
`tests/unit/test_indicator_inputs.py` và quyết định D-IND-01. Gộp CafeF Regular +
raw ngân hàng/CK/bảo hiểm, chuẩn hóa dấu chi phí, đánh lại nhãn khối tài chính
KQKD bị lệch, kiểm DStock theo field, ghi checks/coverage/manifest vào run mới
`inputs-633098561762877d`. Không sửa artifact cũ.


## Financial period serving và UX chỉ số (2026-10-24)

Thêm offline EPS source builder có raw/hash/period/code/unit checks, ledger đầy
đủ kỳ mục tiêu, SQLite read-only theo ticker và trạng thái SOURCE_REPORTED riêng.
Giữ provider-zero chưa xác nhận ở pending, không ghi đè source hoặc scores cũ.
Chạy calculator coverage cho cached annual partitions, xuất input blockers thay
vì tạo scores thiếu input. Panel chỉ số dùng năm/kỳ báo cáo, mô tả mục đích ngắn,
history theo năm và source details; bỏ package IDs khỏi các lựa chọn chính.
Đây là thay đổi local; không tuyên bố coverage sáu families đầy đủ hoặc đã deploy.

## DELTA upgrade — local implementation (2026-10-24)

- Tổ chức lại Home/Stock/Atlas/Financial/Lab; typography 15/14/12px, local Vietnamese mono,
  accessible tabs/drawer/search, lazy deep panels, full-key bounded cache và revision links.
- Typed six-indicator adapter, hai Z reviewed FY2024, exact supplementary components/missing
  inputs; giữ null/decimal/vintages, không thay baseline dataset hoặc PIT gates.
- D0/R0 ledger/dedup và frozen diagnostics; R1 757 configurations/217 transforms independent
  replay PASS. Candidate P1/P3 k2 đạt geometry/seed targets, chưa promote source/usefulness.
- Polynomial rectangular migration, dynamic labels/palette/matrix và profile-only API payload.
- R1 sidecar 202 snapshots/186.228 observations: selector baseline/P1/P3, saved peers/diagnostics, source/version/revision adapters; NOT_PROMOTED và giữ baseline mặc định.
- Browser 25 responsive cases PASS; production build/bundle/synthetic checks PASS. Full suite
  984 tests: một missing legacy fixture error, bốn optional Streamlit skips; chưa public release.
- Chi tiết/pins/recovery/limitations tại `docs/DELTA_UPGRADE_PLAN.md` §11 và `web/README.md`.


## Demo follow-up — bộ sáu chỉ số reference và chất lượng cụm (2026-10-24)

Bổ sung API/panel EPS/P/E/P/B/F/M/Z từ hai gói đã pin hash; giữ nguyên decimal,
null, kỳ YTD/quý và snapshot/vintage. Tách khỏi sáu core ratios của B/C.
Thêm cảnh báo thanh khoản chi phối baseline A; không refit/đổi model hoặc research gates.
16 targeted API/adapter tests, production build, compileall và legacy JS syntax PASS.

## Execution59 — DELTA Intelligence demo web (2026-10-24)

Thêm Next.js terminal 5 modules, FastAPI read-only, A/B/C SQLite exporter/verifier,
search, timeline, scatter, migration alignment, security drawer, historical prices,
stock comparison, financial intersection và Research Lab. Giữ data/research gates.
10 API tests, production build, compileall, legacy JS syntax và 22-source replay PASS.
Full suite PARTIAL (240s timeout ở crawl fixture). [Runbook](web/README.md).

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

## Nội dung từ checkpoint trước integration

Execution56: push checkpoint f1a5ba7 trước chạy; thêm offline driver/config trên handoff
1.172 candidates/11.720 annual rows. Tính lại 70.320 core ratios từ selected CafeF,
DStock, reviewed PDF/HTML inputs, giữ direct-CFO evidence và source partitions.
Reuse k=3/seed42/n_init20/max_iter300/zscore/no winsorization/no PCA; checkpoints theo
năm, immutable result, PowerShell Status/Check/Run và independent verifier.
11 targeted tests, compile, synthetic smoke và 1.786 input pins/scaler/assignments/
inertia/profiles/checkpoints PASS. Cả 10 năm có cụm nhỏ, chất lượng cần review;
không promote original-six/PIT/research/M3. Không network acquisition/PDF/OCR mới.

# Chưa phát hành — Gom lịch sử financial vào archive (2026-10-23)

Execution55 chuyển162data/44report roots vào financial-history-20261023; main data221→59/report57→13. Giữcurrentinput/provenance/boundarycontrol,797anchorsPASS; inventory/filemetadata vànetworkhashes khớp.205directoryIDs nguyênvẹn;1BRCreport kiểmđủpre-pinned manifest memberhashes thayidentityproof. Catalogue/availability/restore vàmasterreportupdated;khôngsửa dữliệu/hashfrozen,counter,formula/model.Đây làmove cùngvolume,khôngclaimgiảmdisk.0network/PDF/OCR/model.

# Chưa phát hành — Clean sâu cache tài chính (2026-10-23)

Execution54 lưu lạnh 102,504derivedcandidatefiles/11,058,805,949bytes của batch500/800/1100/1400 vào4ZIP (661,305,882bytes), kiểmmemberSHA256/inventory/archive/plan/controlhash trước nativePowerShellprune. Raw/receipts/network/results giữtrực tiếp;713directinputpins/11.720handoffrows nguyênvẹn. Restorefixture/pathguardsPASS; sourcecode/configpinned khôngđổi. RútgọnREADME/START HERE, thêmdata/artifactsREADME vàavailabilityindex. Fullhistoricalreplay cầnrestorecache;M2chỉđọchandoff.0network/PDF/OCR/modelrefit;PIT/M3vẫnPARTIAL.

# Chưa phát hành — Cleanup project trước M2 (2026-10-23)

Execution53 archiveverify/prune2,889files;9historicalreportfolders đượcđưa vàoZIPexactbytes, giữactivefrozenpins vàraw/canonical/counters. CachePython/test đượcgỡ; cóplan/hash/restore. Tạo namedhandofffinancial2016–2025 vàbảnglệnh scripts/README;updateMasterreport/index/activepointers vàarchive links. Coveragekhôngđổi1.172full10/13.529rows;no network/PDF/OCR/modelrefit. Không xóa sourceevidence chỉbằng reporttóm tắt, không renamepinnedcode/configs.

# Chưa phát hành — Review95financial one-gap (2026-10-23)

Execution52 review95mã thiếu1năm theo cached CafeF/DStock, pin761inputs và178rawfiles.59cases không có numeric CafeF partition;26complete core;4arithmetic-pass leads API2021/IPA2021/CAP2022/SBD2024 có multiple partitions nên chưa nhận.0newaccepted; vẫn13.529rows/1.172full10. CSVreview/partitionQA/summary/hashverification/report đãseal; master/plan/indexupdated.0request/PDF/OCR,khôngnớiQAhoặcsourcepriority; ưu tiên baselinefinancial-onlyM2trêncohortđãđủ tiếp, chưafitmodel. Originalfamilies/PIT/M3PARTIAL.

# Chưa phát hành — Làm rõ flow hai nguồn financial (2026-10-23)

Execution51 chỉ cập nhật plan và report tổng: CafeF baseline + DStock complete-vector bổ sung theo mã–năm, chưa ghép từng field hoặc reconcile toàn bộ overlap. Kiểm offline1.683DStock+11.835legacy API+11PDF/HTML=13.529rows;761heldcases/257Regular và93candidates ngoài schema. Ghi rõ550no-observations/103denominator/36missing/33membership/39QA-scope là primary groups; số kỳ không phải sốPDF. Coverage vẫn1.172full10;0request/PDF/OCR, không thay run đã seal hoặc acceptance policy. Ưu tiên review95one-gap vàcached sources trước đề xuấtPDF.

# Chưa phát hành — DStock remaining API:1.172full10 (2026-10-23)

Execution50 thu1.647freshcases/360candidates,961rows/+170full10;13.529rows/1.172full10,12.568baseline rows giữ nguyên. Cả2.444Regular gaps đã thử;761heldcases/257Regular và93sector/unknown táchschema.47targeted tests/independent checks PASS;0PDF/0OCR. Core348+metadata11requests;15checks trước nhậnrow,không nới QA hoặc reset budget. Metadata11empty;catalogue probe không chạy do automatic approval review usage limit,0request. Full10/status/one-gap/fieldreview/cohort exports/master/activepointers cập nhật;originalfamilies/PIT/M3PARTIAL.

# Chưa phát hành — DStock đạt1.002full10 sau cash QA (2026-10-23)

Execution49 triển khai nguồn API công khai DStock, checkpoint vàcomplete-vector reference recovery. Pilot10→20→50→100→600candidates/797cases:738pass/1.017full10sơbộ; bổsung3cashchecks vớiunchangedtwo-cap precisiongiữ16cases, bàn giao722newrows/12.568rows/**1.002full10** (+533),11.846oldrowsunchanged.194requests/194attempts/28.262.575bytes,0PDF/0OCR;networkdừng08:10:24UTCtrongownerwindow1giờ.42tests/compile/synthetic/4.332independentratios/23.826sourcevalues/replayPASS. Xuấtcohorts3/5/8/10y,danh sách1.002vàstatus1.522,fieldreview21cases(16held/5smallresidual). Masterreport/activepointers/plan/ADRupdated;PIT/M3/originalsixfamilieschưađạt. Khôngthayfrozenrunhoặcmodelcũ.

# Chưa phát hành — HSG recovery và DStock source pilot (2026-10-23)

Execution48: HSG FY2024/2025 cache review64fields/8OCRpages,12independentratios/2CFObridges,11.844oldrowsunchanged;11.846rows/469full10. VDT2019 onePDFwithinapprovedpilot heldscope. Shadow sign audit3potential/0accepted. Theo owner kiểm traDStock:2frontendassets+5APIresponses,6cases/4tickers,5cases11/11exact;VHC2024PDFcontrol8/8exact,TCM2013held. DStock0PDF/0OCR/0accepted; không sourcepriority/PIT promotion. 4unit/compile/synthetic/offlineauditsPASS. Masterreport vàactivepointers cập nhật;goalPARTIAL.

# Chưa phát hành — Cached four reference recovery (2026-10-23)

Execution47 phục hồi DCM2025/VEA2025/PAN2024/VHC2024 từ4cachedconsolidatedPDFs:131reviewedfields/21selectedOCRpages,47exactaccounting/4CFObridges,0network/download.11.840→11.844reference rows/464→468full10,oldrowsunchanged; giữVEAqualifiedauditwarning vàVHCrawsignpresentation.27targeted/compile/synthetic/source/24independentratiochecks/replayPASS;OCRcampaign155pages/0errors/replay0charge. Currentcohortexportsv2/masterreport/activepointers/planupdated;goal/PIT/M3vẫnPARTIAL,chưamở50.

# Chưa phát hành — Cache recovery readiness (2026-10-23)

Execution46 resolve acquisition metadata28→211/211 PDF files trong inventory cũ bằng exact path/hash/URL receipts, không suy statement identity. Xuất reference cohorts1.365/1.168/790/464 mã theo3/5/8/10kỳ liên tiếp, giữ11.840rows/464full10 và mọi gates. Queuecache11cases/10mã; dependency queue có điều kiện cho1.001full10:537candidates/667annualdependencies, không phải PDFcount/approval.0localrequests/downloads/OCR;14targeted/compile/synthetic/source/exportchecksPASS;masterreport/index/planupdated. Goal vẫnPARTIAL.

# Chưa phát hành — ReusablePDFpilot10 (2026-10-23)

Execution45 thêmPowerShellPDFworkflow códurablecounter/source/cache/text/selectedOCR/review/reference/status; pipelinepilot10:1CNT2018phục hồi,7sourcepending/2cataloguenoexactmatch.1newPDF/4OCRpages,11.840rows/464full10(+1), old11.839rowsgiữnguyên. OCRcontrollerV2fixprepare/runresultcollision vàreuseregisteredpages; actualresume0additionalrequests/OCR.41tests/compile/synthetic/source/independentratiochecksPASS;reporttổng/index/planupdated. Sourceadapters/manualreviewcòn hạnchế,pilotPARTIAL,next50/PIT/M3closed; approvalbatch100đượcgiữtrongscope.

# Chưa phát hành — Bulk recovery queue (2026-10-23)

Execution44 gom635 candidates/862 missing annual cases; chọn100 mã9/10 chỉ vướng một accounting check, xuất field-level review list và đề nghị≤100PDF chia2batch50/pilot10 chờownerduyệt. Counts giữ11.839rows/463full10,0recovered; không nớiQA hoặc tảiPDF.4tests/compile/hash/dependencychecksPASS; cậpnhậtmasterreport/activepointers/plan.

# Chưa phát hành — Full quarterly receipt triage (2026-10-23)

Execution43 audit124remaining annual-input gaps bằng toàn bộ pinnedQUYreceipts, version2 sửa truncatedpage5diagnostic màgiữnguyênoldartifacts. Numericheadercoverage khôngannual/PITacceptance;11.839rows/463full10 giữ nguyên. PrimaryPTB2018/PLC2025leads vàproposal≤2PDFchờowner,0PDFopen/download/OCR.16tests/compile/synthetic/hashandcoveragechecksPASS;reporttổng/activepointersupdated;goalPARTIAL.

# Chưa phát hành — Annual source gap audit và issuer HTML reference (2026-10-22/23)

Audit125annualinputgaps:58internal/38before/29after;legacy3columnsđềutrống,oldcatalogueviewchưamatch. BoundedprimaryHTMLlookup giúp phục hồiPLX2023,462→463full10/11.839rows;CTD2023sixmonthtransitiongiữhold. SnapshotwebextractkhônggọirawHTMLbytes;datecaptionwarningsgiữriêng,unchangedprecision/accountingchecks,0PDF/OCR. External3webtoolcallsloggedriêng/localreplay0network.24tests/compile/synthetic/source/valuechecksPASS;masterreport/index/planupdated;finalgoalPARTIAL.

# Chưa phát hành — Master financial report và near-full10 review (2026-10-22)

Tạo live `artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md`: tổng hợp toàn bộ discovery/pilots/history/audits/acquisition1522/reference/baseline/precision/CFO/near-full10, before-after vàremaining work; quyước cậpnhật mỗi execution, giữsealedevidence vàchưa cleanup. Đồng bộactivepointers/planheader.

Review412one-yeargaps, thêm3single-document core-reference vectorsBRC/GAS/VNM (1newcachedvisualCFO fact),11.838rows/462full10. Giữnguyên11.835oldrows/APIquarantines;409one-yeargaps và2.452annualcases còn lại.39targeted/compile/synthetic/hash/valuechecksPASS;0network/PDF/OCR mới;finalgoalPARTIAL.

# Chưa phát hành — Direct CFO cache recovery (2026-10-22)

Kiểm723cases/181mã bằngexactdirect-method code+label/component/annual/provider/sourcechecks, phục hồi657core-ratio reference rows; dataset11.835/1.422candidates/459full10 (+32). Cohorts1.365≥3consecutive,1.168≥5consecutive,1.098≥8-of10 giữriêng, khôngreportthànhfull10/PIT. Audit480mãthiếuannualmappedperiods và156annual/Q4candidatecases; backlog2.455khôngphảisốPDFphảitải.33targeted/compile/synthetic/source-and-valueverificationPASS. Originaldata/model/6family/PITgatesgiữnguyên;0network/PDF/OCR. Execution40/report; finalgoalPARTIAL.

# Chưa phát hành — Precision QA và document triage (2026-10-22)

Implement offline versioned exploratory QA với absolute+relative residual caps, zero-policy replay và nguyênvẹn6.976baseline featurevalues. Actual11.178rows/1.416candidates/427full10 (+4.202rows/+376full10); giữsource/raw/fact/PIT/model cũ. Xuất QA/coverage/dataset,3.112annual documentreviewcases và queue548mã/736gaps; inventory211PDFfiles/202hashes,7filenamehintcases, chưa xác nhận sốPDFphải tải.0network/PDF/OCR.26targetedtests/compile/synthetic/hash-and-count verificationPASS. Report/Execution39; finalfinancialgoalPARTIAL.

# Chưa phát hành — Coverage/precision diagnosis (2026-10-22)

Offline key-parity xác nhận baseline51 bị giảm nhiều bởi exact-zero QA residual;4.137/4.147 financebridge differences2016–2021 chỉ1rawunit. What-if1unit cho505 balanced-panel candidates, chưa áp tolerance/acceptance hoặc đổi model. Report/source pins và Execution38; không network/PDF.

# Chưa phát hành — Financial exploratory baseline (2026-10-22)

Owner duyệt core-ratio financial baseline độc lập. Đã fit static K-Means2016–2025 trên6.976 rows/1.311 registry candidates (51 có đủ10 kỳ reference); FY2025 zscore982/1/1, rank sensitivity395/361/228 cùng984 mã, chưa chọn final model. Reference6families87 rows/11 mã/5 full6 cohorts giữ riêng. Financial/PIT/M3 cuối vẫn PARTIAL; market handoff chờ teammate, không PDF/OCR mới.

Owner explicitly selected exploratory core ratios while finishing original6families in parallel. Separate reference registry, same-year static fits, no publication/identity inference, no market changes or portfolio selection.24 controls/30 targeted/compile/synthetic/output verification PASS. Xem Execution36–37.

# Chưa phát hành — Cached fact verification (2026-10-22)

Đã xác minh557 fact/vintage observations/11 mã:334 khớp,63 khác giá trị hoặc vintage,160 chưa có direct alias. 9 Z reference tái lập khớp giá trị cũ; bổ sung2 kỳ Z reference BRC2024/VNM2024. Có18 đối chiếu CF interest khớp PDF trong khi KQKD gắn nhãn sai khác; chưa sửa mapping chung. Không PDF/OCR mới; full10y/PIT/M3 vẫn PARTIAL.

Giữ API/report identity unresolved; exact CF-interest match chỉ theo reviewed anchor, không global alias/repair hoặc canonical/PIT promotion. 20 tests/compile/synthetic/source hashes/old-value parity PASS. Xem Execution35.

# Chưa phát hành — Expanded API input review1522 (2026-10-22)

Đang review trực tiếp raw annual 2012–2025 của 1.522 mã, mở rộng mapping và matrix 118.716 tasks. Giữ riêng API arithmetic diagnostics với reference đã kiểm chứng; không tải PDF/OCR hoặc tự mở acceptance/PIT/M3. Kết quả reference stage33 vẫn 11 mã có giá trị, 5 mã đủ6 tại một cohort, 0 mã đủ bộ2016–2025.

Exact code/label, provider partitions, 11 accounting checks, fail-closed checkpoint/source hashes. Conditional EMZ và F signals chỉ là arithmetic diagnostics; không giả EBIT/share/debt proof. 38 targeted/compile/synthetic/PowerShell parse PASS. Execution34 ghi handoff và no-PDF boundary.

# Chưa phát hành — Compute-first1522 offline (2026-10-22)

Đã hoàn tất acquisition và QA diagnostic cho 1.522 mã; compute-first offline tái tính 85 dòng reference từ input reviewed. Có 11 mã có ít nhất một family, 5 mã đủ 6 family cùng năm/scope/vintage (ACV, BRC, FPT, GMD, MWG); chưa mã nào đủ bộ 10 năm 2016–2025. Không tải PDF/OCR mới hoặc tự nâng API candidate thành dữ liệu đã xác minh. VNM F vẫn thiếu input; PIT/M3 chưa mở.

Báo blockers trước khi lập kế hoạch PDF; alias absence không chứng minh raw thiếu field. Tách same-cohort reference, annual/period/TTM và PIT readiness. Giữ immutable v1, metadata fix v2 không đổi85 giá trị. 43 targeted/compileall/synthetic và manifest/numeric parity PASS.

# Chưa phát hành — Dashboard giám sát workflow (2026-10-22)

- Thêm `/monitor/` và API read-only vào HTTP edge hiện có; CLI `monitor`/PowerShell mởlocalhost8765, không cần product bundle.
- Hiển thị tiến độacquisition/QA riêng, mã/checkpoint/log/cập nhật, lỗi/stale activity; tự refresh5giây, giữ last-good status khi writer chưa ghi xong. Không suy ETA/metric validity hoặc worker liveness từ progress.
- Link tải report/coverage/symbols/missing/document queue chỉ mở khi artifact đã xuất hiện; path allowlist trong project, không điều khiển pipeline.
- 9targetedtestsPASS (HTTPloopback chạy ngoài sandbox), compileall và nodecheckPASS; visualbrowser kiểm tra realprogressPASS. Frozen acquisition/QA code và artifacts không sửa.

# Chưa phát hành — Inventory1522 và QA offline (2026-10-22)

Acquisition1.522/1.522 đã hoàn tất và finalauditPASS. Đang hợp nhất10cohort disjoint và chạy QA offline từng mã, có checkpoint, coverage196slots/mã, report gaps/fieldpresence/displacements/conflicts và selective document queue. Không PDF/OCR/network hoặc numeric/PIT acceptance mới; baseline29/30 giữ nguyên.

Pin10terminalcohorts/raw/receipt/shard;196coverage slots/mã;diagnostics chưaacceptfacts,Unknown/Bank/Securitiesheld.19targeted/compile/syntheticPASS. [Execution32](docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#32-inventory1522-va-qa-offline-22102026).

# Chưa phát hành — Audit800 và recovery722 (2026-10-22)

Tổng800 đã terminal task accounting;4DTRCDKTHTTP500 giữ deferred quarantine. Owner duyệt audit rồi nối722 mã còn lại qua recoveryv2,300+300+122. Controller đang chờ audit800, không claim API đang chạy;0,4s/oneworker/checkpoint/deadline cũ. Numerical/PIT/M3 PARTIAL.

Proof yêu cầu terminalHTTP500/2attempts/exactreceipt+request+hash; mọiaccessboundary/lỗi khác vẫnHOLD, khôngretry hoặcacceptfacts. Audit producerpin trước mở disjointwaves.22targeted/compile/synthetic/realDTRproofPASS. [Execution31](docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#31-audit800-va-resume722-22102026).

# Chưa phát hành — Overnight toàn bộ current registry (2026-10-21)

Owner đã duyệt tự nối toàn bộ current registry1.522 candidates: sau tổng800, tiếp300+300+122. Overnight controller đang chờ total800;0,4s/one network worker/checkpoint, audit mỗi parent và finalwave. Giữ originaldeadline22/10/2026 12:55UTC/source latches; không bảo đảm xong trong đêm. Numerical/PIT/M3 vẫn PARTIAL.

722remaining=300+300+122;421legacyUNKNOWN giữ provisional. Chờ current800 rồi audit/gate trước từngwave vàfinalaudit; giữ máy thức trong phiên, khôngshutdown hoặcđổi powerplan.34targeted/compile/synthetic và schedulecoverage testPASS. [Execution30](docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#30-overnight-toan-bo-registry-21102026).

# Chưa phát hành — Audit500 và batch300 tiếp theo (2026-10-21)

Tổng500 đã terminal task accounting; batch300 mới đang chờ audit raw/candidate của batch trước. Controller tự nối đúng1batch khi integrity/engineering/offline replay PASS; hướng tới tổng800, delay0,4s, một network worker. Bốn lỗi GTX HTTP500 giữ quarantine; field/kỳ thiếu deferred review. Numerical/PIT vẫn PARTIAL, baseline29/30.

Gate kiểm exact raw replay và4GTXCDKTHTTP500/2attempts; không retry/reset hoặc nhận financial/PIT. Fresh API-only wave giữ140REPORTtasks/mã, bỏ catalogue placeholders tại host đã latch.29targeted/compile/synthetic PASS. [Execution29](docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#29-audit500-va-batch300-tiep-theo-21102026).

# Chưa phát hành — Financial bulk300/0,4s (2026-10-21)

Tổng200 đã hoàn tất task accounting; lượt hiện tại mở rộng thành300 mã (100 đang dở +200 mới), hướng tới tổng500. Owner duyệt delay0,4s, một network worker. Giữ checkpoint/counters/deadline và source hard-stop; chưa đủ numerical/PIT, baseline29/30. Xem mục28 để theo dõi tiến trình; không cộng trùng checkpoint total300 cũ.

Giữ single network worker, original deadline và toàn bộ source latches. Tối ưu local cache/journal/snapshot;23targetedtests/compile/synthetic PASS. [Execution28](docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md#28-batch300-và-delay04s-21102026).

# Chưa phát hành — F3 GAS reference và SHS quarantine (2026-10-20)

- TảiGASoriginalFY2025, review32facts vàrecompute2annualZ″EMcurrent/comparative;8accountingchecksPASS, cònfamiliesmissingnull, strictPIT0.
- Criticalreview14cases:4matches,2GASannualdifferences,7SHSnamedPDFnonzero/APIzero,1unresolvedorphan.2APIpartitionsquarantine,0repairs/acceptance;6meaningfultests.
- ReusecachedSHSPDF10MB sau khi2newVI/ENfileschạm25MBcap; giữ50MBfailedtransfercounters. SHSpublicationdate/hash mismatch khôngfill; GASexplicitpub04/03/2026.
- OCRv10cumulative130pages/0errors; network2.284requests/211.688.837bytes/18PDFattempts, originaldeadline/latches/caps giữ nguyên. VDSC302 khôngfollow;2independentauditPDF vàDCM/HSGpriority cònpending.
- CorePowerShell nối12documentconfigs/criticalquarantine/GASreference.167targeted/compile/syntheticPASS; goal/F3/PIT vẫnPARTIAL, khôngscale50/M3 hoặcđóng VNM F.

# Chưa phát hành — F3 catalogue và independent audit (2026-10-20)

- Thu15StockbizHTML,parse267rows/237financialPDFlinkcandidates; observed2013–2017 chỉview đầu, không claim catalogue đủ hoặc thiếureport bằng absence.
- Fixedseed6auditdocuments DBC/VCS/FOX theo3exchanges/eras, không resample theoPDFavailability. Tải4PDF gốc, OCR21selectedpages; cumulative120pages/0errors.
- Review4/6documents,35/36exactfieldmatches; DBCFY2022costsign(PDFnegative/APIpositive) giữquarantine, khôngsilentabs/rowrepair. Unitsoverlay16.704monetaryrows,827EPSheld.
- CorePowerShell nối catalogue/parser/newdocs/OCRv9/sampler/units/auditreviewv3;161targeted/compile/syntheticPASS. Localcounters2.276requests/147.695.077bytes/15PDFattempts, originalanchor/deadline/latches giữ nguyên.
- Goal/PIT/F3deliveryPARTIAL;2auditPDF và4priority2025periods cònmở, chưa50/M3 hoặcđóng VNM F.

# Chưa phát hành — Sealed history20 và ACV report vintages (2026-10-20)

- Acquisition15mã bổ sung terminal:3.300tasks accounted,1.486newAPI/180cache,198.778candidateobservations,0parsererrors; inherited2.255requests/117.066.733bytes, không resetdeadline.
- FullQA341missing slots/115periods,193documentqueueperiods/4priority1;3annualshifts vàSHSnonzeroorphan giữ nguyên, không autoaccept/rowrepair.
- Reuse2ACVPDF,115reviewedfacts (52legacyrecheck+63additional);12vintagemetricvalues/10year-familykeys,6FY2025recompute exactmatch. EPS2024original/restated giữ riêng; auxiliarypublicationunknown không lấy ngày primary thay thế.
- CorePowerShell nối finalbatchverify/QA/referencecohorts;151targeted/compile/synthetic/activeverifyPASS. Offline resume cùnghash,110journal/OCRfiles unchanged;320frozenpins/11contracts.
- Baseline29/30 vàVNM Fnull, strictPIT0 giữ nguyên. Không mớiPDF/OCR hoặc mở50; knownM2frozendoc fullgateissue chưa waive.

# Chưa phát hành — F3 offline QA preview và selective queue (2026-10-20)

- QA riêng cho receiptpreview và sealedbatchsnapshot, pin assignment/raw/shards/sourcehashes; không network hoặc acceptfacts.
- Preview563receipts/60.014cells:1.007provenstructuralzeros,330unresolvedcodes,1.029rawchecks equal/7different; DCM/GAS/HSG2025 possibleannualshifts vàSHS2025 nonzero-unmappedLCTT được giữ đểreview.
- Queue8anomalyperiods, không thay finalmissingcoverage hoặc independentaudit. Không rowrepair/scaleinference hoặc dùngregularscoremapping cho bank/securities.
-140targeted/compile/synthetic/PowerShellverifyPASS,1.126pins/665unchangedfixedfiles; collector vẫnlive,450newrequestcheckpoint, chưafinalcoverage/metrics hoặcfullgoalPASS.

# Chưa phát hành — F3 history collector cho mẫu20 (2026-10-20)

- Bounded candidate gate9checks PASS theo adapter mới, giữ4strictparserfailures và536quarantinedcells; không numeric/PIT promotion.
- Collector mới3.300tasks cho15mã bổ sung:2.100API+1.200catalogueaccounting; reuse180page1cache, cataloguelatch giữ nguyên. Candidate shards/checkpoints, independentpaging và inheritedledger/deadline.
- Worker đã chạy vàpoll live;121newAPIreceipts tại07:33:46UTC, chưa finalcoverage. Không sửa frozenpilot5/trial50 hoặc registry.
-129targeted/compile/syntheticPASS; fullsuite564tests3failures/3errors, focusedHTTP5/M1reporting5PASS bằng đúngruntime/localtestpermissions. KnownM2frozenhashissue giữ nguyên, fullgate chưaPASS.

# Chưa phát hành — Financial F2 gate và metadata/template mẫu20 (2026-10-20)

- Engineering gate17checks PASS cho bước candidates; giữ1.100tasks accounting, seeded6audits, exactquarantine vàoriginaldeadlines.
- Chọn15mã bổ sung theo registry/legacyidentity/strata; acquired15profiles khớp mã/sàn,3exchanges/7currentsectors/11industries.
- Acquired180annual/quarterpage1APIprobes; cumulative769requests/102.828.239bytes,0newPDF/OCR. Giữ4strictparserbankNVfailures trong evidence.
- Adapter riêng replay180/180,0errors;24.020candidatecells,536ambiguous/unmappedquarantine, không positionallabel hoặc numeric/PIT promotion.
- 120targetedtests/compile/synthetic/activeprocess+verifyPASS;130resume evidencefiles unchanged,99frozenpins/10contracts. Strictoldparser4/180failures vượt1%, F3fullhistory gate chưa mở; baseline29/30 vàVNM Fnull không đổi.

# Chưa phát hành — Đối chiếu đủ sáu kỳ audit financial (2026-10-20)

- Tải đúng3PDF BRCFY2018/Q22021 vàFPTQ32015 theo linkcatalogue,23.401.578bytes; inherited574requests/98.083.449bytes/11PDFattempts, giữanchors/boundaries.
- Đối chiếu6/6mẫu:49/54fieldmatch,5cells lệch1VND. Explicit candidatequarantine theo sourcepartition, không autooverride; giữcovertypo/scope vàquarterCFOYTD.
- OCRthêm17pages, cumulative99/11runs/0errors. Active7documentconfigs/OCRv6/reviewv4; referencebundle vẫn270facts, strictPIT0,29/30FY2025baseline không thay.
- 73targetedtests/compile/synthetic/activeverifyPASS;69frozenpins/8contracts và107resume evidencefiles unchanged,0newrequests/0newOCR.
- Engineering gate20 cần evidence task/failure/parser/resume/budget và diverse metadata; auditcompletion không tự promote financial/research/M3.

# Chưa phát hành — BRC company references và independent field audit (2026-10-20)

- BRC2014/15 thêm46reviewedfacts/2basicEPS; explicit company scope không trộnconsolidated,5familieskhác vẫnchặn. Bundle8 có270facts/41annualvalues=29legacy+12new,6periodEPS; strictPIT0.
- Seeded audit3issuers/6docs, đãreview3: FPT2023/GMD2024 khớp9/9, GMDQ42019 giữ2chênh1VND vàsource arithmetic anomaly/CFOYTD.3sampledocs pending; không mởbatch20.
- HaiGMDissuerPDF mới, text-first khôngOCR; local571requests/74.681.871bytes/8PDFattempts. Externalpreview ghi riêng, remainingattempt1. OCRcampaign82pages/9runs/0errors; oldanchors/reservations giữ nguyên.
- ActivePowerShell5documentconfigs/OCR4/bundle8/auditplan+review, giữimmutablebaseline/registry/sourceboundaries.71targeted/compile/synthetic/verifyPASS, offline88evidencefiles unchanged,51frozenpinsPASS. Fullgate chưaverified vàM2-PREP frozenhashissue chưawaive.

# Chưa phát hành — Financial OCR campaign, units và date references (2026-10-20)

- BRC2015 BCTN exact observed URL tải13.220.889bytes,100pages mixed;75pages text chỉ đảm bảo phần extract, financial scan nhúng chưaOCR. Active4document configs verifyPASS, inherited569requests/46.902.054bytes/6PDFattempts;42frozen pins giữ nguyên.
- Coordinator nhập mọi old OCR reservation, chặn duplicate page/cap reset khi đổiconfig;63pages/7runs/0errors, global40/PDF–1.000/batch–12.000/campaign và72h/90d. Offline resume4journals/63reservations không đổi.
- MWGQ3:70reviewedfacts/8accountingchecks,4EPS theo3/9months. Catalogue date trước exactPDFcreation bị chặn PIT. FPT H1 thêm6note facts/2EPS, share revision giữ2024vintage. Latest224facts,10annual+6period references ngoài29FY2025baseline.
- Monthly period date view dùngexisting policy/calendar,240rows/36dateeligible references; không TTM/identity/research claim. Same-day conflict/mixed-input vintage fail-closed; tuổi báo cáo chỉ khieligible.
- Unit overlay pin3cached display sources,7.520rawVND candidates/370specialEPS; không magnitude inference, source priority, rowrepair hoặccanonical acceptance.47targeted/compile/synthetic/activeverify PASS;33frozen pins/registry/baseline unchanged. Fullgate còn unverified M1 terminal result và knownM2-PREP fingerprint mismatch.

# Chưa phát hành — MWG2015 issuer documents và text review (2026-10-19)

- Dùng catalogue UI chính thức để lấy exactlinks, tải annual/Q3PDF13.182.640bytes; inherited568requests/33.681.165bytes/5PDFattempts. Annualtext-first75/84pages, Q3scan giữqueue, không OCR mới.
-46MWGreviewedfacts/4accountingchecks, thêm4EPS/Zreferences. Latest148facts/390annualtasks/39values=29legacy+10newhistorical, không PIT/fullhistory claim. Printed signatureyear anomaly vàcomparative revisions giữ provenance; không rowabsent→0.
- Active PowerShell3documents/6OCRruns/2review layers VERIFY PASS;22targeted/compile/syntheticPASS. Cache hash reads mỗi input một lần; reference-only không tựpromotePIT. Registry/frozen4contracts unchanged.

# Chưa phát hành — Financial history reviewed bundle và notes (2026-10-19)

- Thêm full annual task grid390rows,102reviewed reference facts và6new historical EPS/F/M/Z; giữ29legacy FY2025, VNM Fnull và closed gates. Explicit GMD2014→2015 reference bridge chỉ TA2013/owned depreciation2014; EPS revision giữvintage,1VND conflict fail-closed.
- GMD2014 issuer PDF2.205.921bytes, inherited566requests/20.498.525bytes/3PDFattempts, không reset anchors/latches. Sáu selectedOCRruns55pages/0errors, cùngPDF cap cumulative27GMD2015; cacheFPT/VNMkhôngtải lại.
- BOM-aware baseline loader, duplicate/conflict/missing/quartile-vintage regression tests;21targeted/compile/syntheticPASS, PowerShell verify mọi layerPASS. Giữ draftVNM transcription và correctedversion lineage. M1 testlive;fullgate chưaPASS.

# Chưa phát hành — Selective financial PDF/OCR/reference processing (2026-10-19)

- Thêm bounded documents successor kế thừa journal counters/deadline/source boundaries;1GMD FY2015PDF/12.979.440bytes thành công,1FPT H1URL404 terminal. V1local missing cache_epoch dừng trước I/O; preserve v1→v2 lineage, không reset budgets. Cache lookup mở rộng tìm FPT/VNM Q2/2024, ngăn tải lại.
- Thiết lập Tesseract5.5.2 CPU vie+eng local trong .tools, pin wheel/models/runtime hashes; explicit-page workers timeout/reservations, text+TSV+confidence.16pages OCR/0errors, không WindowsOCR/cloud hoặc auto-acceptance. Có setup/process/verify PowerShell chạy lại được.
- Review63referencefacts:40GMD FY2015/14 comparative và23FPT Q2/H1/closing;8accounting checks PASS. Tính2Z annual bằng calculator cũ; giữ29/30FY2025. Reconfirm12cache conflicts, quarantineAPI. Explicit FPT publication18/07/2024→usable19/07/2024 theo policy cũ; chưa complete PITmetrics, không H1→Q2 hoặc annualize quarterly.
-73targetedtests/compile/synthetic PASS; acquisition/OCR/reference replay VERIFIED. Fullsuite468có6fail/error;5HTTPlocalhost rerunPASS, còn missingmatplotlib và M2-PREP frozen-document hash. Giữ assertions/artifacts/gates, goal tiếp tục active.

# Chưa phát hành — Financial history F2 offline QA (2026-10-19)

- Acquisition worker đã hoàn tất:563newrequests/563attempts,5.313.164bytes,27cachehits,71.073candidatecells,0pending. 980coverage slots gồm918main candidate-present/5auxiliary/57missing, không phải accepted financial history.
- Thêm QA module/config/PowerShell riêng, pin sealed report/raw/reviewed inputs/code, deterministic immutable outputs và verify. Không sửa frozen acquisition runner/raw/registry. Chứng minh1.161group-header zeros;69.912nonstructural cells,0unexplained orphans;code+label mapping diagnostic, không missing→0 hoặc dịch hàng.
- 1.646raw accounting checks có95differences;8.645annual–Q4comparisons có1.993differences, giữ provider flags/vintage/scope chưa verified. Detector bắt BRC/VNM FY2025 displacement;150reviewed-PDF input comparisons có138matches/12conflicts. Queue90issuer-periods ưu tiên cache;H1 không thay Q2,0accepted/PIT facts,29/30reference và closed gates giữ nguyên.
- 59targetedtests, compile/synthetic smoke PASS. Cập nhật active pointers/commands/missing-period table; full gate và replay evidence trong QA validation. Chưa PDF/OCR mới hoặc promote20.

# Chưa phát hành — Financial history acquisition pilot5 (2026-10-19)

- Implement successor PowerShell/Python fixedpilot5 cho annual/quarterly2013–2025 +auxiliary2012, NAM/QUY/LUYKE per-group pagination; frozen registry/code/dependencies, immutable raw/receipts, coverage/missing/anomalies/report verification và persistent transport/resume caps. Không nới frozen old runners hoặc scale gates.
- F0audit19legacy journals/35cache URLs, giữ cafef.vn/SSIhost latches; F1replay29/30PASS. Offline27cachehits tái xử lý5.724cells; wave25live thành công25attempts/141.491bytes, tổng7.256candidatecells,0parse errors/92unmapped codes;0newacceptedfacts/PDF/OCR. metrics export giữbaselineFY2025, không gọi historical compute/PIT.
- Đã khởi chạy hidden local worker tiếp F2 cùng counters/deadline; process/assignment và logs trong history_pit_v1. Không auto-promote20 hoặc chạy thêm worker trùng.47targetedtests/compile/synthetic smoke và checkpointverifyPASS; fullsuite bounded120s TIMEOUT ở legacy continuation verifier, chưa fullgatePASS, giữ trace/assertions. Index/active pointers cập nhật; registryv1 đang pin giữ nguyên.

# Chưa phát hành — Hai plan history và registry team (2026-10-19)

- Materialize market plan 2016–2025 +warm-up2013–2015, mục tiêu ≥1.500 cổ phiếu lịch sử; financial plan annual/quarterly2013–2025 +closing2012 theo dependencies, reference/PIT deliveries riêng cho M3.
- Tạo registry UTF-8 1.522 current discovery candidates: 500C5,452C7complete,7failed,3partial,138not-yet trong old campaign,422outside. Pin source hashes, C8 observed bounds/readiness snapshot, financial local export inventory và FY2025 pilot5 counts; unknown không thành not-crawled/zero.
- Bổ sung data dictionary/assignment theo registry hash, domain/range/owner/batch; cập nhật index/active pointers. Không crawl/network/OCR mới, không thay sealed artifacts, metrics29/30, old source boundaries hoặc research gates. Runners trong hai plan là future interfaces.
- Offline verification PASS:1.522unique records/45columns,952C8/905ready đúng snapshot,55mã có financial candidate/reference exports và1.467chưa match trong scope quét.37source files pin hash, C8price hash khớp sealed manifest,17local links của hai plan và git diff whitespace PASS. Không chạy full tests vì chỉ tài liệu/inventory, không đổi runtime.

# Chưa phát hành — VNM subsidiary debt review (2026-10-19)

- Acquire 7 observed PDF mới, 50.239.615 bytes: MCM/Vilico audited 2025, Vietsugar audited 2024/2025 và AGM 2026, VNM Q1/2025. 54 trang render/40 ảnh xem; OCR bị chặn trước output, không bypass policy. CloudFront discovery 403 được giữ boundary.
- Xác nhận MCM/Vilico cùng khoản vay 4–6 tháng 67/99 tỷ, đếm một lần; Vietsugar 420,793/587,716 tỷ đối chiếu được nhưng không có original tenor. Bounds thu hẹp vẫn không xác định leverage signal; không dùng nhãn current hoặc flow để suy stock. Giữ 29/30 và gates false; thêm PowerShell offline replay, pinned review, draft IR chưa gửi. 34 targeted tests PASS.

# Chưa phát hành — VNM quarterly debt follow-up (2026-10-19)

- Thêm bounded acquisition hai observed Q4 documents: 1 XLSX/1 PDF, 4.179.903 bytes; không retry các campaign cũ. Giữ raw receipts, workbook cell coordinates, 16 trang render/8 ảnh xem, source/image hashes và offline PowerShell replay.
- Q4/2024 workbook không có notes; Q4/2025/cached H1 notes chưa tách closing current portion 2024/2025. Primary Piotroski Table 1 xác nhận ngữ nghĩa gồm phần current; không thay công thức, không dùng reclassification flow thay stock. 0 new accepted inputs; goal PARTIAL 29/30.

# Chưa phát hành — Đối chiếu quarterly rows (2026-10-19)

- Kiểm chứng nhận xét owner bằng BRCUIlive và11boundedQUYCDKTrequests cho5mã; annualcache giữ nguyên. BRC/VNM có annual debt-row displacement trong2025, quarterlyrows đặt khoản vay/quỹ đúng nhóm hơn; chưa suy accuracy toàn bảng.
-64arithmetic checks/4conflicts,8BRC PDFspot checks chỉ rõ quarterly vẫn có missing/imbalance/vintage differences.0accepted metricinputs; pilot29/30 và gates không đổi. Evidence/replay tại`data/financial/cafef_quarter_row_check_v1/`.

# Chưa phát hành — Closing-debt continuation pilot5 (2026-10-19)

- Thêm completion runner PowerShell/Python, fixed5 config, explicit closing debt components QA và pinned PDF/image review; immutable successor result, offline replay/verify và queue2field-period. Không thay calculator hoặc29metrics đã seal.
- Acquire1PDF công ty mẹ VNM2.626.709bytes từ observed disclosure URL chưa request trước đó; note16/PDF40 xác nhận vay mẹ1–12tháng. Không suy phạm vi hợp nhất, không dùng flow/2023stock thay2024/2025.11trang render/9trang xem/0OCR; cached acquisition không request lại.
- Goal giữ PARTIAL29/30; VNM F8/9signals interval4–5. Cần closing original-maturity debt split tại công ty con. OldCafeF/TCBS/SSI campaigns giữ nguyên, không mởfinancial/research/cluster.
-12tests mới,46targeted tests, compile và synthetic smokePASS; PowerShellrun/replay/verifyPASS. Full448tests447PASS/1pre-existingM2-PREPdocs hasherror; giữ assertion và frozen evidence.

# Chưa phát hành — Provider/PDF validation pilot5 (2026-10-19)

- Thêm runner PowerShell/Python `financial_provider_validation`, config fixed5, durable bounded provider journals và offline reference decisions/recompute/verify.235reviewed facts/176comparisons/12conflicts, giữ raw và chọn đúng pinned PDF references; không shift rows, infer units hoặc promote gates.
- Đã lấy và kiểm SHA256 wheel VietFin0.2.0; source-route probes qua controlled client (không phải SDK): TCBS15HTTP404, SSIcatalog1HTTP403 rồi hard-stop.0newproviderfieldsQA,0newPDF/OCR; hai metadata/wheel requests riêng. Không gọi source accuracy hoặc goal complete.
- Recompute29/30 giữ nguyên; VNM F current-portion basis còn thiếu.34targeted tests, compile/synthetic smoke, PowerShellreview+verifyPASS. [Runbook](docs/crawl/FINANCIAL_PROVIDER_VALIDATION_USER_GUIDE.md), [report](artifacts/reports/financial-vietfin-pilot5-v1/report.md).
- Full436tests435PASS/1pre-existingM2-PREP input hash mismatch tại docs/DECISIONS.md; giữ assertion và frozen evidence.

# Chưa phát hành — Dọn active financial flow (2026-10-19)

- Đã gỡ 48 legacy financial entry scripts không còn caller trong source/tests/config hoặc runner được giữ; lưu exact bytes vào verified ZIP trước khi xóa. Temporary work được đóng gói cùng; không xóa shared modules/tests/config, raw/canonical hay dependency evidence.
- Rút gọn START HERE, đưa pilot5 runner/report/config lên đầu navigation; đánh dấu các lệnh cũ cần restore và chuyển link script đã gỡ sang archive. Có inventory, hash, restore collision checks tại `artifacts/repository/current-flow-cleanup-v1/`.
- Dọn thêm 8 thư mục báo cáo superseded (102 file), verify ZIP trước khi prune. Tổng 5.548 file; historical-only links trỏ vào archive, sealed evidence không bị sửa. Các reports/config/tests/dependencies còn dùng và market/M2 giữ nguyên.
- Financial vẫn PARTIAL 29/30; không reset CafeF campaign, không thay công thức hoặc chấp nhận nguồn mới trong cleanup.
- Self-review: khôi phục exact `scripts/crawl_cafef_financial.py` vì một test import `verify_handoff` theo dotted module path; giữ assertion và bổ sung guard cho dạng import này. Số xóa ròng là48scripts/5.548files. Full424tests có422PASS,1missing-module đã sửa và isolated rerunPASS,1pre-existingM2-PREP docs hasherror; compile,419Markdownlinks và sealed pilot replayPASS.

# Chưa phát hành — CafeF pilot5 execution (2026-10-18)

- Thực chạy BRC/FPT/MWG/GMD/VNM tới29/30recomputed+checked family cells;4complete workflows. VNM F giữnull8/9signals, interval4–5 vì chưa rõ original-maturity closing current portion2024/2025 sau cache/API/CafeFfullVAS/issuerEnglishnotes review. Goal30chưa đạt, statusPARTIAL_WITH_RESULTS.
- Thêm dedicated adapter code/label/template+per-group periods, disclosureCreateDate; tái hiện upstream BRC debt/interest conflicts và quarantine, dùng reviewedPDFinputs. EPSbasic/annualPE/book-snapshotPB/F-VAS9/M-VAS8/EMZ dùng calculators sẵn; giáraw chung22/04/2026, explicit event/PIT limitations.
- Thêm executableconfig, PowerShell/Python doctor/plan/run/report/resume/verify, durable journal/deadline/counters và immutable inputs/results/source snapshots.48transport/38logical/3PDFattempts/7.103.375bytes/0newOCR; legacyEPShard-stop giữ nguyên.
- [Report/run artifacts](artifacts/reports/financial-cafef-pilot5-execution-v1/report-v2.md), [runbook](docs/crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md).48targeted tests, compile/smoke,29independent Decimal checks/158unique field comparisons/replay/resumePASS. Full421tests420PASS/1pre-existingM2-PREP docs hasherror; không sửa assertion hoặc frozen evidence.
- Active pointers chuyển executionPARTIAL; cohort50baseline32/300 và financial/research/cluster gatesfalse giữ nguyên. Không tự mở50/100.

# Chưa phát hành — Financial pilot5 execution handoff v2 (2026-10-18)

- Viết [report tổng hợp hiện tại](artifacts/reports/financial-cafef-pilot5-handoff-v2/report.md), [plan thực thi mới](docs/crawl/FINANCIAL_CAFEF_PILOT5_EXECUTION_PLAN_V2.md) và planningJSON cho BRC/FPT/MWG/GMD/VNM; thay active handoff12mã, giữ original plan/config/evidence bất biến.
- Goal5×6=30primary recomputed+checked cells EPS/PE/PB/F/M/Z,3complete workflows chỉ checkpoint; provider-only/status rows/report không thay numerical goal. Future agent triển khai và thực hiện toànP0–P5 tới goal hoặc evidenced hard blocker, giao runnerPowerShell/test/replay/resume/runbook.
- Đưa findings mới vào contract: dedicated APIs/disclosure, exact date/file/vintage, BRCdebt-row mismatch, LCTTper-group headers, mixedPDF/notes/units và cache reuse. Annual trước, TTM extension; cap5mã/16PDF/400OCR/6hnetwork, không reset oldcampaign hoặc mở50/100/cluster.
- Cập nhật active pointers/START HERE/status/crawl index/DECISIONS và offline handoffverifier. Lượt này chỉ lậpplan,0newnetwork/OCR/metrics, baseline32/300/gatesfalse giữ nguyên.

# Chưa phát hành — BRC deep document/UI audit (2026-10-18)

- Computer-use5nhóm Tài liệu192links, lọcBCTC/BCTN2025,5pages disclosureBRC92records;92/92 exactURL/title/datejoins. Kiểm lại6financial tabs/annual modes, loaded owners và actual insider history.
- Tải6PDF/215pages/52.318.132bytes, render/visual selected notes;51discovery candidates cóSHA/page/unit. Tìm được EPS numerator/WA, owned-PPEdepreciation, no-capital-change/treasury disclosure và supportingassets2023; nhận diện BCTN mixed text/scanned statements.
- Xác nhận provider annual2025 debt displayed-row mismatch1,18tỷ vsPDF24,14tỷ; ghi quarantine/QA recommendation, chưa sửa bằng index shift. Giữ deadlink404 và exact observed browser viewer URL thành công riêng.
- [Report/worklog/field matrix](artifacts/reports/financial-cafef-brc-deep-audit-v1/report.md), inventory/candidates/offlineverifier, cập nhật trực tiếpCAFEF.md/index/status/decision/activepointer. Old source snapshot giữ hashpin lịch sử; không rewrite sealed reports/campaigns.
-13scripted CDN attempts kể cả6sandboxDNS errors;1browserdownloadtimeout tách riêng;0OCR/acceptedfacts/productionmetrics. Không đổi formulas/calculators/PIT/gates hoặc chạy cohort50.

# Chưa phát hành — CafeF rediscovery các tab BRC (2026-10-18)

- Cập nhật trực tiếp [CAFEF.md](docs/crawl/sources/CAFEF.md):6main/6financial tabs, endpoints v1/v2, modes/units, EPS share-days, disclosure/FileBCTC dates, news/ownership và matrix input cho6families.
- Lưu11successful HTML bodies và UI observations, inventory26page/loader/API entries; offline provider EPS/PE/PB/vốn hóa arithmetic khớp rounding. Phân biệt raw response/UI-only/script-only, current snapshots và historical evidence; loại incomplete loading captures khỏi numerical claims.
- [Report/worklog/verifier](artifacts/reports/financial-cafef-rediscovery-v2/report.md):13scripted attempts/1.528.364bytes,1redirect/1challenge; hard-stop giữ nguyên latch,12tasks chưa attempt. Raw BRC API/sector/history validation PARTIAL; FPT/QNP dùng verified cache correction, không giả là fresh requests.
-0PDF/OCR/acceptedmetrics mới, không sửa calculators/PIT/market pipeline; update docs/status/active pointers. Giữ original sealed plan/config/report; chưa scale50/100 hoặc mở financial cluster.

# Chưa phát hành — Đính chính discovery CafeF từ phản hồi UI (2026-10-18)

- Kiểm trực tiếp FPT ở màn Công bố thông tin:20records với `Id/LinkFile/CreateDate`; inline UI mapCreateDate→“Thời gian gửi”. FY2025audited ID/link khớp FileBCTC cache; giữ initial/reviewed dates riêng, không suy ngày từ filename hoặc ký PDF.
- Trace QNP FinancialAjax tab→GetReportLCTT và fetch JSON3groups có dữ liệu thật;3routes này chưa có trong crawler Python. Ghi nhận thiếu sót discovery/integration, thay nhận định chung “nguồn không có ngày/LCTT” bằng trạng thái source metadata/data chưa tích hợp.
- Thêm [source addendum](docs/crawl/sources/CAFEF_DISCLOSURE_AND_FINANCIAL_TABS.md) bắt buộc đọc trướcR1 plan12, [report/evidence](artifacts/reports/financial-cafef-disclosure-ui-correction-v1/report.md), cập nhật source/index/status/pointers. Original sealed plan/report không rewrite.
-5scripted requests/473.570bytes,0PDF/OCR/metrics mới. Chưa kiểm mọi mã/kỳ, chưa triển khai routes vào runtime, chưa equateCreateDate với issuer-first-public hoặc mở strict PIT/cluster.

# Chưa phát hành — Tổng hợp financial và plan kiểm chứng lại CafeF (2026-10-18)

- Viết [report tổng hợp](artifacts/reports/financial-replan-20261018-v1/report.md): quá trình discovery/detail/KBS benchmark/CafeF50/PDF/OCR/references/PIT, baseline32/300 trên10mã; phân biệt data tồn tại, parser/mapping gaps, code chưa hoàn thiện và rule acceptance.
- Thêm [plan giao agent](docs/crawl/FINANCIAL_CAFEF_REVALIDATION_PLAN.md) và planning JSON:12mã đại diện, goal, R0–R5, nguồn structured/attachment/ratios/external, field/metric QA, finite budgets, source verdict, outputs, Definition of Done và prompt copy giao agent.
- Theo yêu cầu owner, cho phép thiết kế PRACTICAL_FINANCIAL_V1: reported EPS/PE/PB, QA theo template, numerical work không bị chặn bởi publication, named proxies/partial outputs. Strict historical PIT/research/market-only không tự mở; runtime và frozen artifacts chưa thay.
- Cập nhật START HERE/CURRENT_STATUS/crawl guides/CafeF source note/DECISIONS/active plan pointers. Lượt này chỉ lập tài liệu và kiểm handoff, không crawl mới hoặc tăng coverage; planning JSON không phải executable crawler config.

# Chưa phát hành — Financial publication follow-up (2026-10-09)

- Chạy campaign issuer evidence7requests/28.096.954bytes, giữ nguyên expired frozen50 counters/deadline; không OCR hoặc numerical recomputation.
- GMD official FY2025/FY2024 PDFs khớp SHA cache2/2, post dates30/03/2026 và31/03/2025; tạo proposal evidence class ngày bài đăng, MANUAL_REVIEW_REQUIRED, chưa apply PIT hoặc mở gate.
- So hai MWG categories32records và VHC408PDFanchors:0new/changed/absent; phân biệt listing stability với chưa revalidate PDFbytes. DGC notice web screenshot access challenge được giữ observation, không bypass.
- [Report/worklog/self-review](artifacts/reports/financial-publication-followup-v1/report.md),21tests/compile/active workflow verifyPASS. Old publication stage43hashpins nguyên vẹn nhưng có2pre-existing bytecode extras ngoài manifest; không báo full inventoryPASS hoặc xóa evidence. Cohort32/300referencecells, production0.
- Cập nhật START HERE/CURRENT_STATUS/runbook/DECISIONS proposal và active report pointer; chưa periodic refresh/TTM/PE/PB/financial cluster.

# Chưa phát hành — Financial continuation, GMD recovery và cache handoff (2026-10-09)

- Thêm successor run/config trên `research/financial-data`, kế thừa cache/references/receipts/counters/OCR reservations và deadline của frozen50; không sửa code hoặc evidence V1.
- Explicit recovery đúng một failed transient GMD2024 PDF: tải17.522.145bytes, full OCR55pages, bổ sung2 visually reviewed facts trong input riêng; GMD F5/9/M−2,330411, EPS/Z giữ nguyên. Cohort32/300referencecells trên10/50mã, production0/gatesfalse.
- Thêm exact-hash extraction, per-PDF error status và one-shot crash/resume finalization. V2 inherited metadata gap được giữ evidence; sealed adapterV3 đọc hash từ reservation trong bộ nhớ. Handoff active `scripts/financial_resume.ps1`, không rewrite V2 sau freeze.
- [Report/log/self-review](artifacts/reports/financial-continuation50-v2/report.md):37targeted tests/52pins/independentDecimal/cache replay/doctor/workflow verify/synthetic smokePASS. Full-suite environment errors rechecked10testsPASS; M2-PREP historical docs hash mismatch đã tồn tại trước docs edits, full repository gate cònPARTIAL.
- Cập nhật runbook/START HERE/CURRENT_STATUS/DECISIONS/active pointer. Chưa implement periodic discovery, RAG, bulk TTM/valuation, financial history2020 hoặc financial cluster; kế thừa24h network deadline, không reset budgets.

# Chưa phát hành — Review DGC/GMD financial frozen50 (2026-10-09)

- Full OCR phần còn thiếu188trang của DGC2025/DGC2024/GMD2025 cache;3sandbox OCR failures giữ immutable, retry ngoài sandbox3/3PASS, không đổi execution policy/budget/config. Unique cache757pages, reservations651 gồm376mới;0network/PDFdownload mới.
- Tạo reviewed inputs riêng37DGC/35GMDfacts, exact-source/page/unit/locator và supporting FY2024 provenance. DGC EPS7.402/Z13,817568/F5/9/M−1,919528; GMD EPS3.839/Z9,305095, F/Mnull với blockersTA2023/owned-PPEdepreciation2024; GMD2024 terminal acquisition failure không reset/retry tự động.
- Giữ DGC qualified-audit và restatedFY2023TA metadata; CafeF oldTA2023 khác64.607.890.091VND, mechanical sensitivityF5→4. Provider50MATCH/21NO_PROVIDER/1VINTAGE_DIFFERENCE, canonicalnull; numerical reference không phải PIT/production acceptance.
- Cohort30/300FY2025referencecells(10%),10/50mã,EPS10/Z10/F5/M5/PE0/PB0; gates/production0. [Report/log/self-review](artifacts/reports/financial-dgc-gmd-review-v1/report.md),125pins/independentDecimal/23tests/compile/fullworkflowverifyPASS. Cập nhật START HERE/CURRENT_STATUS/runbook/retention pointer; branch `research/financial-data`, frozenV1 branch metadata giữ nguyên. Không đổi plan/market-only/runtime/methodology hoặc mở100/financialcluster.

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
- Xuất phân tích theo mã/kỳ/task,900 strict task rows, report/log và source pins;0 accepted facts/0 task-ready/0cluster eligible. Next: quý/history contract, numeric templates/PIT/events và ledger/verify IO trước trial100. [Report — archived](artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip).

# Chưa phát hành — Flow financial trial50 bàn giao PowerShell (2026-10-06)

- Thêm trial CLI/PowerShell doctor/plan/run/verify/feedback và executable config riêng, pin50 market members/nhánh CafeF; giữ runner pilot10 và market-only protocol.
- Global HTTPS ledger, request/attempt/byte/page reservations,4giờ deadline, epoch registry/OS lock và hard-stop latch giữ qua waves/resume. Annual targets2021–2025, quarter2024–2025, strict task checklist2023–2025; source header/sector/duplicate periods fail-closed.
- Thêm gap-driven history/PDF sample12 đa dạng templates, worker text bounded timeout, wire/field coverage,900 task-input rows và compact feedback ZIP. Scan pages vào review queue, không tự generalize OCR hoặc numeric acceptance.
- 13 new tests PASS qua targeted/full logs; full326/327, còn frozen M2-PREP DECISIONS checksum đã biết. Pilot14/14, PowerShell offline run/verify/feedback, cached exact-PDF73pages và compile/smoke PASS. Live50 chưa chạy; user chạy local và gửi feedback. [Report/log — archived](artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip), [runbook](docs/crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md).

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
- Pilot readiness v11 đạt 150/1.176 verified cells; date overlay v5 có 135 date references; task readiness v7 vẫn 0/120 production-ready. Report và kiểm chứng: [financial-revision-fscore-v1 — archived](artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip).

# Chưa phát hành — FPT executable reference flow (2026-10-03)

- Thêm coordinate OCR table parser, exact-PDF template config, EPS/EM-Z Decimal calculators và offline orchestration CLI từ immutable cache tới QA/PIT/provenance/results.
- FPT2024/25: 22 numeric cells match reviewed evidence, bốn accounting bridges PASS, review queue zero. EPS gốc 2024/25 round 4.944/5.216 VND/share; EM Z reference 6,843186/7,106292.
- Giữ same-PDF inputs, fail-closed trước ngày khả dụng/mixed-vintage/unproved dilution/denominator invalid. Revision alert chặn EPS2024 cũ từ 20/03/2026 vì comparative EPS 4.292 chưa mapped.
- Latest reference_flow_v6: 5 QA-pass executions (4 unique task-years), 6 unavailable, 1 revision blocked, 24 F/M/PE/PB outside reference calculators. Replay v5/v6 deterministic; không thêm value coverage hoặc mở feature/research gate.
- Chín targeted tests/compile/synthetic smoke PASS; full suite 226/227 PASS, lỗi frozen M2-PREP DECISIONS checksum đã biết. Reference registry riêng cluster_eligible=false, market default registry không thay đổi. [Report — archived](artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip). FIN-D2 reference slice đạt trong scope; tổng FIN-D2 PARTIAL, scale chưa mở.

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

# Chưa phát hành — Chia sẻ dashboard qua Git, dữ liệu gửi riêng (2026-10-23)

- Thêm hướng dẫn cài extra dashboard, đặt ba file C8 đúng đường dẫn và verify offline.
- Giữ nguyên bytes bộ handoff bằng `.gitattributes -text` để bảo toàn checksum.
- Pin pandas 2.3.3 trong extra dashboard cho API Styler đang dùng; không đổi model/data.

# Chưa phát hành — Trục cố định liquidity/beta và overview-only (2026-10-23)

- X=liquidity_21 symlog, Y=beta_126 linear cố định toàn dashboard; giữ raw values,
  zero/outliers, nhãn X theo tỷ VND và tooltip VND gốc.
- Thêm viền/focus ring cho ô tìm kiếm; bỏ Stock Detail và bộ chọn chế độ xem.
- Migrate assertions về ticker/source/missing sang member table; giữ query
  offline và mở rộng kiểm tra trục cố định/zero/missing của hai tọa độ mới.

# Chưa phát hành — Thiết kế lại Market dashboard theo ảnh owner (2026-10-23)

- Bộ lọc trái, thẻ tổng quan, scatter mom_252/mom_63, profile và members panels;
  toàn bộ số liệu lấy đúng snapshot, giữ raw outliers và hai nhóm M2 hiện hành.
- Tên nhóm theo liquidity profile: Dẫn đầu thanh khoản / Đại trà, có fallback
  trung tính; không sửa scientific labels hoặc thêm ranking.
- Members có company names từ C8 securities checksummed, đủ 8 ticker features,
  search và pagination 10/25/50/100 rows; giữ Stock Detail/provenance/missing states.
- Thêm native light theme, không thêm dependency; migrate assertions cũ và mở
  rộng targeted tests lên 21.

# Chưa phát hành — M3-B Market-only Streamlit (2026-10-23)

- Thêm entry point duy nhất `m3_dashboard.py`: Overview, members và Stock Detail;
  selector chỉ gồm 84 snapshot từ handoff hiện hành, không dùng bộ legacy 2026.
- Kiểm chứng handoff hashes, C8/development/holdout lineage, schema, exact unique
  join và profile size/ratio. Missing giữ trạng thái rõ ràng, không zero-fill.
- Ticker features lấy trực tiếp JSONL; cluster profiles lấy CSV riêng. Không gọi
  model hoặc tính lại features/clustering, không Financial/ranking/backtest.
- Thêm extra `dashboard` pin Streamlit 1.66.1 và 18 targeted tests, bao gồm UI
  AppTest/dữ liệu thật/cache/missing states; hướng dẫn Windows ở CURRENT_STATUS.
- Giữ nguyên toàn bộ official artifacts và local changes có trước stage này.

# Chưa phát hành — Kết quả mới và báo cáo đầy đủ Nhiệm vụ 11 (2026-10-22)

- Ghi nhận lần chạy thật complete: 24 tháng 2024–2025, 30.155 assignments,
  24 model, 23 cặp thời gian; KMeans Baseline/sklearn/K=2 trên nguồn C8 ab1a34a8….
- Viết lại báo cáo đúng tên chuẩn theo mẫu A/B/C cũ, cập nhật toàn bộ bảng và
  diễn giải bằng kết quả mới: Silhouette median 0,949324, delta +0,008487,
  ARI median 0,843260; giữ cảnh báo Balance/thanh khoản và giới hạn đầu tư.
- Lưu bản xuất tự động gốc trong artifact, cập nhật report checksum/revision;
  không refit hoặc sửa model, numerical artifacts, input, code và thời điểm chạy.
- Cập nhật CURRENT STATUS/START HERE; Nhiệm vụ 12 và M3 thực hiện riêng.

# Chưa phát hành — Chuẩn bị nhiệm vụ 11 trên dữ liệu mới (2026-10-22)

- Tạo notebook/config/runner Task 11 tên chuẩn, chỉ KMeans Baseline/sklearn/K=2,
  24 tháng 2024–2025; không nạp model hoặc kết quả holdout đã xóa trước đó.
- Khóa chín development inputs hiện hành và kiểm chứng 60 model trước khi mở
  holdout; giữ nguyên tham số, boundary, universe và pipeline đã freeze.
- Synthetic tests kiểm tra gate, future availability, skip/gap reset, one-use
  rerun và tamper detection. Chưa fit hoặc xuất kết quả holdout thật.
- Cập nhật kế hoạch/START HERE và giữ generator Task 13 lịch sử chặn rõ ràng
  để không trộn gói 22 snapshot cũ với workflow 60+24 hiện tại.

# Chưa phát hành — Tên chuẩn PCA và xóa Task 11 (2026-10-22)

- Đổi tên toàn bộ notebook/config/artifacts/báo cáo PCA nhiệm vụ 6–9 không thêm
  hậu tố phiên bản; cập nhật kế hoạch, notebook 10 và các bài kiểm chứng artifacts.
- Đồng bộ checksum đường dẫn/config/freeze/model metadata; sửa checksum báo cáo
  7–9, ghi provenance đổi tên, giữ nguyên số liệu và không huấn luyện lại.
- Theo yêu cầu mới nhất, xóa hết Task 11 thay vì thay thế bản cũ: notebook,
  config, runner/helpers, tests riêng, models, artifacts và báo cáo các phiên bản.
- Audit 12 và generator 13 dừng trước khi ghi output nếu thiếu Task 11; giữ
  dữ liệu C8 và kết quả riêng của các phương án khác.

# Chưa phát hành — Kết quả và báo cáo Nhiệm vụ 11 V2 (2026-10-22)

- Holdout đã hoàn tất: 24 snapshot 2024–2025, 28.110 assignments, 24 model,
  23 cặp tháng; chỉ sklearn KMeans/K=2, không skip hoặc chạy comparator.
- Mở rộng báo cáo Nhiệm vụ 11 V2 theo mẫu A/B/C: quality/generalization gap,
  temporal/universe, hồ sơ mean/median, biểu đồ 84 mốc và giới hạn diễn giải.
- Giữ bản xuất tự động gốc trong artifact; làm mới checksum báo cáo và ghi
  nhận revision. Model/numerical outputs/input/code giữ nguyên, không refit.

# Chưa phát hành — Chuẩn bị Nhiệm vụ 11 V2 (2026-10-22)

- Thêm notebook/config/runner V2 cho 24 snapshot holdout 2024–2025, giữ duy nhất
  sklearn KMeans/K=2 đã freeze, Robust Scaling riêng tháng, ngưỡng eligibility 100.
- Gate pin development inputs và kiểm chứng 60 selected models trước đọc holdout;
  khôi phục đúng byte LF theo hash cũ và Git attributes để tránh lỗi checkout Windows.
- Xuất V2 riêng, bảy bước, gap/profile diagnostics, biểu đồ 84 mốc, source snapshot;
  rerun verify-only, từ chối run dở/tamper/code/input thay đổi. Giữ runner V1 lịch sử.
- Chỉ preflight và test dữ liệu giả trong lần chuẩn bị; chưa chạy holdout thật.

# Chưa phát hành — Báo cáo PCA V2 đầy đủ và đồng bộ Git (2026-10-22)

- Thay bốn báo cáo chính PCA + K-Means Nhiệm vụ 6–9 bằng bản đầy đủ theo mẫu
  A/B/C, giữ đường dẫn `_v2.md`; cập nhật trạng thái Task 10 V2 đã freeze.
- Làm mới checksum báo cáo và tham chiếu manifest phụ thuộc; giữ nguyên model,
  numerical artifacts, biểu đồ và frozen Task 10 outputs. Bản trước giữ ở Git history.
- Notebook đánh giá 7–9 tái sử dụng bản đầy đủ sau kiểm chứng checksum để tránh
  ghi đè bằng bản tóm tắt. Đồng bộ các commit KMeans/Task 10 mới từ nhánh GitHub.

# Chưa phát hành — M2 Task 10 V2: sanity warning và final method selection (2026-10-21)

- Làm rõ chính sách sanity Task 10: cụm dưới 5 mã là cảnh báo bắt buộc; chỉ loại phương án khi cảnh báo riêng biệt hoặc có bằng chứng phân mảnh không thể diễn giải. Khi cả ba phương án cùng có cảnh báo, ghi `WARNING` và tiếp tục so sánh evidence-first.
- Chạy lại Task 10 trên 60 snapshot V2; PCA + KMeans dẫn Silhouette nhưng KMeans Baseline được freeze theo Occam do chênh lệch dưới 0,03. Decision trace giữ số snapshot/cụm nhỏ và các phương án đối chứng.

# Chưa phát hành — K-Means Nhiệm vụ 4, 7, 8 và 9 trên C8 v2 (2026-10-21)

- Fit lại 60 development snapshot bằng scikit-learn K-Means với Global K=2 đã khóa; giữ nguyên Nhiệm vụ 1–3 và các nhánh Ward/PCA.
- Đặt output đúng kế hoạch: `M2/artifacts/m2-task4-kmeans-baseline-v1/`, 60 model/scaler ở `M2/models/kmeans/`, notebook và báo cáo Nhiệm vụ 4 đúng tên.
- Cập nhật K-Means Nhiệm vụ 7: `quality_summary.csv` 5 dòng và 5 biểu đồ từ 60 snapshot; Nhiệm vụ 9: 59 cặp tháng, 236 transitions, 944 drift rows, 2 biểu đồ và báo cáo đúng tên.
- Nhiệm vụ 8 K-Means hiển thị ba bảng 60 tháng trong notebook, xuất radar, heatmap và báo cáo đúng tên. Đồng bộ hồ sơ cụm, thành viên và scaler reference K-Means 60 tháng cho các bước sau; manifest Task 4 ghi hash nguồn C8. Đưa code thực thi vào notebook và dọn CSV/script/slide phụ ngoài bộ bàn giao. Đã đối chiếu offline schema, checksum, metrics, báo cáo và biểu đồ. Không chạy Nhiệm vụ 10 trở đi trong lần cập nhật này.
- Chuẩn hóa newline LF của artifact/model K-Means để checksum giữ nguyên sau Git checkout; khai báo `scikit-learn` và `ipywidgets` trong research dependencies cho notebook 4/8.

# Chưa phát hành — PCA + K-Means dữ liệu mới V2 (2026-10-21)

- Đưa lên Git bộ PCA + K-Means Nhiệm vụ 6–9 đã chạy trên 60 tháng development
  2019–2023, 29.907 assignments, Global K=2 và PCA 2 chiều, kèm notebook, config,
  60 models, báo cáo, bằng chứng freeze và checksum.
- Theo yêu cầu owner, loại bốn notebook PCA cũ, config `m2_task6_pca.json`,
  `m2-task6-pca-kmeans-v1` và `m2-evaluation-pca-kmeans` khỏi active tree.
  Git history giữ bản cũ; không xóa lịch sử hoặc thay dữ liệu nguồn C8.
- Chuyển đường dẫn kế hoạch và regression tests sang V2; bảo toàn byte artifact
  qua Git để checksum không đổi khi checkout trên Windows.
- Task 10 yêu cầu cùng development dates và nguồn dữ liệu trước khi so sánh;
  lần chạy mới dùng output V2. Task 10–13 lịch sử không được coi là kết quả V2;
  audit Task 12 lịch sử dừng rõ ràng nếu bộ PCA cũ không còn trong checkout.

# Chưa phát hành — M2 Task 11 Final Holdout (2026-10-04)

- Thêm freeze-gated offline runner `experiments/final_holdout.py`, config và notebook
  11 bảy bước; đọc C8 immutable Feature Store 1.6.0, chỉ KMeans winner/K=2 với tham số
  từ 15 selected models đã verify. Không sửa Task 10, C8 hoặc fit comparator.
- Thực thi 7 holdout tháng 02–08/2026: 4.624 assignments, 14 profiles, 7 models và
  6 cặp tháng; xuất quality/gap/temporal/transitions/drift/scalers, chart 22 mốc,
  source snapshot, checksummed manifest và report. Reset chuỗi tại gap/skip.
- Rerun verify-only, không refit/retune; fail-closed khi frozen inputs/checksum đổi.
  Thêm 11 tests với fixtures và kiểm chứng độc lập saved labels/scalers/transitions;
  targeted tests, compile và synthetic smoke qua. Task 12/backtest chưa thực hiện.

# Chưa phát hành — PCA replacement v2 → v1 theo yêu cầu owner (2026-10-04)

- Thay bộ PCA v1 cũ bằng kết quả sửa v2, dùng `m2-task6-pca-kmeans-v1`,
  `m2-evaluation-pca-kmeans` và `M2/models/pca_kmeans`; giữ nguyên số liệu/model.
- Cập nhật notebook 06–09, config, tests, report links và checksum manifest.
  Notebook 06 tự kiểm chứng bộ hiện hành, không cần artifacts legacy đã loại bỏ.
- Bỏ report Task 6 tên legacy, giữ report đúng tên trong kế hoạch. Ghi rõ
  `storage_migration` và lineage gốc; bản sao khôi phục đã kiểm tra checksum
  nằm ngoài active artifacts. Không chỉnh sửa hoặc chạy nhiệm vụ 10.

# Chưa phát hành — PCA notebook nhiệm vụ 6–9 (2026-10-04)

- Sửa root/import của bốn notebook PCA + K-Means, chạy độc lập từ `M2/notebooks`
  và lưu output đầy đủ. Giữ fitted models/scaler/K=2/số chiều 4; không refit, đọc holdout
  hoặc mở nhiệm vụ 10. Bảng development chứng minh fixed count=4 đủ ≥90% ở mọi tháng.
- Xuất bộ `m2-task6-pca-kmeans-v2`/`m2-evaluation-pca-kmeans-v2` có lineage/checksum;
  giữ v1 nguyên trạng. Bổ sung PC1–PC4, PCA diagnostics/loadings, profile 13 cột,
  quality summary 5×7, bảng Mean/Median/đối đầu/chuỗi thời gian và widget snapshot.
- Sửa transitions dùng aligned IDs xuyên chuỗi và drift có tâm gốc thật hai tháng;
  thêm kiểm tra chain/schema/counts/checksum. Kết luận và reports lấy số liệu chạy thực tế,
  tách migration/entry-exit khỏi chi phí/turnover danh mục. Radar giới hạn hiển thị
  ±3 có đánh dấu ngoài biên; heatmap 2×8 giữ annotation Z thật.
- Runner đọc PCA n_components từ config; protocol yêu cầu số chiều frozen hợp lệ,
  từ chối reduction mâu thuẫn. Thêm regression tests cho cấu hình và artifacts;
  cô lập model output trong test runner để không sửa model thật khi chạy tests.
- Experiment writer từ chối thư mục output đã tồn tại, bảo vệ bộ v1/v2 khỏi
  việc chạy runner đè lên evidence đã freeze.

# Chưa phát hành — FIN-PIT-2-R1 OCR remediation (2026-10-01)

- Thêm selective local OCR runner dùng Tesseract `v5.4.0.20240606`, preflight 5 trạng
  thái, page-level provenance/bounding boxes/confidence, immutable raw-hash checks,
  numeric ambiguity fail-closed, semantic re-extraction và 15 targeted contract tests.
- OCR đúng 26 scan/mixed documents và 209 pages; 205 pages đạt quality gate, 4 pages
  `LOW_CONFIDENCE` không được semantic-promote. Linkage verified tăng 6→27,
  ambiguous giảm 34→4; 9 scope conflicts mới được giữ nguyên thay vì ép match.
- Gate `PARTIAL`: quarantine 29→26, semantic-ready reports 3→6, fact candidates
  220→242 nhưng semantic-ready facts giữ 216; 7 revision groups vẫn `UNKNOWN`, Q2/Q3
  duration chưa resolve. Preserve 4 `A_EXACT_TIMESTAMP`, 28 `B_OFFICIAL_DATE_D1`,
  canonical/features bằng 0 và không mở FIN-PIT-3.

# Chưa phát hành — FIN-PIT-2 semantic extraction (2026-10-01)

- Thêm offline FIN-PIT-2 extractor/verifier và 13 contract tests cho document linkage,
  statement/period/scope/assurance/unit semantics, taxonomy candidates, provenance,
  revision `UNKNOWN`, R5 timing preservation và no-canonical/no-feature boundary.
- Sinh artifact `fin-pit-2-semantic-extraction-v1` từ immutable FIN-PIT-1 evidence:
  32 documents, 40 linkages, 4 primary reports, 220 fact candidates, 29 quarantine,
  0 conflicts; gate `PARTIAL` vì phần lớn PDF scan không có usable text layer và OCR
  engine không khả dụng.
- Preserve 4 `A_EXACT_TIMESTAMP` và 28 report-document candidates dùng
  `B_OFFICIAL_DATE_D1`; không thay methodology R5, không final-promote taxonomy/revision,
  không ghi canonical rows và không bật financial features.

# Chưa phát hành — M2 Ward tasks 7–9 aligned with updated plan (2026-10-03)

- Viết lại ba notebook Ward theo hợp đồng M2 mới, mỗi nhiệm vụ nằm trọn trong một
  file `.ipynb`; không dùng helper `.py`, không fit lại Ward/scaler và không đọc M1
  hoặc final holdout.
- Nhiệm vụ 7 chỉ đọc `diagnostics.csv`, lọc 15 dòng Global K=2, xuất duy nhất
  `quality_summary.csv`, hiển thị hai bảng chuẩn và năm biểu đồ có đường median.
- Nhiệm vụ 8 chuẩn hóa `m2-evaluation-ward/cluster_profiles.csv` về đúng schema cố
  định 13 cột của kế hoạch, xuất ba bảng chuẩn, bảng Robust Z, `radar_chart.png` và
  `heatmap.png`; metadata gốc vẫn được giữ trong artifact Task 5, scaler JSON chỉ
  dùng để đổi thang, clipping [-3, 3] chỉ dùng khi vẽ và widget state được lưu đồng
  bộ để notebook render lại không lỗi.
- Nhiệm vụ 9 đọc trực tiếp ba CSV phẳng trong `m2-evaluation-ward`, xuất bốn bảng
  chuẩn cùng `temporal_trends.png` và `transition_heatmap.png`; bổ sung reset gap,
  năm cặp ARI thấp và đối chiếu bối cảnh thị trường có nguồn, không suy diễn nhân quả.
- Cả ba notebook tự ghi báo cáo Markdown tương ứng; migration được giữ là proxy cho
  áp lực đổi thành viên, không bị gọi là portfolio turnover có trọng số.
- Xóa các artifact reporting cũ ngoài hợp đồng, chuẩn hóa tên ba báo cáo với hậu tố
  `Ward`, chạy sạch 14/14 code cells và lưu output; kiểm tra schema/row count/ảnh và
  đối chiếu số liệu lõi với artifact Task 5 đều PASS.

# Chưa phát hành — Post-M1 documentation alignment (2026-09-26)

- Hoàn tất M2 Nhiệm vụ 3: chạy 105 lượt K-Means trên 15 development snapshots; phê duyệt chính thức Global K = 2 (ADR-049) với median Silhouette 0.7557 và Davies-Bouldin 0.5219; ghi nhận cấu hình k: 2 và chuyển stage sang M2_TASK_3_GLOBAL_K_FROZEN, sẵn sàng thực thi Nhiệm vụ 4.
- Hoàn tất M2 Nhiệm vụ 2: thêm C8 market-only checksum adapter, snapshot-local eligibility, fail-closed 8-feature validation, minimum-120 skip và common clustering interface integration; không chạy Global K/holdout/backtest.
- Thêm 5 nhóm test runner bắt buộc: 142 mã tại `2023-11-30`, terminal-universe guard, 8 finite features, below-minimum skip và `build_snapshot` integration.
- Hoàn tất M2 Nhiệm vụ 1: tạo `m2_market_only_v1.json` với development/holdout snapshots, minimum eligibility, 8 features, fail-closed missing, no clipping, Robust Scaling per-snapshot, `k=2..8`, Global K selection firewall và comparator-only PCA.
- Mở rộng protocol validator bằng strict market-only scope trong khi giữ backward compatibility với config mẫu; thêm fail-closed tests cho feature, portfolio firewall, time boundary và preprocessing.
- Giữ M2-PREP artifact bất biến; verifier có thể đối chiếu input blob tại recorded parent commit khi active source đã tiến hóa.
- Phục hồi local immutable C5 artifact từ upstream reproducibility package sau khi xác minh manifest hash và 20/20 output hashes; full repository gate đạt 173/173 tests. Recovery WIP untracked được backup ngoài active test discovery, không khôi phục stack superseded.
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


## 2026-10-20 — Financial acquisition first

Owner ưu tiên API collection theo batch và defer field review. Thêm successor acquisition-only30 (tổng50), shared registry assignment, kế thừa counters/deadline/source boundaries; không sửa frozen runners hoặc metrics. Thêm report/JSONL review backlog có field/period/source evidence; dừng PDF/OCR mới.14targeted/compile/synthetic PASS; numeric/PIT/M3 chưa promote.


## 2026-10-20 — QA50 và acquisition tổng100

Thêm offlineQA cóexacttemplatefamilyproof/UNKNOWNheld; đã chạy385.792candidatecells, reportfield-level13.802reviewitems deferred. Boundedgenericbatchrunner1..100 giữ source limits, parent counters/deadlines/cache/hash/locks và numeric/PIT gates đóng; assignmentadditional50 loại50previous.32targeted/compile/syntheticPASS; knownfullrepositorygate limitation giữ nguyên.


## 2026-10-21 — Xếp batch financial additional100

Batch100 đã terminal; additional50 có 4.350 requests/464.021 candidate observations/0 parser errors. Tạo assignment additional100 không trùng, dùng lại generic runner. Pipeline local chờ QA+verify, tạo report/gate, replay rồi mới mở network; không restart tự động khi lỗi và không tắt máy. Registry/counters/deadlines/source boundaries/financial gates giữ nguyên; 16 targeted tests và preflight assignment/script PASS.


## 2026-10-21 — Rate successor 1 giây/request

Owner yêu cầu tăng tốc. Thêm successor chuyển batch200 tại zero-attempt reservation, tái dùng raw/receipts/counters/cache epoch/deadline; spacing2→1s, concurrency vẫn1. Không sửa frozen runner cũ, không retry request đã attempt, giữ401/403/429/challenge hard-stop.23targeted cases/compile/synthetic PASS; checkpoint replay trước resume.


## 2026-10-21 — Acquisition200 terminal, nối additional100

Chốt additional100:9.266responses/1.007.884cells/0parsererrors. Thêm streaming exact raw→candidate replay và field/coverage quarantine report; semantic accounting/PDF/PIT review tiếp tục deferred. Fresh boundedrunner rate1 giữ code/config cũ; assignmentnew100 không trùng200. Local pipeline chờ gate rồi zero-requestverify/network, không restart hoặc tắt máy.24targeted/compile/synthetic/preflight PASS.


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


## 2026-10-24 — Dual clusters A/B và combined reference C (owner approved)

Owner yêu cầu giữ hai bộ cụm riêng, có bảng đối chiếu, và thêm model kết hợp.
Unified Project Plan mục16 có A/B/C; historical C vẫn cần PIT. Owner đã duyệt
cấu hình reference C cụ thể: 8 market +6 core financial ratios, cohort giao cuối
mỗi năm2019–2025, z-score từng năm trên cohort chung, blockweightsmarket/financial
50/50 theo sqrt(0.5/p), KMeans k3/seed42/n_init20/max_iter300, no clipping/PCA/imputation.
Không sửa A/B, không chọn bằng returns, không claim holdout mới. Same-year financial
có thể công bố sauDecember: EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT; historical/research/M3
vẫn false. Thí nghiệm riêng có manifest/config/code/input pins, chất lượng review độc lập.
Protocol: configs/experiments/combined_reference_v1.json; chỉ chạy khi owner_approvalAPPROVED.


### Execution58 verification và phạm vi còn lại

27 targeted tests PASS (8tests mới + financial/integration/clustering regression),
compileall PASS; synthetic smoke `run-20261024T021711Z-30619c75` PASS. Independent
C review kiểm lại scalers, weights, nearest-centroid, inertia, raw profile means và
centroids cho5593assignments/7models PASS. RerunC giữ nguyên bytes và timestamps
của numericaloutputs, khôngrefit; comparison idempotent và coverage9213/5593 PASS.
C kế thừa financialfull10fixedcohort, còn selection/survivorshipbias. Sourcefacts
không tự accepted, khôngclaimPIT hoặcnewholdout. Fullsuitegate vẫn PARTIAL;
lượtstage58 có log `.tmp/dual-combined-full-suite.log` và summaryJSON cùngprefix.


### Execution58 final gate — 24/10/2026

Fullsuite timeout 240.1giây, ít nhất254testlines kết thúcok,
không FAIL/ERROR trước timeout. Cuối log ở financial_crawl_trial fixture50;
không diễn giải timeout thành suitePASS hoặc xác định nguyên nhân treo.
Targeted27tests/compile/smoke/independentCverification đềuPASS. A/Bsourceartifacts giữnguyên.
Execution58 đã hoàn tất chạy và đối chiếu ở phạm vi descriptive reference; quality
REVIEW_REQUIRED và PIT/M3gates false. Không tự thay preprocessing sau kết quả.
