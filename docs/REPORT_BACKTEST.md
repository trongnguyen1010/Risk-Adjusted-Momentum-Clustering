# Báo cáo thực hiện backtest M3

**Ngày chốt báo cáo** 04/11/2026, giờ Việt Nam  
**Nhánh** `feature/indicators-v1`  
**Git HEAD ban đầu** `42d3af869ac43c2f199e36916700b58c6959bcf1`<br>
**Commit backtest chính thức** `a5d9872b598bd9878238849835f41beedeb5826f`<br>
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
| Targets-only Development | `PASS` | Run `20261104T041728Z-9c4abba3`, đủ 60/59/1 cho cả năm strategy, source/hash đúng và `git_dirty=false`. Targets khớp universe audit tại mọi kỳ. |
| Targets-only Holdout | `PASS` | Run `20261104T042556Z-9c4abba3`, đủ 24/23/1 cho cả năm strategy. Code, config, hash đầu vào và B-PIT khớp Development; targets khớp universe audit tại mọi kỳ. |
| Strict isolation Q17 và config `LOCKED` | `PASS`, đã commit | Commit `a5d9872`, code/config sạch theo phạm vi runner. Phạm vi giá thật hai đoạn đạt, 49 test M3/compile/synthetic smoke PASS. SHA256 config ghi tại Mục 3.11. |
| Official Development → verify → seal | Run nguồn đã seal. Portfolio accounting `PASS`, cần đồng bộ metadata Q17 | Run `20261104T060408Z-5557288c`. Rà soát Mục 3.20 xác nhận NAV năm strategy khớp, phát hiện count repair 36 cần sửa thành 34. |
| Rà soát trước Holdout | `PARTIAL`, chờ commit và run Development mới | Đã sửa Q17 kiểm tra đúng phiên liền kề. 52 test M3, compile, synthetic smoke PASS. |
| Official Holdout → verify → seal | Chưa thực hiện | Chờ commit bản sửa và verify/seal Development đồng bộ version code theo Mục 3.20. |

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

### 3.8. Checkpoint code trước targets-only

Owner đã commit 14 file M3 bằng thông điệp `Apply M3 Q-date and B-PIT runtime cutoff gates`.
Commit là `e734c5df2042a573324fa408c9dba8d354d7c6dc`, gồm 499 dòng thêm và 23 dòng xóa.
Kiểm tra `git status --porcelain -- src scripts configs` trả về trống. Hash labels khớp config,
status giữ `READY_TO_LOCK_AFTER_BPIT`. Worktree còn `.venv-vci/` untracked, nằm ngoài phạm vi `git_dirty` của runner.
Kết quả checkpoint `PASS`, đủ điều kiện bắt đầu targets-only Development theo readiness.

### 3.9. Targets-only Development

Owner đã chạy `scripts/run_m3.py --segment development --targets-only`, kết thúc với `TARGETS_DEV_EXIT=0`.
Run [20261104T041728Z-9c4abba3](../data/experiments/m3/development/20261104T041728Z-9c4abba3/manifest.json) ghi
Git commit `38948f8e4f15c2c9727ac4da59e2f422ebeda58e`, `git_dirty=false`, `targets_only=true` và
`financial_source=B_PIT`. Kiểm tra code và config hiện có so với commit trong manifest trả về diff trống.
Config hash và sáu hash input được ghi trong manifest khớp file trên máy. `c8_prices_sha256=null` đúng behavior
của targets-only đã mô tả trong kế hoạch. Hash file C8 đầy đủ đã kiểm tra ở bước input readiness.

| Strategy | Decision snapshots | Lịch execution | `UNIVERSE_TOO_SMALL` | Quyết định ngoài biên execution | Dòng targets |
|---|---:|---:|---:|---:|---:|
| Combined | 60 | 59 | 13 | 1 | 787 |
| Market-only | 60 | 59 | 0 | 1 | 1.595 |
| Financial-only | 60 | 59 | 0 | 1 | 4.012 |
| Equal-weight | 60 | 59 | 0 | 1 | 25.647 |
| Momentum-only | 60 | 59 | 0 | 1 | 7.722 |

Mỗi strategy có 45.646 dòng universe audit, một dòng cho từng mã trong Market snapshot. Đã đối chiếu tại đủ
60 kỳ, số dòng `in_candidate_universe=True` khớp `candidates` trong targets. Các mã được chọn thuộc tập ứng viên,
khóa mã/ngày duy nhất, rank liên tục, trọng số bằng nhau và tổng trọng số là 1 khi có picks. Số mã được chọn khớp
rule của từng strategy. Kỳ `UNIVERSE_TOO_SMALL` lưu dòng trạng thái với target trống.

Mọi execution date khớp phiên HOSE mở kế tiếp. Quyết định cuối `2023-12-29` có
`NOT_EXECUTED_SEGMENT_END` cho cả năm strategy. Các dòng Financial đủ điều kiện dùng đúng FY mới nhất đã usable
và có cutoff không sau ngày quyết định. Tập lý do loại khớp contract, gồm 419 dòng Combined và 847 dòng
Financial-only ghi `FINANCIAL_MODEL_BEFORE_CUTOFF`. Không có mã lý do lạ trong audit.

Kết quả verify `PASS`. Run có đủ 11 file targets-only theo contract. SHA256 manifest là
`b5b80bea9b29d56f5f64fb383c8cef924cb0e6a9beed1786e5053b3d90387350`.
Next action là targets-only Holdout, sau đó đối chiếu hai run trước khi khóa config theo readiness.

### 3.10. Targets-only Holdout và đối chiếu hai đoạn

Owner đã chạy `scripts/run_m3.py --segment holdout --targets-only`, kết thúc với `TARGETS_HOLDOUT_EXIT=0`.
Run [20261104T042556Z-9c4abba3](../data/experiments/m3/holdout/20261104T042556Z-9c4abba3/manifest.json) ghi
`targets_only=true`, `financial_source=B_PIT`, `git_dirty=false`, start `2024-01-31` và end `2025-12-31`.
Git commit, config SHA256, toàn bộ hash đầu vào và nguồn tài chính khớp run Development tại Mục 3.9.
Kiểm tra lại file trên máy xác nhận sáu hash input và hash config đều khớp manifest. Code/config hiện có
không có diff so với commit trong manifest. `c8_prices_sha256=null` đúng contract targets-only.

| Strategy | Decision snapshots | Lịch execution | `UNIVERSE_TOO_SMALL` | Quyết định ngoài biên execution | Dòng targets |
|---|---:|---:|---:|---:|---:|
| Combined | 24 | 23 | 1 | 1 | 259 |
| Market-only | 24 | 23 | 0 | 1 | 828 |
| Financial-only | 24 | 23 | 0 | 1 | 1.706 |
| Equal-weight | 24 | 23 | 0 | 1 | 18.087 |
| Momentum-only | 24 | 23 | 0 | 1 | 5.439 |

Mỗi strategy có 30.155 dòng universe audit, đúng một dòng cho từng mã/ngày trong Market snapshot.
Ở đủ 24 kỳ, số ứng viên khớp audit, picks thuộc tập ứng viên, không trùng mã, rank liên tục,
số mã chọn đúng rule và trọng số bằng nhau có tổng bằng 1 khi có picks. Các dòng Financial đủ điều kiện
dùng FY mới nhất đã usable, có model cutoff không sau ngày quyết định và thuộc cụm được phép.
Tập lý do loại khớp contract; các dòng `FINANCIAL_MODEL_BEFORE_CUTOFF` và `FINANCIAL_MODEL_NOT_READY`
được giữ trong audit theo gate runtime đã duyệt.

Combined có một kỳ `UNIVERSE_TOO_SMALL` tại `2025-04-29`, với 4 ứng viên và target trống, khớp feasibility.
Execution date khớp phiên HOSE mở kế tiếp. Quyết định cuối `2025-12-31` được ghi
`NOT_EXECUTED_SEGMENT_END` ở cả năm strategy. Đây là lịch execution dự kiến, chưa phải giao dịch thực tế.

Kết quả verify `PASS`; đủ 11 file theo contract targets-only. SHA256 manifest là
`402112a47154bf64773e809408fc0f884517cc209ada7be22ab89d072c60d10a`.
Self-review xác nhận cả hai run targets-only đã đạt Bước 4 của readiness, giữ nguyên rule và không tạo
NAV, ledger hoặc metrics lợi suất. Bước tiếp theo là kiểm tra strict isolation Q17 và khóa config;
chưa thực hiện bước này trong lần xác minh Holdout.

### 3.11. Strict isolation Q17 và khóa config

Owner yêu cầu thực hiện bước kiểm tra ranh giới giá và khóa config sau khi targets-only hai đoạn PASS.
Kiểm tra code phát hiện `PriceBook` nạp thêm phiên lân cận của execution/valuation date để phục vụ Q17,
nhưng chưa giới hạn theo segment. Trên lịch thật, logic cũ nạp thêm `2024-01-02` cho Development kết thúc
`2023-12-29`. Đây là lỗi implementation so với strict isolation tại Mục 3.9 của kế hoạch.

Đã truyền `segment_start`/`segment_end` từ runner vào `PriceBook`, lọc lịch trước khi query SQLite và từ chối
execution/valuation date nằm ngoài đoạn. Q17 tiếp tục sửa glitch trong đoạn theo detector đã khóa. Nếu phiên
biên thiếu lân cận trong đoạn thì giữ giá nguồn, không dùng phiên ngoài đoạn để repair. Kết nối SQLite đóng
sau khi đọc. Source artifacts và các run targets-only đã có được giữ nguyên.

Kiểm tra đọc giá thật, không chạy portfolio engine hoặc tính lợi suất, cho kết quả:

| Segment | Phiên execution/valuation yêu cầu | Phiên giá đã nạp, gồm lân cận | Dòng giá | Phiên giá đầu | Phiên giá cuối |
|---|---:|---:|---:|---|---|
| Development | 60 | 179 | 246.132 | `2019-01-31` | `2023-12-29` |
| Holdout | 24 | 71 | 103.730 | `2024-01-31` | `2025-12-31` |

Không có ngày ngoài đoạn trong giá/volume đã nạp hoặc Q17 flags. Bộ 43 test M3 ban đầu PASS trước sửa;
sau sửa, 49 test M3 PASS, gồm sáu regression test mới về biên cuối, biên đầu, future append ngoài đoạn,
repair trong đoạn, source immutability, date ngoài đoạn và wiring qua runner fixture. `compileall` PASS.
[Synthetic smoke](../data/runs/run-20261104T043141Z-55c26888/manifest.json) có `status=complete`, `synthetic=true`,
exit 0. Test runner dùng dữ liệu giả trong thư mục tạm; không phải official Development/Holdout.

Config chuyển `READY_TO_LOCK_AFTER_BPIT` sang `LOCKED`. So với config đã chạy targets-only, chỉ thay `status`
và `status_note`; artifact B-PIT, labels hash, rule Va, `N_min`, trọng số, chi phí và segments giữ nguyên.
SHA256 của file config `LOCKED` là `b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d`.
Các hash input đã xác minh ở Mục 3.9–3.10 tiếp tục là danh tính đầu vào; không tạo bản dữ liệu mới.
Hash config mới khác hai manifest targets-only vì đã chuyển trạng thái, không phải thay strategy rule.

Self-review xác nhận bản sửa thực thi ranh giới đã duyệt, không đổi methodology, không dùng kết quả lợi suất
để chọn rule và không sửa immutable artifacts. Gate kỹ thuật `PASS`. Git HEAD trước commit vẫn là
`38948f8e4f15c2c9727ac4da59e2f422ebeda58e`; code/config đang có thay đổi nên chưa đạt `git_dirty=false`.
Next action là owner commit các file của bước này, kiểm tra hash config và worktree sạch theo phạm vi runner.
Sau checkpoint commit mới chuyển sang official Development → verify → seal. Chưa chạy stage đó trong phiên này.

### 3.12. Checkpoint commit config LOCKED

Owner đã commit chín file bằng thông điệp `Lock M3 config and enforce segment price isolation`.
Commit là `a5d9872b598bd9878238849835f41beedeb5826f`, gồm 289 dòng thêm và 16 dòng xóa.
Kiểm tra `git status --porcelain -- src scripts configs` trả về trống, đạt `git_dirty=false` theo runner.
Worktree chỉ còn `.venv-vci/` untracked tại thời điểm kiểm tra, ngoài phạm vi này.

Config có `status=LOCKED`, SHA256 vẫn là
`b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d`.
Hash `labels.csv` khớp pin B-PIT và artifact audit có `status=PASS`. Self-review xác nhận commit chứa đúng
code, test, config và tài liệu của bước strict isolation, không đổi input hoặc rule sau targets-only.
Checkpoint `PASS`. Bước tiếp theo là owner chạy official Development bằng venv M3; chưa chạy lệnh đó trong
lần xác minh này. Sau run phải verify/seal trước khi chuyển sang Holdout bằng cùng frozen code/config/input.

### 3.13. Official Development — verify và seal

Owner đã chạy `scripts/run_m3.py --segment development`, kết thúc với `BACKTEST_DEV_EXIT=0`.
Run [20261104T060408Z-5557288c](../data/experiments/m3/development/20261104T060408Z-5557288c/manifest.json)
ghi `targets_only=false`, `status=LOCKED`, `financial_source=B_PIT`, `git_dirty=false` và commit
`a5d9872b598bd9878238849835f41beedeb5826f`. Config SHA256 là
`b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d`.
Đã đọc và xác minh lại cả bảy hash input, gồm file C8 đầy đủ. Targets và universe audit của năm strategy
khớp byte với run targets-only Development đã PASS tại Mục 3.9.

Lịch giữ nguyên 60 decisions, 59 kỳ có execution trong đoạn và một decision cuối không execution.
Combined có 13 kỳ `UNIVERSE_TOO_SMALL`; bốn strategy đối chứng không có kỳ dưới ngưỡng áp dụng.
Mỗi chuỗi NAV có 60 điểm, bắt đầu `2019-02-01` tại 1, kết thúc `2023-12-29`, tương ứng 59 khoảng return.
Ngày `2023-12-29` chỉ định giá cuối đoạn, không có ledger, turnover hoặc holdings rebalance mới.
Không có execution/valuation sau biên đoạn. Q17 có 36 repair trong tập phiên giá runtime đã nạp.

Xác minh độc lập dùng ledger và giá runtime để dựng lại danh mục từ 100% cash, không gọi lại portfolio engine.
Đã đối chiếu pre-weight, target, intended/executed value, cash conservation, SELL trước BUY, failed orders,
scaling, holdings và NAV cho từng kỳ. Rule `UNIVERSE_TOO_SMALL` chỉ giữ các mã còn trong tập ứng viên,
không tạo BUY mới. Trần/sàn được đối chiếu trực tiếp từ C8 trong cùng lượt xác minh hash file giá.
Turnover tái tính bằng tổng executed BUY/SELL chia `2 × pre_trade_NAV` khớp output.
Benchmark tái tính từ VNINDEX close tại cùng ngày định giá; metrics tái tính độc lập khớp `metrics.json`
với tolerance `rel_tol=1e-9`, `abs_tol=1e-10`. Không có Sharpe trong kết quả Development.

#### Kết quả Development

| Strategy / benchmark | Tổng lợi suất | CAGR | Biến động năm | Max drawdown | Turnover trung bình mỗi kỳ | Cash trung bình sau giao dịch |
|---|---:|---:|---:|---:|---:|---:|
| Combined | 116,15% | 16,97% | 27,39% | -44,60% | 47,62% | 22,40% |
| Market-only | 128,81% | 18,34% | 29,51% | -47,88% | 53,99% | 6,22% |
| Financial-only | 40,74% | 7,20% | 17,09% | -27,20% | 17,69% | 1,02% |
| Equal-weight | 159,03% | 21,36% | 24,45% | -37,01% | 11,89% | 0,48% |
| Momentum-only | 169,73% | 22,36% | 25,51% | -33,71% | 31,54% | 1,47% |
| VNINDEX | 24,35% | 4,53% | 23,56% | -33,02% | — | — |

Các số trên lấy từ [metrics.json](../data/experiments/m3/development/20261104T060408Z-5557288c/metrics.json)
đã xác minh, làm tròn hai chữ số. CAGR và volatility dùng 59 kỳ return với quy đổi 12 kỳ/năm;
drawdown đo trên các điểm NAV được lưu theo lịch execution/valuation, không phải daily drawdown.
Chi phí và slippage bằng 0. Strategy dùng vendor-adjusted close, VNINDEX là price index;
khác biệt basis và giới hạn dữ liệu tài chính tại Mục 3.2 vẫn phải công bố khi diễn giải kết quả.

| Strategy | BUY_FAILED | SELL_FAILED | SCALED | Số sự kiện `PRICE_STALE` | `limit_data_missing` |
|---|---:|---:|---:|---:|---:|
| Combined | 47 | 33 | 263 | 2 | 0 |
| Market-only | 96 | 62 | 537 | 3 | 0 |
| Financial-only | 267 | 280 | 1.301 | 9 | 0 |
| Equal-weight | 1.836 | 2.027 | 11.115 | 111 | 0 |
| Momentum-only | 661 | 739 | 2.735 | 26 | 0 |

`PRICE_STALE` đếm theo cặp mã/ngày định giá của từng strategy, không phải số mã duy nhất. Các sự kiện này
giữ last valid mark theo contract, không suy thành delisting và không tạo observation giá giả.
Failed orders và scaling được giữ đầy đủ trong ledger; không xóa evidence vì kết quả bất lợi.
Combined có lợi suất thấp hơn Market-only, Equal-weight và Momentum-only trong Development này;
không thay rule hoặc config dựa trên kết quả đó trước Holdout.

#### Bằng chứng seal

Đủ 33 file: manifest, metrics, benchmark và sáu nhóm CSV cho mỗi strategy. Đã so hash trước/sau verify,
xác nhận không file nào trong run bị sửa. [Seal Development](../data/experiments/m3/seals/development/20261104T060408Z-5557288c/seal.json)
ghi `status=PASS`, hash của đủ 33 file, code/config/input identities, kết quả kiểm tra và danh sách sự kiện stale.
Seal được ghi riêng ngoài run; giữ nguyên manifest/output gốc.

- SHA256 manifest: `4a0be20861afc48130f206c4ea5828b3e82ea30a0fa7945a76a41b01ae4b5bd8`.
- SHA256 seal: `14953959cdc91956ee0dbf9fee88bf71b81064011b98c51526429efb8a3fd1d8`.
- [Verifier local](../.tmp/verify_m3_development_20261104.py) chỉ đọc run và inputs, đối chiếu accounting,
  tạo seal mới bằng chế độ từ chối ghi đè; không fit model hoặc rerun official backtest.

Self-review xác nhận gate Development verify/seal `PASS`, không đổi code/config/input và không sửa
`M3_READINESS.md`. Bước tiếp theo là owner chạy official Holdout bằng cùng commit/config/input,
sau đó verify/seal riêng. Chưa chạy official Holdout trong phiên này.

### 3.14. CSV backtest v2 diễn giải bốn bước của Combined Development

**Bản xem hiện hành** là bản `plan-columns` với 22 cột tại Mục 3.19.
[CSV v2 theo bố cục đã chốt](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/plan-columns/BACKTEST_DEV_COMBINED_V2.csv)

Theo yêu cầu owner, đã xuất [BACKTEST_DEV_COMBINED_V2.csv](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/BACKTEST_DEV_COMBINED_V2.csv)
để xem kết quả từng bước theo 60 decision snapshots của run Development đã seal tại Mục 3.13.
Đây là phiên bản báo cáo v2; strategy, config, code của official run và 33 file canonical giữ nguyên.
Không chạy lại mô hình hoặc portfolio engine. `M3_READINESS.md` không thay đổi.

File có 5.656 dòng dữ liệu, 40 cột, UTF-8 BOM và delimiter dấu phẩy. Các cột ngày dùng `yyyy-mm-dd`;
NAV và giá trị giao dịch quy đổi theo vốn đầu 100. Cột có hậu tố `(%)` ghi theo điểm phần trăm:
`5.26` nghĩa là 5,26%, không phải tỷ lệ 0,0526. Giữ đầy đủ precision trong CSV.

| Loại dòng | Số dòng | Nội dung |
|---|---:|---|
| `TỔNG HỢP` | 240 | 60 kỳ × 4 bước, gồm cả kỳ cuối bị chặn execution. |
| `ỨNG VIÊN` | 2.584 | Tập ứng viên Bước 1; đánh dấu được chọn, rank, tỷ trọng mục tiêu từng mã và FY/cụm. |
| `GIAO DỊCH` | 1.228 | Lệnh Bước 2: BUY/SELL/HOLD, target, goal thực thi, pre-weight, executed value, scaling và trạng thái. |
| `DANH MỤC` | 802 | Tỷ trọng từng mã và CASH thực tế sau giao dịch Bước 2; 743 dòng cổ phiếu, 59 dòng CASH. |
| `ĐỊNH GIÁ` | 802 | Bước 3: tỷ trọng đầu/cuối giữ, mark giá, lợi suất định giá từng mã, đóng góp NAV và PRICE_STALE. |

Các bước được sắp theo từng kỳ:

1. Chọn cổ phiếu tại decision date: số ứng viên, số mã mục tiêu, mã được chọn và tỷ trọng mục tiêu.
2. Mua/bán tại execution date: lệnh thực tế, tỷ trọng trước/sau giao dịch, số mã thực giữ, CASH và turnover.
3. Giữ đến execution kế tiếp hoặc end_date: NAV đầu/cuối, lợi suất kỳ, lợi suất lũy kế và chi tiết từng mã.
4. Chuyển trạng thái trước giao dịch sang kỳ sau; không thực hiện thêm một lần rebalance trong dòng này.

**Cách đọc:** lọc `Loại dòng=TỔNG HỢP` để xem luồng bốn bước. Lọc `Loại dòng=DANH MỤC` và cột `Kỳ`
để xem từng mã thực giữ, hoặc `Loại dòng=GIAO DỊCH` để hiểu lệnh thất bại. Dùng dòng tổng hợp Bước 3
cho lợi suất từng khoảng giữ; không cộng các dòng tổng hợp Bước 3 và Bước 4 vì Bước 4 nhắc lại state chuyển kỳ.
Cột `Tỷ trọng mục tiêu (%)` khác `Tỷ trọng goal thực thi (%)`: ở kỳ thiếu ứng viên, target mua mới trống
nhưng goal của engine có thể giữ vị thế cũ. Ô trống là không áp dụng/không có giá trị tương ứng, không thay bằng 0.

Kỳ 60 (`2023-12-29`) có 80 ứng viên và 24 mã trong target được lưu, nhưng execution `2024-01-02`
nằm ngoài đoạn. File ghi rõ `NOT_EXECUTED_SEGMENT_END`, không sinh dòng giao dịch/danh mục/định giá mới
cho kỳ đó. NAV cuối 216,15233667541727 được tính ở Bước 3 kỳ 59, rồi nhắc lại khi chốt đoạn.

Đã kiểm tra read-back CSV, 240 khóa kỳ/bước, counts từng kỳ, đủ chi tiết lệnh/holdings,
tổng tỷ trọng 100%, đóng góp từng mã cộng lại khớp biến động NAV, và giá trị cuối khớp run sealed.
Preview và inspect xác nhận nhãn tiếng Việt và ngày/số đọc được. Kiểm tra hash nguồn trước/sau đều khớp seal.
Self-review kết luận báo cáo v2 `PASS`; không mở Holdout hoặc thay đổi methodology.

[Manifest báo cáo v2](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/manifest_v2.json)
ghi nguồn run/seal, hash CSV và hash hai helper local tại `.tmp/m3-backtest-v2/`.
SHA256 CSV: `3978b6500f962b0b2f42d986707bbda03657984382fdafe21c3cc9d61f1a9698`.

### 3.15. Chuẩn hóa tên cột CSV v2 theo kế hoạch

Owner yêu cầu dùng tên cột giống kế hoạch. Đã tạo [CSV v2 bản 35 cột](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/plan-columns/original-35-columns/BACKTEST_DEV_COMBINED_V2.csv),
giữ nguyên 5.656 dòng/60 kỳ, còn 35 cột. File trước được giữ để đối chiếu, không ghi đè artifact sealed.

Tên dữ liệu nghiệp vụ dùng các biến/thuật ngữ tại Mục 3.6.2, 7, 8.3, 16 và 17.4 của kế hoạch:
`decision_date`, `execution_date`, `date`, `candidates`, `N_selected`, `ticker`, `rank`, `target_weight`,
`goal[ticker]`, `pre_weight`, `weight`, `pre-rebalance-weight`, `pre_trade_NAV`, `nav`, `side`,
`intended`, `executed`, `scale`, `turnover`, `financial_year`, `market_cluster`, `financial_cluster`,
`period return`, `Total/Cumulative Return`, `Cash ratio`, `security return`, `contribution`.
`status (targets)` và `status (ledger)` là hai cột cùng biến `status`, thêm nhãn nguồn để không lẫn trạng thái.
`goal[ticker]` biểu diễn một phần tử của dict `goal`; không gán goal giữ vị thế cũ thành target mua mới.

Đã bỏ `Giá mark đầu`, `Giá cuối quan sát`, `Giá mark cuối`, cùng hai cột trùng thông tin `Tên bước`
và `Được chọn`. Hạng khác trống xác định mã được chọn ở Bước 1. Các cột `Kỳ`, `Bước`, `Loại dòng`,
`Kỳ tiếp theo`, `Ghi chú` chỉ phục vụ theo dõi báo cáo. `Số mã thực giữ` là số cổ phiếu đếm từ holdings
theo yêu cầu owner, không tính CASH; không đổi nhãn này thành `N_selected` vì hai số có thể khác nhau.

Đơn vị cũng được đưa về kế hoạch: `target_weight`, `pre_weight`, `weight`, các return và turnover dùng
tỷ lệ 0–1 (`0.05 = 5%`). `nav`, `pre_trade_NAV`, `intended`, `executed` và `contribution` dùng value space
của nguồn, vốn đầu bằng 1. Ví dụ NAV cuối là `2.1615233667541727`, tương đương 216,15233667541727
trong bản gốc 100. Chỉ chuyển đơn vị, không đổi kết quả kinh tế.

[Manifest bản 35 cột](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/plan-columns/original-35-columns/manifest_v2.json)
ghi mapping tên cũ/mới, hệ số đổi đơn vị, mục tương ứng trong kế hoạch và hash nguồn.
SHA256 CSV bản 35 cột là `1f5df8499ba7aa9c6e074d2566f719891e6402c5ea8cfad282b8474ab674b3ac`.
Đã kiểm tra mapping toàn bộ ô được giữ, read-back CSV, tổng tỷ trọng, số dòng và NAV; inspect/render đạt.
Self-review `PASS`: 33 file run gốc, seal, code/config và `M3_READINESS.md` giữ nguyên. Chưa mở Holdout.

### 3.16. CSV v2 tổng hợp cuối bước và phân biệt mã cũ/ứng viên mới

Theo yêu cầu owner, đã xuất [CSV v2 bố cục hiện hành](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/readable-layout/BACKTEST_DEV_COMBINED_V2.csv).
Cả 240 dòng `TỔNG HỢP` nằm cuối từng nhóm `Kỳ/Bước`, sau các dòng chi tiết. Bước không có chi tiết
chỉ giữ một dòng tổng hợp, gồm các bước bị chặn execution ở kỳ 60.

Đã thay cột `ticker` bằng hai cột theo yêu cầu hiển thị:

- `ticker (kỳ trước)`: mã thực giữ sau execution kỳ trước; kỳ 1 chưa có cổ phiếu cũ.
- `ticker (ứng viên kỳ này)`: mã thuộc Candidate Universe tại decision date kỳ hiện tại.

Hai ô cùng một dòng luôn chỉ cùng một tài sản. Có cả hai ô nghĩa là mã cũ vẫn thuộc tập ứng viên mới.
Mã cũ bị loại chỉ có ô bên trái, ứng viên chưa từng giữ chỉ có ô bên phải. Bước 1 được bổ sung 413 dòng
`KỲ TRƯỚC` trên toàn đoạn để hiển thị các mã cũ đã rời tập ứng viên; không đưa chúng vào số `candidates`.
CASH được nhận diện ở cột tài sản kỳ trước vì được carry trong Portfolio, không tính là ứng viên/cổ phiếu.

Ví dụ Bước 1 kỳ 3: CMX ở cả hai cột; 19 mã cũ khác chỉ ở cột kỳ trước; LAF/PSE/SRA chỉ ở cột ứng viên
kỳ này. Số ứng viên vẫn là 4 và `N_selected=0` do `UNIVERSE_TOO_SMALL`.

Giữ riêng `goal[ticker]` và `weight`: goal là tỷ trọng engine muốn đạt, weight là tỷ trọng sau xử lý lệnh.
Trong 743 dòng cổ phiếu thực giữ, 441 dòng có hai tỷ trọng bằng nhau trong tolerance `1e-10`,
302 dòng khác nhau. Bổ sung giải thích ở `Ghi chú` của từng dòng danh mục dựa trên ledger:
HOLD/đạt goal, SELL_FAILED còn giữ vị thế, hoặc SCALED mua bị giảm tỷ lệ.
Kỳ 6: WCS có goal 0 nhưng weight 0,1912395474 do SELL_FAILED; NDN/TIP/TRC có goal 0,2 nhưng weight
0,1362534842 do SCALED. Không coi hai cột là thông tin trùng và không đổi tỷ trọng nguồn.

File có 6.069 dòng, 36 cột; tăng từ bản trước do các dòng mã cũ và cột ticker được tách đôi.
Các giá trị nghiệp vụ/đơn vị giữ nguyên Mục 3.15. Đã kiểm tra toàn bộ 5.656 dòng gốc sau khi thay ticker
bằng hai cột, chỉ bổ sung ghi chú ở các dòng danh mục. Kiểm tra 240 summary nằm cuối bước, membership
cả hai cột theo từng kỳ, đủ union mã cũ/ứng viên Bước 1, source seal và 33 hash run gốc đều PASS.
Inspect/render đạt. Self-review xác nhận đây là chỉnh bố cục báo cáo, không đổi backtest hoặc mở Holdout;
`M3_READINESS.md` và code/config official giữ nguyên.

[Manifest bản bố cục hiện hành](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/readable-layout/manifest_v2.json)
ghi nguồn, đơn vị, quy tắc hai cột ticker, counts và hash CSV.
SHA256 CSV hiện hành là `5836fc22a389eb55120dec6362eb656f3d6c4250e1525da0f653fb2a8db73d41`.

### 3.17. CSV v2 đầy đủ biến bốn bước và dữ liệu giải thích failed orders

Owner yêu cầu mọi biến trong bảng bốn bước có cột, gồm dữ liệu như volume để tự nhận biết nguyên nhân
mua/bán thất bại. Đã xuất [CSV v2 đầy đủ biến](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/full-variables/BACKTEST_DEV_COMBINED_V2.csv)
cho Combined Development: 6.069 dòng, 97 cột, đủ 60 kỳ và 240 dòng tổng hợp ở cuối bước.
Giữ hai cột ticker kỳ trước/ứng viên kỳ này và các đơn vị tỷ lệ 0–1, vốn đầu 1 của bản trước.

Đã đối chiếu tự động đủ **42 dòng** trong `BẢNG CÁC BIẾN TÍNH TOÁN TRONG 4 BƯỚC M3-A` với
`plan_variable_coverage` trong [manifest báo cáo](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/full-variables/manifest_v2.json).
Các tên alias của cùng biến dùng cột tương ứng, không coi là biến độc lập. Các nhóm bổ sung:

- Bước 1: `usable_financial_years`, `selected_fiscal_year`, `usable_from_date`, cutoff, eligibility,
  các tập traded universe/Market Eligible Pool/Financial Eligible Pool/Candidate Universe,
  `mom_126`, `downside_vol_63`, `liquidity_21`, `roe`, `f_score`, `z_score`, percentile từng tiêu chí,
  `S_market`, `S_fin`, `combined_score`, `n_min`, `n_select`, `target` và segment boundary.
- Bước 2: `Current Portfolio`, `Actual Holdings`, `pf`, `cash`, `values[ticker]`, `marks[ticker]`,
  `current_price`, `price(ticker, date)`, `adj_close`, `raw_close`, `volume`, `ceiling`, `floor`,
  `tradable(ticker, date, side)`, `PRICE_STALE`, `delta_weight`, `available_cash`,
  `required_buy_cash`, `execution_scale`, `traded`, `flag` và state sau từng action.
- Bước 3: state/mark/giá trị từng mã tại ngày định giá, `stale`, `PRICE_STALE`, `end_date`, NAV,
  return và contribution. Trạng thái cuối khoảng giữ được tái lập trên bản sao Portfolio để đối chiếu,
  không áp dụng hai lần vào chuỗi Portfolio thực tế.
- Bước 4: `schedule`, `goal`, `Target Portfolio mới` và Portfolio chuyển kỳ. Cột schedule hiển thị
  entry của kỳ đang xử lý; đầy đủ 59 execution entry nằm trong manifest. Callable của Q6 được biểu diễn
  bằng recipe giữ tỷ trọng cũ trên các mã còn thuộc Candidate Universe, không giả thành dict target mua mới.

Các object/dict/set được ghi dạng JSON trong ô tổng hợp; `values[ticker]` và `marks[ticker]` là giá trị
của đúng mã ở dòng chi tiết. `marks[ticker]` dùng tên biến trong kế hoạch tại date tương ứng, không đưa
trở lại ba tên cột giá tự đặt của bản đầu. `available_cash` là cash sau SELL trước BUY; `cash` trên từng
dòng giao dịch là cash sau action đó. `traded` ở dòng giao dịch là giá trị executed cộng dồn,
ở dòng tổng hợp là tổng kỳ. Các ngữ nghĩa/alias được ghi đầy đủ trong manifest.

Để xuất các state chưa persist trong canonical outputs, đã tái lập bằng đúng `engine.py`, `ranking.py`
và `PriceBook` của commit frozen `a5d9872`; không fit lại model, không tạo official run mới.
Đã xác minh hash input; C8 được scan/hash đầy đủ để lấy trần/sàn đúng phiên. Giá gốc `adj_close`
và volume đọc terminal, `current_price` là giá runtime sau Q17, raw close/trần/sàn dùng C8 đúng như engine.
Tái lập 2.584 bộ điểm ứng viên bằng `ranking.py`; đủ ticker/rank/target_weight khớp run gốc.
Tái lập state 59 execution cycles bằng engine đã khóa, đối chiếu từng ledger field, holdings, turnover,
NAV và hai sự kiện stale của Combined đều khớp. NAV cuối vẫn `2.1615233667541727`.

Ví dụ HVT kỳ 2, execution `2019-03-01`, nay đọc trực tiếp được:

| Cột | Giá trị |
|---|---|
| `side` | `BUY` |
| `volume` | 0 |
| `current_price` / `adj_close` | 13327,4 |
| `raw_close` | 50600 |
| `ceiling` / `floor` | 55600 / 45600 |
| `tradable(ticker, date, side)` | `false` |
| `status (ledger)` | `BUY_FAILED` |
| `Ghi chú` | Chặn lệnh: volume = 0. |

Đã kiểm tra đủ 80 failed orders có lý do: 58 volume=0, 12 raw close chạm/vượt ceiling, 8 chạm/dưới floor,
2 thiếu current price và dữ liệu phiên. Đây là chẩn đoán từ input tại execution, giữ nguyên flag canonical;
engine trả về sớm vì thiếu price/volume thì không tự thêm `LIMIT_DATA_MISSING` vào ledger.
Những row HOLD không gọi tradable được để trống, không tự gán false.

Read-back kiểm tra 97 tên cột duy nhất, mapping của đủ 42 dòng biến, số dòng/240 summary cuối bước,
giữ nguyên dữ liệu báo cáo trước ngoài các ô bổ sung được yêu cầu, công thức scoring, cash/required/scale,
turnover, failed reasons và boundary kỳ 60 đều PASS. Inspect/render bảng chính và mẫu HVT/WCS/NDN đạt.
Self-review `PASS`: không sửa 33 file run gốc, seal, code/config hoặc `M3_READINESS.md`; chưa mở Holdout.
SHA256 CSV hiện hành: `b7c498c34c3763579ec7089b098f8f0b78ed3cf1749cfc4e06a0554874623224`.

### 3.18. Bổ sung biến Bước 2 vào bản plan-columns đã chốt

Đã cập nhật trực tiếp file `plan-columns` theo lựa chọn của owner. Bản 57 cột có 5.656 dòng, một cột
`ticker` và dòng tổng hợp ở đầu mỗi bước theo bố cục của bản 35 cột. Đã thêm 22 cột dành riêng cho Bước 2,
thành 57 cột. Ánh xạ bao phủ 21 mục trong bảng biến áp dụng cho Bước 2. Các cột bổ sung để trống ở Bước 1, 3 và 4.

Đã ghép dữ liệu đã đối chiếu ở Mục 3.17 theo kỳ, bước, loại dòng, ngày, mã và hành động. Kiểm tra sau xuất
xác nhận thứ tự dòng và 35 cột đầu khớp bản đã chốt. `Ghi chú` của 80 lệnh thất bại được bổ sung lý do.
Ở HVT kỳ 2, các cột ghi `volume=0`, `tradable(ticker, date, side)=false` và `BUY_FAILED`.
Hash của 33 file nguồn khớp seal Development.

SHA256 CSV là `5166f65166ee4e868d8cc5a1f1a7218c5cdba5b728871c60cae0703715eb723d`.

### 3.19. Bản plan-columns để đọc từng kỳ

Owner chốt 21 cột để theo dõi kết quả chọn mã, giao dịch, tỷ trọng và NAV theo từng kỳ. Đã cập nhật file
`plan-columns` và đối chiếu toàn bộ 5.656 dòng với bản trước theo đúng 21 cột đã chọn. File có đủ 60 kỳ và
240 dòng tổng hợp, mỗi dòng nằm cuối nhóm `Kỳ/Bước` tương ứng. Đã đối chiếu thứ tự và giá trị của các dòng
chi tiết sau khi chuyển dòng tổng hợp. Dòng HVT kỳ 2 ghi `volume=0`, `BUY_FAILED` và lý do trong `Ghi chú`.
Theo yêu cầu owner, bổ sung `pre-rebalance-weight` ngay sau `weight`, đưa tổng số lên 22 cột.
Đã đối chiếu 802 tỷ trọng cuối khoảng giữ ở các dòng `ĐỊNH GIÁ` của Bước 3 với bản gốc 35 cột.
[CSV hiện hành](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/plan-columns/BACKTEST_DEV_COMBINED_V2.csv)
· [Manifest](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/plan-columns/manifest_v2.json)

SHA256 CSV là `511f3cccf0c27309a8486948e39151abad4fe646844110d0d9915b7cc96ff7f4`.

### 3.20. Rà soát Development trước Holdout

Owner yêu cầu kiểm tra toàn bộ kết quả Dev trước khi mở Holdout. Đã rà soát code và đối chiếu độc lập
run `20261104T060408Z-5557288c`, giữ identity commit nguồn `a5d9872` và config đã LOCKED.
Hash của bảy input và của đủ 33 file run khớp manifest/seal. Các lần đối chiếu và mã source dùng cho
review được ghi trong evidence local.

| Phần kiểm tra | Kết quả |
|---|---|
| PIT và Candidate Universe | Đối chiếu từng mã/ngày của cả năm strategy. Q-date, FY mới nhất usable, stale, cutoff, sector, cluster và lý do loại khớp audit. |
| Chọn mã và rank | Đối chiếu đủ 60 decisions của mỗi strategy. Tính percentile/scoring độc lập, tie-break và top-share khớp target. |
| Ngày execution và boundary | 59 executions trong Dev, quyết định cuối chỉ lưu target. NAV cuối đúng `2023-12-29`. |
| Mua/bán | Kiểm tra price/volume/trần/sàn, intended/executed, SELL trước BUY, failed orders, scaling và rule giữ vị thế cũ khi dưới N_min. |
| Dòng tiền và danh mục | Dựng sổ lượng nắm giữ độc lập từ vốn đầu 1. Giá trị bằng lượng × mark, tiền mua/bán cập nhật cash. Ledger, holdings và NAV khớp ở mọi kỳ của năm strategy. |
| Metrics và benchmark | Turnover, total return, CAGR, volatility, drawdown và stale khớp. VNINDEX được chuẩn hóa trên cùng 60 ngày định giá. |
| Q17 | Phát hiện hai cờ sai trên ngày lân cận, cần sửa implementation và đồng bộ count repair trong run mới. |

#### Lỗi phát hiện và ảnh hưởng

`PriceBook` nạp execution/valuation dates và các ngày lân cận. Detector Q17 trước sửa duyệt ba dòng liền
nhau trong tập được nạp. Ở các khoảng không nạp đủ ngày, ba dòng đó có thể cách nhau nhiều phiên.
Điều kiện này khác ba phiên giao dịch liền kề được quy định trong kế hoạch.

| Cờ repair sai trong run nguồn | Ba dòng thực tế detector đã dùng | Phiên lân cận đúng theo calendar |
|---|---|---|
| HND `2023-07-31` | `2023-07-04`, `2023-07-31`, `2023-08-01` | `2023-07-28`, `2023-07-31`, `2023-08-01` |
| DNN `2023-08-02` | `2023-08-01`, `2023-08-02`, `2023-08-31` | `2023-08-01`, `2023-08-02`, `2023-08-03` |

Hai ngày này đều là phiên lân cận, nằm ngoài 60 execution/valuation dates của run Dev. Đối chiếu từng giá
được sử dụng và dựng lại danh mục bằng lượng nắm giữ xác nhận **NAV và lợi suất của cả năm strategy khớp
kết quả nguồn**. Metadata `adj_glitches_repaired` của run nguồn bị đếm 36, còn 34 cờ thỏa đủ điều kiện.

Đã sửa `repair_ratio_glitches` nhận optional calendar, và `PriceBook` truyền lịch đã giới hạn segment.
Detector chỉ repair khi ngày trước/sau trong dữ liệu trùng phiên exchange trước/sau của ngày đang xét.
Ba regression test mới kiểm tra bảng nạp thưa, thiếu giá phiên trước tại execution date và bộ ba phiên
qua kỳ nghỉ lễ. Hai test đầu đã tái hiện lỗi trước sửa. Sau sửa, đủ 52 test M3 PASS, `compileall` PASS,
[synthetic smoke](../data/runs/run-20261104T095526Z-2a2c62ba/manifest.json) có `status=complete`, exit 0.

#### Evidence và gate trước Holdout

- [Review trước sửa](../data/experiments/m3/reviews/development/20261104T060408Z-5557288c/pre-holdout-20261104/verification-before-fix.json)
  ghi hai cờ sai và đối chiếu selection/accounting của năm strategy.
- [Review sau sửa](../data/experiments/m3/reviews/development/20261104T060408Z-5557288c/pre-holdout-20261104/verification-after-fix.json)
  xác nhận runtime còn 34 cờ hợp lệ và toàn bộ giá được sử dụng, selection, accounting, metrics danh mục
  khớp. Trạng thái review là `PARTIAL` vì file metrics của run nguồn vẫn ghi count 36.
- Helper độc lập là `.tmp/review_m3_dev_before_holdout.py`. Hash source `prices.py` ở từng lần kiểm tra
  và danh tính manifest/seal nguồn nằm trong evidence.

Giới hạn đã chấp nhận tiếp tục được công bố khi diễn giải kết quả, gồm chi phí/slippage 0, drawdown trên
các ngày NAV được lưu, vendor-adjusted close so với VNINDEX price index và vintage/revision tài chính
tại Mục 3.2. Các điểm này được giữ theo methodology đã khóa.

Self-review kết luận portfolio accounting Dev `PASS`, sửa Q17 runtime `PASS`, gate chuyển Holdout còn
`PARTIAL`. Next action là owner commit bản sửa, chạy lại Development bằng version code đó, rồi verify/seal
run mới để metadata Q17 và code identity đồng bộ. Sau checkpoint đó mới thực hiện Holdout bằng cùng version.
Kết quả nguồn, seal nguồn và CSV diễn giải hiện có được lưu làm evidence của run trước sửa.

## 4. Công việc còn lại và gate chuyển bước

| Thứ tự | Công việc | Điều kiện hoàn tất |
|---:|---|---|
| 1 | Chấp nhận snapshot đầu vào đã `PASS` theo owner | Xem quyết định ở Mục 3.5. Dùng Indicators v1 đã pin và disclosure các giới hạn ghi tại Mục 3.2. |
| 2 | Gate cutoff tại runtime đã `PASS` | Xem kết quả thực hiện ở Mục 3.4. Dùng implementation này cho feasibility và targets-only chính thức sau khi các gate đầu vào đạt. |
| 3 | Pin B-PIT và feasibility đã `PASS` | Xem Mục 3.6 và 3.7. Giữ `N_min=10` và rule Va theo config đã khóa về methodology. |
| 4 | Targets-only Development và Holdout đã `PASS` | Xem Mục 3.9 và 3.10. Hai run cùng code/config/input/B-PIT; lịch `60/59/1` và `24/23/1`, target weights và số dòng universe audit đều đạt. |
| 5 | Strict isolation, config `LOCKED` và checkpoint commit đã `PASS` | Xem Mục 3.11–3.12. Commit `a5d9872`, hash config đã ghi và code/config đạt `git_dirty=false`. |
| 6 | Dev nguồn đã seal, audit danh mục `PASS`. Cần commit Q17 và verify/seal run Dev đồng bộ | Xem Mục 3.20. Bản sửa qua 52 test/compile/smoke, đếm đúng 34 repair. NAV năm strategy khớp run nguồn. Chờ owner commit và chạy lại Dev. CSV 22 cột vẫn gắn run nguồn. |
| 7 | Holdout → verify → seal — chờ gate Dev tại Mục 3.20 | Dùng version code của run Dev mới sau sửa Q17, cùng config `LOCKED` và input đã pin. Ngày NAV cuối dự kiến `2025-12-31`. |
| 8 | Đối chứng, đánh giá và tái lập | So sánh Combined với bốn strategy đối chứng và VNINDEX theo từng đoạn. Báo số kỳ thiếu ứng viên và giới hạn dữ liệu. Chuẩn bị artifact sealed cho M3-B và notebook M3-C. |

Mỗi lần cập nhật báo cáo sau run chính thức cần ghi segment, run ID, Git commit, `config_sha256`, revision dataset, SHA256 đầu vào và đầu ra, kết quả verify cùng đường dẫn artifact đã seal. Bảng Development đã có tại Mục 3.13; sau Holdout verified bổ sung bảng riêng, không nối hai NAV. Final Evaluation có gate riêng trong kế hoạch chuẩn.
