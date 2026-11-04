"""Thu thập SDK exports VCI theo tháng; checkpoint bất biến, chưa canonical."""
import argparse
import base64
import calendar
import contextlib
import hashlib
import importlib.metadata
import io
import json
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
import sys
import time
from urllib.parse import quote, quote_plus
import zipfile

if __package__:
    from .vci_calendar_pilot import SDK_VERSION, safe_error
else:
    from vci_calendar_pilot import SDK_VERSION, safe_error

CONTRACT = "VCI_CALENDAR_MONTHLY_V1"
SCOPE_SHA = "283edfdb042e864f5565be11a93315af58b0c7538f3d614652494c9ed3b14a14"
SCOPE_INVENTORY_SHA = "49262e96578ed6715696d5ae4a625aa86ed7f546f1e6f3db8f7b10c7adff4316"
PILOT_SHA = "258e2e38e8dd3033c1dc54251d5bdefc142077d5f32472152b377cb76f328efd"
REQUIRED_COLUMNS = {"symbol", "event_name", "event_title", "ex_right_date",
                    "record_date", "payout_date", "value", "ratio", "public_date", "event_type"}
RESUME_STATUSES = {"STOPPED_TIME_BUDGET", "COLLECTION_EXPORTS_READY_FOR_REVIEW"}


def digest(body):
    return hashlib.sha256(body).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def has_secret(body, key):
    if not key:
        return False
    variants = {key, quote(key, safe=""), quote_plus(key),
                base64.b64encode(key.encode()).decode()}
    return any(v.encode() in body for v in variants)


def write_json(path, value, key=None):
    body = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    if has_secret(body, key):
        raise ValueError("SECRET_EXPORT_REFUSED")
    with Path(path).open("xb") as stream:
        stream.write(body)


def months(start, end):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    if start > end:
        raise ValueError("INVALID_DATE_WINDOW")
    cursor = start
    result = []
    while cursor <= end:
        last = date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1])
        result.append({"id": cursor.strftime("%Y-%m"), "start": cursor.isoformat(),
                       "end": min(last, end).isoformat()})
        cursor = date.fromordinal(last.toordinal() + 1)
    return result


def validate_inputs(plan, scope, gate):
    fixed = {"contract": CONTRACT, "start": "2019-01-31", "end": "2025-12-31",
             "event_type": "dividend", "row_cap": 20000, "interval_seconds": 8,
             "session_seconds": 1800, "parent_timeout_seconds": 3600,
             "sdk_version": SDK_VERSION, "scope_count": 1522,
             "scope_inventory_sha256": SCOPE_INVENTORY_SHA,
             "scope_canonical_sha256": SCOPE_SHA, "pilot_zip_sha256": PILOT_SHA,
             "source": "vci", "route": "reference.events.calendar",
             "source_bytes_basis": "SDK_EXPORT_BYTES_NOT_ORIGINAL_HTTP_RESPONSE",
             "date_policy": "PRESERVE_SDK_STRINGS_NO_CANONICAL_CONVERSION",
             "automatic_retry": False, "canonical_build": False,
             "pit_status": "NOT_PROMOTED", "historical_identity": "NOT_CERTIFIED"}
    if plan != fixed:
        raise ValueError("PLAN_REQUIRES_REVIEW")
    if (scope.get("canonical_sha256") != SCOPE_SHA
            or len(scope.get("securities", [])) != 1522
            or len({r["ticker"] for r in scope["securities"]}) != 1522
            or digest(json.dumps(scope["securities"], ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")).encode()) != SCOPE_INVENTORY_SHA):
        raise ValueError("C8_V2_SCOPE_MISMATCH")
    if (gate.get("access_and_export_gate") != "PASS"
            or gate.get("input_sha256") != PILOT_SHA
            or not gate.get("zip_crc_pass")
            or not all(gate.get("manifest_hashes", {}).values())
            or len(gate.get("manifest_hashes", {})) != 7):
        raise ValueError("SUCCESSFUL_PILOT_REQUIRED")


def seal(output):
    output = Path(output)
    files = {p.relative_to(output).as_posix(): digest(p.read_bytes())
             for p in sorted(output.rglob("*")) if p.is_file() and p != output / "manifest.json"}
    write_json(output / "manifest.json", {"artifact_type": CONTRACT, "files": files})


def verify_state(archive):
    """Verify every member before restoring; never extract arbitrary paths."""
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if (len(names) != len(set(names)) or len(names) > 2000
                or sum(i.file_size for i in infos) > 512 * 1024 * 1024):
            raise ValueError("STATE_ARCHIVE_LIMIT_OR_DUPLICATE")
        for info in infos:
            rel = PurePosixPath(info.filename)
            if (info.is_dir() or rel.is_absolute() or ".." in rel.parts
                    or "\\" in info.filename or ":" in info.filename
                    or rel.as_posix() != info.filename
                    or ((info.external_attr >> 16) & 0o170000) == 0o120000):
                raise ValueError("UNSAFE_STATE_PATH")
        if z.testzip() is not None:
            raise ValueError("STATE_CRC_FAILED")
        manifest = json.loads(z.read("manifest.json"))
        if manifest.get("artifact_type") != CONTRACT:
            raise ValueError("STATE_CONTRACT_MISMATCH")
        if set(names) != set(manifest["files"]) | {"manifest.json"}:
            raise ValueError("STATE_INVENTORY_MISMATCH")
        data = {name: z.read(name) for name in names}
        if not all(digest(data[n]) == h for n, h in manifest["files"].items()):
            raise ValueError("STATE_HASH_MISMATCH")
        return data


def committed(output, windows, *, allow_partial=False):
    result = []
    month_root = Path(output) / "months"
    if month_root.exists() and any(p.name not in {w["id"] for w in windows} or not p.is_dir()
                                   for p in month_root.iterdir()):
        raise ValueError("UNKNOWN_MONTH_ARTIFACT")
    for window in windows:
        folder = Path(output) / "months" / window["id"]
        if not folder.exists():
            continue
        if not (folder / "commit.json").exists():
            if allow_partial:
                continue
            raise ValueError("INCOMPLETE_MONTH_REQUIRES_REVIEW")
        receipt = read_json(folder / "commit.json")
        if receipt["window"] != window:
            raise ValueError("MONTH_WINDOW_MISMATCH")
        expected = {"sdk_export.json", "query.json", "review.json"}
        if set(receipt["files"]) != expected or {p.name for p in folder.iterdir()} != expected | {"commit.json"}:
            raise ValueError("MONTH_INVENTORY_MISMATCH")
        if not all(digest((folder / n).read_bytes()) == h for n, h in receipt["files"].items()):
            raise ValueError("MONTH_HASH_MISMATCH")
        result.append(window["id"])
    return result


def prepare(output, plan, scope, gate, resume=None):
    validate_inputs(plan, scope, gate)
    output = Path(output)
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    prior = None
    if resume:
        prior = verify_state(resume)
        if (json.loads(prior["plan.json"]) != plan or json.loads(prior["scope.json"]) != scope
                or json.loads(prior["pilot_gate.json"]) != gate):
            raise ValueError("STATE_INPUT_MISMATCH")
        if json.loads(prior["result.json"])["status"] not in RESUME_STATUSES:
            raise ValueError("SOURCE_OR_INTEGRITY_STOP_NO_AUTOMATIC_RESUME")
    output.mkdir(parents=True)
    write_json(output / "plan.json", plan)
    write_json(output / "scope.json", scope)
    write_json(output / "pilot_gate.json", gate)
    if prior:
        for name, body in prior.items():
            if name.startswith("months/"):
                target = output / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(body)
        write_json(output / "predecessor.json", {
            "archive_sha256": digest(Path(resume).read_bytes()),
            "manifest_sha256": digest(prior["manifest.json"]),
            "result": json.loads(prior["result.json"])})
    windows = months(plan["start"], plan["end"])
    done = committed(output, windows)
    if prior and done != json.loads(prior["result.json"])["completed_windows"]:
        raise ValueError("CHECKPOINT_COMPLETION_MISMATCH")
    return windows, done


def review_rows(rows, scope):
    tickers = {r["ticker"] for r in scope["securities"]}
    issues, seen = [], {}
    inside = 0
    for index, row in enumerate(rows):
        in_scope = row["symbol"] in tickers
        inside += in_scope
        reasons = []
        missing = [f for f in ("ex_right_date", "record_date") if row.get(f) in (None, "")]
        if missing:
            reasons.append("MISSING_DATES_APPLICABILITY_NOT_ASSESSED")
        if row.get("event_type") == "DIV":
            missing += [f for f in ("value", "payout_date") if row.get(f) in (None, "")]
            if any(f in missing for f in ("value", "payout_date")):
                reasons.append("CASH_FIELDS_MISSING")
        row_hash = digest(json.dumps(row, sort_keys=True, ensure_ascii=False).encode())
        duplicate_of = seen.get(row_hash)
        if duplicate_of is not None:
            reasons.append("EXACT_PAYLOAD_DUPLICATE_RETAINED")
        else:
            seen[row_hash] = index
        if not in_scope:
            reasons.append("OUTSIDE_C8_V2_TICKER_INVENTORY_RETAINED")
        if reasons:
            issues.append({"row_index": index, "reasons": reasons,
                           "missing_fields": missing, "duplicate_of_row_index": duplicate_of})
    return {"rows": len(rows), "in_c8_ticker_inventory_rows": inside,
            "outside_c8_ticker_inventory_rows": len(rows) - inside,
            "exact_duplicate_excess_rows": len(rows) - len(seen),
            "field_or_scope_review": issues,
            "all_rows_pit_status": "NOT_PROMOTED",
            "all_rows_historical_identity": "NOT_CERTIFIED",
            "date_precision": "SDK_STRINGS_PRESERVED_ACTUAL_PUBLICATION_TIME_UNVERIFIED",
            "no_events_claim_for_absent_tickers": False}


def report(output, plan, windows, status, calls, diagnostic=None):
    # Only commit receipts count as completed. Partial exports remain evidence.
    done = committed(output, windows, allow_partial=status not in RESUME_STATUSES)
    seen, cross_duplicates, review_count = {}, [], 0
    for month in done:
        folder = Path(output) / "months" / month
        review_count += len(read_json(folder / "review.json")["field_or_scope_review"])
        for index, row in enumerate(read_json(folder / "sdk_export.json")):
            row_hash = digest(json.dumps(row, sort_keys=True, ensure_ascii=False).encode())
            if row_hash in seen and seen[row_hash]["month"] != month:
                cross_duplicates.append({"month": month, "row_index": index,
                                         "same_payload_as": seen[row_hash]})
            else:
                seen.setdefault(row_hash, {"month": month, "row_index": index})
    write_json(Path(output) / "cross_window_review.json", {
        "exact_payload_matches_across_windows": cross_duplicates,
        "all_rows_retained": True, "canonical_event_deduplication": "NOT_PERFORMED"})
    value = {"stage": CONTRACT, "status": status, "completed_windows": done,
             "completed_window_count": len(done), "total_windows": len(windows),
             "pending_windows": [w["id"] for w in windows if w["id"] not in done],
             "logical_calendar_calls_this_run": calls,
             "underlying_http_count": "NOT_INSTRUMENTED",
             "resumable": status == "STOPPED_TIME_BUDGET",
             "automatic_retry": False, "hnx_requests": 0,
             "source_bytes_basis": plan["source_bytes_basis"],
             "canonical_build": False, "pit_status": "NOT_PROMOTED",
             "historical_identity": "NOT_CERTIFIED", "history_completeness": "NOT_CERTIFIED",
             "field_or_scope_review_rows_cumulative": review_count,
             "exact_payload_matches_across_windows": len(cross_duplicates),
             "sdk_export_rows_cumulative": sum(read_json(Path(output) / "months" / n / "query.json")["rows"] for n in done)}
    if diagnostic:
        value["diagnostic"] = diagnostic
    write_json(Path(output) / "result.json", value)
    seal(output)
    return value


def collect(output, fetch, plan, scope, windows, done, *, key=None,
            sleep=time.sleep, clock=time.monotonic, session_seconds=None, emit=None):
    output = Path(output)
    budget = plan["session_seconds"] if session_seconds is None else session_seconds
    started, calls = clock(), 0
    status, diagnostic = "COLLECTION_EXPORTS_READY_FOR_REVIEW", None
    for window in windows:
        if window["id"] in done:
            continue
        if clock() - started + plan["interval_seconds"] >= budget:
            status = "STOPPED_TIME_BUDGET"
            break
        sleep(plan["interval_seconds"])
        if clock() - started >= budget:
            status = "STOPPED_TIME_BUDGET"
            break
        calls += 1
        write_json(output / f"attempt_{calls:03d}.json", {"window": window, "attempted_at": datetime.now(timezone.utc).isoformat()})
        if emit:
            emit({"event": "QUERY_STARTED", "month": window["id"], "completed": len(done), "total": len(windows)})
        try:
            # SDK stdout/stderr never enters the state ZIP or notebook log.
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                frame = fetch(start=window["start"], end=window["end"], event_type=plan["event_type"], limit=plan["row_cap"])
                body = frame.to_json(orient="records", date_format="iso", force_ascii=False).encode()
            if has_secret(body, key):
                raise ValueError("SECRET_EXPORT_REFUSED")
            rows = json.loads(body)
            folder = output / "months" / window["id"]
            folder.mkdir(parents=True, exist_ok=False)
            with (folder / "sdk_export.json").open("xb") as stream:
                stream.write(body)
            attrs = getattr(frame, "attrs", {})
            if attrs.get("source") != plan["source"] or attrs.get("route") != plan["route"]:
                status = "STOPPED_SOURCE_OR_ROUTE_MISMATCH"
                break
            if (not isinstance(rows, list) or not REQUIRED_COLUMNS <= set(frame.columns)
                    or any(not isinstance(r, dict) or not REQUIRED_COLUMNS <= set(r)
                           or not isinstance(r.get("symbol"), str) or not r["symbol"] for r in rows)):
                status = "STOPPED_SCHEMA_REVIEW_REQUIRED"
                break
            if len(rows) >= plan["row_cap"]:
                status = "STOPPED_POSSIBLE_ROW_TRUNCATION"
                break
            write_json(folder / "query.json", {**window, "event_type": plan["event_type"],
                       "limit": plan["row_cap"], "rows": len(rows), "source": plan["source"],
                       "route": plan["route"], "fetched_at": datetime.now(timezone.utc).isoformat(),
                       "export_sha256": digest(body)}, key)
            write_json(folder / "review.json", review_rows(rows, scope), key)
            write_json(folder / "commit.json", {"window": window, "files": {
                n: digest((folder / n).read_bytes()) for n in ("sdk_export.json", "query.json", "review.json")}})
            done.append(window["id"])
            if emit:
                emit({"event": "QUERY_SAVED", "month": window["id"], "rows": len(rows),
                      "completed": len(done), "total": len(windows)})
        except Exception as exc:
            status = "STOPPED_SDK_OR_EXPORT_ERROR_NO_RETRY"
            diagnostic = safe_error(exc, "CALENDAR_FETCH_OR_EXPORT", key)
            break
    # A failed month is retained but not committed; report must still be exportable.
    return report(output, plan, windows, status, calls, diagnostic)


def archive_state(output, target):
    # Export only an explicitly sealed collector tree, never HOME or SDK caches.
    output, target = Path(output), Path(target)
    manifest = read_json(output / "manifest.json")
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for name, expected in manifest["files"].items():
            path = output / name
            if digest(path.read_bytes()) != expected:
                raise ValueError("STATE_CHANGED_BEFORE_EXPORT")
            z.write(path, name)
        z.write(output / "manifest.json", "manifest.json")
    verify_state(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    key = sys.stdin.read().strip()
    stage, windows = "INPUTS", []
    try:
        plan, scope, gate = [read_json(args.inputs / name) for name in ("plan.json", "scope.json", "pilot_gate.json")]
        windows, done = prepare(args.output, plan, scope, gate, args.resume)
        if len(done) == len(windows):
            result = report(args.output, plan, windows, "COLLECTION_EXPORTS_READY_FOR_REVIEW", 0)
        else:
            if not key:
                raise ValueError("MISSING_API_KEY")
            stage = "SDK_VERSION"
            if importlib.metadata.version("vnstock") != SDK_VERSION:
                raise ValueError("SDK_VERSION_MISMATCH")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                stage = "SDK_IMPORT"
                import vnstock
                stage = "SDK_LOGIN"
                if vnstock.login(key) is False:
                    raise ValueError("SDK_LOGIN_RETURNED_FALSE")
                stage = "SDK_STATUS"
                status = vnstock.status()
                if not isinstance(status, dict) or status.get("tier") in (None, "guest"):
                    raise ValueError("AUTHENTICATED_ACCOUNT_REQUIRED")
                stage = "REFERENCE_INIT"
                fetch = vnstock.Reference().events.calendar
            stage = "COLLECTION"
            result = collect(args.output, fetch, plan, scope, windows, done, key=key,
                             emit=lambda x: print(json.dumps(x), flush=True))
        print(json.dumps({"event": "FINISHED", "status": result["status"],
                          "completed": result["completed_window_count"], "total": result["total_windows"]}), flush=True)
        return 0 if result["status"] == "COLLECTION_EXPORTS_READY_FOR_REVIEW" else 2
    except Exception as exc:
        # Never overwrite a sealed result or expose SDK messages on stdout.
        if windows and args.output.exists() and not (args.output / "result.json").exists():
            report(args.output, plan, windows, "STOPPED_SETUP_OR_INTEGRITY_ERROR",
                   None if stage == "COLLECTION" else 0, safe_error(exc, stage, key))
        print(json.dumps({"event": "FINISHED", "status": "STOPPED_SETUP_OR_INTEGRITY_ERROR"}), flush=True)
        return 2
    finally:
        key = None


if __name__ == "__main__":
    raise SystemExit(main())
