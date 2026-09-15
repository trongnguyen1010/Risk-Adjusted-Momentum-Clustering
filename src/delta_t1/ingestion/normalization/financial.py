"""Financial candidate checks; concrete ratios remain feature-layer decisions."""
from datetime import datetime


def normalize_financial_report(row: dict) -> dict:
    period_end = datetime.fromisoformat(row["period_end"] + "T00:00:00+00:00")
    published = datetime.fromisoformat(row["published_at"].replace("Z", "+00:00"))
    available = datetime.fromisoformat(row["available_at"].replace("Z", "+00:00"))
    if published.tzinfo is None or available.tzinfo is None:
        raise ValueError("financial timestamps require timezone")
    if published.date() < period_end.date() or available < published:
        raise ValueError("financial publication/availability timing is invalid")
    return dict(row)


def normalize_financial_fact(row: dict) -> dict:
    if row["period_type"] not in ("instant", "duration"):
        raise ValueError("financial fact period_type must be instant or duration")
    if isinstance(row.get("unit_scale"), bool) or row.get("unit_scale", 0) <= 0:
        raise ValueError("financial fact requires positive unit_scale")
    return dict(row)
