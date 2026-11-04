"""Chẩn đoán SDK đang có, không login/calendar hoặc xuất credential cache."""
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit
import zipfile

SDK_VERSION = "5.2.1"
ERROR_CODES = {"VNSTOCK_AUTH_DEVICE_LIMIT", "VNSTOCK_AUTH_PROTOCOL",
               "VNSTOCK_AUTH_DEVICE_NOT_REGISTERED", "VNSTOCK_AUTH_DEVICE_INACTIVE",
               "VNSTOCK_AUTH_CREDENTIAL_INVALID", "VNSTOCK_AUTH_CREDENTIAL_MISSING"}


def safe_error(exc):
    code = getattr(exc, "code", None)
    return {"sdk_code": code if code in ERROR_CODES else "UNRECOGNIZED_ERROR",
            "exception_class": type(exc).__name__ if type(exc).__name__ in {
                "AuthError", "EntitlementError", "InternalError", "NetworkError",
                "ImportError", "ModuleNotFoundError"} else "OTHER_EXCEPTION"}


def summarize_environment(value):
    if not isinstance(value, dict):
        return {"status": "UNEXPECTED_ENVIRONMENT_SHAPE"}
    base = value.get("api_base")
    try:
        host = urlsplit(base).hostname if isinstance(base, str) else None
    except ValueError:
        host = None
    # No arbitrary host/path/query/profile string is exported.
    known_hosts = {"vnstocks.com", "www.vnstocks.com", "api.vnstocks.com", "hq.vnstocks.com"}
    host = host if host in known_hosts else "OTHER_OR_UNAVAILABLE"
    state = value.get("state_dir")
    path = Path(state) if isinstance(state, str) and state else None
    return {"status": "ENVIRONMENT_READ", "api_base_host": host,
            "api_base_field_present": "api_base" in value,
            "api_base_is_string": isinstance(base, str),
            "api_base_is_empty": base in (None, ""),
            "profile_is_default": value.get("profile") in (None, "", "default"),
            "state_dir_is_default": path == Path.home() / ".vnstock" if path else None,
            "state_dir_exists": path.is_dir() if path else None,
            "state_dir_has_files": any(path.iterdir()) if path and path.is_dir() else None}


def summarize_status(value):
    if not isinstance(value, dict):
        return {"status": "UNEXPECTED_ACCOUNT_STATUS_SHAPE"}
    device = value.get("device_id")
    tier = value.get("tier")
    return {"status": "ACCOUNT_STATUS_READ",
            "authenticated": value.get("authenticated") if type(value.get("authenticated")) is bool else None,
            "tier": tier if tier in {"guest", "free", "community", "bronze", "silver", "gold", "golden", "enterprise"} else "UNVERIFIED",
            "device_id_present": isinstance(device, str) and bool(device),
            "device_id_sha256": hashlib.sha256(device.encode()).hexdigest() if isinstance(device, str) and device else None}


def inspect_sdk(account):
    report = {}
    for name, summarize in [("environment", summarize_environment), ("status", summarize_status)]:
        try:
            # SDK handles its own local store; do not inspect credential files.
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                value = getattr(account, name)()
            report[name] = summarize(value)
        except Exception as exc:
            report[name] = safe_error(exc)
    return report


def worker():
    report = {"stage": "VNSTOCK_ENVIRONMENT_DIAGNOSTIC_V2",
              "explicit_login_calls": 0, "calendar_calls": 0,
              "network_requests": "NOT_INSTRUMENTED_SDK_STATUS_MAY_REFRESH",
              "credential_files_exported": False, "secret_read": False,
              "env_overrides_present": {name: bool(os.environ.get(name)) for name in
                  ("VNSTOCK_HOME", "VNSTOCK_PROFILE", "VNSTOCK_API_BASE", "VNSTOCK_API_KEY")}}
    try:
        version = importlib.metadata.version("vnstock")
        report["sdk_version"] = version if version == SDK_VERSION else "OTHER_VERSION"
        if version != SDK_VERSION:
            report["status"] = "SDK_VERSION_MISMATCH_NO_IMPORT"
            return report
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from vnstock import account
        details = inspect_sdk(account)
        report["environment"] = details["environment"]
        report["account_status"] = details["status"]
        report["status"] = "READ_ONLY_CHECK_RETURNED"
    except Exception as exc:
        report.update(status="DIAGNOSTIC_ERROR", diagnostic=safe_error(exc))
    return report


def run_kaggle_check():
    # Run the embedded source in a finite child. No API key is requested or sent.
    result = {"stage": "VNSTOCK_ENVIRONMENT_DIAGNOSTIC_V2", "status": "DIAGNOSTIC_PROCESS_FAILED",
              "explicit_login_calls": 0, "calendar_calls": 0, "secret_read": False}
    try:
        child = subprocess.run([sys.executable, "-c", DIAGNOSTIC_SOURCE +
            '\nprint("DELTA_ENV_RESULT=" + json.dumps(worker()))'],
            capture_output=True, text=True, encoding="utf-8", timeout=45)
        lines = [line[len("DELTA_ENV_RESULT="):] for line in child.stdout.splitlines()
                 if line.startswith("DELTA_ENV_RESULT=")]
        if child.returncode == 0 and len(lines) == 1:
            result = json.loads(lines[0])
    except subprocess.TimeoutExpired:
        result["status"] = "DIAGNOSTIC_TIMEOUT_NO_RETRY"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = Path("/kaggle/working") / ("delta-vnstock-env-v2-" + stamp + ".zip")
    # Only this allowlisted JSON report enters ZIP, never HOME/SDK cache.
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("environment_diagnostic.json", json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("TẢI ZIP CHẨN ĐOÁN:", target)
    return result


# The packager supplies DIAGNOSTIC_SOURCE before calling run_kaggle_check().
