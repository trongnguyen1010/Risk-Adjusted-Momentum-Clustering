# Hướng dẫn thực hiện công việc — Người 2

**Phạm vi phụ trách:** Tích hợp M3, Chạy Backtest và Bộ quy tắc đánh giá đầu tư.  
**Tổng số nhiệm vụ:** 15 tasks.  
**Tài liệu tham chiếu:** [Kế hoạch tổng thể](KE_HOACH_TRIEN_KHAI_B_PIT_VA_DANH_GIA_DAU_TU.md) · [PHAN_CONG_CONG_VIEC_B_PIT_VA_DANH_GIA_DAU_TU.json](PHAN_CONG_CONG_VIEC_B_PIT_VA_DANH_GIA_DAU_TU.json).

---

## Quy chuẩn làm việc và Commit (Bắt buộc)

1. **Nguyên tắc Atomic Commit (1 Task = ĐÚNG 1 Commit riêng biệt):**
   - Mỗi task là một đơn vị tính năng độc lập. Khi hoàn thành và chạy test pass theo tiêu chuẩn nghiệm thu, **bắt buộc thực hiện commit ngay task đó**.
   - Tuyệt đối **KHÔNG gộp nhiều task vào một commit lớn** để đảm bảo lịch sử phát triển minh bạch, dễ dàng theo dõi tiến độ và thuận tiện rollback khi có sự cố.
2. **Cú pháp commit:** Sử dụng chính xác câu lệnh commit chuẩn đã đính kèm sẵn trong từng task bên dưới.
3. **Trình tự thực hiện:** Làm tuần tự từng task, nghiệm thu xong task hiện tại và commit xong thì mới chuyển sang task tiếp theo.

---

## Danh mục các nhiệm vụ chi tiết

### Task 01 (R2-01) — Sửa loader M3 nhận đủ k cụm

- **Giai đoạn:** Stage D
- **File can thiệp:** `src/delta_t1/m3/inputs.py`, `tests/unit/test_m3_cutoff.py`
- **Nội dung công việc:** Sửa loader theo metadata k, thứ tự và nhãn cụm thay cho điều kiện cố định ba cụm. Giữ interface và kiểm tra legacy; bổ sung fixture k=3,4,8.
- **Tiêu chuẩn nghiệm thu:** Model có đầy đủ metadata giữ được cutoff; order/labels thiếu hoặc trùng bị chặn, legacy k=3 vẫn tái lập đúng.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_cutoff.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/m3/inputs.py tests/unit/test_m3_cutoff.py
  git commit -m "feat(bpit-m3): Sửa loader M3 nhận đủ k cụm"
  ```

### Task 02 (R2-02) — Truyền nguồn enriched xuyên runner

- **Giai đoạn:** Stage E
- **File can thiệp:** `scripts/run_m3.py`, `src/delta_t1/m3/inputs.py`
- **Nội dung công việc:** Resolve SQLite từ config, truyền cùng path cho scoring, sectors và hash trong manifest. Kiểm nhãn/model/availability và mở dữ liệu read-only.
- **Tiêu chuẩn nghiệm thu:** Fixture baseline/enriched cho đúng values, sector và hash cùng một nguồn; không bỏ sót default arguments của loader.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_enriched_sources.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add scripts/run_m3.py src/delta_t1/m3/inputs.py
  git commit -m "feat(bpit-m3): Truyền nguồn enriched xuyên runner"
  ```

### Task 03 (R2-03) — Tạo config thử nghiệm và cache riêng

- **Giai đoạn:** Stage E
- **File can thiệp:** `configs/experiments/m3_strategy_enriched_v1.json`, `scripts/run_m3.py`
- **Nội dung công việc:** Tạo config enriched từ baseline với trạng thái READY_TO_LOCK_AFTER_BPIT. Pin C/D/models/availability và dùng limits cache riêng; giữ các quy tắc M3 đã chốt.
- **Tiêu chuẩn nghiệm thu:** Không tự đổi A, Va, Q-date, 18 tháng, ranking, lịch, basis, chi phí hoặc execution; sai hash thì dừng.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_enriched_sources.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add configs/experiments/m3_strategy_enriched_v1.json scripts/run_m3.py
  git commit -m "feat(bpit-m3): Tạo config thử nghiệm và cache riêng"
  ```

### Task 04 (R2-04) — Thêm --config cho feasibility

- **Giai đoạn:** Stage E
- **File can thiệp:** `scripts/m3_feasibility_variants.py`
- **Nội dung công việc:** Thêm --config, dùng cùng nguồn chỉ số/ngành/scoring/cutoff với runner. Báo official config sau FINANCIAL_CRITERIA_MISSING cho từng segment, gồm median/min và số kỳ N<10.
- **Tiêu chuẩn nghiệm thu:** Counts và lý do loại khớp runner trên fixture; không đọc ngầm config hoặc SQLite baseline khi đã truyền enriched.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_feasibility_config.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add scripts/m3_feasibility_variants.py
  git commit -m "feat(bpit-m3): Thêm --config cho feasibility"
  ```

### Task 05 (R2-05) — Mở rộng regression giá/cutoff/targets

- **Giai đoạn:** Stage E
- **File can thiệp:** `tests/unit/test_m3_cutoff.py`, `tests/unit/test_m3_prices_boundary.py`, `tests/unit/test_m3_engine.py`
- **Nội dung công việc:** Mở rộng tests hiện có cho nguồn enriched, k mới, targets/audit và Q17. Thử thêm giá/lịch tương lai ngoài segment và các phiên lân cận ranh giới.
- **Tiêu chuẩn nghiệm thu:** Future append không đổi Dev; kỳ cuối và NAV bounds đúng, missing limits giữ hành vi đã duyệt; không giảm assertion cũ.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_*.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add tests/unit/test_m3_cutoff.py tests/unit/test_m3_prices_boundary.py tests/unit/test_m3_engine.py
  git commit -m "feat(bpit-m3): Mở rộng regression giá/cutoff/targets"
  ```

### Task 06 (R2-06) — Chuẩn bị verifier và seal hai đoạn

- **Giai đoạn:** Stage E
- **File can thiệp:** `scripts/verify_m3_enriched_run.py`
- **Nội dung công việc:** Viết verifier cho manifest, targets, audit, ledger, cash, holdings, NAV, metrics, controls và hashes. Seal là file riêng; Holdout phải có Dev seal PASS và cùng code/config/inputs.
- **Tiêu chuẩn nghiệm thu:** Fixture sai dòng tiền, date bounds hoặc pin bị phát hiện trước seal; run bytes giữ nguyên và NAV hai đoạn tách riêng.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_enriched_verifier.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add scripts/verify_m3_enriched_run.py
  git commit -m "feat(bpit-m3): Chuẩn bị verifier và seal hai đoạn"
  ```

### Task 07 (R2-07) — Feasibility thật, targets-only và khóa config

- **Giai đoạn:** Stage E
- **File can thiệp:** `configs/experiments/m3_strategy_enriched_v1.json`
- **Nội dung công việc:** Sau khi D được duyệt, chạy feasibility và targets-only cả hai đoạn; kiểm pins, financial_source, git_dirty, candidates/audit/weights và Q17. Review rồi LOCKED, commit code/config và ghi execution SHA.
- **Tiêu chuẩn nghiệm thu:** Dev60/59/1 và Holdout24/23/1 theo lịch; trường hợp số kỳ N<10 tăng được trình owner theo nguồn trước full run.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py scripts/m3_feasibility_variants.py --config configs/experiments/m3_strategy_enriched_v1.json
  & $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment development --targets-only
  & $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment holdout --targets-only
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add configs/experiments/m3_strategy_enriched_v1.json
  git commit -m "feat(bpit-m3): Feasibility thật, targets-only và khóa config"
  ```

### Task 08 (R2-08) — Chạy và seal Development

- **Giai đoạn:** Stage E
- **File can thiệp:** `data/experiments/m3/development/<run_id>/`
- **Nội dung công việc:** Full Dev từ HEAD/config đã khóa; đối chiếu targets-only, ledger, cash, holdings, NAV và controls với baseline. Rà UNIVERSE_TOO_SMALL/LIMIT_DATA_MISSING, verify rồi seal.
- **Tiêu chuẩn nghiệm thu:** NAV kết thúc2023-12-29, pins đúng C/D và controls khớp nghiệp vụ; không thay code/config trước Holdout.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment development
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add data/experiments/m3/development/<run_id>/
  git commit -m "feat(bpit-m3): Chạy và seal Development"
  ```

### Task 09 (R2-09) — Chạy và seal Holdout

- **Giai đoạn:** Stage E
- **File can thiệp:** `data/experiments/m3/holdout/<run_id>/`
- **Nội dung công việc:** Sau Dev seal, chạy full Holdout cùng execution HEAD/config/inputs, khởi tạo NAV riêng, verify và seal. Chỉ commit receipts sau khi hai full run hoàn tất.
- **Tiêu chuẩn nghiệm thu:** NAV kết thúc2025-12-31; pins bằng Dev, không Sharpe. Nếu sửa lỗi code/config phải dùng SHA mới và chạy lại phần chịu ảnh hưởng.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment holdout
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add data/experiments/m3/holdout/<run_id>/
  git commit -m "feat(bpit-m3): Chạy và seal Holdout"
  ```

### Task 10 (R2-10) — Xuất đối sánh M3 theo segment

- **Giai đoạn:** Stage F
- **File can thiệp:** `scripts/export_backtest_comparison_metrics.py`
- **Nội dung công việc:** Đọc baseline và enriched runs/seals, xuất Combined/Financial-only cùng controls theo từng segment. Báo N, cash, failed trades, selected/held, NAV, return, drawdown và cơ sở giá.
- **Tiêu chuẩn nghiệm thu:** Các bảng truy được series và pins; không gộp NAV hai đoạn hoặc dùng performance để chọn lại mô hình; giữ kết quả bất lợi.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_m3_comparison_export.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add scripts/export_backtest_comparison_metrics.py
  git commit -m "feat(bpit-m3): Xuất đối sánh M3 theo segment"
  ```

### Task 11 (R2-11) — Mã hóa policy D-ASS-01

- **Giai đoạn:** Stage S2
- **File can thiệp:** `configs/product/assessment_policy_v1.json`
- **Nội dung công việc:** Chuyển bảng D-ASS-01 thành policy versioned: whitelist18, mandatory/optional, threshold, priority, Peers và cách nhận ô imputed theo policy đã duyệt.
- **Tiêu chuẩn nghiệm thu:** Không tự thêm điểm tổng/penalty hoặc quyết định imputed mới. Ô bắt buộc chưa được phép dùng xử lý đúng mục6.4.3 và8.3 trước verdict thật.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_policy.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add configs/product/assessment_policy_v1.json
  git commit -m "feat(assessment): Mã hóa policy D-ASS-01"
  ```

### Task 12 (R2-12) — Hiện thực điều kiện thị trường

- **Giai đoạn:** Stage S2
- **File can thiệp:** `src/delta_t1/experiments/assessment/rules_market.py`
- **Nội dung công việc:** Hiện thực xu hướng thuận lợi khi mom_63>0 và mom_126>0, đồng thời mom_21>0 hoặc mom_252>0; bất lợi theo điều kiện âm đối xứng. Tổ hợp còn lại mixed; ILLIQUID là cảnh báo trọng yếu.
- **Tiêu chuẩn nghiệm thu:** Ngưỡng 0, missing và mixed đúng; rule results có evidence/status, không dùng cluster ID như thứ hạng hoặc future return.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_market_rules.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/assessment/rules_market.py
  git commit -m "feat(assessment): Hiện thực điều kiện thị trường"
  ```

### Task 13 (R2-13) — Hiện thực tài chính và dòng tiền

- **Giai đoạn:** Stage S2
- **File can thiệp:** `src/delta_t1/experiments/assessment/rules_financial.py`
- **Nội dung công việc:** Hiện thực ROA/net_margin/CFO và các cảnh báo đúng bảng8.3. Chỉ đọc dấu CFO qua tỷ lệ khi NI dương và ratio hợp lệ; watch khi gross_margin<0, current_ratio<1 hoặc revenue_growth<0.
- **Tiêu chuẩn nghiệm thu:** Giá trị bằng ngưỡng không kích hoạt warning; một watch đủ chặn favorable, CFO0 không thuận lợi; imputed/denominator theo policy đã duyệt.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_financial_rules.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/assessment/rules_financial.py
  git commit -m "feat(assessment): Hiện thực tài chính và dòng tiền"
  ```

### Task 14 (R2-14) — Kết hợp eligibility và bốn verdict

- **Giai đoạn:** Stage S2
- **File can thiệp:** `src/delta_t1/experiments/assessment/verdict.py`
- **Nội dung công việc:** Kết hợp eligibility/freshness/model gates với thứ tự INSUFFICIENT_EVIDENCE→CAUTION→RESEARCH_FAVORABLE→WATCH. Optional missing bỏ phép kiểm tương ứng, major warning ưu tiên CAUTION.
- **Tiêu chuẩn nghiệm thu:** Có bảng kiểm bốn verdict và ca biên; thiếu Peers không tự insufficient, FY mới có dữ liệu nhưng chưa có model không fallback năm cũ.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_d_ass_01_rules.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/assessment/verdict.py
  git commit -m "feat(assessment): Kết hợp eligibility và bốn verdict"
  ```

### Task 15 (R2-15) — Dựng rationale và counter-evidence

- **Giai đoạn:** Stage S2
- **File can thiệp:** `src/delta_t1/experiments/assessment/rationale.py`
- **Nội dung công việc:** Dựng drivers/risks/counter_evidence từ templates có rule ID, value, status, unit, kỳ và evidence_ref thuộc18features. Peers là bằng chứng giải thích G4; kiểm replay và mutation Peers.
- **Tiêu chuẩn nghiệm thu:** Lý do truy được nguồn, không text tự do thiếu evidence hoặc đổi verdict do Peers; không mô tả giá trị median như CFO quan sát của doanh nghiệp.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_rationale.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/experiments/assessment/rationale.py
  git commit -m "feat(assessment): Dựng rationale và counter-evidence"
  ```
