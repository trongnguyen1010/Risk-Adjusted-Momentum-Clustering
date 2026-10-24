# DELTA Intelligence — web demo

## Bổ sung bộ sáu chỉ số đã review

Trang Tra cứu cổ phiếu có panel EPS/P/E/P/B/F/M/Z độc lập với sáu core ratios của B/C.
API `/api/v2/indicators/{ticker}` đọc hai gói có hash được chốt trong
`configs/product/indicator_reference_v1.json`: compute-first có 85 numeric reference rows/11 mã,
pilot5 có 29/30 numeric cells trên 5 mã. Pilot5 là một phần dữ liệu đã tổng hợp;
**không cộng hai counter thành coverage mới**, không gọi 85 rows là 85 mã.
Hai Z references bổ sung trong tổng report 87 rows chưa nằm trong hai gói được nối này.

Chọn gói/kỳ/snapshot riêng; FPT cùng PDF nhưng khác snapshot không bị gộp,
EPS YTD9 không ghép với quarter standalone hoặc tự annualize. Thiếu giữ null.
EPS/F/M/Z pilot dùng FY2025; PE/PB pilot dùng giá raw 22/04/2026 và book snapshot31/12/2025.
Chúng không tự trở thành thông tin đã biết ở ngày thị trường đang chọn.

Adapter chỉ đọc kết quả đã tính, không tính lại scores, không fit, không đưa scores vào B/C.
16 targeted tests API/adapter PASS. UI thêm cảnh báo A bị thanh khoản chi phối.

Giao diện demo đã Việt hóa theo yêu cầu owner: 5 màn hình, nhãn đặc trưng, trạng thái, hướng dẫn và định dạng `vi-VN`; giữ mã feature, công thức và protocol gốc để đối chiếu. Không thay dữ liệu hoặc mô hình.

Demo nghiên cứu đọc artifact A market, B financial và C combined; không fit model hoặc sửa research gates. Static dashboard cũ tại `web/index.html`, monitor và Streamlit được giữ nguyên.

## So sánh prompt với project

| Yêu cầu | Evidence có sẵn | Triển khai demo |
|---|---|---|
| Overview | A: 84 tháng/75.801 assignments; B: 10 FY/11.720; C: 7 năm/5.593 | Coverage theo thời gian, bản đồ model availability, kích thước cụm |
| Cluster Atlas | 101 fitted snapshots, 219 profiles | Scatter features thật, đổi trục, zoom, highlight, chọn cụm, drawer, time machine |
| Migration | Nhãn độc lập từng snapshot | Pairwise maximum-overlap alignment để hiển thị; không đổi frozen labels, không coi ID là regime identity |
| Stock Explorer | 3.214.287 daily price rows, memberships và 14 features | Giá raw/adjusted riêng, không nối missing; journey A/B/C; so sánh tối đa 4 mã cùng ngày |
| Financial Lens | 6 core ratios; fixed full10 cohort | Phân bố/boxplots, cụm nhỏ, ma trận giao market cuối năm × FY và drill-down |
| Research Lab | Protocol, definitions, verification và hashes | Configuration, provenance, quality gates, limitations |
| Search/deep link/demo | Ticker/name từ securities | Cmd/Ctrl+K, URL kind/date/ticker/axes/year, guided exploration |
| F/M/Z, live quotes, PIT/backtest | Chưa đủ dữ liệu/gates | Explicit unavailable; không sinh số giả |

C năm 2025: C0=479, C1=663, C2=6. B năm 2025: B0=3, B1=1.168, B2=1. Nhãn không phải xếp hạng đầu tư. Financial có **0/11.720 published_at**; ma trận same-FY và C là ex-post, không phải PIT.

## Kiến trúc

`versioned research artifacts → terminal_export.py → SQLite presentation index + manifest → FastAPI read-only → Next.js`

- Frontend: Next App Router, TypeScript, React, Tailwind, Lucide, ECharts, TanStack Table. Font Inter/Space Grotesk được bundle local. Controls dùng native HTML và components riêng, không phụ thuộc shadcn/ui.
- Backend: FastAPI với response schemas; truy vấn parameterized, whitelist sort, pagination, mode=ro và query_only. Hash database được kiểm tra lúc startup.
- Adapter chỉ copy features/labels/diagnostics có sẵn; median/quartile là presentation aggregates. Không recompute scaler, fit, portfolio metric hoặc mở research gate.
- Dữ liệu price/bundle nằm trong `data/`, bị Git ignore. Không đưa SQLite ~546 MB hay node_modules lên Git.
- API mặc định `127.0.0.1:8010`; frontend `127.0.0.1:3000`, proxy same-origin `/api/v2`. Không cần CORS.

## Chạy local

Từ repository root, cần Python 3.11+ và Node 22/24. Máy hiện tại đã cài dependencies tại `.tools/web-runtime` và `web/frontend/node_modules`, đã export bundle thật.

```powershell
python scripts/start_delta_terminal.py
```

Mở <http://127.0.0.1:3000>. API docs: <http://127.0.0.1:8010/docs>. Ctrl+C dừng cả hai services. Có thể chọn `--web-port 3001 --api-port 8011`.

Máy mới cần setup một lần:

```powershell
python -m venv .venv-web
.venv-web/Scripts/python.exe -m pip install -r web/backend/requirements.txt
npm --prefix web/frontend ci
.venv-web/Scripts/python.exe scripts/export_delta_terminal.py
.venv-web/Scripts/python.exe scripts/start_delta_terminal.py
```

Exporter cần **đầy đủ các artifact local đang active**, gồm canonical market C8 V2, M2 handoff, financial Execution56 và C result mà `artifacts/reports/combined-reference-v1/result-ref.json` trỏ tới. Git clone riêng hoặc chỉ market ZIP chưa đủ. Thiếu source/hash sai sẽ dừng; không có mock fallback.

Bundle mặc định `data/web/delta-intelligence-v1`. Exporter từ chối ghi đè. Khi cần bản mới, dùng `--output data/web/<new-bundle>` và đặt `DELTA_BUNDLE` cho API; giữ bản cũ. `--skip-prices` chỉ dành cho development/test, không phải demo đầy đủ.

Production local:

```powershell
npm --prefix web/frontend run build
python scripts/start_delta_terminal.py --production
```

## API chính

| Endpoint `/api/v2` | Nội dung |
|---|---|
| `/health`, `/catalog` | Readiness kỹ thuật, datasets, source fingerprints |
| `/snapshots/{market\|financial\|combined}?date=...` | Points, profiles, saved metrics |
| `/members/{kind}` | q, exchange, cluster, sort/direction, page/page_size ≤100 |
| `/stocks/{ticker}?kind=...&date=...` | Exact snapshot, history riêng cho A/B/C |
| `/prices/{ticker}?basis=adj_close\|raw_close&end=...` | VND/share, không trộn basis |
| `/compare?tickers=FPT,VNM,HPG&kind=...&date=...` | 1–4 mã; thiếu membership giữ null |
| `/matrix/{year}` | Common cohort same-FY reference, không PIT |
| `/migration/{kind}?source=...&target=...` | Alignment chỉ để hiển thị + entered/exited/common |

Unknown kind/invalid query bị từ chối; ngày không có model trả 404, ticker ambiguous trả 409. Không lấy observation ngày khác để lấp dữ liệu.

## Kiểm tra và demo

```powershell
$env:PYTHONPATH="$PWD/.tools/web-runtime;$PWD/src;$PWD/tests"
python -m unittest unit.test_terminal_api -v
python scripts/verify_delta_terminal.py --check-sources
python -m compileall -q src tests scripts run.py
node --check web/app.js
npm --prefix web/frontend run typecheck
npm --prefix web/frontend run build
```

10 contract tests dùng fixture test tách biệt. Verifier thực kiểm tra 101 snapshots, 219 profiles, 7 ma trận, counts, sample price và optional toàn bộ source hashes. Full repository gate được báo riêng; targeted PASS không thay thế full-suite PASS.

Luồng demo: Overview → Atlas C năm 2025 → chọn C2 (6 mã) → tìm FPT và mở drawer → Stock Explorer → đổi price basis/so sánh FPT,VNM,HPG → Financial Lens FY2025 → click ma trận → FY2016 để xem empty state → Research Lab kiểm protocol/quality/provenance. Guided exploration trong sidebar dẫn qua 5 màn hình.

Thiết kế desktop được ưu tiên; mobile có menu thu gọn, panels xếp dọc, bảng cuộn ngang. Charts dùng raw feature coordinates, không random projection; zoom không clipping đầu vào model. Journey đặt FY tại cuối năm chỉ để bố trí, không ngụ ý publication date.

Tham chiếu bố cục từ trang chính thức [Nansen](https://www.nansen.ai/), [DeFiLlama](https://defillama.com/), [Dune](https://dune.com/), [DEX Screener](https://dexscreener.com/); không sao chép assets hoặc kết quả của họ.

## Deploy demo dùng chung

`HF Dataset (data đã pin hash) → Render Docker (FastAPI read-only) ← Vercel (Next.js proxy /api/v2)`

- Dữ liệu vẫn không vào Git. `python scripts/publish_hf_data.py` kiểm tra hash rồi upload bundle + hai gói indicator lên Dataset công khai `ngyen/delta-intelligence-data`, đồng thời cập nhật `deploy/render/data-files.txt`.
- Backend: Render đọc `render.yaml` (free, Singapore), build `deploy/render/Dockerfile`, tải data lúc build; API vẫn kiểm tra checksum lúc startup và fail-closed. Gói free ngủ sau ~15 phút không truy cập, lần mở đầu có thể chờ ~1 phút.
- Frontend: Vercel project root `web/frontend`, biến `DELTA_API_URL=<Render URL>` cho cả build và runtime (rewrite được chốt lúc build).
- Khi export bundle mới: chạy lại `publish_hf_data.py`, commit `data-files.txt` nếu đổi, rồi Manual Deploy trên Render.

Chưa có auth hoặc multi-user; link demo công khai cho bất kỳ ai có URL.

