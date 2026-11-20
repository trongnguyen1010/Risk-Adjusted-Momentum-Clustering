# Báo cáo tổng kết kỹ thuật và hướng dẫn phát hành tính năng Investment Assessment

## 1. Thông tin chung

* **Dự án:** DELTA / Risk-Adjusted Momentum Clustering.
* **Tài liệu tham chiếu:**
  - `docs/KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md` (Giai đoạn A–F)
  - `docs/Ke_hoach_Output_DELTA_Investment_Assessment.md` (Giai đoạn S0–S6, Quy chuẩn D-ASS-01)
  - `configs/product/assessment_policy_v1.json` & `configs/product/assessment_release_v1.json`
* **Nhánh tích hợp:** `feature/indicators-v1`.
* **Phạm vi báo cáo:** Tổng hợp kết quả kiểm tra, khắc phục sai lệch dữ liệu Assessment, đồng bộ hóa bộ quy tắc D-ASS-01, tối ưu giao diện và xác minh toàn bộ hệ thống trước khi phát hành.

---

## 2. Đánh giá nguyên nhân gốc rễ và tình trạng dữ liệu nguồn

### 2.1. Dữ liệu nguồn và kết quả làm giàu (Giai đoạn A–F)
Kiểm tra toàn vẹn trên các artifact nguồn cho thấy dữ liệu đầu vào và kết quả thử nghiệm M3 trước đó vẫn đảm bảo tính chính xác:
* **Dữ liệu chỉ số tài chính làm giàu (Giai đoạn C):** `data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/indicators.sqlite` bảo toàn đủ 319.620 dòng, hoàn tất làm giàu 1.045 mã–năm (1.111 ô trạng thái `IMPUTED_MEDIAN`) theo đúng bảng ngày khả dụng `availability.csv`.
* **Mô hình & nhãn phân cụm tài chính B-PIT Enriched (Giai đoạn D):** `data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01/` (K-Means `k=3`, 0 lỗi rò rỉ `fit_leaks = 0`, SHA-256 `labels.csv`: `384e36e4521700acb92c8bd69f38204f782e9ab269ba80fe18a6e283a6cf2e35`).
* **Thử nghiệm & đối sánh M3 (Giai đoạn E–F):** Các lượt chạy Development (`20261118T165114Z-46fc18c0`), Holdout (`20261118T170517Z-46fc18c0`) và Comparison (`20261118T173627755165Z`) giữ nguyên trạng thái đã khóa (`LOCKED` / `seal.json`).

### 2.2. Nguyên nhân sai lệch trên artifact Assessment trước đây
Sai lệch trên bộ artifact `assessment_v1_run01` trước đây không xuất phát từ dữ liệu nguồn B-PIT, mà do hai nguyên nhân trong tầng tạo artifact S1/S3:
1. Tệp `src/delta_t1/experiments/assessment/inputs.py` trước đây giữ nguyên khối giả lập demo (`0.1` cho toàn bộ 9 chỉ số thị trường và cụm `#0` cho mọi mã) thay vì nạp dữ liệu quan sát thị trường A v4 thực tế.
2. Tệp điều phối `src/delta_t1/experiments/investment_assessment_v1.py` trước đây sử dụng logic xếp loại giản lược theo số hiệu cụm thay vì nối trực tiếp vào mô-đun quy tắc D-ASS-01 (`rules_market.py`, `rules_financial.py`, `verdict.py`, `rationale.py`).

---

## 3. Các hạng mục kỹ thuật đã xử lý

### 3.1. Kết nối dữ liệu thị trường A v4 thực tế và kiểm soát đầu vào (`inputs.py`)
* **Gỡ bỏ khối giả lập:** Loại bỏ hoàn toàn giá trị hằng số `0.1` và cụm mặc định `#0`.
* **Nạp dữ liệu A v4 thực tế:** Kết nối trực tiếp nguồn quan sát thị trường A v4 tại phiên `2025-12-31` từ bundle v4 (`terminal.sqlite` hoặc tệp trích xuất đồng bộ `data/web/delta-intelligence-v4/market_observations_v4.jsonl`), lấy đúng 9 đặc trưng thị trường (`mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `downside_vol_63`, `mdd_126`, `beta_126`, `liquidity_21`), nhãn cụm A v4 thực tế (`0, 1, 2` hoặc `None` nếu không có quan sát tại phiên chốt) và cờ thanh khoản (`LIQUID` / `ILLIQUID`).
* **Thực thi kiểm tra độ tươi 18 tháng:** Kích hoạt hàm `stale_after(latest_fy, 18)` để chặn 54 mã chỉ có báo cáo tài chính quá hạn 18 tháng tại `as_of = 2026-01-02`.
* **Xác minh mẫu số lợi nhuận và tỷ lệ dòng tiền:** Trích xuất trực tiếp `net_profit@t` từ `inputs_json` trong `indicators.sqlite` để kiểm tra điều kiện dòng tiền `cfo_to_ni` theo đúng mục 8.3. Các mã có FY mới nhất (2025) khả dụng trước `2026-01-02` nhưng chưa có mô hình B-PIT FY2025 (3 mã) được trả về `INSUFFICIENT_EVIDENCE`, không tự ý lùi về mô hình năm cũ.

### 3.2. Tích hợp bộ quy tắc D-ASS-01 (`investment_assessment_v1.py`)
* Nối trực tiếp `InvestmentAssessmentEngine` với các hàm chuẩn hóa của D-ASS-01 (`evaluate_market`, `evaluate_financial`, `evaluate_verdict`, `build_rationale`).
* Tuân thủ thứ tự ưu tiên phân loại cố định: `INSUFFICIENT_EVIDENCE` ➜ `CAUTION` (`LOW_PRIORITY`) ➜ `RESEARCH_FAVORABLE` (`WORTH_CONSIDERING`) ➜ `WATCH` (`MONITOR`).
* Nhóm so sánh tương đồng (`Peers` theo mục 6.3) được tính từ dữ liệu A v4 và B-PIT thực tế theo từng đặc trưng, chỉ dùng cho mục đích giải thích G4 và không làm thay đổi kết luận đánh giá.

### 3.3. Bổ sung chuỗi lịch sử thị trường (`history.py`)
* Mở rộng `feature_history.jsonl` để lưu đầy đủ chuỗi lịch sử của cả 9 chỉ số tài chính (FY2016–FY2024) và 9 chỉ số thị trường A v4 tại các kỳ cuối năm (2019–2025), bảo toàn nguyên trạng dữ liệu thiếu và không nội suy.

### 3.4. Phân bổ kết quả thực tế trên 1.428 mã cổ phiếu (`as_of = 2026-01-02`)
| Mã trạng thái (Artifact / API) | Nhãn hiển thị | Số lượng | Phân tích phân bổ |
|---|---|---:|---|
| `WORTH_CONSIDERING` / `RESEARCH_FAVORABLE` | **Đáng cân nhắc đầu tư** | **67** | Thỏa mãn đồng thời xu hướng thị trường thuận lợi, ROA/biên ròng/CFO dương, thanh khoản `LIQUID` và không có cảnh báo rủi ro (ví dụ: `MWG`, `VNM`, `ABT`). |
| `MONITOR` / `WATCH` | **Cần theo dõi** | **448** | Đủ dữ liệu bắt buộc nhưng xu hướng thị trường và tài chính chưa đồng thuận hoặc phát sinh cảnh báo theo dõi (ví dụ: `FPT`, `HPG`, `AAA`). |
| `LOW_PRIORITY` / `CAUTION` | **Chưa nên ưu tiên đầu tư** | **587** | Phát sinh cảnh báo trọng yếu `ILLIQUID` (370 mã), lợi nhuận dương nhưng `CFO/NI < 0` (130 mã), hoặc đồng thời cả hai (87 mã) (ví dụ: `A32`). |
| `INSUFFICIENT_EVIDENCE` | **Không đủ cơ sở đánh giá** | **326** | Thiếu báo cáo trong hạn 18 tháng (54 mã), chưa có BCTC khả dụng (66 mã), thiếu nhãn B-PIT hợp lệ cho kỳ mới nhất (162 mã), hoặc thiếu dữ liệu/nhãn A v4 tại `2025-12-31` (44 mã) (ví dụ: `AAM`, `AAH`). |

### 3.5. Khắc phục lỗi và chuẩn hóa giao diện Frontend (Next.js)
* **Sửa lỗi tương phản ở chế độ tối (Dark Mode):** Thay thế các biến CSS không tồn tại trong `web/frontend/app/globals.css` (`--foreground`, `--border-subtle`, `--surface-muted`) bằng đúng các biến design tokens hiện hành (`--text`, `--text-2`, `--muted`, `--line`, `--surface-2`) tại `assessment-status.tsx` và `rationale-card.tsx`.
* **Loại bỏ khoảng trắng thừa và khối lặp:** Thay thế class `.state-box` (vốn áp `min-height: 220px` căn giữa) trên các thẻ Drivers, Risks và cụm bằng cấu trúc `.panel` + `.section-gap` căn lề trái gọn gàng; loại bỏ khối tóm tắt kết luận bị lặp giữa `assessment-status.tsx` và `rationale-card.tsx`.
* **Chuẩn hóa ngôn ngữ sản phẩm và hiển thị bảng:**
  - Loại bỏ hoàn toàn chữ `demo` trên toàn bộ component `web/frontend/components/stock/*.tsx`, chuẩn hóa nhãn ngữ cảnh thành `"Mô phỏng tại ngày 02/01/2026"`.
  - Sửa lỗi dính nhãn đơn vị (`ROERATIO`) trong `peer-comparison-table.tsx` bằng cấu trúc `.metric-name` + `.unit-hint`.
  - Hiển thị `"Chưa có"` khi giá trị cụm là `null` trong `assessment-panel.tsx` thay vì mặc định `Cụm #0`.
  - Sử dụng nhãn `Đáng cân nhắc đầu tư` cho `RESEARCH_FAVORABLE`, đồng bộ 4 trụ cột tiêu chí D-ASS-01, biểu đồ lịch sử (`single-feature-chart.tsx`) và bảng chi tiết (`assessment-feature-table.tsx`) cho đủ 18 đặc trưng.

---

## 4. Định danh phiên bản và mã băm phát hành (Release Pins)

* **Release ID:** `assessment_v1_run01`
* **Release Revision:** `assessment-v1-run01-20261116`
* **Assessment Context / As-of:** `SIMULATED_AS_OF` / `2026-01-02` (Phiên giá `2025-12-31`)
* **Manifest SHA-256:** `6bdb5b01cce44c7a87f9fb4545cf4854859983bfa760fadbf52357102018b484`
* **Deterministic Content SHA-256:** `16b259111f69fd0be7bc84fa3aec844677755b1cb488560184252b6aedbae787`
* **Tệp đồng bộ:** `configs/product/assessment_release_v1.json`, `data/experiments/assessment/assessment_v1_run01/manifest.json` và `data/experiments/assessment/verification.json`.

---

## 5. Kết quả kiểm thử và đối chiếu tự động

| Hạng mục kiểm thử | Lệnh / Công cụ kiểm tra | Kết quả | Chi tiết |
|---|---|---|---|
| Xác thực Artifact độc lập | `python scripts/verify_investment_assessment_v1.py --dir data/experiments/assessment/assessment_v1_run01` | **PASS (1.428/1.428)** | Toàn bộ 4 tệp đầu ra khớp SHA-256, 0 lỗi rò rỉ dữ liệu tương lai, đầy đủ trung vị Peers thực. |
| Quy tắc D-ASS-01 | `python -m unittest tests/unit/test_d_ass_01_rules.py` | **PASS (19/19)** | Xác minh ma trận quyết định, thứ tự ưu tiên 4 verdict và cổng G1. |
| Bộ Unit Tests Assessment | `python -m unittest discover -s tests/unit -p "test_*assessment*.py"` | **PASS (118/118)** | Xác minh Inputs, Market/Financial Rules, Peers, History, API, Cache, Schemas. |
| Bộ Integration Tests Assessment | `python -m unittest discover -s tests/integration -p "test_assessment*.py"` | **PASS (9/9)** | Kiểm thử end-to-end Builder, Real Handoff (`FPT`, `A32`, `AAM`, `VCB`) và Endpoints. |
| Biên dịch Python | `python -m compileall -q src tests scripts run.py` | **PASS (0 lỗi)** | Không phát sinh lỗi cú pháp trên mã nguồn Python. |
| Kiểm tra kiểu Frontend | `node node_modules/typescript/bin/tsc --noEmit` (tại `web/frontend`) | **PASS (0 lỗi)** | Không phát sinh lỗi kiểu TypeScript/React; 0 chuỗi `"demo"` còn sót trong `components/stock/*.tsx`. |
| Kiểm thử giao diện UAT (Playwright) | `node tests/integration/verify_assessment_ui.cjs` | **PASS (10/10)** | Đạt đủ 10 kịch bản: 18 đặc trưng, chuyển lookback 5/10 năm, 1 biểu đồ, `INSUFFICIENT_EVIDENCE`, missing ticker, revision 200/409, stale fixture, mobile 390px, keyboard focus, light theme. |

**Giới hạn phạm vi ghi nhận minh bạch:**
* Do chế độ đánh giá hiện đang ở ngữ cảnh mô phỏng hồi cứu `SIMULATED_AS_OF` (`2026-01-02`), cờ `runtime_enabled` trong `configs/product/assessment_policy_v1.json` vẫn giữ `false` theo đúng hợp đồng kiểm thử `test_assessment_policy.py` cho đến khi có phê duyệt chuyển sang vận hành `CURRENT_AS_OF`.
* Việc kiểm thử end-to-end trên môi trường production (Render + Vercel) cần được thực hiện lại sau khi 5 tệp mới trong `data/experiments/assessment/assessment_v1_run01/` được tải lên Hugging Face và nhánh `feature/indicators-v1` được merge vào `main`.

---

## 6. Thành phần bàn giao và quy trình phát hành

### 6.1. Thành phần bàn giao
1. **Mã nguồn và cấu hình trên nhánh Git `feature/indicators-v1`:** Bao gồm các bản sửa tại `src/delta_t1/experiments/`, `web/frontend/components/stock/`, bộ kiểm thử, tài liệu và cấu hình khóa mã băm `configs/product/assessment_release_v1.json`.
2. **Gói dữ liệu ngoại tuyến `data_complete.zip` (chỉ chứa các đầu ra mới, không trùng lặp tệp gốc đã có trên Hugging Face):**
   - `data/experiments/assessment/assessment_v1_run01/` (5 tệp đầu ra chính cho Web/API) và `data/experiments/assessment/verification.json`
   - `data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/` (dữ liệu 9 chỉ số tài chính sau làm giàu — Giai đoạn C)
   - `data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01/` (nhãn và mô hình B-PIT sau làm giàu — Giai đoạn D)
   - `data/experiments/m3/` (`development/20261118T165114Z-46fc18c0`, `holdout/20261118T170517Z-46fc18c0`, `comparison/20261118T173627755165Z` — Giai đoạn E–F)
   - *(Các tệp gốc đã có sẵn trên Hugging Face như `data/web/delta-intelligence-v4/terminal.sqlite`, `indicators_v1`, `availability.csv` và `b_pit_v1` không đóng gói lại để tránh trùng lặp hoặc ghi đè.)*

### 6.2. Các bước triển khai phát hành (Deployment)
1. **Kéo mã nguồn mới:** `git pull origin feature/indicators-v1`.
2. **Giải nén và xác thực dữ liệu:** Giải nén `data_complete.zip` vào thư mục gốc repository và chạy `python scripts/verify_investment_assessment_v1.py --dir data/experiments/assessment/assessment_v1_run01` để xác nhận `verification_status: "PASS"` và khớp `manifest_sha256`.
3. **Đồng bộ lên Hugging Face Dataset (`ngyen/delta-intelligence-data`):** Cập nhật 5 tệp mới trong `data/experiments/assessment/assessment_v1_run01/` (`manifest.json`, `assessments.jsonl`, `peer_benchmarks.csv`, `coverage.csv`, `feature_history.jsonl`) và bảo đảm `deploy/render/data-files.txt` có đủ 5 đường dẫn này.
4. **Hợp nhất và Deploy:** Tạo Pull Request merge nhánh `feature/indicators-v1` vào `main` để kích hoạt deploy trên Render (Backend) và Vercel (Frontend), sau đó thực hiện UAT nghiệm thu trên đường dẫn `/stocks?ticker=MWG&tab=assessment` và `/stocks?ticker=FPT&tab=assessment`.
