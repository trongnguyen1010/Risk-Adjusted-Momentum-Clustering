"""Chẩn đoán bounded public KBS response cho DXG, không normalize/canonical."""
import hashlib
import json
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPSHandler, Request, build_opener
import zipfile

from delta_t1.ingestion.sources.base import NoRedirect
from .kbs_pilot import utc_now, write_json

ENDPOINT = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/event/DXG"
EVIDENCE_HASHES = {
    "company.py": "0d1bc951e79c9d2c85c28c8ceeb62dea59bd504947b48eabd819c67a10bd8256",
    "const.py": "c3eaaeedb0c69e1c20cd4e65e558bc91352ee486414c24f335c59d5eac92e24b",
}


def digest(body):
    return hashlib.sha256(body).hexdigest()


def seal_raw(output, archive, execution):
    write_json(output, "execution.json", execution)
    files = {p.relative_to(output).as_posix(): digest(p.read_bytes()) for p in output.rglob("*") if p.is_file()}
    write_json(output, "manifest.json", {"artifact_type": "kbs-public-raw-diagnostic-v1", "files": files,
        "classification": "PUBLIC_HTTP_BYTES_NOT_CANONICAL_EVENTS", "canonical_build": False})
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output.rglob("*")):
            if p.is_file(): z.write(p, p.relative_to(output).as_posix())


def validate_config(config):
    if config["ticker"] != "DXG" or config["endpoint"] != ENDPOINT:
        raise ValueError("EXACT_DXG_ENDPOINT_REQUIRED")
    if (config["max_requests"], config["page_size"], config["max_pages"]) != (2, 10, 2):
        raise ValueError("EXACT_DIAGNOSTIC_LIMITS_REQUIRED")
    if not 8 <= config["interval_seconds"] <= 60 or not 1 <= config["timeout_seconds"] <= 20:
        raise ValueError("BOUNDED_TIMING_REQUIRED")
    if config["max_response_bytes"] != 1000000 or config["event_type_filter"] is not None:
        raise ValueError("BOUNDED_UNFILTERED_DIAGNOSTIC_REQUIRED")
    if not config["tls_verification"] or any(config[k] for k in ("retries", "follow_redirects", "provider_fallback", "canonical_build")):
        raise ValueError("FAIL_CLOSED_DIAGNOSTIC_REQUIRED")


def verify_inputs(root, config):
    validate_config(config)
    evidence = root / config["endpoint_evidence"]
    for name, expected in EVIDENCE_HASHES.items():
        if digest((evidence / name).read_bytes()) != expected:
            raise ValueError("ENDPOINT_EVIDENCE_HASH_MISMATCH")
    archive = root / config["baseline_zip"]
    if digest(archive.read_bytes()) != config["baseline_zip_sha256"]:
        raise ValueError("BASELINE_ZIP_HASH_MISMATCH")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("BASELINE_ZIP_CRC_FAILED")
        manifest = json.loads(z.read("manifest.json"))
        for name, expected in manifest["files"].items():
            if digest(z.read(name)) != expected:
                raise ValueError("BASELINE_MANIFEST_HASH_MISMATCH")
        export = json.loads(z.read("sdk_exports/DXG.json"))
        if export["source"] != "kbs" or export["route"] != "fundamental.company.events" or export["query_ticker"] != "DXG":
            raise ValueError("BASELINE_SOURCE_ROUTE_MISMATCH")
    return {"baseline_sdk_rows": len(export["data"]), "baseline_zip_sha256": config["baseline_zip_sha256"],
        "endpoint_evidence_hashes": EVIDENCE_HASHES, "baseline_manifest_files_verified": len(manifest["files"])}


def get_public(url, config):
    # No cookie jar, login/token, browser impersonation, redirects or retries.
    opener = build_opener(NoRedirect(), HTTPSHandler(context=ssl.create_default_context()))
    request = Request(url, headers={"User-Agent": "DeltaT1Research/0.2 (public endpoint diagnostic)",
        "Accept": "application/json", "Accept-Encoding": "identity"})
    try:
        response = opener.open(request, timeout=config["timeout_seconds"])
    except HTTPError as exc:
        response = exc  # Preserve even denied/redirect/error response bodies.
    with response:
        body = response.read(config["max_response_bytes"] + 1)
        return {"http_status": response.code, "body": body[:config["max_response_bytes"]],
            "truncated": len(body) > config["max_response_bytes"],
            "headers": {key.lower(): response.headers[key] for key in
                ("Content-Type", "Content-Encoding", "Content-Length", "Retry-After", "Date") if key in response.headers}}


def inspect_response(response):
    body, status = response["body"], response["http_status"]
    if status in (401, 403, 406, 407, 429):
        return {"status": "STOPPED_ACCESS_OR_RATE_LIMIT", "rows": None}
    if 300 <= status < 400:
        return {"status": "STOPPED_REDIRECT", "rows": None}
    if status != 200:
        return {"status": "STOPPED_HTTP_ERROR", "rows": None}
    if response["truncated"]:
        return {"status": "STOPPED_RESPONSE_LIMIT", "rows": None}
    marker = body[:8192].lower()
    if any(term in marker for term in (b"captcha", b"cloudflare", b"managed challenge", b"login wall")):
        return {"status": "STOPPED_ACCESS_OR_RATE_LIMIT", "rows": None}
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return {"status": "STOPPED_NON_JSON_OR_INVALID_JSON", "rows": None}
    # The public SDK source expects a top-level array or single dict. Do not
    # miscount a provider error envelope/single metadata object as one event.
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        return {"status": "STOPPED_UNVERIFIED_JSON_SHAPE", "rows": None,
            "json_type": type(payload).__name__}
    # Raw values remain in the .bin; no date/ratio/unit interpretation here.
    return {"status": "PUBLIC_JSON_ARRAY_RECEIVED", "rows": len(payload),
        "columns": sorted({str(k) for row in payload for k in row}), "json_type": "list"}


def probe(output, config, inputs, *, fetch=get_public, sleep=time.sleep, emit=print):
    validate_config(config)
    receipts = []
    final_status = "RAW_DIAGNOSTIC_READY_FOR_REVIEW"
    for page in range(1, config["max_pages"] + 1):
        if page > 1:
            sleep(config["interval_seconds"])
        params = {"l": 1, "p": page, "s": config["page_size"]}
        url = ENDPOINT + "?" + urlencode(params)
        receipt = {"page": page, "url": url, "params": params, "requested_at": utc_now()}
        receipts.append(receipt)
        emit(json.dumps({"event": "RAW_QUERY_STARTED", "ticker": "DXG", "page": page}), flush=True)
        try:
            response = fetch(url, config)
        except (OSError, URLError, TimeoutError) as exc:
            reason = getattr(exc, "reason", exc)
            receipt.update(status="STOPPED_TLS_OR_TRANSPORT", error_type=type(exc).__name__,
                tls_error=isinstance(reason, ssl.SSLError), response_received=False)
            final_status = receipt["status"]
            write_json(output, f"receipts/page-{page}.json", receipt)
            break
        body = response["body"]
        raw = f"raw/page-{page}.bin"
        (output / "raw").mkdir(exist_ok=True)
        with (output / raw).open("xb") as stream:
            stream.write(body)
        assessment = inspect_response(response)
        receipt.update(response_received=True, http_status=response["http_status"], headers=response["headers"],
            truncated=response["truncated"], raw_file=raw, raw_sha256=digest(body), raw_bytes=len(body), **assessment)
        write_json(output, f"receipts/page-{page}.json", receipt)
        emit(json.dumps({"event": "RAW_QUERY_SAVED", "page": page, "http_status": response["http_status"],
            "rows": assessment["rows"], "status": assessment["status"]}), flush=True)
        if assessment["status"] != "PUBLIC_JSON_ARRAY_RECEIVED":
            final_status = assessment["status"]
            break
        if assessment["rows"] < config["page_size"]:
            break
        if page == 2 and receipt["raw_sha256"] == receipts[0].get("raw_sha256"):
            final_status = "PAGINATION_REPEATED_BODY_REVIEW_REQUIRED"
    raw_rows = [r["rows"] for r in receipts if r.get("status") == "PUBLIC_JSON_ARRAY_RECEIVED"]
    result = {"stage": config["stage"], "status": final_status, "ticker": "DXG", "requests_attempted": len(receipts),
        "receipts": receipts, **inputs, "raw_rows_by_page": raw_rows,
        "rows_are_deduplicated_events": False, "full_history_coverage": "NOT_PROVEN",
        "comparison": "PUBLIC_ENDPOINT_VS_PRIOR_SDK_EXPORT_NOT_CONTROLLED_SAME_REQUEST",
        "installed_native_sdk_endpoint_equivalence": "UNVERIFIED",
        "empty_response_proves_no_historical_events": False, "canonical_build": False,
        "field_approval": False, "source_priority_changed": False}
    write_json(output, "result.json", result)
    return result
