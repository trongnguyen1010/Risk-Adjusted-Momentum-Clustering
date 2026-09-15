# Kiến trúc DELTA

## Nguyên tắc

DELTA có Research Core là upstream producer và Product Layer là downstream consumer. Research validity được quyết định bởi data/methodology/evaluation contract, không bởi dashboard hay portfolio return.

```text
CafeF / VietFin / Vnstock
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

| Context | Sở hữu | Không sở hữu |
|---|---|---|
| Source acquisition | request, raw response, provider/version/rights metadata | canonical meaning |
| Normalization | field/type/unit/basis/identity candidates | conflict winner |
| Reconciliation/canonical | deterministic decision, conflict/evidence, historical identity | model selection |
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
5. Feature eligibility do registry metadata quyết định; Sharpe/ROI không vào clustering.
6. Cluster quality, temporal stability và portfolio performance tách biệt.
7. Product chỉ consume versioned artifact và giữ provenance/limitations.
8. Dynamic package chỉ có interface cho tới explicit methodology approval.

## Scale

JSONL phù hợp smoke/pilot và reproducibility. Khi source validation/pilot pass và scale hàng trăm đến >1.200 mã trong 5–15 năm, analytics có thể chuyển sang partitioned Parquet/DuckDB; quyết định serving storage là M3/later và không được kéo microservice/database migration vào refactor hiện tại.
