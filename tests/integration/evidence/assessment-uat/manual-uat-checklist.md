# Task 14 manual UAT checklist

Status: NOT RUN by a human reviewer. Do not mark PASS until the actual UI is tested against an API that serves the pinned Assessment release.

## Preconditions

- [ ] Record test date/time, reviewer, frontend URL, backend URL, and deployed commit.
- [ ] Confirm `/api/v2/health` returns HTTP 200.
- [ ] Confirm FPT Assessment returns HTTP 200 and its revision/hash/as_of match `response-pins.json`.
- [ ] If Assessment returns 404 or 503, stop the production UAT and record BLOCKED. Do not use a mock response as production evidence.

## Manual browser checks

For each row, record PASS / FAIL / BLOCKED and attach a screenshot or response capture.

| ID | Action | Expected result | Result / evidence |
|---|---|---|---|
| UAT-01 | Open FPT Assessment | Current response, ticker FPT, as_of and release pins visible | |
| UAT-02 | Search A32 and open Assessment | Valid alternative ticker renders; no FPT data remains | |
| UAT-03 | Open AAM Assessment | Insufficient evidence is explicit; no favorable verdict is implied | |
| UAT-04 | Open VCB Assessment | Missing ticker state is explicit; no other ticker's response is shown | |
| UAT-05 | Switch feature selector | Exactly 18 features are available and only one chart is shown | |
| UAT-06 | Switch lookback 10 years to 5 years and back | Only history changes; as_of/verdict/release pins stay the same | |
| UAT-07 | Navigate Overview/Assessment and use browser Back/Forward | Tab, ticker, metric, and lookback match the URL | |
| UAT-08 | Navigate controls using keyboard only | Focus is visible and controls have understandable accessible names | |
| UAT-09 | Set viewport to 390 px wide | No horizontal page overflow; content remains usable | |
| UAT-10 | Switch to light and dark theme | Both themes render; selected state is apparent | |

The stale state is fixture-based in automated UAT. Only test it manually if a clearly identified stale fixture is available; do not label a synthetic fixture as a production stale response.

## Sign-off

Reviewer:

Date/time:

Overall result (PASS / FAIL / BLOCKED):

Open issues: