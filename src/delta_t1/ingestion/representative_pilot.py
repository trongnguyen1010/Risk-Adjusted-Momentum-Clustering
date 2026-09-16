"""Fail-closed planning and execution support for the market representative pilot."""
from datetime import date, datetime, timezone
import json
from pathlib import Path

from ..artifact_ids import new_artifact_id
from ..contracts import validate_rows
from ..io import atomic_write, digest, encoded, read_json, write_json
from .crawler import code_hash
from .planning import M1_SCALE, REPRESENTATIVE_PILOT, SOURCE_SMOKE, representative_pilot_report
from .sources.base import PublicJsonClient
from .sources.cafef import (ADAPTER_VERSION as CAFE_VERSION, CafeFSource,
                            INVALID_ROW_EVIDENCE_FIELDS, apply_invalid_row_policy,
                            classify_cafef_page_row, map_trade_history_row)
from .sources.vnstock import (ADAPTER_VERSION as KBS_VERSION, KBSPublicHttpSource,
                              classify_volume_semantics, date_batches,
                              financial_raw_only_metadata, map_kbs_wire_ohlcv_row)


OFFICIAL_MARKET_SOURCES = {
    "ohlcv": "kbs_delta_public_http",
    "benchmark": "kbs_delta_public_http",
    "reference_limits_value": "cafef_direct",
}
REQUIRED_EXCHANGES = {"HOSE", "HNX", "UPCOM"}
SECRET_KEY_MARKERS = ("secret", "token", "password", "cookie", "credential", "api_key", "authorization")
FINANCIAL_PIT_UNRESOLVED = "PIT_UNRESOLVED"
RUN_IDENTITY_FIELDS = (
    "config_hash", "universe_hash", "source_gate_hash", "code_hash",
    "job_plan_hash", "kbs_adapter_version", "cafef_adapter_version",
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def _years(start, end):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last:
        raise ValueError("pilot start must not follow end")
    return (last - first).days / 365.2425


def _assert_no_secret_keys(value, prefix="config"):
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in SECRET_KEY_MARKERS):
                raise ValueError(f"secret-like config key is forbidden: {prefix}.{key}")
            _assert_no_secret_keys(nested, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_secret_keys(nested, f"{prefix}[{index}]")


def raw_storage_is_gitignored(root):
    ignore = (Path(root) / ".gitignore").read_text(encoding="utf-8").splitlines()
    rules = {line.strip().replace("\\", "/") for line in ignore if line.strip() and not line.startswith("#")}
    return bool({"/data/", "data/", "/data/raw/", "data/raw/"} & rules)


def validate_source_gate(report):
    valid = (
        report.get("gate") == SOURCE_SMOKE
        and report.get("status") == "PASS"
        and REPRESENTATIVE_PILOT in report.get("unlocks", [])
        and report.get("checks", {}).get("real_data") is True
        and bool(report.get("input_evidence_hashes"))
    )
    if not valid:
        raise ValueError("a real PASS SOURCE_SMOKE gate unlocking REPRESENTATIVE_PILOT is required")


def validate_universe(rows, *, sector_limitation=None):
    if not isinstance(rows, list):
        raise ValueError("pilot universe must be a JSON array")
    validate_rows("representative_pilot_universe", rows)
    if not 50 <= len(rows) <= 60:
        raise ValueError("representative pilot requires 50-60 selected symbols")
    tickers = [row["ticker"].upper() for row in rows]
    if len(tickers) != len(set(tickers)):
        raise ValueError("representative pilot symbols must be unique")
    if set(row["exchange"] for row in rows) != REQUIRED_EXCHANGES:
        raise ValueError("representative pilot must cover HOSE, HNX and UPCOM")
    for row in rows:
        if row["ticker"] != row["ticker"].upper() or not row["ticker"].isalnum():
            raise ValueError("pilot ticker must be uppercase alphanumeric")
        if row["history_eligibility"] == "SHORT_HISTORY" and row["reference_only"] is not True:
            raise ValueError("short-history securities must be REFERENCE_ONLY")
        if row["history_eligibility"] == "UNKNOWN_PENDING_REVIEW" and row["reference_only"] is not True:
            raise ValueError("unknown history eligibility must be REFERENCE_ONLY")
    sectors = {row["sector"] for row in rows if row["sector"]}
    limitation_ok = isinstance(sector_limitation, str) and bool(sector_limitation.strip())
    if len(sectors) < 2 and not limitation_ok:
        raise ValueError("multiple sectors or an explicit reviewed sector limitation is required")
    return {
        "symbol_count": len(rows),
        "symbols_unique": True,
        "exchange_coverage": sorted(REQUIRED_EXCHANGES),
        "sector_coverage": sorted(sectors),
        "sector_limitation": sector_limitation if limitation_ok else None,
        "representative_sectors_or_documented_limit": len(sectors) >= 2 or limitation_ok,
        "reference_only_symbols": sorted(row["ticker"] for row in rows if row["reference_only"]),
    }


def validate_config(config, *, root):
    if (config.get("template_type") != REPRESENTATIVE_PILOT
            or config.get("synthetic") is not False
            or config.get("research_demo") is not True
            or config.get("rights_status") != "RIGHTS_NOT_VERIFIED"
            or config.get("risk_acceptance") != "ACCEPTED_RESEARCH_RISK"
            or config.get("raw_redistribution") is not False):
        raise ValueError("representative-pilot research/demo policy is invalid")
    _assert_no_secret_keys(config)
    if config.get("market_sources") != OFFICIAL_MARKET_SOURCES:
        raise ValueError("official pilot routing must match the smoke-validated KBS/CafeF paths")
    if _years(config["start"], config["end"]) < 5:
        raise ValueError("representative pilot must request at least five years")
    financial = config.get("financial", {})
    if (financial.get("mode") != "RAW_ONLY_PIT_UNRESOLVED"
            or financial.get("enabled_for_market_gate") is not False):
        raise ValueError("financial PIT must remain a disabled RAW_ONLY side-track for the market gate")
    http = config.get("http", {})
    if (http.get("timeout", 0) <= 0 or not 1 <= http.get("attempts", 0) <= 3
            or http.get("min_interval", -1) < 1 or http.get("concurrency") != 1):
        raise ValueError("pilot HTTP policy must be bounded, single-threaded and rate-limited")
    cafef = config.get("cafef", {})
    if cafef.get("page_size") != 30 or not 1 <= cafef.get("max_pages", 0) <= 100:
        raise ValueError("CafeF pilot pagination must use page size 30 and max_pages <= 100")
    thresholds = config.get("coverage_thresholds", {})
    ratio = thresholds.get("minimum_usable_five_year_ratio")
    if (not isinstance(ratio, (int, float)) or isinstance(ratio, bool)
            or not 0 < ratio <= 1 or thresholds.get("maximum_failed_symbols") != 0):
        raise ValueError("pilot coverage thresholds must be explicit and fail-closed")
    policy = config.get("invalid_market_row_policy", {})
    if (policy.get("provider"), policy.get("symbol"), policy.get("trade_date"),
            policy.get("classification"), policy.get("row_status"), policy.get("policy")) != (
            "cafef", "VNM", "2021-09-09", "PROVIDER_CORRUPT_ROW",
            "INVALID_REQUIRED_MARKET_ROW", "EXCLUDE_ROW") or set(
                policy.get("expected_raw_fields", {})) != INVALID_ROW_EVIDENCE_FIELDS:
        raise ValueError("the exact evidence-bounded VNM invalid-row policy is required")
    if not raw_storage_is_gitignored(root):
        raise ValueError("data/raw must remain gitignored")


def load_readiness(config_path, gate_report_path, *, root):
    root = Path(root).resolve()
    config_path, gate_report_path = Path(config_path).resolve(), Path(gate_report_path).resolve()
    config = read_json(config_path)
    validate_config(config, root=root)
    gate = read_json(gate_report_path)
    validate_source_gate(gate)
    universe_value = config.get("universe_file")
    if not isinstance(universe_value, str) or "LOCAL_OR_REVIEWED_PATH" in universe_value:
        raise ValueError("a reviewed local universe_file is required")
    universe_path = Path(universe_value)
    if not universe_path.is_absolute():
        universe_path = (config_path.parent / universe_path).resolve()
    if not universe_path.is_file():
        raise ValueError("reviewed pilot universe file does not exist")
    universe = read_json(universe_path)
    universe_summary = validate_universe(
        universe, sector_limitation=config.get("sector_coverage_limitation"))
    return {
        "root": root, "config_path": config_path, "gate_report_path": gate_report_path,
        "universe_path": universe_path, "config": config, "source_gate": gate,
        "universe": universe, "universe_summary": universe_summary,
        "config_hash": digest(config_path.read_bytes()),
        "source_gate_hash": digest(gate_report_path.read_bytes()),
        "universe_hash": digest(universe_path.read_bytes()),
    }


def build_job_plan(prepared):
    config, universe = prepared["config"], prepared["universe"]
    batches = list(date_batches(config["start"], config["end"]))
    jobs = []
    for row in universe:
        for start, end in batches:
            jobs.append({"id": f"kbs-{row['ticker']}-{start}-{end}", "provider": "kbs",
                         "kind": "equity", "symbol": row["ticker"],
                         "exchange": row["exchange"], "start": start, "end": end})
        jobs.append({"id": f"cafef-{row['ticker']}", "provider": "cafef",
                     "kind": "reference_limits_value", "symbol": row["ticker"],
                     "exchange": row["exchange"], "start": config["start"],
                     "end": config["end"], "max_pages": config["cafef"]["max_pages"]})
    for start, end in batches:
        jobs.append({"id": f"kbs-VNINDEX-{start}-{end}", "provider": "kbs",
                     "kind": "index", "symbol": "VNINDEX", "exchange": "HOSE",
                     "start": start, "end": end})
    financial = config["financial"]
    if financial.get("collect_raw_side_track") is True:
        requested = financial.get("symbols", [])
        selected = {row["ticker"] for row in universe}
        if not requested or not set(requested) <= selected:
            raise ValueError("financial side-track symbols must be an explicit pilot subset")
        for symbol in requested:
            jobs.append({"id": f"kbs-{symbol}-financial-raw-only", "provider": "kbs",
                         "kind": "financial_raw_only", "symbol": symbol})
    return {
        "template_type": REPRESENTATIVE_PILOT,
        "source_routing": OFFICIAL_MARKET_SOURCES,
        "requested_range": {"start": config["start"], "end": config["end"]},
        "history_years": _years(config["start"], config["end"]),
        "benchmark": "VNINDEX", "jobs": jobs,
        "requests_lower_bound": len(jobs),
        "financial_pit_status": FINANCIAL_PIT_UNRESOLVED,
        "financial_features_allowed": False,
    }


def _run_directory(root, run_id):
    return Path(root) / "data" / "raw" / "representative_pilot" / run_id


def build_run_identity(prepared, plan):
    """Return the complete immutable identity for a pilot execution plan."""
    return {
        "config_hash": prepared["config_hash"],
        "universe_hash": prepared["universe_hash"],
        "source_gate_hash": prepared["source_gate_hash"],
        "code_hash": code_hash(),
        "job_plan_hash": digest(encoded(plan)),
        "kbs_adapter_version": KBS_VERSION,
        "cafef_adapter_version": CAFE_VERSION,
    }


def validate_resume_identity(run_header, expected_identity):
    """Reject old or mixed-version runs instead of migrating them in place."""
    for field in RUN_IDENTITY_FIELDS:
        if run_header.get(field) != expected_identity[field]:
            raise ValueError(
                f"resume {field} mismatch; start a new immutable run")


def validate_resume_run(directory, run_id, expected_plan, expected_identity):
    """Validate an immutable real run completely before constructing a client."""
    run_header = read_json(directory / "run.json")
    manifest = read_json(directory / "manifest.json")
    for name, document in (("run header", run_header), ("manifest", manifest)):
        if document.get("run_id") != run_id:
            raise ValueError(
                f"resume {name} run_id mismatch; start a new immutable run")
        if document.get("mode") != "REAL_EXECUTION":
            raise ValueError(
                f"resume {name} mode mismatch; only REAL_EXECUTION runs can resume")
    validate_resume_identity(run_header, expected_identity)

    stored_plan = read_json(directory / "job_plan.json")
    if digest(encoded(stored_plan)) != expected_identity["job_plan_hash"]:
        raise ValueError(
            "resume stored job_plan_hash mismatch; start a new immutable run")
    if stored_plan != expected_plan:
        raise ValueError(
            "resume stored job plan mismatch; start a new immutable run")

    expected_jobs = {job["id"]: job for job in expected_plan["jobs"]}
    stored_jobs = manifest.get("jobs")
    if not isinstance(stored_jobs, dict):
        raise ValueError(
            "resume manifest jobs must be an object; start a new immutable run")
    missing = sorted(set(expected_jobs) - set(stored_jobs))
    extra = sorted(set(stored_jobs) - set(expected_jobs))
    if missing or extra:
        raise ValueError(
            f"resume manifest job set mismatch (missing={missing}, extra={extra}); "
            "start a new immutable run")
    for job_id, expected_job in expected_jobs.items():
        state = stored_jobs[job_id]
        if not isinstance(state, dict) or state.get("job") != expected_job:
            raise ValueError(
                f"resume manifest job definition mismatch: {job_id}; "
                "start a new immutable run")
    return manifest


def _write_run_headers(prepared, plan, run_id, *, dry_run):
    directory = _run_directory(prepared["root"], run_id)
    if directory.exists():
        raise ValueError("immutable representative-pilot run already exists")
    identity = build_run_identity(prepared, plan)
    write_json(directory / "run.json", {
        "run_id": run_id, "template_type": REPRESENTATIVE_PILOT,
        "mode": "DRY_RUN" if dry_run else "REAL_EXECUTION",
        "started_at": utc_now(), "network_requests": 0,
        **identity,
    })
    write_json(directory / "source_gate_reference.json", {
        "gate": SOURCE_SMOKE, "status": "PASS", "unlocks": [REPRESENTATIVE_PILOT],
        "path": prepared["gate_report_path"].as_posix(), "sha256": prepared["source_gate_hash"],
    })
    write_json(directory / "job_plan.json", plan)
    return directory


def dry_run(config_path, gate_report_path, *, root, run_id=None):
    """Validate readiness and emit a local plan without constructing a network client."""
    prepared = load_readiness(config_path, gate_report_path, root=root)
    plan = build_job_plan(prepared)
    run_id = run_id or new_artifact_id("representative-pilot")
    directory = _write_run_headers(prepared, plan, run_id, dry_run=True)
    manifest = {
        "run_id": run_id, "mode": "DRY_RUN", "status": "DRY_RUN_READINESS_PASS",
        "readiness": "PASS", "network_requests": 0, "execution_started": False,
        "gate_emitted": False, "unlocks": [],
        "checks": {
            "source_smoke_passed": True, "fifty_to_sixty_symbols": True,
            "symbols_unique": True, "at_least_five_years": True,
            "representative_exchanges": True,
            "representative_sectors_or_documented_limit": prepared["universe_summary"][
                "representative_sectors_or_documented_limit"],
            "source_routing_matches_smoke": True, "raw_storage_gitignored": True,
            "financial_safety_lock_active": True, "no_secrets": True,
        },
        "universe_summary": prepared["universe_summary"],
        "job_count": len(plan["jobs"]), "requests_lower_bound": plan["requests_lower_bound"],
        "financial_pit_status": FINANCIAL_PIT_UNRESOLVED,
        "financial_features_allowed": False,
    }
    write_json(directory / "manifest.json", manifest)
    return directory, manifest


class PilotRawStore:
    def __init__(self, root, run_id):
        self.root, self.run_id = Path(root), run_id

    def save(self, provider, name, response, request, *, adapter_version,
             acquisition_client, endpoint_discovered_via=None):
        directory = self.root / "data" / "raw" / provider / self.run_id
        raw_path, metadata_path = directory / f"{name}.json", directory / f"{name}.metadata.json"
        body, sha256 = response["body"], digest(response["body"])
        if raw_path.exists():
            if digest(raw_path.read_bytes()) != sha256 or not metadata_path.exists():
                raise ValueError("immutable provider artifact collision")
            metadata = read_json(metadata_path)
            if metadata.get("sha256") != sha256:
                raise ValueError("provider metadata checksum mismatch")
            return metadata
        atomic_write(raw_path, body)
        metadata = {
            "provider": provider, "acquisition_client": acquisition_client,
            "endpoint_discovered_via": endpoint_discovered_via,
            "symbol": request["symbol"], "requested_date_range": request.get("date_range"),
            "endpoint_method": "GET", "url": response["url"], "request": request,
            "fetched_at": utc_now(), "adapter_client_version": adapter_version,
            "rights_status": "RIGHTS_NOT_VERIFIED",
            "execution_policy": "ACCEPTED_RESEARCH_RISK",
            "sha256": sha256, "bytes": len(body), "http_status": response["status"],
            "raw_path": raw_path.relative_to(self.root).as_posix(),
        }
        write_json(metadata_path, metadata)
        return metadata

    def verify(self, artifact):
        path = self.root / artifact["raw_path"]
        return path.is_file() and digest(path.read_bytes()) == artifact["sha256"]


def _valid_kbs(rows, *, index=False):
    if not rows or len(rows) != len({row["trade_date"] for row in rows}):
        return False
    return all(
        row["low"] <= row["open"] <= row["high"]
        and row["low"] <= row["close"] <= row["high"]
        and (row["volume"] is None or row["volume"] >= 0)
        and row["price_basis"] == "VENDOR_ADJUSTED"
        and row["price_unit"] == ("INDEX_POINTS" if index else "VND_PER_SHARE")
        for row in rows
    )


def _execute_job(job, config, kbs, cafef, store):
    if job["provider"] == "kbs" and job["kind"] in ("equity", "index"):
        response = kbs.acquire_ohlcv(job["symbol"], job["start"], job["end"],
                                     is_index=job["kind"] == "index")
        return [store.save("kbs", job["id"], response,
                           {"symbol": job["symbol"], "exchange": job["exchange"],
                            "date_range": {"start": job["start"], "end": job["end"]}},
                           adapter_version=KBS_VERSION, acquisition_client="delta_public_http",
                           endpoint_discovered_via="vnstock")]
    if job["kind"] == "financial_raw_only":
        response = kbs.acquire_financial_raw(job["symbol"])
        return [store.save("kbs", job["id"], response,
                           {"symbol": job["symbol"], "mode": "RAW_ONLY_PIT_UNRESOLVED"},
                           adapter_version=KBS_VERSION, acquisition_client="delta_public_http",
                           endpoint_discovered_via="vnstock")]
    artifacts, reached_start = [], False
    for page in range(1, job["max_pages"] + 1):
        response = cafef.acquire_trade_history_page(
            {"symbol": job["symbol"], "page_index": page, "page_size": 30})
        artifact = store.save("cafef", f"{job['id']}-page-{page:03d}", response,
                              {"symbol": job["symbol"], "exchange": job["exchange"],
                               "date_range": {"start": job["start"], "end": job["end"]},
                               "page_index": page, "page_size": 30},
                              adapter_version=CAFE_VERSION, acquisition_client="direct")
        artifacts.append(artifact)
        payload_rows = response["payload"]["Data"]
        if not payload_rows:
            break
        # Exclude the leading current/intraday snapshot row from historical mapping.
        # Evidence only establishes the leading row of CafeF page 1 (page == 1 and row_index == 0)
        # as the current/intraday snapshot.
        # The raw payload is already persisted in the artifact above; we only skip it
        # here to prevent it from entering the historical daily date-window.
        historical_payload_rows = [
            row for row_index, row in enumerate(payload_rows)
            if not (page == 1 and row_index == 0 and
                    classify_cafef_page_row(row.get("TradeDate", ""), page=page, row_index=row_index) == "CURRENT_SNAPSHOT")
        ]
        if not historical_payload_rows:
            continue
        mapped = [map_trade_history_row(row, job["symbol"], job["exchange"])
                  for row in historical_payload_rows]
        if min(row["trade_date"] for row in mapped) <= job["start"]:
            reached_start = True
            break
    if not reached_start:
        raise ValueError(f"CafeF max_pages did not reach requested start for {job['symbol']}")
    return artifacts


def _artifact_payload(root, artifact):
    return json.loads((Path(root) / artifact["raw_path"]).read_text(encoding="utf-8"))


def _build_real_manifest(prepared, plan, manifest):
    config, root = prepared["config"], prepared["root"]
    universe_by_symbol = {row["ticker"]: row for row in prepared["universe"]}
    kbs_rows, cafef_rows, hashes = {}, {}, {}
    financial = []
    for state in manifest["jobs"].values():
        job = state["job"]
        for artifact in state["artifacts"]:
            hashes[artifact["raw_path"]] = artifact["sha256"]
            payload = _artifact_payload(root, artifact)
            if job["kind"] in ("equity", "index"):
                rows = [map_kbs_wire_ohlcv_row(row, job["symbol"], job["exchange"],
                                               is_index=job["kind"] == "index")
                        for row in payload["data_day"]]
                kbs_rows.setdefault(job["symbol"], []).extend(rows)
            elif job["kind"] == "reference_limits_value":
                rows = [map_trade_history_row(row, job["symbol"], job["exchange"])
                        for row in payload["Data"]]
                cafef_rows.setdefault(job["symbol"], []).extend(
                    row for row in rows if job["start"] <= row["trade_date"] <= job["end"])
            elif job["kind"] == "financial_raw_only":
                financial.extend(financial_raw_only_metadata(payload))
    symbol_manifests, failed, quarantined, conflicts = {}, [], 0, 0
    for symbol, meta in universe_by_symbol.items():
        krows = sorted(kbs_rows.get(symbol, []), key=lambda row: row["trade_date"])
        crows = sorted(cafef_rows.get(symbol, []), key=lambda row: row["trade_date"])
        eligible, findings = apply_invalid_row_policy(crows, config["invalid_market_row_policy"])
        volume = classify_volume_semantics(krows, crows)
        k_dates, c_dates = {row["trade_date"] for row in krows}, {row["trade_date"] for row in crows}
        duplicates = (len(krows) - len(k_dates)) + (len(crows) - len(c_dates))
        years = ((date.fromisoformat(max(k_dates)) - date.fromisoformat(min(k_dates))).days / 365.2425
                 if k_dates else 0)
        qc = (_valid_kbs(krows) and bool(eligible) and duplicates == 0
              and all(finding["safe"] for finding in findings)
              and volume["market_collection_safe"])
        reference_only = meta["reference_only"] or years < 3
        if not qc:
            failed.append(symbol)
        quarantined += len(findings)
        conflicts += int(volume["classification"] == "UNRESOLVED")
        symbol_manifests[symbol] = {
            "symbol": symbol, "exchange": meta["exchange"],
            "sector": meta["sector"], "sector_status": meta["sector_status"],
            "requested_range": {"start": config["start"], "end": config["end"]},
            "observed_min_date": min(k_dates) if k_dates else None,
            "observed_max_date": max(k_dates) if k_dates else None,
            "kbs_row_count": len(krows), "cafef_row_count": len(crows),
            "missing_dates_summary": {"basis": "CROSS_SOURCE_OBSERVED_DATES",
                                      "kbs_only": len(k_dates - c_dates),
                                      "cafef_only": len(c_dates - k_dates)},
            "duplicate_count": duplicates, "invalid_row_count": len(findings),
            "price_basis": "VENDOR_ADJUSTED",
            "volume_semantic_status": volume,
            "source_provenance": {
                "ohlcv": {"provider": "kbs", "acquisition_client": "delta_public_http",
                          "endpoint_discovered_via": "vnstock"},
                "reference_limits_value": {"provider": "cafef", "acquisition_client": "direct"},
            },
            "raw_artifact_hashes": {path: value for path, value in hashes.items()
                                    if f"/{symbol}-" in path or f"-{symbol}-" in path},
            "history_usability": {"observed_years": years, "usable_5y": years >= 5,
                                  "usable_3y_for_clustering": years >= 3},
            "reference_only": reference_only, "qc_status": "PASS" if qc else "FAIL",
        }
    benchmark_rows = sorted(kbs_rows.get("VNINDEX", []), key=lambda row: row["trade_date"])
    aggregate = {
        "selected_symbols": len(symbol_manifests),
        "usable_5y_symbols": sum(item["history_usability"]["usable_5y"] for item in symbol_manifests.values()),
        "usable_3y_clustering_symbols": sum(
            item["history_usability"]["usable_3y_for_clustering"] and not item["reference_only"]
            for item in symbol_manifests.values()),
        "reference_only_symbols": sorted(symbol for symbol, item in symbol_manifests.items()
                                         if item["reference_only"]),
        "exchange_coverage": sorted({item["exchange"] for item in symbol_manifests.values()}),
        "sector_coverage": sorted({item["sector"] for item in symbol_manifests.values() if item["sector"]}),
        "failed_symbols": failed, "quarantined_rows": quarantined,
        "provider_conflicts": conflicts,
    }
    manifest.update(symbols=symbol_manifests, aggregate=aggregate,
                    benchmark={"symbol": "VNINDEX", "rows": len(benchmark_rows),
                               "valid": _valid_kbs(benchmark_rows, index=True),
                               "price_unit": "INDEX_POINTS",
                               "volume_unit": "PROVIDER_INDEX_VOLUME"},
                    financial={"pit_status": FINANCIAL_PIT_UNRESOLVED,
                               "features_allowed": False, "observations": len(financial)},
                    provider_artifact_hashes=hashes)
    return manifest


def run_real(config_path, gate_report_path, *, root, resume=None):
    """Execute the official pilot path after the CLI has required --execute."""
    prepared = load_readiness(config_path, gate_report_path, root=root)
    plan = build_job_plan(prepared)
    identity = build_run_identity(prepared, plan)
    run_id = resume or new_artifact_id("representative-pilot")
    directory = _run_directory(prepared["root"], run_id)
    if resume:
        if not run_id.startswith("representative-pilot-") or not directory.is_dir():
            raise ValueError("resume requires an existing representative-pilot run")
        manifest = validate_resume_run(directory, run_id, plan, identity)
    else:
        directory = _write_run_headers(prepared, plan, run_id, dry_run=False)
        manifest = {"run_id": run_id, "mode": "REAL_EXECUTION", "status": "RUNNING",
                    "started_at": utc_now(), "jobs": {
                        job["id"]: {"status": "PENDING", "job": job, "artifacts": []}
                        for job in plan["jobs"]}}
        write_json(directory / "manifest.json", manifest)
    client = PublicJsonClient(**{key: value for key, value in prepared["config"]["http"].items()
                                 if key != "concurrency"})
    kbs, cafef = KBSPublicHttpSource(client), CafeFSource(client)
    store = PilotRawStore(prepared["root"], run_id)
    try:
        for state in manifest["jobs"].values():
            if state["status"] == "COMPLETE":
                if not all(store.verify(artifact) for artifact in state["artifacts"]):
                    raise ValueError("resume artifact checksum mismatch")
                continue
            state.update(status="RUNNING", error=None)
            write_json(directory / "manifest.json", manifest)
            artifacts = _execute_job(state["job"], prepared["config"], kbs, cafef, store)
            state.update(status="COMPLETE", artifacts=artifacts)
            write_json(directory / "manifest.json", manifest)
        manifest = _build_real_manifest(prepared, plan, manifest)
        aggregate = manifest["aggregate"]
        thresholds = prepared["config"]["coverage_thresholds"]
        five_year_ratio = aggregate["usable_5y_symbols"] / aggregate["selected_symbols"]
        evidence = {
            "synthetic": False, "run_mode": "REAL_EXECUTION",
            "symbol_count": aggregate["selected_symbols"], "history_years": plan["history_years"],
            "representative_exchanges": set(aggregate["exchange_coverage"]) == REQUIRED_EXCHANGES,
            "representative_sectors_or_documented_limit": prepared["universe_summary"][
                "representative_sectors_or_documented_limit"],
            "source_routing_matches_smoke": plan["source_routing"] == OFFICIAL_MARKET_SOURCES,
            "market_qc_passed": (
                len(aggregate["failed_symbols"]) <= thresholds["maximum_failed_symbols"]
                and five_year_ratio >= thresholds["minimum_usable_five_year_ratio"]
                and manifest["benchmark"]["valid"]
            ),
            "price_basis_safe": all(item["price_basis"] == "VENDOR_ADJUSTED"
                                    for item in manifest["symbols"].values()),
            "reconciliation_policy_safe": all(
                item["volume_semantic_status"]["storage_policy"] == "KEEP_SOURCE_QUALIFIED"
                and item["volume_semantic_status"]["canonical_merge_allowed"] is False
                for item in manifest["symbols"].values()),
            "provenance_complete": all(
                artifact.get("provider") and artifact.get("acquisition_client")
                for state in manifest["jobs"].values() for artifact in state["artifacts"]),
            "invalid_rows_fail_closed": all(
                item["invalid_row_count"] == 0 or item["qc_status"] == "PASS"
                for item in manifest["symbols"].values()),
            "source_qualified_conflicts": all(
                item["volume_semantic_status"]["storage_policy"] == "KEEP_SOURCE_QUALIFIED"
                and item["volume_semantic_status"]["equality_assumption"] is False
                for item in manifest["symbols"].values()),
            "missing_values_preserved": True,
            "no_price_forward_fill": True,
            "no_current_shares_backfill": True,
            "financial_pit_status": FINANCIAL_PIT_UNRESOLVED,
            "financial_features_allowed": False,
            "provider_artifact_hashes": manifest["provider_artifact_hashes"],
            "evidence_hashes": {
                "pilot-config": prepared["config_hash"], "pilot-universe": prepared["universe_hash"],
                "source-gate": prepared["source_gate_hash"],
            } | manifest["provider_artifact_hashes"],
        }
        gate = representative_pilot_report(evidence, prepared["source_gate"])
        manifest.update(status="COMPLETE" if gate["status"] == "PASS" else "FAILED_GATE",
                        finished_at=utc_now(), gate_status=gate["status"])
        write_json(directory / "manifest.json", manifest)
        write_json(directory / "gate.json", gate)
        return directory, manifest, gate
    except Exception as exc:
        manifest.update(status="FAILED", finished_at=utc_now(), error=f"{type(exc).__name__}: {exc}")
        write_json(directory / "manifest.json", manifest)
        raise
