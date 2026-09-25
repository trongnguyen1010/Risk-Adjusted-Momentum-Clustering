# DELTA

DELTA là repository research + product cho thị trường cổ phiếu Việt Nam. Research Core xây market dataset point-in-time, feature snapshot và protocol clustering; Product Layer chỉ trình bày artifact đã version hóa, không tự fit lại model.

## Trạng thái hiện tại

CafeF `TradeHistoryNew` là nguồn market active. Stage C8 đã được execute và C8-VERIFY đã xác minh offline, không rerun feature build:

- 952 securities trong candidate universe: 500 C5 baseline + 452 C7 complete expansion;
- 905 securities đạt `market_feature_ready_v2=true` và tạo thành proposed `MARKET_ONLY_EXPERIMENTAL_UNIVERSE`;
- 47 securities chưa market-ready; 148 expansion securities còn `DEFERRED_EXPANSION_ACQUISITION`;
- 0 securities đạt `historical_identity_ready`; 0 đạt `research_ready` theo strict gate hiện tại;
- 905 không phải final research universe, canonical production universe hoặc kết quả đầu tư.

R1 đã hợp nhất repository sau C8: bỏ planning/history/runner superseded khỏi active tree, giữ code và evidence cần thiết để verify C8, duy trì acquisition có kiểm soát và chuẩn bị stage nghiên cứu tiếp theo. Các file đã xóa vẫn truy xuất được trong Git history.

## Quick start

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
.venv\Scripts\python.exe scripts\verify_cafef_c8_results.py
.venv\Scripts\python.exe scripts\verify_repository_r1.py --verify-existing
```

Không chạy C8 lại để kiểm chứng: dùng manifest và hash của artifact local bất biến. Synthetic smoke chỉ là regression kỹ thuật, không phải research evidence.

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

Stage đề xuất sau R1 là **M2-PREP — MARKET-ONLY EXPERIMENT PROTOCOL**: review/freeze eligibility và protocol cho proposed 905-security market-only universe trước khi chạy clustering. Stage này không được ngầm nâng 905 securities thành `research_ready`; mọi thay đổi gate identity hoặc eligibility cần manual review.

## Disclaimer

DELTA là project nghiên cứu và công cụ phân tích, không phải khuyến nghị đầu tư.
