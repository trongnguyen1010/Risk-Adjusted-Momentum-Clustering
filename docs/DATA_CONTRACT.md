# Data contract 2.0

## Source of truth

Executable contracts là các JSON trong `src/delta_t1/schemas`; `contracts.py` thực hiện normalize/validate. Đổi type, key, unit hoặc semantics phải đi cùng schema version, migration note, tests, `CHANGELOG.md` và [Decisions](DECISIONS.md).

Canonical row giữ `source`, `fetched_at` và `data_version`. Missing nullable dùng `null`, không dùng chuỗi rỗng, NaN hoặc zero giả. Provider column chưa map ở lại immutable raw envelope.

## Canonical tables

| Table | Key | Semantics chính |
|---|---|---|
| `securities` | security_id, valid_from | historical ticker/exchange/issuer interval, status, currency |
| `prices_daily` | security_id, trade_date | raw/adjusted OHLC, basis, volume/value, status, availability |
| `benchmark_daily` | index_id, trade_date | price hoặc total-return level và basis |
| `trading_calendar` | exchange, trade_date | open/month-end và decision timestamp |
| `corporate_actions` | event_id | announcement/ex/record/effective/payment dates và economic terms |
| `risk_free_rate` | date, tenor | annualized rate, day-count basis và availability |
| `financial_reports` | report_id | fiscal period, scope, audit/revision, publication/availability, document hash |
| `financial_facts` | report_id, item_code | tidy fact, instant/duration, currency/scale, taxonomy |
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

## Unit và price basis

Equity price dùng VND/share, volume dùng shares, traded value dùng VND; index level giữ points. Chỉ áp dụng provider multiplier khi có evidence, không suy từ magnitude.

`raw_close`, split-adjusted, vendor-adjusted và certified total-return là các series khác nhau. `raw_close` có thể null và không được copy từ adjusted close. Basis change reset rolling window. Không suy traded value từ adjusted price × volume nếu chưa có proxy contract riêng.

## Feature eligibility

Real run yêu cầu `minimum_history_years >= 3`, đo từ usable observed price đầu tiên trong cùng basis.

- `ELIGIBLE_FOR_CLUSTERING`: history, identity, status và required features pass.
- `REFERENCE_ONLY`: security hợp lệ nhưng chưa đủ observed history.
- `EXCLUDED`: fail rule khác.

Row giữ history/observation/missing counts, `na_reason` và segment. Gap không bị nén/forward-fill. Feature registry quyết định eligibility bằng metadata; Sharpe/ROI luôn `cluster_eligible=false`. Sharpe chỉ thuộc portfolio evaluation.

## Quality và failure behavior

Duplicate key, invalid type/date/number, overlapping identity, impossible OHLC, timing violation, unknown basis và broken relation phải quarantine kèm rule ID. Blocking issue chặn downstream feature. Sửa mapping/policy tạo run mới; raw/canonical artifact không bị overwrite.

Coverage report missing session và segment count nhưng không tự coi missing price là holiday. Completed run resume chỉ đọc/verify khi config/code/raw hashes khớp. KBS pilot decisions chỉ còn tại [legacy semantics](data/kbs_pilot_semantics.md), không định nghĩa production contract.
