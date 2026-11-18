# Hướng dẫn thực hiện công việc — Người 4

**Phạm vi phụ trách:** Frontend Next.js, Báo cáo F và Tài liệu nghiệm thu.  
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

## Chuẩn bị Dữ liệu (Bắt buộc trước khi chạy)

Do tệp cơ sở dữ liệu `indicators.sqlite` có dung lượng ~106 MB (vượt giới hạn 100 MB của GitHub), thư mục `data/` được đưa vào `.gitignore`. Người 1 đã xuất và đóng gói toàn bộ dữ liệu làm giàu và đánh giá.

Bạn chuẩn bị dữ liệu bằng **1 trong 2 cách sau**:
* **Cách 1 (Nhanh nhất & Khuyên dùng):** Tải file `data.zip` (~40 MB do Người 1 bàn giao tại thư mục `Downloads/data.zip` hoặc trên Google Drive / nhóm chat), giải nén vào thư mục gốc của repo sao cho đường dẫn là `data/...`.
* **Cách 2 (Tự sinh từ baseline):** Nếu máy bạn đã có sẵn thư mục `data` gốc baseline, mở terminal chạy 3 lệnh sau để tự sinh toàn bộ dữ liệu trong 30 giây:
  ```powershell
  $env:PYTHONPATH="src"
  python scripts/build_enriched_indicators.py
  python scripts/build_financial_pit_clusters_enriched.py
  python scripts/build_investment_assessment_v1.py
  ```

---

---

## Danh mục các nhiệm vụ chi tiết

### Task 01 (R4-01) — Tổng hợp đối sánh B-PIT

- **Giai đoạn:** Stage F
- **File can thiệp:** `docs/REPORT_BACKTEST.md`
- **Nội dung công việc:** Báo ô điền theo FY/metric, mã–năm theo số ô điền, coverage9/9, n_fit, sizes, thay nhãn/common ARI và đối chứng k=3 từ audit C/D đã verify.
- **Tiêu chuẩn nghiệm thu:** Số liệu khớp pins; phân biệt tác động mở cohort, refit và ROE scoring; không sửa baseline.
- **Lệnh kiểm tra / Test:**
  ```powershell
  git diff --check
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add docs/REPORT_BACKTEST.md
  git commit -m "docs(bpit-m3): Tổng hợp đối sánh B-PIT"
  ```

### Task 02 (R4-02) — Tổng hợp đối sánh M3

- **Giai đoạn:** Stage F
- **File can thiệp:** `docs/REPORT_BACKTEST.md`
- **Nội dung công việc:** Nhập bảng đối sánh Combined/Financial-only/controls từ Người2 theo từng segment: N, cash, trades, NAV, return, drawdown. Ghi price basis và các giới hạn.
- **Tiêu chuẩn nghiệm thu:** Không gộp NAV hoặc báo Sharpe ở Dev/Holdout; kết quả bất lợi và source references được giữ đủ.
- **Lệnh kiểm tra / Test:**
  ```powershell
  git diff --check
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add docs/REPORT_BACKTEST.md
  git commit -m "docs(bpit-m3): Tổng hợp đối sánh M3"
  ```

### Task 03 (R4-03) — Hoàn tất hồ sơ bàn giao và tài liệu liên quan

- **Giai đoạn:** Stage F
- **File can thiệp:** `docs/REPORT_BACKTEST.md`, `docs/DECISIONS.md`, `CHANGELOG.md`
- **Nội dung công việc:** Ghi mục4 công việc còn lại, phase status/evidence, config/HEAD/hash/run IDs và đường dẫn nhận có quyền. Cập nhật Decisions/Changelog khi quy tắc được triển khai; chuẩn bị bộ bàn giao F.
- **Tiêu chuẩn nghiệm thu:** Bộ C/D/E và đối sánh đủ cho Assessment; owner review theo nguồn trước cân nhắc promote. ADR/Changelog đi cùng PR đổi behavior liên quan.
- **Lệnh kiểm tra / Test:**
  ```powershell
  git diff --check
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add docs/REPORT_BACKTEST.md docs/DECISIONS.md CHANGELOG.md
  git commit -m "docs(bpit-m3): Hoàn tất hồ sơ bàn giao và tài liệu liên quan"
  ```

### Task 04 (R4-04) — Types và trạng thái dữ liệu frontend

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/lib/types.ts`
- **Nội dung công việc:** Bổ sung types theo response đã nghiệm thu S4: status, dates, provenance,18features, Peers và history. Đọc tài liệu Next local theo AGENTS trước khi code.
- **Tiêu chuẩn nghiệm thu:** Typecheck đạt, null/status mapping đúng; không dùng fixture làm fallback production hoặc tạo contract API khác.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/lib/types.ts
  git commit -m "feat(assessment): Types và trạng thái dữ liệu frontend"
  ```

### Task 05 (R4-05) — Verdict và availability states

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/verdict-badge.tsx`, `web/frontend/components/stock/assessment-status.tsx`
- **Nội dung công việc:** Hiển thị bốn verdict, loading/error/insufficient/stale, demo/as_of/session/context bằng text và trạng thái accessible. Reset kết luận cũ khi đổi mã.
- **Tiêu chuẩn nghiệm thu:** Giá trị lấy đúng API, pending/404/503/409 rõ; không đồng nhất availability với verdict.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/verdict-badge.tsx web/frontend/components/stock/assessment-status.tsx
  git commit -m "feat(assessment): Verdict và availability states"
  ```

### Task 06 (R4-06) — Một biểu đồ chuyển đổi chỉ số

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/single-feature-chart.tsx`
- **Nội dung công việc:** Một vùng chart với selector18feature hoặc nhóm cùng unit/tần suất/basis. Trục tài chính theo FY, market theo snapshot; chỉ vẽ điểm hợp lệ tại as_of.
- **Tiêu chuẩn nghiệm thu:** Không ghép line khác đơn vị/tần suất; gap giữ trống, selector không tính lại verdict hoặc model labels.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/single-feature-chart.tsx
  git commit -m "feat(assessment): Một biểu đồ chuyển đổi chỉ số"
  ```

### Task 07 (R4-07) — Lookback và thông tin coverage

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/single-feature-chart.tsx`
- **Nội dung công việc:** Thêm selector5/10 năm mặc định10 tính lùi từ as_of; hiển thị coverage thực và thông tin ngày/status/nguồn. Query theo hợp đồng API.
- **Tiêu chuẩn nghiệm thu:** Đổi lookback không đổi as_of/verdict/evidence; thiếu kỳ chỉ hiện phần thực có, không tạo dữ liệu.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/single-feature-chart.tsx
  git commit -m "feat(assessment): Lookback và thông tin coverage"
  ```

### Task 08 (R4-08) — Bảng Peers theo đặc trưng

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/peer-comparison-table.tsx`
- **Nội dung công việc:** Render basis/count/date/source và median/IQR từng metric;0–2 ghi thiếu đối chứng, đúng3 có median. Missing B-PIT không lập Peers, dữ liệu lấy từ artifact.
- **Tiêu chuẩn nghiệm thu:** Không gọi legacy peers hoặc tính lại nhóm trên client; thiếu Peers không tự đổi verdict.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/peer-comparison-table.tsx
  git commit -m "feat(assessment): Bảng Peers theo đặc trưng"
  ```

### Task 09 (R4-09) — Bảng chi tiết 18 đặc trưng

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/assessment-feature-table.tsx`
- **Nội dung công việc:** Bảng đủ9A+9B với value/unit/period/status/coverage/ref, phân biệt observed/imputed/missing/NOT_APPLICABLE. Dùng formatters và primitives hiện có.
- **Tiêu chuẩn nghiệm thu:** Không thêm metric ngoài18, null khác0; ô imputed có provenance, optional missing không bị trình bày như giá trị quan sát.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/assessment-feature-table.tsx
  git commit -m "feat(assessment): Bảng chi tiết 18 đặc trưng"
  ```

### Task 10 (R4-10) — Giải thích tín hiệu và rủi ro

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/rationale-card.tsx`
- **Nội dung công việc:** Render drivers/risks/counter_evidence từ response, kèm nguồn/ngày/status, giải thích bốn verdict và tín hiệu trái chiều.
- **Tiêu chuẩn nghiệm thu:** Không sinh text thiếu evidence hoặc tính score/đổi rule trên client; Peers chỉ bổ sung giải thích.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/rationale-card.tsx
  git commit -m "feat(assessment): Giải thích tín hiệu và rủi ro"
  ```

### Task 11 (R4-11) — Nguồn và chất lượng dữ liệu

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/evidence-provenance-modal.tsx`
- **Nội dung công việc:** Expander/modal nguồn cạnh chart/bảng, ghi FY/snapshot/usable/as_of/status/revision/evidence. Hỗ trợ keyboard/focus và link phù hợp.
- **Tiêu chuẩn nghiệm thu:** Không lộ token/absolute local paths hoặc tạo dashboard QA riêng; long references đọc được trên mobile.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/evidence-provenance-modal.tsx
  git commit -m "feat(assessment): Nguồn và chất lượng dữ liệu"
  ```

### Task 12 (R4-12) — Ghép panel đánh giá

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/components/stock/assessment-panel.tsx`
- **Nội dung công việc:** Ghép verdict, A/B profiles, một chart, bảng18feature, Peers, rationale, provenance và empty states trong panel Assessment.
- **Tiêu chuẩn nghiệm thu:** Panel read-only, không compute/fit; tại một thời điểm một chart, case stale/insufficient hiển thị đúng.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/components/stock/assessment-panel.tsx
  git commit -m "feat(assessment): Ghép panel đánh giá"
  ```

### Task 13 (R4-13) — Tab, API và URL state

- **Giai đoạn:** Stage S5
- **File can thiệp:** `web/frontend/app/stocks/page.tsx`, `web/frontend/lib/api.ts`
- **Nội dung công việc:** Thêm tab thứ5, nối API và URL state ticker/tab/metric/lookback. Xử lý409 reset/reload và race A→B/Back; giữ các tab hiện hữu.
- **Tiêu chuẩn nghiệm thu:** Response mã cũ không ghi đè mã mới; revision lock đúng; lookback chỉ đổi history, không có nút chọn as_of hoặc mode công khai.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/app/stocks/page.tsx web/frontend/lib/api.ts
  git commit -m "feat(assessment): Tab, API và URL state"
  ```

### Task 14 (R4-14) — UAT và regression giao diện

- **Giai đoạn:** Stage S6
- **File can thiệp:** `web/frontend/`, `tests/integration/`
- **Nội dung công việc:** UAT FPT+mã hợp lệ khác, VCB/mã mới, stale/current fixtures, mismatch/missing; kiểm18selector5/10, một chart, navigation, mobile/keyboard/theme. Ghi rõ manual và automated.
- **Tiêu chuẩn nghiệm thu:** Typecheck/build và ca nghiệm thu đạt; screenshots/response đúng pins, không bỏ case fail để ghi PASS.
- **Lệnh kiểm tra / Test:**
  ```powershell
  npm --prefix web/frontend run typecheck
  npm --prefix web/frontend run build
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/frontend/ tests/integration/
  git commit -m "feat(assessment): UAT và regression giao diện"
  ```

### Task 15 (R4-15) — Hướng dẫn và hồ sơ nghiệm thu

- **Giai đoạn:** Stage S6
- **File can thiệp:** `docs/HUONG_DAN_SU_DUNG_TOOL_DANH_GIA_DAU_TU.md`, `README.md`, `docs/README.md`
- **Nội dung công việc:** Hướng dẫn demo, tra mã, bốn verdict, Peers/history/nguồn; setup/commands/pins/coverage/limitations/rollback. Tổng hợp API/UI/verifier/UAT evidence và index.
- **Tiêu chuẩn nghiệm thu:** Giữ M2/M3/artifact frozen, công bố đúng phần đạt/chưa đạt; production release theo approval của kế hoạch nguồn, không tự deploy.
- **Lệnh kiểm tra / Test:**
  ```powershell
  git diff --check
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add docs/HUONG_DAN_SU_DUNG_TOOL_DANH_GIA_DAU_TU.md README.md docs/README.md
  git commit -m "docs(assessment): Hướng dẫn và hồ sơ nghiệm thu"
  ```
