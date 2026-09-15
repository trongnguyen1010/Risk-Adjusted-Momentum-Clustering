"""Historical security identity normalization and temporal resolution."""


def resolve_security(master: list[dict], ticker: str, day: str) -> dict:
    matches = [row for row in master
               if row["ticker"] == ticker
               and row["valid_from"] <= day < (row.get("valid_to") or "9999-12-31")]
    if len(matches) != 1:
        raise ValueError("no unique temporal security mapping: " + ticker + " " + day)
    return matches[0]


def normalize_identity_candidate(row: dict, *, source: str) -> dict:
    required = ("security_id", "ticker", "exchange", "valid_from")
    if any(not row.get(field) for field in required):
        raise ValueError("identity candidate lacks stable/effective-dated fields")
    return dict(row, source=source)
