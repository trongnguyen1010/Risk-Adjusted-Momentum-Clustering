# Báo cáo thực hiện backtest M3

**Ngày chốt báo cáo** 04/11/2026, giờ Việt Nam  
**Nhánh** `feature/indicators-v1`  
**Git HEAD** `42d3af869ac43c2f199e36916700b58c6959bcf1`  
**Revision dataset** `08c24867b11177072bfe457a4623a38abf9bbc48`

Báo cáo ghi kết quả thực tế đến ngày chốt. Kế hoạch và thứ tự các gate lấy từ [kế hoạch chuẩn M3](KE_HOACH_M3_SCHEMA_GITHUB.md), [ADR D-M3-01](DECISIONS.md) và [hướng dẫn readiness](M3_READINESS.md). Bằng chứng dưới `data/`, `artifacts/` và `.tmp/` được lưu local theo quy tắc Git ignore của dự án.

## 1. Trạng thái tổng thể

| Hạng mục | Trạng thái tại ngày chốt | Bằng chứng hoặc điều kiện còn lại |
|---|---|---|
| A. Môi trường Windows và Git | `PASS` | Python 3.12.7 trong venv M3 cô lập, `pip check` sạch, 35 test M3 ban đầu đạt. Lần đối chiếu GitHub ghi local và remote cùng HEAD, ahead/behind `0/0`. |
| B. Tải dữ liệu | `PASS` | Tải chọn lọc bốn file từ revision đã pin. Hash Indicators và manifest nguồn khớp. Manifest v4 xác nhận đúng SQLite đang có. |
| C. Tổ chức dữ liệu | `PASS` | Copy năm file vào các logical path. Tất cả file đích khớp SHA256 và nằm trong đường dẫn Git ignore. |
| D. Kiểm tra kỹ thuật đầu vào | `PASS` | Sáu runtime input khớp manifest. SQLite integrity, lịch execution, coverage VNINDEX và các kiểm tra C8 đã đạt. |
| D. Chấp nhận snapshot đầu vào tài chính | `PASS` theo quyết định owner ngày 04/11/2026 | B-PIT dùng nguyên Indicators v1 theo cách B v4. Các phát hiện VCG/SBT và giới hạn revision được lưu làm disclosure của dữ liệu đầu vào. |
| E. Build và audit B-PIT | Build hoàn tất, audit kỹ thuật `PASS` | Artifact `bpit-4a9d2e87f0de84ec` có 8.461 labels. Kiểm tra độc lập xác nhận hash, cutoff, roles và cluster order. Manifest ghi `code_dirty=true`. |
| Gate cutoff tại runtime | `PASS` | Phương án 2 đã triển khai và kiểm thử qua fixture runner targets-only, feasibility và kiểm tra đọc artifact thật tại ba snapshot. |
| Pin B-PIT | `PASS`, đã commit | Config đã pin artifact và SHA256 tại commit `8692d3f`. Loader runtime xác nhận `financial_source=B_PIT` và 8.461 labels. Status còn `READY_TO_LOCK_AFTER_BPIT`. |
| Feasibility với B-PIT | `PASS` | Đủ 60/24 snapshot, Combined có 13/60 tháng Development và 1/24 tháng Holdout dưới `N_min=10`. Số tháng thiếu ứng viên Development giữ mức tham khảo lịch sử. |
| Targets-only chính thức | Chưa thực hiện | Cần commit phần code M3 đã kiểm thử để manifest ghi `git_dirty=false` theo readiness, rồi chạy Development targets-only. |
| Config `LOCKED`, Development, Holdout, verify và seal | Chưa thực hiện | Chưa có run backtest Development/Holdout và chưa có NAV, ledger, metrics hay kết quả lợi suất M3. |

## 2. Phạm vi phương pháp đã khóa

- Market dùng A v4, `k=3`. Financial dùng B-PIT, cùng bộ chín chỉ số và công thức phân cụm của B v4. B-PIT fit tại cutoff theo FY và giữ cố định tâm cụm, preprocessing và thứ tự cụm. B v4 làm đối chiếu ARI.
- Combined dùng cụm dẫn dắt Market giao với các cụm Financial không yếu nhất sau các gate eligibility. Điểm Market và Financial có trọng số 50/50. `N_min=10` áp dụng cho Combined, Market-only và Financial-only. Quy tắc top 30% dùng tập mã còn đủ điều kiện theo từng strategy.
- Development có các decision snapshot từ `2019-01-31` đến `2023-12-29`. Holdout từ `2024-01-31` đến `2025-12-31`. Hai đoạn có danh mục và NAV riêng.
- Run chính dùng chi phí và trượt giá bằng 0. Strategy định giá theo `adj_close`. VNINDEX là price index, nên phần đối chứng cần ghi rõ khác biệt về return basis. Sharpe thuộc Final Evaluation.

Chi tiết và tham số nằm trong [config M3](../configs/experiments/m3_strategy_v1.json) và [kế hoạch chuẩn](KE_HOACH_M3_SCHEMA_GITHUB.md).

## 3. KẾT QUẢ THỰC HIỆN

### 3.1. Môi trường và dữ liệu

Venv `%LOCALAPPDATA%\DELTA\venvs\m3-py312` dùng Python **3.12.7**, SQLite **3.45.3**, NumPy **2.2.6** và scikit-learn **1.8.0**. Kết quả kiểm tra môi trường có `PIP_CHECK_EXIT=0`, `IMPORT_EXIT=0`, smoke ARI `1.0` và `M3_TEST_EXIT=0` với **35 test**. CLI Hugging Face `2.4.0` được cài ở venv tải riêng.

`hf download` tải vào `.tmp/m3-hf-staging/08c24867b11177072bfe457a4623a38abf9bbc48/`. Bốn file gồm Indicators SQLite, manifest Indicators, manifest v4 và manifest đầu vào M3. Tổng tải là **111.293.705 byte**. Ba file C8 và `terminal.sqlite` được tái dùng từ dữ liệu local. `availability.csv` và manifest kèm theo được copy từ evidence đã đối chiếu hash. [Manifest đầu vào từ staging](../.tmp/m3-hf-staging/08c24867b11177072bfe457a4623a38abf9bbc48/m3/experiments/inputs/manifest.json)

| Runtime input | Dung lượng (byte) | Đối chiếu |
|---|---:|---|
| `terminal.sqlite` v4 | 526.651.392 | SHA256 khớp, SQLite integrity đạt. Có 84 Market snapshots và 3.214.287 dòng giá. |
| Indicators v1 `indicators.sqlite` | 111.276.032 | SHA256 khớp pointer D-IND-01, SQLite integrity đạt. |
| `availability.csv` | 873.745 | SHA256 khớp, 13.620 dòng cho 1.362 mã. Có 0 dòng lệch quy tắc phiên quan sát kế tiếp. |
| C8 `benchmark_daily.jsonl` | 954.587 | SHA256 khớp, VNINDEX đủ ngày execution và ngày định giá cuối đoạn. |
| C8 `trading_calendar.jsonl` | 2.864.640 | SHA256 khớp, lịch hai segment đạt số kỳ dự kiến. |
| C8 `prices_daily.jsonl` | 4.193.211.376 | SHA256 khớp. Quét 81.103 dòng Development và 33.643 dòng Holdout tại các phiên execution, không thấy trùng ticker/ngày hay thiếu raw close, trần, sàn trong phạm vi quét. |

Lịch dự kiến đạt **60 quyết định, 59 lịch execution, 1 kỳ ngoài ranh giới** cho Development và **24, 23, 1** cho Holdout. Đây là kết quả kiểm tra lịch. Số giao dịch thực tế sẽ lấy từ ledger của từng run.

### 3.2. Q-date và các điểm cần xác minh về dữ liệu tài chính

Theo kế hoạch, mốc 30/06 năm sau là giả định của nhóm cho FY trước 2022. Loader M3 chính thức áp dụng `LAG_RULE` cho giai đoạn này và `CAFEF_DISCLOSURE` từ FY2022. Kiểm tra trên file thật xác nhận 267 dòng fallback từ FY2022 trở đi không còn cấp ngày usable cho M3 chính thức. Trong đó có 162 dòng FY2022–FY2024 và 105 dòng FY2025 đang chờ lịch. SHA256 của bảng availability nguồn vẫn khớp. Chế độ đối chứng lịch sử B v4 đọc dữ liệu theo đường cũ. Sau thay đổi, **36 test M3**, `compileall` và [synthetic smoke](../data/runs/run-20261104T025913Z-f4fd39a0/manifest.json) đều đạt. [Loader Q-date](../src/delta_t1/m3/inputs.py)

Lượt đối chiếu CafeF bao phủ **162 cặp mã–FY thuộc 119 mã**. Smoke 20 mã đạt trước khi mở rộng. Kiểm tra raw, receipt và SHA256 đã đạt trên ba lượt thu thập. Có **32 cặp** có bản ghi báo cáo năm loại `H` bị bộ lọc hiện hành bỏ qua, trong đó **9** tiêu đề ghi đã kiểm toán. Có **7** cặp có loại báo cáo năm khác cần xem riêng, **4** cặp chỉ có mốc nhập lại lịch sử `26/11/2022`, **37** cặp có bản ghi cùng FY nhưng thiếu bản ghi năm và **82** cặp thiếu bản ghi cùng FY trên endpoint được kiểm tra. Các bản ghi mới là evidence đối chiếu. [Kết quả audit Q-date](../data/financial/disclosure_dates_v1/m3-qdate-exceptions-20261104-remaining88-v1/qdate_audit.json)

Audit nguồn tài chính xác nhận hai vấn đề cụ thể. **VCG FY2023** có chín số đầu vào khớp báo cáo hợp nhất kiểm toán, nhưng Indicators thiếu lợi ích cổ đông không kiểm soát cuối năm và áp dụng cờ `NCI_ASSUMED_ZERO`. ROE lưu là **4,72%**. Phép đối chiếu với cùng công thức và số trong báo cáo cho **5,72%**. **SBT FY2024** ghép ngày CafeF của báo cáo riêng với dữ liệu khác số báo cáo hợp nhất kiểm toán. Doanh thu thuần trong Indicators là **29.995,18 tỷ đồng**. Báo cáo hợp nhất kiểm toán cho niên độ kết thúc `2025-06-30` ghi **28.482,17 tỷ đồng**. Nguồn chính xác của số Indicators ở SBT vẫn chưa được xác minh. Hai phát hiện này có phạm vi theo mã–FY đã đối chiếu. [Audit VCG và SBT](../data/financial/review/m3-revision-check-20261104-v1/audit.json)

Đã truy được code tính Indicators theo pin trong SQLite. Run nguồn `inputs-5b4836454b70d737` chưa tìm thấy ở checkout, các bản sao DELTA đã kiểm tra hoặc Hugging Face. Audit trên **9.661 cặp mã–FY đủ biến**, trong đó **8.087 cặp đạt điều kiện ngày fit**, ghi nhận 279 cặp chỉ có nhãn DStock, 310 cặp có ngày CafeF gắn báo cáo riêng `MK` và 2.513 cặp có cờ thiếu lợi ích cổ đông không kiểm soát cuối kỳ trong phép tính ROE. Các nhóm có thể giao nhau và là danh sách ưu tiên kiểm tra. [Audit truy vết upstream](../data/financial/review/m3-indicator-lineage-20261104-v1/audit.json)

### 3.3. Kết quả build B-PIT đã kiểm tra

Artifact [bpit-4a9d2e87f0de84ec](../data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec/manifest.json) được tạo ngày **04/11/2026 lúc 10:23:32 giờ Việt Nam** bằng builder `scripts/build_financial_pit_clusters.py`. Có đủ `labels.csv`, `models.json`, `audit.json` và `manifest.json`. Artifact ghi Git HEAD ở đầu báo cáo và `code_dirty=true` vì builder đã đọc phần thay đổi Q-date trong worktree. Năm hash file code và ba hash input trong manifest khớp file hiện có khi kiểm tra.

| FY | Cutoff | Fit | Gán cụm | ARI so với B v4 |
|---|---|---:|---:|---:|
| 2016 | `2017-07-03` | 135 | 0 | 1,0000 |
| 2017 | `2018-07-02` | 951 | 0 | 1,0000 |
| 2018 | `2019-07-01` | 947 | 0 | 1,0000 |
| 2019 | `2020-07-01` | 972 | 0 | 1,0000 |
| 2020 | `2021-07-01` | 977 | 0 | 1,0000 |
| 2021 | `2022-07-01` | 1.043 | 0 | 1,0000 |
| 2022 | `2023-04-30` | 1.048 | 98 | 0,9553 |
| 2023 | `2024-04-30` | 972 | 153 | 0,9369 |
| 2024 | `2025-04-30` | 1.042 | 123 | 0,8077 |
| 2025 | `2026-04-30` | Bỏ qua | Bỏ qua | Chưa có model, chỉ 3 báo cáo usable tại cutoff |

Kiểm tra độc lập xác nhận **8.461** khóa mã–FY duy nhất, gồm **8.087** `FIT`, **280** `ASSIGNED_AFTER_CUTOFF` và **94** `ASSIGNED_NO_DATE`. Chín model có đủ ba cụm và thứ tự cụm khớp giữa model và audit. Từng ngày usable trong labels khớp loader Q-date. Audit có `status=PASS`, `fit_leaks={}`. Ý nghĩa của PASS này là **tập fit tuân thủ cutoff theo ngày đã gắn trong input**. Việc xác minh ngày đó gắn đúng giá trị của đúng báo cáo là gate nguồn riêng. [Audit theo FY](../data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec/audit.json)

- `labels_sha256` `4a9d2e87f0de84ec9e80364b24043cb6091aa4f34f7dcfd187d8526e9f44579a`
- SHA256 của `manifest.json` `e61652e252ebf4008fd524b007092ddae348d259ae1581030ead18ae63c00322`

### 3.4. Gate cutoff tại runtime đã triển khai và kiểm thử

Ngày 04/11/2026, triển khai phương án 2 theo owner duyệt tạm thời. Runner và feasibility đọc cutoff từ
`models.json`. Combined và Financial-only chọn FY mới nhất theo ngày báo cáo usable, sau đó tạm loại mã nếu
chưa đến cutoff hoặc thiếu metadata model hợp lệ. Chọn FY mới nhất có xét cả các năm chưa có model, vì vậy
FY mới đã usable sẽ thay thế FY cũ theo Q10. Universe audit lưu `FINANCIAL_MODEL_BEFORE_CUTOFF` hoặc
`FINANCIAL_MODEL_NOT_READY`. [Implementation gate](../src/delta_t1/m3/universe.py)

Bộ **43 test M3 PASS**, gồm bảy regression tests mới cho gate và giữ đủ các assertion cũ. Test bao phủ trước,
đúng và sau cutoff, FY mới thiếu model, metadata rỗng, thứ tự cụm thiếu, cùng kiểm tra runner targets-only và
script feasibility trên fixture. Ba strategy Market-only, Equal-weight, Momentum-only và đường đối chứng B v4
được kiểm tra để bảo toàn behavior. `compileall`, Markdown links, kiểm tra diff và
[synthetic smoke](../data/runs/run-20261104T033429Z-d378831c/manifest.json) đạt. Môi trường Windows có cảnh báo
joblib khi dò số lõi vật lý, các test vẫn hoàn tất với exit code 0. [Regression tests](../tests/unit/test_m3_cutoff.py)

Kiểm tra đọc artifact `bpit-4a9d2e87f0de84ec` tại ba snapshot xác nhận mọi dòng `financial_eligible` có cutoff
không sau ngày quyết định. Tại `2024-03-29`, audit ghi 24 mã Combined và 178 mã Financial-only bị chặn trước
cutoff. Tại `2024-05-31`, cả hai strategy có 0 dòng bị chặn bởi gate model. Tại `2025-11-28`, Financial-only
ghi 1 dòng thiếu model của FY mới. Các số này là kiểm tra gate trên snapshot, chưa là lượt feasibility chính thức.

Self-review xác nhận gate dùng chung trong universe của feasibility và targets, cutoff đọc từ artifact,
và việc chọn FY mới nhất tuân theo ngày báo cáo thay vì chỉ duyệt các năm đã có labels. Config còn ở
`READY_TO_LOCK_AFTER_BPIT`, chưa pin B-PIT và chưa có run chính thức trong `data/experiments/m3/`.

### 3.5. Owner chấp nhận dùng snapshot Indicators v1 cho B-PIT

Ngày 04/11/2026, owner quyết định B-PIT dùng bộ Indicators v1 theo cùng cách B v4, gồm cả VCG FY2023 và SBT FY2024.
Các giá trị và công thức trong snapshot đã pin là đầu vào được chấp nhận. Audit nguồn ở Mục 3.2 tiếp tục được lưu
làm bằng chứng về chất lượng và giới hạn vintage/revision để disclosure khi báo cáo kết quả. Trạng thái audit
`MANUAL_REVIEW_REQUIRED` trong các evidence trước đó phản ánh kết luận tại thời điểm tạo evidence. Quyết định mới
được ghi ở [nhật ký owner decisions](DECISIONS.md) và Mục 5.2.B của [kế hoạch chuẩn](KE_HOACH_M3_SCHEMA_GITHUB.md).

Artifact `bpit-4a9d2e87f0de84ec` đã build từ đúng Indicators v1 được chấp nhận và audit kỹ thuật đã PASS.
Cutoff runtime đã kiểm thử PASS. Quy trình chuyển đến bước pin artifact và hash, sau đó feasibility.
Đánh giá PIT của kết quả sẽ nêu rõ bộ lọc ngày/cutoff đã áp dụng cùng giới hạn revision của snapshot đầu vào.

### 3.6. Pin artifact B-PIT vào config

Ngày 04/11/2026, pin hai trường `financial_pit.artifact` và `financial_pit.labels_sha256` trong
[config M3](../configs/experiments/m3_strategy_v1.json). Artifact là `data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec`,
hash labels là `4a9d2e87f0de84ec9e80364b24043cb6091aa4f34f7dcfd187d8526e9f44579a`.

Kiểm tra JSON và SHA256 xác nhận config khớp file labels và manifest của artifact, audit `PASS` và `fit_leaks`
rỗng. Gọi `run_m3.load_financial` xác nhận nguồn `B_PIT`, 8.461 labels và chín model có cutoff.
Self-review xác nhận phần config ngoài `financial_pit` khớp Git HEAD, status là `READY_TO_LOCK_AFTER_BPIT`.
SHA256 của config sau pin là `82dd3cc8e46862f7018bc661b01a19684d0548e326492daba557a0992497d6b4`.

Kết quả bước pin `PASS`. Owner đã commit config bằng `git add -- configs/experiments/m3_strategy_v1.json` và
`git commit -m "Pin verified B-PIT artifact for M3"`. Commit là `8692d3fe8d6b13bc7a89d2425118be6eabe54a89`,
gồm một file config, 4 dòng thêm và 1 dòng xóa. Hash config sau commit khớp giá trị đã ghi ở trên.
Các thay đổi code M3 trong worktree đang chờ commit. Tiếp theo thực hiện feasibility theo kế hoạch.

### 3.7. Feasibility với B-PIT

Owner đã chạy `scripts/m3_feasibility_variants.py` bằng venv M3 và gửi output với `FEASIBILITY_EXIT=0`.
Run là `20261104T034748Z`, nguồn `B_PIT:data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec`.
Kiểm tra độc lập đọc [variants.json](../data/experiments/m3/feasibility-variants/20261104T034748Z/variants.json)
xác nhận 84 ngày quyết định duy nhất, phân đoạn đúng config, và các số min/median/max cùng số tháng
`UNIVERSE_TOO_SMALL` khớp từng dòng monthly. Hash labels vẫn khớp config.

| Official config sau khi loại `FINANCIAL_CRITERIA_MISSING` | Development | Holdout |
|---|---:|---:|
| Số snapshot | 60 | 24 |
| Ứng viên tối thiểu | 3 | 4 |
| Trung vị số ứng viên | 27 | 30 |
| Ứng viên tối đa | 215 | 97 |
| Số tháng `UNIVERSE_TOO_SMALL` | 13 | 1 |
| Trung vị số mã được chọn trước gate `N_min` | 9 | 9,5 |

Development có 13/60 tháng dưới 10, cùng số tháng của mốc B v4 đã ghi trong readiness. Holdout có 1/24 tháng,
là snapshot `2025-04-29` với 4 ứng viên. Mốc lịch sử 13/60 và 0/24 đo trên B v4 trước khi loại thiếu FC, nên chỉ
dùng làm tham khảo. Kết quả hiện tại giữ nguyên config và qua cổng feasibility trong kế hoạch. Các phương án
V0/Vb/Vab trong output là số đếm đối chiếu, strategy chính thức tiếp tục dùng rule Va đã khóa.

SHA256 `variants.json` là `0feff8103c6a4d794cb9cc2ef41ccf88a798e685d788f92e95d36d27c92899a2`.
Git HEAD khi xác minh là `8692d3fe8d6b13bc7a89d2425118be6eabe54a89`. Code M3 trong worktree có thay đổi đã kiểm thử
đang chờ commit. Kết quả feasibility chỉ đếm ứng viên. Bước tiếp theo là commit code để đạt điều kiện
`git_dirty=false` của readiness, rồi chạy targets-only Development.

## 4. Công việc còn lại và gate chuyển bước

| Thứ tự | Công việc | Điều kiện hoàn tất |
|---:|---|---|
| 1 | Chấp nhận snapshot đầu vào đã `PASS` theo owner | Xem quyết định ở Mục 3.5. Dùng Indicators v1 đã pin và disclosure các giới hạn ghi tại Mục 3.2. |
| 2 | Gate cutoff tại runtime đã `PASS` | Xem kết quả thực hiện ở Mục 3.4. Dùng implementation này cho feasibility và targets-only chính thức sau khi các gate đầu vào đạt. |
| 3 | Pin B-PIT và feasibility đã `PASS` | Xem Mục 3.6 và 3.7. Giữ `N_min=10` và rule Va theo config đã khóa về methodology. |
| 4 | Chạy targets-only riêng hai segment | Xác minh B-PIT hash, `financial_source`, lịch `60/59/1` và `24/23/1`, target weights và số dòng universe audit. |
| 5 | Kiểm tra strict isolation và khóa config | Xác minh Q17 ở biên đoạn vì `PriceBook` có thể nạp phiên lân cận. Chốt code, input, config SHA256 và trạng thái `LOCKED` sau khi các gate trước đạt. |
| 6 | Development → verify → seal | Kiểm tra ledger, holdings, turnover, NAV, VNINDEX và metrics. Ngày NAV cuối dự kiến `2023-12-29`. Lưu run ID, manifest và hash đầu ra. |
| 7 | Holdout → verify → seal | Chạy sau khi Development seal, dùng cùng danh tính code, config và input. Ngày NAV cuối dự kiến `2025-12-31`. Xác minh và lưu bộ output riêng. |
| 8 | Đối chứng, đánh giá và tái lập | So sánh Combined với bốn strategy đối chứng và VNINDEX theo từng đoạn. Báo số kỳ thiếu ứng viên và giới hạn dữ liệu. Chuẩn bị artifact sealed cho M3-B và notebook M3-C. |

Mỗi lần cập nhật báo cáo sau run chính thức cần ghi segment, run ID, Git commit, `config_sha256`, revision dataset, SHA256 đầu vào và đầu ra, kết quả verify cùng đường dẫn artifact đã seal. Khi có đủ hai run verified, bổ sung bảng hiệu quả theo từng segment từ `metrics.json` và đối chiếu với NAV, benchmark và ledger. Final Evaluation có gate riêng trong kế hoạch chuẩn.
