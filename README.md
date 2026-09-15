# Delta Intelligence

Nền tảng phân tích doanh nghiệp và cổ phiếu Việt Nam, định hướng sản phẩm thật. Trang chi tiết công ty là bề mặt chính; phân cụm cổ phiếu là một capability tạo peer insight, không còn là toàn bộ danh tính của project.

## Trạng thái hiện tại

- **Product foundation:** company-detail contract, immutable product bundle, REST read API và responsive web shell đã có.
- **Engineering/research core:** immutable ingestion, canonical schemas, QC, monthly features, K-Means baseline, label alignment, transitions và backtest được giữ lại.
- **Chưa production-ready:** mới có dữ liệu pilot thật 10 mã 2023–2025; fundamentals PIT, company profile, news/sentiment, source reconciliation và universe lịch sử lớn chưa được hoàn thiện.
- **Research verdict:** `MAJOR REALIGNMENT REQUIRED`. Pilot cũ chỉ là integration evidence, không phải kết quả cuối khóa luận hay khuyến nghị đầu tư.

Điểm bắt đầu tài liệu là [docs index](docs/README.md). Các tài liệu chính gồm [product requirements](docs/PRODUCT_REQUIREMENTS.md), [architecture](docs/ARCHITECTURE.md), [research protocol](docs/RESEARCH.md), [data pipeline](docs/DATA_PIPELINE.md) và [roadmap](docs/PLAN.md).

## Chạy product demo từ evidence đã đóng băng

Cách nhanh nhất từ PowerShell:

```powershell
.\scripts\start_product.ps1
```

Không mở `web/index.html` trực tiếp: trang cần API local để tải bundle. Sau khi server chạy, mở `http://127.0.0.1:8000/?ticker=FPT`.

Hoặc chạy thủ công:

```powershell
.venv/Scripts/python.exe run.py product-build `
  --canonical data/canonical/canonical-1d2a54288bfc `
  --features data/runs/run-4a1a6203dba7 `
  --experiment data/experiments/experiment-de5f4d68afa0 `
  --output artifacts/product/pilot-v1

.venv/Scripts/python.exe run.py serve --bundle artifacts/product/pilot-v1 --web-root web --port 8000
```

Mở `http://127.0.0.1:8000/?ticker=FPT`. Bundle pilot hiển thị giá điều chỉnh, market analytics và cluster peers; các domain chưa có dữ liệu được ghi rõ là chưa khả dụng.

API v1: `GET /api/v1/health`, `GET /api/v1/companies`, `GET /api/v1/companies/{ticker}`. Xem [API contract](docs/API_CONTRACT.md).

## Pipeline và tests

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe run.py run --config configs/demo.json
```

Synthetic chỉ dùng cho test/regression. Dữ liệu thật yêu cầu tối thiểu ba năm lịch sử quan sát để vào clustering. Sharpe/ROI không được dùng làm clustering input hoặc cluster-quality metric; Sharpe chỉ được phép ở lớp đánh giá portfolio.

## Cấu trúc

```text
src/delta_t1/
  ingestion/       source adapters, staging, promotion, recovery
  features/        as-of feature computation
  clustering/      research baseline
  evaluation/      cluster stability and performance
  backtest/        portfolio simulation
  product/         immutable product projection, repository and HTTP edge
web/               dependency-free company-detail interface
configs/           active pipeline/research configurations
docs/              contracts, decisions and product specifications
data/               ignored immutable evidence and canonical runs
artifacts/          ignored generated product bundles
```

UI không đọc raw tables và không tính lại feature/model. Mọi insight phải truy về `data_version`, `canonical_run_id` và `experiment_run_id`. Missing không được thay bằng zero; raw price, adjusted price và total return phải tách semantics.

Pilot KBS/Vnstock cũ chỉ còn một [semantic evidence](docs/data/kbs_pilot_semantics.md) vì immutable manifests vẫn tham chiếu nó; trạng thái run nằm trong [validation](docs/VALIDATION.md). Pilot không còn là entry point mặc định.
