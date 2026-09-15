"""Evidence-gated market normalization independent from canonical reconciliation."""
from datetime import datetime, timedelta, timezone
import math

from .identity import resolve_security


def evidence_value(policy: dict, key: str, optional: bool = False):
    item = policy.get(key, {})
    allowed = ("verified", "research_assumption") if key == "availability_policy" else ("verified",)
    if item.get("status") not in allowed or not item.get("evidence") or item.get("value") is None:
        if optional:
            return None
        raise ValueError("unresolved semantic: " + key)
    return item["value"]


def trade_date(value: str, offset_minutes: int) -> str:
    if isinstance(offset_minutes, bool) or not isinstance(offset_minutes, int) or abs(offset_minutes) > 840:
        raise ValueError("invalid timezone offset")
    zone = timezone(timedelta(minutes=offset_minutes))
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=zone)
    return stamp.astimezone(zone).date().isoformat()


def multiplier(policy: dict, key: str, optional: bool = False):
    value = evidence_value(policy, key, optional)
    if value is not None and (isinstance(value, bool) or not isinstance(value, (float, int))
                              or not math.isfinite(value) or value <= 0):
        raise ValueError("invalid multiplier: " + key)
    return value


def mapped_market_price(record: dict, policy: dict, canonical_field: str):
    """Map an optional exchange price only with field-level unit evidence.

    Magnitude is never used to guess a multiplier. A missing reviewed mapping
    deliberately produces ``None`` in the nullable canonical field.
    """
    spec = policy.get("market_field_mappings", {}).get(canonical_field)
    if spec is None:
        return None
    if (spec.get("status") != "verified" or not spec.get("evidence")
            or spec.get("canonical_unit") != "VND/share"
            or not spec.get("provider_field")):
        raise ValueError("unresolved market field mapping: " + canonical_field)
    factor = spec.get("multiplier")
    if (isinstance(factor, bool) or not isinstance(factor, (int, float))
            or not math.isfinite(factor) or factor <= 0):
        raise ValueError("invalid evidenced field multiplier: " + canonical_field)
    value = record.get(spec["provider_field"])
    if value is None:
        return None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0):
        raise ValueError("invalid provider value: " + canonical_field)
    return value * factor


def map_record(record: dict, document: dict, policy: dict,
               master: list[dict], observations: dict) -> tuple[str, dict]:
    """Normalize one verified vendor market record; do not resolve source conflicts."""
    job = document["job"]
    day = trade_date(record["time"], evidence_value(policy, "timezone_offset_minutes"))
    if not job["start"] <= day <= job["end"]:
        raise ValueError("record outside requested date range")
    info = observations.get((job["kind"], job["symbol"], day), {})
    mode = evidence_value(policy, "availability_policy")
    if mode == "fetched_at":
        available = document["fetched_at"]
    elif mode == "reference":
        available = info["available_at"]
    elif mode == "market_close_plus_delay":
        assumption = policy["availability_policy"]
        if assumption.get("status") != "research_assumption":
            raise ValueError("historical availability must be labeled research_assumption")
        delay = assumption["safety_delay_minutes"]
        if isinstance(delay, bool) or not isinstance(delay, int) or delay < 0:
            raise ValueError("invalid availability safety delay")
        available = (datetime.fromisoformat(day + "T" + assumption["market_close_time"])
                     + timedelta(minutes=delay)).isoformat()
    else:
        raise ValueError("unsupported availability policy")
    common = dict(trade_date=day, available_at=available, fetched_at=document["fetched_at"],
                  source=document["source_routing"])
    if job["kind"] == "index":
        basis = evidence_value(policy, "index_basis")
        if basis not in ("price", "total_return", "synthetic") or (basis == "synthetic" and not policy["synthetic"]):
            raise ValueError("invalid index basis")
        return "benchmark_daily", dict(common, index_id=job["symbol"],
                                       close=record["close"] * multiplier(policy, "index_multiplier"),
                                       index_basis=basis, exchange=evidence_value(policy, "index_exchange"))
    if job["kind"] != "equity":
        raise ValueError("unsupported vendor job kind")
    meta = resolve_security(master, job["symbol"], day)
    basis = evidence_value(policy, "adjustment_basis")
    if (basis not in ("unadjusted", "split_adjusted", "vendor_adjusted", "total_return", "unknown", "synthetic")
            or (basis == "synthetic" and not policy["synthetic"])):
        raise ValueError("invalid adjustment basis")
    scale = multiplier(policy, "price_multiplier")
    volume_scale = multiplier(policy, "volume_multiplier", True)
    value_scale = multiplier(policy, "traded_value_multiplier", True)
    row = dict(common, security_id=meta["security_id"], ticker=meta["ticker"], exchange=meta["exchange"],
               adjustment_basis=basis, trading_status=info.get("trading_status", "unknown"),
               volume=record["volume"] * volume_scale if volume_scale is not None else None,
               traded_value=(record["va"] * value_scale
                             if value_scale is not None and record.get("va") is not None else None),
               adj_close=(record["close"] * scale
                          if basis in ("split_adjusted", "vendor_adjusted", "total_return", "synthetic") else None))
    band_fields = ("reference_price", "ceiling_price", "floor_price")
    mapped_bands = {field: mapped_market_price(record, policy, field) for field in band_fields}
    if any(value is not None for value in mapped_bands.values()) and basis not in ("unadjusted", "synthetic"):
        raise ValueError("exchange price bands require an unadjusted price basis")
    row.update(mapped_bands)
    open_price, high, low, close = (record[field] for field in ("open", "high", "low", "close"))
    if (any(isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0 for value in (open_price, high, low, close))
            or not low <= min(open_price, close) <= max(open_price, close) <= high):
        raise ValueError("corrupt vendor OHLC")
    for field in ("open", "high", "low", "close"):
        row["raw_" + field] = record[field] * scale if basis in ("unadjusted", "synthetic") else None
    return "prices_daily", row
