# Tài liệu hướng dẫn vận hành và bàn giao dự án DELTA

**Dự án:** Phân cụm động lượng điều chỉnh rủi ro TTCK Việt Nam  
**Phạm vi:** M2 thị trường, M2 tài chính, M3 backtest và web DELTA Intelligence  
**Đối tượng sử dụng:** Người tiếp nhận kỹ thuật, nhóm nghiên cứu và đơn vị vận hành  
**Phiên bản tài liệu:** 1.0  
**Ngày cập nhật:** 22/11/2026

## Mục đích và cách dùng tài liệu

Tài liệu này giúp người nhận bàn giao định vị mã nguồn, giải nén dữ liệu vào đúng cấu trúc, hiểu luồng từ M2 đến M3 và khởi động ứng dụng web. Hãy bắt đầu từ mục trạng thái và checklist bàn giao, sau đó làm theo hướng dẫn từng nhánh. Đường dẫn tương đối được tính từ repository root `Risk-Adjusted-Momentum-Clustering`.

Tài liệu phản ánh cấu trúc repository và các trạng thái đã ghi trong tài liệu dự án tại thời điểm cập nhật. Trước khi chạy lại một pipeline, người tiếp nhận cần đối chiếu manifest, hash nguồn và trạng thái trong README/runbook tương ứng. Mọi dữ liệu lớn có thể nằm ngoài Git; bản clone đơn lẻ không đồng nghĩa đã có dữ liệu cần thiết.

## Tóm tắt bàn giao

| Thành phần | Vai trò | Trạng thái trong repository |
|---|---|---|
| M2 thị trường A | Phân cụm cổ phiếu theo đặc trưng thị trường | Baseline A có trong bundle v4; các notebook/thí nghiệm M2 cũ giữ làm hồ sơ và đối chứng |
| M2 tài chính B | Phân cụm theo đặc trưng tài chính theo năm | Baseline B có trong bundle; dữ liệu financial-full10 và B-PIT là các nhánh riêng, phải phân biệt ex-post với PIT |
| M3 | Tạo danh mục và backtest theo segment | Development và Holdout đã có run được verify/seal; Final Evaluation chưa sẵn sàng do thiếu dữ liệu 2026 |
| Web DELTA | Tra cứu/read-only presentation cho kết quả nghiên cứu | Next.js + FastAPI; cần presentation bundle SQLite local và đúng hash |

Kết quả phân cụm không tự thân là khuyến nghị giao dịch. Các báo cáo hiện có cũng ghi rõ những giới hạn về point-in-time, chất lượng cụm, availability và độ bao phủ dữ liệu. Không diễn giải trạng thái `PARTIAL`, `REVIEW_REQUIRED` hoặc `NOT_READY` thành nghiệm thu hoàn tất.

## Checklist nghiệm thu khi nhận dự án

- [ ] Repository mở được và có đúng nhánh/commit bàn giao; lưu lại `git status` và `git rev-parse HEAD`.
- [ ] Archive dữ liệu được giải nén vào đúng repository root; không phát sinh thêm tầng `data/data` hoặc thư mục ZIP lồng ngoài dự kiến.
- [ ] Có đủ SQLite/CSV/JSONL được pin bởi config và manifest; hash kiểm tra khớp.
- [ ] Có thể mở các báo cáo M2/M3 đã công bố mà không cần chạy lại model/backtest.
- [ ] Backend và frontend web khởi động trên máy bàn giao; API health/catalog và trang chính truy cập được.
- [ ] Người nhận hiểu dữ liệu nào là baseline ex-post, dữ liệu nào là PIT và kết quả nào còn partial.
- [ ] Đã thống nhất nơi lưu dữ liệu cục bộ, quyền truy cập, sao lưu, người phụ trách và quy trình cập nhật.

Mục checklist này là các bước cần xác nhận trong buổi bàn giao, không phải khẳng định tất cả đã được nghiệm thu.

## Quy trình chuẩn bị môi trường mới

1. Clone repository hoặc nhận đúng gói source code đã bàn giao. Ghi lại branch và commit.
2. Giải nén data bundle theo mục 1 bên dưới. Không đưa dữ liệu lớn vào Git nếu `.gitignore` đang loại trừ chúng.
3. Đọc `docs/README.md`, `docs/CURRENT_STATUS.md`, `docs/PROJECT_MAP.md` và hướng dẫn cụ thể của M3/web.
4. Kiểm tra phiên bản Python/Node theo README. Cài dependencies trong môi trường ảo riêng; không cài lẫn vào Python toàn máy.
5. Xác minh input paths, manifest, hash và trạng thái config trước khi chạy.
6. Đọc đầu ra đã seal trước. Chỉ chạy pipeline tạo dữ liệu hoặc backtest mới khi đã có yêu cầu và dữ liệu đúng phiên bản.
7. Chạy web, ghi nhận kết quả kiểm tra, lỗi còn lại và thông tin bàn giao cho người nhận.

---
Tài liệu này hướng dẫn mở bộ dữ liệu đã giải nén, nhận biết cấu trúc thư mục, phân biệt hai nhánh M2 (thị trường và tài chính), theo dõi luồng M3 và chạy giao diện web DELTA Intelligence. Các đường dẫn dưới đây tính từ thư mục gốc repository `Risk-Adjusted-Momentum-Clustering`. Các bundle dữ liệu lớn thường không nằm trong Git; vì vậy cần giải nén đúng chỗ và giữ nguyên cấu trúc thư mục tương đối.

> **Trạng thái cần nhớ:** M2 có cả bộ notebook/thí nghiệm cũ và baseline A/B hiện hành được đóng gói trong bundle v4. M3 Development và Holdout đã có kết quả được seal; cấu hình chiến lược đang LOCKED. Không chạy lại backtest chính thức chỉ để xem kết quả. Giao diện web hiện hành là Next.js + FastAPI, đọc bundle trình bày dạng SQLite; dashboard Streamlit cũ không thuộc luồng web hiện hành.

## 1. Giải nén dữ liệu và mở đúng thư mục dự án

1. Tải file ZIP dữ liệu/bàn giao (ví dụ `DELTA_02_ACTIVE_M2_M3.zip`) về máy. Không giải nén chồng vào một thư mục dự án khác đang dùng.
2. Mở PowerShell và chuyển đến nơi đã clone/giải nén repository. Ví dụ:

```powershell
cd "D:\DuAn\Risk-Adjusted-Momentum-Clustering"
```

3. Giải nén archive vào thư mục gốc repository, trừ khi README của archive chỉ định thư mục đích khác:

```powershell
Expand-Archive -LiteralPath "D:\TaiVe\DELTA_02_ACTIVE_M2_M3.zip" `
  -DestinationPath "D:\DuAn\Risk-Adjusted-Momentum-Clustering" -Force
```

4. Nếu archive chứa một thư mục `data` ở cấp đầu tiên, kiểm tra sau giải nén phải thành `...Risk-Adjusted-Momentum-Clustering\data\...`, không phải `...\Risk-Adjusted-Momentum-Clustering\DELTA_02_ACTIVE_M2_M3\data\...` hoặc `...\data\data\...`. Không đổi tên các thư mục con có version/hash.
5. Hiển thị cây thư mục:

```powershell
# Cây gọn để xem các thư mục cấp dữ liệu
 tree data /A

# Liệt kê cả tệp và thư mục, dùng khi cần kiểm tra một nhánh cụ thể
 Get-ChildItem .\data -Recurse -Force | Select-Object FullName,Length
```

`tree data /A` chỉ hiển thị tên thư mục. Muốn kiểm tra file, dùng lệnh thứ hai. Các thư mục `data` và một số SQLite/CSV có thể bị Git bỏ qua có chủ đích; clone repository mà chưa có bundle dữ liệu không có nghĩa là dữ liệu đã được cài.

### Cây dữ liệu chính liên quan M2, M3 và web

Cây sau là sơ đồ những nhánh cần cho quy trình này, không phải mọi tệp phát sinh của từng lần chạy:

```text
data/
├── web/
│   ├── delta-intelligence-v4/
│   │   └── terminal.sqlite                  # Bundle A/B và dữ liệu trình bày phiên bản v4
│   └── delta-intelligence-v1/               # Bundle web local khác; kiểm tra cấu hình trước khi dùng
├── financial/
│   ├── indicators_v1/results/indicators-<hash>/
│   │   └── indicators.sqlite                # Chỉ báo đã build/pin, dùng bởi M3 và API
│   ├── disclosure_dates_v1/availability-<hash>/
│   │   └── availability.csv                 # Ngày công bố/khả dụng của BCTC
│   ├── b_pit_v1/bpit-<hash>/
│   │   ├── labels.csv                       # Nhãn cụm B theo thời điểm khả dụng
│   │   ├── models.json                      # Model/thứ tự cụm theo năm
│   │   ├── audit.json                       # Kiểm tra cutoff và đối chiếu
│   │   └── manifest.json                    # Hash và thông tin nguồn
│   └── financial_full10_baseline_v1/        # Nhánh baseline tài chính lịch sử
├── experiments/
│   └── m3/
│       ├── development/<run_id>/            # Kết quả lần chạy Development
│       └── holdout/<run_id>/                # Kết quả lần chạy Holdout
└── [nguồn giá/availability bổ sung theo bundle]
```

`<hash>` và `<run_id>` là tên thư mục cụ thể được sinh/pin trong cấu hình hoặc manifest. Không tự thay chúng bằng tên ví dụ. Nếu archive có các nhánh `data/web/delta-intelligence-v4`, `data/financial/indicators_v1`, `data/financial/disclosure_dates_v1` và nguồn C8 tương ứng thì đặt nguyên đường dẫn như trên; thiếu một nguồn sẽ khiến script dừng thay vì tự tạo dữ liệu giả.

## 2. Bản đồ thư mục repository

```text
Risk-Adjusted-Momentum-Clustering/
├── M2/
│   ├── notebooks/       # Notebook thí nghiệm/đánh giá M2 đời trước
│   ├── artifacts/       # Kết quả model, handoff, holdout và kiểm chứng
│   ├── models/          # Model đã lưu theo các phương pháp/thời kỳ
│   └── reports/         # Báo cáo theo nhiệm vụ M2
├── M3/
│   ├── notebooks/       # Notebook 01–05 về dữ liệu, danh mục, backtest, B-PIT
│   ├── outputs/         # CSV canonical Development/Holdout đã công bố và seal
│   ├── reports/         # Báo cáo kỹ thuật M3
│   └── presentation/    # Tài liệu trình bày
├── configs/experiments/ # Cấu hình M2/M3 đã version hóa
├── data/                # Dữ liệu thực; thường không được commit lên Git
├── src/delta_t1/        # Module clustering, feature, ingestion và M3 engine
├── scripts/             # Runner, build, export, verify và khởi động web
├── artifacts/           # Manifest, báo cáo, kết quả nghiên cứu đã pin
├── docs/                # Quyết định, trạng thái, phương pháp, runbook
└── web/
    ├── frontend/        # Next.js UI
    ├── backend/app/     # FastAPI chỉ đọc và API
    └── monitor/         # Trang monitor tĩnh riêng
```

- `configs/experiments`: tham số và đường dẫn nguồn có kiểm soát; trước khi chạy luôn đọc file cấu hình tương ứng.
- `src/delta_t1`: logic có thể tái sử dụng; runner trong `scripts/` gọi các module tại đây.
- `scripts/`: các lệnh điều phối. Tên script có chữ `verify`, `export`, `build`, `run` có vai trò khác nhau; verify thường kiểm tra artifact, không fit lại model.
- `artifacts/` và `M2/`, `M3/`: kết quả/biên bản đã tạo. Không coi mọi thư mục ở đây là input mới nhất; kiểm tra manifest, README và ngày trạng thái trước.

## 3. M2 nhánh thị trường

### Mục tiêu và đầu vào

Nhánh thị trường tạo model A: phân cụm chéo các cổ phiếu tại từng snapshot theo đặc trưng giá/thanh khoản. Mô tả hiện hành trong `docs/CURRENT_STATUS.md` xác định model A bundle v4, 9 đặc trưng, lọc thanh khoản thấp, biến đổi log/winsorize/z-score và K-Means k=3. Đây là baseline thị trường riêng; không trộn dữ liệu tài chính vào phép fit của A.

Input chính của bundle M2/M3 là:

- `data/web/delta-intelligence-v4/terminal.sqlite`, bảng `observations`, các dòng `kind='market'` gồm ngày snapshot, ticker, cluster, đặc trưng và liquidity.
- Nguồn giá/thị trường C8 V2 tại `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/` (benchmark, calendar, prices) phục vụ M3; không nhầm nguồn này với file `terminal.sqlite`.
- Với thí nghiệm M2-PREP/runner development: `configs/experiments/m2_market_only_v2.json` và dữ liệu C8 tương ứng. `scripts/run_m2_global_k.py` là runner chọn K theo development; nó không phải lệnh để chạy lại baseline model A trong bundle v4.

### Mã nguồn/điểm đọc

- `src/delta_t1/clustering/`, `src/delta_t1/features/`, `src/delta_t1/experiments/`: xử lý đặc trưng, tiền xử lý snapshot và clustering.
- `scripts/run_m2_global_k.py`: thí nghiệm chọn K development theo config; sinh bằng chứng ứng viên, không chạy holdout/backtest.
- `scripts/run_clustering_rework_v2.py`: luồng rework lịch sử giúp chọn lại cấu hình A; đọc `artifacts/reports/m2-vs-rework-v1/report.md` để hiểu kết quả đã duyệt.
- Các notebook M2 trong `M2/notebooks/` và báo cáo trong `M2/reports/` chủ yếu là hồ sơ nghiên cứu/bàn giao trước đó. Theo trạng thái hiện hành, một số bàn giao M2 K=2 và notebook cũ là LEGACY; dùng để đối chứng/tái lập lịch sử, không dùng làm đầu vào mặc định cho công việc mới.

### Đầu ra và cách kiểm tra

- Baseline A đã đóng gói: nhãn/đặc trưng market trong `data/web/delta-intelligence-v4/terminal.sqlite`.
- Hồ sơ M2/kiểm chứng nằm trong `M2/artifacts/`, `M2/reports/` và `artifacts/reports/m2-vs-rework-v1/`.
- Xem manifest/config và báo cáo để kiểm tra số snapshot, số mã đủ điều kiện, cấu hình K và hash. Tránh suy ra rằng K=2 trong handoff cũ là cấu hình hiện hành; hướng chính thức được ghi là K=3.

## 4. M2 nhánh tài chính

### Mục tiêu và đầu vào

Nhánh tài chính tạo model B, độc lập với model A, dựa trên đặc trưng cơ bản doanh nghiệp theo năm tài chính. Bundle v4 lưu các quan sát `kind='financial'` trong `terminal.sqlite`; chỉ báo chuẩn hóa và dữ liệu B-PIT nằm trong các nhánh riêng dưới `data/financial/`.

Input chính:

- `data/web/delta-intelligence-v4/terminal.sqlite`: nhãn/đặc trưng tài chính model B theo năm trong phiên bản bundle v4.
- `data/financial/indicators_v1/results/indicators-<hash>/indicators.sqlite`: chỉ báo và metadata doanh nghiệp; hash chính xác được pin trong module/config.
- `data/financial/disclosure_dates_v1/availability-<hash>/availability.csv`: ngày khả dụng/công bố phục vụ kiểm soát thời điểm.
- Bộ dữ liệu gốc cho baseline financial-full10 cần xem handoff trong `data/handoffs/financial-reference-2016-2025/README.md`; đừng mặc định thư mục đó có sẵn sau khi clone.

### Mã nguồn/điểm đọc

- `scripts/financial_full10_baseline.ps1` là wrapper trạng thái/kiểm tra/chạy baseline tài chính lịch sử: `-Mode Status`, `-Mode Check`, `-Mode Run`.
- `scripts/financial_full10_baseline.py` triển khai baseline; `scripts/financial_full10_review.py` đọc lại/đối chiếu baseline mà không refit.
- `scripts/build_financial_pit_clusters.py` tạo nhãn B-PIT từ chỉ báo đã pin, có cutoff theo thời điểm công bố. Đây là bước xây dựng nguồn M3, khác baseline B v4 kiểu ex-post.
- `src/delta_t1/m3/bpit.py` và `src/delta_t1/m3/inputs.py` chứa logic đọc/tạo B-PIT và input.

### Đầu ra và cách phân biệt

- Baseline tài chính: `data/financial/financial_full10_baseline_v1/` và báo cáo tổng ở `artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md`.
- B-PIT: `data/financial/b_pit_v1/bpit-<hash>/labels.csv`, `models.json`, `audit.json`, `manifest.json`.
- Nhãn B v4 trong bundle không tự động là nhãn PIT. Khi M3 chạy chính thức, config phải pin artifact B-PIT và hash `labels.csv`; không được thay bằng B v4 chỉ để chạy được.
- Báo cáo trạng thái ghi rõ baseline B có giới hạn ổn định và cần diễn giải thận trọng. Nhãn cụm mô tả nhóm tương đồng, không phải khuyến nghị mua/bán.

## 5. M3 từ chuẩn bị đến kết quả

### M3 dùng gì và làm gì

M3 dùng kết quả A thị trường, nhãn B-PIT theo thời điểm công bố, Indicators v1, ngày khả dụng, giá/calendar C8 và cấu hình chiến lược đã khóa để kiểm tra chiến lược danh mục theo thời gian. M3 không quay lại chọn K, scaler hay đặc trưng phân cụm bằng lợi suất.

Runner lấy các input sau (đường dẫn mặc định trong `src/delta_t1/m3/inputs.py`):

- `data/web/delta-intelligence-v4/terminal.sqlite` (A/B tham chiếu bundle).
- `data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite`.
- `data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv`.
- `data/financial/b_pit_v1/<artifact đã pin>/labels.csv`, model, manifest và audit.
- `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/{benchmark_daily.jsonl,trading_calendar.jsonl,prices_daily.jsonl}`.
- `configs/experiments/m3_strategy_v1.json` (protocol, segments và trạng thái LOCKED).

Các đường dẫn hash là pin cụ thể của code hiện tại; nếu cấu hình/module checkout của bạn khác, hãy lấy đường dẫn từ phiên bản trong máy và manifest, không đổi hash theo ví dụ này.

### Mã nguồn và các bước

| Bước | Mã/điểm vào | Đầu vào | Đầu ra |
|---|---|---|---|
| Kiểm kê khả năng dữ liệu | `scripts/m3_stage0.py` | Bundle thị trường, cấu hình và dữ liệu M3 được pin | Manifest đầu vào, coverage và số ứng viên; không tính lợi suất danh mục |
| Build nhãn B-PIT | `scripts/build_financial_pit_clusters.py` | Indicators v1, availability, bundle B tham chiếu và quy tắc cutoff | `data/financial/b_pit_v1/bpit-<hash>/` với labels/models/audit/manifest |
| Đánh giá feasibility | `scripts/m3_feasibility_variants.py` | Config M3 và A/B/B-PIT đã chọn | Bảng số ứng viên/khả thi; không phải kết quả lợi suất |
| Tạo targets để kiểm tra | `scripts/run_m3.py --segment <development|holdout> --targets-only` | Toàn bộ input đã pin và `configs/experiments/m3_strategy_v1.json` | `data/experiments/m3/<segment>/<run_id>/targets_*.csv`, audit và manifest |
| Chạy backtest chính thức | `scripts/run_m3.py --segment <development|holdout>` | Cùng input, B-PIT đã pin, code sạch và config `LOCKED` | Trade ledger, holdings, NAV, turnover, benchmark, metrics, manifest |
| Công bố CSV đã seal | `scripts/publish_m3_data.py` | Hai run đã verify/seal | Bản sao CSV canonical vào `M3/outputs/development/`, `M3/outputs/holdout/`, manifest/verification |

M3 Development (60 quyết định, 59 kỳ thực thi) và Holdout (24 quyết định, 23 kỳ thực thi) đã chạy, verify và seal ngày 04/11/2026. Kết quả CSV đang có trong `M3/outputs/`; báo cáo tại `docs/REPORT_BACKTEST.md` và `M3/reports/BAO_CAO_KY_THUAT_M3.md`. Final Evaluation chưa sẵn sàng vì thiếu dữ liệu 2026; M3-C còn PARTIAL và dashboard M3-B chưa làm. Đọc trạng thái mới nhất trước khi thao tác.

**Không chạy lại lệnh backtest chính thức nếu mục tiêu chỉ là xem kết quả.** Để đọc kết quả, mở `M3/outputs/README.md`, `M3/outputs/manifest.json`, run `metrics.json`, `seal.json` và báo cáo. Kết quả Development và Holdout là hai đoạn tách biệt, không nối NAV giữa hai đoạn.

Nếu được giao tái lập trong môi trường đúng dữ liệu và theo hướng dẫn M3 readiness, lệnh targets-only có dạng:

```powershell
python scripts/run_m3.py --segment development --targets-only
python scripts/run_m3.py --segment holdout --targets-only
```

Full backtest chỉ hợp lệ theo gate/approval trong `M3/M3_READINESS.md`: B-PIT được build và pin; hash khớp; code/config đã commit và sạch; config LOCKED; Development được kiểm tra/seal trước Holdout. Luôn dùng notebook `M3/notebooks/01_Du_Lieu_Va_PIT.ipynb` đến `03_Tai_Lap_Backtest_Va_Benchmark.ipynb` hoặc run đã công bố theo đúng hướng dẫn; notebook `04_Bao_Cao_Danh_Gia_Cuoi.ipynb` chưa phải kết quả Final Evaluation.

## 6. Chạy phần web

### Web hiện hành

Web chính là frontend Next.js tại `web/frontend/` và backend FastAPI tại `web/backend/app/`. API là read-only, đọc presentation bundle SQLite đã export. Nó không fit lại mô hình và không chạy backtest. `web/index.html`, `web/app.js`, `web/styles.css` là giao diện tĩnh cũ; `web/monitor/` là monitor riêng, không nhầm với app DELTA chính.

### Input và output của web

- Input bundle mặc định: `data/web/delta-intelligence-v1/` theo `web/README.md` (gồm SQLite và manifest). Kiểm tra cấu hình/README của checkout vì bundle v4 là nguồn dữ liệu nghiên cứu/M3, còn v1 là bundle trình bày local được ghi trong README.
- Bundle mới có thể được tạo bằng `scripts/export_delta_terminal.py`; exporter cần các artifact local active, gồm market C8 V2, M2 handoff, financial Execution56 và C result mà `artifacts/reports/combined-reference-v1/result-ref.json` trỏ tới. Nếu nguồn thiếu hoặc hash sai, exporter dừng; không dùng mock.
- Mã backend: `web/backend/app/main.py` (API), `repository.py` (đọc SQLite), `schemas.py` (response), cùng các module indicator, fundamentals, backtest, availability, alignment, previews.
- Mã giao diện: `web/frontend/` (Next.js). `web/app.js` ở root là bản static cũ.
- Output khi chạy: trang web tại `http://127.0.0.1:3000`, tài liệu API tại `http://127.0.0.1:8010/docs`.

### Khởi động local

Từ repository root, sau khi môi trường đã cài đủ Python 3.11+ và Node.js 22/24, chạy:

```powershell
python scripts/start_delta_terminal.py
```

Mở `http://127.0.0.1:3000`. Dừng hai dịch vụ bằng Ctrl+C trong terminal. Máy mới có thể cần cài dependencies theo `web/README.md`; chỉ chạy `export_delta_terminal.py` khi cần tạo bundle mới và có đủ inputs. Không ghi đè bundle đang sử dụng; exporter yêu cầu output version mới.

Production local theo hướng dẫn README:

```powershell
npm --prefix web/frontend run build
python scripts/start_delta_terminal.py --production
```

## 7. Kiểm tra nhanh khi lỗi

| Triệu chứng | Nguyên nhân thường gặp | Việc cần kiểm tra |
|---|---|---|
| Không tìm thấy `terminal.sqlite` | ZIP giải nén lồng cấp hoặc thiếu data bundle | `Test-Path data/web/delta-intelligence-v4/terminal.sqlite`; mở archive README và kiểm tra vị trí `data/` |
| Thiếu chỉ báo hoặc availability | Archive chỉ có một phần dữ liệu | Kiểm tra đúng thư mục version/hash trong `src/delta_t1/m3/inputs.py` và manifest nguồn |
| B-PIT hash không khớp | File đổi sau khi pin hoặc dùng nhầm artifact | Đối chiếu `labels_sha256` trong config, `manifest.json`, không sửa hash để lách kiểm tra |
| Backtest bị từ chối | Config chưa LOCKED, B-PIT chưa pin hoặc working tree có thay đổi | Đọc `M3/M3_READINESS.md`, kiểm tra config và git state |
| Web báo bundle/database hash sai | Bundle không đúng phiên bản hoặc bị sửa | Kiểm tra `DELTA_BUNDLE`, manifest và README; khôi phục đúng bundle đã export |
| Port đang được dùng | App khác đang nghe ở cổng mặc định | Dùng tùy chọn `--web-port 3001 --api-port 8011` nếu runner hỗ trợ |

## 8. Tài liệu chuẩn để tra cứu

- M3: `M3/M3_READINESS.md`, `M3/KE_HOACH_M3_SCHEMA_GITHUB.md`, `docs/REPORT_BACKTEST.md`.
- Trạng thái tổng và phân biệt nhánh hiện hành/legacy: `docs/CURRENT_STATUS.md`.
- Bản đồ repository: `docs/PROJECT_MAP.md`.
- Web: `web/README.md`.
- Kết quả M3 đã publish: `M3/outputs/README.md` và `M3/outputs/manifest.json`.
- Handoff dữ liệu tài chính: `data/handoffs/financial-reference-2016-2025/README.md` (nếu bundle đã giải nén).


## 9. Phạm vi và giới hạn cần bàn giao cùng mã nguồn

- Tài liệu trạng thái hiện hành là nguồn ưu tiên khi README cũ, notebook hoặc báo cáo lịch sử không đồng nhất. Mở `docs/CURRENT_STATUS.md` và tìm mục cập nhật mới nhất; không mặc định nội dung lịch sử bên dưới phản ánh worker hoặc protocol đang dùng.
- Nhánh M2 K=2 và một số notebook/handoff trong `M2/` là legacy. Mô hình A và B của bundle v4 là các baseline độc lập; không gộp A/B rồi mô tả là đã cùng được fit.
- Model B v4 có thể là nhãn ex-post, không có nghĩa là B-PIT. M3 chính thức cần B-PIT được pin đúng hash và ngày khả dụng.
- M3 Development/Holdout đã có kết quả được seal; Final Evaluation chưa sẵn sàng do dữ liệu 2026. Không nối NAV hai segment thành một chuỗi liên tục.
- Phần web hiện tại là ứng dụng tra cứu chỉ đọc. Dashboard M3-B được ghi là chưa thực hiện; giao diện không phải bằng chứng một quy trình backtest mới đã chạy.
- Dữ liệu tài chính, giá và bundle presentation có thể bị Git ignore. Bàn giao source code mà thiếu data bundle sẽ không đủ để tái lập đầy đủ.
- Khi chuyển archive sang máy Windows khác, kiểm tra encoding, line endings và SHA-256 theo manifest. Không đổi tên thư mục hash hoặc sửa hash trong config để bỏ qua kiểm soát toàn vẹn.

## 10. Đầu ra nên bàn giao cho nhóm tiếp nhận

| Loại | Vị trí chính | Cách dùng |
|---|---|---|
| Mã nguồn và cấu hình | `src/`, `scripts/`, `configs/` | Phiên bản hóa theo Git; ghi branch/commit |
| Bằng chứng/manifest nghiên cứu | `artifacts/`, `M2/artifacts/`, `M2/reports/` | Đọc kết quả và trace nguồn; không coi tất cả artifact là input hiện hành |
| CSV M3 đã công bố | `M3/outputs/` | Dùng bản đã seal; xem `README.md`, `manifest.json`, `seal.json` |
| Dữ liệu thực | `data/` và một phần `artifacts/cafef_primary/` | Bàn giao qua kho/ZIP được kiểm soát; xác minh hash và quyền truy cập |
| Tài liệu vận hành | `docs/`, `M3/`, `web/` | Làm theo tài liệu trạng thái mới nhất và runbook theo thành phần |
| Ứng dụng web | `web/frontend/`, `web/backend/` | Cần bundle SQLite presentation tương ứng và dependency runtime |

Tách source khỏi data bundle khi lưu trữ nếu cần, nhưng phải kèm manifest/checksum và hướng dẫn ghép lại. Không gửi database lớn hoặc dữ liệu nhạy cảm vào kênh công khai nếu chưa được công ty cho phép.

## 11. Thông tin nên ghi vào biên bản bàn giao

- Tên nhánh, commit SHA và trạng thái working tree.
- Tên các archive dữ liệu đã giao, kích thước, SHA-256 và vị trí lưu trữ.
- Phiên bản/hash của bundle v4, Indicators, availability, B-PIT và C8 đang dùng.
- ID/thư mục run M3 Development/Holdout đã seal và vị trí manifest/seal.
- Phiên bản runtime Python/Node và các file requirements/lock đã dùng.
- Lệnh khởi động web, URL kiểm tra, người nhận quyền truy cập và người phụ trách vận hành.
- Các mục còn mở: Final Evaluation 2026, mức độ đầy đủ của dữ liệu, M3 dashboard và các review chất lượng được ghi trong trạng thái dự án.

Không ghi mật khẩu, API key hoặc thông tin đăng nhập vào tài liệu bàn giao hay repository; bàn giao secrets qua cơ chế quản lý secrets của công ty.
