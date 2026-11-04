"""Pilot KBS corporate actions trên local; key nhập ẩn, kết quả ZIP riêng."""
import argparse
import contextlib
from datetime import datetime, timezone
import getpass
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.kbs_pilot import (
    TARGETS, STATUSES, child_environment, collect, config_check, safe_error, sdk_precheck, seal_and_zip, sha, write_json,
)
CONFIG = ROOT / "configs/data/corporate_actions/kbs_events_pilot_v1.json"
OUTPUT_ROOT = ROOT / "data/corporate_actions/work/kbs_pilot_v1"
STATE_HOME = ROOT / "data/corporate_actions/private/vnstock_vci_local_v1"


def progress(line):
    try: value = json.loads(line)
    except ValueError: return None
    if not isinstance(value, dict) or not set(value) <= {"event", "ticker", "completed", "total", "rows", "status"}: return None
    if not isinstance(value.get("event"), str) or value["event"] not in {"QUERY_STARTED", "QUERY_SAVED", "FINISHED"}: return None
    if "ticker" in value and (not isinstance(value["ticker"], str) or value["ticker"] not in {t for t, _ in TARGETS}): return None
    if "status" in value and (not isinstance(value["status"], str) or value["status"] not in STATUSES): return None
    if any(type(value[k]) is not int or not 0 <= value[k] <= 20000 for k in ["completed", "total", "rows"] if k in value): return None
    return value


def execute_child(command, secret, env, timeout):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace", env=env)
    try:
        process.stdin.write(json.dumps({"api_key": secret}))
        process.stdin.close()
        lines = queue.Queue()
        def read():
            try:
                while True:
                    line = process.stdout.readline(4096)
                    if not line: break
                    if len(line) <= 2048: lines.put(line)
            finally: lines.put(None)
        threading.Thread(target=read, daemon=True).start()
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() >= deadline: raise subprocess.TimeoutExpired(command, timeout)
            try: line = lines.get(timeout=1)
            except queue.Empty: continue
            if line is None: break
            value = progress(line)
            if value is not None: print(json.dumps(value), flush=True)
        return process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill(); process.wait(timeout=10)


def worker(output, config):
    stage = "SDK_IMPORT"
    secret = None
    try:
        secret = json.loads(sys.stdin.read()).get("api_key")
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            import vnstock
            if secret:
                stage = "SDK_LOGIN"
                login = vnstock.login(secret)
                if login is False or isinstance(login, dict) and login.get("authenticated") is False:
                    raise ValueError("SDK_LOGIN_NOT_AUTHENTICATED")
            from vnstock import Reference
            reference = Reference()
        stage = "SDK_EVENTS"
        def fetch(ticker):
            with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                return reference.company(ticker).events(source="kbs", lang="vi")
        result = collect(output, config, fetch, secret=secret)
        return 0 if result["status"] == "SDK_EXPORTS_READY_FOR_REVIEW" else 2
    except (Exception, KeyboardInterrupt) as exc:
        if not (output / "result.json").exists():
            write_json(output, "result.json", {"stage": config["stage"], "status": "STOPPED_SETUP_ERROR",
                "setup_stage": stage, **safe_error(exc), "canonical_build": False, "field_approval": False}, secret)
        print(json.dumps({"event": "FINISHED", "status": "STOPPED_SETUP_ERROR"}), flush=True)
        return 2
    finally: secret = None


def main():
    for stream in [sys.stdout, sys.stderr]:
        if hasattr(stream, "reconfigure"): stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Kiểm tra offline; không import/login/call SDK")
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        config_body = CONFIG.read_bytes(); config = json.loads(config_body); config_check(config)
        env = child_environment(os.environ, STATE_HOME)
        runtime = sdk_precheck()
    except Exception as exc:
        reason = "SDK_NOT_INSTALLED" if isinstance(exc, importlib.metadata.PackageNotFoundError) else str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(json.dumps({"status": "LOCAL_PRECHECK_FAILED", "reason": reason})); return 2
    if args.worker_output:
        expected_parent = OUTPUT_ROOT.resolve()
        if not args.worker_output.resolve().is_relative_to(expected_parent): raise ValueError("WORKER_OUTPUT_OUTSIDE_CORPORATE_ACTIONS")
        return worker(args.worker_output, config)
    if args.check:
        print(json.dumps({"status": "LOCAL_CHECK_PASS_AUTH_NOT_TESTED", **runtime, "tickers": [t for t, _ in TARGETS]})); return 0
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            secret = getpass.getpass("VNSTOCK API key (nhap an; Enter = dung dang nhap local da luu): ").strip()
        if secret and (any(c.isspace() for c in secret) or secret[:1] in {"'", '"'}):
            print("KEY_INPUT_INVALID_NO_LOGIN"); return 2
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        print("KEY_INPUT_CANCELLED_NO_LOGIN"); return 2
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = OUTPUT_ROOT / ("run-" + stamp) / "state"
    output.mkdir(parents=True, exist_ok=False)
    STATE_HOME.mkdir(parents=True, exist_ok=True)
    write_json(output, "plan.json", config, secret)
    write_json(output, "runtime.json", {**runtime, "script_sha256": sha(Path(__file__).read_bytes()),
        "collector_sha256": sha((ROOT / "src/delta_t1/ingestion/corporate_actions/kbs_pilot.py").read_bytes()),
        "config_sha256": sha(config_body), "sdk_auth_mode": "EXPLICIT_KEY_LOGIN" if secret else "REUSE_LOCAL_SDK_STATE",
        "python_version": sys.version.split()[0]}, secret)
    archive = OUTPUT_ROOT / ("delta-kbs-pilot-" + stamp + ".zip")
    execution = {"status": "STOPPED_LOCAL_WRAPPER_ERROR", "child_returncode": None, "timeout_seconds": config["parent_timeout_seconds"]}
    try:
        code = execute_child([sys.executable, str(Path(__file__).resolve()), "--worker-output", str(output)],
            secret, env, config["parent_timeout_seconds"])
        execution["child_returncode"] = code
        if (output / "result.json").exists(): execution["status"] = json.loads((output / "result.json").read_text(encoding="utf-8"))["status"]
    except subprocess.TimeoutExpired: execution["status"] = "STOPPED_LOCAL_TIMEOUT"
    except KeyboardInterrupt: execution["status"] = "CANCELLED_BY_USER"
    except Exception: execution["status"] = "STOPPED_LOCAL_WRAPPER_ERROR"
    finally:
        secret = None
        seal_and_zip(output, archive, execution)
        print("STATUS:", execution["status"])
        print("OUTPUT_ZIP:", str(archive))
    return 0 if execution["status"] == "SDK_EXPORTS_READY_FOR_REVIEW" else 2


if __name__ == "__main__": raise SystemExit(main())
