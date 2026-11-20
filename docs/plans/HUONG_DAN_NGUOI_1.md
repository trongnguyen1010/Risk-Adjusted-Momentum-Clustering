# Hướng dẫn thực hiện công việc — Người 1

**Phạm vi phụ trách:** Nguồn dữ liệu, Làm giàu data, B-PIT và Builder Đánh giá đầu tư.  
**Trạng thái:** **ĐÃ HOÀN THÀNH 100% (20/20 tasks)** — Đã push 20 commits lên `origin/feature/indicators-v1`.  
**Tài liệu tham chiếu:** [Kế hoạch tổng thể](KE_HOACH_TRIEN_KHAI_B_PIT_VA_DANH_GIA_DAU_TU.md) · [PHAN_CONG_CONG_VIEC_B_PIT_VA_DANH_GIA_DAU_TU.json](PHAN_CONG_CONG_VIEC_B_PIT_VA_DANH_GIA_DAU_TU.json).

---

## Biên bản bàn giao kết quả thực tế của Người 1

1. **Bộ dữ liệu làm giàu B-PIT (Stage C):**
   * Vị trí: `data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/indicators.sqlite`
   * Số liệu nghiệm thu: Khớp chính xác 1.045 mã-năm, 1.111 ô điền median; bảo toàn nguyên vẹn 319.620 dòng của database gốc.
2. **Bộ mô hình & nhãn phân cụm B-PIT Enriched (Stage D):**
   * Vị trí: `data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01/` (`labels.csv`, `models.json`, `audit.json`, `manifest.json`)
   * Kết quả: Cấu hình K-Means (k=3) đạt độ ổn định 0.922, Silhouette 0.230; 0 lỗi rò rỉ dữ liệu (`fit_leaks = 0`).
3. **Bộ dữ liệu đánh giá đầu tư ngoại tuyến D-ASS-01 (Stage S3):**
   * Vị trí: `data/experiments/assessment/assessment_v1_run01/` (`assessments.jsonl`, `peer_benchmarks.csv`, `coverage.csv`, `feature_history.jsonl`, `manifest.json`)
   * Kết quả: Chấm điểm đầy đủ 1.428 mã với dữ liệu thị trường A v4 thật và bộ quy tắc D-ASS-01 (67 Đáng cân nhắc đầu tư, 448 Cần theo dõi, 587 Chưa nên ưu tiên đầu tư, 326 Không đủ cơ sở đánh giá); verifier độc lập `PASS` 100%.
4. **Gói đóng gói bàn giao (Dành cho Người 2, 3, 4):**
   * Đã nén thành tệp: `Downloads/data.zip` (40.83 MB) chứa toàn bộ thư mục `data/` hoàn chỉnh.

---

## Bảng tổng hợp 20 Atomic Commits đã thực hiện

| STT | Task ID | Commit Hash | Tiêu đề Commit | Trạng thái |
|:---:|:---:|:---:|:---|:---:|
| 1 | R1-01 | `4c53565` | feat(bpit-m3): Khóa môi trường và baseline | PASS |
| 2 | R1-02 | `2ede0af` | feat(bpit-m3): Kiểm kê và pin đầu vào | PASS |
| 3 | R1-03 | `9aaf722` | feat(bpit-m3): Phân loại các ô đủ điều kiện làm giàu | PASS |
| 4 | R1-04 | `3d0727f` | feat(bpit-m3): Tính median từ tập FIT gốc | PASS |
| 5 | R1-05 | `262dc5f` | feat(bpit-m3): Điền giá trị và ghi lineage theo ô | PASS |
| 6 | R1-06 | `85aa97b` & `5b02403` | feat(bpit-m3): Xuất SQLite dẫn xuất và audit | PASS |
| 7 | R1-07 | `ea63ed6` | feat(bpit-m3): Chuẩn hóa cohort và loader enriched | PASS |
| 8 | R1-08 | `1b070d3` | feat(bpit-m3): Thực hiện K-Means và PCA + K-Means | PASS |
| 9 | R1-09 | `240d49f` | feat(bpit-m3): Thực hiện Ward và GMM | PASS |
| 10 | R1-10 | `07545c8` | feat(bpit-m3): Tính chất lượng và độ ổn định cụm | PASS |
| 11 | R1-11 | `86aff9b` | feat(bpit-m3): Sàng lọc và khóa cấu hình chung | PASS |
| 12 | R1-12 | `f841343` | feat(bpit-m3): Xuất mô hình, labels và manifest B-PIT | PASS |
| 13 | R1-13 | `c5f5ba6` | feat(bpit-m3): Hoàn thiện notebook chạy và bàn giao B-PIT | PASS |
| 14 | R1-14 | `4ae316c` | feat(assessment): Nhận pin và chọn input Assessment | PASS |
| 15 | R1-15 | `4981e0a` | feat(assessment): Tạo Peers theo từng đặc trưng | PASS |
| 16 | R1-16 | `d11a6f9` | feat(assessment): Dựng lịch sử và coverage | PASS |
| 17 | R1-17 | `007c831` | feat(assessment): Nối engine đánh giá offline | PASS |
| 18 | R1-18 | `a01ef8a` | feat(assessment): Bổ sung CLI build Assessment | PASS |
| 19 | R1-19 | `2062dec` | feat(assessment): Khóa manifest và deterministic payload | PASS |
| 20 | R1-20 | `3478cef` | feat(assessment): Nghiệm thu builder trên bộ bàn giao thật | PASS |

---

## Quy chuẩn làm việc và Commit (Bắt buộc)

1. **Nguyên tắc Atomic Commit (1 Task = ĐÚNG 1 Commit riêng biệt):**
   - Mỗi task là một đơn vị tính năng độc lập. Khi hoàn thành và chạy test pass theo tiêu chuẩn nghiệm thu, **bắt buộc thực hiện commit ngay task đó**.
   - Tuyệt đối **KHÔNG gộp nhiều task vào một commit lớn** để đảm bảo lịch sử phát triển minh bạch, dễ dàng theo dõi tiến độ và thuận tiện rollback khi có sự cố.
2. **Cú pháp commit:** Sử dụng chính xác câu lệnh commit chuẩn đã đính kèm sẵn trong từng task bên dưới.
3. **Trình tự thực hiện:** Làm tuần tự từng task, nghiệm thu xong task hiện tại và commit xong thì mới chuyển sang task tiếp theo.

---

## Danh mục các nhiệm vụ chi tiết

### Task 01 (R1-01) — Khóa môi trường và baseline

- **Giai đoạn:** Stage A
- **File can thiệp:** `M3/notebooks/05_B_PIT_Enriched.ipynb`
- **Nội dung công việc:** Kiểm HEAD/local diff, Python/kernel, pip check và SQLite/NumPy/scikit-learn; đối chiếu Python3.12.7, SQLite3.45.3, NumPy2.2.6, scikit-learn1.8.0 của baseline. Ghi phiên bản thực tế, pip freeze, test M3 và dung lượng.
- **Tiêu chuẩn nghiệm thu:** Môi trường import được, pip check sạch, test M3 đạt và đủ dung lượng; khác biệt môi trường/baseline có ghi nhận trước khi chuyển B.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_*.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add M3/notebooks/05_B_PIT_Enriched.ipynb
  git commit -m "feat(bpit-m3): Khóa môi trường và baseline"
  ```

### Task 02 (R1-02) — Kiểm kê và pin đầu vào

- **Giai đoạn:** Stage B
- **File can thiệp:** `M3/notebooks/05_B_PIT_Enriched.ipynb`
- **Nội dung công việc:** Kiểm dữ liệu local trước; nhận đúng revision HF trong kế hoạch nguồn khi thiếu, lưu receipt/hash rồi mới copy logical path. Pin Indicators, availability, v4, C8 prices/calendar/VNINDEX, B-PIT baseline và hai run đối chứng; kiểm SQLite/schema. Người 1 tự kiểm hash tất cả nguồn, PRAGMA integrity_check, bảng/cột/unique keys, missingness/coverage và Q-date như mục3.4–3.5 trước khi làm giàu.
- **Tiêu chuẩn nghiệm thu:** Đủ file bắt buộc, hash/schema/integrity/readiness đúng; file khác hash được cô lập để đối chiếu, không ghi đè baseline.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_*.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add M3/notebooks/05_B_PIT_Enriched.ipynb
  git commit -m "feat(bpit-m3): Kiểm kê và pin đầu vào"
  ```

### Task 03 (R1-03) — Phân loại các ô đủ điều kiện làm giàu

- **Giai đoạn:** Stage C
- **File can thiệp:** `src/delta_t1/features/financial_enrichment/eligibility.py`
- **Nội dung công việc:** Lập inventory ticker/FY/metric/status/inputs_json cho FY2017–2024. Xét phi tài chính, báo cáo năm, usable date/cutoff và toàn bộ ô thiếu; CFO thiếu chỉ điền khi NI quan sát dương; ROE giữ điều kiện vốn chủ.
- **Tiêu chuẩn nghiệm thu:** NI0/âm/unknown, equity không hợp lệ, NOT_APPLICABLE hoặc thiếu báo cáo không bị điền. Đối chiếu1045mã–năm/1111ô theo nguồn; nếu lệch ghi nguyên nhân.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_eligibility.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/features/financial_enrichment/eligibility.py
  git commit -m "feat(bpit-m3): Phân loại các ô đủ điều kiện làm giàu"
  ```

### Task 04 (R1-04) — Tính median từ tập FIT gốc

- **Giai đoạn:** Stage C
- **File can thiệp:** `src/delta_t1/features/financial_enrichment/medians.py`
- **Nội dung công việc:** Đọc baseline role=FIT, đủ9/9 tại cutoff từng FY. Tính median theo FY/metric trên raw ratios chưa winsorize/scale; đóng băng donor IDs/counts và median table. Tự đối chiếu median bằng fixture tính tay, donor IDs/counts và thử loại late/imputed donor; các kiểm tra này đi cùng bước tính median.
- **Tiêu chuẩn nghiệm thu:** Median khớp phép tính độc lập; không có donor imputed/late/khácFY; count khớp n_fit. Thiếu donor không tự tạo giá trị.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_medians.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/features/financial_enrichment/medians.py
  git commit -m "feat(bpit-m3): Tính median từ tập FIT gốc"
  ```

### Task 05 (R1-05) — Điền giá trị và ghi lineage theo ô

- **Giai đoạn:** Stage C
- **File can thiệp:** `src/delta_t1/features/financial_enrichment/engine.py`
- **Nội dung công việc:** Áp median cho đúng các ô đủ điều kiện, hỗ trợ một hoặc nhiều ô thiếu trên một row. Giữ observed/F/Z/usable date; receipt gồm original status/value, rule, median/count, cutoff và số ô điền.
- **Tiêu chuẩn nghiệm thu:** Chỉ ô được phép thay đổi; imputed có status riêng. Replay cùng source/rule cho cùng giá trị, không dùng ô vừa điền làm donor.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_engine.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/features/financial_enrichment/engine.py
  git commit -m "feat(bpit-m3): Điền giá trị và ghi lineage theo ô"
  ```

### Task 06 (R1-06) — Xuất SQLite dẫn xuất và audit

- **Giai đoạn:** Stage C
- **File can thiệp:** `src/delta_t1/features/financial_enrichment/export.py`
- **Nội dung công việc:** Tạo run riêng gồm indicators.sqlite, imputed_cells.csv, medians_by_year_metric.csv, imputation_summary.csv, manifest.json. Pin commit/source/availability/FIT/rules và hashes đầu ra. Người 1 tự đối chiếu DB diff với receipts/manifest, baseline hashes, observed/F/Z/availability và FY ngoài scope trước khi bàn giao C.
- **Tiêu chuẩn nghiệm thu:** Integrity/unique keys/DB diff/receipts khớp; observed và FY ngoài scope không đổi, hash baseline giữ nguyên; run có sẵn không bị sửa.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_export.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/features/financial_enrichment/export.py
  git commit -m "feat(bpit-m3): Xuất SQLite dẫn xuất và audit"
  ```

### Task 07 (R1-07) — Chuẩn hóa cohort và loader enriched

- **Giai đoạn:** Stage D
- **File can thiệp:** `src/delta_t1/experiments/bpit_enriched.py`, `configs/experiments/bpit_enriched_v1.json`
- **Nội dung công việc:** Nhận đúng SQLite C; loader thử nghiệm opt-in IMPUTED_MEDIAN. Cohort từng FY = FIT gốc cộng rows hoàn tất9/9 có usable<=cutoff gốc; T1 chỉ fit cohort này, cùng cohort cho mọi candidate. Tự kiểm cohort/cutoff/T1 trên fixture, late/no-date và FY ngoài phạm vi; không cần một người khác chạy lại bước này.
- **Tiêu chuẩn nghiệm thu:** Cutoff/availability không đổi; late/no-date không tham gia FIT. Config enriched pin rõ parameters, scope, selection/validation và đối chứng; baseline builder/pointer giữ read-only.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_bpit_enriched_cohorts.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/bpit_enriched.py configs/experiments/bpit_enriched_v1.json
  git commit -m "feat(bpit-m3): Chuẩn hóa cohort và loader enriched"
  ```

### Task 08 (R1-08) — Thực hiện K-Means và PCA + K-Means

- **Giai đoạn:** Stage D
- **File can thiệp:** `src/delta_t1/clustering/bpit_adapters.py`
- **Nội dung công việc:** Tái sử dụng fitting/transform hiện có; KMeans và PCA-KMeans k3..8, PCA80%, parameters/seed theo config. Lưu state/feature order/label mapping; giữ đối chứng k3 seed42 n_init10 trên cùng dữ liệu enriched.
- **Tiêu chuẩn nghiệm thu:** Reload cho cùng assignment; late dùng frozen transform và centroid trong đúng không gian, không refit PCA/T1/model.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_bpit_kmeans_pca.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/clustering/bpit_adapters.py
  git commit -m "feat(bpit-m3): Thực hiện K-Means và PCA + K-Means"
  ```

### Task 09 (R1-09) — Thực hiện Ward và GMM

- **Giai đoạn:** Stage D
- **File can thiệp:** `src/delta_t1/clustering/bpit_adapters.py`
- **Nội dung công việc:** Bổ sung adapters Ward/GMM theo config tham chiếu; Ward gán late bằng centroid FIT trong T1, GMM bằng posterior của frozen model. Lưu đầy đủ model state và label mapping.
- **Tiêu chuẩn nghiệm thu:** Replay đúng assignments sau reload; nonconvergence/không đủ cụm được ghi evidence. Late inference không sửa model.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_bpit_ward_gmm.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/clustering/bpit_adapters.py
  git commit -m "feat(bpit-m3): Thực hiện Ward và GMM"
  ```

### Task 10 (R1-10) — Tính chất lượng và độ ổn định cụm

- **Giai đoạn:** Stage D
- **File can thiệp:** `src/delta_t1/evaluation/bpit_screening.py`
- **Nội dung công việc:** Silhouette/DB/CH đo trong T1; size/share theo FY; ARI subsample90% với seeds đã pin và temporal ARI trên mã FIT chung. Giữ metrics riêng khỏi portfolio evaluation.
- **Tiêu chuẩn nghiệm thu:** Đối chiếu metric trên fixture; label permutation không đổi ARI; case không tính được có status/null rõ và không được giả0.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_bpit_screening_metrics.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/evaluation/bpit_screening.py
  git commit -m "feat(bpit-m3): Tính chất lượng và độ ổn định cụm"
  ```

### Task 11 (R1-11) — Sàng lọc và khóa cấu hình chung

- **Giai đoạn:** Stage D
- **File can thiệp:** `src/delta_t1/experiments/bpit_enriched.py`
- **Nội dung công việc:** Chạy đủ24cặp trên FY2017–2022; admissibility minshare5% ở≥80%FY và median stability≥0.80; mean rank5metrics, tie nhỏk rồi KMeans/PCA-KMeans/Ward/GMM. Khóa trước validation FY2023–2024.
- **Tiêu chuẩn nghiệm thu:** Thay validation/returns không đổi selection. Validation fit riêng từng FY với algorithm/k đã khóa. Không candidate đạt thì trình đối chứng k3, không tự nới ngưỡng.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_bpit_screening_selection.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/bpit_enriched.py
  git commit -m "feat(bpit-m3): Sàng lọc và khóa cấu hình chung"
  ```

### Task 12 (R1-12) — Xuất mô hình, labels và manifest B-PIT

- **Giai đoạn:** Stage D
- **File can thiệp:** `src/delta_t1/experiments/bpit_enriched.py`, `scripts/build_financial_pit_clusters_enriched.py`
- **Nội dung công việc:** Tạo entrypoint enriched riêng theo nguồn, dùng chung logic với notebook. Xuất labels/models/audit/manifest; pin C/availability/parent/code/config; lưu cohort, transforms, đủk, FIT-only order ROE/D-E, change labels/ARI/đối chứng. Tự reload artifacts và replay inference bốn thuật toán, kiểm feature order/label mapping/model hash và đối chứng k=3 trước xuất bàn giao.
- **Tiêu chuẩn nghiệm thu:** fit_leaks rỗng; model/labels/order/hashes đúng; serializable/reload đạt; không sửa baseline. Loader M3 đọc đủk theo phần Người2.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_bpit_enriched_artifacts.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/bpit_enriched.py scripts/build_financial_pit_clusters_enriched.py
  git commit -m "feat(bpit-m3): Xuất mô hình, labels và manifest B-PIT"
  ```

### Task 13 (R1-13) — Hoàn thiện notebook chạy và bàn giao B-PIT

- **Giai đoạn:** Stage D
- **File can thiệp:** `M3/notebooks/05_B_PIT_Enriched.ipynb`
- **Nội dung công việc:** Tổ chức notebook cấu hình→preflight→C→D→audit→bàn giao, gọi module/entrypoint chung. Run All trên fixture; chạy D thật khi A–C đạt; lập ranking và tác động Va cho owner review. Tổng hợp kết quả self-check C/D, fit_leaks và tương thích loader vào packet owner review; không thêm gate audit dữ liệu bởi Người 3.
- **Tiêu chuẩn nghiệm thu:** Không hidden state/fit ngầm ở chart hoặc sửa run cũ. D chỉ chuyển E sau owner duyệt theo nguồn; chưa được duyệt giữ MANUAL_REVIEW_REQUIRED.
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add M3/notebooks/05_B_PIT_Enriched.ipynb
  git commit -m "feat(bpit-m3): Hoàn thiện notebook chạy và bàn giao B-PIT"
  ```

### Task 14 (R1-14) — Nhận pin và chọn input Assessment

- **Giai đoạn:** Stage S1
- **File can thiệp:** `src/delta_t1/experiments/assessment/inputs.py`, `tests/fixtures/assessment_v1/`
- **Nội dung công việc:** Sau F nhận cùng cặp B-PIT/SQLite enriched; kiểm labels/model/SQLite/availability hashes. Resolve ticker, demo as_of/session,18features/status/provenance, FY usable mới nhất/cutoff/18tháng; không fallback baseline hoặc modelFY cũ. Người 1 tự nhận và đối chiếu đủ pins C/D/E/F trước S1 theo mục6.4; hash thiếu hoặc sai vẫn phải dừng dù không có vai trò QA enrichment riêng.
- **Tiêu chuẩn nghiệm thu:** Pin mismatch/thiếu nguồn dừng build. Case mới usable nhưng thiếu model, sector không áp dụng, missing và stale theo đúng nguồn; không tự thêm policy nhận imputed.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_inputs.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/assessment/inputs.py tests/fixtures/assessment_v1/
  git commit -m "feat(assessment): Nhận pin và chọn input Assessment"
  ```

### Task 15 (R1-15) — Tạo Peers theo từng đặc trưng

- **Giai đoạn:** Stage S1
- **File can thiệp:** `src/delta_t1/experiments/assessment/peers.py`
- **Nội dung công việc:** Ưu tiên cùngA+B, dưới3 thì financial cùngB/market cùngA. Loại self/trùng/null/sai identity/kỳ/unit/source. ≥3 tính median/IQR, lưu basis/count/ref theo metric; missingB không tạoPeers.
- **Tiêu chuẩn nghiệm thu:** 0–2 không median, đúng3 có median; Peers ít không tự đổi verdict. Opt-in imputed theo policy đã duyệt, không kế thừa tự động từ M3.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_peers.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/assessment/peers.py
  git commit -m "feat(assessment): Tạo Peers theo từng đặc trưng"
  ```

### Task 16 (R1-16) — Dựng lịch sử và coverage

- **Giai đoạn:** Stage S3
- **File can thiệp:** `src/delta_t1/experiments/assessment/history.py`
- **Nội dung công việc:** Xuất feature_history.jsonl và coverage.csv cho đúng18features, ngày/FY/usable/status/unit/source. Lookback5/10 từ as_of, giữ gap và coverage thực; dòng tài chính theo FY và market theo snapshot hợp lệ.
- **Tiêu chuẩn nghiệm thu:** Không tạo số liệu/nội suy/đổi missing thành0; không dùng FY tương lai. Đổi lookback chỉ thay phần lịch sử, không đổi evidence/nhãn/verdict.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_history.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/assessment/history.py
  git commit -m "feat(assessment): Dựng lịch sử và coverage"
  ```

### Task 17 (R1-17) — Nối engine đánh giá offline

- **Giai đoạn:** Stage S3
- **File can thiệp:** `src/delta_t1/experiments/investment_assessment_v1.py`
- **Nội dung công việc:** Orchestrate inputs, rule evaluation/verdict/rationale của Người2, Peers/history. Tạo kết quả từng ticker trong danh mục hỗ trợ; không dùng NAV/trades/return để quyết định assessment.
- **Tiêu chuẩn nghiệm thu:** Fixture đủ4verdict, evidence thuộc18features, kết quả đúng mã/as_of/source. Rationale/Peers không thay điều kiện kết luận đã chốt.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/integration -p 'test_assessment_offline_builder.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/investment_assessment_v1.py
  git commit -m "feat(assessment): Nối engine đánh giá offline"
  ```

### Task 18 (R1-18) — Bổ sung CLI build Assessment

- **Giai đoạn:** Stage S3
- **File can thiệp:** `scripts/build_investment_assessment_v1.py`
- **Nội dung công việc:** CLI mỏng nhận source manifest/policy/output root rõ, gọi orchestrator. Preflight pins rồi build run mới; báo paths/counts/status, không crawl/fit realtime hoặc sửa pointer production.
- **Tiêu chuẩn nghiệm thu:** Thiếu input/sai pin/policy/version thì exit lỗi rõ; existing output không bị ghi đè; không dùng default baseline thay nguồn enriched.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_build_cli.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add scripts/build_investment_assessment_v1.py
  git commit -m "feat(assessment): Bổ sung CLI build Assessment"
  ```

### Task 19 (R1-19) — Khóa manifest và deterministic payload

- **Giai đoạn:** Stage S3
- **File can thiệp:** `src/delta_t1/experiments/investment_assessment_v1.py`
- **Nội dung công việc:** Xuất manifest,assessments.jsonl,peer_benchmarks.csv,coverage.csv,feature_history.jsonl; pin A/B-PIT/SQLite/availability/policy/code. Tách operational metadata khỏi deterministic assessment content hash.
- **Tiêu chuẩn nghiệm thu:** Cùng inputs/policy cho cùng nội dung/hash dù run_id/generated_at khác. Mọi file/hash và references truy được, không tự gắn verificationPASS.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_reproducibility.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/investment_assessment_v1.py
  git commit -m "feat(assessment): Khóa manifest và deterministic payload"
  ```

### Task 20 (R1-20) — Nghiệm thu builder trên bộ bàn giao thật

- **Giai đoạn:** Stage S3
- **File can thiệp:** `tests/integration/test_assessment_real_handoff.py`
- **Nội dung công việc:** Build từ F, đối chiếu FPT+ít nhất1mã hợp lệ khác, VCB/mã thiếu lịch sử và missing cases; chạy verifier độc lập, kiểm labels/FY/value/provenance và demo dates.
- **Tiêu chuẩn nghiệm thu:** FPT không bị hard-code verdict; nguồn thiếu/sai không dùng fixture thay thật. Có actual run IDs/hashes/coverage và verifier results trước bàn giao API.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/integration -p 'test_assessment_real_handoff.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add tests/integration/test_assessment_real_handoff.py
  git commit -m "feat(assessment): Nghiệm thu builder trên bộ bàn giao thật"
  ```
