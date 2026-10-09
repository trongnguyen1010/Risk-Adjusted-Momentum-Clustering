# Financial evidence và quyết định triển khai v1

Tài liệu diễn giải cho developer, cập nhật09/10/2026:
[Handbook công thức, raw fields và checklist crawl](FINANCIAL_INDICATORS_AND_DATA_GUIDE.md).
Handbook không thay contract/config hoặc acceptance policy.

Ngày: 03/10/2026. Phạm vi: workstream financial trên nhánh CafeF; giữ M2 market-only độc lập.
Owner yêu cầu tham khảo literature và tự đưa ra quyết định hợp lý. Quyết định dưới đây
khóa mục tiêu thu thập/implementation, **không chứng nhận dữ liệu PIT hoặc mở research gate**.
Executable policy: [financial_evidence_policy_v1.json](../../configs/data/financial_evidence_policy_v1.json).

## Căn cứ và thứ tự ưu tiên

[Literature matrix complete](LITERATURE_MATRIX_COMPLETE.md), B6/B7, hỗ trợ thử
market + firm characteristics và valuation. Matrix chưa chứa công thức F/M/Z;
không suy các công thức này từ B6/B7. Bổ sung nguồn primary/full-text ở bên dưới.
Ưu tiên dữ liệu profitability/growth/leverage/liquidity; F-Score trước, Z và M là
diagnostic sau khi đủ input. Không chọn feature bằng portfolio return/Sharpe.

## Phạm vi và ngữ nghĩa

- Pilot FPT/VNM/PVS/ACV; scope **consolidated**, score **annual**. Không mở rộng
  toàn universe trước pilot gates. Financial institutions cần contract riêng;
  sector lịch sử phải có evidence, không suy từ ticker hoặc profile hiện tại.
- Acquisition năm 2019–2025 để hỗ trợ score 2021–2025: so ROA năm 2021 với 2020
  cần tài sản đầu năm 2020, tức cuối 2019. Kỳ đủ dài không đồng nghĩa đủ input.
- Balance sheet là instant. Income statement có quý riêng và YTD; cash flow
  thường YTD. Giữ ngày bắt đầu/kết thúc từ từng PDF. Không gán CFO 9 tháng thành Q3.
- Giữ accounting framework VAS/IFRS theo từng document; không merge hoặc dùng
  comparator khác framework. Annual report có trích audit letter VAS nhưng bảng
  số IFRS không chứng minh đã có full VAS financial statements/thuyết minh.
- Chỉ hiệu YTD khi input cùng scope, currency, fiscal period và compatible vintage;
  availability của kết quả là availability muộn nhất của input. Không hiệu tự động
  giữa số ban đầu và số đã restate để che version mismatch.
- Raw HTML giữ nguyên số/text/unit candidate; nhãn tỷ đồng chưa xác minh không
  được nhân hệ số. PDF đã nhìn rõ nhãn VND/VND-per-share có thể tạo candidate được
  kiểm chứng về giá trị/đơn vị/kỳ; vẫn thiếu PIT nếu publication chưa xác minh.

## Score definitions được chọn

**F-Score:** [Piotroski, Selected Paper 84](https://www.chicagobooth.edu/~/media/FE874EE65F624AAEBD0166B1974FD74D.pdf),
PDF trang 9–10 và Table 1 trang 15. Dùng chín tín hiệu annual. ROA/CFO chia tài sản
đầu năm; leverage dùng long-term debt gồm current portion và tài sản bình quân.
Body và Table 1 khác nhau về denominator turnover; chọn **Table 1 average-assets
turnover**, ghi tên variant rõ trong config. Tín hiệu thay đổi dùng strict inequality;
thiếu bất kỳ signal thì tổng null. VAS net income không tự đồng nhất với income
before extraordinary items; cần reconciliation. Cash line 31 có thể chứa vốn NCI
vào công ty con: không chứng minh common-equity issuance của parent.

**M-Score:** [Beneish, Lee & Nichols (2013)](https://cpb-us-w2.wpmucdn.com/sites.udel.edu/dist/a/855/files/2020/07/Earnings-Manipulation-and-Expected-Returns.pdf),
Appendices A/B (definitions/model). Chọn eight-variable model với cash-flow accruals;
không gọi đây là exact balance-sheet accruals của bản 1999. DSR, GMI, AQI, SGI,
DEPI, SGAI, Accruals và LEVI cùng annual basis. PPE phải là net tangible PPE;
depreciation phải tách amortization/goodwill. Tổng fixed assets và aggregate D&A
không phải alias hợp lệ. SGA là selling + administration; leverage dùng current
liabilities + long-term debt. Giữ continuous diagnostic, chưa gán fraud threshold.

Clarification implementation09/10/2026: `calculate_vas_m_score` hiện dùng
`(net_profit−operating_cash_flow)/total_assets_t`, trong khi AppendixB mô tả
Accruals chia average total assets. Giữ đây là named sensitivity/reference;
không tuyên bố strict reproduction. Handbook ghi rõ discrepancy để review khi
phát triển tiếp; lượt documentation này không đổi code, denominator hoặc gates.

**Z:** chọn **EM Z-double-prime có hằng số 3,25**, cho non-financial pilot, theo
[IMF WP/19/93, Section II](https://www.imf.org/-/media/Files/Publications/WP/2019/WPIEA2019093.ashx),
PDF trang 8. Working capital, retained earnings, EBIT và book equity/liabilities
là inputs. Dùng denominator liabilities theo Section II; bảng biến cuối paper
có nhãn X4 khác nên không lấy bảng đó để redefine formula. Không map code 30
VAS trực tiếp thành EBIT; cần reconcile thu nhập/chi phí tài chính và lãi vay.
Không áp ngưỡng distress của biến thể khác hoặc tuyên bố xác suất default Việt Nam.

Các biến trung gian thiếu hoặc denominator không hợp lệ trả null với reason;
không impute, average sources hoặc copy score từ website.

## EPS, P/E, P/B

Giữ basic và diluted riêng. Recompute EPS cần numerator sau các điều chỉnh theo
thuyết minh và weighted-average shares; parent net profit chưa chắc là numerator.
Chỉ derive diluted weighted shares bằng basic khi đúng vintage note xác nhận
không có potentially dilutive common shares; ghi rule và page evidence, không
suy từ việc hai EPS in cùng giá trị. EPS rounding QA không mở PIT/feature gate.
Không cộng bốn EPS quý có share basis/restatement khác nhau. Vendor EPS chỉ được
dùng khi scope/kỳ/share adjustment/vintage xác minh. Không lấy current shares
backfill lịch sử. P/E dùng raw VND/share và EPS TTM có cùng share basis, EPS <= 0
trả null với reason. P/B cần parent common equity và common shares tại ngày định giá;
không dùng total group equity gồm NCI thay parent equity. Vendor-adjusted market
proxy hiện tại không tự động là basis phù hợp cho valuation.

## PIT và acceptance

Report identity = issuer + scope + period + document vintage; provider ID và PDF hash
được giữ riêng. Lưu mọi phiên bản, không chọn latest rồi áp ngược lịch sử.
Timestamp consumers giữ `available_at <= decision_at`. Owner đã phê duyệt date-PIT
cho daily/monthly ngày 03/10/2026: `decision_date >= usable_from_date`, trong đó
usable_from_date là phiên exchange quan sát được đầu tiên sau ngày công bố.
Áp dụng cho tất cả input và comparator vintages; không dùng ngay ngày công bố.
Không suy publication từ filename, ObjectId, PDF metadata, ngày ký, ngày kiểm toán
hoặc `fetched_at`. Ngày trên issuer listing được giữ với precision=date; chưa tự
chuyển thành intraday timestamp. Cần source-linked publication evidence theo exact
PDF hash; timezone của phép so ngày là Asia/Ho_Chi_Minh, source timezone/available_at
có thể null với DATE_ONLY. Thiếu giờ không còn là blocker date-PIT. Calendar hiện
là C8 observed-session union, chưa authoritative; thiếu phạm vi/phiên phải fail-closed.
Hai bản cùng ngày khác values không tự chọn. Policy mới:
[financial_date_pit_v1](../../configs/data/financial_date_pit_v1.json) và
[evidence v2](../../configs/data/financial_evidence_policy_v2.json).

Gate mở khi đủ field semantics, scope, đơn vị, revision identity, actual availability,
historical sector/identity và accounting QA. OCR en-US chỉ hỗ trợ tìm trang/ô;
giá trị chưa visual-check không đi vào canonical. Hiện `financial_features_allowed=false`.
Các quyết định này không sửa final M2 protocol, feature registry hoặc backtest.

## Reproducibility và dependencies

Collectors chạy `.venv/Scripts/python.exe`; PDF text runner cần `pypdf` có sẵn trong
bundled Python. OCR cần Windows PowerShell WinRT `Windows.Media.Ocr` với en-US và
Poppler `pdftoppm`. Không thêm cloud OCR hoặc upload raw. Output là run mới dưới
`data/financial/`, manifest exact inventory + SHA256; source PDF/HTML cũ giữ bất biến.
Report hiện hành: [financial date-PIT v1](../../artifacts/reports/financial-date-pit-v1/report.md).

## Executable reference acceptance — 03/10/2026

[Reference flow config](../../configs/data/financial_reference_flow_v1.json) khóa
original audited FPT2024/25 exact PDFs và reviewed OCR templates. EPS/EM-Z output
chỉ reference: same-PDF inputs, expected units/period/VAS/consolidated evidence,
coordinate parser so reviewed ground truth, accounting bridges, date availability
và denominator QA. Reference registry riêng không cluster eligible; không sửa
production feature registry/methodology hoặc full research gate.

EPS2024 original 4.944 không dùng sau known restatement release từ 20/03/2026 khi
comparative share-basis acceptance chưa đủ; giữ null/revision blocker. EPS annual
không là TTM. Z chỉ continuous diagnostic theo frozen EM variant, không threshold.
[Report mới](../../artifacts/reports/financial-reference-flow-v1/report.md).

Reference continuation v2: fiscal EPS2024 revised inputs từ original2025 PDF chỉ
khả dụng từ 20/03/2026. Original no-dilution evidence + disclosed bonus-share
adjustment giữ hai-source lineage cho revised diluted denominator. F-score dùng
loan + finance lease theo original maturity đã gồm current portion; issuance
indicator 1=actual parent common issuance verified, 0=verified absence, null=unknown.
Calculator xuất cả chín signal với missing reasons; total chỉ có khi 9/9 known.
FPT2024/25 hiện 6/9, strict income-before-extraordinary-items vẫn unresolved.
[Report](../../artifacts/reports/financial-revision-fscore-v1/report.md).

## Explicit VAS adaptations và reported valuation reference

Source completion configv3 thêm registry riêng, không thay strict fields/variants.
F-score VAS dùng reported consolidated net profit thay ordinary-income trong
named variant; original-maturity debt và verified actual parent issuance giữ.
M sensitivity dùng owned PPE/depreciation cùng scope, declared gross short trade
receivables/four conditional allowance allocations, reported profit accruals và
CL+noncurrent loan/lease cho LEVI; hệ số2013 giữ nguyên. Không threshold hoặc
strict-score claim. Production acceptance MANUAL_REVIEW_REQUIRED, gates vẫnfalse.

Period EPS giữ exact3/6/9/12-month note, không annualize hoặc cộng EPS các quý.
Reserve H12026 FPT chưa ước tính không verifiedzero. Reported P/E dùng raw-close
và FY2025 exact12-month EPS; reported P/B dùng common equity/shares cùng31/12/2025,
event coverage/historical identity chưa nghiệm thu. FTEL scope change và chế độ
biểu mẫu2026 chặn latestTTM cho đến khi có full-year bridge.

KBS candidates không accepted facts: actualValue1–4 khác Head/pageSize;
null/zero/EPSunitexception giữ riêng, provider dates không publication evidence.
[Report](../../artifacts/reports/financial-source-research-v1/report.md).

Exact-PDF transcription corrections được áp bằng identity/hash/incorrect value,
không source priority; giữ excluded originals và reviewed replacement. Unknown
conflicts còn nguyên để fail-closed. Run fpt_review_corrections_v1 có two-source
page QA cho CFO và noncurrent-liability sum; publication precision/date không đổi.

## FPT TTM và common-share events — 04/10/2026

Named variant `REPORTED_NUMERATOR_SHARE_DAYS_TTM_REFERENCE` chỉ reference.
TTM numerator = FY2025 reported EPS numerator + H12026 numerator − H12025 numerator.
TTM weighted shares = (FY WA × 365 + H12026 WA × 181 − H12025 WA × 181) / 365.
Denominator dùng disclosed post-2025-bonus common basis; giữ propagated source
rounding interval ±0,5 share/input, không snap về outstanding shares. Không sum
rounded EPS, annualize H1 hoặc suy reserve từ dấu gạch. H1 numerator trước khoản
reserve chưa ước tính; FY đã trừ actual reserve. Period allocation chưa đủ evidence,
`strict_normalized_ttm_eps=null`; không gọi kết quả là normalized TTM.

Issuer 18/03/2026 và reviewed H1 comparative chỉ bridge parent earnings khi FTEL
đổi phương pháp hợp nhất. Không mở revenue/total-NI hoặc strict F/M bằng bridge này.
Ledger tách actual issuance, approved plan, cash dividend và publication/effective
dates. ESOP2026 có các mốc 24/06, 03/07, 16/07 và cùng số lượng mới 10.819.301;
historical interval chưa resolved phải null. Reconciled latest ledger dùng từ
24/08 khi H1 PDF đã khả dụng, không backfill review này vào tháng 6/7.
Initial FY snapshot đã gồm ESOP/bonus2025, không cộng lại. Bonus10% approved
31/07/2026 chưa actual issuance trong accepted Aug28 slice, không tăng shares.

P/E reference dùng raw_close/TTM weighted EPS. P/B named reference dùng current
common shares × raw_close / latest reported parent equity; ghi book date 30/06 và
post-balance ESOP. Đây chưa là same-date/event-adjusted equity. Cash dividend đã
reflected trong H1 không trừ lại; 381,75B là capital reclassification có total
equity effect zero, không suy thành ESOP proceeds. Strict event-adjusted P/B null
đến khi proceeds/fees và accounting treatment đủ evidence.
Registry riêng không cluster eligible, historical identity provisional, date policy
giữ nguyên. [Config](../../configs/data/financial_fpt_ttm_valuation_v1.json),
[report](../../artifacts/reports/financial-ttm-valuation-v1/report.md).

## FPT acceptance contract và gross ESOP capital reference — 04/10/2026

[Acceptance config v1](../../configs/data/financial_fpt_acceptance_v1.json) pin
reviewed upstream manifests; [execution plan v6](../../configs/data/financial_execution_plan_v6.json)
giữ nguyên năm stages. Sáu families có reference values từ 24/08; F/M/Z là annual
2025, EPS/PE là reported TTM kết thúc 30/06/2026, P/B giữ book-date và event basis.
Không dùng các kỳ khác nhau như same-period vector hoặc tự đưa vào clustering.

`GROSS_ESOP_CAPITAL_BRIDGE_PB_REFERENCE` = raw_close × current_common_shares /
(June reported consolidated parent equity + verified registered capital increase).
Bank proceeds và registered increase đều 108.193.010.000 VND. Denominator gross
= 39.959.656.534.930 VND; chưa là current net equity. Ngày bank confirmation 25/06,
registration effective 16/07 và publication 17/07 là ba loại ngày riêng; evidence
bán niên chỉ khả dụng từ 24/08. Unknown fee giữ null, không zero-fee estimate.

Cash đã thu trước balance date không chứng minh classification tại 30/06. Khi
chưa exact advance-liability evidence, asset/liability deltas null; không cộng cash
vào assets lần nữa hoặc suy từ aggregate other payables. Nếu một template khác có
verified advance liability cùng balance date/amount, calculator mới cho phép
gross assets delta=0/liabilities delta=-capital; vẫn không chứng nhận net equity.
BCTC riêng chỉ discovery, không thay consolidated equity. Subsequent earnings,
complete events và fee treatment chưa đủ nên strict event-adjusted PB vẫn null.

Acceptance report phân biệt reference calculation coverage với production acceptance.
Strict F/M, normalized TTM, identity và scale gates không mở; no fraud/distress
threshold. Đây là quyết định implementation/reference đã nằm trong owner scope;
production variants tiếp tục MANUAL_REVIEW_REQUIRED. OCR hỗ trợ tìm ô/trang,
new facts vẫn cần explicit visual review và sealed exact hashes.

## Pilot annual VNM/PVS/ACV và disclosed basic EPS — 05/10/2026

[Config v3](../../configs/data/financial_three_symbol_pilot_v3.json) và
[report/log](../../artifacts/reports/financial-three-symbol-pilot-v1/report.md) là
reference slice riêng của FIN-D4; không overwrite matrix/readiness đã sealed.
Basic-only disclosed EPS = exact reported numerator / weighted basic common
shares cho đúng 3/6/9/12-month period. Không suy diluted=basic khi chưa có statement
no dilution, không gọi reserve chưa estimated là zero hoặc normalized numerator.
ACV FY2025 reported numerator chưa deduct reserve và khác parent NI do excluded
KCHTHK/airport security; normalized EPS/dilution giữ unknown.

F VAS debt phải gồm original long-term current portion; noncurrent loans không
được alias total original LTD. VNM vẫn total null dù 8/9 known signals. M dùng
owned tangible-PPE depreciation, không CFO total depreciation/amortization; gross
short-term trade receivables chỉ named sensitivity, không strict M. Z continuous
reference không gắn distress threshold. Supplementary 2024 statements có unknown
publication thì chỉ arithmetic reference, không all-input PIT acceptance.

P/E annual và P/B annual book-snapshot giữ basis 2025 riêng với raw market 28/08;
shares/equity không tự trở thành current effective basis. VNM TTM reference ghép
FY2025/current H1/prior comparative tại current release, không backfill revision
hoặc cộng rounded EPS. Publication mirror có byte-identical attachment và dated
HTML, quality label riêng; primary-source acceptance vẫn pending. PVS changed
prior parent profit/bonus basis cần FY bridge, ACV reviewed H1 after cutoff bị loại.
Registry metadata không cluster eligible; cả ba production/research/scale gates false.
