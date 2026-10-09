# Handbook chỉ số và dữ liệu cần thu thập

Cập nhật: **09/10/2026**. Phạm vi chính: **EPS, P/E, P/B, F-score, M-score,
EM Z-double-prime** của workstream financial; phụ lục ghi các market features
đã có. Dùng tài liệu này để thiết kế crawler, mapping, review và calculator.
Đây là diễn giải implementation hiện có, **không phê duyệt variant mới hoặc mở
financial cluster**. Khi sửa code/policy, cần cập nhật handbook cùng version.

## 1. Đọc tài liệu nào và dùng để làm gì?

Project đã có tài liệu nền tảng, nhưng trước handbook này chưa gom đầy đủ công
thức từng thành phần với field keys và checklist crawl trong một nơi.

| Tài liệu | Vai trò |
|---|---|
| [Financial feature contract](FINANCIAL_FEATURE_CONTRACT.md) | Quyết định variant, accounting basis, PIT và acceptance; ưu tiên khi có xung đột với phần diễn giải |
| **Handbook này** | Công thức, ý nghĩa, raw inputs, nguồn/trang cần lấy, QA và code tương ứng |
| [Data contract](../DATA_CONTRACT.md) | Schema, identity, instant/duration, provenance và units |
| [CafeF source note](../crawl/sources/CAFEF.md) | Discovery, endpoint semantics, giới hạn và các kết quả kiểm nguồn |
| [Hướng dẫn financial readiness](../crawl/FINANCIAL_READINESS_USER_GUIDE.md) | Lệnh PowerShell/Python, cache/OCR/template/review/verify |
| [Feature system](../FEATURE_SYSTEM.md) | Registry, readiness, transform và ranh giới clustering |
| [Literature matrix](LITERATURE_MATRIX_COMPLETE.md) | Cơ sở hướng nghiên cứu; không thay thế công thức score |

Ba câu hỏi phải tách riêng: **đã crawl được số?**, **đã tính được reference?**,
**đã đủ điều kiện dùng tại một thời điểm lịch sử?** Một PDF đầy đủ có thể trả lời
hai câu đầu nhưng chưa trả lời câu cuối nếu thiếu ngày công bố/version evidence.

## 2. Bảng nhu cầu tổng hợp

`t` là năm tài chính, không phải ngày crawl. Các kỳ/comparatives phải compatible
về issuer, consolidated scope, VAS, units và revision basis.

| Nhóm | Mục đích | Inputs chủ yếu | Kỳ cần | Implementation hiện có |
|---|---|---|---|---|
| EPS | Lợi nhuận phân bổ cho một cổ phiếu bình quân | EPS numerator, weighted basic/diluted shares, EPS note | Đúng kỳ3/6/9/12tháng; TTM có bridge riêng | Disclosed basic, period/basic+diluted và reported TTM references |
| P/E | Giá so với lợi nhuận trên mỗi cổ phiếu | Raw price, EPS cùng share basis, share-event evidence | Ngày định giá và12tháng trailing | Annual reported-basis và TTM references riêng; strict PE chưa tích hợp bulk50 |
| P/B | Giá/vốn hóa so với equity cổ đông thường | Raw price, parent common equity, common shares, events | Balance date và valuation date phải giải thích | Reported book snapshot/current-shares/gross ESOP bridge references riêng |
| F-score | Chín tín hiệu lợi nhuận, cash flow, leverage/liquidity, hiệu suất | NI/CFO, assets, LTD, CA/CL, issuance, sales/gross profit | Flows`t,t−1`; assets`t,t−1,t−2` | Strict signal calculator và VAS reported-profit adaptation |
| M-score | Diagnostic về thay đổi chất lượng số liệu kế toán | Receivables, sales/gross profit, assets/PPE/depreciation, SG&A, NI/CFO/debt | Chủ yếu`t,t−1` | VAS sensitivity eight-variable model; chưa fraud threshold |
| EM Z'' | Diagnostic về thanh khoản/lợi nhuận/equity/leverage | CA/CL/TA, retained earnings, EBIT, total equity/liabilities | Một annual report vintage | EM variant có constant3,25; chưa distress threshold |

Annual FY2025 F-score cần asset balances cuối2023/2024/2025. Vì vậy nên tìm
full BCTC2025 và supporting2024; thêm2023 khi comparative2024 không đủ. Không
nhất thiết tải ba PDF nếu hai tài liệu đã có đủ cột so sánh được review. Score
2021–2025 có thể cần history2019–2025. Đủ số năm chưa chứng minh đủ raw fields.

## 3. EPS: numerator và cổ phiếu bình quân

**Công thức arithmetic:**

```text
Basic EPS   = N / WA_basic
Diluted EPS = N_diluted / WA_diluted
```

`N` là lợi nhuận phân bổ cho common shareholders sau các điều chỉnh được thuyết
minh; không mặc định bằng total consolidated NI hoặc parent NI. Công thức tổng
quát cho diluted có thể cần numerator riêng; calculator reference hiện nhận
**một numerator dùng chung**, chỉ dùng khi evidence xác nhận basis đó phù hợp.

**Cần crawl:** full EPS note cho đúng kỳ, parent profit, các khoản trích quỹ/điều
chỉnh, weighted-average basic shares, diluted shares/potential dilution, EPS in
trên báo cáo và share adjustment/restatement notes. Đơn vị numerator **VND**,
shares **SHARES**, EPS **VND/share**. Số cổ phiếu cuối kỳ không thay WA shares.

Workflow50 hiện tính **disclosed basic EPS annual** từ
`eps_adjusted_earnings_numerator / weighted_average_basic_shares`, rồi kiểm
rounded EPS bằng `vendor_basic_eps` lấy từ đúng PDF. Field có chữ `vendor` ở đây
là comparison key, không có nghĩa một EPS website bất kỳ được accepted.
Không review dilution thì `diluted_eps=null`; basic vẫn có thể tính được.

QA: numerator bridge theo EPS note, WA>0, cùng share basis/kỳ/version; rounding
`ROUND_HALF_UP` tới1VND/share trong reference. Printed EPS khớp không chứng minh
normalized numerator, dilution, PIT hoặc production acceptance. Quỹ chưa ước
tính giữ unknown, không suy bằng0; âm EPS có thể tồn tại nhưng PE<=0 bị chặn.

Code: [annual EPS/Z](../../src/delta_t1/features/financial_reference.py),
[disclosed/period EPS](../../src/delta_t1/features/financial_vas_reference.py).

### EPS TTM trong project

Variant **REPORTED_NUMERATOR_SHARE_DAYS_TTM_REFERENCE** hiện ghép năm calendar
trước và YTD hiện tại/cùng kỳ trước, không phải universal four-quarter adapter:

```text
N_TTM = N_FY + N_current_YTD − N_prior_YTD
share_days_TTM = WA_FY*d_FY + WA_current_YTD*d_current_YTD − WA_prior_YTD*d_prior_YTD
d_TTM = d_FY + d_current_YTD − d_prior_YTD
WA_TTM = share_days_TTM / d_TTM
EPS_TTM_reference = N_TTM / WA_TTM
```

`d` là số ngày calendar inclusive trong **đúng kỳ**, không luôn365/181. Phải
bridge bonus/share basis, scope và parent-earnings comparatives. Bộ FY2025 +
H12026 − H12025 cần numerator/WA notes của cả ba kỳ, công bố từng source,
deduction policy, period boundaries và scope/share-basis evidence. Comparative
revised chỉ khả dụng từ publication của tài liệu đưa ra revision.

Không cộng EPS quý đã làm tròn, không annualize H1×2. Rounding whole-share
disclosures được propagate thành interval; không snap WA_TTM về current shares.
Nếu khoản deduction interim chưa estimated hoặc period allocation chưa resolved,
reported TTM reference không trở thành **strict normalized TTM EPS**.
Code: [financial_ttm_reference.py](../../src/delta_t1/features/financial_ttm_reference.py).

## 4. P/E: ngày giá và earnings basis

```text
P/E_TTM = raw_close_VND_per_share / EPS_TTM_VND_per_share
```

Cần raw close tại decision date, exact EPS_TTM và common-share basis/event
coverage. Báo cáo lợi nhuận sau thuế không đủ vì còn numerator/WA/dilution và
TTM bridge. Giá vendor-adjusted dùng trong market momentum không tự thay raw
price cho valuation; không suy raw price bằng một hệ số adjustment chưa verified.

Reference `reported_basis_pe_reference` dùng latest eligible **exact12-month
annual EPS** theo basis đã khai báo. Nó khác `reported_ttm_pe_reference` cập nhật
interim và khác strict PE task trong readiness50. EPS<=0 hoặc price<=0 thì
valuation reference trả null/reason, không gán PE=0 hay coi âm PE là rẻ.

Không có ngưỡng PE tốt/xấu đã được project duyệt. Khi phân tích phải giữ period,
book/share/event basis và sector; một con số PE không tự đưa ra buy/sell signal.
Code: [reported valuation](../../src/delta_t1/features/financial_vas_reference.py),
[TTM valuation](../../src/delta_t1/features/financial_ttm_reference.py).

## 5. P/B, BVPS và market capitalization

```text
BVPS       = parent_common_equity / common_shares
Market cap = raw_close * common_shares
P/B        = raw_close / BVPS = Market cap / parent_common_equity
```

Đây là cùng phép chia khi price/shares/equity compatible. Equity cho P/B thuộc
**common shareholders của parent**, tách NCI và preferred claims nếu có. Không
lấy total group equity gồm NCI; không lấy vốn điều lệ thay equity. Market cap
và BVPS là derived outputs, không thay các raw fields/evidence của phép tính.

Cần BCTC hợp nhất và equity note, share register/issuance/treasury/bonus/ESOP,
effective dates, raw close và các thay đổi equity có liên quan. Không dùng
approved issuance plan như actual shares; không backfill current shares lịch sử.

Các references hiện khác nhau:

| Basis | Công thức/ý nghĩa | Điều chưa chứng minh |
|---|---|---|
| Reported book snapshot | Giá×reported shares/reported parent equity; shares/equity cùng balance date | Book basis có thể cũ so với valuation date |
| Current shares / last reported equity | Giá×current common shares/last reported parent equity | Không phải equity tại ngày giá hoặc complete event-adjusted PB |
| Gross ESOP capital bridge | Giá×current shares/(reported parent equity+verified registered capital increase) | Unknown fees/subsequent earnings/events; không phải current net equity |

Bridge gross cần bank proceeds, registered increase, issue price/actual shares,
registration effective và publication. Tiền nhận trước balance date không tự
chứng minh đã ghi vào equity hoặc advance liability. Không cộng proceeds/cash
hai lần; unknown fee giữ null. Equity/shares/price không dương thì reference
valuation bị chặn. Code:
[gross bridge](../../src/delta_t1/features/financial_equity_reference.py).

## 6. F-score: chín tín hiệu và history

Implementation dưới đây đối chiếu
[calculate_f_score](../../src/delta_t1/features/financial_reference.py),
[SIGNALS](../../src/delta_t1/ingestion/financial_pilot_readiness.py) và
[VAS adapter](../../src/delta_t1/features/financial_vas_reference.py).

```text
A_t = (TA_t + TA_(t−1))/2
ROA_t = NI_t/TA_(t−1)
CFO_ratio_t = CFO_t/TA_(t−1)
LEV_t = LTD_t/A_t
CR_t = CA_t/CL_t
GM_t = GP_t/Sales_t
TURN_t = Sales_t/A_t
F = sum(S1..S9), chỉ có total khi cả9 tín hiệu known
```

| Signal/key | Được1điểm khi | Raw inputs phải có |
|---|---|---|
| S1 `positive_roa` | ROA_t>0 | NI_t, TA_(t−1) |
| S2 `positive_cfo` | CFO_ratio_t>0 | CFO_t, TA_(t−1) |
| S3 `improved_roa` | ROA_t>ROA_(t−1) | NI_t/NI_(t−1), TA_(t−1)/TA_(t−2) |
| S4 `cash_accrual_quality` | CFO_ratio_t>ROA_t | CFO_t, NI_t, TA_(t−1) |
| S5 `reduced_leverage` | LEV_t<LEV_(t−1) | LTD_t/LTD_(t−1), TA_t/TA_(t−1)/TA_(t−2) |
| S6 `improved_liquidity` | CR_t>CR_(t−1) | CA/CL hai năm |
| S7 `no_parent_issuance` | Verified issuance indicator=0 | Actual parent common-equity issuance evidence năm`t` |
| S8 `improved_gross_margin` | GM_t>GM_(t−1) | Gross profit/net revenue hai năm |
| S9 `improved_turnover` | TURN_t>TURN_(t−1) | Sales hai năm, assets ba balance dates |

Strict inequalities: bằng nhau không được điểm. Known nhưng fail=0; **không có
evidence không phải0**. Có8/9signals thì total vẫn null, xuất known_signals và
missing reasons. LTD là original long-term borrowings/finance leases **gồm phần
đến hạn trả**; không lấy riêng noncurrent debt. Dòng tiền thu phát hành có thể
gồm NCI vào công ty con, không chứng minh parent issuance. Indicator raw:
1=verified actual issuance;0=verified absence;null=unknown, khác điểmS7.

Strict calculator cần `income_before_extraordinary_items`. Workflow50 dùng
variant **PIOTROSKI_VAS_REPORTED_NET_PROFIT_REFERENCE**, thay bằng consolidated
`net_profit` **gồm NCI** với adaptation được khai báo. Không tự đổi sang parent
profit. Turnover dùng average assets theo lựa chọn Table1 trong contract, khác
denominator beginning-assets mô tả ở body paper. Cơ sở:
[Piotroski, Selected Paper84](https://www.chicagobooth.edu/~/media/FE874EE65F624AAEBD0166B1974FD74D.pdf).

F từ0–9 phản ánh số tín hiệu đạt **theo variant**, chưa có quy tắc production
ranking/buy-sell hoặc ngưỡng high/low được handbook này phê duyệt.

## 7. M-score: eight-variable sensitivity

Giữ tên **BENEISH_2013_VAS_REPORTED_PROFIT_OWNED_PPE_SENSITIVITY**.
Công thức đang chạy trong
[calculate_vas_m_score](../../src/delta_t1/features/financial_vas_reference.py):

```text
M = −4.84 +0.920*DSR +0.528*GMI +0.404*AQI +0.892*SGI
          +0.115*DEPI −0.172*SGAI +4.679*ACCRUALS −0.327*LEVI
```

| Thành phần | Công thức implementation | Ý nghĩa / dữ liệu |
|---|---|---|
| DSR | (REC_t/Sales_t)/(REC_(t−1)/Sales_(t−1)) | Thay đổi receivables so với doanh thu; cần declared receivables basis |
| GMI | (GP_(t−1)/Sales_(t−1))/(GP_t/Sales_t) | Thay đổi gross margin |
| AQI | [1−(CA_t+PPE_t)/TA_t]/[1−(CA_(t−1)+PPE_(t−1))/TA_(t−1)] | Asset-quality residual; PPE net tangible, không total fixed assets |
| SGI | Sales_t/Sales_(t−1) | Tăng trưởng doanh thu |
| DEPI | [DEP_(t−1)/(DEP_(t−1)+PPE_(t−1))]/[DEP_t/(DEP_t+PPE_t)] | DEP của owned tangible PPE trong năm; PPE là net balance cuối năm |
| SGAI | [(SELL_t+ADMIN_t)/Sales_t]/[(SELL_(t−1)+ADMIN_(t−1))/Sales_(t−1)] | Tỷ lệ selling+administration expense |
| ACCRUALS | (NI_t−CFO_t)/TA_t | Reported-profit cash-flow accruals **trên tài sản cuối năm** trong code |
| LEVI | [(CL_t+NCLD_t)/TA_t]/[(CL_(t−1)+NCLD_(t−1))/TA_(t−1)] | CL+noncurrent loans/finance leases; không cộng current portion lần nữa |

`REC` ở reviewed MWG/VHC là **gross short-term trade receivables**; không tổng
phải thu hoặc net receivables khi basis chưa declared. `PPE`/`DEP` của sensitivity
là owned tangible PPE/net và depreciation tương ứng; không lấy cash-flow total
D&A gồm intangible/lease amortization. `NI` là reported group NI, không tự thay
strict income-before-extraordinary-items.

**Khác biệt cần giữ rõ với paper:** hệ số lấy từ
[Beneish, Lee & Nichols2013, AppendixB](https://cpb-us-w2.wpmucdn.com/sites.udel.edu/dist/a/855/files/2020/07/Earnings-Manipulation-and-Expected-Returns.pdf).
Paper mô tả Accruals trên **average total assets**, còn code hiện chia **TA_t**.
Đây là khác biệt methodology phải review nếu muốn strict reproduction; handbook
ghi đúng code, không tự sửa denominator hoặc promote sensitivity thành original
model. Các lựa chọn earnings/receivables/owned-PPE cũng cần declared basis.

Denominators lồng nhau đều phải>0, finite inputs, nonnegative REC/PPE/DEP/debt;
negative asset-quality residual hiện tại bị chặn. Missing/invalid ratio trả null
toànM; không dùng partial weighted sum. Chi phí website dạng âm phải resolve
sign convention với PDF, không auto-abs. Project giữ **classification_threshold=null**;
không áp ngưỡng từ model khác và không kết luận doanh nghiệp gian lận.

## 8. EM Z-double-prime có constant3,25

```text
WC = CA − CL
X1 = WC/TA
X2 = retained_earnings/TA
X3 = document_reconciled_EBIT/TA
X4 = total_equity/total_liabilities
Z_EM'' = 3.25 + 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
```

Đây là **EM Z''**, không phải mọi Altman variant. X4 dùng **book total group
equity/liabilities**, khác parent common equity của P/B. Nguồn tham chiếu:
[IMF WP19/93, SectionII](https://www.imf.org/-/media/files/publications/wp/2019/wpiea2019093.pdf).
Code: [financial_reference.py](../../src/delta_t1/features/financial_reference.py).

Cần balance sheet và retained-earnings note; annual PBT, pure expensed interest
và EBIT reconciliation. Workflow50 hỗ trợ direct reconciled EBIT hoặc named
basis **EBT_PLUS_DISCLOSED_EXPENSED_INTEREST_EXCLUDING_ISSUANCE_FEES**:
`EBIT=PBT+disclosed expensed interest`. Không gọi mọi VAS operating-profit line
là EBIT; không lấy entire finance expense gồm FX/fees thay pure interest; không
thêm capitalized interest vào P&L interest nếu không phù hợp. Basis này chưa tự
loại mọi associate/financial/other item theo một operational EBIT definition khác.

QA: assets=liabilities+equity, reconciled basis và same vintage; workflow50 hiện
cho chênh tối đa1VND sau unit normalization. TA/TL>0; working capital/retained
earnings có thể âm, không clamp0. Continuous diagnostic; chưa project distress
threshold hoặc xác suất phá sản đã calibrated cho Việt Nam. Banks/brokers/insurers
và fiscal/calendar exceptions cần adapter/contract riêng trước khi tính bulk.

## 9. Data dictionary: lấy trường nào, ở đâu?

Trường dưới đây là **review/reference keys**, không phải universal provider
item codes. CDKT=balance sheet; KQKD=income statement; LCTT=cash-flow statement;
TM=notes. Mapping phải dựa code+label+template+scope đã review; không hard-code
VAS code cho mọi năm/ngành.

| Field/key | Ý nghĩa và vị trí cần crawl | Unit / loại | Dùng cho |
|---|---|---|---|
| `current_assets` | CDKT tài sản ngắn hạn | VND/instant | F,M,Z |
| `total_assets` | CDKT tổng tài sản, gồm comparative`t−2` khi cần | VND/instant | F,M,Z |
| `current_liabilities` | CDKT nợ ngắn hạn | VND/instant | F,M,Z |
| `total_liabilities` | CDKT tổng nợ phải trả | VND/instant | Z/balance QA |
| `total_equity` | CDKT equity group gồm NCI | VND/instant | Z/balance QA |
| `retained_earnings` | CDKT/TM lợi nhuận sau thuế chưa phân phối | VND/instant | Z |
| `parent_common_equity` | Equity parent cho common shareholders; TM NCI/preferred adjustments | VND/instant | PB/BVPS |
| `net_revenue` | KQKD doanh thu thuần đúng annual/YTD duration | VND/duration | F,M |
| `gross_profit` | KQKD lợi nhuận gộp, kiểm revenue−COGS | VND/duration | F,M |
| `net_profit` | KQKD LNST hợp nhất gồm NCI | VND/duration | F-VAS,M-sensitivity |
| `income_before_extraordinary_items` | Earnings definition strict, cần accounting reconciliation | VND/duration | Strict F; không auto-alias net_profit |
| `operating_cash_flow` | LCTT lưu chuyển tiền thuần từ hoạt động kinh doanh | VND/duration | F,M |
| `profit_before_tax` | KQKD lợi nhuận trước thuế | VND/duration | EBIT bridge/Z |
| `interest_expense` | TM pure expensed interest, tách issuance/arrangement fees | VND/duration | EBIT bridge/Z |
| `document_reconciled_ebit` | Derived/reconciled từ evidence, không raw operating-profit alias | VND/duration | Z |
| `long_term_debt_including_current_portion` | TM borrowing/finance lease original maturity, gồm current portion | VND/instant | F leverage |
| `parent_common_equity_issuance_verified` | TM capital/share events, actual issuance của parent trong năm | INDICATOR0/1/null | F-S7 |
| `receivables` | Key generic M; reviewed TM trade receivables với declared basis | VND/instant | M-DSR |
| `net_tangible_ppe` | CDKT/TM PPE hữu hình net theo scope variant | VND/instant | M-AQI/DEPI |
| `owned_tangible_ppe_depreciation` | TM PPE roll-forward depreciation phát sinh năm, không accumulated balance | VND/duration | M-DEPI |
| `selling_expense` | KQKD/TM chi phí bán hàng, positive magnitude đã review | VND/duration | M-SGAI |
| `administrative_expense` | KQKD/TM chi phí quản lý, positive magnitude đã review | VND/duration | M-SGAI |
| `noncurrent_loans_and_finance_leases` | CDKT/TM borrowings/leases còn noncurrent; không toàn bộ LTD | VND/instant | M-LEVI |
| `eps_adjusted_earnings_numerator` | EPS note, numerator disclosed sau điều chỉnh đúng kỳ | VND/duration | Annual/basic EPS |
| `weighted_average_basic_shares` | EPS note, WA basic common shares đúng kỳ | SHARES/duration denominator | EPS |
| `weighted_average_diluted_shares` | EPS note/dilution bridge đã verified | SHARES/duration denominator | Diluted EPS; không required cho basic-only workflow50 |
| `vendor_basic_eps` | EPS được in trong exact PDF để rounding QA | VND_PER_SHARE/duration ratio | EPS QA |
| `reported_eps_numerator`, `weighted_basic_shares`, `parent_profit`, `reported_deduction` | Keys của TTM period input; map từ EPS note, không rename tùy ý | VND/SHARES theo field | Reported TTM |
| `raw_close` | Market daily unadjusted close đúng ngày | VND_PER_SHARE/instant | PE/PB/market cap |
| `historical_common_shares_outstanding` / common-share event ledger | Parent shares outstanding đúng effective interval; tách treasury/plan/actual | SHARES/instant + events | PB/valuation basis |

**Raw nên giữ thêm:** COGS, parent profit/NCI, allowance/gross/net receivables,
PPE gross/accumulated depreciation/net roll-forward, finance-cost breakdown,
debt maturities và share/capital movements. Các dòng này phục vụ reconciliation,
không phải tất cả là required keys của một calculator. Đừng chỉ crawl sáu
provider ratios: không đủ evidence để recompute/review về sau.

## 10. Nguồn dữ liệu và bộ tài liệu cần lấy cho mỗi mã

Source roles theo [source-selection config](../../configs/data/financial_source_selection_v1.json),
không phải canonical source-priority approval:

| Nguồn/lớp | Lấy gì? | Vai trò và giới hạn |
|---|---|---|
| CafeF detail HTML KQKD/CDKT/LCTT | Structured candidate rows, headers, labels/units, periods | Nguồn candidate chính trong flow hiện có; phải review unit/scope/vintage trước acceptance |
| CafeF attachment/listing | Full BCTC PDFs và link công bố | PDF phục vụ exact values/notes; listing date phải gắn đúng file/version |
| Website IR doanh nghiệp | Official full statements/notes, notices/share events | Bổ sung missing notes, PDF identity và publication statements |
| HOSE/HNX/SSC publication evidence | Dated disclosure và exact attachment | Tìm actual public availability khi có; không giả định mọi endpoint đã tích hợp runner |
| Public mirror/broker | Exact attachment hoặc dated repost khi primary thiếu | Evidence source/quality riêng; không suy repost là earliest issuer publication |
| KBS | Diagnostic candidates/cross-check | Không auto-fallback; benchmark có period/value-alignment gaps |
| Market pipeline hiện có | Raw price, calendar và market observations | Dùng lại cache; adjusted proxy không tự đủ valuation/event basis |

Cho annual FY2025 F/M/EPS/Z, bộ đầu tiên cần **full consolidated audited FY2025
BCTC và notes**, supportingFY2024 và comparativeassets2023, dated publication
evidence cho từng PDF, share issuance/maturity/depreciation notes. Thêm FY2023
hoặc notice riêng theo actual missing queue. Muốn PE/PB cập nhật phải lấy thêm
interim EPS/full notes, raw prices, common-share/equity events. Annual report
trích vài bảng không thay full statements; PDF gồm IFRS tables không chứng minh
đã đủ VAS facts chỉ vì có một audit letter VAS.

Text PDF: extract giữ page/locator. Scan PDF: render/OCR để tìm ô, rồi visual
review. OCR output chưa thành accepted value tự động. HTML cung cấp số nhanh;
PDF/notes cung cấp semantics/evidence thiếu. Không phải mọi data đều cần OCR.

## 11. Metadata, PIT và revision: cần crawl cùng số liệu

Mỗi document/fact cần đủ lineage, tối thiểu các nhóm sau theo schema đang dùng:

| Nhóm | Nội dung phải giữ |
|---|---|
| Identity | Issuer/security identity, symbol, scopeCONSOLIDATED/STANDALONE, frameworkVAS/IFRS, company-type/sector evidence |
| Period | Fiscal year; period_start/end cho flows; balance date cho instant; annual/quarter/YTD/TTM; months |
| Vintage | Document/report/provider IDs riêng, revision/restatement relationship, exact `pdf_sha256` |
| Numeric | Raw text/value, field/item code+label, currency/unit/scale/sign basis; normalized value chỉ sau verified mapping |
| Provenance | Source URL, fetched_at, immutable path/manifest/hash, `pdf_page`, `locator`, OCR/page evidence, reviewer/status |
| Availability | Publication date/precision và source-linked evidence/hash, `usable_from_date`; timestamp/timezone khi thực sự có |
| Events | Publication/effective dates, planned vs actual, share counts/price/proceeds/fees và accounting treatment |

DATE_ONLY rule đã duyệt:

```text
usable_from_date(source) = phiên exchange quan sát được đầu tiên sau publication_date
usable_from_date(result) = max(usable_from_date của mọi source được dùng)
decision_date >= usable_from_date(result)
```

Giờ có thể thiếu; calendar coverage và publication ngày vẫn phải verified. Một
supporting PDF thiếu publication có thể làm F/M PIT null dù main PDF có ngày.
Không infer publication từ ngày ký/audit, filename, uploads directory, PDF
metadata hoặc fetched_at. Signature-date proxy nếu làm phải giữ riêng với nhãn
REFERENCE_ONLY; hiện chưa là policy accepted thay publication. Xem
[publication discovery MWG/VHC](../../artifacts/reports/financial-mwg-vhc-publication-review-v1/report.md).

Revision giữ vintage mới và availability mới; không ghi đè/backfill original
historical values bằng latest comparative. Cùng ticker/năm chưa đủ join; file
hash khác phải xác minh quan hệ phiên bản, không tự copy ngày. Calendar source
hiện observed-session union có giới hạn, không tự gọi authoritative exchange calendar.

## 12. Workflow triển khai và điều kiện hoàn tất

```text
Chọn task/năm/variant → xuất required-input/missing queue
→ lấy structured candidates + exact full PDF/notes + publication/events
→ pin raw/hash/receipts → extract text hoặc render/OCR
→ review value/unit/period/scope/vintage + accounting QA
→ tạo input version mới → reference calculator
→ kiểm từng source PIT + revision/event/historical identity
→ report readiness và blockers → acceptance theo contract
```

Workflow50 wrapper hiện `template/review` tích hợp **basic annual EPS, Z, F-VAS,
M-sensitivity**. PE/PB vẫn strict tasks có external blockers; các pilot valuation
modules khác không tự có nghĩa đã được bulk50 pipeline cover. Lệnh, schema JSON
và source SHA selection xem [runbook](../crawl/FINANCIAL_READINESS_USER_GUIDE.md).
Không tự scale network khi budgets/latch hoặc source/acceptance gates còn đóng.

Checklist trước khi đánh dấu một mã-task complete:

1. Khóa variant/task period, đúng company type/scope/framework; không mixing bank/nonfinancial hoặc calendar/noncalendar adapter.
2. Đủ mọi required input và supporting year, unit/sign đã verified; unknown giữ null/reason.
3. Balance equation; income/gross-profit bridge; EPS rounding; PPE/debt/equity roll-forward và provider differences được kiểm ở field level.
4. Các input có exact source hashes/page/locator; publication từng source, revision và share/event basis tương thích decision date.
5. Reference output giữ signals/ratios/denominators, source vintage, formula/version và acceptance; missing không tạo partial total giả.
6. Production/cluster eligibility chỉ theo approved registry+protocol; source recovery/OCR/calculation thành công không tự mở gate.

Snapshot tham chiếu kiểm09/10/2026 từ kết quả stage08/10: workflow50 có
**24/300 FY2025 reference task cells trên8/50mã**, EPS8/Z8/F4/M4/PE0/PB0 trong
matrix đó; production acceptance0. Không gọi đây là8% dữ liệu hoặc8% production
ready. Xem [latest F/M report](../../artifacts/reports/financial-mwg-vhc-fm-review-v1/report.md)
và [CURRENT_STATUS](../CURRENT_STATUS.md) cho tiến độ mới; handbook không thay live report.

## 13. Ví dụ arithmetic để kiểm hiểu công thức

Các số dưới đây là **synthetic**, không phải một mã thật hoặc lời khuyên đầu tư:

- EPS note: numerator100tỷVND, WA_basic20triệuSHARES → basicEPS5.000VND/share. Price50.000VND/share → annual reported PE10; chỉ gọi TTM khi numerator/denominator thực sự là TTM.
- Parent common equity300tỷVND, compatible common shares20triệu → BVPS15.000VND/share, price50.000 → PB3,333333. Group equity chứa thêm NCI không thay denominator này.
- EMZ: CA400, CL200, TA1.000, RE100, EBIT80, E600, TL400, cùng unit → WC200 và Z=**7,0006**. Chỉ là arithmetic của named variant.
- F:8signalsknown,1missing → total**null**, không ghiF-score=8 hay tự cho missing=0; coverage8/9signals có thể báo riêng.
- M: DSR/GMI/AQI/SGI/DEPI/SGAI/LEVI đều1, ACCRUALS0 → M=**−2,48** theo codecoefficients; không tự classify từ con số này.

## 14. Phụ lục market: công thức và data đã có

`P_t` là usable close theo accepted price basis của snapshot; market pipeline
chọn `raw_close` cho unadjusted hoặc `adj_close` cho approved adjusted basis.
`r_t=P_t/P_(t−1)−1`. Không nén missing sessions; đổi basis reset history.
Nguồn implementation:
[market.py](../../src/delta_t1/features/market.py),
[registry.py](../../src/delta_t1/features/registry.py).

| Feature | Công thức / ý nghĩa | Data tối thiểu cho arithmetic |
|---|---|---|
| `mom_21` | P_t/P_(t−21)−1; momentum khoảng1tháng |22usableprices |
| `mom_63` | P_t/P_(t−63)−1 |64prices |
| `mom_126` | P_t/P_(t−126)−1 |127prices |
| `mom_252` | P_t/P_(t−252)−1 |253prices |
| `vol_63` | sample_stdev63returns×sqrt252 |64prices,63consecutive returns |
| `vol_126` | sample_stdev126returns×sqrt252 |127prices |
| `downside_vol_63` | sqrt(mean(min(r,0)^2)×252), mean trên tất cả63returns |64prices; không mean chỉ trên ngày âm |
| `mdd_126` | min(P/running_max(P)−1) trong126prices |126prices; kết quả<=0 |
| `beta_126` | sample_cov(stock,benchmark)/sample_var(benchmark) |126pairedreturns/127alignedprices; benchmark variance>1e−16 |
| `liquidity_21` | mean(traded_value)21phiên |21valuesVND; không thay bằng share volume hoặc mean(price)×mean(volume) |
| `ram_63` | mom_63/vol_63 | Cả2inputs; code yêu cầu vol_63>1e−12 |

Registry có11market features, required market-only set hiện là8:
`mom_21,mom_63,mom_126,mom_252,vol_63,mdd_126,beta_126,liquidity_21`.
Có đủ cửa sổ arithmetic chưa đủ eligibility: còn calendar/PIT/status/basis,
ba calendar years usable observed history, metadata và protocol checks.
CafeF market adjusted price là vendor proxy, không tự là total-return series.
OHLCV/traded value, benchmark, trading calendar, identities và adjustment basis
vẫn là raw requirements; workstream financial không cần crawl lại market cache.

Sharpe/ROI thuộc portfolio evaluation, **không cluster inputs**; metrics đánh giá
cluster/backtest xem [evaluation contract](../EVALUATION_AND_BACKTEST.md), không
trộn với sáu financial families ở trên.

## 15. Quy tắc bảo trì cho developer tiếp theo

Khi thêm/chỉnh chỉ số, cập nhật đồng thời formula/variant, required fields và
units, kỳ/history, sector adapter, PIT/revision/event rules, missing policy,
registry version và relevant tests. Thay methodology cần decision/config version
mới, không sửa sealed historical outputs. Chạy targeted checks phù hợp; ghi report
và changelog. Mọi feature mới cần citation và explicit acceptance, không dựa prefix.

Đọc handbook để hiểu; dùng contract/config/code phiên bản đã pin để execute.
Nếu handbook khác code, ghi discrepancy và resolve qua review; không tự lấy lựa
chọn thuận tiện để bỏ missing data hoặc biến reference thành research-ready.
