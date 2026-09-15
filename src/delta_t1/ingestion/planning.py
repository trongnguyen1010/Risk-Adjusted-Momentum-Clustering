"""Read-only pilot acceptance checks and bounded large-crawl planning."""
from datetime import date
from pathlib import Path

from ..io import digest, read_json, read_rows
from .sources.base import contained_file
from .sources.vnstock import date_batches


def pilot_report(experiment_dir: Path) -> dict:
    """A synthetic run can never unlock a real crawl, regardless of its metrics."""
    directory = Path(experiment_dir).resolve()
    experiment = read_json(directory / "manifest.json")
    checks = {"experiment_complete": experiment["status"] == "complete", "real_data": experiment["synthetic"] is False}
    source_path = Path(experiment["data_run_path"])
    source = read_json(source_path / "manifest.json")
    checks["input_manifest_checksum"] = digest((source_path / "manifest.json").read_bytes()) == experiment["source_manifest_hash"]
    for folder, manifest in ((directory, experiment), (source_path, source)):
        checks[folder.name + "_artifacts"] = all(digest(contained_file(folder, name).read_bytes()) == expected for name, expected in manifest["artifacts"].items())
    prices = read_rows(source_path / "clean/prices_daily.jsonl")
    securities = read_rows(source_path / "clean/securities.jsonl")
    dates = sorted({r["trade_date"] for r in prices})
    checks["3_to_10_securities"] = 3 <= len({r["security_id"] for r in prices}) <= 10
    checks["at_least_18_months"] = bool(dates) and (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days >= 545
    allowed_identity = {"verified"}
    if experiment["config"].get("pilot") and experiment["config"].get("identity_method") == "provisional_verified_for_pilot":
        allowed_identity.add("provisional_verified_for_pilot")
    checks["historical_identity"] = bool(securities) and all(r["identity_status"] in allowed_identity for r in securities)
    checks["ten_securities_for_clustering"] = len(securities) >= 10
    checks["monthly_transitions"] = bool(read_rows(directory / "transitions.jsonl"))
    checks["backtest_complete"] = bool(read_rows(directory / "backtests/cluster.jsonl"))
    checks["long_window_eligible"] = any(r["eligibility"] and r["mom_252"] is not None for r in read_rows(source_path / "features/monthly.jsonl"))
    checks["vendor_lineage"] = bool(source.get("vendor_run_id") and source.get("canonical_manifest_hash"))
    checks["pit_evidence"] = bool(experiment["config"].get("point_in_time_evidence"))
    # Data readiness only. This does not certify a full raw-share accounting engine.
    return dict(status="PASS" if all(checks.values()) else "BLOCKED", checks=checks,
                experiment_manifest_hash=digest((directory / "manifest.json").read_bytes()),
                experiment_run_id=experiment["run_id"], scope="data/features/clustering/return-space pilot; not thesis acceptance")


def plan_large_crawl(config: dict, pilot: dict) -> dict:
    """Build a plan only; explicit temporal-universe symbols must be supplied."""
    if pilot["status"] != "PASS":
        raise ValueError("real pilot has not passed; large crawl blocked")
    if not config.get("universe_evidence") or not config.get("symbols"):
        raise ValueError("explicit historical-universe symbols and evidence required")
    if len(set(config["symbols"])) != len(config["symbols"]) or len(config["symbols"]) > 350:
        raise ValueError("duplicate or oversized universe")
    start, end = date.fromisoformat(config["start"]), date.fromisoformat(config["end"])
    if not 365 * 5 <= (end - start).days <= 366 * 6:
        raise ValueError("scale plan must cover 5–6 years")
    jobs = [dict(symbol=s, start=a, end=b) for s in sorted(config["symbols"] + ["VNINDEX"]) for a, b in date_batches(config["start"], config["end"])]
    return dict(config=config, pilot=pilot, jobs=jobs, requests_lower_bound=len(jobs) + 1, interval_seconds=5, attempts=3, timeout_seconds=90,
                resume_policy="same vendor run ID only with unchanged code/config; preserve successful checksummed snapshots")
