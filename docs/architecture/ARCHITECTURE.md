# Kiến trúc DELTA

## Nguyên tắc

DELTA có Research Core là upstream producer và Product Layer là downstream consumer. Research validity được quyết định bởi data/methodology/evaluation contract, không bởi dashboard hay portfolio return.

```text
CafeF TradeHistoryNew (active market source)
legacy/future source candidates (scoped evidence only)
          ↓
immutable source snapshots
          ↓
normalization → reconciliation/conflicts → canonical + QC
          ↓
feature registry + point-in-time feature snapshots
          ↓
clustering registry → cluster metrics + temporal metrics
          ↓                         ↓
backtest + portfolio metrics    experiment artifacts
          └───────────────┬─────────┘
                    product bundle → read API → web dashboard
```

## Bounded contexts

M1 canonical/core target gồm `securities`, `shares_history`, `prices_daily`, `corporate_actions`, `trading_calendar`, `benchmark_daily`, `financial_reports` và `financial_facts`; `risk_free_rate` chỉ là optional support data. `shares_history` giữ capital structure theo thời gian để hỗ trợ market-cap/valuation, corporate-action cross-check và future size features, không backfill current counts về quá khứ.

| Context | Sở hữu | Không sở hữu |
|---|---|---|
| Source acquisition | request, raw response, provider/version/rights metadata | canonical meaning |
| Normalization | field/type/unit/basis/identity candidates | conflict winner |
| Reconciliation/canonical | field-level decision, semantic comparison key, conflict/evidence, historical identity | model selection |
| Features | registry, formula, PIT join, snapshot preprocessing | network access/portfolio metric |
| Clustering | common interface, model fit/predict/artifact | duplicate metric logic/backtest choice |
| Evaluation | cluster, temporal và portfolio metric ở module riêng | model fit |
| Experiments | protocol, orchestration, immutable artifacts/report | UI state |
| Product projection | stable company JSON từ complete runs | research recomputation |
| API/web | validation, read/interaction/missing-state UX | raw access/formula/model fit |

## Invariants

1. Raw/canonical/experiment artifact là immutable và checksummed.
2. Missing giữ missing; không zero-fill hoặc silent forward-fill.
3. Historical identity dùng interval; `available_at <= decision_at`.
4. Raw, adjusted và total-return basis không được trộn.
5. Feature eligibility do registry metadata quyết định; active feature snapshot không sinh Sharpe/ROI.
6. Cluster quality, temporal stability và portfolio performance tách biệt.
7. Product chỉ consume versioned artifact và giữ provenance/limitations.
8. Dynamic package chỉ có interface cho tới explicit methodology approval.
9. Market-only M2 membership được tính theo từng snapshot; latest 905 không phải terminal filter và không promote strict research readiness.

## M2/M3 execution boundary

M2 config phải khai báo `portfolio_evaluation.enabled=false`; runner vẫn sinh assignments, cluster diagnostics và temporal diagnostics nhưng không tạo targets/backtests/performance. Chỉ M3/frozen protocol được bật portfolio evaluation. Portfolio return, Sharpe và ROI không được dùng chọn feature, PCA components, `k` hoặc algorithm.

Common clustering interface hiện còn fixed-`k`: `config["k"]`, `k_range`, cluster IDs `0..k-1` và temporal alignment cùng số cluster. Đây là technical debt được giữ rõ, không che bằng adapter giả. DBSCAN tương lai cần noise label, variable cluster count, diagnostics riêng và temporal comparison không giả định same-`k`; chưa triển khai trong task này.

## Scale

JSONL hiện vẫn phù hợp cho reproducibility và active artifacts. M2-PREP không bao gồm storage migration hay extended-scale promise. Chỉ cân nhắc partitioned Parquet/DuckDB khi một stage riêng có evidence về volume/performance và contract migration; serving storage là M3/later, không kéo microservice/database migration vào active work.
