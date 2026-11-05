# PLAN — Tính đủ chỉ số tài chính & làm lại trang cổ phiếu (Indicators v1)

> Giao cho agent Claude Code. Repo: `C:\Projects\Intern\SourceCode-CafeF`
> (git worktree của `C:\Projects\Intern\SourceCode`, nhánh `integration/market-financial`).
> Viết ngày 24/10/2026. Đọc hết plan trước khi code.

## 0. Bối cảnh & quyết định của owner (bắt buộc tuân theo)

Owner muốn web demo trở thành **sản phẩm dùng được thật**: mỗi mã có đủ chỉ số
tài chính được **tính ra**, hiển thị gọn, dễ hiểu như CafeF/Vietstock. Không còn
hiển thị "gói review", "vintage", "reviewed periods", hash, package ID trên giao diện chính.

Owner đã duyệt các quyết định sau (ghi vào `docs/DECISIONS.md` thành một mục mới
"D-IND-01", ghi rõ nó **thay thế** các quy tắc cũ cấm inferred shares / proxy EBIT
cho lớp sản phẩm; cập nhật `AGENTS.md` cho khỏi mâu thuẫn):

1. **Công thức chuẩn thị trường VN được chấp nhận**:
   - Số cổ phiếu = vốn góp cổ phiếu phổ thông / 10.000 đ (mệnh giá).
   - EBIT = Lợi nhuận trước thuế + Chi phí lãi vay.
   - P/E, P/B dùng **giá đóng cửa thực tế (raw_close)** của phiên giao dịch cuối cùng ≤ ngày kết thúc năm tài chính.
   - Ưu tiên số **tự tính**; EPS do nguồn công bố chỉ dùng để đối chiếu QA.
2. **Ngân hàng / chứng khoán / bảo hiểm**: vẫn tính EPS, BVPS, P/E, P/B, ROE, ROA, vốn hóa;
   F-score, M-score, Z-score hiển thị **"Không áp dụng"** (không phải "thiếu dữ liệu").
3. **Thứ tự**: tính chỉ số + API + UI trước. **Chưa** chạy lại phân cụm trong lượt này (xem §8).
4. **UI kiểu trang tài chính thật** (spec ở §6).

Ràng buộc kỹ thuật giữ nguyên:
- Không sửa/ghi đè artifacts frozen cũ (A/B/C baseline, handoff 1.172, serving EPS v1–v3, R1).
  Output mới luôn ở thư mục version mới.
- Không cần network/PDF/OCR. Mọi input đã có local.
- Thiếu input ⇒ để `null`, **không bao giờ điền 0**, không forward-fill giữa các năm.
- Mỗi giá trị chỉ số phải truy được về input đã dùng (lưu inputs JSON theo dòng).
- Commit trên nhánh mới; **không push** khi chưa hỏi owner.

## 1. Bước khởi động

1. Chạy `git status` (từ Windows; file `.git` trỏ đường dẫn Windows). Có ~40 file sửa local
   chưa commit (EPS serving, DELTA upgrade UI/API). Commit checkpoint chúng trên nhánh hiện tại
   với message "Checkpoint local EPS serving and DELTA upgrade before indicators v1".
2. Tạo nhánh `feature/indicators-v1` từ checkpoint đó.
3. Đọc nhanh: `README.md`, `docs/CURRENT_STATUS.md` (2 section đầu), `web/README.md` (2 section đầu),
   `web/backend/app/{main,repository,indicators,schemas}.py`, `web/frontend/app/stocks/page.tsx`,
   `web/frontend/components/{indicator-reference,financial-indicators,stock-drawer,snapshot-metrics}.tsx`,
   `web/frontend/lib/{api,types,vi,format}.ts`, `configs/product/indicator_reference_v1.json`.

## 2. Dữ liệu nguồn (đã khảo sát)

| Nguồn | Đường dẫn | Ghi chú |
|---|---|---|
| CafeF field inputs (chính) | `data/financial/history_api_input_review1522_v1/jobs/<job>/symbols/<registry_id>/field-inputs.csv` | Cột dùng: `field, provider_type, symbol, value, year`. Một giá trị/field/năm (đã chọn sẵn HK hợp nhất hoặc K riêng lẻ). Một số file rỗng (<200 bytes) → bỏ qua |
| Bản gộp nháp đã tạo | `data/financial/indicators_v1/cafef-fields-long.csv.gz` | 777.243 dòng, 1.427 mã. Script nháp: `data/financial/indicators_v1/_scratch_aggregate_cafef.py` (~85 giây) → chuyển thành script chính thức |
| Template family | `.../jobs/<job>/results/f5ae2b9bff8017c53091/symbols-readiness.csv` (cột `diagnostic_template_family`) | Regular 1.429, Securities 42, Bank 29, UNKNOWN 22 |
| DStock raw (lấp năm thiếu) | `data/financial/history_dstock_*/raw/*.json` (~528 file) | `{"data":[{code,itemCode,reportType,modelType,numericValue,fiscalDate,...}]}`. Cần mapping `itemCode` → field chuẩn: tìm trong `src/`/`scripts/` (grep `itemCode`), nếu không có thì tự lập bảng mapping và kiểm bằng các năm trùng với CafeF |
| Giá | `data/web/delta-intelligence-v1/terminal.sqlite`, bảng `prices(ticker, security_id, date, adj_close, raw_close, volume, ...)` | 1.499 mã, 2016-01-04 → 2025-12-31, VND (FPT 31/12/2025 raw_close = 95.800). Bảng `securities(ticker,name,exchange)` |
| EPS nguồn công bố (QA) | `data/financial/financial_serving_v1/results/source-period-eps-v3/reported-eps.sqlite` và field `vendor_basic_eps` | Chỉ để đối chiếu |

Coverage CafeF theo năm (số mã có dữ liệu): 2016: 1.158 · 2017: 1.264 · 2018: 1.295 · 2019: 1.323 ·
2020: 1.313 · 2021: 1.355 · 2022: 1.370 · 2023: 1.375 · 2024: 1.386 · 2025: 1.293. Universe 1.522 mã.

50 field có sẵn: `administrative_expense, aggregate_fixed_property_depreciation_amortization,
associate_profit, cash_equity_proceeds_group, cash_nci_contributions, cashflow_interest_adjustment,
cashflow_profit_before_tax, common_share_capital_amount, cost_of_goods_sold, current_assets,
current_liabilities, current_tax_expense, deferred_tax_expense, finance_expense, finance_income,
finance_lease_ppe, gross_profit, gross_revenue, intangible_assets, interest_expense, net_profit,
net_revenue, net_tangible_ppe, noncontrolling_interests, noncontrolling_profit, noncurrent_assets,
noncurrent_liabilities, noncurrent_loans_and_finance_leases, operating_cash_flow, other_expense,
other_income, other_profit, other_short_term_payables, owned_tangible_ppe_accumulated_depreciation,
owned_tangible_ppe_cost, paid_in_capital_amount, parent_net_profit, profit_before_tax, receivables,
reported_operating_profit, retained_earnings, revenue_deductions, selling_expense,
short_term_loans_and_finance_leases, total_assets, total_capital, total_equity, total_liabilities,
vendor_basic_eps, vendor_diluted_eps`.

## 3. Giai đoạn 1 — Bảng input chuẩn

Tạo `scripts/build_indicator_inputs.py` (+ module `src/delta_t1/indicators/inputs.py` nếu hợp kiến trúc):

1. Gộp CafeF field-inputs của 1.522 mã → long table.
2. Parse DStock raw, map `itemCode` → field chuẩn, chỉ dùng để **lấp (mã, năm, field) CafeF không có**.
   Ưu tiên: CafeF HK > CafeF K > DStock. Lưu cột `source` cho mỗi ô.
   Kiểm mapping DStock: trên các ô trùng với CafeF, ≥95% chênh <0,5% với total_assets, net_revenue, total_equity, net_profit; nếu không đạt thì không dùng field đó.
3. Chuẩn hóa dấu: chi phí (`cost_of_goods_sold`, `interest_expense`, `selling_expense`,
   `administrative_expense`, `finance_expense`) lưu thành **số dương** (abs) và ghi chú trong code.
   Kiểm `interest_expense` không lấy nhầm `finance_expense` tổng.
4. Pivot wide: một dòng / (ticker, fiscal_year), kèm `template_family`, `exchange`, `name`.
5. Kiểm tra tự động, ghi `checks.csv`:
   - |total_assets − (total_liabilities + total_equity)| / total_assets < 1%.
   - total_assets > 0; net_revenue ≥ 0.
   - Cờ năm có giá trị nhảy bất thường ×100 so với năm kề (nghi sai đơn vị) → đánh cờ, không tự sửa.
6. Output version mới: `data/financial/indicators_v1/inputs/<run-id>/inputs-wide.parquet`
   (hoặc .csv.gz), `coverage.csv` (ticker × year × field có/không), `checks.csv`, `manifest.json` (hash input).

## 4. Giai đoạn 2 — Engine tính chỉ số

Tạo `src/delta_t1/indicators/compute.py` (hàm thuần, test được) + `scripts/build_indicators.py`.
Ký hiệu: `_t` năm hiện tại, `_p` năm trước; `avg(X) = (X_t + X_p)/2` (nếu thiếu X_p dùng X_t và gắn cờ).

### 4.1 Cơ sở
- `shares = common_share_capital_amount / 10000` (fallback `paid_in_capital_amount / 10000`).
- `parent_ni = parent_net_profit` (fallback `net_profit − noncontrolling_profit`, fallback `net_profit`).
- `parent_equity = total_equity − noncontrolling_interests` (thiếu NCI ⇒ coi 0 chỉ khi field NCI thực sự vắng trong mẫu báo cáo; ghi cờ).
- `price_fy` = raw_close phiên cuối ≤ 31/12/năm (nếu phiên đó cách quá 30 ngày ⇒ null).
- `ebit = profit_before_tax + interest_expense`.
- `ltd = noncurrent_loans_and_finance_leases`; `ppe = net_tangible_ppe (+ finance_lease_ppe nếu có)`;
  `dep = aggregate_fixed_property_depreciation_amortization`; `sga = selling_expense + administrative_expense`.

### 4.2 Chỉ số hiển thị
| Mã chỉ số | Công thức |
|---|---|
| `eps` | parent_ni / shares |
| `bvps` | parent_equity / shares |
| `market_cap` | price_fy × shares |
| `pe` | price_fy / eps (eps ≤ 0 ⇒ null + trạng thái `NEGATIVE_EARNINGS`) |
| `pb` | price_fy / bvps (bvps ≤ 0 ⇒ null + `NEGATIVE_EQUITY`) |
| `roe` | parent_ni / avg(parent_equity) |
| `roa` | net_profit / avg(total_assets) |
| `gross_margin` | gross_profit / net_revenue |
| `net_margin` | net_profit / net_revenue |
| `revenue_growth` | net_revenue_t / net_revenue_p − 1 |
| `profit_growth` | parent_ni_t / parent_ni_p − 1 (parent_ni_p ≤ 0 ⇒ null) |
| `debt_to_equity` | total_liabilities / total_equity |
| `current_ratio` | current_assets / current_liabilities |
| `asset_turnover` | net_revenue / avg(total_assets) |
| `cfo_to_ni` | operating_cash_flow / net_profit |

### 4.3 Piotroski F-score (0–9, cần năm trước; chỉ Regular/UNKNOWN)
ROA dùng `net_profit / total_assets_p`.
1. ROA_t > 0 · 2. CFO_t > 0 · 3. ROA_t > ROA_p · 4. CFO_t/total_assets_p > ROA_t
5. ltd_t/avg(TA)_t < ltd_p/avg(TA)_p (cả hai = 0 ⇒ đạt) · 6. current_ratio_t > current_ratio_p
7. shares_t ≤ shares_p · 8. gross_margin_t > gross_margin_p · 9. asset_turnover_t > asset_turnover_p.
Thiếu ≥1 tín hiệu ⇒ `f_score = null`, nhưng vẫn lưu từng tín hiệu (`f_signals` JSON) để UI hiện "7/8 tín hiệu có dữ liệu" trong phần chi tiết. Đánh giá: ≥7 Mạnh, 4–6 Trung bình, ≤3 Yếu.

### 4.4 Beneish M-score (8 biến; chỉ Regular/UNKNOWN)
- DSRI = (Rec_t/Sales_t)/(Rec_p/Sales_p) · GMI = GM_p/GM_t
- AQI = [1−(CA_t+PPE_t)/TA_t] / [1−(CA_p+PPE_p)/TA_p] · SGI = Sales_t/Sales_p
- DEPI = [Dep_p/(Dep_p+PPE_p)] / [Dep_t/(Dep_t+PPE_t)] · SGAI = (SGA_t/Sales_t)/(SGA_p/Sales_p)
- LVGI = [(CL_t+LTD_t)/TA_t] / [(CL_p+LTD_p)/TA_p] · TATA = (NetProfit_t − CFO_t)/TA_t
- **M = −4,84 + 0,920·DSRI + 0,528·GMI + 0,404·AQI + 0,892·SGI + 0,115·DEPI − 0,172·SGAI + 4,679·TATA − 0,327·LVGI**
- Mẫu số = 0 ⇒ null. Đánh giá: M > −1,78 "Có dấu hiệu bất thường", ngược lại "Bình thường".

### 4.5 Altman Z-score (chỉ Regular/UNKNOWN)
- X1 = (CA−CL)/TA · X2 = retained_earnings/TA · X3 = ebit/TA · X4 = market_cap/total_liabilities · X5 = net_revenue/TA
- **Z = 1,2·X1 + 1,4·X2 + 3,3·X3 + 0,6·X4 + 1,0·X5**. Vùng: <1,81 Nguy hiểm · 1,81–2,99 Cảnh báo · >2,99 An toàn.
- Lưu thêm Z'' (không cần giá): 6,56·X1 + 3,26·X2 + 6,72·X3 + 1,05·(total_equity/total_liabilities) — dùng làm fallback khi thiếu giá, ghi rõ biến thể.

### 4.6 Bank / Securities
Tính `eps, bvps, market_cap, pe, pb, roe, roa, revenue_growth, profit_growth` nếu field có; F/M/Z trả
`status = NOT_APPLICABLE`. Kiểm riêng mapping field của mẫu Bank/Securities (net_revenue có thể vắng → bỏ các chỉ số dựa trên doanh thu, không tính sai). Bảo hiểm nằm trong Regular: lập danh sách mã bảo hiểm (BVH, BMI, PVI, PTI, MIG, BIC, VNR, PGI, ABI, BLI…) và xử lý như ngân hàng.

### 4.7 Trạng thái mỗi ô
`OK` · `MISSING_INPUT` (kèm danh sách field thiếu) · `NOT_APPLICABLE` · `NEGATIVE_EARNINGS` · `NEGATIVE_EQUITY` · `NO_PRICE`. Không có trạng thái "review".

### 4.8 Output
`data/financial/indicators_v1/results/<run-id>/`:
- `indicators.sqlite`: bảng `indicator_values(ticker, fiscal_year, metric, value, status, inputs_json)`
  index (ticker), bảng `company(ticker, name, exchange, template_family, sector_group)`, bảng `latest(ticker, ...)`
  (năm gần nhất có dữ liệu + giá cuối cùng 31/12/2025).
- `indicators-wide.csv` (ticker × year × metric), `coverage-summary.csv`, `qa-report.md`, `manifest.json` (hash input/output).

Phạm vi lượt này: **annual 2016–2025**. Quarterly/TTM để vòng sau (ghi vào roadmap).

## 5. Giai đoạn 3 — QA (bắt buộc trước khi làm UI)

Viết `scripts/verify_indicators.py` (độc lập với engine, tính lại từ inputs-wide):
1. Tính lại ngẫu nhiên ≥500 ô (gồm F/M/Z) và so khớp tuyệt đối.
2. Đối chiếu `eps` tự tính với `vendor_basic_eps`: báo % mã-năm lệch <10%, liệt kê top lệch lớn
   (thường do phát hành thêm CP, cổ phiếu quỹ, mệnh giá khác) vào `qa-report.md`.
3. Outliers: P/E > 500, |ROE| > 200%, Z < −10, M > 10 → liệt kê, không tự xóa.
4. Spot-check thủ công 10 mã: FPT, VNM, HPG, MWG, GAS, VCB, TCB, SSI, BVH, DGC — ghi bảng giá trị năm 2024/2025 vào `qa-report.md` để owner so với CafeF.
5. Bảng coverage cuối theo chỉ số × năm. **Mục tiêu 2025**: ≥90% mã có dữ liệu BCTC có EPS/P/E-hoặc-trạng-thái-hợp-lệ/P/B/ROE; ≥80% mã Regular có F/M/Z. Không đạt ⇒ báo nguyên nhân (field nào thiếu bao nhiêu mã), không hạ mục tiêu ngầm.
6. Unit tests `tests/unit/test_indicators_compute.py`: công thức từng chỉ số trên fixture nhỏ, null propagation, chia 0, EPS âm, bank NOT_APPLICABLE, F-score đủ/thiếu tín hiệu.

**Dừng lại, gửi owner `qa-report.md` + coverage trước khi sang Giai đoạn 4.**

## 6. Giai đoạn 4 — Backend API (FastAPI, `web/backend/app`)

- Repository mới đọc `indicators.sqlite` (read-only, theo ticker, không load toàn bảng mỗi request).
- Endpoints:
  - `GET /api/v2/stocks/{ticker}/overview` → name, exchange, ngành (sector_group), giá cuối & ngày, % thay đổi 1 ngày/1 tháng/YTD, vốn hóa, thẻ chính (eps, pe, pb, roe, f_score, z_score) + rating text.
  - `GET /api/v2/stocks/{ticker}/fundamentals?from=2016&to=2025` → bảng {metric: {year: {value,status}}} + metadata nhóm/đơn vị.
  - `GET /api/v2/stocks/{ticker}/scores/{year}` → chi tiết 9 tín hiệu F, 8 biến M, 5 biến Z.
  - `GET /api/v2/stocks/{ticker}/peers` → 8–10 mã cùng cụm (A/B/C baseline hiện có) hoặc cùng nhóm ngành, kèm pe/pb/roe/vốn hóa.
  - (tuỳ chọn nếu còn thời gian) `GET /api/v2/screener?...` lọc theo pe/pb/roe/f/z.
- Thêm `indicators.sqlite` vào `deploy/render/data-files.txt`, `scripts/publish_hf_data.py` (chỉ chạy `--dry-run`, không upload).
- Giữ endpoint cũ chạy được nhưng frontend mới không dùng các trường review/vintage nữa.
- Tests: mở rộng `tests/unit/test_terminal_api.py` cho các endpoint mới (fixture SQLite nhỏ).

## 7. Giai đoạn 5 — UI trang cổ phiếu (Next.js, `web/frontend`)

Mục tiêu: người dùng phổ thông mở là hiểu. Ngôn ngữ tiếng Việt, câu ngắn.

**Trang `/stocks?ticker=XXX`:**
1. **Header**: Mã · tên công ty · sàn · nhóm ngành; giá đóng cửa + ngày; thay đổi %; vốn hóa (tỷ đồng).
2. **Hàng 6 thẻ chính** (năm gần nhất): EPS (đ) · P/E (lần) · P/B (lần) · ROE (%) · F-score (x/9, badge Mạnh/TB/Yếu) · Z-score (badge An toàn/Cảnh báo/Nguy hiểm).
   Ngân hàng: thay F/Z bằng ROA và BVPS. Mỗi thẻ có icon (i) → tooltip **1 câu mục đích + công thức**, ví dụ:
   - P/E: "Nhà đầu tư trả bao nhiêu đồng cho 1 đồng lợi nhuận. = Giá / EPS."
   - F-score: "Sức khỏe tài chính 0–9 điểm; càng cao càng tốt."
   - Z-score: "Nguy cơ kiệt quệ tài chính; dưới 1,81 là rủi ro cao."
   - M-score: "Dấu hiệu bất thường trong số liệu kế toán; trên −1,78 cần chú ý."
3. **Tabs**:
   - *Tổng quan*: biểu đồ giá (đã có), 6 thẻ, tóm tắt 3 dòng tự sinh (vd "ROE 5 năm trung bình 24%, cao hơn 80% số mã").
   - *Chỉ số tài chính*: bảng **cột = năm 2016→2025, dòng = chỉ số**, nhóm: Định giá · Sinh lời · Tăng trưởng · An toàn tài chính · Điểm sức khỏe. Mỗi dòng có sparkline nhỏ. Định dạng `vi-VN`, đơn vị rõ (đ, %, lần, tỷ đ). Ô trống hiện "—" với tooltip "Chưa có báo cáo năm X" / "Không áp dụng cho ngân hàng" / "Công ty lỗ".
   - *Điểm sức khỏe*: chọn năm → checklist 9 tín hiệu F (✓/✗ + 1 câu), 8 biến M, 5 thành phần Z.
   - *So sánh cùng nhóm*: bảng peers + highlight mã hiện tại.
4. **Footer nhỏ**: "Nguồn: BCTC năm (CafeF/DStock), giá đóng cửa HOSE/HNX/UPCOM. Cách tính" → link mở modal liệt kê công thức. Mọi thông tin kỹ thuật (run-id, hash, nguồn từng ô) chỉ nằm trong modal này.

**Xóa khỏi giao diện chính** (toàn site): các chữ/khái niệm "review", "reviewed", "vintage", "package", "cohort", "pilot", "reference only", hash, trạng thái gate, đoạn diễn giải dài. Rà `lib/vi.ts` và các component: mỗi mô tả ≤ 1 câu. Atlas/Financial/Lab: chỉ làm gọn chữ theo cùng phong cách, không đổi logic.

Giữ: typography/tokens hiện tại, responsive 390px, focus/accessibility, request cache. Dùng ECharts/TanStack sẵn có.

Verification UI: `npm run build` PASS; mở local (`python scripts/start_delta_terminal.py`) và chụp screenshot trang FPT, VCB (ngân hàng), một mã nhỏ thiếu dữ liệu, ở desktop và 390px; cập nhật `scripts/verify_delta_ui.cjs` cho các selector mới.

## 8. Ngoài phạm vi lượt này (ghi vào `docs/ROADMAP.md`)
- Chạy lại phân cụm B/C bằng bộ chỉ số mới; sửa liquidity chi phối cụm A (log-transform + winsorize liquidity_21); ngưỡng coverage cho mã vào cụm.
- Chỉ số quý/TTM; ngày công bố BCTC để làm PIT; backtest M3.
- Deploy public (Render/Vercel/HF upload) — chờ owner duyệt.

## 9. Tài liệu & kết thúc
- Cập nhật `docs/DECISIONS.md` (D-IND-01), `docs/CURRENT_STATUS.md` (section mới ở đầu, ≤12 dòng), `CHANGELOG.md`, `web/README.md` (cách build indicators + chạy web), `scripts/README.md`.
- Chạy targeted tests mới + `test_terminal_api` + `test_indicator_reference`; compileall; `npm run build`.
- Commit theo từng giai đoạn trên `feature/indicators-v1`. Không push.
- Báo cáo cuối cho owner: coverage 2025 theo chỉ số, % EPS khớp nguồn, danh sách vấn đề còn lại, screenshots.

## 10. Checklist nghiệm thu
- [ ] inputs-wide + coverage + checks có manifest/hash, không sửa artifact cũ
- [ ] indicators.sqlite đủ 15 chỉ số + F/M/Z cho 2016–2025, trạng thái rõ cho mọi ô
- [ ] Verifier độc lập PASS; unit tests PASS; qa-report có spot-check 10 mã
- [ ] Coverage 2025 đạt mục tiêu §5.5 hoặc có giải thích theo field
- [ ] API mới + tests PASS
- [ ] Trang cổ phiếu mới: header, 6 thẻ, 4 tabs, tooltip 1 câu, không còn chữ review/vintage/hash trên UI chính
- [ ] Build PASS, screenshots desktop + mobile
- [ ] Docs/DECISIONS/CHANGELOG cập nhật; commit local, chưa push
