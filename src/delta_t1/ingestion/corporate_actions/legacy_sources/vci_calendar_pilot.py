"""Pilot lịch sự kiện VCI qua API Vnstock được tài liệu hoá; không gọi HNX.

Chỉ lưu SDK exports để review, không coi chúng là raw HTTP hoặc canonical events.
"""
import hashlib
import importlib.metadata
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

if __package__:
    from .vnstock_auth_diagnostic import exception_detail
else:
    from vnstock_auth_diagnostic import exception_detail

WINDOWS = [("2019-02-01", "2019-02-28"), ("2024-11-01", "2024-11-30"),
           ("2025-08-01", "2025-08-31")]
SDK_VERSION = "5.2.1"


def safe_error(exc, stage, key=None):
    """Structured diagnostics, plus SDK text redacted with a known key when supplied."""
    detail = {"setup_stage": stage, "error_type": type(exc).__name__}
    for name in ("status_code", "status", "code"):
        value = getattr(exc, name, None)
        if type(value) is int and 100 <= value <= 599:
            detail["http_status"] = value
            break
    if isinstance(exc, (ModuleNotFoundError, AttributeError)):
        name = getattr(exc, "name", None)
        if isinstance(name, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,100}", name):
            detail["missing_name"] = name
    cause = exc.__cause__
    if cause is not None:
        detail["cause_type"] = type(cause).__name__
    if key is not None:
        # SDK-defined code/message/action, redacted using the known secret.
        detail.update(exception_detail(exc, key, stage))
    return detail


def seal_report(output, report):
    with (output / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()
             if p.is_file() and p.name != "manifest.json"}
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump({"artifact_type": "vci-calendar-sdk-pilot-v3", "files": files}, stream, indent=2)


def setup_failure(output, status, diagnostic):
    output.mkdir(parents=True, exist_ok=True)
    report = {"stage": "VCI_CORPORATE_CALENDAR_PILOT_V3", "status": status,
              "setup_diagnostic": diagnostic, "required_sdk_version": SDK_VERSION,
              "queries": [], "logical_calls": None if diagnostic.get("setup_stage") == "PILOT_EXECUTION" else 0,
              "underlying_http_count": "NOT_INSTRUMENTED", "hnx_requests": 0,
              "automatic_retry": False, "canonical_build": False, "pit_status": "NOT_PROMOTED"}
    # Preserve a partially written pilot rather than overwriting its artifacts.
    if (output / "result.json").exists():
        with (output / "setup_error.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
    else:
        seal_report(output, report)
    print(json.dumps({"status": status, **diagnostic}, ensure_ascii=False), flush=True)
    return 2


def pilot(output, fetch, *, sleep=time.sleep, redact_key=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    queries = []
    status = "PILOT_PARTIAL_FOR_REVIEW"
    try:
        for index, (start, end) in enumerate(WINDOWS):
            if index:
                sleep(8)
            entry = {"start": start, "end": end, "event_type": "dividend", "limit": 20000}
            queries.append(entry)
            print(f"VCI PILOT {index + 1}/3: {start} -> {end}", flush=True)
            # One logical SDK call; no outer retry, fallback provider or HNX request.
            frame = fetch(start=start, end=end, event_type="dividend", limit=20000)
            body = frame.to_json(orient="records", date_format="iso", force_ascii=False).encode("utf-8")
            if redact_key and redact_key.encode() in body:
                raise ValueError("SDK_EXPORT_CONTAINS_SECRET")
            rows = json.loads(body)
            path = output / f"sdk_export_{index + 1}.json"
            path.write_bytes(body)
            attrs = getattr(frame, "attrs", {})
            source = "vci" if attrs.get("source") == "vci" else "UNVERIFIED"
            route = attrs.get("route")
            route = route if route == "reference.events.calendar" else "UNVERIFIED"
            entry.update(rows=len(rows), columns=list(frame.columns), export_file=path.name,
                         export_sha256=hashlib.sha256(body).hexdigest(), source=source,
                         route=route, fetched_at=datetime.now(timezone.utc).isoformat())
            (output / f"query_{index + 1}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
            if source != "vci":
                status = "STOPPED_UNVERIFIED_SOURCE_METADATA"
                break
            if len(rows) >= 20000:
                status = "STOPPED_POSSIBLE_ROW_TRUNCATION"
                break
            if not {"symbol", "ex_right_date", "record_date"} <= set(frame.columns):
                status = "STOPPED_SCHEMA_REVIEW_REQUIRED"
                break
        else:
            status = "PILOT_EXPORTS_READY_FOR_REVIEW"
    except Exception as exc:
        # Provider exception text may contain credentials. Never persist or print it.
        status = "STOPPED_SDK_ERROR_NO_RETRY"
        queries[-1].update(safe_error(exc, "CALENDAR_FETCH_OR_EXPORT", redact_key))
    finally:
        report = {"stage": "VCI_CORPORATE_CALENDAR_PILOT_V3", "status": status,
                  "sdk": "vnstock", "required_sdk_version": SDK_VERSION, "queries": queries,
                  "logical_calls": len(queries), "underlying_http_count": "NOT_INSTRUMENTED",
                  "source_bytes_basis": "SDK_EXPORT_BYTES_NOT_ORIGINAL_HTTP_RESPONSE",
                  "automatic_retry": False, "hnx_requests": 0, "canonical_build": False,
                  "pit_status": "NOT_PROMOTED", "historical_identity": "NOT_CERTIFIED",
                  "history_completeness": "NOT_CERTIFIED",
                  "next_step": "Review schema, historical samples, raw-HTTP provenance limitations and coverage before any bulk collection."}
        seal_report(output, report)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        print("REFUSE_OVERWRITE")
        return 2
    # Key is passed through stdin, never argv, an output file, or a shell command.
    secret = sys.stdin.read().strip()
    if not secret:
        return setup_failure(args.output, "MISSING_API_KEY", {"setup_stage": "SECRET_INPUT"})
    stage = "SDK_VERSION"
    diagnostic = {}
    try:
        installed = importlib.metadata.version("vnstock")
        diagnostic["installed_sdk_version"] = installed
        if installed != SDK_VERSION:
            return setup_failure(args.output, "SDK_VERSION_MISMATCH", {**diagnostic, "setup_stage": stage})
        stage = "SDK_IMPORT"
        import vnstock
        stage = "SDK_LOGIN"
        login = vnstock.login(secret)
        diagnostic["login_return_type"] = type(login).__name__
        if login is False:
            return setup_failure(args.output, "SDK_LOGIN_RETURNED_FALSE", {**diagnostic, "setup_stage": stage})
        stage = "SDK_STATUS"
        status = vnstock.status()
        diagnostic["status_return_type"] = type(status).__name__
        if not isinstance(status, dict):
            return setup_failure(args.output, "SDK_STATUS_SCHEMA_MISMATCH", {**diagnostic, "setup_stage": stage})
        tier = status.get("tier")
        if tier in {None, "guest"}:
            return setup_failure(args.output, "AUTHENTICATED_ACCOUNT_REQUIRED", {**diagnostic, "setup_stage": stage})
        stage = "REFERENCE_INIT"
        from vnstock import Reference
        reference = Reference()
        stage = "CALENDAR_INTERFACE"
        fetch = reference.events.calendar
        stage = "PILOT_EXECUTION"
        result = pilot(args.output, fetch, redact_key=secret)
        print(result["status"], flush=True)
        return 0 if result["status"] == "PILOT_EXPORTS_READY_FOR_REVIEW" else 2
    except Exception as exc:
        return setup_failure(args.output, "SDK_SETUP_ERROR", {**diagnostic, **safe_error(exc, stage, secret)})
    finally:
        secret = None


if __name__ == "__main__":
    raise SystemExit(main())
