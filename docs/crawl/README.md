# CafeF data collection

Tra cứu required financial inputs và cách tính:
[Handbook chỉ số/data](../research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md).

## Financial readiness tự chạy cho frozen50 — 08/10/2026

[Hướng dẫn đầy đủ](FINANCIAL_READINESS_USER_GUIDE.md), [report bàn giao](../../artifacts/reports/financial-user-workflow50-v2/report.md).
Dùng `scripts/financial_readiness.ps1` hoặc `.py`; bắt đầu doctor → plan → acquire → extract → audit/review/verify. Default Run mới `data/financial/user_workflow50_v1`; không dùng QA Run để thay lượt user.

## Kiểm tra scale financial frozen50 — 08/10/2026

[Report/log](../../artifacts/reports/financial-scale-validation50-v1/report.md),
[all50 assessment](../../artifacts/reports/financial-scale-validation50-v1/per-symbol.csv),
[review config](../../configs/data/financial_scale_review_v1.json).
Probe kiểm listing/candidates toàn50, PDF mẫu và4 mã mới end-to-end đến reference
arithmetic. Review semantic/notes/date còn cần người kiểm; không tự mở feature gate.

```powershell
# Kiểm data/code/manifests đã chạy, không request network hoặc OCR lại.
& .venv\Scripts\python.exe scripts\verify_financial_scale.py
# Replay numeric/OCR QA offline; output phải là root mới.
& .venv\Scripts\python.exe scripts\review_financial_scale.py `
  --config configs/data/financial_scale_review_v1.json `
  --output data/financial/scale_review_user_v1
```

Acquisition entrypoint: `scripts/probe_financial_scale.py acquire --output <new-root>`;
chỉ thêm `--execute-network` khi chủ động chạy nguồn thật. Config frozen v1 giữ50
membership, max90logical/100attempts/20PDFattempts/250MB; explicit cache từ sealed
batchflow. Worker/analyzer: `scripts/analyze_financial_scale.py --collection <root>
--output <new-root>`. OCR: `scripts/probe_financial_ocr.py --config <versioned-config>
--output <new-root>`, cần Poppler `pdftoppm` trênPATH và Windows.Media.Ocr.
OCR config hiện tại pin **các PDF đã thu thập**, không tự áp dụng cho một collection
mới; phải tạo config mới với exact hashes/page ranges đã kiểm. Review config pin
ảnh/OCR/statement layout/note values và proof ngày công bố; không reuse theo ticker
hay filename nếu PDF hash khác. New probe chưa tích hợp crash-resume production.
Python môi trường này cần execution ngoài sandbox Windows để launcher `.venv`
khởi động; pipeline runtime không bị thiếumatplotlib. Fulltest bằng runtime dự phòng
thiếumatplotlib được ghi riêng, kết quả cuối dùng project `.venv`.

## Nối trial50 với reviewed references — 08/10/2026

[Report/log](../../artifacts/reports/cafef-financial-reviewed-integration-v1/report.md)
và [runtime config](../../configs/data/financial_trial_integration_v1.json).
Flow offline nối sealed CafeF candidates với reviewed PDF facts và existing adapters;
không copy ngày công bố sang HTML theo ticker/year. DATE_ONLY dùng phiên exchange
quan sát đầu tiên sau ngày công bố; không cần suy giờ. Ledger tách annual, TTM và
book/equity-event basis. FPT/ACV có18 reference values,15 trong900 ô annual;
ACV auxiliary dates/TTM và acceptance toàn50 còn thiếu. VNM/PVS controls riêng.

```powershell
# Kiểm lượt đã thực hiện; không cần crawl lại.
.venv\Scripts\python.exe scripts\integrate_financial_trial.py verify --run data/financial/cafef_trial50_reviewed_20261008_v1
# Tái lập offline nếu cần: output phải mới, không overwrite sealed root.
.venv\Scripts\python.exe scripts\integrate_financial_trial.py run --output data/financial/cafef_trial50_reviewed_user_v1
```

Đọc `assessment.csv`, `per-symbol.csv`, `reference-ledger.json` và
`artifacts/reports/cafef-financial-reviewed-integration-v1/next-review-plan.json`.
Missing candidate khác chưa-reviewed input; reference arithmetic khác strict
production acceptance.48 mã chưa có reviewed adapters. Ưu tiên notes/publication
wave PHP/VCS/VEA/PAN và sector templates; integration không tự execute wave này.
Active retention pointer `financial_active_integration_v1.json` giữ sealed integration
và transitive parents; cập nhật active pointer khi bàn giao run/version mới.

## CafeF-first financial trial50 active — 08/10/2026

[Report/log](../../artifacts/reports/cafef-financial-trial50-v1/report.md),
[runbook PowerShell](FINANCIAL_TRIAL_50_USER_GUIDE.md#flow-cafef-first-active--08102026)
và [runtime config](../../configs/data/cafef_financial_trial50_v1.json).
Active runner `crawl_cafef_financial.ps1`: doctor/plan/run/verify/feedback; raw nguồn
CafeF detail HTML, không tự fallback KBS. Mẫu đúng50 đã freeze, không thêm VNM/PVS
pilot vào market membership. Base600 +≤120 gap requests,≤900 attempts/300MB/2h,
spacing≥2s, global access latch và latest-parent resume. Journal một JSONL có hash
chain/fsync, rawSHA/cache pointer; không per-chunk folders hoặc copy raw parent.

Lượt hiện có `data/financial/cafef_trial50_20261008_v1`, đọc report/verify thay fresh
rerun cùng epoch. Không tải PDF/OCR trong structured stage; exact notes/units/scope/
PIT/revisions/share-events/sector gaps nằm trong review queue. Gate financial cluster
vẫnfalse và chưa tự mở100 mã. Retention registry/dependencies giữ active lineage.

Latest financial review08/10: [benchmark/cleanup report](../../artifacts/reports/financial-source-benchmark-v1/report.md).
Recommendation engineering hiện tại là CafeF detail chính, KBS diagnostic pending
period/value QA. Runner trial50 bên dưới là legacy KBS flow; chưa tự chuyển nguồn.

## Financial source benchmark và retention — 08/10/2026

[Config benchmark](../../configs/data/financial_source_benchmark_v1.json) pin9 mã,
target periods và budgets; [selection recommendation](../../configs/data/financial_source_selection_v1.json)
giữ gates false. Từ project root, dùng Python project đã cài hoặc bundled Python:

```powershell
.venv\Scripts\python.exe scripts\benchmark_financial_sources.py --help
# Output phải mới; bỏ --execute-network để tạo planned artifact offline.
.venv\Scripts\python.exe scripts\benchmark_financial_sources.py --output data/financial/source_benchmark_next_v1 --execute-network
.venv\Scripts\python.exe scripts\analyze_financial_source_benchmark.py --run data/financial/source_benchmark_next_v1 --output artifacts/reports/source_benchmark_next_v1/analysis.json
```

Benchmark alternates provider cohorts, mặc định2giây/request, một attempt/URL,
450attempt/150MB/1giờ toàn lượt và3MB/response;401/403/429/challenge dừng toàn lượt.
Output mới không resume; đây là paired measurement, không thay trial scheduler.
Compact append-only `transport.jsonl` ghi reservation/hash chain; raw deduplicate
theo SHA256. Không tạo một file cho mỗi response chunk. CafeF số hiển thị và KBS
unit1000/per-share đều là QA hypotheses, không approved canonical conversion.
Coverage là **wire header presence**, không số kỳ đã đủ tính score/PIT.

Cold archive index tại
`artifacts/archives/financial-cleanup-20261008-v1/prune-plan.json`; mỗi record có
original root, file count/bytes, original manifest pin, archive path/SHA256. Reports
cũ còn local. Links raw thuộc roots đã archive sẽ hoạt động sau restore; không sửa
các immutable reports để đổi provenance. Ví dụ khôi phục exact trial50 để verify:

```powershell
.venv\Scripts\python.exe scripts\financial_retention.py restore --archive artifacts/archives/financial-cleanup-20261008-v1/crawl_50_live_20261007_v1.zip
```

Restore kiểm whole ZIP pin và từng member, tái tạo path/bytes/mtime gốc, từ chối
overwrite nếu root đã có. Sau restore, chạy verifier legacy theo runbook tương ứng;
closed epoch/deadline vẫn có hiệu lực. Không dùng ZIP feedback của user crawler để
thay cold archive vì feedback chỉ giữ subset evidence.

Retention cho lượt khác dùng tên mới và explicit inventory/plan/ready cùng nhau:

```powershell
.venv\Scripts\python.exe scripts\financial_retention.py inventory --inventory .tmp/financial-retention-next.json
.venv\Scripts\python.exe scripts\financial_retention.py archive --inventory .tmp/financial-retention-next.json --archive-dir artifacts/archives/financial-next --plan artifacts/archives/financial-next/prune-plan.json
.venv\Scripts\python.exe scripts\financial_retention.py verify-prune --plan artifacts/archives/financial-next/prune-plan.json --ready artifacts/archives/financial-next/prune-ready.json
.\scripts\prune_financial_archives.ps1 -Ready artifacts/archives/financial-next/prune-ready.json -Log artifacts/archives/financial-next/prune-log.jsonl
```

Inventory hiện dùng active execution plan v9, configs và transitive JSON provenance;
giữ reference raw/PDF/image inputs, financial trial registry và benchmark hiện hành.
Khi active plan/benchmark đổi, cập nhật retention seeds trước inventory. Archive
không xóa gì; verify-prune refresh active closure và kiểm source còn byte-identical;
PowerShell validate mọi absolute direct leaf trong `data/financial` trước deletion.
Không prune market/canonical/clustering trees. Partial archive không có ready file
thì không đủ điều kiện prune; script không tự overwrite output hoặc repeat log.

Financial trial50: [PowerShell runbook](FINANCIAL_TRIAL_50_USER_GUIDE.md) và
[implementation report/log](../../artifacts/reports/financial-crawl-50-flow-v1/report.md).
[Live report07/10](../../artifacts/reports/financial-crawl-50-live-v1/report.md): đã
thử50 mã,300/300 base responses parse được; collection PARTIAL do quarter/history
metadata và document gaps.8 PDF/604 pages,0OCR,0accepted facts; cần đóng parser/PIT/
notes và IO cost trước scale. Flow giữ global budget/access latch và gate cluster.

Đây là entry point duy nhất cho acquisition/recovery còn active. CafeF `TradeHistoryNew` là active market source; source semantics chi tiết nằm tại [CafeF](sources/CAFEF.md), trạng thái dataset nằm tại [Current status](../CURRENT_STATUS.md).

## Active contracts

- `configs/data/cafef_expansion_v1/`: frozen C6 expansion universe, five worker shards và acquisition contract.
- `configs/data/cafef_supplemental_v1/`: 148 deferred expansion candidates; chỉ chạy trong stage supplemental được phê duyệt.
- `configs/data/cafef_c8_complete_only_v1.json`: C8 complete-only offline build contract; không dùng để rerun khi chỉ verify.
- `configs/data/identity_review_v1.json`: reviewed identity aliases/evidence dùng bởi C8.

## Active commands

```powershell
.venv\Scripts\python.exe scripts\run_cafef_expansion_worker.py --help
.venv\Scripts\python.exe scripts\package_cafef_expansion_handoff.py --help
.venv\Scripts\python.exe scripts\verify_cafef_expansion_handoffs.py --help
.venv\Scripts\python.exe scripts\consolidate_cafef_expansion_handoffs.py --help
.venv\Scripts\python.exe scripts\run_cafef_supplemental_worker.py --help
```

Acquisition phải dùng explicit execute/resume contract, immutable raw pages, exact hashes và fail-closed access handling. Không bypass login, anti-bot, paywall hoặc access control. Không coi provider boundary là listing date; không fabricate missing history.

## Financial raw coverage pilot

Nhánh financial kế thừa discovery tại [CAFEF.md](sources/CAFEF.md), dùng
`GetReportSummary` cho FPT/VNM/PVS/ACV, các năm hoàn chỉnh 2021–2025, `QUY`/`NAM`
và KQKD/CDKT/LCTT. Đây là acquisition/coverage stage riêng với market-only M2;
không normalize canonical, không tính ratio/score và không approve PIT.

```powershell
.venv\Scripts\python.exe scripts\run_cafef_financial_pilot.py --dry-run
.venv\Scripts\python.exe scripts\run_cafef_financial_pilot.py --execute
.venv\Scripts\python.exe scripts\run_cafef_financial_pilot.py --verify data/financial/cafef_raw_pilot_v1/<run-id>
```

Config: `configs/data/cafef_financial_pilot_v1.json`. Raw response, request metadata,
config/code snapshots, `coverage.json` và exact-hash manifest nằm trong local ignored
`data/financial/cafef_raw_pilot_v1/`. `--verify` kiểm tra inventory/hash và replay
coverage offline; `--dry-run` không gọi network. Mỗi execute tạo run mới, không
overwrite/resume run cũ. Run bị ngắt chưa có manifest không phải completed evidence.

Collector dùng tối đa 160 logical calls, 8 pages/stream, 4 kỳ/page, khoảng cách
ít nhất 2 giây, timeout 20 giây và tối đa 2 transport attempts/call. Dừng toàn run
khi có access/rate boundary. Không dùng `count` của provider làm bằng chứng đủ kỳ;
kiểm tra kỳ thực tế, overlap/order và liệt kê missing periods trong target window.
`REPORT_TYPE_NOT_RETURNED` khác `EMPTY_PROVIDER_PAGE`; page/request cap không được
gọi COMPLETE. `execution_status` và `coverage_status` độc lập: request hoàn thành
vẫn có thể chỉ đạt coverage PARTIAL. Presence của kỳ không chứng minh đủ đầu vào score.

Provider `quater=0` được giữ cho NAM; QUY yêu cầu 1–4. `type`, `content`, template,
fact codes/values và toàn payload được giữ nguyên, chưa suy scope/audit/duration.
Raw tiền và EPS không áp chung hệ số quy đổi. Mọi output giữ
`PIT_UNRESOLVED`, `published_at/available_at=null`, `financial_features_allowed=false`.
Internal observation/hash không phải verified restatement chain.

## Financial detail remediation — 2026-10-03

Đã thực hiện acquisition/coverage remediation pilot trong nhánh CafeF, kế thừa
summary raw pilot. [Report quá trình và kết quả](../../artifacts/reports/financial-remediation-v1/report.md)
ghi chi tiết phạm vi, coverage, PDF/version evidence, tests và remaining blockers.

```powershell
.venv\Scripts\python.exe scripts\run_cafef_financial_detail.py --dry-run
.venv\Scripts\python.exe scripts\run_cafef_financial_detail.py --execute
.venv\Scripts\python.exe scripts\run_cafef_financial_detail.py --verify data/financial/cafef_detail_v1/<run-id>
.venv\Scripts\python.exe scripts\acquire_cafef_financial_gap_documents.py --detail-run data/financial/cafef_detail_v1/<run-id> --execute
.venv\Scripts\python.exe scripts\analyze_cafef_financial_data.py --detail-run data/financial/cafef_detail_v1/<run-id> --summary-run data/financial/cafef_raw_pilot_v1/<summary-run-id> --output data/financial/<new-analysis-directory>
```

Detail path giữ row code/name/raw display text và provenance; scale/unit và duration
chưa approved không được normalize thành canonical. `bsheet/incsta/cashflow` được
quan sát từ UI; annual anchor có 4 năm, quarterly anchor có 4 quý. Không biến header
có kỳ nhưng toàn ô blank thành observed numeric coverage. Numeric crosswalk chỉ
comparison evidence, không resolve scope/vintage/PIT; failed summary page bị loại
khỏi comparison. CSV export nằm trong private ignored `data/` và không redistribute.

Gap-document collector tải tối đa 20 kỳ từ reviewed local FileBCTC lists; chỉ public
CafeF/mediacdn host, giữ tất cả alternative IDs. Chọn file để inspection không phải
canonical revision rule. 11 gap PDFs đã tải; PDF mẫu là scan, 45 candidate facts được
visual-transcribe với page/hash. Không gọi các mẫu này là automatic full PDF extraction.

Financial PIT vẫn NOT_READY, `financial_features_allowed=false`; chưa đủ điều kiện
historical score/valuation. Các raw runs/manifests cũ được giữ nguyên.

## Current boundary

Financial handoff 03/10/2026: [FPT annual core và readiness report](../../artifacts/reports/financial-pilot-closure-v1/report.md).
Offline OCR/visual review đạt FPT core 49/49 cho 2019–2025. Runner
`scripts/build_financial_pilot_readiness.py` xuất checklist với document evidence,
giữ revisions và null PIT; không chọn canonical hoặc tính score. Overlay hiện hành
`data/financial/pilot_readiness_v4`; full pilot vẫn PARTIAL.

C8 đã dùng 500 baseline + 452 complete expansion. 148 expansion rows còn deferred và chỉ là optional future supplemental stage, không phải blocker của M2-PREP. R1 và D1 không crawl network, không chạy supplemental và không thay data result. Planning/runbook superseded đã rời active tree và chỉ còn trong Git history.

## Financial workflow để mở rộng nhiều mã

Stage hiện tại: FIN-D2 reference mapping/workflow, chưa FIN-D5 full-universe crawl.
Mỗi bước chạy ra directory mới với manifest/hash; raw và evidence cũ bất biến.

| Bước | Tự động hóa hiện có | Acceptance và xử lý exception |
|---|---|---|
| 1. Requirements | Annual checklist/task matrix sinh field-year dependencies; deduplicate inputs dùng chung | Contract ngành/scope/framework/kỳ xác định; ngân hàng cần contract riêng |
| 2. Discover/acquire | CafeF summary/detail/document lists; bounded vintage và explicit issuer collectors | Full statements/notes; audit extract hoặc IFRS annual report không thay full VAS |
| 3. Extract/index | Embedded text trước; scans dùng bounded OCR, cache PDF hash/page | Hints chỉ tìm trang; giữ column/unit; chưa có parser notes tổng quát |
| 4. Work queue | build_financial_workflow.py nối inventories với checklist/task và recipes | Thiếu document → acquire; thiếu mapping → review; raw → extract/verify; conflict → resolve theo vintage |
| 5. Semantic/QA | Evidence overlay, hashes, accounting identity checks | Không alias net profit/debt/cash proceeds/D&A; kiểm tra same-PDF/column/kỳ/unit/scope/framework |
| 6. Publication/revision | Giữ mọi vintage; FPT listing parser giữ exact attachment/date | Actual availability/timezone và historical identity; date-only không tự thành timestamp |
| 7. Task readiness | Rebuild overlay/task matrix sau mỗi accepted evidence run | F/M/Z đủ inputs chưa đủ PIT; P/E cần TTM/raw price/share basis; P/B cần dated parent common equity/shares |
| 8. Scale gate | Pilot-bounded policy, exception queue và immutable replay | Mở batch khi template/mapping/QA đạt; đo verified coverage/conflict/manual load/request cost |

Recipes tại [financial_workflow_v1.json](../../configs/data/financial_workflow_v1.json)
ghi search terms và QA cho earnings/debt/net receivables/issuance/PPE/EBIT/
parent equity/share basis. Đây là extraction/review contract, không tự approve
mapping/features. Document candidates vẫn phải xác minh framework; policy đánh dấu
VNM 2019/2020/2021/2025 thiếu full consolidated VAS dù có annual-report candidate.

Command tái lập queue hiện hành (đổi output khi chạy lại):

```powershell
.venv/Scripts/python.exe scripts/build_financial_workflow.py --readiness-run data/financial/pilot_readiness_v7 --task-run data/financial/task_readiness_v4 --index-run data/financial/all_document_text_v2 --index-run data/financial/fpt_annual_ocr_v1 --index-run data/financial/fpt_full_notes_ocr_v1 --index-run data/financial/fpt_original_2025_main_ocr_v1 --index-run data/financial/fpt_original_2025_notes_ocr_v1 --output data/financial/workflow_<new-run>
```

Output hiện hành `data/financial/workflow_v4/workflow.json`: 1.224 unique field-year
cells (1.176 baseline + 48 semantic targets), 140 external temporal requirements,
reuse 460 OCR pages và 27 annual PDF candidates. Không network/download/OCR lại.
Queue cần cả all-document inventory; chỉ đưa FPT OCR inventory sẽ phân loại sai
các mã khác thành thiếu tài liệu. Candidate PDF không bảo đảm đúng framework.

Khi scale: shard mã theo template/sector, mỗi run giữ caps/cache; parser mới đối
chiếu reference PDF trước áp batch. Publication/corporate actions thu riêng và
join issuer/security/period/vintage; không current-shares backfill hoặc áp latest
revised figures ngược lịch sử. Notes/semantic review hiện còn thủ công; chưa có
unattended end-to-end collector/parser/PIT pipeline cho khoảng 1.000 mã.
Report hiện hành: [financial workflow v1](../../artifacts/reports/financial-workflow-v1/report.md).

### Date-PIT và quarantine — latest 03/10/2026

Owner đã duyệt DATE_ONLY cho daily/monthly. Publication phải nối exact PDF hash;
usable_from_date là phiên exchange quan sát được đầu tiên sau ngày công bố,
`decision_date >= usable_from_date`; source timestamp/available_at giữ null.
Không cần giờ để đạt date coverage, nhưng còn semantics/joint vintages/identity.
Calendar C8 observed union không authoritative; ngoài phạm vi không suy lịch.

Latest runs: pilot_readiness_v10, task_readiness_v6, date_pit_v4, workflow_v6.
10 PDFs có reviewed publication, 11 exceptions; 139 value cells/124 date-reference
cells. Quarantine exact hash qua pilot_publication_review_v1, giữ nguyên raw.
26 annual candidates/488 cached OCR pages, 1.224 queue cells/140 external deps.
Không coi OCR publication prefix đủ cho full statement/field verification.

Tái lập date overlay (đặt output mới):

```powershell
.venv/Scripts/python.exe scripts/build_financial_date_pit.py --readiness-run data/financial/pilot_readiness_v10 --publication-run data/financial/pilot_publication_review_v1 --task-run data/financial/task_readiness_v6 --decision-date 2026-08-28 --output data/financial/date_pit_<new-run>
.venv/Scripts/python.exe scripts/build_financial_workflow.py --readiness-run data/financial/pilot_readiness_v10 --task-run data/financial/task_readiness_v6 --index-run data/financial/all_document_text_v2 --index-run data/financial/fpt_annual_ocr_v1 --index-run data/financial/fpt_full_notes_ocr_v1 --index-run data/financial/fpt_original_2025_main_ocr_v1 --index-run data/financial/fpt_original_2025_notes_ocr_v1 --index-run data/financial/pilot_publication_ocr_v1 --document-review-run data/financial/pilot_publication_review_v1 --output data/financial/workflow_<new-run>
```

Khi rebuild value readiness, thêm --document-review-run tương tự và cả fact runs
fpt_original_2025_core_v1/fpt_original_2024_equity_v1 vào bảy fact runs trước.
Task readiness dùng configs/data/financial_evidence_policy_v2.json. Các run cũ
không sửa; snapshots policy/code/manifests giữ nguyên. [Report mới](../../artifacts/reports/financial-date-pit-v1/report.md)
liệt kê stage status, source evidence, coverage thực tế và remaining workflow.

### Executable reference flow — original slice 03/10/2026

Có code coordinate parser và EPS/EM-Z calculators; replay không nhập lại số bằng
tay. Parser chỉ cho exact PDFs/templates đã review, matched ground truth và QA;
PDF mới/chỉ tiêu chưa mapped vào exception queue. Đây là cache replay, không gọi
network hoặc render/OCR lại. Upstream collector/extract/notes scripts ở trên tạo
cache lần đầu; thiếu/hash sai phải fail, không silently switch source/version.

```powershell
.venv/Scripts/python.exe scripts/run_financial_reference_flow.py --config configs/data/financial_reference_flow_v1.json --output data/financial/reference_flow_<new-run>
```

Latest reference_flow_v6: 22 numeric cells + bốn bridges PASS, bốn task-year EPS/Z
reference kết quả, review queue zero trong calibration scope. Known EPS2024 revision
chặn old result từ 20/03/2026; F/M/PE/PB có missing-input lists nhưng chưa calculators.
Không overwrite output, không approve unseen template hoặc promote research.
[Report](../../artifacts/reports/financial-reference-flow-v1/report.md) ghi số liệu,
precision/revision limits và distinction giữa reference/full financial flow.

### EPS revision/F-score — latest 03/10/2026

Config `financial_reference_flow_v2.json` dùng readiness_v11, thêm restated2024
template và F-score signal calculator. Latest flow_v9: 25 numeric cells/bốn
bridges PASS, EPS2024 chọn4.944 trước20/03/2026 và4.292 từ đó; EPS2025 5.216.
FPT2024/25 có6/9 F-score signals, total null vì ordinary-income reconciliation.
Readiness150/1.176; date_pit_v5 135 date cells; task_readiness_v7 0/120 production
ready. Workflow_v7 reuse488 OCR pages, semantic queue giảm208→197; chưa scale.

```powershell
.venv/Scripts/python.exe scripts/run_financial_reference_flow.py --config configs/data/financial_reference_flow_v2.json --output data/financial/reference_flow_<new-run>
```

Rebuild readiness phải thêm fact-run `data/financial/fpt_revision_fscore_review_v1`
vào các runs trước; task/date/workflow dùng readiness_v11 và task_readiness_v7.
[Report](../../artifacts/reports/financial-revision-fscore-v1/report.md).

## KBS candidates và named VAS reference continuation

Latest report: [source research](../../artifacts/reports/financial-source-research-v1/report.md).
KBS có15 responses trên bốn mã, notes/PIT vẫn cần exact issuer PDFs. VCI403 dừng,
không workaround; monetary match không chấp nhận provider publication dates.
Raw JSON → offline normalize → PDF QA/notes → exact-hash publication/date-PIT →
joint comparability/share events → strict hoặc named reference calculator.
Unseen-PDF semantics còn cần review; FIN-D5 full-universe chưa mở.

```powershell
.venv/Scripts/python.exe scripts/probe_financial_providers.py --config configs/data/financial_provider_probe_v2.json --output data/financial/provider_probe_NEW
.venv/Scripts/python.exe scripts/run_financial_source_completion.py --config configs/data/financial_source_completion_v3.json --output data/financial/source_completion_NEW
```

Mọi output dùng folder mới. Config source completion pin reviewed pilot FPT;
không dùng để tự promote score của VNM/PVS/ACV chưa PDF QA. Registry VAS reference
clustereligiblefalse; production methodology MANUAL_REVIEW_REQUIRED.

## Latest FPT financial handoff — 04/10/2026

Flow: discovered issuer URLs → immutable PDFs/inventory → embedded text index →
bounded render/OCR → visual review giá trị/đơn vị/kỳ → exact-hash publication/date-PIT
→ scope/share/capital bridges → offline calculators → per-task acceptance → replay/report.
Collector/OCR/calculator đã có code; mapping PDF mới và review số liệu vẫn có con người.
Không gọi đây là fully automatic OCR acceptance trên mọi mã.

Hai bank attachments của ESOP là cached source; bổ sung đăng ký vốn và BCTC riêng
để đối chiếu ngày/phải trả. Không suy cash classification hoặc fees từ aggregate.
`extract_financial_selected_pages.py` hỗ trợ disjoint ranges cùng PDF, từ chối
overlap/filename collisions; v1 extraction chưa hoàn tất được giữ và không dùng,
sealed `fpt_esop_evidence_ocr_v2` là input active.

```powershell
.venv/Scripts/python.exe scripts/build_financial_fpt_equity_review.py --output data/financial/fpt_equity_review_NEW
.venv/Scripts/python.exe scripts/run_financial_fpt_acceptance.py --config configs/data/financial_fpt_acceptance_v1.json --output data/financial/fpt_acceptance_NEW
.venv/Scripts/python.exe scripts/validate_financial_fpt_acceptance.py --run data/financial/fpt_acceptance_v5 --replay data/financial/fpt_acceptance_v4
```

Review builder khóa transcription đã visually review của FPT; không dùng trực tiếp
để approve template/mã khác. Nếu tạo review run mới, tạo config version mới pin
manifest đó; không sửa immutable input. Final acceptance_v4/v5 replay-identical,
sáu families từ 24/08, production zero. [Report](../../artifacts/reports/financial-fpt-acceptance-v2/report.md).
Stage kế tiếp dự kiến là bounded VNM/PVS/ACV pilot với cùng workflow/exception queue,
chưa execute và chưa được phép crawl cả universe.

## Pilot VNM/PVS/ACV — 05/10/2026

[Report và log](../../artifacts/reports/financial-three-symbol-pilot-v1/report.md),
[execution plan v7](../../configs/data/financial_execution_plan_v7.json). Workflow:
discover exact attachments → bounded download/hash → select/render/OCR pages →
visual-review value/unit/scope/period → numerator/debt/publication bridges → offline
calculators → reject missing/future/conflicts → immutable report/replay.

OCR là locator; trang scan/xoay vẫn cần visual review. Chỉ config đủ page/PDF/image
proof mới chạy được runner; không lấy số từ OCR tự động hoặc current provider EPS.
Acquisition không chạy lại trong replay:

```powershell
.venv\Scripts\python.exe scripts/run_financial_three_symbol_pilot.py --config configs/data/financial_three_symbol_pilot_v3.json --output data/financial/three_symbol_pilot_NEW_RUN
```

Output path phải mới. Latest v3/replay v4: 158 annual facts, 17/18 annual arithmetic
cells; five reviewed interim observations và VNM TTM reference. Chưa tự đẩy slice
vào readiness matrix, canonical market, clustering hoặc full universe. PVS/ACV
TTM, VNM ninth F input, publication/event coverage nằm trong report blocker matrix.

## Financial batch flow có checkpoint/resume — 05/10/2026

Handoff mới: [report quá trình và self-review](../../artifacts/reports/financial-batch-flow-v1/report.md),
[config active v6](../../configs/data/financial_batch_flow_v6.json).
Batch kỹ thuật10 mã FY2025 gồm FPT/VNM/PVS/ACV và HPG/DGC/MWG/REE/GMD/VHC.
Flow: config nguồn/ngân sách → discovery/cache → PDF → text mọi trang → OCR prefix
scan theo cap → review queue → hai adapter reference đã review → gate theo metric.
691 PDF/text pages,32 unique prefix OCR pages; không phải691 trang đã review số liệu.
Mọi document candidate vẫn cần issuer/scope/VAS/publication/revision và mapping review.

Runner chỉ gọi network khi có `--execute-network`. Không dùng config này như feed
latest: cache epoch là frozen source snapshot. Muốn refresh tạo epoch/config/run mới,
giữ tất cả vintages. Host mới phải có URL discovery độc lập, được ghi rõ trong config.
Không bypass403/429/challenge; HARD_STOP trong lineage cần source/access review riêng.
Limits:≤30 symbols,≤60 logical calls,≤24 PDF attempts/run,≤40 candidates,≤48 OCR
attempts/run,≤1.500 text pages,≤250 pages/PDF và≤300MB responses. Đây là hard caps
engineering, không phải ngưỡng đủ financial coverage. Client tối đa2 HTTP attempts
mỗi logical request, interval2 giây; không chạy1.000 mã trong một config.

Repo venv chưa có pypdf; dùng bundled Python có pypdf6.10.0 và Poppler trên PATH
cho extraction/OCR. Không có pypdf thì task ghi `DEFERRED_DEPENDENCY`, không nhận
dữ liệu rỗng làm thành công. Ví dụ trong PowerShell:

```powershell
$financialPython = 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
# Offline resume từ run gần nhất; output luôn là folder mới.
& $financialPython scripts/run_financial_batch_flow.py --config configs/data/financial_batch_flow_v6.json --output data/financial/batch_flow_NEW --resume-from data/financial/batch_flow_v9_final
.venv/Scripts/python.exe scripts/verify_financial_batch_flow.py --run data/financial/batch_flow_v9_final
```

Run mới có thể `--stop-after acquire`, rồi resume từ đó để tiếp tục extraction.
Interrupted parent chưa sealed chỉ tái dùng tasks có manifest riêng; không đọc files
chưa sealed. Sealed parent lần theo external receipt/manifest nên chỉ cần run gần nhất.
Config pin code; nếu sửa code, dùng `scripts/freeze_financial_batch_config.py --input
configs/data/financial_batch_flow_v6.json --output configs/data/financial_batch_flow_NEW.json`
sau khi review/test, không sửa pins config đã dùng. Đổi extraction fingerprint có thể
trích/OCR lại; raw/download cache vẫn giữ. Verifier kiểm dependency ngoài run và JSONL.

Trạng thái engineering COMPLETE không mở financial_features/research/full_universe.
Sáu mã mới chỉ có candidate; chưa generic parser/mapping tự động cho mọi thuyết minh.
Review queue có10 document items và9 known blocker items. OCR prefix bốn trang đầu
không đọc đủ EPS/debt/PPE notes; chọn trang bằng hints hoặc review rồi chạy extraction
range riêng. Không điền missing, ghép annual/TTM/current-book basis hay nhận provider
ngày/sector/current shares làm dữ liệu lịch sử. Trước mở accepted-data scale cần đóng
pilot, kiểm chứng parser theo template bằng ground truth và batch20–30 có thresholds
reviewed; trước financial clustering cần historical identity/PIT/history/protocol riêng.
# Financial crawler bàn giao người dùng — 06/10/2026

Điểm chạy mới: `scripts/crawl_financial.py` / `scripts/crawl_financial.ps1`.
Đọc [hướng dẫn người dùng](FINANCIAL_CRAWLER_USER_GUIDE.md) và
[report quá trình](../../artifacts/reports/financial-crawl-user-v1/report.md).
Config mẫu `configs/data/financial_crawl_user.example.json` không cần pilot/cache trên
máy tác giả; nối structured KBS, PDF/text/selected OCR, candidate exports, coverage,
accounting QA và semantic/publication queue. V1 vẫn bounded10 mã, raw/candidate-only.
Chưa mở full-universe acceptance/financial clustering. Các runner bên dưới giữ lineage.
