"""Only publish feature artifacts after required downloads and QC have passed."""
import math
from pathlib import Path
from .io import read_json, write_json, write_rows, digest, now
from .contracts import validate_rows, schema
from .ingestion.crawler import crawl
from .ingestion.quality import clean_tables, coverage
from .features.compute import build_features


INPUT_TABLES = {"securities", "prices_daily", "benchmark_daily", "trading_calendar", "corporate_actions", "risk_free_rate"}


def load_config(path):
    config = read_json(path)
    if not isinstance(config.get("synthetic"), bool):
        raise ValueError("config.synthetic must explicitly be true or false")
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
    required = {"securities", "prices_daily", "benchmark_daily", "trading_calendar"}
    if not required <= {job["table"] for job in jobs}:
        raise ValueError("required input tables missing")
    fc = config["features"]
    feature_names = schema("feature_snapshots")["fields"]
    if not fc.get("required_features") or any(k not in feature_names or not k.startswith(("mom_", "vol_", "sharpe_", "mdd_", "beta_", "liquidity_")) for k in fc["required_features"]):
        raise ValueError("invalid required_features")
    if not fc.get("accepted_adjustments") or "unknown" in fc["accepted_adjustments"]:
        raise ValueError("accepted_adjustments must name understood price conventions")
    if not config["synthetic"] and "synthetic" in fc["accepted_adjustments"]:
        raise ValueError("real-data config cannot accept synthetic adjustment basis")
    if fc.get("rf_annual") is None and not fc.get("rf_tenor"):
        raise ValueError("rf_tenor required when using risk_free_rate table")
    if fc.get("rf_annual") is not None and (not math.isfinite(fc["rf_annual"]) or fc["rf_annual"] <= -1):
        raise ValueError("invalid rf_annual")
    return config


def run(config_path, root, resume=None):
    config = load_config(config_path)
    run_dir, manifest, raw = crawl(config, root, resume)
    if manifest["status"] == "failed":
        return run_dir, manifest
    tables, issues, quarantine = clean_tables(raw, manifest["data_version"])
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
        features = build_features(tables, config["features"], manifest["data_version"])
        validate_rows("feature_snapshots", features)
        write_rows(run_dir / "features" / "monthly.jsonl", features)
    report = coverage(tables, features)
    report.update(synthetic=manifest["synthetic"], run_id=manifest["run_id"], n_quality_errors=len(issues))
    write_json(run_dir / "quality" / "coverage.json", report)
    manifest.update(status="quality_failed" if issues else "complete", finished_at=now(), clean_rows={k: len(v) for k, v in tables.items()}, feature_rows=len(features))
    manifest["artifacts"] = {p.relative_to(run_dir).as_posix(): digest(p.read_bytes()) for folder in ("clean", "quality", "features") for p in sorted((run_dir / folder).glob("*")) if p.is_file()}
    write_json(run_dir / "manifest.json", manifest)
    return run_dir, manifest
