# Hướng dẫn cho automated coding/research agents

Đọc `README.md`, `docs/README.md`, `docs/PROJECT_OVERVIEW.md`, `docs/PROJECT_MAP.md`, `docs/ROADMAP.md` và `CONTRIBUTING.md` trước khi thay đổi kiến trúc. Tất cả thay đổi project nằm trong `SourceCode`; không sửa các PDF dưới `../TaiLieu`.

## Architecture boundaries

- `ingestion` chỉ acquire/normalize/reconcile và ghi provenance; không chọn model.
- `features` không gọi network; mọi feature phải đăng ký metadata trong feature registry.
- `clustering` chỉ fit/predict theo interface chung; cluster metrics nằm ở `evaluation`.
- `experiments` validate protocol, orchestrate và ghi immutable artifacts; reporting không fit model.
- `backtest` và portfolio metrics không được tham gia chọn cluster/model.
- `product`/`web` chỉ đọc versioned experiment artifacts, không recompute feature/model.

## Ranh giới M1/M2/M3

- **M1:** `SOURCE_SMOKE` thật 3–5 mã chỉ mở `REPRESENTATIVE_PILOT`; chỉ PASS pilot 50–60 mã, >=5 năm mới mở planning `M1_SCALE` >=300. Synthetic không pass gate thật; `EXTENDED_SCALE` 5–15 năm không có cap 350.
- **M2:** giữ deterministic static K-Means baseline; PCA/comparator đánh giá riêng. Không triển khai concrete dynamic algorithm trước khi `docs/research/DYNAMIC_CLUSTERING_REVIEW.md` phê duyệt.
- **M3:** chỉ final backtest sau methodology freeze; dashboard tiêu thụ artifact, không điều khiển research.

## Research invariants

- Cluster quality, temporal stability và portfolio performance là ba lớp metric độc lập.
- Không chọn `k`/algorithm bằng return, Sharpe hoặc ROI. Sharpe chỉ thuộc portfolio evaluation.
- Monthly independent K-Means + ARI/transition tracking không được gọi là Dynamic Clustering.
- Không fit scaler/PCA bằng future hoặc holdout information; không xóa evidence đầy đủ vì kết quả bất lợi.

## Data invariants

- Raw/canonical/experiment artifact là immutable; sửa policy tạo version/run mới.
- Không dùng current ticker membership làm historical universe; join bằng historical `security_id` interval.
- Không forward-fill missing price, không đổi missing thành zero, không trộn raw/adjusted basis.
- Chỉ dùng row có `available_at <= decision_at`; financial statement phải point-in-time và revision-aware.
- Real clustering cần ít nhất ba calendar years usable observed history; mã ngắn lịch sử là `REFERENCE_ONLY`.
- Market canonical dùng VND/share, volume dùng shares, traded value dùng VND; multiplier phải có evidence và không được suy từ magnitude.
- Reconciliation so theo canonical entity/key ở field level; `source`/`fetched_at` khác nhau không tự tạo value conflict. Không average và không dùng source priority nếu policy chưa approved/versioned.
- Provider report ID, canonical report identity và reconciliation comparison key là ba khái niệm khác nhau; không làm mất provider provenance.

## Testing requirements

- Chạy targeted tests cho subsystem bị ảnh hưởng và `python -m compileall -q src tests scripts run.py`. Chạy full repository gate khi stage hoặc thay đổi code/data/research warrant; tránh lặp full suite khi chỉ sửa documentation/configuration.
- Thay pipeline phải chạy `configs/data/synthetic_smoke.example.json`; source smoke template phải tiếp tục fail-closed. Thay web phải chạy `node --check web/app.js`.
- Giữ và migrate assertion cũ. Không xóa/giảm test để làm migration pass.
- Kiểm tra import cũ, JSON config/schema và Markdown link trước khi xóa file superseded.

## Documentation requirements

- Viết Markdown bằng tiếng Việt; giữ project terms bằng English khi rõ nghĩa hơn.
- Contract/methodology thay đổi phải cập nhật `docs/DECISIONS.md`, `CHANGELOG.md`, config và tests liên quan.
- `docs/README.md` là START HERE; không tạo status/audit/archive document rời.
- Giữ `docs/data/kbs_pilot_semantics.md` đúng path vì immutable legacy evidence có thể tham chiếu.

## Forbidden shortcuts

Không hard-code feature validity bằng prefix; không sinh Sharpe trong active feature snapshot; không duplicate metrics trong model; không đặt placeholder thành kết quả; không crawl lớn trước source/pilot gates; không bypass login/anti-bot/paywall/access control; không thêm microservice, broker, Kubernetes, auth/news/sentiment/database migration ngoài active milestone.

## Single-agent execution policy

DELTA currently uses a single-agent execution workflow. Người dùng tự chọn model cho
mỗi Codex session theo độ khó; repository không prescribe hoặc pin model.

```text
UNDERSTAND TASK
        ↓
READ ONLY NECESSARY CONTEXT
        ↓
IDENTIFY EXACT CURRENT STAGE
        ↓
IMPLEMENT ONLY THAT STAGE
        ↓
RUN RELEVANT TESTS
        ↓
SELF-REVIEW AGAINST THE STAGE CONTRACT
        ↓
UPDATE EXECUTION PROGRESS / HANDOFF
        ↓
STOP
```

Rules:

1. Chỉ thực hiện một DELTA stage mỗi session, trừ khi người dùng yêu cầu rõ khác đi.
2. Không tự động tiếp tục sang stage kế tiếp.
3. Không spawn hoặc delegate cho subagent.
4. Không đọc lại toàn repository khi đã biết exact path.
5. Tránh phân tích trùng lặp hoặc implementation thay thế khi không cần thiết.
6. Preserve evidence thay vì recompute expensive work.
7. Long crawl chạy local; không continuously poll.
8. Self-review là bắt buộc trước khi đánh dấu stage complete.
9. Evidence, tests và artifacts quyết định `PASS`/`PARTIAL`/`BLOCKED`/`FAIL`, không phải code existence.

Nếu stage đề xuất thay đổi methodology-sensitive — gồm nới 100% observation rule,
price-basis acceptance, inferred provider transformation, expected-session semantics,
historical identity, financial PIT, research eligibility, M2 methodology, hoặc final
canonical/research-sample freeze — phải ghi rõ `MANUAL_REVIEW_REQUIRED` và STOP khi
cần approval. Người dùng quyết định model hoặc cách review; repository không pin model.
