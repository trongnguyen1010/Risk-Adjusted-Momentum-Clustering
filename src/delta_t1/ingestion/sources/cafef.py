"""Bounded CafeF public-path adapter for private research/demo acquisition."""
import re
from datetime import datetime, timedelta, timezone

from .base import PublicJsonClient, SemanticValidationError, SourceAdapter


TRADE_HISTORY_ENDPOINT = "https://cafef.vn/du-lieu/Ajax/PageNew/TradeHistoryNew.ashx"
RIGHTS_STATUS = "RIGHTS_NOT_VERIFIED"
EXECUTION_POLICY = "ACCEPTED_RESEARCH_RISK"
PRICE_UNIT = "VND_PER_SHARE"
ADAPTER_VERSION = "cafef-research-demo-3"
INVALID_ROW_EVIDENCE_FIELDS = {
    "BasicPrice", "Ceiling", "Floor", "ClosePrice", "AdjustPrice",
    "Volume", "TotalValue", "AgreedVolume", "AgreedValue",
}
_DOTNET_DATE = re.compile(r"^/?Date\((\d+)(?:[+-]\d+)?\)/?$")
# CafeF legacy historical format: "M/D/YYYY h:mm:ss AM/PM"
_CAFEF_AMPM = re.compile(
    r"^(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s+(AM|PM)$",
    re.IGNORECASE,
)
_VN_TIME = timezone(timedelta(hours=7))
# Sentinel emitted by CafeF for the leading current/intraday snapshot row
# when no intraday time is available (DateTime.MinValue in .NET).
CAFEF_DATETIME_MIN_VALUE = datetime(1, 1, 1, 0, 0, 0)


def _number(value, field, *, integral=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SemanticValidationError(f"CafeF {field} must be numeric or null")
    return int(value) if integral else float(value)


def _parse_cafef_ampm(value):
    """Parse CafeF legacy M/D/YYYY h:mm:ss AM/PM TradeDate string.

    Returns a datetime in UTC (representing documented CafeF UTC-like timestamp
    semantics), or None if the pattern does not match.
    """
    m = _CAFEF_AMPM.match(value.strip())
    if not m:
        return None
    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hour, minute, second = int(m.group(4)), int(m.group(5)), int(m.group(6))
    meridiem = m.group(7).upper()
    if meridiem == "PM" and hour != 12:
        hour += 12
    elif meridiem == "AM" and hour == 12:
        hour = 0
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def cafef_trade_date(value):
    """Parse a CafeF TradeDate string into an ISO-8601 date string (YYYY-MM-DD).

    Supported formats:
    - .NET tick-epoch: /Date(ms)/ or Date(ms+0700)
    - ISO-8601 with explicit timezone: 2026-09-14T17:00:00+07:00
    - CafeF legacy AM/PM: M/D/YYYY h:mm:ss AM/PM (interpreted as UTC, converted
      to Asia/Ho_Chi_Minh local calendar date)
    """
    if not isinstance(value, str):
        raise SemanticValidationError("CafeF TradeDate must be a string")
    normalized = value.replace("\\/", "/").strip("/")
    # .NET /Date(ms)/ epoch
    match = _DOTNET_DATE.match(normalized)
    if match:
        return datetime.fromtimestamp(int(match.group(1)) / 1000, timezone.utc).astimezone(_VN_TIME).date().isoformat()
    # CafeF legacy M/D/YYYY h:mm:ss AM/PM: interpret as UTC, convert to Asia/Ho_Chi_Minh
    parsed_ampm = _parse_cafef_ampm(value)
    if parsed_ampm is not None:
        return parsed_ampm.astimezone(_VN_TIME).date().isoformat()
    # ISO-8601 with explicit timezone
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SemanticValidationError("unsupported CafeF TradeDate") from exc
    if parsed.tzinfo is None:
        raise SemanticValidationError("CafeF ISO TradeDate lacks timezone")
    return parsed.astimezone(_VN_TIME).date().isoformat()


def classify_cafef_page_row(raw_trade_date_value, page=1, row_index=0):
    """Classify a raw CafeF TradeDate string as 'CURRENT_SNAPSHOT' or 'HISTORICAL'.

    Evidence only establishes the leading row of CafeF page 1 (page == 1 and
    row_index == 0) as the current/intraday snapshot that must NOT enter the
    historical daily time-series. Rows at any other position (page > 1 or
    row_index > 0) are historical daily rows.

    For the leading row (page == 1, row_index == 0), two snapshot sentinel
    patterns exist:
    1. DateTime.MinValue (year 0001): 1/1/0001 12:00:00 AM — seen when the
       intraday price is not yet available (e.g. BCC, CMG).
    2. A valid intraday AM/PM timestamp whose time component is NOT 17:00:00
       (market close), e.g. 9/16/2026 7:45:00 AM.

    Both patterns are classified as CURRENT_SNAPSHOT only for page == 1 and
    row_index == 0. Rows at other positions are not globally classified as
    snapshots.
    """
    if page != 1 or row_index != 0:
        return "HISTORICAL"
    if not isinstance(raw_trade_date_value, str):
        return "HISTORICAL"
    parsed_ampm = _parse_cafef_ampm(raw_trade_date_value)
    if parsed_ampm is not None:
        if parsed_ampm.year == CAFEF_DATETIME_MIN_VALUE.year:
            return "CURRENT_SNAPSHOT"
        if parsed_ampm.hour != 17 or parsed_ampm.minute != 0 or parsed_ampm.second != 0:
            return "CURRENT_SNAPSHOT"
        return "HISTORICAL"
    return "HISTORICAL"


def map_trade_history_row(row, symbol, exchange):
    required = {"Symbol", "TradeDate", "BasicPrice", "ClosePrice", "Volume", "AdjustPrice",
                "Ceiling", "Floor", "TotalValue", "AgreedVolume", "AgreedValue"}
    if not isinstance(row, dict) or not required.issubset(row):
        raise SemanticValidationError("CafeF TradeHistoryNew row has unexpected schema")
    if row["Symbol"].upper() != symbol.upper():
        raise SemanticValidationError("CafeF symbol identity mismatch")
    prices = {}
    for source, target in (("BasicPrice", "reference_price"), ("Ceiling", "ceiling_price"),
                           ("Floor", "floor_price")):
        value = _number(row[source], source)
        prices[target] = None if value is None else value * 1000
    matched_value = _number(row["TotalValue"], "TotalValue", integral=True)
    put_through_value = _number(row["AgreedValue"], "AgreedValue", integral=True)
    traded_value = (matched_value + put_through_value
                    if matched_value is not None and put_through_value is not None else None)
    return {
        "symbol": symbol.upper(), "exchange": exchange.upper(),
        "trade_date": cafef_trade_date(row["TradeDate"]), **prices,
        "matched_volume": _number(row["Volume"], "Volume", integral=True),
        "matched_value": matched_value,
        "put_through_volume": _number(row["AgreedVolume"], "AgreedVolume", integral=True),
        "put_through_value": put_through_value,
        "traded_value": traded_value,
        "cafef_close_price": None if row["ClosePrice"] is None else _number(row["ClosePrice"], "ClosePrice") * 1000,
        "cafef_adjust_price": None if row["AdjustPrice"] is None else _number(row["AdjustPrice"], "AdjustPrice") * 1000,
        "price_unit": PRICE_UNIT, "provider": "cafef", "acquisition_client": "direct",
        "rights_status": RIGHTS_STATUS, "execution_policy": EXECUTION_POLICY,
        "raw_fields": {field: row[field] for field in sorted(required)},
    }


def price_band_row_status(row):
    values = (row.get("reference_price"), row.get("ceiling_price"), row.get("floor_price"))
    if all(value is not None for value in values) and values[2] <= values[0] <= values[1]:
        return "VALID"
    return "INVALID_REQUIRED_MARKET_ROW"


def apply_invalid_row_policy(rows, policy):
    """Apply only an evidence-pinned exclusion; never repair provider values."""
    eligible, findings = [], []
    for row in rows:
        status = price_band_row_status(row)
        if status == "VALID":
            eligible.append(row)
            continue
        expected = policy if (row.get("provider"), row["symbol"], row["trade_date"]) == (
            policy.get("provider"), policy.get("symbol"), policy.get("trade_date")) else {}
        expected_raw = expected.get("expected_raw_fields", {})
        raw_match = set(expected_raw) == INVALID_ROW_EVIDENCE_FIELDS and all(
            row["raw_fields"].get(key) == value for key, value in expected_raw.items())
        safe = (expected.get("classification") == "PROVIDER_CORRUPT_ROW"
                and expected.get("row_status") == status
                and expected.get("policy") == "EXCLUDE_ROW" and raw_match)
        findings.append({"symbol": row["symbol"], "trade_date": row["trade_date"],
                         "row_status": status,
                         "classification": expected.get("classification", "UNRESOLVED") if safe else "UNRESOLVED",
                         "policy": "EXCLUDE_ROW" if safe else "FAIL_SYMBOL_WINDOW",
                         "safe": safe, "raw_fields": row["raw_fields"]})
    return eligible, findings


class CafeFSource(SourceAdapter):
    source_id = "cafef"
    verification_status = "RESEARCH_DEMO_ACCEPTED_RISK"

    def __init__(self, client=None):
        self.client = client or PublicJsonClient()

    def acquire(self, request: dict) -> dict:
        """Generic canonical acquisition remains closed; use the bounded named path."""
        self.require_verified_semantics()
        raise AssertionError("generic CafeF acquisition is not available")

    def acquire_trade_history_page(self, request: dict) -> dict:
        symbol = request["symbol"].upper()
        page_index = int(request.get("page_index", 1))
        page_size = int(request.get("page_size", 30))
        if not symbol.isalnum() or not 1 <= page_index <= 100 or page_size != 30:
            raise ValueError("invalid bounded CafeF request")
        response = self.client.get_json(TRADE_HISTORY_ENDPOINT, {
            "Symbol": symbol, "PageIndex": page_index, "PageSize": page_size,
        })
        payload = response["payload"]
        if not isinstance(payload, dict) or payload.get("Success") is not True or not isinstance(payload.get("Data"), list):
            raise SemanticValidationError("CafeF TradeHistoryNew envelope is invalid")
        return response
