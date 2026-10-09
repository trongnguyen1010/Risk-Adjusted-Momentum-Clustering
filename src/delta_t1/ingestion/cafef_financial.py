"""Bounded raw-only financial coverage pilot. No canonical timing or ratios."""
import hashlib
import json
import math
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .sources.base import AccessControlError, PublicJsonClient, RateLimitError, SemanticValidationError

ENDPOINT = "https://apiweb.cafef.vn/api/v1/BCTC/GetReportSummary"
VERSION = "cafef-financial-raw-pilot-v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def immutable_write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(body)


def validate_config(config):
    if config.get("contract_version") != VERSION:
        raise ValueError("unsupported financial pilot contract")
    for field, allowed, limit in (("symbols", None, 10),
                                  ("report_types", {"KQKD", "CDKT", "LCTT"}, 3),
                                  ("time_modes", {"QUY", "NAM"}, 2)):
        values = config.get(field)
        if (not isinstance(values, list) or not 1 <= len(values) <= limit
                or any(not isinstance(v, str) for v in values) or len(set(values)) != len(values)):
            raise ValueError("invalid " + field)
        if allowed and not set(values) <= allowed:
            raise ValueError("unsupported " + field)
    if any(not re.fullmatch(r"[A-Z0-9]{1,10}", s) for s in config["symbols"]):
        raise ValueError("invalid pilot symbol")
    for field, low, high in (("start_year", 1900, 2100), ("end_year", 1900, 2100),
                             ("max_pages_per_stream", 1, 20), ("max_logical_requests", 1, 200)):
        v = config.get(field)
        if type(v) is not int or not low <= v <= high:
            raise ValueError("invalid " + field)
    if not 0 <= config["end_year"] - config["start_year"] <= 9 or config.get("page_size") != 4:
        raise ValueError("pilot requires <=10 years and UI-sized pages")
    if config.get("pit_status") != "PIT_UNRESOLVED" or config.get("financial_features_allowed") is not False:
        raise ValueError("financial pilot must remain raw-only")
    return config


def parse_page(payload, symbol, report_type, time_mode):
    """Return provider periods untouched; missing group is distinct from empty."""
    if (not isinstance(payload, dict) or payload.get("isSuccess") is not True
            or not isinstance(payload.get("value"), dict) or payload.get("errors")):
        raise SemanticValidationError("invalid financial response envelope")
    value = payload["value"]
    if not isinstance(value.get("data"), list) or not isinstance(value.get("templace"), list):
        raise SemanticValidationError("invalid financial data/template")
    groups = value["data"]
    if any(not isinstance(g, dict) or not isinstance(g.get("code"), str) for g in groups):
        raise SemanticValidationError("invalid statement group")
    selected = [g for g in groups if g["code"] == report_type]
    if len(selected) > 1:
        raise SemanticValidationError("duplicate statement group")
    if not selected:
        return [], "REPORT_TYPE_NOT_RETURNED"
    rows = selected[0].get("data")
    if not isinstance(rows, list) or len(rows) > 4:
        raise SemanticValidationError("unexpected financial page size")
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or row.get("symbol") != symbol
                or type(row.get("year")) is not int or not 1900 <= row["year"] <= 2100
                or type(row.get("quater")) is not int
                or row["quater"] not in ((0,) if time_mode == "NAM" else (1, 2, 3, 4))
                or not isinstance(row.get("time"), str) or not isinstance(row.get("data"), list)):
            raise SemanticValidationError("invalid period/symbol identity")
        key = (row["year"], row["quater"])
        if key in seen:
            raise SemanticValidationError("duplicate period on page")
        seen.add(key)
        codes = set()
        for fact in row["data"]:
            if not isinstance(fact, dict) or not isinstance(fact.get("code"), str) or "value" not in fact:
                raise SemanticValidationError("invalid raw financial fact")
            v = fact["value"]
            if v is not None and (type(v) not in (int, float) or not math.isfinite(v)):
                raise SemanticValidationError("non-numeric financial fact")
            if fact["code"] in codes:
                raise SemanticValidationError("duplicate fact code")
            codes.add(fact["code"])
    keys = [(r["year"], r["quater"]) for r in rows]
    if keys != sorted(keys, reverse=True):
        raise SemanticValidationError("period order is not descending")
    return rows, "ROWS" if rows else "EMPTY_PROVIDER_PAGE"


def coverage(config, symbol, report_type, time_mode, observations, stop_reason):
    quarters = (0,) if time_mode == "NAM" else (1, 2, 3, 4)
    expected = {(y, q) for y in range(config["start_year"], config["end_year"] + 1) for q in quarters}
    by_period = {(r["year"], r["quater"]): r for r in observations}
    observed = set(by_period) & expected
    def label(key):
        return str(key[0]) if key[1] == 0 else f"Q{key[1]}-{key[0]}"
    selected = [by_period[k] for k in sorted(observed)]
    return {
        "symbol": symbol, "report_type": report_type, "time_mode": time_mode,
        "stop_reason": stop_reason, "expected_periods": len(expected),
        "observed_periods": len(observed), "missing_periods": [label(k) for k in sorted(expected - observed)],
        "oldest_observed_label": label(min(by_period)) if by_period else None,
        "newest_observed_label": label(max(by_period)) if by_period else None,
        "raw_fact_count": sum(len(r["data"]) for r in selected),
        "null_fact_count": sum(f["value"] is None for r in selected for f in r["data"]),
        "empty_fact_periods": [r["time"] for r in selected if not r["data"]],
        "provider_type_values": sorted({str(r.get("type")) for r in selected}),
        "provider_content_values": sorted({str(r.get("content")) for r in selected}),
        "fact_codes": sorted({f["code"] for r in selected for f in r["data"]}),
        "coverage_complete": observed == expected and all(r["data"] for r in selected),
        "published_at": None, "available_at": None, "pit_status": "PIT_UNRESOLVED",
        "duration_semantics": "UNVERIFIED", "scope_semantics": "UNVERIFIED",
        "revision_semantics": "INTERNAL_OBSERVATION_ONLY", "financial_features_allowed": False,
    }


def collect(config, output_root, client=None):
    validate_config(config)
    client = client or PublicJsonClient(timeout=20, attempts=2, min_interval=2)
    run = Path(output_root) / ("run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    immutable_write(run / "config.json", encoded(config))
    immutable_write(run / "collector.py", Path(__file__).read_bytes())
    immutable_write(run / "transport.py", Path(__file__).with_name("sources").joinpath("base.py").read_bytes())
    streams, requests, hard_stop = [], 0, False
    started = now()
    for symbol in config["symbols"]:
        for mode in config["time_modes"]:
            for typ in config["report_types"]:
                rows, seen, reason = [], set(), "PAGE_CAP_REACHED"
                for page in range(1, config["max_pages_per_stream"] + 1):
                    if hard_stop or requests >= config["max_logical_requests"]:
                        reason = "NOT_REQUESTED_HARD_STOP" if hard_stop else "REQUEST_CAP_REACHED"
                        break
                    params = {"symbol": symbol, "pageIndex": page, "pageSize": 4,
                              "reportType": typ, "TypeTime": mode}
                    requests += 1
                    prefix = run / "raw" / symbol / mode / typ / f"page-{page:03d}"
                    try:
                        response = client.get_json(ENDPOINT, params)
                        immutable_write(prefix.with_suffix(".json"), response["body"])
                        meta = {"params": params, "endpoint": ENDPOINT, "url": response["url"],
                                "http_status": response["status"], "fetched_at": now(),
                                "sha256": digest(response["body"]), "adapter_version": VERSION,
                                "pit_status": "PIT_UNRESOLVED", "published_at": None,
                                "available_at": None, "financial_features_allowed": False,
                                "rights_status": "RIGHTS_NOT_VERIFIED", "execution_policy": "ACCEPTED_RESEARCH_RISK"}
                        immutable_write(prefix.with_suffix(".metadata.json"), encoded(meta))
                        batch, page_status = parse_page(response["payload"], symbol, typ, mode)
                        if page_status != "ROWS":
                            reason = page_status
                            break
                        keys = {(r["year"], r["quater"]) for r in batch}
                        if seen & keys or (seen and max(keys) >= min(seen)):
                            raise SemanticValidationError("pagination repeated/overlapped/reordered periods")
                        seen.update(keys)
                        rows.extend(batch)
                        if min(y for y, _ in keys) <= config["start_year"] and (
                                mode == "NAM" or min(keys) <= (config["start_year"], 1)):
                            reason = "TARGET_START_REACHED"
                            break
                    except (AccessControlError, RateLimitError) as exc:
                        reason, hard_stop = "HARD_STOP", True
                        immutable_write(prefix.with_suffix(".error.json"), encoded({"error": str(exc), "params": params, "at": now()}))
                        break
                    except (ValueError, OSError) as exc:
                        reason = "FAILED"
                        immutable_write(prefix.with_suffix(".error.json"), encoded({"error": str(exc), "params": params, "at": now()}))
                        break
                streams.append(coverage(config, symbol, typ, mode, rows, reason))
    result = {"stage": "FINANCIAL_RAW_COVERAGE_PILOT", "adapter_version": VERSION,
              "started_at": started, "finished_at": now(), "logical_requests": requests,
              "request_count_semantics": "includes_failed_calls; transport may attempt twice",
              "execution_status": "HARD_STOP" if hard_stop else ("PARTIAL" if any(s["stop_reason"] in {
                  "FAILED", "REQUEST_CAP_REACHED", "PAGE_CAP_REACHED"} for s in streams) else "COMPLETE"),
              "coverage_status": "PASS" if all(s["coverage_complete"] for s in streams) else "PARTIAL",
              "financial_pit_gate": "NOT_READY", "financial_features_allowed": False, "streams": streams}
    immutable_write(run / "coverage.json", encoded(result))
    files = {p.relative_to(run).as_posix(): digest(p.read_bytes()) for p in sorted(run.rglob("*")) if p.is_file()}
    immutable_write(run / "manifest.json", encoded({"version": VERSION, "files": files}))
    return run, result


def verify(run):
    """Exact file inventory/hash verification plus offline coverage replay."""
    run = Path(run).resolve()
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    actual = {p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file() and p != run / "manifest.json"}
    if manifest.get("version") != VERSION or actual != set(manifest["files"]):
        raise ValueError("manifest inventory/version mismatch")
    for name, expected in manifest["files"].items():
        path = (run / name).resolve()
        if not path.is_relative_to(run) or digest(path.read_bytes()) != expected:
            raise ValueError("manifest path/hash mismatch: " + name)
    config = validate_config(json.loads((run / "config.json").read_text(encoding="utf-8")))
    result = json.loads((run / "coverage.json").read_text(encoding="utf-8"))
    expected_streams = {(s, t, m) for s in config["symbols"] for t in config["report_types"] for m in config["time_modes"]}
    found = [(s["symbol"], s["report_type"], s["time_mode"]) for s in result["streams"]]
    if set(found) != expected_streams or len(found) != len(expected_streams):
        raise ValueError("coverage stream inventory mismatch")
    for stream in result["streams"]:
        symbol, typ, mode = stream["symbol"], stream["report_type"], stream["time_mode"]
        rows, seen = [], set()
        directory = run / "raw" / symbol / mode / typ
        for path in sorted(directory.glob("page-*.metadata.json")):
            meta = json.loads(path.read_text(encoding="utf-8"))
            body = path.with_name(path.name.replace(".metadata.json", ".json")).read_bytes()
            if digest(body) != meta["sha256"] or meta["available_at"] is not None or meta["financial_features_allowed"] is not False:
                raise ValueError("raw metadata mismatch")
            try:
                batch, _ = parse_page(json.loads(body), symbol, typ, mode)
                keys = {(r["year"], r["quater"]) for r in batch}
                if seen & keys or (seen and keys and max(keys) >= min(seen)):
                    raise SemanticValidationError("pagination overlap")
                seen.update(keys)
                rows.extend(batch)
            except SemanticValidationError:
                if stream["stop_reason"] != "FAILED":
                    raise
        if coverage(config, symbol, typ, mode, rows, stream["stop_reason"]) != stream:
            raise ValueError("coverage replay mismatch")
    if result["financial_pit_gate"] != "NOT_READY" or result["financial_features_allowed"] is not False:
        raise ValueError("financial pilot unexpectedly promoted")
    return result
