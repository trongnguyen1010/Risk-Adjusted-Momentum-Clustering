"""Chạy frozen VCI monthly collector trên local bằng một key nhập ẩn."""
import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.vci_calendar_monthly import (
    archive_state, months, prepare, read_json, report, seal, write_json,
    validate_inputs, verify_state,
)

BUNDLE = ROOT / "tmp/vci_calendar_monthly_20261102_v1"
BUNDLE_PIN = "77c358a3883ba7bae88f63b78e185e8c4bbd64f2f2226845f1b34b72acc38de5"
STATE_HOME = ROOT / "data/corporate_actions/private/vnstock_vci_local_v1"
OUTPUT_ROOT = ROOT / "data/corporate_actions/work/vci_local_v1"
SDK_VERSION = "5.2.1"
PROGRESS_STATUSES = {"COLLECTION_EXPORTS_READY_FOR_REVIEW", "STOPPED_TIME_BUDGET",
    "STOPPED_SOURCE_OR_ROUTE_MISMATCH", "STOPPED_SCHEMA_REVIEW_REQUIRED",
    "STOPPED_POSSIBLE_ROW_TRUNCATION", "STOPPED_SDK_OR_EXPORT_ERROR_NO_RETRY",
    "STOPPED_SETUP_OR_INTEGRITY_ERROR"}


def validate_bundle(bundle=BUNDLE, pin=BUNDLE_PIN):
    body = (bundle / "manifest.json").read_bytes()
    if hashlib.sha256(body).hexdigest() != pin:
        raise ValueError("FROZEN_BUNDLE_MANIFEST_CHANGED")
    manifest = json.loads(body)
    for name, expected in manifest["files"].items():
        if Path(name).name != name or hashlib.sha256((bundle / name).read_bytes()).hexdigest() != expected:
            raise ValueError("FROZEN_BUNDLE_FILE_CHANGED")
    values = [read_json(bundle / n) for n in ("plan.json", "scope.json", "pilot_gate.json")]
    validate_inputs(*values)
    return values


def child_environment(environ, state_home):
    if environ.get("VNSTOCK_PROFILE") or environ.get("VNSTOCK_API_BASE"):
        raise ValueError("CUSTOM_SDK_PROFILE_OR_SERVER_REQUIRES_REVIEW")
    result = dict(environ)
    result.pop("VNSTOCK_API_KEY", None)
    # One stable directory for this installation, never randomize it per run.
    result["VNSTOCK_HOME"] = str(state_home.resolve())
    result["PYTHONUTF8"] = "1"
    return result


def progress_line(line, window_ids):
    if len(line) > 600:
        return None
    try:
        value = json.loads(line)
    except ValueError:
        return None
    if not isinstance(value, dict) or not set(value) <= {"event", "month", "completed", "total", "rows", "status"}:
        return None
    if value.get("event") not in {"QUERY_STARTED", "QUERY_SAVED", "FINISHED"}:
        return None
    if "status" in value and value["status"] not in PROGRESS_STATUSES:
        return None
    if "month" in value and value["month"] not in window_ids:
        return None
    if any(type(value[k]) is not int or not 0 <= value[k] <= 20000
           for k in ("completed", "total", "rows") if k in value):
        return None
    return value


def execute_child(command, key, environment, window_ids, timeout):
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                            errors="replace", env=environment)
    try:
        proc.stdin.write(key)
        proc.stdin.close()
        key = None
        messages = queue.Queue()
        def reader():
            try:
                for line in proc.stdout:
                    if len(line) <= 600:
                        messages.put(line)
            finally:
                messages.put(None)
        threading.Thread(target=reader, daemon=True).start()
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(command, timeout)
            try:
                line = messages.get(timeout=1)
            except queue.Empty:
                continue
            if line is None:
                break
            item = progress_line(line, window_ids)
            if item is not None:
                print(json.dumps(item), flush=True)
        return proc.wait(timeout=15)
    finally:
        key = None
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=15)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra input/SDK version, không login")
    parser.add_argument("--resume", type=Path, help="Chỉ ZIP budget-stop đã verify, không ZIP auth error")
    args = parser.parse_args()
    try:
        plan, scope, gate = validate_bundle()
        environment = child_environment(os.environ, STATE_HOME)
        if importlib.metadata.version("vnstock") != SDK_VERSION:
            raise ValueError("SDK_VERSION_MISMATCH_NEED_5_2_1")
        if args.resume:
            previous = verify_state(args.resume)
            if json.loads(previous["result.json"])["status"] not in {
                    "STOPPED_TIME_BUDGET", "COLLECTION_EXPORTS_READY_FOR_REVIEW"}:
                raise ValueError("FAILED_SOURCE_OR_AUTH_STATE_CANNOT_AUTO_RESUME")
            if any(json.loads(previous[n]) != v for n, v in zip(
                    ("plan.json", "scope.json", "pilot_gate.json"), (plan, scope, gate))):
                raise ValueError("RESUME_INPUT_MISMATCH")
        if args.check:
            print(json.dumps({"status": "LOCAL_CHECK_PASS_AUTH_NOT_TESTED", "sdk_version": SDK_VERSION,
                              "scope_tickers": 1522, "windows": 84, "login_calls": 0}))
            return 0
    except Exception as exc:
        # Input/version errors do not read a Secret or attempt SDK import/login.
        reason = ("SDK_NOT_INSTALLED_RUN_PIP_COMMAND" if isinstance(exc, importlib.metadata.PackageNotFoundError)
                  else str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        allowed = {"FROZEN_BUNDLE_MANIFEST_CHANGED", "FROZEN_BUNDLE_FILE_CHANGED",
            "CUSTOM_SDK_PROFILE_OR_SERVER_REQUIRES_REVIEW", "SDK_VERSION_MISMATCH_NEED_5_2_1",
            "FAILED_SOURCE_OR_AUTH_STATE_CANNOT_AUTO_RESUME", "RESUME_INPUT_MISMATCH",
            "PLAN_REQUIRES_REVIEW", "C8_V2_SCOPE_MISMATCH", "SUCCESSFUL_PILOT_REQUIRED"}
        allowed.add("SDK_NOT_INSTALLED_RUN_PIP_COMMAND")
        print(json.dumps({"status": "LOCAL_PRECHECK_FAILED", "reason": reason if reason in allowed else type(exc).__name__}))
        return 2
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass("VNSTOCK API key (nhap an, Enter de chay): ").strip()
        if not key or any(c.isspace() for c in key) or key[:1] in {"'", '"'}:
            print("KEY_INPUT_INVALID_NO_LOGIN")
            return 2
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        print("KEY_INPUT_CANCELLED_NO_LOGIN")
        return 2
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = OUTPUT_ROOT / ("run-" + stamp) / "state"
    output.parent.mkdir(parents=True, exist_ok=False)
    STATE_HOME.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(BUNDLE / "vci_calendar_monthly.py"),
               "--inputs", str(BUNDLE), "--output", str(output)]
    if args.resume:
        command += ["--resume", str(args.resume)]
    windows = months(plan["start"], plan["end"])
    wrapper_status = "STOPPED_LOCAL_WRAPPER_REVIEW_REQUIRED"
    try:
        execute_child(command, key, environment, {w["id"] for w in windows}, plan["parent_timeout_seconds"])
    except subprocess.TimeoutExpired:
        wrapper_status = "STOPPED_LOCAL_TIMEOUT_REVIEW_REQUIRED"
    except (Exception, KeyboardInterrupt):
        pass
    finally:
        key = None
    if not (output / "manifest.json").exists():
        try:
            if not output.exists():
                prepare(output, plan, scope, gate, args.resume)
            report(output, plan, windows, wrapper_status, None)
        except Exception:
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / "wrapper_failure.json", {"status": wrapper_status, "resumable": False})
            seal(output)
    archive = OUTPUT_ROOT / ("delta-vci-state-local-" + stamp + ".zip")
    archive_state(output, archive)
    value = read_json(output / "result.json") if (output / "result.json").exists() else {"status": wrapper_status}
    print(json.dumps({k: value[k] for k in ("status", "completed_window_count", "total_windows",
        "sdk_export_rows_cumulative", "resumable") if k in value}), flush=True)
    code = value.get("diagnostic", {}).get("sdk_code")
    if code in {"VNSTOCK_AUTH_DEVICE_LIMIT", "VNSTOCK_AUTH_PROTOCOL", "VNSTOCK_AUTH_CREDENTIAL_INVALID"}:
        print("SDK_CODE:", code)
    print("OUTPUT_ZIP:", archive, flush=True)
    return 0 if value["status"] == "COLLECTION_EXPORTS_READY_FOR_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
