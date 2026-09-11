"""Executable table contracts (project format, NOT a JSON Schema validator)."""
import math
from datetime import date, datetime
from importlib.resources import files
import json


def schema(table):
    return json.loads(files("delta_t1").joinpath("schemas", table + ".json").read_text(encoding="utf-8"))


def coerce(value, field):
    if value is None or value == "":
        if field.get("nullable", False):
            return None
        raise ValueError("required value missing")
    kind = field["type"]
    if kind == "string":
        if not isinstance(value, str) or not value.strip():
            raise ValueError("expected non-empty string")
        result = value.strip()
    elif kind in ("number", "integer"):
        if isinstance(value, bool):
            raise ValueError("boolean is not a number")
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite number")
        if kind == "integer":
            if not result.is_integer():
                raise ValueError("expected integer")
            result = int(result)
    elif kind == "boolean":
        if value not in (True, False, "true", "false") or type(value) in (int, float):
            raise ValueError("expected true/false")
        result = value is True or value == "true"
    elif kind == "date":
        result = date.fromisoformat(value).isoformat()
        if result != value:
            raise ValueError("expected YYYY-MM-DD")
    elif kind == "datetime":
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("timezone required")
        result = dt.isoformat()
    elif kind == "object":
        if not isinstance(value, dict):
            raise ValueError("expected object")
        result = value
    elif kind == "array":
        if not isinstance(value, list):
            raise ValueError("expected array")
        result = value
    else:
        raise ValueError("unknown contract type: " + kind)
    if "enum" in field and result not in field["enum"]:
        raise ValueError("value outside enum")
    if "min" in field and result < field["min"]:
        raise ValueError("value below minimum")
    if "exclusive_min" in field and result <= field["exclusive_min"]:
        raise ValueError("value must exceed minimum")
    return result


def normalize(table, row, defaults=None, mapping=None, multipliers=None):
    """Mapping is canonical field -> provider field. Unknown provider columns stay in raw."""
    result = {}
    defaults, mapping, multipliers = defaults or {}, mapping or {}, multipliers or {}
    for name, field in schema(table)["fields"].items():
        value = row.get(mapping.get(name, name), defaults.get(name))
        try:
            result[name] = coerce(value, field)
            if name in multipliers and result[name] is not None:
                result[name] = coerce(result[name] * multipliers[name], field)
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError(f"{table}.{name}: {exc}") from exc
    return result


def validate_rows(table, rows):
    contract = schema(table)
    seen = set()
    for row in rows:
        if set(row) != set(contract["fields"]):
            raise ValueError(f"{table}: output fields differ from contract")
        normalize(table, row)
        key = tuple(row[k] for k in contract["primary_key"])
        if key in seen:
            raise ValueError(f"{table}: duplicate key {key}")
        seen.add(key)
