# Trạng thái hiện tại — M1 market foundation reported

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

- Notebook active: `06_pca_kmeans_v2_rerun.ipynb`,
  `07_cluster_quality_evaluation_pca_kmeans_v2.ipynb`,
  `08_cluster_profiling_pca_kmeans_v2.ipynb`,
  `09_temporal_stability_pca_kmeans_v2.ipynb` trong `M2/notebooks/`.
- Artifact: `M2/artifacts/m2-task6-pca-freeze-v2/`,
  `M2/artifacts/m2-task6-pca-kmeans-v2/`,
  `M2/artifacts/m2-evaluation-pca-kmeans-v2/`; 60 model mới trong
  `M2/models/pca_kmeans/`, config `configs/experiments/m2_pca_market_only_v2.json`.
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
  [07_cluster_quality_evaluation_pca_kmeans_v2.ipynb](../M2/notebooks/07_cluster_quality_evaluation_pca_kmeans_v2.ipynb).
- Bộ mới nằm trong M2/artifacts/m2-evaluation-pca-kmeans-v2/; chỉ có một CSV
  quality_summary.csv đúng 5 dòng × 7 cột, mọi n_total/n_available bằng 60,
  kèm năm PNG và manifest checksum. Bộ đánh giá cũ 15 tháng đã được đưa về Git history.
- Median Silhouette 0,939741; DB 0,383600; CH 1177,053847; Inertia 81023,955397;
  Balance 0,023814. Có 50/60 tháng Balance < 0,05, toàn bộ 60 tháng đạt rubric
  phân cụm bất đối xứng; ba singleton tại 2021-10-29, 2022-01-28, 2022-02-28.
- [Báo cáo Nhiệm vụ 7 V2](../M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_PCA_KMeans_v2.md)
  trình bày phán quyết A/B/C và giới hạn suy luận. Silhouette cao không chứng minh
  hai chế độ cân bằng, nguyên nhân dòng tiền hoặc hiệu quả đầu tư.

Đã kiểm tra thực thi notebook, schema, thống kê, biểu đồ và checksum; toàn bộ
artifact/model Nhiệm vụ 6 V2 và bộ legacy được bảo toàn. Bàn giao quality metrics
cho Nhiệm vụ 10 với điều kiện các phương án dùng cùng dữ liệu/cửa sổ development.
Chưa thực hiện Nhiệm vụ 8–10 V2 trong phiên đánh giá này.

### Nhiệm vụ 8 PCA + K-Means V2 đã được người dùng chạy

Đã chuẩn bị [08_cluster_profiling_pca_kmeans_v2.ipynb](../M2/notebooks/08_cluster_profiling_pca_kmeans_v2.ipynb)
để người dùng tự chạy trên 120 hồ sơ/60 tháng của Nhiệm vụ 6 V2. Đã kiểm tra
ba bảng đúng kích thước 4×10, 9×4, 60×5; dùng scaler đã lưu của đúng tháng,
Radar/Heatmap và dropdown 60 tháng. Chỉ giới hạn hiển thị Z ở ±3, giữ Z thật
trong bảng/Heatmap và bằng chứng; không fit lại hoặc đọc holdout.

Người dùng đã chạy notebook: task8_manifest.json ghi complete, đủ 60 tháng/120
hồ sơ, Primary Driver là liquidity_21, chênh lệch Mean Robust Z C0−C1 = 240,887454.
Hai PNG, bằng chứng và báo cáo Nhiệm vụ 8 tên hậu tố v2 đã được kiểm tra checksum.
Kết quả ở M2/artifacts/m2-evaluation-pca-kmeans-v2/; manifest và CSV Nhiệm vụ 7
được bảo toàn. Các kết luận vẫn giữ nhãn trung tính, không suy chi phí thực thi từ
thanh khoản trung bình hoặc coi cụm thanh khoản thấp hơn là dưới market median.

### Nhiệm vụ 9 PCA + K-Means V2 đã hoàn tất

Đã chuẩn bị [09_temporal_stability_pca_kmeans_v2.ipynb](../M2/notebooks/09_temporal_stability_pca_kmeans_v2.ipynb)
đã được người dùng chạy. Bước đầu chuẩn hóa artifact Task 6 đã có sang ba CSV phẳng
đúng 59×10, 236×6, 944×7; ARI/NMI giữ nguyên, transition dùng nhãn aligned xuyên
chuỗi, drift có hai đầu tâm cụm gốc thật và được đối chiếu mapping đã lưu.
Phần đánh giá đọc ba CSV để tạo bốn bảng và hai biểu đồ; không fit hoặc mở holdout.

Đã kiểm tra toàn luồng và rerun trong thư mục tạm, cùng checksum và bảng số liệu;
đã có CSV/ảnh/báo cáo Task 9 chính thức với manifest `complete`. Đích là
M2/artifacts/m2-evaluation-pca-kmeans-v2/ và báo cáo Nhiệm vụ 9 hậu tố v2.
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

