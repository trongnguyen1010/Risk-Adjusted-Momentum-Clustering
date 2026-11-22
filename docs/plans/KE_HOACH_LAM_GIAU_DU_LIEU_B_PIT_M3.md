# Kế hoạch làm giàu dữ liệu tài chính, huấn luyện lại B-PIT và backtest M3

**Trạng thái** · Owner đã chốt làm giàu cả 9 chỉ số trong một lượt, gồm mã–năm thiếu một hoặc nhiều chỉ số. Kế hoạch chưa được thực thi.

## 1. Mục tiêu và phạm vi

- Làm giàu **các ô thiếu đầu vào** của 9 chỉ số B-PIT trên FY2017–FY2024, là các năm tài chính xuất hiện trong tập ứng viên M3 gốc. Xử lý chung một bộ dữ liệu, tạo một artifact B-PIT cho thử nghiệm và chạy backtest trên hai đoạn Development, Holdout.
- Điều kiện cho mã–năm gồm doanh nghiệp phi tài chính, có báo cáo năm và có `usable_from_date` hợp lệ tại cutoff B-PIT gốc. Chỉ đưa dòng vào tập fit mới nếu dòng đạt đủ 9/9 sau khi áp dụng quy tắc làm giàu.
- Mỗi ô hợp lệ được điền bằng trung vị của **chính chỉ số đó, trong cùng FY**, từ tập fit gốc đủ 9/9 tại cutoff. Giữ các ô trống theo công thức, gồm CFO/LNST khi LNST không dương và ROE khi vốn chủ sở hữu không đáp ứng điều kiện công thức. Với CFO/LNST chỉ điền khi CFO thiếu và LNST quan sát được, dương.
- Giữ nguyên Model A bundle v4, rule Va của Combined, các strategy đối chứng, cutoff, Q-date, thời hạn báo cáo 18 tháng, xếp hạng, lịch giao dịch, cơ sở giá, chi phí và quy tắc thực thi. F-score và Z-score ngoài 9 chỉ số B-PIT nên không điền. ROE đã điền có thể ảnh hưởng cả phân cụm và chấm điểm tài chính M3.
- FY2016 hết hạn trước kỳ quyết định đầu tiên. FY2025 chưa có mô hình trong artifact gốc. Hai năm này ngoài phạm vi làm giàu của thử nghiệm.

Đối chứng theo hai run đã seal. Development dùng `data/experiments/m3/development/20261104T121107Z-5557288c`. Holdout dùng `data/experiments/m3/holdout/20261104T133507Z-5557288c`. Xem [kế hoạch M3](KE_HOACH_M3_SCHEMA_GITHUB.md), [báo cáo baseline](../reports/REPORT_BACKTEST.md) và [cấu hình baseline](../../configs/experiments/m3_strategy_v1.json).

## 2. Giai đoạn A — Kiểm tra môi trường và xác định phiên bản gốc

1. Chạy từ thư mục gốc repository. Ghi checkout, nhánh, Git HEAD, thay đổi local và đường dẫn Python. Kiểm tra code có B-PIT cutoff, Q17 và cách ly giá theo segment. Baseline được chạy tại commit `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf`. Nếu dùng checkout mới hơn, ghi các khác biệt có thể ảnh hưởng đến phép đối chứng.
2. Ưu tiên venv M3 riêng. Baseline dùng Python **3.12.7**, SQLite **3.45.3**, NumPy **2.2.6**, scikit-learn **1.8.0**. Nếu thiếu venv, lập môi trường thử nghiệm riêng với các phiên bản đó. Lưu phiên bản thực tế và `pip freeze` vào evidence của lượt thực hiện.
3. Kiểm tra dung lượng đĩa theo phần đầu vào còn thiếu. Riêng giá C8 giải nén cần khoảng **4,19 GB**, bên cạnh bản nén, SQLite làm giàu và thư mục kết quả. Kiểm tra Bước B trước khi tải hoặc copy file lớn.
4. Chạy kiểm tra môi trường và bộ test M3 hiện có. So sánh kết quả với lịch sử trong báo cáo baseline.

```powershell
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short
$py = Join-Path $env:LOCALAPPDATA 'DELTA\venvs\m3-py312\Scripts\python.exe'
& $py --version
& $py -m pip check
& $py -c "import sqlite3, numpy, sklearn; print(sqlite3.sqlite_version, numpy.__version__, sklearn.__version__)"
& $py -m unittest discover -s tests/unit -p 'test_m3_*.py'
```

Nếu biến `LOCALAPPDATA` trong sandbox trỏ tới profile riêng, đặt `$py` thành đường dẫn tuyệt đối của venv thực tế. Trên máy baseline là `C:\Users\HP\AppData\Local\DELTA\venvs\m3-py312\Scripts\python.exe`.

**Điều kiện chuyển bước** · Môi trường import thành công, `pip check` sạch, test M3 pass và có đủ dung lượng. Không tiếp tục trên checkout có thay đổi ngoài phạm vi mà chưa xác định được ảnh hưởng.

## 3. Giai đoạn B — Thu thập và xác minh dữ liệu đầu vào

1. Kiểm kê dữ liệu local trước. Ưu tiên dùng lại tệp đúng hash, kể cả tệp nhận từ nhóm. Nguồn Hugging Face là dataset [ngyen/delta-intelligence-data](https://huggingface.co/datasets/ngyen/delta-intelligence-data/tree/08c24867b11177072bfe457a4623a38abf9bbc48), tại revision `08c24867b11177072bfe457a4623a38abf9bbc48`. Bảng dưới lấy đường dẫn từ inventory của revision đã lưu trong staging. Khi thực hiện, kiểm tra quyền truy cập và đường dẫn ở đúng revision trước khi tải, rồi ghi receipt.

| Đầu vào | Đường dẫn tại revision Hugging Face | Đường dẫn local theo contract hiện tại |
|---|---|---|
| Financial indicators gốc | `data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite` | Cùng đường dẫn |
| Financial availability | `m3/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv` | `data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv` |
| Bundle v4 | `data/web/delta-intelligence-v4/terminal.sqlite` | Cùng đường dẫn |
| Giá C8 v2 | `m3/c8/prices_daily.jsonl.gz` | `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/prices_daily.jsonl` |
| Lịch phiên C8 v2 | `m3/c8/trading_calendar.jsonl` | `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/trading_calendar.jsonl` |
| VNINDEX C8 v2 | `m3/c8/benchmark_daily.jsonl` | `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/benchmark_daily.jsonl` |
| B-PIT gốc để xác định đúng tập FIT và đối chứng | Nhận từ bộ baseline đã lưu | `data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec/` |
| Manifest và kết quả baseline | Nhận từ hai run gốc. HF có manifest sáu đầu vào tại `m3/experiments/inputs/manifest.json` | Hai thư mục run ở Mục 1 |

2. Nếu thiếu tệp, tải từng đường dẫn cần dùng vào `.tmp/m3-hf-staging/<revision>/`. Bản ghi lần chạy gốc dùng HF CLI **2.4.0** trong venv tải riêng. Có thể dùng CLI sẵn có sau khi kiểm tra `hf version` và `hf download --help`. Cú pháp dưới đã đối chiếu với CLI **1.9.0** đang có trên máy. Nếu chưa có CLI, có thể cài bản này bằng `python -m pip install "huggingface_hub==1.9.0"` trong venv tải riêng. Ví dụ PowerShell khi thiếu manifest và giá C8 nén:

```powershell
$rev = '08c24867b11177072bfe457a4623a38abf9bbc48'
$staging = Join-Path (Get-Location).Path ".tmp/m3-hf-staging/$rev"
$files = @('m3/experiments/inputs/manifest.json', 'm3/c8/prices_daily.jsonl.gz')
hf download ngyen/delta-intelligence-data @files --repo-type dataset --revision $rev --local-dir $staging
```

   Thay `$files` bằng danh sách tệp thực sự thiếu. Nếu mạng gián đoạn, chạy lại cùng lệnh và staging để dùng lại phần đã tải được theo cơ chế của CLI. Nếu thiếu cả sáu đầu vào, dung lượng tải theo inventory là khoảng **762 MB** trước khi giải nén. Các file giá C8 nén và hai SQLite có metadata LFS/Xet tại revision đã pin.

3. Tải xong, kiểm tra dung lượng bằng `Get-Item -LiteralPath <path>` và hash bằng `Get-FileHash -LiteralPath <path> -Algorithm SHA256`. SHA-256 của giá C8 nén là `32bf8c11b8115ddbb11cfe98c167e9ee820bdcf8257e8f32e8982869247fa9c4`. Giải nén bằng trình hỗ trợ gzip hoặc Python `gzip` đọc theo luồng, xuất `prices_daily.jsonl` vào staging và đối chiếu hash giải nén với manifest M3. Copy từng tệp đã xác minh tới logical path trong bảng nếu thiếu. Nếu path đích đã tồn tại mà hash khác, ghi sai lệch và cô lập bản tải mới để xử lý. Dùng `git check-ignore` cho staging và các đầu ra dữ liệu, kiểm tra `git status` trước khi stage.
4. Kiểm tra các đầu vào đã khớp hash trong manifest Development và Holdout. Với B-PIT gốc, kiểm tra hash `labels.csv`, đọc cùng `models.json`, `audit.json` và `manifest.json` để xác định cutoff và tập `role=FIT`.
5. Chạy `PRAGMA integrity_check` cho hai SQLite. Xác minh bảng `company`, `indicator_values` và các cột `ticker`, `fiscal_year`, `metric`, `value`, `status`, `inputs_json`. Với bundle v4, kiểm tra observations Market A, Financial B dùng đối chiếu ARI trong builder, và bảng giá ngày theo loader hiện hành. Kiểm tra khóa trùng, coverage theo ngày và mã, missingness và trường bắt buộc. Áp dụng đúng Q-date cho CSV, gồm `LAG_RULE` trước FY2022 và `CAFEF_DISCLOSURE` từ FY2022. Với C8, xác minh lịch HOSE, VNINDEX và giá đóng cửa chưa điều chỉnh, trần/sàn tại phiên thực thi của cả hai đoạn. Ghi rõ coverage gap và đối chiếu hành vi fail-closed đã chốt.

**Điều kiện chuyển bước** · Đủ các tệp bắt buộc, hash đúng, schema và readiness pass. Nếu đầu vào chưa đạt, ghi tệp, kiểm tra lỗi và cách khắc phục trước khi tiếp tục.

## 4. Giai đoạn C — Làm giàu cả 9 chỉ số trong một lượt

Các chỉ số gồm `roe`, `roa`, `gross_margin`, `net_margin`, `debt_to_equity`, `current_ratio`, `asset_turnover`, `revenue_growth` và `cfo_to_ni`.

1. Tạo thư mục phiên bản mới tại `data/financial/indicators_enriched_v1/<run_id>/`. Dùng `indicators.sqlite` gốc ở chế độ chỉ đọc để lập inventory theo khóa `ticker, fiscal_year, metric`. Ghi nguyên nhân thiếu từ `status` và `inputs_json`. Với từng mã–năm, đếm số chỉ số quan sát được và số ô dự kiến điền.
2. Xác định nhóm có thể hoàn tất 9/9. Mọi ô thiếu của dòng phải thuộc nhóm `MISSING_INPUT` có thể điền theo Mục 1. Loại dòng thiếu báo cáo năm hoặc có ô trống theo công thức. Đếm đủ cả nhóm thiếu một chỉ số và nhóm thiếu nhiều chỉ số. Thống kê chuẩn bị ghi nhận **1.005 + 40 = 1.045 mã–năm**, tương ứng **1.111 ô** cần điền. Nhóm FY2017–FY2021 có 1.019 dòng, FY2022–FY2024 có 26 dòng. Đối chiếu lại bằng script thực thi. Nếu lệch, ghi nguyên nhân trước khi build.
3. Tính trung vị trên giá trị quan sát **chưa winsorize hoặc chuẩn hóa** từ đúng các mã `FIT` của từng FY trong B-PIT gốc. Đối chiếu số quan sát với `n_fit`. Đóng băng bảng trung vị và lưu số quan sát cho mỗi cặp FY–chỉ số. Các ô được điền trong lượt này nằm ngoài tập dùng để tính trung vị.
4. Tạo SQLite dẫn xuất và điền đúng giá trị tỷ lệ/chỉ số đã tính. Ghi provenance theo từng ô, gồm khóa, trạng thái gốc, lý do thiếu, `usable_from_date`, cutoff, giá trị điền, phương pháp, số quan sát dùng tính trung vị và số ô được điền của mã–năm. Dùng trạng thái nhận diện ô điền, ví dụ `IMPUTED_MEDIAN`. Loader B-PIT thử nghiệm cần đọc trạng thái này theo opt-in rõ ràng vì loader gốc chỉ nhận `OK`.
5. Xuất `indicators.sqlite`, `imputed_cells.csv`, `medians_by_year_metric.csv`, `imputation_summary.csv` và `manifest.json`. Manifest pin commit, hash dữ liệu gốc, availability, tập fit gốc, quy tắc điền, số ô và hash đầu ra. Xác minh integrity, các khóa, số ô thay đổi, dữ liệu FY ngoài phạm vi và giá trị quan sát trong SQLite dẫn xuất. `usable_from_date` giữ nguyên từ availability.

**Điều kiện chuyển bước** · Mọi ô đổi giá trị truy được về rule, cutoff và bảng trung vị. Hồ sơ thiếu nhiều chỉ số ghi rõ số ô điền, tới 6 ô trên một dòng. SHA-256 baseline giữ nguyên.

## 5. Giai đoạn D — Chọn và kiểm định cấu hình phân cụm B-PIT (M2)

**Đầu vào bắt buộc** · Dùng `indicators.sqlite` đã làm giàu từ Giai đoạn C cho mọi lượt fit và kiểm định B-PIT trong thử nghiệm, kể cả đối chứng K-Means k=3. Xác minh đường dẫn, run ID và SHA-256 theo manifest Giai đoạn C trước khi chạy.

1. Khi triển khai D, sao chép [build_financial_pit_clusters.py](../../scripts/build_financial_pit_clusters.py) sang `scripts/build_financial_pit_clusters_enriched.py` làm entry point riêng. Script mới nhận tường minh SQLite chỉ số dẫn xuất, availability, artifact B-PIT gốc, cấu hình thử nghiệm và thư mục đầu ra. Bật opt-in cho `IMPUTED_MEDIAN` tại loader thử nghiệm. Tái sử dụng logic cutoff, T1, audit và xếp hạng cụm hiện có. Giữ builder, pointer, config M3 và artifact baseline ở chế độ chỉ đọc trong lượt thử.
2. Đóng băng tập fit theo từng FY2017–FY2024: dùng cutoff đã lưu trong artifact gốc và tập FIT gốc cộng các mã–năm hoàn tất 9/9 ở Giai đoạn C có `usable_from_date <= cutoff`. Dùng cùng tập fit cho mọi cặp cấu hình trong một FY. Fit T1 (cắt đuôi 1–99% và z-score) và mọi tham số mô hình, kể cả PCA, trên tập đó. Hồ sơ có ngày muộn chỉ được gán bằng mô hình đã đóng băng và chỉ dùng từ `usable_from_date`. Hồ sơ thiếu ngày tiếp tục tuân theo rule loại khỏi tập dùng cho M3. Đối chiếu cutoff trước/sau và giữ kết quả baseline cho các FY ngoài phạm vi.
3. Thử **đồng thời 24 cặp (thuật toán, k)** theo [cấu hình sàng lọc của A](../../configs/experiments/clustering_rework_v2.json): K-Means, PCA + K-Means (giữ 80% phương sai), Ward và GMM, mỗi phương án chạy với `k = 3, 4, 5, 6, 7, 8`. Pin tham số và seed theo cấu hình tham chiếu. Giữ K-Means `k=3`, `n_init=10`, seed `42` trên cùng tập làm giàu để đối chiếu với cấu hình được chọn và với B-PIT gốc. Ghi rõ quy tắc gán sau cutoff: K-Means dùng tâm đã fit trong không gian tương ứng, GMM dùng xác suất hậu nghiệm của mô hình đã fit, Ward gán theo tâm gần nhất của các cụm đã fit trong không gian T1. Thứ tự cụm theo ROE rồi D/E chỉ tính từ thành viên FIT và được lưu cùng mô hình.
4. Chọn một cặp chung cho các FY trong phạm vi. Tập chọn cấu hình phân cụm gồm các FY có cutoff đến hết `2023-12-29` (FY2017–FY2022 theo artifact gốc). Mốc này được đặt trùng ngày kết thúc Development của backtest. Dùng nhãn của tập FIT và đo silhouette, Davies–Bouldin, Calinski–Harabasz trên cùng không gian T1. Tính độ ổn định bằng ARI giữa fit đầy đủ và refit trên mẫu con 90% với các seed đã pin. Tính ARI giữa hai FY liên tiếp trên tập mã FIT chung. Yêu cầu cụm nhỏ nhất chiếm ít nhất 5% ở tối thiểu 80% số FY sàng lọc và ARI trung vị lấy mẫu con đạt ít nhất 0,80. Xếp hạng các cặp đạt theo trung bình hạng của 5 thước đo. Khi hòa, ưu tiên k nhỏ hơn rồi theo thứ tự K-Means, PCA + K-Means, Ward, GMM. Đóng băng cặp đã chọn trước khi kiểm định trên các FY có cutoff sau mốc chọn cấu hình. Lợi suất, Sharpe và kết quả backtest nằm ngoài tiêu chí chọn.
   **Tập kiểm định cấu hình phân cụm B-PIT (M2)** · Dùng FY2023 và FY2024, có cutoff lần lượt là `2024-04-30` và `2025-04-30`. Với cặp thuật toán và k đã chốt, fit T1, mô hình và thứ tự cụm riêng cho từng FY trên tập FIT hợp lệ tại cutoff. Báo cáo chất lượng và độ ổn định của cụm trên các FY này riêng với kết quả chọn cấu hình. Giữ cố định thuật toán và k sau kiểm định.

5. Lưu cấu hình, cohort và cutoff theo FY, kết quả từng cặp theo FY, bảng tổng hợp 24 cặp, lý do loại và quyết định chọn vào thư mục run riêng. Artifact chuyển cho M3 tại `data/financial/b_pit_enriched_v1/<run_id>/` gồm `labels.csv`, `models.json`, `audit.json` và `manifest.json`. Manifest pin chỉ số dẫn xuất, availability, artifact cha, code, cấu hình và hash đầu ra. Lưu tham số mô hình theo thuật toán và thống kê số fit trước/sau, phân bố cụm, tỷ lệ mã đổi nhãn sau khi đối sánh nhãn, ARI trên tập mã chung với baseline và với đối chứng K-Means k=3.
6. Kiểm tra loader opt-in, việc tái lập baseline, tập FIT, cutoff, gán sau cutoff, FY ngoài phạm vi và cách ly tập chọn cấu hình khỏi tập kiểm định phân cụm. Kiểm tra loader M3 đọc được nhãn và thứ tự đủ k cụm, đồng thời ghi số mã qua rule Va `not_weakest` theo FY trước khi chuyển bước. Chạy targeted tests của B-PIT và M3, `python -m compileall -q src tests scripts run.py` và synthetic smoke theo `configs/data/synthetic_smoke.example.json` nếu có thay đổi pipeline.

**Điều kiện chuyển bước** · `fit_leaks` rỗng, tập FIT và cutoff khớp evidence, đầu ra truy xuất được từ manifest, kiểm tra tương thích với M3 đạt. Ghi `MANUAL_REVIEW_REQUIRED` và trình owner bảng xếp hạng cùng tác động của cấu hình đề xuất lên rule Va trước khi pin cho Giai đoạn E. Nếu không cặp nào đạt, báo rõ kết quả và trình đối chứng K-Means k=3 để owner quyết định bước tiếp theo.

## 6. Giai đoạn E — Backtest M3 với B-PIT đã làm giàu

**Đầu vào bắt buộc** · Mọi lượt kiểm tra và backtest thử nghiệm ở cả Development và Holdout phải dùng cùng SQLite chỉ số đã làm giàu từ Giai đoạn C và artifact B-PIT được build từ SQLite đó ở Giai đoạn D. Dùng đường dẫn SQLite đã pin cho chấm điểm, đọc dữ liệu ngành và ghi hash đầu vào. Xác minh `indicators_sha256` và `b_pit_labels_sha256` trong manifest từng run khớp các artifact đã bàn giao. Dừng nếu runner còn đọc SQLite mặc định hoặc nếu hash không khớp.

Bắt đầu khi các Giai đoạn A–D đã đạt điều kiện bàn giao và owner đã duyệt cấu hình phân cụm. M3 đọc nhãn đã build và áp dụng cutoff cùng `usable_from_date` tại từng ngày quyết định. Trình tự dưới đây dựa trên Bước 2–5 của [hướng dẫn M3 Readiness](../../M3/M3_READINESS.md#bước-2--pin-b-pit-vào-config).

1. **Pin đầu vào vào config thử nghiệm.** Tạo `configs/experiments/m3_strategy_enriched_v1.json` từ config baseline, đặt trạng thái `READY_TO_LOCK_AFTER_BPIT`. Pin đường dẫn B-PIT, SHA-256 của `labels.csv` và `models.json`, cùng đường dẫn và SHA-256 của SQLite chỉ số đã làm giàu. Runner và công cụ feasibility phải đọc cùng config, kể cả chỉ số dùng cho scoring, dữ liệu ngành và hash trong manifest. Dùng cache giá trần/sàn riêng. Hoàn tất phần tích hợp này trước khi chạy vì `m3_feasibility_variants.py` hiện đọc config baseline cố định và `run_m3.py` vẫn lấy chỉ số từ đường dẫn mặc định.

2. **Chạy feasibility trước khi tính lợi suất.** Dùng `scripts/m3_feasibility_variants.py` với config thử nghiệm sau khi script hỗ trợ `--config`. Với cả hai đoạn, ghi trung vị và số ứng viên thấp nhất, số kỳ dưới `N_min=10`, cùng tỷ lệ loại theo lý do. Dùng kết quả `official config (after FINANCIAL_CRITERIA_MISSING)` để đối chiếu baseline. Nếu số kỳ dưới ngưỡng tăng rõ, trình owner xem xét trước khi chạy full backtest.

3. **Chạy và xác minh `targets-only` cho cả hai đoạn.** Kiểm tra manifest ghi `financial_source=B_PIT`, hash khớp config và `git_dirty=false`. Development phải có **60 quyết định / 59 kỳ thực thi theo lịch / 1 kỳ cuối không thực thi**. Holdout phải có **24 / 23 / 1**. Theo từng kỳ và từng strategy, đối chiếu số ứng viên giữa `universe_audit_*.csv` và `targets_*.csv`, kiểm tra cutoff, lý do loại và tổng tỷ trọng mục tiêu khi có phân bổ. `targets-only` không tính lợi suất và có thể ghi `c8_prices_sha256=null` theo contract của runner.

   ```powershell
   $cfg = 'configs/experiments/m3_strategy_enriched_v1.json'
   & $py scripts/run_m3.py --config $cfg --segment development --targets-only
   & $py scripts/run_m3.py --config $cfg --segment holdout --targets-only
   ```

4. **Kiểm tra ranh giới giá và khóa config.** Sau khi cả hai lượt `targets-only` đạt, kiểm tra Q17 và cách ly giá theo segment, gồm cả các phiên liền kề dùng để kiểm tra giá. Chuyển config sang `LOCKED`, commit code và config, ghi Git commit, `config_sha256` và hash đầu vào. Full run phải ghi đủ SHA-256 của giá C8.

5. **Chạy Development → kiểm tra → seal.** Chạy đoạn **31/01/2019–29/12/2023**:

   ```powershell
   & $py scripts/run_m3.py --config $cfg --segment development
   ```

   Đối chiếu targets và universe audit với lượt `targets-only`. Kiểm tra `trade_ledger`, dòng tiền, holdings, NAV và metrics. NAV phải kết thúc đúng ngày `2023-12-29`. Rà các kỳ `UNIVERSE_TOO_SMALL` và các lệnh `LIMIT_DATA_MISSING`. Xác minh VNINDEX và ba strategy Market-only, Equal-weight, Momentum-only khớp baseline theo dữ liệu nghiệp vụ. Khi kiểm tra đạt, lưu `seal.json` riêng cùng trạng thái `PASS`, run ID và SHA-256 của manifest, đầu vào, đầu ra. [Ví dụ verify và seal Development](../reports/REPORT_BACKTEST.md#321-development-chạy-lại-sau-sửa-q17-verify-và-seal-pass)

6. **Chạy Holdout → kiểm tra → seal.** Sau khi Development đã seal, chạy đoạn **31/01/2024–31/12/2025** bằng đúng commit, config và bộ đầu vào đã khóa:

   ```powershell
   & $py scripts/run_m3.py --config $cfg --segment holdout
   ```

   Lặp lại các kiểm tra của Development và đối chiếu hash với seal Development. Holdout khởi tạo danh mục và NAV riêng, kết thúc NAV ngày `2025-12-31`. Ghi số kỳ dưới `N_min` cùng kết quả từng đoạn. Giữ hai chuỗi NAV riêng và chỉ báo cáo Sharpe ở Final nếu đủ điều kiện. [Ví dụ verify và seal Holdout](../reports/REPORT_BACKTEST.md#322-holdout-chính-thức-verify-và-seal-pass)

**Điều kiện bàn giao sang Giai đoạn F** · Cả hai full run có run ID, manifest và seal riêng. Các kiểm tra trên targets, giao dịch, NAV, ranh giới giá và đối chứng đều đạt. Nếu có sai lệch, ghi rõ bằng chứng và xử lý trước khi chuyển bước.

## 7. Giai đoạn F — Đối sánh và bàn giao

**Đầu vào bắt buộc** · Lập báo cáo thử nghiệm từ dữ liệu chỉ số đã làm giàu ở Giai đoạn C, artifact B-PIT ở Giai đoạn D và các run Development/Holdout ở Giai đoạn E đã xác minh dùng đúng hai artifact đó. Đối chiếu run ID và SHA-256 qua các manifest trước khi tổng hợp. Kết quả gốc được đọc làm baseline đối sánh.

- Với B-PIT, báo cáo số ô điền theo FY và chỉ số, số mã–năm theo số ô điền, độ phủ 9/9, số mã fit, phân bố cụm và thay đổi nhãn trên tập chung.
- Với M3, đối chiếu Combined và Financial-only với baseline theo từng đoạn. Ghi số ứng viên, kỳ thiếu ứng viên, số mã chọn/thực giữ, lệnh thất bại, tiền mặt, NAV, lợi suất và drawdown. Giữ đủ số liệu của các strategy đối chứng. VNINDEX là price index, còn NAV strategy dùng giá điều chỉnh của nhà cung cấp. Khi trình bày chênh lệch, ghi rõ cơ sở giá của hai chuỗi.
- Trình bày tác động chung của một lượt làm giàu. Bảng phân bố theo số ô điền cho biết mức độ sử dụng trung vị. Chênh lệch có thể đến từ tập fit mở rộng, mô hình được fit lại và ROE dùng cho scoring.
- Ghi kết quả và việc còn lại vào mục **4. Công việc còn lại và gate chuyển bước** của [REPORT_BACKTEST.md](../reports/REPORT_BACKTEST.md). Kiểm tra bản Downloads và worktree trước khi đồng bộ. Cập nhật [DECISIONS.md](../DECISIONS.md), [CHANGELOG.md](../../CHANGELOG.md), config và tests khi triển khai quy tắc mới. Giữ nguyên `docs/M3_READINESS.md`.
- Bàn giao đường dẫn config, commit, hash và run ID của bản chỉ số đã làm giàu, B-PIT và hai run M3. Lưu báo cáo phase `PASS`, `PARTIAL`, `BLOCKED` hoặc `FAIL` cùng evidence và hành động còn lại. Đánh giá kết quả thử nghiệm với owner trước khi cân nhắc cập nhật phiên bản chính thức.
