"""Execution prices and tradability for M3 (M3_PLAN Q11, Q12, Q17).

- Price basis: adj_close (vendor-adjusted, includes cash dividends — stage 0.5), never mixed with raw_close returns.
- Q17 glitch repair: a session whose adj/raw ratio jumps > 3 % from the previous session and comes back within
  ±0.5 % the next session gets adj = raw × next-session ratio, flagged ADJ_GLITCH_REPAIRED. Source rows unchanged.
- Q12 tradability: needs a price and volume > 0; BUY fails when the close is at the ceiling price, SELL fails when
  it is at the floor price (no order-book data, so a limit close counts as unfillable).
"""
import json
import sqlite3
from bisect import bisect_left, bisect_right
from collections import defaultdict
from pathlib import Path

from . import inputs

GLITCH_JUMP, GLITCH_BACK = 0.03, 0.005


def repair_ratio_glitches(rows):
    """rows: [(date, adj, raw)] sorted by date. Returns {date: (adj, flag)} with Q17 applied."""
    out = {}
    ratios = [(d, a / r if a and r else None) for d, a, r in rows]
    for i, (d, a, r) in enumerate(rows):
        flag = None
        if 0 < i < len(rows) - 1 and a and r:
            prev, cur, nxt = ratios[i - 1][1], ratios[i][1], ratios[i + 1][1]
            if prev and cur and nxt and abs(cur / prev - 1) > GLITCH_JUMP and abs(nxt / prev - 1) < GLITCH_BACK:
                a, flag = r * nxt, 'ADJ_GLITCH_REPAIRED'
        out[d] = (a, flag)
    return out


class PriceBook:
    """Adjusted prices, volumes and price limits on the sessions M3 trades or values on.

    dates: sessions that matter (execution dates + end dates); their neighbours are loaded too for Q17.
    limits: {(ticker, date): (raw_close, ceiling, floor)} from load_limits(), or None to skip limit checks.
    """

    def __init__(self, dates, calendar, bundle=inputs.BUNDLE, limits=None):
        self.calendar = calendar
        need = set()
        for d in dates:
            i = bisect_left(calendar, d)
            need.update(calendar[max(0, i - 1): i + 2])
        db = sqlite3.connect(f'file:{bundle}?mode=ro', uri=True)
        marks = ','.join('?' * len(need))
        series = defaultdict(list)
        self.volume = {}
        for t, d, a, r, v in db.execute(
                f'select ticker, date, adj_close, raw_close, volume from prices where date in ({marks}) '
                'order by ticker, date', sorted(need)):
            series[t].append((d, a, r))
            self.volume[(t, d)] = v
        self.adj, self.flags = {}, []
        for t, rows in series.items():
            for d, (a, flag) in repair_ratio_glitches(rows).items():
                if a:
                    self.adj[(t, d)] = a
                if flag:
                    self.flags.append((t, d, flag))
        self.limits = limits

    def price(self, ticker, date):
        return self.adj.get((ticker, date))

    def tradable(self, ticker, date, side):
        if self.adj.get((ticker, date)) is None or not self.volume.get((ticker, date)):
            return False
        if self.limits is None:
            return True
        raw, ceiling, floor = self.limits.get((ticker, date), (None, None, None))
        if raw is None:
            return True
        if side == 'BUY' and ceiling and raw >= ceiling:
            return False
        if side == 'SELL' and floor and raw <= floor:
            return False
        return True

    def next_session(self, date):
        i = bisect_right(self.calendar, date)
        return self.calendar[i] if i < len(self.calendar) else None


def load_limits(dates, path=inputs.PRICES_C8, cache=None):
    """{(ticker, date): (raw_close, ceiling, floor)} for `dates` from the C8 price file (4 GB, streamed once and
    cached as JSON next to the M3 manifest)."""
    dates = set(dates)
    if cache and Path(cache).is_file():
        data = json.loads(Path(cache).read_text(encoding='utf-8'))
        if set(data['dates']) >= dates:
            return {(t, d): tuple(v) for t, d, *v in data['rows'] if d in dates}
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            d = line[line.index('"trade_date": "') + 15:][:10]
            if d not in dates:
                continue
            x = json.loads(line)
            rows.append((x['ticker'], d, x['raw_close'], x['ceiling_price'], x['floor_price']))
    if cache:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        Path(cache).write_text(json.dumps(dict(dates=sorted(dates), rows=rows)), encoding='utf-8')
    return {(t, d): (r, c, fl) for t, d, r, c, fl in rows}
