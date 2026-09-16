"""Only publish feature artifacts after required downloads and QC have passed."""
import math
from pathlib import Path
from .artifact_ids import new_artifact_id
from .io import read_json, read_rows, write_json, write_rows, digest, now, encoded
from .contracts import validate_rows, schema
from .ingestion.crawler import crawl
from .ingestion.quality import clean_tables, coverage
from .features.market import build_features
from .features.registry import FEATURE_REGISTRY


REQUIRED_INPUT_TABLES = {"securities", "prices_daily", "benchmark_daily", "trading_calendar"}
OPTIONAL_INPUT_TABLES = {"corporate_actions", "risk_free_rate", "financial_reports", "financial_facts", "shares_history"}
INPUT_TABLES = REQUIRED_INPUT_TABLES | OPTIONAL_INPUT_TABLES


def load_config(path):
    config = read_json(path)
    return validate_config(config)


def validate_config(config):
    if not isinstance(config.get("synthetic"), bool):
        raise ValueError("config.synthetic must explicitly be true or false")
    guard = config.get("execution_guard")
    if guard is not None and guard.get("approved") is not True:
        raise ValueError("source smoke template is fail-closed pending semantics/rights approval")
    jobs = config.get("jobs", [])
    ids = [job["id"] for job in jobs]
    if len(ids) != len(set(ids)) or not jobs:
        raise ValueError("jobs must have unique IDs and not be empty")
    for job in jobs:
        if not job["id"].replace("-", "").replace("_", "").isalnum():
            raise ValueError("invalid job ID")
        if job["table"] not in INPUT_TABLES or job["provider"] not in ("csv", "http_json"):
            raise ValueError("unsupported table/provider")
        if not job.get("source"):
            raise ValueError("job source required")
        if job.get("max_pages", 100) < 1:
            raise ValueError("max_pages must be positive")
        if any(k not in schema(job["table"])["fields"] for k in job.get("mapping", {})):
            raise ValueError("unknown canonical field in mapping")
        for value in job.get("multipliers", {}).values():
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError("multipliers must be finite positive numbers")
        for key in job.get("params", {}):
            if any(secret in key.lower() for secret in ("token", "secret", "password", "api_key", "apikey")):
                raise ValueError("do not put secrets in params; use token_env")
    if not REQUIRED_INPUT_TABLES <= {job["table"] for job in jobs}:
        raise ValueError("required input tables missing")
    fc = config["features"]
    feature_names = schema("feature_snapshots")["fields"]
    try:
        definitions = FEATURE_REGISTRY.require_cluster_eligible(fc.get("required_features", []))
    except ValueError as exc:
        raise ValueError("invalid required_features: " + str(exc)) from exc
    if any(definition.name not in feature_names for definition in definitions):
        raise ValueError("required feature is not present in the active snapshot contract")
    minimum_history_years = fc.get("minimum_history_years", 0)
    if isinstance(minimum_history_years, bool) or not isinstance(minimum_history_years, int) or minimum_history_years < 0:
        raise ValueError("minimum_history_years must be a nonnegative integer")
    if not config["synthetic"] and minimum_history_years < 3:
        raise ValueError("real-data clustering requires minimum_history_years >= 3")
    if not fc.get("accepted_adjustments") or not set(fc["accepted_adjustments"]) <= {"synthetic", "split_adjusted", "vendor_adjusted", "unadjusted", "total_return"}:
        raise ValueError("accepted_adjustments must name understood price conventions")
    if not config["synthetic"] and "synthetic" in fc["accepted_adjustments"]:
        raise ValueError("real-data config cannot accept synthetic adjustment basis")
    return config


def run(config_path, root, resume=None):
    config = load_config(config_path)
    if resume:
        from .ingestion.crawler import code_hash
        from .ingestion.sources.base import contained_file
        if not resume.replace("-", "").isalnum():
            raise ValueError("invalid run id")
        previous_dir = Path(root).resolve() / "data/runs" / resume
        previous = read_json(previous_dir / "manifest.json")
        if previous["status"] == "complete":
            fingerprint = {"config": config, "csv_hashes": {j["id"]: digest((Path(root) / j["path"]).read_bytes()) for j in config["jobs"] if j["provider"] == "csv"}}
            if previous["config_hash"] != digest(encoded(fingerprint)) or previous["code_hash"] != code_hash():
                raise ValueError("resume config/input/code changed")
            checks = dict(previous["artifacts"])
            checks.update({entry["path"]: entry["sha256"] for job in previous["jobs"].values() for entry in job["pages"]})
            for relative, expected in checks.items():
                if digest(contained_file(previous_dir, relative).read_bytes()) != expected:
                    raise ValueError("resume artifact/raw checksum mismatch")
            return previous_dir, previous
    run_dir, manifest, raw = crawl(config, root, resume)
    if manifest["status"] == "failed":
        return run_dir, manifest
    return process_raw(raw, config, run_dir, manifest)


def process_raw(raw, config, run_dir, manifest):
    """Shared canonical QC/features path for CSV, HTTP and verified promotion."""
    import time
    started = time.monotonic()
    manifest["data_mode"] = "synthetic" if config["synthetic"] else "real"
    tables, issues, quarantine = clean_tables(raw, manifest["data_version"])
    if not config["synthetic"]:
        for table, field in (("trading_calendar", "available_at"), ("benchmark_daily", "index_basis")):
            if any(not r.get(field) or r.get(field) in ("unknown", "synthetic") for r in tables.get(table, [])):
                issues.append(dict(rule_id="UNRESOLVED_REFERENCE", table=table, severity="error", message="Real data requires verified " + field))
    for table, rows in tables.items():
        validate_rows(table, rows)
        write_rows(run_dir / "clean" / (table + ".jsonl"), rows)
    for table in ("securities", "prices_daily", "benchmark_daily", "trading_calendar"):
        if not tables.get(table):
            issues.append({"rule_id": "EMPTY_TABLE", "table": table, "severity": "error", "status": "open", "message": "Required clean table is empty"})
    write_rows(run_dir / "quality" / "issues.jsonl", issues)
    write_rows(run_dir / "quality" / "quarantine.jsonl", quarantine)
    features = []
    if not issues:
        feature_config = dict(config["features"], data_mode=manifest["data_mode"], vendor_run_id=manifest.get("vendor_run_id"), canonical_run_id=manifest.get("canonical_run_id"))
        features = build_features(tables, feature_config, manifest["data_version"])
        validate_rows("feature_snapshots", features)
        write_rows(run_dir / "features" / "monthly.jsonl", features)
    report = coverage(tables, features)
    report.update(synthetic=manifest["synthetic"], data_mode=manifest["data_mode"], run_id=manifest["run_id"], n_quality_errors=len(issues))
    write_json(run_dir / "quality" / "coverage.json", report)
    write_rows(run_dir / "quality" / "events.jsonl", [dict(run_id=manifest["run_id"], stage="canonical_qc_features",
               records_in=sum(len(v) for v in raw.values()), records_out=sum(len(v) for v in tables.values()), records_failed=len(quarantine),
               feature_rows=len(features), elapsed=time.monotonic() - started, source=manifest.get("vendor_run_id", "configured_sources"), data_version=manifest["data_version"])])
    manifest.update(status="quality_failed" if issues else "complete", finished_at=now(), clean_rows={k: len(v) for k, v in tables.items()}, feature_rows=len(features))
    manifest["artifacts"] = {p.relative_to(run_dir).as_posix(): digest(p.read_bytes()) for folder in ("clean", "quality", "features") for p in sorted((run_dir / folder).glob("*")) if p.is_file()}
    write_json(run_dir / "manifest.json", manifest)
    return run_dir, manifest


def run_canonical(canonical_path, config_path, root):
    """Verify promoted artifacts and create a new run; never mutate promotion."""
    from .ingestion.sources.base import contained_file
    from .ingestion.crawler import code_hash
    canonical_path = Path(canonical_path).resolve()
    source = read_json(canonical_path / "manifest.json")
    if source["status"] != "complete":
        raise ValueError("canonical promotion is not complete")
    config = read_json(config_path)
    if config["synthetic"] != source["synthetic"]:
        raise ValueError("canonical/config synthetic mismatch")
    for relative, expected in source["artifacts"].items():
        if digest(contained_file(canonical_path, relative).read_bytes()) != expected:
            raise ValueError("canonical artifact checksum mismatch")
    raw = {}
    for table in sorted(INPUT_TABLES):
        relative = "clean/" + table + ".jsonl"
        if relative not in source["artifacts"]:
            if table in REQUIRED_INPUT_TABLES:
                raise ValueError("canonical table missing from manifest: " + table)
            raw[table] = []
            continue
        rows = read_rows(canonical_path / relative)
        raw[table] = [(r, {"source": r["source"]}, r["fetched_at"]) for r in rows]
    validation = dict(config, jobs=[dict(id=name, table=name, provider="csv", source="verified_canonical") for name in sorted(REQUIRED_INPUT_TABLES)])
    validate_config(validation)
    run_id = new_artifact_id("run")
    directory = Path(root).resolve() / "data/runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    manifest = dict(run_id=run_id, data_version=run_id, source_data_version=source["data_version"],
                    vendor_run_id=source["vendor_run_id"], canonical_run_id=source["run_id"], methodology=source.get("methodology", {}), canonical_manifest_hash=digest((canonical_path / "manifest.json").read_bytes()),
                    canonical_path=str(canonical_path),
                    config=config, config_hash=digest(encoded(config)), synthetic=config["synthetic"], code_hash=code_hash(),
                    schema_version="1.4.0", started_at=now(), data_hash=digest(encoded(source["artifacts"])), status="downloaded")
    write_json(directory / "manifest.json", manifest)
    return process_raw(raw, config, directory, manifest)
