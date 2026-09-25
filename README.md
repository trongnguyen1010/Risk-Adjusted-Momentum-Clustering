# DELTA

DELTA là repository research + product cho thị trường cổ phiếu Việt Nam. Research Core xây market dataset point-in-time, feature snapshot và protocol clustering; Product Layer chỉ trình bày artifact đã version hóa, không tự fit lại model.

## Trạng thái hiện tại

CafeF `TradeHistoryNew` là nguồn market active. Stage C8 đã được execute và C8-VERIFY đã xác minh offline, không rerun feature build:

- 952 securities trong candidate universe: 500 C5 baseline + 452 C7 complete expansion;
- 905 securities đạt `market_feature_ready_v2=true` và tạo thành proposed `MARKET_ONLY_EXPERIMENTAL_UNIVERSE`;
- 47 securities chưa market-ready; 148 expansion securities còn `DEFERRED_EXPANSION_ACQUISITION`;
- 0 securities đạt `historical_identity_ready`; 0 đạt `research_ready` theo strict gate hiện tại;
- 905 không phải final research universe, canonical production universe hoặc kết quả đầu tư.

R1 đã hợp nhất repository sau C8: bỏ planning/history/runner superseded khỏi active tree, giữ code và evidence cần thiết để verify C8, duy trì acquisition có kiểm soát và chuẩn bị stage nghiên cứu tiếp theo. M1-REPORT đã hoàn tất tại `artifacts/reports/m1-market-foundation-v1/`; notebook inspection nằm tại `notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb`. Các file đã xóa vẫn truy xuất được trong Git history.

Trong M2-PREP, `market_experiment_eligible(t)` được định nghĩa theo từng snapshot là `market_feature_ready_v2(t)` dưới protocol M2 được freeze. Con số 905 chỉ là membership ở snapshot mới nhất `2026-08-28`, không phải bộ lọc terminal áp ngược về lịch sử và không đồng nghĩa `research_ready`.

## Quick start

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
.venv\Scripts\python.exe scripts\build_m1_market_foundation_report.py --verify-existing
```

Không chạy C8 verifier-generator lại khi compact artifact đã tồn tại. Full tests và M1-REPORT verifier kiểm tra evidence/hash hiện hành; R1 exact-inventory verifier chỉ tái hiện được tại frozen R1 tree, không phải sau các commit M1/D1. Synthetic smoke chỉ là regression kỹ thuật, không phải research evidence.

## Cấu trúc active

```text
src/delta_t1/   Research Core, ingestion, experiment và Product Layer
configs/        Contract/config active cho C8, expansion, supplemental và synthetic smoke
tests/          Unit, integration và regression tests còn hiệu lực
scripts/        Runner/verification active
web/            Dashboard tĩnh đọc Product API
docs/           Contract, methodology, trạng thái và reproducibility
artifacts/      Evidence được version hóa; heavy C8 artifact giữ local, immutable
```

Đọc tiếp tại [Documentation index](docs/README.md), [Current status](docs/CURRENT_STATUS.md), [Project map](docs/PROJECT_MAP.md), [Methodology](docs/METHODOLOGY.md), [Reproducibility](docs/REPRODUCIBILITY.md) và [Roadmap](docs/ROADMAP.md).

## Stage tiếp theo

Stage chính xác tiếp theo sau D1 là **M2-PREP — MARKET-ONLY EXPERIMENT PROTOCOL**: review/freeze eligibility theo snapshot, development/validation windows, preprocessing và evaluation contract trước khi chạy clustering. Stage này không được ngầm nâng 905 securities thành `research_ready`; mọi thay đổi gate identity hoặc strict research eligibility cần manual review.

## Disclaimer

DELTA là project nghiên cứu và công cụ phân tích, không phải khuyến nghị đầu tư.
