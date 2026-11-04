"""Bounded KBS SDK exports for six corporate-action investigations, no promotion."""
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import time
import zipfile

SDK_VERSION = "5.2.1"
TARGETS = [("GSP", "2021-08-23"), ("DTP", "2021-12-20"), ("ASG", "2020-02-13"),
           ("KPF", "2021-01-20"), ("LCG", "2019-12-13"), ("DXG", "2023-12-15")]
STATUSES = {"SDK_EXPORTS_READY_FOR_REVIEW", "PILOT_PARTIAL_FOR_REVIEW", "STOPPED_SDK_OR_ACCESS_ERROR",
    "STOPPED_SOURCE_OR_ROUTE_MISMATCH", "STOPPED_EXPORT_LIMIT", "STOPPED_LOCAL_TIMEOUT",
    "STOPPED_LOCAL_WRAPPER_ERROR", "STOPPED_SETUP_ERROR", "CANCELLED_BY_USER"}
KNOWN_CODES = {"VNSTOCK_AUTH_CREDENTIAL_INVALID", "VNSTOCK_AUTH_DEVICE_LIMIT_REACHED", "VNSTOCK_AUTH_REQUIRED",
    "VNSTOCK_ACCESS_DENIED", "VNSTOCK_RATE_LIMITED", "VNSTOCK_FEATURE_REMOVED", "VNSTOCK_ROUTE_NOT_MIGRATED",
    "VNSTOCK_ROUTE_NOT_FROZEN", "VNSTOCK_SOURCE_BLOCKED", "VNSTOCK_AUTH_DEVICE_REVOKED"}
ALLOWED_ERRORS = {"AuthError", "EntitlementError", "AccessDeniedError", "ChallengeRequiredError", "CircuitOpenError",
    "DataSourceBlockedError", "RateLimitedError", "NetworkError", "ProviderError", "SchemaError", "InputError",
    "UnsupportedError", "InternalError", "ValueError", "TypeError", "AttributeError", "ModuleNotFoundError",
    "SSLError", "TimeoutError", "OSError", "KeyboardInterrupt", "RuntimeError"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def config_check(config):
    if config.get("sdk_version") != SDK_VERSION or config.get("source") != "kbs" or config.get("route") != "reference.company.events":
        raise ValueError("FROZEN_SDK_ROUTE_REQUIRED")
    if config.get("native_route") != "fundamental.company.events":
        raise ValueError("EXACT_NATIVE_COMPANY_EVENTS_ROUTE_REQUIRED")
    if [(t["ticker"], t["record_date"]) for t in config["targets"]] != TARGETS or config["max_logical_queries"] != 6:
        raise ValueError("EXACT_SIX_TARGET_SCOPE_REQUIRED")
    if not 8 <= config["interval_seconds"] <= 60 or not 60 <= config["parent_timeout_seconds"] <= 600:
        raise ValueError("BOUNDED_PILOT_LIMITS_REQUIRED")
    if not 1 <= config["max_export_rows"] <= 20000 or not 1 <= config["max_export_bytes"] <= 8000000:
        raise ValueError("EXPORT_LIMIT_EXCEEDED")
    if not config["tls_verification"] or any(config[k] for k in ["automatic_retry", "provider_fallback", "hnx_requests_allowed", "canonical_build", "field_approval"]):
        raise ValueError("STRICT_PILOT_ONLY")


def child_environment(environ, state_home):
    if environ.get("VNSTOCK_API_BASE") or environ.get("VNSTOCK_PROFILE"):
        raise ValueError("CUSTOM_SDK_SERVER_OR_PROFILE_REQUIRES_REVIEW")
    env = dict(environ)
    env.pop("VNSTOCK_API_KEY", None)
    # Reuse the existing VCI SDK installation state. Never randomize home/device.
    env["VNSTOCK_HOME"] = str(state_home.resolve())
    env["PYTHONUTF8"] = "1"
    return env


def sdk_precheck():
    installed = importlib.metadata.version("vnstock")
    if installed != SDK_VERSION:
        raise ValueError("SDK_VERSION_MISMATCH_NEED_5_2_1")
    # find_spec of the top-level package locates it without importing/logging in.
    spec = importlib.util.find_spec("vnstock")
    if spec is None or not spec.origin:
        raise ValueError("SDK_LOCATION_NOT_FOUND")
    folder = Path(spec.origin).parent
    hashes = {}
    for name in ["__init__.py", "account.py", "ui/reference.py", "_frame.py"]:
        p = folder / name
        hashes[name] = sha(p.read_bytes())
    return {"sdk_version": installed, "sdk_source_hashes": hashes, "sdk_imported": False,
        "authentication_tested": False, "network_requests": 0}


def json_value(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value): return None
        if not math.isfinite(value): return {"nonfinite_float_literal": str(value)}
        return value  # Python JSON repr preserves float precision; no pandas default10-digit rounding.
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, Decimal): return {"decimal_literal": str(value)}
    if isinstance(value, dict): return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [json_value(v) for v in value]
    if type(value).__name__ in {"NAType", "NaTType"}: return None
    if hasattr(value, "item"): return json_value(value.item())
    raise ValueError("UNSUPPORTED_SDK_CELL_TYPE")


def write_json(output, name, value, secret=None):
    body = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    if secret and secret.encode() in body:
        raise ValueError("SECRET_IN_EXPORT_REFUSED")
    path = output / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream: stream.write(body)
    return sha(body)


def safe_error(exc):
    kind = type(exc).__name__
    result = {"error_type": kind if kind in ALLOWED_ERRORS else "OtherError"}
    for name in ["status_code", "http_status", "status"]:
        value = getattr(exc, name, None)
        if type(value) is int and 100 <= value <= 599:
            result["http_status"] = value; break
    # Never serialize arbitrary exception messages, auth replies, keys or tokens.
    candidates = [getattr(exc, "code", None)]
    candidates += re.findall(r"\bVNSTOCK_[A-Z0-9_]{1,80}\b", str(exc))
    for value in candidates:
        if isinstance(value, str) and value in KNOWN_CODES:
            result["sdk_code"] = value; break
    return result


def frame_export(frame, ticker, config):
    columns = [str(c) for c in frame.columns]
    data = [[json_value(v) for v in row] for row in frame.itertuples(index=False, name=None)]
    if len(data) > config["max_export_rows"]:
        raise ValueError("SDK_EXPORT_ROW_LIMIT")
    if any(len(row) != len(columns) for row in data):
        raise ValueError("SDK_EXPORT_ROW_SHAPE_CHANGED")
    attrs = getattr(frame, "attrs", {})
    # UI method and native route are distinct: the installed5.2.1 catalog lists
    # fundamental.company.events for both KBS and VCI. Never infer from columns.
    metadata = {}
    for key in ("source", "route"):
        value = attrs.get(key)
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,95}", value):
            metadata[key] = value
    source = "kbs" if metadata.get("source", "").lower() == "kbs" else "UNVERIFIED"
    route = config["native_route"] if metadata.get("route") == config["native_route"] else "UNVERIFIED"
    exported = {"classification": "SDK_EXPORT_NOT_RAW_HTTP_OR_CANONICAL_EVENTS", "query_ticker": ticker,
        "fetched_at": utc_now(), "source": source, "route": route, "columns": columns,
        "requested_sdk_method": config["route"], "sdk_metadata": metadata,
        "dtypes": [str(v) for v in frame.dtypes], "data": data,
        "duplicate_column_names": len(set(columns)) != len(columns)}
    if len(json.dumps(exported, ensure_ascii=False, allow_nan=False).encode()) > config["max_export_bytes"]:
        raise ValueError("SDK_EXPORT_BYTE_LIMIT")
    profile = [{"column_position": i, "name": name, "dtype": exported["dtypes"][i],
        "null_count": sum(row[i] is None for row in data), "non_null_count": sum(row[i] is not None for row in data)} for i, name in enumerate(columns)]
    return exported, profile


def collect(output, config, fetch, *, secret=None, sleep=time.sleep, emit=print):
    config_check(config)
    queries = []
    status = "SDK_EXPORTS_READY_FOR_REVIEW"
    for index, target in enumerate(config["targets"]):
        if index: sleep(config["interval_seconds"])
        ticker = target["ticker"]
        entry = {"ticker": ticker, "target_record_date_for_later_review": target["record_date"], "started_at": utc_now()}
        queries.append(entry)
        emit(json.dumps({"event": "QUERY_STARTED", "ticker": ticker, "completed": index, "total": 6}), flush=True)
        try:
            frame = fetch(ticker)
        except Exception as exc:
            entry.update(status="SDK_ERROR", **safe_error(exc))
            if type(exc).__name__ == "InputError" and "http_status" not in entry and "sdk_code" not in entry:
                entry["status"] = "QUARANTINED_INPUT_ERROR"
                status = "PILOT_PARTIAL_FOR_REVIEW"
                write_json(output, f"queries/{ticker}.json", entry, secret)
                continue
            status = "STOPPED_SDK_OR_ACCESS_ERROR"
            write_json(output, f"queries/{ticker}.json", entry, secret)
            break
        try:
            export, profile = frame_export(frame, ticker, config)
            entry.update(rows=len(export["data"]), source=export["source"], route=export["route"], sdk_metadata=export["sdk_metadata"],
                columns=export["columns"], column_profile=profile, export_file=f"sdk_exports/{ticker}.json")
            entry["export_sha256"] = write_json(output, entry["export_file"], export, secret)
            entry["status"] = "SDK_EXPORT_SAVED" if export["data"] else "EMPTY_EXPORT_NOT_NO_EVENT_PROOF"
            if export["source"] != "kbs" or export["route"] != config["native_route"]:
                entry["status"] = "UNVERIFIED_SOURCE_OR_ROUTE"
                status = "STOPPED_SOURCE_OR_ROUTE_MISMATCH"
            elif export["duplicate_column_names"]:
                entry["status"] = "DUPLICATE_COLUMNS_PRESERVED_IN_MATRIX"
                status = "PILOT_PARTIAL_FOR_REVIEW"
        except Exception as exc:
            entry.update(status="EXPORT_REVIEW_REQUIRED", **safe_error(exc))
            if isinstance(exc, ValueError) and str(exc) in {"SDK_EXPORT_ROW_LIMIT", "SDK_EXPORT_BYTE_LIMIT"}:
                status = "STOPPED_EXPORT_LIMIT"
            else:
                status = "PILOT_PARTIAL_FOR_REVIEW"
        write_json(output, f"queries/{ticker}.json", entry, secret)
        emit(json.dumps({"event": "QUERY_SAVED", "ticker": ticker, "rows": entry.get("rows", 0),
            "completed": len(queries), "total": 6}), flush=True)
        if status.startswith("STOPPED_"): break
    result = {"stage": config["stage"], "status": status, "logical_company_event_calls": len(queries),
        "total_tickers": 6, "queries": queries, "underlying_http_count": "NOT_INSTRUMENTED_SDK_INTERNALS",
        "history_coverage": "ONLY_ROWS_RETURNED_BY_SDK_NOT_PROVEN_FULL_PERIOD_OR_NO_EVENT",
        "raw_sdk_exports": True, "raw_http_bytes_captured": False,
        "numeric_precision": "Python JSON float representation; SDK upstream transformations remain unverified",
        "canonical_build": False, "field_approval": False, "pit_status": "NOT_PROMOTED",
        "historical_identity": "UNVERIFIED", "outer_retry": False, "provider_fallback": False, "hnx_requests": 0}
    write_json(output, "result.json", result, secret)
    emit(json.dumps({"event": "FINISHED", "status": status}), flush=True)
    return result


def seal_and_zip(output, archive, execution):
    write_json(output, "execution.json", execution)
    files = {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in output.rglob("*") if p.is_file()}
    write_json(output, "manifest.json", {"artifact_type": "kbs-corporate-action-sdk-pilot-v1", "files": files,
        "classification": "SDK_EXPORT_NOT_RAW_HTTP_OR_CANONICAL_EVENTS", "canonical_build": False})
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output.rglob("*")):
            if p.is_file(): z.write(p, p.relative_to(output).as_posix())
    return str(archive)
