"""Bounded CafeF public-path adapter for private research/demo acquisition."""
import re
from datetime import datetime, timedelta, timezone

from .base import PublicJsonClient, SemanticValidationError, SourceAdapter


TRADE_HISTORY_ENDPOINT = "https://cafef.vn/du-lieu/Ajax/PageNew/TradeHistoryNew.ashx"
RIGHTS_STATUS = "RIGHTS_NOT_VERIFIED"
EXECUTION_POLICY = "ACCEPTED_RESEARCH_RISK"
PRICE_UNIT = "VND_PER_SHARE"
ADAPTER_VERSION = "cafef-research-demo-1"
_DOTNET_DATE = re.compile(r"^/?Date\((\d+)(?:[+-]\d+)?\)/?$")
_VN_TIME = timezone(timedelta(hours=7))


def _number(value, field, *, integral=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SemanticValidationError(f"CafeF {field} must be numeric or null")
    return int(value) if integral else float(value)


def cafef_trade_date(value):
    if not isinstance(value, str):
        raise SemanticValidationError("CafeF TradeDate must be a string")
    normalized = value.replace("\\/", "/").strip("/")
    match = _DOTNET_DATE.match(normalized)
    if match:
        return datetime.fromtimestamp(int(match.group(1)) / 1000, timezone.utc).astimezone(_VN_TIME).date().isoformat()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SemanticValidationError("unsupported CafeF TradeDate") from exc
    if parsed.tzinfo is None:
        raise SemanticValidationError("CafeF ISO TradeDate lacks timezone")
    return parsed.astimezone(_VN_TIME).date().isoformat()


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
    }


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
