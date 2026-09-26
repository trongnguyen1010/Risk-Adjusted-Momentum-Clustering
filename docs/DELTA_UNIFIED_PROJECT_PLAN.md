# DELTA — Unified Project Roadmap & Handoff Plan v1.0

**Project:** Risk-Adjusted Momentum Clustering for Vietnamese Equities  
**Active branch baseline:** `m1-cafef-primary-experiment`  
**Reference commit:** `18a99bddefc34c63065c40ae1d50a9dfaeaf0582`  
**Date:** 26/09/2026  
**Purpose:** Tài liệu thống nhất hướng đi từ trạng thái hiện tại đến hết M2/M3 và các nhánh mở rộng, để thành viên mới có thể tiếp nhận công việc mà không cần đọc lại toàn bộ lịch sử C1–C8.

---

## 1. Mục tiêu tài liệu

Tài liệu này là **project execution + handoff plan**. Nó không thay thế artifact khoa học hay `docs/CURRENT_STATUS.md`, nhưng định nghĩa rõ:

- project đang ở đâu;
- M1 đã hoàn tất những gì;
- M2 sẽ chạy theo protocol nào;
- M3 sẽ đánh giá portfolio/backtest như thế nào;
- financial/fundamental extension (F-Score, M-Score, Z-Score) nằm ở đâu;
- input/output/gate của từng stage;
- thành viên mới phải đọc gì, chạy gì và bàn giao gì.

Mỗi khi có methodology decision mới, phải cập nhật document này theo version mới thay vì sửa ngầm.

---

## 2. Đích cuối của DELTA

DELTA không chỉ là crawler hay một lần chạy K-Means. Mục tiêu end-to-end là:

```text
Market Data Foundation
        ↓
PIT-safe Feature Snapshots
        ↓
Static Clustering Baseline
        ↓
Approved Comparators
        ↓
Temporal Stability / Cluster Movement
        ↓
Methodology Freeze
        ↓
Portfolio / Backtest Evaluation
        ↓
Dashboard + Thesis Artifacts
```

Hai hướng nghiên cứu được tách rõ:

1. **Critical path hiện tại:** market-only clustering → temporal evaluation → M3 backtest.
2. **Optional research extension:** market + fundamental/accounting scores sau khi Financial PIT được giải quyết.

Không được để nhánh optional làm chậm critical path nếu mentor không yêu cầu.

---

## 3. Trạng thái hiện tại

### 3.1 M1 — Market Data Foundation

M1 đã **hoàn tất cho market-only experiment preparation**.

Verified state tại snapshot `2026-08-28`:

| Chỉ số | Giá trị |
|---|---:|
| Candidate universe | 952 |
| Feature complete | 922 |
| Market-feature-ready | 905 |
| Market-readiness failures | 47 |
| Latest-253 complete | 922 |
| Latest-253 incomplete | 30 |
| Historical identity ready | 0 |
| Research ready | 0 |
| Deferred expansion | 148 |

`905` chỉ là số mã market-ready ở **latest snapshot**, không phải fixed historical universe.

### 3.2 M2-PREP

M2-PREP đã audit:

- eligibility theo từng snapshot;
- feature set;
- preprocessing support;
- algorithms;
- metrics;
- literature;
- monthly readiness discontinuities;
- runner/input-loader gaps.

Kết quả: `MANUAL_REVIEW_REQUIRED` vì một số methodology choice chưa freeze.

### 3.3 Hai readiness discontinuities quan trọng

- `2023-05 → 2023-10`: thiếu VNINDEX row ngày `2023-05-15`, làm `beta_126` fail theo strict paired-return window.
- `2025-02 → 2026-01`: ngày `2025-02-03` là open session nhưng canonical market có 0 equity rows; `mom_252` cần 253 real prices nên readiness fail cho tới khi gap ra khỏi rolling window.

Không forward-fill, không timeline-compress, không tạo observation giả để “sửa” các đoạn này.

---

## 4. Các nguyên tắc bất biến

Các rule dưới đây áp dụng cho tất cả thành viên và tất cả stage:

1. **No synthetic market data.** Không ffill, bfill, interpolation, previous-close substitution, missing price→0, missing volume→0, fake zero-return.
2. **PIT:** dữ liệu chỉ được dùng nếu `available_at <= decision_at` khi domain có timing semantics.
3. **Per-snapshot universe:** không lấy terminal 905 áp ngược lịch sử.
4. **Evidence controls status:** code tồn tại không đồng nghĩa methodology approved.
5. **Cluster model selection không dùng portfolio performance.** Sharpe, CAGR, ROI, future return không chọn feature/k/algorithm/PCA.
6. **M2 và M3 tách biệt:** M2 đánh giá clustering; M3 mới đánh giá portfolio.
7. **Independent monthly clustering + ARI không được gọi là Dynamic Clustering.**
8. **Dynamic Clustering chỉ triển khai sau dedicated review/approval.**
9. **Artifact immutable:** output hoàn chỉnh không sửa tại chỗ; thay methodology/config phải tạo version/run mới.
10. **Long run:** agent chỉ chuẩn bị + sanity check + exact command; user chạy long job local, agent không poll/wait.

---

## 5. Eligibility contract cho M2

Khái niệm chính:

```text
market_experiment_eligible(t)
=
market_feature_ready_v2(t)
```

Tính tại chính snapshot `t`.

Phải tách biệt với:

- legacy `eligibility`;
- tradability;
- `historical_identity_ready`;
- `research_ready`.

M2 market-only là một scope nghiên cứu hẹp để phát triển clustering methodology. Nó không tự động tạo final historical research universe.

---

# PHẦN A — M2 CLUSTERING RESEARCH

## 6. M2 v1 — Quyết định methodology đề xuất để freeze

Do hiện tại không thể xin mentor ngay, project owner có thể freeze **Protocol v1** trước khi xem kết quả clustering. Nếu sau này mentor yêu cầu thay đổi, tạo Protocol v2 và không overwrite v1.

### 6.1 Development window

**Đề xuất:** `2023-11-30 → 2025-01-24`.

Lý do:

- 15 monthly snapshots liên tục;
- không có zero-readiness snapshot;
- eligible count 142–780;
- dài hơn nhiều so với pre-gap 4 tháng;
- không cần timeline compression;
- kết thúc trước systemic gap 2025-02-03.

### 6.2 Final M2 holdout

**Đề xuất:** `2026-02-27 → 2026-08-28`.

- 7 monthly snapshots;
- eligible count 253–905;
- nằm hoàn toàn sau development;
- không nối temporal metrics qua khoảng gap 2025-02→2026-01.

Holdout phải được seal; không dùng để chọn k, scaler, PCA hoặc algorithm.

### 6.3 Snapshot eligibility threshold

**Đề xuất v1:** `n_eligible >= 120`.

Đây là project protocol choice, không phải threshold lấy trực tiếp từ một paper. Nó đảm bảo ngay cả khi test `k=8` vẫn có trung bình khoảng 15 observations/cluster, đồng thời toàn bộ contiguous development window hiện tại pass.

Nếu snapshot <120: skip với reason rõ ràng; không gộp timeline.

### 6.4 Feature set

Giữ đúng 8 market features đã khóa:

- `mom_21`
- `mom_63`
- `mom_126`
- `mom_252`
- `vol_63`
- `mdd_126`
- `beta_126`
- `liquidity_21`

Không thêm financial features vào M2 v1.

### 6.5 Outlier policy

**Baseline v1: không winsorize / không clipping.**

Lý do: chưa có evidence để chọn quantile cụ thể; clipping có thể xóa extreme market behavior thật.

Extreme observations được giữ nhưng giảm ảnh hưởng thông qua scaling.

### 6.6 Scaling

**Default:** robust scaling per snapshot.

```text
x_scaled = (x - median) / IQR
```

Lý do:

- 8 feature có scale rất khác nhau;
- K-Means/Ward distance-sensitive;
- market features có heavy tails/outliers;
- robust scaling giữ observation thay vì xóa/clipping.

**Sensitivity comparator:** z-score scaling.  
Không dùng việc “z-score cho clustering đẹp hơn” để đổi default sau khi xem holdout.

### 6.7 K policy

Candidate range trên development:

```text
k = 2..8
```

Không chọn k riêng cho từng tháng.

Chọn **một global k** trên development và giữ cố định cho toàn bộ M2 evaluation/holdout.

Primary criterion:

1. median Silhouette cao nhất;
2. nếu gần/tie → median Davies–Bouldin thấp hơn;
3. Calinski–Harabasz + cluster balance là sanity diagnostics;
4. temporal stability dùng để kiểm tra robustness, không tự động override primary rule nếu chưa pre-register.

Không dùng return/Sharpe/ROI để phá tie.

### 6.8 PCA policy

PCA là **comparator branch**, không phải default pipeline.

```text
RobustScaler → PCA → K-Means
```

Component rule đề xuất:

- trong development, tìm smallest `n_components` đạt cumulative explained variance ≥90%;
- freeze thành một số component cố định;
- holdout không được tự chọn lại số component.

90% là project protocol choice, không phải threshold bắt buộc từ Pearson (1901).

### 6.9 K-Means convergence

Giữ exact-label convergence hiện tại cho Protocol v1 nếu deterministic tests vẫn pass. Không thêm tolerance parameter chỉ để tăng tuning surface.

### 6.10 Feature version

C8 feature snapshot `1.6.0` là active M2 input contract. Registry `1.5.0` giữ legacy compatibility. Không mutate C8 artifact; resolve bằng documentation/config version compatibility.

---

## 7. Algorithm plan cho M2

### 7.1 Primary baseline

**Static deterministic K-Means** per monthly snapshot.

Mục tiêu: tạo baseline đơn giản, reproducible và interpretable.

### 7.2 Comparator A

**Ward/Agglomerative** dùng cùng frozen preprocessing và cùng global k.

### 7.3 Comparator B

**PCA + K-Means** để kiểm tra feature correlation/dimension reduction ảnh hưởng cluster structure thế nào.

### 7.4 Third true clustering algorithm

Nếu yêu cầu “≥3 thuật toán phân cụm” được hiểu là ba family thuật toán độc lập, implement **GMM** sau baseline/comparator pipeline.

GMM phải freeze:

- covariance type;
- initialization;
- seed;
- regularization;
- singularity/failure behavior.

### 7.5 DBSCAN

Defer khỏi M2 v1. Current architecture chưa hỗ trợ đúng:

- noise label;
- variable cluster count;
- all-noise/one-cluster cases;
- birth/death temporal alignment.

### 7.6 Dynamic Clustering

Status: **NOT APPROVED**.

Literature candidate:

- Chakrabarti et al. (2006) — evolutionary clustering;
- João et al. (2023) — HMM/dynamic panel clustering;
- João et al. (2024) — persistence/shrinkage dynamic nonparametric clustering.

João et al. (2024) gần kiến trúc DELTA nhất, nhưng phải có dedicated methodology review trước implementation.

---

## 8. Metrics trong M2

### Cluster quality

- Silhouette
- Davies–Bouldin
- Calinski–Harabasz
- Inertia
- Cluster balance

### Temporal stability

- ARI
- NMI
- persistence probability
- migration rate
- transition matrix
- centroid drift
- entry/exit

### Không dùng trong M2 model selection

- Future return
- CAGR
- Sharpe
- Sortino
- ROI
- Calmar
- portfolio alpha
- information ratio
- turnover
- transaction-cost-adjusted return

---

## 9. M2 execution stages

### M2-R1 — Protocol Freeze

**Input:** M2-PREP artifact + plan này.  
**Action:** ghi methodology decision thành ADR/config versioned.  
**Output:** `configs/experiments/m2_market_only_v1.json` + decision artifact.  
**Gate:** mọi decision ở Section 6 được explicit, tests pass.  
**Không chạy real clustering.**

### M2-R2 — Market-only Runner Adapter

**Mục tiêu:** sửa runner hiện còn phụ thuộc legacy `eligibility`.

Required changes:

- explicit `market_only` mode;
- configurable eligibility field;
- no silent fallback;
- checksummed C8/M1 input adapter;
- strict research path giữ nguyên;
- current data artifacts không mutate.

**Gate:** unit/integration tests chứng minh terminal 905 không retrospective-filter lịch sử.

### M2-EXEC-A — Development k Selection

Chạy development window với K-Means `k=2..8`.

Output:

- per-snapshot diagnostics;
- aggregate median metrics by k;
- selected global k theo frozen rule;
- selected-k decision artifact.

Không dùng holdout.

### M2-EXEC-B — Baseline + Comparators

Chạy:

1. RobustScaler → K-Means;
2. RobustScaler → Ward;
3. RobustScaler → PCA → K-Means;
4. optional GMM nếu đã approved/implemented.

Outputs:

- assignments;
- cluster profiles;
- model/scaler/PCA parameters;
- quality metrics;
- temporal metrics;
- skipped snapshot reasons;
- immutable manifest.

### M2-VERIFY

Audit:

- config/input hashes;
- k frozen đúng rule;
- no future/holdout leakage;
- no portfolio metrics used in selection;
- temporal chain reset across gaps;
- deterministic rerun on bounded fixture;
- holdout opened only after development freeze.

### M2-REPORT / HANDOFF

Deliver:

- notebook/report cho mentor;
- final method description;
- selected k;
- comparator results;
- cluster profiles/interpretation;
- temporal stability narrative;
- limitations;
- exact M3 handoff package.

---

# PHẦN B — M3 PORTFOLIO / BACKTEST

## 10. M3 objective

M3 trả lời câu hỏi downstream:

> Cluster structure có giúp xây dựng/giải thích chiến lược luân chuyển danh mục khác benchmark hay không?

M3 **không được quay lại thay đổi M2 model** chỉ vì backtest đẹp/xấu.

---

## 11. M3-PREP — Backtest Protocol Freeze

Trước khi chạy portfolio phải freeze:

- cluster-to-portfolio rule;
- rebalance frequency;
- entry/exit rule;
- weight rule;
- transaction cost assumption;
- cash handling;
- benchmark series;
- return basis;
- missing-price/execution behavior;
- evaluation period;
- bootstrap/sensitivity nếu dùng.

Benchmark tối thiểu:

1. VNINDEX;
2. equal-weight eligible universe;
3. momentum-only baseline;
4. cluster-based strategy.

### M3 holdout caveat

M2 proposed holdout `2026-02..2026-08` chỉ nên mở sau M2 freeze. M3-PREP phải quyết định:

- **Preferred:** cập nhật dữ liệu về sau để có một new unseen portfolio evaluation window;
- **Fallback nếu thesis deadline:** dùng period hiện có nhưng ghi rõ đây là downstream evaluation period, không còn là untouched final research holdout nếu đã xem cluster diagnostics.

Không overclaim.

---

## 12. M3 metrics

Portfolio metrics tách khỏi cluster metrics:

- cumulative return / CAGR;
- annualized volatility;
- Sharpe;
- Sortino;
- maximum drawdown;
- Calmar;
- turnover;
- transaction costs;
- alpha/beta;
- information ratio.

Sharpe annualization phải ghi rõ frequency/serial-correlation assumption; không máy móc `sqrt(12)` nếu assumptions không phù hợp.

---

## 13. M3 execution stages

### M3-R1 — Freeze Strategy Contract

Versioned config, no backtest yet.

### M3-EXEC — Development Backtest

Chạy trên approved development/evaluation data theo frozen strategy. Không sửa cluster methodology.

### M3-VERIFY

Audit leakage, costs, benchmark alignment, missing price, turnover/cash, artifact hashes.

### M3-FINAL-EVAL

Chỉ mở final evaluation window sau freeze. Báo cả kết quả bất lợi.

### M3-REPORT / PRODUCT

Output:

- technical report;
- notebook reproducible;
- benchmark comparison;
- sensitivity/limitations;
- product bundle/dashboard inputs.

---

# PHẦN C — OPTIONAL FUNDAMENTAL EXTENSION

## 14. Vì sao cân nhắc M-Score, F-Score, Z-Score

Market-only features mô tả hành vi giá/risk/liquidity. Financial scores bổ sung company-quality dimensions:

- **Piotroski F-Score:** profitability, leverage/liquidity, operating efficiency;
- **Beneish M-Score:** accounting manipulation / earnings-quality screening;
- **Altman Z-Score:** financial distress / solvency risk.

Các score này có thể giúp cluster profile dễ giải thích hơn và kiểm tra liệu firm fundamentals có tạo thêm structure ngoài market behavior hay không.

---

## 15. Điều kiện bắt buộc trước financial extension

Không đưa financial score vào historical clustering nếu chưa resolve:

- report identity;
- statement scope;
- publication time;
- revision/restatement;
- `available_at`;
- period semantics;
- sector applicability;
- exact formula/reference.

Rule:

```text
available_at <= decision_at
```

### Không copy custom score từ website nếu chưa biết formula

Các biến thể như `M-Score**`, `Z'`, `Z''` hoặc custom ML score chỉ được dùng khi:

- exact formula/model known;
- paper/source traceable;
- input field semantics mapped;
- industry applicability documented.

Không đưa cả Z, Z' và Z'' cùng lúc vào clustering nếu chúng highly correlated; chọn variant phù hợp hoặc chỉ dùng diagnostic.

---

## 16. Fundamental extension experiment design

Nếu PIT được giải quyết, tạo stage riêng, không sửa M2 v1:

```text
Experiment A: Market-only
Experiment B: Fundamental-only
Experiment C: Market + Fundamental
```

Feature candidate priority:

1. Piotroski F-Score;
2. Altman Z variant phù hợp;
3. Beneish M-Score;
4. selected raw ratios nếu literature + PIT cho phép.

Evaluation vẫn dùng cluster quality + temporal stability. Không dùng Sharpe/return để quyết định feature set.

Nếu combined feature space cải thiện interpretability/stability thì ghi nhận như evidence; nếu không thì giữ market-only baseline.

---

# PHẦN D — PRODUCT / DASHBOARD

## 17. Product Layer direction

Dashboard không tự fit model; chỉ consume versioned research artifacts.

Một company detail page có thể hiển thị:

- current cluster;
- cluster profile;
- cluster transition timeline;
- momentum/risk/liquidity features;
- price history;
- optional F/M/Z score timeline sau PIT approval;
- explanation/definitions;
- artifact/version provenance.

Có thể tham khảo UI dạng score timeline + closing price, nhưng DELTA phải giữ methodology/provenance riêng.

---

# PHẦN E — HANDOFF CHO THÀNH VIÊN

## 18. Vai trò đề xuất

### Project/Research Coordinator

- owner methodology/version;
- approve stage transition;
- review manifests/results;
- giữ `CURRENT_STATUS` và plan này đồng bộ.

### Data/PIT Owner

- market/fundamental source semantics;
- identity/PIT;
- input artifacts/hashes;
- không sửa clustering methodology.

### Clustering Owner

- preprocessing;
- K-Means/Ward/PCA/GMM;
- k-selection;
- cluster/temporal diagnostics;
- không chạy portfolio tuning.

### Evaluation/Backtest Owner

- M3 strategy contract;
- execution/cost/benchmark;
- portfolio metrics;
- không thay M2 model theo backtest output.

### Product/Reporting Owner

- notebook/slide/dashboard;
- chỉ consume verified artifacts;
- không recompute scientific logic trong UI.

---

## 19. Handoff package bắt buộc cho mỗi stage

Mỗi thành viên khi bàn giao phải có:

1. **Stage name + status:** PASS / PARTIAL / MANUAL_REVIEW_REQUIRED / BLOCKED.
2. **Parent commit SHA.**
3. **New commit SHA.**
4. **Input artifact paths + hashes.**
5. **Config path + hash.**
6. **Output artifact path + manifest.**
7. **Tests/checks đã chạy.**
8. **Scientific headline counts.**
9. **Known limitations.**
10. **Things explicitly NOT done.**
11. **Exact next stage.**
12. **Exact command cho long-run nếu có.**

Không handoff bằng câu “code xong rồi” mà không có evidence.

---

## 20. Onboarding checklist cho member mới

Member mới đọc theo thứ tự:

1. `docs/CURRENT_STATUS.md`
2. document plan này
3. `docs/METHODOLOGY.md`
4. `docs/research/EXPERIMENT_PROTOCOL.md`
5. `docs/research/LITERATURE_MATRIX_COMPLETE.md`
6. artifact của stage mình nhận
7. tests liên quan

Sau đó phải trả lời được:

- input nào là source of truth?
- stage đang ở đâu?
- output nào immutable?
- rule nào không được thay?
- gate pass/fail dựa trên gì?
- next stage chính xác là gì?

---

## 21. Branch / commit discipline

Khuyến nghị:

- một stage = một commit chính hoặc một corrective sequence rõ lineage;
- commit message theo stage, ví dụ:
  - `prep(m2): freeze market-only protocol v1`
  - `feat(m2): add market-only experiment adapter`
  - `experiment(m2): run development clustering baseline`
  - `verify(m2): audit market-only clustering results`
  - `prep(m3): freeze portfolio evaluation protocol`
- không rewrite historical evidence để “làm đẹp” kết quả;
- Git history là archive; active docs chỉ giữ current guidance.

---

## 22. Risk register

| Risk | Ảnh hưởng | Control |
|---|---|---|
| terminal-universe look-ahead | bias historical clustering | per-snapshot eligibility |
| missing market sessions | invalid rolling features | strict no-imputation windows |
| benchmark gap | beta propagation | diagnose/skip by explicit rule |
| arbitrary preprocessing | result shopping | freeze before clustering |
| k selected by returns | backtest overfit | cluster-quality-only selection |
| holdout repeatedly inspected | methodology overfit | seal + one-use rule |
| financial timing leakage | look-ahead bias | `available_at <= decision_at` |
| DBSCAN forced into fixed-k | invalid temporal comparison | defer until variable-k design |
| Dynamic label misuse | methodology overclaim | dedicated review required |
| UI recomputes logic | reproducibility drift | Product reads immutable artifacts |

---

## 23. Critical path từ hôm nay

```text
M1 COMPLETE
   ↓
M2-PREP COMPLETE
   ↓
M2-R1 Protocol Freeze v1
   ↓
M2-R2 Market-only Runner Adapter
   ↓
M2-EXEC-A Global-k Development
   ↓
M2-EXEC-B Baseline + Comparators
   ↓
M2-VERIFY
   ↓
M2-REPORT / HANDOFF
   ↓
M3-PREP Strategy/Backtest Freeze
   ↓
M3-EXEC / VERIFY / FINAL EVAL
   ↓
Dashboard + Thesis Report
```

Optional parallel branch sau khi PIT sẵn sàng:

```text
Financial PIT Resolution
   ↓
F/M/Z Score Feature Contract
   ↓
Market-only vs Fundamental vs Combined Ablation
```

---

## 24. Definition of Done

### M2 done khi

- protocol versioned và frozen;
- runner market-only không dùng legacy eligibility;
- global k được chọn bằng rule pre-registered;
- baseline + approved comparators chạy reproducibly;
- cluster quality + temporal stability verified;
- holdout được dùng đúng rule;
- không có portfolio leakage;
- report/notebook + handoff package hoàn chỉnh.

### M3 done khi

- portfolio rule frozen trước evaluation;
- benchmarks chạy cùng period/cost assumptions;
- metrics reproducible;
- final evaluation không dùng để retune M2;
- limitations/negative results được giữ;
- dashboard/report consume verified artifacts.

---

## 25. Quyết định cần thực hiện ngay

Bước tiếp theo chính thức là:

**M2-R1 — Protocol Freeze v1**

Freeze các đề xuất ở Section 6 thành config/ADR/testable contract, nhưng **chưa chạy real clustering**.

Sau M2-R1 mới sửa runner ở M2-R2.

---

**End of Plan — Version 1.0**
