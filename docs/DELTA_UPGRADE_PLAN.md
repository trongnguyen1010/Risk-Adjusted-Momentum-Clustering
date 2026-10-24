# DELTA Intelligence — kế hoạch nâng cấp dữ liệu, phân cụm và UI/UX

Ngày review: **24/10/2026**. Phạm vi: bản web tại
[delta-intelligence-omega.vercel.app](https://delta-intelligence-omega.vercel.app/),
source Next.js/FastAPI hiện hành và frozen artifacts A/B/C.

**Trạng thái: đã triển khai nâng cấp local và hoàn tất R1; chưa promote model hoặc production.**
Kết quả thực thi, evidence và các điều kiện còn mở nằm ở **§11**. §§1–10 giữ
nguyên bối cảnh review/proposal trước triển khai, không phải trạng thái hiện tại.
Owner yêu cầu review kỹ, tìm phương án cải thiện và lập plan chi tiết.
Prompt Fey/Linear/Koyfin/Composer được dùng làm design brief; các nội dung như
portfolio alpha, AI signal hoặc live market regime chỉ được hiển thị nếu thực sự
có dữ liệu được nghiệm thu. Hiện không có các kết quả đó để đưa vào hero cards.

## 1. Kết luận và mục tiêu

Kết quả hiện tại **chưa đủ thuyết phục để làm hệ thống nhóm doanh nghiệp tương
đồng cho người dùng phổ thông**. K nhỏ không tự chứng minh sai, và cụm một mã
có thể phản ánh trường hợp đặc biệt có thật. Tuy nhiên, việc một cụm chứa gần
toàn bộ universe, lặp lại nhiều kỳ, khiến baseline A/B hiện tại ít hữu ích cho
mục tiêu khám phá các nhóm tương đồng. Chưa được gọi những cụm nhỏ là lỗi data,
doanh nghiệp rủi ro hoặc nhóm có thể đầu tư nếu chưa có evidence tương ứng.

Ba mục tiêu nâng cấp, nghiệm thu riêng:

1. **Dễ hiểu:** người mới biết bắt đầu ở đâu, đọc được số và hiểu kỳ dữ liệu.
2. **Đủ và minh bạch:** phân biệt dữ liệu có nhưng chưa nối, thiếu input, chưa
   tính và chưa review; không đánh đồng sáu ratios với EPS/P/E/P/B/F/M/Z.
3. **Phân nhóm có ích:** giảm hiện tượng một nhóm khổng lồ và các nhóm cực nhỏ
   bằng phương pháp được kiểm chứng, giữ baseline và toàn bộ unfavorable evidence.

UI có thể nâng cấp trên baseline hiện tại trong khi nghiên cứu mô hình được
thực hiện theo stage riêng. Không đợi có mô hình tốt mới sửa khả năng đọc.

## 2. Evidence đã kiểm tra

### 2.1. Phân cụm: vấn đề có tính hệ thống

Tổng hợp read-only từ `data/web/delta-intelligence-v1/terminal.sqlite`, đối chiếu
`artifacts/reports/cluster-comparison-v1/annual-comparison.csv` và báo cáo A/B/C:

| Mô hình | Quy mô cuối 2025 | Silhouette cuối 2025 | Lặp lại qua lịch sử |
|---|---|---:|---|
| A thị trường, k=2 | 1.384 / 26; nhóm lớn 98,16% | 0,9602 | 84/84 tháng có nhóm >90%; 19/84 tháng có nhóm <10; không có singleton |
| B tài chính, k=3 | 1.168 / 3 / 1; nhóm lớn 99,66% | 0,9045 | 10/10 FY có nhóm <10; 7/10 FY có singleton; 9/10 FY có nhóm >90% |
| C kết hợp, k=3 | 663 / 479 / 6; nhóm lớn 57,75% | 0,1657 | 7/7 năm có nhóm <10; 5/7 năm có singleton |

Các kích thước trên được sắp giảm dần; số nhãn không mang thứ tự tốt/xấu.
Trong B FY2025: **QBS** là singleton; **VTI/CAD/JOS** nằm trong nhóm ba mã.
Trong C năm 2025, nhóm sáu mã gồm DNN/GTD/NVP/TVH/VEC/VIC; không mặc định cùng
nguyên nhân với singleton tài chính của các năm trước.

Một phép mô tả bổ sung, chưa phải quality gate: số cụm hiệu dụng theo entropy
`exp(-Σ p_i ln p_i)` lần lượt khoảng **1,096 / 1,025 / 2,032** cho A/B/C cuối
2025. Nó cho thấy k danh nghĩa không đồng nghĩa có k nhóm đáng kể về quy mô;
không dùng entropy để ép các nhóm bằng nhau.

Evidence nguyên nhân hiện có:

- A: median contribution của `liquidity_21` vào between-centroid separation
  theo fitted metric là **99,997%**. RobustScaler dùng median/IQR nhưng không
  giới hạn độ lớn của tails; cần kiểm tra cả IQR gần 0, phân phối và đơn vị.
- B: replay 180 outlier rows thuộc 157 vectors đúng phép tính từ selected
  inputs, **chưa phải xác minh source facts độc lập**. QBS2025 có net margin
  khoảng −522,434 lần; CAD/VTI có liabilities/assets khoảng 131,480/127,058 lần.
  Đây là cờ kiểm tra doanh thu/tài sản rất nhỏ, unit, scope và source semantics;
  không phải quyền tự sửa hoặc loại các mã đó.
- C: năm 2024 `net_margin` đóng góp khoảng 45,03% separation; năm 2025 các
  momentum/risk features đứng đầu. Không có một nguyên nhân duy nhất cho mọi năm.
- C cân bằng variance đầu vào hai block; điều đó **không đảm bảo** mỗi block
  đóng góp 50% separation sau clustering.

Silhouette cao có thể đi cùng tình trạng nhóm khổng lồ + điểm cực đoan tách xa.
Silhouette thấp của C cũng cần xem từng cụm, từng điểm và sensitivity; không
chọn winner bằng cách so điểm A/B/C trên feature space và cohort khác nhau.
Tài liệu [scikit-learn về clustering](https://scikit-learn.org/stable/modules/clustering.html)
mô tả giới hạn geometry/metric; [silhouette analysis](https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis)
cho phép đọc cả phân bố điểm và quy mô nhóm, thay vì chỉ lấy một số trung bình.

### 2.2. Sáu chỉ số: thiếu coverage thực, không chỉ thiếu giao diện

Nguồn đang nối trong `configs/product/indicator_reference_v1.json`:

| Gói | EPS | P/E | P/B | F | M | Z | Tổng numeric rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| reviewed85, nhiều kỳ/vintage | 31 | 10 | 6 | 6 | 7 | 25 | 85 trên 11 mã |
| pilot5 FY2025 | 5 | 5 | 5 | 4 | 5 | 5 | 29 trên 5 mã |

Pilot là subset đã được tổng hợp: **không cộng hai hàng để công bố coverage**.
Các số là numeric rows, không phải số mã duy nhất hoặc bộ đủ sáu chỉ số.
Tổng report 87 rows có hai Z references bổ sung chưa nối adapter; cần tìm đúng
result/manifest và kiểm chứng trước khi hiển thị, không tự thêm hai dòng số.

Đã kiểm public: FPT hiển thị đủ sáu số; HPG báo chưa có gói đã review, nhưng vẫn
có core ratios B; VNM F-score thiếu input được giữ null theo gói pilot.
11 mã có numeric data hiện gồm ACV/BRC/FPT/GAS/GMD/MWG/PAN/PHP/VCS/VEA/VNM.
Không có evidence để hứa EPS/P/E/P/B/F/M/Z đầy đủ cho 1.172 hoặc 1.522 mã.

### 2.3. UI/UX: số đo và nút thắt

- Body hiện **13px**; CSS có **110/135 khai báo `font-size` theo px dưới 12px**.
  Đây là đếm declarations, không phải tỷ lệ DOM cuối cùng. Đã kiểm computed
  style trên public: nhiều subtitle/model dates là 9px, notes là 10px.
- `components/chart.tsx` có axis label mặc định 10px;
  `components/scatter.tsx` có axis name 9px. Tăng body không tự sửa canvas text.
- Stock page có 6 Panel trực tiếp, thêm indicator panel và members table;
  Atlas có 5 Panel, Financial 6 và Lab 8. Các con số là cấu trúc JSX, không phải
  số panel luôn ở viewport. Nhiều vùng xếp nối làm tác vụ chính bị phân tán.
- Home đang giống trang giới thiệu dự án: hero lớn, coverage counters và
  phương pháp xuất hiện trước nhu cầu tra cứu/so sánh cụ thể.
- Selector indicator đưa package/vintage lên thao tác chính; người dùng phải
  hiểu pipeline mới tìm được bộ số phù hợp.
- Chọn ngày mô hình, FY báo cáo và ngày giá định giá là ba mốc khác nhau,
  nhưng nằm trên cùng trang nên dễ bị hiểu là một ngày chung.
- API hooks lấy data theo mount; các biểu đồ/bảng sâu cần được tách tab và chỉ
  mount khi có nhu cầu. Chưa đo production performance để kết luận bottleneck.
- Cần kiểm tra thêm trạng thái cold start, accessibility, bàn phím và mobile;
  không coi việc có screenshot đẹp là nghiệm thu các mục này.

### 2.4. Đính chính sau truy lineage ngày công bố và dữ liệu quý

Owner nhắc lại cột ngày trên web và dữ liệu quý đã crawl. Đã truy lại evidence:
không được diễn giải `published_at` null trong delivery annual là toàn project
không có ngày công bố hoặc không có dữ liệu quý.

- [UI/API correction 18/10](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cafef-disclosure-ui-correction-v1/report.md)
  đã xác nhận CafeF có cột “Thời gian gửi”, raw `CreateDate`, report ID và
  `LinkFile`; ví dụ FPT FY2025 kiểm toán 20/03/2026, Q2 ban đầu 28/07/2026 và
  Q2 soát xét 22/08/2026. Adapter `cafef_financial_deep.disclosures` hiện có
  parser ra `publication_date` DATE_ONLY. Raw KBS headers còn có
  `DatePubDepartment`, cần giữ riêng basis/provider, không nhập nhằng hai nguồn.
- DATE_ONLY overlay cũng đã có từ các stage trước; `published_at` timestamp
  có thể null trong khi `publication_date`/`usable_from_date` có evidence.
  Policy owner duyệt không yêu cầu suy giờ. Thiếu giờ không phải lý do để bỏ ngày.
- Builder annual reference `financial_exploratory.py` chủ động xuất
  `published_at=None`; bulk delivery hiện chưa có join ngày/version được nghiệm
  thu cho cohort full10. Cần đo coverage metadata có thể nối từ cache, thay vì
  suy toàn bộ 11.720 observations chưa từng được crawl ngày.
- Bằng chứng date của pilot không tự áp dụng toàn cohort: phải nối đúng
  issuer/report period/scope/provider record và revision/document, giữ ngày
  provider hiển thị khác issuer-first-public nếu evidence chưa chứng minh.
- Coverage inventory có dữ liệu raw cả Q1–Q4; kiểm offline bảng đã pin cho
  1.522 candidates/2013–2025 cho thấy **137.733 quarter-statement slots** có
  `CANDIDATE_GROUPS_PRESENT`. Đây là đếm slot theo mã/năm/quý/statement,
  không phải số bộ ratios hoặc scores quý đã nghiệm thu; denominator và source
  nằm trong archived `financial-inventory1522-qa-v1`.
- Gói reviewed lịch sử có **6 kết quả EPS theo kỳ** (MWG Q3/9M2014–2015,
  FPT H12023–2024) và file monthly date reference riêng. Chúng không được phép
  gộp annual/YTD/standalone thành một series quý đồng nhất.
- B/C và presentation bundle hiện dùng financial **annual**; chưa có pipeline
  quarterly ratios/scores đầy đủ nối vào web. Không thấy lựa chọn quý trên
  web phản ánh thiếu integration/product scope, không chứng minh raw quarters không có.

Ưu tiên bổ sung D0/R0: bảng **raw metadata → date overlay → annual/quarter
delivery → API/UI**, chỉ rõ có/thiếu/chưa nối ở từng tầng. Giữ xác nhận
1.172 mã đủ 10 annual periods; tính hoàn chỉnh của core ratios, sáu score
families, quarterly coverage và date/version linkage là bốn tiêu chí khác nhau.

## 3. Hướng thiết kế và cách sử dụng prompt tham khảo

| Nguồn chính thức đã tham khảo | Áp dụng cho DELTA | Giới hạn |
|---|---|---|
| [Linear: interface refresh](https://linear.app/now/behind-the-latest-design-refresh) | Sidebar lùi về vai trò định hướng; header/actions nhất quán; giảm cạnh tranh thị giác | Không bê density của issue tracker vào bảng tài chính |
| [Koyfin: My Dashboards](https://www.koyfin.com/help/mydashboards-myd/) | Chọn ticker ở bảng cập nhật chart/detail cùng ngữ cảnh; workspace có tác vụ rõ | Không thêm dashboard builder, tài khoản hoặc live feed vào milestone này |
| [Composer](https://www.composer.trade/) | Tham khảo cách mô tả quy trình bằng khối và một workspace chính | Không thêm AI/trading/backtest không có trong data |
| [Fey](https://fey.com/) | Giữ mục tiêu clarity trong brief: khoảng trống, tiêu điểm và typography | Trang hiện tại thông báo Fey gia nhập Wealthsimple; không khẳng định đã audit app Fey hiện hành |

Đây là đề xuất thiết kế cho DELTA dựa trên nguồn công khai; không phải kiểm
toàn bộ ứng dụng sau đăng nhập của bốn sản phẩm. Không sao chép assets/branding.

### 3.1. Design tokens và khả năng đọc

| Thành phần | Mục tiêu |
|---|---|
| UI font | Inter hiện có, có glyph tiếng Việt; không thay hai font UI cùng lúc |
| Số/ticker | Geist Mono hoặc JetBrains Mono, chọn **một** sau thử glyph; bundle local, tabular-nums |
| Body, bảng, input, navigation | 15px mặc định, tối thiểu 14px cho nội dung chính; line-height 1,5–1,65 |
| Caption/badge/timestamp/axis | Tối thiểu 12px, ưu tiên 13px; giảm số ticks khi chật |
| Section/card title | 16–18px, weight 600 |
| Page title | 28–32px desktop, 24–28px mobile |
| Giá/chỉ số chính | 28–40px tùy chiều rộng; luôn có đơn vị và ngày |
| Khoảng cách | Grid 20–24px; card padding 20–24px desktop, 16px mobile |
| Hàng bảng | Khoảng 48–56px; padding dọc khoảng 14px; không tăng font rồi giữ hàng quá thấp |
| Canvas/surface/hover | `#090A0F` / `#11131C` / `#181B26`; gradient rất nhẹ trên surface |
| Border | Trắng 7% trang trí, 18% hover; focus/controls phải đủ contrast riêng |
| Semantic colors | Emerald positive, rose negative, indigo/violet interaction/quant; amber quality warning |
| Cluster palette | Categorical riêng cho 2–8 cụm, kèm label/số lượng; không gán xanh=tốt, đỏ=xấu |

Mốc tối thiểu 12px là design rule của DELTA, không phải tuyên bố WCAG quy định
font tối thiểu 12px. Contrast text thường ≥4,5:1, large text ≥3:1 theo
[W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
Không dùng chữ quá mờ để tạo cảm giác premium. Border trang trí 7% không thay
thế yêu cầu contrast của controls/focus. Không chỉ dựa vào màu để truyền trạng thái.

### 3.2. Ba tầng thông tin

1. **Tầng đọc nhanh:** một heading, một hành động chính, tối đa 3–4 số chính,
   một dòng ngữ cảnh ngày/coverage/quality. Không thêm counter chỉ để lấp bento.
2. **Tầng thao tác:** một workspace chính, desktop 8/4 hoặc 7/5; chart và vùng
   detail phản hồi theo cùng mã/cụm. Mobile xếp dọc, ưu tiên nội dung chính.
3. **Tầng đào sâu:** segmented tabs/drawer chứa full table, migration, công
   thức, protocol, hashes. Critical warning vẫn có tóm tắt cạnh kết quả;
   không giấu limitation quan trọng vào footer hoặc tooltip duy nhất.

Chỉ panel của tab active được mount/fetch. Giữ selection khi đổi tab và hỗ trợ
URL deep link; khi input đổi phải bỏ response cũ để không hiện sai mã/ngày.

## 4. Thiết kế lại từng màn hình

### 4.1. Tổng quan `/`

- Thay hero giới thiệu cao bằng header gọn và search doanh nghiệp nổi bật.
- Ba cards: A market n=1.410, B full10 n=1.172, C common n=1.148 tại kỳ cuối;
  ghi đúng kỳ/cohort. Indicator coverage là link riêng, không gộp với B.
- Workspace: preview cấu trúc + danh sách nhóm và quality summary; bấm nhóm
  mở Atlas đúng kind/date/cluster. Một CTA chính: khám phá hoặc tra cứu mã.
- Coverage timeline, protocol và provenance chuyển sang tab chi tiết/Lab.
- Không hero alpha/regime/signal giả. Sparkline chỉ dùng chuỗi đã lưu thực sự
  liên quan tới card, không thêm đường trang trí random.

### 4.2. Doanh nghiệp `/stocks`

Header: ticker + tên + sàn; giá lịch sử quan sát gần nhất và ngày/basis rõ.
Tabs: **Tổng quan | Chỉ số tài chính | Phân cụm | Dữ liệu & nguồn**.

- Tổng quan: sáu cards EPS/P/E/P/B/F/M/Z, mỗi card có số/đơn vị/kỳ/trạng thái;
  tiếp theo chart giá và summary membership A/B/C. Không mount toàn bộ bảng mã.
- Desktop sáu cards dùng 3×2; tablet 3×2 hoặc 2×3; mobile 2×3, không ép sáu
  cột chữ nhỏ. Chữ số 28–32px, labels ≥13px.
- Tab Chỉ số: tách rõ **Bộ EPS/P/E/P/B/F/M/Z** và **Sáu ratios dùng cho B/C**;
  lịch sử theo kỳ; biểu đồ chỉ nối các kỳ/basis tương thích, giữ gaps.
- Mỗi F/M/Z có mô tả, đúng formula variant, components và input thiếu **nếu
  source có**. Không áp ngưỡng phổ quát hoặc kết luận gian lận/phá sản.
- Tab Phân cụm: membership A/B/C, hồ sơ cụm, vị trí tương đối của mã và peer
  list. Peer dựa trên rule/artifact công khai; chưa có thì không giả khoảng cách.
- Tab nguồn: full provenance, source package, FY/period_kind, price date,
  balance date và snapshot vintage. Hash/code không nằm trên mặt chính.
- Default reference do policy minh bạch chọn từ đúng gói được review; không
  ghép từng số tốt nhất từ nhiều vintages. Người dùng vẫn đổi gói trong phần nâng cao.
- Thời điểm model và ngày định giá indicator độc lập, luôn có nhãn; không
  khiến PE/PB 22/04/2026 trông như đã biết tại 31/12/2025.

### 4.3. Atlas `/atlas`

Header: chọn A/B/C bằng tên dễ hiểu, kỳ, trạng thái quality. Bên dưới chỉ một
workspace gồm visualization lớn và panel hồ sơ cụm đang chọn.
Tabs: **Khám phá | Hồ sơ & đối chiếu | Thành viên | Chất lượng**.

- Khám phá: size bars luôn hiện; scatter chọn hai trục và preset có lý do;
  tooltip có ticker, raw values, đơn vị, cluster, ngày. Không mặc định trục
  chỉ vì trục đó tạo hình tách đẹp. Cho xem IQR/median theo feature ở panel bên.
- Hồ sơ: dot/boxplot hoặc heatmap percentile theo feature; ghi cohort/scaling
  hiển thị. Không đặt raw VND và ratios lên một thang chung. Median/IQR là
  chính, mean có thể xem thêm. Không gọi percentile cao luôn là tốt.
- Thành viên: mặc định 5–7 cột cần thiết, column chooser cho phần còn lại;
  lọc cụm đồng bộ chart/list, drill-down mở drawer và link trang doanh nghiệp.
- Chất lượng: size distribution, largest share, singleton/min-size, feature
  contribution nếu artifact có, silhouette distribution nếu được export,
  saved metrics và migration. Không tính model/quality metrics mới ở browser.
- PCA chỉ thêm khi có artifact projection fit/version được review và
  explained variance; raw axes luôn còn. UMAP/t-SNE không ở đợt đầu và không
  được dùng hình vẽ làm bằng chứng chọn model.
- Cụm rất nhỏ có badge “Nhóm rất nhỏ · cần xem xét”, chưa được tự gọi anomaly.
  Nhãn mô tả dựa trên profile, luôn giữ ID/version; không đặt tên mua/bán/tốt/xấu.

### 4.4. Financial `/financial` và Research Lab `/lab`

- Financial: default view là một feature distribution và group comparison;
  tabs **Phân bố | Đối chiếu A/B/C | Coverage**. Matrix không mở cùng tất cả
  boxplots/bảng. Không có model cho FY nào thì empty state giải thích chính xác.
- Lab: trang cho người cần kiểm chứng, không phải nơi người mới bắt buộc ghé.
  Tabs **Phương pháp | Chất lượng | Nguồn & phiên bản**. Protocol/hashes đặt
  trong accordion; technical tests và research readiness trình bày tách biệt.
- Sidebar gọn 5 destinations, giảm lặp lại ba model links nếu selector đã có
  trong workspace. Command palette đã tồn tại: nâng khả năng nhìn thấy và
  kết quả tìm kiếm, không xây một search thứ hai.

### 4.5. Loading, errors, tương tác và accessibility

- Skeleton đúng kích thước layout; API chậm có lời giải thích và Retry,
  không spinner vô hạn hoặc kết luận dữ liệu thiếu khi service chưa sẵn sàng.
- Tooltip dễ đọc, chart labels 12–13px; giảm grid/tick thay vì giảm chữ.
  Không smooth đường giá qua gap hoặc làm sai điểm quan sát.
- Motion 120–200ms, tôn trọng reduced-motion; glow nhẹ ở active/focus,
  không phát sáng đồng thời mọi card. Không dùng animation để che loading.
- Tab semantics, arrow keys, Escape/focus restore cho drawer/command palette;
  biểu đồ có text summary/table alternative cho thông tin chính.
- Controls mục tiêu 40–44px theo design rule; kiểm WCAG 24×24px hoặc spacing
  exceptions theo [target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- Test text zoom 200%, layout 320/390/768/1280/1440px; page không cuộn ngang,
  bảng/chart có vùng cuộn riêng khi cần. Tham chiếu [W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).

## 5. Kế hoạch coverage sáu chỉ số

### D0 — kiểm kê trước khi phát triển thêm

Thực hiện kiểm kê ngày công bố/quý theo §2.4 trong cùng stage, trước mọi đề
nghị crawl thêm. Reuse DATE_ONLY policy đã owner duyệt; không xin duyệt lại
policy chỉ vì timestamp null. Chỉ mở quyết định mới nếu thực sự thay basis,
scope hoặc acceptance. Định lượng phần cache join được và blockers riêng.

Tạo bảng coverage có schema: `security/ticker, FY/period, period_kind, variant,
source_run, vintage, family, value_present, status, missing_inputs, evidence_ref`.
Dedup theo identity của observation và provenance; không chỉ ticker+FY, không
trộn annual/YTD/quarter hoặc hợp nhất vintages theo ô.

Phân loại tối thiểu: AVAILABLE_REVIEWED, AVAILABLE_NOT_CONNECTED,
MISSING_INPUT, NOT_COMPUTED, REVIEW_PENDING, NOT_APPLICABLE, SOURCE_UNAVAILABLE.
Không suy missing reason khi source chỉ cho biết unknown. NOT_APPLICABLE chỉ
khi methodology cho family/loại doanh nghiệp có quy tắc rõ.

Output: coverage theo family/mã/kỳ, bảng full6 trong **cùng gói**, backlog các
input còn thiếu. Đối chiếu hai Z rows chưa nối với source manifest. Ưu tiên
các mã team demo rồi mở rộng theo khả năng inputs; không hứa đủ cả universe.

### D1 — mở rộng adapter và cách giải thích

- Chỉ nối thêm kết quả đã review, pin manifest/CSV hashes, giữ decimal text.
- API bổ sung coverage và missing reasons có nguồn; indicator schema thành
  typed contract, không để frontend đoán trạng thái từ chuỗi tự do.
- Full6 không đồng nghĩa current/PIT/production-ready. Coverage toàn ứng dụng
  phải ghi rõ denominator là cohort nào và số kỳ; tránh cộng trùng pilot5.
- EPS cần đúng reported hoặc weighted-average share basis; PE/PB cần dated
  price/share/book basis; F/M cần paired periods/input components; Z đúng variant.
  Thiếu input thì lập acquisition/computation stage riêng, không lấy ratios
  hiện có để bịa ra bộ score đầy đủ.

## 6. Cải thiện phân cụm: protocol đề xuất tại thời điểm review

R1 đã được owner cho phép thực hiện bằng yêu cầu triển khai hoàn chỉnh plan
trong phiên này; protocol, kết quả và giới hạn promotion ở §11. R2 không mở
vì cả ba family có candidates đạt geometry/seed targets.

### 6.1. Vì sao chưa chốt k mới

K=2 hoặc 3 có thể đúng cho một mục tiêu, nhưng chưa có evidence về k phù hợp
cho nhóm peers ở đây. Tăng k trực tiếp có thể phân thêm outliers trong khi
phần lớn mã vẫn ở một nhóm. Cũng không ép balanced K-Means hoặc tách theo
quantile chỉ để card có số lượng đẹp; đó là thay mục tiêu nghiên cứu.

**MANUAL_REVIEW_REQUIRED trước model run mới.** `AGENTS.md` quy định thay
“M2 methodology” là methodology-sensitive và phải “STOP khi cần approval”.
Owner hiện yêu cầu review/plan; approval chạy C cũ không tự áp dụng cho protocol
preprocessing/k/algorithm mới dưới đây. Có thể hoàn tất D0 và UI trước gate này.

### 6.2. R0 — kiểm tra nguồn và geometry, không fit lại

1. Pin source runs, hashes, feature order, eligibility và model versions.
2. Trace QBS/CAD/VTI/JOS cùng toàn bộ singleton/tiny clusters các kỳ; đối
   chiếu numerator/denominator, source partitions, consolidated/standalone,
   unit, sign, year-pair và evidence đã có. Arithmetic PASS không đóng source QA.
3. Kiểm tra các ví dụ C2025 như DNN có momentum lớn và liquidity=0: nguồn
   prices/volume, stale observations, share events và acceptance policy.
   Không tự kết luận giá sai hoặc loại giao dịch kém thanh khoản.
4. Thống kê per snapshot: quantiles, zero/missing fractions, IQR gần 0,
   tails sau scaler, feature correlation và contributions vào khoảng cách.
   Đặc biệt bốn momentum horizons có tương quan và có thể nhận trọng số lặp.
5. Phân biệt financial sectors nếu có classification đáng tin: ratios hiện
   hành có phù hợp ngân hàng/bảo hiểm/chứng khoán không? Chưa có taxonomy
   versioned thì ghi thiếu, không tự gán ngành từ tên công ty.
6. Row có lỗi được xác minh đi vào delivery version mới theo policy; row
   hợp lệ nhưng cực đoan vẫn được bảo tồn. Không âm thầm winsorize/quarantine.

Deliverables: bảng trace nguyên nhân, source verdict và queue chưa giải quyết;
descriptive diagnostics có pins. Nếu nguồn chưa đạt, báo rõ giới hạn trước R1.

### 6.3. R1 — thí nghiệm preprocessing và k có giới hạn

Đề xuất vòng đầu giữ K-Means để tách ảnh hưởng preprocessing khỏi thuật toán.
Giữ source/cohort/features cố định trong mỗi so sánh. Thử A/B/C riêng, không
gộp sáu composite scores vào C vì thiếu coverage và dễ double-count inputs.

| Recipe | Định nghĩa dự kiến | Lý do / giới hạn |
|---|---|---|
| P0 | Frozen A/B/C hiện tại, đọc artifact | Mốc đối chiếu bắt buộc, không ghi đè |
| P1 | Yeo–Johnson từng feature (`standardize=False`) + StandardScaler | Giảm skew, hỗ trợ số âm/0; phải lưu lambda/scaler và kiểm feature hằng |
| P2 | QuantileTransformer output normal, `n_quantiles=min(1000,n)`, seed42, dùng toàn cohort fit | Giảm leverage của tails; làm mất thông tin độ lớn khoảng cách, cần báo tradeoff |
| P3 | Signed log `sign(x)*log1p(abs(x)/s_j)` rồi RobustScaler; `s_j`=median của abs(nonzero), nếu feature toàn 0 thì giữ 0 | Giữ dấu/thứ tự, giảm tail; định nghĩa scale/basis cụ thể trong protocol, không lẫn log display |

Đây là **candidate recipes** để chốt protocol, chưa phải feature/model policy.
Các preprocessors được fit riêng snapshot cho descriptive reference; không
fit pooled future years. Nếu chuyển predictive/PIT, phải có training window
và availability policy riêng. [Scikit-learn scaler comparison](https://scikit-learn.org/stable/auto_examples/preprocessing/plot_all_scaling.html)
minh họa các tradeoff; không có scaler mặc nhiên giải quyết mọi outlier.

- Screening `k ∈ {2,3,4,5,6,7,8}` cho P1/P2/P3, seed42,
  `n_init=20, max_iter=300`. Với C, đề xuất chuẩn hóa tổng variance mỗi block
  sau recipe: `X'_b = X_b * sqrt(0,5 / Σ_j Var(X_bj))`, variance dùng `ddof=0`
  trên cohort của snapshot. Với block unit-variance từng chiều, công thức trở
  lại `sqrt(0,5/d_b)`. Nếu tổng variance block bằng 0 thì fail recipe/snapshot
  rõ ràng, không chia 0 hoặc âm thầm đổi weights. Đây là policy mới cần duyệt;
  không tự coi RobustScaler đã cho variance1, không hứa separation 50/50.
- Screening cả ba family ở 5 mốc cuối năm 2019–2023: tối đa **315 fits**
  (3 recipes × 7 k × 3 families × 5 snapshots), không lặp lại baseline P0.
  Đây là exploratory screening đã biết dữ liệu, không phải holdout mới.
- Shortlist tối đa 2 recipes/k mỗi family; đánh giá thêm seeds 0–8 trên
  cùng 5 snapshots: tối đa **270 fits**. Seed42 đã có ở screening; không bỏ
  seed bất lợi. Chưa chạy bootstrap lặp hàng nghìn lần trong vòng đầu.
- Tái đánh giá shortlist trên toàn bộ 84/10/7 native snapshots với cấu hình
  chốt; 2024–2025 chỉ là retrospective sensitivity, không gọi untouched test.
- Chọn một recipe/k toàn series trong mỗi family cho release nếu evidence
  ủng hộ. Không chọn k tốt nhất từng ngày để hình nào cũng đẹp; adaptive-k
  cần mục tiêu và protocol riêng.

R1 không mặc định clipping hoặc loại outliers. Nếu muốn winsorization,
feature-group reweight/PCA hoặc sector-specific cohorts, mở ablation preregister
riêng với counts/coverage delta và nguồn gốc từng quyết định.

### 6.4. R2 — comparator khi R1 chưa giải quyết được

Không grid search mọi thuật toán cùng lúc. Chốt preprocessing từ R1 trước.

- **Ward agglomerative** k=2..8 trên shortlist, metric Euclidean: kiểm cấu trúc
  phân cấp; vẫn nhạy với outliers, không coi là guaranteed fix.
- **HDBSCAN** là nhánh tùy chọn tách nhóm mật độ và noise, với
  `min_cluster_size=max(10,ceil(q*n)), q∈{0,01;0,02;0,05}` và
  `min_samples∈{5,10}`. Cần report noise% và coverage; nếu phần lớn mã là
  noise hoặc chỉ còn một nhóm thì đó không phải thành công cho peer grouping.
  [API chính thức](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html)
  có `min_cluster_size` và noise labels; cần contract mới trước khi đưa lên web.
- Không ép điểm noise về cụm gần nhất để đạt coverage. Không ép nhóm đều.
  Giải pháp có thể là peer groups + tập cần review riêng, nhưng chỉ sau kiểm chứng.
- GMM/k-medoids/spectral không đưa vào vòng đầu; thêm khi failure mode cụ thể
  cho thấy cần, thay vì tăng phạm vi thử nghiệm không kiểm soát.

### 6.5. Scorecard và quy tắc quyết định

Tách bốn lớp, không gom thành một điểm tổng hợp tùy ý:

1. **Validity:** source/schema/unit/coverage, không NaN/inf hoặc drop âm thầm;
   danh sách exclusions, zero-variance và mappings được lưu đầy đủ.
2. **Geometry:** size distribution, largest share, singleton/tiny counts,
   effective-k, within/between dispersion, per-feature/block contribution,
   silhouette mean/per-cluster/distribution, DB và CH.
3. **Robustness:** ARI/NMI giữa seeds trên cùng cohort; sensitivity khi đổi
   preprocessing. Adjacent-date ARI chỉ trên common membership, kèm entered/
   exited và n; thị trường thay đổi không mặc định là model lỗi.
4. **Usefulness:** median/IQR profiles có khác biệt có thể giải thích; kiểm
   các peers cụ thể và khoảng cách/rank theo rule công khai. Nhóm lớn bị phá
   nhỏ nhưng không có đặc điểm phân biệt chưa đạt mục tiêu.

Ngưỡng screening **đề xuất để owner chốt trước run**, không phải định luật:

- Tiny flag khi size < `max(10,ceil(0,01*n))`; luôn liệt kê singleton.
- Dominant flag khi largest share >90%; single-feature separation >80% là
  cờ review geometry, không tự kết luận input sai.
- Candidate cho broad peer grouping: hướng tới ≥80% screening snapshots không
  có dominant flag và không có tiny cluster; median seed ARI ≥0,80 là mục tiêu
  độ tái lập. Nêu cả worst cases; không đạt thì không promote hoặc chỉnh ngưỡng
  sau khi xem kết quả để cho PASS.
- Không bắt các cụm bằng nhau hoặc yêu cầu silhouette > một số phổ quát.
  Comparisons nội bộ giữ cùng feature/cohort/metric; giữa transform dùng
  scorecard đa chiều và một reference-distance diagnostic đã preregister,
  không xếp hạng chỉ bằng silhouette trên geometry khác nhau.
- Nếu nhiều candidate tương đương, ưu tiên đơn giản và ít nhóm hơn **khi** vẫn
  đạt usefulness/robustness. Không mặc định k=5/6 là đích phải đạt.
- Không dùng return/Sharpe/ROI hoặc hình PCA/UMAP để chọn cấu hình.

Outcome được phép là “chưa có phân cụm đáng tin cho mục tiêu peers”; UI tiếp
tục ghi exploratory. Không bắt buộc công bố winner nếu data không hỗ trợ.

## 7. Thay đổi kỹ thuật cần chuẩn bị

| Vùng source | Việc dự kiến |
|---|---|
| `web/frontend/app/globals.css` | Hợp nhất tokens/typography, bỏ overrides chữ nhỏ; responsive + focus/reduced-motion |
| `app/layout.tsx`, `package.json` và lock | Thêm một local mono font được pin; giữ Inter và glyph tiếng Việt |
| `components/shell.tsx`, `ui.tsx` | Header/search/segmented tabs, sidebar giản lược, empty/error/loading patterns |
| `app/page.tsx`, `stocks/page.tsx`, `atlas/page.tsx`, `financial/page.tsx`, `lab/page.tsx` | Tách primary workflow khỏi deep-dive, lazy panels, giữ deep links |
| `components/chart.tsx`, `scatter.tsx` | Canvas typography, units/tooltips, semantic/categorical palette, accessible summaries |
| `components/indicator-reference.tsx` | Sáu cards đầy đủ trạng thái, kỳ rõ, history/source drill-down |
| `components/members-table.tsx` | Default 5–7 cột, row spacing, selection đồng bộ, reset paging đúng |
| `lib/selection.ts`, `api.ts`, `types.ts` | URL tabs/group/source, request lifecycle/dedup có cache key đầy đủ, typed availability |
| `web/backend/app/indicators.py`, `schemas.py` | Coverage/reasons từ source, typed response, preserve decimal/null và vintages |
| `src/delta_t1/product/terminal_export.py` | Presentation bundle version mới chỉ khi thêm payload; giữ hashes/version và verifier |

Các blocker khi tăng k/đổi thuật toán cần xử lý **trước model promotion**:

- `lib/format.ts` chỉ có ba cluster colors; một số chart truy cập trực tiếp
  `COLORS[cluster]`. Cần palette/mapping đủ k và cluster IDs không liên tiếp.
- `financial/page.tsx` hard-code `[0,1,2]` trong matrix. Rows/columns phải lấy
  từ labels thực tế của hai model, kể cả k khác nhau.
- `repository.py` migration đang duyệt `permutations(range(k))`: tăng k gây
  factorial cost; cần maximum-weight assignment trên contingency, với unmatched
  groups và k nguồn/đích khác nhau. Không thay ID gốc; test rectangular matching.
- Negative noise label, unknown/unassigned và model-specific k chưa có
  contract hoàn chỉnh. Không chỉ tăng palette rồi coi đã hỗ trợ HDBSCAN.
- Version/run lựa chọn phải là một phần cache key/deep link; không trộn label
  cũ với profile/projection từ experiment khác.
- Browser không fit transform/model, tính lại quality metrics hoặc lấy nguồn
  raw. Projection, representative peers và diagnostics mới nếu có cần export
  artifact riêng, hash/schema rõ, được verifier kiểm.

## 8. Thứ tự triển khai và deliverables

Giữ single-agent workflow và từng stage có điểm dừng. Bảng này là backlog,
không cấp quyền tự chạy toàn bộ research stages trong một session.

| Stage | Công việc / đầu ra | Điều kiện nghiệm thu |
|---|---|---|
| U0 — plan hiện tại | Evidence, scope, tokens, screen structure, protocol proposal | Review rõ fact/hypothesis/proposal; không refit hoặc đổi frozen artifacts |
| D0/R0 — kiểm kê | Coverage ledger + source/outlier trace + geometry diagnostics | Mọi số có source pin; unknown giữ unknown; không acquisition mới ngoài scope |
| U1 — design foundation | Tokens, font, shell, chart axes, reusable states; preview Home + FPT | Text chính ≥14px, captions/axes ≥12px; desktop/mobile đọc được; bindings giữ nguyên |
| U2 — enterprise workflow | Stock tabs + sáu cards + period/history/source; adapter D1 | FPT6/VNM thiếu/HPG chưa có/source lỗi đều đúng; không ghép vintage |
| U3 — cluster workspace | Atlas/Financial tabs, profiles, A/B/C comparison và tables | Một primary workspace, filter/URL đồng bộ, vẫn trung thực với baseline quality |
| R1 — approved experiment | Versioned preprocessing/k screening, seeds, full scorecard | Owner duyệt protocol trước run; không loại bất lợi; không hứa winner |
| R2 — optional comparator | Ward/HDBSCAN nếu cần, noise/coverage contract | Có lý do mở stage, dependencies/params/pins và metrics nhất quán |
| I1 — integration | Model/version/projection adapters, dynamic k, migration fix | Labels/profiles/memberships khớp cùng run; contract tests không mất assertions |
| Q1 — UX/data release | Public preview nghiệm thu, source/docs updated, rollback | Checklist dưới đây PASS hoặc giới hạn được báo cụ thể; production không lệch dataset |

Ưu tiên thực tế: **D0/R0 → U1 → U2 → U3**, đồng thời hoàn tất protocol cho R1.
Một UI release tốt hơn có thể ra trước model release. R2 chỉ mở nếu R1 chưa đủ.
Không gắn deadline cứng cho source-fact review khi chưa biết input blockers.

## 9. Tiêu chí nghiệm thu và verification

### UX và thiết kế

- Home/Stock/Atlas mỗi trang có một hành động chính, ≤4 hero KPIs; trang đầu
  không mount full raw tables/matrices/protocol. User vẫn tìm được detail bằng
  tab có tên rõ, không phải mò accordion khắp trang.
- Không còn text UI/canvas dưới 12px; body/table chính 14–15px, số tabular mono;
  giữ units và tiếng Việt có dấu. Đo computed style và canvas options, không
  chỉ grep CSS. Contrast/focus được kiểm, không tuyên bố WCAG toàn bộ chỉ từ màu.
- 320/390/768/1280/1440px, zoom200%, keyboard-only; không che nút/nhãn bởi drawer,
  chart tooltip hoặc sticky header. Touch target và reduced-motion hoạt động.
- Usability với ít nhất 3 người mới trong nhóm: tìm FPT và đọc EPS+kỳ dưới
  30 giây; tìm lý do HPG thiếu score dưới 30 giây; so sánh hai cụm dưới 60 giây.
  Đây là target đánh giá, chưa có kết quả thử nghiệm; ghi task failures thực tế.

### Data và model

- Replay fixture/API cho FPT full6, VNM partial, HPG missing, unknown ticker,
  invalid date, duplicate family, hash mismatch, source package absent.
- Đổi ticker/kind/date/tab liên tục, đổi page/filter và Back/Forward: không
  hiện data cũ dưới header mới; selection có thể chia sẻ bằng URL.
- New-model tests: feature order/scaler/weights, labels theo đúng experiment,
  variable k, noise/unmatched groups, rectangular migration, palette và matrix.
- Bundle verifier kiểm counts/hashes/schema, mappings và presentation aggregates
  với source artifacts; research verifier độc lập kiểm preprocessing/assignments.
- Baseline A/B/C vẫn chọn/xem lại được. Chưa có PIT publication/identity
  evidence thì strict gates tiếp tục đóng; seed stability không tự mở gates.

### Performance và release

- Đo baseline API/transfer/render trước tối ưu; phân biệt warm/cold start.
  Warm targets dự kiến: chart interaction <100ms, đổi tab đã cache <200ms,
  primary workspace usable <3s trên điều kiện test được ghi rõ. Không dùng
  các số này làm SLA hoặc báo PASS khi chưa đo.
- Không fetch/mount deep panels chưa mở. Lazy ECharts, tránh init/dispose do
  tab hidden không có kích thước; cache có bound, full key và invalidation version.
- Cold start Render có trạng thái dễ hiểu, retry có giới hạn; không dùng
  số giả hoặc fallback local. Đo thực rồi mới cân nhắc đổi hosting plan/cache.
- Targeted tests subsystem bị sửa; frontend typecheck/build;
  `python -m compileall -q src tests scripts run.py`; `node --check web/app.js`.
  Full repository gate theo scope thay đổi; timeout trước đây không được gọi PASS.
- Preview có cùng bundle/source revisions; nghiệm thu xong mới promote production.
  Ghi app commit + bundle hash + model run + Dataset revision; rollback theo bộ.
  `web/README.md` runbook và docs contract/status được cập nhật sau implementation.

## 10. Bàn giao cho agent thực hiện

Đọc `AGENTS.md`, `docs/README.md`, tài liệu này và `web/README.md`; kiểm working
tree hiện tại trước khi sửa. Trước Next.js changes đọc bundled Next docs theo
`web/frontend/AGENTS.md`. Không reset/sửa immutable data hoặc ghi đè thay đổi
đang có. Không spawn subagent theo single-agent policy.

Task đầu tiên nên giao: **D0/R0 — kiểm kê coverage và trace các nhóm nhỏ,
không refit, không acquisition**. Task UI đầu tiên: **U1 — typography/tokens/
shell và bố cục Home+FPT**, có preview desktop/mobile trước khi nhân rộng.
Mỗi stage bàn giao files changed, evidence, tests thực chạy, screenshots khi
có UI changes và unresolved gaps. Plan này không phải xác nhận đã upgrade web.

## 11. Thực thi nâng cấp — 24/10/2026

Yêu cầu mới của owner là thực hiện hoàn chỉnh plan, nên phiên này triển khai
nhiều stage và execute R1 theo giới hạn cụ thể, single-agent. Không acquisition,
PDF/OCR, sửa raw/canonical hoặc ghi đè frozen A/B/C. **Engineering local đã có
kết quả kiểm chứng; toàn bộ plan chưa được gọi COMPLETE vì source/usefulness
review, human usability và public release còn mở.**

### 11.1. Deliverables và trạng thái từng stage

| Stage | Kết quả thực tế | Trạng thái |
|---|---|---|
| D0 | Ledger 576 ô theo package/cohort/family; 87 numeric observations độc lập về identity/provenance, loại 29 duplicate deliveries của pilot; full6 theo đúng gói và backlog input | PASS kiểm kê |
| R0 | 101 snapshots; raw quantiles/zero/missing/IQR/correlations, tails theo **frozen scaler**, baseline separation evidence, trace 180 tiny-member observations và giá/volume cho nhóm market/C | PASS diagnostics; source facts REVIEW_PENDING |
| U1 | Inter + JetBrains Mono pin local có Vietnamese subset; body 15px, main table/control 14px, caption/canvas ≥12px; shell năm destinations, focus/reduced-motion/loading/retry | PASS local browser gate |
| U2 / D1 | Stock bốn tabs, sáu cards kể cả null, history/source theo vintage; hai Z BRC/VNM FY2024 đã nối riêng; typed availability và calculation components/missing dependencies từ manifest | PASS fixtures và browser |
| U3 | Home ưu tiên search; Atlas bốn tabs và size bars; median/IQR, table filter đồng bộ URL; Financial ba tabs và matrix từ actual labels; Lab ba tabs | PASS local browser gate |
| R1 | 315 screening + 270 additional-seed + 172 native-series fits bổ sung; 757 model configurations, 217 saved transforms; verifier độc lập PASS | PASS descriptive experiment; NOT PROMOTED |
| R2 | P1/P3 k=2 đạt screening/seed targets cho cả A/B/C; không có lý do mở thêm Ward/HDBSCAN ở vòng này | Không cần mở theo conditional plan |
| I1 | Palette tám màu, noncontiguous/negative labels; rectangular Hungarian matching, unmatched groups; matrix động; cache/deep links pin bundle revision/model version và từ chối revision khác | PASS baseline + R1 preview integration; chưa promote, chưa thêm projection |
| Q1 | Production build, targeted tests, bundle/source verifier, browser suite và local performance có evidence | PARTIAL: full-suite còn một fixture legacy thiếu; public/human acceptance chưa thực hiện |

### 11.2. Data/source evidence

Audit cuối nằm tại `artifacts/reports/delta-upgrade-d0-r0-release-review/` (local, ignored).
Manifest SHA-256: `a17bd9ca9995f10f0c66acf7ce88e22b56f3f429f4798914f47eb21f050c60ad`.

- `indicator-coverage.csv`, `package-observation-links.csv`, `full6-cohorts.csv`,
  `missing-input-backlog.csv`: dedup bằng cohort + family + variant + dependency
  provenance + period/bases; **không** bằng ticker/FY đơn thuần. 87 không phải
  87 mã; vẫn 11 mã có numeric observations. Không ghép gói để tăng full6.
- `geometry.csv`, `fitted-scaled-geometry.csv`, `correlations.csv`,
  `snapshot-sizes.csv`, `baseline-separation-drivers.csv`: có source pins,
  không fit lại baseline hoặc tính metrics trong browser.
- `tiny-source-trace.csv`, `tiny-market-price-trace.csv`: giữ selected source,
  numerator/denominator replay evidence đã có và các vấn đề còn mở. Arithmetic
  PASS không đóng source QA. Không có versioned sector taxonomy/share-event
  acceptance mới; không tự sửa hoặc loại QBS/CAD/VTI/JOS/DNN.
- Hai Z FY2024 lấy từ `history_cached_fact_reconciliation_v1/97dae86b236d38f54b88`
  trong archive, lọc đúng hai `matches_existing_value=False` rows theo manifest.
  BRC là comparative FY2024 trong FY2025 PDF vintage; không gán ngược PIT.
- VNM F-score vẫn null. `calculation-details.json` và `metric-dependencies.json`
  đã pin cho biết thiếu `long_term_debt_including_current_portion` FY2024/FY2025;
  tám signals và interval trong source được giữ ở phần đào sâu, không tự điền F.

### 11.3. R1, recovery và quyết định promotion

Protocol executable: [`delta_upgrade_r1_v1.json`](../configs/experiments/delta_upgrade_r1_v1.json).
Run cuối: `data/experiments/delta_upgrade_r1_v1/results/09fa9b1ea51d861edbd5`.
Manifest SHA-256: `90308cad3ac41efac61a4ee9b3c514827c7cfc1602008e2f1bcf754424bfaa8c`.

Lượt đầu `cdc9e5247e6ac2823804` gặp lỗi cache ghi lại transform đã tồn tại sau
khi giải phóng RAM. Giữ nguyên cả run/failures. Runner đã sửa để replay saved
parameters; recovery xác minh pins, tái dùng 401 models và thực hiện 356 fits còn
thiếu, **không lặp lại 315 screening fits**. Run cuối có 0 failures. P0 chỉ đọc.

Verifier độc lập không fit: kiểm hash nguồn/result, feature/cohort order,
transform parameters, variance blocks, nearest-centroid labels, inertia,
profiles và 6.056 sampled point silhouettes trên toàn bộ 757 models; PASS.
Không gọi dữ liệu 2024–2025 là untouched holdout.

| Family | P3 k=2 tại cuối 2025 | Largest share tệ nhất toàn native series | Median pairwise seed ARI |
|---|---|---:|---:|
| A, 84 tháng | 1.015 / 395 | 71,99% | 0,9881 |
| B, 10 FY | 735 / 437 | 70,22% | 0,9966 |
| C, 7 năm | 622 / 526 | 62,05% | 0,9867 |

P1 k=2 cũng nằm trong shortlist; cuối 2025 lần lượt 889/521, 758/414, 643/505,
median pairwise seed ARI bằng 1 cho mỗi family. Hai candidate không có tiny hoặc
dominant flag trên toàn native series. Những recipe/k khác và mọi unfavorable
seed/snapshot vẫn nằm trong scorecard/models, không chỉ giữ kết quả đẹp.

**Chưa promote:** geometry và seed stability đạt mục tiêu không chứng minh
source facts hoặc usefulness. Ví dụ peers của FPT thay đổi theo recipe; danh
sách không được gọi là cùng ngành hoặc khuyến nghị đầu tư. Cần review nguồn,
median/IQR profiles và peer examples trước khi owner chọn release configuration.
Ứng dụng local giữ frozen baseline A/B/C làm mặc định. Selector phiên bản trong
Atlas/Stock/Financial cho phép xem P1/P3 ở chế độ **research preview chưa promote**;
Lab có links trực tiếp. Mọi endpoint snapshot/members/stock/history/compare/matrix/
migration dùng cùng version và revision; không âm thầm thay labels đang xem.
Không thêm PCA/UMAP hoặc HDBSCAN/noise model lên web.

### 11.4. Verification và điều kiện còn mở

- 34 targeted API/indicator/alignment/preprocessing/protocol tests: PASS; gồm
  decimal/null, sparse/partial/full6, unknown ticker/invalid dates, duplicate
  family, manifest mismatch, absent source, supplementary evidence, rectangular
  matching, noncontiguous IDs/noise và large k không factorial.
- Frontend typecheck + production build PASS; compileall và JS syntax PASS.
  `node scripts/test_delta_frontend.cjs` PASS cho sparse palette/negative labels,
  null/zero và bảo toàn typed identifiers/Decimal/source evidence qua lớp dịch.
  Synthetic smoke `run-20261024T094923Z-40f46ba2` complete.
- Actual-bundle verifier PASS: 101 snapshots, 219 profiles, 3.214.287 prices,
  22 upstream hashes. SQLite giữ hash
  `66c9b0a48722d5d589e6b15ffae78b22de51162132b0681a7d3d133d4f4dc4f1`.
- Browser suite `scripts/verify_delta_ui.cjs`: 25 combinations của năm trang ×
  320/390/768/1280/1440px; không page overflow hoặc visible DOM text dưới 12px;
  canvas minimum 12px; URL Back/Forward, arrow tabs, drawer/command focus,
  delayed ticker race, no deep-panel fetch, FPT/VNM/HPG, error/retry, revision guard và CSS zoom
  200% PASS. Screenshots/JSON: `.tmp/upgrade-ui/final/`. CSS zoom kiểm reflow,
  chưa thay thế nghiệm thu browser chrome zoom và assistive technology.
- Contrast đã kiểm computed trên FPT và sửa các caption/nav/footer mờ;
  không tuyên bố chứng nhận WCAG toàn ứng dụng.
- Full repository gate cuối: **984 tests, 1 error, 4 optional Streamlit skips**,
  385,29 giây thực thi test. Error duy nhất: thiếu immutable legacy fixture
  `artifacts/financial_pit/fin-pit-1a-20261004T015420Z-continuation-preflight-v2/next_network_proposal.json`.
  Không tìm thấy bản gốc trong checkout/archive hiện có; không sinh fixture giả
  hoặc bỏ assertion. Log `.tmp/upgrade-full-suite-preview.log`; full gate chưa PASS.
- Local performance có đối chiếu HEAD `a03a7fe` dựng riêng: Edge headless,
  localhost API, 1440×1000, không throttle, reduced-motion, warm cache, ba mẫu
  hard-navigation/trang. File `.tmp/upgrade-ui/performance.json` ghi raw samples.
  Đây là retrospective baseline, không phải phép đo trước triển khai hoặc SLA.
  Stock/Atlas giảm request; Home payload tăng do preview C có 14 features, và
  không khẳng định mọi trang đều nhanh hơn. Tab cache và chart-handler probe
  chỉ mô tả điều kiện local đã ghi, không phải hosting cold-start.

**Để đóng Q1:** cần bản gốc fixture legacy hoặc quyết định migrate fixture có
provenance; source/peer review cho promotion; ít nhất ba người mới thực hiện
usability tasks với thời gian/failures thực; browser zoom/keyboard/contrast
nghiệm thu bổ sung; public preview/cold-start và release acceptance. Dataset
publisher mới chỉ dry-run, chưa upload source additions; chưa push/deploy hoặc
promote production. Cần publish đủ indicator supplements, pin Dataset revision,
deploy API trước frontend và giữ rollback cùng app/bundle/model revision.

I1 preview bundle: `data/web/delta-r1-preview-v1/2a79f72e82541b0d6556/` (9,3MB JSON + manifest),
pin tại `configs/product/model_previews_v1.json`. 202 native snapshots P1/P3 và
186.228 observations được verifier đối chiếu với labels/medians/IQR/metrics trong
source models; means là presentation aggregates được replay độc lập từ raw features.
Baseline SQLite vẫn giữ hash cũ. Presentation revision kết hợp parent SQLite +
preview manifest: `ed490fe068722f6b10ec1a545f87bafdfcdd27d5561283579a33188d8f24af80`.
Browser gate có thêm real R1 selection (C2025=622/526), stock peers/members, matrix
membership, saved diagnostics, mobile 390px và kiểm baseline vẫn mặc định.
Saved peer examples chỉ có các mã đã export, dùng đúng Euclidean recipe-space rule;
không gọi là cùng ngành. Không fit transform/model hoặc tính quality mới ở API/browser.

Các code/config có fingerprint được pin `eol=lf` trong `.gitattributes`;
sealed R1/preview artifacts giữ exact bytes. Không đổi bytes baseline/data đã seal
để làm sạch Git warnings. Local source snapshot/checks được ghi ở
`.tmp/upgrade-release-manifest.json` (chưa phải release commit/Dataset revision).

Runbook và lệnh tái kiểm ở [`web/README.md`](../web/README.md). Base commit là
`a03a7fe`; implementation hiện là working-tree changes, chưa có release commit.
Không coi sự tồn tại code/config hoặc preview local là public release PASS.


Local performance cuối (median ba mẫu; số bất lợi vẫn giữ):

| Trang | Primary usable ms, HEAD → upgrade | API requests | API encoded bytes |
|---|---:|---:|---:|
| Home | 493.4 → 310.9 | 2 → 2 | 169175 → 228446 |
| Stock FPT | 457.0 → 471.9 | 6 → 4 | 80768 → 77113 |
| Atlas C | 402.2 → 341.0 | 4 → 2 | 233331 → 228446 |
| Financial | 252.2 → 190.7 | 4 → 2 | 155832 → 38510 |

Cached tab 25.4ms; chart-handler + hai animation frames 10.1ms. Probe này không phải end-to-end tooltip benchmark. Raw samples ở `.tmp/upgrade-ui/performance.json`.
