# Crawl Field Catalog

> Source có thể dùng tên field khác. Bảng này mô tả **meaning cần tìm**, không phải bắt source phải có đúng tên.

## 1. Security master

| Field | Priority | Vì sao |
|---|---|---|
| provider_security_id | Required if available | Giữ provider identity |
| ticker | Required | Display/source lookup |
| company_name | Required | Identity validation |
| exchange | Required | HOSE/HNX/UPCOM |
| listing_date | High | Historical eligibility |
| delisting_date | High | Historical universe |
| status | High | Active/inactive context |
| sector | Medium | Representation / analysis |
| industry | Medium | Representation / analysis |
| ticker_history | Raw/High | Identity changes |
| exchange_history | Raw/High | Historical membership |

## 2. Shares / Capital Structure History

| Field | Priority |
|---|---|
| security_id | Required |
| effective_date | Required |
| available_at | Required |
| listed_shares | Conditional |
| outstanding_shares | Conditional |
| issued_shares | Conditional |
| treasury_shares | Conditional |
| source | Required |
| fetched_at | Required |
| data_version | Required |

Count dùng đơn vị shares và ít nhất một count phải có. Source có thể chỉ cung cấp current snapshot; historical availability phải được ghi trung thực. Không giả định các count bằng nhau và không backfill current counts vào quá khứ.

## 3. Daily market

| Field | Priority | Canonical target | Vì sao |
|---|---|---|---|
| trade_date | Required | trade_date | Primary time key |
| open | Required | raw_open | OHLC / QC |
| high | Required | raw_high | OHLC / QC |
| low | Required | raw_low | OHLC / QC |
| close | Required | raw_close or adj_close | Return path |
| reference | Required for new smoke | reference_price | Price-limit/QC semantics |
| ceiling | Required for new smoke | ceiling_price | Mentor requirement/QC |
| floor | Required for new smoke | floor_price | Mentor requirement/QC |
| volume | Required | volume | Liquidity/activity |
| traded_value | High | traded_value | Liquidity comparable across prices |
| trading_status | High | trading_status | Missing vs halted |
| price_basis | Required semantics | adjustment_basis | Prevent basis mixing |
| source timestamp | Required evidence | available_at/fetched_at | PIT/provenance |

Optional RAW-only candidates:

- matched volume/value;
- put-through volume/value;
- foreign buy/sell;
- trade count;
- bid/ask summaries.

Không promote các field optional trước semantics review.

## 4. Corporate actions

| Field | Priority |
|---|---|
| event_id | Required |
| event_type | Required |
| announcement_date | High |
| ex_date | Required |
| record_date | High |
| effective_date | Required |
| payment_date | Medium |
| cash_amount | Conditional |
| ratio | Conditional |
| issue_price | Conditional |
| currency | Conditional |
| source_document | High |

## 5. Financial reports

### Report metadata

| Field | Priority |
|---|---|
| provider_report_id | Required |
| security_id/ticker | Required |
| fiscal_year | Required |
| fiscal_quarter | Required |
| period_start | Required |
| period_end | Required |
| statement_scope | Required |
| published_at | Required when obtainable |
| available_at | Required for canonical PIT |
| audit_status | High |
| revision/restatement | High |
| currency | Required |
| unit_scale | Required |
| source_document/hash | High |

### Income statement raw facts

Ưu tiên:

- revenue;
- cost_of_goods_sold;
- gross_profit;
- selling_expense;
- administrative_expense;
- operating_profit;
- financial_income;
- financial_expense;
- interest_expense;
- profit_before_tax;
- income_tax;
- net_income;
- net_income_parent.

### Balance sheet raw facts

Ưu tiên:

- cash_and_cash_equivalents;
- short_term_investments;
- receivables;
- inventory;
- current_assets;
- total_assets;
- current_liabilities;
- total_liabilities;
- short_term_debt;
- long_term_debt;
- total_debt;
- shareholders_equity;
- retained_earnings.
- property_plant_equipment.

### Cash-flow raw facts

Ưu tiên:

- cash_flow_from_operations;
- cash_flow_from_investing;
- cash_flow_from_financing;
- capital_expenditure nếu semantics rõ;
- dividends_paid;
- net_change_in_cash.
- depreciation nếu semantics rõ.

Các fact `weighted_average_basic_shares` và `weighted_average_diluted_shares` được giữ khi source semantics đã verify; không thay bằng end-of-period outstanding shares.

## 6. Benchmark

Tối thiểu:

- index_id = VNINDEX;
- trade_date;
- close/index level;
- index basis;
- source/provenance.

## 7. Trading calendar

- exchange;
- trade_date;
- is_open;
- session_open/session_close nếu có;
- is_month_end;
- exceptional closure evidence.
