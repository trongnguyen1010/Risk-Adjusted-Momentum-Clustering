# Báo cáo thực hiện backtest M3

**Ngày chốt báo cáo** 04/11/2026, giờ Việt Nam  
**Nhánh** `feature/indicators-v1`  
**Git HEAD ban đầu** `42d3af869ac43c2f199e36916700b58c6959bcf1`<br>
**Commit backtest chính thức hiện hành** `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf`<br>
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
| Official Development → verify → seal | `PASS` | Run mới `20261104T121107Z-5557288c`, commit `c9c1f5f`, `git_dirty=false`. Đã verify/seal, Q17 có đúng 34 repair; xem Mục 3.21. |
| Rà soát trước Holdout | `PASS` | Sửa Q17 qua 52 test M3, compile, synthetic smoke; run Dev mới có 31 CSV khớp byte với run đã đối chiếu độc lập. NAV và metrics danh mục giữ nguyên. |
| Official Holdout → verify → seal | `PASS` | Run `20261104T133507Z-5557288c`, cùng commit/config/bảy input với Dev đã seal. Đã đối chiếu giao dịch, dòng tiền, lượng nắm giữ, NAV, metrics và VNINDEX; xem Mục 3.22. |
| Final Evaluation | `NOT_READY` | Owner xác nhận ngày 04/11/2026 chưa đủ dữ liệu 2026. Chưa khóa exact window, chưa thêm segment Final vào config và chưa chạy Final. |
| M3-C — notebook và báo cáo kỹ thuật | Dev/Holdout `PASS`, tổng thể `PARTIAL` | Notebook 01–03 đã thực thi từ kernel sạch và đối chiếu hai run đã seal; báo cáo/hướng dẫn ở `M3`. Notebook 04 chưa chạy do Final `NOT_READY`; xem Mục 3.26. |

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
[CSV v2 theo bố cục đã chốt](../M3/BACKTEST_DEV_COMBINED_V2.csv)

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
[CSV hiện hành](../M3/BACKTEST_DEV_COMBINED_V2.csv)
· [Manifest](../data/experiments/m3/reports_v2/development/20261104T060408Z-5557288c/plan-columns/manifest_v2.json)

SHA256 CSV là `511f3cccf0c27309a8486948e39151abad4fe646844110d0d9915b7cc96ff7f4`.

Theo yêu cầu owner, file CSV 22 cột đã được di chuyển vào `M3/BACKTEST_DEV_COMBINED_V2.csv`.
SHA256 trước và sau di chuyển khớp; nội dung giữ nguyên. Manifest tại đường dẫn gốc được giữ làm evidence.

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

### 3.21. Development chạy lại sau sửa Q17: verify và seal `PASS`

Owner đã commit bản sửa Q17 tại `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf` và chạy lại
Development, `BACKTEST_DEV_EXIT=0`. Run chính thức hiện hành là
[20261104T121107Z-5557288c](../data/experiments/m3/development/20261104T121107Z-5557288c/manifest.json).
Manifest xác nhận `git_dirty=false`, `targets_only=false`, `financial_source=B_PIT`, config `LOCKED`.
SHA256 config giữ nguyên `b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d`.
Revision dataset vẫn là `08c24867b11177072bfe457a4623a38abf9bbc48`; đã hash lại đủ bảy input,
gồm toàn bộ C8 prices, và tất cả khớp các giá trị đã pin trong manifest.

| Kiểm tra | Kết quả |
|---|---|
| Lịch và số quyết định | Cả năm strategy có 60 decisions, 59 executions và một quyết định cuối không execution; NAV cuối `2023-12-29`. |
| Thiếu ứng viên | Combined vẫn 13 kỳ dưới `N_min`; bốn strategy đối chứng không có kỳ dưới `N_min`. |
| Q17 runtime | Có đúng 34 repair, khớp bộ đối chiếu độc lập tại Mục 3.20; không còn hai cờ sai HND/DNN. Giá nạp nằm trong ranh giới Dev. |
| Output | Đủ 33 file. Toàn bộ 31 CSV khớp byte với run nguồn đã seal và được đối chiếu độc lập tại Mục 3.20. Chỉ manifest và metadata Q17 trong metrics thay đổi. |
| Metrics | Metrics của năm strategy và VNINDEX giữ nguyên; riêng `adj_glitches_repaired` đổi từ 36 thành 34. Chưa tính Sharpe. |

Việc verify tái sử dụng bằng chứng selection và sổ lượng nắm giữ độc lập của Mục 3.20 thông qua hash
manifest/seal nguồn và hash source `prices.py`. Đối chiếu byte của 31 CSV xác nhận toàn bộ target,
universe audit, ledger, holdings, NAV, turnover và benchmark của run mới giống kết quả đã kiểm tra.
Đồng thời kiểm tra lại code identity, config, input, Q17 runtime và ranh giới segment cho run mới.
Helper kiểm tra là `.tmp/seal_m3_development_q17_rerun.py`; SHA256 helper được ghi trong seal.

Đã tạo [seal Development mới](../data/experiments/m3/seals/development/20261104T121107Z-5557288c/seal.json)
với `status=PASS`, lưu SHA256 của đủ 33 file cùng đường dẫn và hash bằng chứng tham chiếu.

| Artifact | SHA256 |
|---|---|
| `manifest.json` run mới | `994b7bb6bd7473a5bd2f18f02972dab91fd7e02e457bb07666eba6ebc41b623b` |
| `metrics.json` run mới | `dda8a822ec791e390366b2f0aab27a7c4b27b17cbb191f048c62e4c7c37eef84` |
| `seal.json` run mới | `39784248f3777700ebc0261ef53f20053bc4429920785472bba416150e902661` |

Self-review `PASS`: run mới đúng commit đã sửa, output được verify/seal và gate Dev tại Mục 3.20
đã hoàn tất. Run/seal cũ và evidence review được giữ nguyên. CSV diễn giải 22 cột tại Mục 3.19 vẫn ghi
identity run cũ; các CSV nguồn nghiệp vụ của hai run khớp byte, chưa xuất lại bản diễn giải trong bước này.
Chỉ cập nhật báo cáo, không sửa `M3_READINESS.md`, code/config hoặc tự chạy Holdout.
Bước tiếp theo là chạy Holdout bằng cùng commit `c9c1f5f`, config và input đã pin, rồi verify/seal riêng.

### 3.22. Holdout chính thức: verify và seal `PASS`

Owner đã chạy Holdout và nhận `BACKTEST_HOLDOUT_EXIT=0`. Run
[20261104T133507Z-5557288c](../data/experiments/m3/holdout/20261104T133507Z-5557288c/manifest.json)
ghi `targets_only=false`, `financial_source=B_PIT`, config `LOCKED`, `git_dirty=false`.
Commit là `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf`, SHA256 config là
`b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d`, trùng Dev tại Mục 3.21.
Revision dataset giữ nguyên `08c24867b11177072bfe457a4623a38abf9bbc48`.
Đã hash lại bảy input, kể cả toàn bộ C8 prices; các giá trị khớp manifest và seal Dev.

#### Kết quả kiểm tra

- Đủ 33 file output. Mười CSV targets/universe audit khớp byte với Holdout targets-only tại Mục 3.10.
  Kiểm tra 24 decision dates, execution là phiên kế tiếp, số ứng viên, membership, rank và tổng target weight đạt.
- Cả năm strategy có 24 decisions, 23 executions và một quyết định cuối `2025-12-31` không execution.
  NAV được khởi tạo độc lập bằng 1 tại `2024-02-01`, kết thúc tại `2025-12-31`; không nối danh mục/NAV Dev.
- Combined có một kỳ `UNIVERSE_TOO_SMALL`, decision `2025-04-29`, chỉ bốn ứng viên. Rule Q6 giữ mã cũ
  còn thuộc tập ứng viên, không mua mới, được kiểm tra cùng ledger. Bốn strategy còn lại không có kỳ dưới N_min.
- Q17 được tính độc lập từ các phiên exchange liền kề thật: toàn bộ giá và 110 cờ repair khớp runtime.
  Giá/volume nạp nằm trong ranh giới Holdout. Trần/sàn được đọc trực tiếp trong lượt scan/hash C8.
- Đối chiếu từng ledger field: intended/executed, SELL trước BUY, volume/trần/sàn, failed orders, scaling,
  bảo toàn vốn, holdings và turnover. Dựng thêm sổ lượng nắm giữ × giá độc lập xác nhận NAV và tỷ trọng
  ở mọi kỳ của năm strategy. Không gọi portfolio engine để xác minh accounting.
- Metrics được tái tính từ output; VNINDEX chuẩn hóa trên đúng cùng 24 ngày định giá. Không có Sharpe.
  Tất cả hash output trước/sau kiểm tra giữ nguyên.

#### Kết quả Holdout đã seal

Các giá trị dưới đây được lấy từ `metrics.json`; 24 điểm NAV tạo 23 khoảng lợi suất, CAGR dùng `23/12` năm.

| Strategy / benchmark | Tổng lợi suất | CAGR | Biến động năm | Max drawdown | Turnover trung bình mỗi kỳ | Cash trung bình sau giao dịch |
|---|---:|---:|---:|---:|---:|---:|
| Combined | 38,95% | 18,72% | 28,59% | -26,27% | 54,53% | 8,92% |
| Market-only | 22,43% | 11,14% | 23,75% | -18,91% | 58,52% | 3,75% |
| Financial-only | 28,37% | 13,92% | 7,30% | -3,95% | 24,37% | 2,54% |
| Equal-weight | 29,53% | 14,45% | 13,34% | -7,40% | 8,41% | 0,47% |
| Momentum-only | 41,37% | 19,80% | 15,60% | -8,92% | 27,50% | 0,82% |
| VNINDEX | 52,13% | 24,47% | 16,08% | -5,87% | — | — |

Combined kết thúc với NAV `1.3894883661092423`, thấp hơn VNINDEX về tổng lợi suất 13,18 điểm phần trăm.
Combined cao hơn Market-only, Financial-only và Equal-weight, nhưng thấp hơn Momentum-only về tổng lợi suất;
max drawdown sâu hơn cả bốn đối chứng và VNINDEX trên các chuỗi NAV đang dùng.
Đây là kết quả theo config đã khóa, không thay rule để cải thiện kết quả Holdout.

> **Giới hạn đối sánh:** Combined dùng giá cổ phiếu điều chỉnh, còn VNINDEX là chỉ số giá, nên lợi suất và
> mức sụt giảm tối đa chưa hoàn toàn tương đương. Mức sụt giảm chỉ được đo tại các ngày định giá theo kỳ;
> backtest chưa tính phí giao dịch và trượt giá.

Giới hạn vintage/revision tài chính tại Mục 3.2 tiếp tục áp dụng.

| Strategy | BUY_FAILED | SELL_FAILED | SCALED | PRICE_STALE | LIMIT_DATA_MISSING |
|---|---:|---:|---:|---:|---:|
| Combined | 17 | 23 | 93 | 3 | 0 |
| Market-only | 40 | 25 | 254 | 5 | 0 |
| Financial-only | 123 | 96 | 614 | 1 | 0 |
| Equal-weight | 1.073 | 1.169 | 9.019 | 29 | 0 |
| Momentum-only | 409 | 464 | 2.430 | 6 | 0 |

Combined có ba sự kiện dùng last valid mark: PTX ngày `2024-10-01` và `2024-11-01`, VVS ngày `2025-12-01`.
Đây là các mã/ngày thiếu giá được ghi nhận theo policy `PRICE_STALE`; toàn bộ sự kiện của năm strategy
được lưu trong seal. Counts là số sự kiện/lệnh, không phải số mã duy nhất.

#### Evidence và self-review

[Seal Holdout](../data/experiments/m3/seals/holdout/20261104T133507Z-5557288c/seal.json)
ghi `status=PASS`, hash đủ 33 file, hash bảy input, seal Dev tham chiếu, kết quả accounting/metrics và stale.
Helper là `.tmp/verify_m3_holdout_20261104.py`, có SHA256 được ghi trong seal.

| Artifact | SHA256 |
|---|---|
| `manifest.json` Holdout | `78049d610321e1fd63888437d705a57423ec04129549fc7eb255c0d9d046c0c1` |
| `metrics.json` Holdout | `30a45d1556df42e7ecb8e2fd7dd3f04b418be0b329926da1580ceb13bc63d9c7` |
| `seal.json` Holdout | `f54ea2fb1d0da107d684178c541c9f9c634a11f4de463ad4352e4967ec152cbc` |

Self-review `PASS`: hoàn tất đúng bước Holdout → verify → seal, không sửa code/config, dữ liệu đầu vào,
run/seal Dev, CSV diễn giải hoặc `M3_READINESS.md`. Không chạy lại model, không tuning sau Holdout.
Đợt này chỉ dùng helper kiểm tra local và cập nhật báo cáo; không thay pipeline nên không lặp unit suite.
Chưa tự chuyển sang Final Evaluation, dashboard hoặc notebook.

### 3.23. CSV Holdout Combined v2 theo bản Dev đã chốt

Theo yêu cầu owner, đã xuất [BACKTEST_HOLDOUT_COMBINED_V2.csv](../M3/BACKTEST_HOLDOUT_COMBINED_V2.csv)
trong thư mục `M3`, dùng đúng 22 tên cột và thứ tự cột của bản Dev tại Mục 3.19.
File là báo cáo diễn giải từ Holdout đã seal ở Mục 3.22, không chạy lại strategy hoặc portfolio engine.

File có **1.892 dòng**, gồm 829 dòng ứng viên, 411 dòng giao dịch, 278 dòng danh mục,
278 dòng định giá và 96 dòng tổng hợp. Giữ đủ 24 kỳ, bốn bước mỗi kỳ, mỗi dòng tổng hợp nằm cuối bước.
Giữ cả ứng viên không được chọn ở Bước 1. Kỳ 24 chỉ lưu target và các dòng tổng hợp kết thúc đoạn;
không tạo giao dịch hoặc khoảng nắm giữ mới.

`weight` ở Bước 3 là tỷ trọng đầu khoảng giữ, `pre-rebalance-weight` là tỷ trọng cuối khoảng giữ tại `date`.
Các tỷ trọng/lợi suất dùng tỷ lệ 0–1, NAV và executed dùng giá trị vốn chuẩn hóa với vốn ban đầu bằng 1.
Volume được bổ sung tại các dòng mã Bước 2, giữ đơn vị shares. Đủ 40 lệnh thất bại có lý do trong `Ghi chú`,
đối chiếu price/volume và raw close/trần/sàn từ input đã hash. Ô thiếu/không áp dụng giữ trống.

Read-back kiểm tra đủ 22 cột khớp bản Dev, 24 kỳ/96 tổng hợp cuối bước, toàn bộ ứng viên, target weights,
ledger, holdings, 278 tỷ trọng cuối khoảng giữ, cash ratio và NAV/lợi suất từng kỳ đều `PASS`.
Lợi suất ghép của 23 khoảng khớp NAV cuối `1.3894883661092423`.
Artifact Tool round-trip, inspect và render đạt; SHA256 đủ 33 file Holdout vẫn khớp seal.

[Manifest CSV](../data/experiments/m3/reports_v2/holdout/20261104T133507Z-5557288c/plan-columns/manifest_v2.json)
ghi source run/commit/config, seal hash, input/output hashes, template Dev hash, counts, đơn vị và builders.
SHA256 CSV là `82e6b1cb5cb7db061ad3b2a0b838967555604071903d479044699c41c980dcb7`.
Self-review `PASS`: không sửa CSV Dev, run/seal nguồn, code/config hoặc `M3_READINESS.md`;
chỉ xuất báo cáo Holdout được yêu cầu và cập nhật báo cáo tiến độ.

### 3.24. So sánh kết quả đối sánh giữa Development và Holdout

Số liệu lấy từ [metrics Dev hiện hành](../data/experiments/m3/development/20261104T121107Z-5557288c/metrics.json)
và [metrics Holdout](../data/experiments/m3/holdout/20261104T133507Z-5557288c/metrics.json), đều thuộc run đã seal.
Dev có 59 khoảng lợi suất, Holdout có 23 khoảng. Vì độ dài khác nhau, dùng CAGR để so sánh thêm bên cạnh
tổng lợi suất; không nối NAV hai đoạn hoặc diễn giải tổng lợi suất thấp hơn là hiệu quả năm hóa thấp hơn.

| Strategy / benchmark | Tổng lợi suất Dev | Tổng lợi suất Holdout | CAGR Dev | CAGR Holdout |
|---|---:|---:|---:|---:|
| Combined | 116,15% | 38,95% | 16,97% | 18,72% |
| Market-only | 128,81% | 22,43% | 18,34% | 11,14% |
| Financial-only | 40,74% | 28,37% | 7,20% | 13,92% |
| Equal-weight | 159,03% | 29,53% | 21,36% | 14,45% |
| Momentum-only | 169,73% | 41,37% | 22,36% | 19,80% |
| VNINDEX | 24,35% | 52,13% | 4,53% | 24,47% |

Combined tăng từ thứ 4/5 strategy trong Dev lên thứ 2/5 trong Holdout, không tính VNINDEX vào thứ hạng strategy.
Trong Dev, Combined chỉ cao hơn Financial-only; trong Holdout, Combined cao hơn Market-only, Financial-only
và Equal-weight. Khoảng cách CAGR thấp hơn Momentum-only thu hẹp từ 5,39 xuống 1,08 điểm phần trăm.
So với VNINDEX, Combined chuyển từ CAGR cao hơn 12,44 điểm phần trăm trong Dev sang thấp hơn
5,75 điểm phần trăm trong Holdout. Đây là mô tả trên các chuỗi hiện có, với giới hạn return basis bên dưới.

| Strategy / benchmark | Max drawdown Dev | Max drawdown Holdout |
|---|---:|---:|
| Combined | -44,60% | -26,27% |
| Market-only | -47,88% | -18,91% |
| Financial-only | -27,20% | -3,95% |
| Equal-weight | -37,01% | -7,40% |
| Momentum-only | -33,71% | -8,92% |
| VNINDEX | -33,02% | -5,87% |

Combined có drawdown sâu hơn toàn bộ bốn đối chứng và VNINDEX trong Holdout. Drawdown của Combined
ít sâu hơn ở Holdout so với Dev chưa chứng minh rủi ro giảm, vì hai đoạn khác độ dài và giai đoạn thị trường.
Biến động năm của Combined tăng từ 27,39% lên 28,59%.

#### Phân tích ý nghĩa của kết quả đối sánh

**Hiệu quả của Combined qua hai đoạn.** CAGR tăng từ 16,97% lên 18,72% cho thấy lợi suất năm hóa của
Combined không suy giảm trong Holdout. Tuy nhiên, thứ hạng tăng từ 4/5 lên 2/5 còn đi cùng việc CAGR
của Market-only, Equal-weight và Momentum-only giảm. Vì vậy, thứ hạng cải thiện chưa chứng minh mô hình
ổn định hơn hoặc có khả năng khái quát tốt hơn. Hai đoạn thuộc các giai đoạn khác nhau, với Holdout chỉ
có 23 khoảng lợi suất; kết quả hiện tại là bằng chứng mô tả trên hai mẫu, chưa phải kiểm định ý nghĩa thống kê.

**So với Market-only: lợi ích của phương án kết hợp chưa nhất quán về rủi ro.** Trong Dev, Combined có
CAGR thấp hơn 1,36 điểm phần trăm, đồng thời biến động thấp hơn và drawdown ít sâu hơn Market-only.
Đó là một đánh đổi giữa lợi suất và rủi ro. Sang Holdout, Combined cao hơn 7,59 điểm phần trăm CAGR,
nhưng drawdown sâu hơn 7,37 điểm phần trăm và biến động tăng từ mức 23,75% của Market-only lên 28,59%.
Phương án kết hợp có lợi thế lợi suất trong Holdout, nhưng chưa cho thấy tác dụng giảm rủi ro xuyên suốt
hai đoạn. Chênh lệch này phản ánh toàn bộ thay đổi về tập ứng viên và cách xếp hạng giữa hai strategy;
chưa tách riêng được đóng góp nhân quả của bộ lọc Financial.

**So với Financial-only: lợi suất cao hơn đi cùng mức dao động lớn hơn.** Combined có CAGR cao hơn
Financial-only trong cả Dev và Holdout. Tuy nhiên, trong Holdout, phần lợi suất năm hóa tăng thêm
4,81 điểm phần trăm đi cùng biến động 28,59% so với 7,30%, và drawdown -26,27% so với -3,95%.
Do đó, Combined thể hiện khả năng tìm lợi suất cao hơn trên mẫu đang xét, còn Financial-only có kết quả
ít biến động và ít sụt giảm hơn. Chưa có cơ sở mô tả Combined là phương án vượt trội trên cả hai mặt.

**So với Equal-weight: lợi ích của chọn lọc danh mục thay đổi theo giai đoạn.** Trong Dev, Equal-weight
đạt CAGR cao hơn Combined 4,39 điểm phần trăm, đồng thời có biến động thấp hơn và drawdown ít sâu hơn.
Điều này cho thấy quy trình chọn lọc của Combined chưa tạo lợi thế so với việc chia đều trên tập mã đủ
điều kiện của đối chứng trong đoạn Dev. Trong Holdout, Combined vượt Equal-weight 4,27 điểm phần trăm
CAGR, nhưng drawdown sâu hơn 18,88 điểm phần trăm và biến động cao hơn 15,26 điểm phần trăm.
Lợi thế lợi suất ở Holdout vì vậy có mức đánh đổi rủi ro đáng kể. Không thể lấy riêng phần lợi suất tăng
thêm để kết luận việc tập trung danh mục hiệu quả hơn; chưa có phân rã để xác định nguồn của phần rủi ro tăng.

**So với Momentum-only: đây là đối chứng gây bất lợi rõ nhất cho Combined.** Momentum-only có CAGR
cao hơn, biến động thấp hơn và drawdown ít sâu hơn Combined trong cả hai đoạn. Trong Holdout, Combined
chỉ còn thấp hơn 1,08 điểm phần trăm CAGR, nhưng biến động vẫn cao hơn 13,00 điểm phần trăm và drawdown
sâu hơn 17,36 điểm phần trăm. Khoảng cách lợi suất thu hẹp chưa chuyển thành lợi thế về rủi ro.
Trên ba chỉ tiêu đã đo, chiến lược chỉ dùng momentum có kết quả thuận lợi hơn phương án kết hợp phức tạp
hơn. Đây là bằng chứng quan trọng khi đánh giá giá trị tăng thêm của Combined, nhưng chưa phải kết luận
về ý nghĩa thống kê hoặc kết quả sau chi phí giao dịch.

**So với VNINDEX: chưa có lợi thế vượt thị trường nhất quán.** Combined vượt VNINDEX về lợi suất
trong Dev nhưng thấp hơn trong Holdout; ở cả hai đoạn, drawdown của Combined đều sâu hơn VNINDEX.
Vì thế, kết quả hiện hành chưa hỗ trợ nhận định Combined vừa vượt thị trường vừa bảo vệ danh mục tốt hơn.
Đối sánh này còn khác return basis, nên không gọi phần chênh lệch là alpha đã được xác nhận hoặc quy
chênh lệch hoàn toàn cho chất lượng mô hình. Khác biệt cơ sở giá ảnh hưởng cả lợi suất và drawdown,
được phân tích riêng bên dưới.

**Điều kiện vận hành cũng thay đổi giữa hai đoạn.** Combined có 13/60 quyết định thiếu ứng viên trong Dev
và 1/24 trong Holdout; tỷ trọng tiền mặt trung bình sau giao dịch giảm từ 22,40% xuống 8,92%.
Trong Holdout, strategy ít bị giới hạn bởi N_min hơn và giữ phần vốn cổ phiếu lớn hơn theo thước đo này.
Đây là bối cảnh cần xét khi đọc kết quả, chưa chứng minh tiền mặt hoặc số ứng viên là nguyên nhân làm
lợi suất thay đổi. Turnover trung bình mỗi kỳ của Combined tăng từ 47,62% lên 54,53%; khi baseline đang
để chi phí bằng 0, phần kết quả ròng sau phí và trượt giá vẫn chưa được đo. Việc này cũng hạn chế kết luận
về ưu thế sau chi phí giữa các strategy có turnover khác nhau.

> **Đánh giá từ các kết quả đã có:** Combined cải thiện thứ hạng lợi suất trong Holdout và vượt ba trong
> bốn strategy đối chứng, nhưng chưa tạo lợi thế nhất quán về lợi suất và rủi ro qua hai đoạn.
> Momentum-only thuận lợi hơn trên cả CAGR, biến động và drawdown trong cả Dev lẫn Holdout.
> Trạng thái verify/seal `PASS` xác nhận kết quả được tính đúng theo contract đã khóa; trạng thái này
> không đồng nghĩa chiến lược đã chứng minh hiệu quả đầu tư vượt trội hoặc chất lượng phân cụm tốt hơn.

#### Giới hạn cơ sở giá khi so sánh với VNINDEX

Combined dùng `adj_close` của nhà cung cấp, được sử dụng như adjusted-return proxy theo Q11;
VNINDEX là price index. Khác biệt này ảnh hưởng cả lợi suất và drawdown vì hai chỉ tiêu đều tính từ NAV.
Drawdown chỉ đo tại các ngày định giá theo kỳ; backtest chưa tính phí giao dịch và trượt giá.

Hai hướng đối sánh đồng nhất hơn có ý nghĩa khác nhau:

| Hướng tính | Ảnh hưởng có thể xảy ra |
|---|---|
| Tính Combined theo price return, loại ảnh hưởng cổ tức tiền mặt và vẫn xử lý đúng các sự kiện vốn | Lợi suất Combined có thể thấp hơn mức đang báo cáo. Chưa có phép tính để xác định mức giảm. |
| Đối chiếu Combined với benchmark total return có tính cổ tức | Kết quả Combined hiện hành giữ nguyên; lợi suất benchmark có thể cao hơn VNINDEX price index đang dùng. |

Không thay trực tiếp `adj_close` bằng `raw_close`: chia tách, cổ tức bằng cổ phiếu hoặc quyền mua có thể
tạo biến động giá cơ học, cần xử lý phù hợp để tính price return. Giá điều chỉnh hiện có chưa cho phép
tách chính xác phần đóng góp của cổ tức hoặc coi là chuỗi total return đã được tái lập đầy đủ.
Do đó, chưa thể định lượng phần chênh lệch do cơ sở giá, quy toàn bộ chênh lệch cho cổ tức hoặc kết luận
thứ hạng sẽ thay đổi sau khi đồng nhất cơ sở tính.

Các hướng trên chỉ giải thích giới hạn đối sánh, chưa được thực hiện và không thay methodology đã khóa.
Self-review: số liệu, chênh lệch CAGR/biến động/drawdown và thứ hạng đã đối chiếu hai file metrics;
counts đối chiếu manifest, cash/turnover lấy từ metrics. Phân tích phân biệt kết quả quan sát với nguyên nhân
chưa được kiểm chứng; cập nhật này chỉ bổ sung diễn giải báo cáo, không tuning hoặc chọn lại cluster/model.

### 3.25. Kế hoạch thực hiện M3-C khi Final chưa đủ dữ liệu

Theo yêu cầu owner, lập kế hoạch triển khai M3-C theo Mục 20–30 và 35 của kế hoạch chuẩn.
Tại thời điểm lập kế hoạch, chưa có thư mục `M3/notebooks`, báo cáo kỹ thuật hoặc hướng dẫn M3-C.
Hai run Dev/Holdout tại Mục 3.21/3.22 đã seal, đủ làm nguồn cho notebook 01–03 và báo cáo lịch sử.
Notebook 04 chỉ được chạy sau Final sealed theo Mục 25; hiện `NOT_READY` vì chưa đủ dữ liệu 2026.
Kế hoạch này chưa triển khai notebook, chưa thay đổi methodology và chưa đánh dấu M3-C hoàn tất.

#### Đầu vào và phạm vi

- Dev: `data/experiments/m3/development/20261104T121107Z-5557288c/` và seal tương ứng.
- Holdout: `data/experiments/m3/holdout/20261104T133507Z-5557288c/` và seal tương ứng.
- Cùng code nguồn `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf`, config `LOCKED` có SHA256
  `b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d`, bảy input đã pin và B-PIT hiện hành.
- Dùng canonical outputs và `universe_audit` để truy nguyên. Hai CSV Combined v2 là tài liệu đọc từng kỳ,
  không thay thế nguồn canonical hoặc seal trong notebook.
- Gọi lại `src/delta_t1/m3/` và hàm chính thức trong `scripts/run_m3.py` khi cần tái lập;
  không gọi pipeline để ghi đè run đã seal, không fit lại clustering, không viết business logic thứ hai.
- Không lặp audit thu thập/PDF/B-PIT đã hoàn tất. Kiểm tra identity/hash và PIT trong notebook là bước
  tái lập từ evidence hiện có. M3-B không phải phần triển khai của kế hoạch M3-C này.

#### Trình tự triển khai và nghiệm thu từng bước

Mỗi lần triển khai chỉ thực hiện một bước, kiểm tra và cập nhật tiến độ rồi dừng.

| Bước | Đầu ra | Nội dung và điều kiện nghiệm thu |
|---:|---|---|
| 1 | `M3/notebooks/01_Du_Lieu_Va_PIT.ipynb` | Chuẩn bị môi trường notebook; ghi branch/HEAD, code nguồn của run, config, input và seal hashes. Đọc hai manifest, kiểm tra artifact/schema cần dùng. Minh họa tại một số decision dates việc chọn FY usable, cutoff và target bằng module PIT/strategy chính thức. PASS khi identity/hash đạt, mẫu PIT/target khớp canonical; không tạo alignment CSV mới. |
| 2 | `M3/notebooks/02_Tai_Lap_Lua_Chon_Danh_Muc.ipynb` | Dùng `inputs`, `Strategies`, `ranking` và `universe` chính thức cho năm strategy trên toàn bộ 60/24 decisions. Minh họa Candidate → ba MC/ba FC → điểm → rank → top 30% và target weights; giải thích thiếu FC, kỳ dưới N_min và kỳ cuối không execution. PASS khi decision/execution date, ticker, rank, weight, candidates, status và audit khớp output nguồn trong tolerance phù hợp. |
| 3 | `M3/notebooks/03_Tai_Lap_Backtest_Va_Benchmark.ipynb` | Gọi `PriceBook`, `engine.run`, benchmark và hàm metrics chính thức với ranh giới từng segment. Đối chiếu ledger, holdings, turnover, NAV, metrics, failed/scaled/stale và VNINDEX; minh họa giao dịch và biến động tỷ trọng qua các bước. Tạo bảng, đồ thị NAV/drawdown và phân tích Dev/Holdout riêng. PASS khi năm strategy và VNINDEX khớp canonical, CASH/tổng weight và turnover đúng, không có Sharpe hoặc nối NAV hai đoạn. Drawdown theo ngày định giá được ghi rõ. |
| 4 | `M3/reports/BAO_CAO_KY_THUAT_M3.md` và `M3/HUONG_DAN_THUC_HIEN_M3.md` | Hoàn thiện báo cáo lịch sử từ các notebook/output đã đối chiếu: mục tiêu, phiên bản dữ liệu, hai hệ clustering, PIT, ứng viên, sáu tiêu chí, xếp hạng, execution, kết quả Combined/bốn đối chứng/VNINDEX, phân tích và giới hạn. Số liệu/bảng/biểu đồ được sinh từ nguồn, có provenance; không nhập tay số liệu kết quả. Hướng dẫn ghi đủ input/path/hash/config/commit, môi trường, lệnh đã kiểm chứng, output, cách đối chiếu, PASS/FAIL/DỪNG và thứ tự chạy. Thực thi lại notebook 01–03 từ kernel sạch cho cả hai segment, ghi kết quả đối chiếu và kiểm tra liên kết. |
| Chờ Final | `M3/notebooks/04_Bao_Cao_Danh_Gia_Cuoi.ipynb` | Hiện `NOT_READY`, không tạo kết quả giả hoặc thay Final bằng Dev/Holdout. Chỉ triển khai/chạy phần đánh giá cuối khi Final có dữ liệu đủ, window/config/hash đã khóa và run verified + sealed. Khi đó tái tạo bảng/biểu đồ Final, Sharpe nếu contract cho phép, rồi cập nhật báo cáo/hướng dẫn. |

Trong bước 1, xác minh Python/kernel và các phụ thuộc thực sự cần để chạy/hiển thị notebook; venv M3 hiện
có bộ thư viện tính toán đã kiểm tra, chưa suy ra đã có Jupyter hoặc thư viện vẽ. Chỉ bổ sung phụ thuộc
còn thiếu theo lock phù hợp, không đổi phiên bản NumPy/scikit-learn đã dùng tạo run.
Hướng dẫn chỉ công bố lệnh notebook sau khi notebook và lệnh đó đã được tạo, chạy và xác minh.

#### Kiểm tra và trạng thái bàn giao

Mỗi notebook ghi input/source run, commit nguồn và commit thực thi, config/input/output hashes, kết quả
đối chiếu và discrepancy nếu có. Khi code thực thi không còn đúng HEAD nguồn, phải xác minh các module
M3 dùng để tái lập không thay đổi so với commit nguồn; không sửa identity của run để làm khớp.
Ưu tiên tái sử dụng các evidence đã seal và dữ liệu đã nạp trong phiên, tránh build/scan đắt tiền lặp vô ích.
Nếu thêm helper, helper chỉ điều phối/đọc/đối chiếu/trình bày; chạy kiểm tra phù hợp và compile theo quy định.
Checkpoint môi trường/bàn giao áp dụng các kiểm tra repository ở Mục 30.4; không lặp full suite sau mỗi sửa Markdown.

Thiếu file/hash sai, target/accounting không khớp hoặc dùng sai segment phải dừng bước liên quan và ghi
discrepancy; không thay strategy để khớp. Bước 1–4 đạt thì ghi **M3-C phần Dev/Holdout PASS, tổng thể PARTIAL**.
Phần Final trong báo cáo phải ghi `NOT_READY`. Chỉ đánh dấu M3-C hoàn tất sau khi Notebook 04 và phần đánh giá
Final đáp ứng contract. Không sửa `M3_READINESS.md` trong quá trình thực hiện này.

### 3.26. Thực hiện M3-C — phần Dev/Holdout `PASS`, Final `NOT_READY`

Owner yêu cầu thực hiện M3-C và lưu tệp trong `M3`. Đã hoàn tất phần lịch sử theo kế hoạch Mục 3.25,
gồm ba notebook có output thực thi, báo cáo kỹ thuật sinh từ nguồn, biểu đồ và hướng dẫn tái lập.

| Đầu ra | Kết quả |
|---|---|
| [Notebook 01 — Dữ liệu và PIT](../M3/notebooks/01_Du_Lieu_Va_PIT.ipynb) | `PASS`: identity/hash hai run và bảy input; PIT/target tại 11 ngày mẫu, toàn bộ ứng viên đủ điều kiện trong các ngày đó được kiểm tra bằng module chính thức. |
| [Notebook 02 — Lựa chọn danh mục](../M3/notebooks/02_Tai_Lap_Lua_Chon_Danh_Muc.ipynb) | `PASS`: 420 lượt quyết định, gồm năm strategy × 60 Dev và 24 Holdout; đối chiếu toàn bộ target/audit rows. Có bảng ứng viên, sáu tiêu chí, percentile, điểm và trọng số mục tiêu. |
| [Notebook 03 — Backtest và benchmark](../M3/notebooks/03_Tai_Lap_Backtest_Va_Benchmark.ipynb) | `PASS`: 10 lượt strategy/segment; ledger, holdings, NAV, turnover, metrics và hai benchmark khớp canonical. Q17 đúng 34/110; kiểm tra CASH, failed/scaled, stale và segment boundaries. |
| [Notebook 04 — Đánh giá cuối](../M3/notebooks/04_Bao_Cao_Danh_Gia_Cuoi.ipynb) | `NOT_READY`: chỉ ghi phụ thuộc bằng Markdown, không có code tính performance hoặc kết quả giả. CLI từ chối chạy notebook này. |
| [Báo cáo kỹ thuật](../M3/reports/BAO_CAO_KY_THUAT_M3.md) | Sinh từ metrics/canonical đã đối chiếu, có phương pháp, kết quả, phân tích từng đối chứng và giới hạn. Biểu đồ NAV/drawdown tách nhóm theo segment đã kiểm tra trực quan. Final ghi rõ NOT_READY. |
| [Hướng dẫn thực thi](../M3/HUONG_DAN_THUC_HIEN_M3.md) | Ghi môi trường, path/hash/config/commit, lệnh đã kiểm chứng, output, điều kiện PASS/FAIL/DỪNG và thứ tự chạy; có giải thích đơn vị vốn chuẩn hóa/tỷ trọng. |

Phụ thuộc Jupyter/biểu đồ được cài riêng trong `.tmp/m3c-notebook-runtime`, có
[lock đủ phiên bản](../M3/requirements-notebooks.lock.txt); không đổi package của venv backtest M3.
[Pin nguồn](../M3/sources.json) giữ hai seal/config/source commit. `M3/m3c.py` chỉ điều phối và đối chiếu;
PIT, ranking, engine và metrics gọi module chính thức. Không build lại B-PIT, fit model hoặc sửa chiến lược.

Phiên bàn giao cuối là `M3/reproduction/20261104T143919569614Z/`:

- [Verification](../M3/reproduction/20261104T143919569614Z/verification.json) ghi
  `historical_status=PASS`, `overall_status=PARTIAL`, `final_status=NOT_READY`, hash code/notebook/report/biểu đồ,
  guide/lock/pins/Notebook 04 và phiên bản môi trường.
- [Preflight](../M3/reproduction/20261104T143919569614Z/preflight.json) ghi bảy input hash, code identity và
  snapshot trần/sàn được lấy trong cùng lượt hash C8, dùng lại trong các kernel để tránh scan lặp.
- `01_verification.json`, `02_verification.json`, `03_verification.json` ghi chi tiết đối chiếu;
  có bản sao notebook đã thực thi và kernel log.
- [Self-review bàn giao](../M3/reproduction/20261104T143919569614Z/delivery_check.json) xác nhận schema notebook,
  execution counts, không có output lỗi, các hash bàn giao, liên kết Markdown, 66 file canonical và hai CSV v2 giữ nguyên.

SHA256 `verification.json` là `163df17bd3206093a60035c426ad64d322bba5fc3daa13fbdb0dd28cd8ea4e38`.
Lệnh thực thi là `python -I -B -X utf8 M3/run_notebooks.py`, dùng Python M3 3.12.7; exit 0.
Mỗi notebook 01–03 chạy bằng một Jupyter kernel sạch. Runner không thực thi Notebook 04.

Kiểm tra bổ sung: 52 unit tests M3 `PASS`; bảy negative controls M3-C `PASS`, gồm hash/config sai,
schema/order/status sai, NaN, missing khác zero, tolerance và đúng tập mẫu percentile trước loại toàn bộ FC thiếu.
`compileall` và Markdown link checks `PASS`. Full repository suite **chưa PASS**, hết giới hạn 180 giây;
[summary/log checkpoint](../M3/reproduction/checks-20261104T143141Z/summary.json) ghi `TIMEOUT`.
Không sửa subsystem khác hoặc giảm assertion để xử lý giới hạn full suite trong stage này.

Self-review kết luận **M3-C phần Dev/Holdout PASS, M3-C tổng thể PARTIAL** vì chưa có Final đã seal.
Hai run/seal, code/config chính thức, input và CSV v2 giữ nguyên; `M3_READINESS.md` không thay đổi.
Đã cập nhật START HERE/CHANGELOG để dẫn tới bộ bàn giao. Không thực hiện M3-B hoặc mở Final.

Cập nhật theo yêu cầu owner: Notebook 03 có nhận xét ngắn gọn cho biểu đồ Dev/Holdout và lưu ý đọc drawdown.
Chỉ bổ sung Markdown, giữ nguyên code/output hiện có; bằng chứng tái lập trước đó được tham chiếu trong
[bản cập nhật nhận xét](../M3/reproduction/20261104T145154154675Z-chart-notes/verification.json).

Theo phản hồi biểu đồ nhiều đường gây rối, đã đổi bố cục: hình chính chỉ gồm Combined/VNINDEX;
bốn strategy đối chứng tách thành từng hàng NAV/drawdown, mỗi ô hai đường, cùng thang đo theo cột.
Combined luôn màu xanh liền, đối chứng màu cam đứt. Báo cáo và output Notebook 03 đã cập nhật cùng bố cục.
Đã thực thi lại notebook 01–03 từ kernel sạch và kiểm tra trực quan; target/accounting/metrics vẫn khớp nguồn.
[Evidence bố cục mới](../M3/reproduction/20261104T150049600949Z/verification.json) và self-review cùng thư mục
ghi nhận phần lịch sử PASS, 66 file canonical và hai CSV v2 giữ nguyên; Final tiếp tục NOT_READY.

Nhận xét biểu đồ trong Notebook 03 đã được tập trung vào Combined/VNINDEX theo yêu cầu owner:
diễn biến NAV, giai đoạn giảm/phục hồi và đánh đổi lợi suất/drawdown trong từng segment.
Chỉ chỉnh Markdown, giữ nguyên code, hình và kết quả; `M3/reproduction/latest.json` trỏ đến bản cập nhật cùng evidence.

### 3.27. Phân tích Bước 1, mã gây lỗ và thực thi trong đợt giảm Holdout 2024

Theo yêu cầu owner, đã tạo [báo cáo phân tích](../M3/reports/PHAN_TICH_BUOC_1_HOLDOUT_2024.md)
và script tái lập `M3/analyze_holdout_2024.py`. Phạm vi là đỉnh–đáy max drawdown quan sát của Combined,
`2024-05-02` → `2024-11-01`, không phải một cửa sổ đánh giá mới. Combined giảm 26,27%; VNINDEX
trong đúng khoảng này tăng 3,17%, với giới hạn return basis đã công bố.

- Trên cùng đường NAV thực tế, phần goal đóng góp -23,70 điểm phần trăm và lệch phân bổ sau giao dịch
  đóng góp -2,57 điểm phần trăm, cộng lại khớp mức giảm 26,27%. Đây là phân rã PnL, không phải tỷ lệ
  nguyên nhân hoặc lợi suất của một shadow backtest đã giả định fill mọi lệnh.
- CID, CAG và VTK đóng góp lần lượt -7,10, -5,79 và -4,33 điểm phần trăm, tương ứng 65,51% tổn thất ròng
  của cửa sổ. Kỳ đầu chỉ chọn bốn mã với goal 25%/mã; N_min áp dụng cho ứng viên, không bảo đảm mười mã giữ.
- Kỳ `2024-07-01` → `2024-08-01` thực giữ sáu mã khớp goal, không có failed/scaled orders và giảm 15,24%,
  trong khi VNINDEX giảm 2,20%. Đây là bằng chứng tổn thất lớn đã xuất hiện trong danh mục được chọn.
- Các mã tăng bị loại đã được truy về audit/rank tại decision, chỉ xét giá hai đầu quan sát được và BUY
  executable ở đầu kỳ. Có bảng coverage/lý do và ví dụ CDR xếp hạng 9 ngoài top 6 trước đợt tăng; không dùng
  thông tin sau kỳ để chọn lại mã. Lý do audit có thứ tự ưu tiên, chưa đo nhân quả của từng gate.
- Đã ghi các lệnh BUY_FAILED/SELL_FAILED/SCALED, volume/trần/sàn và lệch goal/thực giữ. CID ngày 01/10
  không bán giảm được vì volume=0, giữ tỷ trọng cao hơn goal rồi tiếp tục giảm; một số lệnh mua thất bại
  lại giúp tránh lỗ. Các ảnh hưởng được cộng cả chiều có lợi và bất lợi.

[Evidence phân tích](../M3/reproduction/20261104T152349610446Z-holdout-diagnosis/analysis.json),
[verification](../M3/reproduction/20261104T152349610446Z-holdout-diagnosis/verification.json) và
[self-review](../M3/reproduction/20261104T152349610446Z-holdout-diagnosis/self_review.json) ghi nguồn,
hash và đối chiếu. Replay chính thức toàn bộ ledger/holdings/NAV/turnover Holdout đạt; sổ lượng nắm giữ
độc lập xác nhận từng đóng góp và tổng PnL. Phân rã goal đủ mark, không có quan sát phải tự điền zero.
Lý do và return của mọi quan sát bỏ lỡ đều được kiểm tra lại với canonical audit/target và PriceBook.

Self-review `PASS`, compile/link checks đạt, 66 file canonical và các seal giữ nguyên. Chỉ giải thích
đợt giảm 2024, chưa quy nguyên nhân riêng cho Market/Financial/ranking hoặc giải thích toàn bộ chênh lệch
Holdout với VNINDEX. Không tuning, không thay config/engine/input, không tạo run backtest mới và không sửa
`M3_READINESS.md`. Lệnh tái lập đã chạy thành công: `python -I -B -X utf8 M3/analyze_holdout_2024.py`.

### 3.28. Chuyển mã M3-C vào notebook, bỏ phụ thuộc helper `.py` trong `M3`

Theo yêu cầu owner, notebook 01–03 hiện chứa trực tiếp mã điều phối/đối chiếu, trình bày và sinh báo cáo
trong các cell. Notebook 03 có cả mã phân tích đợt giảm 2024. Người dùng chọn kernel rồi **Run All**,
không cần chạy script/helper trong `M3`; các module nghiên cứu chính thức ở `src/delta_t1/m3` và
`scripts/run_m3.py` vẫn được gọi lại, không viết phiên bản business logic mới.

Đã di chuyển đủ bảy negative controls vào Notebook 02, giữ tên test và các assertion. Các nhận xét ngắn,
bố cục biểu đồ Combined/VNINDEX và đối chứng được giữ. File 04 tiếp tục chỉ có Markdown `NOT_READY`.

Sau khi notebook chạy đạt, đã gỡ năm file cấp `M3`: `m3c.py`, `m3c_report.py`, `run_notebooks.py`,
`test_reproduction.py`, `analyze_holdout_2024.py`. Bản cũ cùng notebook trước chuyển đổi được lưu nguyên
trong [ZIP lịch sử](../M3/reproduction/20261104T154206819006Z-notebook-migration/legacy_helpers.zip),
có [hash từng helper](../M3/reproduction/20261104T154206819006Z-notebook-migration/legacy_helpers_sha256.json).
Notebook hiện hành không import hoặc chạy mã trong ZIP. Đã dọn cache bytecode của các helper đã gỡ.

Môi trường kernel cô lập ở `.tmp/m3c-kernel/Scripts/python.exe`, Python 3.12.7, đọc bộ thư viện
notebook đã khóa qua `.pth`; không thay package venv backtest. [Hướng dẫn](../M3/HUONG_DAN_THUC_HIEN_M3.md)
đã đổi sang cách chọn kernel/Run All, không còn lệnh gọi các script đã gỡ.

Đã thực thi lại cả ba notebook từ kernel sạch **sau khi helper không còn trên filesystem**, làm việc từ
`M3/notebooks`; tất cả cell chạy đạt. [Verification bàn giao](../M3/reproduction/20261104T154826484210Z-direct-notebooks/verification.json)
ghi `historical_status=PASS`, `overall_status=PARTIAL`, `final_status=NOT_READY`, helper còn lại bằng 0.
SHA256 verification là `6ffeb7df0a0e07852121860ab4a39e6f0db28b19e327f7006c4ee5aa7e15f879`.

[Self-review](../M3/reproduction/20261104T154826484210Z-direct-notebooks/self_review.json) xác nhận:
schema/execution counts hợp lệ, 420 lượt quyết định và 10 lượt strategy/segment khớp canonical, bảy test
đã migrate PASS và không giảm assertion. Bốn PNG khớp byte với bản trước; nội dung hai CSV giữ nguyên.
Kết quả phân rã 2024 khớp baseline đã được kiểm tra bằng sổ lượng độc lập. Guide/report links đạt,
66 file canonical và các seal giữ nguyên. 52 test M3 và compileall PASS; không lặp full repository suite
vì module chính thức/pipeline không đổi, trạng thái TIMEOUT của checkpoint full suite trước vẫn được giữ.

Self-review stage chuyển đổi `PASS`; source/config M3-A và `M3_READINESS.md` không đổi. Phần lịch sử
M3-C đạt PASS, phần Final vẫn NOT_READY; chưa triển khai M3-B hoặc đánh giá Final.

## 4. Công việc còn lại và gate chuyển bước

| Thứ tự | Công việc | Điều kiện hoàn tất |
|---:|---|---|
| 1 | Chấp nhận snapshot đầu vào đã `PASS` theo owner | Xem quyết định ở Mục 3.5. Dùng Indicators v1 đã pin và disclosure các giới hạn ghi tại Mục 3.2. |
| 2 | Gate cutoff tại runtime đã `PASS` | Xem kết quả thực hiện ở Mục 3.4. Dùng implementation này cho feasibility và targets-only chính thức sau khi các gate đầu vào đạt. |
| 3 | Pin B-PIT và feasibility đã `PASS` | Xem Mục 3.6 và 3.7. Giữ `N_min=10` và rule Va theo config đã khóa về methodology. |
| 4 | Targets-only Development và Holdout đã `PASS` | Xem Mục 3.9 và 3.10. Hai run cùng code/config/input/B-PIT; lịch `60/59/1` và `24/23/1`, target weights và số dòng universe audit đều đạt. |
| 5 | Strict isolation, config `LOCKED` và checkpoint commit đã `PASS` | Xem Mục 3.11–3.12. Commit `a5d9872`, hash config đã ghi và code/config đạt `git_dirty=false`. |
| 6 | Development → verify → seal đã `PASS` sau sửa Q17 | Xem Mục 3.21. Run `20261104T121107Z-5557288c`, commit `c9c1f5f`, đúng 34 repair. 31 CSV khớp run đã đối chiếu độc lập; NAV năm strategy giữ nguyên. CSV diễn giải 22 cột vẫn gắn identity run cũ. |
| 7 | Holdout → verify → seal đã `PASS` | Xem Mục 3.22. Run `20261104T133507Z-5557288c`, cùng commit/config/input với Dev; lịch `24/23/1`, NAV cuối `2025-12-31`, đã đối chiếu accounting/metrics và seal riêng. CSV diễn giải 22 cột đã xuất tại Mục 3.23. |
| 8 | M3-C phần Dev/Holdout đã `PASS`, tổng thể `PARTIAL` | Bộ notebook hiện hành chạy trực tiếp từ cell, không phụ thuộc helper `.py` trong `M3`; xem Mục 3.28. Các đối chiếu, báo cáo, biểu đồ và phân tích 2024 đạt. Notebook 04 chờ Final sealed; full repository gate còn TIMEOUT. Chưa triển khai M3-B trong phạm vi này. |
| 9 | Final Evaluation — `NOT_READY`, chờ dữ liệu 2026 | Theo thông tin owner ngày 04/11/2026, dữ liệu 2026 chưa đủ; đây chưa phải kết quả audit coverage chi tiết. Chỉ mở lại khi dữ liệu sẵn sàng, qua readiness/evaluation-status audit và khóa exact window trước khi xem performance theo Mục 17.5/Giai đoạn 5 của kế hoạch. Chưa chạy Final, không đổi strategy hoặc chạy lại Dev/Holdout vì thiếu dữ liệu Final. |

Mỗi lần cập nhật báo cáo sau run chính thức cần ghi segment, run ID, Git commit, `config_sha256`, revision dataset, SHA256 đầu vào và đầu ra, kết quả verify cùng đường dẫn artifact đã seal. Bảng Development tại Mục 3.13 và Holdout tại Mục 3.22 được báo cáo riêng, không nối hai NAV. Final Evaluation có gate riêng trong kế hoạch chuẩn.
