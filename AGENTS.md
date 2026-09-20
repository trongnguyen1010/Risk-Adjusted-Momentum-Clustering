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

- Trước và sau mỗi phase: `python -m unittest discover -s tests -v` và `python -m compileall -q src tests scripts run.py`.
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

## Agent orchestration and usage policy

Main/default model: GPT-5.6 Terra High

Default spawned agent: GPT-5.6 Terra High

Main agent là orchestrator. Với mỗi task, dùng routing sau:

```text
UNDERSTAND TASK
        ↓
READ ONLY NECESSARY CONTEXT
        ↓
CAN MAIN AGENT SAFELY DO IT?
        │
        ├── YES → do it directly
        │           ↓
        │     NAMED DELTA STAGE?
        │           │
        │           ├── YES → verifier
        │           └── NO  → STOP
        │
        └── NO
             ↓
      NEED CODEBASE DISCOVERY?
        │
        ├── YES → explorer
        └── NO  → skip explorer
             ↓
         implementer
             ↓
          verifier
             ↓
     methodology ambiguity?
        │
        ├── NO → STOP
        └── YES
             ↓
          auditor
             ↓
            STOP
```

Usage-efficiency rules:

1. Không spawn subagent nếu main Terra High agent có thể hoàn thành task an toàn.
2. Với mọi named DELTA execution stage (A0–A6, B0–B5, Canonical Enriched v2,
   Feature Rebuild, Expanded EDA, Freeze M2 Sample), verification là bắt buộc
   kể cả khi main agent tự thực hiện implementation.
   Implementer subagent là optional; verifier thì không optional.
3. Không tự động spawn toàn bộ roles.
4. Explorer là optional và phải bỏ qua khi đã biết file hoặc symbol liên quan.
5. Không yêu cầu hai agent độc lập giải cùng một implementation problem trừ khi cần independent verification rõ ràng.
6. Tránh để nhiều agent đọc lại toàn bộ repository.
7. Parent agent nên hand off exact stage spec, exact paths và relevant context khi có thể.
8. Mỗi cycle chỉ một implementation stage.
9. Implementer phải STOP sau stage được giao.
10. Verifier read-only và không được âm thầm sửa implementation.
11. Auditor chỉ dùng để escalation.
12. Không dùng Sol cho ordinary coding, boilerplate, docs updates, test writing hoặc routine verification.
13. Giữ concurrency thấp; workflow bình thường chỉ có tối đa một active implementation path.
14. Không poll local crawl dài bằng agents.
15. Crawl dài chạy local và review từ artifacts/logs tạo ra.
16. Preserve evidence thay vì repeatedly recomputing expensive work.

Auditor (Sol) normally chỉ được gọi khi có ít nhất một điều kiện sau:

```text
methodology changed
research invariant touched
canonical semantics changed
expected-session semantics ambiguous
historical identity semantics changed
financial PIT logic changed
price-basis reconciliation changed
unit/reconciliation policy changed
research eligibility changed
M2 methodology decision
final canonical freeze
final research sample freeze
large cross-module architecture change
unexpected regression with unclear cause
tests and generated research evidence disagree
an implementation proposes weakening the 100% observation rule
```

Routine implementation không yêu cầu Sol.

DELTA stage workflow:

```text
MASTER PLAN
    ↓
ONE STAGE
    ↓
IMPLEMENT
    ↓
VERIFY
    ↓
AUDIT ONLY IF NECESSARY
    ↓
REPORT
    ↓
STOP
```

Không tự động tiếp tục sang DELTA stage kế tiếp.
