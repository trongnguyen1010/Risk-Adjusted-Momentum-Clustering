# CafeF C1 PriceHistory Range Contract Finding

- Discovery date: `2026-09-24` (local project context).
- Provider surface: CafeF `PriceHistory`.
- Verified endpoint: `https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx`.
- Original unsafe assumption: `NON_OVERLAPPING_CALENDAR_YEAR_CHUNKS`.

## Live observation

The user requested ACB on HOSE for `2012-01-01` through `2012-12-31`. CafeF
returned `TotalCount = 65` across four internally consistent pages:

- page 1: 20 rows, `2012-12-03` through `2012-12-28`;
- page 2: 20 rows, `2012-11-05` through `2012-11-30`;
- page 3: 20 rows, `2012-10-08` through `2012-11-02`;
- page 4: 5 rows, `2012-10-01` through `2012-10-05`.

Thus the year-sized request returned only approximately Q4 2012, even though HTTP,
envelope, `TotalCount`, and pagination behavior were internally valid. The CafeF UI
also permits a maximum selection of approximately three months.

## Methodology decision

This is an observed operational constraint, not a claim about an undocumented
server-side algorithm. Long ranges may be silently truncated, so HTTP 200 and
`Success=true` do not establish requested-range completeness. Pagination itself was
consistent in this sample; the invalid assumption was the year-sized request range.

Year-range acquisition is therefore invalid for C1 completeness. The corrected
contract is `CALENDAR_QUARTER_INTERSECTION`, applied after the target-window and
verified identity-interval intersection.

All local C1 crawl outputs created under the old range policy were intentionally
deleted at the user's request. They are not research evidence and must not be used
downstream. No full raw payload is retained in this finding.
