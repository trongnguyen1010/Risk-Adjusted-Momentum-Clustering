# Bàn giao session — financial baseline Execution56

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

Ngày bàn giao: **23/10/2026**. Workspace: `C:\Projects\Intern\SourceCode-CafeF`.
Đây là bản bàn giao theo yêu cầu owner để chuyển session, không phải protocol mới
hoặc giấy phép tự đổi phương pháp phân cụm.

## 1. Kết quả phiên này

Owner yêu cầu **commit và push trước**, sau đó tính tỷ số và chạy model financial.

1. Đã tạo commit **`f1a5ba793b62db6bb5f9822281ac4409c5274000`**:
   `Checkpoint financial ingestion, reference delivery and history archival`.
2. Đã push thành công lên nhánh **`research/financial-data`**, remote
   `https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering.git`.
   Commit chứa 379 file code/config/tests/docs/master report; raw/PDF/archive giữ
   local theo ignore policy. Push ban đầu bị automatic approval review chặn;
   owner đã xác nhận chính xác repo/branch/payload rồi mới retry thành công.
3. Đã kiểm đúng cohort **1.172 registry candidates × 10 năm 2016–2025 = 11.720 dòng**.
4. Đã tính lại khớp **70.320 giá trị của sáu core ratios** từ selected source inputs.
5. Đã fit **10 independent annual static K-Means models**, tất cả hội tụ.
6. Đã kiểm độc lập hashes, scalers, assignments, inertia, profiles và checkpoints.
7. Đã cập nhật report tổng, active pointers, quyết định, changelog và runbook.

**Execution kỹ thuật COMPLETE; chất lượng clustering REVIEW_REQUIRED;
final M2/M3 vẫn PARTIAL.** Không có acquisition/PDF/OCR mới trong lượt baseline.
Không còn worker baseline chạy; status đã COMPLETE.

## 2. Git: phần nào đã push, phần nào chưa

HEAD và `origin/research/financial-data` đang cùng `f1a5ba7` tại lúc bàn giao.
**Implementation/report Execution56 và bản bàn giao này chưa commit/push**.
Không reset/discard working tree khi sang session mới.

Các file mới của baseline:

- [Config](../configs/experiments/financial_full10_baseline_v1.json).
- [Driver](../src/delta_t1/experiments/financial_full10_baseline.py).
- [CLI Python](../scripts/financial_full10_baseline.py).
- [PowerShell Run/Check/Status](../scripts/financial_full10_baseline.ps1).
- [Independent verifier](../scripts/financial_full10_review.py).
- [Tests](../tests/unit/experiments/test_financial_full10_baseline.py).

Các file tracked đã sửa: `CHANGELOG.md`, `README.md`, master report,
`docs/CURRENT_STATUS.md`, `docs/DECISIONS.md`, `docs/PROJECT_MAP.md`,
`docs/README.md`, `docs/ROADMAP.md`, `docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md`,
`scripts/README.md`. Kiểm lại `git status --short` để lấy danh sách thực tế.
Các artifacts ngoài master report thường bị ignore; Git clone riêng không chứa
đủ raw/results/archive để replay. Không force-add toàn bộ data/artifacts.

## 3. Input hiện hành và giới hạn

- [Handoff dễ tìm](../data/handoffs/financial-reference-2016-2025/README.md).
- Feature CSV: `data/handoffs/financial-reference-2016-2025/financial-ratios-1172-symbols-2016-2025.csv`.
- Cohort CSV: `data/handoffs/financial-reference-2016-2025/securities-1172-symbols.csv`.
- Handoff manifest giữ hashes và original paths; driver kiểm khớp delivery gốc.
- Frozen delivery: `data/financial/history_dstock_remaining_delivery_v1/results/6eadc4924d41c2de1f9f`.
- Delivery manifest SHA256: `6eadc4924d41c2de1f9f2f05839bf7845727f34e1e2cb4dff6c2ee91fe6b156c`.

Trong cohort full10: **10.400 CafeF API rows**, **1.309 DStock rows**,
**10 reviewed PDF rows**, **1 reviewed issuer HTML row**. PDF/HTML này đã có từ
trước, không tải mới. Một số CafeF rows dùng direct-CFO recovery; driver giữ đúng
evidence/code-label/component checks, không lấy missing CFO thành zero.

Dataset rộng hơn vẫn **13.529 reference rows / 1.428 candidates có ít nhất một kỳ**;
không dùng số này thay số full10. Coverage còn 761 held annual cases/257 Regular
candidates và 93 ngoài Regular schema; 95 mã thiếu một kỳ. Các API gaps đã được
thử trước đó; phiên này không mở lại acquisition.

Arithmetic replay xác nhận phép tính từ selected inputs, **không phải xác thực
mới mọi source fact với BCTC gốc**. Không mix provider partitions, không dùng
source priority mới hoặc sửa các bản đã seal.

## 4. Model đã chạy và kết quả cần chú ý

Reuse [protocol core v1](../configs/experiments/financial_exploratory_core_v1.json):
`k=3`, `seed=42`, `n_init=20`, `max_iter=300`; zscore riêng từng năm;
không winsorization, PCA, imputation hoặc chọn model bằng returns.
Driver chỉ reuse protocol, không chạy acquisition cũ trỏ tới archived inputs.

Sáu features: `gross_margin`, `net_margin`, `liabilities_to_assets`, `current_ratio`,
`operating_cashflow_to_assets`, `asset_turnover_ending_assets`. Turnover dùng
ending assets, không phải average assets.

| Năm | Kích thước cụm, sắp giảm dần | Silhouette |
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

**Cả 10 năm có cụm dưới 10 mã**. Baseline chủ yếu tách cực trị ra khỏi phần lớn
mẫu; silhouette cao chưa đủ kết luận phân nhóm hữu ích. Năm 2025: VTI/CAD/JOS
ở cụm ba mã, QBS singleton. Ví dụ QBS net_margin=-522,434;
CAD liabilities/assets=131,480; VTI liabilities/assets=127,058 (ratio, chưa ×100%).
Cần kiểm tử/mẫu/scope/unit và tình trạng doanh nghiệp; cực trị chưa tự chứng minh
lỗi data. Không tự xóa, clip hoặc sửa số để làm kết quả đẹp.

Cluster IDs chỉ có ý nghĩa trong từng năm. Đây không phải Dynamic Clustering,
out-of-sample result hoặc historical investable universe. Cohort cố định full10
có selection/survivorship bias.

## 5. Output và bằng chứng

- [Report tổng toàn quá trình](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md),
  đọc phần **Execution56** cuối file và latest status đầu file.
- [Report baseline](../artifacts/reports/financial-full10-baseline-v1/report.md).
- [Result pointer](../artifacts/reports/financial-full10-baseline-v1/result-ref.json).
- [Verification](../artifacts/reports/financial-full10-baseline-v1/verification.json).
- [180 dòng review cực trị](../artifacts/reports/financial-full10-baseline-v1/outlier-review.csv).
- [33 memberships trong cụm nhỏ](../artifacts/reports/financial-full10-baseline-v1/small-cluster-members.csv).

Result root: `data/financial/financial_full10_baseline_v1/results/4d521e71139a48340d3d`.
Manifest SHA256: `4d521e71139a48340d3d00f5e505ab3f07613ed9754d5e5ceaf33172c99b1da3`.
Có `features.csv`, `assignments.csv`, `metrics.csv`, `snapshots.json`
(scaler/centroid/profiles), validation, config/protocol và input pins.

Checkpoints nằm dưới `data/financial/financial_full10_baseline_v1/runs/`;
pin config/code/input tạo run identity, mỗi năm có checksum. Resume chỉ reuse
checkpoint khớp identity/checksum; đổi pins sinh run khác. Giữ immutable results.

## 6. Kiểm tra đã chạy

- Trước commit: 26 distinct targeted tests exploratory/DStock/remaining/dashboard
  PASS sau khi rerun HTTP localhost ngoài sandbox; Python compile và Node checks PASS.
- Execution56: **11 targeted tests PASS**, compileall PASS, synthetic smoke PASS:
  `run-20261023T154334Z-8bc948c5`.
- Independent verifier kiểm **1.786 input pins**, 11.720 unique cohort keys,
  scaler mean/population std từng năm; tất cả nearest-centroid assignments,
  inertia, profile means/sizes và checkpoint identities/checksums: **PASS**.
- 15 baseline documentation links và `git diff --check`: PASS.
- **Full repository suite chưa có kết quả PASS**. Hai lượt trước không hoàn tất,
  cuối stdout ở cached PDF fixtures; đã dừng có kiểm soát. Không suy chính xác
  nguyên nhân hang hoặc bỏ assertions. Logs `.tmp/precommit-tests*/test.log`.
  Không cần refit/retest toàn bộ chỉ để bàn giao documentation.

## 7. Lệnh cần dùng ở session mới

PowerShell, chạy từ project root:

```powershell
Set-Location 'C:\Projects\Intern\SourceCode-CafeF'
git status --short
scripts/financial_full10_baseline.ps1 -Mode Status

$FinancialPython = 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = "$PWD/src;$PWD/tests;$PWD/.tools/research-runtime"
& $FinancialPython scripts/financial_full10_review.py
& $FinancialPython -m unittest unit.experiments.test_financial_full10_baseline unit.experiments.test_financial_exploratory -q
```

`.venv` cũ không dùng được trong phiên này; dùng runtime nêu trên.
Lệnh `-Mode Check -Python $FinancialPython` tính lại inputs mà không fit.
`-Mode Run -Python $FinancialPython` chỉ cần khi muốn resume/replay đúng protocol;
**không cần chạy lại baseline đã hoàn tất**. Log lượt chạy:
`.tmp/financial-full10-baseline.log`.

## 8. Bước tiếp theo và những điều chưa được tự làm

1. Đọc `AGENTS.md`, bản bàn giao này, latest section của master report và
   `docs/DECISIONS.md`; kiểm Git và result pins. Không đọc lại toàn bộ lịch sử.
2. Review outlier queue bằng cache hiện có: tử/mẫu, scope/unit, doanh thu cực nhỏ,
   mất vốn, direct-CFO/source mapping. Report bằng chứng và phân biệt bất thường
   kinh tế với lỗi dữ liệu; chưa sửa số hoặc quarantine chỉ theo magnitude.
3. Soạn **protocol comparator preprocessing** với lý do và acceptance criteria.
   Rank hoặc robust/clipping chỉ là đề xuất, **chưa được owner duyệt để chạy**.
   Thay methodology/preprocessing cần `MANUAL_REVIEW_REQUIRED` theo AGENTS/ADR;
   xin owner chốt trước run mới, giữ baseline này làm đối chứng.
4. Khi được duyệt, tạo version/run mới, targeted tests, execute và cập nhật
   report tổng. Không chọn k/algorithm bằng portfolio returns.
5. Sau review có thể chốt commit cho implementation Execution56. Nếu push,
   nêu rõ phạm vi mới; xác nhận cũ chỉ ghi nhận payload checkpoint trước chạy.

Các ràng buộc còn hiệu lực:

- **Không tự tải thêm PDF/OCR**; owner yêu cầu báo nhu cầu/số lượng và hỏi trước.
- EPS/P/E/P/B/F/M/Z đầy đủ 2016–2025 vẫn **0 mã hoàn chỉnh**; pilot FY2025 giữ
  **29/30**, VNM F thiếu basis. Core ratios không thay thế sáu families này.
- PIT/research/M3 gates giữ false. Cần publication/vintages/historical identity,
  market/calendar/share events và protocol trước M3. Market/model ở máy thành
  viên khác, owner chưa có config/artifacts handoff; không tự dựng thay.
- Không refit market, chạy backtest hoặc gọi kết quả hiện tại là final M2/M3.
- Không spawn subagents; repo dùng single-agent workflow.
- Giữ source hashes, counters và blocked boundaries; không reset budget khi resume.
- Cleanup53–55 đã gom lịch sử vào archive; không xóa tiếp evidence dựa vào report
  tóm tắt. Current input dependencies còn cần giữ để verifier chạy được.
  [Kho lịch sử/restore](../artifacts/archives/financial-history-20261023/README.md),
  [cache archive](../artifacts/archives/financial-cache-20261023/README.md).

## 9. Prompt gợi ý để bắt đầu session mới

> Hãy đọc AGENTS.md và docs/FINANCIAL_SESSION_HANDOFF.md trong
> C:\Projects\Intern\SourceCode-CafeF rồi kiểm trạng thái Git và result pointers.
> Execution56 đã chạy baseline 1.172 mã × 10 năm; không cần crawl/refit lại.
> Tiếp tục review outliers từ cache, xác định nguyên nhân cụm nhỏ, viết đề xuất
> preprocessing comparator và cập nhật report tổng. Chưa chạy phương pháp mới
> trước khi tôi duyệt protocol; chưa tải PDF/OCR nếu chưa hỏi tôi. Giữ các thay
> đổi Execution56 chưa commit, không reset working tree. Không gọi core ratios
> là bộ EPS/P/E/P/B/F/M/Z hoàn chỉnh hoặc kết quả PIT/M3 cuối cùng.


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

