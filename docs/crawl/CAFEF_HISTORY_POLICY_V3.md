# CafeF History Policy V3

## Decision

`HISTORY_POLICY_V3` replaces the active 15-year-for-all acquisition policy. A
quarter-bounded 15-year crawl creates about 60 range folders per old listing, multiple
raw pages and sidecars per range, and hundreds of loose files per security. Sequential
collection at that depth is too slow and file-heavy for a future universe of 500–1,000+
securities.

Acquisition depth remains separate from research eligibility. The existing minimum
usable research history remains at least three years where the methodology already
defines it. A legitimate newer listing with three or four usable years is not excluded
merely because it cannot supply five years. Choosing BASE rather than DEEP history also
does not reduce clustering eligibility.

## History tiers

### BASE_5Y

BASE is the default acquisition tier for the primary research and clustering dataset.
The frozen window is `2021-09-23 → 2026-09-23`. Each security starts at the later of
`2021-09-23` and its verified legitimate identity/listing start. The policy never
fabricates unavailable history.

### DEEP_10Y

DEEP is an optional robustness set, not a full-universe requirement. Its lower bound is
`2016-09-23`. Future scale planning selects approximately 10% of eligible securities
with the fixed seed stored in the plan manifest/policy. The selector is deterministic,
input-order independent, and preserves exchange representation where feasible. It uses
only available identity, exchange, history-age, role, sector, or methodology evidence;
it makes no liquidity, market-cap, popularity, or representativeness claim. No DEEP
crawl is authorized by this stage.

### LONG_15Y_VALIDATION

LONG is a small validation tier only. The ten securities completed before the stopped
V2.3 run reached MBB were selected by operational execution order, not random or
representative sampling. After full quarter/page/sidecar/checksum validation they form
the initial `OPERATIONAL_LONG_HISTORY_VALIDATION_SET`. Their raw bytes remain in the
stopped source run and may satisfy BASE without duplication or recrawl. Partial V2.3
history is not automatically spliced into V3.

## Provider and identity contract

All acquisition remains sequential and uses the verified CafeF PriceHistory endpoint,
literal `HOSE`/`HNX`/`UPCOM` exchange values, verified identity intervals, and
`CALENDAR_QUARTER_INTERSECTION`. The pipeline is BASE target window, identity
intersection, quarter intersection, then CafeF pagination. Year-sized requests remain
invalid because long ranges can truncate silently.

The stopped `cafef-c1-solo-main-v2` run is a `STOPPED_SOURCE_ARTIFACT`. It cannot be
resumed into V3 or receive new requests. Only securities classified
`LONG_HISTORY_COMPLETE` by the local registry are reused. MBB is partial and all other
not-started securities require a clean BASE crawl.

## Storage and future scale

Exact raw page preservation remains the acquisition/audit format. The optional offline
compactor can pack a fully completed, checksum-valid ticker after acquisition. It never
runs automatically, refuses partial tickers, preserves source raw by default, and
requires explicit `--delete-source` plus archive/member verification before deletion.

Future scale policy:

- all securities: `BASE_5Y`;
- deep validation: deterministic stratified `DEEP_10Y` subset;
- long validation: tiny explicit `LONG_15Y_VALIDATION` set only;
- more than 500 securities: multi-worker planning may be activated through the approved
  scale workflow;
- 500 or fewer securities: no automatic five-worker activation.

No live request, canonical mutation, research-price build, or feature rebuild occurred
in this policy stage.
