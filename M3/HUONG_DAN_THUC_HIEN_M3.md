# Hướng dẫn chạy trực tiếp notebook M3-C

Notebook 01–03 chứa toàn bộ mã điều phối, kiểm tra, vẽ hình và sinh báo cáo ngay trong các cell.
Bạn mở notebook, chọn kernel và **Run All**; không cần chạy hoặc import helper `.py` trong `M3`.
Các hàm PIT, ranking, portfolio và metrics vẫn gọi module chính thức trong `src/delta_t1/m3`
và `scripts/run_m3.py`, đúng kế hoạch chuẩn.

## 1. Tệp cần dùng

| Tệp | Vai trò |
|---|---|
| [Notebook 01](notebooks/01_Du_Lieu_Va_PIT.ipynb) | Kiểm tra input, code/config/hash và PIT mẫu |
| [Notebook 02](notebooks/02_Tai_Lap_Lua_Chon_Danh_Muc.ipynb) | Tái lập ứng viên, điểm, rank, target và audit; bảy negative controls |
| [Notebook 03](notebooks/03_Tai_Lap_Backtest_Va_Benchmark.ipynb) | Tái lập engine/metrics/VNINDEX, biểu đồ, báo cáo và phân rã Holdout 2024 |
| [Notebook 04](notebooks/04_Bao_Cao_Danh_Gia_Cuoi.ipynb) | Chỉ ghi trạng thái Final `NOT_READY`, chưa có cell tính performance |
| [sources.json](sources.json) | Pin code/config và hai seal nguồn |
| [Lock phụ thuộc](requirements-notebooks.lock.txt) | Các phiên bản thư viện notebook/biểu đồ đã dùng |
| [Báo cáo kỹ thuật](reports/BAO_CAO_KY_THUAT_M3.md) | Báo cáo được sinh từ Notebook 03 |
| [Phân tích đợt giảm 2024](reports/PHAN_TICH_BUOC_1_HOLDOUT_2024.md) | Báo cáo được sinh từ phần cuối Notebook 03 |

## 2. Chọn kernel và chạy

Môi trường đã chuẩn bị trong workspace:

```text
.tmp/m3c-kernel/Scripts/python.exe
```

Trong VS Code, mở file ipynb và chọn Python/kernel tại đường dẫn trên. Chạy **Run All** theo thứ tự
Notebook 01 → 02 → 03. Các notebook cũng có thể chạy độc lập trong kernel sạch; không phụ thuộc biến
hoặc hàm được chạy trước ở một notebook khác. Không cần chạy Notebook 04.

Mở notebook từ gốc repository hoặc thư mục `M3/notebooks` đều được. Cell đầu tự tìm repository root.
Các định nghĩa đọc dữ liệu/đối chiếu nằm trong phần thiết lập; phần tái lập và trình bày nằm tại từng mục.
Nếu sửa cell đầu hoặc định nghĩa hàm, restart kernel rồi Run All để tránh dùng state cũ.

Nếu chỉ đọc kết quả, mở notebook có output đã lưu, không cần thực thi lại.

### Chuẩn bị kernel trên máy khác hoặc khi runtime chưa có

Chạy PowerShell từ gốc repository:

```powershell
$m3Py = Join-Path $env:LOCALAPPDATA 'DELTA\venvs\m3-py312\Scripts\python.exe'
& $m3Py -I -m pip install --only-binary=:all: `
    --target .tmp/m3c-notebook-runtime `
    -c requirements-research.lock.txt `
    -r M3/requirements-notebooks.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Cài runtime notebook thất bại.' }

& $m3Py -I -m venv --without-pip .tmp/m3c-kernel
if ($LASTEXITCODE -ne 0) { throw 'Tạo kernel environment thất bại.' }
$m3Runtime = (Resolve-Path -LiteralPath '.tmp/m3c-notebook-runtime').Path
$m3Site = (Resolve-Path -LiteralPath '.tmp/m3c-kernel/Lib/site-packages').Path
[System.IO.File]::WriteAllText(
    (Join-Path $m3Site 'm3c-runtime.pth'),
    $m3Runtime + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)
```

Kernel environment cô lập đọc bộ thư viện trong runtime đã khóa thông qua file `.pth`.
Không đổi package trong venv backtest M3, không cần cài thêm bộ dữ liệu hoặc fit model.
Sau đó chọn `.tmp/m3c-kernel/Scripts/python.exe` trong trình mở notebook và Run All.

## 3. Nguồn và phiên bản phải giữ đúng

| Thành phần | Giá trị |
|---|---|
| Source commit | `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf` |
| Config | `configs/experiments/m3_strategy_v1.json`, `LOCKED` |
| Config SHA256 | `b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d` |
| Dataset revision | `08c24867b11177072bfe457a4623a38abf9bbc48` |
| Dev run | `data/experiments/m3/development/20261104T121107Z-5557288c/` |
| Holdout run | `data/experiments/m3/holdout/20261104T133507Z-5557288c/` |

Hai seal nằm dưới `data/experiments/m3/seals/<segment>/<run-id>/seal.json`, có hash được pin trong
`sources.json`. Canonical outputs là targets, universe audit, ledger, holdings, turnover, NAV,
VNINDEX, metrics và manifest; mỗi run có 33 file.

Notebook kiểm tra hai seal, 66 file canonical, config và bảy input. Hash input được tính đầy đủ ở preflight;
trần/sàn lấy trong cùng lượt đọc C8. Nếu các kernel dùng cùng `M3C_OUTPUT_DIR`, preflight được tái sử dụng
sau khi kiểm tra fingerprint/hash metadata. Nếu không đặt biến này, mỗi notebook tạo thư mục reproduction mới.
Notebook in đường dẫn `ctx.output` để bạn mở evidence tương ứng.

Code thực thi có thể có thêm commit tài liệu/notebook, nhưng các module M3-A và config phải khớp source commit.
Bằng chứng ghi cả source commit và execution commit, không đổi identity run đã seal để làm khớp.
Hai CSV Combined v2 là bản đọc từng kỳ, không thay canonical outputs để kiểm chứng.

## 4. Đối chiếu và điều kiện hoàn tất

| Notebook | Input/module chính thức | Output và điều kiện PASS | FAIL/DỪNG và bước tiếp theo |
|---|---|---|---|
| 01 | Manifest/config/pins, availability/B-PIT, `inputs`, `universe.financial_state`, `Strategies.target_for` | Bảng provenance, PIT/target mẫu, `01_verification.json`; đúng FY usable/cutoff và target canonical | Sai hash/path/code/schema hoặc PIT/target lệch thì dừng; đạt mới chuyển 02 |
| 02 | Cùng pins; `Strategies`, `ranking`, canonical targets/audit của năm strategy | Đủ 60/24 decisions, target/audit khớp từng trường; ví dụ sáu tiêu chí và bảy kiểm tra phản ví dụ PASS; `02_verification.json`, `negative_controls.json` | Lệch ticker/rank/weight/candidates/reason/status hoặc test không đạt thì dừng; đạt chuyển 03 |
| 03 | Cùng pins; canonical targets/ledger/holdings/NAV/turnover/metrics, `PriceBook`, `engine.run`, `benchmark_nav`, metrics chính thức | Năm strategy × hai đoạn và VNINDEX khớp; CASH/tổng weight đúng, failed=0 executed, scaled đúng scale, turnover hai chiều/(2×NAV); có bảng/biểu đồ/báo cáo, `03_verification.json` | Lệch accounting/metrics, ngày ngoài segment, nối NAV hoặc có Sharpe Dev/Holdout thì dừng |
| 04 | Chỉ được triển khai phần thực thi khi có Final verified + sealed | Hiện `NOT_READY`; file chỉ có Markdown | Không dùng Dev/Holdout thay Final, không tạo performance giả |

Identifiers, schema, status và thứ tự phải khớp chính xác; số thực dùng rtol=1e-9, atol=1e-10.
Không sửa methodology/config để ép notebook khớp. Bảy negative controls được giữ trong Notebook 02,
bao gồm sai seal/config, NaN, missing/zero, lệch schema/order/status, tolerance và population percentile.

## 5. Báo cáo và phân tích đợt giảm năm 2024

Notebook 03 vẽ riêng Dev/Holdout. Hình chính chỉ có Combined/VNINDEX; đối chứng tách từng hàng,
mỗi ô hai đường, chung thang đo theo cột. Combined luôn xanh liền, đối chứng cam đứt.
Các nhận xét ngắn tập trung vào Combined/VNINDEX được giữ trong Markdown dưới phần biểu đồ.

Cell sinh báo cáo ghi `M3/reports/BAO_CAO_KY_THUAT_M3.md` từ số liệu nguồn. Phần 6 của notebook
chứa mã phân rã và sinh `M3/reports/PHAN_TICH_BUOC_1_HOLDOUT_2024.md`, không cần script phân tích riêng.
Phân rã dùng cùng đường vốn thực tế, không tạo chiến lược mới hoặc tune rule sau Holdout.

`nav`, `cash`, `intended`, `executed` là giá trị vốn chuẩn hóa với vốn đầu=1; weight là tỷ trọng.
Cash ratio=cash/NAV. Notebook dùng tỷ lệ 0–1, báo cáo định dạng %. Dev/Holdout có vốn đầu độc lập.
Drawdown chỉ đo theo ngày định giá được lưu. Strategy dùng vendor-adjusted close, VNINDEX là price index;
cả lợi suất và drawdown còn giới hạn cơ sở giá. Chi phí/slippage baseline=0.

## 6. Evidence và trạng thái

Mỗi notebook ghi `direct_01_done.json`, `direct_02_done.json` hoặc `direct_03_done.json` trong `ctx.output`,
kèm hash code của chính notebook. Các tệp kiểm tra 01/02/03 và preflight ở cùng thư mục.
Phân tích năm 2024 có thư mục evidence riêng, được in sau cell thực thi cuối.

[latest.json](reproduction/latest.json) trỏ đến phiên bàn giao trọn bộ đã được kiểm tra từ kernel sạch.
Run All thủ công tạo evidence tại `ctx.output`, không tự thay checkpoint bàn giao này.
Các helper cũ và notebook trước chuyển đổi đã được giữ trong ZIP tại thư mục reproduction để truy nguyên
bằng chứng lịch sử; bộ notebook hiện hành không import hoặc thực thi mã trong ZIP đó.

**Phần Dev/Holdout PASS** khi cả ba notebook chạy đủ cell, không có lỗi và các đối chiếu đạt.
**M3-C tổng thể PARTIAL** vì Final chưa đủ dữ liệu 2026. Notebook 04 tiếp tục NOT_READY.
Full repository gate trước đó hết giới hạn 180 giây; không suy từ notebook PASS rằng cả repository đã PASS.
M3-B có trách nhiệm gói dữ liệu/API/frontend và kiểm thử riêng, không thuộc bộ notebook này.
