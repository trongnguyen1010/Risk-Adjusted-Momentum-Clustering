# Product API v1

Base path: `/api/v1`. The current edge is read-only and serves one immutable bundle.

| Endpoint | Response |
|---|---|
| `GET /health` | server status and bundle manifest |
| `GET /companies` | ticker/name/exchange catalog |
| `GET /companies/{ticker}` | company-detail projection |

Unknown/invalid tickers return HTTP 404 with `{"error":"company_not_found"}`. Tickers normalize to uppercase and contain only letters, numbers or hyphen.

Company fields: `schema_version`, `company`, `quote`, `quote_state`, `market_history`, `analytics`, `cluster`, `cluster_state`, `fundamentals`, `sentiment`, `news`, `quality`, `provenance`.

Each optional domain has a state. `partial` is used when a domain exists but named fields are missing:

```json
{"status":"unavailable","reason":"Human-readable reason"}
```

Clients render `null`/`unavailable` as missing, never zero. `quote.price_basis` distinguishes raw, vendor-adjusted and total-return semantics. Schema 1.x is additive; removing/renaming fields or changing unit/meaning requires v2 or a migration period.
