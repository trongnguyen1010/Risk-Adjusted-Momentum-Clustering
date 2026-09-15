# Delta Intelligence product requirements

## Product thesis

Help an analyst move from a ticker to a defensible company view: what changed in price and financial quality, which peers behave similarly, how the grouping changes over time, what events may explain the change, and how trustworthy/fresh each datum is.

The reference company page demonstrates a useful information architecture: profile, quote/history, technical and sentiment views, annual/quarterly financial metrics, quality/distress scores, peer clustering and news. Delta will implement these capabilities with point-in-time provenance and research-grade cluster evaluation; it will not copy the reference site's code, brand or unexplained calculations.

## Primary users

- Equity analyst: company/peer review with traceable data.
- Researcher: methodology, stability and experiment evidence.
- Portfolio team: clusters, regimes and locked backtests without recommendation wording.
- Data steward: source conflicts, freshness and quality failures.

## Company-detail modules

| Module | MVP | Production acceptance |
|---|---|---|
| Identity/profile | ticker, name, exchange, sector/industry | historical identity, issuer description, source/rights evidence |
| Quote/history | price, change, volume, range, basis | raw OHLC/reference/floor/ceiling, freshness SLA, action semantics |
| Market analytics | 1/3/6/12M momentum, volatility, beta, drawdown | formula/version/citation and missingness |
| Fundamentals | explicit unavailable state | annual/quarterly PIT facts, scope, quarter/YTD/TTM and revisions |
| Quality/risk scores | explicit unavailable state | verified Beneish/Piotroski/Altman variants and applicability warnings |
| Peer intelligence | cluster, peers, profile, membership history | representative universe, approved dynamic method, stability/confidence |
| News/sentiment | explicit unavailable state | licensed sources, deduplication, event links and evaluated model card |
| Trust panel | warnings + run IDs | field-level sources/conflicts/freshness/coverage |

## Extensions beyond the reference

- Cluster-transition timeline and regime alerts.
- Explainable peer differences: feature contribution and centroid distance.
- Multi-source field-conflict viewer.
- Watchlists and alert rules after auth/privacy design.
- Portfolio research workspace with locked experiment IDs.
- Exportable, citation-aware analyst brief.

## Product safety

The interface is analytical, not personalized investment advice. It shows stale/partial data, avoids bullish/bearish certainty from cluster labels, separates cluster-quality from portfolio-performance metrics, and always marks pilot data as non-production.
