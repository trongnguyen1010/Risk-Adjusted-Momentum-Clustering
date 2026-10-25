# DELTA Intelligence — web demo

## API chỉ số tài chính (Indicators v1, D-IND-01)

Backend đọc `indicators.sqlite` đã pin bởi `configs/product/indicators_v1.json` (sai/thiếu hash ⇒ 404, không phục vụ số chưa xác minh).
Build lại dữ liệu: `python scripts/build_indicator_inputs.py` → `python scripts/build_indicators.py` → `python scripts/verify_indicators.py`, rồi cập nhật pointer.

| Endpoint | Nội dung |
|---|---|
| `GET /api/v2/stocks/{ticker}/overview` | Tên, sàn, nhóm ngành, giá đóng cửa (raw) + % 1 ngày/1 tháng/YTD (giá điều chỉnh), vốn hóa, 6 thẻ chính + đánh giá, tóm tắt 3 dòng |
| `GET /api/v2/stocks/{ticker}/fundamentals?from=2016&to=2025` | `{metric: {year: {value, status}}}`, nhóm và đơn vị, mô tả 1 câu + công thức |
| `GET /api/v2/stocks/{ticker}/scores/{year}` | 9 tín hiệu F, 8 biến M, 5 thành phần Z |
| `GET /api/v2/stocks/{ticker}/peers` | Mã cùng cụm C (rồi A), gần vốn hóa nhất; không có cụm ⇒ cùng nhóm ngành |

Trang `/stocks?ticker=XXX` dùng 4 endpoint trên; tab: `overview`, `indicators`, `scores` (`&fy=2024`), `peers`.
Kiểm tra trình duyệt: `PLAYWRIGHT_MODULE=... CHROMIUM_EXECUTABLE=... DELTA_UI_URL=http://127.0.0.1:3000 node scripts/verify_delta_ui.cjs`.

Mặc định local, Render và `publish_hf_data.py` dùng bundle v2 (phân cụm mới). Muốn chạy lại v1:
`DELTA_BUNDLE=data/web/delta-intelligence-v1 python scripts/start_delta_terminal.py`. Bản xem trước R1 chỉ có với v1.

### Deploy bundle v2 (chưa thực hiện, chờ owner)

1. `python scripts/publish_hf_data.py --dry-run` → kiểm tra 14 file, hash khớp (≈ 655 MB).
2. `huggingface-cli login` (token có quyền write), rồi `python scripts/publish_hf_data.py --repo ngyen/delta-intelligence-data`.
3. Lấy commit hash Dataset vừa publish; đặt `DATA_BASE_URL=https://huggingface.co/datasets/ngyen/delta-intelligence-data/resolve/<commit>` cho Render build.
4. Render: service build từ branch đã merge `feature/indicators-v1` (hoặc đổi branch trong Settings), bấm Manual Deploy; kiểm tra `/api/v2/health` và `/api/v2/catalog` (k = 4/3/3).
5. Vercel: không đổi biến; Redeploy để có trang `/stocks` mới. Kiểm tra `/stocks?ticker=FPT`, `/atlas?kind=market`, `/financial?tab=compare`.

Test API cần FastAPI: `python -m venv --system-site-packages .venv-web` rồi `pip install -r web/backend/requirements.txt`.


## Bổ sung EPS theo năm/quý và trải nghiệm chỉ số

Owner yêu cầu tính/hiển thị chỉ số rộng hơn và bỏ UX gói review nội bộ. Đã thực
thi offline, không network/PDF/OCR hoặc fit model mới:

- `scripts/build_financial_serving.py` kiểm lại exact raw EPS code/label, đơn vị
  đồng/cp, provider, năm/quý/mode, giá trị và hashes; không biến quoted EPS thành
  kết quả tự tính. Output active:
  `data/financial/financial_serving_v1/results/source-period-eps-v3`.
- 53.716 quoted EPS/1.427 mã, gồm12.782annual và40.934quý/lũy kế. Display policy
  giữ6.508source-zero chưa xác nhận ở pending: còn47.208số EPS/1.426mã có thể
  xem với nguồn/basis rõ. Không gọi chúng là full6 hoặc independently verified.
- `coverage.csv` có511.272cells/85.212period-mode slots, bao gồm cả missing
  observations trên lưới1.522mã ×2016–2025×annual/Q1–Q4 và các mode lũy kế có sẵn.
  Một slot không chứng minh có đủ6chỉ số; đây là backlog minh bạch, không full coverage.
- `scripts/calculate_cached_financial_scores.py` đã chạy79.566evaluations
  trên13.261annualproviderpartitions/1.428mã. Không có thêm numeric scores đủ
  điều kiện release. Các kết quả/missing inputs nằm ở
  `data/financial/financial_score_attempt_v1/results/cache-calculators-v1`.
  EPS chưa có numerator/weighted shares, F thiếu đủ9signals, M thiếu khấu hao
  đúng basis, Z thiếu reconciledEBIT; PE/PB thiếu temporal/share/valuation basis.
- Quoted EPS và results đã đối chiếu giữ thành hai nhóm provenance độc lập.
  Missing không thành0; quoted0 chưa rõ không trở thành EPS xác nhận. Các ngày
  công bố vẫn cần delivery join riêng; timestamp null không chứng minh raw dates vắng.
- Panel mới `components/financial-indicators.tsx`: chọn năm và kỳ, mô tả từng
  chỉ số, history theo năm. Không đưa cohort IDs/hash vào option labels. Model
  controls chỉ hiện khi mở phân cụm/nguồn, giảm overload ở trang doanh nghiệp.
- Source `provider_eps` trong `configs/product/indicator_reference_v1.json`
  dùng SQLite/pinned manifest. API chỉ đọc ticker đang chọn; publisher/download
  list đã có database và manifest mới. Chưa upload Dataset hoặc redeploy services.

Kiểm tra targeted: `unit.test_financial_serving`, `unit.test_indicator_reference`,
`unit.test_terminal_api` (26testsPASS); compileall, legacyJSsyntax và synthetic
smoke `run-20261024T163303Z-18dd03ea` PASS. Production build vào thư mục riêng
qua `DELTA_BUILD_DIR=.next-product-check` để không ghi đè preview đang chạy.
Giữ báo cáo full-suite cũ riêng; lượt này không tuyên bố full-suite PASS.

Khi tạo lại source bundle, dùng `--output <version-mới>`; không overwrite output
cũ. Giữ pointer/hash tới đúng version và chạy `scripts/publish_hf_data.py --dry-run`
trước deploy. Muốn thêm F/M/Z phải bổ sung đúng input facts, không chỉ đổi trạng
thái hoặc bỏ nhãn reference trong UI.

## Nâng cấp theo DELTA_UPGRADE_PLAN — 24/10/2026

Đã triển khai bản **local review**, chưa thay public production. Xem trạng thái
và evidence chi tiết tại [plan §11](../docs/DELTA_UPGRADE_PLAN.md#11-thực-thi-nâng-cấp--24102026).
Baseline A/B/C vẫn là mặc định. Selector trong Atlas/Stock/Financial cho phép xem
P1/P3 bằng research preview **chưa promote**, có links trong Lab. Source/usefulness
review vẫn mở; dùng preview để nghiệm thu, không coi là production model.

- Home ưu tiên global search; Stock có bốn tabs và sáu cards kể cả null.
- Atlas có tabs, size bars, median/IQR và filter/table đồng bộ URL; Financial
  chỉ tải distribution/profile trước, matrix/members khi mở; Lab tách ba tabs.
- Inter + JetBrains Mono bundle local; body 15px, table 14px, caption/canvas ≥12px.
- URL interactions pin `revision` (parent SQLite + preview manifest digest) và model `version`; revision
  khác bị từ chối hiển thị; API cũng trả 409 khi request revision/version cũ.
  Identifiers/units/availability và raw components không bị lớp dịch thay đổi. Request cache bounded 80 entries/5 phút, dedup,
  abort khi bỏ subscription, timeout 75 giây, retry manual; không giữ số cũ dưới
  header mã/kỳ mới. `include_points=false` trả profiles với `points_included=false`,
  không sửa cached snapshot. Browser không tính model/quality metrics.
- API indicator dùng typed availability, giữ decimal text/null; pilot5 dependencies
  và calculation details có hash/manifest proof. Hai Z FY2024 BRC/VNM đã nối riêng,
  không merge vintage hoặc tính lại bằng giá trên time machine.

Preview production local trong phiên: <http://127.0.0.1:3010> (API 8020).
Để dựng lại cùng cấu hình, từ root:

```powershell
$env:DELTA_API_URL='http://127.0.0.1:8020'
npm --prefix web/frontend ci
npm --prefix web/frontend run build
python scripts/start_delta_terminal.py --production --web-port 3010 --api-port 8020
```

Không có model mới trong SQLite: hash vẫn
`66c9b0a48722d5d589e6b15ffae78b22de51162132b0681a7d3d133d4f4dc4f1`.
API catalog bổ sung `metadata.bundle_revision` theo graph manifests thật;
`metadata.database_sha256` giữ parent SQLite hash, `variants` liệt kê các preview.
Sidecar R1 riêng có 202 snapshots/186.228 observations, không sửa SQLite baseline.
Presentation revision local: `ed490fe068722f6b10ec1a545f87bafdfcdd27d5561283579a33188d8f24af80`.
Chạy dev mặc định vẫn dùng `python scripts/start_delta_terminal.py`.
Nếu dùng production port khác, build với `DELTA_API_URL` tương ứng trước.

Kiểm tra engineering:

```powershell
$env:PYTHONPATH="$PWD/.tools/market-runtime;$PWD/.tools/research-runtime;$PWD/.tools/web-runtime;$PWD/src;$PWD/tests;$PWD/web/backend"
$env:TEMP="$PWD/.tmp/upgrade-tests"
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
python -m unittest unit.test_indicator_reference unit.test_terminal_api unit.test_terminal_previews unit.test_terminal_alignment unit.experiments.test_upgrade_reference -v
python scripts/verify_delta_terminal.py --check-sources
python scripts/verify_delta_research_preview.py
python scripts/verify_delta_upgrade_r1.py data/experiments/delta_upgrade_r1_v1/results/09fa9b1ea51d861edbd5
python -m compileall -q src tests scripts run.py web/backend
node --check web/app.js
node scripts/test_delta_frontend.cjs
npm --prefix web/frontend run typecheck
npm --prefix web/frontend run build
```

Browser tests dùng Playwright optional (hoặc `PLAYWRIGHT_MODULE` trỏ runtime có
sẵn), `CHROMIUM_EXECUTABLE` có thể trỏ Edge/Chrome local. Với server 3010 đang chạy:

```powershell
node scripts/verify_delta_ui.cjs
```

Output screenshots/verification nằm trong `.tmp/upgrade-ui/final/`. Suite kiểm
25 responsive cases, caption/canvas font, FPT/VNM/HPG, deep fetch/mount, URL history,
keyboard focus, request race, 503/retry và CSS zoom 200%. Không thay thế ba người
usability hoặc browser/assistive-technology audit đầy đủ. Local performance có
script `measure_delta_ui.cjs`; cần bản HEAD baseline dựng riêng ở port 3011, cùng
API đã warm. Kết quả không phải cold-start/public SLA.

Full repository gate cuối chạy hết 984 tests, 1 error và 4 optional Streamlit skips;
fixture legacy `artifacts/financial_pit/fin-pit-1a-20261004T015420Z-continuation-preflight-v2/next_network_proposal.json`
không tồn tại. Không hạ assertions hoặc giả evidence để làm gate PASS.

Release còn chờ human acceptance/public preview. `publish_hf_data.py --dry-run`
đã xác minh **12 files** gồm SQLite/manifest, hai package indicator, hai supplementary
JSON và cặp manifest/CSV Z bổ sung và cặp R1 presentation/manifest. `data-files.txt` đã cập nhật; **chưa upload**.
Cần publish đúng danh sách, pin Dataset commit đã verify, deploy API rồi frontend;
kiểm FPT6, VNM F missing, HPG unavailable, Z FY2024 và revision/deep links từ URL
công khai. Ghi release commit + bundle hash + Dataset revision + model run cùng
bộ trước promotion; rollback về frontend/API/Dataset tương thích trước đó.


## Bổ sung bộ sáu chỉ số đã review

Trang Tra cứu cổ phiếu có panel EPS/P/E/P/B/F/M/Z độc lập với sáu core ratios của B/C.
API `/api/v2/indicators/{ticker}` đọc ba nguồn có hash được chốt trong
`configs/product/indicator_reference_v1.json`: compute-first có 85 numeric reference rows/11 mã,
pilot5 có 29/30 numeric cells trên 5 mã. Pilot5 là một phần dữ liệu đã tổng hợp;
**không cộng hai counter thành coverage mới**, không gọi 85 rows là 85 mã.
Hai Z FY2024 BRC/VNM trong archived reconciliation đã được nối riêng theo manifest; không merge vào pilot5 hoặc đổi vintage.

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

- Frontend: Next App Router, TypeScript, React, Tailwind, Lucide, ECharts, TanStack Table. Font Inter/JetBrains Mono được bundle local. Controls dùng native HTML và components riêng, không phụ thuộc shadcn/ui.
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

- Dữ liệu vẫn không vào Git. `python scripts/publish_hf_data.py` kiểm tra hash rồi upload bundle + ba nguồn indicator và hai JSON supplementary lên Dataset công khai `ngyen/delta-intelligence-data`, đồng thời cập nhật `deploy/render/data-files.txt`.
- Backend: Render đọc `render.yaml` (free, Singapore), build `deploy/render/Dockerfile`, tải data lúc build; API vẫn kiểm tra checksum lúc startup và fail-closed. Gói free ngủ sau ~15 phút không truy cập, lần mở đầu có thể chờ ~1 phút.
- Frontend: Vercel project root `web/frontend`, biến `DELTA_API_URL=<Render URL>` cho cả build và runtime (rewrite được chốt lúc build).
- Khi export bundle mới: chạy lại `publish_hf_data.py`, commit `data-files.txt` nếu đổi, rồi Manual Deploy trên Render.

Chưa có auth hoặc multi-user; link demo công khai cho bất kỳ ai có URL.

### Ưu tiên nâng cấp sau deploy — rà soát ngày 24/10/2026

Plan thực thi chi tiết và evidence mới nằm tại
[DELTA_UPGRADE_PLAN](../docs/DELTA_UPGRADE_PLAN.md): typography/design tokens,
screen flows, coverage ledger, source QA, preprocessing/k experiments và acceptance gates.
Các ý dưới đây là bản tóm lược; stage/protocol chi tiết theo plan này.

Đã đọc bản public `https://delta-intelligence-omega.vercel.app` qua trình duyệt:
FPT có đủ EPS/P/E/P/B/F/M/Z trong pilot FY2025; HPG hiện báo chưa có gói
indicator đã review dù có sáu core ratios. Atlas C cuối 2025 hiển thị
479/663/6 thành viên và silhouette 0,1657. Đây là các điểm kiểm tra mẫu,
không phải chứng nhận toàn bộ deployment.

Ưu tiên stage tiếp theo:

1. **Kiểm kê coverage indicator trước khi bổ sung số.** Lập bảng mã × kỳ ×
   EPS/PE/PB/F/M/Z từ các kết quả đã có, phân biệt chưa nối adapter, thiếu input,
   chưa tính và chưa review. Đối chiếu hai Z references chưa được nối. Không
   suy coverage EPS/P/E/P/B/F/M/Z từ coverage sáu ratios của B/C. Chỉ mở rộng
   hiển thị cho các kết quả đã xác minh; acquisition hoặc tính thêm cần stage riêng.
2. **Làm rõ trang doanh nghiệp.** Đưa sáu chỉ số lên vùng đầu, giữ sáu ô kể cả
   thiếu, hiển thị kỳ/ngày giá/đơn vị/lý do thiếu dễ đọc. Tách tổng quan, tài
   chính, phân cụm và nguồn thành các vùng điều hướng rõ. Thêm bảng lịch sử
   kỳ có sẵn, công thức đúng biến thể và các thành phần score nếu nguồn có.
   Không biến selector các gói/vintage nội bộ thành thao tác chính của người xem.
3. **Làm rõ Atlas từ artifacts hiện có.** Cho xem đồng thời quy mô cụm và hồ
   sơ median/IQR theo từng feature, ticker đại diện theo quy tắc công khai,
   bảng đối chiếu A/B/C và các trục gợi ý có lý do. Không so đơn vị khác nhau
   trên cùng thang raw; không gọi hình chiếu 2D là chất lượng toàn mô hình.
   Nhãn mô tả kinh tế phải dựa trên profile, không tự gán tốt/xấu theo cluster ID.
4. **Review mô hình thành stage nghiên cứu riêng.** Kiểm tra đơn vị, mẫu số,
   scope và outliers của inputs; phân tích feature contribution và ổn định
   qua thời gian. Viết protocol thí nghiệm đối chứng trước khi đổi scaler,
   transform, outlier policy, k hoặc algorithm; chỉ chạy sau owner duyệt theo
   `AGENTS.md`. Giữ A/B/C baseline để đối chiếu; không chọn phương án chỉ vì
   hình scatter trông tách rõ hoặc vì portfolio returns.

Nghiệm thu nâng cấp cần kiểm cả mã đủ sáu chỉ số (FPT), mã thiếu một chỉ số
(VNM), mã chưa có gói indicator (HPG), chuyển kỳ/vintage và mobile. Báo coverage
theo mã và kỳ thực tế; không hứa đủ toàn thị trường khi inputs chưa có.

### Plan bàn giao cho agent deploy

Phạm vi: hoàn tất một bản demo dùng chung với frontend Vercel, API Render và
presentation data trên Hugging Face. Cấu hình đã tồn tại trong repo; sự tồn tại
của cấu hình không xác nhận services đã deploy hoặc URL đã hoạt động.

1. **Kiểm kê trạng thái trước khi tạo service.** Đọc `AGENTS.md` và runbook này;
   kiểm tra branch/commit, working tree, project Vercel đã liên kết, Render service
   và Dataset hiện có. Tái sử dụng đúng project/service của owner để tránh tạo
   bản trùng. Không in token hoặc đưa credentials vào Git; nếu thiếu đăng nhập,
   yêu cầu owner đăng nhập qua CLI/dashboard của dịch vụ tương ứng.
2. **Xác minh dữ liệu local.** Chạy `python scripts/publish_hf_data.py --dry-run`
   và `python scripts/verify_delta_terminal.py --check-sources`. Kiểm tra diff
   của `deploy/render/data-files.txt` vì dry-run có ghi lại danh sách này. Cần đủ
   SQLite, bundle manifest, ba cặp CSV/manifest indicator và hai JSON supplementary trong danh sách.
   Không export lại nếu bundle hiện tại đã hợp lệ; không chạy lại model.
3. **Hoàn tất nguồn dữ liệu.** Kiểm tra Dataset `ngyen/delta-intelligence-data`
   có đủ mười hai file và bytes khớp local. Chỉ chạy publisher nếu thiếu hoặc cần
   cập nhật. Ưu tiên pin download URL vào một Dataset commit đã xác minh để
   rebuild có thể tái lập; giữ kiểm tra hash lúc startup. Không upload PDF gốc,
   canonical JSONL nhiều GB, secrets hoặc dữ liệu ngoài danh sách cho demo.
4. **Hoàn tất backend Render trước.** Dùng `render.yaml` và
   `deploy/render/Dockerfile`, context repository root. Xác nhận downloader dùng
   đúng Dataset/revision; kiểm tra cách truyền `DATA_BASE_URL` thực tế trước khi
   đổi nguồn. Deploy commit đã chọn, theo dõi build/startup và thử trực tiếp
   `GET`/`HEAD /api/v2/health`, catalog, snapshot và chỉ số FPT. Lỗi tải data,
   thiếu indicator hay hash sai phải được xử lý trước bước frontend.
5. **Hoàn tất frontend Vercel.** Dùng project root `web/frontend`, cài bằng lockfile,
   đặt `DELTA_API_URL` bằng HTTPS origin của API Render, không thêm `/api/v2`.
   Đặt biến cho đúng Preview/Production cần deploy. Build lại sau khi đổi biến
   vì rewrite Next được chốt lúc build. Kiểm tra preview trước rồi publish
   production; URL production không được proxy về `127.0.0.1:8010`.
6. **Nghiệm thu từ URL công khai.** Kiểm tra đủ năm trang và refresh deep link;
   request `/api/v2` phải đi qua domain frontend thành công. Kiểm tra Atlas A/B/C,
   C năm 2025 có 479/663/6 mã, ma trận FY2025, tìm FPT, giá raw/adjusted riêng,
   sáu chỉ số FPT, F-score thiếu của VNM và empty state khi không có dữ liệu.
   Giữ toàn bộ tiếng Việt và cảnh báo ex-post/PIT/quality. Thử desktop/mobile,
   kiểm tra console/network và cold start sau thời gian Render ngủ.
7. **Bàn giao kết quả.** Ghi URL frontend/API/Dataset revision, Git commit,
   cấu hình biến môi trường không chứa secrets, kết quả kiểm tra và giới hạn
   cold start vào runbook này. Báo riêng bước nào chưa kiểm được; chỉ gọi deploy
   hoàn tất khi URL công khai trả dữ liệu thật. Giữ deployment tốt trước đó để
   rollback frontend/backend cùng phiên bản dữ liệu tương thích.

Kiểm tra code nếu agent có sửa: targeted API/indicator tests, frontend typecheck
và production build, `python -m compileall -q src tests scripts run.py`,
`node --check web/app.js`. Targeted PASS không thay thế full repository gate.
Stage này chỉ deploy presentation layer: không đổi features, labels, scaler,
cluster count hoặc mở PIT/backtest gates; việc review chất lượng cụm là stage riêng.


### R1 preview: build và kiểm tra

`python scripts/export_delta_research_preview.py --connect` chỉ đọc source run R1
đã hoàn tất, ghi sidecar mới có content identity và pin pointer; không fit lại,
không ghi đè SQLite. Nếu đã có sidecar đúng hash thì tái sử dụng. Dataset mới
phải có **cả parent SQLite/manifest và R1 sidecar/manifest** trước khi start API;
thiếu/sai checksum dừng, không tự thay candidate bằng baseline.

`python scripts/verify_delta_research_preview.py` đối chiếu 202 source models,
labels/identity/cohort, saved metrics/median/IQR và raw-feature presentation means.
API registry không gọi sklearn hoặc tính diagnostics mới. Matrix theo đúng
`version` B và `market_version` A; members filter dùng `matrix_market_version`.
Version không tồn tại hoặc revision khác trả 409, không fallback sang labels khác.
Baseline vẫn là mặc định khi URL không chọn version; preview có badge/warning
NOT_PROMOTED trên mọi workspace. Chỉ có các peer examples đã export, không phải
nearest-peer service cho mọi mã và không phải taxonomy cùng ngành.

Ví dụ local:
<http://127.0.0.1:3010/atlas?kind=combined&date=2025-12-31&version=r1%3AP3%3Ak2%3A09fa9b1ea51d861edbd5>.

Khi release, pin **Dataset commit** vừa publish và cấu hình `DATA_BASE_URL` bằng
`resolve/<commit>` trước backend build; không dùng mutable `main` để gọi release
reproducible. Human source/peer review, ba người usability, public/cold-start và
fixture legacy vẫn là các điều kiện mở được ghi trong plan §11.
