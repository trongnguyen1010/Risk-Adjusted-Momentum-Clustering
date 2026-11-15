# Kế hoạch làm giàu dữ liệu tài chính, huấn luyện lại B-PIT và backtest M3

**Trạng thái** · Owner đã chốt làm giàu cả 9 chỉ số trong một lượt, gồm mã–năm thiếu một hoặc nhiều chỉ số. Kế hoạch chưa được thực thi.

## 1. Mục tiêu và phạm vi

- Làm giàu **các ô thiếu đầu vào** của 9 chỉ số B-PIT trên FY2017–FY2024, là các năm tài chính xuất hiện trong tập ứng viên M3 gốc. Xử lý chung một bộ dữ liệu, tạo một artifact B-PIT cho thử nghiệm và chạy backtest trên hai đoạn Development, Holdout.
- Điều kiện cho mã–năm gồm doanh nghiệp phi tài chính, có báo cáo năm và có `usable_from_date` hợp lệ tại cutoff B-PIT gốc. Chỉ đưa dòng vào tập fit mới nếu dòng đạt đủ 9/9 sau khi áp dụng quy tắc làm giàu.
- Mỗi ô hợp lệ được điền bằng trung vị của **chính chỉ số đó, trong cùng FY**, từ tập fit gốc đủ 9/9 tại cutoff. Giữ các ô trống theo công thức, gồm CFO/LNST khi LNST không dương và ROE khi vốn chủ sở hữu không đáp ứng điều kiện công thức. Với CFO/LNST chỉ điền khi CFO thiếu và LNST quan sát được, dương.
- Giữ nguyên Model A bundle v4, rule Va của Combined, các strategy đối chứng, cutoff, Q-date, thời hạn báo cáo 18 tháng, xếp hạng, lịch giao dịch, cơ sở giá, chi phí và quy tắc thực thi. F-score và Z-score ngoài 9 chỉ số B-PIT nên không điền. ROE đã điền có thể ảnh hưởng cả phân cụm và chấm điểm tài chính M3.
- FY2016 hết hạn trước kỳ quyết định đầu tiên. FY2025 chưa có mô hình trong artifact gốc. Hai năm này ngoài phạm vi làm giàu của thử nghiệm.

Đối chứng theo hai run đã seal. Development dùng `data/experiments/m3/development/20261104T121107Z-5557288c`. Holdout dùng `data/experiments/m3/holdout/20261104T133507Z-5557288c`. Xem [kế hoạch M3](KE_HOACH_M3_SCHEMA_GITHUB.md), [báo cáo baseline](REPORT_BACKTEST.md) và [cấu hình baseline](../configs/experiments/m3_strategy_v1.json).

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

## 5. Giai đoạn D — Build B-PIT phiên bản thử nghiệm

1. Dùng builder [build_financial_pit_clusters.py](../scripts/build_financial_pit_clusters.py) làm entry point. Builder hiện đọc pointer `configs/product/indicators_v1.json`. Thêm đầu vào tường minh cho pointer/dữ liệu và thư mục artifact thử nghiệm ở lượt triển khai, với mặc định cũ cho các lệnh hiện hành. Giữ pointer gốc.
2. Fit lại T1 và K-Means `k=3`, `n_init=10`, seed `42` theo từng FY, trên tập fit gốc cộng nhóm hoàn tất 9/9 tại cutoff. Tính thứ tự cụm theo đúng rule baseline. Với FY ngoài phạm vi, giữ hành vi và kết quả mô hình gốc. Đối chiếu cutoff trước/sau. Nếu việc mở rộng tập khiến builder tính ra cutoff khác baseline, dừng để xác định nguyên nhân và áp dụng đúng cutoff đã chốt.
3. Lưu `labels.csv`, `models.json`, `audit.json`, `manifest.json` tại `data/financial/b_pit_enriched_v1/<run_id>/`. Manifest liên kết bản chỉ số dẫn xuất, availability, artifact cha và hash đầu ra. Thống kê số fit trước/sau, phân bố cụm, số mã cũ đổi nhãn và độ tương đồng trên tập mã chung bằng ARI.
4. Chạy test của loader, B-PIT và M3, gồm trường hợp opt-in, dữ liệu gốc, cutoff và FY ngoài phạm vi. Chạy `python -m compileall -q src tests scripts run.py` và synthetic smoke theo `configs/data/synthetic_smoke.example.json` nếu có thay đổi pipeline.

**Điều kiện chuyển bước** · `fit_leaks` rỗng, mỗi FY có group thêm vào fit đúng theo dữ liệu đã xác minh, cutoff và thứ tự cụm có đủ evidence, đầu ra truy xuất được từ manifest.

## 6. Giai đoạn E — Backtest M3 với phiên bản mới

1. Tạo file cấu hình mới, ví dụ `configs/experiments/m3_strategy_enriched_v1.json`, dựa trên config baseline. Pin path, SHA-256 nhãn và xác minh hash `models.json` của B-PIT mới. Runner hiện cho chọn `--config` nhưng vẫn dùng đường dẫn Indicators v1 mặc định và cache giá trần/sàn dùng chung. Khi tích hợp, bổ sung tùy chọn đường dẫn chỉ số, hash và cache riêng cho thử nghiệm. Truyền cùng đường dẫn chỉ số cho phần đọc scoring, sectors và ghi input hash. Giữ cấu hình và cache baseline nguyên vẹn. Thư mục run mới theo từng segment có run ID riêng.
2. Chạy thử `targets-only` cho cả hai đoạn với config mới để xác nhận nguồn là `B_PIT`, hash đầu vào khớp, cutoff hoạt động và lịch quyết định đúng. Chạy test cách ly giá và Q17. Khi readiness đạt, khóa code, config và dữ liệu của thử nghiệm trước full Development.
3. Chạy Development trước và seal artifact. Sau đó chạy Holdout với cùng code, config, bảng trung vị và B-PIT. Dùng đầy đủ SHA-256 C8 ở full run. Lệnh dự kiến sau khi tích hợp các đầu vào mới:

```powershell
$cfg = 'configs/experiments/m3_strategy_enriched_v1.json'
& $py scripts/run_m3.py --config $cfg --segment development --targets-only
& $py scripts/run_m3.py --config $cfg --segment holdout --targets-only
# Sau khi kiểm tra readiness và khóa config
& $py scripts/run_m3.py --config $cfg --segment development
# Sau khi kiểm tra và seal Development
& $py scripts/run_m3.py --config $cfg --segment holdout
```

4. Đối chiếu 60 kỳ quyết định/59 kỳ thực thi của Development và 24/23 của Holdout. Kỳ cuối mỗi đoạn không thực thi. Kiểm tra không đọc giá sau biên segment, manifest ghi đúng hash chỉ số mới, availability và dữ liệu giá khớp baseline. Benchmark và ba strategy Market-only, Equal-weight, Momentum-only phải khớp baseline theo dữ liệu nghiệp vụ. Điều tra sai khác trước khi tiếp tục.

**Điều kiện chuyển bước** · Hai manifest và thư mục kết quả riêng đầy đủ. Kiểm tra hash và hành vi kiểm soát đạt. Các artefact gốc giữ nguyên.

## 7. Giai đoạn F — Đối sánh và bàn giao

- Với B-PIT, báo cáo số ô điền theo FY và chỉ số, số mã–năm theo số ô điền, độ phủ 9/9, số mã fit, phân bố cụm và thay đổi nhãn trên tập chung.
- Với M3, đối chiếu Combined và Financial-only với baseline theo từng đoạn. Ghi số ứng viên, kỳ thiếu ứng viên, số mã chọn/thực giữ, lệnh thất bại, tiền mặt, NAV, lợi suất và drawdown. Giữ đủ số liệu của các strategy đối chứng. VNINDEX là price index, còn NAV strategy dùng giá điều chỉnh của nhà cung cấp. Khi trình bày chênh lệch, ghi rõ cơ sở giá của hai chuỗi.
- Trình bày tác động chung của một lượt làm giàu. Bảng phân bố theo số ô điền cho biết mức độ sử dụng trung vị. Chênh lệch có thể đến từ tập fit mở rộng, mô hình được fit lại và ROE dùng cho scoring.
- Ghi kết quả và việc còn lại vào mục **4. Công việc còn lại và gate chuyển bước** của [REPORT_BACKTEST.md](REPORT_BACKTEST.md). Kiểm tra bản Downloads và worktree trước khi đồng bộ. Cập nhật [DECISIONS.md](DECISIONS.md), [CHANGELOG.md](../CHANGELOG.md), config và tests khi triển khai quy tắc mới. Giữ nguyên `docs/M3_READINESS.md`.
- Bàn giao đường dẫn config, commit, hash và run ID của bản chỉ số đã làm giàu, B-PIT và hai run M3. Lưu báo cáo phase `PASS`, `PARTIAL`, `BLOCKED` hoặc `FAIL` cùng evidence và hành động còn lại. Đánh giá kết quả thử nghiệm với owner trước khi cân nhắc cập nhật phiên bản chính thức.
