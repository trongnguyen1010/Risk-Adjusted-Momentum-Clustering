"""Validate field types, duplicate keys and temporal relationships before features."""
from collections import Counter, defaultdict
from datetime import datetime
from ..contracts import normalize, schema


def clean_tables(raw_tables, data_version):
    tables, issues, quarantine = {}, [], []

    def reject(table, row, rule, message):
        issues.append({"data_version": data_version, "rule_id": rule, "table": table,
                       "security_id": row.get("security_id"), "trade_date": row.get("trade_date"),
                       "severity": "error", "status": "open", "message": message})
        quarantine.append({"table": table, "rule_id": rule, "row": row})

    for table, records in raw_tables.items():
        normalized = []
        for raw, job, fetched_at in records:
            try:
                if not isinstance(raw, dict):
                    raise ValueError("expected row object")
                defaults = {**job.get("defaults", {}), "source": job["source"], "fetched_at": fetched_at, "data_version": data_version}
                row = normalize(table, raw, defaults, job.get("mapping"), job.get("multipliers"))
                # Provenance describes this fetch even if a CSV carries stale provenance.
                for key in ("source", "fetched_at", "data_version"):
                    if key in row:
                        row[key] = defaults[key]
                normalized.append(row)
            except (ValueError, TypeError) as exc:
                reject(table, raw if isinstance(raw, dict) else {"raw": raw}, "SCHEMA", str(exc))
        pk = schema(table)["primary_key"]
        counts = Counter(tuple(r[k] for k in pk) for r in normalized)
        tables[table] = []
        for row in normalized:
            if counts[tuple(row[k] for k in pk)] > 1:
                reject(table, row, "DUPLICATE_KEY", "All conflicting rows quarantined; resolve upstream")
            else:
                tables[table].append(row)

    valid_calendar = []
    for row in tables.get("trading_calendar", []):
        close, decision = datetime.fromisoformat(row["close_at"]), datetime.fromisoformat(row["decision_at"])
        if decision < close or close.date().isoformat() != row["trade_date"] or (row["is_month_end"] and not row["is_open"]):
            reject("trading_calendar", row, "CALENDAR_TIME", "Invalid session date/decision time/month end")
        elif row["is_month_end"] and any(r["exchange"] == row["exchange"] and r["is_open"] and r["trade_date"][:7] == row["trade_date"][:7] and r["trade_date"] > row["trade_date"] for r in tables["trading_calendar"]):
            reject("trading_calendar", row, "MONTH_END", "Later open session exists in same month")
        else:
            valid_calendar.append(row)
    tables["trading_calendar"] = valid_calendar
    securities = tables.get("securities", [])
    bad_metadata = set()
    for i, row in enumerate(securities):
        if ((row["valid_to"] and row["valid_to"] <= row["valid_from"]) or
            (row["delisting_date"] and row["listing_date"] and row["delisting_date"] < row["listing_date"])):
            bad_metadata.add(i)
        for j in range(i):
            other = securities[j]
            same_identity = row["security_id"] == other["security_id"]
            same_ticker = (row["ticker"], row["exchange"]) == (other["ticker"], other["exchange"])
            overlaps = row["valid_from"] < (other["valid_to"] or "9999-12-31") and other["valid_from"] < (row["valid_to"] or "9999-12-31")
            if (same_identity or same_ticker) and overlaps:
                bad_metadata.update((i, j))
    for i in sorted(bad_metadata):
        reject("securities", securities[i], "METADATA_INTERVAL", "Invalid or overlapping identity/ticker interval")
    securities = tables["securities"] = [r for i, r in enumerate(securities) if i not in bad_metadata]
    identities = {r["security_id"] for r in securities}
    calendar = {(r["exchange"], r["trade_date"]): r for r in tables.get("trading_calendar", [])}
    cleaned_prices = []
    for row in tables.get("prices_daily", []):
        day = row["trade_date"]
        matches = [m for m in securities if m["security_id"] == row["security_id"] and m["valid_from"] <= day < (m["valid_to"] or "9999-12-31")]
        reason = None
        if len(matches) != 1 or matches[0]["ticker"] != row["ticker"] or matches[0]["exchange"] != row["exchange"]:
            reason = ("TEMPORAL_FK", "No unique security/ticker/exchange interval on trade_date")
        elif (matches[0]["listing_date"] and day < matches[0]["listing_date"]) or (matches[0]["delisting_date"] and day >= matches[0]["delisting_date"]):
            reason = ("LISTING_LIFETIME", "Price outside listing lifetime")
        elif not calendar.get((row["exchange"], day), {}).get("is_open"):
            reason = ("CALENDAR", "Missing calendar or closed exchange day")
        else:
            low, high = row["raw_low"], row["raw_high"]
            if low is not None and high is not None and (low > high or any(v is not None and not low <= v <= high for v in (row["raw_open"], row["raw_close"]))):
                reason = ("OHLC", "Expected low <= open/close <= high")
            elif datetime.fromisoformat(row["available_at"]) < datetime.fromisoformat(calendar[(row["exchange"], day)]["close_at"]):
                reason = ("AVAILABILITY", "Daily close cannot be available before session close")
        if reason:
            reject("prices_daily", row, *reason)
        else:
            cleaned_prices.append(row)
    tables["prices_daily"] = cleaned_prices
    actions = []
    for row in tables.get("corporate_actions", []):
        if row["security_id"] not in identities:
            reject("corporate_actions", row, "FOREIGN_KEY", "Unknown security_id")
        elif (row["event_type"] == "cash_dividend" and row["cash_amount"] is None) or (row["event_type"] in ("split", "stock_dividend") and row["ratio"] is None):
            reject("corporate_actions", row, "ACTION_FIELDS", "Event is missing amount or ratio")
        else:
            actions.append(row)
    tables["corporate_actions"] = actions
    for table, rows in tables.items():
        keys = schema(table)["primary_key"]
        rows.sort(key=lambda row: tuple(str(row[k]) for k in keys))
    return tables, issues, quarantine


def coverage(tables, features):
    by_security, by_year, by_exchange, snapshots = defaultdict(list), defaultdict(set), defaultdict(set), defaultdict(lambda: [0, 0])
    for row in tables.get("prices_daily", []):
        by_security[row["security_id"]].append(row["trade_date"])
        by_year[row["trade_date"][:4]].add(row["security_id"])
        by_exchange[row["exchange"]].add(row["security_id"])
    details = [{"security_id": key, "first_date": min(days), "last_date": max(days), "observations": len(days)} for key, days in sorted(by_security.items())]
    for row in features:
        snapshots[row["as_of_date"]][0] += 1
        snapshots[row["as_of_date"]][1] += int(row["eligibility"])
    missing = []
    observed = {(r["security_id"], r["trade_date"]) for r in tables.get("prices_daily", [])}
    for meta in tables.get("securities", []):
        for day in tables.get("trading_calendar", []):
            d = day["trade_date"]
            if (day["exchange"] == meta["exchange"] and day["is_open"] and meta["valid_from"] <= d < (meta["valid_to"] or "9999-12-31")
                and (not meta["listing_date"] or meta["listing_date"] <= d) and (not meta["delisting_date"] or d < meta["delisting_date"])
                and (meta["security_id"], d) not in observed):
                missing.append({"security_id": meta["security_id"], "trade_date": d, "reason": "unclassified_gap"})
    return {"n_securities": len(details), "by_security": details, "by_year": {k: len(v) for k, v in sorted(by_year.items())},
            "by_exchange": {k: len(v) for k, v in sorted(by_exchange.items())}, "snapshots": {k: {"rows": v[0], "eligible": v[1]} for k, v in sorted(snapshots.items())},
            "missing_sessions": missing, "m1_accepted": False, "acceptance_note": "Coverage evidence only; source, 300 securities/5 years and review not yet accepted"}
