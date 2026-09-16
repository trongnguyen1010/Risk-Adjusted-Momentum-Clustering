# DELTA

DELTA là project research + product cho thị trường cổ phiếu Việt Nam. Research Core nghiên cứu phân cụm cổ phiếu bằng market feature và point-in-time financial feature; Product Layer trình bày các artifact nghiên cứu đã được version hóa mà không tự fit lại model.

## Hai track

- **Research Core:** xây data foundation, so sánh các phương pháp clustering và đánh giá backtest theo protocol đã khóa.
- **Product Layer:** giữ API, immutable bundle và dashboard để khám phá ticker, cluster, peer, transition, data quality và provenance.

## Trạng thái milestone

| Milestone | Trạng thái hiện tại |
|---|---|
| **M1 — Data Foundation** | Đã có immutable ingestion/schema/QC và gate code; `SOURCE_SMOKE` thật, `REPRESENTATIVE_PILOT` 50–60 mã và scale >=300 đều chưa PASS. |
| **M2 — Clustering Research** | Static K-Means deterministic là baseline; temporal tracking hiện tại không phải Dynamic Clustering. PCA/comparator và methodology động còn phải hoàn thiện. |
| **M3 — Backtest + Product** | Đã có return-space backtest, product bundle, read API và web shell; final backtest chờ freeze methodology và representative data. |

## Quick start

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe run.py run --config configs/data/synthetic_smoke.example.json
.\scripts\start_product.ps1
```

Mở `http://127.0.0.1:8000/?ticker=FPT` sau khi product server khởi động. Synthetic config chỉ dùng cho smoke/regression, không phải research evidence.

## Cấu trúc repository

```text
src/delta_t1/   Research Core, ingestion, experiment và Product Layer
configs/        Data, feature, experiment và product config mẫu
tests/          Unit, integration, regression và fixtures
web/            Dashboard tĩnh đọc Product API
docs/           Tài liệu onboarding, methodology và reproducibility
data/           Immutable/generated run data, không phải source code
artifacts/      Versioned product projection được sinh từ experiment
```

## Bắt đầu đọc tài liệu

[docs/README.md](docs/README.md) → [Project Overview](docs/PROJECT_OVERVIEW.md) → [Project Map](docs/PROJECT_MAP.md) → [Roadmap](docs/ROADMAP.md).

Xem thêm [Architecture](docs/ARCHITECTURE.md), [Data Contract](docs/DATA_CONTRACT.md), [Data Collection — START HERE](docs/crawl/README.md), [Methodology](docs/METHODOLOGY.md), [Product](docs/PRODUCT.md), [Reproducibility](docs/REPRODUCIBILITY.md) và [Contributing](CONTRIBUTING.md).

## Disclaimer

DELTA là project nghiên cứu và công cụ phân tích, không phải khuyến nghị đầu tư. Kết quả synthetic/pilot không được diễn giải thành hiệu quả thực tế; Product Layer không được dùng để quyết định research methodology.
