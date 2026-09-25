# Data contract 2.1

## Source of truth

Executable contracts là các JSON trong `src/delta_t1/schemas`; `contracts.py` thực hiện normalize/validate. Đổi type, key, unit hoặc semantics phải đi cùng schema version, migration note, tests, `CHANGELOG.md` và [Decisions](DECISIONS.md).

Canonical row giữ `source`, `fetched_at` và `data_version`. Missing nullable dùng `null`, không dùng chuỗi rỗng, NaN hoặc zero giả. Provider column chưa map ở lại immutable raw envelope.

## Canonical tables

| Table | Key | Semantics chính |
|---|---|---|
| `securities` | security_id, valid_from | historical ticker/exchange/issuer interval, status, currency |
| `shares_history` | security_id, effective_date | historical listed/outstanding/issued/treasury shares, availability và provenance |
| `prices_daily` | security_id, trade_date | raw OHLC, optional reference/ceiling/floor, adjusted close nếu có, basis, volume/value, status, availability |
| `benchmark_daily` | index_id, trade_date | price hoặc total-return level và basis |
| `trading_calendar` | exchange, trade_date | open/month-end và decision timestamp |
| `corporate_actions` | event_id | announcement/ex/record/effective/payment dates và economic terms |
| `risk_free_rate` (optional support) | date, tenor | annualized rate, day-count basis và availability |
| `financial_reports` | report_id | fiscal period, scope, audit/revision, publication/availability, document hash |
| `financial_facts` | report_id, statement_type, item_code | tidy fact, instant/duration, currency/scale, taxonomy |
| `feature_snapshots` | security_id, as_of_date | PIT features, history, eligibility segment, NA reasons |
| `assignments` | run/snapshot/security | raw/aligned cluster ID |
| `transitions` | run/from/to/clusters | counts/rates trên shared identities |
| `trades`, `nav` | run-specific | future raw-price ledger contracts; không phải alias của return-space simulation |

## Identity và time

- `security_id` ổn định; ticker là thuộc tính theo interval `[valid_from, valid_to)`.
- Current listing không chứng minh historical membership; ambiguous mapping phải quarantine.
- `fetched_at` là lúc acquire; `published_at` là lúc source công bố; `available_at` là thời điểm sớm nhất được phép dùng; `as_of_date` là snapshot date.
- Financial timing phải thỏa `available_at >= published_at >= period_end`.
- Restatement tạo report vintage mới; không overwrite snapshot cũ.
- Market/feature input phải có `available_at <= decision_at`; execution bắt đầu từ eligible session kế tiếp.

## Shares history

`shares_history` giữ số cổ phiếu listed, outstanding, issued và treasury theo `security_id + effective_date` để hỗ trợ historical market cap, valuation, corporate-action cross-check và future size feature. Các count dùng đơn vị shares, nullable non-negative integer; mỗi row phải có ít nhất một count. Không giả định các count bằng nhau và không áp dụng current snapshot ngược về lịch sử. `available_at` có thể trước hoặc sau `effective_date`; `fetched_at` phải không sớm hơn `available_at`. Corrections được giữ bằng immutable run/data version.

Market cap, BVPS, P/E, P/B, Piotroski F-Score, Beneish M-Score và Altman Z-Score variants là derived/versioned analytics, không phải raw source-of-truth. Vendor-derived ratio chỉ giữ làm comparison evidence. End-of-period `outstanding_shares` không đủ để tái tạo standard EPS; cần weighted-average basic/diluted shares hoặc documented vendor EPS basis.

## Unit và price basis

`raw_open`, `raw_high`, `raw_low`, `raw_close`, `reference_price`, `ceiling_price`, `floor_price` và `adj_close` dùng canonical VND/share. Volume dùng shares, traded value dùng VND; index level giữ points. Ba field reference/ceiling/floor nullable vì không phải source nào cũng cung cấp. Chỉ áp dụng provider multiplier khi có field-level evidence, không suy từ magnitude.

`raw_close`, split-adjusted, vendor-adjusted và certified total-return là các series khác nhau. `raw_close` có thể null và không được copy từ adjusted close. Không tạo adjusted OHLC khi source chỉ có adjusted close. Exchange reference/ceiling/floor chỉ gắn với unadjusted basis. Basis change reset rolling window. Không suy traded value từ adjusted price × volume nếu chưa có proxy contract riêng.

## Ba lớp identity của financial report

- **Provider identity:** ID/document ID do CafeF/VietFin/Vnstock cung cấp; luôn giữ trong raw/candidate provenance.
- **Canonical report identity:** ID ổn định do DELTA tạo sau khi period/scope/vintage semantics đã normalize.
- **Reconciliation comparison key:** `security_id`, `fiscal_year`, `fiscal_quarter`, `period_end`, `statement_scope`, `revision` đã harmonize; financial fact nối thêm `statement_type`, `item_code`.

Provider `report_id` không được dùng một mình để ghép cross-source. `revision` chỉ so sánh sau khi source-specific vintage semantics được review; khác `published_at`/`available_at` là timing conflict, không silently choose.

## Feature eligibility

Real run yêu cầu `minimum_history_years >= 3`, đo từ observed price usable đầu tiên trong cùng basis. Calendar span chỉ là evidence về range; density và required-feature window được báo riêng.

- `feature_complete`: mọi required feature có giá trị tại snapshot.
- `market_feature_ready_v2`: feature complete, đủ history và market/status/metadata rules của C8; không phụ thuộc provisional identity.
- `market_experiment_eligible(t)`: khái niệm M2-PREP cần freeze; tại mỗi snapshot `t` bằng `market_feature_ready_v2(t)` dưới protocol market-only. Nó không phải terminal-universe filter, không phải field đã được thêm vào immutable C8 artifact và không tạo historical-identity claim.
- `historical_identity_ready`: identity đủ thẩm quyền cho historical universe; `provisional` luôn false.
- `research_ready`: market-feature-ready và historical-identity-ready cùng pass dưới strict research gate.
- `eligibility`/`universe_segment`: legacy/scoped selection contract được giữ để không silently redefine artifact cũ; strict research dùng `research_ready`.
- `REFERENCE_ONLY`: security hợp lệ nhưng chưa đủ observed history.
- `EXCLUDED`: fail rule khác.

Row giữ history/observation/missing counts, `na_reason` và segment. Gap không bị nén/forward-fill. Active `feature_snapshots` 1.5 không chứa Sharpe/ROI. Immutable snapshot 1.3/1.4 chỉ đọc qua `feature_snapshots_legacy_1_3_0`/`feature_snapshots_legacy_1_4_0`; dữ liệu đó không được mutate. Sharpe chỉ thuộc portfolio evaluation.

905 securities là count mới nhất tại `2026-08-28`, không được áp ngược làm membership cho snapshot cũ. M2-PREP phải xử lý membership từ row readiness tại chính snapshot đó và giải thích các giai đoạn readiness gián đoạn trước khi freeze window.

## Quality và failure behavior

Duplicate key, invalid type/date/number, overlapping identity, impossible OHLC, timing violation, unknown basis và broken relation phải quarantine kèm rule ID. Blocking issue chặn downstream feature. Sửa mapping/policy tạo run mới; raw/canonical artifact không bị overwrite.

Coverage report missing session và segment count nhưng không tự coi missing price là holiday. Completed run resume chỉ đọc/verify khi config/code/raw hashes khớp. KBS pilot decisions chỉ còn tại [legacy semantics](data/kbs_pilot_semantics.md), không định nghĩa production contract.
