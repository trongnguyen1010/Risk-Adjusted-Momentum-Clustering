"""Reference-calendar construction with explicit availability assumptions."""

from datetime import date, datetime, timedelta


def benchmark_calendar(days, start, end, fetched_at, safety_delay_minutes=120):
    """Build a declared benchmark-derived calendar; never infer it from an equity."""
    days = sorted(set(days))
    if not days or any(date.fromisoformat(day).weekday() > 4 for day in days):
        raise ValueError("invalid benchmark sessions")
    month_ends = {day[:7]: day for day in days}
    rows = []
    current, last = date.fromisoformat(start), date.fromisoformat(end)
    opened = set(days)
    while current <= last:
        day = current.isoformat()
        close = datetime.fromisoformat(day + "T15:00:00+07:00")
        decision = close + timedelta(minutes=safety_delay_minutes)
        for exchange in ("HOSE", "HNX"):
            rows.append({
                "exchange": exchange,
                "trade_date": day,
                "is_open": day in opened,
                "is_month_end": day in opened and month_ends[day[:7]] == day,
                "open_at": day + "T09:00:00+07:00",
                "close_at": close.isoformat(),
                "decision_at": decision.isoformat(),
                "available_at": day + "T08:00:00+07:00",
                "source": "research_assumption:benchmark_derived_VNINDEX",
                "fetched_at": fetched_at,
            })
        current += timedelta(days=1)
    return rows
