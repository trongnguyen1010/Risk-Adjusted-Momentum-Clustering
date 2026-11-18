"""Versioned C5 market-observation and activity semantics."""

READINESS_POLICY_V2 = "MARKET_FEATURE_READINESS_V2"


def sum_observed_components(first, second):
    """Sum provider components without turning missing evidence into zero."""
    if first is None or second is None or first < 0 or second < 0:
        return None
    return first + second


def classify_activity(matched_volume, negotiated_volume):
    total = sum_observed_components(matched_volume, negotiated_volume)
    if total is None:
        return {
            "trading_activity_status": "UNKNOWN_ACTIVITY_COMPONENTS",
            "tradability_eligible": None,
            "volume": None,
        }
    if total == 0:
        return {
            "trading_activity_status": "OBSERVED_ZERO_VOLUME",
            "tradability_eligible": False,
            "volume": 0,
        }
    return {
        "trading_activity_status": "ACTIVE",
        "tradability_eligible": True,
        "volume": total,
    }


def enrich_observed_row(row):
    """Add C5 semantics while preserving every provider-published component."""
    result = dict(row)
    activity = classify_activity(
        row.get("matched_volume_shares"), row.get("negotiated_volume_shares")
    )
    result.update(activity)
    result["traded_value"] = sum_observed_components(
        row.get("matched_value_vnd"), row.get("negotiated_value_vnd")
    )
    result["market_observation_status"] = "OBSERVED_VALID"
    result["trading_status"] = (
        "normal" if activity["trading_activity_status"] == "ACTIVE"
        else "illiquid_or_nontraded"
        if activity["trading_activity_status"] == "OBSERVED_ZERO_VOLUME"
        else "unknown"
    )
    result["readiness_policy"] = READINESS_POLICY_V2
    return result
