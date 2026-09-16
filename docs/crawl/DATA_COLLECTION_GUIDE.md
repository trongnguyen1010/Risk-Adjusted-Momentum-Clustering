# Data Collection Guide

## 1. Mục tiêu

DELTA cần dữ liệu đủ sạch để nghiên cứu clustering và sau này phục vụ product. Crawler **không phải feature engine**. Nhiệm vụ crawler là acquire raw evidence có thể kiểm tra lại.

Pipeline chuẩn:

```text
Source
  ↓
RAW immutable evidence
  ↓
Normalization
  ↓
Field-level reconciliation
  ↓
Canonical data
  ↓
QC / coverage
  ↓
Features
  ↓
Clustering / evaluation / backtest
```

## 2. Các data family bắt buộc

### Security master

Crawl:

- provider security id;
- ticker;
- company name;
- exchange;
- sector/industry nếu có;
- listing date;
- delisting date;
- status;
- ticker/exchange history nếu source có;
- source timestamps.

**Lý do:** historical universe, stable `security_id`, chống survivorship bias.

### Daily market data

Crawl:

- trade date;
- open;
- high;
- low;
- close;
- reference price;
- ceiling price;
- floor price;
- volume;
- traded value;
- trading status;
- source price-basis metadata;
- available/fetched timestamps.

**Lý do:** momentum, volatility, drawdown, beta, liquidity, QC và backtest.

### Corporate actions

Crawl:

- event type;
- announcement date;
- ex-date;
- record date;
- effective date;
- payment date;
- cash amount;
- stock/split/rights ratio;
- issue price nếu có;
- source document/event id.

**Lý do:** không nhầm split/dividend/bonus issue với economic return.

### Quarterly financial reports

Crawl raw line items của:

- income statement;
- balance sheet;
- cash-flow statement.

Kèm metadata:

- fiscal year/quarter;
- period start/end;
- consolidated/separate;
- publication/available time;
- audit status;
- revision/restatement;
- currency;
- unit scale;
- document id/hash.

**Lý do:** tạo fundamental features point-in-time và chống look-ahead bias.

### Benchmark

Tối thiểu VNINDEX:

- trade date;
- OHLC/close level nếu có;
- index basis;
- availability/provenance.

**Lý do:** beta, benchmark return, alpha/information ratio.

### Trading calendar

Crawl/reference:

- exchange;
- trade date;
- is_open;
- session close;
- month-end;
- exceptional holiday/halt.

**Lý do:** không coi source gap là holiday, xác định snapshot/rebalance chính xác.

### Provenance

Mọi batch phải biết:

- source/provider;
- endpoint/document;
- request params;
- adapter version;
- fetched_at;
- status/error;
- page/cursor;
- raw hash;
- raw path;
- transform version.

## 3. Những thứ nên tính, không nên crawl làm source of truth

Tự tính từ canonical:

- momentum 1M/3M/6M/12M;
- volatility;
- downside volatility;
- maximum drawdown;
- beta;
- liquidity aggregates;
- ROE/ROA;
- growth;
- leverage ratios;
- PCA;
- clustering labels;
- Sharpe/Sortino/Calmar.

Vendor-computed ratio có thể giữ RAW để cross-check nhưng không mặc định là canonical.

## 4. RAW / normalized / canonical

### RAW

Giữ nguyên bytes/source payload. Không rename field, không scale, không round.

### Normalized candidate

Đã parse:

- canonical field candidate;
- normalized unit;
- timezone;
- price basis;
- provider identity;
- provenance.

Chưa phải winner.

### Canonical

Chỉ được tạo sau:

- schema validation;
- reconciliation;
- QC;
- explicit decision rule.

## 5. Multi-source rule

Hai source cùng field:

```text
CafeF close = 100000
VietFin close = 100000
→ MATCH
```

```text
CafeF volume = 5000000
VietFin volume = 5000
→ UNIT/SCALE CONFLICT
```

Không average conflict.

Source priority chỉ được dùng khi policy đã:

- approved;
- versioned;
- documented.

## 6. M1 scale policy

- Source smoke: 3–5 mã.
- Representative pilot: 50–60 mã, >=5 năm.
- M1: >=300 mã, >=5 năm.
- Extended: historical eligible universe, 5–15 năm, có thể >1.200 mã.

Mã <3 năm usable observed history:

```text
REFERENCE_ONLY
```

không được ép vào clustering universe.
